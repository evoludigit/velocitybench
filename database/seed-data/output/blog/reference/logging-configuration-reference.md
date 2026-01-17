# **[Pattern] Logging Configuration: Reference Guide**

---

## **Overview**
The **Logging Configuration** pattern ensures structured, centralized, and efficient logging across applications by defining reusable configurations. This pattern standardizes log formats, levels, output destinations (e.g., files, consoles, external services), and retention policies. By abstracting logging specifics into a configurable layer, developers reduce boilerplate code, improve debuggability, and enable dynamic log management without application restarts. Use cases include:
- **Centralized logging** (e.g., ELK Stack, Splunk)
- **Auditing compliance** (e.g., GDPR, HIPAA)
- **Performance monitoring** (e.g., latency tracking)
- **Multi-environment support** (dev/staging/production)

Best practices emphasize:
✔ **Separation of concerns** (config vs. code)
✔ **Contextual logging** (e.g., user IDs, request IDs)
✔ **Dynamic adjustment** (e.g., log levels per environment)
✔ **Minimal overhead** (avoid excessive log verbosity)

---

## **Schema Reference**

### **1. Core Configuration Schema**
| Field               | Type           | Required | Description                                                                                                                                                                                                 | Default Value       | Example Values                          |
|---------------------|----------------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------|-----------------------------------------|
| `log_level`         | `string`       | Yes      | Severity threshold (e.g., "INFO", "DEBUG"). Higher levels override lower ones.                                                                                                                               | `"INFO"`            | `"DEBUG"`, `"WARN"`, `"ERROR"`         |
| `format`            | `object`       | No       | Structure of log messages (keys/values for JSON, templates for text).                                                                                                                                         | *N/A*               | `{"type": "json", "template": "..."}` |
| `output_destinations` | `array`       | Yes      | List of log sinks (files, consoles, HTTP endpoints).                                                                                                                                                         | *Empty array*       | `[{"type": "file", "path": "/var/log/app.log"}]` |
| `retention`         | `object`       | No       | Policies for archiving/deletion (e.g., max age, size limits).                                                                                                                                                 | *N/A*               | `{"max_age_days": 30, "max_size_mb": 100}` |
| `context_providers` | `array`        | No       | External data injectors (e.g., user metadata, request IDs).                                                                                                                                                  | *Empty array*       | `[{"type": "headers", "key": "X-Correlation-ID"}]` |

---

### **2. Output Destination Schema**
| Field      | Type      | Required | Description                                                                                                                                                                                                 | Default Value | Example Values                  |
|------------|-----------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|----------------------------------|
| `type`     | `string`  | Yes      | Destination type (`"file"`, `"console"`, `"http"`, `"syslog"`).                                                                                                                                             | *N/A*          | `"file"`                        |
| `path`     | `string`  | Conditional | File path (for `"file"`).                                                                                                                                                                                   | *N/A*          | `"/logs/app.prod.log"`          |
| `url`      | `string`  | Conditional | HTTP endpoint (for `"http"`).                                                                                                                                                                               | *N/A*          | `"https://logs.example.com/api"`|
| `format`   | `string`  | Conditional | Log format for the destination (`"json"`, `"plain"`, `"structured"`).                                                                                                                                        | `"plain"`       | `"json"`                        |
| `rotation` | `object`  | Conditional | File rotation settings (for `"file"`).                                                                                                                                                                     | *N/A*          | `{"policy": "daily", "count": 7}`|

**Example Rotation Policy:**
```json
{
  "policy": "size",   // or "daily", "monthly"
  "max_size_mb": 100,
  "count": 5          // Retain 5 rotated files
}
```

---

### **3. Format Schema**
| Field       | Type      | Required | Description                                                                                                                                                                                                 | Default Value | Example Values               |
|-------------|-----------|----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------|-------------------------------|
| `type`      | `string`  | Yes      | Format type (`"json"`, `"template"`, `"default"`).                                                                                                                                                         | `"default"`    | `"json"`                      |
| `template`  | `string`  | Conditional | Custom log message template (for `"template"`). Use placeholders like `{timestamp}`, `{level}`, `{message}`.                                                                                           | *N/A*          | `"[{timestamp}] {level}: {message} (user={user_id})"` |
| `keys`      | `array`   | Conditional | JSON keys to include (for `"json"`). Order matters.                                                                                                                                                                | *Auto-detect*  | `["timestamp", "level", "error"]` |

**Template Placeholders:**
| Placeholder      | Description                     |
|------------------|---------------------------------|
| `{timestamp}`    | ISO 8601 format (e.g., `2023-10-01T12:00:00Z`) |
| `{level}`        | Log level (e.g., `INFO`)        |
| `{message}`      | Log content                     |
| `{context}`      | Key-value pairs from `context_providers` |

---

### **4. Full Example Configuration**
```json
{
  "log_level": "DEBUG",
  "format": {
    "type": "json",
    "keys": ["timestamp", "level", "message", "user_id", "request_id"]
  },
  "output_destinations": [
    {
      "type": "file",
      "path": "/var/logs/app/app.log",
      "rotation": {
        "policy": "daily",
        "count": 7
      }
    },
    {
      "type": "http",
      "url": "https://logs.example.com/api/v1",
      "format": "json",
      "auth": {
        "token": "secure-token-123"
      }
    }
  ],
  "context_providers": [
    {
      "type": "headers",
      "key": "X-Correlation-ID"
    },
    {
      "type": "env",
      "key": "USER_ID"
    }
  ],
  "retention": {
    "max_age_days": 30,
    "max_size_mb": 500
  }
}
```

---

## **Query Examples**

### **1. Filtering Logs by Level (CLI)**
```bash
# Filter DEBUG-level logs from file
grep \"DEBUG\" /var/logs/app/app.log | tail -n 50
```

### **2. Dynamic Log Level Adjustment (Runtime)**
**Use Case:** Lower log level during debugging without restarting.
**Implementation (Pseudocode):**
```python
# Update log_level dynamically
config["log_level"] = "DEBUG"
logger.update_config(config)
```

**Output:**
```
2023-10-01T12:00:00Z DEBUG: User 'john.doe' initiated session (ID: req-456)
```

---

### **3. Querying Logs via HTTP Endpoint**
**Request:**
```bash
curl -X POST \
  https://logs.example.com/api/v1/query \
  -H "Authorization: Bearer secure-token-123" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "level": "ERROR",
      "timestamp": {
        "gt": "2023-10-01T00:00:00Z",
        "lt": "2023-10-02T00:00:00Z"
      }
    }
  }'
```

**Response:**
```json
{
  "hits": [
    {
      "timestamp": "2023-10-01T15:30:45Z",
      "level": "ERROR",
      "message": "Database connection failed",
      "context": {
        "user_id": "user-789",
        "request_id": "req-123"
      }
    }
  ]
}
```

---

### **4. Rotated Log Analysis**
**Check rotated logs:**
```bash
ls -lth /var/logs/app/app.log* | head -n 5
```
**Output:**
```
-rw-r--r-- 1 root root 12M Oct  1 00:00 /var/logs/app/app.2023-10-01.log
-rw-r--r-- 1 root root  5M Oct  2 00:00 /var/logs/app/app.2023-10-02.log
```

---

## **Implementation Details**

### **Key Concepts**
1. **Log Levels:**
   - Hierarchy: `TRACE < DEBUG < INFO < WARN < ERROR < FATAL`.
   - Example implementation:
     ```python
     class LogLevel:
         DEBUG = 10
         INFO = 20
         WARN = 30
         ERROR = 40
     ```

2. **Context Injection:**
   - Attach dynamic metadata (e.g., user ID, request ID) to logs.
   - **Example (Middleware):**
     ```javascript
     function logContext(req, res, next) {
       const context = { user_id: req.headers['x-user-id'] };
       logger.setContext(context);
       next();
     }
     ```

3. **Output Plugins:**
   - Extendable sinks (e.g., `FileOutput`, `HttpOutput`).
   - **Plugin Interface:**
     ```typescript
     interface LogOutput {
       write(log: LogEntry): Promise<void>;
       close(): Promise<void>;
     }
     ```

4. **Performance Considerations:**
   - **Batching:** Group logs before flushing to reduce I/O.
   - **Async Writes:** Use buffered queues (e.g., `asyncio.Queue` in Python).
   - **Avoid Overhead:** Skip formatting for low-level logs (e.g., `ERROR`).

---

### **Common Pitfalls & Solutions**
| **Pitfall**                          | **Solution**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------|
| Log spam (e.g., `DEBUG` in production)| Use environment-aware log levels (e.g., `config.log_level = process.env.NODE_ENV === 'dev' ? 'DEBUG' : 'INFO'`). |
| Missing context                       | Auto-inject `request_id` from middleware/tracing systems.                   |
| Large log files                       | Enforce rotation policies and compression (e.g., `gzip`).                  |
| Security risks (e.g., PII in logs)    | Mask sensitive fields (e.g., `user.password` → `[REDACTED]`).               |
| Inconsistent formats                  | Enforce a schema (e.g., JSON) or use a formatter library (e.g., `logfmt`). |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Structured Logging](https://example.com/structured-logging)** | Standardize log formats (e.g., JSON) for easier parsing.                     | When integrating with ELK/Splunk or needing queryable logs.                    |
| **[Log Correlation](https://example.com/log-correlation)**          | Link related logs using IDs (e.g., `request_id`).                              | For distributed systems or debugging transactions.                            |
| **[Centralized Logging](https://example.com/centralized-logging)**   | Aggregate logs from multiple services (e.g., Fluentd + Kafka).               | In microservices architectures.                                                |
| **[Log Retention Policy](https://example.com/log-retention)**        | Automate log cleanup based on age/size.                                       | To comply with data privacy laws or save storage.                             |
| **[Dynamic Instrumentation](https://example.com/dynamic-instrumentation)** | Add logs/rules at runtime without code changes.                            | For A/B testing or feature flags.                                              |

---

## **Best Practices Checklist**
1. **Environment-Specific Configs:**
   - Store configs in environment variables or config files (e.g., `config-dev.json`, `config-prod.json`).
   - Example:
     ```yaml
     # config-dev.yml
     log_level: "DEBUG"
     output_destinations:
       - type: "console"
     ```

2. **Avoid Hardcoding:**
   - Use dependency injection for loggers.
   - Example (Python):
     ```python
     def my_function(logger: Logger):
         logger.info("Function executed")
     ```

3. **Test Logging Configs:**
   - Validate configs before deployment (e.g., schema validation with `jsonschema`).
   - Example test:
     ```python
     assert config["log_level"] in ["DEBUG", "INFO", "WARN", "ERROR"]
     ```

4. **Monitor Log Volume:**
   - Set alerts for sudden spikes in log size (e.g., via Prometheus).
   - Example query:
     ```promql
     rate(log_size_bytes[1h]) > 1000000  # Alert if >1MB/hour
     ```

5. **Document Log Formats:**
   - Publish a log schema (e.g., `/docs/log-schema.md`) for consumers.