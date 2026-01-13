# **Debugging Durability Gotchas: A Troubleshooting Guide**

Durability refers to the ability of a system to reliably preserve data even in the face of failures, including crashes, network outages, or hardware failures. Misconfigurations or oversight in durability guarantees can lead to data loss, duplicate transactions, or inconsistent states. This guide provides a structured approach to diagnosing, resolving, and preventing common durability-related issues in distributed systems.

---

## **1. Symptom Checklist: Identifying Durability Issues**
Before diving into fixes, verify whether the system exhibits signs of durability problems. Check for:

| **Symptom**                          | **Likely Cause**                          | **How to Validate** |
|--------------------------------------|-------------------------------------------|---------------------|
| **Data loss after crashes**           | Uncommitted transactions not persisted   | Check log files for incomplete writes |
| **Duplicate operations**              | Transactions committed twice              | Audit transaction logs for duplicates |
| **Inconsistent state between nodes** | Transactions not fully replicated         | Compare state across replicas |
| **Slow recovery time**              | Large transaction log or missing indices  | Monitor disk I/O and log size |
| **Failed rollback on recovery**       | Corrupted transaction log                 | Run `fsck` (filesystem check) or log reindexing |
| **Network partitions leading to data loss** | Unconfirmed writes in partitioned scenarios | Check consensus logs (e.g., Raft/Paxos) |
| **Timeout errors during recovery**    | Unresolved dependencies in transactions   | Review transaction dependencies in logs |

### **First Steps**
- **Check logs:** Look for `ERROR` or `WARNING` entries related to durability (e.g., `Failed to fsync`, `Log replay timeout`).
- **Reproduce the issue:** Restart the system and observe behavior.
- **Isolate the component:** If using a distributed system (e.g., Kafka, ZooKeeper, etcd), check individual node logs.

---

## **2. Common Issues and Fixes (with Code Examples)**

### **Issue 1: Uncommitted Transactions (Data Loss on Crash)**
**Symptoms:** Data disappears after a crash; logs show `TXN_PENDING` but no `COMMIT` record.

**Root Cause:**
- Transactions were not `fsync()`ed before completion.
- Manual commits were skipped due to premature shutdown.

**Fix:**
Ensure **synchronous writes** (`fsync()`) for critical transactions.
**Example (PostgreSQL):**
```sql
-- Force synchronous writes (adjust `synchronous_commit` setting)
ALTER SYSTEM SET synchronous_commit = 'on';
```
**Example (Java with JDBC):**
```java
try (Connection conn = ds.getConnection()) {
    conn.setAutoCommit(false); // Manual commit control
    // ... perform operations
    conn.commit(); // Ensure fsync happens here
} catch (SQLException e) {
    conn.rollback(); // Revert on failure
}
```

**Debugging:**
- Check `pg_stat_activity` (PostgreSQL) or JDBC transaction logs.
- Verify disk sync status with `fdisk -l /path/to/log`.

---

### **Issue 2: Duplicate Transactions (At-Least-Once Delivery)**
**Symptoms:** Duplicate messages/events processed; logs show `DUPLICATE_ID`.

**Root Cause:**
- Idempotent operations not implemented.
- Transaction retries without deduplication.

**Fix:**
Implement **idempotency keys** or **transaction deduplication**.
**Example (Kafka Producer with Idempotent Writes):**
```java
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "my-transactional-id");
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, "true");
```
**Example (Manual Deduplication):**
```python
from collections import defaultdict

deduped = defaultdict(bool)
for msg in messages:
    if not deduped[msg.id]:
        process(msg)  # Only process once
        deduped[msg.id] = True
```

**Debugging:**
- Search logs for duplicate IDs.
- Enable Kafka consumer group logging:
  ```bash
  kafka-consumer-groups --bootstrap-server localhost:9092 --describe
  ```

---

### **Issue 3: Inconsistent State Between Nodes (Partial Replication)**
**Symptoms:** Two replicas show different data; `is_leader` checks fail inconsistently.

**Root Cause:**
- Replication lag (e.g., node B behind node A).
- Unconfirmed writes during network partitions.

**Fix:**
- **Tune replication settings** (e.g., `replication.lag.time.max.ms` in Kafka).
- **Use strong consistency guarantees** (e.g., `quorum` writes in etcd).

**Example (etcd Strong Consistency):**
```bash
etcdctl put --lease=/my-key --lease-ttl=60 key-value
```
**Example (Kafka Replication Fix):**
```bash
# Increase replication factor to 3
kafka-topics --alter --topic my-topic --partitions 3 --replication-factor 3
```

**Debugging:**
- Check replication status:
  ```bash
  etcdctl endpoint health
  kafka-reassign-partitions --bootstrap-server localhost:9092 --execute -reassignment-json-file reassign.json
  ```

---

### **Issue 4: Slow Recovery (Large Transaction Log)**
**Symptoms:** System takes hours to recover; disk usage spikes.

**Root Cause:**
- Log retention policy too aggressive.
- No compaction in log-based stores (e.g., Kafka, RocksDB).

**Fix:**
- **Prune old logs** (e.g., Kafka log retention):
  ```bash
  kafka-log-dirs.sh --delete-log-dir /tmp/kafka-logs/my-topic-0
  ```
- **Enable compaction** (RocksDB):
  ```properties
  # rocksdb.properties
  rocksdb.compaction.filter.class=org.rocksdb.CompactionFilterImpl
  ```

**Debugging:**
- Monitor log sizes:
  ```bash
  du -sh /var/lib/kafka/logs/*
  ```
- Enable slow query logging (PostgreSQL):
  ```sql
  ALTER SYSTEM SET log_min_duration_statement = '100ms';
  ```

---

### **Issue 5: Corrupted Transaction Log (Rollback Fails)**
**Symptoms:** Recovery fails with `CORRUPT_LOG` errors.

**Root Cause:**
- Incomplete writes during crash.
- No checksum validation.

**Fix:**
- **Enable log checksums** (etcd):
  ```bash
  etcd --enable-v2 --enable-v3 --enable-raft-checksums
  ```
- **Reindex corrupted logs** (PostgreSQL):
  ```bash
  REINDEX DATABASE mydb;
  ```

**Debugging:**
- Run filesystem checks:
  ```bash
  fsck -f /var/lib/postgresql/data
  ```

---

## **3. Debugging Tools and Techniques**

| **Tool**               | **Use Case**                          | **Example Command**                     |
|------------------------|---------------------------------------|------------------------------------------|
| **`fsck` (Filesystem Check)** | Detect corrupted disk blocks         | `fsck /var/lib/kafka/`                   |
| **`strace` (System Call Tracer)** | Debug sync/fsync behavior            | `strace -f -e open,write,fsync java -jar myapp.jar` |
| **`Perf` (Performance Monitoring)** | Identify slow I/O                    | `perf top`                              |
| **`etcdctl`**          | Check etcd cluster health             | `etcdctl endpoint health`                |
| **`kafka-consumer-groups`** | Debug consumer lag                 | `kafka-consumer-groups --describe`       |
| **`pgBadger`**         | PostgreSQL log analysis               | `pgbadger --nocolor mylog.log > report.html` |
| **`GDB`**              | Debug crashes in custom durability code | `gdb ./app core`                          |

**Advanced Technique: Transaction Log Dumping**
For databases like PostgreSQL, dump logs before/after crashes:
```bash
pg_dumpall > pre-crash.sql
# After recovery:
pg_dumpall > post-crash.sql
# Compare with `diff pre-crash.sql post-crash.sql`
```

---

## **4. Prevention Strategies**

### **Design-Time Mitigations**
1. **Use ACID-compliant databases** (PostgreSQL, MySQL InnoDB) for critical data.
2. **Enable WAL (Write-Ahead Logging)** to ensure no data loss.
3. **Implement circuit breakers** for retries to avoid cascading failures.

### **Configuration Best Practices**
| **Setting**                     | **Recommendation**                          |
|----------------------------------|---------------------------------------------|
| `fsync` (PostgreSQL)           | `on` for production                        |
| `sync` (MySQL)                  | `1` for critical tables                    |
| Kafka `log.flush.interval.messages` | `1` (flush on every write)              |
| etcd `quota-backend-bytes`      | Set to disk capacity/2                     |

### **Operational Best Practices**
- **Regular backups:** Use tools like `pg_backup` or `etcdctldump`.
- **Monitor replication lag:** Set up alerts for `kafka-replica-lag-monitor.sh`.
- **Test failover scenarios:** Simulate node crashes with `etcdctl member remove`.

### **Code-Level Safeguards**
```java
// Example: Java with DB Connection Leak Protection
try (Connection conn = ds.getConnection()) {
    conn.setAutoCommit(false);
    // ... operations
    conn.commit();
} catch (SQLException e) {
    log.error("Transaction failed, rolling back", e);
    conn.rollback();
} finally {
    if (conn != null && !conn.isClosed()) {
        conn.close(); // Prevent connection leaks
    }
}
```

---

## **5. Summary Checklist for Durability**
| **Step**               | **Action**                                  |
|------------------------|---------------------------------------------|
| **Validate logs**      | Check for `fsync` failures, duplicates     |
| **Tune sync settings** | Enable `fsync`, adjust `sync` settings      |
| **Monitor replication**| Use `kafka-consumer-groups`, `etcdctl`      |
| **Test failover**      | Simulate crashes with `etcdctl member remove`|
| **Enable checksums**   | Add `etcd --enable-raft-checksums`         |
| **Prune logs**         | Clean up old Kafka/postgres WAL segments    |

---

### **Final Notes**
Durability issues often stem from **configuration oversights** rather than bugs. Focus on:
1. **Synchronous writes** (`fsync`, `sync=1`).
2. **Idempotency** for retries.
3. **Replication health** (quorum, lag alerts).
4. **Log integrity** (checksums, backups).

By following this guide, you can quickly diagnose and resolve durability-related outages while implementing safeguards against recurrence.