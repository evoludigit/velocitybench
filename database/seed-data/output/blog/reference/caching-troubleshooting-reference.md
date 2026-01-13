**[Pattern] Reference Guide: **Caching Troubleshooting**

---
### **Overview**
Caching is a critical performance optimization technique that stores frequently accessed data in memory to reduce latency and load on backend systems. However, improperly configured or malfunctioning caches can degrade application performance or return stale/inconsistent data. This guide provides a structured approach to diagnosing, validating, and resolving common caching issues across distributed systems (e.g., Redis, Memcached, CDNs, HTTP caches like Varnish or NGINX).

---
### **Key Concepts**
#### **1. Cache Layers**
Most systems employ a multi-tiered cache strategy:
| **Layer**         | **Purpose**                                                                 | **Common Tools**                     |
|--------------------|------------------------------------------------------------------------------|--------------------------------------|
| **Client-Side**    | Reduces round trips by storing responses locally (e.g., browser cache).      | Service Workers, HTTP `Cache-Control` |
| **Edge Cache**     | Caches content closer to users (reduces TTB from origin).                   | CDNs (Cloudflare, Fastly)            |
| **Application Cache** | Stores data in-memory for rapid retrieval within the app.              | Redis, Memcached                      |
| **Database Proxy** | Caches database query results to reduce load on the database.               | ProxySQL, PgBouncer                  |
| **Server-Side**    | Caches responses at the web server level.                                   | NGINX, Varnish                       |

#### **2. Cache Invalidation Strategies**
| **Strategy**       | **Use Case**                                                                 | **Pros**                          | **Cons**                          |
|--------------------|------------------------------------------------------------------------------|-----------------------------------|-----------------------------------|
| **Time-to-Live (TTL)** | Cache expires after a set duration.                                         | Simple to implement.              | Risk of stale data.               |
| **Event-Based**    | Invalidates cache on specific triggers (e.g., `POST /items/{id}`).           | Real-time consistency.            | Complex event handling.           |
| **Tag-Based**      | Uses metadata (e.g., tags) to invalidate related cache keys.                 | Granular control.                 | Requires tag management.          |
| **Write-Through**  | Updates cache *and* backend on writes.                                       | Strong consistency.              | Higher write latency.             |
| **Write-Behind**   | Updates cache *after* backend write (asynchronous).                         | Lower write latency.              | Potential stale reads.            |

#### **3. Cache Eviction Policies**
| **Policy**         | **Behavior**                                                                 | **Best For**                      |
|--------------------|------------------------------------------------------------------------------|-----------------------------------|
| **LRU (Least Recently Used)** | Removes least recently accessed items.                                      | Uniform access patterns.         |
| **LFU (Least Frequently Used)** | Evicts items accessed least often.                                          | Non-uniform access (e.g., logs).  |
| **FIFO (First-In-First-Out)** | Removes oldest items first.                                                 | Simple queues.                    |
| **All Keys**       | Evicts all keys when memory is full.                                         | Emergency cleanup.                |

---
### **Requirements & Preconditions**
Before troubleshooting:
1. **Monitoring Tools**: Access to APM (e.g., New Relic, Datadog) or cache-specific metrics (Redis CLI, Memcached stats).
2. **Logs**: Enable verbose logging for cache clients (e.g., `DEBUG` level in Redis client libraries).
3. **Reproduce Symptoms**: Isolate scenarios where caching fails (e.g., inconsistent reads, high miss rates).
4. **Permissions**: Admin access to cache servers and application codebase.

---
### **Schema Reference**
#### **Cache Metrics to Monitor**
| **Metric**               | **Description**                                                                 | **Tools to Check**                     |
|--------------------------|-------------------------------------------------------------------------------|----------------------------------------|
| `hit_rate`               | `(hits / (hits + misses)) * 100`; lower = cache inefficiency.               | Redis: `INFO stats`, Memcached: `stats` |
| `memory_usage`           | % of allocated memory in use.                                                 | Cache CLI, Prometheus (exported)      |
| `evictions`              | Number of items evicted due to capacity.                                      | Cache logs, Monitoring dashboards      |
| `latency`                | Average time to fetch cached vs. uncached data.                               | APM tools, `time` command (CLI)       |
| `cache_hit_time`         | Time taken to retrieve from cache (target: <10ms).                           | Custom instrumentation                 |
| `invalidation_lag`       | Time between data update and cache expiry/invalidation.                      | Correlate with DB logs                 |

#### **Common Cache Keys**
| **Pattern**              | **Example Key**                               | **Use Case**                          |
|--------------------------|-----------------------------------------------|---------------------------------------|
| **Object ID**            | `user:123`                                   | User profile data.                    |
| **Query-Based**          | `posts?user_id=123&limit=10`                 | Dynamic query results.                |
| **Tagged**               | `products:category=electronics`              | Bulk invalidation by tag.            |
| **Combined**             | `cache:user:123:notifications:unread`        | Composite keys for nested data.      |

---
### **Query Examples**
#### **1. Diagnosing Hit/Miss Rates (Redis)**
```bash
# Check cache stats
redis-cli INFO stats | grep -E 'keyspace_hits|keyspace_misses'

# Calculate hit rate
keyspace_hits=$(redis-cli INFO stats | grep keyspace_hits | awk '{print $2}')
keyspace_misses=$(redis-cli INFO stats | grep keyspace_misses | awk '{print $2}')
hit_rate=$(echo "scale=2; $keyspace_hits/($keyspace_hits+$keyspace_misses)*100" | bc)
echo "Cache Hit Rate: $hit_rate%"
```

#### **2. Identifying Stale Data (Memcached)**
```bash
# Check for stalled connections or slow queries
memcached-tool stats
```
**Expected Output**:
```
ITEM size    flags    timestamp    seconds    hits     misses   priority
...
```
- **Red Flag**: `misses >> hits` or `seconds` > 0.1s (indicates cache bypass or slow backend).

#### **3. Debugging Invalidations (Custom Cache)**
```python
# Example: Verify cache invalidation on write (Python/Redis)
import redis
r = redis.Redis()
def update_user(user_id, data):
    # Update DB
    db.update_user(user_id, data)
    # Invalidate cache
    r.delete(f"user:{user_id}")
    # Verify invalidation
    assert r.exists(f"user:{user_id}") == 0, "Cache not invalidated!"
```

#### **4. Profiling Latency (NGINX Cache)**
```bash
# Enable slow log for NGINX cache
nginx -V 2>&1 | grep "slow log"
# Check cache hit/latency stats
nginx -T | grep "cache"
```
**Expected Output**:
```
cache_hit_rate: 0.95
cache_max_size: 10g
cache_hit_time: 1.2ms
cache_miss_time: 45ms  # << High miss time suggests DB bottleneck
```

---
### **Troubleshooting Steps**
#### **1. Verify Cache is Active**
- **Symptom**: Unexpected DB queries or slow responses.
- **Checks**:
  - Confirm cache server is running (`redis-cli ping` → `PONG`).
  - Test connectivity from app server (`telnet <cache-host> 6379`).
  - Check for network firewalls blocking ports (6379 for Redis, 11211 for Memcached).

#### **2. Analyze Hit/Miss Ratio**
- **Symptom**: Unusually low hit rate (<70%).
- **Root Causes**:
  - **Overly aggressive TTL**: Set too short (e.g., 1 min for frequently accessed data).
  - **Skewed key distribution**: A few hot keys dominate cache (use `SLOWLOG` in Redis).
  - **Cold starts**: New keys not cached due to `write-behind` delays.
- **Fix**:
  - Adjust TTL based on access patterns (benchmarks with `redis-cli --stat`).
  - Use **local caching** for hot keys (e.g., `redis lpush` + `brpop` for queues).

#### **3. Detect Stale Data**
- **Symptom**: Inconsistent reads (e.g., `GET /users/1` returns old data).
- **Root Causes**:
  - Missing invalidation on writes.
  - Race condition during `DB write → cache update`.
  - TTL too long (> cache invalidation delay).
- **Fix**:
  - Implement **event-driven invalidation** (e.g., Redis Pub/Sub for DB triggers).
  - Use **cache stamps** (add `ETag` or version to keys, e.g., `user:123:v2`).

#### **4. Handle Eviction Storms**
- **Symptom**: Spikes in `evictions` metric, followed by latency.
- **Root Causes**:
  - Memory limits too low.
  - Memory leak in cache keys (e.g., unclosed connections).
- **Fix**:
  - Increase memory (`maxmemory` in Redis: `config set maxmemory 1gb`).
  - Optimize key patterns (shorter keys, compress large values with `snappy`).

#### **5. Debug Network/Serialization Issues**
- **Symptom**: Cache returns `nil` or corrupted data.
- **Root Causes**:
  - Serialization mismatches (e.g., JSON in client, Protobuf in cache).
  - Network timeouts (`socket hang up` in logs).
- **Fix**:
  - Standardize serialization (e.g., `pickle` for Python, `MessagePack` for cross-language).
  - Add retry logic with exponential backoff:
    ```python
    from redis.exceptions import ConnectionError
    max_retries = 3
    for attempts in range(max_retries):
        try:
            r.get(key)
            break
        except ConnectionError:
            time.sleep(2 ** attempts)
    ```

---
### **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Cache Aside (Lazy Loading)](https://martinfowler.com/eaaCatalog/cacheAside.html)** | Fill cache on miss, update on hit.                                          | High-read, low-write workloads.          |
| **[Write-Through](https://martinfowler.com/eaaCatalog/writeThroughCache.html)**     | Update cache *and* DB simultaneously.                                      | Strong consistency required.            |
| **[Write-Behind (Asynchronous)](https://martinfowler.com/eaaCatalog/writeBehindCache.html)** | Defer cache writes to DB.                                                | High-throughput writes (e.g., logs).    |
| **[Cache Stampeding](https://martinfowler.com/bliki/CacheStampede.html)**          | Block concurrent cache misses for the same key.                            | Prevent DB overload during hot-key access. |
| **[CDN Caching](https://martinfowler.com/bliki/CDNCaching.html)**                 | Offload static content to edge servers.                                   | Global low-latency distribution.        |

---
### **Anti-Patterns to Avoid**
1. **Over-Caching**: Cache too much (e.g., entire DB dump) → increases eviction risk.
2. **Static TTLs**: Ignoring access patterns (e.g., TTL=1h for a rarely accessed key).
3. **No Monitoring**: Blindly trusting cache without metrics (e.g., `hit_rate`).
4. **Ignoring Invalidation**: Assuming TTL alone is sufficient for consistency.
5. **Hot Keys**: Not handling skewed access (e.g., one key accounts for 90% of traffic).

---
### **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 | **Link**                                  |
|------------------------|----------------------------------------------------------------------------|-------------------------------------------|
| **Redis CLI**          | Debug keys, stats, and slow queries.                                       | [Docs](https://redis.io/commands/)        |
| **Memcached Tool**     | Analyze server stats and connections.                                     | [GitHub](https://github.com/memcached/memcached) |
| **Prometheus + Grafana** | Expose cache metrics for dashboards.                                      | [Export Redis Metrics](https://prometheus.io/docs/guides/redis_exporter/) |
| **New Relic APM**      | Track cache hits/misses in application traces.                              | [Cache Monitoring](https://newrelic.com/) |
| **Sentry**             | Capture cache-related errors (e.g., serialization fails).                 | [Docs](https://docs.sentry.io/)           |

---
### **Further Reading**
- [Redis Performance Guide](https://redis.io/topics/performance)
- [Memcached Best Practices](https://github.com/memcached/memcached/wiki/BestPractices)
- [CDN Caching Strategies](https://developer.cloudflare.com/learning/what-is-cdn/)
- [Event-Driven Architectures](https://martinfowler.com/articles/201701/event-driven.html) (for real-time invalidation)