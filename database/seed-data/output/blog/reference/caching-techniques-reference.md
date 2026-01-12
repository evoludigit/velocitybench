# **[Pattern] Caching Techniques Reference Guide**

---

## **Overview**
Caching Techniques optimize performance by storing frequently accessed or computationally expensive data in fast-access memory (e.g., RAM, CDN cache, or in-memory databases). This reduces redundant processing, accelerates response times, and lowers backend load. Common use cases include:
- **APIs** (e.g., caching API responses to avoid repeated database queries).
- **Web applications** (e.g., caching rendered pages or static assets).
- **Microservices** (e.g., storing intermediate results of heavy computations).
- **Database interactions** (e.g., caching query results with TTL to prevent stale data).

Caching strategies vary by scope (client-side, server-side, distributed) and eviction policies (LRU, LFU, FIFO). Proper implementation requires balancing **hit rate** (cache effectiveness) and **invalidity** (ensuring freshness).

---

---

## **Schema Reference**

| **Component**          | **Description**                                                                                     | **Examples**                                                                                     | **Key Considerations**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Cache Types**        | Classifies caching based on location and purpose.                                                   | - **Client-side** (browser cache, service workers)<br>- **Server-side** (in-memory caches)<br>- **Distributed** (Redis, Memcached) | Scope impacts latency and consistency.                                                                  |
| **Cache Levels**       | Hierarchical caching tiers (e.g., edge cache → regional cache → backend).                            | - **Edge Cache** (CDN)<br>- **Local Cache** (browser)<br>- **Application Cache** (Redis)<br>- **Database Cache** (query cache) | Higher tiers reduce backend load but increase latency.                                                 |
| **Eviction Policies**  | Rules for removing cached items when space is full.                                                   | - **LRU (Least Recently Used)**<br>- **LFU (Least Frequently Used)**<br>- **TTL (Time-to-Live)**<br>- **FIFO (First-In-First-Out)** | Balances memory usage and hit rate.                                                                   |
| **Cache Invalidation** | Strategies to ensure stale data doesn’t propagate.                                                   | - **Time-based** (TTL)<br>- **Event-based** (cache flush on data change)<br>- **Write-through** (update cache + DB simultaneously) | Avoids inconsistency risks.                                                                        |
| **Data Serialization** | Formats for storing cached objects (speed vs. size tradeoff).                                        | - **JSON** (human-readable, flexible)<br>- **Protocol Buffers** (compact, fast)<br>- **MessagePack** (binary, efficient) | Affects cache read/write performance.                                                                  |
| **Cache Hit/Miss Metrics** | Performance indicators for cache effectiveness.                                                     | - **Hit Rate** (% successful cache retrievals)<br>- **Miss Rate** (% failed cache retrievals)<br>- **Cache Throughput** (operations/sec) | Monitor to tune cache configuration.                                                                 |
| **Distributed Cache Tools** | Systems for scalable, multi-node caching.                                                            | - **Redis** (in-memory, supports persistence)<br>- **Memcached** (simpler, no persistence)<br>- **Apache Ignite** (distributed, SQL support) | Choose based on scalability and persistence needs.                                                    |
| **Proxy Caching**      | Intermediate layer caching responses between clients and servers.                                   | - **Reverse Proxy** (Nginx, Varnish)<br>- **Forward Proxy** (Squid)                            | Reduces backend load but adds complexity.                                                              |
| **Query Caching**      | Caching database query results to avoid repeated execution.                                         | - **SQL Query Cache** (MySQL, PostgreSQL)<br>- **ORM Level** (Hibernate Second-Level Cache)     | Useful for read-heavy workloads with stable schemas.                                                    |

---

---

## **Implementation Details**

### **1. Cache Granularity**
Define the size of cached units to optimize tradeoffs between **hit rate** and **memory usage**:
- **Fine-grained** (e.g., cache individual API responses or database rows):
  - *Pros*: High hit rate for frequent small requests.
  - *Cons*: Higher memory overhead; more complex invalidation.
- **Coarse-grained** (e.g., cache entire HTML pages or aggregated data):
  - *Pros*: Reduces cache misses for complex queries.
  - *Cons*: Lower hit rate if data changes frequently.

**Example**:
```plaintext
# Fine-grained (API response)
Cache: GET /users/123 → { "id": 123, "name": "Alice" }

# Coarse-grained (rendered page)
Cache: /dashboard → Entire HTML response
```

---

### **2. Cache Invalidation Strategies**
| **Strategy**          | **Description**                                                                                     | **When to Use**                                                                                     | **Example**                                                                                             |
|-----------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| **Time-Based (TTL)**  | Auto-expire items after a set duration.                                                               | Data changes infrequently (e.g., product listings).                                                 | `SET user:123 name "Alice" EX 3600` (Redis: expires in 1 hour)                                        |
| **Event-Based**       | Invalidate cache when source data changes (e.g., via pub/sub or database triggers).                 | Real-time systems (e.g., user profiles).                                                           | Delete cache key on `USER_UPDATED` event.                                                              |
| **Write-Through**     | Update cache **and** database simultaneously.                                                        | Strong consistency required (e.g., financial transactions).                                       | After DB update: `UPDATE cache AND DB`.                                                                |
| **Write-Back**        | Update cache first; sync to DB later (risky for consistency).                                       | Low-latency reads, acceptable eventual consistency (e.g., analytics).                              | Cache update → Async DB write.                                                                        |
| **Lazy Loading**      | Populate cache only when accessed (reduces initial load).                                           | Cold-start scenarios (e.g., serverless functions).                                                   | Cache populated on first request; subsequent requests serve from cache.                               |
| **Push/Pull Invalidation** | Cache invalidates manually (push) or checks source (pull).                                        | Hybrid approaches for partial freshness.                                                           | Pull: Check DB version on cache read.                                                                   |

---

### **3. Cache Coherence**
Ensure consistency across distributed caches:
- **Stale-Read Permissive**: Accept occasional stale data (e.g., news articles).
- **Stale-Read Avoidance**: Use TTL or versioning to minimize stale reads.
- **Strong Consistency**: Require cache invalidation on every write (expensive but precise).

**Example (Redis Cluster Coherence)**:
```plaintext
# Use Redis Transactions to ensure atomicity
MULTI
SET user:123 name "Alice"
DEL user:123:cache_v1
EXEC
```

---

### **4. Cache Warm-Up**
Pre-load cache during low-traffic periods to reduce latency spikes:
```python
# Pseudocode for cache warm-up (e.g., in a startup script)
def warm_up_cache():
    popular_items = db.query("SELECT * FROM items WHERE views > 1000 LIMIT 100")
    for item in popular_items:
        cache.set(f"item:{item.id}", item, ttl=3600)
```

---

### **5. Monitoring and Metrics**
Track cache performance with these Key Performance Indicators (KPIs):
| **Metric**            | **Tooling**                          | **Thresholds**                          |
|-----------------------|---------------------------------------|------------------------------------------|
| **Cache Hit Ratio**   | Prometheus, Datadog                   | >90% ideal; <70% indicates tuning needed  |
| **Miss Rate**         | Custom logging                        | <10% for fine-grained caches            |
| **Latency (Cache vs. DB)** | APM tools (New Relic) | Cache: <50ms; DB: >100ms (problem)    |
| **Cache Size**        | Redis `INFO memory`                   | Max 70% of available RAM                 |
| **Eviction Rate**     | Application logs                      | High rate → adjust TTL or eviction policy |

**Example Query (PromQL for Hit Ratio)**:
```plaintext
cache_hits / (cache_hits + cache_misses) > 0.9
```

---

---

## **Query Examples**

---

### **1. Setting and Getting Data (Redis)**
```bash
# Set a value with TTL (5 minutes)
SET user:123 name "Alice" EX 300

# Get the value
GET user:123:name

# Increment a counter (atomic operation)
INCR user:123:visit_count
```

---

### **2. Cache-aside (Database-First) Pattern**
```python
# Pseudocode
def get_user(user_id):
    cache_key = f"user:{user_id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data  # Cache hit
    else:
        user_data = db.query(f"SELECT * FROM users WHERE id = {user_id}")
        cache.set(cache_key, user_data, ttl=3600)  # Cache miss → populate cache
        return user_data
```

---

### **3. Write-Through Pattern**
```python
def update_user(user_id, data):
    # Update database
    db.execute(f"UPDATE users SET name='{data.name}' WHERE id={user_id}")

    # Update cache simultaneously
    cache.set(f"user:{user_id}:name", data.name, ttl=3600)
```

---

### **4. Query Caching (ORM Example: Django)**
```python
# Enable cache in Django ORM settings.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}

# Cache a query result (TTL: 60 seconds)
from django.core.cache import cache

queryset = cache.get("expensive_query")
if not queryset:
    queryset = MyModel.objects.filter(status="active").order_by("created_at")
    cache.set("expensive_query", queryset, 60)
```

---

### **5. CDN Cache Headers (Nginx)**
```nginx
location /static/ {
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
    proxy_pass http://backend;
}
```

---

### **6. Cache Busting**
Prevent stale cached assets by appending version hashes:
```html
<!-- Static file with cache-busting -->
<script src="/js/app-v2.abc123.js"></script>
```
**Automate with build tools (e.g., Webpack)**:
```javascript
// webpack.config.js
output {
    filename: '[name]-[contenthash].js',
}
```

---

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **Relation to Caching**                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Lazy Loading**          | Defer loading of non-critical resources until needed.                                               | Complements caching by reducing initial load time.                                                  |
| **Paging/Offset Limiting** | Split large datasets into smaller chunks (e.g., `LIMIT 10 OFFSET 0`).                              | Reduces memory usage for cached paginated results.                                                  |
| **Database Indexing**     | Optimize query performance with indexes.                                                           | Caching query results can further reduce DB load for indexed queries.                                |
| **Asynchronous Processing** | Offload task execution to background workers (e.g., Celery).                                       | Cache intermediate results of async tasks to avoid reprocessing.                                    |
| **Rate Limiting**         | Throttle requests to prevent abuse.                                                                 | Caching rate-limit decisions reduces DB queries for `/rate_limit` checks.                            |
| **Event Sourcing**        | Store state changes as a sequence of events.                                                        | Cache event streams for real-time updates (e.g., Kafka + Redis).                                    |
| **Circuit Breaker**       | Fail fast and recover gracefully for dependent services.                                             | Cache service responses to avoid repeated failures.                                                 |
| **Retry with Backoff**    | Exponential backoff for transient failures.                                                          | Combine with caching to avoid repeated retries for the same failure.                                 |
| **Compression**           | Reduce payload size (e.g., gzip, Brotli).                                                          | Compressed cache responses save memory and bandwidth.                                                |

---

---

## **Best Practices**
1. **Start Simple**: Use a single cache layer (e.g., Redis) before adding complexity.
2. **Monitor Aggressively**: Alert on high miss rates or cache evictions.
3. **Set Realistic TTLs**: Balance freshness with cache pressure.
   - *Short TTL*: Lower miss rate but more DB load.
   - *Long TTL*: Higher miss rate but less DB load.
4. **Use Compression**: Reduce cache size for text/data-heavy payloads.
5. **Avoid Over-Caching**: Don’t cache data that changes frequently or is unique per request.
6. **Secure Your Cache**:
   - Use authentication for distributed caches.
   - Encrypt sensitive cached data.
7. **Test Invalidation**: Simulate cache storms (e.g., bulk updates) to validate invalidation.
8. **Document Cache Dependencies**: Note which API endpoints or DB tables rely on cached data.

---

---
**Note**: Adjust TTLs, eviction policies, and cache sizes based on workload characteristics. Benchmark with production-like data.