# TDD Verification Checklist

Fill in this checklist before marking any implementation task complete.

**Task:** <!-- feature or bug fix description -->
**Date:**
**Test command:**

---

## Test-First Compliance

- [ ] All new production code was preceded by a failing test
- [ ] No production code was written without an existing failing test
- [ ] No production code was deleted and rewritten without writing a test first

## RED Phase

- [ ] Each test was run and observed to fail before implementing
- [ ] Each failure was for the expected reason (missing behavior, not syntax/import error)
- [ ] No test passed immediately without implementation (revised if it did)

## GREEN Phase

- [ ] Each test passes after minimal implementation
- [ ] Implementation was minimal — no code beyond what the test required
- [ ] No behavior added during GREEN that the current test did not demand

## Full Suite

- [ ] Full test suite passes — not just new tests
- [ ] No previously passing tests were broken
- [ ] No warnings or errors in test output

## REFACTOR Phase

- [ ] Refactoring done only after GREEN confirmed
- [ ] No new behavior added during refactoring
- [ ] Full test suite passes after refactoring

## Test Quality

- [ ] Tests use real code paths (mocks limited to external I/O)
- [ ] Each test asserts on observable behavior, not implementation details
- [ ] One behavior per test — no god tests
- [ ] Test names describe the behavior under test

## Coverage

- [ ] Every new public function or method has at least one test
- [ ] Edge cases covered: empty inputs, boundary values, null/nil/undefined
- [ ] Error paths covered: invalid inputs, failed dependencies, unexpected states
- [ ] Coverage delta recorded (if tooling available)

**Coverage before:** ____%
**Coverage after:** ____%

---

## Sign-off

All items checked. Implementation follows TDD. Ready for review.
