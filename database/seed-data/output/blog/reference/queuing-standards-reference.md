# **[Pattern] Queuing Standards Reference Guide**

---

## **Overview**
The **Queuing Standards** pattern defines consistent conventions for designing, implementing, and consuming asynchronous message queues. Queues enable decoupled, scalable, and resilient event-driven architectures but require standardized semantics to ensure interoperability across services. This guide clarifies **message formats, naming conventions, priority levels, retention policies, and error handling** to minimize ambiguity in distributed systems.

Standards covered:
- **Message Structure:** Required fields, payload schemas, and metadata.
- **Naming Conventions:** Queue/resource naming rules for reliability.
- **Priority Levels:** Queuing tiers (high/normal/low) and use cases.
- **Retention & Expiry:** Durability guarantees and TTL policies.
- **Error Handling:** Dead-lettering, retry semantics, and monitoring.

---

## **Schema Reference**
All queues adhere to the following **mandatory fields** in the message header:

| **Field**               | **Type**   | **Description**                                                                 | **Examples**                          |
|-------------------------|------------|---------------------------------------------------------------------------------|---------------------------------------|
| `message_id`            | UUID       | Unique identifier for message tracking.                                        | `550e8400-e29b-41d4-a716-446655440000` |
| `correlation_id`        | String     | Links messages in a related conversation (e.g., order processing).             | `order#12345_processing`              |
| `source_system`         | String     | Originating service name (e.g., `inventory-service`).                           | `payment-engine`                      |
| `destination_system`    | String     | Target service for processing.                                                 | `notification-service`                |
| `timestamp`             | ISO 8601   | When the message was created.                                                   | `2023-11-01T14:30:00Z`               |
| `priority`              | Enum       | Queue priority (`high`, `normal`, `low`).                                      | `"high"`                              |
| `retry_count`           | Integer    | Number of failed processing attempts (automatically updated).                  | `2`                                    |
| `expiry_time`           | ISO 8601   | When the message becomes invalid (nullable).                                    | `2023-11-07T00:00:00Z`               |
| `content_type`          | String     | MIME type or custom schema identifier.                                          | `"application/vnd.company.order.v1+json"` |
| `payload`               | Binary     | Encoded message content (base64 or custom serialization like Protobuf).          | `{"event":"order_created"...}`         |

---

### **Priority Levels**
| **Priority** | **Use Case**                                                                 | **Expected Latency** | **Retry Policy**               |
|--------------|-----------------------------------------------------------------------------|----------------------|---------------------------------|
| `high`       | Urgent operations (e.g., fraud alerts, payment fails).                     | <10 seconds          | 3 retries, 1 minute intervals   |
| `normal`     | Default workloads (e.g., inventory updates, user registrations).            | <60 seconds          | 5 retries, exponential backoff   |
| `low`        | Background tasks (e.g., report generation, analytics).                       | >5 minutes           | 1 retry, 1 hour interval        |

---

### **Retention & Expiry Policies**
| **Policy**       | **Duration** | **Description**                                                                 | **Applies To**                     |
|------------------|--------------|-------------------------------------------------------------------------------|------------------------------------|
| `persistent`     | N/A          | Messages stored until manually deleted.                                        | Critical event data (e.g., audit logs) |
| `time_to_live`   | Configurable | Expires after `expiry_time` (TTL) or `default_ttl` (1 day).                   | Temporary notifications             |
| `max_retries`    | Configurable | Discarded after `retry_count` exceeds threshold.                              | Fault-tolerant tasks               |

Example TTL rules:
- **`default_ttl`** = 24h for non-persistent queues.
- **`high_priority`** = 1h expiry if unattempted.

---

## **Query Examples**
### **1. Filter Messages by Status**
```sql
-- Example: Query unprocessed messages in a "pending" state
SELECT * FROM message_queue
WHERE status = 'PENDING'
AND priority = 'high'
AND source_system = 'payment-service';
```

### **2. Find Expired Messages**
```sql
-- Identify messages due for cleanup (time > expiry_time)
SELECT message_id, correlation_id, source_system
FROM message_queue
WHERE timestamp < expiry_time
AND status = 'READY'
LIMIT 1000;
```

### **3. Generate Dead-Letter Queue (DLQ) Entries**
```python
# Pseudocode for DLQ processing
for message in queue:
    if message.retry_count >= MAX_RETRIES:
        dlq_record = {
            "message_id": message.message_id,
            "error_details": message.processing_error,
            "timestamp": datetime.utcnow()
        }
        dlq_pubsub.publish(dlq_record)
```

### **4. Schema Validation**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "required": ["message_id", "source_system", "priority", "payload"],
  "properties": {
    "correlation_id": {
      "pattern": "^[a-zA-Z0-9-]+\#[0-9]+$"
    },
    "expiry_time": {
      "format": "date-time",
      "minimum": "2023-11-01T00:00:00Z"
    }
  }
}
```

---

## **Naming Conventions**
| **Component**       | **Rule**                                                                                     | **Example**                          |
|---------------------|---------------------------------------------------------------------------------------------|--------------------------------------|
| **Queue Names**     | `[system].[event].[priority]` (lowercase, hyphens).                                           | `user-notification.auth_failed.high`  |
| **Resource IDs**    | UUIDv4 for global uniqueness.                                                                 | `550e8400-e29b-41d4-a716-446655440000` |
| **DLQ Prefix**      | Append `-dlq` to queue names.                                                                 | `user-notification.order_confirmation-dlq` |

---

## **Error Handling**
### **Dead-Letter Queues (DLQ)**
- **Purpose:** Capture permanently failed messages.
- **Schema:**
  ```json
  {
    "message_id": "...",
    "original_queue": "user-notification.auth_failed",
    "error": {
      "code": "INVALID_FORMAT",
      "description": "Payload missing 'user_id'.",
      "timestamp": "..."
    }
  }
  ```

### **Retry Semantics**
| **Retry Attempt** | **Backoff Strategy**                                                                       | **Action**                          |
|--------------------|-------------------------------------------------------------------------------------------|-------------------------------------|
| 1                  | Fixed delay: 5 seconds.                                                                     | Redeliver to queue.                 |
| 2                  | Exponential: 10 seconds.                                                                  | Log warning.                        |
| 3+                 | 30-second intervals, max 5 minutes total.                                                 | Escalate to DLQ.                    |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                       | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Event Sourcing**        | Store state changes as immutable events in a queue.                                   | Audit trails, replayable transactions.                                         |
| **Saga Pattern**          | Manage distributed transactions via compensating actions.                            | Microservices with ACID-like guarantees.                                      |
| **Circuit Breaker**       | Prevent cascading failures in downstream queues.                                     | Resilience for high-traffic services.                                         |
| **Message Broker**        | Abstraction for RabbitMQ/Kafka/NATS with standardized APIs.                           | Cross-platform interservice communication.                                    |

---

## **Key Considerations**
1. **Backward Compatibility:** Use **semantic versioning** in `content_type` headers.
2. **Monitoring:** Track metrics like `queue_depth`, `message_latency`, and `retry_failures`.
3. **Security:** Enforce TLS for all queue communications; restrict access via IAM roles.
4. **Idempotency:** Design payloads to be safely reprocessed (e.g., include `message_id` in requests).

---
**Last Updated:** `[Insert Date]`
**Version:** `1.2`