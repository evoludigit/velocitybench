# **[Pattern] Durability Monitoring Reference Guide**

---

## **Overview**
**Durability Monitoring** is an architectural pattern designed to ensure **data consistency, system reliability, and failure recovery** in distributed or stateful applications. This pattern tracks changes to data, persists them reliably, and detects inconsistencies or failures to prevent data loss or corruption. It is particularly critical in systems where **ACID compliance, eventual consistency guarantees, or transactional integrity** are required—such as databases, event-driven architectures, or microservices.

Durability Monitoring combines **write-ahead logging (WAL), checkpointing, and validation mechanisms** to validate that changes are correctly persisted and replicated across nodes. It helps identify **durability bottlenecks**, **latency spikes**, and **recovery failures**, enabling proactive maintenance and resilience.

---

## **Key Concepts**

| **Concept**               | **Definition**                                                                                     | **Example Use Case**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Write-Ahead Logging (WAL)** | A mechanism where changes are logged to a durable storage *before* being applied to the main data store. | Example: PostgreSQL’s `fsync()` ensures logs are written to disk before acknowledging a transaction. |
| **Checkpointing**         | Periodically saving the state of a system to a checkpoint file for faster recovery.               | Example: Redis snapshots (`save` or `bgsave`) for recovery after crashes.              |
| **Validation Mechanism**   | A process to verify that persisted changes match the expected state (e.g., checksums, snapshots). | Example: Kafka’s log compaction ensures only the latest message version is stored.     |
| **Durability Threshold**  | Configurable SLA (e.g., "99.9% durability within 1 second") to enforce consistency guarantees.   | Example: Distributed databases like Cassandra enforce `durability=ALL` for strong consistency. |
| **Recovery Workflow**      | Steps to restore a system from a checkpoint or log after a failure.                                | Example: Databases like MySQL restore from `ibdata1` after a server crash.            |

---

## **Schema Reference**

Durability Monitoring relies on three core schemas for tracking and validation:

| **Schema**               | **Fields**                                                                                     | **Purpose**                                                                                     |
|--------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **`DurabilityLogEntry`** | `{ transaction_id: UUID, operation: string, timestamp: ISO8601, status: "pending"/"committed", node_id: string }` | Logs each durability operation for replay in case of failure.                                    |
| **`Checkpoint`**         | `{ checkpoint_id: UUID, timestamp: ISO8601, system_state: JSON, size: MB, durability_metrics: { success: int, failures: int } }` | Captures a system snapshot at a specific point in time for recovery.                           |
| **`DurabilityMetrics`**  | `{ metric: "latency"/"failures"/"recovery_time", value: float, threshold: float, alert_status: boolean }` | Monitors KPIs to detect anomalies and enforce SLAs.                                             |

**Example JSON for `DurabilityLogEntry`:**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "operation": "INSERT",
  "timestamp": "2024-05-20T12:34:56.789Z",
  "status": "committed",
  "node_id": "node-001"
}
```

---

## **Implementation Steps**

### **1. Enable Write-Ahead Logging (WAL)**
Ensure your storage layer supports WAL and configure it to flush logs to disk **before** acknowledging transaction success.
- **Databases:** Enable `fsync` (PostgreSQL), `innodb_flush_log_at_trx_commit=1` (MySQL), or `durability=ALL` (Cassandra).
- **Key-Value Stores:** Use Redlock-like patterns or `WRITE-AFTER-WRITE` protocols (e.g., Redis’ `APPENDONLY` mode).

### **2. Implement Checkpointing**
Periodically save system state to a checkpoint file (e.g., every 10 minutes or after N transactions).
```pseudocode
function checkpoint() {
  capture_system_state();
  write_checkpoint_to_disk(checkpoint_id);
  update_meta_store(last_checkpoint_id);
}
```

### **3. Add Validation Mechanisms**
Compare the current state against the latest checkpoint to detect discrepancies.
```pseudocode
function validate_durability() {
  read_checkpoint(checkpoint_id);
  compare_state(applied_operations, checkpoint_state);
  if (discrepancy) {
    trigger_recovery_workflow();
  }
}
```

### **4. Monitor Durability Metrics**
Track:
- **Latency:** Time between commit and durability acknowledgment.
- **Failure Rate:** % of operations failing durability checks.
- **Recovery Time:** Time to restore from checkpoint.

**Example Query (Prometheus):**
```promql
duration_failure_rate =
  sum(rate(durability_failures_total[5m]))
  / sum(rate(durability_commits_total[5m]))
```

### **5. Design Recovery Workflow**
Automate recovery using checkpoints or logs:
```pseudocode
function recover_from_checkpoint() {
  restore_system_state(checkpoint_id);
  replay_pending_logs();
  notify_admins("Recovery complete");
}
```

---

## **Query Examples**

### **1. Check Durability Log for Failed Operations (SQL)**
```sql
SELECT transaction_id, operation, timestamp
FROM durability_log
WHERE status = 'pending'
  AND timestamp > NOW() - INTERVAL '5 minutes';
```

### **2. Compare Checkpoint State vs. Current State (NoSQL)**
```javascript
// MongoDB Aggregation
db.checkpoints.aggregate([
  { $lookup: {
      from: "system_state",
      let: { checkpoint_id: "$_id" },
      pipeline: [
        { $match: { $expr: { $eq: ["$checkpoint_id", "$$checkpoint_id"] } } }
      ],
      as: "state"
  }},
  { $match: { "state.0": { $exists: true } }},
  { $project: {
      discrepancy: {
        $eq: ["$state.0.data", db.current_state.findOne({}).data]
      }
  }}
]);
```

### **3. Alert on High Latency (Grafana Query)**
```sql
SELECT
  node_id,
  avg(durability_latency_ms) as avg_latency
FROM durability_metrics
WHERE timestamp > NOW() - 1h
GROUP BY node_id
HAVING avg_latency > 500
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Event Sourcing**        | Stores state changes as a sequence of immutable events for replayability.                          | Ideal for audit trails, time-series data, or complex business logic.              |
| **Saga Pattern**          | Manages distributed transactions by breaking them into local transactions coordinated via messages. | Useful for microservices with eventual consistency needs.                         |
| **Circuit Breaker**        | Prevents cascading failures by pausing calls to failing services.                                  | Complements durability checks to avoid overloading unreliable systems.            |
| **Idempotent Operations** | Ensures repeated calls have the same effect as a single call.                                      | Critical for retries in durability-sensitive workflows (e.g., payment processing).|

---

## **Best Practices**
1. **Enforce Durability SLAs:** Define thresholds for latency, failures, and recovery time.
2. **Log Everything:** Capture transaction IDs, timestamps, and node IDs for debugging.
3. **Test Recovery Scenarios:** Simulate failures (disk crashes, node deaths) to validate recovery.
4. **Decouple Monitoring:** Use a dedicated metrics service (e.g., Prometheus, Datadog) to avoid impacting durability.
5. **Optimize Checkpoints:** Balance frequency (too often = overhead; too rare = long recovery).

---
**See also:**
- [Durability in Distributed Systems (CAP Theorem)](https://basho.com/posts/technical/understanding-distributed-systems-with-the-cap-theorem/)
- [PostgreSQL Durability Tuning Guide](https://www.postgresql.org/docs/current/runtime-config-wal.html)