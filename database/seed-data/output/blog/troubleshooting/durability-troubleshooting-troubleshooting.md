# **Debugging Durability: A Troubleshooting Guide**
*Ensuring Data Consistency in Distributed and Stateful Systems*

Durability—guaranteeing that data persists even after system failures—is critical for reliable applications. This guide covers common issues, debugging techniques, and prevention strategies for durability problems in databases, distributed systems, and stateful services.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms to confirm durability issues:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| Data lost after crash/restart        | Uncommitted transactions, improper sync    |
| Inconsistent reads between instances | Replication lag, partial writes            |
| Slow recovery after failure          | Large logs, missing WAL (Write-Ahead Log)  |
| Failed transactions on restart       | Corrupted database, missing checkpoints     |
| High latency in durability operations | Blocked I/O, slow storage backend          |
| Missing logs in primary/standby      | Replication failure, checkpoint corruption |

If multiple of these occur, durability is likely the root cause.

---

## **2. Common Issues & Fixes**

### **2.1. Uncommitted Transactions on Crash**
**Symptom:** Data lost after a sudden server shutdown because transactions weren’t committed to disk.

#### **Fix: Use Write-Ahead Logging (WAL)**
Ensure your database or application uses a WAL to log changes before applying them to storage.

**PostgreSQL Example (WAL Configuration):**
```sql
-- Ensure WAL is enabled and properly synced
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET synchronous_commit = on;
ALTER SYSTEM SET fsync = on;
```
**Application-Level Fix (e.g., Python + SQLAlchemy):**
```python
from sqlalchemy import create_engine

# Enable WAL-like behavior in SQLite (or force sync in other DBs)
engine = create_engine('sqlite:///app.db', echo=True)
engine.execute("PRAGMA synchronous = FULL;")  # Ensures durability
```

---

### **2.2. Replication Lag Causing Inconsistencies**
**Symptom:** Primary and standby databases are out of sync, leading to stale reads.

#### **Fix: Adjust Replication Strategy**
- **For PostgreSQL:**
  ```sql
  -- Increase replication slot timeout
  ALTER SYSTEM SET wal_receiver_timeout = '30s';
  -- Monitor replication lag
  SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) FROM pg_stat_replication;
  ```
- **For Distributed Systems (e.g., Kafka):**
  ```bash
  # Check consumer lag
  kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group my-group --describe
  ```
  **Fix:** Scale brokers, increase partition count, or optimize commit logs.

---

### **2.3. Slow Recovery Due to Large Logs**
**Symptom:** Long downtime after a crash because the system is replaying a massive transaction log.

#### **Fix: Optimize Checkpointing & Log Retention**
- **PostgreSQL:**
  ```sql
  -- Reduce checkpoint frequency (adjust based on workload)
  ALTER SYSTEM SET checkpoint_timeout = '30min';
  -- Limit log retention
  ALTER SYSTEM SET wal_keep_size = '1GB';
  ```
- **General Rule:** Use **periodic checkpoints** + **log compression** (e.g., PostgreSQL’s `walsender` optimization).

---

### **2.4. Corrupted Database on Restart**
**Symptom:** Database refuses to start, reporting corruption.

#### **Fix: Repair & Validate**
- **PostgreSQL:**
  ```bash
  # Run pg_resetwal (for crash recovery)
  pg_resetwal -f /path/to/data

  # Check for corruption
  POSTGRES="pg_isready -U postgres" && touch /tmp/postgres_is_ready || exit 1
  ```
- **Application-Level:** Use **transaction rollback** on startup if possible:
  ```python
  # Example: Auto-recover failed transactions
  def on_startup():
      conn = get_db_connection()
      conn.execute("BEGIN TRANSACTION")
      try:
          # Verify critical data
          if not is_db_healthy():
              conn.rollback()
              raise RuntimeError("Database corrupted!")
      except Exception as e:
          logging.error(f"Recovery failed: {e}")
          raise
  ```

---

### **2.5. High Latency in Durability Operations**
**Symptom:** `fsync`/`commit` operations are slow, causing timeouts.

#### **Fix: Tune Storage & OS Settings**
- **Linux (SSD/HDD):**
  ```bash
  # Disable delayed writes (for SSDs)
  echo 0 | sudo tee /sys/devices/virtual/disk/by-id/*/queue/discard_granularity

  # Increase sync buffer size (if using syncfs)
  sudo sysctl -w vm.dirty_writeback_centisecs=500
  ```
- **Database-Level (PostgreSQL):**
  ```sql
  -- Reduce fsync frequency (trade-off: slight risk of data loss on crash)
  ALTER SYSTEM SET effective_cache_size = '4GB';  # Reduces unnecessary I/O
  ```

---

## **3. Debugging Tools & Techniques**

### **3.1. Logging & Metrics**
- **PostgreSQL:**
  ```sql
  -- Check WAL usage
  SELECT pg_size_pretty(pg_total_relation_size('pg_wal')::bigint);
  -- Monitor replication lag
  SELECT * FROM pg_stat_replication;
  ```
- **Application Logging:**
  ```python
  import logging
  logging.basicConfig(level=logging.INFO)
  logging.info(f"Transaction committed: {tx_id} (WAL offset: {wal_offset})")
  ```

### **3.2. Binary Log Analysis**
- **PostgreSQL:**
  ```bash
  # Parse WAL files for corruption
  pg_waldump -f /path/to/pg_wal/000000010000000000000001
  ```
- **Distributed Systems (e.g., Kafka):**
  ```bash
  # Check log segment health
  kafka-log-dirs --describe --bootstrap-server localhost:9092 --topic my-topic
  ```

### **3.3. Crash Dump Analysis**
- **Linux:**
  ```bash
  # Capture crash info
  gdb /path/to/db_server /var/crash/db_server.core
  (gdb) bt full  # Backtrace on crash
  ```
- **Database-Specific:**
  ```bash
  # PostgreSQL core dump analysis
  pg_checksums --dbname=my_db --file=/tmp/corrupt_db.dump
  ```

### **3.4. Network & Replication Health Checks**
- **PostgreSQL Replication:**
  ```bash
  # Test replication connection
  psql -h standby_host -p 5432 -c "SELECT pg_is_in_recovery()"
  ```
- **Distributed Systems:**
  ```bash
  # Check RPC latency (e.g., gRPC, Kafka)
  curl -v http://primary-rpc-server:50051/health
  ```

---

## **4. Prevention Strategies**

### **4.1. Design for Durability Early**
- **Use ACID-Compliant Databases:** PostgreSQL, MySQL (InnoDB), CockroachDB.
- **Avoid Optimistic Locking for Critical Data:** Use **pessimistic locks** or **MvCC (Multi-Version Concurrency Control)** where needed.
- **Enable Checkpointing:**
  ```sql
  -- PostgreSQL: Auto-checkpointing
  ALTER SYSTEM SET checkpoint_segments = 3;  # Default is 3, adjust as needed
  ```

### **4.2. Automated Failover & Replication**
- **PostgreSQL Stream Replication:**
  ```bash
  # Set up standby
  initdb -D /var/lib/postgresql/standby
  pg_basebackup -h primary_host -D /var/lib/postgresql/standby -R -P
  ```
- **Distributed Systems:**
  - Use **Raft** (etcd, Consul) or **Paxos** (ZooKeeper) for leader election.
  - **Kafka:** Enable `unclean.leader.election.enable=false` to prevent splits.

### **4.3. Regular Maintenance**
- **Vacuum & Analyze (PostgreSQL):**
  ```sql
  VACUUM (VERBOSE, ANALYZE);
  AUTOVACUUM -- Enable for background cleanup
  ```
- **Database Backups:**
  ```bash
  # PostgreSQL: Logical backup (WAL-aware)
  pg_dump --dbname=my_db --format=custom --file=backup.dump
  ```
- **Monitor Durability Metrics:**
  - **Prometheus + Grafana:** Track `pg_stat_replication_lag`, `fsync_time`.
  - **CloudWatch/Stackdriver:** Alert on `WriteLatency > 1s`.

### **4.4. Test Failure Scenarios**
- **Chaos Engineering:**
  ```bash
  # Kill primary node (if using Kubernetes)
  kubectl delete pod primary-pod
  ```
  **Expected:** Standby should promote automatically.
- **Database Crash Tests:**
  ```bash
  # Force a crash (Linux)
  kill -9 $(pgrep postgres)
  ```

---

## **5. Quick Reference Cheat Sheet**
| **Issue**                | **Immediate Fix**                          | **Long-Term Fix**                     |
|--------------------------|--------------------------------------------|---------------------------------------|
| Data lost on crash       | Restore from backup + WAL replay           | Enable WAL + `fsync`                  |
| Replication lag          | Scale replicas                            | Optimize `wal_level`, partitions      |
| Slow recovery            | Reduce log retention (`wal_keep_size`)    | Increase hardware (SSD, RAM)          |
| Corrupted database       | `pg_resetwal` (PostgreSQL)                | Enable `fsync`, test failovers        |
| High `fsync` latency     | Tune OS sync settings (`vm.dirty_writeback`) | Use SSD/NVMe storage                  |

---

## **6. Final Checklist Before Deployment**
1. ✅ **WAL is enabled** (`wal_level=replica`).
2. ✅ **Synchronous commits are enforced** (`synchronous_commit=on`).
3. ✅ **Replication lag < acceptable threshold** (e.g., <1s for OLTP).
4. ✅ **Backups are tested regularly**.
5. ✅ **Failover tests pass** (manual + automated).
6. ✅ **Monitoring alerts exist** for `fsync` delays, replication issues.

---
**Next Steps:**
- If issues persist, **review transaction logs** (`postgres.log`, `syslog`).
- For distributed systems, **check network partitions** (`ping`, `mtr`).
- Consider **third-party tools** like **Perconal Toolkit** (for MySQL) or **Postgres Pro** (for advanced durability checks).