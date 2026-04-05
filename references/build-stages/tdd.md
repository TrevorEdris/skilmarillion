# /fellowship:build

Execute slice-by-slice TDD from a spec or impl-details file. The primary `impl` command.

---

## ON STARTUP

### 1. Check for In-Progress State

Look for `.skilmarillion/projects/*/*/PROJECT-STATE.yaml` files that contain an `impl` section.

If found:
- Parse each file for `slug`, `current_slice`, `total_slices`, `phase` (red/green/refactor)
- Ask the user via `AskUserQuestion`:

  > "Found in-progress TDD state for '{slug}' (slice {current_slice}/{total_slices}, phase: {phase}). Resume or start fresh?"
  >
  > Options: **"Resume"** / **"Start fresh"** / **"Abort"**

- **Resume:** Load the state and jump to the recorded slice and phase.
- **Start fresh:** Delete the state file, proceed to Input Detection.
- **Abort:** Exit.

### 2. Input Detection

Inspect the argument passed to `/fellowship:build`:

- **No argument:** Check for specs in `docs/` — if found, list them and ask the user to pick. If no specs exist, display the precondition guard:
  > "No spec found. Run `/fellowship:plan [task]` to create one, or provide a spec path."

  Use `AskUserQuestion` to offer choices:
  1. "Run /fellowship:plan now" — hand off to the plan plugin
  2. "Provide a spec path" — prompt for a file path, then resume
  3. "Proceed without spec" — continue without a spec (advanced users)

  This guard is **informational, not blocking** — the user can always choose option 3 to proceed.

- **Argument is a file path:** Read the file and classify by content markers:
  - **Spec file:** Contains `## Acceptance Criteria` AND (`## Vertical Slices` OR `## Slice `)
  - **Impl details file:** Contains `## Implementation Steps` OR `## Ordered Implementation Steps`
  - **Neither:** Display error: "This file does not look like a spec or impl-details file. Expected sections: '## Acceptance Criteria' + '## Vertical Slices' (spec) or '## Implementation Steps' (impl details)."

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## PATH A: Spec Input

When the input is a spec file, translate it to impl details before executing.

### A1. Parse the Spec

Extract from the spec:
- **Slices:** Each `## Slice N: [Name]` section
- **ACs per slice:** Each `AC-N.M:` line within a slice
- **TDD Plan:** If a `## TDD Plan` section exists, extract the RED/GREEN/REFACTOR steps per slice
- **Architecture Recommendation:** If present, load as context for implementation decisions

If the spec has no slices (SMALL spec with ACs only), treat the entire AC list as a single slice named "Core".

### A2. Load Arch Artifacts

Check for architecture artifacts in the target project:
- `.skilmarillion/projects/{slug}/` — look for ADR files, OpenAPI specs, schema files
- Load any found artifacts as structured context. Do NOT re-read these per slice — cache them at session start.

### A3. Generate PLAN-NNN-{slug}.md

Delegate to the `spec-to-impl` agent via Task:

```
Task: spec-to-impl agent
Input: {
  "spec_content": "{full spec text}",
  "arch_context": "{loaded arch artifacts or empty}",
  "tdd_plan": "{TDD Plan section if present, otherwise empty}"
}
```

The agent returns a plan document with implementation steps grouped by slice.

**Naming — mirror the spec.** If the input spec is `specs/SPEC-NNN-{slug}.md`, save the plan to `plans/PLAN-NNN-{slug}.md` with matching `NNN` and `{slug}`. One spec → one plan, paired by number.

Save the result to:
```
.skilmarillion/projects/{project-slug}/plans/PLAN-NNN-{spec-slug}.md
```

If the input is a spec without a SPEC number (e.g. a loose spec file), assign the next available `NNN` by scanning `plans/` for existing `PLAN-NNN-*.md` files.

Display to the user:
> "Generated PLAN-{NNN}-{slug}.md from spec. {N} slices, {M} total steps."
> "Review the plan at: {path}"

Ask: "Proceed with TDD execution? (yes / review first / abort)"
- **review first:** Display the full plan content. Ask again.
- **abort:** Exit.
- **yes:** Proceed to Slice Execution.

### A4. Proceed to Slice Execution

Use the generated plan as input for the execution loop (same as Path B).

---

## PATH B: Impl Details Input

When the input is an impl-details file, execute the steps directly.

### B1. Parse Impl Details

Extract:
- **Slices/Phases:** Each major section (e.g., `## Phase 1: ...` or `## Slice 1: ...`)
- **Steps per slice:** Each numbered step or sub-step
- **Verification actions:** Each step's verification command or check
- **Git strategy:** Branch name, commit checkpoints

If the impl details have no slice/phase grouping (flat step list), treat all steps as a single slice named "Implementation".

### B2. Display Summary

> "Loaded impl details: {N} slices, {M} total steps."
> Slice 1: {name} — {step_count} steps
> Slice 2: {name} — {step_count} steps
> ...

Ask: "Ready to begin? (yes / abort)"

---

## SLICE EXECUTION LOOP

For each slice, in order:

### Step 1: Announce Slice

> "**Slice {N}/{total}: {name}**"
> "{slice description or first AC}"

### Step 2: Initialize State

Write state to `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` (under the `impl` key):
```yaml
slug: {slug}
current_slice: {N}
total_slices: {total}
phase: red
step: 1
attempts: 0
gaps: []
```

### Step 3: For Each Step in the Slice

Classify the step:

- **Behavioral step** (adds or changes observable behavior): Execute RED-GREEN-REFACTOR cycle.
- **Non-behavioral step** (config, docs, generated code, infrastructure): Execute directly and verify.

#### RED-GREEN-REFACTOR for Behavioral Steps

Load the `tdd-cycle` skill for discipline enforcement.

##### RED

1. Update state: `phase: red`
2. Write the failing test as specified by the step.
3. **Run the test.** Capture the output.
4. **Verify RED:**
   - If the test **fails for the expected reason** (missing behavior, not syntax/import error): RED confirmed. Proceed to GREEN.
   - If the test **fails for the wrong reason** (syntax error, import error, wrong assertion): Fix the test. Re-run. Do not proceed to GREEN until the failure matches the missing behavior.
   - If the test **passes** (behavior already exists): The step is already satisfied. Skip to the next step. Update state accordingly.

Display:
> "RED confirmed: {test name} fails — {failure reason}"

##### GREEN

1. Update state: `phase: green`
2. Write the minimal production code to make the test pass. Nothing more.
3. **Run the full test suite.** Capture the output.
4. **Verify GREEN:**
   - If **all tests pass**: GREEN confirmed. Proceed to REFACTOR.
   - If the **new test fails**: Fix the production code. Re-run. Increment `attempts`.
   - If **existing tests break**: Fix the regression. Do not proceed until the full suite is green.

Display:
> "GREEN confirmed: {test count} tests pass."

##### REFACTOR

1. Update state: `phase: refactor`
2. Review the code written in this step for:
   - Duplication
   - Poor naming
   - Missing extractions
3. If refactoring is needed: apply the change. **Run the full test suite.** Confirm all green.
4. If no refactoring needed: skip. State: "No refactoring needed."

Display:
> "REFACTOR complete. Suite green."

OR

> "No refactoring needed. Suite green."

#### Non-Behavioral Steps

1. Execute the step (create file, update config, run generator, etc.).
2. Run the verification action specified in the step.
3. Display result.

### Step 4: Slice Completion

After all steps in the slice pass:

1. Update state: `current_slice: {N+1}, phase: red, step: 1, attempts: 0`
2. Display:
   > "Slice {N} green. Moving to slice {N+1}."

If this is the last slice:
   > "All {total} slices green. Implementation complete."

### Step 5: Playwright AC Verification (Optional)

After each slice GREEN, check for browser-based acceptance criteria verification.

**5a. Availability Detection**

Check if Playwright MCP is available by looking for `.mcp.json` at the plugin root or attempting a `ToolSearch` for `mcp__playwright__browser_navigate`.

If not available: skip silently and continue to next slice.

**5b. Dev Server Detection**

If Playwright is available, check for a running dev server:
- Look for common ports: 3000, 5173, 8080, 4200
- Check `package.json` scripts for dev server commands
- If no dev server detected: log "No dev server detected — skipping browser verification" and continue

**5c. Browser Verification**

If both Playwright and a dev server are available:
1. Navigate to the relevant page for the current slice's acceptance criteria
2. Take a screenshot for visual confirmation
3. Execute any browser-testable ACs (element presence, text content, interaction flows)
4. Report results with pass/fail per AC

**5d. Result Handling**

Browser verification is **non-blocking**:
- A Playwright failure does NOT block the next slice
- Log failures as warnings: "Browser AC failed: {description} — continuing with next slice"
- Include browser verification results in the slice completion summary

---

## SLICE FAILURE ESCALATION

Track `attempts` per slice. After **3 failed RED-GREEN attempts** on the same step:

### Diagnostic Step

1. **Pause execution.**
2. Load the `slice-runner` skill for diagnostic guidance.
3. Analyze the failure pattern:
   - What was tried (3 attempts)?
   - What was the failure each time?
   - What is the root cause hypothesis?

4. Output one of three decisions:

#### Decision A: Modified Approach (Retry)

> "Diagnostic: The approach needs adjustment. Retrying with: {modified approach description}."

Reset `attempts` to 0. Apply the modified approach. Continue the cycle.

#### Decision B: Sub-Slice Decomposition (Split)

> "Diagnostic: This step is too large. Splitting into {N} sub-steps."

Decompose the failing step into smaller sub-steps. Insert them into the execution queue. Continue.

#### Decision C: ACCEPT_WITH_DEBT

> "Diagnostic: This behavior cannot be implemented within the current constraints. Accepting with debt."

Produce a structured gap record:
```yaml
slice: {slice_name}
step: {step_number}
missing_behavior: "{description of what was not implemented}"
severity: low | medium | high
justification: "{why this was accepted as debt}"
```

Append the gap record to the impl details file (or spec file if working from a spec).

Notify downstream slices: include the gap note so they can work around the missing behavior.

Advance to the next step or slice.

---

## POST-EXECUTION

After all slices complete (or are accepted with debt):

### 1. Final Suite Run

Run the full test suite as a final confirmation. This is distinct from the per-step GREEN checks.

Display:
> "Final suite: {pass_count} passed, {fail_count} failed."

If any failures: display them and ask the user how to proceed.

### 2. Gap Summary

If any ACCEPT_WITH_DEBT gaps exist:
> "Implementation complete with {N} debt items:"
> - Slice {X}: {missing_behavior} (severity: {severity})
> ...

### 3. State Cleanup

Remove the `impl` section from `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml`. If no other sections remain, delete the file.

### 4. Next Step Breadcrumb

> "All slices green. Implementation complete. Next steps:"
> - `/fellowship:ship` — generate a conventional commit from staged changes
> - "Next step: `/fellowship:review` to run quality checks before merging"

Check whether the `review` plugin is installed (look for a `review/` directory at the skilmarillion plugin root, or check if `/fellowship:review` is a known command). If not installed:
> - `/fellowship:review` — run quality checks before merging. 

---

## WHAT NOT TO DO

- Do NOT write production code before a failing test exists (behavioral steps).
- Do NOT proceed from RED to GREEN if the test failure is a syntax or import error — fix the test first.
- Do NOT skip the full suite run after GREEN — regressions must be caught immediately.
- Do NOT add behavior during REFACTOR phase.
- Do NOT retry the same failing approach more than 3 times — invoke the diagnostic step.
- Do NOT loop indefinitely on a failing step — ACCEPT_WITH_DEBT is a valid exit.
- Do NOT re-read arch artifacts per slice — cache them at session start.
- Do NOT generate impl details if the input is already an impl-details file.
