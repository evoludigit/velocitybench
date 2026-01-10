# **[Pattern] Distributed Tracing & Request Context Reference Guide**

---

## **1. Overview**
In a microservices architecture, user requests often traverse multiple services, databases, and external systems before completing. **Distributed tracing** captures the full end-to-end execution flow by assigning a unique **trace ID** and propagating **context** (e.g., correlation IDs, span metadata) across service boundaries. This enables observability, latency analysis, and debugging across distributed systems.

Key challenges include:
- **Trace ID propagation**: Ensuring every service in the call chain records its execution under the same trace.
- **Sampling**: Controlling trace volume for performance.
- **Context management**: Avoiding excessive overhead while retaining critical metadata.

Tools like **OpenTelemetry**, **Jaeger**, and **Zipkin** standardize implementation via lightweight headers (e.g., `traceparent`) or structured payloads (e.g., JSON).

---

## **2. Key Concepts**
| Concept                | Definition                                                                                     | Example Values/Format                          |
|------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------|
| **Trace**              | A sequence of spans representing a single user request.                                        | `trace_id: 123e4567-e89b-12d3-a456-426614174000` |
| **Span**               | A single operation (e.g., HTTP request, DB query) within a trace.                            | `span_id: 550e8400-e29b-41d4-a716-446655440000` |
| **Trace Context**      | Metadata (headers, payload) attached to requests to link spans.                                | `traceparent: 00-123e4567e89b12d3a456426614174000`|
| **Correlation ID**     | User-facing identifier (e.g., order ID) preserved across services.                           | `correlation_id: abc123`                      |
| **Sampler**            | Decides whether to record a trace (e.g., 1% of requests).                                   | `sampling_rate: 0.01`                         |
| **Exporter**           | Sends spans to a backend system (e.g., Jaeger, OpenTelemetry Collector).                    | `jaeger://localhost:14268/api/traces`         |

**Propagation Modes**:
- **HTTP Headers**: Most common (e.g., `traceparent`, `tracestate`).
- **W3C Trace Context**: Standardized format for HTTP/S.
- **Payload Injection**: For non-HTTP protocols (e.g., gRPC metadata).

---

## **3. Schema Reference**
### **3.1 Traceparent Header (W3C Standard)**
```plaintext
traceparent: <version>-<trace_id>-<parent_span_id>-<flags>
```
| Field       | Data Type   | Description                                                                               | Example (Hex)          |
|-------------|-------------|-------------------------------------------------------------------------------------------|------------------------|
| **version** | String (4)  | Format version (e.g., `"00"`).                                                            | `00`                   |
| **trace_id**| UUID        | Unique identifier for the trace.                                                          | `123e4567e89b12d3`     |
| **parent_id** | UUID    | Span ID of the parent (empty for root span).                                               | `e89b12d3a4564266`     |
| **flags**    | Binary (2)  | Sampling decision (`00` = un-sampled, `01` = sampled).                                   | `01`                   |

**Flags**: `01` = sampled, `00` = un-sampled.

---

### **3.2 Tracestate Header (Optional)**
```plaintext
tracestate: <key1>=<value1>,<key2>=<value2>
```
- Stores vendor-specific context (e.g., `b3={trace_id=123,span_id=456}` for AWS/X-Ray).

---

### **3.3 Span Metadata (JSON Example)**
```json
{
  "trace_id": "123e4567-e89b-12d3-a456-426614174000",
  "span_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "api.service.getUser",
  "start_time": "2023-10-01T12:00:00Z",
  "end_time": "2023-10-01T12:00:05Z",
  "attributes": {
    "http.method": "GET",
    "http.url": "/users/123",
    "user.correlation_id": "abc123",
    "db.query": "SELECT * FROM users WHERE id = 123"
  },
  "status": {
    "code": "OK"
  }
}
```

---

## **4. Implementation Steps**
### **4.1 Instrumentation (Languages)**
#### **Java (OpenTelemetry)**
```java
// Initialize OpenTelemetry
Tracer tracer = OpenTelemetry.getTracer("my-app");

// Start a span
Span span = tracer.spanBuilder("api.service.getUser")
    .setAttribute("http.method", "GET")
    .startSpan();

// Inject trace context into HTTP headers
PropagatorContext propagatorContext = Propagators.HTTP_HEADER.propagate(
    RequestContext.current(),
    new HttpContext(httpRequest, httpResponse));

// Propagate to downstream service
propagatorContext.inject(new SpanContext(traceId, spanId), new HttpRequest());
```

#### **Python (OpenTelemetry)**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

# Configure exporter
exporter = JaegerExporter(
    endpoint="http://jaeger:14268/api/traces",
    sampling_rate=0.01
)
provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

# Get tracer
tracer = trace.get_tracer(__name__)

# Start span
with tracer.start_as_current_span("api.service.getUser") as span:
    span.set_attribute("http.method", "GET")
    # Propagate via headers (auto-injected by OpenTelemetry)
    span_context = span.get_span_context()
    text_map = {}
    Propagators.http().inject(span_context, text_map)
    headers["traceparent"] = text_map["traceparent"]
```

---

### **4.2 Propagation Modes**
| Protocol  | Propagation Mechanism                          | Example Header/Payload                     |
|-----------|------------------------------------------------|--------------------------------------------|
| **HTTP**  | `traceparent` + `tracestate` headers.          | `traceparent: 00-123e4567e89b12d3...`     |
| **gRPC**  | Custom metadata (`b3`, `x-request-id`).         | `b3: {trace_id=123,span_id=456}`          |
| **GraphQL** | HTTP headers (same as REST).                     | Same as HTTP.                              |
| **MQTT**  | Custom MQTT properties or payload injection.   | `{"trace_id": "123e4567..."}` payload     |

---

### **4.3 Sampling Strategies**
| Strategy               | Description                                                                 | Example                          |
|------------------------|-----------------------------------------------------------------------------|----------------------------------|
| **Always-on**          | Record every trace (high overhead).                                         | `sampling_rate: 1.0`             |
| **Probabilistic**      | Sample with X% chance.                                                       | `sampling_rate: 0.01` (1% of traces) |
| **Header-based**       | Sample only if `X-Sampling-Flag` header is set.                              | `X-Sampling-Flag: 1`             |
| **Trace ID-based**     | Sample based on trace ID hash (e.g., first N traces).                       | Custom logic                     |

---

## **5. Query Examples**
### **5.1 Jaeger UI Queries**
- **Trace Search**:
  ```
  trace_id=123e4567-e89b-12d3-a456-426614174000
  ```
- **Service Filter**:
  ```
  service=payment-service
  ```
- **Duration Filter** (slow requests):
  ```
  duration>1000
  ```

### **5.2 OpenTelemetry Collector Query**
```yaml
# metrics.promql_config
query: |
  sum by (service_name) (
    rate({job="otel-collector", metric="openTelemetry/span/duration"})
    [5m]
  ) > 500  # Alert if >500ms avg duration
```

### **5.3 Log Correlation**
**Log Format**:
```json
{
  "message": "Failed to fetch user data",
  "level": "ERROR",
  "trace_id": "123e4567-e89b-12d3-a456-426614174000",
  "span_id": "550e8400-e29b-41d4-a716-446655440000",
  "correlation_id": "abc123"
}
```
**Grep Command**:
```bash
grep -E '"trace_id": "123e4567.*"abc123" logs/*.log
```

---

## **6. Best Practices**
### **6.1 Performance Considerations**
- **Minimize Overhead**: Avoid serializing large payloads (e.g., avoid JSON for HTTP headers).
- **Sampling**: Start with `sampling_rate=0.1` and adjust based on observability needs.
- **Batch Exports**: Use `BatchSpanProcessor` (OpenTelemetry) to reduce network calls.

### **6.2 Error Handling**
- **Fallback**: If headers are missing, use a local-generated `trace_id` (less ideal).
- **Retries**: Ensure retries include the same trace context to avoid "lost" spans.

### **6.3 Schema Evolution**
- **Backward Compatibility**: Use vendor-specific `tracestate` for experimental fields.
- **Deprecation**: Mark deprecated fields (e.g., `b3` for HTTP) and migrate to `traceparent`.

---

## **7. Common Pitfalls**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|---------------------------------------------------------------------------|
| **Trace ID Collisions**           | Use UUIDv4/v7 (time-safe).                                                 |
| **Missing Context Propagation**   | Validate headers on service entry (e.g., middleware).                       |
| **High Cardinality**             | Aggregate metrics by `service_name` + `operation` instead of `trace_id`. |
| **Sampling Bias**                 | Use stratified sampling (e.g., sample 100% of slow traces).                |
| **Vendor Lock-in**                | Prefer W3C standards (`traceparent`) over proprietary formats.             |

---

## **8. Related Patterns**
1. **[Service Mesh Integration]**
   - **Link**: Use Istio/Linkerd’s built-in tracing (e.g., `envoy.filters.http.local_ratelimit`).
   - **Benefit**: Automatic sidecar injection and propagation.

2. **[Centralized Logging]**
   - **Link**: Correlate logs with traces using `trace_id` in log entries.
   - **Tool**: ELK Stack, Loki, or Datadog.

3. **[Circuit Breaker]**
   - **Link**: Attach trace context to circuit-breaker events for failure analysis.
   - **Use Case**: Identify which downstream service caused a timeout.

4. **[Idempotency]**
   - **Link**: Use `correlation_id` as a transaction ID for retryable operations.
   - **Example**: `PUT /orders/{correlation_id}`.

5. **[Distributed Locks]**
   - **Link**: Pass `trace_id` in lock requests to avoid deadlocks in distributed systems.

---

## **9. Tools & Libraries**
| Tool/Library               | Language/Framework       | Key Features                                  |
|----------------------------|--------------------------|-----------------------------------------------|
| **OpenTelemetry**          | Multi-language           | Standard SDKs, auto-instrumentation, exporters |
| **Jaeger**                 | Go/Java/Python           | UI, sampling, storage (Cassandra/Elastic)    |
| **Zipkin**                 | Java/Python              | Simpler than Jaeger, HTTP-based storage       |
| **AWS X-Ray**              | AWS Lambda/ECS           | Native AWS integration                        |
| **Datadog APM**            | Multi-language           | APM + distributed tracing in one dashboard    |
| **Lightstep**              | Multi-language           | Advanced sampling, team-based filtering      |

---

## **10. References**
- [W3C Trace Context Spec](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry HTTP Propagation](https://opentelemetry.io/docs/specs/semconv/http/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [AWS X-Ray Docs](https://docs.aws.amazon.com/xray/latest/devguide/welcome.html)