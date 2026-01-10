---
# **Debugging Health Checks & Liveness Probes: A Troubleshooting Guide**

## **Introduction**
Health checks and liveness probes are critical for Kubernetes and cloud-native systems to ensure resilient traffic routing, auto-recovery, and graceful deployments. When misconfigured or failing, they can cause traffic blackholing, stuck deployments, or cascading failures.

This guide focuses on **quick debugging** of common issues, with actionable steps, code snippets, and prevention tips.

---

## **1. Symptom Checklist**
Before diving into logs, ask these questions:

✅ **Is traffic being routed to dead pods?**
   - Check if load balancers (Ingress/NLB) or service meshes (Istio/Linkerd) are routing to unhealthy instances.
   - Verify if `kubectl get pods` shows pods in `Running` but `livenessProbe` failures.

✅ **Are new deployments stuck?**
   - Are pods stuck in `ContainerCreating` due to liveness probe failures?
   - Is `kubectl rollout status` hanging because probes delay readiness?

✅ **Is the system misbehaving after restarts?**
   - Do restart loops occur (`kubectl get events`)?
   - Are cold starts failing due to slow probes?

✅ **Are external services (DBs, APIs) timing out?**
   - Is your probe timing out before the app can recover?

---

## **2. Common Issues & Fixes**

### **Issue 1: Liveness Probe Fails Too Early (False Positives)**
**Symptom:**
- Pods restart unnecessarily even when the app is functional.
- Logs show `Liveness probe failed: HTTP probe failed with status code: 408`.

**Root Cause:**
- Probe `initialDelaySeconds` too low.
- Probe `periodSeconds` too fast.
- Slow application startup (e.g., database connection delays).

**Fix:**
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30  # Wait for app to fully initialize
  periodSeconds: 10         # Check every 10s (adjust based on app stability)
  timeoutSeconds: 5         # Max 5s to respond
  failureThreshold: 3       # Retry 3 times before restarting
```

**Debugging Steps:**
1. **Test probe manually:** `curl http://<pod-ip>:<port>/healthz` (should return `200`).
2. **Check logs:** `kubectl logs <pod> --previous` (if it crashed).
3. **Adjust thresholds:** Start with `initialDelaySeconds = 30` if app takes >10s to start.

---

### **Issue 2: Dead Pods Not Restarted (False Negatives)**
**Symptom:**
- Pods hang in `Running` but unresponsive.
- `kubectl describe pod` shows no probe failures.

**Root Cause:**
- Probe path (`/healthz`) returns `200` but app is deadlocked.
- HTTP probe doesn’t cover all failure modes (e.g., memory leaks).

**Fix:**
```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 5  # More retries before killing
  successThreshold: 1   # No need to retry on success
```
**Alternative:** Use a **TCP socket probe** if HTTP is unreliable:
```yaml
livenessProbe:
  tcpSocket:
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 20
```

**Debugging Steps:**
1. **Inspect pod manually:** `kubectl exec -it <pod> -- bash` (if possible).
2. **Check process status:** `ps aux | grep <your-app>` (is it stuck?).
3. **Test probe manually:** `curl` or `nc -zv <pod-ip> <port>`.

---

### **Issue 3: Slow Startup → Deployment Failures**
**Symptom:**
- New deployments stuck (`kubectl rollout status` hangs).
- Pods stuck in `ContainerCreating` due to probe delays.

**Root Cause:**
- Liveness probe delays readiness checks.
- Init containers fail silently.

**Fix:**
1. **Use `readinessProbe` separately** (not liveness):
   ```yaml
   readinessProbe:
     httpGet:
       path: /ready
       port: 8080
     initialDelaySeconds: 10
     periodSeconds: 5
   ```
2. **Increase `readinessGate` delay** (if using StatefulSets):
   ```yaml
   readinessProbes:
   - exec:
       command: ["test", "-f", "/tmp/ready"]
   ```
3. **Use `initContainers` for pre-startup checks** (e.g., DB health):
   ```yaml
   initContainers:
     - name: db-check
       image: curlimages/curl
       command: ['sh', '-c', 'until curl -s http://db:5432; do echo waiting; sleep 2; done;']
   ```

**Debugging Steps:**
1. **Check pod events:** `kubectl describe pod <pod> | grep -i "liveness"`.
2. **Test readiness manually:** `kubectl get pod <pod> -o yaml | grep readiness`.
3. **Adjust `terminationGracePeriodSeconds`** if cleanup is slow:
   ```yaml
   terminationGracePeriodSeconds: 30
   ```

---

### **Issue 4: External Dependencies (DBs, APIs) Fail Probes**
**Symptom:**
- Probes fail due to slow external calls (e.g., DB timeouts).
- `Liveness probe failed: HTTP probe failed with status code: 504`.

**Root Cause:**
- Probe timeout too low for external calls.
- External service unreachable (`ConnectionRefused`).

**Fix:**
1. **Increase probe timeout** (if app is slow to recover):
   ```yaml
   livenessProbe:
     httpGet:
       path: /healthz
       port: 8080
     timeoutSeconds: 10  # Up from default 1s
   ```
2. **Use a **health check endpoint that bypasses slow paths**:
   ```python
   # Flask (Python) example
   from flask import Flask
   app = Flask(__name__)

   @app.route('/healthz')
   def health_check():
       return "OK", 200  # Fast check

   @app.route('/ready')
   def readiness_check():
       if db_is_ready():  # Slow check
           return "OK", 200
       return "NotReady", 503
   ```
3. **Add retries in your probe logic** (if external service is flaky):
   ```yaml
   livenessProbe:
     httpGet:
       path: /healthz
       port: 8080
     initialDelaySeconds: 30
     periodSeconds: 30  # Check every 30s
   ```

**Debugging Steps:**
1. **Test externally:** `curl http://<external-service>` (is it reachable?).
2. **Check probe logs:** `kubectl logs <pod> | grep -i "probe"`.
3. **Monitor latency:** Use Prometheus metrics to track slow endpoints.

---

## **3. Debugging Tools & Techniques**

### **A. Log Analysis**
- **Key logs to check:**
  ```bash
  kubectl logs <pod> --tail=50 -c <container>
  kubectl describe pod <pod> | grep "Liveness"
  ```
- **Filter for probe failures:**
  ```bash
  kubectl get events --sort-by=.metadata.creationTimestamp | grep "Liveness"
  ```

### **B. Manual Probe Testing**
- **Test HTTP probes:**
  ```bash
  curl -v http://<pod-ip>:<port>/healthz
  ```
- **Test TCP probes:**
  ```bash
  nc -zv <pod-ip> <port>
  ```
- **Test exec probes:**
  ```bash
  kubectl exec <pod> -- <health-check-command>
  ```

### **C. Monitoring & Observability**
- **Prometheus + Grafana:** Track probe success/failure rates.
- **Kubernetes Events API:** Monitor probe-related events.
- **Slow Logs:** Use `strace` or `pprof` to debug slow startup.

### **D. Debugging with `kubectl`**
| Command | Purpose |
|---------|---------|
| `kubectl get pods -o wide` | Check pod IPs |
| `kubectl exec -it <pod> -- sh` | Debug inside container |
| `kubectl port-forward <pod> <local-port>:8080` | Test locally |
| `kubectl describe pod <pod> > pod-debug.txt` | Full pod status |

---

## **4. Prevention Strategies**

### **✅ Best Practices**
1. **Use separate `liveness` and `readiness` probes.**
   - Liveness: "Am I alive?" (quick check)
   - Readiness: "Am I ready for traffic?" (slower check)

2. **Configure realistic thresholds:**
   - `initialDelaySeconds`: ≥ app startup time.
   - `timeoutSeconds`: ≥ slowest expected response.

3. **Avoid blocking probes:**
   - Don’t make probes wait for DBs (unless critical).
   - Use fast endpoints (`/healthz`) and slower ones (`/ready`) separately.

4. **Test probes in staging:**
   - Simulate failures (`kill -9` a pod) and verify recovery.

5. **Use `livenessProbe` with `restartPolicy: Always`.**
   - Ensures unhealthy pods are killed and replaced.

6. **Monitor probe failures:**
   - Alert on `LivenessProbeFailed` events.

### **❌ Anti-Patterns**
| ❌ Bad Practice | ✅ Better Approach |
|----------------|------------------|
| Single `/healthz` for both liveness & readiness | Separate endpoints |
| Probe timeout = 1s for slow apps | Increase to ≥5s |
| No `initialDelaySeconds` | Always set ≥10s |
| Blocking probe (waits for DB) | Fast check + separate readiness |

---

## **5. Final Checklist for Quick Resolution**
| Step | Action |
|------|--------|
| 1 | Check if pods are `Running` but unresponsive (`kubectl get pods`) |
| 2 | Test probe manually (`curl` or `nc`) |
| 3 | Adjust `initialDelaySeconds`, `periodSeconds`, `timeoutSeconds` |
| 4 | Separate liveness & readiness probes if needed |
| 5 | Check pod logs (`kubectl logs --previous`) |
| 6 | Verify external dependencies (DBs, APIs) |
| 7 | Increase `terminationGracePeriodSeconds` if cleanup is slow |
| 8 | Set up monitoring for probe failures |

---
## **Conclusion**
Health checks and liveness probes are **not one-size-fits-all**. Start with **minimal delays** (`initialDelaySeconds=30`), **realistic timeouts**, and **separate liveness/readiness checks**. Always **test probes manually** and **monitor failures**.

For persistent issues, **debug pod behavior** (`kubectl exec`), **check logs**, and **adjust thresholds incrementally**.

Would you like a deeper dive into any specific section (e.g., custom probe exec checks)?