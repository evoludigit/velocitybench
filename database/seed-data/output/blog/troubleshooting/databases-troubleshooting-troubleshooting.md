# **Debugging Databases: A Practical Troubleshooting Guide**

## **1. Introduction**
Databases are critical components of modern applications, yet they frequently encounter performance bottlenecks, connection issues, data corruption, or schema mismatches. This guide provides a structured approach to diagnosing and resolving common database problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, identify symptoms to narrow down the issue:

### **A. Connection & Availability Issues**
- [ ] Database server is unreachable (`ping`, `telnet`, or connection refused).
- [ ] Connection timeouts (`Connection refused`, `Network is unreachable`).
- [ ] High connection rejection rates (`Too many connections`).
- [ ] Slow query response times (seconds to minutes).
- [ ] Frequent connection resets (`Connection reset by peer`).

### **B. Performance Degradation**
- [ ] Slow query execution (long-running queries).
- [ ] High CPU, memory, or disk I/O usage.
- [ ] Slow reads/writes (e.g., `SELECT` queries taking forever).
- [ ] Frequent `OOM (Out of Memory)` errors.
- [ ] Database server crashes under load.

### **C. Data Integrity & Corruption Issues**
- [ ] Inconsistent data (`NULL` where expected values exist).
- [ ] Duplicate records or missing data.
- [ ] Transaction failures (`Rollback`, `Deadlock`).
- [ ] Corrupted indexes (`Table locked`, `Table corrupted`).
- [ ] Failed backups (`Backup failed`, `Incomplete restore`).

### **D. Schema & Configuration Misconfigurations**
- [ ] Schema mismatches (e.g., missing columns in production).
- [ ] Incorrect constraints (e.g., `FOREIGN KEY` violations).
- [] Missing indexes on frequently queried columns.
- [ ] Improper memory allocation (e.g., `innodb_buffer_pool_size` too low).
- [ ] Misconfigured replication (lag in master-slave setups).

---

## **3. Common Issues & Fixes**

### **A. Connection Problems: "Database Unreachable"**
**Symptoms:**
- Application cannot connect to the database.
- `Connection refused` or `Network is unreachable`.

**Root Causes & Fixes:**
1. **Check Network Connectivity**
   - Verify if the DB server is reachable:
     ```bash
     ping <database-ip>
     telnet <database-ip> <port>  # e.g., 3306 (MySQL), 5432 (PostgreSQL)
     ```
   - If unreachable, check firewalls, VPN, or cloud security groups.

2. **Check Database Service Status**
   - Restart the DB service if down:
     ```bash
     # MySQL
     sudo systemctl restart mysql

     # PostgreSQL
     sudo systemctl restart postgresql
     ```
   - Check logs for errors:
     ```bash
     sudo journalctl -u mysql --no-pager -n 50  # MySQL logs
     sudo tail -n 50 /var/log/postgresql/postgresql-*.log  # PostgreSQL logs
     ```

3. **Verify Listening Port**
   - Ensure the DB is binding to the correct IP/port:
     ```bash
     # MySQL
     netstat -tulnp | grep mysql

     # PostgreSQL
     sudo ss -tulnp | grep postgres
     ```

4. **Check Max Connections**
   - If the DB is overwhelmed, increase max connections:
     ```sql
     -- MySQL
     SHOW VARIABLES LIKE 'max_connections';
     SET GLOBAL max_connections = 1000;  # Temporarily

     -- PostgreSQL
     SHOW max_connections;
     ALTER SYSTEM SET max_connections = 200;
     ```

---

### **B. Slow Queries & Performance Bottlenecks**
**Symptoms:**
- Queries taking >2 seconds.
- High CPU/memory usage.

**Root Causes & Fixes:**
1. **Identify Slow Queries**
   - Enable slow query logging:
     ```sql
     -- MySQL
     SET GLOBAL slow_query_log = 'ON';
     SET GLOBAL long_query_time = 1;  # Log queries >1s

     -- PostgreSQL
     ALTER SYSTEM SET log_min_duration_statement = '1000';  # Log >1s queries
     ```
   - Check slow logs:
     ```bash
     tail -f /var/log/mysql/mysql-slow.log  # MySQL
     psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"  # PostgreSQL
     ```

2. **Optimize Queries**
   - Add missing indexes:
     ```sql
     CREATE INDEX idx_user_email ON users(email);
     ```
   - Avoid `SELECT *`; fetch only needed columns.
   - Rewrite inefficient queries (e.g., `NOT IN` → `NOT EXISTS`).

3. **Tune Database Configuration**
   - Adjust `innodb_buffer_pool_size` (MySQL):
     ```ini
     # my.cnf
     innodb_buffer_pool_size = 2G  # Should be ~70% of RAM
     ```
   - Increase PostgreSQL `shared_buffers`:
     ```sql
     ALTER SYSTEM SET shared_buffers = '1GB';
     ```

4. **Enable Query Cache (If Applicable)**
   ```sql
   -- MySQL
   SET GLOBAL query_cache_size = 64M;
   SET GLOBAL query_cache_type = ON;
   ```

---

### **C. Data Corruption & Consistency Issues**
**Symptoms:**
- `Table corrupted`, `Foreign key violation`, `Deadlock`.

**Root Causes & Fixes:**
1. **Repair Corrupted Tables**
   ```sql
   -- MySQL
   CHECK TABLE users;
   REPAIR TABLE users;

   -- PostgreSQL (use `pg_restore` or `VACUUM FULL`)
   VACUUM (VERBOSE, ANALYZE, FULL) users;
   ```

2. **Handle Deadlocks**
   - Log deadlocks:
     ```sql
     SET GLOBAL innodb_print_all_deadlocks = ON;
     ```
   - Retry failed transactions with exponential backoff (application code).

3. **Fix Foreign Key Issues**
   ```sql
   -- Temporarily disable constraints
   SET FOREIGN_KEY_CHECKS = 0;
   -- Fix data
   SET FOREIGN_KEY_CHECKS = 1;
   ```

---

### **D. Replication Lag & Synchronization Issues**
**Symptoms:**
- Master-slave replication delayed (>5 min).
- `Slave is not running`.

**Root Causes & Fixes:**
1. **Check Replication Status**
   ```sql
   -- MySQL
   SHOW SLAVE STATUS \G;

   -- PostgreSQL
   SELECT * FROM pg_stat_replication;
   ```

2. **Fix Replication Lag**
   - Increase binary log retention:
     ```sql
     -- MySQL
     SET GLOBAL binlog_row_image = 'FULL';
     SET GLOBAL binlog_expire_logs_seconds = 2592000;  # 30 days
     ```
   - Increase network buffer size (PostgreSQL `wal_level`):
     ```sql
     ALTER SYSTEM SET wal_level = 'replica';
     ALTER SYSTEM SET max_wal_senders = 4;
     ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                  | **Example Commands**                     |
|--------------------------|---------------------------------------------|------------------------------------------|
| **`top`/`htop`**         | Check CPU/memory usage.                     | `top -d 1`                               |
| **`iostat`/`vmstat`**    | Monitor disk I/O and system stats.          | `iostat -x 1`                            |
| **`pg_top`/`my_top`**    | Real-time DB performance monitoring.        | `my_top` (MySQL)                        |
| **`EXPLAIN`**            | Analyze query execution plans.              | `EXPLAIN SELECT * FROM users WHERE id=1;` |
| **`pgbadger`/`mydumper`**| Log analysis & backup tools.               | `pgbadger /var/log/postgresql/*.log`     |
| **Cloud DB Dashboards**  | AWS RDS, Google Cloud SQL, Azure Monitor.   | Check metrics in cloud console.          |

**Profiling Queries:**
```sql
-- MySQL
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;

-- PostgreSQL
EXPLAIN (ANALYZE, VERBOSE) SELECT * FROM orders WHERE user_id = 123;
```

---

## **5. Prevention Strategies**

### **A. Best Practices for Database Maintenance**
✅ **Monitor Performance Regularly**
   - Set up alerts for slow queries (`Prometheus + Grafana`).
   - Use `pg_stat_statements` (PostgreSQL) or `Performance Schema` (MySQL).

✅ **Optimize Schema & Indexes**
   - Avoid schema changes in production during peak hours.
   - Regularly optimize tables:
     ```sql
     OPTIMIZE TABLE large_table;  # MySQL
     VACUUM ANALYZE;              # PostgreSQL
     ```

✅ **Backup & Disaster Recovery**
   - Automate backups:
     ```bash
     # MySQL (mysqldump)
     mysqldump -u root -p --all-databases > backup.sql

     # PostgreSQL (pg_dump)
     pg_dumpall -U postgres > backup.sql
     ```
   - Test restore procedures.

✅ **Use Connection Pooling**
   - Reduce connection overhead with `PgBouncer` (PostgreSQL) or `ProxySQL` (MySQL).

✅ **Load Testing**
   - Simulate traffic with `Locust` or `JMeter` before deployment.

### **B. Configuration Checklist**
| **Setting**               | **MySQL**                     | **PostgreSQL**               |
|---------------------------|-------------------------------|------------------------------|
| **Buffer Pool**           | `innodb_buffer_pool_size`    | `shared_buffers`             |
| **Logging**               | `log_error`, `slow_query_log` | `log_statement = 'all'`      |
| **Replication**           | `binlog_format = ROW`         | `wal_level = replica`        |
| **Max Connections**       | `max_connections`             | `max_connections`            |

---

## **6. Conclusion**
Database troubleshooting requires a structured approach:
1. **Isolate symptoms** (connection? performance? corruption?).
2. **Check logs & metrics** (slow logs, CPU, disk I/O).
3. **Apply fixes** (indexes, config tuning, repairs).
4. **Prevent recurrence** (backups, monitoring, load testing).

By following this guide, you can diagnose and resolve most database issues efficiently. For persistent problems, consult **DBA tools** (`pt-query-digest`, `pg_stat_tables`) or vendor documentation.

---
**Need faster resolution?** Use `EXPLAIN`, `pg_top`, and `netstat` first.