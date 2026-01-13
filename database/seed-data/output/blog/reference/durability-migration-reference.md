# **[Pattern] Durability Migration Reference Guide**

---

## **Overview**
The **Durability Migration** pattern ensures seamless transitions between storage systems while maintaining data integrity, minimizing downtime, and preserving performance. This pattern is critical when migrating workloads to new databases, cloud storage, or upgraded on-premises systems where data persistence must remain intact. It consists of **three core phases**:
1. **Pre-Migration**: Assess compatibility, validate schemas, and prepare synchronization tools.
2. **Migration Execution**: Perform incremental or batch data transfers while maintaining dual-write consistency.
3. **Post-Migration**: Validate data integrity, decommission the old system, and optimize the new environment.

Durability Migration balances **atomicity** (all-or-nothing writes) with **consistency** (reducing divergence between systems) while addressing challenges like **temporal decoupling** (time lag between systems) and **failover resilience**.

---
## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Dual-Write Mode**       | Write operations propagate to both the old and new systems simultaneously (or near-simultaneously) in pre-migration to ensure consistency. Requires idempotent writes and conflict resolution logic.                                                       |
| **Incremental Sync**      | Transfer only new/updated records post-migration to reduce latency and bandwidth usage. Uses **log-based replication** (e.g., CDC) or **timestamp-based checksums** to track changes.                                                                   |
| **Temporal Decoupling**   | Acceptable lag between systems (e.g., seconds/minutes) during migration. Mitigated via **asynchronous replication** or **event sourcing**.                                                                                                                 |
| **Idempotent Operations** | Design writes so retries (e.g., during network blips) don’t duplicate data. Use **UUIDs** or **transaction IDs** as keys.                                                                                                                                     |
| **Checksum Validation**   | Post-migration, compare hashes (e.g., MD5, CRC32) of critical datasets in both systems to detect discrepancies.                                                                                                                                              |
| **Failover Strategy**     | Define how to handle failures (e.g., pause migration, retry, or manual intervention). Use **circuit breakers** to avoid cascading issues.                                                                                                                     |
| **Schema Alignment**      | Ensure new system supports old schema (via backward compatibility) or enforce strict type conversions. Tools like **Flyway** or **Liquibase** can automate schema changes.                                                                                 |
| **Atomic Transactions**   | For critical data, wrap migration steps in distributed transactions (e.g., 2PC) or use **sagas** for long-running workflows.                                                                                                                                      |

---

## **Implementation Schema Reference**

### **1. Pre-Migration Schema**
| **Component**            | **Description**                                                                                                                                                                                                       | **Example Tools**                     |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Source System**        | Original database/cloud storage (e.g., PostgreSQL, S3). Must support read replication or CDC.                                                                                                                       | PostgreSQL (WAL archiving), AWS DMS    |
| **Target System**        | New storage with compatible schema (or schema-mapped equivalent).                                                                                                                                                       | MongoDB (MongoDB Atlas), Snowflake     |
| **Sync Layer**           | Middleware for dual-write/incremental sync (e.g., Kafka, Debezium, custom ETL).                                                                                                                                          | Apache Kafka, AWS Lambda, Airbyte      |
| **Validation Layer**     | Scripts/APIs to compare data post-migration (e.g., checksums, sample queries).                                                                                                                                          | Python (Pandas), PrestoDB             |
| **Monitoring Dashboard** | Tracks migration progress, errors, and system health (e.g., latency, throughput).                                                                                                                                         | Prometheus + Grafana, Datadog         |

---

### **2. Core Migration Phases Schema**
| **Phase**               | **Steps**                                                                                                                                                                                                           | **Key Metrics to Monitor**               |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **Phase 1: Assessment** | - Compare schemas (use `pg_dump` + `schema-spy`).<br>- Estimate volume (e.g., `SELECT COUNT(*) FROM table`).<br>- Test dual-write on a subset.                                                                       | Schema drift, write latency (<500ms)     |
| **Phase 2: Dual-Write** | - Implement dual-write logic (e.g., trigger-based or CDC).<br>- Log conflicts (e.g., primary key clashes).<br>- Validate writes via checksums every `X` minutes.                                                          | Conflict rate, throughput (ops/sec)     |
| **Phase 3: Incremental Sync** | - Use CDC (e.g., Debezium) or triggers to sync deltas.<br>- Batch syncs to reduce overhead.<br>- Freeze writes to old system once sync completes.                                                                | Sync lag (seconds), error rate          |
| **Phase 4: Validation**  | - Run `SELECT COUNT(*)` + checksum compares.<br>- Test critical queries.<br>- Perform a cutover dry run.                                                                                                         | Data divergence (<0.1% mismatch)        |
| **Phase 5: Cutover**     | - Route traffic to new system.<br>- Monitor for anomalies.<br>- Decommission old system.                                                                                                                              | Uptime, latency spikes                  |

---

## **Query Examples**

### **1. Schema Comparison (PostgreSQL → MongoDB)**
```sql
-- Generate source schema SQL (PostgreSQL)
pg_dump -s -t customers -f schema.sql

-- Convert to MongoDB-compatible JSON (custom script or use `psql2json`)
SELECT json_build_object(
  'name', name,
  'email', email,
  'created_at', created_at
) FROM customers LIMIT 100;
```

### **2. Dual-Write Validation (Checksum)**
```sql
-- Generate checksum for source (PostgreSQL)
SELECT
  md5(concat_ws('|', id, name, email)) AS record_checksum,
  COUNT(*) FROM customers GROUP BY record_checksum;

-- Compare with target (MongoDB)
db.customers.aggregate([
  { $group: { _id: { $md5: { $concat: ["$id", "$name", "$email"] } }, count: { $sum: 1 } } }
]);
```

### **3. Conflict Detection (Dual-Write)**
```sql
-- Log conflicts during dual-write (e.g., in a "conflicts" table)
INSERT INTO conflicts (source_id, target_id, error)
SELECT c.id, mc.id, 'Duplicate key'
FROM customers c
LEFT JOIN customers mc ON mc.name = c.name AND mc.email = c.email
WHERE mc.id IS NULL;
```

### **4. Incremental Sync (Debezium CDC)**
```json
-- Debezium Kafka connector config (PostgreSQL → Kafka)
{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "source-db",
    "database.port": "5432",
    "database.user": "replicator",
    "database.password": "secret",
    "database.dbname": "mydb",
    "table.include.list": "customers,orders",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState"
  }
}
```

### **5. Post-Migration Validation (Cross-System Query)**
```sql
-- Compare record counts (SQL vs. MongoDB)
-- SQL:
SELECT COUNT(*) FROM customers;

-- MongoDB:
db.customers.countDocuments();

-- Expected: Counts should match (±0.1% tolerance for async lag).
```

---

## **Edge Cases & Mitigations**

| **Scenario**                  | **Risk**                                                                 | **Mitigation**                                                                                                                                                     |
|-------------------------------|--------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Network Partition**         | Dual-write fails, data divergence.                                        | Use **retries with exponential backoff** + **circuit breakers** (e.g., Hystrix).                                                                                        |
| **Schema Drift**              | New system rejects old data format.                                       | Implement **schema versioning** (e.g., Avro) or **fallback logic** for legacy formats.                                                                          |
| **High Write Throughput**     | Dual-write overloads source system.                                       | **Batch writes** (e.g., 1000 records/bulk insert) or **asynchronous queues** (Kafka).                                                                           |
| **Data Corruption**           | Old system writes corrupt data during cutover.                           | **Freeze writes** to old system during final sync + **point-in-time recovery** (PITR) for source.                                                                 |
| **Timezone Mismatches**       | Timestamps misalign between systems.                                      | Normalize timestamps to **UTC** in both systems.                                                                                                                     |
| **Key Clashes**               | Dual-write duplicates primary keys.                                      | Use **UUIDs** instead of auto-increment IDs or **merge conflict resolution** (e.g., last-write-wins with timestamps).                                                |

---

## **Related Patterns**

| **Pattern**                  | **Purpose**                                                                                                                                                                                                   | **When to Use Together**                                                                                                                                                     |
|------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **[Event Sourcing](link)**   | Store state changes as immutable events for auditing/rollback.                                                                                                                                           | Use if **audit trails** or **time-travel debugging** are critical during migration.                                                                                              |
| **[CQRS](link)**              | Separate read/write models to decouple migration paths.                                                                                                                                                     | Ideal for **high-read workloads** where writes can lag behind reads during sync.                                                                                                |
| **[Saga Pattern](link)**     | Manage long-running transactions across systems.                                                                                                                                                       | Required if migration spans **microservices** with distributed transactions.                                                                                                   |
| **[Schema Evolution](link)** | Gradually adapt schemas without downtime.                                                                                                                                                            | Pair with Durability Migration to avoid **schema lock** during cuts.                                                                                                         |
| **[Database Sharding](link)**| Partition data to reduce migration scope.                                                                                                                                                              | Use if migrating **petabyte-scale** datasets; shard by region/tenant.                                                                                                       |
| **[Blue-Green Deployment](link)** | Zero-downtime switch via parallel systems.                                                                                                                                                     | Combine with Durability Migration for **live traffic handoff**.                                                                                                                 |

---
## **Tools & Libraries**
| **Category**          | **Tools**                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **CDC/Replication**   | Debezium, AWS DMS, Google Dataflow, CDC vault (by Materialize).                                                                                                                                         |
| **ETL/Sync**          | Apache NiFi, Talend, Airbyte, Fivetran.                                                                                                                                                                  |
| **Schema Management** | Flyway, Liquibase, SQLDelight (for mobile).                                                                                                                                                              |
| **Monitoring**        | Prometheus + Grafana, Datadog, New Relic.                                                                                                                                                                |
| **Conflict Resolution** | Kafka Streams (exactly-once semantics), custom reconciliation scripts.                                                                                                                              |
| **Idempotency**       | Database-generated UUIDs, sagas, or **client-side idempotency keys** (e.g., `InsertOrUpdate` in SQL).                                                                                                   |

---
## **Best Practices**
1. **Start Small**: Migration a **non-critical subset** (e.g., 1% of data) first.
2. **Automate Validation**: Script **checksum compares** and **sample queries** for post-migration.
3. **Monitor Latency**: Use **distributed tracing** (e.g., Jaeger) to track dual-write delays.
4. **Plan for Rollback**: Document **cutover time windows** and **old-system fallbacks**.
5. **Test Failures**: Simulate **network drops** and **target system crashes** during dual-write.
6. **Document Schema Mappings**: Create a **one-to-one reference** for fields (e.g., `source.id` → `target.user_id`).
7. **Update Documentation**: Update **API specs**, **ingestion guides**, and **alert thresholds** post-migration.

---
## **Common Mistakes to Avoid**
- **Skipping Dual-Write Testing**: Assume writes will work identically—**test conflicts**.
- **Ignoring Async Lag**: Acceptable lag (e.g., 5 minutes) may cause **inconsistent reads**.
- **Not Freezing Writes**: Allowing writes to both systems post-sync risks **data corruption**.
- **Overcomplicating Sync**: Use **simple checksums** before complex reconciliation logic.
- **No Cutover Dry Run**: Always **simulate traffic handoff** before going live.

---
## **Example Workflow (End-to-End)**
1. **Assess**: Compare schemata; estimate data volume (`pg_dump` + `mongodump`).
2. **Set Up Dual-Write**:
   - Deploy Debezium to replicate source (`customers` table) to Kafka.
   - Write Kafka events to **target MongoDB** via Kafka Connect.
3. **Validate Dual-Write**:
   - Run `SELECT md5(...)` in source; compare with MongoDB hashes.
   - Log conflicts (e.g., duplicates) in a `conflicts` table.
4. **Switch to Incremental Sync**:
   - Pause dual-write; sync only new/updated records via CDC.
5. **Monitor Sync Lag**:
   - Use Prometheus to track lag between source and target.
6. **Cutover**:
   - Route reads/writes to new system; freeze writes to old system.
7. **Decommission**:
   - Verify **100% data integrity**; archive old system.

---
**Reference Guide Complete.**
*For deeper dives, see [Durability Migration Patterns](https://microservices.io/patterns/data/durability-migration.html).*