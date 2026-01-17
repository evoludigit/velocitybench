# **Debugging Failover Guidelines: A Troubleshooting Guide**
*Quick and Practical Resolution for Failover-Related Issues*

---

## **Overview**
Failover is a critical component of high-availability systems, ensuring seamless transitions between primary and secondary components when failures occur. This guide focuses on **debugging failover-related issues** in distributed systems, databases, and microservices architectures. We’ll cover common failure modes, debugging techniques, and preventive measures.

---

## **1. Symptom Checklist**
Identify the root cause of failover failures using this checklist:

| **Symptom**                          | **Possible Cause**                          | **Impact**                          |
|--------------------------------------|--------------------------------------------|-------------------------------------|
| Failover triggers but application hangs | Stuck in sync/await state (e.g., DB replication lag) | Downtime, degraded performance |
| Failover triggers but service degrades | Incorrect health checks or degraded secondary | Partial service outage |
| Failover fails silently (no logs)     | Missing failover hooks or misconfigured alerts | Undetected failure |
| Failover works but rolls back immediately | Primary crashes before secondary stabilizes | Repeated failover loops |
| High latency after failover          | Network issues between nodes, slow sync      | Poor user experience                |
| Failover succeeds but data inconsistency | Replication lag or unapplied transactions  | Data corruption risk                |

**Action:** Start by verifying **logs and metrics** before diving into deeper diagnostics.

---

## **2. Common Issues and Fixes**

### **2.1 Failover Triggered but Application Hangs**
**Symptom:** The system switches to backup, but the application remains unresponsive.

**Root Cause:**
- **Blocking operations** (e.g., long-running transactions, stuck `SELECT` queries).
- **Resource starvation** (CPU/memory throttle during failover).
- **Network partitioning** (split-brain scenario).

**Debugging Steps:**
1. **Check database replication lag:**
   ```sql
   -- PostgreSQL: Check replication status
   SELECT pid, application_name, client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn FROM pg_stat_replication;

   -- MySQL: Check replication delay
   SHOW SLAVE STATUS\G;
   ```
   - If `replay_lsn` lags behind `write_lsn`, wait or force sync.

2. **Inspect application logs for blocking queries:**
   ```bash
   # Find long-running queries (PostgreSQL)
   SELECT pid, now() - query_start AS duration, query
   FROM pg_stat_activity
   WHERE state = 'active' AND now() - query_start > interval '30s'
   ORDER BY duration DESC;
   ```

3. **Fix:**
   - **Terminate blocking queries** (PostgreSQL):
     ```sql
     SELECT pg_terminate_backend(pid);
     ```
   - **Optimize queries** (add indexes, parallelize).
   - **Use connection pooling** to avoid resource exhaustion.

---

### **2.2 Failover Triggers but Service Degrades**
**Symptom:** The system switches to secondary, but performance drops.

**Root Causes:**
- **Secondary node underpowered** (CPU/memory constrained).
- **Health checks misconfigured** (failing to detect degraded secondary).
- **Network latency** between primary and secondary.

**Debugging Steps:**
1. **Verify secondary health:**
   ```bash
   # Check CPU/memory usage on secondary
   top -o %CPU
   free -h

   # Compare with primary
   ```
   - If secondary is throttled, scale up or balance load.

2. **Inspect health check scripts:**
   ```bash
   # Example: Health check for a microservice
   curl -I http://<secondary-node>:8080/health
   ```
   - If checks are too lenient, tighten thresholds.

3. **Fix:**
   - **Enable load balancing** (e.g., NGINX, HAProxy) between primaries/secondaries.
   - **Use tiered storage** ( SSD for secondary if latency is an issue).

---

### **2.3 Failover Fails Silently (No Logs)**
**Root Causes:**
- **Missing failover hooks** (e.g., no `POSTGRES_PORT` listener).
- **Permission issues** (e.g., user lacks `SUPERUSER` for replication).
- **Firewall blocking inter-node traffic**.

**Debugging Steps:**
1. **Check failover logs:**
   ```bash
   # Example: Patroni logs (PostgreSQL)
   journalctl -u patroni -f

   # Example: Kubernetes pod logs
   kubectl logs -l app=your-service
   ```
   - Look for `Failed to promote` or `Connection refused` errors.

2. **Test manual failover:**
   ```bash
   # For PostgreSQL with Patroni
   patronictl -c /etc/patroni.yaml demote <primary>
   patronictl -c /etc/patroni.yaml promote <secondary>
   ```
   - If this works, the issue is in **auto-failover config**.

3. **Fix:**
   - **Enable verbose logging** in failover scripts.
   - **Test network connectivity** (`telnet <primary> 5432`).
   - **Grant replication permissions**:
     ```sql
     CREATE USER replicator REPLICATION LOGIN PASSWORD 'securepassword';
     GRANT REPLICA ALL ON DATABASE * TO replicator;
     ```

---

### **2.4 Failover Rolls Back Immediately**
**Symptom:** Secondary takes over but primary crashes before stabilizing.

**Root Causes:**
- **Primary crashes too fast** (e.g., OOM killer kills PostgreSQL).
- **Secondary unable to sync** (replication lag).
- **Manual intervention required** (e.g., `pg_ctl promote` fails).

**Debugging Steps:**
1. **Check primary crash logs:**
   ```bash
   cat /var/log/postgresql/postgresql-*.log | grep -i "fatal"
   ```
   - Look for `out of memory` or `disk full` errors.

2. **Verify replication status before failover:**
   ```bash
   # For PostgreSQL
   pg_isready -h <primary>
   pg_isready -h <secondary> && echo "Secondary is ready"
   ```
   - If secondary is lagging, **wait or force sync**.

3. **Fix:**
   - **Increase primary resources** (RAM/disk).
   - **Use synchronous commit with retry logic**:
     ```yaml
     # Patroni config
     synchronize_bonds: true
     retry_timeout: 60
     ```

---

### **2.5 High Latency After Failover**
**Symptom:** Response times degrade post-failover.

**Root Causes:**
- **Network splits** (AWS AZ failure, GCP regional outage).
- **Secondary node is overloaded**.
- **Rewrite rules not updated** (DNS, load balancer).

**Debugging Steps:**
1. **Compare network paths:**
   ```bash
   # Test latency between primary/secondary and clients
   ping <primary>
   ping <secondary>
   traceroute <primary>
   ```
   - If secondary is in a different AZ, **use cross-AZ replication**.

2. **Check application rewrite logic:**
   ```bash
   # Example: NGINX failover config
   upstream db_nodes {
       server primary:5432;
       server secondary:5432 backup;
   }
   ```
   - Ensure `backup` is properly configured.

3. **Fix:**
   - **Use a global load balancer** (e.g., AWS Global Accelerator).
   - **Enable read replicas in separate AZs**.

---

### **2.6 Data Inconsistency Post-Failover**
**Symptom:** Secondary has stale data after promotion.

**Root Causes:**
- **Replication lag** (not all transactions applied).
- **Manual intervention** (e.g., `pg_basebackup` incomplete).
- **WAL segment corruption**.

**Debugging Steps:**
1. **Check replication lag:**
   ```sql
   -- PostgreSQL: Get replication delay
   SELECT age(pg_current_wal_lsn(), 'replay_lsn') AS replication_lag
   FROM pg_stat_replication;
   ```
   - If lag > acceptable threshold, **force sync or restore**.

2. **Verify WAL archiving:**
   ```bash
   # Check if WAL is being archived
   ls /path/to/wal_archive/
   ```
   - If missing, enable archiving in `postgresql.conf`.

3. **Fix:**
   - **Use synchronous commit with `fsync=on`** (PostgreSQL).
   - **Restore from a recent backup** if data is critical.

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**               | **Use Case**                                  | **Example Command**                     |
|-----------------------------------|-----------------------------------------------|------------------------------------------|
| **`pg_isready`**                 | Check PostgreSQL connection health            | `pg_isready -h <host> -p 5432`           |
| **`patronictl`**                 | Manage Patroni clusters                      | `patronictl -c /etc/patroni.yaml list`  |
| **`kubectl describe pod`**       | Check Kubernetes pod events                  | `kubectl describe pod <pod-name>`        |
| **`tcpdump`**                    | Network packet inspection                    | `tcpdump -i eth0 port 5432`              |
| **`strace`**                     | Trace system calls in failover scripts       | `strace -f patroni`                     |
| **Prometheus + Grafana**         | Monitor replication lag                      | Query `replication_lag_bytes`           |
| **AWS CloudWatch / GCP Stackdriver** | Cloud-based failover metrics               | Check `RDSReadReplicaStatus`             |

**Advanced:**
- **Use `pgBadger`** to analyze PostgreSQL logs:
  ```bash
  pgbadger /var/log/postgresql/postgresql.log
  ```
- **Enable `peer` journaling** (for faster failover in Kubernetes):
  ```yaml
  # In StatefulSet
  volumeMounts:
    - name: data
      mountPath: /var/lib/postgresql/data
      mountOptions:
        - discard
  ```

---

## **4. Prevention Strategies**

### **4.1 Architectural Best Practices**
1. **Multi-AZ Deployments**
   - Deploy secondaries in **different availability zones** (AWS RDS, GCP Cloud SQL).
   - Example (Kubernetes):
     ```yaml
     # Tolerations for AZ separation
     tolerations:
       - key: "topology.kubernetes.io/zone"
         operator: "Equal"
         value: "us-west-1b"
     ```

2. **Automated Health Checks**
   - Use **Prometheus + Alertmanager** to detect replication lag:
     ```yaml
     # Prometheus alert rule
     - alert: ReplicationLagHigh
       expr: replication_lag_seconds > 30
       for: 5m
       labels:
         severity: critical
       annotations:
         summary: "Replication lagging on {{ $labels.instance }}"
     ```

3. **Chaos Engineering**
   - **Simulate failures** with tools like **Chaos Mesh** or **Gremlin**:
     ```bash
     # Example: Kill a pod to test failover
     kubectl delete pod <primary-pod> --grace-period=0 --force
     ```

### **4.2 Configuration Hardening**
- **Set reasonable timeouts** in failover scripts:
  ```bash
  # Example: Retry logic in Patroni
  retry_timeout: 300  # 5-minute timeout
  ```
- **Enable WAL archiving** (PostgreSQL):
  ```conf
  wal_level = replica
  archive_mode = on
  archive_command = 'test ! -f /wal_archive/%f && cp %p /wal_archive/'
  ```

### **4.3 Monitoring and Alerts**
- **Track critical metrics:**
  - Replication lag (`replay_lsn` vs `write_lsn`).
  - Failover duration (should be < 10s for most setups).
  - Connection pool health (e.g., PgBouncer stats).
- **Example Grafana dashboard for PostgreSQL:**
  ![PostgreSQL Replication Dashboard](https://grafana.com/static/img/docs/dashboard.png)

### **4.4 Disaster Recovery Plan**
1. **Regular backups** (daily snapshots + WAL archiving).
2. **Test failover weekly** (manual promotion of secondaries).
3. **Document recovery steps** (e.g., "If primary fails, promote `<secondary-IP>`").

---

## **5. Summary of Key Fixes**
| **Issue**                          | **Quick Fix**                              | **Long-Term Solution**                  |
|-------------------------------------|--------------------------------------------|----------------------------------------|
| Hanging after failover              | Kill blocking queries (`pg_terminate_backend`) | Optimize queries, add indexes          |
| Degraded performance                | Scale secondary node                       | Use load balancer + read replicas      |
| Silent failover failure             | Check logs, test manual failover           | Enable verbose logging                 |
| Rollback after failover             | Increase primary resources                 | Use synchronous commit with retry      |
| High latency post-failover          | Use global load balancer                   | Deploy secondaries in separate AZs    |
| Data inconsistency                  | Force sync or restore from backup          | Enable WAL archiving + point-in-time-restore |

---

## **6. Final Checklist Before Production**
✅ **Test failover manually** (promote secondary, verify data consistency).
✅ **Monitor replication lag** (alert if > 10s).
✅ **Check health checks** (ensure secondary is always healthy).
✅ **Validate backups** (restore test data weekly).
✅ **Document recovery steps** (keep in a shared runbook).

---
**Next Steps:**
- If failover still fails, **isolate the component** (DB, network, application).
- Use **binary search** to narrow down the issue (e.g., "Does it fail with DB only, or with app too?").
- **Reproduce in staging** before applying fixes to production.

By following this guide, you should be able to **resolve 80% of failover issues within 30 minutes**. For deeper problems, consult vendor documentation (e.g., [Patroni docs](https://patroni.readthedocs.io/), [PostgreSQL replication guide](https://www.postgresql.org/docs/current/continuous-archiving.html)).