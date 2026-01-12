# **[Pattern] Cassandra Database Patterns – Reference Guide**

---

## **Overview**
Cassandra’s **wide-column, distributed, and tunable-consistency** architecture enables scalable, high-availability data storage but requires careful modeling to avoid performance bottlenecks, hotspots, or query inefficiencies. This guide outlines key **Cassandra database patterns**, including **partitioning strategies, data modeling, query design, and anti-patterns** to ensure optimal performance, scalability, and maintainability.

Cassandra excels at **write-heavy, time-series, high-throughput** workloads but may struggle with **complex joins, ad-hoc queries, or strict row-level consistency**. This reference provides actionable insights for structuring data, choosing primary keys, and designing queries while balancing **read/write performance, consistency, and cost**.

---

## **1. Core Concepts & Terminology**

| **Term**               | **Definition**                                                                                     | **Key Considerations**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Partition Key**      | Determines data distribution across nodes (hash-based).                                          | Avoid **hot partitions** (uneven distribution); use **composite keys** with multiple columns.           |
| **Clustering Columns** | Defines **sort order** within a partition (alphabetical, timestamp-based, etc.).                 | Optimize for **scan efficiency** (limit clustering columns to 1-3).                                         |
| **SSTable**            | Cassandra’s **immutable, on-disk storage** for rows (merged during compaction).                     | Too many SSTables → **slow reads**; compaction tuning (`SizeTiered`, `Leveled`) affects performance.     |
| **Bloom Filters**      | Probabilistic checks to avoid reading SSTables unnecessarily.                                     | False positives increase **I/O**; default settings (e.g., `0.1`) balance memory vs. speed.                  |
| **Memtable Flush**     | In-memory writes **flush to disk** when size/throttle limits hit.                                | Too frequent → **disk I/O**; too rare → **read latency**.                                                |
| **Tuner (nodetool)**   | Diagnostics tool for **compaction, disk usage, and tuning**.                                      | Key commands: `tuner`, `tpstats`, `proxyhistograms`.                                                   |
| **Table vs. Materialized View** | Tables store data; **materialized views** pre-compute derived data for faster queries. | Avoid overusing; **refresh delay** adds latency.                                                       |

---

## **2. Schema Design Patterns**

### **2.1 Primary Key Strategies**
| **Pattern**               | **Use Case**                                                                 | **Example Schema**                                                                 | **Pros**                                                                 | **Cons**                                                                 |
|---------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Single-Partition Key**  | Simple partitioning (e.g., user IDs).                                        | `CREATE TABLE users_by_id (user_id UUID PRIMARY KEY, name TEXT, email TEXT);`      | Easy to implement.                                                       | Risk of **hot partitions** if key distribution is skewed.                |
| **Composite Key**         | Distribute load across multiple dimensions (e.g., `user_id` + `region`).   | `CREATE TABLE user_events (user_id UUID, region TEXT, event_time TIMESTAMP, PRIMARY KEY((user_id, region), event_time)));` | Avoids hotspots; improves locality.                                       | Requires careful tuning for **clustering column scans**.                  |
| **Time-Bucketed Keys**    | Time-series data (e.g., sensor readings).                                   | `CREATE TABLE sensor_readings (sensor_id UUID, bucket TEXT, reading_time TIMESTAMP, value FLOAT, PRIMARY KEY((sensor_id, bucket), reading_time));` | Efficient **time-range queries**.                                          | Manual bucket management (e.g., `bucket = '2024-01'`).                     |
| **UUID vs. UUIDTime**     | UUIDs for randomness; UUIDTime for **time-sorted** access.                    | `CREATE TABLE logs (log_id TIMEUUID, source TEXT, message TEXT, PRIMARY KEY(log_id));` | Natural **time-based sorting**.                                            | Higher storage overhead than UUID.                                       |
| **Token-Aware Keys**      | Pre-distribute keys to avoid **hot partitions** (e.g., hashed prefixes).   | `CREATE TABLE orders (order_id TEXT, customer_id UUID, PRIMARY KEY(order_id));` + Apply a **hash prefix** (e.g., `order_id = 'A123'`). | Ensures even distribution.                                               | Manual key generation complexity.                                        |

---

### **2.2 Data Modeling Patterns**

#### **A. Denormalization**
Cassandra **favors denormalization** to avoid joins. Instead of:
```sql
-- Bad: Normalized schema (joins required)
CREATE TABLE users (user_id UUID PRIMARY KEY, name TEXT);
CREATE TABLE posts (post_id UUID, user_id UUID, content TEXT, PRIMARY KEY(post_id));
```
Use **embedded data** in the partition key:
```sql
-- Good: Denormalized for partition locality
CREATE TABLE user_posts (
    user_id UUID,
    post_id UUID,
    content TEXT,
    PRIMARY KEY(user_id, post_id)  -- All posts for a user are co-located
);
```

#### **B. Time-Series Data**
For **high-cardinality time-series** (e.g., IoT devices):
```sql
CREATE TABLE device_metrics (
    device_id TEXT,
    bucket TIMEUUID,  -- Bucket by day/month (e.g., '2024-01-15')
    timestamp TIMESTAMP,
    value FLOAT,
    PRIMARY KEY((device_id, bucket), timestamp)
) WITH CLUSTERING ORDER BY (timestamp DESC);
```
**Query Pattern:**
```sql
SELECT * FROM device_metrics
WHERE device_id = 'sensor_42'
AND bucket = toTimestamp('2024-01-15')
AND timestamp > '2024-01-15 08:00:00';
```

#### **C. Multi-Dimensional Access Patterns**
Use **multiple tables with the same primary key** (CQL **denormalization**):
```sql
-- Table 1: Events by user + time
CREATE TABLE user_events (
    user_id UUID,
    event_time TIMESTAMP,
    event_type TEXT,
    PRIMARY KEY((user_id), event_time)
);

-- Table 2: Events by type + time (for "recent posts")
CREATE TABLE event_by_type (
    event_type TEXT,
    event_time TIMESTAMP,
    user_id UUID,
    PRIMARY KEY((event_type), event_time, user_id)
);
```

---

### **2.3 Indexing Strategies**
| **Method**               | **When to Use**                                                                 | **Limitations**                                                                 |
|--------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Secondary Index**      | Low-cardinality columns (e.g., `status`).                                     | **Not recommended** for high-cardinality (slow scans).                        |
| **SASI (SSTable Attached Secondary Index)** | Time-series or high-cardinality fields (e.g., `device_id`). | Requires manual tuning; **Cassandra 4.0+**.                                      |
| **Materialized Views**   | Pre-computed queries (e.g., "top 10 users by activity").                     | **Refresh delay**; not real-time.                                                |
| **Application-Level Joins** | When denormalization isn’t feasible.                                           | Adds **client-side complexity**.                                                |

**Example SASI Index:**
```sql
CREATE CUSTOM INDEX ON device_metrics(device_id) USING 'org.apache.cassandra.index.sasi.SASIIndex';
```

---

## **3. Query Optimization Patterns**

### **3.1 Efficient Reads**
- **Avoid `ALLOW FILTERING`** (full table scans). Instead, design **partition keys** for predictable access.
- **Limit `IN` clauses** (e.g., `WHERE user_id IN (1, 2, 3)`). Cassandra must fetch entire partitions.
- **Use `LIMIT` + pagination** for large result sets:
  ```sql
  -- Paginate with token (not rowCount)
  SELECT * FROM users WHERE user_id > 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' LIMIT 100;
  ```

### **3.2 Write Optimization**
- **Batch writes carefully** (use `LOGGED` batches for durability):
  ```sql
  BEGIN LOGGED BATCH
      INSERT INTO table1 ...;
      INSERT INTO table2 ...;
  APPLY BATCH;
  ```
  - **Avoid `UNLOGGED` batches** (data loss risk).
  - **Limit batch size** (< 256KB to avoid network overhead).
- **Use `IF NOT EXISTS` for upserts**:
  ```sql
  INSERT INTO users (user_id, name) VALUES (?, ?) IF NOT EXISTS;
  ```

### **3.3 Consistency Tuning**
| **Level**  | **Use Case**                          | **Latency Impact**               | **When to Avoid**                          |
|------------|---------------------------------------|-----------------------------------|--------------------------------------------|
| `ONE`      | High throughput, eventual consistency. | Low                               | Critical data integrity needed.            |
| `QUORUM`   | Balanced R/W consistency.              | Moderate                          | Strong consistency required.                |
| `ALL`      | Strong consistency (rarely used).     | High (reads/writes block).        | Avoid in hot partitions.                    |

**Example:** For a `QUORUM` write:
```sql
INSERT INTO orders (order_id, customer_id) VALUES (?, ?) USING CONSISTENCY QUORUM;
```

---

## **4. Common Anti-Patterns & Pitfalls**

| **Anti-Pattern**               | **Problem**                                                                 | **Solution**                                                                 |
|--------------------------------|----------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Single-Column Partition Key** | Hotspots if key distribution is skewed (e.g., `user_id` with 1M reads/s). | Use **composite keys** (e.g., `(user_id, region)`).                         |
| **Wide Partitions**            | Partitions > **100MB** slow down mutations/compactions.                     | Split via **time-bucketing** or **salting**.                                  |
| **Unbounded Clustering Columns** | Scans become **O(n)** (e.g., `WHERE partition_key = ?`).                   | Limit to **1-3 columns**; use `ORDER BY`.                                     |
| **Overusing Secondary Indexes** | High-cardinality indexes degrade performance.                               | Pre-aggregate data or use **SASI**.                                          |
| **Not Tuning Compaction**      | `SizeTieredCompactionStrategy` (STCS) causes **too many SSTables**.        | Use `LeveledCompactionStrategy` (LCS) for reads-heavy workloads.              |
| **Ignoring TTL**               | Unbounded retention bloats storage.                                         | Set **TTL** for transient data (e.g., `USING TTL 86400`).                     |

---

## **5. Performance Tuning Checklist**
1. **Monitor:**
   - `nodetool cfstats` → Check **read/write latency**, **partition sizes**.
   - `nodetool proxyhistograms` → Identify slow queries.
2. **Schema:**
   - Avoid **hot partitions** (< 100MB per partition).
   - Use **composite keys** for multi-dimensional access.
3. **Compaction:**
   - **STCS** for write-heavy workloads.
   - **LCS** for read-heavy workloads.
4. **Network:**
   - Tune `cas.per.request.timeout_in_ms` (default: 5000ms).
5. **JVM:**
   - Increase **Heap (Xmx)** if GC pauses exceed 100ms.

---

## **6. Query Examples**

### **6.1 Time-Series Aggregation**
```sql
-- Get avg sensor reading per bucket
SELECT bucket, AVG(value)
FROM device_metrics
WHERE device_id = 'sensor_42'
AND bucket = '2024-01-15'
GROUP BY bucket;
```

### **6.2 User Activity by Region**
```sql
-- Denormalized query (partition key = (user_id, region))
SELECT region, COUNT(*) as event_count
FROM user_events
WHERE user_id = ?
AND region = ?
GROUP BY region;
```

### **6.3 Batch Insert (Logged)**
```sql
BEGIN LOGGED BATCH
    INSERT INTO user_activity (user_id, activity_type, time)
    VALUES (?, ?, ?);
    INSERT INTO activity_log (user_id, time, details)
    VALUES (?, ?, ?);
APPLY BATCH;
```

### **6.4 Paginated Results**
```sql
-- Fetch next 100 users starting after 'abc123'
SELECT * FROM users
WHERE user_id > 'abc123'
LIMIT 100;
```

---

## **7. Related Patterns**
- **[Partitioning Strategies](link)** – Deep dive into key distribution techniques.
- **[Denormalization for Cassandra](link)** – Advanced denormalization patterns.
- **[Time-Series Optimization](link)** – Bucketing, compaction, and query tuning.
- **[CQL Anti-Patterns](link)** – Common mistakes in query design.
- **[Cassandra Benchmarking](link)** – Tools and metrics for performance testing.
- **[Event Sourcing in Cassandra](link)** – Modeling audit logs and event streams.

---
**Last Updated:** [Date]
**Version:** 1.2
**Feedback:** [Contact]