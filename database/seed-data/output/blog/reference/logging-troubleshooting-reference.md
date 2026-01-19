# **[Pattern] Logging Troubleshooting Reference Guide**

---

## **Overview**
Effective **logging troubleshooting** ensures visibility into application behavior, performance bottlenecks, and runtime errors. This guide outlines best practices, schema requirements, and query patterns for diagnosing logging-related issues in distributed systems, microservices, or monolithic applications. By leveraging structured logs, filters, and aggregation techniques, developers and DevOps teams can efficiently isolate issues, reduce mean time to resolution (MTTR), and maintain system reliability.

---

## **Key Concepts**
| Term                | Definition                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Structured Log**  | Logs formatted as key-value pairs (e.g., JSON) for easier parsing and querying. |
| **Log Level**       | Severity categorization (e.g., `DEBUG`, `INFO`, `ERROR`, `CRITICAL`).    |
| **Log Correlation** | Associating logs across services using trace IDs, request IDs, or session IDs. |
| **Sampling**        | Selectively capturing logs for high-throughput systems (e.g., 1% of requests). |
| **Log Retention**   | Policy defining how long logs are stored (e.g., 7 days, 1 month).          |
| **Log Shipping**    | Forwarding logs from applications to centralized storage (e.g., ELK, Splunk). |
| **Anomaly Detection** | Alerting on unusual log patterns (e.g., spike in `ERROR` logs).           |

---

## **Schema Reference**
A standardized schema improves log querying and analysis. Below is a recommended schema for structured logs:

| Field               | Type    | Description                                                                                                                                                                                                                                                                 |
|---------------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **@timestamp**      | string  | ISO-8601 formatted timestamp (e.g., `2024-05-20T14:30:00Z`).                                                                                                                                                                                                                  |
| **@version**        | string  | Log version (e.g., `1`).                                                                                                                                                                                                                                   |
| **host**            | string  | Machine generating the log (e.g., `web-server-01`).                                                                                                                                                                                                                  |
| **service**         | string  | Application/service name (e.g., `auth-service`, `payment-gateway`).                                                                                                                                                                                              |
| **level**           | string  | Severity: `DEBUG`, `INFO`, `WARN`, `ERROR`, `CRITICAL`.                                                                                                                                                                                                        |
| **message**         | string  | Human-readable log content.                                                                                                                                                                                                                             |
| **trace_id**        | string  | Unique identifier for end-to-end request tracing (e.g., `123e4567-e89b-12d3-a456-426614174000`).                                                                                                                                                                 |
| **request_id**      | string  | Unique identifier for individual requests (e.g., `req_789abc`).                                                                                                                                                                                                |
| **user_id**         | string  | User identifier if applicable (e.g., `user_12345`).                                                                                                                                                                                                      |
| **metrics**         | object  | Key-value metrics (e.g., `{"response_time": "500ms", "status_code": "500"}`).                                                                                                                                                                        |
| **context**         | object  | Additional structured data (e.g., `{"database": "postgres", "version": "v2.1.0"}`).                                                                                                                                                                   |
| **stack_trace**     | string  | Error stack trace (if `level` is `ERROR` or `CRITICAL`).                                                                                                                                                                                                       |

---

## **Implementation Patterns**

### **1. Log Collection & Centralization**
Use agents or SDKs to forward logs to a centralized store (e.g., **Fluentd**, **Logstash**, **AWS CloudWatch**).
**Example (Fluentd Config)**:
```conf
<source>
  @type tail
  path /var/log/app/app.log
  pos_file /var/log/fluentd-app.pos
  tag app.logs
</source>

<match app.logs>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  type_name app
</match>
```

### **2. Structured Logging**
Encode logs as JSON for machine readability. Example in Python:
```python
import logging
import json
from datetime import datetime

logger = logging.getLogger("app")

def structured_log(level, message, trace_id, user_id=None):
    log_entry = {
        "@timestamp": datetime.utcnow().isoformat() + "Z",
        "@version": "1",
        "level": level,
        "message": message,
        "trace_id": trace_id,
        "user_id": user_id
    }
    logger.log(getattr(logging, level), json.dumps(log_entry))
```

### **3. Log Filtering & Aggregation**
Apply filters to focus on critical logs:
- **ELK (Elasticsearch, Logstash, Kibana)**:
  ```json
  // Kibana Discovery Query (find 500 errors in last hour)
  {
    "query": {
      "bool": {
        "must": [
          { "term": { "level": "ERROR" } },
          { "range": { "@timestamp": { "gte": "now-1h" } } }
        ]
      }
    }
  }
  ```
- **Grafana Loki**:
  ```logql
  // Alert on errors in payment service
  sum by (service) (rate(logs{level="ERROR", service="payment-service"}[5m])) > 5
  ```

### **4. Correlation Across Services**
Use **trace IDs** to link logs across distributed systems:
```
- Service A (trace_id=123) → Service B (trace_id=123) → Service C (trace_id=123)
```
**Query Example (Grafana Loki)**:
```logql
// Find all logs with trace_id=123
{ trace_id="123" }
```

### **5. Sampling for High-Volume Systems**
Reduce log volume by sampling (e.g., 1% of requests):
```python
def log_with_sampling(message, probability=0.01):
    if random.random() < probability:
        structured_log("INFO", message, trace_id="123")
```

### **6. Anomaly Detection**
Set up alerts for unusual patterns:
- **Spike in errors**: `ERROR` logs > 10% over baseline.
- **Latency spikes**: `response_time > 2s` for >5 requests/minute.
**Example (Prometheus + Alertmanager)**:
```yaml
# alert_rule.yml
groups:
- name: logging-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(logs{level="ERROR"}[5m]) > 10
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High error rate in {{ $labels.service }}"
```

---

## **Query Examples**
### **1. Find Critical Errors in Last 24 Hours**
```json
// Elasticsearch Query
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "CRITICAL" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  }
}
```
**Output**:
```json
[
  {
    "@timestamp": "2024-05-20T14:30:00Z",
    "level": "CRITICAL",
    "message": "Database connection failed",
    "service": "user-service",
    "trace_id": "abc123"
  }
]
```

### **2. Correlate Logs by Trace ID**
```logql
// Grafana Loki: Show all logs for trace_id=abc123
{ trace_id="abc123" } | json
```

### **3. Identify Slow Requests**
```sql
// Athena/BigQuery: Find slow API responses (response_time > 1s)
SELECT *
FROM logs
WHERE metrics.response_time > '1000ms'
  AND @timestamp > timestamp_sub(now(), interval 1 hour)
ORDER BY metrics.response_time DESC
LIMIT 10;
```

### **4. User-Specific Errors**
```json
// Elasticsearch: Find errors for user_id=12345
{
  "query": {
    "bool": {
      "must": [
        { "term": { "level": "ERROR" } },
        { "term": { "user_id": "12345" } }
      ]
    }
  }
}
```

### **5. Log Volume Analysis**
```logql
// Grafana Loki: Count logs by service per hour
sum by (service) (count_over_time({}[1h]))
```

---

## **Tools & Integrations**
| Tool               | Purpose                                                                 | Example Use Case                                  |
|--------------------|-------------------------------------------------------------------------|---------------------------------------------------|
| **Elasticsearch**  | Full-text search, aggregation                                          | Analyzing error patterns.                         |
| **Grafana Loki**   | Lightweight log aggregation                                           | Monitoring containerized apps.                    |
| **AWS CloudWatch** | Native AWS logging with anomaly detection                              | Alerting on EC2 instance logs.                    |
| **Datadog**        | APM + logs + infrastructure monitoring                                 | Tracing microservices.                            |
| **Splunk**         | SIEM + log analysis                                                    | Security incident analysis.                       |
| **Fluentd/Fluent Bit** | Log shipping                                                                 | Forwarding logs from Kubernetes pods.           |
| **Loki (Grafana)** | Cost-effective log aggregation                                         | Observing serverless functions.                  |

---

## **Common Pitfalls & Mitigations**
| Pitfall                          | Mitigation                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **Unstructured logs**             | Enforce JSON/key-value formatting.                                          |
| **High log volume**               | Implement sampling or retention policies.                                  |
| **Missing trace IDs**             | Auto-generate trace IDs in distributed systems.                           |
| **No log levels**                 | Define severity tiers (DEBUG, INFO, ERROR) for filtering.                 |
| **Slow queries**                  | Optimize Elasticsearch indices (e.g., use `keyword` instead of `text`).     |
| **No correlation**                | Use trace IDs or request IDs across services.                               |
| **Retention policies not enforced**| Set TTL (Time-To-Live) for logs (e.g., 30 days).                           |

---

## **Related Patterns**
1. **[Distributed Tracing]** – Use OpenTelemetry to trace requests across services.
2. **[Metrics Collection]** – Combine logs with Prometheus/Grafana metrics.
3. **[Error Tracking]** – Integrate with Sentry or Rollbar for real-time error alerts.
4. **[Configurable Logging]** – Dynamic log levels via environment variables.
5. **[Audit Logging]** – Immutable logs for security/compliance (e.g., AWS CloudTrail).
6. **[Log Analysis Pipelines]** – ELT (Extract, Load, Transform) with Python Spark or Flink.

---
**References:**
- [OpenTelemetry Logs Specification](https://opentelemetry.io/docs/specs/logs/)
- [ELK Stack Guide](https://www.elastic.co/guide/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)