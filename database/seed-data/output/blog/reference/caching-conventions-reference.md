# **[Pattern] Caching Conventions Reference Guide**

---

## **Overview**
The **Caching Conventions** pattern defines standardized rules for identifying, validating, and managing cached data to improve performance, consistency, and scalability. This guide outlines key principles, schema structures, and implementation practices to ensure predictable caching behavior across systems. It addresses common challenges like cache invalidation, TTL (Time-To-Live) management, and cache granularity while aligning with microservices, distributed systems, and caching layers (e.g., Redis, CDN, or in-memory caches).

---

## **Key Concepts**
### **Core Principles**
| Concept               | Definition                                                                                     | Example                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Cache Key**         | A unique identifier for cached data, derived from request/response metadata.                 | `GET /api/users/12345?sort=name` → `cache-key: users-12345-sort-name` |
| **Cache TTL**         | Duration (e.g., seconds) data remains valid before revalidation or eviction.                 | `TTL: 3600` (1 hour)                                                    |
| **Cache Invalidation**| Mechanisms to remove stale data when source changes (e.g., via event triggers or manual tags). | `Invalidate: { "tag": "user-profile-12345", "expires": "2024-05-20T00:00:00Z" }` |
| **Cache Granularity** | Level of data caching (e.g., full document, partial fragments, or key-value pairs).         | Full document vs. caching only the `name` field of a user object.        |
| **Cache Stampede**    | Concurrent request surge after cache expiration, overwhelming the source system.             | Mitigated via probabilistic early expiration or background reloads.     |
| **Cache Coherence**   | Ensuring consistency between cached and source data (e.g., via versioning or timestamps).    | `version: "v2"` or `etag: "abc123"`                                    |

---

## **Schema Reference**
### **1. Cache Key Schema**
Defines standardized formats for cache keys to ensure uniformity.

| Field          | Type    | Description                                                                                     | Example                                  |
|----------------|---------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `namespace`    | String  | Logical group for cache keys (e.g., `users`, `products`).                                        | `users`                                  |
| `entity`       | String  | Resource identifier (e.g., `id`, `slug`).                                                     | `id` or `slug: "widget-pro-1"`           |
| `selector`     | Object  | Query parameters (e.g., `sort`, `filter`) to vary cache granularity.                           | `{ "sort": "name", "limit": 10 }`       |
| `version`      | String  | Semantic version to handle breaking changes.                                                   | `v1.2.0`                                 |
| **Key Format** | —       | `namespace:entity-selector-version` or `namespace:entity-selector` (if version omitted).      | `users:id-12345-v1.2.0`                  |

---

### **2. Cache Metadata Schema**
Attributes associated with cached data to support invalidation and TTL management.

| Field          | Type    | Description                                                                                     | Example                                  |
|----------------|---------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `ttl`          | Integer | Time-to-live in seconds. Default: `300` (5 minutes).                                           | `3600` (1 hour)                          |
| `expires_at`   | String  | Absolute expiration timestamp (ISO 8601).                                                      | `"2024-05-21T12:00:00Z"`                |
| `version`      | String  | Version of cached data (linked to `namespace:entity`).                                          | `"v1"`                                   |
| `tags`         | Array   | Logical groupings for bulk invalidation (e.g., `user-profile`, `inventory-stock`).            | `["user-profile-12345", "inventory"]`    |
| `etag`         | String  | Hash of cached data for conditional requests (e.g., `If-None-Match`).                         | `"d41d8cd98f00b204e9800998ecf8427e"`    |
| `conditional`  | Object  | Rules for cache bypass (e.g., `if-modified-since`).                                            | `{ "if-modified-since": "Wed, 21 May 2024 12:00:00 GMT" }` |

---

### **3. Cache Invalidation Schema**
Triggers to invalidate cached data programmatically.

| Field          | Type    | Description                                                                                     | Example                                  |
|----------------|---------|-------------------------------------------------------------------------------------------------|------------------------------------------|
| `type`         | String  | Invalidation method (`delete`, `tag`, `version`).                                             | `"tag"`                                  |
| `target`       | String  | Namespace or tag to invalidate (e.g., `users:*` or `user-profile-12345`).                      | `"users:id-12345"`                       |
| `source`       | String  | System/endpoint triggering invalidation (e.g., `db-updater`, `admin-panel`).                  | `"db-updater"`                           |
| `timestamp`    | String  | When invalidation occurred (ISO 8601).                                                        | `"2024-05-20T10:00:00Z"`                |

---

## **Query Examples**
### **1. Generating a Cache Key**
**Request:**
```http
GET /api/users/12345?sort=name&limit=10
```
**Cache Key:**
```plaintext
users:id-12345-sort-name:limit-10-v1.2.0
```

**Metadata:**
```json
{
  "ttl": 3600,
  "expires_at": "2024-05-21T12:00:00Z",
  "tags": ["user-profile-12345", "user-listings"],
  "etag": "abc123"
}
```

---

### **2. Conditional Cache Fetch (ETag)**
**Request:**
```http
GET /api/users/12345 HTTP/1.1
If-None-Match: "abc123"
```
**Response (200 if unchanged, 304 if stale):**
```http
HTTP/1.1 304 Not Modified
ETag: "abc123"
```

---

### **3. Invalidating by Tag**
**Invalidation Payload:**
```json
{
  "type": "tag",
  "target": "user-profile-12345",
  "source": "db-updater"
}
```
**Cache Layer Action:**
Remove all entries tagged `user-profile-12345`.

---

### **4. Background Cache Rebuild**
**Trigger:**
```python
# Pseudocode: Queue a background job to rebuild stale cache
cache_rebuilder.add_task(
  key="users:id-12345-v1.2.0",
  priority="high",
  ttl=300  # Rebuild within 5 minutes
)
```

---

## **Implementation Patterns**
### **1. Cache Key Generation**
- **Dynamic Keys:** Use templating (e.g., Jinja2, Handlebars) to inject variables:
  ```python
  cache_key = f"products:category-{category_id}-{sort_by}-{page_limit}"
  ```
- **Hashing:** For large payloads, hash parameters (e.g., MD5) to limit key length:
  ```python
  import hashlib
  cache_key = f"search:query-{hashlib.md5(query.encode()).hexdigest()}"
  ```

---

### **2. TTL Strategies**
| Strategy               | Use Case                                                                | Example TTL       |
|------------------------|------------------------------------------------------------------------|-------------------|
| **Short TTL**          | High-frequency updates (e.g., stock prices).                           | `60` (1 minute)   |
| **Long TTL**           | Stable data (e.g., product catalogs).                                 | `86400` (1 day)   |
| **Dynamic TTL**        | Context-aware (e.g., prioritize recent activity).                      | `ttl = 3600 * priority_factor` |
| **Sliding Window**     | Recent activity (e.g., trending items).                                | Reset TTL on access. |

---

### **3. Invalidation Triggers**
| Trigger Type          | Description                                                                 | Example                          |
|-----------------------|-----------------------------------------------------------------------------|----------------------------------|
| **Event-Driven**      | Pub/Sub (e.g., Kafka, RabbitMQ) triggers invalidation on source changes.     | `user_updated → invalidate("users:id-12345")` |
| **Manual Tags**       | Admin UI or CLI to invalidate by tag.                                      | `admin-cli invalidate --tag user-profile-12345` |
| **Version Bump**      | Change `version` in metadata when data schema evolves.                      | Bump from `v1` to `v2`.           |
| **Time-Based**        | Rotate cache entries at fixed intervals (e.g., daily).                     | `0 3 * * * invalidate("users:*:v1")` (cron). |

---

### **4. Cache Granularity**
| Granularity Level      | Pros                                      | Cons                                      | Use Case                          |
|------------------------|-------------------------------------------|-------------------------------------------|-----------------------------------|
| **Full Document**      | Simple, low fragmentation.                | High memory usage for large changes.     | Static content (e.g., FAQs).      |
| **Partial (Fragments)**| Efficient updates (e.g., single field).   | Complex key management.                   | Dynamic UI (e.g., user dashboard).|
| **Key-Value**          | Atomic operations.                        | Less flexible for nested data.           | Session tokens or counters.       |

---

## **Query Examples (API Integration)**
### **1. Cache-Hit Response (HTTP)**
```http
HTTP/1.1 200 OK
Cache-Control: max-age=3600
X-Cache: HIT
ETag: "abc123"
Content-Type: application/json

{"id": "12345", "name": "John Doe", ...}
```

### **2. Cache-Miss Response**
```http
HTTP/1.1 200 OK
Cache-Control: public, max-age=3600
ETag: "abc123"
Content-Type: application/json

{"id": "12345", "name": "John Doe", ...}
```

### **3. Conditional Get (ETag)**
```http
HTTP/1.1 304 Not Modified
Cache-Control: max-age=0
ETag: "abc123"
```

---

## **Related Patterns**
| Pattern                     | Description                                                                 | When to Use                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[Cache Aside (Lazy Loading)**](https://microservices.io/patterns/data/cache-aside.html) | Fetch from cache first; miss → load from DB → update cache.               | General-purpose caching with fallback.                                    |
| **[Write-Through**](https://microservices.io/patterns/data/write-through.html) | Update cache *and* DB simultaneously.                                     | Strong consistency requirements (e.g., financial data).                   |
| **[Write-Behind**](https://microservices.io/patterns/data/write-behind.html) | Asynchronously update cache after DB write.                                | High write throughput (e.g., logs).                                       |
| **[Cache Stampede Protection**](https://martinfowler.com/bliki/TwoPhaseTermination.html) | Probabilistic early expiration to avoid load spikes.                        | High-concurrency scenarios (e.g., hot product pages).                    |
| **[Cache Warmer**](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-warming) | Pre-warm cache with anticipated requests.                                 | Predictable traffic patterns (e.g., dashboards).                         |
| **[Event Sourcing + CQRS**](https://martinfowler.com/eaaP/patterns.html) | Separate read/write models with cached projections.                        | Complex event-driven systems (e.g., e-commerce).                          |
| **[CDN Caching**](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)   | Edge caching for static assets or low-latency APIs.                       | Global audiences (e.g., media sites).                                    |

---

## **Best Practices**
1. **Key Design:**
   - Keep keys **predictable** and **consistent** across services.
   - Avoid regex in keys (e.g., use `namespace:entity-id` instead of `users_*`).
   - Limit key length (e.g., < 256 chars) to avoid fragmentation.

2. **TTL Tuning:**
   - Start with **short TTLs** (e.g., 5–30 minutes) and increase based on tests.
   - Use **dynamic TTLs** for data with varying update frequencies.

3. **Invalidation:**
   - Prefer **tag-based** invalidation for bulk updates (e.g., `user-*`).
   - Log invalidation events for debugging:
     ```json
     { "event": "cache_invalidate", "key": "users:id-12345", "timestamp": "2024-05-20T10:00:00Z", "source": "admin-panel" }
     ```

4. **Monitoring:**
   - Track **cache hit/miss ratios** (aim for >90% hits).
   - Alert on **cache stampedes** (spikes in DB load after expiration).
   - Monitor **memory usage** to avoid eviction storms.

5. **Security:**
   - Sanitize cache keys to prevent injection (e.g., `user_id=123' OR '1'='1`).
   - Use **short-lived tokens** for sensitive data (e.g., `cache_key:session-12345-ttl:300`).

6. **Testing:**
   - **Unit Tests:** Validate key generation and metadata.
   - **Integration Tests:** Simulate cache hits/misses and invalidations.
   - **Load Tests:** Stress-test under concurrent cache misses.

---
## **Troubleshooting**
| Issue                     | Root Cause                          | Solution                                                                 |
|---------------------------|-------------------------------------|--------------------------------------------------------------------------|
| **Cache Stampede**        | All requests expire simultaneously. | Use **probabilistic early expiration** or **background reloads**.        |
| **Thundering Herd**       | Cache invalidation triggers DB load. | **Tag-based invalidation** + **asynchronous reloads**.                  |
| **Cache Inconsistency**   | DB writes lag behind cache updates. | **Write-through** or **eventual consistency** with TTLs.               |
| **Key Collision**         | Duplicate keys due to poor design.  | **Hash suffixes** or **namespacing** (e.g., `serviceA:key`, `serviceB:key`). |
| **Memory Bloat**          | Too many unused cache entries.     | **TTL cleanup jobs** + **LRU eviction**.                                |

---
## **Tools & Libraries**
| Tool/Library               | Purpose                                                                 | Example Use Case                          |
|----------------------------|-------------------------------------------------------------------------|-------------------------------------------|
| **Redis**                 | In-memory key-value store.                                               | Session caching, rate limiting.          |
| **Memcached**             | Distributed caching for low-latency access.                            | API response caching.                   |
| **Vitess**                | Database proxy with caching support.                                   | MySQL-compatible caching for large-scale DBs. |
| **CDN (Cloudflare, Akamai)** | Edge caching for static/dynamic content.                               | Global API latency reduction.           |
| **Cache2k** (Java)        | Local caching with TTL and eviction policies.                         | Microservices caching.                   |
| **Guava Cache** (Java)    | Local cache with loader/callbacks.                                    | Offline-first apps.                      |
| **Purge.js**              | CDN cache invalidation tool.                                           | Purging stale static assets.             |

---
## **Example Implementation (Python + Redis)**
```python
import redis
import hashlib

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0)

def generate_cache_key(namespace: str, entity: str, selector: dict, version: str = "v1") -> str:
    """Generate a standardized cache key."""
    selector_str = "".join(f"{k}-{v}" for k, v in sorted(selector.items()))
    return f"{namespace}:{entity}-{selector_str}-{version}"

def cache_get(key: str) -> tuple[bool, str]:
    """Retrieve data from cache or return empty."""
    data = redis_client.get(key)
    return (data is not None, data.decode() if data else None)

def cache_set(key: str, data: str, ttl: int = 3600) -> None:
    """Store data with TTL."""
    redis_client.setex(key, ttl, data)

# Example Usage
key = generate_cache_key("users", "id-12345", {"sort": "name"}, "v1.2.0")
cache_set(key, '{"id": "12345", "name": "John Doe"}', ttl=3600)
hit, data = cache_get(key)
print(hit, data)  # True, '{"id": "12345", ...}'
```

---
## **Antipatterns**
1. **Over-Caching:**
   - Cache **too much** (e.g., entire DB tables) → increases memory usage and invalidation complexity.
   - **Fix:** Cache only **frequently accessed, immutable, or expensive-to-compute** data.

2. **No Invalidation Strategy:**
   - Relying on **TTL alone** ignores intentional updates (e.g., admin changes).
   - **Fix:** Combine **TTL + tag-based invalidation**.

3. **Ignoring Cache Coherence:**
   - **Stale reads** due to missing version checks or ETags.
   - **Fix:** Use **conditional requests** (`If-None-Match