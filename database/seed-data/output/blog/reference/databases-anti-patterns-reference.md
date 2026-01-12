#[Pattern] **Databases Anti-Patterns: Comprehensive Reference Guide**

---

## **Overview**
Databases **anti-patterns** are common, suboptimal design or implementation choices that degrade performance, scalability, maintainability, or data integrity. Unlike proven patterns (e.g., **Single-Table Inheritance** or **Read Replicas**), these pitfalls can introduce technical debt, bottlenecks, or costly refactoring. This guide categorizes **10 critical anti-patterns**, outlines their negative impacts, and provides corrective alternatives, ensuring architects and developers avoid inefficient database designs.

---

## **Key Anti-Patterns and Impacts**
| **Anti-Pattern**               | **Description**                                                                                                                                                                                                 | **Impact**                                                                                                                                                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **1. Poor Normalization**       | Excessively or insufficiently normalized tables (e.g., 5NF in favor of 1NF).                                                                                                                                  | Performance degradation, redundancy, or update anomalies.                                                                                                                                                       |
| **2. Overuse of JOINs**          | Deep, complex joins (>3) or unoptimized cartesian products.                                                                                                                                                     | Slow queries, high CPU/memory usage, and scalability issues.                                                                                                                                                         |
| **3. Unbounded Data Growth**     | Retaining data indefinitely without archival/TTL policies.                                                                                                                                                     | Storage bloat, backup costs, and query slowness.                                                                                                                                                                   |
| **4. Single-Table Design**       | Storing unrelated entities (e.g., "all data in one table") without clear separation.                                                                                                                              | Hard-to-read queries, inefficient indexing, and scalability bottlenecks.                                                                                                                                      |
| **5. Unindexed Foreign Keys**    | Foreign keys without indexes on referenced columns.                                                                                                                                                           | Slow joins, especially with large tables.                                                                                                                                                                     |
| **6. Excessive Transactions**    | Long-running or nested transactions (e.g., >100ms duration).                                                                                                                                                     | Lock contention, deadlocks, and degraded concurrency.                                                                                                                                                               |
| **7. Shadow Tables**             | Duplicate "shadow" tables for legacy or ad-hoc queries without proper ETL pipelines.                                                                                                                               | Data inconsistency, duplication, and maintenance overhead.                                                                                                                                                            |
| **8. No Partitioning**           | Large, monolithic tables without horizontal/vertical partitioning (e.g., time-based splits).                                                                                                                   | Slow scans, high I/O, and poor query performance.                                                                                                                                                                   |
| **9. Dynamic SQL Abuse**         | Generating and executing dynamic SQL without proper validation or caching (e.g., `EXECUTE IMMEDIATE`).                                                                                                       | Security risks (SQL injection), unpredictable performance, and cache misses.                                                                                                                                    |
| **10. Ignoring Query Tuning**    | Accepting slow queries without optimization (e.g., missing `EXPLAIN`, no statistics update).                                                                                                                   | Unpredictable performance, frustrated users, and inefficient resource usage.                                                                                                                                    |

---

## **Implementation Details: Avoiding Anti-Patterns**
### **1. Database Design**
- **Normalization Trade-offs**:
  - Use **3NF** for most OLTP systems; **denormalize strategically** for read-heavy workloads (e.g., star schema in data warehouses).
  - *Rule of Thumb*: Denormalize only if queries benefit from fewer joins (e.g., `SELECT user_name FROM users JOIN orders` → `SELECT name FROM user_orders`).
- **Partitioning Strategies**:
  - **Horizontal**: Split by time (e.g., `log_data_2023`, `log_data_2024`).
  - **Vertical**: Separate high-volume columns (e.g., `users(id, email)` and `users_activity(id, activity_log)`).
  - *Tools*: PostgreSQL `PARTITION BY RANGE`, MySQL `PARTITION BY LIST`.

### **2. Query Optimization**
- **Join Optimization**:
  - Limit joins to **2–3 tables** per query. Use **CTEs** (Common Table Expressions) for complex logic:
    ```sql
    WITH user_orders AS (
      SELECT * FROM orders WHERE user_id = 123
    )
    SELECT u.name, oo.total
    FROM users u JOIN user_orders oo ON u.id = oo.user_id;
    ```
  - *Avoid*: `SELECT * FROM table1 JOIN table2 JOIN table3 ON ...`.
- **Indexing**:
  - **Composite indexes** for multi-column filters (e.g., `CREATE INDEX idx_name_email ON users(name, email)` for `WHERE name LIKE '%A%' AND email IS NOT NULL`).
  - *Rule*: Index only columns used in `WHERE`, `JOIN`, or `ORDER BY`.

### **3. Transaction Management**
- **Keep Transactions Short**:
  - Goal: **<100ms** for most transactions. Avoid holding locks longer than necessary.
  - *Example*: Split a multi-step update into atomic transactions:
    ```sql
    -- Instead of:
    BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    INSERT INTO transactions (user_id, amount) VALUES (1, -100);
    COMMIT;

    -- Use:
    BEGIN;
    UPDATE accounts SET balance = balance - 100 WHERE id = 1;
    COMMIT;
    BEGIN;
    INSERT INTO transactions (user_id, amount) VALUES (1, -100);
    COMMIT;
    ```
- **Use Savepoints**:
  - For nested transactions, roll back specific parts:
    ```sql
    BEGIN;
    -- Step 1 (risky)
    UPDATE inventory SET stock = stock - 1 WHERE id = 1;
    SAVEPOINT step1;
    -- Step 2 (safe)
    INSERT INTO orders (item_id) VALUES (1);
    ROLLBACK TO step1; -- Revert only Step 1
    ```

### **4. Data Lifecycle Management**
- **Time-to-Live (TTL)**:
  - Auto-expire old data (e.g., PostgreSQL `DROP TABLE old_logs` via `pg_cron`).
  - *Example*: Purge logs older than 30 days:
    ```sql
    DELETE FROM logs WHERE created_at < CURRENT_DATE - INTERVAL '30 days';
    ```
- **Archiving**:
  - Move cold data to cheaper storage (e.g., S3, Snowflake stages) with `EXTERNAL TABLE`:
    ```sql
    CREATE EXTERNAL TABLE archived_logs (like logs)
    STORED AS PARQUET LOCATION 's3://bucket/logs/archived/';
    ```

### **5. Security and Performance**
- **Dynamic SQL**:
  - *Never* use `EXECUTE IMMEDIATE` with unvalidated input (SQL injection risk).
  - *Safe Alternative*: Parameterized queries:
    ```sql
    -- Bad:
    EXECUTE IMMEDIATE 'DELETE FROM users WHERE id = ' || input_id;

    -- Good:
    DELETE FROM users WHERE id = $1;
    ```
  - Cache frequent queries (e.g., Redis, Materialized Views):
    ```sql
    CREATE MATERIALIZED VIEW mv_daily_active_users AS
    SELECT user_id, COUNT(*) FROM page_views GROUP BY user_id;
    ```
    *Refresh daily:* `REFRESH MATERIALIZED VIEW mv_daily_active_users;`

---

## **Schema Reference: Anti-Pattern vs. Pattern**
| **Anti-Pattern Schema**               | **Refactored Schema**                          | **Improvement**                                                                 |
|----------------------------------------|-----------------------------------------------|-------------------------------------------------------------------------------|
| Single monolithic table:               | Separated tables with relations:              | Faster queries, clearer data model.                                          |
| ```sql CREATE TABLE everything (id INT, name TEXT, order_date DATE, product_id INT, user_email TEXT);``` | ```sql CREATE TABLE users (id INT, email TEXT); CREATE TABLE orders (id INT, user_id INT, date DATE); CREATE TABLE products (id INT, name TEXT);``` | Reduces join complexity; enables partitioning on `orders(date)`.          |
| Poorly indexed foreign key:            | Indexed foreign key:                          | Speeds up joins.                                                              |
| ```sql ALTER TABLE orders ADD COLUMN user_id INT;``` | ```sql ALTER TABLE orders ADD COLUMN user_id INT, ADD INDEX idx_user_id (user_id);``` | Join on `orders.user_id = users.id` is now efficient.                     |
| Unpartitioned large table:             | Partitioned by time:                          | Faster scans for recent data.                                                 |
| ```sql CREATE TABLE huge_logs (id INT, message TEXT, created_at TIMESTAMP);``` | ```sql CREATE TABLE huge_logs (LIKE logs PARTITION BY RANGE (created_at) (PARTITION p2023 VALUES LESS THAN ('2024-01-01'));``` | Only scans relevant partitions for `WHERE created_at > '2023-12-01'`. |

---

## **Query Examples: Anti-Pattern vs. Optimized**
### **1. Excessive JOINs**
| **Anti-Pattern**                          | **Optimized**                                                                 | **Key Fix**                          |
|--------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| ```sql SELECT u.name, o.product_id, p.category FROM users u JOIN orders o ON u.id = o.user_id JOIN products p ON o.product_id = p.id WHERE o.status = 'shipped';``` | ```sql SELECT u.name, o.product_id, p.category FROM users u JOIN (SELECT user_id, product_id FROM orders WHERE status = 'shipped') AS shipped_orders ON u.id = shipped_orders.user_id JOIN products p ON shipped_orders.product_id = p.id;``` | Pre-filters `orders` before joining. |

### **2. No Index Usage**
| **Anti-Pattern**                          | **Optimized**                                                                 | **Key Fix**                          |
|--------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| ```sql SELECT * FROM users WHERE email LIKE '%@gmail.com' ORDER BY name;```    | ```sql CREATE INDEX idx_email_name ON users(email, name); SELECT * FROM users WHERE email LIKE '%@gmail.com' ORDER BY name;``` | Index covers both `WHERE` and `ORDER BY`. |

### **3. Long Transactions**
| **Anti-Pattern**                          | **Optimized**                                                                 | **Key Fix**                          |
|--------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| ```sql BEGIN; UPDATE inventory SET stock = stock - 1 WHERE id = 1; UPDATE audit_log SET action = 'deduct' WHERE item_id = 1; COMMIT;``` | ```sql BEGIN; UPDATE inventory SET stock = stock - 1 WHERE id = 1; COMMIT; BEGIN; INSERT INTO audit_log (item_id, action) VALUES (1, 'deduct'); COMMIT;``` | Atomicity per logical step.          |

### **4. Dynamic SQL Risk**
| **Anti-Pattern**                          | **Optimized**                                                                 | **Key Fix**                          |
|--------------------------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| ```sql EXECUTE IMMEDIATE 'DELETE FROM users WHERE id = ' || user_id;```        | ```sql DELETE FROM users WHERE id = $1;```                                    | Uses parameterized query.             |

---

## **Related Patterns**
To complement anti-pattern avoidance, adopt these **proven patterns**:
| **Pattern**                     | **Purpose**                                                                         | **When to Use**                                                                 |
|----------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Single-Table Inheritance**     | Store hierarchical data in one table (e.g., `users(id, type, data)`.               | When entities share 90%+ fields (e.g., `User`/`Admin` extensions).              |
| **Read Replicas**                | Offload read queries to replica nodes.                                            | For read-heavy workloads (e.g., reporting).                                     |
| **Materialized Views**           | Pre-compute expensive aggregations.                                                | For dashboards with static data (refresh periodically).                          |
| **Sharding**                     | Split data across servers (e.g., by `user_id % 10`).                               | When a single table exceeds 10TB or query performance degrades.                  |
| **Event Sourcing**               | Store state changes as immutable events (e.g., `order_created`, `order_shipped`). | For audit trails or complex workflows (e.g., financial transactions).            |
| **Connection Pooling**           | Reuse database connections (e.g., PgBouncer).                                      | To reduce overhead of connection setup.                                       |

---

## **Mitigation Checklist**
Before production, audit your database for anti-patterns:
1. [ ] **Design**:
   - [ ] Tables are normalized to **3NF** (or denormalized intentionally).
   - [ ] Foreign keys are **indexed** on referenced columns.
   - [ ] Large tables are **partitioned** by access patterns.
2. **Queries**:
   - [ ] Joins are **limited to <3 tables** per query.
   - [ ] `EXPLAIN ANALYZE` confirms no **full-table scans**.
   - [ ] Dynamic SQL uses **parameterized queries**.
3. **Lifecycle**:
   - [ ] Old data has a **TTL policy** (e.g., logs purged after 30 days).
   - [ ] Archives are **externalized** (e.g., S3, Snowflake).
4. **Performance**:
   - [ ] Transactions run **<100ms**.
   - [ ] Long-running queries are **queued** (e.g., Celery for async jobs).
5. **Security**:
   - [ ] No **hardcoded credentials** in application code.
   - [ ] **Least privilege** granted to database users.

---
**Further Reading**:
- [15 Database Anti-Patterns and How to Avoid Them](https://www.percona.com/resources/15-database-anti-patterns-and-how-to-avoid-them)
- *Database-System-Concepts* by Silberschatz (Chapter 10: Query Optimization)
- [PostgreSQL Partitioning Guide](https://www.postgresql.org/docs/current/ddl-partitioning.html)