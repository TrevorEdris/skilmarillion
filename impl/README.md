# impl — Implementation Executor Plugin

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`impl` takes a spec or impl-details file and drives the developer through slice-by-slice TDD, structured debugging, phase-gated refactoring, and clean conventional commits. It enforces RED-GREEN-REFACTOR at every step.

## Standalone Entry Conditions

`impl` works independently — no other Skilmarillion plugins are required.

**With a `plan`-generated spec:** Parses slices and acceptance criteria, generates a session-scoped IMPL_DETAILS.md, then executes slice-by-slice TDD.

**With an impl-details file:** Executes the steps directly.

**With neither:** Prompts the developer for what to build. Offers a lightweight impl-details outline, or suggests `plan` for full spec-driven workflow.

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install impl@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/impl:tdd [spec-or-impl-details]` | Slice-by-slice TDD execution. Main entry point. |
| `/impl:debug [issue]` | Structured debugging: reproduce, isolate, root cause, fix. |
| `/impl:refactor [target]` | Phase-gated refactoring with test verification between steps. |
| `/impl:commit` | Conventional commit from staged changes with scope detection. |
| `/impl:pr [base]` | PR description generation with AC traceability. |
| `/impl:help` | Interactive tour of impl capabilities. |

## Prerequisites (Optional)

### Playwright MCP

The `impl` plugin ships with an `.mcp.json` that configures the Playwright MCP server for browser-based acceptance criteria verification during TDD. This is **optional** — all commands work without it.

To enable browser verification:

```bash
npx playwright install chromium
```

When Playwright is available, `/impl:tdd` will automatically run browser-based AC checks after each slice reaches GREEN. When absent, it degrades silently.

## Artifact Paths

Implementation details are saved to:

```
.skilmarillion/projects/{slug}/impl/IMPL_DETAILS.md
```

All committed code lands on a feature branch with conventional commits.

## Workflow Integration

```
plan/  ->  .skilmarillion/projects/{slug}/specs/SPEC-NNN-{slug}.md
  |
  v
impl/  ->  committed branch + open PR
  |
  v
review/  ->  review report
```

`arch/` (architecture design) is optional. When `arch` artifacts exist (ADR, OpenAPI spec, schema), `impl` injects them as context during TDD execution.
