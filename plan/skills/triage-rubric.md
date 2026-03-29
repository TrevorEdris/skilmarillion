---
name: triage-rubric
user-invocable: false
allowed-tools: []
model: haiku
tags: [planning, triage]
---

# Triage Rubric

Use this rubric to classify a task by size and risk before routing it through the appropriate workflow. When uncertain, apply the over-classification rule.

---

### TRIVIAL

A single-line or single-config change with no new behavior. The entire change fits in one edit and requires no design decisions.

**Examples:**
- Fix a typo in a README or user-facing string
- Update a hardcoded constant or configuration value
- Add a missing import or remove an unused variable

---

### SMALL

Touches 1–3 files to fix or enhance existing behavior. No new user-visible capabilities are introduced. The change is contained within an already-understood system boundary.

**Examples:**
- Add a nil/null check to prevent a crash in an existing function
- Extend an existing API response with one additional field
- Improve an error message to include context

---

### FEATURE

Introduces at least one new vertical behavior or user-visible capability. May span multiple files or introduce a new endpoint, route, screen, or event. Requires some design consideration but fits within a single, coherent deliverable.

**Examples:**
- Add email notification on password change
- Implement a new OAuth2 login provider
- Add a search filter to an existing list view

---

### EPIC

Spans multiple features or requires decomposition before any spec can be written. No single deliverable captures the full scope. Must be broken into FEATURE-sized chunks first.

**Examples:**
- Build a multi-tenant billing system
- Migrate the authentication layer to a new provider across all services
- Redesign the data model for a core domain object

---

### LOW

Internal change, easy to revert. No user-facing impact. Failure is contained and recoverable without a hotfix.

**Examples:**
- Refactor internal helper function
- Update a developer-only config file
- Fix a typo in an internal log message

---

### MODERATE

User-facing change but recoverable. A rollback is possible. Failures affect users but do not cause data loss or security exposure.

**Examples:**
- Change a UI label or error message visible to users
- Add a new optional field to a public API response
- Enable a new non-critical notification

---

### HIGH

Touches payment, authentication, data migration, or any change that is hard to revert. Failures may cause data loss, security exposure, or require a coordinated rollback across systems.

**Examples:**
- Modify payment processing logic
- Change session token storage or auth middleware
- Run a database migration that alters existing rows

---

## Over-Classification Rule

When uncertain between two sizes, classify at the **larger** category. A SMALL misclassified as TRIVIAL skips a spec. A FEATURE misclassified as SMALL skips architecture review. The cost of over-classifying is a slightly heavier process; the cost of under-classifying is missed risk.

Answer these four questions. If any answer is YES, move up one size:

1. Does this introduce new user-visible behavior that does not currently exist?
2. Does this touch more than 3 files?
3. Does this introduce a new endpoint, route, screen, or domain event?
4. Does this span multiple features or require multiple independent deliverables?

If two or more answers are YES, move up two sizes (e.g., SMALL → FEATURE, not just SMALL → FEATURE).
