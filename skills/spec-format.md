---
name: spec-format
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, spec]
---

# spec-format

Defines the canonical SPEC schema used by `spec-builder`. A SPEC is one wave-agent's complete implementation plan — there is no separate PLAN artifact.

---

## File Naming

```
.skilmarillion/projects/{slug}/specs/SPEC-{wave_id}-{slug}.md
```

Where `wave_id` is `W{N}{letter}` (e.g., `W1a`, `W2c`). One SPEC per wave-agent.

---

## Required Sections

Every SPEC must include all of the following sections, in order. A SPEC missing any required section fails validation.

1. **Header / Metadata** — frontmatter + summary block (see schema below)
2. **Problem Statement** — one paragraph; what this wave-agent delivers and why
3. **Acceptance Criteria** — Given/When/Then format, one behavior per AC
4. **Target Repo** — single repo path (typically the project root)
5. **Files to Touch** — explicit list of file paths the agent will create/modify
6. **Structure** — phase breakdown if the SPEC's work splits into internal slices
7. **Ordered Implementation Steps** — atomic 2-5 minute steps with file paths and RED-GREEN markers
8. **Risks & Assumptions** — what could go wrong, what we're assuming
9. **Verification Plan** — how to confirm correctness (test/lint/build/manual)
10. **Out of Scope** — explicit exclusions
11. **Git Strategy** — branch, commit checkpoints, PR title/body
12. **Traceability** — PRD requirement IDs and DISCOVERY findings mapped to steps

---

## Header Schema

```markdown
---
spec_id: W1a
wave: 1.1
paired_prd: PRD.md
depends_on: []
touches:
  - path/one
  - path/two
status: PENDING
---

# SPEC-W1a — [Agent Name]

**Phase:** 1 — [Phase Name]
**Wave:** 1.1
**Spec ID:** W1a
**Depends on:** Nothing (or list of `W{N}{letter}` IDs)
```

The `touches` list in frontmatter MUST be a subset of the `Touches:` declared for this agent in `ROADMAP.md`. The validator may warn on divergence.

---

## Acceptance Criteria

One behavior per AC, in Given/When/Then format. Rules:

- No "and" joining two behaviors — split into separate ACs
- Each AC must be independently testable
- IDs use `AC-{spec_id}.{n}` (e.g., `AC-W1a.1`)

Examples:

**Good:**
> AC-W1a.1: Given a refund request with status=pending, when the repo's `MarkApproved` is called, then the row's status updates to `approved`.

**Bad — joined behaviors:**
> Given a refund request, when MarkApproved runs, then the row updates and an event is emitted.

Fix by splitting:
> AC-W1a.1: Given …, when MarkApproved runs, then the row updates.
> AC-W1a.2: Given the row updated, when the transaction commits, then a `RefundApproved` event is emitted.

---

## Files to Touch

Each entry on its own line. Use backticks for paths. Mark with `[NEW]`, `[MODIFY]`, or `[DELETE]`.

```markdown
- `internal/refund/repo.go` [MODIFY] — add `MarkApproved` method
- `internal/refund/repo_test.go` [NEW] — test coverage for new method
```

Each path here must appear in at least one Implementation Step.

---

## Ordered Implementation Steps

Each step is atomic (2-5 minutes for a focused agent). Format:

```markdown
### Step N.M (RED|GREEN|REFACTOR|non-behavioral) — [One-line summary]

**File:** `path/to/file`

**Action:** [What the agent writes/changes]

**Verification:** [Exact command — `go test ./internal/refund/...`, `python scripts/validate.py …`, or `manual: open …`]
```

RED-GREEN-REFACTOR rule:

- Behavioral steps (new feature, bug fix, behavior change) must follow RED → GREEN → REFACTOR
- Mark each step with one of: `RED`, `GREEN`, `REFACTOR`, or `non-behavioral`
- `non-behavioral` covers config, docs, generated code, scaffolding, and dependency updates

Every step must:
- Reference at least one file path
- Specify a verification action (test command, lint, build, or manual check)

---

## Structure (Optional)

Use when the SPEC's work splits into internal phases (e.g., `## P1 Foundations`, `## P2 Wiring`). For single-phase specs, omit the section and use a flat numbered step list.

---

## Risks & Assumptions

Bullet list. For each risk, state likelihood, impact, and mitigation.

```markdown
- **Risk:** Existing callers of `Repo.Update` may rely on side effects.
  **Likelihood:** Medium · **Impact:** High · **Mitigation:** Grep all call sites in Step 1.1, document behavior delta.
```

---

## Verification Plan

How the agent confirms the SPEC is fully delivered. Distinct from per-step verification.

```markdown
- `go test ./internal/refund/...` — all green
- `golangci-lint run ./internal/refund/...` — no new findings
- `go build ./...` — compiles
- Manual: send POST to `/refunds/{id}/approve`, observe DB row update
```

---

## Out of Scope

Explicit exclusions. Anchors against scope creep mid-implementation.

```markdown
- Refund webhook delivery (handled by W2b)
- UI button for approve action (W3a)
- Backfill of historical pending refunds
```

---

## Git Strategy

```markdown
**Branch:** `feat/refund-repo-approve`
**Commits:**
- `test(refund): RED for MarkApproved happy path`
- `feat(refund): GREEN MarkApproved implementation`
- `refactor(refund): extract row-update helper`
**PR Title:** `feat(refund): add MarkApproved to refund repo (W1a)`
**PR Body Outline:**
- Summary, Test Plan, Wave Context (links to ROADMAP wave 1.1)
```

---

## Traceability

A table mapping PRD requirement IDs and DISCOVERY findings to steps in this SPEC.

| Source | Step | Notes |
|--------|------|-------|
| FR-003 (PRD) | Step 1.1, 1.2 | core repo behavior |
| F4 (DISCOVERY) | Step 2.1 | event-emit hook |

---

## Authoring Heuristics

- Single-agent scope: a SPEC should be completable by one agent in one session (~30-90 min of focused work).
- If a SPEC exceeds ~30 ordered steps, consider splitting at a wave boundary (consult `wave-format` for collision rules).
- Prefer ≥1 RED step before any GREEN step in each behavioral slice.
- Code blocks longer than 15 lines are allowed in SPECs (SPECs are PLAN-grade); keep them representative, not exhaustive.

---

## Validation Threshold

`scripts/validate.py <spec> --type spec` enforces structural completeness, file-path specificity, per-step verification, traceability, and Git Strategy. PASS threshold: ≥85.
