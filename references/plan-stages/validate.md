# /fellowship:plan --validate

Score a spec or PRD document for structural completeness. Returns a 0–100 score with actionable findings.

---

## Flow

### 1. Resolve document path

Determine the artifact type from user input. If the user specifies `--type <spec|prd|roadmap>`, use that. Otherwise, infer from the argument (SPEC-W{N}{letter} → spec, path containing `/specs/` → spec, path ending in `PRD.md` → prd, path ending in `ROADMAP.md` → roadmap). If ambiguous, ask the user.

Delegate discovery to the `artifact-resolver` agent. See `artifact-paths` skill § "Artifact Resolution" for the calling contract.

```
Task: artifact-resolver agent
Input: {
  "artifact_type": "{inferred type}",
  "query": "{raw argument or empty string}",
  "project_root": "{resolved project root}"
}
```

Confirm the selected document with the user per the caller flow in the `artifact-paths` skill — present candidates via `AskUserQuestion` for every `match_type` and wait for explicit selection.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Run structural validation

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py <path> --type <type> --verbose --json
```

If `--type` was not specified by the user, omit it and let the script auto-detect.

If the user passed `--draft`, include `--draft` in the command.

### 3. Parse and display results

Parse the JSON output from the script. The `threshold` field tells you the PASS bar (85 for all types, 50 with `--draft`).

**If score >= threshold (PASS):**

Display:
> **PASS** — Score: {score}/100
> {summary of any warnings}

**If score < threshold (NEEDS WORK):**

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
- Do NOT run semantic checks on PRD documents — only specs get the AC quality layer.

---

## NEXT STEP BREADCRUMB

After displaying validation results, suggest the logical next command based on document type:

- **Spec (PASS):** "Ready for implementation. Run `/fellowship:build spec W{N}{letter}` (or pass the spec path) to begin the TDD cycle."
- **PRD (PASS):** "PRD is valid. Run `/fellowship:plan --roadmap {prd-path}` to decompose into phases and waves."
- **Any (NEEDS WORK):** "Fix the findings above, then re-run `/fellowship:plan --validate {path}` to confirm."
