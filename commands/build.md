---
description: TDD execution. Slice-by-slice RED/GREEN/REFACTOR from a spec, with debug and refactor modes.
argument-hint: "[--debug <issue> | --refactor <target>] [spec-or-impl-details]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - Task
  - ToolSearch
model: sonnet
---

# /fellowship:build

**STUB — ported in Phase E.**

Slice-by-slice TDD execution driven from a spec or impl-details file. Enforces RED → GREEN → REFACTOR per slice. Resumes from `PROJECT-STATE.yaml` when state is found.

Flags:
- (default) — TDD loop
- `--debug <issue>` — structured debugging (reproduce → isolate → root cause → fix)
- `--refactor <target>` — phase-gated refactoring with test verification between steps

After 3 failed attempts on a slice: diagnostic step → modified approach, sub-slice split, or ACCEPT_WITH_DEBT.
