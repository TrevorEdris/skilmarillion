# dream — Spec-Driven Planning Plugin

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`dream` turns a task description into testable acceptance criteria, a vertical slice spec, and a TDD plan before any code is written. It routes by task size: a config change gets a quick confirm; a new feature gets the full interview-driven workflow.

## Standalone Entry Conditions

`dream` is the first plugin in the Skilmarillion workflow. It has no dependencies — use it with or without `draft`, `do`, or `discern` installed.

**Input:** A task description (plain language), or nothing — `/dream:sdd` will ask.
**Output:** `docs/specs/[feature]-spec.md` with testable ACs, vertical slices, architecture recommendation, and TDD plan.

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install dream@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/dream:sdd [task]` | Full spec-driven workflow. Routes by size (TRIVIAL → quick confirm; FEATURE → full workflow). |
| `/dream:prd [feature]` | Client-shareable PRD from a plain-language description. Saves to `docs/prds/`. |
| `/dream:validate [path]` | Score a spec, PRD, or plan (0–100; PASS at ≥70). |
| `/dream:migrate [legacy] [target]` | Prioritized migration plan as independent specs. *(P0-H)* |

## Artifact Paths

| Artifact | Path |
|----------|------|
| Spec | `docs/specs/[feature-name]-spec.md` |
| PRD | `docs/prds/[feature-name]-prd.md` |

## Session Documentation Hooks (Optional)

To enable automatic session tracking, add these hooks to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-end.sh"
      }
    ]
  },
  "env": {
    "SKILMARILLION_SESSIONS_DIR": ".ai/sessions"
  }
}
```

Set `SKILMARILLION_SESSIONS_DIR` to redirect session docs — e.g., to an Obsidian vault:
```json
"SKILMARILLION_SESSIONS_DIR": "/path/to/your/vault/sessions"
```

> **Note:** Hook scripts (`hooks/session-start.sh`, `hooks/session-end.sh`) are implemented in P0-F.

## Workflow Integration

```
dream/  →  docs/specs/[feature]-spec.md
   ↓
do/     →  committed branch + open PR
   ↓
discern/  →  review report
```

`draft/` (architecture design) is optional and can be invoked before `dream/` when the problem space is large or the architecture is unclear.
