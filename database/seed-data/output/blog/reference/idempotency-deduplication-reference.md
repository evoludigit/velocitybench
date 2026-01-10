---
# **[Pattern] Idempotency & Deduplication – Reference Guide**
*Ensure safe retries and prevent duplicate operations in distributed systems.*

---

## **1. Overview**
Distributed systems often require clients to retry failed requests due to network instability, timeouts, or temporary server unavailability. Without safeguards, these retries can lead to **duplicate operations**—e.g., duplicate payments, redundant data inserts, or concurrent updates that overwrite intended state.

This pattern addresses the problem by enforcing two core principles:
- **Idempotency**: Ensures a request can be safely retried without altering system state (e.g., `PUT /orders/{id}` is safe to repeat).
- **Deduplication**: Prevents duplicates when idempotency isn’t feasible (e.g., time-sensitive operations like event processing), by tracking and discarding redundant requests.

Together, they eliminate side effects from retries while maintaining data consistency.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Idempotency**
**Definition**: An operation is *idempotent* if invoking it multiple times produces the same result as invoking it once.

**Use Cases**:
- **Safe State Transitions**: Operations like `POST /orders` (create), `PUT /orders/{id}` (update), or `DELETE /orders/{id}` (delete) can be retried.
- **Resource Allocation**: Duplicate payments or reservations (e.g., flights, hotel rooms) must be avoided.

**Implementation Strategies**:
| Approach               | Description                                                                                     | Example Use Case                          |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Idempotency Key**    | Clients generate a unique key (e.g., UUID) to track retries; servers validate it on each call. | `PUT /orders/123?idempotency_key=abc123`   |
| **Server-Side Tracking** | Servers maintain a cache (e.g., Redis) of processed requests by key.                          | Block duplicate `POST /payments` calls.   |
| **Versioned Resources** | Use ETag/If-None-Match headers to detect unchanged states.                                         | `PUT /profile` with `If-Match: ETag=abc` |

**Tradeoffs**:
- **Pros**: Simple, widely applicable (e.g., REST APIs).
- **Cons**: Requires client cooperation (key generation); server storage overhead.

---

### **2.2 Deduplication**
**Definition**: Mechanisms to detect and ignore duplicate operations when idempotency isn’t possible (e.g., time-critical events).

**Use Cases**:
- **Event Processing**: Duplicate messages in Kafka/RabbitMQ queues.
- **Time-Sensitive Actions**: Retries on `POST /webhooks` must not trigger duplicate effects.
- **Event Sourcing**: Duplicate event writes can corrupt state.

**Implementation Strategies**:
| Approach               | Description                                                                                     | Example Use Case                          |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Message Deduplication** | Use message IDs or timestamps to drop duplicates (e.g., Kafka `max.in.flight.requests.per.connection`). | Kafka consumers ignore `duplicate=true`  |
| **Server-Side Hashing** | Hash payloads (e.g., MD5) and compare against a deduplication table (e.g., PostgreSQL `UNIQUE` constraints). | Block duplicate `POST /events` by `hash(payload)`. |
| **Client-Side Tracking** | Clients track processed IDs and skip duplicates (e.g., `lastProcessedId` in pagination).      | Paginated API retries.                   |

**Tradeoffs**:
- **Pros**: Works for non-idempotent operations; low client overhead.
- **Cons**: Server storage required; false positives if hashing collides.

---

### **2.3 Hybrid Approach**
Combine both patterns for robustness:
1. **Client generates an idempotency key** for retriable requests.
2. **Server deduplicates** all requests (idempotent or not) using a hash or ID.
3. **Idempotency key takes precedence** for reprocessing (e.g., retrying a failed `POST /payment`).

**Example Workflow**:
```
Client → POST /payment (idempotency_key=123)
Server → Checks Redis for key=123 → Returns 200 (success)
Client → Network fails → Retries with same key → Server returns 200 (idempotent)
```

---

## **3. Schema Reference**
### **3.1 Idempotency Key Schema**
| Field            | Type   | Description                                                                 | Example                     |
|------------------|--------|-----------------------------------------------------------------------------|-----------------------------|
| `idempotency_key` | string | Unique identifier for tracking retries.                                    | `uuid4()` or `sha256(request_body)` |
| `expires_at`     | date   | TTL for the key (prevents stale retries).                                 | `2024-01-01T00:00:00Z`      |
| `status`         | enum   | `pending`/`completed`/`failed` (for server-side tracking).                 | `completed`                 |

**Redis Example**:
```redis
SET payment:123 "{\"key\":\"123\",\"status\":\"completed\"}" EX 86400
```

---

### **3.2 Deduplication Table Schema**
| Field          | Type    | Description                                                                 | Example                     |
|----------------|---------|-----------------------------------------------------------------------------|-----------------------------|
| `request_id`   | string  | Unique message/operation ID (e.g., Kafka message ID).                      | `msg_12345`                 |
| `payload_hash` | string  | Hash of the request payload (e.g., SHA-256).                               | `5e884898da28047151d0e56f8...` |
| `processed_at` | timestamp| When the request was processed (for TTL-based cleanup).                    | `2024-01-01 12:00:00 UTC`   |
| `is_idempotent`| boolean | Flag if the operation supports idempotency.                                | `true`                      |

**PostgreSQL Example**:
```sql
CREATE TABLE deduplicated_requests (
    request_id VARCHAR(255) PRIMARY KEY,
    payload_hash VARCHAR(64) NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    is_idempotent BOOLEAN DEFAULT false,
    EXCLUDE (payload_hash WITH =)
);
```

---

## **4. Query Examples**
### **4.1 Idempotency Endpoint (REST API)**
**Request**:
```http
PUT /orders/123
Idempotency-Key: abc123
Content-Type: application/json

{
  "status": "shipped",
  "tracking_number": "TRK456"
}
```

**Server Logic (Pseudocode)**:
```python
def handle_request(request):
    key = request.headers["Idempotency-Key"]
    if not redis.exists(f"idempotency:{key}"):
        # Process request
        update_order(request.body)
        redis.setex(f"idempotency:{key}", 86400, "completed")
        return 200
    return 200  # Idempotent; return previous response
```

**Response**:
```http
HTTP/1.1 200 OK
{
  "message": "Order updated (idempotent retry)"
}
```

---

### **4.2 Deduplication (Event Processing)**
**Kafka Consumer (Python)**:
```python
from kafka import KafkaConsumer
import hashlib

consumer = KafkaConsumer('orders-topic')
dedup_cache = set()

def process_event(event):
    payload_hash = hashlib.sha256(event.value).hexdigest()
    if payload_hash not in dedup_cache:
        dedup_cache.add(payload_hash)
        # Process event (e.g., create order)
        print(f"Processing: {event.value}")
```

**PostgreSQL Deduplication (SQL)**:
```sql
-- Insert only if not duplicate
INSERT INTO deduplicated_requests (request_id, payload_hash, processed_at, is_idempotent)
VALUES ('msg_123', SHA256('{"event":"order_created"}'), NOW(), true)
ON CONFLICT (payload_hash) DO NOTHING;
```

---

## **5. Error Handling & Edge Cases**
| Scenario                     | Solution                                                                 |
|------------------------------|--------------------------------------------------------------------------|
| **Idempotency key collision** | Use UUIDs or timestamp-based keys; log collisions for analysis.           |
| **Expired keys**              | Clients should retry with new keys after TTL expires.                     |
| **Network partition**        | Implement circuit breakers (e.g., Retry-After header) for failed retries.|
| **Malicious duplicates**     | Rate-limit idempotency keys to prevent abuse.                            |
| **Schema drift**             | Validate payloads against a schema (e.g., JSON Schema) before deduplication. |

---

## **6. Benchmarking & Optimization**
| Metric               | Idempotency Key | Deduplication Table | Hybrid Approach |
|----------------------|-----------------|----------------------|-----------------|
| **Server latency**   | Low (Redis lookup) | Medium (DB query)    | Medium          |
| **Storage overhead** | Low (key-value)  | High (table + index) | High            |
| **Throughput**       | High            | Medium               | Medium-High     |

**Optimizations**:
- **Idempotency**: Use Redis for low-latency key tracking.
- **Deduplication**: Add a `payload_hash` index to PostgreSQL for faster lookups.
- **Hybrid**: Tag idempotent requests in the deduplication table for prioritized processing.

---

## **7. Related Patterns**
| Pattern                  | Description                                                                                     | When to Use                                      |
|--------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Retry with Backoff**   | Exponential backoff for retries to avoid thundering herds.                                      | Network instability scenarios.                  |
| **Saga Pattern**         | Manage distributed transactions with compensating actions.                                     | Microservices with complex workflows.           |
| **Idempotent Workflows** | End-to-end idempotency for long-running processes (e.g., payments).                             | Critical payment flows.                          |
| **Event Sourcing**       | Store state changes as immutable events; replay for deduplication.                                | Auditable, replayable systems.                   |
| **CQRS**                 | Separate read/write models to handle inconsistencies during retries.                              | High-concurrency write-heavy systems.            |

---

## **8. Tools & Libraries**
| Tool/Library               | Purpose                                                                                          | Link                                  |
|----------------------------|--------------------------------------------------------------------------------------------------|---------------------------------------|
| **Redis**                  | In-memory storage for idempotency keys.                                                          | [redis.io](https://redis.io)          |
| **PostgreSQL**             | Deduplication tables with `UNIQUE` constraints.                                                  | [postgresql.org](https://www.postgresql.org) |
| **Kafka**                  | Message deduplication via `max.in.flight.requests.per.connection`.                              | [kafka.apache.org](https://kafka.apache.org) |
| **AWS Step Functions**     | Idempotent workflow retries with built-in deduplication.                                          | [aws.amazon.com/step-functions](https://aws.amazon.com/step-functions/) |
| **Spring Retry**           | Idempotency support in Spring Boot applications.                                                 | [spring.io/projects/spring-retry](https://spring.io/projects/spring-retry) |

---

## **9. Anti-Patterns**
- **Global Idempotency Keys**: Avoid sharing keys across unrelated operations (e.g., `order_123` for both orders and payments).
- **No TTL on Keys**: Stale keys can lead to false positives (e.g., a "completed" payment key reused on a new request).
- **Client-Side Only**: Relying only on client-side tracking (e.g., `lastProcessedId`) fails if the server state diverges.
- **Over-Deduplicating**: Deduplicating all requests increases latency; prioritize high-value operations.

---
**See Also**:
- [Idempotency in REST APIs (O’Reilly)](https://www.oreilly.com/library/view/restful-web-services/9781491957659/ch09.html)
- [Kafka Deduplication Guide](https://kafka.apache.org/documentation/#deduplication)