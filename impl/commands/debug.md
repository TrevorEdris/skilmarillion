---
description: Structured debugging with mandatory root cause analysis before any fix proposal. Four phases: reproduce, isolate, identify root cause, propose fix.
argument-hint: "[issue description, error message, or failing test]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
  - ToolSearch
model: sonnet
---

# /impl:debug

Structured root cause analysis for bugs, test failures, and unexpected behavior. Follows a four-phase methodology: investigate, analyze patterns, hypothesize, fix. The root cause template **must** be completed before any fix is proposed.

---

## ON STARTUP

> **Deferred tool note:** Before calling `AskUserQuestion`, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

If no issue description is provided as an argument, ask the user:

> "Describe the bug, paste the error message, or point me to the failing test."

---

## Phase 1: Reproduce and Investigate (MANDATORY FIRST)

Do not form a hypothesis until this phase is complete.

1. **Read the full error** — stack traces, line numbers, error codes. Read every line.
2. **Reproduce consistently** — run the failing test or trigger the bug. Record the exact command and output.
3. **Check recent changes** — `git diff`, `git log --oneline -10`, new dependencies, config changes.
4. **Trace the data flow** — where does the bad value originate? Follow it upstream until you find the source.
5. **Gather boundary evidence** — in multi-component systems, check inputs and outputs at each boundary.

### Output after Phase 1

```
**Symptom:** [exact error message or unexpected behavior]
**Reproduction:** [exact command that triggers it, every time]
**Scope:** [which files/modules are involved]
```

If the issue cannot be reproduced, ask the user for additional context before proceeding.

---

## Phase 2: Pattern Analysis

1. Find **working examples** of similar code in the codebase.
2. Compare working vs. broken implementations — identify every difference.
3. Map the dependency chain: what calls what, in what order.
4. Check for recent regressions: does `git bisect` narrow it down?

---

## Phase 3: Root Cause Identification

### Root Cause Template (REQUIRED)

Before proposing any fix, you **must** complete this template with specifics. Vague answers are rejected.

```
The bug occurs because [SPECIFIC CONDITION] causes [SPECIFIC COMPONENT]
to [SPECIFIC INCORRECT BEHAVIOR] when [SPECIFIC TRIGGER].
```

**Validation rules:**
- `[SPECIFIC CONDITION]` must name a concrete state, value, or configuration — not "something is wrong."
- `[SPECIFIC COMPONENT]` must be a file, function, class, or module name — not "the system."
- `[SPECIFIC INCORRECT BEHAVIOR]` must describe the actual vs. expected behavior — not "it breaks."
- `[SPECIFIC TRIGGER]` must be a reproducible action or input — not "sometimes."

If you cannot fill in all four fields with specifics: return to Phase 1 or Phase 2. You are not ready to fix.

### Hypothesis Testing

- Form **one** hypothesis at a time. Never bundle multiple theories.
- Test with the **smallest possible change** — one variable only.
- If the hypothesis fails: discard it entirely. Do not layer fixes on a failed hypothesis.
- If you cannot form a specific hypothesis: state what you do not know rather than guessing.

---

## Phase 4: Fix Proposal and Verification

Only reachable after the root cause template is complete.

### Debugging Report

Present findings in this exact format:

```markdown
### Debugging Report

**Symptom**
[What was observed — exact error, unexpected behavior, test failure output]

**Root Cause**
The bug occurs because [condition] causes [component] to [behavior] when [trigger].

**Evidence**
[Files read, commands run, outputs that confirm the root cause]

**Severity**
[CRITICAL | HIGH | MEDIUM | LOW]

**Recommended Fix**
[Specific, minimal change — file path, line number, exact change]

**Verification Plan**
[Exact command or test that confirms the fix works]

**Confidence**
[High | Medium | Low — and why if not High]
```

### Severity Classification

- **CRITICAL** — data corruption, security exposure, system unavailability
- **HIGH** — incorrect behavior, silent failures, performance degradation
- **MEDIUM** — edge case failures, degraded behavior under specific conditions
- **LOW** — minor inconsistencies, cosmetic issues, non-blocking problems

---

## Three-Fix Limit (ENFORCED)

Track the number of fix attempts for the current issue.

- **After fix attempt 1:** If the fix does not resolve the issue, state what was learned and form a new hypothesis.
- **After fix attempt 2:** If still unresolved, re-examine Phase 1 evidence. Something was missed.
- **After fix attempt 3:** **STOP.** Do not attempt a fourth fix.

When the three-fix limit is reached, present:

```
THREE-FIX LIMIT REACHED

Attempted fixes:
1. [what was tried] — [why it failed]
2. [what was tried] — [why it failed]
3. [what was tried] — [why it failed]

This is likely an architectural issue, not a code bug.
Continuing without deeper understanding will add complexity without solving the problem.

Recommended next steps:
- Review the component's design assumptions
- Check if the contract between [component A] and [component B] is correct
- Consider whether the current architecture supports this use case
```

Ask the user how to proceed. Do not attempt another fix without explicit approval.

---

## Behavioral Rules

- Phase 1 is mandatory before any hypothesis — no exceptions.
- The root cause template must be filled with specifics before any fix is proposed.
- One hypothesis at a time — never bundle multiple theories.
- One variable at a time — never combine multiple changes in a single fix attempt.
- After every fix: run the relevant test or check. Report actual output, not "this should work."
- Never say "I think" or "probably" without evidence. State what you know and what you do not.
- Do not skip evidence gathering because the bug "looks obvious."
