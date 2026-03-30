package auth

import (
	"fmt"
	"net"
	"net/http"
	"sync"
	"time"
)

type entry struct {
	count     int
	windowStart time.Time
}

// RateLimiter provides per-IP fixed-window rate limiting.
type RateLimiter struct {
	maxAttempts int
	window      time.Duration
	mu          sync.Mutex
	entries     map[string]*entry
	stopCh      chan struct{}
}

// NewRateLimiter creates a rate limiter that allows maxAttempts requests per
// IP within the given window duration.
func NewRateLimiter(maxAttempts int, window time.Duration) *RateLimiter {
	if maxAttempts <= 0 {
		panic("ratelimit: maxAttempts must be positive")
	}
	if window <= 0 {
		panic("ratelimit: window must be positive")
	}
	rl := &RateLimiter{
		maxAttempts: maxAttempts,
		window:      window,
		entries:     make(map[string]*entry),
		stopCh:      make(chan struct{}),
	}
	go rl.cleanup()
	return rl
}

// Middleware returns an http.Handler that enforces the rate limit before
// calling next. Returns 429 with Retry-After header when the limit is exceeded.
func (rl *RateLimiter) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := extractIP(r)

		rl.mu.Lock()
		now := time.Now()
		e, ok := rl.entries[ip]
		if !ok || now.Sub(e.windowStart) >= rl.window {
			rl.entries[ip] = &entry{count: 1, windowStart: now}
			rl.mu.Unlock()
			next.ServeHTTP(w, r)
			return
		}

		if e.count >= rl.maxAttempts {
			remaining := rl.window - now.Sub(e.windowStart)
			rl.mu.Unlock()
			w.Header().Set("Retry-After", fmt.Sprintf("%d", int(remaining.Seconds())+1))
			http.Error(w, "rate limit exceeded", http.StatusTooManyRequests)
			return
		}
		e.count++
		rl.mu.Unlock()
		next.ServeHTTP(w, r)
	})
}

// Stop halts the background cleanup goroutine.
func (rl *RateLimiter) Stop() {
	close(rl.stopCh)
}

func (rl *RateLimiter) cleanup() {
	interval := rl.window / 2
	if interval < 1*time.Second {
		interval = 1 * time.Second
	}
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ticker.C:
			rl.mu.Lock()
			now := time.Now()
			for ip, e := range rl.entries {
				if now.Sub(e.windowStart) >= rl.window {
					delete(rl.entries, ip)
				}
			}
			rl.mu.Unlock()
		case <-rl.stopCh:
			return
		}
	}
}

func extractIP(r *http.Request) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		return r.RemoteAddr
	}
	return host
}
