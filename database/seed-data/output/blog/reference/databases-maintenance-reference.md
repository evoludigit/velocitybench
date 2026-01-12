# **[Pattern] Database Maintenance Reference Guide**

---

## **Overview**
Database maintenance ensures optimal performance, reliability, and security of database systems by systematically addressing routine tasks like indexing, backups, monitoring, and optimization. This pattern provides a structured approach to maintaining databases across different environments—production, staging, and development—while minimizing downtime and reducing risk. Key activities include **scheduling regular checks**, **applying patches**, **optimizing queries**, and **managing storage growth**. Proactive maintenance prevents degradation, improves scalability, and supports business continuity. Follow this guide to integrate maintenance best practices into your database lifecycle.

---

## **Key Concepts & Schema Reference**

### **1. Core Maintenance Activities**
| **Activity**               | **Description**                                                                                     | **Frequency**       | **Tools/Techniques**                          |
|----------------------------|-----------------------------------------------------------------------------------------------------|---------------------|-----------------------------------------------|
| **Backup & Restore**       | Creates snapshots of databases for disaster recovery and rollback.                                | Daily (prod), Weekly (dev/stage) |pg_dump, mysqldump, AWS RDS snapshots         |
| **Indexing**               | Optimizes query performance by maintaining/updating indexes.                                       | Monthly, post-major schema changes |EXPLAIN, dbms_stats, auto_indexing tools     |
| **Monitoring**             | Tracks resource usage, slow queries, and anomalies.                                               | Real-time + scheduled |Prometheus, New Relic, Oracle AWR, cloud-native metrics |
| **Patch Management**       | Applies vendor security patches and bug fixes.                                                    | Monthly (prod), immediately (critical) |Vendor alerts, automated patch tools (e.g., Red Hat Satellite) |
| **Fragmentation Cleanup**  | Defragments tables to improve read/write speeds.                                                   | Quarterly           |ALTER TABLE REORGANIZE (IBM DB2), dbcc (SQL Server) |
| **Storage Optimization**   | Removes unnecessary data via archiving/partitioning.                                               | Annually or as-needed |Partitioning (e.g., Oracle's ANALYZE TABLE), archival policies |
| **Security Audits**        | Validates permissions, encryption, and compliance (e.g., GDPR).                                    | Quarterly           |Oracle Security Assessment, PostgreSQL pgAudit |
| **Query Tuning**           | Identifies and optimizes slow-performing queries.                                                 | Ad-hoc + monthly reviews |EXPLAIN PLAN, query profiler tools            |
| **Replication Sync**       | Ensures consistency across read replicas and failover clusters.                                     | Hourly (sync checks) |AWS RDS replication lag, PostgreSQL pg_basebackup |

---

### **2. Maintenance Window Best Practices**
| **Environment**   | **Window Timing**               | **Priorities**                                                                                     |
|-------------------|----------------------------------|------------------------------------------------------------------------------------------------------|
| **Production**    | Low-traffic hours (e.g., 2–4 AM)| Minimal downtime; prioritize backups, critical patches, and monitoring setup.                      |
| **Staging**       | During off-peak development hours| Run E2E tests, validate patches, and simulate failovers.                                             |
| **Development**   | Flexible (e.g., nightly)        | Focus on schema changes, local tuning, and experiment with optimizations without impact risk.       |

---

## **Implementation Details**

### **1. Backup Strategy**
- **Full Backups**: Complete copies of the entire database (e.g., `pg_dump --format=custom` for PostgreSQL).
  ```bash
  pg_dump -U postgres -Fc -f /backups/prod_db_full_backup_$(date +%Y%m%d).dump database_name
  ```
- **Incremental Log Backups**: Capture transactions since the last full backup (e.g., PostgreSQL’s WAL archiving).
- **Cloud Backups**: Use vendor-native tools (e.g., AWS RDS automated backups, Azure SQL Elastic Jobs).
- **Retention Policy**: Store backups for **30 days (dev)**, **90 days (staging)**, and **1–3 years (prod)**.

### **2. Indexing**
- **Rule of Thumb**: Index columns frequently used in `WHERE`, `JOIN`, or `ORDER BY` clauses.
- **Auto-Indexing**: Enable database-specific features (e.g., PostgreSQL’s `autovacuum`).
  ```sql
  -- PostgreSQL: Create an index on 'created_at' for time-based queries
  CREATE INDEX idx_orders_created ON orders(created_at);
  ```
- **Monitor Index Usage**:
  ```sql
  -- PostgreSQL: Check unused indexes
  SELECT schemaname, tablename, indexname
  FROM pg_stat_user_indexes
  WHERE idx_scan = 0 AND n_live_tup > 0;
  ```

### **3. Monitoring & Alerts**
- **Critical Metrics to Track**:
  - Query latency (P99 > 1s).
  - Disk I/O saturation (>90%).
  - Deadlocks (>5/day).
  - Long-running transactions (e.g., via `pg_stat_activity` in PostgreSQL).
- **Alerting Tools**:
  - **Cloud**: AWS CloudWatch Alarms, Azure Monitor.
  - **Self-Hosted**: Prometheus + Grafana dashboards.
  - **Database-Specific**:
    ```sql
    -- Oracle: Check for long-running sessions
    SELECT * FROM v$session WHERE status = 'ACTIVE' AND seconds_in_wait > 300;
    ```

### **4. Patch Management**
- **Steps**:
  1. **Test Patches**: Apply to staging first (e.g., via Oracle’s `OPatch` or PostgreSQL’s `pg_upgrade`).
  2. **Rollback Plan**: Document steps to revert if issues arise (e.g., restore from backup).
  3. **Schedule**: Use zero-downtime upgrades where possible (e.g., AWS RDS blue/green deployments).
- **Example (PostgreSQL)**:
  ```bash
  # Downgrade PostgreSQL if needed
  sudo systemctl stop postgresql
  sudo pg_upgrade --old-bindir=/usr/lib/postgresql/previous_version/bin \
                  --new-bindir=/usr/lib/postgresql/current_version/bin \
                  --old-datadir=/var/lib/postgresql/old_data \
                  --new-datadir=/var/lib/postgresql/current_data
  ```

### **5. Query Optimization**
- **Common Issues**:
  - Full table scans (`Seq Scan` in PostgreSQL `EXPLAIN`).
  - Missing indexes (check `n_live_tup` vs. `idx_tup`).
  - N+1 query problems (e.g., ORMs fetching unrelated data).
- **Tools**:
  - **PostgreSQL**:
    ```sql
    EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
    ```
  - **SQL Server**: Use **SQL Server Management Studio (SSMS)**'s Execution Plan tool.

### **6. Storage Management**
- **Partitioning**: Split large tables by date ranges (e.g., `PARITION BY RANGE (created_at)` in PostgreSQL).
- **Archiving**: Move old data to cold storage (e.g., PostgreSQL’s `pg_partman` or Oracle’s `TTADMIN`).
  ```sql
  -- PostgreSQL: Create a partitioned table
  CREATE TABLE sales (
      id SERIAL,
      amount NUMERIC
  ) PARTITION BY RANGE (date_trunc('month', sale_date)) (
      PARTITION sales_2023 Q1 VALUES FROM (DATE '2023-01-01') TO (DATE '2023-04-01'),
      PARTITION sales_2024 Q2 VALUES FROM (DATE '2023-04-01') TO (DATE '2023-07-01')
  );
  ```

### **7. Security Audits**
- **Checklist**:
  - [ ] Audit user permissions (`GRANT`/`REVOKE` reviews).
  - [ ] Enable encryption (TDE for Oracle, `pgcrypto` for PostgreSQL).
  - [ ] Rotate credentials (e.g., `ALTER USER admin WITH PASSWORD 'new_password'`).
  - [ ] Scan for vulnerabilities (e.g., **OpenSCAP**, **Trivy**).
- **Example (PostgreSQL Audit)**:
  ```sql
  CREATE EXTENSION pgAudit;
  SELECT * FROM pgAudit.USERS;
  ```

---

## **Query Examples**

### **1. PostgreSQL: Check for Long-Running Transactions**
```sql
SELECT pid, now() - xact_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - xact_start > interval '5 minutes';
```

### **2. MySQL: Identify Large Tables**
```sql
SELECT table_name, data_length + index_length AS size_bytes
FROM information_schema.TABLES
WHERE table_schema = 'your_database'
ORDER BY size_bytes DESC
LIMIT 10;
```

### **3. Oracle: Monitor Blocking Sessions**
```sql
SELECT blocking_session, sid, serial#, username, machine
FROM v$session
WHERE blocking_session IS NOT NULL;
```

### **4. SQL Server: Find Missing Indexes**
```sql
-- Requires Query Store or DMVs
SELECT * FROM sys.dm_db_missing_index_details;
```

### **5. PostgreSQL: Vacuum Analyze (Cleanup & Stats Update)**
```sql
-- Run in maintenance window
VACUUM (VERBOSE, ANALYZE) users;
```

---

## **Related Patterns**
| **Pattern**                | **Description**                                                                 | **When to Use**                                  |
|----------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Database Sharding]**    | Splits data across multiple database instances for scalability.                | High write loads, global scale.                 |
| **[Caching Layer]**        | Reduces database load with in-memory caches (Redis, Memcached).              | Frequent read-heavy operations.                 |
| **[Blue-Green Deployment]**| Minimizes downtime during schema changes or upgrades.                          | Zero-downtime migrations.                       |
| **[Schema Migration]**     | Safely evolves database schemas over time.                                    | Feature rollouts requiring DB changes.          |
| **[Event Sourcing]**       | Stores state changes as a sequence of events instead of traditional tables.   | Audit trails, complex transaction log needs.    |
| **[Materialized Views]**   | Pre-computes query results for faster access.                                 | Reports, analytics with static data.            |

---

## **Troubleshooting**
| **Issue**                  | **Diagnosis**                                                                 | **Solution**                                      |
|-----------------------------|-------------------------------------------------------------------------------|---------------------------------------------------|
| **High CPU Usage**         | Check `pg_stat_activity` (PostgreSQL) for long queries or locks.            | Optimize queries; add indexes; increase `work_mem`. |
| **Disk Full**              | Monitor `df -h`; look for large tables in `information_schema`.             | Archive old data; add storage.                    |
| **Replication Lag**        | Use `pg_stat_replication` (PostgreSQL) or AWS RDS replication lag metrics.   | Increase replica capacity; filter logs.          |
| **Connection Leaks**       | Find open sessions in `v$session` (Oracle) or `pg_stat_activity`.         | Implement connection pooling (PgBouncer, ProxySQL).|
| **Slow Logins**            | Check authentication logs (`postgresql.log` for PostgreSQL).               | Tune `pg_hba.conf`; enable SSO.                   |

---

## **Templates for Maintenance Plans**
### **1. Weekly Checklist (Dev/Stage)**
- [ ] Run `VACUUM ANALYZE` on all tables.
- [ ] Test backups with `pg_restore` (PostgreSQL) or `mysqldump --test`.
- [ ] Review slow query logs.
- [ ] Update monitoring dashboards.

### **2. Monthly Checklist (Production)**
- [ ] Apply vendor security patches.
- [ ] Partition large tables (e.g., logs, transactions).
- [ ] Review user permissions for least privilege.
- [ ] Test failover scripts (for clusters).

---
**Note**: Customize frequencies based on your SLA, data volatility, and tooling. Automate repetitive tasks (e.g., backups, monitoring) using scripts (Bash, Python) or tools like **Liquibase**, **Flyway**, or **SQL Server Maintenance Plans**.