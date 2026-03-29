---
description: Software-Driven Development entry point. Triages a task and routes it to the appropriate workflow.
argument-hint: "[task description or spec path]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh:*)"
  - "Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
---

# /plan:sdd

Triage a task and route it to the correct workflow. Run at the start of every development session.

---

## ON STARTUP

Before anything else, run:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh list
```

Parse the output and categorize each result:

1. **Done files** — `current_phase` is `done — shipped` → silently run `clear --slug {slug}` and skip.
2. **Abandoned files** — file age > 30 days → add to abandoned list.
3. **Resume candidates** — all remaining files.

### If abandoned files exist

Ask the user (using `AskUserQuestion`):

> "Found {N} abandoned plan states older than 30 days: {list of feature names}. Remove them?"

Options: **"Yes, clean up"** / **"No, keep them"**

If "Yes": run `clear --slug {slug}` for each abandoned file.

### If resume candidates exist

Ask the user (using `AskUserQuestion`) with a numbered list:

> "Active plan states found. Resume one or start something new?
> 1. {feature name} — phase: {current_phase}
> 2. {feature name} — phase: {current_phase}
> ...
> N. Start something new"

If a resume candidate is selected: load its state with `get --slug {slug}`, display current phase and triage result, and resume from the appropriate P0-C step. Do not re-triage.

If "Start something new": proceed to Entry Mode Detection without clearing any existing state files.

### If no state files

Skip directly to Entry Mode Detection.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## Entry Mode Detection

Inspect the argument passed to `/plan:sdd`:

- **Mode A** — argument ends in `.md` and resolves to an existing file path → the user is providing a pre-written spec. Skip triage. Go to **MODE A: Existing Spec**.
- **Mode B** — argument is a task description string, or no argument provided → full triage flow. Proceed to MODE B.

---

## MODE A — Existing Spec

1. Read the spec file at the provided path.
2. Check which sections exist: Problem Statement, Acceptance Criteria, Vertical Slices, Architecture Recommendation, TDD Plan.
3. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug-from-filename}" \
     --current-phase "spec-reviewing"
   ```
4. If Architecture Recommendation section is absent or contains the placeholder string `_To be filled by architecture-advisor_`: delegate to `architecture-advisor` agent via Task:
   ```
   Task: architecture-advisor agent
   Input: { "spec_content": "{full spec text}", "context": {} }
   ```
   Append the returned markdown to the spec using Edit.
5. If TDD Plan section is absent or contains the placeholder string `_To be filled by tdd-planner_`: delegate to `tdd-planner` agent via Task:
   ```
   Task: tdd-planner agent
   Input: { "spec_content": "{full spec text}", "arch_recommendation": "{arch section text}" }
   ```
   Append the returned markdown to the spec using Edit.
6. If both sections were already present and complete: display the spec summary and confirm with the user.
7. **Validation gate:** Run the validation script on the spec:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py <spec-path> --type spec --verbose --json
   ```
   - If score >= 70: display PASS with summary and proceed to step 8.
   - If score < 70: display findings, re-draft the failing sections using the findings as feedback, then re-run validation. Repeat until score >= 70.
8. Ask user: "This spec is ready for `/do:tdd`. Does it look correct? (yes / request changes)"
   - If "request changes": return to step 4 and re-run the relevant agents with the user's feedback as additional context.
   - If "yes": update state `set --slug {slug} --current-phase "spec-confirmed"`.

---

## MODE B — Triage and Route

### B1 — Triage

Delegate to the `triage` agent using the `Task` tool:

```
Task: triage agent
Input: { "task": "<user's task description or prompted input>", "context": "<any codebase notes>" }
```

The agent returns bare JSON: `{ size, risk, routing_decision, rationale, slug }`.

Parse the JSON. If parsing fails or the output contains prose, ask the user to re-describe the task and retry once.

Before initializing state, resolve the project root per `artifact-paths` skill — determine which git repo this task targets. Cache the result as `{project_root}`.

Initialize state:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh init \
  --slug "{slug}" \
  --feature "{task description}" \
  --size "{size}" \
  --risk "{risk}" \
  --routing "{routing_decision}" \
  --current-phase "triaged" \
  --project-root "{project_root}"
```

Display the triage result to the user:

> **Triage result:**
> - Size: {size}
> - Risk: {risk}
> - Routing: {routing_decision}
> - Rationale: {rationale}
> - State file: `.plan-state-{slug}.local.yaml`

### B2 — Route by Size

#### TRIVIAL

1. Confirm intent with the user:
   > "This looks like a trivial change. Ready to apply it now? (yes/no)"
2. If yes: apply the change directly (inline edit — no spec). Verify it works.
3. After applying, auto-clear state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh clear --slug "{slug}"
   ```
4. Report completion.

If no: ask what the user would like to do instead.

#### SMALL — QRSPI Cycle

SMALL tasks use the QRSPI cycle (Question, Research, Structure, Plan, Implement-offer) instead of a full spec workflow. The output is an `IMPL_DETAILS.md` saved to the active session directory — not a spec in `docs/`.

> **Risk promotion gate:** If the triage result shows SMALL + HIGH risk, pause before starting QRSPI:
> "This task is small but high-risk. Promote to FEATURE workflow for full spec coverage? (yes / no)"
> If "yes": re-route to the FEATURE workflow below. If "no": continue with QRSPI.

##### Q — Question

Surface design decisions as explicit choices **before reading any code**.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "qrspi-question"
   ```
2. Work only from the user's task description. Do NOT read code yet.
3. Identify every decision point that will shape the fix or change. Present numbered options for each:
   - "What approach for X? (1) option-a (2) option-b (3) option-c"
   - "Which trade-off matters? (a) performance (b) simplicity (c) consistency"
4. Ask clarifying questions about scope, constraints, and non-goals.
5. Confirm answers with the user. Record confirmed answers as the **research frame** — the specific questions that code reading must answer.
6. If no design decisions exist (e.g., a straightforward bug fix with one obvious approach), state that explicitly and proceed directly to Research.

**Gate:** Do not proceed to Research until design questions are answered or explicitly scoped out.

##### R — Research

Targeted codebase reading to answer each question from the Question phase.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "qrspi-research"
   ```
2. Map each research question to specific files and code paths to read.
3. Read **only** what is needed to answer the identified questions — no broad exploration.
4. For each question, provide an answer with code evidence (`file:line` references).
5. Present findings to the user as a summary:
   > **Research findings:**
   > - Q1: {answer} — `src/foo.py:42`
   > - Q2: {answer} — `src/bar.py:18`, `src/baz.py:7`
   > - Constraints identified: {list}
6. If research reveals the task is larger than expected (e.g., touches more than 5 files or requires new behavior), prompt:
   > "Research suggests this is bigger than SMALL. Promote to FEATURE workflow? (yes / no)"

**Gate:** Every question from the Question phase must be answered or explicitly deferred with rationale.

##### S — Structure

Phase breakdown with dependencies. For SMALL tasks, this is typically 1-2 phases.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "qrspi-structure"
   ```
2. Decompose the work into phases (usually 1-2 for SMALL tasks):
   - What each phase delivers
   - Dependencies between phases
   - What each phase enables
3. Identify the critical path — which phase must land first.
4. Surface risks: what could cause a phase to fail or expand in scope.
5. Present the structure to the user for confirmation before detailed planning.

**Gate:** Structure must be confirmed before proceeding to Plan.

##### P — Plan

Produce `IMPL_DETAILS.md` with target files, ordered steps, git strategy, and verification actions.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "qrspi-plan"
   ```
2. Draft `IMPL_DETAILS.md` following the template defined in the `qrspi-prompts` skill. Required sections:
   - **Target Repos and File Paths** — explicit list of every file to be touched
   - **Structure** — phase breakdown from step S
   - **Ordered Implementation Steps** — each step has an exact file path and a verification action; steps that add behavior are structured as RED-GREEN pairs
   - **Risks and Assumptions** — what could go wrong, what we assume
   - **Verification Steps** — how to confirm each step is correct
   - **Traceability** — map each research finding to a plan step
   - **Git Strategy** — branch name, commit checkpoints with messages, anticipated PR title and description
3. Resolve the active session directory. Save `IMPL_DETAILS.md` to:
   ```
   {session_dir}/IMPL_DETAILS.md
   ```
   Where `{session_dir}` is the current session's `.ai/sessions/YYYY-MM-DD_<slug>/` directory. Do NOT save to `docs/`.
4. **Validation gate:** Run the validation script on the saved plan:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {session_dir}/IMPL_DETAILS.md --type plan --verbose --json
   ```
   - If score >= 70: display PASS with summary and proceed to step 5.
   - If score < 70: display findings, re-draft the failing sections using the findings as feedback, then re-run validation. Repeat until score >= 70.
5. Present the plan to the user:
   > **Implementation plan ready** (validation score: {score}/100)
   > {summary of steps}
6. Ask user: "This plan is ready. Looks good? (yes / request changes)"
   - If "request changes": re-draft with user's feedback as additional context. Repeat from step 2.
   - If "yes": update state `set --slug {slug} --current-phase "plan-confirmed"`.

##### I — Implement Offer

After plan approval, offer execution options.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "plan-confirmed"
   ```
2. Ask the user:
   > "Execute now or hand to `/impl:tdd`?"
   - **"Execute now"**: Run implementation steps in-place within the current session, following RED-GREEN-REFACTOR for each behavioral step. Update state to `implementing`, then `done — shipped` on completion. Auto-clear state file.
   - **"Hand to `/impl:tdd`"**: Report the path to `IMPL_DETAILS.md` and instruct the user to run `/impl:tdd {session_dir}/IMPL_DETAILS.md`. Update state to `ready-for-impl`.

#### FEATURE

1. **Context gathering:** Delegate to `context-gatherer` agent via Task:
   ```
   Task: context-gatherer agent
   Input: { "task": "{task description}", "triage_result": {triage JSON} }
   ```
   Parse the returned JSON as `context`. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "context-gathered"
   ```
2. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "spec-drafting"
   ```
3. **Spec building:** Delegate to `spec-builder` agent via Task:
   ```
   Task: spec-builder agent
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "context": {context JSON}, "mode": "feature" }
   ```
   Receive spec markdown as `spec_draft`. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "arch-reviewing"
   ```
4. **Architecture advising:** Delegate to `architecture-advisor` agent via Task:
   ```
   Task: architecture-advisor agent
   Input: { "spec_content": "{spec_draft}", "context": {context JSON} }
   ```
   Receive architecture section markdown as `arch_section`. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "tdd-planning"
   ```
5. **TDD planning:** Delegate to `tdd-planner` agent via Task:
   ```
   Task: tdd-planner agent
   Input: { "spec_content": "{spec_draft}\n\n{arch_section}", "arch_recommendation": "{arch_section}" }
   ```
   Receive TDD plan section as `tdd_section`.
6. **Assemble spec:** Replace `_To be filled by architecture-advisor_` placeholder in `spec_draft` with `arch_section`. Replace `_To be filled by tdd-planner_` placeholder with `tdd_section`.
7. **Resolve artifact path** per `artifact-paths` skill:
   - Resolve project root (git root of target project — not necessarily CWD).
   - Resolve feature directory (`{project_root}/docs/{feature}/`).
   - Auto-increment spec number from existing `SPEC-*.md` files in `{project_root}/docs/{feature}/specs/`.
   - Derive spec path: `{project_root}/docs/{feature}/specs/SPEC-{NNN}-{slug}.md`.
8. **Confirm path with user** per `artifact-paths` slug confirmation protocol. User may accept, override slug, or override feature directory.
9. Create target directory if it does not exist:
   ```bash
   mkdir -p {project_root}/docs/{feature}/specs
   ```
10. Save assembled spec using Write tool to the confirmed path.
11. Update state:
    ```bash
    ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
      --slug "{slug}" \
      --current-phase "spec-drafted" \
      --spec-path "{confirmed_path}"
    ```
12. Display spec to user.
13. **Validation gate:** Run the validation script on the assembled spec:
    ```bash
    python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {confirmed_path} --type spec --verbose --json
    ```
    - If score >= 70: display PASS with summary and proceed to step 14.
    - If score < 70: display findings, re-run `spec-builder` with findings as feedback, then re-assemble and re-validate. Repeat until score >= 70.
14. Ask user: "This spec is ready for `/do:tdd`. Does it look correct? (yes / request changes)"
    - If "request changes": re-run `spec-builder` with user's feedback as additional context, then repeat steps 4–13.
    - If "yes": update state `set --slug {slug} --current-phase "spec-confirmed"`.

#### EPIC

EPIC tasks require a PRD and a roadmap before individual milestones can be specced. Route the user to the appropriate commands instead of generating inline.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "epic-detected"
   ```
2. **Resolve project root** per `artifact-paths` skill. Check for an existing PRD at `docs/{feature}/PRD.md` where `{feature}` is derived from the task slug.
3. **If no PRD exists:**
   > "This is EPIC-scale and needs a PRD first. Run `/plan:prd [description]` to define the feature, then `/plan:roadmap [prd-path]` to decompose into milestones, then `/plan:sdd [milestone]` to spec each one."
4. **If a PRD exists:**
   > "This is EPIC-scale. Run `/plan:roadmap {prd-path}` to decompose into milestones, then `/plan:sdd [milestone]` to spec each one."
5. Clear state — the user will re-enter via `/plan:roadmap` or `/plan:sdd`:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh clear --slug "{slug}"
   ```

---

## WHAT NOT TO DO

- Do NOT re-classify a task that already has an active state file — resume instead.
- Do NOT skip the startup scan — state files from prior sessions must be checked every time.
- Do NOT apply a TRIVIAL change without confirmation from the user.
- Do NOT proceed past triage if the triage agent returns prose instead of JSON — retry once, then ask the user to re-describe the task.
- Do NOT save SMALL task IMPL_DETAILS.md to `docs/` — it belongs in the active session directory.
- Do NOT read code during the Question phase of QRSPI — work only from the user's task description.
- Do NOT over-plan SMALL tasks — a 3-file bug fix should not produce a 50-step plan. See `qrspi-prompts` skill for size guidance.
- Do NOT skip the risk promotion gate — SMALL + HIGH risk must prompt for FEATURE promotion.
