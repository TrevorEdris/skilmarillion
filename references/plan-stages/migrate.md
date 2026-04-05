# /fellowship:plan --migrate

Produce a prioritized migration plan where every unit is an independently shippable spec with testable acceptance criteria. Units are ordered by coupling analysis (high fan-in modules migrate last) and git hotspot data (frequently changed files migrate early).

---

## Flow

### 1. Input Resolution

Resolve the legacy and target codebase paths:

- **Both arguments provided** — Use the first argument as `{legacy_path}` and the second as `{target_path}`. Verify both resolve to directories containing a git repo (`git rev-parse --show-toplevel` from each).
- **One argument provided** — Treat it as `{legacy_path}`. Ask the user for `{target_path}`: "Where is the target codebase? Provide the repo path."
- **No arguments** — Ask the user for both paths:
  > "Which codebase are we migrating from? Provide the legacy repo path."
  Then:
  > "Where is the target codebase? Provide the target repo path."

Validate both paths:

```bash
git -C {legacy_path} rev-parse --show-toplevel
git -C {target_path} rev-parse --show-toplevel
```

If either fails, report the error and ask the user to correct the path.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Migration Slug

Derive a migration slug that identifies this migration:

1. Extract the repo names from both paths (last path segment, or git remote origin name if available).
2. Combine as `{legacy-name}-to-{target-name}` (e.g., `legacy-api-to-platform-v2`).
3. Apply the canonical slug algorithm from `artifact-paths` skill (lowercase, hyphens, truncate to 40 chars).
4. Confirm with the user: "Migration slug: `{slug}`. Accept or override?"

### 3. Codebase Survey

Scan the legacy codebase to build a module inventory:

1. **Identify top-level modules** — Scan directory structure to find packages, modules, or major directories. Use language-appropriate heuristics:
   - Go: directories with `.go` files
   - Python: directories with `__init__.py`
   - TypeScript/JavaScript: directories with `index.ts`/`index.js` or `package.json`
   - Java: `src/main/java/**` package directories
   - Generic fallback: top-level directories under `src/`, `lib/`, `app/`, `pkg/`

2. **Count files per module** — For each module, count source files (exclude tests, vendor, node_modules, generated code).

3. **Identify entry points** — Find `main` functions, HTTP route registrations, CLI command registrations, or equivalent. These are the roots of the dependency graph.

Present the module inventory to the user:

> "Found {N} modules in the legacy codebase:"
> - `{module-name}` — {file-count} files
> - ...
>
> "Does this look right? Any modules to exclude from migration?"

### 4. Coupling Analysis

For each module, measure **fan-in** (how many other modules depend on it) and **fan-out** (how many other modules it depends on).

#### Method

1. **Import/dependency scanning** — Parse import statements, require calls, or equivalent for the detected language:
   - Go: `import` blocks in `.go` files
   - Python: `import` and `from ... import` in `.py` files
   - TypeScript/JavaScript: `import` and `require` in `.ts`/`.js` files
   - Java: `import` in `.java` files
   - Generic fallback: grep for common import patterns

2. **Build adjacency matrix** — For each module pair (A, B), record whether A imports from B.

3. **Compute fan-in per module** — Count of distinct modules that import from this module.

4. **Compute fan-out per module** — Count of distinct modules this module imports from.

5. **Classify coupling:**
   - **Foundation** (fan-in >= 5, or top 20% by fan-in) — Core dependencies; migrate last. Breaking changes here affect many consumers.
   - **Shared** (fan-in 2-4) — Used by multiple modules; migrate after their consumers are ready.
   - **Leaf** (fan-in 0-1) — Few or no dependents; safe to migrate early.

### 5. Git Hotspot Analysis

Parse git log to identify files that change frequently (hotspots). Hotspots should migrate early to reduce ongoing churn in the legacy codebase.

```bash
git -C {legacy_path} log --format=format: --name-only --since="6 months ago" | sort | uniq -c | sort -rn | head -50
```

For each module, compute:
- **Total commits** — Sum of commit counts for all files in the module.
- **Hotspot score** — Normalized commits (0-100 scale, 100 = most active).

Modules with high hotspot scores benefit from early migration — ongoing changes to them create merge conflicts and drift between legacy and target.

### 6. Migration Ordering

Combine coupling classification and hotspot score to produce a migration priority for each module:

#### Priority Rules

1. **Leaf + High Hotspot** — Migrate first. No dependents to break, and early migration reduces churn.
2. **Leaf + Low Hotspot** — Migrate second. No dependents to break, low urgency.
3. **Shared + High Hotspot** — Migrate third. Coordinate with consumers, but high churn justifies earlier attention.
4. **Shared + Low Hotspot** — Migrate fourth. Coordinate with consumers.
5. **Foundation + High Hotspot** — Migrate fifth. High churn but many dependents; requires careful coordination.
6. **Foundation + Low Hotspot** — Migrate last. Stable and heavily depended upon; defer until consumers are migrated.

Within each priority tier, break ties by:
- Higher hotspot score first
- Lower file count first (smaller modules are faster to migrate)

Present the ordered list to the user:

> "Proposed migration order:"
> | # | Module | Coupling | Hotspot | Files | Priority |
> |---|--------|----------|---------|-------|----------|
> | 1 | `user-service` | Leaf | 85 | 12 | 1 — Leaf+Hot |
> | ... |
>
> "Does this ordering look right? Any modules to reorder or group?"

### 7. Generate Migration Units

For each module in the confirmed order, produce a migration unit. Each unit is an independently shippable spec following the FEATURE spec format.

Each migration unit spec contains:

```markdown
---
type: migration-spec
migration: {migration-slug}
sequence: {N}
module: {module-name}
coupling: {foundation|shared|leaf}
hotspot-score: {0-100}
status: draft
---

# Migration Unit {N}: {Module Name}

## Problem Statement

Migrate `{module-name}` from `{legacy-path}` to `{target-path}`. This module has {coupling-class} coupling (fan-in: {fan-in}, fan-out: {fan-out}) and a hotspot score of {score}.

## Dependencies

- **Upstream (must migrate first):** {list of modules this depends on that must exist in target, or "None"}
- **Downstream (blocks):** {list of modules that depend on this one, or "None"}

## Acceptance Criteria

- [ ] All public interfaces from `{module-name}` are available in the target codebase
- [ ] Existing tests from the legacy codebase pass against the migrated module (or equivalent new tests cover the same behavior)
- [ ] No remaining imports of `{module-name}` from the legacy codebase in migrated consumers
- [ ] The legacy module can be deleted without breaking any migrated code

## Scope

- **Files to migrate:** {file count} source files, {test count} test files
- **Key interfaces:** {list of exported functions, types, or classes that other modules consume}

## Migration Strategy

{One of: copy-and-adapt, rewrite-to-target-conventions, bridge-then-migrate}

## Verification

- [ ] Target module compiles/type-checks independently
- [ ] Legacy tests pass against target module (or new equivalent tests pass)
- [ ] Integration: at least one consumer can import from target instead of legacy without breakage
```

### 8. Produce Migration ROADMAP

Assemble the ordered migration units into a ROADMAP.md following the same structure as `/fellowship:plan --roadmap` output.

Group migration units into phases:
- **Phase 1: Leaf modules** — All leaf-coupling modules, ordered by hotspot score descending
- **Phase 2: Shared modules** — All shared-coupling modules, ordered by hotspot score descending
- **Phase 3: Foundation modules** — All foundation-coupling modules, ordered by hotspot score descending

Each phase section includes:
- Entry criteria (prior phase complete, or nothing for Phase 1)
- Exit criteria (all modules in the phase migrated and verified)
- Feature details per module (What, Depends on, Risk, Checklist)

Include a dependency graph (Mermaid or text) showing module migration order and dependencies.

### 9. Save Artifacts

Resolve artifact paths per `artifact-paths` skill:

1. **Resolve project root** — Use the target project's git root as the artifact destination.
2. **Derive migration directory:** `{project_root}/.skilmarillion/projects/{migration-slug}/`
3. **Confirm path with user** per `artifact-paths` slug confirmation protocol: "Save migration plan to `{project_root}/.skilmarillion/projects/{migration-slug}/ROADMAP.md`?"
5. **Create directories:**
   ```bash
   mkdir -p {project_root}/.skilmarillion/projects/{migration-slug}/specs
   ```
6. **Save ROADMAP.md:** `{project_root}/.skilmarillion/projects/{migration-slug}/ROADMAP.md`
7. **Save individual specs:** `{project_root}/.skilmarillion/projects/{migration-slug}/specs/SPEC-{NNN}-migrate-{module-slug}.md` for each migration unit.

### 10. Confirm and Suggest Next Steps

Present the migration plan summary:
- Total modules: {N}
- Phases: {phase count}
- Estimated specs: {spec count}
- Critical path: {longest dependency chain}

Suggest next steps:

> "Migration plan saved to `.skilmarillion/projects/{migration-slug}/ROADMAP.md` with {N} specs in `.skilmarillion/projects/{migration-slug}/specs/`."
>
> "To begin migration, run `/fellowship:build` on each spec in order:"
> 1. `/fellowship:build .skilmarillion/projects/{migration-slug}/specs/SPEC-001-migrate-{first-module}.md`
> 2. ...

---

## WHAT NOT TO DO

- Do NOT begin migrating code — this command produces a plan, not code changes.
- Do NOT skip coupling analysis and produce a flat, unordered list of modules.
- Do NOT skip the git hotspot analysis — ordering without churn data produces suboptimal sequences.
- Do NOT produce migration units that depend on un-migrated modules without noting the dependency explicitly.
- Do NOT hardcode paths — use the `artifact-paths` skill for all path resolution.
- Do NOT skip the slug confirmation protocol — always confirm the save path with the user.
- Do NOT merge migration units — each module is its own independently shippable spec.
- Do NOT include implementation details (specific code changes, refactoring steps) in the migration plan — that belongs in the individual specs.
