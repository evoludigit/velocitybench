---

# **[Pattern] Scaling Migration Reference Guide**

---

## **Overview**
**Scaling Migration** is a database refactoring pattern that ensures high availability, minimal downtime, and consistent performance during large-scale database schema or data transformations. This pattern is critical for systems where data volumes grow exponentially (e.g., SaaS applications, IoT platforms) or when migrating to cloud-native architectures (e.g., Kubernetes, serverless databases).

The pattern balances **zero-downtime requirements**, **data consistency**, and **scalable throughput** by:
- **Phasing migrations** across shards, regions, or tenants.
- **Decoupling writes and reads** using dual-write or dual-read approaches.
- **Leveraging asynchronous processing** (e.g., queues, event sourcing) to defer non-critical transformations.
- **Monitoring and validation** to detect drift or failures before full rollout.

**When to use this pattern:**
✔ Migrating from a monolithic database to sharded/multi-region storage.
✔ Upgrading schema with backward-incompatible changes (e.g., adding required columns).
✔ Transitioning from on-premises to cloud databases (e.g., PostgreSQL → Aurora).
✔ Handling high-throughput writes (e.g., 10K+ TPS) during data model changes.

**When to avoid:**
✗ Migrating small, low-volume databases with simple schemas.
✗ Changes requiring immediate global consistency (use *two-phase commit* instead).
✗ Teams without observability tools for migration tracking.

---

## **Schema Reference**
The following tables define core components and their relationships.

### **1. Core Components**
| **Component**               | **Description**                                                                 | **Example Technologies**                          |
|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------------|
| **Source Database**         | Original database being migrated.                                                | PostgreSQL, MySQL, MongoDB                         |
| **Target Database**         | Destination database post-migration.                                            | Aurora, Cosmos DB, Cassandra                       |
| **Shadow Database**         | Read-only replica of the source for validation (optional but recommended).     | Same as target or a lightweight clone            |
| **Migration Service**       | Orchestrates data transfer (synchronous/asynchronous).                          | AWS DMS, Debezium, custom ETL pipelines           |
| **Validation Service**      | Checks data consistency between source and target.                              | Custom scripts, tools like Sqitch, Flyway        |
| **Queue System**            | Handles asynchronous writes/transformations (e.g., Kafka, RabbitMQ).           | Kafka, AWS SQS                                    |
| **Monitoring Dashboard**    | Tracks migration progress, errors, and performance metrics.                     | Prometheus + Grafana, Datadog, CloudWatch         |

---

### **2. Key Tables (Example Data Model)**
Assumes a **user profile migration** from a legacy system to a cloud database.

| **Table**            | **Source Schema**                          | **Target Schema**                          | **Migration Strategy**                     |
|----------------------|--------------------------------------------|--------------------------------------------|--------------------------------------------|
| `users`              | `id (PK), name, email, signup_date`        | `id (PK), name, email, signup_date, last_login` | **Add column** + async fill via queue.    |
| `user_logins`        | N/A                                        | `id (FK), login_time, ip_address`          | **New table** + backfill from logs.        |
| `preferences`        | `user_id (FK), setting_key, setting_value` | Same, but adds `updated_at (indexed)`        | **Schema change** + data reprocessing.     |

---

## **Implementation Details**
### **1. Phase 1: Preparation**
- **Assessment**:
  - Audit schema complexity (joins, triggers, stored procedures).
  - Estimate data volume and transfer time (e.g., 10GB/hour vs. 100GB/hour).
  - Define **SLA targets** (e.g., 99.9% uptime, <500ms latency drift).
- **Tools**:
  - Use **DMS (Database Migration Service)** for AWS or **Flyway/Sqitch** for schema sync.
  - Set up **shadow database** for validation (read-only clone).

### **2. Phase 2: Dual-Write Deployment**
Deploy a **dual-write** system where writes go to **both source and target** temporarily. This ensures no data loss during cutover.

**Architecture**:
```
[Client App] → [Source DB] ← [Migration Service] → [Target DB]
               ↑ (optional) ↓
             [Shadow DB]
```

**Implementation Steps**:
1. **Route writes to both databases**:
   - Modify application to write to **both** source and target (e.g., using database sharding logic).
   - For async writes (e.g., Kafka), deploy a **transformer service** to normalize data before target writes.
2. **Resolve conflicts**:
   - Use **timestamp-based resolution** (last write wins) or **application-specific rules**.
   - Example: For `user_logins`, prioritize target writes if they include `last_login`.

### **3. Phase 3: Asynchronous Backfilling**
For large historical data (e.g., archived logs), use **async processing**:
- **Queue-based backfill**:
  ```mermaid
  sequenceDiagram
    participant Client
    participant MigrationService
    participant TargetDB
    participant AsyncWorker

    Client->>MigrationService: Enqueue backfill job
    MigrationService->>AsyncWorker: Process batch (e.g., 1M records)
    AsyncWorker->>TargetDB: Write batch
  ```
- **Incremental sync**:
  - Use **CDC (Change Data Capture)** tools like Debezium to stream changes from source to target.
  - Example Debezium configuration for PostgreSQL:
    ```yaml
    connectors:
      postgres-connector:
        tasks.max: 1
        database.hostname: source-db
        database.port: 5432
        database.user: migrator
        database.password: "password"
        database.dbname: legacy_db
        table.include.list: "users,user_logins"
        plugin.name: pgoutput
    ```

### **4. Phase 4: Cutover**
- **Test cutover in staging**:
  - Simulate a **hard cutover** (switch all reads to target) for 1 hour.
  - Verify **read consistency** (e.g., `SELECT * FROM users WHERE id = 1` returns identical results).
- **Execute production cutover**:
  1. **Route reads to target** (update DNS/resolver or app config).
  2. **Monitor drift**: Use tools like [pgMustard](https://github.com/eulerto/pgmustard) for PostgreSQL to detect schema/data mismatches.
  3. **Final validation**: Run a **full data diff** (e.g., `EXCEPT` in SQL or custom scripts).

### **5. Phase 5: Validation & Rollback Plan**
- **Validation**:
  - **Statistical checks**: Compare row counts, averages (e.g., `AVG(user_age)`).
  - **Business logic tests**: Query target data to ensure reported metrics match (e.g., "Total active users").
  - **Automated alerts**: Fail if drift exceeds threshold (e.g., 0.5% data mismatch).
- **Rollback Plan**:
  - Pre-script a **failback** to source if target fails validation.
  - Example rollback command:
    ```sql
    -- Disable target writes
    UPDATE config SET is_active = false WHERE name = 'target_db';

    -- Re-enable source writes
    UPDATE config SET is_active = true WHERE name = 'source_db';
    ```

---

## **Query Examples**
### **1. Dual-Write Schema Sync**
**Source Database (PostgreSQL)**:
```sql
-- Create target-compatible schema in source
CREATE TABLE users_target (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    signup_date TIMESTAMP,
    last_login TIMESTAMP DEFAULT NULL
);

-- Fill target columns with NULLs (async fill later)
INSERT INTO users_target (id, name, email, signup_date)
SELECT id, name, email, signup_date FROM users;
```

### **2. Conflict Resolution for Last Write**
**Target Database (MongoDB)**:
```javascript
// Use $merge with conflict resolution
db.users.$merge({
  on: "email",
  whenMatched: {
    updateOne: {
      filter: { email: "$email" },
      update: {
        $set: {
          last_login: new Date(),  // Overwrite if target has newer data
          metadata: { updated_by: "migration_service" }
        }
      }
    }
  },
  whenNotMatched: { insert: true }
});
```

### **3. CDC-Based Incremental Sync (Debezium)**
**Kafka Connect Config**:
```json
{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "source-db",
    "database.port": "5432",
    "database.user": "migrator",
    "database.password": "secret",
    "database.dbname": "legacy_db",
    "table.include.list": "users",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState"
  }
}
```

### **4. Validation Query (SQL)**
**Check Data Consistency**:
```sql
-- Compare row counts
SELECT
    (SELECT COUNT(*) FROM source_db.users) AS source_count,
    (SELECT COUNT(*) FROM target_db.users) AS target_count,
    (source_count - target_count) AS diff;

-- Check last_login consistency (for migrated rows)
SELECT
    s.id,
    s.last_login AS source_last_login,
    t.last_login AS target_last_login
FROM source_db.users s
FULL OUTER JOIN target_db.users t ON s.id = t.id
WHERE s.last_login IS DISTINCT FROM t.last_login;
```

---

## **Related Patterns**
| **Pattern**                | **Description**                                                                 | **When to Use Together**                          |
|----------------------------|---------------------------------------------------------------------------------|---------------------------------------------------|
| **Dual-Write**             | Write to both source and target during migration.                               | Mandatory for zero-downtime cuts.                 |
| **Event Sourcing**         | Store state changes as immutable events for replayable migrations.               | Use when historical data reconstruction is needed.|
| **Schema Evolution**       | Gradually update schema (e.g., add columns with defaults).                      | Pair with async backfilling.                     |
| **CQRS**                   | Separate read (target) and write (source) models.                                | Ideal for high-read-load migrations.             |
| **Database Sharding**      | Split data across multiple instances for horizontal scaling.                     | Pre-migration step to enable parallel transfers. |
| **Feature Flags**          | Gradually roll out new schema features to users.                                 | Combine with dual-write for safe rollouts.       |
| **Chaos Engineering**      | Test failure scenarios (e.g., network partitions) during migration.            | Validate rollback resilience.                    |

---

## **Anti-Patterns & Pitfalls**
1. **Big Bang Migration**:
   - ❌ **Problem**: Cutover all writes at once leads to downtime or data loss.
   - ✅ **Fix**: Use phased cutovers with dual-write.

2. **Ignoring Validation**:
   - ❌ **Problem**: Skipping data consistency checks results in silently corrupted data.
   - ✅ **Fix**: Automate diff checks (e.g., `pgMustard` for PostgreSQL).

3. **Overloading the Target**:
   - ❌ **Problem**: Async backfilling is too slow, causing target lag.
   - ✅ **Fix**: Distribute workload (e.g., partition by `user_id`).

4. **No Rollback Plan**:
   - ❌ **Problem**: Migration fails but can’t revert quickly.
   - ✅ **Fix**: Document failback scripts and test them.

5. **Tight Coupling to Source Schema**:
   - ❌ **Problem**: Target schema mirrors source exactly, limiting future optimizations.
   - ✅ **Fix**: Design target schema independently (e.g., denormalize for read performance).

---
**Key Takeaway**: Scaling migrations require **phased execution**, **asynchronous processing**, and **rigorous validation**. Always prioritize **read consistency** during cutover and design for **fail-safe rollback**.