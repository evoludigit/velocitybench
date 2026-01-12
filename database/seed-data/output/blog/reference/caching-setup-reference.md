# **[Pattern] Caching Setup Reference Guide**

---
## **Overview**
Caching reduces latency and load by storing frequently accessed data in fast, in-memory storage (e.g., Redis, Memcached) instead of repeatedly querying slower databases (e.g., PostgreSQL, MySQL). This guide outlines how to design, implement, and maintain caching layers in distributed systems, covering key concepts, configuration, query strategies, and best practices.

---

## **Key Concepts**
| Term               | Definition                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Cache Tier**     | A layer between the application and data source that stores precomputed or frequently accessed data. |
| **Cache Hit**      | When the cache returns requested data without querying the backend.                           |
| **Cache Miss**     | When the application queries the backend because the cache does not contain the requested data. |
| **TTL (Time-to-Live)** | Duration (in seconds) a cache entry remains valid before being evicted.                     |
| **Cache Invalidation** | Process of removing stale or expired data from the cache.                                       |
| **Cache-Warm-Up**  | Preloading data into the cache before peak traffic to reduce miss rates.                   |

---

## **Schema Reference**
### **Core Cache Setup Components**
| Component          | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **Cache Backend**  | Underlying storage (e.g., Redis, Memcached, local in-memory).
| **Cache Client**   | SDK/library (e.g., `redis-py`, `spring-cache`) for querying/storing data.                     |
| **Cache Key**      | Unique identifier for cached data (e.g., `user:123:profile`, `product:456:details`).           |
| **Cache Strategy** | Pattern used (e.g., **Cache-Aside**, **Write-Through**, **Write-Behind**).                      |
| **Eviction Policy** | Rules for removing stale/expired entries (e.g., LRU, FIFO, TTL-based).                        |
| **Monitoring**     | Tools to track hit/miss ratios (e.g., Prometheus, Grafana).                                  |

---

## **Implementation Details by Strategy**
### **1. Cache-Aside (Lazy Loading)**
- **How it works**: Data is cached only when accessed. Misses trigger backend queries.
- **Use case**: High-read, low-write workloads (e.g., user profiles, product listings).
- **Example Flow**:
  1. Application queries cache.
  2. If **miss**, fetch from DB, store in cache, return to app.
  3. Subsequent requests use cached data.

#### **Query Example (Pseudocode)**
```python
def get_user_profile(user_id):
    cache_key = f"user:{user_id}:profile"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data  # Cache hit
    else:
        data = database.query_user(user_id)  # Fallback to DB
        cache.set(cache_key, data, ttl=3600)  # Store with 1-hour TTL
        return data
```

---

### **2. Write-Through**
- **How it works**: Updates are written to both cache and DB simultaneously.
- **Use case**: Strong consistency required (e.g., financial transactions).
- **Tradeoff**: Higher write latency due to dual writes.

#### **Query Example**
```python
def update_user_profile(user_id, data):
    database.update_user(user_id, data)  # Update DB first (or simultaneously)
    cache_key = f"user:{user_id}:profile"
    cache.set(cache_key, data, ttl=3600)  # Sync cache
```

---

### **3. Write-Behind (Write-Back)**
- **How it works**: Updates are written to cache first; DB updates asynchronously (e.g., via queue).
- **Use case**: Low-latency writes acceptable (e.g., logging systems).
- **Risk**: Temporarily inconsistent data.

#### **Query Example**
```python
def update_user_profile(user_id, data):
    cache_key = f"user:{user_id}:profile"
    cache.set(cache_key, data, ttl=3600)  # Write to cache first
    async_tasks.push(db_update_task(user_id, data))  # Async DB update
```

---

## **Configuration Examples**
### **Redis Setup (Cache-Aside)**
```yaml
# redis.conf (or environment variables)
port: 6379
bind: 0.0.0.0
maxmemory 1gb
maxmemory-policy allkeys-lru  # Evict least recently used keys
```

**Python Client (Redis-Py)**
```python
import redis

cache = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
    max_connections=100  # Limit concurrency
)
```

---

### **Spring Cache (Java)**
```java
@Configuration
@EnableCaching
public class CacheConfig {
    @Bean
    public RedisCacheManager redisCacheManager(RedisConnectionFactory cf) {
        return RedisCacheManager.builder(cf)
                .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                        .entryTtl(Duration.ofHours(1)))
                .build();
    }
}
```

---

## **Query Examples**
### **Command-Line (Redis CLI)**
```bash
# Set a key (TTL=30s)
SET user:123:profile '{"name":"Alice"}' EX 30

# Get a key
GET user:123:profile

# Delete a key
DEL user:123:profile
```

### **Bulk Operations (Redis)**
```python
# MGET multiple keys efficiently
keys = ["user:1:profile", "user:2:profile"]
results = cache.mget(keys)  # Returns list of values
```

---

## **Best Practices**
1. **Key Design**:
   - Use a consistent naming convention (e.g., `namespace:id:entity`).
   - Avoid dynamic keys (e.g., `user_${random_id}`) that complicate invalidation.
2. **TTL Management**:
   - Set TTLs based on data volatility (e.g., 1 hour for news, 24h for static pages).
   - Use shorter TTLs for sensitive data (e.g., auth tokens).
3. **Invalidation**:
   - **Time-based**: Let TTL expire.
   - **Event-based**: Invalidate keys after DB updates (e.g., publish-subscribe pattern).
4. **Monitoring**:
   - Track hit/miss ratios (aim for >90% hits).
   - Monitor memory usage to avoid eviction storms.
5. **Fallbacks**:
   - Design for cache failures (e.g., retry with exponential backoff).

---

## **Related Patterns**
| Pattern               | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Bulkhead**          | Isolate cache clients to prevent cascading failures.                                          |
| **Circuit Breaker**   | Stop querying cache/DB after repeated failures.                                               |
| **Retry with Backoff** | Exponential backoff for transient cache failures.                                            |
| **Database Sharding**  | Distribute DB load to complement caching strategies.                                          |
| **Event Sourcing**    | Use for audit logs to rebuild cache state if corrupted.                                        |

---

## **Troubleshooting**
| Issue               | Cause                          | Solution                                                                 |
|---------------------|--------------------------------|--------------------------------------------------------------------------|
| High miss rate      | Cache too small/TTL too short. | Increase cache size or adjust TTL.                                       |
| Memory overload     | Too many keys or large values. | Compress values or use LRU eviction.                                     |
| Stale data          | Invalidation lag.              | Use event-based invalidation or shorter TTLs.                           |
| Cache client crash  | Unhandled exceptions.          | Implement retry logic and health checks.                                |

---
## **Tools & Libraries**
| Tool/Library         | Purpose                                                                                     |
|----------------------|---------------------------------------------------------------------------------------------|
| **Redis**            | In-memory key-value store with persistence options.                                        |
| **Memcached**        | Simple, multi-threaded cache (lower feature set than Redis).                                |
| **Spring Cache**     | Java annotations (`@Cacheable`, `@CacheEvict`) for Spring Boot applications.              |
| **Redis Insight**    | GUI for monitoring Redis caches.                                                          |
| **Prometheus + Grafana** | Track cache metrics (hits, misses, latency).                                           |

---
## **Example Architecture Diagram**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│  Application│───▶│  Cache (Redis)│───▶│  Application│
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                     ▲                       ▲
       │                     │                       │
       │                     │                       │
┌──────┴─────┐    ┌──────────┴───────┐    ┌──────────▼───────┐
│             │    │                     │    │                  │
│ Database   │    │  Cache Invalidation │    │  Fallback Logic  │
│ (PostgreSQL)│    │  (Pub/Sub)         │    │  (Retry/DB Query)│
│             │    │                     │    │                  │
└─────────────┘    └─────────────────────┘    └──────────────────┘
```
**Legend**:
- Blue: Normal flow (cache hit).
- Red: Cache miss → Fallback to DB.
- Green: Invalidation event (e.g., DB update triggers cache clear).