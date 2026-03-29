# Skilmarillion

## Project Overview

Skilmarillion is a Claude Code plugin system organized as a lifecycle: `dream` (specify) → `draft` (design) → `do` (implement) → `discern` (review). Currently in Phase 0 — building the `dream` plugin for spec-driven planning.

## Repository Structure

- `dream/` — The spec-driven planning plugin (commands, agents, skills, references)
- `docs/planning/` — Project PRD and roadmap
- `docs/{feature}/` — Feature-grouped artifacts: PRD, roadmap, specs, plans (see `dream/skills/artifact-paths.md`)
- `test-fixtures/` — Sample app used for testing plugin commands

## Build & Test Commands

Python 3.10+ required for the validation script (stdlib only, no external dependencies).

```bash
# Validate a spec, PRD, or plan
python dream/scripts/validate.py <path> --verbose

# Validate with explicit type and JSON output
python dream/scripts/validate.py <path> --type spec|prd|plan --json

# Draft mode (relaxed threshold: 50)
python dream/scripts/validate.py <path> --draft

# Install the plugin
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
```

## Roadmap Completion Rule

When implementing a roadmap item (DREAM-NNN / P0-X), the implementing PR must update `docs/planning/ROADMAP.md` to mark that item as complete in the status section. This includes:

- Moving the item from "In Progress" or "Not Started" to "Completed" with the PR number
- Checking the item's checklist boxes if applicable
- Updating the "Last Updated" date

Do not merge a roadmap-item PR without this update.

## Plugin Development Conventions

- **Versioning:** Semver for `plugin.json` — patch for fixes, minor for new commands, major for breaking changes.
- **Command files:** YAML frontmatter (`description`, `argument-hint`, `allowed-tools`, `model`) + markdown body.
- **Artifact paths:** Deterministic, feature-grouped — `docs/{feature}/PRD.md`, `docs/{feature}/specs/SPEC-NNN-{slug}.md`. Slug confirmed with user before save. See `dream/skills/artifact-paths.md`.
- **Model tiering:** Use the minimum model that handles the task reliably. Haiku for deterministic/structured output. Sonnet for judgment and context. Opus for security/quality-critical roles.
