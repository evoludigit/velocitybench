# **Debugging *FraiseQL Aggregation Model*: A Troubleshooting Guide**
*A focused guide for optimizing database-native aggregations to prevent memory bloat, performance degradation, and network overload.*

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms in your system:
- **[ ]** API endpoints return with **latency spikes** (e.g., 1–10 sec for a `SUM()` or `COUNT()` operation).
- **[ ]** Server memory (`/proc/meminfo`, `jstat -gc`, or `top`) shows **unexpected surges** when aggregations run.
- **[ ]** Database logs (`ERROR`, `WARN`, `slow_query`) reveal:
  - `external sort` or `tmp table` operations (indicating insufficient RAM).
  - `SELECT` queries fetching **millions of rows** before aggregation.
- **[ ]** **Network tools** (`netdata`, `tshark`, `nginx` logs) show:
  - Large payloads (e.g., 500MB+) from DB→Application.
  - **Timeouts** or **connection drops** during aggregation phases.
- **[ ]** **Client-side** (e.g., React/Next.js) displays:
  - *"Request timed out"* or *"Failed to fetch"* for aggregations.

---

## **2. Common Issues & Fixes**
### **Issue 1: Unoptimized SELECT Queries Pull Too Many Rows**
**Symptoms:**
- `EXPLAIN ANALYZE` shows a full table scan (`Seq Scan`) with high row counts.
- Application logs show `ArrayList` or `List<T>` growing to **millions of entries**.

**Root Cause:**
- Query lacks `WHERE`/`JOIN` filters or uses `SELECT *`.
- Aggregation runs **after** fetching all data (e.g., `db.query().then(rows => rows.reduce(...))`).

**Fixes:**
#### **Option A: Push Filters to Database (Best)**
```sql
-- ❌ Bad: Fetch all, then filter in app
SELECT * FROM users;  -- 10M rows

-- ✅ Good: Filter in SQL
SELECT * FROM users WHERE created_at > '2023-01-01';
```

#### **Option B: Use LIMIT Early**
If you *must* fetch partial data:
```sql
-- For paginated aggregations (e.g., dashboards)
SELECT id, value FROM metrics
WHERE time > NOW() - INTERVAL '7 days'
ORDER BY time
LIMIT 1000;  -- Process in batches
```

#### **Option C: Client-Side Batching (Last Resort)**
If server-side filtering isn’t feasible:
```javascript
// Node.js + FraiseQL
const batchSize = 10000;
const results = [];
for (let offset = 0; ; offset += batchSize) {
  const batch = await db.query(`
    SELECT * FROM large_table
    WHERE id > $1
    LIMIT $2
  `, [lastId, batchSize]);

  if (!batch.rows.length) break;
  results.push(...processBatch(batch.rows));
}
```

---

### **Issue 2: Missing Indexes Cause Full Scans**
**Symptoms:**
- `EXPLAIN ANALYZE` shows `Seq Scan` (no `Index Scan`).
- Aggregations work but are **10–100x slower** than expected.

**Root Cause:**
- Missing indexes on `GROUP BY`, `JOIN`, or `WHERE` columns.

**Fixes:**
#### **Add Composite Indexes**
```sql
-- For GROUP BY + WHERE
CREATE INDEX idx_group_filter ON metrics (category, status, date);
```
#### **Check with `EXPLAIN ANALYZE`**
```sql
EXPLAIN ANALYZE
SELECT category, SUM(value)
FROM metrics
WHERE date > '2023-01-01'
GROUP BY category;
```
**Goal:** Look for `Index Scan` (not `Seq Scan`).

---

### **Issue 3: HAVING Clauses Trigger Full Row Loads**
**Symptoms:**
- `HAVING` conditions (e.g., `SUM(value) > 1000`) cause **temporary tables** (`tmp_table` in logs).
- Memory usage spikes when `SUM`/`AVG` exceeds available RAM.

**Root Cause:**
- Database materializes all rows before applying `HAVING`.

**Fixes:**
#### **Rewrite as Subqueries**
```sql
-- ❌ Bad: HAVING pushes data to app
SELECT category, SUM(value)
FROM metrics
GROUP BY category
HAVING SUM(value) > 1000;

-- ✅ Good: Filter in SQL
SELECT category
FROM (
  SELECT category, SUM(value) as total
  FROM metrics
  GROUP BY category
) subquery
WHERE total > 1000;
```

#### **Use Window Functions (PostgreSQL)**
For conditional aggregations:
```sql
SELECT category, SUM(value) as total
FROM metrics
GROUP BY category
HAVING total > 1000
WITH ROLLUP;  -- Optional: Include totals
```

---

### **Issue 4: Network Bottlenecks from Large Payloads**
**Symptoms:**
- **GBs of data** transferred (e.g., `SELECT * FROM table` returns 5GB).
- **App crashes** due to `ObjectSizeError` (Node.js) or `OutOfMemoryError` (Java).

**Root Cause:**
- Application fetches **all columns** or **unfiltered rows**.

**Fixes:**
#### **Select Only Aggregated Columns**
```sql
-- ❌ Bad: Fetches 50 columns
SELECT * FROM sales;

-- ✅ Good: Only needed aggregations
SELECT month, SUM(revenue) as total_revenue
FROM sales
GROUP BY month;
```

#### **Stream Results with Server-Side Pagination**
```sql
-- PostgreSQL: Use `LIMIT` + `OFFSET` (or `cursor` for large datasets)
SELECT * FROM (
  SELECT *,
    ROW_NUMBER() OVER (ORDER BY id) as row_num
  FROM large_table
) subquery
WHERE row_num BETWEEN 1 AND 1000;
```

---

### **Issue 5: Application Misuses Aggregation Results**
**Symptoms:**
- App stores entire `GROUP BY` results in memory (e.g., `new Map()` with 1M entries).
- **Timeouts** when processing large arrays in JavaScript.

**Root Cause:**
- Frontend/backend processes aggregations **after** fetching all data.

**Fixes:**
#### **Offload Processing to Database**
```sql
-- Let DB compute the final result
SELECT
  COUNT(*) as total_users,
  AVG(age) as avg_age
FROM users
WHERE active = true;
```

#### **Use Streaming in Application**
```javascript
// Node.js: Stream aggregations (e.g., with `pg.stream`)
const client = new pg.Client();
await client.connect();

const query = client.query(`
  SELECT user_id, SUM(amount)
  FROM transactions
  GROUP BY user_id
`);

query.on('row', (row) => {
  process(row);  // Handle one row at a time
});
```

---

## **3. Debugging Tools & Techniques**
### **Database-Side Diagnostics**
| Tool               | Purpose                                      | Command/Flag                          |
|--------------------|-----------------------------------------------|----------------------------------------|
| `EXPLAIN ANALYZE`  | Shows query execution plan + runtime stats   | `EXPLAIN ANALYZE SELECT ...`           |
| `pg_stat_statements` | Tracks slow queries                          | Enable in `postgresql.conf`: `share_all_plan` |
| `pg_buffer_cache`  | Checks cache hits/misses                     | `SELECT * FROM pg_stat_activity;`      |
| `pg_stat_activity` | Identifies long-running queries              | `SELECT * FROM pg_stat_activity;`      |
| `pg_tablesize`     | Estimates table size                          | `SELECT pg_size_pretty(pg_total_relation_size('table_name'));` |

### **Application-Side Diagnostics**
| Tool               | Purpose                                      | Example                                  |
|--------------------|-----------------------------------------------|------------------------------------------|
| **Memory Profiling** | Monitor heap usage                          | Node: `--inspect` + Chrome DevTools      |
| **Network Inspection** | Check payload sizes                         | `curl -v http://api/aggregation`          |
| **Query Logging**   | Log slow aggregations                        | `LOG_LEVEL=debug` (FraiseQL)             |
| **Load Testing**    | Simulate traffic                            | `ab -n 1000 -c 100 http://api/aggregation` |

### **Key Metrics to Monitor**
1. **Database:**
   - `Seq Scan` vs. `Index Scan` ratio.
   - Temporary tables (`tmp_table`) usage.
   - Query duration (`pg_stat_statements`).
2. **Application:**
   - Memory growth during aggregation (`process.memoryUsage()`).
   - Request duration (`response-time` in APM tools like Datadog).
3. **Network:**
   - Payload size (`curl -H "Accept-Encoding: none"`).
   - Latency (`ping` + `traceroute`).

---

## **4. Prevention Strategies**
### **Design-Time Optimizations**
1. **Denormalize for Aggregations**
   - Pre-compute `SUM`/`AVG` in materialized views:
     ```sql
     CREATE MATERIALIZED VIEW daily_sales AS
     SELECT
       date_trunc('day', created_at) as day,
       SUM(amount) as total
     FROM sales
     GROUP BY day;
     ```
   - **Refresh daily** (e.g., with `pg_cron`).

2. **Use Time-Series Databases**
   - For time-based aggregations (e.g., InfluxDB, TimescaleDB):
     ```sql
     -- TimescaleDB: Optimized for time-series
     SELECT SUM(value) FROM metrics
     WHERE time > NOW() - INTERVAL '1 day';
     ```

3. **Implement Query Caching**
   - Cache aggregations with TTL (e.g., Redis):
     ```javascript
     const cache = new NodeCache({ stdTTL: 3600 }); // 1-hour cache
     const result = cache.get('daily_revenue');
     if (!result) {
       result = await db.query('SELECT SUM(amount) FROM sales');
       cache.set('daily_revenue', result);
     }
     ```

### **Runtime Optimizations**
1. **Add Query Timeouts**
   - Prevent hanging aggregations:
     ```sql
     -- PostgreSQL: Set statement_timeout
     SET statement_timeout = '30s';
     ```

2. **Use Approximate Aggregations (For Analytics)**
   - Trade accuracy for speed (e.g., HyperLogLog for `COUNT DISTINCT`):
     ```sql
     -- PostgreSQL + pg_hyperloglog
     SELECT hyperloglog_approx_count(distinct user_id) FROM logs;
     ```

3. **Monitor and Alert**
   - Set up alerts for:
     - `Seq Scan` > 50% of queries.
     - Memory usage > 80% of RAM.
     - Query duration > 2 sec.

### **Code-Level Patterns**
1. **Avoid ORM Bloat**
   - Use raw SQL for aggregations (avoid `Model.aggregate()`):
     ```javascript
     // ❌ Bad: ORM bloat
     await User.aggregate().sum('revenue');

     // ✅ Good: Direct SQL
     await db.query('SELECT SUM(revenue) FROM users');
     ```

2. **Batch Processing**
   - For offline aggregations:
     ```javascript
     import { pipeline } from 'stream';
     import { readFile } from 'fs';

     const dataStream = readFile('large_data.csv');
     const processedStream = dataStream.pipe(processAggregate());
     await pipeline(dataStream, processedStream);
     ```

3. **Use Connection Pooling**
   - Reuse DB connections to avoid overhead:
     ```javascript
     // FraiseQL + pg-pool
     const pool = new Pool({ max: 20 });
     const client = await pool.connect();
     ```

---

## **5. Checklist for Quick Resolution**
| Step                          | Action                                                                 |
|-------------------------------|------------------------------------------------------------------------|
| **1. Identify slow queries** | Check `pg_stat_statements` for `Seq Scan` or `tmp_table` usage.       |
| **2. Add indexes**            | Ensure `GROUP BY`, `WHERE`, and `JOIN` columns are indexed.            |
| **3. Optimize SQL**           | Rewrite `HAVING` as subqueries; use `LIMIT` for partial data.           |
| **4. Reduce payloads**        | Select only aggregated columns; stream results.                        |
| **5. Monitor memory**         | Use `top`/`htop` to catch in-memory bloat.                              |
| **6. Cache results**          | Cache aggregations (Redis/Memcached) with TTL.                          |
| **7. Test with realistic data** | Use `pg_test` or `dbschema` to simulate production volumes.           |
| **8. Document fixes**         | Update runbooks with query optimizations.                              |

---

## **Final Notes**
- **Start with `EXPLAIN ANALYZE`**—it reveals **90% of issues**.
- **Favor database optimizations** over application-side fixes (fewer moving parts).
- **Test with production-like data**—small datasets hide bottlenecks.
- **Monitor post-fix**—aggregations can degrade over time (e.g., schema changes).

By following this guide, you’ll **eliminate 80% of aggregation-related issues** within hours, not days. For persistent problems, revisit **indexes**, **query patterns**, and **memory limits**.