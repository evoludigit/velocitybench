# **[Pattern] Queuing Troubleshooting – Reference Guide**

---
## **Overview**
Queuing systems are fundamental to distributed architectures, enabling scalable event processing, workflow automation, and async communication. When issues arise—such as **latency spikes, consumer blockages, poison pills, or system-wide failures**—troubleshooting requires a structured approach. This guide covers **diagnostic methods, metrics, and patterns** for identifying and resolving common queuing problems in systems like **Kafka, RabbitMQ, AWS SQS/SNS, or Azure Service Bus**.

Key areas addressed:
- **Performance bottlenecks** (e.g., consumer lag, backpressure)
- **Error handling** (e.g., retries, dead-letter queues)
- **Resource constraints** (e.g., memory leaks, disk exhaustion)
- **Network/dependency issues** (e.g., broker unavailability, throttling)

---
## **Schema Reference**
Below are standardized metrics and structures for troubleshooting:

| **Category**               | **Metric/Property**          | **Description**                                                                                                                                                                                                 | **Tools to Check**                     |
|----------------------------|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| **Broker Health**          | Broker Replication Lag      | Distance between leader and follower partitions (for replication-based brokers).                                                                                                                       | Kafka: `kafka-consumer-groups`, Kafka Manager; RabbitMQ: `rabbitmqctl` |
|                            | Node Disks/CPU Load         | Disk saturation, CPU throttling, or high GC pauses.                                                                                                                                                     | `iotop`, `top`, Prometheus/Grafana     |
|                            | Partition Count/Size        | Uneven distribution of partitions or excessive message sizes.                                                                                                                                             | Broker CLI (e.g., `kafka-topics`)      |
| **Consumer State**         | Consumer Lag                | Messages lagging behind the broker’s commit index (high lag = processing delay).                                                                                                                              | Kafka: `kafka-consumer-groups --describe`; RabbitMQ: `rabbitmqctl list_consumers` |
|                            | Processing Time (p50/p99)   | Latency percentiles to detect slow consumers or hot partitions.                                                                                                                                         | Metrics: Datadog, New Relic             |
|                            | Active Consumers            | Number of active consumers per queue/partition.                                                                                                                                                     | Broker CLI, Queue Manager UI           |
| **Error Handling**         | Retry Count                 | Exponential backoff or fixed retries per message.                                                                                                                                                       | Broker logs, DLQ metrics                |
|                            | Dead-Letter Queue (DLQ)     | Accumulation of poison messages (e.g., malformed payloads).                                                                                                                                             | Broker-specific DLQ views               |
| **Network/Dependencies**   | TLS Handshake Failures      | SSL/TLS negotiation errors between clients/brokers.                                                                                                                                                     | Broker logs, `openssl s_client`         |
|                            | Throttling Limits           | Client-side or broker-side rate limits (e.g., Kafka’s `fetch.max.bytes`).                                                                                                                                | Broker configs, client telemetry       |
| **Schema Validation**      | Schema Registry Errors      | Mismatched Avro/Protobuf schemas causing deserialization failures.                                                                                                                                         | Confluent Schema Registry, Avro tools  |

---

## **Query Examples**
### **1. Identifying Consumer Lag in Kafka**
```bash
# List consumer groups and lag (Kafka CLI)
kafka-consumer-groups --bootstrap-server <broker>:9092 --describe \
  --group <group-id>

# Filter lag > X minutes (jq for JSON parsing)
kafka-consumer-groups --bootstrap-server <broker>:9092 --describe \
  | jq -r '.groups[] | select(.topic == "my-topic") | .members[] | select(.lag > 60 * 10)'
```

#### **Interpretation:**
- **Lag > 0**: Consumer is falling behind.
- **Lag %99 > 1000ms**: Hot partition detected.

---

### **2. RabbitMQ: Checking Consumer Health**
```bash
# List consumers and queue metrics
rabbitmqctl list_consumers --vhost / my_queue

# Filter stalled consumers (using `rabbitmqadmin`)
curl -s http://admin:pass@localhost:15672/api/consumers | jq '.[] | select(.consumer_tag == "my_tag") | .consuming | .lag'
```

#### **Troubleshooting Flags:**
- **`consuming == false`**: Consumer crashed or disconnected.
- **`lag > 1000`**: Backpressure detected.

---

### **3. AWS SQS: Detecting Throttling**
```bash
# Check throttled requests (CloudWatch Metrics)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfThrottledRequests \
  --dimensions Name=QueueName,Value=my-queue \
  --start-time $(date -u -v-2D +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 --statistics Average

# SNS: Check failed deliveries
aws sns get-policy --policy-arn <topic-arn> | jq '.Policy | .Statement[].Condition | .Arn[0]'
```

#### **Actions:**
- **Increase `SendingLimit`** (if throttled).
- **Enable DLQ** for failed deliveries.

---

## **Step-by-Step Troubleshooting Workflow**
### **1. Verify Broker Health**
- **Check disk/CPU**: Use `iotop` or `top` to identify disk I/O bottlenecks.
- **Replication lag**: For Kafka, ensure followers are not lagging:
  ```bash
  kafka-topics --describe --topic my-topic --bootstrap-server <broker>
  ```

### **2. Analyze Consumer Lag**
- **Kafka**: Use `kafka-consumer-groups` to spot lagging topics/partitions.
- **RabbitMQ**: Monitor `consumer_lag` in `rabbitmqctl list_queues`.
- **Action**: Scale consumers or optimize processing (e.g., batch messages).

### **3. Investigate Errors**
- **Dead-Letter Queues (DLQ)**: Check for poison messages:
  ```bash
  # RabbitMQ example
  rabbitmqadmin list queues name=my-dlx-queue --vhost /
  ```
- **Retry loops**: Audit consumer code for infinite retries.

### **4. Network/Dependency Issues**
- **TLS errors**: Test connectivity with `openssl s_client -connect <broker>:9443`.
- **Throttling**: Adjust client-side `fetch.max.bytes` or broker-side quotas.

### **5. Schema Mismatches**
- **Validate Avro/Protobuf schemas** against producer/consumer versions:
  ```bash
  # Compare schemas in Confluent Registry
  curl -X GET http://localhost:8081/subjects/my-topic-value/versions/latest
  ```

---

## **Related Patterns**
1. **[Idempotent Producer/Consumer](pattern-idempotent-producer.md)**
   - Ensures retries don’t duplicate side effects.
2. **[Circuit Breaker for Queues](pattern-circuit-breaker.md)**
   - Temporarily blocks consumers during broker outages.
3. **[Exponential Backoff Retries](pattern-retry-strategy.md)**
   - Mitigates transient failures with adaptive delays.
4. **[Multi-Tenant Queues](pattern-multi-tenant-queues.md)**
   - Isolates traffic for high-latency users.

---
## **Tools & References**
- **Monitoring**:
  - [Kafka Lag Exporter](https://github.com/danielqsj/kafka-lag-exporter)
  - [RabbitMQ Prometheus Plug-in](https://www.rabbitmq.com/monitoring.html)
- **Debugging**:
  - `kafka-reassign-partitions.sh` (Kafka partition rebalancing)
  - `rabbitmq-diagnostics` (RabbitMQ CLI tool)
- **Best Practices**:
  - [Kafka: Monitoring Consumer Lag](https://kafka.apache.org/documentation/#monitoring)
  - [RabbitMQ: Handling Backpressure](https://www.rabbitmq.com/blog/2020/04/20/backpressure-in-rabbitmq)

---
**Note**: Adjust metrics/tools based on your queue system (Kafka, RabbitMQ, SQS, etc.). Always validate changes in a staging environment.