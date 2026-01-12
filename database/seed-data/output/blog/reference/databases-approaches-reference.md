# **[Pattern] Databases Approaches Reference Guide**

---

### **1. Overview**
The **Databases Approaches Pattern** defines how data persistence, storage, and retrieval are organized in a system. It encompasses foundational patterns for modeling data relationships, query optimization, and scalability. This pattern addresses trade-offs between **relational (SQL), NoSQL, hybrid, or distributed** storage models, ensuring alignment with business logic, performance needs, and evolution requirements.

Key considerations include:
- **Data semantics**: Structured (tables/rows) vs. unstructured (documents/graphs).
- **Consistency vs. availability**: CAP theorem implications (e.g., ACID vs. BASE).
- **Query patterns**: Single-document access vs. complex joins.
- **Scalability**: Vertical vs. horizontal scaling strategies.

Adopting the right approach depends on workload type (OLTP, OLAP), latency constraints, and team expertise.

---

### **2. Schema Reference**
Choose a model based on your data characteristics and access patterns.

| **Approach**       | **Use Case**                          | **Pros**                                                                 | **Cons**                                                                 | **Examples**                          | **Schema Example**                          |
|--------------------|---------------------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|----------------------------------------|---------------------------------------------|
| **Relational (SQL)** | Transactional workloads, complex joins | Strong consistency, enforce constraints, mature tooling                 | Scaling limits, rigid schema         | PostgreSQL, MySQL                      |```CREATE TABLE Users (id SERIAL, name VARCHAR(100));``` |
| **Document (NoSQL)** | Flexible schemas, nested data        | Horizontal scalability, fast read/write | No joins, eventual consistency        | MongoDB, DynamoDB                     |```{ "_id": 1, "name": "Alice", "orders": [...] }```|
| **Key-Value**       | Simple key-value mappings             | Extremely fast, highly available      | No query flexibility, limited data  | Redis, Cassandra                       |`{ "user:123": "{name: Alice}" }`          |
| **Column-Family**   | Time-series, analytical data          | Optimized for writes/compression      | Complex queries, no native joins     | Apache Cassandra, HBase               |`(user:123, name) = "Alice"`                |
| **Graph**           | Relationship-heavy data (e.g., networks) | Traversal optimization, rich queries | High memory usage, less mature       | Neo4j, Amazon Neptune                  |```(Alice)-[:FRIENDS_WITH]->(Bob)```     |
| **Wide-Column**     | Distributed data across nodes        | Scalable reads/writes                 | Schema complexity, eventual consistency | Apache Cassandra                      |```FamilyName→User→Name="Alice"`            |
| **Time-Series**     | Metrics, logs, IoT data               | Optimized for time-based queries       | Limited aggregation capabilities      | InfluxDB, TimescaleDB                 |```measures → {timestamp: 1600000000, value: 42}``` |

---

### **3. Query Examples**
#### **Relational (SQL)**
```sql
-- Retrieve users with orders > $100
SELECT u.name, SUM(o.amount)
FROM Users u
JOIN Orders o ON u.id = o.user_id
WHERE o.amount > 100
GROUP BY u.id;
```

#### **Document (MongoDB)**
```javascript
// Find users with orders > $100 and project specific fields
db.users.aggregate([
  { $unwind: "$orders" },
  { $match: { "orders.amount": { $gt: 100 } } },
  { $project: { name: 1, orderAmount: "$orders.amount" } }
]);
```

#### **Graph (Cypher)**
```cypher
// Find all friends of friends for Alice
MATCH (a:User {name: 'Alice'})-[:FRIENDS_WITH]->(f1)-[:FRIENDS_WITH]->(f2:User)
WHERE NOT (a)-[:FRIENDS_WITH]->(f2)
RETURN DISTINCT f2.name;
```

#### **Key-Value (Redis)**
```bash
# Get user data by ID
GET user:123
# Set user data
SET user:123 '{"name": "Alice", "email": "alice@example.com"}'
```

#### **Time-Series (InfluxDB)**
```sql
-- Query sensor data for last 24 hours
SELECT * FROM sensors
WHERE time > now() - 24h
GROUP BY device_id
FILL(linear);
```

---
### **4. Implementation Considerations**
#### **A. Schema Design**
- **Relational**: Normalize tables (3NF) for minimal redundancy.
- **Document**: Denormalize for performance; embed related data.
- **Graph**: Model entities as nodes; relationships as edges (e.g., `:FRIENDS_WITH`).
- **Time-Series**: Use timestamps as primary keys; avoid aggregations in schema.

#### **B. Query Optimization**
| **Approach**       | **Optimizations**                                                                 |
|--------------------|----------------------------------------------------------------------------------|
| **SQL**            | Indexes (B-tree), partitioning, query caching.                                  |
| **NoSQL**          | Sharding, denormalization, read replicas.                                         |
| **Graph**          | Index nodes/edges, limit traversal depth.                                        |
| **Time-Series**    | Retention policies, downsampling, compression.                                   |

#### **C. Scaling Strategies**
| **Approach**       | **Vertical Scaling**               | **Horizontal Scaling**                |
|--------------------|-------------------------------------|----------------------------------------|
| **SQL**            | Add CPU/RAM to single node          | Replication, read replicas.            |
| **NoSQL**          | Scale individual shards             | Partition data across nodes (e.g., DynamoDB). |
| **Graph**          | N/A (memory-bound)                  | Distribute via partitioning.           |
| **Time-Series**    | N/A                                 | Shard by time/device (e.g., Cassandra). |

#### **D. Trade-offs**
- **Consistency vs. Availability**: SQL (strong consistency); NoSQL (eventual consistency).
- **Flexibility vs. Query Power**: Documents (flexible queries); SQL (complex joins).
- **Latency vs. Throughput**: Key-value (low latency); Graph (high latency for traversals).

---

### **5. Query Examples (Advanced)**
#### **Hybrid Approach (SQL + NoSQL)**
- **Use Case**: Query SQL for structured data; use NoSQL for unstructured metadata.
- **Example**:
  ```sql
  -- SQL: Join users with orders
  SELECT u.*, o.metadata->>'notes' AS order_notes
  FROM Users u
  JOIN Orders o ON u.id = o.user_id;
  ```

#### **Polyglot Persistence**
- Store transactions in PostgreSQL; analytics in Cassandra.
- Example workflow:
  1. Write transaction → PostgreSQL (ACID).
  2. Replicate to Cassandra (for analytics) via CDC (Change Data Capture).

---

### **6. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Repository Pattern**    | Abstraction layer for data access (unifies CRUD operations).                    | When abstracting database access layers. |
| **CQRS**                  | Separate read/write models (optimize queries independently).                    | High-write/read disparity workloads.    |
| **Event Sourcing**        | Store state changes as immutable events.                                       | Audit trails, time-based queries.         |
| **Materialized View**     | Pre-compute query results for performance.                                     | Complex aggregations (e.g., dashboards). |
| **Sharding**              | Partition data across nodes (horizontal scaling).                             | Global distributed systems.              |

---
### **7. Anti-Patterns**
- **Over-normalization**: Excessive joins degrade performance (common in SQL).
- **Schema-less Overuse**: Uncontrolled NoSQL schemas become unmaintainable.
- **Ignoring CAP**: Choosing SQL for globally distributed systems without replication.
- **Not Monitoring**: Blindly trusting default configurations (e.g., Cassandra’s replication factor).

---
### **8. Tools & Libraries**
| **Approach**       | **Recommended Tools**                                                                 |
|--------------------|------------------------------------------------------------------------------------|
| **SQL**            | PostgreSQL, MySQL, Prisma (ORM), Dapper (.NET).                                     |
| **NoSQL**          | MongoDB (ODM: Mongoose), DynamoDB (AWS SDK), Cassandra (CQL).                     |
| **Graph**          | Neo4j (Cypher), Amazon Neptune (Gremlin), TigerGraph.                               |
| **Time-Series**    | TimescaleDB, InfluxDB, Prometheus.                                                 |
| **Hybrid**         | Debezium (CDC), Apache Kafka (event streaming), DataStax Enterprise (Cassandra + SQL). |

---
### **9. Further Reading**
- **Books**:
  - *"Designing Data-Intensive Applications"* (Martin Kleppmann) – CAP theorem, distributed systems.
  - *"NoSQL Distilled"* (Martin Fowler) – NoSQL trade-offs.
- **Papers**:
  - [CAP Theorem](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/) (Gilbert & Lynch).
  - [NewSQL](https://dl.acm.org/doi/10.1145/2660095.2660104) (Stonebraker et al.).
- **Talks**:
  - *"Database Percolator"* (Jepsen.io) – Comparative benchmarks.

---
### **10. Example Workflow: E-Commerce System**
| **Component**       | **Database Approach** | **Why?**                                                                 |
|---------------------|-----------------------|--------------------------------------------------------------------------|
| User Management     | SQL (PostgreSQL)      | Strong consistency for payments.                                          |
| Product Catalog     | Document (MongoDB)    | Flexible attributes (e.g., variants, reviews).                           |
| Orders               | Wide-Column (Cassandra)| High write throughput for transactions.                                  |
| Recommendations     | Graph (Neo4j)         | Traversal of user-item interactions.                                      |
| Analytics            | Time-Series (InfluxDB)| Track sales metrics over time.                                            |

---
**Key Takeaway**: Choose a database approach aligned with your **data access patterns**, **scalability needs**, and **team expertise**. Combine patterns (e.g., CQRS + Polyglot Persistence) for complex systems. Always benchmark and iterate.