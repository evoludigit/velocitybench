---
**[Pattern] Tracing Migration: Reference Guide**

---

### **1. Overview**
The **Tracing Migration** pattern orchestrates the gradual movement of data between two systems (e.g., legacy → modern infrastructure) while maintaining **real-time consistency** and **minimal downtime**. Unlike one-time data loads, this pattern uses **transactional outbox patterns**, **event sourcing**, or **change data capture (CDC)** to track and replay changes bidirectionally. It’s ideal for **high-availability systems**, **microservices**, or **database refactoring** where atomicity across systems is critical.

Key goals:
- **Seamless transition**: Ensure new system state matches the old system at all times.
- **Backward compatibility**: Allow phased adoption without disrupting clients.
- **Resilience**: Support rollback in case of failures.
- **Performance**: Minimize latency by batching or streaming changes.

---

### **2. Schema Reference**
Below are core schemas for tracing migration implementations.

#### **2.1 Core Tables/Collections**
| Schema Name          | Description                                                                 | Fields                                                                                     |
|----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `Migrations`         | Tracks migration state (e.g., progress, errors).                            | `id`, `source_system`, `target_system`, `status` (`PENDING`, `RUNNING`, `COMPLETED`), `created_at`, `updated_at` |
| `OutboundChanges`    | Captures changes from source system (e.g., database logs, event streams).     | `id`, `source_id`, `source_table`, `change_type` (`INSERT`, `UPDATE`, `DELETE`), `payload` (JSON), `processed_at` |
| `InboundChanges`     | Stores changes applied to the target system.                               | `id`, `outbound_change_id` (FK), `target_id`, `target_table`, `applied_at`, `status` (`PENDING`, `AWAITING_REPLAY`) |
| `RetryQueue`         | Manages failed changes for reprocessing.                                   | `id`, `change_id` (FK to `OutboundChanges`), `retry_count`, `next_attempt_at`            |

#### **2.2 Supporting Schemas**
| Schema Name          | Description                                                                 | Fields                                                                                     |
|----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `SystemSyncStatus`   | Monitors real-time sync health (e.g., lag, errors).                         | `system_pair` (e.g., `legacy_db → new_db`), `last_sync_timestamp`, `error_count`, `warning_threshold` |
| `ClientRedirects`    | Routes API calls to the new system after migration completion.               | `legacy_endpoint`, `new_endpoint`, `redirect_status` (`ACTIVE`, `DISABLED`)             |

---
### **3. Implementation Steps**

#### **3.1 Phase 1: Setup**
1. **Instrument Source System**:
   - Deploy a **change data capture (CDC) agent** (e.g., Debezium, AWS DMS) to log changes to `OutboundChanges`.
   - For event-driven systems, subscribe to domain events (e.g., Kafka topics).
   - *Example*: Use AWS DMS for RDS → Aurora PostgreSQL migrations.

2. **Initialize Target System**:
   - Seed initial data via **ETL** (e.g., AWS Glue, Talend) or **batch load**.
   - Deploy a **migration service** to process `OutboundChanges` and update the target.

3. **Enable Dual-Write (Optional)**:
   - Write changes to **both** systems temporarily to ensure consistency before hard-cutover.

#### **3.2 Phase 2: Synchronization**
- **Change Propagation**:
  - The migration service **polling** or **subscribes** to `OutboundChanges`.
  - For each change, it:
    1. Validates the payload (schema, dependencies).
    2. Applies the change to the target system.
    3. Marks records in `InboundChanges` as `APPLIED`.
    4. Updates `SystemSyncStatus` with metrics (e.g., lag time).

- **Conflict Resolution**:
  - Use **last-write-wins**, **manual review**, or **automated merging** (e.g., for `UPDATE` conflicts).
  - Log conflicts in `OutboundChanges` with a `conflict_resolved_at` timestamp.

- **Retries**:
  - Failed changes move to `RetryQueue` with exponential backoff.

#### **3.3 Phase 3: Validation & Cutover**
1. **Health Checks**:
   - Run **end-to-end tests** (e.g., compare `InboundChanges` with source via sample queries).
   - Verify `SystemSyncStatus` shows `error_count = 0` and `lag < threshold`.

2. **Cutover**:
   - Update `ClientRedirects` to route traffic to the new system.
   - Disable writes to the legacy system (e.g., via API gating).

3. **Final Sync**:
   - Process any remaining `OutboundChanges` before shutting down the source.
   - Archive the source system (or keep it read-only for auditing).

---
### **4. Query Examples**
#### **4.1 Check Migration Status**
```sql
-- SQL (PostgreSQL)
SELECT
    status,
    COUNT(*) as pending_changes
FROM Migrations
WHERE status = 'RUNNING'
GROUP BY status;
```

#### **4.2 Identify Stalled Changes**
```sql
-- SQL (for OutboundChanges not processed)
SELECT
    source_table,
    COUNT(*) as stalled_count,
    MAX(created_at) as last_change_time
FROM OutboundChanges oc
LEFT JOIN InboundChanges ic ON oc.id = ic.outbound_change_id
WHERE ic.id IS NULL
GROUP BY source_table
ORDER BY stalled_count DESC;
```

#### **4.3 Monitor Sync Lag**
```sql
-- Query to calculate lag between source and target
WITH latest_source AS (
    SELECT MAX(created_at) as last_source_time
    FROM OutboundChanges
    WHERE source_table = 'users'
),
latest_target AS (
    SELECT MAX(applied_at) as last_target_time
    FROM InboundChanges
    WHERE target_table = 'users'
)
SELECT
    (EXTRACT(EPOCH FROM (latest_source.last_source_time - latest_target.last_target_time)) / 60) as lag_minutes
FROM latest_source, latest_target;
```

#### **4.4 Retry Failed Changes**
```python
# Pseudocode for retry logic (Python + SQLAlchemy)
def retry_failed_changes():
    from sqlalchemy import text
    engine = create_engine("postgresql://...")
    with engine.connect() as conn:
        retry_batch = conn.execute(text("""
            SELECT id, retry_count
            FROM RetryQueue
            WHERE next_attempt_at <= NOW()
            LIMIT 100
        """))
        for change_id, retry_count in retry_batch:
            # Reprocess the change (e.g., via message queue)
            process_outbound_change(change_id)
            conn.execute(text(f"""
                UPDATE RetryQueue
                SET retry_count = {retry_count + 1},
                    next_attempt_at = NOW() + INTERVAL '5 seconds'
                WHERE id = {change_id}
            """))
```

---
### **5. Related Patterns**
| Pattern Name               | Description                                                                 | When to Use                                                                 |
|----------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Event Sourcing**         | Store all state changes as a sequence of events.                           | When historical auditing or replayability is critical.                      |
| **Transactional Outbox**   | Buffer database changes for async processing.                               | For event-driven architectures with ACID compliance.                       |
| **CQRS (Command Query Separation)** | Separate read/write models for performance.                                | When read-heavy systems need fast queries without write bottlenecks.         |
| **Database Sharding**      | Split data across multiple instances.                                       | Scale horizontally for high-throughput writes.                              |
| **Feature Flags**          | Gradually roll out new system features.                                     | Test new functionality without affecting all users simultaneously.           |
| **Saga Pattern**           | Coordinate distributed transactions across services.                       | For long-running workflows spanning multiple microservices.                  |

---
### **6. Best Practices**
1. **Idempotency**:
   - Design `OutboundChanges` to be replayable (e.g., include a `version` or `transaction_id`).

2. **Monitoring**:
   - Alert on `SystemSyncStatus` anomalies (e.g., `error_count > 0` or `lag > 5 minutes`).

3. **Backpressure**:
   - Throttle `OutboundChanges` consumption if the target system is slow.

4. **Data Validation**:
   - Use **schema registries** (e.g., Confluent Schema Registry) for JSON payloads.

5. **Cutover Safety**:
   - Keep the legacy system in **read-only mode** post-cutover for a grace period.

6. **Cleanup**:
   - Archive old data after confirmation (e.g., via `TRUNCATE` or CDC cleanup tools).

---
### **7. Anti-Patterns to Avoid**
- **Blocking Writes**: Don’t freeze the source system during migration (use CDC or dual-write).
- **Ignoring Conflicts**: Unresolved conflicts can corrupt data; prioritize manual review for critical systems.
- **Over-Batching**: Large batches may time out or lose context (e.g., database transactions).
- **No Rollback Plan**: Always define a fallback to revert changes (e.g., restore source system).

---
### **8. Tools & Libraries**
| Category               | Tools/Libraries                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **CDC**                | Debezium, AWS DMS, Kafka Connect, Debezium Kafka Connectors                      |
| **Event Streaming**    | Apache Kafka, Amazon MSK, Google Pub/Sub                                         |
| **ETL**                | AWS Glue, Talend, Apache NiFi, Airbyte                                          |
| **Event Sourcing**     | EventStoreDB, Axon Framework, EventSourced (JavaScript)                          |
| **Orchestration**      | Kubernetes CronJobs, AWS Step Functions, Apache Airflow                            |
| **Monitoring**         | Prometheus + Grafana, Datadog, New Relic                                        |

---
### **9. Example Architecture**
```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│             │       │             │       │                 │
│  Legacy DB  ├──────▶ OutboundChanges ├──────▶ Migration     │
│             │       │             │       │  Service        │
└─────────────┘       └─────────────┘       └──────────┬──────┘
                                     ▲               │
                                     │               ▼
                                     │      ┌─────────────┐
                                     │      │ InboundChanges│
                                     │      └─────────────┘
                                     │
                                     ▼
                          ┌─────────────────┐
                          │  Target System   │
                          └─────────────────┘
```
**Key Components**:
1. Legacy DB → CDC Agent → `OutboundChanges` (streaming).
2. Migration Service → Reads `OutboundChanges` → Applies to Target → Writes to `InboundChanges`.
3. Monitoring dashboards track `SystemSyncStatus`.

---
**References**:
- [Debezium Documentation](https://debezium.io/documentation/reference/)
- [AWS DMS Migration Guide](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)
- *Domain-Driven Design* (Eric Evans) – For event-sourcing principles.