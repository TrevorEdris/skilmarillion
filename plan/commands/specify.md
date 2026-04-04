---
description: Generate all spec documents from a ROADMAP. Takes a ROADMAP.md as input and outputs individual SPEC files for each milestone.
argument-hint: "[roadmap-path]"
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

# /plan:specify

Generate spec documents from a ROADMAP. Reads the roadmap, extracts milestones, and produces a SPEC file for each one using parallel agents. Run after `/plan:roadmap` and before `/impl:tdd`.

---

## Flow

### 1. Input Resolution

Resolve the ROADMAP to decompose into specs:

- **Argument provided** — If the argument is a file path ending in `.md`, use it directly.
- **No argument, feature directory context** — Search for `.skilmarillion/projects/*/*/ROADMAP.md` in the resolved project root:
  - If exactly one ROADMAP found, use it.
  - If multiple found, present a numbered list and ask the user to select one.
  - If none found, ask the user for a ROADMAP path or suggest running `/plan:roadmap` first.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. ROADMAP Validation Gate

Before proceeding, check for a sibling PRD and validate the roadmap structure:

1. Derive the feature directory from the roadmap path (parent directory).
2. Check for `{feature-dir}/PRD.md` — if present, validate it:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {prd_path} --type prd --json
   ```
   - If score < 70: warn the user but do not block (the roadmap may have been created independently).

3. Read the ROADMAP file and verify it contains:
   - At least one phase section (`## Phase N:`)
   - At least one milestone (`### P{N}-{letter}:`)
   - A Spec Index section

If the roadmap has no parseable milestones, stop and report: "Could not find milestones in the roadmap. Expected format: `### P0-A: [Feature Name]` with `**What:**` and `**Checklist:**` fields."

### 3. Extract Milestones

Parse the ROADMAP to extract each milestone. For each milestone, capture:

- **Feature ID** — e.g., `P0-A`, `P1-B`
- **Name** — the milestone heading text after the ID
- **What** — the plain-language description from the `**What:**` field
- **Depends on** — dependency references from `**Depends on:**` field
- **Risk** — from the `**Risk:**` field (default to MODERATE if absent)
- **Checklist** — implementation sub-tasks from the `**Checklist:**` field
- **Estimated scope** — from the roadmap if present; infer from checklist length if absent:
  - 1-2 checklist items → TRIVIAL
  - 3-5 checklist items → SMALL
  - 6+ checklist items → FEATURE

Present the extracted milestones to the user:

> "Found {N} milestones in the roadmap:"
>
> | # | ID | Name | Scope | Depends on |
> |---|-----|------|-------|------------|
> | 1 | P0-A | [name] | SMALL | Nothing |
> | 2 | P0-B | [name] | FEATURE | P0-A |
> | ... |
>
> "Generate specs for all milestones, or select specific ones?"
>
> 1. All milestones
> 2. Select milestones (comma-separated numbers)

### 4. Resolve Artifact Paths

Before generating specs, resolve the output paths:

1. **Resolve project root** per `artifact-paths` skill.
2. **Derive feature directory** from the roadmap's parent: `{project_root}/.skilmarillion/projects/{slug}/specs/`
3. **Count existing specs** to determine the starting SPEC number.
4. **Confirm base path with user** per `artifact-paths` slug confirmation protocol:
   > "Specs will be saved to `{project_root}/.skilmarillion/projects/{slug}/specs/SPEC-{NNN}-{slug}.md`. Confirm?"
5. **Create directory** if it does not exist:
   ```bash
   mkdir -p {project_root}/.skilmarillion/projects/{slug}/specs
   ```

### 5. Generate Specs in Parallel

Launch spec generation for multiple milestones concurrently using the `Task` tool. Group milestones into batches by dependency order — milestones with no unresolved dependencies can run in parallel.

#### Dependency-Aware Batching

1. **Batch 0** — All milestones with `Depends on: Nothing` (or no dependencies).
2. **Batch 1** — Milestones whose dependencies are all in Batch 0.
3. **Batch N** — Milestones whose dependencies are all in Batch 0..N-1.

Within each batch, launch all milestones in parallel.

#### Per-Milestone Spec Generation

For each milestone, the generation pipeline depends on its estimated scope:

##### TRIVIAL

1. Draft a lightweight spec directly with:
   - **Problem Statement** — derived from the milestone's `What` field
   - **Acceptance Criteria** — happy path only, Given/When/Then format, derived from the milestone's checklist
2. **TDD planning:** Delegate to `tdd-planner` agent via Task:
   ```
   Task: tdd-planner agent
   Input: { "spec_content": "{spec_draft}", "arch_recommendation": "" }
   ```
3. Append the TDD plan to the spec draft.

##### SMALL

1. **Context gathering:** Delegate to `context-gatherer` agent via Task:
   ```
   Task: context-gatherer agent
   Input: { "task": "{milestone What}", "triage_result": { "size": "SMALL", "risk": "{milestone risk}", "routing_decision": "lightweight_spec", "slug": "{milestone slug}" } }
   ```
2. **Spec building:** Delegate to `spec-builder` agent via Task:
   ```
   Task: spec-builder agent
   Input: { "task": "{milestone What}", "triage_result": { "size": "SMALL", "risk": "{milestone risk}", "routing_decision": "lightweight_spec", "slug": "{milestone slug}" }, "context": {context JSON}, "mode": "small" }
   ```
3. **Architecture advising:** Delegate to `architecture-advisor` agent via Task:
   ```
   Task: architecture-advisor agent
   Input: { "spec_content": "{spec_draft}", "context": {context JSON} }
   ```
4. **TDD planning:** Delegate to `tdd-planner` agent via Task:
   ```
   Task: tdd-planner agent
   Input: { "spec_content": "{spec_draft}\n\n{arch_section}", "arch_recommendation": "{arch_section}" }
   ```
5. **Assemble spec:** Replace placeholders with agent outputs.

##### FEATURE

1. **Context gathering:** Delegate to `context-gatherer` agent via Task:
   ```
   Task: context-gatherer agent
   Input: { "task": "{milestone What}", "triage_result": { "size": "FEATURE", "risk": "{milestone risk}", "routing_decision": "full_workflow", "slug": "{milestone slug}" } }
   ```
2. **Spec building:** Delegate to `spec-builder` agent via Task:
   ```
   Task: spec-builder agent
   Input: { "task": "{milestone What}", "triage_result": { "size": "FEATURE", "risk": "{milestone risk}", "routing_decision": "full_workflow", "slug": "{milestone slug}" }, "context": {context JSON}, "mode": "feature" }
   ```
3. **Architecture advising:** Delegate to `architecture-advisor` agent via Task:
   ```
   Task: architecture-advisor agent
   Input: { "spec_content": "{spec_draft}", "context": {context JSON} }
   ```
4. **TDD planning:** Delegate to `tdd-planner` agent via Task:
   ```
   Task: tdd-planner agent
   Input: { "spec_content": "{spec_draft}\n\n{arch_section}", "arch_recommendation": "{arch_section}" }
   ```
5. **Assemble spec:** Replace placeholders with agent outputs.

### 6. Validate and Save

For each generated spec:

1. Derive the slug from the milestone name using the `artifact-paths` slug algorithm.
2. Assign the next auto-incrementing SPEC number.
3. Save the spec to `{project_root}/.skilmarillion/projects/{slug}/specs/SPEC-{NNN}-{slug}.md` using the Write tool.
4. **Validation gate:** Run the validation script:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {spec_path} --type spec --json
   ```
   - If score >= 70: **PASS** — proceed.
   - If score < 70: display findings, re-draft failing sections using findings as feedback, re-validate. Repeat until score >= 70.
5. Display per-spec status as each completes:
   > `SPEC-{NNN}-{slug}.md` — PASS ({score}/100)

### 7. Update Roadmap Spec Index

After all specs are generated and validated, update the Spec Index table in the ROADMAP:

1. Read the ROADMAP file.
2. Locate the `## Spec Index` section.
3. For each generated spec, add or update a row:
   ```
   | SPEC-{NNN} | {milestone name} | DRAFT | {phase} | {feature ID} |
   ```
4. Save the updated ROADMAP using the Edit tool.

### 8. Summary and Next Steps

Present the generation summary:

> **Specs generated:** {N} of {total milestones}
>
> | Spec | Milestone | Score | Status |
> |------|-----------|-------|--------|
> | SPEC-001-{slug} | P0-A: {name} | 85 | PASS |
> | SPEC-002-{slug} | P0-B: {name} | 78 | PASS |
> | ... |

If any specs failed validation after retries, list them with their findings.

---

## NEXT STEP BREADCRUMB

After all specs are generated, display:

> **All specs generated.** Next step: run `/impl:tdd` on each spec to begin implementation.
>
> Suggested commands (in dependency order):
> ```
> /impl:tdd .skilmarillion/projects/{slug}/specs/SPEC-001-{slug}.md
> /impl:tdd .skilmarillion/projects/{slug}/specs/SPEC-002-{slug}.md
> ...
> ```

**If the `impl` plugin is not installed:** Check whether `/impl:tdd` is available by looking for `impl/` in the plugin directory or checking plugin manifest. If not found, display instead:

> **All specs generated.** Next step: run `/impl:tdd {spec-path}` on each spec to begin implementation.
>
> The `impl` plugin is not yet installed. Install it with:
> ```
> claude plugin add impl
> ```

---

## WHAT NOT TO DO

- Do NOT generate specs without a validated ROADMAP as input — refuse and suggest `/plan:roadmap` first.
- Do NOT triage milestones — the ROADMAP already provides scope estimates from the PRD decomposition.
- Do NOT ask design questions per milestone — the PRD and ROADMAP already captured requirements. Use the milestone's `What` and `Checklist` as the task description for agents.
- Do NOT run milestones sequentially when they have no dependency relationship — use parallel agents.
- Do NOT skip the validation gate — every spec must score >= 70 before it is considered complete.
- Do NOT modify the ROADMAP except for the Spec Index table update.
- Do NOT hardcode paths — use the `artifact-paths` skill for all path resolution.
- Do NOT skip the slug confirmation protocol — always confirm the base save path with the user.
