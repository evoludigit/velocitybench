# **[Pattern] Latency Monitoring – Reference Guide**

---

## **Overview**
Latency Monitoring is a **distributed tracing and performance optimization** pattern used to track and analyze delays in system responses across microservices, APIs, databases, or external dependencies. By instrumenting application code with timestamps and correlating requests across services, teams can:
- **Identify bottlenecks** in real time (e.g., slow database queries, network hops, or third-party APIs).
- **Set up SLOs (Service Level Objectives)** with automated alerts for latency thresholds.
- **Correlate user-facing latency** with internal service metrics.
- **Optimize performance** by resolving high-latency paths before they impact end users.

Latency Monitoring is critical for **SRE (Site Reliability Engineering)** and **observability** pipelines, particularly in cloud-native and serverless architectures. This guide covers implementation best practices, schemas, and query examples using common tools like **OpenTelemetry, Prometheus, Jaeger, and Grafana**.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**         | **Description**                                                                                     | **Tools/Standards**                          |
|-----------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Trace IDs**         | Unique identifiers for end-to-end requests across services.                                          | OpenTelemetry, Jaeger, Zipkin               |
| **Timestamps**        | Mark the start/end of critical operations (e.g., API calls, DB queries, cache hits/misses).         | OTLP (OpenTelemetry Protocol)               |
| **Span Context**      | Propagates trace IDs between services (e.g., `traceparent` HTTP header).                           | W3C Trace Context (RFC 9324)               |
| **Instrumentation**   | Auto-instrumentation (e.g., OpenTelemetry Agent) or manual instrumentation (SDKs for Go/Java/Python). | OTel SDKs, Datadog, New Relic              |
| **Sampling**          | Controls trace volume (e.g., probabilistic sampling, adaptive sampling, or trace-by-ID).           | Jaeger, OpenTelemetry Collector             |
| **Storage Backend**   | Persistent storage for traces (e.g., Elasticsearch, PostgreSQL, or managed services like Honeycomb). | Jaeger, Grafana Tempo, AWS X-Ray            |
| **Visualization**     | Dashboards for latency analysis (e.g., service maps, flame graphs, histograms).                   | Grafana, Kibana, Datadog                    |
| **Alerting**          | Triggers alerts when latency exceeds thresholds (e.g., Prometheus + Alertmanager).                 | Prometheus, PagerDuty, Opsgenie            |

---

### **2. Latency Monitoring Lifecycle**
1. **Instrumentation**
   - Add timing annotations (spans) to key operations (e.g., `db.query`, `http.request`, `cache.get`).
   - Example (OpenTelemetry Python):
     ```python
     from opentelemetry import trace
     tracer = trace.get_tracer(__name__)

     with tracer.start_as_current_span("database_query"):
         # Execute DB query
         start = time.time()
         results = db.query("SELECT * FROM users")
         tracer.add_event("query_completed", attributes={"duration_ms": time.time() - start})
     ```

2. **Propagation**
   - Attach `traceparent` header to HTTP requests:
     ```
     traceparent: 00-<trace_id>-<span_id>-01
     ```

3. **Storage & Processing**
   - Send traces to a backend (e.g., Jaeger, OpenTelemetry Collector).
   - Aggregate metrics (e.g., `http_server_duration_milliseconds`).

4. **Analysis & Alerting**
   - Query traces for slow endpoints (e.g., `%99 HTTP latency > 500ms`).
   - Set up alerts in Prometheus:
     ```
     alert HighLatency { alert if http_server_duration_milliseconds > 500 for 5m }
     ```

---

## **Schema Reference**
Below are standard schemas for latency monitoring data models.

### **1. Trace Data Model (OpenTelemetry)**
| **Field**            | **Type**       | **Description**                                                                 |
|----------------------|----------------|---------------------------------------------------------------------------------|
| `trace_id`           | UUID (hex)     | Globally unique identifier for an end-to-end request.                           |
| `span_id`            | UUID (hex)     | Unique identifier for a single operation within a trace.                         |
| `name`               | String         | Operation name (e.g., `get_user`, `process_payment`).                           |
| `start_time`         | Unix timestamp | When the span began (nanoseconds since epoch).                                  |
| `end_time`           | Unix timestamp | When the span completed.                                                         |
| `duration`           | Duration       | Time taken (nanoseconds).                                                        |
| `attributes`         | Key-value pairs| Metadata (e.g., `http.method="POST"`, `db.system="PostgreSQL"`, `status_code=500`). |
| `status`             | String         | Span status (`OK`, `ERROR`, `UNKNOWN`).                                          |
| `parent_span_id`     | UUID (hex)     | ID of the parent span (for hierarchical traces).                                |

---

### **2. Aggregated Metrics (Prometheus)**
| **Metric Name**                          | **Type**  | **Description**                                                                 |
|------------------------------------------|-----------|---------------------------------------------------------------------------------|
| `http_server_requests_total`             | Counter   | Total HTTP requests.                                                            |
| `http_server_duration_seconds`           | Histogram | Latency distribution (buckets: 50ms, 100ms, 500ms, 1s, etc.).                 |
| `db_query_duration_seconds`               | Summary   | Average DB query latency (with quantiles: `p99`, `p95`).                        |
| `service_latency_seconds_bucket`          | Histogram | Custom latency buckets (e.g., `le="0.1"`, `le="0.5"`).                          |
| `trace_count_total`                      | Counter   | Total traces sampled.                                                           |
| `error_span_count_total`                 | Counter   | Spans marked as `ERROR`.                                                         |

---

## **Query Examples**
### **1. Querying Traces (Jaeger/Zipkin)**
**Find slow API calls (top 5 endpoints by latency):**
```
span.name = "api.endpoint"
| bucket(span.duration, 50ms) group by span.name
| sort -span.duration
| limit 5
```

**Correlate latency with errors:**
```
findService("payment-service")
| filter(span.name == "process_payment" AND span.status == "ERROR")
| timeslice(1m)
| aggregate count:span_id by {span.name}
```

---

### **2. Querying Metrics (Prometheus)**
**Find services with P99 latency > 500ms:**
```promql
histogram_quantile(0.99, rate(http_server_duration_seconds_bucket[5m])) > 0.5
```

**Compare latency before/after a deployment:**
```promql
rate(http_server_duration_seconds_sum[5m]) /
  rate(http_server_duration_seconds_count[5m])  # Average latency
```
Filter for a specific revision:
```
{deployment="rev-abc123"} rate(http_server_duration_seconds_sum[5m]) / rate(http_server_duration_seconds_count[5m])
```

**Alert for sudden latency spikes:**
```promql
rate(http_server_duration_seconds{quantile="0.95"}[5m]) > 2 * rate(http_server_duration_seconds{quantile="0.95"}[1h])
```

---

### **3. Visualization (Grafana)**
- **Service Graph**: Use the [Service Map Panel](https://grafana.com/docs/grafana/latest/panels-visualizations/service-map/) to visualize trace paths.
- **Latency Histograms**: Plot `http_server_duration_seconds_bucket` with percentiles.
- **Error Rate + Latency Correlation**: Annotate traces with `span.status=ERROR` to find latency-eroding errors.

**Grafana Dashboard Example:**
1. **Panel 1**: `rate(http_server_duration_seconds_sum{quantile="0.99"}[5m])` (P99 latency).
2. **Panel 2**: `http_server_requests_total` (request volume).
3. **Panel 3**: Traces view (filter by `http_server_duration_seconds > 1s`).

---

## **Implementation Checklist**
| **Step**                          | **Action Items**                                                                                     |
|-----------------------------------|------------------------------------------------------------------------------------------------------|
| **1. Instrument Code**            | Add OpenTelemetry SDK to all services.                                                               |
| **2. Define Key Spans**           | Instrument critical paths (APIs, DB calls, external APIs).                                         |
| **3. Configure Sampling**         | Start with **100% sampling** for debugging, then adjust (e.g., probabilistic or adaptive).          |
| **4. Set Up Propagation**         | Enable `traceparent` header propagation for HTTP services.                                          |
| **5. Store Traces**               | Use Jaeger, Tempo, or Honeycomb for persistence.                                                   |
| **6. Aggregate Metrics**          | Export to Prometheus/Chronix for dashboards and alerts.                                             |
| **7. Define SLOs**                | Set latency budgets (e.g., "99% of requests < 300ms").                                             |
| **8. Build Alerts**               | Use Prometheus + Alertmanager to notify on SLO breaches.                                          |
| **9. Optimize**                   | Analyze slow traces weekly; refactor bottlenects (e.g., cache DB queries).                         |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Distributed Tracing](https://github.com/microsoft/architecture-guidance/tree/main/patterns/distributed-tracing)** | End-to-end request tracking across services.                                                   | Debugging cross-service latency or errors.                                      |
| **[Metrics-Based Alerting](https://martinfowler.com/articles/metrics.html)** | Alert on key metrics (e.g., error rates, latency).                                               | Proactive issue detection.                                                      |
| **[Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)** | Fail fast for dependent services with high latency.                                              | Prevent cascading failures from slow third-party APIs.                            |
| **[Retry with Backoff](https://martinfowler.com/eaaCatalog/retry.html)** | Handle transient latency spikes with exponential backoff.                                         | Resilient communication with external systems.                                  |
| **[Auto-Scaling](https://cloud.google.com/blog/products/compute/auto-scaling-101)** | Dynamically adjust resources based on latency spikes.                                             | Handle sudden traffic loads.                                                     |
| **[Canary Deployments](https://martinfowler.com/bliki/CanaryRelease.html)** | Gradually roll out changes while monitoring latency impact.                                       | Low-risk feature rollouts.                                                      |

---

## **Tools & Libraries**
| **Category**          | **Tools**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------|
| **Tracing**           | [OpenTelemetry](https://opentelemetry.io/), Jaeger, Zipkin, Honeycomb                         |
| **Metrics**           | Prometheus, Graphite, Datadog, New Relic                                                  |
| **Logging**           | ELK Stack (Elasticsearch, Logstash, Kibana), Loki, Splunk                                   |
| **Alerting**          | Prometheus Alertmanager, PagerDuty, Opsgenie, VictorOps                                      |
| **Visualization**     | Grafana, Kibana, Datadog Dashboards, Honeycomb Query Language                               |
| **Sampling**          | OpenTelemetry Collector (adaptive sampling), Jaeger Head-Based Sampling                     |

---

## **Best Practices**
1. **Start Simple**: Begin with **auto-instrumentation** (e.g., OpenTelemetry Agent) before manual spans.
2. **Sample Wisely**: Use **adaptive sampling** to reduce trace volume while capturing critical paths.
3. **Annotate Meaningfully**: Add useful attributes (e.g., `user_id`, `request_body_size`, `db.table`).
4. **Set Realistic SLOs**: Align latency targets with business needs (e.g., 99th percentile < 500ms).
5. **Correlate Logs, Metrics, Traces**: Use tools like [CorrelateID](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/correlation/context.md) to link records.
6. **Monitor Monitoring**: Track `trace_count_total` and sampling efficiency.
7. **Document Bottlenecks**: Maintain a runbook for common latency issues (e.g., "Slow DB query on `users` table").

---
**Further Reading**:
- [OpenTelemetry Latency Best Practices](https://opentelemetry.io/docs/concepts/latency/)
- [Prometheus Histogram Documentation](https://prometheus.io/docs/practices/histograms/)
- [Grafana Service Map Tutorial](https://grafana.com/docs/grafana/latest/panels-visualizations/service-map/)