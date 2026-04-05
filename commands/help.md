---
description: Interactive tour of fellowship. Detects project state and recommends a starting command. Accepts a task description to classify and recommend.
argument-hint: "[task description | --phase plan|build|review|ship]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /fellowship:help

Interactive, context-aware tour of the **fellowship** plugin. Scans the current project for artifacts and state files, then recommends the right command to run next.

Three modes:
- **No argument** — full lifecycle tour
- **`--phase <name>`** — scoped tour of one phase (`plan`, `build`, `review`, `ship`)
- **Task description** — classify the task and **print a recommended command**. This command does NOT auto-run the recommendation — the user runs it themselves.

This command is read-only. Never modifies files.

---

## ON STARTUP — Scan Project State

Run all scans in parallel, then choose a greeting and tour path.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 1. Scan for artifacts

```
Glob: .skilmarillion/projects/*/PRD.md
Glob: .skilmarillion/projects/*/ROADMAP.md
Glob: .skilmarillion/projects/*/specs/SPEC-*.md
Glob: .skilmarillion/projects/*/adrs/*.md
Glob: .skilmarillion/projects/*/reviews/*.md
```

Store counts as `{prds}`, `{roadmaps}`, `{specs}`, `{adrs}`, `{review_reports}`.

### 2. Scan for active state files

```
Glob: .skilmarillion/projects/*/PROJECT-STATE.yaml
```

For each file, read it and detect which sections are present (`plan:`, `impl:`, `review:`). Store as `{active_states}`.

---

## MODE ROUTING

### Mode A — Task description (classify + recommend)

If `$ARGUMENTS` contains a task description (not a flag), classify intent by keyword match:

| Signal | Recommended Command |
|--------|---------------------|
| plan, spec, prd, roadmap, requirements, acceptance criteria, user story, scope, define | `/fellowship:plan` |
| architecture, adr, api design, schema, database, diagram, data model, endpoint, openapi, erd | `/fellowship:plan --arch <type>` |
| build, implement, tdd, write code, fix bug, debug, refactor, add feature, create endpoint | `/fellowship:build` |
| review, audit, security, accessibility, a11y, quality, lint, vulnerability, ai slop, clean | `/fellowship:review` |
| commit, pr, pull request, ship, merge, conventional commit | `/fellowship:ship` |

If ambiguous or none match, ask `AskUserQuestion`:

> "Which phase fits your task?"
> 1. Plan — define what to build (`/fellowship:plan`)
> 2. Build — implement with TDD (`/fellowship:build`)
> 3. Review — audit code quality (`/fellowship:review`)
> 4. Ship — commit + PR (`/fellowship:ship`)

**Output format** (recommendation only, no delegation):

> **Recommendation:** "{task}" → `/fellowship:{command}`
>
> Run:
> ```
> /fellowship:{command} {task}
> ```
>
> *(not auto-executing — your call)*

Stop. Do NOT invoke the target command.

### Mode B — `--phase <name>` flag

Jump straight to the matching phase section in the tour below. No greeting, no summary — just that one phase.

### Mode C — No argument (full tour)

Display greeting based on scan results, then walk all phases.

---

## GREETING (Full Tour Mode)

Choose based on scan results:

**Fresh project** (no artifacts, no state):
> **Welcome to fellowship.** No specs, PRDs, or active workflows yet. Let me show you around.

**Existing artifacts**:
> **Welcome back.** Found {specs} spec(s), {prds} PRD(s), {review_reports} review report(s). Here's the lay of the land.

**Active workflows**:
> **Welcome back.** You have active work in progress. Here's where you stand.

Then show the 7-command map:

```
init  →  plan  →  build  →  review  →  ship
                                status  |  help
```

Ask:
> "Full tour, or jump to a phase?"
> 1. Full tour
> 2. Jump to: plan | build | review | ship

---

## LIFECYCLE TOUR

Walk through each phase one at a time. After each, ask whether to continue.

### Phase 1 — `/fellowship:plan` (Council)

> **Plan — spec-driven planning**
>
> Turns a task description into a testable spec and TDD plan before any code is written.
>
> **Stages** (select via flags):
> - `--prd` — client-shareable Product Requirements Document
> - `--roadmap <prd-path>` — decompose an approved PRD into ordered milestones
> - `--specify <roadmap-path>` — generate SPEC files from a roadmap (parallel agents)
> - `--migrate <legacy> <target>` — prioritized migration plan
> - `--validate <path>` — score a PRD/spec/plan (0-100; PASS at ≥85 for all types)
> - `--arch <adr|api|schema|diagram>` — design-session artifacts
>
> **Default (no flag):** runs the guided PRD → ROADMAP → specs flow end to end.
>
> **Artifacts:** `.skilmarillion/projects/{slug}/{PRD.md | ROADMAP.md | specs/ | adrs/ | api/ | schema/ | diagrams/}`

Ask:
> "Continue to Build, jump elsewhere, or end the tour?"

### Phase 2 — `/fellowship:build` (Journey)

> **Build — slice-by-slice TDD execution**
>
> Takes a spec and drives RED → GREEN → REFACTOR, one slice at a time. Resumes from `PROJECT-STATE.yaml` when state is found.
>
> **Modes:**
> - (default) — TDD loop
> - `--debug <issue>` — structured debugging: reproduce → isolate → root cause → fix
> - `--refactor <target>` — phase-gated refactoring with tests between steps
>
> **Escalation:** after 3 failed attempts on a slice, diagnostic step → modified approach, sub-slice split, or ACCEPT_WITH_DEBT.

Ask:
> "Continue to Review, jump elsewhere, or end the tour?"

### Phase 3 — `/fellowship:review` (Rivendell)

> **Review — parallel quality gates, findings only**
>
> Spawns specialist reviewers in parallel, deduplicates findings, sorts by impact-to-effort. Never modifies code.
>
> **Filters:**
> - (default) — full review (code quality + security + a11y)
> - `--security` — security only (>80% confidence threshold)
> - `--a11y` — WCAG 2.1/2.2 (uses Playwright MCP when available)
> - `--clean` — AI-generated noise detection
>
> **Artifact:** `.skilmarillion/projects/{slug}/reviews/review-{target}.md`

Ask:
> "Continue to Ship, jump elsewhere, or end the tour?"

### Phase 4 — `/fellowship:ship`

> **Ship — conventional commit + PR**
>
> Generates a conventional commit from staged changes. Detects breaking changes, infers type and scope, asks for approval before committing.
>
> **Flags:**
> - (default) — commit only
> - `--pr` — push branch + open PR with AC traceability
> - `--breaking` — force BREAKING CHANGE footer
> - `--scope <scope>` — override auto-detected scope

Ask:
> "Ready for a recommended starting point?"

---

## RECOMMENDATION — Starting Point

Based on the project state scan, recommend the next move:

**Active state files exist** →
> **Recommendation:** You have active work. Run `/fellowship:status` to see where it stands, then resume with the matching command.

**PRDs exist, no specs for those features** →
> **Recommendation:** Run `/fellowship:plan --roadmap {prd-path}` to decompose the PRD into milestones, then `/fellowship:plan --specify {roadmap-path}`.

**Specs exist, no in-progress build** →
> **Recommendation:** Run `/fellowship:build {spec-path}` to start TDD execution.

**Fresh project, no artifacts** →
> **Recommendation:** Run `/fellowship:plan` to start the guided PRD → ROADMAP → specs flow, or `/fellowship:plan --prd "[feature description]"` to skip straight to a PRD.

---

## SUPPORTING COMMANDS

Always end the tour with:

> **Other commands:**
> - `/fellowship:init` — bootstrap `.skilmarillion/projects/{slug}/` scaffolding
> - `/fellowship:status` — read-only dashboard of active work
> - `/fellowship:help [task]` — classify a task and recommend a command
>
> Run `/fellowship:help --phase <name>` for a scoped tour of one phase.

---

## WHAT NOT TO DO

- Do NOT modify any files — this command is read-only.
- Do NOT auto-execute the recommended command in task-routing mode — print the recommendation and stop.
- Do NOT present all phases at once in full-tour mode — walk them one at a time with navigation.
- Do NOT omit the project-state scan — the recommendation depends on it.
