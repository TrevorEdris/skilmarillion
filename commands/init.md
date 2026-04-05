---
description: Bootstrap the .skilmarillion/projects/ scaffolding for a target project. Idempotent.
argument-hint: "[project-slug]"
allowed-tools:
  - Read
  - Write
  - Glob
  - Bash(mkdir:*)
  - Bash(ls:*)
  - Bash(pwd)
  - AskUserQuestion
  - Task
  - ToolSearch
model: haiku
---

# /fellowship:init

Bootstraps `.skilmarillion/projects/{slug}/` at the target project's git root. Creates scaffold directories and an initial `PROJECT-STATE.yaml`. **Idempotent** — safe to re-run, only creates what is missing, never overwrites.

---

## Flow

### 1. Determine the slug

- If `$ARGUMENTS` contains a slug, pass it through the `slug-namer` agent for normalization (or use verbatim if it already matches `[a-z0-9-]+`).
- Otherwise, ask the user for a feature description, then delegate to the `slug-namer` agent (see `${CLAUDE_PLUGIN_ROOT}/agents/slug-namer.md`) to generate the slug.

**ALWAYS confirm the slug with the user via `AskUserQuestion` before creating any files or directories.** Show the proposed slug and ask "Proposed slug: `{slug}`. Accept, or provide an alternative?" If the user provides an alternative, re-call `slug-namer` to normalize it and re-confirm. Never create files with an unconfirmed slug.

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Create the directory tree

Run (idempotent — `mkdir -p` won't error if dirs exist):

```bash
mkdir -p .skilmarillion/projects/{slug}/{specs,plans,adrs,reviews,diagrams,api,schema}
```

### 3. Create PROJECT-STATE.yaml (only if missing)

Check with `ls .skilmarillion/projects/{slug}/PROJECT-STATE.yaml` first. If it exists: skip. Never overwrite.

If missing, write:

```yaml
slug: {slug}
created: {YYYY-MM-DD}
# sections added by /fellowship:plan, /fellowship:build, /fellowship:review
```

### 4. Report

```
Scaffolded .skilmarillion/projects/{slug}/
  specs/  plans/  adrs/  reviews/  diagrams/  api/  schema/
  PROJECT-STATE.yaml

Next: /fellowship:plan to create a PRD, or /fellowship:plan --prd "[feature]" to skip straight to spec.
```

If the directory already existed: report which files/dirs were already present and which were created.

---

## GIT EXCLUSION

Remind the user (once per invocation):

> `.skilmarillion/` is local workflow state. Add it to `.gitignore` unless you specifically want to track specs, ADRs, or reviews. See `README.md` for recommended strategies.

Do NOT modify `.gitignore` automatically. The user decides.

---

## WHAT NOT TO DO

- Do NOT overwrite an existing `PROJECT-STATE.yaml`.
- Do NOT modify `.gitignore` automatically.
- Do NOT guess the slug silently — confirm with the user on first save.
- Do NOT create files outside `.skilmarillion/projects/{slug}/`.
