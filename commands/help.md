---
description: Interactive tour. Detects project state and recommends the next command. Accepts a task description for routing.
argument-hint: "[task description | --phase plan|build|review]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /fellowship:help

**STUB — ported in Phase C.**

Interactive, context-aware tour of the fellowship plugin. Detects existing project state and recommends a starting command.

When called with a task description, classifies intent (plan / build / review / ship) and **prints the recommended command** — does not auto-run it.

Flags:
- (no arg) — full tour
- `[task description]` — classify and recommend
- `--phase plan|build|review` — scoped tour of one phase
