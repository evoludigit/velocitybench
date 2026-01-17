---
# **[Pattern] REST Observability Reference Guide**

---

## **Overview**
REST Observability provides a structured approach to monitoring, logging, and tracing microservices communicating via REST APIs. It ensures resilience, performance insights, and debugging capabilities by capturing key request/response metadata—such as latency, status codes, headers, and payloads—while adhering to REST conventions. This pattern complements existing observability tools like OpenTelemetry but focuses specifically on REST-specific artifacts (e.g., `Location` headers, HATEOAS links) and distributed tracing for RESTful workflows.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Log Injection**         | Appending structured metadata (e.g., `requestID`, `apiVersion`) to logs to correlate logs, traces, and metrics.                                                                                                                                                       |
| **REST-Specific Context** | Embedding context (e.g., `Authorization`, `X-Request-ID`) in HTTP headers to propagate across hops.                                                                                                                                                          |
| **HATEOAS Links**         | Treating HATEOAS links (`_links` in JSON responses) as observable artifacts to track navigation paths.                                                                                                                                                          |
| **Error Budgets**         | Calculating failure rates per endpoint to enforce reliability SLAs (e.g., 99.9% uptime).                                                                                                                                                            |
| **Payload Redaction**     | Masking sensitive fields (e.g., PII, tokens) in logs/traces to comply with security policies.                                                                                                                                                                   |
| **Distributed Traces**    | Assigning unique trace IDs to REST calls and correlating with downstream services.                                                                                                                                                                      |
| **Schema Enforcement**    | Validating API responses against OpenAPI/Swagger schemas to detect inconsistencies.                                                                                                                                                                   |
| **Anomaly Detection**     | Using statistical models (e.g., P99 latency thresholds) to flag aberrant behavior.                                                                                                                                                                      |

---

## **Schema Reference**
Below is a schema for REST Observability metadata. Useful for logs, traces, and metrics instrumentation.

| **Field**               | **Type**   | **Description**                                                                                                                                                             | **Example**                          |
|-------------------------|------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `trace_id`              | String     | Unique identifier for distributed traces.                                                                                                                                       | `trace-123e4567-e89b-12d3-a456`      |
| `span_id`               | String     | Span identifier for individual requests.                                                                                                                                         | `span-56789`                         |
| `request_id`            | String     | Client-facing request identifier for correlation across services.                                                                                                          | `req-abc123`                         |
| `method`                | String     | HTTP method (GET, POST, etc.).                                                                                                                                                   | `POST`                               |
| `path`                  | String     | REST endpoint path (e.g., `/v1/users`).                                                                                                                                          | `/api/v2/orders`                     |
| `status_code`           | Integer    | HTTP status code (200, 404, etc.).                                                                                                                                                 | `200`                                |
| `latency_ms`            | Number     | End-to-end latency in milliseconds.                                                                                                                                              | `124.5`                              |
| `headers`               | Object     | Request/response headers (sanitized).                                                                                                                                          | `{ "Authorization": "Bearer xxxx" }` |
| `payload_size`          | Number     | Request/response payload size in bytes.                                                                                                                                           | `892`                                |
| `location_header`       | String     | Value of `Location` header (for redirects).                                                                                                                                     | `https://api.example.com/users/42`   |
| `links`                 | Array      | HATEOAS links in response (e.g., `{ "self": "/users", "delete": "/users/42" }`).                                                                                          | `[{"rel": "self", "href": "/users"}]`|
| `error_code`            | String     | Custom error identifier (e.g., `INVALID_PARAM`).                                                                                                                                        | `40001`                              |
| `observation_time`      | Timestamp  | When the observation was recorded (UTC).                                                                                                                                         | `2024-01-15T12:00:00Z`               |
| `retry_count`           | Integer    | Number of retries for the request.                                                                                                                                              | `2`                                  |

---

## **Implementation Details**

### **1. Log Injection**
Inject a `request_id` into logs and traces using middleware or SDKs (e.g., `OpenTelemetry`):

```python
import uuid
import logging

def inject_metadata(request, response):
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    logging.info(f"Request ID: {request_id}; Path: {request.path}")
    response.headers['X-Request-ID'] = request_id
```

### **2. Distributed Tracing**
For each REST call, create an OpenTelemetry span with a parent span for downstream calls:

```java
// Java (Spring Boot + OpenTelemetry)
@Autowired
private Tracer tracer;

@GetMapping("/orders")
public ResponseEntity<Order> getOrder(@RequestParam Long id) {
    Span span = tracer.spanBuilder("GET /orders").startSpan();
    try (Scope scope = span.makeCurrent()) {
        Order order = orderService.getOrder(id);
        return ResponseEntity.ok(order);
    } finally {
        span.end();
    }
}
```

### **3. HATEOAS Tracking**
Log HATEOAS links for navigation analysis:

```javascript
// Node.js (Express)
app.get('/users/:id', (req, res) => {
  const user = await db.getUser(req.params.id);
  const response = {
    ...user,
    _links: {
      self: `/users/${req.params.id}`,
      orders: `/users/${req.params.id}/orders`
    }
  };
  res.json(response);
});
```

### **4. Schema Enforcement**
Validate API responses against OpenAPI schemas using tools like `JSON Schema` or `FastAPI` (Python):

```yaml
# OpenAPI schema snippet
responses:
  200:
    description: Successful response
    content:
      application/json:
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            _links:
              type: object
              patternProperties:  # HATEOAS links
                "^[a-z]+$":
                  type: string
```

---

## **Query Examples**

### **1. Correlate Logs with a `request_id`**
```sql
-- PostgreSQL
SELECT *
FROM api_logs
WHERE request_id = 'req-abc123'
ORDER BY timestamp DESC;
```

### **2. Trace Latency by Endpoint**
```sql
-- Using OpenTelemetry traces
SELECT
  method,
  path,
  percentile(latency_ms, 99) as p99_latency
FROM api_traces
GROUP BY method, path
ORDER BY p99_latency DESC;
```

### **3. Detect HATEOAS Navigation Patterns**
```sql
-- Correlate with HATEOAS links
SELECT
  COUNT(*) as navigation_count,
  links.href as path
FROM api_traces
JOIN JSON_TABLE(
  CAST(payload AS JSON),
  '$._links[*].href'
  COLUMNS (href VARCHAR(255) PATH '$')
) links
GROUP BY links.href;
```

### **4. Error Budget Calculation**
```sql
-- Python (using Prometheus metrics)
from prometheus_client import Gauge

error_budget_gauge = Gauge(
    'api_error_budget',
    '99.9% SLA compliance for endpoints',
    ['endpoint', 'time_window']
)

# Update metric daily
error_budget_gauge.labels(endpoint='/user/create', time_window='daily').set(0.01)
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                   |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Asynchronous Observability**   | Extends REST Observability to async messaging (e.g., Kafka, SQS) with trace headers.                                                                                                                      |
| **Metrics-Driven API Design**   | Aligns API contracts with metrics (e.g., rate limits, quotas) using OpenTelemetry SDKs.                                                                                                               |
| **Security Observability**      | Adds JWT validation checks and anomaly detection for `Authorization` headers.                                                                                                                           |
| **Distributed Rate Limiting**   | Enforces rate limits per trace_id to prevent abuse across services.                                                                                                                                    |
| **Schema Registry Integration** | Version APIs using OpenAPI schemas and track breaking changes.                                                                                                                                          |

---
**Note:** Combine with **OpenTelemetry**, **Prometheus**, and **Grafana** for end-to-end observability. For sensitive data, use **payload redaction** tools like `AWS Kinesis Data Firehose`.