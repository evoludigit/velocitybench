```markdown
---
title: "Throughput Conventions: Designing APIs That Scale Without Exploding"
date: 2023-11-15
author: "Alex Carter"
description: "Learn how throughput conventions can prevent API bottlenecks, optimize database queries, and scale your applications predictably. Real-world patterns and tradeoffs explained."
tags: ["database design", "API patterns", "scalability", "backend engineering", "caching", "performance optimization"]
---

# Throughput Conventions: Designing APIs That Scale Without Exploding

![Throughput Conventions](https://images.unsplash.com/photo-1631679706909-f2a7faaa4b14?ixlib=rb-4.0.3&auto=format&fit=crop&w=1350&q=80)

When your API starts receiving 10x the traffic overnight, you expect *scalability*. You don’t expect your database to turn into a performance black hole, your caching layer to become a gating factor, or your application to spiral into a race condition nightmare. Yet, many systems fail spectacularly when load increases—not because of technical debt, but because they lack a foundational principle: **throughput conventions**.

Throughput conventions are the unseen rules that govern how your system processes requests at scale. They define how requests are distributed, how data is accessed, how resources are shared, and how dependencies are managed. Without explicit throughput conventions, your system’s behavior becomes unpredictable. A seemingly innocuous change (like adding a new query or changing a cache key) might suddenly turn a fast API into a slow one, or a stable system into a fragile one.

In this post, we’ll explore:
- Why throughput conventions matter—and what happens when they’re missing.
- The core components of throughput conventions (e.g., partitioning, caching, and concurrency strategies).
- Practical code examples (written in Go and Python) to demonstrate how throughput conventions work in real systems.
- Common pitfalls and how to avoid them.
- Tradeoffs and when to deviate from strict conventions.

---

## The Problem: Chaos Without Throughput Conventions

Imagine this scenario: You’re responsible for an e-commerce API that handles user profiles, product catalogs, and order processing. Initially, traffic is light, so you design your system with simplicity in mind. You use a single database table for products, fetch all fields on every request, and rely on application-level caching (like Redis) for popular items. Everything works fine until Black Friday.

Suddenly, your database hits 10,000 queries per second. The API starts timing out. Redis becomes a bottleneck as it floods with requests for cache misses. You notice that some requests take 50ms while others take 5 seconds—randomly. You introduce a new feature to recommend products based on user history, and suddenly, the latency spikes again.

What went wrong? You didn’t explicitly define throughput conventions. Here’s what happened under the hood:

1. **Unbounded Query Patterns**: Your original design fetched all product fields (e.g., `SELECT * FROM products`) for every request. As traffic increased, the database couldn’t keep up with the payload size.
2. **No Partitioning**: All queries hit the same database partitions, leading to hotspots. The database’s read-replica couldn’t handle the load without data skew.
3. **Cache Invalidation Chaos**: Redis was acting as a global cache, but your application didn’t coordinate cache keys or TTLs. Updates to products invalidated the cache unpredictably, causing cache stampedes (thundering herds).
4. **Concurrency Nightmares**: Without explicit locking or retries, concurrent requests could overwrite each other’s changes, leading to race conditions (e.g., lost updates in inventory).

This isn’t just a hypothetical. I’ve seen teams spend months debugging these issues after the fact—only to realize they could have avoided them with a few simple throughput conventions upfront.

---

## The Solution: Throughput Conventions

Throughput conventions are the **rules of engagement** for how your system handles load. They address three key dimensions:
1. **Data Access**: How requests fetch and modify data (e.g., query patterns, indexing, pagination).
2. **Resource Sharing**: How requests compete for shared resources (e.g., caching, database connections, locks).
3. **Dependency Management**: How requests interact with external systems (e.g., retries, circuit breakers).

The goal is to create a system where:
- **Predictable Latency**: Requests consistently perform within expected bounds.
- **Fair Concurrency**: No request starves another for resources.
- **Graceful Degradation**: The system fails predictably (e.g., timeouts, retries) rather than crashing.

---

## Components of Throughput Conventions

### 1. Query Patterns: Avoid the SELECT *
**Problem**: Fetching all columns (`SELECT *`) is convenient but scales poorly. As traffic grows, the payload size increases, and the database spends more time transferring data than processing it.

**Solution**: Use **explicit column selection** and **denormalized views** for common query patterns.

#### Code Example: Explicit Column Selection
```sql
-- Bad: Fetches all columns (e.g., 100 columns for a single product).
SELECT * FROM products WHERE id = 123;

-- Good: Only fetches the columns needed for the API response.
SELECT id, name, price, stock_quantity FROM products WHERE id = 123;
```

#### Denormalized Views for Performance
```sql
-- Create a view for the most common query: product details + user ratings.
CREATE VIEW product_with_ratings AS
SELECT p.id, p.name, p.price, p.stock_quantity,
       AVG(r.rating) as avg_rating
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id;
```

#### Implementation in Go
```go
type ProductRequest struct {
    ID int
}

type ProductResponse struct {
    ID          int     `json:"id"`
    Name        string  `json:"name"`
    Price       float64 `json:"price"`
    Stock       int     `json:"stock"`
    AvgRating   float64 `json:"avg_rating,omitempty"` // Optional field
}

func GetProduct(db *sql.DB, req ProductRequest) (ProductResponse, error) {
    var res ProductResponse
    // Explicitly select only needed columns.
    query := `
        SELECT id, name, price, stock_quantity,
               (SELECT AVG(rating) FROM reviews WHERE product_id = p.id) as avg_rating
        FROM products p
        WHERE id = $1
        LIMIT 1
    `
    err := db.QueryRow(query, req.ID).Scan(
        &res.ID, &res.Name, &res.Price, &res.Stock, &res.AvgRating,
    )
    return res, err
}
```

---

### 2. Partitioning: Distribute Load Evenly
**Problem**: Without partitioning, all queries hit the same data shard, creating bottlenecks (hotspots). For example:
- A single table for all users in a global app.
- A monolithic queue handling all events.

**Solution**: Use **sharding** or **partitioning keys** to distribute load.

#### Example: User Table Sharding
```sql
-- Partition users by geographic region (e.g., us-east, eu-west).
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL
) PARTITION BY LIST (username[1]);

-- Create partitions for each region.
CREATE TABLE users_us PARTITION OF users
    FOR VALUES IN ('us-');

CREATE TABLE users_eu PARTITION OF users
    FOR VALUES IN ('eu-');
```

#### Implementation in Python (using `psycopg2`)
```python
import psycopg2
from psycopg2 import sql

def get_user(db_conn, username: str) -> dict:
    # Construct a dynamic query to partition by the user's region.
    partition_query = sql.SQL("users_{}").format(
        sql.Identifier(username[:2].lower())  # e.g., 'us', 'eu'
    )
    query = sql.SQL("SELECT * FROM {} WHERE username = %s").format(partition_query)

    with db_conn.cursor() as cur:
        cur.execute(query, (username,))
        return cur.fetchone()
```

#### Tradeoff: Sharding Complexity
- **Pros**: Even distribution of load, horizontal scalability.
- **Cons**: Requires application-aware routing (e.g., consistent hashing), cross-partition joins are expensive.

---

### 3. Caching: Avoid Cache Stampedes
**Problem**: Without cache TTLs or invalidation strategies, cache misses trigger a flood of database requests (thundering herd problem).

**Solution**: Use **time-based TTLs** + **eventual consistency** for cache invalidation.

#### Example: Redis Cache with TTL
```go
// Set cache with a 5-minute TTL.
cacheKey := fmt.Sprintf("product:%d", productID)
err := redisClient.Set(cacheKey, jsonData, 5*time.Minute).Err()
if err != nil {
    log.Printf("Failed to cache product %d: %v", productID, err)
}

// Get with caching.
var cachedData string
if err := redisClient.Get(&cachedData, cacheKey).Err(); err == nil {
    return cachedData
}
// ... (fallback to database)
```

#### Cache Invalidation Strategy
```go
// Invalidate cache on product update.
func UpdateProduct(db *sql.DB, redisClient *redis.Client, product Product) error {
    _, err := db.Exec(updateQuery, product)
    if err != nil {
        return err
    }
    // Invalidate cache for this product.
    cacheKey := fmt.Sprintf("product:%d", product.ID)
    return redisClient.Del(cacheKey).Err()
}
```

#### Tradeoff: Stale Data
- **Pros**: Reduced database load, faster reads.
- **Cons**: Read-staleness (e.g., users see old prices). Mitigate with:
  - **Short TTLs** for volatile data.
  - **Write-through caching** (update cache + database atomically).

---

### 4. Concurrency Control: Avoid Race Conditions
**Problem**: Concurrent requests can overwrite changes (e.g., two users incrementing inventory count simultaneously).

**Solution**: Use **optimistic locking** or **pessimistic locking** based on your needs.

#### Optimistic Locking (Recommended for Read-Heavy)
```sql
-- Add a version column to track changes.
ALTER TABLE inventory ADD COLUMN version INTEGER NOT NULL DEFAULT 0;

-- Update with check for version conflict.
UPDATE inventory
SET quantity = quantity + 1, version = version + 1
WHERE id = 123 AND version = 42;  // Expected version
```

#### Implementation in Python
```python
def increment_inventory(db_conn, product_id: int, expected_version: int) -> bool:
    query = """
        UPDATE inventory
        SET quantity = quantity + 1, version = version + 1
        WHERE id = %s AND version = %s
        RETURNING version;
    """
    with db_conn.cursor() as cur:
        cur.execute(query, (product_id, expected_version))
        result = cur.fetchone()
        return result is not None  # True if update succeeded
```

#### Pessimistic Locking (For Write-Heavy)
```sql
-- Acquire a lock before updating.
BEGIN;
SELECT pg_advisory_xact_lock(123);  -- Lock for this product.
UPDATE inventory SET quantity = quantity + 1 WHERE id = 123;
COMMIT;
```

#### Tradeoffs:
- **Optimistic**: Cheaper (no locks), but requires retries.
- **Pessimistic**: Slower (blocking), but simpler to implement.

---

## Implementation Guide: Throughput Conventions in Practice

Here’s a step-by-step guide to applying throughput conventions to a new API:

### Step 1: Define Your Throughput Requirements
- **Expected QPS (Queries Per Second)**: e.g., 10,000 reads, 1,000 writes.
- **Latency SLA**: e.g., 99th percentile < 200ms.
- **Resource Constraints**: e.g., 50 concurrent database connections.

### Step 2: Design for Partitioning
- **Shard data** based on expected access patterns (e.g., by region, by tenant).
- **Avoid hotspots**: Ensure queries distribute evenly across partitions.

### Step 3: Optimize Queries
- **Replace `SELECT *`** with explicit column selection.
- **Use indexes** for join columns and filters.
- **Denormalize** for common query patterns.

### Step 4: Implement Caching Strategies
- **Cache frequently accessed data** (e.g., product listings).
- **Set appropriate TTLs** (e.g., 5 mins for prices, 1 hour for catalog data).
- **Invalidate caches** on writes (use pub/sub for distributed caches like Redis).

### Step 5: Handle Concurrency
- **Use optimistic locking** for most cases.
- **Use pessimistic locks** only for critical sections (e.g., inventory updates).

### Step 6: Test Under Load
- **Simulate traffic** with tools like Locust or k6.
- **Monitor for bottlenecks** (e.g., database queries, cache misses).
- **Adjust TTLs and retries** as needed.

---

## Common Mistakes to Avoid

1. **Ignoring Query Patterns**: Fetching `SELECT *` or using `LIKE '%search_term%'` will kill your database under load.
   - *Fix*: Use full-text search (PostgreSQL `tsvector`) or dedicated search engines (Elasticsearch).

2. **Global Caching**: Caching everything globally leads to cache stampedes and inconsistency.
   - *Fix*: Use **partitioned caching** (e.g., cache keys scoped to shards).

3. **No Retry Logic**: Failing on database timeouts causes cascading failures.
   - *Fix*: Implement **exponential backoff retries** (e.g., Go’s `database/sql` with retries).

4. **Overusing Pessimistic Locks**: Blocks all requests, killing concurrency.
   - *Fix*: Prefer optimistic locking and handle conflicts gracefully.

5. **Inconsistent TTLs**: Mixing 1-hour TTLs with 1-second TTLs makes caching unpredictable.
   - *Fix*: Align TTLs with data volatility (e.g., long TTLs for static data).

---

## Key Takeaways

- **Throughput conventions prevent chaos at scale**. They’re the difference between a system that handles 10x traffic gracefully and one that collapses.
- **Start with query patterns**. Optimize `SELECT *` → explicit columns, and denormalize for common queries.
- **Partition data strategically**. Distribute load evenly to avoid hotspots.
- **Cache aggressively, but invalidate intelligently**. Use TTLs + eventual consistency.
- **Handle concurrency with optimism (retries) or pessimism (locks)**, but avoid over-locks.
- **Test under load early**. Use tools like Locust or k6 to uncover bottlenecks before they become bugs.

---

## Conclusion

Throughput conventions aren’t just theoretical—they’re the difference between a system that scales predictably and one that surprises you with outages. By designing your API with explicit rules for query patterns, partitioning, caching, and concurrency, you build a system that can handle growth without reinventing itself every time traffic spikes.

Remember:
- **No silver bullet**: Tradeoffs exist (e.g., denormalization vs. consistency). Choose based on your use case.
- **Measure, iterate**: Use observability tools (Prometheus, Datadog) to refine your conventions over time.
- **Document your conventions**: So future developers (or you) don’t have to guess why the system behaves the way it does.

Start small—apply throughput conventions to one critical path in your API. You’ll be glad you did when Black Friday (or your next viral feature) hits.

---
```