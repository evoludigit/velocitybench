# **[Pattern] Queuing Conventions Reference Guide**

---

## **Overview**
The **Queuing Conventions** pattern defines standardized rules for handling message queues (e.g., Kafka, RabbitMQ, SQS) to ensure consistency, reliability, and maintainability across microservices. This pattern enforces conventions around message structure, naming, prioritization, and error handling, reducing ambiguity and improving interoperability.

Key benefits:
- **Decoupled communication** with explicit contract definitions.
- **Reduced context-switching** via standardized schemas.
- **Predictable behavior** in failure scenarios (retries, dead-letter queues).
- **Scalability** through structured queue management.

This guide covers core conventions, schema requirements, query patterns, and integrations with related architectural patterns.

---

## **Implementation Details**

### **1. Core Conventions**
| **Category**         | **Definition**                                                                 | **Example**                                                                 |
|----------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Message Naming**   | Use lowercase, kebab-case for queue/topic names, prefixed with `v<version>`.   | `orders-v2`, `payments-processed`                                            |
| **Schema Versioning**| Append `-v<major>.<minor>` to topic names for backward compatibility.         | `user-events-v1.2` (supports v1.2 schema)                                   |
| **Message Structure**| All messages must include:                                                     |                                                                             |
|                      | - `message_id` (UUID)                                                         | `{ "message_id": "550e8400-e29b-41d4-a716-446655440000", ... }`             |
|                      | - `timestamp` (ISO-8601)                                                       | `{ "timestamp": "2024-02-20T12:00:00Z", ... }`                               |
|                      | - `event_type` (enum, e.g., `order_created`, `payment_failed`)                | `{ "event_type": "order_created", ... }`                                    |
|                      | - `payload` (JSON, PII anonymized)                                           | `{ "payload": { "order_id": "ord-123", "amount": 99.99 }, ... }`            |
| **Priority Levels**  | Use numeric values (0 = lowest, 9 = highest) for QoS.                         | `{ "priority": 3 }` (medium priority)                                        |
| **TTL (Time-to-Live)**| Set TTL for stale messages (e.g., 24h for `invoices-v1`).                     | Kafka: `message.ttl.ms=86400000` (1 day)                                     |
| **Dead-Letter Queue**| Route failed messages to `dlq/<topic>/<version>` (e.g., `dlq/orders-v2`).    | Failed `orders-v2` → `dlq/orders-v2` with `error_code` and `retries_left`.|
| **Idempotency**      | Use `idempotency_key` for deduplication (e.g., `order_id`).                   | `{ "idempotency_key": "ord-123" }`                                          |

---

### **2. Schema Reference**
All messages adhere to the **OpenAPI 3.0** schema below. Custom fields must be prefixed with `x-` (e.g., `x_customer_id`).

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["message_id", "timestamp", "event_type", "payload"],
  "properties": {
    "message_id": { "type": "string", "format": "uuid" },
    "timestamp": { "type": "string", "format": "date-time" },
    "event_type": {
      "type": "string",
      "enum": [
        "order_created", "order_canceled", "payment_processed",
        "inventory_updated", "user_registered"
      ]
    },
    "priority": { "type": "integer", "minimum": 0, "maximum": 9, "default": 2 },
    "payload": {
      "type": "object",
      "additionalProperties": true
    },
    "idempotency_key": { "type": "string" },
    "metadata": {
      "type": "object",
      "additionalProperties": { "type": "string" }
    }
  }
}
```

**Validation Tools:**
- [JSON Schema Validator](https://www.jsonschemavalidator.net/)
- Kafka: Use [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html).

---

## **Query Examples**

### **1. Publishing a Message**
**Kafka (Python - `confluent_kafka`):**
```python
from confluent_kafka import Producer

conf = {"bootstrap.servers": "kafka:9092"}
producer = Producer(conf)

message = {
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-02-20T12:00:00Z",
    "event_type": "order_created",
    "payload": {"order_id": "ord-123", "status": "pending"},
    "priority": 3
}
producer.produce(
    topic="orders-v2",
    value=json.dumps(message),
    callback=lambda err, _: print(f"Error: {err}") if err else None
)
producer.flush()
```

**AWS SQS (Node.js - `aws-sdk`):**
```javascript
const AWS = require("aws-sdk");
const sqs = new AWS.SQS();

const params = {
  QueueUrl: "https://sqs.us-east-1.amazonaws.com/123456789012/orders-v2",
  MessageBody: JSON.stringify({
    message_id: "550e8400-e29b-41d4-a716-446655440000",
    event_type: "order_created",
    payload: { order_id: "ord-123" }
  }),
  MessageAttributes: {
    Priority: { DataType: "Number", StringValue: "3" }
  }
};

sqs.sendMessage(params, (err, data) => {
  if (err) console.error(err);
});
```

---

### **2. Consuming Messages**
**Kafka (Go - `sarama`):**
```go
package main

import (
	"github.com/Shopify/sarama"
)

func main() {
	config := sarama.NewConfig()
	config.Consumer.Return.Errors = true

	consumer, _ := sarama.NewConsumer([]string{"kafka:9092"}, config)
	delegate := consumer.Consume("orders-v2", nil)

	for msg := range delegate.Messages() {
		var payload struct {
			OrderID string `json:"order_id"`
			Status  string `json:"status"`
		}
		json.Unmarshal(msg.Value, &payload)
		println("Received:", payload)
	}
}
```

**RabbitMQ (Python - `pika`):**
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()
channel.queue_declare(queue="orders-v2")

def callback(ch, method, properties, body):
    data = json.loads(body)
    print(f"Event: {data['event_type']}, Payload: {data['payload']}")

channel.basic_consume(
    queue="orders-v2",
    on_message_callback=callback,
    auto_ack=True
)
channel.start_consuming()
```

---

### **3. Querying Dead-Letter Queues (DLQ)**
**SQL (PostgreSQL - for DLQ tracking):**
```sql
-- Create DLQ tracking table
CREATE TABLE dlq_events (
    event_id UUID PRIMARY KEY,
    queue_name VARCHAR(255),
    version VARCHAR(10),
    error_code VARCHAR(50),
    retries_left INTEGER,
    payload JSONB,
    occurred_at TIMESTAMP DEFAULT NOW()
);

-- Insert failed event
INSERT INTO dlq_events (event_id, queue_name, version, error_code, retries_left, payload)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    'orders-v2',
    'v2',
    'SCHEMA_MISMATCH',
    0,
    '{"event_type": "order_created", "payload": {"order_id": "ord-123"}}'
);
```

**Kafka DLQ Workflow:**
1. Enable `max.inflight.requests.per.connection=5` in consumer config.
2. Set `delivery.timeout.ms=300000` (5 mins) for retries.
3. Route failed messages to `dlq/orders-v2` with:
   ```json
   {
     "original_message": "...",
     "error": "DeserializationFailed",
     "retry_count": 3
   }
   ```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **Integration**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Command Query Responsibility Segregation (CQRS)** | Separates read/write models; use queues for async writes.                      | Publish `order_created` to `orders-writes-v2`; read from `orders-reads-v1`. |
| **Saga Pattern**          | Manages distributed transactions via choreography or orchestration.          | Use queues to coordinate `payment_saga` steps (e.g., `payments-pending`).   |
| **Event Sourcing**        | Stores state changes as immutable events in a queue.                          | Append `user_events-v1` with `user_registered` events.                        |
| **Circuit Breaker**       | Prevents queue overload by throttling consumers.                             | Limit `invoices-v2` consumers to 100 msgs/sec with `max_consumers=5`.         |
| **Rate Limiting**         | Controls message volume per consumer.                                         | Use `priority=9` for urgent orders; `priority=0` for batch processing.       |

---

## **Best Practices**
1. **Versioning**:
   - Increment `minor` for backward-compatible changes (e.g., `v1.1`).
   - Increment `major` for breaking changes (e.g., `v2.0`).
   - Deprecate old versions with `deprecated=true` in metadata.

2. **Monitoring**:
   - Track queue lag: `kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group orders-consumer`.
   - Alert on DLQ growth: `SELECT COUNT(*) FROM dlq_events WHERE retries_left = 0`.

3. **Security**:
   - Encrypt sensitive payloads (e.g., `payment_data` field) with [AWS KMS](https://aws.amazon.com/kms/).
   - Restrict ACLs: `ALTER TOPIC orders-v2 --add-owners user:orders-service`.

4. **Testing**:
   - Use [Kafka Unit](https://github.com/edenhill/kafkatest) for local testing.
   - Mock queues in unit tests with [Mockqueue](https://github.com/rotisserie/mockqueue).

---
**See Also:**
- [CNCF Messaging Patterns](https://messagingpatterns.info/)
- [Kafka Best Practices](https://kafka.apache.org/documentation/#best_practices)