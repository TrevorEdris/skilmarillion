---
description: TDD execution. Slice-by-slice RED/GREEN/REFACTOR from a spec, with debug and refactor modes.
argument-hint: "[--debug <issue> | --refactor <target>] [spec-or-impl-details]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
model: sonnet
---

# /fellowship:build

Turns a spec into committed, tested code — one slice at a time. Enforces RED → GREEN → REFACTOR. Resumes from `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` when state is found.

> **The rule:** RED before GREEN. No production code without a failing test first.
>
> **Personality:** direct, brief, action-oriented. "We" framing: "Let's get this green." When tests fail: state the failure clearly, propose the fix. Celebrate slice completions: "Slice 1 green. Moving to slice 2."

---

## DISPATCH — Pick the Mode

Parse `$ARGUMENTS` for a leading flag:

| Flag | Stage file | Purpose |
|------|------------|---------|
| *(no flag)* | `references/build-stages/tdd.md` | Slice-by-slice TDD execution (primary mode) |
| `--debug` | `references/build-stages/debug.md` | Structured debugging: reproduce → isolate → root cause → fix |
| `--refactor` | `references/build-stages/refactor.md` | Phase-gated refactoring with test verification between steps |

**How to run a stage:**
1. `Read` the stage file from `${CLAUDE_PLUGIN_ROOT}/references/build-stages/{stage}.md`.
2. Follow its instructions exactly. Stage files are self-contained playbooks.
3. Pass through the remaining `$ARGUMENTS` (after the flag) as the stage input.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## DEFAULT — TDD Execution (No Flag)

### Input Detection

1. **No argument:** Look for in-progress state files under `.skilmarillion/projects/*/PROJECT-STATE.yaml` with an `impl:` section. If found, offer to resume. Otherwise look for specs under `.skilmarillion/projects/*/specs/` and offer to pick one.
2. **Argument is a spec path** (contains `## Acceptance Criteria` AND `## Vertical Slices`): translate to impl details via the `spec-to-impl` agent, then execute.
3. **Argument is an impl-details path** (contains `## Implementation Steps`): execute steps directly.
4. **Neither:** error — point at the markers the file is missing.

### State Resumption

If `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` contains an `impl:` section, ask:

> "Found in-progress TDD state for '{slug}' (slice {current_slice}/{total_slices}, phase: {phase}). Resume or start fresh?"
>
> Options: **Resume** / **Start fresh** / **Abort**

Then follow the full playbook in `references/build-stages/tdd.md`.

---

## SLICE FAILURE ESCALATION

After **3 failed RED-GREEN attempts** on the same step, invoke the diagnostic step (detailed in `references/build-stages/tdd.md`). Output one of:

- **Modified Approach** — reset attempts, apply the modified approach, continue
- **Sub-Slice Decomposition** — split the step into smaller sub-steps, continue
- **ACCEPT_WITH_DEBT** — record a structured gap, advance to the next step

Never loop indefinitely. ACCEPT_WITH_DEBT is a valid exit.

---

## STATE TRACKING

Write state to `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` under the `impl:` key as the TDD loop progresses. Required fields: `slug`, `current_slice`, `total_slices`, `phase` (red|green|refactor), `step`, `attempts`, `gaps`.

Use `${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh` to modify the state file idempotently.

---

## POST-EXECUTION

After all slices complete (or are accepted with debt):

1. Run the full test suite as a final confirmation (distinct from per-step GREEN checks).
2. If any ACCEPT_WITH_DEBT gaps exist, display the gap summary.
3. Clean up the `impl:` section from `PROJECT-STATE.yaml` (delete the file if no other sections remain).
4. Breadcrumb:
   > "All slices green. Next: `/fellowship:review` to run quality checks, then `/fellowship:ship` to commit."

---

## GIT EXCLUSION

`.skilmarillion/` files are **never auto-staged or auto-committed** by this command. The user decides whether to track them.

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
- Do NOT auto-commit `.skilmarillion/` files.
