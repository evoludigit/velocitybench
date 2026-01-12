```markdown
---
title: "Availability Maintenance: Keeping Your Database Happy in the Long Run"
date: 2023-11-15
author: "Alex Carter"
tags: ["database", "backend design", "maintenance", "SQL", "API patterns"]
---

# Availability Maintenance: Keeping Your Database Happy in the Long Run

Have you ever received a desperate customer support ticket at 2 AM? Like, "Our app is slow—it was fine this morning!" Or perhaps you've looked at your database logs to find a long-running query clawing its way through hundreds of thousands of records, leaving your entire system gasping for air.

This isn't a story about some exotic bug—it's the reality of databases that aren't *properly maintained*. Over time, even well-designed systems degrade through unchecked growth, inefficient queries, or neglected indexes. This is where **the Availability Maintenance pattern** comes into play—an often overlooked but critical technique to ensure your database stays fast, reliable, and available for years.

This guide will walk you through why databases need maintenance, what components keep them healthy, and practical code examples to help you implement *real-world* availability maintenance. We’ll cover everything from reclaiming wasted space to balancing load dynamically. Let’s dive in.

---

## The Problem: Why Your Database Gets Slower (Without Maintenance)

Databases aren’t like web servers—you can’t just throw more resources at a slow SQL query. The performance of a database is tied to its *design*, *usage habits*, and *physical organization*. Without maintenance, databases gradually degrade in ways that are subtle but destructive:

1. **Bloat from Unused Data**
   Every time you insert, update, and delete records, the database’s internal storage structure changes. Over time, tables accumulate "dead" space—rows that are logically deleted but not physically reclaimed. This leaves your database with large gaps in its storage, slowing down scans and inserts.

2. **Index Pollution**
   Indexes are your database’s roadmap. But like a map with too many new routes, indexes can become cluttered. If you frequently update values that change how data relates (e.g., changing a user’s last name), the indexes for related tables (e.g., orders) get fragmented and slow.

3. **Fragmented Logs and Transaction Tables**
   Some databases, like PostgreSQL, have transaction logs and temporary tables that accumulate data over time. Without cleanup, these can bloat to hundreds of gigabytes, making backups slower and increasing recovery times.

4. **Schema Drift**
   When teams add new fields or tables without proper planning, they often do so with minimal testing. This can lead to:
   - **Null-heavy tables** where most columns are empty but take up space.
   - **Unused indexes** that slow down queries.
   - **Unpartitioned large tables** that make queries scan gigabytes of unrelated data.

5. **Connection Leaks**
   Every open connection consumes memory and resources. If your application fails to close connections (or leaves them dangling), your database can become overwhelmed, forcing it to reject new connections and crash under load.

6. **Long-Running Queries**
   One query can paralyze a database if it doesn’t release resources in time. This is especially common in systems with poorly written batch jobs or non-idempotent operations.

---

## The Solution: Availability Maintenance Pattern

The **Availability Maintenance pattern** is about *proactively* managing databases to keep them performant, reliable, and available. It combines best practices from schema optimization, performance tuning, and operational hygiene. Here’s how it works:

- **Regular Cleanup**: Automatically remove unused data and reclaim wasted space.
- **Schema Management**: Ensure your schema stays lean, efficient, and aligned with business needs.
- **Performance Monitoring**: Track slow queries and index usage to maintain optimal performance.
- **Load Management**: Distribute database load evenly and prevent resource leaks.
- **Backup and Recovery Hygiene**: Keep backups manageable and recovery fast.

Unlike reactive fixes (e.g., adding RAM when performance sags), the Availability Maintenance pattern is *preventative*. It’s the daily hygiene routine for your databases.

---

## Components/Solutions

Let’s break down the key components of Availability Maintenance:

### 1. **Scheduled Cleanup Jobs**
   Automate tasks like:
   - Dropping old/unused data.
   - Index rebuilding.
   - Temp table cleanup.

### 2. **Auto-Vacuum and Analysis**
   Databases like PostgreSQL rely on `VACUUM` and `ANALYZE` to keep storage efficient and query statistics accurate. These should run automatically unless you have a very good reason not to.

### 3. **Partitioned Tables**
   Split large tables into smaller, manageable chunks based on time, ranges, or values. This makes queries faster and backups easier.

### 4. **Query Optimization**
   Use `EXPLAIN` to analyze queries and identify slow or inefficient patterns.

### 5. **Connection Pooling**
   Configure your application to reuse connections instead of opening new ones for every request.

### 6. **Backup and Recovery Strategies**
   Automate backups and test recovery to ensure they work when you need them.

Let’s explore these in detail with code examples.

---

## Implementation Guide

### 1. Automated Data Cleanup

Bad: Manually dropping data or relying on users to delete records.

Good: Use scheduled jobs to clean up old, unused, or invalidated data.

#### Example: Cleaning Old Order Data (PostgreSQL)
```sql
-- Drop orders older than 90 days (run via cron job)
TRUNCATE TABLE orders
WHERE order_date < CURRENT_DATE - INTERVAL '90 days'
CASCADE;
```

But wait! `TRUNCATE` is fast but irreversible. If you need to recover data, use `DELETE` instead:

```sql
-- Faster than DELETE for large tables, but no transaction log
TRUNCATE TABLE orders WHERE order_date < '2023-02-01';

-- Safer, but slower and logs each deletion
DELETE FROM orders WHERE order_date < '2023-02-01';
```

#### Example: Python Scheduler for Maintenance Tasks
```python
# Use APScheduler to run cleanup tasks hourly
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('hourly')
def cleanup_old_orders():
    connection = psycopg2.connect("dbname=your_db user=postgres")
    cursor = connection.cursor()
    cursor.execute("""
        DELETE FROM orders
        WHERE order_date < CURRENT_DATE - INTERVAL '90 days'
    """)
    connection.commit()
    cursor.close()
    connection.close()

scheduler.start()
```

**Note**: Always test your cleanup jobs in a staging environment first!

---

### 2. Auto-Vacuum and Index Optimization

PostgreSQL’s `VACUUM` and `ANALYZE` commands reclaim space and update statistics.

#### Running Vacuum (via `pg_cron`)
```sql
-- Enable cron in PostgreSQL (requires pg_cron extension)
CREATE EXTENSION pg_cron;

-- Schedule vacuum for the 'app_schema' database every 6 hours
SELECT cron.schedule(
    'every_6_hours_vacuum',
    '0 */6 * * *',
    'VACUUM ANALYZE app_schema'
);
```

#### Checking Vacuum Status
```sql
-- List tables that are worst in need of vacuum
SELECT
    schemaname || '.' || relname AS table_name,
    n_dead_tup AS dead_rows,
    reltuples AS live_rows,
    pg_size_pretty(pg_relation_size(C.oid)) AS table_size
FROM pg_stat_user_tables C
WHERE n_dead_tup > 0
ORDER BY dead_rows DESC;
```

---

### 3. Partitioning Large Tables

Partitioning splits a table into smaller pieces, improving query performance.

#### Example: Order Table by Date Range
```sql
-- Create a new partitioned table
CREATE TABLE orders (
    id SERIAL,
    customer_id INT,
    order_date TIMESTAMP,
    status VARCHAR(20),
    -- other columns
    PRIMARY KEY (id)
) PARTITION BY RANGE (order_date);

-- Create monthly partitions for the past 2 years
CREATE TABLE orders_2022_01 PARTITION OF orders
    FOR VALUES FROM ('2022-01-01') TO ('2022-02-01');

CREATE TABLE orders_2022_02 PARTITION OF orders
    FOR VALUES FROM ('2022-02-01') TO ('2022-03-01');

-- ... continue for all partitions ...
```

#### Inserting into Partitions
```sql
INSERT INTO orders (customer_id, order_date, status)
VALUES (1, '2023-11-05', 'completed') -- Automatically routes to the correct partition
```

**Pros of Partitioning**:
- Quicker queries (only scan relevant partitions).
- Easier to delete old data (`DROP TABLE orders_2020_01`).

**Cons**:
- More complex schema management.
- May require downtime for table splits.

---

### 4. Managing Long-Running Queries

Bad queries can freeze a database. Here’s how to identify and fix them.

#### Finding Slow Queries (PostgreSQL)
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = '100ms';

-- View slow queries
SELECT query, total_time, calls
FROM pg_stat_statements
ORDER BY total_time DESC;
```

#### Example: Fixing a Slow Query
**Bad Query** (forcing a full table scan):
```sql
SELECT * FROM users WHERE name LIKE '%john%';
-- Uses full scan on a non-indexed column
```

**Fixed Query** (uses index and `ILIKE`):
```sql
-- Ensure index exists
CREATE INDEX idx_users_name ON users (name);

-- Use ILIKE for case-insensitive search
SELECT * FROM users WHERE name ILIKE '%john%';
```

---

### 5. Connection Pooling

Open database connections are expensive. Use a connection pooler to reuse connections.

#### Example: Using pgBouncer
1. Install pgBouncer:
   ```sh
   sudo apt-get install pgbouncer
   ```

2. Configure `/etc/pgbouncer/pgbouncer.ini`:
   ```ini
   [databases]
   your_db = host=localhost port=5432 dbname=your_db user=pgbouncer

   [pgbouncer]
   auth_type = md5
   auth_file = /etc/pgbouncer/userlist.txt
   pool_mode = transaction
   max_client_conn = 1000
   default_pool_size = 20
   ```

3. Client code now connects to pgBouncer instead of the database directly:
   ```python
   # Connecting to pgBouncer instead of PostgreSQL directly
   connection = psycopg2.connect("host=localhost port=6432 dbname=your_db")
   ```

**Why This Matters**:
- Reduces overhead of opening/closing connections.
- Limits total connections to the database (protecting from connection leaks).

---

## Common Mistakes to Avoid

1. **Ignoring `ANALYZE`**
   If you don’t run `ANALYZE`, PostgreSQL’s query planner won’t have accurate statistics, leading to slow queries.

2. **Not Testing Cleanup Jobs in Staging**
   Always verify your `TRUNCATE` or `DELETE` jobs in a test environment first.

3. **Over-Partitioning**
   If you have too many partitions, the overhead of managing them can outweigh the benefits.

4. **Leaking Database Connections**
   Forgetting to close connections in error-handling paths leads to connection pools growing indefinitely.

5. **Assuming "Big Enough" RAM Fixes Everything**
   RAM alone won’t solve index fragmentation or bad query patterns.

---

## Key Takeaways

- **Maintenance is not a one-time task.** Databases require *ongoing* care to stay fast and reliable.
- **Automate cleanup jobs** to avoid manual errors and ensure consistency.
- **Monitor and optimize** queries regularly to catch performance issues early.
- **Use partitioning** for large tables to improve query performance and reduce backup times.
- **Connection pooling** is cheaper than opening and closing connections for every request.
- **Test in staging** before applying changes to production.

---

## Conclusion

Availability Maintenance isn’t glamorous—it’s not a shimmering new feature or a cool microservice. But like brushing your teeth or changing your car’s oil, it’s *essential* to keep things running smoothly.

Without proper maintenance, even a well-designed database will slow down, become unreliable, and eventually break under the weight of unchecked growth. The Availability Maintenance pattern gives you the tools to keep your database happy and performant for years.

Start small. Pick one area (like cleanup jobs or connection pooling) and improve it this week. Then expand. Your future self will thank you when the system handles traffic without stumbling.

---
```

---
**TL;DR:**
This post covers the **Availability Maintenance pattern**—a practical, code-first guide to keeping databases performant and reliable long-term. It includes real-world SQL examples, Python automation scripts, and pitfalls to avoid, with a focus on proactive maintenance, not reactive fixes. By automating cleanup, optimizing queries, and managing connections efficiently, you’ll ensure your database stays fast and scalable. 🚀