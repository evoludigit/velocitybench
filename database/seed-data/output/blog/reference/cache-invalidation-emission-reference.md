**[Pattern] Cache Invalidation Emission Reference Guide**

---

### **Overview**
The **Cache Invalidation Emission** pattern ensures data consistency between cached state and the underlying data source by emitting events whenever mutations (e.g., CRUD operations) make cached data stale. This decouples invalidation logic from the mutation itself, allowing consumers (e.g., client apps, analytics tools) to proactively update their caches or fetch fresh data. The pattern is typically used in distributed systems with eventual consistency requirements (e.g., microservices, GraphQL APIs, or reactive applications).

Key benefits include:
- **Decoupled invalidation**: Mutations emit events rather than directly triggering invalidation.
- **Flexible consumption**: Subscribers can invalidate caches or trigger refetches based on their needs.
- **Efficiency**: Avoids redundant invalidations by using targeted event filtering (e.g., only invalidate specific cache keys).
- **Extensibility**: Events can include metadata (e.g., `cache-ttl`, `scope`) to guide consumers.

This pattern is commonly paired with **Cache-Aside** or **Read-Through** patterns and supports architectures like **CQRS**, **Event Sourcing**, or **GraphQL subscriptions**.

---

### **Schema Reference**
Below are the core components of the pattern, represented in a schema-like table for clarity.

| **Category**       | **Field**               | **Type**               | **Description**                                                                                     | **Example Values**                          |
|--------------------|-------------------------|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Event**          | `eventType`             | `String` (enum)        | Identifies the mutation type that triggered invalidation (e.g., `create`, `update`, `delete`).        | `"update"`, `"delete:post/123"`              |
|                    | `resourceType`          | `String`               | The type of resource affected (e.g., `user`, `order`).                                               | `"user"`, `"product"`                       |
|                    | `resourceId`            | `String` / `UUID`      | Unique identifier of the mutated resource (optional for bulk operations).                           | `"550e8400-e29b-41d4-a716-446655440000"`     |
|                    | `timestamp`             | `ISO 8601`             | When the mutation occurred (for eventual consistency tracking).                                     | `"2023-10-15T14:30:00Z"`                   |
|                    | `version`               | `Integer`              | Cache version or sequence number to handle concurrent updates.                                      | `42`                                        |
| **Cache Scope**    | `cacheKeys`             | `Array[String]`        | List of cache keys or patterns to invalidate (e.g., `user:123`, `posts:*`).                        | `["user:123", "comments:post:123"]`         |
|                    | `cacheGroup`            | `String`               | Logical grouping of related cache keys (e.g., `user-profile`, `inventory`).                        | `"user-profile"`                            |
|                    | `ttlOverrides`          | `Object`               | Custom TTL or invalidation rules for specific keys.                                                  | `{"comments:post:123": 3600}`               |
| **Metadata**       | `correlationId`         | `String`               | Unique ID to trace the event across systems (e.g., for audit logs).                                | `"abc123-xyz789"`                           |
|                    | `sourceSystem`          | `String`               | Origin of the event (e.g., `backend-api`, `external-service`).                                       | `"backend-api"`                              |
| **Payload**        | `mutationData`          | `Object`               | Optional payload containing details of the mutation (e.g., updated fields).                        | `{ "name": "John Doe", "email": "john@example.com" }` |

---

### **Event Types and Scopes**
Invalidation events are emitted for specific mutations. Below are common patterns:

| **Event Type**               | **Cache Keys to Invalidate**                          | **Example**                                  |
|------------------------------|-------------------------------------------------------|----------------------------------------------|
| `create:user/123`            | `user:123`, `users:list`, `dashboard:user-summary`     | New user created.                            |
| `update:post/456`            | `post:456`, `post:456:comments`, `feed:user:789`       | Post title updated; affects comments and feed.|
| `delete:order/789`           | `order:789`, `user:123:orders`, `inventory:productA`   | Order deleted; may affect inventory.          |
| `bulk:update:products`       | `products:list`, `products:search`                    | Batch price update.                          |
| `reconciliation:user/123`    | `user:123`, `user:123:transactions`                   | External sync resolved discrepancies.         |

---

### **Implementation Details**
#### **1. Emitting Events**
Events are emitted **after** a mutation completes but **before** returning a response to the client. This ensures the database/primary source is updated.

**Example (Pseudocode - Node.js/Express):**
```javascript
app.post("/users/:id", async (req, res) => {
  const user = await userService.update(req.params.id, req.body);
  // Emit invalidation event AFTER updating the DB
  io.emit("cache:invalidated", {
    eventType: `update:user/${user.id}`,
    cacheKeys: ["user:${user.id}", "users:list"],
    version: getNextCacheVersion(),
  });
  res.json(user);
});
```

#### **2. Consuming Events**
Consumers (e.g., client apps, cache layers) subscribe to events and act on them. Common strategies:
- **Direct Cache Invalidation**: Delete or update cache entries matching `cacheKeys`.
- **Lazy Refetch**: Mark keys as stale and refetch on next access.
- **Event-Driven UI Updates**: Update UI components without polling (e.g., WebSocket subscribers).

**Example (Cache Layer - Redis):**
```bash
# Subscribe to invalidation events
SUBSCRIBE cache:invalidated

# On message, delete keys
127.0.0.1:6379> DEL user:123 comments:post:123
```

#### **3. Event Delivery Mechanisms**
| **Mechanism**       | **Use Case**                                  | **Pros**                          | **Cons**                          |
|---------------------|-----------------------------------------------|-----------------------------------|-----------------------------------|
| **Pub/Sub (Redis, Kafka)** | High-throughput systems.                     | Scalable, decoupled.              | Eventual consistency.             |
| **WebSockets**      | Real-time UI updates (e.g., live dashboards).| Low latency.                      | Harder to scale.                  |
| **HTTP Polling**    | Simple integrations (e.g., mobile apps).      | Easy to implement.                | Polling overhead.                 |
| **Database Triggers** | Tightly coupled to a specific DB.           | No external dependency.           | Limited to supported databases.   |

#### **4. Handling Event Ordering**
In distributed systems, events may arrive out of order. Solutions:
- **Sequence Numbers**: Include a `version` field to detect stale events.
- **Idempotency**: Design consumers to handle duplicate events (e.g., Redis `DEL` is idempotent).
- **Transactional Outbox**: Group events in a transactional queue (e.g., Kafka `txid`).

**Example (Idempotent Consumer):**
```python
def handle_invalidation(event):
    if event["version"] <= last_processed_version:
        return  # Skip if already processed
    for key in event["cacheKeys"]:
        cache.delete(key)  # Idempotent operation
    last_processed_version = event["version"]
```

#### **5. Event Filtering**
Consumers often don’t need all events. Use:
- **Wildcards**: Subscribe to `update:user:*` instead of all events.
- **Metadata Fields**: Filter by `sourceSystem` or `correlationId`.
- **Cache Grouping**: Subscribe to `cacheGroup:user-profile` for scoped invalidations.

**Example (Filtering with Kafka):**
```bash
# Subscribe only to user-related events
kafka-consumer --topic cache-invalidated --filter "eventType like 'update:user%'"
```

#### **6. Performance Considerations**
- **Batching**: Combine multiple invalidations into a single event (e.g., `bulk:update:users`).
- **Compression**: For high-volume systems, compress payloads (e.g., Protobuf).
- **Backpressure**: Implement rate limiting for consumers to avoid overwhelming them.

---

### **Query Examples**
#### **1. Subscribing to Invalidation Events (WebSocket)**
```websocket
# Client subscribes to user updates
SUBSCRIBE cache:invalidated filter='eventType = "update:user/*"'

# Server responds with an event
{
  "eventType": "update:user/123",
  "cacheKeys": ["user:123", "users:list"],
  "timestamp": "2023-10-15T14:30:00Z"
}
```

#### **2. Invalidate Cache Keys (Redis)**
```bash
# Server emits event
SUBSCRIBE cache:invalidated

# On event, client deletes keys
127.0.0.1:6379> DEL user:123
(integer) 1
```

#### **3. Lazy Refetch Strategy (Client Side)**
```javascript
// Track stale keys
const STALE_KEYS = new Set();

io.on("cache:invalidated", (event) => {
  event.cacheKeys.forEach(key => STALE_KEYS.add(key));
});

// On next fetch, check for stale keys
async function fetchUser(id) {
  const cacheKey = `user:${id}`;
  if (STALE_KEYS.has(cacheKey)) {
    const freshData = await api.fetchUser(id);
    STALE_KEYS.delete(cacheKey);
    return freshData;
  }
  return cache.get(cacheKey);
}
```

#### **4. Event-Driven UI Update (React)**
```jsx
import { useEffect } from 'react';

function UserProfile({ userId }) {
  useEffect(() => {
    const subscription = io.connect().subscribe(
      `cache:invalidated eventType = "update:user/${userId}"`,
      (event) => {
        // Update UI or refetch data
        refetchUserProfile(userId);
      }
    );

    return () => subscription.unsubscribe();
  }, [userId]);

  return <div>{/* Profile UI */}</div>;
}
```

---

### **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Cache-Aside](https://docs.mermaidjs.com/syntax/caching)** | Load data from cache; if missing, fetch from DB and update cache.               | Simple caching with fallback to database.       |
| **[Read-Through](https://docs.mermaidjs.com/syntax/caching)** | Cache is populated on every read (e.g., via a proxy).                          | High read-to-write ratio scenarios.             |
| **[Write-Behind](https://docs.mermaidjs.com/syntax/caching)** | Write operations are async and cached immediately.                             | Performance-critical write-heavy systems.       |
| **[Event Sourcing](https://docs.mermaidjs.com/syntax/event-sourcing)** | Store state changes as a sequence of events.                                   | Audit trails, time-travel debugging.            |
| **[CQRS](https://docs.merriadjs.com/syntax/cqrs)**            | Separate read and write models (often with cached views).                     | Complex query patterns (e.g., analytics).        |
| **[Optimistic Locking](https://docs.mermaidjs.com/syntax/concurrency)** | Assume mutations succeed; handle conflicts on failure.                        | Offline-first apps or high-contention systems.  |
| **[GraphQL Subscriptions](https://docs.mermaidjs.com/syntax/graphql)** | Real-time updates for GraphQL clients.                                        | Interactive dashboards or live collaboration.    |

---

### **Anti-Patterns & Pitfalls**
1. **Blocking on Invalidation**:
   - *Avoid*: Emitting events synchronously during a mutation (causes latency).
   - *Fix*: Use async event buses (e.g., Kafka, Redis Pub/Sub).

2. **Over-Invalidation**:
   - *Avoid*: Invalidate all caches for every mutation (e.g., `delete:user/123` → clear `posts:*`).
   - *Fix*: Scope invalidations to affected data (e.g., only invalidate `user:123:posts`).

3. **Ignoring Event Order**:
   - *Avoid*: Assuming events arrive in mutation order.
   - *Fix*: Use sequence numbers or idempotent consumers.

4. **Tight Coupling to Cache**:
   - *Avoid*: Baking cache invalidation into business logic (violates separation of concerns).
   - *Fix*: Treat invalidation as a cross-cutting concern (e.g., decorators, middleware).

5. **No Fallback for Failed Invalidation**:
   - *Avoid*: Assuming invalidation will always succeed.
   - *Fix*: Implement retries with backoff (e.g., for down cache services).

---

### **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                 | **Example Use Case**                          |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Redis Pub/Sub**         | In-memory event bus with low latency.                                      | Real-time cache synchronization.              |
| **Apache Kafka**          | Distributed event streaming with persistence.                              | High-volume audit logs.                       |
| **NATS**                  | Lightweight messaging for microservices.                                   | Decoupled service communication.              |
| **GraphQL Subscriptions** | Real-time GraphQL updates via WebSockets.                                  | Live UI updates (e.g., Slack notifications).   |
| **JCache (Java)**         | Standard API for caching (supports invalidation listeners).                | Java EE/Jakarta EE applications.              |
| **RedisTemplate (Spring)**| Spring integration for Redis invalidation events.                          | Spring Boot apps.                             |
| **AWS EventBridge**       | Serverless event bus for AWS services.                                     | Multi-service invalidation pipelines.         |

---
### **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │    │             │
│   Client    │───▶│   API       │───▶│   DB        │    │  Cache      │
│             │    │  (Express)  │    │  (PostgreSQL)│    │  (Redis)    │
└─────────────┘    └─────────────┘    └─────────────┘    └───────┬───────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│   Kafka     │───▶│   Consumer  │───▶│   UI        │
│  (Topic:    │    │  (Node.js)  │    │  (React)    │
│   cache-    │    │             │    │             │
│   invalid- │───▶│             │───▶│             │
│   ated)     │    └─────────────┘    └─────────────┘
└─────────────┘
```

---
### **Key Takeaways**
1. **Decouple**: Mutations emit events; consumers handle invalidation.
2. **Scope Events**: Use `cacheKeys`, `cacheGroup`, and `eventType` to target invalidations.
3. **Support Scalability**: Use async event buses (e.g., Kafka, Redis Pub/Sub) for high throughput.
4. **Handle Ordering**: Use sequence numbers or idempotent consumers for eventual consistency.
5. **Monitor**: Track event delivery latency and invalidation success rates.