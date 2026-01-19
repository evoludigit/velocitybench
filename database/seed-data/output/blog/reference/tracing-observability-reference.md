# **[Pattern] Tracing Observability: Reference Guide**

---

## **Overview**
**Tracing Observability** is a distributed tracing pattern that monitors interactions between microservices, APIs, and components by capturing request flows across systems. This pattern ensures visibility into latency, dependencies, and bottlenecks in polyglot architectures, enabling efficient debugging, performance tuning, and SLO/SLA compliance.

Unlike logging (which records event data) or metrics (which aggregates performance stats), tracing provides **end-to-end visibility** by correlating events via unique request IDs and timestamps. Ideal for cloud-native applications, tracing helps teams trace:
- **User requests** across services (e.g., frontend → payment service → inventory).
- **Internal system calls** (e.g., database queries, third-party APIs).
- **Error propagation** (e.g., upstream failures cascading downstream).

Key benefits include improved **mean time to resolve (MTTR)** and **proactive issue detection**. This guide covers core concepts, implementation (tools/standards), schema references, and query strategies.

---

## **2. Implementation Details**

### **Key Concepts**
| **Term**               | **Definition**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Span**               | A single operation (e.g., API call, DB query) with start/end timestamps, tags, and logs. |
| **Trace**              | A collection of spans forming a hierarchical tree, representing a single request. |
| **Trace ID**           | A globally unique identifier for all spans in a trace (e.g., UUID).           |
| **Span ID**            | Identifies a specific span; child spans reference parent span IDs via `traceparent` headers. |
| **Context Propagation**| Passing trace IDs via HTTP headers (`tracerspan`, `traceparent`) or W3C Trace Context. |
| **Sampling**           | Randomly selecting traces to reduce overhead (e.g., 1% sampling).               |
| **Tags/Annotations**   | Key-value pairs labeling spans (e.g., `http.method=GET`, `error=true`).        |
| **Logs**               | Structured messages attached to spans (e.g., `error.message=DB timeout`).      |
| **Links**              | References to external traces (e.g., linked to a parent trace for cross-service correlation). |

---

### **3. Core Components**
#### **A. Trace Generation**
1. **Instrumentation**
   - Libraries inject spans manually (sdk-based, e.g., OpenTelemetry) or automatically (agent-based, e.g., Jaeger).
   - Example: A microservice logs a span for an `/orders` API call with tags:
     ```json
     {
       "name": "GET /orders",
       "tags": {
         "http.method": "GET",
         "http.status_code": "200",
         "user.id": "abc123"
       }
     }
     ```
2. **Context Propagation**
   - Trace IDs are embedded in HTTP headers (e.g., `tracerspan=00-4bf92f3577b34dafa3dd330fcfa6e0ba-00f067aa0ba92ace-01`).
   - Auto-injected by SDKs or middleware (e.g., Envoy).

#### **B. Trace Collection**
- **Backends**: Centralized collectors aggregate spans (e.g., OpenTelemetry Collector, Zipkin).
- **Storage**: Traces are stored in databases (e.g., Jaeger, Elasticsearch).

#### **C. Visualization**
- Dashboards (e.g., Grafana, Dynatrace) render traces as:
  - **Service maps**: Dependency graphs with latency heatmaps.
  - **Trace exploration**: Drilldown into individual requests (e.g., "Why did OrderService take 1.2s?").

---

## **3. Schema Reference**
### **Trace Schema (JSON Format)**
```json
{
  "trace_id": "00-4bf92f3577b34dafa3dd330fcfa6e0ba",
  "spans": [
    {
      "span_id": "00f067aa0ba92ace",
      "trace_id": "00-4bf92f3577b34dafa3dd330fcfa6e0ba",
      "parent_id": null,  // Root span
      "name": "/orders",
      "start_time": "2023-10-01T12:00:00.000Z",
      "end_time": "2023-10-01T12:00:05.123Z",
      "duration": 5123000,  // Microseconds
      "tags": {
        "http.method": "GET",
        "http.status_code": "200",
        "user.id": "abc123"
      },
      "logs": [
        {
          "timestamp": "2023-10-01T12:00:02.500Z",
          "severity": "INFO",
          "message": "Querying OrdersDB"
        }
      ],
      "links": [
        {
          "trace_id": "123-...",  // Linked to upstream trace
          "span_id": "xyz-..."
        }
      ]
    },
    {
      "span_id": "1234567890abcdef",
      "trace_id": "00-4bf92f3577b34dafa3dd330fcfa6e0ba",
      "parent_id": "00f067aa0ba92ace",
      "name": "OrdersDB.query",
      "start_time": "2023-10-01T12:00:02.000Z",
      "end_time": "2023-10-01T12:00:04.500Z",
      "tags": {
        "db.operation": "SELECT",
        "db.type": "PostgreSQL"
      }
    }
  ]
}
```

---

## **4. Query Examples**
### **A. Querying Traces via OpenTelemetry**
```bash
# List traces for the last hour with error spans
curl -X POST \
  http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "filter": {
        "start_time": "1h.ago",
        "end_time": "now",
        "spans": [
          {
            "attributes": {
              "error": { "string_value": "true" }
            }
          }
        ]
      }
    }
  }'
```

### **B. Jaeger Query (via CLI)**
```bash
# Find traces where "OrdersDB.query" exceeds 500ms
jaeger query --query 'duration > 500ms and name="OrdersDB.query"'
```

### **C. Grafana Explore (PromQL-like)**
```promql
# Average latency of PaymentService spans
avg(
  histogram_quantile(0.95,
    sum(rate(otel_spans{service="PaymentService"}[5m]))
  )
) by (service)
```

---

## **5. Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **Tools/Libraries**                          |
|---------------------------|-----------------------------------------------------------------------------------|---------------------------------------------|
| **Logging Observability** | Complements traces by attaching logs to spans via `logs` field.                   | OpenTelemetry, Loki                        |
| **Metrics Observability** | Provides aggregate data (e.g., p99 latency) to complement trace details.         | Prometheus, Grafana                        |
| **Distributed Context**   | Extends traces with business context (e.g., `user_id`) for correlation.           | W3C Trace Context, Baggage                  |
| **Auto-Instrumentation**  | Reduces manual instrumentation effort (e.g., auto-injecting spans into HTTP calls).| OpenTelemetry Auto-Instrumentation SDKs     |
| **SLO-Based Alerting**    | Triggers alerts on trace anomalies (e.g., "PaymentService latency > 1s").         | Grafana Alerting, Datadog                   |

---

## **6. Best Practices**
1. **Sampling Strategy**
   - Use **adaptive sampling** (e.g., Jaeger’s "rate-sampling") to balance load and coverage.
   - Prioritize traces for:
     - Errors (`error=true` tag).
     - High-value API routes (e.g., `/checkout`).

2. **Tagging Consistency**
   - Standardize tags (e.g., `http.method`, `db.type`) across services.
   - Avoid redundant tags (e.g., `service.name` if context propagation is used).

3. **Storage Optimization**
   - Archive cold traces (e.g., >7 days old) to reduce costs.
   - Use **trace sampling** to limit stored traces (e.g., 1% of total traffic).

4. **Performance**
   - Minimize span creation overhead (e.g., batch logs).
   - Use **lightweight exporters** (e.g., OTLP gRPC) for high-throughput systems.

5. **Security**
   - Mask sensitive data (e.g., PII) in logs/tags.
   - Validate trace IDs to prevent replay attacks.

---

## **7. Troubleshooting**
| **Issue**                  | **Diagnosis**                                                                 | **Solution**                                  |
|----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Missing traces**         | SDK not initialized or headers not propagated.                               | Verify `otel.traces.exporter` config.        |
| **High latency in traces** | Long DB queries or network delays.                                           | Analyze slow spans in dashboard.             |
| **Orphaned spans**         | Context lost due to misconfigured propagation.                                | Inspect `tracerspan` headers.                |
| **Storage overload**       | Too many traces sampled.                                                      | Adjust sampling rate or archive old traces.   |

---
**See Also**:
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [W3C Trace Context Spec](https://www.w3.org/TR/trace-context/)
- [Jaeger Trace Format](https://www.jaegertracing.io/docs/1.44/spec/)