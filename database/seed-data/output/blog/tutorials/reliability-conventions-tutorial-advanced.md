```markdown
# **Reliability Conventions: Building Robust APIs and Systems with Predictable Behavior**

*How consistent, well-defined reliability patterns prevent cascading failures and improve operational resilience in distributed systems.*

---

## **Introduction**

In modern backend engineering, reliability isn’t just about writing correct code—it’s about **designing systems that behave predictably under stress**. Every API call, database query, or microservice interaction should adhere to clear, documented reliability conventions, ensuring that errors, timeouts, and retries follow a consistent pattern across the entire stack.

Why does this matter? Because distributed systems are inherently unreliable. Network partitions, database timeouts, and external service failures are not questions of *if*, but *when*. When they happen, poorly designed systems can spiral into cascading failures, leading to outages, inconsistent states, or degraded performance.

This post explores the **"Reliability Conventions"** pattern—a structured approach to defining how your system handles errors, retries, timeouts, and fallback mechanisms in a way that’s **explicit, auditable, and team-wide**. We’ll cover:
- The problems caused by ad-hoc reliability approaches
- How conventions improve predictability
- Practical code examples in Go (for HTTP clients), Python (for async retries), and SQL (for database transactions)
- A step-by-step implementation guide
- Common pitfalls and how to avoid them

By the end, you’ll have a playbook for designing systems that **fail gracefully** rather than unpredictably.

---

## **The Problem: Chaos Without Conventions**

Imagine you’re building a payment processing system integrated with multiple external services (e.g., Stripe, fraud detection APIs, and a third-party KYC service). Without reliability conventions, you might see:

| Scenario                     | Without Conventions | With Conventions |
|------------------------------|--------------------|------------------|
| **Stripe API timeout**       | Retry indefinitely, risking race conditions | Exponential backoff, max retries (3x) |
| **Fraud API fails intermittently** | Retry aggressively, consuming quotas | Circuit breaker waits 5 mins before retrying |
| **Database timeout**         | Crash the whole service | Fallback to read replicas, log error |
| **Inconsistent retry logic** | Some paths retry, others don’t | Standardized retry config across all clients |

### **Real-World Fallout**
- **Cascading Failures**: A single API timeout triggers retries that overload downstream services.
- **Inconsistent State**: Some transactions roll back, others commit, leading to duplication or loss.
- **Debugging Nightmares**: Logs show `retry=3` in one place and `retry=infinite` in another—who’s doing it right?
- **Performance Spikes**: Uncontrolled retries during high traffic degrade system stability.

These issues aren’t hypothetical. They’ve caused outages at companies like **Netflix** (due to cascading timeouts) and **Twitter** (due to inconsistent retry logic during peak load).

---

## **The Solution: Reliability Conventions**

Reliability conventions are **explicit, documented rules** that dictate how your system behaves under failure. They answer questions like:
- How many times should we retry a failed request?
- What’s the maximum allowed latency for a critical operation?
- When should we fail fast vs. retry?
- How do we handle partial failures in distributed transactions?

### **Key Principles**
1. **Explicit Over Implicit**: Document retry policies, timeouts, and fallbacks in a shared spec (e.g., `RELIABILITY_CONVENTIONS.md`).
2. **Consistency**: Apply the same rules across all clients, services, and languages.
3. **Observability**: Log retry attempts, timeouts, and fallbacks for debugging.
4. **Bounded Retry Attempts**: Never retry indefinitely—use exponential backoff with limits.
5. **Isolation**: Failures in one component shouldn’t crash the entire system.

---

## **Components/Solutions**

A robust reliability convention system includes:

| Component               | Purpose                                                                 | Example Tools/Libraries          |
|-------------------------|-------------------------------------------------------------------------|-----------------------------------|
| **Retry Policies**      | Define how often and when to retry requests.                            | `go-retry`, `tenacity` (Python)   |
| **Timeouts**            | Enforce maximum execution time for critical paths.                      | `context.Timeout` (Go), `asyncio` (Python) |
| **Circuit Breakers**    | Stop retries if a service is failing repeatedly.                        | `resilience4j`, `Hystrix` (legacy) |
| **Fallbacks**           | Provide degraded functionality when primary sources fail.               | `gRPC` deadlines, `Redis` caching |
| **Idempotency**         | Ensure retries don’t cause duplicate side effects.                     | `Idempotency Key` in DB            |
| **Transaction Boundaries** | Define atomicity for multi-service operations.                       | `Saga Pattern`, `Two-Phase Commit` |

---

## **Code Examples**

### **1. HTTP Client with Retry and Timeout (Go)**
```go
package main

import (
	"context"
	"net/http"
	"time"

	"golang.org/x/time/rate"
	"github.com/go-resty/resty/v2"
)

// Config defines reliability conventions for HTTP clients.
type Config struct {
	MaxRetries   int      // Max attempts before failing
	BaseTimeout  time.Duration // Initial timeout (e.g., 500ms)
	RetryBackoff time.Duration // Exponential backoff factor
	RateLimit    *rate.Limit  // Request throttling (e.g., 100 req/s)
}

func NewClient(cfg Config) *resty.Client {
	client := resty.New().SetTimeout(cfg.BaseTimeout)
	client.SetRetryCount(cfg.MaxRetries)
	client.SetRetryWaitTime(cfg.RetryBackoff)
	client.SetRateLimiter(cfg.RateLimit)

	// Apply circuit breaker logic (simplified)
	client.OnAfterResponse(func(client *resty.Client, resp *resty.Response) {
		if resp.IsError() && resp.StatusCode() >= 500 {
			// Log failure and potentially trigger circuit breaker
		}
	})

	return client
}
```

**Usage:**
```go
client := NewClient(Config{
	MaxRetries:   3,
	BaseTimeout:  500 * time.Millisecond,
	RetryBackoff: 100 * time.Millisecond,
	RateLimit:    rate.Limit(100).Burst(200),
})

resp, err := client.R().SetContext(context.Background()).Get("https://api.example.com/orders")
if err != nil {
	log.Printf("Failed after %d retries: %v", cfg.MaxRetries, err)
}
```

---

### **2. Async Retry with Fallback (Python)**
```python
import asyncio
import backoff
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)

def exponential_backoff(max_tries: int = 3) -> Callable:
    """Reliability convention: Exponential backoff with jitter."""
    return backoff.on_exception(
        backoff.expo,
        (Exception, TimeoutError),
        max_tries=max_tries,
        jitter=backoff.full_jitter,
        logger=logger,
    )

@exponential_backoff(max_tries=3)
async def fetch_order(order_id: str) -> dict:
    """Fallback to cache if primary API fails."""
    try:
        # Try primary API
        response = await httpx_async.get(f"https://api.example.com/orders/{order_id}")
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPStatusError, httpx.TimeoutException):
        # Fallback: Read from Redis
        logger.warning(f"Primary API failed for order {order_id}, falling back to cache")
        cache_key = f"order:{order_id}"
        cached_data = await redis.get(cache_key)
        if not cached_data:
            raise ValueError("No fallback data available")
        return cached_data
```

---

### **3. Database Transaction with Timeout and Retry (SQL)**
```sql
-- PostgreSQL: Define a retry-able transaction with timeout
DO $$
DECLARE
    retries INT := 3;
    success BOOLEAN;
BEGIN
    WHILE retries > 0 LOOP
        BEGIN
            -- Simulate a transaction (e.g., update inventory)
            UPDATE products
            SET stock = stock - 1
            WHERE id = '123'
            AND stock > 0
            RETURNING stock;

            success := TRUE;
            EXIT;
        EXCEPTION WHEN OTHERS THEN
            retries := retries - 1;
            IF retries = 0 THEN
                RAISE EXCEPTION 'Failed after % retries', retries;
            END IF;
            WAIT 100 * retries; -- Exponential backoff (100ms, 200ms, etc.)
        END;
    END LOOP;
END $$;
```

---

## **Implementation Guide**

### **Step 1: Define Your Conventions**
Create a shared document (e.g., `RELIABILITY_CONVENTIONS.md`) with rules like:
```markdown
## Retry Policies
- **HTTP Clients**: Max 3 retries with exponential backoff (100ms, 200ms, 400ms).
- **Database Operations**: Max 2 retries for timeouts (100ms delay).
- **External APIs**: Circuit breaker trips after 5 consecutive failures (reset after 1 minute).

## Timeouts
- HTTP calls: 500ms for reads, 2s for writes.
- Database queries: 1s for reads, 3s for writes.
- Long-running tasks: Use context cancellation (e.g., `context.Background()`).

## Fallbacks
- If primary DB fails, read from Redis (TTL=1h).
- If Stripe API fails, retry once with fallback to legacy payment gateway.
```

### **Step 2: Enforce Consistency**
- **Client Libraries**: Build reusable HTTP/database clients with baked-in conventions (as in the Go example).
- **API Specs**: Document timeout/retry rules in OpenAPI/Swagger specs.
- **CI Checks**: Add a test that verifies retry logic (e.g., mock a failing service and check for retries).

### **Step 3: Monitor and Alert**
- **Metrics**: Track:
  - `retry_attempts_total` (per endpoint).
  - `circuit_breaker_open` (for external dependencies).
  - `fallback_used`.
- **Alerts**: Notify if retry rates spike (e.g., "5xx errors > 1% for `/api/orders`").

### **Step 4: Test Reliability**
- **Chaos Engineering**: Use tools like **Gremlin** or **Chaos Mesh** to simulate timeouts/latency.
- **Load Testing**: Validate retry behavior under load (e.g., 1000 RPS).

---

## **Common Mistakes to Avoid**

1. **Infinite Retries**
   - ❌ Retry forever on `500` errors.
   - ✅ Use `MaxRetries` with exponential backoff.

2. **No Circuit Breakers**
   - ❌ Retry indefinitely during a database outage.
   - ✅ Implement a circuit breaker (e.g., `resilience4j`).

3. **Inconsistent Timeouts**
   - ❌ Some endpoints timeout at 1s, others at 10s.
   - ✅ Standardize timeouts (e.g., 500ms for reads).

4. **Ignoring Idempotency**
   - ❌ Retry a non-idempotent `POST /pay` and double-charge.
   - ✅ Use idempotency keys (e.g., `X-Idempotency-Key`).

5. **No Fallbacks**
   - ❌ Crash the app when the primary DB fails.
   - ✅ Fall back to read replicas or cache.

6. **Over-Reliance on Retries**
   - ❌ Retry every `429 Too Many Requests`.
   - ✅ Respect API rate limits (use exponential backoff + jitter).

---

## **Key Takeaways**
- **Conventions prevent inconsistency**: Explicit rules > ad-hoc code.
- **Bounded retries prevent cascading failures**: Always set `MaxRetries` and timeouts.
- **Fallbacks preserve usability**: Graceful degradation > crashes.
- **Monitor reliability metrics**: Know when your system is struggling.
- **Test under failure**: Chaos testing catches hidden reliability holes.

---

## **Conclusion**

Reliability conventions aren’t just "nice to have"—they’re the difference between a system that **recovers gracefully** and one that **collapses under pressure**. By documenting and enforcing retry policies, timeouts, and fallbacks, you create a **predictable, resilient** backend that handles failures like a Swiss watch.

Start small: pick one critical path (e.g., HTTP clients) and apply conventions there. Then expand to databases, async tasks, and external APIs. Over time, your entire system will become **more robust, more debuggable, and less prone to outages**.

**Next steps:**
1. Define your team’s reliability conventions (use the template above).
2. Build reusable client libraries with these rules baked in.
3. Instrument metrics and alerts for reliability events.
4. Run chaos tests to verify your conventions hold under stress.

Build systems that **work when they need to**.

---
```