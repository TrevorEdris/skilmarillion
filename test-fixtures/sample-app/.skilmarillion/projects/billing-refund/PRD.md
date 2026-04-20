---
title: Billing Refund Flow
slug: billing-refund
status: Approved
---

# PRD — Billing Refund Flow

**Status:** Approved — 2026-04-20

---

## Problem Statement

Sample-app customers who are charged in error have no way to request a refund and our support operators have no workflow to approve or deny those requests. Every refund today is handled by direct database writes against the `subscriptions` table, which is error-prone, leaves no audit trail, and blocks us from reporting on refund volume. Support has absorbed a growing share of engineering time — three incidents last quarter traced back to hand-edited refund rows — and finance cannot reconcile refunds against Stripe without a structured record.

This matters now because customer-success is scaling, our new finance lead requires a weekly refund reconciliation report by end of Q2 2026, and a pending SOC2 control demands that every refund decision be attributable to a named operator.

---

## User Personas

### Casey — End Customer

- **Goals:**
  - Submit a refund request for a specific charge without emailing support
  - See the status of a submitted request (pending / approved / denied)
- **Pain Points:**
  - Must email support and wait days for a human response
  - No visibility into whether the request was received

### Riley — Support Operator

- **Goals:**
  - Review a queue of pending refund requests and act on each one
  - Capture a reason when denying a request so the customer understands the outcome
- **Pain Points:**
  - Today patches refund state by running SQL UPDATE statements by hand
  - Cannot prove to finance who approved which refund

### Dana — Finance Analyst

- **Goals:**
  - Reconcile refund totals against Stripe payouts weekly
  - Export a structured refund ledger for SOC2 evidence
- **Pain Points:**
  - Today re-creates the ledger in a spreadsheet from Slack threads
  - No confidence the spreadsheet matches the real ledger

---

## Functional Requirements

### FR-001: Customer Requests a Refund

**Description:** Casey can submit a refund request tied to their own user ID, specifying an amount in cents. The system records the request with status `pending`.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Submitting a valid user ID and positive amount stores a refund row with status `pending`
- [ ] Each stored refund has a unique, server-assigned ID

---

### FR-002: Operator Approves a Refund

**Description:** Riley can approve a pending refund by its ID. The refund's status transitions from `pending` to `approved` and becomes visible in the ledger.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Approving a pending refund transitions status to `approved`
- [ ] Approving an already-approved or denied refund is rejected with a clear error

---

### FR-003: Operator Denies a Refund With a Reason

**Description:** Riley can deny a pending refund, supplying a reason string. The refund transitions to `denied` and the reason is stored for the customer and for audit.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Denying a pending refund transitions status to `denied`
- [ ] The provided denial reason is persisted on the refund row

---

### FR-004: Refund State Transitions Emit Events

**Description:** Every status transition (created, approved, denied) publishes a typed event so downstream ledgers and notifications stay in sync.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Creating a refund emits a `RefundCreated` event
- [ ] Approving or denying a refund emits `RefundApproved` or `RefundDenied`, respectively

---

### FR-005: HTTP API Surface

**Description:** An authenticated HTTP API exposes the create, approve, and deny operations for refunds so the customer and operator UIs can call them.

**Priority:** Must

**Acceptance Criteria:**
- [ ] `POST /refunds` creates a refund and returns the stored row
- [ ] `POST /refunds/{id}/approve` and `POST /refunds/{id}/deny` drive the state transitions

---

### FR-006: Unknown Refund IDs Return a Typed Error

**Description:** Any operation that targets a refund by ID must reject unknown IDs with a stable, typed error so API clients can render a clear message.

**Priority:** Must

**Acceptance Criteria:**
- [ ] Unknown IDs passed to approve/deny return a `not found` error
- [ ] The HTTP layer maps that error to HTTP 404

---

## Non-Functional Requirements

### NFR-001: Performance

**Description:** API responses for refund operations must feel instant in the operator console.

**Measurable Target:** P95 latency under 200 ms for each refund endpoint when backed by the in-memory repo fixture.

---

### NFR-002: Auditability

**Description:** Every refund decision must be attributable to the operator who made it and retained for audit.

**Measurable Target:** 100% of approve/deny operations emit an event with operator identity; events retained for 13 months.

---

### NFR-003: Reliability

**Description:** Refund endpoints must not drop state under operator retry.

**Measurable Target:** Duplicate approve/deny calls for the same refund produce deterministic outcomes (idempotent) and never corrupt the stored row.

---

## Scope Boundary

### In Scope

- Customer-initiated refund request
- Operator approval and denial with reason
- Typed events on every state transition
- Authenticated HTTP API for the three operations

### Out of Scope

- Persistent storage backend (Postgres / SQLite) — in-memory only for the fixture; durable storage arrives in a later phase
- Stripe payout orchestration — finance reconciles manually until the ledger integration lands
- Customer-facing email notifications — deferred to the notifications workstream
- Multi-currency support — USD-only for the initial release

---

## Milestones / Phases

### Milestone 1: Refund Data & Events

**Includes:** FR-001, FR-002, FR-003, FR-004, FR-006

**Deliverable:** The domain layer can create, approve, and deny refunds, emit events, and reject unknown IDs — all verified by unit tests against the in-memory repo.

**Depends on:** Nothing — greenfield package inside `internal/billing`.

### Milestone 2: HTTP API

**Includes:** FR-005

**Deliverable:** Authenticated HTTP endpoints drive the three refund operations and map `ErrNotFound` to HTTP 404, exercised by handler tests.

**Depends on:** Milestone 1.

---

## Success Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Operator refund handle time | < 2 minutes per request | Operator console analytics |
| Support tickets citing "refund stuck" | reduced by 70% | Helpdesk tag report |
| SOC2 evidence coverage for refunds | 100% | Audit event query |
| Finance reconciliation errors per week | 0 | Finance weekly report |

---

## Dependencies

- **Auth service:** Operator identity claim must be on the request context — owned by the platform team, available today.
- **Event bus stub:** In-memory event recorder exists in the sample-app fixture; no external broker needed for this scope.
- **Design:** Operator console wireframes — owned by design, needed before Milestone 2 ships.

---

## Open Questions

| Question | Owner | Target Date |
|----------|-------|-------------|
| Do we need partial refunds in v1 or only full-amount? | Product | 2026-05-01 |
| Should the denial reason be free-text or picked from a code list? | Support lead | 2026-05-08 |
