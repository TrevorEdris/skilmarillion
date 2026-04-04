---
description: Interactive tour of the full Skilmarillion plugin suite. Detects installed plugins and project state, walks through lifecycle phases.
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

# /skil:help

Interactive, context-aware tour of the entire Skilmarillion plugin suite. Detects which lifecycle plugins are installed, scans for project artifacts, and walks the user through each phase one at a time.

Unlike per-plugin `:help` commands (which go deep on a single plugin), `/skil:help` covers the full suite at a high level and directs users to per-plugin help for details.

---

## ON STARTUP -- Plugin Detection

Before presenting anything, detect which lifecycle plugins are installed and scan for project artifacts.

### 1. Detect installed plugins

Check for each plugin manifest relative to the skilmarillion root:

- `plan`: check for `plan/.claude-plugin/plugin.json`
- `arch`: check for `arch/.claude-plugin/plugin.json`
- `impl`: check for `impl/.claude-plugin/plugin.json`
- `review`: check for `review/.claude-plugin/plugin.json`

```
Glob: */.claude-plugin/plugin.json
```

Store results as `{installed_plugins}` (list of plugin names found).

### 2. Scan for specs

```
Glob: docs/*/specs/SPEC-*.md
```

Store count and paths as `{specs}`.

### 3. Scan for PRDs

```
Glob: docs/*/PRD.md
```

Store count and paths as `{prds}`.

### 4. Scan for active state files

```
Glob: .skilmarillion/projects/*/PROJECT-STATE.yaml
```

Store count and paths as `{plan_state_files}`.

For each file found, check if it contains an `impl:` section. If so, also count it as an impl state entry.

Store impl entries as `{impl_state_files}`.

### 5. Scan for review reports

```
Glob: .skilmarillion/projects/*/reviews/*.md
```

Store count as `{review_reports}`.

---

## GREETING -- Adapt Based on Findings

Choose one greeting based on the scan results:

### Fresh project (no artifacts, no state files)

> **Welcome to Skilmarillion -- your AI-powered development lifecycle.**
>
> This project has no specs, PRDs, or active workflows yet. Let me show you around.

### Existing artifacts (specs or PRDs found)

> **Welcome back.** Found {specs} spec(s) and {prds} PRD(s) in this project. Here is what is available across the suite.

### Active workflows (state files found)

> **Welcome back.** You have active workflows in progress. Here is a quick tour of the full suite and where you stand.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

After displaying the greeting, show the installed plugin summary:

> **Installed plugins:** {list of installed plugin names, or "only skil" if none}

Then ask:

> "Want the full tour of all lifecycle phases, or jump to a specific plugin?"
>
> 1. Full tour
> 2. Jump to a plugin: `plan` | `arch` | `impl` | `review`

If "Full tour": proceed through all phases in order (LIFECYCLE TOUR section).
If a specific plugin is named: jump directly to that plugin's section in the tour.

---

## LIFECYCLE TOUR

Walk through each lifecycle phase one at a time. After each phase description, ask the user how to proceed before moving to the next.

### Phase 1: `plan` -- Spec-Driven Planning

#### If `plan` is installed:

> **`plan` -- Spec-Driven Planning**
>
> Turns task descriptions into testable specs and TDD plans before any code is written.
>
> **Key commands:**
> - `/plan:sdd [task]` -- Main entry point. Classifies task size (TRIVIAL/SMALL/FEATURE/EPIC) and produces the right level of spec.
> - `/plan:prd [feature]` -- Produces a client-shareable Product Requirements Document.
> - `/plan:roadmap [prd-path]` -- Decomposes a PRD into ordered milestones.
> - `/plan:validate [path]` -- Scores a spec, PRD, or plan (0-100, PASS at 70+).
> - `/plan:migrate [legacy] [target]` -- Produces a prioritized migration plan.
> - `/plan:help` -- Deep-dive tour of plan commands.
>
> **Artifact produced:** `.skilmarillion/projects/{slug}/specs/SPEC-{NNN}-{slug}.md`
>
> Run `/plan:help` for a detailed walkthrough of each command.

#### If `plan` is NOT installed:

> **`plan` -- Spec-Driven Planning** *(not installed)*
>
> Turns task descriptions into testable specs and TDD plans. This is where most workflows start.
>
> **Install:**
> ```
> /plugin install plan@skilmarillion
> ```

Ask (using `AskUserQuestion`):

> "Next phase, or want to try a plan command now?"
>
> 1. Next phase
> 2. Try a plan command (if installed)
> 3. Skip to a specific plugin

- If "Next phase": proceed to Phase 2.
- If "Try a plan command": suggest `/plan:sdd` with a task description. End the tour.
- If "Skip to": ask which plugin and jump there.

### Phase 2: `arch` -- Architecture & Design

#### If `arch` is installed:

> **`arch` -- Architecture & Design**
>
> Produces architecture decision records (ADRs), API specs, schema designs, and system diagrams. Use after planning, before implementation.
>
> **Key commands:** Run `/arch:help` for the full command list.
>
> **Artifact produced:** `.skilmarillion/projects/{slug}/adrs/{NNN}-{slug}.md`

#### If `arch` is NOT installed:

> **`arch` -- Architecture & Design** *(not installed)*
>
> Produces ADRs, API specs, schema designs, and diagrams. Best for complex systems where design decisions need documentation.
>
> **Install:**
> ```
> /plugin install arch@skilmarillion
> ```

Ask (using `AskUserQuestion`):

> "Next phase?"
>
> 1. Next phase
> 2. Skip to a specific plugin

- If "Next phase": proceed to Phase 3.
- If "Skip to": ask which plugin and jump there.

### Phase 3: `impl` -- Implementation

#### If `impl` is installed:

> **`impl` -- Implementation Executor**
>
> Takes specs from `plan` and executes them with TDD, slice-by-slice. Handles debugging, refactoring, and commits.
>
> **Key commands:** Run `/impl:help` for the full command list.
>
> **Artifact produced:** Committed branch with passing tests and open PR.

#### If `impl` is NOT installed:

> **`impl` -- Implementation Executor** *(not installed)*
>
> Executes specs with TDD (RED-GREEN-REFACTOR), slice-by-slice. Install when you are ready to turn specs into code.
>
> **Install:**
> ```
> /plugin install impl@skilmarillion
> ```

Ask (using `AskUserQuestion`):

> "Next phase?"
>
> 1. Next phase
> 2. Skip to a specific plugin

- If "Next phase": proceed to Phase 4.
- If "Skip to": ask which plugin and jump there.

### Phase 4: `review` -- Review & Quality

#### If `review` is installed:

> **`review` -- Review & Quality Gates**
>
> Code review, security audits, accessibility checks, and quality gates before merge.
>
> **Key commands:** Run `/review:help` for the full command list.
>
> **Artifact produced:** Review report in the session directory.

#### If `review` is NOT installed:

> **`review` -- Review & Quality Gates** *(not installed)*
>
> Provides code review, security audits, and accessibility checks. Install as your pre-merge quality gate.
>
> **Install:**
> ```
> /plugin install review@skilmarillion
> ```

Ask (using `AskUserQuestion`):

> "That covers all four lifecycle phases. Ready for a recommendation?"
>
> 1. Give me a recommendation
> 2. Go back to a plugin
> 3. I am good -- end tour

- If "Give me a recommendation": proceed to RECOMMENDATION section.
- If "Go back": ask which plugin and jump there.
- If "End tour": display the closing message and stop.

---

## RECOMMENDATION -- Starting Point

Based on the project state scan, recommend the best starting point:

### If active plan state files exist

> **Recommendation:** You have active planning workflows. Resume with `/plan:sdd` -- it detects in-progress state and offers to pick up where you left off.

### If PRDs exist but no specs for those features

> **Recommendation:** You have PRDs but no specs yet. Run `/plan:roadmap {prd-path}` to break them into milestones, then `/plan:sdd` on each milestone.

### If specs exist (project has been through planning)

> **Recommendation:** This project already has specs. Run `/plan:sdd [task]` for a new task, or `/plan:validate` to check existing specs.

### If nothing exists (fresh project)

> **Recommendation:** Start with `/plan:sdd [task]` if you have a specific task. For a larger feature, start with `/plan:prd [feature]` to define requirements first.

### If `plan` is not installed

> **Recommendation:** Install the `plan` plugin first -- it is the starting point for most workflows:
> ```
> /plugin install plan@skilmarillion
> ```

---

## SKIL COMMANDS REMINDER

After the recommendation, remind the user about other `skil` commands:

> **Other `skil` commands:**
> - `/skil [task]` -- Describe any task and get routed to the right plugin command.
> - `/skil:status` -- See workflow state across all installed plugins.
> - `/skil:help` -- Return to this tour anytime.

---

## CLOSING

> That is the full Skilmarillion suite: **plan** -> **arch** -> **impl** -> **review**, with **skil** as your guide. Run any command to get started.

---

## WHAT NOT TO DO

- Do NOT modify any files -- this command is entirely read-only.
- Do NOT create state files -- this is an informational tour only.
- Do NOT skip the plugin detection scan -- the greeting, phase descriptions, and install hints depend on it.
- Do NOT present all phases at once -- walk through them one at a time with navigation between each.
- Do NOT assume plugin availability -- always check before showing commands vs. install hints.
- Do NOT go deep on individual commands -- direct users to per-plugin `:help` for details.
