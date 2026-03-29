---
description: Interactive tour of impl plugin capabilities. Detects project state and recommends a starting command.
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

# /impl:help

Interactive, context-aware tour of the `impl` plugin. Scans the project for existing artifacts and in-progress work, walks through each command, and recommends a starting point.

---

## ON STARTUP — Project State Scan

Before presenting anything, scan for existing project artifacts to determine context.

### 1. Scan for specs

```
Glob: docs/*/specs/SPEC-*.md
```

Store the count and paths as `{specs}`.

### 2. Scan for active impl state files

```
Glob: .impl-state-*.local.yaml
```

Store the count and paths as `{impl_state_files}`.

### 3. Scan for active plan state files

```
Glob: .plan-state-*.local.yaml
```

Store the count and paths as `{plan_state_files}`.

### 4. Scan for staged changes

```
Bash: git diff --cached --stat
```

Store whether staged changes exist as `{has_staged_changes}`.

### 5. Detect upstream/downstream plugins

Check whether sibling lifecycle plugins are installed by looking for their manifests:

- `plan`: check for `plan/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `arch`: check for `arch/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins
- `review`: check for `review/.claude-plugin/plugin.json` relative to the skilmarillion root, or check installed plugins

Store availability as `{plugins_installed}`.

---

## GREETING — Adapt Based on Findings

Choose one greeting based on the scan results:

### Active TDD workflow (impl state files found)

> **Welcome back.** You have {N} active TDD workflow(s) in progress. You can resume with `/impl:tdd`, or let me walk you through all available commands.

### Specs exist but no active impl workflow

> **Welcome back.** Found {N} spec(s) ready for implementation. Let me show you what `impl` can do.

### Fresh project (no specs, no impl state)

> **Welcome to `/impl` — the implementation executor.**
>
> This project has no specs or active TDD workflows yet. Let me walk you through what `impl` can do.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

After displaying the greeting, ask:

> "Want the full tour, or jump to a specific command?"
>
> 1. Full tour
> 2. Jump to a command: `tdd` | `debug` | `refactor` | `commit` | `pr`

If "Full tour": proceed through all commands in order (COMMAND TOUR section).
If a specific command is named: jump directly to that command's section in the tour.

---

## COMMAND TOUR

Walk through each command one at a time. After each command description, ask the user how to proceed before moving to the next.

### Command 1: `/impl:tdd`

> **`/impl:tdd [spec-or-impl-details]`** — Slice-by-Slice TDD
>
> The main entry point. Takes a spec file (from `/plan:sdd`) or an impl-details file and drives RED-GREEN-REFACTOR for each vertical slice:
>
> - **RED**: Write a failing test for the next slice's acceptance criteria.
> - **GREEN**: Write the minimal production code to make it pass.
> - **REFACTOR**: Clean up without adding behavior. Full suite stays green.
>
> Tracks progress in `.impl-state-{slug}.local.yaml` so you can resume if interrupted.
>
> **Example:** `/impl:tdd docs/auth/specs/SPEC-001-oauth-flow.md`
>
> **Produces:** Committed, tested code with one commit per slice.

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `tdd`
> 3. Try `/impl:tdd` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 2.
- If "Tell me more": explain slice failure escalation (3-attempt limit, diagnostic step, ACCEPT_WITH_DEBT), state file resume behavior, and how specs are parsed into slices. Then re-ask.
- If "Try it now": if specs were found in the scan, suggest using one (e.g., "Try `/impl:tdd {spec-path}`"). Otherwise tell the user to create a spec first with `/plan:sdd`. End the tour.
- If "Skip to": ask which command and jump there.

### Command 2: `/impl:debug`

> **`/impl:debug [issue]`** — Structured Debugging
>
> Systematic root-cause analysis: reproduce the issue, isolate the cause, identify the fix, verify it works. Follows the "no brute-force debugging" rule — root cause first, fix second.
>
> **Example:** `/impl:debug "500 error on POST /api/users when email contains +"`
>
> **Produces:** Root cause analysis and verified fix.

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `debug`
> 3. Try `/impl:debug` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 3.
- If "Tell me more": explain the four-phase approach (reproduce, isolate, root cause, fix), the three-fix limit before escalation, and how it integrates with TDD (bug fix = failing test first). Then re-ask.
- If "Try it now": tell the user to run `/impl:debug` with a description of the issue. End the tour.
- If "Skip to": ask which command and jump there.

### Command 3: `/impl:refactor`

> **`/impl:refactor [target]`** — Phase-Gated Refactoring
>
> Safe refactoring with test verification between each step. Identifies code smells, proposes transformations, and verifies the test suite stays green after every change.
>
> **Example:** `/impl:refactor src/api/handlers/user.go`
>
> **Produces:** Refactored code with all tests passing.

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `refactor`
> 3. Try `/impl:refactor` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 4.
- If "Tell me more": explain smell detection, the transformation catalog (extract method, inline, rename, move), and how each step is verified against the test suite before proceeding. Then re-ask.
- If "Try it now": tell the user to run `/impl:refactor` with a file or module path. End the tour.
- If "Skip to": ask which command and jump there.

### Command 4: `/impl:commit`

> **`/impl:commit`** — Conventional Commit
>
> Generates a conventional commit message from staged changes. Detects scope from file paths and classifies the change type (feat, fix, refactor, test, docs, chore).
>
> **Example:** `/impl:commit`
>
> **Produces:** A well-formatted conventional commit.

Ask (using `AskUserQuestion`):

> "Next command, or want to try this one now?"
>
> 1. Next command
> 2. Tell me more about `commit`
> 3. Try `/impl:commit` now
> 4. Skip to a specific command

- If "Next command": proceed to Command 5.
- If "Tell me more": explain conventional commit format (`type(scope): description`), how scope is auto-detected from file paths, and how it integrates with the TDD workflow (one commit per green slice). Then re-ask.
- If "Try it now": if staged changes exist, suggest running `/impl:commit` now. Otherwise tell the user to stage changes first. End the tour.
- If "Skip to": ask which command and jump there.

### Command 5: `/impl:pr`

> **`/impl:pr [base]`** — PR Description Generator
>
> Generates a pull request description with acceptance criteria traceability. Links each AC back to the spec and reports test coverage per slice.
>
> **Example:** `/impl:pr main`
>
> **Produces:** PR opened against the target branch with structured description.

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

### If active impl state files exist

> **Recommendation:** You have active TDD workflows. Resume with `/impl:tdd` — it detects your in-progress state and offers to pick up where you left off.

### If specs exist but no active impl state

> **Recommendation:** You have specs ready for implementation. Start with `/impl:tdd {spec-path}` to begin slice-by-slice TDD.

If multiple specs were found, list them and suggest the user pick one:

> Found these specs:
> {list of spec paths}
>
> Pick one and run `/impl:tdd {path}`.

### If staged changes exist

> **Recommendation:** You have staged changes. Run `/impl:commit` to create a conventional commit, then `/impl:pr` to open a PR.

### If nothing exists (no specs, no state, no staged changes)

> **Recommendation:** No specs found. Create one first:
> - If `plan` is installed: run `/plan:sdd [task]` to generate a spec.
> - If `plan` is not installed: provide a spec or impl-details file directly to `/impl:tdd`.

---

## UPSTREAM / DOWNSTREAM PLUGIN REFERENCES

After the recommendation, reference upstream and downstream plugins with install hints if not present.

### Upstream: `plan`

#### If `plan` is installed

> **Upstream:** Specs come from `/plan:sdd`. Run `/plan:help` for a tour of planning capabilities.

#### If `plan` is NOT installed

> **Tip:** The `plan` plugin generates specs that feed into `/impl:tdd`. Install it for spec-driven planning:
> ```
> /plugin install plan@skilmarillion
> ```

### Downstream: `review`

#### If `review` is installed

> **Downstream:** After implementation, run `/review:review` to check code quality before merging.

#### If `review` is NOT installed

> **Tip:** The `review` plugin handles code review, security audits, and accessibility checks. Install it as your pre-merge quality gate:
> ```
> /plugin install review@skilmarillion
> ```

---

## CLOSING

> Run any command to get started. You can return here anytime with `/impl:help`.

---

## WHAT NOT TO DO

- Do NOT modify any files — this command is entirely read-only.
- Do NOT create state files — this is an informational tour only.
- Do NOT skip the project state scan — the greeting and recommendation depend on it.
- Do NOT present all commands at once — walk through them one at a time with navigation between each.
- Do NOT assume plugin availability — always check before referencing upstream/downstream plugins.
