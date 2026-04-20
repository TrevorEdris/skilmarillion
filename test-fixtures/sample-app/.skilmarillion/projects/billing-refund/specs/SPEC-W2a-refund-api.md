---
spec_id: W2a
wave: 2.1
paired_prd: PRD.md
depends_on: [W1a, W1b]
touches:
  - internal/billing/refund_api.go
  - internal/billing/refund_api_test.go
status: PENDING
---

# SPEC-W2a — Refund HTTP API

**Phase:** 2 — HTTP API
**Wave:** 2.1
**Spec ID:** W2a
**Depends on:** W1a (refund repo), W1b (refund events)

---

## Problem Statement

The operator console and the customer UI both need an HTTP surface to create, approve, and deny refunds. This wave-agent wires the domain (W1a's repo) and the event publishers (W1b) behind three authenticated endpoints and maps `ErrNotFound` to HTTP 404. It is the last wave-agent in the roadmap and ships the externally visible API.

---

## Acceptance Criteria

- AC-W2a.1: Given a valid body, when `POST /refunds` is invoked, then the response is HTTP 200 and the refund is persisted with status `pending`.
- AC-W2a.2: Given a pending refund ID, when `POST /refunds/{id}/approve` is invoked, then the refund's status becomes `approved` and a `RefundApproved` event is recorded.
- AC-W2a.3: Given a pending refund ID and a denial reason, when `POST /refunds/{id}/deny` is invoked, then the refund's status becomes `denied` with the reason stored and a `RefundDenied` event is recorded.
- AC-W2a.4: Given an unknown refund ID, when approve or deny is called, then the response is HTTP 404 with a stable error body.

---

## Target Repo

`test-fixtures/sample-app/`

---

## Files to Touch

- `internal/billing/refund_api.go` [NEW] — handler struct, route registration, JSON encoding, error mapping
- `internal/billing/refund_api_test.go` [NEW] — `httptest`-based handler tests for each AC

---

## Structure

Single phase. Logical grouping inside one file: create (Steps 1–2), approve (Steps 3–4), deny (Steps 5–6), not-found mapping (Steps 7–8). Linear execution within the wave-agent.

---

## Ordered Implementation Steps

### Step 1 (RED) — Test POST /refunds returns stored refund

**File:** `internal/billing/refund_api_test.go`

**Action:** Create file. Add `TestCreateRefund_Returns200` that wires a fresh `RefundRepo`, a fake recorder, and the handler; POSTs `{"user_id":"u1","amount_cents":500}`; asserts 200 and decoded body has `status == "pending"`.

**Verification:** `go test ./internal/billing/...` — expect compile error (no handler type).

### Step 2 (GREEN) — Implement RefundHandler + Create

**File:** `internal/billing/refund_api.go`

**Action:** Create file. Declare `RefundHandler{Repo *RefundRepo; Rec Recorder}`. Implement `Create(w, r)` decoding the body, calling `Repo.CreateRefund`, publishing `RefundCreated`, and JSON-encoding the stored refund.

**Verification:** `go test ./internal/billing/...` — Step 1 passes.

### Step 3 (RED) — Test POST /refunds/{id}/approve

**File:** `internal/billing/refund_api_test.go`

**Action:** Add `TestApproveRefund_Returns200`. Seed a refund through the repo, call the approve endpoint with `{id}` path param, assert 200 and a `RefundApproved` event was recorded.

**Verification:** `go test ./internal/billing/...` — expect failure (no Approve handler).

### Step 4 (GREEN) — Implement Approve handler

**File:** `internal/billing/refund_api.go`

**Action:** Add `Approve(w, r)`. Extract `{id}` from the path, call `Repo.MarkApproved`, publish `RefundApproved`, return the updated refund.

**Verification:** `go test ./internal/billing/...` — Steps 1+3 pass.

### Step 5 (RED) — Test POST /refunds/{id}/deny with reason

**File:** `internal/billing/refund_api_test.go`

**Action:** Add `TestDenyRefund_RecordsReason`. Seed a refund, POST with `{"reason":"duplicate charge"}`, assert 200, status `denied`, reason persisted, and a `RefundDenied` event was recorded carrying the reason.

**Verification:** `go test ./internal/billing/...` — expect failure.

### Step 6 (GREEN) — Implement Deny handler

**File:** `internal/billing/refund_api.go`

**Action:** Add `Deny(w, r)` decoding the reason, calling `Repo.MarkDenied`, publishing `RefundDenied`.

**Verification:** `go test ./internal/billing/...` — Steps 1, 3, 5 pass.

### Step 7 (RED) — Test unknown ID returns 404

**File:** `internal/billing/refund_api_test.go`

**Action:** Add `TestApproveDeny_UnknownID_Returns404`. Call approve and deny with a missing ID, assert HTTP 404 and a body with `{"error":"not_found"}`.

**Verification:** `go test ./internal/billing/...` — expect failure (status mapping missing).

### Step 8 (GREEN) — Map ErrNotFound to HTTP 404

**File:** `internal/billing/refund_api.go`

**Action:** Add a private `writeError(w, err)` helper that maps `errors.Is(err, ErrNotFound)` to 404 and everything else to 500. Wire approve and deny through it.

**Verification:** `go test ./internal/billing/...` — all four ACs green.

### Step 9 (REFACTOR) — Extract decodeBody + route registration

**File:** `internal/billing/refund_api.go`

**Action:** Pull JSON body decoding into a private `decodeBody[T]` generic helper; add `(h *RefundHandler) Register(mux *http.ServeMux)` that wires `/refunds`, `/refunds/{id}/approve`, `/refunds/{id}/deny`. Handlers stay behavior-equivalent.

**Verification:** `go test ./internal/billing/...` — still green; `go vet ./internal/billing/...` — clean.

---

## Risks & Assumptions

- **Risk:** The sample-app's router uses path variables in a way that differs from `http.ServeMux`'s go1.22 pattern syntax.
  **Likelihood:** Low · **Impact:** Low · **Mitigation:** Keep path parsing inside `Register` so the adapter is swappable.
- **Risk:** Operator identity extraction from context may not be wired in tests.
  **Likelihood:** Medium · **Impact:** Low · **Mitigation:** Tests inject a `context.WithValue` seeded with a known operator; production relies on the existing middleware.
- **Assumption:** W1a and W1b have already landed; the imports resolve at compile time.

---

## Verification Plan

- `go test ./internal/billing/...` — all tests green
- `go vet ./internal/billing/...` — no findings
- `go build ./...` — compiles
- Manual: start the sample-app binary and `curl -X POST /refunds -d '{"user_id":"u1","amount_cents":500}'` — observe 200 and a stored refund

---

## Out of Scope

- Rate limiting or quota enforcement — handled by the API gateway
- Stripe integration — future roadmap
- Pagination or list endpoints — only the three state-changing operations ship here

---

## Git Strategy

**Branch:** `feat/billing-refund-api`

**Commits:**
- `test(billing): RED for refund HTTP handlers`
- `feat(billing): GREEN refund create/approve/deny handlers`
- `refactor(billing): extract decodeBody + Register`

**PR Title:** `feat(billing): add refund HTTP API (W2a)`

**PR Body Outline:**
- Summary — three endpoints wire domain + events
- Test Plan — `go test ./internal/billing/...` plus manual `curl`
- Wave Context — link to ROADMAP wave 2.1; depends on W1a + W1b; closes Phase 2

---

## Traceability

| Source | Step | Notes |
|--------|------|-------|
| FR-005 (PRD) | Steps 1–8 | HTTP API surface |
| FR-001 (PRD) | Steps 1, 2 | create endpoint persists pending refund |
| FR-002 (PRD) | Steps 3, 4 | approve endpoint drives status |
| FR-003 (PRD) | Steps 5, 6 | deny endpoint stores reason |
| FR-004 (PRD) | Steps 2, 4, 6 | each handler invokes the W1b publisher |
| FR-006 (PRD) | Steps 7, 8 | unknown ID → HTTP 404 |
| Convention (DISCOVERY) | Step 9 | routing follows `internal/http/router.go` pattern |
