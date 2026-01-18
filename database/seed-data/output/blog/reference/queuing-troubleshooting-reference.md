# **[Pattern] Queuing Troubleshooting Reference Guide**

---

## **Overview**
This guide provides a structured approach to diagnosing, resolving, and preventing common issues in queuing systems. Whether dealing with high latency, message loss, or system stalls, this guide covers root-cause analysis, monitoring best practices, and corrective actions for distributed and in-memory queue systems (e.g., Kafka, RabbitMQ, AWS SQS, Redis Streams). It emphasizes observable metrics, log patterns, and pattern-specific workflows to streamline troubleshooting efforts.

---

## **Key Concepts & Implementation Details**

### **1. Common Queuing Patterns & Failure Modes**
| **Pattern**               | **Description**                                                                 | **Failure Mode**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **Producer-Publisher**    | Messages are enqueued by producers (e.g., microservices, IoT devices).         | Overload, duplicate messages, or throttling due to rate limits.                 |
| **Consumer-Subscriber**   | Consumers process messages from queues (e.g., async tasks, event handlers).    | Stalled consumers, backpressure, or unhandled exceptions causing requeue loops. |
| **Dead Letter Queue (DLQ)**| Failed messages are routed to a DLQ for later inspection.                     | Unmonitored DLQ growth or incorrect routing rules.                             |
| **Priority Queue**        | Messages with higher priority are processed first.                             | Starvation of low-priority queues or misconfigured priorities.                   |
| **Distributed Locking**   | Ensures only one consumer processes a message concurrently.                   | Lock timeouts or contention leading to duplicate processing.                     |
| **Exactly-Once Semantics**| Guarantees each message is processed once (e.g., Kafka transactions).         | Transaction failures or incomplete commits.                                     |

---

### **2. Troubleshooting Workflow**
Follow this structured approach to diagnose issues:

#### **Step 1: Identify the Symptom**
- **Symptom:** High latency in message processing?
- **Symptom:** Messages disappearing from the queue?
- **Symptom:** Consumers crashing repeatedly?
- **Symptom:** Queue growing uncontrollably?

#### **Step 2: Gather Observability Data**
| **Data Source**          | **Key Metrics/Logs to Check**                                                                 |
|--------------------------|------------------------------------------------------------------------------------------------|
| **Monitoring Tools**     | Queue depth, enqueue/dequeue rates, consumer lag (Kafka: `kafka-consumer-groups`, RabbitMQ: `rabbitmqctl list_queues`). |
| **Application Logs**     | Error rates, retry attempts, DLQ entries, or timeouts.                                       |
| **Infrastructure Logs**  | Disk I/O, memory pressure, or network bottlenecks impacting message persistence.               |
| **Dead Letter Queues (DLQ)** | Inspect failed messages for patterns (e.g., schema validation errors, network failures).   |

#### **Step 3: Root-Cause Analysis**
Use the following decision tree for common issues:

1. **Are messages disappearing?**
   - Check for **acknowledgment (ACK) failures** (consumer crashes without sending ACK).
   - Verify **persistent storage** (e.g., Kafka log retention, RabbitMQ disk writes).
   - Audit **security policies** (e.g., VPC peering issues, IAM permissions).

2. **Is the queue growing uncontrollably?**
   - **Producers:** Check for **rate limits** or **unacked messages** (consumers falling behind).
   - **Consumers:** Look for **slow processing** (e.g., external API calls timing out).
   - **Schema changes:** Validate backward compatibility.

3. **Are consumers crashing?**
   - Review **stack traces** for unhandled exceptions.
   - Check **resource constraints** (e.g., CPU/memory limits in Kubernetes pods).
   - Audit **dependency failures** (e.g., databases, third-party APIs).

4. **Is there high latency?**
   - **Network:** Measure **end-to-end delays** (e.g., `ping`, `traceroute`).
   - **Serialization:** Profile **message size** and **de/serialization overhead**.
   - **Backpressure:** Monitor **consumer lag** (e.g., Kafka `lag` metric).

#### **Step 4: Take Corrective Action**
| **Issue**                     | **Solution**                                                                                     | **Mitigation**                                                                     |
|-------------------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Message Loss**              | Enable **idempotent producers**, use **Kafka transactions**, or **RabbitMQ `x-dead-letter-exchange`**. | Implement **retry policies** with exponential backoff.                            |
| **Consumer Stalls**           | Scale consumers horizontally, optimize **batch processing**, or **tune prefetch settings**.     | Use **auto-scaling** (e.g., Kubernetes HPA) based on queue depth.                 |
| **DLQ Overflow**              | Review **DLQ retention policies**, alert on growth, or **process DLQ manually**.                | Automate **DLQ reprocessing** with a dedicated consumer.                          |
| **Network Partitioning**      | Use **Kafka `min.insync.replicas`** or **RabbitMQ `ha-mode`** for high availability.             | Monitor **partition health** (e.g., `kafka-broker-api-versions`).                    |
| **Slow Processing**           | Optimize **SQL queries**, cache frequent lookups, or **parallelize work**.                      | Use **async I/O** (e.g., `asyncio` in Python) or **stream processing** (e.g., Flink). |

#### **Step 5: Prevent Reoccurrence**
- **Automate Alerts:** Set up dashboards (e.g., Prometheus + Grafana) for:
  - Queue depth > threshold.
  - Consumer lag > 1000 messages.
  - DLQ growth rate > X messages/minute.
- **Chaos Engineering:** Test failure scenarios (e.g., broker outages, network drops).
- **Document SLAs:** Define acceptable **end-to-end latencies** and **error budgets**.

---

## **Schema Reference**
Below are key schema fields for common queuing systems. Use these to query metrics and logs.

### **1. Kafka**
| **Metric/Log Field**         | **Description**                                                                 | **Tools to Query**                          |
|------------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec` | Incoming message rate per topic.                                             | JMX, Kafka Manager, Prometheus exporter.    |
| `kafka.consumer:type=ConsumerTopicMetrics,name=RecordsLag`  | Difference between latest offset and commit offset.                           | `kafka-consumer-groups --bootstrap-server`. |
| `kafka.log:type=Log,name=Size` | Disk space used by topic logs.                                                | `kafka-topics --describe`.                   |
| `kafka.consumer:type=ConsumerNetworkMetrics,name=RequestLatencyAvg` | Avg time to fetch messages.                                                  | `kafka-producer-perf-test`.                  |

**Example JQL (JMX Query Language):**
```java
NEW String[]{
    "kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec,topic=\"orders\""
}, new Object[]{Integer.class, Long.class}
```

---

### **2. RabbitMQ**
| **Metric/Log Field**         | **Description**                                                                 | **Tools to Query**                          |
|------------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| `queue_messages`             | Current message count in the queue.                                             | `rabbitmqctl list_queues`.                  |
| `queue_declare_ok`           | Successful queue declarations.                                                 | Management API: `/api/queues/%2F`.          |
| `consumer_count`             | Active consumers per queue.                                                     | `rabbitmqctl list_queues detail`.           |
| `deliver_get`                | Messages delivered to consumers.                                                | `rabbitmqctl list_consumers`.               |

**Example `rabbitmqctl` Command:**
```bash
rabbitmqctl list_queues name messages_ready messages_unacknowledged consumer_count
```

---

### **3. AWS SQS**
| **Metric/Log Field**         | **Description**                                                                 | **CloudWatch Metric**                     |
|------------------------------|---------------------------------------------------------------------------------|-------------------------------------------|
| `ApproximateNumberOfMessagesVisible` | Messages waiting to be processed.                                             | `ApproximateNumberOfMessagesVisible`.     |
| `ApproximateNumberOfMessagesNotVisible` | Messages in flight (being processed).                                         | `ApproximateNumberOfMessagesNotVisible`.  |
| `NumberOfEmptyReceives`      | Failed to receive messages (e.g., throttle).                                   | `NumberOfEmptyReceives`.                  |
| `SentToDLQ`                  | Messages moved to DLQ.                                                          | Custom CloudWatch Logs filter.            |

**CloudWatch Query Example:**
```sql
stats avg(ApproximateNumberOfMessagesVisible)
by QueueName
from now-1h
```

---

## **Query Examples**

### **1. Kafka Consumer Lag (Bash)**
```bash
kafka-consumer-groups --bootstrap-server broker:9092 \
  --group my-group \
  --describe \
  --topic orders
```
**Output:**
```
TOPIC         PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
orders        0          10000          15000             5000
```

---

### **2. RabbitMQ Queue Depth (Python)**
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
queue_info = channel.queue_info('orders')

print(f"Messages ready: {queue_info['messages_ready']}")
print(f"Messages unacked: {queue_info['messages_unacknowledged']}")
connection.close()
```

---

### **3. AWS SQS Queue Depth (AWS CLI)**
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=orders \
  --start-time $(date -u -v-1h +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average
```

---

## **Related Patterns**
1. **[Idempotent Producer](https://github.com/pattern-explorer/idempotent-producer)**
   - Ensures messages are not reprocessed after failures.
   - *Use case:* Compensate for network partitions or duplicate sends.

2. **[Circuit Breaker](https://github.com/pattern-explorer/circuit-breaker)**
   - Stops sending requests to failing services to prevent cascading failures.
   - *Use case:* Protect consumers from slow or unresponsive dependencies.

3. **[Retry with Backoff](https://github.com/pattern-explorer/retry-backoff)**
   - Exponentially increases retry delays for transient errors.
   - *Use case:* Handle temporary queue unavailability.

4. **[Event Sourcing](https://github.com/pattern-explorer/event-sourcing)**
   - Stores state changes as an append-only sequence of events.
   - *Use case:* Rebuild queue state from logs if persistence is lost.

5. **[Saga Pattern](https://github.com/pattern-explorer/saga)**
   - Coordinates transactions across multiple services.
   - *Use case:* Handle distributed transactions when using queues for workflows.

---

## **Glossary**
| **Term**               | **Definition**                                                                 |
|------------------------|--------------------------------------------------------------------------------|
| **ACK**                | Acknowledgment sent by consumer to confirm message processing.                |
| **Backpressure**       | Mechanism to slow down producers when consumers can’t keep up.                 |
| **DLQ**                | Dead Letter Queue for failed messages that couldn’t be processed.              |
| **Exactly-Once**       | Guarantee that each message is processed exactly once.                         |
| **Idempotent Producer**| Producer ensures duplicate messages don’t cause side effects.                   |
| **Lag**                | Difference between the latest message offset and the offset consumed.         |
| **Partition Tolerance**| System continues operating despite network splits (e.g., Kafka ISR).          |
| **Prefetch Count**     | Number of unacknowledged messages a consumer can fetch (RabbitMQ/Kafka).      |

---
**Last Updated:** [Date]
**Contributors:** [List of maintainers]