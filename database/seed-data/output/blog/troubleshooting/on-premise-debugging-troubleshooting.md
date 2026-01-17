# **Debugging On-Premise Debugging: A Troubleshooting Guide**
*Quickly diagnose and resolve backend issues in controlled environments*

---

## **1. Introduction**
On-premise debugging involves fixing and diagnosing issues in locally hosted infrastructure, applications, and services rather than relying on cloud-based logs or remote debugging tools. Unlike cloud debugging, on-premise environments require direct access to physical or virtual machines, logs, and backend processes.

This guide provides a structured approach to troubleshooting common **on-premise backend issues**, focusing on efficiency and quick resolution.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the symptoms to narrow down the problem:

| **Category**          | **Symptoms** |
|-----------------------|-------------|
| **Application Crashes** | App restarts unexpectedly, 500 errors, `OutOfMemoryError` |
| **Performance Degradation** | Sluggish response times, high CPU/memory usage, timeouts |
| **Network Issues** | Connection timeouts, DNS resolution failures, slow DB queries |
| **Dependency Failures** | External API timeouts, database connection drops, cache failures |
| **Logging/Monitoring Missing** | No logs, incomplete telemetry, missing error traces |
| **Authentication/Authorization** | Users locked out, RBAC misconfigurations, token expiration |
| **Hardware Failures** | Disk failures, overheating, power supply issues |

*Action:* Record **symptoms in chronological order** (e.g., timestamps, error messages) before proceeding.

---

## **3. Common Issues & Fixes**

### **3.1. Application Crashes (NullPointerException, OutOfMemoryError)**
**Symptoms:**
- App crashes silently or with stack traces.
- Logs show `NullPointerException` or `OutOfMemoryError`.

**Root Causes:**
- Missing dependency injection.
- Unhandled exceptions in critical paths.
- Memory leaks (e.g., caching issues).

**Fixes:**
#### **A. Log Full Stack Traces**
Add logging middleware (e.g., **Log4j, Winston.js, or Java’s `logging.properties`**) to capture full stack traces.

**Example (Node.js):**
```javascript
app.use((err, req, res, next) => {
  console.error(err.stack); // Log full stack trace
  res.status(500).send('Something broke!');
});
```

#### **B. Fix Memory Leaks**
Check heap dumps (Java) or heap snapshots (Node.js) to identify leaks.

**Example (Java - Using VisualVM):**
1. Enable JVM heap dump:
   ```bash
   javac -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp/heapdump.hprof yourApp.jar
   ```
2. Analyze with **Eclipse MAT** or **VisualVM**.

**For Node.js:**
```bash
node --inspect --inspect-port=9229 yourApp.js
```
Use Chrome DevTools to inspect memory usage.

#### **C. NullPointerException Handling**
Ensure proper null checks or use defensive programming.

**Example (Java):**
```java
if (user == null) {
    throw new IllegalArgumentException("User cannot be null");
}
```

---

### **3.2. Performance Degradation (Slow Queries, High CPU)**
**Symptoms:**
- Application responds slowly after a sudden workload spike.
- Database queries take >1s.
- CPU usage near 100%.

**Root Causes:**
- Inefficient SQL queries.
- Unoptimized algorithms.
- Lack of caching.

**Fixes:**
#### **A. Optimize SQL Queries**
Use **EXPLAIN ANALYZE** (PostgreSQL) to identify slow queries.

**Example (PostgreSQL):**
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE status = 'active';
```

**Fix:**
- Add indexes:
  ```sql
  CREATE INDEX idx_users_status ON users(status);
  ```
- Use query caching (Redis, Memcached).

#### **B. Profile CPU Usage (Java/Node.js)**
- **Java:** Use **JProfiler** or **Async Profiler**.
- **Node.js:** Use **Clinic.js** or Chrome DevTools.

**Example (Node.js - Async Profiler):**
```bash
async-profiler start --duration=60s --cpu
```

#### **C. Implement Rate Limiting**
Prevent overload with **Express Rate Limiter** (Node.js) or **Guava RateLimiter** (Java).

**Example (Node.js):**
```javascript
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
app.use(limiter);
```

---

### **3.3. Network Issues (Timeouts, DNS Failures)**
**Symptoms:**
- API calls failing with `Connection Timeout`.
- DNS resolution failing (`nslookup` not working).

**Root Causes:**
- Misconfigured proxy/firewall.
- DNS server failure.
- Network partition (e.g., Kubernetes pod network issues).

**Fixes:**
#### **A. Check Connectivity**
- **Ping & Traceroute:**
  ```bash
  ping <database-ip>
  traceroute <external-api>
  ```
- **Check Firewall Rules:**
  ```bash
  sudo iptables -L  # Linux
  netsh advfirewall show allprofiles  # Windows
  ```

#### **B. Debug API Calls (Postman/cURL)**
```bash
curl -v http://api.example.com/users
```
Look for **HTTP 5xx errors** or **DNS resolution failures**.

#### **C. Retry Mechanisms**
Implement **exponential backoff** in your application.

**Example (Java - Resilience4j):**
```java
RetryConfig retryConfig = RetryConfig.custom()
    .maxAttempts(3)
    .waitDuration(Duration.ofSeconds(1))
    .build();
Retry retry = Retry.of("myRetry", retryConfig);
```

---

### **3.4. Missing/Incomplete Logs**
**Symptoms:**
- No logs in application logs directory.
- Log rotation causing gaps.

**Fixes:**
#### **A. Configure Log Rotation**
Use **Logrotate** (Linux) or **Winlogbeat** (Windows).

**Example (Logrotate Config):**
```
/var/log/myapp/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

#### **B. Centralize Logging (ELK Stack, Splunk)**
Use **Fluentd** to forward logs to **Elasticsearch**.

**Example (Fluentd Config for Node.js):**
```conf
<source>
  @type tail
  path /var/log/myapp/app.log
  pos_file /var/log/td-agent/pos_app.log
</source>

<filter>
  @type parser
  key_name log
  reserve_data true
  <parse>
    @type json
  </parse>
</filter>

<match **>
  @type elasticsearch
  host elasticsearch
  port 9200
</match>
```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Purpose**                          | **Use Case** |
|-------------------------|--------------------------------------|--------------|
| **tldr**                | Simplified man pages                  | Quick CLI reference |
| **strace**              | System call tracing                  | Debugging slow syscalls |
| **lsof**                | List open files/ports                | Find stuck connections |
| **tcpdump/Wireshark**   | Network packet analysis              | Analyze HTTP traffic |
| **JVM Flight Recorder** | Low-overhead Java profiling          | Memory/CPU issues |
| **Kubernetes `kubectl debug`** | Debug running pods | Container issues |
| **GDB (GNU Debugger)**  | Binary-level debugging               | Crash dumps |

**Example (Using `strace`):**
```bash
strace -f -o /tmp/app_trace.log ./your_app_server
```
Check for slow `open()`/`read()` calls.

---

## **5. Prevention Strategies**
| **Strategy**               | **Action** |
|----------------------------|------------|
| **Logging Best Practices**  | Structured logs (JSON), retention policies. |
| **Automated Monitoring**   | Prometheus + Grafana for metrics. |
| **Infrastructure as Code (IaC)** | Terraform/Ansible to avoid config drift. |
| **Chaos Engineering**      | Use **Gremlin** to test failure resilience. |
| **Blue-Green Deployments** | Reduce downtime risks. |
| **Regular Backups**        | Ensure quick recovery from disk failures. |

---

## **6. Step-by-Step Debugging Workflow**
1. **Reproduce the Issue** → Confirm symptoms.
2. **Check Logs** → Use `tail -f /var/log/app.log`.
3. **Isolate the Component** → Is it DB, network, or app?
4. **Apply Fixes** → Use tools (GDB, `strace`, profiling).
5. **Test & Monitor** → Verify fix with load testing (`ab`, `k6`).
6. **Document** → Update runbooks for future incidents.

---

## **7. Final Checklist Before Closing an Issue**
✅ **Symptoms logged** (with timestamps).
✅ **Root cause identified**.
✅ **Fix implemented & tested**.
✅ **Monitoring confirmed** (no regressions).
✅ **Documentation updated**.

---
**Next Steps:**
- **For recurring issues:** Automate detection (e.g., Prometheus alerts).
- **For complex debugging:** Use **debugging containers** (Docker + VS Code Remote Debugging).

---
**End of Guide** 🚀
*Need deeper debugging? Check out:*
- [Java Debugging Guide](https://www.baeldung.com/)
- [Node.js Debugging with Node Inspector](https://nodejs.org/api/inspector.html)