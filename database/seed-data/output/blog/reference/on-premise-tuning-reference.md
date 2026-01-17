# **[Pattern] On-Premise Tuning Reference Guide**

---

## **1. Overview**
Optimizing database performance on-premise requires systematic tuning of hardware, configuration, and query execution. This pattern ensures efficient resource utilization, minimizes latency, and maximizes throughput for applications running in a controlled, private environment (e.g., data centers, VMs, or bare-metal servers). Key focus areas include:
- **Hardware optimization** (CPU, memory, storage) to match workload demands.
- **Database configuration tuning** (query optimizer, memory settings, caching).
- **Indexing, partitioning, and query refinement** to reduce execution time.
- **Monitoring and profiling** to identify bottlenecks.

This guide provides actionable steps to implement and validate tuning adjustments in an on-premise setup.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Hardware Requirements**
Tuning starts with aligning hardware resources to workload characteristics. Refer to the following table for baseline recommendations:

| **Resource**       | **Recommendation**                                                                                     | **Tuning Levers**                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **CPU**            | Match core count to parallelizable workloads (e.g., 40+ cores for high-concurrency OLTP).            | Adjust `work_mem`, `max_parallel_workers`, `max_worker_per_node`.                                  |
| **RAM**            | Allocate ~70–80% of available memory to the database (`shared_buffers`, `effective_cache_size`).     | Increase `shared_buffers` incrementally (10% of RAM as a maximum).                                   |
| **Storage**        | Use SSDs for I/O-bound workloads; prioritize local NVMe for low-latency.                              | Enable `random_page_cost` tuning for disk types; partition tables by access patterns.               |
| **Network**        | Ensure 10Gbps+ connectivity for high-throughput replication or distributed queries.                   | Monitor network saturation with `pg_stat_ssl` (PostgreSQL) or `sys.dm_exec_connections`.            |

---

### **2.2 Database Configuration Tuning**
Configure database settings to balance memory, I/O, and concurrency. Use `postgresql.conf` (PostgreSQL) or equivalent for your system.

| **Parameter**              | **Purpose**                                                                                       | **Default Tuning Values**                                                                         |
|----------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| `shared_buffers`           | Cache frequently accessed data blocks.                                                           | 4GB–16GB (10% of RAM max).                                                                      |
| `work_mem`                 | Limit per-query memory usage (critical for sorts/joins).                                           | 4MB–64MB (adjust based on query complexity).                                                     |
| `maintenance_work_mem`     | Control VACUUM/ANALYZE memory allocation.                                                         | 16MB–512MB (scale with WAL archiving).                                                             |
| `effective_cache_size`    | Simulate client-side cache for query planner.                                                    | 80% of total RAM.                                                                                 |
| `max_parallel_workers`     | Enable parallel query execution (PostgreSQL).                                                    | `0.5 × (CPU cores)` (e.g., 20 for a 40-core server).                                              |
| `random_page_cost`         | Adjust for SSD vs. HDD latency (lower values for SSDs).                                           | 1.1–4.0 (SSD: ~1.1; HDD: ~4.0).                                                                  |
| `wal_buffers`              | Buffer WAL writes for throughput (reduce disk I/O spikes).                                        | `-1` (auto) or `16MB`–`128MB` (reduce if WAL writes bottleneck).                                 |

**Validation:**
After tuning, verify changes with:
```sql
-- PostgreSQL: Check active settings
SELECT name, setting, unit, short_desc FROM pg_settings WHERE name IN ('shared_buffers', 'work_mem');
```

---

### **2.3 Indexing & Query Optimization**
**Indexing Strategy:**
- **B-tree indexes**: Default for equality/range scans (OLTP).
- **GiST/SP-GiST**: For complex data types (e.g., JSON, geospatial).
- **Hash indexes**: Limited to PostgreSQL 13+; use for exact-match lookups.
- **Partial indexes**: Filter indexes by conditions (e.g., `WHERE is_active = true`).

**Query Tuning:**
- **EXPLAIN ANALYZE**: Profile queries to identify bottlenecks.
  Example:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 12345;
  ```
- **Avoid `SELECT *`**: Fetch only required columns.
- **Use `LIMIT`**: Restrict result sets for debugging.
- **Denormalize judiciously**: Reduce joins but monitor storage growth.

**Partitioning:**
Partition large tables by time, range, or list:
```sql
CREATE TABLE sales (
  id SERIAL,
  sale_date DATE,
  amount DECIMAL
) PARTITION BY RANGE (sale_date);

-- Create monthly partitions
CREATE TABLE sales_y2023m01 PARTITION OF sales
  FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');
```

---

### **2.4 Monitoring & Profiling**
Track performance metrics to validate tuning:
- **Database-specific tools**:
  - PostgreSQL: `pg_stat_statements`, `pgBadger`.
  - MySQL: `Performance Schema`, `Slow Query Log`.
  - SQL Server: `DMVs` (`sys.dm_exec_query_stats`).
- **System-level tools**:
  - `top`/`htop` (Linux) for CPU/RAM.
  - `iostat` for disk I/O.
  - `netstat` for network latency.

**Alert Thresholds:**
| **Metric**               | **Warning Threshold**               | **Critical Threshold**              |
|--------------------------|-------------------------------------|--------------------------------------|
| CPU usage                | >80% for 5+ minutes                 | >95% sustained                         |
| Disk I/O latency         | >20ms (SSD) / >100ms (HDD)          | >50ms (SSD) / >500ms (HDD)            |
| Connection queue length  | >100                                | >500                                  |
| Query duration           | >3 seconds (OLTP) / >10 seconds (OLAP)| >60 seconds                           |

---

## **3. Schema Reference**
### **Database Configuration Schema**
| **Table**          | **Description**                                                                                     | **Key Fields**                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| `pg_settings`      | PostgreSQL runtime parameters (active/inherited).                                                 | `name`, `setting`, `unit`, `short_desc`.                                                          |
| `sys.dm_os_performance_counters` (SQL Server) | OS-level performance metrics (CPU, memory, disk).               | `object_name`, `counter_name`, `instances`, `cntr_value`.                                         |
| `information_schema.views` | User-created views with potential query bottlenecks.          | `table_name`, `view_definition`, `check_option`.                                                   |

**Example Query:**
```sql
-- List all settings with manual modification
SELECT name, setting, unit
FROM pg_settings
WHERE context = 'user' AND modified IS NOT NULL;
```

---

## **4. Query Examples**

### **4.1 Benchmarking Query Performance**
```sql
-- Compare indexed vs. non-indexed query (PostgreSQL)
EXPLAIN ANALYZE
SELECT * FROM users WHERE email = 'test@example.com';
-- vs.
EXPLAIN ANALYZE
SELECT * FROM users USING index ON users(email) WHERE email = 'test@example.com';
```

### **4.2 Identifying Long-Running Transactions**
```sql
-- PostgreSQL: Find blocked transactions
SELECT pid, query, now() - query_start AS duration
FROM pg_stat_activity
WHERE state = 'active' AND query NOT LIKE '%pg_stat_%'
ORDER BY duration DESC
LIMIT 10;

-- SQL Server: Blocking sessions
SELECT
  s.session_id,
  s.login_name,
  s.blocking_session_id,
  t.text AS blocking_query
FROM sys.dm_exec_sessions s
CROSS APPLY sys.dm_exec_sql_text(s.sql_handle) t
WHERE s.is_user_process = 1 AND s.blocking_session_id IS NOT NULL;
```

### **4.3 Dynamic Configuration Adjustment**
```sql
-- PostgreSQL: Adjust work_mem for a session (temporary)
SET work_mem = '64MB';
-- Verify change
SHOW work_mem;
```

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **[Sharding]**                   | Split database horizontally to reduce query load.                                                   | High-scale OLTP systems with global read/write patterns.                                            |
| **[Caching Layer]**              | Offload frequent queries to Redis/Memcached.                                                       | Read-heavy applications with repetitive queries.                                                    |
| **[Connection Pooling]**        | Reuse database connections to reduce overhead.                                                     | Web apps with high client-to-server ratio.                                                          |
| **[Materialized Views]**         | Pre-compute aggregations for analytical queries.                                                   | OLAP workloads with static or slow-changing data.                                                   |
| **[Replication]**                | Distribute read queries across replicas for scalability.                                            | High-read-low-write workloads (e.g., reporting).                                                    |

---

## **6. Validation Checklist**
Use this to confirm tuning effectiveness:
1. **[ ]** CPU utilization < 70% under peak load.
2. **[ ]** Disk I/O latency < 20ms (SSD) for 95th percentile.
3. **[ ]** Top 10 queries account for < 50% of total execution time.
4. **[ ]** Memory usage stable (no excessive `shared_buffers` swaps).
5. **[ ]** Connection queue length < 50 for sustained workloads.
6. **[ ]** Index usage > 90% for critical queries (use `pg_stat_user_indexes`).

---
**Note:** Document changes in a version-controlled `tuning_config.txt` for rollback capability. Adjust incrementally and validate post-change.