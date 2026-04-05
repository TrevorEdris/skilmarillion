# /fellowship:review --clean

Identify and flag AI-generated noise in code. Every comment, docstring, and prose paragraph must earn its place. If removing it loses no information, it is slop.

**Rule: findings only, no code edits.** This command produces a report. The user decides what to fix.

---

## Flow

### 1. Resolve target

If a PR number is provided: extract changed files via `git diff`.

```bash
git diff --name-only origin/main...HEAD
```

If a file path is provided: use it directly.

If a directory is provided: scan all source files in it.

If no argument is provided: check for staged or recent changes.

```bash
git diff --name-only --cached
```

If still nothing: ask the user to provide a target path or PR number.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Scan each file

For every target file, read its contents and check every comment, docstring, and prose paragraph against the noise categories below. Classify each finding by severity and confidence.

**Confidence gate: only report findings with >90% confidence of being noise.** When in doubt, do not flag. It is better to miss one piece of slop than to flag a legitimate comment.

### 3. Noise categories

#### Comment slop (detect in comments and docstrings)

| Pattern | Description | Severity |
|---------|-------------|----------|
| Narrator comments | Restate function/method name: "This function processes the user request" above `processUserRequest()` | CRITICAL |
| Obvious comments | Restate the code: `counter += 1 # Increment counter` | CRITICAL |
| Section dividers | Decorative separators: `# ===== MAIN LOGIC =====` | HIGH |
| Step comments | Procedural narration: "Step 1: Validate", "First, we...", "Next, we..." | HIGH |
| Over-documented trivials | Multi-line docstring on a one-liner where the type signature says everything | HIGH |
| Language tutorial comments | Explain what a for-loop or dictionary is | CRITICAL |
| Redundant type docs | `@param {string} name` when the type signature already has `name: string` | HIGH |
| Apologetic comments | "This shouldn't happen but just in case", "This might not be the best approach" | MEDIUM |
| Placeholder comments | "TODO: implement", "Add your logic here", "Replace with actual" | CRITICAL |

#### Code pattern slop (detect in the code itself)

| Pattern | Description | Severity |
|---------|-------------|----------|
| Unnecessary try-catch | Wrapping code that cannot throw (dict access on known keys, arithmetic, string ops) | HIGH |
| Defensive impossible-case handling | Null checks on non-optional params, type guards on already-typed values | HIGH |
| Empty/silent catch blocks | Catch errors and do nothing or just log | HIGH |
| Single-use constants | `MAGIC_OFFSET = 1` used once, name restates the value | LOW |

#### Prose slop (detect in markdown, docstrings, README content)

| Pattern | Description | Severity |
|---------|-------------|----------|
| Filler openers | "It's worth noting that...", "Let's dive in", "In order to..." | HIGH |
| AI vocabulary | robust, leverage, seamless, comprehensive, cutting-edge, streamlined | MEDIUM |
| Promotional adjectives | groundbreaking, revolutionary, state-of-the-art, powerful, elegant | HIGH |
| Hedging language | "One might argue...", "It could be said...", "In some cases, it may be possible to..." | MEDIUM |
| Idea repetition | Same concept restated in different words across paragraphs | HIGH |
| Buzzword-stuffed docstrings | Function docs full of "robust", "comprehensive", "leverages" | HIGH |

### 4. Distinguish signal from noise

**NOT slop (leave these alone):**

- Comments explaining *why* — business logic, performance decisions, external system behavior, security rationale, non-obvious implementation details
- Try-catch around external API calls, file I/O with user-provided paths, deserialization of external data
- Comments explaining specific failure modes: "API has 99.9% uptime but we've seen transient failures"
- Domain-specific terminology that happens to overlap with the AI vocabulary list
- TODOs with ticket references or specific context: `// TODO(PROJ-123): migrate to v2 endpoint after deprecation`

When a comment has both signal and noise (verbose but contains real information), classify as MEDIUM and suggest a concise rewrite that preserves the signal.

### 5. Format findings

For every finding, include ALL of:

1. **File location** — `filename:line`
2. **Quoted text** — the exact slop text
3. **Pattern** — which noise category it matches
4. **Severity** — CRITICAL, HIGH, MEDIUM, or LOW
5. **Confidence** — percentage (only findings >90% reported)
6. **Suggested fix** — concrete replacement text OR "Delete entirely"

Group findings by severity (CRITICAL first, then HIGH, MEDIUM, LOW).

### 6. Clean input handling

If the target has no slop, report exactly:

> Clean run. No noise patterns detected above the 90% confidence threshold.

Do NOT invent problems to fill a report.

### 7. Produce report

Save the report to the `.skilmarillion/` output directory:

```
.skilmarillion/projects/{slug}/reviews/clean-{target}.md
```

Report structure:

```markdown
# Clean Report: <target>

**Date:** YYYY-MM-DD
**Files scanned:** N
**Findings:** N (X critical, Y high, Z medium, W low)
**Confidence threshold:** 90%

## Summary

<1-2 sentence overview>

## Findings

### CRITICAL

- **<file>:<line>** — `<quoted text>`
  Pattern: <category>. Confidence: <N>%.
  Fix: <replacement or "Delete entirely">

### HIGH

...

### MEDIUM

...

### LOW

...
```

### 8. Summary statistics

End the report with:

```markdown
## Statistics

| Severity | Count |
|----------|-------|
| CRITICAL | N |
| HIGH | N |
| MEDIUM | N |
| LOW | N |
| **Total** | **N** |

Lines of noise identified: N
Estimated signal-to-noise improvement: <percentage of comment/doc lines that are noise>
```

---

## WHAT NOT TO DO

- Do NOT modify any file — this command is read-only, findings only.
- Do NOT flag comments that explain *why* — only flag comments that restate *what*.
- Do NOT report findings below 90% confidence — silence is preferable to false positives.
- Do NOT flag defensive code at system boundaries (external APIs, user input, deserialization).
- Do NOT flag TODOs that reference tickets or contain specific context.
- Do NOT use Write or Edit tools under any circumstances.

---

## NEXT STEP BREADCRUMB

After displaying the report:

- If findings exist: "To address these findings, run `/fellowship:build --debug` or `/fellowship:build --refactor` on the flagged files."
- If clean: "No action needed. The code is clean."
- 
