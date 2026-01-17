---
**[Pattern] Resilience Observability: Reference Guide**
*Version [X.Y.Z]* | *Last Updated: [MM/YYYY]*

---

### **1. Overview**
Resilience Observability is a systematic approach to **monitoring the health, behavior, and failure modes of resilient systems** (e.g., microservices, distributed apps, or cloud-native architectures). It focuses on:
- **Real-time insights** into system resilience (e.g., retries, circuit breakers, rate limiting).
- **Proactive issue detection** (e.g., latency spikes, error cascades).
- **Root-cause analysis** for failures tied to resilience mechanisms (e.g., throttling, fallback strategies).

Unlike traditional observability (metrics, logs, traces), Resilience Observability explicitly tracks **how systems recover from disruptions**, enabling data-driven resilience tuning. Key stakeholders include **DevOps, SREs, and platform engineers**.

---
## **2. Key Concepts & Schema Reference**

| **Term**               | **Definition**                                                                 | **Example Attributes**                                                                 |
|------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Resilience Metrics** | Quantifiable signals of system resilience (e.g., retry attempts, failure rates). | `retry_count`, `circuit_breaker_state`, `fallback_latency`                           |
| **Resilience Events**  | Time-stamped incidents tied to resilience behaviors (e.g., circuit trip).     | `event_type: "circuit_trip"`, `timestamp`, `affected_service`                       |
| **Resilience Traces**  | Context-aware paths of resilience mechanisms (e.g., retry chains).          | `span_id`, `parent_span_id`, `resilience_action: "throttle"`                         |
| **Resilience Thresholds** | Configurable rules for alerting (e.g., "warn if retry failures exceed 5%"). | `threshold: "error_rate > 0.05"`, `severity: "warning"`                              |
| **Resilience Debug Context** | Additional metadata (e.g., environment, config version) for tracing issues.   | `env: "prod"`, `resilience_config_version: "v1.2"`                                  |

---

### **2.1 Implementation Details**
#### **Pillars of Resilience Observability**
1. **Metrics**:
   - Track resilience-specific KPIs (e.g., `retry_success_rate`, `circuit_breaker_open_duration`).
   - Use **distribution histograms** (e.g., latency percentiles) to analyze resilience actions.
   - *Tools*: Prometheus (`resilience_*` metrics), OpenTelemetry.

2. **Logs**:
   - Enrich logs with resilience events (e.g., `{"resilience_action": "retry", "attempt": 3}`).
   - Example log format:
     ```json
     {
       "service": "payment-service",
       "level": "WARN",
       "message": "Retry #3 failed for order_id=123",
       "resilience": {
         "type": "retry",
         "max_attempts": 5,
         "backoff": "exponential"
       }
     }
     ```

3. **Traces**:
   - Instrument resilience actions as **trace spans** (e.g., `resilience.retry`, `resilience.circuit_break`).
   - Use **context propagation** (e.g., W3C Trace Context) to correlate spans across services.
   - *Tools*: Jaeger, Zipkin, OpenTelemetry Trace API.

4. **Alerts & Dashboards**:
   - Define **resilience-specific alerts** (e.g., "Circuit breaker open > 10 mins").
   - Visualize:
     - Resilience action frequencies (bar charts).
     - Failure rate trends over time (line graphs).
   - *Tools*: Grafana (with Prometheus/PromQL), Datadog.

5. **Configuration & Context**:
   - Store resilience configs (e.g., `retry.max_attempts`) in **observability metadata**.
   - Example (OpenTelemetry):
     ```python
     resource = Resource(
       attributes={
         "resilience.config": '{"retry": {"max_attempts": 3}}'
       }
     )
     ```

---
## **3. Query Examples**
### **3.1 Metrics Queries (PromQL)**
| **Use Case**                          | **Query**                                                                                     | **Tool**          |
|---------------------------------------|---------------------------------------------------------------------------------------------|-------------------|
| Retry failures (%) per service        | `rate(resilience_retry_failures_total[5m]) / rate(resilience_retry_attempts_total[5m])`    | Prometheus        |
| Circuit breaker open duration         | `histogram_quantile(0.95, sum(rate(resilience_circuit_breaker_open_seconds_bucket[5m])) by (le))` | Prometheus        |
| Fallback latency (p99)                | `histogram_quantile(0.99, rate(resilience_fallback_latency_seconds_bucket[5m]))`           | Prometheus        |
| Throttling rate by endpoint           | `sum(rate(resilience_throttle_drops_total[5m])) by (endpoint)`                                | Prometheus        |

### **3.2 Logs Queries (Loki/Grafana)**
| **Query**                          | **Filter Example (Loki)**                                                                 |
|------------------------------------|-------------------------------------------------------------------------------------------|
| Retry failures > 3 attempts        | `service="payment-service" AND "resilience_action"="retry" AND "attempt" > 3`             |
| Circuit breaker trips in last hour | `level="ERROR" AND "resilience_action"="circuit_trip" AND @timestamp > now()-1h`          |
| Fallback usage by service          | `resilience_action="fallback" BY service`                                                 |

### **3.3 Trace Analysis (Jaeger)**
1. **Find resilience-related spans**:
   - Filter: `operation_name =~ "resilience.*"` (e.g., `resilience.retry`, `resilience.circuit_break`).
2. **Analyze retry chains**:
   - Use **trace dependencies** to visualize retry loops across services.
3. **Correlate with errors**:
   - Search for traces where `error=true` AND `resilience_action` exists.

---
## **4. Implementation Steps**
### **4.1 Instrumentation**
1. **Metrics**:
   - Expose Prometheus metrics (e.g., `resilience_retry_failures_total{service="x"}`).
   - Use OpenTelemetry’s `MetricsExporter` for cloud-native setups.
2. **Logs**:
   - Structured logging with resilience metadata (see **2.1 Logs**).
   - Tools: JSON logs (ELK Stack), OpenTelemetry Logs.
3. **Traces**:
   - Add spans for resilience actions:
     ```java
     // Example: Java (Micrometer + OpenTelemetry)
     tracer.spanBuilder("resilience.retry")
           .setAttribute("attempt", retryCount)
           .startSpan()
           .use((s) -> { /* retry logic */ });
     ```

### **4.2 Alerting Rules**
Example (Prometheus Alertmanager):
```yaml
groups:
- name: resilience-alerts
  rules:
  - alert: HighRetryFailureRate
    expr: rate(resilience_retry_failures_total[5m]) > 0.1 * rate(resilience_retry_attempts_total[5m])
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High retry failure rate in {{ $labels.service }}"
```

### **4.3 Dashboards**
**Recommended Grafana Panels**:
1. **Resilience Action Over Time**:
   - Bar chart: `resilience_action` vs. time (group by `type`).
2. **Failure Rate by Service**:
   - Stacked area chart: `sum(rate(resilience_failures[5m])) by service`.
3. **Circuit Breaker Health**:
   - Gauge: `resilience_circuit_breaker_state{state="open"}`.

---
## **5. Schema Reference (Machine Format)**
### **5.1 Metrics Schema (Prometheus)**
```plaintext
# Retry metrics
resilience_retry_attempts_total{service="x", endpoint="y"}   counter
resilience_retry_failures_total{service="x", endpoint="y"}  counter
resilience_retry_latency_seconds{service="x", endpoint="y"} histogram

# Circuit breaker metrics
resilience_circuit_breaker_open_seconds_bucket{...}          histogram
resilience_circuit_breaker_state{service="x", state="open"} gauge
```

### **5.2 Log Schema (Structured)**
```json
{
  "timestamp": "2023-10-01T12:00:00Z",
  "service": "order-service",
  "level": "INFO"|"WARN"|"ERROR",
  "resilience": {
    "action": "retry"|"circuit_break"|"throttle"|"fallback",
    "attempt": 1, // For retries
    "config": { "max_attempts": 3, "backoff_ms": 100 }
  },
  "context": {
    "request_id": "abc123",
    "env": "prod"
  }
}
```

### **5.3 Trace Schema (OpenTelemetry)**
```yaml
# Span attributes for resilience actions
attributes:
  resilience.action: retry|circuit_break|...
  resilience.attempt: 1
  resilience.config: '{"max_attempts": 3, ...}'
```

---
## **6. Query Examples (CLI)**
### **6.1 Prometheus**
```bash
# Retry success rate per service
curl http://prometheus:9090/api/v1/query?query=sum(rate(resilience_retry_successes_total[5m]))+by+(service)
```

### **6.2 Loki (Logs)**
```bash
# Find services with >5 retries
loki query='service="*" AND "resilience_action"="retry" AND "attempt" > 5'
```

### **6.3 Jaeger (Traces)**
```bash
# List traces with circuit breaker spans
jaeger query traces \
  --lookup.field=operation_name \
  --lookup.value="resilience.circuit_break" \
  --limit=10
```

---
## **7. Related Patterns**
| **Pattern**               | **Description**                                                                 | **Observability Synergy**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Prevents cascading failures by temporarily stopping requests to a failing service. | Track `circuit_breaker_state` and `open_duration` in observability.                     |
| **Retry with Backoff**    | Automatically retries failed requests with exponential backoff.                | Monitor `retry_attempts` and `retry_latency` to tune strategies.                           |
| **Bulkheading**           | Isolates failures by limiting concurrent executions.                          | Observe `concurrency_limits` and `throttle_drops` in metrics.                             |
| **Fallback**              | Provides degraded functionality when primary service fails.                   | Compare `fallback_latency` with `primary_latency` to assess impact.                      |
| **Rate Limiting**         | Controls request volume to prevent overload.                                  | Use `throttle_drops` to correlate with error spikes.                                     |
| **Chaos Engineering**     | Proactively tests resilience by injecting failures.                         | Measure `resilience_event_counts` to validate failure recovery.                           |

---
## **8. Best Practices**
1. **Instrument Early**:
   - Add resilience observability **before** deploying resilience mechanisms.
2. **Correlate Context**:
   - Link resilience events to **request IDs**, **user sessions**, or **transactions**.
3. **Set Resilience-Specific Thresholds**:
   - Example: Alert if `retry_failure_rate > 10%` for 15 minutes.
4. **Avoid Overhead**:
   - Sample traces/logs for high-volume resilience actions (e.g., retries).
5. **Document Configs**:
   - Tag resilience policies with **version** and **intent** (e.g., `resilience_config_version="v1.0"`).
6. **Test Observability**:
   - Simulate failures (e.g., `kill -9` a service) and verify observability captures resilience actions.

---
## **9. Tools & Libraries**
| **Category**          | **Tools/Libraries**                                                                 |
|-----------------------|------------------------------------------------------------------------------------|
| **Metrics**           | Prometheus, OpenTelemetry Collector, Datadog, New Relic                             |
| **Logs**              | Loki, ELK Stack (Elasticsearch/Logstash/Kibana), OpenTelemetry Logs               |
| **Traces**            | Jaeger, Zipkin, OpenTelemetry Trace API, AWS X-Ray                                 |
| **Alerting**          | Alertmanager, PagerDuty, Opsgenie, Grafana Alerting                                 |
| **Instrumentation**   | OpenTelemetry SDKs (Java, Python, Go, etc.), Micrometer, Hystrix Metrics            |

---
## **10. Example Workflow**
**Scenario**: Payment service fails intermittently due to downstream service `account-api`.

1. **Observability Setup**:
   - Instrument `payment-service` to track `resilience_retry_attempts` and `resilience_circuit_breaker_state`.
   - Add spans for retries: `resilience.retry` (with `attempt=3`).

2. **Detection**:
   - PromQL alert fires:
     ```promql
     rate(resilience_retry_failures_total[5m]) > 0.2 * rate(resilience_retry_attempts_total[5m])
     ```
   - Jaeger trace shows **5 retry attempts** for a single request to `account-api`.

3. **Root Cause**:
   - Loki logs reveal:
     ```json
     { "level": "ERROR", "resilience_action": "retry", "attempt": 5, "target": "account-api" }
     ```
   - Circuit breaker is **open for 20 mins**.

4. **Resolution**:
   - Adjust `account-api` retry timeout (observed via `resilience_retry_latency_p99`).
   - Add fallback to `legacy-payment-gateway` and monitor `fallback_latency`.

---
## **11. References**
- **[Resilience Patterns (Microsoft)](https://resiliencepatterns.com/)**
- [OpenTelemetry Resilience Documentation](https://opentelemetry.io/docs/specs/otlp/)
- [Prometheus Documentation](https://prometheus.io/docs/prometheus/latest/querying/promql/)
- [Chaos Engineering (Gremlin)](https://www.gremlin.com/)