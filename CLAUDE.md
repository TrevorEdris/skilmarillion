# Skilmarillion / Fellowship

## What This Repo Is

The `skilmarillion` marketplace, shipping a single plugin: **`fellowship`** — spec-driven development from discovery through TDD to review, as one cohesive command surface.

- **Marketplace:** `skilmarillion`
- **Plugin:** `fellowship` (this repo root)
- **Install:** `/plugin install fellowship@skilmarillion`

## Phase Vocabulary (Internal Metaphor)

```
Palantír (Discover)  →  Council (Plan)  →  Journey (Build)  →  Rivendell (Review)
     scout                  spec                TDD                findings
```

These are the mental stages the Fellowship travels through. Command names stay flat and functional — the metaphor is for framing, not routing.

## Repository Structure

```
.claude-plugin/
  plugin.json               # fellowship manifest (v0.1.0+)
  marketplace.json          # skilmarillion marketplace → single plugin
commands/                   # 7 flat commands
  init.md  plan.md  build.md  review.md  ship.md  status.md  help.md
agents/                     # specialist sub-agents (triage, spec-builder, reviewers, …)
skills/                     # reusable skills (artifact-paths, spec-format, tdd-cycle, …)
references/                 # templates and rubrics (prd-template, discovery-questions, …)
scripts/                    # validate.py, update-state.sh
hooks/                      # session lifecycle hooks
docs/planning/              # skilmarillion's own PRD + ROADMAP
test-fixtures/              # sample project for end-to-end testing
```

## The 7 Commands

| Command | Purpose | Model |
|---------|---------|-------|
| `/fellowship:init` | Bootstrap `.skilmarillion/projects/{slug}/` scaffolding | haiku |
| `/fellowship:plan` | PRD → roadmap → specs; ADR/API/schema/diagram via `--arch` | sonnet |
| `/fellowship:build` | Slice-by-slice TDD; `--debug` and `--refactor` modes | sonnet |
| `/fellowship:review` | Parallel code-quality / security / a11y; findings only | opus |
| `/fellowship:ship` | Conventional commit; `--pr` opens a PR | haiku |
| `/fellowship:status` | Read-only dashboard of active work | haiku |
| `/fellowship:help` | Context-aware tour; recommends a command from a task description | haiku |

## Core Conventions

### Output Paths

All artifacts land under the **target project's** git root at:

```
{target_project}/.skilmarillion/projects/{slug}/
  PRD.md                       # /fellowship:plan --prd
  ROADMAP.md                   # /fellowship:plan --roadmap
  PROJECT-STATE.yaml           # workflow state (sections: plan, impl, review)
  specs/SPEC-NNN-{slug}.md     # /fellowship:plan --specify
  adrs/NNN-{slug}.md           # /fellowship:plan --arch adr
  api/{name}-openapi.yaml      # /fellowship:plan --arch api
  schema/{name}-schema.sql     # /fellowship:plan --arch schema
  diagrams/{name}-{type}.md    # /fellowship:plan --arch diagram
  plans/PLAN-NNN-{slug}.md     # implementation plans
  reviews/review-{target}.md   # /fellowship:review
```

Slugs are confirmed with the user before first save (see `skills/artifact-paths.md`).

### Git Exclusion Policy

`.skilmarillion/` files are **never auto-staged or auto-committed**. The user decides whether to track them. `/fellowship:ship` ignores these paths unless explicitly asked.

### Model Tiering

Use the minimum model that handles the task reliably. Cost compounds across multi-agent workflows.

- **Haiku** — deterministic, structured output (commit formatting, state dashboards, review deduplication, routing)
- **Sonnet** — judgment, codebase context, design reasoning (spec authoring, TDD loops, planning)
- **Opus** — safety-critical roles where a miss has real consequences (security, accessibility, code quality)

### Agent Tool-Access Principle

Read-only roles get read-only tools. No agent holds Write/Edit unless it explicitly produces code or files. Constrained tool sets enforce role boundaries and keep context clean.

### TDD Discipline

`/fellowship:build` enforces **RED → GREEN → REFACTOR**. No production code before a failing test for any behavioral step. Config, docs, generated code, and infrastructure are exempt. After 3 failed attempts on a slice: diagnostic step → modified approach, sub-slice split, or ACCEPT_WITH_DEBT.

### Review Discipline

`/fellowship:review` is findings-only. Never modifies code. Every finding must be actionable and high-confidence (>80% for security). The user decides what to fix.

### Validation Gate

Specs, PRDs, and plans are scored 0–100 by `scripts/validate.py`. **PASS threshold: ≥70.** Draft threshold: 50. Never present artifacts below the threshold as finished.

## Build & Test

Python 3.10+ (stdlib only) required for the validator:

```bash
# Validate a spec, PRD, or plan
python scripts/validate.py <path> --verbose

# Validate with explicit type and JSON output
python scripts/validate.py <path> --type spec|prd|plan --json

# Draft mode (relaxed threshold: 50)
python scripts/validate.py <path> --draft
```

## Personality (Applies Across All Commands)

- Direct, brief, warm. One question at a time.
- "We" framing: "Let's spec this out." / "Let's get this green." / "Let's review this."
- When the user says "just start coding": "Got it — one quick question first: [single most important decision]."
- When findings are clean: "Clean run. No issues above threshold."
- When findings are serious: state them plainly without alarm.
- Celebrate phase transitions: "Spec confirmed. Architecture decided. Ready to build."

## Versioning

Semver on `.claude-plugin/plugin.json`:
- **patch** — bug fixes, doc updates
- **minor** — new commands, new flags, new artifacts
- **major** — breaking command/flag/artifact changes

## Roadmap Completion Rule

When implementing a roadmap item (DREAM-NNN / P0-X), the implementing PR must update `docs/planning/ROADMAP.md` to mark that item complete:
- Move from "In Progress" or "Not Started" to "Completed" with PR number
- Check checklist boxes
- Update "Last Updated" date

Do not merge a roadmap-item PR without this update.
