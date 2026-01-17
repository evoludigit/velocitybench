# **Debugging Hybrid Maintenance: A Troubleshooting Guide**
*(For Microservices, Kubernetes, and Service Mesh Environments)*

---

## **1. Introduction**
The **Hybrid Maintenance** pattern allows systems to operate simultaneously in **online (live) and offline (maintenance) modes** while ensuring high availability, graceful degradation, and zero-downtime updates. Common use cases include:
- Kubernetes rolling updates with traffic splitting
- Service mesh-based Canary deployments
- Database schema migrations with read replicas
- Hybrid cloud workloads with regional failover

This guide focuses on debugging failures in hybrid maintenance setups, particularly in **microservices architectures** with Kubernetes, Istio, or similar tools.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms to narrow down issues:

| **Symptom**                          | **Root Cause Likelihood**                     | **Impact**                          |
|--------------------------------------|-----------------------------------------------|-------------------------------------|
| Traffic routed to outdated versions | Misconfigured traffic splitting rules        | Partial outages, inconsistent data |
| High error rates after rollout       | Incompatible service versions                 | Degraded performance                |
| Database connection failures         | Schema drift between online/offline modes     | App crashes or timeouts             |
| Timeouts in service mesh routing     | Sidecar misconfiguration or resource exhaustion | Latency spikes                      |
| Inconsistent logs between environments | Logging misalignment in online/offline modes  | Debugging complexity                |

---

## **3. Common Issues & Fixes**

### **Issue 1: Incorrect Traffic Splitting (Kubernetes/Service Mesh)**
**Symptom:**
- Users intermittently hit `v1.0` while `v2.0` is deployed.
- Logs show mixed responses from different versions.

**Root Cause:**
- **Kubernetes**: Service or Ingress misconfigured.
- **Istio/Linkerd**: `VirtualService` rules not updated or misapplied.

**Fix:**
#### **For Kubernetes:**
```yaml
# Example: Correct traffic splitting in Kubernetes (using labels)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hybrid-maintenance-ingress
spec:
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: app-service
            port:
              number: 80
---
# Ensure pods are labeled for version-based routing
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-service-v2
spec:
  selector:
    matchLabels:
      app: app-service
      version: v2
  template:
    metadata:
      labels:
        app: app-service
        version: v2  # <-- Critical for traffic splitting
```

#### **For Istio:**
```yaml
# Correct VirtualService for hybrid maintenance
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: app-service
spec:
  hosts:
  - example.com
  http:
  - route:
    - destination:
        host: app-service
        subset: v1  # Online mode (e.g., 90%)
    - destination:
        host: app-service
        subset: v2  # Offline mode (e.g., 10%)
      weight: 10
---
# Sidecar configuration
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: app-service
spec:
  host: app-service
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

**Debugging Steps:**
1. Verify pod labels:
   ```sh
   kubectl get pods -l app=app-service --show-labels
   ```
2. Check Istio traffic stats:
   ```sh
   istioctl analyse
   kubectl exec -it <istio-pod> -- curl http://localhost:15020/stats/prometheus
   ```

---

### **Issue 2: Database Schema Drift (Read Replicas/Offline Modes)**
**Symptom:**
- App crashes with `column not found` errors.
- Offline mode (read replicas) has stale data.

**Root Cause:**
- Schema migrations not synchronized.
- Transaction isolation issues in hybrid mode.

**Fix:**
#### **Option 1: Use Database-Specific Tools**
- **PostgreSQL:** `pg_backrest` or `TimescaleDB` for hybrid reads.
- **MySQL:** Read replicas with `GTID` consistency.

```sql
-- Example: Enable GTID replication for MySQL
CHANGE MASTER TO MASTER_USE_GTID = slave_pos;
```

#### **Option 2: Application-Level Fallback**
```python
# Python example: Query offline mode if online fails
from sqlalchemy import create_engine, event

def hybrid_maintenance_query(db_url_online, db_url_offline):
    online_engine = create_engine(db_url_online)
    offline_engine = create_engine(db_url_offline)

    @event.listens_for(online_engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
        try:
            cursor.execute("SELECT 1 FROM dual")  # Ping check
        except:
            print("Falling back to offline mode")
            return offline_engine.execute(statement, params)

    return online_engine.execute("SELECT * FROM users").fetchall()
```

**Debugging Steps:**
1. Verify replica lag:
   ```sh
   SHOW SLAVE STATUS\G  # MySQL
   SELECT pg_is_in_recovery();  # PostgreSQL
   ```
2. Check schema consistency:
   ```sh
   diff <(mysql -u root -e "SHOW CREATE TABLE users" db_online) <(mysql -u root -e "SHOW CREATE TABLE users" db_offline)
   ```

---

### **Issue 3: Sidecar Resource Exhaustion (Istio/Linkerd)**
**Symptom:**
- 5xx errors spike during traffic shifts.
- Sidecar pods show `OOMKilled` or high CPU.

**Root Cause:**
- Insufficient resource limits for sidecars.
- Misconfigured `envoy` proxy settings.

**Fix:**
```yaml
# Update sidecar resource limits in Istio
apiVersion: networking.istio.io/v1alpha3
kind: Sidecar
metadata:
  name: default
spec:
  resources:
    limits:
      cpu: 500m
      memory: 1Gi
    requests:
      cpu: 100m
      memory: 512Mi
```

**Debugging Steps:**
1. Check sidecar metrics:
   ```sh
   kubectl top pods --containers=istio-proxy
   ```
2. Review `envoy` logs:
   ```sh
   kubectl logs <pod> -c istio-proxy | grep -i "oom\|error"
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                  | **Command/Example**                     |
|------------------------|----------------------------------------------|------------------------------------------|
| **kubectl**            | Pod/Service inspection                       | `kubectl describe pod <pod>`             |
| **Istioctl**           | Service mesh diagnostics                     | `istioctl analyze`                       |
| **Prometheus + Grafana** | Metrics for traffic shifts                  | `kubectl port-forward svc/prometheus 9090` |
| **Journalctl**         | Sidecar logs (if running outside K8s)       | `journalctl -u istio-sidecar`            |
| **Database Exporters** | Schema drift detection                      | `pg_exporter` (PostgreSQL)               |
| **Chaos Mesh**         | Simulate hybrid mode failures                | `chaos mesh inject pod --graceful --pod <pod>` |

**Advanced Technique: Distributed Tracing**
- Use **Jaeger** or **OpenTelemetry** to track requests across online/offline modes.
- Example:
  ```sh
  jaeger query --service app-service --duration 5m
  ```

---

## **5. Prevention Strategies**

### **1. Automated Canary Analysis**
- Use **Flagger** (Istio + Prometheus) for automated rollback:
  ```yaml
  apiVersion: flagger.app/v1beta1
  kind: Canary
  metadata:
    name: app-service
  spec:
    provider: istio
    targetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: app-service
    analysis:
      interval: 1m
      threshold: 5
      maxWeight: 50
      stepWeight: 10
      metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
      - name: request-duration
        thresholdRange:
          max: 500
  ```

### **2. Schema Migration Safeguards**
- **Pre-Migration Check:**
  ```sh
  # Ensure replicas are in sync before promoting
  psql -h <replica> -c "SELECT COUNT(*) FROM users;" | awk '{print $1}' > online_count.txt
  psql -h <offline> -c "SELECT COUNT(*) FROM users;" | awk '{print $1}' > offline_count.txt
  diff online_count.txt offline_count.txt
  ```
- **Use `pg_partman` (PostgreSQL) or `gh-ost` (MySQL)** for zero-downtime migrations.

### **3. Resource Quotas for Sidecars**
- Enforce limits in `ResourceQuota`:
  ```yaml
  apiVersion: v1
  kind: ResourceQuota
  metadata:
    name: istio-resources
  spec:
    hard:
      requests.cpu: "10"
      requests.memory: 10Gi
      limits.cpu: "20"
      limits.memory: 20Gi
  ```

### **4. Hybrid Mode Health Checks**
- Implement **active-active validation**:
  ```python
  import requests

  def validate_hybrid_mode(online_url, offline_url):
      online_resp = requests.get(online_url, timeout=2)
      offline_resp = requests.get(offline_url, timeout=2)
      if online_resp.status_code != offline_resp.status_code:
          raise RuntimeError("Inconsistent responses!")
  ```

---

## **6. Summary of Key Takeaways**
| **Problem Area**       | **Quick Fix**                                  | **Prevention**                          |
|------------------------|-----------------------------------------------|-----------------------------------------|
| Traffic routing        | Verify `VirtualService`/`Ingress` rules        | Use Flagger for automated canaries     |
| Database drift         | Compare schemas; use GTID/pg_backrest         | Automate sync checks before promotion   |
| Sidecar issues         | Adjust resource limits                       | Enforce `ResourceQuota`                |
| Logging inconsistencies| Align log levels between modes                | Centralized logging (Loki, ELK)        |

---

## **7. Final Checklist for Hybrid Maintenance Stability**
1. [ ] Traffic splitting rules match deployment versions.
2. [ ] Database replicas are synchronized (check lag).
3. [ ] Sidecars have sufficient CPU/memory limits.
4. [ ] Schema migrations are validated pre-promotion.
5. [ ] Monitoring covers both online/offline modes.
6. [ ] Rollback strategy is automated (e.g., Flagger).

---
**Pro Tip:** Start with **10% traffic to the new version** and monitor errors before scaling up. Use **Chaos Engineering** (e.g., Gremlin) to test failure scenarios in hybrid mode.