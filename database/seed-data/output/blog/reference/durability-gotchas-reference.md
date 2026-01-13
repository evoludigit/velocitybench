# **[Pattern] Durability Gotchas – Reference Guide**

## **Overview**
Durability—ensuring data is preserved beyond transient failures—is a critical concern in distributed systems. However, subtle pitfalls can undermine even well-designed systems. This guide outlines common **Durability Gotchas**, their root causes, and mitigation strategies, helping architects and engineers design resilient, fault-tolerant applications.

---

## **Key Concepts & Implementation Details**
Durability failures arise from three primary causes:
1. **Unacknowledged Writes** – Data written but not committed or logged.
2. **Partial Failures** – Some nodes/records survive while others don’t due to inconsistent recovery.
3. **Latency vs. Guarantees** – Trade-offs between performance and strict durability promises.

### **Common Scenarios & Gotchas**
| **Gotcha** | **Description** | **Impact** | **Root Cause** |
|------------|----------------|------------|----------------|
| **Write-Ahead Logging (WAL) Failures** | WAL corruption, truncation, or unflushed data due to crashes. | Lost writes; incomplete state recovery. | Lack of WAL integrity checks or quorum-based commits. |
| **Quorum-Based Consistency Misconfigurations** | Insufficient replication factors or node failures exceeding quorum. | Temporary or permanent data loss. | Underestimating failure domains (e.g., rack/zone failures). |
| **Eventual Consistency Exploits** | Clients reading stale data post-write before replication completes. | Inconsistent client-side state. | Optimistic concurrency or weak durability guarantees. |
| **Durable Queues Without Persistence** | Messages lost due to in-memory queue failures. | Critical workflow disruptions. | Missing disk-backed durability (e.g., Kafka without `min.insync.replicas`). |
| **Timeouts Overriding Durability** | Client timeouts causing premature failure before server acknowledges. | Uncommitted writes discarded. | Short-lived connections or misconfigured retries. |
| **Leaky Durability in CRDTs** | Concurrency control failures in conflict-free replicated data types (CRDTs). | Inconsistent merging across nodes. | Lack of operational transformation or validation. |
| **Idempotent Operations Bypassed** | Retries without deduplication cause duplicate side effects. | Duplicate transactions or resource exhaustion. | Missing idempotency keys or checks. |

---

## **Schema Reference**
Use the following schema to model key durability constraints in your system. Adjust based on your storage engine (e.g., SQL, NoSQL, or ledger-based systems).

| **Field**               | **Type**       | **Description**                                                                 | **Example**                     |
|-------------------------|----------------|-------------------------------------------------------------------------------|---------------------------------|
| `durability_level`      | `ENUM`         | Strictness of durability guarantees (`NONE`, `SINGLE`, `MULTI`, `FULL`).     | `FULL`                          |
| `write_acknowledgment`  | `BOOLEAN`      | Require server-side commit confirmation?                                       | `TRUE`                          |
| `replication_factor`    | `INTEGER`      | Minimum replicas to acknowledge a write.                                       | `3`                             |
| `quorum_writes`         | `INTEGER`      | Majority threshold for durability (e.g., `(3 replicas + 1) / 2 = 2`).         | `2`                             |
| `sync_period_ms`        | `INTEGER`      | Time to wait for sync before acknowledging a batch write.                     | `500`                           |
| `idempotency_key`       | `STRING`       | Unique key to deduplicate retries (e.g., client + timestamp).                 | `user_12345#2024-05-15T10:00`   |
| `max_partial_writes`    | `INTEGER`      | Tolerated partial writes before aborting (e.g., 0 = strict all-or-nothing).   | `0`                             |

---

## **Query Examples**
### **1. Enforcing Durable Writes (SQL)**
```sql
-- Ensure all writes require 2/3 replicas (Raft consensus)
SET durable_write_quorum = 2;

-- Insert with durability guarantee
INSERT INTO orders (id, user_id, amount)
VALUES (123, 1, 99.99)
WITH ACKNOWLEDGE_DURABILITY;
```

### **2. Checking Replication Health (NoSQL)**
```javascript
// Check if a shard meets durability requirements (MongoDB)
db.runCommand({
  ping: "durabilityCheck",
  replicaSet: "replicaSet1",
  expectedReplicas: 3,
  minCommitQuorum: 2
});
// Output: {"ok": 1, "durable": true/false, "warnedNodes": [...]}
```

### **3. Handling Partial Failures (Ledger-based)**
```python
# In a state machine (e.g., Hyperledger)
def durable_update(self, key, value):
    try:
        tx = self.ledger.begin_transaction()
        tx.put(key, value)
        tx.commit()  # Blocks until durability confirmed
    except PartialFailure:
        self.ledger.abort()
        raise DurabilityError("Write failed; retry with idempotency key.")
```

### **4. Idempotent Retry with Exponential Backoff**
```bash
# AWS DynamoDB with idempotency
aws dynamodb put-item \
  --table-name Orders \
  --item '{"OrderID": {"S": "123"}}' \
  --condition-expression "attribute_not_exists(OrderID)" \
  --retry-mode adaptive \
  --retry-delay 100 \
  --max-retry-attempts 5
```

---

## **Mitigation Strategies**
| **Gotcha**               | **Solution**                                                                 |
|--------------------------|------------------------------------------------------------------------------|
| WAL Failures             | Enable crash recovery checks; use checksums for WAL segments.              |
| Quorum Misconfigurations | Set `replication_factor = failure_domain_size + 1` (e.g., 3 for multi-zone). |
| Eventual Consistency      | Use `LEASE`-based reads (e.g., Kafka `read.uncommitted`).                |
| Durable Queues           | Configure `min.insync.replicas` ≥ 2 in Kafka; use disk-backed stores.      |
| Timeouts                 | Use `SO_TIMEOUT` ≥ 3x expected write latency; implement circuit breakers. |
| CRDT Leakiness           | Validate CRDT ops with ` OperationalTransformation` (OT) before apply.     |
| Idempotent Failures      | Hash payload + timestamp as `idempotency_key`; track seen keys in a bloom filter. |

---

## **Related Patterns**
1. **Idempotent Operations** – Ensure retries don’t duplicate side effects.
2. **Two-Phase Commit (2PC)** – Atomic cross-service transactions (though 2PC has its own gotchas).
3. **CRDTs (Conflict-Free Replicated Data Types)** – For strongly consistent eventual consistency.
4. **Saga Pattern** – Manage distributed transactions with compensating actions.
5. **Retry-as-a-Service (e.g., Resilience4j)** – Handle transient failures with backoff.

---

## **Anti-Patterns to Avoid**
- **Optimistic Durability**: Assuming writes will succeed without checks (e.g., `ACKNOWLEDGE=0`).
- **Single-Write Points**: Centralizing writes to a single node (bottleneck + single point of failure).
- **Ignoring Partial Updates**: Allowing partial writes in transactions (violates atomicity).
- **Hardcoded Retries**: Linear retries without exponential backoff or circuit breakers.

---
**Key Takeaway**: Durability is invisible until it fails. Use this guide to proactively audit your system’s failure modes and instrument monitoring for partial or lost writes.