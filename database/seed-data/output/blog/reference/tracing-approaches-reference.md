# **[Pattern] Tracing Approaches Reference Guide**

---

## **Overview**
Distributed tracing is essential for diagnosing performance bottlenecks, debugging failures, and understanding system behavior in microservices architectures. This **Tracing Approaches** reference guide outlines key methods, implementations, and best practices for tracing user requests and system interactions across services.

Tracing involves collecting timestamps, contexts, and metadata from requests as they propagate through a distributed system. This guide covers **instrumentation strategies, tracing tools, common schemas, and query techniques** to extract meaningful insights. Whether integrating **OpenTelemetry, Jaeger, Zipkin, or custom solutions**, understanding these approaches ensures efficient observability at scale.

---

## **1. Key Concepts**
### **1.1 Core Components**
| Term                  | Description                                                                                                                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Span**              | A single operation or task (e.g., API call, database query) with start/end timestamps, trace ID, operation name, and attributes.                                    |
| **Trace**             | A collection of spans forming an end-to-end request flow, correlated via `trace_id`.                                                                          |
| **Trace ID**          | A unique identifier for a single request across services.                                                                                                      |
| **Span Context**      | Metadata (e.g., `trace_id`, `span_id`, `sampling_decision`) passed between services to maintain trace continuity.                                                 |
| **Instrumentation**   | Adding tracing code (e.g., SDKs, libraries) to applications to generate spans.                                                                                   |
| **Sampling**          | Selecting traces to record (e.g., always, probabilistic, or rule-based) to reduce overhead.                                                                    |
| **Backends**          | Tools (e.g., Jaeger, Zipkin) that store, aggregate, and visualize traces.                                                                                        |

---

## **2. Tracing Approaches**
### **2.1 Instrumentation Strategies**
| Approach               | Description                                                                                                                                                     | Use Case                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------|
| **Auto-Instrumentation** | SDKless tracing via proxies (e.g., Envoy, Istio) or language auto-injectors (e.g., OpenTelemetry AutoInstrumentation).                 | Simplifies tracing for unmodified legacy applications.                                       |
| **Manual Instrumentation** | Explicitly adding trace spans using SDKs (e.g., OpenTelemetry, Datadog, New Relic).                                                                  | Fine-grained control over metrics and attributes in custom services.                           |
| **Library-Based**      | Tracing via existing libraries (e.g., HTTP clients like `axios`, database drivers).                                                           | Reduces boilerplate for common operations (e.g., REST calls, DB queries).                     |
| **Aspect-Oriented**    | Weaving tracing logic into bytecode (e.g., Java agents) or AOP frameworks (e.g., Spring AOP).                                                          | Ideal for enterprise apps with transitive dependencies.                                      |

### **2.2 Sampling Methods**
| Method               | Description                                                                                                                                                     | Pros                                  | Cons                                  |
|----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|---------------------------------------|
| **Always-On**        | Records every span.                                                                                                                                       | High fidelity for debugging.           | High storage/CPU overhead.            |
| **Probabilistic**    | Randomly samples traces (e.g., 1% probability).                                                                                                       | Balances load and fidelity.            | May miss rare edge cases.              |
| **Rule-Based**       | Samples based on criteria (e.g., `error=true`, `latency > 1s`).                                                                                     | Targets critical paths.                | Complex setup; requires monitoring.   |
| **Adaptive**         | Dynamically adjusts sampling rate (e.g., based on system load).                                                                                         | Optimizes resource usage.              | Requires back-end support (e.g., OpenTelemetry Collector). |

---

## **3. Schema Reference**
### **3.1 Standard Span Attributes**
| Attribute          | Type    | Description                                                                                                                                                     | Example Values                          |
|--------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| `trace_id`         | String  | Correlates spans across services.                                                                                                                         | `00-0af7651b8bbd4b9d84d2686rf4e5a3cc`    |
| `span_id`          | String  | Unique identifier for a span.                                                                                                                             | `4af7651b8bbd4b9d84d2686rf4e5a3cc`       |
| `operation_name`   | String  | Describes the span’s purpose (e.g., `GET /users`).                                                                                                        | `database.query`                        |
| `start_time`       | Int64   | Unix timestamp (nanoseconds) when the span began.                                                                                                         | `1678901234567890000`                    |
| `end_time`         | Int64   | Unix timestamp when the span ended.                                                                                                                      | `1678901235123456700`                    |
| `duration`         | Int64   | Span duration in nanoseconds.                                                                                                                             | `500000000`                             |
| `status`           | Enum    | Span status (`UNSET`, `OK`, `ERROR`).                                                                                                                     | `{ code: "OK" }`                         |
| `attributes`       | Map     | Key-value pairs (e.g., `http.method`, `db.user`).                                                                                                         | `{ "http.method": "GET", "db.queryset": "users" }` |

### **3.2 Trace Context Propagation**
| Header/Field       | Purpose                                                                                                                                                     | Example Format                          |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| `traceparent`      | W3C Trace Context header (RFC 8297). Contains `trace_id`, `parent_span_id`, `trace_flags`, and `trace_state`.                                              | `00-0af7651b8bbd4b9d84d2686rf4e5a3cc-0af7651b8bbd4b9d84d2686rf4e5a3cc-01-0000000000000000` |
| `b3` (Zipkin)      | Zipkin-specific headers (`X-B3-TraceId`, `X-B3-SpanId`, `X-B3-ParentSpanId`).                                                                             | `X-B3-TraceId: 0af7651b8bbd4b9d84d2686rf4e5a3cc` |
| `ot` (OpenTelemetry)| OpenTelemetry headers (`traceparent`, `tracestate`).                                                                                                       | Same as `traceparent` above.             |

---

## **4. Query Examples**
### **4.1 Filtering Traces (Jaeger CLI)**
```bash
# Find traces with errors in the last hour
jaeger query --limit=100 --filter='status.code=ERROR' --start=1h ago

# Trace a specific user request (by trace_id)
jaeger query --trace-id=00-0af7651b8bbd4b9d84d2686rf4e5a3cc
```

### **4.2 SQL-like Queries (OpenTelemetry Collector)**
```yaml
pipelines:
  traces:
    receivers:
      otlp:
        endpoint: 0.0.0.0:4317
    processors:
      batch:
        timeout: 1s
    exporters:
      logging:
        loglevel: debug
```

**SQL-like Query Example (PromQL in OpenTelemetry):**
```promql
# Latency percentiles for API endpoints
sum by (service_name, endpoint) (
  rate(otel_http_server_duration_seconds_bucket[5m])
)
```

### **4.3 Aggregating by Service (Zipkin UI)**
1. Navigate to the **Services** tab.
2. Click a service (e.g., `auth-service`).
3. Filter by:
   - **Duration** (e.g., `> 500ms`).
   - **Attributes** (e.g., `user_id = "123"`).

---

## **5. Implementation Details**
### **5.1 OpenTelemetry Setup (Python)**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Configure tracer
trace.set_tracer_provider(TracerProvider())
otel_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otel_exporter)
)

# Instrument a function
tracer = trace.get_tracer(__name__)
@tracer.start_as_current_span("fetch_user")
def fetch_user(user_id):
    # Your logic here
    return user_data
```

### **5.2 Sampling Configuration (OpenTelemetry Collector)**
```yaml
processors:
  sampler:
    type: probabilistic
    parameters:
      sampling_rate: 0.1  # 10% of traces
```

### **5.3 Backend Storage Options**
| Backend     | Type               | Features                                                                                                                                                     | Ingestion Cost |
|-------------|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|
| **Jaeger**  | Distributed        | Native UI, Thrift gRPC, strong consistency.                                                                                                                 | Medium         |
| **Zipkin**  | Centralized        | Simple, HTTP/JSON storage, less scalable.                                                                                                                  | Low            |
| **OpenTelemetry Collector** | Hybrid          | Processes, routes, and exports traces (e.g., to Elasticsearch, BigQuery).                                                                                 | Medium         |

---

## **6. Query Performance Best Practices**
1. **Limit Scope**: Use `trace_id` or `service_name` filters to avoid full-scope queries.
2. **Avoid `*` Wildcards**: Replace with specific attribute keys (e.g., `http.method = "POST"` instead of `http.*`).
3. **Sampling**: Use **adaptive sampling** (e.g., OpenTelemetry’s `always_sampler` for critical paths).
4. **Indexing**: Ensure backends (e.g., Elasticsearch, Jaeger) index attributes like `status.code` for fast queries.

---
## **7. Common Pitfalls**
| Pitfall                          | Solution                                                                                                                                                     |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **High Cardinality Attributes**   | Use fixed sets of values (e.g., `http.method` instead of raw URLs).                                                                                         |
| **Trace ID Collisions**           | Use **W3C Trace Context** (`traceparent`) headers for propagation.                                                                                          |
| **Cold Starts in Serverless**     | Pre-warm tracing agents or use **auto-instrumentation** (e.g., OpenTelemetry AutoInstrumentation).                                                           |
| **Overhead from Always-On Tracing** | Implement **probabilistic sampling** or **rule-based sampling** for non-critical services.                                                            |

---

## **8. Related Patterns**
| Pattern                          | Description                                                                                                                                                     | When to Use                                                                                     |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **[Distributed Context Propagation]** | Passing request context (e.g., `user_id`, `auth_token`) across services.                                                                           | When services need to correlate logs/metrics beyond traces.                                      |
| **[Circuit Breaker]**             | Limiting calls to failing services to prevent cascading failures.                                                                                     | In resilient architectures with unreliable dependencies.                                        |
| **[Retry with Backoff]**         | Exponential backoff for transient failures (e.g., database retries).                                                                                 | Handling flaky services in event-driven systems.                                                |
| **[Observability Pipeline]**      | Centralizing logs, metrics, and traces (e.g., ELK, Grafana + Prometheus + Jaeger).                                                              | For holistic system monitoring and SLO tracking.                                                 |
| **[Idempotent Operations]**       | Ensuring retries/side effects are non-destructive.                                                                                                     | In payment systems or order processing where duplicates are harmful.                             |

---
## **9. Further Reading**
- [OpenTelemetry Tracing Documentation](https://opentelemetry.io/docs/tracing/)
- [Jaeger Architecture Guide](https://www.jaegertracing.io/docs/1.36/architecture/)
- [W3C Trace Context Specification (RFC 8297)](https://www.w3.org/TR/trace-context/)
- [Distributed Tracing Anti-Patterns (Grafana)](https://grafana.com/blog/2021/02/25/distributed-tracing-anti-patterns/)