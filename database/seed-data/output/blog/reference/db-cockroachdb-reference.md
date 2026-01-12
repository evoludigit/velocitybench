---
# **[CockroachDB Database Patterns] Reference Guide**

---

## **Overview**
This guide documents **CockroachDB database patterns**—proven approaches for modeling, querying, and optimizing data in distributed SQL databases. It covers **schema design best practices**, **transactional patterns**, **indexing strategies**, **distributed data partitioning**, and **common anti-patterns** to avoid. Leveraging CockroachDB’s **strong consistency**, **horizontal scalability**, and **global availability**, these patterns ensure high performance, reliability, and maintainability in production deployments.

---

## **Key Concepts**
CockroachDB’s **distributed architecture** introduces unique challenges and optimizations. Key concepts include:
- **Replicated tables**: Data is distributed across nodes with **automatic leader-follower replication** for write availability.
- **Spans**: A logical grouping of rows across multiple nodes (e.g., `users_by_country`).
- **TTL and time-series**: Optimized for time-based data (e.g., logs, metrics).
- **Secondary indexes**: Separate tables for low-cardinality columns (e.g., `user_status`).
- **Constraints**: Enforced via **Raft groups** (similar to PostgreSQL, but distributed).

---
## **Schema Reference**

| **Pattern**               | **Use Case**                          | **Example Schema**                                                                 | **Key Considerations**                                                                 |
|---------------------------|---------------------------------------|-----------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Primary Table**         | Core business data                    | `CREATE TABLE orders (id UUID PRIMARY KEY, user_id UUID NOT NULL, amount DECIMAL)`  | Use `UUID` for globally unique IDs; avoid `SERIAL` for distributed environments.    |
| **Secondary Index**       | Low-cardinality filters (e.g., status)| `CREATE TABLE order_status (order_id UUID PRIMARY KEY, status TEXT NOT NULL)`    | Indexes are **materialized**—update via triggers or `INSERT`/`UPDATE` cascades.      |
| **Time-Series (TTL)**     | Event logs, metrics                    | `CREATE TABLE sensor_readings (timestamp TIMESTAMP NOT NULL, value FLOAT)`        | Set TTL (e.g., `ALTER TABLE sensor_readings SET TTL timestamp + INTERVAL '1 year'`). |
| **Partitioned Table**     | Large datasets (e.g., by region)       | `CREATE TABLE users_by_region (region TEXT, user_id UUID PRIMARY KEY, ...)`      | Partitioning is **logical** (via spans); avoid over-partitioning.                   |
| **Hierarchical Data**     | Parent-child relationships            | `CREATE TABLE products (id UUID, parent_id UUID REFERENCES products(id))`         | Use `FOREIGN KEY` with `ON DELETE CASCADE` or triggers for consistency.              |
| **JSONB for Semi-Structured** | Flexible schemas (e.g., user prefs) | `CREATE TABLE user_profiles (id UUID PRIMARY KEY, settings JSONB)`                | Query with `->>` or `?&` operators; avoid deep nesting for performance.               |

---
## **Query Examples**

### **1. Basic CRUD Operations**
```sql
-- Insert with UUID (auto-generated or manual)
INSERT INTO orders (id, user_id, amount) VALUES (gen_random_uuid(), 'user-123', 99.99);

-- Update via secondary index (requires transaction)
BEGIN;
  UPDATE orders SET amount = 109.99 WHERE id = 'order-456';
  UPDATE order_status SET status = 'shipped' WHERE order_id = 'order-456';
COMMIT;

-- Delete with cascade (if FK defined)
DELETE FROM orders WHERE id = 'order-789';
```

### **2. Distributed Queries (Cross-Nodes)**
```sql
-- Aggregate across spans (e.g., orders by region)
SELECT region, COUNT(*) FROM orders
JOIN users_by_region USING (user_id)
GROUP BY region;

-- Time-range scan with TTL optimization
SELECT * FROM sensor_readings
WHERE timestamp > NOW() - INTERVAL '7 days';
```

### **3. Concurrency Control**
```sql
-- Optimistic locking (retry on conflict)
BEGIN;
  SELECT amount FROM orders WHERE id = 'order-123' FOR UPDATE;
  -- Application checks for version/timestamp mismatch and retries.
END;

-- Pessimistic locking (use sparingly)
LOCK TABLE orders IN SHARE MODE;
```

### **4. JSONB Queries**
```sql
-- Filter by nested JSON field
SELECT * FROM user_profiles
WHERE settings->>'theme' = 'dark';

-- Update nested field
UPDATE user_profiles
SET settings = settings || '{"last_login": NOW()}'
WHERE id = 'user-1';
```

---
## **Best Practices**

### **Schema Design**
1. **Avoid `SERIAL`**: Use `gen_random_uuid()` or `UUID()` for distributed IDs.
2. **Index Strategically**:
   - Primary keys are **automatically indexed**.
   - Secondary indexes should target **high-selectivity columns** (e.g., `status`, `region`).
3. **Time-Series Data**:
   - Use `TIMESTAMP` + TTL for logs/metrics.
   - Partition by date (e.g., `region_date` span).

### **Transactions**
1. **Keep Transactions Short**: CockroachDB’s **distributed transactions** add latency.
2. **Use Batch Writes**: For bulk inserts, use `INSERT ... ON CONFLICT` or `COPY` (via `psql`).
3. **Retry on Conflicts**: Implement exponential backoff for `RETRIES_EXHAUSTED` errors.

### **Performance**
1. **Monitor Spans**: Use `EXPLAIN ANALYZE` to identify slow spans.
   ```sql
   EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 'user-1';
   ```
2. **Leverage Secondary Indexes**: Reduce full-table scans.
3. **Avoid `SELECT *`**: Explicitly fetch columns.

### **Anti-Patterns**
| **Anti-Pattern**          | **Problem**                                                                 | **Fix**                                                                           |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Monolithic Tables**     | Single table with mixed data (e.g., `users` + `orders`).                     | Split into normalized tables with FKs.                                            |
| **Unbounded Secondary Indexes** | Indexes growing indefinitely (e.g., `user_activity`).            | Add TTL or partition by time.                                                    |
| **Long-Running Transactions** | Holds locks for >30 seconds.                                          | Break into smaller transactions or use sagas.                                     |
| **Ignoring Span Coverage** | Uneven data distribution across nodes.                                  | Analyze `cockroach sql --exec=EXPLAIN ANALYZE count(*) FROM table;`.              |

---
## **Related Patterns**
1. **[Saga Pattern]**: For long-running workflows (e.g., order processing) to avoid distributed transaction bottlenecks.
   - *Use Case*: Microservices coordinating via eventual consistency.
   - *Example*: compartments pattern for compensating transactions.

2. **[Event Sourcing]**: Store state changes as immutable events for auditability and replayability.
   - *Use Case*: Financial transactions, audit logs.
   - *Example*: Time-series tables with `version` column.

3. **[Materialized Views]**: Pre-compute aggregates for read-heavy workloads.
   - *Use Case*: Dashboards, analytics.
   - *Example*:
     ```sql
     CREATE MATERIALIZED VIEW daily_revenue AS
     SELECT DATE(trunc(order_timestamp, 'day')), SUM(amount)
     FROM orders
     GROUP BY 1;
     ```

4. **[Sharding by Hash]**: Distribute data evenly using `HASH()` for custom partitioning.
   - *Use Case*: User sessions, high-write tables.
   - *Example*:
     ```sql
     CREATE TABLE sessions (
       user_id UUID,
       session_key TEXT PRIMARY KEY,
       data JSONB
     ) SPAN BY HASH(user_id);
     ```

5. **[Connection Pooling]**: Manage client connections efficiently.
   - *Tools*: `pgbouncer`, CockroachDB’s built-in `pgpool`.
   - *Config*: Adjust `max_prepared_transactions` and `statement_timeout`.

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                       |
|-------------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **High Latency**                    | Check `EXPLAIN ANALYZE` for full-table scans or slow spans.                 | Add indexes, optimize queries, or increase node count.                           |
| **Replication Lag**                 | Use `cockroach diagnose` or `cockroach sql --exec=SHOW TABLE status`.     | Scale nodes or reduce write volume.                                               |
| **Deadlocks**                       | Enable `cockroach sql --exec=SET CLOCK_TIMEOUT = '30s'`.                   | Retry transactions or break into smaller steps.                                 |
| **Storage Bloat**                   | Monitor `cockroach sql --exec=SELECT pg_size_pretty(pg_total_relation_size('table'));`. | Reclaim space with `VACUUM` or optimize schemas.                                |

---
## **References**
- [CockroachDB Documentation](https://www.cockroachlabs.com/docs/)
- [Secondary Indexes Deep Dive](https://www.cockroachlabs.com/docs/stable/secondary-indexes.html)
- [TTL and Time-Series Guide](https://www.cockroachlabs.com/docs/stable/ttl.html)