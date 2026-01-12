# **[Pattern] Databases Techniques Reference Guide**

---

## **Overview**
This guide provides a structured breakdown of common **database techniques** used to optimize data storage, improve query performance, and ensure scalability. Whether you're working with **relational databases (SQL)**, **NoSQL databases**, or distributed systems, mastering these techniques helps enforce best practices in schema design, indexing, sharding, replication, and query optimization. We cover **key patterns** like normalization, denormalization, partitioning, caching, and write-behind, along with their trade-offs and use cases.

---

## **Key Concepts & Implementation Details**

### **1. Data Model Patterns**
| **Pattern**         | **Description**                                                                 | **Use Case**                                                                 |
|----------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Normalization**    | Organizing data into tables to minimize redundancy via **1NF, 2NF, 3NF**.     | Traditional relational databases where data integrity is critical.            |
| **Denormalization**  | Deliberately duplicating data to reduce joins and improve read speed.         | High-performance read-heavy applications (e.g., analytics, reporting).       |
| **Schema-less (NoSQL)** | Schemas are dynamic, allowing flexible data structures.                     | Unstructured or semi-structured data (e.g., JSON, documents, graphs).       |
| **Event Sourcing**   | Storing state changes as an immutable sequence of events.                     | Audit trails, time-based queries, and CQRS architectures.                   |

---

### **2. Indexing & Query Optimization**
#### **Indexing Techniques**
| **Type**            | **Description**                                                                 | **When to Use**                                                                 |
|---------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **B-tree Index**    | Balanced tree structure for range queries and equality checks.                  | Default for most relational databases (PostgreSQL, MySQL).                   |
| **Hash Index**      | Uses a hash function for O(1) lookups (no range queries).                      | Exact-match queries (e.g., caching key-value stores).                        |
| **Bitmap Index**    | Uses bitmaps for low-cardinality columns (e.g., flags, categories).            | Analytics tables with many filters.                                           |
| **Full-Text Index** | Optimized for text search (e.g., `LIKE %pattern%`).                        | Search engines, document databases.                                           |

#### **Query Optimization Tips**
- **Avoid `SELECT *`** – Fetch only required columns.
- **Use `EXPLAIN ANALYZE`** – Analyze query execution plans in PostgreSQL/MySQL.
- **Limit `JOIN` depth** – Deep joins degrade performance.
- **Leverage `LIMIT`** – Paginate results instead of fetching all rows.

---

### **3. Data Partitioning & Sharding**
#### **Partitioning**
| **Strategy**        | **Definition**                                                                 | **Example**                                                                 |
|---------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Range Partitioning** | Splits data by numeric/date ranges (e.g., `year` columns).               | Log tables by year (`partition by range (created_at)`).                     |
| **Hash Partitioning** | Distributes data using a hash function (e.g., `hash(id) % N`).             | Evenly distribute load across nodes.                                        |
| **List Partitioning** | Groups data by predefined lists (e.g., `country` in a global table).      | Multi-region deployments.                                                    |
| **Composite Partitioning** | Combines multiple strategies (e.g., `range + hash`).                  | Large-scale analytics with time + key-based splits.                         |

#### **Sharding**
- **Horizontal scaling** by splitting data across multiple machines.
- **Common sharding keys**: `user_id`, `geo-location`, `time-based`.
- **Trade-offs**:
  - **Pros**: Improved read/write throughput.
  - **Cons**: Complex joins, data migration overhead.

---

### **4. Replication & High Availability**
| **Technique**       | **Description**                                                                 | **Use Case**                                                                 |
|---------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Master-Slave Replication** | Read replicas offload read queries.                                          | Scaling read-heavy applications.                                             |
| **Multi-Master Replication** | Multiple writable nodes (requires conflict resolution).                    | Geo-distributed databases (e.g., Cassandra).                                |
| **Synchronous Replication** | Writes commit only after replicating to all nodes.                          | High durability (but lower write throughput).                               |
| **Asynchronous Replication** | Writes commit immediately; replication happens later.                       | High write throughput (risk of data loss if node fails).                    |
| **Causal Consistency** | Ensures operations respect causal order (e.g., CRDTs).                      | Distributed systems with eventual consistency.                              |

---

### **5. Caching Strategies**
| **Cache Type**      | **Implementation**                                                             | **Best For**                                                                 |
|---------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **In-Memory Cache** | Redis, Memcached (key-value store).                                           | Microsecond latency for frequent reads.                                       |
| **Query Caching**   | Storing SQL query results (e.g., PostgreSQL `pg_cache` extension).          | Expensive analytical queries.                                                |
| **Application-Level Cache** | Caching computed results in the app.                           | Reducing redundant calculations (e.g., user profiles).                       |
| **CDN Caching**     | Edge caching for static assets.                                               | Web applications with global traffic.                                       |

**Cache Invalidation Rules**:
- **Time-based**: Expire after `N` seconds (e.g., `cache.set("key", value, 3600)`).
- **Event-based**: Invalidate on write (e.g., Redis `PUB/SUB` for cache updates).
- **Lazy Loading**: Load cache only when accessed.

---

### **6. Write-Behind & Eventual Consistency**
- **Write-Behind**: Queue writes (e.g., Kafka, RabbitMQ) before persistence.
- **Use Cases**:
  - Decoupling services (e.g., order processing → inventory update).
  - Handling spikes in write load.
- **Conflict Resolution**:
  - **Last Write Wins (LWW)**: Simple but may lose updates.
  - **Version Vectors**: Track causality for accurate merges.
  - **Operational Transformation (OT)**: Used in collaborative editing (e.g., Google Docs).

---

## **Schema Reference**
Below are common schema patterns with trade-offs.

| **Pattern**         | **Schema Example**                                                                 | **Pros**                                  | **Cons**                                  |
|----------------------|-----------------------------------------------------------------------------------|------------------------------------------|------------------------------------------|
| **Star Schema**     | Fact table → Dimension tables (e.g., `sales` → `products`, `customers`).       | Optimized for OLAP (analytics).         | Not ideal for transactional workloads. |
| **Snowflake Schema**| Normalized star schema (further decomposed dimensions).                          | Reduces redundancy.                     | More complex joins.                     |
| **Wide Column Store** | Columnar storage (e.g., Cassandra, Parquet).                                   | Fast analytical queries.                | Poor for row-level transactions.        |
| **Document Store**  | JSON/BSON documents (e.g., MongoDB).                                            | Flexible schema, nested data.            | Harder to query cross-field relationships. |

---

## **Query Examples**
### **SQL Optimization**
```sql
-- ❌ Inefficient: Full table scan + no index
SELECT * FROM users WHERE email LIKE '%@gmail.com' LIMIT 10;

-- ✅ Optimized: Uses full-text index
CREATE INDEX idx_user_email ON users USING GIN (to_tsvector('english', email));
SELECT * FROM users WHERE email @@ to_tsquery('gmail');
```

### **NoSQL (MongoDB)**
```javascript
-- ❌ Nested lookup (slow)
db.orders.find({ user: userId }, { items: 1 });

-- ✅ Denormalized (faster read)
db.orders.findOne({ user: userId });
// Result includes embedded items
```

### **Caching (Redis)**
```bash
# Set cache (TTL = 300s)
SET user:123 "{\"name\":\"Alice\"}" EX 300

# Get cached value
GET user:123
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **[CQRS](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs)** | Separates read (queries) and write (commands) paths.                      | Complex event-driven systems.                                                  |
| **[Event Sourcing](https://martinfowler.com/eaaToc.html)** | Stores state changes as events.                                           | Audit logs, time travel debugging.                                             |
| **[Database Per Service](https://microservices.io/patterns/data/database-per-service.html)** | Isolates data per microservice.                                  | Decentralized ownership in microservices.                                     |
| **[Materialized View](https://use-the-index-luke.com/sql/materialized-views)** | Pre-computes query results.                                              | Repeated complex aggregations.                                                 |
| **[Read Replicas](https://www.postgresql.org/docs/current/replication.html)** | Scales read operations.                                                      | High-traffic read-heavy applications.                                         |

---

## **Best Practices Summary**
1. **Start normalized**, denormalize only when necessary.
2. **Index strategically**: Avoid over-indexing (slows writes).
3. **Partition large tables** to improve query performance.
4. **Cache aggressively** for read-heavy workloads.
5. **Use connection pooling** (e.g., PgBouncer, HikariCP).
6. **Monitor slow queries** with tools like `pg_stat_statements`, Slow Query Log.
7. **Consider NoSQL** for unstructured data or horizontal scaling needs.

---
**Further Reading**:
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Designing Data-Intensive Applications](https://dataintensive.net/) (Book)
- [Base vs. ACID](https://www.infoq.com/news/2011/08/ACID-vs-BASE) (Trade-offs)