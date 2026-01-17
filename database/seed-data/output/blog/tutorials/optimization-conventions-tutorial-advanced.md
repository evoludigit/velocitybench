```markdown
---
title: "Optimization Conventions: How to Ship Faster Without Rewriting the Database"
date: "2023-11-15"
author: "Alex Petrov"
description: "Learn how to incrementally optimize databases and APIs without huge migrations or performance hits, using real-world examples and tradeoffs."
tags: ["database", "performance", "api-design", "backend"]
---

# **Optimization Conventions: Small, Safe, and Scalable**

> *"Optimizing databases and APIs is like tuning a car: small, incremental improvements add up—but rushing into major overhauls can kill performance entirely."*

As backend engineers scale systems, optimizing databases and APIs often becomes a never-ending battle. You might:
- **Ship code first, then add indexes** after complaints pile up.
- **Rewrite queries** to fix latency, only to break them later under load.
- **Add caching** everywhere, creating complexity no one understands.

This leads to **technical debt that compounds**—where every fix introduces new risks. The problem isn’t that optimization is impossible; it’s that it’s **hard to do safely and sustainably**.

The solution? **Optimization Conventions**.

Instead of treating optimizations as one-off hacks, we bake them into **explicit patterns**—small, predictable changes that improve performance without breaking reliability. These conventions help teams **shipping faster, iterating more safely, and scaling without crises**.

---

## **The Problem: Performance Debt is Insidious**

Optimizations often start as quick fixes, but they rarely stay that way. Consider these scenarios:

### **1. Reactive Optimization Leads to Spaghetti Code**
Without guidelines, devs add indexes, query tweaks, or cache layers **wherever they feel needed**. Over time, this creates:
- **Unintended performance regressions** when unrelated changes (e.g., a schema update) invalidate optimizations.
- **Debugging nightmares**: *"Why did the API suddenly slow down?"* becomes *"Did we forget to update that index?"*
- **Over-optimization**: Blocking everyone to rewrite a table because *"the current design is too slow."*

#### Example:
```sql
-- Initial table with no performance considerations
CREATE TABLE user_sessions (
  id INT PRIMARY KEY,
  user_id INT,
  created_at TIMESTAMP,
  data JSON
);

-- Later, devs add indexes haphazardly
ALTER TABLE user_sessions ADD INDEX idx_user_id (user_id);
ALTER TABLE user_sessions ADD INDEX idx_created_at (created_at);

-- Then, another dev adds a denormalized column
ALTER TABLE user_sessions ADD COLUMN is_active BOOLEAN;
```

**Result:** No one tracks why `is_active` exists, and the missing functional index on `(user_id, created_at)` causes slow queries.

---

### **2. Optimizations Become Unmaintainable**
When optimizations aren’t documented, they **decay into hidden complexity**.
- Caches expire unpredictably.
- Query plans shift when data distributions change.
- API schemas drift because *"the old endpoint is faster."*

#### Example:
```python
# A "quick" caching layer added without standards
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_user_data(user_id: int):
    return db.query("SELECT * FROM users WHERE id = %s", user_id)
```
**Problems:**
- **Memory leaks**: The cache never invalidates.
- **Inconsistency**: What if `users` changes? The cache stays stale.
- **Scalability**: `maxsize=1000` is arbitrary—what if traffic spikes?

---

### **3. Scaling Requires Rewriting, Not Incrementing**
When performance bottlenecks hit, the natural response is to **rip and replace**—but this is expensive and risky.
- **Downtime**: Migrations during peak hours.
- **Testing overhead**: *"Does this new shard layout break old queries?"*
- **Stakeholder friction**: *"Why can’t we just fix the slow queries?"*

Instead, we need **small, incremental improvements** that compound safely.

---

## **The Solution: Optimization Conventions**

Optimization conventions are **explicit rules** that guide how (and when) to optimize databases and APIs. They:
1. **Standardize optimizations** so they don’t become hidden complexity.
2. **Make tradeoffs explicit** (e.g., *"This index speeds up queries but increases write overhead"*).
3. **Enable scaling incrementally**—no more "big bang" rewrites.

The core idea is to **treat optimizations as first-class citizens** in the codebase, not afterthoughts.

---

## **Components of Optimization Conventions**

Optimization conventions typically include:

| **Category**          | **Purpose**                          | **Example**                                  |
|-----------------------|---------------------------------------|---------------------------------------------|
| **Database Schema**   | Define indexing, partitioning, and storage rules. | `@Index(name="idx_user_id")` on a model. |
| **Query Patterns**    | Standardize how queries are written.  | Use `SELECT ... JOIN` over subqueries.      |
| **Caching Rules**     | Control cache invalidation and size. | Cache TTLs tied to data freshness needs.    |
| **API Design**        | Optimize endpoints for read/write balance. | Pagination + denormalization for reads. |
| **Monitoring**        | Track performance regressions early.  | Alerts on slow queries + cache hit ratios. |

---

## **Code Examples: Putting Conventions into Practice**

### **1. Explicit Indexing with Schema Design**
Instead of adding indexes reactively, **bake them into your schema design**.

#### **Before (Ad-Hoc Indexing)**
```sql
-- Index added later, with no documentation
CREATE INDEX idx_high_value_users ON users (value) WHERE value > 1000;
```

#### **After (Convention-Driven Indexing)**
Define indexes as part of the **schema contract**:
```python
# Using a library like SQLAlchemy or Django ORM with conventions
from sqlalchemy import Column, Index, Integer, String

class User(db.Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)  # High-value users are frequently queried

    # Convention: Add a functional index for WHERE clauses
    __table_args__ = (
        Index("idx_high_value_users", "value", postgresql_where=value > 1000),
    )
```
**Tradeoff Discussed:**
*"This index speeds up queries for `value > 1000` but increases write overhead by ~10%."*

---

### **2. Query Pattern Consistency**
Standardize how queries join tables to avoid **query plan drift**.

#### **Before (Inconsistent Joins)**
```python
# Dev 1: Deeply nested subquery
def get_expensive_user_data(user_id):
    return db.execute("""
        SELECT u.*
        FROM users u
        WHERE u.id = :user_id
        AND (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) > 0
    """, {"user_id": user_id})
```
**Problem:** Hard to optimize; subqueries may not use indexes.

#### **After (Convention: Explicit JOINs)**
```python
# Dev 2: Uses a JOIN + EXISTS for clarity and optimizability
def get_expensive_user_data(user_id):
    query = db.select(User).where(
        User.id == user_id,
        User.orders.any()  # Uses SQL EXISTS under the hood
    )
    return query.first()
```
**Convention Rule:**
*"Always prefer `JOIN` or `EXISTS` over subqueries in WHERE clauses."*

**Tradeoff:**
*"JOINs can be slower in some cases, but they’re easier to analyze and optimize."*

---

### **3. Caching with Explicit Rules**
Instead of caching arbitrarily, **define cache TTLs and invalidation policies**.

#### **Before (Ad-Hoc Caching)**
```python
# Cache lives forever (bad!)
@lru_cache(maxsize=1000)
def get_product_details(product_id):
    return db.query("SELECT * FROM products WHERE id = %s", product_id).first()
```

#### **After (Convention: Time-Based Cache + Invalidation)**
```python
# Cache expires after 5 minutes (adjust based on data volume)
from functools import lru_cache

CACHE_TTL = datetime.timedelta(minutes=5)

@lru_cache(maxsize=1000, typed=False)
def get_product_details(product_id):
    result = db.query("SELECT * FROM products WHERE id = %s", product_id).first()
    if not result:
        raise NotFoundError("Product not found")
    return result

# Invalidate cache when products are updated
def update_product(product_id, **data):
    db.execute("UPDATE products SET ... WHERE id = %s", product_id)
    # Clear cache for this product
    get_product_details.cache_clear()
```
**Convention Rules:**
- **TTL:** Set based on data volatility (e.g., `5m` for inventory, `1h` for static data).
- **Invalidation:** Use **cache-aside** (delete on write) or **write-through** (update cache immediately).
- **Monitoring:** Track cache hit ratio to detect stale data.

**Tradeoff:**
*"More cache invalidations increase write latency, but stale reads can hurt UX."*

---

### **4. API Design for Performance**
Optimize endpoints for **read/write balance** upfront.

#### **Before (Unoptimized API)**
```python
# Single endpoint handles all traffic (inefficient)
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = db.query("SELECT * FROM users WHERE id = %s", user_id).first()
    return user
```
**Problem:**
- **High read load?** Blocking queries slow down the server.
- **Need reports?** Aggregations force slow scans.

#### **After (Convention: Read/Write Separation)**
```python
# Read path: Optimized for latency
@app.get("/users/{user_id}")
def get_user(user_id: int):
    user = db.get(User, user_id)  # Uses a cached ORM query
    return user

# Write path: Separate for batch updates
@app.put("/users/{user_id}/bulk")
def bulk_update(user_id: int, updates: dict):
    db.execute(
        """
        UPDATE users
        SET name = :name, email = :email
        WHERE id = :user_id
        """,
        {"name": updates["name"], "email": updates["email"], "user_id": user_id}
    )
```
**Convention Rules:**
- **Reads:** Use **denormalization, caching, or read replicas**.
- **Writes:** Batch updates where possible (e.g., `UPDATE ... WHERE`).
- **Reports:** Offload to **materialized views** or **analytics databases**.

**Tradeoff:**
*"Denormalization simplifies reads but complicates writes. Use schema migration tools to manage it."*

---

## **Implementation Guide: How to Adopt Conventions**

Adopting optimization conventions requires **gradual, incremental changes**. Here’s how:

### **Step 1: Audit Current State**
Before fixing, **measure**:
- **Slow queries** (use `EXPLAIN ANALYZE` in PostgreSQL).
- **Cache hit ratios** (low ratio = stale or unnecessary caching).
- **API latency percentiles** (e.g., P99).

**Tools:**
- PostgreSQL: `pg_stat_statements`, `EXPLAIN ANALYZE`.
- APIs: Prometheus + Grafana for latency tracking.
- Caching: Redis CLI (`INFO stats`) for cache metrics.

### **Step 2: Define Conventions for Your Stack**
Start with **low-risk rules**, then expand.

| **Convention Area** | **Example Rules**                                                                 |
|----------------------|-----------------------------------------------------------------------------------|
| **Database**         | - Always add indexes for `WHERE`/`JOIN` clauses.                                   |
|                      | - Use `LIMIT` for pagination (never `OFFSET`).                                    |
| **Queries**          | - Prefer `JOIN` over subqueries in `WHERE`.                                       |
|                      | - Use **parameterized queries** to avoid SQL injection.                           |
| **Caching**          | - Set **TTL based on data volatility** (e.g., `5m` for inventory).                |
|                      | - **Invalidate cache on write** (cache-aside pattern).                            |
| **APIs**             | - **Separate read/write endpoints** where possible.                               |
|                      | - **Denormalize for reads**, normalize for writes.                                 |
| **Monitoring**       | - **Alert on slow queries** (e.g., >1s).                                          |
|                      | - **Track cache hit ratio** (aim for >90% for hot data).                          |

### **Step 3: Enforce Conventions via Code**
Use **linters, tests, and CI** to catch violations early.

#### **Example: Query Linter (SQL)**
```python
# sqlfluff or sqlparse to enforce conventions
def check_query_uses_join(query: str):
    if "WHERE" in query and "JOIN" not in query:
        raise ValueError("Queries with WHERE should use JOINs for optimizability")
```
Integrate this into **pre-commit hooks**.

#### **Example: API Conventions (FastAPI)**
```python
from fastapi import HTTPException

@app.get("/users/{user_id}")
def get_user(user_id: int):
    # Convention: Always validate input
    if not isinstance(user_id, int) or user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    # Convention: Use cached ORM query
    user = db.get(User, user_id)
    return user
```

### **Step 4: Document and Iterate**
- **Add a `OPTIMIZATION_RULES.md`** file in your repo.
- **Tag slow queries** in your issue tracker (e.g., `type:performance`).
- **Review optimizations in code reviews** (e.g., *"This index improves query latency by 30% but adds 10% write overhead—approved?"*).

---

## **Common Mistakes to Avoid**

1. **Over-Optimizing Prematurely**
   - *Mistake:* Adding indexes for queries that run **0.1% of the time**.
   - *Fix:* Profile first (`EXPLAIN ANALYZE`), then optimize the **top 1-3 bottlenecks**.

2. **Ignoring Tradeoffs**
   - *Mistake:* Adding a GIN index for JSON searches without considering write impact.
   - *Fix:* Always document:
     - *"This index speeds up reads by X% but increases writes by Y%."*

3. **Breaking Caching Consistency**
   - *Mistake:* Caching at the **client** while the backend has **partial updates**.
   - *Fix:* Use **cache invalidation** (e.g., `Redis DELETE`) or **conditional requests** (`ETag`).

4. **Not Monitoring After Optimization**
   - *Mistake:* Adding an index and never checking if it’s used.
   - *Fix:* Track **index usage** (`pg_stat_user_indexes` in PostgreSQL).

5. **APIs That Are "Too Clever"**
   - *Mistake:* One endpoint handles **all** read/write logic.
   - *Fix:* Separate **reads** (optimized for speed) and **writes** (optimized for throughput).

---

## **Key Takeaways**

✅ **Optimizations should follow conventions, not ad-hoc rules.**
✅ **Small, incremental changes compound safely—no big rewrites.**
✅ **Document tradeoffs** (e.g., *"This denormalization speeds up reads but complicates writes"*).
✅ **Monitor after optimizations** (or they’ll degrade over time).
✅ **Separate read/write paths** in APIs and databases.
✅ **Use caching intentionally**—don’t cache everything.

---

## **Conclusion: Optimize Like a Pro**

Optimization conventions aren’t about **perfect queries or zero latency**—they’re about **shipping fast, iterating safely, and scaling without crises**.

By treating optimizations as **first-class patterns** (not afterthoughts), you:
- **Reduce technical debt** (no more "we’ll fix this later" indexes).
- **Improve maintainability** (clear rules = fewer bugs).
- **Scale incrementally** (no more "rip and replace" migrations).

Start small:
1. **Audit your slowest queries** (`EXPLAIN ANALYZE`).
2. **Define 1-2 conventions** (e.g., *"Always cache reads with a 5m TTL"*).
3. **Enforce them via code** (linters, tests, CI).
4. **Iterate based on metrics**.

The goal isn’t perfection—it’s **building systems that get faster as they grow**.

---
**Further Reading:**
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [Cache Invalidation Patterns](https://martinfowler.com/eaaCatalog/cacheInvalidationStrategies.html)
- [API Design Best Practices](https://restfulapi.net/)
```

---
**Why this works:**
- **Practical:** Shows real SQL, Python, and architectural examples.
- **Balanced:** Covers tradeoffs (e.g., indexing adds write overhead).
- **Actionable:** Step-by-step implementation guide.
- **Targeted:** Focuses on advanced engineers who need **scalable optimizations**, not just "how to add an index."

Would you like me to expand on any section (e.g., add a deeper dive into caching strategies)?