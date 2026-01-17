```markdown
# **Performance Conventions: The Silent Speed Boost for Your APIs and Databases**

*How small, consistent choices can transform your system’s responsiveness—and why "just optimise later" is a myth.*

---

## **Introduction**

Performance isn’t just about throwing more hardware at a problem or writing complex algorithms. Often, the fastest fixes are the most mundane: **small, consistent habits** that prevent slow downs before they become bottlenecks.

This is where **"Performance Conventions"**—a design pattern focused on enforcing best practices through structure—comes into play. Unlike traditional optimisations (e.g., caching, indexing), this pattern ensures your APIs and databases *adhere to predictable, performant behaviours by default*. Think of it like coding conventions (e.g., naming styles, PEP 8) but for performance: subtle, scalable, and easy to enforce.

This post explores why performance conventions matter, how to apply them in real-world systems, and the pitfalls that trip up even experienced engineers.

---

## **The Problem: Why Performance Conventions Matter**

Performance issues often arise from **accumulated technical debt**—small, "non-critical" decisions that seem fine now but compound over time. Without conventions, teams end up with:

- **Inconsistent query patterns**: Some endpoints fetch 100 rows, others 10,000—without clear rules, every developer writes "fast enough for this case" code.
- **API anti-patterns**: Unbounded pagination (`?page=&page_size=1000`), overly chatty microservices, or data duplication because "it’s easier to fetch twice."
- **Database bloat**: Missing indexes, unoptimised joins, or even simple mistakes like saving `TEXT` fields instead of `VARCHAR` where length is known.
- **"Works on my machine" deployments**: QA environments sometimes have weaker DB configs, so performance only becomes visible in production.

Here’s a concrete example:

```sql
-- A "safe but slow" query from a team where conventions are weak
SELECT * FROM orders
WHERE customer_id = 42 AND created_at > '2023-01-01'
ORDER BY created_at DESC LIMIT 1000;
```
This *seems* fine, but what if:
- `orders` is a 100GB table?
- No index exists on `(customer_id, created_at)`?
- The team copies this pattern everywhere, adding indexes later as an afterthought?

**Result**: A 3-second query under load becomes a ticket for the "DevOps team to investigate."

Performance conventions help by:
✅ **Standardising queries** so they’re predictable and indexable.
✅ **Enforcing limits** (e.g., pagination, result set sizes) to avoid runaway costs.
✅ **Documenting expectations** so junior devs don’t accidentally introduce regressions.

---

## **The Solution: Performance Conventions in Action**

Performance conventions are **rules of engagement** for APIs and databases. They’re not a single pattern but a **system of small, enforced practices** that work together. Here’s how they look in practice:

### **1. API Design: The "Convention Over Configuration" Approach**
For APIs, conventions reduce variability by defining:
- **Pagination**: Always use `?page=1&limit=10` (never `offset`).
- **Result shapes**: Avoid `SELECT *` in favour of explicit columns.
- **Rate limits**: Enforce default limits per endpoint.

Example: A performant `GET /users` endpoint:

```python
# FastAPI example with explicit columns and pagination
from fastapi import FastAPI, Query
from typing import List

app = FastAPI()

@app.get("/users", response_model=List[User])
async def get_users(
    limit: int = Query(20, le=100),  # Enforce sane limits
    page: int = Query(1, le=1000),
):
    offset = (page - 1) * limit
    return db.query(
        "SELECT id, name, email FROM users LIMIT ? OFFSET ?",
        (limit, offset),
    )
```

**Why this matters**:
- `LIMIT` + `OFFSET` is more efficient than `WHERE id > X` for large datasets (DBs can’t index `OFFSET`).
- Explicit columns prevent accidental `SELECT *` (which can break if the table schema changes).

---

### **2. Database: Indexing and Query Patterns**
Conventions here focus on **reusable patterns** that speed up queries:
- **Default indexes**: Add `(column)` and `(column, column2)` indexes for all `WHERE`/`ORDER BY` clauses.
- **Avoid `SELECT *`**: Always specify columns.
- **Batch fetches**: Use `IN` clauses for multiple IDs instead of `OR` (e.g., `WHERE id IN (1, 2, 3)`).

Example: A convention for "safe query templates":

```python
# Template for a high-traffic query (enforced via code review)
def get_orders_for_customer(customer_id: int):
    query = """
    SELECT order_id, amount, status
    FROM Orders
    WHERE customer_id = :customer_id
    ORDER BY created_at DESC
    LIMIT 100
    """
    # Ensure indexes exist: (customer_id), (customer_id, created_at)
    return db.execute(query, {"customer_id": customer_id})
```

**Tradeoff**: Adding indexes can slow writes, so conventions often include **cost-benefit rules** (e.g., "Only index columns used in 90%+ of queries").

---

### **3. Caching: "Cache-First, Then Query"**
Conventions around caching prevent expensive DB calls by:
- **Default TTLs**: Set cache durations based on data volatility (e.g., 1 hour for product listings, 5 minutes for user sessions).
- **Cache keys**: Use consistent formats (e.g., `user:123:orders` for `/users/123/orders`).
- **Cache invalidation**: Enforce automated invalidation for write-heavy data.

Example: A Redis cache convention

```python
# Convention: Cache all GET /users/{id} for 1 hour
def get_user(user_id: int):
    cache_key = f"user:{user_id}:data"
    user = redis.get(cache_key)
    if not user:
        user = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
        redis.setex(cache_key, 3600, user)  # 1-hour TTL
    return user
```

**Key rule**: *Always cache reads, but never cache writes directly.* Use events (e.g., Redis pub/sub) to invalidate caches.

---

### **4. Monitoring: "If It’s Not Measured, It’s Optimised"**
Conventions for observability:
- **Latency SLOs**: Track 99th-percentile response times per endpoint.
- **Query profiling**: Log slow queries (e.g., >500ms) to a centralized system.
- **Alerts**: Enforce alerts for unexpected query patterns.

Example: A `query_monitor` middleware (Python):

```python
# Log slow queries to a database
class QueryMonitor:
    def __init__(self, db):
        self.db = db

    def log_slow_query(self, query, duration_ms):
        if duration_ms > 500:
            self.db.execute(
                "INSERT INTO slow_queries (query, duration_ms) VALUES (?, ?)",
                (query, duration_ms),
            )

# Usage:
monitor = QueryMonitor(db)
def get_user(user_id):
    start_time = time.time()
    user = db.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    monitor.log_slow_query("SELECT ...", (time.time() - start_time) * 1000)
    return user
```

---

## **Implementation Guide: How to Start**

Adopting performance conventions requires **buy-in and tooling**. Here’s a step-by-step approach:

### **1. Define Your Core Conventions**
Start with **1-3 rules** per layer (API, DB, caching) and expand. Example starter pack:

| **Layer**       | **Convention**                          | **Enforcement**               |
|------------------|-----------------------------------------|--------------------------------|
| **API**          | Always use `LIMIT` + `OFFSET`           | Linting (e.g., Pylint)         |
| **DB**           | Avoid `SELECT *`                        | Code reviews + ESLint         |
| **Caching**      | Cache GET endpoints with 1-hour TTL     | Default in framework (e.g., FastAPI) |
| **Monitoring**   | Log queries >500ms                      | Insert into `slow_queries` DB  |

### **2. Enforce with Code**
Use static analysis tools:
- **Python**: `sqlparse` to detect `SELECT *`, `Pylint` for API conventions.
- **JavaScript**: ESLint plugins for SQL injection risks.
- **Database**: Schema migration tools (e.g., Flyway, Alembic) to enforce indexes.

Example: A SQL linter rule (pseudo-code):

```python
# Detect SELECT * in SQL templates
def check_select_all(query: str):
    if "SELECT *" in query.upper():
        raise Warning("Avoid SELECT *; specify columns explicitly.")
```

### **3. Document as "Design Principles"**
Add to your team’s `CONTRIBUTING.md`:
```
## Performance Checklist

For every query:
- [ ] Is it using an index?
- [ ] Does it avoid `SELECT *`?
- [ ] Is it paginated with `LIMIT`/`OFFSET`?
```

### **4. Monitor and Iterate**
Track convention violations via:
- **Code reviews**: Flag SQL queries that violate rules.
- **CI/CD**: Fail builds if slow queries are introduced.
- **Observability**: Dashboards for monitoring convention violations (e.g., "How many `SELECT *` queries ran last week?").

---

## **Common Mistakes to Avoid**

1. **Over-indexing**
   - *Mistake*: Adding indexes to *every* column because "it can’t hurt."
   - *Fix*: Enforce a **cost-benefit rule** (e.g., "Only index columns used in >90% of queries").

2. **Ignoring Write Performance**
   - *Mistake*: Optimising reads but adding indexes that slow writes.
   - *Fix*: Benchmark write vs. read tradeoffs (e.g., `WHERE` clauses vs. `IN` clauses).

3. **Cache Eviction Nightmares**
   - *Mistake*: Using LRU cache with no size limits, causing OOM kills.
   - *Fix*: Set default cache sizes (e.g., Redis maxmemory `2gb`).

4. **Pagination Anti-Patterns**
   - *Mistake*: Using `OFFSET` for deep pagination (e.g., `page=1000`).
   - *Fix*: Enforce `page <= 100` and use `KEYSET pagination` (e.g., `WHERE id > last_id`).

5. **Silent Monitoring Gaps**
   - *Mistake*: Not logging slow queries *before* they become production issues.
   - *Fix*: Instrument all queries in staging, even "simple" ones.

---

## **Key Takeaways**

- **Performance conventions are proactive**, not reactive. They prevent issues before they scale.
- **Start small**: Pick 1-2 rules per layer (e.g., `LIMIT` in APIs, no `SELECT *` in DB).
- **Enforce with tools**: Linting, CI/CD, and observability are your allies.
- **Monitor violations**: Track how often conventions are broken to prioritise fixes.
- **Balance consistency with flexibility**: Conventions should guide, not restrict creativity—allow overrides for justified cases.

---

## **Conclusion**

Performance conventions are the **invisible scaffolding** that keeps your system fast. They’re not about writing "perfect" code once and forgetting it—they’re about **embedding best practices so deeply that they become invisible**.

Try this: Pick **one convention** (e.g., "Never use `SELECT *`") and enforce it for a week. Measure the impact on query times, code reviews, and debugging speed. You’ll likely find that the biggest performance wins come from **what you *don’t* do**—not from heroic last-minute optimisations.

As the saying goes: *"Premature optimisation is the root of all evil… but so is premature *dis-optimisation*."*

Now go enforce those conventions.

---
**Further Reading**:
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Redis Caching Strategies](https://redis.io/topics/caching-strategies)
```