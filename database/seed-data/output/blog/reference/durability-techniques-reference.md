# **[Pattern] Durability Techniques – Reference Guide**

---

## **1. Overview**
Ensure system resilience by implementing **durability techniques** to guarantee data persistence, fault tolerance, and recovery from failures. This pattern addresses scenarios where data integrity must survive crashes, network partitions, or hardware failures. Common durability strategies include **write-ahead logging (WAL), checkpointing, replication, and transactional integrity mechanisms**. This guide provides key concepts, implementation details, schema references, and query patterns for building robust systems.

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                 | **Use Case**                                                                 |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Write-Ahead Logging (WAL)** | Logs operations before applying them to persistent storage to ensure atomicity. | Transactional databases, distributed systems requiring crash recovery.       |
| **Checkpointing**      | Periodically saving the current state of the system to disk for recovery.       | Long-running processes where unlogged changes must survive crashes.         |
| **Replication**        | Duplicating data across multiple nodes to prevent data loss.                  | High-availability systems, backup redundancy.                              |
| **ACID Transactions**  | Ensures **Atomicity**, **Consistency**, **Isolation**, and **Durability**.     | Financial systems, inventory management, where data integrity is critical. |
| **Immutable Logs**     | Appending-only logs that cannot be altered after creation.                     | Audit trails, version control, and replayable execution.                    |
| **Force Sync (fsync)** | Explicitly syncing data to disk to prevent buffer caching.                    | High-priority systems where durability is mandatory (e.g., blockchain).     |

---

## **3. Implementation Details**

### **3.1 Write-Ahead Logging (WAL)**
- **Mechanism**: Before modifying persistent storage, append operations to a log.
- **Benefits**: Recovers lost changes post-crash, enforces atomicity.
- **Implementation**:
  - Use a file-based log (e.g., SQLite, PostgreSQL) or append-only database (e.g., Kafka, Cassandra).
  - Example (pseudocode):
    ```python
    def insert_log(entry):
        open("wal.log", "a").write(f"{entry}\n")
        fsync("wal.log")  # Force sync to disk
    ```

### **3.2 Checkpointing**
- **Mechanism**: Periodically snapshot the system state to disk.
- **Benefits**: Reduces recovery time from WAL replay.
- **Implementation**:
  - Schedule snapshots (e.g., every 5 minutes).
  - Use tools like `fsync()` or database-specific checkpoints (e.g., MySQL `FLUSH TABLES WITH READ LOCK`).
  - Example (Linux cron):
    ```bash
    0 * * * * /bin/sh -c "sync && fsync /path/to/data"
    ```

### **3.3 Replication**
- **Mechanism**: Synchronize data across multiple nodes.
- **Types**:
  - **Synchronous**: Blocks writes until all replicas acknowledge (high durability, low throughput).
  - **Asynchronous**: Accepts writes immediately (higher throughput, risk of data loss).
- **Tools**: PostgreSQL streaming replication, Kubernetes Operators, DynamoDB Global Tables.
- **Example (PostgreSQL):**
  ```sql
  SELECT pg_start_backup('full_backup', true);
  -- Replicate to standby node
  SELECT pg_stop_backup();
  ```

### **3.4 ACID Transactions**
- **Atomicity**: All-or-nothing execution (e.g., bank transfers).
- **Consistency**: Maintains constraints (e.g., `NOT NULL`, `FOREIGN KEY`).
- **Isolation**: Prevents dirty reads (e.g., MVCC in PostgreSQL).
- **Durability**: Writes survive crashes (e.g., `COMMIT` + WAL).
- **Query Example (SQL):**
  ```sql
  BEGIN TRANSACTION;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
  COMMIT;  -- Ensures both updates persist or fail together
  ```

### **3.5 Immutable Logs**
- **Use Case**: Tamper-proof audit trails (e.g., blockchain, distributed tracing).
- **Implementation**:
  - Append-only structure (e.g., LevelDB, RocksDB).
  - Cryptographic hashing for integrity (e.g., `SHA-256`).
  - Example (Python):
    ```python
    import hashlib
    log = []
    def append(entry):
        entry_hash = hashlib.sha256(entry.encode()).hexdigest()
        log.append((entry, entry_hash))
        with open("immutable.log", "ab") as f:
            f.write(entry.encode() + b"\n")
    ```

### **3.6 Force Sync (`fsync`)**
- **When to Use**: Critical operations requiring immediate disk persistence.
- **Example (C):**
  ```c
  FILE *log = fopen("critical.log", "a");
  fprintf(log, "Operation X\n");
  fflush(log);  // Sync buffer
  fsync(fileno(log));  // Force to disk
  fclose(log);
  ```

---

## **4. Schema Reference**
| **Pattern**            | **Data Structure**       | **Storage Layer**          | **Recovery Method**               |
|------------------------|--------------------------|----------------------------|------------------------------------|
| Write-Ahead Logging    | Append-only log file      | File system (e.g., `/var/log/wal`) | Replay log on reboot.              |
| Checkpointing          | Periodic snapshot file    | Disk partition (e.g., `/data/backup`) | Restore snapshot after crash.      |
| Replication (Sync)     | Duplicate database tables | Primary + replica nodes   | Promote replica on primary failure.|
| ACID Transactions      | Transaction log (WAL)     | Database engine (e.g., PostgreSQL) | Reapply WAL entries on recovery.   |
| Immutable Log          | Sequential key-value pairs | RocksDB/LevelDB            | Reconstruct state from log.        |

---

## **5. Query Examples**

### **5.1 Recovering from a Crash Using WAL**
```sql
-- PostgreSQL: Reconstruct database using WAL
pg_restore -U postgres --clean --dbname mydb /path/to/wal_archive
```

### **5.2 Checkpoint Recovery (Bash)**
```bash
# After crash, restore from checkpoint
cp /data/checkpoint-20230101 /data/current
```

### **5.3 ACID Transaction Rollback**
```sql
-- If a transaction fails, roll back:
BEGIN TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
-- Assume failure here (e.g., insufficient funds)
ROLLBACK;  -- Reverts all changes
```

### **5.4 Immutable Log Verification**
```bash
# Verify log integrity:
sha256sum -c expected_hashes.txt < immutable.log
```

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Circuit Breaker]**     | Prevent cascading failures in distributed systems.                           | High-latency APIs, microservices.               |
| **[Retry with Backoff]**  | Resilient retry logic for transient failures.                               | External API calls, network partitions.          |
| **[Idempotent Operations]**| Ensure repeated executes produce the same result.                           | Payment processing, order confirmations.        |
| **[Event Sourcing]**      | Store state changes as an append-only event log.                            | Auditing, time-travel debugging.                 |
| **[Saga Pattern]**        | Manage long-running transactions via choreography or orchestration.         | Distributed workflows (e.g., order fulfillment). |

---

## **7. Best Practices**
1. **Optimize Log Size**: Balance durability with performance (e.g., segment WAL files).
2. **Test Failures**: Simulate crashes/hardware failures in CI (e.g., `kill -9` production process).
3. **Monitor Replication Lag**: Use tools like `pg_isready` (PostgreSQL) or CloudWatch (AWS).
4. **Minimize Lock Contention**: Use optimistic concurrency control for scalability.
5. **Document Recovery Steps**: Maintain runbooks for disaster recovery (e.g., `RECOVERY.md`).

---
**Note**: Durability techniques trade off performance for reliability. Tailor choices based on latency vs. correctness requirements. For critical systems, combine multiple strategies (e.g., WAL + replication).