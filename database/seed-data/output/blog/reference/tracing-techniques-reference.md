# **[Pattern] Tracing Techniques - Reference Guide**

---

## **1. Overview**
The **Tracing Techniques** pattern enables tracking and logging requests, transactions, correlations, and dependencies across distributed systems. It provides visibility into system behavior, debugging capabilities, and performance optimization by capturing detailed traces of execution flow. This pattern is essential for microservices architectures, event-driven systems, and distributed workflows where understanding the end-to-end flow of a request is critical.

Tracing involves **instrumenting** applications to collect data points (spans) during execution, structuring them hierarchically (traces), and exporting them to a centralized tracing system. Key use cases include:
- **Debugging & Root Cause Analysis**: Reconstructing failures across services.
- **Performance Bottleneck Identification**: Analyzing latency distribution.
- **User-Experience Monitoring**: Mapping requests to business transactions.

---

## **2. Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                          |
|------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Trace**              | A sequence of spans representing an end-to-end request flow.                  | HTTP request from client to DB.     |
| **Span**               | A single operation/segment of a trace (e.g., API call, database query).      | `/users/getUser` endpoint.           |
| **Span Context**       | Metadata (e.g., trace ID, span ID) attached to a span to correlate traces.     | `trace-id=1a2b3c4d`, `span-id=5e6f7g`|
| **Trace Parent**       | The span that generated the current span (establishes hierarchical flow).    | Parent: `GET /orders`, Child: `POST /payments`. |
| **Instrumentation**    | Adding tracing code (e.g., W3C Trace Context headers, SDKs) to applications. | OpenTelemetry SDK in Node.js.        |
| **Sampling**           | Selecting traces to record (e.g., probabilistic or trace-based).             | 1% of traces sampled for cost savings. |
| **Trace Store**        | A database (e.g., Jaeger, Zipkin, OpenTelemetry Collector) storing traces.   | Distributed log backend.             |

---

## **3. Schema Reference**
### **3.1 Core Trace Schema**
| **Field**          | **Type**       | **Description**                                                                 | **Example Value**                       |
|--------------------|----------------|---------------------------------------------------------------------------------|------------------------------------------|
| `trace_id`         | UUID           | Unique identifier for the entire trace.                                        | `1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p`  |
| `start_time`       | Timestamp      | When the trace began.                                                           | `2024-01-01T12:00:00Z`                  |
| `end_time`         | Timestamp      | When the trace completed.                                                      | `2024-01-01T12:00:05Z`                  |
| `spans`            | Array[Span]    | List of spans in the trace.                                                    | `[span1, span2, span3]`                 |

---

### **3.2 Span Schema**
| **Field**          | **Type**       | **Description**                                                                 | **Example Value**                       |
|--------------------|----------------|---------------------------------------------------------------------------------|------------------------------------------|
| `span_id`          | UUID           | Unique identifier for the span.                                                 | `5e6f7g8h-9i0j-1k2l-3m4n-5o6p1r2s3t4u`  |
| `parent_span_id`   | UUID (nullable)| ID of the parent span (nullable for root spans).                                | `1a2b3c4d-5e6f-7g8h` (or `null`)        |
| `name`             | String         | Human-readable operation name (e.g., API endpoint, database query).              | `GET /users/:id`                        |
| `start_time`       | Timestamp      | When the span began.                                                            | `2024-01-01T12:00:01Z`                  |
| `end_time`         | Timestamp      | When the span completed.                                                       | `2024-01-01T12:00:03Z`                  |
| `duration`         | Duration       | Time taken by the span.                                                         | `2ms`                                   |
| `attributes`       | Key-Value Pairs| Metadata (e.g., HTTP status, DB query).                                         | `{http.method: "GET", db.system: "Postgres"}` |
| `events`           | Array[Event]   | Timed log entries (e.g., "Query executed").                                     | `[{timestamp: "12:00:02Z", name: "SQL executed"}]` |
| `links`            | Array[Link]    | References to related traces/spans (for async workflows).                       | `[{trace_id: "1b2c3d4e", span_id: "8h9i0j1k"}]` |

---

### **3.3 Trace Context Header (W3C Standard)**
Used to propagate trace IDs across service boundaries.

| **Header**               | **Description**                                                                 | **Example**                          |
|--------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| `traceparent`            | Base64-encoded trace context.                                                  | `00-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p-01-0000000000000000-01` |
| `tracestate`             | Additional context (e.g., baggage keys).                                     | `p=3;ds=abc123`                      |

**Breakdown of `traceparent`:**
- **Version**: `00` (current W3C version).
- **Trace ID**: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`.
- **Parent ID**: `01` (or `00` for root spans).
- **Flags**: `00` (reserved).

---

## **4. Implementation Details**
### **4.1 Instrumenting Applications**
#### **4.1.1 Client-Side Instrumentation**
- **HTTP Requests**: Inject `traceparent` header in outgoing requests.
  ```javascript
  // Node.js with OpenTelemetry
  const { trace } = require('@opentelemetry/api');
  const tracer = trace.getTracer('http-client');

  async function fetchWithTracing(url) {
    const span = tracer.startSpan('HTTP Request');
    try {
      const response = await fetch(url, {
        headers: {
          'traceparent': trace.getCurrentSpan().context().toTraceparent()
        }
      });
      span.setAttribute('http.status_code', response.status);
      return response;
    } finally {
      span.end();
    }
  }
  ```

#### **4.1.2 Server-Side Instrumentation**
- **Web Frameworks**: Auto-instrument middleware (e.g., Express, FastAPI).
  ```python
  # FastAPI with OpenTelemetry
  from opentelemetry import trace
  from opentelemetry.sdk.trace import TracerProvider
  from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

  trace.set_tracer_provider(TracerProvider())
  FastAPIInstrumentor.instrument_app(app)

  @app.get("/users/{user_id}")
  async def get_user(user_id: str):
      # Span created automatically by FastAPIInstrumentor
      pass
  ```

#### **4.1.3 Database Queries**
- **SDKs**: Wrap database calls with spans.
  ```java
  // Java with OpenTelemetry
  Span currentSpan = tracer.spanBuilder("DB Query").startSpan();
  try (SQLConnection connection = ...; Statement stmt = connection.createStatement()) {
      currentSpan.setAttribute("db.system", "PostgreSQL");
      stmt.execute("SELECT * FROM users WHERE id = ?");
  } finally {
      currentSpan.end();
  }
  ```

---

### **4.2 Sampling Strategies**
| **Strategy**               | **Description**                                                                 | **Use Case**                          |
|----------------------------|-------------------------------------------------------------------------------|----------------------------------------|
| **Always-on Sampling**     | Trace every request (high overhead).                                          | Development environments.              |
| **Probabilistic Sampling** | Randomly sample traces (e.g., 1% probability).                               | Production with high volume.           |
| **Trace-based Sampling**   | Sample based on trace properties (e.g., error traces, slow traces).           | Debugging failures.                   |
| **Head-based Sampling**    | Sample the first N spans in a trace (reduces cost).                          | Cost-sensitive monitoring.             |

**Example (OpenTelemetry):**
```yaml
# sampler.yaml (for OpenTelemetry Collector)
sampling:
  decision_wait: "200ms"
  trace_id_ratio: 0.01  # 1% sampling rate
  asymptote: 0.5
  num_traces: 1000
```

---

### **4.3 Trace Export**
Exported traces are sent to a **trace store** (e.g., Jaeger, Zipkin, OpenTelemetry Collector) via:
- **OTLP (OpenTelemetry Protocol)** (recommended): gRPC or HTTP.
- **Zipkin Thrift**: Legacy format.
- **Logging**: Export to structured logs (e.g., ELK, Splunk).

**Example OTLP Exporter (Node.js):**
```javascript
const { OTLPSpanExporter } = require('@opentelemetry/exporter-otlp');
const exporter = new OTLPSpanExporter({
  url: 'http://localhost:4318/v1/traces'
});

const tracer = new TracerProvider().register({
  spanProcessor: new BatchSpanProcessor(exporter)
});
```

---

## **5. Query Examples**
### **5.1 Filtering Traces by Duration**
**Query (Jaeger UI):**
```
service: "order-service" AND duration > 500ms
```
**Output**: Traces for `order-service` with >500ms latency.

---

### **5.2 Finding Traces with Errors**
**Query (OpenTelemetry Collector):**
```sql
SELECT
  trace_id,
  span.name AS operation,
  duration,
  attributes['error.message']
FROM traces
WHERE attributes['error.type'] = "500"
LIMIT 100;
```
**Output**: HTTP 500 errors across services.

---

### **5.3 Correlating Requests Across Services**
**Query (Zipkin UI):**
```
trace_id: "1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p" AND service: "payment-service, inventory-service"
```
**Output**: Full trace showing `payment-service` → `inventory-service` flow.

---

## **6. Best Practices**
1. **Minimize Overhead**:
   - Use sampling to reduce trace volume.
   - Avoid excessive attributes/events.

2. **Consistent Naming**:
   - Standardize span names (e.g., `GET /users/{id}` instead of `userAPICall`).

3. **Error Handling**:
   - Set `error` attributes when exceptions occur:
     ```javascript
     span.setAttribute('error.message', e.message);
     span.setStatus({ code: SpanStatusCode.ERROR, message: e.message });
     ```

4. **Security**:
   - Sanitize PII in traces (e.g., mask credit card numbers).

5. **Retention Policies**:
   - Delete old traces to avoid storage bloat.

---

## **7. Tools & Ecosystem**
| **Tool**               | **Role**                                  | **Link**                              |
|------------------------|-------------------------------------------|---------------------------------------|
| **OpenTelemetry**      | Standard SDKs/libraries for instrumentation. | [opentelemetry.io](https://opentelemetry.io) |
| **Jaeger**             | Distributed tracing UI/store.            | [jaegertracing.io](https://jaegertracing.io) |
| **Zipkin**             | Legacy tracing system.                   | [zipkin.io](https://zipkin.io)        |
| **OpenTelemetry Collector** | Centralized ingestion/processing.      | [opentelemetry.io/docs/collector/](https://opentelemetry.io/docs/collector/) |
| **Datadog APM**        | Hosted tracing with APM integrations.     | [datadoghq.com](https://www.datadoghq.com) |

---

## **8. Related Patterns**
1. **[Structured Logging]**
   - Complements tracing by logging detailed events at the same level of granularity.
   - *Differences*: Traces are relational (spans), logs are flat (timestamps + metadata).

2. **[Distributed ID Generation]**
   - Ensures unique trace/span IDs across services (e.g., UUIDs, Snowflake IDs).

3. **[Circuit Breaker]**
   - Traces can feed into circuit breakers to detect cascading failures.

4. **[Request/Response Correlation]**
   - Uses trace IDs to correlate logs across services (e.g., `X-Correlation-ID`).

5. **[Metrics]**
   - Traces provide context for metrics (e.g., `latency_p99` from traces).

---

## **9. Troubleshooting**
| **Issue**                     | **Diagnosis**                                                                 | **Solution** |
|--------------------------------|-------------------------------------------------------------------------------|--------------|
| **Missing Traces**             | Instrumentation not applied or exporter failure.                              | Check SDK logs; verify OTLP/HTTP endpoint. |
| **High Latency in Traces**     | Overhead from tracing SDKs or exporter bottlenecks.                           | Enable sampling; reduce attribute volume. |
| **Orphaned Spans**             | Spans without parent/child links (async workflows).                           | Use `links` field to reference async spans. |
| **Duplicate Trace IDs**        | Race conditions in ID generation.                                             | Use distributed ID generators (e.g., Snowflake). |

---

## **10. References**
- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/latest/)
- [Google’s Distributed Tracing Guide](https://cloud.google.com/blog/products/operations/distributed-tracing)