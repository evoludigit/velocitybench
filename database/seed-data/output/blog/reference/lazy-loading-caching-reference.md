# **[Pattern] Lazy Loading & Caching Reference Guide**

---

## **Overview**
The **Lazy Loading & Caching** pattern defers resource-intensive computations, expensive data retrievals, or heavy object creations until they are *actually needed*. This improves performance by:
- Reducing initial load times (e.g., loading UI elements on demand).
- Minimizing repeated computations (e.g., reusing cached results).
- Optimizing memory/CPU usage by deferring work until necessary.

Caching stores computed or fetched data temporarily, avoiding redundant operations. Lazy loading ensures resources are loaded *only when accessed*. Together, they balance responsiveness and resource efficiency.

---

## **Core Concepts**
| **Term**            | **Definition**                                                                 | **Use Case Example**                          |
|---------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Lazy Loading**    | Delaying initialization/loading until required.                               | Loading images in a gallery only when scrolled into view. |
| **Caching**         | Storing computed/fetched data for reuse.                                      | Caching API responses to avoid repeated requests. |
| **Eager Loading**   | Opposite of lazy loading—resources are initialized upfront.                  | Preloading all menu items on app startup.      |
| **Cache Invalidation** | Mechanisms to update stale cached data (e.g., timestamps, versioning).        | Refreshing session tokens after expiration.   |
| **Memory vs. Disk Cache** | Memory cache (fast, volatile); Disk cache (slower, persistent).             | Mobile apps store temporary data in SQLite vs. RAM. |

---

## **Implementation Details**

### **1. Lazy Loading Strategies**
#### **A. Data Fetching**
- **Defer API Calls**: Load data when a user interacts with a UI element (e.g., clicking a button).
  ```javascript
  // React example: Lazy-loaded component
  const [DataComponent] = React.lazy(() => import('./DataComponent'));
  // Usage:
  <Suspense fallback={<Spinner />}>
    <DataComponent />
  </Suspense>
  ```
  *Key*: Wrap lazy-loaded components in `<Suspense>` for fallback states.

- **Pagination**: Load records in chunks (e.g., infinite scroll).
  ```python
  # Django paginator (lazy-loading query)
  from django.core.paginator import Paginator
  paginator = Paginator(query_set, 20)  # Load 20 records at a time
  ```

#### **B. Resource Loading**
- **Image Lazy Loading**: Load images as they enter the viewport.
  ```html
  <!-- HTML5 lazy-loading -->
  <img src="image.jpg" loading="lazy" alt="Placeholder">
  ```
  *Optimization*: Use `srcset` for responsive images.

- **Third-Party Libraries**: Delay loading scripts until needed.
  ```html
  <!-- Dynamic script loading -->
  <script>
    if (window.scrollY > 500) {
      const script = document.createElement('script');
      script.src = 'analytics.js';
      document.body.appendChild(script);
    }
  </script>
  ```

#### **C. Object Instantiation**
- **Factory Patterns**: Create objects on demand.
  ```typescript
  class DatabaseConnection {
    private static instance: DatabaseConnection;
    private constructor() {} // Private ctor enforces lazy init

    public static getInstance(): DatabaseConnection {
      if (!DatabaseConnection.instance) {
        DatabaseConnection.instance = new DatabaseConnection();
      }
      return DatabaseConnection.instance;
    }
  }
  ```
  *Use Case*: Singleton patterns for expensive resources (e.g., DB connections).

---

### **2. Caching Mechanisms**
#### **A. In-Memory Caching**
- **Key-Value Stores**: Use native JS objects, Redis, or Memcached.
  ```javascript
  // Simple in-memory cache
  const cache = new Map();
  function getCachedData(key) {
    if (!cache.has(key)) {
      cache.set(key, fetchData(key)); // Expensive operation
    }
    return cache.get(key);
  }
  ```
  *Best For*: Short-lived data with high access frequency.

#### **B. LocalStorage/SessionStorage**
- Persistent caching for browsers.
  ```javascript
  // Cache API responses in LocalStorage
  const CACHE_KEY = 'api_response_cache_2024';
  const cachedData = localStorage.getItem(CACHE_KEY);

  if (!cachedData) {
    const data = await fetch('/api/data');
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  }
  ```
  *Limitations*: Size limits (~5MB), synchronous API.

#### **C. Disk-Based Caching**
- **Databases**: SQLite, LevelDB for larger datasets.
  ```javascript
  // Using IndexedDB (disk cache)
  const request = indexedDB.open('MyCacheDB', 1);
  request.onsuccess = (event) => {
    const db = event.target.result;
    const transaction = db.transaction('cache', 'readwrite');
    const store = transaction.objectStore('cache');
    // Store/retrieve data
  };
  ```

#### **D. HTTP Caching**
- **Headers**: Use `Cache-Control` to dictate browser caching.
  ```http
  HTTP/1.1 200 OK
  Cache-Control: max-age=3600, public  # Cache for 1 hour
  ```
  *Example Tools*: Varnish, Nginx for CDN-level caching.

---

### **3. Cache Invalidation Strategies**
| **Strategy**          | **Description**                                  | **Example**                                  |
|-----------------------|--------------------------------------------------|---------------------------------------------|
| **Time-Based**        | Delete cache after a TTL (Time-To-Live).          | `Cache-Control: max-age=86400` (1 day).     |
| **Event-Based**       | Invalidate on specific events (e.g., edits).      | Redis `DEL` key after database update.      |
| **Versioning**        | Append version numbers to keys (e.g., `data_v2`). | `cacheKey: 'user_123_v4'` (updated on schema change). |
| **Manual Invalidations** | Explicit calls to clear cache.                 | `localStorage.clear()` on logout.           |

---

## **Schema Reference**
Below are common patterns with their trade-offs.

| **Pattern**               | **When to Use**                          | **Pros**                                  | **Cons**                                  | **Example Tools**                  |
|---------------------------|------------------------------------------|-------------------------------------------|-------------------------------------------|-------------------------------------|
| **Lazy Loading (UI)**     | Images, heavy components, scripts.       | Faster perceived performance.            | Complex debugging (e.g., hydration issues). | React.lazy, Intersection Observer. |
| **API Caching**           | Repeated API calls (e.g., user profiles).| Reduces network requests.                 | Cache stale data if not invalidated.     | Redis, Memcached.                   |
| **Database Query Caching**| Expensive SQL queries (e.g., reports).   | Avoids recomputation.                     | Risk of data inconsistency.               | PostgreSQL `EXPLAIN ANALYZE`, Redis.|
| **CDN Caching**           | Static assets (JS, CSS, images).         | Global low-latency delivery.              | High setup cost.                          | Cloudflare, Fastly.                 |
| **LocalStorage Caching**  | Browser-side data (e.g., offline apps).  | Persists across sessions.                 | Size limits (~5MB).                      | localStorage, IndexedDB.            |

---

## **Query Examples**
### **1. Lazy-Loaded API Response (Node.js)**
```javascript
const axios = require('axios');
const NodeCache = require('node-cache');
const cache = new NodeCache({ stdTTL: 300 }); // 5-minute TTL

async function getUser(id) {
  const cacheKey = `user_${id}`;
  const cachedData = cache.get(cacheKey);

  if (!cachedData) {
    const response = await axios.get(`/api/users/${id}`);
    cache.set(cacheKey, response.data);
    return response.data;
  }
  return cachedData;
}
```

### **2. Lazy-Loaded React Component with Suspense**
```jsx
import React, { Suspense, lazy } from 'react';

const HeavyComponent = lazy(() => import('./HeavyComponent'));

function App() {
  return (
    <div>
      <Suspense fallback={<div>Loading...</div>}>
        <HeavyComponent />
      </Suspense>
    </div>
  );
}
```

### **3. Cache Invalidation on Database Update (Django)**
```python
# Signal to invalidate cache on model save
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=User)
def invalidate_user_cache(sender, instance, **kwargs):
    cache_key = f'user_{instance.id}'
    cache.delete(cache_key)  # Clear stale cache
```

---

## **Best Practices**
1. **Cache Granularity**:
   - Cache at the right level (e.g., cache entire API responses vs. individual fields).
   - Example: Cache `/users/123` instead of all users.

2. **Cache Size Management**:
   - Set reasonable TTLs (e.g., 5–30 minutes for dynamic data).
   - Use LRU (Least Recently Used) eviction for memory caches.

3. **Error Handling**:
   - Handle cache misses gracefully (e.g., fall back to stale data or retries).
   - Example:
     ```javascript
     try {
       const data = cache.get(key);
       if (!data) throw new Error('Cache miss');
     } catch (err) {
       console.warn('Falling back to fresh data');
       const freshData = fetchData();
       cache.set(key, freshData);
       return freshData;
     }
     ```

4. **Monitoring**:
   - Track cache hit/miss ratios (e.g., 90%+ hits indicate good cache utilization).
   - Tools: Prometheus, Datadog, or custom logging.

5. **Security**:
   - Validate cache keys to prevent injection attacks.
   - Example: Sanitize user input before using it as a cache key.

6. **Fallback for Offline Use**:
   - Combine caching with service workers for progressive enhancement.
   - Example: Use IndexedDB to store API responses for offline access.

---

## **Anti-Patterns & Pitfalls**
| **Anti-Pattern**               | **Risk**                                      | **Solution**                                  |
|---------------------------------|-----------------------------------------------|-----------------------------------------------|
| **Over-Caching**                | Cache becomes a bottleneck for writes.        | Use short TTLs or event-based invalidation.   |
| **No Cache Invalidation**       | Stale data corrupts application state.         | Implement versioning or timestamp checks.    |
| **Global Cache**                | Memory bloat from caching everything.         | Scope caches to specific modules/users.      |
| **Lazy Loading in Critical Path** | Initial render is slow (e.g., above-the-fold content). | Use eager loading for above-the-fold content. |
| **Ignoring Cache Headers**      | CDNs/browsers cache stale or incorrect responses. | Set proper `Cache-Control` and `ETag` headers. |

---

## **Related Patterns**
1. **[Command Pattern](link)**:
   - Useful for deferring operations (e.g., caching API commands until execution).

2. **[Observer Pattern](link)**:
   - Notify caches when data changes (e.g., Redis pub/sub for invalidation).

3. **[Proxy Pattern](link)**:
   - Lazy-load objects via proxies (e.g., virtual proxies for heavy objects).

4. **[Strategic Pattern](link)**:
   - Dynamically switch caching strategies (e.g., disk vs. memory) based on context.

5. **[Pagination & Infinite Scroll](link)**:
   - Complements lazy loading for data-heavy applications.

6. **[Service Worker (Offline-First)](link)**:
   - Cache assets for offline use, paired with lazy loading for performance.

7. **[Bulkhead Pattern](link)**:
   - Isolate caching failures to prevent cascading issues (e.g., circuit breakers for API calls).

8. **[Circuit Breaker Pattern](link)**:
   - Prevent repeated cache misses during outages (fall back to offline data).

---
**See Also**:
- [MDN Web Docs: Lazy Loading](https://developer.mozilla.org/en-US/docs/Web/Performance/Lazy_loading)
- [Redis Caching Guide](https://redis.io/topics/caching)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)