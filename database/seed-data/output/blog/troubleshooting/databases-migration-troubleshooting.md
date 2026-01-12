---
# **Debugging Databases Migration: A Troubleshooting Guide**
*(For Backend Engineers)*

---

## **1. Introduction**
Databases migrations are critical operations that can introduce downtime, data corruption, or performance degradation if not executed properly. This guide focuses on **quick resolution** of common migration issues using practical debugging techniques, code fixes, and preventive strategies.

---

## **2. Symptom Checklist**
Before diving into fixes, verify if your migration is failing due to one or more of these symptoms:

✅ **Application Crashes or Errors**
   - SQL errors (e.g., `foreign_key_violation`, `unique_violation`).
   - Application logs showing DB connection timeouts (`ConnectionRefusedError`, `OperationTimeout`).
   - Unhandled exceptions like `IntegrityError` (Flask/Django) or `PostgresError` (Node.js).

✅ **Data Inconsistencies**
   - Missing records in the new database.
   - Duplicate entries where uniqueness was enforced.
   - Old vs. new data not matching (e.g., aggregated values).

✅ **Performance Issues**
   - Slow migration progress (long-running queries, blocking locks).
   - High CPU/Memory usage during migration.

✅ **Transaction Failures**
   - Partial migrations (some tables updated, others not).
   - Rollback failures (`MigrationFailed` errors).

✅ **Dependency Errors**
   - Missing required packages (`psycopg2`, `sqlalchemy`).
   - Schema mismatches between source and target DBs.

✅ **Locking Issues (PostgreSQL/MySQL)**
   - `LockTimeoutError` (concurrent transactions).
   - `Deadlock` errors.

---

## **3. Common Issues & Fixes**

### **3.1 Migration Script Fails with `IntegrityError`**
**Symptom:**
`IntegrityError: null value in column "id" violates not-null constraint` (PostgreSQL) or similar foreign key violations.

**Root Cause:**
- Missing `ON UPDATE CASCADE` or `ON DELETE SET NULL` in constraints.
- Mismatched data types between source and target.

#### **Fix (PostgreSQL Example)**
```sql
-- Add constraints with proper handling
ALTER TABLE new_table
ADD CONSTRAINT fk_example
FOREIGN KEY (external_id) REFERENCES old_table(id) ON DELETE CASCADE;
```

**Debugging Steps:**
1. Check the migration log for the first failing row.
2. Verify data types (`SELECT data_type FROM information_schema.columns`).
3. Manually insert a test row to reproduce the error.

---

### **3.2 Slow Migration Due to Large Tables**
**Symptom:**
Migration hangs or takes hours to complete.

**Root Cause:**
- Lack of batching in bulk operations.
- Missing indexes on foreign keys.

#### **Fix (Batched Inserts in Python)**
```python
# Instead of bulk insert, use chunked batches
batch_size = 1000
for i in range(0, total_rows, batch_size):
    chunk = data[i:i + batch_size]
    cursor.executemany("INSERT INTO new_table VALUES (%s, %s)", chunk)
    conn.commit()  # Commit after each batch
```

**Optimizations:**
- Disable indexes temporarily (`ALTER TABLE ... DISABLE TRIGGER ALL;`).
- Use `COPY` (PostgreSQL) or `LOAD DATA INFILE` (MySQL) for bulk loads.

---

### **3.3 Data Corruption After Migration**
**Symptom:**
Aggregated values (sums, counts) don’t match between source and target.

**Root Cause:**
- Aggregation logic differs (e.g., `NULL` handling).
- Foreign key constraints dropped mid-migration.

#### **Fix (Validate with Checks)**
```python
# Compare counts (example in Python)
source_count = db.execute("SELECT COUNT(*) FROM old_table").fetchone()[0]
target_count = db.execute("SELECT COUNT(*) FROM new_table").fetchone()[0]
if source_count != target_count:
    raise ValueError("Data mismatch!")
```

**Debugging Tools:**
- Generate hash checksums (`CHECKSUM TABLE` in PostgreSQL).
- Use database-specific tools like `mysqlpump` (MySQL) or `pg_dump` (PostgreSQL) for verification.

---

### **3.4 Transaction Timeout or Deadlock**
**Symptom:**
`DeadlockDetected` or `OperationTimeout` errors.

**Root Cause:**
- Long-running transactions blocking others.
- No transaction isolation level set (e.g., `READ COMMITTED`).

#### **Fix (PostgreSQL)**
```sql
-- Set a short timeout and use explicit transactions
SET LOCAL lock_timeout = '5s';
BEGIN;
-- Your migration queries here
COMMIT;
```

**Prevention:**
- Use `BEGIN ... COMMIT` blocks for critical operations.
- Split large migrations into smaller transactions.

---

### **3.5 Schema Mismatch Between Environments**
**Symptom:**
Migration works in dev but fails in prod due to schema differences.

**Root Cause:**
- Dev environment has extra columns/constraints.
- Target DB is on a different minor version (e.g., PostgreSQL 13 vs. 14).

#### **Fix (Generate Schema Dump)**
```bash
# Compare schemas
pg_dump -h old_db -U user --schema-only old_db > schema_old.sql
pg_dump -h new_db -U user --schema-only new_db > schema_new.sql
diff schema_old.sql schema_new.sql
```

**Solution:**
- Use `alembic` (Python) or `Flyway` (Java) to auto-generate migrations.
- Test migrations in a staging environment that mirrors prod.

---

### **3.6 Missing Dependencies**
**Symptom:**
`ModuleNotFoundError` or `No such table` errors.

**Root Cause:**
- Missing database drivers (`psycopg2`, `pymysql`).
- Migration script not installed in the runtime environment.

#### **Fix (Virtual Environment Example)**
```bash
# Ensure dependencies are installed
pip install psycopg2-binary alembic
```

**Debugging:**
- Check `pip list` for missing packages.
- Verify `INSTALLED_APPS` (Django) or `ALLOWED_MIGRATION_PACKAGES` (Alembic).

---

## **4. Debugging Tools & Techniques**

### **4.1 Database-Specific Tools**
| Database  | Tool                          | Use Case                          |
|-----------|-------------------------------|-----------------------------------|
| PostgreSQL| `pgbadger`, `pg_monitor`      | Log analysis, query performance   |
| MySQL     | `mysqldumpslow`, `pt-query-digitement` | Slow queries, replication issues |
| MongoDB   | `mongostat`, `db.currentOp()` | Replica lag, write performance   |

**Example (PostgreSQL):**
```sql
-- Find slow queries
SELECT query, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### **4.2 Logging & Monitoring**
- **Application Logs:** Filter for `SQLAlchemy` or `Django DB` logs.
  ```python
  # Enable logging in Django
  LOGGING = {
      'loggers': {
          'django.db.backends': {
              'level': 'DEBUG',
              'handlers': ['console'],
          },
      },
  }
  ```
- **Database Logs:**
  - PostgreSQL: `log_statement = 'all'` in `postgresql.conf`.
  - MySQL: `general_log = 1` in `my.cnf`.

### **4.3 Transaction Tracing**
- **PostgreSQL:**
  ```sql
  -- Enable transaction tracing
  SET client_min_messages = 'LOG';
  ```
- **MySQL:**
  ```sql
  SET GLOBAL general_log = 'ON';
  ```

### **4.4 Health Checks**
Add pre-migration checks:
```python
# Example: Verify DB connection before migration
import psycopg2
conn = psycopg2.connect("dbname=test user=postgres")
conn.close()  # If this fails, abort migration
```

---

## **5. Prevention Strategies**

### **5.1 Version Control for Migrations**
- Store migration scripts in Git with proper branching:
  ```bash
  git init /path/to/migrations
  git add alembic/versions/
  git commit -m "Add schema migration for users_table"
  ```

### **5.2 Test Migrations in Staging**
- Use a **staging database** identical to production.
- Automate testing with CI/CD pipelines (e.g., GitHub Actions).

### **5.3 Rollback Plan**
- Always include a **rollback script** in migrations.
  ```python
  # Example: Rollback a table drop
  def rollback():
      cursor.execute("CREATE TABLE old_table (id SERIAL PRIMARY KEY);")
      conn.commit()
  ```

### **5.4 Batch Operations for Large Data**
- Avoid `INSERT INTO ... SELECT` for huge datasets.
- Use **incremental migration** (e.g., process 1% of data at a time).

### **5.5 Schema Design Best Practices**
- **Add `created_at`/`updated_at` columns** for audit trails.
- **Avoid `CASCADE` deletions** if possible (use application logic instead).
- **Use transactions** for atomic operations.

### **5.6 Automated Validation**
- Write tests to validate migration outputs:
  ```python
  # Example: PyTest for migration validation
  def test_migration_output():
      assert db.execute("SELECT COUNT(*) FROM new_table").fetchone()[0] == 1000
  ```

### **5.7 Document Migration Steps**
- Maintain a **runbook** with:
  - Pre-migration checks.
  - Rollback procedures.
  - Contact info for emergencies.

---

## **6. Quick Reference Cheat Sheet**
| **Issue**               | **Quick Fix**                          | **Tool**                     |
|--------------------------|----------------------------------------|------------------------------|
| Foreign Key Error        | `ON DELETE SET NULL`                   | `ALTER TABLE`                |
| Slow Bulk Inserts        | Use `COPY` (PostgreSQL)                | `psql \copy`                 |
| Data Mismatch            | Compare `COUNT(*)`                     | `pg_dump --schema-only`      |
| Deadlock                 | `SET lock_timeout = '5s'`              | PostgreSQL CLI               |
| Schema Mismatch          | `diff <(pg_dump --schema-only old) <(pg_dump --schema-only new)` | Bash |

---

## **7. When to Escalate**
- **Database crashes** (e.g., `PANIC: checkpoints failed` in PostgreSQL).
- **Data loss** confirmed by checksums.
- **SLA violations** (e.g., downtime exceeds 30 minutes).

**Next Steps:**
1. **Restore from backup** (if critical).
2. **Engage DBA team** for deep investigations.
3. **Post-mortem meeting** to update runbooks.

---
**Final Note:** Always **test migrations in a non-production environment first**. Use **idempotent migrations** (repeating the same migration should not cause errors). Happy debugging! 🚀