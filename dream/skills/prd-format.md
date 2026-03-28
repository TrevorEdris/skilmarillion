---
name: prd-format
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, prd]
---

# prd-format

A loadable skill that defines the structure, requirement format, and abstraction rules for dream PRDs.

---

## Required Sections

Every PRD produced by the `/dream:prd` command must include these sections:

1. **Problem Statement** — 1-3 paragraphs. What problem exists, who has it, why it matters now.
2. **User Personas** — 2-3 personas with goals and pain points.
3. **Functional Requirements** — FR-001 format with description, priority, and acceptance criteria.
4. **Non-Functional Requirements** — NFR-001 format with category and measurable target.
5. **Scope Boundary** — Explicit in-scope and out-of-scope lists with rationale for exclusions.
6. **Milestones / Phases** — Phased delivery plan with FR references and deliverables.
7. **Success Metrics** — Measurable targets with measurement method.
8. **Dependencies** — External dependencies with owners and timelines.
9. **Open Questions** — Unresolved items with owners and target dates, or explicit "All questions resolved" statement.

A section is **substantive** when it contains specific, actionable content — not just the template placeholder text.

---

## Status Field

Every PRD must include a `Status` field at the top, immediately after the title.

- New PRDs default to: `Status: Draft — Awaiting Approval`
- The status is updated manually by the document owner as it progresses through review.

---

## Functional Requirement Format

```
### FR-001: [Requirement Name]

**Description:** [What the product must do — observable behavior]

**Priority:** Must | Should | Could

**Acceptance Criteria:**
- [ ] [Observable, testable condition]
- [ ] [Another condition]
```

Rules:
- IDs are sequential: FR-001, FR-002, FR-003...
- Priority uses MoSCoW: Must (required for launch), Should (expected), Could (nice to have)
- Each acceptance criterion must be independently testable and describe observable behavior
- One behavior per criterion — no "and" combining two behaviors

---

## Non-Functional Requirement Format

```
### NFR-001: [Category]

**Description:** [What quality attribute is required]

**Measurable Target:** [Specific, testable threshold]
```

Categories: Performance, Security, Scalability, Accessibility, Reliability, Compliance.

Measurable targets must be specific: "page load < 2s at P95" not "should be fast."

---

## Abstraction Boundary

PRDs describe *what* the product must do, not *how* to build it.

**Do NOT include:**
- File paths (`src/components/foo.tsx`)
- Line numbers
- Code patterns (hook names, event handlers, state management)
- Implementation instructions ("call X before Y")
- "Files to change" sections
- Database schema or API endpoint definitions

**Do include:**
- Observable user behavior ("user sees a confirmation dialog")
- Measurable outcomes ("search returns results within 2 seconds")
- Business rules ("discounts apply only to orders over $50")
- Data requirements at a conceptual level ("the system stores user preferences")

Codebase context from discovery *informs* requirements but stays in DISCOVERY.md.

---

## Quality Checklist

A PRD is ready for handoff when:

- [ ] All 9 sections are present and substantive
- [ ] Status field is set
- [ ] Every FR has an ID, description, priority, and at least one acceptance criterion
- [ ] Every NFR has a category and measurable target
- [ ] Scope boundary includes at least one out-of-scope item with rationale
- [ ] No implementation details leak into requirements (abstraction boundary respected)
- [ ] Success metrics have specific targets, not vague aspirations
- [ ] Open questions have owners and target dates, or are explicitly resolved
