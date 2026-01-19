---

# **[Tracing Patterns] Reference Guide**

---

## **Overview**
**Tracing Patterns** enable observability by capturing structured traces of system interactions, user actions, and operational events across distributed microservices, APIs, or monolithic applications. Traces are time-ordered sequences of spans (recorded operations) that help diagnose latency, dependency failures, and user flows. This guide defines key tracing patterns, their schema structure, implementation details, and example queries for observability platforms like OpenTelemetry, Jaeger, or Datadog.

---

## **Implementation Details**

### **1. Core Concepts**
- **Trace**: A logical unit of work (e.g., API request, database query) composed of hierarchically related spans.
- **Span**: A single operation (e.g., `HTTP Request`, `DB Query`) with metadata (start/end time, attributes, logs).
- **Trace ID**: Unique identifier for a trace; spans inherit this ID.
- **Span ID**: Unique identifier for a span; used to link child spans to their parent.

### **2. Common Tracing Patterns**
| **Pattern**          | **Purpose**                                                                 | **Use Case**                     |
|----------------------|------------------------------------------------------------------------------|----------------------------------|
| **Request-Response** | Trace a full request lifecycle (e.g., API → Service A → Service B).         | Microservices communication.     |
| **Sidecar Injection**| Inject tracing agents (e.g., OpenTelemetry Collector) alongside services.   | Sidecar proxy tracing.          |
| **Manual Instrumentation** | Explicitly add spans/logs to custom code (e.g., batch jobs, cron tasks).   | Legacy systems or non-HTTP flows.|
| **Automatic Instrumentation** | Use SDKs to auto-instrument libraries (e.g., HTTP clients, DB drivers).     | Reducing boilerplate.            |
| **Distributed Context Propagation** | Pass trace/span IDs between services via headers (e.g., `traceparent`).    | Cross-service correlation.       |

---

## **Schema Reference**

### **Trace Schema**
| Field          | Type    | Description                                                                                                                                 | Example Value                     |
|----------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| `traceId`      | UUID    | Unique identifier for the trace.                                                                                                             | `a1b2c3d4-5678-90ef-1234-56789abc`|
| `startTime`    | Timestamp| Creation time of the trace.                                                                                                                 | `2024-05-15T12:00:00Z`           |
| `spans`        | Array   | List of spans in the trace. Each span has:                                                                                                  | N/A                               |

### **Span Schema**
| Field          | Type    | Description                                                                                                                                 | Example Value                     |
|----------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| `spanId`       | UUID    | Unique identifier for the span.                                                                                                             | `f1e2d3c4-7890-12ab-3456-7890abc12`|
| `name`         | String  | Human-readable operation name (e.g., `GET /user`).                                                                                          | `GET /api/v1/users`              |
| `parentSpanId` | UUID    | Parent span ID (if child span).                                                                                                           | `e3d2c1b0-9876-54ab-2345-67890abc11`|
| `startTime`    | Timestamp| Start time of the span.                                                                                                                   | `2024-05-15T12:00:05Z`           |
| `endTime`      | Timestamp| End time of the span.                                                                                                                     | `2024-05-15T12:00:10Z`           |
| `duration`     | Duration| Span duration (calculated from start/end).                                                                                                 | `5ms`                             |
| `attributes`   | Key-Value| Metadata (e.g., `http.method=POST`, `db.table=users`).                                                                                   | `{"status": "200", "user_id": "123"}` |
| `logs`         | Array   | Structured logs (timestamped entries).                                                                                                        | `[{"message": "Query executed", "severity": "INFO"}]`|
| `links`        | Array   | References to other traces/spans (e.g., for dependency tracking).                                                                            | `[{"trace_id": "x1", "span_id": "y1"}]` |

---

## **Query Examples**

### **1. Filter Traces by Service Name**
**Objective**: Find all traces involving `auth-service` in the last hour.
```kql
// Azure Monitor Logs (KQL)
traces
| where TimeGenerated > ago(1h)
| where tolower(tags["serviceName"]) == "auth-service"
| project traceId, startTime, duration, attributes
```

**Equivalent in Jaeger CLI**:
```bash
jaeger query --start="1h ago" --service=auth-service
```

---

### **2. Latency Analysis for a User Flow**
**Objective**: Identify slow paths in the `checkout` flow (API → Payment → Shipping).
```sql
// Grafana Loki + MetricQL (simplified)
(
  sum by (service, span_name) (
    rate(
      {job="traces", span_name="checkout_api"}
        |> __error__() == 0
        |> duration() > 1000
    )
  )
)
where service in ["api-gateway", "payment-service"]
```

**OpenTelemetry Query**:
```sql
SELECT
  service_name,
  AVG(duration)
FROM traces
WHERE span_name = "checkout_api"
  AND service_name IN ("api-gateway", "payment-service")
GROUP BY service_name
ORDER BY AVG(duration) DESC
LIMIT 10;
```

---

### **3. Error Correlation**
**Objective**: Find all traces where a `5xx` error occurred in `payment-service`.
```python
# Python (using OpenTelemetry SDK)
def trace_error_handler(request):
    if request.status_code >= 500:
        current_span = open_telemetry.get_current_span()
        current_span.set_attribute("error.status", f"{request.status_code}")
        current_span.record_exception(exception=request.exception)
```

**Query in Datadog**:
```sql
// Datadog API Query
{
  "query": "traces WHERE @service:payment-service AND @status.code:>=500",
  "limit": 100
}
```

---

### **4. User Session Reconstruction**
**Objective**: Reconstruct a user session across multiple services (e.g., login → dashboard).
```sql
// OpenTelemetry Collector (custom pipeline)
stream: {
  traces: {
    receivers: [otlp],
    processors: [
      batch,
      resource,
      memory_limiter,
      # Custom processor to link spans by user_id
      {
        "span_processor": {
          "name": "user_context",
          "attributes": {
            "user_id": "${attributes.user_id}",  // Assume injected from auth service
            "user_session": "${span_name}"
          }
        }
      }
    ],
    exporters: [logging, prometheus]
  }
}
```

---

### **5. Dependency Heatmap**
**Objective**: Visualize latency bottlenecks between services.
```bash
# Jaeger CLI + custom metrics
jaeger query --start="24h ago" --services="*" --format=json | grep -E '"name":.*-"service' | jq '.[].spans[] | {parent: .parent_id, child: .id, duration: .duration}'
```

**Visualization Tip**:
Use Grafana’s **Trace Explorer** to plot dependency graphs with latency colors.

---

## **Requirements & Validation**
| Checklist Item                          | Validation Method                                                                 |
|-----------------------------------------|-----------------------------------------------------------------------------------|
| Trace IDs propagated across services    | Verify `traceparent` header in HTTP requests (e.g., `WITH=1-ffffffffffffffffffffffffffffffffffffffff;o=1`). |
| Span attributes include critical fields | Check for `http.method`, `http.url`, `db.statement`, `user_id`.                   |
| Error spans tagged with severity        | Ensure `error.type` and `status.code` are set for `5xx`/`4xx` responses.        |
| Sampling rate configured for cost       | Adjust `sampling_probability` (e.g., `0.1` for 10% traces) in OTel Collector.     |

---

## **Related Patterns**

### **1. Logging Patterns**
- **[Structured Logging](#)** – Align span attributes with log messages for correlation.
- **[Distributed Logging](#)** – Send logs to the same backend as traces (e.g., Loki + OpenTelemetry).

### **2. Metrics Patterns**
- **[Latency Percentiles](#)** – Use trace durations to compute `p99` response times.
- **[Error Rates](#)** – Correlate spans with `error=true` to metric error rates.

### **3. Monitoring Patterns**
- **[SLOs from Traces](#)** – Define SLOs (e.g., "99% of traces < 500ms") using trace data.
- **[Alerting on Traces](#)** – Trigger alerts when trace counts exceed thresholds (e.g., ">10 lost traces/hour").

### **4. Advanced Patterns**
- **[Trace Annotations](#)** – Add custom annotations (e.g., `business_event="checkout"`) for filtering.
- **[Trace Sampling Strategies](#)** – Use adaptive sampling (e.g., lower sampling for 404s).
- **[Egress Monitoring](#)** – Trace external API calls (e.g., `POST /stripe/charge`) with `peer.service`.

---

## **Tools & Libraries**
| Tool/Library               | Purpose                                                                           | Notes                                  |
|----------------------------|-----------------------------------------------------------------------------------|----------------------------------------|
| [OpenTelemetry SDK](https://opentelemetry.io/docs/) | Instrument apps in Java, Python, Go, etc.                                      | Supports auto-instrumentation.        |
| [Jaeger](https://www.jaegertracing.io/)          | Trace visualization and analysis.                                                | Self-hosted or managed (e.g., Datadog).|
| [Zipkin](https://zipkin.io/)                   | Lightweight trace collector/visualizer.                                         | Older but widely supported.           |
| [Datadog APM](https://www.datadoghq.com/apm)      | Unified APM with traces, metrics, and logs.                                     | Enterprise-grade.                      |
| [New Relic](https://newrelic.com/apm)            | APM with distributed tracing.                                                    | Strong UI for dependency mapping.      |
| [AWS X-Ray](https://aws.amazon.com/xray/)         | Native AWS tracing with Lambda integrations.                                    | Regional costs apply.                 |

---

## **Troubleshooting**
| Issue                          | Diagnosis                                                                 | Solution                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Missing trace IDs**           | Check `traceparent` header propagation.                                     | Ensure headers are copied in load balancers/proxies (e.g., Nginx).       |
| **High cardinality attributes**| Too many distinct `user_id` values in spans.                               | Sample attributes or use hash-based aggregation (e.g., `user_id_hash`).   |
| **Slow trace ingestion**        | Bottleneck in collector/export pipeline.                                    | Scale exporters (e.g., OTLP HTTP gRPC) or use batching.                  |
| **False positives in alerts**   | Alerts triggered by expected latencies (e.g., DB queries).                   | Add context to alerts (e.g., `exclude_spans: ["query.db"]`).             |
| **Cross-service latency hidden**| Parent-child span relationships unclear.                                     | Use `links` field to explicitly reference related traces/spans.          |

---
**References**:
- [OpenTelemetry Spec](https://github.com/open-telemetry/specification)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Grafana Trace Explorer](https://grafana.com/docs/grafana-cloud/trace/)