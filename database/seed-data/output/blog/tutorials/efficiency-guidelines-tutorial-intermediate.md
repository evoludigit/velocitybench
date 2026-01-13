```markdown
# **Efficiency Guidelines: How to Build High-Performance APIs Without Guessing**

As backend engineers, we’ve all been there: staring at slow queries, API response times creeping into the hundreds of milliseconds, and users complaining about "lag." You’ve refactored this, tweaked that, and still hit performance walls. What if the answer wasn’t in rewriting your entire system but instead in **systematic efficiency guidelines**?

Efficiency isn’t just about optimizing code—it’s about **making intentional, repeatable decisions** that reduce waste while keeping your system scalable. In this guide, we’ll explore the **"Efficiency Guidelines"** pattern: a structured approach to crafting performant APIs and databases without relying on vague "optimize later" promises. We’ll cover the problems they solve, real-world examples, tradeoffs, and practical patterns you can implement today.

---

## **The Problem: Performance Debt Without Intentionality**

Let’s start with a common scenario:

**Scenario: The E-Commerce Checkout API**
A mid-sized online store sees traffic spike during Black Friday, and their checkout API—built with good intentions but no explicit efficiency rules—suddenly slows to a crawl. After digging, you find:

1. **N+1 Query Problem**:
   ```sql
   -- Slow: Fetching product details in a loop
   SELECT * FROM products WHERE id IN (SELECT product_id FROM cart_items WHERE user_id = 123);
   ```
   No index. No batching. Just 100+ queries for 100 items.

2. **Uncontrolled Caching**:
   The team redid the DB schema for "flexibility," but now `Redux` and `Memcached` are bloated with stale data. The cache invalidation logic? A comment in a 5-year-old PR.

3. **Over-Fetching**:
   A GET `/orders` endpoint returns *everything*—user addresses, shipping details, inventory counts—even though the frontend only needs IDs and timestamps.

4. **Unbounded Data Growth**:
   Logs, audit trails, and "just-in-case" columns in tables like `users` (e.g., `last_seen_at`, `preferred_currency`, `bio`) bloat the database without clear purpose.

---

### **Why This Happens**
1. **"It’s Fast Enough for Now" syndrome**: Developers make quick decisions without documenting them, leading to **technical debt that compounds**.
2. **Lack of standards**: Different devs optimize differently (e.g., one uses `EXPLAIN`; another rewrites the entire schema).
3. **Scale is invisible until it’s not**: Small apps grow without noticing that a `SELECT *` isn’t a big deal until you hit thousands of concurrent users.
4. **Over-eager "pre-optimization"**: Adding indexes, denormalizing, or caching without measuring first wastes effort.

The **Efficiency Guidelines** pattern solves this by:
- Enforcing **rules of thumb** (e.g., "Never fetch more data than needed").
- Providing **templates for common scenarios** (e.g., pagination, caching).
- **Documenting tradeoffs** (e.g., "This query is 10x faster but locks the table for 2 seconds").

---

## **The Solution: Efficiency Guidelines as a Framework**

Efficiency Guidelines are a **set of reusable principles** that apply across your codebase. They should be:
- **Measurable**: Rules like "99% of queries must finish under 100ms" or "95% of responses must be under 500KB."
- **Documented**: Written in a team wiki or codebase (e.g., `/docs/efficiency.md`).
- **Enforceable**: Cached in tests or CI (e.g., "Run `db-checker.sh` before merging").

Here’s how we’ll structure them:

| **Category**          | **Rule**                                  | **Example**                                  |
|-----------------------|-------------------------------------------|---------------------------------------------|
| **Database**          | Avoid `SELECT *`                          | Use explicit columns: `SELECT id, price`    |
| **API Design**        | Enforce pagination                         | `/products?page=1&limit=20`                 |
| **Caching**           | Cache key design                          | `{namespace}:{resource}:{id}:{timestamp}`   |
| **Concurrency**       | Avoid long-running transactions           | Use sagas or event sourcing                 |
| **Data Growth**       | Soft-delete before hard-delete            | Add `is_active` column instead of `DELETE`  |

---
## **Components/Solutions: Practical Patterns**

### **1. Database: The "Fetch Only What You Need" Rule**
**Problem**: Over-fetching is the silent killer of performance. A single `SELECT *` can include 50 columns when you only need 2.

**Solution**: Enforce **explicit column selection** and **use projections** (e.g., GraphQL fragments or SQL views).

#### **Bad**:
```sql
-- Fetches all columns, even unused ones
SELECT * FROM orders WHERE user_id = 123;
```

#### **Good**: Explicit columns + database-level projection
```sql
-- Only fetch what you need
SELECT order_id, amount, status FROM orders WHERE user_id = 123;

-- Or, in GraphQL:
type Order {
  id: ID!
  amount: Float!
  status: String!
  # Exclude these from default query
  shippingDetails: ShippingDetails
}
```
**Tradeoff**: More upfront work to define schemas, but avoids bloating queries.

---

### **2. API Design: Pagination + Offset Limiting**
**Problem**: `/orders` returns 1000 rows → frontend chokes → users complain.

**Solution**: **Pagination + rate limiting**.

#### **Bad**: No pagination
```http
GET /orders
```
**Good**: Paginated + limit
```http
GET /orders?page=1&page_size=20
```
**Implementation (Express.js + Prisma)**:
```javascript
router.get("/orders", async (req, res) => {
  const { page = 1, pageSize = 20 } = req.query;
  const skip = (page - 1) * pageSize;

  const [orders, total] = await Promise.all([
    prisma.order.findMany({
      skip,
      take: parseInt(pageSize),
      orderBy: { createdAt: "desc" },
    }),
    prisma.order.count(),
  ]);

  res.json({
    data: orders,
    pagination: {
      total,
      page: parseInt(page),
      pageSize: parseInt(pageSize),
      totalPages: Math.ceil(total / pageSize),
    },
  });
});
```
**Tradeoff**: Requires frontend pagination logic, but avoids overwhelming users or your database.

---

### **3. Caching: The "Cache Key Design" Rule**
**Problem**: Caching works… until it doesn’t. Keys like `user:123` clash with `user:123:preferences`, leading to misshits.

**Solution**: **Structured cache keys** with namespaces.

#### **Bad Key Design**:
```javascript
// Clashes: `user:123` vs `user:123:address`
cache.set(`user:123`, userData);
```

#### **Good Key Design**:
```javascript
// Explicit namespaces
cache.set(`user:123:profile`, userData);
cache.set(`user:123:addresses`, userAddresses);

// Or, Redis-style hashes
cache.hSet(`user:123:address`, { street: "123 Main", city: "NY" });
```
**Tradeoff**: More verbose keys now, but avoids collisions and stale data.

---

### **4. Concurrency: The "No Long Transactions" Rule**
**Problem**: A 5-second `UPDATE` in a transaction blocks all reads.

**Solution**: **Avoid long-running transactions** or use **sagas** (split transactions into steps).

#### **Bad**: Long transaction
```sql
-- Locks the table for 5 seconds!
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

#### **Good**: Saga pattern (two-phase commit)
```javascript
// Step 1: Reserve first
await prisma.$executeRawUnsafe(
  `UPDATE accounts SET reserved_balance = reserved_balance + 100 WHERE id = 1`
);

// Step 2: If successful, deduct
if (paymentProcessed) {
  await prisma.$executeRawUnsafe(
    `UPDATE accounts SET balance = balance - 100, reserved_balance = reserved_balance - 100 WHERE id = 1`
  );
}
```
**Tradeoff**: More complex, but prevents deadlocks.

---

### **5. Data Growth: "Soft-Delete Before Hard-Delete"**
**Problem**: Deleting 10,000 records at once triggers a 10-minute lock.

**Solution**: **Soft-delete first** (set `is_active: false`) and clean up asynchronously.

#### **Bad**: Hard delete
```sql
DELETE FROM orders WHERE user_id = 123 AND created_at < '2020-01-01';
```

#### **Good**: Soft-delete
```sql
UPDATE orders SET is_active = false WHERE user_id = 123 AND created_at < '2020-01-01';
```
**Implementation (with background job)**:
```javascript
// Run this periodically
async function cleanupOldOrders() {
  const oldOrders = await prisma.order.findMany({
    where: { isActive: false, createdAt: { lt: new Date('2020-01-01') } },
  });

  // Delete in batches to avoid locking
  for (const order of oldOrders) {
    await prisma.order.delete({ where: { id: order.id } });
  }
}
```
**Tradeoff**: More storage in the short term, but avoids blocking.

---

## **Implementation Guide: How to Adopt Efficiency Guidelines**

### **Step 1: Document the Rules**
Create a team wiki or `/docs/efficiency.md` with your guidelines. Example:

```markdown
# Efficiency Guidelines

## Database
- Avoid `SELECT *`. Always specify columns.
- Use indexes for `WHERE`, `JOIN`, and `ORDER BY` clauses.
- Limit `JOIN` depth to 3 levels.

## API
- Enforce pagination: `?page=1&limit=20`.
- Return JSON with `pagination.total` and `pagination.page`.
- Cache API responses with TTL ≤ 5 minutes.

## Caching
- Use Redis keys: `{namespace}:{id}` (e.g., `user:123`).
- Invalidate cache on writes with a job queue.
```

### **Step 2: Enforce in Code Reviews**
Add checks to your CI (e.g., `db-checker.sh`):
```bash
#!/bin/bash
# Checks for SELECT * in PRs
grep -r "SELECT \*" . | grep -v "__tests__" && echo "❌ Found SELECT *! Use explicit columns." && exit 1
```

### **Step 3: Instrument and Monitor**
Track metrics like:
- **Query performance**: Use `pgBadger` (PostgreSQL) or AWS RDS Performance Insights.
- **Cache hit rate**: Monitor `cache.hits` vs `cache.misses` in Redis.
- **API latency**: Set up Prometheus alerts for >100ms responses.

Example (Prometheus metrics):
```go
// Track slow queries
func handleOrderRequest(w http.ResponseWriter, r *http.Request) {
  start := time.Now()
  defer func() {
    duration := time.Since(start)
    if duration > 100*time.Millisecond {
      metrics.APILatencyHist.Observe(duration.Seconds())
    }
  }()
  // ... rest of endpoint
}
```

### **Step 4: Iterate**
Regularly review:
- **Database**: Run `EXPLAIN` on slow queries.
- **API**: Simulate traffic with `locust` or `k6`.
- **Caching**: Check for cache stampedes.

---

## **Common Mistakes to Avoid**

1. **Over-complicating caching**:
   - ❌ "We need a distributed cache with TTL, eviction policies, and hot/cold partitions."
   - ✅ Start with Redis and measure. Optimize later.

2. **Ignoring cold starts**:
   - Warm up your cache (e.g., preload `/products` during deployment).

3. **Not indexing join columns**:
   - ❌ `JOIN users ON orders.user_id = users.id` without an index.
   - ✅ `CREATE INDEX idx_orders_user_id ON orders(user_id);`

4. **Assuming "faster is always better"**:
   - A 1ms query with a 10x CPU hit might not be worth it if a 50ms query is more readable.

5. **Forgetting about edge cases**:
   - Test with **high concurrency** (e.g., `wrk` or `hey`).
   - Test with **malformed data** (e.g., SQL injection).

---

## **Key Takeaways**

- **Efficiency Guidelines are not silver bullets**: They’re a framework to avoid ad-hoc optimizations.
- **Start small**: Pick 2-3 rules (e.g., "no `SELECT *`") and enforce them first.
- **Measure everything**: Use tools like `EXPLAIN`, Prometheus, and load tests.
- **Document tradeoffs**: If you add an index, note why and when it’s worth it.
- **Review continuously**: Efficiency is a never-ending journey, not a one-time task.

---

## **Conclusion: Build for Performance by Design**

Performance isn’t an afterthought—it’s a **feature of good engineering**. By adopting Efficiency Guidelines, you:
- Reduce surprises during scale.
- Make performance decisions **repeatable and predictable**.
- Spend time on what matters: **building features**, not firefighting.

Start with one rule (e.g., "no `SELECT *`") and expand from there. Over time, your APIs will feel **light, responsive, and scalable**—not because you rewrote everything, but because you **designed for efficiency from the start**.

---
**Next Steps**:
1. Pick one rule from this post and enforce it in your next PR.
2. Run `EXPLAIN` on your 5 slowest queries and optimize them.
3. Share your learnings with your team—efficiency is a shared responsibility.

Happy optimizing!
```

---
**P.S.**: Want to dive deeper? Check out:
- [PostgreSQL `EXPLAIN` Guide](https://www.postgresql-guide.com/performance/explain/)
- [Redis Best Practices](https://redis.io/docs/latest/develop/patterns/)
- [K6 for Load Testing](https://k6.io/docs/overview/)