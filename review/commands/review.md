---
description: Full parallel review -- spawns code quality, security, and accessibility specialists, deduplicates findings, and produces a unified report
argument-hint: "[file|directory|branch|PR-number]"
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
  - SubAgent
model: opus
---

# /review:review

Spawn three specialist reviewer agents in parallel, deduplicate their findings, and produce a unified report sorted by impact-to-effort ratio. Lead with what is working well before surfacing issues.

**Rule: findings only, no code edits.** This command produces a report. It never proposes or applies code changes.

---

## Flow

### 1. Resolve target

Determine what code to review based on the argument provided.

**PR number provided:**

```bash
gh pr diff <number> --name-only
```

Extract the diff for review context:

```bash
gh pr diff <number>
```

**Branch name provided:**

```bash
git diff --name-only origin/main...<branch>
```

**File or directory path provided:** Use directly.

**No argument provided:** Check for an open PR on the current branch:

```bash
gh pr view --json number,title,headRefName 2>/dev/null
```

If a PR exists, use it. If not, check for staged or recent changes:

```bash
git diff --name-only --cached
git diff --name-only origin/main...HEAD
```

If still nothing: display the following message and offer choices:

> Nothing to review. Provide a file path, PR number, or stage changes first.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

Use `AskUserQuestion` to present the following choices:
1. **Review a specific file** -- prompt the user for a file or directory path, then restart from step 1 with that path.
2. **Review latest PR** -- run `gh pr list --state open --limit 1 --json number,title` to find the most recent open PR and use it as the target. If no open PR exists, report "No open PRs found" and return to the choices.
3. **Cancel** -- exit cleanly with no report.

### 2. Gather context

For the resolved target, collect:

1. **File list** -- all files in scope
2. **Diff content** -- the actual changes (for PR/branch targets)
3. **PR metadata** -- title, description, author (for PR targets)
4. **Commit history** -- commit messages for the target (for PR/branch targets)

```bash
gh pr view --json title,body,author,headRefName,additions,deletions 2>/dev/null
```

```bash
gh pr view --json commits --jq '.commits[].messageHeadline' 2>/dev/null || git log --oneline origin/main...HEAD
```

### 3. Spawn specialist agents in parallel

Launch three specialist agents simultaneously. Each agent receives the same target context and produces structured findings.

> **Deferred tool note:** Before spawning agents, call `ToolSearch` with query `"select:SubAgent"` to load the tool schema.

**Agent 1: Code Quality** (`review/agents/code-quality.md`)
- Focus: architecture, design patterns, naming, complexity, duplication, correctness
- Model tier: Opus
- Tool access: Read, Glob, Grep, Bash (read-only git/gh commands only)

**Agent 2: Security** (`review/agents/security.md`)
- Focus: vulnerabilities with >80% confidence of real exploitation potential
- Model tier: Opus
- Tool access: Read, Glob, Grep, Bash (read-only git/gh commands only)

**Agent 3: Accessibility** (`review/agents/accessibility.md`)
- Focus: WCAG 2.1/2.2 audit with severity ratings
- Model tier: Opus
- Tool access: Read, Glob, Grep, Bash (read-only git/gh commands only), Playwright MCP (when available)

Each agent MUST return findings in this structured format:

```markdown
## Findings

### <SEVERITY>

- **<file>:<line>** -- <description>
  Category: <category>
  Impact: <HIGH|MEDIUM|LOW>
  Effort to fix: <HIGH|MEDIUM|LOW>
  Suggested action: <specific actionable fix>
```

Each agent MUST also return a "What's Working" section:

```markdown
## What's Working

- <positive observation with file reference>
```

### 4. Deduplicate and synthesize

After all three agents return, pass their combined output to the deduplication synthesizer (`review/agents/dedup-synthesizer.md`).

The synthesizer is a **tool-free** step. It receives the structured output from all three agents as input and produces the final report. It does NOT access the codebase.

Model tier: Haiku

The synthesizer:

1. **Collapses near-duplicate findings** -- normalize descriptions, merge findings that reference the same code location or pattern. Attribute to all sources that flagged it.
2. **Computes impact-to-effort ratio** -- sort by HIGH impact + LOW effort first, then HIGH impact + HIGH effort, then MEDIUM impact + LOW effort, etc.
3. **Merges "What's Working" sections** -- deduplicate positive observations across agents.
4. **Produces the final report** in the structure defined below.

### 5. Format report

The final report follows this structure:

```markdown
# Review Report: <target>

**Date:** YYYY-MM-DD
**Target:** <PR #N / branch / file path>
**Files reviewed:** N
**Specialists:** Code Quality, Security, Accessibility

---

## What's Working

- <positive observation>
- <positive observation>

---

## Findings

Sorted by impact-to-effort ratio (HIGH impact, LOW effort first).

### 1. <Title>

- **Location:** `<file>:<line>`
- **Category:** <Code Quality | Security | Accessibility>
- **Severity:** <CRITICAL | HIGH | MEDIUM | LOW>
- **Impact:** <HIGH | MEDIUM | LOW>
- **Effort:** <HIGH | MEDIUM | LOW>
- **Source:** <which specialist(s) flagged this>
- **Description:** <what the issue is and why it matters>
- **Suggested action:** <specific, actionable fix>

### 2. <Title>

...

---

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |
| **Total** | **N** |

**Overall assessment:** <1-2 sentence assessment>
```

### 6. Save report

Save the report to the active session directory:

```
${SKILMARILLION_SESSIONS_DIR:-.ai/sessions}/YYYY-MM-DD_<slug>/review-<target>.md
```

Where `<target>` is the PR number, branch name, or file/directory name (sanitized for filenames).

### 7. Clean input handling

If all three specialists return no findings, report exactly:

> Clean run. No issues found above confidence thresholds. All specialists report clean.

Display the "What's Working" section even when no issues are found.

---

## WHAT NOT TO DO

- Do NOT modify any file -- this command is read-only, findings only.
- Do NOT propose code changes, patches, or diffs as part of the output.
- Do NOT use Write or Edit tools under any circumstances.
- Do NOT spawn agents with Write or Edit tool access.
- Do NOT lower confidence thresholds to fill a report -- silence is preferable to false positives.
- Do NOT report theoretical concerns without a concrete impact path.

---

## NEXT STEP BREADCRUMB

After displaying the report:

- If CRITICAL or HIGH findings exist: "To address these findings, run `/impl:debug` or `/impl:refactor` on the flagged files."
- If only MEDIUM/LOW findings: "Minor findings detected. Address at your discretion or proceed to merge."
- If clean: "Clean run. No action needed."
- If `impl` plugin is not installed, include: "Install the impl plugin: `/plugin install impl@skilmarillion`"
