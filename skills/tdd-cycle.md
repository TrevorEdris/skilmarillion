---
name: tdd-cycle
user-invocable: false
allowed-tools: []
model: haiku
tags: [implementation, tdd]
---

# tdd-cycle

Loadable skill defining the RED-GREEN-REFACTOR discipline. Referenced by the `/fellowship:build` command during slice execution.

---

## The Iron Law

**No production code without a failing test first.** This is a hard constraint, not a preference.

If production code was written before a failing test existed:
1. Delete the production code.
2. Write the test first.
3. Implement again from scratch.

---

## Test Runner Discovery

Before writing any test, identify the project's test command:

| Project File | Test Command |
|---|---|
| `package.json` | `npm test` or check `scripts.test` |
| `pyproject.toml` | `pytest` |
| `go.mod` | `go test ./...` |
| `Cargo.toml` | `cargo test` |
| `Makefile` | `make test` |
| `Taskfile.yml` | `task test` |

If unclear: ask the user. Do not guess.

Cache the test command at session start. Use it consistently throughout execution.

---

## RED Phase Rules

Write a test that captures exactly one behavior.

- One behavior per test
- Descriptive name: `test_empty_email_returns_validation_error`, not `test_validate`
- Use real code paths — avoid mocks unless the dependency requires network I/O
- The test defines the interface — write it as if the production code already exists

### RED Verification

Run the test. Confirm:
1. The test **fails** (not errors).
2. The failure message **matches the expected missing behavior**.
3. If the failure is a syntax error or import error: fix that first. It is not a valid RED.
4. If the test passes: the behavior already exists. Skip this step.

**Gate:** Do not proceed to GREEN until RED is confirmed with the correct failure reason.

---

## GREEN Phase Rules

Write the simplest code that makes the test pass.

- Do not add features the test does not require.
- Do not refactor yet. Ugly passing code is correct at this stage.
- Do not generalize prematurely. Hardcoding a return value is acceptable if only one test demands it.

### GREEN Verification

Run the **full test suite**, not just the new test.

Confirm:
1. The new test **passes**.
2. **All existing tests still pass** — no regressions.
3. **No warnings or errors** in the output.

If the new test fails: fix the production code, not the test.
If existing tests fail: fix the regression before proceeding.

**Gate:** Do not proceed to REFACTOR until the full suite is green.

---

## REFACTOR Phase Rules

Only after GREEN, clean the implementation:

- Remove duplication
- Improve names
- Extract helpers
- Improve readability

**Do not add new behavior during REFACTOR.** New behavior requires a new RED.

### REFACTOR Verification

Run the full test suite. All tests must remain green. No warnings.

If any test fails: the refactor introduced a regression. Revert or fix.

---

## Bug Fix Protocol

Bugs are fixed via TDD. The test is the reproduction case.

1. Write a test that demonstrates the incorrect behavior.
2. Run it. Confirm RED — the test fails showing the bug.
3. Fix the bug minimally.
4. Confirm GREEN — new test passes, full suite passes.
5. Refactor if needed. Confirm suite stays green.

---

## Common Rationalizations (Reject All)

| Excuse | Response |
|---|---|
| "Too simple to test" | Simple code breaks too. Write the test. |
| "I'll write tests after" | Tests after implementation verify what the code does, not what it should do. |
| "I manually tested it" | Manual tests don't run on CI and don't prevent regressions. |
| "Deleting my code is wasteful" | Unverified code is the waste. Delete it. |
| "I need to explore first" | Exploration is valid. Write spike code, then delete it and start TDD. |
| "This is hard to test" | Hard-to-test code is a design signal. TDD will improve the design. |
| "TDD will slow me down" | TDD eliminates debugging time. It is faster in aggregate. |

---

## Red Flags — Stop and Restart

TDD was violated if any of these are true:

- Production code was written before any test file was modified
- You cannot point to a specific test that fails because the feature doesn't exist yet
- All tests were written after implementation was complete
- Tests mock so extensively that no real code paths run
- The test suite was run once at the end to confirm "everything passes"
