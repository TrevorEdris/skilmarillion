---
description: Workflow state dashboard across all installed Skilmarillion plugins. Shows active specs, in-progress implementations, and pending reviews.
argument-hint: ""
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash(ls:*)
  - Bash(cat:*)
model: haiku
---

# /skil:status

Read-only workflow state dashboard. Reads state files from all installed plugins and presents a unified view of active work across the Skilmarillion lifecycle.

**This command is entirely read-only. Never create, modify, or delete any files.**

---

## ON STARTUP — Gather State

Run all scans in parallel, then present a unified report.

### 1. Detect installed plugins

Check for sibling plugin manifests relative to the skilmarillion root:

```
Glob: plan/.claude-plugin/plugin.json
Glob: arch/.claude-plugin/plugin.json
Glob: impl/.claude-plugin/plugin.json
Glob: review/.claude-plugin/plugin.json
```

Store results as `{installed_plugins}` — a list of which plugins are present.

### 2. Read project state files

```
Glob: .skilmarillion/projects/*/PROJECT-STATE.yaml
```

For each file found, read it and extract:

**Plan section** (under `plan:` key):
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
- Any fields present (slice progress, current step, etc.)
- File modification time

Store as `{impl_states}`.

### 4. Scan for artifacts

```
Glob: docs/*/specs/SPEC-*.md
Glob: docs/*/PRD.md
Glob: docs/*/ROADMAP.md
```

Count and store paths as `{specs}`, `{prds}`, `{roadmaps}`.

### 5. Scan for project session logs

```
Glob: .skilmarillion/projects/*/SESSION.md
```

Count recent sessions (modified in last 7 days) as `{recent_sessions}`.

---

## REPORT — Present Unified Dashboard

Format the output as a structured dashboard. Use the sections below in order, skipping any section that has no data.

### Header

> **Skilmarillion Status Dashboard**

### Installed Plugins

List each lifecycle plugin and its status:

```
Plugins:
  plan   ✓ installed
  arch   ✗ not installed
  impl   ✓ installed
  review ✗ not installed
```

Use `✓ installed` for detected plugins and `✗ not installed` for missing ones.

For missing plugins, append the install hint on the same line:

```
  arch   ✗ not installed  →  /plugin install arch@skilmarillion
```

### Active Workflows

For each plan state file found, display:

```
Active work:
  [{slug}] {feature}
    size: {size} | risk: {risk} | phase: {current_phase}
    spec: {spec_path or "not yet produced"}
```

If impl state files exist for the same slug, merge into the same entry:

```
  [{slug}] {feature}
    plan: {current_phase} | impl: {impl_current_step}
```

If no active workflows exist:

> No active workflows. Start one with `/plan:sdd [task]` or `/skil [task]`.

### Artifacts Summary

```
Artifacts:
  Specs:    {count} across {feature_count} feature(s)
  PRDs:     {count}
  Roadmaps: {count}
```

If no artifacts exist:

> No artifacts found. Run `/plan:sdd [task]` to create your first spec.

### Plugin-Specific Notes

For each installed plugin that has no state files and no artifacts:

> `plan` is installed but has no active work or artifacts.

For each missing plugin that would normally contribute state:

> `impl` is not installed — no implementation state available. Install with `/plugin install impl@skilmarillion`

> `review` is not installed — no review state available. Install with `/plugin install review@skilmarillion`

Only show notes for `arch`, `impl`, and `review` if they are missing. Do not show a missing-plugin note for `skil` itself.

### Recent Sessions

If recent sessions were found:

```
Recent sessions (last 7 days): {count}
```

If none:

> No recent sessions found.

---

## OUTPUT FORMAT

Present the entire dashboard as a single formatted message. Do not use `AskUserQuestion` — this is a one-shot status report with no interactivity.

Keep output concise. One line per state file entry. No padding paragraphs.

---

## WHAT NOT TO DO

- Do NOT modify any files — this command is entirely read-only.
- Do NOT create state files or artifacts.
- Do NOT write to any state file or session directory.
- Do NOT use interactive prompts — this is a one-shot report.
- Do NOT crash or error if a plugin is missing — gracefully report its absence.
- Do NOT attempt to parse state files with non-YAML tools — use `Read` or `Bash(cat:*)` and parse the YAML fields from the text.
- Do NOT show install hints for `plan` or `skil` — only for `arch`, `impl`, and `review`.
