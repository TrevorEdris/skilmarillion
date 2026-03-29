# PRD: Skilmarillion

**Version:** 1.3
**Date:** 2026-03-29
**Status:** Draft — Awaiting Approval

---

## Problem Statement

Claude Code users today have two unsatisfying options for AI-assisted development workflows. Fellowship-of-the-Workflows (fotw) offers 40+ skills across every domain imaginable, but the breadth comes at the cost of focus — skills vary widely in quality, there is no coherent workflow connecting them, and users must self-assemble a process from loosely related pieces. Incubyte's `claude-plugins` offers a tightly designed spec-driven development workflow (`bee/`) but is scoped narrowly to that single workflow and does not cover architecture design, git operations, or quality review.

Neither option serves the full development lifecycle. A new Claude Code user has no guided path from "I have an idea" to "I have merged, reviewed code." An experienced user has no single set of high-quality, coherent plugins they can trust to produce consistent, repeatable artifacts across every phase of their work.

Skilmarillion addresses this gap: a curated, published collection of five Claude Code plugins — `skil` (router), `plan`, `arch`, `impl`, `review` — that together cover the complete development lifecycle from initial specification through final quality review. Each plugin is independently installable, high-quality, and produces deterministic artifacts. Together they form a workflow with clear entry conditions and exit artifacts at every phase boundary. [MODIFIED]

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
  - Discovers one plugin but has no guided path to learn about the others or the full lifecycle [ADDED]

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

### FR-001: Spec-Driven Planning Plugin (`plan`) [MODIFIED]

**Description:** Users can invoke a planning workflow that triages a task by size and risk, then routes to the appropriate planning depth. For trivial tasks, the workflow short-circuits to a quick confirmation. For small tasks (bug fixes, small features), the workflow runs a lightweight QRSPI cycle (Question → Research → Structure → Plan → Implement) and produces a session-scoped IMPL_DETAILS.md with target files, ordered steps, git strategy, and verification actions — no formal spec document. For feature-scale tasks, it runs the full interview-driven process and produces a durable SPEC.md with testable acceptance criteria, architecture recommendation, and TDD plan. [MODIFIED]

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the planning command with a FEATURE-scale task produces a spec file with testable acceptance criteria and vertical slices
- [ ] Invoking the planning command with a SMALL-scale task runs a QRSPI cycle and produces an IMPL_DETAILS.md in the active session directory with: target files, ordered implementation steps, risks, verification actions, and git strategy [ADDED]
- [ ] The workflow routes differently for trivial, small, feature, and epic tasks without user configuration [MODIFIED]
- [ ] A spec produced by the FEATURE workflow is sufficient input for the implementation plugin without additional clarification
- [ ] An impl details document produced by the SMALL workflow is sufficient input for the implementation plugin without additional clarification — `impl:tdd` accepts both spec and impl details files [ADDED]
- [ ] Users can invoke a standalone PRD command that produces a client-shareable PRD document
- [ ] Users can invoke a validate command against any spec, PRD, or plan document and receive a scored quality report
- [ ] Users can invoke a migrate command with two codebase paths and receive a prioritized migration plan where every unit is an independently shippable spec with testable ACs, ordered by coupling analysis and git hotspot data

---

### FR-002: Architecture & Design Plugin (`arch`) [MODIFIED]

**Description:** Users can invoke design commands for system architecture, API design, database schema, event-driven architecture, and diagram generation. Each command conducts a structured design session and produces a durable artifact (ADR, OpenAPI spec, schema diagram, C4 Mermaid diagram).

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the system design command produces an ADR and a C4 context diagram
- [ ] Invoking the API design command produces an OpenAPI 3.1 spec covering versioning, pagination, and error envelopes
- [ ] Invoking the schema design command produces a schema with a zero-downtime migration plan
- [ ] All design artifacts are saved to documented, predictable paths
- [ ] The plugin operates independently — it does not require `plan` to have run first

---

### FR-003: Implementation Plugin (`impl`) [MODIFIED]

**Description:** Users can execute a TDD implementation cycle driven by either a spec (FEATURE-scale, from `plan`) or an impl details document (SMALL-scale, from `plan`'s QRSPI mode). When given a spec, `impl` first generates a session-scoped IMPL_DETAILS.md translating the spec's ACs and slices into concrete implementation steps (target files, ordered steps, git strategy, verification actions), then executes slice by slice. When given impl details directly, it executes the steps as-is. Users can also run systematic debugging, refactoring, and generate conventional commits and PR descriptions from within the same plugin. [MODIFIED]

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the TDD command with a spec path generates a session-scoped IMPL_DETAILS.md from the spec, then executes each slice in order, gating advancement on passing tests [MODIFIED]
- [ ] Invoking the TDD command with an impl details path executes the steps directly without generating an additional document [ADDED]
- [ ] The session-scoped IMPL_DETAILS.md is saved to the active session directory (not `docs/`) and follows the QRSPI format: target files, ordered steps, risks, verification actions, git strategy [ADDED]
- [ ] When Playwright MCP is available and a dev server is running, the TDD command optionally verifies each slice's ACs in a live browser after GREEN — producing a pass/fail result per AC with screenshots on failure
- [ ] Browser verification in the TDD command is opt-in and non-blocking — if Playwright MCP is unavailable or no dev server is detected, the command proceeds with test-only verification without prompting
- [ ] The debug command produces a root cause statement before proposing any fix
- [ ] The refactor command runs phase-gated (each step passes tests before the next begins)
- [ ] The commit command produces a conventional commit message from staged changes, detecting breaking changes automatically
- [ ] The PR command detects and follows `.github/PULL_REQUEST_TEMPLATE.md` when present

---

### FR-004: Review & Quality Plugin (`review`) [MODIFIED]

**Description:** Users can invoke a full parallel code review, a desloppify pass, a security review, and an accessibility audit after a PR exists. Review findings are deduplicated, sorted by impact-to-effort ratio, and lead with what is working well before surfacing issues. The plugin evaluates; it does not modify code. The `review` plugin bundles Playwright MCP via `.mcp.json`, enabling live browser-based verification for the a11y command and optional browser-assisted review without requiring users to manually configure MCP servers.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Invoking the review command spawns specialist reviewer agents in parallel and produces a unified report with deduplicated findings
- [ ] The clean command identifies and removes AI-generated noise (narrator comments, obvious comments, hollow prose) without altering logic
- [ ] The security command produces only findings with >80% confidence of real exploitation potential — no theoretical concerns
- [ ] The a11y command produces findings mapped to WCAG 2.1/2.2 criteria with severity ratings
- [ ] When Playwright MCP is available (bundled via the plugin's `.mcp.json`), the a11y command performs live browser rendering — navigating to the running app, interacting with elements, and verifying WCAG criteria against real DOM state — rather than static code analysis alone
- [ ] The a11y command degrades gracefully when no dev server is running or Playwright MCP fails to connect — falls back to static analysis and notes the limitation in the report
- [ ] `review` produces no code changes — findings only
- [ ] Review reports are saved to the active session directory (`$SKILMARILLION_SESSIONS_DIR/YYYY-MM-DD_<slug>/review-<target>.md`)

---

### FR-005: Adaptive Workflow by Task Size [MODIFIED]

**Description:** The planning and implementation plugins route differently based on assessed task size (TRIVIAL / SMALL / FEATURE / EPIC) and risk level (LOW / MODERATE / HIGH). A typo fix does not receive the same ceremony as a multi-slice feature. The artifact type changes with scale: TRIVIAL produces no document, SMALL produces a session-scoped IMPL_DETAILS.md, FEATURE produces a durable SPEC.md, and EPIC decomposes into features first.

**Priority:** Must

**Acceptance Criteria:**
- [ ] A trivial task (single-line fix, config change) completes in one round-trip without any planning document being produced
- [ ] A small task (bug fix, 1-3 file change) runs QRSPI and produces an IMPL_DETAILS.md in the session directory — no spec, no formal ACs [MODIFIED]
- [ ] A feature-scale task triggers the full spec → architecture → TDD plan workflow before any code is written
- [ ] An epic-scale task decomposes into features via PRD → roadmap before speccing individual features
- [ ] Risk level influences planning depth — HIGH risk SMALL tasks may be promoted to FEATURE; HIGH risk FEATURE tasks produce edge cases and failure modes in ACs; LOW risk tasks produce happy path only [MODIFIED]
- [ ] `impl:tdd` accepts both spec files (from FEATURE workflow) and impl details files (from SMALL workflow) as input [ADDED]

---

### FR-006: Session Documentation via Hooks

**Description:** Users can configure session documentation hooks that automatically create a session directory and SESSION.md at the start of each session, and append to an INDEX.md at session end. The session directory path is configurable via environment variable, defaulting to `.ai/sessions`.

**Priority:** Should

**Acceptance Criteria:**
- [ ] `plan`'s README documents the exact `settings.json` hook configuration required [MODIFIED]
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

### FR-008: GitHub Pages Homepage

**Description:** A publicly hosted GitHub Pages site that showcases the "why" of skilmarillion — what problem it solves, who it's for, and what the plan → arch → impl → review workflow looks like end-to-end. The site has strong visual design (comparable in quality and impact to impeccable.style) and serves as the primary discovery surface for new users. It links directly to the GitHub repo for installation. [MODIFIED]

**Priority:** Should

**Acceptance Criteria:**
- [ ] The site is live at the project's GitHub Pages URL and loads without errors
- [ ] The homepage communicates the core problem (fragmented, inconsistent AI dev workflows) and the solution without requiring the visitor to read the README
- [ ] Each of the four lifecycle plugins (`plan`, `arch`, `impl`, `review`) is visually represented with a one-line description of what it does and what artifact it produces [MODIFIED]
- [ ] The `skil` meta-plugin is presented as the recommended starting point for new users [ADDED]
- [ ] The plan → arch → impl → review workflow is presented as a clear visual narrative (e.g., a flow, timeline, or step sequence) [MODIFIED]
- [ ] At least one real artifact excerpt is shown (e.g., a truncated spec or review report) so visitors can evaluate output quality concretely
- [ ] A primary call-to-action links to the GitHub repo (installation instructions)
- [ ] The site renders correctly on mobile and desktop viewports
- [ ] Page load time is under 2 seconds on a standard connection (no bloated JS frameworks unless justified)

---

### FR-009: Bundled MCP Servers via Plugin `.mcp.json`

**Description:** Plugins that require MCP tool access (e.g., Playwright for browser automation) bundle their MCP server configuration in a `.mcp.json` file at the plugin root. When a user installs the plugin, the MCP server starts automatically at session startup — no manual `claude mcp add` step required. This eliminates the single biggest adoption friction for browser-dependent features.

**Priority:** Must

**Acceptance Criteria:**
- [ ] The `review` plugin includes a `.mcp.json` that configures Playwright MCP with `${CLAUDE_PLUGIN_ROOT}` paths for any bundled server files [MODIFIED]
- [ ] Installing `review` via `claude plugin add` makes Playwright MCP tools available without additional user configuration [MODIFIED]
- [ ] The `impl` plugin includes an optional `.mcp.json` for Playwright MCP (used by browser-based AC verification in the TDD command when a dev server is running) [MODIFIED]
- [ ] Plugin MCP servers appear in `/mcp` output with plugin attribution
- [ ] If the bundled MCP server fails to start (e.g., missing system dependency like Chromium), the plugin commands that depend on it degrade gracefully with a clear diagnostic message and fallback behavior
- [ ] Plugin `.mcp.json` uses `${CLAUDE_PLUGIN_ROOT}` (not hardcoded paths) so the configuration is portable across machines

---

### FR-010: Workflow Router Meta-Plugin (`skil`) [ADDED]

**Description:** A lightweight meta-plugin that serves as the top-level entry point for the skilmarillion suite. It provides three capabilities: (1) a task router that triages a plain-language task description and delegates to the appropriate lifecycle plugin, (2) an interactive help tour that walks users through all available plugins and commands, and (3) a status dashboard that shows current workflow state across all installed plugins. `skil` is a separate plugin (not embedded in `plan`) so it remains available regardless of which lifecycle plugins are installed.

**Priority:** Must

**Acceptance Criteria:**
- [ ] `/skil [task description]` triages a task and routes to the appropriate plugin command (e.g., a planning task routes to `/plan:sdd`, a review request routes to `/review:review`)
- [ ] `/skil:help` launches an interactive, context-aware tour that detects which plugins are installed, what artifacts exist in the project, and walks the user through available commands one at a time
- [ ] `/skil:help` adapts its greeting based on project state — fresh project vs. existing artifacts vs. active workflow in progress
- [ ] `/skil:status` shows the current workflow state across all installed plugins — active specs, in-progress implementations, pending reviews — by reading each plugin's state files
- [ ] When `skil` detects a command that requires an uninstalled plugin, it displays the install command (e.g., "Run `/plugin install impl@skilmarillion` to enable implementation commands")
- [ ] `skil` has no MCP dependencies, no agents, and no write operations — it is read-only and delegates all work to lifecycle plugins

---

### FR-011: Per-Plugin Help Commands [ADDED]

**Description:** Each lifecycle plugin (`plan`, `arch`, `impl`, `review`) includes a `:help` command that provides an interactive, context-aware tour of that plugin's capabilities. Unlike `skil:help` which covers the full suite, per-plugin help commands go deeper into the specific plugin's commands, agents, artifacts, and typical workflows. They detect project state and tailor their guidance accordingly.

**Priority:** Should

**Acceptance Criteria:**
- [ ] Each lifecycle plugin exposes a `:help` command (e.g., `/plan:help`, `/arch:help`, `/impl:help`, `/review:help`)
- [ ] Each help command detects relevant project artifacts (e.g., `/plan:help` checks for existing specs and active dream states; `/review:help` checks for open PRs and existing review reports)
- [ ] Each help command walks through the plugin's commands one at a time using `AskUserQuestion`, allowing the user to skip ahead, dive deeper, or exit
- [ ] Each help command ends with a recommended starting command based on current project state
- [ ] Help commands are read-only — no artifacts produced, no state modified

---

### FR-012: Out-of-Order Execution Guards [ADDED]

**Description:** Each plugin command checks its preconditions before executing and provides clear guidance when preconditions are not met. Guards are informational, not blocking — they tell the user what's missing and how to get it, but allow the user to proceed if they choose. This prevents new users from accidentally running commands in the wrong order while preserving advanced users' ability to override.

**Priority:** Must

**Acceptance Criteria:**
- [ ] `/impl:tdd` without a spec path and without any specs in `docs/` displays: "No spec found. Run `/plan:sdd [task]` to create one, or provide a spec path as an argument."
- [ ] `/review:review` with no staged changes, no open PR, and no file path argument displays: "Nothing to review. Provide a file path, PR number, or stage changes first."
- [ ] When a command's output references a downstream plugin that is not installed, the output includes the install command (e.g., "Next step: `/impl:tdd docs/auth/specs/SPEC-001.md` — plugin not installed. Run `/plugin install impl@skilmarillion`")
- [ ] Guards use `AskUserQuestion` to offer choices: proceed anyway, run the prerequisite command, or cancel
- [ ] Guards do not block execution if the user explicitly chooses to proceed — the user always has final say

---

## Non-Functional Requirements

### NFR-001: Ease of Use for New Users [MODIFIED]

**Description:** A user with no prior knowledge of skilmarillion's workflow should be able to install `skil` and produce a meaningful artifact within their first session. The `skil:help` tour provides guided discovery of the full plugin suite without requiring the user to read documentation.

**Measurable Target:** New user can run `/skil:help` to discover available commands, then invoke `/plan:sdd` with a plain-language task description and receive a complete spec without reading documentation first.

---

### NFR-002: Workflow Repeatability

**Description:** Running the same command against the same input (codebase state + task description) should produce structurally identical artifacts — same sections, same format, same artifact paths — even if content varies.

**Measurable Target:** Artifact structure (sections, headings, file path) is identical across two runs of the same command on the same input. Content variation is acceptable; structural variation is not.

---

### NFR-003: Plugin Independence

**Description:** Each plugin must be independently installable and usable. A user who only installs `review` can run code review without installing `plan`, `arch`, or `impl`. When a command references a sibling plugin that is not installed, it provides a clear install hint rather than failing silently. [MODIFIED]

**Measurable Target:** Each plugin's README documents its standalone entry conditions. No plugin's commands fail due to a missing sibling plugin. Missing-sibling references produce actionable install hints.

---

### NFR-004: Claude Code Compatibility

**Description:** All plugins target Claude Code only. No multi-tool translation layer is required.

**Measurable Target:** All commands invoke correctly using Claude Code's plugin command syntax (`/plugin:command`). No Cursor, Copilot, or Windsurf compatibility required.

---

### NFR-005: Homepage Web Performance & Accessibility

**Description:** The GitHub Pages homepage must meet baseline web performance and accessibility standards so it does not undermine the credibility of a project whose `review` plugin runs accessibility audits. [MODIFIED]

**Measurable Target:** Lighthouse score ≥ 90 on Performance, Accessibility, and Best Practices. WCAG 2.1 AA compliance for all interactive elements.

---

### NFR-006: Command Discoverability [ADDED]

**Description:** A user should be able to discover every available command in the skilmarillion suite without leaving the CLI. The combination of `/skil:help` (full suite tour), per-plugin `:help` commands (deep dives), and out-of-order guards (contextual hints) forms a layered discoverability system that serves both new and experienced users.

**Measurable Target:** A new user who installs only `skil` can discover the names, purposes, and install commands for all four lifecycle plugins within 60 seconds via `/skil:help`.

---

## Scope Boundary

### In Scope
- Five plugins: `skil` (router/help), `plan` (planning), `arch` (architecture), `impl` (implementation), `review` (review) [MODIFIED]
- Bundled Playwright MCP via plugin `.mcp.json` for browser-based verification in `review` (required) and `impl` (optional) (FR-009) [MODIFIED]
- Session documentation hooks (configurable path via env var)
- Spec, PRD, and plan validation command in `plan` [MODIFIED]
- Per-plugin help commands and out-of-order execution guards (FR-011, FR-012) [ADDED]
- Skills sourced and rewritten from fotw's VERY HIGH and HIGH quality material
- Published to the Claude Code community via GitHub
- GitHub Pages homepage showcasing the full workflow with strong visual design (FR-008)

### Out of Scope
- CI/CD pipeline plugin — too implementation-specific; deferred
- Observability plugin — fotw source material is reference-only, not production-quality
- Incident management plugin — fotw source is 25 lines; not sourceable
- Learning / onboarding plugin — no strong fotw backing; revisit after core four ship
- Vendor-specific plugins (PagerDuty, Grafana, Better Stack) — narrow domain; defer
- Multi-tool support (Cursor, Copilot, Windsurf) — skilmarillion targets Claude Code only
- A marketplace listing or automated install script — distribution is via GitHub clone/copy; tooling deferred
- A full documentation site (multi-page) — the homepage is single-page; per-plugin READMEs cover reference docs

---

## Milestones / Phases

### Milestone 0: `skil` — Workflow Router [ADDED]

**Includes:** FR-010

**Deliverable:** Users can run `/skil:help` for an interactive tour of the full plugin suite, `/skil [task]` to be routed to the appropriate plugin, and `/skil:status` to see workflow state across all installed plugins.

**Depends on:** Nothing. Lightweight plugin with no agents or write operations. Can be built first or in parallel with Milestone 1. Should be available before any lifecycle plugin ships so new users have guided discovery from day one.

---

### Milestone 1: `plan` — Spec-Driven Planning [MODIFIED]

**Includes:** FR-001, FR-005, FR-006, FR-007 (spec/PRD paths), FR-011 (`plan:help`), FR-012 (guards)

**Deliverable:** Users can run `/plan:sdd` on any task and receive a spec with testable acceptance criteria, an architecture recommendation, and a TDD plan — all before writing any code. `/plan:help` provides an interactive tour of planning commands. Cross-plugin references include install hints for `impl`.

**Depends on:** Nothing. First lifecycle plugin to build. `skil` (Milestone 0) is recommended but not required.

---

### Milestone 2: `impl` — Implementation [MODIFIED]

**Includes:** FR-003, FR-005, FR-007, FR-009 (optional Playwright MCP for browser AC verification), FR-011 (`impl:help`), FR-012 (guards)

**Deliverable:** Users can run `/impl:tdd` against a plan-generated spec and execute the full slice-by-slice TDD cycle with quality gates, then commit and open a PR without leaving the plugin. Out-of-order guards warn when no spec is found and suggest `/plan:sdd`.

**Depends on:** Milestone 1 (plan-generated specs are the primary input)

---

### Milestone 3: `arch` — Architecture & Design [MODIFIED]

**Includes:** FR-002, FR-007 (ADR paths), FR-011 (`arch:help`), FR-012 (guards)

**Deliverable:** Users can run `/arch:api`, `/arch:schema`, `/arch:design`, or `/arch:diagram` and receive a production-ready design artifact saved to a predictable path.

**Depends on:** Neither Milestone 1 nor 2 — `arch` is independently usable. Build after `impl` for sequencing convenience only.

---

### Milestone 4: `review` — Review & Quality [MODIFIED]

**Includes:** FR-004, FR-009 (bundled Playwright MCP for live browser a11y and review), FR-011 (`review:help`), FR-012 (guards)

**Deliverable:** Users can run `/review:review` on any PR or file set and receive a parallel, deduplicated, prioritised review report covering code quality, security, and accessibility. The a11y command performs live browser WCAG verification when a dev server is running. Out-of-order guards inform when nothing is staged for review.

**Depends on:** Milestone 2 (`impl` produces the PRs that `review` evaluates; useful to have both working together)

---

### Milestone 5: Homepage — GitHub Pages [MODIFIED]

**Includes:** FR-008, NFR-005

**Deliverable:** A publicly hosted GitHub Pages site is live, communicating the "why" of skilmarillion with strong visual design, showing the full five-plugin suite and the plan → arch → impl → review lifecycle, and linking visitors directly to the repo for installation.

**Depends on:** Milestones 0–4 (the homepage showcases all five plugins; content and example artifacts require them to exist)

---

## Success Metrics

| Metric | Target | How to Measure |
|---|---|---|
| New user time-to-first-artifact | User produces a spec within first session starting from `/skil:help` with no prior knowledge [MODIFIED] | Self-reported in GitHub issues / discussions |
| Artifact structural consistency | Same command produces same structure on repeated runs | Manual spot-check across 5 runs per command |
| Plugin independence | Each plugin usable standalone | Install each plugin in isolation; verify all commands succeed |
| Workflow coverage | All five plugins cover plan → arch → impl → review end-to-end [MODIFIED] | Complete a feature from `/plan:sdd` to `/review:review` with no gaps |
| Command discoverability | New user discovers all commands via `/skil:help` without reading docs [ADDED] | Usability test: fresh user finds and describes all four lifecycle plugins within 60 seconds |
| Community adoption | Stars, forks, or reported usage from non-author users | GitHub metrics, 90 days post-publish |
| Homepage engagement | Visitors navigate from homepage to GitHub repo | GitHub traffic referrers, 90 days post-publish |

---

## Dependencies

- **fotw (fellowship-of-the-workflows):** Source material for skills. Skills must be rewritten, not copied. Available now at `~/src/github.com/TrevorEdris/fellowship-of-the-workflows`.
- **incubyte/claude-plugins:** Reference architecture for plugin structure (`commands/`, `agents/`, `skills/`, `CLAUDE.md`, `plugin.json`). Available now at `~/src/github.com/incubyte/claude-plugins`.
- **Claude Code plugin spec:** The `.claude-plugin/plugin.json` manifest format and `.mcp.json` plugin MCP bundling must remain stable. No known breaking changes anticipated. Note: inline `mcpServers` in `plugin.json` has a known parsing bug ([anthropics/claude-code#16143](https://github.com/anthropics/claude-code/issues/16143)); use `.mcp.json` at plugin root instead.
- **Playwright MCP:** Browser automation server bundled via `.mcp.json` in `review` (required) and `impl` (optional). Playwright must be installable via `npx playwright install chromium` or equivalent. If Chromium is not installed, commands degrade gracefully to static analysis. [MODIFIED]
- **GitHub Pages:** The repository must have GitHub Pages enabled (branch or `/docs` directory). No third-party hosting or build pipeline required — static HTML/CSS is sufficient.

---

## Open Questions

| Question | Owner | Target Date |
|---|---|---|
| ~~Should `dream` include a `migrate` command?~~ | ~~TrevorEdris~~ | Resolved: yes, included in FR-001 as a Should |
| ~~Distribution mechanism~~ | ~~TrevorEdris~~ | Resolved: native Claude Code plugin system (`claude plugin marketplace add ...`) |
| ~~Should users be able to BYOT (Bring Your Own Template) for the PRD format?~~ | ~~TrevorEdris~~ | Resolved: No for v1. PRD is a pipeline input to `prd-to-roadmap` and `plan:validate`; both require known structure. BYOT undermines NFR-002 (repeatability) and breaks validators/parsers. Defer to future milestone if demand emerges. |
| ~~Should `review` and `impl` bundle Playwright MCP via plugin `.mcp.json`?~~ | ~~TrevorEdris~~ | Resolved: Yes. Added as FR-009. `.mcp.json` at plugin root (not inline `plugin.json` due to anthropics/claude-code#16143). `review` bundles it as required; `impl` as optional. Graceful degradation when Chromium unavailable. |
| ~~Should plugins use poetic names (dream/draft/do/discern) or functional names?~~ | ~~TrevorEdris~~ | Resolved: Functional names (`plan`/`arch`/`impl`/`review`). Alliterative branding reserved for marketing/homepage. Functional names reduce cognitive load — a user should type what they mean without a decode step. |
| ~~Where should the `skil` meta-command live?~~ | ~~TrevorEdris~~ | Resolved: Separate lightweight plugin. Cannot embed in `plan` because users who install only `review` would lose access to the router and help tour. `skil` has no agents, no MCP deps, no write ops. |
| ~~What does `plan:sdd` produce for SMALL tasks — a spec or a plan?~~ | ~~TrevorEdris~~ | Resolved: SMALL tasks produce a session-scoped IMPL_DETAILS.md via QRSPI (Question → Research → Structure → Plan → Implement). FEATURE tasks produce a durable SPEC.md. `impl:tdd` accepts both formats. The SPEC is "what" (ACs, slices); the IMPL_DETAILS is "how" (files, steps, git strategy). For FEATURE tasks, `impl` generates IMPL_DETAILS.md from the SPEC before executing. |
