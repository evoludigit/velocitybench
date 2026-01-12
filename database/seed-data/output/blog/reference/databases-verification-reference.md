# **[Pattern] Databases Verification Reference Guide**

---
## **1. Overview**
The **Databases Verification** pattern ensures data consistency, integrity, and compliance across multiple databases by systematically validating schema, data, and metadata. This pattern is critical for systems where synchronization between databases (e.g., transactional, analytical, or multi-cloud environments) is required. It helps detect discrepancies early (e.g., schema drift, missing records, or stale data), reduces operational risks, and improves confidence in data-driven decisions.

Key scenarios:
- Continuous integration for database migrations.
- Ensuring **eventual consistency** in distributed systems.
- Cross-cloud or multi-region synchronization.
- Compliance audits for financial, healthcare, or regulatory data.

---

## **2. Core Concepts & Requirements**
| **Concept**               | **Description**                                                                 | **Key Considerations**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Verification Targets**  | Elements to validate (e.g., tables, rows, constraints, stored procedures).      | Define granularity (e.g., table-level vs. row-level).                                  |
| **Verification Rules**    | Logic to enforce consistency (e.g., referential integrity, data type validation). | Use declarative rules (e.g., SQL checks) or imperative checks (e.g., scripts).        |
| **Verification Engine**   | Tool or framework to execute checks (e.g., custom scripts, DBMS built-ins).   | Supports parallel execution, logging, and failure recovery.                           |
| **Synchronization Logic** | Rules to resolve conflicts (e.g., last-write-wins, merge strategies).          | Define conflict resolution policies (e.g., `MERGE`, `UPDATE`, `IGNORE`).              |
| **Thresholds**            | Tolerance for data drift (e.g., 5% divergence allowed).                         | Adjust based on business sensitivity (e.g., 0% for financial records).                |
| **Audit Trail**           | Records of verification results (e.g., timestamps, differences, actions taken).  | Required for compliance and debugging.                                               |

---

## **3. Schema Reference**
### **Verification Table Structure**
A standardized table (`verification_metadata`) can track checks across databases. Below is a reference schema:

| **Column**               | **Data Type**       | **Description**                                                                                     | **Examples**                                  |
|--------------------------|---------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| `check_id`               | `VARCHAR(50)`       | Unique identifier for the verification rule.                                                        | `ref_integrity_employees_departments`         |
| `database_name`          | `VARCHAR(100)`      | Name of the source/target database.                                                               | `prod_db`, `staging_db`                      |
| `table_name`             | `VARCHAR(100)`      | Table subject to verification.                                                                  | `employees`, `departments`                    |
| `check_type`             | `ENUM`              | Type of check (e.g., schema, data, constraint).                                                 | `schema`, `row_count`, `foreign_key`          |
| `expected_value`         | `JSON`              | Expected result (e.g., row count, schema definition).                                             | `{"column_count": 5, "columns": ["id", ...]}` |
| `last_verified`          | `TIMESTAMP`         | Timestamp of the last verification run.                                                          | `2024-05-20 14:30:00`                        |
| `status`                 | `ENUM`              | Result (`PASS`, `FAIL`, `WARNING`).                                                              | `FAIL`                                       |
| `difference`             | `TEXT`              | Details of discrepancies (e.g., missing rows, schema drift).                                      | `'Row with id=101 missing in target.'`         |
| `resolved_by`            | `VARCHAR(50)`       | User/process that fixed the issue.                                                              | `admin_script`                                |
| `resolution_timestamp`   | `TIMESTAMP`         | When the issue was addressed.                                                                     | `2024-05-20 15:45:00`                        |

---

## **4. Query Examples**
### **A. Schema Verification**
**Goal:** Verify that two databases (`source_db` and `target_db`) have identical table schemas for `employees`.

```sql
-- Check if tables exist and columns match
SELECT
    'source_db' AS db_name,
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'employees'
ORDER BY ordinal_position;

-- Compare with target_db (pseudo-code; use a tool like `pg_diff` or `dbdiff` in practice)
SELECT
    source_table.column_name,
    source_table.data_type,
    target_table.column_name AS target_column_name
FROM source_db.information_schema.columns AS source_table
FULL OUTER JOIN target_db.information_schema.columns AS target_table
    ON source_table.column_name = target_table.column_name
    AND source_table.table_name = target_table.table_name
WHERE source_table.table_name = 'employees'
AND (source_table.column_name IS NULL OR target_table.column_name IS NULL)
AND source_table.data_type != target_table.data_type;
```

### **B. Data Validation (Row Count)**
**Goal:** Ensure `target_db` has no missing rows compared to `source_db` for the `employees` table.

```sql
-- Count rows in source and target
SELECT
    'source_db' AS db_name,
    COUNT(*) AS row_count
FROM source_db.employees;

SELECT
    'target_db' AS db_name,
    COUNT(*) AS row_count
FROM target_db.employees;

-- Compare counts (add a threshold check)
WITH counts AS (
    SELECT 'source_db' AS db_name, COUNT(*) AS row_count FROM source_db.employees
    UNION ALL
    SELECT 'target_db', COUNT(*) FROM target_db.employees
)
SELECT db_name, row_count,
    CASE WHEN MAX(row_count) OVER () - row_count > (SELECT threshold FROM verification_config)
         THEN 'WARNING: Data drift detected'
         ELSE 'OK' END AS status
FROM counts;
```

### **C. Referential Integrity Check**
**Goal:** Verify foreign key constraints between `departments` (parent) and `employees` (child).

```sql
-- Check for orphaned employees (no matching department_id)
SELECT e.name AS employee_name
FROM source_db.employees e
LEFT JOIN source_db.departments d ON e.department_id = d.id
WHERE d.id IS NULL;

-- Cross-database check (requires connected DBs or federated queries)
SELECT
    e.name AS employee_name,
    e.department_id AS missing_dept_id,
    'target_db' AS db_name
FROM target_db.employees e
LEFT JOIN source_db.departments d ON e.department_id = d.id
WHERE d.id IS NULL;
```

### **D. Metadata Audit (Stored Procedures)**
**Goal:** Ensure stored procedures exist and have identical definitions.

```sql
-- List procedures in source
SELECT routine_name, routine_definition
FROM source_db.information_schema.routines
WHERE routine_schema = 'public';

-- Compare with target (use a diff tool or custom script)
-- Example: Flag procedures in source not found in target
SELECT s.routine_name
FROM source_db.information_schema.routines s
WHERE NOT EXISTS (
    SELECT 1 FROM target_db.information_schema.routines t
    WHERE t.routine_name = s.routine_name
);
```

---

## **5. Implementation Steps**
### **Step 1: Define Verification Rules**
- Use a **declarative approach** (e.g., YAML/config files) to define checks:
  ```yaml
  checks:
    - id: "emp_dept_fk"
      type: "foreign_key"
      source_db: "prod_db"
      target_db: "replica_db"
      table: "employees"
      parent_table: "departments"
      parent_column: "id"
      child_column: "department_id"
  ```

### **Step 2: Schedule Automated Runs**
- Integrate with CI/CD pipelines (e.g., **GitHub Actions**, **Jenkins**) or cron jobs.
- Example script to trigger checks:
  ```bash
  #!/bin/bash
  python3 verify_databases.py --config validation_rules.yaml --log results.log
  ```

### **Step 3: Handle Failures**
- **Fail fast:** Stop the pipeline if critical checks fail.
- **Notify:** Send alerts (e.g., Slack, email) for non-critical warnings.
- **Resolve:** Use `resolution_timestamp` in the metadata table to track fixes.

### **Step 4: Document Drift**
- Log differences in the `verification_metadata` table.
- Use tools like **Git for databases** (e.g., [Liquibase](https://www.liquibase.org/), [Flyway](https://flywaydb.org/)) to version-control schema changes.

---

## **6. Query Examples (Advanced)**
### **A. Check for Schema Drift Over Time**
```sql
-- Track schema changes in a table (e.g., added/removed columns)
WITH
source_schema AS (
    SELECT column_name, data_type
    FROM source_db.information_schema.columns
    WHERE table_name = 'employees'
),
target_schema AS (
    SELECT column_name, data_type
    FROM target_db.information_schema.columns
    WHERE table_name = 'employees'
)
SELECT
    s.column_name,
    s.data_type,
    t.column_name AS target_column,
    t.data_type AS target_type,
    CASE
        WHEN s.column_name IS NULL THEN 'Added in target'
        WHEN t.column_name IS NULL THEN 'Removed from target'
        WHEN s.data_type != t.data_type THEN 'Data type changed'
        ELSE 'Unchanged'
    END AS change_type
FROM source_schema s
FULL OUTER JOIN target_schema t ON s.column_name = t.column_name;
```

### **B. Cross-Database Aggregation Check**
**Goal:** Ensure sum of salaries in `source_db` matches `target_db`.

```sql
SELECT
    db_name,
    SUM(salary) AS total_salary,
    CASE WHEN (SELECT SUM(salary) FROM source_db.employees) <> SUM(salary)
         THEN 'FAIL: Aggregate mismatch'
         ELSE 'PASS' END AS status
FROM (
    SELECT 'source_db' AS db_name, salary FROM source_db.employees
    UNION ALL
    SELECT 'target_db', salary FROM target_db.employees
) AS salaries
GROUP BY db_name;
```

### **C. Data Quality Checks (Null Values)**
**Goal:** Verify no critical fields (e.g., `email`, `hire_date`) are null in `target_db`.

```sql
-- Flag rows with nulls in critical columns
SELECT
    name,
    email,
    hire_date
FROM target_db.employees
WHERE email IS NULL OR hire_date IS NULL;
```

---

## **7. Tools & Libraries**
| **Tool**               | **Purpose**                                                                 | **Link**                                  |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------|
| **pg_diff**            | Compare PostgreSQL databases.                                                | [GitHub](https://github.com/ArkhipovDmitry/pg_diff) |
| **dbdiff**             | Cross-database schema differencing (SQL Server, MySQL, etc.).               | [GitHub](https://github.com/xo/DBDiff)    |
| **Liquibase**          | Database version control and schema validation.                             | [Docs](https://docs.liquibase.com/)       |
| **Airflow**            | Schedule and orchestrate verification jobs.                                | [Apache Airflow](https://airflow.apache.org/) |
| **pgAdmin/PhpMyAdmin** | Manual verification via GUI.                                                | [pgAdmin](https://www.pgadmin.org/)       |
| **Custom Scripts**     | Python/Node.js scripts for custom logic (e.g., using `psycopg2`, `mysql-connector`). | [Example](https://www.postgresqltutorial.com/postgresql-python/connect/) |

---

## **8. Related Patterns**
### **A. Database Synchronization**
- **When to use:** When real-time or near-real-time synchronization is required.
- **Tools:** [Debezium](https://debezium.io/), CDC pipelines.
- **Key difference:** Synchronization *moves* data; Verification *checks* consistency.

### **B. Eventual Consistency Pattern**
- **When to use:** For distributed systems where full synchronization isn’t feasible.
- **Mechanism:** Use conflict resolution strategies (e.g., vector clocks, CRDTs).
- **Verification:** Add checks for "staleness" (e.g., time-to-live for stale data).

### **C. Data Lineage**
- **When to use:** To trace data flow and dependencies across databases.
- **Tools:** [Amundsen](https://github.com/lyft/amundsen), [Collibra](https://www.collibra.com/).
- **Synergy:** Link verification results to lineage metadata for auditing.

### **D. Schema Migration**
- **When to use:** To evolve databases without downtime.
- **Tools:** [Flyway](https://flywaydb.org/), [Alembic](https://alembic.sqlalchemy.org/).
- **Verification:** Add post-migration checks to confirm schema changes landed correctly.

### **E. Data Masking/Anonymization**
- **When to use:** For compliance (e.g., GDPR) or testing.
- **Tools:** [Apache Druid](https://druid.apache.org/), [Redact](https://github.com/redacted/redact).
- **Verification:** Ensure masked data doesn’t violate validation rules.

---

## **9. Best Practices**
1. **Start Small**: Verify critical tables first (e.g., financial data).
2. **Automate Early**: Integrate checks into CI/CD pipelines.
3. **Define Thresholds**:
   - **0% tolerance** for financial records.
   - **<5% drift** for analytical data (adjust based on SLA).
4. **Log Everything**: Use the `verification_metadata` table for traceability.
5. **Monitor Over Time**: Track trends in data drift (e.g., increasing null values).
6. **Document Exceptions**: Use comments in the metadata table for known issues.
7. **Performance Considerations**:
   - Run checks during off-peak hours.
   - Parallelize across tables (e.g., use database partitioning).
8. **Security**:
   - Use least-privilege access for verification scripts.
   - Encrypt sensitive data in logs (e.g., `email` fields).

---
## **10. Troubleshooting**
| **Issue**                          | **Possible Cause**                          | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------|-----------------------------------------------------------------------------|
| False positives in schema checks    | Case sensitivity in column names.          | Normalize names (e.g., lowercase all column names in checks).             |
| Slow verification runs              | Large tables or complex queries.          | Sample data or run checks in batches.                                       |
| Orphaned records in cross-db checks | Network issues during sync.                | Validate connection health before running checks.                          |
| Schema drift not detected           | Cached metadata queries.                  | Refresh metadata (e.g., `information_schema` cache).                       |
| Alert fatigue (too many warnings)  | Overly strict thresholds.                 | Adjust thresholds or categorize warnings by severity.                       |

---
## **11. Example Workflow**
1. **Pre-Migration**:
   - Run `schema_verify.sql` to compare `source_db` and `target_db`.
   - Log results in `verification_metadata`.
2. **Post-Migration**:
   - Execute `data_consistency_checks.sql` to validate row counts and constraints.
   - If failures: Investigate via `difference` column in `verification_metadata`.
3. **Daily Monitoring**:
   - Use Airflow DAG to run `drift_analysis.sql` weekly.
   - Alert on >3% drift in `employees` table.

---
## **12. Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Schema Drift**       | Unintended changes to database structure (e.g., added/removed columns).         |
| **Eventual Consistency** | A system state where changes propagate eventually (not necessarily immediately). |
| **Referential Integrity** | Enforces relationships between tables (e.g., foreign keys).                     |
| **CDC (Change Data Capture)** | Technology to track and replicate changes from a database.                      |
| **Threshold**          | Maximum allowed deviation between databases (e.g., 2% row count difference).   |
| **Audit Trail**        | Historical record of changes and verifications.                                 |
| **Last-Write-Wins**    | Conflict resolution strategy where the latest update replaces previous ones.    |

---
**End of Document** (≈1,000 words)