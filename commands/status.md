---
description: Read-only workflow dashboard. Active projects, current phase, spec counts, in-progress TDD state.
argument-hint: ""
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - Bash(cat:*)
model: haiku
---

# /fellowship:status

Read-only workflow dashboard. Reads state files and artifact directories under `.skilmarillion/projects/` and presents a unified view of active work.

**This command is entirely read-only. Never create, modify, or delete any files.**

---

## ON STARTUP — Gather State

Run all scans in parallel, then present a unified report.

### 1. Read project state files

```
Glob: .skilmarillion/projects/*/PROJECT-STATE.yaml
```

For each file found, read it and extract:

**Plan section** (under `plan:` key, if present):
- `slug` (from directory name)
- `feature` field
- `size` field
- `risk` field
- `current_phase` field
- `spec_path` field (if present)
- File modification time (via `ls -l`)

Store as `{plan_states}`.

**Impl section** (under `impl:` key, if present):
- `slug` (from directory name)
- `current_slice`, `total_slices`, `phase` (red/green/refactor)
- `attempts` counter
- Any `gaps` entries (ACCEPT_WITH_DEBT records)
- File modification time

Store as `{impl_states}`.

**Review section** (under `review:` key, if present):
- `slug`, most recent review target, report path

Store as `{review_states}`.

### 2. Scan for artifacts

```
Glob: .skilmarillion/projects/*/PRD.md
Glob: .skilmarillion/projects/*/ROADMAP.md
Glob: .skilmarillion/projects/*/specs/SPEC-*.md
Glob: .skilmarillion/projects/*/adrs/*.md
Glob: .skilmarillion/projects/*/reviews/*.md
```

Count and store paths as `{prds}`, `{roadmaps}`, `{specs}`, `{adrs}`, `{reviews}`.

### 3. Scan for session logs

```
Glob: .skilmarillion/projects/*/SESSION.md
```

Count files modified in the last 7 days as `{recent_sessions}`.

---

## REPORT — Unified Dashboard

Format the output as a single structured message. Skip any section with no data.

### Header

> **Fellowship Status Dashboard**

### Active Workflows

For each project state file found, display:

```
[{slug}] {feature}
  plan:   size={size} | risk={risk} | phase={current_phase} | spec={spec_path or "pending"}
  impl:   slice={current_slice}/{total_slices} | phase={tdd_phase} | attempts={attempts}
  review: target={target} | report={report_path}
```

Only include the sub-lines that have matching sections in the state file. If a project only has a `plan:` section, only show the `plan:` line.

If no active workflows exist:
> No active workflows. Start one with `/fellowship:plan` or `/fellowship:help [task]`.

### Artifacts Summary

```
Artifacts:
  PRDs:            {count} across {project_count} project(s)
  Roadmaps:        {count}
  Specs:           {count}
  ADRs:            {count}
  Review reports:  {count}
```

If no artifacts exist:
> No artifacts found. Run `/fellowship:plan` to create your first PRD or spec.

### Recent Sessions

If recent sessions were found:
```
Recent sessions (last 7 days): {count}
```

If none:
> No recent sessions found.

### ACCEPT_WITH_DEBT Gaps (if any)

If any `impl:` state files contain `gaps:` entries:

```
Debt items (ACCEPT_WITH_DEBT):
  [{slug}] slice {slice_name}: {missing_behavior} (severity: {severity})
```

---

## OUTPUT FORMAT

Present the entire dashboard as a single formatted message. Do not use `AskUserQuestion` — this is a one-shot status report with no interactivity.

Keep output concise. One line per state entry. No padding.

---

## WHAT NOT TO DO

- Do NOT modify any files — this command is entirely read-only.
- Do NOT create state files or artifacts.
- Do NOT write to any state file or session directory.
- Do NOT use interactive prompts — this is a one-shot report.
- Do NOT attempt to parse state files with non-YAML tools — use `Read` or `Bash(cat:*)` and parse the YAML fields from the text.
