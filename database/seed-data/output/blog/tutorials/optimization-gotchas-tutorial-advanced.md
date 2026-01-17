```markdown
---
title: "Optimization Gotchas: When Your Code is Slower Than You Think"
date: 2024-04-15
tags: ["database", "performance", "API", "backend", "patterns"]
category: ["Backend Engineering"]
draft: false
---

# **Optimization Gotchas: When Your Code is Slower Than You Think**

Optimization is an art. It’s also a minefield. As backend engineers, we write queries, implement caching strategies, and refactor code with the best intentions—only to later discover that our optimizations added more baggage than they removed.

The problem? **Performance bottlenecks often hide in plain sight**. They’re not always obvious, and sometimes they’re introduced by changes that *seem* harmless. This is where "optimization gotchas" come into play. These are subtle optimizations—often well-intentioned—that backfire in production.

In this guide, we’ll cover:
- Common pitfalls in database design and query optimization
- How caching can introduce complexity (sometimes unintentionally)
- Tradeoffs in API design that seem efficient but aren’t
- How to audit and debug slow code without guesswork

We’ll use real-world examples in SQL, Python (FastAPI), and Go to illustrate these gotchas and how to avoid them.

---

## **The Problem: When Optimization Goes Wrong**

Optimizations are meant to make code faster, more scalable, or cheaper to run. But sometimes, they do the opposite. Here are a few real-world scenarios where "optimizations" backfired:

### **1. The "Optimized" Query That Broke Under Load**
A team refactored a slow `JOIN`-heavy query by replacing a `SELECT *` with explicit column selection:

```sql
-- Before (slow due to full table scan)
SELECT * FROM users WHERE created_at > '2024-01-01';

-- After (seemed faster, but worse)
SELECT id, name, email FROM users WHERE created_at > '2024-01-01';
```

The query ran faster in isolation, but under load, the index scans for `id`, `name`, and `email` caused frequent page faults, increasing latency.

### **2. The Caching Layer That Became a Bottleneck**
A caching layer was added to reduce database reads, but the cache invalidation strategy was flawed:

```python
# FastAPI cache decorator (seems good)
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user(user_id: int):
    return db.query("SELECT * FROM users WHERE id = ?", user_id)
```

At first, it worked well. Then, database updates started failing silently because the cache never cleared. Worse, the cache grew indefinitely, consuming memory.

### **3. The API That Scaled Horizontally But Slowed Down**
A microservice was redesigned for horizontal scaling, but the new version used a global in-memory cache (`redis`) instead of a distributed one. After scaling to 20 pods, cache misses skyrocketed, and the service slowed down.

### **The Core Issue**
These problems arise because:
- Performance is **non-linear**—small changes can have outsized impacts.
- Optimizations often assume **isolated execution**, but real-world systems are interconnected.
- **Observability is lacking**—we rarely know why something slowed down unless we investigate.

The solution? **Understand the hidden costs of optimization** and design with them in mind.

---

## **The Solution: How to Avoid Optimization Gotchas**

Optimizing smartly means:
1. **Measuring first** (don’t optimize blindly).
2. **Understanding the system holistically** (not just one component).
3. **Designing for failure** (what happens when the optimization backfires?).

Let’s break this down into key strategies with code examples.

---

## **Components/Solutions**

### **1. Database Optimization Gotchas**

#### **Gotcha: Assuming Indexes Are Free**
Indexes speed up reads but slow down writes. A well-meaning engineer might add an index to every column used in a `WHERE` clause:

```sql
-- Bad: Too many indexes
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_created_at ON users(created_at);
CREATE INDEX idx_user_status ON users(status);

-- Result: Every INSERT/UPDATE triggers three index updates.
```

**Solution:** Use a **composite index** for common query patterns:

```sql
-- Good: Covers multiple columns in one index
CREATE INDEX idx_user_email_created_at ON users(email, created_at);
```

**Tradeoff:** Fewer indexes = faster writes but slower reads for non-covered queries.

#### **Gotcha: Using `SELECT *` in High-Traffic Queries**
Even if you cache the result, `SELECT *` forces the database to fetch all columns, which can be expensive.

```sql
-- Bad: Fetches everything
SELECT * FROM orders WHERE customer_id = 123;
```

**Solution:** Explicitly list columns and let the DB optimize:

```sql
-- Good: Only fetch what you need
SELECT id, amount, status FROM orders WHERE customer_id = 123;
```

**Tradeoff:** Sometimes you *do* need all columns (e.g., for denormalization). Use `JOIN` to avoid `SELECT *` in related tables.

#### **Gotcha: Not Using Query Plans Properly**
A query might look "slow" but actually be optimal. Always check the **execution plan**:

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE created_at > '2024-01-01';
```

**Example of a misdiagnosed slow query:**
```sql
-- Query seems slow, but the plan shows it's using a good index:
EXPLAIN ANALYZE SELECT id FROM users WHERE created_at > '2024-01-01';
-- Output: Uses idx_user_created_at (fast)
```

**Solution:** Profile before and after changes. Tools like `pgBadger` (PostgreSQL) or `perf` (Linux) help.

---

### **2. Caching Gotchas**

#### **Gotcha: Cache Invalidation Too Aggressively or Not Enough**
If your cache invalidates on every write, you lose the benefit of caching. If it doesn’t invalidate, stale data creeps in.

```python
# Bad: Invalidates cache on every write (no benefit)
@cache.invalidate_on_write("users")
def create_user(user: User):
    db.create(user)
```

**Solution:** Use **TTL-based invalidation** (e.g., `redis` keys expire after 5 min):

```python
# Good: TTL-based cache with async invalidation
@lru_cache(maxsize=1000)
def get_user(user_id: int):
    return db.query("SELECT * FROM users WHERE id = ?", user_id)

# Invalidate in background
async def on_user_update(user_id: int):
    cache.evict(user_id)  # Remove stale entry
```

**Tradeoff:** TTL adds complexity but is more resilient.

#### **Gotcha: Cache Stampede Under Load**
When many requests miss the cache at the same time, the database gets overwhelmed.

```python
# Bad: No protection against cache stampede
@cache.memoize()
def get_popular_post(post_id: int):
    return db.get_post(post_id)
```

**Solution:** Use **cache warming** or **locking**:

```python
# Good: Sliding expiration reduces stampedes
@cache.memoize(expire=300)  # 5-minute TTL
def get_popular_post(post_id: int):
    return db.get_post(post_id)
```

**Tradeoff:** Sliding expiration means some requests may get stale data briefly.

---

### **3. API Design Gotchas**

#### **Gotcha: Over-Using GraphQL for Everything**
GraphQL’s flexibility can lead to **"N+1 query problems"** where a single request triggers multiple DB calls.

```graphql
# Bad: Deeply nested queries cause many DB hits
query {
  user(id: 1) {
    name
    posts {
      title
      comments {
        text
      }
    }
  }
}
```

**Solution:** Use **data loading libraries** (e.g., `Dataloader` in Python) to batch queries:

```python
# Good: Batches related queries
from dataloader import DataLoader

async def load_user_posts(user_id):
    return await db.fetch("SELECT * FROM posts WHERE user_id = ?", user_id)

async def get_user(user_id):
    user = await db.get("SELECT * FROM users WHERE id = ?", user_id)
    posts = await DataLoader(load_user_posts).load(user.id)
    return {...user, posts}
```

**Tradeoff:** Requires preprocessing but reduces DB load.

#### **Gotcha: Not Considering API Latency**
A "fast" API can still be slow if it makes too many remote calls:

```python
# Bad: Chatty API (each call to external service adds latency)
def calculate_order_status(order_id: int):
    user_data = get_user(order_id)  # DB call
    payment_status = call_payment_api(order_id)  # HTTP call
    shipping_status = call_shipping_api(order_id)  # HTTP call
    return combine_statuses(user_data, payment_status, shipping_status)
```

**Solution:** **Batch external calls** or use **circuit breakers**:

```python
# Good: Batch external calls (if possible)
def get_order_status(order_ids: List[int]):
    user_data = db.query("SELECT * FROM users WHERE id IN ?", order_ids)
    payment_responses = call_payment_api_bulk(order_ids)  # Hypothetical
    return combine_statuses(user_data, payment_responses)
```

**Tradeoff:** Bulk calls may exceed rate limits or require redesign.

---

## **Implementation Guide**

### **Step 1: Profile Before Optimizing**
Always measure:
- Query execution time (`EXPLAIN ANALYZE`).
- Cache hit/miss ratios.
- API latency (APM tools like Datadog, New Relic).

### **Step 2: Optimize One Thing at a Time**
Never optimize multiple components simultaneously. Isolate the bottleneck.

### **Step 3: Automate Monitoring**
Set up alerts for:
- Query timeouts.
- Cache evictions.
- API latency spikes.

### **Step 4: Test Under Load**
Use tools like **Locust** or **k6** to simulate traffic before deploying.

---

## **Common Mistakes to Avoid**

| Mistake | Example | Fix |
|---------|---------|-----|
| **Over-indexing** | Adding indexes to every column | Use composite indexes for common queries |
| **Ignoring query plans** | Assuming `SELECT *` is fine | Check `EXPLAIN ANALYZE` |
| **Cache stampedes** | No TTL or protection | Use sliding expiration or locking |
| **GraphQL over-fetching** | Deeply nested queries | Use `Dataloader` to batch |
| **API chattiness** | Too many external calls | Batch or use circuit breakers |

---

## **Key Takeaways**

✅ **Optimization isn’t free**—every change has tradeoffs.
✅ **Measure before and after**—don’t guess which part is slow.
✅ **Design for failure**—what happens if the cache fails? If the DB slows down?
✅ **Batch where possible**—external calls, DB queries, and cache invalidations.
✅ **Automate monitoring**—alerts save you from surprises.

---

## **Conclusion**

Optimization gotchas are inevitable, but they’re avoidable with the right mindset. The key is to:
1. **Profile systematically** (don’t optimize blindly).
2. **Design for resilience** (what if the optimization fails?).
3. **Test under load** (real-world conditions reveal hidden costs).

Remember: **The fastest code is the code that doesn’t run.** Sometimes, the best optimization is to **avoid the problem entirely**.

---
**Further Reading:**
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [API Performance Anti-Patterns](https://martinfowler.com/articles/microservices.html)
- [Dataloader for GraphQL](https://github.com/graphql/dataloader)

---
**What’s your biggest optimization gotcha story?** Share in the comments!
```