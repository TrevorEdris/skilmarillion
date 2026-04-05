---
description: Read-only workflow dashboard. Active projects, current phase, spec counts, in-progress TDD state.
argument-hint: ""
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - Bash(cat:*)
model: haiku
---

# /fellowship:status

**STUB — ported in Phase C.**

Read-only dashboard. Scans `.skilmarillion/projects/*/PROJECT-STATE.yaml` and artifact directories to present a unified view of active work.

Never modifies files.
