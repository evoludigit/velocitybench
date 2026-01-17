# **[Pattern] Reference Guide: Logging Techniques**

---

## **Overview**
Logging is a critical practice for debugging, monitoring, and auditing applications. This guide outlines structured and best-practice approaches to logging, covering techniques for different scenarios, log formats, retention policies, and integration with observability tools. The techniques described herein ensure logs are **structured**, **actionable**, and **scalable** while adhering to security and compliance standards.

---

## **Key Concepts**

### **1. Log Levels & Severity**
Define the severity of log entries to prioritize debugging efforts.

| **Level**       | **Purpose**                                                                 | **Example Use Case**                     |
|-----------------|-----------------------------------------------------------------------------|------------------------------------------|
| **TRACE**       | Detailed debugging info (lowest priority).                                  | API request/response parsing.            |
| **DEBUG**       | Step-by-step execution tracking.                                            | User session state changes.              |
| **INFO**        | General operational status updates.                                         | Service startup/shutdown events.         |
| **WARN**        | Potential issues (non-critical but noteworthy).                             | Throttled API calls.                     |
| **ERROR**       | Critical failures that may require manual intervention.                     | Database connection failures.            |
| **FATAL**       | System-critical failures leading to application crash.                      | Out-of-memory errors.                    |

**Best Practice:**
- Avoid logging `TRACE` in production.
- Use `INFO` for expected user flows; `WARN`/`ERROR` for anomalies.

---

### **2. Structured Logging**
Replace unstructured text logs with **JSON/key-value pairs** for easier parsing and querying.

**Example (JSON):**
```json
{
  "timestamp": "2024-05-20T14:30:00Z",
  "level": "ERROR",
  "service": "payment-processor",
  "request_id": "req_123abc",
  "user_id": "usr_456xyz",
  "message": "Insufficient funds",
  "context": {
    "amount": 1000,
    "balance": 500,
    "transaction": "purchase_789"
  }
}
```
**Tools:**
- **Logback** (Java), **Serilog** (C#), **structlog** (Python).

---

### **3. Log Enrichment**
Add context to logs dynamically (e.g., user IDs, request headers).

**Example (Python with `structlog`):**
```python
import structlog

logger = structlog.get_logger()
logger.info("User logged in", user_id="1001", ip="192.168.1.1")
```
**Output:**
```json
{
  "event": "User logged in",
  "user_id": "1001",
  "ip": "192.168.1.1",
  "timestamp": "2024-05-20T14:30:00Z"
}
```

---

### **4. Log Retention & Rotation**
Prevent disk space exhaustion with policies based on **size/time**.

| **Policy**       | **Description**                                                                 | **Example**                          |
|------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Daily Rotation** | Split logs by date (e.g., `app.log.2024-05-20`).                               | `logrotate` (Linux).                 |
| **Size-Based**   | Archive files when exceeding a threshold (e.g., 100MB).                      | `logback.xml` (Java).                |
| **TTL (Time-to-Live)** | Auto-delete logs older than `N` days (e.g., 30 days).                        | AWS CloudWatch Logs.                 |

**Best Practice:**
- Retain **ERROR** logs indefinitely; rotate others aggressively.

---

### **5. Asynchronous Logging**
Avoid blocking application threads with slow I/O.

**Implementations:**
- **Buffering:** Queue logs and flush periodically.
  ```python
  logger = structlog.stdlib.LoggerFactory().bind(log_level="INFO")
  logger.info("Slow operation")  # Async via `structlog.stdlib.processor.StackInfo`
  ```
- **Dedicated Workers:** Use Kafka/ELK for log ingestion.

---

### **6. Sensitive Data Handling**
Secure logs by:
- **Redacting** PII (e.g., passwords, tokens).
  ```python
  import re
  log_entry = re.sub(r"password=.*", "password=[REDACTED]", log_entry)
  ```
- **Encrypting** logs at rest (e.g., AWS KMS).

---

### **7. Log Aggregation & Centralization**
Collect logs from multiple sources into a single system.

| **Tool**         | **Use Case**                                      | **Features**                          |
|------------------|--------------------------------------------------|----------------------------------------|
| **ELK Stack**    | Full-text search, visualization.                 | Kibana dashboards.                     |
| **Fluentd/FluentBit** | Lightweight log forwarder.                     | Supports AWS/GCP/S3.                   |
| **Loki**         | High-performance log storage (Grafana-native). | No indexing overhead.                  |

---

## **Schema Reference**

| **Field**            | **Type**       | **Required** | **Description**                                      | **Example**                     |
|----------------------|----------------|--------------|------------------------------------------------------|---------------------------------|
| `timestamp`          | ISO 8601       | Yes          | When the log was generated.                          | `2024-05-20T14:30:00.123Z`      |
| `level`              | String         | Yes          | Log severity (`TRACE`, `ERROR`, etc.).               | `"WARN"`                        |
| `service`            | String         | Recommended  | Application/service name.                           | `"auth-service"`                |
| `request_id`         | UUID/String    | Recommended  | Correlate logs across microservices.                | `"req_123abc"`                  |
| `user_id`            | String         | Conditional  | Identifier for authenticated users.                  | `"usr_456xyz"`                  |
| `message`            | String         | Yes          | Human-readable description of the event.             | `"Failed to validate token"`    |
| `context`            | Object         | Optional     | Key-value pairs for extra details.                   | `{"token": "xyz", "status": 403}` |

---

## **Query Examples**
### **1. Filter by Service & Level (ELK Query DSL)**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "service": "payment-processor" } },
        { "term": { "level": "ERROR" } }
      ]
    }
  }
}
```

### **2. Correlation by Request ID (Loki)**
```
{request_id="req_123abc"} | json
```
**Output:**
```json
{
  "request_id": "req_123abc",
  "level": "ERROR",
  "message": "Payment declined",
  "context": { "amount": 500 }
}
```

### **3. Anomaly Detection (Grafana Explore)**
```sql
-- Identify 5xx errors in last 24h
sum(rate(http_requests_total{status=~"5.."}[1m])) by (service)
```

---

## **Implementation Details**
### **1. Logging Libraries**
| **Language** | **Library**          | **Features**                                  |
|--------------|----------------------|-----------------------------------------------|
| Python       | `structlog`          | Structured logging, async support.            |
| Java         | `SLF4J + Logback`    | Extensible, JSON formatting.                 |
| Node.js      | `pino`               | Fast, streaming logs.                         |
| Go           | `zap`                | Zero-allocation, structured.                  |

### **2. Configuration Examples**
#### **Logback (Java)**
```xml
<configuration>
  <appender name="JSON" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>app.log</file>
    <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>app.log.%d{yyyy-MM-dd}.gz</fileNamePattern>
    </rollingPolicy>
  </appender>
  <root level="INFO">
    <appender-ref ref="JSON"/>
  </root>
</configuration>
```

#### **Python (structlog)**
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer(),
        structlog.dev.ConsoleRenderer(colors=True)
    ]
)
logger = structlog.get_logger()
logger.info("User action", action="login", user="Alice")
```

---

## **Requirements & Constraints**
| **Constraint**               | **Guideline**                                                                 |
|-------------------------------|-------------------------------------------------------------------------------|
| **Latency**                   | Async logging to avoid blocking (e.g., `structlog` buffer).                   |
| **Disk Space**                | Rotate logs daily; use TTL for older logs.                                   |
| **Compliance (GDPR/HIPAA)**   | Redact PII; encrypt logs at rest.                                            |
| **Scalability**               | Use log sharding (e.g., by `service`/`timestamp`) for distributed systems.   |

---

## **Related Patterns**
1. **[Observability](Observability.md)**
   - Correlate logs with metrics and traces (e.g., OpenTelemetry).

2. **[Distributed Tracing](Tracing.md)**
   - Add `trace_id` to logs for end-to-end debugging.

3. **[Audit Logging](AuditLogging.md)**
   - Log sensitive actions (e.g., admin changes) separately.

4. **[Circuit Breaker](CircuitBreaker.md)**
   - Log failures to detect cascading outages.

5. **[Resilience Patterns](Resilience.md)**
   - Combine with retries/fallbacks for graceful degradation.

---
**See Also:**
- [AWS CloudWatch Logs Best Practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/LogBestPractices.html)
- [OpenTelemetry Logs Specification](https://opentelemetry.io/docs/specs/logs/)