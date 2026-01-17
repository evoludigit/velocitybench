---
# **[Logging Patterns] Reference Guide**
*Structured, Consistent, and Actionable Logging for Debugging, Monitoring, and Observability*

---

## **1. Overview**
**Logging Patterns** define standardized structures for log messages to ensure consistency, readability, and machine-parsability. They improve debugging, observability, and automation by enforcing uniform log formatting across applications. Key benefits include:
- **Machine-friendly logs** (JSON, structured text) for analytics and parsing.
- **Reduced noise** via structured metadata (timestamps, severity, context).
- **Standardized querying** across distributed systems.
- **Compliance-friendly** auditing with traceable metadata.

This guide covers best practices for implementing logging patterns in microservices, monoliths, and cloud-native environments. Adopted by teams using **Serilog (C#), Structured Logging (Python/Java)**, and cloud providers (AWS CloudWatch, Azure Monitor).

---

## **2. Schema Reference**
A **logging pattern** comprises **core fields** (mandatory) and **contextual fields** (optional). Use tables below as a reference schema.

### **Core Fields (Required)**
| Field Name        | Type       | Description                                                                                     | Example Value                     |
|-------------------|------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `@timestamp`      | ISO 8601   | RFC 3339-compliant timestamp (UTC).                                                           | `2024-05-20T14:30:45.123Z`       |
| `level`           | String     | Severity level (DEBUG, INFO, WARN, ERROR, FATAL).                                             | `"ERROR"`                         |
| `service`         | String     | Unique identifier for the service/application.                                                 | `"order-service"`                 |
| `trace_id`        | UUID       | Correlates logs across distributed transactions (e.g., microservices).                          | `"a1b2c3d4-e5f6-7890-g1h2-i3j4k5"`|
| `span_id`         | UUID       | Individual request/operation id (for distributed tracing).                                      | `"b2c3d4e5-f6g7-890h-i1j2-k3l4"`  |

---

### **Contextual Fields (Recommended)**
| Field Name        | Type       | Description                                                                                     | Example Value                     |
|-------------------|------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `user_id`         | String     | User identifier (for identity-based logging).                                                   | `"usr-76543"`                     |
| `request_id`      | String     | HTTP request trace identifier.                                                                 | `"req-xyz-12345"`                 |
| `method`          | String     | HTTP method (GET, POST, etc.).                                                                   | `"POST"`                          |
| `path`            | String     | Request path (for APIs).                                                                       | `"/api/v1/orders"`                |
| `status_code`     | Integer    | HTTP status code (e.g., 200, 404).                                                               | `404`                             |
| `error`           | String     | Human-readable error message (sanitized).                                                       | `"Invalid payment token"`          |
| `metadata`        | JSON       | Free-form key-value pairs for additional context (e.g., `{"db": "postgres"}`).                 | `{"env":"prod","version":"1.2.0"}`|

---
### **Example Structured Log**
```json
{
  "@timestamp": "2024-05-20T14:30:45.123Z",
  "level": "ERROR",
  "service": "inventory-service",
  "trace_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5",
  "user_id": "usr-76543",
  "status_code": 500,
  "error": "Database connection failed",
  "metadata": {
    "db": "mongodb",
    "version": "2.1.0",
    "retry_count": 3
  }
}
```

---

## **3. Implementation Details**
### **3.1. Choosing a Logging Framework**
| Framework         | Language  | Notes                                                                                     |
|-------------------|-----------|-------------------------------------------------------------------------------------------|
| **Serilog**       | C#        | Supports structured logging with `Log.ForContext()`.                                      |
| **StructuredLog** | Python    | Uses `structlog` for JSON output.                                                      |
| **Log4j/SLF4J**   | Java      | Configured via MDC (Mapped Diagnostic Context).                                         |
| **AWS CloudWatch**| Cloud     | Auto-instrumentation for Lambda applications.                                           |
| **OpenTelemetry** | Multi-lang | Integrates with distributed tracing (e.g., Jaeger).                                      |

---
### **3.2. Key Implementation Steps**
1. **Enable Structured Logging**
   - Use frameworks that natively support JSON (e.g., `structlog`, Serilog).
   - Avoid plain-text logs; prioritize parsable formats.

2. **Correlate Logs via Trace/Span IDs**
   - Generate unique `trace_id`/`span_id` at request entry.
   - Propagate IDs across services using headers (e.g., `X-Trace-ID`).

3. **Sanitize Sensitive Data**
   - Exclude PII (Personally Identifiable Information) from logs (e.g., passwords, tokens).
   - Use dynamic redaction (e.g., `Log.Error("Login failed: {Password}", redacted: true)`).

4. **Include Contextual Metadata**
   - Add `service`, `environment`, and `version` for environment differentiation.
   - Use `metadata` for ephemeral data (e.g., `{"user_ip": "192.168.1.1"}`).

5. **Standardize Severity Levels**
   - Follow [RFC 5424](https://tools.ietf.org/html/rfc5424) for consistency.
   - Example hierarchy: `DEBUG < INFO < WARN < ERROR < FATAL`.

6. **Optimize Log Volume**
   - Avoid verbose `DEBUG` logs in production.
   - Use log levels dynamically (e.g., `os.getenv("LOG_LEVEL")`).

---

### **3.3. Example Code Snippets**
#### **C# (Serilog)**
```csharp
using Serilog;

Log.Logger = new LoggerConfiguration()
    .WriteTo.Console(outputTemplate: "[{@timestamp:yyyy-MM-dd HH:mm:ss} {Level}] {Message}{NewLine}{Exception}")
    .CreateLogger();

Log.Information("User {UserId} accessed {Path}", userId: "usr-76543", path: "/dashboard");

Log.ForContext("UserId", "usr-76543")
    .ForContext("RequestId", "req-xyz-12345")
    .Error("Failed to process order");
```

#### **Python (StructLog)**
```python
import structlog
from structlog.stdlib import LoggerFactory

logger = structlog.stdlib.create_logger(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)

logger.info("user_login", user_id="usr-76543", status_code=200)
logger.error("database_error", db="postgres", error="Connection timeout")
```

#### **Java (Log4j)**
```xml
<!-- log4j2.xml -->
<Configuration>
  <Appenders>
    <JSON name="JSONAppender" fileName="app.log">
      <ContextData>
        <KeyValue pair="service" value="user-service"/>
      </ContextData>
    </JSON>
  </Appenders>
  <Loggers>
    <Logger name="com.example" level="error" additivity="false">
      <AppenderRef ref="JSONAppender"/>
    </Logger>
  </Loggers>
</Configuration>
```

---

## **4. Query Examples**
Leverage structured logs to query efficiently. Below are **Lucidworks Fusion**, **Grafana**, or **AWS Athena** examples.

### **4.1. Find Errors in a Service**
```sql
SELECT *
FROM logs
WHERE service = 'order-service'
  AND level = 'ERROR'
  AND "@timestamp" > '2024-05-20T00:00:00Z'
ORDER BY "@timestamp" DESC
LIMIT 100;
```

### **4.2. Trace a User’s Request**
```sql
SELECT *
FROM logs
WHERE trace_id = 'a1b2c3d4-e5f6-7890-g1h2-i3j4k5'
ORDER BY "@timestamp";
```

### **4.3. Count Failed Payments**
```sql
SELECT
    status_code,
    COUNT(*) as failure_count
FROM logs
WHERE error LIKE '%payment%'
  AND level = 'ERROR'
GROUP BY status_code;
```

### **4.4. Filter by Environment**
```sql
SELECT *
FROM logs
WHERE metadata->>'env' = 'production'
  AND level IN ('WARN', 'ERROR');
```

---

## **5. Related Patterns**
| Pattern Name               | Description                                                                                     | When to Use                                  |
|----------------------------|----------------------------------------------------------------                                 |----------------------------------------------|
| **Distributed Tracing**    | Correlate logs with traces (e.g., Jaeger, OpenTelemetry) for end-to-end request analysis.     | Microservices architecture.                 |
| **Log Retention Policy**   | Define rules for log cleanup (e.g., 30 days for DEBUG, 1 year for ERROR).                    | Compliance requirements.                    |
| **Anomaly Detection**      | Use ML models (e.g., ELK Stack) to flag unusual log patterns (e.g., sudden ERROR spikes).      | Production monitoring.                       |
| **Log Shipping**           | Centralize logs in a SIEM (e.g., Splunk, Datadog) for cross-service analysis.                 | Large-scale applications.                   |
| **Structured Error Handling** | Format errors consistently with stack traces, root causes, and suggested fixes.             | Debugging complex failures.                  |

---

## **6. Best Practices**
1. **Consistency**: Apply the same schema across all services.
2. **Minimize Overhead**: Avoid logging large objects (e.g., entire request/response payloads).
3. **Retention**: Archive logs to cold storage (e.g., S3) after active analysis.
4. **Tooling**: Use log management tools (e.g., **ELK Stack**, **Loki**, **CloudWatch**) for querying.
5. **Documentation**: Maintain a **logging schema reference** for onboarding new teams.

---
## **7. Common Pitfalls**
| Pitfall                          | Solution                                                                                     |
|-----------------------------------|---------------------------------------------------------------------------------------------|
| **Inconsistent Formatting**       | Enforce schema validation (e.g., via OpenTelemetry).                                      |
| **Over-Logging**                  | Use log levels judiciously; avoid `DEBUG` in production.                                    |
| **Missing Correlations**          | Always include `trace_id`/`span_id` for distributed requests.                               |
| **Sensitive Data Leaks**          | Redact PII dynamically (e.g., `***-****-1234`).                                            |
| **Vendor Lock-in**                | Use open standards (e.g., OpenTelemetry) instead of proprietary formats.                    |

---
## **8. Further Reading**
- [OpenTelemetry Logs Specification](https://github.com/open-telemetry/opentelemetry-specification/tree/main/specification/logs)
- [Serilog Structured Logging](https://serilog.net/docs/usage/structured-data/)
- [StructLog Python Documentation](https://www.structlog.org/en/stable/)
- [AWS CloudWatch Logs Best Practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/LogInsight-QueryExamples.html)