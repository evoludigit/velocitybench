---
# **[Pattern] Consistency Migration Reference Guide**

---

## **1. Overview**
The **Consistency Migration** pattern addresses the challenge of transitioning data systems while maintaining data consistency between source and target systems. This is critical during refactors, schema migrations, or system upgrades where partial availability is unavoidable. The pattern ensures that while one system (e.g., a new database) remains operational, the other (e.g., an old system) is phased out safely. Key strategies include:
- **Dual-write** (sending updates to both systems).
- **Eventual consistency** (propagating changes asynchronously).
- **Metadata flags** (tracking migration state to avoid conflicts).
- **Read-through/proxy** (resolving queries via the target system while the source remains available).

This guide outlines implementation details, schema requirements, query patterns, and related strategies for a seamless migration.

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Source System**      | The "old" system being phased out (e.g., legacy database, backend service).                                                                                           |
| **Target System**      | The "new" system (e.g., modern database, microservice) that will eventually replace the source.                                                                   |
| **Dual-Write**         | Writing data changes to *both* systems during migration to ensure consistency.                                                                                       |
| **Eventual Consistency** | Changes propagate from source to target asynchronously; temporary divergence is tolerated.                                                                    |
| **Metadata Flag**      | A flag (e.g., `migrated_at`) marking records in the source system as ready for eventual removal.                                                                 |
| **Read-Through**       | Redirecting queries to the target system via a proxy/load balancer while the source remains available for writes.                                                     |
| **Migration Window**   | A defined timeframe during which both systems operate in dual-write mode. Afterward, the source system is decommissioned.                                         |

---

## **3. Schema Reference**

### **Core Tables/Collections**
The schema must support *dual-write* and *migration tracking*. Below are essential fields:

#### **Source System Table (Example: `legacy_customers`)**
| Field               | Type          | Description                                                                                                                                                     | Example                          |
|---------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `id`                | UUID/PK       | Primary key (must match target system).                                                                                                                     | `550e8400-e29b-41d4-a716-446655440000` |
| `migrated_at`       | TIMESTAMP     | When the record was migrated to the target; `NULL` if not yet migrated.                                                                                       | `2023-10-01 14:30:00`            |
| `deprecated`        | BOOLEAN       | `TRUE` if the record is no longer writable in the source; used to enforce read-only mode during migration.                                                   | `FALSE`                          |
| `sync_status`       | ENUM          | State of migration: `pending`, `in_progress`, `completed`, or `failed`.                                                                                       | `completed`                      |

---

#### **Target System Table (Example: `new_customers`)**
| Field          | Type          | Description                                                                                                                                                     | Example                          |
|----------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `id`           | UUID/PK       | Must match `legacy_customers.id` for consistency.                                                                                                          | Same as source                    |
| `created_at`   | TIMESTAMP     | When the record was *first* created (source system timestamp).                                                                                                | `2023-09-15 08:15:00`            |
| `updated_at`   | TIMESTAMP     | Last update timestamp (may lag behind source during dual-write).                                                                                            | `2023-10-02 09:45:00`            |
| `migration_id` | UUID/FK       | Reference to a `migrations` audit log (optional).                                                                                                          | `60f8bc9d-...`                   |

---

#### **Audit Log Table (Example: `migrations`)**
| Field          | Type          | Description                                                                                                                                                     | Example                          |
|----------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------|
| `id`           | UUID/PK       | Unique ID for tracking individual migration jobs.                                                                                                           | `60f8bc9d-...`                   |
| `source_id`    | UUID/FK       | Reference to the source record being migrated.                                                                                                             | `550e8400-e29b-41d4-a716-446655440000` |
| `target_id`    | UUID/FK       | Reference to the *new* record in the target system.                                                                                                       | Same as `source_id`              |
| `status`       | ENUM          | `queued`, `in_progress`, `completed`, `failed`.                                                                                                          | `completed`                      |
| `started_at`   | TIMESTAMP     | When migration began.                                                                                                                                       | `2023-10-01 15:00:00`            |
| `completed_at` | TIMESTAMP     | When migration finished (or `NULL` if pending).                                                                                                            | `2023-10-01 15:05:00`            |

---

### **Indexes for Performance**
| Table               | Index Name               | Columns            | Purpose                                                                                     |
|---------------------|--------------------------|--------------------|---------------------------------------------------------------------------------------------|
| `legacy_customers`  | `idx_migrated_status`    | `migrated_at`      | Speed up queries filtering by migration status (e.g., `WHERE migrated_at IS NULL`).          |
| `new_customers`     | `idx_id_created_at`      | `id`, `created_at` | Optimize joins between source and target tables.                                             |
| `migrations`        | `idx_source_status`      | `source_id`, `status` | Quickly locate failed/missing migrations.                                                  |

---

## **4. Query Examples**

### **4.1. Dual-Write Workflow**
**Scenario**: Insert/Update a record in both systems atomically.

#### **Pseudocode (Transaction)**
```sql
-- Start transaction
BEGIN TRANSACTION;

-- Update source system
INSERT INTO legacy_customers (id, name, email)
VALUES (UUID(), 'John Doe', 'john@example.com');

-- Update target system
INSERT INTO new_customers (id, name, email, created_at)
VALUES (UUID(), 'John Doe', 'john@example.com', NOW());

-- Mark migration as started in audit log
INSERT INTO migrations (id, source_id, status, started_at)
VALUES (UUID(), UUID(), 'in_progress', NOW());

COMMIT;
```

**Note**: Use distributed transactions (e.g., Saga pattern) if databases are separate. Fall back to **eventual consistency** if atomicity fails.

---

### **4.2. Read-Through Implementation**
**Scenario**: Query the *new* system while the *old* system remains available for writes.

#### **Proxy Logic (Pseudocode)**
```python
def get_customer(customer_id):
    # Check if source system is fully migrated
    legacy_record = db_source.query(legacy_customers, id=customer_id)
    if legacy_record.deprecated:
        return db_target.query(new_customers, id=customer_id)
    else:
        # Fallback to source if not yet migrated
        return legacy_record
```

---

### **4.3. Migration Status Checks**
**Query to find records pending migration**:
```sql
SELECT id, name
FROM legacy_customers
WHERE migrated_at IS NULL
LIMIT 1000;  -- Batch processing
```

**Query to resume failed migrations**:
```sql
SELECT source_id, started_at
FROM migrations
WHERE status = 'failed'
ORDER BY started_at ASC;
```

---

### **4.4. Dual-Write Validation**
**Check for divergence between source and target**:
```sql
-- Records in source *not* in target
SELECT lc.id, lc.name
FROM legacy_customers lc
LEFT JOIN new_customers nc ON lc.id = nc.id
WHERE nc.id IS NULL;

-- Records in target *not* in source (edge case)
SELECT nc.id, nc.name
FROM new_customers nc
LEFT JOIN legacy_customers lc ON nc.id = lc.id
WHERE lc.id IS NULL;
```

---

## **5. Implementation Strategies**

### **5.1. Dual-Write Options**
| Strategy               | Pros                                      | Cons                                      | Best For                          |
|------------------------|-------------------------------------------|-------------------------------------------|-----------------------------------|
| **Saga Pattern**       | Works with distributed systems.          | Complex to implement.                     | Microservices                     |
| **Eventual Consistency**| Simpler, tolerates lag.                  | Temporary divergence possible.             | High-traffic systems              |
| **Transaction Log Replay** | Atomic if source/target are co-located. | Performance overhead.                     | Monolithic systems                |

---

### **5.2. Migration Phases**
1. **Pre-Migration (Setup)**
   - Deploy read-through proxy.
   - Enable dual-write for critical tables.
   - Set up audit logging.

2. **During Migration**
   - Write to both systems (dual-write).
   - Batch-migrate historical data (e.g., nightly jobs).
   - Monitor for divergence.

3. **Post-Migration**
   - Deprecate source system writes (`deprecated = TRUE`).
   - Redirect all reads to target.
   - Sunset source system after validation.

---

## **6. Error Handling**
| Issue                  | Mitigation Strategy                                                                 |
|------------------------|------------------------------------------------------------------------------------|
| **Data Divergence**    | Use reconciliation jobs to sync missing/changed records.                           |
| **Failed Transactions**| Retry or mark as `failed` in `migrations` log; alert team.                         |
| **Performance Lag**    | Increase batch sizes or use async queues (e.g., Kafka).                             |
| **Schema Mismatches**  | Use a transformation layer (e.g., ETL) before writing to the target.                |

---

## **7. Related Patterns**
| Pattern                     | Description                                                                                                                                                     | When to Use                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| **Saga Pattern**            | Manage distributed transactions via compensating actions.                                                                                                   | Microservices with eventual consistency. |
| **CQRS**                    | Separate read/write models for scalability during migration.                                                                                                | High-read-volume systems.            |
| **Event Sourcing**          | Track state changes via events for precise migration.                                                                                                      | Audit-heavy systems.                 |
| **Database Sharding**       | Distribute load across systems during migration.                                                                                                           | Horizontal scaling needs.            |
| **Feature Flags**           | Gradually roll out target system while keeping source available.                                                                                           | Canary deployments.                  |

---
## **8. Anti-Patterns**
- **Cutover Without Validation**: Never decommission the source system until all data is confirmed migrated.
- **Blocking Writes**: Avoid locking the source system during migration (use async queues).
- **Ignoring Divergence**: Regularly check for and resolve inconsistencies.
- **Overcomplicating Dual-Write**: Start simple (e.g., batch jobs) before adding complexity.

---
## **9. Tools & Libraries**
| Category               | Tools/Libraries                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **ETL/Transformations**| Apache NiFi, Debezium, Airbyte                                                   |
| **Async Queues**       | Kafka, RabbitMQ, AWS SQS                                                         |
| **Proxy Layer**        | NGINX, Envoy, or custom service mesh                                              |
| **Monitoring**         | Prometheus + Grafana, Datadog                                                    |
| **Distributed TX**     | 2-phase commit (limited), Saga pattern (recommended)                             |

---
## **10. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│  Client     ├────┤  Read-     ├────┤  Target     ├────┤  Source     │
│             │    │  Through    │    │  System     │    │  System     │
│             │    │  Proxy      │    │ (New DB)    │    │ (Legacy DB) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲            ▲                       ▲                       ▲
       │            │                       │                       │
       │            │                       │                       │
┌──────┴─────┐   ┌──────────┴─────┐        │                       │
│             │   │                 │        │                       │
│  Dual-Write │   │  Async       │        │                       │
│  (Write to  │   │  Migration   │        │                       │
│   Both Sys- │   │  Jobs)       │   ┌────┴───────┐               │
│   tems)     │   │                 │   │           │               │
└─────────────┘   └───────────────┘   │ Migration │               │
                                      │  Log      │               │
                                      └───────────┘               │
                                                            │
                                                            ▼
                                                  ┌─────────────┐
                                                  │              │
                                                  │  Monitoring  │
                                                  │  (Prometheus │
                                                  │   + Alerts)  │
                                                  └─────────────┘
```