# **[Pattern] Caching Tuning – Reference Guide**

---

## **Overview**
Caching Tuning optimizes the performance and efficiency of caching layers in distributed systems by adjusting configuration, eviction policies, and cache invalidation strategies. Proper tuning reduces latency, minimizes memory overhead, and ensures data consistency. This guide covers key concepts, implementation best practices, and practical adjustments for in-memory caches (e.g., Redis, Memcached), CDNs, and application-level caches.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Example**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Cache Hit Rate**     | Percentage of requests served from cache (lower misses = better tuning).                           | `85% hit rate` means 85% of requests avoid database queries.                                  |
| **Time-to-Live (TTL)** | Duration (in seconds) objects remain in cache before expiration.                                    | `3600` (1 hour TTL) for user sessions.                                                          |
| **Eviction Policy**    | Rule for removing stale cached items when memory is full.                                            | **LRU (Least Recently Used)**: Drops items least recently accessed.                              |
| **Cache Invalidation** | Sync mechanism to purge stale data from cache (e.g., on DB updates).                               | Invalidate cache after `update_user()` in the database.                                         |
| **Cache Partitioning** | Splitting cache into isolated segments to reduce contention.                                       | Use separate Redis keyspaces for `users` vs. `products`.                                      |
| **Cache Warming**      | Preloading frequently accessed data into cache proactively.                                         | Load top 100 blog posts into cache at startup.                                                 |
| **Cache Granularity**  | Size of data units stored in cache (coarse/fine).                                                   | **Coarse**: Cache entire API responses.<br>**Fine**: Cache individual DB records.              |

---

## **Implementation Details**

### **1. Caching Backend Selection**
Choose a cache based on use case:

| **Cache Type**       | **Use Case**                          | **Example Tools**       | **Pros**                          | **Cons**                          |
|----------------------|---------------------------------------|-------------------------|-----------------------------------|-----------------------------------|
| **In-Memory (Redis)**| High-speed key-value storage          | Redis, Memcached        | Low latency (~1ms), persistence   | Memory-intensive, not for large data |
| **Distributed Cache**| Scalable, fault-tolerant storage      | Hazelcast, ScyllaDB     | Horizontally scalable             | Higher complexity                  |
| **CDN Cache**        | Static content (images, JS/CSS)       | Cloudflare, Fastly      | Global low latency                | Expires data quickly              |
| **Application Cache**| Local caching (e.g., `guavaCache`)    | Java `Cache`, Python `functools.lru_cache` | No external dependency | Limited size, ephemeral |

---

### **2. Tuning TTL (Time-to-Live)**
- **Short TTL (e.g., 5–10 mins)**:
  - Use for highly dynamic data (e.g., stock prices, real-time analytics).
  - Reduces stale data but increases cache misses.
  - *Example*: `SET user:123 data "..." EX 600` (10-minute TTL in Redis).

- **Long TTL (e.g., 1–24 hours)**:
  - Use for stable data (e.g., product catalogs, user profiles).
  - Optimizes hit rate but risks stale reads.
  - *Example*: `EXPIRE user:123 86400` (24-hour TTL).

- **Dynamic TTL**:
  - Adjust TTL based on data freshness (e.g., shorter TTL for frequently updated items).
  - *Tool*: Redis `TTL` command to check remaining time.

---

### **3. Eviction Policies**
Select a policy based on workload:

| **Policy**               | **Best For**                          | **Redis Equivalent**       | **When to Avoid**                  |
|--------------------------|---------------------------------------|----------------------------|------------------------------------|
| **LRU (Least Recently Used)** | General-purpose, uniform access | `maxmemory-policy lru`     | Data accessed at regular intervals |
| **LFU (Least Frequently Used)** | Sparse access patterns        | `maxmemory-policy lfu`     | New data rarely accessed           |
| **AllKeys-LRu**          | Memory-heavy caches                  | `maxmemory-policy allkeys-lru` | High eviction rate |
| **Volatile-LRu**         | Key-value pairs with TTL            | `maxmemory-policy volatile-lru` | No expiration |
| **No Eviction**          | Small, rarely full caches            | `maxmemory noeviction`     | Risk of OOM crashes                |

**Command Example (Redis):**
```bash
# Set maxmemory to 1GB with LRU eviction
CONFIG SET maxmemory 1gb maxmemory-policy lru
```

---

### **4. Cache Invalidation Strategies**
Purpose: Ensure cached data matches database state.

| **Strategy**               | **Description**                          | **Pros**                          | **Cons**                          | **Example**                                  |
|----------------------------|------------------------------------------|-----------------------------------|-----------------------------------|---------------------------------------------|
| **Time-Based**             | Delete after TTL expires.                | Simple, no extra logic            | Risk of stale data                | `EXPIRE key 3600`                            |
| **Event-Based**            | Invalidate on DB writes (e.g., via DB triggers). | Accurate                         | Adds complexity                    | Redis `DEL key` after `UPDATE user`        |
| **Write-Through**          | Write to cache **and** database.        | Strong consistency                | Higher write latency              | `SET key value AND UPDATE db`             |
| **Write-Back**             | Write only to cache; sync to DB later.   | Faster writes                     | Risk of data loss on failure       | Cache-aside pattern                          |
| **Tag-Based**              | Invalidate by tags (e.g., `user:profile`). | Flexible                         | Requires tagging system           | `UNLINK tag:user:*`                          |

**Example (Redis Pub/Sub for Invalidation):**
```bash
# Subscriber (listens to DB updates)
SUBSCRIBE db_updates
# Publisher (on DB write)
PUBLISH db_updates "INVALIDATE user:123"
```

---

### **5. Cache Partitioning**
Reduce cache contention by isolating data:

- **Sharding**: Split cache by entity (e.g., `user:*`, `product:*`).
  ```bash
  # Redis sharding example
  SET user:123:data "value" DB 1  # Database 1 for users
  SET product:456:data "value" DB 2 # Database 2 for products
  ```

- **Namespaces**: Use prefixes to avoid collisions.
  ```bash
  SET cache:user:123 "data"       # Prefix avoids key conflicts
  ```

- **Local vs. Global Cache**:
  - **Local**: Per-instance cache (e.g., `guavaCache` in Java).
  - **Global**: Shared cache (e.g., Redis cluster).

---

### **6. Cache Warming**
Preload expected data to avoid cold starts.

**Approach 1: Startup Script**
```python
# Preload popular blog posts
for post in db.query("SELECT id FROM posts WHERE views > 1000"):
    cache.set(f"post:{post.id}", db.get_post(post.id), TTL=3600)
```

**Approach 2: Scheduled Task**
```bash
# Cron job to warm cache every 6 AM
0 6 * * * python cache_warm.py
```

---

### **7. Cache Granularity**
- **Coarse-Grained**: Cache entire responses (e.g., API endpoints).
  ```bash
  # Cache API response for `/users/123`
  SET api:users:123 "{\"id\":123,\"name\":\"Alice\"}" EX 3600
  ```
  - *Pros*: Fewer cache misses.
  - *Cons*: Stale partial data if only one field updates.

- **Fine-Grained**: Cache individual fields (e.g., `user:123:name`).
  ```bash
  # Cache only the name field
  SET user:123:name "Alice" EX 3600
  ```
  - *Pros*: Faster invalidation.
  - *Cons*: More cache keys to manage.

---

### **8. Monitoring and Metrics**
Track tuning effectiveness with:

| **Metric**               | **Tool**               | **Target**                          |
|--------------------------|------------------------|-------------------------------------|
| **Hit Rate**             | Redis `INFO stats`     | >80% hit rate                        |
| **Evictions**            | Prometheus/Grafana     | <1000 evictions/day                 |
| **Latency**              | New Relic/Datadog      | <10ms p99 cache access               |
| **Memory Usage**         | Redis `MEMORY USAGE`   | Below 80% of maxmemory              |
| **TTL Distribution**     | Custom script          | Most TTLs between 300–3600 seconds  |

**Redis CLI Command for Metrics:**
```bash
INFO stats | grep -E "keyspace_hits|keyspace_misses|used_memory"
```

---

## **Query Examples**

### **1. Basic Cache Operations (Redis)**
```bash
# Set with TTL
SET user:123:name "Alice" EX 3600

# Get with TTL remaining
GET user:123:name
TTL user:123:name

# Delete
DEL user:123:name

# Check type
TYPE user:123:name
```

### **2. Redis Hash for Structured Data**
```bash
# Store user as a hash
HSET user:123 name "Alice" email "alice@example.com" age 30

# Get field
HGET user:123 name

# Increment field (e.g., visit count)
HINCRBY user:123 visits 1
```

### **3. Cache-Aside Pattern (Pseudocode)**
```python
def get_user(user_id):
    cache_key = f"user:{user_id}"
    user = cache.get(cache_key)
    if user is None:
        user = db.query(f"SELECT * FROM users WHERE id={user_id}")
        cache.set(cache_key, user, TTL=3600)
    return user

def update_user(user_id, data):
    db.update(f"UPDATE users SET ... WHERE id={user_id}")
    cache.delete(f"user:{user_id}")  # Invalidate
```

### **4. Cache with Fallback (Circuit Breaker)**
```python
def get_product(product_id):
    cache_key = f"product:{product_id}"
    product = cache.get(cache_key)
    if product is None:
        if db.is_down():  # Check circuit breaker
            return cache.get(f"product:{product_id}:fallback")
        product = db.get_product(product_id)
        cache.set(cache_key, product, TTL=7200)
    return product
```

---

## **Common Pitfalls and Fixes**

| **Pitfall**                          | **Cause**                          | **Solution**                                  |
|---------------------------------------|------------------------------------|-----------------------------------------------|
| **Thundering Herd**                   | Too many requests invalidate cache. | Use read-through + write-behind patterns.   |
| **Over-Caching**                      | Cache too much data.               | Audit cache keys; set realistic TTLs.         |
| **Cache Stampede**                    | High contention on invalidation.  | Add random delays (`Jittered Expiration`).    |
| **Memory Bloat**                      | Unbounded growth (e.g., hashes).    | Use `REDIS_MAXMEMORY_POLICY` (e.g., `allkeys-lru`). |
| **Stale Data**                        | No proper invalidation.            | Implement event-based invalidation.           |

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Cache-Aside](https://martinfowler.com/eaaCatalog/cacheAside.html)** | Query cache first; fall back to DB.                                        | Most application caching scenarios.     |
| **[Read-Through](https://martinfowler.com/eaaCatalog/readThroughCache.html)** | Cache on DB read; write-through on writes.                     | High-read, low-write workloads.         |
| **[Write-Through](https://martinfowler.com/eaaCatalog/writeThroughCache.html)** | Write to cache **and** DB.                                                 | Strong consistency required.             |
| **[Write-Back](https://martinfowler.com/eaaCatalog/writeBehind.html)** | Write to cache first; async DB sync.                                    | High-write throughput.                   |
| **[Database Sharding](https://martinfowler.com/eaaCatalog/databaseSharding.html)** | Split DB into horizontal partitions.                                     | Scale DB reads/writes independently.     |
| **[CDN Caching](https://martinfowler.com/eaaCatalog/cdnCaching.html)** | Cache static assets at edge locations.                                 | Global low-latency for static content.  |

---

## **Tools and Libraries**
| **Tool**               | **Purpose**                          | **Links**                                  |
|------------------------|---------------------------------------|--------------------------------------------|
| **Redis**              | In-memory key-value store.            | [https://redis.io](https://redis.io)        |
| **Memcached**          | Simple in-memory caching.             | [http://memcached.org](http://memcached.org) |
| **Guava Cache (Java)** | Local caching library.                | [https://github.com/google/guava](https://github.com/google/guava) |
| **Caffeine (Java)**    | High-performance caching.             | [https://github.com/ben-manes/caffeine](https://github.com/ben-manes/caffeine) |
| **Prometheus + Grafana** | Monitor cache metrics.                | [https://prometheus.io](https://prometheus.io) |
| **RedisInsight**       | GUI for Redis management.            | [https://redisinsight.redislabs.com](https://redisinsight.redislabs.com) |

---
**Summary**: Caching Tuning balances hit rate, consistency, and memory usage. Start with TTL and eviction policies, then refine with invalidation strategies, partitioning, and monitoring. Always measure impact on latency and cache hit rate.