---
description: Parallel code-quality, security, and accessibility review. Deduplicated, prioritized findings. No code changes.
argument-hint: "[--security | --a11y | --clean] [file|directory|branch|PR-number]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git show:*)
  - Bash(git status)
  - Bash(git branch:*)
  - Bash(gh pr view:*)
  - Bash(gh pr diff:*)
  - Bash(gh pr list:*)
  - ToolSearch
  - Task
model: opus
---

# /fellowship:review

**STUB — ported in Phase F.**

Spawns specialist reviewers in parallel, deduplicates findings, sorts by impact-to-effort, produces a unified report. Findings-only: never modifies code.

Flags:
- (default) — full review (code quality + security + a11y)
- `--security` — security-only
- `--a11y` — accessibility-only (WCAG 2.1/2.2, Playwright MCP when available)
- `--clean` — AI-generated noise detection

Reports saved to `.skilmarillion/projects/{slug}/reviews/`.
