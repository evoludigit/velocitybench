# **Debugging Health Check Endpoints: A Troubleshooting Guide**
*(Kubernetes `/health/live` and `/health/ready` Probes)*

---

## **1. Symptom Checklist**
Before diving into fixes, quickly verify whether your health check endpoints are causing issues. Check if any of the following symptoms apply:

| **Symptom** | **Expected Behavior** | **Possible Root Cause** |
|-------------|----------------------|-------------------------|
| **Kubernetes frequently restarts healthy pods** | Pods remain stable; restarts only happen on failures | Misconfigured `livenessProbe` (too aggressive) or race condition |
| **Traffic routed to pods failing readiness checks** | Traffic only hits pods when `readinessProbe` passes | Incorrect `initialDelaySeconds` or missing `/health/ready` |
| **Application deadlocks or hangs** | Container responds quickly to `/health/live` | Blocking operation in liveness check (e.g., DB call) |
| **No visibility into dependency health** | `/health/ready` should reflect downstream service health | Hardcoded `false` or missing checks for external services |
| **Pods stuck in `CrashLoopBackOff`** | Logs show exit status 137 (OOM) or crash | Liveness probe kills container before it initializes |
| **Slow probing responses** | `/health/live` should return **< 1s**, `/health/ready` **< 5s** | Expensive checks (e.g., redundant DB queries) |
| **Unpredictable readiness check failures** | `readinessProbe` should be consistent | Race condition with DB initialization or async tasks |

If multiple symptoms apply, focus on **`livenessProbe` first** (crash recovery) and then **`readinessProbe`** (traffic distribution).

---

## **2. Common Issues and Fixes**
### **Issue 1: Liveness Probe Kills Healthy Pods**
**Symptom:** Kubernetes restarts pods even when they’re functioning correctly.
**Root Cause:**
- The `/health/live` endpoint takes too long (>30s timeout) or performs unnecessary work.
- The probe fails intermittently due to race conditions (e.g., database connection flapping).

**Fix:**
```yaml
# Example: Optimized liveness probe
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 5       # Wait for app to start
  periodSeconds: 10            # Check every 10s (default: 10)
  timeoutSeconds: 2            # Fail fast if endpoint hangs
  failureThreshold: 3          # Retry 3 times before restart
```
**Best Practices:**
- **Avoid DB calls** in `/health/live`. Use a simple HTTP check (`200 OK`).
- **Test locally** with `curl -w "\n%{http_code}" http://localhost:8080/health/live`.
- **Monitor probe failures** in Kubernetes events:
  ```sh
  kubectl describe pod <pod-name> | grep -i "liveness"
  ```

---

### **Issue 2: Readiness Probe Blocks Traffic to Unhealthy Pods**
**Symptom:** Traffic hits pods even though `/health/ready` returns `503`.
**Root Cause:**
- `initialDelaySeconds` is too low (pod not ready yet).
- Missing checks for critical dependencies (e.g., Redis, Kafka).

**Fix:**
```yaml
# Example: Readiness probe with dependency checks
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 15       # Wait for DB to initialize
  periodSeconds: 5              # Check every 5s
  timeoutSeconds: 1             # Fail fast
  failureThreshold: 1           # Mark as ready on first success
```
**Implement `/health/ready` Logic (Node.js Example):**
```javascript
// server.js
app.get('/health/ready', async (req, res) => {
  try {
    const dbConnected = await db.ping(); // Critical dependency
    const redisReady = await redis.check(); // Another dependency
    res.status(200).json({ status: "ready", db: dbConnected, redis: redisReady });
  } catch (err) {
    res.status(503).json({ status: "not_ready", error: err.message });
  }
});
```
**Debugging:**
- **Test locally** with:
  ```sh
  curl http://localhost:8080/health/ready
  ```
- **Check logs** for readiness failures:
  ```sh
  kubectl logs <pod-name> | grep "readiness"
  ```

---

### **Issue 3: Slow Probe Responses Cause Timeouts**
**Symptom:** `/health/live` takes **> 1s**, causing probe timeouts.
**Root Cause:**
- Heavy logic in the endpoint (e.g., serialization, expensive queries).
- Missing HTTP caching (`Cache-Control: no-store` header).

**Fix:**
```javascript
// Fast `/health/live` endpoint (Node.js)
app.get('/health/live', (req, res) => {
  res.status(200).json({ status: "alive" }); // No DB calls!
});
```
**Add Headers for Caching:**
```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
    httpHeaders:
    - name: Cache-Control
      value: "no-store"  # Prevents stale responses
```
**Debugging:**
- Use **`time curl`** to measure response time:
  ```sh
  time curl -o /dev/null -s -w "%{time_total}s\n" http://localhost:8080/health/live
  ```
- **Profile slow endpoints** with:
  ```sh
  kubectl exec <pod> -- node --inspect=0.0.0.0:9229 server.js  # (Node.js)
  ```

---

### **Issue 4: Race Condition with Database Initialization**
**Symptom:** `/health/ready` fails intermittently due to DB connection flapping.
**Root Cause:**
- DB connection retry logic is too aggressive.
- Probe checks before DB is fully ready.

**Fix (PostgreSQL Example):**
```javascript
async function checkDbReady() {
  let attempts = 0;
  const maxAttempts = 10;
  while (attempts < maxAttempts) {
    try {
      await db.connect(); // Wait for DB to accept connections
      return true;
    } catch (err) {
      attempts++;
      if (attempts === maxAttempts) throw err;
      await new Promise(res => setTimeout(res, 1000)); // Exponential backoff?
    }
  }
}
```
**Kubernetes Probe Adjustments:**
```yaml
readinessProbe:
  exec:
    command: ["sh", "-c", "until nc -z db 5432; do echo waiting for DB; sleep 2; done;"]
  initialDelaySeconds: 20
  periodSeconds: 5
```
**Debugging:**
- **Check DB logs** for connection issues:
  ```sh
  kubectl logs -l app=db
  ```
- **Use `nc` (netcat) for local testing**:
  ```sh
  nc -zv db 5432
  ```

---

## **3. Debugging Tools and Techniques**
### **A. Kubernetes-Specific Tools**
| **Tool** | **Use Case** | **Command** |
|----------|-------------|-------------|
| `kubectl get events` | Check probe failures | `kubectl get events --sort-by=.metadata.creationTimestamp` |
| `kubectl describe pod` | Inspect probe logs | `kubectl describe pod <pod> \| grep -i "probe"` |
| `kubectl exec` | Test endpoints manually | `kubectl exec <pod> -- curl localhost:8080/health/live` |
| `kubectl port-forward` | Test locally | `kubectl port-forward pod/<pod> 8080:8080` |

### **B. Logging and Monitoring**
- **Prometheus + Grafana:**
  - Expose metrics for probe success/failure rates.
  - Example endpoint:
    ```go
    http.HandleFunc("/metrics", func(w http.ResponseWriter, r *http.Request) {
      w.Write([]byte(`# HELP probe_success_total Successful probe calls\n` +
                     `# TYPE probe_success_total counter\n` +
                     `probe_success_total 1\n`))
    })
    ```
- **Structured Logging:**
  Add probe-specific logs:
  ```javascript
  app.get('/health/live', (req, res) => {
    console.log({ event: "liveness_probe_passed", timestamp: new Date() });
    res.status(200).send();
  });
  ```

### **C. Local Testing**
- **Mock the Probe:**
  Start a local server and test:
  ```sh
  curl -v http://localhost:8080/health/live
  ```
- **Simulate Kubernetes Probes:**
  Use `kubectl proxy` to test:
  ```sh
  kubectl proxy --port=8081 &
  curl http://localhost:8081/api/v1/namespaces/<ns>/pods/<pod>/proxy/health/live
  ```

---

## **4. Prevention Strategies**
### **A. Design Guidelines**
1. **Separate Concerns:**
   - `/health/live` → **Container health** (no DB calls).
   - `/health/ready` → **Application readiness** (checks dependencies).
2. **Avoid Common Pitfalls:**
   - ❌ **Don’t** block on slow operations (e.g., DB queries).
   - ✅ **Do** use lightweight checks (e.g., HTTP pings).
3. **Optimize Probe Intervals:**
   - **Liveness:** Check every **10–30s** (default: 10s).
   - **Readiness:** Check every **5–15s** (faster recovery).

### **B. Testing Checklist Before Deployment**
| **Check** | **Action** |
|-----------|------------|
| **Liveness Probe** | Ensure `< 1s` response, no DB calls. |
| **Readiness Probe** | Verify dependency checks (DB, Redis, etc.). |
| **Edge Cases** | Test under load (`k6`, `locust`). |
| **Kubernetes Events** | No `CrashLoopBackOff` or `ContainerFailed`. |
| **Traffic Distribution** | Verify `kubectl get pods -o wide` shows traffic only to `Ready` pods. |

### **C. Automated Validation**
Add a **pre-commit hook** to test probes:
```yaml
# .github/workflows/health-check.yml
- name: Test health endpoints
  run: |
    curl -f http://localhost:8080/health/live || exit 1
    curl -f http://localhost:8080/health/ready || exit 1
```
Or use **Conftest** for Kubernetes YAML validation:
```sh
conftest test --policy file://policies/probe-policy.json k8s-manifests/deployment.yaml
```

---

## **5. Summary of Key Fixes**
| **Problem** | **Quick Fix** | **Long-Term Solution** |
|-------------|--------------|-----------------------|
| Pods restart too often | Reduce `failureThreshold`, optimize `/health/live`. | Use **exponential backoff** in liveness logic. |
| Traffic hits unhealthy pods | Increase `initialDelaySeconds`, add dependency checks. | **Isolate** readiness checks from liveness. |
| Slow probe responses | Simplify endpoint, add `timeoutSeconds`. | **Cache** responses where possible. |
| Race condition with DB | Add retry logic in `/health/ready`. | **Wait for DB ready** before marking as ready. |

---

## **6. Final Checklist Before Fixing**
1. **Is the issue affecting `liveness` or `readiness`?**
   - Restarts? → **Liveness**.
   - Traffic issues? → **Readiness**.
2. **Test locally first** (`curl`, `kubectl port-forward`).
3. **Check logs** for probe failures (`kubectl logs`).
4. **Monitor metrics** (Prometheus/Grafana).
5. **Iterate** with small changes (e.g., adjust `initialDelaySeconds`).

---
**Debugging health checks should be quick—focus on the simplest fix first (e.g., `initialDelaySeconds`).** If problems persist, **log probe responses** and **test locally** before scaling up.