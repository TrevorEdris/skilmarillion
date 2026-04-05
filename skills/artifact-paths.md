---
name: artifact-paths
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, paths, artifacts]
---

# artifact-paths

Shared path resolution for all plan artifacts. Every command that saves an artifact references this skill instead of hardcoding paths.

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

Cache the resolved root in the project state file as `project_root`. Subsequent artifact saves in the same session reuse this value without re-prompting.

---

## Feature Directory Resolution

Determines the `{feature-slug}` segment of the path.

**Resolution chain** (use the first that succeeds):

1. **Explicit argument** — User provides `--feature add-oauth` or equivalent.
2. **Project state** — Read `feature` from `.skilmarillion/projects/{slug}/PROJECT-STATE.yaml` if the current session has an active project state.
3. **Prompt user** — "Which feature does this belong to?" List existing `{project_root}/.skilmarillion/projects/*/` directories. User may select one or provide a new feature slug.

For `/fellowship:plan --prd`, the PRD's feature name becomes the directory name. For `/fellowship:plan --specify`, the feature directory should already exist (created by a prior PRD/roadmap) or be created if needed.

---

## Directory Structure

All paths below are relative to the resolved project root.

```
{project_root}/.skilmarillion/projects/{feature-slug}/
  PRD.md                           # One per feature (/fellowship:plan --prd output)
  ROADMAP.md                       # Colocated roadmap (epic decomposition or manual)
  PROJECT-STATE.yaml               # Unified state file (replaces .plan-state-* and .impl-state-*)
  specs/
    SPEC-{NNN}-{slug}.md           # Auto-incrementing (/fellowship:plan --specify output)
  adrs/
    {NNN}-{slug}.md                # Auto-incrementing (/fellowship:plan --arch adr output)
  api/
    {name}-openapi.yaml            # /fellowship:plan --arch api output
  schema/
    {name}-schema.sql              # /fellowship:plan --arch schema output
  diagrams/
    {name}-{type}.md               # /fellowship:plan --arch diagram output
  impl/
    IMPL_DETAILS.md                # /fellowship:build output (generated from spec)
  reviews/
    review-{target}.md             # /fellowship:review output
    security-{target}.md           # /fellowship:review --security output
    a11y-{target}.md               # /fellowship:review --a11y output
    clean-{target}.md              # /fellowship:review --clean output
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

## Spec Numbering

Auto-incrementing, zero-padded to 3 digits.

1. List existing `SPEC-*.md` files in `{project_root}/.skilmarillion/projects/{feature-slug}/specs/`
2. Next number = count + 1
3. Format: `SPEC-{NNN}-{slug}.md` (e.g., `SPEC-001-auth-flow.md`, `SPEC-002-token-refresh.md`)

If the directory does not exist yet, the next number is `001`.

---

## Slug Confirmation Protocol

Before saving any artifact, present the resolved path to the user for confirmation.

**First save in a session** — show the full absolute path so the user can verify the project root:
> Save to `/Users/you/src/github.com/org/repo/.skilmarillion/projects/auth/add-oauth/specs/SPEC-001-auth-flow.md`?

**Subsequent saves** (same session, same project root) — abbreviate:
> Save to `.skilmarillion/projects/auth/add-oauth/specs/SPEC-002-token-refresh.md`?

**User options:**
- Accept as-is
- Override the slug (free text → re-apply slug algorithm)
- Override the feature directory
- Override the domain
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
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/specs
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/adrs
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/api
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/schema
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/diagrams
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/impl
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/reviews
```

---

## Path Templates by Command

| Command | Artifact | Path |
|---------|----------|------|
| `/fellowship:plan --prd` | PRD | `{project_root}/.skilmarillion/projects/{feature-slug}/PRD.md` |
| `/fellowship:plan --specify` | Specs | `{project_root}/.skilmarillion/projects/{feature-slug}/specs/SPEC-{NNN}-{slug}.md` |
| `/fellowship:plan --roadmap` | Roadmap | `{project_root}/.skilmarillion/projects/{feature-slug}/ROADMAP.md` |
| `/fellowship:plan --arch adr` | ADRs | `{project_root}/.skilmarillion/projects/{feature-slug}/adrs/{NNN}-{slug}.md` |
| `/fellowship:plan --arch api` | OpenAPI | `{project_root}/.skilmarillion/projects/{feature-slug}/api/{name}-openapi.yaml` |
| `/fellowship:plan --arch schema` | Schema | `{project_root}/.skilmarillion/projects/{feature-slug}/schema/{name}-schema.sql` |
| `/fellowship:plan --arch diagram` | Diagrams | `{project_root}/.skilmarillion/projects/{feature-slug}/diagrams/{name}-{type}.md` |
| `/fellowship:build` | Impl details | `{project_root}/.skilmarillion/projects/{feature-slug}/impl/IMPL_DETAILS.md` |
| `/fellowship:review` | Review | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/review-{target}.md` |
| `/fellowship:review --security` | Security | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/security-{target}.md` |
| `/fellowship:review --a11y` | Accessibility | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/a11y-{target}.md` |
| `/fellowship:review --clean` | Clean code | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/clean-{target}.md` |
