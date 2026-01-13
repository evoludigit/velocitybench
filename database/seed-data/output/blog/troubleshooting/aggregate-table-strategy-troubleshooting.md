# **Debugging "Aggregate Tables for Pre-Computed Rollups (ta_*)" – A Troubleshooting Guide**
*For Backend Engineers*

---

## **1. Introduction**
This guide helps debug performance issues related to the **pre-computed rollup table pattern (ta_*)**, where aggregated data is stored in materialized tables (e.g., `ta_daily_metrics`, `ta_hourly_revenue`) to avoid expensive real-time aggregations. If dashboards are slow, queries repeat excessively, or the database is overloaded by aggregations, this guide provides a structured approach to diagnose and fix the problem.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms (check all that apply):

| **Symptom** | **Severity** | **How to Confirm** |
|--------------|-------------|--------------------|
| ✅ Dashboard load time > 5s for simple charts | High | Log query execution time (e.g., `EXPLAIN ANALYZE`) |
| ✅ Same `GROUP BY` queries run thousands of times daily | High | Check slow query logs, query monitoring tools (e.g., Datadog, Percona PMM) |
| ✅ Database CPU spikes during business hours | High | Monitor CPU usage (e.g., `pg_stat_activity`, `sysstat -S`) |
| ✅ Missing or stale data in `ta_*` tables | Medium | Compare `ta_daily_metrics` counts with raw data (e.g., `SELECT COUNT(*) FROM transactions`) |
| ✅ Large `ta_*` tables growing uncontrollably | Medium | Check table sizes (`SELECT pg_size_pretty(pg_total_relation_size('ta_daily_metrics'))`) |
| ✅ Inserts/updates to `ta_*` tables are slow | Medium | Log `INSERT`/`UPDATE` times (e.g., `EXPLAIN ANALYZE INSERT INTO ta_daily_metrics...`) |
| ✅ Missing indexes on `ta_*` tables | Low | Verify index coverage (`EXPLAIN ANALYZE` missing `Index Scan`) |
| ✅ Schema changes breaking rollup logic | Low | Audit recent schema migrations affecting `ta_*` tables |

**Action:**
- Prioritize fixing **High** symptoms first.
- If **Medium** symptoms exist but no **High** issues, investigate further (see Section 3).

---

## **3. Common Issues & Fixes**

### **Issue 1: Pre-Computed Rollups Are Missing or Stale**
**Symptoms:**
- Dashboards show incorrect aggregated data.
- Raw data exists, but `ta_*` tables are empty or outdated.

**Root Causes:**
1. **Rollup jobs failed silently** (e.g., cron job missed, retry logic broken).
2. **Incremental updates not working** (e.g., logic skips new records).
3. **Schema drift** (e.g., raw table columns changed, but rollups didn’t adapt).

**Debugging Steps:**
1. **Check job logs:**
   ```bash
   # Example for a Python-based rollup job
   journalctl -u rollup-job --no-pager -n 50  # Systemd
   # OR
   grep "ERROR" /var/log/rollup-job.log
   ```
2. **Verify rollup coverage:**
   ```sql
   -- Compare counts: Are all raw records in ta_*?
   SELECT COUNT(*) FROM transactions WHERE date = CURRENT_DATE;
   SELECT COUNT(*) FROM ta_daily_metrics WHERE date = CURRENT_DATE;
   ```
3. **Test incremental logic:**
   ```python
   # Example: Ensure only new records are processed
   last_processed = get_last_rollup_timestamp()
   new_records = Transactions.query.filter(
       Transactions.timestamp > last_processed
   ).all()
   assert len(new_records) > 0, "No new records to process!"
   ```

**Fixes:**
- **Add health checks** to rollup jobs:
  ```python
  def run_rollup():
      try:
          process_new_data()
          log_success("Rollup completed for {timestamp}")
      except Exception as e:
          log_error(f"Rollup failed: {e}")
          raise  # Trigger alerting
  ```
- **Use incremental IDs** (if applicable):
  ```sql
  -- Example: Rollup only rows with id > last_rollup_id
  INSERT INTO ta_daily_metrics
  SELECT date_trunc('day', t.timestamp), SUM(amount)
  FROM transactions t
  WHERE t.id > (SELECT MAX(id) FROM ta_daily_metrics)
  GROUP BY 1;
  ```
- **Re-run failed jobs:**
  ```bash
  python rollup_script.py --force-full-run  # Fallback to full reprocessing
  ```

---

### **Issue 2: Repeated Aggregations (ta_* Tables Ignored)**
**Symptoms:**
- Same `GROUP BY` queries run thousands of times per day (e.g., 1000x `SELECT SUM(...) GROUP BY date`).
- `EXPLAIN ANALYZE` shows `Seq Scan` on raw tables instead of `Index Scan` on `ta_*`.

**Root Causes:**
1. **Application queries bypass `ta_*` tables** (e.g., hardcoded aggregations).
2. **Cache invalidation not working** (e.g., stale cache forces re-aggregation).
3. **Missing indexes** on `ta_*` tables for query patterns.

**Debugging Steps:**
1. **Inspect query plans:**
   ```sql
   EXPLAIN ANALYZE
   SELECT date, SUM(revenue) FROM ta_daily_metrics WHERE date BETWEEN '2023-01-01' AND '2023-01-31'
   GROUP BY 1;
   ```
   - **Bad:** Uses `Seq Scan` on raw tables.
   - **Good:** Uses `Index Scan` on `ta_daily_metrics`.

2. **Check application code:**
   ```python
   # Example: Bad - Hardcoded aggregation
   def get_monthly_revenue():
       return db.session.query(func.sum(Revenue.amount)).group_by(func.date_trunc('month', Revenue.timestamp)).all()
   ```
   ```python
   # Example: Good - Uses ta_* table
   def get_monthly_revenue():
       return db.session.query(ta_daily_metrics.date, func.sum(ta_daily_metrics.revenue)) \
               .filter(ta_daily_metrics.date.between('2023-01-01', '2023-01-31')) \
               .group_by(ta_daily_metrics.date).all()
   ```

3. **Audit query logs:**
   ```bash
   # PostgreSQL slow query log
   psql -c "SELECT query, calls, total_time FROM pg_stat_statements ORDER BY calls DESC LIMIT 10;"
   ```

**Fixes:**
- **Enforce `ta_*` usage in queries:**
  ```python
  # Add a query validator (e.g., SQLAlchemy event)
  from sqlalchemy import event

  @event.listens_for(Revenue.query, 'after_compile')
  def validate_revenue_query(element, clauseelement, **kw):
      if "GROUP BY" in str(clauseelement):
          raise Exception("Use ta_daily_metrics instead of raw aggregation!")
  ```
- **Add cache headers** (if applicable):
  ```python
  # Example: API response with Cache-Control
  @app.route('/api/revenue')
  def revenue():
      response = make_response(jsonify(data))
      response.headers['Cache-Control'] = 'max-age=3600'  # 1 hour
      return response
  ```
- **Optimize `ta_*` indexes:**
  ```sql
  -- Ensure indexes cover common query patterns
  CREATE INDEX idx_ta_daily_metrics_date ON ta_daily_metrics(date);
  CREATE INDEX idx_ta_daily_metrics_date_product ON ta_daily_metrics(date, product_id);
  ```

---

### **Issue 3: High CPU Due to Rollup Jobs**
**Symptoms:**
- Database CPU 100% during rollup job execution.
- `pg_stat_activity` shows long-running `INSERT`/`UPDATE` on `ta_*`.

**Root Causes:**
1. **Full-table scans** during rollup (no incremental logic).
2. **Large `ta_*` tables** with inefficient joins/aggregations.
3. **Concurrent rollup jobs** competing for resources.

**Debugging Steps:**
1. **Profile rollup job:**
   ```sql
   -- Check the cost of the rollup query
   EXPLAIN ANALYZE
   INSERT INTO ta_daily_metrics
   SELECT date_trunc('day', t.timestamp), SUM(t.amount)
   FROM transactions t
   WHERE t.timestamp >= '2023-01-01'
   GROUP BY 1;
   ```
   - Look for `Seq Scan`, `Hash Aggregate`, or `Nested Loop` with high cost.

2. **Monitor concurrent jobs:**
   ```sql
   SELECT pid, usename, query, now() - query_start AS runtime
   FROM pg_stat_activity
   WHERE query LIKE '%INSERT INTO ta_%'
   ORDER BY runtime DESC;
   ```

**Fixes:**
- **Optimize rollup queries:**
  ```sql
  -- Use incremental IDs (if possible)
  INSERT INTO ta_daily_metrics
  SELECT date_trunc('day', t.timestamp), SUM(t.amount)
  FROM transactions t
  WHERE t.id > (SELECT COALESCE(MAX(id), 0) FROM ta_daily_metrics)
  GROUP BY 1;
  ```
- **Partition `ta_*` tables** (for PostgreSQL):
  ```sql
  CREATE TABLE ta_daily_metrics (
      date DATE NOT NULL,
      revenue NUMERIC,
      -- other columns
  ) PARTITION BY RANGE (date);
  ```
- **Schedule rollups off-peak:**
  ```bash
  # Example: Run during low-traffic hours
  0 3 * * * /usr/bin/python3 /app/rollup_job.py >> /var/log/rollup.log 2>&1
  ```
- **Limit concurrent jobs:**
  ```python
  # Use a semaphore or database lock
  import psycopg2
  conn = psycopg2.connect("dbname=rollups")
  with conn.cursor() as cur:
      cur.execute("SELECT pg_try_advisory_lock(12345)")
      if cur.fetchone()[0]:
          run_rollup()
          cur.execute("SELECT pg_advisory_unlock(12345)")
      else:
          print("Rollup in progress, skipping")
  ```

---

### **Issue 4: Missing Indexes on ta_* Tables**
**Symptoms:**
- `EXPLAIN ANALYZE` shows `Seq Scan` instead of `Index Scan`.
- Queries are slow despite `ta_*` being pre-computed.

**Root Causes:**
- Missing indexes for `GROUP BY`, `WHERE`, or `JOIN` clauses.
- Overly broad indexes (high maintenance cost).

**Debugging Steps:**
1. **Analyze query plans:**
   ```sql
   EXPLAIN ANALYZE
   SELECT date, SUM(revenue) FROM ta_daily_metrics
   WHERE date BETWEEN '2023-01-01' AND '2023-01-31'
   GROUP BY 1;
   ```
   - **Bad:** `Seq Scan` on `ta_daily_metrics` (1M rows).
   - **Good:** `Index Scan` using `idx_ta_daily_metrics_date`.

2. **Check missing indexes:**
   ```sql
   -- Find unused indexes (PostgreSQL)
   SELECT schemaname || '.' || relname AS table_name,
          indexrelname AS index_name,
          pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
   FROM pg_indexes
   WHERE indexrelname NOT LIKE 'pg_%'
   ORDER BY pg_relation_size(indexrelid) DESC;
   ```

**Fixes:**
- **Add targeted indexes:**
  ```sql
  -- Index for date-based queries
  CREATE INDEX idx_ta_daily_metrics_date ON ta_daily_metrics(date);

  -- Index for date + product_id queries
  CREATE INDEX idx_ta_daily_metrics_date_product ON ta_daily_metrics(date, product_id);
  ```
- **Use partial indexes** (if filtering is common):
  ```sql
  CREATE INDEX idx_active_revenue ON ta_daily_metrics(date) WHERE revenue > 0;
  ```
- **Avoid over-indexing:**
  - Limit indexes to **common query patterns** (use `ANALYZE` to confirm usage).

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique** | **Purpose** | **Example Command/Query** |
|--------------------|-------------|---------------------------|
| **Slow Query Log** | Identify expensive queries | `pg_stat_statements` (PostgreSQL) |
| **EXPLAIN ANALYZE** | Analyze query execution | `EXPLAIN ANALYZE SELECT * FROM ta_daily_metrics WHERE date = '2023-01-01';` |
| **Database Monitoring** | Track CPU, locks, queries | `pg_stat_activity`, Datadog, Prometheus |
| **Query Digester** | Find duplicate queries | `pg_stat_statements` (show `query` and `calls`) |
| **Avoidish / pgBadger** | Log analysis | `pgBadger /var/log/postgresql/postgresql-*.log` |
| **Incremental Rollup Tests** | Verify new data is processed | `SELECT COUNT(*) FROM ta_daily_metrics WHERE date = CURRENT_DATE;` |
| **Lock Timeouts** | Detect blocking jobs | `SELECT pid, query, now() - query_start FROM pg_stat_activity WHERE state = 'active';` |

**Pro Tip:**
- Use **`pg_stat_statements`** to find the top 10 slowest queries:
  ```sql
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY mean_time DESC
  LIMIT 10;
  ```

---

## **5. Prevention Strategies**
To avoid future issues, implement these best practices:

### **A. Rollup Job Design**
1. **Always use incremental processing:**
   ```python
   def run_rollup():
       last_id = get_last_processed_id()
       new_data = RawData.query.filter(RawData.id > last_id).all()
       if not new_data:
           print("No new data, skipping")
           return
       # Process new_data
   ```
2. **Add retries for failed jobs:**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def run_rollup():
       # Logic here
   ```
3. **Log and alert on failures:**
   ```python
   import sms_api  # Hypothetical alerting

   def run_rollup():
       try:
           process_data()
       except Exception as e:
           log.error(f"Rollup failed: {e}")
           sms_api.send_alert("Database rollup failed!")
           raise
   ```

### **B. Database Schema**
1. **Partition `ta_*` tables** for large datasets:
   ```sql
   CREATE TABLE ta_daily_metrics (
       date DATE NOT NULL,
       revenue NUMERIC
   ) PARTITION BY RANGE (date);
   ```
2. **Use appropriate data types:**
   - Replace `TEXT` with `VARCHAR(255)` for fixed-length data.
   - Use `NUMERIC` instead of `FLOAT` for precise aggregations.
3. **Add indexes proactively:**
   - Index all `GROUP BY`, `WHERE`, and `JOIN` columns in `ta_*`.

### **C. Application Layer**
1. **Enforce `ta_*` usage in queries:**
   - Use **SQLAlchemy events** or **database triggers** to block raw aggregations.
2. **Cache API responses:**
   - Use **Redis** or **Varnish** for dashboard queries.
   ```python
   @app.route('/api/revenue')
   @cache.cached(timeout=3600)
   def revenue():
       return jsonify(get_revenue_from_ta_tables())
   ```
3. **Validate schema changes:**
   - Use **migrations** (e.g., Alembic) to track schema drift.
   - Run **data consistency checks** after deployments:
     ```sql
     -- Verify counts match between raw and ta_* tables
     SELECT
         "raw_count" := COUNT(*) FROM transactions,
         "rollup_count" := COUNT(*) FROM ta_daily_metrics
     WHERE date = '2023-01-01';
     ```

### **D. Monitoring & Alerting**
1. **Monitor rollup job success:**
   - Alert if a rollup job fails or misses a run.
2. **Track query performance:**
   - Set alerts for slow queries on `ta_*` tables.
3. **Monitor table growth:**
   - Alert if `ta_*` tables grow uncontrollably.
   ```sql
   -- Example: Alert if ta_daily_metrics grows >10% in a day
   SELECT
       NOW() - last_check AS time_since_check,
       pg_size_pretty(pg_total_relation_size('ta_daily_metrics')) AS current_size,
       pg_size_pretty(pg_total_relation_size('ta_daily_metrics') - last_size) AS size_change
   FROM (
       SELECT pg_total_relation_size('ta_daily_metrics') AS last_size, NOW() AS last_check
   ) prev;
   ```

---

## **6. Summary Checklist for Resolution**
| **Step** | **Action** | **Tool/Query** |
|----------|------------|----------------|
| 1 | Verify `ta_*` tables exist and are populated | `SELECT COUNT(*) FROM ta_daily_metrics;` |
| 2 | Check for missing incremental logic | Compare raw vs. rollup counts |
| 3 | Audit application queries for raw aggregations | `EXPLAIN ANALYZE`, code review |
| 4 | Optimize query plans with indexes | `CREATE INDEX` on common columns |
| 5 | Schedule rollups during off-peak hours | `crontab`, `pg_cron` |
| 6 | Monitor job success and query performance | `pg_stat_statements`, Datadog |
| 7 | Add retries and alerts for failed jobs | Custom scripts, SMS/email alerts |
| 8 | Partition large `ta_*` tables | `CREATE