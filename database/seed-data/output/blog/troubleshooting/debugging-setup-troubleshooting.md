# **Debugging Debugging Setup: A Troubleshooting Guide**
*A focused approach to diagnosing and resolving issues in debug configurations, logging, and debugging frameworks.*

---

## **1. Introduction**
Debugging setup refers to the infrastructure (logging, tracing, debugging tools, configuration, and monitoring) that allows developers to identify, replicate, and resolve production/pre-production issues efficiently. Problems in this setup can lead to blind spots, slow issue resolution, and missed outages.

This guide provides a structured approach to diagnosing debugging-related issues, ensuring quick resolution with minimal downtime.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these common symptoms:

✅ **Missing or Incomplete Logs**
   - Logs are missing entirely, truncated, or lack critical context.
   - Example: No exception stack traces in production logs.

✅ **Slow Debugging Experience**
   - Debugging tools (e.g., `pdb`, `chrome-devtools`, `postman`) behave unpredictably (hangs, crashes, or incorrect data).
   - Example: Debugger breaks at unexpected places in Python.

✅ **Incorrect Debug Configuration**
   - Debug settings (e.g., `DEBUG=True` in Django, `log.level` in logs) are misconfigured.
   - Example: Debug logs are written to production, exposing sensitive data.

✅ **Debug Tools Not Capturing Expected Data**
   - APM (Application Performance Monitoring) tools (e.g., Datadog, New Relic) show incorrect metrics or traces.
   - Example: `slow-log` filters capture too few/many requests.

✅ **Race Conditions in Debugging**
   - Debug probes (e.g., print statements, breakpoints) interfere with production behavior.
   - Example: A debug `print()` causes a thread deadlock.

✅ **Debug Data Not Persisting**
   - Debug outputs (logs, traces) are overwritten or lost (e.g., due to log rotation or disk issues).
   - Example: Critical logs from a production incident are lost after system reboot.

✅ **Debugging Tools Fail to Attach**
   - Debuggers (e.g., `gdb`, `lldb`, `VS Code debugger`) cannot attach to the process.
   - Example: `gdb` fails with "Process not found" on a Kubernetes pod.

---

## **3. Common Issues and Fixes**

### **Issue 1: Missing/Incomplete Logs**
**Symptoms:**
- No logs appear in log files or monitoring tools.
- Logs contain only generic messages (e.g., "request received").

**Root Causes & Fixes:**

| **Root Cause**               | **Fix**                                                                 | **Code/Config Example** |
|------------------------------|------------------------------------------------------------------------|-------------------------|
| Log level too high (e.g., `ERROR` when debug needed). | Lower log level (e.g., `DEBUG`). | ```python # Django settings LOGGING = { 'loggers': { 'myapp': { 'level': 'DEBUG', }, }, } ``` |
| Logging not configured for the framework. | Enable framework logging (e.g., `logging.basicConfig()` in Python). | ```python import logging logging.basicConfig(level=logging.DEBUG) ``` |
| Logs not written to the correct file. | Verify log file path and permissions. | ```ini [logging] handlers = file console file.filename = /var/log/myapp/debug.log ``` |
| Log rotation truncates logs. | Adjust log rotation settings. | ```ini [logrotate] /var/log/myapp/*.log { daily rotate 7 missingok compress delaycompress maxage 30 } ``` |
| Async logging race condition. | Use `logging.handlers.RotatingFileHandler` with proper buffering. | ```python import logging from logging.handlers import RotatingFileHandler handler = RotatingFileHandler( "debug.log", maxBytes=1024*1024, backupCount=5) ``` |

**Debugging Steps:**
1. Check log file location with `ls -l /var/log/myapp/` (Linux) or `Get-ChildItem "C:\logs\"` (Windows).
2. Run `journalctl -u myapp` (systemd) or `tail -f /var/log/myapp/debug.log` to verify real-time logs.
3. Temporarily set `loglevel=DEBUG` in production (if safe) and restart the service.

---

### **Issue 2: Slow Debugging Experience**
**Symptoms:**
- Debugger hangs on breakpoint.
- `pdb`/`lldb` slows down for large codebases.
- APM tools lag behind real-time requests.

**Root Causes & Fixes:**

| **Root Cause**               | **Fix**                                                                 | **Example** |
|------------------------------|------------------------------------------------------------------------|-------------|
| Debugger sampling too frequently. | Increase sampling interval in APM tools. | ```yaml # Datadog config distributed_tracing: sampling_rate: 0.1 ``` |
| Breakpoints in tight loops. | Use `pdb ±` to step out of loops. | In `pdb`: `pdb ± 10` (skip 10 steps) |
| Debugger breakpoints not working. | Verify debug symbols are loaded (`gdb`/`lldb`). | ```bash gdb ./myapp core core.core gcore ``` |
| Profiler overhead in debug mode. | Disable profiling in production. | ```python import cProfile; cProfile.runctx("main()", globals(), locals(), "profile.prof") ``` |

**Debugging Steps:**
1. For Python: Use `pdb.set_trace()` sparingly; prefer `print()` for quick checks.
2. For C/C++: Ensure debug symbols are built (`gcc -g`).
3. For APM tools: Check sampling rate and agent memory usage (`docker stats`).

---

### **Issue 3: Incorrect Debug Configuration**
**Symptoms:**
- Debug logs expose secrets (e.g., API keys).
- `DEBUG=True` in production causes performance issues.

**Root Causes & Fixes:**

| **Root Cause**               | **Fix**                                                                 | **Example** |
|------------------------------|------------------------------------------------------------------------|-------------|
| Hardcoded `DEBUG=True` in production. | Use environment variables. | ```python # Django settings.py DEBUG = os.getenv("DEBUG", "False") == "True" ``` |
| Logs include sensitive data. | Sanitize logs before writing. | ```python import re from myapp.models import Secret logging.warning(re.sub(r'\d{3}-\d{2}-\d{4}', 'XXX-XX-XXXX', sensitive_data)) ``` |
| Debug middleware enabled in production. | Disable debug middleware in production. | ```python # Middleware class DjangoDebugToolbar(Middleware): def __call__(self, request): if not request.META.get('HTTP_X_FORWARDED_FOR'):  # Only in dev return self.process_request(request) ``` |

**Debugging Steps:**
1. Audit log files for secrets using `grep`/`ack`:
   ```bash grep -r "api_key" /var/log/myapp/ | less ```
2. Use `.gitignore` to exclude `*.log` and debug configs from source control.
3. For Django: Set `DEBUG = False` in production `settings.py`.

---

### **Issue 4: Debug Tools Not Capturing Expected Data**
**Symptoms:**
- APM traces show no requests.
- `print()` statements missing in logs.

**Root Causes & Fixes:**

| **Root Cause**               | **Fix**                                                                 | **Example** |
|------------------------------|------------------------------------------------------------------------|-------------|
| APM agent not installed. | Install the agent (e.g., Datadog, New Relic). | ```bash # Kubectl inject datadog agent kubectl create -f https://raw.githubusercontent.com/DataDog/dd-agent/master/manifests/kubernetes/datadog-cluster-agent.yaml ``` |
| Logs not captured by APM. | Ensure agent is configured to ingest logs. | ```yaml # Datadog log_intake: enabled: true ``` |
| `print()` statements not appearing. | Use logging instead of `print()`. | ```python import logging logging.debug("This will appear in logs!") ``` |

**Debugging Steps:**
1. Verify APM agent is running:
   ```bash kubectl get pods | grep datadog-agent ```
2. Check agent logs for errors:
   ```bash kubectl logs <datadog-pod> ```
3. For custom logging, ensure handlers are set up:
   ```python logging.basicConfig(filename="/var/log/myapp/debug.log", level=logging.DEBUG) ```

---

### **Issue 5: Race Conditions in Debugging**
**Symptoms:**
- Debug `print()` causes thread hangs.
- APM traces show race conditions.

**Root Causes & Fixes:**

| **Root Cause**               | **Fix**                                                                 | **Example** |
|------------------------------|------------------------------------------------------------------------|-------------|
| Debug `print()` in a loop. | Use thread-safe logging. | ```python import logging from threading import Lock lock = Lock() def debug_print(msg): with lock: logging.debug(msg) ``` |
| Debugger attached to wrong thread. | Use `threading.enumerate()` to find the right thread. | ```python import threading for thread in threading.enumerate(): print(thread.name, thread.ident) ``` |
| APM sampling interferes with timing. | Disable APM sampling during critical sections. | ```python from datadog import trace @trace.segment('critical_section') def do_work(): ``` |

**Debugging Steps:**
1. Use `strace` to monitor system calls during hangs:
   ```bash strace -p <PID> ```
2. For Python, use `threading` module to inspect active threads:
   ```python import threading print(threading.enumerate()) ```
3. Avoid debug `print()` in release builds (build-time optimization removes them).

---

### **Issue 6: Debug Data Not Persisting**
**Symptoms:**
- Logs disappear after log rotation.
- APM traces vanish after a restart.

**Root Causes & Fixes:**

| **Root Cause**               | **Fix**                                                                 | **Example** |
|------------------------------|------------------------------------------------------------------------|-------------|
| Log rotation too aggressive. | Increase retention period. | ```ini /var/log/myapp/*.log { daily rotate 30 missingok compress delaycompress maxage 90 } ``` |
| APM agent not persisting traces. | Configure trace archiving. | ```yaml # Datadog tracing: archive_service: enabled: true ``` |
| Logs overwritten by new writes. | Use append mode (`a` in file mode). | ```python with open("debug.log", "a") as f: f.write("New debug info\n") ``` |

**Debugging Steps:**
1. Check log rotation config (`/etc/logrotate.conf`).
2. For APM, verify agent is configured to archive traces:
   ```bash kubectl exec <datadog-pod> -c datadog-agent -- datadog-status check trace-agent ```
3. Use cloud storage (e.g., S3) for long-term log retention.

---

## **4. Debugging Tools and Techniques**

### **Logging Tools**
| Tool               | Purpose                                  | Example Command                          |
|--------------------|------------------------------------------|------------------------------------------|
| `journalctl`       | View systemd logs.                       | `journalctl -u myapp -f`                  |
| `tail`             | Follow log files in real-time.           | `tail -f /var/log/myapp/debug.log`       |
| `logrotate`        | Manage log file rotation.                | `logrotate -f /etc/logrotate.conf`       |
| `elasticsearch`    | Centralized log search.                  | `curl -XGET 'localhost:9200/myapp/_search?pretty'` |
| `grep`/`ack`       | Search logs for keywords.                | `grep -r "ERROR" /var/log/`               |

### **Debugging Frameworks**
| Tool               | Language/Use Case                     | Key Features                          |
|--------------------|---------------------------------------|----------------------------------------|
| `pdb`              | Python debugging.                     | Breakpoints, post-mortem debugging.    |
| `gdb`/`lldb`       | C/C++/Rust debugging.                  | Core dumps, symbol inspection.         |
| `VS Code Debugger` | Multi-language debugger.               | GPU debugging, Docker support.         |
| `postman`          | API debugging.                         | Request/response inspection.           |
| `chrome-devtools` | Frontend debugging.                    | Network, console, performance tabs.    |

### **APM & Observability Tools**
| Tool               | Purpose                                  | Key Features                          |
|--------------------|------------------------------------------|----------------------------------------|
| Datadog            | Full-stack observability.                 | Distributed tracing, logs, metrics.   |
| New Relic          | APM for apps.                            | Transaction tracing, error tracking.   |
| Jaeger             | Distributed tracing.                     | Sampler-based tracing.                 |
| Prometheus         | Metrics monitoring.                      | Custom dashboards.                     |

### **Advanced Techniques**
1. **Core Dumps:**
   - Capture crashes in C/C++:
     ```bash gcore <PID> ```
   - Analyze with `gdb`:
     ```bash gdb ./myapp core core.core ```

2. **Thread Sanitizer (TSan):**
   - Detect race conditions in C/C++:
     ```bash clang -fsanitize=thread -g myapp.cc -o myapp ```

3. **Python `faulthandler`:**
   - Dump stack traces on crashes:
     ```python import faulthandler faulthandler.enable() ```

4. **Kubernetes Debugging:**
   - Exec into a pod:
     ```bash kubectl exec -it <pod> -- /bin/sh ```
   - Port-forward for debugging:
     ```bash kubectl port-forward <pod> 5678:5678 ```

---

## **5. Prevention Strategies**

### **Logging Best Practices**
1. **Use Structured Logging:**
   - JSON logs for easier parsing.
   ```python import json logging.info(json.dumps({"event": "user_login", "user_id": 123})) ```

2. **Avoid Debug `print()` in Production:**
   - Replace with logging:
   ```python logging.debug("Value: %s", some_var) ```

3. **Sanitize Logs:**
   - Obfuscate secrets:
   ```python logging.warning("User %s logged in", user_id)  # Instead of logging full password ```

4. **Centralize Logs:**
   - Use ELK Stack (Elasticsearch, Logstash, Kibana) or Datadog.

### **Debugging Configuration**
1. **Environment-Specific Settings:**
   - Use `.env` files for debug/prod differences.
   ```python # .env.prod DEBUG=False # .env.dev DEBUG=True ```

2. **Debug Mode Flags:**
   - Disable debug in production:
   ```python if os.getenv("DEBUG") == "True":  # Only enable in dev ```'

3. **Log Rotation Policies:**
   - Retain logs for 30-90 days:
   ```ini /var/log/myapp/*.log { daily rotate 7 missingok compress delaycompress maxage 90 } ```

### **APM & Observability**
1. **Enable Distributed Tracing:**
   - Use `jaeger-client` or Datadog tracing.

2. **Set Proper Sampling Rates:**
   - Avoid overwhelming APM tools:
   ```yaml # Datadog distributed_tracing: sampling_rate: 0.5 ```'

3. **Monitor Agent Health:**
   - Use `kubectl` or `systemctl` to check APM agents.

### **Code-Level Debugging**
1. **Use Debug Builds in Development:**
   - Enable optimizations in production:
   ```bash # Release build gcc -O3 myapp.c -o myapp # Debug build gcc -g -O0 myapp.c -o myapp-debug ```

2. **Avoid Debug Code in Release:**
   - Wrap debug statements in `if DEBUG:` blocks.

3. **Use Assertions for Debugging:**
   ```python assert some_var is not None, "some_var should not be None" ```

4. **Implement Post-Mortem Debugging:**
   - Use tools like `faulthandler` or `sentry` to capture crashes.

---

## **6. Summary Checklist for Quick Resolution**
| Step | Action |
|------|--------|
| **1** | Verify logs exist (`tail -f /var/log/myapp/debug.log`). |
| **2** | Check log levels (`DEBUG`, `INFO`, `ERROR`). |
| **3** | Validate APM agent is running (`kubectl get pods`). |
| **4** | Ensure debug flags are production-safe (`DEBUG=False`). |
| **5** | Use structured logging (JSON) for easier parsing. |
| **6** | Avoid `print()` in production; use logging instead. |
| **7** | Check for race conditions with `strace` or `TSan`. |
| **8** | Persist logs with proper rotation (`logrotate`). |
| **9** | Monitor APM agents for health issues. |
| **10** | Disable debug features in release builds. |

---

## **7. Final Notes**
Debugging setup issues are often a chain reaction (e.g., missing logs → inability to reproduce bugs → outages). The key is **proactive monitoring** and **environment separation** (dev/stage/prod).

- **For logs:** Use centralized tools (ELK, Datadog) and structured formats.
- **For debugging:** Deploy debug builds only in non-production.
- **For APM:** Configure proper sampling and agent health checks.

By following this guide, you’ll reduce debugging time from hours to minutes and prevent silent failures in production. Happy debugging! 🚀