# **[Anti-Pattern] Durability Anti-Patterns: Reference Guide**

---

## **Overview**
Durability anti-patterns arise when systems incorrectly handle data persistence, leading to accidental data loss, corruption, or inconsistency. While *durability* ensures data survives failures (e.g., crashes, network outages, or hardware failures), these patterns often result from misconfigurations, lack of redundancy, or naive assumptions about persistence. Common anti-patterns include **improper transaction handling**, **ignoring checkpointing**, **over-reliance on volatile storage**, and **lack of validation before writes**. Addressing these pitfalls requires strict adherence to well-defined durability guarantees and robust error handling mechanisms.

---

## **Schema Reference**
Below are the key anti-patterns with their root causes, symptoms, and mitigation strategies.

| **Anti-Pattern**               | **Root Cause**                                                                 | **Symptoms**                                                                 | **Mitigation**                                                                                     |
|---------------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **No Transaction Management**   | Missing atomicity in write operations; commits/aprolls ignored.               | Data inconsistencies (partial writes, orphaned rows, race conditions).      | Use ACID transactions with explicit `commit()`/`rollback()` calls.                               |
| **Volatile Storage Dependency** | Writing to RAM disks, in-memory DBs, or temporary files without backup.         | Data loss on system reboot or power failure.                                  | Persist to durable storage (e.g., disk) with sync I/O (`O_SYNC` or `fsync`).                      |
| **Unbounded Retries Without Backoff** | Infinite retries on transient failures (e.g., network timeouts).              | Network congestion, cascading failures, or resource exhaustion.             | Implement exponential backoff + retry limits (e.g., `3 tries with 5s, 10s, 20s delays`).         |
| **Checkpointing Ignored**       | No periodic snapshots or transaction logs; writes not flushed to disk.         | Long recovery times after crash; lost uncommitted changes.                    | Enable checkpointing (e.g., PostgreSQL `checkpoint_timeout`) or WAL (Write-Ahead Logging).       |
| **Unvalidated Writes**          | Writing raw data without schema validation or constraints.                     | Schema drift, corruption, or invalid data filling storage.                   | Enforce schema validation (e.g., `CREATE TABLE ... CHECK (field = expected_value)`).           |
| **Single-Writer Bottleneck**    | No replication or leader-follower redundancy for critical writes.              | Single point of failure (SPOF).                                               | Use leader-based replication (e.g., Kafka, ZooKeeper) or synchronous multi-master setups.      |
| **Lazy Writes**                 | Buffering writes without persistence guarantees (e.g., async queues).          | Delayed durability; data loss if queue crashes.                               | Use synchronous writes or persistent queues (e.g., Kafka with `acks=all`).                        |
| **No Idempotency for Retries**  | Duplicate operations on retry (e.g., `INSERT` without unique constraints).      | Duplicate records or data anomalies.                                          | Design for idempotency (e.g., use `ON DUPLICATE KEY UPDATE` or transaction IDs).                |

---

## **Query Examples**
### **1. Detecting Uncommitted Transactions (PostgreSQL)**
```sql
-- List open transactions (High risk of durability loss on crash)
SELECT pid, now() - xact_start AS duration FROM pg_stat_activity
WHERE state = 'active' AND query LIKE '%INSERT/UPDATE/DELETE%';
```

### **2. Checking for Volatile Storage Usage**
```bash
# Identify files stored in /dev/shm (RAM disk)
find /dev/shm -type f -name "*.dat" | xargs ls -lh
```
**Mitigation:** Move to `/var/lib/` or configure `tmpfs` with `discard` option.

### **3. Simulating a Network Timeout Retry**
```python
import requests
from time import sleep

def retry_with_backoff(url, max_retries=3):
    for i in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if i == max_retries - 1:
                raise
            sleep(2 ** i)  # Exponential backoff
```
**Pattern Violation:** Removing the `sleep` or setting fixed delays would risk cascading failures.

### **4. Enforcing Checkpointing (MySQL)**
```sql
-- Enable binary logging (for durability)
SET GLOBAL binlog_format = 'ROW';
SET GLOBAL sync_binlog = 1; -- Force every transaction to disk

-- Schedule checkpoints manually (or rely on MySQL's auto-checkpoint)
FLUSH TABLES WITH READ LOCK; -- Pause writes (use cautiously)
UNLOCK TABLES;
```

### **5. Validating Writes Before Persistence**
```sql
-- Enforce schema constraints in PostgreSQL
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL CHECK (email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
);

-- Use NOTICE to log schema violations
INSERT INTO users (email) VALUES ('invalid-email') ON CONFLICT DO NOTHING;
```

---

## **Implementation Details**
### **Key Concepts**
1. **Atomicity**
   - Principle: All-or-nothing execution of a transaction. *Anti-pattern:* Partial commits (e.g., writing to DB but not logs).
   - **Fix:** Use `BEGIN`/`COMMIT` blocks or ORMs with session management.

2. **Durability Guarantees**
   - **Strong Durability:** Data survives *any* failure (e.g., disk writes + power loss protection).
   - **Weak Durability:** Data survives *crashes* but not hardware failure (e.g., no `fsync`).
   - *Anti-pattern:* Assuming "ACID" without verifying `fsync` or WAL.

3. **Idempotency**
   - Ensures retries don’t cause duplicate side effects. *Anti-pattern:* HTTP `POST` without `idempotency-key`.

4. **Checkpoints**
   - Periodic snapshots of the DB state to limit recovery time.
   - *Anti-pattern:* Disabling checkpoints (e.g., `checkpoint_segments=0` in PostgreSQL).

### **Common Pitfalls**
- **Overconfidence in "ACID" Compliance:**
  - PostgreSQL’s `BEGIN`/`COMMIT` doesn’t guarantee disk durability without `fsync`.
  - *Fix:* Set `synchronous_commit = on` and `fsync = on`.

- **Misconfigured Replication:**
  - Async replication can lag behind writes, risking data loss on master failure.
  - *Fix:* Use synchronous replication (e.g., `replica_placement_policies` in CockroachDB).

- **Ignoring OS-Level Durability:**
  - Linux’s `O_DIRECT` bypasses cache but may lose writes on crash unless paired with `fsync`.

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Relation to Durability Anti-Patterns**                                      |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Saga Pattern**          | Manage long-running transactions via compensating actions.                     | Mitigates *No Transaction Management* by breaking work into atomic units.     |
| **Write-Ahead Logging (WAL)** | Log changes before applying them to storage.                                | Directly counters *Checkpointing Ignored* by ensuring durability via logs.    |
| **Idempotent Operations** | Design operations to be safely retried without side effects.                   | Fixes *Unidempotency* by ensuring retries don’t corrupt data.                   |
| **Multi-Region Replication** | Distribute writes across geographic regions for fault tolerance.            | Complements *Single-Writer Bottleneck* by eliminating SPOFs.                   |
| **Event Sourcing**        | Store state changes as immutable events.                                        | Reduces risk of *Unvalidated Writes* via audit trails.                          |

---
## **Further Reading**
- [PostgreSQL Durability Tuning Guide](https://www.postgresql.org/docs/current/runtime-config-pg-hba.html)
- [CACM: Why Software Crashes](https://queued.jp/en/articles/past/16981) (Discusses durability in distributed systems)
- [AWS Well-Architected Framework: Reliability](https://aws.amazon.com/architecture/well-architected/) (Section on durability best practices)