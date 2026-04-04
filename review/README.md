# review -- Review & Quality Plugin

Part of the [Skilmarillion](https://github.com/TrevorEdris/skilmarillion) workflow.

## What It Does

`review` spawns specialist reviewer agents in parallel (code quality, security, accessibility), deduplicates their findings, and produces a unified report sorted by impact-to-effort ratio. It evaluates code -- it never modifies it.

## Standalone Entry Conditions

`review` has no dependencies on other Skilmarillion plugins. Use it with or without `plan`, `arch`, or `impl` installed.

**Input:** A PR number, branch name, file path, or directory -- or nothing (`/review:review` will ask).
**Output:** A findings report saved to the session directory.

## Installation

```bash
/plugin marketplace add https://github.com/TrevorEdris/skilmarillion
/plugin install review@skilmarillion
```

## Commands

| Command | Purpose |
|---------|---------|
| `/review:review [target]` | Full parallel review (code quality + security + a11y). Main entry point. |
| `/review:security [target]` | Security-focused review only. >80% confidence threshold. |
| `/review:a11y [target]` | Accessibility audit (WCAG 2.1/2.2). Live browser when Playwright MCP available; static fallback. |
| `/review:clean [target]` | Detect and flag AI-generated noise in code comments and prose. |
| `/review:help` | Interactive tour of review capabilities. |

## Report Structure

1. **What's Working** -- Positive observations first
2. **Findings** -- Sorted by impact-to-effort ratio (HIGH impact, LOW effort first); each with category, severity, file:line, description, suggested action
3. **Summary** -- Counts by severity, overall assessment

## Prerequisites (Optional)

### Playwright MCP

The `review` plugin ships with a `.mcp.json` that configures the Playwright MCP server for live browser testing during accessibility audits. This is **optional** — all commands work without it, falling back to static analysis.

To enable live browser testing:

```bash
npx playwright install chromium
```

When Playwright is available, `/review:a11y` runs live browser tests. When absent, it degrades gracefully to static-only analysis and declares the mode in the report header.

## Artifact Paths

Reports are saved to the `.skilmarillion/` output directory:

```
.skilmarillion/projects/{slug}/reviews/
  review-{target}.md              # /review:review output
  security-{target}.md            # /review:security output
  a11y-{target}.md                # /review:a11y output
  clean-{target}.md               # /review:clean output
```

## Workflow Integration

```
plan/  ->  .skilmarillion/projects/{slug}/specs/SPEC-NNN-{slug}.md
   |
impl/  ->  committed branch + open PR
   |
review/  ->  findings report (no code changes)
```

`review` sits at the end of the lifecycle. It evaluates what `impl` produces. `plan` and `arch` are optional upstream plugins.

## Model Tiering

- **Specialist agents** (code quality, security, a11y): Opus -- a missed finding is the failure mode
- **Deduplication synthesizer**: Haiku -- pure aggregation of structured inputs, no codebase access needed
- **Clean command**: Sonnet -- distinguishing useful comments from AI noise requires nuance
- **Help command**: Haiku -- deterministic, read-only tour
