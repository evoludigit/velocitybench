# **[Pattern] Durability Maintenance Reference Guide**

---

## **Overview**
The **Durability Maintenance** pattern ensures that data or system state remains consistent and recoverable over time, even in the event of failures, crashes, or partial outages. This pattern is critical for systems requiring **ACID compliance, fault tolerance, or long-term reliability**, such as financial transaction processing, distributed databases, or stateful microservices.

The pattern focuses on:
- **Persisting state reliably** (e.g., using write-ahead logs, transactions).
- **Handling failures gracefully** (e.g., retries, recovery procedures).
- **Ensuring eventual consistency** (if applicable) when partial failures occur.

Unlike patterns like **Circuit Breaker**, which addresses transient failures, **Durability Maintenance** specifically targets **permanent data integrity**.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Write-Ahead Log (WAL)** | A sequence of records detailing all changes before they are applied to primary storage.          |
| **Checkpointing**         | Periodically saving a snapshot of the system state to disk to reduce recovery time.                |
| **Transaction Logs**      | Ordered records of transactions used for recovery and rollback in distributed systems.              |
| **Atomic Commit**         | Ensuring all parts of a transaction succeed or fail together (e.g., 2PC, saga pattern variants).   |
| **Recovery Procedures**   | Scripts or logic to restore system state from logs/checkpoints after a crash.                       |

---

## **Schema Reference**
Below are common components used in **Durability Maintenance**:

| **Component**            | **Description**                                                                                     | **Example Fields**                                                                 |
|--------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Write-Ahead Log Entry**| A record of a single operation before persistence.                                                  | `{ timestamp, operation_id, data, status (pending/committed/aborted) }`             |
| **Checkpoint Record**    | A snapshot of system state at a given time.                                                         | `{ timestamp, state_hash, metadata, recovery_script_reference }`                     |
| **Transaction Log**      | Ordered list of committed transactions for replay during recovery.                                  | `[ { tx_id, timestamp, operations, commit_status } ]`                               |
| **Recovery Script**      | Logic to restore state from logs/checkpoints (e.g., SQL scripts, custom logic).                    | `function recover(state_hash, log_entries) { ... }`                                |

---

## **Implementation Details**
### **1. Write-Ahead Logging (WAL)**
- **Purpose**: Guarantee durability by recording operations before applying them.
- **Implementation**:
  - Append each operation to a log file **before** modifying primary storage.
  - Use **fsync()** (Linux) or **FlushFileBuffers()** (Windows) to ensure log persistence.
- **Example (Pseudocode)**:
  ```python
  def write_to_wal(operation):
      log_entry = {"timestamp": get_current_time(), "data": operation}
      with open("wal_log.bin", "ab") as f:
          f.write(pickle.dumps(log_entry))
          f.flush()  # Force OS to write to disk
  ```

### **2. Checkpointing**
- **Purpose**: Reduce recovery time by saving snapshots periodically.
- **Implementation**:
  - Trigger checkpoints on:
    - Fixed intervals (e.g., every 5 minutes).
    - Before major operations (e.g., database restarts).
  - Store checkpoints in a separate file or database.
- **Example (Bash Script)**:
  ```bash
  # Checkpoint script
  CHECKPOINT_DIR="/var/backups/checkpoints"
  timestamp=$(date +%Y%m%d_%H%M%S)
  cp -f /var/data/system_state.json "$CHECKPOINT_DIR/state_$timestamp.json"
  ```

### **3. Transaction Logs (Distributed Systems)**
- **Purpose**: Ensure consistency across nodes in a distributed system.
- **Implementation**:
  - Use **log-based replication** (e.g., Kafka, etcd).
  - Implement **2-phase commit (2PC)** for strong consistency:
    1. **Prepare Phase**: Coordinate with all nodes.
    2. **Commit Phase**: Apply changes if all nodes agree.
- **Example (2PC Flow)**:
  ```
  Node A → [PREPARE] → Node B, Node C
  Node B, C → [ACK/NACK]
  If all ACK:
    Node A → [COMMIT] → Node B, C
  ```

### **4. Recovery Procedures**
- **Purpose**: Restore state after a crash.
- **Implementation**:
  - Replay the WAL from the last checkpoint.
  - Skip logged operations already applied (idempotency).
- **Example (Python Recovery Function)**:
  ```python
  def recover_system():
      last_checkpoint = get_latest_checkpoint()
      for entry in get_unapplied_log_entries(last_checkpoint.timestamp):
          apply_operation(entry["data"])
  ```

---

## **Query Examples**
### **1. Querying Unapplied Log Entries (SQL)**
```sql
SELECT *
FROM write_audit_log
WHERE timestamp > '2024-01-01 00:00:00'
  AND status = 'pending';
```

### **2. Finding the Latest Checkpoint (Shell)**
```bash
ls -t /var/backups/checkpoints/ | head -1  # Latest file
```

### **3. Replaying a Transaction Log (Python)**
```python
def replay_txn(txn_id):
    txn = get_transaction_log(txn_id)
    for op in txn["operations"]:
        if not is_applied(op):
            apply_operation(op)
            mark_applied(op)
```

---

## **Failure Scenarios & Mitigations**
| **Scenario**               | **Risk**                          | **Mitigation**                                                                 |
|-----------------------------|-----------------------------------|---------------------------------------------------------------------------------|
| Disk crash during WAL write | Lost uncommitted data             | Use **fsync** to ensure log persistence before proceeding.                       |
| Checkpoint corruption       | Incomplete recovery               | Store checkpoints in **RAID 1** or distributed storage (e.g., S3).             |
| Network partition (distributed) | Split-brain                   | Implement **quorum-based commits** (e.g., Raft consensus).                     |

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Combine**                                                                 |
|---------------------------|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Circuit Breaker**       | Complements durability by avoiding cascading failures during recovery.           | Use after failed durability checks (e.g., retry WAL writes with backoff).           |
| **Saga Pattern**          | Handles distributed transactions with eventual consistency.                       | Use for microservices where full ACID is impractical.                              |
| **Idempotency**           | Ensures repeated operations are safe (critical for recovery replay).             | Always pair with durability patterns to prevent duplicate side effects.            |
| **Leader Election**       | Manages primary nodes in distributed durability (e.g., ZooKeeper).              | Required for consensus-based checkpoints (e.g., Raft).                            |
| **Retry with Exponential Backoff** | Helps recover from transient failures during durability operations.       | Use for WAL writes or checkpoint replication over unreliable networks.              |

---

## **Best Practices**
1. **Atomicity**: Ensure WAL entries and primary storage updates are **all-or-nothing**.
2. **Ordering**: Log entries must be **append-only** and processed sequentially.
3. **Redundancy**: Replicate critical logs/checkpoints across nodes/regions.
4. **Monitoring**: Track:
   - Log replay time.
   - Checkpoint success/failure rates.
   - WAL disk space usage.
5. **Testing**: Simulate crashes (e.g., kill processes mid-WAL write) to verify recovery.

---
## **Anti-Patterns**
| **Anti-Pattern**               | **Why It Fails**                                                                 |
|---------------------------------|-----------------------------------------------------------------------------------|
| **Sync Writes Without fsync**    | OS buffers may lose data on crash.                                               |
| **No Checkpoints**              | Recovery time scales with log size.                                               |
| **Skipping Log Entries**        | Leads to silent data loss during replay.                                          |
| **Single Point of Failure**     | No redundancy for logs/checkpoints.                                              |

---
## **Tools & Libraries**
| **Tool/Library**       | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **PostgreSQL WAL**     | Native transaction logging and recovery.                                   |
| **etcd**               | Distributed key-value store with strong consistency.                        |
| **Apache Kafka**       | Log-based event streaming for durability.                                  |
| **SQL Server TLOG**    | Transaction log for SQL Server recovery.                                   |
| **CrashPlan**          | Automated checkpointing for critical data.                                 |

---
**Next Steps**:
- [ ] Implement WAL with `fsync` for critical operations.
- [ ] Schedule checkpoints (e.g., cron job).
- [ ] Test recovery procedures with simulated crashes.