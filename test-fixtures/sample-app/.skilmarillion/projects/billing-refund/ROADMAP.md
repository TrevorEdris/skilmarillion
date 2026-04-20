---
project: billing-refund
paired_prd: PRD.md
status: Active
---

# ROADMAP — Billing Refund Flow

## Current Status

- **Phase:** 1 — Refund Data & Events
- **Wave:** 1.1
- **Last Updated:** 2026-04-20

---

## Philosophy

Phases map 1:1 with PRD milestones. Each phase decomposes into Waves; each Wave decomposes into Wave-Agents (`W{N}{letter}`) whose writes are disjoint so they can execute in parallel. Paired with `PRD.md` (FR-001..FR-006, NFR-001..NFR-003).

---

## Discovery Summary

- **Entry points:** `cmd/sample-app/main.go`, `internal/http/router.go`, `internal/billing/`
- **Layout:** domain packages under `internal/`, in-memory event recorder under `pkg/events/`
- **Conventions:** map-backed repo + sentinel `ErrNotFound`, table-driven tests, typed event structs
- **Hotspots:** `subscription.go` and `router.go` are hot — refund work uses dedicated new files to avoid collisions

Full notes: `DISCOVERY.md`.

---

## Phase 1 — Refund Data & Events

**Entry:** Nothing · **Exit:** Domain layer creates/approves/denies refunds, emits typed events, rejects unknown IDs. Verified by `go test ./internal/billing/...`.

### Wave 1.1

> Wave-agents below run in parallel — writes are disjoint.

#### W1a — Refund Repository

- **Scope:** `Refund` type and map-backed repository with create/approve/deny and `ErrNotFound`
- **Touches:**
  - `internal/billing/refund.go`
  - `internal/billing/refund_test.go`
- **Depends on:** Nothing
- **Acceptance:** AC-W1a.1 pending → approved; AC-W1a.2 denial records reason; AC-W1a.3 unknown IDs return `ErrNotFound`
- **Spec:** `specs/SPEC-W1a-refund-repo.md`

#### W1b — Refund Events

- **Scope:** Typed `RefundCreated` / `RefundApproved` / `RefundDenied` events and a publisher helper
- **Touches:**
  - `internal/billing/refund_events.go`
  - `internal/billing/refund_events_test.go`
- **Depends on:** Nothing (event types are self-contained; repo integration happens in Phase 2 via W2a)
- **Acceptance:** AC-W1b.1 each event type carries refund ID, operator ID, timestamp; AC-W1b.2 publisher forwards to `pkg/events.Recorder`
- **Spec:** `specs/SPEC-W1b-refund-events.md`

**Deliverable:** `go test ./internal/billing/...` green with repo + events available as building blocks.

---

## Phase 2 — HTTP API

**Entry:** Phase 1 complete · **Exit:** Authenticated endpoints drive refund state transitions and map `ErrNotFound` to HTTP 404.

### Wave 2.1

> Single wave-agent — HTTP wiring must serialize after the domain layer.

#### W2a — Refund HTTP API

- **Scope:** `POST /refunds`, `POST /refunds/{id}/approve`, `POST /refunds/{id}/deny` handlers that call the repo and publish events
- **Touches:**
  - `internal/billing/refund_api.go`
  - `internal/billing/refund_api_test.go`
- **Depends on:** W1a, W1b
- **Acceptance:** AC-W2a.1 create endpoint returns 200 with refund body; AC-W2a.2 approve/deny endpoints drive state and emit events; AC-W2a.3 unknown IDs return HTTP 404
- **Spec:** `specs/SPEC-W2a-refund-api.md`

**Deliverable:** HTTP handlers exercised by handler tests; sample-app binary serves the refund routes.

---

## Cross-Cutting Concerns

- **Auth:** `auth.OperatorFromContext` already in middleware — consumed by W1b and W2a without modification.
- **Events:** `pkg/events.Recorder` is the in-memory bus; W1b publishes to it, W2a invokes W1b's publisher.
- **No storage migration:** everything is in-memory for this roadmap; durable storage is a later roadmap.

---

## Dependency Summary

| Wave-Agent | Depends on |
|------------|------------|
| W1a | Nothing |
| W1b | Nothing |
| W2a | W1a, W1b |

---

## Independence Check

| Wave | Collision? | Notes |
|------|-----------|-------|
| 1.1 (W1a + W1b) | No | Disjoint files: `refund.go` + `refund_test.go` vs `refund_events.go` + `refund_events_test.go` |
| 2.1 (W2a only) | No | Single wave-agent; depends on 1.1 outputs by import |

`collisions_resolved: 0`

---

## Spec Index

| Spec ID | Wave | Scope | Status |
|---------|------|-------|--------|
| W1a | 1.1 | Refund repository | PENDING |
| W1b | 1.1 | Refund events | PENDING |
| W2a | 2.1 | Refund HTTP API | PENDING |
