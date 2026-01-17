# **[Reliability Patterns] Reference Guide**

---

## **Overview**
Reliability Patterns are architectural and design techniques used to ensure systems maintain consistent performance, availability, and resilience under adverse conditions (e.g., failures, load spikes, or network issues). These patterns help mitigate risks such as crashes, data loss, or degraded user experience by implementing redundancy, graceful degradation, circuit breaking, retries, and other defensive strategies.

A robust reliability strategy combines patterns like **Retry & Backoff**, **Circuit Breaker**, **Bulkhead**, **Fallback/Degradation**, and **Idempotency**, ensuring systems remain operational even as components fail. This guide covers key patterns, their trade-offs, implementation details, and practical examples.

---

## **Schema Reference**

| **Pattern**            | **Purpose**                                                                 | **When to Use**                                                                 | **Trade-offs**                                                                 | **Key Implementation Components**                                                                 |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Retry & Backoff**    | Automatically retry failed operations with exponential backoff to reduce load. | Transient failures (timeouts, throttling, network issues).                     | Risk of cascading failures if retries don’t resolve root cause.                | Exponential backoff, max retries, jitter, circuit breaker integration.                                 |
| **Circuit Breaker**    | Prevents cascading failures by halting requests to a failing service.       | High-latency or frequently failing dependencies.                               | False positives/negatives if thresholds are misconfigured.                     | Thresholds (error %, timeout), half-open state, fallback logic.                                       |
| **Bulkhead**           | Isolates failures by limiting concurrent executions per resource.            | Prevent overload on shared resources (e.g., database, API).                     | Potential resource exhaustion if limits are too high.                       | Thread pools, semaphores, queue-based rate limiting.                                                   |
| **Fallback/Degradation** | Gracefully handles failures with reduced functionality.                 | Temporary service unavailability or degraded quality.                       | User experience may degrade (e.g., cached data instead of fresh).              | Pre-fetched data, cached responses, degraded UI modes.                                               |
| **Idempotency**        | Ensures repeated identical requests have the same outcome.               | Retry mechanisms (e.g., payment processing, order placement).                   | Complexity in implementing unique identifiers for idempotency keys.          | Idempotency keys, request deduplication, state tracking.                                              |
| **Polly (Retry + Circuit Breaker)** | Combined pattern for resilient client operations.                      | Client-server interactions with transient failures.                           | Overhead of managing multiple policies.                                       | Retry policies, circuit breaker thresholds, custom exceptions.                                        |
| **Queue-Based Retry**  | Decouples retries from the calling application using a message queue.       | Long-running processes or async workflows.                                     | Additional infrastructure (queue) and latency.                             | Message brokers (Kafka, RabbitMQ), delayed deliveries, retry policies.                                |
| **Chaos Engineering**  | Proactively tests system resilience by injecting failures.                | Stress-testing production-like environments.                                  | Requires controlled, monitored testing.                                       | Chaos tools (Gremlin, Chaos Monkey), failure injection rules, observability integration.           |

---
---

## **Implementation Details**

### **1. Retry & Backoff**
**Concept:**
Automatically retry failed operations (e.g., API calls, database queries) with exponential backoff to avoid overwhelming a failing service.

**When to Use:**
- Transient errors (timeouts, throttling, network issues).
- Idempotent operations (e.g., reading data).

**Key Configuration:**
```plaintext
Max Retries: 3
Initial Delay: 100ms
Backoff Factor: 2.0 (doubling delay each retry)
Jitter: ±10% (randomization to avoid thundering herd)
```

**Example (C# with Polly):**
```csharp
var retryPolicy = Policy
    .Handle<TimeoutException>()
    .WaitAndRetryAsync(
        retryCount: 3,
        sleepDurationProvider: retryAttempt => TimeSpan.FromMilliseconds(100 * Math.Pow(2, retryAttempt)),
        onRetry: (exception, delay, retryCount, context) =>
            Logger.LogWarning($"Retry {retryCount} after {delay.TotalMilliseconds}ms due to: {exception}")
    );
```

**Trade-offs:**
- **Pros:** Resilient to temporary failures.
- **Cons:** Risk of retrying indefinitely if the issue persists; may exacerbate problems if the root cause is not addressed.

---

### **2. Circuit Breaker**
**Concept:**
Stops forwarding requests to a failing service after a threshold of failures, allowing recovery time.

**When to Use:**
- High-latency dependencies (e.g., third-party APIs).
- Services with slow recovery times.

**Key States:**
1. **Closed:** Normal operation; track failures.
2. **Open:** Stops requests; allows recovery after timeout.
3. **Half-Open:** Allows limited requests to test recovery.

**Example (C#):**
```csharp
var circuitBreaker = Policy
    .Handle<TimeoutException>()
    .CircuitBreakerAsync(
        exceptionsAllowedBeforeBreaking: 5,
        durationOfBreak: TimeSpan.FromSeconds(30),
        onBreak: (exception, breakDelay) => Logger.LogWarning("Circuit opened; will re-enable in {0}", breakDelay),
        onReset: () => Logger.LogInformation("Circuit reset")
    );
```

**Trade-offs:**
- **Pros:** Prevents cascading failures.
- **Cons:** False positives/negatives if thresholds are misconfigured; may increase latency during recovery.

---

### **3. Bulkhead**
**Concept:**
Isolates failures by limiting concurrent executions to a shared resource (e.g., thread pool, database connection).

**When to Use:**
- Preventing resource exhaustion (e.g., database overload).
- CPU-bound or I/O-bound tasks.

**Example (Java with Thread Pool):**
```java
ExecutorService executor = Executors.newFixedThreadPool(10); // Bulkhead size
executor.submit(() -> {
    try {
        // Database operation
    } catch (Exception e) {
        // Log and retry via circuit breaker
    }
});
```

**Trade-offs:**
- **Pros:** Prevents resource starvation.
- **Cons:** May underutilize resources if limits are too low.

---
---
## **Query Examples**

### **1. Retry a Database Query (SQL)**
```sql
-- Example: Retry a failing INSERT with exponential backoff
BEGIN TRY
    INSERT INTO Orders (CustomerId, Amount) VALUES (123, 99.99);
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    WAITFOR DELAY '00:00:01'; -- Manual backoff (automate in app code)
    -- Retry logic in application (e.g., retry after delay)
END CATCH
```

### **2. Circuit Breaker for External API (Python with `tenacity`)**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda attempt: logger.warning(f"Retry {attempt.attempt_number} failed")
)
def call_external_api():
    response = requests.get("https://api.example.com/data")
    response.raise_for_status()
    return response.json()
```

### **3. Bulkhead with Thread Pool (Go)**
```go
package main

import (
	"sync"
	"time"
)

func main() {
	pool := make(chan struct{}, 5) // Bulkhead size = 5 goroutines
	var wg sync.WaitGroup

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			pool <- struct{}{} // Acquire slot
			defer <-pool        // Release slot
			// Simulate work (e.g., DB call)
			time.Sleep(100 * time.Millisecond)
		}(i)
	}
	wg.Wait()
}
```

---
---

## **Related Patterns**

| **Pattern**               | **Relationship**                                                                 | **When to Combine**                                                                 |
|---------------------------|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Resilience Patterns**   | Overlapping category; includes Reliability Patterns + Fault Tolerance Patterns.   | Use both for end-to-end resilience (e.g., retry + circuit breaker).                |
| **Caching**               | Complements Fallback/Degradation by providing stale-but-good data.              | Cache API responses to enable graceful degradation during outages.               |
| **Asynchronous Processing** | Helps with Queue-Based Retry by decoupling operations.                         | Use async queues (e.g., Kafka) for retries in long-running workflows.            |
| **Idempotency**           | Critical for Retry & Backoff to avoid duplicate side effects.                   | Always pair retry mechanisms with idempotent operations.                          |
| **Chaos Engineering**     | Tests the effectiveness of Reliability Patterns in production.                 | Run chaos experiments to validate circuit breakers, bulkheads, etc.              |
| **Rate Limiting**         | Prevents overload; works with Bulkhead to control concurrency.                  | Use rate limiting to avoid hitting bulkhead limits.                               |

---
---
## **Best Practices**
1. **Combine Patterns:**
   - Use **Retry + Circuit Breaker** (Polly) for client-side resilience.
   - Pair **Bulkhead** with **Queue-Based Retry** for async workloads.
2. **Monitor Metrics:**
   - Track retry counts, circuit breaker states, and bulkhead usage.
   - Tools: Prometheus, Datadog, or application-specific dashboards.
3. **Test Rigorously:**
   - Simulate failures (e.g., network partitions) with chaos tools.
   - Validate idempotency in retry scenarios.
4. **Graceful Degradation:**
   - Prioritize user flows (e.g., show cached data instead of failing silently).
5. **Document Failover Logic:**
   - Clearly define fallback behaviors for operators/maintainers.

---
---
## **Anti-Patterns to Avoid**
- **Retry Without Backoff:** Can amplify load and worsen failures.
- **Unbounded Retries:** Risks infinite loops for permanent failures.
- **Ignoring Circuit Breaker State:** May lead to cascading failures.
- **Bulkhead Too Small:** Causes unnecessary throttling.
- **Hardcoded Fallbacks:** Assuming services will recover may hide issues.