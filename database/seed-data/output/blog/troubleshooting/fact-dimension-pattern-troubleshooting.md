# **Debugging the Fact-Dimension Pattern in FraiseQL: A Troubleshooting Guide**

## **1. Introduction**
The **Fact-Dimension Pattern** in FraiseQL (a Postgres-based analytics stack) is designed to simplify schema complexity by storing dimensions in JSONB and measures as regular SQL columns. While this approach avoids joins by embedding metadata, it can lead to **poor aggregation performance**, especially when dealing with large datasets.

This guide provides a **structured debugging approach** to identify bottlenecks, optimize queries, and prevent future issues.

---

# **2. Symptom Checklist**
Before diving into fixes, verify if your issue matches these symptoms:

| **Symptom** | **Description** | **Impact** |
|-------------|----------------|------------|
| **Slow Aggregations** | Simple `SUM`, `AVG`, or `COUNT` queries take > 1s | Degraded query performance |
| **Deep Query Plans** | `EXPLAIN ANALYZE` shows 5+ hash joins or sequential scans | High CPU/memory usage |
| **JSONB Filtering Overhead** | Complex `jsonb_*` functions slow down queries | High computation cost |
| **Fragmentation Issues** | `ANALYZE` reports skewed row distribution | Uneven workload across partitions |
| **Large JSONB Size** | Dimensions consume > 50% of row size | High storage & I/O pressure |

**Next Steps:**
- Confirm if the issue is **read-heavy** (aggregations) or **write-heavy** (data changes).
- Check if the problem persists on **small vs. large datasets**.

---

# **3. Common Issues & Fixes**

### **Issue 1: Slow Aggregations Due to JSONB Extraction**
**Symptom:** Queries like `SELECT SUM(value), jsonb_extract_path(dims, 'category') FROM facts GROUP BY category` are slow.

**Root Cause:**
- FraiseQL must **scan all rows** and **extract JSONB fields** for grouping.
- Without a **materialized index**, this is an **O(n) operation**.

**Fix: Add a Partial Index on JSONB Paths**
```sql
-- Option 1: Partial index on a single JSONB field
CREATE INDEX idx_facts_category ON facts USING GIN ((dims ->> 'category'));
```
**Impact:** Speeds up `WHERE dims->>'category' = 'Electronics'` queries.

**Alternative: Denormalize Highly Filtered Fields**
```sql
-- Add a column if JSONB access is frequent
ALTER TABLE facts ADD COLUMN category TEXT;
UPDATE facts SET category = dims->>'category';
CREATE INDEX idx_facts_category ON facts(category);
```
**When to use?**
- If **>30% of queries filter by this field**, denormalization helps.

---

### **Issue 2: Deep Join Plans from Unoptimized JSONB Filtering**
**Symptom:** `EXPLAIN` shows **nested loop joins** or **hash joins** on JSONB columns.

**Root Cause:**
- FraiseQL **cannot optimize JSONB lookups** as well as regular columns.
- Multiple `jsonb_*` functions force full-table scans.

**Fix: Use `jsonb_path_ops` for Better Indexing**
```sql
-- Better than ->> for partial indexing
CREATE INDEX idx_facts_path ON facts USING GIN ((dims @> '{"category": "Electronics"}'));
```
**Alternative: Pre-aggregate JSONB Data**
```sql
-- Materialized view for common aggregations
CREATE MATERIALIZED VIEW mv_facts_by_category AS
SELECT
    (dims->>'category') AS category,
    SUM(value) AS total_sales
FROM facts
GROUP BY category;
```
**Impact:**
- Reduces query complexity by **70-90%** for precomputed aggregations.

---

### **Issue 3: Storage vs. Query Tradeoff (JSONB Bloat)**
**Symptom:** JSONB columns consume **>50% of row size**, leading to slow I/O.

**Root Cause:**
- Large JSONB payloads increase **disk reads** and **CPU parsing overhead**.

**Fix: Compress JSONB Data**
```sql
-- Use TOAST for large JSONB fields
ALTER TABLE facts ALTER COLUMN dims SET STORAGE EXTERNAL;
```
**Alternative: Shard or Partition by Time/Dimension**
```sql
-- Partition by month to reduce scan size
CREATE TABLE facts_y2023 (
    LIKE facts INCLUDING ALL
) PARTITION BY RANGE (created_at);
INSERT INTO facts_y2023 SELECT ... WHERE EXTRACT(YEAR FROM created_at) = 2023;
```
**Impact:**
- Reduces **full-table scans** by **90%** for time-bound queries.

---

### **Issue 4: Inefficient GROUP BY on JSONB**
**Symptom:** `GROUP BY dims->>'category'` is slow because **Postgres must extract for every row**.

**Root Cause:**
- No direct indexing on JSONB paths in grouping.

**Fix: Use `jsonb_array_elements_text` for Array Dimensions**
```sql
-- If dimensions are stored in arrays
SELECT
    value,
    jsonb_array_elements_text(dims -> 'tags') AS tag
FROM facts;
```
**Alternative: Use `jsonb_path_ops` with `WITH ORDINALITY`**
```sql
-- For nested JSON structures
SELECT
    jsonb_path_query_array(dims, '$..category') AS category
FROM facts;
```
**Impact:**
- **3-5x faster** than manual extraction in some cases.

---

### **Issue 5: Skewed Data Distribution**
**Symptom:** `ANALYZE` shows **uneven row distribution** across dimensions.

**Root Cause:**
- Some dimension values dominate, causing **hot partitions**.

**Fix: Add Partial Indexes for Hot Keys**
```sql
-- Index only the top 10% of categories
CREATE INDEX idx_facts_popular_categories ON facts(dims->>'category')
WHERE dims->>'category' LIKE '%Electronics%' OR dims->>'category' LIKE '%Clothing%';
```
**Alternative: Use `DISTINCT ON` for Analytics**
```sql
-- Get top categories without full scan
SELECT DISTINCT ON (category) category, COUNT(*)
FROM (
    SELECT dims->>'category' AS category
    FROM facts
    WHERE created_at > '2023-01-01'
) AS subq
ORDER BY category, COUNT(*) DESC;
```
**Impact:**
- Reduces **full-table scans for common queries**.

---

# **4. Debugging Tools & Techniques**

### **A. Query Optimization Workflow**
1. **Check the Execution Plan**
   ```sql
   EXPLAIN (ANALYZE, BUFFERS) SELECT SUM(value), dims->>'category' FROM facts GROUP BY category;
   ```
   - Look for **Seq Scan, Hash Join, or Nested Loop**.
   - High **seq_page_hit ratio (<20%)** = missing indexes.

2. **Profile JSONB Access Patterns**
   ```sql
   -- Find most accessed JSONB paths
   SELECT substr(path, 0, 10) AS prefix, count *
   FROM jsonb_path_query_array(dims, '$..*') AS data
   GROUP BY prefix
   LIMIT 10;
   ```
   - Identify **high-frequency fields** for indexing.

3. **Test with `EXPLAIN (VERBOSE, COSTS)`**
   ```sql
   EXPLAIN (VERBOSE, COSTS) SELECT * FROM facts WHERE dims @> '{"status": "active"}';
   ```
   - Check if **cost estimates** match reality.

### **B. Key Metrics to Monitor**
| **Metric** | **Tool** | **Threshold** |
|------------|----------|---------------|
| Seq Scan Time | `EXPLAIN (ANALYZE)` | >1s for 1M rows |
| JSONB Extraction Latency | `pg_stat_activity` | >100ms per query |
| Index Usage | `pg_stat_user_indexes` | `idx_scan` < 10% of rows |
| Memory Usage | `pg_stat_activity` | `shared_blks_read` > 10K |

### **C. Benchmarking JSONB vs. Denormalized**
```sql
-- Compare performance
EXPLAIN (ANALYZE) SELECT SUM(value) FROM facts WHERE category = 'Electronics';
-- vs.
EXPLAIN (ANALYZE) SELECT SUM(value) FROM facts_denormalized WHERE category = 'Electronics';
```
**Rule of Thumb:**
- If **denormalized query is 10x faster**, consider keeping it.

---

# **5. Prevention Strategies**
### **A. Schema Design Best Practices**
✅ **Use JSONB for:**
- Rarely queried metadata (e.g., user preferences).
- Semi-structured data with low cardinality.

❌ **Avoid JSONB for:**
- High-cardinality dimensions (categories, products).
- Fields used in `WHERE`, `GROUP BY`, or `JOIN`.

### **B. Indexing Strategies**
| **Use Case** | **Index Type** | **Example** |
|-------------|----------------|-------------|
| Exact JSONB match | GIN | `CREATE INDEX ON facts USING GIN (dims)` |
| Path extraction | BRIN/Hash | `CREATE INDEX ON facts((dims->>'category'))` |
| Array elements | GiST | `CREATE INDEX ON facts USING GIST (dims @ jsonb_path_ops)` |

### **C. Query Optimization Rules**
1. **Limit JSONB Extraction in WHERE Clauses**
   ```sql
   -- ❌ Slow
   WHERE dims->>'status' = 'active'

   -- ✅ Fast (if indexed)
   WHERE dims @> '{"status": "active"}'
   ```

2. **Use `jsonb_path_ops` for Complex Queries**
   ```sql
   -- Faster than manual JSONB parsing
   SELECT * FROM facts WHERE dims @> '{"category": "Electronics", "price": {"min": 100}}';
   ```

3. **Consider Hybrid Schemas**
   - Store **frequently filtered fields** in columns.
   - Keep **infrequent metadata** in JSONB.

### **D. Monitoring & Alerting**
- **Set up alerts** for:
  - High `jsonb_*` function usage in slow queries.
  - Large JSONB sizes (`pg_total_relation_size`).
- **Use FraiseQL’s Query Logs** to track JSONB access patterns.

---

# **6. Final Checklist for Resolution**
| **Step** | **Action** | **Expected Outcome** |
|---------|------------|----------------------|
| 1 | Check `EXPLAIN ANALYZE` for JSONB scans | Identify slow operations |
| 2 | Add GIN/BRIN indexes on hot JSONB paths | Reduce full scans |
| 3 | Test denormalization for critical fields | Compare performance |
| 4 | Monitor `pg_stat_user_indexes` usage | Ensure indexes are used |
| 5 | Partition large tables by time/dimension | Improve query speed |

---
**If the issue persists:**
- **Re-evaluate** whether JSONB is the right choice for this use case.
- **Consider** a **hybrid schema** (some columns, some JSONB).
- **Test with smaller datasets** to isolate bottlenecks.

---
**Key Takeaway:**
The **Fact-Dimension Pattern** shines for **flexibility** but **struggles with performance** under heavy aggregation. By **indexing strategically** and **denormalizing hot paths**, you can achieve **90%+ speedups** in most cases.

Would you like a **deep dive** into any specific optimization technique?