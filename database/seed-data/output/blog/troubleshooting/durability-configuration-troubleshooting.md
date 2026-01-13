# **Debugging Durability Configuration: A Troubleshooting Guide**

## **Introduction**
Durability in distributed systems ensures that data persists reliably across failures—whether due to crashes, network partitions, or hardware issues. Common durability patterns include **write-ahead logging (WAL), snapshots, replication, and eventual consistency mechanisms**.

This guide focuses on diagnosing and resolving issues related to **Durability Configuration**, covering symptoms, root causes, and actionable fixes.

---

## **1. Symptom Checklist**
Before diving into debugging, verify if the issue aligns with durability-related symptoms:

| **Symptom**                          | **Description**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------|
| **Data Loss on Crash**               | After a server restart, recent writes are missing from the database.           |
| **Inconsistent Replication**         | Primary and replica nodes have diverging data states.                         |
| **Slow Write Performance**           | Transactions take unusually long to complete, even under low load.             |
| **Corrupted Log Files**               | Crash recovery fails due to invalid log entries.                               |
| **Failover Timeouts**                | Primary node takes too long to failover, causing prolonged downtime.          |
| **Eventual Consistency Delays**       | Clients see stale data after replication propagates (longer than expected).   |
| **Snapshot Recovery Fails**          | Restoring from a snapshot fails with I/O or corruption errors.                  |

If multiple symptoms appear, prioritize **data loss** first, as it indicates severe configuration misalignment.

---

## **2. Common Issues & Fixes**
### **2.1 Data Loss on Crash (Unflushed Writes)**
**Cause:**
- Transactions committed but not persisted to disk before failure.
- Missing `fsync()` or `sync()` operations in storage engines (e.g., PostgreSQL, MongoDB).

**Debugging Steps:**
1. **Check Logs for Unflushed Entries**
   - For PostgreSQL:
     ```bash
     grep "unflushed" /var/log/postgresql/postgresql-*log
     ```
   - For MongoDB:
     ```bash
     mongod --logpath /var/log/mongodb/mongod.log --quiet --grep "unflushed"
     ```

2. **Verify WAL (Write-Ahead Log) Configuration**
   - **PostgreSQL:**
     Ensure `synchronous_commit = on` and `fsync = on` in `postgresql.conf`.
   - **MongoDB:**
     Check `journal: true` in `mongod.conf`.

3. **Force Sync on Commit (If Missing)**
   - **PostgreSQL (via `pg_controldata`):**
     ```sql
     SELECT pg_controldata('pgdata') -> 'checksum'; -- Verify WAL is active
     ```
   - **MongoDB (Logging):**
     ```bash
     tail -f /var/log/mongodb/mongod.log | grep "journal write"
     ```

**Fix (If Applicable):**
- **PostgreSQL:** Restart with `pg_controldata -o -f` (if WAL is missing).
- **MongoDB:** Enable WAL: `mongod --journal --storageEngine wiredTiger`.

---

### **2.2 Inconsistent Replication**
**Cause:**
- Replication lag due to slow followers or misconfigured sync mechanisms.
- Network partitions causing splits-brain scenarios.

**Debugging Steps:**
1. **Check Replication Lag**
   - **PostgreSQL:**
     ```sql
     SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
     ```
   - **MongoDB:**
     ```bash
     rs.printReplicationInfo()
     ```

2. **Verify Replica Set Configuration**
   - Ensure `replSetName` matches across all nodes.
   - Check `priority` and `votes` in MongoDB’s `rs.conf()` to avoid splits-brain.

3. **Inspect Network Latency**
   - Use `ping` and `mtr` to test connectivity between nodes.

**Fix:**
- **PostgreSQL:** Adjust `max_replication_slots`.
- **MongoDB:** Increase `replTimeout` or add a secondary node:
  ```javascript
  rs.add("secondary-node:27017")
  ```

---

### **2.3 Slow Write Performance**
**Cause:**
- Over-optimized durability settings (e.g., `fsync` too frequent).
- Disk I/O bottlenecks due to high WAL writes.

**Debugging Steps:**
1. **Measure Disk I/O**
   ```bash
   iostat -x 1  # Check disk utilization
   dstat -d     # Detailed disk stats
   ```

2. **Check Database Metrics**
   - **PostgreSQL:**
     ```sql
     SELECT * FROM pg_stat_database WHERE datname = 'your_db';
     ```
   - **MongoDB:**
     ```bash
     db.serverStatus().opcounters
     ```

3. **Optimize Durability Settings**
   - **PostgreSQL:** Tune `effective_cache_size` and `shared_buffers`.
   - **MongoDB:** Adjust `writeConcern` to `majority` vs. `acknowledged`.

**Fix:**
- **PostgreSQL:**
  ```ini
  # Reduce sync frequency (if acceptable)
  synchronous_commit = on          # Default is safe
  ```
- **MongoDB:**
  ```javascript
  db.getSiblingDB("db").setWriteConcern({ w: 1 })  # Less strict
  ```

---

### **2.4 Corrupted Log Files**
**Cause:**
- Improper shutdown (e.g., `kill -9` instead of `shutdown`).
- Disk failures or filesystem corruption.

**Debugging Steps:**
1. **Check Log File Integrity**
   ```bash
   fsck -f /var/lib/postgresql     # PostgreSQL
   fsck -f /var/lib/mongodb        # MongoDB
   ```

2. **Inspect WAL Files**
   - **PostgreSQL:**
     ```bash
     ls -la /var/lib/postgresql/9.6/main/pg_wal/
     ```
   - **MongoDB:**
     ```bash
     ls -la /var/lib/mongodb/journal/
     ```

**Fix:**
- **PostgreSQL:** Restore from backup or use `pg_resetwal`.
- **MongoDB:** Reconfigure WAL path:
  ```bash
  mongod --journal --storageEngine wiredTiger --dbpath /custom/wal/path
  ```

---

## **3. Debugging Tools & Techniques**
### **3.1 Logging & Monitoring**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **PostgreSQL Logs**    | `postgresql.conf` (`log_statement = all`, `log_line_prefix = '%m [%p]')`    |
| **MongoDB Logs**       | `mongod.log` (`--logpath`, `--logAppend`)                                  |
| **Prometheus/Grafana** | Track replication lag, write latency, and node health.                     |
| **Journald (Linux)**   | `journalctl -u postgresql` (systemd-based systems)                         |

### **3.2 Recovery Testing**
- **PostgreSQL:**
  ```bash
  pg_ctl start -D /path/to/data --single -l /tmp/recovery.log
  ```
- **MongoDB:**
  ```bash
  mongod --replSet "rs0" --dbpath /backup/path --oplogSize 1024
  ```

### **3.3 Network Diagnostics**
- **Latency Check:**
  ```bash
  mtr replica-node.example.com
  ```
- **Packet Loss:**
  ```bash
  ping -c 100 replica-node.example.com
  ```

---

## **4. Prevention Strategies**
### **4.1 Configuration Best Practices**
| **Database**  | **Setting**                     | **Recommended Value**                          |
|---------------|----------------------------------|-----------------------------------------------|
| **PostgreSQL** | `synchronous_commit`             | `on`                                          |
| **PostgreSQL** | `full_page_writes`               | `on` (for critical data)                     |
| **MongoDB**    | `journal`                        | `true`                                        |
| **MongoDB**    | `replSetSyncPeriodSecs`          | `2` (balance between speed and safety)        |

### **4.2 Regular Maintenance**
- **Backup Testing:** Validate restore procedures monthly.
- **Disk Health Checks:** Use `smartctl` to monitor HDD/SSD health:
  ```bash
  smartctl -a /dev/sda
  ```
- **Failover Drills:** Test failover scenarios quarterly.

### **4.3 Automated Alerts**
- **PostgreSQL:**
  ```sql
  CREATE OR REPLACE FUNCTION check_replication_lag()
  RETURNS trigger AS $$
  BEGIN
    IF lag_greater_than_5_secs THEN
      RAISE EXCEPTION 'Replication lag detected!';
    END IF;
  END;
  $$ LANGUAGE plpgsql;
  ```
- **MongoDB:**
  ```javascript
  db.adminCommand({
    replSetGetStatus: 1,
    explain: true
  });
  ```

---

## **5. Conclusion**
Durability issues are critical but often preventable with proper configuration and monitoring. This guide provides a structured approach to:
1. **Identify symptoms** (data loss, replication lag).
2. **Diagnose root causes** (missing WAL, network issues).
3. **Apply fixes** (tune settings, restore from backups).
4. **Prevent recurrence** (testing, alerts, regular checks).

**Final Checklist Before Production Deployment:**
✅ Validate WAL/journal configuration.
✅ Test failover scenarios.
✅ Monitor replication lag in staging.

By following these steps, you can resolve durability-related issues efficiently and maintain system reliability.