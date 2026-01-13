---
# **[Pattern] Durability Approaches – Reference Guide**

---

## **Overview**

Durability in distributed systems ensures that written data persists reliably, even in the face of failures. This reference guide categorizes and defines three primary **durability approaches**—**Synchronous**, **Asynchronous**, and **Best-Effort**—along with their trade-offs, use cases, and implementation details. Each approach balances latency, consistency, and system resilience differently. This guide provides a structured reference for choosing the right durability strategy for your architecture, including schema definitions, query examples, and related patterns.

---

## **Implementation Details**

### **1. Key Concepts**
Durability approaches define how a system guarantees written data survives failures:

| **Concept**               | **Definition**                                                                                                                                 | **Example Use Case**                                                                                     |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Synchronous**           | Writes are acknowledged only after the data is persisted to durable storage (e.g., disk).                                                                 | Financial transactions requiring transactional reliability.                                            |
| **Asynchronous**          | Writes are acknowledged immediately, but persistence happens in the background (e.g., via queues or write-back caches).                              | High-throughput logging systems where immediate acknowledgment is critical.                           |
| **Best-Effort**           | No explicit durability guarantees; system relies on application-level retries or external monitoring.                                             | Low-latency caching layers where consistency is secondary to performance.                               |

**Trade-offs:**
- **Synchronous:** High reliability but latency-sensitive.
- **Asynchronous:** Low latency but potential data loss if the background process fails.
- **Best-Effort:** High performance but no guarantees; requires application resilience.

---

## **2. Schema Reference**
Below are schema definitions for common durability strategies in a distributed system.

### **A. Synchronous Durability**
```json
{
  "durability": {
    "type": "synchronous",
    "storage": {
      "backend": "disk|replicated_disk|distributed_storage",
      "replicationFactor": 3,  // Optional: For fault tolerance
      "acknowledgmentTimeout": "5s"  // Timeout for persistence confirmation
    },
    "writeBehavior": "blocking"  // Write waits for persistence
  }
}
```

#### **Variants:**
| **Attribute**            | **Description**                                                                                     | **Example Values**                          |
|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `acknowledgmentTimeout`  | Timeout for waiting for persistence confirmation.                                                  | `"3s"`, `"10s"`                              |
| `replicationFactor`      | Number of copies for fault tolerance (synchronous durability only).                                | `1` (single-node), `3` (multi-region)        |

---

### **B. Asynchronous Durability**
```json
{
  "durability": {
    "type": "asynchronous",
    "writeBehavior": "non-blocking",
    "persistenceQueue": {
      "backend": "kafka|rabbitmq|local_buffer",
      "maxBatchSize": 1000,
      "batchTimeout": "1s"
    },
    "fallback": {
      "retryPolicy": "exponential_backoff|constant_delay",
      "maxRetries": 5
    }
  }
}
```

#### **Key Attributes:**
| **Attribute**            | **Description**                                                                                     | **Example Values**                          |
|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `persistenceQueue`       | Queue system for buffering writes before persistence.                                               | `"kafka"`, `"rabbitmq"`                     |
| `maxBatchSize`           | Number of writes batched before flushing to storage.                                                 | `100`, `1000`                               |
| `retryPolicy`            | Strategy for retrying failed persistence operations.                                                | `"exponential_backoff"`                     |

---

### **C. Best-Effort Durability**
```json
{
  "durability": {
    "type": "best_effort",
    "storage": {
      "backend": "memory|ephemeral_disk",
      "fallback": {
        "monitoring": {
          "alertThreshold": 0.1,  // % of lost writes
          "notificationChannel": "slack|email"
        }
      }
    },
    "retentionPolicy": {
      "maxAge": "24h",  // Data expiry for non-critical writes
      "evictionStrategy": "lru|ttl"  // Eviction policy for memory
    }
  }
}
```

#### **Key Attributes:**
| **Attribute**            | **Description**                                                                                     | **Example Values**                          |
|--------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `retentionPolicy`        | Rules for data expiration or eviction.                                                               | `"maxAge": "1h"`, `"evictionStrategy": "ttl"` |
| `alertThreshold`         | Percentage of lost writes that triggers alerts.                                                      | `0.05` (5%)                                 |

---

## **3. Query Examples**

### **A. Checking Durability Configuration**
```sql
-- SQL-like pseudo-query to fetch durability settings for a table
SELECT durability.type, storage.backend, writeBehavior
FROM system_settings
WHERE table_name = 'transactions';
```

**Expected Output:**
```json
{
  "type": "synchronous",
  "storage": { "backend": "replicated_disk" },
  "writeBehavior": "blocking"
}
```

---

### **B. Simulating an Asynchronous Write**
```javascript
// Application-level call to write data asynchronously
await writeAsync({
  key: "user_123",
  value: "updated_profile",
  durability: {
    type: "asynchronous",
    persistenceQueue: "order_events_queue"
  }
});
```
**Flow:**
1. Write is acknowledged immediately.
2. Event is enqueued for later persistence.
3. Background worker processes the queue.

---

### **C. Enforcing Best-Effort Durability with Retries**
```python
# Client-side retry logic for best-effort writes
def write_with_retries(key, value, max_retries=3):
    retry_count = 0
    while retry_count < max_retries:
        try:
            write_to_storage(key, value, durability="best_effort")
            break
        except StorageError:
            retry_count += 1
            time.sleep(2 ** retry_count)  # Exponential backoff
    else:
        notify_failure(key, value)  # Fallback alert
```

---

## **4. Implementation Patterns**

### **A. Combined Durability Strategies**
- **Hybrid Approach:** Use synchronous durability for critical operations (e.g., financial transactions) and asynchronous for non-critical logs.
- **Schema Example:**
  ```json
  {
    "durability": {
      "critical": { "type": "synchronous", "storage": "replicated_disk" },
      "nonCritical": { "type": "asynchronous", "persistenceQueue": "logs_queue" }
    }
  }
  ```

---

### **B. Durability with Event Sourcing**
- **Pattern:** Append-only log for state changes, with replayability for recovery.
- **Use Case:** Audit trails or complex event processing.
- **Example:**
  ```json
  {
    "durability": {
      "type": "synchronous",
      "storage": {
        "backend": "event_sourced_db",
        "replayPolicy": "linear|parallel"
      }
    }
  }
  ```

---

### **C. Durability in State Machines**
- **Pattern:** State transitions are logged synchronously, with async reprocessing if needed.
- **Example Workflow:**
  1. State change → synchronous write to log.
  2. Async worker reads log and updates state.

---

## **5. Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Idempotent Operations** | Ensures repeated writes have the same effect.                                                       | Systems with unreliable networks (e.g., API calls).                                                 |
| **Transactional Outbox**  | Buffers writes for persistence in a separate transactional layer.                                   | Microservices where async processing is needed but durability is critical.                           |
| **CRDTs (Conflict-Free Replicated Data Types)** | Data structures that automatically merge updates without conflicts.                                 | Collaborative applications (e.g., shared whiteboards) where eventual consistency is acceptable.    |
| **Saga Pattern**          | Manages distributed transactions via compensating actions.                                           | Long-running workflows requiring ACID-like guarantees.                                               |

---

## **6. Best Practices**
1. **Monitoring:**
   - Track persistence latency (`acknowledgmentTimeout` violations).
   - Alert on queue backlogs (asynchronous durability).
2. **Fallbacks:**
   - For best-effort durability, implement application-level retries or idempotency.
3. **Testing:**
   - Simulate disk failures (synchronous durability).
   - Test queue failures (asynchronous durability).
4. **Documentation:**
   - Clearly label durability guarantees per API/table.
   - Example:
     ```
     // POST /transactions
     // Durability: Synchronous (blocking)
     ```

---
**References:**
- [CAP Theorem](https://en.wikipedia.org/wiki/CAP_theorem)
- [Event Sourcing](https://martinfowler.com/eaaP.html)
- [Idempotent Operations Guide](https://docs.aws.amazon.com/amazons3/latest/userguide/idempotency.html)