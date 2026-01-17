---
# **[Pattern] Logging Integration Reference Guide**

---

## **Overview**
The **Logging Integration** pattern centralizes log collection, processing, and distribution from applications, APIs, and infrastructure components into a structured logging system (e.g., ELK Stack, Splunk, Azure Monitor). This enables unified log analysis, correlation of events, debugging, and compliance reporting.

Key benefits:
- **Consolidated visibility**: All logs—application, system, and audit—streamed to a single platform.
- **Structured querying**: Logs normalized into a searchable format (e.g., JSON, CSV).
- **Reduced noise**: Filtering, enrichment, and retention policies applied at ingestion.
- **Compliance**: Retention, exporting, and anonymization aligned with regulatory requirements.

This guide covers:
1. Core schema for log integration.
2. Implementation options (agents, APIs, SDKs).
3. Query syntax for analysis.
4. Integration with monitoring and observability stacks.

---

## **1. Implementation Details**

### **1.1 Log Collection Methods**
| **Method**          | **Use Case**                          | **Pros**                          | **Cons**                          |
|----------------------|---------------------------------------|------------------------------------|-----------------------------------|
| **Log Shippers**     | Lightweight agents for server logs    | Low overhead, direct shipping      | Limited to supported formats      |
| **API Endpoints**    | Custom applications                  | Full control over data format      | Requires explicit integration     |
| **SDKs**             | Cloud-native apps (e.g., AWS Lambda) | Built-in error tracking            | Vendor lock-in risk               |
| **File Monitoring**  | Legacy systems                       | Minimal changes to existing apps   | Higher latency                    |

### **1.2 Log Formats**
| **Format** | **Description**                                                                 | **Example**                                                                 |
|------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **JSON**   | Structured data (recommended for querying).                                  | `{"timestamp": "2023-11-15T12:00:00Z", "level": "ERROR", "message": "..."}` |
| **CEF**    | Cisco’s standardized format for SIEM compatibility.                          | `CEF:0|MyApp|1.0|Error|loginfailed|12345|user=invalid`                       |
| **Plaintext** | Simple logs (low overhead, but unstructured).                              | `2023-11-15 12:00:00 ERROR Failed login`                                  |

### **1.3 Core Schema (Log Entry Structure)**
Logs must adhere to this schema for standardized querying. Use a library like **OpenTelemetry** or **structlog** to enforce consistency.

| **Field**               | **Type**   | **Description**                                                                 | **Example**                          |
|-------------------------|------------|-------------------------------------------------------------------------------|---------------------------------------|
| `timestamp`             | ISO8601    | When the log event occurred.                                                 | `2023-11-15T12:00:00.123Z`           |
| `level`                 | String     | Severity (DEBUG, INFO, WARNING, ERROR, CRITICAL).                           | `"ERROR"`                            |
| `message`               | String     | Human-readable message.                                                      | `"Database connection failed"`        |
| `app_name`              | String     | Application name (e.g., `auth-service`).                                      | `"user-service"`                     |
| `service_version`       | String     | Version of the application.                                                  | `"v1.2.0"`                           |
| `user_id`               | String     | User identifier for traceability.                                             | `"user_12345"`                       |
| `timestamp_utc_ms`      | Integer    | Unix timestamp in milliseconds (for time-series analysis).                   | `1699980000123`                      |
| `metadata`              | Object     | Key-value pairs for context (e.g., `{"ip": "192.168.1.1", "status_code": 500}` | `{"ip": "192.168.1.1"}`              |

---
### **1.4 Ingestion Pipelines**
Logs can be shipped via:
1. **Filebeat/Logstash**: Agent-based shipping.
   ```yaml
   # Filebeat configuration (YAML)
   filebeat.inputs:
   - type: container
     paths: ["/var/log/containers/*.log"]
     processors:
       - decode_json_fields:
           fields: ["message"]
           target: "json"
   ```
2. **Direct API Post**: Endpoint-based (e.g., `/api/v1/logs`).
   ```http
   POST /api/v1/logs HTTP/1.1
   Content-Type: application/json

   {
     "timestamp": "2023-11-15T12:00:00Z",
     "level": "ERROR",
     "message": "Invalid token",
     "user_id": "user_12345"
   }
   ```
3. **Cloud Native (AWS, GCP)**:
   - AWS Lambda: Use the `context` object or `console.log` (via CloudWatch Logs).
   - GCP Cloud Logging: Automatically captures logs from App Engine/Cloud Run.

---
### **1.5 Enrichment & Processing**
Apply transformations to raw logs before storage:
- **Parsing**: Extract structured fields (e.g., IP addresses, timestamps).
- **Normalization**: Convert inconsistent formats (e.g., `2023-11-15` → ISO8601).
- **Sampling**: Reduce volume (e.g., sample 10% of DEBUG logs).
- **Anonymization**: Mask PII (e.g., `user_id: "****-12345"`).

Example **Logstash pipeline**:
```ruby
filter {
  grok {
    match => ["message", "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level}: %{GREEDYDATA:message}"]
  }
  mutate {
    convert => ["timestamp", "unixmillis"]
  }
}
```

---
## **2. Schema Reference**

### **Required Fields**
| Field            | Data Type | Notes                                  |
|------------------|-----------|----------------------------------------|
| `timestamp`      | timestamp | UTC timezone required.                 |
| `level`          | string    | Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL. |
| `message`        | string    | Mandatory; must be non-empty.          |

### **Recommended Fields**
| Field               | Data Type | Description                          |
|---------------------|-----------|--------------------------------------|
| `app_name`          | string    | Identifies the source application.   |
| `service_version`   | string    | Helps isolate issues by version.     |
| `user_id`           | string    | Enables user-level analysis.         |
| `trace_id`          | string    | Correlates logs with traces/metrics.  |
| `host`              | string    | Machine name/identifier.             |
| `stack_trace`       | string    | For errors (optional but useful).    |

### **Conditional Fields**
| Field               | Data Type | Use Case                          |
|---------------------|-----------|-----------------------------------|
| `ip_address`        | string    | Required for network logs.        |
| `request_id`        | string    | Required for API gateway logs.    |
| `duration_ms`       | integer   | Required for performance logs.    |

---
## **3. Query Examples**

### **3.1 Searching Logs**
#### **Basics**
- **All ERROR logs from the past hour**:
  ```kibana
  level: ERROR AND timestamp > now-1h
  ```
- **User-specific errors**:
  ```kibana
  level: ERROR AND user_id: "user_12345" AND message: "auth failed"
  ```
- **Logs by service version**:
  ```kibana
  app_name: "order-service" AND service_version: "v2.*"
  ```

#### **Advanced**
- **Correlate logs with metrics**:
  ```kibana
  (level: ERROR AND app_name: "payment-service") AND
  (timestamp > now-5m AND duration_ms > 2000)
  ```
- **Find anomalous spikes**:
  ```sql
  -- Using Elasticsearch Query DSL
  {
    "query": {
      "bool": {
        "must": [
          { "term": { "level": "ERROR" } },
          { "range": { "timestamp": { "gte": "now-1h", "lte": "now" } } }
        ]
      }
    },
    "aggs": {
      "count_by_minute": {
        "date_histogram": {
          "field": "timestamp",
          "interval": "1m"
        }
      }
    }
  }
  ```

#### **Log Analysis Tools**
| Tool          | Query Example                          | Notes                                  |
|---------------|----------------------------------------|----------------------------------------|
| **Elasticsearch** | `GET /logs/_search?q=level:ERROR`      | REST API for deep analysis.            |
| **Grafana Loki** | `{job="myapp"} | level="error"`                         | Lightweight log aggregation.          |
| **Kibana**     | `discover` + filter: `level: ERROR`   | UI-based for exploratory analysis.     |

---
## **4. Related Patterns**

### **4.1 Distributed Tracing**
- **Purpose**: Correlate logs with traces/metrics for end-to-end analysis.
- **Integration**: Add a `trace_id` field to logs (matching OpenTelemetry trace IDs).
- **Tools**: Jaeger, Zipkin, AWS X-Ray.

### **4.2 Structured Logging**
- **Purpose**: Enforce consistency in log formats across services.
- **Implementation**: Use libraries like:
  - Python: `structlog`
  - Java: `Logback` with JSON encoder
  - Go: `zap` or `logrus`
- **Benefit**: Simplifies querying and reduces noise.

### **4.3 Log Retention & Export**
- **Purpose**: Comply with data residency and compliance requirements.
- **Options**:
  - **Retention policies**: Automatically purge old logs (e.g., Elasticsearch `ilm`).
  - **Export**: Periodically export to S3/Google Cloud Storage.
  - **Anonymization**: Mask PII before long-term storage.

### **4.4 Centralized Configuration**
- **Purpose**: Manage log levels, formats, and destinations dynamically.
- **Implementation**:
  - Use **config maps** (Kubernetes) or **environment variables** to override settings.
  - Example:
    ```yaml
    # Kubernetes ConfigMap for log level
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: app-logs-config
    data:
      LOG_LEVEL: "ERROR"
    ```

---
## **5. Troubleshooting**
| **Issue**                     | **Root Cause**                          | **Solution**                                  |
|-------------------------------|-----------------------------------------|-----------------------------------------------|
| **Missing fields in logs**    | Inconsistent formatting across services | Enforce schema via SDKs (e.g., `structlog`).   |
| **High ingestion latency**    | Slow API endpoints or network issues   | Use agents (Filebeat) or batch processing.    |
| **Correlation between logs**  | Missing `trace_id` or `request_id`      | Add distributed tracing (OpenTelemetry).       |
| **Log volume overload**       | Unstructured or verbose logs            | Implement sampling (e.g., `logrus` hooks).    |

---
## **6. Best Practices**
1. **Adopt a standard schema**: Avoid ad-hoc formats.
2. **Sample low-priority logs**: Reduce volume (e.g., sample 5% of INFO logs).
3. **Compress logs**: Use gzip for storage efficiency.
4. **Monitor pipeline health**: Track ingestion rates and errors.
5. **Test queries early**: Validate log structure before production.

---
## **7. References**
- **OpenTelemetry Logs**: [Specification](https://opentelemetry.io/docs/specs/otel/logs/)
- **ELK Stack**: [Logstash Guide](https://www.elastic.co/guide/en/logstash/current/index.html)
- **AWS CloudWatch**: [Log Ingestion](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)
- **Structured Logging**: [Google’s Guide](https://cloud.google.com/blog/products/management-tools/structured-logging)