# PRD: Skilmarillion

**Version:** 1.0
**Date:** 2026-03-26
**Status:** Draft — Awaiting Approval

---

## Problem Statement

Claude Code users today have two unsatisfying options for AI-assisted development workflows. Fellowship-of-the-Workflows (fotw) offers 40+ skills across every domain imaginable, but the breadth comes at the cost of focus — skills vary widely in quality, there is no coherent workflow connecting them, and users must self-assemble a process from loosely related pieces. Incubyte's `claude-plugins` offers a tightly designed spec-driven development workflow (`bee/`) but is scoped narrowly to that single workflow and does not cover architecture design, git operations, or quality review.

Neither option serves the full development lifecycle. A new Claude Code user has no guided path from "I have an idea" to "I have merged, reviewed code." An experienced user has no single set of high-quality, coherent plugins they can trust to produce consistent, repeatable artifacts across every phase of their work.

Skilmarillion addresses this gap: a curated, published collection of four Claude Code plugins — `dream`, `draft`, `do`, `discern` — that together cover the complete development lifecycle from initial specification through final quality review. Each plugin is independently installable, high-quality, and produces deterministic artifacts. Together they form a workflow with clear entry conditions and exit artifacts at every phase boundary.

---

## User Personas

### Alex — New Claude Code User

- **Goals:**
  - Get productive with Claude Code quickly without needing to understand the full ecosystem
  - Follow a guided workflow that tells them what to do and when, rather than assembling their own from scratch
  - Produce artifacts (specs, PRs, review reports) that look professional without prior experience writing them
- **Pain Points:**
  - Overwhelmed by fotw's 40+ skills with no guidance on which to use or in what order
  - Produces inconsistent output — sometimes great, sometimes off-track — with no understanding of why
  - Has no mental model of what "done" looks like at each phase of AI-assisted development

### Morgan — Experienced Claude Code User

- **Goals:**
  - Use Claude Code with enough structure that AI behavior is predictable and repeatable across different features
  - Have specialist agents handle distinct phases without one agent's context bleeding into another's
  - Produce artifacts at each phase (spec, TDD plan, PR description, review report) that are consistent enough to share with teammates
- **Pain Points:**
  - Existing tools apply uniform process to all task sizes — a typo fix gets the same ceremony as a new feature
  - No separation between planning agents and coding agents; context from earlier phases pollutes later ones
  - Review is either manual or handled by the same generalist agent that wrote the code, reducing objectivity

### Casey — Team Lead Evaluating AI Tooling

- **Goals:**
  - Evaluate whether AI-assisted development can be introduced to their team without creating unpredictable, unreviewed output
  - Find tooling that produces reviewable artifacts at each phase, not just generated code
  - Ensure the workflow scales from simple bug fixes to multi-slice features without changing tools
- **Pain Points:**
  - Most AI coding tools are black boxes — hard to audit what decisions were made and why
  - No existing plugin collection produces consistent, shareable artifacts (specs, ADRs, review reports) that fit into a team's existing documentation practices
  - Concerned that AI-written code bypasses quality gates that would normally catch security and accessibility issues

---

## Functional Requirements

### FR-001: Spec-Driven Planning Plugin (`dream`)

**Description:** Users can invoke a planning workflow that triages a task by size and risk, gathers codebase context, produces testable acceptance criteria as a spec document, selects an architecture pattern, and generates a TDD plan — all before any code is written. For trivial tasks, the workflow short-circuits to a quick confirmation. For feature-scale tasks, it runs the full interview-driven process.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the planning command with a task description produces a spec file with testable acceptance criteria and vertical slices
- [ ] The workflow routes differently for trivial vs. feature-scale tasks without user configuration
- [ ] A spec produced by the planning workflow is sufficient input for the implementation plugin without additional clarification
- [ ] Users can invoke a standalone PRD command that produces a client-shareable PRD document
- [ ] Users can invoke a validate command against any spec, PRD, or plan document and receive a scored quality report
- [ ] Users can invoke a migrate command with two codebase paths and receive a prioritized migration plan where every unit is an independently shippable spec with testable ACs, ordered by coupling analysis and git hotspot data

---

### FR-002: Architecture & Design Plugin (`draft`)

**Description:** Users can invoke design commands for system architecture, API design, database schema, event-driven architecture, and diagram generation. Each command conducts a structured design session and produces a durable artifact (ADR, OpenAPI spec, schema diagram, C4 Mermaid diagram).

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the system design command produces an ADR and a C4 context diagram
- [ ] Invoking the API design command produces an OpenAPI 3.1 spec covering versioning, pagination, and error envelopes
- [ ] Invoking the schema design command produces a schema with a zero-downtime migration plan
- [ ] All design artifacts are saved to documented, predictable paths
- [ ] The plugin operates independently — it does not require `dream` to have run first

---

### FR-003: Implementation Plugin (`do`)

**Description:** Users can execute a TDD implementation cycle slice by slice, driven by a spec produced by `dream`. Each slice is implemented, tested, and verified before the next begins. Users can also run systematic debugging, refactoring, and generate conventional commits and PR descriptions from within the same plugin.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the TDD command with a spec path executes each slice in order, gating advancement on passing tests
- [ ] The debug command produces a root cause statement before proposing any fix
- [ ] The refactor command runs phase-gated (each step passes tests before the next begins)
- [ ] The commit command produces a conventional commit message from staged changes, detecting breaking changes automatically
- [ ] The PR command detects and follows `.github/PULL_REQUEST_TEMPLATE.md` when present

---

### FR-004: Review & Quality Plugin (`discern`)

**Description:** Users can invoke a full parallel code review, a desloppify pass, a security review, and an accessibility audit after a PR exists. Review findings are deduplicated, sorted by impact-to-effort ratio, and lead with what is working well before surfacing issues. The plugin evaluates; it does not modify code.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the review command spawns specialist reviewer agents in parallel and produces a unified report with deduplicated findings
- [ ] The clean command identifies and removes AI-generated noise (narrator comments, obvious comments, hollow prose) without altering logic
- [ ] The security command produces only findings with >80% confidence of real exploitation potential — no theoretical concerns
- [ ] The a11y command produces findings mapped to WCAG 2.1/2.2 criteria with severity ratings
- [ ] `discern` produces no code changes — findings only
- [ ] Review reports are saved to the active session directory (`$SKILMARILLION_SESSIONS_DIR/YYYY-MM-DD_<slug>/review-<target>.md`)

---

### FR-005: Adaptive Workflow by Task Size

**Description:** The planning and implementation plugins route differently based on assessed task size (TRIVIAL / SMALL / FEATURE / EPIC) and risk level (LOW / MODERATE / HIGH). A typo fix does not receive the same ceremony as a multi-slice feature.

**Priority:** Must

**Acceptance Criteria:**
- [ ] A trivial task (single-line fix, config change) completes in one round-trip without a spec document being produced
- [ ] A feature-scale task triggers the full spec → architecture → TDD plan workflow before any code is written
- [ ] Risk level influences the depth of acceptance criteria — HIGH risk tasks produce edge cases and failure modes; LOW risk tasks produce happy path only

---

### FR-006: Session Documentation via Hooks

**Description:** Users can configure session documentation hooks that automatically create a session directory and SESSION.md at the start of each session, and append to an INDEX.md at session end. The session directory path is configurable via environment variable, defaulting to `.ai/sessions`.

**Priority:** Should

**Acceptance Criteria:**
- [ ] `dream`'s README documents the exact `settings.json` hook configuration required
- [ ] The hook uses `${SKILMARILLION_SESSIONS_DIR:-.ai/sessions}` so users can redirect session docs to any directory (e.g., an Obsidian vault)
- [ ] A session start creates `YYYY-MM-DD_<slug>/SESSION.md` automatically without user action
- [ ] A session end appends a one-line entry to `INDEX.md`

---

### FR-007: Deterministic Artifact Paths

**Description:** Every plugin command that produces an artifact saves it to a documented, predictable path. Users and teammates can find any artifact without asking Claude where it was saved.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Specs are always saved to `docs/specs/[feature-name]-spec.md`
- [ ] PRDs are always saved to `docs/prds/[feature-name]-prd.md`
- [ ] ADRs are always saved to `docs/adrs/[NNN]-[title].md`
- [ ] Review reports are saved to the active session directory as `review-<target>.md`
- [ ] Session documents follow the path convention defined in FR-006

---

## Non-Functional Requirements

### NFR-001: Ease of Use for New Users

**Description:** A user with no prior knowledge of skilmarillion's workflow should be able to install one plugin and produce a meaningful artifact within their first session.

**Measurable Target:** New user can invoke `/dream:sdd` with a plain-language task description and receive a complete spec without reading documentation first.

---

### NFR-002: Workflow Repeatability

**Description:** Running the same command against the same input (codebase state + task description) should produce structurally identical artifacts — same sections, same format, same artifact paths — even if content varies.

**Measurable Target:** Artifact structure (sections, headings, file path) is identical across two runs of the same command on the same input. Content variation is acceptable; structural variation is not.

---

### NFR-003: Plugin Independence

**Description:** Each plugin must be independently installable and usable. A user who only installs `discern` can run code review without installing `dream`, `draft`, or `do`.

**Measurable Target:** Each plugin's README documents its standalone entry conditions. No plugin's commands fail due to a missing sibling plugin.

---

### NFR-004: Claude Code Compatibility

**Description:** All plugins target Claude Code only. No multi-tool translation layer is required.

**Measurable Target:** All commands invoke correctly using Claude Code's plugin command syntax (`/plugin:command`). No Cursor, Copilot, or Windsurf compatibility required.

---

## Scope Boundary

### In Scope
- Four plugins: `dream` (planning), `draft` (architecture), `do` (implementation), `discern` (review)
- Session documentation hooks (configurable path via env var)
- Spec, PRD, and plan validation command in `dream`
- Skills sourced and rewritten from fotw's VERY HIGH and HIGH quality material
- Published to the Claude Code community via GitHub

### Out of Scope
- CI/CD pipeline plugin — too implementation-specific; deferred
- Observability plugin — fotw source material is reference-only, not production-quality
- Incident management plugin — fotw source is 25 lines; not sourceable
- Learning / onboarding plugin — no strong fotw backing; revisit after core four ship
- Vendor-specific plugins (PagerDuty, Grafana, Better Stack) — narrow domain; defer
- Multi-tool support (Cursor, Copilot, Windsurf) — skilmarillion targets Claude Code only
- A GUI, marketplace listing, or install script — distribution is via GitHub clone/copy; tooling deferred

---

## Milestones / Phases

### Milestone 1: `dream` — Spec-Driven Planning

**Includes:** FR-001, FR-005, FR-006, FR-007 (spec/PRD paths)

**Deliverable:** Users can run `/dream:sdd` on any task and receive a spec with testable acceptance criteria, an architecture recommendation, and a TDD plan — all before writing any code.

**Depends on:** Nothing. First plugin to build.

---

### Milestone 2: `do` — Implementation

**Includes:** FR-003, FR-005, FR-007 (no artifact paths — do produces code, not docs)

**Deliverable:** Users can run `/do:tdd` against a dream-generated spec and execute the full slice-by-slice TDD cycle with quality gates, then commit and open a PR without leaving the plugin.

**Depends on:** Milestone 1 (dream-generated specs are the primary input)

---

### Milestone 3: `draft` — Architecture & Design

**Includes:** FR-002, FR-007 (ADR paths)

**Deliverable:** Users can run `/draft:api`, `/draft:schema`, `/draft:design`, or `/draft:diagram` and receive a production-ready design artifact saved to a predictable path.

**Depends on:** Neither Milestone 1 nor 2 — `draft` is independently usable. Build after `do` for sequencing convenience only.

---

### Milestone 4: `discern` — Review & Quality

**Includes:** FR-004

**Deliverable:** Users can run `/discern:review` on any PR or file set and receive a parallel, deduplicated, prioritised review report covering code quality, security, and accessibility.

**Depends on:** Milestone 2 (`do` produces the PRs that `discern` evaluates; useful to have both working together)

---

## Success Metrics

| Metric | Target | How to Measure |
|---|---|---|
| New user time-to-first-artifact | User produces a spec within first session with no prior knowledge | Self-reported in GitHub issues / discussions |
| Artifact structural consistency | Same command produces same structure on repeated runs | Manual spot-check across 5 runs per command |
| Plugin independence | Each plugin usable standalone | Install each plugin in isolation; verify all commands succeed |
| Workflow coverage | All four plugins cover dream → draft → do → discern end-to-end | Complete a feature from `/dream:sdd` to `/discern:review` with no gaps |
| Community adoption | Stars, forks, or reported usage from non-author users | GitHub metrics, 90 days post-publish |

---

## Dependencies

- **fotw (fellowship-of-the-workflows):** Source material for skills. Skills must be rewritten, not copied. Available now at `~/src/github.com/TrevorEdris/fellowship-of-the-workflows`.
- **incubyte/claude-plugins:** Reference architecture for plugin structure (`commands/`, `agents/`, `skills/`, `CLAUDE.md`, `plugin.json`). Available now at `~/src/github.com/incubyte/claude-plugins`.
- **Claude Code plugin spec:** The `.claude-plugin/plugin.json` manifest format must remain stable. No known breaking changes anticipated.

---

## Open Questions

| Question | Owner | Target Date |
|---|---|---|
| ~~Should `dream` include a `migrate` command?~~ | ~~TrevorEdris~~ | Resolved: yes, included in FR-001 as a Should |
| ~~Distribution mechanism~~ | ~~TrevorEdris~~ | Resolved: native Claude Code plugin system (`claude plugin marketplace add ...`) |
