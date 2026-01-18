# **[Pattern] Databases Troubleshooting – Reference Guide**

---

## **1. Overview**
Databases Troubleshooting is a systematic approach to identifying, diagnosing, and resolving performance bottlenecks, connectivity issues, data corruption, or operational failures in database systems. This pattern covers diagnostic techniques, common error patterns, tooling, and best practices for ensuring database reliability, optimizing query performance, and restoring data integrity. Whether dealing with SQL Server, PostgreSQL, MySQL, or NoSQL systems, this guide provides a structured methodology for root-cause analysis and remediation.

---

## **2. Key Concepts**

### **2.1 Core Components**
| **Component**          | **Description**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Log Analysis**       | Reviewing database logs (e.g., error logs, slow query logs) to identify patterns, failures, or resource constraints.                                                                                                  |
| **Performance Monitoring** | Tracking key metrics (CPU, memory, I/O, query latency) to detect anomalies, bottlenecks, or inefficient operations.                                                                                               |
| **Query Analysis**     | Profiling slow queries using tools like `EXPLAIN`, `SHOW PROFILE`, or database-specific performance dashboards.                                                                                                   |
| **Data Integrity Checks** | Validating transactions, locks, deadlocks, and foreign key constraints to ensure data consistency.                                                                                                          |
| **Replication & Backup Troubleshooting** | Diagnosing lag in replication, failed backups, or corrupted restore points.                                                                                                                              |
| **Configuration Optimization** | Reviewing settings (e.g., `max_connections`, `innodb_buffer_pool_size`) to align with workload demands.                                                                                                       |
| **Hardware & OS Level Issues** | Investigating disk I/O saturation, memory pressure, or VM/container constraints impacting database performance.                                                                                                |
| **Security Audits**    | Checking for unauthorized access attempts, privilege escalation risks, or misconfigurations (e.g., weak passwords, open ports).                                                                         |

---

### **2.2 Common Troubleshooting Scenarios**
| **Scenario**                     | **Root Causes**                                                                                     | **Diagnostic Steps**                                                                                                                                                     |
|----------------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Slow Queries**                 | Missing indexes, complex joins, lack of proper indexing, or `SELECT *`.                          | Run `EXPLAIN` or use database profiling tools; analyze query execution plans.                                                                        |
| **High CPU/Memory Usage**        | Unoptimized queries, long-running transactions, or insufficient resources.                        | Check `top`, `htop`, or database-specific metrics (e.g., `pg_stat_activity` in PostgreSQL).                                                                           |
| **Deadlocks**                    | Concurrent transactions with conflicting locks.                                                      | Review deadlock graphs; adjust transaction isolation levels or optimize query order.                                                                                  |
| **Connection Pool Exhaustion**   | Too many idle connections or insufficient `max_connections` limit.                              | Adjust connection pooling settings or optimize application code to reuse connections.                                                                                  |
| **Failed Replication**           | Network issues, lag, or data type mismatches between primary and replica.                         | Check replication logs (`SHOW SLAVE STATUS` in MySQL); verify network stability and schema consistency.                                                          |
| **Corrupted Data**               | Unexpected crashes, improper shutdowns, or disk failures.                                          | Run database repair tools (`REPAIR TABLE` in MySQL, `pg_rewind` for PostgreSQL); restore from backups if corruption is severe.                                      |
| **Backup Failures**              | Permission issues, disk full, or corrupted backup media.                                          | Verify backup scripts, storage quotas, and test restore procedures regularly.                                                                                             |
| **Authentication Failures**     | Incorrect credentials, role permissions, or network restrictions.                               | Check authentication logs; validate user roles and network policies (e.g., firewalls).                                                                                  |

---

## **3. Schema Reference**
Below are key tables and metrics to monitor across databases (adjust syntax per engine).

### **3.1 Performance Monitoring Tables**
| **Database**   | **Table/View**               | **Description**                                                                                                                                                     |
|-----------------|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PostgreSQL**  | `pg_stat_activity`           | Active database sessions, CPU/time, and query duration.                                                                                                             |
| **MySQL**       | `performance_schema.events_statements_summary_by_digest` | Slow query analysis with execution counts and latency.                                                                                                           |
| **SQL Server**  | `sys.dm_exec_query_stats`    | Query performance metrics, including execution plan cache.                                                                                                         |
| **MongoDB**     | `db.system.profile`          | Slow operation log (enable with `profile: 1` or `profile: { slowms: 100 }`).                                                                                     |

### **3.2 Log Files**
| **Database**   | **Log File**                  | **Key Entries to Monitor**                                                                                                                                   |
|-----------------|------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **PostgreSQL**  | `postgresql.log` (or `pg_log`) | Connection errors, deadlocks, and slow query warnings.                                                                                                         |
| **MySQL**       | `error.log`                   | Startup errors, replication lag, and query execution warnings (set `log_errors` and `slow_query_log`).                                                       |
| **SQL Server**  | `ERRORLOG`                    | Failures, spills to tempdb, and replication issues (location: `C:\Program Files\Microsoft SQL Server\MSSQL.X\MSSQL\Log\`).                                  |
| **MongoDB**     | `mongod.log`                  | Auth failures, replication errors, and slow operations.                                                                                                         |

---

## **4. Query Examples**

### **4.1 Identifying Slow Queries**
#### **PostgreSQL**
```sql
-- Top 10 slowest queries by execution time
SELECT
    query,
    total_time,
    calls,
    mean_time
FROM
    pg_stat_statements
ORDER BY
    mean_time DESC
LIMIT 10;
```

#### **MySQL**
```sql
-- Slow queries with duration > 1 second
SELECT *
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_TIMER_WAIT > 1000000000;
```

#### **SQL Server**
```sql
-- Queries with high logical reads
SELECT
    qs.total_logical_reads,
    qs.execution_count,
    qs.total_worker_time,
    qs.query_plan
FROM
    sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_query_plan(qs.plan_handle)
ORDER BY
    qs.total_logical_reads DESC;
```

---

### **4.2 Checking Database Health**
#### **PostgreSQL: Connection Pool Status**
```sql
-- Active connections and their duration
SELECT
    usename,
    application_name,
    state,
    backend_start,
    now() - backend_start AS uptime
FROM
    pg_stat_activity
WHERE
    state = 'active';
```

#### **MySQL: Replication Status**
```sql
-- Check replication lag
SHOW SLAVE STATUS\G
-- Look for 'Seconds_Behind_Master' in the output.
```

#### **MongoDB: Replica Set Health**
```javascript
// Check replica set health in mongosh
rs.status()
-- Verify 'members' for "HEALTH OK" and "PB" (primary) status.
```

---

### **4.3 Data Integrity Checks**
#### **PostgreSQL: Check for Orphaned Rows**
```sql
-- Find rows violating foreign key constraints (e.g., `users.department_id`)
SELECT
    u.id,
    u.name,
    d.id AS missing_dept_id
FROM
    users u
LEFT JOIN
    departments d ON u.department_id = d.id
WHERE
    d.id IS NULL;
```

#### **SQL Server: Detect Lock Contention**
```sql
-- Identify long-running locks
SELECT
    r.resource_type,
    r.resource_database_id,
    r.resource_associated_entity_id,
    s.blocking_session_id,
    s.session_id
FROM
    sys.dm_tran_locks r
INNER JOIN
    sys.dm_tran_session_transactions t ON r.lock_session_id = t.transaction_id
INNER JOIN
    sys.dm_exec_sessions s ON t.session_id = s.session_id
WHERE
    r.request_mode IN ('X', 'U') AND s.is_user_process = 1;
```

---

## **5. Tools & Utilities**
| **Tool/Utility**               | **Purpose**                                                                                                                                                     | **Database Support**               |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| **pgBadger**                    | Parse PostgreSQL logs for errors, warnings, and slow queries.                                                                                                   | PostgreSQL                          |
| **mysqldump**                   | Backup/restore MySQL databases; useful for partial recovery.                                                                                                  | MySQL                               |
| **SQL Server Profiler**         | Capture and analyze T-SQL statements in real-time.                                                                                                           | SQL Server                          |
| **MongoDB Compass**             | GUI for diagnosing replication lag, index performance, and collection stats.                                                                                   | MongoDB                             |
| **pt-query-digest** (Percona)  | Analyze MySQL slow logs for patterns and bottlenecks.                                                                                                         | MySQL                               |
| **Redis CLI**                   | Inspect Redis keyspace, memory usage, and slow log.                                                                                                           | Redis                               |
| **Prometheus + Grafana**        | Monitor database metrics (CPU, memory, query latency) via exporters (e.g., `postgres_exporter`).                                                              | Multi-database                      |
| **AWS RDS Performance Insights** | Cloud-based query performance analysis for RDS instances.                                                                                                     | AWS RDS (PostgreSQL/MySQL)         |

---

## **6. Best Practices**
1. **Regular Maintenance**:
   - Schedule `VACUUM` (PostgreSQL), `OPTIMIZE TABLE` (MySQL), or `REINDEX` (SQL Server) to reclaim space.
   - Update statistics: `ANALYZE` (PostgreSQL), `UPDATE STATISTICS` (SQL Server).

2. **Indexing Strategy**:
   - Avoid over-indexing; focus on columns frequently filtered/sorted.
   - Use composite indexes for multi-column queries.

3. **Connection Management**:
   - Limit connection pool size; reuse connections with tools like PgBouncer (PostgreSQL) or ProxySQL (MySQL).

4. **Backup & Disaster Recovery**:
   - Test restores quarterly; document recovery procedures.
   - Use immutable backups (e.g., AWS S3 object locks) to prevent tampering.

5. **Security**:
   - Rotate credentials regularly; enforce least-privilege access.
   - Audit logs for suspicious activity (e.g., `pgAudit` for PostgreSQL).

6. **Scaling**:
   - Vertical scaling: Upgrade hardware for CPU/memory-bound workloads.
   - Horizontal scaling: Shard data (e.g., MongoDB sharding) or use read replicas.

---

## **7. Related Patterns**
- **[Database Scaling]** – Strategies for handling growth (sharding, partitioning, read replicas).
- **[Monitoring & Observability]** – Centralized logging, metrics, and alerting for databases.
- **[Schema Migration]** – Safely altering tables across environments without downtime.
- **[Data Replication]** – Designing high-availability setups (primary-replica, multi-region).
- **[Security Hardening]** – Protecting databases from injection, privilege escalation, and ransomware.
- **[Caching Strategies]** – Offloading queries to Redis or Memcached to reduce database load.

---
**References**:
- [PostgreSQL Docs – Troubleshooting](https://www.postgresql.org/docs/current/troubleshooting.html)
- [MySQL Performance Blog](https://www.percona.com/blog)
- [SQL Server Best Practices](https://learn.microsoft.com/en-us/sql/relational-databases/performance/best-practices-for-performance)
- [MongoDB Troubleshooting Guide](https://www.mongodb.com/docs/manual/troubleshooting/)