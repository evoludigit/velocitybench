```markdown
# **Throughput Gotchas: How Your System’s Performance Can Betray You**

Every backend engineer knows that **throughput**—the rate at which a system processes requests—is critical to success. High throughput means responsiveness, scalability, and happy users. But here’s the twist: **throughput isn’t just about raw power—it’s about avoiding hidden bottlenecks, underutilized resources, and architectural traps that silently sabotage your system.**

You might think your API is optimized, but unless you account for **concurrency patterns, database locks, network latency spikes, or inefficient query plans**, you’re playing a game of whack-a-mole where performance degrades under real-world load. This post dives into **throughput gotchas**—real-world pitfalls that silently erode your system’s efficiency—and provides battle-tested solutions to keep your system humming.

---

## **The Problem: Why Throughput Gotchas Matter**

Throughput isn’t just about pushing more requests through your system. It’s about **consistently delivering performance under varying loads**—and that’s where gotchas hide.

### **1. The False Sense of Security from Benchmarks**
You might run load tests and see your system handle 10,000 RPS (requests per second). But real-world throughput depends on:
- **Patterned workloads** (e.g., sudden spikes, batch processing at night)
- **Data skew** (few hot keys dominating queries)
- **External dependencies** (API calls, third-party services, or stale caches)

A benchmark that works in isolation often fails when thrown into production traffic.

### **2. The Illusion of Parallelism**
If you design your API to process requests in parallel (e.g., using connection pooling or async I/O), you might assume more threads = better throughput. But:
- **Database locks** can turn parallel queries into serial bottlenecks.
- **Memory pressure** from too many connections can cause GC pauses in JVM-based systems.
- **Network saturation** (TCP backlog) can starve new connections.

### **3. The Cache Misconfiguration**
A well-cached system seems fast—but if your caching layer isn’t tuned for **TTL (Time-To-Live), eviction policies, or hit rates**, you’ll end up with:
- **Cache stampedes** (thousands of requests hitting the database when cache expires).
- **Over-partitioning** (too many small cache entries causing high memory fragmentation).
- **Stale reads** (caching too aggressively with dirty data).

### **4. The Query Plan That Fails Under Load**
A query that works fine in development might **degenerate into a full table scan** when production data grows. Why?
- **Missing indexes** on frequently queried but rarely updated columns.
- **Dynamic SQL** that doesn’t adapt to changing schemas.
- **Join optimizations** that break under high concurrency.

### **5. The Unpredictable External Call**
Every API that calls another service (payment processor, analytics platform, etc.) introduces **latency variability**. If you’re not:
- **Implementing retries with backoff**
- **Circuit-breaking failed dependencies**
- **Throttling external requests**
…you risk **throughput collapse** when downstream services slow down.

---

## **The Solution: Throughput Gotchas & How to Fix Them**

Throughput optimization isn’t just about writing faster code—it’s about **systematic debugging** of real-world bottlenecks. Below are the most common gotchas and how to address them.

---

### **1. Database Lock Contention (The Silent Throttler)**
**Issue:** When multiple transactions compete for the same row or table lock, throughput drops.

**Example:**
```sql
-- This query can block other writes if many users are editing the same row.
UPDATE accounts SET balance = balance - 100
WHERE id = 123 AND version = 1;
```

**Solution:**
- **Use optimistic concurrency control** (version checks) instead of pessimistic locks.
- **Break long-running transactions** (e.g., avoid holding locks during batch processing).
- **Partition hot keys** (e.g., shard accounts by user ID ranges).

**Optimized Query:**
```sql
-- Optimistic locking with retry logic (pseudo-code)
RETRY:
  SELECT balance FROM accounts WHERE id = 123 FOR UPDATE;
  IF (SELECT version FROM accounts WHERE id = 123) == expected_version:
    UPDATE accounts SET balance = balance - 100, version = version + 1
    WHERE id = 123 AND version = expected_version;
  ELSE:
    INCREMENT expected_version AND RETRY;
```

---

### **2. Connection Pool Starvation (The TCP Backlog Nightmare)**
**Issue:** If your app opens too many DB connections (or external HTTP clients), the OS or database hits its connection limit, killing throughput.

**Example:**
```python
# Bad: Unbounded connections (e.g., in a microservice)
def process_order(order_id):
    conn = psycopg2.connect("...")  # No pool!
    with conn.cursor() as cur:
        cur.execute("UPDATE orders SET status = 'processing' WHERE id = %s", (order_id,))
    conn.close()
```

**Solution:**
- **Use connection pooling** (e.g., `pgbouncer`, `HikariCP` for Java).
- **Set reasonable pool sizes** (e.g., `max_pool_size = 50` in PostgreSQL).
- **Reuse connections** instead of closing them per request.

**Optimized Code (HikariCP Example):**
```java
// Java with HikariCP (auto-managed pool)
HikariConfig config = new HikariConfig();
config.setMaximumPoolSize(50);
config.setConnectionTimeout(30000);

HikariDataSource ds = new HikariDataSource(config);

// Reuse connection
try (Connection conn = ds.getConnection()) {
    conn.prepareStatement("UPDATE orders SET status = ? WHERE id = ?")
        .setString(1, "processing")
        .setInt(2, order_id)
        .execute();
}
```

---

### **3. Cache Miss Explosion (The Stampede Problem)**
**Issue:** When cache expires, every request hits the database, causing a **thundering herd phenomenon**.

**Example:**
```python
# Bad: No cache invalidation strategy
@app.get("/product/123")
def get_product():
    data = cache.get("product:123")
    if not data:
        data = db.query("SELECT * FROM products WHERE id = 123").fetchone()
        cache.set("product:123", data, ttl=300)  # Cache for 5 mins
    return data
```

**Solution:**
- **Use probabilistic caching** (e.g., `Cache-Aside` pattern with TTLs).
- **Implement cache invalidation** (e.g., broadcast updates via Pub/Sub).
- **Add a bloom filter** to avoid DB hits for non-existent keys.

**Optimized Code (Redis + Pub/Sub):**
```python
from redis import Redis
import json

redis = Redis(host='localhost', port=6379)

def update_product(product_id, new_data):
    redis.hset(f"product:{product_id}", mapping=new_data)
    redis.publish("product_updates", json.dumps({"id": product_id}))

def get_product(product_id):
    # Check bloom filter first (not shown for brevity)
    data = redis.hgetall(f"product:{product_id}")
    if not data:
        data = db.query(f"SELECT * FROM products WHERE id = {product_id}").fetchone()
        if data:
            redis.hset(f"product:{product_id}", mapping=data)
            redis.expire(f"product:{product_id}", 300)
    return data
```

---

### **4. Slow Queries Under Load (The Query Plan Degradation)**
**Issue:** A query that runs in 10ms in dev might take **1000ms in production** due to missing indexes or poor join strategies.

**Example:**
```sql
-- Bad: Full table scan on a large table
SELECT * FROM users
WHERE created_at > '2023-01-01'
ORDER BY last_login DESC;
```

**Solution:**
- **Profile queries under load** (e.g., `pg_stat_statements` in PostgreSQL).
- **Add indexes** for filtered/sorted columns.
- **Use query hints** or **force execution plans** if needed.

**Optimized Query:**
```sql
-- Add index first
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login);

-- Optimized query
SELECT * FROM users
WHERE created_at > '2023-01-01'
ORDER BY last_login DESC
LIMIT 100;
```

**Debugging Tool:**
```sql
-- Check actual query plan in PostgreSQL
EXPLAIN ANALYZE
SELECT * FROM users
WHERE created_at > '2023-01-01'
ORDER BY last_login DESC;
```

---

### **5. External API Throttling (The Dependency Bottleneck)**
**Issue:** If your app depends on a slow third-party API (e.g., Stripe, Twilio), you risk **starving your own users**.

**Example:**
```python
# Bad: Uncontrolled external calls
def charge_customer(card_id, amount):
    stripe_response = requests.post(
        "https://api.stripe.com/v1/charges",
        json={"amount": amount, "source": card_id}
    )
    # No retries, no rate limiting
```

**Solution:**
- **Implement retry logic with exponential backoff.**
- **Throttle requests** (e.g., `asyncio.Semaphore`).
- **Cache responses** where possible.

**Optimized Code (Python with `tenacity`):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def charge_customer(card_id, amount):
    semaphore.acquire()  # Limits concurrent calls
    try:
        response = requests.post(
            "https://api.stripe.com/v1/charges",
            json={"amount": amount, "source": card_id},
            headers={"Authorization": "Bearer YOUR_KEY"}
        )
        return response.json()
    finally:
        semaphore.release()
```

---

## **Implementation Guide: How to Hunt Throughput Gotchas**

### **Step 1: Instrument Your System**
- **Database:** Enable slow query logging (`pgbadger`, `percona pm`).
- **API:** Log request timestamps, cache hits/misses, and error rates.
- **Monitoring:** Use tools like **Prometheus + Grafana** to track latency percentiles.

### **Step 2: Load Test Realistically**
- **Simulate production traffic** (e.g., with `k6`, `Locust`, or `JMeter`).
- **Test edge cases:**
  - Sudden spikes (e.g., 10x traffic in 5 minutes).
  - Data skew (e.g., 90% requests for 10% of keys).
  - Network partitions (simulate slow external APIs).

### **Step 3: Profile Under Load**
- **Database:** Check for long-running transactions (`pg_stat_activity`).
- **Application:** Use CPU profiling (`pprof` in Go, `async-profiler` in Java).
- **Network:** Monitor TCP backlog (`netstat`, `sar`).

### **Step 4: Optimize Incrementally**
- **Fix the worst offenders first** (e.g., slowest queries, highest latency APIs).
- **Avoid premature optimization**—profile before optimizing.

---

## **Common Mistakes to Avoid**

❌ **Ignoring tail latencies** – Optimizing for 99th percentile while ignoring the 99.9th.
❌ **Over-indexing** – Too many indexes slow down writes and bloat storage.
❌ **No circuit breakers** – Letting one failing API call cascade failures.
❌ **Static connection pools** – Not adjusting pool sizes based on load.
❌ **Assuming "faster code" = better throughput** – Sometimes, better algorithms (e.g., batching) help more.

---

## **Key Takeaways**

✅ **Throughput isn’t just about speed—it’s about consistency.**
✅ **Database locks, cache misses, and external APIs can silently kill performance.**
✅ **Always test under realistic load, not just benchmarking.**
✅ **Optimize incrementally: fix the worst bottlenecks first.**
✅ **Monitor everything: queries, cache hits, external API calls.**

---

## **Conclusion: Throughput Gotchas Are Everywhere—Be Prepared**

Throughput isn’t a one-time fix—it’s an ongoing battle against **unpredictable workloads, hidden bottlenecks, and external dependencies**. The systems that scale under real-world load are the ones where engineers:
1. **Instrument properly** (metrics, traces, logs).
2. **Load test realistically** (not just in isolation).
3. **Optimize systematically** (profile → fix → repeat).

Next time you ship a new feature, ask:
- *Does this add to throughput, or introduce a new gotcha?*
- *How will this behave under 10x load?*

Because in the end, **a system that works in dev but fails in production isn’t just slow—it’s broken.**

---
**Happy optimizing!** 🚀
```

---
**Why this works:**
- **Code-first approach** – Every concept has a concrete example.
- **Honest tradeoffs** – Covers both pros and cons (e.g., indexing tradeoffs).
- **Actionable** – Step-by-step guide + common pitfalls.
- **Engaging** – Balances technical depth with readability.