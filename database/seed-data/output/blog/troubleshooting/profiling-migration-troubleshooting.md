# **Debugging Profiling Migration: A Troubleshooting Guide**

## **Overview**
The **Profiling Migration** pattern is used to gradually migrate from an old data model to a new one without disrupting existing services. It involves maintaining dual data structures (current and new) during a transition period, ensuring both consistency and performance.

This guide provides a structured approach to debugging common issues during a profiling migration.

---

## **Symptom Checklist**
Before diving into debugging, verify these symptoms to narrow down the problem:

### **1. Data Inconsistency**
- Queries return mismatched results between old and new schemas.
- Aggregations or summaries differ between systems.
- Duplicate or missing records in the new schema.

### **2. Performance Degradation**
- Slow response times during migration.
- Increased query time when using dual-read strategies.
- High CPU/RAM usage during sync operations.

### **3. Schema Mismatch**
- New schema fields are missing in some records.
- Old schema constraints break new schema operations.
- Transaction rollback errors due to schema conflicts.

### **4. Transaction & Consistency Issues**
- Incomplete migrations (partial syncs).
- Deadlocks when updating dual structures.
- Race conditions during schema transitions.

### **5. Error Logs & Failures**
- Database connection resets during sync.
- Application crashes when reading/writing to new schema.
- Logs show inconsistencies in schema metadata.

---

## **Common Issues & Fixes**

### **1. Data Inconsistency Between Old & New Schemas**
**Symptoms:**
- Queries return different results when reading from old vs. new tables.
- Aggregations (e.g., SUM, AVG) differ between systems.

**Root Causes:**
- Missing records in the new schema.
- Timing issues during synchronization.
- Schema changes not reflected in query logic.

**Fixes:**

#### **a) Validate Migration Completeness**
Ensure all records exist in both schemas before production use:
```sql
-- Check if all old records were migrated
SELECT COUNT(*) FROM old_schema.users
MINUS
SELECT COUNT(*) FROM new_schema.users;
```

#### **b) Use Dual-Query Logic (Temporarily)**
If sync is incomplete, query both schemas and reconcile:
```python
def get_user(old_db, new_db, user_id):
    old_data = old_db.query(f"SELECT * FROM old_schema.users WHERE id = {user_id}")
    new_data = new_db.query(f"SELECT * FROM new_schema.users WHERE id = {user_id}")

    # Fallback to old data if new data is missing
    return new_data if new_data else old_data
```

#### **c) Implement a Reconciliation Job**
Periodically check for missing records:
```python
def fix_missing_records():
    missing = old_db.query("""
        SELECT id FROM old_schema.users
        WHERE id NOT IN (SELECT id FROM new_schema.users)
    """)
    for row in missing:
        new_db.insert(
            "new_schema.users",
            {"id": row.id, "migrated_at": datetime.now()}
        )
```

---

### **2. Performance Issues During Migration**
**Symptoms:**
- Slow queries due to dual-table reads.
- High database lock contention.

**Root Causes:**
- No indexing on new schema.
- Frequent writes during sync.
- Unoptimized migration jobs.

**Fixes:**

#### **a) Optimize New Schema Indexes**
```sql
-- Add indexes before heavy reads
CREATE INDEX idx_new_schema_users_name ON new_schema.users(name);
```

#### **b) Batch Migration Instead of Real-Time Sync**
```python
def batch_migrate(records_per_batch=1000):
    while True:
        records = old_db.query("""
            SELECT id FROM old_schema.users
            WHERE migrated = FALSE
            LIMIT 1000
        """)
        if not records:
            break

        new_db.bulk_insert(
            new_schema.users,
            [{"id": r.id, "migrated": True} for r in records]
        )
```

#### **c) Use Asynchronous Migration**
Run migration in a background job (e.g., Celery, AWS Lambda) to avoid blocking requests:
```python
@celery.task
def async_migrate():
    # Migration logic here
```

---

### **3. Schema Mismatch Issues**
**Symptoms:**
- New schema fields are missing.
- Old schema constraints break new operations.

**Root Causes:**
- Schema migrations not applied in all environments.
- New schema assumes data format changes not yet enforced.

**Fixes:**

#### **a) Validate Schema Compatibility**
Check if new schema can handle old data:
```sql
-- Test if new schema can accept old data
INSERT INTO new_schema.users
SELECT * FROM old_schema.users
WHERE "new_column" IS NULL;  -- Ensure no conflicts
```

#### **b) Use Schema Versioning**
Track schema changes to avoid conflicts:
```python
def verify_schema_version():
    old_version = old_db.query("SELECT schema_version FROM system_configs")
    new_version = new_db.query("SELECT schema_version FROM system_configs")
    assert old_version == new_version, "Schema versions mismatch!"
```

---

### **4. Transaction & Consistency Failures**
**Symptoms:**
- Partial migrations (some records synced, others not).
- Deadlocks during dual writes.

**Root Causes:**
- No transaction handling.
- Long-running sync jobs.

**Fixes:**

#### **a) Use Transactions for Dual Updates**
```sql
BEGIN TRANSACTION;
-- Update old schema
UPDATE old_schema.users SET migrated = TRUE WHERE id = 123;
-- Insert into new schema
INSERT INTO new_schema.users SELECT * FROM old_schema.users WHERE id = 123;
COMMIT;
```

#### **b) Implement Retry Logic for Deadlocks**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def safe_migrate(user_id):
    try:
        migrate_user(user_id)
    except psycopg2.OperationalError as e:
        if "deadlock" in str(e):
            raise
        else:
            raise
```

---

## **Debugging Tools & Techniques**

### **1. Logging & Monitoring**
- **Database Logs:** Check for slow queries or deadlocks.
- **Application Logs:** Track migration job progress.
- **Monitoring Tools:** Prometheus, Grafana for performance trends.

### **2. Query Profiling**
Use `EXPLAIN ANALYZE` to find slow queries:
```sql
EXPLAIN ANALYZE SELECT * FROM new_schema.users WHERE name = 'Alice';
```

### **3. Schema Comparison Tools**
- **Flyway / Liquibase:** Compare DB schemas.
- **pgAdmin / MySQL Workbench:** Visual schema diffing.

### **4. Transaction Debugging**
- **PostgreSQL:** `pg_stat_activity` to find locked transactions.
- **MySQL:** `SHOW ENGINE INNODB STATUS;` for deadlocks.

---

## **Prevention Strategies**

### **1. Test Migration in Staging**
- Ensure data consistency between old and new schemas before production.
- Load test with high concurrency.

### **2. Use Feature Flags**
- Gradually roll out new schema reads in production:
```python
@feature_flag("use_new_schema")
def get_user(user_id):
    return new_db.query("SELECT * FROM new_schema.users WHERE id = %s", [user_id])
```

### **3. Schema Migration Checklist**
Before cutover:
✅ All records migrated.
✅ New schema indexes created.
✅ Dual reads validated.
✅ Backup & rollback plan ready.

### **4. Automated Validation Jobs**
Run post-migration checks:
```python
def run_validation():
    assert len(old_db.query("SELECT * FROM old_schema.users")) == len(new_db.query("SELECT * FROM new_schema.users"))
```

---

## **Conclusion**
Debugging profiling migrations requires:
1. **Data validation** (ensure completeness).
2. **Performance tuning** (batch sync, async jobs).
3. **Schema consistency** (versioning, testing).
4. **Transactional safety** (retries, rollback plans).

By following this guide, you can resolve issues efficiently and prevent future problems. Always test migrations thoroughly in staging before production.