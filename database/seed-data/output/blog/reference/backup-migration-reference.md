# **[Pattern] Backup Migration Reference Guide**

---

## **1. Overview**
The **Backup Migration** pattern ensures data integrity and availability by migrating data to a new system while retaining a **full, point-in-time backup** of the source system. This approach mitigates risk during migration by allowing rollback to the original state if issues arise. It is particularly useful for **critical data sets, financial systems, or high-availability applications** where zero downtime or data loss is unacceptable.

The pattern follows a **three-phase process**:
1. **Backup Creation** – A full snapshot of the source system is taken before migration.
2. **Parallel Operation** – Both systems (source and target) run concurrently during migration.
3. **Failover & Validation** – After migration, the backup is verified, and the target system is declared primary if successful. If not, the backup is restored to the source.

Key benefits include:
✅ **Atomicity** – No partial migration; full rollback capability.
✅ **Data Consistency** – Ensures source and target match before cutover.
✅ **Minimal Downtime** – Operations continue on the source during migration.
✅ **Compliance** – Meets audit and regulatory requirements for data retention.

---

## **2. Schema Reference**
Below are the core components of the **Backup Migration** pattern and their relationships.

| **Component**               | **Description**                                                                                     | **Key Attributes**                                                                                     | **Dependencies**                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|--------------------------------------------|
| **Source System**           | Original data store (e.g., database, file storage) before migration.                                | - Schema version <br> - Data volume <br> - Backup window requirements                                 | None                                       |
| **Backup Snapshot**         | Immutable copy of the source system at a specific point in time.                                     | - Backup timestamp <br> - Compression method <br> - Storage location (e.g., S3, tape)                | Source System                              |
| **Target System**           | New data store (e.g., cloud database, upgraded on-premise system).                                  | - Schema compatibility <br> - Migration window <br> - Sync mechanism (e.g., CDC, bulk load)         | Backup Snapshot                            |
| **Migration Engine**        | Tool/process responsible for transferring data from source to target (e.g., AWS Database Migration Service, custom ETL). | - Batch size <br> - Transaction logging <br> - Conflict resolution strategy                      | Source & Target Systems                    |
| **Validation Check**        | Scripts or tools to verify data integrity between source and target.                                | - Checksum comparison <br> - Row count validation <br> - Business logic tests                      | Backup Snapshot, Target System             |
| **Failover Mechanism**      | Automated or manual process to revert to backup if migration fails.                                 | - Rollback script <br> - Cutover procedure <br> - Notification triggers                              | Backup Snapshot, Source System             |
| **Monitoring Dashboard**    | Real-time tracking of migration progress, backup health, and failover status.                       | - Progress metrics <br> - Alert thresholds <br> - Audit logs                                         | All Components                              |

---

## **3. Implementation Steps**

### **Phase 1: Backup Creation**
1. **Freeze the Source System**
   - Temporarily halt writes to the source to ensure a consistent backup.
   - Use tools like `pg_dump` (PostgreSQL), `mysqldump` (MySQL), or cloud-native snapshots (e.g., AWS RDS).

   ```sql
   -- Example: PostgreSQL backup command
   pg_dump -Fc -b -v -f /backups/source_db_$(date +%Y%m%d).dump db_name
   ```

2. **Store the Backup Offline**
   - Upload to immutable storage (e.g., S3 with versioning, tape archive) or a geographically separate location.
   - Encrypt the backup (e.g., AES-256) and retain for a compliance-defined retention period.

3. **Document the Backup Metadata**
   - Log backup timestamp, checksum, and system state (e.g., transaction ID for databases).

---

### **Phase 2: Parallel Operation**
1. **Initialize the Target System**
   - Deploy the target system with an empty schema matching the source.
   - Configure replication or CDC (Change Data Capture) if needed for ongoing syncs.

2. **Run the Migration Engine**
   - Use tools like:
     - **Bulk Load**: `LOAD DATA INFILE` (MySQL), `COPY` (PostgreSQL).
     - **CDC Tools**: Debezium, AWS DMS, or custom change logs.
     - **Hybrid Approach**: Initial bulk load + ongoing sync.

   ```bash
   # Example: AWS DMS migration task (JSON snippet)
   {
     "MigrationType": "full-load",
     "SourceEndpoint": {
       "EndpointType": "source",
       "DatabaseName": "source_db",
       "Host": "source-server",
       "Port": 5432
     },
     "TargetEndpoint": {
       "EndpointType": "target",
       "DatabaseName": "target_db",
       "Host": "target-server",
       "Port": 5432
     }
   }
   ```

3. **Monitor Data Sync**
   - Track progress via logs or dashboards (e.g., Prometheus + Grafana).
   - Set alerts for:
     - High latency (>X seconds).
     - Data discrepancy (e.g., row count mismatch).

---
### **Phase 3: Failover & Validation**
1. **Perform Validation Checks**
   - **Schema Validation**: Compare ERDs or generate schema diffs.
   - **Data Validation**:
     ```sql
     -- Example: Row count check
     SELECT COUNT(*) FROM source_table;
     SELECT COUNT(*) FROM target_table;

     -- Example: Checksum comparison (Python)
     import hashlib
     def checksum_table(conn, table):
         return hashlib.md5(conn.execute(f"SELECT * FROM {table}").fetchall()).hexdigest()
     ```

2. **Conduct a Dry Run**
   - Simulate failover by switching read traffic to the target for a subset of users.
   - Test backup restoration to ensure the snapshot is usable.

3. **Execute Cutover**
   - If successful:
     - Update DNS or application configs to point to the target.
     - Decommission the source system (after verifying no stale writes).
   - If failed:
     - Trigger rollback:
       ```bash
       # Example: PostgreSQL restore from backup
       pg_restore -d source_db /backups/source_db_backup.dump
       ```

4. **Post-Migration Cleanup**
   - Archive backups per retention policy.
   - Document lessons learned (e.g., performance bottlenecks).

---

## **4. Query Examples**
### **Database Backups**
| **Database**  | **Backup Command**                                                                 |
|---------------|------------------------------------------------------------------------------------|
| PostgreSQL    | `pg_dump -Fc -f backup.dump db_name` (custom format)                               |
| MySQL         | `mysqldump -u user -p --single-transaction --routines --triggers db_name > backup.sql` |
| MongoDB       | `mongodump --db db_name --out /path/to/backup`                                    |
| Oracle        | `expdp user/password FULL=Y DIRECTORY=backup_dir DUMPFILE=backup.dmp`            |

### **Data Validation Queries**
#### **Check Row Counts**
```sql
-- SQL query to compare row counts
SELECT
    table_name,
    (SELECT COUNT(*) FROM source_table) AS source_rows,
    (SELECT COUNT(*) FROM target_table) AS target_rows,
    CASE WHEN (SELECT COUNT(*) FROM source_table) = (SELECT COUNT(*) FROM target_table)
         THEN 'PASS' ELSE 'FAIL' END AS sync_status
FROM information_schema.tables
WHERE table_name IN ('source_table', 'target_table');
```

#### **Check for Orphaned Records**
```sql
-- Find records in target missing from source
SELECT t.*
FROM target_table t
LEFT JOIN source_table s ON t.id = s.id
WHERE s.id IS NULL;
```

---

## **5. Error Handling & Edge Cases**
| **Scenario**               | **Mitigation Strategy**                                                                 |
|----------------------------|----------------------------------------------------------------------------------------|
| **Backup Corruption**      | Verify checksums; retake backup if invalid.                                            |
| **Partial Migration**      | Log transaction IDs; use CDC to replay missed changes.                                 |
| **Schema Drift**           | Freeze schema changes during migration; use versioned schemas.                       |
| **Network Outage**         | Implement retry logic with exponential backoff.                                        |
| **Concurrent Writes**      | Use `SELECT FOR UPDATE` locks or snapshot isolation levels.                            |
| **Storage Quota Exceeded** | Compress backups; split into smaller chunks.                                          |

---

## **6. Performance Considerations**
- **Backup Size**: Large databases may require incremental backups (e.g., WAL archiving in PostgreSQL).
- **Migration Bandwidth**: Use compression (e.g., `gzip` for SQL dumps) or network optimization (e.g., AWS Direct Connect).
- **Downtime**: Minimize source freeze window; prioritize mission-critical tables.

---

## **7. Related Patterns**
| **Pattern**               | **Description**                                                                       | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Blue-Green Deployment** | Deploy a parallel environment and switch traffic abruptly.                          | Low-risk, non-critical systems with fast failover.                             |
| **Canary Migration**      | Gradually shift traffic to the new system while monitoring.                           | High-traffic systems requiring zero-downtime testing.                         |
| **Change Data Capture (CDC)** | Continuously sync changes between systems in real time.                            | Ongoing syncs for near-real-time updates (e.g., analytics pipelines).           |
| **Database Sharding**     | Split data across multiple instances for scalability.                                | Horizontal scaling under high read/write loads.                                |
| **Disaster Recovery (DR)** | Replicate data to a geographically separate system for failover.                     | Compliance or high-availability requirements (e.g., financial services).       |

---

## **8. Tools & Technologies**
| **Category**          | **Tools**                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------|
| **Backup Tools**      | `pg_dump`, `mysqldump`, `mongodump`, Veeam, Commvault                                        |
| **Migration ETL**     | AWS DMS, Azure Data Factory, Talend, Custom scripts (Python, Go)                              |
| **CDC Tools**         | Debezium, Oracle GoldenGate, AWS Kinesis Data Streams                                        |
| **Validation**        | Great Expectations, dbt tests, custom SQL queries                                             |
| **Monitoring**        | Prometheus, Grafana, ELK Stack, Datadog                                                    |

---
## **9. Best Practices**
1. **Automate Validation**: Use CI/CD pipelines to validate backups and migrations.
2. **Document Rollback Steps**: Include procedures for reverting in the migration playbook.
3. **Test Failover**: Simulate cutover failures to validate recovery procedures.
4. **Monitor Retention**: Ensure backups are stored securely and meet compliance requirements.
5. **Notify Stakeholders**: Coordinate with teams during cutover to minimize impact.

---
## **10. Example Architecture Diagram**
```
[Source System] → (Backup: S3/Tape) → [Migration Engine] → [Target System]
                              ↓
                       [Validation Checks]
                              ↓
                       [Failover Mechanism]
```

---
## **11. References**
- [AWS Backup Migration Guide](https://docs.aws.amazon.com/dms/latest/userguide/CHAP_MigratingSourceDB.html)
- [PostgreSQL pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [Debezium CDC Overview](https://debezium.io/documentation/reference/stable/concepts.html)
- [Gartner: Data Migration Patterns](https://www.gartner.com/smarterwithgartner/data-migration-patterns)