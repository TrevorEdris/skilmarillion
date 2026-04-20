---
spec_id: W1b
wave: 1.1
paired_prd: PRD.md
depends_on: []
touches:
  - internal/billing/refund_events.go
  - internal/billing/refund_events_test.go
status: PENDING
---

# SPEC-W1b — Refund Events

**Phase:** 1 — Refund Data & Events
**Wave:** 1.1
**Spec ID:** W1b
**Depends on:** Nothing

---

## Problem Statement

Downstream consumers (ledger export, notifications, audit trail) need typed events whenever a refund is created, approved, or denied. This wave-agent defines the three event types and a publisher that forwards them through the existing `pkg/events.Recorder`. It ships independently of the repository (W1a) — the HTTP API wave-agent (W2a) will import both and connect them.

---

## Acceptance Criteria

- AC-W1b.1: Given a refund ID, operator ID, and timestamp, when `PublishCreated` is called, then a `RefundCreated` event is recorded on the shared recorder.
- AC-W1b.2: Given a refund ID, operator ID, and timestamp, when `PublishApproved` is called, then a `RefundApproved` event is recorded.
- AC-W1b.3: Given a refund ID, operator ID, timestamp, and reason, when `PublishDenied` is called, then a `RefundDenied` event carrying the reason is recorded.
- AC-W1b.4: Given a nil recorder, when any publish function is called, then it returns `ErrNoRecorder` and emits nothing.

---

## Target Repo

`test-fixtures/sample-app/`

---

## Files to Touch

- `internal/billing/refund_events.go` [NEW] — event types (`RefundCreated`, `RefundApproved`, `RefundDenied`) and publisher helpers
- `internal/billing/refund_events_test.go` [NEW] — table-driven tests covering each publisher and the nil-recorder guard

---

## Structure

Single phase. Two logical groupings in one file: event types (Steps 1–2) and publishers (Steps 3–8). Linear execution.

---

## Ordered Implementation Steps

### Step 1 (RED) — Test for RefundCreated event shape

**File:** `internal/billing/refund_events_test.go`

**Action:** Create file. Add `TestRefundCreated_CarriesFields` that constructs a `RefundCreated{RefundID: "r1", OperatorID: "op1", At: ts}` and asserts each field round-trips. Compile will fail (no type yet).

**Verification:** `go test ./internal/billing/...` — expect compile error referencing `RefundCreated`.

### Step 2 (GREEN) — Define RefundCreated struct

**File:** `internal/billing/refund_events.go`

**Action:** Create file. Declare `package billing`. Add `type RefundCreated struct { RefundID, OperatorID string; At time.Time }`.

**Verification:** `go test ./internal/billing/...` — Step 1 passes.

### Step 3 (RED) — Test PublishCreated forwards to recorder

**File:** `internal/billing/refund_events_test.go`

**Action:** Add `TestPublishCreated_RecordsEvent`. Construct a test recorder capturing events, call `PublishCreated(rec, "r1", "op1", ts)`, assert `rec.Events()` contains one `RefundCreated` with matching fields.

**Verification:** `go test ./internal/billing/...` — expect failure (missing `PublishCreated`).

### Step 4 (GREEN) — Implement PublishCreated

**File:** `internal/billing/refund_events.go`

**Action:** Add `func PublishCreated(rec Recorder, id, operatorID string, at time.Time) error`. Wrap fields into `RefundCreated` and call `rec.Publish(evt)`. Return `nil`.

**Verification:** `go test ./internal/billing/...` — Steps 1+3 pass.

### Step 5 (RED) — Test PublishApproved

**File:** `internal/billing/refund_events_test.go`

**Action:** Add `TestPublishApproved_RecordsEvent` mirroring Step 3 for the approved case.

**Verification:** `go test ./internal/billing/...` — expect failure.

### Step 6 (GREEN) — Implement RefundApproved + PublishApproved

**File:** `internal/billing/refund_events.go`

**Action:** Add `RefundApproved` struct with same fields as `RefundCreated`; add `PublishApproved` helper.

**Verification:** `go test ./internal/billing/...` — Steps 1, 3, 5 pass.

### Step 7 (RED) — Test PublishDenied carries reason

**File:** `internal/billing/refund_events_test.go`

**Action:** Add `TestPublishDenied_CarriesReason`. Call `PublishDenied(rec, "r1", "op1", ts, "duplicate charge")`, assert recorded event's `Reason` matches.

**Verification:** `go test ./internal/billing/...` — expect failure.

### Step 8 (GREEN) — Implement RefundDenied + PublishDenied

**File:** `internal/billing/refund_events.go`

**Action:** Add `RefundDenied` struct with `Reason string` plus the common fields. Add `PublishDenied(rec, id, operatorID, at, reason)` helper.

**Verification:** `go test ./internal/billing/...` — Steps 1, 3, 5, 7 pass.

### Step 9 (RED) — Test nil recorder returns ErrNoRecorder

**File:** `internal/billing/refund_events_test.go`

**Action:** Add `TestPublish_NilRecorder_ReturnsError` calling each publisher with `nil` recorder and asserting `errors.Is(err, ErrNoRecorder)` for all three.

**Verification:** `go test ./internal/billing/...` — expect failure (no `ErrNoRecorder`).

### Step 10 (GREEN) — Define ErrNoRecorder and guard publishers

**File:** `internal/billing/refund_events.go`

**Action:** Add `var ErrNoRecorder = errors.New("billing: nil events recorder")`. Each publisher returns `ErrNoRecorder` when `rec == nil`.

**Verification:** `go test ./internal/billing/...` — all ACs green.

### Step 11 (REFACTOR) — Extract shared publish helper

**File:** `internal/billing/refund_events.go`

**Action:** Collapse the three publishers onto a private `publish(rec, evt)` helper that handles the nil guard and `rec.Publish`. Each public helper constructs the event and calls `publish`.

**Verification:** `go test ./internal/billing/...` — still green; `go vet ./...` — clean.

---

## Risks & Assumptions

- **Risk:** The `Recorder` interface imported from `pkg/events` may rename `Publish` before this lands.
  **Likelihood:** Low · **Impact:** Low · **Mitigation:** Keep the helper surface narrow; one find-replace if the rename happens.
- **Assumption:** Phase 1 does not require durable event storage; the in-memory recorder is sufficient.
- **Assumption:** Timestamp is supplied by the caller (not generated in the publisher) so tests remain deterministic.

---

## Verification Plan

- `go test ./internal/billing/...` — all tests green
- `go vet ./internal/billing/...` — no findings
- `go build ./...` — compiles
- Manual: `go doc internal/billing.PublishCreated` — surface matches documented helpers

---

## Out of Scope

- Wiring events into the refund repo — W2a composes them at the API layer
- Durable event storage — future phase
- Notification templates — owned by the notifications workstream

---

## Git Strategy

**Branch:** `feat/billing-refund-events`

**Commits:**
- `test(billing): RED for refund event types + publishers`
- `feat(billing): GREEN refund event types and publish helpers`
- `refactor(billing): collapse publishers onto shared helper`

**PR Title:** `feat(billing): add refund events (W1b)`

**PR Body Outline:**
- Summary — typed events and publishers land
- Test Plan — `go test ./internal/billing/...`
- Wave Context — link to ROADMAP wave 1.1; parallel with W1a; unblocks W2a

---

## Traceability

| Source | Step | Notes |
|--------|------|-------|
| FR-004 (PRD) | Steps 1–8 | "state transitions emit events" |
| FR-006 (PRD) | Steps 9–10 | typed error for misuse (nil recorder) |
| Convention (DISCOVERY) | Step 2 | event structs follow `pkg/events` typed pattern |
