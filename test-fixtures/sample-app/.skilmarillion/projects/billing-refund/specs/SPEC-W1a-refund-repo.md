---
spec_id: W1a
wave: 1.1
paired_prd: PRD.md
depends_on: []
touches:
  - internal/billing/refund.go
  - internal/billing/refund_test.go
status: PENDING
---

# SPEC-W1a — Refund Repository

**Phase:** 1 — Refund Data Layer
**Wave:** 1.1
**Spec ID:** W1a
**Depends on:** Nothing

---

## Problem Statement

The billing service stores subscriptions but has no way to record or query refund requests. This wave-agent introduces a `Refund` data type and a repository for create/read/update operations. Downstream wave-agents (`W1b` for events, `W2a` for the API) depend on this contract being in place.

---

## Acceptance Criteria

- AC-W1a.1: Given a valid user and amount, when `CreateRefund` is called, then a `Refund` row is stored with status `pending`.
- AC-W1a.2: Given a `pending` refund, when `MarkApproved` is called with that refund's ID, then the row's status updates to `approved`.
- AC-W1a.3: Given a `pending` refund, when `MarkDenied` is called with a denial reason, then the row's status updates to `denied`.
- AC-W1a.3b: Given a `MarkDenied` call has succeeded, when the refund is read back, then the recorded `DenialReason` matches the input.
- AC-W1a.4: Given a refund ID that does not exist, when any update method is called, then the call returns `ErrNotFound` and no state changes.

---

## Target Repo

`test-fixtures/sample-app/`

---

## Files to Touch

- `internal/billing/refund.go` [NEW] — `Refund` type, `RefundRepo` interface and in-memory implementation
- `internal/billing/refund_test.go` [NEW] — table-driven tests for all four ACs

---

## Structure

Single phase. No internal slices. Linear step list.

---

## Ordered Implementation Steps

### Step 1 (RED) — Write failing test for CreateRefund

**File:** `internal/billing/refund_test.go`

**Action:** Create file. Add test `TestRefundRepo_CreateRefund_StoresPending` that constructs a fresh repo, calls `CreateRefund("user-1", 1000)`, and asserts the returned refund has `Status == "pending"`. Compile will fail (no `Refund` type).

**Verification:** `go test ./internal/billing/...` — expect compile error referencing missing symbols.

### Step 2 (GREEN) — Implement minimal Refund + RefundRepo

**File:** `internal/billing/refund.go`

**Action:** Define `Refund` struct (`ID`, `UserID`, `AmountCents`, `Status`, `DenialReason`). Define `RefundRepo` with map-backed `CreateRefund`. Status defaults to `"pending"`.

**Verification:** `go test ./internal/billing/...` — Step 1 test passes.

### Step 3 (RED) — Test for MarkApproved

**File:** `internal/billing/refund_test.go`

**Action:** Add `TestRefundRepo_MarkApproved_UpdatesStatus`. Create a refund, call `MarkApproved(id)`, assert status is `"approved"`.

**Verification:** `go test ./internal/billing/...` — expect failure (method missing).

### Step 4 (GREEN) — Implement MarkApproved

**File:** `internal/billing/refund.go`

**Action:** Add `MarkApproved(id string) error` that looks up the refund and sets `Status = "approved"`.

**Verification:** `go test ./internal/billing/...` — Steps 1+3 pass.

### Step 5 (RED) — Test for MarkDenied with reason

**File:** `internal/billing/refund_test.go`

**Action:** Add `TestRefundRepo_MarkDenied_RecordsReason`. Create refund, call `MarkDenied(id, "duplicate charge")`, assert status `"denied"` and `DenialReason == "duplicate charge"`.

**Verification:** `go test ./internal/billing/...` — expect failure.

### Step 6 (GREEN) — Implement MarkDenied

**File:** `internal/billing/refund.go`

**Action:** Add `MarkDenied(id, reason string) error`.

**Verification:** `go test ./internal/billing/...` — all three GREEN tests pass.

### Step 7 (RED) — Test for ErrNotFound on unknown ID

**File:** `internal/billing/refund_test.go`

**Action:** Add `TestRefundRepo_NotFound_ReturnsError`. Call `MarkApproved("missing")` and `MarkDenied("missing", "x")`. Assert both return `ErrNotFound`.

**Verification:** `go test ./internal/billing/...` — expect failure (no `ErrNotFound`).

### Step 8 (GREEN) — Define ErrNotFound + guard updates

**File:** `internal/billing/refund.go`

**Action:** Define `var ErrNotFound = errors.New("refund: not found")`. Update both mutators to return it when the ID is unknown.

**Verification:** `go test ./internal/billing/...` — all four ACs green.

### Step 9 (REFACTOR) — Extract status-mutation helper

**File:** `internal/billing/refund.go`

**Action:** Pull common lookup-and-mutate logic into private `mutate(id, fn)` helper. Behavior unchanged.

**Verification:** `go test ./internal/billing/...` — still all green; `go vet ./...` — clean.

---

## Risks & Assumptions

- **Risk:** In-memory repo is not safe for concurrent callers.
  **Likelihood:** Low (W2a is the only consumer in this phase) · **Impact:** Medium · **Mitigation:** Add `sync.Mutex` in Step 2; tests assert no panics under `t.Parallel()`.
- **Assumption:** Persistence layer is out of scope for Phase 1; durable storage arrives in Phase 2 alongside Postgres adoption.

---

## Verification Plan

- `go test ./internal/billing/...` — all tests green
- `go vet ./internal/billing/...` — no findings
- `go build ./...` — compiles
- Manual: `go doc internal/billing.RefundRepo` — confirm public interface matches AC list

---

## Out of Scope

- Persistent storage backend (Postgres / SQLite)
- Refund event emission (handled by W1b)
- HTTP endpoint for approve / deny (handled by W2a)
- UI surface (handled by W3a in a future phase)

---

## Git Strategy

**Branch:** `feat/billing-refund-repo`

**Commits:**
- `test(billing): RED for refund create/approve/deny/not-found`
- `feat(billing): GREEN refund repo with in-memory store`
- `refactor(billing): extract mutate helper`

**PR Title:** `feat(billing): add refund repo (W1a)`

**PR Body Outline:**
- Summary — what behaviors land
- Test Plan — `go test ./internal/billing/...` output
- Wave Context — link to ROADMAP wave 1.1; depends on Nothing; unblocks W1b reading the type, W2a wiring the API

---

## Traceability

| Source | Step | Notes |
|--------|------|-------|
| FR-001 (PRD) | Step 1, 2 | "user can request refund" |
| FR-002 (PRD) | Step 3, 4 | "operator can approve refund" |
| FR-003 (PRD) | Step 5, 6 | "operator can deny refund with reason" |
| FR-006 (PRD) | Step 7, 8 | "invalid refund IDs return a typed error" |
| F2 (DISCOVERY) | Step 2 | repo pattern matches existing `internal/user/repository.go` |
