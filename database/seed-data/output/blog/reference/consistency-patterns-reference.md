# **[Consistency Patterns] Reference Guide**

## **Overview**
The **Consistency Patterns** framework defines strategies to manage data consistency across distributed systems, ensuring that application states remain logically coherent even in the presence of network partitions, failures, or delayed operations. These patterns help developers balance the trade-offs between **availability**, **partition tolerance**, and **consistency** (CAP theorem) while implementing distributed applications. Common use cases include microservices, databases, event-driven architectures, and caching systems. This guide outlines key consistency patterns, their trade-offs, and implementation considerations.

---

## **Schema Reference**

| **Pattern**          | **Description**                                                                 | **When to Use**                                                                 | **Trade-offs**                                                                 | **Implementation Notes**                                                                 |
|----------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| **Strong Consistency** | Ensures all nodes see the same data at the same time.                          | Critical financial transactions, inventory systems.                          | High latency, lower availability under network partitions.                      | Use synchronous replication (Paxos, Raft) or distributed locks.                     |
| **Eventual Consistency** | Updates propagate asynchronously; system converges over time.               | High-availability systems (e.g., social media feeds, non-critical data).     | Stale reads possible; requires conflict resolution.                          | Implement CRDTs (Conflict-free Replicated Data Types) or operational transformation. |
| **Causal Consistency** | Preserves causal order of operations (e.g., if A → B, then B must follow A). | Collaborative editing (e.g., Google Docs), audit logs.                       | Higher complexity than eventual consistency but stronger than weak consistency. | Use vector clocks or Lamport timestamps.                                                 |
| **Session Consistency** | Guarantees consistency within a user's session but not across sessions.      | Web applications with per-user data (e.g., shopping carts).                  | Limited to single-client scenarios.                                           | Use signed cookies, JWT, or session-based databases.                                   |
| **Monotonic Reads**   | Once a client reads a value, subsequent reads never return an older value.    | Time-sensitive applications (e.g., stock prices).                            | Higher latency due to synchronization.                                          | Combine with strong consistency or snapshot isolation.                                |
| **Monotonic Writes**  | Writes from a client are always seen by that client.                          | Systems requiring write persistence (e.g., configuration settings).          | May not enforce global consistency.                                              | Use write-ahead logging + client-side tracking.                                         |
| **Read-Your-Writes**  | A client’s writes are immediately visible to their own reads.                  | User-facing applications (e.g., comments, likes).                           | No global consistency; requires application logic.                           | Cache read-after-write responses locally.                                               |
| **Read-Repair**       | Detects and fixes inconsistencies during reads.                               | Systems with eventual consistency (e.g., Dynamo-style databases).             | Higher read latency due to repairs.                                              | Implement hinted handoffs or anti-entropy protocols.                                  |
| **Hinted Handoff**    | Temporarily stores writes for unavailable nodes; delivers later.             | High-availability clusters (e.g., Cassandra).                                | Risk of stale writes if nodes stay down.                                          | Configure TTL (Time-To-Live) for hints.                                                 |
| **Quorum-Based**      | Requires a majority of nodes to acknowledge writes/reads.                     | Durable systems (e.g., blockchain, consensus protocols).                     | Higher latency; only works with odd-numbered node counts.                       | Use in Raft or Dynamo-style systems.                                                    |
| **Bulkhead**          | Isolates consistency checks to prevent cascading failures.                   | Resilient microservices (e.g., payment processing).                          | Overhead from isolation boundaries.                                              | Implement circuit breakers or retry policies.                                           |

---

## **Implementation Details**

### **1. Strong Consistency**
- **How it works**: Replicas acknowledge a write only after all nodes confirm receipt.
- **Pros**: No stale reads; predictable behavior.
- **Cons**: High latency; single point of failure (if leader fails).
- **Example Libraries**:
  - **Databases**: PostgreSQL (row-level locks), MongoDB (strong write concern).
  - **Consensus**: Raft (`raft-go`, `etcd`).
- **Anti-Pattern**: Avoid in high-latency environments (e.g., global apps).

### **2. Eventual Consistency**
- **How it works**: Writes propagate asynchronously via replication or event sourcing.
- **Pros**: High availability; scales horizontally.
- **Cons**: Stale reads; requires conflict resolution (e.g., last-write-wins or merge strategies).
- **Example Libraries**:
  - **Databases**: DynamoDB, Cassandra.
  - **State Sync**: Apache Kafka (event streaming), CRDTs (`automerge-js`).
- **Conflict Resolution**:
  - **Last-Write-Wins (LWW)**: Simple but loses data if conflicts occur.
  - **CRDTs**: Conflict-free by design (e.g., `yjs` for collaborative editing).

### **3. Causal Consistency**
- **How it works**: Tracks dependencies between operations using **vector clocks** or **Lamport timestamps**.
- **Pros**: Stronger than eventual consistency; preserves logical order.
- **Cons**: Complex implementation; higher overhead.
- **Example Libraries**:
  - **Vector Clocks**: `crdt` (JavaScript), `crdt.ts`.
  - **Operational Transformation**: `ot.js` (for collaborative editing).

### **4. Session Consistency**
- **How it works**: Isolates data per user session (e.g., via JWT, cookies, or session tokens).
- **Pros**: Simple for single-client apps; no global coordination needed.
- **Cons**: Doesn’t scale for multi-user collaborations.
- **Example**:
  ```javascript
  // Pseudocode: Session-based data access
  const sessionToken = getCookie("session");
  const userData = db.query(`SELECT * FROM cart WHERE session_id = ?`, [sessionToken]);
  ```

### **5. Monotonic Reads/Writes**
- **Monotonic Reads**:
  - **Implementation**: Use `READ_COMMITTED` isolation or snapshot isolation in databases.
  - **Example** (PostgreSQL):
    ```sql
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
    ```
- **Monotonic Writes**:
  - **Implementation**: Append-only logs (e.g., Kafka) or write-ahead logs (WAL).
  - **Example** (Kafka):
    ```python
    producer.send("topic", value=b"update_data", timestamp=time.time())
    ```

### **6. Read-Repair**
- **How it works**: Detects inconsistencies during reads and fixes them (e.g., compare values across replicas).
- **Example** (Cassandra):
  ```python
  # Pseudocode: Compare replicas and repair
  def read_repair(session, key):
      replica1 = session.execute(f"SELECT value FROM table WHERE key = {key}").one()
      replica2 = session.execute(f"SELECT value FROM table WHERE key = {key}").one()
      if replica1.value != replica2.value:
          session.execute(f"UPDATE table SET value = ? WHERE key = ?", (replica1.value, key))
  ```

### **7. Hinted Handoff**
- **How it works**: Store writes for down nodes temporarily; deliver them when nodes recover.
- **Example** (Cassandra Configuration):
  ```yaml
  # seed.properties
  hinted_handoff_enabled=true
  max_hint_window_in_ms=10000
  ```

### **8. Quorum-Based**
- **How it works**: Require `W` writes + `R` reads from `N` nodes where `W + R > N`.
  - Example: `N=5`, `W=3`, `R=3` (for majority consistency).
- **Example** (DynamoDB):
  ```python
  table.put_item(
      Item={"id": "123", "value": "x"},
      ReturnConsistency="STRONG"  # Enforces quorum
  )
  ```

### **9. Bulkhead**
- **How it works**: Isolate consistency checks in microservices to prevent cascading failures.
- **Example** (Spring Boot Circuit Breaker):
  ```java
  @CircuitBreaker(name = "consistency-check", fallbackMethod = "fallback")
  public boolean isDataConsistent() {
      return db.query("SELECT * FROM consistency_check") != null;
  }
  ```

---

## **Query Examples**

### **1. Strong Consistency Query (PostgreSQL)**
```sql
-- Ensure all replicas acknowledge the write
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;  -- Fails if any node rejects
```

### **2. Eventual Consistency Query (Cassandra)**
```python
# Write (asynchronous)
session.execute("""
    INSERT INTO transactions (user_id, amount)
    VALUES (%s, %s)
""", ("user1", 50))

# Read (may return stale data)
result = session.execute("SELECT balance FROM accounts WHERE user_id = 'user1'")
print(result[0].balance)  # Eventually correct
```

### **3. Causal Consistency (Vector Clocks)**
```javascript
// Pseudocode: Track causality with vector clocks
const clock = { user1: 1, user2: 1 };
const updateClock = (key, value) => {
    clock[key]++;
    return { ...clock, value };
};

// Merge two causal states
const merge = (a, b) => {
    const merged = { ...a };
    for (const [key, val] in b) {
        merged[key] = Math.max(merged[key] || 0, val);
    }
    return merged;
};
```

### **4. Read-Your-Writes (Redis)**
```javascript
// Write with flag to notify reads
SET user:123:balance 100
PUBLISH user:123:updates "balance=100"

// Subscribe to updates
SUBSCRIBE user:123:updates
```

### **5. Read-Repair (Custom Implementation)**
```python
def read_repair(db, key):
    replica1 = db.execute(f"SELECT * FROM data WHERE key = {key}").replica1
    replica2 = db.execute(f"SELECT * FROM data WHERE key = {key}").replica2
    if replica1.value != replica2.value:
        db.execute(f"UPDATE data SET value = {replica1.value} WHERE key = {key}")
        return replica1.value
    return replica1.value
```

---

## **Related Patterns**

| **Related Pattern**       | **Connection to Consistency**                                                                 | **When to Pair**                                                                 |
|---------------------------|--------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Idempotency**           | Ensures repeated operations don’t cause duplicates or side effects.                          | Pair with strong consistency to avoid accidental retries.                         |
| **Saga Pattern**          | Manages distributed transactions via a sequence of local transactions.                      | Use with eventual consistency for long-running workflows.                       |
| **CQRS**                  | Separates read and write models; read models can use eventual consistency.                    | Ideal for high-throughput systems with stale-read tolerance.                     |
| **Event Sourcing**        | Stores state changes as immutable events; enables replayability and auditing.              | Combine with eventual consistency for scalable event replay.                      |
| **Compensating Transactions** | Rolls back operations if a saga fails.                                                   | Use in distributed systems with eventual consistency to recover failed writes.   |
| **Optimistic Locking**    | Uses versioning to handle concurrent updates (e.g., `SELECT ... FOR UPDATE`).              | Pair with strong consistency to prevent lost updates.                           |
| **Sakila Database Schema** | Reference for relational consistency (e.g., foreign keys, ACID).                            | Use as a baseline for strong consistency in traditional databases.               |

---

## **Key Considerations**
1. **Choose Based on Use Case**:
   - **Financial systems** → Strong consistency.
   - **Social media** → Eventual consistency.
   - **Collaborative editing** → Causal consistency.
2. **Trade-Offs**:
   - **Availability vs. Consistency**: CAP theorem mandates a choice.
   - **Latency**: Strong consistency adds delay; eventual consistency trades reads for speed.
3. **Conflict Resolution**:
   - Use **CRDTs** for multi-user apps.
   - Implement **merge strategies** (e.g., operational transformation).
4. **Observability**:
   - Monitor consistency with:
     - **Latency metrics** (e.g., P99 write latency).
     - **Conflict rates** (e.g., % of stale reads).
     - **Replication lag** (for eventual consistency).

---
**Further Reading**:
- [CAP Theorem (Gilbert & Lynch, 2002)](https://www.cs.berkeley.edu/~brewer/cs262b-2004/lectures/lec6-s1.pdf)
- [CRDTs: Theory & Practice](https://hal.inria.fr/inria-00398049/document)
- [Eventual Consistency Done Right (YC 2010)](https://www.ycombinator.com/blog/2010/04/consistency-is-for-quits.html)