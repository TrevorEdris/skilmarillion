# Testing Anti-Patterns

**Load when:** Writing tests, reviewing test coverage, working with mocks, or debugging why tests pass but code is broken.

---

## Iron Laws of Testing

Non-negotiable. Violating them produces tests that give false confidence.

1. **Never test mock behavior.** If a test only verifies a mock was called with certain arguments, it tests nothing about production code.
2. **Never add test-only methods to production code.** If you need to expose internal state, the design is wrong. Test through the public interface.
3. **Never mock without understanding the real implementation.** A mock that doesn't reflect actual behavior lets bugs through.
4. **Never assert on implementation details.** Assert on observable behavior: return values, side effects, state changes.
5. **Never write tests after the fact and call it TDD.** Tests written after implementation encode bugs as expected behavior.

---

## Anti-Pattern Catalog

### The Mock Forest

**Signal:** 3+ mocks, no behavior assertions.

**Problem:** Test exercises no production logic. Verifies that the mock was called — which is only true if the code calls the mock. Real bugs pass through.

**Fix:** Test through the real dependency graph. Mock only the HTTP client at the lowest level, not the service itself.

**Gate:** "Does removing this mock and using the real implementation require network I/O?" If no, don't mock.

### The Tautology Test

**Signal:** Test passes with any implementation.

**Problem:** Asserts something trivially true (`expect(x).toEqual(x)`) or only verifies plumbing exists without checking output.

**Fix:** Assert on specific observable outcomes. What should the function return? Assert that exact value.

**Gate:** "Would this assertion still pass if I introduced an obvious bug?" If yes, the assertion is insufficient.

### Tests the Framework

**Signal:** No production code called.

**Problem:** Verifies language features (struct assignment works, array push works), not production behavior.

**Fix:** Call the production function and assert on its behavior.

**Gate:** "Does this test call any production code?" If no, delete it.

### The Brittle Test

**Signal:** Breaks on unrelated changes.

**Problem:** Tightly coupled to internal formatting or fixture shapes. Any change breaks it even when behavior is correct.

**Fix:** Test the behavioral contract, not the implementation. Include only necessary fixture fields.

**Gate:** "Am I including fields the behavior actually requires, or copying a full object shape?"

### The God Test

**Signal:** Test covers multiple behaviors.

**Problem:** When it fails, you don't know which behavior broke. Couples unrelated behaviors.

**Fix:** One test per behavior. Each test fails for exactly one reason.

**Gate:** "Is this assertion testing the same behavior or a different one?" If different, create a new test.

### The Pesticide Paradox

**Signal:** New code, no new tests.

**Problem:** Tests become documentation of past bugs, not detectors of future ones.

**Fix:** Every new behavior requires a new test. Every bug fix requires a reproduction test.

**Gate:** "What behaviors does the system have that no test exercises?"

---

## Quick Reference

| Anti-Pattern | Signal | Fix |
|---|---|---|
| Mock Forest | 3+ mocks, no behavior assertions | Mock only external I/O |
| Tautology Test | Test passes with any implementation | Assert on specific outcomes |
| Tests the Framework | No production code called | Call real production functions |
| Brittle Test | Breaks on unrelated changes | Test behavioral invariants |
| God Test | Covers multiple behaviors | One test per behavior |
| Pesticide Paradox | New code, no new tests | Test every new behavior |

---

## Red Flags

Stop and reassess if:

- A test file has more mock setup lines than assertion lines
- Removing a production function causes no test to fail
- Tests pass faster after a new implementation than before
- Adding new production behavior requires no new test
- A test was written "just to get coverage"
- You cannot describe what specific behavior would cause a test to fail
