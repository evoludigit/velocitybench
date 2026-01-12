**[Pattern] Audit Migration – Reference Guide**

---

### **1. Overview**
The **Audit Migration** pattern ensures that changes made during a system migration are tracked, validated, and preserved to maintain compliance, traceability, and data integrity. This pattern is critical when migrating from one system to another (e.g., databases, legacy systems, or cloud platforms), where historical records must be retained for auditing purposes.

Key objectives include:
- **Continuity of audit trails** post-migration.
- **Validation of migrated data** against original records.
- **Reduction of disruption** to operations by logging changes systematically.
- **Compliance adherence** (e.g., GDPR, HIPAA, SOX).

This guide outlines the schema, implementation steps, and query examples for setting up an audit migration pipeline.

---

### **2. Key Concepts & Schema Reference**
Audit migration involves three core components:
1. **Source System**: The legacy system from which data is migrated.
2. **Migration Tool**: A mechanism (ETL, API, or custom script) to transfer data.
3. **Audit Log System**: A dedicated repository to record changes (e.g., database tables, SIEM tools, or audit trails).

#### **Schema Reference**
The following tables define the required schema for audit migration:

| **Component**               | **Description**                                                                 | **Example Fields**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Audit Header Table**      | Stores metadata about each migration batch (e.g., timestamp, user, source ID). | `migration_id (PK), batch_start_time, batch_end_time, user_id, status, source_system_name` |
| **Audit Change Log Table**  | Logs individual record changes (inserts, updates, deletes).                     | `change_id (PK), migration_id (FK), record_id, original_value, new_value, change_type (INSERT/UPDATE/DELETE), change_timestamp, affected_table` |
| **Validation Table**        | Tracks discrepancies between source and target systems.                      | `validation_id (PK), record_id, source_value, target_value, status (MATCH/MISSING/DIFFERENT), resolution_notes` |

**Database Example (SQL-like Pseudocode):**
```sql
CREATE TABLE audit_header (
    migration_id INT PRIMARY KEY AUTO_INCREMENT,
    batch_start_time DATETIME NOT NULL,
    batch_end_time DATETIME,
    user_id VARCHAR(50),
    status ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED'),
    source_system_name VARCHAR(100)
);

CREATE TABLE audit_change_log (
    change_id INT PRIMARY KEY AUTO_INCREMENT,
    migration_id INT NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    original_value TEXT,
    new_value TEXT,
    change_type ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    change_timestamp DATETIME NOT NULL,
    affected_table VARCHAR(50) NOT NULL,
    FOREIGN KEY (migration_id) REFERENCES audit_header(migration_id)
);

CREATE TABLE validation_results (
    validation_id INT PRIMARY KEY AUTO_INCREMENT,
    record_id VARCHAR(100) NOT NULL,
    source_value TEXT,
    target_value TEXT,
    status ENUM('MATCH', 'MISSING', 'DIFFERENT') NOT NULL,
    resolution_notes TEXT,
    UNIQUE (record_id)
);
```

---
### **3. Implementation Steps**
#### **Step 1: Define Scope**
- **Identify critical tables/records** requiring audit trails (e.g., user accounts, financial transactions).
- **Classify records** by sensitivity (e.g., PII vs. non-PII).

#### **Step 2: Set Up Audit Logging**
- **Integrate with the source system**:
  - Use database triggers, change data capture (CDC) tools, or API hooks to log changes.
  - Example: For a PostgreSQL migration, enable `log_statement = 'all'` or use `pgAudit`.
- **Capture metadata**:
  - Timestamp, user, and operation type (insert/update/delete).
  - Original and new values for modified records.

#### **Step 3: Migrate Data with Audit Trails**
- **Batch processing**: Migrate data in chunks to avoid locking tables.
  ```python
  # Pseudocode for ETL migration
  def migrate_with_audit(source_conn, target_conn, batch_size=1000):
      batch = source_conn.query("SELECT * FROM users LIMIT 1000")
      for record in batch:
          target_conn.insert(record)
          audit_log = {
              "migration_id": current_batch_id,
              "record_id": record['user_id'],
              "change_type": "INSERT",
              "original_value": None,
              "new_value": record,
              "change_timestamp": datetime.now()
          }
          log_audit(audit_log)
  ```
- **Track progress**: Update `audit_header.status` during migration (e.g., `IN_PROGRESS` → `COMPLETED`).

#### **Step 4: Validate Migrated Data**
- **Compare source/target**:
  ```sql
  -- Example validation query (SQL)
  SELECT
      u.user_id,
      s.data AS source_value,
      t.data AS target_value,
      CASE WHEN s.data = t.data THEN 'MATCH' ELSE 'DIFFERENT' END AS status
  FROM source_users s
  JOIN target_users t ON s.user_id = t.user_id
  WHERE s.data != t.data;
  ```
- **Resolve discrepancies**: Update `validation_results.resolution_notes` with fixes (e.g., "Data sanitized during migration").

#### **Step 5: Post-Migration Audit**
- **Generate reports**:
  ```sql
  -- Example: Audit report for failed migrations
  SELECT
      ah.migration_id,
      ah.status,
      COUNT(ac.change_id) AS changes_logged,
      COUNT(vr.validation_id) AS validation_errors
  FROM audit_header ah
  LEFT JOIN audit_change_log ac ON ah.migration_id = ac.migration_id
  LEFT JOIN validation_results vr ON ah.migration_id = vr.migration_id
  WHERE ah.status = 'FAILED'
  GROUP BY ah.migration_id;
  ```
- **Archive logs**: Retain audit data per regulatory requirements (e.g., 7 years for GDPR).

---

### **4. Query Examples**
#### **Query 1: List All Changes for a Migration Batch**
```sql
SELECT
    ac.record_id,
    ac.change_type,
    ac.original_value,
    ac.new_value,
    ac.change_timestamp
FROM audit_change_log ac
JOIN audit_header ah ON ac.migration_id = ah.migration_id
WHERE ah.migration_id = 123;
```

#### **Query 2: Find Unmatched Records in Validation**
```sql
SELECT vr.record_id, vr.source_value, vr.target_value
FROM validation_results vr
WHERE vr.status = 'DIFFERENT';
```

#### **Query 3: Count Changes by Table**
```sql
SELECT
    affected_table,
    COUNT(*) AS change_count,
    COUNT(CASE WHEN change_type = 'INSERT' THEN 1 END) AS inserts,
    COUNT(CASE WHEN change_type = 'UPDATE' THEN 1 END) AS updates,
    COUNT(CASE WHEN change_type = 'DELETE' THEN 1 END) AS deletes
FROM audit_change_log
WHERE migration_id = 123
GROUP BY affected_table;
```

#### **Query 4: Find Orphaned Records (Missing in Target)**
```sql
-- Assuming 'users' table exists in source but not target
SELECT u.*
FROM source_users u
LEFT JOIN target_users t ON u.user_id = t.user_id
WHERE t.user_id IS NULL;
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **Data Validation**       | Ensures migrated data meets integrity constraints (e.g., checks for nulls, duplicates). | Before/after migration to catch errors early.                                |
| **Incremental Migration** | Migrates data in real-time or batches to minimize downtime.                  | High-volume systems where full migration is disruptive.                        |
| **Canary Migration**      | Gradually migrates a subset of users/data to test the new system.              | Critical systems where risk mitigation is needed.                              |
| **Change Data Capture (CDC)** | Captures only changes (inserts/updates/deletes) from the source system.     | Real-time auditing or near-synchronous migrations.                              |
| **Immutable Audit Logs**  | Stores audit data in a write-once format (e.g., blockchain, append-only DB). | High-security environments requiring tamper-proof records.                     |

---
### **6. Best Practices**
1. **Automate logging**: Use tools like AWS Database Migration Service (DMS) or Debezium for CDC.
2. **Minimize latency**: Batch logs efficiently to avoid performance bottlenecks.
3. **Secure logs**: Encrypt audit data and restrict access to authorized personnel.
4. **Document thresholds**: Define what constitutes a "critical" audit failure (e.g., 5% data loss).
5. **Test migration**: Run a pilot audit migration before full deployment.

---
### **7. Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| **Missing records in logs**         | Verify CDC/triggers are enabled; check source system logs.                  |
| **Performance bottlenecks**         | Optimize batch sizes; consider asynchronous logging.                       |
| **Data consistency errors**         | Revalidate source/target post-migration; use checksums for critical data.   |
| **Audit log corruption**            | Use database replication or backup logs periodically.                       |

---
**References**:
- [GDPR Article 30: Record-Keeping Obligations](https://gdpr-info.eu/art-30-gdpr/)
- [AWS DMS Documentation](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)
- [Debezium CDC Framework](https://debezium.io/documentation/reference/stable/)