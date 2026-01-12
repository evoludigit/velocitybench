# **Debugging Database Issues: A Troubleshooting Guide**

Debugging database-related issues is one of the most critical yet challenging tasks in backend engineering. Whether dealing with slow queries, connection failures, schema inconsistencies, or corrupted data, a systematic approach ensures swift resolution and prevents recurring problems.

This guide provides a **focused, actionable** approach to diagnosing and fixing common database issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, identify the root cause by evaluating these symptoms:

| **Symptom**                     | **Description**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------|
| **Slow Queries**                 | Long-running queries causing timeouts or degraded performance.                                     |
| **Connection Failures**          | Apps unable to connect to the database (timeout, `ConnectionRefused`, `AuthenticationFailed`).     |
| **Data Consistency Issues**      | Inconsistent reads/writes, stale data, or race conditions.                                        |
| **Storage Full or Space Issues** | Database running out of disk space, leading to crashes or errors like `DiskFull` or `OutOfSpace`. |
| **Locking & Deadlocks**          | Transactions stuck due to locks, resulting in `LockTimeout` or deadlock errors.                   |
| **Corrupted Data**               | Numeric overflow, invalid records, or metadata corruption.                                       |
| **Backup & Recovery Failures**   | Failed backups, point-in-time recovery issues, or corrupted backups.                             |
| **Logging & Auditing Issues**    | Missing logs, audit trail corruption, or permission-related logging failures.                     |

**Next Step:** Before fixing, confirm the symptom by checking:
- **Application logs** (`ERROR`, `WARN`, `INFO` levels).
- **Database logs** (`ERROR_LOG`, slow query logs).
- **Monitoring tools** (Prometheus, DataDog, CloudWatch).
- **Database metrics** (latency, CPU, memory, IOPS).

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Slow Queries**
**Symptoms:**
- `timeout` errors in application.
- High `Slow Query Log` entries.
- Slow response times (>1s for simple queries).

#### **Root Causes:**
- Missing or inefficient indexes.
- N+1 query problems (unoptimized ORMs).
- Large tables with poor partitioning.
- Lack of query caching.

#### **Fixes:**
**A. Identify Slow Queries**
```sql
-- MySQL/MariaDB
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1; -- Log queries >1s

-- PostgreSQL
SET log_min_duration_statement = 1000; -- Log queries >1s
ALTER SYSTEM SET log_min_duration_statement TO 1000;
```

**B. Optimize Queries**
- **Add Indexes** (if missing):
  ```sql
  CREATE INDEX idx_user_email ON users(email);
  ```
- **Use EXPLAIN** to analyze query plans:
  ```sql
  EXPLAIN SELECT * FROM orders WHERE user_id = 123;
  ```
  - Look for `Full Table Scan` → Add missing indexes.
  - High `Seq Scan` cost → Consider GIN/GIST indexes (PostgreSQL).

**C. Fix N+1 Queries (e.g., Django/SQLAlchemy)**
```python
# Bad (N+1 queries)
users = User.objects.all()
for user in users:
    print(user.posts.count())  # One query per user → 100 users → 100 queries

# Good (Join or Prefetch)
users = User.objects.prefetch_related('posts').all()  # Single query
```

**D. Enable Query Caching**
```sql
-- Redis-based caching (PostgreSQL)
SELECT * FROM posts WHERE id = 1;  -- First query (slow)
SELECT * FROM posts WHERE id = 1;  -- Second query (fast, from cache)
```

---

### **Issue 2: Database Connection Failures**
**Symptoms:**
- `ConnectionRefused` (DB not running).
- `AuthenticationFailed` (wrong credentials).
- `TimeoutError` (connection pool exhausted).

#### **Root Causes:**
- DB server down or misconfigured.
- Incorrect credentials in config.
- Connection pool exhausted (too many concurrent connections).
- Network issues (firewall blocking ports).

#### **Fixes:**
**A. Verify DB Server Status**
```bash
# Check PostgreSQL
sudo systemctl status postgresql

# Check MySQL
sudo systemctl status mysql
```

**B. Check Connection Pooling (Node.js/Pool Example)**
```javascript
// Node.js (pg library)
const { Pool } = require('pg');
const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'mydb',
  max: 20, // Adjust based on app load
  idleTimeoutMillis: 30000,
});
```

**C. Validate Credentials**
- Check `.env` or config files for typos.
- Verify user permissions:
  ```sql
  -- MySQL
  SHOW GRANTS FOR 'app_user'@'localhost';
  ```

**D. Increase Connection Limits (PostgreSQL)**
```sql
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '1GB';
```

---

### **Issue 3: Data Consistency Issues**
**Symptoms:**
- Duplicate entries.
- Race conditions (e.g., double bookings).
- Inconsistent state after crashes.

#### **Root Causes:**
- Lack of transactions.
- Missing `UNIQUE` constraints.
- Improper locking.
- Eventual consistency bugs.

#### **Fixes:**
**A. Enforce Transactions**
```sql
-- PostgreSQL (BEGIN/COMMIT)
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

**B. Use `UNIQUE` Constraints**
```sql
ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);
```

**C. Implement Locking (PostgreSQL)**
```sql
SELECT pg_advisory_lock(12345);  -- Acquire lock
-- Critical section
SELECT pg_advisory_unlock(12345);
```

**D. Use Optimistic Locking (ORM Approach)**
```python
# Django
from django.db import transaction

@transaction.atomic
def transfer(user1, user2, amount):
    user1.balance -= amount
    user2.balance += amount
    user1.save()
    user2.save()
```

---

### **Issue 4: Storage Full / OutOfSpace Errors**
**Symptoms:**
- `Disk full` errors.
- `OutOfSpace` in logs.
- Slow performance due to disk thrashing.

#### **Root Causes:**
- No auto-vacuum (PostgreSQL).
- Large unused tables.
- Unbounded logs.

#### **Fixes:**
**A. Check Disk Usage**
```bash
# PostgreSQL
SELECT pg_size_pretty(pg_database_size('mydb'));

# MySQL
SHOW TABLE STATUS WHERE Name = 'large_table';
```

**B. Run Vacuum (PostgreSQL)**
```sql
VACUUM FULL ANALYZE;  -- Extreme case (locks table)
```

**C. Archive Old Data**
```sql
-- PostgreSQL (partitioning)
ALTER TABLE logs ADD PARTITION FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
```

**D. Clean Up Logs**
```bash
# PostgreSQL log rotation
sudo truncate -s 0 /var/log/postgresql/postgresql-*.log
```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**          | **Purpose**                                                                 | **Example Usage**                          |
|-----------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **Database Logs**           | Catch low-level errors (corruption, crashes).                             | `tail -f /var/log/mysql/error.log`         |
| **Slow Query Log**          | Identify performance bottlenecks.                                         | `mysqld --slow-query-log-file=/var/log/slow.log` |
| **EXPLAIN & EXPLAIN ANALYZE** | Analyze query execution plans.                                            | `EXPLAIN ANALYZE SELECT * FROM big_table;` |
| **Database Benchmarking**   | Compare performance before/after changes.                                  | `pgbench -c 100 -T 60` (PostgreSQL)        |
| **Connection Pool Monitors** | Track connection leaks/pool exhaustion.                                   | `pgBadger` (PostgreSQL)                    |
| **Replication Lag Checks**  | Verify master-slave sync status.                                           | `SELECT * FROM pg_stat_replication;`       |
| **Lock Table Analyzer**     | Find long-running locks/deadlocks.                                        | `pg_locks` (PostgreSQL)                    |
| **Schema Comparison Tools** | Detect schema drift between environments.                                | `pgAdmin / Sqitch`                         |
| **Health Checks**           | Automated DB readiness probes.                                             | `/healthz` (HTTP endpoint checking DB)     |

**Pro Tip:**
- **Reproduce issues in staging** before fixing in production.
- **Use `strace` for system calls** (Linux):
  ```bash
  strace -f -e trace=open,read,write -p <PID>
  ```

---

## **4. Prevention Strategies**

### **A. Best Practices for Database Design**
1. **Index Wisely**
   - Avoid over-indexing (slows writes).
   - Use composite indexes for common query patterns:
     ```sql
     CREATE INDEX idx_user_name_email ON users (last_name, email);
     ```

2. **Schema Optimization**
   - Normalize where it matters, denormalize for performance.
   - Use `JSONB` (PostgreSQL) for flexible schemas.

3. **Partition Large Tables**
   ```sql
   -- PostgreSQL
   CREATE TABLE sales (
       id SERIAL,
       amount NUMERIC,
       sale_date DATE
   ) PARTITION BY RANGE (sale_date);
   ```

### **B. Monitoring & Alerts**
- **Set up alerts** for:
  - Slow queries (>500ms).
  - High connection pool usage.
  - Disk space < 10%.
- **Tools:**
  - Prometheus + Grafana (metrics).
  - Datadog/New Relic (APM + DB monitoring).

### **C. Backup & Recovery**
1. **Automate Backups**
   ```bash
   # PostgreSQL (pg_dump)
   pg_dump -U postgres mydb > backup.sql
   ```
2. **Test Restores**
   ```bash
   pg_restore -U postgres -d mydb_test < backup.sql
   ```
3. **Use Point-in-Time Recovery (PITR)**
   ```bash
   pg_restore -U postgres -d mydb -T sales -Fc backup.7z
   ```

### **D. Disaster Recovery Plan**
- **RPO (Recovery Point Objective):** How much data loss can you tolerate?
- **RTO (Recovery Time Objective):** How fast must recovery happen?
- **Multi-region replication** (for zero-downtime failover).

### **E. Code-Level Safeguards**
1. **Use ORMs with Caution**
   - Avoid ORM-generated inefficient queries.
   - Use raw SQL for complex operations.
2. **Implement Circuit Breakers**
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def query_db():
       return db.execute("SELECT * FROM users")
   ```
3. **Logging & Tracing**
   - Log all database operations (for auditing).
   - Use distributed tracing (Jaeger, OpenTelemetry).

---

## **5. Quick Resolution Cheat Sheet**

| **Issue**               | **Immediate Fix**                          | **Long-Term Fix**                     |
|-------------------------|--------------------------------------------|---------------------------------------|
| Slow queries            | Kill long-running queries (`pg_terminate_backend`). | Add indexes, optimize queries.        |
| Connection pool exhausted | Increase `max_connections`.               | Fix connection leaks in app.          |
| Data corruption         | Restore from backup.                       | Validate data on writes (checksums).  |
| Deadlocks               | Restart app or kill stuck sessions.        | Optimize transactions, use locks.    |
| Disk full               | Free space manually.                       | Set up auto-cleanup policies.          |
| Authentication errors   | Check credentials/permissions.             | Use IAM roles for DB access.           |

---

## **Final Thoughts**
Debugging databases requires a mix of **log analysis, performance tuning, and defensive coding**. The key is:
1. **Isolate the symptom** (slow queries? locks? corruption?).
2. **Check logs, metrics, and slow query logs**.
3. **Apply fixes incrementally** (avoid big swings in production).
4. **Prevent recurrence** with monitoring, backups, and code patterns.

**Next Steps:**
- Bookmark this guide for quick reference.
- Set up automated database monitoring.
- Train team on common pitfalls (e.g., N+1 queries).

Would you like a deeper dive into any specific area (e.g., PostgreSQL vs. MySQL optimizations)?