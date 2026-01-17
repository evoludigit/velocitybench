---
# **[Pattern] Reference Guide: Messaging Debugging**

---
## **1. Overview**
**Messaging Debugging** is a structured approach to tracing, logging, and diagnosing issues in distributed systems that rely on messaging queues (e.g., Kafka, RabbitMQ, AWS SQS/SNS, Azure Service Bus). This pattern ensures traceability from **message producers** to **consumers**, enabling cross-service debugging for delays, corruption, or unexpected failures.

Key use cases:
- Root-cause analysis of stuck messages
- Verifying message routing and transformations
- Performance bottlenecks in event-driven workflows

**Scope**: Applies to **synchronous** (e.g., REST → RabbitMQ → Microservice) and **asynchronous** (e.g., Kafka → Stream Processing → Database) architectures.

---

## **2. Key Concepts**
| Concept               | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **Message Logs**      | Structured entries (e.g., JSON) capturing metadata like timestamp, source, destination, errors. |
| **Trace ID**          | Unique identifier linking messages across services (UUID/v4 preferred).                        |
| **Dead-Letter Queue** | Destination for unprocessable messages (e.g., malformed payload).                              |
| **Correlation ID**    | Links messages in a chain (e.g., order → payment → fulfillment).                                |
| **Span Context**      | OpenTelemetry/W3C Trace Context for distributed tracing.                                         |

---

## **3. Schema Reference**
### **3.1 Standard Message Logging Fields**
| Field Name          | Type      | Required | Example Value                     | Notes                                  |
|---------------------|-----------|----------|-----------------------------------|----------------------------------------|
| `trace_id`          | UUID      | ✅        | `123e4567-e89b-12d3-a456-426614174000` | Globally unique across services.   |
| `correlation_id`    | UUID      | ❌        | `a1b2c3d4-5678-90ef-ghij-klmnopqrstuv` | Used for related messages (e.g., order/payment). |
| `message_id`        | UUID      | ✅        | `550e8400-e29b-41d4-a716-446655440000` | Unique within a batch.                  |
| `source_service`    | String    | ✅        | `"orders-service"`                | Name of the producer.                  |
| `destination`       | String    | ✅        | `"payments-topic"`                | Topic/queue name.                       |
| `timestamp`         | ISO8601   | ✅        | `"2024-05-20T14:30:45.123Z"`      | UTC for consistency.                   |
| `payload_hash`      | SHA-256   | ❌        | `"d5e783d0e463a4d912c4b7114f0d579f"` | Verify payload integrity.               |
| `error`             | String    | ❌        | `"Schema validation failed"`      | Null if successful.                     |

---

### **3.2 Dead-Letter Queue (DLQ) Schema**
| Field Name       | Type    | Example Value                     |
|------------------|---------|-----------------------------------|
| `dlq_reason`     | String  | `"DeserializationError"`           |
| `original_queue` | String  | `"orders-topic"`                   |
| `retries`        | Integer | `3`                               |
| `first_seen`     | ISO8601 | `"2024-05-20T14:30:45.123Z"`      |

---

## **4. Implementation Details**
### **4.1 Producer-Side Debugging**
1. **Enrich Messages with Metadata**:
   ```java
   // Example: Adding trace/correlation IDs to a Kafka message
   var headers = new RecordHeaders();
   headers.add("trace_id", traceId.getBytes());
   headers.add("correlation_id", correlationId.getBytes());
   producer.send(new ProducerRecord<>("orders-topic", headers, payload));
   ```

2. **Validate Payloads**:
   - Use schemas (e.g., Avro, Protobuf) and validate against them before sending.
   - Log `payload_hash` for verification.

3. **Monitor Send Failures**:
   - Implement retry logic with exponential backoff.
   - Log `error` field with details (e.g., `BrokerNotAvailableException`).

---

### **4.2 Consumer-Side Debugging**
1. **Trace Propagation**:
   - Extract `trace_id`/`correlation_id` from headers/attributes and propagate to downstream calls.

2. **Error Handling**:
   ```python
   # Example: Handling malformed messages in RabbitMQ
   try:
       payload = json.loads(message.body)
   except json.JSONDecodeError as e:
       log.error(f"Invalid JSON: {e}", extra={"error": "DeserializationError"})
       dlq_channel.basic_publish(
           exchange="dlq_exchange",
           routing_key="orders-dlq",
           body=message.body
       )
   ```

3. **Dead-Letter Queues**:
   - Configure DLQs with TTL (e.g., 7 days) and alerts for unprocessed messages.
   - Use `x-dead-letter-exchange` (RabbitMQ) or `max.in.flight.requests.per.connection` (Kafka) to control backpressure.

---

### **4.3 Distributed Tracing**
- **Tools**: Integrate OpenTelemetry or Jaeger to correlate spans across services.
- **Example Trace Flow**:
  ```
  [Producer] → [Kafka] → [Consumer A] → [Database] → [Consumer B]
  ```

---

## **5. Query Examples**
### **5.1 Finding Stuck Messages**
**SQL (Log Database)**:
```sql
SELECT * FROM message_logs
WHERE destination = 'payments-topic'
  AND timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

**Kafka CLI**:
```bash
# List unprocessed messages in a consumer group
kafka-consumer-groups --bootstrap-server broker:9092 \
  --describe --group payments-consumer-group
```

---

### **5.2 Analyzing DLQ**
**RabbitMQ Management API**:
```bash
# List messages in DLQ
curl -u guest:guest http://localhost:15672/api/queues/%2F/orders-dlq/indices
```

**AWS SQS**:
```bash
aws sqs list-queues --query 'QueueUrls[?contains(QueueUrl, \'orders-dlq\')]'
```

---

## **6. Tools & Libraries**
| Tool/Library               | Purpose                                      | Example                     |
|----------------------------|----------------------------------------------|-----------------------------|
| **OpenTelemetry SDK**      | Distributed tracing                           | `opentelemetry-java`        |
| **Loki/Grafana**           | Log aggregation                               | `loki-distributed`          |
| **Kafka Consumer Offsets** | Track processing lag                          | `kafka-consumer-groups`     |
| **Sentry**                 | Error tracking                                | `@sentry/node`              |
| **Serilog**                | Structured logging                           | `Serilog.Sinks.Sequential`  |

---

## **7. Common Pitfalls & Mitigations**
| Pitfall                          | Mitigation                                  |
|----------------------------------|--------------------------------------------|
| Missing `trace_id` in headers    | Enforce header injection in producers.      |
| No DLQ configuration             | Set up DLQs with TTL and monitoring.        |
| Overhead from logging            | Sample logs (e.g., 1% of messages).         |
| Correlation ID collisions        | Use UUIDs with namespace.                   |

---

## **8. Related Patterns**
1. **Circuit Breaker** – Limits cascading failures in event-driven flows.
2. **Saga Pattern** – Manages distributed transactions with compensating actions.
3. **Schema Registry** – Ensures backward/forward compatibility of messages.
4. **Resilience Patterns** (Retry, Bulkhead) – Handles transient failures gracefully.

---
**Further Reading**:
- [CNCF Distributed Tracing Guide](https://github.com/cncf/distributed-tracing-taxonomy)
- [Kafka Debugging Cheatsheet](https://kafka.apache.org/documentation/#debug)