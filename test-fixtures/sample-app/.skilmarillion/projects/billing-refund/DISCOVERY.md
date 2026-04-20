# DISCOVERY — Billing Refund Flow

**Scope:** roadmap · **Last Updated:** 2026-04-20

---

## Entry Points

- `cmd/sample-app/main.go` — wires the HTTP router and starts the server
- `internal/http/router.go` — registers all HTTP routes; the refund API will register here
- `internal/billing/` — domain package for subscriptions today; refunds will co-locate here

---

## Repo Layout

```
cmd/sample-app/           # binary entry point
internal/
  billing/                # domain — subscriptions live here; refunds land alongside
    subscription.go
    subscription_test.go
  user/                   # repository pattern reference
    repository.go
    repository_test.go
  http/
    router.go
    middleware.go
pkg/
  events/                 # in-memory event recorder
    recorder.go
```

---

## Conventions

- **Repository pattern:** `internal/user/repository.go` is the canonical in-memory repo — map-backed with `sync.Mutex`, typed `ErrNotFound` sentinel. Refunds will mirror this shape.
- **Tests:** table-driven tests using `testing.T` and `t.Run`; no external test framework.
- **Errors:** sentinel errors declared at package top (`var ErrX = errors.New("pkg: message")`).
- **Events:** `pkg/events.Recorder` is the in-memory bus; handlers call `recorder.Publish(evt)` and events are typed structs.
- **HTTP:** handlers use `net/http`; JSON encode/decode via `encoding/json`; request IDs via middleware.

---

## Hotspots

- `internal/billing/subscription.go` — touched by three open branches this month; refund work must not collide. Refunds get their own files (`refund.go`, `refund_events.go`, `refund_api.go`).
- `internal/http/router.go` — concurrent registration by multiple features; refund API appends its routes in a dedicated init block.

---

## Coverage Gaps

- No prior refund concept exists in the domain — greenfield within `internal/billing/`.
- `pkg/events` has no `Refund*` event types today.
- Router has no `/refunds` prefix registered.

---

## Constraints Carried Into Planning

- In-memory storage only for this slice (matches sample-app fixture posture).
- Must not modify `subscription.go` or `user/repository.go`.
- Operator identity comes from `auth.OperatorFromContext(ctx)` already wired in middleware.
