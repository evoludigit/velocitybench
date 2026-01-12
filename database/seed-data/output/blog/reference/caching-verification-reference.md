# **[Pattern] Caching Verification Reference Guide**

---

## **1. Overview**
The **Caching Verification** pattern ensures data consistency between cached and live database values by validating whether cached copies need updates. This pattern is critical for microservices, high-traffic APIs, and systems where stale cache data could lead to inconsistencies. By implementing periodic or event-driven verification checks, applications maintain accurate cache integrity with minimal overhead, improving performance and reliability.

Common use cases include:
- **E-commerce:** Real-time product inventory validation.
- **IoT:** Device state synchronization.
- **Financial Systems:** Account balance verification.
- **Content Delivery:** Dynamic content updates (e.g., blog posts, ads).

---

## **2. Key Concepts**

| **Term**               | **Definition**                                                                                     |
|------------------------|---------------------------------------------------------------------------------------------------|
| **Cache Layer**        | In-memory storage (e.g., Redis, Memcached) for fast data retrieval.                              |
| **Live DB**            | Primary data source (e.g., PostgreSQL, MongoDB) with authoritative values.                       |
| **TTL (Time-to-Live)** | Expiry duration for cached entries before automatic revalidation.                                |
| **Verification Trigger** | Event (e.g., cache miss, TTL expiry) or schedule (e.g., cron job) to check cache validity.      |
| **Consistency Window** | Timeout allowed for cache updates to propagate to the live DB (e.g., 500ms).                   |
| **Sync Policy**        | Rules defining how conflicts are resolved (e.g., overwrite, merge, or notify stakeholders).      |

---

## **3. Schema Reference**

### **Core Objects**
| **Object**         | **Fields**                                                                                     | **Description**                                                                           |
|--------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **CacheEntry**     | `key` (string), `value` (JSON), `version` (int), `ttl` (millis), `lastUpdated` (timestamp)   | Represents a cached data entry with metadata for verification.                          |
| **LiveDBRecord**   | `key` (string), `value` (JSON), `version` (int), `lastModified` (timestamp)                 | Corresponding live DB entry for validation.                                             |
| **VerificationJob**| `id` (UUID), `entryKey` (string), `scheduledTime` (timestamp), `status` ("PENDING\|COMPLETE") | Tracks verification tasks (e.g., cron jobs or async tasks).                              |

---

### **Example Schema (JSON)**
```json
// CacheEntry
{
  "key": "product:123",
  "value": {"price": 99.99, "stock": 10},
  "version": 3,
  "ttl": 3600000, // 1 hour
  "lastUpdated": "2023-10-01T12:00:00Z"
}

// LiveDBRecord (PostgreSQL example)
SELECT * FROM products WHERE id = '123';
-- Returns: {price: 99.99, stock: 9, version: 4, lastModified: "2023-10-01T12:05:00Z"}
```

---

## **4. Implementation Steps**

### **Step 1: Define Verification Logic**
```python
def verify_cache(entry: CacheEntry, live_record: LiveDBRecord) -> bool:
    # Check if live data is newer or version differs
    if (live_record.lastModified > entry.lastUpdated or
        live_record.version != entry.version):
        update_cache(entry.key, live_record.value, live_record.version)
        return False  # Cache was stale
    return True  # Cache is valid
```

### **Step 2: Trigger Verification**
| **Trigger Type**       | **Implementation**                                                                             |
|------------------------|-----------------------------------------------------------------------------------------------|
| **TTL Expiry**         | Use Redis `EXPIRE` + Lua script to validate on eviction.                                      |
| **Cache Miss**         | Fallback to DB on miss, then verify during population (e.g., `getWithFallback` pattern).    |
| **Event-Driven**       | Publish `CacheInvalidate` event on DB writes; trigger revalidation.                          |
| **Scheduled**          | Cron job (e.g., `every 5 minutes`) to poll all cache entries.                                |

**Example (Redis Lua Script for TTL Verification):**
```lua
local key = KEYS[1]
local entry = redis.call('GET', key)
if not entry then return 0 end  -- Cache miss

local parsed = cjson.decode(entry)
local live_data = redis.call('GET', 'live:' .. key)
if live_data then
    local live = cjson.decode(live_data)
    if (live.lastModified > parsed.lastUpdated or live.version ~= parsed.version) then
        redis.call('SET', key, live_data, 'EX', parsed.ttl/1000)  -- Re-save if stale
    end
end
return 1
```

---

### **Step 3: Handle Conflict Resolution**
| **Conflict Scenario**          | **Resolution Strategy**                                                                       |
|--------------------------------|---------------------------------------------------------------------------------------------|
| **Live DB newer**              | Overwrite cache with live DB value.                                                          |
| **Cache newer**                | Merge changes (if supported) or log a warning.                                              |
| **Version mismatch**           | Reject cache update; require manual intervention or retry.                                  |
| **Consistency window exceeded**| Fall back to DB-only mode or notify operators.                                             |

**Example (Sync Policy in Code):**
```javascript
function handleSyncConflict(cacheValue, liveValue) {
  if (liveValue.lastModified > cacheValue.lastUpdated) {
    // Live wins (overwrite)
    cacheStore.set(key, liveValue);
  } else if (liveValue.version === cacheValue.version) {
    // No conflict (do nothing)
  } else {
    // Version mismatch: Log and notify
    logger.warn(`Conflict for ${key}: cache=${cacheValue.version}, db=${liveValue.version}`);
  }
}
```

---

## **5. Query Examples**

### **Query 1: Verify Cache on Startup**
```sql
-- Check all products in cache against live DB
SELECT p.id, pe.value, p.version, p.lastModified
FROM products p
JOIN cache_entries pe ON p.id = pe.entryKey
WHERE pe.lastUpdated < p.lastModified;
```

**Output:**
| `id` | `pe.value`               | `p.version` | `p.lastModified`       | **Action**          |
|------|--------------------------|-------------|------------------------|---------------------|
| 123  | {"stock": 10}            | 4           | 2023-10-01T12:05:00Z   | **Update Cache**    |

---

### **Query 2: Event-Driven Revalidation**
**Trigger (DB Write):**
```python
# Pseudo-code for PostgreSQL trigger
CREATE TRIGGER revalidate_cache
AFTER UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION revalidate_cache_entry(NEW.id);
```

**Function (Python):**
```python
def revalidate_cache_entry(product_id: str) -> None:
    live_record = db.get_product(product_id)
    cache_key = f"product:{product_id}"
    cache_entry = cache.get(cache_key)

    if cache_entry and not verify_cache(cache_entry, live_record):
        cache.set(cache_key, live_record.value, ttl=3600)
```

---

### **Query 3: Scheduled Verification (Cron Job)**
```bash
# Linux cron job (runs every 60 seconds)
*/1 * * * * python3 -c "
  from caching_verify import verify_all_entries
  verify_all_entries()
"
```

**Python Implementation:**
```python
def verify_all_entries() -> None:
    cache_entries = cache.scan_matches("product:*")
    for entry_key in cache_entries:
        live_record = db.get(entry_key.replace('product:', ''))
        if not verify_cache(cache.get(entry_key), live_record):
            print(f"Updated: {entry_key}")
```

---

## **6. Performance Considerations**

| **Optimization**               | **Description**                                                                               |
|---------------------------------|-----------------------------------------------------------------------------------------------|
| **Batch Verification**          | Process multiple cache entries in a single DB query (e.g., `IN` clause).                    |
| **Lazy Validation**             | Only verify on cache hit (not on every request).                                             |
| **Probabilistic Verification**  | Sample a subset of cache entries (e.g., 10%) to reduce DB load.                              |
| **Cache Partitioning**          | Shard cache keys by entity type (e.g., `user:*`, `product:*`) for parallel validation.     |
| **TTL Tuning**                  | Balance between stale reads and write overhead (e.g., TTL = 50% of DB update frequency).    |

**Example (Batch Verification in SQL):**
```sql
-- Verify multiple products at once
SELECT * FROM products
WHERE id IN (
    SELECT entryKey FROM cache_entries
    WHERE lastUpdated < NOW() - INTERVAL '1 minute'
);
```

---

## **7. Error Handling & Retries**
| **Scenario**                 | **Action**                                                                                   |
|------------------------------|---------------------------------------------------------------------------------------------|
| **DB Unavailable**           | Queue verification for later (e.g., using a task queue like RabbitMQ).                      |
| **Cache Corruption**         | Fall back to DB-only mode; log for manual review.                                           |
| **Timeout Errors**           | Implement exponential backoff (e.g., retry after 1s, 2s, 4s).                                |
| **Version Skew**             | Use optimistic concurrency control (e.g., `version` field) to detect races.               |

**Example (Retry Logic):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def verify_with_retry(entry_key: str) -> bool:
    try:
        return verify_cache(cache.get(entry_key), db.get(entry_key))
    except DBTimeoutError:
        raise  # Will retry
```

---

## **8. Related Patterns**

| **Pattern**                  | **Purpose**                                                                                   | **When to Combine**                                                                       |
|------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **[Cache-Aside](https://microservices.io/patterns/data/cache-aside.html)** | Load data into cache on demand.                                                              | Use to populate cache before verification.                                               |
| **[Read-Through](https://microservices.io/patterns/data/read-through-cache.html)** | Automatically populate cache on read.                                                      | Ideal for event-driven revalidation (e.g., after DB writes).                            |
| **[Write-Through](https://microservices.io/patterns/data/write-through-cache.html)** | Update cache on every write.                                                                  | Ensures cache stays in sync with DB (but adds write latency).                            |
| **[Write-Behind](https://microservices.io/patterns/data/write-behind-cache.html)** | Asynchronously update cache after DB writes.                                                 | Reduces write overhead; pair with scheduled verification to catch delays.               |
| **[Circuit Breaker](https://microservices.io/patterns/reliability/circuit-breaker.html)** | Fail fast if DB is unavailable during verification.                                          | Protects from cascading failures during cache revalidation.                              |
| **[Retry with Backoff](https://microservices.io/patterns/reliability/retry.html)**          | Handle transient DB errors during verification.                                              | Use for resilient verification in distributed systems.                                   |
| **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)**              | Track changes via events for precise cache invalidation.                                     | Complementary for audit trails and complex sync policies.                                |

---
## **9. References**
1. **Microservices Patterns**: [Cache Aside](https://microservices.io/patterns/data/cache-aside.html)
2. **Redis Best Practices**: [Cache Invalidation Strategies](https://redis.io/topics/invalidation)
3. **PostgreSQL Triggers**: [Documentation](https://www.postgresql.org/docs/current/plpgsql-trigger.html)
4. **Tenacity Retry Library**: [GitHub](https://github.com/jd/tenacity)

---
**Last Updated:** `2023-10-01`
**Version:** `1.0`