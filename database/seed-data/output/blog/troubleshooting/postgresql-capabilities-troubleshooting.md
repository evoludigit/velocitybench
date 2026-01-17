# **Debugging PostgreSQL-Specific Features: A Troubleshooting Guide**
*(Focused on Common PostgreSQL Capabilities & Edge Cases)*

---

## **1. Introduction**
PostgreSQL is renowned for its advanced features—partitioning, JSON/JSONB, window functions, CTEs, triggers, and extension-based functionality (like `pg_trgm`, `pg_stat_statements`). While these capabilities enhance performance and flexibility, they can also introduce subtle bugs.

This guide provides a **practical, step-by-step** approach to diagnosing and resolving PostgreSQL-specific issues efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, systematically verify the following symptoms:

### **General Symptoms**
✅ **Performance degradation** (e.g., prolonged query times, locking issues)
✅ **Unexpected query behavior** (e.g., wrong results, errors on certain operations)
✅ **Extension-related failures** (e.g., `CREATE EXTENSION` errors, missing functions)
✅ **Serialization issues** (e.g., deadlocks, "cache invalidated" errors)
✅ **JSON/JSONB parsing failures** (e.g., incorrect schema inference, missing operators)
✅ **Partitioning-related errors** (e.g., `distribute by` failures, `LIST` partition misconfigurations)

### **PostgreSQL Version-Specific Quirks**
- **Pre-11.0**: Some `WITH` clause behaviors differ (e.g., recursive CTEs).
- **12.0+**: `UNLOGGED` tables may behave unexpectedly in replication.
- **14.0+**: `ANALYZE` may ignore certain partitioning stats until a full refresh.

---

## **3. Common Issues & Fixes**

### **3.1 JSON/JSONB Operations Fail**
**Symptom**: Queries like `->`, `#>>`, or aggregation functions (`json_agg`) produce incorrect results.
**Possible Causes**:
- Schema drift (e.g., expected structure changed).
- Missing `jsonb` vs. `json` handling (e.g., `jsonb_path_query` vs. `json_path_query`).
- Null handling in nested structures.

**Debugging Steps**:
1. **Inspect Sample Data**:
   ```sql
   SELECT to_jsonb(column) FROM your_table LIMIT 5;
   ```
   Compare against expected schema.

2. **Check for Nulls**:
   ```sql
   SELECT COUNT(*) FROM your_table WHERE column->>'key' IS NULL;
   ```

3. **Fix with Explicit Casting** (if schema mismatch):
   ```sql
   SELECT column::jsonb->>'key' FROM your_table;  -- Force JSONB
   ```

### **3.2 Partitioning Misconfiguration**
**Symptom**: Partitioned table fails to distribute data correctly, or queries ignore partitions.
**Possible Causes**:
- Incorrect `DISTRIBUTE BY` clause (e.g., wrong column type).
- Missing `PARTITION OF` reference.
- Inheritance mismatch (e.g., parent table not created properly).

**Debugging Steps**:
1. **Verify Partitioning Structure**:
   ```sql
   SELECT * FROM pg_partitioned_tables();  -- PostgreSQL 12+
   ```
   or:
   ```sql
   SELECT table_name, partition_method FROM information_schema.tables
   WHERE table_schema = 'public';
   ```

2. **Test Data Distribution**:
   ```sql
   SELECT partition_key, COUNT(*)
   FROM your_table
   GROUP BY partition_key;
   ```

3. **Recreate Partitions** (if corrupted):
   ```sql
   DROP TABLE your_table CASCADE;
   CREATE TABLE your_table (
     id BIGSERIAL,
     data VARCHAR(255)
   ) PARTITION BY LIST (data);
   ```

### **3.3 Triggers Failing Silently**
**Symptom**: Triggers execute but don’t update dependent data (e.g., views, other tables).
**Possible Causes**:
- Missing `BEFORE/AFTER` trigger timing.
- Error in trigger function (e.g., missing `RETURNS TRIGGER`).
- Row-level security (RLS) conflicts.

**Debugging Steps**:
1. **Check Trigger Definition**:
   ```sql
   SELECT event_object_table, function_name, trigger_type
   FROM information_schema.triggers;
   ```

2. **Test Trigger Manually**:
   ```sql
   CALL your_trigger_function('inserted_row_data');
   ```

3. **Enable Logging** (in `postgresql.conf`):
   ```
   log_statement = 'all'
   log_min_duration_statement = 0
   ```
   Then inspect logs for errors.

### **3.4 Recursive CTEs Hanging or Misbehaving**
**Symptom**: Recursive CTEs time out or return unexpected rows.
**Possible Causes**:
- Missing `MATERIALIZED` clause in PostgreSQL <12.
- Infinite recursion (no termination condition).
- Heavy join operations in recursion.

**Debugging Steps**:
1. **Verify Recursion Logic**:
   ```sql
   WITH RECURSIVE cte AS (
     SELECT ...  -- Initial query
     UNION ALL
     SELECT ...  -- Recursive part
     WHERE ...   -- Termination condition
   )
   SELECT * FROM cte;
   ```

2. **Add `LIMIT` for Testing**:
   ```sql
   WITH RECURSIVE cte AS (...)
   SELECT * FROM cte LIMIT 100;
   ```

3. **Use `MATERIALIZED` (PostgreSQL 12+)**:
   ```sql
   WITH RECURSIVE cte AS (
     SELECT ... MATERIALIZED
     UNION ALL
     SELECT ...
   )
   ```

### **3.5 `pg_trgm` Performance Issues**
**Symptom**: Full-text search queries are slow despite `pg_trgm` installation.
**Possible Causes**:
- Missing `pg_trgm` extension.
- GIN index not created.
- Incorrect tokenization (e.g., `trgm_similarity` vs. `websearch_to_tsquery`).

**Debugging Steps**:
1. **Verify Extension**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS pg_trgm;
   ```

2. **Check for GIN Index**:
   ```sql
   CREATE INDEX idx_search ON search_table USING GIN (text_column gin_trgm_ops);
   ```

3. **Test with `similarity`**:
   ```sql
   SELECT similarity('apple', 'apples') > 0.8;
   ```

---

## **4. Debugging Tools & Techniques**

### **4.1 PostgreSQL Extras**
- **`pgBadger`**: Log analyzer for performance bottlenecks.
  ```bash
  pgbadger /path/to/postgresql.log
  ```
- **`pg_mustard`**: Visualizes query plans.
- **`pev` (PostgreSQL Explain Visualizer)**: Simplifies `EXPLAIN` output.

### **4.2 Query Profiling**
1. **Enable Query Slowness Logging**:
   ```sql
   SET log_min_duration_statement = 1000;  -- Log queries >1s
   ```
2. **Use `EXPLAIN ANALYZE`**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM large_table WHERE jsonb_column->>'key' = 'value';
   ```
   Look for **sequential scans**, **high cost**, or **partition skips**.

### **4.3 Advanced Logging**
- **`postgres.conf` Tuning** (for debugging):
  ```
  log_temp_files = 0  -- Log temp file usage
  log_lock_waits = on  -- Track lock contention
  ```
- **`pg_stat_statements`** (Enable with `CREATE EXTENSION`):
  ```sql
  SELECT query, calls, total_time FROM pg_stat_statements
  ORDER BY total_time DESC LIMIT 10;
  ```

### **4.4 Replication Debugging**
- **Check `pg_stat_replication`** for lag:
  ```sql
  SELECT * FROM pg_stat_replication;
  ```
- **Verify `recovery.conf`** (standby servers):
  ```bash
  psql -U postgres -h standby_host -c "SHOW primary_conninfo;"
  ```

---

## **5. Prevention Strategies**

### **5.1 Version Compatibility**
- **Test on Same PostgreSQL Version** as production.
- **Use `CREATE TABLE ... LIKE`** for partitioning templates to avoid schema drift.

### **5.2 Schema Design**
- **Avoid `json` vs. `jsonb` Mixing**: Stick to one type per column.
- **Partitioning Best Practices**:
  - Use `INTEGER RANGE` for time-series data.
  - Avoid `LIST` partitioning unless static.

### **5.3 Query Optimization**
- **Use `EXPLAIN` Early**: Profile before finalizing queries.
- **Leverage `WITH` for Large CTEs**:
  ```sql
  WITH filtered AS (SELECT * FROM large_table WHERE condition)
  SELECT * FROM filtered;
  ```

### **5.4 Extension Management**
- **Document Dependencies**: Track required extensions (e.g., `citus`, `plpython3u`).
- **Test Extension Updates**: Avoid breaking changes.

### **5.5 Backup & Rollback Planning**
- **Use `pg_dump` with `--clean`** for partitioned tables:
  ```bash
  pg_dump --clean --if-exists --schema public your_db > dump.sql
  ```
- **Test Restore** on a staging environment.

---

## **6. Conclusion**
PostgreSQL’s power comes with complexity. By following this structured approach:
1. **Systematically check symptoms** (performance, correctness).
2. **Use targeted debugging tools** (`EXPLAIN`, `pg_stat_statements`).
3. **Prevent issues** with version control, schema design, and testing.

For persistent problems, **check PostgreSQL’s version-specific documentation** ([docs.postgresql.org](https://docs.postgresql.org/)) and the [#postgresql IRC channel](https://irc.postgresql.org/).

---
**Next Steps**:
- If the issue persists, **open a debug-level query** in the PostgreSQL community forums.
- For performance bottlenecks, **share `EXPLAIN ANALYZE` logs**.