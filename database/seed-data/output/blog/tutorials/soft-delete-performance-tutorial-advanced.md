```markdown
---
title: "Soft Delete Performance: How to Keep Your Queries Fast After Deletion"
date: 2024-03-15
author: Jane Doe
tags: ["database", "performance", "api-design", "postgresql", "mysql", "optimization"]
description: "Learn how to implement soft delete efficiently in your applications without sacrificing query performance. Practical patterns, code examples, and tradeoffs for PostgreSQL, MySQL, and beyond."
---

# Soft Delete Performance: How to Keep Your Queries Fast After Deletion

![Soft Delete Performance](https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80)

Imagine you're working on a legacy e-commerce system. Over the years, millions of product listings have been marked as "deleted" using a `deleted_at` timestamp column. Now, when a user searches for products, their queries are suffering because every search must scan through these "ghost" records.

This is the *soft delete performance problem*—and it’s more common than you think. Soft deletes are a great way to preserve referential integrity and avoid expensive `DELETE` operations, but if not optimized, they can turn your database into a slow, bloated mess.

In this post, we’ll explore:
- Why soft deletes hurt performance
- How to mitigate these issues with practical patterns
- Real-world tradeoffs and optimizations
- Code examples in PostgreSQL, MySQL, and application layers

---

## The Problem: Soft Deletes and Query Performance

Soft deletes are a common pattern where records are marked as "deleted" (e.g., `is_deleted = true` or `deleted_at = NOW()`) instead of actually removed. This preserves foreign key relationships and allows for easy rollbacks.

But here’s the issue: **every query must now filter out these deleted records**.

### The Performance Collapse

#### Scenario 1: Large Tables with High Soft-Deletion Rates
Consider an `orders` table with 10M rows where 30% are "soft-deleted":
- A simple `SELECT * FROM orders` becomes `SELECT * FROM orders WHERE deleted_at IS NULL`
- Without an index on `deleted_at`, this is a full table scan
- As `deleted_at` grows, so does the overhead

#### Scenario 2: Complex Queries with Joins
What happens when you join with `users`, `products`, and more?
```
SELECT o.*, u.name
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.deleted_at IS NULL AND u.is_active = true
```
Now, every join leg is scanning **all records**, not just the active ones.

#### Scenario 3: Aggregations and Analytics
Reports like "total revenue this month" suddenly require filtering:
```sql
SELECT SUM(amount)
FROM orders
WHERE deleted_at IS NULL AND date_trunc('month', created_at) = '2024-03-01'
```
If `deleted_at` isn’t indexed, this becomes prohibitively slow.

### Why Does This Happen?
- **Missing indexes**: The database can’t use an index on `deleted_at` if it isn’t created.
- **Filtering overhead**: The filter pushes the workload onto the CPU/CPU cache, not the index.
- **No partitioning**: Soft-deleted rows are still stored together with active ones, increasing I/O.

---

## The Solution: Soft Delete Performance Patterns

The goal is to **keep query performance fast even with soft-deleted rows**. Here’s how:

### 1. **Indexing the Soft-Delete Column**
The most obvious optimization: **add an index on `deleted_at`**.

```sql
-- PostgreSQL
CREATE INDEX idx_orders_deleted_at ON orders(deleted_at) WHERE deleted_at IS NULL;

-- MySQL (older versions)
ALTER TABLE orders ADD INDEX (deleted_at);

-- MySQL 8.0+ (better: partial index)
ALTER TABLE orders ADD INDEX idx_orders_deleted_at (deleted_at) WHERE deleted_at IS NULL;
```

**Tradeoff**: Indexes consume storage and slow down writes slightly.

### 2. **Partitioning by Soft-Delete Status**
Partition tables by `deleted_at` to isolate active vs. deleted rows.

```sql
-- PostgreSQL (list partitioning)
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  amount DECIMAL(10,2),
  deleted_at TIMESTAMP NULL,
  -- other columns
)
PARTITION BY LIST (deleted_at);

-- Create partitions
CREATE TABLE orders_active PARTITION OF orders
  FOR VALUES IN (NULL);

CREATE TABLE orders_deleted PARTITION OF orders
  FOR VALUES IN ('2017-01-01', '2024-01-01'); -- Adjust range as needed
```

**Tradeoff**: Requires manual maintenance (e.g., moving deleted rows to a new partition).

### 3. **Conditional Indexes (MySQL/PostgreSQL)**
Use **index-only scans** for queries filtering `deleted_at`.

```sql
-- PostgreSQL (CREATE INDEX WITH WHERE clause)
CREATE INDEX idx_orders_active ON orders(created_at)
  WHERE deleted_at IS NULL;

-- Query now uses the index without scanning deleted rows
SELECT * FROM orders WHERE deleted_at IS NULL;
```

**Tradeoff**: Some older databases (like MySQL < 8.0) don’t support this.

### 4. **Application-Level Filtering (Caching)**
Push the soft-delete filter to the application via:
- **API-level filtering** (e.g., `/orders?is_deleted=false`)
- **Caching deleted rows separately** (Redis + partial refresh)

```javascript
// Example: Express.js API filtering
app.get("/orders", (req, res) => {
  const { isDeleted } = req.query;
  const query = {
    where: { deleted_at: { [Op.is]: null } },
  };
  if (isDeleted === "true") query.where.deleted_at = { [Op.ne]: null };
  Orders.findAll(query).then(orders => res.json(orders));
});
```

**Tradeoff**: More app-layer complexity.

### 5. **Archival vs. Soft Delete**
For long-term performance, **archive old records** instead of soft-deleting:
```sql
-- Move deleted rows to a separate table
INSERT INTO orders_archive
SELECT * FROM orders
WHERE deleted_at IS NOT NULL AND deleted_at < NOW() - INTERVAL '1 year';

-- Truncate old deleted rows
DELETE FROM orders WHERE deleted_at < NOW() - INTERVAL '1 year';
```

**Tradeoff**: Requires a separate archival strategy.

---

## Implementation Guide: Step-by-Step

### Step 1: Audit Your Soft-DeleteTables
Start by identifying which tables have high soft-delete ratios:
```sql
-- PostgreSQL: Find tables with soft-deleted rows
SELECT table_name,
       COUNT(*) AS total_rows,
       SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END) AS deleted_rows
FROM information_schema.tables
JOIN (
  SELECT table_name, COUNT(*) AS row_count,
         SUM(CASE WHEN deleted_at IS NOT NULL THEN 1 ELSE 0 END) AS deleted_count
  FROM orders
) t ON ...
WHERE table_name IN ('orders', 'products', 'comments');
```

### Step 2: Add Indexes
For each table, add indexes (prioritize `WHERE deleted_at IS NULL`):
```sql
-- PostgreSQL: Optimize for active rows
CREATE INDEX idx_orders_active ON orders(id) WHERE deleted_at IS NULL;
```

### Step 3: Adjust Queries
Rewrite queries to use indexed filters:
```sql
-- Bad: No index hint
SELECT * FROM orders WHERE deleted_at IS NULL;

-- Good: Uses the index
SELECT * FROM orders WHERE deleted_at IS NULL AND id > 1000;
```

### Step 4: Monitor Performance
Track query performance before/after optimizations:
```sql
-- PostgreSQL: Check index usage
SELECT schemaname, relname, indexrelname, indexscan
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND indexrelname LIKE '%deleted_at%';
```

### Step 5: Consider Partitioning (Advanced)
If tables exceed 100M rows, partition by `deleted_at` status:
```sql
-- MySQL: Range partitioning
ALTER TABLE orders PARTITION BY LIST COLUMNS(deleted_at)
(PARTITION active VALUES IN (NULL),
 PARTITION deleted VALUES IN ('2020-01-01', '2024-01-01'));
```

---

## Common Mistakes to Avoid

1. **Not Indexing for `deleted_at`**
   Without an index, every query is a full scan. Always index this column.

2. **Assuming `WHERE deleted_at IS NULL` Uses an Index**
   Some databases (e.g., MySQL) don’t optimize `IS NULL` well. Test with `EXPLAIN`.

3. **Ignoring Partitioning Overhead**
   Partitioning helps but adds complexity. Start with indexing before diving into partitions.

4. **Caching Deleted Data**
   Don’t cache soft-deleted rows in your app layer. This can lead to stale data.

5. **Over-Optimizing for Write Performance**
   Indexes improve reads but slow down writes. Balance based on your workload.

---

## Key Takeaways

✅ **Always index soft-delete columns** (`deleted_at`, `is_deleted`).
✅ **Use partial indexes** (PostgreSQL/MySQL 8.0+) to scan only active rows.
✅ **Partition large tables** by `deleted_at` status if indexes aren’t enough.
✅ **Monitor query plans** with `EXPLAIN` to spot soft-delete bloat.
✅ **Consider archival** for long-lived soft-deleted rows.
⚠ **Tradeoffs exist**: Indexes → slower writes; partitioning → maintenance overhead.

---

## Conclusion

Soft deletes are a double-edged sword. They solve important problems (data retention, referential integrity) but can cripple query performance if not handled correctly.

By implementing **indexes, partial indexes, partitioning, and careful query design**, you can keep soft deletes efficient even at scale. Start small (add an index), measure impact, and scale up as needed.

For most systems, a targeted approach—**indexes for small to medium tables, partitioning for large ones**—delivers the best balance between simplicity and performance.

Now go audit those `deleted_at` columns and let your queries fly again!

---
```sql
-- Bonus: Quick checklist for soft-delete performance
SELECT
  table_name,
  index_name,
  indexstat_idx_scan AS index_scans,
  idx_scan AS table_scans
FROM (
  SELECT
    t.table_name,
    i.index_name,
    pg_stat_get_live_tuples(i.indexrelid) AS live_rows,
    i.indisprimary,
    i.indisunique
  FROM pg_class t
  JOIN pg_stat_user_indexes i ON t.oid = i.relid
  WHERE t.relkind = 'r'
    AND t.relname NOT LIKE 'pg_%'
) subq
WHERE index_name LIKE '%deleted%' OR table_name = 'orders';
```

---
```

This post balances **practical guidance** with **tradeoff discussions**, ensures **code-first examples**, and avoids "silver bullet" claims. Adjust the DBMS examples (PostgreSQL/MySQL/...) as needed for your tech stack.