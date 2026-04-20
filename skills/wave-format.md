---
name: wave-format
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, roadmap, waves]
---

# wave-format

Defines the canonical Phase → Wave → Wave-Agent decomposition used by `wave-planner` and consumed by `roadmap-template`, `spec-builder`, and `commands/build.md`.

---

## Vocabulary

| Term | Meaning |
|------|---------|
| **Phase** | A PRD-level delivery slice (e.g., "Phase 1: Data + Events"). Maps 1:1 to a section in the PRD's Milestones / Delivery Phases. |
| **Wave** | A set of wave-agents within a phase that all run in parallel. Wave N+1 cannot start until every agent in Wave N has merged + green CI. |
| **Wave-Agent** | A single Claude Code session executing one SPEC. Identified as `W{N}{letter}` where N = wave number, letter = `a..z` within that wave. |
| **Touches** | The list of file paths a wave-agent will create/modify. Authoritative source of truth for collision detection. |

---

## Wave-Agent ID Convention

- Format: `W{N}{letter}` — examples: `W1a`, `W1b`, `W2a`, `W3c`
- N is the **global wave sequence number** (1-indexed, monotonic across phases). N advances each time a new wave opens, whether that wave is the first of a new phase or a later sub-wave within the same phase.
- letter is `a` through `z` (lowercase, no punctuation), unique within a single wave
- IDs are globally unique across the project, not per-phase
- **Re-bucket rule (canonical):** when `wave-planner` re-buckets an agent because of a collision, the agent moves to the **next wave**, its N advances to that new wave's global sequence number, and the letter restarts at `a` within the new wave. Letters are never reused inside the same wave.

### Example

Given Phase 1 with two waves and Phase 2 with one wave:

| Wave | Phase.Seq | Agents |
|------|-----------|--------|
| Global wave 1 | Phase 1, wave 1.1 | `W1a`, `W1b` |
| Global wave 2 | Phase 1, wave 1.2 | `W2a`, `W2b` |
| Global wave 3 | Phase 2, wave 2.1 | `W3a` |

Note: the "1" in the wave-agent ID `W1a` is the global wave sequence number (matches the "1" in "wave 1.1"). When Phase 1 opens a second wave (`wave 1.2`), its agents start at `W2a`, not `W1c`.

---

## Independence Rule

Two wave-agents may run in parallel iff their `Touches` lists are disjoint as **write sets**. Read-only sharing is permitted.

```
W{X}.touches ∩ W{Y}.touches = ∅
```

If a SPEC needs to *read* a file owned by another agent, that is permitted — only writes collide. The roadmap stage must track this distinction explicitly when it emits a wave.

---

## JSON Output Contract (wave-planner)

`wave-planner` emits one JSON object per `--roadmap` invocation:

```json
{
  "phases": [
    {
      "id": "1",
      "name": "Data + Events",
      "entry_criteria": "PRD signed off",
      "exit_criteria": "Refund row + event emit live in staging",
      "waves": [
        {
          "id": "1.1",
          "agents": [
            {
              "id": "W1a",
              "name": "refund repo",
              "scope": "Add MarkApproved / MarkDenied to refund repo + tests.",
              "touches": ["internal/refund/repo.go", "internal/refund/repo_test.go"],
              "depends_on": [],
              "acceptance": "FR-003, FR-004"
            },
            {
              "id": "W1b",
              "name": "refund events",
              "scope": "Define RefundApproved / RefundDenied event payloads.",
              "touches": ["internal/events/refund.go", "internal/events/refund_test.go"],
              "depends_on": [],
              "acceptance": "FR-007"
            }
          ]
        },
        {
          "id": "1.2",
          "agents": [
            {
              "id": "W2a",
              "name": "refund api",
              "scope": "Wire HTTP endpoint /refunds/{id}/approve to repo + event.",
              "touches": ["cmd/api/refund.go", "cmd/api/refund_test.go"],
              "depends_on": ["W1a", "W1b"],
              "acceptance": "FR-005"
            }
          ]
        }
      ]
    }
  ],
  "collisions_resolved": 0,
  "collisions_unresolved": []
}
```

### Field Definitions

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `phases[].id` | string | yes | matches PRD phase numbering |
| `phases[].name` | string | yes | from PRD |
| `phases[].entry_criteria` | string | yes | what must be true to start |
| `phases[].exit_criteria` | string | yes | what proves the phase shipped |
| `phases[].waves[].id` | string | yes | format `{phase}.{wave_seq_in_phase}` |
| `phases[].waves[].agents[].id` | string | yes | `W{N}{letter}` global ID |
| `phases[].waves[].agents[].name` | string | yes | short noun phrase |
| `phases[].waves[].agents[].scope` | string | yes | one sentence |
| `phases[].waves[].agents[].touches` | string[] | yes | file paths; write set |
| `phases[].waves[].agents[].depends_on` | string[] | yes | wave-agent IDs that must complete first |
| `phases[].waves[].agents[].acceptance` | string | yes | comma-separated PRD requirement IDs |
| `collisions_resolved` | int | yes | count of agents auto-bucketed to a later wave |
| `collisions_unresolved` | array | yes | non-empty = wave-planner failure |

---

## Collision Detection + Re-Bucket Algorithm

Run after the initial assignment, before emitting JSON.

```
for each wave W:
    for each pair (agent_i, agent_j) in W.agents:
        if agent_i.touches ∩ agent_j.touches != ∅:
            move smaller-scope agent to wave W+1
            increment collisions_resolved
            re-check W and W+1
            if iteration count > max_wave_attempts (default 3):
                append to collisions_unresolved with full collision detail
                exit
```

`max_wave_attempts` is configurable (default 3). On unresolved collisions, the planner returns a structured error to the human operator — no SPECs are generated until resolved.

---

## Dependency Rule

`depends_on` may only reference wave-agents in **earlier** waves of the same phase, or any wave of an earlier phase. A `depends_on` entry pointing to a same-wave or later-wave agent is invalid and must trigger collision/re-bucket.

---

## Authoring Heuristics (Soft)

- Aim for 2-5 wave-agents per wave. Single-agent waves are acceptable but lose parallelism benefit.
- Aim for ≤4 waves per phase. Larger fan-outs suggest the phase should split.
- Prefer agents whose `Touches` list is 1-3 files. Agents touching >5 files are usually too coarse — split.
- Each wave-agent's `scope` must compress to one sentence. If it can't, it's not a single agent's work.

---

## Mapping to ROADMAP.md

The `roadmap-template` renders this JSON as:

```
## Phase {id}: {name}
### Wave {wave.id}
#### {agent.id}: {agent.name}
- **Scope:** {agent.scope}
- **Touches:** {agent.touches joined with `, `}
- **Depends on:** {agent.depends_on joined or "Nothing"}
- **Spec:** SPEC-{agent.id}-{slug} (PENDING)
```

The `## Independence Check` table in ROADMAP is populated from `collisions_resolved` + `collisions_unresolved`.

---

## Mapping to SPEC.md

For each wave-agent, `spec-builder` produces `specs/SPEC-{agent.id}-{slug}.md`. The SPEC frontmatter `touches` array MUST be a subset of the corresponding ROADMAP `Touches:` list. Validator warns on divergence.

---

## Build Dispatch Inputs

`/fellowship:build` reads the wave structure to dispatch:

| Invocation | Behavior |
|------------|----------|
| `build wave N` | Spawn parallel Task subagents for every agent whose ID starts with `W{N}` |
| `build spec W{N}{letter}` | Spawn one agent for the named SPEC |
| `build wave N --team` | Use Agent Teams primitives (`TeamCreate`) instead of Task subagents |

---

## Validation

`scripts/validate.py` validates ROADMAP.md against this schema (touches subset check, ID format, depends_on resolvability) when `--type roadmap` is passed (future work).
