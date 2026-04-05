# TDD Cycle Examples

Concrete RED-GREEN-REFACTOR examples in three languages. Each is minimal and realistic.

---

## Example 1: Bug Fix — TypeScript

**Scenario:** `validateEmail('')` returns `true` when it should return `false`.

### RED

```typescript
// src/validation/__tests__/validateEmail.test.ts
import { validateEmail } from '../validateEmail';

describe('validateEmail', () => {
  it('should return false for an empty string', () => {
    expect(validateEmail('')).toBe(false);
  });
});
```

```
$ npm test src/validation/__tests__/validateEmail.test.ts

FAIL  validateEmail
  ✕ should return false for an empty string
    Expected: false
    Received: true
```

RED confirmed: failure matches the missing behavior.

### GREEN

```typescript
// src/validation/validateEmail.ts
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateEmail(email: string): boolean {
  if (email.trim() === '') return false;
  return EMAIL_REGEX.test(email);
}
```

```
$ npm test
Tests: 47 passed, 0 failed
```

GREEN confirmed.

### REFACTOR

Implementation is clean. No changes needed.

---

## Example 2: New Feature — Python

**Scenario:** Validate incoming webhook payloads — must contain `event_type` (from allowed set) and `timestamp`.

### RED

```python
# tests/test_webhook_validation.py
import pytest
from app.validation import validate_webhook_payload

ALLOWED_EVENTS = {'user.created', 'user.deleted', 'order.placed'}

def test_valid_payload_passes():
    payload = {'event_type': 'user.created', 'timestamp': '2025-01-01T00:00:00Z'}
    assert validate_webhook_payload(payload, ALLOWED_EVENTS) is True

def test_missing_event_type_fails():
    payload = {'timestamp': '2025-01-01T00:00:00Z'}
    with pytest.raises(ValueError, match="Missing required field: event_type"):
        validate_webhook_payload(payload, ALLOWED_EVENTS)

def test_unknown_event_type_fails():
    payload = {'event_type': 'unknown.event', 'timestamp': '2025-01-01T00:00:00Z'}
    with pytest.raises(ValueError, match="Unknown event_type"):
        validate_webhook_payload(payload, ALLOWED_EVENTS)
```

```
$ pytest tests/test_webhook_validation.py -v
FAILED test_valid_payload_passes - assert None is True
FAILED test_missing_event_type_fails - DID NOT RAISE ValueError
FAILED test_unknown_event_type_fails - DID NOT RAISE ValueError
```

RED confirmed: all tests fail for expected reasons (function returns None / doesn't raise).

### GREEN

```python
# app/validation.py
def validate_webhook_payload(payload: dict, allowed_events: set) -> bool:
    for field in ('event_type', 'timestamp'):
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    if payload['event_type'] not in allowed_events:
        raise ValueError(f"Unknown event_type: {payload['event_type']}")
    return True
```

```
$ pytest
63 passed in 0.84s
```

GREEN confirmed.

### REFACTOR

Extract required fields as a constant:

```python
REQUIRED_FIELDS = ('event_type', 'timestamp')

def validate_webhook_payload(payload: dict, allowed_events: set) -> bool:
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
    if payload['event_type'] not in allowed_events:
        raise ValueError(f"Unknown event_type: {payload['event_type']}")
    return True
```

```
$ pytest
63 passed in 0.82s
```

REFACTOR confirmed.

---

## Example 3: New Feature — Go

**Scenario:** Health check handler — `{"status": "ok"}` with 200 when healthy, `{"status": "degraded", "reason": "..."}` with 503 when degraded.

### RED

```go
// internal/handlers/health_test.go
func TestHealthHandler_Healthy(t *testing.T) {
    checker := &mockChecker{healthy: true}
    handler := handlers.NewHealthHandler(checker)

    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    rec := httptest.NewRecorder()
    handler.ServeHTTP(rec, req)

    if rec.Code != http.StatusOK {
        t.Errorf("expected 200, got %d", rec.Code)
    }
    var body map[string]string
    json.NewDecoder(rec.Body).Decode(&body)
    if body["status"] != "ok" {
        t.Errorf("expected ok, got %s", body["status"])
    }
}

func TestHealthHandler_Degraded(t *testing.T) {
    checker := &mockChecker{healthy: false, reason: "database unreachable"}
    handler := handlers.NewHealthHandler(checker)

    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    rec := httptest.NewRecorder()
    handler.ServeHTTP(rec, req)

    if rec.Code != http.StatusServiceUnavailable {
        t.Errorf("expected 503, got %d", rec.Code)
    }
}
```

```
$ go test ./internal/handlers/...
./health_test.go:14:14: undefined: handlers.NewHealthHandler
FAIL [build failed]
```

RED confirmed: function doesn't exist yet.

### GREEN

```go
// internal/handlers/health.go
type HealthChecker interface {
    Check() (bool, string)
}

type HealthHandler struct {
    checker HealthChecker
}

func NewHealthHandler(checker HealthChecker) *HealthHandler {
    return &HealthHandler{checker: checker}
}

func (h *HealthHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    healthy, reason := h.checker.Check()
    w.Header().Set("Content-Type", "application/json")
    if healthy {
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
        return
    }
    w.WriteHeader(http.StatusServiceUnavailable)
    json.NewEncoder(w).Encode(map[string]string{"status": "degraded", "reason": reason})
}
```

```
$ go test ./...
ok  internal/handlers  0.003s
All tests passed.
```

GREEN confirmed.

### REFACTOR

Extract JSON response helper:

```go
func writeJSON(w http.ResponseWriter, status int, body any) {
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(body)
}
```

```
$ go test ./...
All tests passed.
```

REFACTOR confirmed.
