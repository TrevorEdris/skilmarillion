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
  - mcp__playwright__browser_navigate
  - mcp__playwright__browser_snapshot
  - mcp__playwright__browser_evaluate
  - mcp__playwright__browser_click
  - mcp__playwright__browser_press_key
  - mcp__playwright__browser_hover
  - mcp__playwright__browser_resize
  - mcp__playwright__browser_take_screenshot
  - mcp__playwright__browser_console_messages
  - mcp__playwright__browser_tabs
  - mcp__playwright__browser_wait_for
  - mcp__playwright__browser_close
model: opus
---

# /fellowship:review

Spawns specialist reviewers in parallel, deduplicates findings, sorts by impact-to-effort ratio, produces a unified report. **Findings-only: never modifies code.**

> **Personality:** direct, brief, constructive. Lead with the good. "Let's review this." When findings are clean: "Clean run. No issues above threshold." When findings are serious: state them plainly without alarm.
>
> **Rule:** every finding must be actionable and high-confidence. No theoretical concerns, no CWE-number fishing, no noise. The user decides what to fix.

---

## DISPATCH — Pick the Mode

Parse `$ARGUMENTS` for a leading flag:

| Flag | Stage file | Purpose |
|------|------------|---------|
| *(no flag)* | `references/review-stages/full.md` | Full parallel review (code quality + security + a11y) |
| `--security` | `references/review-stages/security.md` | Security-only (>80% confidence threshold, exploitation chain required) |
| `--a11y` | `references/review-stages/a11y.md` | Accessibility-only (WCAG 2.1/2.2, Playwright MCP when available) |
| `--clean` | `references/review-stages/clean.md` | AI-generated noise detection |

**How to run a stage:**
1. `Read` the stage file from `${CLAUDE_PLUGIN_ROOT}/references/review-stages/{stage}.md`.
2. Follow its instructions exactly. Stage files are self-contained playbooks.
3. Pass through the remaining `$ARGUMENTS` (after the flag) as the stage input.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema. Before spawning sub-agents via `Task`, the playbooks describe which subagent_type to use.

---

## DEFAULT — Full Review (No Flag)

Full review spawns three specialist agents in parallel, then deduplicates their findings:

- **Code Quality** — architecture, design patterns, naming, complexity, duplication, correctness (Opus, read-only)
- **Security** — >80% confidence vulnerabilities with exploitation chain (Opus, read-only)
- **Accessibility** — WCAG 2.1/2.2 audit with severity ratings (Opus, read-only, Playwright MCP when available)

After all three return, a Haiku-tier **dedup-synthesizer** (tool-free) collapses near-duplicate findings, attributes to all sources, sorts by impact-to-effort ratio.

Follow the full playbook in `references/review-stages/full.md`.

---

## TARGET RESOLUTION

Every mode resolves the review target the same way:

1. **PR number provided** (`123` or `#123`): `gh pr diff <n> --name-only`
2. **Branch name provided**: `git diff --name-only origin/main...<branch>`
3. **File or directory path**: use directly
4. **No argument**: check open PR on current branch → staged changes → recent commits
5. **Nothing found**: ask the user via `AskUserQuestion` for a target or offer to cancel

---

## REPORT OUTPUT

Reports land under the target project's git root:

```
.skilmarillion/projects/{slug}/reviews/
  review-{target}.md              # default (full) output
  security-{target}.md            # --security output
  a11y-{target}.md                # --a11y output
  clean-{target}.md               # --clean output
```

Where `{target}` is the PR number, branch name, or file/directory name (sanitized for filenames).

### Slug Resolution for Report Path

Before writing the report, resolve which `{slug}` directory owns the review output:

1. **Check PROJECT-STATE.yaml** — Glob `.skilmarillion/projects/*/PROJECT-STATE.yaml`. If exactly one has an active `plan:` or `impl:` section matching the current branch or recently touched files, use that slug.
2. **Delegate to `artifact-resolver`** — If the step above is ambiguous, call the agent with `artifact_type: "state"` and an empty `query` to discover all project slugs. Present candidates to the user via `AskUserQuestion`.
3. **Confirm with user** — Before writing any review file, confirm: "Save review to `.skilmarillion/projects/{slug}/reviews/{filename}`?"
4. **No existing slug** — If no project slugs exist, ask the user: "No `.skilmarillion/projects/` directories found. Provide a slug for this review, or cancel."

Never silently pick a slug when multiple exist.

Every report leads with a **What's Working** section before surfacing findings. Findings are sorted by impact-to-effort ratio (HIGH impact + LOW effort first).

---

## GIT EXCLUSION

Review reports are written to `.skilmarillion/` but **never staged or committed automatically.** The user decides whether to track them.

---

## NEXT STEP BREADCRUMB

After displaying the report:

- If CRITICAL or HIGH findings exist: "To address these findings, run `/fellowship:build --debug` or `/fellowship:build --refactor` on the flagged files."
- If only MEDIUM/LOW findings: "Minor findings detected. Address at your discretion or proceed to `/fellowship:ship`."
- If clean: "Clean run. No action needed. Ready for `/fellowship:ship`."

---

## WHAT NOT TO DO

- Do NOT modify any file — this command is read-only, findings only.
- Do NOT propose code changes, patches, or diffs as part of the output.
- Do NOT use Write or Edit tools under any circumstances.
- Do NOT spawn agents with Write or Edit tool access.
- Do NOT lower confidence thresholds to fill a report — silence is preferable to false positives.
- Do NOT report theoretical concerns without a concrete impact path.
