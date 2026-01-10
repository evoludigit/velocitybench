# **Debugging Database Replication Strategies: A Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **1. Introduction**
Database replication ensures data consistency across multiple nodes, improving fault tolerance, read scalability, and disaster recovery. However, misconfigurations, network issues, or storage failures can disrupt replication, leading to outages, data inconsistency, or corruption.

This guide provides a **practical, actionable troubleshooting approach** for common replication failures, focusing on **quick diagnosis and resolution**.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the issue using these **quick checks**:

| **Symptom**               | **How to Detect**                                                                 | **Severity** |
|---------------------------|------------------------------------------------------------------------------------|--------------|
| **Primary unavailable**   | `SHOW MASTER STATUS` (MySQL), `pg_isready -U postgres` (PostgreSQL), `kubectl logs` (K8s) | Critical     |
| **Replica lagging**       | `SHOW SLAVE STATUS \G` (MySQL), `pg_repack` lag analysis (PostgreSQL), Prometheus metrics | Medium       |
| **Failed replication**    | Error logs (`/var/log/mysql/error.log`, `/var/log/postgresql/postgresql-*.log`) | High         |
| **Data drift**            | `SELECT * FROM table1 WHERE id = X` (compare primary vs. replica)                | Critical     |
| **Network issues**        | `ping`, `tcpdump`, `netstat -an` (check network latency, dropouts)                | Medium       |
| **Storage full**          | `df -h` (filesystem full), `du -sh /var/lib/mysql`                               | High         |

🔹 **Action:** If primary is down, **failover immediately** (if using a HA setup like Galera, Patroni, or Kubernetes-based replicas).

---

## **3. Common Issues & Fixes**

### **Issue 1: Replication Not Starting (MySQL)**
**Symptoms:**
- `SHOW SLAVE STATUS` shows `Slave_IO_Running: No`
- Error logs contain `Got fatal error 1236` (out of sync) or `Could not start slave`

**Root Causes:**
✅ **Binary log (`binlog`) misconfiguration** (e.g., `log_bin` not enabled on primary)
✅ **Incorrect replication user permissions** (`REPLICATION SLAVE` not granted)
✅ **Network issues** (firewall blocking port `3306`)
✅ **Clock skew** (`NTP` misconfigured between nodes)

**Quick Fixes:**
```sql
-- On PRIMARY:
1. Ensure binlogs are enabled:
   SET GLOBAL log_bin = ON;

2. Grant replication privileges:
   GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'%' IDENTIFIED BY 'password';

3. Find binlog position (for new slaves):
   SHOW MASTER STATUS;  -- Note File & Position

-- On REPLICA:
4. Configure replication in my.cnf (or my.ini):
   [mysqld]
   server-id = 2
   replicate-do-db = your_db
   relay-log = /var/log/mysql/relay-bin.log

5. Start replication:
   STOP SLAVE;
   RESET SLAVE ALL;
   CHANGE MASTER TO
     MASTER_HOST='primary-ip',
     MASTER_USER='repl_user',
     MASTER_PASSWORD='password',
     MASTER_LOG_FILE='binlog.000001',
     MASTER_LOG_POS=1234;
   START SLAVE;
```

**Verification:**
```sql
SHOW SLAVE STATUS \G
-- Check: Slave_IO_Running: Yes, Slave_SQL_Running: Yes
```

---

### **Issue 2: Replication Lag (PostgreSQL)**
**Symptoms:**
- `pg_isready` shows replication active but queries return stale data.
- `SELECT * FROM pg_stat_replication` shows `replay_lag` > X seconds.

**Root Causes:**
✅ **High WAL (`Write-Ahead Log`) generation rate** (primary overloaded)
✅ **Slow replica disks** (HDD vs. SSD, full disk)
✅ **Network congestion** (high latency between nodes)
✅ **Stuck transactions** (long-running queries on primary)

**Quick Fixes:**
```sql
-- On PRIMARY:
1. Check active WAL replay (PostgreSQL 10+):
   SELECT * FROM pg_stat_replication;

-- On REPLICA:
2. Increase `max_wal_senders` (if replication load is high):
   ALTER SYSTEM SET max_wal_senders = 10;

3. Check disk I/O:
   iostat -x 1  -- Monitor disk latency

4. If stuck, reset replication (careful!):
   SELECT pg_stop_backup();
   SELECT pg_start_backup('manual_resync', true);
   -- Reconnect the replica
```

**Alternative:** Use **logical replication** (PostgreSQL 10+) for better control:
```sql
-- On PRIMARY:
CREATE PUBLICATION my_pub FOR ALL TABLES;

-- On REPLICA:
CREATE SUBSCRIPTION my_sub CONNECTION 'host=primary port=5432 user=repl_user'
PUBLISHER my_pub;
```

---

### **Issue 3: Data Corruption Propagation**
**Symptoms:**
- `PRIMARY` and `REPLICA` have different row counts.
- Errors like `ERROR 1062 (23000): Duplicate entry` on replica.

**Root Causes:**
✅ **Manual `INSERT`/`UPDATE` on replica** (bypassing replication)
✅ **Cascading delete issues** (foreign key constraints)
✅ **Partial replication** (`replicate-ignore-db` misconfigured)

**Quick Fixes:**
```sql
-- On REPLICA:
1. Check for rogue transactions:
   SHOW BINARY LOGS;  -- MySQL
   SELECT * FROM pg_stat_replication;  -- PostgreSQL

2. If corruption detected:
   -- MySQL: Reset replica (last resort)
   STOP SLAVE;
   RESET SLAVE ALL;
   RESET MASTER;  -- Only if primary is safe

   -- PostgreSQL: Use `pg_rewind` (if safe)
   pg_rewind --source primary-host --target replica-host
```

**Prevention:**
- **Enforce strict replication rules** (e.g., `replicate-do-db=only_db_name`)
- **Use `CHANGE MASTER TO MASTER_AUTO_POSITION = 1`** (PostgreSQL) to avoid log file tracking.

---

### **Issue 4: Network-Dependent Failures**
**Symptoms:**
- `Slave_IO_Running: Disconnected` (MySQL)
- `ERROR: could not connect to server: Connection refused` (PostgreSQL)

**Root Causes:**
✅ **Firewall blocking** (ports `3306`/PostgreSQL default `5432`)
✅ **MTU issues** (jumbo frames not configured)
✅ **Load balancer misrouting** (traffic not reaching replica)

**Quick Fixes:**
```bash
# Test connectivity
nc -zv replica-ip 3306  # MySQL
telnet replica-ip 5432  # PostgreSQL

# Check firewall (Ubuntu)
sudo ufw allow 3306/tcp
sudo ufw allow 5432/tcp

# Check MTU (if latency issues)
ping -M do -s 1472 replica-ip  # Test 1500-byte MTU
```

**Permanent Fix:**
- **Use dedicated VPC peering/network** for replication traffic.
- **Monitor with `ping` and `mtr`** for latency spikes.

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                                                 | **Command/Usage**                          |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **`SHOW MASTER STATUS`** | Get replication binlog position (MySQL)                                    | `SHOW MASTER STATUS;`                      |
| **`pg_stat_replication`** | Check replication lag (PostgreSQL)                                          | `SELECT * FROM pg_stat_replication;`       |
| **`netstat`**          | Verify network connections between nodes                                    | `netstat -an | grep 3306`                                |
| **`tcpdump`**          | Capture replication traffic for analysis                                    | `tcpdump -i eth0 port 3306 -w replay.pcap` |
| **`Prometheus + Grafana`** | Monitor replication lag, errors, and latency historically              | Query `replication_lag_seconds`             |
| **`pgBadger`**         | Analyze PostgreSQL logs for replication errors                             | `pgbadger /var/log/postgresql/postgresql.log` |
| **`mysqldump`**        | Compare schema/data between nodes (if replication is broken)               | `mysqldump -u root -p db_name > backup.sql` |

**Advanced Debugging:**
- **Enable binary log (`binlog`) debugging** (MySQL):
  ```ini
  [mysqld]
  log_bin = /var/log/mysql/mysql-bin.log
  binlog_format = ROW
  server-id = 1
  ```
- **PostgreSQL Wal Receiver Debugging**:
  ```bash
  psql -c "SHOW replication_slots;"
  psql -c "SHOW wal_level;"
  ```

---

## **5. Prevention Strategies**

### **A. Configuration Best Practices**
| **Database**  | **Recommendation**                                                                 |
|---------------|-------------------------------------------------------------------------------|
| **MySQL**     | Use `GTID` (Global Transaction IDs) for failover safety.                         |
| **PostgreSQL** | Enable **logical replication** for fine-grained control.                       |
| **General**   | Always **test failover** in staging before production.                          |

### **B. Monitoring & Alerts**
- **Replication Lag Alerts** (Prometheus):
  ```yaml
  - alert: ReplicationLagHigh
    expr: replication_lag_seconds > 60
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Replication lagging on {{ $labels.instance }}"
  ```
- **Disk Space Alerts**:
  ```bash
  watch -n 1 'df -h | grep /var/lib/mysql && free -m'
  ```

### **C. Backup & Recovery**
- **Automated backups** (MySQL):
  ```bash
  mysqldump -u root -p --all-databases > full_backup.sql
  ```
- **PostgreSQL WAL Archiving**:
  ```ini
  # postgresql.conf
  wal_level = replica
  archive_mode = on
  archive_command = 'test ! -f /backup/%f && cp %p /backup/%f'
  ```

### **D. Disaster Recovery Plan**
1. **Primary Failure?** → Promote replica (using `pt-table-sync` for MySQL, `pg_rewind` for PostgreSQL).
2. **Replica Corruption?** → Restore from backup + reconfigure replication.
3. **Network Outage?** → Use **asynchronous replication** temporarily.

---

## **6. Final Checklist for Resolution**
✅ **Verify primary health** (`SHOW STATUS LIKE 'Uptime'`)
✅ **Check replication status** (`SHOW SLAVE STATUS`)
✅ **Inspect logs** (`tail -f /var/log/mysql/error.log`)
✅ **Test connectivity** (`telnet`, `ping`)
✅ **Monitor lag** (`SHOW SLAVE STATUS \G`)
✅ **Failover if needed** (if primary is down)

---
**Next Steps:**
- **For MySQL:** Use `pt-table-checksum` to verify data consistency.
- **For PostgreSQL:** Consider **Patroni** for automated failover.
- **For Kubernetes:** Use **Velero** for backup + **Stolon** for PostgreSQL HA.

---
**This guide ensures rapid diagnosis and resolution of replication issues while preventing future outages.** 🚀