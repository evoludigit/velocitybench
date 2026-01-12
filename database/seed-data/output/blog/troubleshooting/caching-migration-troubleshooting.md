# **Debugging Caching Migration: A Troubleshooting Guide**

## **1. Introduction**
Caching migration involves transitioning from one caching layer to another (e.g., Redis → Memcached, local cache → CDN, or upgrading cache versions). Even with a well-planned migration, issues like cache inconsistencies, stale data, increased latency, or application crashes can arise.

This guide provides a **hands-on, symptom-driven approach** to diagnose and resolve common caching migration problems efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, quickly assess the following symptoms to narrow down the issue:

| **Symptom**                     | **Possible Cause**                          | **Severity** |
|---------------------------------|--------------------------------------------|--------------|
| **Increased API response times** | Cache miss rate too high, stale cache      | Low-Medium   |
| **Cache inconsistencies**        | Data not persisted, stale reads/writes     | High         |
| **Duplicate requests**          | Cache bypassed, stale cache in flight      | Low-Medium   |
| **Application crashes**          | Cache-related timeouts, missing dependencies | High         |
| **High memory usage**           | Leaked cache entries, improper TTL         | Medium-High  |
| **Partial cache failures**       | Partial failover, inconsistent cache sync  | Medium       |
| **Read-heavy vs. write-heavy imbalance** | Cache eviction policies misconfigured | Medium |

**Quick Check:**
- **Is the new cache instance reachable?** (`ping`, `telnet`, or connectivity tests)
- **Are cache keys consistent?** (Same key behavior in old vs. new cache?)
- **Is the fallback mechanism working?** (Graceful degradation if cache fails)
- **Are metrics monitoring the cache hit/miss ratio?** (Use Prometheus, Datadog, etc.)

---

## **3. Common Issues & Fixes**

### **Issue 1: Stale Cache Data**
**Symptoms:**
- Users see outdated data (e.g., product prices, user profiles).
- `SELECT * FROM cache` shows inconsistent entries.

**Root Causes:**
- Cache invalidation not triggered on data updates.
- TTL too long, causing data to stay cached past changes.
- Race condition between write and cache update.

**Debugging Steps:**
1. **Check Cache Invalidation Logic**
   - Ensure cache keys are invalidated on write operations.
   - Example (Node.js with Redis):
     ```javascript
     // Before write → Invalidate cache
     await redis.del(`user:${userId}`);

     // After write → Update cache
     await userRepository.save(user);
     await redis.set(`user:${userId}`, JSON.stringify(user), 'EX', 3600);
     ```

2. **Verify TTL Configuration**
   - If using `set(key, value, 'EX', ttl)`, ensure `ttl` is appropriate.
   - Example (Python with Redis):
     ```python
     cache.set(f"product:{id}", product_data, ex=300)  # 5 min TTL
     ```

3. **Enable Cache Debug Logging**
   - Log cache hits/misses and invalidations:
     ```javascript
     console.log(`Cache hit/miss for key: ${key}, value: ${value}`);
     ```

**Fixes:**
- Implement **cache-aside pattern** with strict invalidation.
- Use **write-through caching** (update cache on every write).
- Introduce a **cache stampede protection** mechanism.

---

### **Issue 2: Increased Latency (Cache Misses)**
**Symptoms:**
- `cache hit ratio < 90%` (monitored via Prometheus/Grafana).
- Requests take longer than expected.

**Root Causes:**
- Cache too small → frequent misses.
- Cache keys not optimized (e.g., too broad or inconsistent).
- New cache instance not warmed up.

**Debugging Steps:**
1. **Check Cache Hit/Miss Metrics**
   - Example (Redis CLI):
     ```sh
     INFO stats  # Check hit rate, keyspace hits
     ```

2. **Analyze Cache Key Design**
   - Are keys **unique and consistent**?
   - Example (Bad vs. Good):
     ```python
     # Bad: Too broad (misses often)
     cache_key = "all_products"

     # Good: Granular (fewer misses)
     cache_key = f"product:{id}:details"
     ```

3. **Warm Up the Cache**
   - Pre-populate cache before migration:
     ```bash
     # Example: Load top 1000 products before cutoff
     ./load_cache.sh
     ```

**Fixes:**
- **Increase cache size** (or optimize eviction policy).
- **Use lazy loading** for rarely accessed data.
- **Implement cache sharding** if keys are too large.

---

### **Issue 3: Cache Failover Failures**
**Symptoms:**
- Application crashes with `RedisConnectionError` or `CacheNotFound`.
- Fallback mechanism not triggered.

**Root Causes:**
- Cache instance unreachable (network issues, misconfig).
- Fallback logic broken (e.g., database overload).
- Circuit breakers not implemented.

**Debugging Steps:**
1. **Test Connectivity**
   - Verify cache server is up:
     ```sh
     redis-cli ping  # Should return "PONG"
     ```
   - Check firewall/network rules.

2. **Check Fallback Logic**
   - Example (Node.js fallback):
     ```javascript
     try {
       const cachedData = await cache.get(key);
       if (!cachedData) throw new Error("Cache miss");
       return JSON.parse(cachedData);
     } catch (err) {
       console.error("Cache failed, falling back to DB");
       return await db.get(key);  // Fallback
     }
     ```

3. **Enable Retry Policies**
   - Add exponential backoff:
     ```javascript
     const retry = async (fn, maxRetries = 3) => {
       for (let i = 0; i < maxRetries; i++) {
         try { return await fn(); } catch (err) {}
         await new Promise(res => setTimeout(res, 100 * (i + 1)));
       }
       throw new Error("All retries failed");
     };
     ```

**Fixes:**
- **Implement circuit breakers** (e.g., Hystrix, Resilience4j).
- **Use a secondary cache** (e.g., Memcached if Redis fails).
- **Monitor cache health** (alert on `down` status).

---

### **Issue 4: Memory Leaks in Cache**
**Symptoms:**
- Cache server OOM (Out of Memory) errors.
- Memory usage spikes over time.

**Root Causes:**
- Unlimited TTL → infinite cache growth.
- Memory leaks in cache client (e.g., Redis connections not closed).
- Large objects cached without limits.

**Debugging Steps:**
1. **Check Memory Usage**
   - Redis:
     ```sh
     INFO memory  # Check used_memory, fragments
     ```
   - Docker:
     ```sh
     docker stats <container>
     ```

2. **Review TTL Policies**
   - Ensure `maxmemory-policy` is set:
     ```conf
     # redis.conf
     maxmemory 1gb
     maxmemory-policy allkeys-lru  # Evict least recently used
     ```

3. **Profile Cache Client**
   - Example (Node.js memory leak check):
     ```javascript
     const heapdump = require('heapdump');
     if (global.gc) {
       global.gc();  // Force GC and check for leaks
       heapdump.writeSnapshot('./heapdump-' + Date.now() + '.heapsnapshot');
     }
     ```

**Fixes:**
- **Set strict TTLs** (`EX`, `PX` in Redis commands).
- **Use `CLIENT-KILL`** to drop idle connections.
- **Limit object size** in cache keys (e.g., compress large data).

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                          | **Example Command**                  |
|--------------------------|---------------------------------------|--------------------------------------|
| **Redis CLI**            | Check server health, keyspace        | `INFO stats`, `KEYS *` (careful!)    |
| **Prometheus + Grafana** | Monitor cache hit/miss ratio          | `cache_hits_total / (cache_hits + cache_misses)` |
| **Redis Debug Mode**     | Enable slow query logging             | `slowlog "slowlog-log-slower-than 100ms"` |
| **Cache Client Profiling** | Detect memory leaks in app          | `node --inspect app.js` (Chrome DevTools) |
| **Network Sniffing (Wireshark/tcpdump)** | Check cache communication | `tcpdump -i eth0 port 6379` |
| **Load Testing (Locust/k6)** | Simulate cache under pressure | `locust -f cache_load_test.py` |

---

## **5. Prevention Strategies**
To avoid future caching migration headaches:

### **Pre-Migration Checklist**
✅ **Test in Staging**
- Simulate production traffic before full cutover.
- Verify **zero-downtime migration** (e.g., dual-write to old & new cache).

✅ **Monitor Key Metrics**
- Cache hit ratio (`> 90%` desired for most apps).
- Latency (`< 100ms` for API responses).
- Error rates (`0` cache-related errors).

✅ **Backup Cache Data**
- Use `SAVE` or `BGSAVE` in Redis before migration.
- Export keys if using Memcached:
  ```sh
  redis-cli --pipe < import.memcached
  ```

✅ **Fallback Mechanism**
- Always have a **secondary data source** (DB, static files).
- Example (Spring Boot fallback to DB):
  ```java
  @Cacheable(value = "products", key = "#id")
  public Product getProduct(@PathVariable Long id) {
      return productRepository.findById(id)
              .orElseThrow(() -> new RuntimeException("Not found"));
  }
  ```

### **Post-Migration Best Practices**
🔹 **Gradual Rollout**
- Use **canary releases** (deploy to 10% of users first).

🔹 **Automated Rollback**
- Script to switch back to old cache if issues arise:
  ```bash
  # Example: Switch from Redis to Memcached
  docker stop redis
  docker start memcached
  ```

🔹 **Document Cache Invalidation Rules**
- Keep a **cheat sheet** of which API calls invalidate which cache keys.

🔹 **Automated Alerts**
- Set up alerts for:
  - `cache_hit_ratio < 80%`
  - `cache_errors > 0`
  - `memory_usage > 90%`

---

## **6. Final Checklist Before Declaring Success**
| **Check**                          | **Pass/Fail** |
|------------------------------------|---------------|
| Cache hit ratio stable (≥90%)      | ✅/❌          |
| No stale data reported by users    | ✅/❌          |
| Fallback mechanism tested          | ✅/❌          |
| Memory usage < 80% of limit        | ✅/❌          |
| Zero production incidents          | ✅/❌          |

If all checks pass, **celebrate**—you’ve successfully migrated caching!

---
**Need help?** Check:
- [Redis Debugging Guide](https://redis.io/docs/management/debugging/)
- [Prometheus Cache Monitoring](https://prometheus.io/docs/introduction/overview/)
- [Cache Eviction Policies](https://redis.io/topics/lru-cache)