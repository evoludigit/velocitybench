# **[Pattern] Latency Conventions: Reference Guide**

---

## **Overview**
Latency Conventions define standardized practices for measuring, reporting, and interpreting latency-related metrics in distributed systems, microservices, or cloud-native architectures. This pattern ensures consistency in how latency is tracked across services, APIs, and infrastructure components, improving observability, debugging efficiency, and performance benchmarking.

Latency conventions address:
- **Unified metric definitions** (e.g., p50, p95, p99 percentiles).
- **Contextual latency breakdowns** (e.g., client → API → DB).
- **Standardized naming and instrumentation** (e.g., `latency_duration_microseconds`).
- **SLO (Service Level Objective) alignment** for latency thresholds.

Implementing these conventions reduces ambiguity in monitoring dashboards (e.g., Prometheus, Grafana) and alerts, enabling teams to compare latency trends across services objectively.

---

## **Schema Reference**
Use the following structured schema to define latency metrics. Adjust fields as needed for your environment.

| **Field**                     | **Description**                                                                 | **Example Value**                          | **Type**       | **Required** |
|-------------------------------|---------------------------------------------------------------------------------|--------------------------------------------|----------------|--------------|
| **metric_name**               | Name of the latency metric (follows OpenTelemetry conventions).                  | `api.request.duration`                     | String         | ✅           |
| **unit**                      | Time unit for the metric.                                                        | `microseconds`                              | Enum           | ✅           |
| **percentile**                | Percentile of interest (e.g., p50, p99).                                        | `95`                                       | Integer/Float  | ✅           |
| **context_labels**            | Tags to classify latency (e.g., `service_name`, `region`).                       | `{service: "user-service", region: "us-west"}` | JSON           | ❌           |
| **components**                | Breakdown of latency phases (e.g., `client`, `api_processing`, `db_query`).     | `["client", "api", "db"]`                  | Array          | ✅           |
| **is_slo**                    | Boolean flag if this metric is tied to an SLO (e.g., `latency_slo.missed`).      | `true`                                     | Boolean        | ❌           |
| **description**               | Human-readable explanation of the metric's purpose.                               | "API request latency (p95)."               | String         | ❌           |
| **dimensions**                | Additional context (e.g., `http_method`, `user_type`).                           | `{method: "GET", user_type: "premium"}`    | JSON           | ❌           |

Example Latency Metric Definition:
```json
{
  "name": "api.request.duration",
  "unit": "microseconds",
  "percentile": 95,
  "context_labels": {"service": "order-service", "env": "prod"},
  "components": ["client", "api", "db"],
  "description": "Latency of order processing API (p95)."
}
```

---

## **Implementation Details**

### **1. Key Concepts**
#### **Latency Components**
Breakdown latency into logical phases to isolate bottlenecks:
| **Component**      | **Description**                                                                 | **Example Metric**                     |
|--------------------|---------------------------------------------------------------------------------|----------------------------------------|
| **Client**         | Time to send/receive HTTP requests or gRPC calls.                                 | `client_connect_duration`             |
| **Network**        | Time for data to traverse network layers (e.g., VPN, CDN).                      | `network_transit_time`                |
| **API Processing** | Time spent in your application layer (e.g., middleware, business logic).        | `api_processing_time`                 |
| **Database**       | Time for DB queries (including retries).                                          | `db_query_latency`                     |
| **External API**   | Latency of calls to third-party services.                                        | `external_call.duration`               |
| **End-to-End**     | Total latency from client request to server response.                             | `end_to_end_latency`                   |

#### **Percentiles**
Use percentiles to capture latency distributions:
- **p50 (Median)**: 50% of requests completed within this time.
- **p95**: 95% of requests completed; useful for identifying slow outliers.
- **p99**: Critical for detecting extreme latency spikes (e.g., 1% of requests).

#### **Standard Naming**
Adopt OpenTelemetry conventions for consistency:
- **Prefix**: `<resource>.<type>.<action>.<metric>`
  Example: `api.http.request.duration`
- **Suffix**: `.{percentile}` or `.{phase}` (e.g., `.client`, `.p99`).

---

### **2. Instrumentation**
#### **Instrumentation Libraries**
| **Language** | **Library**               | **Example Code Snippet**                                                                 |
|--------------|---------------------------|-----------------------------------------------------------------------------------------|
| Go           | OpenTelemetry SDK         | `tracer.SpanFromContext(ctx).SetAttribute("latency.phase", "api_processing")`          |
| Java         | OpenTelemetry Auto-Instr. | `@WithSpan` annotation on method with phase labeling.                                   |
| Python       | OpenTelemetry             | `span.set_attribute("http.method", request.method)` + record duration.                  |
| Node.js      | OpenTelemetry             | `tracer.startActiveSpan("api.request", callback, { attributes: { phase: "db" } })`      |

#### **HTTP/HTTP2 Instrumentation**
Add latency labels to outgoing HTTP requests:
```go
func handleRequest(w http.ResponseWriter, r *http.Request) {
    start := time.Now()
    defer func() {
        span := tracer.SpanFromContext(r.Context())
        span.SetAttributes(
            attribute.String("http.method", r.Method),
            attribute.String("latency.phase", "api_processing"),
            attribute.Int64("latency.duration", time.Since(start).Microseconds()),
        )
        span.End()
    }()
    // ... handler logic
}
```

#### **Database Queries**
Track DB latency separately:
```python
# Pseudocode
with tracer.start_as_current_span("db.query") as span:
    start_time = time.time()
    result = db.execute("SELECT * FROM users")
    span.set_attribute("latency.phase", "db_query")
    span.set_attribute("latency.duration", (time.time() - start_time) * 1e6)  # Microseconds
```

---

### **3. Querying Latency Metrics**
#### **Prometheus Query Examples**
##### **Total API Latency (p95)**
```promql
histogram_quantile(0.95, sum(rate(api_request_duration_microseconds_bucket[5m])) by (le))
```
##### **Latency by Service and Phase**
```promql
histogram_quantile(0.99, sum(
    rate(user_service_api_request_duration{phase="db"}[1m])
) by (le, service))
```
##### **End-to-End Latency SLO Violation**
```promql
sum(
    rate(api_request_duration_seconds_bucket{le="1000"}[5m])
) > threshold  # Alert if >1000ms for 5m
```

#### **Grafana Dashboard Suggestions**
1. **Latency Percentiles**: Time-series chart for p50/p95/p99.
2. **Histogram**: Show latency distribution (e.g., 90th percentile).
3. **Breakdown by Phase**: Stacked bar chart for `latency.phase` components.
4. **SLO Dashboard**: Compare current latency against SLO thresholds.

---

## **Query Examples (OpenTelemetry)**
#### **Trace-Based Latency**
```bash
# Filter traces where API phase > 500ms
otlpquery \
  'resource.service.name="order-service" and attributes.latency.phase="api"' \
  --metric query='latency.duration > 500000'  # Microseconds
```

#### **Span Aggregation**
```bash
# Group spans by latency and phase
otlpquery \
  'resource.service.name="payment-service"' \
  --metric group='attributes.latency.phase' \
  --metric avg('attributes.latency.duration')
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Metrics-Based Alerts**  | Use latency metrics to trigger alerts (e.g., p99 > 1s).                     | Detecting performance regressions.                                               |
| **Distributed Tracing**   | Correlate latency across services using trace IDs.                            | Debugging cross-service latency issues.                                         |
| **Service Level Objectives (SLOs)** | Define latency-based SLOs (e.g., "99% of requests < 500ms").      | Setting performance expectations.                                                |
| **Chaos Engineering**     | Intentionally introduce latency to test resilience.                          | Validating system recovery from latency spikes.                                  |
| **Circuit Breakers**      | Throttle external API calls if latency exceeds a threshold.                    | Preventing cascading failures due to slow dependencies.                         |

---
## **Best Practices**
1. **Align with OpenTelemetry**: Use standardized metric names/attributes.
2. **Sample Heavy Traces**: For high-cardinality traces (e.g., user IDs), sample traces > p99.
3. **Document SLOs**: Publish latency SLOs alongside metrics (e.g., "Order Service API SLO: p99 < 300ms").
4. **Avoid Overhead**: Sample latency metrics aggressively to reduce instrumentation impact.
5. **Context Propagation**: Ensure latency labels are propagated across service boundaries (e.g., via `traceparent` header).

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Latency spikes missing**          | Missing instrumentation in one phase (e.g., DB).                             | Verify spans are recorded for all components.                                |
| **Noisy percentiles**              | High-cardinality metrics (e.g., `user_id` in labels).                         | Reduce labels or use aggregations (e.g., `user_type`).                       |
| **SLO breaches not alerting**      | Alert threshold mismatch or Prometheus query error.                           | Validate query: `rate(api_request_duration_seconds_bucket{le="1000"}[5m])`. |
| **Traces disconnected**             | Missing traceparent header in cross-service calls.                           | Use OpenTelemetry’s auto-instrumentation or propagate context manually.       |

---
## **References**
- [OpenTelemetry Latency Metrics](https://opentelemetry.io/docs/specs/semantic_conventions/metrics/)
- [Prometheus Histogram Quantiles](https://prometheus.io/docs/practices/histograms/)
- [SLOs: Latency Example](https://sre.google/sre-book/metrics/)

---
**End of Guide** (Word count: ~1000)