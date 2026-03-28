# dream — Spec-Driven Planning Plugin

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`dream` turns a task description into testable acceptance criteria, a vertical slice spec, and a TDD plan before any code is written. It routes by task size: a config change gets a quick confirm; a new feature gets the full interview-driven workflow.

## Standalone Entry Conditions

`dream` is the first plugin in the Skilmarillion workflow. It has no dependencies — use it with or without `draft`, `do`, or `discern` installed.

**Input:** A task description (plain language), or nothing — `/dream:sdd` will ask.
**Output:** `docs/{feature}/specs/SPEC-{NNN}-{slug}.md` with testable ACs, vertical slices, architecture recommendation, and TDD plan.

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install dream@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/dream:sdd [task]` | Full spec-driven workflow. Routes by size (TRIVIAL → quick confirm; FEATURE → full workflow). |
| `/dream:prd [feature]` | Client-shareable PRD from a plain-language description. Saves to `docs/{feature}/PRD.md`. |
| `/dream:validate [path]` | Score a spec, PRD, or plan (0–100; PASS at ≥70). Auto-detects doc type. Supports `--draft` for relaxed threshold (50). |
| `/dream:migrate [legacy] [target]` | Prioritized migration plan as independent specs. *(P0-H)* |

### Standalone validation script

The validate command wraps `dream/scripts/validate.py`, which can also be run directly:

```bash
# Auto-detect doc type
python dream/scripts/validate.py docs/my-feature/specs/SPEC-001-auth-flow.md --verbose

# Explicit type + JSON output
python dream/scripts/validate.py docs/my-feature/PRD.md --type prd --json

# Draft mode (relaxed threshold: 50)
python dream/scripts/validate.py docs/my-feature/specs/SPEC-001-wip.md --draft
```

Requires Python 3.10+ (stdlib only, no external dependencies).

## Artifact Paths

All paths are relative to the target project's git root (resolved automatically — see `artifact-paths` skill). Slugs are confirmed with the user before save.

```
{project_root}/docs/{feature}/
  PRD.md                           # /dream:prd output
  ROADMAP.md                       # Epic decomposition or manual roadmap
  specs/
    SPEC-001-{slug}.md             # /dream:sdd output (auto-incrementing)
  plans/
    PLAN-001-{slug}.md             # Future /do output (convention reserved)
```

| Command | Artifact | Path |
|---------|----------|------|
| `/dream:prd` | PRD | `docs/{feature}/PRD.md` |
| `/dream:sdd` (FEATURE/SMALL) | Spec | `docs/{feature}/specs/SPEC-{NNN}-{slug}.md` |
| `/dream:sdd` (EPIC) | Roadmap | `docs/{feature}/ROADMAP.md` |

## Session Documentation Hooks

Hooks auto-register when the plugin is installed via the marketplace. If using `--plugin-dir` for local development, copy the hook config into your project's `.claude/settings.local.json`:

```bash
# Extract just the hooks block from hooks.json, replacing ${CLAUDE_PLUGIN_ROOT}
# with the absolute path to the dream plugin's hooks/ directory
```

Or merge `dream/hooks/hooks.json` into `.claude/settings.local.json` manually, replacing `${CLAUDE_PLUGIN_ROOT}` with the absolute path to `dream/`.

### What happens automatically

1. **Session start** (`SessionStart` hook) — creates `{sessions_root}/YYYY-MM/DD-HHMM_pending_{id}/SESSION.md`
2. **First prompt** (`UserPromptSubmit` hook) — renames the pending dir with a slug from your message (e.g., `28-1430_PROJ-123_Add-User-Auth/`). Extracts ticket IDs automatically.
3. **Session end** (`SessionEnd` hook) — marks `SESSION.md` as completed and appends a row to `{sessions_root}/INDEX.md`

Sessions are organized into monthly subdirectories (`YYYY-MM/`) to keep the sessions root clean.

### Configuration

Set `SKILMARILLION_SESSIONS_DIR` to override the default sessions root (`$CLAUDE_PROJECT_DIR/.ai/sessions`):

```bash
# In your shell or .env
export SKILMARILLION_SESSIONS_DIR="/path/to/your/vault/sessions"
```

### INDEX.md format

A global `INDEX.md` at the sessions root tracks all sessions:

```
| Date | Ticket | Title | Discovery | Plan | Session |
|------|--------|-------|-----------|------|---------|
| 2026-03-28 | PROJ-123 | Add User Auth | Y | Y | Y |
```

## Workflow Integration

```
dream/  →  docs/{feature}/specs/SPEC-NNN-{slug}.md
   ↓
do/     →  committed branch + open PR
   ↓
discern/  →  review report
```

`draft/` (architecture design) is optional and can be invoked before `dream/` when the problem space is large or the architecture is unclear.
