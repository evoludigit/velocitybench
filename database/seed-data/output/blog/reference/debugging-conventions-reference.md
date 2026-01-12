# **[Pattern] Debugging Conventions Reference Guide**

---

## **Overview**

Debugging Conventions is a structured approach to standardizing error handling, logging, and traceability across an application or system. This pattern ensures that debugging information follows predictable formats, reducing ambiguity and streamlining issue resolution. By enforcing conventions for:
- **Error codes** (numeric or alphanumeric identifiers)
- **Log levels** (e.g., `DEBUG`, `INFO`, `WARN`, `ERROR`)
- **Stack trace formatting**
- **Contextual metadata** (e.g., request IDs, timestamps)
- **Structured logging** (JSON, key-value pairs)

developers and operations teams can quickly correlate issues, automate monitoring, and minimize downtime. This guide outlines the components, requirements, and examples for implementing Debugging Conventions effectively.

---

## **Implementation Details**

### **Core Principles**
1. **Consistency**: All errors and logs must adhere to the same schema.
2. **Contextual Relevance**: Include traceable identifiers (e.g., `trace_id`, `user_id`) where applicable.
3. **Human + Machine Readability**: Format logs for both developers (structured) and tools (e.g., ELK, Prometheus).
4. **Versioning**: Support backward compatibility when updating schemas.

---

### **Key Components**

| **Component**          | **Description**                                                                                     | **Example Value**                     |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------|
| **Log Level**          | Severity of the log entry (per [RFC 5424](https://tools.ietf.org/html/rfc5424)).                    | `ERROR`, `5` (numeric equivalent)      |
| **Timestamp**          | ISO 8601 formatted time when the log was generated.                                                 | `2024-05-20T14:30:45.123Z`             |
| **Trace ID**           | Unique identifier for a request/transaction flow.                                                    | `xf3r89a2-d1b0-4e5d-8f7a-1234567890ab` |
| **Error Code**         | Numeric or alphanumeric identifier for the specific error (see [Schema Reference](#schema-reference)).| `400-002`, `404`                       |
| **Module/Service**     | Name of the component generating the log.                                                            | `auth-service`, `order-api`            |
| **Message**            | Human-readable description of the issue.                                                             | `"Invalid API key format supplied"`    |
| **Metadata**           | Additional context (e.g., input data, affected entities).                                           | `{"user_ip": "192.0.2.1", "status": 403}` |
| **Stack Trace**        | (For errors) Call stack details including filenames, line numbers, and relevant code snippets.       | `File "orders.py", line 42, in process()` |

---

## **Schema Reference**

| **Field**              | **Type**       | **Required** | **Description**                                                                                     | **Validation Rules**                          | **Example**                                      |
|------------------------|---------------|--------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|--------------------------------------------------|
| `timestamp`            | string        | ✅            | ISO 8601 formatted UTC timestamp.                                                                    | Regex: `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$` | `2024-05-20T14:30:45.123Z`                     |
| `level`                | string/enum   | ✅            | Log level from `["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]`.                                   | Fixed set of values                           | `"ERROR"`                                       |
| `trace_id`             | string (UUID) | ✅            | 36-character UUIDv4 (or custom format).                                                            | Valid UUID regex                               | `550e8400-e29b-41d4-a716-446655440000`           |
| `error_code`           | string/int    | ❌ (for `INFO`/`DEBUG`) | Numeric (e.g., HTTP status) or alphanumeric (e.g., `DB-001`).                                    | Alpha-numeric or numeric                       | `500`, `DB-003`                                  |
| `module`               | string        | ✅            | Name of the service/module logging the entry.                                                      | Max 64 chars                                  | `payment-gateway`                               |
| `message`              | string        | ✅            | Human-readable error message.                                                                         | Max 512 chars                                  | `"Database connection timeout exceeded"`         |
| `metadata`             | object        | ❌            | Key-value pairs for additional context (e.g., `{"retries": 3}`).                                   | JSON-serializable                              | `{"user_id": "u123", "request_body": "..."}`     |
| `stack_trace`          | string[]      | ❌ (for non-errors) | Array of stack frames (filename, line, function).                                                 | Max 5 entries per trace                       | `[{"file": "app.py", "line": 42, "function": "validate"}]` |

---

## **Query Examples**

### **1. Filtering Errors by Trace ID**
**Use Case**: Isolate logs for a specific problematic request.
```sql
-- Example for ELK (Logstash Query DSL)
trace_id: "550e8400-e29b-41d4-a716-446655440000" AND level: "ERROR"
```

**Grok Pattern** (for parsing logs):
```plaintext
%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{UUID:trace_id} %{WORD:module} - %{GREEDYDATA:message}
```

---

### **2. Identifying Frequent Errors by Code**
**Use Case**: Prioritize error codes with high occurrence.
```python
# Pseudocode for Python (using a logging library)
from collections import defaultdict

errors_by_code = defaultdict(int)
for record in logs:
    if record["level"] == "ERROR":
        errors_by_code[record["error_code"]] += 1

sorted(errors_by_code.items(), key=lambda x: x[1], reverse=True)
```

**Output**:
```
[('500', 124), ('DB-003', 87), ('404', 62)]
```

---

### **3. Correlating Errors with User Impact**
**Use Case**: Find all errors affecting a specific user.
```javascript
// MongoDB Query Example
db.logs.aggregate([
  {
    $match: {
      "metadata.user_id": "u123",
      "level": "ERROR"
    }
  },
  {
    $group: {
      _id: "$error_code",
      count: { $sum: 1 },
      first_seen: { $min: "$timestamp" }
    }
  }
])
```

---

## **Error Code Schema (Extensible Example)**

| **Domain**       | **Code** | **Description**                                                                 | **HTTP Equivalent** | **When Used**                                  |
|------------------|----------|---------------------------------------------------------------------------------|---------------------|------------------------------------------------|
| **Client Errors**| `400-001`| Invalid request payload.                                                       | 400                 | Bad API input (e.g., malformed JSON).         |
|                  | `401-002`| Authentication failed.                                                          | 401                 | Invalid credentials/tokens.                   |
| **Server Errors**| `500-001`| Database query timeout.                                                         | 500                 | DB connection issues.                          |
|                  | `500-002`| Rate limit exceeded.                                                            | 429                 | Throttled due to high traffic.                 |
| **Custom**       | `DB-001` | Primary key violation (e.g., duplicate entry).                                 | 409                 | Database conflicts.                            |
|                  | `API-001`| Third-party API unavailability.                                                | -                   | External service downtime.                     |

**Format Rules**:
- **HTTP-aligned codes**: Prefix with `4xx`/`5xx` (e.g., `400-001`).
- **Domain-specific codes**: Use hyphenated namespaces (e.g., `DB-001`).
- **Versioning**: Append `-v2` if the schema changes (e.g., `400-001-v2`).

---

## **Query Examples for Structured Logs (JSON)**

### **1. Find All Warnings with a Specific Keyword**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level.keyword": "WARN" } },
        { "wildcard": { "message": "*timeout*" } }
      ]
    }
  }
}
```
*(ELK/Kibana query syntax)*

---

### **2. Aggregate Errors by Service**
```sql
SELECT
  module,
  error_code,
  COUNT(*) as frequency
FROM logs
WHERE level = 'ERROR'
GROUP BY module, error_code
ORDER BY frequency DESC;
```
*(SQL-compatible format for databases like PostgreSQL)*

---

## **Related Patterns**

1. **[Structured Logging](https://example.com/structured-logging)**
   - Extends Debugging Conventions by enforcing JSON/key-value log formats for easier parsing.

2. **[Centralized Logging](https://example.com/centralized-logging)**
   - Complements this pattern by aggregating logs from multiple services (e.g., using ELK, Splunk, or Loki).

3. **[Error Budgets](https://example.com/error-budgets)**
   - Use error codes to calculate failure rates and allocate "error budgets" for deployments.

4. **[Distributed Tracing](https://example.com/distributed-tracing)**
   - Integrates with `trace_id` to correlate logs across microservices (e.g., using OpenTelemetry).

5. **[Graceful Degradation](https://example.com/graceful-degradation)**
   - Pair with error codes to implement fallback behavior for critical failures (e.g., `DB-001` → switch to cache).

6. **[Circuit Breakers](https://example.com/circuit-breaker)**
   - Map error codes (e.g., `API-001`) to trigger circuit breaker logic for external dependencies.

---

## **Best Practices**

### **1. Error Code Naming**
- **Specificity**: Avoid vague codes like `ERR-001`; use descriptive names (e.g., `DB-CONN-FAIL`).
- **Hierarchy**: Group codes by domain (e.g., `AUTH-`, `PAY-`, `CACHE-`).
- **Documentation**: Maintain a **codex** (e.g., Markdown/Confluence page) for all error codes.

### **2. Log Rotation & Retention**
- **Short-term**: Retain `ERROR`/`CRITICAL` logs for **90 days** (for incident analysis).
- **Long-term**: Archive `INFO`/`DEBUG` logs for **30 days** (or until next major release).
- **Tools**: Use tools like Logrotate or AWS CloudWatch Logs to automate retention.

### **3. Handling Sensitive Data**
- **Redact PII**: Never log passwords, tokens, or user IDs in `DEBUG` logs.
- **Example**:
  ```json
  {
    "level": "DEBUG",
    "message": "User authentication attempt",
    "metadata": {
      "user_id": "[REDACTED]",  // Always redact
      "ip_address": "192.0.2.1"
    }
  }
  ```

### **4. Performance Considerations**
- **Avoid Over-Logging**: Use `DEBUG` sparingly; default to `INFO` in production.
- **Batch Writes**: For high-throughput services, aggregate logs and write in batches (e.g., every 1 second).
- **Sampling**: Use probabilistic sampling (e.g., 1% of `DEBUG` logs) for monitoring tools.

### **5. Integration with Monitoring**
- **Alerts**: Map error codes to alert rules (e.g., `DB-001` triggers a database health alert).
- **Dashboards**: Visualize error trends by code/module (e.g., Grafana panels).
- **SLOs**: Define **Service Level Objectives (SLOs)** based on error rates (e.g., "≤1% of requests return `500` errors").

---

## **Example Implementation (Python)**

```python
import logging
from uuid import uuid4
from typing import Dict, Optional

# Configure structured logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(trace_id)s %(module)s - %(message)s %(metadata)s',
    style='%'
)

class StructuredLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def log_error(
        self,
        error_code: str,
        message: str,
        metadata: Optional[Dict] = None,
        trace_id: Optional[str] = None
    ):
        """Log an error with structured conventions."""
        trace_id = trace_id or str(uuid4())
        metadata = metadata or {}

        # Enforce schema compliance
        assert error_code in [
            "400-001", "401-002", "500-001",  # Example codes
            "DB-001", "API-001"
        ], "Invalid error code"

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "ERROR",
            "trace_id": trace_id,
            "error_code": error_code,
            "message": message,
            "metadata": metadata
        }

        # Convert to JSON string for structured logging
        self.logger.error(
            json.dumps(log_entry),
            extra={
                "trace_id": trace_id,
                "metadata": metadata
            }
        )

# Usage
logger = StructuredLogger()
logger.log_error(
    error_code="DB-001",
    message="Duplicate primary key violation",
    metadata={"table": "users", "key": "email"},
    trace_id="existing-trace-id-123"
)
```

**Output Log**:
```json
2024-05-20 14:30:45,123 ERROR existing-trace-id-123 app - {"timestamp": "2024-05-20T14:30:45.123Z", "level": "ERROR", "trace_id": "existing-trace-id-123", "error_code": "DB-001", "message": "Duplicate primary key violation", "metadata": {"table": "users", "key": "email"}}
```

---

## **Troubleshooting**

| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Inconsistent Log Formats**        | Multiple services log in different schemas.                                    | Enforce a **global logging library** (e.g., custom Python library).          |
| **Missing Trace IDs**               | Distributed traces are uncorrelated.                                          | Auto-inject `trace_id` in middleware (e.g., Flask/Django middleware).       |
| **High Log Volume**                 | Debug logs overwhelm storage.                                                  | Implement **log level filtering** in production (disable `DEBUG`).           |
| **Error Codes Aren’t Actionable**    | Codes lack clear documentation.                                               | Maintain a **living codex** (e.g., GitHub Wiki) with escalation paths.      |
| **Performance Degradation**         | Heavy logging slows down the system.                                           | Use **async logging** (e.g., `aiohttp` for Python) or batch writes.         |

---

## **Tools & Libraries**

| **Tool/Library**       | **Purpose**                                                                 | **Example Use Case**                                  |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------------------|
| **Structured Logging** | Enforce schema consistency.                                                | `loguru`, `structlog` (Python)                       |
| **APM Agents**         | Correlate logs with traces.                                                 | Jaeger, OpenTelemetry                                |
| **Log Management**     | Centralize and query logs.                                                  | ELK Stack, Datadog, Honeycomb                         |
| **Error Tracking**     | Aggregate and prioritize errors.                                            | Sentry, Datadog Error Tracking                       |
| **Schema Validation**  | Enforce log structure.                                                      | `jsonschema`, `cerberus`                              |

---

## **Migration Checklist**

1. **Audit Existing Logs**:
   - Identify current log formats and error codes.
   - Document inconsistencies (e.g., mixed numeric/alphanumeric codes).

2. **Update Logging Libraries**:
   - Replace ad-hoc loggers with a structured solution (e.g., `structlog`).

3. **Define Error Codes**:
   - Create a **codex** with domain-specific codes.
   - Assign numeric equivalents for HTTP-like codes (e.g., `400` → `400-001`).

4. **Instrument Services**:
   - Add `trace_id` injection in API gateways.
   - Update service endpoints to propagate `trace_id`.

5. **Validate Backward Compatibility**:
   - Ensure existing monitoring tools can parse old logs.
   - Plan a **deprecation period** for non-compliant logs.

6. **Train Teams**:
   - Document conventions in the **engineering handbook**.
   - Conduct workshops on new logging patterns.

7. **Monitor Adoption**:
   - Track percentages of logs following the schema.
   - Alert on non-compliant log sources.

---

## **Further Reading**
- [RFC 5424: Syslog Protocol](https://tools.ietf.org/html/rfc5424) (Log standard).
- [OpenTelemetry Logs Specification](https://opentelemetry.io/docs/specs/otel/logs/).
- [Google’s SRE Book (Error Budgets)](https://sre.google/sre-book/error-budgets/).
- [AWS Well-Architected Logging Framework](https://aws.amazon.com/architecture/well-architected/logging/).