# **Debugging Database Guidelines: A Troubleshooting Guide**
*For Backend Engineers*

Databases are the foundation of most applications, yet misconfigurations, performance bottlenecks, and structural issues can lead to system failures. This guide provides a **practical, step-by-step approach** to diagnosing and resolving common database-related problems efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, identify which symptoms match your issue. Check off relevant signs:

| **Category**          | **Symptoms**                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Performance Issues** | Slow queries, high CPU/memory usage, timeouts, database locks, high latency |
| **Connectivity Problems** | Connection refused, handshake errors, "Connection timed out"               |
| **Data Corruption**    | Inconsistent data, duplicate entries, missing records, deadlocks            |
| **Configuration Errors** | "Table doesn’t exist," "Permission denied," "Disk full" errors          |
| **High Resource Usage** | Full disk space, excessive log growth, excessive lock contention          |
| **Backup & Recovery Failures** | Failed backups, restore errors, version mismatches                      |

**Action:** If multiple symptoms appear simultaneously, prioritize based on impact (e.g., a system-wide freeze due to a deadlock is more urgent than slow queries).

---

## **2. Common Issues and Fixes (With Code Examples)**

### **2.1 Slow Query Performance**
**Symptoms:**
- Queries taking >1 second to execute (arbitrary threshold).
- High `Slow Query Log` entries in database logs.
- Application latency spikes.

**Root Causes:**
- Missing indexes on frequently queried columns.
- `SELECT *` queries fetching unnecessary columns.
- Lack of query optimization (e.g., `NOT IN` instead of `NOT EXISTS`).
- Insufficient database resources (CPU, RAM).

#### **Debugging Steps:**
1. **Identify the slow query:**
   ```sql
   -- PostgreSQL: Find slow queries
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```
   ```sql
   -- MySQL: Check slow query log
   SHOW GLOBAL STATUS LIKE '%Slow_queries%';
   ```

2. **Optimize the query:**
   - Add missing indexes:
     ```sql
     CREATE INDEX idx_user_email ON users(email);
     ```
   - Rewrite inefficient queries (e.g., replace `NOT IN` with `NOT EXISTS`):
     ```sql
     -- Bad (can cause performance issues)
     SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM bans);

     -- Better (uses indexes better)
     SELECT * FROM users WHERE NOT EXISTS (
       SELECT 1 FROM bans WHERE bans.user_id = users.id
     );
     ```

3. **Check for locking bottlenecks:**
   ```sql
   -- PostgreSQL: Find active locks
   SELECT * FROM pg_locks;
   ```

4. **Tune database parameters:**
   - Increase `work_mem` (PostgreSQL) or `innodb_buffer_pool_size` (MySQL).
   - Enable query caching (if applicable).

---

### **2.2 Connection Pool Exhaustion**
**Symptoms:**
- `Connection refused` or `TimeoutError` from the application.
- Logs show `Too many connections` errors.

**Root Causes:**
- Too few connections in the pool (default settings too low).
- Long-running transactions holding connections open.
- Memory leaks in the application (orphaned connections).

#### **Debugging Steps:**
1. **Check connection pool usage:**
   - For **PostgreSQL**, monitor:
     ```sql
     SELECT count(*) FROM pg_stat_activity WHERE state = 'active';
     ```
   - For **MySQL**, check:
     ```sql
     SHOW STATUS LIKE 'Threads_connected';
     ```

2. **Adjust connection pool settings (Python - `psycopg2` example):**
   ```python
   # Increase pool size (default=5)
   pool = psycopg2.pool.SimpleConnectionPool(
       minconn=5,
       maxconn=20,
       host="localhost",
       database="mydb"
   )
   ```

3. **Reduce transaction duration:**
   - Avoid `SELECT *` in transactions; fetch only needed data.
   - Use `BEGIN; COMMIT;` explicitly instead of implicit commits.

4. **Implement connection cleanup:**
   - Ensure connections are closed properly:
     ```python
     try:
         with pool.getconn() as conn:
             conn.cursor().execute("SELECT 1")
     finally:
         pool.putconn(conn)  # Return to pool
     ```

---

### **2.3 Data Corruption (Deadlocks, Duplicates, Missing Data)**
**Symptoms:**
- "Deadlock detected" errors.
- Duplicate records appearing unexpectedly.
- `NULL` values where they shouldn’t exist.

**Root Causes:**
- Missing constraints (e.g., `UNIQUE`, `PRIMARY KEY`).
- Race conditions in concurrent writes.
- Improper transaction management.

#### **Debugging Steps:**
1. **Check for deadlocks:**
   ```sql
   -- PostgreSQL: Resolve deadlocks
   SELECT pg_terminate_backend(pid) FROM pg_locks l JOIN pg_stat_activity a ON l.pid = a.pid WHERE NOT l.locktype = 'relation';
   ```

2. **Add missing constraints:**
   ```sql
   ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);
   ```

3. **Use transactions properly:**
   - Always wrap writes in transactions:
     ```python
     with conn.cursor() as cur:
         cur.execute("BEGIN")
         try:
             cur.execute("INSERT INTO users VALUES (%s, %s)", (name, email))
             cur.execute("COMMIT")
         except Exception as e:
             cur.execute("ROLLBACK")
             raise e
     ```

4. **Enable foreign key checks (if disabled):**
   ```sql
   SET FOREIGN_KEY_CHECKS = 1;  -- MySQL
   ```

---

### **2.4 High Disk Usage / Full Disk**
**Symptoms:**
- "Disk full" errors.
- Slow performance due to disk I/O bottlenecks.
- Large `pg_log` or `innodb_log_file` files.

**Root Causes:**
- Unbounded log retention.
- Large tables without partitioning.
- Missing `VACUUM` (PostgreSQL) or `OPTIMIZE TABLE` (MySQL).

#### **Debugging Steps:**
1. **Check disk usage:**
   ```bash
   # PostgreSQL: Check tablespace size
   SELECT pg_size_pretty(pg_total_relation_size('schema.table')) AS size;
   ```

2. **Clean up old logs:**
   - **PostgreSQL:** Adjust `log_rotation_age` and `log_rotation_size` in `postgresql.conf`.
   - **MySQL:** Enable binary logging with retention:
     ```sql
     SET GLOBAL log_bin_trust_function_creators = 1;
     SET GLOBAL expire_logs_days = 7;
     ```

3. **Partition large tables:**
   ```sql
   -- MySQL: Add partition key
   ALTER TABLE logs ADD COLUMN date DATE;
   ALTER TABLE logs PARTITION BY RANGE (YEAR(date)) (
       PARTITION p2023 VALUES LESS THAN (2024)
   );
   ```

4. **Run maintenance commands:**
   - **PostgreSQL:**
     ```sql
     VACUUM ANALYZE users;  -- Reclaim space
     ```
   - **MySQL:**
     ```sql
     OPTIMIZE TABLE users;  -- Rebuild table
     ```

---

## **3. Debugging Tools and Techniques**

### **3.1 Database-Specific Tools**
| Database  | Tool/Library | Purpose |
|-----------|-------------|---------|
| PostgreSQL | `pgAdmin`, `pgBadger`, `pg_mustard` | Log analysis, performance monitoring |
| MySQL      | `Percona PMM`, `MySQL Workbench`, `pt-query-digest` | Query profiling, slow query analysis |
| MongoDB    | `mongostat`, `mongotop`, `mongodump` | Metrics, backup/recovery |

### **3.2 General Debugging Techniques**
1. **Enable Slow Query Logging:**
   - **PostgreSQL:** Add to `postgresql.conf`:
     ```ini
     slow_query_file = '/var/log/postgresql/slow.log'
     slow_query_threshold = '100ms'
     ```
   - **MySQL:** Run:
     ```sql
     SET GLOBAL slow_query_log = 'ON';
     SET GLOBAL long_query_time = 1;
     ```

2. **Use Explain Plans:**
   ```sql
   -- PostgreSQL
   EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

   -- MySQL
   EXPLAIN FORMAT=JSON SELECT * FROM users WHERE email = 'test@example.com';
   ```
   - Look for `Seq Scan` (full table scans) or `Full Table Scan`—these indicate missing indexes.

3. **Monitor Locks and Transactions:**
   ```sql
   -- PostgreSQL: Active locks
   SELECT * FROM pg_locks;

   -- MySQL: Long-running transactions
   SHOW PROCESSLIST;
   ```

4. **Capture Replication Lag (for Replicated DBs):**
   ```sql
   -- MySQL: Replication status
   SHOW SLAVE STATUS\G;
   ```

---

## **4. Prevention Strategies**

### **4.1 Coding Best Practices**
- **Use Prepared Statements** to avoid SQL injection and improve performance:
  ```python
  # Bad (vulnerable to SQLi)
  cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")

  # Good
  cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
  ```

- **Follow the "One Query per Request" Rule** where possible to reduce connection overhead.

- **Implement Retry Logic for Transient Errors:**
  ```python
  from tenacity import retry, stop_after_attempt

  @retry(stop=stop_after_attempt(3))
  def fetch_user(user_id):
      try:
          return db.fetchone(f"SELECT * FROM users WHERE id = {user_id}")
      except psycopg2.OperationalError:
          raise
  ```

### **4.2 Database Configuration**
- **Set Reasonable Timeouts:**
  ```ini
  # PostgreSQL: Increase statement_timeout
  statement_timeout = '10s'
  ```

- **Enable Maintenance Windows:**
  - Schedule `VACUUM` (PostgreSQL) or `OPTIMIZE TABLE` (MySQL) during off-peak hours.

- **Use Read Replicas for Scaling:**
  - Offload read queries to replicas to reduce master load.

### **4.3 Observability**
- **Monitor Key Metrics:**
  - Connection pool usage.
  - Query latency (P99, P95 percentiles).
  - Disk I/O, CPU, and memory usage.

- **Set Up Alerts:**
  - Alert on `Slow Query Log` growth.
  - Alert on `Connection refused` errors.

- **Regular Backups:**
  - Test restore procedures quarterly.
  - Use tools like **WAL-G (PostgreSQL)** or **Percona XtraBackup (MySQL)**.

---

## **5. Step-by-Step Troubleshooting Workflow**
1. **Reproduce the Issue:** Isolate the problem (e.g., "Slows down only after 5 PM").
2. **Check Logs:** Review database and application logs for clues.
3. **Run Diagnostics:** Use `EXPLAIN`, `SHOW STATUS`, or `pg_stat_statements`.
4. **Apply Fix:** Patch the issue (index, query, config change).
5. **Validate:** Test the fix in a staging environment before production.
6. **Monitor:** Ensure the fix resolves the issue without introducing new problems.

---

## **Final Notes**
- **Start Simple:** Rule out obvious issues (e.g., disk space, misconfigured pools) before diving deep.
- **Leverage Community Tools:** Many databases have official tools (e.g., MySQL’s `pt-query-digest`).
- **Automate Alerts:** Use tools like **Prometheus + Grafana** or **Datadog** to catch issues early.

By following this guide, you’ll quickly diagnose and resolve most database-related issues while preventing future problems.