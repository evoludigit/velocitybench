# **[Caching Patterns] Reference Guide**

---

## **Overview**
Caching Patterns optimize application performance by temporarily storing frequently accessed or computationally expensive data to reduce latency and load on underlying systems. This guide covers core caching concepts, implementation strategies, schema conventions, query examples, and related patterns for efficient data retrieval and retrieval optimization.

Caching eliminates redundant computations by storing results (e.g., database queries, API responses) in a fast-access layer (e.g., in-memory caches like Redis or local caches). Key benefits include:
- **Reduced response times** (milliseconds vs. seconds for database lookups).
- **Lower database/API load** (workload offloading).
- **Improved scalability** (reduced overhead during traffic spikes).

This pattern is critical for web applications, microservices, and real-time analytics. Proper design requires balancing cache invalidation, consistency, and resource usage.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example Use Case**                          |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Cache Layer**        | Storage mechanism (in-memory, disk-based, distributed) where data is temporarily stored.         | Redis, Memcached, local `HashMap`.            |
| **Cache Key**          | Unique identifier used to fetch/store cache entries (e.g., `user:123`).                       | `product_id:456`.                              |
| **Cache TTL (Time-to-Live)** | Duration (in seconds) before a cached entry expires (default: 300 sec).                     | TTL=86400 for session data.                   |
| **Cache Invalidation** | Mechanism to update or remove stale cached data (e.g., on write operations).                     | Invalidate cache after `user_update` API call. |
| **Cache Hit/Miss**     | - **Hit**: Data found in cache. <br> - **Miss**: Data not in cache; fetched from source.       | 90% cache hits, 10% misses.                   |
| **Cache Stampede**     | Concurrent requests for missing data, overwhelming the source system.                          | Mitigated via **pre-warming** or **random delays**. |
| **Cache Aside (Lazy Loading)** | Load data into cache only when requested.                                                       | Fetch from DB on `get_user(123)`.              |
| **Write-Through**     | Update cache *and* source simultaneously.                                                       | Sync user profile to DB *and* cache.          |
| **Write-Behind (Async)** | Update source first; cache updates asynchronously.                                             | Queue DB writes; update cache via background job. |
| **Multi-Level Caching** | Combine caches (e.g., in-memory + disk) for performance tiers.                                 | Local cache (fast) + Redis (persistent).      |
| **Cache Eviction Policy** | Rule to remove least-used items when cache is full (e.g., LRU, FIFO).                          | `LRU` evicts oldest unused item.               |

---

## **Schema Reference**
Below are common cache schemas and their use cases.

### **1. Key-Value Cache**
| **Field**     | **Type**       | **Description**                                                                 | **Example**                     |
|---------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `key`         | `string`       | Unique identifier for the cached entry.                                         | `"user:42"`                     |
| `value`       | `string/json`  | Serialized data (e.g., JSON, binary).                                           | `{"name": "Alice", "role": "admin"}` |
| `ttl`         | `integer`      | Time-to-live in seconds (0 = no expiry).                                         | `3600`                          |
| `timestamp`   | `timestamp`    | When the entry was last updated.                                                 | `2023-11-15T12:00:00Z`         |
| `version`     | `string`       | Optional: Track changes (e.g., `v1`, `v2`).                                     | `"v2"`                          |

**Use Case**: Storing user sessions, API responses, or small datasets.

---

### **2. Cache With Metadata (for Advanced Patterns)**
| **Field**       | **Type**       | **Description**                                                                 | **Example**                     |
|-----------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `key`           | `string`       | Unique identifier.                                                             | `"order:1001"`                  |
| `value`         | `string/json`  | Serialized payload.                                                             | `{"items": [...], "total": 99.99}` |
| `ttl`           | `integer`      | Expiry time.                                                                     | `7200`                          |
| `source`        | `string`       | Origin system (e.g., `db`, `microservice`).                                     | `"database"`                    |
| `last_updated`  | `timestamp`    | Timestamp of last write.                                                        | `2023-11-15T14:30:00Z`         |
| `dependencies`  | `array`        | Keys that must be invalidated if this cache entry changes.                      | `["user:100", "product:5"]`     |

**Use Case**: Tracking dependencies for **cache invalidation** or **conditional updates**.

---

### **3. Distributed Cache (Redis-like)**
| **Field**       | **Type**       | **Description**                                                                 | **Example**                     |
|-----------------|----------------|---------------------------------------------------------------------------------|---------------------------------|
| `namespace`     | `string`       | Group keys by context (e.g., `users`, `products`).                               | `"users:sessions"`              |
| `key`           | `string`       | Unique key within namespace.                                                   | `"sess_abc123"`                 |
| `value`         | `string/json`  | Serialized data.                                                               | `{"ip": "192.168.1.1"}`        |
| `ttl`           | `integer`      | Expiry in seconds.                                                             | `1800`                          |
| `hits`          | `integer`      | Cache hit count (for analytics).                                               | `42`                            |
| `last_access`   | `timestamp`    | When the key was last accessed.                                                | `2023-11-15T15:00:00Z`         |

**Use Case**: High-concurrency applications needing distributed caching (e.g., Redis).

---

## **Implementation Patterns**
### **1. Cache Aside (Lazy Loading)**
**Behavior**:
- Check cache first; if **miss**, fetch from source and populate cache.
- **No cache update on source writes** (caller must invalidate manually).

**Schema Example**:
```json
// Cache Key: "user:42"
{
  "value": {"name": "Alice", "email": "alice@example.com"},
  "ttl": 3600,
  "source": "database"
}
```

**Pseudocode**:
```python
def get_user(user_id):
    cache_key = f"user:{user_id}"
    cached_data = cache.get(cache_key)

    if not cached_data:
        # Cache miss → fetch from DB
        data = database.query(f"SELECT * FROM users WHERE id = {user_id}")
        cache.set(cache_key, data, ttl=3600)
    return cached_data
```

**Invalidation**:
- Caller must delete/expire the key after writes:
  ```python
  cache.delete("user:42")  # Manual invalidation
  ```

**Pros**:
- Simple to implement.
- No performance overhead on reads.

**Cons**:
- Risk of **cache stampede** (multiple misses under high load).
- Stale data if not invalidated properly.

---

### **2. Write-Through**
**Behavior**:
- Update **both cache and source** simultaneously.
- Ensures consistency but adds latency.

**Schema Example**:
```json
// Cache Key: "order:1001"
{
  "value": {"status": "shipped", "tracking": "ABC123"},
  "ttl": 86400,
  "version": "v1"
}
```

**Pseudocode**:
```python
def update_order(order_id, data):
    cache_key = f"order:{order_id}"

    # Update DB first (fail-safe)
    database.update(f"UPDATE orders SET status = '{data['status']}' WHERE id = {order_id}")

    # Write-through to cache
    cache.set(cache_key, data, ttl=86400)
```

**Pros**:
- Strong consistency (no stale data).
- Simple logic.

**Cons**:
- Slower writes (double writes).
- Overkill for low-frequency updates.

---

### **3. Write-Behind (Async)**
**Behavior**:
- Update **source first**; cache updates asynchronously (via queue or background job).
- Reduces write latency but risks temporary inconsistency.

**Schema Example**:
```json
// Cache Key: "order:1001"
{
  "value": {"status": "processed"},  // Stale until async job runs
  "pending_updates": [{"status": "shipped", "timestamp": "2023-11-15T16:00:00Z"}],
  "ttl": 3600
}
```

**Pseudocode**:
```python
def update_order(order_id, data):
    # Update DB immediately
    database.update(f"UPDATE orders SET status = 'processed' WHERE id = {order_id}")

    # Queue async cache update
    async_job_queue.enqueue(
        task="update_cache",
        args=[f"order:{order_id}", data],
        ttl=10  # Retry in 10 seconds if DB update fails
    )
```

**Pros**:
- Faster writes.
- Scales well for high-throughput systems.

**Cons**:
- Temporary inconsistency (reads may return stale data).
- Complexity in handling failures.

---

### **4. Cache Stampede Protection**
**Problem**: Thousands of requests hit a cache miss simultaneously, overwhelming the source.

**Solutions**:
1. **Pre-Warming**:
   - Pre-load data before expected traffic spikes.
   ```python
   cache.set("popular_product:123", product_data, ttl=3600)
   ```
2. **Random Backoff**:
   - Randomize delays for subsequent requests.
   ```python
   def get_with_random_delay(key):
       if cache.is_missing(key):
           time.sleep(random.uniform(0.1, 0.5))  # Random 100ms–500ms delay
           data = database.query(key)
           cache.set(key, data, ttl=3600)
       return cache.get(key)
   ```
3. **Two-Level Cache**:
   - Use a faster local cache + slower distributed cache.
   ```python
   if local_cache.is_missing(key):
       data = distributed_cache.get(key)
       if data:
           local_cache.set(key, data, ttl=3600)
   ```

---

## **Query Examples**
### **1. Basic CRUD Operations (Key-Value Cache)**
**Language**: Python (with `redis-py`)

```python
import redis

cache = redis.Redis(host='localhost', port=6379, db=0)

# Set (Write)
cache.set("user:42", '{"name": "Alice"}', ex=3600)  # TTL=3600 sec

# Get (Read)
user_data = cache.get("user:42")
print(user_data.decode())  # Output: {"name": "Alice"}

# Delete (Invalidate)
cache.delete("user:42")

# Check if key exists
exists = cache.exists("user:42")  # False
```

---

### **2. Conditional Cache Updates**
**Scenario**: Update cache only if the database value hasn’t changed.

```python
def safe_update_cache(key, data):
    current_db_value = database.query(key)
    if current_db_value != data:
        cache.set(key, data, ttl=3600)
        return True  # Updated
    return False  # No-op
```

---

### **3. Multi-Key Invalidation (Using Dependencies)**
**Schema**:
```json
// Cache Key: "user:42"
{
  "dependencies": ["addresses:42", "orders:42"],
  "ttl": 3600
}
```

**Pseudocode** (Invalidate all dependent keys):
```python
def invalidate_dependencies(key):
    entry = cache.get(key)
    if entry and "dependencies" in entry:
        for dep_key in entry["dependencies"]:
            cache.delete(dep_key)
```

---

### **4. Cache With Versioning**
**Schema**:
```json
// Cache Key: "product:123"
{
  "value": {"price": 9.99},
  "version": "v2",
  "created_at": "2023-11-15T10:00:00Z"
}
```

**Query** (Fetch only if version matches):
```python
def get_product_with_version(key, expected_version):
    entry = cache.get(key)
    if entry and entry["version"] == expected_version:
        return entry["value"]
    return None  # Stale or missing
```

---

## **Best Practices**
1. **Cache Granularity**:
   - Cache at the **right level** (e.g., cache entire objects, not individual fields).
   - Avoid over-fragmenting (e.g., caching each user field separately).

2. **TTL Strategy**:
   - Short TTL (e.g., 1 min) for **frequently changing** data.
   - Long TTL (e.g., 1 day) for **static** data (e.g., product catalogs).

3. **Cache Invalidation**:
   - Use **publish-subscribe** (e.g., Redis Pub/Sub) to notify caches of changes.
   - Example:
     ```python
     # After updating DB:
     redis.publish("invalidations", f"user:42")
     ```
   - Subscribers listen and invalidate keys:
     ```python
     def on_invalidation(message):
         key = message.decode()
         cache.delete(key)
     ```

4. **Monitoring**:
   - Track **hit/miss ratios** (aim for >90% hits).
   - Monitor **cache size growth** (evict old items if full).

5. **Fallback Mechanisms**:
   - If cache fails, **fall back to source** (e.g., circuit breaker pattern).

6. **Serialization**:
   - Use **efficient formats** (e.g., Protobuf, MessagePack) for large payloads.

---

## **Tools & Libraries**
| **Tool/Library**       | **Type**          | **Use Case**                                      | **Language Support**          |
|------------------------|-------------------|---------------------------------------------------|-------------------------------|
| Redis                 | Distributed Cache | High-performance key-value store.                 | Python, Java, Go, Node.js     |
| Memcached             | Distributed Cache | Low-latency caching for web apps.                 | C, Python, Java               |
| Guava Cache (Java)    | Local Cache       | In-memory caching for Java applications.          | Java                          |
| Caffeine (Java)       | Local Cache       | High-performance, load-based cache eviction.      | Java                          |
| Python `functools.lru_cache` | Local Cache  | Simple decorator-based caching.                   | Python                        |
| AWS ElastiCache       | Managed Cache     | Redis/Memcached hosted on AWS.                    | Multi-language                 |
| Hazelcast              | Distributed Cache | In-memory data grid for real-time processing.     | Java, .NET, Python            |

---

## **Anti-Patterns**
| **Anti-Pattern**          | **Description**                                                                 | **Fix**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Over-Caching**          | Caching every single query, bloating memory.                                   | Cache strategically (e.g., only expensive queries).                     |
| **No Cache Invalidation**| Forgetting to purge stale data, leading to inconsistent reads.               | Implement **write-back** or **event-based** invalidation.               |
| **Ignoring Cache Hit/Miss Ratios** | Optimizing blindly without metrics. | Monitor and adjust TTL/granularity based on usage.                    |
| **Cache Key Pollution**   | Using non-unique keys (e.g., `GET /products` → `key="products"`).       | Use **composite keys** (e.g., `product:123`).                           |
| **Single-Point Failure** | Relying on one cache server without redundancy.                              | Use **distributed caches** (Redis Cluster, Hazelcast).                |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                          |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **[Circuit Breaker](https://microservices.io/patterns/data/circuit-breaker.html)** | Prevents cascading failures by stopping cache calls when the source is down. | High-availability systems.           |
| **[Bulkhead](https://docs.microsoft.com/en-us/azure/architecture/patterns/bulkhead)** | Isolates cache requests to limit contention.                                  | Microservices under load.             |
| **[Retry](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)** | Retries failed cache fetches with backoff.                                   | Volatile network conditions.         |
| **[Idempotency](https://martinfowler.com/bliki/Idempotency.html)**              | Ensures repeated cache writes don’t cause duplicates.                         | Payment systems, order processing.   |
| **[Event Sourcing](https://martinfowler.com/eaaT/s.html)**                   | Appends changes as events; rebuilds cache from events.                        | Audit trails, complex state.         |
| **[Database Sharding](https://martinfowler.com/articles/sharding.html)**       | Distributes data across caches to scale horizontally.                        | Global applications.                 |

---

## **Further Reading**
- [Martin Fowler – Caching Patterns](https://martinfowler.com/eaaCatalog/cachingStrategies.html)
- [Redis Design Patterns](https://redis.io/topics/patterns)
- [Google’s Caching Best Practices](https://cloud.google.com/blog/products/devops-sre/google-cloud-operations-golden-rule-of-caching)
- [Amazon’s Caching Strategy](https://aws.amazon.com/blogs/architecture/key-patterns-for-caching-in-aws/)

---
**Note**: Adjust