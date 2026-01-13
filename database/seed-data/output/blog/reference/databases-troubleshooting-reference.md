# **[Pattern] Databases Troubleshooting Reference Guide**

---

## **Overview**
This reference guide provides structured methods to identify, diagnose, and resolve common database-related issues. It outlines a systematic troubleshooting approach, covering schema inconsistencies, performance bottlenecks, connectivity errors, and data integrity problems. The guide assumes familiarity with core database concepts (SQL, indexing, transactions) and is applicable to relational databases (e.g., PostgreSQL, MySQL, SQL Server) and NoSQL (e.g., MongoDB, Cassandra).

Key goals:
- **Minimize downtime** by pinpointing root causes efficiently.
- **Improve reliability** through proactive monitoring and validation.
- **Ensure maintainability** by documenting fixes and patterns.

---

## **Schema Reference**
Use this table to categorize troubleshooting scenarios based on root causes.

| **Category**               | **Subcategory**                     | **Common Symptoms**                                                                 | **Tools/Metrics**                                                                 |
|----------------------------|-------------------------------------|------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Connectivity**           | Network issues                      | Timeouts, "Cannot connect to server" errors, high latency                         | `ping`, `telnet`, `netstat`, network logs                                         |
|                            | Authentication errors               | Login failures, "Incorrect credentials"                                          | `sqlserver.log`, `auth.log`, user permissions audit                                 |
| **Performance**            | Slow queries                        | Long-running transactions, high CPU/memory usage                                   | `EXPLAIN ANALYZE`, `pg_stat_statements`, query profiling tools                    |
|                            | Table bloat                         | OOM errors, "Table too large" warnings                                             | `VACUUM` analytics, `table bloat` checks (PostgreSQL: `pg_size_pretty('tablename')`)|
| **Data Integrity**         | Corruption                          | Null/duplicate values in critical fields, transaction rollback failures             | `CHECKSUM`, `pg_checksums`, `PRAGMA integrity_check` (SQLite)                      |
|                            | Constraints violations              | Foreign key errors, unique constraint failures                                    | `pg_constraints`, `error logs`                                                    |
| **Schema Design**          | Schema drift                        | Schema inconsistencies between dev/prod, missing indexes                           | `schema diff` tools (e.g., ` schema_crawler`), `pg_catalog` metadata queries      |
|                            | Missing indexes                     | Full table scans, slow joins                                                        | `EXPLAIN` output, `analyze` queries                                               |
| **Backup/Restore**         | Failed backups                      | Partial/restored data, `pg_dump` errors                                            | `pg_basebackup` logs, `restore_verbose` flags                                     |
|                            | Restore corruption                  | Mismatched schema versions, data inconsistency                                   | `pg_restore --check` (PostgreSQL), `--verbose` flags                             |

---

## **Implementation Details**

### **1. Structured Troubleshooting Workflow**
Follow this step-by-step process to resolve issues systematically:

#### **Step 1: Reproduce the Issue**
- **For connectivity errors**:
  - Verify from the client machine: `telnet <host> <port>`. If fails, check firewall rules (`iptables`, `ufw`).
  - Test with a generic client (e.g., `mysql -u root -h localhost`).
- **For data issues**:
  - Validate data via a simple query: `SELECT COUNT(*) FROM users WHERE status = 'active';`.
- **For performance issues**:
  - Run a baseline query under normal load: `EXPLAIN ANALYZE SELECT * FROM orders WHERE date > '2023-01-01';`.

#### **Step 2: Gather Logs and Metrics**
- **Database logs**:
  - PostgreSQL: `/var/log/postgresql/postgresql-*.log`.
  - MySQL: `/var/log/mysql/error.log`.
  - Check for patterns (e.g., repeated errors, timestamp clusters).
- **System logs**:
  - OS-level logs (`dmesg`, `journalctl`) for disk I/O or memory issues.
- **Monitoring tools**:
  - Prometheus + Grafana for metrics (e.g., `db_connections`, `query_latency`).
  - `pg_stat_activity` (PostgreSQL) to identify long-running transactions:
    ```sql
    SELECT pid, usename, query, state, now() - query_start AS duration
    FROM pg_stat_activity
    WHERE state = 'active' ORDER BY duration DESC;
    ```

#### **Step 3: Narrow Down the Root Cause**
Use the **Schema Reference** table to identify the likely category. For example:
- **Slow queries**: Check `EXPLAIN` output for full scans or missing indexes.
- **Data corruption**: Run `VACUUM FULL ANALYZE` (PostgreSQL) or `pg_checksums` to validate integrity.
- **Schema drift**: Compare schemas with a tool like [Sqitch](https://sqitch.org/) or `pg_dump --schema-only`.

#### **Step 4: Apply Fixes**
| **Issue**               | **Action Items**                                                                                     | **Verification**                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| Missing index           | Create index: `CREATE INDEX idx_orders_date ON orders(date);`                                     | Re-run `EXPLAIN`; check query speed improvement.                                     |
| Corrupted table         | Rebuild: `REINDEX TABLE users;`                                                                   | Verify data consistency with `SELECT COUNT(*) FROM users;`                             |
| Failed backup           | Restore from secondary node or recovery point.                                                    | Test restore: `pg_restore --clean --verbose dump.sql` (PostgreSQL)                   |
| Connection leaks        | Fix app code to close connections; set `max_connections` appropriately.                           | Monitor `pg_stat_database` for `num_backend_xact` spikes.                           |
| Schema drift            | Apply missing migrations (e.g., `sqitch deploy`).                                                 | Run schema comparison tool (e.g., `pg_schema_diff`).                                  |

#### **Step 5: Prevent Recurrence**
- **Automate monitoring**:
  - Set up alerts for `pg_stat_database` metrics (e.g., high `cached_bytes` or `blks_read`).
- **Implement schema versioning**:
  - Use tools like [Flyway](https://flywaydb.org/) or [Liquibase](https://liquibase.org/) for migrations.
- **Regular maintenance**:
  - Schedule `VACUUM` (PostgreSQL) or `OPTIMIZE TABLE` (MySQL) jobs.
  - Archive old data to reduce table bloat.

---

## **Query Examples**

### **1. Identify Slow Queries**
**PostgreSQL**:
```sql
-- Top 10 slowest queries by execution time
SELECT
    query,
    total_time,
    calls,
    mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**MySQL**:
```sql
-- Slow query log analysis (enable in my.cnf: slow_query_log = 1)
SELECT
    sql_text,
    count(*) AS query_count,
    avg_timer_wait AS avg_duration_ms
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_duration_ms DESC
LIMIT 10;
```

### **2. Check for Long-Running Transactions**
```sql
-- PostgreSQL: Find transactions blocking others
SELECT
    blocking_pid AS blocked_pid,
    pid AS blocker_pid,
    now() - query_start AS duration
FROM pg_stat_activity
WHERE state = 'active'
AND blocked_by IS NOT NULL;
```

### **3. Validate Data Integrity**
```sql
-- PostgreSQL: Check for orphaned foreign key references
SELECT
    tc.conname,
    tc.reltable AS table_name,
    tc.table_name,
    tc.relname AS constraint_name
FROM pg_catalog.pg_constraint tc
         JOIN pg_catalog.pg_namespace n ON n.oid = tc.connamespace
WHERE tc.contype = 'f'
  AND n.nspname = 'public'
  AND NOT EXISTS (
    SELECT 1
    FROM tc.constraint_relnames
    WHERE tc.conname = constraint_relnames
  );
```

### **4. Diagnose Table Bloat**
```sql
-- PostgreSQL: Identify bloated tables
SELECT
    schemaname,
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(C.oid)) AS total_size,
    pg_size_pretty(pg_relation_size(C.oid)) AS live_size,
    (pg_total_relation_size(C.oid) - pg_relation_size(C.oid)) AS dead_size,
    (pg_total_relation_size(C.oid) - pg_relation_size(C.oid)) * 100.0 / NULLIF(pg_total_relation_size(C.oid), 0) AS bloat_pct
FROM pg_class C
         LEFT JOIN pg_namespace N ON (C.relnamespace = N.oid)
WHERE nspname NOT IN ('pg_catalog', 'information_schema')
  AND C.relkind = 'r'
  AND pg_total_relation_size(C.oid) > 1024*1024 -- >1MB
ORDER BY bloat_pct DESC;
```

### **5. Analyze Index Usage**
```sql
-- PostgreSQL: Find unused indexes
SELECT
    schemaname,
    relname AS table_name,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
  AND idx_scan = 0
ORDER BY schemaname, relname;
```

---

## **Related Patterns**
1. **[Database Performance Optimization]**
   - Complementary to troubleshooting; focuses on proactive tuning (e.g., partitioning, caching).
   - *Key overlap*: Both use `EXPLAIN` and `pg_stat_statements` for analysis.

2. **[Schema Migration Strategies]**
   - Prevents schema drift by standardizing migration workflows.
   - *Key overlap*: Schema comparison tools (e.g., `pg_schema_diff`) are used in both.

3. **[Distributed Transaction Management]**
   - Addresses issues in distributed systems (e.g., 2PC, Saga patterns).
   - *Key overlap*: Troubleshooting transaction rollbacks and deadlocks.

4. **[Data Pipeline Monitoring]**
   - Detects issues in ETL jobs feeding databases.
   - *Key overlap*: Log analysis and alerting for data accuracy problems.

5. **[Disaster Recovery Planning]**
   - Ensures databases are resilient to failures.
   - *Key overlap*: Backup/restore troubleshooting (e.g., failed `pg_basebackup`).

---
## **Further Reading**
- [PostgreSQL Troubleshooting Guide](https://www.postgresql.org/docs/current/troubleshooting.html)
- [MySQL Performance Blog](https://www.percona.com/blog/)
- [SQL Server Best Practices](https://docs.microsoft.com/en-us/sql/relational-databases/system-catalog-views/system-statistics-catalog-views-transact-sql?view=sql-server-ver16)