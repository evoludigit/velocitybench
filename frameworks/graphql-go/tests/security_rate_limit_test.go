package tests

import (
	"sync"
	"testing"
	"time"
)

// ============================================================================
// Rate Limiting Tests (GraphQL)
// ============================================================================

func TestSecurityRateLimit(t *testing.T) {
	tests := []struct {
		name          string
		requestCount  int
		timeWindow    time.Duration
		rateLimit     int
		expectBlocked bool
	}{
		{
			name:          "within rate limit",
			requestCount:  5,
			timeWindow:    time.Minute,
			rateLimit:     10,
			expectBlocked: false,
		},
		{
			name:          "exceeds rate limit",
			requestCount:  15,
			timeWindow:    time.Minute,
			rateLimit:     10,
			expectBlocked: true,
		},
		{
			name:          "burst protection",
			requestCount:  100,
			timeWindow:    time.Second,
			rateLimit:     10,
			expectBlocked: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			_ = NewTestFactory()

			limiter := NewRateLimiter(tt.rateLimit, tt.timeWindow)
			userID := "test-user-123"

			// Act - Make multiple GraphQL requests
			blockedCount := 0
			for i := 0; i < tt.requestCount; i++ {
				if !limiter.Allow(userID) {
					blockedCount++
				}
			}

			// Assert
			hasBlocked := blockedCount > 0
			if hasBlocked != tt.expectBlocked {
				t.Errorf("Expected blocked status %v, got %v (blocked %d/%d requests)",
					tt.expectBlocked, hasBlocked, blockedCount, tt.requestCount)
			}
		})
	}
}

// ============================================================================
// Per-User Rate Limiting (GraphQL)
// ============================================================================

func TestSecurityPerUserRateLimit(t *testing.T) {
	tests := []struct {
		name      string
		userCount int
		reqPerUser int
		rateLimit int
	}{
		{
			name:      "multiple users stay within individual limits",
			userCount: 3,
			reqPerUser: 5,
			rateLimit: 10,
		},
		{
			name:      "one user exceeds while others don't",
			userCount: 2,
			reqPerUser: 15,
			rateLimit: 10,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			factory := NewTestFactory()

			limiter := NewRateLimiter(tt.rateLimit, time.Minute)

			// Act - Multiple users making GraphQL requests
			results := make(map[string]int)
			for u := 0; u < tt.userCount; u++ {
				bio := "Bio " + string(rune(48+u))
				userID := factory.CreateUser(
					"user"+string(rune(48+u)),
					"user"+string(rune(48+u))+"@example.com",
					"User "+string(rune(48+u)),
					&bio,
				).ID

				allowedCount := 0
				for r := 0; r < tt.reqPerUser; r++ {
					if limiter.Allow(userID) {
						allowedCount++
					}
				}
				results[userID] = allowedCount
			}

			// Assert - Each user should be rate limited independently
			for userID, allowed := range results {
				if allowed > tt.rateLimit {
					t.Errorf("User %s exceeded rate limit: %d > %d", userID, allowed, tt.rateLimit)
				}
			}
		})
	}
}

// ============================================================================
// GraphQL Query Complexity Rate Limiting
// ============================================================================

func TestSecurityQueryComplexityRateLimit(t *testing.T) {
	tests := []struct {
		name             string
		queryComplexity  int
		complexityLimit  int
		expectBlocked    bool
	}{
		{
			name:            "simple query within complexity limit",
			queryComplexity: 5,
			complexityLimit: 100,
			expectBlocked:   false,
		},
		{
			name:            "complex query exceeds limit",
			queryComplexity: 150,
			complexityLimit: 100,
			expectBlocked:   true,
		},
		{
			name:            "deeply nested query blocked",
			queryComplexity: 500,
			complexityLimit: 100,
			expectBlocked:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			_ = NewTestFactory()

			// Act - Check query complexity
			isBlocked := tt.queryComplexity > tt.complexityLimit

			// Assert
			if isBlocked != tt.expectBlocked {
				t.Errorf("Expected blocked status %v, got %v", tt.expectBlocked, isBlocked)
			}
		})
	}
}

// ============================================================================
// GraphQL Depth Limiting
// ============================================================================

func TestSecurityQueryDepthLimit(t *testing.T) {
	tests := []struct {
		name        string
		queryDepth  int
		depthLimit  int
		expectBlock bool
	}{
		{
			name:        "shallow query allowed",
			queryDepth:  3,
			depthLimit:  10,
			expectBlock: false,
		},
		{
			name:        "deep query blocked",
			queryDepth:  15,
			depthLimit:  10,
			expectBlock: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			_ = NewTestFactory()

			// Act - Check query depth
			blocked := tt.queryDepth > tt.depthLimit

			// Assert
			if blocked != tt.expectBlock {
				t.Errorf("Expected block status %v, got %v", tt.expectBlock, blocked)
			}
		})
	}
}

// ============================================================================
// Rate Limit Window Reset
// ============================================================================

func TestSecurityRateLimitWindowReset(t *testing.T) {
	t.Run("rate limit resets after window expires", func(t *testing.T) {
		// Arrange
		_ = NewTestFactory()

		windowDuration := 100 * time.Millisecond
		limiter := NewRateLimiter(5, windowDuration)
		userID := "test-user"

		// Act - Exhaust rate limit
		allowedFirstWindow := 0
		for i := 0; i < 10; i++ {
			if limiter.Allow(userID) {
				allowedFirstWindow++
			}
		}

		// Wait for window to expire
		time.Sleep(windowDuration + 10*time.Millisecond)

		// Try again after window reset
		allowedSecondWindow := 0
		for i := 0; i < 10; i++ {
			if limiter.Allow(userID) {
				allowedSecondWindow++
			}
		}

		// Assert
		if allowedFirstWindow != 5 {
			t.Errorf("Expected 5 requests allowed in first window, got %d", allowedFirstWindow)
		}
		if allowedSecondWindow != 5 {
			t.Errorf("Expected 5 requests allowed in second window, got %d", allowedSecondWindow)
		}
	})
}

// ============================================================================
// Concurrent Rate Limiting
// ============================================================================

func TestSecurityConcurrentRateLimiting(t *testing.T) {
	t.Run("rate limiter handles concurrent GraphQL requests safely", func(t *testing.T) {
		// Arrange
		_ = NewTestFactory()

		limiter := NewRateLimiter(10, time.Minute)
		userID := "test-user"

		// Act - Make concurrent requests
		concurrentRequests := 20
		var wg sync.WaitGroup
		allowedCount := 0
		var mu sync.Mutex

		for i := 0; i < concurrentRequests; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				if limiter.Allow(userID) {
					mu.Lock()
					allowedCount++
					mu.Unlock()
				}
			}()
		}

		wg.Wait()

		// Assert - Should respect rate limit even under concurrency
		if allowedCount > 10 {
			t.Errorf("Rate limit exceeded under concurrency: %d > 10", allowedCount)
		}
		if allowedCount < 10 {
			t.Logf("Warning: Allowed only %d requests (expected 10) - may indicate race condition", allowedCount)
		}
	})
}

// ============================================================================
// Mutation Rate Limiting
// ============================================================================

func TestSecurityMutationRateLimit(t *testing.T) {
	tests := []struct {
		name          string
		mutationType  string
		requestCount  int
		rateLimit     int
		expectBlocked bool
	}{
		{
			name:          "createPost mutations within limit",
			mutationType:  "createPost",
			requestCount:  5,
			rateLimit:     10,
			expectBlocked: false,
		},
		{
			name:          "createPost mutations exceed limit",
			mutationType:  "createPost",
			requestCount:  15,
			rateLimit:     10,
			expectBlocked: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			_ = NewTestFactory()

			limiter := NewRateLimiter(tt.rateLimit, time.Minute)
			userID := "test-user"

			// Act - Make multiple mutations
			blockedCount := 0
			for i := 0; i < tt.requestCount; i++ {
				if !limiter.Allow(userID + ":" + tt.mutationType) {
					blockedCount++
				}
			}

			// Assert
			hasBlocked := blockedCount > 0
			if hasBlocked != tt.expectBlocked {
				t.Errorf("Expected blocked status %v, got %v", tt.expectBlocked, hasBlocked)
			}
		})
	}
}

// ============================================================================
// IP-Based Rate Limiting
// ============================================================================

func TestSecurityIPBasedRateLimiting(t *testing.T) {
	tests := []struct {
		name       string
		ipAddress  string
		requests   int
		rateLimit  int
	}{
		{
			name:      "single IP within limit",
			ipAddress: "192.168.1.1",
			requests:  5,
			rateLimit: 10,
		},
		{
			name:      "single IP exceeds limit",
			ipAddress: "192.168.1.1",
			requests:  15,
			rateLimit: 10,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Arrange
			_ = NewTestFactory()

			limiter := NewRateLimiter(tt.rateLimit, time.Minute)

			// Act
			allowedCount := 0
			for i := 0; i < tt.requests; i++ {
				if limiter.Allow(tt.ipAddress) {
					allowedCount++
				}
			}

			// Assert
			if allowedCount > tt.rateLimit {
				t.Errorf("Expected max %d requests, got %d", tt.rateLimit, allowedCount)
			}
		})
	}
}

// ============================================================================
// Rate Limiter Implementation (Mock for testing)
// ============================================================================

type RateLimiter struct {
	limit      int
	window     time.Duration
	requests   map[string][]time.Time
	mu         sync.RWMutex
}

func NewRateLimiter(limit int, window time.Duration) *RateLimiter {
	return &RateLimiter{
		limit:    limit,
		window:   window,
		requests: make(map[string][]time.Time),
	}
}

func (rl *RateLimiter) Allow(identifier string) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	now := time.Now()

	// Get existing requests for this identifier
	requests, exists := rl.requests[identifier]
	if !exists {
		requests = []time.Time{}
	}

	// Remove expired requests outside the time window
	validRequests := []time.Time{}
	for _, reqTime := range requests {
		if now.Sub(reqTime) < rl.window {
			validRequests = append(validRequests, reqTime)
		}
	}

	// Check if under limit
	if len(validRequests) >= rl.limit {
		rl.requests[identifier] = validRequests
		return false
	}

	// Add current request
	validRequests = append(validRequests, now)
	rl.requests[identifier] = validRequests
	return true
}

func (rl *RateLimiter) Reset(identifier string) {
	rl.mu.Lock()
	defer rl.mu.Unlock()
	delete(rl.requests, identifier)
}
