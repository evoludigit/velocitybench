# **[Pattern] Logging & Debugging Reference Guide**

---

## **Overview**
The **Logging & Debugging** pattern provides structured, context-rich logs that enable developers and operators to diagnose issues, trace execution flow, and monitor system behavior. Unlike raw console logs, this pattern enforces consistency in log formatting, categorization, and metadata inclusion, ensuring logs are both **machine-readable** (for automated analysis) and **human-readable** (for manual troubleshooting).

This guide outlines best practices for implementing a robust logging system, including log levels, schema standards, query techniques, and integration with debugging tools.

---

## **Key Concepts**

| Concept               | Description |
|-----------------------|------------|
| **Log Level**         | Severity marker (e.g., `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`). Determines log retention and visibility. |
| **Structured Logging**| Logs formatted as JSON/schema (e.g., `{timestamp, level, message, context, traceId}`), enabling filtering and analysis. |
| **Contextual Data**   | Metadata (e.g., `userId`, `requestId`, `serviceName`) to correlate logs across distributed systems. |
| **Trace IDs**         | Unique identifiers to match logs across services in a distributed trace. |
| **Log Rotations**     | Policies for log file cleanup (e.g., daily/retention limits) to manage storage. |
| **Sensitive Data**    | Exclusion of PII/credentials (redacted or excluded via policies). |
| **Debugging Tools**   | Integration with APM (e.g., Datadog, New Relic) or custom dashboards for log analysis. |

---

## **Implementation Schema Reference**

### **Core Log Structure**
| Field          | Type       | Description                                                                 | Example Value                     |
|----------------|------------|-----------------------------------------------------------------------------|-----------------------------------|
| `timestamp`    | ISO-8601   | Log emission time in UTC.                                                   | `"2024-05-20T14:30:45Z"`         |
| `level`        | Enum       | Log severity (see **Log Levels** section below).                           | `"ERROR"`                         |
| `message`      | String     | Human-readable event description.                                          | `"Failed to connect to DB"`       |
| `service`      | String     | Name of the emitting service/module.                                       | `"user-auth-service"`             |
| `traceId`      | UUID       | Correlation ID for distributed tracing.                                     | `"a1b2c3d4-e5f6-7890-g1h2-i3j4k5"`|
| `requestId`    | String     | Unique ID for the current HTTP request (if applicable).                    | `"req-1234"`                      |
| `userId`       | String     | User identifier (if logged-in; redact if PII).                            | `"user-5678"`                     |
| `error`        | Struct     | Optional: Stack trace, error code, or detailed error metadata.             | `{"code": 500, "stack": "..."}`   |
| `context`      | Object     | Key-value pairs for additional debugging context.                           | `{"query": "SELECT * FROM users"}`|

### **Log Levels**
| Level   | Usage                                                                 |
|---------|-----------------------------------------------------------------------|
| `TRACE` | Extremely detailed debug info (e.g., SQL queries, internal state).       |
| `DEBUG` | Debug-specific details (e.g., function entry/exit, variable values).   |
| `INFO`  | Normal operational messages (e.g., service startup, successful requests).|
| `WARN`  | Potential issues (e.g., retrying a failed operation).                 |
| `ERROR` | Failed operations with recoverable/critical implications.             |
| `FATAL` | System-critical failures (e.g., crashes, data corruption).              |

---
## **Implementation Steps**

### **1. Log Initialization**
Initialize a logger with a structured format. Example (Python with `structlog`):
```python
import structlog

logger = structlog.get_logger()
logger.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
```

### **2. Structured Logging**
Log with contextual data:
```python
logger.debug(
    "Processing user request",
    user_id=current_user.id,
    request_id=generate_request_id(),
    context={"action": "update_profile"}
)
```

### **3. Error Handling**
Log errors with stack traces:
```python
try:
    db.query("SELECT * FROM users")
except Exception as e:
    logger.error(
        "Database query failed",
        error={"code": 500, "stack": traceback.format_exc()},
        trace_id=generate_trace_id()
    )
```

### **4. Trace Correlation**
Assign a `traceId` to log entries to correlate across services:
```python
trace_id = generate_trace_id()  # UUID or similar
logger.info("Initiating transaction", trace_id=trace_id)
# ... logic ...
logger.debug("Transaction committed", trace_id=trace_id)
```

### **5. Log Rotation & Retention**
Configure log rotation (e.g., via `logrotate` or cloud provider settings):
```
```
/var/log/app/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 app-user app-group
}
```

---

## **Query Examples**
### **1. Filtering by Severity**
```sql
-- In a log analysis tool (e.g., ELK/CloudWatch):
SELECT * FROM logs
WHERE level = 'ERROR'
AND timestamp > '2024-05-20T00:00:00Z'
LIMIT 100;
```

### **2. Correlating Distributed Logs**
```sql
-- Find all logs for a specific traceId:
SELECT * FROM logs
WHERE traceId = 'a1b2c3d4-e5f6-7890-g1h2-i3j4k5'
ORDER BY timestamp;
```

### **3. Debugging a Failed Request**
```sql
-- Identify failed requests with userId:
SELECT *
FROM logs
WHERE level = 'ERROR'
AND userId = 'user-5678'
AND message LIKE '%Failed%';
```

### **4. Analyzing Query Performance**
```sql
-- Find slow database queries (TRACE level):
SELECT *
FROM logs
WHERE level = 'TRACE'
AND message LIKE '%query%'
AND duration_ms > 1000;
```

---

## **Related Patterns**

| Pattern                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| **[Distributed Tracing]**        | Complements logging by providing end-to-end request latency and dependency maps. |
| **[Circuit Breaker]**             | Logs integration failures; debugging aids in identifying flaky services.    |
| **[Observability with Metrics]**  | Combines logs, metrics, and traces for holistic system analysis.            |
| **[Idempotency Keys]**            | Logs with `requestId` ensure deduplication of identical operations.         |
| **[Feature Flags]**               | Logs enable debugging of flagged vs. unflagged user flows.                  |

---
## **Best Practices**
1. **Avoid Logging Sensitive Data**: Redact PII, tokens, or passwords.
2. **Limit TRACE/DEBUG in Production**: Disable in non-debug builds.
3. **Use Standardized Fields**: Align with your organization’s schema (e.g., `service`, `traceId`).
4. **Log Correlators**: Always include `traceId`/`requestId` in distributed systems.
5. **Compress & Archive**: Use tools like `logrotate` or cloud storage (S3/Blob) for retention.
6. **Automate Alerts**: Set up rules for `ERROR`/`FATAL` logs (e.g., PagerDuty/Slack).
7. **Test Logs**: Verify log output in staging before production deployment.

---
## **Tools & Libraries**
| Tool/Library          | Purpose                                                                 |
|-----------------------|-------------------------------------------------------------------------|
| `structlog` (Python)  | Structured logging with Python.                                         |
| `Winston` (Node.js)   | Flexible logging for JavaScript.                                        |
| `Logstash`            | Ship, parse, and analyze logs at scale.                                  |
| `Prometheus`          | Metrics + logs integration (via `logs` exporter).                        |
| `OpenTelemetry`       | Standardized tracing/logging/metrics.                                    |
| `Sentry`              | Error tracking with contextual logs.                                     |

---
## **Example Workflow**
1. **User Submits Request**: `requestId` and `traceId` generated.
2. **Service Logs**:
   ```json
   {
     "timestamp": "2024-05-20T14:30:45Z",
     "level": "INFO",
     "message": "Processing payment",
     "service": "payment-service",
     "traceId": "a1b2c3...",
     "requestId": "req-1234",
     "userId": "user-5678",
     "context": {"amount": 99.99, "currency": "USD"}
   }
   ```
3. **Database Fails**: `ERROR` log with stack trace.
4. **Operator Queries**:
   ```sql
   -- Find the root cause:
   SELECT * FROM logs
   WHERE traceId = 'a1b2c3...'
   ORDER BY timestamp;
   ```
5. **Alert Triggers**: `ERROR` log for `payment-service` triggers a PagerDuty alert.

---
## **Anti-Patterns**
| **❌ Anti-Pattern**               | **Risk**                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| Logging raw exception objects     | Can expose sensitive data (e.g., passwords in `str(e)`).                 |
| No log levels                     | Hard to filter critical messages from noise.                             |
| Missing traceIds                 | Impossible to correlate logs across services.                            |
| Over-logging in production       | Inflates storage costs and slows down systems.                           |
| Static log files                  | No retention policy → disk exhaustion.                                  |
| Ignoring PII in logs              | Compliance violations (GDPR, HIPAA).                                     |