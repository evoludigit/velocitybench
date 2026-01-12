**[Pattern] Consistency Strategies Reference Guide**

---

### **Overview**
**Consistency Strategies** define how distributed systems reconcile conflicting states across nodes, ensuring data integrity despite eventual latency or network partitions. This pattern is critical for high-availability systems (e.g., databases, microservices) where consistency must be balanced with availability and partition tolerance (CAP theorem). Common strategies include **strong consistency** (linearizable, serializable), **eventual consistency** (relaxed, weak), **tunable consistency** (configurable trade-offs), **hybrid approaches** (e.g., multi-active with conflict resolution), and **optimistic/pessimistic locking**.

Key trade-offs:
- **Strong consistency**: High latency, low availability during partitions.
- **Eventual consistency**: Lower latency, higher availability, but stale reads.
- **Hybrid/Conflict-Free Replicated Data Types (CRDTs)**: Decentralized consistency with automatic resolution.

---

### **Schema Reference**
| **Component**               | **Description**                                                                                     | **Example Implementations**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Consistency Model**       | Defines rules for data propagation and conflict resolution.                                         | Strong (Paxos, Raft), Eventual (Dynamo, Cassandra), Tunable (Amazon DynamoDB), CRDTs (YugabyteDB) |
| **Conflict Resolution**     | Mechanisms to handle concurrent writes (e.g., timestamps, vectors, merge functions).              | Last-Write-Wins (LWW), Operational Transformation (OT), CRDTs (add-only, state-based).       |
| **Propagation Protocol**    | How data is synchronized across nodes (e.g., gossip, batching, replication).                       | Paxos (leader-based), Raft (log replication), Dynamo’s Hinted Handoff, Kafka (event log).  |
| **Conflict Detection**      | Methods to identify inconsistencies (e.g., version vectors, causality checks).                    | Vector clocks, Lamport timestamps, causal consistency checks.                              |
| **Failover Mechanism**      | How the system handles node failures (e.g., leader election, read repair).                         | Raft’s leader election, Cassandra’s read repair, Dynamo’s gossip protocol.                 |
| **Performance Tuning**      | Optimizations for latency/throughput (e.g., batching, compression, retries).                       | Tunable consistency in DynamoDB (strong/weak/consistent reads), Cassandra’s replication factor. |

---

### **Implementation Details**

#### **1. Strong Consistency**
**Goal**: All reads return the most recent write.
**Mechanisms**:
- **Primary-Backup Models**: Paxos/Raft (linearizable reads/writes require acknowledgments from a majority of nodes).
- **Two-Phase Commit (2PC)**: Atomic commits across nodes but blocks during failures.
- **Distributed Locks**: Pessimistic locking (e.g., ZooKeeper) to serialize access.

**Trade-offs**:
- High latency (requires coordination).
- Available only if ≥N/2 nodes are up (N = replication factor).

**Example (Raft)**:
```plaintext
1. Leader receives write → appends to log.
2. Leader replicates log to followers (acknowledgments required).
3. Client waits for majority ACK → proceeds.
```

---

#### **2. Eventual Consistency**
**Goal**: Conflicts resolved asynchronously; reads may return stale data.
**Mechanisms**:
- **Last-Write-Wins (LWW)**: Timestamps resolve conflicts (e.g., DynamoDB).
- **Conflict-Free Replicated Data Types (CRDTs)**:
  - **Add-only CRDTs**: Planar/gnumeric sets (e.g., HyperLogLog for cardinality).
  - **State-based CRDTs**: Counter, register (e.g., YCSB’s CRDT benchmarks).
- **Gossip Protocols**: Nodes exchange state periodically (e.g., Dynamo’s anti-entropy).

**Trade-offs**:
- Lower latency/throughput.
- Stale reads until convergence.

**Example (Dynamo’s Hinted Handoff)**:
```plaintext
1. Node A fails → writes are "hinted" to node B.
2. Node A recovers → B forwards hints.
3. Anti-entropy (e.g., Merkle trees) detects missing data.
```

---

#### **3. Tunable Consistency**
**Goal**: Adjust consistency per operation (e.g., "strong for writes, weak for reads").
**Mechanisms**:
- **Consistency Levels** (e.g., Cassandra’s `ONE`, `QUORUM`, `ALL`).
- **Dynamic Trade-offs** (e.g., DynamoDB’s `ConsistentRead` flag).

**Example (Cassandra Query)**:
```sql
-- Strong consistency (write + read quorum)
INSERT INTO users (id, name) VALUES (1, 'Alice');
SELECT * FROM users WHERE id = 1 USING CONSISTENCY QUORUM;
```

---

#### **4. Hybrid Approaches**
**Goal**: Combine strong/weak consistency for specific use cases.
**Mechanisms**:
- **Multi-Active Replication**: Multiple active replicas (e.g., Oracle RAC) with conflict resolution (e.g., SCRAM for SQL).
- **Conflict-Free Replicated Data Types (CRDTs)**: Decentralized merges (e.g., Apache Cassandra’s CRDT extensions).

**Example (SCRAM for SQL)**:
```sql
-- Conflict resolution via timestamps + application logic
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
```

---

#### **5. Conflict Resolution Strategies**
| **Strategy**               | **When to Use**                          | **Pros**                          | **Cons**                          |
|----------------------------|-----------------------------------------|-----------------------------------|-----------------------------------|
| **Last-Write-Wins (LWW)**  | Orderly writes (e.g., CRUD operations). | Simple, low overhead.             | Data loss if primary fails.       |
| **Operational Transformation (OT)** | Collaborative editing (e.g., Google Docs). | Preserves causality.              | Complex state management.          |
| **CRDTs (Add-only)**       | Offline-first apps (e.g., Notion).      | Conflict-free, merges automatically. | Higher memory usage.               |
| **Application-Level**     | Custom conflict rules (e.g., banking).   | Flexible.                         | Requires logic in application.      |

---

### **Query Examples**

#### **1. Strong Consistency (Raft)**
**Scenario**: Deploy a key-value store with Raft consensus.
**Commands**:
```bash
# Initialize cluster (3 nodes)
raft init-cluster --nodes node1,node2,node3

# Write (requires leader)
curl -X POST http://leader:8080/key/value -d "hello"

# Read (strong consistency)
curl http://leader:8080/key
```

#### **2. Eventual Consistency (DynamoDB)**
**Scenario**: Configure DynamoDB for eventual consistency.
```bash
# Write (eventual by default)
aws dynamodb put-item \
    --table-name Users \
    --item '{"id": {"S": "1"}, "name": {"S": "Alice"}}'

# Read (eventually consistent)
aws dynamodb get-item \
    --table-name Users \
    --key '{"id": {"S": "1"}}' \
    --consistent-read FALSE
```

#### **3. Tunable Consistency (Cassandra)**
**Scenario**: Set consistency level for a query.
```sql
-- Write with LOCAL_QUORUM (strong)
INSERT INTO users (id, name) VALUES (1, 'Bob') USING CONSISTENCY LOCAL_QUORUM;

-- Read with ONE (weak)
SELECT * FROM users WHERE id = 1 USING CONSISTENCY ONE;
```

#### **4. CRDT-Based Conflict Resolution (YugabyteDB)**
**Scenario**: Use a state-based CRDT (e.g., register) for counters.
```sql
-- Initialize counter (CRDT-based)
CREATE TABLE counters (id UUID PRIMARY KEY, value INT64);

-- Increment (automatically resolves conflicts)
UPDATE counters SET value = value + 1 WHERE id = '123';
```

---

### **Related Patterns**
1. **[Saga Pattern]** – Manage distributed transactions via compensating actions (useful with eventual consistency).
2. **[Leader Election]** – Critical for strong consistency models (e.g., Raft, ZooKeeper).
3. **[Event Sourcing]** – Append-only logs for auditing and replay (complements eventual consistency).
4. **[CQRS]** – Separate reads/writes to optimize consistency (e.g., strong writes + eventual reads).
5. **[Partitions]** – Split data for scalability (e.g., Dynamo’s partition key design).
6. **[Idempotency]** – Ensure retries don’t corrupt state (e.g., `PUT` with idempotency keys).

---

### **Best Practices**
1. **Choose Based on Use Case**:
   - **Strong**: Financial transactions, inventory systems.
   - **Eventual**: Social media feeds, caching layers.
   - **Tunable**: Hybrid OLTP/OLAP workloads.
2. **Monitor Convergence**:
   - Track divergence metrics (e.g., Cassandra’s `repair` latency).
   - Use vector clocks to debug causality violations.
3. **Optimize Propagation**:
   - Batch writes (e.g., Kafka’s log compaction).
   - Prioritize critical data (e.g., Dynamo’s `TTL` for ephemeral keys).
4. **Test Failure Scenarios**:
   - Chaos engineering (e.g., kill nodes in Raft/Paxos clusters).
   - Validate conflict resolution under load (e.g., CRDT benchmarks).

---
**See Also**:
- [CAP Theorem](https://en.wikipedia.org/wiki/CAP_theorem)
- [CRDT Paper](https://hal.inria.fr/hal-00849061/document)
- [DynamoDB Consistency Models](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html)