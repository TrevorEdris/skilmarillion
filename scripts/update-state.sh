#!/usr/bin/env bash
# update-state.sh — Silent plan state persistence for /fellowship:plan --specify
# State files: .skilmarillion/projects/{slug}/PROJECT-STATE.yaml
set -euo pipefail

COMMAND="${1:-}"
shift || true

# Globals with safe defaults so `set -u` never crashes a caller that omits a
# field. Every subcommand re-assigns these inside parse_flags.
SLUG=""
FEATURE=""
SIZE=""
RISK=""
ROUTING=""
CURRENT_PHASE=""
CURRENT_WAVE=""
WAVE_AGENT_COMPLETED=""
SPEC_PATH=""
PROJECT_ROOT=""
FIELD=""
ALL=false
WAVE_AGENTS_COMPLETED_LIST=""
UNKNOWN_BLOCKS=""

# Slug shape: lowercase kebab, starts alphanumeric, up to 64 chars.
# Rejects path traversal (/, ..), uppercase, underscores, whitespace.
SLUG_REGEX='^[a-z0-9][a-z0-9-]{0,63}$'

usage() {
  echo "Usage:"
  echo "  $0 init --slug SLUG --feature FEATURE [--size SIZE] [--risk RISK] [--routing ROUTING] [--current-phase PHASE] [--current-wave WAVE] [--project-root ROOT]"
  echo "  $0 set --slug SLUG [--feature FEATURE] [--size SIZE] [--risk RISK] [--routing ROUTING] [--current-phase PHASE] [--current-wave WAVE] [--wave-agent-completed ID] [--spec-path PATH] [--project-root ROOT]"
  echo "  $0 get --slug SLUG [--field FIELD]"
  echo "  $0 list"
  echo "  $0 clear --slug SLUG"
  echo "  $0 clear --all"
  exit 1
}

validate_slug() {
  local slug="$1"
  if [[ ! "$slug" =~ $SLUG_REGEX ]]; then
    echo "Error: invalid slug '$slug' — expected lowercase kebab-case matching ${SLUG_REGEX}" >&2
    exit 1
  fi
}

state_file() {
  local slug="$1"
  validate_slug "$slug"
  echo ".skilmarillion/projects/${slug}/PROJECT-STATE.yaml"
}

# Acquire an exclusive lock on a file using mkdir (portable atomic primitive).
# Blocks up to ~3 s; exits non-zero on timeout. Releases via EXIT trap.
acquire_lock() {
  local target="$1"
  local lockdir="${target}.lock"
  local waited=0
  local max_wait=30
  while ! mkdir "$lockdir" 2>/dev/null; do
    if (( waited >= max_wait )); then
      echo "Error: lock timeout on $lockdir — another state writer is holding it" >&2
      exit 1
    fi
    sleep 0.1
    waited=$((waited + 1))
  done
  # shellcheck disable=SC2064
  trap "rmdir '$lockdir' 2>/dev/null || true" EXIT
}

parse_flags() {
  SLUG=""
  FEATURE=""
  SIZE=""
  RISK=""
  ROUTING=""
  CURRENT_PHASE=""
  CURRENT_WAVE=""
  WAVE_AGENT_COMPLETED=""
  SPEC_PATH=""
  PROJECT_ROOT=""
  FIELD=""
  ALL=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --slug)       SLUG="$2";         shift 2 ;;
      --feature)    FEATURE="$2";      shift 2 ;;
      --size)       SIZE="$2";         shift 2 ;;
      --risk)       RISK="$2";         shift 2 ;;
      --routing)    ROUTING="$2";      shift 2 ;;
      --current-phase) CURRENT_PHASE="$2"; shift 2 ;;
      --current-wave)  CURRENT_WAVE="$2";  shift 2 ;;
      --wave-agent-completed) WAVE_AGENT_COMPLETED="$2"; shift 2 ;;
      --spec-path)  SPEC_PATH="$2";    shift 2 ;;
      --project-root) PROJECT_ROOT="$2"; shift 2 ;;
      --field)      FIELD="$2";        shift 2 ;;
      --all)        ALL=true;          shift ;;
      *) echo "Unknown flag: $1" >&2; usage ;;
    esac
  done
}

read_field() {
  local file="$1"
  local key="$2"
  awk -v key="$key" '$0 ~ "^"key":[[:space:]]*" { sub(/^[^:]+:[[:space:]]*/, ""); print; exit }' "$file"
}

read_wave_agents_completed() {
  # Extract the YAML list under `wave_agents_completed:` as space-separated IDs.
  local file="$1"
  awk '
    /^wave_agents_completed:/ { in_list=1; next }
    in_list && /^  - / { sub(/^  - /, ""); printf "%s ", $0; next }
    in_list && !/^  - / && !/^$/ { in_list=0 }
  ' "$file"
}

# Capture every top-level block in the state file that update-state.sh does NOT
# own. Preserves arbitrary extensions (for example `impl:` blocks written by
# /fellowship:build) across merge writes — without this, every set() would
# silently drop them.
KNOWN_SCALARS=(feature size risk routing_decision current_phase current_wave spec_path project_root)
KNOWN_LISTS=(wave_agents_completed)

capture_unknown_blocks() {
  local file="$1"
  UNKNOWN_BLOCKS=""
  [[ -f "$file" ]] || return 0

  local known_pattern
  known_pattern="$(printf "%s|" "${KNOWN_SCALARS[@]}" "${KNOWN_LISTS[@]}")"
  known_pattern="${known_pattern%|}"

  UNKNOWN_BLOCKS="$(awk -v known="$known_pattern" '
    function is_key(line) { return line ~ /^[A-Za-z_][A-Za-z_0-9]*:/ }
    function key_name(line,    k) {
      k = line; sub(/:.*/, "", k); return k
    }
    function is_known(k,    n, i, parts) {
      n = split(known, parts, "|")
      for (i = 1; i <= n; i++) if (parts[i] == k) return 1
      return 0
    }
    BEGIN { capturing = 0 }
    {
      if (is_key($0)) {
        capturing = !is_known(key_name($0))
      }
      if (capturing) print
    }
  ' "$file")"
}

render_wave_agents_completed() {
  # Render a space-separated list of IDs as YAML list items.
  local ids="$1"
  if [[ -z "$ids" ]]; then
    echo "wave_agents_completed: []"
    return
  fi
  echo "wave_agents_completed:"
  for id in $ids; do
    echo "  - ${id}"
  done
}

write_state() {
  local file="$1"
  local tmp="${file}.tmp.$$"
  {
    cat <<EOF
feature: ${FEATURE}
size: ${SIZE}
risk: ${RISK}
routing_decision: ${ROUTING}
current_phase: ${CURRENT_PHASE}
current_wave: ${CURRENT_WAVE}
spec_path: ${SPEC_PATH}
project_root: ${PROJECT_ROOT}
EOF
    render_wave_agents_completed "${WAVE_AGENTS_COMPLETED_LIST}"
    if [[ -n "$UNKNOWN_BLOCKS" ]]; then
      printf '%s\n' "$UNKNOWN_BLOCKS"
    fi
  } > "$tmp"
  mv "$tmp" "$file"
}

merge_and_write_state() {
  local file="$1"
  acquire_lock "$file"

  capture_unknown_blocks "$file"

  local cur_feature cur_size cur_risk cur_routing cur_phase cur_wave cur_spec cur_project_root cur_wave_agents
  cur_feature=$(read_field "$file" "feature")
  cur_size=$(read_field "$file" "size")
  cur_risk=$(read_field "$file" "risk")
  cur_routing=$(read_field "$file" "routing_decision")
  cur_phase=$(read_field "$file" "current_phase")
  cur_wave=$(read_field "$file" "current_wave")
  cur_spec=$(read_field "$file" "spec_path")
  cur_project_root=$(read_field "$file" "project_root")
  cur_wave_agents=$(read_wave_agents_completed "$file")

  FEATURE="${FEATURE:-$cur_feature}"
  SIZE="${SIZE:-$cur_size}"
  RISK="${RISK:-$cur_risk}"
  ROUTING="${ROUTING:-$cur_routing}"
  CURRENT_PHASE="${CURRENT_PHASE:-$cur_phase}"
  CURRENT_WAVE="${CURRENT_WAVE:-$cur_wave}"
  SPEC_PATH="${SPEC_PATH:-$cur_spec}"
  PROJECT_ROOT="${PROJECT_ROOT:-$cur_project_root}"

  WAVE_AGENTS_COMPLETED_LIST="$(echo "$cur_wave_agents" | tr -s ' ')"
  if [[ -n "$WAVE_AGENT_COMPLETED" ]]; then
    local already_present=false
    for id in $WAVE_AGENTS_COMPLETED_LIST; do
      if [[ "$id" == "$WAVE_AGENT_COMPLETED" ]]; then
        already_present=true
        break
      fi
    done
    if [[ "$already_present" == false ]]; then
      WAVE_AGENTS_COMPLETED_LIST="${WAVE_AGENTS_COMPLETED_LIST} ${WAVE_AGENT_COMPLETED}"
    fi
  fi
  WAVE_AGENTS_COMPLETED_LIST="$(echo "$WAVE_AGENTS_COMPLETED_LIST" | xargs || true)"

  write_state "$file"
}

file_age_days() {
  local file="$1"
  local now
  now=$(date +%s)
  local mtime
  if stat -f %m "$file" &>/dev/null; then
    mtime=$(stat -f %m "$file")
  else
    mtime=$(stat -c %Y "$file")
  fi
  local age=$(( (now - mtime) / 86400 ))
  # Clock skew can produce a future mtime; clamp to 0.
  if (( age < 0 )); then age=0; fi
  echo "$age"
}

case "$COMMAND" in
  init)
    parse_flags "$@"
    [[ -z "$FEATURE" ]] && { echo "Error: --feature is required" >&2; exit 1; }
    [[ -z "$SLUG"    ]] && { echo "Error: --slug is required"    >&2; exit 1; }
    FILE=$(state_file "$SLUG")
    mkdir -p "$(dirname "$FILE")"
    acquire_lock "$FILE"
    CURRENT_PHASE="${CURRENT_PHASE:-initialized}"
    WAVE_AGENTS_COMPLETED_LIST=""
    UNKNOWN_BLOCKS=""
    write_state "$FILE"
    ;;

  set)
    parse_flags "$@"
    [[ -z "$SLUG" ]] && { echo "Error: --slug is required" >&2; exit 1; }
    FILE=$(state_file "$SLUG")
    if [[ ! -f "$FILE" ]]; then
      echo "No state file for slug: $SLUG" >&2; exit 1
    fi
    merge_and_write_state "$FILE"
    ;;

  get)
    parse_flags "$@"
    [[ -z "$SLUG" ]] && { echo "Error: --slug is required" >&2; exit 1; }
    FILE=$(state_file "$SLUG")
    if [[ ! -f "$FILE" ]]; then
      echo "No active plan state."
      exit 0
    fi
    if [[ -n "$FIELD" ]]; then
      read_field "$FILE" "$FIELD"
    else
      cat "$FILE"
    fi
    ;;

  list)
    shopt -s nullglob
    root_dir="${PROJECT_ROOT:-.}"
    FILES=("$root_dir"/.skilmarillion/projects/*/PROJECT-STATE.yaml)
    if [[ ${#FILES[@]} -eq 0 ]]; then
      echo "No plan state files found."
      exit 0
    fi
    for f in "${FILES[@]}"; do
      rel="${f#*.skilmarillion/projects/}"
      slug="${rel%/PROJECT-STATE.yaml}"
      phase=$(read_field "$f" "current_phase")
      age=$(file_age_days "$f")
      echo "${slug} | phase: ${phase} | age: ${age}d"
    done
    ;;

  clear)
    parse_flags "$@"
    if [[ "$ALL" == true ]]; then
      shopt -s nullglob
      root_dir="${PROJECT_ROOT:-.}"
      FILES=("$root_dir"/.skilmarillion/projects/*/PROJECT-STATE.yaml)
      for f in "${FILES[@]}"; do
        rm -f "$f"
      done
    else
      [[ -z "$SLUG" ]] && { echo "Error: --slug or --all is required" >&2; exit 1; }
      FILE=$(state_file "$SLUG")
      rm -f "$FILE"
    fi
    ;;

  *)
    echo "Unknown command: $COMMAND" >&2
    usage
    ;;
esac
