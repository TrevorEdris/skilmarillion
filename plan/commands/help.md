---
description: Interactive tour of plan plugin capabilities. Detects project state and recommends a starting command.
argument-hint: ""
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - AskUserQuestion
  - ToolSearch
model: haiku
---

# /plan:help

Interactive, context-aware tour of the `plan` plugin. Scans the project for existing artifacts, walks through each command, and recommends a starting point.

---

## ON STARTUP — Project State Scan

Before presenting anything, scan for existing project artifacts to determine context.

### 1. Scan for specs

```
Glob: docs/*/specs/SPEC-*.md
```

Store the count and paths as `{specs}`.

### 2. Scan for active state files

```
Glob: .plan-state-*.local.yaml
```

Store the count and paths as `{state_files}`.

### 3. Scan for PRDs

```
Glob: docs/*/PRD.md
```

Store the count and paths as `{prds}`.

### 4. Scan for roadmaps

```
Glob: docs/*/ROADMAP.md
```

Store the count and paths as `{roadmaps}`.

### 5. Detect downstream plugins

Check whether sibling lifecycle plugins are installed by looking for their manifests:

- `impl`: check for `impl/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `arch`: check for `arch/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `review`: check for `review/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins

Store availability as `{plugins_installed}`.

---

## GREETING — Adapt Based on Findings

Choose one greeting based on the scan results:

### Fresh project (no specs, no PRDs, no state files)

> **Welcome to `/plan` — the spec-driven planning plugin.**
>
> This project has no specs, PRDs, or active workflows yet. Let me walk you through what `plan` can do.

### Existing artifacts (specs or PRDs found, no active state files)

> **Welcome back.** Found {N} spec(s) and {M} PRD(s) in this project. Let me show you what else `plan` can do.

### Active workflow (state files found)

> **Welcome back.** You have {N} active workflow(s) in progress. You can resume those with `/plan:specify`, or let me walk you through all available commands.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

After displaying the greeting, ask:

> "Want the full tour, or jump to a specific command?"
>
> 1. Full tour
> 2. Jump to a command: `specify` | `prd` | `validate` | `roadmap` | `migrate`

If "Full tour": proceed through all commands in order (COMMAND TOUR section).
If a specific command is named: jump directly to that command's section in the tour.

---

## COMMAND TOUR

Walk through each command one at a time. After each command description, ask the user how to proceed before moving to the next.

### Command 1: `/plan:specify`

> **`/plan:specify [roadmap-path]`** — Spec Generator
>
> Takes a ROADMAP and generates a SPEC for each milestone using parallel agents. Milestones are batched by dependency order — independent milestones are processed concurrently.
>
> - **TRIVIAL** milestones: Lightweight spec (Problem Statement, happy-path ACs, TDD Plan)
> - **SMALL** milestones: Spec with risk-scaled ACs, Architecture Recommendation, TDD Plan
> - **FEATURE** milestones: Full spec with vertical slices, Architecture Recommendation, TDD Plan
>
> **Example:** `/plan:specify docs/auth/ROADMAP.md`
>
> **Produces:** `docs/{feature}/specs/SPEC-{NNN}-{slug}.md` for each milestone

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `specify`
> 3. Try `/plan:specify` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 2.
- If "Tell me more": explain the parallel agent batching, dependency-aware ordering, and how milestone scope determines spec depth. Then re-ask.
- If "Try it now": if roadmaps were found in the scan, suggest using one. Otherwise tell the user to create a roadmap first with `/plan:roadmap`. End the tour.
- If "Skip to": ask which command and jump there.

### Command 2: `/plan:prd`

> **`/plan:prd [feature]`** — Product Requirements Document
>
> Produces a client-shareable PRD from a plain-language feature description. Use this when defining a new feature or epic before breaking it into specs.
>
> **Example:** `/plan:prd User authentication with OAuth2 and MFA`
>
> **Produces:** `docs/{feature}/PRD.md`

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `prd`
> 3. Try `/plan:prd` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 3.
- If "Tell me more": explain PRD structure (problem statement, user stories, requirements, success metrics) and how it feeds into `/plan:roadmap`. Then re-ask.
- If "Try it now": tell the user to run `/plan:prd` with their feature description. End the tour.
- If "Skip to": ask which command and jump there.

### Command 3: `/plan:validate`

> **`/plan:validate [path]`** — Document Validator
>
> Scores a spec, PRD, or plan document for structural completeness (0-100). PASS at 70 or above. Auto-detects document type. Supports `--draft` for a relaxed threshold of 50.
>
> **Example:** `/plan:validate docs/auth/specs/SPEC-001-oauth-flow.md`
>
> **Produces:** Score report with actionable findings (no file output).

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `validate`
> 3. Try `/plan:validate` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 4.
- If "Tell me more": explain the scoring rubric, the difference between errors and warnings, and how other commands auto-validate before saving. Then re-ask.
- If "Try it now": if specs or PRDs were found in the scan, suggest validating one of them. Otherwise tell the user to provide a path. End the tour.
- If "Skip to": ask which command and jump there.

### Command 4: `/plan:roadmap`

> **`/plan:roadmap [prd-path]`** — Roadmap Generator
>
> Decomposes an approved PRD into ordered, shippable milestones. Run `/plan:specify` on the roadmap to generate all specs.
>
> **Example:** `/plan:roadmap docs/auth/PRD.md`
>
> **Produces:** `docs/{feature}/ROADMAP.md`

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `roadmap`
> 3. Try `/plan:roadmap` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 5.
- If "Tell me more": explain how milestones are ordered by dependency, how `/plan:specify` generates all specs in parallel, and the PRD-to-roadmap-to-specify pipeline. Then re-ask.
- If "Try it now": if PRDs were found in the scan, suggest using one. Otherwise tell the user to create a PRD first with `/plan:prd`. End the tour.
- If "Skip to": ask which command and jump there.

### Command 5: `/plan:migrate`

> **`/plan:migrate [legacy] [target]`** — Migration Planner
>
> Produces a prioritized migration plan as independently shippable specs. Use when moving from one technology, framework, or architecture to another.
>
> **Example:** `/plan:migrate express fastify`
>
> **Produces:** Migration roadmap with ordered specs in `docs/{migration-slug}/`

Ask (using `AskUserQuestion`):

> "That covers all five commands. Ready for a recommendation, or have questions?"
>
> 1. Give me a recommendation
> 2. Go back to a command
> 3. I'm good — end tour

- If "Give me a recommendation": proceed to RECOMMENDATION section.
- If "Go back to a command": ask which and jump there.
- If "End tour": display the closing message and stop.

---

## RECOMMENDATION — Starting Command

Based on the project state scan, recommend the best starting command:

### If active state files exist

> **Recommendation:** You have active workflows. Resume with `/plan:specify` — it will detect your in-progress state and offer to pick up where you left off.

### If PRDs exist but no specs for those features

> **Recommendation:** You have PRDs but no specs yet. Run `/plan:roadmap {prd-path}` to break them into milestones, then `/plan:specify {roadmap-path}` to generate all specs.

### If specs exist (project has been through planning before)

> **Recommendation:** This project already has specs. If you have a new task, start with `/plan:prd` to define requirements. If you want to validate existing specs, run `/plan:validate`.

### If nothing exists (fresh project)

> **Recommendation:** Start with `/plan:prd [feature]` to define requirements, then `/plan:roadmap` to decompose into milestones, then `/plan:specify` to generate all specs.

---

## DOWNSTREAM PLUGIN REFERENCES

After the recommendation, if any downstream plugins are not installed, append:

### If `impl` is not installed

> **Tip:** The `impl` plugin handles implementation from specs. Install it when you are ready to build:
> ```
> /plugin install impl@skilmarillion
> ```

### If `arch` is not installed

> **Tip:** The `arch` plugin provides architecture design (ADRs, API specs, schema design). Install it for deeper design work:
> ```
> /plugin install arch@skilmarillion
> ```

### If `review` is not installed

> **Tip:** The `review` plugin handles code review, security audits, and accessibility checks. Install it when you have code to review:
> ```
> /plugin install review@skilmarillion
> ```

---

## CLOSING

> Run any command to get started. You can return here anytime with `/plan:help`.

---

## WHAT NOT TO DO

- Do NOT modify any files — this command is entirely read-only.
- Do NOT create state files — this is an informational tour only.
- Do NOT skip the project state scan — the greeting and recommendation depend on it.
- Do NOT present all commands at once — walk through them one at a time with navigation between each.
- Do NOT assume plugin availability — always check before referencing downstream plugins.
