---
description: Produce a client-shareable PRD from a plain-language feature description
argument-hint: "[feature description]"
allowed-tools:
  - Read
  - Write
  - Glob
  - "Bash(python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py:*)"
  - AskUserQuestion
  - ToolSearch
model: sonnet
---

# /dream:prd

Produce a client-shareable PRD from a plain-language feature description. The output is ready to share with stakeholders without editing.

---

## Flow

### 1. Input Resolution

- If an argument is provided: use it as the feature description.
- If no argument: ask the user to describe the feature they want to specify.

> **Deferred tool note:** Before calling `AskUserQuestion` for the first time, call `ToolSearch` with query `"select:AskUserQuestion"` to load the tool schema.

### 2. Discovery Phase (Hybrid)

Load `${CLAUDE_PLUGIN_ROOT}/references/discovery-questions.md`.

Present the **core questions** (1-5) as a single batch. Do NOT walk through them one at a time — present all core questions together and wait for the user to answer.

Example presentation:

> Before writing the PRD, I need to understand the problem space. Please answer these questions:
>
> 1. **The Problem** — What problem are we solving? Describe it without mentioning any solution.
> 2. **The Stakes** — What happens if we don't solve this? Who is affected?
> 3. **Success Definition** — If this ships and works perfectly, what changes in 6 months?
> 4. **Non-Goals** — What are we explicitly NOT trying to achieve?
> 5. **Constraints** — Any hard deadlines, budget limits, tech requirements, or compliance needs? (Skip if not relevant.)

After receiving answers:
- If answers surface context relevant to a **situational question** (Prior Art, Stakeholders, Existing Context), ask targeted follow-ups for those specific questions only.
- If the user's initial feature description already covers some core questions, acknowledge the existing answers and only ask about gaps.

### 3. Authoring Phase

Load these references:
- `${CLAUDE_PLUGIN_ROOT}/references/prd-template.md` — canonical format
- `${CLAUDE_PLUGIN_ROOT}/skills/prd-format.md` — format rules
- `${CLAUDE_PLUGIN_ROOT}/references/facilitation-prompts.md` — section guidance

Pre-fill PRD sections using discovery answers (see the mapping table in `discovery-questions.md`).

For sections where the discovery answers provide insufficient input:
- Use the facilitation prompts to ask **targeted follow-ups** for those specific sections only.
- Do NOT ask the user to fill in every section — use judgment to infer reasonable content from context and flag assumptions.

Produce the full PRD in template format with:
- `Status: Draft — Awaiting Approval` at the top
- All 9 sections populated
- FR-001 sequential numbering for functional requirements
- NFR-001 sequential numbering for non-functional requirements
- No implementation details (respect the abstraction boundary)

### 4. Validation Gate

Run the validation script in draft mode first:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py <path> --type prd --draft --json
```

- If score < 50 (draft threshold): display findings, re-draft failing sections, re-validate.

Then run full validation:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate.py <path> --type prd --verbose --json
```

- If score >= 70: **PASS** — present the PRD to the user.
- If score < 70: display findings as warnings, present to user with note: "PRD has gaps — consider addressing before sharing."

### 5. Save

- Save to `docs/prds/[feature-slug]-prd.md`
- Create `docs/prds/` directory if it does not exist: `mkdir -p docs/prds`
- Derive the feature slug from the feature description (lowercase, hyphens, no special characters)
- Confirm the save path to the user

---

## WHAT NOT TO DO

- Do NOT walk through all questions serially one at a time — batch the core questions.
- Do NOT include implementation details in the PRD (file paths, code patterns, database schemas).
- Do NOT skip the validation gate.
- Do NOT produce a PRD without the Status field.
- Do NOT ask the user to fill in every section individually — use discovery answers and inference, then ask about gaps.
- Do NOT modify any existing files — this command only creates new PRDs.
