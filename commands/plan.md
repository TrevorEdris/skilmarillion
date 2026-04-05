---
description: Spec-driven planning. Runs PRD to ROADMAP to specs pipeline, or individual stages via flags.
argument-hint: "[--prd | --roadmap | --specify | --migrate | --validate | --arch <type>] [input]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh:*)"
  - "Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
model: sonnet
---

# /fellowship:plan

**STUB — ported in Phase D.**

Spec-driven planning. Default flow: PRD → ROADMAP → Specs. Flag-driven stages:

- `--prd` — produce a client-shareable PRD
- `--roadmap` — decompose an approved PRD into ordered milestones
- `--specify` — generate SPEC files from a ROADMAP using parallel agents
- `--migrate` — produce a prioritized migration plan
- `--validate [path]` — score a PRD, spec, or plan (0-100; PASS at ≥70)
- `--arch <adr|api|schema|diagram>` — design-session artifacts

All outputs land under `.skilmarillion/projects/{slug}/`.
