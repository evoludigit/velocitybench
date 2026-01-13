# **Debugging Durability Testing: A Troubleshooting Guide**

## **1. Introduction**
Durability Testing ensures that a system can reliably handle failures, data persistence, and recover from unexpected interruptions without losing critical data or functionality. This guide provides a structured approach to debugging common durability-related issues in distributed systems, databases, and applications.

---

## **2. Symptom Checklist**
Before diving into fixes, identify which of the following symptoms match your issue:

| **Symptom**                          | **Likely Cause**                          | **Possible Impact**                     |
|--------------------------------------|------------------------------------------|-----------------------------------------|
| Data loss after crashes/reboots      | Uncommitted transactions, improper logs  | Permanent data corruption              |
| High latency during recovery         | Slow checkpointing, delayed replication  | Poor user experience                    |
| Failed transactions on restart       | Dirty page detection, WAL corruption   | Application crashes or inconsistencies  |
| Persistent state corruption         | Race conditions, incorrect serialization | Inconsistent application state         |
| Slow recovery despite sufficient storage | Optimizer misconfiguration, lazy writes | Degraded system performance             |
| Replicated data inconsistencies      | Eventual consistency delays, failed quorums | Split-brain or stale reads             |

---

## **3. Common Issues and Fixes**

### **3.1 Data Loss After Crashes**
**Symptom:** Critical database records or application state disappear after a server crash or unexpected shutdown.

#### **Root Causes & Fixes**
| **Root Cause**                     | **Fix (Code/Config Example)**                                                                 | **Verification Steps**                          |
|------------------------------------|-----------------------------------------------------------------------------------------------|------------------------------------------------|
| **Unflushed writes**               | Ensure transaction logs (WAL) are synced before commit.                                      | Check `fsync(2)` or `fdatasync(2)` calls for databases (e.g., PostgreSQL, RocksDB). |
| **No transactions**               | Wrap critical operations in database transactions.                                           | Example (SQL): `BEGIN; INSERT...; COMMIT;`     |
| **Improper checkpointing**        | Configure a checkpoint interval (`checkpoint_segments` in PostgreSQL).                       | Monitor `pg_switch_wal` logs.                   |
| **Missing durable storage**        | Use `O_DSYNC` (`open(..., O_DSYNC)`) for critical files to force OS-level durability.         | Check `dmesg` for sync operations.            |

**Example (PostgreSQL Durability Fix):**
```sql
-- Ensure synchronous commit (default: on)
ALTER SYSTEM SET synchronous_commit = 'on';

-- Force WAL segment rotation
ALTER SYSTEM SET wal_segment_size = '16MB';
```
**Example (In-Memory Cache Durability Fix):**
```java
// Use Filesystem-backed storage with sync
try (DataOutputStream dos = new DataOutputStream(new FileOutputStream("cache.dat", true))) {
    dos.writeBytes(serialize(state));
    dos.flush();
    dos.getChannel().force(true); // Force OS sync
}
```

---

### **3.2 High Recovery Latency**
**Symptom:** System recovers slowly after a failure, causing timeouts or degraded performance.

#### **Root Causes & Fixes**
| **Root Cause**                     | **Fix**                                                                                     | **Verification**                               |
|------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------|
| **Large checkpoint size**          | Increase parallel checkpoint threads (`checkpoint_completion_target` in PostgreSQL).         | Monitor `pg_stat_activity` for checkpoint time. |
| **Delayed replication**            | Tune `replication_slots` (PostgreSQL) or `wal_level=replica`.                              | Check `pg_stat_replication`.                    |
| **Lazy writes not flushed**        | Use synchronous replication (`synchronous_commit = 'remote_apply'`).                     | Verify `peer` status with `pg_isready`.        |
| **Slow disk I/O**                  | Use SSDs, RAID 10, or partition WAL files across disks.                                     | Run `iostat -x 1` to check disk latency.       |

**Example (PostgreSQL Checkpoint Tuning):**
```sql
-- Reduce checkpoint overhead
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET checkpoint_timeout = '30min';
```

---

### **3.3 Failed Transactions on Restart**
**Symptom:** Database or application fails to recover transactions from the last checkpoint.

#### **Root Causes & Fixes**
| **Root Cause**                     | **Fix**                                                                                     | **Verification**                               |
|------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------|
| **Dirty pages at crash**           | Ensure `fsync` after every `insert`/`update` (PostgreSQL default: `fsync = on`).            | Check `postgres.conf`: `fsync = on`.           |
| **WAL corruption**                 | Run `pg_resetwal -f` (careful: destroys data unless backed up).                             | Test with `pg_checksums`.                      |
| **Serialization errors**           | Use `BEGIN TRANSACTION` with explicit `ISOLATION LEVEL SERIALIZABLE`.                      | Example: `BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;`. |
| **Inconsistent replication lag**   | Adjust `max_wal_senders` and `max_replication_slots`.                                        | Check `show max_wal_senders;`.                 |

**Example (RocksDB Durability Fix):**
```cpp
// Enable write-ahead logging (WAL) with sync
RocksDB::Options options;
options.write_buffer_size = 64 * 1024 * 1024;
options.write_buffer_count = 2;
options.db_log_dir = "/var/log/rocksdb_wal";
db->SetCompressionType(kSnappyCompression);
db->SetAllowWriteStall(true);
```

---

### **3.4 Persistent State Corruption**
**Symptom:** Application state (e.g., in-memory caches, config maps) becomes inconsistent after restarts.

#### **Root Causes & Fixes**
| **Root Cause**                     | **Fix**                                                                                     | **Verification**                               |
|------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------|
| **In-memory-only storage**         | Persist state to disk (e.g., Redis RDB snapshots, etcd backups).                           | Example: `save 900 10` (Redis AOF + RDB).      |
| **Race conditions in writes**      | Use atomic updates (e.g., `CompareAndSwap`) or distributed locks (e.g., ZooKeeper).         | Example (Java): `AtomicReference`.             |
| **Improper serialization**         | Use structured formats (Protocol Buffers, Avro) with checksums.                            | Example: `protobuf::Message::SerializeToString()`. |

**Example (Etcd Durability Fix):**
```bash
# Enable periodic snapshots
ETCD_SNAPSHOT_COUNT=10000 etcd --snapshot-count=10000
```

---

### **3.5 Slow Recovery Despite Sufficient Storage**
**Symptom:** System recovers slowly even when storage is not a bottleneck.

#### **Root Causes & Fixes**
| **Root Cause**                     | **Fix**                                                                                     | **Verification**                               |
|------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------|
| **Optimizer misconfig**            | Tune `effective_cache_size` (PostgreSQL) or RocksDB block cache.                            | Example: `ALTER SYSTEM SET effective_cache_size = '8GB';` |
| **Lazy recovery mode**             | Force immediate recovery (`ALTER SYSTEM SET recovery_target_inclusive = 'true'`).          | Check `pg_stat_replication` for recovery progress. |
| **Background writer stall**        | Increase `maintenance_work_mem` (PostgreSQL) or `background_threads` (RocksDB).            | Monitor `pg_stat_database` for long queries.    |

**Example (RocksDB Block Cache Tuning):**
```cpp
RocksDB::Options options;
options.block_cache = CreateBlockCache(512 * 1024 * 1024); // 512MB cache
```

---

## **4. Debugging Tools and Techniques**

### **4.1 Database-Specific Tools**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `pg_checksums`         | Verify WAL and table integrity in PostgreSQL.                               | `pg_checksums --global`                     |
| `rocksdb_db_dump`      | Inspect RocksDB state before recovery.                                        | `rocksdb_db_dump --dump_filter="*" dbpath` |
| `etcdctl snapshot save` | Capture etcd cluster state for manual recovery.                             | `etcdctl snapshot save snapshot.db`        |

### **4.2 OS-Level Debugging**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `dmesg`                | Check kernel logs for filesystem sync errors.                                | `dmesg | grep -i "sync\|error"`                     |
| `iostat -x 1`          | Monitor disk I/O latency during recovery.                                    | Look for `await` > 100ms.                  |
| `strace`               | Trace system calls in a crashing process.                                   | `strace -f -e trace=file ./your_binary`    |

### **4.3 Distributed Tracing**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| **OpenTelemetry**      | Correlate durability failures across services.                              | `otel-collector --config=otel-config.yml`   |
| **Prometheus + Alerts**| Track recovery time (e.g., `postgres_up` vs. `postgres_recovery_time`).    | `alert("HighRecoveryTime", if recovery_time > 300s)` |

---

## **5. Prevention Strategies**

### **5.1 Design-Time Mitigations**
| **Strategy**                          | **Implementation**                                                                 | **Example**                                  |
|---------------------------------------|------------------------------------------------------------------------------------|---------------------------------------------|
| **Atomic Writes**                     | Use ACID transactions or distributed transactions (Saga pattern).                | PostgreSQL `BEGIN/COMMIT`, Kafka transactions. |
| **Checkpointing**                     | Configure regular snapshots (PostgreSQL `checkpoint_segments`, Kafka `log.segment.bytes`). | `ALTER SYSTEM SET checkpoint_timeout = '10min';` |
| **Replication**                       | Set up synchronous replication (PostgreSQL `synchronous_commit = 'on'`).          | `ALTER SYSTEM SET max_replication_slots = 10;` |
| **Durable Storage**                   | Avoid in-memory-only stores; use SSDs with `O_DSYNC`.                              | `open("/data/file", O_WRONLY | O_DSYNC)`  |

### **5.2 Runtime Monitoring**
| **Metric**                          | **Tool**                | **Threshold**                     |
|-------------------------------------|-------------------------|-----------------------------------|
| WAL write latency                   | PostgreSQL `pg_stat_wal_receiver` | < 100ms                            |
| Checkpoint duration                 | Prometheus `postgres_checkpoint_duration_seconds` | < 10s for 1TB+ DB       |
| Replication lag                     | `pg_isready -U user -d db` | < 1s                               |
| Disk sync time                      | `dmesg` logs            | < 50ms for critical writes        |

### **5.3 Automated Recovery**
| **Technique**                        | **Tool/Example**                                                                 | **Use Case**                              |
|--------------------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Automated Failover**              | PostgreSQL `pg_ctl promote`, etcd `etcdctl snapshot restore`.                  | High-availability clusters.              |
| **Chaos Engineering**               | Run `chaos-mesh` to simulate node failures.                                     | Test durability under stress.            |
| **Backup Validation**               | Use `pg_basebackup` (PostgreSQL) or `etcdbackup` to verify backups.            | Recover from worst-case scenarios.        |

---

## **6. Step-by-Step Recovery Procedure**
1. **Identify the Failure Mode**
   - Check logs (`journalctl`, `postgres.log`, `etcd.log`) for `ERROR` or `PANIC` entries.
   - Verify if the issue is data loss, latency, or corruption.

2. **Assess Storage Health**
   ```bash
   # Check disk health (Linux)
   smartctl -a /dev/sdX | grep "Reallocated_Sector_Ct"
   ```

3. **Restore from Backup (If Data Loss)**
   ```bash
   # Example: PostgreSQL restore
   pg_restore -U postgres -d dbname -F custom backup.dump
   ```

4. **Manual Recovery (If No Backup)**
   - For PostgreSQL: `pg_resetwal -f` (destructive, use only if no backup).
   - For RocksDB: Repopulate from `db_log` if available.

5. **Tune for Future Durability**
   - Adjust `synchronous_commit`, `checkpoint_segments`, or `wal_level` as needed.

6. **Monitor Recovery**
   ```sql
   -- PostgreSQL: Check recovery progress
   SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
   ```

---

## **7. Conclusion**
Durability issues often stem from **unflushed writes**, **misconfigured replication**, or **race conditions**. The key is:
1. **Prevent** with ACID, checkpoints, and replication.
2. **Detect** using logs, metrics, and tracing.
3. **Recover** with backups or atomic rollback (if possible).

**Final Checklist Before Rollout:**
- [ ] Enable `fsync` (or equivalent) for critical writes.
- [ ] Configure synchronous replication.
- [ ] Test recovery in a staging environment.
- [ ] Monitor `recovery_time` and `checkpoint_duration` post-deployment.

By following this guide, you can systematically diagnose and resolve durability-related failures while building resilience into your systems.