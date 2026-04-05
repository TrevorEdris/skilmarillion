# Discovery Questions

Ask these questions BEFORE writing any PRD sections. The goal is to surface assumptions, constraints, and scope boundaries upfront — preventing PRDs that answer the wrong question.

---

## Core Questions (Always Ask)

Present these as a batch — not one at a time. Wait for the user to answer all before proceeding to authoring.

### 1. The Problem

> "What problem are we solving? Describe it without mentioning any solution."
>
> Follow-up if the answer includes a solution: "That sounds like a solution. What's the problem it solves? What pain exists if we build nothing?"

### 2. The Stakes

> "What happens if we don't solve this? Who is affected, and how much does it cost them (time, money, frustration, risk)?"

### 3. Success Definition

> "If this ships and works perfectly, what changes? What do you see in 6 months that you don't see today?"
>
> Push for specifics: "Users are happier" → "What would they say in a survey? What number would change?"

### 4. Non-Goals

> "What are we explicitly NOT trying to achieve? What should we resist even if it seems tempting?"

### 5. Constraints (Ask if not obvious from context)

> "What constraints exist that will shape the solution?"
>
> Prompt for each:
> - **Timeline:** Is there a hard deadline? What drives it?
> - **Budget:** Is there a spending limit (infrastructure, vendor, headcount)?
> - **Team:** Who will build this? What skills do they have?
> - **Technology:** Are there tech stack requirements or restrictions?
> - **Compliance:** Any regulatory requirements (HIPAA, SOC2, GDPR, accessibility)?

---

## Situational Questions (Ask if relevant)

Only ask these if the user's answers to core questions surface relevant context.

### Prior Art

> "What has been tried before? Why didn't it work? What can we learn from the attempt?"

Ask when: the user mentions previous attempts, failed projects, or existing workarounds.

### Stakeholders

> "Who are the stakeholders? Who has input? Who has veto power? Who will be surprised if they aren't consulted?"

Ask when: the feature is multi-team, external-facing, or involves approvals.

### Existing Context

> "Is there existing code, an existing product, or an existing process that this relates to? Should we reverse-engineer requirements from what exists?"

Ask when: the user references an existing system being replaced or extended.

---

## Answer → Section Mapping

| Question | Feeds PRD Section |
|----------|-------------------|
| 1. The Problem | Problem Statement |
| 2. The Stakes | Problem Statement (impact), Success Metrics |
| 3. Success Definition | Success Metrics, Milestone deliverables |
| 4. Non-Goals | Scope Boundary (out-of-scope) |
| 5. Constraints | Non-Functional Requirements, Dependencies, Scope Boundary |
| Prior Art | Problem Statement (context), Open Questions |
| Stakeholders | User Personas, Dependencies |
| Existing Context | Problem Statement, Functional Requirements |

---

## When to Skip

- If the user has already documented answers (e.g., in a brief, a Slack thread, or a prior PRD), reference existing answers rather than re-asking.
- If the user provides a detailed feature description as the command argument, extract answers from it and only ask about gaps.
