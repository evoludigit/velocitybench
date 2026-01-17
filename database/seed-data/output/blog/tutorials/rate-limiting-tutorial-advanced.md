```markdown
---
title: "API Rate Limiting Patterns: How to Protect Your Backend and Keep Your Clients Happy"
date: 2023-11-10
tags: ["database", "api-design", "backend-engineering", "rate-limiting", "performance"]
draft: false
author: "Alex Chen"
---

# API Rate Limiting Patterns: How to Protect Your Backend and Keep Your Clients Happy

Rate limiting is one of the unsung heroes of backend engineering—it’s not flashy like distributed transactions or it doesn’t solve the "last mile" of user experience like caching might. But without it, your API could crumble under the weight of a single malicious actor, a scrubbing bot, or even a misconfigured client.

In this post, I’ll walk you through the **core rate-limiting patterns**, their tradeoffs, and how to implement them in real-world scenarios. We’ll cover **fixed window, sliding window, token bucket, and leaky bucket algorithms**, along with practical examples in Go, Node.js, and Redis.

---

## The Problem: Why Rate Limiting Matters

Imagine this:
- Your API is suddenly flooded with **50,000 requests per second** from a single IP because a scraper misconfigured its headers.
- A **DDoS attack** overwhelms your database with malformed queries, slowing down real users.
- A **buggy client** accidentally enters an infinite loop, spamming your API with redundant calls.

Without rate limiting, your system could:
✅ Crash under load (OOM errors, timeouts)
✅ Waste resources (CPU, memory, DB connections)
✅ Punish well-behaved users (throttling legitimate traffic)
✅ Become an easy target for abuse

Rate limiting is **not just about security**—it’s about **fairness, stability, and scalability**. A well-designed rate limiter ensures:
✔ **Predictable performance** (no surprise slowdowns)
✔ **Defense against abuse** (DDoS, scraping)
✔ **Controlled resource usage** (avoid cascading failures)

---

## The Solution: Rate Limiting Patterns

There are **four primary rate-limiting algorithms**, each with its own strengths and weaknesses. Let’s break them down:

| Algorithm       | Description                                                                 | Best For                          | Drawbacks                     |
|-----------------|-----------------------------------------------------------------------------|-----------------------------------|-------------------------------|
| **Fixed Window** | Counts requests in a fixed time window (e.g., 100 requests per minute).   | Simple, low overhead              | Burstiness possible           |
| **Sliding Window** | Divides the window into smaller intervals (e.g., 100 requests per 1m sliding). | More precise rate limiting        | Complexer to implement        |
| **Token Bucket** | Accumulates "tokens" at a fixed rate; requests consume tokens.            | Smooth bursty traffic             | Token replenishment logic     |
| **Leaky Bucket** | Requests are processed at a fixed rate; excess is dropped.               | Strict, deterministic rate limiting | High latency for bursts        |

We’ll implement each in **Go** (with Redis) and **Node.js** (with in-memory structures).

---

## Implementation Guide

### 1. Fixed Window Rate Limiter

**Concept:**
- Divide time into fixed windows (e.g., 1-minute slots).
- Count requests in each window.
- If count exceeds limit, reject requests.

**Tradeoff:**
✅ Simple to implement
❌ Can allow bursts in the last few seconds of a window

#### Example (Go + Redis)
```go
package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"

	"github.com/go-redis/redis/v8"
)

type FixedWindowLimiter struct {
	client   *redis.Client
	limit    int
	interval time.Duration
}

func NewFixedWindowLimiter(redisAddr string, limit int, interval time.Duration) (*FixedWindowLimiter, error) {
	ctx := context.Background()
	client := redis.NewClient(&redis.Options{Addr: redisAddr})
	_, err := client.Ping(ctx).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %v", err)
	}
	return &FixedWindowLimiter{
		client:   client,
		limit:    limit,
		interval: interval,
	}, nil
}

func (l *FixedWindowLimiter) Allow(ip string) (bool, error) {
	ctx := context.Background()
	now := time.Now()
	windowStart := now.Truncate(l.interval)

	// Key: "rate:fixed:window:{ip}:{timeWindow}"
	key := fmt.Sprintf("rate:fixed:window:%s:%d", ip, windowStart.Unix())

	// Increment count (returns previous count)
	current, err := l.client.Incr(ctx, key).Result()
	if err != nil {
		return false, fmt.Errorf("failed to increment count: %v", err)
	}

	// Set TTL to ensure cleanup
	if err := l.client.Expire(ctx, key, l.interval).Err(); err != nil {
		return false, fmt.Errorf("failed to set TTL: %v", err)
	}

	return current < l.limit, nil
}

func main() {
	limiter, err := NewFixedWindowLimiter("localhost:6379", 100, time.Minute)
	if err != nil {
		log.Fatal(err)
	}

	// Test
	for i := 0; i < 150; i++ {
		allowed, err := limiter.Allow("1.2.3.4")
		if err != nil {
			log.Fatal(err)
		}
		fmt.Printf("Request %d: %v\n", i, allowed)
		time.Sleep(300 * time.Millisecond)
	}
}
```

#### Example (Node.js + In-Memory)
```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,
  message: 'Too many requests from this IP, please try again later',
  handler: (req, res) => {
    res.status(429).json({ error: 'Rate limit exceeded' });
  },
});

app.use(limiter);
```

---

### 2. Sliding Window Rate Limiter

**Concept:**
- Divides the window into smaller buckets (e.g., 10-second intervals).
- Tracks counts per bucket.
- Smooths out bursts better than fixed window.

**Tradeoff:**
✅ More accurate than fixed window
❌ More complex (requires per-second tracking)

#### Example (Go + Redis)
```go
type SlidingWindowLimiter struct {
	client   *redis.Client
	limit    int
	interval time.Duration
	buckets  int // e.g., 6 buckets for 60s window
}

func NewSlidingWindowLimiter(redisAddr string, limit int, interval time.Duration) (*SlidingWindowLimiter, error) {
	// ... (similar to FixedWindowLimiter setup)
	return &SlidingWindowLimiter{
		client:  client,
		limit:   limit,
		interval: interval,
		buckets: int(interval.Seconds() / 10), // 10s buckets
	}, nil
}

func (l *SlidingWindowLimiter) Allow(ip string) (bool, error) {
	ctx := context.Background()
	now := time.Now()
	bucketIndex := int(now.Unix() % l.interval.Seconds())

	key := fmt.Sprintf("rate:sliding:window:%s:%d", ip, bucketIndex)

	current, err := l.client.Incr(ctx, key).Result()
	if err != nil {
		return false, fmt.Errorf("failed to increment count: %v", err)
	}

	if err := l.client.Expire(ctx, key, l.interval).Err(); err != nil {
		return false, fmt.Errorf("failed to set TTL: %v", err)
	}

	return current < l.limit, nil
}
```

---

### 3. Token Bucket Rate Limiter

**Concept:**
- "Tokens" are added at a fixed rate (e.g., 10 tokens per second).
- Each request consumes one token.
- If no tokens, request is rejected (or queued).

**Tradeoff:**
✅ Allows bursts (tokens can accumulate)
❌ Requires careful token replenishment logic

#### Example (Go + Redis)
```go
type TokenBucketLimiter struct {
	client    *redis.Client
	rate      int           // tokens per second
	capacity  int           // max tokens
	lastRefill time.Time    // last refill time
}

func (l *TokenBucketLimiter) Allow(ip string) (bool, error) {
	ctx := context.Background()
	now := time.Now()

	// Calculate tokens since last refill
	elapsed := now.Sub(l.lastRefill)
	tokensGained := int(elapsed.Seconds() * float64(l.rate))

	// Update last refill time
	l.lastRefill = now

	// Key: "rate:token:bucket:{ip}"
	key := fmt.Sprintf("rate:token:bucket:%s", ip)

	// Get current tokens (default to 0 if key doesn't exist)
	var current int64
	current, err = l.client.Get(ctx, key).Int64()
	if err != nil && err != redis.Nil {
		return false, fmt.Errorf("failed to get token count: %v", err)
	}

	// Add gained tokens
	current += int64(tokensGained)

	// Apply request (consume 1 token)
	if current <= 0 {
		return false, nil // No tokens left
	}

	current--
	l.client.Set(ctx, key, current, l.interval) // Set TTL if needed

	return true, nil
}
```

---

### 4. Leaky Bucket Rate Limiter

**Concept:**
- Requests are processed at a fixed rate (e.g., 1 request per second).
- Excess requests are dropped or queued.

**Tradeoff:**
✅ Strict rate limiting (no bursts allowed)
❌ High latency for bursts (requests wait in queue)

#### Example (Go + Redis)
```go
type LeakyBucketLimiter struct {
	client   *redis.Client
	rate     time.Duration // time per request (e.g., 1s)
	queue    *list.List
	maxQueue int
}

func (l *LeakyBucketLimiter) Allow(ip string) (bool, error) {
	ctx := context.Background()

	// Try to dequeue a request
	if l.queue.Len() > 0 {
		l.queue.Remove(l.queue.Front())
		return true, nil
	}

	// If queue is empty, check if we can accept a new request
	key := fmt.Sprintf("rate:leaky:bucket:%s", ip)
	timestamp, err := l.client.Get(ctx, key).Int64()
	if err != redis.Nil {
		last := time.Unix(0, timestamp)
		if time.Since(last) >= l.rate {
			l.client.Set(ctx, key, time.Now().UnixNano(), l.rate)
			return true, nil
		}
	}

	return false, nil
}
```

---

## Common Mistakes to Avoid

1. **Overcomplicating Redis keys**
   - Use simple, predictable key names (e.g., `rate:{type}:{ip}`).
   - Avoid dynamic key generation that could lead to collisions.

2. **Not handling cache eviction**
   - Redis keys must have TTLs to avoid memory bloat.
   - Example: `EXPIRE key 60` ensures keys are cleaned up.

3. **Ignoring burst tolerance**
   - Fixed window allows bursts; if you need strict limits, use **sliding window + token bucket**.

4. **Not testing under load**
   - Always test with tools like **k6** or **Locust** to simulate abuse.

5. **Hardcoding limits**
   - Make limits configurable (e.g., via env vars or a dashboard).

---

## Key Takeaways

✔ **Fixed window** is simple but allows bursts.
✔ **Sliding window** is more precise but complex.
✔ **Token bucket** allows bursts but needs careful token logic.
✔ **Leaky bucket** is strict but can introduce latency.
✔ **Redis is great for distributed rate limiting**, but in-memory works for single-server setups.
✔ **Always test under load** to catch edge cases.
✔ **Combine patterns** (e.g., token bucket + sliding window).

---

## Conclusion

Rate limiting is **not just about blocking bad actors**—it’s about **designing a robust, fair, and scalable API**. Whether you’re protecting against DDoS, preventing abuse, or ensuring consistent performance, choosing the right algorithm matters.

**Start simple (fixed window), then refine** based on your needs. Use **Redis for distributed systems** and **in-memory for local testing**. Always **monitor and tweak** based on real-world usage.

Now go forth and **limit like a pro**!

---

### Further Reading
- [Redis Rate Limiting with Sorted Sets](https://redis.io/docs/manual/patterns/rate-limiter)
- [Token Bucket Algorithm Deep Dive](https://www.baeldung.com/cs/token-bucket-algorithm)
- [k6 for API Load Testing](https://k6.io/docs/)
```

---

### Why This Works:
1. **Code-first approach** – Practical examples in Go/Node.js make it actionable.
2. **Honest tradeoffs** – Every pattern’s pros/cons are clearly stated.
3. **Real-world focus** – Covers distributed (Redis) and local (in-memory) setups.
4. **Actionable advice** – Common mistakes and key takeaways are distilled.

Would you like any refinements (e.g., more detail on Redis optimizations, or a comparison with cloud-based solutions like AWS WAF)?