# **[Pattern] Structured Logging Reference Guide**

---

## **Overview**
Structured logging is a **best practice** for writing machine-readable log data that simplifies debugging, monitoring, and analysis across distributed systems. Unlike traditional unstructured logs (key-value pairs or plain text), structured logs use a **consistent schema** (e.g., JSON, Protobuf) for logs to be easily parsed, queried, and correlated across tools like ELK Stack, Splunk, or cloud-based logging platforms (e.g., AWS CloudWatch, Google Cloud Logging).

This guide covers:
- **Key principles** of structured logging
- **Schema design** for consistency
- **Implementation** in common languages/frameworks
- **Best practices** for logging levels, context, and performance
- **Querying and analysis** techniques
- **Related patterns** for advanced use cases

---

## **Key Concepts**
### **1. Why Structured Logging?**
- **Machine-readable**: Logs can be processed without manual parsing.
- **Queryable**: Filter by fields (e.g., `event: "checkout_failure" AND user_id: "123"`).
- **Correlation**: Link logs across services using traces (e.g., request IDs).
- **Scalability**: Easily aggregate logs from microservices.

### **2. Core Components**
| Component          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Log Format**     | Structured (JSON, Protobuf) vs. unstructured (plain text).                 |
| **Schema**         | Defined fields (e.g., `timestamp`, `level`, `message`, `context`).          |
| **Context**        | Additional metadata (e.g., `user_id`, `request_id`, `service_name`).        |
| **Severity Levels**| Log levels (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`) with consistent rules. |
| **Error Details**  | Structured error objects (e.g., `{"error": "timeout", "code": "504"}`).     |
| **Sampling**       | Reduce log volume for non-critical events (e.g., `INFO` logs).              |

---

## **Schema Reference**
A **standardized schema** ensures consistency across services. Below is a **recommended template** (JSON format):

| Field            | Type      | Description                                                                 | Example Values                          |
|------------------|-----------|-----------------------------------------------------------------------------|-----------------------------------------|
| `@timestamp`     | `string`  | ISO 8601 timestamp of the log event.                                         | `"2024-05-20T12:00:00Z"`                 |
| `level`          | `string`  | Severity level (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`).                  | `"ERROR"`                               |
| `message`        | `string`  | Human-readable log content (sanitized).                                     | `"User login failed"`                   |
| `service`        | `string`  | Name of the service generating the log.                                      | `"auth-service"`                        |
| `trace_id`       | `string`  | Unique identifier for correlating logs across services.                      | `"abc123-xyz456"`                       |
| `span_id`        | `string`  | Sub-operation ID (for distributed tracing).                                 | `"def789"`                              |
| `user_id`        | `string`  | Anonymous or authenticated user identifier (PII-sensitive; mask if needed). | `"user-456"`                            |
| `request_id`     | `string`  | End-user request ID (for correlation).                                       | `"req-789"`                             |
| `http`           | `object`  | HTTP-specific metadata (method, status, URL).                                | `{ "method": "POST", "status": 404 }`   |
| `error`          | `object`  | Structured error details (only for `ERROR`/`FATAL`).                        | `{ "code": "403", "message": "Forbidden" }` |
| `metadata`       | `object`  | Custom key-value pairs (e.g., `{"db": "postgres", "version": "v2.1"}`).     | `{ "db": "postgres" }`                  |

---
### **Example Structured Log (JSON)**
```json
{
  "@timestamp": "2024-05-20T12:00:00Z",
  "level": "ERROR",
  "message": "Failed to validate token",
  "service": "auth-service",
  "trace_id": "abc123-xyz456",
  "user_id": "user-456",
  "request_id": "req-789",
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Token expired"
  }
}
```

---

## **Implementation Details**
### **1. Language/Framework Support**
| Language/Framework | Library/Tool               | Example Code Snippet                          |
|--------------------|----------------------------|-----------------------------------------------|
| **Python**         | `structlog`, `logging`      | ```python<br>logger = structlog.get_logger()<br>logger.bind(service="api").error("Failed login", user_id="123")``` |
| **Java**           | SLF4J + Logback             | ```java<br>log.error("Login failed", "userId=123", "errorCode=403");``` |
| **Node.js**        | `pino`, `winston`           | ```javascript<br>logger.error({ userId: "123", error: "Invalid token" }, "Login failed");``` |
| **Go**             | `zap`                       | ```go<br>log.Error("login failed", "user_id", "123", "error_code", "403")``` |
| **.NET**           | `Serilog`                   | ```csharp<br>Log.Error("Login failed", new { UserId = "123", ErrorCode = "403" });``` |

### **2. Best Practices for Implementation**
- **Avoid PII**: Mask sensitive data (e.g., `user_id` as `"user-*"`).
- **Performance**: Use synchronous logging (async can add latency).
- **Consistency**: Enforce a **single schema** across services.
- **Compression**: Use gzip for log storage/retrieval.
- **Retention**: Follow **log retention policies** (e.g., 30–90 days).

---

## **Query Examples**
Structured logs enable **powerful querying** via tools like:
- **ELK Stack (Elasticsearch/Kibana)**
  ```json
  // Find all 403 errors in the last 24h
  {
    "query": {
      "bool": {
        "must": [
          { "match": { "level": "ERROR" } },
          { "match": { "error.code": "403" } },
          { "range": { "@timestamp": { "gte": "now-24h" } } }
        ]
      }
    }
  }
  ```
- **AWS CloudWatch Logs Insights**
  ```sql
  // Count failed logins by user (last 7 days)
  filter level = "ERROR" and message like /"login failed"/
  | stats count(*) by user_id
  | sort -count
  ```
- **Grafana Loki**
  ```grafana
  // Errors in the payment service with HTTP 5xx
  {service="payment-service", level="ERROR", http.status >= 500}
  ```

---

## **Performance Considerations**
| Action                          | Impact                          | Mitigation Strategy                          |
|---------------------------------|---------------------------------|---------------------------------------------|
| **Async logging**               | Adds ~1–5ms latency.           | Use synchronous logging for critical paths. |
| **High volume**                 | Storage costs/slow queries.    | Sample logs (e.g., `INFO` → `WARN` only).    |
| **Serialization overhead**      | Slower than plaintext.         | Use lightweight formats (e.g., Protobuf).   |

---

## **Related Patterns**
1. **Distributed Tracing**
   - Correlate logs with traces (e.g., **OpenTelemetry**, **Jaeger**).
   - *Use case*: Debug cross-service failures.

2. **Log Sampling**
   - Reduce volume by sampling logs (e.g., sample 1% of `DEBUG` logs).
   - *Tools*: AWS CloudWatch Logs, Datadog.

3. **Structured Error Handling**
   - Log errors as structured objects (e.g., `{ "type": "DatabaseError", "table": "users" }`).
   - *Tools*: Sentry, ErrorTracking.

4. **Log Sharding**
   - Partition logs by service/region to improve query performance.
   - *Tools*: Elasticsearch indices, Splunk buckets.

5. **Observability Pipeline**
   - Combine logs with **metrics** (Prometheus) and **traces** (OpenTelemetry).
   - *Tools*: Grafana, Lumigo.

---

## **Checklist for Adoption**
| Task                                      | Status  |
|-------------------------------------------|---------|
| Define a **shared log schema**.           | [ ]     |
| Replace `print`/`console.log` with structured logging. | [ ]   |
| Add `trace_id`/`request_id` to all logs.    | [ ]     |
| Mask PII in logs.                          | [ ]     |
| Test log queries in your SIEM tool.        | [ ]     |
| Implement log retention policies.          | [ ]     |
| Monitor log cardinality (number of unique fields). | [ ] |

---
## **Further Reading**
- [OpenTelemetry Logs Specification](https://opentelemetry.io/docs/specs/logs/)
- [AWS Best Practices for Structured Logging](https://aws.amazon.com/blogs/architecture/)
- [ELK Stack Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)