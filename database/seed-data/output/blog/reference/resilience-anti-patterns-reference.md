# **[Anti-Pattern] Resilience Anti-Patterns Reference Guide**

---

## **1. Overview**
Resilience Anti-Patterns refer to common pitfalls in architectural or implementation practices that undermine system reliability, fault tolerance, and recovery capabilities. Unlike established resilience patterns (e.g., Circuit Breaker, Retry with Backoff, Bulkheads), these anti-patterns introduce vulnerabilities that can lead to cascading failures, degraded performance, or complete system collapse under stress.

These anti-patterns often arise from shortcuts, misplaced optimizations, or a lack of foresight in handling failure scenarios. Recognizing and avoiding them is critical for building systems that can withstand disruptions—whether caused by external dependencies, hardware failures, or human error.

---

## **2. Key Anti-Patterns & Implementation Pitfalls**

| **Anti-Pattern**          | **Description**                                                                                     | **Impact**                                                                                     | **Example Scenario**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **1. Blind Retry**        | Naive retry mechanisms without backoff, jitter, or exponential delays.                              | Thundering herd problem; increased load on downstream systems; timeout exhaustion.          | A payment service keeps retrying a failed bank transaction at fixed intervals.         |
| **2. Retry Without Isolation** | Retrying operations without isolating failures (e.g., calling the same overloaded service).      | Amplifies failures (e.g., cascading timeouts, resource exhaustion).                         | A monolithic app retries database calls during a DB outage, worsening congestion.      |
| **3. Hard-Coded Timeouts** | Fixed, inflexible timeout values that don’t adapt to system load.                                | Under- or over-provisioning; poor user experience (e.g., slow responses or abrupt failures). | A web app times out API calls at 2 seconds for all users, failing during peak traffic.   |
| **4. No Circuit Breaker** | No mechanism to stop cascading failures after repeated retries.                                   | System-wide outages; wasted resources on failing operations.                                  | An e-commerce site keeps processing failed inventory checks, draining CPU/RAM.          |
| **5. Unbounded Retry Loops** | Infinite or excessively long retry loops without a failure threshold.                            | System hangs; resource starvation.                                                            | A background job retries forever after a network partition, never failing over.        |
| **6. Silent Failures**    | Swallowing exceptions or errors without logging or alerting.                                      | Undetected failures; degraded state; security risks (e.g., data loss).                     | A payment service silently drops failed transactions, leading to financial discrepancies. |
| **7. No Graceful Degradation** | Lack of fallback mechanisms (e.g., static data, degraded functionality).                         | Poor user experience; abrupt crashes during partial failures.                               | An app crashes entirely when a third-party API fails, instead of loading cached data.   |
| **8. Global Locking**     | Using coarse-grained locks (e.g., table-level locks) for all operations.                        | Bottlenecks; reduced concurrency; deadlocks.                                                | A distributed transaction system locks entire database tables during updates.           |
| **9. No Backpressure**     | Accepting requests at full capacity without throttling, even under load.                          | Overloading downstream systems; cascading failures.                                        | A chat server accepts unlimited messages during a database outage, crashing under load. |
| **10. Ignoring Metrics**  | Not monitoring failure rates, latency, or error patterns to inform resilience strategies.         | Blind spots in failure handling; delayed incident response.                                 | A service deploys new code without monitoring API error rates, missing a latent bug.    |
| **11. Single Point of Failure (SPOF) in Resilience Logic** | Centralized retry logic or recovery mechanisms (e.g., shared shared cache for retries).            | Single failure cascades; no redundancy in failure handling.                                  | All retries depend on a single in-memory cache; its crash halts recovery attempts.      |
| **12. Over-Reliance on Retries** | Treating retries as a silver bullet without addressing root causes (e.g., flaky APIs).           | Masking deeper problems; increased operational overhead.                                      | A system retries failed microservices indefinitely instead of fixing their instability.  |
| **13. No Chaos Engineering** | Lack of controlled failure testing (e.g., no "kill switch" or failure injection).               | Undiscovered fragilities; real-world failures have higher impact.                           | A production system fails catastrophically during an unplanned outage.                 |
| **14. Inconsistent Error Handling** | Different components handle errors inconsistently (e.g., some retry, others fail silently).     | Inconsistent behavior; debugging difficulties.                                              | API Gateway retries failures, but downstream services fail fast.                       |

---

## **3. Schema Reference**
Below is a structured breakdown of **anti-pattern properties** and their **mitigation strategies**:

| **Property**               | **Definition**                                                                                     | **Anti-Pattern Example**                          | **Mitigation Strategy**                                                                 |
|----------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------|----------------------------------------------------------------------------------------|
| **Retry Policy**           | Rules governing retry attempts (e.g., attempts, backoff, jitter).                                  | Fixed delay (e.g., `retry: 5 * 100ms`).           | Use **exponential backoff + jitter** (e.g., `maxRetries=3; delay=1s → 4s → 8s`).        |
| **Isolation Strategy**     | How failures are contained (e.g., bulkheads, circuit breakers).                                    | No isolation; all threads call the same DB.       | Implement **bulkheads** (e.g., thread pools per service) or **circuit breakers**.       |
| **Timeout Configuration**  | Hardcoded or dynamic timeout values.                                                              | `timeout=2s` for all endpoints.                     | Use **adaptive timeouts** (e.g., scale with load) or **context-aware defaults**.       |
| **Failure Monitoring**     | Tracking of failures (e.g., metrics, logs, alerts).                                              | No alerts for repeated DB timeouts.                | Instrument with **prometheus + alerts** (e.g., `rate(http_errors_total[5m]) > 0.1`).   |
| **Fallback Mechanism**     | Alternative behavior when primary fails (e.g., cache, degraded mode).                            | No fallback; app crashes on API failure.           | Design **graceful degradation** (e.g., fall back to static data).                       |
| **Resource Limits**        | Control over resource usage (e.g., concurrency limits, memory).                                  | Unbounded retries → OOM crashes.                   | Enforce **rate limiting** (e.g., `maxConcurrentRequests=50`) and **memory guards**.    |
| **Chaos Testing**          | Proactive failure simulation (e.g., kill pods in Kubernetes).                                    | No failure injection tests.                        | Run **chaos experiments** (e.g., `Chaos Mesh` or `Gremlin`).                            |
| **Error Handling Consistency** | Uniform error treatment across components.                                                        | Some services retry; others throw.                  | Define **centralized error policies** (e.g., `ErrorHandler` class).                     |
| **Circuit Breaker State**  | How circuit breakers reset (e.g., time-based vs. success-based).                                 | Circuit breaker never resets.                       | Use **sliding window** or **event-based** reset policies.                                |

---

## **4. Query Examples**
Below are **real-world scenarios** where anti-patterns appear and how to detect/fix them:

---

### **Example 1: Blind Retry in a Microservice**
**Anti-Pattern:**
A payment service retries failed bank API calls every 1 second without backoff:
```java
// ❌ Blind Retry
for (int i = 0; i < 5; i++) {
    bankApi.processPayment();  // Fixed 1s delay between retries
}
```

**Fix (Exponential Backoff + Jitter):**
```java
// ✅ Resilient Retry
RetryPolicy policy = RetryPolicyBuilder.newBuilder()
    .maxAttempts(5)
    .backoff(BackoffConfig.exponential(100, 2000))
    .jitter(JitterConfig.constant(100))
    .build();
bankApi.processPaymentWithRetry(policy);
```

---

### **Example 2: No Circuit Breaker in a Monolith**
**Anti-Pattern:**
A legacy monolith keeps retrying a failed database connection:
```python
# ❌ No Circuit Breaker
while True:
    try:
        db.connect()
        break
    except ConnectionError:
        time.sleep(1)  # Blind retry
```

**Fix (Circuit Breaker):**
```python
# ✅ Circuit Breaker (using Python `resilience` library)
from resilience import CircuitBreaker

@circuit_breaker(max_failures=3, reset_timeout=60)
def connect_db():
    return db.connect()
```

---

### **Example 3: Silent Failures in Log Processing**
**Anti-Pattern:**
A log parser silently drops malformed entries:
```go
// ❌ Silent Failure
func parseLog(line string) {
    // No error handling; drops bad logs silently
    json.Unmarshal([]byte(line), &event)
}
```

**Fix (Graceful Degradation + Metrics):**
```go
// ✅ Resilient Parsing
func parseLog(line string) (event *LogEvent, err error) {
    defer func() {
        if err != nil {
            metrics.IncFailedParses()
            log.Warnf("Failed to parse: %v", err)
        }
    }()
    return json.Unmarshal([]byte(line), &event)
}
```

---

### **Example 4: Global Locking in Distributed Systems**
**Anti-Pattern:**
A distributed order system locks the entire `orders` table:
```sql
-- ❌ Coarse-Grained Lock
LOCK TABLE orders IN SHARE MODE;
UPDATE orders SET status = 'processing' WHERE id = 123;
```

**Fix (Fine-Grained Locking):**
```sql
-- ✅ Fine-Grained Lock (row-level)
UPDATE orders SET status = 'processing' WHERE id = 123 FOR SHARE;
```

---

## **5. Related Patterns**
To mitigate resilience anti-patterns, leverage these complementary patterns:

| **Pattern**               | **Purpose**                                                                                     | **When to Use**                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**        | Stops cascading failures after a threshold of retries.                                            | When retrying external dependencies (e.g., APIs, databases).                                        |
| **Bulkhead**               | Isolates failures by limiting concurrency per component.                                          | To prevent resource exhaustion (e.g., thread pools, connection pools).                              |
| **Retry with Backoff**     | Reduces load on failing systems with exponential delays.                                         | For transient failures (e.g., network timeouts, DB retries).                                        |
| **Fallback**               | Provides degraded functionality when primaries fail.                                             | For critical paths (e.g., offline mode, cached data).                                               |
| **Rate Limiting**          | Controls request volume to avoid overloading systems.                                           | During peak traffic or when downstream services are slow.                                           |
| **Chaos Engineering**      | Proactively tests system resilience to failures.                                                 | During development or pre-deployment stages.                                                      |
| **Graceful Degradation**   | Maintains partial functionality under stress.                                                    | When full system failure is unacceptable (e.g., e-commerce checkout).                                |
| **Circuit Breaker Fallback** | Combines circuit breakers with fallback strategies.                                             | When primary failure requires temporary workarounds (e.g., retry with a backup service).            |

---

## **6. Detection & Remediation Checklist**
| **Step**                  | **Action**                                                                                       | **Tools/Techniques**                                                                               |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Audit Codebase**        | Search for blind retries, unbounded loops, or missing timeouts.                                 | Static analysis (e.g., **SonarQube**, **Checkmarx**), regex searches (`grep "while.*retry"`).     |
| **Review Metrics**        | Look for high error rates, throttled requests, or timeouts.                                     | **Prometheus**, **Grafana**, **New Relic**.                                                       |
| **Load Test**             | Simulate failure conditions (e.g., kill pods, inject latency).                                    | **Locust**, **k6**, **Chaos Mesh**.                                                              |
| **Chaos Experiments**     | Run controlled failures to expose fragilities.                                                   | **Gremlin**, **Chaos Monkey**.                                                                  |
| **Update Policies**       | Enforce retry backoff, circuit breakers, and timeouts in contracts.                            | **OpenAPI/Swagger** specs, **Contract Tests**.                                                    |
| **Monitor Culture**       | Train teams on resilience patterns and anti-patterns.                                           | **Code reviews**, **technical blogs**, **post-mortems**.                                           |

---
**Key Takeaway:**
Resilience anti-patterns often stem from **shortcuts in failure handling**. Replace them with **explicit policies** (retries, timeouts, circuit breakers) and **observability** (metrics, logs). Proactively test failure scenarios to avoid surprises in production.