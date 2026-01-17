# **[Pattern] NoSQL Database Patterns – Reference Guide**

---

## **Overview**
NoSQL databases offer flexible, scalable, and high-performance data storage tailored for modern applications. Unlike relational databases, they emphasize **schema-less design**, **horizontal scalability**, and **optimized query patterns** for specifically structured data.

This reference guide outlines key **NoSQL schema design principles**, **query optimization techniques**, and **common patterns** (e.g., wide-column, document, key-value) to ensure efficient data modeling, indexing, and performance. Best practices include leveraging **denormalization**, **partitioning**, and **query-specific optimizations** while avoiding common anti-patterns such as over-normalization or inefficient joins.

---

## **Schema Reference**

### **1. Core NoSQL Data Models & Schema Structures**

| **Pattern**          | **Description**                                                                                     | **Use Case**                                                                                     | **Example Data Model**                                                                 |
|----------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Document**         | Semi-structured JSON/XML data stored as BSON/JSON documents.                                          | Content management, catalogs, user profiles.                                                   | `{ "_id": "user1", "name": "Alice", "orders": [{"id": "101", "date": "2023-10-01"}] }` |
| **Key-Value**        | Simple key-value pairs with minimal structure.                                                      | Session storage, caching, shopping carts.                                                       | `{ "key": "cart123", "value": { "items": ["101", "102"] } }`                              |
| **Wide-Column**      | Rows partitioned into columns (e.g., Cassandra, ScyllaDB) with flexible schemas per row.             | Time-series data, logs, analytics.                                                              | `(user_id, event_date => { "action": "login", "timestamp": "2023-10-02" })`          |
| **Graph**            | Nodes (entities) connected by edges (relationships) via properties.                                   | Social networks, fraud detection, recommenders.                                                | `{ "user1": { "friends": ["user2", "user3"] } }`                                      |
| **Column-Family**    | Similar to wide-column but with predefined column families (e.g., HBase).                          | Distributed search, IoT telemetry.                                                              | `{ "user_sessions": [{"sessionId": "abc123", "metrics": {"latency": 100}} ] }`          |

---

### **2. Key Schema Optimization Techniques**

| **Technique**        | **Description**                                                                                     | **When to Apply**                                                                              |
|----------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Denormalization**  | Repeating data to avoid joins (e.g., embedding documents).                                         | When read-heavy operations dominate and join overhead is costly.                               |
| **Partitioning**     | Distributing data across nodes by key (e.g., `user_id`).                                           | For high-throughput writes and horizontal scaling.                                             |
| **Sharding**         | Splitting data across multiple machines (e.g., by geographic region).                               | Large-scale applications (e.g., global apps with regional data isolation).                     |
| **TTL (Time-to-Live)**| Auto-expiring data by timestamp (e.g., session cache).                                             | Temporary data (e.g., analytics, logs).                                                        |
| **Secondary Indexes**| Non-primary keys for faster lookups (e.g., `email` or `status` fields).                           | When queries filter on non-primary fields (e.g., `WHERE status = "active"`).                 |

---

## **Query Examples**

### **1. Document Store (MongoDB)**
**Model:**
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "Alice",
  "orders": [
    { "orderId": "101", "amount": 99.99 },
    { "orderId": "102", "amount": 49.99 }
  ]
}
```

**Queries:**
| **Goal**                          | **Query (MongoDB)**                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------------|
| Find all users with orders > $50  | `db.users.find({ "orders.amount": { $gt: 50 } })`                                    |
| Aggregate total orders per user   | `db.users.aggregate([{ $unwind: "$orders" }, { $group: { _id: "$_id", total: { $sum: "$orders.amount" } } }])` |
| Update a user’s email             | `db.users.updateOne( { "_id": ObjectId("507f1f77bcf86cd799439011") }, { $set: { "email": "alice@example.com" } } )` |

---

### **2. Wide-Column Store (Cassandra)**
**Model:**
```sql
CREATE TABLE orders_by_user (
  user_id UUID,
  order_id UUID,
  amount DECIMAL,
  timestamp TIMESTAMP,
  PRIMARY KEY ((user_id), order_id, timestamp)
) WITH CLUSTERING ORDER BY (order_id DESC);
```

**Queries:**
| **Goal**                          | **Query (Cassandra CQL)**                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------------------|
| Get all orders for user           | `SELECT * FROM orders_by_user WHERE user_id = ?;`                                          |
| Get orders in a time range        | `SELECT * FROM orders_by_user WHERE user_id = ? AND timestamp > '2023-10-01' AND timestamp < '2023-10-03';` |
| Insert a new order                | `INSERT INTO orders_by_user (user_id, order_id, amount, timestamp) VALUES (?, ?, ?, toTimestamp(now()));` |

---
### **3. Key-Value Store (Redis)**
**Model:**
```bash
SET user:123 '{"name": "Bob", "age": 30}'
```

**Commands:**
| **Goal**                          | **Command**                                                                              |
|-----------------------------------|-------------------------------------------------------------------------------------------|
| Get user data                     | `GET user:123`                                                                           |
| Set TTL (expiry)                  | `SETEX user:123 3600 '{"name": "Bob"}'` (expires in 1 hour)                            |
| Increment a counter               | `INCR user:123:visits` (atomic counter)                                                  |

---
### **4. Graph Database (Neo4j)**
**Model:**
```cypher
CREATE (alice:User {id: "1", name: "Alice"})
CREATE (bob:User {id: "2", name: "Bob"})
CREATE (alice)-[:FRIENDS_WITH]->(bob)
```

**Queries:**
| **Goal**                          | **Cypher Query**                                                                          |
|-----------------------------------|-------------------------------------------------------------------------------------------|
| Find friends of Alice             | `MATCH (a:User {id: "1"})-[:FRIENDS_WITH]->(f) RETURN f;`                                |
| Find mutual friends               | `MATCH (a:User {id: "1"})-[:FRIENDS_WITH]->(m)-[:FRIENDS_WITH]->(b:User {id: "2"}) RETURN m;` |
| Add a new friendship               | `CREATE (a:User {id: "1"})-[:FRIENDS_WITH]->(newUser:User {id: "3"})`                   |

---

## **Common Anti-Patterns & Mitigations**

| **Anti-Pattern**               | **Risk**                                                                                     | **Mitigation**                                                                                   |
|---------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| Over-normalization              | Joins become bottlenecks in NoSQL (which lacks SQL joins).                                  | Denormalize data (e.g., embed related documents).                                              |
| Unbounded wide-column queries   | Scans entire partitions (e.g., `SELECT * FROM table`).                                      | Use `LIMIT` and clustering columns for pagination.                                            |
| No secondary indexes            | Slow queries on non-primary keys (e.g., `WHERE status = "active"`).                          | Add composite indexes or materialized views.                                                   |
| Ignoring TTL for cache          | Memory bloat from unused data (e.g., Redis keys).                                           | Set TTL for ephemeral data (e.g., sessions, logs).                                            |
| Monolithic shards               | Single-shard bottlenecks under high load.                                                    | Design shards by high-cardinality keys (e.g., `user_id`).                                    |

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                             | **When to Use**                                                                               |
|---------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **[Event Sourcing](link)**      | Store state changes as immutable events for auditability.                                    | Financial systems, audit logs, time-sensitive data.                                         |
| **[CQRS](link)**                | Separate read (views) and write (commands) models for scalability.                           | High-throughput apps with complex queries (e.g., e-commerce).                              |
| **[Micro-Batching](link)**      | Group writes (e.g., Kafka) to reduce overhead.                                               | High-write-volume systems (e.g., IoT, clickstreams).                                       |
| **[Polyglot Persistence](link)**| Mix NoSQL and SQL databases for different access patterns.                                  | Apps needing both structured (SQL) and flexible (NoSQL) data storage.                        |
| **[Idempotent Operations](link)**| Ensure repeatable writes without side effects.                                                | Distributed systems with retries or eventual consistency.                                  |

---
## **Further Reading**
1. **Books**:
   - *NoSQL Distilled* – Martin Fowler (patterns and trade-offs).
   - *Designing Data-Intensive Applications* – Martin Kleppmann (NoSQL fundamentals).
2. **Tools**:
   - **MongoDB Compass** (GUI for documents).
   - **CQL Shell** (Cassandra query tool).
   - **Neo4j Browser** (graph database client).
3. **Resources**:
   - [NoSQL Database Comparison Chart](https://db-engines.com/en/system/Cassandra%3BMongoDB%3BRedis)
   - [CNCF NoSQL Landscape](https://landscape.cncf.io/?search=nosql)

---
**© [Your Company/Organization]**
*Last updated: [Date]*