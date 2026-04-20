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
  ROADMAP.md                       # Phase → Wave → Wave-Agent decomposition (/fellowship:plan --roadmap output)
  DISCOVERY.md                     # Codebase findings emitted during --roadmap (context-gatherer at scope=roadmap)
  PROJECT-STATE.yaml               # Unified state file (sections: plan, impl, review, waves)
  specs/
    SPEC-{wave_id}-{slug}.md       # One per wave-agent (/fellowship:plan --specify output)
                                   # wave_id format: W{N}{letter} — e.g., W1a, W2c
  adrs/
    {NNN}-{slug}.md                # Auto-incrementing (/fellowship:plan --arch adr output)
  api/
    {name}-openapi.yaml            # /fellowship:plan --arch api output
  schema/
    {name}-schema.sql              # /fellowship:plan --arch schema output
  diagrams/
    {name}-{type}.md               # /fellowship:plan --arch diagram output
  reviews/
    review-{target}.md             # /fellowship:review output
    security-{target}.md           # /fellowship:review --security output
    a11y-{target}.md               # /fellowship:review --a11y output
    clean-{target}.md              # /fellowship:review --clean output
```

The SPEC is the implementation plan. There is no separate `plans/` directory.

---

## Slug Generation

Slug generation is delegated to the **`slug-namer` agent** (haiku model). Do not apply string-munging rules inline — call the agent with the source text and treat the response as a **proposal that requires user confirmation**.

**Every slug MUST be confirmed with the user before it is used to create directories, save files, or write state.** This is non-negotiable. The agent produces candidates; the user approves them.

**How to call:**

```
Task: slug-namer agent
Input: { "text": "{free-text feature description}", "context": "{what the slug represents}" }
Output: single-line slug string (e.g., "add-oauth-login")
```

**Required post-call flow:**

1. Receive the slug proposal from the agent.
2. Ask the user via `AskUserQuestion`: "Proposed slug: `{slug}`. Accept, or provide an alternative?"
3. If the user supplies an alternative, re-call `slug-namer` to normalize it, then re-confirm.
4. Only commit the slug to disk or state after explicit user approval.

The agent handles:
- Case normalization and kebab-casing
- Semantic trimming (drops filler words like "the", "with", "for")
- camelCase splitting and acronym handling
- Punctuation, emoji, and noise stripping
- Length cap (~40 chars, 2–5 tokens)
- Empty/unparseable fallback to `unnamed`

See `agents/slug-namer.md` for the full contract and examples.

**When slug-namer is unavailable** (agent delegation not supported in the current context), fall back to this minimum-viable transform and flag it to the user: lowercase → replace non-alphanumeric with hyphens → collapse repeats → truncate to 40 → strip trailing hyphens.

---

## Artifact Resolution

When a command needs to **discover an existing artifact** (spec, PRD, roadmap, ADR, API, schema, diagram, or state file) from user input, delegate to the **`artifact-resolver` agent** (haiku model). Do not glob inline — call the agent, inspect its structured output, confirm with the user.

**How to call:**

```
Task: artifact-resolver agent
Input: {
  "artifact_type": "spec|prd|roadmap|state|adr|api|schema|diagram",
  "query": "{user input: free text, path, SPEC-W{N}{letter}, or empty}",
  "project_root": "{absolute path to target repo git root}"
}
Output: JSON with { match_type, candidates[], total_count }
```

**Required caller flow** — confirmation is mandatory for every `match_type`:

| `match_type` | Caller Action |
|--------------|---------------|
| `exact_path` | Confirm: "Using `{path}`. Proceed?" — **Proceed / Pick different / Cancel** |
| `single` | Confirm: "Found `{slug}/{filename}`. Use this one?" — **Yes / Pick different / Cancel** |
| `multiple` | Present top 5 candidates via `AskUserQuestion` with `{slug}/{filename}` labels; include "None of these / list all" option |
| `none` | Re-call the agent with `query: ""` to get `all` candidates; present via `AskUserQuestion` or abort |
| `all` | Present via `AskUserQuestion` grouped by slug; include "None — cancel" option |

**Never skip the confirmation gate.** The agent ranks and discovers; the user decides.

**Override handling:** If the user provides a different slug or path than the proposed one, re-call `artifact-resolver` with the new input to validate it exists, then re-confirm.

See `agents/artifact-resolver.md` for the full contract, glob patterns, and ranking algorithm.

---

## Spec Naming

Specs are named after the **wave-agent** they implement, not by auto-incremented integers.

**Format:** `SPEC-{wave_id}-{slug}.md`

Where `wave_id` is `W{N}{letter}` — `N` is the wave number (1-indexed, monotonic across phases), `letter` is `a..z` lowercase identifying the agent within that wave. The `wave_id` for each spec is assigned by `wave-planner` during `/fellowship:plan --roadmap` and recorded in `ROADMAP.md`.

Examples:
- `SPEC-W1a-refund-repo.md`
- `SPEC-W1b-refund-events.md`
- `SPEC-W2a-refund-api.md`

There is no separate plan artifact — the SPEC contains the full PLAN-grade implementation detail per `skills/spec-format.md`.

---

## Slug Confirmation Protocol

**Two confirmation gates — both are mandatory.** Never skip either.

**Gate 1: Slug proposal** (when a new slug is generated).
After the `slug-namer` agent returns a candidate, ask the user to approve the slug itself before resolving any path. This catches bad slugs early, before path resolution work.

**Gate 2: Path confirmation** (before writing any file).
After the slug is approved, present the resolved path to the user for confirmation.

**First save in a session** — show the full absolute path so the user can verify the project root:
> Save to `/Users/you/src/github.com/org/repo/.skilmarillion/projects/auth/add-oauth/specs/SPEC-001-auth-flow.md`?

**Subsequent saves** (same session, same project root) — abbreviate:
> Save to `.skilmarillion/projects/auth/add-oauth/specs/SPEC-002-token-refresh.md`?

**User options:**
- Accept as-is
- Override the slug (free text → re-delegate to `slug-namer` agent)
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
mkdir -p {project_root}/.skilmarillion/projects/{feature-slug}/reviews
```

---

## Path Templates by Command

| Command | Artifact | Path |
|---------|----------|------|
| `/fellowship:plan --prd` | PRD | `{project_root}/.skilmarillion/projects/{feature-slug}/PRD.md` |
| `/fellowship:plan --roadmap` | Roadmap | `{project_root}/.skilmarillion/projects/{feature-slug}/ROADMAP.md` |
| `/fellowship:plan --roadmap` | Discovery | `{project_root}/.skilmarillion/projects/{feature-slug}/DISCOVERY.md` |
| `/fellowship:plan --specify` | Specs | `{project_root}/.skilmarillion/projects/{feature-slug}/specs/SPEC-{wave_id}-{slug}.md` |
| `/fellowship:plan --arch adr` | ADRs | `{project_root}/.skilmarillion/projects/{feature-slug}/adrs/{NNN}-{slug}.md` |
| `/fellowship:plan --arch api` | OpenAPI | `{project_root}/.skilmarillion/projects/{feature-slug}/api/{name}-openapi.yaml` |
| `/fellowship:plan --arch schema` | Schema | `{project_root}/.skilmarillion/projects/{feature-slug}/schema/{name}-schema.sql` |
| `/fellowship:plan --arch diagram` | Diagrams | `{project_root}/.skilmarillion/projects/{feature-slug}/diagrams/{name}-{type}.md` |
| `/fellowship:build` | (no new artifact — implements code per SPEC; updates `PROJECT-STATE.yaml.waves`) |
| `/fellowship:review` | Review | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/review-{target}.md` |
| `/fellowship:review --security` | Security | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/security-{target}.md` |
| `/fellowship:review --a11y` | Accessibility | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/a11y-{target}.md` |
| `/fellowship:review --clean` | Clean code | `{project_root}/.skilmarillion/projects/{feature-slug}/reviews/clean-{target}.md` |
