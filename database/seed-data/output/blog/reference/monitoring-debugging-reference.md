# **[Pattern] Monitoring & Debugging Reference Guide**

---

## **Overview**
The **Monitoring & Debugging** pattern ensures observability and rapid issue resolution in distributed systems by capturing runtime metrics, logs, traces, and contextual data. This pattern provides structured ways to:
- **Monitor system health** via real-time metrics (CPU, memory, latency, error rates).
- **Debug issues** with structured logs, distributed tracing, and correlation IDs.
- **Alert on anomalies** (e.g., spikes in failure rates, degraded performance).
- **Analyze telemetry** retrospectively for root-cause analysis.

Successful implementation reduces **mean time to detect (MTTD)** and **mean time to resolve (MTTR)** by automating data collection and exposing actionable insights. This guide covers key components, schema references, and implementation best practices.

---

## **Implementation Details**

### **1. Core Components**
The pattern combines **four foundational dimensions** of observability:

| **Component**       | **Purpose**                                                                 | **Example Data Points**                          |
|----------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Metrics**          | Quantitative measurement of system behavior (e.g., performance, availability). | Requests/sec, error rates, p99 latency, GC pauses |
| **Logs**             | Qualitative records of application events (e.g., errors, user actions).      | `{timestamp, level: ERROR, message: "DB timeout"}` |
| **Traces**           | End-to-end request flow across services (distributed tracing).               | Service calls, timing, dependencies               |
| **Contextual Data**  | Additional metadata (e.g., user IDs, request IDs) for correlation.          | `{user_id: 123, correlation_id: abc123}`         |

### **2. Data Collection Strategies**
Capture data at **strategic points** in the system lifecycle:

| **Stage**           | **Data to Capture**                     | **Tools/Techniques**                          |
|---------------------|-----------------------------------------|-----------------------------------------------|
| **Request Handling** | Latency, error flags, context           | Instrumentation (e.g., OpenTelemetry)        |
| **Business Logic**  | Custom events (e.g., "Payment failed")  | Structured logging (JSON, Protobuf)          |
| **Infrastructure**  | Host metrics (CPU, disk I/O)            | Prometheus, CloudWatch                        |
| **User Sessions**   | Session IDs, application errors         | Frontend telemetry (e.g., Sentry)             |

### **3. Storage & Retention**
| **Component**  | **Storage Layer**       | **Retention Policy**                     | **Use Case**                          |
|----------------|--------------------------|-------------------------------------------|---------------------------------------|
| **Metrics**    | Time-series DB (e.g., Prometheus) | 1–30 days (compressed)                   | Real-time dashboards, alerts          |
| **Logs**       | Log aggregator (e.g., ELK, Loki)  | 30–365 days (depends on compliance)      | Debugging, auditing                   |
| **Traces**     | Trace DB (e.g., Jaeger, Zipkin)    | 30–90 days                                | Distributed debugging                |

---

## **Schema Reference**

### **1. Metric Schema**
| Field         | Type       | Description                                                                 | Example Value          |
|---------------|------------|-----------------------------------------------------------------------------|------------------------|
| `name`        | `string`   | Identifies the metric (e.g., `http_requests_total`).                       | `api.v1.get.status_code` |
| `value`       | `float`    | Numeric value (e.g., counter, gauge).                                     | `150.2`                 |
| `labels`      | `map`      | Key-value pairs for granular filtering (e.g., `service=payment`).          | `{service: "payment", code: "200"}` |
| `timestamp`   | `timestamp`| When the metric was recorded.                                               | `2023-10-01T12:00:00Z` |
| `unit`        | `string`   | Measurement unit (e.g., `seconds`, `requests`).                            | `seconds`               |

**Example Payload:**
```json
{
  "name": "http_request_duration_seconds",
  "value": 0.456,
  "labels": {"route": "/checkout", "status": "200"},
  "timestamp": "2023-10-01T12:00:00Z",
  "unit": "seconds"
}
```

---

### **2. Log Schema**
| Field          | Type       | Description                                                                 | Example Value                     |
|----------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `timestamp`    | `timestamp`| When the log entry was generated.                                           | `2023-10-01T12:00:00.123Z`       |
| `level`        | `string`   | Severity (e.g., `ERROR`, `WARN`, `INFO`).                                  | `ERROR`                           |
| `message`      | `string`   | Human-readable event description.                                           | `"Database connection timeout"`   |
| `context`      | `map`      | Structured metadata (e.g., `user_id`, `correlation_id`).                   | `{user_id: "user123", trace_id: "abc"}` |
| `trace_id`     | `string`   | Links to distributed trace (if available).                                | `abc123-xyz456`                   |

**Example Payload:**
```json
{
  "timestamp": "2023-10-01T12:00:00.123Z",
  "level": "ERROR",
  "message": "Failed to connect to DB",
  "context": {"user_id": "user123", "service": "payment"},
  "trace_id": "abc123-xyz456"
}
```

---

### **3. Trace Schema (OpenTelemetry)**
| Field          | Type       | Description                                                                 | Example Value                     |
|----------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `trace_id`     | `string`   | Unique identifier for the trace.                                            | `abc123-xyz456`                   |
| `span_id`      | `string`   | Identifies an individual operation within the trace.                        | `def789-ghi012`                   |
| `name`         | `string`   | Operation name (e.g., `DB.Query`, `Auth.Check`).                           | `DB.Query`                        |
| `start_time`   | `timestamp`| When the span began.                                                        | `2023-10-01T12:00:00.000Z`       |
| `end_time`     | `timestamp`| When the span completed.                                                    | `2023-10-01T12:00:00.456Z`       |
| `attributes`   | `map`      | Key-value pairs (e.g., `db.table=orders`).                                | `{db.table: "orders", status: "200"}` |
| `links`        | `array`    | References to related spans/traces.                                         | `[{trace_id: "other-trace-id"}]`  |

**Example Payload:**
```json
{
  "trace_id": "abc123-xyz456",
  "span_id": "def789-ghi012",
  "name": "DB.Query",
  "start_time": "2023-10-01T12:00:00.000Z",
  "end_time": "2023-10-01T12:00:00.456Z",
  "attributes": {"db.table": "orders", "status": "200"}
}
```

---

## **Query Examples**

### **1. PromQL (Metrics)**
**Query:** Find the 99th percentile latency for `/api/checkout` over the last 5 minutes.
```promql
histogram_quantile(0.99, sum by (le, route) (rate(http_request_duration_seconds_bucket[5m])))
    where route = "/api/checkout"
```

**Query:** Alert if error rate exceeds 1% for the `payment` service.
```promql
rate(http_errors_total{service="payment"}[1m])
    / rate(http_requests_total{service="payment"}[1m])
    > 0.01
```

---

### **2. LogQL (Grafana/Loki)**
**Query:** Find all `ERROR` logs for `user123` in the last hour.
```logql
{level="ERROR", context.user_id="user123"}
| json
| line_format "{{.message}} ({{.context.service}})"
```

**Query:** Correlate logs with a specific trace ID.
```logql
{trace_id="abc123-xyz456"}
| json
| line_format "Log: {{.message}} in {{.context.service}}"
```

---

### **3. SpanQL (Jaeger/Zipkin)**
**Query:** Find all spans where `db.table=orders` and duration > 500ms.
```spql
SELECT * FROM Spans
WHERE db.table = "orders"
AND duration > 500ms
ORDER BY end_time DESC
LIMIT 100
```

**Query:** Trace the full request flow for a user session.
```spql
SELECT * FROM Traces
WHERE context.user_id = "user123"
ORDER BY start_time DESC
```

---

## **Related Patterns**

| **Related Pattern**          | **Description**                                                                 | **Synergy**                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Circuit Breaker**           | Limits cascading failures by halting calls to failing services.                | Use metrics to trigger circuit breakers (e.g., `error_rate > 5%`).         |
| **Retry with Backoff**        | Automatically retries failed requests with exponential delays.                 | Combine with traces to avoid retry storms in unstable services.            |
| **Idempotency Keys**          | Ensures duplicate requests are safely processed.                            | Log idempotency key failures for debugging.                                |
| **Rate Limiting**             | Controls request volume to prevent overload.                                | Monitor `429 Too Many Requests` metrics for enforcement.                    |
| **Saga Pattern**              | Manages distributed transactions via compensating actions.                   | Traces help debug saga failures across services.                           |

---

## **Best Practices**
1. **Standardize Context Propagation**
   - Use **correlation IDs** and **trace IDs** across services to link logs/traces.
2. **Avoid Log Spam**
   - Structured logging > raw logs; filter low-severity events (e.g., `DEBUG`).
3. **Retain Critical Data Long-Term**
   - Archive logs/traces for compliance (e.g., GDPR) in a separate cold storage.
4. **Instrument Early**
   - Add monitoring hooks during development, not as an afterthought.
5. **Visualize Key Metrics**
   - Dashboards for:
     - Service-level SLIs (e.g., `p99 < 500ms`).
     - Error budgets (e.g., `allow 0.1% errors/day`).
6. **Automate Alerts**
   - Set up alerts for:
     - Spikes in latency (`http_request_duration_seconds > 2s`).
     - High error rates (`errors_total` increasing).

---
## **Tools & Ecosystem**
| **Category**       | **Tools**                                                                 |
|--------------------|---------------------------------------------------------------------------|
| **Metrics**        | Prometheus, Datadog, Cloud Monitoring, Grafana                          |
| **Logs**           | ELK Stack, Loki, Splunk, Sumologic                                       |
| **Traces**         | Jaeger, Zipkin, OpenTelemetry, Datadog Trace                              |
| **APM**            | New Relic, Dynatrace, AppDynamics                                        |
| **Open Standards** | OpenTelemetry, W3C Trace Context, OpenTelemetry Protocol (OTLP)          |
| **Alerting**       | PagerDuty, Opsgenie, Alertmanager (Prometheus)                           |

---
**Note:** For production use, refer to vendor-specific documentation (e.g., [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)) and compliance guidelines (e.g., HIPAA, GDPR).