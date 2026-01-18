# **[Pattern] Streaming Conventions Reference Guide**

---

## **Overview**
The **Streaming Conventions** pattern defines standardized rules for structured data streaming, ensuring consistency in event payload schemas, serialization, metadata handling, and delivery guarantees across microservices, real-time systems, and event-driven architectures. This pattern addresses scalability, interoperability, and reliability by enforcing explicit conventions for:
- **Event Schema Registry** (schema evolution, versioning)
- **Serialization & Encoding** (structured binary formats, compression)
- **Streaming Messaging Protocols** (exactly-once delivery, backpressure)
- **Metadata & Semantics** (event context, routing keys, timestamps)
- **Error Handling & Retries** (idempotency, dead-letter queues)

Adopting these conventions minimizes friction between producers and consumers, reduces debugging overhead, and enables seamless integration with tools like Apache Kafka, NATS streaming, or Pulsar.

---

## **Key Concepts**

### **1. Event Schema Design**
- **Schema Registry**: Use a centralized registry (e.g., [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)) to manage schemas with versioned evolution.
- **Schema Evolution**: Support backward/forward compatibility via **Avro (with schema evolution)** or **Protobuf (with breaking change flags)**.
- **Naming Conventions**: Enforce domain-agnostic event types (e.g., `OrderCreatedEvent`, `PaymentProcessedEvent`).

| **Aspect**               | **Recommended Convention**                                                                 | **Example**                          |
|--------------------------|-------------------------------------------------------------------------------------------|---------------------------------------|
| **Schema Format**        | Avro (for nested data), Protobuf (for performance), JSON Schema (for flexibility)         | `{ "type": "order_created", "payload": {...} }` |
| **Versioning**           | Semantic Versioning (`MAJOR.MINOR.PATCH`) or Kafka’s `event-key` with `version` field      | `event_key: "order123", version: "1.0.0"` |
| **Idempotency Key**      | Unique identifier for replay safety                                                            | `id: "order-456"`                     |
| **Timestamp**            | ISO-8601 UTC (`2024-02-20T14:30:00Z`) or Unix epoch                                             | `timestamp: 1708414200000`            |

---

### **2. Serialization & Encoding**
| **Decision Point**       | **Recommendation**                                                                       | **Tooling**                          |
|--------------------------|-----------------------------------------------------------------------------------------|---------------------------------------|
| **Serialization**        | **Structured Binary** (Avro/Protobuf) > **Text** (JSON) for performance/capacity         | Avro, Protobuf, MessagePack            |
| **Compression**          | **Snappy** (balance speed/compression) > **Gzip** > **Zstd** (CPU-heavy but better ratio) | Avro Snappy, Protobuf Zstd            |
| **Encoding Overhead**    | Limit headers to **100B** (e.g., Kafka headers) to avoid disk/network bloat               | Kafka `Headers` (serialized as bytes) |

**Example Payload (Avro):**
```json
{
  "type": "order_created",
  "id": "order-123",
  "version": "1.0.0",
  "data": {
    "customer_id": "cust-789",
    "items": [{"sku": "ABC", "quantity": 2}]
  },
  "_metadata": {
    "timestamp": "2024-02-20T14:30:00Z",
    "source_system": "ecommerce"
  }
}
```
**Serialized (Avro Binary):**
`0x0A056F72646572010A036964010A0876657273696F6E010A05312E302E30...`

---

### **3. Stream Messaging Protocols**
| **Protocol**             | **Key Convention**                                                                       | **Delivery Guarantee**               |
|--------------------------|-----------------------------------------------------------------------------------------|---------------------------------------|
| **Kafka**                | Partition key based on `event_key`; Retention: 7–30 days                               | At-least-once (configurable: exactly-once via Kafka Streams) |
| **NATS Streaming**       | Subject prefix (`>event_type.user_id`) for filtering; Duration: 24h–90 days            | Best-effort (ACK/NACK flow control)  |
| **Apache Pulsar**        | Schema enforcement at broker level; TTL: 1 day–1 year                                  | Exactly-once (with transactional consumers) |

**Example Kafka Topic Partitioning:**
```
Topic: `orders`
Partition Key: `order_id` (e.g., `order-123`) → Ensures sequential processing.
```

---

### **4. Metadata & Semantics**
| **Field**                | **Purpose**                                                                               | **Example Value**                     |
|--------------------------|-----------------------------------------------------------------------------------------|---------------------------------------|
| `event_type`             | Human-readable event category (e.g., `payment.failed`)                                 | `"payment_processing.failed"`         |
| `correlation_id`         | Links related events (e.g., payment → refund)                                          | `"txn-abc123"`                        |
| `routing_key`            | Kafka/NATS subject or topic filter                                                   | `users.#{user_id}.orders`             |
| `source_application`     | Identifies producer system                                                               | `"ecommerce-service"`                 |

**Dead-Letter Queue (DLQ) Convention:**
```
Topic: `dlq.orders.v1`
Partition Key: `original_topic + original_key`
Meta-fields: `error_code`, `retry_count`, `original_payload_hash`
```

---

### **5. Error Handling & Retries**
- **Idempotency**: Design consumers to handle duplicate events via `id` or `event_type+version`.
- **Retries**: Exponential backoff (e.g., **1s → 10s → 1m**) with max retries = **3**.
- **Dead-Letter Queues (DLQ)**: Route failed events to a separate topic with enriched metadata.

**Retry Header Example (Kafka):**
```json
{
  "retry_count": 2,
  "last_attempt": "2024-02-20T14:35:00Z",
  "error_type": "ConsumerTimeoutError"
}
```

---

## **Implementation Details**

### **A. Schema Evolution Strategy**
| **Scenario**             | **Action**                                                                               | **Tools**                              |
|--------------------------|-----------------------------------------------------------------------------------------|----------------------------------------|
| **Backward-Compatible**  | Add optional fields or use `null` defaults                                             | Avro `add field`, Protobuf `oneof`     |
| **Forward-Compatible**   | Use `enum` or `union` for new types                                                     | Protobuf `extensions`, JSON Schema `anyOf` |
| **Breaking Change**      | Increment `MAJOR` version; deprecate old schema with `deprecated: true`                   | Schema Registry flags                  |

**Example (Protobuf):**
```protobuf
syntax = "proto3";
message OrderCreated {
  string id = 1;
  string customer_id = 2;
  repeated Item items = 3;  // Backward-compatible: `items` was optional before
}

message Item {
  string sku = 1;
  int32 quantity = 2;
  // New field (forward-compatible if optional)
  string discount_code = 3 [ (deprecated) = true ];
}
```

---

### **B. Compression Benchmark**
| **Format**       | **Size (KB)** | **Decode Time (µs)** | **Use Case**                  |
|------------------|---------------|----------------------|-------------------------------|
| Avro (Snappy)    | 4.2           | 15                   | High throughput (Kafka)       |
| Protobuf (Zstd)  | 3.8           | 30                   | Low-latency APIs               |
| JSON (Gzip)      | 6.1           | 80                   | Debugging/logging              |

*Benchmarks: 1KB payload, 1000 iterations on i9-12900K.*

---

### **C. Backpressure Handling**
- **Producer Side**: Buffer events in-memory (max size: **1MB**) before throttling.
- **Consumer Side**:
  - Use **Kafka’s `max.poll.records`** (e.g., `100`) to limit batch size.
  - Implement **dynamic scaling** (e.g., Kubernetes HPA based on `kafka-lag`).

**Example Consumer Offset Commit:**
```java
// Kafka Consumer (Java)
Properties props = new Properties();
props.put(ConsumerConfig.ENABLE_AUTO_COMMIT, "false");
// ...
while (!closed) {
  ConsumerRecords<String, byte[]> records = consumer.poll(Duration.ofMillis(100));
  for (Record<String, byte[]> record : records) {
    try {
      process(record.value());  // Avro/Protobuf deserialization
      consumer.commitSync();    // Manual commit on success
    } catch (Exception e) {
      // DLQ or retry logic
    }
  }
}
```

---

## **Query Examples**

### **1. Filtering Events by Schema Version**
**Kafka Query (Confluent Schema Registry):**
```bash
curl -X GET "http://schema-registry:8081/subjects/orders-value/versions?schemaType=AVRO" \
  | jq '.[] | select(.schema_version == "1.0")'
```
**Output:**
```json
{
  "id": 1,
  "schema": "{\"type\":\"record\",\"name\":\"OrderCreated\",\"fields\":[...]}",
  "version": "1.0",
  "registered_at": "2024-02-01T00:00:00Z"
}
```

### **2. Consuming with Protobuf in Python**
```python
from confluent_kafka import Consumer, KafkaException
import protobuf_order_pb2  # Generated from `.proto`

conf = {'bootstrap.servers': 'kafka:9092', 'group.id': 'orders-v1'}
consumer = Consumer(conf)
consumer.subscribe(['orders'])

while True:
    msg = consumer.poll(1.0)
    if msg is None: continue
    if msg.error(): raise KafkaException(msg.error())
    # Deserialize Protobuf
    order = protobuf_order_pb2.OrderCreated()
    order.ParseFromString(msg.value())
    print(f"Received: {order.id}, Items: {order.items}")
```

### **3. Nats Streaming Query (Subjects)**
```
> SUB orders.created.*
{ "type": "orders.created.order-123",
  "data": { "customer_id": "cust-789" },
  "_metadata": { "received": "2024-02-20T14:30:00Z" } }
```

---

## **Related Patterns**
| **Pattern**               | **Relation to Streaming Conventions**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------|
| **Event Sourcing**        | Storing events in a stream enables replayability and audit trails.                                     | Use for audit logs or CQRS.              |
| **CQRS**                  | Streaming conventions power event projections to materialized views (e.g., `user_orders` table).      | High-write, low-read workloads.         |
| **Saga Pattern**          | Event streams coordinate distributed transactions across services.                                      | Microservices with compensating actions.|
| **Idempotent Producer**   | Ensures no duplicate processing by leveraging `event_key` + idempotent consumers.                     | External APIs or retries.               |
| **Schema Registry**       | Centralized schema governance for streaming schemas (Avro/Protobuf).                                   | Multi-team environments.                 |

---

## **Best Practices**
1. **Versioning**: Tag schemas with `event_type.version` (e.g., `orders.v1`).
2. **Monitoring**: Track:
   - Schema registry usage (` subjects` API).
   - Consumer lag (`kafka-consumer-groups` CLI).
   - DLQ metrics (`error_rate` per event type).
3. **Security**:
   - Encrypt schemas in transit (TLS).
   - Use SASL/SCRAM for broker access.
4. **Performance**:
   - Batch small events (e.g., Kafka `batch.size=16KB`).
   - Avoid nested Avro/Protobuf for deep hierarchies.

---
## **Troubleshooting**
| **Issue**                  | **Diagnosis**                                                                 | **Solution**                              |
|----------------------------|--------------------------------------------------------------------------------|-------------------------------------------|
| **Schema Mismatch**        | Consumer fails to deserialize payload.                                        | Check `consumer_schema_version` vs. producer. |
| **Consumer Lag**           | `kafka-consumer-groups --describe` shows high offset lag.                     | Scale consumers or tune `fetch.min.bytes`. |
| **Duplicate Events**       | Idempotent consumer processing malfunctions.                                   | Add `dedupe_window` (e.g., 5 minutes).    |
| **High Latency**           | `kafka-consumer-lag` shows slow processing.                                    | Optimize serialization (e.g., Protobuf).  |

---
**Appendix**: [Schema Registry API Reference](https://docs.confluent.io/platform/current/schema-registry/developer-guide/index.html) | [Kafka Streams Exactly-Once](https://kafka.apache.org/documentation/#streams_exactlyonce)