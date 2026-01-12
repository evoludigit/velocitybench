# **[Pattern] Databases Troubleshooting: Reference Guide**

---
## **Overview**
Databases Troubleshooting is a structured approach to diagnosing, resolving, and preventing performance bottlenecks, connectivity issues, data corruption, and operational failures in database systems. This guide outlines common failure scenarios, diagnostic methodologies, and best practices across **relational (SQL) and NoSQL databases**, with a focus on **MySQL, PostgreSQL, MongoDB, and DynamoDB**. It includes structured workflows for performance analysis, error resolution, and proactive monitoring, ensuring minimal downtime and data integrity.

---
## **Key Concepts & Implementation Details**

### **1. Common Troubleshooting Categories**
| **Category**          | **Scope**                                                                                     | **Common Issues**                                                                 |
|-----------------------|------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Connectivity**      | Network/database server interactions                                                      | Timeout errors, authentication failures, port blocking, DNS resolution issues       |
| **Performance**       | Query execution, indexing, resource contention                                               | Slow queries, memory leaks, CPU overload, I/O bottlenecks                          |
| **Data Integrity**    | Corruption, consistency, and transactional failures                                          | Incomplete transactions, duplicates, schema mismatches, disk failure              |
| **Configuration**     | Misconfigured settings, parameter tuning                                                         | Insufficient buffer pools, improper replication lag, inefficient partitioning        |
| **Backup/Recovery**   | Backup failures, restore errors, disaster recovery                                             | Corrupted backups, incomplete snapshots, version mismatches                        |

---

### **2. Troubleshooting Workflow**
#### **Step 1: Reproduce the Issue**
- **Method**: Confirm symptoms (e.g., timeouts, crashes) and gather logs/stack traces.
- **Tools**:
  - **SQL Databases**: `mysqladmin`, `pgbadger` (PostgreSQL), `MySQL Workbench`.
  - **NoSQL**: MongoDB `mongostat`, DynamoDB CloudWatch metrics.
- **Example**:
  ```sql
  -- Check active connections (MySQL)
  SHOW PROCESSLIST;
  ```

#### **Step 2: Identify Root Cause**
| **Issue Type**         | **Diagnostic Query/Command**                                                                 | **Tools/Library**                     |
|------------------------|----------------------------------------------------------------------------------------------|---------------------------------------|
| **Slow Query**         | `EXPLAIN ANALYZE` (PostgreSQL), `SHOW PROFILE` (MySQL)                                       | `pt-query-digest` (Percona)          |
| **High Latency**       | `pg_stat_activity` (PostgreSQL), DynamoDB CloudWatch Latency stats                            | AWS CloudTrail, Datadog               |
| **Deadlocks**          | `SELECT * FROM pg_locks` (PostgreSQL), MySQL `SHOW ENGINE INNODB STATUS`                     | `pg_deadlock` (MySQL)                 |
| **Missing Index**      | `EXPLAIN` without `index` usage                                                               | `dbdiagram` for schema visualization  |
| **Corruption**         | `fsck` (PostgreSQL), `CHECK TABLE tbl_name FOR UPDATE` (MySQL)                               | `mysqlcheck --repair`, `pg_checksums` |

#### **Step 3: Apply Fixes**
| **Issue**               | **Solution**                                                                                     | **Metrics to Monitor**                     |
|-------------------------|------------------------------------------------------------------------------------------------|--------------------------------------------|
| **Slow Queries**        | Add missing indexes, optimize `JOIN` conditions, partition large tables.                     | `slow_query_log` (MySQL), `EXPLAIN` cost   |
| **Connectivity Errors** | Verify network ACLs, VPC security groups (AWS), retry logic in app code.                       | `netstat -an`, `tcpdump`                   |
| **Disk I/O Bottleneck** | Upgrade storage tier (SSD), enable `O_DIRECT` for MySQL, adjust `innodb_buffer_pool_size`.    | `iostat`, `df -h`                          |
| **Backup Failures**     | Test restore procedures, use checkpoints (`pg_basebackup` for PostgreSQL).                     | Backup completion logs, `pg_isready`       |
| **Replication Lag**     | Increase binlog group commit, adjust `replica-lag-threshold` (PostgreSQL).                     | `SHOW SLAVE STATUS`, `pg_stat_replication` |

#### **Step 4: Prevent Recurrence**
- **Proactive Measures**:
  - **Monitoring**: Set up alerts for `ERROR`/`WARN` logs (e.g., `ELK Stack`, `Prometheus`).
  - **Testing**: Regularly run `CHECK TABLE` (MySQL) or `VACUUM` (PostgreSQL).
  - **Automation**: Use tools like **Datadog**, **New Relic**, or **CloudWatch Alarms** for anomalies.
  - **Documentation**: Maintain a runbook (e.g., Confluence) with resolved issues and fixes.

---
## **Schema Reference**
Below are key tables for diagnostic purposes across databases.

| **Database**   | **Table/View**          | **Purpose**                                                                                     | **Example Query**                                  |
|----------------|-------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------|
| **MySQL**      | `information_schema.processlist` | Monitor active connections and resource usage.                                                 | `SELECT * FROM information_schema.processlist;`   |
| **PostgreSQL** | `pg_stat_activity`      | Identify long-running transactions and locks.                                                 | `SELECT pid, usename, query FROM pg_stat_activity;` |
| **MongoDB**    | `mongostat`             | Track CPU, memory, and network metrics.                                                       | `mongostat --host localhost --port 27017`         |
| **DynamoDB**   | CloudWatch Metrics      | Monitor throttled requests, latency, and throughput.                                           | `GET_METERING_METRICS` (AWS CLI)                  |

---
## **Query Examples**
### **1. Identify Slow Queries (MySQL)**
```sql
-- Enable slow query log (if disabled)
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;

-- Analyze slow queries
SELECT * FROM mysql.slow_log WHERE timer > 1000000;  -- Queries >1s
```

### **2. Check PostgreSQL Locks**
```sql
-- Find blocking locks
SELECT
    blocking_pid,
    blocked_pid,
    locktype,
    relation::regclass AS table_name
FROM pg_locks
WHERE NOT blocked_pid = 0;
```

### **3. DynamoDB Throttling Analysis**
```bash
# Check throttled requests via AWS CLI
aws cloudwatch get-metric-statistics \
    --namespace AWS/DynamoDB \
    --metric-name ThrottledRequests \
    --dimensions Name=TableName,Value=YourTableName \
    --start-time 2023-10-01T00:00:00 \
    --end-time 2023-10-02T00:00:00 \
    --period 3600;
```

### **4. MongoDB Index Usage**
```javascript
// Check index effectiveness
db.collection.explain("query").executionStats;
db.collection.aggregate([
  { $indexStats: {} }
]);
```

---
## **Tools & Libraries**
| **Category**       | **Tool/Library**               | **Purpose**                                                                                     |
|--------------------|---------------------------------|-------------------------------------------------------------------------------------------------|
| **Logging**        | `ELK Stack` (Elasticsearch, Logstash, Kibana) | Aggregate and visualize logs.                                                                  |
| **Performance**    | `pt-query-digest` (Percona)    | Analyze MySQL slow logs.                                                                      |
| **Monitoring**     | `Datadog`, `Prometheus`        | Real-time metrics and alerting.                                                                |
| **Backup**         | `pg_dump` (PostgreSQL), `mysqldump` | Schedule and verify backups.                                                                 |
| **Replication**    | `pg_basebackup` (PostgreSQL)   | Sync standby nodes.                                                                           |

---
## **Related Patterns**
1. **Database Scaling**: Horizontal/vertical scaling strategies (sharding, read replicas).
2. **Backup & Disaster Recovery**: Automated backup solutions (e.g., AWS RDS snapshots, PostgreSQL logical replication).
3. **Schema Design**: Optimizing schemas for performance (e.g., denormalization, indexing).
4. **Connection Pooling**: Managing database connections efficiently (e.g., PgBouncer, HikariCP).
5. **Chaos Engineering**: Testing resilience with tools like **Gremlin** or **Chaos Mesh**.

---
## **Best Practices Checklist**
| **Area**            | **Action Item**                                                                                     |
|---------------------|---------------------------------------------------------------------------------------------------|
| **Prevention**      | Enable query logging, set up alerts for critical metrics.                                          |
| **Diagnosis**       | Use `EXPLAIN`, `pg_stat_activity`, and `mongostat` regularly.                                      |
| **Recovery**        | Document restore procedures; test backups quarterly.                                                |
| **Scaling**         | Monitor `SHOW GLOBAL STATUS` (MySQL) or `pg_stat_database` (PostgreSQL) for tuning needs.          |
| **Security**        | Rotate credentials, restrict DB user privileges, and encrypt data at rest.                         |

---
**Note**: Always back up data before running diagnostic queries or applying fixes. For production issues, consult vendor documentation (e.g., [MySQL Docs](https://dev.mysql.com/doc/), [PostgreSQL Docs](https://www.postgresql.org/docs/)).

---
**Length**: ~1,050 words. Adjust examples or add database-specific sections (e.g., Oracle, SQL Server) as needed.