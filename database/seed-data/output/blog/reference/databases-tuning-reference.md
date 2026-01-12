# **[Pattern] Database Tuning Reference Guide**

---

## **1. Overview**
Database tuning optimizes query performance, resource allocation, and system responsiveness to reduce latency, minimize resource contention, and scale efficiently. This guide covers tuning techniques for relational (SQL) databases, with considerations for NoSQL systems. Key areas include indexing, query optimization, hardware allocation, and configuration adjustments tailored to workloads (OLTP, OLAP, mixed).

---

## **2. Schema & Implementation Schema Reference**

| **Category**               | **Component**               | **Description**                                                                 | **Key Metrics/Parameters**                     |
|----------------------------|-----------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **Database Engines**       | PostgreSQL/MySQL/Redis      | Relational/NoSQL databases.                                                   | Version, concurrency, memory usage            |
| **Indexing Strategy**      | B-Tree, Hash, GIN           | Index types for faster lookups; avoid over-indexing.                          | Index size, query speedup, write overhead       |
| **Query Optimization**     | Execution Plans              | Analyze and rewrite queries for efficiency (e.g., `EXPLAIN`, `ANALYZE`).       | Cost, rows examined, sorting/joins              |
| **Hardware & Storage**     | SSDs, RAID, Memory          | Use high-speed storage; allocate RAM for buffers/cache.                        | IOPS, latency, cache hit ratio                 |
| **Connection Pooling**     | PgBouncer, HikariCP         | Manage database connections to avoid bottlenecks.                              | Pool size, idle connections, connection time  |
| **Configuration Tuning**  | `postgresql.conf`, `my.cnf` | Adjust `work_mem`, `shared_buffers`, `innodb_buffer_pool_size`.                | Buffer hit rate, memory usage                  |
| **Partitioning**           | Horizontal Vertical         | Split large tables by range/hash/distribution.                                 | Query speed, partition count                   |
| **Caching**                | Redis, Memcached            | Offload read-heavy workloads to in-memory stores.                              | Latency, cache hit ratio                      |
| **Workflow Orchestration** | Celery, Apache Airflow      | Schedule batch jobs to avoid peak loads.                                       | Job duration, resource contention              |
| **Monitoring Tools**       | Prometheus, Datadog, pgBadger| Track performance metrics for proactive tuning.                               | Query slowlogs, CPU/memory usage                |

---

## **3. Key Implementation Details**

### **3.1 Indexing Strategies**
- **When to Index**: Index columns frequently used in `WHERE`, `JOIN`, or `ORDER BY` clauses.
- **Index Types**:
  - **B-Tree**: Default for ordered data (e.g., `INT`, `VARCHAR`).
  - **Hash**: For equality checks (`=` only); avoids sorting overhead.
  - **GIN/SGiST**: Full-text search, JSON, or geospatial data.
- **Avoid Over-Indexing**: Each index increases write latency and storage usage.
- **Composite Indexes**: Combine columns in `WHERE` clauses (e.g., `(user_id, timestamp)`).

**Example Schema**:
```sql
CREATE INDEX idx_user_activity_date ON user_activity (user_id, timestamp);
```

---

### **3.2 Query Optimization**
- **Analyze Query Plans**:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM orders WHERE status = 'shipped';
  ```
- **Common Pitfalls**:
  - **N+1 Queries**: Optimize with JOINs or batch fetches.
  - **Selective Columns**: Avoid `SELECT *`; fetch only needed columns.
  - **Lack of Indexes**: Add indexes for `WHERE`/`ORDER BY` clauses.
- **Rewrite Slow Queries**:
  ```sql
  -- Before (inefficient)
  SELECT * FROM products WHERE category IN (SELECT id FROM categories WHERE active = true);

  -- After (use JOIN)
  SELECT p.*
  FROM products p
  JOIN categories c ON p.category_id = c.id
  WHERE c.active = true;
  ```

---

### **3.3 Hardware & Storage Tuning**
| **Parameter**               | **Recommendation**                                                                 | **Tools**                     |
|-----------------------------|------------------------------------------------------------------------------------|-------------------------------|
| **Storage**                 | Use NVMe SSDs for I/O-bound workloads; RAID 10 for redundancy.                   | `fdisk`, `iostat`             |
| **Memory (RAM)**            | Allocate 20–30% of RAM to `shared_buffers` (PostgreSQL) or buffer pool (MySQL).   | `free -h`, `vmstat`           |
| **CPU Cores**               | Dedicated cores for database processes; avoid shared-hosting for critical DBs.   | `top`, `htop`                 |
| **Network Latency**         | Use low-latency connections (e.g., `keepalives`, compression).                  | `ping`, `netstat`             |

---

### **3.4 Connection Pooling**
- **Why Pool?**: Reduces connection overhead; avoids "too many connections" errors.
- **Tools**:
  - **PostgreSQL**: `pgBouncer` (session pooling).
  - **Java**: HikariCP (connection reuse).
- **Configuration**:
  ```ini
  # pgBouncer config (pool_size = 50)
  pool_mode = transaction
  max_client_conn = 200
  ```
- **Monitor**: Track `max_connections` vs. active connections.

---

### **3.5 Configuration Tuning**
| **Database** | **Parameter**               | **Default** | **Recommended Tuning**                     | **Impact**                          |
|--------------|-----------------------------|-------------|--------------------------------------------|-------------------------------------|
| PostgreSQL   | `shared_buffers`            | 128MB       | 25–50% of RAM (e.g., 8GB for 16GB RAM)     | Reduces disk reads                  |
| PostgreSQL   | `work_mem`                  | 4MB         | 16–64MB for complex queries                | Improves sorting/joins              |
| MySQL        | `innodb_buffer_pool_size`   | 128MB       | 70% of available RAM                       | Caches indexes/data in memory       |
| MySQL        | `innodb_log_file_size`      | 5MB         | 25–100% of RAM (for high write loads)      | Reduces crash recovery time         |

**Example (PostgreSQL `postgresql.conf`)**:
```conf
shared_buffers = 4GB
effective_cache_size = 12GB
work_mem = 32MB
maintenance_work_mem = 2GB
```

---

### **3.6 Partitioning**
- **Horizontal Partitioning**: Split by range (e.g., `date` columns).
  ```sql
  CREATE TABLE sales (
      id SERIAL,
      sale_date DATE,
      amount DECIMAL
  ) PARTITION BY RANGE (sale_date);
  ```
- **Vertical Partitioning**: Separate frequently accessed columns into smaller tables.
- **Benefits**:
  - Faster queries on partitioned data.
  - Easier maintenance (e.g., drop old partitions).

---

### **3.7 Caching Layers**
- **In-Memory Caches**: Use Redis/Memcached for:
  - Session storage.
  - Repeated read-heavy queries.
  - Rate-limiting and analytics.
- **Example (Redis for Query Caching)**:
  ```python
  import redis
  r = redis.Redis()
  query_result = r.get("popular_products:2023")
  if not query_result:
      query_result = db.execute("SELECT * FROM products WHERE popular = true")
      r.setex("popular_products:2023", 3600, query_result)
  ```

---

### **3.8 Monitoring & Logging**
| **Tool**       | **Purpose**                          | **Key Metrics**                          |
|----------------|---------------------------------------|------------------------------------------|
| `pg_stat_statements` (PostgreSQL) | Track slow queries.                | `query`, `rows`, `shared_blks_read`      |
| `mysqld --slow-query-log` (MySQL) | Log queries > threshold (e.g., 2s).  | `Query_time`, `Rows_examined`           |
| Prometheus + Grafana | Visualize metrics (CPU, disk, queries). | Latency, throughput, error rates         |
| `EXPLAIN`      | Analyze query execution plans.        | `Seq Scan` vs. `Index Scan`              |

**Example Slow Query Log Filter (MySQL)**:
```ini
[mysqld]
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
```

---

## **4. Query Examples**

### **4.1 Optimized Index Usage**
**Before (No Index)**:
```sql
-- Slow: Full table scan on large table
SELECT * FROM users WHERE country = 'US';
```
**After (Add Index)**:
```sql
CREATE INDEX idx_country ON users (country);
-- Now uses index
```

---

### **4.2 Efficient JOINs**
**Before (Nested Loop)**:
```sql
-- Inefficient: Correlated subquery
SELECT o.* FROM orders o
WHERE o.user_id IN (SELECT id FROM users WHERE status = 'active');
```
**After (JOIN)**:
```sql
-- Efficient: Single JOIN
SELECT o.*
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE u.status = 'active';
```

---

### **4.3 Partitioned Query**
```sql
-- Query only recent data (partitioned by month)
SELECT SUM(amount)
FROM sales
PARTITION (FOR DATE '2023-01-01' AND DATE '2023-01-31')
WHERE sale_date BETWEEN '2023-01-01' AND '2023-01-31';
```

---

### **4.4 Batch Operations**
**Before (Single Row)**:
```sql
-- Slow: 1000 rows processed one-by-one
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
UPDATE accounts SET balance = balance - 10 WHERE id = 2;
// ...
```
**After (Batch)**:
```sql
-- Fast: Single transaction
UPDATE accounts
SET balance = balance - 10
WHERE id IN (1, 2, ..., 1000);
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Caching Layer](link)** | Offload read-heavy workloads to Redis/Memcached.                             | High read-to-write ratios                |
| **[Connection Pooling](link)** | Manage database connections efficiently.                                  | Multi-threaded applications               |
| **[Query Sharding](link)** | Split data across multiple DB instances.                                    | Horizontal scaling for large datasets     |
| **[Read Replicas](link)** | Distribute read load across replicas.                                       | Read-heavy applications                   |
| **[Batch Processing](link)**| Process large datasets in chunks.                                           | ETL pipelines, analytics                 |
| **[Asynchronous Workloads](link)** | Offload long-running tasks to queues (e.g., Celery).                      | Avoid blocking database threads           |

---

## **6. Troubleshooting & FAQ**
### **Q: How do I find slow queries?**
- Use `pg_stat_statements` (PostgreSQL) or `slow_query_log` (MySQL).
- Look for queries with high `shared_blks_read` or `Rows_examined`.

### **Q: When should I avoid indexing?**
- Columns with **low selectivity** (e.g., `status` with few unique values).
- **Frequently written** columns (indexes slow down `INSERT`s/`UPDATE`s).

### **Q: How much RAM should I allocate to `shared_buffers`?**
- **Rule of thumb**: 20–30% of total RAM (e.g., 8GB for 16GB RAM).
- Monitor `shared_hit_ratio` (target > 95%).

### **Q: What’s the difference between `EXPLAIN` and `EXPLAIN ANALYZE`?**
- `EXPLAIN`: Shows the **plan** (costs, steps) but not execution stats.
- `EXPLAIN ANALYZE`: **Runs the query** and shows actual row counts, runtime.

### **Q: How do I handle write-heavy workloads?**
- Increase `innodb_buffer_pool_size` (MySQL) or `fsync` intervals.
- Use **write-ahead logging (WAL)** optimizations.
- Consider **replication** for high availability.

---
**See Also**:
- [Database Schema Design](link)
- [Asynchronous Processing](link)
- [Monitoring & Observability](link)