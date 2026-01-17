**[Pattern] Logging Strategies Pattern Reference Guide**

---
### **Overview**
The **Logging Strategies** pattern provides a structured approach to capturing, processing, and storing application logs at different levels of detail and urgency. It ensures observability, debugging efficiency, and compliance by enabling application developers to choose or configure logging behaviors dynamically based on runtime context—such as environment, user actions, or system errors. This pattern is essential for debugging, monitoring, and maintaining applications in production. It supports categorization of logs into formats like **Structured Logging** (JSON, key-value pairs) or **Unstructured Logging** (plaintext), and allows customization of log levels (DEBUG, INFO, WARN, ERROR, CRITICAL) and retention policies.

---

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Log Level**             | Defines the severity of a log message (e.g., DEBUG for detailed traces, CRITICAL for system failures).                                                                                                           |
| **Log Format**            | The structure of log entries (e.g., **JSON** for machine-parsable data, **plaintext** for human readability).                                                                                               |
| **Log Destination**       | Where logs are sent (e.g., **local file**, **cloud storage**, **SIEM** like Splunk or ELK stack).                                                                                                             |
| **Log Retention Policy**  | Rules for how long logs are retained (e.g., **7 days in cloud**, **permanent for CRITICAL errors**).                                                                                                           |
| **Dynamic Strategies**    | Rules or conditions to apply different logging behaviors (e.g., verbose logging in DEV, minimal in PROD).                                                                                                  |
| **Correlation ID**        | A unique identifier for tracing requests or events across logs.                                                                                                                                           |
| **Bulk Logging**          | Collecting and transmitting logs in batches for efficiency.                                                                                                                                              |
| **Sensitive Data Handling** | Obfuscation or exclusion of PII/PHI (e.g., masking passwords, tokens).                                                                                                                                       |
| **Log Aggregator**        | Centralized systems (e.g., **Fluentd**, **Logstash**) for forwarding, filtering, and processing logs.                                                                                                         |

---

## **Implementation Details**

### **1. Schema Reference**
Below are common log message schemas supported by the **Logging Strategies** pattern.

#### **Structured Log (JSON)**
| Field               | Type      | Required | Description                                                                                                                                                     |
|---------------------|-----------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `@timestamp`        | String    | Yes      | ISO-8601 timestamp of the log entry.                                                                                                                           |
| `log_level`         | String    | Yes      | Severity level (e.g., "ERROR", "DEBUG").                                                                                                                         |
| `logger`            | String    | No       | Component generating the log (e.g., "auth-service", "payment-gateway").                                                                                     |
| `correlation_id`    | String    | No       | Unique identifier for tracing a user request or event across logs.                                                                                          |
| `message`           | String    | Yes      | Human-readable log message.                                                                                                                                   |
| `metadata`          | Object    | No       | Key-value pairs for additional context (e.g., `{"user_id": "123", "status_code": 404}`).                                                               |
| `sensitive_data`    | Boolean   | No       | Flag indicating if the log contains PII/PHI (default: `false`).                                                                                              |
| `destination`       | String    | No       | Target system (e.g., "cloud_storage", "local_file").                                                                                                       |

#### **Unstructured Log (Plaintext)**
Example:
```
2024-05-20T12:34:56.789Z ERROR auth-service [correlation_id=abc123] User login failed: Invalid credentials
```

---

### **2. Query Examples**
Use these queries to filter and analyze logs in a **log aggregator** (e.g., Elasticsearch, Splunk).

#### **Find Critical Errors in Last 24 Hours**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "log_level.keyword": "CRITICAL" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  }
}
```

#### **Trace Requests by Correlation ID**
```json
{
  "query": {
    "terms": { "correlation_id.keyword": ["abc123"] }
  },
  "sort": [ { "@timestamp": { "order": "desc" } } ]
}
```

#### **Filter Debug Logs for a Specific Service**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "log_level.keyword": "DEBUG" } },
        { "match": { "logger": "payment-gateway" } }
      ]
    }
  }
}
```

---

### **3. Dynamic Logging Strategies**
Apply different logging behaviors based on runtime conditions.

| **Strategy**               | **Condition**                          | **Example Behavior**                                                                                                                                 |
|----------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| **Environment-Based**      | `ENVIRONMENT=DEV`                     | Log all `DEBUG` messages to console.                                                                                                                 |
| **User Role-Based**        | `user.role="admin"`                   | Include extended metadata (e.g., `session_details`) for admin actions.                                                                              |
| **Rate-Limited Logging**   | `request.frequency > 100/s`            | Suppress `INFO` logs from high-frequency API calls.                                                                                                |
| **Context-Aware**          | `error_type="timeout"`                | Automatically log to `ERROR` level and notify the SRE team via Slack.                                                                             |
| **Geolocation-Based**      | `user.location="eu"`                  | Obfuscate sensitive data for GDPR compliance.                                                                                                       |
| **Batch Logging**          | `batch_size >= 100`                   | Flush logs to cloud storage every 5 seconds to reduce latency.                                                                                   |

---

### **4. Implementation Steps**
1. **Choose a Logging Library**
   - **JavaScript/TypeScript**: Winston, Pino
   - **Python**: Logging module, `structlog`
   - **Java**: SLF4J + Logback
   - **Go**: Zap, Logrus

2. **Define Log Formats**
   - Structured (JSON) for parsing and analysis.
   - Unstructured for human-readable debugging.

3. **Configure Destinations**
   ```python
   # Example (Python)
   logger = logging.getLogger()
   logger.addHandler(LogstashHandler(host="logstash.example.com", port=5000))
   ```

4. **Apply Retention Policies**
   - Use **cloud providers** (AWS CloudWatch, GCP Logging) with automated retention rules.
   - Rotate local logs daily with `logrotate`.

5. **Handle Sensitive Data**
   ```javascript
   // Example (Node.js)
   const logger = winston.createLogger({
     format: winston.format.json(),
     transports: [
       new winston.transports.File({
         filename: "logs/app.log",
         handleExceptions: true,
         json: true,
         meta: { timestamp: () => new Date().toISOString() },
         filter: (info) => !info.sensitiveData // Exclude sensitive fields
       })
     ]
   });
   ```

6. **Integrate with Monitoring Tools**
   - Ship logs to **SIEMs** (Splunk, Datadog) or **APM tools** (New Relic, AppDynamics).

---

### **5. Best Practices**
- **Standardize Log Formats**: Use JSON for consistency.
- **Avoid Overlogging**: Filter redundant logs (e.g., `DEBUG` in production).
- **Correlate Logs**: Use `correlation_id` for end-to-end tracing.
- **Secure Logs**: Encrypt logs in transit (TLS) and at rest.
- **Monitor Log Volume**: Alert on sudden spikes (e.g., DDoS attacks).
- **Test Strategies**: Validate log routing in staging before production.

---

## **Query Examples (Advanced)**
### **Find All Failed Payments in the Last Week**
```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "logger": "payment-service" } },
        { "match": { "message": "Failed" } },
        { "range": { "@timestamp": { "gte": "now-7d" } } }
      ]
    }
  }
}
```

### **Group Logs by User Session**
```json
{
  "size": 0,
  "aggs": {
    "user_sessions": {
      "terms": { "field": "metadata.user_id.keyword" }
    }
  }
}
```

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                       |
|---------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Observer**                    | Publish-subscribe model for distributing logs to multiple handlers (e.g., console, file, SIEM).                                                            |
| **Circuit Breaker**             | Logs failures and triggers fallback strategies (e.g., retry limits) in distributed systems.                                                                   |
| **Distributed Tracing**         | Uses `correlation_id` to track requests across microservices (e.g., OpenTelemetry).                                                                           |
| **Idempotency**                 | Logs retries to avoid duplicate processing (e.g., in event-driven architectures).                                                                             |
| **Rate Limiting**               | Logs throttled requests to monitor abuse (e.g., API rate limits).                                                                                                |
| **CQRS Event Sourcing**         | Logs command events and queries separately for auditability.                                                                                                     |
| **Service Mesh Logging**        | Integrates logs from Envoy/Istio for network-level observability.                                                                                                |
| **Chaos Engineering**           | Logs failures induced by experiments (e.g., latency injection) to validate resilience.                                                                          |

---
### **References**
- [Structured Logging Best Practices (AWS)](https://aws.amazon.com/blogs/architecture/guidelines-for-structured-logging/)
- [OpenTelemetry Logs Specification](https://opentelemetry.io/docs/specs/logs/)
- [GDPR-Compliant Logging (CISA)](https://www.cisa.gov/insights-analyses/2021/05/05/guidelines-logging-gdpr-compliance)

---
**Note**: Adjust schemas and queries based on your log aggregator (Elasticsearch, Splunk, etc.). Always validate log rotation and retention policies to comply with legal requirements.