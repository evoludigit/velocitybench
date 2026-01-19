# **[Pattern] Three-Layer Cache Hierarchy – Reference Guide**

---

## **Overview**
The **Three-Layer Cache Hierarchy** pattern in FraiseQL layers caching mechanisms to balance speed, scalability, and consistency. This approach uses **three distinct storage tiers**:

1. **In-Memory Cache** – Ultra-low-latency cache for hot data, ideal for millisecond read responses.
2. **Distributed Cache (Redis)** – Persistent, high-performance caching layer for commonly accessed but non-critical data.
3. **Database** – The authoritative source of truth, with eventual consistency updates propagat-ed via invalidation triggers.

The hierarchy ensures that **frequently accessed queries** bypass slow database operations, while **stale but tolerable data** is served from Redis, and the **source-of-truth** remains the database.

This pattern is particularly effective in read-heavy workloads where consistency can tolerate slight latency, but critical operations must always reflect the latest state.

---

## **Schema Reference**

| **Layer**          | **Technology** | **Use Case**                     | **TTL (Default)** | **Invalidation Mechanism**                     | **Consistency Model**          | **Failure Handling**                     |
|--------------------|----------------|----------------------------------|-------------------|-----------------------------------------------|--------------------------------|-------------------------------------------|
| **In-Memory**      | Local JVM Cache | Ultra-fast reads (e.g., session data, computed views) | 10–60 sec        | Manual (`Cache.EVICT`) or time-based expiration | Strong (immediate updates)      | Cache miss → fall through to Redis         |
| **Distributed**    | Redis (Cluster)| High-traffic hot keys (e.g., product listings, top N queries) | 1–24 hrs         | Pub/Sub invalidation or manual (`REDIS_DEL`) | Eventual (TTL-driven refresh) | Fallback to database if Redis unavailable |
| **Database**       | PostgreSQL     | Source of truth (always authoritative) | N/A               | Write-through triggers (e.g., `AFTER INSERT`) | Strong (immediate consistency) | Primary DB failover → replication lag |

---

## **Key Components**
### **1. In-Memory Cache (`fraise.local.cache`)**
- **Type:** Off-heap LRU cache (Java `Cache` API)
- **Scope:** Per-FraiseQL worker process
- **TTL:** Short-lived (configurable per key)
- **Usage:**
  ```java
  Cache<String, User> inMemoryCache = Caches.newGuavaCache(/*builder*/);
  User user = inMemoryCache.getIfPresent("user_123");
  ```
- **When to Use:**
  - Cache computed results (e.g., aggregations).
  - Store ephemeral data (e.g., request-scoped tokens).

### **2. Distributed Cache (`fraise.redis`)**
- **Type:** Redis Cluster (via Lettuce client)
- **Scope:** Shared across all FraiseQL workers
- **TTL:** Adjustable (default: 1 hour for hot keys)
- **Integration:**
  ```sql
  -- Query with Redis fallback
  SELECT * FROM products WHERE category = 'electronics'
    CACHE IN_MEMORY TTL 60s
    FALLBACK TO REDIS TTL 3600s;
  ```
- **Invalidation:**
  - **Manual:** `REDIS_DEL key` after DB write.
  - **Event-Driven:** Redis Pub/Sub triggers invalidation on `AFTER INSERT/UPDATE`.

### **3. Database Layer (PostgreSQL)**
- **Role:** Final source of truth
- **Triggers:** Automatically invalidate caches on writes:
  ```sql
  CREATE TRIGGER invalidate_product_cache
  AFTER UPDATE ON products
  FOR EACH ROW EXECUTE FUNCTION update_redis_cache();
  ```
- **Query Patterns:**
  - Use `CACHE` hints to enforce hierarchical lookup:
    ```sql
    SELECT * FROM orders
      CACHE IN_MEMORY TTL 30s  -- First try in-memory
      FALLBACK TO REDIS TTL 1h -- Then Redis
      FALLBACK TO DB;          -- Finally, DB
    ```

---

## **Query Examples**

### **1. Basic Caching with Fallback**
```sql
-- Cache in-memory for 30s, then Redis for 1h, DB last
SELECT name, price FROM products WHERE id = 42
  CACHE IN_MEMORY TTL 30s
  FALLBACK TO REDIS TTL 3600s;
```

### **2. Time-Series Aggregation with Cache**
```sql
-- Cache aggregations in-memory (TTL: 1 minute)
SELECT SUM(revenue) FROM sales
  WHERE YEAR(date) = 2023
  CACHE IN_MEMORY TTL 60s;
```

### **3. Forge Ignore for No-Caching**
```sql
-- Skip cache entirely (e.g., for sensitive data)
SELECT * FROM user_profiles WHERE id = 123
  NO_CACHE;
```

### **4. Conditional Cache Invalidation**
```sql
-- Invalidate Redis cache if DB row is updated
SELECT * FROM inventory WHERE product_id = 101
  CACHE REDIS TTL 3600s
  INVALIDATE REDIS_ON_UPDATE;
```

---

## **TTL Strategies**
| **Scenario**               | **In-Memory TTL** | **Redis TTL** | **Database Fallback** |
|----------------------------|-------------------|---------------|-----------------------|
| Hot product listings       | 10s               | 1 hour        | No                   |
| User sessions               | 5 min             | N/A           | Yes (refresh token)   |
| Real-time analytics        | 30 sec            | N/A           | Yes                   |
| Static configuration       | 24 hrs            | 7 days        | No                    |

**Best Practices:**
- **In-Memory:** Use short TTLs (≤1 min) for volatility.
- **Redis:** Longer TTLs (1–24 hrs) for shared data.
- **Database:** Always the last resort; avoid caching critical writes.

---

## **Invalidation Patterns**
### **1. Manual Invalidation**
```java
// Explicitly clear in-memory cache
fraise.local.cache.invalidate("user_456");

// Delete from Redis
fraise.redis.del("product_789");
```

### **2. Automatic Invalidation (Triggers)**
```sql
-- PostgreSQL trigger to clear Redis on write
CREATE OR REPLACE FUNCTION update_product_cache()
RETURNS TRIGGER AS $$
BEGIN
  EXECUTE 'REDIS_DEL "product_' || NEW.id || '"';
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER refresh_product_cache
AFTER UPDATE ON products
FOR EACH ROW EXECUTE FUNCTION update_product_cache();
```

### **3. Event-Driven (Pub/Sub)**
```java
// Subscribe to Redis Pub/Sub channel
fraise.redis.subscribe("product_updates", (message) -> {
    fraise.local.cache.invalidate(message.getPayload());
});
```

---

## **Performance Considerations**
| **Metric**               | **In-Memory** | **Redis**               | **Database**          |
|--------------------------|---------------|-------------------------|-----------------------|
| Avg. Read Latency        | <1 ms         | ~5–50 ms                | ~10–100 ms            |
| Write Latency            | N/A           | ~1–10 ms                | ~5–50 ms              |
| Memory Footprint         | Low           | Moderate (GBs)          | High (TB-scale)       |
| Scalability              | Single-node   | Cluster (multi-node)    | Replicated DB cluster |

**Rule of Thumb:**
- **90%+ reads** should hit cache layers.
- **Cache hit ratio** >80% for Redis; >50% for in-memory.

---

## **Related Patterns**
1. **Cache Aside (Lazy Loading)**
   - FraiseQL’s default; valid when data is read infrequently.
   - *Complement:* Explicit cache invalidation on writes.

2. **Write-Through Cache**
   - Use for critical data where immutability is required.
   - *Example:* Cache database writes to Redis **and** DB simultaneously.

3. **Write-Behind Cache**
   - Batch writes to Redis to reduce load (e.g., analytics).
   - *Implementation:* Async task queue (e.g., Kafka topic).

4. **Stale-While-Revalidate**
   - Serve stale Redis data while async refreshes DB.
   - *Use Case:* High-traffic dashboards with eventual consistency.

5. **Multi-Region Caching**
   - Deploy Redis clusters in each region + CDN edge caching.
   - *Challenge:* Cross-region consistency tradeoffs.

---

## **Configuration Reference**
| **Property**                     | **Default**               | **Description**                                  |
|----------------------------------|---------------------------|--------------------------------------------------|
| `fraise.cache.inMemory.maxSize`  | 10,000                    | Max entries in JVM cache                         |
| `fraise.cache.redis.ttl`         | 3600 (1 hour)             | Default Redis TTL for queries                    |
| `fraise.cache.fallbackToDB`      | `true`                    | Enable DB fallback if cache layers fail          |
| `fraise.cache.invalidateOnWrite` | `true`                    | Auto-clear cache on DB writes                    |

**Example `application.yml`:**
```yaml
fraise:
  cache:
    inMemory:
      maxSize: 20000
    redis:
      ttl: 7200  # 2 hours
      clusterNodes: ["redis1:6379", "redis2:6379"]
```

---
## **Troubleshooting**
### **Common Issues**
| **Symptom**               | **Root Cause**                          | **Solution**                                  |
|---------------------------|----------------------------------------|-----------------------------------------------|
| High DB load              | Cache misses >50%                      | Increase TTLs or optimize queries             |
| Stale data                | TTL too long or missed invalidation    | Debug triggers/Pub/Sub                         |
| Redis connection errors   | Node failure or network partition      | Enable Redis failover (Sentinel)               |
| Memory spikes             | In-memory cache not evicting aggressively | Adjust `maxSize` or use `GuavaCache#size()`    |

### **Diagnostics Commands**
```sql
-- Check cache hit ratio (FraiseQL CLI)
SELECT cache_metrics();

-- Redis stats
INFO stats | grep keyspace_hits
```

---
## **Conclusion**
The **Three-Layer Cache Hierarchy** balances performance, consistency, and operational simplicity. By strategically layering in-memory, distributed, and database caches, FraiseQL minimizes database load while maintaining tight control over stale data. **Key takeaways:**
1. Use in-memory for short-lived, high-frequency data.
2. Offload medium-traffic data to Redis with long TTLs.
3. Let the database handle writes and critical consistency.

For further reading, see the [Cache Tuning Guide](link) and [Redis Cluster Setup](link).