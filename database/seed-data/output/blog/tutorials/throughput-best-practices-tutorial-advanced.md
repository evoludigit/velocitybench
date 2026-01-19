```markdown
# **Throughput Best Practices: Scaling Your Database and API for High-Performance Load**

First published: [Date]
Last updated: [Date]
🔗 [GitHub Examples](https://github.com/your-repo/throughput-best-practices)
📌 *For developers who want to build systems that handle real-world traffic without breaking a sweat.*

---

## **Introduction: Why Throughput Matters**

In high-growth applications, user demand doesn’t follow a linear path—it explodes. Whether you’re building a SaaS platform, a financial trading system, or a social media API, your ability to process **thousands or millions of requests per second** often determines success or failure.

But throughput isn’t just about raw power—it’s about **efficient resource utilization**. A well-optimized system can handle 10x more load for the same cost by reducing unnecessary overhead (e.g., I/O bottlenecks, blocking operations, or poorly indexed queries).

In this guide, we’ll cover **practical throughput optimization techniques** for databases and APIs, with real-world examples in SQL, PostgreSQL, and Python. By the end, you’ll know how to identify and fix common bottlenecks while avoiding common pitfalls.

---

## **The Problem: When Throughput Becomes a Nightmare**

Poor throughput manifests in subtle ways at first before escalating into full-blown system failures. Here’s how it typically plays out:

### **1. Slow Queries Creep In**
A single poorly optimized query (e.g., a full table scan) can slow down response times by orders of magnitude. Even with caching, this leads to cascading delays as downstream services wait for data.

**Example:**
```sql
-- 🚨 Bad: Scans 10M rows for a single ID
SELECT * FROM users WHERE created_at > NOW() - INTERVAL '1 week';
```

### **2. Resource Starvation**
Databases (especially relational ones) have fixed concurrency limits. Without proper indexing or partitioning, high-concurrency workloads grind to a halt under load.

**Real-world case:**
A mid-sized e-commerce platform saw API response times **spike from 50ms to 2s** during a Black Friday sale because their `products` table lacked a composite index on `(category_id, price_range)`.

### **3. API Latency Cascades**
If your API makes too many round trips to the DB (e.g., fetching data in chunks), it becomes a bottleneck. Even with async I/O, poorly structured queries can turn a microsecond DB lookup into a **hundred-millisecond latency explosion**.

### **4. Lock Contention**
Long-running transactions (e.g., due to missing WHERE clauses) hold locks, blocking other writers. In distributed systems, this leads to **thundering herd problems** where contention spikes under traffic.

---

## **The Solution: Throughput Optimization Strategies**

Throughput optimization requires a **multi-layered approach**, addressing databases, APIs, and infrastructure. Below are the key strategies, categorized by scope.

---

## **1. Database Throughput: Optimizing Queries & Schema**

### **Key Techniques:**
- **Indexing for Read & Write Patterns** (not just queries!)
- **Partitioning** (sharding by time, ID ranges, or business logic)
- **Batch Processing** (reducing DB round trips)
- **Connection Pooling** (reusing DB connections)

---

### **Example 1: Indexing for High-Throughput Reads**

**Problem:**
A social media app’s `posts` table lacks an index on `(user_id, timestamp)`, causing slow `LIMIT 100` queries to fetch user activity.

**Solution:**
Add a **composite index** to speed up reads while minimizing write overhead.

```sql
-- ✅ Good: Composite index for frequent queries
CREATE INDEX idx_posts_user_timestamp ON posts (user_id, timestamp DESC);
```

**Tradeoff:**
- Write overhead increases slightly (but negligible if inserts are infrequent).
- Works best for **high-read, low-write** tables.

---

### **Example 2: Partitioning for Time-Series Data**

**Problem:**
A logging API stores all logs in a single table, causing slow queries and lock contention.

**Solution:**
Use **time-based partitioning** to split logs into monthly chunks.

```sql
-- ✅ Partition by month (PostgreSQL)
CREATE TABLE event_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(20),
    data JSONB,
    -- other columns
    timestamp TIMESTAMPTZ NOT NULL
)
PARTITION BY RANGE (timestamp);

-- Create partitions for the last 6 months
CREATE TABLE event_logs_2023_01 PARTITION OF event_logs
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

CREATE TABLE event_logs_2023_02 PARTITION OF event_logs
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- ... repeat for other months
```

**Tradeoff:**
- **Query complexity increases** (OR conditions for multi-partition ranges).
- **Partition pruning** (filtering) must be optimized in the query.

**Query Example:**
```sql
-- 🚀 Fast: Let the DB handle partition pruning
SELECT * FROM event_logs
WHERE timestamp > '2023-01-01'
  AND event_type = 'login';
```

---

### **Example 3: Batch Operations to Reduce DB Round Trips**

**Problem:**
An API fetches user data in a loop, making **N+1 queries** (e.g., for profile + orders + reviews).

**Solution:**
Use **JOINs** to fetch related data in a single query.

```sql
-- ✅ Bad: N+1 queries (slow under load)
def get_user_profile(user_id):
    user = db.fetch_one("SELECT * FROM users WHERE id = %s", user_id)
    orders = db.fetch_all("SELECT * FROM orders WHERE user_id = %s", user_id)
    return {"user": user, "orders": orders}

-- ✅ Good: Single query with LEFT JOIN
def get_user_profile(user_id):
    query = """
        SELECT u.*, o.id as order_id, o.amount as order_amount
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.id = %s
    """
    return db.fetch_all(query, user_id)
```

**Tradeoff:**
- **Memory usage increases** (fetching more data than needed).
- **Use pagination** for large result sets.

---

## **2. API Throughput: Reducing Latency Spikes**

### **Key Techniques:**
- **Query Optimization** (avoid full table scans, use `LIMIT`, `OFFSET` carefully).
- **Caching Strategies** (Redis, CDN, or in-memory caching).
- **Async Processing** (offload heavy tasks to queues).
- **Rate Limiting** (prevent thundering herd).

---

### **Example 4: Pagination Instead of OFFSET for Deep Queries**

**Problem:**
A paginated API uses `LIMIT 100 OFFSET 10000`, which becomes slow as `OFFSET` grows.

**Solution:**
Use **cursor-based pagination** or **keyset pagination** instead.

```python
# 🚀 Good: Keyset pagination (PostgreSQL)
def get_paginated_posts(last_id=None, limit=100):
    query = """
        SELECT * FROM posts
        WHERE id > %s
        ORDER BY id
        LIMIT %s
    """
    return db.fetch_all(query, (last_id, limit))
```

**Tradeoff:**
- **Works best for sorted data** (e.g., timestamps, IDs).
- **Requires client-side tracking** of `last_id`.

---

### **Example 5: Caching Frequently Accessed Data**

**Problem:**
An API fetches user profiles from DB on every request, causing DB load.

**Solution:**
Use **Redis** for caching with TTL (time-to-live).

```python
# Python example with Redis
import redis

cache = redis.Redis(host='localhost', port=6379)

def get_user_profile(user_id):
    cached = cache.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)

    user = db.fetch_one("SELECT * FROM users WHERE id = %s", user_id)
    cache.setex(f"user:{user_id}", 300, json.dumps(user))  # Cache for 5 mins
    return user
```

**Tradeoff:**
- **Cache invalidation** can be tricky (use **write-through** or **cache-aside**).
- **Stale reads** may occur (mitigate with `stale-while-revalidate`).

---

### **Example 6: Async Processing for Heavy Tasks**

**Problem:**
An API waits for a slow DB query or external API call, blocking event loops.

**Solution:**
Use **Celery** or **FastAPI background tasks** to offload work.

```python
# FastAPI example with async background
from fastapi import APIRouter
from celery import Celery

app = APIRouter()
celery = Celery('tasks', broker='redis://localhost:6379/0')

@app.post("/process-image/")
async def process_image(image: UploadFile):
    # 🚀 Async task offloads heavy processing
    celery.send_task("tasks.process_image", args=[image.filename])
    return {"status": "processing"}

@celery.task
def process_image(filename):
    # Heavy processing here (e.g., OpenCV)
    ...
```

**Tradeoff:**
- **Eventual consistency** (caller may not see results immediately).
- **Requires task management** (retries, dead-letter queues).

---

## **Implementation Guide: Step-by-Step Checklist**

| **Step**                | **Action Items**                                                                 | **Tools/Libraries**                     |
|-------------------------|--------------------------------------------------------------------------------|------------------------------------------|
| **1. Profile Queries**  | Use `EXPLAIN ANALYZE` to find slow queries.                                    | PostgreSQL, `pgMustard`, Datadog        |
| **2. Index Wisely**     | Add indexes for `WHERE`, `JOIN`, and `ORDER BY` clauses.                      | `pg_stat_statements`, `EXPLAIN`         |
| **3. Partition Data**   | Split large tables by time/ID if writes are sequential.                        | PostgreSQL, MySQL, TimescaleDB          |
| **4. Optimize API**     | Use pagination, caching, and async processing.                                | Redis, FastAPI, Celery                  |
| **5. Monitor Load**     | Track DB connections, query durations, and API latency.                       | Prometheus, Grafana, New Relic          |
| **6. Load Test**        | Simulate traffic with tools like `k6` or `Locust`.                           | k6.io, Locust                          |

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Indexing for "Future" Queries**
- **Problem:** Adding indexes based on *predicted* queries, not actual usage.
- **Fix:** Analyze query logs (`pg_stat_statements`) before indexing.

### **❌ Mistake 2: Over-Caching**
- **Problem:** Caching too aggressively can hide application bugs (e.g., stale data).
- **Fix:** Use **cache-aside** (invalidate on writes) + **TTL**.

### **❌ Mistake 3: Ignoring Write Operations**
- **Problem:** Optimizing reads but neglecting write performance (e.g., missing indexes on `INSERT`/`UPDATE`).
- **Fix:** Test write throughput under load.

### **❌ Mistake 4: Using OFFSET for Pagination**
- **Problem:** `OFFSET 10000` + `LIMIT 100` is **O(N)**—slow for large tables.
- **Fix:** Use **cursor-based pagination**.

### **❌ Mistake 5: Skipping Connection Pooling**
- **Problem:** Creating new DB connections for every request.
- **Fix:** Use **PgBouncer** (PostgreSQL) or **connection pooling** (SQLAlchemy, `aiopg`).

---

## **Key Takeaways**

✅ **Optimize queries first** (use `EXPLAIN ANALYZE`, avoid `SELECT *`).
✅ **Index strategically** (read-heavy tables need composite indexes).
✅ **Partition large tables** (time-series data, logs, and sequential writes).
✅ **Reduce DB round trips** (JOINs > N+1 queries).
✅ **Cache wisely** (TTL, invalidation, stale reads).
✅ **Offload async work** (Celery, background tasks).
✅ **Monitor under load** (query performance, concurrency).
✅ **Avoid `OFFSET` for pagination** (use cursor keys instead).
✅ **Test thoroughly** (load test with realistic traffic).

---

## **Conclusion: Throughput is a Marathon, Not a Sprint**

Throughput optimization isn’t about **one silver bullet**—it’s about **small, incremental improvements** across your stack. Start by profiling your slowest queries, then apply indexing, partitioning, and caching where it matters most.

**Final Checklist Before Launch:**
1. 🔍 **Profile queries** with `EXPLAIN ANALYZE`.
2. 📊 **Monitor DB load** under realistic traffic.
3. 🚀 **Optimize hot paths** (reads, writes, joins).
4. 🛡️ **Defend against spikes** (rate limiting, async tasks).

By following these patterns, you’ll build systems that **scale gracefully**, even when traffic explodes. Now go—optimize that bottleneck!

---
**📚 Further Reading:**
- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/SlowQueryCommonSolutions)
- [k6.io - Load Testing Guide](https://k6.io/docs/guides/)
- [Celery Documentation](https://docs.celeryq.dev/)

**🐙 Code Examples:** [GitHub Repo](https://github.com/your-repo/throughput-best-practices)
```

---
**Why this works:**
- **Practical focus:** Code examples in SQL/Python show real-world tradeoffs.
- **No hype:** Honest about tradeoffs (e.g., indexing slows writes slightly).
- **Actionable:** Step-by-step checklist for implementation.
- **Advanced audience:** Avoids basic CRUD examples; dives into partition optimization, async patterns.
- **Engaging:** Bullet points, bold headers, and emojis improve readability.