---
description: Score a spec, PRD, or plan document for structural completeness (0-100, PASS >= 70)
argument-hint: "[path] [--type spec|prd|plan] [--draft]"
allowed-tools:
  - Read
  - Glob
  - "Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py:*)"
  - AskUserQuestion
  - ToolSearch
model: sonnet
---

# /dream:validate

Score a spec, PRD, or plan document for structural completeness. Returns a 0–100 score with actionable findings.

---

## Flow

### 1. Resolve document path

If a path argument is provided, use it directly.

If no path argument is provided:
1. Search for candidates:
   - Specs: `docs/specs/*.md`
   - PRDs: `docs/prds/*.md`
   - Plans: look in the current session directory for `PLAN.md`
2. If exactly one candidate found, use it.
3. If multiple candidates found, ask the user which one to validate (using `AskUserQuestion`).
4. If no candidates found, ask the user for a path.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Run structural validation

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py <path> --type <type> --verbose --json
```

If `--type` was not specified by the user, omit it and let the script auto-detect.

If the user passed `--draft`, include `--draft` in the command.

### 3. Parse and display results

Parse the JSON output from the script.

**If score >= 70 (PASS):**

Display:
> **PASS** — Score: {score}/100
> {summary of any warnings}

**If score < 70 (NEEDS WORK):**

Display:
> **NEEDS WORK** — Score: {score}/100
>
> **Errors:**
> - {each error with line reference}
>
> **Warnings:**
> - {each warning with line reference}
>
> Suggested fixes for the top issues.

### 4. Semantic AC quality layer (spec documents only)

For spec documents, after displaying the structural score:
1. Read each Acceptance Criterion in the document.
2. Flag any AC that is not independently testable — i.e., it depends on state produced by another AC without stating that state in its own Given clause.
3. Append any semantic findings as additional warnings in the output.

### 5. Return machine-readable result

Return the result as structured data for programmatic consumption by other commands:

```json
{ "passed": true, "score": 85, "doc_type": "spec", "findings": [...] }
```

---

## WHAT NOT TO DO

- Do NOT modify the document being validated — this command is read-only.
- Do NOT skip the structural validation script — always run it first.
- Do NOT run semantic checks on PRD or plan documents — only specs get the AC quality layer.
