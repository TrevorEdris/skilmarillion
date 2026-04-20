---
description: TDD execution. Slice-by-slice RED/GREEN/REFACTOR from a spec, with wave-parallel, debug, and refactor modes.
argument-hint: "[wave N | spec W{N}{letter} | --debug <issue> | --refactor <target>] [--team]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - "Bash(${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh:*)"
  - AskUserQuestion
  - Task
  - ToolSearch
model: sonnet
---

# /fellowship:build

Turns a SPEC (or a wave of SPECs) into committed, tested code. Enforces RED → GREEN → REFACTOR per SPEC. Resumes from `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` when state is found.

> **The rule:** RED before GREEN. No production code without a failing test first.
>
> **Personality:** direct, brief, action-oriented. "We" framing: "Let's get this green." When tests fail: state the failure clearly, propose the fix. Celebrate slice completions: "W1a green. Moving to W1b."

---

## DISPATCH — Pick the Mode

Parse `$ARGUMENTS` for a leading keyword or flag:

| Invocation | Stage file | Purpose |
|------------|------------|---------|
| `wave {N}` | `references/build-stages/tdd.md` | Spawn parallel agents, one per wave-agent in Wave N.M (all W{N}* specs) |
| `spec W{N}{letter}` | `references/build-stages/tdd.md` | Single wave-agent TDD run (one SPEC) |
| *(no keyword — plain spec path)* | `references/build-stages/tdd.md` | Single SPEC TDD run (legacy / ad-hoc path) |
| `--debug` | `references/build-stages/debug.md` | Structured debugging: reproduce → isolate → root cause → fix |
| `--refactor` | `references/build-stages/refactor.md` | Phase-gated refactoring with test verification between steps |

The `--team` flag is orthogonal — it applies to `wave N` and forces Agent Teams spawning instead of the default Task subagents. See "Wave Concurrency" below.

**How to run a stage:**
1. `Read` the stage file from `${CLAUDE_PLUGIN_ROOT}/references/build-stages/{stage}.md`.
2. Follow its instructions exactly. Stage files are self-contained playbooks.
3. Pass through the remaining `$ARGUMENTS` (after the keyword/flag) as the stage input.

> **Deferred tool note:** Before calling `AskUserQuestion` or `TeamCreate` for the first time, call `ToolSearch` with query `"select:AskUserQuestion,TeamCreate"` to load the tool schemas.

---

## WAVE DISPATCH — `wave N`

Parse `N` as a wave identifier (supports `1`, `1.2`, or `Wave 1.2`).

1. **Resolve ROADMAP** via `artifact-resolver` (`artifact_type: roadmap`). Confirm with the user per `artifact-paths`.
2. **Parse the ROADMAP** to find the target wave:
   - `wave 1` → every `#### W1{letter}` block under Phase 1 (union of Wave 1.1, 1.2, …).
   - `wave 1.2` → only `### Wave 1.2`.
3. **Collision revalidation** — assert each SPEC's frontmatter `touches` is disjoint from every other targeted SPEC's `touches`. If any collision, STOP and report which SPECs conflict.
4. **Load each wave-agent's SPEC** from `specs/SPEC-W{N}{letter}-{slug}.md`. Require every SPEC to exist and to have passed validator PASS (score >= 85). If any SPEC is missing or below threshold, list the offending IDs and abort.
5. **Spawn concurrency** — see "Wave Concurrency" below.
6. **Merge barrier** — the wave closes when every spawned run reports green (tests pass + SPEC validator PASS + no unresolved `ACCEPT_WITH_DEBT` above the user's tolerance). Update `PROJECT-STATE.yaml` `impl.wave_agents_completed[]`.

### Wave Concurrency

| Mode | Trigger | Mechanism |
|------|---------|-----------|
| Task subagents (default) | `wave N` with no `--team` | Spawn one Task per wave-agent in a single message (parallel). Each Task follows `references/build-stages/tdd.md` against its assigned SPEC. |
| Agent Teams | `wave N --team` | Call `TeamCreate` with one teammate per wave-agent. Teammates coordinate via shared tasks and SendMessage per `teams/rules/team-conventions.md`. |

Within a wave-agent, TDD execution is sequential (per-step RED → GREEN → REFACTOR). Across wave-agents within the same wave, execution is fully parallel — wave-planner guarantees disjoint `touches` so two agents cannot step on each other's files.

---

## SPEC DISPATCH — `spec W{N}{letter}`

Single wave-agent path. Equivalent to the pre-wave behavior but keyed on the `W{N}{letter}` identifier.

1. **Resolve ROADMAP** (to find which project the SPEC belongs to) OR accept a direct SPEC path in `$ARGUMENTS`.
2. **Resolve SPEC** via `artifact-resolver` (`artifact_type: spec`, `query: W{N}{letter}`). The resolver's spec rule matches `W{id}` patterns (see `agents/artifact-resolver.md`).
3. **Confirm selection** with the user per `artifact-paths` flow.
4. **Final confirmation gate:**
   > "Building from `{slug}/SPEC-W{N}{letter}-{name}.md`. Proceed?"
5. Follow `references/build-stages/tdd.md` against the single SPEC.

---

## LEGACY / AD-HOC SPEC PATH

If `$ARGUMENTS` is a bare path (no `wave` or `spec W{id}` keyword):

1. **Check for in-progress state first.** If `$ARGUMENTS` is empty, glob `.skilmarillion/projects/*/PROJECT-STATE.yaml` for files with an `impl:` section. If any are found, offer to resume (see State Resumption below). Otherwise, proceed to step 2.

2. **Resolve via `artifact-resolver` agent.** Delegate to the agent (see `artifact-paths` skill § "Artifact Resolution") with `artifact_type: "spec"`, the raw `$ARGUMENTS` as `query`, and the resolved `project_root`.

3. **Confirm with the user** per the caller flow in the `artifact-paths` skill. For every `match_type` (`exact_path`, `single`, `multiple`, `none`, `all`), present candidates via `AskUserQuestion` and wait for explicit selection.

4. **Verify the selected file is a SPEC** — it must contain `## Acceptance Criteria` AND `## Ordered Implementation Steps`. If it does not, error with a pointer at the missing markers. (There is no separate PLAN artifact under the current model — the SPEC is the plan.)

5. **Final confirmation gate** — after selection and before reading the file:
   > "Building from `{slug}/SPEC-W{N}{letter}-{name}.md`. Proceed?"

### State Resumption

If `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` contains an `impl:` section, ask:

> "Found in-progress TDD state for '{slug}' (wave {current_wave}, agent {current_wave_agent}, step {current_step}/{total_steps}, phase: {phase}). Resume or start fresh?"
>
> Options: **Resume** / **Start fresh** / **Abort**

Then follow the full playbook in `references/build-stages/tdd.md`.

---

## STEP FAILURE ESCALATION

After **3 failed RED-GREEN attempts** on the same step, invoke the diagnostic step (detailed in `references/build-stages/tdd.md`). Output one of:

- **Modified Approach** — reset attempts, apply the modified approach, continue
- **Sub-Step Decomposition** — split the step into smaller sub-steps, continue
- **ACCEPT_WITH_DEBT** — record a structured gap, advance to the next step

Never loop indefinitely. ACCEPT_WITH_DEBT is a valid exit.

---

## STATE TRACKING

Write state to `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` under the `impl:` key as the TDD loop progresses. Required fields: `slug`, `current_wave` (e.g., `1.1`), `current_wave_agent` (e.g., `W1a`), `wave_agents_completed` (list), `current_step`, `total_steps`, `phase` (red|green|refactor), `attempts`, `gaps`.

Use `${CLAUDE_PLUGIN_ROOT}/scripts/update-state.sh` to modify the state file idempotently.

---

## POST-EXECUTION

After all targeted wave-agents complete (or are accepted with debt):

1. Run the full test suite as a final confirmation (distinct from per-step GREEN checks).
2. If any ACCEPT_WITH_DEBT gaps exist, display the gap summary.
3. Clean up the `impl:` section from `PROJECT-STATE.yaml` (delete the file if no other sections remain).
4. Breadcrumb:
   > "Wave {N.M} green ({count} wave-agents complete). Next: `/fellowship:review` to run quality checks, then `/fellowship:ship` to commit. When Wave {N.M} PRs are all green, run `/fellowship:build wave {next}`."

---

## GIT EXCLUSION

`.skilmarillion/` files are **never auto-staged or auto-committed** by this command. The user decides whether to track them.

---

## WHAT NOT TO DO

- Do NOT write production code before a failing test exists (behavioral steps).
- Do NOT proceed from RED to GREEN if the test failure is a syntax or import error — fix the test first.
- Do NOT skip the full suite run after GREEN — regressions must be caught immediately.
- Do NOT add behavior during REFACTOR phase.
- Do NOT retry the same failing approach more than 3 times — invoke the diagnostic step.
- Do NOT loop indefinitely on a failing step — ACCEPT_WITH_DEBT is a valid exit.
- Do NOT re-read arch artifacts per wave-agent — cache them at session start.
- Do NOT start Wave N.M+1 before every wave-agent in Wave N.M reports green.
- Do NOT spawn a wave-agent whose SPEC has `touches` colliding with another in-flight wave-agent's SPEC.
- Do NOT auto-commit `.skilmarillion/` files.
