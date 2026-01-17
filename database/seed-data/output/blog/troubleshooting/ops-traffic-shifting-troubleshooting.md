# **Debugging Traffic Shifting Patterns: A Troubleshooting Guide**
*For backend engineers handling gradual rollouts, canary releases, A/B testing, or blue-green deployments.*

Traffic shifting patterns allow controlled distribution of traffic across different versions of services, ensuring minimal risk during deployments. However, misconfigurations or race conditions can lead to degraded performance, data inconsistencies, or partial failures.

This guide provides a **practical, step-by-step** approach to diagnosing and resolving issues.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm whether the issue aligns with traffic shifting problems. Check for:

✅ **Partial Outages**
- Some users hit `Service Unavailable` (503) while others work fine.
- Error logs show `Connection refused` or `DNS lookup failed`.

✅ **Inconsistent Behavior**
- Random failures from the same backend endpoint.
- Read vs. write operations behave differently (e.g., reads return stale data).

✅ **Traffic Leakage or Overload**
- Unexpected spikes in a new version’s load (e.g., 80% traffic routed to v2 when v1 should handle 70%).
- Requests bypassing intended routing rules (e.g., canary users getting full production traffic).

✅ **Race Condition Errors**
- Timeouts due to slow rollback mechanisms.
- `NetworkUnavailable` errors when shifting traffic from one backend to another.

✅ **Monitoring Alerts**
- Latency spikes in shifted traffic.
- Increased retry attempts (e.g., from service mesh retries).
- **Metrics anomalies** (e.g., `requests_in_progress` spikes during shifts).

---

## **2. Common Issues & Fixes**
### **Issue 1: Incorrect Traffic Distribution (Weight Mismatch)**
**Symptom:** Users experience inconsistent errors as traffic isn’t evenly distributed.

**Root Cause:**
- Misconfigured weights in an **Ingress Controller** (Nginx, AWS ALB), **Service Mesh** (Istio, Linkerd), or **Load Balancer** (HAProxy, Envoy).
- Hardcoded weights override dynamic routing.

**Debugging Steps:**
1. **Check Current Weights**
   ```sh
   # Istio example (verify service weights)
   kubectl get virtualservices -A | grep my-service
   ```
   ```yaml
   # Example: 70% v1, 30% v2
   trafficPolicy:
     loadBalancer:
       simple: 70
   ```
   - If weights don’t match your intent, update the `VirtualService`/`TrafficSplit`.

2. **Verify Backend Health**
   ```sh
   # Check backend pods/servers
   kubectl get pods -l app=my-service
   ```
   - Ensure all instances are running and healthy (`kubectl describe pod`).

3. **Test Traffic Routing Manually**
   ```sh
   # Use cURL with a headers-based rule (if applicable)
   curl -H "X-User-Type: canary" http://my-service
   ```
   - If canary users hit v1 instead of v2, check **header-based routing** in your service mesh.

**Fix:**
```yaml
# Correct Istio VirtualService (70/30 split)
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  hosts:
  - my-service
  http:
  - route:
    - destination:
        host: my-service-v1
        subset: v1
      weight: 70
    - destination:
        host: my-service-v2
        subset: v2
      weight: 30
```

---

### **Issue 2: Traffic Leakage (Users Bypassing Rules)**
**Symptom:** Some users end up on unintended versions despite weight settings.

**Root Cause:**
- **Sticky Sessions** override dynamic routing (e.g., AWS ALB `sticky_sessions`).
- **DNS-based routing** (e.g., split DNS) misconfigured.
- **Client-side caching** serving stale responses.

**Debugging Steps:**
1. **Disable Sticky Sessions**
   ```yaml
   # AWS ALB (remove sticky_sessions)
   type: application
   backend:
     service:
       name: my-service
       port: 80
   attributes:
     sticky_session_cookie: none
   ```

2. **Check DNS Records**
   ```sh
   # Verify DNS A/AAAA records point to the correct load balancer
   dig my-service
   ```
   - If multiple IPs exist, traffic may split unpredictably.

3. **Inspect Client Requests**
   ```sh
   # Use Wireshark/tcpdump to check Host header
   tcpdump -i any port 80 -A | grep "Host"
   ```
   - Ensure clients are sending the correct `Host` header.

**Fix:**
- **For Service Mesh:** Use **destination rules** to enforce versioned subnets.
  ```yaml
  apiVersion: networking.istio.io/v1alpha3
  kind: DestinationRule
  metadata:
    name: my-service
  spec:
    host: my-service
    trafficPolicy:
      loadBalancer:
        simple: LEAST_CONN  # Avoid sticky sessions
  ```

---

### **Issue 3: Slow Rollbacks (Timeouts During Shift)**
**Symptom:** Traffic shift fails with `Request Timeout` or `Connection Reset`.

**Root Cause:**
- **Gradual rollback too slow** (e.g., shifting from v2 → v1 at 1% per minute).
- **Backend congestion** (v1 overwhelmed by sudden traffic).
- **Service Mesh retries** not properly configured.

**Debugging Steps:**
1. **Check Rollback Rate**
   ```sh
   # Istio example: Check shift speed
   kubectl get virtualservices -w
   ```
   - If shifts take >5 min, increase rate (e.g., `5% per second`).

2. **Monitor Backend Load**
   ```sh
   # Prometheus query for CPU/memory under pressure
   prometheus query "container_cpu_usage_seconds_total"
   ```
   - If v1 is maxed out, **scale horizontally** before shifting.

3. **Adjust Retries in Service Mesh**
   ```yaml
   # Istio: Reduce retries during shifts
   trafficPolicy:
     outlierDetection:
       consecutive5xxErrors: 1
       interval: 5s
       baseEjectionTime: 30s
   ```

**Fix:**
```yaml
# Faster rollback (e.g., 20% per second)
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: my-service
spec:
  http:
  - route:
    - destination:
        host: my-service-v1
        subset: v1
      weight: 80  # Shift from 30%→80% in 3 steps (~25% per shift)
```

---

### **Issue 4: Data Inconsistency (Read/Write Mismatch)**
**Symptom:** Reads return old data after writes go to a new version.

**Root Cause:**
- **Async writes** not propagated to all versions.
- **Database connection pooling** reusing stale connections.
- **Caching layers** (Redis, CDN) not invalidated.

**Debugging Steps:**
1. **Check Database Replication Lag**
   ```sh
   # PostgreSQL example: Check replication status
   psql -c "SELECT * FROM pg_stat_replication;"
   ```
   - If lag >1s, **increase replication workers**.

2. **Verify Connection Pool Behavior**
   ```sh
   # Check DB client (e.g., PgBouncer) connections
   psql -c "SHOW pool_status;"
   ```
   - If pools are reused, **invalidate connections on version shifts**.

3. **Test with New Requests**
   ```sh
   # Force a new DB connection
   curl -H "X-New-Connection: true" http://my-write-service
   ```

**Fix:**
- **Database:** Enable **q-sync** or **logical replication**.
- **App Code:** Force new DB sessions on version shifts:
  ```go
  // Example: Close stale DB connections
  db, _ := sql.Open("postgres", "new-connection-string")
  defer db.Close()
  ```

---

## **3. Debugging Tools & Techniques**
| **Tool**          | **Use Case**                                                                 | **Example Command**                          |
|--------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **kubectl get events** | Check Kubernetes pod/rollout events.                                      | `kubectl get events -A --sort-by=.metadata.creationTimestamp` |
| **Prometheus/Grafana** | Monitor latency, error rates, and traffic shifts.                          | `rate(http_requests_total{status=5xx}[1m])` |
| **Istio Telemetry** | Trace requests across service versions.                                   | `kubectl port-forward svc/istio-ingressgateway 8080:80` |
| **Wireshark**      | Inspect network headers (Host, X-User-Type) for routing leaks.            | `tcpdump -i eth0 port 80 -w traffic.pcap` |
| **cURL + Headers** | Test routing rules manually.                                               | `curl -H "X-Target-Version: v2" http://service` |
| **Chaos Mesh**     | Simulate failures during traffic shifts.                                   | `chaosmesh inject pod my-service --kill --duration 10s` |
| **Jeager/Zipkin**  | Trace requests across services to find bottlenecks.                        | `kubectl port-forward svc/tracing 9411:9411` |

**Advanced Debugging:**
- **Service Mesh Debugging:**
  ```sh
  # Enable Istio-sidecar logging
  kubectl edit cm istio-sidecar -n istio-system
  # Add: "env": [{ "name": "ISTIO_META_LOG_LEVEL", "value": "debug" }]
  ```
- **DNS Debugging:**
  ```sh
  # Verify DNS resolution
  nslookup my-service
  ```

---

## **4. Prevention Strategies**
### **Pre-Deployment Checks**
1. **Test Traffic Shifts in Staging**
   - Use **canary testing** in a non-production environment first.
   - Example:
     ```yaml
     # Istio canary test (5% traffic)
     - destination:
         host: my-service-v2
         subset: v2
       weight: 5
     ```

2. **Automate Rollback Triggers**
   - **Prometheus Alerts** for `error_rate > 1%` or `latency > 500ms`.
   - Example Alert:
     ```yaml
     - alert: HighErrorRate
       expr: rate(http_requests_total{status=5xx}[5m]) > 0.01
       for: 1m
       labels:
         severity: critical
       annotations:
         summary: "High error rate in {{ $labels.service }}"
     ```

3. **Use Feature Flags Over Traffic Shifts**
   - **LaunchDarkly/Unleash** for safer gradual rollouts.
   - Example:
     ```python
     # Python example (using feature flags)
     from featureflags import FeatureFlag

     if FeatureFlag("new-ui").is_enabled(user):
         # Route to v2
     else:
         # Route to v1
     ```

### **Operational Best Practices**
- **Monitor Traffic Shifts in Real-Time**
  - Use **Istio Kiali** or **Grafana dashboards** to visualize shifts.
  - Example Kiali query:
    ```sh
    kubectl port-forward svc/kiali 20001:20001
    ```

- **Document Shift Procedures**
  - Define **SLOs** (e.g., "99.9% availability during shifts").
  - Example:
    ```
    PROCEDURE: TrafficShift
    1. Shift at 5% per minute.
    2. Monitor error rates via Prometheus.
    3. Roll back if error rate > 0.5%.
    ```

- **Limit Shift Duration**
  - **Never shift >20% in a single step** unless tested.
  - Use **exponential backoff** for retries.

- **Prepare Rollback Plan**
  - **Automated rollback scripts** (e.g., Terraform + Istio).
    ```sh
    # Auto-rollback if error spike detected
    if prometheus_query "error_rate > 0.01"; then
      kubectl apply -f traffic-shift-rollback.yml
    fi
    ```

---

## **5. Summary Checklist for Quick Resolution**
| **Step** | **Action** |
|----------|-----------|
| 1 | **Confirm symptoms** (check logs, metrics, errors). |
| 2 | **Verify traffic weights** (`kubectl get virtualservices`). |
| 3 | **Test manually** (`curl` with headers). |
| 4 | **Check backend health** (`kubectl describe pod`). |
| 5 | **Adjust shift rate** (e.g., `weight: 5` → `weight: 10`). |
| 6 | **Monitor rollback** (Prometheus/Grafana). |
| 7 | **Fix caching/DNS issues** if traffic leaks persist. |
| 8 | **Document lessons learned** for future shifts. |

---

### **Final Notes**
- **Traffic shifting is safer with automation** (e.g., **Argo Rollouts** for GitOps-based shifts).
- **Always test in staging** before production.
- **Use circuit breakers** (Istio `outlierDetection`) to protect backends.

By following this guide, you should be able to **diagnose and resolve traffic shifting issues in <30 minutes** in most cases. For complex failures, **simulate in staging** before applying fixes in production.