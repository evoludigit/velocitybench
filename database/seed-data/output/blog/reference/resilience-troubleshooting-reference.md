**[Pattern] Resilience Troubleshooting – Reference Guide**

---

### **Overview**
The **Resilience Troubleshooting** pattern helps identify, diagnose, and mitigate failures in distributed systems by analyzing resilience mechanisms (e.g., retries, circuit breakers, fallbacks, and rate limiting). This guide provides structured approaches to detecting resilience-related issues and applying corrective actions efficiently.

Resilience patterns are critical in modern architectures to handle transient failures, dependencies, and overloads. When these mechanisms fail (e.g., retries loop indefinitely, circuit breakers open prematurely, or fallbacks degrade service), they can amplify outages. This pattern ensures you can:
- **Detect** resilience-related failures via observability tools (logs, metrics, traces).
- **Diagnose** why resilience mechanisms are malfunctioning (e.g., misconfigured thresholds, unhandled exceptions).
- **Resolve** issues with targeted fixes (e.g., adjusting retry logic, improving fallback logic).

This guide focuses on **key components**, **troubleshooting steps**, and **implementation details** for common resilience strategies.

---

### **Schema Reference**
Below are **tables outlining key resilience mechanisms**, their common failure modes, and troubleshooting checklists.

| **Component**       | **Purpose**                          | **Failure Modes**                                                                 | **Troubleshooting Checks**                                                                                     |
|---------------------|--------------------------------------|-------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Retry Policy**    | Automatically retry failed requests   | - Infinite retries <br> - Too aggressive retries (increase load) <br> - Ignored exceptions | - Verify `maxRetries` and `backoff` settings <br> - Confirm retryable exceptions are handled <br> - Check for cascading retries |
| **Circuit Breaker** | Prevents cascading failures           | - Breaker trips too often (false positives) <br> - Never resets (false negatives)  | - Review `failureThreshold` and `resetTimeout` <br> - Check error classification logic <br> - Test with load simulations |
| **Fallback/Degradation** | Provides graceful degradation   | - Fallback fails <br> - Overuse of fallback degrades performance <br> - Not triggered when expected | - Validate fallback logic and dependencies <br> - Monitor fallback invocation rates <br> - Ensure graceful degradation doesn’t break SLOs |
| **Rate Limiting**   | Protects against overload            | - Too restrictive (blocking valid traffic) <br> - Too lenient (DDoS vulnerability) | - Verify rate limits per client/endpoint <br> - Check burst tolerance settings <br> - Test with traffic spikes |
| **Bulkhead**        | Isolates resource contention         | - Thread pool exhaustion <br> - Ineffective isolation (shared resources)         | - Monitor thread pool metrics (e.g., `activeThreads`, `rejectedTasks`) <br> - Audit shared dependency usage |
| **Timeouts**        | Prevents hanging operations          | - Too short (misses legitimate delays) <br> - Too long (wastes resources)         | - Validate timeout values for latency characteristics <br> - Check for unhandled `TimeoutException` |

---

### **Key Troubleshooting Steps**
Use the **five-step framework** below to diagnose resilience issues systematically.

#### **1. Identify the Symptom**
- **Symptoms of Resilience Failures:**
  - Sudden spikes in **error rates** or **latency**.
  - **Cascading failures** after a single component fails.
  - **Unintended retries** or **overloaded fallback services**.
  - **Circuit breakers stuck open** or **never resetting**.

- **Observability Tools to Use:**
  - **Metrics:** Error rates, retry counts, circuit breaker state.
  - **Logs:** Filter for `Retry`, `Fallback`, or `CircuitBreaker` logs.
  - **Traces:** Identify slow or failed dependencies (e.g., database timeouts).

#### **2. Reproduce the Issue**
- **Test Scenarios:**
  - Simulate **high load** to trigger retries/rate limiting.
  - Inject **artificial failures** (e.g., mock service errors).
  - Verify **edge cases** (e.g., network partitions, dependency downtime).

- **Tools for Reproduction:**
  - **Chaos Engineering:** Tools like **Gremlin** or **Chaos Monkey**.
  - **Load Testing:** **JMeter**, **k6**, or **Locust**.
  - **Mock Services:** **WireMock**, **Postman**.

#### **3. Diagnose the Root Cause**
| **Failure Scenario**       | **Root Cause Hypotheses**                                                                 | **Diagnostic Queries/Commands**                                                                 |
|----------------------------|-----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Infinite Retries**       | - Retryable exceptions are not caught <br> - `maxRetries` misconfigured                 | ```grep "Retry.*Exception" /var/log/app.log | tail -n 50``` <br> Check `maxRetries` in config (e.g., `application.yml`). |
| **Circuit Breaker Stuck Open** | - Failure threshold too low <br> - Errors not classified correctly                 | ```promql query: rate(circuit_breaker_failures_total[5m]) or error_classification_logs```        |
| **Fallback Degrades Performance** | - Fallback is slow or inefficient <br> - Overused due to misconfigured breakers       | ```profile fallback_service_latency (pprof or distrac```) <br> Check fallback invocation metrics. |
| **Rate Limiting Too Aggressive** | - Throttling valid traffic <br> - Incorrect rate limit per endpoint               | ```curl -H "X-RateLimit-Limit: 100" http://api.example.com``` <br> Check rate limit headers. |

#### **4. Apply Fixes**
| **Failure**               | **Recommended Fixes**                                                                                     | **Validation Steps**                                                                                  |
|---------------------------|---------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Retry Issues**          | - Adjust `maxRetries` and `backoff` <br> - Log retryable vs. non-retryable exceptions                 | Deploy fix; monitor `retry_failure_rate` metrics.                                                  |
| **Circuit Breaker Misbehavior** | - Tune `failureThreshold` and `resetTimeout` <br> - Improve error classification logic          | Run load test; verify breaker state transitions in observability dashboard.                       |
| **Fallback Problems**     | - Optimize fallback logic <br> - Cache fallback responses <br> - Add circuit breaker for fallbacks  | A/B test fallback; ensure no regression in error rates.                                            |
| **Rate Limiting Too Strict** | - Increase rate limits <br> - Use adaptive throttling (e.g., token bucket algorithm)          | Check user feedback on blocked requests; adjust dynamically.                                         |

#### **5. Validate the Resolution**
- **Post-Fix Metrics to Monitor:**
  - **Error rates** (should decrease).
  - **Retry counts** (should stabilize).
  - **Circuit breaker state** (should reset normally).
  - **Fallback invocation rates** (should reduce if fixed).
  - **Latency percentiles** (should improve or stay stable).

- **Automated Validation:**
  - **Unit Tests:** Verify resilience logic in isolation (e.g., mock failovers).
  - **Integration Tests:** Test end-to-end with simulated failures.
  - **Chaos Tests:** Re-run chaos experiments post-fix.

---

### **Query Examples**
#### **1. Detecting Retry Loop in Logs (Gelf/Grafana)**
```bash
# Filter logs for retry loops (e.g., Spring Retry)
grep -i "retry\|attempt" /var/log/app.log | awk '{print $1, $2, $NF}' | sort | uniq -c | sort -nr
```
**Expected Output:**
```
1500 2024-05-20T12:00:00 retry_successful
50   2024-05-20T12:00:05 retry_failed_after_5_attempts
```

#### **2. PromQL Query for Circuit Breaker State**
```promql
# Check if circuit breaker is open for a specific service
rate(circuit_breaker_open_total{service="payment_api"}[1m]) > 0
```
**Alert Rule:**
```
IF rate(circuit_breaker_open_total[1m]) > 0 THEN alert("CircuitBreakerOpen") ELSE ignore
```

#### **3. SQL Query for Fallback Degradation (PostgreSQL)**
```sql
-- Identify endpoints where fallbacks are overused
SELECT
    endpoint,
    COUNT(*) as fallback_invocations,
    AVG(response_time) as avg_fallback_time
FROM fallback_logs
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY endpoint
HAVING COUNT(*) > 1000  -- Threshold for "overuse"
ORDER BY avg_fallback_time DESC;
```

#### **4. Kubernetes Event Dump for Resource Exhaustion (Bulkhead)**
```bash
# Check pod events for OOM or CPU throttling
kubectl describe pod <pod-name> | grep -i "limited\|oom\|throttled"
```
**Example Output:**
```
Warning  CPUThrottled  3m (x10 over 1h)  kubelet            pod had high CPU throttling
Warning  OOMKilled      1m               kubelet            container killed due to OOM
```

---

### **Implementation Details**
#### **1. Retry Policy Best Practices**
- **Exponential Backoff:** Start with `initialInterval=100ms`, `maxInterval=10s`.
- **Retryable Exceptions:** Only retry transient errors (e.g., `Timeout`, `ConnectionRefused`).
  ```yaml
  # Example: Spring Retry Configuration
  spring:
    retry:
      max-attempts: 3
      backoff:
        initial-interval: 1s
        max-interval: 10s
        multiplier: 2.0
  ```
- **Circuit Breaker Integration:** Combine with Hystrix/Resilience4j.
  ```java
  @Retryable(value = {TimeoutException.class}, maxAttempts = 3)
  public User getUser(String id) {
      return userService.fetchUser(id);
  }
  ```

#### **2. Circuit Breaker Tuning**
| **Parameter**       | **Recommendation**                                                                 |
|---------------------|------------------------------------------------------------------------------------|
| `failureThreshold`  | Start with **5 failed calls in 10s**; adjust based on SLA.                          |
| `resetTimeout`      | Set to **30s–2m** (longer if recovery is slow).                                     |
| `automaticTransitionFromOpenToHalfOpen` | Enable if you want to test recovery.            |

#### **3. Fallback Design**
- **Cache Fallbacks:** Use **Redis** or **CDN** for fast responses.
- **Graceful Degradation:** Return **cached data** or **stale reads** instead of failing.
  ```python
  # Example: Fallback with caching (FastAPI)
  from fastapi import HTTPException
  from caches import cached

  @cached(ttl=300)
  async def fallback_get_user(user_id: str):
      try:
          return await user_service.get_user(user_id)
      except Exception:
          return {"status": "degraded", "data": "cached_response"}
  ```

#### **4. Rate Limiting Strategies**
| **Algorithm**       | **Use Case**                          | **Implementation**                                                                 |
|---------------------|---------------------------------------|-----------------------------------------------------------------------------------|
| **Fixed Window**    | Simple rate limiting                  | Use `Redis` or `Token Bucket` with fixed slots.                                  |
| **Sliding Window**  | Accurate per-second limiting          | Track requests in a time window; use `Leaky Bucket`.                              |
| **Adaptive**        | Dynamic limits (e.g., burst tolerance)| Combine with **machine learning** to adjust limits based on traffic patterns.    |

#### **5. Bulkhead Isolation**
- **Thread Pools:** Limit concurrent executions per component.
  ```java
  // Thread Pool Bulkhead (Java)
  ExecutorService bulkhead = Executors.newFixedThreadPool(10);
  bulkhead.submit(() -> { /* task */ });
  ```
- **Custom Isolators:** Use **Resilience4j Bulkhead**:
  ```java
  Bulkhead bulkhead = Bulkhead.of("userService", 10);
  bulkhead.executeRunnable(() -> {
      userService.processRequest();
  });
  ```

#### **6. Timeout Strategies**
- **Context Propagation:** Ensure timeouts propagate across async calls (e.g., **Spring Cloud Sleuth**).
  ```yaml
  # Spring Cloud Sleuth Timeout Configuration
  spring:
    sleuth:
      sampler:
        probability: 1.0
    cloud:
      circuitbreaker:
        enabled: true
  ```
- **Graceful Degradation on Timeout:** Log and return a `429 Too Many Requests` instead of failing.

---

### **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **Connection to Resilience Troubleshooting**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures                                                 | Troubleshooting requires verifying breaker thresholds and reset logic.                                       |
| **Bulkhead**              | Isolates resource contention                                                | Diagnose thread pool exhaustion or shared dependency issues.                                               |
| **Rate Limiting**         | Protects against overload                                                   | Tuning requires analyzing throttling policies and false positives.                                          |
| **Retry as a Service**    | Manages retries centrally                                                  | Centralized retries simplify logging and debugging of retry loops.                                         |
| **Chaos Engineering**     | Proactively tests resilience                                               | Use chaos experiments to reproduce and validate fixes for resilience issues.                                |
| **Observability**         | Monitors system health                                                    | Essential for detecting resilience-related failures (logs, metrics, traces).                               |
| **Fallback/Degradation**  | Provides graceful degradation                                             | Troubleshoot when fallbacks fail or are overused.                                                         |

---

### **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------|
| **Over-Reliance on Retries**         | Leads to cascading failures. Use **circuit breakers** to complement retries.                     |
| **Ignoring Non-Transient Errors**     | Retrying permanent failures (e.g., `404 Not Found`). Use **retry filters** to exclude them.       |
| **Static Rate Limits**               | Can block legitimate traffic spikes. Use **adaptive limits** or **burst tolerance**.             |
| **Fallbacks Without Monitoring**      | Hidden performance bottlenecks. Monitor fallback invocation rates and latency.                   |
| **No Integration Testing**           | Resilience logic may fail in production. Test with **chaos engineering**.                          |

---
**Final Notes:**
- **Resilience is iterative:** Adjust thresholds based on real-world failure patterns.
- **Automate alerts:** Set up dashboards (e.g., **Grafana**) for resilience metrics.
- **Document fixes:** Update runbooks for recurring resilience issues.

For further reading, see:
- [Resilience4j Documentation](https://resilience4j.readme.io/)
- [Chaos Engineering Handbook](https://chaosengineering.io/handbook/)
- [Spring Retry Reference](https://docs.spring.io/spring-retry/docs/current/reference/html/)