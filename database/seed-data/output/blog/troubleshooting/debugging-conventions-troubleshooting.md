# **Debugging Debugging Conventions: A Troubleshooting Guide**
*A practical guide for maintaining, debugging, and improving structured debugging patterns in codebases.*

---

## **1. Introduction**
Debugging Conventions refer to standardized ways of embedding diagnostic information, logging, error handling, and observability into code. These conventions ensure consistency across services, making troubleshooting faster and more reliable. When misapplied or missing, they can lead to confusing logs, undetected errors, and inefficiencies in debugging.

This guide helps you:
- Identify common issues with debugging conventions.
- Apply fixes efficiently.
- Use tools to validate and enforce conventions.
- Prevent future inconsistencies.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the problem. Check for:
✅ **Inconsistent Logging**
- Logs vary in format, severity, or scope.
- Some errors are logged as `INFO`, while critical issues are barely visible.

✅ **Missing Key Context**
- Logs lack method names, request IDs, or trace IDs.
- No timestamps or structured data (JSON vs. plain text).

✅ **Improper Error Handling**
- Exceptions are silently ignored, or generic messages are logged.
- No distinction between recoverable vs. fatal errors.

✅ **Performance Bottlenecks**
- Overhead from excessive logging or slow serialization.
- Debug logs slow down production systems.

✅ **Tooling Gaps**
- Logs not aggregatable (e.g., no correlation IDs).
- Metrics/errors not linked to traces in APM tools.

✅ **Configuration Drift**
- Debug levels differ across environments (`DEBUG` in Prod, `ERROR` in Staging).
- Logs are disabled in critical paths.

---

## **3. Common Issues & Fixes**

### **Issue 1: Inconsistent Logging Formats**
**Symptom:** Logs are hard to parse due to mixed formats.
**Example:**
```python
# Classic
print("User signed up: " + name)  # No structure

# Standardized
logger.info("User signed up", {"user_id": user.id, "event": "signup"})
```

**Fix:**
Use **structured logging** (JSON) with libraries like:
- **Python:** `structlog`, `logging` module
- **Java:** SLF4J + Logback
- **Go:** `slog` (stdlib) or `zap`
- **Node.js:** `pino`

**Code Example (Python):**
```python
import structlog

logger = structlog.get_logger()

# Before
logger.error("Failed to fetch data")

# After
logger.error("Failed to fetch data", extra={
    "error": str(exc),
    "context_id": request_id,
    "user_id": current_user.id
})
```
**Tooling Tip:** Use `jq` to filter logs dynamically:
```bash
jq '.message, .level, .error' access.log | less
```

---

### **Issue 2: Missing Trace Context**
**Symptom:** Debugging distributed systems without a trace ID.
**Example:**
```java
// Missing trace ID propagation
HttpClient.post("/api").then(...).catch(...);
```

**Fix: Propagate Context**
Use a **trace ID** (or correlation ID) across services:
1. Generate a trace ID at entry points.
2. Propagate it via headers:
   ```http
   X-Trace-ID: abc123-4567-890
   ```
3. Attach it to every log/metric.

**Code Example (Node.js):**
```javascript
import { trace } from 'trace-context';
const traceId = trace.getTraceparent()?.value || crypto.randomUUID();

app.use((req, res, next) => {
  req.traceId = traceId;
  next();
});

// In controllers/loggers
logger.info("Order failed", { traceId: req.traceId, error });
```
**Tools:**
- **OpenTelemetry** (standard for distributed tracing).
- **Jaeger/Zipkin** for visualization.

---

### **Issue 3: Silently Swallowed Errors**
**Symptom:** Exceptions are caught without logging or alerts.
**Example:**
```go
// Bad: Error goes unnoticed
if _, err := db.Query("SELECT * FROM users"); err != nil {
  // Do nothing
}
```

**Fix: Use Error Middleware/Handlers**
- Log **always**, alert on critical errors.
- Example (Python Flask):
```python
@app.errorhandler(Exception)
def handle_error(e):
    logger.critical(f"Unhandled error: {type(e).__name__}", exc_info=True)
    return jsonify({"error": "Internal server error"}), 500
```
- **Go:** Use `recover()` and structured logging.
```go
func handler(w http.ResponseWriter, r *http.Request) {
    defer func() {
        if err := recover(); err != nil {
            logger.Error("Panic caught", "error", err, "stack", debug.Stack())
        }
    }()
}
```

**Prevention:** Enforce error logging via **linting** (e.g., `eslint-plugin-error-logging` for JS).

---

### **Issue 4: Overhead from Debug Logs in Production**
**Symptom:** DEBUG logs slow down the system.
**Fix:**
- **Dynamic Log Levels:** Use environment variables.
  ```python
  import os
  LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
  logging.basicConfig(level=LOG_LEVEL)
  ```
- **Conditional Logging:** Avoid expensive ops in DEBUG.
  ```go
  if log.GetLevel() >= log.DEBUG {
      log.Debug().Str("data", expensiveCompute()).Msg("Debug data")
  }
  ```
- **Log Sampling:** For high-traffic systems (e.g., sample 1% of requests).

---

### **Issue 5: Broken Alerts on Errors**
**Symptom:** Critical errors trigger no alerts.
**Fix:**
- **Structured Alerts:** Use severity levels (e.g., `ERROR`, `CRITICAL`).
- **Tool Integration:**
  - **Prometheus + Alertmanager** for metrics-based alerts.
  - **Sentry/ErrorTracking** for crash reports.
  ```python
  # Sentry integration
  sentry_sdk.init(dsn="YOUR_DSN")
  sentry_sdk.set_tag("service", "user-service")
  sentry_sdk.capture_exception(exc)
  ```

---

## **4. Debugging Tools & Techniques**

### **A. Log Aggregation & Parsing**
- **ELK Stack (Elasticsearch + Logstash + Kibana):** Parse logs at scale.
- **Loki (Grafana):** Lightweight log aggregation.
- **AWS CloudWatch Logs:** Native integration for cloud apps.

**Example (Log Parsing with `awk`):**
```bash
# Extract error counts from logs
awk '/ERROR/{count++} END {print "Total errors:", count}' access.log > errors.txt
```

### **B. APM & Distributed Tracing**
- **OpenTelemetry:** Open-source standard for observability.
- **Datadog/New Relic:** Commercial APM tools.
- **Jaeger:** Open-source tracer.

**Example (OpenTelemetry Trace Setup):**
```python
# Python OpenTelemetry
from opentelemetry import trace
tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("fetch_user"):
    user = db.get_user(user_id)
```

### **C. Debugging Workflows**
1. **Reproduce:** Ensure logs are enabled (`LOG_LEVEL=DEBUG`).
2. **Filter:** Use `grep`/`jq` to narrow logs.
   ```bash
   grep -E "ERROR|traceId [a-f0-9]+" access.log
   ```
3. **Inspect Dependencies:** Check external API calls with `curl`/`Postman`.
4. **Code Walkthrough:** Use `breakpoint()` (Python) or `debugpy` for live debugging.

---

## **5. Prevention Strategies**

### **A. Enforce Consistency**
- **Logging Guidelines:**
  - Always log: `method`, `user`, `error`, `traceId`.
  - Avoid `debug` in production unless explicitly enabled.
- **Linting:**
  - Use `eslint`, `pylint`, or `Go lint` to enforce conventions.

**Example `.eslintrc` Rule:**
```json
{
  "rules": {
    "no-console": ["error", { "allow": ["warn", "error"] }],
    "log-level": ["error", { "required": ["error", "warn"] }]
  }
}
```

### **B. Automated Testing**
- **Unit Tests:** Verify log outputs.
  ```python
  def test_logger_output(capsys):
      logger.error("Failed task")
      captured = capsys.readouterr()
      assert "Failed task" in captured.out
  ```
- **Integration Tests:** Simulate error paths.

### **C. CI/CD Checks**
- **Pre-commit Hooks:** Validate logs before merge.
  ```bash
  # Example: Check for missing trace IDs
  grep -q "X-Trace-ID" *.py || exit 1
  ```
- **Deployment Checks:** Ensure `LOG_LEVEL` is set correctly.

### **D. Documentation**
- **Internal Wiki:** Document logging conventions (e.g., Confluence).
- **Code Comments:**
  ```python
  # LOGGING CONVENTION: Always include "transaction_id" in logs.
  logger.info("Payment processed", {"transaction_id": tx.id})
  ```

### **E. Monitoring & Alerts**
- **SLOs:** Set alert thresholds (e.g., "Error rate > 1%").
- **Synthetic Monitoring:** Use tools like **Pingdom** to test endpoints.

---

## **6. Key Takeaways**
| **Issue**               | **Quick Fix**                          | **Prevention Tool**          |
|-------------------------|----------------------------------------|------------------------------|
| Inconsistent logs       | Use structured logging (JSON).        | `structlog`, SLF4J, `pino`    |
| Missing trace IDs       | Propagate `X-Trace-ID` headers.        | OpenTelemetry                 |
| Silent exceptions       | Add error middleware/logging.         | `recover()`, `sentry-sdk`     |
| Overhead in production  | Set dynamic log levels.                | `LOG_LEVEL` env var           |
| No alerts               | Integrate Sentry/Prometheus.           | Alertmanager                  |

---

## **7. Further Reading**
- [Google’s Error Handling Guide](https://google.github.io/engineering-guides/sre/error-handling/)
- [OpenTelemetry Docs](https://opentelemetry.io/)
- [Structured Logging in Python](https://github.com/hynek/structlog)

---
**Final Tip:** Start with one service—audit its logs, fix the worst offenders, then expand. Consistency is key!