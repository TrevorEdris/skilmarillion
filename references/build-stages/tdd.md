# /fellowship:build — TDD Stage

Execute RED → GREEN → REFACTOR against a SPEC's Ordered Implementation Steps. The SPEC is the plan; there is no separate PLAN artifact.

This stage serves three dispatch forms (see `commands/build.md`):
1. **Single SPEC** — `spec W{N}{letter}` or a bare spec path.
2. **Wave parallel** — `wave N` spawns one run of this stage per wave-agent in the wave. Wave mechanics live in § "Wave Parallel Dispatch" below.
3. **State resume** — no argument, pick up a stored `PROJECT-STATE.yaml`.

---

## ON STARTUP

### 1. Check for In-Progress State

Look for `.skilmarillion/projects/*/PROJECT-STATE.yaml` files that contain an `impl:` section.

If found:
- Parse each file for `slug`, `current_wave`, `current_wave_agent`, `current_step`, `total_steps`, `phase` (red/green/refactor)
- Ask the user via `AskUserQuestion`:

  > "Found in-progress TDD state for '{slug}' (wave {current_wave}, agent {current_wave_agent}, step {current_step}/{total_steps}, phase: {phase}). Resume or start fresh?"
  >
  > Options: **"Resume"** / **"Start fresh"** / **"Abort"**

- **Resume:** Load the state and jump to the recorded step and phase.
- **Start fresh:** Delete the state file, proceed to Input Detection.
- **Abort:** Exit.

### 2. Input Detection & SPEC Resolution

**Core principle:** Always confirm the resolved SPEC file with the user before reading it. With multiple `.skilmarillion/projects/*/` slug directories, ambiguous input is the norm — never silently pick one.

#### 2a. Check for In-Progress State (no argument only)

If `$ARGUMENTS` is empty, search `.skilmarillion/projects/*/PROJECT-STATE.yaml` for files with an `impl:` section. If found, jump to step 1 above (State Resumption). Otherwise, proceed.

#### 2b. Delegate to `artifact-resolver` Agent

For any non-empty argument (or empty argument after the in-progress check), delegate SPEC discovery to the `artifact-resolver` agent. See `artifact-paths` skill § "Artifact Resolution" for the calling contract.

```
Task: artifact-resolver agent
Input: {
  "artifact_type": "spec",
  "query": "{raw $ARGUMENTS or wave-agent id W{N}{letter}}",
  "project_root": "{resolved project root}"
}
```

The agent returns a structured `{ match_type, candidates, total_count }` response. The spec resolver understands `W{N}{letter}` IDs directly — see `agents/artifact-resolver.md`.

#### 2c. Confirm Selection with User

Per the caller flow in the `artifact-paths` skill, present candidates via `AskUserQuestion`:

| `match_type` | Prompt |
|--------------|--------|
| `exact_path` | "Using `{path}`. Proceed?" (Proceed / Pick different / Cancel) |
| `single` | "Found `{slug}/{filename}`. Build this one?" (Yes / Pick different / Cancel) |
| `multiple` | "Multiple matches. Pick one:" + top 5 candidates + "None — list all" |
| `none` | Re-call agent with `query: ""`, present `all` result |
| `all` | Present every SPEC grouped by slug + "None — cancel" |

If **no SPECs exist at all** (agent returns empty `all`), display:
> "No SPECs found under `.skilmarillion/projects/*/specs/`. Run `/fellowship:plan --specify` to generate them from a ROADMAP, or provide a SPEC path directly."

#### 2d. Classify Selected File

After the user confirms a candidate, read the file and verify it is a SPEC:
- Contains `## Acceptance Criteria` AND `## Ordered Implementation Steps`.
- If either marker is missing, display: "This file does not look like a SPEC. Expected sections: `## Acceptance Criteria` + `## Ordered Implementation Steps`."

There is no PLAN artifact in the current model — the SPEC is the plan. Do not look for a PLAN file and do not translate the SPEC to a separate plan.

#### 2e. Final Confirmation Gate

Before reading the SPEC for TDD execution, confirm the absolute path:

> "Building from `.skilmarillion/projects/{slug}/specs/SPEC-W{N}{letter}-{name}.md`. Proceed?"

Options: **Proceed** / **Pick a different SPEC** / **Cancel**.

Never skip this gate. A wrong SPEC triggers TDD against the wrong ACs and wastes the engineer's time.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## TDD LOOP — Execute the SPEC's Ordered Steps

### L1. Parse the SPEC

Extract from the SPEC frontmatter and body:
- **Wave-agent id** — `wave_id` (e.g., `W1a`)
- **Acceptance Criteria** — every `AC-{wave_id}.{n}` block
- **Ordered Implementation Steps** — every numbered step with its `File`, `Action`, `Verification`, and `RED|GREEN|REFACTOR|non-behavioral` marker
- **Git Strategy** — branch name, commit checkpoints
- **Architecture Recommendation** — load as context for implementation decisions (if present)

The SPEC is the single source of truth. Do not re-derive steps from ACs at runtime.

### L2. Load Cached Arch Artifacts

Check for architecture artifacts in the target project:
- `.skilmarillion/projects/{slug}/` — look for ADR files, OpenAPI specs, schema files
- Load any found artifacts as structured context. Do NOT re-read these per step — cache them at session start.

### L3. Display Summary and Confirm

> "Loaded SPEC-{wave_id}-{slug}: {N} steps (AC count: {M}), branch: `{branch}`."

Ask: "Ready to begin? (yes / abort)"

### L4. Initialize State

Write state to `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` (under the `impl` key):
```yaml
slug: {slug}
current_wave: {wave}
current_wave_agent: {wave_id}
wave_agents_completed: []
current_step: 1
total_steps: {N}
phase: red
attempts: 0
gaps: []
```

### L5. For Each Step in Order

Use the step's explicit `RED|GREEN|REFACTOR|non-behavioral` marker from the SPEC. Do not re-classify.

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

### L6. Step Completion

After each step passes:

1. Update state: `current_step: {N+1}, phase: red, attempts: 0`
2. Display:
   > "Step {N} green. Moving to step {N+1}."

After the last step:
> "SPEC-{wave_id}-{slug} complete. All {total_steps} steps green."

### L7. Playwright AC Verification (Optional)

After the final step GREEN (not per-step — once per SPEC), check for browser-based acceptance criteria verification.

**7a. Availability Detection**

Check if Playwright MCP is available by looking for `.mcp.json` at the plugin root or attempting a `ToolSearch` for `mcp__playwright__browser_navigate`.

If not available: skip silently.

**7b. Dev Server Detection**

If Playwright is available, check for a running dev server:
- Look for common ports: 3000, 5173, 8080, 4200
- Check `package.json` scripts for dev server commands
- If no dev server detected: log "No dev server detected — skipping browser verification" and continue

**7c. Browser Verification**

If both Playwright and a dev server are available:
1. Navigate to the relevant page for the SPEC's acceptance criteria
2. Take a screenshot for visual confirmation
3. Execute any browser-testable ACs (element presence, text content, interaction flows)
4. Report results with pass/fail per AC

**7d. Result Handling**

Browser verification is **non-blocking**:
- A Playwright failure does NOT block commit or wave completion
- Log failures as warnings: "Browser AC failed: {description} — continuing"
- Include browser verification results in the SPEC completion summary

---

## STEP FAILURE ESCALATION

Track `attempts` per step. After **3 failed RED-GREEN attempts** on the same step:

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

#### Decision B: Sub-Step Decomposition (Split)

> "Diagnostic: This step is too large. Splitting into {N} sub-steps."

Decompose the failing step into smaller sub-steps. Insert them into the execution queue. Continue.

#### Decision C: ACCEPT_WITH_DEBT

> "Diagnostic: This behavior cannot be implemented within the current constraints. Accepting with debt."

Produce a structured gap record:
```yaml
wave_agent: {wave_id}
step: {step_number}
missing_behavior: "{description of what was not implemented}"
severity: low | medium | high
justification: "{why this was accepted as debt}"
```

Append the gap record to the SPEC file under a `## Gaps` section (create if absent).

Advance to the next step.

---

## WAVE PARALLEL DISPATCH

When this stage is invoked as part of `/fellowship:build wave N`, multiple wave-agents run this loop concurrently, one per SPEC in the wave.

### Spawning

`commands/build.md` spawns parallelism. Two modes:

| Mode | Spawner |
|------|---------|
| Task subagents (default) | One `Task` per wave-agent, all sent in a single message so they execute concurrently. |
| Agent Teams (`--team`) | `TeamCreate` with one teammate per wave-agent. Teammates follow `teams/rules/team-conventions.md`. |

### Per-Agent Isolation

Each spawned agent receives:
- Its assigned SPEC path (`specs/SPEC-W{N}{letter}-{slug}.md`)
- Its own `PROJECT-STATE.yaml` key scope (`impl.wave_agents[{wave_id}]`)
- The roadmap-level wave id (for state tracking)

The wave-planner guarantees `touches` disjointness across wave-agents in the same wave. No agent should see any other agent's in-flight writes.

### Merge Barrier

The wave is green when every agent reports:
- All SPEC steps complete (or ACCEPT_WITH_DEBT recorded)
- Full test suite passes for the repo

`/fellowship:build wave N` blocks until the barrier is met. On completion it updates `PROJECT-STATE.yaml`:
```yaml
impl:
  current_wave: {next}
  wave_agents_completed: [W1a, W1b, ...]
```

If any agent fails non-recoverably, `wave N` surfaces the failure and does not mark the wave green. The user decides whether to retry the failed agent or split it into a sub-wave.

---

## POST-EXECUTION (per SPEC)

After a single SPEC completes:

### 1. Final Suite Run

Run the full test suite as a final confirmation. This is distinct from the per-step GREEN checks.

Display:
> "Final suite: {pass_count} passed, {fail_count} failed."

If any failures: display them and ask the user how to proceed.

### 2. Gap Summary

If any ACCEPT_WITH_DEBT gaps exist:
> "SPEC-{wave_id} complete with {N} debt items:"
> - Step {X}: {missing_behavior} (severity: {severity})

### 3. State Cleanup

When the SPEC is the last remaining wave-agent in its wave, and no other `impl:` scopes remain, remove the `impl:` section from `PROJECT-STATE.yaml`. If no other sections remain, delete the file.

### 4. Next Step Breadcrumb

Single-SPEC run:
> "SPEC-{wave_id}-{slug} green. Next: `/fellowship:ship` (commit + optional PR), then `/fellowship:build spec W{next_wave_agent}` or `/fellowship:build wave {next_wave}` when the rest of the wave is green."

Wave run (spawner after barrier):
> "Wave {N.M} green ({count} wave-agents complete). Next: `/fellowship:review` to run quality checks, then `/fellowship:build wave {next}`."

---

## WHAT NOT TO DO

- Do NOT write production code before a failing test exists (behavioral steps).
- Do NOT proceed from RED to GREEN if the test failure is a syntax or import error — fix the test first.
- Do NOT skip the full suite run after GREEN — regressions must be caught immediately.
- Do NOT add behavior during REFACTOR phase.
- Do NOT retry the same failing approach more than 3 times — invoke the diagnostic step.
- Do NOT loop indefinitely on a failing step — ACCEPT_WITH_DEBT is a valid exit.
- Do NOT re-read arch artifacts per step — cache them at session start.
- Do NOT translate the SPEC into a separate PLAN file — the SPEC is the plan.
- Do NOT touch files outside the SPEC's frontmatter `touches` list — the wave-planner's disjointness guarantee depends on it.
