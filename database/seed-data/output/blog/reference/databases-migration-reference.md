# **[Pattern] Reference Guide: Database Migration**

---
## **1. Overview**
Database migration refers to the process of transferring data between database systems while maintaining data integrity, minimizing downtime, and ensuring compatibility between source and target environments. This pattern is critical for cloud adoption, legacy system modernization, or transitioning between database technologies (e.g., MySQL → PostgreSQL, Oracle → MongoDB). Migrations may involve **schema updates** (altering tables, adding constraints), **data transformation** (converting formats, normalizing data), or **full schema/data replication**. Best practices include incremental migration, validation checks, and rollback planning to mitigate risks.

---
## **2. Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Source & Target DB**   | The database being migrated **from** (source) and **to** (target). May involve same vendors (e.g., MySQL 5.7 → MySQL 8.0) or cross-platform shifts (SQL → NoSQL).                                         |
| **Schema Migration**     | Changes to table structures (e.g., adding columns, renaming indexes, modifying constraints). Tools like **Flyway**, **Liquibase**, or custom scripts handle this.                                           |
| **Data Migration**       | Transferring data between systems, often involving transformations (e.g., parsing legacy formats, enriching records). May require **ETL** (Extract-Transform-Load) or **CDC** (Change Data Capture).          |
| **Dual-Write Mode**      | Writing data to both source and target temporarily to validate consistency before full cutover. Reduces downtime but doubles storage/write operations.                                                 |
| **Cutover Strategy**     | Timeline for switching from source to target:
   - **Big Bang**: Immediate switch (high risk).
   - **Phase-by-Phase**: Gradual rollout (e.g., feature-based).
   - **Parallel Run**: Both systems operate until validation passes.
   - **Staged**: Migrate non-critical data first, then critical.                                                                                                                                 |
| **Validation**           | Post-migration checks to ensure:
   - Data **completeness** (no missing records).
   - **Accuracy** (values match source).
   - **Consistency** (constraints, foreign keys intact).
   | **Rollback Plan**      | Predefined steps to revert to the source database (e.g., failing back to a backup, restoring source data) if issues arise during migration.                                                              |
| **Performance Impact**   | Large migrations may cause:
   - High CPU/memory usage during data transfer.
   - Lock contention if tables are locked during schema changes.
   - Solution: Schedule migrations during low-traffic periods or use parallel processing.                                                                                                       |
| **Data Types Mapping**   | Converting between incompatible data types (e.g., `VARCHAR(255)` → `TEXT`, `DATE` → `TIMESTAMP`). Tools like **AWS Database Migration Service (DMS)** or **EnterpriseDB’s AWS Migration Toolkit** automate this. |

---

## **3. Schema Reference**

Below are common table structure changes during migrations. Adjust syntax for your database system (e.g., replace `DROP TABLE` with `TRUNCATE TABLE` for PostgreSQL).

### **3.1 Schema Migration SQL Examples**
| **Action**               | **Source SQL**                          | **Target SQL**                          | **Notes**                                                                                     |
|--------------------------|----------------------------------------|-----------------------------------------|-----------------------------------------------------------------------------------------------|
| **Add Column**           | `ALTER TABLE users ADD COLUMN age INT;` | Same (target syntax may vary).           | Use `NULL` for optional fields.                                                               |
| **Drop Column**          | `ALTER TABLE products DROP COLUMN sku;` | Same.                                   | Ensure no foreign keys depend on the column.                                                |
| **Change Column Type**   | `ALTER TABLE orders MODIFY email VARCHAR(254) NOT NULL;` | `ALTER TABLE orders ALTER COLUMN email TYPE VARCHAR NOT NULL;` | PostgreSQL syntax differs from MySQL.                                                       |
| **Add Primary Key**      | `ALTER TABLE users ADD PRIMARY KEY (id);` | Same.                                   | Requires `id` to be unique in the source.                                                    |
| **Add Foreign Key**      | `ALTER TABLE orders ADD FOREIGN KEY (user_id) REFERENCES users(id);` | Same. | Ensure referential integrity is preserved.                                                   |
| **Add Index**            | `CREATE INDEX idx_name ON users(name);`  | Same.                                   | Improves query performance post-migration.                                                  |
| **Add Constraint**       | `ALTER TABLE products ADD CONSTRAINT CHECK (price > 0);` | Same. | Validate data before applying constraints.                                                   |

---

## **4. Query Examples**

### **4.1 Data Extraction (Source)**
```sql
-- Export users table to CSV (MySQL)
SELECT * INTO OUTFILE '/tmp/users.csv'
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
FROM users;

-- Export with WHERE clause (PostgreSQL)
COPY (SELECT * FROM orders WHERE status = 'pending') TO '/tmp/pending_orders.csv' WITH CSV HEADER;
```

### **4.2 Data Transformation (ETL)**
```python
# Python example: Convert legacy JSON format to structured records
import json
import pandas as pd

def transform_legacy_data(file_path):
    with open(file_path) as f:
        legacy_data = json.load(f)
    # Flatten nested JSON and cleanse data
    df = pd.json_normalize(legacy_data, 'user', ['name', 'email', 'age'])
    df['email'] = df['email'].str.lower()  # Standardize format
    return df.to_dict('records')
```

### **4.3 Data Loading (Target)**
```sql
-- Bulk insert into target PostgreSQL (using COPY for speed)
COPY users FROM '/tmp/users.csv' WITH (FORMAT csv, HEADER true);

-- Insert with transformations (SQLite example)
INSERT INTO target_table (id, name)
SELECT id, UPPER(name) FROM source_table;
```

### **4.4 Validation Queries**
```sql
-- Compare record counts
SELECT
    (SELECT COUNT(*) FROM source_table) AS source_count,
    (SELECT COUNT(*) FROM target_table) AS target_count;

-- Check for missing records
SELECT s.id
FROM source_table s
LEFT JOIN target_table t ON s.id = t.id
WHERE t.id IS NULL;

-- Verify data type conversion
SELECT source_column::TEXT AS original, target_column::TEXT AS converted
FROM target_table
WHERE original != target_column;
```

### **4.5 Change Data Capture (CDC) Example**
```sql
-- Track changes in MySQL (using binlog)
CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000002';
-- Capture new records in target DB via triggers or AWS DMS.
```

---

## **5. Implementation Steps**

### **5.1 Pre-Migration**
1. **Audit Source Data**:
   - Run `SHOW CREATE TABLE` or equivalent to document schemas.
   - Identify orphaned records, null values, or data type mismatches.
2. **Plan Cutover**:
   - Choose a strategy (e.g., parallel run for 24 hours).
   - Schedule during low-traffic periods.
3. **Set Up Target**:
   - Provision target DB with identical hardware (if applicable).
   - Configure backups (e.g., PostgreSQL’s `pg_dump`).

### **5.2 Migration Execution**
1. **Schema Migration**:
   - Use tools like **Liquibase** (XML/YAML) or **Flyway** (SQL scripts):
     ```xml
     <!-- Liquibase changelog example -->
     <changeSet id="add-email-column" author="admin">
       <addColumn tableName="users">
         <column name="email" type="varchar(255)"/>
       </addColumn>
     </changeSet>
     ```
2. **Data Migration**:
   - For large datasets, use **incremental loads** or **partitioning**.
   - Example with **AWS DMS**:
     ```json
     {
       "sourceEndpoint": {
         "endpointType": "source",
         "engineName": "mysql",
         "serverName": "source-db.example.com",
         "port": 3306
       },
       "targetEndpoint": {
         "endpointType": "target",
         "engineName": "postgres",
         "serverName": "target-db.example.com"
       }
     }
     ```
3. **Validation**:
   - Compare hashes of key fields (e.g., `MD5` of user records).
   - Run application tests against the target DB.

### **5.3 Post-Migration**
1. **Cutover**:
   - Update application config to point to target DB.
   - Monitor performance for bottlenecks.
2. **Documentation**:
   - Record schema changes in a **migration log**.
   - Update database diagrams (e.g., ER diagrams in **Lucidchart**).
3. **Rollback (if needed)**:
   - Restore source DB from backup.
   - Revert application config.

---

## **6. Tools & Libraries**
| **Tool**                     | **Purpose**                                                                 | **Best For**                          |
|------------------------------|-----------------------------------------------------------------------------|----------------------------------------|
| **Liquibase**                | Schema versioning and migration automation.                                | Multi-DB migrations (SQL-based).     |
| **Flyway**                   | SQL script-based migrations with rollback support.                          | Simple schema changes.                |
| **AWS Database Migration Service (DMS)** | CDC and batch migration between cloud/on-prem DBs.                      | Large-scale cloud migrations.        |
| **DBeaver**                  | GUI for comparing schemas/data between DBs.                                | Manual validation.                    |
| **dbdiagram.io**             | Generate ER diagrams from SQL.                                             | Documentation.                         |
| **Sqoop**                    | Import/export between Hadoop and relational DBs.                            | Big Data integrations.                |

---

## **7. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------|
| **Data Loss**                         | Use **transactional migrations** (wrap in `BEGIN/COMMIT`).                     |
| **Downtime During Schema Changes**     | Apply changes during off-peak hours or use **online schema change** tools (e.g., **gh-ost** for MySQL). |
| **Incompatible Data Types**           | Pre-process data (e.g., cast `DATE` to `TIMESTAMP` in Python).                |
| **Foreign Key Constraints**           | Temporarily disable constraints during migration, re-enable post-load.         |
| **Application Breaks**                | Test target DB with a **staging environment** mirroring production.             |

---

## **8. Related Patterns**
1. **Data Synchronization**: Keep source and target DBs in sync post-migration (e.g., using **Debezium** for CDC).
2. **Database Sharding**: Distribute data across multiple DB instances if target DB cannot handle the load.
3. **Microservices Data Strategy**: Design DB-per-service architecture to avoid monolithic migrations.
4. **Schema Evolution**: Gradually update schemas without downtime (e.g., **add-only columns**).
5. **Blue-Green Deployment**: Migrate DB alongside application deployment for zero-downtime cutover.

---
## **9. References**
- [Liquibase Documentation](https://www.liquibase.org/)
- [AWS DMS User Guide](https://docs.aws.amazon.com/dms/latest/userguide/Welcome.html)
- [Database Migration Best Practices (Redgate)](https://www.red-gate.com/simple-talk/blogs/database-migration-best-practices/)