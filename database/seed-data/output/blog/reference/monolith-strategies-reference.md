**[Pattern] Reference Guide: Monolith Strategies**

---

### **Overview**
The **Monolith Strategies** pattern organizes a *single database schema* (or shard) into logically partitioned tables, enabling horizontal scalability while maintaining data consistency and centralized management. Unlike traditional monoliths, this approach deconstructs data into *strategically segmented tables* (e.g., by tenant, region, or feature) to optimize query performance, reduce contention, and simplify scaling. It’s ideal for systems where:
- **Single-writer/multi-reader** access patterns dominate (e.g., SaaS platforms, analytics tools).
- **Strong consistency** is required within partitions but eventual consistency can be tolerated across them.
- **Schema flexibility** is needed without full table sharding complexity.

Key tradeoffs include *increased schema complexity* and *partition-boundary management*, but it balances flexibility with performance better than monolithic tables alone.

---

### **Schema Reference**
The pattern divides data into **strategically grouped tables** according to a *partitioning key* (e.g., `tenant_id`, `region`, or `feature_flag`). Below is a **general schema template** for common use cases:

| **Partition Key**       | **Table Name**               | **Description**                                                                 | **Example Keys**                     |
|-------------------------|------------------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **Tenant-based**        | `tenants_users`              | User data segmented by tenant (e.g., SaaS).                                    | `tenant_id (PK), user_id, email`     |
|                         | `tenants_orders`             | Orders tied to a specific tenant tenant.                                        | `tenant_id (PK), order_id, amount`   |
|                         | `global_users`               | System-wide users (admins, support) with no tenant partitioning.                | `user_id (PK), role`                 |
| **Region-based**        | `regions_products`           | Products partitioned by geographic region for latency optimization.              | `region_id (PK), product_id, price`  |
|                         | `regions_analytics`          | Analytics data isolated per region to reduce cross-partition queries.            | `region_id (PK), event_id, metrics`  |
| **Feature-based**       | `feature_a_events`           | Events logged for a specific feature flag (e.g., "PremiumUI").                 | `feature_id (PK), event_id, payload` |
| **Time-based**          | `time_shard_users`           | Users split by time ranges (e.g., monthly) for archival or compliance.          | `shard_date (PK), user_id, name`     |

#### **Key Schema Rules:**
1. **Partition Key as Primary Key (PK):**
   - The partitioning key (e.g., `tenant_id`) is included in the PK to enforce isolation.
   - *Avoid composite PKs* unless necessary to maintain referential integrity.

2. **Foreign Keys Across Partitions:**
   - Use **partition-aware foreign keys** (e.g., `tenant_id` in `tenants_orders` referencing `tenants_users`).
   - *Global hashes* (e.g., UUIDs) should be avoided within a partition to prevent skew.

3. **Denormalization:**
   - Duplicate frequently accessed data within partitions (e.g., `tenant_metadata` embedded in `tenants_users`).
   - Use **materialized views** for analytics-heavy partitions.

4. **Indexing:**
   - Indexes should include the partition key + frequently queried columns (e.g., `CREATE INDEX idx_orders_tenant_amount ON tenants_orders(tenant_id, amount)`).

---

### **Implementation Details**

#### **1. Partitioning Strategies**
Choose a strategy based on access patterns:
| **Strategy**          | **Use Case**                          | **Pros**                                  | **Cons**                                   |
|-----------------------|---------------------------------------|-------------------------------------------|-------------------------------------------|
| **Tenant Partitioning** | SaaS applications with isolated tenants. | Strong tenant isolation, simple scaling. | Hard to query cross-tenant data.          |
| **Region Partitioning** | Global applications with latency needs. | Localized reads/writes, lower latency.   | Complex replication across regions.       |
| **Feature Partitioning** | Modular features (e.g., A/B testing). | Isolate feature-specific data.            | Overhead from managing many small tables.|
| **Time-Based Sharding** | Time-series or archival data.         | Efficient for historical queries.        | Requires re-sharding for time windows.   |

#### **2. Query Optimization**
- **Partition-Prone Queries:**
  ```sql
  -- Efficient: Filter by partition key first.
  SELECT * FROM tenants_users WHERE tenant_id = 1234 AND status = 'active';
  ```
- **Avoid Cross-Partition Queries:**
  ```sql
  -- Inefficient: Scans all tenants (anti-pattern).
  SELECT COUNT(*) FROM tenants_users WHERE status = 'active';
  ```
  *Workaround:* Use application logic to aggregate results per tenant.

- **Batch Operations:**
  Use **CTE (Common Table Expressions)** or temporary tables for multi-partition updates:
  ```sql
  WITH updated_users AS (
    UPDATE tenants_users
    SET last_login = NOW()
    WHERE tenant_id = 1234 AND last_login < '2023-01-01'
    RETURNING *
  )
  SELECT * FROM updated_users; -- Process results in batches.
  ```

#### **3. Scaling Considerations**
- **Read Scaling:**
  - Replicate partitioned tables **regionally** (e.g., `regions_products` in `us-east`, `eu-west`).
  - Use **read replicas** for analytical queries (e.g., `regions_analytics`).
- **Write Scaling:**
  - **Shard writes** by partition key (e.g., `tenants_orders` writes go to the tenant’s partition).
  - **Queue writes** (e.g., Kafka) to balance load across partitions.

#### **4. Migration to Monolith Strategies**
1. **Assess Partitioning Needs:**
   - Identify hotspots (e.g., `tenant_id = 1` has 80% of writes).
   - Use query logs to detect cross-partition queries.
2. **Refactor Schema:**
   - Split monolithic tables into partitioned ones (e.g., `users` → `tenants_users`, `global_users`).
   - *Tooling:* Use database migration tools like **Flyway** or **Liquibase**.
3. **Update Applications:**
   - Replace joins across partitions with **application-level aggregation**.
   - Example: Replace `SELECT u.name, o.amount FROM users u JOIN orders o` with:
     ```python
     # Pseudocode: Fetch users and orders separately, then merge.
     users = db.query("tenants_users WHERE tenant_id = 1234")
     orders = db.query("tenants_orders WHERE tenant_id = 1234")
     ```

---

### **Query Examples**

#### **1. Basic CRUD in Partitioned Tables**
```sql
-- Create (partition-aware)
INSERT INTO tenants_users (tenant_id, user_id, email)
VALUES (1234, 'user-5678', 'user@example.com');

-- Read (filtered by partition)
SELECT * FROM tenants_users
WHERE tenant_id = 1234 AND user_id = 'user-5678';

-- Update (partitioned)
UPDATE tenants_orders
SET status = 'shipped'
WHERE tenant_id = 1234 AND order_id = 'order-101';

-- Delete (partitioned)
DELETE FROM regions_products
WHERE region_id = 'us-west' AND product_id = 'prod-999';
```

#### **2. Aggregations Within Partitions**
```sql
-- Sum orders by tenant (efficient)
SELECT tenant_id, SUM(amount)
FROM tenants_orders
GROUP BY tenant_id;

-- Count active users per tenant
SELECT tenant_id, COUNT(*)
FROM tenants_users
WHERE status = 'active'
GROUP BY tenant_id;
```

#### **3. Cross-Partition Joins (Avoid When Possible)**
```sql
-- Inefficient: Forces a cross-partition scan.
SELECT u.tenant_id, o.amount
FROM global_users u
JOIN tenants_orders o ON u.user_id = o.user_id;
```
*Alternative:* Use a **denormalized `global_user_tenant_map`** table:
```sql
CREATE TABLE global_user_tenant_map (
  user_id VARCHAR(36) PRIMARY KEY,
  tenant_id INT NOT NULL,
  FOREIGN KEY (tenant_id) REFERENCES tenants_users(tenant_id)
);
```

---

### **Related Patterns**

1. **Sharding:**
   - *Difference:* Sharding splits data across *multiple databases*, while Monolith Strategies keeps tables in a single schema.
   - *When to use together:* Start with Monolith Strategies for schema flexibility, then shard individual partitions (e.g., `tenants_users` → sharded by `tenant_id`).

2. **Composite Database:**
   - *Use when:* You need mixed consistency models (e.g., strong consistency for orders, eventual consistency for analytics).
   - *Example:* Combine a partitioned SQL database (orders) with a NoSQL store (clickstream data).

3. **Denormalization:**
   - *Complement:* Denormalize *within partitions* to avoid joins (e.g., embed `tenant_metadata` in `tenants_users`).

4. **Event Sourcing:**
   - *Use when:* Your system requires auditability across partitions.
   - *Example:* Store partition-bound events in an append-only log (e.g., Kafka) for replayability.

5. **Database Per Tenant:**
   - *Alternative:* Isolate tenants in *separate databases* if you need strict isolation and don’t require cross-tenant queries.
   - *Tradeoff:* Higher operational complexity (e.g., managing multiple DBs).

---
### **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Risk**                                  | **Fix**                                  |
|----------------------------------|-------------------------------------------|------------------------------------------|
| Ignoring partition key in queries | Hotspots, poor performance.               | Always filter by partition key first.    |
| Over-partitioning                | Schema bloat, high maintenance cost.      | Start with 2–4 partitions; merge if needed. |
| Cross-partition joins for critical paths | High latency, scalability limits.       | Denormalize or restructure schema.        |
| Static partitions                | Inflexible scaling (e.g., fixed tenant IDs). | Use dynamic partitioning (e.g., hash-based). |

---
### **Tools & Libraries**
- **Database:**
  - PostgreSQL (with `pg_shard` or custom partitioning).
  - MySQL (with `PRIMARY KEY` partitioning).
  - MongoDB (sharded collections).
- **ORM/Query Builders:**
  - Prisma (supports complex joins with partitioning).
  - SQLAlchemy (for denormalized queries).
- **Migration:**
  - Flyway, Liquibase (schema migrations).
  - AWS Glue/Azure Data Factory (ETL for large datasets).