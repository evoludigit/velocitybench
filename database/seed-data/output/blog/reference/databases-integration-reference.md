---
# **[Pattern] Databases Integration – Reference Guide**

---

## **1 Overview**
The **Databases Integration** pattern ensures seamless connectivity and data consistency across multiple databases in a distributed system. It standardizes how disparate data sources—such as relational databases (e.g., PostgreSQL), NoSQL databases (e.g., MongoDB), or cloud-based solutions (e.g., AWS RDS)—interact while maintaining **ACID compliance**, **performance**, and **scalability**. This guide covers core concepts, schema design, query patterns, and best practices for integrating databases in enterprise applications.

---

## **2 Key Concepts & Implementation Details**

### **2.1 Core Principles**
| **Concept**               | **Description**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| **Schema Synchronization** | Ensures tables/collections align across systems (e.g., foreign keys, constraints). |
| **Data Partitioning**     | Splits data across databases to optimize performance (sharding, replication).   |
| **Event-Driven Sync**     | Uses change data capture (CDC) for real-time updates via Kafka, Debezium, etc. |
| **Query Federation**      | Aggregates results from multiple databases via middleware (e.g., Presto, Apache Athena). |
| **Idempotency**           | Prevents duplicate operations in distributed transactions (e.g., UUIDs, retries). |

### **2.2 Integration Modes**
| **Mode**                  | **Use Case**                                                                 | **Tools/Techniques**                          |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Direct Connection**     | Low-latency reads/writes to a single database.                            | JDBC, ODBC, native drivers.                   |
| **API Gateway**           | Centralized access layer for multi-database queries.                       | REST/gRPC APIs, GraphQL (e.g., Apollo, Hasura).|
| **Change Data Capture (CDC)** | Real-time sync between databases.                                           | Debezium, Kafka Connect.                     |
| **Batch Processing**      | Offline sync for large datasets (e.g., ETL).                              | Airflow, Spark.                              |

---
## **3 Schema Reference**

### **3.1 Standardized Schema Design**
| **Database Type**       | **Key Tables/Collections**       | **Constraints**                          | **Example Schema**                                                                 |
|-------------------------|-----------------------------------|------------------------------------------|-----------------------------------------------------------------------------------|
| **PostgreSQL**          | `users`, `orders`, `products`     | `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`   | ```sql CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE); ``` |
| **MongoDB**             | `users`, `orders` (embedded docs) | `_id` (auto-generated), indexes        | ```json { "_id": ObjectId("..."), "name": "John", "orders": [ ... ] }```            |
| **Amazon DynamoDB**     | `User` (partition key: `userId`)  | Partition/sort keys, TTL                | ```aws CreateTable(AttributeDefinitions: [{...}], KeySchema: [{...}] )```           |
| **Google Cloud SQL**    | `transactions` (sharded by `region`) | Partitioning, read replicas           | ```sql CREATE TABLE transactions (id INT, region VARCHAR(50), PRIMARY KEY (region, id)); ``` |

---
### **3.2 Cross-Database Compatibility**
| **Feature**          | **PostgreSQL**       | **MongoDB**          | **DynamoDB**       |
|----------------------|----------------------|----------------------|--------------------|
| **Transactions**     | ACID (default)       | Multi-doc ACID (v6+) | Conditional writes  |
| **Joins**            | Native (SQL)         | Manual (application) | Denormalized       |
| **Indexing**         | B-tree, GIN          | TTL, text, geospatial| GSIs, LSIs         |
| **Query Language**   | SQL                  | JSON-based (`find()`, `aggregate()`)   | Query API          |

---
## **4 Query Examples**

### **4.1 Joining Data Across Databases (SQL + NoSQL Hybrid)**
**Scenario**: Retrieve a user’s orders from PostgreSQL and their shipping address (stored in MongoDB).

#### **PostgreSQL Query (Orders)**
```sql
SELECT order_id, user_id, amount
FROM orders
WHERE user_id = 'user_123';
```

#### **MongoDB Query (Shipping Address)**
```javascript
db.users.findOne(
  { "userId": "user_123" },
  { "shipping.address": 1 }
);
```

#### **Application-Level Join (Python Example)**
```python
# Pseudocode: Merge results in the application layer
orders = execute_postgres_query("""SELECT * FROM orders WHERE user_id = %s""", user_id)
user_address = execute_mongodb_query("""
    { "userId": user_id, "_id": False, "shipping.address": True }
""")
result = { "orders": orders, "address": user_address["shipping"]["address"] }
```

---

### **4.2 Change Data Capture (CDC) Example (Debezium + Kafka)**
**Scenario**: Sync PostgreSQL `users` table changes to MongoDB in real time.

1. **Debezium Source Connector (PostgreSQL → Kafka)**
   ```yaml
   connector.class: "io.debezium.connector.postgresql.PostgresConnector"
   database.hostname: "postgres-host"
   database.port: "5432"
   database.dbname: "mydb"
   topic.prefix: "db"
   ```

2. **MongoDB Sink Connector (Kafka → MongoDB)**
   ```yaml
   connector.class: "com.mongodb.kafka.connect.MongoSinkConnector"
   tasks.max: "1"
   connection.uri: "mongodb://mongo-host:27017"
   topic: "db.mydb.users"
   ```

3. **Sample Kafka Message (JSON)**
   ```json
   {
     "before": { "name": "Old Name" },
     "after": { "name": "New Name", "id": "user_123" },
     "op": "update",
     "source": { "version": "1.0", "db": "mydb", "table": "users" }
   }
   ```

---

### **4.3 Federated Queries (Presto)**
**Scenario**: Query orders from PostgreSQL and products from MongoDB via Presto.

```sql
SELECT
  p.product_id,
  o.order_id,
  p.price,
  o.user_id
FROM
  postgres.default.orders o
CROSS JOIN LATERAL
  mongo.db.products p
WHERE
  p._id = o.product_id;
```

---

## **5 Performance Optimization**
| **Technique**               | **Description**                                                                 | **Example Tools**                          |
|-----------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **Connection Pooling**      | Reuse database connections to reduce overhead.                               | HikariCP, PgBouncer.                      |
| **Read Replicas**           | Offload read queries to replicas.                                           | PostgreSQL replicas, DynamoDB global tables.|
| **Caching**                 | Cache frequent queries (e.g., user profiles).                                | Redis, Memcached.                          |
| **Query Optimization**      | Use EXPLAIN to analyze and optimize slow queries.                            | PostgreSQL `EXPLAIN ANALYZE`, MongoDB `explain()`. |
| **Batching**                | Group writes (e.g., bulk inserts) to reduce network calls.                  | JDBC batch updates, MongoDB bulk API.     |

---

## **6 Error Handling & Retries**
| **Scenario**               | **Solution**                                                                 | **Example**                                  |
|----------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **Temporary Failures**     | Exponential backoff for retries.                                            | `retry: backoff(max_retries=3, delay=1s)`   |
| **Idempotent Operations**  | Use unique IDs to avoid duplicates (e.g., UUIDs).                          | `INSERT ... ON CONFLICT DO NOTHING` (PostgreSQL). |
| **Dead Letter Queue (DLQ)** | Route failed CDC events to a queue for manual review.                       | Kafka DLQ + Sentry for alerts.              |

---

## **7 Security Considerations**
| **Risk**                   | **Mitigation**                                                                 | **Tools**                                  |
|----------------------------|-------------------------------------------------------------------------------|--------------------------------------------|
| **Unauthorized Access**    | Role-based access control (RBAC) and IAM policies.                            | PostgreSQL `GRANT`, MongoDB roles.         |
| **Data Leakage**           | Encrypt sensitive fields (e.g., PII) at rest/in-transit.                     | AWS KMS, MongoDB Field-Level Encryption.   |
| **Injection Attacks**      | Use parameterized queries and ORMs.                                          | SQLAlchemy, Prisma.                        |
| **Network Latency**        | Use VPNs or private endpoints for database access.                           | AWS VPC Peering, TLS.                      |

---

## **8 Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                          |
|----------------------------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **[CQRS]**                       | Separate read/write models for scalability.                                    | High-throughput systems (e.g., e-commerce). |
| **[Event Sourcing]**             | Store state changes as a sequence of events.                                  | Audit trails, complex workflows.          |
| **[Polyglot Persistence]**       | Use multiple databases for different data models.                            | Mixed workloads (e.g., SQL for transactions, NoSQL for analytics). |
| **[Saga Pattern]**               | Manage distributed transactions via compensating actions.                      | Microservices with eventual consistency.  |
| **[Sharding]**                   | Split data across databases to improve performance.                           | Global applications with high scale.      |

---
**References**:
- Debezium Documentation: [https://debezium.io/documentation/](https://debezium.io/documentation/)
- Presto Federated Queries: [https://prestodb.io/docs/current/federation.html](https://prestodb.io/docs/current/federation.html)
- AWS DynamoDB Best Practices: [https://aws.amazon.com/dynamodb/faqs/](https://aws.amazon.com/dynamodb/faqs/)

---
**Notes**:
- For **real-time sync**, prioritize CDC tools like Debezium or AWS DMS.
- For **batch processing**, use ETL pipelines (e.g., Airflow + Spark).
- Always test schema migrations in a staging environment.