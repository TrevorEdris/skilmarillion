---
description: Software-Driven Development entry point. Triages a task and routes it to the appropriate workflow.
argument-hint: "[task description or spec path]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh:*)"
  - "Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
---

# /dream:sdd

Triage a task and route it to the correct workflow. Run at the start of every development session.

---

## ON STARTUP

Before anything else, run:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh list
```

Parse the output and categorize each result:

1. **Done files** — `current_phase` is `done — shipped` → silently run `clear --slug {slug}` and skip.
2. **Abandoned files** — file age > 30 days → add to abandoned list.
3. **Resume candidates** — all remaining files.

### If abandoned files exist

Ask the user (using `AskUserQuestion`):

> "Found {N} abandoned dream states older than 30 days: {list of feature names}. Remove them?"

Options: **"Yes, clean up"** / **"No, keep them"**

If "Yes": run `clear --slug {slug}` for each abandoned file.

### If resume candidates exist

Ask the user (using `AskUserQuestion`) with a numbered list:

> "Active dream states found. Resume one or start something new?
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

Inspect the argument passed to `/dream:sdd`:

- **Mode A** — argument ends in `.md` and resolves to an existing file path → the user is providing a pre-written spec. Skip triage. Go to **MODE A: Existing Spec**.
- **Mode B** — argument is a task description string, or no argument provided → full triage flow. Proceed to MODE B.

---

## MODE A — Existing Spec

1. Read the spec file at the provided path.
2. Check which sections exist: Problem Statement, Acceptance Criteria, Vertical Slices, Architecture Recommendation, TDD Plan.
3. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
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
${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh init \
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
> - State file: `.dream-state-{slug}.local.yaml`

### B2 — Route by Size

#### TRIVIAL

1. Confirm intent with the user:
   > "This looks like a trivial change. Ready to apply it now? (yes/no)"
2. If yes: apply the change directly (inline edit — no spec). Verify it works.
3. After applying, auto-clear state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh clear --slug "{slug}"
   ```
4. Report completion.

If no: ask what the user would like to do instead.

#### SMALL

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
     --slug "{slug}" \
     --current-phase "spec-drafting"
   ```
2. Delegate to `spec-builder` agent via Task:
   ```
   Task: spec-builder agent
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "mode": "small" }
   ```
3. Receive spec markdown from agent.
4. **Resolve artifact path** per `artifact-paths` skill:
   - Resolve project root (git root of target project — not necessarily CWD).
   - Resolve feature directory (`{project_root}/docs/{feature}/`).
   - Auto-increment spec number from existing `SPEC-*.md` files in `{project_root}/docs/{feature}/specs/`.
   - Derive spec path: `{project_root}/docs/{feature}/specs/SPEC-{NNN}-{slug}.md`.
5. **Confirm path with user** per `artifact-paths` slug confirmation protocol. User may accept, override slug, or override feature directory.
6. Create target directory if it does not exist:
   ```bash
   mkdir -p {project_root}/docs/{feature}/specs
   ```
7. Save spec using Write tool to the confirmed path.
8. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
     --slug "{slug}" \
     --current-phase "spec-drafted" \
     --spec-path "{confirmed_path}"
   ```
9. Display spec to user.
10. **Validation gate:** Run the validation script on the saved spec:
    ```bash
    python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {confirmed_path} --type spec --verbose --json
    ```
    - If score >= 70: display PASS with summary and proceed to step 11.
    - If score < 70: display findings, re-run `spec-builder` with findings as feedback, save the updated spec, then re-validate. Repeat until score >= 70.
11. Ask user: "This spec is ready. Looks good? (yes / request changes)"
    - If "request changes": re-run `spec-builder` with user's feedback as additional context. Repeat from step 3.
    - If "yes": update state `set --slug {slug} --current-phase "spec-confirmed"`.

#### FEATURE

1. **Context gathering:** Delegate to `context-gatherer` agent via Task:
   ```
   Task: context-gatherer agent
   Input: { "task": "{task description}", "triage_result": {triage JSON} }
   ```
   Parse the returned JSON as `context`. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
     --slug "{slug}" \
     --current-phase "context-gathered"
   ```
2. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
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
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
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
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
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
    ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
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

1. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
     --slug "{slug}" \
     --current-phase "epic-decomposing"
   ```
2. Delegate to `spec-builder` agent via Task:
   ```
   Task: spec-builder agent
   Input: { "task": "{task description}", "triage_result": {triage JSON}, "mode": "epic" }
   ```
   Receive phase map markdown as `phase_map`.
3. **Resolve artifact path** per `artifact-paths` skill:
   - Resolve project root (git root of target project — not necessarily CWD).
   - Resolve feature directory (`{project_root}/docs/{feature}/`). For EPICs, the feature slug is the epic slug.
   - Derive roadmap path: `{project_root}/docs/{feature}/ROADMAP.md`.
4. **Confirm path with user** per `artifact-paths` slug confirmation protocol. User may accept or override the feature directory.
5. Create target directory if it does not exist:
   ```bash
   mkdir -p {project_root}/docs/{feature}
   ```
6. Save phase map using Write tool to the confirmed roadmap path.
7. Update state:
   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/update-dream-state.sh set \
     --slug "{slug}" \
     --current-phase "epic-decomposed" \
     --spec-path "{confirmed_roadmap_path}"
   ```
8. Display phase map to user.
9. Ask user: "Roadmap saved to `{confirmed_roadmap_path}`. Run `/dream:sdd [phase description]` to spec each phase as `docs/{feature}/specs/SPEC-NNN-{phase-slug}.md`. Ready to start with Phase 1?"
   - If yes: proceed to the FEATURE flow above using Phase 1's description as the task. The current EPIC slug state is preserved; Phase 1 will create its own state file with the same feature directory.
   - If no: end session. State remains at `epic-decomposed`.

---

## WHAT NOT TO DO

- Do NOT write a spec in this command — spec writing is P0-C.
- Do NOT re-classify a task that already has an active state file — resume instead.
- Do NOT skip the startup scan — state files from prior sessions must be checked every time.
- Do NOT apply a TRIVIAL change without confirmation from the user.
- Do NOT proceed past triage if the triage agent returns prose instead of JSON — retry once, then ask the user to re-describe the task.
