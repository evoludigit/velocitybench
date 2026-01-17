**[Pattern] Profiling Integration Reference Guide**

---

### **1. Overview**
The **Profiling Integration** pattern enables seamless integration of profiling tools, observability frameworks, or analytics platforms into applications, microservices, or infrastructure. It provides standardized mechanisms to collect, aggregate, and analyze runtime data (e.g., performance metrics, trace logs, telemetry) from distributed systems. This pattern ensures interoperability between profiling tools (e.g., PPROF, X-Ray, Jaeger) and monitoring systems (e.g., Prometheus, OpenTelemetry, Datadog) while maintaining minimal overhead and flexibility for extensibility.

Key use cases include:
- **Performance monitoring** (latency, throughput, resource usage).
- **Debugging and trace analysis** (distributed request flows).
- **Compliance and security auditing** (anomaly detection).
- **Automated scaling and optimization** (based on real-time metrics).

---

### **2. Schema Reference**

| **Component**               | **Description**                                                                                                                                                                                                                                                                 | **Required Attributes**                                                                                                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| **Profiling Endpoint**      | HTTP/gRPC endpoint where profiling data is ingested. Supports structured logs, metrics, and traces.                                                                                                                                                                 | - `endpoint_url` (string)<br>- `protocol` (`http`, `grpc`, or `udp`)<br>- `auth_token` (optional, string)                        |
| **Trace Context**           | Header/query parameters for correlating requests across services (e.g., `trace_id`, `span_id`). Must adhere to [W3C Trace Context](https://www.w3.org/TR/trace-context/).                                                                                           | - `traceparent` (required, string)<br>- `tracestate` (optional, string)                                                        |
| **Metrics Schema**          | Standardized key-value pairs for performance metrics (e.g., `cpu_usage`, `request_latency`). Uses [OpenTelemetry Semantic Conventions](https://github.com/open-telemetry/semantic-conventions).                                                                       | - `metric_name` (string)<br>- `metric_type` (`gauge`, `counter`, `histogram`)<br>- `value` (numeric)<br>- `tags` (optional, dict) |
| **Log Entry**               | Structured log format with severity, context, and timestamps.                                                                                                                                                                                                           | - `timestamp` (ISO 8601)<br>- `level` (`info`, `warn`, `error`)<br>- `message` (string)<br>- `context` (optional, dict)           |
| **Trace Span**              | Representation of a single operation (e.g., HTTP request, database query) with start/end timestamps, attributes, and nested spans.                                                                                                                                         | - `span_id` (hex string)<br>- `parent_span_id` (optional)<br>- `operation_name` (string)<br>- `start_time`/`end_time` (ISO 8601) |
| **Instrumentation Library** | SDK or agent (e.g., OpenTelemetry Python SDK, AWS X-Ray SDK) that collects and exports data to the profiling endpoint.                                                                                                                                               | - `language` (string)<br>- `version` (string)<br>- `exporter` (`otlp`, `zipkin`, `custom`)                                             |
| **Processor**               | Optional middleware (e.g., sampling, filtering, enrichment) applied before data is sent to the endpoint.                                                                                                                                                                    | - `type` (`sampler`, `filter`, `annotator`)<br>- `config` (JSON string)                                                          |

---

### **3. Implementation Details**

#### **3.1 Core Architecture**
Profiling integration follows a **producer-consumer** model:
1. **Producers**: Applications/services instrumented with profiling libraries (e.g., OpenTelemetry auto-instrumentation for HTTP servers).
2. **Consumers**: Backend services (e.g., Prometheus, Jaeger) or aggregation platforms (e.g., Grafana, Lumigo).
3. **Exporters**: Middleware (e.g., `otlpgrpc`, `otlphttp`) that serialize and send data to endpoints.

![Architecture Diagram](https://miro.medium.com/max/1400/1*XxXxXxXxXxXxXxXxXxXxX.png)
*Example: OpenTelemetry Pipeline*

---

#### **3.2 Key Components**
| **Component**          | **Purpose**                                                                                                                                                                                                                     | **Example Implementations**                                                                                                   |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| **Auto-Instrumentation** | Automatically injects tracing/logging into application code (e.g., HTTP handlers, database queries).                                                                                                                | OpenTelemetry auto-instrumentation for Java, Go, or Node.js.                                                                        |
| **Manual Instrumentation** | Developer-defined spans/logs for custom business logic.                                                                                                                                                              | `otel.tracer.start_span("process_order")` in Python.                                                                               |
| **Samplers**           | Controls the volume of traces logged (e.g., probabilistic, always-on, or adaptive sampling).                                                                                                                        | `AlwaysOnSampler`, `ParentBasedSampler`.                                                                                         |
| **Batching**           | Aggregates small metric/log entries to reduce overhead.                                                                                                                                                                | OpenTelemetry `BatchSpanProcessor`.                                                                                            |
| **Headers Propagation** | Ensures trace context is carried across service boundaries (e.g., via `traceparent` header).                                                                                                                        | W3C Trace Context format: `traceparent=00-<trace_id>-<parent_id>-01`.                                                            |

---

#### **3.3 Supported Protocols**
| **Protocol** | **Use Case**                          | **Schema Example**                                                                                     |
|--------------|---------------------------------------|---------------------------------------------------------------------------------------------------------|
| **OTLP (gRPC/HTTP)** | High-performance telemetry export.   | `POST /v1/traces { "resource_spans": [...] }`                                                       |
| **Zipkin**   | Legacy tracing format.               | `span_id` + `parent_id` + `timestamp` in JSON.                                                       |
| **Custom UDP** | Lightweight log forwarding.          | `{ "log": { "timestamp": "2023-01-01T00:00:00Z", "level": "info", ... } }` via UDP port `4242`. |

---

#### **3.4 Error Handling**
| **Scenario**               | **Response**                                                                                                                                                                                                 | **Retry Policy**                                                                                                                                 |
|----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Endpoint Unreachable**   | Queue locally (buffer) and retry with exponential backoff.                                                                                                                                                     | Max retries: 5, initial delay: 1s, max delay: 30s.                                                                                          |
| **Authentication Failure** | Log error and stop exporting until credentials are refreshed.                                                                                                                                               | No retry; trigger alert.                                                                                                                 |
| **Schema Validation Fail** | Drop invalid entries and continue processing.                                                                                                                                                              | None.                                                                                                                                          |
| **Quota Exceeded**        | Sample a subset of traces or batch smaller payloads.                                                                                                                                                          | Reduce batch size or wait for throttling to lift.                                                                                           |

---

### **4. Query Examples**

#### **4.1 Prometheus Metrics Query**
```promql
# Latency P99 (99th percentile) for /api/users endpoint
histogram_quantile(0.99, sum(rate(http_request_duration_microseconds_bucket{route="/api/users"}[5m])) by (le))
```
**Output**:
```
120.5ms
```

#### **4.2 Jaeger Trace Query**
```json
{
  "query": {
    "end_time": "2023-10-01T12:00:00Z",
    "limit": 10,
    "filters": {
      "service_names": ["order-service"],
      "operation_names": ["/checkout"]
    }
  }
}
```
**Response**:
```json
{
  "data": [
    {
      "trace_id": "b9a9e2e5463d596f",
      "spans": [
        { "operation_name": "checkout", "start_time": "2023-10-01T11:59:00Z", ... }
      ]
    }
  ]
}
```

#### **4.3 OpenTelemetry Logs Query (Loki)**
```logql
# Errors in payment service for the last 24 hours
{job="payment-service"} | json | logmsg ~ "payment failed" | count_over_time([24h])
```
**Output**:
```
42 errors
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **Use Case Example**                                                                                                        |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------|
| **[Distributed Tracing]**  | Correlates requests across services using trace IDs.                                                                                                                                                           | Debugging a cross-service transaction.                                                                                        |
| **[Metrics Aggregation]**  | Consolidates metrics from multiple sources (e.g., Prometheus + custom metrics).                                                                                                                               | Dashboards showing system-wide performance.                                                                                    |
| **[Sampling]**            | Reduces telemetry volume by selectively exporting traces/logs.                                                                                                                                                   | High-throughput systems with limited storage.                                                                                     |
| **[Observability Pipeline]** | Orchestrates data flow from instrumentation to storage (e.g., Fluentd → Elasticsearch).                                                                                                                       | Centralized logging for security compliance.                                                                                  |
| **[Canary Analysis]**      | Gradually rolls out profiling to a subset of users.                                                                                                                                                           | Testing new metrics before full deployment.                                                                                     |

---
**Next Steps**:
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [W3C Trace Context Spec](https://www.w3.org/TR/trace-context/)
- [Prometheus Metrics](https://prometheus.io/docs/practices/naming/)