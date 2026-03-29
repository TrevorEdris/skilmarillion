# Skilmarillion — Roadmap

## Current Status

**Phase:** 0 — In Progress
**Last Updated:** 2026-03-29

### Completed
- [x] PLAN-001: Plugin Scaffold (P0-A) — merged PR #1
- [x] PLAN-002: Task Triage Engine (P0-B) — merged PR #2
- [x] PLAN-003: SDD Core Planning Workflow (P0-C) — merged PR #3
- [x] PLAN-004: Validate Command (P0-E) — merged PR #5
- [x] PLAN-005: PRD Command (P0-D) — merged PR #TBD
- [x] PLAN-006: Session Documentation Hooks (P0-F) — merged PR #TBD
- [x] PLAN-007: Deterministic Artifact Paths (P0-G) — merged PR #TBD

### In Progress
(none)

### Not Started
- [ ] PLAN-009: Roadmap Command (P0-I)
- [ ] PLAN-008: Migrate Command (P0-H) — Should priority
- [ ] PLAN-010: Help Command (P0-J) — FR-011
- [ ] PLAN-011: Out-of-Order Guards (P0-K) — FR-012
- [ ] PLAN-012: QRSPI Mode for SMALL Tasks (P0-C extension) — FR-001, FR-005
- [ ] Phase 0.5: `skil` — Workflow Router
- [ ] Phase 1: `impl` — Implementation
- [ ] Phase 2: `arch` — Architecture & Design
- [ ] Phase 3: `review` — Review & Quality
- [ ] Phase 4: Homepage — GitHub Pages

---

## Philosophy

Build the lifecycle vertically, one plugin at a time, with each phase delivering something independently useful before the next begins. Plugin names are functional — `plan`, `arch`, `impl`, `review` — so a user can type what they mean without a decode step. The `skil` meta-plugin provides guided discovery and cross-plugin routing so new users never hit a dead end.

**Model tiering principle:** Use the minimum model that can handle the task reliably. Haiku for deterministic, tool-free, or structured-output tasks (commit formatting, review deduplication). Sonnet for tasks requiring judgment, codebase context, or design reasoning. Opus for roles where a missed finding has real consequences — security vulnerabilities, accessibility barriers, and code quality issues that could reach production. Never assign a heavier model to a role that doesn't need it — cost compounds across multi-agent workflows.

**Tool access principle:** Agents that only produce findings or aggregate structured inputs must be read-only or tool-free. No agent should have WRITE or EDIT access unless it is explicitly producing code or files. Constrained tool sets prevent context bloat and enforce role boundaries.

---

## Phase 0: `plan` — Spec-Driven Planning

**Entry Criteria:** Repository scaffolded; `incubyte/claude-plugins` reference architecture reviewed; fotw source skills identified.
**Exit Criteria:** A user can run `/plan:sdd` with a plain-language task description and receive a spec with testable acceptance criteria, an architecture recommendation, and a TDD plan — without reading documentation first. Trivial tasks short-circuit in one round-trip. All artifacts land at deterministic paths. `/plan:help` provides an interactive tour. Cross-plugin references include install hints for `impl`.

### P0-A: Plugin Scaffold

- **What:** Establish the `plan` plugin directory structure — manifest, commands, agents, skills, CLAUDE.md, and README — following the `incubyte/claude-plugins` reference architecture.
- **Depends on:** Nothing
- **Risk:** `plugin.json` manifest format may evolve; pin to a known-good Claude Code version.
- **Checklist:**
  - [x] Create `.claude-plugin/` directory with `plugin.json` manifest (name, version, description, commands)
  - [x] Scaffold `commands/`, `agents/`, `skills/`, `references/` directories
  - [x] Write `CLAUDE.md` for the `plan` plugin context
  - [x] Write `README.md` with standalone entry conditions and command reference
  - [x] Verify `claude plugin add` loads the plugin without errors

### P0-B: Task Triage Engine

- **What:** When a user describes a task, `plan` automatically classifies it as TRIVIAL, SMALL, FEATURE, or EPIC and routes accordingly — trivial tasks get a one-round-trip confirmation; feature-scale tasks get the full spec workflow.
- **Depends on:** P0-A
- **Risk:** Classification false negatives (treating a FEATURE as SMALL) will silently skip spec generation. Err on the side of over-classification.
- **Note:** Risk level (LOW / MODERATE / HIGH) is a second axis — HIGH risk tasks produce edge cases and failure modes in their ACs; LOW risk produces happy path only.
- **Model tier:** Sonnet — classifying "FEATURE vs SMALL" from a plain-language description requires understanding user intent, not just pattern matching; a misclassification silently skips spec generation, so accuracy matters
- **Checklist:**
  - [x] Define classification rubric: TRIVIAL (single line / config), SMALL (1-3 files, no new behavior), FEATURE (new vertical behavior, AC required), EPIC (multiple features, must be decomposed)
  - [x] Implement triage prompt that outputs structured JSON: `{ size, risk, routing_decision, slug }` — typed output enables downstream agents to consume without re-parsing
  - [x] TRIVIAL path: confirm intent, apply change, done — no spec file produced
  - [x] SMALL path: lightweight spec (ACs only, no arch section)
  - [x] FEATURE/EPIC path: full workflow (P0-C)
  - [x] Write triage unit tests: 5 representative inputs across all four sizes
  - [x] Verify no user configuration required to trigger routing
  - [x] State files use feature-slug-based filenames (`.plan-state-{slug}.local.yaml`) so concurrent sessions from the same directory do not clobber each other
  - [x] Auto-clear state file on task completion (`done — shipped`)
  - [x] Startup scan silently prunes completed (`done — shipped`) state files; surfaces files older than 30 days as abandoned with a cleanup prompt
  - [x] `update-plan-state.sh` supports `list` (enumerate all state files with age and phase), `clear --slug {slug}`, and `clear --all`

### P0-C: SDD Command (Core Planning Workflow)

- **What:** The primary `plan` command. Routes by triage size to produce the right artifact. **FEATURE tasks:** Gathers codebase context, produces testable acceptance criteria organized as vertical slices, selects an architecture pattern, and generates a TDD plan — output is a durable SPEC.md in `docs/`. **SMALL tasks:** Runs a QRSPI cycle (Question → Research → Structure → Plan → Implement) — output is a session-scoped IMPL_DETAILS.md with target files, ordered steps, git strategy, and verification actions. Both outputs are sufficient input for `/impl:tdd`.
- **Depends on:** P0-B (routing decision determines whether this runs and which mode)
- **Risk:** Spec quality degrades when codebase context is large. Implement progressive context loading (read entry points first; deep-read only what triage identifies as relevant). For SMALL tasks, the QRSPI cycle must resist the temptation to over-plan — a 3-file bug fix should not produce a 50-step plan.
- **Checklist:**
  - [x] Implement context-gathering phase: read entry points, identify relevant modules for the stated task
  - [x] Produce spec with required sections: Problem, Acceptance Criteria (testable, Given/When/Then), Vertical Slices, Architecture Recommendation, TDD Plan
  - [x] Ensure every AC is independently testable (no "and" in a single criterion)
  - [x] Include edge cases and failure modes in ACs when risk = HIGH
  - [x] Save spec to `docs/{feature}/specs/SPEC-{NNN}-{slug}.md` (see P0-G)
  - [x] Run the spec through the validate command (P0-E) before presenting to user; re-draft if score < 70
  - [x] Manual verification: feed a FEATURE task; confirm spec alone is sufficient to start `/impl:tdd`
  - [ ] **SMALL mode (QRSPI):** Implement Question phase — surface design decisions as explicit choices before reading code [ADDED]
  - [ ] **SMALL mode (QRSPI):** Implement Research phase — targeted codebase reading to answer each question with file:line evidence [ADDED]
  - [ ] **SMALL mode (QRSPI):** Implement Structure phase — phase breakdown with dependencies (usually 1-2 phases for SMALL tasks) [ADDED]
  - [ ] **SMALL mode (QRSPI):** Implement Plan phase — produce IMPL_DETAILS.md with: target files, ordered steps (each with exact file path + verification action), risks, git strategy (branch, commit checkpoints, PR title) [ADDED]
  - [ ] **SMALL mode (QRSPI):** Save IMPL_DETAILS.md to active session directory (`${SKILMARILLION_SESSIONS_DIR}/YYYY-MM-DD_<slug>/IMPL_DETAILS.md`), not `docs/` [ADDED]
  - [ ] **SMALL mode (QRSPI):** Run plan through `validate.py --type plan` before presenting; re-draft if score < 70 [ADDED]
  - [ ] **SMALL mode (QRSPI):** After plan approval, offer: "Execute now or hand to `/impl:tdd`?" — if execute, run implementation steps in-place within the same session [ADDED]
  - [ ] **Risk promotion:** When a SMALL task has HIGH risk, prompt user: "This task is small but high-risk. Promote to FEATURE workflow for full spec coverage?" [ADDED]
  - [ ] Manual verification: feed a SMALL task (bug fix); confirm IMPL_DETAILS.md is produced (not a spec) and is sufficient for `/impl:tdd` [ADDED]

### P0-D: PRD Command

- **What:** A standalone command that produces a client-shareable PRD document from a plain-language feature description. Follows the standard PRD format (Problem Statement, User Personas, Functional Requirements, NFRs, Scope Boundary, Milestones, Success Metrics).
- **Depends on:** P0-A
- **Risk:** Low — PRD generation is relatively self-contained.
- **Checklist:**
  - [x] Implement interview-style PRD authoring: gather problem, personas, requirements via structured prompts
  - [x] Output PRD in canonical format matching `docs/planning/PRD.md` structure
  - [x] Save to `docs/{feature}/PRD.md` (see P0-G)
  - [x] Verify status field defaults to "Draft — Awaiting Approval"
  - [x] Manual verification: run `/plan:prd` on a new feature description; confirm output is client-shareable without editing

### P0-E: Validate Command

- **What:** A validation command that accepts any spec, PRD, or plan document and returns a scored quality report (pass/fail at threshold 70/100) with specific, actionable findings for any gaps.
- **Depends on:** P0-A
- **Note:** This is the internal gate used by P0-C to validate specs before presenting them. Also exposed as a standalone command users can run on any document.
- **Model tier:** Sonnet — judging AC testability ("is this criterion independently verifiable?") and specificity requires understanding what makes a good acceptance criterion, not just pattern matching; this is an internal quality gate and a wrong pass propagates to implementation
- **Checklist:**
  - [x] Port and rewrite `prd-validator` scoring rubric from fotw source
  - [x] Support spec, PRD, and plan document types (detect from frontmatter or structure)
  - [x] Produce scored report: section coverage, AC testability, specificity of steps, missing sections
  - [x] Return machine-readable score for use as internal gate in P0-C
  - [x] Verify threshold: score >= 70 = PASS; score < 70 = NEEDS WORK with specific findings
  - [x] Test: run against a deliberately incomplete spec; confirm findings are actionable

### P0-F: Session Documentation Hooks

- **What:** Auto-registering hooks that create a dated session directory and `SESSION.md` on session start, rename the directory with an LLM-generated slug on the first user prompt, and append a deterministic INDEX.md entry on session end. Sessions organized into `YYYY-MM/` monthly subdirs. Path configurable via `$SKILMARILLION_SESSIONS_DIR`, defaulting to `$CLAUDE_PROJECT_DIR/.ai/sessions`.
- **Depends on:** P0-A
- **Risk:** Hooks auto-register via `hooks/hooks.json` — no manual `settings.json` editing needed.
- **Checklist:**
  - [x] Write `hooks/session_start.py`: creates `{sessions_root}/YYYY-MM/DD-HHMM_pending_{id}/SESSION.md`
  - [x] Write `hooks/slug_rename.py`: renames pending dir with slug from first user prompt (extracts ticket IDs)
  - [x] Write `hooks/session_end.py`: marks session completed, appends deterministic row to `INDEX.md`
  - [x] Write `hooks/hooks.json` for auto-registration (SessionStart, UserPromptSubmit, SessionEnd)
  - [x] Verify `SKILMARILLION_SESSIONS_DIR` override redirects session docs correctly
  - [x] Test: 27 unit tests covering creation, idempotency, slug generation, INDEX.md dedup, graceful degradation
- **Future:**
  - [ ] LLM-generated INDEX.md summaries (deterministic entry shipped first)
  - [ ] Update fotw `/session-index` skill to recurse into `YYYY-MM/` subdirs

### P0-G: Deterministic Artifact Paths

- **What:** Every `plan` command saves its output to a documented, predictable path so users and teammates can find any artifact without asking where it was saved.
- **Depends on:** P0-C, P0-D
- **Checklist:**
  - [x] Specs → `docs/{feature}/specs/SPEC-{NNN}-{slug}.md` (feature-grouped, auto-incrementing)
  - [x] PRDs → `docs/{feature}/PRD.md` (colocated with roadmap)
  - [x] Roadmaps → `docs/{feature}/ROADMAP.md` (colocated with PRD)
  - [x] Impl details → `docs/{feature}/plans/IMPL_DETAILS-{NNN}-{slug}.md` (convention reserved for `/impl`; session-scoped IMPL_DETAILS.md lives in session dir instead)
  - [x] Shared `artifact-paths` skill centralizes path resolution, slug algorithm, and project root detection
  - [x] Paths resolved relative to target project git root (not CWD)
  - [x] Confirm paths are created if directories don't exist (mkdir -p equivalent)
  - [x] Document all paths in `plan` README and CLAUDE.md
  - [x] Slug confirmed with user before save; user may override

### P0-I: Roadmap Command

- **What:** A standalone command that decomposes an approved PRD into a phased, ordered roadmap with shippable milestones. Each milestone maps to one or more `/plan:sdd` specs. The EPIC flow in `/plan:sdd` currently generates a phase map inline — this command extracts that responsibility into a dedicated, reusable command and replaces the EPIC inline decomposition.
- **Depends on:** P0-D (PRD command — roadmap consumes a PRD), P0-G (artifact paths — saves to `docs/{feature}/ROADMAP.md`)
- **Risk:** Roadmap quality depends on PRD quality. If the PRD is vague, the roadmap will decompose poorly. **Mitigation:** Gate on PRD validation score (>= 70) before generating the roadmap — refuse to proceed on an unvalidated PRD.
- **Model tier:** Sonnet — decomposing a PRD into ordered, dependency-aware milestones requires judgment about scope, coupling, and shippability; not a mechanical transformation.
- **Checklist:**
  - [ ] Implement `/plan:roadmap [prd-path]` command that accepts a PRD file path (or auto-discovers `docs/{feature}/PRD.md` if invoked from a feature directory)
  - [ ] Gate: run `validate.py` on the PRD before proceeding — refuse if score < 70 with message "PRD needs work before roadmap generation. Run `/plan:validate` to see findings."
  - [ ] Decompose PRD functional requirements into ordered milestones with: milestone name, capability delivered, dependency on prior milestones, estimated scope (SMALL/FEATURE), and acceptance summary
  - [ ] Identify critical path — which milestone must land first to unblock others
  - [ ] Produce ROADMAP.md with: phased milestone list, dependency graph (text or Mermaid), risk notes per milestone, and a checklist of `/plan:sdd` invocations to spec each milestone
  - [ ] Save to `{project_root}/docs/{feature}/ROADMAP.md` per `artifact-paths` skill (confirm path with user)
  - [ ] Refactor EPIC flow in `/plan:sdd`: replace inline phase map generation with delegation to `/plan:roadmap`, then proceed to spec Phase 1
  - [ ] Port relevant decomposition logic from `fotw:prd-to-roadmap` skill
  - [ ] Manual verification: run `/plan:roadmap` against a real PRD; confirm milestones are ordered, dependencies are explicit, and each milestone is independently spec-able via `/plan:sdd`

### P0-H: Migrate Command

- **What:** Given two codebase paths (source and target), produces a prioritized migration plan where every unit is an independently shippable spec with testable ACs. Units are ordered by coupling analysis and git hotspot data.
- **Depends on:** P0-C (each migration unit is a spec)
- **Risk:** Coupling analysis and git hotspot parsing may be brittle across diverse codebases. Scope to a known-good subset of analysis techniques.
- **Note:** This is a Should priority — ship after P0-A through P0-G are stable.
- **Checklist:**
  - [ ] Implement coupling analysis: identify modules with high fan-in (depended upon by many; migrate last)
  - [ ] Parse git log to identify hotspot files (frequently changed; migrate early to reduce churn)
  - [ ] Produce ordered list of migration units, each as an independent spec (P0-C format)
  - [ ] Save migration plan to `docs/{migration-slug}/ROADMAP.md` per `artifact-paths` skill
  - [ ] Manual verification: run on a small real codebase; confirm ordering is defensible

### P0-J: Help Command

- **What:** An interactive, context-aware tour of `plan`'s capabilities. Detects project state (existing specs, active state files, PRDs) and walks the user through available commands one at a time using `AskUserQuestion`. Ends with a recommended starting command based on current project context.
- **Depends on:** P0-A
- **Risk:** Low — read-only command with no state mutation.
- **Model tier:** Haiku — the help command reads project state and presents pre-written descriptions; no codebase reasoning or judgment required
- **Checklist:**
  - [ ] Implement `/plan:help` command
  - [ ] On startup: scan for existing specs (`docs/*/specs/`), active state files (`.plan-state-*.local.yaml`), PRDs (`docs/*/PRD.md`)
  - [ ] Adapt greeting based on findings: fresh project vs. existing artifacts vs. active workflow
  - [ ] Walk through commands one at a time: `sdd`, `prd`, `validate`, `roadmap`, `migrate`
  - [ ] For each command: describe purpose, show example invocation, name artifact produced
  - [ ] Use `AskUserQuestion` for navigation: "Next command?" / "Tell me more" / "Skip to a specific command"
  - [ ] End with recommended starting command based on project state
  - [ ] When referencing downstream plugins (`impl`, `arch`, `review`), include install command if not detected
  - [ ] Verify: run in a fresh project; confirm tour covers all commands and ends with a recommendation

### P0-K: Out-of-Order Guards

- **What:** Each `plan` command that produces downstream-consumable artifacts includes breadcrumb output referencing the next logical step. When that next step's plugin is not installed, the breadcrumb includes the install command. Guards are informational, not blocking.
- **Depends on:** P0-C (guards apply to sdd output), P0-D (guards apply to PRD output)
- **Risk:** Low — additive change to existing command output.
- **Checklist:**
  - [ ] After `/plan:sdd` completes, append to output: "Next step: `/impl:tdd {spec-path}`" with copy-pasteable command
  - [ ] If `impl` plugin not detected (check for `impl/.claude-plugin/plugin.json` relative to skilmarillion root or check installed plugins): add "Plugin not installed. Run `/plugin install impl@skilmarillion`"
  - [ ] After `/plan:prd` completes, append: "Next step: `/plan:roadmap {prd-path}` to decompose into milestones"
  - [ ] After `/plan:roadmap` completes, append: "Next step: `/plan:sdd` on each milestone to generate specs"
  - [ ] Verify: run `/plan:sdd` without `impl` installed; confirm install hint appears in output

**Deliverable:** *Users can run `/plan:prd` to define a feature, `/plan:roadmap` to decompose it into milestones, and `/plan:sdd` to spec each milestone — producing a complete PRD → Roadmap → Spec pipeline. Trivial tasks short-circuit in one round-trip. All artifacts land at deterministic, feature-grouped paths (`docs/{feature}/`). `/plan:help` provides guided discovery. Cross-plugin breadcrumbs guide users to the next step with install hints when needed.*

---

## Phase 0.5: `skil` — Workflow Router

**Entry Criteria:** None. Lightweight meta-plugin with no agents, no MCP deps, no write operations.
**Exit Criteria:** A user can run `/skil:help` to discover all installed plugins and their commands, `/skil [task]` to be routed to the appropriate plugin command, and `/skil:status` to see workflow state across installed plugins.

### P0.5-A: Plugin Scaffold

- **What:** Establish the `skil` meta-plugin — manifest, commands, CLAUDE.md, README. No agents, no skills, no MCP dependencies.
- **Depends on:** Nothing
- **Note:** `skil` is deliberately minimal. It delegates all real work to lifecycle plugins. It should be the first plugin a new user installs.
- **Checklist:**
  - [ ] Create `skil/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold `commands/` directory
  - [ ] Write `CLAUDE.md` describing `skil` as the router and discovery layer
  - [ ] Write `README.md` with: install instructions, command reference, recommended install order for lifecycle plugins
  - [ ] Verify `claude plugin add` loads `skil` without any other Skilmarillion plugin installed

### P0.5-B: Help Tour Command

- **What:** An interactive, context-aware tour of the full skilmarillion suite. Detects which lifecycle plugins are installed, what artifacts exist in the project, and walks the user through available commands one at a time. Unlike per-plugin `:help` commands (which go deep on one plugin), `/skil:help` covers the full suite at a high level and directs users to per-plugin help for details.
- **Depends on:** P0.5-A
- **Risk:** Tour content may become stale as plugins evolve. Keep descriptions in a single reference file within `skil` so updates are centralized.
- **Model tier:** Haiku — reads project state, presents pre-written descriptions, no codebase reasoning
- **Checklist:**
  - [ ] Implement `/skil:help` command
  - [ ] Detect installed plugins: check for `plan/`, `arch/`, `impl/`, `review/` plugin manifests
  - [ ] Detect project artifacts: specs, PRDs, active state files, review reports, open PRs
  - [ ] Adapt greeting: fresh project ("Let me show you around") vs. existing artifacts ("Looks like you've been working — here's what's available")
  - [ ] Walk through lifecycle phases in order: plan → arch → impl → review
  - [ ] For each phase: name, one-line purpose, key commands, artifact produced
  - [ ] For uninstalled plugins: show install command instead of commands
  - [ ] Use `AskUserQuestion` for pacing: "Next plugin?" / "Tell me more" / "Skip to a specific plugin"
  - [ ] End with recommended starting point based on project state
  - [ ] Verify: install only `skil` + `plan`; confirm tour shows `plan` commands and install hints for `arch`, `impl`, `review`

### P0.5-C: Task Router Command

- **What:** The default `/skil [task description]` command. Triages a plain-language task description and routes to the appropriate lifecycle plugin command. If the required plugin is not installed, tells the user what to install.
- **Depends on:** P0.5-A
- **Risk:** Routing heuristic may misroute tasks. Keep the heuristic simple: planning/spec tasks → `plan:sdd`, design/architecture tasks → `arch:*`, "build/implement/code" → `impl:tdd`, "review/audit/check" → `review:*`. When ambiguous, ask the user.
- **Model tier:** Haiku — the routing decision is keyword-based classification, not deep reasoning
- **Checklist:**
  - [ ] Implement `/skil [task]` as the default command
  - [ ] Route by intent classification: plan/spec/prd → `/plan:sdd`, design/api/schema/diagram → `/arch:*`, build/implement/code/fix → `/impl:tdd`, review/audit/security/a11y → `/review:*`
  - [ ] When intent is ambiguous, use `AskUserQuestion`: "What would you like to do?" with options mapping to lifecycle phases
  - [ ] When target plugin is not installed: "This task needs the `impl` plugin. Run `/plugin install impl@skilmarillion`"
  - [ ] When target plugin is installed: delegate by invoking the appropriate command with the task description
  - [ ] Verify: route "add user authentication" → `/plan:sdd`; route "review my PR" → `/review:review`; route ambiguous task → user prompt

### P0.5-D: Status Dashboard Command

- **What:** `/skil:status` shows the current workflow state across all installed plugins. Reads each plugin's state files and presents a unified view: active specs, in-progress implementations, pending reviews.
- **Depends on:** P0.5-A
- **Risk:** Each plugin's state file format must be stable. `skil` reads but never writes these files.
- **Model tier:** Haiku — reads files, formats output; no judgment required
- **Checklist:**
  - [ ] Implement `/skil:status` command
  - [ ] Read `plan` state: `.plan-state-*.local.yaml` files — show active features, current phases
  - [ ] Read `impl` state: `.impl-state-*.local.yaml` files — show in-progress TDD slices
  - [ ] Scan for artifacts: specs in `docs/*/specs/`, PRDs in `docs/*/PRD.md`, review reports in sessions dir
  - [ ] Present unified view: "Active work: [feature] — plan phase: spec-confirmed, impl phase: slice 2 of 4"
  - [ ] Gracefully handle missing plugins: "impl not installed — no implementation state available"
  - [ ] Verify: with active `plan` state and no `impl` installed; confirm output shows plan state and missing-plugin note

**Deliverable:** *Users can install `skil` as their first skilmarillion plugin and immediately discover the full suite via `/skil:help`, route any task to the right plugin via `/skil [task]`, and check workflow progress via `/skil:status` — all without reading documentation.*

---

## Phase 1: `impl` — Implementation

**Entry Criteria:** Phase 0 complete (`plan` produces validated specs). `impl` is most useful with plan-generated specs but can accept any spec file.
**Exit Criteria:** A user can take a `plan`-generated spec and optional `arch` artifacts, run `/impl:tdd`, execute the full slice-by-slice TDD cycle with quality gates, and open a PR — without leaving the plugin. `/impl:help` provides an interactive tour. Out-of-order guards warn when no spec is found.

### P1-A: Plugin Scaffold

- **What:** Establish the `impl` plugin directory structure following the same conventions as `plan`.
- **Depends on:** Nothing (independent plugin; mirrors scaffold pattern from P0-A)
- **Checklist:**
  - [ ] Create `impl/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold `commands/`, `agents/`, `skills/`, `references/` directories
  - [ ] Write `CLAUDE.md` and `README.md` with standalone entry conditions
  - [ ] Verify `claude plugin add` loads `impl` without `plan` or `arch` installed

### P1-B: TDD Command

- **What:** The primary `impl` command. Accepts either a **spec file** (from FEATURE workflow) or an **impl details file** (from SMALL/QRSPI workflow). When given a spec: generates a session-scoped IMPL_DETAILS.md translating the spec's ACs and slices into concrete implementation steps (target files, ordered steps, git strategy, verification actions), then executes slice by slice using RED-GREEN-REFACTOR. When given impl details: executes the steps directly. The session-scoped IMPL_DETAILS.md lives in the active session directory, not `docs/`.
- **Depends on:** P1-A
- **Risk:** If the spec's slices are not truly independent (slice 3 depends on slice 2 but the spec doesn't say so), the TDD cycle will fail mid-run. Document that specs must define slice dependencies.
- **Model tier:** Sonnet — coding requires codebase judgment, context synthesis, and slice-by-slice decision-making
- **Checklist:**
  - [ ] Implement input detection: distinguish spec files (contain `## Acceptance Criteria`, `## Vertical Slices`) from impl details files (contain `## Implementation Steps`, `## Target Files`) [ADDED]
  - [ ] **Spec input path:** Generate a session-scoped IMPL_DETAILS.md from the spec — translating ACs into implementation steps with target files, verification actions, and git strategy. Save to `${SKILMARILLION_SESSIONS_DIR}/YYYY-MM-DD_<slug>/IMPL_DETAILS.md` [ADDED]
  - [ ] **Impl details input path:** Read the impl details steps directly — no additional generation needed [ADDED]
  - [ ] Implement spec parser: read slices and their ACs from a `plan`-generated spec
  - [ ] Inject spec slices and any `arch` design artifacts (ADR, OpenAPI spec, schema) as structured context at session start — do not re-read files per slice iteration; pass already-loaded artifacts as typed inputs
  - [ ] For each slice: write failing test → confirm RED → write minimal production code → confirm GREEN → refactor → confirm GREEN
  - [ ] Gate: do not advance to next slice until all tests pass
  - [ ] Surface clear failure messages when RED confirmation fails for the wrong reason (syntax error vs. missing behavior)
  - [ ] Implement slice failure escalation: after 3 failed RED-GREEN attempts on the same slice, invoke a diagnostic step (root cause analysis) before retrying with a modified approach
  - [ ] Diagnostic step produces one of: modified approach (retry), sub-slice decomposition (split), or ACCEPT_WITH_DEBT (close slice with a documented gap — do not loop indefinitely)
  - [ ] ACCEPT_WITH_DEBT output: structured gap record `{ slice, missing_behavior, severity, justification }` appended to spec file; downstream slices receive gap notes so they can work around missing behavior
  - [ ] Handle impl-details-based input (SMALL tasks) with a simplified step-by-step cycle: execute each step, verify, advance [MODIFIED]
  - [ ] After each slice GREEN: if Playwright MCP available and dev server running, invoke browser AC verification for that slice (see P1-G); non-blocking if unavailable
  - [ ] Manual verification: run `/impl:tdd` against a spec; confirm session-scoped IMPL_DETAILS.md is generated before execution begins [ADDED]
  - [ ] Manual verification: run `/impl:tdd` against impl details; confirm steps execute directly without additional generation [ADDED]
  - [ ] Manual verification: run `/impl:tdd` against a P0-C-generated spec; confirm slice-by-slice execution with no manual intervention between slices

### P1-C: Debug Command

- **What:** Structured debugging that produces a root cause statement before proposing any fix. Follows four-phase methodology: reproduce → isolate → identify root cause → propose fix.
- **Depends on:** P1-A
- **Risk:** LLMs tend to jump to fixes. The root cause gate must be enforced structurally (require a filled root cause template before a fix is proposed).
- **Checklist:**
  - [ ] Port and rewrite `systematic-debugger` methodology from fotw source
  - [ ] Implement root cause template: "The bug occurs because [condition] causes [component] to [behavior] when [trigger]"
  - [ ] Block fix proposals until template is complete with specifics (no vague answers)
  - [ ] Enforce three-fix limit: after 3 failed fixes, stop and escalate to user
  - [ ] Manual verification: present a known bug; confirm root cause statement precedes fix proposal

### P1-D: Refactor Command

- **What:** Phase-gated refactoring that runs each transformation step (extract method, rename, dead code removal, etc.) only after all tests pass for the previous step.
- **Depends on:** P1-A
- **Checklist:**
  - [ ] Port and rewrite `refactoring-specialist` methodology from fotw source
  - [ ] Implement code smell detection: God objects, anemic models, premature abstractions, pattern soup
  - [ ] Each refactor step: transform → run full test suite → confirm green before next step
  - [ ] Never add behavior during refactor phase (enforce via post-step diff check)
  - [ ] Manual verification: apply to a file with known smells; confirm no behavior change and green suite throughout

### P1-E: Commit Command

- **What:** Generates a conventional commit message from staged changes, automatically detecting breaking changes (exclamation mark prefix, BREAKING CHANGE footer) and suggesting scope based on changed file paths.
- **Depends on:** P1-A
- **Model tier:** Haiku — diff → commit message is a deterministic transformation; input is structured (staged diff), output is a fixed format (conventional commit); no codebase reasoning required
- **Checklist:**
  - [ ] Port and rewrite `git-workflow` commit generation from fotw source
  - [ ] Parse `git diff --staged` to infer type (feat/fix/refactor/docs/chore) and scope
  - [ ] Detect breaking changes: flag if public API signatures changed or if any AC in spec is removed
  - [ ] Output: `type(scope)!: description` with optional body and `BREAKING CHANGE:` footer
  - [ ] Never commit automatically — output message for user to review and approve
  - [ ] Verify: stage a breaking change; confirm `!` and footer are present in output

### P1-F: PR Command

- **What:** Generates a pull request description. Detects and follows `.github/PULL_REQUEST_TEMPLATE.md` when present; falls back to a standard format (Summary, Test Plan, Checklist) when absent.
- **Depends on:** P1-E (PR typically follows commit)
- **Model tier:** Haiku when a PR template is present (mechanical section fill from diff + spec ACs); Sonnet when no template exists (judgment needed to write a coherent summary without structural guidance)
- **Checklist:**
  - [ ] Detect `.github/PULL_REQUEST_TEMPLATE.md` and parse its structure
  - [ ] When template present: fill each template section from staged diff and spec ACs
  - [ ] When template absent: use standard format (Summary bullets, Test Plan checklist, linked spec path)
  - [ ] Include spec path in PR description for traceability back to `plan` artifact
  - [ ] Verify: run in a repo with and without a PR template; confirm correct format in both cases

### P1-G: Playwright MCP Bundle (Optional)

- **What:** Bundle Playwright MCP in `impl` via a `.mcp.json` at the plugin root. When the user has `impl` installed, Playwright MCP starts automatically — no manual `claude mcp add` step. The TDD command uses it to verify ACs in a running browser after each slice's GREEN, when a dev server is available.
- **Depends on:** P1-A (plugin scaffold), P1-B (TDD command — browser verification hooks into the slice loop)
- **Risk:** Chromium may not be installed on the user's machine. The command must detect absence and fall back to test-only verification without erroring. Playwright install instructions belong in the README.
- **Note:** Use `.mcp.json` at plugin root — NOT inline `mcpServers` in `plugin.json` (open bug: [anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)). Browser verification is opt-in and non-blocking.
- **Model tier:** Haiku for dev-server detection (deterministic) + structured pass/fail output; browser interaction delegates to Playwright tools directly
- **Checklist:**
  - [ ] Create `impl/.mcp.json` with Playwright MCP server config using `${CLAUDE_PLUGIN_ROOT}` paths
  - [ ] Detect dev server: check CLAUDE.md first, then chat context, then package.json/Makefile scripts — ask user to confirm before starting
  - [ ] After each slice GREEN: if Playwright MCP available and dev server confirmed, invoke browser verification for that slice's ACs
  - [ ] Browser verification output: PASS (AC text) or FAILED (AC text, expected vs. observed, screenshot path on failure)
  - [ ] Graceful degradation: if Playwright MCP unavailable or dev server unreachable, log `Browser verification skipped — no dev server` and continue slice loop without blocking
  - [ ] Browser verification result appended to slice summary in SESSION.md
  - [ ] Verify: install `impl` with no prior MCP config; confirm Playwright MCP appears in `/mcp` output automatically
  - [ ] Verify: run TDD command with no dev server; confirm slice loop completes without error

### P1-H: Help Command

- **What:** Interactive tour of `impl`'s capabilities. Detects in-progress TDD state, existing specs, and active PRs to tailor guidance.
- **Depends on:** P1-A
- **Model tier:** Haiku
- **Checklist:**
  - [ ] Implement `/impl:help` command
  - [ ] Detect project state: active impl state files, specs in `docs/`, staged changes, open PRs
  - [ ] Walk through commands: `tdd`, `debug`, `refactor`, `commit`, `pr`
  - [ ] Recommend starting command based on state (e.g., spec exists but no impl state → suggest `/impl:tdd {spec-path}`)
  - [ ] Reference upstream (`/plan:sdd` for spec creation) and downstream (`/review:review` for code review) with install hints if not present
  - [ ] Verify: run in project with an existing spec; confirm recommendation targets that spec

### P1-I: Out-of-Order Guards

- **What:** Commands check preconditions and provide guidance when not met. Guards are informational, not blocking.
- **Depends on:** P1-B
- **Checklist:**
  - [ ] `/impl:tdd` with no argument and no specs in `docs/`: display "No spec found. Run `/plan:sdd [task]` to create one, or provide a spec path." Offer choices via `AskUserQuestion`: "Run /plan:sdd now" / "Provide a spec path" / "Proceed without spec"
  - [ ] After `/impl:tdd` completes all slices, append: "Next step: `/review:review` to run quality checks before merging"
  - [ ] After `/impl:commit` and `/impl:pr`, append: "Consider running `/review:review` on this PR"
  - [ ] If `review` not installed, include install command in breadcrumb
  - [ ] Verify: run `/impl:tdd` with no spec; confirm guidance appears and user can choose to proceed

**Deliverable:** *Users can bring a `plan` spec and optional `arch` design artifacts to `/impl:tdd`, implement each slice with full TDD quality gates (optionally extended with live browser AC verification when a dev server is running), and open a PR with a conventional commit and a correct PR description — without leaving the plugin. `/impl:help` provides guided discovery. Guards warn when prerequisites are missing.*

---

## Phase 2: `arch` — Architecture & Design

**Entry Criteria:** Phase 0 complete. `arch` is independently usable — users may invoke it standalone without any prior `plan` output. Build after `impl` for sequencing convenience only.
**Exit Criteria:** A user can run any `arch` command and receive a production-ready design artifact (ADR, OpenAPI spec, schema, diagram) saved to a documented, predictable path — ready to use as implementation input for `impl`.

### P2-A: Plugin Scaffold

- **What:** Establish the `arch` plugin directory structure — manifest, commands, agents, skills, CLAUDE.md, and README.
- **Depends on:** Nothing (independent plugin)
- **Checklist:**
  - [ ] Create `arch/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold `commands/`, `agents/`, `skills/`, `references/` directories
  - [ ] Write `CLAUDE.md` and `README.md` with standalone entry conditions
  - [ ] Verify `claude plugin add` loads `arch` without any other Skilmarillion plugin installed

### P2-B: System Design Command

- **What:** A structured design session that produces an Architecture Decision Record (ADR) and a C4 context diagram in Mermaid format, saved to `docs/adrs/`.
- **Depends on:** P2-A
- **Risk:** C4 diagram quality degrades when the system boundary is poorly defined. Enforce a system boundary clarification step before generating the diagram.
- **Checklist:**
  - [ ] Port and rewrite `system-design-reviewer` + `c4-architecture` from fotw source
  - [ ] Implement structured interview: system boundaries, actors, external dependencies, key quality attributes
  - [ ] Produce ADR with standard sections: Status, Context, Decision, Consequences
  - [ ] Produce C4 context diagram in Mermaid (system boundary, external actors, major integrations)
  - [ ] Save ADR to `docs/adrs/[NNN]-[title].md` with auto-incrementing NNN
  - [ ] Verify: run command for a simple system; confirm ADR and Mermaid diagram are syntactically valid

### P2-C: API Design Command

- **What:** A guided API design session that produces an OpenAPI 3.1 specification covering versioning strategy, pagination, and standard error envelopes.
- **Depends on:** P2-A
- **Risk:** OpenAPI 3.1 vs 3.0 differences (e.g., nullable handling) cause downstream validator failures. Pin to 3.1 and validate with a spec linter.
- **Checklist:**
  - [ ] Port and rewrite `api-design` from fotw source
  - [ ] Implement design interview: resource names, HTTP verbs, versioning strategy, auth scheme, pagination model
  - [ ] Include standard error envelope schema (RFC 7807 Problem Details or equivalent)
  - [ ] Include pagination schema (cursor-based or offset; document the trade-off)
  - [ ] Save to `docs/api/[api-name]-openapi.yaml`
  - [ ] Validate output with a YAML linter and OpenAPI schema validator
  - [ ] Verify: generate a spec for a simple CRUD API; confirm it passes `openapi-validator` with no errors

### P2-D: Schema Design Command

- **What:** A guided database schema design session that produces a schema definition and a zero-downtime migration plan (expand-contract pattern where relevant).
- **Depends on:** P2-A
- **Risk:** Zero-downtime migration plans are only valid for specific database engines. Scope to PostgreSQL initially; note limitations for other engines.
- **Checklist:**
  - [ ] Port and rewrite `database-schema-designer` from fotw source
  - [ ] Implement design interview: entity relationships, cardinality, indexes, normalization trade-offs
  - [ ] Produce schema in SQL DDL (PostgreSQL) with constraints and indexes
  - [ ] Produce zero-downtime migration plan: expand phase (additive changes), contract phase (remove old columns after backfill)
  - [ ] Save schema to `docs/schema/[name]-schema.sql` and migration plan to `docs/schema/[name]-migration.md`
  - [ ] Verify: design a schema with a column rename; confirm expand-contract plan is present and sequenced correctly

### P2-E: Diagram Command

- **What:** A general-purpose Mermaid diagram generator supporting flowcharts, sequence diagrams, ERDs, and C4 variants. Takes a plain-language description and produces a syntactically valid Mermaid diagram.
- **Depends on:** P2-A
- **Checklist:**
  - [ ] Port and rewrite `mermaid-diagram-specialist` from fotw source
  - [ ] Support: flowchart, sequence, ERD, C4 context, C4 container
  - [ ] Validate output is syntactically correct Mermaid before presenting
  - [ ] Save diagram to `docs/diagrams/[name]-[type].md`
  - [ ] Verify: generate each diagram type; paste into mermaid.live and confirm renders without errors

### P2-F: Help Command

- **What:** Interactive tour of `arch`'s capabilities. Detects existing ADRs, schemas, and diagrams to tailor guidance.
- **Depends on:** P2-A
- **Model tier:** Haiku
- **Checklist:**
  - [ ] Implement `/arch:help` command
  - [ ] Detect project state: existing ADRs in `docs/adrs/`, schemas, OpenAPI specs, diagrams
  - [ ] Walk through commands: `design`, `api`, `schema`, `diagram`
  - [ ] Recommend starting command based on context (e.g., no ADRs → suggest `/arch:design`)
  - [ ] Reference upstream (`/plan:sdd`) and downstream (`/impl:tdd`) with install hints if needed
  - [ ] Verify: run in a project with no design artifacts; confirm appropriate recommendation

### P2-G: Out-of-Order Guards

- **What:** Informational breadcrumbs after each command output referencing the next logical step.
- **Depends on:** P2-B, P2-C, P2-D, P2-E
- **Checklist:**
  - [ ] After design artifacts are saved, append: "These artifacts can be passed to `/impl:tdd` as structured context for implementation"
  - [ ] If `impl` not installed, include install hint
  - [ ] If a spec exists for the same feature, suggest: "A spec exists at {path} — `/impl:tdd {spec-path}` will pick up both the spec and these design artifacts"
  - [ ] Verify: produce an ADR without `impl` installed; confirm install hint in output

**Deliverable:** *Users can run `/arch:design`, `/arch:api`, `/arch:schema`, or `/arch:diagram` and receive a production-ready design artifact saved to a predictable path — ready to use as implementation input for `impl`. `/arch:help` provides guided discovery.*

---

## Phase 3: `review` — Review & Quality

**Entry Criteria:** Phase 1 complete (`impl` produces PRs that `review` evaluates). `review` is most useful with real PRs to review.
**Exit Criteria:** A user can run `/review:review` on any PR or file set and receive a parallel, deduplicated, prioritized review report. The a11y command performs live browser WCAG verification when a dev server is available, falling back to static analysis otherwise. `review` produces no code changes — findings only. `/review:help` provides an interactive tour. Guards inform when nothing is staged for review.

### P3-A: Plugin Scaffold

- **What:** Establish the `review` plugin directory structure.
- **Depends on:** Nothing (independent plugin)
- **Checklist:**
  - [ ] Create `review/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold directories; write `CLAUDE.md` and `README.md`
  - [ ] Verify `claude plugin add` loads `review` in isolation

### P3-B: Playwright MCP Bundle (Required)

- **What:** Bundle Playwright MCP in `review` via a `.mcp.json` at the plugin root. Installing `review` makes Playwright MCP available automatically. This enables the a11y command to perform live browser WCAG verification (navigate to running app, interact with elements, check real DOM state) rather than static code analysis alone.
- **Depends on:** P3-A (plugin scaffold)
- **Risk:** Same as P1-G — Chromium may be absent; graceful degradation to static analysis is required. `review` depends on this more heavily than `impl` (it is required, not optional) so the degradation message must be clear and actionable.
- **Note:** Use `.mcp.json` at plugin root — NOT inline `mcpServers` in `plugin.json` (open bug: [anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)).
- **Model tier:** Playwright tool invocations are deterministic; the a11y judgment agent (P3-E, Opus) interprets browser output — model tier lives there, not here
- **Checklist:**
  - [ ] Create `review/.mcp.json` with Playwright MCP server config using `${CLAUDE_PLUGIN_ROOT}` paths
  - [ ] Verify plugin install makes Playwright MCP appear in `/mcp` output automatically, without user running `claude mcp add`
  - [ ] Dev server detection: check CLAUDE.md, prior context, then package.json scripts; ask user to confirm URL before proceeding
  - [ ] On dev server confirmed: navigate to URL, produce accessibility tree snapshot, pass to a11y agent (P3-E)
  - [ ] On dev server unavailable or Playwright MCP not connected: fall back to static analysis; note in report: "Live browser verification unavailable — static analysis only. To enable: start dev server and re-run."
  - [ ] Browser session is read-only: no clicks that mutate state (form submits, deletes) — navigation and inspection only
  - [ ] Verify: install `review` with no prior MCP config; confirm Playwright MCP in `/mcp`; run `/review:a11y` against a running app; confirm browser-based findings appear

### P3-C: Review Command

- **What:** Spawns specialist reviewer agents in parallel (code quality, security, accessibility) and produces a unified report with deduplicated findings, sorted by impact-to-effort ratio, leading with what is working well before surfacing issues.
- **Depends on:** P3-A
- **Risk:** Parallel agents may produce duplicate or contradictory findings. Deduplication must normalize finding descriptions before collapsing.
- **Note:** `review` is evaluator-only. It must never propose or apply code changes.
- **Checklist:**
  - [ ] Port and rewrite `pragmatic-code-review` orchestration pattern from fotw source
  - [ ] Spawn three specialist agents in parallel: code quality, security (P3-D), accessibility (P3-E)
  - [ ] Each specialist agent: read-only tool access only (READ, GLOB, GREP, BASH) — no WRITE or EDIT; findings only; model tier: Opus (maximum accuracy — a missed finding is the failure mode)
  - [ ] Implement a deduplication synthesizer as a separate, tool-free step: receives structured output from all three agents, collapses near-duplicates, attributes to all sources; model tier: Haiku — no codebase access needed, pure aggregation of structured inputs
  - [ ] Sort findings by impact-to-effort ratio (HIGH impact, LOW effort first)
  - [ ] Lead report with "What's Working" section before surfacing issues
  - [ ] Save report to `${SKILMARILLION_SESSIONS_DIR:-.ai/sessions}/YYYY-MM-DD_<slug>/review-<target>.md`
  - [ ] Verify: run on a PR with known issues; confirm findings are deduplicated and no code edits are made

### P3-D: Clean Command

- **What:** Identifies and flags AI-generated noise in code — narrator comments ("Now we handle errors"), obvious comments (`// increment i`), hollow prose in docstrings — without altering logic or changing behavior.
- **Depends on:** P3-A
- **Risk:** Over-aggressive noise removal deletes genuinely useful comments. Confidence threshold must be high (>90%) before flagging.
- **Note:** `review` evaluates; the clean command produces a findings list, not a diff. The user applies changes.
- **Model tier:** Sonnet — distinguishing "genuinely useful comment" from "AI noise" is nuanced; the >90% confidence gate prevents over-firing but the judgment itself requires more than pattern matching; read-only
- **Checklist:**
  - [ ] Port and rewrite `desloppify` from fotw source
  - [ ] Define noise categories: narrator comments, obvious comments, hollow prose, excessive hedging
  - [ ] Produce findings list with file:line references and suggested replacements
  - [ ] Confidence gate: only flag findings with >90% confidence of being noise
  - [ ] Verify: run on a file with deliberate AI slop; confirm noise flagged and signal-carrying comments retained

### P3-E: Security Command

- **What:** A security-focused review that produces only findings with >80% confidence of real exploitation potential — no theoretical concerns, no CWE-number fishing.
- **Depends on:** P3-A
- **Risk:** False positives erode trust in the command. The 80% confidence threshold must be enforced structurally (require exploitation chain before flagging).
- **Model tier:** Opus — a missed real vulnerability is the worst outcome; exploitation chain reasoning requires deep understanding of code paths, attack surfaces, and precondition chains; read-only tool access only (READ, GLOB, GREP, BASH)
- **Checklist:**
  - [ ] Port and rewrite `security-review` from fotw source
  - [ ] For each finding, require: vulnerability type, exploitation chain, affected code path, severity (CRITICAL/HIGH/MEDIUM)
  - [ ] Suppress any finding where exploitation chain is theoretical or requires unlikely preconditions
  - [ ] Cover OWASP Top 10 as baseline scan surface
  - [ ] Save findings as a section in the review report (P3-C) or as standalone `security-<target>.md`
  - [ ] Verify: run on code with a known SQLI vulnerability; confirm it is found. Run on clean code; confirm no false positives.

### P3-F: A11y Command

- **What:** An accessibility audit that produces findings mapped to WCAG 2.1/2.2 criteria with severity ratings (critical/serious/moderate/minor) and reproduction steps. When Playwright MCP is available (see P3-B) and a dev server is running, performs live browser WCAG verification against real DOM state; otherwise falls back to static code analysis.
- **Depends on:** P3-A, P3-B (Playwright MCP bundle — required for browser mode)
- **Note:** Frontend-only. For backend or CLI code, the command should exit cleanly with "No UI components detected."
- **Model tier:** Opus — missing a WCAG criterion has real accessibility impact for real users; POUR principle coverage and criterion mapping requires authoritative judgment; read-only tool access only (READ, GLOB, GREP, BASH, Playwright MCP tools)
- **Checklist:**
  - [ ] Port and rewrite `accessibility-audit` from fotw source
  - [ ] Cover all four POUR principles (Perceivable, Operable, Understandable, Robust)
  - [ ] Map each finding to a WCAG 2.1/2.2 success criterion (e.g., 1.4.3 Contrast)
  - [ ] Assign severity: critical (blocks use), serious (major barrier), moderate (inconvenience), minor (best practice)
  - [ ] Include reproduction steps for each finding
  - [ ] **Browser mode (when Playwright MCP available + dev server confirmed):** Navigate to the running app, take accessibility tree snapshot, check color contrast via computed styles, verify keyboard focus order, check ARIA attributes against live DOM — findings grounded in real rendered state, not source code
  - [ ] **Static mode (fallback):** Analyze source code and component definitions for WCAG violations; note in report that findings are based on static analysis and may miss runtime-rendered issues
  - [ ] Report header must declare mode used: `Verification mode: live browser` or `Verification mode: static analysis (no dev server)`
  - [ ] Gracefully handle non-UI code: detect no DOM/component output and exit cleanly
  - [ ] Verify (browser mode): run on a running app with known contrast failure; confirm WCAG criterion cited, severity rated, and finding grounded in live DOM state
  - [ ] Verify (static mode): run with no dev server; confirm fallback note present and no error thrown

### P3-G: Help Command

- **What:** Interactive tour of `review`'s capabilities. Detects open PRs, existing review reports, and staged changes to tailor guidance.
- **Depends on:** P3-A
- **Model tier:** Haiku
- **Checklist:**
  - [ ] Implement `/review:help` command
  - [ ] Detect project state: open PRs (via `gh pr list`), existing review reports, staged changes, Playwright MCP availability
  - [ ] Walk through commands: `review`, `clean`, `security`, `a11y`
  - [ ] Recommend starting command based on state (e.g., open PR exists → suggest `/review:review {PR-number}`)
  - [ ] Reference upstream (`/impl:tdd` for implementation) with install hint if needed
  - [ ] Verify: run in project with an open PR; confirm recommendation targets that PR

### P3-H: Out-of-Order Guards

- **What:** Commands check preconditions and provide guidance when not met.
- **Depends on:** P3-C
- **Checklist:**
  - [ ] `/review:review` with no argument, no staged changes, and no open PR: display "Nothing to review. Provide a file path, PR number, or stage changes first." Offer choices via `AskUserQuestion`: "Review a specific file" / "Review latest PR" / "Cancel"
  - [ ] `/review:a11y` on a backend-only codebase: exit cleanly with "No UI components detected. This command targets frontend code."
  - [ ] After review completes, if findings exist: "To address these findings, run `/impl:debug` or `/impl:refactor`" (with install hint if needed)
  - [ ] Verify: run `/review:review` with nothing staged; confirm guidance appears

**Deliverable:** *Users can run `/review:review` on any PR or file set and receive a parallel, deduplicated, prioritized report covering code quality, AI noise, security, and accessibility — with no code changes made by the plugin. The a11y command performs live browser WCAG verification against a running app when available, with clear static-analysis fallback. `/review:help` provides guided discovery. Guards inform when nothing is available to review.*

---

## Phase 4: Homepage — GitHub Pages

**Entry Criteria:** Phases 0–3 complete. All five plugins ship and produce real artifacts. At least one real spec and one real review report exist to use as excerpt material.
**Exit Criteria:** The site is live at the project's GitHub Pages URL, communicates the problem and solution without requiring the visitor to read the README, shows the five-plugin suite and plan → arch → impl → review lifecycle visually, includes at least one real artifact excerpt, renders correctly on mobile and desktop, and achieves Lighthouse ≥ 90 on Performance, Accessibility, and Best Practices.

### P4-A: Site Scaffold

- **What:** Bootstrap the GitHub Pages site — directory structure, HTML/CSS files, and the repository configuration to enable GitHub Pages. No JS framework required; static HTML and CSS only unless a justified exception is made.
- **Depends on:** Nothing (can scaffold structure ahead of content, but content requires Phases 0–3)
- **Risk:** GitHub Pages branch or `/docs` directory configuration is a one-time manual step in repo settings. Document it explicitly so it isn't a surprise at launch.
- **Checklist:**
  - [ ] Create `docs/site/` (or `gh-pages` branch) with `index.html` and `style.css`
  - [ ] Enable GitHub Pages in repo settings, pointing to the correct branch/directory
  - [ ] Verify the site loads at the Pages URL with no 404 or build errors
  - [ ] Add a `<meta>` description, `og:title`, and `og:description` for link previews
  - [ ] Confirm mobile viewport meta tag is present

### P4-B: Core Narrative — Problem, Solution, Workflow

- **What:** The homepage's primary content: a clear statement of the problem (fragmented, inconsistent AI dev workflows), the solution (five coherent plugins), and a visual representation of the plan → arch → impl → review lifecycle with a one-line description and artifact output for each plugin. `skil` presented as the recommended starting point.
- **Depends on:** P4-A
- **Risk:** The narrative risks being too abstract ("better AI workflows") without concrete specificity. Ground each plugin description in what artifact it produces — specs, ADRs, review reports — not just what it does.
- **Checklist:**
  - [ ] Write problem statement section: 2-3 sentences, no jargon, grounded in the user's frustration (not in architecture)
  - [ ] Write solution section: introduce the five plugins by name with a one-line description each
  - [ ] Present `skil` as the recommended entry point: "Start here → `/skil:help`"
  - [ ] Build workflow visualization: plan → arch → impl → review as a visual sequence (CSS only, no JS library)
  - [ ] For each plugin node in the workflow, show: command invoked, artifact produced, example path
  - [ ] Add a primary CTA button linking to the GitHub repo

### P4-C: Artifact Excerpt Showcase

- **What:** At least one real artifact excerpt (e.g., 15–20 lines from an actual `/plan:sdd` spec or `/review:review` report) displayed on the page so visitors can evaluate output quality concretely without installing anything.
- **Depends on:** P4-B, and at least one real spec or review report from Phases 0–3
- **Risk:** Excerpts may become stale as plugin output evolves. Treat the showcase content as manually maintained; note in the repo that it should be refreshed when artifact format changes significantly.
- **Checklist:**
  - [ ] Select one real spec excerpt and/or one real review report excerpt from actual plugin output
  - [ ] Display as a styled code/pre block with syntax highlighting (CSS-only highlight is fine)
  - [ ] Truncate tastefully — show enough to demonstrate structure and quality, not a wall of text
  - [ ] Add a caption identifying the source command and plugin
  - [ ] Verify the excerpt renders correctly at mobile viewport width

### P4-D: Polish — Performance, Accessibility, Mobile

- **What:** Final quality pass ensuring the site meets NFR-005: Lighthouse ≥ 90 on Performance, Accessibility, and Best Practices; WCAG 2.1 AA for all interactive elements; correct rendering at mobile and desktop viewports.
- **Depends on:** P4-A, P4-B, P4-C
- **Risk:** A project that ships an accessibility audit plugin (`review:a11y`) with an inaccessible homepage is a credibility failure. This phase is not optional polish — it is a hard exit criterion.
- **Checklist:**
  - [ ] Run Lighthouse against the live Pages URL; confirm ≥ 90 on Performance, Accessibility, Best Practices
  - [ ] Fix any WCAG 2.1 AA failures (contrast, focus indicators, alt text, heading order)
  - [ ] Verify CTA button and any interactive elements are keyboard-navigable
  - [ ] Test at 375px (mobile) and 1280px (desktop) — no horizontal scroll, no clipped content
  - [ ] Confirm page load time < 2s on a standard connection (no unoptimized images or blocking scripts)
  - [ ] Run `/review:a11y` against the site's HTML as a final gate before marking phase complete

**Deliverable:** *A publicly hosted GitHub Pages site is live, communicating the "why" of skilmarillion with strong visual design, showing the full five-plugin suite with the plan → arch → impl → review lifecycle, `skil` as the entry point, real artifact excerpts, and linking visitors directly to the repo for installation.*

---

## Cross-Cutting Concerns

- **Claude Code only** (NFR-004): All commands use `/plugin:command` syntax. No Cursor, Copilot, or Windsurf compatibility layer is required or planned.
- **Plugin independence** (NFR-003): Each plugin's README must document its standalone entry conditions. No plugin may fail due to a missing sibling. When a command references a sibling plugin that is not installed, it provides an actionable install hint. Test each plugin in a clean environment before marking its phase complete.
- **Command discoverability** (NFR-006): The combination of `/skil:help` (full suite tour), per-plugin `:help` commands (deep dives), and out-of-order guards (contextual hints) forms a layered discoverability system. A new user who installs only `skil` can discover all four lifecycle plugins within 60 seconds.
- **Workflow repeatability** (NFR-002): Artifact structure (sections, headings, file path) must be identical across runs of the same command on the same input. Content may vary; structure must not. Verify with two runs per command before shipping each phase.
- **Ease of use for new users** (NFR-001): A user with no prior knowledge must be able to run `/skil:help` to discover commands, then invoke `/plan:sdd` and produce a meaningful artifact in their first session, without reading docs. Validate this by having a non-author user attempt it.
- **Source material is fotw** (Scope): All skills are rewritten from fotw source — not copied. Reference `~/src/github.com/TrevorEdris/fellowship-of-the-workflows`. Rewriting is a quality gate, not optional.
- **Distribution via GitHub** (Scope): No install script, GUI, or marketplace listing. Users clone/copy the repo. Each plugin's README covers installation.
- **Model tier defaults:** Each agent role carries a documented model tier annotation (Haiku / Sonnet / Opus). Haiku for deterministic, tool-free, or structured-output roles (commit formatting, review deduplication, help tours, routing). Sonnet for roles requiring judgment or codebase context (triage, spec validation, coding, clean). Opus for accuracy-critical review roles where a missed finding has real consequences (code quality review, security, accessibility). Never assign a heavier model to a role that doesn't need it. These annotations are defaults — users may override per-role via `models.<role>` config.
- **Homepage quality gate** (NFR-005): The GitHub Pages site must achieve Lighthouse ≥ 90 on Performance, Accessibility, and Best Practices. A project that ships an accessibility audit plugin with an inaccessible homepage is a credibility failure. Run `/review:a11y` against the site HTML before marking Phase 4 complete.
- **Bundled MCP servers** (FR-009): Plugins that require MCP tooling declare it in `.mcp.json` at the plugin root — never inline in `plugin.json` (open bug: [anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)). Use `${CLAUDE_PLUGIN_ROOT}` for all paths. Commands that depend on MCP tools must degrade gracefully when the tool is unavailable. Document the `npx playwright install chromium` step in each affected plugin's README.
- **Tool access constraints:** Reviewer and synthesizer agents are read-only (READ, GLOB, GREP, BASH only — no WRITE, EDIT). Synthesis/aggregation agents are tool-free. Only agents that produce code or artifacts (coder, spec writer, schema designer) have write access. Document tool access in each agent's definition.
- **Structured handoffs between agents:** Design artifacts from `arch` and specs from `plan` are injected as typed structured context into `impl` agents — not re-read from disk per iteration. This avoids redundant file reads and keeps per-iteration token cost low.
- **Failure escalation over blind retries:** Any agent that fails after a bounded number of attempts must escalate (invoke a diagnostic step or accept-with-debt) rather than retry the same strategy. Blind retry loops are a token anti-pattern and a quality failure.

---

## Dependency Summary

| Dependency | Source | Status |
|---|---|---|
| fotw (fellowship-of-the-workflows) | `~/src/github.com/TrevorEdris/fellowship-of-the-workflows` | Available |
| incubyte/claude-plugins (reference architecture) | `~/src/github.com/incubyte/claude-plugins` | Available |
| Claude Code plugin spec (`plugin.json` format) | Claude Code CLI | Stable (no breaking changes anticipated) |
| Playwright MCP | `npx playwright install chromium` | Available (graceful degradation when absent) |
| GitHub Pages | Repository settings (branch or `/docs` directory) | Requires one-time manual enable in repo settings |

---

## Spec Index

| ID | Name | Status | Phase | Roadmap Ref |
|----|------|--------|-------|-------------|
| PLAN-001 | Plugin Scaffold | COMPLETE | 0 | P0-A |
| PLAN-002 | Task Triage Engine | COMPLETE | 0 | P0-B |
| PLAN-003 | SDD Command | COMPLETE | 0 | P0-C |
| PLAN-004 | Validate Command | COMPLETE | 0 | P0-E |
| PLAN-005 | PRD Command | COMPLETE | 0 | P0-D |
| PLAN-006 | Session Hooks | COMPLETE | 0 | P0-F |
| PLAN-007 | Deterministic Paths | COMPLETE | 0 | P0-G |
| PLAN-008 | Migrate Command | PENDING | 0 | P0-H |
| PLAN-009 | Roadmap Command | PENDING | 0 | P0-I |
| PLAN-010 | Help Command | PENDING | 0 | P0-J |
| PLAN-011 | Out-of-Order Guards | PENDING | 0 | P0-K |
| PLAN-012 | QRSPI Mode for SMALL Tasks | PENDING | 0 | P0-C (extension) |
| SKIL-001 | Plugin Scaffold | PENDING | 0.5 | P0.5-A |
| SKIL-002 | Help Tour Command | PENDING | 0.5 | P0.5-B |
| SKIL-003 | Task Router Command | PENDING | 0.5 | P0.5-C |
| SKIL-004 | Status Dashboard | PENDING | 0.5 | P0.5-D |
| IMPL-001 | Plugin Scaffold | PENDING | 1 | P1-A |
| IMPL-002 | TDD Command | PENDING | 1 | P1-B |
| IMPL-003 | Debug Command | PENDING | 1 | P1-C |
| IMPL-004 | Refactor Command | PENDING | 1 | P1-D |
| IMPL-005 | Commit Command | PENDING | 1 | P1-E |
| IMPL-006 | PR Command | PENDING | 1 | P1-F |
| IMPL-007 | Playwright MCP Bundle (Optional) | PENDING | 1 | P1-G |
| IMPL-008 | Help Command | PENDING | 1 | P1-H |
| IMPL-009 | Out-of-Order Guards | PENDING | 1 | P1-I |
| ARCH-001 | Plugin Scaffold | PENDING | 2 | P2-A |
| ARCH-002 | System Design Command | PENDING | 2 | P2-B |
| ARCH-003 | API Design Command | PENDING | 2 | P2-C |
| ARCH-004 | Schema Design Command | PENDING | 2 | P2-D |
| ARCH-005 | Diagram Command | PENDING | 2 | P2-E |
| ARCH-006 | Help Command | PENDING | 2 | P2-F |
| ARCH-007 | Out-of-Order Guards | PENDING | 2 | P2-G |
| REVIEW-001 | Plugin Scaffold | PENDING | 3 | P3-A |
| REVIEW-002 | Playwright MCP Bundle (Required) | PENDING | 3 | P3-B |
| REVIEW-003 | Review Command | PENDING | 3 | P3-C |
| REVIEW-004 | Clean Command | PENDING | 3 | P3-D |
| REVIEW-005 | Security Command | PENDING | 3 | P3-E |
| REVIEW-006 | A11y Command | PENDING | 3 | P3-F |
| REVIEW-007 | Help Command | PENDING | 3 | P3-G |
| REVIEW-008 | Out-of-Order Guards | PENDING | 3 | P3-H |
| SITE-001 | Site Scaffold | PENDING | 4 | P4-A |
| SITE-002 | Core Narrative & Workflow | PENDING | 4 | P4-B |
| SITE-003 | Artifact Excerpt Showcase | PENDING | 4 | P4-C |
| SITE-004 | Polish & Quality Gate | PENDING | 4 | P4-D |
