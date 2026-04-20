# Skilmarillion

Spec-driven development from discovery through TDD to review.

```
/plugin marketplace add TrevorEdris/skilmarillion
/plugin install fellowship@skilmarillion
```

## The Seven Commands

| Command | Purpose | Model |
|---------|---------|-------|
| `/fellowship:init` | Bootstrap `.skilmarillion/projects/{slug}/` scaffolding | haiku |
| `/fellowship:plan` | PRD → roadmap → specs; `--arch`, `--migrate`, `--validate` | sonnet |
| `/fellowship:build` | Slice-by-slice TDD; `--debug` and `--refactor` modes | sonnet |
| `/fellowship:review` | Parallel code-quality / security / a11y; findings only | opus |
| `/fellowship:ship` | Conventional commit; `--pr` opens a PR | haiku |
| `/fellowship:status` | Read-only dashboard of active work | haiku |
| `/fellowship:help` | Context-aware tour; recommends a command from a task description | haiku |

## Artifacts

### Output Paths

All artifacts land under the target project's git root at `.skilmarillion/projects/{slug}/`:

```
{target}/.skilmarillion/projects/{slug}/
  PRD.md                                 # /fellowship:plan --prd
  ROADMAP.md                             # /fellowship:plan --roadmap (Phase → Wave → W{N}{letter})
  DISCOVERY.md                           # /fellowship:plan --roadmap (inline context-gatherer, roadmap scope)
  PROJECT-STATE.yaml                     # workflow state (current_wave, wave_agents_completed, …)
  specs/SPEC-W{N}{letter}-{slug}.md      # /fellowship:plan --specify (one per wave-agent)
  adrs/NNN-{slug}.md                     # /fellowship:plan --arch adr
  api/{name}-openapi.yaml                # /fellowship:plan --arch api
  schema/{name}-schema.sql               # /fellowship:plan --arch schema
  diagrams/{name}-{type}.md              # /fellowship:plan --arch diagram
  reviews/review-{target}.md             # /fellowship:review
```

There is no `plans/` directory — the SPEC absorbed the PLAN schema (ordered RED-GREEN-REFACTOR steps, files to touch, git strategy, traceability all live inside each SPEC).

### Git Exclusion

`.skilmarillion/` files are **never auto-staged or auto-committed**. The user decides whether to track them. `/fellowship:ship` ignores these paths unless explicitly asked.

### Model Tiering

Match model to task:
- **Haiku** — deterministic, structured output (commit formatting, dashboards, dedup, routing)
- **Sonnet** — judgment with codebase context (spec authoring, TDD loops, planning)
- **Opus** — safety-critical (security, accessibility, code quality)

### Validation Gate

PRDs and SPECs are scored 0–100 by `scripts/validate.py`. PASS threshold: ≥85 for all document types. Draft threshold: 50.

## Recommended .gitignore

### Strategy A — Ignore everything (simplest)

```gitignore
.skilmarillion/
```

### Strategy B — Track shared design, ignore working state (recommended for teams)

Commit the design artifacts the team agrees on. Keep per-engineer working state local.

```gitignore
.skilmarillion/projects/*/reviews/
.skilmarillion/projects/*/PROJECT-STATE.yaml
```

| Committed (shared) | Ignored (per-laptop) |
|--------------------|----------------------|
| `PRD.md`, `ROADMAP.md`, `DISCOVERY.md` | `PROJECT-STATE.yaml` (resume state, `current_wave`, `wave_agents_completed`) |
| `specs/SPEC-W{id}-*.md` | `reviews/review-*.md` (per-engineer findings) |
| `adrs/`, `api/`, `schema/`, `diagrams/` | |

Rationale: SPECs, ADRs, and API/schema contracts are the team's *durable agreement*. SPECs may accumulate `ACCEPT_WITH_DEBT` annotations during `/fellowship:build` — that's part of the shared record, so they stay committed. Reviews are findings-only and feed the PR's review thread, not the repo.

## Usage By Role

Who runs which command depends on your role. Full playbook: [HOW_TO_USE.md](HOW_TO_USE.md).

| Persona | Commands | Produces |
|---------|----------|----------|
| **Product Manager** | `/fellowship:plan --prd` | `PRD.md` (validated ≥85) |
| **Lead Engineer** | `/fellowship:plan --prd/--roadmap/--arch/--specify/--validate` | `DISCOVERY.md`, `ROADMAP.md` (Phase → Wave → `W{N}{letter}`), `specs/SPEC-W{id}-*.md` (each ≥85), ADRs, API, schema, diagrams |
| **Individual Engineer** | `/fellowship:build wave N` or `/fellowship:build spec W{id}` → `/fellowship:review` → `/fellowship:ship --pr` | code + tests (one SPEC per wave-agent), PR with AC traceability |

Handoff: PM writes the PRD → Lead decomposes into a wave-based roadmap and PLAN-grade SPECs → engineers pick a wave (parallel) or a single SPEC and ship it.

## License

MIT
