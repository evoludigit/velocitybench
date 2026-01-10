# **[Pattern] API Caching Strategies – Reference Guide**

---
## **Overview**
API caching optimizes performance by storing compute-intensive results (e.g., database queries, external calls) so they can be served from memory rather than recomputed. A robust caching strategy reduces latency, minimizes backend load, and scales seamlessly under high traffic. Key considerations include **cache location** (client, edge, API layer, or database), **eviction policies** (TTL, size limits), and **invalidations** (manual or event-driven). Poorly designed caches can lead to stale data, cache stampedes, or resource exhaustion. This guide outlines common strategies, trade-offs, and implementation best practices.

---

## **Schema Reference**
| **Component**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Cache Store**             | Persistent key-value store (in-memory or disk-backed) with low-latency access.                                                                                                                                | Redis, Memcached, local HTTP cache, Cloudflare Workers KV                                      |
| **Cache Key**               | Unique identifier for cached data, combining request context and dynamic values (e.g., `GET /users/{id}?status=active`). Must be deterministic and collision-resistant.           | `user:123:status:active`                                                                         |
| **Cache TTL (Time-to-Live)**| Duration to retain cached data before expiring (e.g., 5 minutes, 24 hours).                                                                                                                                  | `TTL=300` (5 minutes)                                                                           |
| **Cache Invalidation**      | Mechanism to remove stale data:                                                                                                                                                                             |                                                                                                 |
| &nbsp;&nbsp;&nbsp;**Manual** | Developer-triggered (e.g., after `POST /users/123/update`).                                                                                                                                                 | `cache.delete("user:123")`                                                                       |
| &nbsp;&nbsp;&nbsp;**TTL**    | Automatic expiration after `TTL`.                                                                                                                                                                           | `redis.set("user:123", "data", EX 3600)` (expires in 1 hour)                                   |
| &nbsp;&nbsp;&nbsp;**Event-Driven** | Invalidates on upstream changes (e.g., database trigger, webhook).                                                                                                                                            | PostgreSQL `ON UPDATE` trigger calling `cache.invalidate("user:123")`                           |
| **Cache Stampede Protection**| Mitigates "thundering herd" problem where all requests hit the cache after invalidation.                                                                                                                  | Redis `Pipelining` or `QUERYSTORE`                                                                 |
| **Cache Warmer**            | Pre-fetches popular data before it’s requested (e.g., cron job for trending posts).                                                                                                                              | `cache.set("trending:posts", fetchTrendingPosts(), EX 3600)`                                     |
| **Cache Granularity**       | Scope of cached data:                                                                                                                                                                                       |                                                                                                 |
| &nbsp;&nbsp;&nbsp;**Fine-Grained** | Cache individual API responses (e.g., single user record).                                                                                                                                                 | `GET /users/123` → cache `user:123`                                                                 |
| &nbsp;&nbsp;&nbsp;**Coarse-Grained**| Cache broader blocks (e.g., all users for a role).                                                                                                                                                         | `GET /users?role=admin` → cache `users:role:admin`                                             |
| **Cache Side Effects**      | Undesired behaviors like:                                                                                                                                                                                   |                                                                                                 |
| &nbsp;&nbsp;&nbsp;**Stale Reads** | Returning outdated data due to missed invalidations.                                                                                                                                                       | Use `If-Modified-Since` headers or versioned keys (`user:123:v2`).                              |
| &nbsp;&nbsp;&nbsp;**Cache Invalidation Lag** | Delay between data change and cache purge.                                                                                                                                                                 | Combine TTL + event-driven invalidation.                                                         |

---

## **Query Examples**
### **1. Basic API Caching with Redis (Node.js)**
```javascript
const redis = require('redis');
const client = redis.createClient();

// Cache GET /products/{id}
app.get('/products/:id', async (req, res) => {
  const { id } = req.params;
  const cacheKey = `product:${id}`;

  // Try to fetch from cache
  const cachedData = await client.get(cacheKey);
  if (cachedData) return res.json(JSON.parse(cachedData));

  // Fallback to DB
  const product = await db.query('SELECT * FROM products WHERE id = ?', [id]);

  // Cache response (TTL=1 hour)
  await client.set(
    cacheKey,
    JSON.stringify(product),
    'EX',
    3600
  );

  res.json(product);
});
```

### **2. Cache Invalidation on Database Update (PostgreSQL + Redis)**
```sql
-- PostgreSQL trigger to invalidate cache on update
CREATE OR REPLACE FUNCTION invalidate_product_cache()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('product_updated', JSON_BUILD_OBJECT('id', NEW.id)::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invalidate_product
AFTER UPDATE OF name, price ON products
FOR EACH ROW EXECUTE FUNCTION invalidate_product_cache();
```
```javascript
// Redis subscriber for invalidation
const subscriber = redis.createClient();
subscriber.subscribe('product_updated');

subscriber.on('message', (channel, data) => {
  const { id } = JSON.parse(data);
  client.del(`product:${id}`);
});
```

### **3. Edge Caching with Cloudflare Workers KV**
```javascript
// Cloudflare Workers script
addEventListener('fetch', (event) => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const cacheKey = `api:${url.pathname}:${request.headers.get('x-api-version')}`;

  // Try KV cache
  const cached = await caches.default.match(cacheKey);
  if (cached) return cached;

  // Fallback to origin
  const originResponse = await fetch(request);
  const clone = originResponse.clone();
  const data = await clone.text();

  // Cache response (TTL=1 minute)
  await caches.default.put(cacheKey, new Response(data, {
    headers: { 'Content-Type': 'application/json' }
  }));

  return originResponse;
}
```

### **4. Cache Stampede Protection (Redis)**
```javascript
async function getWithStampedeProtection(cacheKey) {
  // Try to acquire a lock
  const lock = await client.set(`lock:${cacheKey}`, 'locked', 'NX', 'EX', 5); // 5s lock
  if (!lock) {
    // Wait and retry (exponential backoff)
    await new Promise(resolve => setTimeout(resolve, 100));
    return getWithStampedeProtection(cacheKey);
  }

  // Check cache again
  const cachedData = await client.get(cacheKey);
  if (cachedData) {
    await client.del(`lock:${cacheKey}`); // Release lock
    return JSON.parse(cachedData);
  }

  // Simulate DB call
  const dbData = await db.query('SELECT * FROM users WHERE id = ?', [123]);

  // Update cache
  await client.set(cacheKey, JSON.stringify(dbData), 'EX', 3600);
  await client.del(`lock:${cacheKey}`);

  return dbData;
}
```

### **5. Coarse-Grained Caching (Bulk Fetching)**
```javascript
// Cache all active users at once (instead of per-request)
const cacheKey = 'users:active';
const cachedUsers = await client.get(cacheKey);

if (!cachedUsers) {
  const users = await db.query('SELECT * FROM users WHERE is_active = true');
  await client.set(cacheKey, JSON.stringify(users), 'EX', 600); // 10 minutes
}

return JSON.parse(cachedUsers);
```

---

## **Components/Solutions**
### **1. Cache Store**
| **Option**       | **Use Case**                          | **Pros**                                  | **Cons**                                  |
|------------------|---------------------------------------|------------------------------------------|------------------------------------------|
| **Redis**        | High-performance, persistent key-value | Supports pub/sub, high throughput (100K+ ops/sec) | Requires managed service (e.g., Redis Labs) |
| **Memcached**    | Simple in-memory caching              | Low latency, no persistence              | No persistence, no advanced features     |
| **Local HTTP Cache** | Browser/client-side caching          | Zero dependencies                        | Limited storage (~80MB in browsers)      |
| **Cloudflare KV** | Edge caching                         | Sub-10ms latency, globally distributed   | No TTL-based eviction                      |
| **Database Cache** | Hybrid approach (e.g., PostgreSQL `pg_cache`) | No external dependency                   | Higher latency than Redis                |

### **2. Cache Key Strategies**
- **Static + Dynamic Components**:
  `GET /products?category=electronics&sort=price` →
  `products:category=electronics:sort=price`
- **Versioned Keys**:
  Prevent stale reads when schemas change:
  `user:123:v2` (appends version on updates).
- **Query Parameter Handling**:
  Use `*` for optional params:
  `users:?*name=john*` → matches `/users?name=john` or `/users?name=john%20doe`.

### **3. Invalidation Strategies**
| **Strategy**          | **When to Use**                          | **Implementation**                                  |
|-----------------------|------------------------------------------|----------------------------------------------------|
| **TTL-Based**         | Data changes infrequently (e.g., product listings). | Set `EX` flag in Redis (`set(key, value, EX, 3600)`). |
| **Event-Driven**      | Real-time updates (e.g., live scores).    | Use database triggers or message queues (Kafka).   |
| **Manual**            | Critical data (e.g., admin actions).      | Call `cache.delete()` after write operations.      |
| **Conditional GETs**  | HTTP caching (Etag/Last-Modified).       | Serve `ETag` headers to allow clients to skip requests. |

---

## **Related Patterns**
1. **Request Throttling**
   Pair caching with throttling to prevent cache stampedes (e.g., rate-limit cache invalidations).
2. **Circuit Breaker**
   Combine with caching to fail fast during database outages (e.g., return stale data if DB is down).
3. **Retry with Backoff**
   For invalidation failures, use exponential backoff before retrying (e.g., `try-catch` with `await retry()`).
4. **Database Denormalization**
   Cache join-heavy queries by pre-aggregating data (e.g., denormalize `users_with_orders`).
5. **Edge Functions**
   Offload caching to edge (e.g., Cloudflare Workers) to reduce origin load.

---
## **Antipatterns to Avoid**
1. **Over-Caching**
   Cache everything → leads to memory bloat and inconsistency. Focus on **hot paths** (e.g., 80/20 rule).
2. **Ignoring Cache Invalidation**
   Relying only on TTL for dynamic data → risk stale reads. Combine with event-driven invalidation.
3. **Cache Key Collisions**
   Poorly designed keys (e.g., `GET /users?id=123` → `user:123` and `user:123?active=true` share key).
4. **No Cache Side Effects Testing**
   Assume caching works in dev → production fails due to untested invalidations. Use tools like [RedisInsight](https://redisinsight.redis.com/).

---
## **Tools & Libraries**
| **Tool**               | **Purpose**                          | **Language Support**       |
|------------------------|--------------------------------------|----------------------------|
| **Redis**              | In-memory data structure store       | Node.js, Python, Java      |
| **Memcached**          | Simple in-memory caching             | C, Java, PHP               |
| **Cloudflare Workers KV** | Edge caching                        | JavaScript/TypeScript       |
| **Varnish Cache**      | HTTP cache (CDN layer)               | C, Lua                     |
| **SQLite Cache Extensions** | Database-level caching          | PostgreSQL, MySQL           |
| **Axios Cache Interceptor** | HTTP client caching          | JavaScript (Frontend/Backend) |

---
## **Further Reading**
- [Redis Best Practices](https://redis.io/topics/best-practices)
- [HTTP Caching: How It Works](https://httpwg.org/specs/rfc7234.html)
- [Caching Strategies for Web Applications](https://www.nginx.com/blog/caching-in-web-applications/) (NGINX)
- [Event-Driven Architecture with Kafka](https://kafka.apache.org/)