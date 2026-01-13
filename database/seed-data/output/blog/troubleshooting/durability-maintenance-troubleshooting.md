# **Debugging Durability Maintenance: A Troubleshooting Guide**

## **Introduction**
The **Durability Maintenance** pattern ensures data persistence, fault tolerance, and recovery in distributed systems. It guarantees that critical operations (e.g., transactions, checks, or state updates) remain intact even in the event of failures (node crashes, network partitions, or crashes). This guide provides a structured approach to diagnosing and resolving common issues related to Durability Maintenance.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms to confirm if Durability Maintenance is the root cause:

| **Symptom** | **Description** | **How to Detect** |
|-------------|----------------|------------------|
| **Data Loss on Node Crash** | Critical writes are not reflected after a node restart. | Compare DB state before and after a crash. |
| **Inconsistent Replication** | Some nodes lag behind or have stale data. | Check replication lag metrics (e.g., `pg_last_xact_replay_time` in PostgreSQL). |
| **Failed Transaction Retry Loops** | Transactions repeatedly fail due to lock conflicts or timeouts. | Review log files for repeated retry patterns. |
| **Slow Recovery Time** | System takes unusually long to recover from failures. | Measure recovery time (e.g., `pg_postmaster_start_time` vs. actual recovery completion). |
| **Network Partition-Induced Failures** | Split-brain scenarios occur where multiple nodes believe they are leaders. | Check consensus logs (e.g., ZooKeeper, Raft logs). |
| **Unreliable Checksum/Fingerprints** | Data integrity checks fail post-failure. | Run checksum validation scripts. |

**Next Steps:**
- If **any symptom matches**, proceed to **Common Issues & Fixes**.
- If **no symptoms match**, consider other failure modes (e.g., networking, storage).

---

## **2. Common Issues & Fixes**

### **Issue 1: Data Loss After Node Crash (Logical Durability Failure)**
**Symptom:**
- A write operation (e.g., `INSERT/UPDATE`) appears successful but is lost after a crash.

**Root Cause:**
- **In-flight writes not synced to disk** before crash (e.g., `sync=False` in PostgreSQL, `fsync` bypassed).
- **Replication lag** where followers haven’t applied changes before a primary fails.

**Debugging Steps:**
1. **Check Write-Ahead Logs (WAL)**
   ```bash
   psql -c "SHOW wal_level;"  # Should be "replica" or "logical" for durability
   ```
   - If `wal_level=minimal`, enable it:
     ```sql
     ALTER SYSTEM SET wal_level = replica;
     ```
2. **Verify `fsync` Behavior**
   ```bash
   psql -c "SHOW synchronous_commit;"  # Should be "on"
   ```
   - If `off`, enforce durability:
     ```sql
     ALTER SYSTEM SET synchronous_commit = on;
     ```
3. **Check Replication Status**
   ```bash
   psql -c "SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();"
   ```
   - If `pg_last_wal_replay_lsn()` lags behind, force a sync:
     ```bash
     pg_ctl promote  # For PostgreSQL standby
     ```

**Fix (PostgreSQL Example):**
```sql
-- Ensure durability settings are strict
ALTER SYSTEM SET fsync = on;
ALTER SYSTEM SET synchronous_commit = on;
ALTER SYSTEM SET wal_sync_method = fdatasync;  # Faster but riskier (use with caution)
```

---

### **Issue 2: Inconsistent Replication (Asynchronous Lag)**
**Symptom:**
- Primary node commits a transaction, but followers haven’t applied it yet when queried.

**Root Cause:**
- **Asynchronous replication** where followers lag behind.
- **Network bottlenecks** or high write load.

**Debugging Steps:**
1. **Check Replication Lag**
   ```bash
   SELECT
     pg_stat_replication.usage,
     pg_stat_replication.send_lsn,
     pg_stat_replication.replay_lsn,
     (pg_stat_replication.replay_lsn - pg_stat_replication.send_lsn) AS lag_bytes
   FROM pg_stat_replication;
   ```
2. **Enable Hot Standby (if not already)**
   ```sql
   ALTER SYSTEM SET hot_standby = on;
   ```
3. **Tune Replication Timeout**
   ```bash
   psql -c "SHOW max_replication_lag;"  # Default: 30s
   ```
   - Adjust if lag persists:
     ```sql
     ALTER SYSTEM SET max_replication_lag = '10min';
     ```

**Fix (Kubernetes Example with Mirroring):**
```yaml
# Deploy a StatefulSet with strong consistency
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-ha
spec:
  replicas: 3
  selector:
    matchLabels:
      app: postgres-ha
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:14
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        env:
        - name: POSTGRES_SYNC
          value: "on"  # Force synchronous replication
---
# PersistentVolume for durability
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: "ssd"  # Use SSD for lower latency
```

---

### **Issue 3: Failed Transaction Retry Loops (Lock/Timeout)**
**Symptom:**
- Application retries transactions indefinitely due to `lock_timeout` or `statement_timeout`.

**Root Cause:**
- **Long-running transactions** holding locks.
- **Network partitions** delaying lock resolution.

**Debugging Steps:**
1. **Find Blocking Transactions**
   ```sql
   SELECT
     pid,
     now() - query_start AS duration,
     query
   FROM pg_stat_activity
   WHERE state = 'active' AND query NOT LIKE '%pg_stat%';
   ```
2. **Kill Stuck Sessions**
   ```sql
   SELECT pg_terminate_backend(pid);
   ```
3. **Adjust Timeout Settings**
   ```sql
   -- Increase lock timeout (default: 10s)
   SET lock_timeout = '60s';

   -- Increase statement timeout (default: 0 = unlimited)
   SET statement_timeout = '300s';
   ```

**Fix (Application-Level Retry Logic):**
```python
# Example: Exponential backoff for retries
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def execute_transaction(tx):
    try:
        tx.execute("INSERT INTO users (name) VALUES ('test')")
        tx.commit()
    except Exception as e:
        if "lock" in str(e).lower():
            raise  # Re-raise to trigger retry
        else:
            raise
```

---

### **Issue 4: Split-Brain Scenario (Multi-Leader Inconsistency)**
**Symptom:**
- Two nodes believe they are leaders, causing divergent writes.

**Root Cause:**
- **No quorum enforcement** in consensus protocols (e.g., Raft/ZooKeeper).
- **Network partitions** without automatic failover.

**Debugging Steps:**
1. **Check Consensus Logs**
   ```bash
   # For ZooKeeper (if applicable)
   tail -f /var/log/zookeeper/data/log.*.log
   ```
2. **Verify Leader Election**
   ```bash
   # For Raft (e.g., etcd)
   ETCDCTL_API=3 etcdctl endpoint health
   ```
3. **Enforce Quorum**
   - Ensure `raft.follower_count` ≥ `(total_nodes / 2) + 1`.

**Fix (Kubernetes Example with Operator):**
```yaml
# Deploy HAProxy for leader election control
apiVersion: apps/v1
kind: Deployment
metadata:
  name: haproxy-leader
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: haproxy
        image: haproxy:2.4
        ports:
        - containerPort: 80
        volumeMounts:
        - name: config
          mountPath: /usr/local/etc/haproxy
---
# Configure sticky sessions for consistency
apiVersion: v1
kind: Service
metadata:
  name: postgres-leader
spec:
  selector:
    app: postgres-ha
  clusterIP: None  # Headless service for DNS-based discovery
  sessionAffinity: ClientIP
```

---

## **3. Debugging Tools & Techniques**

| **Tool** | **Use Case** | **Example Command** |
|----------|-------------|---------------------|
| **`pgbadger`** | PostgreSQL log analysis | `pgbadger -f postgres.log -o report.html` |
| **`strace`** | Track filesystem sync operations | `strace -e trace=file -f postgres` |
| **`kubectl`** | Kubernetes pod/log inspection | `kubectl logs -l app=postgres-ha` |
| **`etcdctl`** | Raft consensus inspection | `etcdctl endpoint status --write-out=table` |
| **`journalctl`** | Systemd service logs | `journalctl -u postgres.service -f` |
| **`ping`/`mtr`** | Network latency checks | `mtr postgres-primary` |

**Advanced Techniques:**
- **WAL Segmentation Analysis** (PostgreSQL):
  ```bash
  find /var/lib/postgresql/data -name "pg_wal" -type f -exec ls -lh {} \;
  ```
- **Replication Lag Alerting** (Prometheus + Grafana):
  ```yaml
  # Alert for replication lag > 10s
  - alert: ReplicationLagHigh
    expr: pg_stat_replication_replay_lsn_offset > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "PostgreSQL replication lagging"
  ```

---

## **4. Prevention Strategies**

### **Configuration Hardening**
| **Setting** | **Recommended Value** | **Purpose** |
|-------------|----------------------|-------------|
| `fsync` | `on` | Ensures writes to disk before ack |
| `synchronous_commit` | `on` | Waits for durability confirmation |
| `wal_level` | `replica` | Enables logical replication |
| `max_wal_size` | `1GB` | Prevents WAL bloat |
| `archive_mode` | `on` | Enables point-in-time recovery (PITR) |

### **Automated Recovery Testing**
1. **Chaos Engineering (Gremlin/Kubernetes Chaos Mesh)**
   - Simulate node failures:
     ```bash
     kubectl delete pod <postgres-pod> --grace-period=0 --force
     ```
   - Verify recovery time (RTO) and data integrity.

2. **Regular Failover Drills**
   - Manually promote a standby:
     ```bash
     pg_ctl promote -D /var/lib/postgresql/data
     ```

### **Monitoring & Alerting**
- **Metrics to Track:**
  - `pg_stat_replication.replay_lsn` lag
  - `pg_stat_activity.wait_event_type` (blocked queries)
  - `disk_io_time` (high latency)
- **Alert Rules:**
  - Replication lag > 30s → **Critical**
  - Disk sync time > 1s → **Warning**

### **Infrastructure Best Practices**
- **Use SSD** for WAL storage (lower latency).
- **Isolate Replication Traffic** (dedicated network for followers).
- **Enable Compression** for WAL replication:
  ```sql
  ALTER SYSTEM SET wal_compression = on;
  ```

---

## **Conclusion**
Durability Maintenance failures typically stem from **misconfigured write-ahead logs, replication lag, or split-brain scenarios**. By following this guide:
1. **Check symptoms** systematically.
2. **Fix root causes** (e.g., `fsync`, quorum enforcement).
3. **Prevent recurrences** with testing and monitoring.

**Final Checklist Before Production:**
✅ All writes are `fsync`-protected.
✅ Replication lag < 10s (adjust `max_replication_lag`).
✅ Leader election quorum enforced.
✅ Backup retention policy tested (e.g., `pg_basebackup`).

If issues persist, **review database logs (`pg_log`)** and **consensus logs (ZooKeeper/Raft)** for timestamps.

---
**Next Steps:**
- [ ] Test recovery from a crash.
- [ ] Simulate network partitions in staging.
- [ ] Schedule a durability audit with `pg_stat_replication`.