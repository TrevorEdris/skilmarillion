package auth

import (
	"net/http"
	"net/http/httptest"
	"strconv"
	"testing"
	"time"
)

func TestRateLimiter(t *testing.T) {
	okHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	tests := []struct {
		name           string
		maxAttempts    int
		window         time.Duration
		requests       int
		wantLastStatus int
	}{
		{
			name:           "requests under limit pass",
			maxAttempts:    5,
			window:         1 * time.Minute,
			requests:       3,
			wantLastStatus: http.StatusOK,
		},
		{
			name:           "requests at limit get blocked",
			maxAttempts:    3,
			window:         1 * time.Minute,
			requests:       4,
			wantLastStatus: http.StatusTooManyRequests,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rl := NewRateLimiter(tt.maxAttempts, tt.window)
			defer rl.Stop()

			handler := rl.Middleware(okHandler)
			var lastStatus int
			for i := 0; i < tt.requests; i++ {
				req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
				req.RemoteAddr = "192.168.1.1:12345"
				rec := httptest.NewRecorder()
				handler.ServeHTTP(rec, req)
				lastStatus = rec.Code
			}

			if lastStatus != tt.wantLastStatus {
				t.Errorf("last status = %d, want %d", lastStatus, tt.wantLastStatus)
			}
		})
	}
}

func TestRateLimiter_IndependentIPs(t *testing.T) {
	okHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	rl := NewRateLimiter(2, 1*time.Minute)
	defer rl.Stop()

	handler := rl.Middleware(okHandler)

	// Exhaust limit for IP A
	for i := 0; i < 3; i++ {
		req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
		req.RemoteAddr = "10.0.0.1:1111"
		rec := httptest.NewRecorder()
		handler.ServeHTTP(rec, req)
	}

	// IP B should still be allowed
	req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
	req.RemoteAddr = "10.0.0.2:2222"
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("independent IP got status %d, want %d", rec.Code, http.StatusOK)
	}
}

func TestRateLimiter_Integration429(t *testing.T) {
	okHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	rl := NewRateLimiter(3, 1*time.Minute)
	defer rl.Stop()

	handler := rl.Middleware(okHandler)

	// Send maxAttempts+1 requests from same IP
	var statuses []int
	for i := 0; i < 4; i++ {
		req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
		req.RemoteAddr = "172.16.0.1:9999"
		rec := httptest.NewRecorder()
		handler.ServeHTTP(rec, req)
		statuses = append(statuses, rec.Code)
	}

	// First 3 should pass
	for i := 0; i < 3; i++ {
		if statuses[i] != http.StatusOK {
			t.Errorf("request %d: got %d, want %d", i+1, statuses[i], http.StatusOK)
		}
	}

	// 4th should be 429
	if statuses[3] != http.StatusTooManyRequests {
		t.Errorf("request 4: got %d, want %d", statuses[3], http.StatusTooManyRequests)
	}
}

func TestRateLimiter_RetryAfterHeader(t *testing.T) {
	okHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	rl := NewRateLimiter(1, 1*time.Minute)
	defer rl.Stop()

	handler := rl.Middleware(okHandler)

	// First request passes
	req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
	req.RemoteAddr = "10.0.0.99:5555"
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	// Second request should be 429 with Retry-After
	req = httptest.NewRequest(http.MethodPost, "/auth/login", nil)
	req.RemoteAddr = "10.0.0.99:5555"
	rec = httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusTooManyRequests {
		t.Fatalf("got status %d, want 429", rec.Code)
	}

	retryAfter := rec.Header().Get("Retry-After")
	if retryAfter == "" {
		t.Fatal("Retry-After header missing on 429 response")
	}

	seconds, err := strconv.Atoi(retryAfter)
	if err != nil {
		t.Fatalf("Retry-After header %q is not a valid integer: %v", retryAfter, err)
	}
	if seconds <= 0 || seconds > 61 {
		t.Errorf("Retry-After = %d, want value between 1 and 61", seconds)
	}
}

func TestRateLimiter_WindowReset(t *testing.T) {
	okHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	rl := NewRateLimiter(2, 50*time.Millisecond)
	defer rl.Stop()

	handler := rl.Middleware(okHandler)

	// Exhaust the limit
	for i := 0; i < 3; i++ {
		req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
		req.RemoteAddr = "10.0.0.1:1111"
		rec := httptest.NewRecorder()
		handler.ServeHTTP(rec, req)
	}

	// Wait for window to expire
	time.Sleep(60 * time.Millisecond)

	// Should be allowed again
	req := httptest.NewRequest(http.MethodPost, "/auth/login", nil)
	req.RemoteAddr = "10.0.0.1:1111"
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("after window reset got status %d, want %d", rec.Code, http.StatusOK)
	}
}
