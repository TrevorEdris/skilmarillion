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
  PRD.md                       # /fellowship:plan --prd
  ROADMAP.md                   # /fellowship:plan --roadmap
  PROJECT-STATE.yaml           # workflow state (plan | impl | review sections)
  specs/SPEC-NNN-{slug}.md     # /fellowship:plan --specify
  adrs/NNN-{slug}.md           # /fellowship:plan --arch adr
  api/{name}-openapi.yaml      # /fellowship:plan --arch api
  schema/{name}-schema.sql     # /fellowship:plan --arch schema
  diagrams/{name}-{type}.md    # /fellowship:plan --arch diagram
  plans/PLAN-NNN-{slug}.md     # /fellowship:build (paired with SPEC-NNN)
  reviews/review-{target}.md   # /fellowship:review
```

### Git Exclusion

`.skilmarillion/` files are **never auto-staged or auto-committed**. The user decides whether to track them. `/fellowship:ship` ignores these paths unless explicitly asked.

### Model Tiering

Match model to task:
- **Haiku** — deterministic, structured output (commit formatting, dashboards, dedup, routing)
- **Sonnet** — judgment with codebase context (spec authoring, TDD loops, planning)
- **Opus** — safety-critical (security, accessibility, code quality)

### Validation Gate

Specs, PRDs, and plans are scored 0–100 by `scripts/validate.py`. PASS threshold: ≥85 for all document types. Draft threshold: 50.

## Recommended .gitignore

### Strategy A — Ignore everything (simplest)

```gitignore
.skilmarillion/
```

### Strategy B — Track shared design, ignore working state (recommended for teams)

Commit the design artifacts the team agrees on. Keep per-engineer working state local.

```gitignore
.skilmarillion/projects/*/plans/
.skilmarillion/projects/*/reviews/
.skilmarillion/projects/*/PROJECT-STATE.yaml
```

| Committed (shared) | Ignored (per-laptop) |
|--------------------|----------------------|
| `PRD.md`, `ROADMAP.md` | `PROJECT-STATE.yaml` (resume state) |
| `specs/SPEC-NNN-*.md` | `plans/PLAN-NNN-*.md` (how *you* will implement it) |
| `adrs/`, `api/`, `schema/`, `diagrams/` | `reviews/review-*.md` (per-engineer findings) |

Rationale: specs, ADRs, and API/schema contracts are the team's *durable agreement*. Plans get actively rewritten during `/fellowship:build` (debt notes, slice status, attempt counts) — they're the working document for whoever picks up the spec. Reviews are findings-only and feed the PR's review thread, not the repo.

## Usage By Role

Who runs which command depends on your role. Full playbook: [HOW_TO_USE.md](HOW_TO_USE.md).

| Persona | Commands | Produces |
|---------|----------|----------|
| **Product Manager** | `/fellowship:plan --prd` | `PRD.md` (validated ≥85) |
| **Lead Engineer** | `/fellowship:plan --prd/--roadmap/--arch/--specify/--validate` | `ROADMAP.md`, `specs/SPEC-NNN-*.md` (each ≥85), ADRs, API, schema, diagrams |
| **Individual Engineer** | `/fellowship:build` → `/fellowship:review` → `/fellowship:ship --pr` | `plans/PLAN-NNN-*.md` (paired with SPEC), code + tests, PR with AC traceability |

Handoff: PM writes the PRD → Lead decomposes into roadmap + specs → Engineer picks a spec and ships it.

## License

MIT
