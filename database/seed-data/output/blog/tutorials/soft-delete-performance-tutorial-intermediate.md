```markdown
---
title: "Soft Deletes Done Right: Performance Patterns for Efficient Database Filtering"
date: 2023-11-15
author: Alex Carter
tags: [database, patterns, performance, soft-delete]
description: "Learn how to implement efficient soft delete filtering in your database, avoiding the pitfalls of slow queries and bloated indexes."
---

# Soft Deletes Done Right: Performance Patterns for Efficient Database Filtering

![Soft Delete Performance](https://dev.to/logos/dev.to.svg) *By Alex Carter, Senior Backend Engineer*

---

## Introduction

Have you ever noticed how some APIs return "deleted" records that shouldn’t be visible to users? Or maybe you’ve seen your query performance degrade as your soft-deleted records pile up? Soft deletes are intuitive—they preserve data integrity, enable easy recovery, and mimic the real-world behavior of "archiving" data. But when implemented naively, they can turn into a performance nightmare.

In this post, we’ll explore **how to design soft delete filters that scale without sacrificing query performance**. You’ll learn why raw `WHERE deleted_at IS NULL` queries slow down over time, and how to optimize them with indexing, partition pruning, and clever query patterns. We’ll also dive into tradeoffs, anti-patterns, and real-world solutions you can apply to your next project.

Let’s get started.

---

## The Problem: Soft Deletes and the Performance Landmine

Soft deletes work by marking records as inactive instead of removing them. A typical implementation uses a `deleted_at` timestamp column, and applications filter out deleted records with:

```sql
SELECT * FROM users WHERE deleted_at IS NULL
```

Sounds simple, right? But here’s the catch:

### 1. Indexing Inefficiency
Most databases can efficiently filter by `IS NULL`, but **efficiently using indexes depends on the query plan**. As your dataset grows, the cost of scanning rows to find `NULL` values increases. Without proper indexing, even a moderately sized table with soft deletes can become sluggish.

### 2. Bloat and Replication Overhead
Soft-deleted rows are still stored in your database, contributing to disk usage, replication lag, and backup size. This isn’t just a performance issue—it’s a cost and scalability issue.

### 3. Query Plan Degradation
Over time, the query optimizer may start using less optimal plans for soft-delete queries, leading to full table scans or inefficient index skips. This is especially problematic for read-heavy applications like dashboards or analytics.

### Example Scenario
Imagine a SaaS application with 1 million users, where 10% are soft-deleted. If your dashboard query always filters by `deleted_at IS NULL`, you’re effectively scanning 900,000 rows per query. On a high-traffic day, this can cause:
- Slow API responses.
- Increased database load.
- Higher cloud costs due to over-provisioned resources.

---

## The Solution: Performance-Optimized Soft Deletes

The key to solving soft delete performance is **minimizing the work your database does to filter out inactive records**. Here are the core strategies:

### 1. Partitioning Deleted Data
By partitioning your table into "active" and "inactive" segments, you can eliminate `IS NULL` checks entirely. This is most effective with time-based soft deletes (e.g., `deleted_at` column).

### 2. Using a Separate Deleted Table
Move soft-deleted records to a separate table or schema. This ensures your active data remains compact and fast.

### 3. Optimizing Indexes for `IS NULL` Filters
If you must keep deleted records in the same table, ensure your indexes support `IS NULL` efficiently. This often involves composite indexes or functional indexes.

### 4. Query-Level Optimizations
Rewrite queries to reduce the number of rows scanned, such as adding bounds checks on `deleted_at`.

---

## Code Examples: Patterns in Action

Let’s explore these solutions in code.

---

### 1. Partitioning by `deleted_at`

#### Database Setup
```sql
-- PostgreSQL example (other databases have similar partitioning)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    deleted_at TIMESTAMP NULL
)
PARTITION BY RANGE (deleted_at);

-- Create a partition for active users (NULL deleted_at)
CREATE TABLE users_active PARTITION OF users
    FOR VALUES FROM (NULL) TO ('2024-01-01');

-- Create a partition for soft-deleted users (future timestamp)
CREATE TABLE users_deleted PARTITION OF users
    FOR VALUES FROM ('2024-01-01') TO ('9999-01-01');
```

#### Query Optimization
When querying active users, the database **automatically** filters to the `users_active` partition, avoiding any `IS NULL` checks:
```sql
SELECT * FROM users WHERE deleted_at IS NULL;
-- Optimized by the query planner to only read from `users_active`.
```

#### Migration Strategy
To migrate existing data:
```sql
-- Create new partitions first
CREATE TABLE users_active PARTITION OF users ...
CREATE TABLE users_deleted PARTITION OF users ...

-- Insert active users into the new partition
INSERT INTO users_active SELECT * FROM users WHERE deleted_at IS NULL;

-- Update deleted users to point to the new partition
UPDATE users SET deleted_at = '2024-01-01' WHERE deleted_at IS NULL;

-- Rebuild indexes
REINDEX TABLE users;
```

---

### 2. Separate Deleted Table (Denormalization)

#### Schema Design
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255)
);

CREATE TABLE users_deleted (
    id SERIAL PRIMARY KEY REFERENCES users(id),
    deleted_at TIMESTAMP NOT NULL,
    UNIQUE (id)
);
```

#### Application Logic
In your ORM or query layer, always join with the deleted table:
```sql
-- Example in Django/Python
from django.db.models import Q

def get_active_user(user_id):
    return User.objects.filter(
        ~Q(id__in=UsersDeleted.objects.filter(id=user_id))
    ).get(id=user_id)
```

#### Performance Benefit
- The `users` table remains lean and fast.
- Deleted records are neatly isolated, reducing scan costs.

---

### 3. Index Optimization for `IS NULL`

#### Problematic Query
```sql
-- Slow if no index exists or if the index isn't used properly
SELECT * FROM users WHERE deleted_at IS NULL AND name = 'John';
```

#### Solution: Composite Index
```sql
-- PostgreSQL: Use a partial index for active users
CREATE INDEX idx_users_active ON users (name) WHERE deleted_at IS NULL;
```

#### How It Works
The index is only created for rows where `deleted_at IS NULL`, so the database can **skip** the deleted rows entirely during the query. This is far more efficient than scanning all rows and filtering in Python.

---

### 4. Query-Level Optimization: Bounds Checking

#### Poor Practice
```sql
-- Scans all rows where deleted_at is NULL, even if they're old
SELECT * FROM users WHERE deleted_at IS NULL;
```

#### Optimized Query
```sql
-- Limits the scan to recent records
SELECT * FROM users WHERE deleted_at IS NULL AND created_at > NOW() - INTERVAL '30 days';
```

#### Why This Works
- Many applications only need recent data (e.g., dashboards).
- Adding bounds checks reduces the rowset size early, improving performance.

---

## Implementation Guide: Choosing the Right Approach

| Approach               | Pros                                      | Cons                                      | Best For                          |
|------------------------|-------------------------------------------|-------------------------------------------|-----------------------------------|
| **Partitioning**       | Fast queries, automatic filtering        | Complex migration, not all DBs support    | Large tables with many soft deletes |
| **Separate Deleted Table** | Isolated performance, simple queries    | Higher write cost (inserts/updates)       | Denormalized schemas               |
| **Index Optimization** | Works with existing schema               | May not be enough for very large datasets | Medium-sized tables                |
| **Bounds Checking**    | No schema change, simple                | Doesn’t help if you *must* scan all data  | Read-heavy, time-bound queries    |

---

## Common Mistakes to Avoid

1. **Ignoring Index Usage**
   - Always check `EXPLAIN ANALYZE` to confirm your indexes are being used.
   - Example:
     ```sql
     EXPLAIN ANALYZE SELECT * FROM users WHERE deleted_at IS NULL;
     ```
   - Look for `Seq Scan`—this means you’re scanning rows inefficiently.

2. **Not Testing Degradation**
   - Soft deletes are harmless in small datasets but become problematic at scale.
   - Simulate growth by inserting test data and measuring query times.

3. **Overusing Soft Deletes**
   - If your app rarely recovers deleted data, consider **hard deletes** instead.
   - Example: Audit logs or temporary data don’t need soft deletes.

4. **Forgetting to Update Indexes**
   - When you add a new column to your soft-delete filter (e.g., `deleted_at`), remember to rebuild indexes:
     ```sql
     CREATE INDEX idx_users_deleted ON users (deleted_at) WHERE deleted_at IS NOT NULL;
     ```

5. **Assuming `IS NULL` is Cheap**
   - In some databases (like MySQL without proper indexes), `IS NULL` can be expensive.
   - Test with `WHERE deleted_at IS NULL` vs. `WHERE deleted_at = NULL` (which is often worse).

---

## Key Takeaways

- **Soft deletes are great for data integrity but can bloat your database.**
  - Always weigh the tradeoff between recovery flexibility and performance.

- **Partitioning is the gold standard for large-scale soft deletes.**
  - If your database supports it (PostgreSQL, MySQL, BigQuery), use it.

- **Indexes matter more than you think.**
  - A well-placed partial index (`WHERE deleted_at IS NULL`) can save orders of magnitude in I/O.

- **Query optimization is a marathon, not a sprint.**
  - Regularly review your slowest queries and refactor as needed.

- **Consider alternatives for specific use cases.**
  - Hard deletes for temporary data.
  - Separate tables for audit logs or archival data.

---

## Conclusion

Soft deletes are a double-edged sword—intuitive and useful, but prone to performance pitfalls if not designed carefully. The key is to **reduce the work your database does to filter inactive records**. Whether you choose partitioning, separate tables, or index optimization, the goal is the same: **keep your active data fast and your system scalable**.

### Next Steps:
1. Audit your soft-delete queries with `EXPLAIN ANALYZE`.
2. Start small—optimize your slowest queries first.
3. If you’re using PostgreSQL or MySQL, experiment with partitioning.
4. Document your soft-delete strategy for future teams.

---

### Further Reading:
- [PostgreSQL Partitioning Guide](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [MySQL Partitioning Best Practices](https://dev.mysql.com/doc/refman/8.0/en/partitioning-best-practices.html)
- [Database Indexing Deep Dive](https://use-the-index-luke.com/)

---

**What’s your soft-delete strategy?** Have you run into performance issues? Share your experiences in the comments—I’d love to hear from you!
```