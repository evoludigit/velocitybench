---
**[Pattern] Durability Troubleshooting – Reference Guide**
*Ensure system resilience by diagnosing and resolving persistent data loss or corruption during failures.*

---

### **Overview**
Durability issues in distributed systems often manifest as **inconsistent transactions, lost writes, or degraded performance under load**. This reference guide outlines systematic troubleshooting for **data persistence failures**, focusing on common root causes (e.g., disk I/O bottlenecks, network partitioning, or transaction log corruption) and mitigations. It applies to databases (e.g., PostgreSQL, Cassandra), event-driven architectures (Kafka), or stateful services (e.g., Redis, DynamoDB).

Key pillars addressed:
- **Persistence layers** (storage engines, WAL journals).
- **Fault tolerance mechanisms** (replication, checkpoints).
- **Recovery workflows** (post-failure data consistency).

---

### **Schema Reference**
| **Category**               | **Metadata**               | **Diagnostic Flags**                          | **Remedies**                                                                 |
|----------------------------|----------------------------|-----------------------------------------------|------------------------------------------------------------------------------|
| **Storage Layer**          | Disk health (SMART logs)   | High latency, uncorrectable errors (`read_error_count`) | Replace or rebalance disks; adjust `sync` behavior (e.g., `fsync` intervals). |
|                            | Filesystem type            | `ext4`/`xfs` corruption flags (check `dmesg`) | Run `fsck`, remount with `errors=remount-ro`.                              |
|                            | WAL/Log retention          | Truncated logs (`postgresql -V`), missing segments | Increase `log_archive_mode`; monitor `archiver_processes`.                 |
| **Replication Sync**       | Lag in followers           | `pg_stat_replication.lag`, `replica_lag`      | Scale read replicas; adjust `async_commit`/`synchronous_commit`.            |
|                            | Network partitions         | `replication_slave_delay`, `ConnectionReset`   | Use `max_replication_slots`; test with `ping`/`mtr`.                        |
| **Transaction Handling**   | Aborted transactions       | `pg_stat_activity.state = 'idle in transaction'`| Check `pg_stat_activity`; analyze `pg_locks` for deadlocks.                 |
|                            | Durability guarantees      | `pgsql` `effective_cache_size` vs. heap size | Tune `shared_buffers`, enable `checksum` (`postgresql.conf`).               |
| **Client-Side Checks**     | Client-side retries        | Exponential backoff delays (`Retry-After`)   | Configure `max_retries`, validate `timeout` settings.                       |

---

### **Query Examples**
#### **1. Disk Health (Linux)**
```bash
# Check SMART attributes (postgres user)
sudo smartctl -a /dev/sdX | grep "Reallocated_Sector_Ct"
```
- **Threshold**: Values < 100 indicate imminent failure.

#### **2. PostgreSQL Log Integrity**
```sql
-- Verify WAL archiving status
SELECT
    pg_current_wal_lsn(),
    pg_wal_lsn_diff(pg_current_wal_lsn(), pg_last_wal_receive_lsn());
```
- **Expected**: `0` (full sync); non-zero indicates lag.

#### **3. Cassandra Data Corruption**
```bash
# Check node consistency
nodetool repair --full
nodetool status
```
- **Output Flags**:
  - `UN` (Unreachable) → Network issue.
  - `DG` (Down) → Node crash.

#### **4. Kafka Consumer Lag**
```bash
# Monitor partition lag
kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>
```
- **Action**: Scale brokers or increase `fetch.max.bytes`.

---

### **Implementation Details**
#### **Root Causes & Mitigations**
| **Failure Mode**               | **Root Cause**                          | **Diagnostic Steps**                                                                 | **Fix**                                                                                     |
|---------------------------------|-----------------------------------------|--------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **Transaction Fails at Commit** | Disk `fsync` timeout                    | `postgresql.log` shows `ERROR:  write ahead log out of space`                        | Increase `checkpoint_segments`; adjust `checkpoint_completion_target`.                    |
| **Data Loss on Crash**          | WAL truncation                          | `pg_xlogdump` shows missing segments; `pg_controldata` reports inconsistent LSN.      | Restore from backup; replay WAL from latest checkpoint.                                    |
| **Replication Lag**             | Network bandwidth throttling            | `pg_stat_replication` shows `send_lag`.                                               | Use `pg_bouncer` for connection pooling; monitor `netstat -s`.                            |
| **Corrupt Pages**               | Filesystem corruption                   | `pg_checksums` reports mismatches.                                                    | Rebuild tables with `REINDEX`; repair filesystem.                                         |
| **Serializable Isolation Viols.**| Long-running transactions               | `pg_stat_activity` shows `serializable` locks.                                       | Break transactions; implement application retries with `REPEATABLE READ`.                  |

---
#### **Preventive Checks**
1. **Storage**:
   - Monitor `iostat` for disk saturation (`iostat -x 1`).
   - Set `postgresql.conf`:
     ```ini
     sync_method = fdatasync  # Faster than fsync (for safe but faster writes).
     wal_sync_method = fsync  # Critical for durability.
     ```
2. **Network**:
   - Use `etcd` or `Consul` for cluster health checks.
   - Configure `ressource_group_replication` in MySQL for near-zero data loss.
3. **Client-Side**:
   - Implement **idempotent writes** (e.g., UUIDs for Kafka producers).
   - Enable **transaction logging** (e.g., `pgAudit` for PostgreSQL).

---
### **Recovery Procedures**
#### **Post-Crash Workflow**
1. **Verify Consistency**:
   ```sql
   -- Check for orphaned transactions
   SELECT pid, now() - xact_start FROM pg_stat_activity WHERE state = 'idle in transaction';
   ```
2. **Restore from Backup**:
   ```bash
   pg_restore --clean --if-exists -d <dbname> <backup>.dump
   ```
3. **Replay Logs** (if no full backup):
   ```bash
   pg_standby -D /path/to/data -R /path/to/recovery.conf -c 'max_recovery_time = 1h'
   ```

#### **Cassandra Example**
```bash
# Start nodetool repair in interactive mode
nodetool repair --mode=LAZY
nodetool status  # Verify repaired nodes.
```

---

### **Related Patterns**
1. **[Idempotent Operations](https://example.com/idempotent-ops)**
   - Ensures retries don’t cause duplicates.
2. **[Circuit Breakers](https://example.com/circuit-breaker)**
   - Limits cascading failures during storage outages.
3. **[Chaos Engineering for Durability](https://example.com/chaos-durability)**
   - Simulate disk failures to test recovery.
4. **[Multi-Region Replication](https://example.com/multi-region-rep)**
   - Mitigate regional outages (e.g., DynamoDB Global Tables).

---
### **Key Terms**
| **Term**               | **Definition**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **WAL (Write-Ahead Log)** | Sequential log of all data changes for crash recovery.                          |
| **Checkpoint**         | Snapshot of DB state; WAL truncates after checkpoint completion.                |
| **Serialization Gap**  | Time between when a transaction commits and is visible to others.               |
| **Durability Guarantee** | Promise that committed data survives crashes (e.g., `fsync` in PostgreSQL).    |

---
### **Further Reading**
- [PostgreSQL Durability Tuning](https://www.postgresql.org/docs/current/runtime-config-wal.html)
- [Cassandra Repair Mechanisms](https://cassandra.apache.org/doc/latest/operations/repair.html)
- [Kafka’s Durability Model](https://kafka.apache.org/documentation/#durability)