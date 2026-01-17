# **[Pattern] Trace Collection Patterns Reference Guide**

---

## **Overview**
Trace Collection Patterns provide a structured approach to capturing, analyzing, and optimizing application tracing data. These patterns help standardize logging, tracing, and monitoring to improve observability, debug performance bottlenecks, and ensure traceability across distributed systems. By defining consistent conventions for trace collection, teams can reduce noise, accelerate incident resolution, and automate trace-based insights.

Common use cases include:
- Debugging microservices and distributed transactions.
- Analyzing performance degradation in cloud-native applications.
- Correlating logs, metrics, and traces for root-cause analysis.
- Enforcing compliance requirements for audit trails.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
Trace collection involves three primary elements:
- **Trace Context Propagation**: Passing trace IDs across service boundaries (e.g., via HTTP headers, W3C Trace Context header).
- **Trace Segment Generation**: Recording events (e.g., incoming requests, database queries, errors) with timestamps and metadata.
- **Trace Aggregation**: Collecting, storing, and correlating segments into structured traces.

### **2. Trace Collection Modes**
| Mode               | Description                                                                 | Use Case                          |
|--------------------|-----------------------------------------------------------------------------|-----------------------------------|
| **Manual**         | Developers explicitly instrument code with trace calls.                     | Legacy systems, custom analytics. |
| **Automatic**      | Instrumentation is auto-injected (e.g., via APM tools).                     | Cloud-native apps, microservices. |
| **Hybrid**         | Combines manual (critical paths) and automatic (common operations).       | Balanced observability.           |

### **3. Trace Attributes**
Standard metadata attached to trace segments:

| Attribute          | Type      | Description                                                                 |
|--------------------|-----------|-----------------------------------------------------------------------------|
| `trace_id`         | String    | Unique identifier for a single trace (W3C standard: `format: [X]{12}`).    |
| `span_id`          | String    | Unique identifier for a trace segment.                                       |
| `parent_id`        | String    | References the trace/span this segment belongs to (if nested).              |
| `operation_name`   | String    | Human-readable name of the operation (e.g., `GET /users`).                |
| `timestamp`        | ISO 8601  | When the event occurred (start/end of span).                                |
| `duration`         | Duration  | Time taken for the span (e.g., `P0.150S`).                                  |
| `status`           | Enum      | `UNSET`, `OK`, `ERROR` (W3C Trace Status).                                  |
| `resource`         | Object    | Context (e.g., `service.name=order-service`, `version=v1.2.0`).             |
| `tags`             | Key-Value | Custom metadata (e.g., `http.method=POST`, `user.id=1234`).                 |

---
## **Schema Reference**

### **1. Trace Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Trace",
  "type": "object",
  "properties": {
    "trace_id": { "type": "string", "format": "uuid" },
    "created_at": { "type": "string", "format": "date-time" },
    "resource": {
      "type": "object",
      "properties": {
        "service": { "type": "string" },
        "version": { "type": "string" },
        "environment": { "type": "string" }
      }
    },
    "spans": {
      "type": "array",
      "items": { "$ref": "#/definitions/span" }
    }
  },
  "required": ["trace_id", "spans"],
  "definitions": {
    "span": {
      "type": "object",
      "properties": {
        "span_id": { "type": "string", "format": "uuid" },
        "parent_id": { "type": "string", "format": "uuid" },
        "operation_name": { "type": "string" },
        "start_time": { "type": "string", "format": "date-time" },
        "duration": { "type": "string", "format": "duration" },
        "status": { "enum": ["UNSET", "OK", "ERROR"] },
        "tags": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      },
      "required": ["span_id", "operation_name", "start_time", "duration"]
    }
  }
}
```

---

### **2. Example Trace Payload**
```json
{
  "trace_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2023-10-05T12:00:00Z",
  "resource": {
    "service": "order-service",
    "version": "v1.2.0",
    "environment": "production"
  },
  "spans": [
    {
      "span_id": "a1b2c3d4-e5f6-7890",
      "operation_name": "GET /orders/123",
      "start_time": "2023-10-05T12:00:01Z",
      "duration": "P0.002S",
      "status": "OK",
      "tags": {
        "http.method": "GET",
        "user.id": "456"
      }
    },
    {
      "span_id": "b2c3d4e5-f678-90ab",
      "parent_id": "a1b2c3d4-e5f6-7890",
      "operation_name": "db.query",
      "start_time": "2023-10-05T12:00:02Z",
      "duration": "P0.001S",
      "status": "OK",
      "tags": {
        "db.operation": "SELECT",
        "query": "SELECT * FROM orders WHERE id=123"
      }
    }
  ]
}
```

---

## **Query Examples**
### **1. Find Traces with Errors**
```sql
SELECT *
FROM traces
WHERE EXISTS (
  SELECT 1
  FROM spans
  WHERE spans.trace_id = traces.trace_id
  AND spans.status = 'ERROR'
)
ORDER BY traces.created_at DESC
LIMIT 100;
```

### **2. Correlate Traces with Slow Spans**
```sql
SELECT t.trace_id, s.operation_name, s.duration
FROM traces t
JOIN spans s ON t.trace_id = s.trace_id
WHERE s.duration > 'PT5S'
ORDER BY s.duration DESC;
```

### **3. Group Traces by Service**
```sql
SELECT
  r.service,
  COUNT(DISTINCT t.trace_id) as trace_count
FROM traces t
JOIN trace_resources r ON t.trace_id = r.trace_id
GROUP BY r.service
ORDER BY trace_count DESC;
```

### **4. Filter Traces by Custom Tags**
```sql
SELECT *
FROM traces
WHERE EXISTS (
  SELECT 1
  FROM spans
  WHERE spans.trace_id = traces.trace_id
  AND spans.tags->>'http.method' = 'POST'
);
```

---

## **Implementation Best Practices**

### **1. Instrumentation**
- **Auto-instrumentation**: Use APM tools (e.g., OpenTelemetry, Datadog, New Relic) for cloud-native apps.
- **Manual traces**: Add traces for critical paths (e.g., payment processing) using:
  ```python
  from opentelemetry import trace

  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("process_order"):
      # Business logic
  ```

### **2. Trace Context Propagation**
- **HTTP Headers**: Use `traceparent` header (W3C standard) for distributed tracing.
  Example:
  ```
  traceparent: 00-123e4567e89b12d3a456426614174000-00f067aa0ba902b7-01
  ```
- **gRPC/Thrift**: Inject trace context via metadata.

### **3. Sampling Strategies**
| Strategy       | Description                                                                 | When to Use                          |
|----------------|-----------------------------------------------------------------------------|--------------------------------------|
| **Always**     | Trace every request (high overhead).                                       | Development environments.           |
| **Probabilistic** | Trace with a fixed probability (e.g., 10%).                               | Production (balance overhead/coverage). |
| **Adaptive**   | Dynamically adjust sampling based on error rates or latency spikes.        | Observability-heavy workloads.       |

### **4. Storage & Retention**
- **Short-term**: Store raw traces for real-time analysis (e.g., Elasticsearch).
- **Long-term**: Aggregate traces (e.g., flame graphs, latency histograms) for historical analysis.

---

## **Related Patterns**
1. **Instrumentation Pattern**: Guidelines for adding observability instrumentation.
2. **Log Correlation Pattern**: Linking logs with traces for deeper analysis.
3. **Distributed Tracing Pattern**: Design principles for tracing across services.
4. **Performance Optimization Pattern**: Using traces to identify and fix bottlenecks.
5. **Data Retention Policy Pattern**: Managing trace storage costs and compliance.

---
## **Tools & Libraries**
| Category               | Tools/Libraries                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **APM Tools**          | Datadog, New Relic, Dynatrace, AppDynamics, Azure Application Insights.       |
| **OpenTelemetry**      | [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/), SDKs.     |
| **Trace Storage**      | Jaeger, Zipkin, Elasticsearch, Datadog Trace.                                   |
| **Samplers**           | Tail sampling, head-based sampling, adaptive sampling.                         |

---
## **Common Pitfalls & Mitigations**
| Pitfall                          | Mitigation                                                                     |
|-----------------------------------|-------------------------------------------------------------------------------|
| **Trace Overhead**               | Use sampling; prioritize traces for errors/latency.                            |
| **Inconsistent Trace IDs**       | Standardize trace context propagation (W3C headers).                          |
| **Noise in Logs/Traces**         | Filter low-value spans (e.g., ignore `GET /health`).                          |
| **Vendor Lock-in**               | Use OpenTelemetry for vendor-agnostic instrumentation.                        |

---
## **Further Reading**
- [W3C Trace Context Specification](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Distributed Tracing in Microservices](https://www.oreilly.com/library/view/distributed-tracing-in/9781492033467/)