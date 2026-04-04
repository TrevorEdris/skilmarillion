# plan — Spec-Driven Planning Plugin

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`plan` turns a task description into testable acceptance criteria, a vertical slice spec, and a TDD plan before any code is written. It routes by task size: a config change gets a quick confirm; a new feature gets the full interview-driven workflow.

## Standalone Entry Conditions

`plan` is the first plugin in the Skilmarillion workflow. It has no dependencies — use it with or without `arch`, `impl`, or `review` installed.

**Input:** A ROADMAP.md path, or nothing — `/plan:specify` will search for one.
**Output:** `.skilmarillion/projects/{slug}/specs/SPEC-{NNN}-{slug}.md` for each milestone, with testable ACs, vertical slices, architecture recommendation, and TDD plan.

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install plan@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/plan:help` | Interactive, context-aware tour of plan's capabilities. Detects project state and recommends a starting command. |
| `/plan:specify [roadmap-path]` | Generate all specs from a ROADMAP. Launches parallel agents per milestone. |
| `/plan:prd [feature]` | Client-shareable PRD from a plain-language description. Saves to `.skilmarillion/projects/{slug}/PRD.md`. |
| `/plan:roadmap [prd-path]` | Decompose an approved PRD into ordered milestones. Saves to `.skilmarillion/projects/{slug}/ROADMAP.md`. *(P0-I)* |
| `/plan:validate [path]` | Score a spec, PRD, or plan (0–100; PASS at ≥70). Auto-detects doc type. Supports `--draft` for relaxed threshold (50). |
| `/plan:migrate [legacy] [target]` | Prioritized migration plan as independent specs. Orders by coupling analysis (fan-in) and git hotspot data. Saves to `.skilmarillion/projects/{migration-slug}/ROADMAP.md`. |

### Standalone validation script

The validate command wraps `plan/scripts/validate.py`, which can also be run directly:

```bash
# Auto-detect doc type
python plan/scripts/validate.py .skilmarillion/projects/auth/my-feature/specs/SPEC-001-auth-flow.md --verbose

# Explicit type + JSON output
python plan/scripts/validate.py .skilmarillion/projects/auth/my-feature/PRD.md --type prd --json

# Draft mode (relaxed threshold: 50)
python plan/scripts/validate.py .skilmarillion/projects/auth/my-feature/specs/SPEC-001-wip.md --draft
```

Requires Python 3.10+ (stdlib only, no external dependencies).

## Artifact Paths

All paths are relative to the target project's git root (resolved automatically — see `artifact-paths` skill). Slugs are confirmed with the user before save.

```
{project_root}/.skilmarillion/projects/{slug}/
  PRD.md                           # /plan:prd output
  ROADMAP.md                       # /plan:roadmap output
  PROJECT-STATE.yaml               # workflow state
  specs/
    SPEC-001-{slug}.md             # /plan:specify output (auto-incrementing)
  plans/
    PLAN-001-{slug}.md             # Future /impl output (convention reserved)
```

| Command | Artifact | Path |
|---------|----------|------|
| `/plan:prd` | PRD | `.skilmarillion/projects/{slug}/PRD.md` |
| `/plan:specify` | Specs | `.skilmarillion/projects/{slug}/specs/SPEC-{NNN}-{slug}.md` |
| `/plan:roadmap` | Roadmap | `.skilmarillion/projects/{slug}/ROADMAP.md` |
| `/plan:migrate` | Migration ROADMAP + Specs | `.skilmarillion/projects/{migration-slug}/ROADMAP.md` + `.skilmarillion/projects/{migration-slug}/specs/SPEC-{NNN}-migrate-{module}.md` |

## Session Documentation Hooks

Hooks auto-register when the plugin is installed via the marketplace. If using `--plugin-dir` for local development, copy the hook config into your project's `.claude/settings.local.json`:

```bash
# Extract just the hooks block from hooks.json, replacing ${CLAUDE_PLUGIN_ROOT}
# with the absolute path to the plan plugin's hooks/ directory
```

Or merge `plan/hooks/hooks.json` into `.claude/settings.local.json` manually, replacing `${CLAUDE_PLUGIN_ROOT}` with the absolute path to `plan/`.

### What happens automatically

1. **Session start** (`SessionStart` hook) — creates `{sessions_root}/YYYY-MM/DD-HHMM_pending_{id}/SESSION.md`
2. **First prompt** (`UserPromptSubmit` hook) — renames the pending dir with a slug from your message (e.g., `28-1430_PROJ-123_Add-User-Auth/`). Extracts ticket IDs automatically.
3. **Session end** (`SessionEnd` hook) — marks `SESSION.md` as completed and appends a row to `{sessions_root}/INDEX.md`

Sessions are organized into monthly subdirectories (`YYYY-MM/`) to keep the sessions root clean.

### INDEX.md format

A global `INDEX.md` at the sessions root tracks all sessions:

```
| Date | Ticket | Title | Discovery | Plan | Session |
|------|--------|-------|-----------|------|---------|
| 2026-03-28 | PROJ-123 | Add User Auth | Y | Y | Y |
```

## Workflow Integration

```
plan/  →  .skilmarillion/projects/{slug}/specs/SPEC-NNN-{slug}.md
   ↓
impl/     →  committed branch + open PR
   ↓
review/  →  review report
```

`arch/` (architecture design) is optional and can be invoked before `plan/` when the problem space is large or the architecture is unclear.
