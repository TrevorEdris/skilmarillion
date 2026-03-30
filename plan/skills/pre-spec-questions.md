---
name: pre-spec-questions
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, questions, pre-spec]
---

# pre-spec-questions

Design decision prompts to surface before spec generation. Run after triage, before context gathering or spec building. Work only from the task description — no code reading yet.

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

**For new behavior (FEATURE):**
- "What is the primary user-facing capability this delivers?"
- "Which existing system boundaries does this cross? (1) none — contained in one service (2) API boundary (3) database schema (4) multiple services"
- "What trade-off matters most? (1) performance (2) simplicity (3) consistency with existing patterns"

**When no decisions exist:**
> "This is a straightforward change with one obvious approach. No design decisions to surface. Proceeding to context gathering."

---

## Gate

Do not proceed to context gathering or spec building until design questions are answered or explicitly scoped out. Confirmed answers become constraints passed to `context-gatherer` and `spec-builder`.
