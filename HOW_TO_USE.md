# How To Use Fellowship — Persona Playbooks

Three role-specific command flows. Each persona exercises a different slice of the seven commands.

```
init → plan → build → review → ship
                          status | help
```

All artifacts land under `{target_project}/.skilmarillion/projects/{slug}/`. Validation gate: score ≥85 PASS for PRDs and SPECs. There is no separate PLAN artifact — the SPEC IS the plan.

**Team convention (recommended gitignore):** commit the shared design (PRD, ROADMAP, DISCOVERY, SPECs, ADRs, API, schema, diagrams). Ignore per-engineer working state (`reviews/`, `PROJECT-STATE.yaml`). PM → Lead → Engineer handoffs flow through git; each engineer's review findings and resume state stay on their laptop. See README.md § "Strategy B" for the exact gitignore lines.

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

**Goal:** Turn the PM's PRD into a wave-based roadmap and a PLAN-grade SPEC per wave-agent.

**Scope:** Plan command, multiple flags, multi-step.

### Command Flow

```
# Phase 1 — refine PRD (if needed)
/fellowship:plan --prd                               # reopens interview if PRD exists
/fellowship:plan --validate .skilmarillion/projects/{slug}/PRD.md

# Phase 2 — decompose into phased waves (runs DISCOVERY + wave-planner inline)
/fellowship:plan --roadmap

# Phase 3 — architecture artifacts for risky areas (optional)
/fellowship:plan --arch adr "use-saga-for-refund-orchestration"
/fellowship:plan --arch schema "order_cancellations"
/fellowship:plan --arch api "refund-service"
/fellowship:plan --arch diagram "cancellation-sequence"

# Phase 4 — generate one SPEC per wave-agent (wave-batched parallel)
/fellowship:plan --specify
```

### Expected Outputs

| File | Purpose |
|------|---------|
| `PRD.md` (refined) | Validated ≥85 after any lead-engineer edits |
| `DISCOVERY.md` | Entry points, layout, conventions, hotspots — written by `context-gatherer` at roadmap scope |
| `ROADMAP.md` | Phase → Wave → `W{N}{letter}` wave-agent tree with Scope/Touches/Depends on/Acceptance/Spec bullets, Independence Check, Spec Index |
| `adrs/NNN-{slug}.md` | Architecture decision records for contested choices |
| `schema/{name}-schema.sql` + `schema/{name}-migration.md` | DDL + expand-contract migration plan |
| `api/{name}-openapi.yaml` | API contract |
| `diagrams/{name}-{type}.md` | Mermaid sequence/state/component diagrams |
| `specs/SPEC-W1a-{slug}.md`, `SPEC-W1b-{slug}.md`, `SPEC-W2a-{slug}.md`... | One PLAN-grade SPEC per wave-agent, each scored ≥85 |

### What The Lead Does

1. **Review PRD** from PM. If gaps exist, re-run `--prd` to refine (the command preserves existing content and re-enters the interview).
2. **Run `--roadmap`** — the stage runs DISCOVERY inline (`context-gatherer` at roadmap scope) and delegates wave decomposition to `wave-planner`. Produces `DISCOVERY.md` + `ROADMAP.md` with Phase/Wave/`W{N}{letter}` leaves. Wave-agents within a wave have disjoint `Touches:` — the planner guarantees this via the collision algorithm.
3. **Identify architecture-heavy areas.** For each risky area, run the appropriate `--arch` flag:
   - `adr` — contested decisions (framework choice, pattern selection, tradeoff resolution)
   - `schema` — new tables, migrations, data model changes
   - `api` — new endpoints, contract-first design
   - `diagram` — complex flows worth visualizing
4. **Run `--specify`** — reads ROADMAP, extracts wave-agents, re-runs the collision check, then wave-batches parallel `spec-builder` → `architecture-advisor` → `tdd-planner` chains. Within a wave: all agents parallel. Across waves: hard sync barrier.
5. **Review SPECs** — the command presents a table of generated SPECs with validation scores. Lead reads each, requests re-drafts for weak ones. Each SPEC is a full implementation plan (ordered RED-GREEN-REFACTOR steps, files to touch, git strategy, traceability).
6. **Commit and push** — `git add .skilmarillion/projects/{slug}/` and commit all design artifacts (DISCOVERY, ROADMAP, SPECs, ADRs, API, schema, diagrams) so engineers can pull and reference them directly.

### Verification

| Check | How |
|-------|-----|
| ROADMAP has parseable wave-agents | `#### W{N}{letter}:` heading + `**Scope:**` + `**Touches:**` + `**Depends on:**` + `**Acceptance:**` + `**Spec:**` per wave-agent |
| Independence Check is green | Every wave's row in the Independence Check table reports `None` — no touches-collision within a wave |
| Spec Index table populated | Every wave-agent has a row mapping to a `SPEC-W{N}{letter}` filename |
| Every SPEC scored ≥85 | `/fellowship:plan --specify` enforces this before saving |
| Dependencies form a DAG | Every `depends_on` points to a wave-agent in an earlier wave (same phase) or any earlier phase |
| SPEC IDs match ROADMAP | `ls specs/` returns one `SPEC-W{id}-{slug}.md` per wave-agent |
| SPEC `touches` ⊆ ROADMAP `Touches:` | Validator warns on divergence |

### What The Lead Does NOT Do

- Does NOT generate a separate PLAN file — the SPEC is the plan.
- Does NOT invoke `/fellowship:build`, `/fellowship:review`, or `/fellowship:ship` for feature work — those belong to the implementing engineer(s).

### Handoff

Lead pushes the design artifacts commit, then signals the team: "ROADMAP and SPECs are in `main` under `.skilmarillion/projects/{slug}/`. Wave 1.1 is unblocked — pull and run `/fellowship:build wave 1` to start all W1* agents in parallel."

---

## Persona 3 — Individual Engineer (build → review → ship a wave-agent)

**Goal:** Take one SPEC (one wave-agent), build it test-first, review it, ship it. Or take a whole wave and coordinate parallel runs.

**Scope:** Build → review → ship pipeline, scoped to a single wave-agent or a full wave.

### Command Flow

```
# Pick a wave-agent from the ROADMAP's Spec Index
/fellowship:build spec W1a                          # single wave-agent

# Or run an entire wave in parallel (all W1* agents at once)
/fellowship:build wave 1

# Or use Agent Teams instead of Task subagents for the wave
/fellowship:build wave 1 --team

# Check progress anytime
/fellowship:status

# Review the implementation
/fellowship:review

# Commit + open PR (one per wave-agent PR-per-branch)
/fellowship:ship --pr
```

### Expected Outputs

| File | Purpose |
|------|---------|
| Production code + tests | Actual feature, RED → GREEN → REFACTOR per ordered step in the SPEC |
| `reviews/review-SPEC-W1a.md` | Findings from code-quality + security + a11y specialists, deduped |
| Git commit (conventional format) | `feat(order): refund repo per SPEC-W1a` |
| PR (if `--pr`) | With AC traceability table linking each `AC-W1a.N` to code |

### What The Engineer Does

1. **Pick a wave-agent** — from the Spec Index in `ROADMAP.md`, grab a `W{id}` whose `Depends on:` is satisfied.
2. **Run `/fellowship:build`** in one of three forms:
   - `spec W{N}{letter}` — single wave-agent. TDD loop walks the SPEC's `## Ordered Implementation Steps` with the explicit `RED|GREEN|REFACTOR|non-behavioral` markers. No SPEC-to-PLAN translation; the SPEC is the plan.
   - `wave N` — spawns one Task per wave-agent in Wave N.M concurrently. The wave merge barrier blocks until every spawned run reports green.
   - `wave N --team` — same as above but spawns Agent Teams so long-running wave-agents can coordinate via shared tasks and SendMessage (see `teams/rules/team-conventions.md`).

   In all forms, the build stage stops after 3 failed attempts on any step → diagnostic → modified approach, sub-step split, or `ACCEPT_WITH_DEBT` annotation appended to the SPEC.
3. **Check `/fellowship:status`** to see which wave-agent is active, which are complete, which are blocked.
4. **Run `/fellowship:review`** — spawns code-quality, security, and accessibility reviewers in parallel. Findings-only, never modifies code. Engineer decides what to fix, loops back to `/fellowship:build` as needed.
5. **Run `/fellowship:ship --pr`** — stages only source/test files (`.skilmarillion/` excluded), crafts a conventional commit, pushes, opens a PR with AC traceability.

### Verification

| Check | How |
|-------|-----|
| Every acceptance criterion has a failing test first | TDD discipline enforced by `/fellowship:build` — RED before GREEN |
| All steps reach GREEN | `/fellowship:status` shows all steps marked complete for the wave-agent |
| No high-severity findings | `/fellowship:review` output; security findings >80% confidence threshold |
| Tests pass locally | Engineer runs project's test suite (pytest/vitest/etc.) |
| Conventional commit format | `/fellowship:ship` generates it; engineer verifies scope + breaking flag |
| PR template filled out | `/fellowship:ship --pr` detects `.github/PULL_REQUEST_TEMPLATE.md` and populates it |
| AC traceability in PR | PR body links each `AC-W{id}.N` to its implementing commit/file |
| Wave merge barrier | When running `wave N`, no wave-agent advances to the next wave until every sibling is green |

### Variants

**Bug fix (no SPEC):**
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
- Does NOT touch files outside their SPEC's `touches` list — this guarantee is what makes wave parallelism safe.
- Does NOT bypass review findings — high-severity items block ship; engineer fixes or documents why they're accepted.
- Does NOT auto-commit `.skilmarillion/` files — git exclusion is enforced by `/fellowship:ship`.

---

## Cross-Persona Handoff Map

```
PM                      Lead Engineer              Individual Engineer(s)
──                      ─────────────              ──────────────────────
/fellowship:plan --prd
  └─► PRD.md ─────────► /fellowship:plan --prd (refine)
                          /fellowship:plan --roadmap
                            └─► DISCOVERY.md (context-gatherer, roadmap scope)
                            └─► ROADMAP.md  (Phase → Wave → W{N}{letter})
                          /fellowship:plan --arch (per risky area)
                            └─► adrs/ api/ schema/ diagrams/
                          /fellowship:plan --specify  (wave-batched parallel)
                            └─► specs/SPEC-W1a-{slug}.md ──┐
                            └─► specs/SPEC-W1b-{slug}.md ──┤── /fellowship:build wave 1
                            └─► specs/SPEC-W2a-{slug}.md ──┘     ├─► W1a: code + tests
                                                                 ├─► W1b: code + tests
                                                                 └─► (merge barrier)
                                                                  /fellowship:build wave 2
                                                                   └─► W2a: code + tests
                                                                 /fellowship:review
                                                                   └─► reviews/review-SPEC-W*.md
                                                                 /fellowship:ship --pr (one per wave-agent)
                                                                   └─► commit + PR
```

---

## Which Model Runs Each Step

| Command | Model | Why |
|---------|-------|-----|
| `/fellowship:init` | haiku | Deterministic scaffolding |
| `/fellowship:plan` | sonnet | Judgment, codebase context, design reasoning |
| `/fellowship:build` | sonnet | TDD loops, SPEC interpretation, wave dispatch |
| `/fellowship:review` | opus | Safety-critical, high-confidence findings |
| `/fellowship:ship` | haiku | Structured commit/PR formatting |
| `/fellowship:status` | haiku | Read-only dashboard |
| `/fellowship:help` | haiku | Routing and tour |

Match your persona to the models you'll invoke: PM hits haiku + sonnet; lead hits sonnet heavily (plus opus indirectly via `wave-planner` / `architecture-advisor`); individual engineer hits all three.

---

## Exit Criteria Per Persona

| Persona | Done When |
|---------|-----------|
| PM | `PRD.md` exists, scores ≥85, PM approves content |
| Lead | `DISCOVERY.md` + `ROADMAP.md` + all `specs/SPEC-W{id}-*.md` exist, each SPEC scored ≥85, Spec Index populated, Independence Check all green, `collisions_unresolved` empty |
| Engineer | All SPEC steps GREEN for their wave-agent, wave merge barrier met (all siblings green), no high-severity review findings, PR open with AC traceability |
