**[Pattern] Durability Debugging Reference Guide**

---

### **1. Overview**
Durability debugging is a specialized troubleshooting technique used to diagnose and resolve issues where data persistence fails in distributed systems, databases, or applications. This pattern helps identify root causes of inconsistencies in state, such as lost transactions, corrupted writes, or incomplete replication, by tracing the lifecycle of data from origin to storage.

Key focus areas include:
- **Transaction tracking**: Verifying whether writes reach storage or are lost.
- **Consistency checks**: Validating whether replicas or clusters stay in sync.
- **Recovery verification**: Confirming that failed writes can be restored or replayed.
- **Metadata inspection**: Reviewing logs, timestamps, and WAL (Write-Ahead Log) entries for gaps.

This guide assumes familiarity with distributed systems concepts, such as **CAP theorem**, **ACID properties**, and **idempotency**. It applies to databases (e.g., PostgreSQL, Cassandra), message brokers (e.g., Kafka), and custom applications using durability guarantees.

---

### **2. Key Concepts**
| Concept               | Description                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Durability**        | Guarantee that data persists beyond a single system failure.               |
| **Write-Ahead Log (WAL)** | Sequential log of all write operations before applying them to storage.    |
| **Commit Timestamp**  | Point at which a write is considered durably stored (e.g., `commit_lsn`).  |
| **Replication Lag**    | Delay between primary and replica synchronization.                          |
| **Checkpoint**        | Periodic snapshot of database state for recovery.                           |
| **Idempotency Key**   | Unique identifier to prevent duplicate operations (e.g., `transaction_id`).  |

---

### **3. Schema Reference**
Below are tables of critical components and their properties for durability debugging.

#### **3.1 Log Entry Schema (Database/WAL)**
| Field               | Data Type   | Description                                                                 |
|---------------------|-------------|-----------------------------------------------------------------------------|
| `entry_id`          | `BIGINT`    | Unique identifier for the log entry.                                        |
| `timestamp`         | `TIMESTAMP` | When the write was recorded (milliseconds/nanoseconds precision).           |
| `operation`         | `ENUM`      | `INSERT`, `UPDATE`, `DELETE`, `COMMIT`, `ROLLBACK`.                        |
| `key`               | `VARBINARY` | Primary key or partition key of affected row.                               |
| `value`             | `VARBINARY` | Serialized data (e.g., JSON, Protobuf) or metadata (e.g., `NULL` for `DELETE`). |
| `transaction_id`    | `UUID`      | Correlates entries to a transaction (if applicable).                       |
| `commit_timestamp`  | `TIMESTAMP` | When the transaction was committed to storage (if applicable).             |
| `replica_status`    | `BOOLEAN`   | `TRUE` if replicated to all replicas; `NULL` if pending.                   |
| `error_code`        | `INT`       | `NULL` if successful; error code (e.g., `5` for `IOError`) if failed.       |

#### **3.2 Replication Status Table**
| Field            | Data Type   | Description                                                                 |
|------------------|-------------|-----------------------------------------------------------------------------|
| `replica_id`     | `UUID`      | Identifier for the replica node.                                            |
| `last_applied_lsn`| `BIGINT`    | Highest log sequence number (LSN) applied to this replica.                  |
| `lag_seconds`    | `FLOAT`     | Time (seconds) behind the primary since last sync.                         |
| `status`         | `ENUM`      | `SYNCED`, `LAGGING`, `FAILED`, `RECOVERING`.                                |
| `checkpoint_ts`   | `TIMESTAMP` | Last checkpoint timestamp before recovery.                                  |

#### **3.3 Transaction Summary Table**
| Field               | Data Type   | Description                                                                 |
|---------------------|-------------|-----------------------------------------------------------------------------|
| `tx_id`             | `UUID`      | Unique transaction identifier.                                              |
| `start_time`        | `TIMESTAMP` | When the transaction began.                                                 |
| `end_time`          | `TIMESTAMP` | When the transaction completed (`NULL` if open).                           |
| `status`            | `ENUM`      | `PENDING`, `COMMITTED`, `ROLLED_BACK`, `TIMEOUT`.                            |
| `affected_rows`     | `INT`       | Number of rows modified.                                                    |
| `durable_at`        | `TIMESTAMP` | When writes were confirmed as durable (derived from `commit_timestamp`).    |
| `retry_count`       | `INT`       | Number of retries due to failures.                                          |

---

### **4. Query Examples**
Use these queries to inspect durability-related issues in a PostgreSQL-inspired schema.
*(Adjust syntax for your database; examples use `pg_catalog` or `durability_debug` schema.)*

#### **4.1 Find Unacknowledged Writes (Pending Durability)**
```sql
-- Log entries not yet replicated (replica_status = NULL)
SELECT
  entry_id,
  operation,
  key,
  timestamp,
  transaction_id,
  commit_timestamp
FROM
  durability_debug.log_entries
WHERE
  replica_status IS NULL
  AND commit_timestamp IS NOT NULL
ORDER BY
  timestamp DESC;
```

#### **4.2 Detect Stale Replicas (Replication Lag)**
```sql
-- Replicas lagging behind primary by >5 seconds
SELECT
  replica_id,
  last_applied_lsn,
  lag_seconds,
  status,
  (EXTRACT(EPOCH FROM (NOW() - last_sync_time))) AS current_lag
FROM
  durability_debug.replica_status
WHERE
  lag_seconds > 5
  OR status = 'LAGGING';
```

#### **4.3 Identify Failed Transactions**
```sql
-- Transactions that rolled back or timed out
SELECT
  tx_id,
  start_time,
  end_time,
  status,
  retry_count
FROM
  durability_debug.transaction_summary
WHERE
  status IN ('ROLLED_BACK', 'TIMEOUT')
ORDER BY
  start_time DESC;
```

#### **4.4 Cross-Reference WAL and Transactions**
```sql
-- Missing commit timestamps (potential durability loss)
SELECT
  t.tx_id,
  COUNT(l.entry_id) AS wals_without_commit
FROM
  durability_debug.transaction_summary t
LEFT JOIN
  durability_debug.log_entries l
    ON t.tx_id = l.transaction_id
    AND l.commit_timestamp IS NULL
WHERE
  t.status = 'COMMITTED'
GROUP BY
  t.tx_id
HAVING
  COUNT(l.entry_id) > 0;
```

#### **4.5 Checkpoint Recovery Verification**
```sql
-- Gaps between checkpoints (risk of data loss on crash)
SELECT
  checkpoint_id,
  checkpoint_ts,
  LEAD(checkpoint_ts) OVER (ORDER BY checkpoint_ts) AS next_checkpoint_ts,
  EXTRACT(EPOCH FROM (LEAD(checkpoint_ts) OVER (ORDER BY checkpoint_ts) - checkpoint_ts)) AS gap_seconds
FROM
  durability_debug.checkpoints
ORDER BY
  checkpoint_ts;
```

---

### **5. Workflow for Durability Debugging**
Follow this 5-step process to diagnose durability issues:

1. **Reproduce the Issue**
   - Trigger the error (e.g., crash the primary node, simulate network partitions).
   - Verify symptoms (e.g., missing data, replication lag).

2. **Inspect Logs**
   - Query `log_entries` for unacknowledged writes (`replica_status IS NULL`).
   - Check for WAL corruption or truncated logs.

3. **Analyze Replication**
   - Run the *Detect Stale Replicas* query. Investigate replicas with `lag_seconds > 0`.
   - Verify metadata (e.g., `last_applied_lsn` gaps).

4. **Audit Transactions**
   - Query *Failed Transactions* for `ROLLED_BACK` or `TIMEOUT` entries.
   - Cross-check with `log_entries` for missing commits.

5. **Validate Recovery**
   - Restore from the last checkpoint and verify data consistency.
   - Use `checkpoint_recovery_gap` query to ensure no data loss.

---

### **6. Common Pitfalls & Mitigations**
| Pitfall                          | Cause                                  | Mitigation                                                                 |
|-----------------------------------|----------------------------------------|----------------------------------------------------------------------------|
| **False Positives in Durability** | Idempotent writes appear lost.        | Use `transaction_id` to dedupe.                                           |
| **Replication Lag Misattribution**| Lag due to network, not storage.      | Filter by `status = 'FAILED'` in replication logs.                         |
| **Checkpoint Overlap**           | Incomplete checkpoint on crash.       | Increase checkpoint frequency or use WAL archiving.                       |
| **WAL Corruption**                | Disk errors during write.             | Enable WAL checksums and validate logs post-recovery.                      |
| **Clock Synchronization**        | Time skew between nodes.              | Use NTP or distributed clocks (e.g., Raft consensus).                     |

---

### **7. Related Patterns**
| Pattern Name               | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| **Retry with Exponential Backoff** | Resend failed writes with increasing delays to avoid thundering herd.     |
| **Idempotent Operations**   | Design writes to be safely repeated (e.g., using `transaction_id`).         |
| **Leader Election (Paxos/Raft)** | Ensure a single durable leader for write consensus in clusters.              |
| **Data Sharding**          | Distribute writes to reduce single-point failure impact.                    |
| **Checksum Validation**    | Verify data integrity post-recovery (e.g., CRC32 of stored rows).           |

---

### **8. Tools & Extensions**
| Tool/Extension       | Purpose                                                                 |
|----------------------|-------------------------------------------------------------------------|
| **pgbadger**         | Analyze PostgreSQL logs for durability anomalies.                      |
| **Kafka Consumer Groups Offset** | Debug message broker durability via `CONSUMER_GROUPS` table.           |
| **Prometheus Alerts** | Monitor `replication_lag` and `txn_failures` metrics.                  |
| **Custom WAL Inspection** | Write scripts to scan `pg_wal` for gaps (e.g., in Python with `psycopg2`). |

---
**Note:** Adjust schema names and queries to match your database’s specific APIs (e.g., for Cassandra, use `system.log` tables). For custom applications, log durability events to a dedicated table with the same fields as shown.