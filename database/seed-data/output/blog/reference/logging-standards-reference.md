**[Pattern] Logging Standards Reference Guide**
*Version: 1.0*
*Last Updated: [Insert Date]*

---

---
### **1. Overview**
**Logging Standards** is a foundational pattern that defines consistent, structured, and actionable logging practices across an application’s lifecycle. It ensures logs are machine-readable, context-rich, and optimized for observability, debugging, and compliance. This guide outlines schema requirements, implementation best practices, and query patterns for structured logging at scale.

---

---
### **2. Key Concepts**
#### **Core Principles**
- **Structured Logging**: Logs must follow a standardized schema (JSON by default) for parsability by SIEMs, monitoring tools, and custom query engines.
- **Hierarchical Context**: Logs should propagate contextual metadata (e.g., `user_id`, `correlation_id`) across requests to trace events.
- **Retention & Compliance**: Align logging with regulatory requirements (e.g., GDPR, HIPAA) via redaction and retention policies.
- **Performance**: Minimize overhead by avoiding large payloads or synchronous blocking operations (e.g., disk I/O).

#### **Log Types**
| Type               | Use Case                                                                 |
|--------------------|--------------------------------------------------------------------------|
| **Request Logs**   | Track HTTP/gRPC requests (methods, status codes, latency).               |
| **Error Logs**     | Capture exceptions, stack traces, and remediation steps.                 |
| **Audit Logs**     | Record security-sensitive actions (e.g., user logins, permission changes).|
| **Metrics Logs**   | Include counters/aggregates (e.g., `{"type": "counter", "value": 42}`).  |
| **Diagnostic Logs**| Developer-facing details (e.g., debug-level SQL queries).                 |

---

---
### **3. Schema Reference**
#### **Mandatory Fields**
| Field               | Type       | Description                                                                                     | Example Value                     |
|---------------------|------------|-------------------------------------------------------------------------------------------------|------------------------------------|
| `@timestamp`        | ISO 8601   | UTC timestamp with millisecond precision.                                                      | `2023-10-15T14:30:45.123Z`        |
| `level`             | String     | Severity level: `TRACE`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.                       | `"ERROR"`                          |
| `logger`            | String     | Component/class generating the log (e.g., `auth_service:user_validator`).                     | `"payment_service:checkout"`       |
| `message`           | String     | Human-readable summary (sanitized for logs < `WARNING`).                                       | `"Payment processing failed"`      |
| `correlation_id`    | UUID       | Unique identifier to trace cross-service requests.                                             | `"550e8400-e29b-41d4-a716-446655440000"` |
| `trace_id`          | UUID       | Distributed tracing ID (aligned with OpenTelemetry/W3C standards).                             | Same as `correlation_id`           |

#### **Conditional Fields**
| Field              | Type          | Description                                                                                     | Example Value                     |
|--------------------|---------------|-------------------------------------------------------------------------------------------------|------------------------------------|
| `error`            | Object        | Error details (mandatory for `level: ERROR`).                                                  | `{"code": 500, "type": "ValidationError"}` |
| `user`             | Object        | User metadata (redact if PII, ensure compliance).                                               | `{"id": "abc123", "roles": ["admin"]}` |
| `request`          | Object        | HTTP metadata (omit for non-web services).                                                     | `{"method": "POST", "path": "/api/pay"}` |
| `duration_ms`      | Integer       | End-to-end request latency (for `INFO`/`ERROR` levels).                                        | `125`                              |
| `tags`             | Array[String] | Key-value pairs for filtering (e.g., `{"env": "prod", "deployment": "v2"}`).                   | `["db:postgres", "feature:payments"]` |

#### **Example Log Payload**
```json
{
  "@timestamp": "2023-10-15T14:30:45.123Z",
  "level": "ERROR",
  "logger": "payment_service:checkout",
  "message": "Payment failed due to insufficient funds",
  "error": {
    "code": 402,
    "type": "PaymentError",
    "stack": "PaymentGateway::reject(...)"
  },
  "user": {
    "id": "abc123",
    "email": "[REDACTED]"  // Compliance: PII masked
  },
  "request": {
    "method": "POST",
    "path": "/api/pay",
    "id": "req_789"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "tags": ["currency:USD", "environment:production"]
}
```

---

---
### **4. Implementation Details**
#### **Tools & Libraries**
| Component          | Recommended Tools                                                                 |
|--------------------|-----------------------------------------------------------------------------------|
| **Logging Agents** | Elasticsearch-Beats, Fluentd, Logstash                                            |
| **Storage**        | Elasticsearch, Loki, AWS CloudWatch, Datadog                                        |
| **Structured Format** | JSON (default), Protobuf for high-throughput systems                              |
| **Runtime**        | Python: `structlog`, Java: SLF4J, Go: `zap`, Node.js: `Pino`                    |

#### **Best Practices**
1. **Avoid Log Spam**:
   - Use `DEBUG` logs sparingly; default to `INFO` for production.
   - Sample logs at `TRACE` level (e.g., every 10th request).
2. **Performance**:
   - Batch logs (e.g., `Fluentd` buffer mode) to reduce I/O.
   - Async loggers (e.g., Python’s `logging.handlers.AsyncHandler`).
3. **Security**:
   - Redact PII (use `{"email": "[REDACTED]"}`).
   - Encrypt sensitive logs at rest (e.g., KMS).
4. **Schema Validation**:
   - Use OpenAPI Schema or JSON Schema to validate logs before ingestion.
   - Example validator: [`jsonschema`](https://github.com/python-jsonschema/jsonschema).

#### **Common Pitfalls**
- **Over-Logging**: Include all fields in every log (e.g., `user` for `INFO` levels).
- **Inconsistent Timestamps**: Ensure `@timestamp` aligns with the event’s occurrence, not log generation.
- **Ignoring Retention**: Default retention (e.g., 30 days) may violate compliance (e.g., audit logs require 7+ years).

---

---
### **5. Query Examples**
#### **Basic Filtering**
**Query**: Find all `ERROR` logs for payment failures in the last 7 days.
```plaintext
@timestamp >= now()-7d AND level="ERROR" AND message="Payment failed"
```
**Tool**: Elasticsearch/Kibana, Loki, Datadog.

#### **Correlation Analysis**
**Query**: Trace a `correlation_id` across services.
```plaintext
correlation_id="550e8400-e29b-41d4-a716-446655440000" AND "service" IN ["auth", "payment", "notification"]
```
**Tool**: Custom dashboards (e.g., Grafana) or tracing tools (Jaeger).

#### **Metric Extraction**
**Query**: Count `ERROR` logs by `error.type` (e.g., for SLOs).
```plaintext
stats count by error.type WHERE level="ERROR" AND now()-1h
```
**Tool**: Metrics pipelines (e.g., Prometheus via log metrics).

#### **Compliance Audits**
**Query**: Find all `CRITICAL` logs with user PII (redaction check).
```plaintext
level="CRITICAL" AND NOT ("user.*": "[REDACTED]")
```
**Tool**: SIEM (e.g., Splunk).

---

---
### **6. Related Patterns**
| Pattern                  | Description                                                                                     | Integration Point                          |
|--------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------|
| **[Distributed Tracing]** | Correlate logs with trace spans for end-to-end debugging.                                     | Share `correlation_id`/`trace_id`.          |
| **[Circuit Breakers]**    | Log fallback mechanisms (e.g., `{"fallback": "cache"}`).                                       | Embed in `error` field.                    |
| **[Rate Limiting]**       | Log throttled requests (e.g., `{"type": "throttled", "limit": 100}`).                         | Include in `request` metadata.             |
| **[Observability Policy]**| Define SLOs/SLIs via logs (e.g., "99.9% of `ERROR` logs resolved within 1h").                 | Use `level`/`error.type` for dashboards.   |
| **[Secret Management]**   | Rotate log-sensitive keys (e.g., API tokens) without reprocessing old logs.                   | Avoid embedding `secrets` in logs.          |

---

---
### **7. References**
- **Standards**:
  - [W3C Trace Context](https://www.w3.org/TR/trace-context/)
  - [OpenTelemetry Logs Specification](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/logs/logs-examples.md)
- **Tools**:
  - [Elasticsearch Logging Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/logging.html)
  - [Google Cloud Logging](https://cloud.google.com/logging/docs/reference/v2/rest/v2/LogEntry)
- **Compliance**:
  - [GDPR Art. 32](https://gdpr-info.eu/art-32-gdpr/) (Security of Processing)
  - [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security-rule/index.html)

---
**Feedback**: Report schema gaps or tool-specific quirks to [#logging-standards] in Slack.