# **Debugging Consistency Migration: A Troubleshooting Guide**

## **Introduction**
The **Consistency Migration** pattern is used when a system evolves from an eventual to a strongly consistent model while minimizing downtime. This often involves rewriting data to ensure current reads always reflect the latest state. However, inconsistencies, performance bottlenecks, or migration failures can occur.

This guide helps diagnose and resolve common issues during or after a Consistency Migration.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms to confirm a Consistency Migration issue:

| **Symptom** | **Description** | **Impact** |
|------------|----------------|------------|
| **Inconsistent Reads** | Some queries return stale data despite recent writes. | Data correctness issues. |
| **High Latency** | Operations are slower than expected during migration. | Poor user experience. |
| **Failed Migrations** | Migration jobs stalled or errored out. | Partial or incomplete migration. |
| **Duplicate Data** | Extra records appear in the system. | Data integrity problems. |
| **Error Logs** | Errors like `MigrationInProgress`, `SourceUnavailable`, or `TargetSchemaMismatch` in logs. | Technical blocking issues. |
| **Deadlocks/Timeouts** | Long-running transactions or stuck processes. | System unresponsiveness. |

---
## **2. Common Issues and Fixes**

### **Issue 1: Inconsistent Reads (Stale Data)**
**Cause:**
- Not all data was rewritten before enabling strong consistency.
- Reads still hitting an eventual consistency layer.

**Debugging Steps:**
1. **Check Migration Status**
   ```bash
   # Example: Query migration status in a database
   SELECT * FROM migration_status WHERE target_table = 'orders';
   ```
   - If `is_complete = false`, migration is incomplete.

2. **Verify Replication Lag**
   ```sql
   -- PostgreSQL example: Check replication lag
   SELECT pg_is_in_recovery(), lag_time;
   ```
   - If `lag_time` is high, replication is slow.

3. **Force Sync (If Applicable)**
   ```bash
   # In Kafka/Event Sourcing, reprocess lagging partitions
   kafka-consumer-groups --bootstrap-server <broker> --group <topic-group> --describe
   ```
   - Manually rewind consumers if stuck.

**Fix:**
- **Redo Failed Records** (if partial migration occurs):
  ```python
  def retry_failed_records():
      failed = db.query("SELECT id FROM migration_log WHERE status = 'failed'")
      for record in failed:
          rewrite_data(record.id)  # Re-run migration logic
  ```
- **Enable Strong Consistency Early** (if using CDC):
  ```yaml
  # Example: Prometheus alert for replication lag
  alert: ReplicationLagHigh
    expr: avg(rate(cdc_lag_bytes[5m])) > 10000
  ```

---

### **Issue 2: High Latency During Migration**
**Cause:**
- Heavy write load overwhelming the migration process.
- Lock contention on target tables.

**Debugging Steps:**
1. **Monitor Database Load**
   ```sql
   -- PostgreSQL: Check active queries
   SELECT query, count(*) FROM pg_stat_statements GROUP BY query;
   ```
   - Look for slow `INSERT`/`UPDATE` statements.

2. **Check Queue Backlog**
   ```bash
   # Kafka lag monitoring
   kafka-consumer-groups --bootstrap-server <broker> --group migration-group --describe
   ```
   - If lag > 1000 messages, throttling is needed.

3. **Analyze Lock Contention**
   ```sql
   -- MySQL: Lock wait analysis
   SHOW ENGINE INNODB STATUS;
   ```
   - Look for `Buffer Pool and Memory` or `TRANSACTION` sections.

**Fix:**
- **Batch Processing**
  ```python
  def batch_migrate(records, batch_size=1000):
      for i in range(0, len(records), batch_size):
          chunk = records[i:i + batch_size]
          db.execute_bulk("INSERT INTO target (...) VALUES (...)", chunk)
  ```
- **Optimize Target Schema**
  ```sql
  -- Add indexes to speed up writes
  CREATE INDEX idx_migration_id ON target_table(id);
  ```

---

### **Issue 3: Failed Migrations (Stalled Jobs)**
**Cause:**
- Network failures.
- Schema drift between source and target.
- Timeout errors.

**Debugging Steps:**
1. **Check Job Logs**
   ```bash
   # Example: Airflow task logs
   airflow tasks logs <dag_id> <task_id>
   ```
   - Look for `ConnectionError`, `SchemaError`, or `Timeout`.

2. **Validate Schema Compatibility**
   ```sql
   -- Compare source and target columns
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'orders'
   ORDER BY column_name;
   ```
   - If schema mismatches, adjust mapping logic.

3. **Network Diagnostics**
   ```bash
   # Ping and latency checks
   ping <database_host>
   mtr <database_host>
   ```

**Fix:**
- **Restart Failed Jobs**
  ```bash
  # Retry failed tasks in Airflow
  airflow dags backfill --retries 3 <dag_id>
  ```
- **Update Schema Gradually**
  ```python
  def migrate_with_schema_fallback():
      try:
          db.migrate_normal()
      except SchemaMismatch:
          db.migrate_fallback_mode()  # Use lighter schema
  ```

---

### **Issue 4: Duplicate Data**
**Cause:**
- Race conditions in migration logic.
- Incorrect `ON DUPLICATE KEY UPDATE` handling.

**Debugging Steps:**
1. **Check for Duplicates**
   ```sql
   -- Find duplicates in target table
   SELECT id, COUNT(*) as cnt
   FROM target_table
   GROUP BY id
   HAVING cnt > 1;
   ```
2. **Review Migration Logic**
   ```python
   # Example: Safe UPSERT in SQLAlchemy
   db.session.execute(
       "INSERT INTO target (...) VALUES (...) ON CONFLICT (id) DO UPDATE SET ..."
   )
   ```

**Fix:**
- **Idempotent Writes**
  ```python
  def safe_insert(id, data):
      if not db.exists(id):
          db.insert(id, data)  # Only if not present
  ```
- **Use Database-Side Deduplication**
  ```sql
  -- PostgreSQL: Handle duplicates via CHECK constraints
  CREATE UNIQUE INDEX unique_id ON target_table(id);
  ```

---

### **Issue 5: Deadlocks/Timeouts**
**Cause:**
- Long-running transactions.
- Heavy write contention.

**Debugging Steps:**
1. **Check Active Transactions**
   ```sql
   -- PostgreSQL: List long-running transactions
   SELECT pid, now() - xact_start AS duration
   FROM pg_stat_activity
   WHERE state = 'active' AND duration > '1m';
   ```
2. **Analyze Locks**
   ```sql
   -- MySQL: Show lock wait
   SHOW ENGINE INNODB STATUS;
   ```

**Fix:**
- **Break Transactions into Smaller Batches**
  ```python
  def migrate_in_batches(batch_size=500):
      for offset in range(0, total_records, batch_size):
          batch = db.query("SELECT * FROM source LIMIT %s OFFSET %s", batch_size, offset)
          db.migrate_batch(batch)
  ```
- **Use Read-Committed Isolation**
  ```sql
  SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
  ```

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique** | **Use Case** | **Example Command** |
|---------------------|-------------|---------------------|
| **Database Exporters** | Analyze replication lag. | `pg_dump --table=target` (PostgreSQL) |
| **APM Tools** (Datadog, New Relic) | Track migration performance. | `SELECT * FROM tracing_metrics;` |
| **Log Aggregation** (ELK, Loki) | Filter migration errors. | `kibana: index=logs.* AND message:"MigrationFailed"` |
| **Schema Diff Tools** (Sqitch, Flyway) | Compare source/target schemas. | `sqitch diff --dry-run` |
| **Load Testing** (Locust, JMeter) | Validate migration under load. | `locust -f migration_test.py` |

---

## **4. Prevention Strategies**

### **Pre-Migration Checks**
1. **Test Migration in Staging**
   ```bash
   # Run migration on a staging DB
   ./migrate.sh --environment staging
   ```
2. **Backup Source Data**
   ```bash
   # Example: Pre-migration backup
   mysqldump -u user -p db_name > backup.sql
   ```
3. **Monitor Migration Progress**
   ```python
   def monitor_migration():
       while not is_complete():
           print(f"Progress: {get_completion_rate()}")
           time.sleep(60)
   ```

### **During Migration**
- **Use Circular Rewriting** (for large datasets):
  ```python
  def circular_migrate(total_records, batch_size=1000):
      for i in range(batch_size, total_records, batch_size):
          db.migrate_chunk(i - batch_size, i)
  ```
- **Implement Circuit Breakers** (for retries):
  ```python
  from tenacity import retry, stop_after_attempt

  @retry(stop=stop_after_attempt(3))
  def retryable_migrate():
      db.migrate()
  ```

### **Post-Migration**
- **Validate Data Integrity**
  ```sql
  -- Check row counts match
  SELECT COUNT(*) FROM source_table;
  SELECT COUNT(*) FROM target_table;
  ```
- **Monitor for Regression**
  ```bash
  # Alert if consistency drops
  prometheus alert: ConsistencyFailed if (read_latency > 1s) for 5m
  ```

---

## **Conclusion**
Consistency Migration is critical but complex. Focus on:
✅ **Verification** (check logs, schemas, and progress).
✅ **Performance Optimization** (batch processing, indexing).
✅ **Fallbacks** (idempotency, schema flexibility).

Use the tools above to detect issues early and **test migrations in staging before production**. If stuck, refer to database-specific docs (e.g., PostgreSQL replication tuning, Kafka CDC retries).

For deeper issues, consider:
- **Database-Specific Tuning** (e.g., `innodb_buffer_pool_size` in MySQL).
- **Event Sourcing** (if migrations are too slow).

---