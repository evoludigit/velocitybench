---

# **[In-Memory Caching (Redis/Memcached)] Reference Guide**

## **Overview**
In-memory caching leverages high-speed data stores (e.g., **Redis**, **Memcached**) to reduce database load and improve application performance by storing frequently accessed or computed data temporarily. This pattern addresses **latency reduction**, **scalability**, and **cost efficiency** for read-heavy workloads.

### **Key Benefits:**
- **Sub-millisecond response times** for cached data.
- **Reduced database load**, lowering operational costs.
- **Flexible data structures** (strings, hashes, lists, sets, etc.).
- **Persistence options** (optional disk backup in Redis).

### **Use Cases:**
- Session management.
- API response caching.
- Computation-heavy queries (e.g., report generation).
- Rate limiting and throttling.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                     | **Redis/Memcached Support** | **Example Key Structure**          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------|-------------------------------------|
| **Cache Key**               | Unique identifier for cached data (often combines namespace and ID).                                | Both                         | `user:profile:123`                  |
| **TTL (Time-to-Live)**      | Expiration time (seconds) to automatically evict stale entries.                                    | Both                         | `TTL: 3600` (1 hour)               |
| **Value**                   | Serialized data (JSON, Protocol Buffers, etc.) stored in memory.                                  | Both                         | `{"name": "Alice", "age": 30}`     |
| **Namespace**               | Logical grouping (e.g., `user`, `product`) to avoid key collisions.                                | Both                         | `user:` prefix                      |
| **Data Structure**          | Redis supports **hashtables, lists, sets, sorted sets**, while Memcached is key-value only.          | Redis: Full; Memcached: K/V | `HSET user:profile:123 name Alice`  |
| **Distributed Locks**       | Prevents race conditions during writes (e.g., Redis `SETNX`).                                      | Redis                         | `LOCK:user:123`                     |
| **Pub/Sub Channels**        | Real-time notifications (e.g., Redis channels).                                                   | Redis                         | `CHANNEL:orders`                    |
| **Pipeline Commands**       | Batch requests to reduce network roundtrips (Redis only).                                           | Redis                         | `MULTI → SET → GET → EXEC`          |

---

## **Implementation Best Practices**

### **1. Key Design**
- **Prefix keys** for logical separation (e.g., `user:`, `product:`).
- **Use hashes** for nested data (e.g., `user:profile:123` → `name`, `email`).
- **Avoid long keys** (>256 chars may cause compatibility issues).

**Example Key Patterns:**
| **Pattern**               | **Use Case**                              | **Example**                     |
|---------------------------|------------------------------------------|---------------------------------|
| `entity:type:id`          | Basic key structure                     | `user:session:abc123`           |
| `hash:entity:id:field`   | Nested attributes (Redis hashes)        | `user:123:name`                 |
| `list:entity:type`        | Ordered collections (e.g., recent items) | `recent:products:user1`         |

---

### **2. Value Serialization**
- **Redis:** Native support for **JSON, Protocol Buffers, or simple strings**.
- **Memcached:** Only supports **binary-safe strings** (serialize manually).
- **Avoid storing large objects** (>1MB may exceed memory limits).

**Example (JSON Serialization):**
```python
import json
key = "user:123"
value = json.dumps({"name": "Alice", "age": 30})
redis.set(key, value)
```

---

### **3. Cache Invalidation**
- **Explicit Invalidation:**
  Delete keys when data changes (e.g., after `user:update`).
  ```redis
  DEL user:123
  ```
- **Time-Based (TTL):**
  Set expiration to auto-delete after idle time.
  ```redis
  SET user:profile:123 "data" EX 3600  # Expires in 1 hour
  ```
- **Write-Through Caching:**
  Update cache **and** database simultaneously.

---

### **4. Performance Optimization**
- **Use `MGET`/`MSET`** for batch operations.
  ```redis
  MGET user:123 user:456  # Fetch multiple keys in one call
  ```
- **Leverage `PIPELINE`** for bulk commands (reduces latency).
- **Partition keys** for horizontal scaling (e.g., `user:1-1000:profile`).

---

## **Query Examples**

### **1. Basic Operations (Redis/Memcached)**
| **Operation**               | **Redis Command**       | **Memcached Command**  | **Use Case**                          |
|-----------------------------|-------------------------|------------------------|---------------------------------------|
| **Set a key-value pair**    | `SET key "value"`       | `set key value`        | Cache a user profile.                 |
| **Get a value**             | `GET key`               | `get key`              | Retrieve cached data.                 |
| **Set with TTL**            | `SET key "value" EX 60` | `set key value 0 60`   | Auto-expire after 60 seconds.         |
| **Delete a key**            | `DEL key`               | `delete key`           | Invalidate stale data.                |

---

### **2. Advanced Redis Features**
| **Operation**               | **Command**                     | **Example**                          | **Use Case**                          |
|-----------------------------|----------------------------------|--------------------------------------|---------------------------------------|
| **Hash Operations**         | `HSET`, `HGET`, `HGETALL`        | `HSET user:123 name "Alice"`         | Store nested user attributes.         |
| **Lists (Ordered Collections)** | `LPUSH`, `LPOP`, `LRANGE` | `LPUSH recent:items 1001`            | Track user activity.                  |
| **Sorted Sets**             | `ZADD`, `ZRANGE`                 | `ZADD ranks 100 user:123`            | Leaderboards.                         |
| **Pub/Sub**                 | `PUBLISH`, `SUBSCRIBE`           | `PUBLISH orders "new_order"`         | Real-time notifications.               |
| **Distributed Locks**       | `SETNX`, `WATCH`                 | `SETNX lock:user123 1 PX 10000`      | Prevent concurrent updates.            |

---

### **3. Memcached-Specific Queries**
```plaintext
# Set a key with flags (for serialization)
set user:123 0 3600 0 customflags "{\"name\":\"Alice\"}"

# Get with flags (validate serialization)
get user:123 flags
```

---

## **Error Handling & Edge Cases**

| **Scenario**               | **Solution**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Cache Miss (Stale Data)** | Fallback to database + cache update (cache-aside pattern).               |
| **Key Collision**           | Use namespaces (e.g., `app1:user:123`).                                    |
| **Memory Pressure**         | Monitor `redis-cli --latency`; evict old keys with `LRU`.                  |
| **Network Partitions**      | Use **Redis Cluster** for high availability.                               |
| **Malformed Data**          | Validate deserialized values (e.g., JSON parsing errors).                  |

---

## **Related Patterns**

1. **[Cache-Aside Pattern]**
   - **Description:** Fetch data from cache first; fall back to DB if missing. Update cache post-write.
   - **When to Use:** Read-heavy workloads with occasional writes.

2. **[Write-Through Caching]**
   - **Description:** Update cache **and** DB simultaneously to avoid stale data.
   - **When to Use:** Strong consistency requirements (e.g., financial systems).

3. **[Write-Behind Caching]**
   - **Description:** Delay cache updates until DB commit (for write-heavy workloads).
   - **When to Use:** High write-volume scenarios (e.g., IoT telemetry).

4. **[Cache Stampede Protection]**
   - **Description:** Prevent multiple threads from refetching expired data.
   - **Implementation:** Use **distributed locks** (Redis `SETNX`) or **stale-while-revalidate**.

5. **[Cache Warming]**
   - **Description:** Pre-load cache for predicted high-traffic events (e.g., Black Friday).
   - **Tools:** Cron jobs or event-driven scripts.

6. **[Eventual Consistency with CQRS]**
   - **Description:** Separate read/write models; sync cache via event sourcing (e.g., Kafka → Redis).

---

## **Tools & Libraries**
| **Language** | **Redis Client**       | **Memcached Client**     |
|--------------|------------------------|--------------------------|
| Python       | `redis-py`             | `pymemcache`             |
| Java         | `Jedis`, `Lettuce`     | `SpxMemcached`           |
| Node.js      | `ioredis`              | `memcached`              |
| Go           | `go-redis`             | `golem`                  |

---
**Example (Python with Redis):**
```python
import redis

r = redis.Redis(host='localhost', port=6379)

# Cache a value
r.set("user:123", '{"name": "Alice"}', ex=3600)

# Retrieve data
data = r.get("user:123")
user = json.loads(data.decode())
```

---
**Example (Memcached with Python):**
```python
import memcache

client = memcache.Client(['127.0.0.1:11211'])
client.set("user:123", '{"name": "Alice"}', time=3600)

data = client.get("user:123")
```

---
**Monitoring:**
- **Redis:** `redis-cli --stat`, Prometheus + Redis Exporter.
- **Memcached:** `stats`, `telnet` metrics.

---
**Security:**
- **Authenticate** Redis (`requirepass`).
- **Use TLS** for Memcached connections.
- **Rate-limit** cache writes to prevent abuse.