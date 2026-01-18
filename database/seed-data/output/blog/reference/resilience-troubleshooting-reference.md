---
# **[Resilience Troubleshooting] Reference Guide**

---

## **Overview**
This guide provides a structured approach to diagnosing and resolving resilience failures in distributed systems, particularly those using **retries, circuit breakers, bulkheads, fallbacks, and timeouts**. Resilience patterns often introduce complexity, and failures may manifest indirectly (e.g., degraded performance, cascading failures, or silent errors). This guide categorizes troubleshooting techniques by pattern, outlines key failure modes, and provides tools (logging, metrics, and tracing) to isolate root causes. Best practices for simulating resilience errors and validating fixes are also included.

---

## **Schema Reference**
Use the following schema to document resilience-related metrics, logs, and traces for troubleshooting.

| **Category**       | **Metric/Field**               | **Description**                                                                                     | **Severe Threshold**                                                                                     | **Tools**                                                                                     |
|--------------------|--------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Retries**        | `retryAttempts`                | Total retries for a given operation (counter)                                                      | `> 5 * defaultRetries` (adjust based on SLA)                                                          | APM tools (e.g., New Relic, Datadog), custom logging                                         |
|                    | `retryFailures`                | Retries that resulted in failures (counter)                                                         | `retryFailures / retryAttempts > 50%`                                                              |                                                                                               |
|                    | `retryBackoff`                 | Time between retry attempts (histogram)                                                              | Backoff > `2 * timeout` (risk of starvation)                                                          | OpenTelemetry, custom instrumentation                                                        |
| **Circuit Breaker**| `stateChanges`                 | Transitions between `Closed`, `Open`, and `Half-Open` states (counter)                               | Rapid state changes (e.g., 5 `Open` → `Closed` cycles/min)                                           | Hystrix Metrics, Resilience4j monitoring                                                        |
|                    | `errorThreshold`               | Invocation failures required to trip the circuit (metric)                                           | Exceeded threshold (e.g., `5 failures / 10s`)                                                       | Circuit breaker library dashboards                                                            |
|                    | `resetTimeout`                 | Time until circuit resets to `Half-Open` (histogram)                                               | Reset too aggressively (e.g., `5s` when SLO requires `1m`)                                           |                                                                                               |
| **Bulkheads**      | `concurrencyUsage`             | Concurrent requests blocked due to thread pool exhaustion (counter)                                  | `concurrencyUsage > 80% * maxThreads`                                                              | Resilience4j dashboards, custom metrics                                                       |
|                    | `queueWaitTime`                | Time spent waiting in bulkhead queue (histogram)                                                    | Median `> 500ms` (latency degradation)                                                               | APM tools                                                                                       |
| **Fallbacks**      | `fallbackExecutions`           | Fallback invoked (counter)                                                                          | `> 10%` of total invocations (indicates pattern misconfiguration)                                      | Custom logs, distributed tracing                                                               |
|                    | `fallbackLatency`              | Time taken by fallback (histogram)                                                                   | Median `> 2 * timeout` (fallback too slow)                                                          | OpenTelemetry, APM tools                                                                       |
| **Timeouts**       | `timeoutOccurrences`           | Operations failing due to timeout (counter)                                                         | `> 5%` of total invocations                                                                          | APM tools, CloudWatch                                                                      |
|                    | `timeoutValue`                 | Configured timeout duration (metric)                                                              | Too short (e.g., `1s` for external API with `100ms` variance)                                      | Configuration management logs, Resilience4j metrics                                           |
| **General**        | `resilienceErrorCode`          | Custom error code for resilience failures (e.g., `RESILIENCY_RETRY_EXHAUSTED`)                      | Monitored via structured logging                                                                   | ELK Stack, Datadog                                                                              |
|                    | `resilienceTraceId`            | Correlates resilience events across services (string)                                                | Required for distributed tracing                                                                   | OpenTelemetry, Jaeger                                                                         |

---

## **Query Examples**
Use these queries to diagnose resilience issues in your monitoring stack.

---

### **1. Retry Troubleshooting**
#### **Query: Retry Failures by Endpoint**
**Tool:** PromQL (Prometheus) / KQL (Azure Monitor)
```sql
# Metric: retry_failures total
sum(rate(retry_failures_total[5m])) by (endpoint)
  > sum(rate(successful_requests_total[5m])) by (endpoint) * 0.5
```
**Interpretation:** Endpoints where retry failures exceed 50% of successful requests.

#### **Query: Longest Retry Backoff**
**Tool:** Grafana (Histograms)
```sql
# Metric: retry_backoff_seconds_bucket{le="10"}
sum(rate(retry_backoff_seconds_bucket{le="10"}[5m])) / sum(rate(retry_attempts_total[5m]))
```
**Threshold:** Backoff > `2 * timeout` (e.g., `backoff=30s` when `timeout=10s`).

---

### **2. Circuit Breaker Analysis**
#### **Query: Circuit Breaker State Transitions**
**Tool:** Resilience4j Dashboard / Grafana
```sql
# Metric: circuit_breaker_state.count
increase(circuit_breaker_state_count{state="OPEN"}[1m])
  > 3  # 3 state changes in 1 minute (adjust threshold)
```
**Interpretation:** Rapid toggling indicates flapping; investigate root cause (e.g., upstream API instability).

#### **Query: Failed Requests Before Reset**
**Tool:** PromQL
```sql
# Metric: circuit_breaker_failures_before_trip
histogram_quantile(0.99, rate(circuit_breaker_failures_before_trip[5m]))
```
**Threshold:** 99th percentile > configured `failureThreshold` (e.g., `5` failures).

---

### **3. Bulkhead Congestion**
#### **Query: Queue Wait Time Percentiles**
**Tool:** Datadog / Elasticsearch
```sql
# Metric: bulkhead_queue_wait_ms
histogram_quantile(0.95, bulkhead_queue_wait_ms{service="user-service"}) > 500
```
**Interpretation:** P95 > `500ms` indicates latency spikes due to bulkhead contention.

#### **Query: Rejected Requests**
**Tool:** KQL
```sql
requests
| where operationName == "processOrder"
| where isempty(correlationId)  // Fallback/bulkhead rejection
| summarize count() by bin(timestamp, 1m)
```
**Threshold:** > `10%` of total requests rejected.

---

### **4. Fallback Issues**
#### **Query: Fallback Execution Rate**
**Tool:** ELK Stack
```sql
# Log query: "fallback: invoked"
logs
| filter message: "fallback: invoked"
| count by @timestamp, endpoint
| where count > (total_requests * 0.1)
```
**Interpretation:** Fallback invoked >10% of time → consider revisiting fallback logic.

#### **Query: Fallback Latency Spikes**
**Tool:** OpenTelemetry
```sql
# Span query: fallback_latency > 2s
tracespan
| where resource.service.name == "user-service"
| where operation.name == "fallbackHandler"
| where duration > 2000ms
| summarize count() by bin(timestamp, 1h)
```
**Threshold:** > `5` spans/hour (indicates fallback degradation).

---

### **5. Timeout Failures**
#### **Query: Timeout by Endpoint**
**Tool:** CloudWatch
```sql
# Metric: timeout_occurrences
metrics
| where metricName == "timeout_occurrences"
| summarize count() by endpoint, bin(timestamp, 5m)
| where count > 0
```
**Interpretation:** Investigate endpoints with `>5%` timeouts (adjust threshold based on SLA).

#### **Query: Timeout Value Distribution**
**Tool:** Prometheus
```sql
# Metric: timeout_config
histogram_quantile(0.5, timeout_config_seconds_bucket)
```
**Threshold:** P50 < `2 * expected_operation_time` (e.g., `timeout=100ms` for `50ms` API).

---

## **Step-by-Step Troubleshooting Workflow**
Follow this flow to diagnose resilience failures:

1. **Identify the Pattern Affected**
   - Check logs/metrics for `retryFailures`, `circuit_breaker_state`, or `fallback_executions`.

2. **Reproduce the Failure**
   - **Retries:** Use a load tester (e.g., k6) to simulate upstream failures.
   - **Circuit Breaker:** Force failures (e.g., `POST /api/unsafe`).
   - **Bulkhead:** Spam the system with concurrent requests.

3. **Validate Fixes**
   - **Retry:** Verify `retryAttempts` decreases after fixing upstream issues.
   - **Circuit Breaker:** Ensure `resetTimeout` aligns with SLO recovery time.
   - **Fallback:** Test fallback paths in staging with `timeout=0`.

4. **Monitor Post-Fix**
   - Set alerts for:
     - `retryFailures > 3 * historical_avg`.
     - `circuit_breaker_state` toggling > `1/min`.
     - `fallbackLatency` > `2 * timeout`.

---

## **Related Patterns**
| **Pattern**            | **Description**                                                                 | **Troubleshooting Overlap**                                                                 |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Retry**              | Exponentially back off on transient failures.                                | Shared metrics: `retryAttempts`, `retryBackoff`.                                            |
| **Circuit Breaker**    | Prevents cascading failures by stopping calls to failing services.             | Shared: `errorThreshold`, `stateChanges`.                                                   |
| **Bulkhead**           | Isolates resource exhaustion (e.g., thread pools).                           | Shared: `concurrencyUsage`, `queueWaitTime`.                                              |
| **Fallback**           | Provides degraded functionality when primary fails.                          | Shared: `fallbackExecutions`, `fallbackLatency`.                                            |
| **Timeout**            | Aborts long-running operations.                                               | Shared: `timeoutOccurrences`, `timeoutValue`.                                               |
| **Bulkhead with Timeout** | Combines bulkhead and timeout for strict SLA enforcement.                  | Use `concurrencyUsage` + `timeoutOccurrences` queries.                                     |
| **Resilience Testing** | Proactively simulates failures to validate resilience patterns.              | Use in Step 2 above to reproduce issues.                                                    |

---

## **Tools & Libraries**
| **Tool/Library**       | **Purpose**                                                                 | **Key Metrics/Logs**                                                                 |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Resilience4j**       | Java library for circuit breakers, retries, etc.                           | `CircuitBreakerMetrics`, `RetryMetrics`.                                              |
| **Hystrix**            | Legacy Netflix library (circuit breakers, bulkheads).                     | Hystrix streaming metrics.                                                            |
| **OpenTelemetry**      | Distributed tracing for resilience events.                                  | Spans tagged with `resilience.error` or `resilience.retry`.                            |
| **Prometheus + Grafana** | Monitoring for resilience metrics.                                         | Custom counters (e.g., `retry_failures_total`).                                       |
| **k6**                 | Load testing to simulate resilience failures.                               | Simulate `retryExhausted` or `circuitOpen` scenarios.                                  |

---

## **Common Pitfalls & Fixes**
| **Pitfall**                          | **Root Cause**                                      | **Solution**                                                                       |
|--------------------------------------|----------------------------------------------------|------------------------------------------------------------------------------------|
| Retry loop starvation                | Backoff too long relative to timeout.               | Set `backoffFactor <= 2 * timeout`.                                                 |
| Circuit breaker thrashing            | `resetTimeout` too short.                          | Align with SLO recovery time (e.g., `1m` if SLO is `1h`).                           |
| Bulkhead queue flooding              | `maxThreads` too low.                              | Scale `maxThreads` based on P99 load.                                               |
| Fallback too slow                    | Fallback implementation > `timeout`.                | Optimize fallback or increase `timeout`.                                            |
| Silent retries                       | No logging for retry exhaustions.                  | Add `INFO` log for `retryAttempts >= maxRetries`.                                   |

---
**Note:** Replace placeholder values (e.g., `5m`, `10%`) with your SLO-based thresholds.