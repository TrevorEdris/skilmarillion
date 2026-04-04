#!/usr/bin/env bash
# update-plan-state.sh — Silent plan state persistence for /plan:specify
# State files: .skilmarillion/projects/{slug}/PROJECT-STATE.yaml
set -euo pipefail

COMMAND="${1:-}"
shift || true

usage() {
  echo "Usage:"
  echo "  $0 init --slug SLUG --feature FEATURE [--size SIZE] [--risk RISK] [--routing ROUTING] [--current-phase PHASE] [--project-root ROOT]"
  echo "  $0 set --slug SLUG [--feature FEATURE] [--size SIZE] [--risk RISK] [--routing ROUTING] [--current-phase PHASE] [--spec-path PATH] [--project-root ROOT]"
  echo "  $0 get --slug SLUG [--field FIELD]"
  echo "  $0 list"
  echo "  $0 clear --slug SLUG"
  echo "  $0 clear --all"
  exit 1
}

state_file() {
  local slug="$1"
  echo ".skilmarillion/projects/${slug}/PROJECT-STATE.yaml"
}

# Parse key=value args into named vars
parse_flags() {
  SLUG=""
  FEATURE=""
  SIZE=""
  RISK=""
  ROUTING=""
  CURRENT_PHASE=""
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
  awk -v key="$key" '$0 ~ "^"key":" { sub(/^[^:]+: ?/, ""); print; exit }' "$file"
}

write_state() {
  local file="$1"
  cat > "$file" <<EOF
feature: ${FEATURE}
size: ${SIZE}
risk: ${RISK}
routing_decision: ${ROUTING}
current_phase: ${CURRENT_PHASE}
spec_path: ${SPEC_PATH}
project_root: ${PROJECT_ROOT}
EOF
}

merge_and_write_state() {
  local file="$1"
  # Load existing values as defaults
  local cur_feature cur_size cur_risk cur_routing cur_phase cur_spec cur_project_root
  cur_feature=$(read_field "$file" "feature")
  cur_size=$(read_field "$file" "size")
  cur_risk=$(read_field "$file" "risk")
  cur_routing=$(read_field "$file" "routing_decision")
  cur_phase=$(read_field "$file" "current_phase")
  cur_spec=$(read_field "$file" "spec_path")
  cur_project_root=$(read_field "$file" "project_root")

  FEATURE="${FEATURE:-$cur_feature}"
  SIZE="${SIZE:-$cur_size}"
  RISK="${RISK:-$cur_risk}"
  ROUTING="${ROUTING:-$cur_routing}"
  CURRENT_PHASE="${CURRENT_PHASE:-$cur_phase}"
  SPEC_PATH="${SPEC_PATH:-$cur_spec}"
  PROJECT_ROOT="${PROJECT_ROOT:-$cur_project_root}"

  write_state "$file"
}

file_age_days() {
  local file="$1"
  local now
  now=$(date +%s)
  local mtime
  if stat -f %m "$file" &>/dev/null; then
    # macOS
    mtime=$(stat -f %m "$file")
  else
    # Linux
    mtime=$(stat -c %Y "$file")
  fi
  echo $(( (now - mtime) / 86400 ))
}

case "$COMMAND" in
  init)
    parse_flags "$@"
    [[ -z "$FEATURE" ]] && { echo "Error: --feature is required" >&2; exit 1; }
    [[ -z "$SLUG"    ]] && { echo "Error: --slug is required"    >&2; exit 1; }
    FILE=$(state_file "$SLUG")
    mkdir -p "$(dirname "$FILE")"
    CURRENT_PHASE="${CURRENT_PHASE:-initialized}"
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
    FILES=(.skilmarillion/projects/*/PROJECT-STATE.yaml)
    if [[ ${#FILES[@]} -eq 0 ]]; then
      echo "No plan state files found."
      exit 0
    fi
    for f in "${FILES[@]}"; do
      # Extract slug from path: .skilmarillion/projects/{slug}/PROJECT-STATE.yaml
      rel="${f#.skilmarillion/projects/}"
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
      FILES=(.skilmarillion/projects/*/PROJECT-STATE.yaml)
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
