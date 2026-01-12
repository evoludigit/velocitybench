# **[Pattern] Databases Debugging: Reference Guide**

---

## **Overview**
Debugging databases involves identifying, isolating, and resolving performance bottlenecks, logical errors, or data inconsistencies in relational, NoSQL, or distributed database systems. This guide outlines systematic approaches to diagnosing issues, examining query execution plans, analyzing transaction logs, and optimizing database operations. Covered are key techniques such as indexing strategies, constraint validation, slow query analysis, and replication troubleshooting. Whether dealing with slow queries, deadlocks, or data corruption, this pattern provides structured methods to trace errors, validate assumptions, and restore operational integrity.

---

## **Schema Reference**
Below is a standardized schema for debugging environments, tools, and methodologies:

| **Category**               | **Component**                     | **Description**                                                                                                                                                                                                 |
|----------------------------|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Environment**            | Database Type                     | Type of database (e.g., PostgreSQL, MySQL, MongoDB, Firebase).                                                                                                                                                   |
|                            | Schema Diagram                    | Visual representation of tables, relationships, and constraints.                                                                                                                                                     |
|                            | Replication Status               | Primary/secondary nodes, lag status, and synchronization health.                                                                                                                                                  |
|                            | Log Locations                     | Paths to error logs, transaction logs, and application logs.                                                                                                                                                    |
| **Tools & Metrics**        | Query Profiler                    | Tools like `EXPLAIN ANALYZE` (SQL) or MongoDB’s `explain()` for query performance.                                                                                                                              |
|                            | Wait Event Analyzer               | Metrics on blocking operations (e.g., MySQL’s `SHOW PROCESSLIST`).                                                                                                                                                |
|                            | Lock Table                        | Current locks, active transactions, and deadlock graphs (if applicable).                                                                                                                                          |
| **Common Issues**          | Slow Query                        | Queries with high execution time or full table scans.                                                                                                                                                            |
|                            | Data Inconsistency                | Missing/duplicate records, orphaned references, or transaction aborts.                                                                                                                                            |
|                            | Replication Lag                   | Delay in data propagation between nodes.                                                                                                                                                                       |
|                            | Connection Issues                 | Timeout errors, connection leaks, or pool exhaustion.                                                                                                                                                             |
| **Debugging Steps**        | Step 1: Reproduce Issue           | Steps to recreate the problem (e.g., specific queries, workload).                                                                                                                                                   |
|                            | Step 2: Review Logs               | Parse error logs for patterns (e.g., deadlock timestamps, query timeouts).                                                                                                                                          |
|                            | Step 3: Analyze Execution Plan    | Inspect `EXPLAIN` output for cardinality estimates, join operations, or missing indexes.                                                                                                                       |
|                            | Step 4: Validate Constraints      | Check for foreign key violations, unique constraint breaches, or checksum mismatches.                                                                                                                         |
|                            | Step 5: Test Fixes                | Deploy patches incrementally and verify resolution via monitoring tools.                                                                                                                                          |

---

## **Query Examples**
### **1. Identifying Slow Queries**
**PostgreSQL:**
```sql
-- Find queries exceeding 1 second (adjust threshold as needed)
SELECT query, calls, total_time, mean_time, rows
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY mean_time DESC;
```

**MySQL:**
```sql
-- Top 5 slowest queries (requires `slow_query_log` enabled)
SELECT *
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM(TIMER_WAIT/1000000000) DESC
LIMIT 5;
```

---

### **2. Deadlock Detection**
**SQL Server:**
```sql
-- Detect active deadlocks
SELECT
    r.session_id AS deadlock_session_id,
    t.text AS deadlock_query
FROM sys.dm_tran_deadlock_list AS d
CROSS APPLY sys.dm_tran_locks AS l
CROSS APPLY sys.dm_os_tasks AS t
WHERE l.request_session_id = t.task_address
AND t.blocking_session_id > 0;
```

**MySQL:**
```sql
-- Check for blocking processes
SHOW PROCESSLIST WHERE State = 'Lock wait';
```

---

### **3. Check for Data Inconsistency**
**PostgreSQL (Row Count Check):**
```sql
-- Compare row counts across tables in a relationship
SELECT
    t1.name AS table1,
    (SELECT COUNT(*) FROM t1) AS count_table1,
    t2.name AS table2,
    (SELECT COUNT(*) FROM t2 WHERE fk_column IN (SELECT pk_column FROM t1)) AS count_table2
FROM information_schema.tables t1, information_schema.tables t2
WHERE t1.table_name = 'table1' AND t2.table_name = 'table2';
```

**MongoDB (Checksum Validation):**
```javascript
// Compare document counts and sample checksums
db.parentTable.count()
db.childTable.count({ parent_id: { $exists: true } });
db.childTable.aggregate([
    { $match: { parent_id: { $exists: true } } },
    { $group: { _id: null, checksum: { $md5: { $concatArrays: ["$parent_id", "$other_field"] } } } }
]);
```

---

### **4. Replication Lag Analysis**
**PostgreSQL (Logical Replication):**
```sql
-- Identify lagging slots
SELECT
    slot_name,
    pg_is_in_recovery() AS is_replica,
    pg_current_wal_lsn() - pg_last_wal_receive_lsn() AS lag_bytes
FROM pg_replication_slots;
```

**MySQL:**
```sql
-- Check replication status
SHOW SLAVE STATUS\G
-- Filter for lag (e.g., > 1 minute)
SELECT @@global.gtpid_slave_sql_thread @@global.gtpid_replica_lag AS lag_seconds;
```

---

## **Implementation Details**
### **Key Concepts**
1. **Execution Plan Analysis**:
   - Use `EXPLAIN` (SQL) or `explain()` (MongoDB) to visualize query steps. Look for:
     - Full table scans (`Seq Scan`).
     - Nested loops with high loop count.
     - Missing indexes (`Impossible Where`).
   - **Tool Tip**: PostgreSQL’s `pg_stat_statements` or MySQL’s `performance_schema`.

2. **Locking Strategies**:
   - **Read Locks**: Use `SELECT FOR SHARE` (PostgreSQL) for advisory locks.
   - **Write Locks**: Avoid long-running transactions; break them into smaller units.
   - **Deadlock Prevention**: Implement retry logic or timeouts for critical operations.

3. **Index Optimization**:
   - **Covering Indexes**: Include all columns in `SELECT` to avoid table access.
   - **Composite Indexes**: Order columns by selectivity (e.g., `WHERE` clauses first).
   - **Filter Indexes** (PostgreSQL): For large tables with frequent filtered queries.

4. **Transaction Isolation**:
   - Test with `READ UNCOMMITTED`, `READ COMMITTED`, etc., to identify dirty reads or phantom issues.
   - **PostgreSQL Example**:
     ```sql
     SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
     ```

5. **Distributed Debugging**:
   - **Consistency Checks**: Use distributed transaction logs (e.g., `pg_logical` for PostgreSQL).
   - **Latency Monitoring**: Track round-trip times between nodes (e.g., `pgBadger` for PostgreSQL).

---

### **Step-by-Step Debugging Workflow**
1. **Reproduce the Issue**:
   - Note: Time of day, user role, and affected data ranges.
   - Example: "Slowness occurs at 3 PM on `users.update()` for admin users."

2. **Isolate the Component**:
   - **Application**: Check app logs for failed connections or timeouts.
   - **Database**: Focus on query logs or replication status.

3. **Analyze Data**:
   - **Query Logs**: Filter by `query_time > threshold`.
   - **Replication Logs**: Look for lag spikes in `secondaries.log`.
   - **Checksums**: Compare aggregates (e.g., `SUM(column)`) across nodes.

4. **Test Hypotheses**:
   - **Hypothesis**: "Missing index on `users.last_login` causes full scans."
   - **Test**: Add the index and monitor query performance.

5. **Validate Fixes**:
   - Use A/B testing (e.g., deploy fix to a subset of replicas).
   - Monitor metrics post-deployment (e.g., `pg_stat_activity`).

---

## **Requirements Checklist**
| **Requirement**               | **Tool/Command**                          | **Example Output**                          |
|-------------------------------|-------------------------------------------|---------------------------------------------|
| Enable slow query logging     | MySQL: `slow_query_log = ON`              | `performance_schema.events_statements_summary` |
| Generate execution plans      | PostgreSQL: `EXPLAIN ANALYZE query`       | `Seq Scan on users  (cost=0.00..8.99 rows=1000)` |
| Check replication health      | PostgreSQL: `pg_is_in_recovery()`          | `false` (primary) / `true` (replica)       |
| Detect deadlocks              | SQL Server: `sys.dm_tran_deadlock_list`   | `Query: UPDATE accounts SET balance = ...`   |
| Compare row counts            | Custom script (e.g., Python + `sqlite3`) | `parent: 5000, child: 4980` (missing 20)    |

---

## **Related Patterns**
1. **[Database Optimization] Indexing Strategy**
   - *Focus*: Designing indexes for read/write patterns.
   - *Connection*: Debugging often reveals missing indexes (e.g., slow queries).

2. **[Distributed Transactions] Saga Pattern**
   - *Focus*: Handling ACID violations in microservices.
   - *Connection*: Useful for debugging replication lag or partial failures.

3. **[Monitoring] Database Metrics**
   - *Focus*: Proactively tracking CPU, memory, and query latency.
   - *Connection*: Debugging relies on historical metrics (e.g., `pg_stat_activity`).

4. **[Backup & Recovery] Point-in-Time Recovery**
   - *Focus*: Restoring databases to a known good state.
   - *Connection*: Critical for diagnosing data corruption post-incident.

5. **[Security] Query Injection Mitigation**
   - *Focus*: Preventing malicious SQL queries.
   - *Connection*: Debugging may uncover injection attempts via logs.

---
**Notes**:
- For **NoSQL databases**, replace SQL-specific tools with equivalents (e.g., MongoDB’s `explain()`).
- **Cloud databases** (e.g., AWS RDS) may require cloud-specific debug tools (e.g., CloudWatch logs).