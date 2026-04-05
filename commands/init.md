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
  - ToolSearch
model: haiku
---

# /fellowship:init

Bootstraps `.skilmarillion/projects/{slug}/` at the target project's git root. Creates scaffold directories and an initial `PROJECT-STATE.yaml`. **Idempotent** — safe to re-run, only creates what is missing, never overwrites.

---

## Flow

### 1. Determine the slug

- If `$ARGUMENTS` contains a slug, use it verbatim (after basic sanitization: lowercase, spaces → hyphens, drop anything that isn't `[a-z0-9-]`).
- Otherwise, load `${CLAUDE_PLUGIN_ROOT}/skills/artifact-paths.md` and follow its slug-derivation algorithm. Ask the user to confirm the derived slug via `AskUserQuestion` before creating any files.

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
