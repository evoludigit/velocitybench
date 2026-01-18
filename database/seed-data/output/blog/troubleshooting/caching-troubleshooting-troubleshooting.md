# **Debugging *Caching*: A Troubleshooting Guide**

Caching is a critical performance optimization tool, but misconfigurations, stale data, or improper invalidation can lead to slow responses, inconsistent data, or even system failures. This guide provides a structured approach to diagnosing and resolving caching-related issues in backend systems.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms align with your issue:

| **Symptom**                     | **Possible Cause**                          |
|----------------------------------|---------------------------------------------|
| Slower-than-expected responses   | Cache miss rate too high                    |
| Stale or outdated data           | Cache not invalidating properly            |
| Cache memory exhaustion          | No TTL (Time-To-Live) or aggressive caching |
| Race conditions / inconsistent reads | Missing cache lock or stale reads          |
| High CPU/Memory usage            | Unnecessary cache computation               |
| Cache bypassing completely       | Misconfigured cache layer or missing setup   |

If you observe **multiple symptoms**, start with the most critical (e.g., stale data before performance degradation).

---

## **2. Common Issues and Fixes**

### **Issue 1: High Cache Miss Rate → Slow Queries**
**Symptom:** Responses degrade to database latency despite caching.

**Root Cause:**
- Cache key is too broad (e.g., caching entire API responses instead of individual data chunks).
- Cache is not **TTL-aware** (data remains too long after changes).
- Cache is **not warmed** (first requests still hit DB).

**Fix:**
#### **Solution: Optimize Cache Keys & TTL**
```javascript
// Example: Use granular keys (e.g., per-ID instead of per-table)
const cacheKey = `user:${userId}:profile`;

// Set appropriate TTL (e.g., 5 mins for frequently changing data)
const ttl = process.env.CACHE_TTL || 300; // Default 5 mins
cache.set(key, data, ttl);
```

#### **Solution: Pre-warm Cache (for critical data)**
```javascript
// Pre-load cache during app startup
async function preWarmCache() {
  const popularUsers = await fetchPopularUsers();
  popularUsers.forEach(user => {
    cache.set(`user:${user.id}:profile`, user.profile, 300);
  });
}
preWarmCache();
```

---

### **Issue 2: Stale Data → Inconsistent UI**
**Symptom:** Frontend shows outdated data even after DB updates.

**Root Cause:**
- Missing **cache invalidation** (e.g., ` cache.del(key)` on DB update).
- Cache key doesn’t reflect version (e.g., missing `v2` suffix).

**Fix:**
#### **Solution: Implement Cache Invalidation**
```javascript
// On DB write, invalidate related cache entries
async function updateUserProfile(userId, newData) {
  await db.updateUserProfile(userId, newData);
  cache.del(`user:${userId}:profile`);
  return newData;
}
```

#### **Solution: Add Versioned Keys**
```javascript
const cacheKey = `user:${userId}:profile:v${version}`;
// Update version on schema changes
```

---

### **Issue 3: Cache Exhaustion → OOM Errors**
**Symptom:** App crashes with `ENOMEM` or `CacheError: over capacity`.

**Root Cause:**
- Unlimited cache size or **missing size limits**.
- **Bloated cache keys** (e.g., serializing entire objects instead of IDs).

**Fix:**
#### **Solution: Set Cache Size Limits**
```javascript
// Redis example: Configure maxmemory policy
redisConfig.maxmemory = "100mb";
redisConfig.maxmemoryPolicy = "allkeys-lru"; // Evict LRU keys
```

#### **Solution: Compress/Serialize Efficiently**
```javascript
// Use JSON.stringify + compression (e.g., zlib) for large data
const compressedData = zlib.sync.compress(JSON.stringify(data));
cache.set(key, compressedData);
```

---

### **Issue 4: Race Conditions → Missing Data**
**Symptom:** Intermittent `null` returns or missing cached data.

**Root Cause:**
- **No cache lock** (multiple processes write simultaneously).
- **Race between read & write** (data is updated while being read).

**Fix:**
#### **Solution: Use Cache Locks**
```javascript
// Redis LUA script for atomic cache set + lock
const lockScript = `
  if redis.call("set", KEYS[1], ARGV[1], "NX", "PX", 5000) then
    return 1
  else
    return 0
  end
`;
const isLocked = await redis.eval(lockScript, 1, cacheKey, JSON.stringify(data));
```

#### **Solution: Implement Read-Through + Write-Through**
```javascript
// First try cache, if miss, fetch + update cache atomically
async function getUserProfile(userId) {
  const cached = await cache.get(`user:${userId}:profile`);
  if (cached) return JSON.parse(cached);

  const dbData = await db.getUserProfile(userId);
  await cache.set(`user:${userId}:profile`, JSON.stringify(dbData), 300);
  return dbData;
}
```

---

## **3. Debugging Tools & Techniques**

### **A. Check Cache Stats**
| **Tool**          | **Command**                          | **Interpretation**                     |
|--------------------|--------------------------------------|-----------------------------------------|
| **Redis CLI**     | `INFO stats`                         | Cache hits/misses, memory usage          |
| **Prometheus**    | `cache_hits_total` vs `cache_misses_total` | Miss rate (% misses = 100 * misses / (hits + misses)) |

**Target:** Miss rate ≤ 10%. If higher, optimize keys/TTL.

### **B. Log Cache Hits/Misses**
```javascript
// Instrument cache calls
const originalGet = cache.get;
cache.get = async (key) => {
  const result = await originalGet(key);
  console.log(`Cache get ${key}: ${result ? 'HIT' : 'MISS'}`);
  return result;
};
```

### **C. Manual Cache Inspection**
```bash
# Redis example: Check all keys
redis-cli --scan --pattern 'user:*'
```

### **D. Cache Throttling (Load Testing)**
```javascript
// Simulate high traffic to detect bottlenecks
await Promise.all(Array(100).fill().map(() => cache.get("testKey")));
```

---

## **4. Prevention Strategies**

### **A. Design Principles**
1. **Cache Granularity:** Cache at the smallest logical unit (e.g., individual rows, not entire tables).
2. **TTL Best Practices:**
   - Short TTL (e.g., 5-30 mins) for frequently changing data.
   - Long TTL (e.g., 1 hour+) for static data.
3. **Invalidation Strategies:**
   - **Time-based:** TTL + re-fetch.
   - **Event-based:** Invalidate on DB write (e.g., using Redis Pub/Sub).

### **B. Monitoring**
- **Alert on high miss rates** (e.g., Prometheus + Alertmanager).
- **Track cache size growth** (e.g., `redis-cli memory usage`).

### **C. Testing**
- **Unit Tests:** Mock cache in tests (e.g., `jest.mock("cache")`).
- **Load Tests:** Use tools like **k6** to simulate traffic.
  ```javascript
  // k6 test for cache behavior
  import http from 'k6/http';
  import { check, sleep } from 'k6';

  export default function () {
    const res = http.get('http://api/users/1');
    check(res, { 'is 200': (r) => r.status === 200 });
    sleep(1); // Force revalidate
  }
  ```

---

## **5. Quick Reference Checklist**
✅ **Symptom:** Slow responses?
   → Check miss rate (`50%+` → optimize keys/TTL).

✅ **Symptom:** Stale data?
   → Audit invalidation (missing `cache.del()`?).

✅ **Symptom:** OOM crashes?
   → Set `maxmemory` + compress cache entries.

✅ **Symptom:** Race conditions?
   → Add cache locks or read-through pattern.

✅ **Prevention:**
   - Instrument cache (logs/stats).
   - Test with load (k6/Prometheus).

---
**Final Tip:** Start with **logs**, then **stats**, then **manual inspection**. Most caching issues boil down to **keys**, **TTL**, or **invalidation**. Keep it simple!