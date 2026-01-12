**[Pattern] Consistency Tuning Reference Guide**

---

### **Overview**
**Consistency Tuning** is a critical pattern for managing trade-offs between system consistency, performance, and availability in distributed applications—especially in event-driven architectures. This pattern allows developers to dynamically adjust consistency levels per operation (e.g., read/write, query/update) to balance data consistency with operational performance. It is essential for systems where strict consistency across all operations may be unnecessary or even detrimental to scalability.

Key use cases include:
- Microservices communicating via event sourcing or CQRS architectures.
- Data-intensive applications (e.g., IoT, financial systems) where some operations tolerate eventual consistency.
- Systems requiring **dynamic consistency**—where certain operations (e.g., analytics vs. transactional writes) demand different guarantees.

This guide covers:
- Core concepts of consistency tuning.
- Implementation strategies (e.g., using consistency levels in messaging, database leasing).
- Schema design for consistent metadata management.
- Query examples for configuring consistency per operation.
- Related patterns to complement Consistency Tuning.

---

---

### **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                                                                      |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Strong Consistency**  | All nodes see the same data, and writes propagate immediately. Guarantees ACID properties.                                                                                                                                                                     |
| **Eventual Consistency**| Reads may temporarily return stale data, but all updates will eventually propagate. Latency vs. consistency trade-off.                                                                                                                              |
| **Hybrid Consistency**  | Per-operation consistency tuning (e.g., using "consistency levels" in APIs).                                                                                                                                                                        |
| **Conflict Resolution** | Mechanisms like CRDTs (Commutative, Reassociative, Idempotent Operations) or last-write-wins (LWW) to resolve inconsistencies.                                                                                                                    |
| **Consistency Metadata**| Tags or labels attached to data (e.g., `version`, `timestamp`) to track consistency state.                                                                                                                                                               |

---

### **Implementation Details**

#### **1. Consistency Levers**
Adjust consistency via:
- **Messaging Systems**: Kafka (isolation levels), RabbitMQ (persistence modes).
- **Databases**: PostgreSQL’s `READ COMMITTED` vs. `SERIALIZABLE`, or DynamoDB’s `Strong/Eventual` consistency reads.
- **APIs**: Adding `ConsistencyLevel` headers to requests (e.g., `Accept: application/consistent=strong`).

#### **2. Schema Design**
**Core tables required:**
| Table Name          | Purpose                                                                                                                                                                                                                     |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ConsistencyPolicy` | Stores default/app-specific consistency rules (e.g., `{ "service": "order-service", "default": "eventual", "exceptions": ["payment"] }`).                                                             |
| `DataLock`          | Tracks active write locks to prevent conflicts (e.g., `{ "entity": "user:123", "lock_version": 42, "expiry": "2024-01-01T00:00:00Z" }`).                                                              |
| `EventLog`          | Event-sourced history with `consistency_level` metadata (e.g., `{ "event": "order_created", "version": 2, "consistency": "strong" }`).                                                                       |

**Example Relationships:**
- `DataLock` → Associated with `DataPolicy` (policy lookup).
- `EventLog` → References `ConsistencyPolicy` via `consistency_level`.

#### **3. Conflict Resolution**
| Mechanism       | Description                                                                                                                                                                                                                     |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **CRDTs**       | Conflict-free replicas (e.g., `PNCounter` for counters).                                                                                                                                                                  |
| **Last-Write-Wins** | Uses timestamps/versions to resolve conflicts (risk of data loss if inconsistent writes).                                                                                                                               |
| **Merge Patches** | Applies patches sequentially (e.g., CRDT operations or JSON merge strategies).                                                                                                                                              |

---

### **Schema Reference**

#### **1. `ConsistencyPolicy` Schema**
```sql
CREATE TABLE ConsistencyPolicy (
  policy_id VARCHAR(64) PRIMARY KEY,
  service_name VARCHAR(128) NOT NULL,
  default_level VARCHAR(64) CHECK (level IN ('strong', 'eventual', 'quorum')),
  exceptions JSONB,      -- e.g., {"write": ["order-payment"], "read": ["stats"]}
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```
**Example Data:**
```json
{
  "policy_id": "order-service:consistency",
  "service_name": "order-service",
  "default_level": "eventual",
  "exceptions": {
    "write": ["payment"],
    "read": ["recommendations"]
  }
}
```

#### **2. `DataLock` Schema**
```sql
CREATE TABLE DataLock (
  lock_id VARCHAR(64) PRIMARY KEY,
  entity_id VARCHAR(128) NOT NULL,
  lock_version INTEGER NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  locked_by VARCHAR(64),
  consistency_level VARCHAR(64) CHECK (level IN ('strong', 'eventual'))
);
```
**Example Data:**
```json
{
  "lock_id": "user_lock_123",
  "entity_id": "user:123",
  "lock_version": 42,
  "expires_at": "2024-01-01T00:00:00Z",
  "locked_by": "orderservice",
  "consistency_level": "strong"
}
```

#### **3. `EventLog` Schema**
```sql
CREATE TABLE EventLog (
  event_id UUID PRIMARY KEY,
  entity_id VARCHAR(128) NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  payload JSONB NOT NULL,
  version INTEGER NOT NULL,
  consistency_level VARCHAR(64) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (consistency_level) REFERENCES ConsistencyPolicy(level)
);
```
**Example Data:**
```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_id": "order:456",
  "event_type": "item_added",
  "payload": {"item_id": "789", "quantity": 2},
  "version": 3,
  "consistency_level": "eventual"
}
```

---

### **Query Examples**

#### **1. Fetch Consistency Policy for a Service**
```sql
-- Get default policy for 'order-service'
SELECT * FROM ConsistencyPolicy
WHERE service_name = 'order-service';
```
**Response:**
```json
{
  "policy_id": "order-service:consistency",
  "service_name": "order-service",
  "default_level": "eventual",
  "exceptions": { "write": ["payment"] }
}
```

#### **2. Check if an Entity is Locked**
```sql
-- Check if 'order:123' has a strong consistency lock
SELECT * FROM DataLock
WHERE entity_id = 'order:123' AND consistency_level = 'strong';
```
**Response:**
```json
{
  "lock_id": "order_lock_123",
  "entity_id": "order:123",
  "lock_version": 42,
  "expires_at": "2024-01-01T00:00:00Z",
  "consistency_level": "strong"
}
```

#### **3. Apply a Write with Custom Consistency**
```sql
-- Write an event with 'strong' consistency (overrides default)
INSERT INTO EventLog (
  event_id, entity_id, event_type, payload, version, consistency_level
) VALUES (
  gen_random_uuid(),
  'order:456',
  'item_added',
  '{"item_id": "789", "quantity": 2}::jsonb',
  3,
  'strong'
);
```

#### **4. Query Events with Consistency Filter**
```sql
-- Get all events for 'order:456' with strong consistency
SELECT * FROM EventLog
WHERE entity_id = 'order:456' AND consistency_level = 'strong';
```
**Response:**
```json
[
  {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "entity_id": "order:456",
    "event_type": "item_added",
    "payload": {"item_id": "789", "quantity": 2},
    "version": 3,
    "consistency_level": "strong"
  }
]
```

#### **5. Update Consistency Policy**
```sql
-- Temporarily enforce strong consistency for payments
UPDATE ConsistencyPolicy
SET exceptions = '{ "write": ["payment", "order-checkout"] }'
WHERE policy_id = 'order-service:consistency';
```

---

### **Related Patterns**

| **Pattern**               | **When to Use**                                                                                                                                                                                                                     | **Key Interaction with Consistency Tuning**                                                                                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **CQRS**                  | Separate read/write models (e.g., analytics vs. transactions).                                                                                                                                                                     | Use Consistency Tuning to set different consistency levels per model (e.g., `eventual` for analytics, `strong` for transactions).                                                          |
| **Event Sourcing**         | Audit trail via immutable logs.                                                                                                                                                                                                     | Append `consistency_level` to events; replay with targeted consistency.                                                                                                                 |
| **Saga Pattern**           | Long-running transactions across services.                                                                                                                                                                                           | Apply per-step consistency (e.g., `strong` for payments, `eventual` for notifications).                                                                                                   |
| **Compensating Transactions** | Roll back steps in case of failure.                                                                                                                                                                                             | Ensure compensating actions match the original consistency level (e.g., if a write was `strong`, the rollback must also be `strong`).                                                 |
| **Idempotency Keys**       | Prevent duplicate operations (e.g., retries).                                                                                                                                                                                         | Store `consistency_level` in the key to enforce consistency guarantees per idempotent operation.                                                                                       |

---

### **Best Practices**
1. **Default to Eventual Consistency**: Assume eventual consistency unless strong consistency is explicitly required.
2. **Versioning**: Always include a `version` field in events/keys to handle concurrent updates.
3. **Monitor Conflicts**: Log conflict resolutions (e.g., CRDT merges vs. LWW discards) for debugging.
4. **Fallbacks**: Define fallback strategies for failed strong-consistency operations (e.g., retry with eventual).
5. **Document Assumptions**: Clearly label which operations guarantee consistency and which are eventual.

---
**See Also**:
- [Event Sourcing Pattern](link)
- [CQRS Pattern](link)
- [CRDTs for Conflict-Free Replication](link)