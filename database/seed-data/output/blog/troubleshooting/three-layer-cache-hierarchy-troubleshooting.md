# **Debugging the Three-Layer Cache Hierarchy: A Troubleshooting Guide**
*(L1 → L2 → L3: In-Memory → Redis → Database)*

This guide helps diagnose and resolve issues in a **three-layer cache** system where:
- **L1 (In-Memory Cache)** → Sub-millisecond access (e.g., `java.util.concurrent.ConcurrentHashMap`, Caffeine, Guava Cache).
- **L2 (Redis)** → 1-5ms latency (distributed, shared across instances).
- **L3 (Database)** → Fallback (10-50ms, e.g., PostgreSQL, MySQL).

---

## **1. Symptom Checklist**
Before diving into fixes, verify these common symptoms to narrow down the issue:

| **Symptom**                          | **Possible Cause**                          | **Immediate Check** |
|--------------------------------------|--------------------------------------------|---------------------|
| High database load despite caching   | Cache misses overwhelming DB               | Check DB query logs, cache hit/miss ratios |
| Inconsistent data across instances   | Stale L1/L2 cache (no proper invalidation) | Verify cache TTL, write-through semantics |
| Slow response times (50+ ms)         | L2 (Redis) latency spikes or L1 misses     | Monitor Redis latency, in-memory cache size |
| Memory spikes and GC pressure        | L1 cache not evicting stale data           | Check JVM heap usage, cache eviction policies |
| Cache stampedes (thundering herd)    | L2 misses causing DB overload               | Review cache key design and TTL settings |
| Application crashes on startup       | Redis connection errors or misconfig        | Check `INFO stats` in Redis CLI |

---

## **2. Common Issues & Fixes**

### **Issue 1: High Database Load Due to Cache Misses**
**Root Cause:**
- L1/L2 misses force requests to L3 (DB), causing bottlenecks.
- Cache keys are too broad (e.g., caching entire DB rows instead of specific fields).

**Debugging Steps:**
1. **Check Cache Hit/Miss Metrics**
   - For L1: Log cache miss ratio (e.g., `% of requests hitting DB`).
   - For L2: Use Redis `INFO stats` to see `keyspace_hits` vs. `keyspace_misses`.
   - **Tool:** Prometheus + Grafana (if metrics are exposed).

2. **Example: Debugging L1 Cache Misses (Java - Caffeine)**
   ```java
   Cache<String, User> l1Cache = Caffeine.newBuilder()
       .maximumSize(10_000)  // Tune based on memory constraints
       .recordStats()        // Track hits/misses
       .build();

   // Log stats periodically
   Metrics metrics = l1Cache.stats();
   log.info("L1 Cache: Hits={}, Misses={}, Load={}",
       metrics.hitCount(), metrics.missCount(), metrics.loadCount());
   ```
   - **Fix:** Optimize cache keys (e.g., cache by ID instead of entire objects).

3. **Check Redis Latency**
   - Use `redis-cli --latency` to measure latency spikes.
   - **Fix:** If Redis is slow, consider:
     - Increasing Redis memory (`maxmemory`).
     - Using `memory-max-fragments` to prevent fragmentation.
     - Migrating to a Redis cluster if single-node is a bottleneck.

---

### **Issue 2: Inconsistent Data Across Instances (Stale Cache)**
**Root Cause:**
- L1/L2 caches aren’t invalidated after writes.
- Eventual consistency missed (e.g., no pub/sub for cache updates).

**Debugging Steps:**
1. **Verify Write-Through/Update Semantics**
   - Ensure writes **always** update L1, L2, and DB.
   - **Example (Spring Data Redis):**
     ```java
     @Cacheable(cacheNames = "users")  // Read from L1/L2
     public User getUser(Long id) {}

     @CacheEvict(cacheNames = "users", key = "#id")  // Invalidate on write
     public User saveUser(User user) {}
     ```
   - **Fix:** If using manual updates, add a **cache invalidation queue** (e.g., Kafka topic).

2. **Check Redis Pub/Sub for Distributed Invalidation**
   - If using **write-behind**, ensure Redis syncs are reliable.
   - **Example (Redis Lua Script for Invalidation):**
     ```lua
     -- Script to delete a key and publish an event
     if redis.call("exists", KEYS[1]) == 1 then
       redis.call("del", KEYS[1])
       redis.publish("cache:invalidate", ARGV[1])
     end
     ```
   - **Fix:** If pub/sub is slow, use **Redis `SORT` + `LPUSH`** for FIFO invalidation.

---

### **Issue 3: L1 Cache Stale (Memory Pressure)**
**Root Cause:**
- L1 cache never evicts old data (e.g., `ConcurrentHashMap` with no size limit).
- Memory leaks from cached objects.

**Debugging Steps:**
1. **Check JVM Heap Usage**
   - Run `jmap -histo:live <pid>` to find large cached objects.
   - **Fix:** Use a **size-limited cache** (e.g., Caffeine, Guava).
     ```java
     Cache<String, User> cache = Caffeine.newBuilder()
         .maximumSize(5_000)  // Evict least recently used
         .expireAfterWrite(5, TimeUnit.MINUTES)
         .build();
     ```

2. **Enable Cache Stats Logging**
   - Log evictions and misses to detect leaks.
     ```java
     cache.stats().evictionCount();
     ```

---

### **Issue 4: Thundering Herd (Cache Stampede)**
**Root Cause:**
- All instances miss L2 cache simultaneously → DB overload.

**Debugging Steps:**
1. **Enable Redis Persistence Logging**
   - Check `redis.conf` for `slowlog-log-slower-than` and monitor `slowlog`.
   - **Fix:** Implement **cache warming** or **sticky sessions** to distribute load.

2. **Use Probabilistic Early Expiration (PEE)**
   - Expire cache keys **randomly** before TTL to reduce stampedes.
   - **Example (Caffeine):**
     ```java
     .expireAfterWrite(10, TimeUnit.MINUTES)
     .recordStats()
     .maximumSize(10_000);
     ```

---

### **Issue 5: Redis Connection Issues**
**Root Cause:**
- Application can’t connect to Redis (misconfigured `host:port`).
- Redis server overloaded (memory exhaustion).

**Debugging Steps:**
1. **Check Redis Connection Pool**
   - Use **HikariCP for Redis** (or `lettuce` pooling).
     ```java
     RedisConnectionFactory factory = new RedisConnectionFactory();
     factory.setHost("redis-host");
     factory.setPort(6379);
     factory.setPoolConfig(new PoolConfig(10, 100, 2, 5)); // min-max threads
     ```
   - **Fix:** Increase pool size if seeing `ConnectionTimeoutException`.

2. ** Monitor Redis Memory**
   - Run `redis-cli --stat` to check used memory vs. maxmemory.
   - **Fix:** If OOM, enable **maxmemory-policy** (e.g., `allkeys-lru`).

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**          | **Use Case**                                  | **Example Command**                          |
|-----------------------------|---------------------------------------------|---------------------------------------------|
| **Redis CLI (`redis-cli`)** | Check keys, latency, memory usage.          | `redis-cli --latency`                       |
| **Prometheus + Grafana**    | Monitor cache hit ratios, DB query times.    | `redis_misses_total`, `cache_miss_rate`     |
| **Java Flight Recorder (JFR)** | Profile L1 cache performance.               | `jcmd <pid> JFR.start duration=60s filename=cache_profile.jfr` |
| **Redis Sentinel**          | High-availability checks.                  | `sentinel monitor mymaster 127.0.0.1 6379 1` |
| **Log4j2 + MDC**            | Correlate cache misses to requests.        | `MDC.put("cache_layer", "L2")` in logs     |
| **PostgreSQL Slow Query Log** | Identify slow DB fallbacks.            | `log_min_duration_statement = 1000`         |

---

## **4. Prevention Strategies**

### **A. Optimize Cache Key Design**
- **Do:**
  - Cache by **unique IDs** (not entire objects).
  - Use **composite keys** for frequently accessed subsets.
    ```java
    // Bad: Cache entire User object
    cache.put("user:123", user);

    // Good: Cache only fields needed by API
    cache.put("user:123:profile", user.getProfile());
    ```
- **Avoid:**
  - Keys with wildcards (e.g., `user:*`).
  - Keys that grow indefinitely (e.g., `user:1_000_000`).

### **B. Implement Proper TTLs**
- **L1:** Short TTL (e.g., 1min) + high eviction rate.
- **L2:** Medium TTL (e.g., 10min) + Redis persistence.
- **L3:** Long TTL (e.g., 1h) + database sync.

**Example (Caffeine + Redis):**
```java
// L1 (In-Memory)
Cache<String, User> l1 = Caffeine.newBuilder()
    .expireAfterWrite(1, TimeUnit.MINUTES)
    .maximumSize(10_000)
    .build();

// L2 (Redis)
@Cacheable(value = "users", key = "#id", ttl = 10) // 10 minutes
public User getUserFromRedis(Long id) { ... }
```

### **C. Use Write-Through for Critical Data**
- Instead of **write-behind**, update **all layers** (L1 → L2 → DB) on every write.
- **Example (Spring Data):**
  ```java
  @CacheEvict(value = "users", key = "#user.id")
  @Transactional
  public User updateUser(User user) {
      userRepository.save(user); // Updates DB and flushes L2
      return user;
  }
  ```

### **D. Implement Cache Warming**
- Pre-load L1/L2 with **hot keys** on startup.
  ```java
  @PostConstruct
  public void warmCache() {
      List<User> users = userRepository.findTop100ByPopularity();
      l1Cache.putAll(users.stream()
          .collect(Collectors.toMap(User::getId, user -> user)));
  }
  ```

### **E. Monitor & Alert on Cache Degradation**
- **Set up alerts** for:
  - Redis latency > 5ms.
  - L3 (DB) query time > 50ms (indicating cache misses).
  - High Redis evictions (`evicted_keys` in `INFO stats`).

**Prometheus Alert Example:**
```yaml
groups:
- name: cache-alerts
  rules:
  - alert: HighRedisLatency
    expr: redis_latency_seconds > 0.005
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Redis latency spike ({{ $value }}s)"
```

---

## **5. Summary Checklist for Quick Fixes**
| **Issue**               | **Quick Fix**                          | **Long-Term Solution**                    |
|--------------------------|----------------------------------------|-------------------------------------------|
| High DB load             | Check cache hit ratio                  | Optimize keys, add L1/L2                     |
| Stale cache              | Force invalidate (`REDIS DEL`, `@CacheEvict`) | Pub/Sub or Lua scripts for invalidation |
| Memory leaks (L1)        | Enable eviction logging                | Use Caffeine/Guava with size limits         |
| Thundering herd          | Add probabilistic expiration           | Cache warming, sticky sessions             |
| Redis connection fails   | Check `maxActive` in connection pool  | Use Redis Sentinel for HA                  |
| Slow L2 responses        | Check `redis-cli --latency`            | Scale Redis or use Redis Cluster           |

---

## **Final Notes**
- **Start with metrics** (`INFO stats`, `jstat -gc`).
- **Test invalidation** manually (e.g., `FLUSHALL` in Redis, then verify data).
- **Benchmark under load** (e.g., using **Locust** or **k6**).
- **Document cache policies** (TTLs, key design, invalidation triggers).

By following this guide, you can **diagnose, fix, and prevent** common issues in a **three-layer cache** system efficiently.