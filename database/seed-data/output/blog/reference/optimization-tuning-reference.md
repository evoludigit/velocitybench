# **[Pattern] Optimization Tuning – Reference Guide**

---

## **Overview**
Optimization tuning improves query and application performance by systematically adjusting database, caching, and execution parameters to minimize latency, CPU/memory usage, and cost. This pattern applies to **SQL databases, NoSQL systems, code-level optimizations, and infrastructure tuning**. It includes techniques like indexing, query restructuring, caching layers, and resource allocation to achieve scalable and efficient operations.

Key benefits:
- Reduces execution time for critical queries.
- Lowers operational costs (e.g., compute, storage).
- Minimizes resource contention (CPU, memory, I/O).
- Improves user experience with faster data retrieval.

Best suited for:
- High-traffic applications (e.g., e-commerce, analytics dashboards).
- Systems with performance bottlenecks (e.g., slow queries, high latency).
- Cost-sensitive environments (e.g., serverless databases, pay-per-use models).

---
## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Execution Plan**     | A step-by-step strategy the database uses to execute a query (e.g., hash join, nested loop).    | `EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 100;`                                |
| **Indexing**           | Data structures (B-trees, hash indexes) to speed up `WHERE`, `JOIN`, and `ORDER BY` clauses.      | `CREATE INDEX idx_customer_id ON orders(customer_id);`                                          |
| **Query Rewriting**    | Modifying SQL to leverage indexes, reduce scans, or use simpler operators.                        | Replacing `LIKE 'A%'` with `WHERE name >= 'A' AND name < 'B'` to use a range scan.             |
| **Caching**            | Storing frequently accessed data in memory (e.g., Redis, in-memory DBs) to avoid disk I/O.        | Caching user sessions with `GET /api/session` responding from Redis instead of SQL.           |
| **Partitioning**       | Splitting tables into smaller chunks to parallelize queries or reduce scan size.                 | `PARTITION BY RANGE (YEAR(order_date))` on an `orders` table.                                |
| **Resource Throttling**| Limiting concurrent requests to prevent overload (e.g., connection pooling, query timeouts).    | Setting `max_connections = 50` in PostgreSQL to avoid CPU spikes.                               |
| **Denormalization**    | Reducing joins by duplicating data ( trade-off: storage for speed).                              | Storing `customer_name` in the `orders` table instead of joining with `customers`.           |
| **Batch Processing**   | Executing multiple operations in a single call to reduce round-trips (e.g., bulk inserts).     | `INSERT INTO logs VALUES (...), (...), (...)` (1 call vs. 3).                                 |
| **Monitoring Metrics** | Tracking performance indicators (e.g., query duration, cache hit ratio, lock contention).         | Prometheus metrics: `db_query_duration_seconds`, `cache_hits_total`.                           |

---
## **Implementation Details**

### **1. Identify Bottlenecks**
- **Tools**:
  - Database: `EXPLAIN ANALYZE`, query profiling (e.g., PostgreSQL `pg_stat_statements`, MySQL Slow Query Log).
  - Application: APM tools (e.g., New Relic, Datadog), distributed tracing (e.g., Jaeger).
  - Infrastructure: Cloud provider metrics (e.g., AWS CloudWatch, GCP Stackdriver).
- **Targets**:
  - Slowest queries (>100ms, >1% of runtime).
  - High I/O or CPU usage.
  - Lock contention or deadlocks.

### **2. Optimize Queries**
#### **A. Indexing Strategy**
- **When to Add**:
  - Columns in `WHERE`, `JOIN`, `ORDER BY`, or `GROUP BY` clauses.
  - Low-cardinality columns (e.g., `status` with 3 values) unless already indexed.
- **Avoid Over-Indexing**:
  - Each index adds write overhead (~10–20% slower inserts/updates).
  - Use `EXPLAIN` to verify indexes are used:
    ```sql
    EXPLAIN SELECT * FROM products WHERE category = 'Electronics';
    -- Look for "Index Scan" vs. "Seq Scan".
    ```
- **Composite Indexes**:
  - Order columns by selectivity (most selective first):
    ```sql
    CREATE INDEX idx_name_category ON products(name, category);
    -- Faster for WHERE name = 'Laptop' AND category = 'Electronics'.
    ```

#### **B. Query Rewriting**
- **Replace `LIKE` with Range Scans**:
  ```sql
  -- Slow (full scan):
  SELECT * FROM users WHERE name LIKE 'A%';

  -- Faster (uses index):
  SELECT * FROM users WHERE name >= 'A' AND name < 'B';
  ```
- **Use `EXISTS` Instead of `IN` for Joins**:
  ```sql
  -- Better for large tables:
  SELECT * FROM orders o WHERE EXISTS (SELECT 1 FROM customers c WHERE o.customer_id = c.id);

  -- Avoid:
  SELECT * FROM orders o WHERE customer_id IN (SELECT id FROM customers);
  ```
- **Limit Result Sets**:
  ```sql
  -- Fetch only needed columns:
  SELECT id, name FROM products LIMIT 1000; -- Instead of SELECT *
  ```

#### **C. Caching Layer**
- **Implementation**:
  - **In-Memory Caching**: Redis, Memcached (for microseconds latency).
  - **Application-Level**: Cache frequent queries (e.g., `GET /api/product/123`).
  - **Database-Level**: PostgreSQL `pg_cache`, MySQL Query Cache (limited use).
- **Cache Invalidation**:
  - Time-based (e.g., TTL=1 hour).
  - Event-based (e.g., invalidate on `PRODUCT_UPDATED` event).
- **Example (Redis)**:
  ```bash
  # Set cache for 5 minutes
  SET product:123 '{"name": "Laptop", "price": 999}' EX 300

  # Check cache before querying DB
  IF NOT EXISTS product:123 THEN
      GET FROM DATABASE
      SET product:123 <result>
  END
  ```

#### **D. Partitioning**
- **Horizontal Partitioning**:
  - Split by time, range, or hash:
    ```sql
    -- PostgreSQL (by time):
    CREATE TABLE sales (
        id SERIAL,
        amount NUMERIC
    ) PARTITION BY RANGE (sale_date);
    CREATE TABLE sales_y2023 PARTITION OF sales FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
    ```
- **Vertical Partitioning**:
  - Separate hot/cold data (e.g., move logs to archival storage).

### **3. Infrastructure Tuning**
| **Resource**       | **Optimization**                                                                 | **Example**                                                                                     |
|--------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Database**       | Adjust `work_mem`, `shared_buffers` (PostgreSQL), `innodb_buffer_pool_size` (MySQL). | `shared_buffers = 8GB` for PostgreSQL to reduce disk I/O.                                      |
| **Connections**    | Limit pool size, use connection pooling (PgBouncer, ProxySQL).                     | `max_connections = 200` in PostgreSQL, pool size = 50 in PgBouncer.                            |
| **Network**        | Reduce latency: co-locate DB and app, use TCP keepalive.                           | `tcp_keepalive = 30` in PostgreSQL to detect dead connections early.                           |
| **Storage**        | Use SSDs, compress data (e.g., PostgreSQL `pg_compress`), archive old data.        | `ALTER TABLE logs SET TABLESPACE TO ssds;`.                                                    |
| **Server**         | Scale vertically (CPU/RAM) or horizontally (read replicas).                      | Add read replica for read-heavy workloads (e.g., MySQL `REPLICATE DO DB`).                     |

### **4. Code-Level Optimizations**
- **Avoid N+1 Queries**:
  ```javascript
  // Bad (N+1):
  const orders = await Order.findAll();
  const users = await Promise.all(orders.map(order => User.findById(order.userId)));

  // Good (Eager Load):
  const orders = await Order.findAll({ include: [User] });
  ```
- **Batch Writes**:
  ```sql
  -- Instead of 100 separate INSERTs:
  INSERT INTO users (id, name) VALUES
      (1, 'Alice'), (2, 'Bob'), (3, 'Charlie');
  ```
- **Lazy Loading**:
  - Load only needed data (e.g., avoid `SELECT *`).

### **5. Monitoring and Iteration**
- **Key Metrics**:
  - **Query**: Execution time, rows scanned, index usage.
  - **Cache**: Hit ratio (e.g., 90%+ is ideal), evictions.
  - **Resource**: CPU/memory usage, disk I/O, connection count.
- **Tools**:
  - Databases: `pg_stat_activity`, `sys.schema_discover_*` (SQL Server).
  - APM: New Relic, Datadog, Prometheus + Grafana.
- **Iterative Process**:
  1. Identify slow queries.
  2. Apply optimizations (indexes, caching, etc.).
  3. Measure impact with `EXPLAIN ANALYZE` or APM.
  4. Repeat for next bottleneck.

---
## **Schema Reference**
| **Category**          | **Parameter**               | **Description**                                                                                     | **Example Value**                          |
|-----------------------|-----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Database Tuning**   | `work_mem`                  | Memory allocated per query (PostgreSQL).                                                          | `16MB`                                      |
|                       | `shared_buffers`            | Memory for shared cache (PostgreSQL).                                                              | `4GB`                                       |
|                       | `innodb_buffer_pool_size`   | Memory for InnoDB buffer pool (MySQL).                                                             | `6GB`                                       |
| **Connection Pooling**| `max_connections`           | Max concurrent DB connections.                                                                     | `200`                                       |
|                       | `pgbouncer.pool_size`       | Pool size for PgBouncer.                                                                          | `50`                                        |
| **Caching**           | `redis.memory_limit`        | Max Redis memory (MB).                                                                           | `512MB`                                     |
| **Storage**           | `postgresql.table_space`    | Filesystem for tables (e.g., `ssds`).                                                              | `ssd_data`                                  |
| **Query**             | `sql.max_execution_time`    | Timeout for long-running queries (ms).                                                            | `30000` (30s)                               |
| **Partitioning**      | `partition_by`              | Table partitioning strategy (range, list, hash).                                                   | `PARTITION BY RANGE (order_date)`          |

---
## **Query Examples**
### **1. Analyzing Query Performance**
```sql
-- PostgreSQL: Show execution plan with timing
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 100;

-- MySQL: Slow query log (enable in my.cnf)
log-slow-queries = /var/log/mysql/slow.log
long_query_time = 1
```

### **2. Adding an Index**
```sql
-- PostgreSQL: Create a composite index
CREATE INDEX idx_customer_order_date ON orders(customer_id, order_date);

-- MySQL: Add a covering index (includes selected columns)
CREATE INDEX idx_email_status ON users(email, status) INCLUDE (name);
```

### **3. Using a Cache Layer (Pseudocode)**
```python
import redis

r = redis.Redis(host='localhost', port=6379)

def get_product(product_id):
    cache_key = f"product:{product_id}"
    cached = r.get(cache_key)
    if cached:
        return json.loads(cached)
    result = db.query("SELECT * FROM products WHERE id = %s", product_id)
    r.setex(cache_key, 300, json.dumps(result))  # Cache for 5 mins
    return result
```

### **4. Partitioning a Table (PostgreSQL)**
```sql
-- Create table with range partitioning
CREATE TABLE sales (
    id SERIAL,
    amount NUMERIC,
    sale_date TIMESTAMP
) PARTITION BY RANGE (sale_date);

-- Create partitions for each year
CREATE TABLE sales_2023 PARTITION OF sales
    FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE sales_2024 PARTITION OF sales
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### **5. Optimizing a Slow Query**
```sql
-- Original slow query (full scan)
SELECT * FROM products WHERE name LIKE 'A%';

-- Optimized (uses index + range scan)
SELECT id, name, price FROM products
WHERE name >= 'A' AND name < 'B'
ORDER BY name;
```

---
## **Related Patterns**
| **Pattern**              | **Description**                                                                                     | **When to Use**                                                                                  |
|--------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Caching]**            | Store frequently accessed data in memory to reduce DB load.                                          | High-read, low-write workloads (e.g., product catalogs).                                        |
| **[Connection Pooling]** | Reuse DB connections to reduce overhead.                                                            | Applications with many short-lived connections (e.g., microservices).                            |
| **[Read Replicas]**      | Distribute read load across multiple DB instances.                                                 | Read-heavy applications needing scalability (e.g., analytics dashboards).                       |
| **[Denormalization]**    | Duplicate data to reduce joins (trade-off: storage for speed).                                      | OLTP systems where query speed > data consistency (e.g., user profiles).                         |
| **[Query Sharding]**     | Split data across multiple DB instances by key (e.g., `user_id`).                                   | Global applications with high write volume (e.g., social media).                                |
| **[Asynchronous Processing]** | Offload heavy tasks (e.g., reports) to background workers.                                      | Batch jobs, analytics, and non-critical operations.                                            |
| **[Rate Limiting]**      | Throttle API/database access to prevent overload.                                                  | Public APIs, microservices under DDoS risk.                                                    |

---
## **Anti-Patterns**
1. **Over-Indexing**:
   - Adding indexes without measuring impact (e.g., indexing all columns).
   - *Mitigation*: Use `EXPLAIN ANALYZE` to verify indexes are used.

2. **Ignoring Monitoring**:
   - Not tracking query performance after changes.
   - *Mitigation*: Set up alerts for slow queries (e.g., >500ms).

3. **Caching Everything**:
   - Caching stale or rarely accessed data.
   - *Mitigation*: Use TTLs or event-based invalidation.

4. **Static Optimizations**:
   - Tuning without considering workload changes.
   - *Mitigation*: Monitor and retune periodically.

5. **Ignoring Write Performance**:
   - Optimizing only reads, leading to bottlenecks during bulk inserts.
   - *Mitigation*: Test write operations under load (e.g., `pgbench` for PostgreSQL).