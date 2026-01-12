# **Debugging Availability Setup: A Troubleshooting Guide**

## **Introduction**
The **Availability Setup** pattern ensures that systems remain operational with minimal downtime by distributing workloads across multiple instances (e.g., failover clusters, load balancers, or microservices deployments). Common failures include node unavailability, misconfigured failover logic, or degraded performance under load.

This guide helps diagnose and resolve issues efficiently, focusing on **quick resolution** rather than exhaustive explanations.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms:

✅ **Primary Symptoms:**
- [ ] System crashes or becomes unresponsive during high traffic.
- [ ] Failover mechanisms fail to activate when a node goes down.
- [ ] High latency or degraded performance despite redundant nodes.
- [ ] Logs indicate failed health checks or connection timeouts.
- [ ] Users report intermittent errors (e.g., 5xx responses).

✅ **Secondary Symptoms (Indicators for Deeper Issues):**
- [ ] Load balancer logs show stuck or failed probes.
- [ ] Replication lag in distributed databases.
- [ ] API calls fail intermittently (check `curl`/`Postman` tests).
- [ ] Docker/Kubernetes pods crashloop or are in `Pending`/`CrashLoopBackOff` state.
- [ ] Monitoring alerts for high CPU/memory on a single node.

---
## **2. Common Issues & Fixes**

### **Issue 1: Failover Not Triggering (No Automatic Switchover)**
**Possible Causes:**
- Health checks misconfigured (wrong endpoints, timeout thresholds).
- Anti-affinity rules preventing pod scheduling.
- Node declared as `Unschedulable` or drained.

**Quick Fixes:**
#### **Check Health Check Configuration**
```yaml
# Example Kubernetes Liveness Probe
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```
- Verify `/healthz` endpoint returns `200`; adjust `timeoutSeconds` if needed.
- Test manually:
  ```bash
  curl -v http://<node-ip>:<port>/healthz
  ```

#### **Review Node Affinity/Anti-Affinity**
```yaml
# Example Anti-Affinity Rule (prevents all pods on same node)
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - my-app
      topologyKey: "kubernetes.io/hostname"
```
- If misconfigured, pods may not reschedule.
- Check node status:
  ```bash
  kubectl get nodes
  ```

#### **Check Node Status & Drain**
```bash
kubectl describe node <node-name>
```
- If the node is `NotReady`, drain it and check logs:
  ```bash
  kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
  kubectl logs <pod-name> -n <namespace>
  ```

---

### **Issue 2: Load Balancer Not Distributing Traffic Properly**
**Possible Causes:**
- Backend health checks failing (incorrect thresholds).
- Session affinity misconfigured (stickiness breaking failover).
- Load balancer (NGINX, ALB, Nginx Ingress) misconfigured.

**Quick Fixes:**
#### **Inspect Load Balancer Health Checks**
```nginx
# Example NGINX upstream health check
upstream backend {
    server backend1:8080 check interval=5s rise=2 fall=3 timeout=2s;
    server backend2:8080 backup;
}
```
- Adjust `interval`, `rise`, and `fall` values if checks are too aggressive.
- Test with:
  ```bash
  curl -I http://<load-balancer-ip>
  ```

#### **Disable Session Affinity (If Needed)**
```nginx
# Remove session sticky logic
http {
    upstream backend {
        server backend1:8080;
        server backend2:8080;
    }
    server {
        location / {
            proxy_pass http://backend;
            # Remove: proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            # Remove: proxy_ssl_session_reuse off;
        }
    }
}
```

#### **Check Kubernetes Ingress/Service Endpoints**
```bash
kubectl get endpoints <service-name>
```
- If endpoints list only one IP, check pod status:
  ```bash
  kubectl get pods -o wide
  ```

---

### **Issue 3: Database Replication Lag (Synchronous Failover Fails)**
**Possible Causes:**
- Replication lag due to high write load.
- Network partition between primary and secondary.
- Sync delay settings too aggressive.

**Quick Fixes:**
#### **Check Replication Status (PostgreSQL Example)**
```bash
pg_isready -h <replica> -U <user>
SELECT * FROM pg_stat_replication;
```
- If `replay_lag` is high, scale writes or reduce `synchronous_commit=remote_apply`.

#### **Adjust Sync Settings (MySQL Example)**
```sql
-- Temporarily reduce sync delay (MySQL)
SET GLOBAL sync_binlog=0;  -- Reduces delay but risks data loss
-- For production, use async replication
```
- For PostgreSQL:
  ```sql
  ALTER SYSTEM SET max_wal_sender_delay = '100ms';
  ```

---

### **Issue 4: Pods CrashLoopBackOff (Kubernetes)**
**Possible Causes:**
- Resource constraints (`OOMKilled`).
- Image pull errors.
- Liveness probes failing too often.

**Quick Fixes:**
#### **Check Pod Logs**
```bash
kubectl logs <pod-name> --previous -n <namespace>
```
- Look for `OutOfMemory`, `PermissionDenied`, or `ConnectionRefused`.

#### **Adjust Resource Limits**
```yaml
# Example resource limits
resources:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "1"
    memory: "1Gi"
```

#### **Increase Probe Retry Delay**
```yaml
livenessProbe:
  initialDelaySeconds: 30  # Wait longer before retrying
  failureThreshold: 3
```

---

## **3. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                                                 | **Example Command**                          |
|------------------------|----------------------------------------------------------------------------|---------------------------------------------|
| `kubectl describe`     | Inspect pods, nodes, services                                               | `kubectl describe pod <pod-name>`           |
| `curl`/`Postman`       | Test API endpoints                                                         | `curl -v http://<service>:8080/healthz`    |
| `tcpdump`/`Wireshark`  | Network-level debugging (ping, TCP handshakes)                              | `tcpdump -i eth0 port 8080`                |
| `Prometheus/Grafana`   | Check metrics (latency, error rates, memory)                                 | Query: `rate(http_requests_total[5m])`     |
| `journalctl` (Linux)   | Systemd service logs                                                         | `journalctl -u <service-name> -n 50`       |
| `kubectl exec`         | Shell into a pod for debugging                                              | `kubectl exec -it <pod-name> -- /bin/bash` |
| `kubectl port-forward` | Forward local port to pod services                                          | `kubectl port-forward svc/<service> 8080:80` |

---

## **4. Prevention Strategies**

### **A. Proactive Monitoring**
- **Set up alerts** for:
  - Node health (`kubectl describe node` failures).
  - Pod evictions (`Evicted` events).
  - High replication lag (`SELECT * FROM pg_stat_replication`).
- **Use Prometheus + Alertmanager** for real-time alerts:
  ```yaml
  # Example Alert (High Pod Latency)
  alert: HighLatency
    expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 1.0
    for: 5m
    labels:
      severity: warning
  ```

### **B. Configuration Best Practices**
- **Health checks:**
  - Use `/healthz` endpoints with **short timeouts** (1-2s).
  - Avoid CPU-heavy checks (e.g., database queries).
- **Load balancing:**
  - Prefer **round-robin** over sticky sessions unless required.
  - Test failover manually:
    ```bash
    kubectl delete pod <pod-name>  # Force failover
    ```
- **Database replication:**
  - Use **async replication** for high-write systems.
  - Monitor lag with `pg_stat_replication`/`SHOW SLAVE STATUS`.

### **C. Chaos Engineering**
- **Test failover** periodically:
  - Kill a pod (`kubectl delete pod <pod-name>`).
  - Simulate network partitions (`ip netns` or `iptables`).
- **Use tools like Chaos Mesh** for automated chaos testing.

### **D. Documentation & Runbooks**
- Maintain a **runbook** for common issues (e.g., "Pod CrashLoopBackOff").
- Document **failover steps** (e.g., manually promote a replica).

---

## **5. Final Checklist Before Production Rollout**
1. [ ] Health checks work in staging (`curl -v`).
2. [ ] Load balancer distributes traffic evenly (check `kubectl get endpoints`).
3. [ ] Failover test passes (kill a pod, verify traffic redirects).
4. [ ] Database replication lag < 5s (monitor `pg_stat_replication`).
5. [ ] Prometheus alerts configured for critical metrics.
6. [ ] Runbooks updated with troubleshooting steps.

---
## **Conclusion**
Availability issues are often **configuration or monitoring gaps** rather than code bugs. By following this guide, you can:
✔ **Quickly identify** if failover is misconfigured.
✔ **Test health checks** and load balancer behavior.
✔ **Prevent future outages** with proactive monitoring.

For deeper issues, refer to:
- [Kubernetes Debugging Guide](https://kubernetes.io/docs/tasks/debug/)
- [Prometheus Alerting Docs](https://prometheus.io/docs/alerting/latest/)
- [Database Replication Best Practices](https://www.percona.com/blog/)