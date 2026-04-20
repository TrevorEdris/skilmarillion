# /fellowship:plan --specify

Generate one SPEC per wave-agent from a wave-based ROADMAP. Reads the roadmap, extracts `W{N}{letter}` wave-agents, re-validates wave independence, then authors SPECs in wave-batched parallel passes.

Run after `/fellowship:plan --roadmap` (which produced both ROADMAP.md and DISCOVERY.md) and before `/fellowship:build`.

---

## Flow

### 1. Input Resolution

Delegate ROADMAP discovery to the `artifact-resolver` agent. See `artifact-paths` skill § "Artifact Resolution" for the calling contract.

```
Task: artifact-resolver agent
Input: {
  "artifact_type": "roadmap",
  "query": "{raw $ARGUMENTS}",
  "project_root": "{resolved project root}"
}
```

Confirm the selected ROADMAP with the user per the caller flow in the `artifact-paths` skill — present candidates via `AskUserQuestion` for every `match_type` and wait for explicit selection.

If no ROADMAPs exist at all (agent returns empty `all`), display:
> "No ROADMAPs found under `.skilmarillion/projects/*/ROADMAP.md`. Run `/fellowship:plan --roadmap` to create one, or provide a ROADMAP path directly."

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. ROADMAP Validation Gate

1. Derive the feature directory from the roadmap path (parent directory).
2. Require `{feature-dir}/DISCOVERY.md`. If absent, stop and instruct the user to re-run `/fellowship:plan --roadmap` — specify cannot author SPECs without discovery context.
3. Check for `{feature-dir}/PRD.md` — if present, validate it:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {prd_path} --type prd --json
   ```
   - If score < 85: warn the user but do not block (the roadmap may have been created independently).

4. Read the ROADMAP file and verify it contains:
   - At least one phase section (`## Phase N:`)
   - At least one wave section (`### Wave N.M`)
   - At least one wave-agent block (`#### W{N}{letter}:`)
   - A Spec Index section

If the roadmap has no parseable wave-agents, stop and report: "Could not find wave-agents in the roadmap. Expected format: `#### W1a: [Agent Name]` with `**Scope:**`, `**Touches:**`, `**Depends on:**`, `**Acceptance:**`, `**Spec:**` fields."

### 3. Extract Wave Agents

Parse the ROADMAP. For each wave-agent, capture:

- **Wave-agent ID** — e.g., `W1a`, `W1b`, `W2a`
- **Phase + Wave** — the containing `## Phase N:` and `### Wave N.M` headers
- **Name** — heading text after the ID
- **Scope** — one-sentence `**Scope:**` value
- **Touches** — file paths from `**Touches:**` (comma or line-separated)
- **Depends on** — IDs from `**Depends on:**` (or `Nothing`)
- **Acceptance** — PRD requirement IDs from `**Acceptance:**` (e.g., `FR-001, FR-002`)
- **Spec slug** — from `**Spec:**` value (or derive via `slug-namer`)

Present the extracted wave-agents to the user:

> "Found {N} wave-agents across {P} phases / {W} waves:"
>
> | ID | Phase.Wave | Name | Touches | Depends on |
> |----|-----------|------|---------|------------|
> | W1a | 1.1 | [name] | `repo.go` | Nothing |
> | W1b | 1.1 | [name] | `events.go` | Nothing |
> | W2a | 2.1 | [name] | `api.go` | W1a |
>
> "Generate SPECs for all wave-agents, or select specific ones?"
>
> 1. All wave-agents
> 2. Select a single wave (e.g., `Wave 1.1`)
> 3. Select specific IDs (comma-separated, e.g., `W1a, W2a`)

### 3b. Collision + Dependency Revalidation Gate

Before spawning any spec-builder, re-run two checks against the extracted wave-agent set. ROADMAP is a markdown file and users may have hand-edited it since `wave-planner` ran.

**Check 1 — Touches collision.** For every pair `(A, B)` within the same wave, assert `A.touches ∩ B.touches == ∅`.

**Check 2 — `depends_on` acyclicity and ordering.** Build the directed graph where each edge `A → B` means "B depends on A." Assert:

- the graph is a DAG (no cycles; run Kahn's algorithm or equivalent);
- every dependency target exists in the wave-agent set;
- every dependency points to an **earlier** wave (same-wave or later-wave references are illegal per `skills/wave-format § Dependency Rule`).

If any check fails, STOP and report:

> "Roadmap drift detected:
> - Collisions: W{id} and W{id} in Wave N.M both touch `{file}`
> - Dependency violations: W{id} depends_on W{id} but the target is in the same or a later wave (or forms a cycle)
>
> Re-plan waves before generating SPECs:
>
> ```
> /fellowship:plan --roadmap {roadmap-path}
> ```
> "

This gate prevents SPECs that would write-conflict at build time or deadlock the wave barrier.

### 4. Resolve Artifact Paths

1. **Resolve project root** per `artifact-paths` skill.
2. **Derive specs directory** from the roadmap's parent: `{project_root}/.skilmarillion/projects/{slug}/specs/`
3. **Confirm base path with user** per `artifact-paths` slug confirmation protocol:
   > "SPECs will be saved to `{project_root}/.skilmarillion/projects/{slug}/specs/SPEC-{wave_id}-{slug}.md`. Confirm?"
4. **Create directory** if it does not exist:
   ```bash
   mkdir -p {project_root}/.skilmarillion/projects/{slug}/specs
   ```

### 5. Generate SPECs — Wave-Batched Parallel

Waves are hard sync barriers. Within a single wave, spawn all wave-agents' SPEC pipelines concurrently via the Task tool. Do not start Wave N.M+1 until every SPEC in Wave N.M has been authored and validated.

Across phases, the same rule applies: Wave 2.1 starts only after every SPEC in Wave 1.N has passed.

#### Per-Wave-Agent SPEC Pipeline

For each wave-agent in the current wave, run this chain (all agents within a wave run in parallel with each other; each agent's own chain is sequential):

1. **Context gathering (spec scope):**
   ```
   Task: context-gatherer agent
   Input: {
     "task": "{wave_agent.scope}",
     "scope": "spec",
     "touches": {wave_agent.touches},
     "triage_result": null
   }
   ```
   Returns JSON with `entry_points`, `relevant_files`, `patterns`, `conventions`.

2. **Spec building:**
   ```
   Task: spec-builder agent
   Input: {
     "wave_assignment": {
       "id": "{wave_agent.id}",
       "name": "{wave_agent.name}",
       "scope": "{wave_agent.scope}",
       "touches": {wave_agent.touches},
       "depends_on": {wave_agent.depends_on},
       "acceptance": "{wave_agent.acceptance}"
     },
     "prd_path": "{absolute path to PRD.md}",
     "prd_references": {list of FR-IDs from acceptance},
     "discovery_path": "{absolute path to DISCOVERY.md}",
     "context": {context JSON},
     "paired_prd_phase": { "id": "{phase id}", "name": "{phase name}" },
     "wave_id": "{wave_agent.id}"
   }
   ```
   Returns raw SPEC markdown. Save to `specs/SPEC-{wave_id}-{slug}.md`.

3. **Architecture advising (spec level):**
   ```
   Task: architecture-advisor agent
   Input: {
     "spec_content": "{spec markdown}",
     "context": {context JSON},
     "invocation_level": "spec"
   }
   ```
   Append the returned `## Architecture Recommendation` section to the SPEC.

4. **TDD planning:**
   ```
   Task: tdd-planner agent
   Input: {
     "spec_content": "{spec markdown with arch}",
     "arch_recommendation": "{arch section}"
   }
   ```
   Merge the returned TDD plan into the SPEC's Ordered Implementation Steps (spec-builder emits a draft; tdd-planner refines RED-GREEN cadence).

### 6. Validate and Save

For each generated SPEC:

1. Assert `frontmatter.touches ⊆ wave_assignment.touches`. If divergence, warn the user and re-run spec-builder on the offending wave-agent (validator also catches this).
2. Run the validator:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {spec_path} --type spec --json
   ```
   - If score >= 85: **PASS** — mark complete.
   - If score < 85: display findings, re-draft failing sections using findings as feedback, re-validate. Repeat until score >= 85.
3. Display per-SPEC status as each completes:
   > `SPEC-{wave_id}-{slug}.md` — PASS ({score}/100)

### 7. Update Roadmap Spec Index

After all SPECs in the requested wave(s) pass, update the Spec Index table in the ROADMAP:

1. Read the ROADMAP file.
2. Locate the `## Spec Index` section.
3. For each generated SPEC, update the matching `SPEC-{wave_id}` row's Status from `PENDING` to `DRAFT`.
4. Save the updated ROADMAP using the Edit tool.

### 8. Summary and Next Steps

Present the generation summary:

> **SPECs generated:** {N} of {total wave-agents in selected scope}
>
> | SPEC | Wave | Score | Status |
> |------|------|-------|--------|
> | SPEC-W1a-{slug} | 1.1 | 92 | PASS |
> | SPEC-W1b-{slug} | 1.1 | 88 | PASS |
> | SPEC-W2a-{slug} | 2.1 | 90 | PASS |

If any SPECs failed validation after retries, list them with their findings.

---

## NEXT STEP BREADCRUMB

After SPECs are generated, display:

> **SPECs ready.** Next step: run `/fellowship:build` by wave or by individual spec.
>
> ```
> /fellowship:build wave 1               # run all W1* wave-agents in parallel
> /fellowship:build spec W1a             # run a single wave-agent
> /fellowship:build wave 1 --team        # spawn Agent Teams instead of Task subagents
> ```

> `/fellowship:build` is part of this plugin — no additional install needed.

---

## WHAT NOT TO DO

- Do NOT generate SPECs from a roadmap that is missing DISCOVERY.md — re-run `/fellowship:plan --roadmap` first.
- Do NOT skip the collision revalidation gate — a drifted roadmap is the most common source of wave-merge conflicts.
- Do NOT triage wave-agents — the ROADMAP (via `wave-planner`) already locked scope and touches.
- Do NOT ask design questions per wave-agent — the SPEC compiles from PRD + DISCOVERY + wave assignment.
- Do NOT run wave-agents sequentially within a wave — always parallel.
- Do NOT start Wave N.M+1 until every SPEC in Wave N.M has passed validation.
- Do NOT skip the validation gate — every SPEC must score >= 85 before it is considered complete.
- Do NOT modify the ROADMAP except for the Spec Index table update.
- Do NOT hardcode paths — use the `artifact-paths` skill for all path resolution.
- Do NOT skip the slug confirmation protocol — always confirm the base save path with the user.
