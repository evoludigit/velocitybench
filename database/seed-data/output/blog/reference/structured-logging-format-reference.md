# **[Pattern] Structured Logging Format Reference Guide**

---

## **1. Overview**
The **Structured Logging Format** pattern standardizes log entries as **JSON documents**, enabling efficient **aggregation, filtering, and analysis** across distributed systems. Unlike traditional text-based logs, this format ensures **machine-readability**, simplifies log parsing, and supports advanced querying tools (e.g., ELK Stack, Splunk, Datadog).

Key benefits:
- **Consistency**: Enforces uniform log structure across services.
- **Searchability**: Facilitates querying by fields (e.g., `status`, `user_id`).
- **Tooling Integration**: Works seamlessly with log analytics platforms.
- **Reduced Noise**: Excludes human-readable metadata (e.g., timestamps) from log content.

This guide covers the **JSON schema**, implementation best practices, and query examples for structured logs.

---

## **2. Schema Reference**
A structured log entry must include **mandatory** and **optional** fields. Below is the core schema:

| **Field**          | **Type**   | **Description**                                                                 | **Example Value**                     |
|--------------------|------------|---------------------------------------------------------------------------------|---------------------------------------|
| **`@timestamp`**   | `string`   | ISO-8601 formatted timestamp (RFC 3339). **Required**                           | `"2024-02-20T14:30:45.123Z"`         |
| **`@level`**       | `string`   | Log severity (e.g., `INFO`, `ERROR`, `DEBUG`). **Required**                     | `"ERROR"`                              |
| **`@service`**     | `string`   | Service name identifier (e.g., `auth-service`, `api-gateway`). **Required**     | `"payment-service"`                   |
| **`@version`**     | `string`   | Log format version (e.g., `1.0`). **Required**                                  | `"1.0"`                               |
| **`@correlation_id`** | `string`  | Unique request/trace ID for cross-service correlation. **Optional**              | `"req_1234abc"`                       |
| **`message`**      | `string`   | Human-readable log content (e.g., error descriptions). **Required**             | `"Invalid credentials for user: jdoe"` |
| **`context`**      | `object`   | Nested metadata (e.g., user details, request data). **Optional**                | `{ "user_id": "123", "ip": "192.0.2.1" }` |
| **`metadata`**     | `object`   | Additional key-value pairs (e.g., system stats). **Optional**                   | `{ "latency_ms": 420, "db": "postgres" }` |

---
### **Examples**
#### **Basic Log Entry**
```json
{
  "@timestamp": "2024-02-20T14:30:45.123Z",
  "@level": "ERROR",
  "@service": "auth-service",
  "@version": "1.0",
  "message": "Login failed: Invalid password",
  "context": { "user_id": "456", "ip": "203.0.113.45" }
}
```

#### **Complex Log with Nested Fields**
```json
{
  "@timestamp": "2024-02-20T14:35:00.000Z",
  "@level": "INFO",
  "@service": "api-gateway",
  "@version": "1.0",
  "@correlation_id": "req_4567xyz",
  "message": "Outbound call to payment-service succeeded",
  "metadata": {
    "latency_ms": 150,
    "caller": { "service": "frontend", "version": "v2" }
  }
}
```

---

## **3. Implementation Details**
### **3.1 Key Concepts**
- **Atomic Fields**: Prefixed with `@` (e.g., `@timestamp`) are **reserved** for core logging functionality.
- **Semantic Fields**: Custom fields (e.g., `context.user_id`) should be **self-documenting** (avoid `data` or `payload`).
- **Field Naming Conventions**:
  - Use **snake_case** (e.g., `user_id`, not `userID`).
  - Avoid spaces or special characters.
  - Prefix service-specific fields (e.g., `db.connection_pool_size`).

### **3.2 Tooling Integration**
| **Tool**       | **Integration Guide**                                                                 |
|-----------------|--------------------------------------------------------------------------------------|
| **ELK Stack**   | Use the `logstash-filter-json` plugin to parse JSON logs and index fields separately. |
| **Splunk**      | Configure the `sourcetype=json` and extract fields via `SPL` queries.                 |
| **Datadog**     | Enable JSON parsing in the **Log Processing** settings.                               |
| **AWS CloudWatch** | Use the `JSON` parsing format in Log Groups.                                           |

### **3.3 Validation**
Validate logs against the schema using:
- **JSON Schema**: Define a schema (e.g., [JSON Schema Validator](https://www.jsonschema.org/)).
- **OpenTelemetry**: Use the [OpenTelemetry Logs API](https://opentelemetry.io/docs/specs/otel/logs/) for structured logging.
- **Custom Scripts**: Python example:
  ```python
  import jsonschema
  schema = {...}  # Define schema here
  log_entry = {...}  # Load log data
  jsonschema.validate(instance=log_entry, schema=schema)
  ```

---

## **4. Query Examples**
### **4.1 Filtering by Severity**
**Query (ELK/Kibana):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "@level": "ERROR" } }
      ]
    }
  }
}
```
**Splunk Search:**
```
sourcetype=json @level=ERROR
```

### **4.2 Correlating Requests**
**Query (Datadog):**
```
logs @correlation_id="req_4567xyz" --service=api-gateway
```

### **4.3 Aggregating User Activity**
**Query (ELK/Aggregation):**
```json
{
  "aggs": {
    "users_by_status": {
      "terms": { "field": "context.user_id", "script": "_source['@level'] == 'ERROR'" }
    }
  }
}
```

### **4.4 Finding Slow Endpoints**
**Query (Splunk):**
```
sourcetype=json
| stats avg(metadata.latency_ms) as avg_latency BY context.endpoint
| where avg_latency > 500
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                  |
|----------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Centralized Logging**          | Aggregate logs from multiple services into a single system (e.g., ELK, Datadog).                  | When logs are distributed across microservices.   |
| **Structured Error Tracking**    | Extend structured logs with error IDs for debugging (e.g., Sentry integration).                 | For critical error monitoring.                    |
| **Log Sampling**                 | Reduce log volume by sampling (e.g., 1% of logs).                                                 | In high-throughput systems.                      |
| **Context Propagation**          | Correlate logs across services using trace IDs (e.g., OpenTelemetry).                            | In distributed traces.                           |
| **JSON vs. CSV Logs**             | Compare structured (JSON) vs. unstructured (CSV) formats for specific use cases.                   | Legacy systems may require CSV for legacy tools. |

---

## **6. Best Practices**
1. **Keep Logs Minimal**: Avoid logging sensitive data (e.g., PII, tokens).
2. **Consistent Timestamps**: Use UTC for `@timestamp` to avoid timezone issues.
3. **Field Naming**: Prefix with `@` for reserved fields (e.g., `@service`).
4. **Performance**: For high-volume systems, consider **async log flushing** (e.g., Buffering in Logback).
5. **Schema Evolution**: Use **backward-compatible** changes (e.g., add optional fields).
6. **Tool-Specific Optimizations**:
   - **Splunk**: Use `SPL` for complex extractions.
   - **ELK**: Leverage `painless` scripts for dynamic fields.
   - **Datadog**: Use `@service` for dashboard filtering.

---
## **7. Example Implementations**
### **7.1 Node.js (Winston)**
```javascript
const winston = require('winston');
const { combine, timestamp, printf, json } = winston.format;

const logger = winston.createLogger({
  formatter: combine(
    json(),  // Emit structured logs
    timestamp({ format: 'YYYY-MM-DDTHH:mm:ss.SSS[Z]' })
  ),
  transports: [new winston.transports.Console()]
});

logger.error('Failed login', { user_id: '123', ip: '192.0.2.1' });
```
**Output**:
```json
{"level":"error","message":"Failed login","user_id":"123","ip":"192.0.2.1","timestamp":"2024-02-20T14:30:45.123Z"}
```
*Note*: Manually add `@service` and other required fields.

### **7.2 Python (Python `logging`)**
```python
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("structured_logger")

def log_structured(message, **kwargs):
    log_entry = {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "@level": logger.levelName,
        "@service": "python-service",
        "@version": "1.0",
        "message": message,
        **kwargs  # Merge custom fields
    }
    print(json.dumps(log_entry))

log_structured("User deleted", user_id="456", action="delete")
```
**Output**:
```json
{
  "@timestamp": "2024-02-20T14:30:45.123Z",
  "@level": "INFO",
  "@service": "python-service",
  "@version": "1.0",
  "message": "User deleted",
  "user_id": "456",
  "action": "delete"
}
```

---

## **8. Troubleshooting**
| **Issue**                          | **Solution**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------------------------|
| **Malformed JSON**                  | Use a validator (e.g., [JSONLint](https://jsonlint.com/)) to debug syntax errors.             |
| **Missing Fields**                  | Enforce schema validation during log generation (e.g., OpenTelemetry).                        |
| **Performance Overhead**            | Use async loggers (e.g., Python `QueueHandler`) or buffering.                                  |
| **Correlation Failures**            | Ensure `@correlation_id` is propagated across services (e.g., headers in HTTP requests).       |
| **Tool Compatibility Issues**        | Check vendor-specific guidelines (e.g., Splunk field extractions).                              |

---
## **9. Further Reading**
- [OpenTelemetry Logs Specification](https://opentelemetry.io/docs/specs/otel/logs/)
- [ELK Stack JSON Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/json-logging.html)
- [Splunk JSON Parsing](https://docs.splunk.com/Documentation/Splunk/latest/Data/ParseJSON)
- [Datadog Structured Logging](https://docs.datadoghq.com/logs/log_configuration/structured_logs/)