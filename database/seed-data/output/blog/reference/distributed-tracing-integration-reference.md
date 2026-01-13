**[Pattern] Distributed Tracing Integration Reference Guide**
*OpenTelemetry/Jaeger Patterns for Observability*

---

### **1. Overview**
Distributed tracing integrates instrumentation across microservices, containers, or cloud services to track requests as they traverse distributed systems. This pattern leverages **OpenTelemetry** (an industry-standard SDK) and **Jaeger** (a popular tracing backend) to collect telemetry data (traces, metrics, logs), visualize latency, and diagnose performance bottlenecks. By attaching trace IDs to requests, developers can correlate transactions end-to-end, identify dependencies, and troubleshoot failures in real time. This guide covers core concepts, schema references, query examples, and synergies with related patterns.

---

### **2. Key Concepts**
#### **Core Components**
| **Component**       | **Description**                                                                                                                                                                                                                                                                 | **Tools Supported**                     |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **Trace**           | A sequence of spans recording a single logical operation (e.g., user request) across services. Each trace has a unique **trace ID**.                                                                                                                                        | OpenTelemetry, Jaeger, Zipkin           |
| **Span**            | A single unit of work (e.g., database query, RPC call) with metadata like timestamps, attributes, and event logs. Spans are nested hierarchically under a trace.                                                                                                  | OpenTelemetry, Jaeger                    |
| **OpenTelemetry SDK**| Language-specific libraries to generate/collect telemetry. Supports auto-instrumentation (e.g., HTTP clients) or manual instrumentation (custom spans).                                                                                                                    | Python, Java, C++, Go, Node.js           |
| **Collector**       | Centralized service that aggregates traces from SDKs, batches them, and exports to backends (e.g., Jaeger).                                                                                                                                                  | OpenTelemetry Collector, Tempo           |
| **Jaeger UI**       | Web-based interface to explore traces, filter by service, duration, or error spans.                                                                                                                                                                                 | Jaeger (All-In-One, Distributed)         |
| **Sampling**        | Mechanism to limit trace volume (e.g., probabilistic or adaptive sampling). Reduces overhead while preserving critical paths.                                                                                                                                         | OpenTelemetry, Jaeger                    |

#### **Workflow**
1. **Instrumentation**: SDK injects trace context (e.g., headers) into outbound requests.
2. **Propagation**: Context propagates across service boundaries via headers/cookies.
3. **Collection**: Traces are sent to the Collector, which exports them to Jaeger.
4. **Visualization**: Jaeger UI renders traces as dependency graphs or timelines.

---

### **3. Schema Reference**
#### **Trace Structure (JSON)**
```json
{
  "trace_id": "a1b2c3...",  // Unique identifier (128-bit)
  "spans": [
    {
      "span_id": "d4e5f6...",
      "name": "api.getUser",
      "start_time": "2023-10-01T12:00:00Z",
      "end_time": "2023-10-01T12:00:05Z",
      "duration": "5000ns",
      "attributes": {
        "http.method": "GET",
        "user.id": "123"
      },
      "links": [  // Parent/child relationships
        {
          "trace_id": "a1b2c3...",
          "span_id": "g7h8i9...",
          "type": "CHILD_OF"
        }
      ]
    }
  ]
}
```

#### **OpenTelemetry Exporter Config (YAML)**
```yaml
exporters:
  jaeger:
    endpoint: "jaeger-collector:14250"
    tls:
      insecure: true  # Disable for local testing
    sampling:
      decision_wait: 500ms
      sampler_name: "probabilistic"
      sampler_param: 0.1  # 10% of traces sampled
```

#### **Jaeger Query Parameters**
| **Parameter**       | **Description**                                                                                     | **Example**                     |
|---------------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `service`           | Filter traces by service name.                                                                       | `service=auth-service`           |
| `duration`          | Min/max latency (e.g., `duration:[500ms..1000ms]`).                                                   | `duration:[500ms..]`            |
| `tags`              | Filter by span attributes (e.g., `error=true`).                                                     | `tags[error]=true`              |
| `limit`             | Limit results to `N` traces.                                                                         | `limit=100`                     |
| `op`                | Filter by operation name.                                                                           | `op=db.query`                   |

---

### **4. Query Examples**
#### **Exploring Traces in Jaeger UI**
1. **Filter by Service**:
   - Navigate to [Jaeger UI](http://jaeger-ui:16686) → Search bar: `service:payment-service error:true`.
2. **Latency Analysis**:
   - Use the duration filter: `duration:[200ms..]`.
3. **Dependency Graph**:
   - Click "Dependencies" tab to visualize cross-service calls.
4. **Error Correlation**:
   - Search by `tags[error.message]="DB timeout"` to find failed transactions.

#### **OpenTelemetry Collector Pipeline (YAML)**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

processors:
  batch:
    timeout: 1s
    send_batch_size: 1000

exporters:
  jaeger:
    endpoint: "jaeger-collector:14250"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
```

#### **SDK Instrumentation (Python Example)**
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

# Configure tracer
exporter = JaegerExporter(endpoint="http://jaeger-agent:14268/api/traces")
processor = BatchSpanProcessor(exporter)
provider = TracerProvider(span_processors=[processor])
trace.set_tracer_provider(provider)

# Instrument a function
tracer = trace.get_tracer(__name__)
def get_user(user_id):
    with tracer.start_as_current_span("get_user"):
        # Simulate DB call
        span = trace.get_current_span()
        span.set_attribute("db.query", "SELECT * FROM users WHERE id = ?")
```

---

### **5. Implementation Steps**
#### **A. Set Up Jaeger**
1. Deploy Jaeger (Docker example):
   ```bash
   docker run -d -p 16686:16686 -p 14268:14268 jaegertracing/all-in-one:latest
   ```
2. Verify at [http://localhost:16686](http://localhost:16686).

#### **B. Instrument Services**
1. **Auto-Instrumentation**:
   - Use OpenTelemetry’s language auto-instrumentation (e.g., `opentelemetry-auto-instrumentation-node` for Node.js).
2. **Manual Instrumentation**:
   - Add SDK to `requirements.txt`/`pom.xml` (example for Python):
     ```bash
     pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
     ```

#### **C. Configure Collector (Optional)**
1. Deploy OpenTelemetry Collector in Kubernetes or Docker:
   ```yaml
   # Deployment snippet
   env:
     - name: JAEGER_AGENT_HOST
       value: "jaeger-agent"
   ```
2. Ensure exporters match your backend (e.g., `jaeger-thrift` for Thrift protocol).

#### **D. Validate Traces**
1. Trigger a request (e.g., `/api/user/123`).
2. Check Jaeger UI for traces with `service=your-service`.

---

### **6. Common Pitfalls & Mitigations**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|------------------------------------|----------------------------------------|------------------------------------------------------------------------------|
| **High Cardinality**               | Too many unique attributes (e.g., `user.id`). | Use sampling, aggregate rare attributes, or enforce schema validation.      |
| **Context Loss**                   | Missing propagation headers.           | Ensure SDKs set/extract headers (e.g., `traceparent` in HTTP).                |
| **Collector Overload**             | Unbatched high-volume traces.          | Adjust `batch` processor timeout/size or use async exporters.                |
| **Cold Start Latency**             | Jaeger agent initialization delay.     | Pre-warm agents or use distributed mode.                                     |

---

### **7. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **Synergy**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Log Correlation**       | Link traces to logs using `trace_id`/`span_id` in log entries.                                                                                                                                               | Combine Jaeger traces with ELK/Loki for deeper context.                       |
| **Metrics-Based Alerting**| Use OpenTelemetry metrics (e.g., P99 latency) to trigger alerts in Prometheus/Grafana.                                                                                                                 | Correlate high-latency traces with metric spikes.                             |
| **Service Mesh Integration** | Inject OpenTelemetry auto-instrumentation via Istio/Linkerd.                                                                                                                                             | Reduce manual SDK boilerplate; leverage mesh-sidecar tracing.                 |
| **Distributed Logging**   | Forward logs to OpenTelemetry Collector for enrichment with trace context.                                                                                                                               | Centralize logs and traces in a unified dashboard (e.g., Grafana Tempo + Jaeger). |

---

### **8. Further Reading**
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Jaeger Operator for Kubernetes](https://github.com/jaegertracing/jaeger-operator)
- [Sampling Strategies](https://opentelemetry.io/docs/specs/semconv/distributed-tracing/sampling/)
- [Auto-Instrumentation Guides](https://opentelemetry.io/docs/instrumentation/)