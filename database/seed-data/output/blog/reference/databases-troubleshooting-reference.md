# **[Pattern] Databases Troubleshooting: Reference Guide**

---

## **Overview**
Database troubleshooting ensures optimal performance, reliability, and data integrity in systems relying on relational, NoSQL, or specialized databases. This guide consolidates structured approaches, common issues, and actionable steps for diagnosing and resolving issues across cloud, on-premises, and hybrid environments. Key areas include performance bottlenecks, connectivity errors, schema inconsistencies, replication failures, and security vulnerabilities. The guide emphasizes systematic debugging—leveraging logs, metrics, and diagnostic tools—while providing role-specific workflows for DBAs, developers, and DevOps teams.

---

## **Key Concepts & Implementation Details**
### **1. Troubleshooting Phases**
| **Phase**          | **Objective**                                                                 | **Key Actions**                                                                                     |
|--------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Identification** | Pinpoint symptoms & categorize issues (e.g., latency, crashes, corruption). | Review logs (e.g., `syslog`, application logs), monitor metrics (CPU, I/O, queries), and analyze error codes. |
| **Reproduction**   | Recreate issues in a controlled environment (staging/Dev).                     | Use load generators (e.g., `JMeter`, `Locust`) or isolated test cases.                             |
| **Root Cause**     | Determine underlying cause (e.g., misconfiguration, hardware failure).      | Review dependencies (e.g., OS, network, storage), check database-specific tools (e.g., `pgBadger`, `MySQL Slow Query Log`). |
| **Resolution**     | Apply fixes (patches, optimizations, reconfiguration).                         | Validate changes via rollback tests; monitor post-resolution metrics.                              |
| **Prevention**     | Implement safeguards (alerts, backups, automation).                            | Configure monitoring (e.g., Prometheus, Datadog), enforce schema migrations via CI/CD pipelines.   |

---

### **2. Common Troubleshooting Categories**
#### **A. Connectivity Issues**
- **Symptoms**: Timeouts, "Connection refused," or "Host unreachable."
- **Root Causes**:
  - Firewall/network misconfigurations.
  - Service outages (e.g., RDS instance stopped).
  - Authentication failures (e.g., expired credentials).
- **Diagnostics**:
  ```bash
  # Test connectivity (replace `host:port`)
  telnet <db_host> <port>
  # Check listener status (PostgreSQL example)
  sudo -u postgres ps aux | grep postgres
  ```

#### **B. Performance Degradation**
- **Symptoms**: Slow queries, high latency, or prolonged locks.
- **Root Causes**:
  - Unoptimized queries (e.g., full table scans).
  - Insufficient resources (CPU, memory, or disk I/O).
  - Missing indexes or poor schema design.
- **Diagnostics**:
  - **Slow Query Logs** (MySQL):
    ```sql
    SET GLOBAL slow_query_log = 'ON';
    SET GLOBAL long_query_time = 1;
    ```
  - **EXPLAIN Plan** (PostgreSQL):
    ```sql
    EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;
    ```

#### **C. Schema & Data Corruption**
- **Symptoms**: Errors like "Table corrupted," "Foreign key constraint violated," or inconsistent data.
- **Root Causes**:
  - Improper `ALTER TABLE` operations.
  - Unexpected `DROP` or `TRUNCATE` commands.
  - Disk failures or improper shutdowns.
- **Diagnostics**:
  - **Check DB Integrity** (SQLite example):
    ```bash
    sqlite3 database.db ".database list" "PRAGMA integrity_check;"
    ```
  - **Validate Transactions** (PostgreSQL):
    ```sql
    SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';
    ```

#### **D. Replication Lag**
- **Symptoms**: Stale reads or delayed writes in replica databases.
- **Root Causes**:
  - Network bottlenecks.
  - High load on primary.
  - Binary log (`binlog`) corruption.
- **Diagnostics**:
  - **Replication Lag Check** (MySQL):
    ```sql
    SHOW SLAVE STATUS\G;
    ```
  - **Gap Detection** (PostgreSQL):
    ```sql
    SELECT pg_is_in_recovery(), pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
    ```

#### **E. Security Vulnerabilities**
- **Symptoms**: Unauthorized access, data leaks, or brute-force attacks.
- **Root Causes**:
  - Weak credentials or default passwords.
  - Missing encryption (e.g., SSL for connections).
  - Excessive permissions (e.g., `GRANT ALL` to users).
- **Diagnostics**:
  - **Audit Logs** (AWS RDS):
    ```bash
    # Parse CloudTrail logs for RDS events
    grep "rds:" /var/log/cloudtrail/*
    ```
  - **Permission Review** (PostgreSQL):
    ```sql
    SELECT usename, setconfig('role', 'default') FROM pg_user;
    ```

---

## **Schema Reference**
Below are essential tables and their roles in troubleshooting.

| **Table**               | **Purpose**                                                                 | **Key Columns**                                                                                     | **Example Queries**                                                                                     |
|-------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **`information_schema.tables`** | List all tables in the database.                                           | `TABLE_SCHEMA`, `TABLE_NAME`, `TABLE_TYPE`                                                      | `SELECT * FROM information_schema.tables WHERE TABLE_SCHEMA = 'public';`                                 |
| **`pg_stat_activity`**   | Track active connections and queries (PostgreSQL).                          | `pid`, `usename`, `query`, `state`                                                              | `SELECT query, state FROM pg_stat_activity WHERE state = 'active';`                                     |
| **`performance_schema.events_statements_summary_by_digest`** | Identify slow queries (MySQL). | `DIGEST_TEXT`, `COUNT_STAR`, `TOTAL_LATENCY`                                                  | `SELECT * FROM performance_schema.events_statements_summary_by_digest ORDER BY TOTAL_LATENCY DESC LIMIT 10;` |
| **`sys.dm_exec_query_stats`** | Query performance (SQL Server).         | `total_worker_time`, `logical_reads`, `rows`                                                      | `SELECT TOP 10 qs.total_worker_time, qs.logical_reads FROM sys.dm_exec_query_stats qs;`                |
| **`pg_stat_user_tables`** | Monitor table-level statistics (PostgreSQL).                              | `seq_scan`, `idx_scan`, `n_live_tup`                                                             | `SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;`             |

---

## **Query Examples**
### **1. Identify Long-Running Queries (PostgreSQL)**
```sql
SELECT
    pid,
    now() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC
LIMIT 10;
```

### **2. Check for Lock Contention (MySQL)**
```sql
SELECT
    request_id AS lock_request_id,
    resource_type,
    resource_id
FROM performance_schema.data_locks
WHERE event_lock_type = 'waiting';
```

### **3. Verify Replication Status (MongoDB)**
```javascript
db.replSetGetStatus()
```
**Output Key Metrics**:
- `members`: List of replicas.
- `optime`: Last committed operation time (should align across nodes).

### **4. Audit Failed Logins (SQL Server)**
```sql
SELECT
    login_time,
    application_name,
    nt_username,
    status
FROM sys.dm_exec_sessions
JOIN sys.dm_exec_connections ON session_id = session_id
WHERE is_user_process = 1 AND status = 'failed';
```

### **5. Detect Table Growth (Oracle)**
```sql
SELECT
    table_name,
    blocks,
    (blocks * block_size / 1024 / 1024) AS size_mb
FROM user_tables
ORDER BY size_mb DESC;
```

---

## **Tools & Utilities**
| **Tool**               | **Purpose**                                                                 | **Use Case**                                                                                     |
|------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **`pg_profiler`**       | Profile queries in PostgreSQL.                                             | Identify CPU/memory-heavy queries.                                                              |
| **`pt-query-digest`**  | Analyze MySQL slow logs.                                                   | Find repetitive or inefficient queries.                                                        |
| **`dbeaver`**          | Cross-database GUI for queries, schema inspection.                          | Visualize complex joins or missing indexes.                                                    |
| **`kubectl exec`**     | Debug databases in Kubernetes.                                              | Run ad-hoc commands inside a pod (e.g., `kubectl exec -it mongo-pod -- mongo --eval "db.stats()"`). |
| **`AWS RDS Performance Insights`** | Cloud-based monitoring for RDS. | Alert on anomalous CPU/network usage.                                                          |

---

## **Related Patterns**
1. **[Database Scaling]** – Vertical/horizontal scaling strategies (e.g., sharding, read replicas).
2. **[Backup & Recovery]** – Automated backup validation and point-in-time recovery (PITR).
3. **[Schema Migration]** – Zero-downtime migrations using tools like Flyway or Liquibase.
4. **[Security Hardening]** – Least-privilege access, encryption (TLS, at-rest), and audit trails.
5. **[Observability]** – Centralized logging (ELK stack) and metrics (Grafana + Prometheus).
6. **[Disaster Recovery]** – Multi-region replication and failover testing.
7. **[Cost Optimization]** – Right-sizing instances and queries (e.g., avoiding `SELECT *`).

---
## **Best Practices**
- **Log Everything**: Enable database-specific logs (e.g., `log_statement = 'all'` in PostgreSQL).
- **Isolate Issues**: Use staging environments to test fixes without affecting production.
- **Automate Alerts**: Set thresholds for critical metrics (e.g., replication lag > 30s).
- **Document Fixes**: Maintain a knowledge base for recurring issues (e.g., "Query X times out due to missing index Y").
- **Stay Updated**: Patch databases regularly (e.g., PostgreSQL updates include performance fixes).