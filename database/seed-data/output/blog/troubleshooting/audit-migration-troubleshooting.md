# **Debugging Audit Migration: A Troubleshooting Guide**
*Audit Migration* involves transitioning legacy audit data from an older system to a modern audit trail (e.g., database changes, logs, or compliance tracking). Migrations can fail due to data inconsistencies, performance bottlenecks, or misconfigured mapping logic. This guide focuses on **quick root-cause analysis** and resolution.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these common symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **Partial data migration** | Only some records were migrated (e.g., 80% of logs, but not 100%). | Incomplete compliance/audit history. |
| **Duplicate entries** | Duplicate audit events after migration. | Data integrity issues. |
| **Missing timestamps** | Audit entries lack correct timestamps or are out-of-sync. | Compliance gaps; incorrect change tracking. |
| **Performance degradation** | Migration jobs run slowly or time out. | Long-duration outages; failed batches. |
| **Invalid data types** | Mapped fields (e.g., JSON → SQL) contain corrupted data. | Query failures; logging errors. |
| **Schema discrepancies** | New audit table lacks expected columns. | Missing metadata (e.g., user actions). |
| **Transaction rollbacks** | Database transactions fail during migration. | Partial writes; orphaned data. |
| **Failed validation checks** | Post-migration data doesn’t pass compliance rules. | Audit tool rejection (e.g., SOX, GDPR). |

**Action:** Cross-check these symptoms with logs, database dumps, and migration scripts.

---

## **2. Common Issues and Fixes**

### **Issue 1: Partial Data Migration**
**Cause:**
- Batch processing fails silently (e.g., `try-catch` hides errors).
- Query timeouts truncate large datasets.
- Filtering logic excludes unintended records.

**Debugging Steps:**
1. **Check batch logs** for errors:
   ```log
   # Example: Failed batch log (Python)
   2024-05-10T14:30:00 ERROR [Migrator] Batch 5 failed: Query timeout (1h) exceeded.
   ```
2. **Validate record counts**:
   ```sql
   -- Compare source vs. destination counts
   SELECT COUNT(*) FROM source_audit_logs;
   SELECT COUNT(*) FROM target_audit_table;
   ```
3. **Fix:**
   - Split large batches or increase timeout:
     ```python
     # Example: Adjust query timeout (SQLAlchemy)
     engine.execute(
         "SELECT * FROM large_table", timeout=3600  # 1-hour timeout
     )
     ```
   - Add retries for transient failures:
     ```python
     from tenacity import retry, stop_after_attempt

     @retry(stop=stop_after_attempt(3))
     def migrate_batch(batch_id):
         try:
             migrate_one_batch(batch_id)
         except Exception as e:
             logger.error(f"Batch {batch_id} failed: {e}")
             raise
     ```

---

### **Issue 2: Duplicate Entries**
**Cause:**
- Idempotent writes (e.g., `INSERT ... ON DUPLICATE KEY UPDATE` misconfigured).
- Manual re-runs of migration scripts.
- Source data has duplicate `event_id` fields.

**Debugging Steps:**
1. **Identify duplicates**:
   ```sql
   -- Find duplicates in target table
   SELECT event_id, COUNT(*) as dup_count
   FROM target_audit_table
   GROUP BY event_id
   HAVING COUNT(*) > 1;
   ```
2. **Fix:**
   - Use a deduplication pass:
     ```sql
     -- PostgreSQL example: Upsert with merge
     INSERT INTO target_audit_table (event_id, details)
     SELECT DISTINCT ON (event_id) event_id, details
     FROM source_audit_logs
     ON CONFLICT (event_id) DO NOTHING;
     ```
   - Add a uniqueness constraint:
     ```sql
     ALTER TABLE target_audit_table ADD CONSTRAINT unique_event_id UNIQUE (event_id);
     ```

---

### **Issue 3: Missing/Timestamp Mismatches**
**Cause:**
- Timezone misalignment (e.g., UTC vs. local time).
- Source system records timestamps as epoch or ISO strings incorrectly parsed.
- Transaction delays (e.g., `BEGIN`/`COMMIT` spanning hours).

**Debugging Steps:**
1. **Inspect sample data**:
   ```sql
   -- Compare timestamps
   SELECT event_id, source_timestamp, target_timestamp
   FROM source_audit_logs s
   JOIN target_audit_table t ON s.event_id = t.event_id
   WHERE s.source_timestamp != t.target_timestamp;
   ```
2. **Fix:**
   - Standardize time handling:
     ```python
     # Convert epoch to UTC (Python)
     from datetime import datetime
     def fix_epoch(epoch_ms):
         return datetime.utcfromtimestamp(epoch_ms / 1000).isoformat()
     ```
   - Use `TIMESTAMP WITH TIME ZONE` in SQL:
     ```sql
     ALTER TABLE target_audit_table
     ALTER COLUMN event_time TYPE TIMESTAMP WITH TIME ZONE;
     ```

---

### **Issue 4: Performance Bottlenecks**
**Cause:**
- Large `JOIN` operations between source/destination.
- No indexing on frequently queried columns (e.g., `user_id`).
- Unoptimized batch sizes (e.g., 10K rows per batch is too much).

**Debugging Steps:**
1. **Profile queries**:
   ```sql
   -- PostgreSQL: Explain slow query
   EXPLAIN ANALYZE
   SELECT * FROM source_audit_logs s
   JOIN users u ON s.user_id = u.id
   WHERE s.event_time > '2024-01-01';
   ```
2. **Fix:**
   - Add indexes:
     ```sql
     CREATE INDEX idx_source_event_time ON source_audit_logs(event_time);
     CREATE INDEX idx_source_user_id ON source_audit_logs(user_id);
     ```
   - Use `LIMIT` + `OFFSET` for incremental batches:
     ```python
     # Optimized batching (PostgreSQL)
     batch_size = 1000
     offset = 0
     while True:
         result = db.execute(
             "SELECT * FROM source_audit_logs LIMIT {} OFFSET {}".format(batch_size, offset)
         )
         if not result:
             break
         migrate_rows(result.fetchall())
         offset += batch_size
     ```

---

### **Issue 5: Schema Mismatches**
**Cause:**
- New audit table lacks required columns (e.g., `ip_address`, `action_type`).
- Data type mismatches (e.g., `TEXT` → `JSONB`).
- Missing constraints (e.g., `NOT NULL` violations).

**Debugging Steps:**
1. **Compare schemas**:
   ```sql
   -- Generate schema diff (PostgreSQL)
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'target_audit_table';

   -- Compare with source schema
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'source_audit_logs';
   ```
2. **Fix:**
   - Alter schema dynamically:
     ```sql
     -- Add missing column
     ALTER TABLE target_audit_table ADD COLUMN ip_address VARCHAR(45);

     -- Change data type
     ALTER TABLE target_audit_table
     ALTER COLUMN details TYPE JSONB USING details::jsonb;
     ```

---

## **3. Debugging Tools and Techniques**
| **Tool/Technique**       | **Use Case**                                  | **Example Command/Code**                          |
|--------------------------|-----------------------------------------------|--------------------------------------------------|
| **Database Profiling**   | Identify slow queries.                        | `EXPLAIN ANALYZE SELECT * FROM logs;`            |
| **Log Aggregation**      | Correlate logs with migration failures.       | `grep "ERROR" /var/log/migration.log`           |
| **Transaction Logging**  | Debug partial commits/rollbacks.              | `PG_LOG_MIN_DURATION_STATEMENT = 0` (PostgreSQL) |
| **Data Diff Tools**      | Compare source vs. destination.               | `pg_dump source | diff - target_dump`                            |
| **Distributed Tracing**  | Trace cross-service migrations.               | Jaeger/Zipkin for microservices.                 |
| **Unit Tests**           | Validate edge cases (e.g., empty batches).    | `pytest test_migration.py --migration-failures` |

**Key Tip:** Use **`strace`** (Linux) to trace system calls for slow I/O:
```bash
strace -c python migrate.py  # Analyze slow syscalls
```

---

## **4. Prevention Strategies**
### **Pre-Migration**
1. **Backup Critical Data**
   ```bash
   pg_dump -U postgres -d source_db > audit_backup.sql
   ```
2. **Test with Sample Data**
   - Migrate a subset (e.g., 1% of records) and verify.
3. **Schema Validation**
   - Use tools like **SchemaCrawler** to compare schemas:
     ```java
     // Pseudocode: Generate SQL diff
     SchemaCrawler sc = new SchemaCrawler(settings);
     sc.compare(sourceDB, targetDB, ReportFormat.SQL);
     ```

### **During Migration**
- **Idempotency:** Design for retries (e.g., `DO NOTHING` on conflicts).
- **Checkpoints:** Save progress to resume after failures.
  ```python
  def migrate_with_checkpoints():
      checkpoint = get_last_checkpoint()  # e.g., from DB
      while checkpoint:
          migrate_next_batch(checkpoint)
          checkpoint += batch_size
          save_checkpoint(checkpoint)
  ```
- **Monitoring:** Set up alerts for:
  - Long-running transactions (`pg_stat_activity`).
  - High error rates (Prometheus + Alertmanager).

### **Post-Migration**
1. **Validation Scripts**
   ```python
   def validate_audit_data():
       # Check: No rows older than 30 days are missing
       assert len(missing_30day_rows()) == 0
   ```
2. **Rollback Plan**
   - Keep a reverse-migration script.
   ```sql
   -- Example: Revert a table
   CREATE TABLE source_audit_logs_reverted AS
   SELECT * FROM target_audit_table WHERE migrated = false;
   ```

---

## **5. Advanced: Handling Complex Scenarios**
### **Scenario: Cross-Database Migration (e.g., MySQL → PostgreSQL)**
- **Problem:** Different SQL dialects (e.g., `NOW()` vs. `CURRENT_TIMESTAMP`).
- **Fix:** Use a **transpiler** like `sqlx` (Rust) or **Alembic** (Python) to rewrite queries:
  ```python
  # Alembic migration example (Python)
  def upgrade():
      op.execute("SELECT NOW()::timestamp AS current_time")
      # Convert MySQL `NOW()` to PostgreSQL syntax
  ```

### **Scenario: Real-Time Audit Logs During Migration**
- **Problem:** Concurrent writes corrupt the migration.
- **Solution:** Use **database triggers** or **CDC (Change Data Capture)**:
  ```sql
  -- PostgreSQL: Log changes to a separate table
  CREATE OR REPLACE FUNCTION audit_trigger()
  RETURNS TRIGGER AS $$
  BEGIN
      INSERT INTO realtime_audit_table VALUES (NEW.*);
      RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER realtime_trigger
  AFTER INSERT ON users FOR EACH ROW
  EXECUTE FUNCTION audit_trigger();
  ```

---

## **Summary Checklist for Quick Resolution**
| **Step**               | **Action**                                      |
|------------------------|------------------------------------------------|
| 1. **Reproduce**       | Run migration with `--verbose` logs.           |
| 2. **Isolate**         | Check one batch; narrow down to a specific record. |
| 3. **Validate Data**   | Compare counts, timestamps, and schemas.       |
| 4. **Fix**             | Apply fixes iteratively (e.g., add indexes).   |
| 5. **Test**            | Verify with a subset before full rollout.      |
| 6. **Monitor**         | Set up alerts for future issues.               |

---
**Final Note:** Audit migrations are **high-risk, high-reward**. Always:
- **Test in staging** with production-like data.
- **Document assumptions** (e.g., "Source timestamps are in UTC").
- **Communicate failures** to stakeholders proactively.