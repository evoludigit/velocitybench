# **Debugging Database Maintenance: A Troubleshooting Guide**

## **Introduction**
Maintaining databases is critical for system reliability, performance, and data integrity. When database-related issues arise, they can manifest as slow queries, crashes, corruption, or inconsistent data. This guide provides a structured approach to diagnosing and resolving common database maintenance problems efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, verify which symptoms are present:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------|
| Slow query performance               | Queries taking abnormally long to execute (seconds vs. milliseconds).         |
| Database crashes or timeouts         | Application or DB server crashes, connection pools exhausted.                   |
| Corrupted data or inconsistent reads | Inconsistent results, NULL values where expected, or schema integrity violations. |
| High disk I/O or CPU usage          | Database server overloaded, slow disk operations, or high CPU spikes.           |
| Failed backups or maintenance tasks  | Backup jobs hanging, `VACUUM`/`OPTIMIZE` failing, or `ALTER TABLE` hangs.       |
| Connection pool exhaustion          | Applications unable to connect to the database ("Too many connections").         |
| Log errors (e.g., PostgreSQL, MySQL) | Repeated errors in `postgresql.log`, `mysqld.log`, or cloud DB console logs. |

---

## **2. Common Issues and Fixes (with Code)**

### **2.1 Slow Query Performance**
**Symptoms:**
- Queries degrade over time.
- `EXPLAIN` shows full table scans (`Seq Scan`, `Full Table Scan`).

**Root Causes:**
- Missing indexes.
- Poorly optimized queries (e.g., `SELECT *`).
- Table bloat (unreclaimed space due to frequent `INSERT/DELETE`).

**Debugging Steps:**
1. **Check for Missing Indexes**
   ```sql
   -- PostgreSQL: Find queries with high sequential reads
   SELECT query, exec_count, calls, total_time, share
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   ```
   - If a query lacks an index, add one:
     ```sql
     CREATE INDEX idx_user_email ON users(email);
     ```

2. **Analyze Query Execution Plans**
   ```sql
   -- PostgreSQL
   EXPLAIN ANALYZE SELECT * FROM large_table WHERE id = 1;
   ```
   - Look for `Seq Scan` (bad) vs. `Index Scan` (good).

3. **Defragment Tables (Vacuum/AutoVacuum Issues)**
   ```sql
   -- PostgreSQL: Manually vacuum a table
   VACUUM (ANALYZE) large_table;
   ```
   - If `AUTO_VACUUM` is slow, adjust settings:
     ```sql
     ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.1; -- Tune for frequency
     ```

---

### **2.2 Database Crashes or Timeouts**
**Symptoms:**
- DB server crashes unexpectedly.
- Applications hang on `SELECT`/`INSERT` operations.

**Root Causes:**
- Disk full (`Out of Disk Space`).
- Lock contention (long-running transactions).
- Connection leaks (unclosed connections).

**Debugging Steps:**
1. **Check Disk Space**
   ```bash
   df -h  # Linux/macOS
   ```
   - Free up space or resize the DB volume.

2. **Inspect Locks (PostgreSQL)**
   ```sql
   SELECT * FROM pg_locks WHERE relation::regclass = 'users';
   ```
   - Kill blocking transactions:
     ```sql
     SELECT pg_terminate_backend(pid);
     ```

3. **Connection Leak Detection**
   ```bash
   # PostgreSQL: Check active connections
   psql -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle in transaction';"
   ```
   - Fix connection leaks in application code (close connections explicitly).

---

### **2.3 Corrupted Data or Inconsistent Reads**
**Symptoms:**
- NULLs in non-nullable columns.
- Schema mismatches between DB and application.

**Root Causes:**
- Transaction rollbacks without cleanup.
- Schema migrations failing mid-execution.

**Debugging Steps:**
1. **Check for Orphaned Data**
   ```sql
   -- Find rows with NULL in a NOT NULL column
   SELECT * FROM users WHERE name IS NULL;
   ```

2. **Verify Schema Consistency**
   ```bash
   # Compare DB schema with migration files (e.g., Flyway/DbMigrate)
   psql -U postgres -c "\d users"  # PostgreSQL
   ```
   - Re-run migrations if needed:
     ```bash
     flyway migrate  # Flyway CLI
     ```

---

### **2.4 High Disk I/O & CPU Usage**
**Symptoms:**
- DB server CPU throttled (fan noise).
- Slow disk operations (`/var/lib/postgresql` full I/O).

**Root Causes:**
- Missing indexes (full scans).
- Large transactions (WAL growth).

**Debugging Steps:**
1. **Check PostgreSQL WAL Logs**
   ```bash
   ls -lh /var/lib/postgresql/14/main/pg_wal/
   ```
   - Truncate WAL archives (if using `archive_mode`):
     ```bash
     pg_archivecleanup -d /var/lib/postgresql/14/main
     ```

2. **Optimize WAL Settings**
   ```sql
   ALTER SYSTEM SET wal_level = minimal; -- If not using replication
   ```

---

### **2.5 Failed Backups**
**Symptoms:**
- Backup jobs timeout.
- Incomplete `.dump` files.

**Root Causes:**
- Disk I/O bottlenecks.
- Large tables without compression.

**Debugging Steps:**
1. **Test Backup with Smaller Tables**
   ```bash
   pg_dump -U postgres -t small_table db_name > backup.sql
   ```
2. **Compress Backups**
   ```bash
   pg_dump db_name | gzip > backup.sql.gz
   ```

---

## **3. Debugging Tools and Techniques**

| **Tool**               | **Usage**                                                                 |
|------------------------|----------------------------------------------------------------------------|
| **`pg_stat_statements`** | Track slow queries (PostgreSQL).                                         |
| **`EXPLAIN`**          | Analyze query execution plans.                                            |
| **`pgBadger`**         | Log analysis for PostgreSQL.                                               |
| **`pt-query-digest`**  | Query performance analysis (MySQL).                                       |
| **`dd`/`iostat`**      | Check disk I/O bottlenecks.                                              |
| **Cloud DB Metrics**   | AWS RDS, Google Cloud SQL, Azure DB logs.                                  |

**Example: Using `pgBadger` (PostgreSQL)**
```bash
pgbadger /var/log/postgresql/postgresql-14-main.log -o report.html
```

---

## **4. Prevention Strategies**

### **4.1 Regular Maintenance**
- **Vacuum/AutoVacuum Tuning**
  ```sql
  -- PostgreSQL: Adjust for high write workloads
  ALTER SYSTEM SET autovacuum_vacuum_scale_factor = 0.2;
  ```
- **Monitor Table Bloat**
  ```sql
  SELECT n_live_tup, n_dead_tup, n_live_tup - n_dead_tup AS usable_space
  FROM pg_stat_all_tables WHERE relname = 'large_table';
  ```

### **4.2 Schema Management**
- Use **schema migrations** (Flyway, Liquibase) to avoid manual SQL errors.
- **Avoid `SELECT *`** (fetch only needed columns).

### **4.3 Connection Pooling**
- Configure **PgBouncer** or **ProxySQL** to manage connections.
- Set **connection timeouts** in the app:
  ```python
  # SQLAlchemy (Python) example
  engine = create_engine("postgresql://user:pass@host/db", pool_pre_ping=True)
  ```

### **4.4 Logging & Alerts**
- Set up **database alerts** (Prometheus + Alertmanager).
- Log slow queries:
  ```sql
  -- Enable in postgresql.conf
  shared_preload_libraries = 'pg_stat_statements'
  ```

---

## **5. Conclusion**
Database maintenance issues often stem from **poor indexing, lack of monitoring, or misconfigured settings**. By following this guide:
1. **Check symptoms** (slow queries, crashes, corruption).
2. **Use tools** (`EXPLAIN`, `pgBadger`, `iostat`).
3. **Apply fixes** (indexes, `VACUUM`, connection tuning).
4. **Prevent future issues** (migrations, pooling, alerts).

For critical systems, **automate backups and monitoring** to catch problems early. If issues persist, consult vendor documentation (PostgreSQL docs, MySQL docs) or open an issue in the relevant GitHub repo.

---
**Next Steps:**
- Revisit this guide when database issues arise.
- Integrate monitoring into CI/CD pipelines.
- Document known issues and fixes in a team wiki.