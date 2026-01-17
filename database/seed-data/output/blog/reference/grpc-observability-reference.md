# **[Pattern] gRPC Observability Reference Guide**

---

## **Overview**
gRPC Observability is a structured approach to monitoring, tracing, and logging gRPC-based microservices to ensure reliability, performance, and debugging efficiency. This pattern ensures visibility into latency, error rates, traffic patterns, and dependency flows across distributed systems. By implementing standardized telemetry (metrics, logs, traces), teams can detect anomalies early, optimize service performance, and align observability data with DevOps and SRE goals.

Key benefits include:
- **Real-time insights** into service health and performance.
- **Root cause analysis** for failures via distributed tracing.
- **Compliance** with SLIs/SLOs through structured metrics.
- **Reduced MTTR** by correlating logs, traces, and metrics.

---

## **Schema Reference**
The following tables outline standardized schemas for gRPC observability data, adhering to **OpenTelemetry** and **W3C Trace Context** standards.

### **1. Metrics Schema**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|---------------|---------------------------------------------------------------------------------|---------------------------------------|
| `resource.attributes`   | Object        | System-level metadata (e.g., service name, version, environment).              | `{"service.name": "auth-service", "version": "1.2.0"}` |
| `scope.name`            | String        | gRPC service name (e.g., `auth.v1.AuthService`).                              | `"auth.v1.AuthService"`               |
| `measurement.name`      | String        | Metric name (e.g., `rpc.duration`, `rpc.server.errors`).                        | `"rpc.server.errors"`                 |
| `measurement.unit`      | String        | SI unit (e.g., `seconds`, `count`).                                             | `"seconds"`                           |
| `measurement.value`     | Numeric       | Metric value (e.g., latency in ms, error count).                               | `42.3`                                |
| `attributes`            | Object        | Contextual labels (e.g., HTTP method, status code, peer address).             | `{"http.method": "POST", "status": "403"}` |
| `timestamp`             | ISO 8601      | Event timestamp.                                                                | `"2024-05-20T14:30:00Z"`             |

---
### **2. Logs Schema**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|---------------|---------------------------------------------------------------------------------|---------------------------------------|
| `resource.attributes`   | Object        | Same as Metrics schema.                                                         | `{"service.name": "order-service"}`   |
| `severity`              | String        | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `FATAL`).                       | `"ERROR"`                             |
| `message`               | String        | Human-readable log content.                                                      | `"Token validation failed: invalid issuer."` |
| `attributes`            | Object        | Structured context (e.g., `grpc.method`, `user.id`).                           | `{"grpc.method": "CreateOrder", "user.id": "123"}` |
| `timestamp`             | ISO 8601      | Event timestamp.                                                                | `"2024-05-20T14:30:01Z"`             |
| `trace.id`              | String        | Correlates logs with traces (from Trace Context).                               | `"abc123-def456"`                     |

---
### **3. Traces Schema**
| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                     |
|-------------------------|---------------|---------------------------------------------------------------------------------|---------------------------------------|
| `resource.attributes`   | Object        | Service metadata.                                                               | `{"service.name": "payment-service"}` |
| `trace.id`              | String        | Unique identifier for the trace.                                                | `"abc123-def456-ghi789"`               |
| `span.id`               | String        | Unique identifier for an individual span.                                       | `"def456-ghi789"`                     |
| `name`                  | String        | Span name (e.g., `/auth.v1.AuthService/VerifyToken`).                          | `"/auth.v1.AuthService/VerifyToken"`  |
| `kind`                  | String        | Span type (`SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`).                        | `"SERVER"`                            |
| `start_time`            | ISO 8601      | Span start timestamp.                                                            | `"2024-05-20T14:30:00Z"`             |
| `end_time`              | ISO 8601      | Span end timestamp.                                                              | `"2024-05-20T14:30:02Z"`             |
| `attributes`            | Object        | Contextual data (e.g., `grpc.status_code`, `latency`).                         | `{"grpc.status_code": "200", "latency": "2ms"}` |
| `spans`                 | Array         | Child spans (for nested RPC calls).                                             | *(Nested objects)*                     |

---
### **4. Trace Context (Headers)**
gRPC propagates trace context via HTTP-style headers (RFC 6830). Key headers:
| **Header**              | **Purpose**                                                                     |
|-------------------------|-------------------------------------------------------------------------------|
| `traceparent`           | Encodes `trace_id`, `span_id`, `trace_flags`, and trace version.                |
| `tracestate`            | Extensible carrier for custom trace data (e.g., baggage keys).                |
| `grpc-trace-bin`        | Legacy binary format (deprecated; use OpenTelemetry).                           |

**Example `traceparent`:**
`"00-abc123-def456-01-01"`

---
## **Implementation Details**
### **Core Components**
1. **Instrumentation**
   - **Auto-instrumentation**: Use frameworks like **OpenTelemetry gRPC auto-instrumentation** ([docs](https://github.com/open-telemetry/opentelemetry-auto-instrumentation-node)).
   - **Manual instrumentation**: Explicitly add metrics/logs/traces via language SDKs (e.g., Go’s `otelgrpc`).
   - **gRPC-URL Interceptors**: Inject trace context into client/server calls.

   ```go
   // Go: Instrumenting a gRPC server
   func (s *unaryServerInterceptor) UnaryServerInterceptor(
       ctx context.Context,
       req interface{},
       info *grpc.UnaryServerInfo,
       handler grpc.UnaryHandler,
   ) (interface{}, error) {
       // Start a span for the RPC
       ctx, span := oteltrace.StartSpan(ctx, info.FullMethod)
       defer span.End()
       return handler(ctx, req)
   }
   ```

2. **Sampling**
   - Balance overhead vs. data volume using:
     - **Probabilistic sampling** (e.g., sample 10% of traces).
     - **Adaptive sampling** (increase sampling for errors).
   - Configure via OpenTelemetry Collector or cloud providers (e.g., AWS X-Ray).

3. **Exporting Data**
   - **Backends**: Cloud (Datadog, New Relic, AWS CloudWatch), self-hosted (Prometheus, Loki, Jaeger), or hybrid.
   - **Protocols**: OTLP (recommended), Zipkin, or legacy gRPC/metrics HTTP.

   ```yaml
   # OpenTelemetry Collector config (OTLP export)
   receivers:
     otlp:
       protocols:
         grpc:
         http:
   exporters:
     logging:
       loglevel: debug
     prometheus:
       endpoint: "0.0.0.0:8889"
   ```

4. **Error Handling**
   - Explicitly log gRPC status codes (`status.Code()`, `status.Details()`).
   - Correlate errors with traces via `grpc.status` attributes.

   ```json
   // Example log entry correlating with a trace
   {
     "message": "Token expired",
     "grpc.status_code": "UNAUTHENTICATED",
     "trace.id": "abc123-def456",
     "span.id": "def456-ghi789"
   }
   ```

---

## **Query Examples**
### **1. Metrics Queries (PromQL)**
- **gRPC Server Latency (99th percentile):**
  ```promql
  histogram_quantile(0.99, sum(rate(grpc_server_handling_seconds_bucket[5m])) by (le, service))
  ```
- **RPC Error Rate:**
  ```promql
  sum(rate(grpc_server_started_total[5m])) by (service)
  / sum(rate(grpc_server_handling_seconds_count[5m])) by (service)
  ```
- **Unary vs. Streaming RPCs:**
  ```promql
  sum(rate(grpc_server_unary_server_handled_total[5m])) by (service)
  vs.
  sum(rate(grpc_server_streaming_server_handled_total[5m])) by (service)
  ```

---

### **2. Logs Queries (Loki)**
- **Error Logs for `auth-service`:**
  ```logql
  {service="auth-service", severity="ERROR"} | json | logmsg ~ "token"
  ```
- **Correlated Logs/Traces:**
  ```logql
  {trace_id="abc123-def456"} | logmsg ~ "latency"
  ```

---
### **3. Trace Analysis (Jaeger/Zipkin)**
- **Find slow RPCs (>500ms):**
  ```sql
  SELECT * FROM traces
  WHERE duration > 500
  ORDER BY duration DESC
  LIMIT 10;
  ```
- **Dependency Graph (Service-to-Service):**
  ```sql
  SELECT source_service, target_service, avg(duration)
  FROM traces
  GROUP BY source_service, target_service;
  ```

---

## **Related Patterns**
1. **[Distributed Tracing]** – Extends gRPC Observability to non-gRPC services (e.g., HTTP, databases).
   - *Reference*: [OpenTelemetry Distributed Tracing](https://opentelemetry.io/docs/concepts/distributed-tracing/)

2. **[Metrics-Driven Observability]** – Uses metrics to define SLIs/SLOs (e.g., p99 latency < 100ms).
   - *Tools*: Prometheus, Grafana.

3. **[Structured Logging]** – Standardizes logs with JSON (e.g., [JSON Schema](https://json-schema.org/)).
   - *Example*: Logs as OpenTelemetry Resource Attributes.

4. **[gRPC Load Testing]** – Validates observability under load (e.g., using `k6`).
   - *Tool*: [k6 gRPC Plugin](https://github.com/k6io/k6-grpc).

5. **[Service Mesh Observability]** – Integrates with Istio/Linkerd for mTLS, retries, and circuit breaking metrics.

---
## **Best Practices**
1. **Tag Consistency**: Use consistent `service.name`, `version`, and `environment` labels across metrics/logs/traces.
2. **Sampling Strategy**: Avoid sampling all traces in production; prioritize error paths.
3. **Trace Propagation**: Ensure `traceparent` headers are propagated across all RPCs (including retry logic).
4. **Alerting**: Set up alerts for:
   - `rpc.server.errors` > 1%.
   - `rpc.duration` p99 > SLO threshold.
5. **Cost Optimization**: Downsample metrics in cloud backends (e.g., Prometheus remote write).

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|------------------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Missing traces**                | Client/server not injecting `traceparent`.                                   | Enable auto-instrumentation or manually add interceptors.                    |
| **High cardinality metrics**      | Too many labels (e.g., `peer.address`).                                     | Sample dimensions or use aggregations.                                       |
| **Log correlation fails**          | `trace.id` missing in logs.                                                 | Ensure propagation via `otel.traces.exporter` or custom baggage keys.       |
| **Slow query performance**         | Trace backend (Jaeger) under high load.                                     | Increase Jaeger storage replicas or switch to a managed service (e.g., AWS X-Ray). |

---
## **References**
- **[OpenTelemetry gRPC Guide](https://opentelemetry.io/docs/instrumentation/grpc/)**
- **[gRPC Status Codes](https://grpc.io/docs/what-is-grpc/status-codes/)**
- **[W3C Trace Context](https://www.w3.org/TR/trace-context/)**
- **[OTLP Protocol Spec](https://github.com/open-telemetry/opentelemetry-protocol/tree/main/specification)**