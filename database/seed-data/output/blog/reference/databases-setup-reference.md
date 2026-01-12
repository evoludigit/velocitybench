---

# **[Pattern Name: Databases Setup] Reference Guide**

## **Overview**
This guide outlines the foundational **Databases Setup Pattern**, a structured approach to configuring, scaling, and optimizing relational and non-relational database systems. Whether deploying a single-instance database, a multi-node cluster, or a serverless database, this pattern ensures consistency, performance, and maintainability. It covers schema design, connection pooling, backup strategies, security hardening, and deployment automation—critical for both development and production environments.

---

## **1. Key Concepts**
### **1.1 Core Principles**
- **Normalization vs. Denormalization**: Balance between redundancy and query efficiency.
- **ACID vs. BASE**: Trade-offs between consistency and availability in distributed systems.
- **Sharding vs. Partitioning**: Horizontal scaling strategies.
- **Connection Management**: Pools, timeouts, and retries for resilient applications.

### **1.2 Database Models**
| **Model**          | **Use Case**                          | **Example Tools**                     |
|---------------------|---------------------------------------|----------------------------------------|
| **Relational**      | Structured data, transactions        | PostgreSQL, MySQL, SQL Server          |
| **NoSQL**           | Unstructured/semi-structured data     | MongoDB, Cassandra, Redis              |
| **NewSQL**          | Scalable SQL                           | CockroachDB, Google Spanner             |
| **Serverless**      | Event-driven, auto-scaling             | AWS Aurora Serverless, Firebase        |

### **1.3 Deployment Topologies**
| **Topology**        | **Description**                          | **When to Use**                     |
|---------------------|-----------------------------------------|-------------------------------------|
| **Single-node**     | Single instance, no redundancy          | Dev/test environments              |
| **Replicated**      | Primary + standby nodes                 | High availability (HA) deployments  |
| **Sharded**         | Data split across multiple nodes        | Horizontal scaling                  |
| **Federated**       | Multiple databases working in sync      | Microservices architecture          |

---

## **2. Schema Reference**
### **2.1 Database Schema Design**
#### **Relational Example (MySQL/PostgreSQL)**
```sql
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (username),
    INDEX (email)
);

CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'shipped', 'delivered'),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

#### **NoSQL Example (MongoDB)**
```json
{
  "_id": ObjectId("5f8d...abc"),
  "username": "jdoe",
  "email": "jdoe@example.com",
  "orders": [
    {
      "productId": "prod123",
      "orderDate": ISODate("2023-10-01"),
      "status": "delivered"
    }
  ]
}
```

### **2.2 Indexing Strategies**
| **Index Type**      | **Use Case**                          | **Example**                          |
|---------------------|---------------------------------------|--------------------------------------|
| **B-tree**          | Equality/range queries                 | `CREATE INDEX idx_name ON users(name)`|
| **Hash**            | Exact-match lookups                    | Redis keys                            |
| **Full-text**       | Search operations                      | PostgreSQL `tsvector`                 |
| **Composite**       | Multi-column queries                   | `CREATE INDEX idx_user_email ON users(email, created_at)` |

### **2.3 Partitioning Strategies**
| **Method**          | **Purpose**                            | **Example**                          |
|---------------------|----------------------------------------|--------------------------------------|
| **Range**           | Split by time/value ranges             | `PARTITION BY RANGE (year)`          |
| **List**            | Fixed categories                       | `PARTITION BY LIST (region)`         |
| **Hash**            | Even distribution                      | `PARTITION BY HASH (user_id)`        |
| **Key**             | Custom hash-based partitioning         | `PARTITION BY KEY (user_id)`         |

---

## **3. Query Examples**
### **3.1 CRUD Operations (PostgreSQL)**
```sql
-- CREATE
INSERT INTO users (username, email) VALUES ('alice', 'alice@example.com');

-- READ
SELECT * FROM users WHERE status = 'active' LIMIT 10;

-- UPDATE
UPDATE orders SET status = 'shipped' WHERE order_id = 1001;

-- DELETE
DELETE FROM users WHERE user_id = 999;
```

### **3.2 Transaction Management**
```sql
BEGIN;
    INSERT INTO accounts (user_id, balance) VALUES (1, 1000);
    UPDATE accounts SET balance = balance - 500 WHERE user_id = 1;
    INSERT INTO transactions (user_id, amount, type) VALUES (1, -500, 'withdrawal');
COMMIT;
-- OR ROLLBACK; on failure
```

### **3.3 NoSQL Aggregations (MongoDB)**
```javascript
db.orders.aggregate([
  { $match: { status: "delivered", "orderDate": { $gte: new Date("2023-01-01") } } },
  { $group: { _id: "$userId", totalSpent: { $sum: "$amount" } } },
  { $sort: { totalSpent: -1 } }
]);
```

### **3.4connection Pooling (Python - `psycopg2`)**
```python
import psycopg2
from psycopg2 import pool

# Create a connection pool
pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)

# Use a connection from the pool
conn = pool.getconn()
cursor = conn.cursor()
cursor.execute("SELECT * FROM users;")
results = cursor.fetchall()
pool.putconn(conn)  # Return to pool
```

---

## **4. Security Best Practices**
| **Measure**         | **Implementation**                          |
|----------------------|--------------------------------------------|
| **Authentication**   | Use IAM roles, TLS, and rotating credentials. |
| **Encryption**       | Enable TLS for connections; encrypt data at rest (AES-256). |
| **Least Privilege**  | Grant minimal permissions (e.g., `SELECT` only). |
| **Audit Logging**    | Enable PostgreSQL `log_statement = 'all'` or AWS CloudTrail. |
| **Backup Validation**| Test restores periodically (e.g., `pg_dump --blobs`). |

---

## **5. Backup & Recovery**
### **5.1 Relational Backups**
| **Tool**            | **Command**                              | **Notes**                          |
|---------------------|------------------------------------------|------------------------------------|
| **PostgreSQL**      | `pg_dump -U user -d dbname -f backup.sql` | Schedule with `cron` or `pgBackRest`. |
| **MySQL**           | `mysqldump -u user -p dbname > backup.sql` | Use `xtrabackup` for hot backups. |
| **Cloud (AWS RDS)** | Enable **Automated Backups** + **Snapshots**. | Retention: 7+ days.                |

### **5.2 NoSQL Backups**
| **Tool**            | **Command**                              | **Notes**                          |
|---------------------|------------------------------------------|------------------------------------|
| **MongoDB**         | `mongodump --db dbname --out /backups/`   | Use `mongorestore` for recovery.   |
| **DynamoDB**        | AWS **Point-in-Time Recovery**            | Enable for critical tables.        |
| **Redis**           | `redis-cli --rdb /path/to/snapshot.rdb`  | Use `AOF` (Append-Only File) for logs. |

---

## **6. Performance Optimization**
### **6.1 Indexing Tuning**
- **Rule of Thumb**: Index columns used in `WHERE`, `JOIN`, or `ORDER BY`.
- **Avoid Over-Indexing**: Each index slows down `INSERT`/`UPDATE`.

### **6.2 Query Optimization**
- **EXPLAIN ANALYZE**:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM users WHERE name LIKE '% Smith%';
  ```
  - **Bad**: Full table scans (`Seq Scan`).
  - **Good**: Uses B-tree index (`Index Scan`).

- **Avoid `SELECT *`**: Fetch only needed columns.

### **6.3 Connection Management**
- **Pool Size**: Set to `(max_connections / 2)` per app instance.
- **Timeouts**: Configure `wait_timeout` (e.g., MySQL `wait_timeout = 30` seconds).

---

## **7. Deployment Automation**
### **7.1 Infrastructure as Code (IaC)**
| **Tool**            | **Use Case**                              |
|---------------------|------------------------------------------|
| **Terraform**       | Define databases as modules (e.g., RDS). |
| **Ansible**         | Configure DB settings post-deployment.   |
| **Docker**          | Containerize DB for testing (e.g., `postgres:15`). |

### **7.2 CI/CD Pipelines**
1. **Test Schema Changes**: Use `flyway` or `liquibase` for migrations.
   ```yaml
   # GitHub Actions example
   - name: Run migrations
     run: |
       flyway migrate -url=jdbc:postgresql://localhost:5432/mydb \
                    -user=postgres -password=password
   ```
2. **Canary Deployments**: Route 5% of traffic to a new DB version.

---

## **8. Monitoring & Alerts**
| **Metric**          | **Tool**               | **Threshold**                     |
|----------------------|------------------------|------------------------------------|
| **CPU Usage**        | Prometheus/Grafana     | > 80% for 5+ minutes              |
| **Connection Pool**  | `pg_stat_activity`      | > 90% idle connections             |
| **Latency (p99)**    | Datadog                | > 500ms queries                    |
| **Disk Space**       | `df -h`                | < 10% free space                   |

**Alert Rules (Example):**
```promql
# High query latency
rate(pg_query_duration_seconds_count{}[5m]) > 0.1
```

---

## **9. Related Patterns**
1. **[Data Migration]** – Strategies for zero-downtime schema changes.
2. **[Caching Layer]** – Integrate Redis/Memcached for read-heavy workloads.
3. **[Event Sourcing]** – Use databases for audit trails and replayability.
4. **[Multi-Region Replication]** – For global low-latency access.
5. **[Database Sharding]** – Horizontal scaling for large datasets.
6. **[Chaos Engineering for Databases]** – Test failure resilience.

---

## **10. Troubleshooting**
### **10.1 Common Issues & Fixes**
| **Issue**               | **Root Cause**                          | **Solution**                          |
|-------------------------|----------------------------------------|---------------------------------------|
| **Slow Queries**        | Missing indexes                       | Add indexes; use `EXPLAIN`.          |
| **Connection Leaks**    | Unclosed DB connections               | Implement connection pooling.         |
| **Lock Contention**     | Long-running transactions              | Break into smaller transactions.      |
| **Storage Bloat**       | Unused data                          | Archive old data; vacuum (PostgreSQL).|

### **10.2 Tools**
- **PostgreSQL**: `pgbadger`, `pg_stat_statements`.
- **MySQL**: `pt-query-digest`, `perf_schema`.
- **NoSQL**: MongoDB `mongostat`, Cassandra `nodetool cfstats`.

---

## **11. References**
- **Books**:
  - *Database Design for Mere Mortals* (Michael J. Hernandez).
  - *Designing Data-Intensive Applications* (Martin Kleppmann).
- **Tools**:
  - [PostgreSQL Documentation](https://www.postgresql.org/docs/)
  - [AWS RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/WELCOME.html)
- **Communities**:
  - r/postgresql, r/nosql, Stack Overflow [database-tag].

---
**Last Updated:** [Insert Date]
**Version:** 1.2