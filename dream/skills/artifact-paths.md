---
name: artifact-paths
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, paths, artifacts]
---

# artifact-paths

Shared path resolution for all dream artifacts. Every command that saves an artifact references this skill instead of hardcoding paths.

---

## Project Root Resolution

Artifacts are always saved relative to the target project's git root — never relative to CWD, which may be outside any repo.

**Resolution chain** (use the first that succeeds):

1. **Git context** — If the conversation involves files inside a git repo, run `git rev-parse --show-toplevel` from any known file path to get the root.
2. **Project name interpretation** — If the user names a project (e.g., "working on skilmarillion", "the multi-app-platform repo"), search for a matching git repo:
   - `~/src/github.com/**/{name}`
   - `~/src/{name}`
   - Confirm the resolved path with the user before proceeding.
3. **Ask explicitly** — If no git repo can be determined: "Which project should these artifacts live in? Provide the repo path."

Cache the resolved root in the triage state file as `project_root`. Subsequent artifact saves in the same session reuse this value without re-prompting.

---

## Directory Structure

All paths below are relative to the resolved project root.

```
{project_root}/docs/{feature}/
  PRD.md                           # One per feature (/dream:prd output)
  ROADMAP.md                       # Colocated roadmap (epic decomposition or manual)
  specs/
    SPEC-{NNN}-{slug}.md           # Auto-incrementing (/dream:sdd output)
  plans/
    PLAN-{NNN}-{slug}.md           # Mirrors spec numbering (future /do output)
```

---

## Slug Algorithm

Canonical slug generation — used by all commands and the triage agent.

1. Lowercase the entire string
2. Replace spaces and special characters (`/`, `_`, `.`, `,`, `'`, `"`, `(`, `)`, etc.) with hyphens
3. Collapse consecutive hyphens into one
4. Truncate to **40 characters**
5. Strip trailing hyphens after truncation

**Examples:**
- "Add OAuth login" → `add-oauth-login`
- "Fix getUserProfile() null check" → `fix-getuserprofile-null-check`

---

## Feature Directory Resolution

Determines the `{feature}` segment of the path.

**Resolution chain** (use the first that succeeds):

1. **Explicit argument** — User provides `--feature add-oauth` or equivalent.
2. **Triage state** — Read `feature` from `.dream-state-{slug}.local.yaml` if the current session has an active triage state.
3. **Prompt user** — "Which feature does this belong to?" List existing `{project_root}/docs/*/` directories. User may select one or provide a new feature slug.

For `/dream:prd`, the PRD's feature name becomes the directory name. For `/dream:sdd`, the feature directory should already exist (created by a prior PRD) or be created if this is a standalone spec.

---

## Spec Numbering

Auto-incrementing, zero-padded to 3 digits.

1. List existing `SPEC-*.md` files in `{project_root}/docs/{feature}/specs/`
2. Next number = count + 1
3. Format: `SPEC-{NNN}-{slug}.md` (e.g., `SPEC-001-auth-flow.md`, `SPEC-002-token-refresh.md`)

If the directory does not exist yet, the next number is `001`.

---

## Slug Confirmation Protocol

Before saving any artifact, present the resolved path to the user for confirmation.

**First save in a session** — show the full absolute path so the user can verify the project root:
> Save to `/Users/you/src/github.com/org/repo/docs/add-oauth/specs/SPEC-001-auth-flow.md`?

**Subsequent saves** (same session, same project root) — abbreviate:
> Save to `docs/add-oauth/specs/SPEC-002-token-refresh.md`?

**User options:**
- Accept as-is
- Override the slug (free text → re-apply slug algorithm)
- Override the feature directory
- Correct the project root (triggers re-resolution and cache update)

---

## Collision Detection

Before saving, check if the target path already exists.

- If it exists: "File already exists at `{path}`. Overwrite, or provide a different slug?"
- User may overwrite or provide an alternative.

---

## Directory Creation

Before writing any artifact, create the target directory if it does not exist:

```bash
mkdir -p {project_root}/docs/{feature}/specs
mkdir -p {project_root}/docs/{feature}/plans
```

---

## Path Templates by Command

| Command | Artifact | Path |
|---------|----------|------|
| `/dream:prd` | PRD | `{project_root}/docs/{feature}/PRD.md` |
| `/dream:sdd` (FEATURE/SMALL) | Spec | `{project_root}/docs/{feature}/specs/SPEC-{NNN}-{slug}.md` |
| `/dream:sdd` (EPIC) | Roadmap | `{project_root}/docs/{feature}/ROADMAP.md` |
| `/do:tdd` (future) | Plan | `{project_root}/docs/{feature}/plans/PLAN-{NNN}-{slug}.md` |
