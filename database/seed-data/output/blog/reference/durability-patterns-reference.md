---
# **[Durability Patterns] Reference Guide**

---

## **Overview**
Durability Patterns ensure that data and system state survive failures, network partitions, or process crashes. They provide resilience by guaranteeing eventual consistency through replication, logging, or recovery mechanisms. This reference covers key **durability patterns**, their trade-offs, and implementation considerations, focusing on **replication, persistence, and recovery strategies**.

Common use cases include distributed systems, microservices, event-driven architectures, and database-backed applications where data loss or corruption must be avoided.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                     | **Use Case**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| **Atomicity**             | All-or-nothing execution of operations (e.g., transactions).                                         | Financial transactions, inventory sync. |
| **Consistency**           | Guaranteeing read-after-write correctness (strong, eventual, or causal).                             | Data integrity across nodes.         |
| **Repair**                | Mechanisms to recover from failures (e.g., checkpointing, snapshots).                               | Disaster recovery, failover systems.  |
| **Replication**           | Copying data to multiple nodes for fault tolerance.                                                 | Distributed databases, load balancing. |
| **Persistency**           | Writing data to durable storage (e.g., disk, distributed logs).                                     | Event streaming, audit trails.        |
| **Causality**             | Preserving order of operations even across failures.                                                 | Distributed systems with linearizability. |

---

## **Schema Reference**
Below are common durability pattern implementations with their **schema** and properties.

| **Pattern**               | **Schema Attributes**                                                                                     | **Trade-offs**                                                                                     |
|---------------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Log-Based Replication** | - `LogEntry`: `<sequence_id, payload, timestamp>` <br> - `Replica`: `<id, role (leader/follower), last_applied_offset>` | **Pros**: Ordered, append-only; **Cons**: High latency if leader fails.                          |
| **Checkpointing**        | - `Checkpoint`: `<timestamp, state_snapshot, metadata>` <br> - `RecoveryPoint`: `<latest_checkpoint, pending_log_entries>` | **Pros**: Fast recovery; **Cons**: Manual tuning required.                                        |
| **Two-Phase Commit (2PC)**| - `Prepare Phase`: All replicas acknowledge readiness. <br> - `Commit Phase`: All confirm or abort. | **Pros**: Strong consistency; **Cons**: Blocking, single point of failure (coordinator).            |
| **Multi-Leader Replication** | Multiple leaders; conflicts resolved via `last-write-wins` or application logic.                          | **Pros**: Low latency for local writes; **Cons**: Conflict resolution complexity.                |
| **Event Sourcing**        | - `EventStream`: `<event_id, event_type, data, timestamp>` <br> - `Aggregate`: State derived from events. | **Pros**: Full audit trail; **Cons**: Complex querying.                                            |
| **Causal Consistency (CRDTs)** | Conflict-free replicated data types (e.g., `map`, `counter`).                                            | **Pros**: No coordination; **Cons**: Limited use cases.                                           |

---

## **Implementation Details**
### **1. Log-Based Replication**
**Purpose**: Replicate changes from a leader to followers via a log (e.g., Kafka, log-structured merge trees).

#### **How It Works**
1. **Leader** appends new entries to the log (e.g., `log[offset=100] = {"type": "order_created", "data": {...}}`).
2. **Followers** asynchronously replicate logs and apply them to their state.
3. **Consensus** (optional): Use RPCs (e.g., Raft) or distributed locks to prevent split-brain.

#### **Example Code (Pseudocode)**
```python
# Leader node
def append_to_log(entry):
    offset = get_next_offset()
    log[offset] = entry
    broadcast_to_followers(log[offset])
    return offset

# Follower node
def replicate_log(entry):
    apply_to_state(entry)
    acknowledge_to_leader()
```

#### **Failure Handling**
- **Leader failover**: Elected via Raft/Paxos; followers promote a new leader.
- **Follower lag**: Monitor `last_applied_offset`; trigger re-sync if behind.

---

### **2. Checkpointing**
**Purpose**: Periodically save full system state to disk for fast recovery.

#### **How It Works**
1. **Periodically** (or on demand), save the current state:
   ```json
   {
     "timestamp": "2024-05-20T12:00:00Z",
     "state": {
       "inventory": { "item1": 100 },
       "users": { "user1": {...} }
     }
   }
   ```
2. **On crash**, restore from the latest checkpoint and replay pending log entries.

#### **Trade-offs**
- **Pros**: O(1) recovery time.
- **Cons**: High storage overhead; risk of data loss between checkpoints.

---

### **3. Two-Phase Commit (2PC)**
**Purpose**: Ensure all replicas agree before committing a transaction.

#### **How It Works**
1. **Prepare Phase**: Coordinator sends `prepare` to all replicas.
   - Replicas respond with `ACK`/`NACK`.
2. **Commit Phase**: If all `ACK`, coordinator sends `commit`; else, `abort`.

#### **Example (Pseudocode)**
```python
def commit_transaction(transaction):
    # Phase 1: Prepare
    for replica in replicas:
        if not replica.prepare(transaction):
            abort()
    # Phase 2: Commit
    for replica in replicas:
        replica.commit(transaction)
```

#### **Failure Handling**
- **Coordinator failover**: Use a backup coordinator or recover via logs.
- **Timeouts**: Abort if no response within `T` seconds.

---

### **4. Event Sourcing**
**Purpose**: Store state changes as immutable events; derive current state by replaying events.

#### **How It Works**
1. **Append events** to a log:
   ```json
   [{"id": "1", "type": "OrderCreated", "data": {...}},
    {"id": "2", "type": "PaymentProcessed", "data": {...}}]
   ```
2. **Project state** by replaying events:
   ```python
   def get_state():
       state = initial_state
       for event in log:
           state = apply_event(state, event)
       return state
   ```

#### **Trade-offs**
- **Pros**: Full audit trail, easy time-travel debugging.
- **Cons**: Querying current state requires replaying all events.

---

## **Query Examples**
### **1. Log-Based Replication Query**
**Query**: List unapplied log entries on a follower.
```sql
SELECT * FROM log_entries
WHERE offset > last_applied_offset
ORDER BY offset;
```

### **2. Checkpoint Recovery**
**Query**: Restore system state to the last checkpoint.
```bash
# Pseudocode for recovery script
load_checkpoint("latest_checkpoint.json")
replay_pending_logs("pending_events.log")
```

### **3. Event Sourcing Projection**
**Query**: Get user orders after a specific event.
```python
# Pseudocode
events = get_events("user1", after="2024-05-10")
state = initial_state
for event in events:
    state = apply_order_event(state, event)
return state.orders
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Saga Pattern**          | Manage distributed transactions via compensating actions.                                           | Microservices with eventual consistency. |
| **Circuit Breaker**       | Prevent cascading failures by interrupting calls to unhealthy services.                             | Resilient APIs.                          |
| **Idempotency**           | Ensure retries don’t cause duplicate side effects.                                                    | External APIs (e.g., payments).          |
| **Retry with Backoff**    | Exponential backoff for transient failures.                                                          | Network partitions.                       |
| **Leader Election (Raft)**| Elect a leader for consensus in distributed systems.                                                 | High-availability clusters.              |

---

## **Failure Modes & Mitigations**
| **Failure**               | **Mitigation Strategy**                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Leader crash**          | Automatic failover (Raft), or use multi-leader replication.                                         |
| **Network partition**     | Quorum-based consensus (e.g., 2PC with `N/2+1` replicas).                                          |
| **Storage corruption**    | Periodic snapshots, checksum validation, or distributed storage (e.g., S3).                      |
| **Log truncation**        | Retain logs for `T` weeks; use append-only storage (e.g., WAL).                                  |
| **Clock skew**            | Use NTP-synchronized clocks or vector clocks for causality.                                         |

---
**Note**: Durability patterns are often combined (e.g., **log-based replication + checkpoints**). Choose based on your **consistency vs. availability** trade-offs (CAP Theorem).