# **Debugging Failover Systems: A Troubleshooting Guide**
*(For Backend Engineers)*

Failover mechanisms are critical for high-availability (HA) systems. When they fail, downstream services degrade or crash, leading to downtime. This guide provides a structured approach to diagnosing failover failures efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms to confirm a failover issue:

### **Primary Indicators of Failover Failure**
| Symptom | Description | Likely Cause |
|---------|------------|-------------|
| **Primary node unresponsive** | API calls, database queries, or core services fail to respond. | Crash, OOM, misconfiguration |
| **Backup node not taking over** | Traffic remains on the failed primary; no health check callbacks. | Misconfigured health checks, unhealthty state, network issues |
| **Circus or load balancer stuck** | Reverse proxy (Nginx, HAProxy) or service mesh (Istio, Linkerd) not rerouting. | Config mismatch, DNS propagation delay |
| **Database replication lag** | Primary DB fails, but replica hasn’t caught up. | Slow replication, network latency |
| **Timeout errors in logs** | `Connection refused`, `ETIMEDOUT`, or `ECONNRESET` from downstream services. | Network partition, timeouts, misconfigured retries |
| **Logs show no failover trigger** | No entries in `healthcheck`, `failover` logs, or Kubernetes events. | Broken monitoring, disabled failover hooks |

**Quick Check:**
```bash
# Check primary health (e.g., Kubernetes liveness probes)
kubectl get pods -l app=primary -o wide | grep -i "Running"

# Check backup node readiness
kubectl get pods -l app=backup -o wide | grep -i "Ready"

# Check database replication lag (PostgreSQL example)
pg_isready -U user -d dbname
SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn();
```

---

## **2. Common Issues and Fixes**
### **A. Failover Trigger Not Firing**
**Symptom:** Primary fails, but backup doesn’t take over automatically.

#### **Root Causes & Fixes**
| Issue | Debugging Steps | Code/Config Fixes |
|-------|----------------|-------------------|
| **Health check misconfigured** | Probe returns `200` even when unhealthy. | Adjust liveness probe thresholds: |
| | ```yaml
  livenessProbe:
    httpGet:
      path: /health
      port: 8080
    initialDelaySeconds: 30
    failureThreshold: 5
    timeoutSeconds: 2
    periodSeconds: 10
    successThreshold: 1
  ``` | |
| **Backup node not ready** | `kubectl describe pod <backup>` shows pending status. | Ensure resources (CPU, memory) are allocated: |
| | ```bash
  kubectl describe pod <backup> | grep -i "0/1 node"
  ``` | ```yaml
  resources:
    requests:
      cpu: "0.5"
      memory: "512Mi"
    limits:
      cpu: "1"
      memory: "1Gi"
  ``` | |
| **DNS/Service mesh misrouting** | Primary node still gets traffic. | Verify service discovery: |
| | ```bash
  kubectl get svc primary -o yaml | grep -i "selectors"
  ``` | ```yaml
  # Ensure selector matches only healthy pods
  selectors:
    app: primary
    environment: production
  ``` | |

---

### **B. Database Replication Failures**
**Symptom:** Primary DB crashes, but replica hasn’t promoted.

#### **Root Causes & Fixes**
| Issue | Debugging Steps | Code/Config Fixes |
|-------|----------------|-------------------|
| **Replica lag too high** | `pg_last_wal_receive_lsn()` lags behind `pg_last_xact_replay_lsn()`. | Increase replication slots: |
| | ```sql
  SELECT * FROM pg_stat_replication;
  ``` | ```bash
  # PostgreSQL: Increase replication slots
  SELECT * FROM pg_replication_slots;
  ALTER SYSTEM SET max_replication_slots = 10;
  ``` | |
| **Primary WAL not flushed** | Replica fails to sync due to unclean shutdown. | Enable `synchronous_commit=off` (temporarily) for recovery: |
| | ```bash
  psql -c "SHOW synchronous_commit;"
  ``` | ```conf
  # postgresql.conf
  synchronous_commit = off
  ``` | |
| **Network partition** | `pg_isready` fails on replica. | Check `pg_hba.conf` and firewall rules: |
| | ```bash
  tcpdump -i lo0 port 5432  # Check for dropped packets
  ``` | ```conf
  # Allow replication traffic
  host replication all 0.0.0.0/0 md5
  ``` | |

---

### **C. Load Balancer/Proxy Failover Hang**
**Symptom:** Nginx/HAProxy doesn’t reroute traffic after health check failure.

#### **Root Causes & Fixes**
| Issue | Debugging Steps | Code/Config Fixes |
|-------|----------------|-------------------|
| **Health check interval too long** | Probe runs every 30s, but failover takes longer. | Shorten health check interval: |
| | ```bash
  # Nginx: Check health check interval
  nginx -T | grep -i "health_check"
  ``` | ```nginx
  upstream primary {
    server backend1:8080 health_check interval=5s;
  }
  ``` | |
| **Sticky sessions enabled** | Client sessions stuck on dead primary. | Disable sticky sessions: |
| | ```bash
  # Kubernetes: Check service annotations
  kubectl get svc primary -o yaml | grep -i "sessionAffinity"
  ``` | ```yaml
  sessionAffinity: None
  ``` | |
| **Backend timeout too short** | HAProxy drops connections before failover. | Increase timeout: |
| | ```bash
  # HAProxy: Check timeouts
  echo "show stats" | socat /var/run/haproxy.sock STDIN
  ``` | ```haproxy
  timeout client 30s
  timeout server 30s
  ``` | |

---

## **3. Debugging Tools and Techniques**
### **A. Logging & Metrics**
| Tool | Purpose | Example Query |
|------|---------|--------------|
| **Prometheus + Grafana** | Track health checks, latency, errors. | `rate(http_requests_total{status=~"5.."}[1m])` |
| **ELK Stack** | Aggregate logs for failover events. | `log "health check failed" AND status:5xx` |
| **Kubernetes Events** | Check pod/container failures. | `kubectl get events --sort-by=.metadata.creationTimestamp` |
| **Database Logs** | Inspect replication errors. | `grep "replication" /var/log/postgresql/postgresql*.log` |

**Example Prometheus Alert Rule:**
```yaml
- alert: FailoverNotTriggered
  expr: up{job="primary"} == 0 and up{job="backup"} == 1
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Primary node down, no failover detected"
```

---

### **B. Network Diagnostics**
| Command | Purpose |
|---------|---------|
| `tcpdump -i any -n host <primary_ip>` | Capture network traffic between nodes. |
| `mtr <backup_ip>` | Trace route and latency to backup. |
| `ss -tulnp` | Check open ports on primary/backup. |
| `dig @<dns-server> primary.svc.cluster.local` | Verify DNS resolution. |

---

### **C. Failover Simulation**
Test failover without downtime:
```bash
# Kill primary gracefully (Kubernetes)
kubectl delete pod primary-<pod-name> --grace-period=30 --force

# PostgreSQL: Force failover (manual)
pg_ctl promote -D /var/lib/postgresql/14/main
```

---

## **4. Prevention Strategies**
### **A. Design-Time Mitigations**
1. **Redundant failover controllers** (e.g., Kubernetes `ControllerManager` HA).
2. **Circus-style failover** (use [circus](https://github.com/facebookarchive/circus) for process management).
3. **Automated rollback** (if failover causes more issues, revert to primary).

### **B. Runtime Checks**
| Check | Tool/Method |
|-------|------------|
| **Health check thresholds** | Adjust `failureThreshold` in Kubernetes probes. |
| **Replication health** | Monitor `pg_stat_replication` or `SHOW replication slots`. |
| **Network partitions** | Use `etcd` or `consul` for distributed coordination. |
| **Timeout tuning** | Test with chaotic monkey tools (e.g., [Chaos Mesh](https://chaos-mesh.org/)).

### **C. Post-Failover Validation**
```bash
# Verify backup is now primary
kubectl get pods -l app=primary,role=backup | grep "Running"

# Check traffic shift (e.g., via Prometheus)
kubectl port-forward svc/primary 8080:8080
curl -I localhost:8080/health
```

---

## **5. Summary Checklist for Quick Resolution**
1. **Confirm primary is dead** (`kubectl get pods`, `pg_isready`).
2. **Check backup health** (`kubectl describe pod`, `SELECT pg_is_in_recovery()`).
3. **Inspect logs** (`journalctl`, `kubectl logs`, DB logs).
4. **Verify failover trigger** (health checks, DNS, load balancer).
5. **Restore traffic** (manually if needed; use `kubectl patch` or `pg_ctl promote`).
6. **Prevent recurrence** (tune thresholds, add alerts).

---
**Final Note:** Failover issues often stem from **configuration drift** or **misaligned timeouts**. Start with logs, then verify infrastructure (network, DB, orchestration). Use **automated recovery scripts** (e.g., Terraform, Ansible) to avoid manual errors.

Would you like a deeper dive into any specific area (e.g., Kubernetes HA, PostgreSQL streaming replication)?