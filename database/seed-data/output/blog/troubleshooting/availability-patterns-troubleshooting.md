# **Debugging Availability Patterns: A Troubleshooting Guide**

Availability Patterns are architectural strategies designed to ensure high system uptime, fault tolerance, and resilience under failure conditions. Common implementations include **active-passive redundancy, active-active clustering, circuit breakers, retries with backoff, and failover mechanisms**. This guide provides a structured approach to diagnosing and resolving availability-related issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, systematically check the following symptoms to narrow down the root cause:

### **User-Level Symptoms**
- [ ] **Service Unavailability**: End users report timeouts, 503 errors, or complete service failures.
- [ ] **Spikes in Latency**: Requests take significantly longer than expected (e.g., 500ms → 5s).
- [ ] **Inconsistent Behavior**: Some requests succeed while others fail intermittently.
- [ ] **Error Codes**: Check for HTTP 5xx, database connection errors, or external API failures.
- [ ] **Monitoring Alerts**: Are there spikes in error rates, high CPU/memory usage, or throttling events?

### **Infrastructure-Level Symptoms**
- [ ] **Node Failures**: Are specific instances crashing or becoming unresponsive?
- [ ] **Load Imbalance**: Are some nodes handling disproportionate traffic?
- [ ] **Dependency Failures**: Are downstream services (databases, APIs, caches) unreachable?
- [ ] **Network Issues**: Latency, packet loss, or DNS resolution failures?
- [ ] **Resource Exhaustion**: High disk I/O, memory leaks, or thrashing?

### **Log & Metric Clues**
- [ ] Logs indicate **circuit breakers tripping** (e.g., Hystrix, Resilience4j).
- [ ] Retry mechanisms are **failing to recover** from transient failures.
- [ ] Failover **not triggering** when expected.
- [ ] **Health checks** returning `UNHEALTHY` for critical components.
- [ ] Metrics show **snowflake spikes** (sudden, brief bursts of errors).

---
## **2. Common Issues & Fixes**

### **Issue 1: Circuit Breaker Tripping Too Aggressively**
**Symptom:**
- Application suddenly stops calling downstream services, leading to cascading failures.
- Logs show `CircuitBreaker.OPEN` state with high error rates.

**Root Cause:**
- The breach threshold (e.g., 50% error rate in 10 seconds) is too low.
- The circuit isn’t resetting (half-open state) properly due to slow recovery.

**Fix:**
```java
// Example: Adjusting Resilience4j Circuit Breaker config
CircuitBreakerConfig config = CircuitBreakerConfig.custom()
    .failureRateThreshold(70) // Allow 70% errors before tripping (default: 50)
    .waitDurationInOpenState(Duration.ofSeconds(30)) // Allow 30s recovery
    .slidingWindowSize(2) // Evaluate last 2 requests
    .permittedNumberOfCallsInHalfOpenState(3) // Test 3 calls before closing
    .build();

CircuitBreaker circuitBreaker = CircuitBreaker.of("externalApi", config);
```

**Debugging Steps:**
1. Check `CircuitBreakerMetrics` for `failureRate` and `transitionCount`.
2. Verify `waitDurationInOpenState` aligns with your SLO.
3. Log transitions (`OPEN → HALF_OPEN → CLOSED`).

---

### **Issue 2: Retry Mechanism Not Handling Failures Gracefully**
**Symptom:**
- Retries exhaust quickly, leading to cascading failures.
- Logs show `RetryLimitExceeded` or `TimeoutException`.

**Root Cause:**
- Fixed retry count without exponential backoff.
- Retries don’t account for **non-idempotent operations** (e.g., payments).
- No **jitter** to avoid thundering herd problems.

**Fix:**
```java
// Example: Configuring Retry with Backoff (Spring Retry)
@Retryable(
    maxAttempts = 3,
    backoff = @Backoff(delay = 1000, multiplier = 2),
    include = { IOException.class }
)
public void callExternalService() {
    // Logic
}
```

**Debugging Steps:**
1. Check retry logs for `attempt X of Y`.
2. Verify backoff delays are increasing (`1s, 2s, 4s`).
3. For non-idempotent calls, replace retries with **idempotency keys** or **compensating transactions**.

---

### **Issue 3: Failover Not Triggering When Expected**
**Symptom:**
- Primary node fails, but traffic isn’t routed to the standby.
- Load balancer health checks pass, but requests time out.

**Root Cause:**
- **Sticky sessions** prevent failover.
- **Health check thresholds** are too strict (e.g., `HTTP 200` required).
- **DNS propagation delay** for failover IPs.

**Fix:**
```yaml
# Example: NGINX Health Check Config
upstream backend {
    server primary.example.com:8080 max_fails=3 fail_timeout=30s;
    server standby.example.com:8080 backup;
}
```

**Debugging Steps:**
1. Test failover manually:
   ```bash
   curl -v http://primary.example.com/health  # Should fail
   curl -v http://standby.example.com/health   # Should succeed
   ```
2. Check load balancer logs for `fail_timeout` events.
3. For Kubernetes, verify `ReadinessProbes`:
   ```yaml
   livenessProbe:
     httpGet:
       path: /health
       port: 8080
     initialDelaySeconds: 5
     failureThreshold: 3
   ```

---

### **Issue 4: Database Failover Corruption or Lag**
**Symptom:**
- Read replicas fall behind, leading to stale data.
- Write operations fail with `Timeout` or `PrimaryHostDown` (MongoDB).

**Root Cause:**
- Replica lag due to high write load.
- **Read preference** set to `Primary` instead of `Secondary`.
- **Connection pooling** exhausted during failover.

**Fix:**
```java
// MongoDB: Configure Read Preference for Failover
MongoClientSettings settings = MongoClientSettings.builder()
    .readPreference(ReadPreference.secondaryPreferred())
    .build();
```

**Debugging Steps:**
1. Check replica set status:
   ```bash
   mongo --eval "rs.status()"
   ```
2. Monitor `oplogDelay` (should be <1s).
3. Test failover:
   ```bash
   rs.stepDown()  # Simulate primary failure
   ```

---

### **Issue 5: Node-Level Crashes (OOM, Thread Leaks)**
**Symptom:**
- Node restarts unexpectedly (`Killed` by OOM killer).
- Thread dump shows **deadlocks** or **stuck threads**.

**Root Cause:**
- **Memory leak** (e.g., unclosed DB connections).
- **Thread pool exhaustion** (e.g., no dynamic scaling).
- **Garbage collection pauses** freezing the JVM.

**Fix:**
```java
// Example: JVM Flags for Memory Leaks & GC
# Add to JVM opts
-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/path/to/dump.hprof
-XX:+UseG1GC -XX:MaxGCPauseMillis=200  # Limit GC pauses
```

**Debugging Steps:**
1. Capture a **heap dump** on OOM:
   ```bash
   jmap -dump:live,format=b,file=heap.hprof <pid>
   ```
2. Analyze with **Eclipse MAT** or `jhat`.
3. Check thread dumps for stuck threads:
   ```bash
   jstack <pid> > thread_dump.txt
   ```
4. Monitor GC logs:
   ```bash
   -Xlog:gc*:file=gc.log:time,uptime:filecount=5,filesize=10M
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                  | **Command/Usage**                          |
|-------------------------|---------------------------------------------|--------------------------------------------|
| **Prometheus + Grafana** | Monitor latency, error rates, circuit breaker states | `http_request_duration_seconds{}` |
| **OpenTelemetry**       | Distributed tracing for failures            | `otelcol --config file.yml`                |
| **Chaos Mesh/Chaos Monkey** | Inject failures to test resilience          | `kubectl apply -f chaos-mesh.yaml`         |
| **K6/Locust**           | Load test failover scenarios                | `k6 run --vus 100 script.js`               |
| **Jaeger**              | Trace request flows across services          | `jaeger ui`                                |
| **JvmStat**             | JVM metrics (GC, heap, threads)             | `jvmstat -gc <pid>`                        |
| **Netdata**             | Real-time infrastructure monitoring         | `netdata`                                  |
| **Postman/Newman**      | Test API failover endpoints                  | `newman run collection.json --reporters=cli` |

**Advanced Techniques:**
- **Chaos Engineering**: Intentionally kill nodes to test failover:
  ```bash
  # Kill a pod (Kubernetes)
  kubectl delete pod <pod-name> --grace-period=0 --force
  ```
- **Canary Deployments**: Route 5% traffic to a new version to test stability.
- **Circuit Breaker Dummy Testing**:
  ```java
  // Force a circuit breaker open in tests
  circuitBreaker.onBulkHeadersReceived(new BulkHeaders(10, 5)); // 50% error rate
  ```

---

## **4. Prevention Strategies**

### **Design-Time Mitigations**
1. **Adopt Resilience Patterns Early**:
   - Use **circuit breakers** (Hystrix, Resilience4j) for external calls.
   - Implement **retries with jitter** for transient failures.
   - Design **failover paths** (multi-AZ, multi-cloud).

2. **Automated Health Checks**:
   - **Liveness probes** (Kubernetes) to detect unresponsive nodes.
   - **Readiness probes** to gate traffic based on backend health.

3. **Observability First**:
   - Instrument all services with **metrics, logs, and traces** (OpenTelemetry).
   - Set up **SLOs/SLIs** to proactively detect degradation.

### **Runtime Mitigations**
1. **Auto-Scaling**:
   - Scale out during traffic spikes (Kubernetes HPA, AWS Auto Scaling).
   - Example:
     ```yaml
     # Kubernetes HPA (Horizontal Pod Autoscaler)
     apiVersion: autoscaling/v2
     kind: HorizontalPodAutoscaler
     metadata:
       name: app-hpa
     spec:
       scaleTargetRef:
         apiVersion: apps/v1
         kind: Deployment
         name: app
       minReplicas: 3
       maxReplicas: 10
       metrics:
       - type: Resource
         resource:
           name: cpu
           target:
             type: Utilization
             averageUtilization: 70
     ```

2. **Dependency Resilience**:
   - **Circuit breakers** for external APIs.
   - **Bulkheads** to isolate failure domains (e.g., separate thread pools per service).

3. **Data Consistency**:
   - Use **eventual consistency** for non-critical reads.
   - Implement **compensating transactions** for failed writes.

### **Post-Mortem & Improvement**
1. **Blame Nothing, Learn Everything**:
   - Document the **root cause** (not just symptoms).
   - Example template:
     ```
     Incident: [Description]
     Root Cause: [Technical Issue]
     Impact: [Duration, Users Affected]
     Fix: [Immediate + Long-term]
     Prevention: [New Monitoring/Policy]
     ```

2. **Chaos Testing in CI/CD**:
   - Integrate **chaos experiments** into pipeline stages.
   - Example (Chaos Mesh):
     ```yaml
     apiVersion: chaos-mesh.org/v1alpha1
     kind: PodChaos
     metadata:
       name: pod-failure
     spec:
       action: pod-failure
       mode: one
       selector:
         namespaces:
           - default
         labelSelectors:
           app: my-app
       duration: "10s"
     ```

3. **Game Days**:
   - Schedule **planned outages** (e.g., primary DC failure) to validate failover.

---
## **5. Summary Checklist for Quick Resolution**
| **Step**               | **Action**                                  | **Tools**                     |
|-------------------------|---------------------------------------------|-------------------------------|
| **1. Identify Symptom** | Check logs/metrics for errors, timeouts.     | Prometheus, ELK, Datadog      |
| **2. Isolate Failure** | Determine if it’s node-level, dependency, or app logic. | `jstack`, `curl -v`, `kubectl describe pod` |
| **3. Reproduce**        | Trigger the failure manually (e.g., kill node). | Chaos Mesh, `kubectl delete`  |
| **4. Apply Fix**        | Patch config, retry logic, or failover path. | Code changes, Helm/Kustomize   |
| **5. Validate**         | Test failover, retries, and circuit breaker. | Postman, k6, `kubectl rollout` |
| **6. Monitor**          | Set up alerts for recurrence.               | Grafana Alerts, PagerDuty     |

---
## **Final Notes**
- **Availability ≠ Uptime**: Focus on **recovery time (RTO)** and **failure volume (RPO)**.
- **Test Failures**: Assume everything will fail—**validate failover scenarios**.
- **Keep It Simple**: Over-engineering resilience can introduce new fragility.

By following this guide, you can systematically diagnose availability issues and implement targeted fixes. Always **measure impact** and **iterate** on your resilience patterns.