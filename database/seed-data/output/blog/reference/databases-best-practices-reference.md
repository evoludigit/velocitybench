**[Pattern] Database Best Practices – Reference Guide**

---

### **Overview**
This guide outlines proven techniques, optimizations, and architectural patterns for designing, implementing, and maintaining high-performance, scalable, and maintainable databases. Adhering to these best practices minimizes technical debt, improves query efficiency, and ensures data integrity. Best practices are categorized by **schema design, indexing, query optimization, security, monitoring, and scalability**—critical areas that impact system reliability and performance at scale.

---

## **1. Key Concepts**

### **Core Principles**
- **Normalize where it matters**: Balance denormalization (for performance) with normalization (to avoid redundancy) using 3NF or BCNF as a baseline.
- **Index judiciously**: Indexes speed up queries but increase write overhead. Use them only for columns frequently queried or filtered.
- **Write for scale**: Design schemas to handle growth (e.g., sharding, partitioning).
- **Monitor, measure, iterate**: Regularly review query performance, lock contention, and resource usage.

---

## **2. Schema Design Best Practices**

### **2.1. Schema Reference**
| **Category**       | **Best Practice**                                                                 | **Example**                                                                 |
|--------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Table Design**   | Avoid single-column tables ("junk dimensions"); group related data.                | ❌ `Users`, `Orders` → ✅ `UserOrders` (if tightly coupled)                 |
| **Data Types**     | Use appropriate types (e.g., `UUID` for IDs, `ENUM` for fixed sets, `JSON` for flexible data). | `ORDER BY created_at` (use `TIMESTAMP` over `DATETIME`)                  |
| **Constraints**    | Enforce business rules with `NOT NULL`, `UNIQUE`, `CHECK`, and `FOREIGN KEY`.      | `CONSTRAINT valid_email CHECK (email LIKE '%@%.%')`                         |
| **Partitioning**   | Split large tables by time ranges, regions, or workloads (e.g., `PARTITION BY RANGE`). | `PARTITION BY MONTH(created_at)` for analytics tables                      |
| **Denormalization**| Duplicate data to avoid joins (if read-heavy, e.g., materialized views or EAV).    | `Cache` table with pre-computed aggregates for dashboard queries          |

---

## **2.2. Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                                                         | **Fix**                                                                       |
|---------------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Super Tables**                | Poor performance; difficult to partition.                                        | Split high-cardinality tables into smaller tables.                         |
| **Mega-Joins**                  | Slow queries; high CPU/memory usage.                                           | Precompute joins (e.g., CTEs, temporary tables) or denormalize.           |
| **Unused Columns**              | Wastes storage and slows inserts.                                               | Remove or archive stale columns.                                           |
| **No Schema Evolution Plan**    | Breaking changes during migrations.                                             | Use **forward-compatible schemas** (e.g., `ALTER TABLE` with column additions). |

---

## **3. Indexing Strategies**

### **3.1. Index Types and Use Cases**
| **Index Type**       | **When to Use**                                                                 | **Syntax Example**                                                                 |
|----------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **B-Tree**           | Default for equality/range queries on ordered data.                              | `CREATE INDEX idx_name ON table(name)`                                          |
| **Hash**             | Equality-only lookups (e.g., `WHERE id = ?`).                                   | `CREATE INDEX idx_hash ON table(id) USING HASH` (PostgreSQL)                   |
| **GIN/GIST**         | Full-text, JSON, or geospatial data.                                             | `CREATE INDEX idx_gin ON table USING GIN(to_tsvector('english', text_column))` |
| **Composite**        | Queries filtering on multiple columns in order.                                 | `CREATE INDEX idx_name_email ON table(name, email)`                            |
| **Partial**          | Index subsets of data (e.g., active users only).                                | `CREATE INDEX idx_active ON table(email) WHERE is_active = true` (PostgreSQL) |

---

### **3.2. Indexing Dos and Don’ts**
| **Do**                          | **Don’t**                                                                       |
|---------------------------------|-------------------------------------------------------------------------------|
| Index columns used in `WHERE`, `JOIN`, or `ORDER BY`.                           | Index every column (reduces write throughput).                                |
| Use **covering indexes** (include all columns in `SELECT`).                     | Let the query planner guess—**hint manually** if needed (e.g., `/*+ INDEX */`).|
| Monitor unused indexes with `pg_stat_user_indexes` (PostgreSQL).                 | Assume indexes are always beneficial.                                          |

---
## **4. Query Optimization**

### **4.1. Key Techniques**
#### **A. Avoid N+1 Queries**
- **Problem**: Fetching related data in loops (e.g., fetching a user’s orders in a loop per user).
- **Solution**: Use **joins** or **batch loading** (e.g., `JOIN`, `IN` clauses, or bulk DML).
  ```sql
  -- ❌ N+1 (slow)
  FOR user IN SELECT * FROM users LOOP
    SELECT * FROM orders WHERE user_id = user.id;
  END LOOP;

  -- ✅ Join (fast)
  SELECT u.*, o.*
  FROM users u
  JOIN orders o ON u.id = o.user_id;
  ```

#### **B. Limit Result Sets**
- Use `LIMIT` to reduce network overhead:
  ```sql
  SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100;
  ```

#### **C. Batch Operations**
- Replace row-by-row updates with bulk DML:
  ```sql
  -- ❌ Slow (1 row at a time)
  UPDATE products SET price = price * 1.1 WHERE category = 'electronics';

  -- ✅ Fast (single statement)
  UPDATE products SET price = price * 1.1 WHERE category = 'electronics';
  ```

#### **D. Use EXPLAIN**
- Analyze query plans to identify bottlenecks:
  ```sql
  EXPLAIN ANALYZE
  SELECT u.name, COUNT(o.id) as order_count
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  GROUP BY u.id;
  ```
  - Look for **Sequential Scan** (missing indexes), **Full Table Scans**, or **Sort** operations.

---

### **4.2. Common Query Pitfalls**
| **Pitfall**               | **Example**                                                                     | **Solution**                                                                   |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **SELECT \***            | Retrieves unnecessary columns.                                                  | Explicitly list columns: `SELECT id, name FROM users`.                      |
| **OR in WHERE Clauses**  | Prevents index usage (try `IN` instead).                                        | Rewrite: `WHERE id IN (1, 2, 3)` instead of `WHERE id = 1 OR id = 2 OR ...` |
| **Not Using LIMIT**       | Returns large datasets unnecessarily.                                           | Always limit results unless you need all rows.                              |

---

## **5. Security Best Practices**

### **5.1. Data Protection**
| **Best Practice**               | **Implementation**                                                                 |
|----------------------------------|------------------------------------------------------------------------------------|
| **Encrypt sensitive data**       | Use `pgcrypto` (PostgreSQL) or `AES_ENCRYPT` (MySQL) for PII.                     |
| **Principle of Least Privilege** | Grant minimal permissions (e.g., `SELECT` only, not `ALTER`).                     |
| **Parameterized Queries**        | Prevent SQL injection with prepared statements:                                     |
  ```sql
  -- ✅ Safe
  PREPARE search_users FROM 'SELECT * FROM users WHERE name = $1 LIMIT 10';
  EXECUTE search_users('John Doe');
  ```                                                                                  |
| **Audit Logs**                  | Log sensitive operations (e.g., `DROP TABLE`, `GRANT`).                            |

---

### **5.2. Backup and Recovery**
| **Strategy**               | **Tools/Commands**                                                                 |
|----------------------------|-----------------------------------------------------------------------------------|
| **Automated Backups**       | Schedule regular backups (e.g., `pg_dump` for PostgreSQL, `mysqldump` for MySQL).   |
| **Point-in-Time Recovery**  | Use WAL (Write-Ahead Log) for crash recovery (PostgreSQL: `RESTORE POINTS`).       |
| **Test Restores**           | Validate backups periodically.                                                     |

---

## **6. Scaling Strategies**

### **6.1. Vertical vs. Horizontal Scaling**
| **Approach**       | **When to Use**                                                                 | **Example**                                                                   |
|--------------------|-----------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Vertical Scaling** | Small workloads with predictable growth.                                         | Upgrade CPU/RAM on a single server.                                          |
| **Horizontal Scaling** | High write/read throughput (e.g., sharding, read replicas).                     | Use **PostgreSQL Citus** or **MySQL Router** for sharding.                   |

---

### **6.2. Read Replicas**
- **Use Case**: Offload read-heavy workloads.
- **Setup**:
  ```sql
  -- PostgreSQL: Configure in postgresql.conf
  wal_level = replica
  max_wal_senders = 5
  ```
- **Tools**:
  - PostgreSQL: `pg_basebackup`
  - MySQL: `mysqldump` + replication setup

---

### **6.3. Connection Pooling**
- **Why?** Reduce connection overhead (databases have finite connection limits).
- **Tools**:
  - PostgreSQL: `pgbouncer`
  - MySQL: `ProxySQL` or `HAProxy`
  - General: **PgBouncer** (connection pooling) or **PgPool-II**.

---

## **7. Monitoring and Maintenance**

### **7.1. Key Metrics to Monitor**
| **Metric**               | **Tool/Command**                                                                 | **Threshold Alerts**                                                      |
|--------------------------|-----------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Query Latency**        | `pg_stat_statements` (PostgreSQL), `MySQL Performance Schema`.                    | >500ms average latency.                                                  |
| **Lock Contention**      | `pg_locks`, `pg_stat_activity` (PostgreSQL).                                      | High `blocked` count.                                                     |
| **Disk I/O**             | `iostat`, `pg_stat_activity` (`blks_read`, `blks_written`).                     | >90% disk utilization.                                                   |
| **Table Bloat**          | `pg_table_size` vs. `pg_size_pretty` (PostgreSQL).                               | Tables >2x larger than expected.                                         |
| **Dead Tuples**         | `pg_stat_all_tables` (`n_dead_tup`).                                             | >10% dead tuples (run `VACUUM`).                                         |

---

### **7.2. Regular Maintenance Tasks**
| **Task**               | **Frequency** | **Tool/Command**                                                                 |
|------------------------|---------------|-----------------------------------------------------------------------------------|
| **Vacuum/Analyze**     | Weekly        | `VACUUM ANALYZE table_name;` (PostgreSQL).                                      |
| **Update Statistics**  | Monthly       | `ANALYZE table_name;` (PostgreSQL).                                             |
| **Rebuild Indexes**    | Quarterly     | `REINDEX TABLE table_name;` (PostgreSQL).                                       |
| **Check for Orphans**  | Ad-hoc        | `pg_locks` + `pg_stat_activity` (find long-running transactions).                |

---

## **8. Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **When to Use**                                                                 |
|--------------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[CQRS](https://microservices.io/)** | Separate read (query) and write (command) models for scalability.                                | High-write systems with complex read patterns (e.g., analytics dashboards).   |
| **[Event Sourcing](https://martinfowler.com/eaaTutorial/m_es.html)** | Store state changes as an immutable log.                                                          | Audit trails, audit compliance, or time-travel debugging.                     |
| **[Database Sharding](https://www.databasesharding.com/)** | Split data across multiple servers (horizontal partitioning).                                      | Global applications with high read/write throughput.                          |
| **[Materialized Views](https://www.postgresql.org/docs/current/materialized-views.html)** | Pre-compute aggregate data for faster queries.                                                   | Read-heavy analytics with slow joins/calculations.                             |
| **[Schema Migration Strategies](https://martinfowler.com/eaaCatalog/schemaMigration.html)** | Zero-downtime schema changes (e.g., backward-compatible alterations).                          | Microservices or polyglot persistence.                                         |

---

## **9. Further Reading**
- **[PostgreSQL Official Docs](https://www.postgresql.org/docs/)** (Indexing, Optimization)
- **[MySQL Performance Blog](https://www.percona.com/blog/)**
- **[Database Design for Performance](https://www.oreilly.com/library/view/database-design-for/9781491965266/)**
- **[SQL Performance Explained](https://use-the-index-luke.com/)**

---
**End of Document** (Word Count: ~950)