# **[Pattern] Debugging Migration: Reference Guide**

---

## **Overview**
The **Debugging Migration** pattern provides structured techniques to identify, isolate, and resolve failures in database migrations—critical when schema changes introduce operational disruptions. This pattern helps teams diagnose issues by systematically comparing expected and actual states, validating data integrity, and ensuring backward compatibility. It is essential for large-scale deployments, multi-team environments, or migrations involving complex data transformations.

Key use cases include:
- **Schema inconsistencies** (missing columns, incorrect data types).
- **Data corruption** (invalid values, referential integrity violations).
- **Performance bottlenecks** (query degradation post-migration).
- **Compatibility issues** (application code failures due to schema changes).

The pattern leverages tools like database logs, version control, and validation scripts to streamline debugging.

---

## **Implementation Details**

### **Core Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Migration State Tracking** | Records the current schema version (e.g., via `schema_migrations` table) to detect unstaged or incomplete migrations.                                                                                       |
| **Delta Analysis**         | Compares pre- and post-migration schemas to identify structural changes (e.g., column additions/deletions). Tools: `pg_dump --schema-only`, `SHOW CREATE TABLE`.                                          |
| **Data Validation**        | Uses checksums, row counts, or constraints to verify data integrity. Example: `CHECKSUM TABLE table_name`.                                                                                               |
| **Rollback Plan**          | Defines steps to revert migrations (e.g., restoring from backups, reversing scripts).                                                                                                                         |
| **Transaction Batching**   | Splits large migrations into smaller, reversible transactions to isolate failures.                                                                                                                          |
| **Dependency Mapping**     | Tracks application code dependencies on specific schema elements (e.g., table references in queries).                                                                                                      |
| **Logging & Instrumentation** | Captures migration execution logs (success/failure timestamps, affected rows) for post-mortem analysis.                                                                                                    |
| **Staging Environments**   | Tests migrations in a non-production environment with identical data volume and constraints.                                                                                                              |

---

### **Requirements**
#### **Tools & Technologies**
- **Database**: PostgreSQL, MySQL, MongoDB (with schema support), or SQL Server.
- **Version Control**: Git (for migration scripts), Docker (for reproducible environments).
- **Validation Tools**:
  - `psql`/`mysql` CLI for ad-hoc queries.
  - Tools like **Great Expectations**, **dbt**, or **SQLFluff** for automated checks.
  - Custom scripts (Python, Bash) for custom validations.
- **Monitoring**: Prometheus/Grafana for performance metrics post-migration.

#### **Prerequisites**
1. A **migration history log** (e.g., table tracking applied versions).
2. **Backup** of the database before migration execution.
3. **Access** to all affected environments (dev, staging, prod).
4. **Clear ownership** of migration scripts and validation rules.

---

## **Schema Reference**

| **Component**              | **Description**                                                                 | **Example Schema**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Migration Log Table**    | Tracks applied migrations (version, timestamp, user).                         | ``` sql CREATE TABLE schema_migrations ( id SERIAL PRIMARY KEY, version VARCHAR(50), applied_at TIMESTAMP, applied_by VARCHAR(100) ); ``` |
| **Pre-/Post-Migration Hooks** | Triggers for validation before/after migration.                              | ``` sql CREATE OR REPLACE FUNCTION validate_data_integrity() RETURNS VOID AS $$ ... $$ LANGUAGE plpgsql; ```                  |
| **Checksum Table**         | Stores hash checksums of critical tables for post-migration verification.     | ``` sql CREATE TABLE table_checksums ( table_name VARCHAR(100), previous_checksum VARCHAR(64), current_checksum VARCHAR(64) ); ``` |
| **Error Logging Table**    | Captures migration errors (error code, affected rows, stack trace).           | ``` sql CREATE TABLE migration_errors ( error_id UUID PRIMARY KEY, migration_version VARCHAR(50), error_message TEXT, timestamp TIMESTAMP ); ``` |

---

## **Query Examples**

### **1. Verify Applied Migrations**
```sql
-- List all applied migrations
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- Check if a specific version is applied
SELECT COUNT(*) FROM schema_migrations WHERE version = 'v2.3.1';
```

### **2. Compare Schemas Before/After Migration**
```sql
-- Generate current schema (PostgreSQL)
\dt+ schema_version_v2  -- Lists tables/columns in v2 schema
\o schema_dump.sql       -- Export schema to file
\dt+                     -- Compare with pre-migration dump

-- MySQL: Compare with `INFORMATION_SCHEMA.COLUMNS`
SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'db_name' AND TABLE_NAME = 'target_table';
```

### **3. Validate Data Integrity**
```sql
-- Check row counts
SELECT COUNT(*) FROM users_pre_migration, users_post_migration WHERE users_pre_migration.id = users_post_migration.id;

-- Compare checksums
SELECT * FROM table_checksums WHERE previous_checksum != current_checksum;

-- Validate foreign key constraints
SELECT * FROM pg_constraint WHERE conrelid = 'users'::regclass;
```

### **4. Rollback to Previous Version**
```sql
-- Rollback a migration (example: revert column removal)
ALTER TABLE users ADD COLUMN old_column VARCHAR(255);

-- Alternative: Restore from backup
pg_restore -d db_name -t users -f backup.sql
```

### **5. Debug Performance Issues**
```sql
-- Compare query execution plans
EXPLAIN ANALYZE SELECT * FROM users WHERE created_at > '2023-01-01' LIMIT 10;

-- Check for missing indexes
SELECT * FROM pg_stat_user_indexes WHERE indexrelname NOT LIKE 'idx_%';
```

### **6. Automated Validation Script (Python Example)**
```python
import psycopg2
from hashlib import sha256

def verify_checksums():
    conn = psycopg2.connect("dbname=test user=postgres")
    cursor = conn.cursor()

    # Fetch expected checksums
    cursor.execute("SELECT table_name, previous_checksum FROM table_checksums")
    expected = {row[0]: row[1] for row in cursor.fetchall()}

    # Compute current checksums
    current = {}
    for table in expected:
        cursor.execute(f"SELECT md5(digest(text, 'sha256')) FROM {table}")
        current[table] = cursor.fetchone()[0]

    # Report mismatches
    mismatches = [table for table in expected if expected[table] != current[table]]
    print(f"Mismatches: {mismatches}")
```

---

## **Error Handling & Common Pitfalls**

| **Issue**                          | **Cause**                                  | **Debugging Steps**                                                                                     | **Prevention**                                                                                     |
|-------------------------------------|--------------------------------------------|---------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Schema drift**                    | Manual schema changes bypass migrations.     | Compare `schema_migrations` with `INFORMATION_SCHEMA`.                                                  | Enforce migrations for all schema changes.                                                       |
| **Data corruption**                 | Invalid constraints or transactions.       | Use `CHECKSUM TABLE` and validate referential integrity.                                                 | Test migrations in staging with identical data volume.                                            |
| **Lock contention**                 | Long-running migrations block queries.      | Monitor `pg_locks` or `sys.dm_tran_locks`.                                                             | Batch migrations or run during low-traffic periods.                                               |
| **Missing dependencies**            | Application code references old schema.     | Check application logs for `SQL error: column not found`.                                               | Document schema dependencies and notify teams before migrations.                                   |
| **Transaction timeouts**            | Large migrations exceed session timeout.    | Split into smaller transactions or increase `timeout` in `postgresql.conf`.                           | Profile migration scripts for duration.                                                          |
| **Backup failure**                  | Corrupted or incomplete backups.            | Test restore from backup in staging.                                                                   | Automate backup verification.                                                                    |

---

## **Related Patterns**

1. **Blue-Green Migration**
   - *Connection*: Debugging migrations is critical when switching traffic between old and new schemas.
   - *Example*: Use feature flags to route queries to the old schema during validation.

2. **Canary Migrations**
   - *Connection*: Gradually roll out migrations to minimize impact if debugging fails.
   - *Example*: Deploy to 10% of servers first, then monitor for errors.

3. **Idempotent Migrations**
   - *Connection*: Ensures migrations can be repeated safely, easing debugging.
   - *Example*: Add `IF NOT EXISTS` checks in SQL scripts.

4. **Schema Evolution**
   - *Connection*: Gradually modify schemas while maintaining backward compatibility.
   - *Example*: Add columns with `DEFAULT` values to avoid breaking changes.

5. **Observability-Driven Migration**
   - *Connection*: Integrate metrics and logs to detect migration failures early.
   - *Example*: Track `active_migrations` metric in Prometheus.

6. **Test-Driven Migration**
   - *Connection*: Write tests before migrations to verify expected behavior.
   - *Example*: Use `pytest` with database fixtures for validation.

---

## **Best Practices**
1. **Test in Isolation**:
   - Apply migrations to a staging database with identical constraints (e.g., indexes, constraints).
   - Use tools like **GitLab CI** or **Jenkins** to automate staging tests.

2. **Minimize Downtime**:
   - Schedule migrations during low-traffic periods.
   - For critical systems, use **zero-downtime migrations** (e.g., adding columns first).

3. **Document Everything**:
   - Include migration scripts, validation steps, and rollback instructions in the `README`.
   - Tag migrations with Jira tickets or changelogs.

4. **Automate Validation**:
   - Integrate validation scripts into migration tools (e.g., **Flyway**, **Liquibase**, **Alembic**).
   - Example Flyway hook:
     ```xml
     <changeSet id="validate-data" author="dev">
       <sql>SELECT * FROM validate_data_integrity();</sql>
     </changeSet>
     ```

5. **Monitor Post-Migration**:
   - Set up alerts for anomalies (e.g., query timeouts, error spikes).
   - Use **Grafana dashboards** to compare pre/post-migration metrics.

6. **Review Migration Scripts**:
   - Use **static analysis tools** (e.g., **SQLLint**, **SQLFluff**) to catch syntax issues.
   - Pair-review migration scripts to reduce human error.

---

## **Example Workflow**
1. **Pre-Migration**:
   - Backup the database.
   - Run `validate_data_integrity()` in staging.
   - Review `schema_migrations` for completeness.

2. **During Migration**:
   - Execute migration in a transaction.
   - Log each step’s success/failure.
   - Use `ON CONFLICT` or `RETRY` for idempotency.

3. **Post-Migration**:
   - Compare checksums:
     ```sql
     INSERT INTO table_checksums (table_name, previous_checksum, current_checksum)
     VALUES ('users', old_hash, new_hash);
     ```
   - Validate application performance:
     ```bash
     ab -n 1000 -c 50 http://app/api/users  # Load test
     ```
   - Monitor for errors in logs.

4. **Rollback (if needed)**:
   - Execute `rollback_migration.sh`.
   - Restore from backup as a last resort.

---

## **Tools Cheat Sheet**
| **Tool**               | **Purpose**                                                                 | **Example Command**                                                                 |
|------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **pg_dump**            | Backup schema/data for rollback.                                           | `pg_dump -U user db_name -f backup.sql`                                             |
| **SQLFluff**           | Lint SQL for syntax/style issues.                                          | `sqlfluff fix migration_script.sql --dialect postgresql`                            |
| **Great Expectations** | Validate data quality pre/post-migration.                                  | `great_expectations check suite --suite-name migration_validation`                 |
| **Flyway/Liquibase**   | Manage migrations with versioning.                                         | `flyway migrate`                                                                   |
| **dbt**                | Test migrations with data modeling tests.                                   | `dbt test --select migration_validation`                                             |
| **Prometheus**         | Monitor migration impact on query performance.                              | `prometheus_query --query 'rate(query_duration_seconds_count[5m])'`                |
| **Grafana**            | Visualize pre/post-migration metrics.                                       | Create dashboard for `migration_errors`, `query_latency`.                          |

---
**Final Note**: Debugging migrations requires a combination of **proactive validation**, **automated testing**, and **clear documentation**. Prioritize staging environments and idempotent scripts to minimize production risks. For complex migrations, consider hiring a **database specialist** or using **enterprise tools** like Oracle GoldenGate or AWS Database Migration Service.