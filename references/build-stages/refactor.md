# /fellowship:build --refactor

Phase-gated refactoring. Each transformation step runs the full test suite before the next step begins. Behavior preservation is non-negotiable.

---

## Core Rule

**Never add behavior during a refactor.** If a refactoring step changes observable output, revert and re-approach. One smell per commit.

---

## Input Detection

1. If argument is a file path or directory: scope analysis to that target.
2. If no argument: ask the user what to refactor (file, directory, or "recent changes").
3. If "recent changes": derive scope from `git diff --stat HEAD~5`.

---

## Phase 1: Baseline

Establish a green test suite before touching anything.

1. Detect the project's test runner:
   ```
   npm test || pnpm test || yarn test || pytest || go test ./... || cargo test || make test || task test
   ```
2. Run the full suite. Record the result.
3. **If red:** STOP. Do not refactor against a failing suite. Report the failures and suggest `/fellowship:build --debug` instead.
4. **If no tests exist for the target code:** Write characterization tests that lock in current behavior before proceeding. These tests assert what the code *does*, not what it *should* do.
5. Record baseline: test count, pass count, suite runtime.

**Gate:** Green suite required to proceed.

---

## Phase 2: Reconnaissance

Detect code smells in the target scope.

### Smell Catalog

#### Bloaters
- **Long Method** -- function does too much; harder to name, test, and reason about
- **Large Class** -- class has too many responsibilities; violates SRP
- **Long Parameter List** -- more than 3-4 parameters signals missing abstraction
- **Primitive Obsession** -- domain concepts represented as raw strings/ints instead of types
- **Data Clumps** -- groups of fields that always travel together should be their own type

#### Object-Orientation Abusers
- **Switch Statements** -- repeated type-dispatch logic that should be polymorphism
- **Parallel Inheritance Hierarchies** -- adding a class in one hierarchy requires adding in another
- **Refused Bequest** -- subclass ignores inherited interface, signaling wrong hierarchy

#### Change Preventers
- **Divergent Change** -- one class must be changed in many ways for different reasons
- **Shotgun Surgery** -- one change requires edits in many classes simultaneously
- **Feature Envy** -- method uses another class's data more than its own

#### Dispensables
- **Dead Code** -- unreachable code, unused variables, unused exports
- **Lazy Class** -- class does so little it doesn't justify existence
- **Speculative Generality** -- abstractions added "just in case" with no current use
- **Duplicate Code** -- identical or near-identical code in multiple locations
- **Comments as Deodorant** -- comments explaining *what* bad code does instead of cleaning it up

#### Couplers
- **Inappropriate Intimacy** -- class accesses another's private members or internal details
- **Message Chains** -- `a.b().c().d()` long chains of navigation
- **Middle Man** -- class that only delegates to another; pointless indirection

#### Architecture Smells
- **God Object** -- single class/module that knows too much and does too much
- **Anemic Model** -- domain objects with no behavior, all logic in services
- **Premature Abstraction** -- interface/abstract class with exactly one implementation and no planned second
- **Pattern Soup** -- multiple design patterns layered where a simple function would suffice

### Detection Steps

1. Read each file in scope.
2. Identify smells with `file:line` references.
3. Classify each finding by triage level:
   - **[Design Discussion]** -- structural issue requiring user alignment before refactoring (god object decomposition, circular dependency breaking, interface segregation affecting multiple callers)
   - **[Active Smell]** -- clear smell addressable with standard techniques (duplicate logic, long methods, dead code, feature envy)
   - **[Quick Fix]** -- minor cleanup, low effort, low risk (rename for clarity, remove unused import, extract a well-named variable)
4. Output the triaged findings list.

---

## Phase 3: Refactoring Plan

Map each smell to a transformation technique and present for approval.

### Technique Selection

| Smell | Primary Technique | Alternative |
|-------|------------------|-------------|
| Long Method | Extract Method | Replace Temp with Query |
| Large Class | Extract Class | Extract Subclass |
| Long Parameter List | Introduce Parameter Object | Preserve Whole Object |
| Duplicate Code | Extract Method + Pull Up | Form Template Method |
| Feature Envy | Move Method | Extract Method + Move |
| Shotgun Surgery | Inline Class + Move Method | Extract Class |
| Dead Code | Safe Delete | Conditional Compilation |
| Tight Coupling | Dependency Inversion | Extract Interface |
| God Object | Extract Class | Facade Pattern |
| Switch Statements | Replace Conditional with Polymorphism | Replace Type Code with Subclasses |
| Primitive Obsession | Replace Primitive with Object | Introduce Value Object |
| Message Chains | Hide Delegate | Extract Method |
| Anemic Model | Move logic to domain object | Enrich with behavior methods |
| Premature Abstraction | Inline Class / Remove Interface | Defer until second use case |
| Pattern Soup | Collapse layers | Replace with plain function |

### Plan Structure

For each item, produce:

```
Step N: [technique] on [file:line]
  Smell: [smell name]
  Triage: [Design Discussion | Active Smell | Quick Fix]
  Effort: S (< 30 min) | M (< 2 hrs) | L (multi-session)
  Risk: [what could break]
  Depends on: [step N-1, or "none"]
```

Order steps by dependency -- some refactorings enable others (extract method before move method).

**Present the plan to the user. Wait for explicit approval before executing any changes.**

Use `AskUserQuestion` with options:
- "Approve all steps"
- "Approve with modifications"
- "Cancel"

---

## Phase 4: Execution

For each approved step, run the transform-test-commit loop.

### The Loop

```
1. Confirm tests are GREEN (baseline for this step)
2. Apply the refactoring -- minimal, atomic diff
3. Run the FULL test suite
4. If GREEN:
   a. Verify the diff contains NO behavior changes
   b. Report: "Step N complete. [technique] applied to [file]. Suite green."
   c. Proceed to next step
5. If RED:
   a. Revert immediately: git checkout -- <affected files>
   b. Report the failure with test output
   c. Ask user: "Skip this step?" / "Retry with different approach?" / "Stop"
```

### Post-Step Diff Check

After each step, before proceeding:

1. Run `git diff` on the changed files.
2. Scan the diff for behavior-change indicators:
   - New `if`/`else`/`switch` branches not present in original
   - Changed return values or error messages
   - New function calls not present in original (beyond the extraction itself)
   - Modified loop bounds or conditions
3. If any indicator is detected: flag it and ask the user to confirm it is purely structural.

### Commit Convention

Each step gets its own commit:

```
refactor: [technique] [target]

Examples:
  refactor: extract validatePayload from processRequest
  refactor: remove dead code in utils/legacy.ts
  refactor: introduce ParameterObject for createUser args
```

---

## Phase 5: Verification

After all steps complete:

1. Run the full test suite end-to-end.
2. Compare before/after: file count, line count, test count (should not decrease).
3. Confirm git log shows atomic, clearly-labeled commits.
4. Generate summary:

```markdown
### Refactoring Summary

**Scope:** [files/directories]
**Steps completed:** N of M
**Steps skipped:** [list with reasons]
**Test suite:** [pass count] passing, [baseline runtime] -> [current runtime]

#### Changes
- [Step 1]: [technique] on [file] -- [one-line description]
- [Step 2]: [technique] on [file] -- [one-line description]

#### Deferred
- [Smell]: [reason deferred]
```

5. Suggest: "Run `/fellowship:review` to validate the refactoring" (with install hint not needed; review is built-in).

---

## Quick Reference

| Phase | Action | Gate |
|-------|--------|------|
| 1. Baseline | Run full test suite | GREEN required |
| 2. Reconnaissance | Detect and classify smells | -- |
| 3. Plan | Map techniques, order, estimate | **User approval required** |
| 4. Execute | Transform -> test -> commit loop | GREEN after each step |
| 5. Verify | Full suite + metrics + summary | -- |

---

## Failure Escalation

- **3 consecutive RED results on the same step:** Stop attempting. Report the pattern and suggest `/fellowship:build --debug` for root cause analysis.
- **User cancels mid-execution:** Committed steps remain (they are individually green). Uncommitted work is reverted.
- **No test runner detected:** Write characterization tests first (Phase 1, step 4). If user declines, warn that refactoring without tests is high-risk and proceed only with explicit consent.
