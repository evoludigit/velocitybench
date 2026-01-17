---
# **[Pattern] Reference Guide: Logging Guidelines**

---

## **Overview**
Effective logging is a cornerstone of observability, debugging, and operational resilience in distributed systems. This **Logging Guidelines** pattern defines best practices for structured, actionable, and scalable logging in applications. It ensures logs are:
- **Consistent**: Uniform format and severity levels across services.
- **Actionable**: Include contextual metadata (e.g., request IDs, timestamps) for troubleshooting.
- **Efficient**: Minimize overhead while retaining diagnostic value.
- **Secure**: Avoid logging sensitive data (passwords, PII).

Adhering to these guidelines improves debugging efficiency, reduces alert fatigue, and facilitates compliance.

---

## **Key Concepts**
### **1. Log Levels**
Define severity levels to prioritize log messages:
| Level       | Usage Example                                                                 |
|-------------|--------------------------------------------------------------------------------|
| **TRACE**   | Detailed debug info (e.g., internal function calls). Use sparingly.            |
| **DEBUG**   | Debugging-specific messages (e.g., variable states). Disabled in production.   |
| **INFO**    | Application progress or user actions (e.g., "User logged in").                |
| **WARNING** | Non-critical issues (e.g., deprecated feature usage).                          |
| **ERROR**   | Critical failures (e.g., DB connection errors).                               |
| **FATAL**   | System-wide failures requiring restart (rare).                                |

---

### **2. Log Structure**
Use **structured logging** (e.g., JSON) for machine-readable logs:
```json
{
  "timestamp": "2023-10-15T12:34:56.789Z",
  "level": "ERROR",
  "service": "order-service",
  "instance": "order-service-01",
  "requestId": "req_abc123",
  "message": "Payment failed for order #42",
  "context": {
    "orderId": "ord_789",
    "amount": 19.99,
    "errorCode": "PAYMENT_GATEWAY_DOWN"
  }
}
```
**Mandatory Fields**:
- `timestamp` (ISO 8601 format).
- `level` (from table above).
- `service` (unique identifier for your service).

**Optional but Recommended**:
- `requestId`: Track user/native request flows.
- `traceId`: Link to distributed tracing systems (e.g., Jaeger).
- `userId`: For privacy-compliant anonymization.

---

### **3. Guidelines by Scenario**
| Scenario               | Guideline                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| **Error Logging**      | Always log errors with context (e.g., failed dependencies, input data). Avoid generic messages like "Failed".                              |
| **Sensitive Data**     | Mask or exclude PII (e.g., `user: {password: "[REDACTED]"}`). Log errors instead of raw exceptions (e.g., `error: "Invalid API key"`). |
| **Performance**        | Avoid blocking calls (e.g., async logging). Batch logs where possible (e.g., HTTP endpoints).                                                   |
| **Localization**       | Use English for log messages; localize UI messages separately.                                                                              |
| **Retention**          | Follow organizational policies (e.g., 30-day rotation for INFO, 1-year for ERROR). Use tools like Fluentd or Loki for retention.             |

---

## **Implementation Details**

### **1. Example Loggers**
#### **Python (Structlog)**
```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "Processed order",
    order_id=42,
    user_id="user123",
    amount=19.99,
    additional_fields={"shipping": {"country": "US"}}
)
```

#### **Java (SLF4J)**
```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

Logger logger = LoggerFactory.getLogger(MyClass.class);

logger.error(
    "Failed to fetch data",
    "requestId", requestId,
    "errorCode", "TIMEOUT",
    "attempts", 3,
    Exception.class, e
);
```

#### **Go (Zap)**
```go
import "go.uber.org/zap"

logger := zap.NewNop() // Replace with real logger in production
logger.Info("User login",
    zap.String("userId", "user123"),
    zap.String("ip", "192.168.1.1"),
)
```

---

### **2. Tooling Recommendations**
| Tool          | Purpose                                                                                     |
|---------------|---------------------------------------------------------------------------------------------|
| **Log Shipping** | Fluentd, Logstash: Aggregate logs from multiple services.                                    |
| **Storage**    | Loki, ELK Stack: Index and search logs efficiently.                                          |
| **Alerting**   | Prometheus Alertmanager, Datadog: Filter logs for anomalies.                                |
| **Sampling**   | Use tools like OpenTelemetry to sample logs in high-volume scenarios.                        |

---

## **Schema Reference**
| Field          | Type     | Required | Description                                                                                       |
|----------------|----------|----------|---------------------------------------------------------------------------------------------------|
| `timestamp`    | string   | ✅        | ISO 8601 formatted log generation time.                                                            |
| `level`        | string   | ✅        | One of: TRACE, DEBUG, INFO, WARNING, ERROR, FATAL.                                               |
| `service`      | string   | ✅        | Unique service identifier (e.g., `payment-service`).                                               |
| `instance`     | string   | ❌        | Instance ID (e.g., pod name in Kubernetes).                                                      |
| `requestId`    | string   | ❌        | Correlate with user/API requests.                                                                 |
| `message`      | string   | ✅        | Human-readable log text (localized to English).                                                   |
| `context`      | object   | ❌        | Key-value pairs for structured data (e.g., `{"status": "404"}`).                                  |

---

## **Query Examples**
### **1. Find Errors in Payment Service**
```sql
// Loki query
{service="payment-service", level="ERROR"} | line_format "{{.message}} ({{.context.errorCode}})"
```

### **2. Trace Failed Orders**
```json
// Using OpenTelemetry traceId
// Filter logs with traceId: "trace_abc456"
{
  "requestId": "req_789",
  "level": "ERROR",
  "message": "*failed*"
}
```

### **3. Analyze Slow API Responses**
```bash
// ELK Kibana Discover query
service: "api-gateway" AND duration > 2000ms AND level: "DEBUG"
```

---

## **Common Pitfalls & Fixes**
| Pitfall                          | Solution                                                                                          |
|-----------------------------------|--------------------------------------------------------------------------------------------------|
| **Log Spam**                      | Disable `DEBUG`/`TRACE` in production; use sampling for high-volume services.                    |
| **Missing Context**              | Always include `requestId`/`traceId` for correlating logs with traces/metrics.                     |
| **Overlogging Sensitive Data**   | Use masking (e.g., `user: {email: "[REDACTED]"}`.                                               |
| **Log Rotation Issues**          | Configure log retention policies (e.g., rotate INFO logs daily).                                   |
| **Inconsistent Formats**         | Enforce structured logging (e.g., JSON) across all services.                                     |

---

## **Related Patterns**
1. **[Distributed Tracing](link)** – Correlate logs with traces for end-to-end visibility.
2. **[Metrics Pattern](link)** – Use metrics to complement logs (e.g., `error_rate` metrics).
3. **[Idempotency](link)** – Design retry logic to avoid duplicate logs from failed operations.
4. **[Observability as Code](link)** – Define log schemas/configs via Infrastructure as Code (e.g., Terraform).
5. **[Security Logging](link)** – Extend guidelines for audit trails (e.g., failed auth attempts).

---
## **Further Reading**
- [Structured Logging RFC](https://github.com/open-telemetry/opentelemetry-specification/blob/main/specification/logs/data-model.md)
- [SLF4J Manual](https://www.slf4j.org/manual.html)
- [Log Management Best Practices (Gartner)](https://www.gartner.com/en/documents/3954981/log-management-best-practices)