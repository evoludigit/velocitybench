# **Debugging Availability: A Troubleshooting Guide**
*For Senior Backend Engineers*

---
## **Introduction**
Availability issues—whether due to hardware failures, misconfigurations, network latency, or misbehaving components—can disrupt services and degrade user experience. This guide focuses on **quickly identifying and resolving availability problems** by structuring a methodical debugging approach.

---

## **Symptom Checklist**
Before diving into fixes, ensure you’ve ruled out the following common symptoms:

| **Symptom**                          | **Description**                                                                 | **Severity** |
|--------------------------------------|-------------------------------------------------------------------------------|--------------|
| High error rates (5xx, 4xx)          | Unreachable services, timeouts, or failed requests.                          | Critical     |
| Slow response times (> 1s for API)   | Latency spikes, prolonged request processing.                                 | High         |
| Unreachable services (Ping/HTTP)     | Services not responding to health checks or client requests.                 | Critical     |
| Load balancer saturation            | Frontend services overwhelmed, requests queued or throttled.                  | Critical     |
| Database connection drops           | Sudden disconnects, queries failing with "connection refused."               | High         |
| External dependencies unavailable     | Third-party APIs, cache providers, or messaging systems failing.             | High         |
| Memory/CPU throttling                | Services crashing due to resource exhaustion.                                | High         |
| Race conditions or deadlocks         | Cyclic dependencies causing service hangs or timeouts.                      | Critical     |

---

## **Common Issues and Fixes**

### **1. Unreachable Services (HTTP/Ping Failures)**
**Symptom:** Services return `ERR_CONNECTION_REFUSED`, `503 Service Unavailable`, or `Connection Timeout`.

#### **Possible Causes & Fixes**
| **Root Cause**                     | **Debugging Steps**                                                                 | **Code/Fix Example** |
|------------------------------------|------------------------------------------------------------------------------------|-----------------------|
| **Network Partition**              | Check if pods/containers are up.                                                   | `kubectl get pods` (K8s) |
| **Misconfigured Service Discovery** | DNS resolution failing (e.g., incorrect `hosts` file, misaligned DNS records).     | **Fix:** Verify `/etc/hosts` or DNS settings. |
| **Firewall/Network ACLs**          | Ingress/egress traffic blocked by security groups or firewalls.                   | **Fix:** Open necessary ports in cloud security groups or `iptables`. |
| **Load Balancer Misconfiguration** | Backend health checks misconfigured or unhealthy endpoints excluded.               | **Fix:** Validate health check paths in LB settings. |
| **Container/VM Not Responding**    | Service crashed silently or stuck in `CrashLoopBackOff`.                           | **Fix:** Check logs: `kubectl logs <pod>`. |

**Sample Fix (Docker/K8s):**
```yaml
# Check if a deployment is stuck
kubectl describe deployment <deployment-name>

# Restart a pod (if stuck)
kubectl delete pod <pod-name> --grace-period=0 --force
```

---

### **2. High Latency (Slow API Responses)**
**Symptom:** Endpoints respond in **>1s** (threshold depends on use case; 100ms-500ms is ideal for most APIs).

#### **Possible Causes & Fixes**
| **Root Cause**                     | **Debugging Steps**                                                                 | **Fix** |
|------------------------------------|------------------------------------------------------------------------------------|---------|
| **Database Bottleneck**            | Slow queries, missing indexes, or connection pooling exhaustion.                    | **Check:** `EXPLAIN ANALYZE` on slow queries. |
| **Unoptimized Code**              | Synchronous blocking calls (e.g., `await` without async/await).                    | **Fix:** Use async/await or parallelize requests. |
| **Network Latency**                | External APIs, CDNs, or regional distance causing delays.                          | **Fix:** Cache responses or use a closer region. |
| **Overloaded Cache**              | Cache misses forcing full recomputation.                                           | **Fix:** Validate cache TTL and eviction policies. |

**Example (Optimizing Slow Queries):**
```sql
-- Before (slow)
SELECT * FROM users WHERE status = 'active';

-- After (optimized with index)
CREATE INDEX idx_users_status ON users(status);
```

**Code Example (Async vs. Sync):**
```javascript
// Bad: Blocking sync call
const data = await fetchSlowAPI(); // Hangs UI thread

// Good: Async/await or parallelize
const fetchMultiple = async () => {
  const [user1, user2] = await Promise.all([
    fetchUser1(),
    fetchUser2()
  ]);
};
```

---

### **3. Resource Exhaustion (OOM, Throttling)**
**Symptom:** Services crash with `OutOfMemory` or `CPU Throttling`.

#### **Possible Causes & Fixes**
| **Root Cause**                     | **Debugging Steps**                                                                 | **Fix** |
|------------------------------------|------------------------------------------------------------------------------------|---------|
| **Memory Leaks**                   | Unreleased objects accumulating over time.                                         | **Check:** `heapdump` (Node.js) or `gdb` (Java). |
| **Exponential Backoff Failures**   | Retries causing cascading failures (e.g., database overload).                     | **Fix:** Implement circuit breakers (`Hystrix`, `Resilience4j`). |
| **Too Many Open Connections**      | Connection pooling exhausted (e.g., database, HTTP clients).                      | **Fix:** Adjust pool size in config. |
| **Unbounded Logs**                 | Log files growing uncontrollably (e.g., `console.log` in loops).                   | **Fix:** Implement log rotation (`logrotate`). |

**Example (Java Connection Pooling):**
```java
// Before: Default pool may be too small
DataSource dataSource = DriverManagerDataSource();

// After: Configure pool size
DataSource dataSource = new HikariDataSource();
dataSource.setMaximumPoolSize(20);
```

---

### **4. External Dependency Failures**
**Symptom:** Third-party APIs, messaging queues, or caches fail intermittently.

#### **Debugging Steps**
1. **Check Dependency Status:**
   - If using **AWS SQS**, check `ApproximateNumberOfMessagesVisible`.
   - If using **Redis**, run `redis-cli info` to check connections.
2. **Retry Logic:**
   - Implement retries with exponential backoff.
3. **Fallback Mechanisms:**
   - Cache results locally or return stale data.

**Example (Exponential Backoff in Python):**
```python
import time

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

---

### **5. Race Conditions & Deadlocks**
**Symptom:** Services hang, timeouts, or corrupt data due to concurrent access.

#### **Debugging Steps**
1. **Check Locks:**
   - Are database transactions improperly nested?
   - Are in-memory locks being released?
2. **Thread Dumps:**
   - Capture thread states (`jstack` for Java, `gdb` for Go).
3. **Use Distributed Locks:**
   - Redis, ZooKeeper, or database-based locks.

**Example (Deadlock in Java):**
```java
// Bad: Potential deadlock
synchronized (lock1) {
    synchronized (lock2) { ... }
}

// Good: Acquire locks in consistent order
synchronized (lock1) { ... }
synchronized (lock2) { ... }
```

---

## **Debugging Tools and Techniques**

| **Tool/Technique**          | **Purpose**                                                                 | **Example Use Case** |
|-----------------------------|-----------------------------------------------------------------------------|----------------------|
| **APM Tools (Datadog, New Relic, Prometheus)** | Monitor latency, errors, and throughput in real-time.                     | Detecting 5xx error spikes. |
| **Distributed Tracing (OpenTelemetry, Jaeger)** | Trace requests across microservices.                                     | Identifying slow DB calls. |
| **Logging Aggregators (ELK, Loki)** | Centralize logs for correlation.                                          | Debugging a failed microservice. |
| **Health Checks (Liveness/Readiness Probes)** | Automatically restart unhealthy containers.                               | Auto-recovering failed pods. |
| **Chaos Engineering (Gremlin, Chaos Mesh)** | Test failure resilience by injecting synthetic failures.                  | Validating circuit breaker behavior. |
| **Network Tools (`tcpdump`, `Wireshark`, `netstat`)** | Inspect traffic for dropped packets or delays.                          | Diagnosing slow API responses. |
| **Load Testing (Locust, k6)** | Simulate traffic to find bottlenecks.                                      | Stress-testing before deployment. |

---

## **Prevention Strategies**

### **1. Infrastructure Resilience**
- **Multi-AZ Deployments:** Ensure services run across multiple availability zones.
- **Auto-Scaling:** Use K8s HPA or cloud auto-scaling based on CPU/memory.
- **Chaos Testing:** Regularly inject failures to validate recovery mechanisms.

### **2. Code-Level Resilience**
- **Circuit Breakers:** Prevent cascading failures (e.g., `Resilience4j`).
- **Retries with Backoff:** Handle transient failures gracefully.
- **Graceful Degradation:** Fall back to cached/partial data when needed.

### **3. Observability**
- **Metrics First:** Track latency, error rates, and saturation (e.g., Prometheus).
- **Structured Logging:** Use JSON logs for easy parsing (e.g., `pino`, `structlog`).
- **Distributed Tracing:** Correlate requests across services.

### **4. Proactive Monitoring**
- **Anomaly Detection:** Use ML-based tools (e.g., Amazon DevOps Guru) to detect issues early.
- **Synthetic Monitoring:** Simulate user actions to catch degraded performance.

### **5. Disaster Recovery**
- **Backup Strategies:** Regular DB snapshots, immutable backups.
- **Failover Testing:** Validate DR plans with tabletop exercises.

---

## **Quick Reference Cheat Sheet**
| **Issue**               | **First Steps**                          | **Tools to Use**               |
|--------------------------|------------------------------------------|---------------------------------|
| **Service Unreachable**  | Check `kubectl get pods`, `ping`, health checks. | `curl`, `telnet`, `kubectl logs` |
| **High Latency**         | Profile API calls, check DB queries.     | `traceroute`, `EXPLAIN ANALYZE` |
| **OOM Errors**           | Check memory usage, leaks.              | `top`, `htop`, `gdb`            |
| **Dependency Failures**  | Verify third-party status, retry logic. | `curl` (test external endpoints) |
| **Race Conditions**      | Capture thread dumps, use locks.         | `jstack`, `gdb`                 |

---

## **Conclusion**
Availability issues are rarely caused by a single factor. Follow this structured approach:
1. **Isolate the problem** (symptoms, logs, metrics).
2. **Reproduce** in a controlled environment (staging).
3. **Fix** with minimal changes (prefer configuration over code).
4. **Prevent recurrence** with resilience patterns and observability.

By combining **systemic debugging** (network, infrastructure) with **code-level fixes** (async, retries), you can restore availability quickly and reduce future outages.