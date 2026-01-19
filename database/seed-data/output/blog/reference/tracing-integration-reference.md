# **[Pattern] Tracing Integration: Reference Guide**

---

## **Overview**
The **Tracing Integration** pattern enables distributed applications to capture, analyze, and correlate request flows across microservices, containers, or cloud services. By embedding structured trace data (e.g., trace IDs, spans, and metadata), it provides end-to-end observability into latency, bottlenecks, and dependencies. This pattern leverages standardized instrumentation libraries (e.g., OpenTelemetry, Jaeger, or Zipkin) to automatically collect telemetry without disrupting business logic.

Key benefits include:
- **Debugging efficiency**: Quick identification of failure paths in distributed systems.
- **Performance optimization**: Pinpointing slow services or network hops.
- **Compliance**: Aligning with observability best practices (e.g., DORA metrics).
- **Cost savings**: Reducing manual incident investigation time.

---

## **Implementation Details**

### **1. Core Components**
| **Component**          | **Purpose**                                                                 | **Example Technologies**                                                                 |
|------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| **Trace ID**           | Globally unique identifier for a single request flow.                       | UUID or 64-bit integer (e.g., `0x1234abcd5678ef01`).                                      |
| **Span**               | Represents a single operation (e.g., HTTP call, DB query) with timestamps. | Attributes (key-value pairs), start/end time, parent span reference.                       |
| **Span Context**       | Metadata passed between services (e.g., parent span ID, trace flags).        | Propagated via headers or libraries (e.g., `traceparent` header in W3C Trace Context).   |
| **Sampler**            | Controls trace volume (e.g., always-on, probabilistic, or adaptive).        | OpenTelemetry’s `HeadSampler` or Jaeger’s `ConstSampler`.                                 |
| **Span Processor**     | Modifies/filters spans before export (e.g., batching, anonymization).      | OpenTelemetry’s `BatchSpanProcessor` or custom filters.                                   |
| **Trace Exporter**     | Sends spans to a backend (e.g., OTLP, Jaeger, Zipkin).                     | OpenTelemetry’s `OTLPExporter` or Zipkin’s HTTP endpoint (`http://zipkin:9411/api/v2/spans`).|
| **Backend**            | Stores and visualizes traces (e.g., dashboards, alerting).                 | Jaeger UI, Grafana with Tempo, or Lightstep.                                              |

---

### **2. Trace Propagation**
Spans must propagate context between services via:
- **HTTP Headers**: Standardized by [W3C Trace Context](https://www.w3.org/TR/trace-context/).
  ```http
  GET /api/users HTTP/1.1
  Traceparent: 00-1234abcd5678ef01-1234abcd5678ef01-01
  Tracesampled: 1
  ```
- **Custom Headers**: Service-specific (e.g., `X-B3-TraceId` in Zipkin).
- **gRPC Metadata**: Key-value pairs (e.g., `traceparent` in gRPC headers).

**Library Support**:
- **OpenTelemetry**: Auto-propagates via `TextMapPropagator`.
- **Zipkin/Jaeger**: Uses `B3 Propagation`.

---

### **3. Instrumentation Libraries**
| **Library**            | **Language**       | **Key Features**                                                                 |
|------------------------|--------------------|----------------------------------------------------------------------------------|
| OpenTelemetry SDK      | Multi-lang         | vendor-agnostic, pluggable exporters, auto-instrumentation for frameworks (e.g., Spring Boot, Django). |
| Jaeger Client          | Go, Java, Python   | Low-level control, supports custom sampling.                                     |
| Zipkin Auto-Instrument | Java, Node.js      | Generates spans for HTTP calls, DB queries, and caches.                          |
| AWS X-Ray             | Multi-lang         | AWS-native traces, integrates with CloudWatch.                                  |

**Example (OpenTelemetry Python):**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor

# Configure tracer
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Get tracer
tracer = trace.get_tracer(__name__)

# Create a span
with tracer.start_as_current_span("fetch_user") as span:
    # Simulate work
    span.set_attribute("user.id", "123")
    print(f"Span ID: {span.span_context.span_id}")
```

---

### **4. Sampling Strategies**
| **Strategy**           | **Description**                                      | **Use Case**                                  |
|------------------------|------------------------------------------------------|-----------------------------------------------|
| **Always-on**          | Traces all requests.                                | Development or low-volume production.         |
| **Probabilistic**      | Samples *N*% of traces (e.g., 1%).                  | High-volume systems to balance load.          |
| **Adaptive**           | Samples based on latency/priority (e.g., slow paths). | Detecting anomalies in production.            |
| **Traceparent Header** | Uses `TraceState` to override client-side sampling.  | Cross-service consistency.                    |

**Configuring OpenTelemetry Sampling:**
```python
from opentelemetry.sdk.trace import SamplingSettings

# 1% sampling
sampler = SamplingSettings(1.0, 1000)  # 1% of first 1000 traces
processor = BatchSpanProcessor(OTLPExporter(endpoint="http://otlp-collector:4317"))
provider.add_span_processor(processor)
```

---

### **5. Querying Traces**
#### **Schema Reference**
| **Field**               | **Type**      | **Description**                                                                 |
|-------------------------|---------------|---------------------------------------------------------------------------------|
| `trace_id`              | string (hex)  | Unique identifier for the entire trace.                                        |
| `span_id`               | string (hex)  | Unique identifier for a single span within the trace.                           |
| `name`                  | string        | Human-readable operation name (e.g., `GET /users`).                            |
| `start_time`            | timestamp     | When the span began (ISO 8601).                                                  |
| `end_time`              | timestamp     | When the span ended.                                                           |
| `duration`              | duration      | Elapsed time (e.g., `123.45ms`).                                                 |
| `attributes`            | key-value     | Metadata (e.g., `http.method=GET`, `db.operation=query`).                       |
| `status`                | enum          | `"OK"`, `"ERROR"`, or custom (e.g., `"DEGRADED"`).                             |
| `resource`              | object        | Service metadata (e.g., `service.name`, `cloud.region`).                         |

---

#### **Query Examples**
##### **1. List Traces by Service**
```sql
-- Jaeger SQL (PostgreSQL)
SELECT trace_id, start_time
FROM spans
WHERE resource.attributes -> 'service.name' = 'auth-service'
ORDER BY start_time DESC
LIMIT 10;
```

##### **2. Find Slow Spans (Top 5)**
```bash
# OpenTelemetry Query (OTLP)
curl http://otlp-collector:4318/v1/traces \
  -H "Accept: application/json" \
  | jq 'map(select(.resource.attributes."duration" > 500))' | head -5
```

##### **3. Filter by Error Status**
```groovy
// Jaeger UI Query (JavaScript-like pseudocode)
var errors = traces.filter(t =>
  t.spans.some(s => s.status.code == "ERROR")
);
```

##### **4. Correlation with Logs**
```sql
-- Correlate with ELK Stack
SELECT *
FROM logs
WHERE log.message LIKE '%db.connection%'
AND log.headers ->> 'traceparent' IN (
  SELECT DISTINCT attributes ->> 'traceparent'
  FROM spans
  WHERE resource.service.name = 'database'
);
```

##### **5. Service Dependency Graph**
```bash
# Export to Graphviz (via Jaeger)
jaeger query --query 'dependencies(span.service.name, span.operation.name)'
```

---

### **6. Common Pitfalls & Mitigations**
| **Pitfall**                     | **Root Cause**                          | **Solution**                                                                 |
|----------------------------------|-----------------------------------------|------------------------------------------------------------------------------|
| **High cardinality**             | Too many unique attributes (e.g., DB query plans). | Use histograms or aggregates (e.g., `db.operation:query`, not `db.query.plan`). |
| **Sampling gaps**                | Inconsistent sampling across services.   | Standardize on OpenTelemetry’s probabilistic sampler.                          |
| **Header propagation errors**    | Missing/invalid `traceparent` headers.  | Validate headers in logs (e.g., `if (!req.headers.traceparent) { reject() }`). |
| **Cold starts in serverless**    | Traces delayed due to initialization.   | Pre-warm instrumentation (e.g., Java’s `@PostConstruct`).                     |
| **Storage costs**                | Unbounded trace retention.              | Implement [retention policies](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/trace/sdk.md#retention) or sampling. |

---

## **Related Patterns**
1. **[Metrics Integration](metrics-integration.md)**
   - *Why?* Traces complement metrics (e.g., latency percentiles) for deeper analysis.
   - *Example:* Pair `p99 latency` from metrics with slow traces.

2. **[Distributed Logging](distributed-logging.md)**
   - *Why?* Logs + traces provide rich context (e.g., `log Correlation-ID: <trace_id>`).
   - *Tool:* [Correlate logs with OpenTelemetry](https://opentelemetry.io/docs/specs/otel/logs/data-model/).

3. **[Circuit Breakers](circuit-breaker.md)**
   - *Why?* Traces help diagnose failures when circuit breakers trip.
   - *Example:* Trace a `CircuitBreakerClosed` event in your backend.

4. **[Self-Healing Systems](self-healing.md)**
   - *Why?* Traces inform auto-remediation (e.g., "If `span.duration > 2s`, scale up").
   - *Tool:* [Prometheus + OpenTelemetry](https://github.com/open-telemetry/opentelemetry-prometheus-exporter).

5. **[Observability as Code](obs-as-code.md)**
   - *Why?* Standardize tracing configs (e.g., sampling rules) in Git.
   - *Example:* [OpenTelemetry Collector Config](https://github.com/open-telemetry/opentelemetry-collector-config).

---

## **Further Reading**
- [OpenTelemetry Spec](https://github.com/open-telemetry/specification)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/latest/)
- [Zipkin Guide](https://zipkin.io/overview/)