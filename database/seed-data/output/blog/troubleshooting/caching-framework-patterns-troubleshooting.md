# **Debugging In-Memory Caching (Redis/Memcached) Patterns: A Troubleshooting Guide**
*(Focused on Redis and Memcached for production debugging)*

This guide helps identify, diagnose, and resolve common caching-related issues in distributed systems using Redis or Memcached. We’ll cover **performance bottlenecks, reliability failures, scaling problems, and integration errors**—all with **practical, actionable fixes**.

---

## **1. Symptom Checklist**
Before diving into debugging, verify if caching issues are present:

| **Symptom**                          | **Sub-Symptoms**                                                                 | **Likely Cause**                          |
|--------------------------------------|---------------------------------------------------------------------------------|-------------------------------------------|
| **High Latency**                     | Slower-than-expected API responses, cache misses despite high hit ratios       | Expired keys, stale data, misconfigured TTLs |
| **Cache Misses Spiking**             | Cache hit rate < 90% (expecting >95% for most workloads)                          | Inefficient key design, stale data, race conditions |
| **Unexpected Failures**              | App crashes, "Redis/Memcached server not found," connection resets               | Connection pool exhaustion, unhandled retries, misconfigured timeouts |
| **Memory Pressure**                  | High memory usage in Redis/Memcached, evictions, or OOM errors                   | Unbounded key growth, leaks, improper TTLs |
| **Data Inconsistency**               | Stale or missing data in cache vs. database                                   | Cache invalidation failures, write-through bypass |
| **Scaling Issues**                   | Poor read/write throughput under load                                           | Underpowered cluster, inefficient serialization, client bottleneck |
| **High CPU/Memory in Clients**       | Caching client processes consume excessive CPU/memory                            | Poorly optimized serialization, large payloads |
| **Network Saturation**               | High TCP/UDP traffic between apps & cache                                      | Unoptimized cluster networking, excessive chattiness |
| **Slow Cluster Replication**         | Lag between primary and replica nodes                                          | High write load, slow network, or improper replication settings |

---
---

## **2. Common Issues & Fixes**
### **2.1 Cache Miss Spikes: Why Hit Ratio Drops**
**Symptoms:**
- Sudden drop in cache hit ratio (e.g., 98% → 70%).
- Increased database load despite cache being enabled.

**Root Causes & Fixes:**
| **Cause**                          | **Diagnosis**                          | **Fix**                                                                 |
|------------------------------------|----------------------------------------|--------------------------------------------------------------------------|
| **Expiring Keys Too Early**        | `TTL` too low, keys expiring before reuse. | Increase TTL or use **LRU eviction** in Memcached/Redis.                |
| **Incomplete Cache Population**   | Keys written to cache but not read before expiry. | Use **write-behind + lazy loading** for critical keys.                  |
| **Key Prefix Collisions**          | Wildcard pattern (`KEYS *`) blocking eviction. | Avoid `KEYS *`, use **prefixes** (e.g., `user:123`).                     |
| **Stale Keys from Database Sync**  | Cache not invalidated on DB updates.    | Implement **cache-aside with TTL + event-based invalidation** (e.g., Redis Pub/Sub for DB changes). |

**Code Example: Exponential Backoff for Cache Misses**
```python
import redis
from time import sleep

r = redis.Redis(host='localhost', port=6379)

def get_with_cache(key, db_query_func, ttl=300):
    cached = r.get(key)
    if cached:
        return cached.decode()
    # Exponential backoff for DB fallback
    retry_delay = 1 << min(3, random.randint(0, 5))  # 1-8s max
    sleep(retry_delay)
    data = db_query_func()
    r.setex(key, ttl, data)
    return data
```

---

### **2.2 Connection Issues: "Connection Refused" or "Timeout"**
**Symptoms:**
- `redis.ReconnectionError`, `redis.ConnectionError`, or HTTP 503.
- Logs show `Connection refused` or `_socket.timeout`.

**Root Causes & Fixes:**
| **Cause**                          | **Diagnosis**                          | **Fix**                                                                 |
|------------------------------------|----------------------------------------|--------------------------------------------------------------------------|
| **Client Connection Pool Exhausted** | Too many open connections.            | Increase `pool_size` in Redis client (e.g., `pool_max_connections=100`). |
| **Redis/Memcached Unavailable**    | Node crashed or network partition.     | Enable **health checks** (e.g., `redis-cli ping` in monitoring).         |
| **Firewall/Network Blocking**      | Port `6379` (Redis) or `11211` (Memcached) blocked. | Whitelist ports in security groups; use **VPC peering/private IPs**.    |
| **Client Timeout Too Short**       | Default timeout too low (e.g., 0.1s).  | Set `socket_timeout=2` in Redis client config.                          |

**Code Example: Healthy Connection Handling**
```python
from redis.sents import Redis
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_redis_connection():
    try:
        return Redis(host='redis-host', socket_timeout=2)
    except Exception as e:
        logging.error(f"Redis connection failed: {e}")
        raise
```

---

### **2.3 Memory Overuse & Evictions**
**Symptoms:**
- Redis/Memcached reports `active_memory` > 90% of maxmem.
- `evicted_keys` spikes in logs.

**Root Causes & Fixes:**
| **Cause**                          | **Diagnosis**                          | **Fix**                                                                 |
|------------------------------------|----------------------------------------|--------------------------------------------------------------------------|
| **Unbounded Keys (e.g., session data)** | Keys grow indefinitely.           | Set **TTL** (e.g., `setex('user:123', 3600, serialized_data)`).       |
| **Large Payloads Stored**          | Keys >1MB stored (Redis default 5MB limit). | Compress data (`zlib`) or split into chunks.                         |
| **LRU Eviction Too Aggressive**    | Small frequently accessed keys evicted. | Adjust `maxmemory-policy` (e.g., `volatile-lru` for time-bound keys).    |

**Redis Config Fix:**
```ini
# Redis config
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used keys
```

**Code Example: Key Size Monitoring**
```python
def get_key_size(r: Redis, key: str) -> int:
    info = r.info('memory')
    key_size = int(info['keyspace_hits'])  # Approximate (use `object encoding`)
    return key_size
```

---

### **2.4 Data Inconsistency: Cache vs. DB Mismatch**
**Symptoms:**
- API returns stale data (e.g., `user:balance` in cache ≠ DB).
- Race condition: DB update → cache read → stale response.

**Root Causes & Fixes:**
| **Cause**                          | **Diagnosis**                          | **Fix**                                                                 |
|------------------------------------|----------------------------------------|--------------------------------------------------------------------------|
| **Lazy Cache Invalidation**        | Cache not updated on DB writes.       | Use **write-through** (sync DB → cache) or **event-driven** invalidation. |
| **TTL Too Long**                   | Key expires after DB update.          | Shorten TTL or use **conditional deletes** (`del_if_older_than`).      |
| **Network Partition**              | Primary Redis fails, replicas stale.  | Enable **Redis Sentinel** or **Cluster Mode**.                          |

**Code Example: Event-Driven Invalidation (Redis Pub/Sub)**
```python
import redis

r_pub = redis.Redis(host='pub-sub-host')
r_cache = redis.Redis(host='cache-host')

# Subscribe to DB change notifications
sub = r_pub.pubsub()
sub.subscribe('db_changes')
for msg in sub.listen():
    if msg['type'] == 'message':
        key = msg['data'].decode()
        r_cache.delete(key)  # Invalidate cache
```

---

### **2.5 Scaling Issues: Poor Throughput**
**Symptoms:**
- High latency under load (e.g., 100 QPS → 500ms responses).
- Redis/Memcached CPU spikes to 100%.

**Root Causes & Fixes:**
| **Cause**                          | **Diagnosis**                          | **Fix**                                                                 |
|------------------------------------|----------------------------------------|--------------------------------------------------------------------------|
| **Single Node Bottleneck**         | Redis/Memcached is a hotspot.         | Use **Redis Cluster** or **Memcached sharding**.                      |
| **Client Serialization Overhead**  | JSON/Protobuf conversion slow.         | Use **binary protocol** (e.g., `msgpack` instead of JSON).              |
| **High Chattiness**                | Too many small writes.                 | Batch writes (e.g., `MSET` instead of `SET` per key).                   |

**Redis Cluster Setup (Minimal Example)**
```bash
# Start 3 master nodes and replicas
redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
redis-cli --cluster create node1:6379 node2:6379 node3:6379 --cluster-replicas 1
```

**Code Example: Batch writes**
```python
def batch_set_keys(keys_data: list[tuple]):
    """Set multiple keys atomically."""
    r.mset(keys_data)  # Faster than N SET calls
```

---

## **3. Debugging Tools & Techniques**
### **3.1 Redis-Specific Tools**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `redis-cli --stat`     | Check CPU, memory, and latency metrics.                                   | `redis-cli --stat`                          |
| `redis-cli --latency`  | Identify slow commands (e.g., `>1ms`).                                    | `redis-cli --latency`                       |
| `redis-cli --bigkeys`  | Find large keys slowing down eviction.                                   | `redis-cli --bigkeys`                       |
| `redis-cli monitor`    | Real-time command logging.                                                | `redis-cli monitor`                         |
| **RedisInsight**       | GUI for cluster health, slow logs, and alerts.                            | Download from [RedisInsight](https://redisinsight.redis.com/) |

### **3.2 Memcached-Specific Tools**
| **Tool**               | **Purpose**                                                                 | **Example Command**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `memcached-tool`       | Check server stats (uptime, hits/misses).                                  | `memcached-tool -s 127.0.0.1:11211 stats`   |
| `sar`/`vmstat`         | Monitor system-level memory/CPU usage.                                     | `sar -r`                                    |
| **Tcmalloc Debugger**  | Track memory leaks in Memcached client.                                  | `--heap-check` flag in Memcached           |

### **3.3 Cross-Platform Debugging**
- **Prometheus + Grafana**: Monitor cache hit ratios, latency, and evictions.
  ```yaml
  # Prometheus alert for high miss ratio
  alert: HighCacheMissRatio
    if (cache_hits_total / cache_requests_total < 0.9)
    for: 5m
  ```
- **APM Tools (Datadog, New Relic)**: Trace cache hits/misses in application flow.
- **Log Analysis**: Filter logs for `KEYNOTFOUND`, `EXPIRED`, or `MOVED` errors.

---
---

## **4. Prevention Strategies**
### **4.1 Design-Time Best Practices**
1. **Key Naming Convention**:
   - Use **long prefixes** (e.g., `app:user:123`) to avoid wildcard collisions.
   - Avoid wildcard keys (`KEYS *`).

2. **TTL Management**:
   - Default TTL: **5-30 minutes** for high-churn data (e.g., sessions).
   - Infinite TTL: Only for **immutable** data (e.g., config).

3. **Clustering**:
   - **Redis Cluster**: Auto-shard data; use for >100GB memory.
   - **Memcached**: Shard manually (e.g., `crc32(key) % num_nodes`).

4. **Serialization**:
   - Use **binary formats** (`msgpack`, `protobuf`) instead of JSON.

### **4.2 Runtime Monitoring**
- **Set Up Alerts**:
  - Hit ratio < 90% → Alert.
  - Memory usage > 80% → Alert.
  - Eviction rate > 1000/hour → Alert.

- **Chaos Engineering**:
  - Simulate cache failures (e.g., kill Redis pods) to test fallbacks.

### **4.3 Code-Level Safeguards**
- **Defensive Programming**:
  - Always handle cache misses gracefully (fallback to DB).
  - Use **circuit breakers** (e.g., Hystrix) for cache unavailability.

- **Idempotent Writes**:
  - Ensure `SET`/`MSET` are retried on failure (e.g., with `RETRY` in Redis pipeline).

**Example: Idempotent Cache Write**
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
def set_key_safe(key, value):
    r.set(key, value)
```

---
---

## **5. Checklist for Fast Resolution**
1. **Check Hit Ratio**:
   - `redis-cli --stat | grep keyspace_hits` (Redis).
   - `memcached-tool stats` (Memcached).

2. **Inspect Logs**:
   - Look for `KEYNOTFOUND`, `EXPIRED`, or `MOVED` errors.

3. **Test Connectivity**:
   - `ping redis-host` (should respond in <10ms).
   - Check firewall rules (`tcpdump` if needed).

4. **Profile Slow Commands**:
   - Run `redis-cli --latency`; kill/optimize slow commands.

5. **Validate TTLs**:
   - `TTL user:123` (should match expected value).

6. **Scale Horizontally**:
   - If single node is saturated, add replicas or shards.

---
**Final Note**: Caching is **asynchronous**; assume it can fail. Design for failure by combining it with a **fallback mechanism** (e.g., database) and **monitoring**. For critical systems, pair caching with **write-ahead logs** (e.g., Redis RDB/AOF) to survive restarts.