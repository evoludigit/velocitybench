# **Debugging Databases: A Troubleshooting Guide**
*A structured, actionable approach to identifying and resolving database-related issues efficiently.*

---

## **1. Introduction**
Databases serve as the backbone of modern applications, handling critical data storage, retrieval, and transactions. When issues arise—whether performance degradation, connectivity failures, or logical errors—quick resolution is essential to minimize downtime.

This guide provides a **systematic breakdown** of common database symptoms, root causes, and fixes, along with debugging tools, techniques, and prevention strategies.

---

## **2. Symptom Checklist**
Before diving into fixes, verify if the issue aligns with any of these symptoms:

| **Category**          | **Symptoms**                                                                 |
|-----------------------|------------------------------------------------------------------------------|
| **Availability**      | Database unreachable (connection refused, timeouts)                        |
|                       | Service crashes (e.g., PostgreSQL "fatal: refusing to shut down while sessions remain") |
| **Performance**       | Slow queries (response times > 1-2 seconds)                                 |
|                       | High CPU/memory usage in database processes                                 |
| **Data Corruption**   | Inconsistent data (null values where expected, duplicate records)           |
|                       | Failed transactions (e.g., "deadlock," "serialization failure")             |
| **Configuration**     | Logs indicate misconfigured settings (e.g., `max_connections` exhausted)    |
| **Replication**       | Lag between primary and replica nodes                                       |
| **Backup & Recovery** | Failed backups or corruption in restored data                              |

---

## **3. Common Issues & Fixes**

### **Issue 1: Database Unreachable (Connection Failures)**
**Symptoms:**
- `Connection refused` (e.g., MySQL: `MySQL server has gone away`)
- Timeout errors when connecting from application

**Root Causes:**
- Database server down (crash, kill -9)
- Firewall blocking ports (e.g., MySQL: `3306`, PostgreSQL: `5432`)
- Incorrect credentials or IP whitelisting
- Resource exhaustion (max connections reached)

**Debugging Steps:**
1. **Verify Server Status**
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql

   # Check MySQL status
   sudo systemctl status mysql
   ```
   - If down, restart the service:
     ```bash
     sudo systemctl restart postgresql
     ```

2. **Check Listeners**
   - Ensure the database is listening on the correct IP/port:
     ```sql
     -- PostgreSQL: Check active connections and listeners
     SELECT pid, usename, application_name, client_addr FROM pg_stat_activity;

     -- MySQL: Check active connections
     SHOW PROCESSLIST;
     ```

3. **Firewall/Network**
   - Test connectivity from the application server:
     ```bash
     telnet <db-host> <port>  # Should succeed
     ```
   - If blocked, add a rule:
     ```bash
     sudo ufw allow from <app-server-ip> to any port <port>
     ```

4. **Max Connections Exhausted**
   - Check current connections vs. limit:
     ```sql
     -- PostgreSQL
     SHOW max_connections;
     SELECT count(*) FROM pg_stat_activity;

     -- MySQL
     SHOW VARIABLES LIKE 'max_connections';
     SHOW STATUS LIKE 'Threads_connected';
     ```
   - Increase limit (temporarily for testing):
     ```sql
     -- PostgreSQL (via postgresql.conf)
     max_connections = 200
     ```
     ```sql
     -- MySQL (via my.cnf)
     max_connections = 300
     ```
   - Restart the database after changes.

---

### **Issue 2: Slow Queries & Performance Degradation**
**Symptoms:**
- Long-running queries (>1s)
- High CPU/memory usage
- "Table lock" or "full table scan" warnings in logs

**Root Causes:**
- Missing indexes
- Poorly written queries (e.g., `SELECT *`)
- Lack of query optimization
- Disk I/O bottlenecks (SSD vs. HDD)

**Debugging Steps:**
1. **Identify Slow Queries**
   - Enable slow query logging (PostgreSQL/MySQL):
     ```sql
     -- PostgreSQL: log_min_duration_statement = 1000 (ms)
     -- MySQL: slow_query_log = 1, slow_query_log_file = /var/log/mysql/slow.log
     ```
   - Check logs for problematic queries.

2. **Analyze Query Plans**
   - Use `EXPLAIN` to inspect execution plans:
     ```sql
     EXPLAIN ANALYZE SELECT * FROM users WHERE created_at > '2023-01-01';
     ```
   - Look for:
     - Full table scans (`Seq Scan` instead of `Index Scan`)
     - High cost operations (`Sort`, `Hash Join`)

3. **Add/Improve Indexes**
   - If a query lacks an index:
     ```sql
     CREATE INDEX idx_users_created_at ON users(created_at);
     ```
   - Verify with `EXPLAIN` after adding.

4. **Optimize Queries**
   - Avoid `SELECT *`; fetch only needed columns.
   - Use `LIMIT` for pagination.
   - Replace `IN` clauses with joins if possible.

5. **Monitor Resource Usage**
   - Check database process resource usage:
     ```bash
     # PostgreSQL
     pg_stat_activity;

     # MySQL
     SHOW FULL PROCESSLIST;
     ```

---

### **Issue 3: Data Corruption**
**Symptoms:**
- Null values in non-nullable columns
- Duplicate primary keys
- Transaction errors ("unique violation")

**Root Causes:**
- Programmatic errors (e.g., failing to check `INSERT` returns)
- Disk corruption
- Improper shutdowns

**Debugging Steps:**
1. **Validate Data Integrity**
   - Check for constraints violations:
     ```sql
     -- PostgreSQL: Check for NULLs in NOT NULL columns
     SELECT column_name, COUNT(*)
     FROM information_schema.columns
     WHERE table_name = 'users'
     AND is_nullable = 'NO';

     -- MySQL: Check duplicate keys
     SHOW KEYS FROM users;
     ```

2. **Transaction Logs**
   - Review `pg_notify` (PostgreSQL) or MySQL error logs for transaction failures.

3. **Database Consistency Checks**
   - Run integrity checks (PostgreSQL):
     ```sql
     VACUUM VERBOSE ANALYZE users;
     ```
   - For MySQL:
     ```sql
     REPAIR TABLE users;
     ```

4. **Restore from Backup**
   - If corruption is severe, restore from the last known-good backup.

---

### **Issue 4: Replication Lag**
**Symptoms:**
- Secondary nodes fall behind the primary by minutes/hours
- Stale reads from replicas

**Root Causes:**
- Slow network between nodes
- High write load on primary
- Replication filter misconfigurations

**Debugging Steps:**
1. **Check Replication Status**
   - PostgreSQL:
     ```sql
     SELECT * FROM pg_stat_replication;
     ```
   - MySQL:
     ```sql
     SHOW SLAVE STATUS;
     ```
   - Look for `Seconds_Behind_Master`.

2. **Increase Replication Buffer**
   - Postgres: Adjust `max_wal_senders` and `max_replication_slots`.
   - MySQL: Increase `binlog_row_event_max_msec_delay`.

3. **Tune Network**
   - Ensure low-latency connections between nodes:
     ```bash
     ping <primary-ip>
     ```

4. **Filter Relevant Changes**
   - Use `replica_identification` (Postgres) or `binlog-do-table` (MySQL) to reduce traffic.

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Usage**                          |
|--------------------------|-----------------------------------------------------------------------------|--------------------------------------------|
| **`pgbadger`**           | PostgreSQL log analysis                                                              | `pgbadger /var/log/postgresql/postgresql.log` |
| **`mysqldump`**          | MySQL backup/restore and query inspection                                       | `mysqldump -u root db_name > query.sql`      |
| **`pg_profiler`**        | PostgreSQL query profiling                                                        | Attach to PostgreSQL process with `pg_profiler` |
| **`pt-query-digest`**   | Analyze MySQL slow queries                                                      | `pt-query-digest slow.log`                 |
| **`strace`**             | Trace system calls (e.g., for stuck processes)                                  | `strace -p <pid>`                          |
| **`netstat`/`ss`**       | Check network connections to/from the database                                  | `ss -tulnp | grep mysql`                        |
| **`pg_top`/`mysqlslow`** | Interactive monitoring of database processes                                   | `pg_top`                                  |

**Advanced Technique: Kernel Logs**
- Check for OS-level issues (e.g., OOM killer killing database processes):
  ```bash
  dmesg | grep -i "kill" | tail -n 20
  ```

---

## **5. Prevention Strategies**

### **A. Monitoring & Alerts**
- **Key Metrics to Monitor:**
  - Connection counts (`max_connections` vs. active)
  - Query performance (slow queries)
  - Replication lag
  - Disk I/O latency
- **Tools:**
  - Prometheus + Grafana
  - Datadog/New Relic
  - Custom scripts (e.g., `pg_stat_statements` for PostgreSQL)

### **B. Configuration Best Practices**
- **General:**
  - Set `max_connections` to ~1.5x expected peak load.
  - Enable query logging (but avoid excessive disk writes).
- **PostgreSQL:**
  - `shared_buffers`: 25% of RAM (minimum 1GB).
  - `effective_cache_size`: 70% of RAM.
- **MySQL:**
  - `innodb_buffer_pool_size`: 80% of RAM.
  - `innodb_log_file_size`: 25% of `innodb_buffer_pool_size`.

### **C. Backup & Recovery**
- **Automate backups** (e.g., `pg_dump` cron jobs, MySQL `mysqldump`).
- **Test restores** regularly.
- **Use point-in-time recovery (PITR)** for critical databases (Postgres: `pg_basebackup`).

### **D. Query Optimization**
- **Standardize SQL**: Enforce consistent query formats (e.g., avoid dynamic SQL where possible).
- **Use ORMs wisely**: Avoid N+1 queries (e.g., Django `select_related`).
- **Denormalize judiciously**: Add computed columns if joins are expensive.

### **E. Hardware & OS Tuning**
- **SSDs for databases** (avoid HDDs for I/O-bound workloads).
- **Tune kernel parameters** (e.g., `vm.swappiness=10`).
- **Separate database from application servers** (dedicated nodes for high availability).

---

## **6. Summary of Quick Fixes**
| **Issue**                | **Immediate Action**                                                                 |
|--------------------------|------------------------------------------------------------------------------------|
| **Database down**        | Restart service (`systemctl restart postgresql`)                                   |
| **Connection refused**   | Check firewall, credentials, and `netstat -tulnp`                                   |
| **Slow queries**         | Add indexes, use `EXPLAIN`, optimize SQL                                             |
| **Max connections**      | Temporarily increase `max_connections`                                            |
| **Replication lag**      | Check `pg_stat_replication`/`SHOW SLAVE STATUS`; adjust network/buffer settings    |
| **Data corruption**      | Restore from backup; validate with `VACUUM` or `REPAIR TABLE`                     |

---

## **7. When to Escalate**
- If issues persist after applying fixes, consult:
  - Database vendor resources (e.g., [PostgreSQL docs](https://www.postgresql.org/docs/))
  - Community forums (e.g., [Server Fault](https://serverfault.com/), [r/postgresql](https://www.reddit.com/r/postgresql/))
  - Professional support (e.g., AWS RDS support, Percona for MySQL)

---
**Final Tip:** Always **reproduce the issue in a staging environment** before applying fixes in production. Use tools like `docker-compose` to spin up test databases quickly.

---
This guide balances **depth** (with concrete examples) and **practicality** (focused on quick resolution). Adjust based on your specific database (PostgreSQL, MySQL, MongoDB, etc.) and stack.