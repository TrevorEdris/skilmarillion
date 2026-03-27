---
name: spec-format
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, spec]
---

# spec-format

A loadable skill that defines the structure, AC format, vertical slice format, and risk-depth rules for dream specs.

---

## Required Sections

Every spec produced by `spec-builder` must include these sections:

1. **Problem Statement** — One paragraph. What problem does this solve? Who is affected?
2. **Acceptance Criteria** — Testable conditions in Given/When/Then format. Organized as Vertical Slices for FEATURE specs.
3. **Vertical Slices** — *(FEATURE only)* Self-contained, independently shippable units of behavior. Each slice has its own ACs.
4. **Architecture Recommendation** — *(FEATURE only)* Pattern chosen and rationale. Filled by `architecture-advisor`.
5. **TDD Plan** — *(FEATURE only)* Ordered RED→GREEN→REFACTOR steps per slice. Filled by `tdd-planner`.

**SMALL spec minimum:** Problem Statement and Acceptance Criteria only. Architecture and TDD sections are omitted.

---

## AC Format

Each acceptance criterion is one sentence in **Given/When/Then** format.

Rules:
- No "and" within a single criterion — split into separate ACs
- One behavior per AC
- Each AC must be independently testable

### Examples

**Good AC:**
> Given a registered user, when they submit a valid login form, then they receive an authenticated session token.

**Bad AC — uses "and" (two behaviors):**
> Given a registered user, when they submit a valid login form, then they receive an authenticated session token and are redirected to the dashboard.

Fix by splitting:
> AC-1: Given a registered user, when they submit a valid login form, then they receive an authenticated session token.
> AC-2: Given an authenticated user, when login succeeds, then they are redirected to the dashboard.

**Bad AC — vague (not testable):**
> Given a user, when they log in, then the system works correctly.

Fix by making it specific:
> Given a registered user with correct credentials, when they submit the login form, then the response status is 200 and a session cookie is set.

---

## Vertical Slice Format

Each slice is a self-contained, independently shippable unit of behavior.

Format:
```
## Slice N: [Name]

[One sentence describing what this slice delivers.]

- AC-N.1: Given ..., when ..., then ...
- AC-N.2: Given ..., when ..., then ...
```

Slices are ordered from foundational to surface:
1. Data model / schema changes
2. Business logic / service layer
3. API / interface layer
4. UI / consumer layer (if applicable)

Each slice should be mergeable and testable on its own. A slice must not depend on a later slice.

---

## Risk-Based Depth

The `risk` field from the triage result determines how many AC scenarios to cover.

| Risk Level | Required Coverage |
|------------|------------------|
| LOW | Happy path ACs only |
| MODERATE | Happy path + key error cases |
| HIGH | Happy path + edge cases + failure modes + rollback path |

### Examples

**LOW risk:**
> AC-1: Given valid input, when the function is called, then it returns the expected result.

**MODERATE risk:**
> AC-1: Given valid input, when the function is called, then it returns the expected result.
> AC-2: Given invalid input, when the function is called, then it returns a 400 error with a descriptive message.

**HIGH risk:**
> AC-1: Given valid input, when the function is called, then it returns the expected result.
> AC-2: Given invalid input, when the function is called, then it returns a 400 error with a descriptive message.
> AC-3: Given a concurrent write conflict, when the function is called, then it returns a 409 and does not corrupt data.
> AC-4: Given an upstream service failure, when the function is called, then it fails safely and the rollback path is triggered.
