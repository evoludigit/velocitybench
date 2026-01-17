# **[Pattern] Request Tracing Through Execution (RTTE) Reference Guide**

---

## **Overview**
The **Request Tracing Through Execution (RTTE)** pattern ensures end-to-end visibility of a request’s lifecycle by assigning a unique **correlation ID** (often called a **trace ID** or **transaction ID**) that propagates across all system components. This enables:
- **Debugging**: Quickly identify a user’s request flow by tracing logs, calls, and errors.
- **Performance Analysis**: Measure latency and bottlenecks across microservices or distributed systems.
- **Data Correlation**: Link related events (e.g., API calls, DB queries, cache hits/misses) to a single user action.

RTTE is critical for **distributed systems**, **event-driven architectures**, and **multi-step workflows** (e.g., order processing, user authentication).

---

## **Core Concepts**
| Term               | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Correlation ID** | A globally unique identifier (e.g., UUID, snowflake ID) tied to a single request.               |
| **Trace ID**       | Synonymous with correlation ID; sometimes split into `trace_id` + `span_id` (for sub-requests).|
| **Span**           | A unit of work (e.g., API call, DB query) annotated with metadata (timestamps, duration).     |
| **Span Context**   | Carries the trace ID, span ID, and other tracing metadata between services.                    |
| **Sampling**       | Techniques (e.g., probabilistic, trace-based) to reduce tracing overhead.                      |
| **Injector/Extractor** | Methods to add/remove trace context (e.g., HTTP headers, message headers, cookies).          |

---

## **Implementation Details**
### **1. Correlation ID Generation**
- **Format**: Use UUIDs (`123e4567-e89b-12d3-a456-426614174000`), snowflake IDs, or custom hex/numeric IDs.
- **Guidelines**:
  - **Uniqueness**: Avoid collisions (use distributed ID generators like Snowflake or UUIDv4).
  - **Length**: Balance readability and header limits (e.g., 32 chars for UUIDs).
  - **Immutability**: Do not regenerate for the same request.

**Example (Pseudocode):**
```python
import uuid
correlation_id = str(uuid.uuid4())
```

### **2. Propagation Mechanisms**
Attach the correlation ID to:
- **HTTP Headers**: `X-Correlation-ID`, `traceparent` (W3C Trace Context).
  ```http
  GET /api/users HTTP/1.1
  Host: example.com
  X-Correlation-ID: abc123-xyz456
  ```
- **Message Headers**: Kafka, RabbitMQ, or gRPC metadata.
- **Database Context**: Pass via connection strings or context binding (e.g., PgBouncer).
- **Cookies**: For browser-based tracing (avoid security risks).

### **3. Tracing Instrumentation**
Inject the correlation ID into:
- **API Gateways**: Automatically propagate via headers.
- **Service Calls**: Extract headers in downstream calls (e.g., `nextjs` middleware).
- **Databases**: Use connection context (e.g., PostgreSQL `pg_current_wal_lsn`).
- **Caches**: Tag cache keys (e.g., `cache_key:request_id:*`).

**Example (Node.js - Express Middleware):**
```javascript
app.use((req, res, next) => {
  req.correlationId = req.headers['x-correlation-id'] || uuid();
  next();
});
```

### **4. Span Creation & Context**
Track spans for:
- Incoming/outgoing HTTP calls.
- Database queries.
- Background jobs/async tasks.
- External API calls (e.g., payment processors).

**Example (OpenTelemetry Span):**
```javascript
const { trace } = require('@opentelemetry/api');
const tracer = trace.getTracer('myApp');

const span = tracer.startSpan('fetchUser', {
  context: trace.setSpanInContext(activeSpan?.context(), {
    traceId: correlationId,
    spanId: uuid(),
  }),
});
```

### **5. Sampling Strategies**
To avoid performance overhead:
- **Probabilistic Sampling**: Trace a subset of requests (e.g., 1%).
- **Trace-Based Sampling**: Trace child spans if the parent is sampled.
- **Head-Based Sampling**: Decide at the gateway (reduces latency).

**Example (OpenTelemetry Sampling):**
```javascript
const sampler = new AlwaysOnSampler();
const tracer = new TracerProvider().register({
  sampler,
});
```

### **6. Storage & Visualization**
- **Logs**: Append `correlation_id` to log entries (e.g., `logger.info({ correlation_id }, 'User action')`).
- **APM Tools**: Export to Jaeger, Zipkin, or OpenTelemetry Collector.
- **Dashboards**: Use Grafana or custom tools to link traces.

**Log Format (JSON):**
```json
{
  "timestamp": "2023-10-15T12:00:00Z",
  "level": "INFO",
  "correlation_id": "abc123",
  "message": "Processing order",
  "service": "order-service"
}
```

---

## **Schema Reference**
| Field               | Type     | Description                                                                 |
|---------------------|----------|-----------------------------------------------------------------------------|
| `correlation_id`    | String   | Unique identifier for the request (e.g., UUID).                           |
| `trace_id`          | String   | Global trace identifier (aligns with W3C Trace Context).                    |
| `span_id`           | String   | Unique identifier for a span (child of trace).                             |
| `parent_span_id`    | String   | ID of the parent span (for hierarchical traces).                           |
| `service_name`      | String   | Name of the service generating the span (e.g., `order-service`).           |
| `operation_name`    | String   | Type of operation (e.g., `GET /users`, `saveOrder`).                        |
| `timestamp`         | ISO8601  | When the span started/ended.                                               |
| `duration_ns`       | Integer  | Span duration in nanoseconds.                                               |
| `attributes`        | Object   | Key-value pairs (e.g., `user_id: "123"`, `status: "200"`).                  |
| `status`            | Enum     | `UNSET`, `OK`, `ERROR` (e.g., `status: "ERROR"`, `error.message: "DB down"`). |

**Example Trace ( JSON ):**
```json
{
  "trace_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
  "spans": [
    {
      "span_id": "x1y2z3",
      "name": "GET /api/users",
      "timestamp": "2023-10-15T12:00:00Z",
      "duration_ns": 5000000,
      "attributes": {
        "http.method": "GET",
        "http.url": "/api/users",
        "user_id": "42"
      },
      "status": "OK"
    },
    {
      "span_id": "x2y3z4",
      "name": "db.query",
      "timestamp": "2023-10-15T12:00:01Z",
      "duration_ns": 1000000,
      "attributes": {
        "db.operation": "SELECT",
        "db.collection": "users"
      },
      "status": "OK"
    }
  ]
}
```

---

## **Query Examples**
### **1. Filter Logs by Correlation ID**
**Tool**: ELK Stack (Elasticsearch + Kibana)
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "correlation_id": "abc123" } }
      ]
    }
  }
}
```

**Tool**: Datadog (Log Search):
```
correlation_id: "abc123" level: ERROR
```

### **2. Trace Latency in APM**
**Tool**: Jaeger Query:
```
service:order-service trace_id:abc123
```
**Tool**: OpenTelemetry Collector (Export to Prometheus):
```yaml
metrics:
  receivers:
    otlp:
      protocols:
        grpc:
        http:
  processors:
    batch:
  exporters:
    prometheus:
      endpoint: "0.0.0.0:8889"
```

### **3. Identify Slow Spans**
**Tool**: Grafana Dashboard (PromQL):
```
sum(rate(otel SpanDurationSum[5m])) by (span_name)
  / sum(rate(otel SpanCount[5m])) by (span_name)
  > 1000 # Spans >1s
```

---

## **Related Patterns**
| Pattern                          | Purpose                                                                 | When to Use                                                                 |
|----------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Circuit Breaker**              | Prevent cascading failures by limiting calls to unhealthy services.      | Distributed systems with high latency/unreliable dependencies.            |
| **Bulkhead Pattern**             | Isolate failures to prevent resource exhaustion.                        | High-throughput services with shared dependencies (e.g., DB connections). |
| **Saga Pattern**                 | Manage distributed transactions via a series of local transactions.     | Microservices with ACID compliance needs (e.g., payment processing).       |
| **Rate Limiting**                | Control request volume to avoid overload.                              | Public APIs or to prevent abuse.                                           |
| **Distributed Locks**            | Synchronize access to shared resources.                                 | Concurrent modifications to critical data.                                |
| **Event Sourcing**               | Store state changes as immutable events.                                | Audit trails or replayable workflows.                                       |

---

## **Best Practices**
1. **Minimize Overhead**:
   - Use sampling to reduce trace volume.
   - Avoid heavy serialization (e.g., JSON) in high-throughput systems.
2. **Security**:
   - Never expose correlation IDs in URLs or public logs.
   - Validate headers to prevent header injection attacks.
3. **Observability**:
   - Correlate logs, metrics, and traces (e.g., link spans to metrics).
   - Use structured logging (e.g., OpenTelemetry’s `attributes`).
4. **Backward Compatibility**:
   - Support both new and legacy systems (e.g., fall back to random IDs if headers are missing).
5. **Tooling**:
   - Integrate with OpenTelemetry, Jaeger, or Zipkin for visualization.
   - Use standards like W3C Trace Context where possible.

---

## **Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                                                 | **Fix**                                                                     |
|---------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Hardcoded IDs**               | Manual ID generation leads to collisions or inconsistencies.               | Use distributed ID generators (e.g., Snowflake, UUID).                      |
| **No Propagation**              | Correlation IDs are lost between services.                                  | Automate header forwarding (e.g., via API gateways).                      |
| **Over-Tracing**                | Every request is traced, causing performance degradation.                  | Implement sampling (e.g., 1% of requests).                                 |
| **Ignoring Spans**              | Critical operations are untracked.                                          | Instrument all external calls (DB, APIs, caches).                          |
| **Inconsistent Formats**        | Mixing UUIDs, strings, and numeric IDs increases complexity.                | Standardize on one format (e.g., UUIDv4).                                  |

---
**References**:
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry API](https://opentelemetry.io/docs/specs/otel/specification/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/latest/)