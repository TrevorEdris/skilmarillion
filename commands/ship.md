---
description: Conventional commit from staged changes, with optional PR description generation.
argument-hint: "[--pr] [--breaking] [--scope <scope>]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff:*)
  - Bash(git status:*)
  - Bash(git log:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git push:*)
  - Bash(git branch:*)
  - Bash(gh pr create:*)
  - Bash(gh pr view:*)
  - AskUserQuestion
model: haiku
---

# /fellowship:ship

**STUB — ported in Phase F.**

Generates a conventional commit message from staged changes. Detects breaking changes, infers type and scope, presents for user approval. Never commits without approval.

Flags:
- (default) — commit only
- `--pr` — after commit, push branch and open a PR with AC traceability
- `--breaking` — force BREAKING CHANGE footer
- `--scope <scope>` — override auto-detected scope
