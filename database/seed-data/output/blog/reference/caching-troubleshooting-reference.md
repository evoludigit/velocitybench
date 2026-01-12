# **[Pattern] Reference Guide: Caching Troubleshooting**

---

## **Overview**
Caching improves application performance by storing frequently accessed data in fast, low-latency memory. However, when misconfigured or corrupted, caching can degrade performance, introduce stale data, or cause application failures. This guide provides a structured approach to diagnosing and resolving common caching issues. It covers detection, root-cause analysis, mitigation, and preventative measures, ensuring optimal cache deployment.

---

## **Key Concepts**
### **1. Caching Layers & Types**
| **Layer**         | **Description**                                                                 | **Common Issues**                                                                 |
|-------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Memory Cache**  | In-memory data store (e.g., Redis, Memcached).                                  | Connection failures, key expiration, memory leaks, eviction policies.              |
| **Database Cache**| Cached database queries (e.g., Query Store, application-level caching).        | Stale queries, cache invalidation delays, inconsistent reads.                      |
| **Browser Cache** | Client-side caching (HTTP headers: `Cache-Control`, `ETag`).                   | Outdated content, cache busting issues (`Cache-Control: no-cache`).               |
| **CDN Cache**     | Edge caching (e.g., Cloudflare, Akamai).                                       | TTL misconfigurations, cache misses during traffic spikes.                          |
| **Application Cache** | Object-level caching (e.g., `HttpRuntime.Cache` in .NET, `Cache` in Java).  | Memory exhaustion, thread-safety issues, race conditions during writes.            |

---

### **2. Common Caching Problems**
| **Issue**               | **Symptom**                          | **Root Cause**                                                                 |
|-------------------------|--------------------------------------|--------------------------------------------------------------------------------|
| **Cache Misses**        | Slower response times, increased DB load. | Misconfigured TTL, incorrect cache key, stale key eviction.                  |
| **Stale Data**          | Users see outdated information.      | Cache not invalidated post-write, long TTLs, no cache versioning.            |
| **Memory Bloat**        | High memory usage, OOM errors.       | Unbounded cache growth, no eviction policy, memory leaks in cached objects.   |
| **Thundering Herd**     | Sudden spikes in DB queries.         | Cache invalidation race condition (e.g., all nodes request data simultaneously). |
| **Cache Invalidation**  | Delayed data updates.                | Missing `post-write` cache flush, weak consistency model.                     |
| **Connection Failures** | App crashes or timeouts.             | Network issues, Redis cluster down, misconfigured replication.                 |
| **Cache Overhead**      | High CPU/memory usage.               | Over-partitioning, excessive serialization/deserialization.                   |

---

## **Implementation Details**
### **Step 1: Detect Caching Issues**
#### **Logging & Monitoring**
- **Metrics to Track:**
  - Cache hit/miss ratio (`cache_hits / (cache_hits + cache_misses)`).
    - * Ideal: **> 90%** hit rate.
    - * < 80% indicates inefficient caching.
  - Latency comparison between cached vs. uncached endpoints.
  - Memory usage trends (e.g., Redis `used_memory`).
  - Error rates (e.g., Redis connection errors).

- **Tools:**
  - **Application Insights** (App Center), **Prometheus + Grafana** (metrics).
  - **Redis CLI**: `INFO stats` for memory/CPU usage.
  - **APM Tools**: New Relic, Datadog (distributed tracing).

#### **Logging Key Events**
```plaintext
[CacheHit] Key: "user:123", ValueSize: 4KB, TTL: 300s
[CacheMiss] Key: "product:456", FallbackToDB: true, Latency: 500ms
[CacheEvict] Key: "session:abc", Reason: "MemoryLimitExceeded"
[CacheWrite] Key: "config:settings", ValueSize: 10KB, TTL: 86400s
```

---

### **Step 2: Root-Cause Analysis**
#### **A. Cache Misses**
- **Common Causes:**
  - **Incorrect Key Generation**: Missing dynamic parameters (e.g., missing timestamp in query key).
  - **Short TTL**: Data expires too quickly (e.g., TTL=1s for a page).
  - **No Cache Key**: Accidental bypass (e.g., `Cache.Missing` return in .NET).
  - **Partitioning Issues**: Keys distributed unevenly (hot/cold keys).

- **Debugging Steps:**
  1. Check cache hit/miss logs for the problematic key.
  2. Verify TTL settings (`expire` in Redis, `CacheItemPolicy` in .NET).
  3. Validate key generation (e.g., `MD5(userId + timestamp)`).

#### **B. Stale Data**
- **Common Causes:**
  - Missing **cache invalidation** (e.g., no `Cache.Remove` on write).
  - **Long TTL** (e.g., 1 day for user preferences).
  - **Optimistic Locking Mismatch**: Cache update conflicts.

- **Debugging Steps:**
  1. Compare cached value with DB value.
  2. Check for `post-write` cache invalidation logic.
  3. Use **cache versioning** (e.g., append timestamp to key: `user:123:v2`).

#### **C. Memory Bloat**
- **Common Causes:**
  - **Unbounded Cache Growth**: No `maxmemory-policy` in Redis.
  - **Large Objects**: Caching entire DB rows instead of denormalized fields.
  - **Memory Leaks**: Unreleased cached objects (e.g., unclosed streams in cached values).

- **Debugging Steps:**
  1. Analyze `redis-cli --bigkeys` for large keys.
  2. Set eviction policies:
     ```redis
     config set maxmemory 1gb
     config set maxmemory-policy allkeys-lru
     ```
  3. Profile memory usage with tools like **Redis Memory Analyzer**.

#### **D. Thundering Herd**
- **Common Causes:**
  - **Lazy Invalidation**: Cache invalidated only on next read (race condition).
  - **No Background Refresh**: Cache expires, but fallback query overloads DB.

- **Debugging Steps:**
  1. Enable **pre-fetching** (refresh cache before it expires).
  2. Use **stale-while-revalidate** (HTTP: `Cache-Control: stale-while-revalidate=60`).
  3. Implement **distributed locks** (e.g., Redis `SET key value NX PX 10000`).

#### **E. Connection Failures**
- **Common Causes:**
  - **Redis Cluster Down**: No failover configured.
  - **Throttling**: Too many connections (default: 10k in Redis).
  - **Network Partitions**: Unreachable cache nodes.

- **Debugging Steps:**
  1. Check Redis logs for errors (`redis-cli --slaveof 127.0.0.1 6379` for replication issues).
  2. Configure **connection pooling** (e.g., `StackExchange.Redis` in .NET).
  3. Set up **high availability** (sentinel, Redis Cluster).

---

### **Step 3: Mitigation Strategies**
| **Issue**               | **Solution**                                                                 | **Tools/Configurations**                                  |
|-------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------|
| **High Cache Misses**   | Optimize TTL, improve key design.                                           | Redis `PERSIST` for critical data, hash keys for objects. |
| **Stale Data**          | Implement cache invalidation on write.                                      | `Cache.Remove(key)`, `publish-subscribe` for events.      |
| **Memory Bloat**        | Set eviction policies, compress large objects.                             | `maxmemory`, `lzf` compression in Redis.                   |
| **Thundering Herd**     | Use stale-while-revalidate or background refresh.                           | HTTP headers, `AsyncTask` for refresh.                    |
| **Connection Failures** | Add retry logic, configure HA.                                             | Polly library, Redis Sentinel.                            |
| **Cache Overhead**      | Reduce serialization overhead, optimize partitions.                         | Protobuf instead of JSON, consistent hashing.            |

---

## **Schema Reference**
### **1. Cache Key Design**
| **Field**       | **Description**                                                                 | **Example**                          | **Best Practices**                          |
|-----------------|---------------------------------------------------------------------------------|--------------------------------------|---------------------------------------------|
| `entityType`    | Type of cached data (e.g., `user`, `product`, `config`).                       | `"user"`                             | Use a fixed prefix (`user:123`).            |
| `entityId`      | Unique identifier (e.g., DB ID, UUID).                                         | `123`                                | Append version/timestamp (`user:123:v2`).    |
| `version`       | Version for cache invalidation (e.g., DB version, ETag).                        | `v2`                                 | Auto-increment on write.                    |
| `timestamp`     | Optional: Helps with stale detection.                                          | `1680000000`                         | Use `DateTime.UtcNow.Ticks`.                 |
| **Composite Key** | Combine fields for complex queries (e.g., `product:category:10:discount`).    | `product:123:price`                  | Avoid key explosion; use delimiters (`:`).   |

**Example Key:**
```
user:123:v2:profile:2023-04-01
```

---

### **2. Cache Invalidation Strategies**
| **Strategy**          | **Description**                                                                 | **When to Use**                          | **Tools**                                  |
|-----------------------|---------------------------------------------------------------------------------|------------------------------------------|--------------------------------------------|
| **Time-Based (TTL)**  | Data expires after a fixed duration.                                           | Static data (e.g., FAQs).               | Redis `EXPIRE`, .NET `CacheItemPolicy`.     |
| **Event-Based**       | Invalidate on specific events (e.g., `UserUpdated`).                            | Dynamic data (e.g., user profiles).      | Message queues (RabbitMQ, Kafka), DB triggers. |
| **Write-Through**     | Write to cache **and** DB simultaneously.                                      | Strong consistency required.            | Application logic.                          |
| **Write-Behind**      | Write to DB first, then cache (async).                                        | High throughput, eventual consistency.   | Background tasks (Hangfire, Celery).        |
| **Lazy Loading**      | Load from cache on first access; invalidate on DB update.                       | Low-traffic data.                        | Proxies (Varnish), CDN rules.              |
| **Cache-Aside (Lookup)** | Check cache first; fall back to DB.                                           | Default pattern.                         | All caching layers.                         |

---

### **3. Cache Configuration Examples**
#### **Redis (Cluster Mode)**
```ini
# redis.conf
cluster-enabled yes
cluster-config-file nodes.conf
cluster-node-timeout 5000
maxmemory 2gb
maxmemory-policy allkeys-lru
```

#### **.NET MemoryCache (AppSettings.json)**
```json
{
  "Caching": {
    "DefaultTTL": 60,
    "SlidingExpiration": true,
    "MaxItems": 10000,
    "MemoryCacheSizeLimit": 1073741824 // 1GB
  }
}
```

#### **HTTP Cache Headers**
```http
Cache-Control: public, max-age=3600, stale-while-revalidate=60
ETag: "xyz123"
```

---

## **Query Examples**
### **1. Diagnosing Cache Hits/Misses (Redis)**
```bash
# Check cache stats
redis-cli INFO stats | grep -i "keyspace_hits"

# List keys matching a pattern
redis-cli KEYS "user:*"

# Monitor cache access (real-time)
redis-cli monitor
```

### **2. .NET: Log Cache Activity**
```csharp
// Configure in Program.cs
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = "localhost";
    options.InstanceName = "MyAppCache";
});

// Log cache operations
public class CacheLogger : ICacheLogger
{
    public void LogCacheHit(string key, long sizeBytes) { /* Log */ }
    public void LogCacheMiss(string key) { /* Log */ }
}
```

### **3. SQL Server: Query Store Cache Analysis**
```sql
-- Check cache hits vs. recompiles
DBCC TRACEON (8272);
DBCC TRACEON (8273);

-- Review cached plans
SELECT plan_handle, cacheobjtype_desc
FROM sys.dm_exec_cached_plans
WHERE objecttype = 'Compiled Plan';
```

### **4. CDN: Purge Cached Files**
```bash
# Cloudflare CLI
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
     -H "Authorization: Bearer {api_token}" \
     -H "Content-Type: application/json" \
     --data '{"purge_everything":true}'
```

---

## **Related Patterns**
1. **[Cache-Aside Pattern]**
   - *Use Case*: Read-heavy applications.
   - *Key Idea*: Check cache first; fall back to DB if missed.
   - *Reference*: [Microsoft Cache-Aside Docs](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside).

2. **[Read-Through Pattern]**
   - *Use Case*: Hide database complexity from clients.
   - *Key Idea*: Cache layer fetches from DB on miss; clients interact only with cache.

3. **[Write-Through Pattern]**
   - *Use Case*: Strong consistency required.
   - *Key Idea*: Write to cache **and** DB simultaneously.

4. **[Write-Behind Pattern]**
   - *Use Case*: High throughput, eventual consistency.
   - *Key Idea*: Write to DB first; asynchronously update cache.

5. **[Circuit Breaker Pattern]**
   - *Use Case*: Handle cache service failures gracefully.
   - *Key Idea*: Fail fast and fallback (e.g., to a secondary cache).

6. **[Bulkhead Pattern]**
   - *Use Case*: Isolate cache failures from other services.
   - *Key Idea*: Limit concurrent cache operations.

7. **[Retry Pattern]**
   - *Use Case*: Transient cache failures (e.g., network blips).
   - *Key Idea*: Exponential backoff for cache writes/reads.
   - *Tools*: Polly library, `retry` in Redis clients.

8. **[Cache Warm-Up Pattern]**
   - *Use Case*: Pre-load cache at startup or during low-traffic periods.
   - *Key Idea*: Proactively populate cache to avoid thrashing.

---
## **Preventative Measures**
1. **Automated Testing**:
   - Unit tests for cache key generation.
   - Integration tests for cache invalidation.

2. **Chaos Engineering**:
   - Randomly kill cache nodes (simulate failures).
   - Test TTL expiry under load.

3. **Observability**:
   - Monitor cache metrics in production (e.g., Prometheus alerts).
   - Set up dashboards for hit/miss ratios.

4. **Documentation**:
   - Document cache schemas, TTLs, and invalidation rules.
   - Example:
     ```
     Cache: /api/users/{id}
     Key:   user:{id}:profile
     TTL:   300s
     Invalidation: Publish "UserUpdated" event.
     ```

5. **Gradual Rollout**:
   - Enable caching in staging first.
   - Use feature flags to toggle cache regionally.