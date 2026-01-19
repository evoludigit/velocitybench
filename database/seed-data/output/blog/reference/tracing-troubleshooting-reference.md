# **[Pattern] Tracing Troubleshooting – Reference Guide**

---
## **Overview**
Tracing Troubleshooting is a structured approach to diagnosing distributed systems by analyzing request flow, service interactions, and latency bottlenecks using trace data. This pattern helps identify slow endpoints, cascading failures, or misconfigurations by following requests across microservices, containerized environments, or serverless functions. It leverages distributed tracing tools (e.g., OpenTelemetry, Jaeger, Zipkin) to correlate logs, metrics, and traces, improving MTTR (Mean Time to Repair) in complex architectures.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Trace**              | A sequence of spans representing a single request’s journey through services.                   | A user clicking a button → frontend → API gateway → payment service → database.                |
| **Span**               | A logical unit of work (e.g., an HTTP call, DB query) with start/end timestamps and attributes. | `GET /api/payment` span with a `950ms` duration and `user_id=12345` context.                   |
| **Context Propagation**| Attaching trace IDs/spans to outgoing requests to maintain correlation across services.        | Setting `X-Trace-ID` header in each request to link spans.                                      |
| **Sampling**           | Selecting traces for capture based on rate (e.g., 1% of requests) or criteria (e.g., errors).   | Enabling traces only for `5XX` responses or `/admin` endpoints.                                 |
| **Annotations**        | Key-value pairs added to spans for debugging (e.g., `error_type=timeout`).                      | `{ "db": "postgres", "query": "SELECT * FROM orders WHERE status='pending'" }` in a span.       |
| **Service Map**        | Visual representation of dependencies between services based on trace data.                       | A graph showing `frontend → auth-service → cache` with latency annotations.                    |

---

## **Implementation Details**
### **1. Setup & Tools**
#### **Core Components**
| **Tool**       | **Purpose**                                                                 | **Example Integration**                          |
|----------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **OpenTelemetry** | Standardized SDKs for instrumentation (auto-instrumentation, manual tags). | Python `opentelemetry-sdk`, Java `OpenTelemetry Auto-Instrumentation`. |
| **Trace Backend** | Stores and processes traces (e.g., Jaeger, Zipkin, Datadog, AWS X-Ray).   | Sending traces to `Jaeger Collector` via OTLP.    |
| **Instrumentation** | Adding trace spans to code (libraries, SDKs, or custom tags).            | Wrapping a `db.query()` call in a span.          |

#### **Instrumentation Levels**
| **Level**       | **Scope**                          | **Implementation**                                  |
|-----------------|------------------------------------|-----------------------------------------------------|
| **Library**     | Framework-level (e.g., Flask, Spring Boot). | Use `opentelemetry-instrumentation-flask`.          |
| **Custom**      | Business logic (e.g., `orderProcess()`). | Manually create spans: `tracer.start_span("process_order")`. |
| **Proxy-Based** | Sidecar (e.g., Istio, Envoy) or API Gateway. | Inject `X-B3-*` headers for context propagation.    |

---

### **2. Trace Sampling**
Configure sampling to balance trace volume and debugging efficiency:
| **Strategy**       | **Use Case**                          | **Example**                                      |
|--------------------|---------------------------------------|--------------------------------------------------|
| **Rate-based**     | Fixed percentage of traces (e.g., 1%). | `sampling_rate=0.01` in OpenTelemetry.           |
| **Threshold**      | Sample based on span duration/error.   | `if span.duration > 1000ms: sample` in Jaeger.   |
| **Headers**        | Explicitly request traces (e.g., debug mode). | Set `X-Debug-ID: 123` in test requests.          |

**Code Example (OpenTelemetry SDK):**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import sampling

# Configure adaptive sampling
sampler = sampling.AdaptiveSampler(1.0, 100.0, 10)
tracer_provider = trace.get_tracer_provider()
tracer_provider.add_span_processor(trace.propagation.TraceContextPropagator())
tracer_provider.sampler = sampler
```

---

### **3. Context Propagation**
Ensure trace IDs flow between services via headers or message payloads:
| **Protocol** | **Header Format**                     | **Example**                                  |
|--------------|--------------------------------------|----------------------------------------------|
| **HTTP**     | `traceparent` (W3C standard)         | `traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01` |
| **gRPC**     | `X-B3-TraceId` (B3 format)           | `X-B3-TraceId: 4bf92f3577b34da6a3ce929d0e0e4736` |
| **Kafka**    | Message header (`_ot_*` keys)        | `{"_ot_trace_id": "12345"}`                   |

**Example (Python HTTP Client):**
```python
import http.client
from opentelemetry import trace

conn = http.client.HTTPSConnection("api.example.com")
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("client_call") as span:
    # Propagate context
    headers = trace.propagation.get_formatter(
        trace.propagation.TraceContextPropagator()
    )(trace.get_current_span().context)
    conn.request("GET", "/data", headers=headers)
```

---

### **4. Advanced Techniques**
| **Technique**          | **Description**                                                                 | **Tool/Example**                              |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Span Attributes**    | Add custom metadata to spans for filtering.                                   | `span.set_attribute("user_role", "admin")`    |
| **Subspans**           | Break down complex operations (e.g., `db.query` → `analyze`, `execute`).     | Nested spans in a database interaction.       |
| **Error Handling**     | Auto-link errors to spans (e.g., `500` → mark span as `error=true`).           | OpenTelemetry SDK auto-instrumentation.       |
| **Service Graph**      | Visualize dependencies and latency between services.                           | Jaeger UI, Datadog Service Map.               |

---

## **Schema Reference**
### **Trace Schema (JSON)**
```json
{
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spans": [
    {
      "span_id": "00f067aa0ba902b7",
      "name": "GET /api/users",
      "start_time": "2023-10-01T12:00:00Z",
      "end_time": "2023-10-01T12:00:05Z",
      "duration": "5000000",  // Microseconds
      "attributes": {
        "http.method": "GET",
        "http.url": "/api/users",
        "user.id": "12345"
      },
      "status": {
        "code": "OK"
      },
      "links": [
        {
          "trace_id": "4bf92f3577b34da6...",
          "span_id": "00f067aa0ba902b7",
          "type": "CHILD_OF"
        }
      ]
    },
    {
      "span_id": "4a56f61b1b1a44f2",
      "name": "query_users_db",
      "start_time": "2023-10-01T12:00:02Z",
      "end_time": "2023-10-01T12:00:03Z",
      "attributes": {
        "db.system": "postgres",
        "db.statement": "SELECT * FROM users WHERE id = :id"
      },
      "status": {
        "code": "OK"
      }
    }
  ]
}
```

### **Key Fields**
| **Field**       | **Type**    | **Description**                                      | **Example**                          |
|-----------------|------------|------------------------------------------------------|--------------------------------------|
| `trace_id`      | String     | Unique identifier for the entire trace.               | `4bf92f3577b34da6a3ce929d0e0e4736`   |
| `span_id`       | String     | Unique ID for a single span.                          | `00f067aa0ba902b7`                   |
| `name`          | String     | Operation name (e.g., HTTP endpoint, DB query).       | `GET /api/users`                     |
| `duration`      | Int (µs)   | Span execution time.                                 | `5000000` (5 ms)                     |
| `attributes`    | Dict       | Key-value pairs (e.g., HTTP headers, custom tags).    | `{"user.role": "premium"}`           |
| `status`        | Object     | Success/failure code.                                | `{"code": "ERROR", "message": "Timeout"}` |
| `links`         | Array      | References to parent/child spans.                     | `[{ "trace_id": "...", "type": "CHILD_OF" }]` |

---

## **Query Examples**
### **1. Filter Traces by Error**
**Jaeger CLI:**
```bash
jaeger query --filter 'status.code=ERROR'
```
**Datadog:**
```sql
/* Datadog Trace Search */
SELECT
  trace_id,
  span.name,
  duration
FROM traces
WHERE status == "ERROR"
  AND span.name LIKE "%payment%"
LIMIT 10;
```

### **2. Latency Analysis**
**Zipkin:**
```bash
zipkin query --maxDuration=1000ms --startTime=2023-10-01T12:00:00Z
```

**OpenTelemetry Query (PromQL):**
```promql
# Traces with >1s duration
sum by (service) (
  rate(otel_service_attributes{attribute_service_name!="", attribute_span_name!=""}[5m])
  * on(service) group_left(span_name)
  histograms_quantile(0.99, sum by (le, service, span_name) (rate(otel_span_attributes{attribute_span_name!=""}[5m])))
)
> 1000
```

### **3. Service Dependency Graph**
**Jaeger UI:**
- Navigate to **Service Map** tab.
- Filter for `/api/payment` to see downstream calls.

**Datadog:**
```sql
/* Service dependency graph */
SELECT
  source_service,
  target_service,
  avg(duration)
FROM service_dependencies
WHERE source_service = "frontend"
GROUP BY source_service, target_service
ORDER BY avg(duration) DESC;
```

---

## **Common Pitfalls & Fixes**
| **Issue**                          | **Root Cause**                          | **Solution**                                  |
|-------------------------------------|----------------------------------------|-----------------------------------------------|
| **Missing trace IDs**               | Context not propagated between services. | Check headers (e.g., `X-B3-TraceId`).         |
| **High sampling overhead**          | 100% sampling on production.           | Use adaptive sampling (e.g., `AdaptiveSampler`). |
| **No errors linked to traces**       | Errors not auto-instrumented.          | Enable SDK error handlers (e.g., `opentelemetry.instrumentation.requests`). |
| **Slow trace processing**           | Backend (e.g., Jaeger) overload.      | Increase collector resources or enable compression. |

---

## **Related Patterns**
| **Pattern**               | **Connection to Tracing**                                                                 | **Reference**                          |
|---------------------------|-------------------------------------------------------------------------------------------|----------------------------------------|
| **Circuit Breaker**       | Use traces to detect cascading failures (e.g., `5XX` spans triggering circuit trips).    | [Circuit Breaker Pattern](link)        |
| **Retry with Exponential Backoff** | Analyze traces to identify retryable vs. non-retryable errors (e.g., `429` vs. `500`).       | [Retry Pattern](link)                  |
| **Distributed Locks**     | Instrument locks to trace contention (e.g., `Redlock` span duration).                       | [Distributed Locks Pattern](link)      |
| **Observability Pipeline** | Combine traces with metrics/logs (e.g., correlate `high_latency` metric with slow traces). | [Observability Pipeline](link)          |

---
## **Further Reading**
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger User Guide](https://www.jaegertracing.io/docs/latest/)
- [Grafana Mimir + OpenTelemetry](https://grafana.com/docs/mimir/latest/get-started/opentelemetry/)