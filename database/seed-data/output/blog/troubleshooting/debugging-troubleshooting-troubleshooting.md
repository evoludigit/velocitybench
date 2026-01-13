# **Debugging *Troubleshooting*: A Practical Guide**
*When debugging debugging itself (i.e., fixing issues in debugging code, logs, or monitoring systems).*

---

## **1. Introduction**
This guide focuses on debugging **debugging**—a meta-problem where the tools, logs, or processes used to identify issues themselves are malfunctioning. Common scenarios include:
- Crashes in debug probe code (e.g., Python’s `logging`, Java’s `System.out.println`, or observability agents).
- Broken monitoring dashboards or missing telemetry.
- Incorrect error reporting or false positives in alerts.
- Debugging tools (e.g., Chrome DevTools, `strace`, or APM agents) failing to collect data.
- Circular dependencies in debug configurations (e.g., a debug script that fails because it relies on a service that’s dead).

This guide assumes you’re already familiar with basic debugging. Here, we’ll dig into **debugging the debugging process itself**.

---

## **2. Symptom Checklist**
Before diving into fixes, quickly verify these symptoms to narrow the scope:

| **Symptom**                          | **Likely Cause**                          | **Quick Check**                                                                 |
|--------------------------------------|------------------------------------------|---------------------------------------------------------------------------------|
| Debug logs are missing or corrupted. | Log shipping broken, rotation not working. | Check disk space (`df -h`), log file timestamps (`ls -lt /var/log/`).          |
| Debug probes crash on startup.       | Configuration misaligned, permissions.   | Review debug probe logs (e.g., `journalctl -u my-debug-service`).               |
| Alerts trigger for "missing data."   | Timeouts, rate limits, or agent crashes.  | Test endpoint manually (`curl http://localhost:8080/health`).                   |
| Debug tools hang or respond slowly.  | High CPU/memory, feature toggles off.     | Run `top`/`htop`; check for `OOMKilled` processes.                            |
| Circular dependencies in debug setup.| Services depend on each other in debug mode. | Temporarily disable half the dependencies to isolate the issue.               |
| "Success" logs but no actionable data.| Incorrect filtering or aggregation.      | Verify log format (e.g., JSON parsing errors) or query samples manually.       |

---
## **3. Common Issues and Fixes**
### **3.1 Debug Logs Not Appearing**
**Symptom:** Critical logs vanish during operations, leaving no trace.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Code Example**                                                                 |
|------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Log rotation truncating files.    | Configure retention (e.g., `logrotate`).                               | **Linux (`/etc/logrotate.d/app`):**                                             |
|                                    |                                                                         | `*/var/log/myapp.log { daily size 10M rotate 7 missingok copytruncate }`        |
| Log shipping (e.g., Fluentd/Logstash) dead. | Restart agent; check for errors.                                        | **Fluentd Check:**                                                                 |
|                                    |                                                                         | ```bash                                                                          |
|                                    | `journalctl -u fluentd --no-pager`                                        |                                                                                 |
| Wrong log level set.              | Lower log level (e.g., `DEBUG` instead of `INFO`).                      | **Python (`logging`):**                                                           |
|                                    |                                                                         | ```python                                                                         |
|                                    | `import logging; logging.basicConfig(level=logging.DEBUG)`              |                                                                                 |
| Log probe crashes silently.       | Add exception handling to probes.                                       | **Java (Logging Wrapper):**                                                         |
|                                    |                                                                         | ```java                                                                           |
|                                    | `try { Logger.debug("Check status"); } catch (Exception e) {            |                                                                                 |
|                                    |   Logger.error("Debug probe failed", e); }`                             |                                                                                 |

---

### **3.2 Debug Probes Crash on Startup**
**Symptom:** Debug scripts or agents (e.g., OpenTelemetry collectors, `strace`) fail to initialize.

#### **Common Fixes**
| **Issue**                           | **Fix**                                                                 | **Example**                                                                       |
|-------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Missing environment variables.      | Set defaults or require explicit config.                                | **Bash Script:**                                                                   |
|                                     |                                                                         | ```bash                                                                           |
|                                     | `DEBUG_LEVEL=${DEBUG_LEVEL:-INFO}`                                       |                                                                                 |
| Incorrect permissions.             | Run probes as non-root or adjust file permissions.                     | **Linux:**                                                                         |
|                                     |                                                                         | ```bash                                                                           |
|                                     | `chmod +x /path/to/debug-probe`                                          |                                                                                 |
| Probe depends on a dead service.    | Use health checks or timeouts.                                           | **Python (`requests` with timeout):**                                             |
|                                     |                                                                         | ```python                                                                         |
|                                     | `import requests; requests.get("http://dead-service/api", timeout=2)`   |                                                                                 |
| Debug probe logs to nowhere.       | Redirect stderr/stdout to files.                                         | **Go:**                                                                             |
|                                     |                                                                         | ```go                                                                             |
|                                     | `func main() { log.SetOutput(os.Stdout); log.Println("Debugging") }`    |                                                                                 |

---

### **3.3 Alerts Trigger for "Missing Data"**
**Symptom:** APM tools (e.g., Datadog, Prometheus) alert that metrics are missing, even though the app works.

#### **Root Causes**
- **Agent configuration mismatch:** Probe endpoint or tags are wrong.
- **Network issues:** Firewalls blocking agent-to-tool communication.
- **Rate limiting:** Cloud provider throttling requests.

#### **Fixes**
| **Issue**                           | **Fix**                                                                 | **Example**                                                                       |
|-------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| Wrong endpoint in config.          | Verify agent host/port in config.                                        | **OpenTelemetry Config (`otlp-config.yml`):**                                     |
|                                     |                                                                         | `service: http://correct-agent-host:4317`                                       |
| Firewall blocking metrics.         | Whitelist agent IPs/ports.                                              | **AWS Security Group Rule:**                                                     |
|                                     |                                                                         | `Type: UDP/TCP, Port: 4317, Source: Agent’s CIDR`                              |
| Rate limiting in cloud provider.  | Increase quotas or batch requests.                                       | **Prometheus Alert Rule (adjust interval):**                                     |
|                                     |                                                                         | ```yaml                                                                           |
|                                     | `interval: 30s`                                                           |                                                                                 |

---

### **3.4 Circular Dependencies in Debug Setup**
**Symptom:** Debug scripts fail because they depend on services that are also being debugged.

#### **Example Scenario**
- A debug script calls `ServiceA`, which calls `ServiceB`, which calls the debug script.
- **Fix:** Isolate debug dependencies.

#### **Solutions**
| **Approach**                        | **Implementations**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------------|
| **Mock external services.**         | Use `nock` (HTTP), `Mockito` (Java), or `pytest-mock` (Python).                  |
|                                     | **Python Example:**                                                               |
|                                     | ```python                                                                         |
|                                     | `import nock; nock('http://serviceB').get('/').reply(200, '{"status": "ok"}')`    |
| **Run in parallel.**              | Use `asyncio` or Docker containers to isolate processes.                         |
|                                     | **Docker Compose Example:**                                                      |
|                                     | ```yaml                                                                           |
|                                     | `debug-service: depends_on: { serviceA: { condition: service_healthy } }`       |
| **Disable circular deps temporarily.** | Comment out problematic calls during initial debugging.                          |

---

## **4. Debugging Tools and Techniques**
### **4.1 Logging Workflow**
1. **Temporary Log Injection:**
   Use `tee` or `script` to dump logs to a file while testing.
   ```bash
   script -f debug_session.log bash -c "your_debug_command"
   ```
2. **Structured Logging:**
   Enforce JSON/logging standards (e.g., `pino` in Node.js, `structlog` in Python).
   ```python
   import structlog
   structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
   structlog.logger.info("key=value", extra={"status": "debugging"})
   ```

### **4.2 Observability Debugging**
| **Tool**            | **Use Case**                                                                 | **Command/Example**                                                              |
|----------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `strace`            | Trace syscalls in debug probes.                                            | `strace -f -o debug_probe.log ./debug_script`                                  |
| `dtrace`/`perf`     | Profile CPU/memory in debug tools.                                         | `perf record -g ./debug_script`                                                 |
| `netstat`/`ss`      | Check if debug agents are reaching endpoints.                               | `ss -tulnp | grep 4317` (for OpenTelemetry)                                                 |
| `curl`/`httpie`     | Manually verify debug endpoints.                                           | `httpie POST http://localhost:8080/debug --json '{"level": "DEBUG"}'`           |
| `kubectl logs`      | Debug Kubernetes debugging pods.                                            | `kubectl logs -l app=debug-agent --previous`                                    |

### **4.3 Debugging Debugging Tools**
- **If `strace` fails:**
  Run in a container: `docker run --rm -it ubuntu strace -f ./debug_script`.
- **If APM agents crash:**
  Check their own logs (`/var/log/opentelemetry-agent.log`).
- **If logs are corrupted:**
  Use `grep` or `jq` to parse raw logs:
  ```bash
  grep -E '"level":"DEBUG"' /var/log/app.log | jq
  ```

---

## **5. Prevention Strategies**
### **5.1 Debug Configuration Management**
- **Use feature flags** for debug modes:
  ```python
  if feature_flags.is_debug_enabled():
      logging.debug("Debugging enabled")
  ```
- **Centralize debug configs** (e.g., GitOps with ArgoCD/Kustomize).
- **Add health checks** to debug probes:
  ```yaml
  # Kubernetes Liveness Probe
  livenessProbe:
    httpGet:
      path: /debug/health
      port: 8000
    initialDelaySeconds: 5
  ```

### **5.2 Automated Debug Validation**
- **Unit tests for debug probes:**
  ```python
  def test_debug_probe_runs():
      subprocess.run(["./debug_script", "--verbose"], check=True)
  ```
- **E2E tests** simulating debug workloads (e.g., `selenium` for browser devtools).
- **Synthetic monitoring** for debug endpoints (e.g., Pingdom, Datadog Synthetics).

### **5.3 Documentation**
- **Document debug workflows** (e.g., `CONTRIBUTING.md`):
  ```markdown
  ## Debugging Steps
  1. Enable debug logs: `export DEBUG=true`
  2. Run with: `./run.sh --debug`
  3. Check logs: `journalctl -u myapp -f --no-pager`
  ```
- **Keep a "debug toolbar"** (e.g., a Slack channel or GitHub issue template) for common debug scenarios.

### **5.4 Monitoring Debug Health**
- **Alert on debug probe failures** (e.g., Prometheus alert for `"debug_probe_status == 'CRASHED'"`).
- **Set up dashboards** for debug metrics (e.g., Grafana panel for log latency).
- **Automate log retention policies** (e.g., rotate logs nightly).

---

## **6. When All Else Fails: Nuclear Options**
1. **Revert to minimal debug setup:**
   - Disable all debug features except critical logging.
   ```bash
   # Example: Reset to default debug level
   export DEBUG=
   ```
2. **Switch to a simpler debug tool:**
   - Replace `strace` with `dtrace` if `strace` fails.
   - Use `echo` for quick log checks:
     ```bash
     echo "DEBUG: $(date)" >> /tmp/debug.log
     ```
3. **Isolate the system:**
   - Run the app in a container with no dependencies:
     ```bash
     docker run --rm -it ubuntu ./debug_script
     ```
4. **Manually inspect memory:**
   - Use `valgrind` or `pdb` (Python debugger):
     ```bash
     pdb ./debug_script.py
     ```

---

## **7. Case Study: Debugging a Debug Crash**
**Scenario:**
A debug script (`debug.py`) crashes on startup with `AttributeError: module 'debug' has no attribute 'probe'`.

**Steps:**
1. **Check the error:**
   ```bash
   python debug.py --debug
   ```
   Output:
   ```
   Traceback (most recent call last):
     File "debug.py", line 10, in <module>
       from debug.probe import initialize
     File "/app/debug/probe.py", line 1, in <module>
       import incorrect_module  # Typo in import!
   ```
2. **Fix the typo:**
   ```python
   # Incorrect:
   import incorrect_module
   # Correct:
   import correct_module
   ```
3. **Verify with a minimal test:**
   ```python
   def test_probe_import():
       import debug.probe
       assert hasattr(debug.probe, "initialize")
   ```

---

## **8. Summary Checklist for Debugging Debugging**
| **Step**                          | **Action**                                                                 |
|-----------------------------------|----------------------------------------------------------------------------|
| **Isolate the issue.**           | Disable half the debug setup to find the culprit.                         |
| **Check basics.**                | Logs, permissions, network (`ping`, `curl`).                             |
| **Use simple tools first.**      | `echo`, `script`, `strace` > complex agents.                             |
| **Document everything.**         | Log fixes in a shared doc or ticket.                                     |
| **Prevent recurrence.**          | Feature flags, automated tests, monitoring.                               |

---
**Final Tip:** If you’re debugging debugging, **simplify first**. Strip away half the debug tools and rebuild incrementally. The goal is to get *any* debug output, then expand from there.