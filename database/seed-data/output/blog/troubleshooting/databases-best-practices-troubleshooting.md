---
# **Debugging Database Best Practices: A Troubleshooting Guide**
*For Senior Backend Engineers*

Databases are the backbone of most applications, and ignoring best practices can lead to performance bottlenecks, security vulnerabilities, and operational instability. This guide covers common database issues, their root causes, fixes, debugging techniques, and preventative strategies.

---

## **1. Symptom Checklist**
Before diving into fixes, identify symptoms that indicate database misconfiguration or abuse of best practices:

### **Performance-Related Symptoms**
✅ **Slow Queries**
- High execution time (>1s) in critical paths.
- Long-running transactions (blocking others).
- Frequent timeouts (e.g., PostgreSQL: `connection timeout`; MySQL: `lock wait timeout`).

✅ **High CPU/Memory Usage**
- Database server CPU > 80% under normal load.
- OOM (Out-of-Memory) errors in logs.
- Swapping (disk I/O spikes).

✅ **Increased Disk I/O**
- High disk latency (`iostat -x 1` on Linux shows high `%util`).
- Slow `fsync` or `write` operations in logs.

✅ **Connection Leaks**
- Too many open connections (`SHOW PROCESSLIST` in MySQL).
- Connection pool exhaustion errors (e.g., `"Too many connections"`).
- Zombie connections (orphaned but unclosed).

✅ **Lock Contention**
- `SHOW ENGINE INNODB STATUS` (MySQL) shows long-running locks.
- PostgreSQL: `pg_locks` shows blocked transactions.

### **Security & Compliance Symptoms**
✅ **Unauthorized Access Attempts**
- Failed login attempts in logs (`auth.log`, `postgresql.log`).
- Suspicious SQL queries (e.g., `DROP TABLE`, `GRANT ALL`).

✅ **Exposed Credentials**
- Hardcoded passwords in source code (e.g., via `git grep`).
- Missing TLS/SSL in connections.

### **Data Integrity & Availability Symptoms**
✅ **Corrupted Data**
- Inconsistent records (e.g., foreign key violations).
- `PANIC` logs in PostgreSQL (`postgresql-XX.log`).
- MySQL: `InnoDB: Error: page 0 corrupted`.

✅ **Failed Backups**
- Corrupted backup files (e.g., `pg_dump: error: could not connect to database`).
- Long backup times (> expected duration).

✅ **Replication Lag**
- Slave falls behind master (`SHOW SLAVE STATUS` in MySQL).
- PostgreSQL: `pg_stat_replication` shows high lag.

---

## **2. Common Issues and Fixes**

### **Issue 1: Slow Queries**
**Symptom:**
- A specific query takes >500ms to execute.
- Application logs show slow SQL execution.

**Root Causes:**
- Missing indexes on frequently queried columns.
- Unoptimized JOINs or subqueries.
- Lack of query caching.
- Full table scans (`Full Table Scan` in PostgreSQL EXPLAIN).

**Fixes:**

#### **MySQL Example: Analyze and Fix Slow Query**
```sql
-- Find the slowest query
SELECT * FROM performance_schema.events_statements_summary_by_digest
ORDER BY sum_timer_wait DESC LIMIT 1;

-- Add an index
ALTER TABLE orders ADD INDEX idx_customer_id (customer_id);

-- Use EXPLAIN to verify
EXPLAIN SELECT * FROM orders WHERE customer_id = 123;
```
**Expected Output:**
```
+------+-------------+-----------+------------+------+---------------+------+---------+------+------+----------+-------------+
| id   | select_type | table     | partitions | type | possible_keys | key  | key_len | ref  | rows | filtered | Extra       |
+------+-------------+-----------+------------+------+---------------+------+---------+------+------+----------+-------------+
| 1    | SIMPLE      | orders    | NULL       | ref  | idx_customer_id | idx_customer_id | 4 | const     | 1    | 100.00   | NULL        |
+------+-------------+-----------+------------+------+---------------+------+---------+------+------+----------+-------------+
```
**Key Fix:**
- `type: ref` is efficient (uses index).
- If `type: ALL` (full scan), add an index.

---

#### **PostgreSQL Example: Use EXPLAIN ANALYZE**
```sql
-- Analyze the query plan
EXPLAIN ANALYZE SELECT * FROM products WHERE category = 'Electronics';

-- If it does a Seq Scan, add an index
CREATE INDEX idx_category ON products(category);

-- Verify
EXPLAIN ANALYZE SELECT * FROM products WHERE category = 'Electronics';
```
**Expected Output (after index):**
```
Index Scan using idx_category on products  (cost=0.27..8.29 rows=1 width=12)
```

**Prevention:**
- Enable the query cache:
  ```sql
  -- MySQL
  SET optimizer_switch='index_merge=on';

  -- PostgreSQL
  SET enable_seqscan = off;  -- Disable sequential scans (use with caution)
  ```
- Use ORM query logging (e.g., Django `DEBUG=True`, Spring `spring.jpa.show-sql=true`).

---

### **Issue 2: Connection Leaks**
**Symptom:**
- `Too many connections` error in MySQL/PostgreSQL.
- Connection pool (e.g., PgBouncer, HikariCP) reports exhaustion.

**Root Causes:**
- Unclosed database connections in code.
- Long-running transactions without `COMMIT`/`ROLLBACK`.
- Connection timeouts not handled properly.

**Fixes:**

#### **Java (HikariCP) Example: Close Connections Properly**
```java
// BAD: Missing close
try (Connection conn = dataSource.getConnection()) {
    Statement stmt = conn.createStatement();
    ResultSet rs = stmt.executeQuery("SELECT * FROM users");
} // Connection auto-closed, but Statement/ResultSet may leak

// GOOD: Use try-with-resources for all resources
try (Connection conn = dataSource.getConnection();
     Statement stmt = conn.createStatement();
     ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {
    while (rs.next()) {
        System.out.println(rs.getString("name"));
    }
}
```
**Key Fix:**
- Always close `Statement`, `ResultSet`, and `Connection` in a `try-with-resources` block.

---

#### **PostgreSQL: Configure PgBouncer**
```ini
# /etc/pgbouncer/pgbouncer.ini
[databases]
* = host=dbhost port=5432 dbname=app user=app

[pgbouncer]
listen_addr = *
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 1000  # Increase if needed
default_pool_size = 50
```
**Restart PgBouncer:**
```bash
sudo systemctl restart pgbouncer
```

**Prevention:**
- Enforce connection timeouts in DB config:
  ```sql
  -- MySQL
  SET wait_timeout = 300;  -- 5 minutes

  -- PostgreSQL
  ALTER SYSTEM SET statement_timeout = '10min';
  ```
- Use connection pooling (e.g., PgBouncer, HikariCP).

---

### **Issue 3: Lock Contention**
**Symptom:**
- Long-running transactions block others.
- `pg_locks` (PostgreSQL) or `SHOW ENGINE INNODB STATUS` (MySQL) shows deadlocks.

**Root Causes:**
- No proper index on `WHERE`/`JOIN` clauses.
- Long transactions (e.g., bulk inserts without `COMMIT`).
- Nested transactions without explicit `COMMIT`.

**Fixes:**

#### **PostgreSQL: Break Long Transactions**
```sql
-- Check for long transactions
SELECT pid, now() - query_start AS duration
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 min';

-- Kill the problematic transaction
SELECT pg_terminate_backend(pid);
```
**Best Practice:**
- Use `BEGIN;` + `COMMIT;` for short transactions.
- Avoid `AUTOCOMMIT=0` unless necessary.

---

#### **MySQL: Optimize Locking with Proper Indexes**
```sql
-- BAD: No index → table lock
UPDATE orders SET status = 'shipped' WHERE order_id = 123;

-- GOOD: Use index for row-level lock
ALTER TABLE orders ADD INDEX idx_status (status);

-- Still slow? Use batch updates
UPDATE orders SET status = 'shipped' WHERE order_id IN (123, 456, 789);
```
**Prevention:**
- Use `SELECT ... FOR UPDATE` sparingly (it locks rows).
- Avoid `LEFT JOIN ... WHERE right_table.column IS NULL` (can block).

---

### **Issue 4: Replication Lag**
**Symptom:**
- Slave falls behind master by >5 minutes.
- Transactions are lost on failover.

**Root Causes:**
- Slow replica (underpowered hardware).
- High load on master.
- Binary log group size too large (`binlog_row_image=FULL`).
- Replica lag due to disk I/O bottleneck.

**Fixes:**

#### **MySQL: Check Replication Status**
```sql
SHOW SLAVE STATUS\G
```
**If `Seconds_Behind_Master > 300`:**
```sql
-- Increase binlog group commit settings (reduces lag)
SET GLOBAL binlog_group_commit_sync_delay = 0;
SET GLOBAL binlog_group_commit_sync_no_delay_count = 3;
```

#### **PostgreSQL: Optimize Replication**
```sql
-- Check replication lag
SELECT * FROM pg_stat_replication;

-- Increase wal_level for better replication
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 10;  -- Increase parallel streams
```
**Prevention:**
- Use **GTID-based replication** (MySQL) or **Logical Replication** (PostgreSQL).
- Monitor lag with tools like `pt-heartbeat` (MySQL) or `pg_qcluster` (PostgreSQL).

---

### **Issue 5: Corrupted Data**
**Symptom:**
- `PANIC` in PostgreSQL logs.
- MySQL: `InnoDB: Error: page 0 corrupted`.
- Data inconsistency (e.g., orphaned records).

**Root Causes:**
- Forceful shutdown (`kill -9` on DB process).
- Disk failures or filesystem errors.
- Custom triggers/`AFTER` hooks causing issues.

**Fixes:**

#### **PostgreSQL: Recover from Corruption**
```bash
# Run fsck on the database cluster
sudo -u postgres /usr/lib/postgresql/XX/bin/pg_resetwal -f /var/lib/postgresql/XX/main
sudo -u postgres /usr/lib/postgresql/XX/bin/pg_ctl -D /var/lib/postgresql/XX/main -l logfile start
```
**Prevention:**
- **Always use `pg_ctl` or `mysqld_safe`** (never `kill -9`).
- Enable **point-in-time recovery (PITR)**:
  ```sql
  -- PostgreSQL: Configure WAL archiving
  ALTER SYSTEM SET wal_keep_size = '1GB';
  ALTER SYSTEM SET archive_command = 'test ! -f /backups/wal_%f && cp %p /backups/wal_%f';

  -- MySQL: Enable binary logging
  SET GLOBAL log_bin = '/var/log/mysql/mysql-bin.log';
  SET GLOBAL binlog_format = 'ROW';
  ```

---

## **3. Debugging Tools and Techniques**

### **Performance Analysis**
| Tool               | Purpose                          | Example Command/Usage                     |
|--------------------|----------------------------------|-------------------------------------------|
| **MySQL `EXPLAIN`** | Query optimization              | `EXPLAIN SELECT * FROM users WHERE email = 'x@y.com'` |
| **PostgreSQL `EXPLAIN ANALYZE`** | Query profiling                 | `EXPLAIN ANALYZE SELECT * FROM orders`   |
| **`pt-query-digest`** | MySQL slow query analysis      | `pt-query-digest /var/log/mysql/slow.log` |
| **`pg_stat_statements`** | PostgreSQL query tracking       | `CREATE EXTENSION pg_stat_statements;`    |
| **`perf` (Linux)** | System-level profiling          | `perf top` (for DB server bottlenecks)    |
| **`vmstat`, `iostat`** | Disk & memory analysis         | `iostat -x 1` (check `%util` for disk)    |
| **`NETSTAT`**      | Connection leaks                 | `netstat -tulnp | grep mysql`                            |

---

### **Security Auditing**
| Tool               | Purpose                          | Example Command/Usage                     |
|--------------------|----------------------------------|-------------------------------------------|
| **`pgAudit` (PostgreSQL)** | Audit logs                        | `CREATE EXTENSION pgaudit;`               |
| **`auditd` (Linux)** | System-level security logs       | `sudo auditctl -w /var/lib/postgresql -p wa` |
| **`mysqld --verbose`** | MySQL security checks        | `mysqld --verbose --help | grep "security"` |
| **`pgBadger`**      | PostgreSQL log analysis          | `pgBadger /var/log/postgresql/postgresql-XX.log` |
| **`sqitch`**        | Database schema migrations        | `sqitch deploy` (tracks changes)          |

---

### **Replication & High Availability**
| Tool               | Purpose                          | Example Command/Usage                     |
|--------------------|----------------------------------|-------------------------------------------|
| **`pt-table-checksum`** | MySQL replication health      | `pt-table-checksum -h master -u user -p'pass' -a DB.table` |
| **`pg_isready`**      | PostgreSQL health check         | `pg_isready -h replica -p 5432`           |
| **`mysqlrpladmin`**   | MySQL replication monitoring    | `mysqlrpladmin --host master --port 3306` |
| **`consul`/`etcd`**   | Service discovery for DB failover | Auto-detect primary replica               |

---

## **4. Prevention Strategies**

### **Database Configuration Best Practices**
| Database  | Setting                          | Recommended Value                          | Purpose                                  |
|-----------|----------------------------------|-------------------------------------------|------------------------------------------|
| **MySQL** | `innodb_buffer_pool_size`       | 50-70% of RAM                             | Optimize InnoDB cache                     |
| **MySQL** | `max_connections`                | 2-4x CPU cores                            | Prevent connection leaks                 |
| **MySQL** | `wait_timeout`                   | 300 (5 min)                               | Auto-close idle connections              |
| **MySQL** | `binlog_format`                  | `ROW`                                      | For better replication                  |
| **PostgreSQL** | `shared_buffers`          | 25% of RAM                                | Optimize shared memory caching           |
| **PostgreSQL** | `effective_cache_size`      | 75% of RAM                               | PostgreSQL cache estimation              |
| **PostgreSQL** | `work_mem`                       | 16MB–64MB (adjust for large queries)     | Temp memory for sorts/joins              |
| **PostgreSQL** | `max_worker_processes`         | `max_connections / 4`                     | Parallel query processing                |

---

### **Schema & Index Optimization**
✅ **Normalize when possible**, but avoid over-normalization (denormalize for read-heavy workloads).
✅ **Use composite indexes** for common query patterns:
   ```sql
   CREATE INDEX idx_user_email_status ON users(email, status);
   ```
✅ **Avoid `SELECT *`**—fetch only needed columns.
✅ **Use `EXPLAIN` early** in development to catch bad queries.
✅ **Partition large tables**:
   ```sql
   -- MySQL: Partition by range
   ALTER TABLE logs PARTITION BY RANGE (YEAR(date)) (
       PARTITION p2023 VALUES LESS THAN (2024),
       PARTITION p2024 VALUES LESS THAN (2025)
   );

   -- PostgreSQL: Partition by list
   CREATE TABLE sales (
       id SERIAL,
       amount DECIMAL
   ) PARTITION BY LIST (quarter);

   CREATE TABLE sales_q1 PARTITION OF sales FOR VALUES IN (1);
   ```

---

### **Backup & Disaster Recovery**
✅ **Automate backups** (e.g., `mysqldump`, `pg_dump`, or logical backups via `WAL`).
✅ **Test restore procedures** monthly.
✅ **Use immutable backups** (e.g., AWS S3 + versioning, GCS).
✅ **Set up replication for HA**:
   - **MySQL**: Async + Semi-sync replication.
   - **PostgreSQL**: Streaming replication + Patroni/Repmgr.

**Example MySQL Backup Script:**
```bash
#!/bin/bash
DB_USER="backup_user"
DB_PASS="secure_password"
BACKUP_DIR="/backups/mysql"

# Full backup
mysqldump -u $DB_USER -p$DB_PASS --all-databases --single-transaction --master-data=2 > $BACKUP_DIR/full_backup.sql

# Binary log backup
mysql -u $DB_USER -p$DB_PASS -e "SHOW MASTER STATUS" | awk 'NR==2 {print $1}' > $BACKUP_DIR/master_binlog
```

---

### **Monitoring & Alerting**
✅ **Track these metrics** (via Prometheus/Grafana, Datadog, etc.):
- **Performance**: Query latency, lock wait time, disk I/O.
- **Replication**: Slave lag, transaction backlog.
- **Connections**: Active connections, pool usage.
- **Errors**: Failed logins, disk errors.

**Example Grafana Dashboard:**
- **MySQL**: `Slow queries`, `Threads_running`, `Innodb_buffer_pool_wait_free`.
- **PostgreSQL**: `pg_stat_database`,