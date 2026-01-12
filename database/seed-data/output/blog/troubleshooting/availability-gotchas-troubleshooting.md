# **Debugging Availability Gotchas: A Troubleshooting Guide**

## **Introduction**
Availability is a critical non-functional requirement for modern distributed systems. Poor availability can lead to downtime, degraded performance, and lost revenue. **"Availability Gotchas"** refer to subtle, often overlooked issues that can silently degrade system availability, such as resource leaks, cascading failures, improper circuit breakers, or inefficient scaling strategies.

This guide provides a structured approach to identifying, diagnosing, and resolving availability-related problems, with practical debugging techniques and code examples.

---

## **1. Symptom Checklist**
Before diving into debugging, verify if your system is suffering from availability issues. Common symptoms include:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|---------------------------------------------|
| **Intermittent service failures**    | Resource exhaustion, connection leaks       |
| **Sudden spikes in latency**         | Throttling, cascading failures              |
| **High error rates (5xx responses)** | Misconfigured retries, timeouts, or circuit breakers |
| **Unexpected scaling behavior**      | Improper load balancing, auto-scaling rules |
| **Database connection pool exhaustion** | Poor connection management, leaky queries   |
| **Memory leaks**                     | Accumulated object references, unused connections |
| **Unpredictable timeouts**           | Inconsistent retry logic, network issues    |
| **Unstable pod/container restarts**  | Resource limits exceeded, health checks failing |

If multiple symptoms appear simultaneously, **availability issues are likely the root cause**.

---

## **2. Common Issues and Fixes**

### **2.1. Resource Exhaustion (Memory, CPU, Connections)**
**Symptoms:**
- System crashes under load
- OOM (Out of Memory) errors
- Database connection pool depletion

**Cause:**
Unmanaged resources (e.g., open file handles, database connections, or memory leaks) can exhaust system limits.

#### **Fix: Implement Proper Resource Cleanup**
**Example (Java – Connection Pool Leak):**
```java
// ❌ Bad: Missing close() in finally block
public String fetchData() {
    try (Connection conn = dbPool.getConnection()) {
        // Use connection
    }
    // Connection is auto-closed, but if error occurs, leak can happen
}

// ✅ Good: Explicit cleanup in finally
public String fetchData() {
    Connection conn = null;
    try {
        conn = dbPool.getConnection();
        // Use connection
    } catch (SQLException e) {
        log.error("Failed to fetch data", e);
    } finally {
        if (conn != null) {
            conn.close();
        }
    }
}
```
**Fix (Python – Context Managers for DB Connections):**
```python
# ✅ Using context manager to auto-close connections
from contextlib import contextmanager
import psycopg2

@contextmanager
def get_db_connection():
    conn = psycopg2.connect("db_uri")
    try:
        yield conn
    finally:
        conn.close()

def fetch_data():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Query logic
```

**Prevention:**
- Use **connection pooling** (HikariCP, PgBouncer, JDBC pool).
- Implement **soft limits and warnings** before hitting hard limits.
- Monitor **connection/CPU/memory usage** in production.

---

### **2.2. Cascading Failures (Remote Dependency Failures)**
**Symptoms:**
- A single failure (e.g., DB timeout) causes chain reactions (e.g., API failures).
- High error rates after a minor outage.

**Cause:**
Lack of **retries, circuit breakers, or graceful degradation**.

#### **Fix: Implement Resilience Patterns**
**Example (Circuit Breaker in Node.js – `opossum` library):**
```javascript
const circuitBreaker = require('opossum');
const axios = require('axios');

const breaker = circuitBreaker(
  async (url) => await axios.get(url),
  { timeout: 5000, errorThresholdPercentage: 50, resetTimeout: 30000 }
);

async function fetchData() {
  try {
    return await breaker('https://api.example.com/data');
  } catch (err) {
    if (err instanceof circuitBreaker.CircuitBreakerError) {
      log.warning("Circuit breaker tripped, retrying later");
    }
    return fallbackData();
  }
}
```
**Example (Python – Retry with Exponential Backoff):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_unstable_api():
    try:
        response = requests.get("https://unreliable-api.com")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"Retrying after failure: {e}")
        raise
```

**Prevention:**
- Use **exponential backoff retries** (not fixed delays).
- Implement **circuit breakers** (Hystrix, Resilience4j).
- **Graceful degradation** (fallback responses, queueing for later processing).

---

### **2.3. Improper Load Balancing & Auto-Scaling**
**Symptoms:**
- Uneven traffic distribution
- Some nodes overloaded while others idle
- Auto-scaling triggers unexpectedly

**Cause:**
- **Sticky sessions** (affinity) not configured properly.
- **Poor scaling rules** (e.g., scaling out too late).
- **Cold starts** in serverless (if applicable).

#### **Fix: Optimize Load Balancing & Scaling**
**Example (Kubernetes – Horizontal Pod Autoscaler):**
```yaml
# ✅ Configure HPA with proper metrics (CPU, custom metrics)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: External  # Custom metrics (e.g., request latency)
      external:
        metric:
          name: myapp_request_latency
        target:
          type: AverageValue
          averageValue: 500  # ms
```
**Prevention:**
- Use **metric-based scaling** (not just CPU).
- **Warm-up requests** for cold starts (e.g., AWS Lambda provisioned concurrency).
- **Session affinity** only where necessary (e.g., for user sessions).

---

### **2.4. Timeouts & Unresponsive Services**
**Symptoms:**
- HTTP 504 Gateway Timeouts
- Long-running requests stuck
- Timeouts increase under load

**Cause:**
- **No reasonable timeout** on client/server calls.
- **Blocking I/O** (e.g., synchronous DB calls).
- **Slow background tasks** blocking main threads.

#### **Fix: Set Timeouts Properly**
**Example (Go – HTTP Client Timeout):**
```go
// ✅ Set timeout for HTTP requests
client := &http.Client{
    Timeout: 5 * time.Second,
}

resp, err := client.Get("https://slow-api.com")
if err != nil {
    log.Error("Request timed out", err)
}
```
**Example (Python – Async Timeout with `aiohttp`):**
```python
import aiohttp
import asyncio

async def fetch_with_timeout(url):
    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            return await resp.json()
```

**Prevention:**
- **Default timeouts** for all external calls.
- **Async I/O** where possible (e.g., `aiohttp`, `asyncio`).
- **Non-blocking background tasks** (e.g., Celery, Kafka, SQS).

---

### **2.5. Health Check Misconfigurations**
**Symptoms:**
- Pods/VMs marked as `CrashLoopBackOff`
- Load balancers dropping traffic to unhealthy instances
- Slow health check responses

**Cause:**
- **Health checks too slow** (blocking DB queries).
- **Incorrect readiness/liveness probe logic**.
- **External dependencies not included in checks**.

#### **Fix: Optimize Health Checks**
**Example (Kubernetes – Liveness Probe):**
```yaml
# ✅ Fast, non-blocking health check (e.g., HTTP endpoint)
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 2  # Very short!
```
**Prevention:**
- **Health checks should be fast** (no DB calls).
- **Include all dependencies** (e.g., check upstream services).
- **Use readiness probes** to avoid traffic to unready pods.

---

## **3. Debugging Tools and Techniques**

### **3.1. Logs & Distributed Tracing**
- **Centralized logging** (ELK, Loki, Datadog) to correlate failures.
- **Distributed tracing** (Jaeger, OpenTelemetry) to track requests across services.
- **Key log entries to check:**
  - Connection pool errors
  - Retry counts
  - Circuit breaker states
  - Auto-scaling events

**Example (OpenTelemetry Trace Analysis):**
```
✅ Normal Flow:
  API → DB (200ms) → Return (OK)
❌ Failed Flow:
  API → DB (Timeout) → Retry (500ms) → Circuit Breaker Tripped → Fallback
```

### **3.2. Metrics & Monitoring**
- **Key metrics to monitor:**
  - `connection_pool_used/connections` (e.g., Prometheus)
  - `http_server_requests_duration` (latency)
  - `error_rate` (5xx responses)
  - `memory_usage` (heap, GC time)
  - `pod_restart_count` (if using Kubernetes)

**Example (Prometheus Alert for High Latency):**
```yaml
# Alert if API latency > 1s for 5 minutes
- alert: HighRequestLatency
  expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High API latency detected"
```

### **3.3. Stress Testing & Chaos Engineering**
- **Simulate failures** (e.g., `chaos-mesh`, `chaoskube`).
- **Load test** with tools like **Locust, k6, JMeter**.
- **Chaos experiments:**
  - Kill random pods.
  - Simulate network partitions.
  - Inject latency.

**Example (Locust Load Test Script):**
```python
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def fetch_data(self):
        with self.client.get("/api/data", catch_response=True) as response:
            if response.status_code != 200:
                print(f"Failed: {response.status_code}")
```

### **3.4. Memory & Profiling Tools**
- **Heap dumps** (Java: VisualVM, Eclipse MAT).
- **CPU profiling** (Python: `py-spy`, Go: `pprof`).
- **Connection leak detection** (e.g., `jstack` for Java).

**Example (Go Pprof CPU Analysis):**
```bash
go tool pprof http://localhost:6060/debug/pprof/profile
# Analyze for high CPU usage
```

---

## **4. Prevention Strategies**

### **4.1. Design for Resilience**
- **Stateless services** (easy to scale).
- **Idempotent operations** (retries are safe).
- **Decoupled components** (event-driven architecture).
- **Graceful degradation** (fallback responses).

### **4.2. Automated Testing**
- **Chaos testing** in CI/CD.
- **Load testing** before deployments.
- **Unit tests for retries/circuit breakers**.

### **4.3. Observability First**
- **Logs:** Structured (JSON), not too verbose.
- **Metrics:** Per-request, per-service.
- **Traces:** End-to-end request flow.

### **4.4. Incident Response Plan**
- **Runbooks** for common availability issues.
- **Postmortems** to prevent recurrence.
- **Blame-free analysis** (focus on system design).

---

## **5. Summary Checklist**
| **Step** | **Action** |
|----------|------------|
| **Check logs** | Look for connection leaks, retries, circuit breaker trips. |
| **Monitor metrics** | High latency, error rates, resource exhaustion. |
| **Test assumptions** | Load test, chaos engineering. |
| **Fix root cause** | Implement timeouts, retries, circuit breakers. |
| **Prevent recurrence** | Automated checks, proper scaling, observability. |

---

## **Final Notes**
Availability issues are often **silent until they explode**. The key is **proactive monitoring, resilience patterns, and systematic debugging**.

**Next Steps:**
1. **Audit** your system for the issues above.
2. **Set up** proper logging, metrics, and tracing.
3. **Run load tests** to find weak points.
4. **Implement fixes** incrementally and validate.

By following this guide, you should be able to **quickly identify, debug, and resolve** availability-related issues in distributed systems. 🚀