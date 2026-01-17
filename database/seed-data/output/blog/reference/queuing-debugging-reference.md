**[Pattern] Queuing Debugging Reference Guide**

---
### **Overview**
The **Queuing Debugging** pattern provides a structured approach to diagnose, trace, and resolve issues in distributed systems where messages are processed asynchronously via queues (e.g., Kafka, RabbitMQ, AWS SQS). This pattern helps identify bottlenecks, message loss, duplication, or processing failures by examining queue metadata, producer/consumer logs, and system dependencies. It ensures traceability across services and reduces blind spots in observability while maintaining scalability.

---
### **Key Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Message Flow**      | The lifecycle of a message: *published → enqueued → consumed → processed → acknowledged*. Debugging focuses on anomalies at each stage.                                                                 |
| **Queue Partitions**  | In partitioned queues (e.g., Kafka), messages are distributed across partitions. Debugging may require analyzing individual partitions for OOM errors or skew.                          |
| **Message Idempotency** | Ensures reprocessing the same message doesn’t cause side effects. Debugging may check for duplicate handling logic or transactional retries.                                         |
| **TTL & Expiry**      | Time-to-live settings define when messages are discarded. Stuck messages may hint at consumer delays or processing deadlocks.                                                                          |
| **Dead/Late Letter Queues** | Alternate queues for failed or delayed messages (e.g., DLQ/DeadMQ). Debugging involves inspecting these queues for root causes (e.g., retries exceeding limits).                     |
| **Consumer Lag**      | The gap between the latest message in the queue and the highest offset consumed by a group. High lag may indicate backpressure or slow processing.                                            |
| **Eventual Consistency** | Queues often expose stale states. Debugging aligns timestamps across producers, consumers, and databases.                                                                                              |

---
### **Implementation Details**

#### **1. Debugging Workflow**
Follow this systematic approach to diagnose queuing issues:

1. **Reproduce the Problem**
   - Trigger the issue via controlled test data (e.g., spam high-volume messages).
   - Use feature flags to isolate the problematic service.

2. **Gather Metadata**
   - Logs: Producer/consumer timestamps, queue metrics (e.g., `consumer_lag`, `message_rate`).
   - Tracing: Correlate spans across services using a unique `trace_id` or `message_id`.
   - Schemas: Validate message payloads for corruption (e.g., JSON schema mismatches).

3. **Analyze Bottlenecks**
   - **Producer Side**: Check for throttling, serialization errors, or failed `publish()` calls.
     - *Tooling*: Monitor queue metrics (e.g., `queue_depth`, `publish_latency`).
   - **Queue Side**: Query partition stats (e.g., `offset_lag`, `replication_status`).
     - *Tooling*: Use CLI tools (e.g., `kafka-consumer-groups`, `aws sqs listqueues`).
   - **Consumer Side**: Look for:
     - High CPU/network usage.
     - Unhandled exceptions in processing (e.g., `ConsumeFailedException`).
     - Deadlocks in task queues (e.g., Redis queues).

4. **Validate Fixes**
   - Test with back-to-back repros.
   - Monitor for regression in `consumer_lag` or `message_drop_rate`.

---

#### **2. Schema Reference**
| Metric/Property          | Description                                                                                       | Example Tools/Queries                                                                                  |
|--------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Queue Depth**          | Total unprocessed messages in the queue.                                                        | `aws sqs get-queue-attributes --queue-url <URL> --attribute-names ApproximateNumberOfMessages`        |
| **Consumer Lag**         | Time delay between producer and consumer offsets.                                                | `kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>`                       |
| **Message Size**         | Payload size (GBs may cause consumer crashes).                                                   | `kafka-console-producer --topic <topic> --print-key --bootstrap-server <broker>` (estimate avg size) |
| **Partition Offset**     | Current read/write position per partition.                                                       | `kafka-consumer-groups --bootstrap-server <broker> --describe --group <group> --topic <topic>`         |
| **Publish Errors**       | Failed attempts to enqueue messages.                                                             | Consumer logs (`ERROR`/`WARN` filters for `publisher` keywords).                                      |
| **Consumer Errors**      | Processing failures (e.g., `TimeoutException`).                                                 | Application logs (filter for `consumer_<service>`).                                                 |
| **DLQ Entries**          | Dead-letter queue contents (for retries/failed processing).                                      | `aws sqs list-queue-attributes --queue-url <dlq-url> --attribute-names All`.                           |

---

#### **3. Query Examples**
##### **Kafka**
**Check Consumer Lag:**
```bash
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-group --topic my-topic
```
*Output:*
```plaintext
GROUP       TOPIC      PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG       CONSUMERS
my-group    my-topic   0          1000              2000             1000      1
```

**Inspect Partition Offsets:**
```bash
kafka-consumer-groups --bootstrap-server localhost:9092 --group my-group --describe --topic my-topic --partition 0
```

**List Failed Messages (DLQ):**
```bash
kafka-console-consumer --bootstrap-server localhost:9092 --topic my-dlq --from-beginning
```

##### **AWS SQS**
**Get Queue Attributes:**
```bash
aws sqs get-queue-attributes --queue-url https://sqs.us-east-1.amazonaws.com/123456789/my-queue --attribute-names All
```
*Key Attributes to Check:*
- `ApproximateNumberOfMessages`: Queue depth.
- `ApproximateNumberOfMessagesNotVisible`: Messages in flight.

**Poll for Messages:**
```bash
aws sqs receive-message --queue-url https://sqs.us-east-1.amazonaws.com/123456789/my-queue --max-number-of-messages 10
```

##### **RabbitMQ**
**Check Queue Length:**
```bash
rabbitmqctl list_queues name messages_ready messages_unacknowledged
```
*Output:*
```plaintext
Listing queues ...
my-queue     1000     200                # Unacknowledged messages
```

**Inspect Consumer Logs:**
```bash
journalctl -u rabbitmq-server -f  # For systemd-based deployments
```

---
#### **4. Common Debugging Scenarios & Tools**
| Scenario                        | Tools/Commands                                                                                     | Mitigation Steps                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **High Consumer Lag**            | `kafka-consumer-groups --describe`                                                               | Scale consumers horizontally; optimize processing logic.                                             |
| **Message Duplication**          | Check consumer `delivery_tag` for retries; validate idempotency in payload.                  | Use exactly-once semantics (e.g., Kafka transactions); deduplicate via message payloads.          |
| **Producer Throttling**          | Monitor `publish_latency` in metrics; check broker-side `request_rate`.                         | Increase broker resources; batch messages; use async producers.                                      |
| **Dead Messages in DLQ**         | Inspect `sqs.get-queue-attributes --attribute-names All` for DLQ.                             | Review processing logic for crashes; implement circuit breakers.                                     |
| **Schema Mismatch**              | Validate payloads with OpenAPI/JSON Schema (e.g., `jsonschema validate`).                        | Update producer/consumer schemas; use schema registry (e.g., Confluent).                           |

---

#### **5. Related Patterns**
- **[Circuit Breaker Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)**
  *Use when*: Queues lead to cascading failures (e.g., consumer overload).
  *Integration*: Embed circuit breakers in consumers to avoid DLQ overflow.

- **[Retry with Backoff](https://microservices.io/patterns/data/retry.html)**
  *Use when*: Transient errors (e.g., network timeouts) cause message loss.
  *Implementation*: Exponential backoff in consumers (e.g., `retry` library in Java).

- **[Saga Pattern](https://microservices.io/patterns/data/saga.html)**
  *Use when*: Debugging requires cross-service transactional visibility.
  *Integration*: Correlate queue events with saga `compensating transactions`.

- **[Distributed Tracing](https://www.elastic.co/guide/en/elasticsearch/reference/current/trace.html)**
  *Use when*: Trace message flow across services.
  *Tools*: OpenTelemetry, Jaeger, or Datadog traces with `trace_id` in message headers.

---
#### **6. Best Practices**
1. **Instrumentation**:
   - Inject `timestamp`, `trace_id`, and `source_service` into messages.
   - Log at `INFO`/`DEBUG` level for all queue events (e.g., `ConsumerRecord` timestamps).

2. **Monitoring**:
   - Set alerts for:
     - `consumer_lag > threshold` (e.g., 10 minutes).
     - `publish_errors > 0` for 5 consecutive minutes.
   - Use tools: Prometheus + Grafana (for metrics), Elasticsearch (for logs).

3. **Testing**:
   - Load test with tools like [Locust](https://locust.io/) to simulate high queue depth.
   - Validate idempotency by reprocessing messages.

4. **Schema Evolution**:
   - Use backward-compatible schemas (e.g., add optional fields).
   - Version message schemas (e.g., Avro with `namespace`).

---
#### **7. Example: Debugging a Stuck Consumer**
**Symptom**: `ConsumerGroup` shows `LAG: 5000`, but no errors in logs.
**Steps**:
1. **Check Metrics**:
   ```bash
   kafka-consumer-groups --describe --group my-group
   ```
   *Output*: `current-offset: 1000`, `log-end-offset: 6000` → **lag = 5000**.

2. **Inspect Consumer Logs**:
   ```bash
   grep "consumer-my-group" /var/log/myapp/consumer.log | tail -n 20
   ```
   *Find*: No `ERROR` logs, but `WARNING: Task timed out after 30s`.

3. **Analyze Processing Logic**:
   - External API call (e.g., `POST /payments`) was slow.
   - Consumer used blocking `Future.get()` instead of async.

4. **Fix**:
   - Refactor to use non-blocking I/O (e.g., `CompletableFuture` in Java).
   - Monitor `/payments` latency separately.

5. **Validate**:
   - Retest lag: `lag` drops to `0` after 5 minutes.
   - Confirm no messages in DLQ: `kafka-consumer-groups --describe --topic my-dlq`.