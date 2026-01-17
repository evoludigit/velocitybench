# **[Pattern] Resilience Setup Reference Guide**

## **Overview**
The **Resilience Setup** pattern ensures systems can gracefully handle failures, degrade performance, and recover from transient or permanent disruptions. This pattern employs **circuit breakers, retries, fallbacks, rate limiting, and bulkheads** to enhance reliability, availability, and fault tolerance.

By applying **timeouts, exponential backoff, and cascading failure prevention**, this pattern minimizes impact when downstream services fail. It is widely used in microservices architectures, distributed systems, and cloud-native applications.

---

## **Key Concepts**
| **Component**          | **Purpose**                                                                 | **Implementation Considerations**                                                                 |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Circuit Breaker**    | Stops cascading failures by preventing repeated calls to a failed service. | Define a failure threshold (e.g., 5 failures in 10 minutes) and reset timeout (e.g., 30 minutes). |
| **Retry with Backoff** | Retries failed operations with increasing delays to avoid overwhelming a recovering service. | Use **exponential backoff** (e.g., 1s, 2s, 4s) or **jitter** to prevent thundering herds. |
| **Fallback Mechanism** | Provides a degraded response when the primary service fails.                 | Cache stale data, use a mock response, or return meaningful errors.                              |
| **Rate Limiting**      | Prevents overload by restricting request volume.                            | Apply **token bucket** or **leaky bucket** algorithms to smooth traffic spikes.                  |
| **Bulkhead**           | Isolates failures by limiting resource usage per thread/pool.               | Use **thread pools** or **async task queues** to segment workloads.                              |
| **Timeout**            | Forces a failure after a configured duration if no response is received.     | Set realistic timeouts (e.g., 2s for HTTP APIs, 1min for DB queries).                           |

---

## **Schema Reference**

### **1. Circuit Breaker Configuration**
| **Parameter**          | **Type**   | **Description**                                                                                     | **Default Value** |
|------------------------|------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `failureThreshold`     | Integer    | Number of consecutive failures before tripping the circuit.                                          | `5`               |
| `resetTimeout`         | Duration   | Time after which the circuit resets (allows retries again).                                          | `30m`             |
| `halfOpenTimeout`      | Duration   | Time to wait in the "half-open" state (tests a single request) before fully resetting.              | `5s`              |
| `successThreshold`     | Integer    | Minimum successful calls needed to reset the circuit in the half-open state.                     | `1`               |

**Example Implementation (Pseudocode):**
```java
CircuitBreaker breaker = new CircuitBreaker(
    5, // failures before trip
    30 * 60, // reset timeout (30m)
    5, // half-open test delay (5s)
    1  // success threshold to reset
);
```

---

### **2. Retry Policy with Exponential Backoff**
| **Parameter**          | **Type**   | **Description**                                                                                     | **Default Value** |
|------------------------|------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `maxRetries`           | Integer    | Maximum number of retry attempts.                                                                   | `3`               |
| `baseInterval`         | Duration   | Initial delay between retries.                                                                     | `1s`              |
| `multiplier`           | Float      | Exponential multiplier (e.g., 2.0 for doubling delays).                                              | `2.0`             |
| `maxInterval`          | Duration   | Maximum delay between retries (prevents unbounded growth).                                          | `30s`             |
| `jitter`               | Boolean    | Adds randomness to backoff to avoid synchronized retries.                                           | `true`            |

**Example (Pseudocode):**
```python
retry_policy = RetryPolicy(
    max_retries=3,
    base_interval=1,  # seconds
    multiplier=2.0,
    max_interval=30,  # seconds
    jitter=True
)
```

---

### **3. Fallback Mechanism**
| **Parameter**          | **Type**   | **Description**                                                                                     | **Example**                          |
|------------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `fallbackType`         | Enum       | `CACHE`, `MOCK`, `ERROR`, or `DEGRADED_RESPONSE`.                                                 | `CACHE`                              |
| `cacheTTL`             | Duration   | Time-to-live for cached responses (if using `CACHE`).                                              | `5m`                                 |
| `mockResponse`         | Any        | Hardcoded fallback data (if using `MOCK`).                                                        | `{ "status": "degraded" }`           |
| `errorMessage`         | String     | Custom error message (if using `ERROR`).                                                          | `"Service temporarily unavailable"`   |

**Example (Pseudocode):**
```java
FallbackConfig fallback = new FallbackConfig(
    FallbackType.CACHE,
    5 * 60,  // 5-minute TTL
    null    // No mock response (uses cache)
);
```

---

### **4. Rate Limiting**
| **Parameter**          | **Type**   | **Description**                                                                                     | **Algorithm**       |
|------------------------|------------|-----------------------------------------------------------------------------------------------------|----------------------|
| `limit`                | Integer    | Maximum allowed requests per time window.                                                          | Token Bucket         |
| `window`               | Duration   | Time window (e.g., 1 minute).                                                                      | Leaky Bucket         |
| `burstCapacity`        | Integer    | Maximum burst requests allowed (if using `TokenBucket`).                                          | N/A                  |
| `rejectionPolicy`      | Enum       | `REJECT`, `QUARANTINE`, or `THROTTLE`.                                                           | N/A                  |

**Example (Pseudocode):**
```csharp
RateLimiterConfig limiter = new RateLimiterConfig(
    limit: 100,
    window: TimeSpan.FromMinutes(1),
    burstCapacity: 50,
    rejectionPolicy: RejectionPolicy.QUARANTINE
);
```

---

### **5. Bulkhead Configuration**
| **Parameter**          | **Type**   | **Description**                                                                                     | **Default Value** |
|------------------------|------------|-----------------------------------------------------------------------------------------------------|-------------------|
| `concurrencyLimit`     | Integer    | Maximum concurrent executions allowed.                                                              | `10`              |
| `queueCapacity`        | Integer    | Maximum pending requests in the queue.                                                              | `50`              |
| `rejectPolicy`         | Enum       | `REJECT`, `WAIT`, or `THROTTLE`.                                                                   | `REJECT`          |

**Example (Pseudocode):**
```go
bulkhead := NewBulkhead(
    concurrencyLimit: 10,
    queueCapacity: 50,
    rejectPolicy: RejectPolicy.WAIT
)
```

---

## **Query Examples**

### **1. Circuit Breaker Trip Detection**
**Scenario:** A microservice fails 5 times in a row.
**Expected Behavior:** Circuit breaker trips after the 5th failure.

```http
# HTTP Request (after 5 failures)
POST /api/inventory/check-stock HTTP/1.1
Host: inventory-service.example.com
Retry-After: 300  # Circuit breaker reset in 5 minutes

# Response (503 Service Unavailable)
HTTP/1.1 503 Service Unavailable
Retry-After: 300
```

---

### **2. Retry with Exponential Backoff**
**Scenario:** A DB query fails, retries with delays.

| **Attempt** | **Delay (s)** | **Result**          |
|-------------|---------------|---------------------|
| 1           | 1             | **Failure**         |
| 2           | 2             | **Success**         |

**Logging Example:**
```
[00:00:00] Attempt 1/3 - Retrying in 1s... (Failed)
[00:00:01] Attempt 2/3 - Retrying in 2s... (Success)
```

---

### **3. Fallback Response**
**Scenario:** Primary service fails, fallback returns cached data.

```http
# Failed Primary Request (500 Internal Server Error)
GET /api/user/profile HTTP/1.1
Host: user-service.example.com
Cache-Control: max-age=300  # TTL from fallback

# Fallback Response (200 OK with stale data)
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user": {
    "id": "123",
    "name": "John Doe",  # Cached from 5 minutes ago
    "status": "degraded"
  }
}
```

---

### **4. Rate Limiting Enforcement**
**Scenario:** Client exceeds request limit (100 req/min).

```http
# First Request (Allowed)
GET /api/events HTTP/1.1
Host: events-service.example.com
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99

# 101st Request (Rejected)
GET /api/events HTTP/1.1
Host: events-service.example.com
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## **Related Patterns**
1. **Idempotency** – Ensures repeated requests have the same effect (complements retries).
2. **Saga Pattern** – Manages distributed transactions with fallback compensating actions.
3. **Chaos Engineering** – Proactively tests resilience by injecting failures.
4. **Circuit Breaker Fallback** – Combines circuit breakers with fallback mechanisms.
5. **Bulkhead Isolation** – Segments system components to prevent cascading failures.

---
**Best Practices:**
- **Monitor Resilience Metrics** (e.g., failure rates, retry counts, circuit breaker state).
- **Avoid Over-Retrying** (some failures are permanent; use circuit breakers).
- **Test Resilience** with chaos experiments (e.g., kill services randomly).
- **Log Resilience Events** for debugging (e.g., circuit breaker trips, fallback activations).

For further reading, refer to:
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Google’s Site Reliability Engineering (SRE) Book](https://sre.google/sre-book/table-of-contents/)