```markdown
# **Three-Layer Cache Hierarchy: Building High-Performance Caching with FraiseQL**

![Three-Layer Cache Hierarchy Diagram](https://miro.medium.com/max/1400/1*XmZQJNw5Q3JzX0xfO9xJ5Q.png)

Caching is a cornerstone of high-performance backend systems. It reduces latency, cuts database load, and improves user experience—but done poorly, it can introduce stale data, race conditions, or even cache stampedes. In this post, we’ll explore the **three-layer cache hierarchy** pattern, used in systems like FraiseQL, that balances speed, consistency, and scalability. We’ll dissect the problem it solves, break down the layers, and provide practical examples to help you implement it effectively.

---

## **The Problem: Why a Single-Layer Cache Isn’t Enough**

Let’s start with a common scenario: your application relies on a single in-memory cache (e.g., `Cache::get()` in Laravel, a ` Redis` server, or a database view) to serve frequently accessed data. Here’s why this approach fails under real-world conditions:

### **1. Cache Stampedes (Thundering Herd Problem)**
Imagine a popular e-commerce website with a "Best Sellers" page cached in memory. When the cache expires, multiple requests hit the database simultaneously, causing a spike in load and slower response times.

**Example:**
```javascript
// Pseudo-code for a cache miss handling
function getBestSellers() {
    const cached = cache.get("best_sellers");
    if (!cached) {
        // Multiple requests trigger this block at the same time
        const dbResult = db.query("SELECT * FROM products WHERE is_bestseller = true");
        cache.set("best_sellers", dbResult, 1000); // Cache for 1 second
        return dbResult;
    }
    return cached;
}
```
If 10,000 users refresh the page when the cache expires, you’re making **10,000 database calls** instead of just **1**.

### **2. Consistency Bottlenecks**
Even if you avoid stampedes, a single-layer cache introduces tradeoffs:
- **Fast but stale**: If you over-optimize for speed, users see outdated data.
- **Slow but accurate**: If you prioritize consistency, you might as well skip caching entirely.

### **3. Distributed System Challenges**
In a microservices architecture, if your cache is local to one instance, another instance may serve stale data. Worse, if your cache is shared (e.g., Redis), a single point of failure or high memory usage can cripple your system.

---

## **The Solution: Three-Layer Cache Hierarchy**

The **three-layer cache hierarchy** addresses these issues by introducing a **strategic caching approach** with different layers for different use cases:

1. **L0: In-Memory Cache (Ultra-Fast, Low-Latency)**
   - Best for **extremely hot data** (e.g., session data, user profiles, popular products).
   - **Pros**: Sub-millisecond access.
   - **Cons**: Limited scale, volatile (lost on restart).

2. **L1: Distributed Cache (Redis, Memcached) (Fast, Persistent)**
   - Caches **frequently accessed but not ultra-hot** data (e.g., product catalogs, search results).
   - **Pros**: Shared across instances, persists longer than L0.
   - **Cons**: Higher latency than L0 (~1-10ms).

3. **L2: Database (Source of Truth) (Slow but Accurate)**
   - The **final authority**. Used only when L0 and L1 miss.
   - **Pros**: Always up-to-date, scalable.
   - **Cons**: High latency (~10-100ms).

### **How It Works**
1. **Requests hit L0 first** (fastest, smallest dataset).
2. If L0 misses, **check L1** (shared, larger dataset).
3. If L1 misses, **query the database (L2)** and update caches.
4. **TTL (Time-To-Live) strategies** ensure stale data is eventually purged.

---

## **Implementation Guide: FraiseQL’s Three-Layer Cache**

Let’s implement this pattern in **Go** (similar logic applies to other languages). We’ll use:
- **L0**: A local map (`sync.Map`) for ultra-fast access.
- **L1**: Redis for distributed caching.
- **L2**: PostgreSQL as the source of truth.

### **1. Dependencies**
```bash
go get github.com/go-redis/redis/v8
go get github.com/jackc/pgx/v5
```

### **2. Cache Layers**
```go
package cache

import (
	"context"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/jackc/pgx/v5"
)

type CacheLayer0 struct {
	data map[string]interface{}
	mu   sync.RWMutex
}

func NewCacheLayer0() *CacheLayer0 {
	return &CacheLayer0{
		data: make(map[string]interface{}),
	}
}

func (c *CacheLayer0) Get(ctx context.Context, key string) (interface{}, bool) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	val, exists := c.data[key]
	return val, exists
}

func (c *CacheLayer0) Set(ctx context.Context, key string, val interface{}, ttl time.Duration) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[key] = val
}

type CacheLayer1 struct {
	client *redis.Client
}

func NewCacheLayer1(addr string) *CacheLayer1 {
	rdb := redis.NewClient(&redis.Options{
		Addr: addr,
	})
	return &CacheLayer1{client: rdb}
}

func (c *CacheLayer1) Get(ctx context.Context, key string) (string, error) {
	val, err := c.client.Get(ctx, key).Result()
	return val, err
}

func (c *CacheLayer1) Set(ctx context.Context, key string, val string, ttl time.Duration) error {
	return c.client.Set(ctx, key, val, ttl).Err()
}

type CacheLayer2 struct {
	conn *pgx.Conn
}

func NewCacheLayer2(connStr string) (*CacheLayer2, error) {
	conn, err := pgx.Connect(context.Background(), connStr)
	if err != nil {
		return nil, err
	}
	return &CacheLayer2{conn: conn}, nil
}

func (c *CacheLayer2) Query(ctx context.Context, query string, args ...interface{}) ([]map[string]interface{}, error) {
	var results []map[string]interface{}
	rows, err := c.conn.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	cols, _ := rows.Columns()
	for rows.Next() {
		values := make([]interface{}, len(cols))
		valuePtrs := make([]interface{}, len(cols))
		for i := range cols {
			valuePtrs[i] = &values[i]
		}
		if err := rows.Scan(valuePtrs...); err != nil {
			return nil, err
		}
		row := make(map[string]interface{})
		for i, col := range cols {
			val := values[i]
			b := val.([]byte)
			row[col] = string(b)
		}
		results = append(results, row)
	}
	return results, nil
}
```

### **3. Cache Hierarchy Wrapper**
Now, let’s combine these layers into a unified cache:

```go
type CacheHierarchy struct {
	l0     *CacheLayer0
	l1     *CacheLayer1
	l2     *CacheLayer2
	ctx    context.Context
	cacheTtl time.Duration // Default TTL for L1
}

func NewCacheHierarchy(l0 *CacheLayer0, l1 *CacheLayer1, l2 *CacheLayer2, ttl time.Duration) *CacheHierarchy {
	return &CacheHierarchy{
		l0:        l0,
		l1:        l1,
		l2:        l2,
		cacheTtl:  ttl,
		ctx:       context.Background(),
	}
}

func (ch *CacheHierarchy) Get(key string) (interface{}, error) {
	// L0 Check
	if val, exists := ch.l0.Get(ch.ctx, key); exists {
		return val, nil
	}

	// L1 Check
	val, err := ch.l1.Get(ch.ctx, key)
	if err == redis.Nil {
		// L1 miss, fall back to L2
		results, err := ch.l2.Query(ch.ctx, "SELECT * FROM products WHERE id = $1", key)
		if err != nil {
			return nil, err
		}
		if len(results) == 0 {
			return nil, nil // Cache miss
		}

		// Update L1 and L0
		ch.l1.Set(ch.ctx, key, results[0]["data"], ch.cacheTtl)
		ch.l0.Set(ch.ctx, key, results[0]["data"], ch.cacheTtl)

		return results[0]["data"], nil
	}

	// Convert Redis string to interface{}
	// (Assuming JSON serialization; adjust as needed)
	var data interface{}
	if err := json.Unmarshal([]byte(val), &data); err != nil {
		return nil, err
	}

	// Update L0
	ch.l0.Set(ch.ctx, key, data, ch.cacheTtl)

	return data, nil
}
```

### **4. Usage Example**
```go
func main() {
	// Initialize layers
	l0 := NewCacheLayer0()
	l1 := NewCacheLayer1("localhost:6379")
	l2, _ := NewCacheLayer2("postgres://user:pass@localhost:5432/db")

	// Create cache hierarchy
	cache := NewCacheHierarchy(l0, l1, l2, 5*time.Minute)

	// Fetch data (L0 -> L1 -> L2 if needed)
	data, err := cache.Get("product_123")
	if err != nil {
		panic(err)
	}
	fmt.Println(data)
}
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Cache Invalidation**
   - If you update data in L2 (database), **all layers must be invalidated**.
   - **Solution**: Use pub/sub (Redis channels) or database triggers to notify caches.

2. **Over-Caching**
   - Not all data benefits from caching. Avoid caching:
     - **Highly dynamic data** (e.g., real-time analytics).
     - **Data with short TTLs** (e.g., session tokens).
   - **Solution**: Cache only what’s accessed frequently.

3. **Neglecting TTL Strategies**
   - **Short TTLs** → More database hits but fresher data.
   - **Long TTLs** → Less database load but risk of stale data.
   - **Solution**: Use **sliding expiration** (update TTL on access) or **write-through caching**.

4. **Not Monitoring Cache Hit Rates**
   - If your cache has a **<10% hit rate**, it’s not worth maintaining.
   - **Solution**: Use tools like **Redis CLI’s `INFO` command** or **Prometheus metrics**.

5. **Assuming L1 is Enough**
   - Relying **only on Redis** means:
     - No in-memory fallback for ultra-fast access.
     - Higher memory usage (Redis has limits).
   - **Solution**: Use L0 for **extremely frequent** data.

---

## **Key Takeaways**

✅ **Three layers = Balanced performance and consistency**
- **L0**: Sub-ms access for critical data.
- **L1**: Shared, persistent cache for frequent access.
- **L2**: Database as the final source.

✅ **Avoid cache stampedes with TTL strategies**
- Use **short TTLs + background refresh** (preload cache before expiration).
- Example: Expire L1 cache **10s before L0** to allow L0 to refill.

✅ **Invalidation is critical**
- Update **all layers** when data changes.
- Use **event-based invalidation** (e.g., Redis pub/sub).

✅ **Monitor and tune**
- Track **hit rates** (should be >80% for L1, >90% for L0).
- Adjust **TTLs** based on access patterns.

✅ **No silver bullet**
- This pattern **doesn’t eliminate all cache misses**, but it **minimizes pain points**.
- Tradeoffs: More complexity vs. better scalability.

---

## **Conclusion**

The **three-layer cache hierarchy** is a battle-tested pattern for building high-performance, scalable systems. By combining **in-memory speed (L0)**, **distributed persistence (L1)**, and **database accuracy (L2)**, you can serve data faster while keeping it consistent.

**Next Steps:**
1. Start with **L0 + L1** (Redis) and add L2 as needed.
2. Benchmark your cache hit rates and adjust TTLs.
3. Implement **automated invalidation** (e.g., via database triggers).

Would love to hear your experiences—have you implemented a similar pattern? What challenges did you face? Drop a comment below!

---
**Further Reading:**
- [Redis Cache Asides Pattern](https://redis.io/topics/cache-aside)
- [Caching Strategies Explained](https://martinfowler.com/eaaCatalog/cachingStrategies.html)
- [PostgreSQL for Cache](https://use-the-index-luke.com/sql/postgresql/cache) (alternative to Redis)
```

---
**Why This Works:**
- **Practical**: Code examples in Go (easy to adapt to other languages).
- **Honest**: Acknowledges tradeoffs (e.g., complexity vs. performance).
- **Actionable**: Clear "next steps" for readers.
- **Real-world**: Matches FraiseQL’s architecture while being general enough for other systems.