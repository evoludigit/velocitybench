# **[Pattern] Resilience Debugging Reference Guide**

---

## **Overview**
Resilience debugging is a structured approach to identifying, diagnosing, and resolving failures in resilient systems, particularly those built with patterns like **Retry**, **Circuit Breaker**, **Bulkhead**, **Fallback**, or **Rate Limiting**. Unlike traditional debugging, which focuses on individual component failures, resilience debugging examines:
- **Failure patterns** (e.g., cascading failures, throttling, or delayed retries).
- **Resilience policy misconfigurations** (e.g., incorrect timeouts, retry limits, or fallback logic).
- **Observability gaps** (e.g., missing metrics, logs, or tracing for resilience components).
- **Environment-specific issues** (e.g., degraded performance under high load).

This guide provides a structured methodology for diagnosing resilience-related failures, supported by schemas for querying distributed traces, logs, and metrics, and references to related resilience patterns.

---

## **Key Concepts**
To debug resilience issues effectively, understand these foundational concepts:

| **Concept**               | **Definition**                                                                                     | **Common Pitfalls**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Resilience Policy**     | Rules (retry count, timeout, circuit breaker threshold) governing how a system recovers from failure. | Over-aggressive policies (e.g., too many retries) or underprotective (e.g., no circuit breaker). |
| **Failure Mode**          | How a system behaves under failure (e.g., graceful degradation vs. cascading failures).            | Ignoring fallback mechanisms or assuming retries always succeed.                     |
| **Observability Triad**   | **Logs** (textual context), **Metrics** (quantitative trends), and **Traces** (request flow).     | Inadequate sampling or missing correlation IDs in logs.                               |
| **Canary Analysis**       | Testing resilience changes in a subset of traffic before full rollout.                             | Skipping validation or misinterpreting partial results.                              |

---

## **Implementation Details**
### **1. Debugging Workflow**
Follow this structured approach to diagnose resilience issues:

1. **Reproduce the Issue**
   - Confirm the failure (e.g., slow responses, timeouts, or degraded performance).
   - Check if it’s intermittent or consistent.

2. **Isolate the Resilience Component**
   - Use traces/logs to identify which resilience pattern (Retry, Circuit Breaker, etc.) is involved.
   - Example: Is a service failing due to `RetryPolicy` exhaustion or a `CircuitBreaker` tripping?

3. **Validate Resilience Policies**
   - Compare current policies against expected behavior (e.g., retry count vs. observed failures).
   - Query metrics to check if policies are being applied correctly.

4. **Check Observability**
   - Ensure traces include resilience-specific fields (e.g., `retry_count`, `circuit_breaker_state`).
   - Correlate logs with metrics (e.g., spikes in latency coinciding with failed retries).

5. **Test Local Fixes**
   - Adjust policies (e.g., reduce retry count) and monitor impact.
   - Use canary deployments to validate changes safely.

6. **Document Findings**
   - Record the root cause (e.g., "CircuitBreaker threshold too low").
   - Update alerting rules if new patterns emerge.

---

### **2. Schema Reference**
Below are key schemas for querying resilience-related data. Use these with tools like **OpenTelemetry**, **Prometheus**, or **ELK Stack**.

#### **A. Resilience Trace Schema (OpenTelemetry)**
| **Field**               | **Type**   | **Description**                                                                                     | **Example Values**                          |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `span.kind`             | String     | Type of span (server/client).                                                                       | "CLIENT", "SERVER"                          |
| `resilience.pattern`    | String     | Resilience pattern applied (e.g., `retry`, `circuit_breaker`).                                        | "retry", "bulkhead"                         |
| `resilience.retry_count`| Integer    | Number of retries attempted for this span.                                                            | 3                                           |
| `resilience.state`      | String     | Current state of resilience component (e.g., `open`, `half_open`, `closed`).                          | "open", "half_open"                         |
| `resilience.fallback`   | Boolean    | Whether a fallback was triggered.                                                                      | `true`, `false`                             |
| `resilience.error`      | String     | Error code or type (e.g., `timeout`, `rate_limited`).                                                 | "timeout", "503"                            |
| `resilience.timeout_ms` | Integer    | Timeout duration for this operation.                                                                   | 5000                                        |

**Example Trace Query (OpenTelemetry Query Language):**
```sql
SELECT
  service_name,
  resilience.pattern,
  resilience.retry_count,
  resilience.state,
  duration_ms
FROM traces
WHERE resilience.pattern = "retry"
  AND resilience.retry_count > 5
ORDER BY duration_ms DESC
LIMIT 10;
```

---

#### **B. Resilience Metrics Schema (Prometheus)**
| **Metric**               | **Type**   | **Description**                                                                                     | **Example Label Selectors**               |
|--------------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `resilience_retries_total` | Counter    | Total number of retries across all services.                                                         | `service="payment-service"`                |
| `resilience_circuit_open_duration_seconds` | Gauge | Duration the circuit breaker has been in the `open` state.         | `service="order-service", circuit="paypal"` |
| `resilience_fallback_invoked_total` | Counter | Number of times a fallback was triggered.                                                                 | `service="auth-service"`                  |
| `resilience_latency_quantile` | Histogram | Latency distribution for retried requests (e.g., 99th percentile).                                  | `resilience_pattern="bulkhead"`           |
| `resilience_throttled_requests_total` | Counter | Requests rejected due to rate limiting.                                                                 | `service="cache-service"`                 |

**Example PromQL Query:**
```promql
# Retries per second for a specific service
rate(resilience_retries_total{service="payment-service"}[5m])

# Circuit breaker state changes
resilience_circuit_open_duration_seconds{service="order-service"} > 0
```

---

#### **C. Log Fields for Resilience Debugging**
Include these fields in logs for correlation:

| **Field**               | **Description**                                                                                     | **Example**                                |
|-------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `resilience.pattern`    | Resilience pattern applied.                                                                         | `{"retry": {"maxAttempts": 3}}`             |
| `resilience.attempt`    | Current retry attempt number.                                                                       | `2`                                        |
| `resilience.fallback_used` | Whether a fallback was invoked.                                                                      | `true`                                     |
| `resilience.error_type`  | Type of failure (e.g., `timeout`, `rate_limited`).                                                   | `timeout`                                  |
| `resilience.trace_id`    | Correlation ID for tracing across logs.                                                                | `123e4567-e89b-12d3-a456-426614174000`     |

**Example Log Entry:**
```json
{
  "timestamp": "2023-10-15T12:00:00Z",
  "level": "ERROR",
  "resilience": {
    "pattern": "retry",
    "attempt": 3,
    "maxAttempts": 3,
    "error_type": "timeout",
    "trace_id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "message": "Request to downstream service timed out after 3 retries."
}
```

---

## **Query Examples**
### **Example 1: Debugging Retry Exhaustion**
**Issue:** A service fails intermittently after 3 retries, but logs don’t show the root cause.

**Steps:**
1. **Query Traces:**
   ```sql
   SELECT
     span.name,
     resilience.pattern,
     resilience.retry_count,
     resilience.error
   FROM traces
   WHERE resilience.pattern = "retry"
     AND resilience.retry_count = 3
     AND resilience.error = "timeout"
   ORDER BY timestamp DESC
   LIMIT 5;
   ```
   *Expected:* Identify which downstream service is timing out.

2. **Check Metrics:**
   ```promql
   rate(resilience_retries_total{service="order-service", resilience.pattern="retry"}[1m])
   ```
   *Expected:* Confirm if retries are spiking before failures.

3. **Inspect Logs:**
   Filter for `resilience.attempt=3` and `error_type=timeout`.

---

### **Example 2: Circuit Breaker Tripping**
**Issue:** A `CircuitBreaker` is opening unexpectedly, causing cascading failures.

**Steps:**
1. **Query Metrics for State Changes:**
   ```promql
   histogram_quantile(0.99, resilience_latency_quantile{resilience.pattern="circuit_breaker"}) > 1000
   ```
   *Expected:* High latency may trigger the breaker prematurely.

2. **Trace the Circuit Breaker State:**
   ```sql
   SELECT
     timestamp,
     resilience.state,
     resilience.error
   FROM traces
   WHERE resilience.pattern = "circuit_breaker"
     AND resilience.state = "open"
   ORDER BY timestamp DESC;
   ```
   *Expected:* Correlate with error types (e.g., `500` errors).

3. **Update Policy:**
   Adjust the failure threshold in the `CircuitBreaker` config (e.g., reduce `failureRatio` from `50%` to `70%`).

---

### **Example 3: Fallback Not Invoked When Expected**
**Issue:** A service should fallback to a cache but fails silently.

**Steps:**
1. **Query Fallback Metrics:**
   ```promql
   resilience_fallback_invoked_total{service="auth-service", expectation="cache_fallback"} == 0
   ```
   *Expected:* Zero invocations may indicate misconfiguration.

2. **Check Traces for Fallback Logic:**
   ```sql
   SELECT
     span.name,
     resilience.pattern,
     resilience.fallback
   FROM traces
   WHERE resilience.pattern = "fallback"
     AND resilience.fallback_used = false
   LIMIT 10;
   ```
   *Expected:* Verify if the fallback condition (e.g., `status_code=500`) was met.

3. **Validate Logs:**
   Filter for `resilience.pattern="fallback"` and `fallback_used=false`.

---

## **Related Patterns**
Resilience debugging often intersects with these patterns. Refer to their documentation for deeper context:

| **Pattern**               | **Purpose**                                                                                     | **Debugging Tip**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **[Retry]**                | Automatically retry failed requests.                                                             | Check for infinite loops (e.g., retrying a transient failure that’s now permanent). |
| **[Circuit Breaker]**      | Prevent cascading failures by isolating unstable services.                                        | Monitor `open` state duration; adjust thresholds based on SLA.                     |
| **[Bulkhead]**             | Isolate components to prevent resource exhaustion.                                                | Check thread pool exhaustion in logs.                                               |
| **[Fallback]**             | Provide degraded functionality when primary service fails.                                        | Verify fallback is triggered under expected failure scenarios.                      |
| **[Rate Limiting]**        | Control resource consumption.                                                                   | Debug throttling by checking `resilience_throttled_requests_total`.               |
| **[Bulkhead Isolation]**   | Separate components to contain failures (e.g., per-thread pools).                             | Use traces to identify which bulkhead thread pool was exhausted.                   |

---

## **Tools and Libraries**
| **Tool**                  | **Purpose**                                                                                     | **Use Case**                                  |
|---------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **OpenTelemetry**         | Standardized observability (traces, logs, metrics).                                               | Query resilience-specific spans.               |
| **Prometheus + Grafana**  | Monitoring and alerting on resilience metrics.                                                   | Dashboards for retry counts or circuit states. |
| **ELK Stack**             | Log aggregation and analysis.                                                                      | Correlate logs with resilience events.         |
| **Jaeger**                | Distributed tracing for resilience debugging.                                                     | Trace retry/fallback flows across services.   |
| **Resilience4j**          | Java library for resilience patterns (Retry, Circuit Breaker).                                     | Validate policy configurations.               |

---

## **Best Practices**
1. **Instrument Resilience Components Early**
   Add schema fields (e.g., `resilience.pattern`) to traces/logs during development.

2. **Set Up Alerts for Anomalies**
   Example Prometheus alerts:
   ```yaml
   alert: HighRetryRate
     expr: rate(resilience_retries_total{service="X"}[5m]) > 100
     for: 5m
     labels:
       severity: warning
   ```

3. **Use Canary Analysis**
   Test resilience changes in staging with **10% traffic** before full rollout.

4. **Document Assumptions**
   Note why a retry limit is set to `3` or a fallback is disabled (e.g., "Primary is SLAs").

5. **Regularly Review Policies**
   Update thresholds (e.g., circuit breaker) based on **P99 latency** or failure rates.

---
**See Also:**
- [Resilience Patterns Thresholds Guide](link)
- [OpenTelemetry Resilience Attributes](link)
- [Circuit Breaker Anti-Patterns](link)