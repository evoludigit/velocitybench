# **[Pattern] Cascade Operation Tracking Reference Guide**

---
## **Overview**
The **Cascade Operation Tracking** pattern ensures that when a mutation (e.g., update, delete) affects downstream entities due to data relationships (e.g., one-to-many, many-to-many), all changes—both primary and cascaded—are systematically logged in an **audit trail** (change log). This approach improves observability, compliance, and rollback capabilities by capturing the full impact of operations.

This pattern is particularly useful in systems with complex relationships (e.g., e-commerce order systems, inventory management) where a single update may trigger changes across multiple tables or microservices.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Primary Entity**     | The origin entity (e.g., `Customer`) that initiates the mutation.                                                                                                                                        |
| **Cascaded Entity**    | A related entity (e.g., `Order`, `Address`) whose state is modified indirectly due to the primary mutation.                                                                                             |
| **Change Log**         | A centralized audit table tracking all mutations (user, timestamp, affected fields, previous/next state).                                                                                        |
| **Trigger-Based**      | Cascaded operations are logged via database triggers, application-level event listeners, or CDC (Change Data Capture) pipelines.                                           |
| **Transactional**      | All changes (primary + cascaded) must be logged within the same transaction to maintain consistency.                                                                    |

---

## **Schema Reference**
### **Core Tables**
| Table                | Description                                                                                                                                                   | Example Fields                                                                                     |
|----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **`primary_entities`** | Stores the original entity (e.g., `Customers`, `Products`).                                                                                               | `id (PK)`, `name`, `created_at`, `updated_at`, `deleted_at`                                        |
| **`cascaded_entities`** | Stores related entities (e.g., `Orders`, `Order_Items`).                                                                                                 | `id (PK)`, `primary_entity_id (FK)`, `status`, `quantity`, `updated_by`                           |
| **`change_log`**     | Audit trail for all mutations (primary + cascaded).                                                                                                      | `log_id (PK)`, `entity_type`, `entity_id`, `action` (`CREATE/UPDATE/DELETE`), `old_value`, `new_value`, `changed_at`, `changed_by` |

---
### **Relationships**
1. **Primary → Cascaded**:
   - One-to-Many (e.g., `Customer` → `Orders`).
   - Many-to-Many (e.g., `Product` ↔ `Order_Items` via a junction table).

2. **Change Log**:
   - Linked to both `primary_entities` and `cascaded_entities` via `entity_id` and `entity_type`.

---
### **Example Schema (SQL)**
```sql
-- Primary entity table
CREATE TABLE Customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Cascaded entity table
CREATE TABLE Orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES Customers(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Change log table
CREATE TABLE change_log (
    log_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,  -- 'Customers', 'Orders', etc.
    entity_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL,       -- 'CREATE', 'UPDATE', 'DELETE'
    old_value JSONB,                   -- Previous state (for UPDATE/DELETE)
    new_value JSONB,                   -- New state (for CREATE/UPDATE)
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by VARCHAR(50)             -- User/process ID
);

-- Trigger for logging updates to Customers
CREATE OR REPLACE FUNCTION log_customer_change()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO change_log (
            entity_type, entity_id, action, old_value, new_value, changed_by
        ) VALUES (
            'Customers', NEW.id, 'UPDATE',
            to_jsonb(OLD),
            to_jsonb(NEW),
            current_user
        );
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO change_log (
            entity_type, entity_id, action, old_value, new_value, changed_by
        ) VALUES (
            'Customers', OLD.id, 'DELETE',
            to_jsonb(OLD),
            NULL,
            current_user
        );
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_customer_update
AFTER UPDATE OR DELETE ON Customers
FOR EACH ROW EXECUTE FUNCTION log_customer_change();
```

---

## **Query Examples**
### **1. Log a Primary Mutation (Customer Update)**
```sql
-- Update a customer (triggers change_log)
UPDATE Customers
SET name = 'Updated Name', email = 'new@example.com'
WHERE id = 123;
```
**Result in `change_log`**:
```json
{
  "entity_type": "Customers",
  "entity_id": 123,
  "action": "UPDATE",
  "old_value": {"name": "Old Name", "email": "old@example.com"},
  "new_value": {"name": "Updated Name", "email": "new@example.com"}
}
```

### **2. Log Cascaded Mutations (Order Status Change)**
If updating a `Customer` triggers an `Orders` status change (e.g., via application logic):
```python
def update_customer_status(customer_id, new_status):
    customer = Customers.query.get(customer_id)
    customer.status = new_status
    db.session.commit()

    # Log order cascades (if any)
    orders = Orders.query.filter_by(customer_id=customer_id).all()
    for order in orders:
        change_log = ChangeLog(
            entity_type="Orders",
            entity_id=order.id,
            action="UPDATE",
            old_value={"status": order.status},
            new_value={"status": "active"},
            changed_by=current_user
        )
        db.session.add(change_log)
    db.session.commit()
```

### **3. Retrieve Full Change History for an Entity**
```sql
-- Get all changes for a customer (primary + cascaded)
SELECT *
FROM change_log
WHERE entity_type = 'Customers' OR (
    entity_type = 'Orders' AND entity_id IN (
        SELECT id FROM Orders WHERE customer_id = 123
    )
)
ORDER BY changed_at DESC;
```

### **4. Rollback a Failed Cascade**
```sql
-- Undo all changes for an order batch
BEGIN;
-- Revert Orders
UPDATE Orders
SET status = (SELECT old_value->>'status' FROM change_log WHERE entity_id = Orders.id AND action = 'UPDATE' AND entity_type = 'Orders'),
    updated_at = (SELECT changed_at FROM change_log WHERE entity_id = Orders.id AND action = 'UPDATE' AND entity_type = 'Orders')
WHERE id IN (SELECT entity_id FROM change_log WHERE entity_type = 'Orders' AND action = 'UPDATE' AND changed_at > '2023-10-01');

-- Revert Change Log updates
DELETE FROM change_log
WHERE entity_type = 'Orders' AND changed_at > '2023-10-01';
COMMIT;
```

---

## **Implementation Strategies**
| **Strategy**         | **Pros**                                                                 | **Cons**                                                                 | **Best For**                                  |
|----------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|-----------------------------------------------|
| **Database Triggers** | Automatic, no app code changes.                                         | Limited to specific DB, may cause performance overhead.                  | Simple CRUD apps, single Database systems.   |
| **Application Logic** | Full control over cascades (e.g., business rules).                    | Requires explicit code for each relationship.                           | Complex business logic, microservices.       |
| **CDC Pipelines**    | Scales well, works across services (e.g., Debezium).                   | High setup complexity.                                                  | Distributed systems, event-driven architectures. |

---

## **Performance Considerations**
1. **Optimize Logging**:
   - Use **JSONB** for flexible change tracking (e.g., `old_value`, `new_value`).
   - Add **indexes** on `(entity_type, entity_id, changed_at)` for fast queries.
   - Batch log entries for high-throughput systems.

2. **Circuit Breakers**:
   - If logging fails, implement a **dead-letter queue** to retry later.

3. **Selective Logging**:
   - Exclude trivial fields (e.g., `updated_at`) or use a **diff algorithm** to log only changed fields.

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Event Sourcing](https://martinfowler.com/eaaT/dontUseIt.html)** | Stores state changes as a sequence of events (immutable log).                                                                                                                                                        | Systems needing full auditability and replayability (e.g., financial transactions).            |
| **[Open/Closed Principle (OCP)](https://en.wikipedia.org/wiki/Open–closed_principle)** | Design cascades to be extensible without modifying existing code.                                                                                                                                            | Adding new entity types or cascade rules without refactoring.                                      |
| **[CQRS](https://martinfowler.com/bliki/CQRS.html)** | Separates read/write models; change logs feed read models.                                                                                                                                                 | High-concurrency systems with complex queries (e.g., analytics dashboards).                          |
| **[Saga Pattern](https://microservices.io/patterns/data-management/saga.html)** | Coordinates distributed transactions via compensating actions (useful if cascades span services).                                                                                                                          | Microservices where transactions span multiple services.                                             |
| **[Immutable Audit Trail](https://www.percona.com/blog/2018/05/24/immutable-audit-logging/)** | Stores logs in a write-once format (e.g., blockchain-like structure).                                                                                                                                           | Regulatory compliance (e.g., healthcare, finance) where tamper-proofing is critical.               |

---

## **Anti-Patterns to Avoid**
1. **Logging Everything**:
   - Avoid storing unnecessary data (e.g., large binary fields). Use **diff tracking** or **checksums** for large objects.

2. **Circular Dependencies**:
   - Ensure cascades don’t create infinite loops (e.g., `Customer → Order → Customer`).

3. **Tight Coupling**:
   - Don’t hardcode cascade logic in entities; use **polymorphism** or **event buses** (e.g., Kafka) for loose coupling.

4. **Ignoring Performance**:
   - Logging every change can bottleneck write operations. Use **sampling** or **threshold-based logging** for high-volume systems.

---
## **Example Workflow (E-Commerce)**
1. **User Update**:
   - A buyer updates their `Address` (primary entity).
   - The system **cascades** this to all linked `Orders` (updating shipping details).
   - Both changes are logged in `change_log`.

2. **Audit Query**:
   - A support agent queries the `change_log` to see all address changes for a customer.

3. **Rollback**:
   - If the address update causes a payment failure, the system **reverts** the `Orders` and relogs the changes.

---
## **Tools & Libraries**
| **Tool/Library**               | **Purpose**                                                                                                                                                     | **Example Use Case**                                  |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Debezium**                     | CDC for real-time change streams (Kafka).                                                                                                                          | Distributed microservices with cross-service audits. |
| **Liquibase/Flyway**             | Schema migrations with audit-friendly changes.                                                                                                                   | Version-controlled database changes.                  |
| **Apache Kafka + Schema Registry** | Stream processing for complex cascades.                                                                                                                          | Real-time inventory updates across warehouses.        |
| **PostgreSQL `pgAudit`**         | Extensive logging for SQL operations.                                                                                                                          | Compliance-heavy applications.                       |
| **AWS DMS / Azure Data Factory** | ETL with change tracking for cloud migrations.                                                                                                                 | Migrating legacy systems with full audit trails.      |

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                                                                 | **Solution**                                                                                     |
|-------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Duplicate log entries**           | Trigger fired multiple times due to cascading deletes.                          | Use `EXISTS` checks in triggers or deduplicate logs.                                           |
| **Performance degradation**         | Logging adds latency to writes.                                                | Batch log inserts or use asynchronous logging (e.g., Kafka).                                     |
| **Missing cascaded logs**           | Application missed logging a related entity.                                    | Implement **pre-commit hooks** or **event listeners**.                                          |
| **Inconsistent rollback**           | Compensating actions fail mid-transaction.                                     | Use **sagas** or **two-phase commit** for distributed rollbacks.                                 |

---
## **Further Reading**
1. **Patterns of Enterprise Application Architecture** – Martin Fowler ([Event Sourcing](https://martinfowler.com/eaaT/dontUseIt.html)).
2. **Database-Driven Apps** – Martin Fowler ([Auditing](https://martinfowler.com/eaaCatalog/auditing.html)).
3. **CDC with Debezium** – [Debezium Documentation](https://debezium.io/documentation/reference/).
4. **Immutable Audit Logging** – [Percona Blog](https://www.percona.com/blog/2018/05/24/immutable-audit-logging/).