```markdown
# **Index Strategy for Compiled Queries: How to Optimize Your Most Repeated SQL**

*Write once, run millions of times—why your most critical queries deserve a tailored indexing strategy.*

---

## **Introduction: The Hidden Cost of "Fast" Code**

Have you ever written a query that *seemed* fast in development but became a performance bottleneck in production? The culprit is often the database—even with "optimized" application code, poorly indexed compiled queries can drag down your entire system.

Compiled queries (repeated SQL calls) are everywhere:
- **Pagination** (`SELECT * FROM users LIMIT 20 OFFSET 100`)
- **Reporting** (`SELECT SUM(revenue) FROM sales WHERE month = '2023-10'`)
- **Caching layers** (`SELECT * FROM cache_key WHERE type = 'user_data' AND id = ?`)

Without the right indexing strategy, these queries can become **linear-time operations**, crushing your application’s scalability.

In this post, we’ll explore:
✅ **Why compiled queries need special indexing attention**
✅ **How to identify performance killers early**
✅ **Practical indexing techniques for common patterns**
✅ **Anti-patterns that waste time and resources**

Let’s dive in.

---

## **The Problem: Why Compiled Queries Are Different**

Compiled queries aren’t just "normal" queries—they’re **repeated** queries. And repetition reveals inefficiencies.

### **1. The Compounded Cost of Latency**
Every time a query runs without an index, it performs a **full table scan** (or worse, a nested loop join). If this happens **millions of times an hour**, those scans add up.

Example:
```sql
-- Bad: No index, runs every time a user loads their profile
SELECT * FROM user_profiles WHERE user_id = ?;
-- If this runs 10,000x/day, a 100ms scan → 16 minutes of wasted time.
```

### **2. The "I Didn’t Know It Was Slow" Trap**
Developers often assume `EXPLAIN` tells the whole story. But:
- `EXPLAIN` shows **one run’s plan**, not cumulative behavior.
- **A good index today may become a bottleneck tomorrow** (e.g., as data grows).
- **Compiled queries often ignore index hints** (e.g., OR conditions, function-based lookups).

### **3. False Positives: "It Works in Dev, So It’s Fine"**
Local databases (like SQLite or small MySQL instances) can hide inefficiencies. But in production:
- Larger datasets **expose hidden costs**.
- **Network latency** makes poor queries feel sluggish.
- **Caching layers** (Redis, CDN) don’t help if the query itself is slow.

---
## **The Solution: Indexing for Compiled Queries**

The key insight: **Not all queries are created equal.** Some run once; others run **millions of times**. We need **strategic indexing**—not just slapping indexes everywhere.

### **Core Principles**
1. **Profile first, index later** – Use tools to find the real bottlenecks.
2. **Index for the most critical paths** – Not every query needs optimization.
3. **Consider the query’s lifetime** – A one-time migration script ≠ a paginated API endpoint.
4. **Balance read vs. write performance** – Indexes speed up queries but slow down inserts.

---

## **Components of the Index Strategy**

### **1. Query Profiling: Find the Culprits**
Before optimizing, **measure**. Use:
- **Database tools**: `EXPLAIN ANALYZE`, `pg_stat_statements` (PostgreSQL), slow log (MySQL).
- **Application metrics**: Track slow queries in APM tools (New Relic, Datadog).

**Example (PostgreSQL):**
```sql
-- Enable statement stats (postgres.conf)
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all

-- Check top slow queries
SELECT * FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

### **2. Index Selection Criteria**
Not all compiled queries deserve optimization. Prioritize:
✔ **High-frequency queries** (e.g., API endpoints, caching keys).
✔ **Large result sets** (e.g., pagination, reporting).
✔ **Queries with `ORDER BY`, `JOIN`, or `GROUP BY`** (indexes help here).
❌ **One-off migrations** or **rare admin queries**.

#### **Common Compiled Query Patterns & Their Index Needs**
| **Query Type**               | **Index Strategy**                          | **Example**                          |
|------------------------------|--------------------------------------------|--------------------------------------|
| **Single-column equality**   | B-tree index                                | `WHERE user_id = ?`                  |
| **Range queries**            | B-tree (for `<`, `>`, `BETWEEN`)            | `WHERE created_at BETWEEN ? AND ?`   |
| **OR conditions**            | Composite index (if possible) or `IN`       | `WHERE status IN ('active', 'pending')` |
| **Text search (LIKE, `ILIKE`)** | Full-text or hash index (for prefix matches) | `WHERE name LIKE 'J%'`               |
| **Paginated results**        | Covering index (includes `LIMIT/OFFSET`)    | `SELECT id, name FROM users WHERE ...` |
| **Aggregations**             | Index on `GROUP BY` columns                | `SUM(revenue) WHERE month = ?`       |

---

## **Code Examples: Putting It Into Practice**

### **Example 1: Optimizing a Paginated API Endpoint**
**Problem:**
A `/users?page=10` endpoint is slow because it scans the entire `users` table.

**Bad Index (or no index):**
```sql
-- No index → Full scan
SELECT id, name, email FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 180;
```

**Solution: Covering Index**
```sql
-- Add a covering index (includes ALL selected columns)
CREATE INDEX idx_users_paginated ON users(created_at DESC)
INCLUDE (id, name, email);

-- Now uses the index for both ORDER BY and LIMIT/OFFSET
```

**Result:**
- **Before**: ~500ms for 1,000,000 rows.
- **After**: ~1ms (index-only scan).

---

### **Example 2: Fixing an OR Condition Bottleneck**
**Problem:**
A frequently used query filters users by role (`admin`, `editor`, `viewer`), but the index isn’t helping.

**Bad (missing index):**
```sql
-- No index → Full table scan
SELECT * FROM users
WHERE role IN ('admin', 'editor');
```

**Solution: Composite Index**
```sql
-- Add a composite index (order matters!)
CREATE INDEX idx_users_role ON users(role);
```

**Even Better: Hash Index for Large `IN` Sets**
```sql
-- For many possible values, use a hash index (PostgreSQL)
CREATE INDEX idx_users_role_hash ON users USING hash(role);
```

**Result:**
- **Before**: ~300ms for 5M rows.
- **After (B-tree)**: ~5ms.
- **After (hash)**: ~2ms (but slower for `NOT IN`).

---

### **Example 3: Speeding Up Time-Based Aggregations**
**Problem:**
A reporting query sums monthly revenue but scans the entire table.

**Bad Query:**
```sql
-- No index → Full scan
SELECT SUM(amount) FROM sales
WHERE month = '2023-10';
```

**Solution: Partial Index + Covering**
```sql
-- Partial index (only 2023 data)
CREATE INDEX idx_sales_month_2023 ON sales(month)
WHERE month >= '2023-01-01';

-- Covering index for the SUM (if only amount is needed)
CREATE INDEX idx_sales_amount_month ON sales(month, amount);
```

**Alternative: Partitioning (for massive datasets)**
```sql
-- Partition by month (auto-managed indexes)
CREATE TABLE sales (
    id SERIAL,
    amount DECIMAL(10,2),
    month DATE
)
PARTITION BY RANGE (month);
```

**Result:**
- **Before**: ~1.2s for 100M rows.
- **After (partial index)**: ~50ms.
- **After (partitioning)**: ~10ms (scalable).

---

## **Implementation Guide: Step-by-Step**

### **1. Identify the Top 5 Slowest Compiled Queries**
Use database logs or APM tools to find:
- Which queries run most frequently?
- Which take the longest relative to their frequency?

### **2. Analyze Each Query with `EXPLAIN ANALYZE`**
Example:
```sql
EXPLAIN ANALYZE
SELECT id, name FROM users WHERE email = 'user@example.com';
```
Look for:
- **Seq Scan** (bad) vs. **Index Scan** (good).
- **Full table scans** on large tables.
- **Sort operations** (can often be avoided with the right index).

### **3. Choose the Right Index Type**
| **Use Case**               | **Index Type**       | **When to Avoid**               |
|----------------------------|----------------------|----------------------------------|
| Equality filters (`=`)     | B-tree               | High cardinality (see below)    |
| Range filters (`>`, `<`)   | B-tree               | Not for exact matches            |
| Hash lookups               | Hash index           | Not for ranges or sorting       |
| Full-text search           | GIN/GIST             | Not for exact matches            |
| JSON fields                | GiST                 | Not for equality comparisons     |
| Composite keys             | B-tree               | If one column is rarely used     |

**Tradeoff Example:**
- **B-tree indexes** are great for ranges but slower for low-cardinality columns (e.g., `status IN ('active', 'inactive')`).
- **Hash indexes** are fast for exact matches but useless for `BETWEEN`.

### **4. Test Before Deploying**
Always run:
```sql
-- Simulate production load
EXPLAIN ANALYZE SELECT ... [your query] [with index];
```
Compare **before** and **after** to confirm improvements.

### **5. Monitor After Deployment**
Use:
- Database stats (`pg_stat_statements`, MySQL slow query log).
- Application metrics (latency percentiles).
- Alert if performance degrades (e.g., "Index scan time > 500ms").

---

## **Common Mistakes to Avoid**

### **1. Over-Indexing (The "Index Bomb")**
❌ **Problem**: Adding too many indexes slows down writes.
```sql
-- Avoid: Indexing every column!
CREATE INDEX idx_user_all ON users(id, name, email, created_at);
```

✅ **Solution**: Only index:
- Columns used in **frequent filters**.
- Columns in **JOINs** or **GROUP BY**.
- Columns in **ORDER BY** (if not already indexed).

### **2. Ignoring Index Selectivity**
❌ **Problem**: Indexing a low-cardinality column (e.g., `is_active BOOLEAN`) is useless.
```sql
-- Bad: 80% of rows match!
CREATE INDEX idx_users_active ON users(is_active);
```

✅ **Solution**: Check distribution:
```sql
-- Check column uniqueness
SELECT COUNT(DISTINCT column) FROM table;
```
**Rule of thumb**: If fewer than **10-20%** of rows match a filter, an index may not help.

### **3. Not Updating Statistics**
❌ **Problem**: Databases sometimes use stale index plans.
```sql
-- Fix: Recalculate stats (PostgreSQL)
ANALYZE users;
```

✅ **Solution**: Run `ANALYZE` after:
- Big data migrations.
- Schema changes.
- Every few days (automate it).

### **4. Using `LIMIT/OFFSET` Without a Covering Index**
❌ **Problem**: `OFFSET` forces a full scan even with an index.
```sql
-- Bad: OFFSET forces a full scan
SELECT * FROM orders OFFSET 1000 LIMIT 100;
```

✅ **Solution**:
- Use **keyset pagination** (recommended):
  ```sql
  -- Better: Filter by a previous row's ID
  SELECT * FROM orders
  WHERE id > last_seen_id
  ORDER BY id
  LIMIT 100;
  ```
- Or **materialized views** for large datasets.

### **5. Forgetting About Locking**
❌ **Problem**: Long-running queries block writes.
```sql
-- Bad: Holds locks for minutes
SELECT * FROM inventory WHERE product_id = ? FOR UPDATE;
```

✅ **Solution**:
- Use **shorter transactions**.
- Add **optimistic concurrency** (e.g., `WHERE version = ?`).

---

## **Key Takeaways**

### **✅ Do:**
- **Profile first**: Use `EXPLAIN ANALYZE` and slow query logs.
- **Index strategically**: Focus on **compiled queries**, not every query.
- **Use covering indexes**: Include all columns needed for the query.
- **Choose the right index type**: B-tree for ranges, hash for exact matches.
- **Monitor after deployment**: Performance can degrade over time.

### **❌ Don’t:**
- **Index indiscriminately**: Every index adds write overhead.
- **Ignore selectivity**: Low-cardinality columns rarely benefit from indexes.
- **Neglect `LIMIT/OFFSET`**: Use keyset pagination instead.
- **Forget statistics**: Run `ANALYZE` regularly.

### **🔥 Pro Tip:**
For **extremely high-throughput** systems (e.g., 10M+ queries/day), consider:
- **Read replicas** for indexed queries.
- **Caching layers** (Redis) for compiled results.
- **Query sharding** (split data by frequency).

---

## **Conclusion: Indexing for Compiled Queries Isn’t Optional**

Compiled queries are the **engine oil** of high-performance applications. Without the right indexing strategy, even a well-written API can bog down under load.

**Key lessons:**
1. **Not all queries deserve optimization**—focus on the **most critical paths**.
2. **Indexing is a balancing act**—read speed vs. write performance.
3. **Measure, test, and monitor**—assume nothing works forever.

### **Next Steps**
- **For SQL developers**: Try the `EXPLAIN ANALYZE` technique on your slowest queries.
- **For team leads**: Enforce index reviews in PRs (e.g., "Add `EXPLAIN` results to the PR").
- **For architects**: Consider **query caching** (e.g., Redis) for volatile compiled queries.

**Final thought**: *A well-indexed compiled query isn’t just faster—it’s the difference between a system that scales and one that chokes.*

---
**What’s your biggest compiled query bottleneck?** Share in the comments—I’d love to hear your war stories (and optimizations)!

---
**Further Reading:**
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [MySQL Indexing Best Practices](https://dev.mysql.com/doc/refman/8.0/en/optimization.html)
- [Hash vs. B-tree Indexes: When to Use What](https://use-the-index-luke.com/sql/where-clause/sql-hash-indexes)
```