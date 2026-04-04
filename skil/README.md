# skil -- Workflow Router & Discovery Layer

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`skil` is the entry point to the Skilmarillion plugin suite. It routes task descriptions to the right lifecycle plugin, provides guided discovery of available commands, and shows workflow state across installed plugins. It does no real work itself -- it delegates to `plan`, `arch`, `impl`, and `review`.

## Standalone Entry Conditions

`skil` has no dependencies on other Skilmarillion plugins. Install it first to discover the full suite. It works with any combination of lifecycle plugins installed (or none).

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install skil@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/skil:help` | Interactive tour of the full suite. Detects installed plugins and project state. |
| `/skil [task]` | Route a task description to the appropriate lifecycle plugin command. |
| `/skil:status` | Workflow state dashboard across all installed plugins. |

## Recommended Install Order

1. `skil` -- Discovery and routing (install first)
2. `plan` -- Spec-driven planning (start here for new features)
3. `arch` -- Architecture and design (optional, for complex systems)
4. `impl` -- TDD implementation (execute specs from `plan`)
5. `review` -- Code review and quality audits (gate before merge)

## Workflow Integration

```
skil  -->  routes to the right plugin
  |
  +--> plan/   -->  .skilmarillion/projects/{slug}/specs/SPEC-NNN-{slug}.md
  +--> arch/   -->  .skilmarillion/projects/{slug}/adrs/NNN-{slug}.md
  +--> impl/   -->  committed branch + open PR
  +--> review/ -->  review report
```
