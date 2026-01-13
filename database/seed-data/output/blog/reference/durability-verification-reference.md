# **[Pattern] Durability Verification Reference Guide**

---
## **1. Overview**
**Durability Verification** is a pattern used to ensure that written data remains intact and accessible over time, particularly in distributed systems where nodes, storage, or network failures may occur. This pattern validates that persistent storage (e.g., databases, logs, or files) correctly records and preserves data, mitigating risks like silent corruption or data loss. By combining **write-ahead logging (WAL)**, **checksum validation**, and **periodic integrity checks**, systems can detect and recover from inconsistencies before they impact downstream operations.

Key use cases include:
- **Financial transactions** (preventing loss of trade records).
- **Medical records** (ensuring patient data integrity).
- **IoT device telemetry** (verifying sensor data is not altered).
- **Distributed databases** (cross-node consistency checks).

This guide outlines the **schema, implementation strategies, query examples**, and related patterns to achieve robust durability verification.

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                     | **Example (Pseudocode)**                                      |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| **Write-Ahead Log (WAL)**   | Sequential log of all write operations before database updates.                                    | `append(WAL, {op: "INSERT", table: "orders", data: {id: 1}})` |
| **Checksum Table**          | Stores computed hashes (e.g., SHA-256) of critical data for later verification.                  | `checksums[<table>][<row_id>] = "d7a8f..."`                  |
| **Verification Job**        | Periodic task to cross-validate WAL entries with checksums and physical storage.                 | `verifyDurability("orders")`                                  |
| **Recovery Trigger**        | Alerts or automates recovery when checksum mismatches are detected.                               | `if (mismatchFound()) triggerRecovery()`                      |
| **Metadata Log**            | Tracks timestamps, operation IDs, and success/failure status of writes.                          | `{id: "txn-123", status: "completed", timestamp: "2024-01-01"}`|

---
### **Data Flow**
1. **Write Operation**:
   - Data → **WAL** (logged before storage).
   - **Checksum** computed → stored in checksum table.
   - Data persisted to primary storage.
2. **Verification**:
   - Scheduled job reads **WAL** and recomputes checksums.
   - Compares with stored checksums; logs discrepancies.
3. **Recovery** (if needed):
   - Rolls back failed writes or reprocesses logs.

---

## **3. Implementation Details**

### **3.1. Key Techniques**
| **Technique**               | **Purpose**                                                                                     | **Example Tools/Libraries**                                  |
|-----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| **Write-Ahead Logging (WAL)** | Ensures durability by forcing writes to log before committing to storage.                     | PostgreSQL WAL, Kafka Logs                                  |
| **Periodic Integrity Checks** | Automated validation of stored data against checksums.                                        | `pg_checksums` (PostgreSQL), custom scripts (Python/Go)    |
| **Atomic Transactions**      | Groups related writes as a single unit to prevent partial failures.                            | JDBC Transactions, MongoDB Transactions                     |
| **Redundant Replication**   | Copies data across nodes to survive local failures.                                            | Cassandra, ZooKeeper                                         |
| **Time-Based Verification** | Runs checks at predictable intervals (e.g., hourly/daily).                                      | Cron jobs, Kubernetes CronJobs                              |

### **3.2. Trade-offs**
| **Consideration**               | **Pros**                          | **Cons**                                  | **Mitigation**                          |
|----------------------------------|-----------------------------------|-------------------------------------------|-----------------------------------------|
| **Performance Overhead**         | Slower writes due to logging.     | Higher latency.                          | Batch logging, async verification.      |
| **Storage Cost**                 | Extra space for WAL/checksums.    | Increased disk usage.                     | Compress logs; prune old entries.       |
| **Complexity**                   | Harder to debug.                  | More moving parts.                        | Automated monitoring; clear logging.    |

---

## **4. Query Examples**

### **4.1. Validate Checksums (SQL)**
```sql
-- Compare checksums for a table
SELECT
    t.id,
    h hash_value,
    CASE
        WHEN h.hash_value != sha256(to_jsonb(t)) THEN 'FAIL'
        ELSE 'PASS'
    END AS integrity_check
FROM
    transactions t
JOIN
    checksums h ON t.id = h.object_id
WHERE
    h.table_name = 'transactions';
```

### **4.2. Reconstruct Data from WAL (Pseudocode)**
```python
def recover_from_wal(log_path, target_table):
    # Replay log entries to rebuild the table
    for entry in read_wal(log_path):
        if entry['table'] == target_table:
            insert_into_target_table(entry['data'])
```

### **4.3. Schedule Verification (Bash)**
```bash
#!/bin/bash
# Run hourly durability check
0 * * * * /path/to/verify-durability.sh >> /var/log/durability.log
```

### **4.4. Detect Corruption (Python)**
```python
import hashlib

def verify_table_integrity(table_name):
    stored_checksums = get_checksums(table_name)
    for row_id, row_data in get_table_rows(table_name):
        computed_hash = hashlib.sha256(str(row_data).encode()).hexdigest()
        if computed_hash != stored_checksums[row_id]:
            print(f"Corruption detected in row {row_id}!")
            trigger_recovery()
```

---
## **5. Related Patterns**

| **Pattern**                  | **Relationship**                                                                                     | **When to Use**                                  |
|------------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Idempotent Operations**    | Works with durability verification to ensure repeated writes don’t corrupt data.                  | APIs, microservices.                              |
| **Circuit Breaker**          | Temporarily halts writes if verification failures exceed a threshold.                                   | High-availability systems.                       |
| **Snapshot Isolation**       | Provides consistent reads during durability checks by locking rows.                                   | OLTP databases.                                  |
| **Event Sourcing**           | Stores state changes as immutable logs, simplifying verification.                                    | CQRS architectures.                              |
| **Retries with Backoff**     | Handles transient failures during recovery.                                                        | Fault-tolerant systems.                          |

---
## **6. Best Practices**
1. **Log Everything**: Capture metadata (timestamps, users, IP addresses) for auditing.
2. **Automate Verification**: Use orchestration tools (Kubernetes, Airflow) to schedule checks.
3. **Monitor Anomalies**: Set up alerts for failed checks (e.g., Prometheus + Alertmanager).
4. **Test Recovery**: Simulate failures (e.g., disk corruption) to validate recovery workflows.
5. **Minimize Locking**: Use optimistic concurrency control to avoid deadlocks during checks.

---
## **7. Example Architecture**
```
┌───────────────────────────────────────────────────────────────────────────────┐
│                            Durability Verification System                     │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────┤
│   Application   │     WAL         │ Checksum DB     │   Primary DB    │  Job   │
│   Layer         │ (Append-Only)  │                 │                 │ Scheduler│
└────────┬────────┴────────┬────────┴────────┬────────┴────────┬────────┴────────┘
         │                │                 │                 │              │
         ▼                ▼                 ▼                 ▼              ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│               Verification Workflow                                      │
│                                                                           │
│  1. App writes → WAL logged → DB updated → checksum computed → stored.  │
│  2. Scheduled job reads WAL → recomputes checksums → compares.           │
│  3. On mismatch: triggers recovery (e.g., replay WAL).                    │
└───────────────────────────────────────────────────────────────────────────────┘
```

---
## **8. References**
- [PostgreSQL Write-Ahead Logging](https://www.postgresql.org/docs/current/wal-intro.html)
- [Cassandra Checksum Validation](https://cassandra.apache.org/doc/latest/architecture/checksums.html)
- [SRE Book: Reliability](https://sre.google/sre-book/table-of-contents/#reliability)

---
**Note**: Adjust schemas/tools based on your tech stack (e.g., replace SQL with NoSQL queries for MongoDB/Cassandra). For cloud-native environments, leverage services like **AWS CloudTrail** or **GCP Audit Logs** for durability tracking.