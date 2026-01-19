# **[Notification Systems Patterns] Reference Guide**

## **Overview**
The **Notification Systems Patterns** reference guide outlines robust, scalable, and maintainable approaches for designing systems that deliver real-time events, alerts, or updates to subscribed clients. This pattern addresses core challenges in event sourcing, publisher-subscriber architectures, and async communication across distributed services. It covers foundational patterns (e.g., **Event Bus**, **Observer**, **CQRS with Event Sourcing**) and advanced variants (e.g., **Dead Letter Queues**, **Event Retry Policies**) to ensure reliability, throughput, and fault tolerance.

Key use cases include:
- **Real-time notifications** (e.g., chat apps, social media updates).
- **Distributed traceability** (e.g., logging, audit trails).
- **Decoupled microservices** (e.g., order processing → inventory updates).

---

## **Schema Reference**

| **Pattern**               | **Description**                                                                                       | **Use Case Example**                          | **Key Components**                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------|------------------------------------------------------------------------------------|
| **Event Bus**             | Centralized messaging layer where producers send events, and subscribers react asynchronously.      | Order confirmation → shipping team            | Broker (Kafka, RabbitMQ), Event Schema (JSON/Avro), Topics/Queues                  |
| **Observer**              | классический шаблон проектирования для уведомления объектов о событиях других объектов.           | UI refresh on database changes               | Subject (Event Source), Observer (Listener), Registration/Unregistration API      |
| **CQRS with Event Sourcing** | Separates read/writes via commands and queries, storing state as immutable event logs.             | Financial ledger updates                      | Command Handler, Query Handler, Event Store (e.g., EventStoreDB), Snapshots        |
| **Dead Letter Queue (DLQ)** | Captures and reprocesses failed events to prevent data loss.                                      | Retry failed payment notifications            | DLQ (S3, Dead Letter Topic), Retry Policy (Exponential Backoff)                    |
| **Event Retry Policy**    | Implements backoff strategies for transient failures (e.g., network issues).                         | Retry failed notifications after 503 errors   | Retry Count, Max Attempts, Jitter, Circuit Breaker (e.g., Hystrix)                |
| **Event Slicing**         | Partitions events by entity (e.g., user, order) to avoid monolithic event streams.                 | User activity logs                            | Event Boundaries (e.g., `UserUpdated`, `OrderPaid`), Projection Tables             |
| **Fan-Out Subscription**  | Publishes events to multiple subscribers for parallel processing.                                   | Broadcast stock price changes to traders      | Subscriber Groups, Partitioning (e.g., Kafka Consumer Groups)                      |
| **Event Projection**      | Reconstructs state from event logs for queries (e.g., materialized views).                         | Aggregated sales reports                      | View Model, Subscribers to Event Stream, Caching (Redis)                          |
| **Schema Registry**       | Maintains backward/forward compatibility of event schemas.                                          | Microservices with evolving APIs              | Avro/Protobuf Schema, Versioning, Validation Rules                               |
| **Event Time vs. Processing Time** | Differentiates between when an event occurred (wall-clock) vs. when it was processed.         | Late-arriving order events                   | Watermarks, Event Time Tracking, Out-of-Order Handling                            |

---

## **Implementation Details**

### **1. Core Components**
- **Producers**: Services emitting events (e.g., `OrderCreated`).
- **Broker**: Distributed messaging system (e.g., Kafka, RabbitMQ, NATS).
- **Consumers**: Subscribers processing events (e.g., notification service).
- **Schema Registry**: Ensures schema consistency (e.g., Confluent Schema Registry).
- **Monitoring**: Tracks latency, throughput, and failures (e.g., Prometheus + Grafana).

### **2. Event Design Principles**
- **Idempotency**: Ensure reprocessing the same event doesn’t cause side effects (e.g., via `event_id`).
- **Immutability**: Events are never modified after publication.
- **Semantic Versioning**: Schema changes follow [SemVer](https://semver.org/).

### **3. Error Handling**
| **Failure Type**          | **Pattern**                          | **Mitigation**                                                                 |
|---------------------------|--------------------------------------|---------------------------------------------------------------------------------|
| Broker Unavailable        | **Retry with Backoff**               | Exponential backoff (e.g., 1s → 2s → 4s) with max retries (e.g., 5).           |
| Consumer Lag              | **Dead Letter Queue (DLQ)**          | Route failed events to DLQ for manual review or reprocessing.                   |
| Schema Mismatch           | **Schema Registry**                  | Validate events against registered schemas before processing.                     |
| Duplicate Events          | **Idempotent Consumers**             | Use event IDs or deduplication keys (e.g., Kafka `isr` checks).                 |

---

## **Query Examples**
### **1. Publishing an Event (Kafka Example)**
```python
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers=["kafka:9092"])
event = {
    "event_id": "order-123",
    "type": "OrderCreated",
    "timestamp": "2023-10-01T12:00:00Z",
    "data": {"user_id": 42, "amount": 99.99}
}
producer.send("orders-topic", value=json.dumps(event).encode("utf-8"))
```

### **2. Subscribing to Events (Python with Confluent)**
```python
from confluent_kafka import Consumer

conf = {"bootstrap.servers": "kafka:9092", "group.id": "notification-group"}
consumer = Consumer(conf)
consumer.subscribe(["notifications-topic"])

while True:
    msg = consumer.poll(timeout=1.0)
    if msg is None:
        continue
    event = json.loads(msg.value.decode("utf-8"))
    print(f"Received {event['type']}: {event['data']}")
```

### **3. Querying Event Logs (SQL Example)**
```sql
-- Find all failed payment notifications (DLQ)
SELECT * FROM dead_letter_queue
WHERE event_type = 'PaymentFailed'
ORDER BY timestamp DESC
LIMIT 100;

-- Reconstruct user balance from events (Event Sourcing)
SELECT
    user_id,
    SUM(CASE WHEN type = 'Deposit' THEN amount ELSE -amount END) AS balance
FROM event_logs
WHERE user_id = 42 AND type IN ('Deposit', 'Withdrawal')
GROUP BY user_id;
```

### **4. Schema Validation (Avro + Schema Registry)**
```json
-- Define an event schema (user_updated.avsc)
{
  "type": "record",
  "name": "UserUpdated",
  "namespace": "com.example",
  "fields": [
    {"name": "user_id", "type": "string"},
    {"name": "updated_at", "type": ["null", "int"]}
  ]
}
```
**Validation Rule**:
```bash
curl -X POST -H "Content-Type: application/vnd.schemaregistry.v1+json" \
     --data '{"schema": "..."}' \
     http://schema-registry:8081/subjects/user_updated-value/versions
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[CQRS](https://microservices.io/patterns/data/cmd-query-separation.html)** | Separates read/write operations to optimize for each.                                              | High-read workloads with complex queries (e.g., e-commerce dashboards).        |
| **[Event Sourcing](https://martinfowler.com/eaaCatalog/eventSourcing.html)** | Stores state changes as a sequence of events.                                                    | Audit trails, time-travel debugging, or compliance requirements.                |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)**       | Manages distributed transactions via orchestrated events.                                         | Cross-service workflows (e.g., order → payment → shipping).                     |
| **[Circuit Breaker](https://microservices.io/patterns/resilience/circuit-breaker.html)** | Prevents cascading failures by stopping requests to faulty services.                           | Resilient notifications during broker outages.                                  |
| **[Bulkheads](https://microservices.io/patterns/resilience/bulkhead.html)** | Isolates resource contention (e.g., thread pools) for consumers.                                  | High-throughput event processing with limited resources.                        |
| **[Idempotent Consumer](https://docs.confluent.io/platform/current/kafka/design.html#idempotent-producer)** | Handles duplicate events safely.                                                                  | Eventual consistency scenarios (e.g., user profile updates).                    |

---

## **Best Practices**
1. **Schema Evolution**:
   - Use **backward-compatible** changes (e.g., adding optional fields).
   - Avoid breaking changes in production (e.g., removing fields).

2. **Performance**:
   - **Batch events** where possible (e.g., Kafka `batch.size`).
   - **Compress payloads** (e.g., Avro + Snappy).

3. **Monitoring**:
   - Track **end-to-end latency** (publish → consume).
   - Alert on **consumer lag** (e.g., Kafka `lag` metric).

4. **Security**:
   - **Authenticate producers/consumers** (e.g., SASL/SCRAM).
   - **Encrypt data in transit** (TLS) and **at rest** (broker storage encryption).

5. **Testing**:
   - **Integration Tests**: Verify end-to-end event flows.
   - **Chaos Testing**: Simulate broker failures to test DLQ handling.

---
**References**:
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [CQRS Patterns](https://msddd.github.io/CQRS-Patterns/)
- [Event Sourcing Patterns](https://martinfowler.com/eaaCatalog/eventSourcing.html)