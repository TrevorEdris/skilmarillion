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

### B2 — Question Phase (All Sizes)

Surface design decisions **before reading any code**. See `pre-spec-questions` skill for size-appropriate prompts.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "questioning"
   ```
2. Work only from the user's task description. Do NOT read code yet.
3. Identify every decision point that will shape the fix or change. Present numbered options for each using prompts from the `pre-spec-questions` skill.
4. Ask clarifying questions about scope, constraints, and non-goals.
5. Confirm answers with the user. Record confirmed answers as **design constraints** — these are passed to downstream agents.
6. If no design decisions exist (e.g., a straightforward bug fix with one obvious approach), state that explicitly and proceed directly to B3.

**Gate:** Do not proceed to B3 until design questions are answered or explicitly scoped out.

### B3 — Route by Size

All non-EPIC sizes produce a SPEC file at `docs/{feature}/specs/SPEC-{NNN}-{slug}.md`. Size determines which agents are invoked and which spec sections are required. See `spec-format` skill for the section gating table.

#### TRIVIAL

Lightweight spec: Problem Statement, happy-path ACs, TDD Plan. No context gathering, no spec-builder interview, no architecture advisor.

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "spec-drafting"
   ```
2. Draft a lightweight spec directly with:
   - **Problem Statement** — one paragraph derived from the task description and confirmed design constraints
   - **Acceptance Criteria** — happy path only, Given/When/Then format
3. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "tdd-planning"
   ```
4. **TDD planning:** Delegate to `tdd-planner` agent via Task:
   ```
   Task: tdd-planner agent
   Input: { "spec_content": "{spec_draft}", "arch_recommendation": "" }
   ```
   Receive TDD plan section as `tdd_section`.
5. Append `tdd_section` to spec draft.
6. Proceed to **Save and Validate** (B4).

#### SMALL

Spec with Problem Statement, risk-scaled ACs, Architecture Recommendation, TDD Plan. No vertical slices.

1. **Context gathering:** Delegate to `context-gatherer` agent via Task:
   ```
   Task: context-gatherer agent
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "design_constraints": {confirmed answers from B2} }
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
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "context": {context JSON}, "design_constraints": {confirmed answers from B2}, "mode": "small" }
   ```
   Receive spec markdown as `spec_draft` (Problem Statement + risk-scaled ACs, no vertical slices). Update state:
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
7. Proceed to **Save and Validate** (B4).

#### FEATURE

Full spec with Problem Statement, risk-scaled ACs organized as Vertical Slices, Architecture Recommendation, TDD Plan.

1. **Context gathering:** Delegate to `context-gatherer` agent via Task:
   ```
   Task: context-gatherer agent
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "design_constraints": {confirmed answers from B2} }
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
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "context": {context JSON}, "design_constraints": {confirmed answers from B2}, "mode": "feature" }
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
7. Proceed to **Save and Validate** (B4).

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

### B4 — Save and Validate (TRIVIAL, SMALL, FEATURE)

1. **Resolve artifact path** per `artifact-paths` skill:
   - Resolve project root (git root of target project — not necessarily CWD).
   - Resolve feature directory (`{project_root}/docs/{feature}/`).
   - Auto-increment spec number from existing `SPEC-*.md` files in `{project_root}/docs/{feature}/specs/`.
   - Derive spec path: `{project_root}/docs/{feature}/specs/SPEC-{NNN}-{slug}.md`.
2. **Confirm path with user** per `artifact-paths` slug confirmation protocol. User may accept, override slug, or override feature directory.
3. Create target directory if it does not exist:
   ```bash
   mkdir -p {project_root}/docs/{feature}/specs
   ```
4. Save assembled spec using Write tool to the confirmed path.
5. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-plan-state.sh set \
     --slug "{slug}" \
     --current-phase "spec-drafted" \
     --spec-path "{confirmed_path}"
   ```
6. Display spec to user.
7. **Validation gate:** Run the validation script on the assembled spec:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {confirmed_path} --type spec --verbose --json
   ```
   - If score >= 70: display PASS with summary and proceed to step 8.
   - If score < 70: display findings, re-draft the failing sections using the findings as feedback, then re-validate. Repeat until score >= 70.
8. Ask user: "This spec is ready for `/impl:tdd`. Does it look correct? (yes / request changes)"
   - If "request changes": re-draft with user's feedback as additional context, then repeat from the relevant agent step.
   - If "yes": update state `set --slug {slug} --current-phase "spec-confirmed"`.

---

## WHAT NOT TO DO

- Do NOT re-classify a task that already has an active state file — resume instead.
- Do NOT skip the startup scan — state files from prior sessions must be checked every time.
- Do NOT proceed past triage if the triage agent returns prose instead of JSON — retry once, then ask the user to re-describe the task.
- Do NOT read code during the Question phase — work only from the user's task description.
- Do NOT skip the Question phase — design decisions must be surfaced before spec generation, even if the answer is "no decisions to make."

---

## NEXT STEP BREADCRUMB

After the spec is confirmed (state = `spec-confirmed`), display:

> **Spec confirmed.** Next step:
> ```
> /impl:tdd {spec-path}
> ```
> This hands the spec to the implementation plugin for test-driven development.

**If the `impl` plugin is not installed:** Check whether `/impl:tdd` is available by looking for `impl/` in the plugin directory or checking plugin manifest. If not found, display instead:

> **Spec confirmed.** Next step: run `/impl:tdd {spec-path}` to begin implementation.
>
> The `impl` plugin is not yet installed. Install it with:
> ```
> claude plugin add impl
> ```
> Once installed, run `/impl:tdd {spec-path}` to start the TDD cycle from this spec.
