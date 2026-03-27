# Skilmarillion — Roadmap

## Current Status

**Phase:** 0 — In Progress
**Last Updated:** 2026-03-27

### Completed
- [x] DREAM-001: Plugin Scaffold (P0-A) — merged PR #1
- [x] DREAM-002: Task Triage Engine (P0-B) — merged PR #2

### In Progress
- [ ] DREAM-003: SDD Core Planning Workflow (P0-C)

### Not Started
- [ ] Phase 1: `draft` — Architecture & Design
- [ ] Phase 2: `do` — Implementation
- [ ] Phase 3: `discern` — Review & Quality
- [ ] Phase 4: Homepage — GitHub Pages

---

## Philosophy

Build the lifecycle vertically, one plugin at a time, with each phase delivering something independently useful before the next begins. Phases follow workflow order — `dream` (specify) → `draft` (design) → `do` (implement) → `discern` (review) — because design artifacts from `draft` are inputs to `do`, and users should have both before writing code.

**Model tiering principle:** Use the minimum model that can handle the task reliably. Haiku for deterministic, tool-free, or structured-output tasks (commit formatting, review deduplication). Sonnet for tasks requiring judgment, codebase context, or design reasoning. Opus for roles where a missed finding has real consequences — security vulnerabilities, accessibility barriers, and code quality issues that could reach production. Never assign a heavier model to a role that doesn't need it — cost compounds across multi-agent workflows.

**Tool access principle:** Agents that only produce findings or aggregate structured inputs must be read-only or tool-free. No agent should have WRITE or EDIT access unless it is explicitly producing code or files. Constrained tool sets prevent context bloat and enforce role boundaries.

---

## Phase 0: `dream` — Spec-Driven Planning

**Entry Criteria:** Repository scaffolded; `incubyte/claude-plugins` reference architecture reviewed; fotw source skills identified.
**Exit Criteria:** A user can run `/dream:sdd` with a plain-language task description and receive a spec with testable acceptance criteria, an architecture recommendation, and a TDD plan — without reading documentation first. Trivial tasks short-circuit in one round-trip. All artifacts land at deterministic paths.

### P0-A: Plugin Scaffold

- **What:** Establish the `dream` plugin directory structure — manifest, commands, agents, skills, CLAUDE.md, and README — following the `incubyte/claude-plugins` reference architecture.
- **Depends on:** Nothing
- **Risk:** `plugin.json` manifest format may evolve; pin to a known-good Claude Code version.
- **Checklist:**
  - [ ] Create `.claude-plugin/` directory with `plugin.json` manifest (name, version, description, commands)
  - [ ] Scaffold `commands/`, `agents/`, `skills/`, `references/` directories
  - [ ] Write `CLAUDE.md` for the `dream` plugin context
  - [ ] Write `README.md` with standalone entry conditions and command reference
  - [ ] Verify `claude plugin add` loads the plugin without errors

### P0-B: Task Triage Engine

- **What:** When a user describes a task, `dream` automatically classifies it as TRIVIAL, SMALL, FEATURE, or EPIC and routes accordingly — trivial tasks get a one-round-trip confirmation; feature-scale tasks get the full spec workflow.
- **Depends on:** P0-A
- **Risk:** Classification false negatives (treating a FEATURE as SMALL) will silently skip spec generation. Err on the side of over-classification.
- **Note:** Risk level (LOW / MODERATE / HIGH) is a second axis — HIGH risk tasks produce edge cases and failure modes in their ACs; LOW risk produces happy path only.
- **Model tier:** Sonnet — classifying "FEATURE vs SMALL" from a plain-language description requires understanding user intent, not just pattern matching; a misclassification silently skips spec generation, so accuracy matters
- **Checklist:**
  - [ ] Define classification rubric: TRIVIAL (single line / config), SMALL (1-3 files, no new behavior), FEATURE (new vertical behavior, AC required), EPIC (multiple features, must be decomposed)
  - [ ] Implement triage prompt that outputs structured JSON: `{ size, risk, routing_decision, slug }` — typed output enables downstream agents to consume without re-parsing
  - [ ] TRIVIAL path: confirm intent, apply change, done — no spec file produced
  - [ ] SMALL path: lightweight spec (ACs only, no arch section)
  - [ ] FEATURE/EPIC path: full workflow (P0-C)
  - [ ] Write triage unit tests: 5 representative inputs across all four sizes
  - [ ] Verify no user configuration required to trigger routing
  - [ ] State files use feature-slug-based filenames (`.dream-state-{slug}.local.md`) so concurrent sessions from the same directory do not clobber each other
  - [ ] Auto-clear state file on task completion (`done — shipped`)
  - [ ] Startup scan silently prunes completed (`done — shipped`) state files; surfaces files older than 30 days as abandoned with a cleanup prompt
  - [ ] `update-dream-state.sh` supports `list` (enumerate all state files with age and phase), `clear --slug {slug}`, and `clear --all`

### P0-C: SDD Command (Core Planning Workflow)

- **What:** The primary `dream` command. Gathers codebase context, produces testable acceptance criteria organized as vertical slices, selects an architecture pattern, and generates a TDD plan — all before any code is written. The output spec is sufficient input for `/do:tdd` with no additional clarification.
- **Depends on:** P0-B (routing decision determines whether this runs)
- **Risk:** Spec quality degrades when codebase context is large. Implement progressive context loading (read entry points first; deep-read only what triage identifies as relevant).
- **Checklist:**
  - [ ] Implement context-gathering phase: read entry points, identify relevant modules for the stated task
  - [ ] Produce spec with required sections: Problem, Acceptance Criteria (testable, Given/When/Then), Vertical Slices, Architecture Recommendation, TDD Plan
  - [ ] Ensure every AC is independently testable (no "and" in a single criterion)
  - [ ] Include edge cases and failure modes in ACs when risk = HIGH
  - [ ] Save spec to `docs/specs/[feature-name]-spec.md` (see P0-G)
  - [ ] Run the spec through the validate command (P0-E) before presenting to user; re-draft if score < 70
  - [ ] Manual verification: feed a FEATURE task; confirm spec alone is sufficient to start `/do:tdd`

### P0-D: PRD Command

- **What:** A standalone command that produces a client-shareable PRD document from a plain-language feature description. Follows the standard PRD format (Problem Statement, User Personas, Functional Requirements, NFRs, Scope Boundary, Milestones, Success Metrics).
- **Depends on:** P0-A
- **Risk:** Low — PRD generation is relatively self-contained.
- **Checklist:**
  - [ ] Implement interview-style PRD authoring: gather problem, personas, requirements via structured prompts
  - [ ] Output PRD in canonical format matching `docs/planning/PRD.md` structure
  - [ ] Save to `docs/prds/[feature-name]-prd.md` (see P0-G)
  - [ ] Verify status field defaults to "Draft — Awaiting Approval"
  - [ ] Manual verification: run `/dream:prd` on a new feature description; confirm output is client-shareable without editing

### P0-E: Validate Command

- **What:** A validation command that accepts any spec, PRD, or plan document and returns a scored quality report (pass/fail at threshold 70/100) with specific, actionable findings for any gaps.
- **Depends on:** P0-A
- **Note:** This is the internal gate used by P0-C to validate specs before presenting them. Also exposed as a standalone command users can run on any document.
- **Model tier:** Sonnet — judging AC testability ("is this criterion independently verifiable?") and specificity requires understanding what makes a good acceptance criterion, not just pattern matching; this is an internal quality gate and a wrong pass propagates to implementation
- **Checklist:**
  - [ ] Port and rewrite `prd-validator` scoring rubric from fotw source
  - [ ] Support spec, PRD, and plan document types (detect from frontmatter or structure)
  - [ ] Produce scored report: section coverage, AC testability, specificity of steps, missing sections
  - [ ] Return machine-readable score for use as internal gate in P0-C
  - [ ] Verify threshold: score >= 70 = PASS; score < 70 = NEEDS WORK with specific findings
  - [ ] Test: run against a deliberately incomplete spec; confirm findings are actionable

### P0-F: Session Documentation Hooks

- **What:** Hook configuration that automatically creates a dated session directory and `SESSION.md` at the start of each Claude Code session, and appends a one-line summary entry to `INDEX.md` at session end. Session path is configurable via `$SKILMARILLION_SESSIONS_DIR`, defaulting to `.ai/sessions`.
- **Depends on:** P0-A
- **Risk:** Hooks require manual user configuration in `settings.json`. Clear documentation is the mitigation.
- **Checklist:**
  - [ ] Write `hooks/session-start.sh`: creates `${SKILMARILLION_SESSIONS_DIR:-.ai/sessions}/YYYY-MM-DD_<slug>/SESSION.md`
  - [ ] Write `hooks/session-end.sh`: appends one-line entry to `INDEX.md` in the sessions root
  - [ ] Document exact `settings.json` hook configuration in `dream`'s README
  - [ ] Verify `SKILMARILLION_SESSIONS_DIR` override redirects session docs correctly (e.g., to an Obsidian vault path)
  - [ ] Test: start a session; confirm `SESSION.md` created at correct path without user action
  - [ ] Test: end a session; confirm `INDEX.md` updated with one-line entry

### P0-G: Deterministic Artifact Paths

- **What:** Every `dream` command saves its output to a documented, predictable path so users and teammates can find any artifact without asking where it was saved.
- **Depends on:** P0-C, P0-D
- **Checklist:**
  - [ ] Specs → `docs/specs/[feature-name]-spec.md`
  - [ ] PRDs → `docs/prds/[feature-name]-prd.md`
  - [ ] Confirm paths are created if directories don't exist (mkdir -p equivalent)
  - [ ] Document all paths in `dream` README
  - [ ] Verify: run two commands back-to-back; confirm no path collisions, no prompting for save location

### P0-H: Migrate Command

- **What:** Given two codebase paths (source and target), produces a prioritized migration plan where every unit is an independently shippable spec with testable ACs. Units are ordered by coupling analysis and git hotspot data.
- **Depends on:** P0-C (each migration unit is a spec)
- **Risk:** Coupling analysis and git hotspot parsing may be brittle across diverse codebases. Scope to a known-good subset of analysis techniques.
- **Note:** This is a Should priority — ship after P0-A through P0-G are stable.
- **Checklist:**
  - [ ] Implement coupling analysis: identify modules with high fan-in (depended upon by many; migrate last)
  - [ ] Parse git log to identify hotspot files (frequently changed; migrate early to reduce churn)
  - [ ] Produce ordered list of migration units, each as an independent spec (P0-C format)
  - [ ] Save migration plan to `docs/specs/migration-[source-to-target].md`
  - [ ] Manual verification: run on a small real codebase; confirm ordering is defensible

**Deliverable:** *Users can run `/dream:sdd` on any task and receive a spec with testable acceptance criteria, an architecture recommendation, and a TDD plan. Trivial tasks complete in one round-trip. Artifacts always land at the same predictable paths.*

---

## Phase 1: `draft` — Architecture & Design

**Entry Criteria:** Phase 0 complete. `dream` produces validated specs. `draft` is independently usable — users may also invoke it standalone without any prior `dream` output.
**Exit Criteria:** A user can run any `draft` command and receive a production-ready design artifact (ADR, OpenAPI spec, schema, diagram) saved to a documented, predictable path — ready to hand to `do` as implementation input.

### P1-A: Plugin Scaffold

- **What:** Establish the `draft` plugin directory structure — manifest, commands, agents, skills, CLAUDE.md, and README.
- **Depends on:** Nothing (independent plugin)
- **Checklist:**
  - [ ] Create `draft/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold `commands/`, `agents/`, `skills/`, `references/` directories
  - [ ] Write `CLAUDE.md` and `README.md` with standalone entry conditions
  - [ ] Verify `claude plugin add` loads `draft` without any other Skilmarillion plugin installed

### P1-B: System Design Command

- **What:** A structured design session that produces an Architecture Decision Record (ADR) and a C4 context diagram in Mermaid format, saved to `docs/adrs/`.
- **Depends on:** P1-A
- **Risk:** C4 diagram quality degrades when the system boundary is poorly defined. Enforce a system boundary clarification step before generating the diagram.
- **Checklist:**
  - [ ] Port and rewrite `system-design-reviewer` + `c4-architecture` from fotw source
  - [ ] Implement structured interview: system boundaries, actors, external dependencies, key quality attributes
  - [ ] Produce ADR with standard sections: Status, Context, Decision, Consequences
  - [ ] Produce C4 context diagram in Mermaid (system boundary, external actors, major integrations)
  - [ ] Save ADR to `docs/adrs/[NNN]-[title].md` with auto-incrementing NNN
  - [ ] Verify: run command for a simple system; confirm ADR and Mermaid diagram are syntactically valid

### P1-C: API Design Command

- **What:** A guided API design session that produces an OpenAPI 3.1 specification covering versioning strategy, pagination, and standard error envelopes.
- **Depends on:** P1-A
- **Risk:** OpenAPI 3.1 vs 3.0 differences (e.g., nullable handling) cause downstream validator failures. Pin to 3.1 and validate with a spec linter.
- **Checklist:**
  - [ ] Port and rewrite `api-design` from fotw source
  - [ ] Implement design interview: resource names, HTTP verbs, versioning strategy, auth scheme, pagination model
  - [ ] Include standard error envelope schema (RFC 7807 Problem Details or equivalent)
  - [ ] Include pagination schema (cursor-based or offset; document the trade-off)
  - [ ] Save to `docs/api/[api-name]-openapi.yaml`
  - [ ] Validate output with a YAML linter and OpenAPI schema validator
  - [ ] Verify: generate a spec for a simple CRUD API; confirm it passes `openapi-validator` with no errors

### P1-D: Schema Design Command

- **What:** A guided database schema design session that produces a schema definition and a zero-downtime migration plan (expand-contract pattern where relevant).
- **Depends on:** P1-A
- **Risk:** Zero-downtime migration plans are only valid for specific database engines. Scope to PostgreSQL initially; note limitations for other engines.
- **Checklist:**
  - [ ] Port and rewrite `database-schema-designer` from fotw source
  - [ ] Implement design interview: entity relationships, cardinality, indexes, normalization trade-offs
  - [ ] Produce schema in SQL DDL (PostgreSQL) with constraints and indexes
  - [ ] Produce zero-downtime migration plan: expand phase (additive changes), contract phase (remove old columns after backfill)
  - [ ] Save schema to `docs/schema/[name]-schema.sql` and migration plan to `docs/schema/[name]-migration.md`
  - [ ] Verify: design a schema with a column rename; confirm expand-contract plan is present and sequenced correctly

### P1-E: Diagram Command

- **What:** A general-purpose Mermaid diagram generator supporting flowcharts, sequence diagrams, ERDs, and C4 variants. Takes a plain-language description and produces a syntactically valid Mermaid diagram.
- **Depends on:** P1-A
- **Checklist:**
  - [ ] Port and rewrite `mermaid-diagram-specialist` from fotw source
  - [ ] Support: flowchart, sequence, ERD, C4 context, C4 container
  - [ ] Validate output is syntactically correct Mermaid before presenting
  - [ ] Save diagram to `docs/diagrams/[name]-[type].md`
  - [ ] Verify: generate each diagram type; paste into mermaid.live and confirm renders without errors

**Deliverable:** *Users can run `/draft:design`, `/draft:api`, `/draft:schema`, or `/draft:diagram` and receive a production-ready design artifact saved to a predictable path — ready to use as implementation input for `do`.*

---

## Phase 2: `do` — Implementation

**Entry Criteria:** Phase 0 complete (`dream` produces validated specs). Phase 1 complete (`draft` produces design artifacts). A user can bring both a spec and design artifacts to `do` without gaps.
**Exit Criteria:** A user can take a `dream`-generated spec and optional `draft` artifacts, run `/do:tdd`, execute the full slice-by-slice TDD cycle with quality gates, and open a PR — without leaving the plugin.

### P2-A: Plugin Scaffold

- **What:** Establish the `do` plugin directory structure following the same conventions as `dream` and `draft`.
- **Depends on:** Nothing (independent plugin; mirrors scaffold pattern from P0-A and P1-A)
- **Checklist:**
  - [ ] Create `do/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold `commands/`, `agents/`, `skills/`, `references/` directories
  - [ ] Write `CLAUDE.md` and `README.md` with standalone entry conditions
  - [ ] Verify `claude plugin add` loads `do` without `dream` or `draft` installed

### P2-B: TDD Command

- **What:** The primary `do` command. Accepts a spec file path, reads each vertical slice in order, implements it using RED-GREEN-REFACTOR, gates advancement on all tests passing, and repeats until all slices are complete.
- **Depends on:** P2-A
- **Risk:** If the spec's slices are not truly independent (slice 3 depends on slice 2 but the spec doesn't say so), the TDD cycle will fail mid-run. Document that specs must define slice dependencies.
- **Model tier:** Sonnet — coding requires codebase judgment, context synthesis, and slice-by-slice decision-making
- **Checklist:**
  - [ ] Implement spec parser: read slices and their ACs from a `dream`-generated spec
  - [ ] Inject spec slices and any `draft` design artifacts (ADR, OpenAPI spec, schema) as structured context at session start — do not re-read files per slice iteration; pass already-loaded artifacts as typed inputs
  - [ ] For each slice: write failing test → confirm RED → write minimal production code → confirm GREEN → refactor → confirm GREEN
  - [ ] Gate: do not advance to next slice until all tests pass
  - [ ] Surface clear failure messages when RED confirmation fails for the wrong reason (syntax error vs. missing behavior)
  - [ ] Implement slice failure escalation: after 3 failed RED-GREEN attempts on the same slice, invoke a diagnostic step (root cause analysis) before retrying with a modified approach
  - [ ] Diagnostic step produces one of: modified approach (retry), sub-slice decomposition (split), or ACCEPT_WITH_DEBT (close slice with a documented gap — do not loop indefinitely)
  - [ ] ACCEPT_WITH_DEBT output: structured gap record `{ slice, missing_behavior, severity, justification }` appended to spec file; downstream slices receive gap notes so they can work around missing behavior
  - [ ] Handle TRIVIAL and SMALL specs (no slice structure) with a simplified one-step cycle
  - [ ] After each slice GREEN: if Playwright MCP available and dev server running, invoke browser AC verification for that slice (see P2-G); non-blocking if unavailable
  - [ ] Manual verification: run `/do:tdd` against a P0-C-generated spec; confirm slice-by-slice execution with no manual intervention between slices

### P2-C: Debug Command

- **What:** Structured debugging that produces a root cause statement before proposing any fix. Follows four-phase methodology: reproduce → isolate → identify root cause → propose fix.
- **Depends on:** P2-A
- **Risk:** LLMs tend to jump to fixes. The root cause gate must be enforced structurally (require a filled root cause template before a fix is proposed).
- **Checklist:**
  - [ ] Port and rewrite `systematic-debugger` methodology from fotw source
  - [ ] Implement root cause template: "The bug occurs because [condition] causes [component] to [behavior] when [trigger]"
  - [ ] Block fix proposals until template is complete with specifics (no vague answers)
  - [ ] Enforce three-fix limit: after 3 failed fixes, stop and escalate to user
  - [ ] Manual verification: present a known bug; confirm root cause statement precedes fix proposal

### P2-D: Refactor Command

- **What:** Phase-gated refactoring that runs each transformation step (extract method, rename, dead code removal, etc.) only after all tests pass for the previous step.
- **Depends on:** P2-A
- **Checklist:**
  - [ ] Port and rewrite `refactoring-specialist` methodology from fotw source
  - [ ] Implement code smell detection: God objects, anemic models, premature abstractions, pattern soup
  - [ ] Each refactor step: transform → run full test suite → confirm green before next step
  - [ ] Never add behavior during refactor phase (enforce via post-step diff check)
  - [ ] Manual verification: apply to a file with known smells; confirm no behavior change and green suite throughout

### P2-G: Playwright MCP Bundle (Optional)

- **What:** Bundle Playwright MCP in `do` via a `.mcp.json` at the plugin root. When the user has `do` installed, Playwright MCP starts automatically — no manual `claude mcp add` step. The TDD command uses it to verify ACs in a running browser after each slice's GREEN, when a dev server is available.
- **Depends on:** P2-A (plugin scaffold), P2-B (TDD command — browser verification hooks into the slice loop)
- **Risk:** Chromium may not be installed on the user's machine. The command must detect absence and fall back to test-only verification without erroring. Playwright install instructions belong in the README.
- **Note:** Use `.mcp.json` at plugin root — NOT inline `mcpServers` in `plugin.json` (open bug: [anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)). Browser verification is opt-in and non-blocking.
- **Model tier:** Haiku for dev-server detection (deterministic) + structured pass/fail output; browser interaction delegates to Playwright tools directly
- **Checklist:**
  - [ ] Create `do/.mcp.json` with Playwright MCP server config using `${CLAUDE_PLUGIN_ROOT}` paths
  - [ ] Detect dev server: check CLAUDE.md first, then chat context, then package.json/Makefile scripts — ask user to confirm before starting
  - [ ] After each slice GREEN: if Playwright MCP available and dev server confirmed, invoke browser verification for that slice's ACs
  - [ ] Browser verification output: PASS (AC text) or FAILED (AC text, expected vs. observed, screenshot path on failure)
  - [ ] Graceful degradation: if Playwright MCP unavailable or dev server unreachable, log `Browser verification skipped — no dev server` and continue slice loop without blocking
  - [ ] Browser verification result appended to slice summary in SESSION.md
  - [ ] Verify: install `do` with no prior MCP config; confirm Playwright MCP appears in `/mcp` output automatically
  - [ ] Verify: run TDD command with no dev server; confirm slice loop completes without error

### P2-E: Commit Command

- **What:** Generates a conventional commit message from staged changes, automatically detecting breaking changes (exclamation mark prefix, BREAKING CHANGE footer) and suggesting scope based on changed file paths.
- **Depends on:** P2-A
- **Model tier:** Haiku — diff → commit message is a deterministic transformation; input is structured (staged diff), output is a fixed format (conventional commit); no codebase reasoning required
- **Checklist:**
  - [ ] Port and rewrite `git-workflow` commit generation from fotw source
  - [ ] Parse `git diff --staged` to infer type (feat/fix/refactor/docs/chore) and scope
  - [ ] Detect breaking changes: flag if public API signatures changed or if any AC in spec is removed
  - [ ] Output: `type(scope)!: description` with optional body and `BREAKING CHANGE:` footer
  - [ ] Never commit automatically — output message for user to review and approve
  - [ ] Verify: stage a breaking change; confirm `!` and footer are present in output

### P2-F: PR Command

- **What:** Generates a pull request description. Detects and follows `.github/PULL_REQUEST_TEMPLATE.md` when present; falls back to a standard format (Summary, Test Plan, Checklist) when absent.
- **Depends on:** P2-E (PR typically follows commit)
- **Model tier:** Haiku when a PR template is present (mechanical section fill from diff + spec ACs); Sonnet when no template exists (judgment needed to write a coherent summary without structural guidance)
- **Checklist:**
  - [ ] Detect `.github/PULL_REQUEST_TEMPLATE.md` and parse its structure
  - [ ] When template present: fill each template section from staged diff and spec ACs
  - [ ] When template absent: use standard format (Summary bullets, Test Plan checklist, linked spec path)
  - [ ] Include spec path in PR description for traceability back to `dream` artifact
  - [ ] Verify: run in a repo with and without a PR template; confirm correct format in both cases

**Deliverable:** *Users can bring a `dream` spec and optional `draft` design artifacts to `/do:tdd`, implement each slice with full TDD quality gates (optionally extended with live browser AC verification when a dev server is running), and open a PR with a conventional commit and a correct PR description — without leaving the plugin.*

---

## Phase 3: `discern` — Review & Quality

**Entry Criteria:** Phase 2 complete (`do` produces PRs that `discern` evaluates). `discern` is most useful with real PRs to review.
**Exit Criteria:** A user can run `/discern:review` on any PR or file set and receive a parallel, deduplicated, prioritized review report. The a11y command performs live browser WCAG verification when a dev server is available, falling back to static analysis otherwise. `discern` produces no code changes — findings only.

### P3-A: Plugin Scaffold

- **What:** Establish the `discern` plugin directory structure.
- **Depends on:** Nothing (independent plugin)
- **Checklist:**
  - [ ] Create `discern/.claude-plugin/plugin.json` manifest
  - [ ] Scaffold directories; write `CLAUDE.md` and `README.md`
  - [ ] Verify `claude plugin add` loads `discern` in isolation

### P3-F: Playwright MCP Bundle (Required)

- **What:** Bundle Playwright MCP in `discern` via a `.mcp.json` at the plugin root. Installing `discern` makes Playwright MCP available automatically. This enables the a11y command to perform live browser WCAG verification (navigate to running app, interact with elements, check real DOM state) rather than static code analysis alone.
- **Depends on:** P3-A (plugin scaffold)
- **Risk:** Same as P2-G — Chromium may be absent; graceful degradation to static analysis is required. `discern` depends on this more heavily than `do` (it is required, not optional) so the degradation message must be clear and actionable.
- **Note:** Use `.mcp.json` at plugin root — NOT inline `mcpServers` in `plugin.json` (open bug: [anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)).
- **Model tier:** Playwright tool invocations are deterministic; the a11y judgment agent (P3-E, Opus) interprets browser output — model tier lives there, not here
- **Checklist:**
  - [ ] Create `discern/.mcp.json` with Playwright MCP server config using `${CLAUDE_PLUGIN_ROOT}` paths
  - [ ] Verify plugin install makes Playwright MCP appear in `/mcp` output automatically, without user running `claude mcp add`
  - [ ] Dev server detection: check CLAUDE.md, prior context, then package.json scripts; ask user to confirm URL before proceeding
  - [ ] On dev server confirmed: navigate to URL, produce accessibility tree snapshot, pass to a11y agent (P3-E)
  - [ ] On dev server unavailable or Playwright MCP not connected: fall back to static analysis; note in report: "Live browser verification unavailable — static analysis only. To enable: start dev server and re-run."
  - [ ] Browser session is read-only: no clicks that mutate state (form submits, deletes) — navigation and inspection only
  - [ ] Verify: install `discern` with no prior MCP config; confirm Playwright MCP in `/mcp`; run `/discern:a11y` against a running app; confirm browser-based findings appear

### P3-B: Review Command

- **What:** Spawns specialist reviewer agents in parallel (code quality, security, accessibility) and produces a unified report with deduplicated findings, sorted by impact-to-effort ratio, leading with what is working well before surfacing issues.
- **Depends on:** P3-A
- **Risk:** Parallel agents may produce duplicate or contradictory findings. Deduplication must normalize finding descriptions before collapsing.
- **Note:** `discern` is evaluator-only. It must never propose or apply code changes.
- **Checklist:**
  - [ ] Port and rewrite `pragmatic-code-review` orchestration pattern from fotw source
  - [ ] Spawn three specialist agents in parallel: code quality, security (P3-D), accessibility (P3-E)
  - [ ] Each specialist agent: read-only tool access only (READ, GLOB, GREP, BASH) — no WRITE or EDIT; findings only; model tier: Opus (maximum accuracy — a missed finding is the failure mode)
  - [ ] Implement a deduplication synthesizer as a separate, tool-free step: receives structured output from all three agents, collapses near-duplicates, attributes to all sources; model tier: Haiku — no codebase access needed, pure aggregation of structured inputs
  - [ ] Sort findings by impact-to-effort ratio (HIGH impact, LOW effort first)
  - [ ] Lead report with "What's Working" section before surfacing issues
  - [ ] Save report to `${SKILMARILLION_SESSIONS_DIR:-.ai/sessions}/YYYY-MM-DD_<slug>/review-<target>.md`
  - [ ] Verify: run on a PR with known issues; confirm findings are deduplicated and no code edits are made

### P3-C: Clean Command

- **What:** Identifies and flags AI-generated noise in code — narrator comments ("Now we handle errors"), obvious comments (`// increment i`), hollow prose in docstrings — without altering logic or changing behavior.
- **Depends on:** P3-A
- **Risk:** Over-aggressive noise removal deletes genuinely useful comments. Confidence threshold must be high (>90%) before flagging.
- **Note:** `discern` evaluates; the clean command produces a findings list, not a diff. The user applies changes.
- **Model tier:** Sonnet — distinguishing "genuinely useful comment" from "AI noise" is nuanced; the >90% confidence gate prevents over-firing but the judgment itself requires more than pattern matching; read-only
- **Checklist:**
  - [ ] Port and rewrite `desloppify` from fotw source
  - [ ] Define noise categories: narrator comments, obvious comments, hollow prose, excessive hedging
  - [ ] Produce findings list with file:line references and suggested replacements
  - [ ] Confidence gate: only flag findings with >90% confidence of being noise
  - [ ] Verify: run on a file with deliberate AI slop; confirm noise flagged and signal-carrying comments retained

### P3-D: Security Command

- **What:** A security-focused review that produces only findings with >80% confidence of real exploitation potential — no theoretical concerns, no CWE-number fishing.
- **Depends on:** P3-A
- **Risk:** False positives erode trust in the command. The 80% confidence threshold must be enforced structurally (require exploitation chain before flagging).
- **Model tier:** Opus — a missed real vulnerability is the worst outcome; exploitation chain reasoning requires deep understanding of code paths, attack surfaces, and precondition chains; read-only tool access only (READ, GLOB, GREP, BASH)
- **Checklist:**
  - [ ] Port and rewrite `security-review` from fotw source
  - [ ] For each finding, require: vulnerability type, exploitation chain, affected code path, severity (CRITICAL/HIGH/MEDIUM)
  - [ ] Suppress any finding where exploitation chain is theoretical or requires unlikely preconditions
  - [ ] Cover OWASP Top 10 as baseline scan surface
  - [ ] Save findings as a section in the review report (P3-B) or as standalone `security-<target>.md`
  - [ ] Verify: run on code with a known SQLI vulnerability; confirm it is found. Run on clean code; confirm no false positives.

### P3-E: A11y Command

- **What:** An accessibility audit that produces findings mapped to WCAG 2.1/2.2 criteria with severity ratings (critical/serious/moderate/minor) and reproduction steps. When Playwright MCP is available (see P3-F) and a dev server is running, performs live browser WCAG verification against real DOM state; otherwise falls back to static code analysis.
- **Depends on:** P3-A, P3-F (Playwright MCP bundle — required for browser mode)
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

**Deliverable:** *Users can run `/discern:review` on any PR or file set and receive a parallel, deduplicated, prioritized report covering code quality, AI noise, security, and accessibility — with no code changes made by the plugin. The a11y command performs live browser WCAG verification against a running app when available, with clear static-analysis fallback.*

---

## Phase 4: Homepage — GitHub Pages

**Entry Criteria:** Phases 0–3 complete. All four plugins ship and produce real artifacts. At least one real spec and one real review report exist to use as excerpt material.
**Exit Criteria:** The site is live at the project's GitHub Pages URL, communicates the problem and solution without requiring the visitor to read the README, shows the four-plugin workflow visually, includes at least one real artifact excerpt, renders correctly on mobile and desktop, and achieves Lighthouse ≥ 90 on Performance, Accessibility, and Best Practices.

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

- **What:** The homepage's primary content: a clear statement of the problem (fragmented, inconsistent AI dev workflows), the solution (four coherent plugins), and a visual representation of the dream → draft → do → discern lifecycle with a one-line description and artifact output for each plugin.
- **Depends on:** P4-A
- **Risk:** The narrative risks being too abstract ("better AI workflows") without concrete specificity. Ground each plugin description in what artifact it produces — specs, ADRs, review reports — not just what it does.
- **Checklist:**
  - [ ] Write problem statement section: 2-3 sentences, no jargon, grounded in the user's frustration (not in architecture)
  - [ ] Write solution section: introduce the four plugins by name with a one-line description each
  - [ ] Build workflow visualization: dream → draft → do → discern as a visual sequence (CSS only, no JS library)
  - [ ] For each plugin node in the workflow, show: command invoked, artifact produced, example path
  - [ ] Add a primary CTA button linking to the GitHub repo

### P4-C: Artifact Excerpt Showcase

- **What:** At least one real artifact excerpt (e.g., 15–20 lines from an actual `/dream:sdd` spec or `/discern:review` report) displayed on the page so visitors can evaluate output quality concretely without installing anything.
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
- **Risk:** A project that ships an accessibility audit plugin (`discern:a11y`) with an inaccessible homepage is a credibility failure. This phase is not optional polish — it is a hard exit criterion.
- **Checklist:**
  - [ ] Run Lighthouse against the live Pages URL; confirm ≥ 90 on Performance, Accessibility, Best Practices
  - [ ] Fix any WCAG 2.1 AA failures (contrast, focus indicators, alt text, heading order)
  - [ ] Verify CTA button and any interactive elements are keyboard-navigable
  - [ ] Test at 375px (mobile) and 1280px (desktop) — no horizontal scroll, no clipped content
  - [ ] Confirm page load time < 2s on a standard connection (no unoptimized images or blocking scripts)
  - [ ] Run `/discern:a11y` against the site's HTML as a final gate before marking phase complete

**Deliverable:** *A publicly hosted GitHub Pages site is live, communicating the "why" of skilmarillion with strong visual design, showing the full four-plugin workflow with real artifact excerpts, and linking visitors directly to the repo for installation.*

---

## Cross-Cutting Concerns

- **Claude Code only** (NFR-004): All commands use `/plugin:command` syntax. No Cursor, Copilot, or Windsurf compatibility layer is required or planned.
- **Plugin independence** (NFR-003): Each plugin's README must document its standalone entry conditions. No plugin may fail due to a missing sibling. Test each plugin in a clean environment before marking its phase complete.
- **Workflow repeatability** (NFR-002): Artifact structure (sections, headings, file path) must be identical across runs of the same command on the same input. Content may vary; structure must not. Verify with two runs per command before shipping each phase.
- **Ease of use for new users** (NFR-001): A user with no prior knowledge must be able to invoke `/dream:sdd` and produce a meaningful artifact in their first session, without reading docs. Validate this by having a non-author user attempt it.
- **Source material is fotw** (Scope): All skills are rewritten from fotw source — not copied. Reference `~/src/github.com/TrevorEdris/fellowship-of-the-workflows`. Rewriting is a quality gate, not optional.
- **Distribution via GitHub** (Scope): No install script, GUI, or marketplace listing. Users clone/copy the repo. Each plugin's README covers installation.
- **Model tier defaults:** Each agent role carries a documented model tier annotation (Haiku / Sonnet / Opus). Haiku for deterministic, tool-free, or structured-output roles (commit formatting, review deduplication). Sonnet for roles requiring judgment or codebase context (triage, spec validation, coding, clean). Opus for accuracy-critical review roles where a missed finding has real consequences (code quality review, security, accessibility). Never assign a heavier model to a role that doesn't need it. These annotations are defaults — users may override per-role via `models.<role>` config.
- **Homepage quality gate** (NFR-005): The GitHub Pages site must achieve Lighthouse ≥ 90 on Performance, Accessibility, and Best Practices. A project that ships an accessibility audit plugin with an inaccessible homepage is a credibility failure. Run `/discern:a11y` against the site HTML before marking Phase 4 complete.
- **Bundled MCP servers** (FR-009): Plugins that require MCP tooling declare it in `.mcp.json` at the plugin root — never inline in `plugin.json` (open bug: [anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)). Use `${CLAUDE_PLUGIN_ROOT}` for all paths. Commands that depend on MCP tools must degrade gracefully when the tool is unavailable. Document the `npx playwright install chromium` step in each affected plugin's README.
- **Tool access constraints:** Reviewer and synthesizer agents are read-only (READ, GLOB, GREP, BASH only — no WRITE, EDIT). Synthesis/aggregation agents are tool-free. Only agents that produce code or artifacts (coder, spec writer, schema designer) have write access. Document tool access in each agent's definition.
- **Structured handoffs between agents:** Design artifacts from `draft` and specs from `dream` are injected as typed structured context into `do` agents — not re-read from disk per iteration. This avoids redundant file reads and keeps per-iteration token cost low.
- **Failure escalation over blind retries:** Any agent that fails after a bounded number of attempts must escalate (invoke a diagnostic step or accept-with-debt) rather than retry the same strategy. Blind retry loops are a token anti-pattern and a quality failure.

---

## Dependency Summary

| Dependency | Source | Status |
|---|---|---|
| fotw (fellowship-of-the-workflows) | `~/src/github.com/TrevorEdris/fellowship-of-the-workflows` | Available |
| incubyte/claude-plugins (reference architecture) | `~/src/github.com/incubyte/claude-plugins` | Available |
| Claude Code plugin spec (`plugin.json` format) | Claude Code CLI | Stable (no breaking changes anticipated) |
| GitHub Pages | Repository settings (branch or `/docs` directory) | Requires one-time manual enable in repo settings |

---

## Spec Index

| ID | Name | Status | Phase | Roadmap Ref |
|----|------|--------|-------|-------------|
| DREAM-001 | Plugin Scaffold | COMPLETE | 0 | P0-A |
| DREAM-002 | Task Triage Engine | IN PROGRESS | 0 | P0-B |
| DREAM-003 | SDD Command | PENDING | 0 | P0-C |
| DREAM-004 | PRD Command | PENDING | 0 | P0-D |
| DREAM-005 | Validate Command | PENDING | 0 | P0-E |
| DREAM-006 | Session Hooks | PENDING | 0 | P0-F |
| DREAM-007 | Deterministic Paths | PENDING | 0 | P0-G |
| DREAM-008 | Migrate Command | PENDING | 0 | P0-H |
| DRAFT-001 | Plugin Scaffold | PENDING | 1 | P1-A |
| DRAFT-002 | System Design Command | PENDING | 1 | P1-B |
| DRAFT-003 | API Design Command | PENDING | 1 | P1-C |
| DRAFT-004 | Schema Design Command | PENDING | 1 | P1-D |
| DRAFT-005 | Diagram Command | PENDING | 1 | P1-E |
| DO-001 | Plugin Scaffold | PENDING | 2 | P2-A |
| DO-002 | TDD Command | PENDING | 2 | P2-B |
| DO-003 | Debug Command | PENDING | 2 | P2-C |
| DO-004 | Refactor Command | PENDING | 2 | P2-D |
| DO-005 | Commit Command | PENDING | 2 | P2-E |
| DO-006 | PR Command | PENDING | 2 | P2-F |
| DO-007 | Playwright MCP Bundle (Optional) | PENDING | 2 | P2-G |
| DISCERN-001 | Plugin Scaffold | PENDING | 3 | P3-A |
| DISCERN-002 | Review Command | PENDING | 3 | P3-B |
| DISCERN-003 | Clean Command | PENDING | 3 | P3-C |
| DISCERN-004 | Security Command | PENDING | 3 | P3-D |
| DISCERN-005 | A11y Command | PENDING | 3 | P3-E |
| DISCERN-006 | Playwright MCP Bundle (Required) | PENDING | 3 | P3-F |
| SITE-001 | Site Scaffold | PENDING | 4 | P4-A |
| SITE-002 | Core Narrative & Workflow | PENDING | 4 | P4-B |
| SITE-003 | Artifact Excerpt Showcase | PENDING | 4 | P4-C |
| SITE-004 | Polish & Quality Gate | PENDING | 4 | P4-D |
