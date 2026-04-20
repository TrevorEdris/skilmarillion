---
description: Spec-driven planning. Runs PRD to ROADMAP to specs pipeline, or individual stages via flags.
argument-hint: "[--prd | --roadmap | --specify | --migrate | --validate | --arch <type>] [input]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh:*)"
  - "Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
model: sonnet
---

# /fellowship:plan

Spec-driven planning. Turns a feature description into a testable, TDD-ready spec (or ADR / API / schema / diagram). All artifacts land under `.skilmarillion/projects/{slug}/`.

> **Personality:** direct, brief, warm. "Let's spec this out." One question at a time. When the user says "just start coding," respond: "Got it — one quick question first: [single most important decision]."

---

## DISPATCH — Pick the Stage

Parse `$ARGUMENTS` for a leading flag:

| Flag | Stage file | Purpose |
|------|------------|---------|
| `--prd` | `references/plan-stages/prd.md` | Client-shareable Product Requirements Document |
| `--roadmap` | `references/plan-stages/roadmap.md` | Decompose an approved PRD into phased, wave-based decomposition (runs DISCOVERY + `wave-planner` inline) |
| `--specify` | `references/plan-stages/specify.md` | Generate one SPEC per wave-agent; wave-batched parallel authoring |
| `--migrate` | `references/plan-stages/migrate.md` | Prioritized migration plan from legacy → target |
| `--validate` | `references/plan-stages/validate.md` | Score a PRD or SPEC (0-100; PASS ≥85 for all types) |
| `--arch adr` | `references/plan-stages/arch-adr.md` | Architecture Decision Record + C4 diagram |
| `--arch api` | `references/plan-stages/arch-api.md` | OpenAPI 3.0 spec |
| `--arch schema` | `references/plan-stages/arch-schema.md` | Database schema DDL |
| `--arch diagram` | `references/plan-stages/arch-diagram.md` | Mermaid architecture diagrams |
| *(no flag)* | — | **Default guided pipeline:** PRD → ROADMAP → specs, end to end |

**How to run a stage:**
1. `Read` the corresponding stage file from `${CLAUDE_PLUGIN_ROOT}/references/plan-stages/{stage}.md`.
2. Follow its instructions exactly. Stage files are self-contained playbooks.
3. Pass through the remaining `$ARGUMENTS` (after the flag) as the stage input.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

---

## DEFAULT FLOW — Guided PRD → ROADMAP → Specs

If no flag is given, walk the user through the full pipeline:

### 1. Greeting & Intent Capture

If `$ARGUMENTS` contains a feature description, use it. Otherwise ask:

> "What are we specifying today? One sentence is plenty."

### 2. Confirm Slug

Load `${CLAUDE_PLUGIN_ROOT}/skills/artifact-paths.md` and propose a project slug. Confirm with the user before first save.

### 3. Stage 1 — PRD

Run the PRD stage (`references/plan-stages/prd.md`) with the feature description. Save to `.skilmarillion/projects/{slug}/PRD.md`.

At the end of this stage: **checkpoint**. Run `python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py .skilmarillion/projects/{slug}/PRD.md --type prd`. If score < 85, iterate until PASS. Then ask:

> "PRD scored {N}/100. Ready to decompose into a roadmap, or pause here?"

If the user pauses, stop. Resume later via `/fellowship:plan --roadmap .skilmarillion/projects/{slug}/PRD.md`.

### 4. Stage 2 — ROADMAP (runs DISCOVERY + wave-planner inline)

Run the roadmap stage (`references/plan-stages/roadmap.md`) against the PRD. Save ROADMAP.md + DISCOVERY.md to `.skilmarillion/projects/{slug}/`. Validate (≥85). Checkpoint:

> "Roadmap scored {N}/100. {P} phases, {W} waves, {A} wave-agents, {C} collisions resolved. Generate SPECs for all wave-agents, or stop here?"

### 5. Stage 3 — SPECs (one per wave-agent, wave-batched)

Run the specify stage (`references/plan-stages/specify.md`) against the ROADMAP. For each wave (in order), spawn parallel spec-builder → architecture-advisor → tdd-planner chains per wave-agent. Save each to `.skilmarillion/projects/{slug}/specs/SPEC-W{N}{letter}-{slug}.md`. Validate each. Summarize:

> "SPECs generated: {N} total across {W} waves, {M} PASS, {K} below threshold. Next: `/fellowship:build wave 1` (all Wave 1.* agents in parallel) or `/fellowship:build spec W1a` (single wave-agent)."

### 6. State Tracking

After each stage, update `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` via `${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh`. Write `slug`, `feature`, `size`, `risk`, `current_phase`, `current_wave`, `spec_path` (if present).

---

## VALIDATION GATE

Every artifact produced by this command must be scored by `scripts/validate.py` before being presented as finished.

- **PASS threshold:** score ≥ 85
- **Draft threshold:** score ≥ 50 (`--draft` flag)
- Never present an artifact below threshold as complete. Iterate until PASS, or tell the user explicitly that it's a draft.

---

## OUTPUT CONVENTIONS

All artifacts land under the **target project's** git root:

```
{target}/.skilmarillion/projects/{slug}/
  PRD.md
  ROADMAP.md
  DISCOVERY.md
  PROJECT-STATE.yaml
  specs/SPEC-W{N}{letter}-{slug}.md
  adrs/NNN-{slug}.md
  api/{name}-openapi.yaml
  schema/{name}-schema.sql
  diagrams/{name}-{type}.md
```

There is no `plans/` directory. The SPEC absorbed the PLAN schema — see `skills/spec-format`.

`.skilmarillion/` files are **never auto-staged or auto-committed.** The user decides whether to track them.

---

## WHAT NOT TO DO

- Do NOT skip the stage file. `plan.md` is a dispatcher; the stage files hold the actual playbooks.
- Do NOT write production code. This command produces specs, not implementations.
- Do NOT present any artifact that scores below 85 as finished.
- Do NOT auto-run the next stage without user confirmation at each checkpoint.
- Do NOT commit `.skilmarillion/` files automatically.
