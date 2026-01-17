# **Debugging Failover & Failback Patterns: A Troubleshooting Guide**

## **Introduction**
Failover and failback are critical mechanisms ensuring high availability in distributed systems. When a primary service fails, a backup (replica, standby, or secondary node) seamlessly takes over. After the primary recovers, traffic should gracefully migrate back. However, misconfigurations, race conditions, or network issues can disrupt this process, leading to downtime, data inconsistency, or split-brain scenarios.

This guide helps you diagnose and resolve common failover/failback issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

### **Primary Failover Issues**
| Symptom | Likely Cause |
|---------|-------------|
| ✅ Manual promotion takes **30+ minutes** | Long replica lag, manual intervention required |
| ✅ **All traffic lost** after load balancer failure | LB health checks misconfigured, no failover trigger |
| ✅ **Unnecessary failovers** during minor issues | Aggressive health checks, no grace period |
| ✅ **Traffic stuck on backup** after primary recovers | Failback disabled, stuck session LB mode |
| ✅ **Split-brain** (both primaries acting active) | Incorrect quorum, no consensus protocol (e.g., Raft, Paxos) |

### **Post-Failover Issues**
| Symptom | Likely Cause |
|---------|-------------|
| ✅ **Replica lag** (high replication delay) | Slow network, disk I/O bottleneck |
| ✅ **Data inconsistency** after failback | Unresolved conflicts, partial writes |
| ✅ **Connection leaks** (orphaned DB sessions) | Session affinity not cleared post-failover |
| ✅ **LB stuck in maintenance mode** | Misconfigured health check thresholds |
| ✅ **Slow failback** (hours to recover) | Manual intervention needed, no automated check |

---

## **2. Common Issues & Fixes**

### **Issue 1: Manual Failover Takes Too Long (30+ Minutes)**
**Root Cause:**
- Replica lag due to slow replication, network latency, or disk I/O.
- No automated health checks trigger failover early.

**Fixes:**
#### **A. Reduce Replica Lag**
- **For Databases (Postgres, MySQL, MongoDB):**
  ```sql
  -- Check replication lag (PostgreSQL)
  SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), pg_last_wal_receive_lsn());
  ```
  - **Fix:** Increase replica WAL archiving (`wal_level = replica`) or use **logical replication** for lower overhead.
  - **Example (PostgreSQL):**
    ```sql
    ALTER SYSTEM SET max_wal_senders = 5; -- Increase parallel replication slots
    ```

- **For Kafka:**
  ```bash
  kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>
  ```
  - **Fix:** Scale brokers or optimize `unclean.leader.election.enable=false`.

#### **B. Automate Failover with Health Checks**
- **For Kubernetes (Kube-DNS, CoreDNS):**
  ```yaml
  # ConfigMap for CoreDNS health checks
  health:
    kubernetes cluster.local in-addr.arpa ip6.arpa {
      fallthrough
      hosts {
        fallthrough
        prometheus :5302
        forward . /etc/resolv.conf
      }
    }
  ```
  - **Fix:** Add `kubernetes` plugin with `healthCheckPeriod` tuning.

---

### **Issue 2: Load Balancer (LB) Fails → All Traffic Lost**
**Root Cause:**
- LB health checks too strict or misconfigured.
- No failover node in LB backend.

**Fixes:**
#### **A. Configure Proper Health Checks**
- **AWS ALB/NLB Example:**
  ```json
  {
    "HealthCheck": {
      "HealthyThreshold": 2,
      "UnhealthyThreshold": 3,
      "Interval": 30,  // Check every 30s (default)
      "Timeout": 5     // Fail after 5s if no response
    }
  }
  ```
  - **Fix:** Adjust thresholds based on expected recovery time.

- **NGINX Example:**
  ```nginx
  upstream backend {
    server 192.168.1.1:8080 max_fails=3 fail_timeout=30s;
    server 192.168.1.2:8080 backup;
  }
  ```

#### **B. Ensure Failover Node is Always in LB**
- **Kubernetes (Service) Example:**
  ```yaml
  spec:
    loadBalancer:
      sourceRanges: ["10.0.0.0/8"]  # Allow only trusted IPs
    selector:
      app: myapp  # Must match Pod labels
    sessionAffinity: ClientIP  # Prevent session leaks
  ```

---

### **Issue 3: Unnecessary Failovers (Too Eager)**
**Root Cause:**
- Health checks too aggressive (e.g., timeout too low).
- No grace period before triggering failover.

**Fixes:**
#### **A. Add Grace Period**
- **PostgreSQL Example (pg_autofailover):**
  ```ini
  # config.conf
  [failover]
  grace_period = 60  # Wait 60s before failing over
  ```
- **Kubernetes Liveness Probe:**
  ```yaml
  livenessProbe:
    httpGet:
      path: /healthz
      port: 8080
    initialDelaySeconds: 30  # Avoid early failures
    periodSeconds: 10
    failureThreshold: 5
  ```

---

### **Issue 4: Traffic Stuck on Backup After Primary Recovers**
**Root Cause:**
- **Session affinity** not cleared.
- **Failback disabled** in the LB/DB cluster.

**Fixes:**
#### **A. Disable Session Affinity (If Applicable)**
- **NGINX Example:**
  ```nginx
  stream {
    upstream backend {
      server backend1;
      server backend2;
    }
    server {
      listen 5000;
      proxy_pass backend;
      proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
      # No session sticky!
    }
  }
  ```

#### **B. Force Failback in Databases**
- **PostgreSQL (pgAutoFailover):**
  ```bash
  failover --master <primary-node> --promote <backup-node>
  ```
- **Kubernetes (Manual Pod Deletion):**
  ```bash
  kubectl delete pod -l app=myapp --grace-period=0 --force
  ```

---

### **Issue 5: Split-Brain (Both Primaries Active)**
**Root Cause:**
- No consensus protocol (e.g., Raft, Paxos).
- Misconfigured quorum (e.g., 2 out of 3 nodes).
- Network partition allows conflicting writes.

**Fixes:**
#### **A. Enforce Quorum (Raft/Paxos)**
- **Example (Election Timeout Tuning):**
  ```yaml
  # Etcd Config
  election-timeout: "10000"  # 10s (default)
  heartbeat-interval: "2000" # Must be < election-timeout
  ```

- **PostgreSQL Patroni:**
  ```yaml
  scope: mycluster
  restore_command: pg_basebackup -h %h -p %p -D %t -U replica -C -v6 -S %s --wal-method=stream
  postgresql:
    listen: "0.0.0.0:5432"
    data_dir: /var/lib/postgresql/data
    bin_dir: /usr/lib/postgresql/13/bin
    pgpass: /tmp/pgpass
    parameters:
      max_connections: 100
    synchronous_standby_names: "*"  # Force synchronous replication
  ```

#### **B. Use Network Partition Detection**
- **Kubernetes NetworkPolicy Example:**
  ```yaml
  apiVersion: networking.k8s.io/v1
  kind: NetworkPolicy
  metadata:
    name: split-brain-prevent
  spec:
    podSelector: {}
    policyTypes:
    - Ingress
    ingress:
    - from:
      - podSelector:
          matchLabels:
            role: db-master
      ports:
      - protocol: TCP
        port: 5432  # PostgreSQL
  ```

---

## **3. Debugging Tools & Techniques**

### **A. Database-Specific Tools**
| Database | Tool | Command |
|----------|------|---------|
| PostgreSQL | `pg_ctl switch` | `sudo -u postgres pg_ctl switch -D /var/lib/postgresql/data` |
| MySQL | `mysqlfailover` (MHA) | `mysqlfailover --apply-conf /etc/mysqlfailover.conf` |
| MongoDB | `rs.status()` | `mongosh --eval "rs.status()" admin` |
| Kafka | `kafka-leader-election` | `bin/kafka-leader-election.sh --bootstrap-server localhost:9092 --election-type preferred --group my-group` |

### **B. LB & Network Debugging**
| Tool | Command |
|------|---------|
| **ngrep** (Packet Capture) | `ngrep -d any -W byline tcp port 80` |
| **tcpdump** | `tcpdump -i eth0 port 5432` |
| **kubectl describe** (K8s) | `kubectl describe pod my-pod -n db` |
| **AWS CloudWatch** | Check ALB health check failures |

### **C. Log Analysis**
- **PostgreSQL Logs:**
  ```bash
  grep "failed to connect" /var/log/postgresql/postgresql-13-main.log
  ```
- **Kubernetes Events:**
  ```bash
  kubectl get events --sort-by=.metadata.creationTimestamp
  ```

---

## **4. Prevention Strategies**
### **A. Automate Failover Testing**
- **Chaos Engineering (Chaos Mesh):**
  ```yaml
  apiVersion: chaos-mesh.org/v1alpha1
  kind: PodChaos
  metadata:
    name: db-pod-failure
  spec:
    action: pod-failure
    mode: one
    selector:
      namespaces:
        - default
      labelSelectors:
        app: my-db
    duration: "5m"
  ```

### **B. Configure Proper Timeouts**
| Component | Recommended Timeout |
|-----------|---------------------|
| LB Health Check | 5-10s (adjust based on RTO) |
| Database Replication Lag | < 1s (for strong consistency) |
| Failover Election | 2-3x heartbeat interval |

### **C. Use Blue-Green or Canary Deployments**
- **Example (K8s Rollout):**
  ```bash
  kubectl rollout status deployment/myapp --watch
  ```

### **D. Monitor Replication Lag**
- **Prometheus Alert (PostgreSQL):**
  ```yaml
  - alert: HighReplicationLag
    expr: pg_replication_lag_seconds > 5
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "PostgreSQL replication lagging (>5s)"
  ```

### **E. Document Failover Procedures**
- **Example Checklist:**
  1. Verify replication health (`pg_isready`).
  2. Check LB health (`kubectl get endpoints`).
  3. Test failover (`pg_ctl promote`).
  4. Validate failback (`kubectl rollout restart`).

---

## **Conclusion**
Failover and failback are complex but manageable with the right tools and configurations. **Always test failover scenarios in staging before production.** Use health checks, monitoring, and automated failback to minimize downtime.

### **Quick Checklist for Troubleshooting:**
✅ **Is replication lag acceptable?** (Check `pg_stat_replication`, Kafka lag)
✅ **Are health checks too aggressive?** (Adjust thresholds)
✅ **Is session affinity breaking failback?** (Disable if not needed)
✅ **Is the quorum correct?** (For Raft/Paxos clusters)
✅ **Are logs showing split-brain?** (Check `etcdctl endpoint health`)

By following this guide, you can quickly identify and resolve failover issues while preventing future outages.