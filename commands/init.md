---
description: Bootstrap the .skilmarillion/projects/ scaffolding for a target project. Idempotent.
argument-hint: "[project-slug]"
allowed-tools:
  - Read
  - Write
  - Glob
  - Bash(mkdir:*)
  - Bash(ls:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /fellowship:init

**STUB — ported in Phase A finalization.** Bootstraps the `.skilmarillion/projects/{slug}/` directory tree at a target project's git root. Creates empty scaffold directories (`specs/`, `adrs/`, `plans/`, `reviews/`, `diagrams/`) and an initial `PROJECT-STATE.yaml`.

Safe to re-run. Only creates what is missing. Never overwrites.
