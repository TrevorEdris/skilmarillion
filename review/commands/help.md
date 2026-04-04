---
description: Interactive tour of review plugin capabilities. Detects open PRs, existing review reports, and Playwright MCP availability to tailor guidance.
argument-hint: ""
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - Bash(gh pr list:*)
  - Bash(gh pr view:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /review:help

Interactive, context-aware tour of the `review` plugin. Scans the project for open PRs, existing review reports, staged changes, and Playwright MCP availability, walks through each command, and recommends a starting point.

---

## ON STARTUP -- Project State Scan

Before presenting anything, scan for project state to determine context.

### 1. Detect open PRs

```bash
gh pr list --state open --json number,title,headRefName --limit 10
```

Store the count and list as `{open_prs}`.

### 2. Scan for existing review reports

```
Glob: .skilmarillion/projects/*/reviews/review-*.md
Glob: .skilmarillion/projects/*/reviews/security-*.md
Glob: .skilmarillion/projects/*/reviews/a11y-*.md
Glob: .skilmarillion/projects/*/reviews/clean-*.md
```

Store the combined count and paths as `{review_reports}`.

### 3. Detect staged changes

```bash
git diff --cached --stat
```

Store whether staged changes exist as `{has_staged_changes}`.

### 4. Detect Playwright MCP availability

Call `ToolSearch` with query `"mcp__playwright"` to check if Playwright MCP tools are available.

Store availability as `{playwright_available}` (true/false).

### 5. Detect sibling plugins

Check whether sibling lifecycle plugins are installed by looking for their manifests:

- `plan`: check for `plan/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `arch`: check for `arch/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `impl`: check for `impl/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins

Store availability as `{plugins_installed}`.

---

## GREETING -- Adapt Based on Findings

Choose one greeting based on the scan results:

### Open PRs found

> **Welcome to `/review` -- the pre-merge quality gate.**
>
> Found {N} open PR(s) on this repo. Let me walk you through the review capabilities.

### Existing review reports found but no open PRs

> **Welcome back.** Found {N} existing review report(s). Let me show you what else `review` can do.

### Fresh project (no open PRs, no review reports)

> **Welcome to `/review` -- the pre-merge quality gate.**
>
> No open PRs or existing review reports found. Let me walk you through what `review` can do.

### Playwright MCP status note

Append to the greeting:

- If `{playwright_available}` is true: "Playwright MCP detected -- `/review:a11y` can use live browser verification."
- If `{playwright_available}` is false: "Playwright MCP not detected -- `/review:a11y` will use static analysis mode."

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

After displaying the greeting, ask:

> "Want the full tour, or jump to a specific command?"
>
> 1. Full tour
> 2. Jump to a command: `review` | `clean` | `security` | `a11y`

If "Full tour": proceed through all commands in order (COMMAND TOUR section).
If a specific command is named: jump directly to that command's section in the tour.

---

## COMMAND TOUR

Walk through each command one at a time. After each command description, ask the user how to proceed before moving to the next.

### Command 1: `/review:review`

> **`/review:review [target]`** -- Full Parallel Review
>
> The main entry point. Spawns three specialist reviewers in parallel (code quality, security, accessibility), deduplicates their findings, and produces a unified report sorted by impact-to-effort ratio.
>
> Accepts: PR number, branch name, file path, or directory. If no argument is given, auto-detects an open PR on the current branch.
>
> - Leads with what is working well before surfacing issues
> - Deduplicates findings across specialists
> - Sorts by HIGH impact + LOW effort first
>
> **Example:** `/review:review 42` (reviews PR #42)
>
> **Produces:** `review-<target>.md` in the session directory

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `review`
> 3. Try `/review:review` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 2.
- If "Tell me more": explain the three specialist agents (Code Quality, Security, Accessibility), how deduplication works (Haiku-tier synthesizer collapses near-duplicates, attributes to all sources), and the report structure (What's Working, Findings sorted by impact-to-effort, Summary table). Then re-ask.
- If "Try it now": if open PRs were found in the scan, suggest using one (e.g., "Try `/review:review {pr-number}` -- you have PR #{number}: {title}"). Otherwise tell the user to provide a target. End the tour.
- If "Skip to": ask which command and jump there.

### Command 2: `/review:clean`

> **`/review:clean [target]`** -- AI Noise Detection
>
> Detects and flags AI-generated noise in code comments, docstrings, and prose. Identifies filler phrases, over-documentation, unnecessary hedging, and other patterns that signal AI-generated content.
>
> Findings only -- does not modify files.
>
> **Example:** `/review:clean src/`
>
> **Produces:** `clean-<target>.md` in the session directory

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `clean`
> 3. Try `/review:clean` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 3.
- If "Tell me more": explain the AI slop patterns detected (filler phrases like "It's worth noting", over-commented obvious code, unnecessary hedging, verbose docstrings that restate the function signature), and how findings are presented with file:line references and severity ratings. Then re-ask.
- If "Try it now": tell the user to run `/review:clean` with a file or directory path. End the tour.
- If "Skip to": ask which command and jump there.

### Command 3: `/review:security`

> **`/review:security [target]`** -- Security-Focused Review
>
> Identifies vulnerabilities with >80% confidence of real exploitation potential. Every finding requires a concrete exploitation chain -- no theoretical CWE-number fishing.
>
> Accepts: PR number, file path, or directory.
>
> **Example:** `/review:security src/api/`
>
> **Produces:** `security-<target>.md` in the session directory

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `security`
> 3. Try `/review:security` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 4.
- If "Tell me more": explain the >80% confidence threshold, the exploitation chain requirement (attacker → entry point → vulnerability → impact), severity mapping, and how the command avoids false positives by requiring real exploit potential. Then re-ask.
- If "Try it now": tell the user to run `/review:security` with a target. End the tour.
- If "Skip to": ask which command and jump there.

### Command 4: `/review:a11y`

> **`/review:a11y [target]`** -- Accessibility Audit
>
> WCAG 2.1/2.2 accessibility audit. Maps findings to specific success criteria with severity ratings (critical, serious, moderate, minor).
>
> **Two modes:**
> - **Live browser** (when Playwright MCP is available + dev server confirmed): navigates to the running app, takes accessibility tree snapshots, checks color contrast, verifies keyboard focus order
> - **Static analysis** (fallback): analyzes source code and component definitions for WCAG violations

Append mode status based on the startup scan:

- If `{playwright_available}` is true: "Currently available: **live browser mode**."
- If `{playwright_available}` is false: "Currently available: **static analysis mode** (install Playwright MCP for live browser verification)."

> **Example:** `/review:a11y http://localhost:3000`
>
> **Produces:** `a11y-<target>.md` in the session directory

Ask (using `AskUserQuestion`):

> "That covers all four commands. Ready for a recommendation, or have questions?"
>
> 1. Give me a recommendation
> 2. Go back to a command
> 3. I'm good -- end tour

- If "Give me a recommendation": proceed to RECOMMENDATION section.
- If "Go back to a command": ask which and jump there.
- If "End tour": display the closing message and stop.

---

## RECOMMENDATION -- Starting Command

Based on the project state scan, recommend the best starting command:

### If open PRs exist

> **Recommendation:** You have open PRs. Start with `/review:review {pr-number}` to run a full review on a PR before merging.

If multiple open PRs were found, list them:

> Open PRs:
> {list of PR numbers and titles}
>
> Pick one and run `/review:review {number}`.

### If no open PRs but staged changes exist

> **Recommendation:** You have staged changes but no open PR. Run `/review:clean` or `/review:security` on the changed files before committing.

### If existing review reports exist

> **Recommendation:** You have prior review reports. Run `/review:review` on new changes, or re-run on previously reviewed code to check if findings were addressed.

### If nothing exists (no open PRs, no reports, no staged changes)

> **Recommendation:** No open PRs or review targets found. When you have code ready for review:
> - Open a PR and run `/review:review {pr-number}` for a full review.
> - Run `/review:security {path}` or `/review:clean {path}` on any file or directory.

---

## UPSTREAM / DOWNSTREAM PLUGIN REFERENCES

After the recommendation, reference upstream plugins with install hints if not present.

### Upstream: `impl`

#### If `impl` is installed

> **Upstream:** Implementation comes from `/impl:tdd`. Run `/impl:help` for a tour of implementation capabilities.

#### If `impl` is NOT installed

> **Tip:** The `impl` plugin drives TDD implementation that produces reviewable code. Install it for spec-driven implementation:
> ```
> /plugin install impl@skilmarillion
> ```

### Upstream: `arch`

#### If `arch` is installed

> **Upstream:** Architecture decisions come from `/arch:design`. Run `/arch:help` for a tour of design capabilities.

#### If `arch` is NOT installed

> **Tip:** The `arch` plugin documents architecture decisions before implementation. Install it for structured design:
> ```
> /plugin install arch@skilmarillion
> ```

### Upstream: `plan`

#### If `plan` is installed

> **Upstream:** Specs originate from `/plan:sdd`. Run `/plan:help` for a tour of planning capabilities.

#### If `plan` is NOT installed

> **Tip:** The `plan` plugin generates specs that drive the full lifecycle. Install it for spec-driven planning:
> ```
> /plugin install plan@skilmarillion
> ```

---

## CLOSING

> Run any command to get started. You can return here anytime with `/review:help`.

---

## WHAT NOT TO DO

- Do NOT modify any files -- this command is entirely read-only.
- Do NOT create state files -- this is an informational tour only.
- Do NOT skip the project state scan -- the greeting and recommendation depend on it.
- Do NOT present all commands at once -- walk through them one at a time with navigation between each.
- Do NOT assume plugin availability -- always check before referencing upstream plugins.
- Do NOT assume Playwright MCP is available -- always check via ToolSearch.
