# **[Anti-Pattern] Consistency Anti-Patterns: Reference Guide**

---

## **Overview**
Consistency Anti-Patterns describe architectural or design flaws that undermine data consistency across distributed systems. These patterns arise from misaligned assumptions about synchronization, eventual consistency, or transaction boundaries. Unlike well-defined anti-patterns (e.g., God Object), these often result from misconfigured persistence layers, distributed databases, or overly optimistic optimistic concurrency control.

Common causes include:
- **Over-reliance on eventual consistency** without compensating mechanisms.
- **Lack of transactional boundaries** across microservices.
- **Implicit assumptions** about network latency or failure recovery.
- **Underestimated fan-out** in eventual consistency models.

This guide outlines key anti-patterns, their schemas, and technical mitigations.

---

## **Schema Reference**
Below are the most critical **Consistency Anti-Patterns** with their core characteristics.

| **Pattern Name**               | **Description**                                                                                     | **Root Cause**                                                                                     | **Impact**                                                                                     |
|--------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Blind Optimistic Locking**   | Using coarse-grained locks (e.g., database `SELECT ... FOR UPDATE`) without validation.            | Assumes contention is rare or network latency is negligible.                                       | Deadlocks, cascading rollbacks, or stale data reads.                                           |
| **Distributed Monolith**       | Tight coupling between services via shared databases instead of explicit communication.              | Siloed teams treat a distributed database as a single unit.                                        | Bottlenecks, divergence of data replicas, and cascading failures.                               |
| **Outdated Leaderboard**       | Displaying stale metrics (e.g., user rankings) without real-time updates.                          | Prioritizing availability over consistency in read-heavy systems.                                  | User dissatisfaction due to perceived unfairness or incorrect data.                             |
| **Saga of Shadows**            | Managing distributed transactions via manual reconciliation without compensating actions.          | Lack of explicit rollback logic or transactional integrity enforcement.                             | Inconsistent state or partial updates in cross-service workflows.                                |
| **Race Condition Resolver**    | Handling conflicts via static priorities (e.g., timestamp-based wins) without domain-specific rules. | Treating conflicts as binary outcomes rather than resolving them contextually.                       | Suboptimal resolutions (e.g., losing user edits due to arbitrary tie-breakers).                  |
| **Event Storming Without Acts**| Publishing events without ensuring eventual consistency guarantees.                                 | Assuming events automatically correlate without compensating logic.                                | Lost updates, duplicate processing, or orphaned state.                                          |
| **Lock-Free Illusion**         | Implementing optimistic concurrency without fallback mechanisms for conflicts.                      | Overconfidence in eventual consistency without validation.                                          | Silent failures or silent data corruption.                                                     |

---

## **Query Examples**
### **1. Blind Optimistic Locking**
**Problem:** A backend service locks a row to prevent concurrent modifications but doesn’t revalidate the row’s state after the lock expires.

**Bad Query (Vulnerable):**
```sql
-- Locks row but doesn't check for external changes post-lock
BEGIN TRANSACTION;
SELECT id, version FROM accounts WHERE id = 1 FOR UPDATE;
-- ...update logic...
COMMIT;
```

**Mitigation Query (Idempotent Check):**
```sql
-- Re-checks the row before applying changes
BEGIN TRANSACTION;
SELECT id, version FROM accounts WHERE id = 1 FOR UPDATE;
-- Re-fetch AFTER locking
SELECT version FROM accounts WHERE id = 1;
IF (version_matched) UPDATE ...
COMMIT;
```

---

### **2. Distributed Monolith**
**Problem:** Service A and Service B query the same database table, leading to inconsistencies when either updates it.

**Anti-Pattern Example:**
```python
# Service A (no transaction boundaries)
conn.execute("UPDATE users SET status='active' WHERE id=1")  # No isolation

# Concurrently, Service B:
conn.execute("UPDATE orders SET status='shipped' WHERE user_id=1")  # Race condition
```

**Mitigation Pattern:**
Use **explicit transactions** per service with **event sourcing** or **CQRS**:
```python
# Service A (transactional write)
with conn.begin():
    conn.execute("UPDATE users SET status='active' WHERE id=1")
    conn.execute("INSERT INTO audit_log (user_id, action) VALUES (1, 'status_updated')")
```

---

### **3. Outdated Leaderboard**
**Problem:** Displaying a user’s rank based on a snapshot instead of real-time data.

**Anti-Pattern Schema (Eventual Consistency Misuse):**
```sql
-- Leaderboard is rebuilt hourly via cron job (stale data)
CREATE OR REPLACE VIEW leaderboard AS
SELECT user_id, score, RANK() OVER (ORDER BY score DESC) as rank
FROM user_scores;
```

**Mitigation:**
Use **real-time pub/sub** (e.g., Kafka) to update ranks incrementally:
```python
# Kafka Topic: user_rank_updates
def update_rank(event: UserScoreUpdate):
    if event.score > user.old_score:
        publish("user_rank_updates", {"user_id": event.user_id, "rank": new_rank})
```

---

### **4. Saga of Shadows**
**Problem:** A transfer saga fails midway, leaving accounts in an inconsistent state.

**Anti-Pattern (No Compensation):**
```java
// Transfer Saga (no rollback)
public void transfer(Account from, Account to, BigDecimal amount) {
    from.debit(amount);
    // Failure here leaves `to` unchanged!
    to.credit(amount);
}
```

**Mitigation:**
Implement **compensating transactions**:
```java
// Saga with Rollback
public void transfer(Account from, Account to, BigDecimal amount) {
    try {
        from.debit(amount);
        to.credit(amount);
    } catch (Exception e) {
        from.credit(amount); // Compensating transaction
        throw e;
    }
}
```

---

### **5. Event Storming Without Acts**
**Problem:** Publishing events without ensuring eventual consistency.

**Anti-Pattern:**
```python
# Kafka Producer (no validation)
producer.send("user_updated", {"action": "rename", "old_name": "Alice", "new_name": "Bob"})

# Kafka Consumer (no validation)
def handle_user_update(event):
    db.query("UPDATE users SET name = %s WHERE old_name = %s", event["new_name"], event["old_name"])
```

**Mitigation:**
Use **exactly-once processing** with idempotency keys:
```python
def handle_user_update(event):
    if not db.query("SELECT 1 FROM processed_events WHERE event_id = %s", event["id"]):
        db.execute("UPDATE users SET name = %s WHERE id = %s", event["new_name"], event["user_id"])
        db.execute("INSERT INTO processed_events (event_id) VALUES (%s)", event["id"])
```

---

## **Related Patterns**
To counteract Consistency Anti-Patterns, consider these **constructive patterns**:

### **1. Saga Pattern**
- **Purpose:** Manage long-running transactions across services.
- **When to Use:** When ACID is insufficient (distributed systems).
- **Key Mechanisms:**
  - **Saga Choreography:** Decentralized state management via events.
  - **Saga Orchestration:** Centralized workflow with compensating actions.

### **2. Event Sourcing**
- **Purpose:** Maintain a complete audit trail of state changes.
- **When to Use:** Highly volatile or audit-required systems.
- **Key Mechanisms:**
  - Immutable event store (e.g., Kafka, EventStoreDB).
  - State reconstruction via replay.

### **3. CRDT (Conflict-Free Replicated Data Type)**
- **Purpose:** Enable offline-first consistency without locks.
- **When to Use:** Collaborative applications (e.g., shared documents).
- **Key Mechanisms:**
  - Operation-based merge (e.g., Yjs, RGA).

### **4. Two-Phase Commit (2PC) Alternatives**
- **Purpose:** Strong consistency in distributed transactions.
- **When to Use:** Critical cross-service workflows (e.g., payments).
- **Alternatives:**
  - **Saga Pattern** (for high availability).
  - **Distributed Transactions with TCC (Try-Cancel-Confirm)**.

### **5. Optimistic Concurrency Control (OCC)**
- **Purpose:** Reduce contention via version vectors.
- **When to Use:** Low-contention writes with rare conflicts.
- **Key Mechanisms:**
  - Compare-and-swap (e.g., `IF (version == expected_version)`).

---
## **Footnotes**
- **Trade-offs:** Prioritize consistency over availability only when absolutely necessary (CAP Theorem).
- **Monitoring:** Use tools like **Datadog**, **Prometheus**, or **Jaeger** to detect anti-patterns (e.g., lock contention).
- **Testing:** Stress-test with tools like **Chaos Monkey** to expose hidden inconsistencies.

---
**Last Updated:** [Insert Date]
**Contributors:** [List Names]