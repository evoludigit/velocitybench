```markdown
# **Throughput Best Practices: Designing APIs & Databases for Scalable Performance**

*How to build systems that handle 10x traffic without breaking a sweat*

---

## **Introduction**

Imagine your application is a busy café:
- On a quiet Monday, you serve coffee to 5 customers per hour.
- By Friday rush hour, you’re serving **100+ customers per minute**.

If you only designed the café for 5 customers/hour, you’ll quickly run out of counter space, coffee machines, and baristas—your system will **crash under load**.

Now, scale that up. Your web API or database is like that café. Without proper **throughput optimization**, your system will:
- Slow down under traffic spikes
- Consume unnecessary resources
- Fail catastrophically when demand increases

But here’s the good news: throughput optimizations are **practical, testable, and often low-cost**. In this guide, you’ll learn **proven patterns** to design APIs and databases that scale gracefully—without rewriting everything from scratch.

This isn’t just theory. We’ll cover:
✅ **Real-world examples** (e.g., handling payment spikes, API analytics)
✅ **Code snippets** for common tools (PostgreSQL, Redis, Node.js, Python)
✅ **Tradeoffs** (e.g., caching vs. database impact)
✅ **Mistakes** that even senior devs make

By the end, you’ll know how to **prevent bottlenecks** before they hurt your users.

---

## **The Problem: Why Throughput Matters (And Why You’re Losing Money)**

Throughput is the **rate at which your system processes requests**. Poor throughput means:
- Slow APIs → users abandon your site (Google found a **1s delay = 20% fewer users**).
- Expensive bills → databases spinning up more servers than needed.
- Unpredictable failures → customers see errors during "prime time."

### **Common Symptoms of Low Throughput**
1. **Database queries become slow** (e.g., `COUNT(*)` on a large table).
   ```sql
   SELECT COUNT(*) FROM orders; -- Slows down with 1M+ rows
   ```
2. **APIs time out under load** (e.g., 500+ concurrent users).
   ```javascript
   // A naive loop that blocks the event loop
   for (let i = 0; i < 1000; i++) {
     await fetchDataFromDB(); // Freezes the whole API!
   }
   ```
3. **Caching layer is overwhelmed** (e.g., Redis memory exhaustion).
   ```python
   # Bad: No TTL or eviction policy
   cache.set("user:123", user_data, timeout=0)  # Never expires!
   ```
4. **Lock contention** (e.g., too many `SELECT FOR UPDATE` in a high-traffic app).
   ```sql
   -- Blocking other transactions
   SELECT * FROM inventory WHERE product_id = 1 FOR UPDATE;
   ```

### **Real-World Example: The "Black Friday" Nightmare**
A mid-sized e-commerce company saw a **10x traffic spike** on Black Friday. Their backend:
- Used raw SQL joins without indexing.
- Lacked rate limiting.
- Had no database read replicas.

**Result?** The system **collapsed** after 1 hour. Users saw 502 errors, and revenue dropped by **$50k**.

**The fix?** They added:
✔ Indexes (`CREATE INDEX idx_customer_order ON orders(customer_id)`)
✔ API throttling (e.g., 100 requests/minute per user)
✔ Read replicas

**Revenue recovery?** **$100k in 3 days** after optimizations.

---

## **The Solution: Throughput Best Practices**

Throughput optimization comes down to **three pillars**:
1. **Efficient Data Access** (SQL, caching, denormalization)
2. **Parallelism & Async Processing** (event queues, sharding)
3. **Resource Management** (connection pooling, batching)

Let’s dive into each with **practical examples**.

---

## **1. Efficient Data Access: Write Queries That Scale**

### **Problem: N+1 Query Problem**
Imagine fetching a list of **100 users** from an API, then querying each user’s orders:
```javascript
// Bad: 101 queries (1 for users + 100 for orders)
const users = await db.query("SELECT * FROM users");
for (const user of users) {
  const orders = await db.query(`SELECT * FROM orders WHERE user_id = ${user.id}`);
  // ...
}
```
**Result:** 100 slow queries → **slow API response**.

### **Solution: Batch or Denormalize**
#### **Option A: Batch Fetching (SQL)**
```sql
-- Fetch users AND their orders in ONE query
SELECT u.*, o.*
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.active = true;
```
#### **Option B: Caching (Redis)**
```javascript
// Cache orders per user (expires in 5 mins)
const orderCacheKey = `user:${userId}:orders`;
const cachedOrders = await redis.get(orderCacheKey);

if (!cachedOrders) {
  const orders = await db.query(`SELECT * FROM orders WHERE user_id = ?`, [userId]);
  await redis.setex(orderCacheKey, 300, JSON.stringify(orders)); // 5 min TTL
}
```
#### **Option C: Denormalization (NoSQL Example)**
```javascript
// Store orders directly in the user doc (MongoDB)
db.users.findOne(
  { id: userId },
  { orders: 1 }  // Only fetch orders
);
```

### **Key Tradeoffs**
| Approach       | Pros                          | Cons                          |
|----------------|-------------------------------|-------------------------------|
| **Batching**   | Fast, no cache needed         | Harder to update              |
| **Caching**    | Flexible, reduces DB load     | Cache invalidation overhead   |
| **Denormalize**| Single query                  | Data duplication              |

**Best for most APIs:** **Batching + caching** (Option A + B).

---

## **2. Parallelism: Let Your System Work in the Background**

### **Problem: Blocking APIs**
If your API waits for slow operations (e.g., sending emails, processing payments), **users see delays**:
```javascript
// Bad: Blocks the HTTP response
const result = await processPayment(userId); // Takes 2s
return sendResponse(result); // User waits 2s!
```

### **Solution: Async Processing with Queues**
Use a **message queue** (e.g., RabbitMQ, AWS SQS, Celery) to offload work:
```/javascript
// Step 1: Queue the task
await queue.push('process_payment', { userId, amount });

// Step 2: API responds immediately
return sendResponse({ success: true });
```
**Example with Bull (Node.js):**
```javascript
const queue = new Queue(1, processPayment);

app.post('/checkout', async (req, res) => {
  await queue.add({ userId: req.body.userId, amount: req.body.amount });
  res.json({ success: true });
});
```
**Worker process (handles queue):**
```javascript
queue.process(async (job) => {
  await processPayment(job.data.userId, job.data.amount);
});
```
**Benefits:**
✅ Users get **instant responses**.
✅ Heavy work runs in the background.
✅ **Scalable** (add more workers = faster processing).

---

## **3. Resource Management: Don’t Let Databases Drown**

### **Problem: Database Connections & Memory**
- **Connection leaks:** Too many open DB connections → `Too many connections` error.
- **Memory bloat:** Caching everything → `OOM (Out of Memory)`.

### **Solution: Pooling & Eviction Policies**
#### **A. Connection Pooling (PostgreSQL)**
```sql
-- Use a pool (e.g., `pg` in Node.js)
const pool = new Pool({
  user: 'db_user',
  host: 'localhost',
  pool: {
    max: 20,  // Limit to 20 connections
    idleTimeoutMillis: 30000
  }
});
```
#### **B. Cache Eviction (Redis)**
```javascript
// Use LRU (Least Recently Used) eviction
await redis.configSet('maxmemory-policy', 'allkeys-lru');
await redis.configSet('maxmemory', '1gb');
```
#### **C. Batch Writes (Reduce DB Load)**
```javascript
// Bad: 1000 separate INSERTs
for (let i = 0; i < 1000; i++) {
  await db.insert({ data: `item-${i}` });
}

// Good: Batch INSERT
await db.query(`
  INSERT INTO items (data)
  VALUES ${items.map(() => '(?,?)').join(', ')}
`, items.flatMap(item => [item.id, item.data])
);
```

---

## **Implementation Guide: Step-by-Step Checklist**

| Step               | Action Items                          | Tools/Libraries                     |
|--------------------|---------------------------------------|-------------------------------------|
| **1. Audit Queries** | Find slow SQL (`EXPLAIN ANALYZE`)    | `pgBadger`, `SlowQueryLog`          |
| **2. Add Indexes** | Index frequently filtered columns     | `CREATE INDEX idx_user_email ON users(email)` |
| **3. Implement Caching** | Cache expensive reads (Redis, CDN) | `redis`, `@fastify/cache`           |
| **4. Offload Work** | Use queues for async tasks            | `Bull`, `RabbitMQ`, `Celery`        |
| **5. Limit Connections** | Set DB pool sizes & TTLs           | `pgPool`, `mysql2`                  |
| **6. Monitor** | Track throughput (APM tools)        | `New Relic`, `Datadog`, `Prometheus`|

---

## **Common Mistakes to Avoid**

🚨 **Mistake 1: Caching Everything**
- **Problem:** Cache becomes a bottleneck (e.g., `GET /api/data` misses cache 100%).
- **Fix:** Only cache **expensive** or **frequently accessed** data.

🚨 **Mistake 2: Ignoring Database Reads & Writes**
- **Problem:** `SELECT *` on a big table.
- **Fix:** Use **projections** (`SELECT id, name FROM users`) and **indexes**.

🚨 **Mistake 3: No Async Processing**
- **Problem:** Users wait for slow operations (e.g., PDF generation).
- **Fix:** Queue them (`processPaymentJob`).

🚨 **Mistake 4: Over-Sharding Without Planning**
- **Problem:** Too many database shards → management overhead.
- **Fix:** Start with **read replicas**, then shard if needed.

🚨 **Mistake 5: No Load Testing**
- **Problem:** System works fine in dev, but crashes in production.
- **Fix:** Simulate traffic with `k6` or `Locust`.

---

## **Key Takeaways (Cheat Sheet)**

✅ **Optimize Queries First**
- Use `EXPLAIN ANALYZE` to find slow SQL.
- Add indexes (`CREATE INDEX`) on filtered columns.

✅ **Cache Strategically**
- Cache **expensive reads** (e.g., `GET /products?category=electronics`).
- Set **TTLs** (e.g., 5–30 minutes) to avoid stale data.

✅ **Offload Work**
- Use **queues** (RabbitMQ, Bull) for async tasks.
- Let users see "processing" instead of waiting.

✅ **Manage Resources**
- **Limit DB connections** (`max: 20` in pool config).
- **Batch writes** (reduce DB load).

✅ **Test Under Load**
- Simulate traffic with `k6` or `Locust`.
- Monitor **throughput** (reqs/sec) and **latency**.

❌ **Don’t:**
- Ignore slow queries.
- Cache everything.
- Block the event loop with sync code.

---

## **Conclusion: Scale Smarter, Not Harder**

Throughput optimization isn’t about **magic solutions**—it’s about **small, measurable improvements**:
1. **Fix slow queries** (indexes, batching).
2. **Cache intelligently** (only what’s expensive).
3. **Offload work** (queues, background jobs).
4. **Monitor & iterate** (load test, monitor).

**Start small:**
- Add indexes to your top 5 slowest queries.
- Cache one high-traffic API endpoint.
- Queue one async task.

**Measure impact:**
- Compare before/after latency.
- Check database load (`pg_stat_activity`).

**Repeat.**

Your users (and your bank account) will thank you.

---

### **Further Reading**
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [Redis Best Practices](https://redis.io/docs/management/guidelines/)
- [Load Testing with k6](https://k6.io/docs/)

**Got questions?** Hit reply—I’d love to discuss your specific setup!

---
```