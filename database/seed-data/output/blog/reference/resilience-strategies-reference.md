# **[Pattern] Resilience Strategies – Reference Guide**

---

## **Overview**
The **Resilience Strategies** pattern ensures systems gracefully handle failures, unexpected workloads, or transient errors by applying automated compensation mechanisms. This pattern builds robustness into distributed architectures, microservices, and event-driven systems by implementing fault-tolerant behaviors like retries, circuit breakers, bulkheads, fallbacks, and rate limiting.

Key benefits include:
- **Fault isolation** (preventing cascading failures)
- **Improved user experience** (smooth degradation under load)
- **Operational stability** (automated recovery from transient errors)
- **Resource optimization** (preventing overloading critical dependencies)

This pattern is commonly applied in **cloud-native architectures, event-driven workflows, and high-availability systems**.

---

## **Schema Reference**
| **Component**          | **Description**                                                                 | **Implementation Options**                                                                 | **Key Properties**                                                                 |
|------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Retry Mechanism**    | Automatically attempts operations after failures.                                | Exponential backoff, fixed delays, jitter (randomized delays).                          | Max retries, retry interval, failure threshold, circuit breaker integration.       |
| **Circuit Breaker**    | Stops cascading failures if a dependency fails repeatedly.                      | Circuit breaker states (closed/open/half-open), automatic recovery thresholds.           | Error threshold, timeout, reset delay, fallback action.                            |
| **Bulkhead**           | Limits concurrent executions to prevent resource exhaustion.                     | Thread pools (fixed/synchronous), connection pools, concurrency limits.                 | Pool size, queue capacity, resource isolation (CPU/memory/network).               |
| **Fallback**           | Provides alternative behavior when primary operations fail.                     | Static responses, cached data, degraded functionality, user notifications.               | Fallback priority, degradation level, retry-first vs. fallback-first.             |
| **Rate Limiting**      | Controls request volume to prevent overload.                                    | Fixed window, sliding window, token bucket algorithms.                                | Rate limits (RPS/QPS), burst tolerance, whitelisting/prioritization.              |
| **Bulkhead Isolation** | Further isolates bulkhead implementations per service/function.                 | Nested bulkheads, per-call isolation, tenant-specific quotas.                          | Isolation granularity, isolation context (user/service).                          |
| **Chaos Engineering**  | Proactively tests resilience by injecting failures.                              | Simulated latency, node failures, network partitions, data corruption.                  | Trigger conditions, monitoring hooks, recovery validation.                         |
| **Degradation Policies**| Gradually reduces functionality under stress.                                    | Progressive degradation (disable non-critical features), load shedding.                 | Degradation triggers (CPU/memory/latency), priority-based shutdowns.               |

---

## **Implementation Details**
### **1. Retry Mechanism**
**Purpose**: Recover from transient failures (e.g., temporary network outages, throttled APIs).

**Best Practices**:
- Use **exponential backoff** to avoid overwhelming dependencies:
  `retryDelay = baseDelay * (2^attempt) + jitter`.
- Avoid retries for **idempotent** operations (e.g., `POST /order` without duplicates).
- **Do not retry**: Timeouts, 500 errors without retriable state, or operations with side effects.

**Example (Java/Python)**:
```java
RetryPolicy retryPolicy = RetryPolicyBuilder.newBuilder()
    .maxAttempts(3)
    .retryInterval(RetryInterval.exponential(RetryInterval.TimeUnit.SECONDS, 1, 2))
    .build();
```

```python
from tenacity import retry, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def call_external_api():
    ...
```

---

### **2. Circuit Breaker**
**Purpose**: Stop cascading failures after repeated dependency errors.

**States**:
| State       | Description                                                                 | Action                                                                 |
|-------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Closed**  | Normal operation; allows requests.                                          | Track failures.                                                         |
| **Open**    | Dependency fails; blocks requests.                                          | Fallback or error response.                                             |
| **Half-Open** | Tentatively resumes requests after recovery timeout.                       | Monitor for success/failure to transition back to closed.                |

**Implementation Libraries**:
- **Java**: [Resilience4j](https://resilience4j.readme.io/docs/circuit-breaker)
- **Python**: [PyResilience4J](https://pypi.org/project/py-resilience4j/)
- **Node.js**: [opossum](https://github.com/plantain-00/opossum)

**Example (Circuit Breaker + Retry)**:
```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(50) // Fail after 50% errors
    .waitDurationInOpenState(Duration.ofSeconds(10))
    .permittedNumberOfCallsInHalfOpenState(2)
    .slidingWindowType(SlidingWindowType.COUNT_BASED)
    .slidingWindowSize(5)
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("apiService", config);
circuitBreaker.executeSuppliedCommand(command ->
    callExternalApiWithRetry(command));
```

---

### **3. Bulkhead**
**Purpose**: Prevent resource exhaustion by limiting concurrent executions.

**Types**:
| Type               | Description                                                                 | Use Case                                                                 |
|--------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Synchronous**    | Fixed thread pool for synchronous work.                                    | CPU-bound tasks (e.g., PDF generation).                                  |
| **Asynchronous**   | Queues requests to avoid overload.                                           | I/O-bound tasks (e.g., DB calls).                                        |
| **Connection Pool**| Limits concurrent connections to a dependency (e.g., DB, HTTP clients).     | External service calls.                                                  |
| **Tenant-Specific**| Isolates bulkheads per user/org to prevent one tenant from starving others.| Multi-tenant applications.                                               |

**Example (Connection Pool Bulkhead)**:
```python
from resilience4j.bulkhead import Bulkhead
from resilience4j.registry import Resilience4jRegistry

registry = Resilience4jRegistry()
bulkhead = Bulkhead.of("connectionPool", BulkheadConfig.custom()
    .maxConcurrentCalls(10)
    .maxWaitDuration(Duration.ofMillis(100))
    .build(), registry)

def call_api():
    bulkhead.execute(() -> external_api_call())
```

---

### **4. Fallback Mechanisms**
**Purpose**: Provide graceful degradation when primary operations fail.

**Strategies**:
1. **Static Fallback**: Hardcoded response (e.g., default user data).
2. **Dynamic Fallback**: Cached or degraded data (e.g., stale product listings).
3. **User Notification**: Alert users of service degradation (e.g., "Order processing delayed").
4. **Retry-First**: Attempt retry before fallback (if operation is idempotent).

**Example (Fallback with Resilience4j)**:
```java
FallbackConfig fallbackConfig = FallbackConfig.custom()
    .fallbackSupplier((Exception ex) -> fallbackResponse())
    .build();

Fallback fallback = Fallback.of("orderService", fallbackConfig, registry);
fallback.executeSuppliedCommand(command -> placeOrder(command));
```

---

### **5. Rate Limiting**
**Purpose**: Prevent abuse and resource exhaustion by enforcing request quotas.

**Algorithms**:
| Algorithm       | Description                                                                 | When to Use                                                                 |
|-----------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Fixed Window**| Counts requests in a fixed time window (e.g., 1000 requests/second).       | Simple rate limiting.                                                      |
| **Sliding Window**| Adjusts window dynamically based on request timestamps.                   | More accurate for bursty traffic.                                           |
| **Token Bucket** | Releases tokens at a fixed rate; requests consume tokens.                  | Smooth throttling (e.g., API keys).                                        |

**Example (Fixed Window)**:
```java
RateLimiterConfig config = RateLimiterConfig.custom()
    .limitForPeriod(100) // Max 100 requests
    .timeUnit(TimeUnit.SECONDS)
    .timeoutDuration(Duration.ofMillis(100))
    .build();

RateLimiter rateLimiter = RateLimiter.of("apiLimit", config, registry);
rateLimiter.executeRunnable(() -> processRequest());
```

---

### **6. Bulkhead Isolation**
**Purpose**: Further segmented bulkheads to avoid cross-service starvation.

**Granularity Options**:
- **Per Service**: Isolate bulkheads by service boundary.
- **Per Function**: Isolate per operation (e.g., `AuthService.getUser()` vs. `AuthService.refreshToken()`).
- **Per Tenant**: Quotas per user/org (e.g., 10 concurrent payments per account).

**Example (Nested Bulkheads)**:
```java
// Top-level bulkhead (e.g., "paymentService")
Bulkhead paymentBulkhead = Bulkhead.of("paymentService", ...);

// Nested bulkhead for "processPayment"
Bulkhead paymentProcessing = Bulkhead.of("processPayment", ...,
    Registry.of("paymentService"));
paymentBulkhead.execute(() -> paymentProcessing.execute(() -> chargeCard()));
```

---

### **7. Chaos Engineering**
**Purpose**: Proactively test resilience by injecting failures.

**Techniques**:
- **Simulated Latency**: Add delays to measure timeouts.
- **Node Failures**: Kill containers/pods to test failover.
- **Network Partitions**: Isolate services to test isolation.
- **Data Corruption**: Inject errors in DB calls.

**Tools**:
- **Gremlin** (Netflix chaos engineering tool).
- **Chaos Mesh** (Kubernetes-native chaos engineering).
- **Chaos Monkey** (Spotify’s pod killer).

**Example (Chaos Mesh YAML)**:
```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: partition-pod
spec:
  action: partition
  mode: one
  selector:
    namespaces:
      - default
    labelSelectors:
      app: my-app
  duration: "30s"
```

---

### **8. Degradation Policies**
**Purpose**: Gracefully degrade functionality under load.

**Strategies**:
- **Priority-Based**: Disable non-critical features first (e.g., analytics before core payments).
- **Load Shedding**: Reject requests during peak load (e.g., HTTP 429 for APIs).
- **Dynamic Resource Allocation**: Shift resources to critical paths.

**Example (Priority Degradation)**:
| Priority | Feature          | Action on Degradation                          |
|----------|------------------|-----------------------------------------------|
| 1        | Payments         | Maintain (critical).                           |
| 2        | Recommendations  | Disable (fallback to static suggestions).       |
| 3        | Analytics        | Pause collection until load improves.          |

---

## **Query Examples**
### **1. Retry Failed API Calls**
**Scenario**: A microservice calls an external payment gateway that occasionally fails.
**Query**:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)  # Retry on any exception
)
def process_payment(order_id):
    response = requests.post(f"https://api.payments.com/process", json={"order_id": order_id})
    response.raise_for_status()  # Retry if HTTP error
    return response.json()
```

---

### **2. Circuit Break for Database Calls**
**Scenario**: A service queries a slow or failing database.
**Query**:
```java
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(70)  // Open after 70% errors
    .slowCallDurationThreshold(Duration.ofSeconds(2))  # Consider >2s as "slow"
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("dbService", config);

circuitBreaker.executeSupplier(() -> {
    return database.query("SELECT * FROM orders WHERE status='pending'");
});
```

---

### **3. Rate-Limited User Authentications**
**Scenario**: Limit failed login attempts to prevent brute-force attacks.
**Query**:
```java
RateLimiterConfig config = RateLimiterConfig.custom()
    .limitForPeriod(5)  // Max 5 attempts
    .timeUnit(TimeUnit.MINUTES)
    .timeoutDuration(Duration.ofMillis(500))
    .build();

RateLimiter rateLimiter = RateLimiter.of("auth-attempts", config);

public String attemptLogin(String username, String password) {
    if (!rateLimiter.tryAcquire()) {
        throw new TooManyRequestsException("Rate limit exceeded");
    }
    // Proceed with login logic...
}
```

---

### **4. Bulkhead for Order Processing**
**Scenario**: Limit concurrent order processing to avoid DB overload.
**Query**:
```java
BulkheadConfig bulkheadConfig = BulkheadConfig.custom()
    .maxConcurrentCalls(20)  // Max 20 concurrent orders
    .maxWaitDuration(Duration.ofMillis(500))  // Queue requests for 500ms
    .build();

Bulkhead bulkhead = Bulkhead.of("orderProcessing", bulkheadConfig);

bulkhead.executeSupplier(() -> {
    return processOrder(order);
});
```

---

## **Related Patterns**
| Pattern                     | Description                                                                 | When to Use                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Circuit Breaker**         | Stops cascading failures in dependent services.                            | When a service depends on unstable APIs.                                   |
| **Retry + Exponential Backoff** | Automatically retries operations with delayed attempts.                   | For transient network/DB errors.                                           |
| **Bulkhead Pattern**        | Isolates resource usage to prevent overload.                               | For CPU/memory/network-bound services.                                     |
| **Fallback Pattern**        | Provides alternative behavior when primary operations fail.                 | For gracefully degrading user experience.                                  |
| **Rate Limiting**           | Controls request volume to prevent abuse.                                   | For APIs, payment gateways, or public-facing endpoints.                    |
| **Saga Pattern**            | Manages distributed transactions across services.                         | For long-running workflows (e.g., order fulfillment).                      |
| **Asynchronous Processing** | Decouples synchronous calls using queues/events.                          | For non-critical background tasks.                                         |
| **Caching**                 | Reduces load on downstream services by storing responses.                  | For read-heavy operations (e.g., product catalogs).                        |
| **Chaos Engineering**       | Proactively tests resilience by injecting failures.                        | During development or disaster recovery drills.                            |
| **Resilience at the Edge**  | Deploys resilience logic in CDNs/edge servers.                              | For global low-latency requirements.                                       |
| **Multi-Region Deployment** | Distributes services across regions for fault tolerance.                   | For global applications with strict uptime SLA.                            |

---

## **Anti-Patterns & Pitfalls**
1. **Over-Retrying**: Retrying non-idempotent operations (e.g., `DELETE`) can cause data loss.
2. **No Circuit Breaker**: Allowing cascading failures when a dependency fails.
3. **Unbounded Bulkheads**: No limits on concurrency → resource exhaustion.
4. **Fallback Complexity**: Over-engineering fallbacks instead of simple degradations.
5. **Ignoring Metrics**: Not monitoring retry/circuit breaker stats → blind spots.
6. **Static Rate Limits**: Fixed limits that don’t adapt to traffic spikes.
7. **Chaos Without Observability**: Injecting chaos without logging/monitoring recovery.
8. **Global Bulkheads**: One bulkhead for all services → starves critical paths.