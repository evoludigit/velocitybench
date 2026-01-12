---

# **[Pattern] Caching Approaches: Reference Guide**

---

## **Overview**
Caching is a performance optimization pattern that stores frequently accessed or computationally expensive data in a **fast-access memory layer (cache)** to reduce latency and offload backend resources. This guide covers three primary caching approaches—**Client-Side, Edge/Proxy Caching, and Server-Side Caching**—highlighting use cases, trade-offs, and implementation details. Each approach targets different scopes (user vs. network vs. application) and requires distinct configuration, validation strategies, and invalidation mechanisms to ensure data consistency.

---

## **Schema Reference**
| **Approach**               | **Scope**               | **Key Components**                                                                 | **Pros**                                                                                     | **Cons**                                                                                     |
|----------------------------|-------------------------|------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Client-Side Caching**    | User-level             | Browser cache, localStorage, Service Workers, CDN caches (e.g., Cloudflare)        | Low-latency, offline support, reduces bandwidth usage                                       | Cache invalidation challenges, security risks (XSS, MITM), limited cache size (~5MB–5GB) |
| **Edge/Proxy Caching**     | Network-level (CDN/ISP) | Edge nodes (Cloudflare, Fastly), reverse proxies (Nginx, Varnish)                  | Reduces latency globally, offloads origin servers, scalable for static assets               | Requires CDN provider, stale content risk, higher costs for dynamic content                 |
| **Server-Side Caching**    | Application-level       | In-memory caches (Redis, Memcached), database-level caches (PostgreSQL `pg_temp`), or application-specific caches (e.g., Django Cache Framework) | Fine-grained control, supports dynamic content, integratable with backend logic          | Memory constraints, cache stampede risk, requires consistent invalidation policies         |

---

## **Implementation Details**

### **1. Client-Side Caching**
**Use Cases**:
- Static assets (JS/CSS/images), API responses with long TTLs, or offline-first apps.
- Reducing round trips for repeated requests (e.g., autocomplete, user preferences).

#### **Key Techniques**:
- **HTTP Caching Headers**:
  - `Cache-Control`: `public max-age=3600` (cacheable by clients/CDNs), `private` (client-only).
  - `ETag`/`Last-Modified`: Enable conditional requests (`If-None-Match: abc123`) to skip fetching unchanged data.
  - Example response:
    ```http
    HTTP/2 200 OK
    Cache-Control: public, max-age=86400
    ETag: "abc123"
    Content-Type: application/json
    ```

- **Service Workers**:
  Use the [Cache API](https://developer.mozilla.org/en-US/docs/Web/API/Caches_API) to intercept network requests and serve cached responses:
  ```javascript
  self.addEventListener('fetch', (event) => {
    event.respondWith(
      caches.match(event.request)
        .then((cachedResponse) => cachedResponse || fetch(event.request))
    );
  });
  ```

- **LocalStorage/SessionStorage**:
  For non-HTTP data (e.g., user settings):
  ```javascript
  localStorage.setItem('userPref', JSON.stringify({ theme: 'dark' }));
  const pref = JSON.parse(localStorage.getItem('userPref'));
  ```

#### **Invalidation Strategies**:
- **Time-Based**: Set `max-age` or `s-maxage` (shared cache, e.g., CDN).
- **Event-Based**: Clear cache on backend writes (e.g., Webhook → client cache purge via SW).
- **Manual**: API endpoints with `/refresh` or `Cache-Control: no-store`.

**Tools**:
- Browser DevTools (`Application` tab → `Cache Storage`).
- CDNs: Cloudflare Workers, Vercel Edge Cache.

---

### **2. Edge/Proxy Caching**
**Use Cases**:
- Global distribution of static content (e.g., images, videos).
- Reducing origin server load for repeated requests (e.g., dashboard analytics).

#### **Key Techniques**:
- **CDN Configuration**:
  - Configure TTLs via provider dashboard (e.g., Cloudflare’s `Cache Level: Standard`).
  - Use `Vary: Accept-Encoding` to cache gzipped responses separately.
  - Example Cloudflare Purge API:
    ```bash
    curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
    -H "Authorization: Bearer YOUR_API_TOKEN" \
    --data '{"purge_everything":true}'
    ```

- **Reverse Proxy Caching** (e.g., Nginx):
  ```nginx
  proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m inactive=60m;
  server {
    location / {
      proxy_cache my_cache;
      proxy_pass http://backend;
      proxy_cache_valid 200 302 1d;
      proxy_cache_valid 404 1m;
    }
  }
  ```

#### **Invalidation Strategies**:
- **Manual Purge**: Trigger via API (e.g., CDN purge) or backend validation.
- **Cache-Busting**: Append versioned query strings (e.g., `/script?v=2.0`).
- **TTL Tuning**: Balance freshness vs. storage (e.g., `max-age=300` for low-change data).

**Tools**:
- CDN Providers: Cloudflare, Fastly, Akamai.
- Proxy Tools: Nginx, Varnish, Squid.

---

### **3. Server-Side Caching**
**Use Cases**:
- Dynamic content (e.g., personalized feeds, database query results).
- Expensive computations (e.g., ML predictions, graph traversals).

#### **Key Techniques**:
- **In-Memory Caches**:
  - **Redis/Memcached**: Key-value stores with sub-millisecond latency.
    ```python
    import redis
    r = redis.Redis(host='localhost', port=6379)
    r.set('user:123:profile', json.dumps(user_profile), ex=3600)  # 1-hour TTL
    cached_data = r.get('user:123:profile')
    ```
  - **Cache Keys**: Use a consistent format (e.g., `entity:type:id` or hash of input parameters).

- **Database Caching**:
  - PostgreSQL `pg_temp`: Temporary tables for query results.
  - Redis integration via extensions (e.g., `redis_store`).

- **Application-Level Caching**:
  - Frameworks:
    - **Django**: `django.core.cache` (backends: Redis, Memcached, LocMem).
    ```python
    from django.core.cache import cache
    cache.set('key', 'value', timeout=60)
    value = cache.get('key')
    ```
    - **Spring Boot**: `@Cacheable`, `@CacheEvict` annotations.
      ```java
      @Cacheable(value = "userCache", key = "#id")
      public User getUser(Long id) { ... }
      ```

#### **Invalidation Strategies**:
- **Time-Based**: Set TTL (`ex` in Redis, `timeout` in Django).
- **Event-Driven**: Listen to database changes (e.g., Redis Pub/Sub for cache updates).
- **Manual**: Invalidate via API or backend triggers (e.g., `cache.delete('key')`).

**Tools**:
- Caching Layers: Redis, Memcached, Apache Ignite.
- ORMs: SQLAlchemy (`cache`), Django ORM (`select_related` + manual cache).

---

## **Query Examples**

### **1. Client-Side Cache Validation (API)**
**Request (First Fetch)**:
```http
GET /api/user/123 HTTP/1.1
Host: example.com
Accept: application/json
```
**Response**:
```http
HTTP/1.1 200 OK
ETag: "abc123"
Cache-Control: max-age=300
Content: { "id": 123, "name": "Alice" }
```

**Request (Subsequent Fetch)**:
```http
GET /api/user/123 HTTP/1.1
Host: example.com
If-None-Match: "abc123"
Accept: application/json
```
**Response (If Unchanged)**:
```http
HTTP/1.1 304 Not Modified
Cache-Control: max-age=300
```

---

### **2. Redis Cache Update (Server-Side)**
**Backend Code (Python)**:
```python
import redis
r = redis.Redis()

# Cache a user profile
user_data = {"name": "Alice", "email": "alice@example.com"}
r.setex('user:123', 300, json.dumps(user_data))  # 5-minute TTL

# Invalidate on update
def update_profile(user_id, new_data):
    r.delete(f'user:{user_id}')
    r.setex(f'user:{user_id}', 300, json.dumps(new_data))
```

**Query the Cache**:
```python
cached_data = json.loads(r.get('user:123'))  # Returns None if expired
```

---

### **3. CDN Purge (Edge Caching)**
**Cloudflare API Purge**:
```bash
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"files":["/static/images/logo.jpg"]}'
```

---

## **Validation and Error Handling**
| **Approach**          | **Validation Check**                     | **Error Handling**                                                                 |
|-----------------------|-----------------------------------------|-----------------------------------------------------------------------------------|
| **Client-Side**       | `Cache-Control` headers, `ETag` checks  | Fallback to network request if cache fails (e.g., `fetch()` in Service Worker).   |
| **Edge/Proxy**        | CDN status checks, `Vary` header        | Graceful degradation: Serve stale content if purge fails.                          |
| **Server-Side**       | Cache hit/miss metrics, TTL expiration  | Circuit breakers (e.g., Redis cluster failover) or fallback to database.         |

---

## **Related Patterns**
1. **[Circuit Breaker](https://microservices.io/patterns/contextual"NoCache.html)**:
   Temporarily stops caching invalidation requests to prevent overload during failures.

2. **[Rate Limiting](https://docs.aws.amazon.com/whitepapers/latest/amazon-cloudfront-best-practices/rate-limiting)**:
   Works with caching to throttle CDN/edge traffic spikes.

3. **[Lazy Loading](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading)**:
   Complements client-side caching by loading assets only when needed.

4. **[Database Sharding](https://aws.amazon.com/sharding/)**:
   Scales read-heavy workloads alongside caching (e.g., shard data by region for Redis clusters).

5. **[Event Sourcing](https://martinfowler.com/eaacatalog/eventSourcing.html)**:
   Enables precise cache invalidation by tracking state changes via events.

---

## **Best Practices**
1. **TTL Tuning**:
   - Short TTLs (e.g., `< 1 hour`) for dynamic data; longer for static assets.
   - Use `s-maxage` for shared caches (CDN) and `max-age` for private caches (client).

2. **Cache Stampede Mitigation**:
   - **Release Acquisition**: Random delays for concurrent cache misses (e.g., Redis `setnx` + loop).
   - **Probabilistic Early Response**: Return stale data with a `stale-while-revalidate: 5` header.

3. **Security**:
   - Sanitize cache keys to prevent injection (e.g., `user:123` → `user:${id}`).
   - Use `Cache-Control: no-cache` for sensitive data (e.g., `/account/billing`).

4. **Monitoring**:
   - Track cache hit/miss ratios (e.g., Prometheus + Grafana for Redis).
   - Alert on high invalidation rates (potential data inconsistency).

5. **Hybrid Caching**:
   Combine approaches (e.g., CDN for static assets + Redis for dynamic API responses).

---
**References**:
- [HTTP Caching RFC 7234](https://tools.ietf.org/html/rfc7234)
- [Redis Caching Guide](https://redis.io/topics/caching)
- [Cloudflare Caching Docs](https://developers.cloudflare.com/cache/)