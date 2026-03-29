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

## Artifact Paths

Reports are saved to the active session directory:

```
${SKILMARILLION_SESSIONS_DIR:-.ai/sessions}/YYYY-MM-DD_<slug>/
  review-<target>.md              # /review:review output
  security-<target>.md            # /review:security output
  a11y-<target>.md                # /review:a11y output
  clean-<target>.md               # /review:clean output
```

## Workflow Integration

```
plan/  ->  docs/{feature}/specs/SPEC-NNN-{slug}.md
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
