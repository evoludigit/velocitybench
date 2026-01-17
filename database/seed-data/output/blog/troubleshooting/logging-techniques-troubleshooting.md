# **Debugging Logging Techniques: A Troubleshooting Guide**

Logging is a critical component of modern backend systems, enabling visibility into application behavior, error tracking, and performance optimization. However, improper logging configurations, missing logs, or excessive log volume can lead to operational inefficiencies and undetected issues.

This guide provides a structured approach to diagnosing, resolving, and preventing common logging-related problems.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm whether the issue is logging-related by checking:

| **Symptom**                          | **Possible Root Cause**                          |
|--------------------------------------|--------------------------------------------------|
| Logs missing in production          | Incorrect log level, logger misconfiguration      |
| Logs too verbose (high volume)      | Improper log level settings, unnecessary debug logs |
| Critical errors not logged          | Log filter exclusion, logger not initialized      |
| Logs not reaching central logging   | Failed log transport (e.g., dead letter queues)  |
| Logs appear delayed or out of order | Async logger misconfiguration, buffering issues   |
| Logging performance degradation     | Heavy log formatting, disk I/O bottlenecks        |
| Logs missing timestamps              | Logger misconfiguration, timezone issues          |
| Logs contain sensitive data          | Poor log masking, insecure log storage           |
| Logs inconsistent between stages     | Distributed tracing misconfigured                 |

**Next Steps:**
- Verify logs on **staging vs. production** environments.
- Check if logs are **filtered** (e.g., excluded by level or pattern).
- Confirm if logs are **delivered** to the expected destination (console, file, SIEM).

---

## **2. Common Issues and Fixes**

### **Issue 1: Logs Not Being Written**
**Symptom:** No logs appear in the expected location (file, console, SIEM).

#### **Root Causes & Fixes**
| **Cause**                          | **Fix (Code Example)**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Logger not initialized**         | Ensure the logger is properly instantiated (e.g., `logging.basicConfig()` in Python). |
| **Incorrect log level**            | Set the correct log level (e.g., `logging.getLogger().setLevel(logging.INFO)`).      |
| **Log file not writable**          | Check permissions (`chmod 644 /var/log/app.log`) or use relative paths.             |
| **Handler not configured**         | Add a proper handler (e.g., `FileHandler`, `StreamHandler`).                          |
| **Async logger blocking**          | If using `async` logging, ensure proper queuing and worker setup.                   |

**Example (Python - Minimal Logger Setup):**
```python
import logging

logging.basicConfig(
    level=logging.INFO,  # Only log INFO and above
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Write to file
        logging.StreamHandler()            # Also print to console
    ]
)
logger = logging.getLogger(__name__)
logger.info("This is a test log message.")  # Should appear in both file & console
```

**Common Mistake:**
❌ Forgetting to call `logging.basicConfig()` before logging.
✅ Always initialize logging **before** any log calls.

---

### **Issue 2: Logs Too Verbose (High Volume)**
**Symptom:** Logs flood production, making debugging difficult.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix (Code Example)**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Debug/Trace logs in production** | Set log level to `INFO` (or higher) in production.                                   |
| **Unnecessary third-party logs**   | Filter third-party libraries (e.g., `requests`, `SQLAlchemy`) using `logger.disabled`. |
| **Log format too heavy**           | Optimize log format (avoid JSON serialization in high-volume logs).                 |

**Example (Python - Filtering Unwanted Logs):**
```python
import logging

# Disable logging for a specific library
logging.getLogger("requests").setLevel(logging.WARNING)  # Only log WARNING and above
logging.getLogger("urllib3").setLevel(logging.ERROR)     # Only log ERRORS

# Set overall log level
logging.getLogger().setLevel(logging.INFO)
```

**Best Practice:**
- Use **different log levels** (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- **Exclude non-critical logs** in production (e.g., `DEBUG` level).

---

### **Issue 3: Critical Errors Not Logged**
**Symptom:** Application crashes silently without logs.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix (Code Example)**                                                                 |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Exception not caught**           | Wrap critical sections in `try-except`.                                             |
| **Logger not configured for errors**| Ensure `ERROR` level is enabled and exceptions are logged.                          |
| **Silent failure in async tasks**  | Use `asyncio.get_event_loop().run_until_complete()` with error handling.            |

**Example (Python - Catching and Logging Exceptions):**
```python
import logging

logger = logging.getLogger(__name__)

try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed: %s", str(e), exc_info=True)  # Log full traceback
```

**Key Fixes:**
✅ **Always log exceptions with `exc_info=True`.**
✅ **Use structured logging** (e.g., `{"error": "details", "stack_trace": str(e)}`).

---

### **Issue 4: Logs Not Reaching Central Logging (ELK, Splunk, etc.)**
**Symptom:** Logs appear locally but not in the SIEM/centralized log system.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                               |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Failed log shipment**            | Check if log forwarder (Fluentd, Logstash, AWS CloudWatch) is running.                |
| **Dead letter queue full**         | Flush logs periodically or increase queue capacity.                                  |
| **Network issues**                 | Verify network connectivity between app and log collector.                            |
| **Incorrect log format**           | Ensure logs follow the expected format (e.g., JSON for ELK).                         |

**Example (Python - Shipping Logs to a Central System with `logging.handlers.SysLogHandler`):**
```python
import logging
from logging.handlers import SysLogHandler

syslog_handler = SysLogHandler(address=("localhost", 514))  # UDP port 514
syslog_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logging.getLogger().addHandler(syslog_handler)
```

**Debugging Steps:**
1. **Check log forwarder logs** (e.g., `/var/log/fluentd/fluentd.log`).
2. **Test with a simple `echo` log** to confirm shipment works.
3. **Monitor network traffic** (`tcpdump -i eth0 port 514`).

---

### **Issue 5: Logs Out of Order or Delayed**
**Symptom:** Logs appear in the wrong sequence, making debugging chaotic.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                               |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Async logging with buffering**   | Ensure proper synchronization (e.g., `logging.shutdown()` before app exit).         |
| **Multiple loggers competing**     | Use a single logger instance or structured IDs.                                    |
| **Clock skew between nodes**       | Ensure all servers sync time (NTP).                                                 |

**Example (Python - Ensuring Log Order in Async Apps):**
```python
import logging
import threading

logger = logging.getLogger(__name__)
logger_lock = threading.Lock()

def safe_log(message):
    with logger_lock:
        logger.info(message)
```

**Best Practice:**
- **Use `asctime` in log format** (`%(asctime)s`).
- **Avoid async logging in critical sections.**

---

### **Issue 6: Performance Degradation Due to Logging**
**Symptom:** Application slows down due to heavy logging.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                               |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Excessive JSON serialization**   | Use string formatting instead of `json.dumps()` in hot paths.                       |
| **Disk I/O bottlenecks**           | Rotate logs (`FileHandler` with `maxBytes`).                                       |
| **High-frequency debug logs**      | Batch logs or suppress them in production.                                         |

**Example (Python - Optimized Logging):**
```python
# Avoid JSON in performance-critical code
logger.info("User %s logged in", username)  # Fast (no serialization)
# vs.
logger.info(json.dumps({"user": username, "action": "login"}))  # Slow
```

**Optimizations:**
✔ **Use `logging.warning()` instead of `print()`** (faster).
✔ **Rotate logs** (`maxBytes=10MB`, `backupCount=5`).
✔ **Disable debug logs in production** (`logging.getLogger("DEBUG").disabled = True`).

---

### **Issue 7: Sensitive Data Leaked in Logs**
**Symptom:** Logs contain passwords, tokens, or PII.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                               |
|------------------------------------|--------------------------------------------------------------------------------------|
| **Unmasked credentials**           | Replace sensitive fields with `****` or tokens.                                      |
| **Log format includes raw data**   | Use structured logging and omit sensitive fields.                                   |
| **Log retention too long**         | Rotate and purge logs with sensitive data.                                           |

**Example (Python - Masking Sensitive Data):**
```python
import logging

def log_user_action(user_id, password):
    masked_password = "*****"  # or use `hashlib.sha256(password).hexdigest()`
    logger.info(f"User {user_id} logged in. Credential masked: {masked_password}")
```

**Best Practices:**
✅ **Never log raw passwords/tokens.**
✅ **Use environment variables** for secrets (e.g., `os.getenv("DB_PASSWORD")`).
✅ **Rotate logs automatically** (`logrotate`).

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**          | **Purpose**                                                                 | **Example Usage**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **`strace` (Linux)**        | Trace system calls (e.g., file permissions, network issues).                | `strace -e trace=open,write python app.py`                                     |
| **`logrotate`**            | Manage log file rotation and cleanup.                                      | Edit `/etc/logrotate.conf` to configure retention policies.                   |
| **Fluentd (Log Forwarder)** | Centralize and filter logs before shipment.                                | Configure `/etc/td-agent/td-agent.conf` to filter sensitive logs.              |
| **Prometheus + Grafana**   | Monitor log volume and latency.                                             | Set up alerts for `log_volume > 10MB/min`.                                    |
| **`jq` (for JSON Logs)**    | Parse and filter structured logs.                                           | `journalctl | grep ERROR | jq '.msg' | less`                                  |
| **Distributed Tracing (OpenTelemetry)** | Correlate logs across microservices. | Instrument code with `opentelemetry-sdk`.                                      |
| **`tail -f` + `grep`**     | Quickly check live logs.                                                     | `tail -f /var/log/app.log | grep "ERROR"`                              |
| **`awslogs` (AWS)**         | Debug CloudWatch Logs delivery issues.                                       | Check `/var/log/awslogs/` for errors.                                          |

**Advanced Debugging:**
- **Use `logging.handlers.RotatingFileHandler`** to prevent disk overload.
- **Enable `logging.handlers.SysLogHandler`** for network-based logging.
- **Test with `stderr` first** before integrating with centralized logging.

---

## **4. Prevention Strategies**

### **Best Practices for Logging**
1. **Follow the 12-Factor App Logging Principles**
   - Outgoing logs are the responsibility of the app (not the OS).
   - Treat logs as event streams (not files).
   - Use structured logging (JSON) for easier parsing.

2. **Implement Log Levels Properly**
   | **Level** | **Use Case**                          |
   |-----------|---------------------------------------|
   | `DEBUG`   | Detailed internal logs (dev only).    |
   | `INFO`    | General application flow.             |
   | `WARNING` | Potential issues (e.g., retry limits). |
   | `ERROR`   | Critical failures.                    |
   | `CRITICAL`| System-breaking errors.               |

3. **Use Structured Logging (JSON)**
   ```python
   import logging
   import json

   logger = logging.getLogger(__name__)

   def log_event(event_type, data):
       log_entry = {
           "timestamp": datetime.utcnow().isoformat(),
           "event": event_type,
           "data": data
       }
       logger.info(json.dumps(log_entry))
   ```

4. **Automate Log Rotation & Retention**
   - Configure `logrotate` (Linux) or CloudWatch Logs (AWS).
   - Example `/etc/logrotate.d/app`:
     ```
     /var/log/app.log {
         daily
         missingok
         rotate 7
         compress
         delaycompress
         notifempty
         create 640 root adm
     }
     ```

5. **Centralize Logs with a SIEM**
   - Tools: **ELK Stack, Splunk, Datadog, AWS CloudWatch**.
   - Ensure **secure transport** (TLS for log shipment).

6. **Mask Sensitive Data**
   - Use **environment variables** for secrets.
   - Implement **log redaction** (e.g., `mc-log-replay` for Splunk).

7. **Monitor Log Volume & Performance**
   - Set up **alerts** for sudden log spikes.
   - Use **sampling** for high-volume logs (e.g., log every 10th request in `DEBUG`).

8. **Test Logging in CI/CD**
   - Ensure logs work in **staging before production**.
   - Use **log simulation** in unit tests:
     ```python
     import logging
     import unittest
     from unittest.mock import patch

     class TestLogging(unittest.TestCase):
         @patch('logging.getLogger')
         def test_log_called(self, mock_logger):
             logger = mock_logger.return_value
             logger.info("Test log")
             self.assertEqual(logger.info.call_count, 1)
     ```

---

## **5. Quick Resolution Checklist**
| **Problem**               | **Immediate Fix**                                                                 | **Long-Term Solution**                                                          |
|---------------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| No logs appear            | Check `logging.basicConfig()` and handler setup.                                   | Use a logging library (e.g., `structlog`, `loguru`) for better defaults.     |
| Logs too verbose          | Set `logger.setLevel(logging.INFO)`.                                               | Implement log filtering in the logging pipeline (e.g., Fluentd).             |
| Critical errors missing   | Catch exceptions and log with `exc_info=True`.                                     | Use an error tracking tool (e.g., Sentry, Datadog).                          |
| Logs not centralizing     | Test `SysLogHandler` or check Fluentd logs.                                       | Use a dedicated log shipper (e.g., `logstash-forwarder`).                      |
| Performance issues        | Disable debug logs; optimize log format.                                          | Use async logging carefully (e.g., `logging.asynclogging`).                   |
| Sensitive data leaked     | Manually mask logs in code.                                                       | Implement automated redaction (e.g., `logmask` for Splunk).                   |

---

## **Final Recommendations**
1. **Start Simple:** Use `logging` (Python), `log4j` (Java), or `logrus` (Go) before moving to advanced tools.
2. **Standardize Log Format:** JSON is widely supported (ELK, Splunk).
3. **Automate Everything:** Rotation, retention, and monitoring.
4. **Security First:** Mask secrets; rotate logs; encrypt in transit.
5. **Test Logs Early:** Verify logging works in **local dev → staging → prod** stages.

By following this guide, you can quickly diagnose, fix, and prevent logging-related issues, ensuring your backend remains observable and reliable.