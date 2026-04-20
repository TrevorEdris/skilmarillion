# ROADMAP.md Template

Unified roadmap document. Top-level sections are PRD delivery phases. Each phase contains waves of independent, parallel wave-agents. Produced from an approved PRD via `/fellowship:plan --roadmap` (which chains `context-gatherer` → `wave-planner`).

---

## Structure

```markdown
# [Project Name] — Roadmap

## Current Status

**Phase:** [current phase]
**Wave:** [current wave, e.g. `1.2`]
**Last Updated:** [date]

### Completed
- [x] Phase 0: [name]

### In Progress
- [ ] Phase 1: [name] — Wave 1.1 (W1a, W1b)

---

## Philosophy

[1-2 sentences: wave-based parallel decomposition. Each wave-agent owns a disjoint file set; waves are hard sync barriers.]

---

## Discovery Summary

Auto-populated from `context-gatherer` at `scope: roadmap`.

- **Entry points:** [files]
- **Layout:** [top-level directory structure]
- **Conventions:** [naming, testing, error handling]
- **Hotspots:** [directories expected to receive heavy edits]

---

## Phase 1: [Name]

**Entry Criteria:** [What must be true before this phase starts]
**Exit Criteria:** [What must be true for this phase to be complete]

### Wave 1.1

> All W1a/W1b/W1c… agents in this wave run in parallel on disjoint file sets. No wave-agent reads or depends on another wave-agent's in-flight output. The wave closes when every agent's PR is green.

#### W1a: [Agent Name]

- **Scope:** [One sentence — the atomic deliverable this agent owns.]
- **Touches:** `path/to/file_a.go`, `path/to/file_b.go`
- **Depends on:** [`W{id}` of an agent in an earlier wave/phase, or `Nothing`]
- **Acceptance:** FR-001, FR-002
- **Spec:** `specs/SPEC-W1a-{slug}.md`

#### W1b: [Agent Name]

- **Scope:** ...
- **Touches:** ...
- **Depends on:** Nothing
- **Acceptance:** FR-003
- **Spec:** `specs/SPEC-W1b-{slug}.md`

### Wave 1.2

#### W1c: [Agent Name]

- **Scope:** ...
- **Touches:** ...
- **Depends on:** W1a, W1b
- **Acceptance:** FR-004
- **Spec:** `specs/SPEC-W1c-{slug}.md`

**Deliverable:** *[One-sentence milestone statement — what ships when the phase closes.]*

---

## Phase 2: [Name]

**Entry Criteria:** Phase 1 complete.
**Exit Criteria:** [Measurable outcome.]

### Wave 2.1

#### W2a: [Agent Name]
...

**Deliverable:** *...*

---

## Cross-Cutting Concerns

[Constraints that apply across all phases — technology choices, platform targets,
performance budgets, compliance requirements. Reference NFRs from the PRD.]

---

## Dependency Summary

| Dependency | Source | Status |
|-----------|--------|--------|
| [Library/API/Team] | [Where it comes from] | [Available / Pending / Blocked] |

---

## Independence Check

Collision audit from `wave-planner`. A green check means no two agents in the same wave touch the same file.

| Wave | Collision? | Notes |
|------|-----------|-------|
| 1.1 | None | W1a ∩ W1b = ∅ |
| 1.2 | None | solo |
| 2.1 | None | — |

`collisions_resolved`: 0 (re-buckets performed by wave-planner)

---

## Spec Index

| ID | Wave | Scope | Status |
|----|------|-------|--------|
| SPEC-W1a | 1.1 | [scope] | PENDING |
| SPEC-W1b | 1.1 | [scope] | PENDING |
| SPEC-W1c | 1.2 | [scope] | PENDING |
| SPEC-W2a | 2.1 | [scope] | PENDING |

Status values: **PENDING** | **DRAFT** | **REVIEW** | **FINAL**
```

---

## Wave-Agent ID Convention

Wave-agents use the format `W{N}{letter}`:
- `W1a` — first agent in Phase 1, Wave 1.1
- `W1b` — second agent in the same or next wave of Phase 1
- `W2a` — first agent of Phase 2

Letters are monotonic across waves within a phase. `W1a` and `W1b` may live in the same wave (parallel) or different waves (sequential) — the `### Wave N.M` header groups them.

The wave-agent ID maps 1:1 to a SPEC filename: `specs/SPEC-{wave_id}-{slug}.md`.

---

## Independence Rule

Within a single wave, no two agents' `Touches:` lists may share a file. Read-only file sharing is allowed — two agents may read the same file. Writes must be disjoint.

If two candidate agents collide on a file, `wave-planner` moves the smaller-scope agent to the next wave. Up to `max_wave_attempts` (default 3) re-buckets are allowed before the planner fails loud.

---

## Audience Guide

| Section | Product reads? | Engineering reads? |
|---------|---------------|-------------------|
| Current Status | Yes | Yes |
| Philosophy | Yes | Yes |
| Discovery Summary | Sometimes | Yes |
| Phase entry/exit criteria | Yes | Yes |
| Wave block (parallelism note) | Sometimes | Yes |
| Wave-agent — Scope / Depends on / Acceptance | Yes | Yes |
| Wave-agent — Touches | No (implementation detail) | Yes |
| Deliverable statement | Yes | Yes |
| Cross-Cutting Concerns | Sometimes | Yes |
| Dependency Summary | Yes | Yes |
| Independence Check | No | Yes |
| Spec Index | Sometimes | Yes |
