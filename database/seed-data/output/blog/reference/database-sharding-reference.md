# **[Pattern] Database Sharding Strategies – Reference Guide**

---

## **1. Overview**
Database sharding distributes data across multiple database instances (shards) to scale read/write throughput, storage capacity, and fault tolerance beyond the limits of a single server. Each shard holds a logically partitioned subset of data, determined by a **shard key** (e.g., `user_id`, `region_id`). Queries must be designed to target specific shards, eliminating cross-shard dependencies. While sharding enables near-linear scalability, it introduces complexity in **horizontal query execution**, **join optimization**, and **data consistency**.

Common use cases include:
- High-traffic web applications (e.g., social media, e-commerce).
- Global applications requiring regional data localization.
- Analytics workloads with partitioned time-series data.

---
## **2. Core Concepts & Terminology**

| Term               | Definition                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------|
| **Shard Key**      | Column(s) used to partition data (e.g., `user_id`, `timestamp`). Must be selected carefully. |
| **Sharding Function** | Algorithm (e.g., modulo, hashing, range-based) mapping keys to shards.                      |
| **Shard**          | Independent database instance containing a subset of data.                                   |
| **Shard Router**   | Middleware (e.g., proxy, application logic) directing queries to the correct shard.        |
| **Partitioning Key** | Same as shard key; ensures data locality for queries.                                       |
| **Cross-Shard Query** | Query accessing data from multiple shards (expensive; mitigated via denormalization).     |

---

## **3. Schema Reference**
Below are common sharding strategies and their schema implications. Assume a `users` table with a shard key.

### **3.1. Hash-Based Sharding**
Distributes data uniformly using a hash function (e.g., `HASH(user_id) % NUM_SHARDS`).

| Schema Example          | Shard Key  | Pros                                      | Cons                                  |
|-------------------------|------------|-------------------------------------------|---------------------------------------|
| `users(user_id, name)`  | `user_id`  | Even distribution, simple routing        | Hotspots if `user_id` isn’t random.  |
|                         |            |                                           |                                       |

**Example Sharding Function**:
```python
def hash_shard(user_id, shard_count):
    return hash(user_id) % shard_count
```

---

### **3.2. Range-Based Sharding**
Partitions data into contiguous ranges (e.g., `user_id` intervals).

| Schema Example          | Shard Key  | Pros                                      | Cons                                  |
|-------------------------|------------|-------------------------------------------|---------------------------------------|
| `users(user_id, name)`  | `user_id`  | Predictable shard access (e.g., by region)| Skewed if ranges aren’t balanced.     |

**Example Sharding Function**:
```python
def range_shard(user_id, shard_ranges):
    for range_start, range_end in shard_ranges:
        if range_start <= user_id <= range_end:
            return shard_ranges.index((range_start, range_end))
```

---
### **3.3. Directory-Based Sharding**
Maintains a global directory (e.g., Zookeeper, etcd) tracking shard ownership.

| Schema Example          | Shard Key  | Pros                                      | Cons                                  |
|-------------------------|------------|-------------------------------------------|---------------------------------------|
| `users(user_id, name)`  | `user_id`  | Dynamic shard rebalancing                | Adds latency for directory lookups.  |

**Use Case**: Cloud-native applications with dynamic workloads.

---

### **3.4. Composite Sharding**
Combines multiple shard keys (e.g., `user_id + region_id`) for multi-dimensional partitioning.

| Schema Example               | Shard Key         | Pros                                      | Cons                                  |
|------------------------------|-------------------|-------------------------------------------|---------------------------------------|
| `users(user_id, region_id)`  | `(user_id, region)| Localizes regional queries               | Complex routing logic.               |

**Example Sharding Function**:
```python
def composite_shard(user_id, region_id, shard_count):
    return (hash(user_id) + hash(region_id)) % shard_count
```

---
## **4. Query Examples**
### **4.1. Simple Query (Single-Shard)**
**Query**:
```sql
SELECT * FROM users WHERE user_id = 123;
```
**Execution**:
- Router resolves `user_id = 123` → Shard 2.
- Executes locally on Shard 2.

---

### **4.2. Cross-Shard Join (Anti-Pattern)**
**Query**:
```sql
SELECT u.name, o.order_id
FROM users u
JOIN orders o ON u.user_id = o.user_id;
```
**Problem**:
- Joins require merging data from multiple shards (slow).
**Solution**: Denormalize or use a separate analytics database.

---

### **4.3. Efficient Query (Denormalized)**
**Schema**:
```sql
-- Shard 1: users(user_id, name)
-- Shard 2: user_orders(user_id, order_id)  -- Localized to Shard 1
```
**Query**:
```sql
SELECT name, order_id
FROM users u, user_orders o
WHERE u.user_id = o.user_id AND u.user_id = 123;
```
**Execution**:
- Both tables reside on Shard 1 → Fast join.

---

### **4.4. Aggregations Across Shards**
**Query**:
```sql
SELECT COUNT(*) FROM users;
```
**Execution**:
1. Router broadcasts query to all shards.
2. Each shard computes `COUNT(*)` locally.
3. Aggregates results (e.g., `SUM(shard_results)`).
**Optimization**: Use **sampling** or **pre-aggregated metrics**.

---

## **5. Implementation Considerations**
### **5.1. Shard Key Design**
| Criteria               | Recommendation                                                                 |
|------------------------|---------------------------------------------------------------------------------|
| **Uniform Distribution** | Avoid hotspots (e.g., `user_id` may skew if sequential).                      |
| **Query Patterns**     | Prioritize keys used in `WHERE`, `JOIN`, or `ORDER BY` clauses.                |
| **Stability**          | Chose keys unlikely to change (e.g., `user_id` > `created_at`).               |

---
### **5.2. Shard Management**
| Task                | Approach                                                                       |
|---------------------|---------------------------------------------------------------------------------|
| **Adding Shards**   | Use **directory-based** or **range-based** sharding for incremental scaling. |
| **Rebalancing**     | Migrate data incrementally (minimize downtime).                               |
| **Failure Handling**| Replicate shards or use **multi-AZ deployments**.                            |

---
### **5.3. Transactions**
- **Within a Shard**: Use ACID transactions normally.
- **Cross-Shard**: Avoid; use **sagas** or **eventual consistency** for distributed transactions.

---

## **6. Tradeoffs**
| **Pros**                              | **Cons**                                                    |
|---------------------------------------|-------------------------------------------------------------|
| Scales horizontally to petabytes.     | Complex routing and debugging.                              |
| Isolates failures (e.g., one shard down). | Cross-shard queries are expensive.                           |
| Supports high availability.           | Requires application-level changes (e.g., denormalization). |

---

## **7. Related Patterns**
| Pattern                          | Description                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|
| **CQRS**                          | Separate read/write models to avoid cross-shard reads.                        |
| **Event Sourcing**                | Use shards for time-partitioned event storage.                              |
| **Denormalization**               | Duplicate data locally per shard to enable joins.                           |
| **Federated Querying**            | Tools like Presto/Cosmos DB optimize cross-shard queries.                    |
| **Database Replication**          | Complements sharding for high availability (but not scaling).                |

---
## **8. Tools & Frameworks**
- **Shard Routing**: Vitess, CockroachDB, ShardingSphere.
- **Orchestration**: Kubernetes (for dynamic shard scaling), Consul/Zookeeper.
- **Analytics**: Druid (for cross-shard aggregations).

---
## **9. Anti-Patterns**
1. **Ignoring Shard Key in Joins/Indexes**
   - *Problem*: Queries scan all shards.
   - *Fix*: Include shard key in joins or denormalize.

2. **Monolithic Queries**
   - *Problem*: A single query updates 10 shards.
   - *Fix*: Break into batches or use sagas.

3. **Static Shard Allocation**
   - *Problem*: Workloads change, but shards are fixed.
   - *Fix*: Use dynamic directory-based routing.

---
## **10. Example Architecture**
```
[Client] → [Shard Router] → [Shard 1, Shard 2, Shard 3]
   │
   ├─── Shard 1: Users 1-100K (user_id)
   ├─── Shard 2: Users 101K-200K
   └─── Shard 3: Users 201K+
```
- **Router**: Resolves `user_id` → shard via `HASH(user_id) % 3`.
- **Denormalized Tables**: `user_orders` co-located with `users` on Shard 1.

---
### **11. References**
- [Vitess Sharding Guide](https://vitess.io/docs/)
- [Database Sharding: A Comprehensive Guide](https://www.percona.com/resources/white-papers/database-sharding-guide)
- [CockroachDB Sharding](https://www.cockroachlabs.com/docs/stable/architecture/sharding.html)