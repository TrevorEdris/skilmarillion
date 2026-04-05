# skilmarillion · fellowship

Spec-driven development from discovery through TDD to review — one Claude Code plugin, seven commands.

```
/plugin marketplace add TrevorEdris/skilmarillion
/plugin install fellowship@skilmarillion
```

## The Seven Commands

```
init  →  plan  →  build  →  review  →  ship
                                 status  |  help
```

| Command | Purpose | Model |
|---------|---------|-------|
| `/fellowship:init` | Bootstrap `.skilmarillion/projects/{slug}/` scaffolding | haiku |
| `/fellowship:plan` | PRD → roadmap → specs; `--arch`, `--migrate`, `--validate` | sonnet |
| `/fellowship:build` | Slice-by-slice TDD; `--debug` and `--refactor` modes | sonnet |
| `/fellowship:review` | Parallel code-quality / security / a11y; findings only | opus |
| `/fellowship:ship` | Conventional commit; `--pr` opens a PR | haiku |
| `/fellowship:status` | Read-only dashboard of active work | haiku |
| `/fellowship:help` | Context-aware tour; recommends a command from a task description | haiku |

## Phase Vocabulary (Internal Metaphor)

```
Palantír (Discover)  →  Council (Plan)  →  Journey (Build)  →  Rivendell (Review)
     scout                  spec               TDD                findings
```

Command names stay flat. The metaphor is for framing, not routing.

## Core Conventions

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

Specs, PRDs, and plans are scored 0–100 by `scripts/validate.py`. PASS threshold: ≥85 for PRDs/ROADMAPs/SPECs, ≥70 for plans. Draft threshold: 50.

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

## Workflow Examples

**Greenfield feature:**
```
/fellowship:plan "order cancellation with refund window"
  → PRD.md → ROADMAP.md → specs/SPEC-001-...md
/fellowship:build specs/SPEC-001-order-cancellation.md
  → plans/PLAN-001-order-cancellation.md → RED → GREEN → REFACTOR, slice by slice
/fellowship:review
  → findings sorted by impact-to-effort
/fellowship:ship --pr
  → conventional commit, PR opened with AC traceability
```

**Bug fix:**
```
/fellowship:build --debug "users can create orders without auth"
  → reproduce → isolate → root cause → fix proposal
/fellowship:ship
```

**Refactoring:**
```
/fellowship:build --refactor src/checkout/
  → baseline green → smell detection → plan → transform loop
/fellowship:review
/fellowship:ship
```

## Personas & Flows

Who runs which command depends on your role. Full playbook: [HOW_TO_USE.md](HOW_TO_USE.md).

| Persona | Commands | Produces |
|---------|----------|----------|
| **Product Manager** | `/fellowship:plan --prd` | `PRD.md` (validated ≥85) |
| **Lead Engineer** | `/fellowship:plan --prd/--roadmap/--arch/--specify/--validate` | `ROADMAP.md`, `specs/SPEC-NNN-*.md` (each ≥85), ADRs, API, schema, diagrams |
| **Individual Engineer** | `/fellowship:build` → `/fellowship:review` → `/fellowship:ship --pr` | `plans/PLAN-NNN-*.md` (paired with SPEC), code + tests, PR with AC traceability |

Handoff: PM writes the PRD → Lead decomposes into roadmap + specs → Engineer picks a spec and ships it.

## Repository Layout

```
.claude-plugin/
  plugin.json               # fellowship manifest
  marketplace.json          # skilmarillion marketplace → fellowship
commands/                   # 7 flat commands
  init.md  plan.md  build.md  review.md  ship.md  status.md  help.md
agents/                     # specialist sub-agents
skills/                     # reusable skills
references/                 # templates, rubrics, stage playbooks
  plan-stages/              # /fellowship:plan flag bodies
  build-stages/             # /fellowship:build flag bodies
  review-stages/            # /fellowship:review flag bodies
scripts/                    # validate.py, update-state.sh
hooks/                      # session lifecycle hooks
docs/planning/              # skilmarillion's own PRD + ROADMAP
test-fixtures/              # sample project for end-to-end testing
```

## License

MIT
