# **[Pattern] Caching Best Practices – Reference Guide**

---

## **Overview**
Caching is a performance optimization technique that stores frequently accessed data in faster-accessible memory layers (e.g., in-memory caches, CDNs, or edge caches) to reduce latency and database/query load. This guide outlines proven caching best practices to maximize efficiency, minimize overhead, and ensure consistency when integrating caching into applications.

Best practices cover:
- **Cache placement** (client-side, server-side, distributed)
- **Cache invalidation strategies** (time-based vs. event-based)
- **Data serialization** (JSON, Protocol Buffers, MessagePack)
- **Cache size and eviction policies** (LRU, LFU, TTL)
- **Monitoring and analytics** (cache hit rate, miss rate, latency)
- **Security considerations** (cache poisoning, side-channel attacks)

Follow these guidelines to avoid common pitfalls like stale data, cache stampedes, or resource exhaustion while achieving optimal performance.

---

## **Implementation Details**

### **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                  |
|------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Cache hit**          | Request retrieved from cache without querying the source.                     | User fetches product page; data from Redis.  |
| **Cache miss**         | Request requires querying the source due to a stale or missing cache entry.  | User visits first-time product page; DB hit. |
| **Cache stampede**     | Multiple requests flood the source when cache expires simultaneously.        | All users refresh at TTL expiry.           |
| **Cache-invalidation** | Process of removing stale or outdated entries from the cache.                  | New product published → cache purge.        |
| **Time-to-Live (TTL)** | Duration an item remains valid in cache before expiration.                    | API response cached for 5 minutes.         |
| **Write-through**      | Updates to cache and source happen simultaneously.                            | User edits profile → cache + DB updated.    |
| **Write-behind**       | Updates are written to cache first; source is updated later (async).          | Order processed → cache updated; DB syncs later. |
| **Cache-aside (Lazy)**  | Cache is checked first; source is queried only on miss.                      | User requests data → check cache → DB fallback. |

---

## **Schema Reference**

| **Parameter**          | **Description**                                                                                     | **Recommended Value/Strategy**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Cache Layer**        | Where cache is deployed (client, server, distributed).                                           | Distributed (e.g., Redis, Memcached) for multi-instance apps; client-side for static assets.                          |
| **Cache Key**          | Unique identifier for cache entries (e.g., URL, request ID, object ID).                          | Use consistent hashing; avoid long, variable-length keys.                                                     |
| **Cache Value**        | Serialized data stored in cache (e.g., JSON, Protocol Buffers).                                  | Use efficient formats (e.g., MessagePack for binary data).                                                      |
| **TTL**                | Time-to-live for cache entries (in seconds or datetime).                                          | Set TTL based on data volatility (e.g., 1h for dynamic content, 24h for static).                                  |
| **Max Size**           | Maximum memory allocated to cache (e.g., 1GB).                                                      | Monitor usage; adjust based on workload.                                                                          |
| **Eviction Policy**    | Rule for removing least valuable entries when cache is full (LRU, LFU, FIFO).                     | **LRU (Least Recently Used)** for most cases; **LFU (Least Frequently Used)** for long-tailed data.                  |
| **Invalidation Rule**  | How cache entries are marked as stale (time-based, event-based, or hybrid).                       | Hybrid (e.g., TTL + cache-invalidation on write).                                                                |
| **Cache Coherence**    | Mechanism to ensure all cache instances have identical data (e.g., distributed locks).             | Use **distributed locks** (e.g., Redis LUA scripts) for write-behind caches.                                       |
| **Cache Warmup**       | Pre-loading cache with anticipated requests to reduce cold-start latency.                          | Schedule warmup during off-peak hours; use **proactive caching** for expected spikes.                              |
| **Compression**        | Compressing cache values to reduce memory usage.                                                 | Enable gzip or Snappy for text-based data; avoid for small or binary data.                                         |
| **Security Headers**   | Protecting cache from attacks (e.g., cache poisoning, side-channel leaks).                       | Use **Cache-Control: no-store** for sensitive data; sanitize keys.                                               |

---

## **Query Examples**

### **1. Basic Caching (Write-Through)**
**Scenario:** Cache and database are updated simultaneously when a user creates a profile.
```python
# Pseudocode
def update_user_profile(user_id, data):
    # 1. Update database
    db.update(user_id, data)

    # 2. Update cache (write-through)
    cache.set(f"user:{user_id}", data, ttl=3600)  # 1-hour TTL
```

### **2. Cache-Aside (Lazy Loading)**
**Scenario:** Check cache first; fall back to database if missing.
```javascript
// Node.js (with Redis)
async function getUserProfile(userId) {
    const cacheKey = `user:${userId}`;
    const cachedData = await redis.get(cacheKey);

    if (cachedData) {
        return JSON.parse(cachedData); // Cache hit
    }

    // Cache miss → fetch from DB
    const dbData = await db.query("SELECT * FROM users WHERE id = ?", [userId]);
    if (dbData.length) {
        await redis.setex(cacheKey, 3600, JSON.stringify(dbData[0])); // Set with TTL
    }
    return dbData[0];
}
```

### **3. Cache Invalidation (Event-Based)**
**Scenario:** Invalidate cache when a product price changes.
```java
// Java (with Spring Cache)
@CacheEvict(value = "products", key = "#productId")
public void updateProductPrice(Long productId, BigDecimal newPrice) {
    // Update database
    productRepository.save(productId, newPrice);
    // Cache is automatically invalidated via @CacheEvict
}
```

### **4. Cache Stampede Protection**
**Scenario:** Prevent multiple requests from querying the database when cache expires.
```python
# Pseudocode using a distributed lock
def getExpensiveData(key):
    lock = get_lock(f"lock:{key}")  # Redis lock
    try:
        lock.acquire(timeout=5)  # 5-second lock

        cachedData = cache.get(key)
        if cachedData:
            return cachedData

        # Cache miss → compute data (single thread)
        data = compute_expensive_data(key)
        cache.set(key, data, ttl=3600)
        return data
    finally:
        lock.release()
```

### **5. Conditional Caching (ETag/Last-Modified)**
**Scenario:** Use HTTP headers to validate cache freshness.
```http
# Response headers
Cache-Control: max-age=3600
ETag: "abc123"  # Unique hash of the response body
```

**Client-side validation:**
```javascript
// Fetch with ETag
fetch("/api/data", {
    headers: { "If-None-Match": "abc123" }
})
.then(response => {
    if (response.status === 304) {
        // Cache hit (no new data)
        console.log("Using cached data");
    } else {
        // Cache miss → update cache
    }
});
```

---

## **Advanced Patterns**

| **Pattern**               | **Use Case**                                                                 | **Implementation Notes**                                                                                     |
|---------------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| **Multi-Level Caching**   | Combine fast local cache (e.g., in-memory) with a distributed cache (Redis). | Example: Local cache → Redis → Database.                                                              |
| **Cache Sharding**        | Split cache into partitions to reduce contention in distributed systems.        | Use consistent hashing for key distribution (e.g., `shard_key = hash(key) % num_shards`).                 |
| **Cache Preloading**      | Load frequently accessed data into cache during idle periods.                  | Use cron jobs or event triggers (e.g., "popular posts" preload).                                       |
| **Cache Stampede Recovery** | Limit concurrent fallback queries during cache misses.                       | Implement **rate limiting** (e.g., allow only 10 parallel DB queries per cache miss).                     |
| **Cache Warming**         | Proactively load expected data before traffic spikes.                        | Example: Warm cache for Black Friday sales 1 hour before event.                                        |

---

## **Monitoring and Metrics**

| **Metric**               | **Purpose**                                                                 | **Example Tools**                                                                   |
|--------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Cache Hit Ratio**      | % of requests served from cache vs. source.                                | `hit_ratio = hits / (hits + misses)` (Ideal: >90%)                               |
| **Average Cache Latency**| Time to retrieve data from cache (target: <1ms).                            | Use APM tools like New Relic or Datadog.                                         |
| **Cache Size Usage**     | Track memory consumption to avoid evictions.                                | Redis `INFO memory` command; Prometheus metrics.                                  |
| **Eviction Rate**        | Frequency of entries removed due to capacity limits.                        | Monitor `evictions` counter in cache metrics.                                      |
| **TTL Distribution**     | Analyze cache entry lifespans to optimize TTL policies.                      | Use histogram metrics (e.g., Prometheus `histogram_quantile`).                     |
| **Cache Miss Patterns**  | Identify hotkeys causing frequent cache misses.                            | Log cache keys on misses; use tools like Redis Slowlog.                           |

**Example Query (PromQL):**
```promql
# Cache hit ratio
1 - (redis_cache_misses_total{rrole="products"}) / (redis_cache_misses_total{rrole="products"} + redis_cache_hits_total{rrole="products"})
```

---

## **Security Considerations**

| **Risk**                  | **Mitigation Strategy**                                                                                     | **Example**                                                                   |
|---------------------------|----------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Cache Poisoning**       | Sanitize cache keys to prevent injection attacks.                                                          | Use `cache_key = sanitize_input(user_input)` (e.g., remove special chars).   |
| **Side-Channel Attacks**  | Avoid exposing sensitive data in cache keys or metadata.                                                 | Use generic keys (e.g., `user_123` instead of `user_email=user@example.com`). |
| **Cache Denial-of-Service** | Limit cache size per key to prevent abuse.                                                                 | Set `maxmemory-policy=allkeys-lru` in Redis with per-key limits.              |
| **Stale Data Attacks**    | Use short TTLs or event-based invalidation for critical data.                                             | TTL=5m for session tokens; invalidate on logout.                                |
| **Cache Bypass**          | Ensure cache headers (`Cache-Control`) are respected by clients.                                          | Enforce `no-cache` for sensitive endpoints.                                  |

---

## **Anti-Patterns to Avoid**

| **Anti-Pattern**          | **Problem**                                                                                               | **Solution**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Over-Caching**          | Caching every API response, increasing memory usage without benefits.                                    | Cache only expensive or frequently accessed data.                                             |
| **Infinite TTL**          | Never-invalidating cache leads to stale data.                                                              | Use **short TTLs (e.g., 5–30 mins)** + event-based invalidation.                               |
| **No Cache Invalidation** | Failing to update cache after writes causes inconsistent data.                                           | Implement **write-through** or **cache-aside** + invalidation.                                |
| **Cache Key Collisions**  | Similar keys (e.g., `user:1` vs. `user:001`) wasting memory.                                              | Normalize keys (e.g., `user_1`).                                                              |
| **Ignoring Cache Size**    | Unbounded cache growth leads to evictions or OOM errors.                                                 | Set **memory limits** and use eviction policies (LRU/LFU).                                      |
| **No Monitoring**         | Undetected cache inefficiencies (e.g., low hit ratio).                                                  | Track **hit/miss ratios**, **latency**, and **evictions**.                                      |

---

## **Tools and Libraries**
| **Tool/Library**          | **Purpose**                                                                                            | **Supported Languages**                     |
|---------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Redis**                 | In-memory data store with persistence and pub/sub.                                                    | Multi-language (CLI, Python, Java, etc.)     |
| **Memcached**             | Fast, distributed caching for simple key-value storage.                                              | C, Java, PHP, Node.js                       |
| **Apache Guacamayo**      | Automatic cache invalidation for Spring Boot.                                                         | Java                                        |
| **Caffeine**              | High-performance JVM cache library.                                                                   | Java                                        |
| **Guava Cache**           | Java cache with TTL, size limits, and eviction policies.                                              | Java                                        |
| **Varnish Cache**         | HTTP accelerator/cache for web servers.                                                               | CLI, Lua                                     |
| **CloudFront (AWS)**      | CDN with edge caching for global low-latency access.                                                  | HTTP requests                               |
| **Prometheus + Grafana**  | Monitoring and alerting for cache metrics.                                                              | Multi-language                               |

---

## **Related Patterns**
1. **Circuit Breaker**
   - **Relation:** Prevents cache stampedes by throttling fallback queries to the source.
   - **When to Use:** Combine with caching for resilient high-latency APIs.

2. **Bulkhead**
   - **Relation:** Isolates cache-related operations to prevent cascading failures.
   - **When to Use:** Distributed systems where cache misses could overload databases.

3. **Retries with Exponential Backoff**
   - **Relation:** Handles transient cache failures (e.g., Redis outage) gracefully.
   - **When to Use:** Pair with cache-aside patterns for robustness.

4. **Asynchronous Processing (Queue-Based)**
   - **Relation:** Offloads cache updates to background workers to avoid blocking.
   - **When to Use:** Write-behind caching for non-critical updates.

5. **Rate Limiting**
   - **Relation:** Protects cache from abuse (e.g., DDoS attacks).
   - **When to Use:** APIs with caching to prevent cache exhaustion.

6. **Database Sharding**
   - **Relation:** Complements caching by distributing query load.
   - **When to Use:** High-traffic apps where caching alone can’t handle demand.

---
**Further Reading:**
- [Redis Best Practices](https://redis.io/topics/best-practices)
- [Google’s Caffeine Cache Guide](https://github.com/ben-manes/caffeine/wiki)
- [AWS Caching Strategies](https://docs.aws.amazon.com/whitepapers/latest/caching-strategies-for-microservices-on-aws/cache-strategies.html)