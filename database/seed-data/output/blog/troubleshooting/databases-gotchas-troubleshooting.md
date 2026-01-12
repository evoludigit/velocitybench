# **Debugging Databases Gotchas: A Troubleshooting Guide**

## **Introduction**
Databases are the backbone of most modern applications, but they are also a frequent source of subtle bugs, performance issues, and unexpected failures. This guide focuses on **common "gotchas"**—pitfalls that even experienced engineers often overlook—when working with databases. We’ll cover symptoms, fixes, debugging tools, and prevention strategies to help you resolve issues quickly and efficiently.

---

## **Symptom Checklist**
Before diving into debugging, check if your issue aligns with these common database symptoms:

### **Performance-Related Issues**
- [ ] Slow queries (response times > 500ms, random spikes)
- [ ] Database server overload (high CPU, memory, or disk I/O)
- [ ] Connection timeouts or "server busy" errors
- [ ] Large transactions causing locks or timeouts

### **Data Integrity & Consistency Issues**
- [ ] Inconsistent reads (dirty reads, phantom reads, or stale data)
- [ ] Failed transactions or partial updates
- [ ] Missing or duplicated records
- [ ] Index corruption or table fragmentation

### **Connection & Reliability Issues**
- [ ] "Connection refused" errors (network issues, misconfigured credentials)
- [ ] "Too many connections" errors (connection pooling misconfigurations)
- [ ] Session timeouts or lost transactions
- [ ] Database server crashes or unexpected restarts

### **Query & Schema Issues**
- [ ] SQL syntax errors (unclosed brackets, typo in column names)
- [ ] Schema migrations failing (missing dependencies, rollback issues)
- [ ] Missing constraints (missing `FOREIGN KEY`, `UNIQUE`, or `NOT NULL` checks)
- [ ] Improper indexing leading to full table scans

### **Replication & High Availability Issues**
- [ ] Master-slave replication lag or synchronization failures
- [ ] Failed failover or automatic recovery
- [ ] Data inconsistencies across replicas

If your issue aligns with multiple boxes, prioritize **performance and reliability** before diving into complex fixes.

---

## **Common Issues and Fixes (with Code Examples)**

### **1. Slow Queries (Full Table Scans)**
**Symptom:**
Queries taking much longer than expected, even with proper indexing.

**Root Cause:**
- Missing or inefficient indexes.
- Lack of query optimization (e.g., `SELECT *` instead of specific columns).
- High-cardinality columns being used in `WHERE` clauses without indexing.

**Fix:**
#### **A. Check Index Usage**
```sql
-- PostgreSQL: Check which queries benefit from indexes
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- MySQL: Show slow queries
SHOW GLOBAL STATUS LIKE 'Slow_queries';
```

#### **B. Add Missing Indexes**
```sql
-- PostgreSQL / MySQL: Add a composite index for frequent queries
CREATE INDEX idx_users_email_name ON users (email, name);
```

#### **C. Optimize Queries**
```sql
-- Bad: Fetching all columns
SELECT * FROM orders;

-- Good: Fetch only needed columns
SELECT order_id, customer_id, amount FROM orders;
```

#### **D. Partition Large Tables**
```sql
-- MySQL: Partition by date range
ALTER TABLE logs PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025)
);
```

---

### **2. Connection Pooling Issues**
**Symptom:**
"Connection refused" or "too many connections" errors, even with idle connections.

**Root Cause:**
- Pool size too small for concurrent requests.
- Connections not being properly closed (leak).
- Connection timeout misconfigurations.

**Fix:**
#### **A. Configure Connection Pool Properly**
**Node.js (PgPool):**
```javascript
const { Pool } = require('pg');
const pool = new Pool({
  max: 20,       // Max connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

**Python (SQLAlchemy):**
```python
from sqlalchemy import create_engine
engine = create_engine(
    "postgresql://user:pass@localhost/db",
    pool_size=10,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=3600
)
```

#### **B. Ensure Proper Connection Closing**
```javascript
// Always close connections in Node.js
const client = await pool.connect();
try {
  await client.query('SELECT * FROM users');
} finally {
  client.release(); // Critical: Release back to pool
}
```

#### **C. Monitor Connection Usage**
**PostgreSQL:**
```sql
SELECT usename, numbackends FROM pg_stat_activity;
-- Kill stale connections if needed
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE usename = 'bad_user';
```

---

### **3. Transaction Isolations Gotchas**
**Symptom:**
Dirty reads, phantom reads, or deadlocks.

**Root Cause:**
- Incorrect transaction isolation level (e.g., `READ COMMITTED` instead of `REPEATABLE READ`).
- Long-running transactions causing locks.
- No retry logic for deadlocks.

**Fix:**
#### **A. Set Appropriate Isolation Level**
```sql
-- PostgreSQL: Set transaction isolation
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
```

#### **B. Avoid Long Transactions**
```javascript
// Example: Use async transaction with timeout
async function updateUser(userId) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    await client.query('UPDATE users SET balance = balance - 100 WHERE id = $1', [userId]);
    await client.query('COMMIT');
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}
```

#### **C. Handle Deadlocks with Retries**
```python
import psycopg2
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def transfer_funds(from_user, to_user, amount):
    conn = psycopg2.connect("db_uri")
    try:
        conn.autocommit = False
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, from_user))
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, to_user))
        conn.commit()
    except psycopg2.DatabaseError as e:
        conn.rollback()
        raise
    finally:
        conn.close()
```

---

### **4. Schema Migration Failures**
**Symptom:**
Migrations stuck, partial rollbacks, or schema conflicts.

**Root Cause:**
- Missing dependencies between migrations.
- No transaction wrap for schema changes.
- Rollback scripts not written.

**Fix:**
#### **A. Use Atomic Migrations**
```javascript
// Example: Sequelize migration with transaction
module.exports = {
  up: async (queryInterface, Sequelize) => {
    const transaction = await queryInterface.sequelize.transaction();
    try {
      await queryInterface.createTable('users', { ... }, { transaction });
      await transaction.commit();
    } catch (err) {
      await transaction.rollback();
      throw err;
    }
  },
  down: async (queryInterface, Sequelize) => {
    await queryInterface.dropTable('users');
  }
};
```

#### **B. Add Migration Dependencies**
```bash
# Example: Ensure table 'logs' exists before 'audit_logs'
npx sequelize-cli migration:generate --name "Add-audit-logs-table"
# Then manually edit the migration to check for 'logs' first
```

#### **C. Test Migrations in Staging**
```bash
# Run migrations dry-run first
npm run migrations:test
```

---

### **5. Replication Lag & Data Sync Issues**
**Symptom:**
Slave database is falling behind, or data inconsistencies.

**Root Cause:**
- Replication filter missing (only syncing certain tables).
- Binary log (`binlog`) not configured properly.
- Network issues between master and slave.

**Fix:**
#### **A. Configure Proper Replication Filter**
**MySQL:**
```sql
-- Master: Enable binary logging
SET GLOBAL binlog_format = 'ROW';
SET GLOBAL log_bin = 'mysql-bin';
SET GLOBAL sync_binlog = 1;

-- Slave: Replicate only specific tables
CHANGE MASTER TO
  MASTER_AUTO_POSITION = 1,
  MASTER_CONNECT_RETRY = 10,
  IGNORE_SERVER_IDS = 1;
```

#### **B. Monitor Replication Status**
```sql
-- MySQL: Check replication lag
SHOW SLAVE STATUS\G
-- If 'Seconds_Behind_Master' > 0, investigate
```

#### **C. Increase Replication Buffer Size**
```ini
# MySQL config (my.cnf)
[mysqld]
binlog_group_commit_sync_delay = 0
binlog_group_commit_sync_no_delay_count = 3
```

---

## **Debugging Tools and Techniques**

### **1. Database-Specific Tools**
| Database  | Tool | Purpose |
|-----------|------|---------|
| **PostgreSQL** | `pgBadger`, `pg_stat_statements` | Log analysis, slow query detection |
| **MySQL** | `pt-query-digest`, `SHOW PROFILE` | Query profiling, replication checks |
| **MongoDB** | `mongostat`, `db.currentOp()` | Performance monitoring, blocking operations |

### **2. Logging & Slow Query Logging**
```sql
-- Enable slow query logging (PostgreSQL)
ALTER SYSTEM SET log_min_duration_statement = '100ms';
ALTER SYSTEM SET log_statement = 'all';

-- MySQL: Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;
```

### **3. Profiler-Based Debugging**
```javascript
// Node.js: Use `pg-profiler` to log slow queries
const profiler = require('pg-profiler')({
  captureSlowQueries: true,
  slowThreshold: 500
});

const pool = new Pool({ connectionString: 'postgres://...' }, profiler);
```

### **4. Network & Connection Debugging**
- **Check connection strings** for typos (e.g., `localhost` vs `127.0.0.1`).
- **Use packet sniffers** (Wireshark, tcpdump) to verify network traffic.
- **Test connectivity** with `telnet` or `nc`:
  ```bash
  telnet localhost 5432  # PostgreSQL default port
  ```

### **5. Replication Debugging**
- **Check GTID vs Binary Log Position** for MySQL:
  ```sql
  SHOW MASTER STATUS;
  SHOW SLAVE STATUS;
  ```
- **Compare checksums** between master and slave for data consistency:
  ```sql
  -- MySQL: Compare checksums of critical tables
  SELECT COUNT(*) FROM master_table;
  SELECT COUNT(*) FROM slave_table;
  ```

---

## **Prevention Strategies**

### **1. Database Design Best Practices**
✅ **Normalize where necessary, denormalize for performance.**
✅ **Use appropriate data types** (e.g., `BOOLEAN` instead of `TINYINT`).
✅ **Avoid `SELECT *`**—fetch only required columns.

### **2. Query Optimization**
✅ **Explain queries** (`EXPLAIN ANALYZE`) before production.
✅ **Add indexes strategically** (not every column, but frequently queried ones).
✅ **Use query caching** (e.g., Redis for read-heavy workloads).

### **3. Connection Management**
✅ **Use connection pooling** (avoid `new Connection` per request).
✅ **Set reasonable timeouts** (avoid hanging connections).
✅ **Monitor connection leaks** (tools like `pgwatch2` for PostgreSQL).

### **4. Transaction Management**
✅ **Keep transactions short** (avoid long-running `BEGIN` blocks).
✅ **Set appropriate isolation levels** (e.g., `REPEATABLE READ` for most cases).
✅ **Implement retry logic for deadlocks**.

### **5. Migration Safety**
✅ **Test migrations in staging** before production.
✅ **Use version control for migrations** (Git).
✅ **Write rollback scripts** for every migration.

### **6. Monitoring & Alerts**
✅ **Set up alerts for:**
   - High query latency (`p99 > 500ms`).
   - Connection errors (`connection refused`).
   - Replication lag (`Seconds_Behind_Master > 60`).
✅ **Use tools like:**
   - **Prometheus + Grafana** (metrics).
   - **Datadog / New Relic** (APM + DB monitoring).
   - **Sentry** (error tracking for DB issues).

---

## **Final Checklist for Quick Resolution**
| Step | Action |
|------|--------|
| 1 | **Check logs** (`journalctl`, application logs, DB logs). |
| 2 | **Isolate the issue** (is it a query, connection, or app bug?). |
| 3 | **Reproduce in staging** (avoid guessing in production). |
| 4 | **Use `EXPLAIN`** to analyze slow queries. |
| 5 | **Review recent changes** (new migrations, code deployments). |
| 6 | **Test fixes in staging** before applying to production. |
| 7 | **Monitor post-fix** (ensure the issue doesn’t reoccur). |

---
## **Conclusion**
Database gotchas are inevitable, but with the right debugging tools, strategies, and preventive measures, you can **minimize downtime and resolve issues quickly**. Always:
- **Log everything** (queries, connections, transactions).
- **Use profiling** to catch performance bottlenecks early.
- **Test migrations and schema changes** before production.
- **Monitor replication and connection health** proactively.

By following this guide, you’ll be better equipped to **diagnose and fix database issues efficiently**, keeping your applications running smoothly. 🚀