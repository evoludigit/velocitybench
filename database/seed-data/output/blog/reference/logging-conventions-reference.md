# **[Pattern] Logging Conventions Reference Guide**

---

## **Overview**
Effective logging is critical for observability, debugging, and diagnostics in distributed systems. The **Logging Conventions** pattern ensures consistency, readability, and actionability in log entries across services. This pattern defines standardized structure, key fields, and formatting rules to simplify log parsing, correlation, and analysis.

Key benefits include:
✔ **Standardized output** – Logs across services follow a predictable format.
✔ **Efficient debugging** – Critical values (timestamps, requests, errors) are easily extractable.
✔ **Tooling-friendly** – Logs are machine-readable and compatible with SIEM, ELK, and other observability tools.
✔ **Traceability** – Contextual information (e.g., request IDs, user sessions) enables correlation across microservices.

This guide outlines the recommended fields, schema, and usage patterns for logging conventions in a distributed system.

---

## **Implementation Details**

### **1. Core Log Fields**
Every log entry must include the following **mandatory** fields to ensure consistency:

| **Field Name**       | **Type**       | **Description**                                                                                     | **Example Value**                          |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `timestamp`          | ISO 8601      | Log entry timestamp (UTC). Must be in `YYYY-MM-DDTHH:mm:ss.sssZ` format.                          | `2024-02-20T14:30:45.123Z`                |
| `level`              | String        | Log severity: `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`.                              | `"ERROR"`                                  |
| `service`            | String        | Name of the service generating the log (e.g., `auth-service`, `order-api`).                       | `"payment-service"`                        |
| `component`          | String        | Sub-component within the service (e.g., `controller`, `repository`, `cache`).                     | `"auth.controller.user"`                   |
| `request_id`         | String (UUID) | Unique identifier for the current request (correlation ID for distributed tracing).              | `"550e8400-e29b-41d4-a716-446655440000"`   |
| `user_id`            | String (UUID) | User’s session ID (if applicable). Omits for anonymous users.                                     | `"a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8o"`   |
| `trace_id`           | String (UUID) | Root trace ID for distributed tracing (if available).                                               | `"12345678-90ab-cdef-1234-56789abcdef0"`   |
| `span_id`            | String (UUID) | Current operation’s span ID (for distributed tracing).                                              | `"87654321-09ab-cdef-4321-56789abcdef1"`   |
| `context`            | JSON Object   | Dynamic key-value pairs for request-specific data (e.g., `user: { name: "Alice" }`).              | `{"user": {"name": "Alice", "role": "admin"}}` |

### **2. Optional Fields**
Enhance logs with context-sensitive data when relevant:

| **Field Name**       | **Type**       | **Description**                                                                                     | **Example Value**                          |
|----------------------|---------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `method`             | String        | HTTP method (for API services).                                                                     | `"POST"`                                   |
| `path`               | String        | Requested endpoint path.                                                                             | `"/api/v1/users/profile"`                  |
| `status`             | Integer       | HTTP status code (for API services).                                                                  | `200`                                      |
| `duration_ms`        | Float         | Execution time in milliseconds.                                                                    | `42.5`                                     |
| `error`              | String        | Error message (if applicable).                                                                       | `"Database connection timeout"`             |
| `stack_trace`        | String        | Full stack trace (for `ERROR`/`CRITICAL` levels).                                                   | `[...truncated stack trace...]`            |
| `payload`            | JSON Object   | Raw request/response payload (sanitized for PII).                                                   | `{"data": {"id": 123}}`                    |
| `tags`               | Array         | Custom metadata (e.g., `["high-priority", "user-action"]`).                                          | `["user-login", "failed-attempt"]`         |

---

## **Schema Reference**
Below is the **recommended JSON schema** for log entries. Tools like OpenTelemetry, Fluentd, or custom log parsers can validate logs against this schema.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Logging Conventions Schema",
  "type": "object",
  "required": ["timestamp", "level", "service", "component", "request_id"],
  "properties": {
    "timestamp": { "type": "string", "format": "date-time" },
    "level": {
      "type": "string",
      "enum": ["TRACE", "DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
    },
    "service": { "type": "string", "minLength": 1 },
    "component": { "type": "string", "minLength": 1 },
    "request_id": { "type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" },
    "user_id": { "type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" },
    "trace_id": { "type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" },
    "span_id": { "type": "string", "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" },
    "context": { "type": "object" },
    "method": { "type": "string" },
    "path": { "type": "string" },
    "status": { "type": "integer", "minimum": 100, "maximum": 599 },
    "duration_ms": { "type": "number", "minimum": 0 },
    "error": { "type": "string" },
    "stack_trace": { "type": "string" },
    "payload": { "type": "object" },
    "tags": { "type": "array", "items": { "type": "string" } }
  },
  "additionalProperties": false
}
```

---

## **Query Examples**
Below are **Grok patterns** and **query examples** for common log analysis tools:

### **1. ELK Stack (Kibana Discover)**
**Grok Pattern:**
```plaintext
%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:service} %{DATA:component} \[%{UUID:request_id}\] %{OPTIONAL:user_id} %{OPTIONAL:trace_id} %{OPTIONAL:span_id} - %{GREEDYDATA:context}
```

**Query Example:**
```plaintext
service:"payment-service" AND level:"ERROR" AND "Database connection timeout"
```

### **2. Prometheus Log Querying**
**Label Extraction:**
```plaintext
{level="ERROR", service="auth-service", request_id="550e8400-e29b-41d4-a716-446655440000"}
```

**Count Errors by Component:**
```plaintext
count(up{job="logging-metrics"} AND on(level, service) level="ERROR" GROUP BY (component))
```

### **3. AWS CloudWatch Logs Insights**
**Filter for Critical Failures:**
```plaintext
fields @timestamp, @message
| filter level = "CRITICAL"
| sort @timestamp desc
| limit 50
```

**Group by User ID:**
```plaintext
fields user_id, @message
| stats count(*) as error_count by user_id
| filter error_count > 3
```

---

## **Related Patterns**
To complement **Logging Conventions**, consider integrating these patterns:

1. **[Distributed Tracing](https://example.com/distributed-tracing)**
   - Use `trace_id`/`span_id` fields to correlate logs with trace data (e.g., OpenTelemetry).

2. **[Structured Logging](https://example.com/structured-logging)**
   - Enforce JSON logs for tooling compatibility (e.g., Fluentd, Loki).

3. **[Observability with Metrics](https://example.com/observability-metrics)**
   - Supplement logs with metrics (e.g., `latency`, `error_rate`) for SLO/SLI tracking.

4. **[Log Sampling](https://example.com/log-sampling)**
   - Apply sampling strategies (e.g., `1% of ERROR logs`) to reduce volume in high-traffic systems.

5. **[Audit Logging](https://example.com/audit-logging)**
   - Extend logging conventions for compliance (e.g., add `event_type: "authentication"`).

---

## **Best Practices**
1. **Sanitize Sensitive Data**
   - Omit or mask PII (e.g., passwords, credit cards) in `payload` fields.
   - Use `user_id` instead of full names where possible.

2. **Avoid Log Spam**
   - Use `TRACE`/`DEBUG` sparingly; default to `INFO`/`WARN` for production.

3. **Standardize Severity Levels**
   - Align `level` values with monitoring thresholds (e.g., alert on `ERROR`/`CRITICAL`).

4. **Tooling Integration**
   - Validate logs against the schema using tools like:
     - [JSON Schema](https://json-schema.org/)
     - [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
     - [Loki](https://grafana.com/oss/loki/) (for log aggregation).

5. **Backward Compatibility**
   - Maintain legacy log formats if migrating slowly; add a `format_version` field.

---
**Example Log Entry:**
```json
{
  "timestamp": "2024-02-20T14:30:45.123Z",
  "level": "ERROR",
  "service": "order-service",
  "component": "payment.gateway",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "12345678-90ab-cdef-1234-56789abcdef0",
  "span_id": "87654321-09ab-cdef-4321-56789abcdef1",
  "error": "Payment gateway timeout",
  "status": 504,
  "duration_ms": 3000,
  "context": {
    "user": { "id": "a1b2c3d4...", "email": "[REDACTED]" },
    "payment": { "amount": 99.99, "currency": "USD" }
  },
  "tags": ["timeout", "user-payment"]
}
```