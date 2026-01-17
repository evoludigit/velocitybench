```markdown
# **"Performance Conventions": How Small Decisions Make or Break Your API**

*Designing APIs and databases that scale under load isn’t just about raw optimization—it’s about consistency, predictability, and small conventions that compound over time.*

Imagine your API handles a million requests/day. Now imagine those requests trigger a cascade of database queries, each with its own latency, locking behavior, and caching implications. Without deliberate performance conventions, these decisions become a patchwork of optimizations—some effective, some counterproductive—that no single team member understands. **Performance conventions** are the silent architecture: a set of agreed-upon practices that shape how teams interact with data and APIs, ensuring predictable performance at scale.

In this guide, we’ll explore how small but deliberate design choices—around indexing, query patterns, caching, and concurrency—can transform a system from a fragile monolith into a resilient, high-performance API. We’ll dive into concrete examples, tradeoffs, and anti-patterns to help you implement performance conventions that last.

---

## **The Problem: Performance Without Principles**

Most teams start with good intentions: "We’ll optimize queries later" or "Let’s just add indexes as we find bottlenecks." But without a cohesive set of performance conventions, the system evolves into a "spaghetti architecture" where:

1. **Ad-hoc Optimizations**
   - Query 1 returns fast with a `WHERE` clause on `created_at`.
   - Query 2 (identical data) runs slow because it uses `LIMIT`, `OFFSET`, or a `JOIN` on a non-indexed column.
   - Result: The same data access pattern behaves differently across the API.

2. **Caching Anarchy**
   - Team A caches `User` objects in Redis with a 5-minute TTL.
   - Team B fetches the same users via a different endpoint with no caching.
   - Outcome: Inconsistent performance for identical queries.

3. **Concurrency Overload**
   - A optimistic-locking strategy works for `User` updates but deadlocks on `Order` transactions.
   - Another team adds `FOR UPDATE` locks without coordinating with the database team.
   - Result: Unpredictable latency spikes during peak traffic.

4. **Schema Drift**
   - One microservice adds a `is_active` flag as a column.
   - Another microservice indexes it for `WHERE` clauses.
   - A third team ignores it, leading to full-table scans.
   - Outcome: Schema changes become landmines.

These problems aren’t just about performance—they’re about **technical debt** and **maintainability**. Without conventions, every optimization becomes a local fix, and the system’s total performance degrades over time.

---

## **The Solution: Performance Conventions as a First-Class Design Pattern**

Performance conventions are a set of **universal rules** that govern how teams interact with databases and APIs. They fall into four categories:

1. **Query Design Conventions**
   Ensuring consistent indexing, pagination, and aggregation patterns.
2. **Caching Conventions**
   Standardizing cache keys, TTLs, and invalidate strategies.
3. **Concurrency Control Conventions**
   Defining lock types, retry logic, and transaction boundaries.
4. **Schema Evolution Conventions**
   Rules for adding columns, indexes, and constraints without breaking performance.

The key insight: **Conventions reduce variability.** When all teams follow the same patterns, performance becomes predictable, and bottlenecks become easier to identify and fix.

---

## **Components & Solutions**

### **1. Query Design Conventions**
**Why it matters:** Poorly structured queries can kill performance, even with proper indexing.

#### **Example: Pagination Anti-Pattern**
```sql
-- ❌ Bad: LIMIT + OFFSET is slow for large datasets
SELECT * FROM users ORDER BY created_at LIMIT 10 OFFSET 10000;
```
- **Problem:** `OFFSET` requires scanning all rows before the 10,000th record.
- **Convention:** Use **key-based pagination** (e.g., `last_id` or `cursor`).

```sql
-- ✅ Good: Key-based pagination
SELECT * FROM users
WHERE id > 10000
ORDER BY id
LIMIT 10;
```
**Tradeoff:** Requires storing the last ID in the client.

#### **Example: Selective Fields**
**Convention:** Always specify columns in `SELECT` (never `SELECT *`).

```sql
-- ❌ Bad: Full table scans
SELECT * FROM orders WHERE user_id = 123;

-- ✅ Good: Only fetch needed fields
SELECT order_id, amount, status FROM orders WHERE user_id = 123;
```
**Why?** Reduces network overhead and speeds up query execution.

#### **Example: Indexing Guidelines**
**Convention:** Follow the **"16.9 Characters Rule"** (for MySQL):
- If a column is used in `WHERE`, `JOIN`, or `ORDER BY`, consider indexing it.
- **But:** Avoid over-indexing (each index adds overhead).

```sql
-- ✅ Good: Index for common filters
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- ❌ Bad: Over-indexing (slow writes)
CREATE INDEX idx_orders_everything ON orders(user_id, status, amount, created_at);
```

---

### **2. Caching Conventions**
**Why it matters:** Inconsistent caching leads to wasted compute and stale data.

#### **Example: Cache Key Consistency**
**Convention:** Use a **deterministic key format** for identical queries.

```python
# ❌ Inconsistent cache keys (same query → different keys)
cache_key = f"user_{user_id}"  # Misses if cache expires
cache_key = f"users:{user_id}:profile"  # Different key for same data

# ✅ Good: Standardized key format
def get_cache_key(entity_type, id, suffix=""):
    return f"{entity_type.lower()}:{id}:{suffix}"
```
**Usage:**
```python
cache_key = get_cache_key("user", 123, "profile")
```

#### **Example: TTL Strategies**
**Convention:** Align TTLs with data volatility.

| Data Type       | Recommended TTL | Why?                                  |
|-----------------|-----------------|----------------------------------------|
| User profiles   | 5 minutes       | Low churn, frequent reads             |
| Real-time data  | 30 seconds      | High volatility (e.g., WebSocket feeds)|
| Config settings | 1 hour          | Rarely changes                       |

---

### **3. Concurrency Control Conventions**
**Why it matters:** Race conditions and deadlocks are silent killers.

#### **Example: Lock Granularity**
**Convention:** Use **fine-grained locks** to avoid blocking.

```sql
-- ❌ Bad: Table-level lock (blocks everything)
BEGIN;
SELECT * FROM orders WHERE id = 123 FOR UPDATE; -- Locks entire table
-- (Potentially deadlocks other transactions)
```
```sql
-- ✅ Good: Row-level lock (only locks the specific order)
BEGIN;
SELECT * FROM orders WHERE id = 123 FOR UPDATE; -- Locks only row 123
```

#### **Example: Retry Logic**
**Convention:** Implement **exponential backoff** for retryable errors.

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def retry_on_conflict():
    try:
        update_order_status(order_id)
    except DatabaseLockError as e:
        logger.warning(f"Retrying due to lock: {e}")
        raise
```

---

### **4. Schema Evolution Conventions**
**Why it matters:** Adding columns or indexes too eagerly slows writes.

#### **Example: Backward-Compatible Schema Changes**
**Convention:** Use **nullable columns** and **default values** to avoid breaking changes.

```sql
-- ✅ Good: Add nullable column (no breaking change)
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) NULL DEFAULT NULL;

-- ❌ Bad: Non-nullable column (requires migration)
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) NOT NULL DEFAULT "";
```

#### **Example: Indexing New Columns**
**Convention:** **Index only if needed** (e.g., for `WHERE` clauses).

```sql
-- Only add index if this column is frequently filtered
IF EXISTS (
    SELECT 1 FROM information_schema.statistics
    WHERE table_name = 'orders'
    AND index_name = 'idx_orders_search'
) THEN
    DROP INDEX idx_orders_search ON orders;
END IF;

CREATE INDEX idx_orders_search ON orders(search_term);
```

---

## **Implementation Guide: How to Start**

### **Step 1: Audit Your Current State**
1. **Tools:** Use `EXPLAIN ANALYZE` (PostgreSQL) or `EXPLAIN` (MySQL) to profile slow queries.
2. **Log queries:** Enable query logging to identify inconsistent patterns.
3. **Benchmark:** Test pagination, caching, and concurrency under load.

### **Step 2: Define Conventions (Team Agreement)**
Draft a **Performance Conventions Document** (e.g., in GitHub Wiki) with:
- **Query patterns** (pagination, `SELECT` clauses).
- **Caching rules** (key formats, TTLs).
- **Concurrency policies** (lock types, retries).
- **Schema evolution rules** (column additions, indexes).

### **Step 3: Enforce via Code & Tooling**
- **Code Reviews:** Mandate compliance with conventions (e.g., "No `SELECT *`").
- **Automated Checks:** Use linting (e.g., `sqlfluff`) or CI checks.
- **Database Migrations:** Add migration scripts to enforce indexing.

### **Step 4: Monitor & Iterate**
- **Track performance metrics** (latency, cache hit rate, lock contention).
- **Rotate conventions** as data patterns change (e.g., switch from `LIMIT/OFFSET` to cursor-based pagination).

---

## **Common Mistakes to Avoid**

1. **Over-Optimizing Early**
   - **Mistake:** Adding indexes for every possible query.
   - **Fix:** Measure first, optimize later (YAGNI).

2. **Ignoring Read/Write Tradeoffs**
   - **Mistake:** Indexing everything for reads, ignoring write performance.
   - **Fix:** Use **partial indexes** (e.g., `WHERE is_active = true`).

3. **Inconsistent Caching**
   - **Mistake:** Mixing Redis, Memcached, and local caches.
   - **Fix:** Standardize on **one cache** (e.g., Redis) with consistent TTLs.

4. **Tight Coupling to Schema**
   - **Mistake:** Hardcoding table/column names in application logic.
   - **Fix:** Use **abstraction layers** (e.g., ORM queries, DBAL).

5. **Forgetting About the "Happy Path"**
   - **Mistake:** Optimizing for edge cases while neglecting common workflows.
   - **Fix:** Profile **real-world query patterns** (not synthetic tests).

---

## **Key Takeaways**

✅ **Performance conventions reduce variability**—small, consistent patterns compound into scalable systems.
✅ **Query design matters most**—pagination, `SELECT` clauses, and indexing should be standardized.
✅ **Caching inconsistency kills performance**—agree on key formats, TTLs, and invalidate strategies.
✅ **Concurrency requires discipline**—fine-grained locks and retries prevent deadlocks.
✅ **Schema evolution should be predictable**—nullable columns and backward-compatible changes avoid breaking changes.
✅ **Measure before optimizing**—don’t guess; profile real workloads.

---

## **Conclusion: The Silent Architecture of Scalability**

Performance conventions aren’t just about *fixing* slow queries—they’re about **building systems that stay fast**. By treating performance as a **first-class design concern** (not an afterthought), you create APIs that:
- Scale predictably under load.
- Are easier to maintain as teams grow.
- Avoid the "spaghetti optimization" trap.

Start small: pick **one convention** (e.g., key-based pagination) and enforce it. Over time, your system will become **self-evidently performant**—because the performance is baked into the architecture, not bolted on later.

Now go write **consistent, performant code**—your future self will thank you.
```

---
### **Appendix: Further Reading**
- [Database Performance Tuning](https://use-the-index-luke.com/) (Luke Plant)
- [Caching Strategies](https://blog.sqlauthority.com/2011/09/20/sql-server-caching-strategies/) (SQL Authority)
- [Concurrency Control Patterns](https://craftinginterpreters.com/locking.html) (Crafting Interpreters)

Would you like any section expanded (e.g., deeper dive into retry logic or schema migrations)?