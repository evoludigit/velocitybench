# **[Pattern] Database Optimization – Reference Guide**

---

## **Overview**
Database optimization ensures efficient performance, scalability, and cost-effectiveness in data management. This pattern focuses on techniques to reduce query execution time, minimize resource consumption (CPU, memory, storage), improve indexing strategies, and optimize database schema design. By implementing these best practices—like query tuning, indexing, partitioning, and caching—you can significantly enhance application responsiveness and support growing data volumes.

Key outcomes include:
✔ **Faster query performance** – Reduced latency for read/write operations.
✔ **Lower operational costs** – Optimized storage and resource usage.
✔ **Better scalability** – Efficient handling of large datasets.
✔ **Maintainable databases** – Clean, well-structured schemas.

---

## **Schema Reference**

Optimizing a database begins with a well-designed schema. Below is a table of common optimization considerations:

| **Aspect**               | **Optimization Technique**                          | **Description**                                                                                     | **When to Apply**                                                                 |
|--------------------------|----------------------------------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Indexing**             | B-Tree Indexes                                      | Improves search performance for `WHERE`, `JOIN`, and `ORDER BY` clauses.                          | Highly selective columns with frequent filtering.                                |
|                          | Composite Indexes                                  | Optimizes queries with multiple conditions (e.g., `WHERE col1 = X AND col2 = Y`).              | Multi-column filtering or sorting.                                              |
|                          | Covering Indexes                                   | Includes all columns needed for a query, avoiding table lookups.                                    | Read-heavy queries with predictable access patterns.                             |
| **Partitioning**         | Range Partitioning                                  | Splits data into ranges (e.g., by date or numeric ranges).                                         | Large tables with time-series or range-based queries.                             |
|                          | Hash Partitioning                                   | Distributes data evenly using a hash function.                                                     | Evenly distributed workloads with no inherent ordering.                           |
| **Schema Design**        | Normalization (3NF)                                | Reduces redundancy by eliminating duplicate data.                                                 | OLTP systems with frequent updates.                                              |
|                          | Denormalization                                 | Combines related tables to improve read performance (trade-off for write overhead).                 | Analytical queries or reporting systems.                                          |
| **Data Types**           | Appropriate Column Types                           | Use `VARCHAR` for text, `INT` for IDs, `BOOLEAN` for flags, etc.                                   | Reduces storage and improves comparison speed.                                   |
|                          | Avoid `TEXT`/`BLOB` for Indexed Columns           | Indexes on large binary/text fields degrade performance.                                            | Non-indexed columns or external storage (e.g., S3).                              |
| **Constraints**          | `NOT NULL` Constraints                             | Forces data integrity and reduces NULL-related inefficiencies.                                       | Critical fields that cannot be missing.                                          |
|                          | Foreign Key Constraints                            | Enforces referential integrity and enables optimized joins.                                         | Relationship-heavy schemas.                                                      |
| **Storage**              | Compression                                        | Reduces storage footprint (e.g., `ROW_FORMAT=COMPRESSED`).                                        | Large datasets with repetitive data.                                             |
|                          | Archiving Old Data                                 | Moves stale data to cold storage (e.g., Amazon S3, HDFS).                                           | Long-term retention requirements.                                                |
| **Caching**              | In-Memory Caching (Redis, Memcached)               | Stores frequently accessed data in RAM for sub-millisecond latency.                                | High-traffic applications with repetitive queries.                              |
|                          | Query Result Caching                               | Caches repeated query results (e.g., MySQL Query Cache).                                          | Read-heavy applications with predictable queries.                                |

---

## **Query Optimization Techniques**

### **1. Indexing Strategies**
#### **Best Practices:**
- **Avoid Over-Indexing**: Too many indexes slow down `INSERT`/`UPDATE` operations.
- **Use Selective Indexes**: Index only columns frequently used in `WHERE`, `JOIN`, or `ORDER BY`.
- **Monitor Index Usage**: Drop unused indexes (`EXPLAIN` in MySQL/PostgreSQL).

#### **Example: Adding a Composite Index**
```sql
-- Optimizes queries filtering by `status` and `created_at`
CREATE INDEX idx_status_created ON orders (status, created_at);
```

#### **Example: Dropping an Unused Index**
```sql
-- Check usage first (PostgreSQL example)
SELECT * FROM pg_stat_user_indexes WHERE indexrelname = 'idx_unused_column';

-- Drop if unused
DROP INDEX idx_unused_column;
```

---

### **2. Query Tuning**
#### **Key Areas to Review:**
- **Join Optimization**: Ensure proper join order and use indexes.
- **Subquery Rewriting**: Replace correlated subqueries with `JOIN`s.
- **Avoid `SELECT *`**: Fetch only required columns.
- **Limit Result Sets**: Use `LIMIT` for pagination.

#### **Example: Optimizing a Slow Query**
**Before (Inefficient):**
```sql
-- Full table scan due to missing index
SELECT * FROM users WHERE email = 'user@example.com';
```

**After (Optimized with Index):**
```sql
-- Add index first
CREATE INDEX idx_users_email ON users (email);

-- Query now uses the index
SELECT * FROM users WHERE email = 'user@example.com';
```

**Example: Rewriting a Correlated Subquery**
**Before:**
```sql
-- Slow due to repeated subquery execution
SELECT u.name FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.id AND o.status = 'pending'
);
```

**After:**
```sql
-- Optimized join
SELECT DISTINCT u.name FROM users u
JOIN orders o ON u.id = o.user_id AND o.status = 'pending';
```

---

### **3. Partitioning Example**
#### **Range Partitioning (MySQL)**
```sql
-- Partition a large orders table by month
CREATE TABLE orders (
    id INT AUTO_INCREMENT,
    user_id INT,
    amount DECIMAL(10,2),
    created_at DATETIME,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (YEAR(created_at) * 100 + MONTH(created_at)) (
    PARTITION p_202301 VALUES LESS THAN (202302),
    PARTITION p_202302 VALUES LESS THAN (202303),
    PARTITION p_202303 VALUES LESS THAN (202304),
    PARTITION p_max VALUES LESS THAN MAXVALUE
);
```

#### **Hash Partitioning (PostgreSQL)**
```sql
-- Distribute data evenly using hash of user_id
CREATE TABLE users (
    id SERIAL,
    username VARCHAR(50),
    email VARCHAR(100)
) PARTITION BY HASH(id);

-- Create partitions
CREATE TABLE users_p1 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE users_p2 PARTITION OF users
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- ... repeat for remaining partitions
```

---

### **4. Denormalization Example**
#### **Normalized Schema (OLTP)**
```sql
CREATE TABLE products (id INT, name VARCHAR(100), price DECIMAL(10,2));
CREATE TABLE orders (id INT, user_id INT, order_date DATE);
CREATE TABLE order_items (id INT, order_id INT, product_id INT, quantity INT);
```

#### **Denormalized Schema (Optimized for Analytics)**
```sql
CREATE TABLE product_orders (
    product_id INT,
    order_date DATE,
    total_quantity INT,  -- Aggregated from order_items
    total_revenue DECIMAL(10,2)  -- price * quantity
);
```

---

### **5. Caching Strategies**
#### **Redis Caching Example**
```sql
-- Cache query results in Redis (pseudo-code)
SET cache:users:100 JSON '{"name": "Alice", "email": "alice@example.com"}'
EXPIRE cache:users:100 3600  -- Cache for 1 hour

-- Application checks cache before querying DB
GET cache:users:100
```

#### **Database-Level Query Caching (MySQL)**
```sql
-- Enable query cache (MySQL)
SET GLOBAL query_cache_size = 10000000;  -- 10MB
SET GLOBAL query_cache_type = ON;

-- Query result cached automatically
SELECT * FROM products WHERE category = 'electronics';
```

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Cause**                                      | **Mitigation**                                                                                     |
|--------------------------------------|-----------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Full Table Scans**                 | Missing indexes on filtered columns.        | Add indexes, review `EXPLAIN` output.                                                            |
| **Lock Contention**                  | Long-running transactions.                   | Use optimistic concurrency control, break queries into smaller transactions.                     |
| **Over-Partitioning**                | Too many small partitions.                   | Consolidate partitions, avoid excessive overhead.                                                 |
| **Index Bloat**                      | Frequent updates on indexed columns.         | Rebuild indexes periodically (`ALTER TABLE ... REBUILD`).                                        |
| **Unused Constraints**               | Foreign keys or checks slowing inserts.      | Drop unused constraints, consider deferred checks if needed.                                     |
| **Ignoring Query Plans**             | Blindly writing queries without optimization. | Use `EXPLAIN` to analyze and rewrite slow queries.                                                 |

---

## **Tools for Database Optimization**
| **Tool**            | **Purpose**                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **`EXPLAIN` (SQL)** | Analyzes query execution plans (e.g., `EXPLAIN SELECT * FROM table`).      |
| **MySQL Workbench** | Visual query editor, performance insights, and schema migration.           |
| **pgAdmin (PostgreSQL)** | GUI for indexing, partitioning, and query optimization.                  |
| **Percona Toolkit** | Advanced monitoring and optimization tools for MySQL.                     |
| **AWS RDS Performance Insights** | Tracks slow queries and resource usage in AWS RDS.                        |
| **Redis CLI**       | Manages caching layers and monitors cache hits/misses.                     |

---

## **Related Patterns**
To complement database optimization, consider integrating these patterns:

1. ****Application-Level Caching**
   - *Pattern*: Cache frequently accessed data in-memory (e.g., Redis) to reduce database load.
   - *Use Case*: E-commerce product listings, user sessions.

2. ****Read Replicas**
   - *Pattern*: Deploy read replicas to distribute read workloads.
   - *Use Case*: High-traffic applications with heavy read operations.

3. ****Connection Pooling**
   - *Pattern*: Reuse database connections to minimize overhead.
   - *Use Case*: Web applications with variable traffic.

4. ****Query Sharding**
   - *Pattern*: Split data across multiple database instances based on keys (e.g., user ID ranges).
   - *Use Case*: Scaling horizontally for massive datasets.

5. ****Database-Migration Strategies**
   - *Pattern*: Gradually migrate from legacy to optimized schemas (e.g., blue-green deployment).
   - *Use Case*: Refactoring large, monolithic databases.

---

## **When to Revisit Optimization**
- **After Schema Changes**: New indexes or columns may break performance.
- **Seasonal Traffic Spikes**: Optimize for peak loads (e.g., Black Friday sales).
- **Data Growth**: Partition or archive old data to maintain speed.
- **Tool Updates**: Databases evolve; review optimizer settings (e.g., MySQL 8.0+ improvements).

---
**Next Steps**:
- Audit your slowest queries with `EXPLAIN`.
- Profile your schema for normalization/denormalization trade-offs.
- Implement caching for repeatable operations.