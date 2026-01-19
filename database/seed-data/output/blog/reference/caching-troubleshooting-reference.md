# **[Pattern] Caching Troubleshooting – Reference Guide**

---

## **Overview**
Caching improves application performance by storing frequently accessed data in memory, reducing latency and database load. However, misconfigurations, stale data, or improper invalidation can degrade performance or cause inconsistencies. This guide covers common caching issues, diagnostic steps, and resolution strategies for in-memory caches (e.g., Redis, Memcached), CDNs, and application-level caches. Follow structured troubleshooting to identify bottlenecks, verify cache hits/misses, and ensure data freshness without overloading systems.

---

## **Implementation Details**
### **Key Concepts**
| Concept               | Definition                                                                                     | Example                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Cache Hit/Miss**    | **Hit**: Data retrieved from cache. **Miss**: Data fetched from storage (DB, API).           | Hit: `GET /user/123` returns cached response in 10ms. Miss: Cache returns `null`, DB query slows to 300ms. |
| **Cache Invalidation**| Removing stale data from cache to reflect backend changes.                                     | After `UPDATE user/123`, call `DEL user:123` in Redis.                                      |
| **Cache Stampede**    | Thundering herd problem: Many requests miss cache simultaneously, overwhelming the backend.   | High spike in DB queries when cache expires (`TTL=0`).                                        |
| **Cache Bypass**      | Requests skip cache due to misconfigured conditions (e.g., `Cache-Control: no-cache`).         | API endpoint ignores cache headers, forcing DB hits.                                          |
| **Cache Sharding**    | Partitioning cache across nodes to distribute load.                                          | Redis cluster splits keys by hash to avoid hotspots.                                        |
| **TTL (Time-to-Live)**| Time (seconds) cache entries remain valid before expiration.                                    | `SET key value EX 3600` stores data for 1 hour.                                              |
| **Cache-Warming**     | Preloading cache with expected high-demand data.                                             | Scheduled script to populate cache before traffic peaks.                                    |
| **Cache Layer**       | Where cache resides: **Application** (e.g., Guava), **CDN**, **Database** (e.g., PostgreSQL), or **External** (e.g., Redis). | Nginx CDN caches static assets; Redis caches API responses.                                  |

---

## **Schema Reference**
### **1. Cache Configuration Schema**
| Field               | Type     | Description                                                                                     | Example                                  |
|---------------------|----------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `cache_name`        | String   | Identifier for the cache layer (e.g., `redis-primary`, `cdn-edge`).                           | `redis-primary`                          |
| `provider`          | Enum     | `redis`, `memcached`, `nginx`, `varnish`, `cdn`, `application`.                               | `redis`                                  |
| `host`              | String   | Server address for cache backend.                                                              | `cache.example.com:6379`                 |
| `timeout`           | Integer  | Connection timeout in milliseconds.                                                            | `1000`                                   |
| `max_size`          | Integer  | Max items (Redis) or memory (Memcached) before eviction.                                      | `10000`                                  |
| `ttl_default`       | Integer  | Default TTL in seconds for uncached entries.                                                  | `300` (5 minutes)                        |
| `compression`       | Boolean  | Enable compression for large responses.                                                       | `true`                                   |
| `invalidation_strategy` | String | `lazy`, `aggressive`, or `manual` (e.g., pub/sub for event-based invalidation).          | `aggressive`                             |
| `hit_rate_threshold`| Float    | Minimum cache hit rate (%) to consider cache effective.                                       | `0.7` (70%)                              |
| `warmup_segments`   | Array    | URLs/keys to preload during startup.                                                          | `["/api/users", "/api/products"]`         |

---

### **2. Monitoring Metrics Schema**
| Metric               | Description                                                                                     | Tool Example                                      |
|----------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------|
| `cache_hits`         | Number of requests served from cache.                                                            | `redis-cli info keyspace`                         |
| `cache_misses`       | Number of requests fetching data from backend.                                                  | `APM: "CacheMiss"` (Datadog, New Relic)           |
| `evictions`          | Cache evicts items due to capacity limits.                                                      | `Memcached stats cache_hits cache_misses`        |
| `latency`            | Time (ms) to retrieve data from cache vs. backend.                                             | Prometheus: `cache_latency_seconds{type="hit"}`    |
| `hit_rate`           | `% hits / (hits + misses)`.                                                                     | `cache_hits / (cache_hits + cache_misses) * 100`   |
| `invalidation_errors`| Failed cache invalidation attempts.                                                             | Logs: `ERR: DEL failed on key user:123`            |
| `memory_usage`       | Cache memory consumption (bytes/MB).                                                           | `redis-cli info memory`                           |
| `stale_reads`        | Reads of expired/invalid cache entries.                                                        | Application logs: `Stale data returned for /api/x` |

---

## **Query Examples**
### **1. Diagnosing Cache Performance**
#### **Redis**
```bash
# Check cache hit/miss ratio
redis-cli info stats | grep "keyspace_hits" "keyspace_misses"
# Example output:
keyspace_hits:10000
keyspace_misses:2000

# Calculate hit rate
echo "scale=2; 10000/(10000+2000)" | bc  # Output: 83.33%

# Monitor latency (using `redis-cli --latency-history`)
redis-cli --latency-history 0
```
**Expected Output:**
```
Latency distribution:
   0-100µs: 95%
  100-500µs: 3%
  >500µs: 2% (potential issue)
```

#### **Memcached**
```bash
# Check stats (client-side)
memcached-tool -s 127.0.0.1:11211 stats
# Look for:
GET_HITS
GET_MISSES
```
**Thresholds:**
- If `GET_MISSES` > 20% of total requests → **Cache ineffectiveness**.

#### **CDN (Cloudflare/Nginx)**
```bash
# Cloudflare Dashboard: Analytics > Cache
curl "https://api.cloudflare.com/client/v4/zones/{zone_id}/analytics/cache" \
     -H "Authorization: Bearer YOUR_TOKEN"
```
**Key Metrics:**
- `cache_hit_ratio`: Target > 80%.
- `cache_origin_requests`: High values may indicate cache bypass or stale data.

---

### **2. Common Troubleshooting Queries**
#### **a) Identify Stale Cache Entries**
**Redis:**
```bash
# List keys matching a pattern (e.g., expired TTLs)
redis-cli keys "user:*" | xargs redis-cli ttl
# Output: `-2` = never expires, `-1` = expired.
```

**Nginx:**
```nginx
# Check cache status (enable `stub_status` in nginx.conf)
curl "http://localhost/nginx_status"
```
**Expected:**
```
Active connections: 100
Server accepts handled requests
Reading: 10 Writing: 5 Waiting: 84
Cache hits: 5000 Cache misses: 1000 (miss rate: 16.67%)
```

#### **b) Detect Cache Bypass**
**Check HTTP Headers:**
```bash
curl -v "https://example.com/api/users" | grep "Cache"
```
**Look for:**
- `Cache-Control: no-cache` or `max-age=0` → **Bypassing cache**.
- Missing `ETag` or `Last-Modified` → **No cache validation**.

#### **c) Investigate Cache Stampede**
**Tool:** Use APM (e.g., Datadog, New Relic) to trace:
```sql
-- SQL query to find stampede (sudden DB spikes):
SELECT * FROM metrics
WHERE timestamp BETWEEN '2023-10-01T12:00:00Z' AND '2023-10-01T13:00:00Z'
  AND metric = 'db.queries'
ORDER BY value DESC
LIMIT 10;
```
**Fix:** Implement **slotted expiration** (e.g., Redis `EXPIREAT` with random offsets).

---

### **3. Cache Invalidation**
#### **Event-Based (Pub/Sub)**
**Redis:**
```bash
# Publisher (on DB update):
redis-cli publish "user:updates" "{\"action\":\"delete\",\"key\":\"user:123\"}"

# Subscriber (cache invalidator):
redis-cli psubscribe "__keyevent@0__:expired"
```
**Python Example:**
```python
import redis
r = redis.Redis()
pubsub = r.pubsub()
pubsub.subscribe("user:updates")

for message in pubsub.listen():
    if message["type"] == "message":
        r.delete(message["data"]["key"])
```

#### **Manual (API Endpoint)**
```bash
# HTTP endpoint to invalidate cache
curl -X POST "http://localhost:3000/cache/invalidate?key=user:123"
```
**Backend Code (Python/Flask):**
```python
from flask import request
@app.route("/cache/invalidate", methods=["POST"])
def invalidate():
    key = request.args.get("key")
    cache.delete(key)
    return {"status": "success"}
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Cache-Aside (Lazy Loading)](https://microservices.io/patterns/data/cache-aside.html)** | Load data into cache only when missed.                                                          | General-purpose caching (e.g., Redis for API responses).                                        |
| **[Write-Through Cache](https://microservices.io/patterns/data/write-through-cache.html)**  | Update cache **and** DB simultaneously.                                                         | Strong consistency required (e.g., financial transactions).                                    |
| **[Write-Behind Cache](https://microservices.io/patterns/data/write-behind-cache.html)**   | Write to DB asynchronously; update cache later.                                                | High write-throughput systems (e.g., logs, analytics).                                        |
| **[Cache Stampede Protection](https://blog.jooq.org/2017/04/05/avoid-the-cache-stampede-anti-pattern/)** | Randomize TTLs to distribute load.                                                              | Avoid thundering herd during cache expiry.                                                     |
| **[CDN Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)**                  | Cache static assets at edge locations.                                                          | Global apps with static content (images, CSS, JS).                                             |
| **[Database Caching](https://www.percona.com/resources/videos/database-caching)**             | Use database built-in cache (e.g., PostgreSQL `pg_cache` extension).                           | Simplify caching for small-scale apps without external tools.                                  |
| **[Distributed Cache Sharding](https://redis.io/topics/sharding)**                         | Split cache across nodes (e.g., Redis Cluster).                                                 | Horizontal scaling for large datasets.                                                         |
| **[Cache Warming](https://dzone.com/articles/cache-warming)**                                | Preload cache with expected high-demand data.                                                   | E-commerce sites during sales events.                                                         |

---

## **Next Steps**
1. **Baseline Metrics**: Set up monitoring for `cache_hits`, `latency`, and `hit_rate`.
2. **Alerting**: Configure alerts for `hit_rate < 70%` or `memory_usage > 80%`.
3. **Testing**: Simulate cache invalidation under load (e.g., `locust` + Redis).
4. **Optimize**:
   - Reduce TTL for volatile data.
   - Use compression for large responses.
   - Implement cache warming for predictable traffic spikes.

---
**References:**
- [Redis Best Practices](https://redis.io/topics/best-practices)
- [CDN Caching Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [Cache Anti-Patterns](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch04.html)