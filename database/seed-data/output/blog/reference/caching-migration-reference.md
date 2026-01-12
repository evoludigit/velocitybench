---
# **[Pattern] Caching Migration: Reference Guide**

---
## **Overview**
The **Caching Migration** pattern addresses performance bottlenecks in systems where data retrieval from a primary database is slow or resource-intensive. This pattern gradually shifts read operations from the underlying database to a cache layer (e.g., Redis, Memcached) while ensuring data consistency. Key benefits include reduced latency, lower database load, and improved scalability. The migration is phased to minimize risk, balancing performance gains with data accuracy. Common use cases include e-commerce product listings, social media feeds, or any high-traffic application where stale data is tolerable for short intervals.

---
## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Example**                          |
|------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------|
| **Cache Invalidation** | Process of updating cached data when the source changes.                                           | Deleting a Redis key after DB update. |
| **Cache Stampede**     | Multiple concurrent requests triggering recaching when cache expires.                            | 1000 users hitting a cache miss.     |
| **TTL (Time-To-Live)** | Duration after which cached data expires.                                                          | `ttl=60` (1 minute).                 |
| **Read-Through Cache** | Cache fetches data from the DB if missing, then stores it.                                         | API response checks cache → DB.      |
| **Write-Behind Cache** | Cache updates asynchronously after DB writes.                                                     | DB commit → background cache update.  |
| **Cache Partitioning** | Splitting cache data across multiple instances (e.g., by shard/region).                         | Regionalized product listings.        |

---

## **Implementation Details**
### **1. Phased Migration Strategy**
Avoid abrupt cutovers by using the **double-write pattern**:
1. **Phase 1: Cache on Read** – Serve cached data when possible; fall back to DB.
2. **Phase 2: Cache on Write** – Update cache asynchronously after DB writes.
3. **Phase 3: Full Migration** – Redirect all reads to cache; monitor for drift.

**Mitigation for Phase 1:**
- Use **time-based TTLs** (e.g., 5-minute expiry) for critical data.
- Implement **cache-aside (Lazy Loading)** for sporadic access patterns.

### **2. Cache Invalidation Strategies**
| **Strategy**               | **Use Case**                                      | **Implementation**                                                                 |
|----------------------------|---------------------------------------------------|-------------------------------------------------------------------------------------|
| **Time-Based**             | Data rarely updated (e.g., product categories).     | Set `TTL=3600` (1 hour).                                                         |
| **Event-Based**            | Real-time data (e.g., user sessions).              | Pub/Sub: Trigger cache invalidation on DB changes.                                |
| **Tag-Based**              | Grouped invalidation (e.g., "products:electronics"). | Update all keys tagged `products:electronics`.                                     |
| **Dependency-Based**       | Cached data derived from other data.                | Invalidate child cache when parent data changes (e.g., user profile → posts).     |
| **Manual (Admin)**         | Bulk operations (e.g., database resets).           | API endpoint to flush cache keys.                                                 |

### **3. Handling Cache Stampedes**
Deploy **locking mechanisms** or **snowflake patterns**:
- **Locking**: Use a distributed lock (e.g., Redis `SETNX`) to serialize recaching.
- **Snowflake Pattern**: Randomly delay recaching on cache miss to smooth load.
  ```python
  if cache_miss:
      delay = random.uniform(0, 0.1) * 1000  # 0–100ms delay
      time.sleep(delay / 1000)
      fetch_and_store_data()
  ```

### **4. Consistency Trade-offs**
- **Strong Consistency**: Cache invalidated immediately (high latency).
- **Eventual Consistency**: Accept temporary stale data (lower latency).
- **Read-Your-Writes**: Ensure users see their own recent changes (e.g., via `version` fields).

---
## **Schema Reference**
### **Core Tables/Entities**
| **Entity**       | **Fields**                          | **Purpose**                                                                       | **Cache Key Format**               |
|------------------|-------------------------------------|-----------------------------------------------------------------------------------|-------------------------------------|
| `Products`       | `id`, `name`, `price`, `stock`      | Product listings.                                                               | `product:{id}`                      |
| `Users`          | `id`, `username`, `last_login`      | User profiles.                                                                    | `user:{id}`                         |
| `Orders`         | `id`, `user_id`, `status`, `items`  | Order history.                                                                  | `user:{user_id}:orders` (partitioned)|
| `Session`        | `session_id`, `user_id`, `expiry`   | User sessions.                                                                   | `session:{session_id}`              |

**Example Cache Key Patterns:**
- **Simple Key**: `product:123` (single ID).
- **Composite Key**: `user:456:posts:recent` (nested structure).
- **Wildcards**: `products:electronics:*` (tag-based invalidation).

---
## **Query Examples**
### **1. Read-Through Cache (Pseudocode)**
```python
def get_product(id):
    cache_key = f"product:{id}"
    data = cache.get(cache_key)
    if not data:  # Cache miss
        data = db.query("SELECT * FROM Products WHERE id=? LIMIT 1", id)
        cache.set(cache_key, data, ttl=3600)  # Cache hit on next request
    return data
```

### **2. Write-Behind Cache (Async Task)**
```python
def update_product(id, data):
    # 1. Update DB immediately
    db.update("UPDATE Products SET ... WHERE id=?", id)

    # 2. Queue cache update (background task)
    task_queue.enqueue("invalidate_product_cache", id)
```

### **3. Event-Based Invalidation (Pub/Sub)**
**Publisher (DB Trigger):**
```sql
-- PostgreSQL trigger for invalidating product cache on update
CREATE TRIGGER product_cache_invalidator
AFTER UPDATE ON Products
FOR EACH ROW EXECUTE FUNCTION invalidate_product_cache();
```

**Subscriber (Cache Layer):**
```python
def invalidate_product_cache(payload):
    product_id = payload["id"]
    cache.delete(f"product:{product_id}")
    # Invalidate related keys (e.g., aggregations)
    cache.delete(f"product:{product_id}:stats")
```

### **4. Cache Partitioning (Sharding)**
```python
def get_user_posts(user_id, limit=10):
    cache_key = f"user:{user_id}:posts"
    posts = cache.get(cache_key)
    if not posts:
        posts = db.query(
            "SELECT * FROM Posts WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
            user_id, limit
        )
        cache.set(cache_key, posts, ttl=60)  # Shorter TTL for freshness
    return posts
```

---
## **Error Handling & Monitoring**
| **Scenario**               | **Action**                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|
| **Cache Serious Failure**   | Fall back to DB-only mode; log errors (e.g., `cache_miss_rate > 90%` for 5 mins).             |
| **DB Failure**              | Serve stale cache data; alert operators.                                                      |
| **Cache Invalidation Lag**  | Use `version` fields to detect stale reads (e.g., `IF (cache_version < db_version) REFRESH`). |
| **Hot Keys**                | Monitor cache hit ratios; redistribute keys if skewed.                                         |

**Key Metrics to Track:**
- `cache_hit_ratio` (target: >90%).
- `cache_latency` (P99 < 10ms).
- `invalidations_per_second` (spikes indicate misconfigurations).
- `db_reads_ignored` (cache served all requests).

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                               | **When to Use**                                      |
|---------------------------|-----------------------------------------------------------------------------------------------|------------------------------------------------------|
| **[CQRS](https://microservices.io/patterns/data/cqrs.html)** | Separate read/write models for performance.                                                   | High-write, high-read workloads.                     |
| **[Event Sourcing](https://martinfowler.com/eaaT.html)** | Store state as a sequence of events for auditability.                                          | Financial systems, audit trails.                     |
| **[Cache-Warming](https://www.benkehoe.com/blog/2018/cache-warming/)** | Pre-load cache for predictable traffic spikes.                                              | Scheduled events (e.g., Black Friday sales).         |
| **[Materialized Views](https://www.postgresql.org/docs/current/materialized-views.html)** | Pre-computed DB aggregates for faster reads.                                                 | Dashboards, reporting.                                |
| **[Bulkhead Pattern](https://martinfowler.com/bliki/BulkheadPattern.html)** | Isolate cache layer from DB failures.                                                          | Critical systems with strict SLA (e.g., payment processing). |

---
## **Anti-Patterns to Avoid**
1. **Unbounded Cache Retention**: Never use `TTL=0` for frequently updated data (e.g., real-time feeds).
2. **Ignoring Cache Stampedes**: Without mitigation, cache misses can overwhelm the DB.
3. **Over-Caching**: Cache irrelevant data (e.g., admin-only queries).
4. **Poor Key Design**: Wildcard keys (`products:*`) reduce cache efficiency.
5. **No Fallback**: Always define a DB fallback for cache failures.

---
## **Tools & Technologies**
| **Component**       | **Options**                                                                                     | **Best For**                          |
|---------------------|-------------------------------------------------------------------------------------------------|---------------------------------------|
| **Cache Layer**     | Redis, Memcached, Hazelcast, Couchbase.                                                          | High-throughput, low-latency needs.   |
| **Invalidation**    | Redis Pub/Sub, DB triggers, application events.                                                 | Event-driven systems.                 |
| **Monitoring**      | Prometheus + Grafana, Datadog, New Relic.                                                       | Observability.                        |
| **Asynchronous**    | Celery, Kafka, RabbitMQ.                                                                        | Decoupled cache updates.              |
| **ORM/Query Layer** | Django ORM (with `@cached`), SQLAlchemy Cache Extension, TypeORM.                              | ORM-heavy applications.               |