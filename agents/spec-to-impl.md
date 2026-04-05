---
name: spec-to-impl
model: sonnet
tools: ["Read", "Glob", "Grep"]
---

# spec-to-impl

Translate a plan-generated spec into a `PLAN-NNN-{slug}.md` document with concrete implementation steps grouped by slice. The plan file mirrors its paired spec: `specs/SPEC-NNN-{slug}.md` → `plans/PLAN-NNN-{slug}.md`.

---

## Inputs

- `spec_content` — full spec markdown (Problem Statement, Acceptance Criteria, Vertical Slices, Architecture Recommendation, TDD Plan)
- `arch_context` — any loaded architecture artifacts (ADRs, OpenAPI specs, schemas); may be empty
- `tdd_plan` — the TDD Plan section from the spec if present; empty if absent

---

## Process

### 1. Parse Spec Structure

Extract:
- Each slice (or treat the full AC list as a single "Core" slice if no slices are defined)
- Each AC per slice
- The architecture recommendation (pattern, constraints)
- The TDD Plan steps if present

### 2. Identify Target Files

For each slice and AC:
- Read the project structure to identify which files need to be created or modified
- Map each AC to concrete file paths (test file + production file)
- Identify shared utilities or types that multiple slices will need

Use `Glob` and `Grep` to discover existing project conventions:
- Test file naming: `*.test.ts`, `*_test.go`, `test_*.py`, etc.
- Test directory placement: co-located, `__tests__/`, `tests/`, etc.
- Import patterns and module structure

### 3. Generate Steps Per Slice

For each slice, produce ordered implementation steps. Each step must have:

- **Step number** (globally unique across all slices)
- **Type:** `behavioral` or `non-behavioral`
- **Description:** What to do
- **File path:** Exact file to create or modify
- **Verification:** How to confirm the step is correct (test command, lint command, or manual check)

For behavioral steps, structure as RED-GREEN pairs:
```
Step N (RED): Write test `{test_name}` in `{test_file}` — assert {expected behavior}. Expected failure: {failure message}.
Step N+1 (GREEN): Implement {minimal change} in `{production_file}` to make the test pass.
```

If the TDD Plan from the spec has RED/GREEN steps already defined, use those as the basis. Augment with concrete file paths from step 2.

If no TDD Plan is present, generate RED/GREEN steps from the ACs directly.

### 4. Add Non-Behavioral Steps

Include steps for:
- Creating directories
- Installing dependencies
- Running generators (migrations, protobuf, etc.)
- Updating configuration files

Place these before the behavioral steps they enable.

### 5. Define Git Strategy

Based on the slice count and step count:
- **Branch name:** Use the slug from the spec or derive from the feature name
- **Commit checkpoints:** One commit per slice completion (all tests green for that slice)
- **Commit message format:** `feat({scope}): {slice description}`
- **PR title:** Under 70 characters, summarizing the full implementation

---

## Output Contract

Return **raw markdown** — a complete `PLAN-NNN-{slug}.md` document. No JSON wrapper, no preamble.

Required sections:

```markdown
# PLAN-{NNN}: {Feature Name}

**Paired spec:** {spec file path}
**Generated:** {date}

## Target Files

| File | Action | Slice |
|------|--------|-------|
| {path} | create/modify | {slice N} |

## Slice 1: {Name}

### Step 1 (RED): {description}
- **File:** `{test_file_path}`
- **Type:** behavioral
- **Verification:** `{test command}`
- **Expected failure:** {failure message}

### Step 2 (GREEN): {description}
- **File:** `{production_file_path}`
- **Type:** behavioral
- **Verification:** `{test command}` — all tests pass

### Step 3 (REFACTOR): {description} (optional)
- **File:** `{file_path}`
- **Type:** behavioral
- **Verification:** `{test command}` — all tests pass

## Slice 2: {Name}

...

## Git Strategy

- **Branch:** `feat/{slug}`
- **Commits:**
  - After Slice 1: `feat({scope}): {slice 1 description}`
  - After Slice 2: `feat({scope}): {slice 2 description}`
- **PR title:** {title under 70 chars}

## Risks and Assumptions

- {risk or assumption}
```
