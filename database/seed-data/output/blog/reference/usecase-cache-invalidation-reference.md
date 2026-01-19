**[Pattern] Cache Invalidation Patterns – Reference Guide**

---
### **Overview**
**Cache Invalidation Patterns** define strategies to ensure stale or outdated data is removed from a cache system, maintaining consistency between cached and source data. This pattern is critical for distributed systems where latency-sensitive reads must balance performance with accuracy. Effective invalidation prevents logical inconsistencies, such as serving outdated inventory levels or stale user profiles.

Common invalidation strategies include:
- **Time-based (TTL)**: Automatically expiring entries after a defined duration.
- **Event-based**: Invalidation triggered by upstream system changes (e.g., write operations).
- **Conditional invalidation**: Using metadata (e.g., versioning) to invalidate only relevant data.
- **Delta-based**: Invalidation via incremental data diffs rather than full cache purges.

This guide covers key patterns, trade-offs, and implementation best practices.

---

### **Schema Reference**
| **Component**          | **Description**                                                                 | **Attributes**                                                                 |
|-------------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Cache Entry**         | Data stored in cache (e.g., key-value pairs).                                   | `key` (string), `value` (serialized data), `metadata` (TTL, version, tags) |
| **Invalidation Trigger**| Mechanism that identifies stale data (e.g., update/delete events).               | `source` (system/database), `event_type` (CREATE/UPDATE/DELETE), `payload`  |
| **Invalidation Policy** | Rules defining how/when cache is invalidated.                                  | `strategy` (TTL/event-based/conditional), `scope` (full/partial), `priority`  |
| **Cache Invalidation Service** | Backend responsible for processing invalidation triggers.               | `listeners` (event subscriptions), `queues` (asynchronous processing), `sync` (real-time) |

---

### **Key Invalidation Patterns**
#### **1. Time-Based (TTL) Invalidation**
- **How it works**: Cache entries expire after a fixed or dynamic timeout.
- **Use case**: Read-heavy workloads with occasional writes (e.g., product catalogs).
- **Trade-offs**:
  - *Pros*: Simple, scalable, no coordination needed.
  - *Cons*: May serve stale data during expiration.

| **Schema Example** | `TTL` (seconds), `max_age` (dynamic calculation) |
|--------------------|----------------------------------------------------|
| **Example**        | `{ "key": "user:123", "value": {...}, "metadata": { "ttl": 3600 } }` |

#### **2. Event-Based Invalidation**
- **How it works**: Cache is invalidated upon write events (e.g., database mutations).
- **Use case**: Critical data (e.g., financial transactions, user sessions).
- **Trade-offs**:
  - *Pros*: Real-time consistency.
  - *Cons*: Requires event bus integration (e.g., Kafka, Webhooks).

| **Event Trigger**      | `event_type: "UPDATE"`, `table: "products"`, `primary_key: "id"` |
|------------------------|-------------------------------------------------------------------|
| **Example**            | ```json { "source": "db", "table": "users", "action": "UPDATE", "key": "user:456" } ``` |

#### **3. Conditional Invalidation**
- **How it works**: Invalidation only for keys meeting criteria (e.g., version tags).
- **Use case**: Optimistic concurrency control (e.g., distributed locks).
- **Trade-offs**:
  - *Pros*: Granular control.
  - *Cons*: Complex implementation (e.g., version tracking).

| **Metadata Schema**   | `version: "v2"`, `tags: ["status:active"]` |
|-----------------------|--------------------------------------------|
| **Example**           | Cache invalidates only keys with `version: "v2"` after a write. |

#### **4. Delta-Based Invalidation**
- **How it works**: Partial invalidation via incremental data changes (e.g., diff logs).
- **Use case**: Large datasets (e.g., analytics dashboards).
- **Trade-offs**:
  - *Pros*: Efficient for high-cardinality data.
  - *Cons*: Requires diff tracking (e.g., database triggers).

| **Delta Schema**      | `[ { "key": "metric:q1_2023", "op": "UPDATE", "delta": { "value": 10 } } ]` |
|-----------------------|---------------------------------------------------------------------|
| **Implementation**    | Use database triggers to emit deltas on write operations. |

---

### **Implementation Details**
#### **System Architecture**
1. **Cache Layer**: Key-value store (Redis, Memcached) with metadata support.
2. **Event Bus**: Asynchronous events (e.g., Kafka topics) for event-based invalidation.
3. **Invalidation Service**: Processes triggers via:
   - **Synchronous**: Direct cache API calls (e.g., `cache.invalidate(key)`).
   - **Asynchronous**: Queues (e.g., RabbitMQ) for batch invalidation.

#### **Code Example (TTL Invalidation in Redis)**
```python
import redis

# Initialize cache with TTL
cache = redis.Redis()
cache.setex(
    "user:456",
    3600,  # 1-hour TTL
    '{"name": "Alice"}'
)
```

#### **Event-Based Invalidation (Pseudocode)**
```javascript
// Listener for DB updates
app.on("db_update", (event) => {
    if (event.table === "users" && event.action === "UPDATE") {
        cache.invalidate(`user:${event.key}`);
    }
});
```

---

### **Query Examples**
#### **1. Invalidating a Single Key**
```sql
-- Redis CLI
DEL user:456
```
#### **2. Bulk Invalidation (Event-Based)**
```json
// Kafka Consumer (JSON)
{ "keys": [ "user:101", "user:102" ], "reason": "account_merge" }
```
#### **3. Conditional Invalidation (SQL)**
```sql
-- Trigger on UPDATE
CREATE TRIGGER invalidate_user_cache
AFTER UPDATE ON users
FOR EACH ROW BEGIN
    CALL cache.invalidate('user:%v', NEW.id);
END;
```

---

### **Performance Considerations**
- **TTL Strategy**:
  - Set TTLs based on data volatility (e.g., 1h for news, 8h for static content).
  - Monitor cache hit ratios to adjust TTL dynamically.
- **Event-Based**:
  - Debounce rapid invalidations (e.g., batch user updates).
  - Use a distributed lock (e.g., Redis `SET` with `NX`) to avoid race conditions.
- **Delta-Based**:
  - Optimize diff storage (e.g., Merkle trees for large datasets).

---

### **Fault Tolerance**
| **Scenario**               | **Mitigation**                                                                 |
|----------------------------|-------------------------------------------------------------------------------|
| Cache service downtime     | Implement fallback to database (e.g., `cache-first` pattern).                |
| Event bus failure          | Idempotent triggers (e.g., retry with deduplication via IDs).                |
| Network partitions         | Async invalidation with acknowledgments (e.g., Kafka `offsets`).               |

---

### **Related Patterns**
1. **[Cache-Aside (Lazy Loading)](https://microservices.io/patterns/data/cache-aside.html)**
   - Complements invalidation by only populating cache on demand.
2. **[Write-Through Cache](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)**
   - Updates cache *and* database simultaneously to avoid inconsistencies.
3. **[Distributed Cache for State](https://martinfowler.com/eaaCatalog/cache.html)**
   - Extends invalidation to session/transient state in microservices.
4. **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)**
   - Enables precise invalidation via immutable event logs.

---
### **Anti-Patterns to Avoid**
- **Blind Purge**: Invalidate entire cache partitions (e.g., `cache.clear()`) instead of granular keys.
- **Static TTLs**: Hardcoded TTLs ignore data volatility (e.g., always 1 hour).
- **No Monitoring**: Lack of metrics for cache hit ratios or invalidation delays.

---
**Further Reading**:
- [Redis Invalidation Docs](https://redis.io/docs/reference/patterns/caching/)
- [Event Sourcing Invalidations](https://www.eventstore.com/blog/event-sourcing-invalidation-patterns)