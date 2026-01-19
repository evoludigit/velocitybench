# **[Pattern] Tracing Best Practices – Reference Guide**

---

## **Overview**
Tracing provides end-to-end visibility into request flows across distributed systems, ensuring observability of latency, errors, and dependencies. This reference outlines best practices for implementing, configuring, and optimizing traces to maximize operational efficiency and troubleshooting accuracy.

### **Key Benefits**
- **Latency Analysis:** Identify bottlenecks in microservices or APIs.
- **Dependency Mapping:** Visualize cross-service workflows and data flow.
- **Error Correlation:** Link errors to their root causes across services.
- **Performance Optimization:** Spot inefficient components or misconfigurations.

---

## **Schema Reference**
Below are standard fields to include in traces for compatibility with observability tools (e.g., Jaeger, OpenTelemetry, Datadog).

| **Field**               | **Type**       | **Description**                                                                                     | **Example Values**                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------|
| `trace_id`              | String (UUID)  | Globally unique identifier for the entire trace.                                                  | `00000000000000000000000000000001`     |
| `span_id`               | String (UUID)  | Unique identifier for individual operations within a trace.                                         | `11111111111111111111111111111111`     |
| `parent_span_id`        | String (UUID)  | Identifies the parent span (if applicable).                                                        | `22222222222222222222222222222222`     |
| `operation_name`        | String         | Descriptive name of the operation (e.g., `GET /api/users`).                                       | `authenticate_user`                     |
| `service_name`          | String         | Name of the service emitting the trace.                                                            | `auth-service`                          |
| `resource_name`         | String         | Path/endpoint or resource being accessed (e.g., database query).                                  | `db.query_users`                       |
| `start_time`            | Timestamp      | When the span began (ISO 8601 format).                                                              | `2023-10-01T12:00:00.123Z`             |
| `end_time`              | Timestamp      | When the span completed.                                                                           | `2023-10-01T12:00:00.456Z`             |
| `duration`              | Float (ms)     | Duration of the span in milliseconds.                                                             | `333.33`                                |
| `status`                | String         | Span outcome (e.g., `"OK"`, `"ERROR"`).                                                            | `"ERROR"`                               |
| `status_code`           | Integer        | HTTP status code (if applicable) or custom error code.                                             | `500`                                    |
| `attributes`            | Key-Value Pairs| Metadata (e.g., `user_id`, `region`, `http.method`).                                               | `{ "user_id": "123", "db": "mongo" }`   |
| `logs`                  | Array          | Structured logs (timestamped key-value pairs for debugging).                                       | `[{ "timestamp": "2023-10-01T12:00:00Z", "key": "debug", "value": "User not found" }]` |
| `tags`                  | Key-Value Pairs| Predefined labels for filtering (e.g., `environment: production`).                                 | `{ "env": "prod", "team": "backend" }`  |
| `links`                 | Array          | References to related spans (e.g., child spans, dependencies).                                     | `[{ "type": "CHILD_OF", "trace_id": "..." }]` |

---

## **Implementation Details**
### **1. Instrumentation Best Practices**
#### **A. Scope of Traces**
- **Include all critical paths:** Network calls, database queries, external APIs, and user-facing operations.
- **Exclude noisy data:** Avoid tracing internal loops (e.g., object serialization) unless critical.
- **Sample strategically:**
  - **100% sampling** for production errors or critical paths.
  - **Random sampling (e.g., 1–10%)** for high-throughput services to balance load and visibility.

#### **B. Span Naming Conventions**
- Use **descriptive, consistent names** (e.g., `POST /api/orders` instead of `rest_call`).
- Include **service context** (e.g., `order-service.db.query`).
- Avoid **dynamic names** (e.g., `db.$collection.find()`), as they reduce queryability.

#### **C. Error Handling**
- **Automatically capture errors:** Include `status: "ERROR"` and `attributes.error.message` for exceptions.
- **Correlate with logs:** Add `attributes.log.correlation_id` to link traces with logs (e.g., ELK, Splunk).

#### **D. Context Propagation**
- **Pass traces across services:** Use headers (e.g., `traceparent`, `x-request-id`) for HTTP calls.
  Example HTTP header:
  ```
  traceparent: 00-0af7651916cd43d2b13486da41e73e9a-00f067aa0ba902b7-01
  ```
- **For gRPC:** Use `binary` or `text` format for `trace-context` headers.

---

### **2. Configuration**
#### **A. Sampling**
- **Static sampling:** Set a fixed rate (e.g., `1%` for all traces).
- **Dynamic sampling:** Adjust based on:
  - **User impact** (e.g., trace slow requests to 100%).
  - **Error rates** (e.g., trace errors to 100%).
- **Tools:** OpenTelemetry’s [`Sampler`](https://opentelemetry.io/docs/specs/semconv/dynamic-sampling/) or Datadog’s [Agent Rules](https://docs.datadoghq.com/tracing/guide/configure-sampling/).

#### **B. Instrumentation Libraries**
| **Language/Platform** | **Recommended Libraries**                          | **Notes**                                  |
|-----------------------|----------------------------------------------------|--------------------------------------------|
| Node.js               | `@opentelemetry/auto-instrumentation-node`          | Supports Express, Fastify, Kafka.         |
| Python                | `opentelemetry-instrumentation-*` (e.g., ` requests`) | Auto-instrument HTTP clients.             |
| Java                  | `opentelemetry-java-contrib`                       | Supports Spring Boot, Micrometer.         |
| Go                    | `go.opentelemetry.io/contrib/instrumentation/net/http` | Wraps `http.Server`/`http.Client`.       |
| .NET                  | `OpenTelemetry.Instrumentation.AspNetCore`          | Middleware for ASP.NET Core.              |
| Kubernetes            | `OpenTelemetry Operator`                           | Auto-instruments pods.                    |

#### **C. Exporter Configuration**
Choose exporters based on your observability stack:

| **Exporter**          | **Use Case**                          | **Configuration Example**                          |
|-----------------------|---------------------------------------|----------------------------------------------------|
| **Jaeger**            | Local debugging/tracing               | `OTEL_EXPORTER_JAEGER_ENDPOINT=http://jaeger:14268` |
| **Zipkin**            | Legacy systems                        | `OTEL_EXPORTER_ZIPKIN_ENDPOINT=http://zipkin:9411` |
| **OTLP (gRPC/HTTP)**  | Cloud-native (Datadog, AWS X-Ray)    | `OTEL_EXPORTER_OTLP_ENDPOINT=http://otlp:4318`      |
| **Prometheus**        | Metrics + traces                      | Enable `OTEL_METRICS_EXPORTER=prometheus`         |

---
### **3. Query Examples**
#### **A. Filtering Traces by Service**
**Query (Jaeger UI):**
```
service = "auth-service" AND duration > 100ms
```
**Query (OpenTelemetry Query Language - OTQL):**
```sql
SELECT * FROM traces
WHERE resource.attributes["service.name"] = "auth-service"
AND duration > 100ms
LIMIT 100
```

#### **B. Correlating Errors**
**Query (Datadog):**
```
trace("service:auth-service error:auth_failed").summary
```
**Query (Grafana Tempo + PromQL):**
```promql
rate(
  trace{service="auth-service", status!="OK"}
  [5m]
)
```

#### **C. Dependency Mapping**
**Query (OpenTelemetry Collector):**
```yaml
# Templates/processors to extract dependencies
span_processors:
  batch:
    timeout: 10s
    send_batch_size: 100
```

#### **D. Latency Percentiles**
**Query (Prometheus + Tempo):**
```promql
histogram_quantile(0.95,
  sum(rate(trace{service="order-service"}[5m]))
  by (le)
)
```

---

## **Related Patterns**
1. **[Distributed Tracing]** – Core concept behind this pattern. See [OpenTelemetry Docs](https://opentelemetry.io/docs/concepts/).
2. **[Metrics + Tracing Hybrid Observability]** – Combine traces with metrics (e.g., Prometheus + OpenTelemetry).
3. **[Structured Logging]** – Correlate traces with logs using `correlation_id`.
4. **[Rate Limiting]** – Use traces to throttle high-latency requests (e.g., via `OTEL_ATTR_REQUEST_RATE_LIMIT`).
5. **[Chaos Engineering]** – Inject errors/failures to test trace resilience.

---
## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------|
| **Trace explosion**                   | Use adaptive sampling or discard internal loops.                               |
| **Header propagation failures**       | Validate headers in service boundaries (e.g., middleware checks).              |
| **Noisy spans**                       | Limit span creation to critical paths (e.g., `db.query` instead of `db._do_query`). |
| **Missing context**                   | Enforce trace headers in API gateways or service meshes (e.g., Istio).        |
| **Vendor lock-in**                    | Use OpenTelemetry as an abstraction layer.                                    |

---
## **Further Reading**
- [OpenTelemetry Tracing Docs](https://opentelemetry.io/docs/instrumentation/)
- [Jaeger Tracing Guide](https://www.jaegertracing.io/docs/latest/)
- [Datadog Trace Sampling](https://docs.datadoghq.com/tracing/guide/configure-sampling/)
- [AWS X-Ray Best Practices](https://docs.aws.amazon.com/xray/latest/devguide/xray-best-practices.html)