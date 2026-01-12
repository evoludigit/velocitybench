# **[Pattern] Reference Guide – *Caching Standards***

---
## **1. Overview**
The **Caching Standards** pattern defines consistent rules, structures, and best practices for designing, implementing, and maintaining caching layers in distributed systems. It ensures predictable performance, reduces redundant computations, and minimizes resource consumption while maintaining data freshness. This pattern applies to in-memory caches (e.g., Redis, Memcached), CDNs, application-level caches (e.g., Guava Cache, Caffeine), and database query caching. Key benefits include **reduced latency**, **lower server load**, and **scalability** under heavy traffic.

The pattern enforces **standardized key formats**, **TTL (Time-To-Live) policies**, **cache invalidation strategies**, and **fault tolerance mechanisms**. It also addresses trade-offs between **provisioning overhead** and **hit/miss ratios** to optimize caching efficiency.

---

## **2. Schema Reference**

### **2.1 Core Components**
| **Component**          | **Description**                                                                                     | **Example Value**                          | **Required/Optional** |
|-------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|------------------------|
| **Cache Scope**         | Defines when the cache is applied (e.g., request-level, session-based, global).                    | `request`, `session`, `global`             | Required               |
| **Cache Key**           | Unique identifier for cache entries (must be deterministic and collision-resistant).                | `user:123:profile:2024-05-20T12:00:00Z`   | Required               |
| **Cache Value**         | Serialized data stored in cache (supports JSON, protobuf, Avro).                                   | `{"id":123, ...}` (serialized)             | Required               |
| **Time-To-Live (TTL)**  | Duration (in seconds) before cache expires (default: `300` sec).                                    | `3600` (1 hour)                             | Optional (default)     |
| **Cache Hit Policy**    | Rules for handling cache hits (e.g., `use`, `skip`, `fallback`).                                  | `use`                                      | Optional (default)     |
| **Cache Miss Policy**   | Rules for handling cache misses (e.g., `compute`, `return-empty`, `stub`).                         | `compute`                                  | Optional (default)     |
| **Invalidation Trigger**| Events that invalidate cache (e.g., `write`, `delete`, `scheduled`).                               | `write`                                    | Optional               |
| **Cache Region**        | Logical grouping of related cache entries (e.g., `user_profiles`, `product_catalog`).             | `user_profiles`                             | Optional               |
| **Cache Provider**      | Technology used (e.g., `Redis`, `Memcached`, `Guava`).                                            | `Redis`                                    | Required               |
| **Fallback Mechanism**  | Behavior when cache fails (e.g., `skip`, `retry`, `circuit-break`).                                | `retry:3` (retry 3 times)                  | Optional               |

---

### **2.2 Key Schema Fields Explained**
#### **Cache Key**
- **Format**: Must include:
  - **Entity type** (e.g., `user`, `product`).
  - **Identifier** (e.g., `id:123`).
  - **Versioning** (if applicable, e.g., `:v2`).
  - **Timestamp** (for time-sensitive data, e.g., `:2024-05-20`).
  - **Optional qualifiers** (e.g., `:lang=en` for localized data).
- **Example**:
  ```
  user:123:profile:v2:2024-05-20
  ```
- **Validation**:
  - Avoid special characters (use `-` or `_`).
  - Limit length to **255 chars**.
  - Use **SHA-256 hashes** for sensitive keys.

#### **Time-To-Live (TTL)**
- **Defaults**:
  - **Short-lived** (e.g., `60` sec): High-frequency data (e.g., session tokens).
  - **Medium-lived** (e.g., `3600` sec): User profiles, product listings.
  - **Long-lived** (e.g., `86400` sec): Static assets, configuration.
- **Dynamic TTL**: Adjust based on data volatility (e.g., TTL = `300 + (last_write_ms / 1000)`).

#### **Invalidation Trigger**
| **Trigger**      | **Description**                                                                                     | **Example Use Case**                     |
|-------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| `write`           | Invalidate on entity modification.                                                                  | User edits profile → cache for `user:123` invalidated. |
| `delete`          | Invalidate on entity removal.                                                                        | Product deleted → cache for `product:456` cleared. |
| `scheduled`       | Invalidate at a fixed interval (e.g., daily).                                                      | Cache for `news_headlines` refreshed at 00:00 UTC. |
| `dependency`      | Invalidate if dependent data changes (e.g., cache for `order:789` if `user:123:wallet` updates). | Order totals recalculated.                |
| `event-stream`    | Invalidate via event-driven systems (e.g., Kafka Pub/Sub).                                         | New product added → cache for `catalog` invalidated. |

#### **Fallback Mechanism**
| **Mechanism**     | **Behavior**                                                                                       | **Use Case**                              |
|-------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| `skip`            | Return cached value even if stale (no fallback computation).                                      | Low-cost read-only operations.            |
| `retry`           | Retry cache operation `N` times before failing.                                                  | Temporary cache outages.                 |
| `circuit-break`   | Fail fast if cache errors persist (e.g., Redis down).                                            | High-availability scenarios.              |
| `stub`            | Return a placeholder value (e.g., empty object) while reloading.                                  | Graceful degradation.                    |

---

## **3. Query Examples**
### **3.1 Cache Lookup (Read)**
```sql
-- Standard cache GET request (key = 'user:123:profile:v2')
GET user:123:profile:v2
```

**Response**:
```json
{
  "status": "HIT",
  "key": "user:123:profile:v2",
  "value": "{\"id\":123,\"name\":\"Alice\"}",
  "ttl": 3600
}
```

### **3.2 Cache Write (Put/Set)**
```sql
-- Set with TTL=7200 seconds
SET user:123:profile:v2 "{\"id\":123,\"name\":\"Alice\"}" TTL 7200
```

**With Invalidation Trigger**:
```json
// Invalidate cache for user:123:profile when user data updates
{
  "operation": "INVALIDATE",
  "key": "user:123:profile",
  "trigger": "write",
  "version": "v2"
}
```

### **3.3 Conditional Cache Update (If-Not-Exists)**
```sql
-- Only update if key doesn't exist (atomic operation)
SET user:124:profile:v2 "{\"id\":124,\"name\":\"Bob\"}" NX TTL 3600
```

### **3.4 Bulk Cache Operations**
```sql
-- Get multiple keys in one request
MGET user:123:profile user:124:profile
```

**Response**:
```json
{
  "hits": [
    {"key": "user:123:profile", "value": "...", "status": "HIT"},
    {"key": "user:124:profile", "status": "MISS"}
  ]
}
```

### **3.5 Cache Eviction (By Region)**
```sql
-- Clear all keys in 'user_profiles' region
EVICT_REGION user_profiles
```

### **3.6 Cache Analytics**
```sql
-- Get cache hit/miss ratio for last hour
ANALYTICS
  FILTER (region = 'user_profiles' AND timestamp > '2024-05-20T12:00:00Z')
  GROUP BY (cache_provider)
```

**Response**:
```json
{
  "region": "user_profiles",
  "hit_ratio": 0.85,
  "cache_provider": "Redis",
  "last_refreshed": "2024-05-20T13:05:00Z"
}
```

---

## **4. Implementation Best Practices**
### **4.1 Key Design**
- **Use versioning**: Include `:v1`, `:v2` to avoid key collisions during refactoring.
- **Avoid dynamic keys**: Keys like `user:${id}` are harder to invalidate. Use `user:123` instead.
- **Hash sensitive data**: For PII, hash keys (e.g., `user_hash:abc123` instead of `user:john_doe`).

### **4.2 TTL Strategies**
| **Strategy**          | **When to Use**                                                                                     | **Example TTL**          |
|-----------------------|-----------------------------------------------------------------------------------------------------|--------------------------|
| **Fixed TTL**         | Stable data (e.g., product catalog).                                                              | `86400` (1 day)          |
| **Sliding Window**    | Data accessed frequently (e.g., session tokens).                                                   | Reset TTL on access.     |
| **Dynamic TTL**       | Data with variable volatility (e.g., stock prices).                                                | `300 + (last_update_ms / 1000)` |
| **Short-Lived**       | High-frequency, low-cost data (e.g., ads).                                                        | `60` (1 minute)          |
| **Long-Lived**        | Rarely changing data (e.g., static pages).                                                       | `604800` (7 days)        |

### **4.3 Invalidation**
- **Event-Driven Invalidation**:
  - Use pub/sub (e.g., Kafka, RabbitMQ) to notify caches when data changes.
  - Example: When a `user:123` is updated, publish `UserUpdated{id:123}` to a topic.
- **Time-Based Invalidation**:
  - Use **Scheduled Jobs** (e.g., cron) to refresh stale caches (e.g., daily news).
- **Lazy Loading**:
  - Mark stale caches as `INVALID` and recompute on next access.

### **4.4 Fault Tolerance**
| **Scenario**               | **Mitigation Strategy**                                                                              |
|-----------------------------|-------------------------------------------------------------------------------------------------------|
| Cache server down           | Use **fallback to database** or return stub data.                                                 |
| Thundering herd             | Implement **rate limiting** or **early expiration**.                                               |
| Cache key collisions        | Use **SHA-256 hashes** for dynamic keys.                                                          |
| Stale reads                 | Use **conditional writes** (`SET ... NX`) or **versioned keys**.                                 |

### **4.5 Monitoring**
- **Metrics to Track**:
  - `cache_hit_ratio` (target: **>80%**).
  - `cache_latency_p99` (target: **<100ms**).
  - `eviction_rate` (high rate → resize cache).
  - `fallback_fails` (increase fallback thresholds).
- **Tools**:
  - Prometheus + Grafana for metrics.
  - RedisInsight (for Redis debugging).
  - Distributed tracing (Jaeger) for cache request flow.

---

## **5. Query Examples (Code Snippets)**
### **5.1 Java (Caffeine Cache)**
```java
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;

public class UserProfileCache {
    private final Cache<String, UserProfile> cache = Caffeine.newBuilder()
        .maximumSize(10_000)
        .expireAfterWrite(3600, TimeUnit.SECONDS)
        .build();

    public UserProfile getProfile(String userId) {
        return cache.get(
            key -> db.getUserProfile(userId),
            userId + ":profile:v2"
        );
    }
}
```

### **5.2 Python (Redis)**
```python
import redis
import json

r = redis.Redis(host='localhost', port=6379)
USER_PROFILE_KEY = "user:{}:profile:v2"

def get_profile(user_id):
    cache_key = USER_PROFILE_KEY.format(user_id)
    data = r.get(cache_key)
    if data:
        return json.loads(data)
    # Fallback to DB
    profile = db.get_user_profile(user_id)
    r.setex(cache_key, 3600, json.dumps(profile))
    return profile
```

### **5.3 Go (Redis)**
```go
package main

import (
	"context"
	"github.com/go-redis/redis/v8"
)

func getUserProfile(ctx context.Context, r *redis.Client, id string) (*UserProfile, error) {
	key := fmt.Sprintf("user:%s:profile:v2", id)
	val, err := r.Get(ctx, key).Result()
	if err == redis.Nil {
		// Miss: fetch from DB
		profile, err := db.GetUserProfile(id)
		if err != nil {
			return nil, err
		}
		_, err = r.SetEx(ctx, key, profile.JSON(), 3600).Result()
		return profile, err
	}
	// Parse and return
	return userProfileFromJSON(val)
}
```

---

## **6. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Combine**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Request-Response**      | Standard HTTP/REST flow.                                                                             | Use caching to reduce database queries in request handling.                          |
| **Circuit Breaker**       | Prevents cascading failures by limiting cache-dependent operations.                                 | Fallback to database if cache is unavailable.                                       |
| **Event Sourcing**        | Tracks data changes via events.                                                                       | Invalidate caches via event streams (e.g., Kafka).                                  |
| **Bulkhead Pattern**      | Limits concurrency for cache operations to prevent overload.                                         | Protect cache writes during high traffic.                                           |
| **Rate Limiting**         | Controls cache access to prevent abuse.                                                             | Apply rate limits to cache regions (e.g., `user_profiles`).                         |
| **CQRS (Command Query Responsibility Segregation)** | Separates read (cached) and write (database) models.               | Cache is the "Read Model" in CQRS.                                                  |
| **Optimistic Locking**    | Detects cache stampedes on concurrent writes.                                                        | Use versioned keys (`:v2`) to handle conflicts.                                       |
| **Retry Pattern**         | Handles transient cache failures (e.g., Redis downtime).                                           | Retry failed cache operations with exponential backoff.                               |

---

## **7. Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                                                                       | **Solution**                                                                          |
|----------------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Over-Caching**                | Caching small, frequently changing data (e.g., user sessions).                                   | Use **short TTLs** or **lazy loading**.                                              |
| **Key Design Fluctuations**      | Changing key formats mid-deployment (breaking existing caches).                                   | Freeze cache keys during schema changes; use `:v2` for migrations.                    |
| **No Invalidation Strategy**     | Stale data propagates indefinitely.                                                              | Implement **event-based** or **time-based** invalidation.                             |
| **Cache Invalidation Storm**     | Invalidate entire regions on single writes (e.g., invalidating `user:*` when one user updates). | Use **fine-grained keys** (e.g., `user:123:profile`).                                  |
| **Ignoring Cache Hit Ratio**     | Accepting high miss rates without optimization.                                                   | Analyze **cache miss patterns** and add more data to cache.                          |
| **Monolithic Cache Regions**     | Single cache region for unrelated data (e.g., `all_data`).                                       | Split into **logical regions** (e.g., `user_profiles`, `product_catalog`).            |

---
## **8. Tools & Libraries**
| **Tool/Library**       | **Use Case**                                                                                     | **Language Support**       |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------|
| **Redis**              | In-memory data store with TTL support.                                                          | Multi-language              |
| **Memcached**          | Simple, high-performance caching.                                                                | C, Python, Java, Go         |
| **Guava Cache**        | Embedded caching for Java.                                                                       | Java                        |
| **Caffeine**           | High-performance caching for Java (drop-in replacement for Guava).                              | Java                        |
| **RedisStack**         | Redis with built-in JSON and ML capabilities.                                                    | Multi-language              |
| **Apache Ignite**      | Distributed cache with SQL-like queries.                                                       | Java, C++, Python           |
| **HashiCorp Consul**   | Service mesh with integrated caching.                                                           | Multi-language              |
| **PgBouncer**          | Connection pooling for PostgreSQL (can act as a cache for query results).                        | PostgreSQL                  |

---
## **9. Glossary**
| **Term**                | **Definition**                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------|
| **Cache Hit**           | Request retrieving data from cache.                                                              |
| **Cache Miss**          | Request fetching data from fallback (e.g., database).                                            |
| **Cache Stampede**      | Many requests miss cache simultaneously, overwhelming the backend.                               |
| **TTL (Time-To-Live)**  | Duration (in seconds) before cache entry expires.                                                 |
| **Cache Warmer**        | Pre-loads cache entries to reduce initial misses.                                                 |
| **Cache Eviction**      | Removing least recently used or oldest entries when cache is full.                                 |
| **Cache Stampede Protection** | Mechanisms to prevent concurrent misses (e.g., locks, probabilistic early expiration).   |
| **Distributed Cache**   | Cache shared across