# /fellowship:plan --roadmap

Decompose an approved PRD into a phased, wave-based roadmap. Each phase is a PRD delivery phase. Each wave inside a phase is a set of parallel, independent wave-agents (`W{N}{letter}`). Each wave-agent later becomes one SPEC via `/fellowship:plan --specify`.

This stage runs DISCOVERY inline via `context-gatherer` at `scope: roadmap`, then delegates wave decomposition to `wave-planner`.

---

## Flow

### 1. Input Resolution

Delegate PRD discovery to the `artifact-resolver` agent. See `artifact-paths` skill § "Artifact Resolution" for the calling contract.

```
Task: artifact-resolver agent
Input: {
  "artifact_type": "prd",
  "query": "{raw $ARGUMENTS}",
  "project_root": "{resolved project root}"
}
```

Confirm the selected PRD with the user per the caller flow in the `artifact-paths` skill — present candidates via `AskUserQuestion` for every `match_type` and wait for explicit selection.

If no PRDs exist at all (agent returns empty `all`), display:
> "No PRDs found under `.skilmarillion/projects/*/PRD.md`. Run `/fellowship:plan --prd` to create one, or provide a PRD path directly."

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. PRD Validation Gate

Before proceeding, validate the PRD:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py {prd_path} --type prd --verbose --json
```

- If score >= 85: **PASS** — proceed to step 3.
- If score < 85: **STOP** — display findings and tell the user: "PRD needs work before roadmap generation. Run `/fellowship:plan --validate {prd_path}` to see findings, then update the PRD and re-run `/fellowship:plan --roadmap`."

Do NOT proceed with roadmap generation on an unvalidated PRD.

### 3. Read and Analyze the PRD

Extract:
- All functional requirements (FR-NNN) with priorities and acceptance criteria
- All non-functional requirements (NFR-NNN)
- PRD delivery phase structure (the top-level phases become roadmap Phase N sections 1:1)
- Dependencies between requirements
- Cross-cutting constraints

### 3a. Inline Discovery

Delegate to the `context-gatherer` agent at `scope: roadmap`:

```
Task: context-gatherer agent
Input: {
  "task": "{prd_title} — {prd_summary}",
  "scope": "roadmap",
  "prd_path": "{absolute path to PRD.md}"
}
```

The agent returns a JSON block with `entry_points`, `relevant_files`, `patterns`, `conventions` (naming/structure/testing/errors), and `hotspots`. Persist this for step 4b and for the Discovery Summary rendered in step 6.

Write the raw discovery findings to `{project_root}/.skilmarillion/projects/{slug}/DISCOVERY.md` using the Write tool — this file is consumed by `/fellowship:plan --specify` and by every `spec-builder` invocation downstream.

### 4. Decompose into Phases

Phases are PRD-defined. Map each PRD delivery phase to one roadmap Phase N section. Do NOT invent phases.

For each phase, capture:
- **Entry criteria** — what must be true before the phase starts (prior phase complete, dependencies available)
- **Exit criteria** — measurable condition for phase complete
- **Deliverable** — one-sentence milestone

### 4b. Wave Planning

Delegate to the `wave-planner` agent:

```
Task: wave-planner agent
Input: {
  "prd_path": "{absolute path to PRD.md}",
  "discovery_path": "{absolute path to DISCOVERY.md}",
  "project_root": "{resolved project root}",
  "max_wave_attempts": 3
}
```

The agent returns the JSON contract defined in `skills/wave-format`:
- `phases[]` — one per PRD phase
- `phases[].waves[]` — parallel batches within a phase
- `waves[].agents[]` — wave-agents with `id`, `name`, `scope`, `touches`, `depends_on`, `acceptance`
- `collisions_resolved` — integer count of re-buckets performed
- `collisions_unresolved` — list; MUST be empty to proceed

**Gate:** If `collisions_unresolved` is non-empty, STOP. Display the unresolved collisions to the user and ask how to proceed (split scope, merge agents, or accept serial execution). Do NOT produce a partial roadmap.

Record `collisions_resolved` — it appears in the Independence Check rationale block.

### 5. Identify Cross-Phase Dependencies

Validate `depends_on` references — every entry in a wave-agent's `depends_on` must point to an earlier wave of the same phase, or any earlier phase. The wave-planner already enforces this, but re-check here and surface any anomalies.

### 6. Produce ROADMAP.md

Load `${CLAUDE_PLUGIN_ROOT}/references/roadmap-template.md` for the canonical format. Render the wave-planner JSON into the template:

- **Current Status** — Phase 1, Wave 1.1, all wave-agents `PENDING`.
- **Philosophy** — Infer from the PRD's problem statement and project context. Present the inferred philosophy statement to the user for confirmation before finalizing. Keep it to 1-2 sentences.
- **Discovery Summary** — Render `entry_points`, `layout` (from `patterns`), `conventions`, `hotspots` from the step 3a output.
- **Phase sections** — one per `phases[]` entry. Inside each, one `### Wave N.M` per `waves[]`. Inside each wave, one `#### W{N}{letter}: {agent.name}` block per agent, with required bullets: `Scope`, `Touches`, `Depends on`, `Acceptance`, `Spec`.
- **Cross-Cutting Concerns** — Map from PRD NFRs.
- **Dependency Summary** — External dependencies with status.
- **Independence Check** — Table with one row per wave. Add the `collisions_resolved: N` footnote.
- **Spec Index** — Pre-populate one row per wave-agent: `SPEC-W{N}{letter}` | `{wave}` | `{scope}` | `PENDING`.

### 7. Save

Resolve artifact path per `artifact-paths` skill:

1. **Resolve project root** — determine which git repo this roadmap targets (git root of target project, not necessarily CWD). See `artifact-paths` skill for the resolution chain.
2. **Derive feature slug** from the PRD's feature name by delegating to the `slug-namer` agent, then **confirm the proposed slug with the user** via `AskUserQuestion` before resolving any paths. Re-call the agent if the user supplies an alternative.
3. **Derive domain** from the feature context (e.g., `auth`, `billing`, `core`). Present for user confirmation.
4. **Derive roadmap path:** `{project_root}/.skilmarillion/projects/{feature-slug}/ROADMAP.md`
5. **Confirm path with user** per `artifact-paths` slug confirmation protocol. Show full absolute path on first save. User may accept, override the slug/domain, or correct the project root.
6. **Create directory** if it does not exist: `mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}`
7. **Save** roadmap using Write tool to the confirmed path. Save DISCOVERY.md alongside it (see step 3a).

### 8. Confirm and Suggest Next Step

Present the roadmap summary to the user:
- Phase count, wave count, and wave-agent count
- `collisions_resolved` count (how many re-buckets the wave-planner performed)
- Any PRD requirements that didn't map cleanly to a single wave-agent

Suggest next step:

> **Roadmap saved.** Next step: run `/fellowship:plan --specify` to generate one SPEC per wave-agent.
>
> ```
> /fellowship:plan --specify {roadmap-path}
> ```
> This generates `specs/SPEC-W{N}{letter}-{slug}.md` for each wave-agent. Within a wave, SPECs are authored in parallel.

---

## WHAT NOT TO DO

- Do NOT generate a roadmap from an unvalidated PRD (score < 85) — refuse and explain why.
- Do NOT include implementation details in the roadmap (file paths beyond `Touches:`, code snippets, database schemas) — that belongs in SPECs.
- Do NOT invent phases that the PRD does not define.
- Do NOT skip the philosophy confirmation — infer it, but always present for user approval.
- Do NOT hardcode paths — use the `artifact-paths` skill for all path resolution.
- Do NOT modify any existing files — this command only creates new roadmaps and a new DISCOVERY.md.
- Do NOT skip the slug confirmation protocol — always confirm the save path with the user.
- Do NOT proceed with any `collisions_unresolved` — surface them to the user and stop.
