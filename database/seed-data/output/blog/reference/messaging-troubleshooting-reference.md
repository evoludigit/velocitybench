# **[Pattern] Messaging Troubleshooting – Reference Guide**

---
## **Overview**
Messaging systems are foundational to distributed architectures, enabling real-time data exchange, event-driven workflows, and decoupled components. However, messaging failures—due to network issues, consumer lag, schema mismatches, or infrastructure constraints—can disrupt business continuity. This guide outlines a structured **Messaging Troubleshooting Pattern**, combining diagnostic frameworks, logging strategies, and recovery workflows. It covers:
- **Common failure modes** (e.g., producer/consumer deadlocks, partition rebalancing).
- **Proactive monitoring metrics** (e.g., enqueue/dequeue rates, latency percentiles).
- **Diagnostic tools** (CLI, SDKs, observability platforms).
- **Recovery procedures** (rerouting, backpressure, manual intervention).

Use this pattern to systematically isolate, debug, and resolve messaging failures while minimizing downtime.

---

## **Key Concepts & Schema Reference**
### **1. Messaging System Topology**
A typical messaging architecture consists of the following components:

| **Component**       | **Description**                                                                                     | **Common Failure Scenarios**                          |
|---------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------|
| **Producer**        | Application/service emitting messages (e.g., Kafka `Producer`, RabbitMQ `Publisher`).            | Throttling, serialization errors, broker timeouts.      |
| **Broker**          | Message broker (e.g., Apache Kafka, AWS SNS/SQS, RabbitMQ).                                      | Disk full, broker crash, partition leadership changes.  |
| **Queue/Topic**     | Logical channel where messages are stored/received.                                               | Backpressure, TTL violations, consumer lag.            |
| **Consumer**        | Application/service processing messages (e.g., Kafka `Consumer`, SQS `Worker`).                  | Overloaded consumers, schema drift, network partitions. |
| **Monitoring**      | Tools (Prometheus, Datadog, Kafka Metrics) tracking system health.                                | Alert fatigue, missing metrics.                      |

---

### **2. Failure Modes & Symptoms**
Below is a taxonomy of messaging failures with observable symptoms:

| **Failure Type**          | **Symptoms**                                                                                     | **Root Causes**                                      |
|---------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------|
| **Producer Failures**     | Messages are not enqueued (retries exhausted).                                                 | Authentication errors, quota limits, network drops.   |
| **Broker Failures**       | Topic partitions unavailable, leader elections stalled.                                         | Disk I/O bottlenecks, Zookeeper/Kafka Controller issues. |
| **Consumer Lag**          | `lag` metric spikes, messages piling up in queues.                                             | Slow processing, insufficient consumers, schema changes. |
| **Schema Mismatch**       | Deserialization errors (`SchemaMismatchException` in Avro, `InvalidFormatException` in Protobuf). | Backward-incompatible schema updates.                |
| **Network Partitions**    | Brokers/consumers unable to communicate (e.g., Kafka `NotEnoughReplicasException`).             | Subnet failures, DNS issues.                        |
| **Resource Exhaustion**   | Broker OOM, consumer memory leaks, disk space depletion.                                        | Unbounded queues, inefficient serializers.           |

---

## **Implementation Details**
### **1. Diagnostic Workflow**
Adopt a **structured troubleshooting approach**:

1. **Observe Symptoms**
   - Check logs (e.g., `ProducerRecord` errors in Kafka, `BasicDeliver` failures in RabbitMQ).
   - Review metrics (e.g., `record-send-rate`, `record-receive-rate`, `consumer-lag`).

2. **Isolate the Component**
   - Use **binary search**: Is the issue at the producer, broker, or consumer?

3. **Reproduce Locally**
   - Test with a minimal producer/consumer against a single broker partition.

4. **Apply Fixes**
   - Mitigate (e.g., increase consumer parallelism) or resolve (e.g., update schema).

5. **Validate**
   - Confirm metrics return to baseline and reprocess no longer fails.

---

### **2. Key Metrics to Monitor**
Track these metrics to detect anomalies early:

| **Metric**                     | **Tool**               | **Threshold Alert**                          | **Action**                                  |
|--------------------------------|------------------------|-----------------------------------------------|---------------------------------------------|
| `record-send-rate`             | Kafka Producer Metrics | >95% of max throughput for 5 minutes.       | Scale producers or adjust batch size.       |
| `consumer-lag`                 | Kafka Consumer Groups  | Lag >10x avg processing time for >1 hour.    | Scale consumers or optimize processing.     |
| `disk-usage`                   | Broker OS Metrics      | >80% disk usage.                              | Clean old messages or add storage.          |
| `request-latency`              | Prometheus             | 99th percentile >500ms for 15 minutes.       | Investigate broker load or network issues.  |
| `retry-rate`                   | SDL (Stream Data Library) | >1% of total messages.                     | Fix producer/consumer errors.               |

---
## **Schema Reference**
### **1. Message Schema Validation**
Ensure producers/consumers agree on message schemas using:
- **Avro**: Schema registry (e.g., Confluent Schema Registry).
- **Protobuf**: Compile with the same `.proto` file.
- **JSON**: Enforce a schema with tools like [JSON Schema](https://json-schema.org/).

**Example Schema Validation Workflow**:
1. **Producer** publishes message → **Schema Registry** validates against latest schema.
2. **Consumer** checks schema compatibility before deserialization.
3. If mismatch, fail fast with `SchemaValidationException`.

---
## **Query Examples**
### **1. Kafka CLI Commands for Troubleshooting**
| **Use Case**               | **Command**                                                                                     | **Output Interpretation**                          |
|----------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------|
| Check consumer lag         | `kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>`               | Lag >0 indicates processing delay.                 |
| List topics/partitions     | `kafka-topics --bootstrap-server <broker> --list`                                               | Missing topics may cause producer failures.         |
| Inspect message offsets     | `kafka-consumer-groups --bootstrap-server <broker> --group <group> --describe --verify-only` | Laggy partitions show up as `-1` (behind).          |
| Reassign partitions        | `kafka-reassign-partitions --bootstrap-server <broker> --reassignment-json-file <file>.json`    | Useful after broker failures.                     |

---
### **2. RabbitMQ Troubleshooting**
| **Use Case**               | **Command**                                                                                     | **Output Interpretation**                          |
|----------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------|
| Check queue length         | `rabbitmqctl list_queues name messages_ready messages_unacknowledged`                           | `messages_unacknowledged` >0 indicates unprocessed messages. |
| Monitor consumer lag       | `rabbitmqctl list_connections` + manual calculation of `deliver-get` rate.                     | High `deliver-get` rate with low `ack` rate = lag.  |
| Force message re-delivery  | `rabbitmqadmin declare exchange=<exchange> routing_key=<key> properties='{"x-delay":0}'`       | Bypass TTL for stuck messages.                     |

---
### **3. SQL Query for SQS Lag Detection**
```sql
SELECT
    queue_url,
    ApproximateNumberOfMessagesVisible,
    ApproximateNumberOfMessagesNotVisible,
    LastModifiedTimestamp
FROM
    "AWS_SQS_Metrics"
WHERE
    ApproximateNumberOfMessagesVisible > 1000  -- Threshold for lag
    AND LastModifiedTimestamp > NOW() - INTERVAL '5 minutes';
```

---

## **Recovery Procedures**
### **1. Mitigate Consumer Lag**
- **Scale consumers**: Add more workers to parallelize processing.
- **Adjust batch size**: Increase `fetch.min.bytes` (Kafka) or `prefetch_count` (RabbitMQ).
- **Prioritize messages**: Use TTL or message attributes to drop old messages.

### **2. Handle Schema Migrations**
1. **Backward-compatible changes**: Add optional fields (Avro).
2. **Fallback logic**: Consumers handle unknown fields gracefully.
3. **Schema evolution**: Use tools like [Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html).

### **3. Broker Recovery**
| **Scenario**               | **Action**                                                                                       |
|----------------------------|-------------------------------------------------------------------------------------------------|
| Broker crash               | Reassign partitions using `kafka-reassign-partitions`.                                         |
| Disk full                  | Clean old messages or add storage (e.g., `kafka-log-cleaner`).                              |
| Network partition          | Check broker connectivity; retry `LeaderElection` if needed.                                   |

---
## **Related Patterns**
1. **[Idempotent Producer](https://patterns.devopsish.com/patterns/idempotent-producer/)**
   - Ensures duplicate messages are safely handled.
2. **[ircuit Breaker](https://patterns.devopsish.com/patterns/circuit-breaker/)**
   - Prevents cascading failures in consumers.
3. **[Dead Letter Queue (DLQ)](https://patterns.devopsish.com/patterns/dead-letter-queue/)**
   - Isolates unprocessable messages for manual review.
4. **[Exactly-Once Processing](https://patterns.devopsish.com/patterns/exactly-once-processing/)**
   - Guarantees message processing without duplicates.
5. **[Event Sourcing](https://patterns.devopsish.com/patterns/event-sourcing/)**
   - Reconstructs state from message history (useful for auditing).

---
## **Tools & Libraries**
| **Tool/Library**       | **Purpose**                                                                                     | **Link**                                      |
|------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Confluent Platform** | Kafka monitoring, schema registry.                                                            | [confluent.io](https://www.confluent.io/)    |
| **Prometheus + Grafana** | Custom metrics visualization for messaging systems.                                           | [prometheus.io](https://prometheus.io/)      |
| **Burrow**             | Consumer lag detection for Kafka.                                                              | [github.com/lightbend/burrow](https://github.com/lightbend/burrow) |
| **Skaffold**           | Debug Kafka locally with Docker.                                                               | [skaffold.dev](https://skaffold.dev/)          |
| **AWS SQS/SNS ALB**    | Auto-scaling for SQS/SNS consumers.                                                           | [aws.amazon.com/sqs](https://aws.amazon.com/sqs/) |

---
## **Best Practices**
1. **Log Contextually**:
   - Include `message_key`, `partition`, and `offset` in logs for traceability.
2. **Set Alerts**:
   - Alert on `consumer-lag > 2x avg` or `producer-error-rate > 0.1%`.
3. **Test Failures**:
   - Simulate broker crashes or network partitions in staging.
4. **Document Schemas**:
   - Version schemas and track backward compatibility.
5. **Automate Recovery**:
   - Use **Kafka Consumer Offset Commit** or **SQS Visibility Timeout** to resume processing.

---
**End of Guide**