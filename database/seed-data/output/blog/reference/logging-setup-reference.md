# **[Pattern] Logging Setup Reference Guide**

---

## **Overview**
The **Logging Setup** pattern defines a structured approach to configuring, implementing, and managing logging in applications. Proper logging captures runtime events, errors, and performance metrics, enabling debugging, auditing, and operational insights. This pattern ensures consistency across logging levels (`DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`), formats (JSON, structured text), output destinations (files, syslog, cloud services), and rotation policies.

This guide covers:
- Key configuration components (log levels, formatters, appenders).
- Best practices for scalability, security, and observability.
- Implementation examples across languages/frameworks.
- Integration with monitoring tools (Prometheus, ELK, Datadog).

---

## **Key Concepts**
| Concept           | Description                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| **Log Level**     | Severity of log messages (`DEBUG` for diagnostics, `ERROR` for failures).   |
| **Formatter**     | Defines log output structure (e.g., JSON for machine parsing).               |
| **Appender**      | Destination for logs (file, console, network).                             |
| **Rotation Policy** | Automatically manage log files (size/time-based rotation).                 |
| **Synchronous/Async** | Log processing mode (blocking vs. non-blocking).                           |
| **Correlation ID** | Unique identifier for tracing requests across logs.                        |

---

## **Schema Reference**
Below are the core components of a **Logging Setup**.

### **1. Log Configuration Schema**
| Attribute            | Type       | Required | Default          | Description                                                                 |
|----------------------|------------|----------|------------------|-----------------------------------------------------------------------------|
| `log_level`          | String     | Yes      | `INFO`           | Log severity threshold (e.g., `"DEBUG"`).                                  |
| `format`             | String     | No       | `text`           | Format type (`text`, `json`, `xml`).                                        |
| `appenders`          | Array      | Yes      | `[]`             | List of destinations (e.g., `[{ type: "file", path: "/var/log/app.log" }]`). |
| `rotation`           | Object     | No       | `null`           | Rotation settings (max size, max files).                                   |
| `synchronous`        | Boolean    | No       | `false`          | Enable synchronous log processing.                                           |
| `correlation_id`     | Boolean    | No       | `false`          | Enable request correlation IDs.                                             |
| `sampling_rate`      | Number     | No       | `1.0`            | Sample logs (e.g., `0.5` for 50% of logs).                                  |

---

### **2. Appender Types**
| Appender Type | Configuration Example                                                                 | Use Case                          |
|----------------|--------------------------------------------------------------------------------------|-----------------------------------|
| **File**       | `{ type: "file", path: "/var/log/app.log", rotation: { maxSize: "10MB", maxFiles: 3 } }` | Persistent storage.                |
| **Console**    | `{ type: "console" }`                                                                 | Real-time debugging.               |
| **Syslog**     | `{ type: "syslog", host: "logs.example.com", port: 514 }`                           | Centralized logging (Unix syslog). |
| **HTTP**       | `{ type: "http", url: "https://logs.example.com/api/v1/logs" }`                     | Cloud log aggregation.            |
| **Database**   | `{ type: "db", connection: "postgres://user:pass@localhost/db" }`                  | Structured log storage.           |

---

### **3. Rotation Policy Schema**
| Attribute      | Type       | Required | Default   | Description                          |
|----------------|------------|----------|-----------|--------------------------------------|
| `max_size`     | String     | No       | `null`    | Max log file size (e.g., `"10MB"`). |
| `max_files`    | Number     | No       | `5`       | Number of rotated log files to keep. |
| `time_based`   | Boolean    | No       | `false`   | Rotate by time (e.g., daily).        |

---

## **Implementation Examples**

### **1. Java (Logback)**
```xml
<!-- logback.xml -->
<configuration>
  <property name="LOG_DIR" value="/var/log" />
  <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>${LOG_DIR}/app.log</file>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>${LOG_DIR}/app.%d{yyyy-MM-dd}.log</fileNamePattern>
      <maxHistory>30</maxHistory>
    </rollingPolicy>
    <encoder>
      <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
    </encoder>
  </appender>
  <root level="INFO">
    <appender-ref ref="FILE" />
  </root>
</configuration>
```

**Key Points:**
- Uses **time-based rotation** (daily logs).
- **Structured pattern** for readability.
- **RollingPolicy** ensures old logs are preserved.

---

### **2. Node.js (Winston)**
```javascript
const { createLogger, transports, format } = require('winston');
const logger = createLogger({
  level: 'info',
  format: format.combine(
    format.timestamp(),
    format.json()
  ),
  transports: [
    new transports.Console(),
    new transports.File({
      filename: 'combined.log',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 3,
    }),
    new transports.Http({
      host: 'logs.example.com',
      path: '/api/v1/logs',
    }),
  ],
});
```

**Key Points:**
- **Multi-appender** setup (console + file + HTTP).
- **JSON formatting** for structured logs.
- **Automatic rotation** based on file size.

---

### **3. Python (Python Logging)**
```python
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger("my_app")
logger.setLevel(logging.DEBUG)

handler = RotatingFileHandler(
    "app.log",
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=3,
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)
```

**Key Points:**
- **RotatingFileHandler** for automatic log rotation.
- **UTF-8 encoding** for international characters.
- **Basic formatting** with timestamps.

---

## **Query Examples**
### **1. Filtering Logs by Level (Grep)**
```bash
# Filter INFO-level logs in a file
grep "INFO" app.log

# Filter errors from syslog
grep "ERROR" /var/log/syslog | less
```

### **2. JSON Log Aggregation (jq)**
```bash
# Parse JSON logs for HTTP errors
cat logs.json | jq '.msg | select(.level == "ERROR") | .http.status'
```

### **3. Log Correlation (ELK Stack)**
```json
// Kibana DSL Query for correlated logs
{
  "query": {
    "bool": {
      "must": [
        { "term": { "correlation_id": "abc123" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```

---

## **Best Practices**
1. **Avoid Sensitive Data**
   - Never log passwords, tokens, or PII (use masking if necessary).
2. **Performance Considerations**
   - Use **asynchronous logging** to avoid thread blocking.
   - Batch logs for high-throughput systems.
3. **Structured Logging**
   - Prefer **JSON** over plain text for machine parsing.
4. **Retention Policies**
   - Automate log cleanup (e.g., AWS CloudWatch retention).
5. **Distributed Tracing**
   - Include **correlation IDs** for request tracking.

---

## **Related Patterns**
| Pattern               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **[Observability]**    | Combines logging, metrics, and tracing for system visibility.                 |
| **[Error Handling]**  | Defines strategies for handling and logging exceptions.                     |
| **[Audit Logging]**   | Records security-relevant events (user actions, access changes).              |
| **[Distributed Tracing]** | Tracks requests across microservices using unique IDs.                     |
| **[Metrics Collection]** | Measures performance metrics (latency, throughput) alongside logs.           |

---

## **Troubleshooting**
| Issue                     | Cause                          | Solution                                  |
|---------------------------|--------------------------------|-------------------------------------------|
| Logs too verbose          | `DEBUG` level set globally.     | Adjust log level to `INFO` or higher.     |
| Missing logs              | Appender misconfiguration.     | Verify file permissions and paths.        |
| Slow application          | Synchronous logging.           | Switch to async logging.                  |
| Corrupted JSON logs       | Malformed log entries.         | Validate log formatters.                  |
| High disk usage           | No rotation policy.            | Implement `RotatingFileHandler` or similar. |

---

## **Further Reading**
- [Logback Manual](http://logback.qos.ch/)
- [Winston Documentation](https://github.com/winstonjs/winston)
- [Python Logging HOWTO](https://docs.python.org/3/library/logging.html)
- [ELK Stack Guide](https://www.elastic.co/guide/en/elastic-stack-guide/current/index.html)