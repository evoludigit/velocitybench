# **[Pattern] ACID vs. BASE Transactions: Reference Guide**

---

## **Overview**
The **ACID vs. BASE transactions** pattern contrasts two foundational database transaction models:
- **ACID (Atomicity, Consistency, Isolation, Durability)** ensures strict consistency but struggles with scalability in distributed systems.
- **BASE (Basically Available, Soft state, Eventually consistent)** prioritizes availability and partition tolerance, sacrificing immediate consistency for performance.

This guide elucidates their definitions, tradeoffs, use cases, and distributed transaction strategies (e.g., 2PC, eventual consistency, conflict-free replicated data types). It includes schema mappings, query examples, and patterns like **Saga**, **CRDTs**, and **optimistic concurrency control**.

---

## **1. Definitions & Key Concepts**

### **1.1 ACID Transactions**
A set of operations executed as a **single logical unit** under strict guarantees:

| **Property**       | **Definition**                                                                                     | **Example**                                                                 |
|--------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Atomicity**      | All operations succeed or none do (no partial updates).                                           | Bank transfer: If `A→B` fails, neither account changes.                     |
| **Consistency**    | Transforms valid state to valid state (e.g., invariants like `balance ≥ 0`).                      | Enforces rules: `debit + credit = 0` after transfer.                       |
| **Isolation**      | Concurrent transactions see a consistent snapshot (no dirty reads, phantom reads).              | Two transactions can’t read/write the same row simultaneously.             |
| **Durability**     | Committed changes persist even after failures (e.g., via write-ahead logging).                 | WAL (Write-Ahead Log) ensures data survives crashes.                       |

**Isolation Levels** (SQL Standard):
| Level              | Description                                                                                     | Use Case                          |
|--------------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| **Read Uncommitted** | Dirty reads allowed (dirty pages visible).                                                     | Rare (high risk).                 |
| **Read Committed**  | Prevents dirty reads (default in most DBs).                                                    | General-purpose OLTP.             |
| **Repeatable Read** | Prevents non-repeatable reads/phantom reads (uses MVCC).                                       | Financial systems.                |
| **Serializable**    | Strongest isolation (serializable schedule).                                                   | Strictly consistent applications.  |

---

### **1.2 BASE Transactions**
A **relaxed** alternative for distributed systems, emphasizing:

| **Property**       | **Definition**                                                                                     | **Example**                                                                 |
|--------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Basically Available** | System remains operational even during partitions (no guarantees of instant consistency).      | Online social platforms during outages.                                  |
| **Soft State**      | System state evolves over time; not required to match exactly.                                      | User profiles (e.g., "last seen" timestamps drift slightly).                |
| **Eventually Consistent** | Changes propagate to all replicas asymptotically (no strict ordering).                         | Distributed caches (e.g., Redis Cluster).                                |

**Tradeoffs vs. ACID**:
| **Factor**         | **ACID**                          | **BASE**                          |
|--------------------|-----------------------------------|-----------------------------------|
| **Consistency**    | Strong (immediate)                | Weak (eventual)                   |
| **Availability**   | Lower (blocking under contention) | Higher (no blocking)              |
| **Partition Tolerance** | Fails if network splits (CAP) | Tolerates partitions (CAP)        |
| **Scalability**    | Limited (serialization overhead)  | High (decentralized ops)          |
| **Complexity**     | Simpler (local transactions)      | Complex (conflict resolution)     |

---

## **2. Schema Reference**

### **2.1 ACID Schema Example (Relational DB)**
```sql
-- Bank accounts table (ACID-compliant)
CREATE TABLE accounts (
    account_id INT PRIMARY KEY,
    balance DECIMAL(10, 2) NOT NULL CHECK (balance >= 0),
    version INT NOT NULL  -- For optimistic concurrency control
);
```

| **Field**      | **Type**       | **Description**                                                                 |
|----------------|----------------|---------------------------------------------------------------------------------|
| `account_id`   | `INT`          | Unique identifier for the account.                                              |
| `balance`      | `DECIMAL`      | Current balance (enforced ≥ 0 via `CHECK`).                                    |
| `version`      | `INT`          | Row version for optimistic concurrency (prevents lost updates).               |

**Primary Key Constraint**: `(account_id)` ensures uniqueness.
**Foreign Key Example** (ACID):
```sql
CREATE TABLE transfers (
    transfer_id INT PRIMARY KEY,
    from_account INT REFERENCES accounts(account_id),
    to_account INT REFERENCES accounts(account_id),
    amount DECIMAL(10, 2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### **2.2 BASE Schema Example (Eventual Consistency)**
```sql
-- User profiles (BASE: soft state, eventual consistency)
CREATE TABLE user_profiles (
    user_id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100),
    last_seen TIMESTAMP,  -- May drift across replicas
    metadata TEXT         -- Stored as JSON (schema-less)
);
```

| **Field**      | **Type**       | **Description**                                                                 |
|----------------|----------------|---------------------------------------------------------------------------------|
| `user_id`      | `VARCHAR`      | Unique identifier (UUID).                                                      |
| `name`         | `VARCHAR`      | User’s name (may be stale).                                                    |
| `last_seen`    | `TIMESTAMP`    | Approximate time of last activity (eventually consistent).                     |
| `metadata`     | `TEXT`         | Flexible data (e.g., preferences) stored as JSON for schema flexibility.       |

**Denormalization Example**:
```sql
-- BASE: Denormalized posts (reduces joins but may cause duplicates)
CREATE TABLE posts (
    post_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,  -- Embedded for locality
    content TEXT,
    timestamp TIMESTAMP
);
```

---

## **3. Query Examples**

### **3.1 ACID Queries (Strict Consistency)**
**1. Bank Transfer (2-Phase Commit Example)**
```sql
-- Step 1: Lock accounts (serializable isolation)
BEGIN TRANSACTION;
    UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
    UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
-- Step 2: Commit or rollback
COMMIT;  -- Both updates succeed or neither does.
```

**2. Optimistic Concurrency Control (Prevent Lost Updates)**
```sql
-- Check version before updating
SELECT balance, version FROM accounts WHERE account_id = 1;
-- Application validates version matches expected value.
UPDATE accounts SET balance = balance - 50, version = version + 1
WHERE account_id = 1 AND version = CURRENT_VERSION;
```

**3. Serializable Read (No Phantom Reads)**
```sql
-- Start transaction with SERIALIZABLE isolation
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    SELECT * FROM accounts WHERE balance > 0;  -- Consistent snapshot.
COMMIT;
```

---

### **3.2 BASE Queries (Eventual Consistency)**
**1. Read/Write with Conflict Resolution (CRDTs)**
```sql
-- Append-only log (BASE: no conflicting writes)
INSERT INTO activity_log (user_id, action, timestamp)
VALUES ('user1', 'liked_post', NOW());
-- Conflict-free: Duplicate writes are idempotent.
```

**2. Conditional Writes (Happy Path)**
```sql
-- Update if condition is met (BASE: may fail without blocking)
UPDATE user_profiles
SET last_seen = NOW()
WHERE user_id = 'user1' AND last_seen < NOW() - INTERVAL '1 hour';
```

**3. Eventual Consistency Workflow (Distributed Cache)**
```sql
-- Read from primary replica (may be stale)
SELECT name FROM user_profiles WHERE user_id = 'user1';

-- Write to all replicas (asynchronously)
INSERT INTO user_profiles (user_id, name, last_seen)
VALUES ('user1', 'Alice', NOW());
-- Replicas update eventually (e.g., via gossip protocol).
```

**4. Conflict-Free Replicated Data Type (CRDT) Example**
```sql
-- Example: Set Operations (CRDT for user preferences)
-- Application merges updates (e.g., `theme: 'dark'` vs. `theme: 'light'`).
UPDATE user_prefs SET theme = 'dark' WHERE user_id = 'user1';
```

---

## **4. Distributed Transaction Strategies**

### **4.1 Sagas (BASE)**
**Pattern**: Break long transactions into **local transactions** with compensating actions.
**Use Case**: Order processing (payments → inventory → shipping).

**Example Workflow**:
1. **Start Saga**:
   ```sql
   -- Payment (ACID)
   INSERT INTO payments (order_id, amount, status) VALUES (1, 100.00, 'PENDING');
   ```
2. **Inventory Deduction (Local TX)**:
   ```sql
   UPDATE inventory SET stock = stock - 1 WHERE product_id = 101;
   ```
3. **Failure Handling**:
   - If payment fails, compensate by **returning stock**:
     ```sql
     UPDATE inventory SET stock = stock + 1 WHERE product_id = 101;
     ```

**Tools**: Apache Kafka (event sourcing), AWS Step Functions.

---

### **4.2 Two-Phase Commit (ACID)**
**Pattern**: Global commit/rollback via coordinator (e.g., **Distributed Lock Manager**).
**Use Case**: Distributed databases (e.g., Oracle Global Transaction Manager).

**Phases**:
1. **Prepare**: All participants vote to commit.
2. **Commit/Rollback**: If all say "yes," execute globally.

**Problem**: Bottleneck; avoids only if all participants are available.

**Tools**: PostgreSQL `pg_prepare_transaction`, JDBC `XA`.

---
### **4.3 Eventual Consistency (BASE)**
**Pattern**: Decouple reads/writes via **replication lag**.
**Use Case**: Caching (Redis), CDNs (Cloudflare).

**Example**:
1. Write to primary:
   ```sql
   UPDATE cache SET value = 'new_data' WHERE key = 'user1';
   ```
2. Replicas update asynchronously (e.g., via **change data capture**).

**Conflict Resolution**:
- **Last Write Wins (LWW)**: Timestamp-based (e.g., `last_seen`).
- **Mergeable Data Types**: CRDTs (e.g., sets, counters).

**Tools**: DynamoDB (eventual consistency), Cassandra.

---
### **4.4 Optimistic Concurrency Control (ACID)**
**Pattern**: Assume no conflicts; validate on commit.
**Use Case**: High-contention systems (e.g., Git).

**Example**:
```sql
-- Read version
SELECT version FROM accounts WHERE account_id = 1;

-- Update with version check
UPDATE accounts
SET balance = balance - 50, version = version + 1
WHERE account_id = 1 AND version = 123;  -- Fails if version changed.
```

**Tools**: SQL `version` columns, MongoDB `_etag`.

---

## **5. Tradeoff Decision Matrix**

| **Scenario**               | **ACID**                          | **BASE**                          | **Pattern Suggestion**            |
|----------------------------|-----------------------------------|-----------------------------------|-----------------------------------|
| **Single-node OLTP**       | ✅ (e.g., PostgreSQL)             | ❌                                | ACID with `REPEATABLE READ`.       |
| **High-throughput logs**   | ❌ (too slow)                     | ✅ (e.g., Kafka)                  | BASE with append-only model.      |
| **Global financial system**| ✅ (e.g., distributed SQL)        | ❌                                | ACID + 2PC or Saga.               |
| **Geographically distributed app** | ❌ (latency)                 | ✅ (e.g., DynamoDB)               | BASE with CRDTs.                  |
| **Content management**      | ❌ (conflicts)                    | ✅ (e.g., Git, Markdown)          | BASE with LWW or mergeable types. |
| **Real-time analytics**     | ❌ (blocking)                     | ✅ (e.g., Kafka Streams)          | BASE with eventual consistency.   |

---

## **6. Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                      |
|---------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Saga**                  | Choreography/Orchestration of local transactions with compensating actions.                         | Long-running workflows (e.g., order processing).     |
| **CRDTs**                 | Conflict-free, mergeable data types for distributed systems.                                        | Collaborative editing (e.g., Google Docs).          |
| **Event Sourcing**        | Store state changes as an append-only event log.                                                   | Audit trails, time Travel.                            |
| **CAP Theorem**           | Design tradeoffs: Consistency, Availability, Partition tolerance.                                   | Choose based on `P` (e.g., BASE for `AP`).          |
| **Optimistic Locking**    | Assume no conflicts; validate on commit (e.g., version vectors).                                    | Low-contention systems.                               |
| ** eventual consistency** | Decouple reads/writes with replication lag (e.g., DynamoDB).                                     | Scalable, tolerant systems.                           |
| **Distributed Locks**     | ACID-like isolation via external locks (e.g., Redis `SETNX`).                                      | High-contention shared resources.                    |

---

## **7. Anti-Patterns & Pitfalls**

### **7.1 ACID Anti-Patterns**
- **Long-running transactions**: Held locks → deadlocks.
  **Fix**: Break into smaller transactions (Saga).
- **Overusing SERIALIZABLE**: Performance bottleneck.
  **Fix**: Use `READ COMMITTED` unless needed.
- **Ignoring versioning**: Lost updates in optimistic CC.
  **Fix**: Add `version` columns.

### **7.2 BASE Anti-Patterns**
- **Stale reads**: Assumed consistency where it doesn’t hold.
  **Fix**: Explicitly mark reads as "stale-tolerant."
- **No conflict resolution**: Silent data corruption.
  **Fix**: Use CRDTs or application-level merging.
- **Over-replication**: Wasted bandwidth.
  **Fix**: Filter updates with **vector clocks** or **gossip protocols**.

---

## **8. Tools & Libraries**

| **Category**               | **Tools**                                                                                     | **Use Case**                          |
|----------------------------|-----------------------------------------------------------------------------------------------|---------------------------------------|
| **ACID DBs**               | PostgreSQL, MySQL, SQL Server                                                               | OLTP, financial systems.              |
| **BASE DBs**               | DynamoDB, Cassandra, Redis Cluster                                                           | High-scale, eventual consistency.    |
| **Saga Frameworks**        | Apache Kafka, AWS Step Functions, Temporal.io                                              | Distributed workflows.               |
| **CRDTs**                  | Yjs, Automerge, Riak TS                                                                     | Collaborative apps.                   |
| **Conflict Resolution**    | Otter, CRDT.js                                                                             | Offline-first apps.                   |
| **2PC Implementations**    | JTA (Java), Spring TX, PostgreSQL `pg_prepare`                                             | Distributed ACID.                     |

---

## **9. Further Reading**
- **Books**:
  - *Designing Data-Intensive Applications* (Martin Kleppmann) – CAP, distributed systems.
  - *Transactions and Concurrency Control* (Bruce Lindsay) – ACID theory.
- **Papers**:
  - **CAP Theorem** (Gilbert & Lynch, 2002).
  - **CRDTs** (Shapiro et al., 2011).
- **Talks**:
  - [Eventual Consistency by Martin Kleppmann](https://www.youtube.com/watch?v=wI6XwPgaSV0).
  - [Sagas by Paul Dix](https://www.youtube.com/watch?v=HqYXGYgkB5k).