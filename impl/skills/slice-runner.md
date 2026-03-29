---
name: slice-runner
user-invocable: false
allowed-tools: []
model: haiku
tags: [implementation, tdd, debugging]
---

# slice-runner

Loadable skill for slice execution state management and failure escalation. Referenced by `/impl:tdd` when a slice encounters repeated failures.

---

## State Machine

Each slice progresses through a defined state machine:

```
PENDING -> RED -> GREEN -> REFACTOR -> COMPLETE
                    |          |
                    v          v
                 FAILING -> DIAGNOSTIC -> (RETRY | SPLIT | DEBT)
```

### States

| State | Description |
|---|---|
| PENDING | Slice not yet started |
| RED | Writing/running failing test |
| GREEN | Writing/running minimal implementation |
| REFACTOR | Cleaning up after GREEN |
| COMPLETE | All steps in slice pass; full suite green |
| FAILING | A step has failed (attempts < 3) |
| DIAGNOSTIC | 3 attempts exhausted; analyzing root cause |

---

## Failure Escalation Protocol

When a step fails 3 times, the runner enters DIAGNOSTIC state.

### Diagnostic Analysis

Collect:
1. **What was tried:** List all 3 attempts with their approach and result
2. **Failure pattern:** Are the failures consistent (same error) or varied?
3. **Root cause hypothesis:** Complete this sentence:
   > "The step fails because [condition] causes [component] to [behavior] when [trigger]."

If the sentence cannot be completed with specifics: the root cause is not understood. More investigation is needed before choosing a decision.

### Decision Matrix

| Pattern | Decision | Action |
|---|---|---|
| Same error each time, approach was wrong | **Modified Approach** | Reset attempts to 0, try a fundamentally different approach |
| Varied errors, step is too large | **Sub-Slice Decomposition** | Split the step into 2-3 smaller steps |
| External constraint prevents implementation | **ACCEPT_WITH_DEBT** | Record gap, notify downstream slices, advance |
| Root cause unclear after analysis | **ACCEPT_WITH_DEBT** | Do not loop — accept and move on |

### Modified Approach (Decision A)

The modification must be **fundamentally different**, not a minor variation:
- Different algorithm or data structure
- Different API or library
- Different architectural pattern
- Reordered dependencies

If the modification is "try the same thing but change line 42": it is not a modified approach. Choose SPLIT or DEBT instead.

### Sub-Slice Decomposition (Decision B)

Split the failing step into smaller, independently testable sub-steps.

Rules:
- Each sub-step must have its own RED-GREEN cycle
- Sub-steps inherit the parent step's slice context
- Sub-steps are inserted into the execution queue immediately after the current position
- The parent step is marked as decomposed (not failed, not complete)

### ACCEPT_WITH_DEBT (Decision C)

Produce a structured gap record:

```yaml
slice: "{slice_name}"
step: {step_number}
missing_behavior: "{what was not implemented}"
severity: "low | medium | high"
justification: "{why this was accepted — external constraint, time box, etc.}"
attempted_approaches:
  - "{approach 1 summary}"
  - "{approach 2 summary}"
  - "{approach 3 summary}"
```

Severity guide:
- **low:** Cosmetic or non-functional; does not affect correctness
- **medium:** Functional gap; workaround exists; should be addressed before production
- **high:** Core behavior missing; no workaround; must be addressed before merge

Downstream notification: Append a note to the IMPL_DETAILS.md:
```markdown
> **Debt note from Slice {N}:** {missing_behavior}. Downstream slices should {workaround or constraint}.
```

---

## Step Classification

The runner classifies each step to determine whether RED-GREEN-REFACTOR applies.

### Behavioral Steps (RED-GREEN-REFACTOR required)

A step is behavioral if it introduces or changes **observable behavior**:
- New function, method, or handler
- Changed return value, side effect, or error behavior
- New endpoint, route, or event handler
- Modified business logic

### Non-Behavioral Steps (direct execution)

A step is non-behavioral if it does not change observable behavior:
- Creating directories or configuration files
- Installing dependencies
- Running code generators (migrations, protobuf, OpenAPI)
- Updating documentation
- Renaming files (without behavior change)
- Adding type annotations (without changing runtime behavior)

Non-behavioral steps execute directly and verify via their specified check (lint, build, manual).

---

## Commit Checkpoints

After each slice reaches COMPLETE state:
1. Run the full test suite (final confirmation for the slice)
2. Stage the changed files
3. The commit checkpoint is informational — the user decides when to actually commit
4. Suggested message format: `feat({scope}): {slice description}`
