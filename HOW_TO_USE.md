# How To Use Fellowship — Persona Playbooks

Three role-specific command flows. Each persona exercises a different slice of the seven commands.

```
init → plan → build → review → ship
                          status | help
```

All artifacts land under `{target_project}/.skilmarillion/projects/{slug}/`. Validation gate: score ≥85 PASS for PRDs, ROADMAPs, and SPECs.

**Team convention (recommended gitignore):** commit the shared design (PRD, ROADMAP, specs, ADRs, API, schema, diagrams). Ignore per-engineer working state (`plans/`, `reviews/`, `PROJECT-STATE.yaml`). This means PM → Lead → Engineer handoffs flow through git, while each engineer's PLAN, review findings, and resume state stay on their laptop. See README.md § "Strategy B" for the exact gitignore lines.

---

## Persona 1 — Product Manager (PRD only)

**Goal:** Capture feature intent as a validated PRD that engineering can decompose.

**Scope:** One command, one artifact.

### Command Flow

```
/fellowship:init "order-cancellation"               # (optional) scaffolding
/fellowship:plan --prd "order cancellation with refund window"
```

### Expected Outputs

| File | Purpose |
|------|---------|
| `.skilmarillion/projects/order-cancellation/PRD.md` | Problem, users, success metrics, scope, out-of-scope, risks, open questions |
| `.skilmarillion/projects/order-cancellation/PROJECT-STATE.yaml` | Initial state with slug + created date |

### What The PM Does

1. **Kick off** — run `/fellowship:plan --prd "[feature in one sentence]"`.
2. **Answer interview questions** — the command walks through discovery one question at a time (problem, users, success criteria, scope boundaries, constraints).
3. **Review the draft** — the plugin presents the PRD inline before saving. PM edits any section that's wrong.
4. **Confirm save path** — PM approves or overrides the suggested `{slug}`.
5. **Commit and push** — `git add .skilmarillion/projects/{slug}/PRD.md && git commit -m "docs: add PRD for {slug}"` and push so engineering can access it directly.

### Verification

| Check | How |
|-------|-----|
| Validation score ≥85 | `python scripts/validate.py .skilmarillion/projects/{slug}/PRD.md --type prd --verbose` |
| All required sections present | Validator reports section-by-section scoring |
| PM reads and approves | Human review — PRD reflects the actual intent |
| Out-of-scope is explicit | PRD contains a dedicated "Out of Scope" section with items listed |

If score <85: the command surfaces findings and re-drafts until passing. PM does not need to run the validator manually — the command enforces it.

### What The PM Does NOT Do

- Does NOT run `--roadmap` or `--specify` — those are engineering decomposition tasks.
- Does NOT invoke `/fellowship:build`, `/fellowship:review`, or `/fellowship:ship`.

### Handoff

PM pushes the PRD commit, then signals the lead: "PRD is in `main` under `.skilmarillion/projects/{slug}/PRD.md` — please decompose."

---

## Persona 2 — Lead Engineer (PRD collaboration → ROADMAP → SPECS)

**Goal:** Turn the PM's PRD into a phased roadmap and a set of executable specs engineers can pick up.

**Scope:** Plan command, multiple flags, multi-step.

### Command Flow

```
# Phase 1 — refine PRD (if needed)
/fellowship:plan --prd                               # reopens interview if PRD exists
/fellowship:plan --validate .skilmarillion/projects/{slug}/PRD.md

# Phase 2 — decompose into phased milestones
/fellowship:plan --roadmap

# Phase 3 — architecture artifacts for risky milestones (optional, per-milestone)
/fellowship:plan --arch adr "use-saga-for-refund-orchestration"
/fellowship:plan --arch schema "order_cancellations"
/fellowship:plan --arch api "refund-service"
/fellowship:plan --arch diagram "cancellation-sequence"

# Phase 4 — generate one spec per roadmap milestone, in parallel
/fellowship:plan --specify
```

### Expected Outputs

| File | Purpose |
|------|---------|
| `PRD.md` (refined) | Validated ≥85 after any lead-engineer edits |
| `ROADMAP.md` | Phased milestones (P0-A, P0-B, P1-A...) with dependencies, risk, checklist, Spec Index |
| `adrs/NNN-{slug}.md` | Architecture decision records for contested choices |
| `schema/{name}-schema.sql` + `schema/{name}-migration.md` | DDL + expand-contract migration plan |
| `api/{name}-openapi.yaml` | API contract |
| `diagrams/{name}-{type}.md` | Mermaid sequence/state/component diagrams |
| `specs/SPEC-001-{slug}.md` ... `SPEC-NNN-{slug}.md` | One spec per milestone, each scored ≥85 |

### What The Lead Does

1. **Review PRD** from PM. If gaps exist, re-run `--prd` to refine (the command preserves existing content and re-enters the interview).
2. **Run `--roadmap`** — walks through phase boundaries, milestone decomposition, dependency mapping, risk labeling. Produces a single `ROADMAP.md` with a Spec Index table.
3. **Identify architecture-heavy milestones.** For each risky area, run the appropriate `--arch` flag:
   - `adr` — contested decisions (framework choice, pattern selection, tradeoff resolution)
   - `schema` — new tables, migrations, data model changes
   - `api` — new endpoints, contract-first design
   - `diagram` — complex flows worth visualizing
4. **Run `--specify`** — reads ROADMAP, extracts milestones, launches parallel spec generation (context-gatherer → spec-builder → architecture-advisor → tdd-planner). Dependency-aware batching: milestones with no unmet deps run in parallel; dependent ones wait.
5. **Review specs** — the command presents a table of generated specs with validation scores. Lead reads each, requests re-drafts for weak ones.
6. **Commit and push** — `git add .skilmarillion/projects/{slug}/` and commit all design artifacts (ROADMAP, specs, ADRs, API, schema, diagrams) so engineers can pull and reference them directly.

### Verification

| Check | How |
|-------|-----|
| ROADMAP has parseable milestones | `### P0-A:` heading + `**What:**` + `**Checklist:**` per milestone |
| Spec Index table populated | Every milestone has a row mapping to a SPEC-NNN filename |
| Every spec scored ≥85 | `/fellowship:plan --specify` enforces this before saving |
| Dependencies form a DAG | ROADMAP's dependency graph is acyclic; lead eyeballs the table |
| SPEC numbering is sequential | `ls specs/` shows SPEC-001, SPEC-002, ... no gaps |
| Slug matches milestone name | `SPEC-003-order-refund.md` pairs with milestone `P0-C: Order Refund` |

### What The Lead Does NOT Do

- Does NOT write PLANs — the individual engineer owns implementation-level decomposition.
- Does NOT invoke `/fellowship:build`, `/fellowship:review`, or `/fellowship:ship` for feature work — those belong to the implementing engineer.

### Handoff

Lead pushes the design artifacts commit, then signals the team: "ROADMAP and specs are in `main` under `.skilmarillion/projects/{slug}/`. P0-A through P0-C are unblocked — pull and run `/fellowship:build specs/SPEC-NNN-{slug}.md`."

---

## Persona 3 — Individual Engineer (PLAN → implement → review → ship)

**Goal:** Take one SPEC, build it test-first, review it, ship it.

**Scope:** Build → review → ship pipeline, scoped to a single spec.

### Command Flow

```
# Pick a spec (from the Spec Index in ROADMAP.md)
/fellowship:build .skilmarillion/projects/{slug}/specs/SPEC-003-order-refund.md

# Check progress anytime
/fellowship:status

# Review the implementation
/fellowship:review

# Commit + open PR
/fellowship:ship --pr
```

### Expected Outputs

| File | Purpose |
|------|---------|
| `plans/PLAN-003-order-refund.md` | Translation of SPEC into executable slices, paired 1:1 with the spec |
| Production code + tests | Actual feature, RED → GREEN → REFACTOR per slice |
| `reviews/review-SPEC-003.md` | Findings from code-quality + security + a11y specialists, deduped |
| Git commit (conventional format) | `feat(order): add refund workflow per SPEC-003` |
| PR (if `--pr`) | With AC traceability table linking each acceptance criterion to code |

### What The Engineer Does

1. **Pick a SPEC** — from the Spec Index in `ROADMAP.md`, grab one with no unmet dependencies.
2. **Run `/fellowship:build`** against the spec path. The command:
   - Delegates to `spec-to-impl` agent to translate SPEC → `plans/PLAN-NNN-{slug}.md` (paired 1:1 with the spec by number and slug)
   - Presents the plan — engineer reviews slice boundaries before execution
   - Runs each slice RED → GREEN → REFACTOR
   - Stops after 3 failed attempts on any slice → diagnostic → modified approach, sub-slice split, or `ACCEPT_WITH_DEBT` annotation in the plan
3. **Check `/fellowship:status`** to see which slice is active, which are done, which are blocked.
4. **Run `/fellowship:review`** — spawns code-quality, security, and accessibility reviewers in parallel. Findings-only, never modifies code. Engineer decides what to fix, loops back to `/fellowship:build` as needed.
5. **Run `/fellowship:ship --pr`** — stages only source/test files (`.skilmarillion/` excluded), crafts a conventional commit, pushes, opens a PR with AC traceability.

### Verification

| Check | How |
|-------|-----|
| Every acceptance criterion has a failing test first | TDD discipline enforced by `/fellowship:build` — RED before GREEN |
| All slices reach GREEN | `/fellowship:status` shows all slices marked complete |
| PLAN pairs 1:1 with SPEC | `plans/PLAN-003-order-refund.md` matches `specs/SPEC-003-order-refund.md` |
| No high-severity findings | `/fellowship:review` output; security findings >80% confidence threshold |
| Tests pass locally | Engineer runs project's test suite (pytest/vitest/etc.) |
| Conventional commit format | `/fellowship:ship` generates it; engineer verifies scope + breaking flag |
| PR template filled out | `/fellowship:ship --pr` detects `.github/PULL_REQUEST_TEMPLATE.md` and populates it |
| AC traceability in PR | PR body links each spec AC to its implementing commit/file |

### Variants

**Bug fix (no spec):**
```
/fellowship:build --debug "users can create orders without auth"
  → reproduce → isolate → root cause → proposed fix
/fellowship:ship
```

**Refactor (baseline must be green):**
```
/fellowship:build --refactor src/checkout/
  → baseline green check → smell detection → plan → transform loop
/fellowship:review
/fellowship:ship
```

### What The Engineer Does NOT Do

- Does NOT skip RED — no production code before a failing test (config/docs/generated code exempt).
- Does NOT bypass review findings — high-severity items block ship; engineer fixes or documents why they're accepted.
- Does NOT auto-commit `.skilmarillion/` files — git exclusion is enforced by `/fellowship:ship`.

---

## Cross-Persona Handoff Map

```
PM                      Lead Engineer              Individual Engineer
──                      ─────────────              ──────────────────
/fellowship:plan --prd
  └─► PRD.md ─────────► /fellowship:plan --prd (refine)
                          /fellowship:plan --roadmap
                            └─► ROADMAP.md
                          /fellowship:plan --arch (per risky milestone)
                            └─► adrs/ api/ schema/ diagrams/
                          /fellowship:plan --specify
                            └─► specs/SPEC-NNN-{slug}.md ────► /fellowship:build specs/SPEC-NNN...
                                                                 └─► plans/PLAN-NNN-{slug}.md
                                                                 └─► code + tests
                                                               /fellowship:review
                                                                 └─► reviews/review-*.md
                                                               /fellowship:ship --pr
                                                                 └─► commit + PR
```

---

## Which Model Runs Each Step

| Command | Model | Why |
|---------|-------|-----|
| `/fellowship:init` | haiku | Deterministic scaffolding |
| `/fellowship:plan` | sonnet | Judgment, codebase context, design reasoning |
| `/fellowship:build` | sonnet | TDD loops, spec interpretation |
| `/fellowship:review` | opus | Safety-critical, high-confidence findings |
| `/fellowship:ship` | haiku | Structured commit/PR formatting |
| `/fellowship:status` | haiku | Read-only dashboard |
| `/fellowship:help` | haiku | Routing and tour |

Match your persona to the models you'll invoke: PM hits haiku + sonnet; lead hits sonnet heavily; individual engineer hits all three (sonnet for build, opus for review, haiku for ship/status).

---

## Exit Criteria Per Persona

| Persona | Done When |
|---------|-----------|
| PM | `PRD.md` exists, scores ≥85, PM approves content |
| Lead | `ROADMAP.md` + all `specs/SPEC-NNN-*.md` exist, each scored ≥85, Spec Index populated, dependencies are a DAG |
| Engineer | All slices GREEN, no high-severity review findings, PR open with AC traceability |
