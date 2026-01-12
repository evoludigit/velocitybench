# **Debugging Database Techniques: A Troubleshooting Guide**
*A Practical Guide for Backend Engineers*

---

## **1. Introduction**
Databases are the backbone of most applications, yet they can introduce subtle bugs, performance bottlenecks, or unexpected failures. This guide covers common database-related issues—from connection problems to slow queries—and provides actionable fixes.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these symptoms:

| **Symptom**                          | **Possible Cause**                          | **Immediate Check** |
|--------------------------------------|--------------------------------------------|----------------------|
| **Connection failures**              | Invalid credentials, network issues, or exhausted pools | Check `db_connection` logs, test connectivity manually |
| **Slow queries**                     | Missing indexes, inefficient SQL, or high load | Run `EXPLAIN` (PostgreSQL), slow query logs (MySQL) |
| **Deadlocks/locking issues**         | Long-running transactions, improper isolation levels | Check `pg_locks` (PostgreSQL), `SHOW ENGINE INNODB STATUS` (MySQL) |
| **Data integrity issues** (corruption, duplicates) | Missing constraints, improper transactions | Verify `ON CONSTRAINT FAIL` behavior, transaction logs |
| **High disk I/O or memory usage**    | Unoptimized queries, lack of caching | Monitor with `pg_stat_activity`, `SHOW PROCESSLIST` |
| **Application crashes on DB calls**  | ORM/DB driver timeouts, improper error handling | Check connection timeouts, retry logic |
| **Replication lag**                  | Slow master, high write load, network issues | Monitor `Show Slave Status` (MySQL), `pg_stat_replication` |

---

## **3. Common Issues and Fixes**

### **A. Connection Failures**
**Symptom:** Application crashes with "Connection refused" or "Timeout" errors.
**Root Cause:**
- Invalid credentials or incorrect connection string.
- Database server down or network issues.
- Connection pool exhausted (e.g., too many open connections).

#### **Fixes:**
1. **Validate Connection String**
   ```bash
   # Test connection manually (PostgreSQL example)
   psql -h localhost -p 5432 -U user -d dbname
   ```
   Fix credentials or network settings in `.env` or config.

2. **Check Connection Pooling**
   ```javascript
   // Example: Node.js with PostgreSQL
   const { Pool } = require('pg');
   const pool = new Pool({
     max: 20, // Adjust based on app needs
     idleTimeoutMillis: 30000,
     connectionTimeoutMillis: 2000,
   });
   ```
   - **Key settings:**
     - `max`: Number of concurrent connections.
     - `idleTimeoutMillis`: Close idle connections after X ms.
     - `connectionTimeoutMillis`: Fail fast if DB is unresponsive.

3. **Enable Connection Retry Logic**
   ```python
   # Python (SQLAlchemy example)
   from sqlalchemy import exc
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def get_db_connection():
       try:
           return engine.connect()
       except exc.OperationalError as e:
           raise e  # Retry will handle it
   ```

---

### **B. Slow Queries**
**Symptom:** Applications freeze or respond slowly (>1s for queries).
**Root Cause:**
- Missing indexes on `WHERE`, `JOIN`, or `ORDER BY` clauses.
- N+1 query problem (e.g., fetching related records inefficiently).
- Large result sets or unoptimized `SELECT *`.

#### **Fixes:**
1. **Identify Bottlenecks**
   ```sql
   -- PostgreSQL: Find slow queries
   SELECT query, rows, shared_blks_hit, shared_blks_read
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;

   -- MySQL: Enable slow query log
   SET GLOBAL slow_query_log = 'ON';
   ```
   - **Fix:** Add indexes or rewrite queries.
   ```sql
   -- Example: Add index for a slow WHERE clause
   CREATE INDEX idx_user_email ON users(email);
   ```

2. **Optimize Joins**
   ```sql
   -- Bad: Full table scan
   SELECT * FROM orders JOIN users ON orders.user_id = users.id
   WHERE users.email LIKE '%@example.com';

   -- Good: Index hints + LIMIT
   SELECT o.*, u.id, u.email
   FROM orders o
   INNER JOIN users u ON o.user_id = u.id
   WHERE u.email LIKE '%@example.com'
   ORDER BY o.created_at DESC
   LIMIT 100;
   ```

3. **Use Caching (Redis, Query Cache)**
   ```javascript
   // Node.js + Redis example
   const { createClient } = require('redis');
   const redisClient = createClient();

   async function getCachedUser(id) {
     const cached = await redisClient.get(`user:${id}`);
     if (cached) return JSON.parse(cached);

     const user = await db.query('SELECT * FROM users WHERE id = $1', [id]);
     await redisClient.set(`user:${id}`, JSON.stringify(user), 'EX', 3600);
     return user;
   }
   ```

---

### **C. Deadlocks & Locking Issues**
**Symptom:** Transactions fail with "deadlock detected" or "lock timeout".
**Root Cause:**
- Long-running transactions holding locks.
- Improper transaction isolation (e.g., `REPEATABLE READ` conflicts).
- High contention on certain tables.

#### **Fixes:**
1. **Analyze Deadlocks**
   ```sql
   -- PostgreSQL: Check active locks
   SELECT * FROM pg_locks WHERE NOT locktype = 'transactionid';
   ```
   - **Solution:** Break up large transactions or use `SELECT FOR UPDATE SKIP LOCKED`.

2. **Use `FOR UPDATE` Wisely**
   ```sql
   -- Lock a row temporarily (PostgreSQL)
   BEGIN;
   SELECT * FROM accounts WHERE id = 1 FOR UPDATE;
   -- Update logic here
   COMMIT;
   ```

3. **Optimize Isolation Levels**
   ```sql
   -- MySQL: Use READ COMMITTED (default) instead of REPEATABLE READ
   SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
   ```

---

### **D. Data Integrity Issues**
**Symptom:** Duplicates, null values, or orphaned records.
**Root Cause:**
- Missing `UNIQUE` constraints.
- Manual `INSERT` bypassing validations.
- Transaction rollbacks not handled properly.

#### **Fixes:**
1. **Enforce Constraints**
   ```sql
   -- Add UNIQUE constraint
   ALTER TABLE users ADD CONSTRAINT unique_email UNIQUE (email);
   ```

2. **Use Transactions for Critical Operations**
   ```python
   # Python (SQLAlchemy)
   session = db.Session()
   try:
       session.begin()  # Start transaction
       user = session.query(User).filter_by(email="test@example.com").first()
       if not user:
           user = User(email="test@example.com")
           session.add(user)
       session.commit()  # Commit on success
   except:
       session.rollback()  # Rollback on error
   finally:
       session.close()
   ```

3. **Audit Changes with Triggers**
   ```sql
   -- PostgreSQL: Log all changes to a table
   CREATE TABLE audit_log (
       id SERIAL PRIMARY KEY,
       table_name VARCHAR(50),
       action VARCHAR(10),  -- 'INSERT', 'UPDATE', 'DELETE'
       data JSONB,
       timestamp TIMESTAMP DEFAULT NOW()
   );

   CREATE OR REPLACE FUNCTION log_changes()
   RETURNS TRIGGER AS $$
   BEGIN
       INSERT INTO audit_log (table_name, action, data)
       VALUES (TG_TABLE_NAME, TG_OP, to_jsonb(NEW));
       RETURN NEW;
   END;
   $$ LANGUAGE plpgsql;

   CREATE TRIGGER trigger_audit
   AFTER INSERT OR UPDATE OR DELETE ON users
   FOR EACH ROW EXECUTE FUNCTION log_changes();
   ```

---

### **E. Replication Lag**
**Symptom:** Read replicas are hours behind the master.
**Root Cause:**
- High write load on master.
- Slow replication network.
- Binary log (`binlog`) not configured properly.

#### **Fixes:**
1. **Monitor Replication Status**
   ```sql
   -- MySQL: Check slave status
   SHOW SLAVE STATUS;

   -- PostgreSQL: Check replication lag
   SELECT * FROM pg_stat_replication;
   ```

2. **Optimize Replication**
   - **Binlog Grouping (MySQL):**
     ```sql
     [mysqld]
     binlog_group_commit_sync_delay = 0.01
     binloggroup_commit_sync_no_delay_count = 5
     ```
   - **Streaming Replication (PostgreSQL):**
     ```sql
     SELECT pg_is_in_recovery();  -- Check if replica is syncing
     ```

3. **Scale Reads with Read Replicas**
   ```python
   # Python: Route reads to replicas
   def get_connection():
       if db_role == 'write':
           return write_db_engine.connect()
       else:
           return read_db_engines[0].connect()  # Round-robin logic
   ```

---

## **4. Debugging Tools and Techniques**

### **A. Query Profiling**
- **PostgreSQL:** `EXPLAIN ANALYZE` to see execution plans.
  ```sql
  EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 1;
  ```
- **MySQL:** Use `EXPLAIN` and slow query logs.
  ```sql
  EXPLAIN FORMAT=JSON SELECT * FROM users WHERE email = 'test@example.com';
  ```

### **B. Database-Specific Tools**
| **Database** | **Tool**                     | **Use Case**                          |
|--------------|------------------------------|---------------------------------------|
| PostgreSQL   | `pgBadger`                   | Analyze log files for slow queries.   |
| MySQL        | `pt-stalk` (Percona)         | Diagnose replication issues.         |
| MongoDB      | `mongostat`, `db.currentOp()` | Monitor live operations.              |

### **C. Transaction Debugging**
- **Log Transactions:**
  ```sql
  -- PostgreSQL: Enable transaction logs
  ALTER SYSTEM SET log_statement = 'all';
  ```
- **Use `pg_dump` for Recovery:**
  ```bash
  pg_dump -U user -Fc dbname > backup.dump  # Full backup
  pg_restore -U user -d dbname backup.dump # Restore
  ```

### **D. Connection Pool Debugging**
- **Check Pool Stats:**
  ```javascript
  // Node.js: Check connection pool status
  pool.on('error', (err) => console.error('Pool error:', err));
  console.log('Active connections:', pool.totalCount);
  ```

---

## **5. Prevention Strategies**

### **A. Database Design Best Practices**
1. **Schema Optimization:**
   - Normalize tables to reduce redundancy.
   - Denormalize for read-heavy workloads (if acceptable).

2. **Indexing Strategy:**
   - Index `PRIMARY KEY`, `UNIQUE`, and frequently queried columns.
   - Avoid over-indexing (hurts writes).

3. **Partitioning:**
   ```sql
   -- MySQL: Partition by date
   CREATE TABLE orders (
       id INT PRIMARY KEY,
       order_date DATE
   ) PARTITION BY RANGE (YEAR(order_date)) (
       PARTITION p2023 VALUES LESS THAN (2024),
       PARTITION p2024 VALUES LESS THAN (2025)
   );
   ```

### **B. Query Optimization**
- **Use ORMs Judiciously:**
  - Avoid `SELECT *`; fetch only needed columns.
  ```python
  # Bad: Fetches all columns
  User.query.filter_by(email="test@example.com").first()

  # Good: Explicit columns
  User.query.with_entities(User.id, User.email).filter_by(email="test@example.com").first()
  ```

- **Batch Operations:**
  ```python
  # Bulk INSERT (PostgreSQL)
  from sqlalchemy import text
  db.execute(text("INSERT INTO users (email) VALUES (:email)"), [{"email": "test1@example.com"}, {"email": "test2@example.com"}])
  ```

### **C. Monitoring and Alerts**
- **Set Up Alerts:**
  - **PostgreSQL:** `pg_stat_activity` + Prometheus/Grafana.
  - **MySQL:** `PERFORMANCE_SCHEMA` + Datadog.

  Example alert (Prometheus):
  ```yaml
  - alert: HighDatabaseLatency
    expr: avg(rate(pg_stat_activity_count{state="active"}[5m])) > 1000
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High DB load detected"
  ```

- **Regular Maintenance:**
  - Vacuum (PostgreSQL) / Optimize (MySQL) tables weekly.
  - Update database and drivers.

### **D. Backup and Disaster Recovery**
1. **Automated Backups:**
   ```bash
   # PostgreSQL: Automated daily backups
   pg_dump -U user -Fd -f /backups/db_$(date +\%Y\%m\%d).dump dbname
   ```
2. **Test Restores:**
   - Schedule quarterly restore drills.

3. **Use Replication for HA:**
   - Set up read replicas + failover (e.g., Patroni for PostgreSQL).

---

## **6. Quick Reference Cheat Sheet**
| **Issue**               | **Immediate Fix**                          | **Long-Term Solution**                  |
|-------------------------|--------------------------------------------|-----------------------------------------|
| Connection errors       | Check credentials, retry logic.            | Use connection pooling.                 |
| Slow queries            | Run `EXPLAIN`, add indexes.                | Implement caching (Redis).               |
| Deadlocks               | Restart stalled sessions.                  | Shorten transactions, use `SKIP LOCKED`.|
| Data corruption         | Restore from backup.                       | Add triggers, enforce constraints.      |
| Replication lag         | Scale master, check network.               | Use binlog grouping, async replication. |

---

## **7. When to Escalate**
- **Database downtime** (even for reads).
- **Data corruption** (risk of loss).
- **Unresolvable deadlocks** (manual intervention needed).
- **Performance degradation** affecting SLAs.

**Next Steps:**
1. Check logs (`/var/log/postgresql/postgresql-*.log` for PostgreSQL).
2. Engage DBA or cloud provider support (AWS RDS, GCP Cloud SQL).
3. Consider upgrading the database version if it’s unsupported.

---
**Final Note:** Database debugging is 80% about **profiling** and 20% about fixing. Always start with `EXPLAIN`, logs, and monitoring before diving into code changes.