# **[Pattern] Tracing Standards Reference Guide**

---

## **Overview**
**Tracing Standards** is a distributed tracing pattern that standardizes how requests and operations are tracked across microservices and components in a distributed system. By defining consistent naming conventions, metadata structures, and semantic annotations, this pattern ensures interoperability between tracing systems (e.g., OpenTelemetry, Jaeger, Zipkin) and improves observability, debugging, and performance analysis. This guide outlines key concepts, schema standards, implementation best practices, and integration examples.

---

## **Key Concepts**
Ensure clarity and consistency across tracing implementations:

| **Concept**            | **Description**                                                                                     | **Example**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Trace ID**           | Unique identifier for an end-to-end request flow.                                                   | `0af76b71-0b8d-4d4a-832e-1b2f3d445e6a`                                                          |
| **Span**               | Represents a single operation (e.g., API call, DB query) within a trace.                           | `GET /api/users/{id}`                                                                         |
| **Span Context**       | Contains trace and span IDs to propagate context across service boundaries.                          | `{ trace_id: "..." }`                                                                          |
| **Attributes (Tags)**  | Key-value pairs describing a span (e.g., status, user-agent).                                       | `{"db.system": "PostgreSQL", "http.method": "POST"}`                                           |
| **Logs**               | Time-series events within a span (e.g., "Query executed in 10ms").                                  | `{ timestamp: "2023-10-01T12:00:00Z", message: "Slow query" }                                  |
| **Links**              | References to related spans (e.g., async calls).                                                   | `"span_id": "9b1deca3-..."`, `"type": "CHILD_OF"`                                             |
| **Resource Attributes**| Describes the system/process running the span (e.g., service name, version).                       | `{"service.name": "user-service", "service.version": "v1.2.3"}`                               |

---

## **Schema Reference**
Standardized schema for trace data (OpenTelemetry-compatible). **Required** fields are marked (`*`).

| **Field**          | **Type**       | **Description**                                                                                     | **Example**                                                                                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **trace_id**       | `string*`      | Globally unique identifier for the entire trace.                                                    | `0af76b71-0b8d-4d4a-832e-1b2f3d445e6a`                                                          |
| **span_id**        | `string*`      | Unique identifier for the span within a trace.                                                      | `8b7c2b4b-3a1d-4b3f-9e2c-1a3b7d6e4f5g`                                                          |
| **name**           | `string*`      | Human-readable span operation name (e.g., `process_order`).                                         | `GET /orders`                                                                                  |
| **kind**           | `enum*`        | Span type (`CLIENT`, `SERVER`, `PRODUCER`, `CONSUMER`, `INTERNAL`).                               | `"SERVER"`                                                                                     |
| **start_time**     | `string*`      | ISO 8601 timestamp when the span began.                                                             | `"2023-10-01T12:30:45.123Z"`                                                                  |
| **end_time**       | `string`       | ISO 8601 timestamp when the span ended (optional for incomplete spans).                            | `"2023-10-01T12:31:00.456Z"`                                                                  |
| **status**         | `object`       | Span outcome (`code`: `OK`, `ERROR`; `message`: optional error details).                           | `{"code": "ERROR", "message": "Database timeout"}`                                              |
| **attributes**     | `map<string, string>` | Key-value metadata (e.g., `http.method`, `db.user`).                                               | `{"user.id": "123", "request.duration": "50ms"}`                                              |
| **links**          | `array<object>`| References to related spans (e.g., `TRACE_ID` or `CAUSE`).                                         | `[{"trace_id": "abc123", "type": "TRACE_ID"}]`                                                  |
| **resource**       | `object`       | System context (e.g., service name, environment).                                                  | `{"service.name": "payment-gateway", "deployment.environment": "prod"}`                       |

---

## **Implementation Best Practices**
### **1. Trace Propagation**
Use **headers** or **carrier formats** (e.g., W3C Trace Context) to propagate trace IDs:
```http
GET /orders/123 HTTP/1.1
traceparent: 00-0af76b710b8d4d4a832e1b2f3d445e6a-0af76b710b8d4d4a832e1b2f3d445e6a-01
```

### **2. Attribute Naming Conventions**
- **Prefixes**:
  - `http.` for HTTP spans (e.g., `http.method`).
  - `db.` for database operations (e.g., `db.type="postgresql"`).
  - `cloud.` for cloud providers (e.g., `cloud.provider="aws"`).
- **Reserved Attributes**:
  Avoid overriding system-defined keys (e.g., `span.id`, `trace.id`).

### **3. Error Handling**
- Set `status.code="ERROR"` and include a `message` attribute.
- Example:
  ```json
  {
    "status": {"code": "ERROR", "message": "Timeout connecting to payment service"}
  }
  ```

### **4. Sampling**
- Use **probabilistic sampling** (e.g., 1% of traces) to balance load and observability.
- Example (OpenTelemetry):
  ```python
  sampler = ProbabilitySampler(0.01)  # 1% sampling rate
  ```

---

## **Query Examples**
### **1. Filter Traces by Service**
**OpenTelemetry Query (PromQL-like):**
```sql
{
  resource.attributes["service.name"] = "user-service"
  attributes["http.method"] = "POST"
}
```

### **2. Find Slow Spans**
**Jaeger Query:**
```sql
span.duration > 1000ms
AND attributes["http.url"] =~ ".*/orders.*"
```

### **3. Correlate Dependencies**
**Zipkin Query:**
```sql
trace(trace_id="0af76b71-0b8d-4d4a-832e-1b2f3d445e6a")
AND span(span_id="8b7c2b4b-3a1d-4b3f-9e2c-1a3b7d6e4f5g")
```

### **4. Aggregate by Attribute**
**OpenTelemetry Metrics:**
```sql
histogram.bucket(
  name: "http.request.duration",
  sum(attributes["http.method"] == "GET" ? span.duration : 0)
)
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **Use Case**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Context Propagation]**    | Mechanisms to pass request context (e.g., user ID, auth token) across services.                    | Secure microservices communication.                                                              |
| **[Instrumentation]**        | Adding code to generate trace data (e.g., auto-instrumentation libraries).                       | Reduce manual tracing boilerplate.                                                                |
| **[Sampling]**              | Controlling the volume of traces to analyze.                                                        | Optimize tracing overhead in high-throughput systems.                                           |
| **[Distributed Locks]**     | Avoiding duplicate work in async flows.                                                           | Event-driven architectures (e.g., sagas).                                                       |
| **[Circuit Breaker]**       | Preventing cascading failures via trace-based fault isolation.                                     | Resilient service mesh integrations.                                                            |

---

## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                                     | **Links**                                                                                       |
|------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **OpenTelemetry**      | Standardized SDKs for instrumentation (Java, Go, Python, etc.).                                 | [https://opentelemetry.io](https://opentelemetry.io)                                              |
| **Jaeger**             | UI for visualizing traces (supports OpenTelemetry).                                             | [https://www.jaegertracing.io](https://www.jaegertracing.io)                                      |
| **Zipkin**             | Lightweight trace collector (relies on Thrift protocol).                                        | [https://zipkin.io](https://zipkin.io)                                                          |
| **Grafana Tempo**      | High-performance trace storage (with Loki for logs).                                              | [https://grafana.com/docs/tempo](https://grafana.com/docs/tempo)                                  |
| **AWS X-Ray**          | AWS-native tracing with serverless integrations.                                                 | [https://aws.amazon.com/xray](https://aws.amazon.com/xray)                                        |

---

## **Troubleshooting Common Issues**
| **Issue**                          | **Root Cause**                                                                                     | **Solution**                                                                                     |
|-------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Incomplete traces**               | Missing span propagation headers.                                                                  | Verify `traceparent`/`tracecontext` headers are sent/received.                                   |
| **High cardinality in attributes**  | Too many unique attribute values (e.g., raw query strings).                                       | Use normalized values (e.g., `db.query_type="SELECT"` instead of full SQL).                     |
| **Sampling rate too low**           | Missing traces after sampling.                                                                    | Increase sampling probability or use adaptive sampling.                                         |
| **Trace ID collisions**             | Race conditions generating duplicate IDs.                                                          | Use UUIDv4 or cryptographically secure random IDs.                                                |

---

## **Schema Evolution**
To maintain backward compatibility:
1. **Add new attributes** with optional prefixes (e.g., `experimental.`).
   Example:
   ```json
   {"experimental.new_metric": "value"}  // Safe to ignore in older systems
   ```
2. **Use backward-compatible formats** (e.g., Protobuf for OpenTelemetry).
3. **Deprecate attributes** via versioned schemas (e.g., `deprecated_since="v2.0"`).