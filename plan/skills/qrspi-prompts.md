---
name: qrspi-prompts
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, small, qrspi]
---

# qrspi-prompts

Phase-specific guidance and the IMPL_DETAILS.md template for the QRSPI cycle used by SMALL tasks in `/plan:sdd`.

---

## When to Use QRSPI vs Full Spec

| Signal | Route |
|--------|-------|
| 1-3 files, no new behavior, bug fix or config change | QRSPI (SMALL) |
| SMALL + HIGH risk | Prompt to promote to FEATURE |
| Research reveals >5 files or new behavior needed | Prompt to promote to FEATURE |
| New endpoint, new screen, new vertical behavior | FEATURE (full spec) |

---

## Question Phase Prompts

Present design decisions as numbered choices. Work only from the task description — no code reading yet.

**For bug fixes:**
- "Where should the fix live? (1) at the call site (2) in the called function (3) add a guard/validation layer"
- "What is the expected behavior after the fix? Describe in one sentence."
- "Should this fix include a regression test? (1) yes — unit test (2) yes — integration test (3) no — explain why"

**For small changes:**
- "What approach for this change? (1) {option} (2) {option} (3) {option}"
- "Any constraints on backward compatibility? (1) must be backward-compatible (2) breaking change is acceptable (3) not applicable"
- "Scope boundary — what is explicitly out of scope for this change?"

**When no decisions exist:**
> "This is a straightforward change with one obvious approach. No design decisions to surface. Proceeding to Research."

---

## Research Phase Prompts

Map each question to specific files. Read only what answers the question.

**Finding format:**
```
- Q{N}: {question summary}
  Answer: {concise answer}
  Evidence: `{file}:{line}` — {what the code shows}
  Constraints: {any constraints discovered}
```

**Size escalation check:**
After completing research, count the files that need changes. If >5 files or if new behavior (new functions, new modules, new tests beyond regression) is required:
> "Research suggests this is bigger than SMALL. Promote to FEATURE workflow? (yes / no)"

---

## Structure Phase Prompts

For SMALL tasks, structure is typically 1-2 phases.

**Single-phase template (most SMALL tasks):**
```
## Structure

### Phase 1: {capability name}
- Delivers: {what this phase produces}
- Dependencies: none
- Risk: {what could go wrong}
```

**Two-phase template (when test + implementation are separable):**
```
## Structure

### Phase 1: {test/setup name}
- Delivers: {failing test or setup}
- Dependencies: none
- Enables: Phase 2

### Phase 2: {implementation name}
- Delivers: {the fix or change}
- Dependencies: Phase 1
- Risk: {what could go wrong}
```

---

## IMPL_DETAILS.md Template

This is the output artifact for the Plan phase. It must pass `validate.py --type plan` (score >= 70).

```markdown
# Implementation Details: {task title}

## Target Repos and File Paths

- **Repo:** `{repo-name}` (`{absolute-path}`)
- **Files to modify:**
  - `{relative/path/to/file1}` — {what changes}
  - `{relative/path/to/file2}` — {what changes}
- **Files to create:**
  - `{relative/path/to/new-file}` — {purpose}

## Structure

### Phase 1: {phase name}
- Delivers: {capability}
- Dependencies: {none | Phase N}
- Risk: {risk description} (likelihood: low/medium, impact: low/medium)

## Ordered Implementation Steps

### Step 1: {description}
- **File:** `{exact/file/path}`
- **Action:** {specific change to make}
- **Verification:** {how to confirm — test command, lint, manual check}

### Step 2: {description}
- **File:** `{exact/file/path}`
- **Action:** {specific change to make}
- **Verification:** {how to confirm}

## Risks and Assumptions

- **Risk:** {description} — Mitigation: {mitigation}
- **Assumption:** {what we assume to be true}

## Verification Steps

- [ ] {verification action 1 — e.g., `pytest tests/test_foo.py -v`}
- [ ] {verification action 2 — e.g., `python -m mypy src/`}
- [ ] {verification action 3 — e.g., manual smoke test description}

## Scope Boundary

- **In scope:** {what this plan covers}
- **Out of scope:** {what this plan does NOT cover}

## Traceability

| Research Finding | Plan Step | Notes |
|------------------|-----------|-------|
| {finding from Research phase} | Step N | |
| {finding} | Step M | |

## Git Strategy

- **Branch:** `{branch-name}`
- **Commit checkpoints:**
  1. `{commit message for first logical unit}`
  2. `{commit message for second logical unit}`
- **PR title:** {short title, under 70 chars}
- **PR description:** {1-2 sentence summary of the change}
```

---

## Restraint Principle

A 3-file bug fix should not produce a 50-step plan. Match plan granularity to task size:

| Task scope | Expected steps | Expected phases |
|------------|---------------|-----------------|
| 1 file, config or typo | 1-2 steps | 1 phase |
| 1-2 files, bug fix | 2-4 steps | 1 phase |
| 2-3 files, small change | 3-6 steps | 1-2 phases |

If the plan exceeds these ranges, re-evaluate whether the task is truly SMALL.
