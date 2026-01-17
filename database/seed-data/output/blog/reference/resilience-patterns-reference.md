# **[Pattern Name] Resilience Patterns – Reference Guide**

---

## **1. Overview**
Resilience patterns help software systems recover from failures by implementing strategies for fault tolerance, graceful degradation, and fallback mechanisms. These patterns are essential for designing robust applications that handle transient or permanent failures in distributed systems, external service dependencies, or resource constraints. By applying resilience patterns, developers mitigate cascading failures, improve reliability, and enhance user experience during outages.

Common scenarios include:
- **External API failures** (e.g., third-party services)
- **Network partitioning** (e.g., microservices communication)
- **Resource exhaustion** (e.g., thread pools, memory limits)
- **Timeouts and latency spikes**

This guide covers **key concepts**, **implementation details**, and **practical examples** for major resilience patterns.

---

## **2. Schema Reference**
Below is a table of core resilience patterns, their purposes, and applicable scenarios:

| **Pattern**          | **Purpose**                                                                 | **Applicable Scenarios**                                                                 | **Key Considerations**                                                                 |
|----------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Retry**            | Re-execute failed operations after a delay to handle transient errors.       | Database timeouts, network retries, temporary unavailability.                           | Exponential backoff, jitter, max retry attempts.                                    |
| **Circuit Breaker**  | Prevent cascading failures by stopping calls to a failing service.           | External API failures, microservices with high latency/errors.                            | Half-open state, failure threshold, timeout.                                          |
| **Bulkhead**         | Isolate failures by limiting resource consumption in parallel tasks.         | CPU/memory-constrained systems, high-concurrency scenarios (e.g., order processing).      | Thread pools, executor services, isolation per module.                               |
| **Fallback**         | Provide a degraded alternative when primary functionality fails.            | Critical data unaccessible, offline modes, feature deactivation.                        | Cache-based fallbacks, placeholder responses, user notifications.                    |
| **Rate Limiting**    | Control resource usage to prevent overload (e.g., API calls).               | Denial-of-service mitigation, cost-sensitive services (e.g., cloud functions).           | Token bucket, sliding window, hard vs. soft limits.                                  |
| **Bulkhead with Isolation** | Combines bulkhead + circuit breaker for granular fault isolation.     | Multi-tenant applications, distributed systems with shared dependencies.                 | Per-tenant executor pools, dynamic circuit breaker thresholds.                       |
| **Retry with Bulkhead** | Retry logic wrapped in a bulkhead to avoid resource exhaustion.          | Database bulk operations, batch processing.                                              | Bulkhead size per retry attempt, exponential jitter.                                |
| **Cache Asynchrony**  | Decouple reads/writes to avoid blocking operations.                         | High-read/write workloads (e.g., e-commerce product catalogs).                          | Eventual consistency, cache invalidation strategies.                                 |
| **Deferred Processing** | Offload non-critical work to asynchronous queues.                          | Image resizing, report generation, notifications.                                        | Queue depth limits, error handling for failed jobs.                                  |

---

## **3. Implementation Details**

### **3.1 Retry Pattern**
**When to Use**: Handle transient errors (e.g., `ConnectionTimeout`, `ServiceUnavailable`).

#### **Key Parameters**
| Parameter          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `maxRetries`       | Max attempts before giving up (default: 3–5).                               |
| `initialInterval`  | Initial delay between retries (e.g., 100ms).                                |
| `backoffFactor`    | Multiplier for exponential backoff (e.g., 2.0).                           |
| `jitter`           | Random delay to avoid thundering herd (e.g., 50ms).                        |

#### **Implementation Snippet (Java)**
```java
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.retry.RetryConfig;

RetryConfig config = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofMillis(100))
    .backoffExponential()
    .build();

Retry retry = Retry.of("retryConfig", config);
retry.executeRunnable(() -> {
    if (failedOperation()) {
        throw new RetryException("Operation failed after retries");
    }
});
```

#### **Best Practices**
- **Exponential Backoff**: Reduce retry aggressiveness over time.
- **Circuit Breaker + Retry**: Combine with circuit breaker to avoid retries when the service is down.
- **Metrics**: Track retry success/failure rates.

---

### **3.2 Circuit Breaker**
**When to Use**: Stop calling a failing service to prevent cascading failures.

#### **Key Parameters**
| Parameter          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `failureThreshold` | % of failures to trigger open state (default: 50%).                         |
| `timeoutDuration`  | Time to wait before resuming calls (e.g., 1 minute).                        |
| `automaticTransitionFromOpenToHalfOpen` | Enable half-open state testing. |

#### **Implementation Snippet (Python)**
```python
from resilience4j.circuitbreaker import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_rate_threshold=0.5,  # 50% failures
    wait_duration_in_open_state="1m",
    permitted_number_of_calls_in_half_open_state=3,
    sliding_window_size=10,
    sliding_window_type="COUNT_BASED",
)

breaker = CircuitBreaker(config)
breaker.execute_callable(lambda: callExternalService())
```

#### **States**
| State          | Behavior                                                                   |
|----------------|-----------------------------------------------------------------------------|
| **Closed**     | All calls permitted; track failures.                                       |
| **Open**       | Rejects all calls; service is suspected to be down.                         |
| **Half-Open**  | Allows limited calls to test recovery.                                      |

#### **Best Practices**
- **Half-Open Testing**: Gradually resume calls to validate recovery.
- **Metrics**: Monitor `errorRate`, `stateTransitions`.
- **Integration**: Combine with retries for transient failures.

---

### **3.3 Bulkhead Pattern**
**When to Use**: Isolate concurrent operations to prevent resource exhaustion.

#### **Key Parameters**
| Parameter          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| `maxConcurrentCalls` | Max threads/executors allowed (e.g., 10).                                  |
| `queueCapacity`    | Buffer size for queued requests (e.g., 100).                                |

#### **Implementation Snippet (Go)**
```go
import (
    "github.com/resilience/resilience-go/bulkhead"
)

config := bulkhead.Config{
    MaxConcurrentCalls: 10,
    QueueCapacity:      100,
}

bulkhead, err := bulkhead.New(&config)
if err != nil {
    // Handle error
}

bulkhead.Execute(func() {
    // Critical operation (e.g., DB write)
})
```

#### **Best Practices**
- **Per-Module Bulkheads**: Isolate different services (e.g., `user-service`, `order-service`).
- **Thread Pools**: Use `ExecutorService` (Java) or `goroutines` (Go) for granular control.
- ** Timeout Handling**: Fail fast if the bulkhead is full.

---

### **3.4 Fallback Pattern**
**When to Use**: Provide a degraded response when primary logic fails.

#### **Implementation Snippet (TypeScript)**
```typescript
import { fallback } from "resilience-js";

const fetchWithFallback = fallback({
  operation: () => fetch("https://api.example.com/data").then(res => res.json()),
  fallback: () => Promise.resolve({ cachedData: "fallback-value" }),
});

fetchWithFallback()
  .then(data => console.log(data))
  .catch(err => console.error("Primary + fallback failed", err));
```

#### **Best Practices**
- **Cache Fallbacks**: Persist degraded data for offline use.
- **User Communication**: Notify users about degraded functionality.
- **Graceful Degradation**: Prioritize critical features.

---

### **3.5 Rate Limiting**
**When to Use**: Prevent overload from excessive requests.

#### **Implementation Snippet (Java)**
```java
import io.github.resilience4j.ratelimiter.RateLimiterConfig;

RateLimiterConfig config = RateLimiterConfig.custom()
    .limitForPeriod(100)       // 100 calls
    .limitRefreshPeriod(1000)  // per 1 second
    .timeoutDuration(Duration.ofMillis(500))
    .build();

RateLimiter rateLimiter = RateLimiter.of("rateLimiter", config);
if (!rateLimiter.acquire()) {
    throw new RateLimiterException("Rate limit exceeded");
}
```

#### **Strategies**
| Strategy          | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| **Token Bucket**  | Accumulate tokens over time; spend tokens for requests.                     |
| **Sliding Window** | Count requests in a fixed-time window (e.g., last 1 minute).               |
| **Fixed Window**  | Count requests per time bucket (e.g., every 1 second).                      |

#### **Best Practices**
- **Dynamic Limits**: Adjust limits based on workload (e.g., burst tolerance).
- **Priority-Based**: Allow critical operations to bypass limits.
- **Metrics**: Track `rejectedRequests`, `currentRate`.

---

## **4. Query Examples**
Below are examples of how to integrate resilience patterns in common scenarios.

### **4.1 Retry + Circuit Breaker (API Calls)**
```java
CircuitBreakerConfig cbConfig = CircuitBreakerConfig.custom()
    .failureRateThreshold(0.7)
    .build();

RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofSeconds(1))
    .build();

Retry retry = Retry.of("apiRetry", retryConfig);
CircuitBreaker breaker = CircuitBreaker.of("apiCircuitBreaker", cbConfig);

breaker.executeSupplier(() -> retry.executeSupplier(() ->
    callExternalApi("https://api.example.com/data")
));
```

### **4.2 Bulkhead for Database Writes**
```python
from resilience4j.bulkhead import BulkheadConfig

config = BulkheadConfig(
    max_concurrent_calls=5,
    max_wait_duration="2s",
)

bulkhead = Bulkhead(config)
bulkhead.execute_callable(lambda: database.bulk_insert(users))
```

### **4.3 Fallback for User Profiles**
```javascript
const { fallback } = require("resilience-js");

const getUserProfile = fallback({
  operation: () => fetchUserProfileFromDB(userId),
  fallback: () => fetchUserProfileFromCache(userId),
});
```

---

## **5. Related Patterns**
- **[Idempotency Pattern](#)** – Ensure operations are repeatable (e.g., duplicate payments).
- **[Saga Pattern](#)** – Manage distributed transactions via compensating actions.
- **[CQRS Pattern](#)** – Separate reads/writes for scalability (often paired with caching).
- **[Exponential Backoff](#)** – Dynamic delay strategy for retries.
- **[Chaos Engineering](#)** – Proactively test resilience by injecting failures.

---
## **6. Further Reading**
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- *Site Reliability Engineering (SRE) by Google* – Chapter on Fault Tolerance
- *Designing Data-Intensive Applications* – Handling Faults

---
**Last Updated**: [Date]
**Version**: 1.0