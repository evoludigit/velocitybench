---
# **[Pattern] Caching Debugging Reference Guide**

---

## **Overview**
Caching Debugging is a pattern used to identify, diagnose, and resolve performance bottlenecks in systems that rely on caches—such as in-memory caches (Redis, Memcached), database query caches, or application-layer caches. The goal is to verify cache behavior, validate hit/miss ratios, and troubleshoot issues like stale data, cache storms, or misconfigured eviction policies. This guide covers key concepts, implementation steps, schema references, and practical query examples for debugging cache behavior in distributed systems.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                  |
|-------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| **Cache Hit**           | A request retrieved from the cache instead of the source (e.g., DB).         | Redis: `GET user:123` → Returns cached data. |
| **Cache Miss**          | A request fetched from the source due to a cache miss.                        | Redis: `GET user:123` → Hits DB.             |
| **Cache Eviction**      | Removal of stale or least-recently-used (LRU) data from the cache.            | Memcached: Automatically drops 10% of items. |
| **Cache Storm**         | A surge of cache misses overwhelming the source system (e.g., DB).           | Sudden spike in `SELECT * FROM orders`.      |
| **TTL (Time-to-Live)**  | Duration a cached item remains valid before expiration.                       | Redis: `SET user:123 "data" EX 3600`.        |
| **Stale Data**          | Outdated cache entries due to failed updates or TTL misconfigurations.        | Shopping cart price not reflecting DB change.|
| **Cache Invalidation**  | Explicitly removing or updating cached data to reflect changes.               | `DEL user:123` in Redis after DB update.     |
| **Cache Warmer**        | Pre-loading cache entries to reduce miss rates during peak traffic.           | Script to populate `recommendations` cache. |

---

## **Implementation Details**

### **1. Debugging Cache Hits/Misses**
Monitor cache hit/miss ratios to identify inefficiencies:
- **Goal**: Aim for **>90% hit rate** for critical queries.
- **Tools**:
  - **Redis**: `INFO stats` command.
  - **Memcached**: Log analysis or `stats items` command.
  - **Application**: Instrument cache client libraries (e.g., Redis Java Client).

**Example (Redis CLI):**
```bash
# Check cache stats
127.0.0.1:6379> INFO stats | grep -i "hits\|misses"
keyspace_hits:100000
keyspace_misses:1000
```

**Code Instrumentation (Python with `redis-py`):**
```python
import redis
from prometheus_client import Counter

cache_hits = Counter('cache_hits_total', 'Cache hits')
cache_misses = Counter('cache_misses_total', 'Cache misses')

r = redis.Redis()
user_data = r.get('user:123')
if user_data:
    cache_hits.inc()
else:
    cache_misses.inc()
```

---

### **2. Diagnosing Cache Storms**
A cache storm occurs when a sudden spike in misses overloads the backend (e.g., database).
**Mitigation**:
- **Rate Limiting**: Throttle cache misses (e.g., using `Redis` `SET` with `NX` flag or application-level queues).
- **Cache Sharding**: Distribute cache keys across multiple cache instances.
- **Backoff Strategies**: Exponential backoff for retrying failed cache fetches.

**Example (Rate Limiting in Redis Lua):**
```lua
-- Lua script to limit cache misses per second per key
local max_misses = 10
local window_sec = 60
local key = KEYS[1]
local current = tonumber(redis.call('GET', key .. ':misses') or "0")
if current >= max_misses then
    return 0  -- Reject request
else
    redis.call('INCR', key .. ':misses')
    redis.call('EXPIRE', key .. ':misses', window_sec)
    return 1  -- Allow request
end
```

---

### **3. Validating Cache Invalidation**
Ensure cached data is invalidated when the source changes:
- **Strategies**:
  - **Explicit Invalidation**: Delete keys after DB updates (e.g., `DEL` in Redis).
  - **TTL-Based**: Rely on TTL to expire stale data.
  - **Pub/Sub Notifications**: Use event-driven invalidation (e.g., Redis Pub/Sub).

**Example (Pub/Sub Invalidation):**
1. **Publisher (DB listener)**:
   ```python
   from redis import Redis
   r = Redis()
   r.publish("db:updates", 'user:123')  # Notify cache to invalidate
   ```
2. **Subscriber (Cache)**:
   ```python
   def on_update(message):
       if message.decode() == 'user:123':
           r.delete(f'user:{message.decode()}')
   r.subscribe("db:updates", on_update)
   ```

---

### **4. Detecting Stale Data**
Stale data occurs when:
- TTL is too long.
- Invalidation fails silently.

**Debugging Steps**:
1. **Compare Cache vs. Source**:
   ```bash
   # Compare Redis with database
   redis-cli GET user:123 | jq .  # Cache
   curl http://api/db/user/123      # Source
   ```
2. **Log Cache-Write Timestamps**:
   ```python
   # Store write time in cache key
   r.hset('user:123', 'timestamp', str(time.time()))
   ```

---

### **5. Analyzing Cache Eviction Policies**
Cache eviction can degrade performance. Common policies:
| **Policy**       | **Description**                          | **When to Use**                          |
|-------------------|------------------------------------------|------------------------------------------|
| **LRU**           | Evicts least recently used items.        | Medium-sized caches with frequent access patterns. |
| **LFU**           | Evicts least frequently used items.       | Data with predictable access patterns.   |
| **Time-Based**    | Evicts items after TTL expires.          | Data with fixed lifespans.               |
| **Random**        | Evicts items randomly.                   | Low-traffic systems.                     |
| **AllKeysLru**    | Evicts all keys if capacity is exceeded. | Edge cases (e.g., memcached).           |

**Example (Memcached Eviction):**
```bash
# Check eviction policy in memcached
memclient -c -a -s 127.0.0.1:11211
> stats settings
```

---

## **Schema Reference**
| **Component**          | **Attributes**                          | **Purpose**                                      |
|------------------------|-----------------------------------------|--------------------------------------------------|
| **Cache Hit/Miss Log** | `timestamp`, `key`, `hit_miss`, `source` | Track cache performance over time.               |
| **Cache Key**          | `name`, `namespace`, `ttl`, `eviction_policy` | Define cache key metadata.                      |
| **Cache Storm Alert**  | `threshold`, `duration`, `miss_rate`    | Trigger alerts during cache storms.              |
| **Invalidation Queue** | `event_type`, `key`, `priority`         | Manage invalidation requests (e.g., Kafka).     |
| **Cache Stats**        | `hits`, `misses`, `memory_used`         | Monitor cache efficiency.                       |

**Example Schema (JSON):**
```json
{
  "cache_key": "user:123",
  "namespace": "auth",
  "ttl": 3600,
  "eviction_policy": "LRU",
  "last_accessed": "2023-10-01T12:00:00Z",
  "size_bytes": 1024
}
```

---

## **Query Examples**

### **1. Redis**
**Check Cache Hit Rate Over Time:**
```bash
# Use Redis time-series module (if available)
redis-cli --bigkeys | grep -i "hit\|miss"
```

**Find Most Frequently Accessed Keys:**
```bash
# Use Redis CLI + sorting
redis-cli --scan --pattern "*" | awk '{print $1}' | sort | uniq -c | sort -nr
```

### **2. Memcached**
**Monitor Cache Size and Evictions:**
```bash
# Use `memcached-tools` or `memtier_benchmark`
memcached-tool stats
```

**Check Eviction Rate:**
```bash
# Parse logs for evictions
grep "evicted" /var/log/memcached.log | awk '{print $NF}' | sort | uniq -c
```

### **3. Application-Level (Java)**
**Track Cache Performance with Prometheus:**
```java
// Metrics endpoint (Spring Boot)
@GetMapping("/cache/metrics")
public Map<String, Long> getCacheMetrics() {
    return Map.of(
        "hits", cacheHits.get(),
        "misses", cacheMisses.get(),
        "load_time_ms", cacheLoadTime.sum()
    );
}
```

---

## **Related Patterns**
| **Pattern**               | **Purpose**                                                                 | **When to Use**                                  |
|---------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **[Cache Aside]**         | Load data from cache; fallback to DB if cache miss.                        | General-purpose caching.                        |
| **[Write Through]**       | Update cache **and** DB on write operations.                                | Strong consistency required.                    |
| **[Write Behind]**        | Asynchronously update cache/DB after write.                                 | High write throughput needed.                   |
| **[Cache Stampede]**      | Mitigate cache storms using locking or queueing.                            | High-contention scenarios.                      |
| **[Cache Warmer]**        | Pre-load cache during low-traffic periods.                                  | Predictable traffic patterns.                  |
| **[Database Sharding]**    | Distribute DB load; cache per shard.                                       | Horizontal scaling for DB.                      |
| **[Circuit Breaker]**      | Fallback when cache/DB is unavailable.                                     | Fault tolerance.                                |

---

## **Best Practices**
1. **Monitor Continuously**: Use tools like Prometheus + Grafana for cache metrics.
2. **Set Realistic TTLs**: Balance freshness vs. cache load (e.g., 5–30 minutes for user profiles).
3. **Test Eviction Policies**: Simulate high-traffic scenarios to validate policies.
4. **Log Cache Misses**: Correlate with backend load to identify bottlenecks.
5. **Use Distributed Tracing**: Tools like Jaeger to trace cache requests across services.

---
**See Also**:
- [Redis Documentation: Debugging](https://redis.io/docs/references/cli/)
- [Memcached Best Practices](https://memcached.org/documentation.php)
- [Site Reliability Engineering: Caching](https://sre.google/sre-book/caching/)