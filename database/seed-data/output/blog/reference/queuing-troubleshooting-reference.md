# **[Pattern] Queuing Troubleshooting Reference Guide**

---

## **Overview**
Queuing systems are integral to distributed applications, enabling asynchronous processing, load balancing, and fault tolerance. However, queues can fail due to misconfigurations, resource constraints, or unexpected workload spikes. This reference guide provides structured troubleshooting techniques for common queuing issues (e.g., delays, throttling, message loss) across systems like **RabbitMQ, Apache Kafka, AWS SQS/SNS, and Azure Service Bus**.

Key focus areas include:
- **Diagnosis**: Identifying symptoms (e.g., stale tasks, consumer overload) via logs, metrics, and system alerts.
- **Remediation**: Adjusting concurrency, retry policies, and dead-letter queues (DLQs).
- **Prevention**: Proactive monitoring and queue design best practices.

---

## **Schema Reference**
| **Component**          | **Description**                                                                 | **Common Issues**                                                                 |
|------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Producer**           | Sends messages to the queue.                                                    | **High throughput**: Exceeds broker limits; **Throttling**: Rate limits enabled.   |
| **Consumer**           | Processes messages from the queue.                                              | **Backlog**: Underpowered or slow processing; **Deadlocks**: No ack/reject logic. |
| **Broker**             | Hosts the queue (e.g., RabbitMQ, Kafka).                                       | **Memory pressure**: Too many unacknowledged messages; **Network splits**: Partitioning. |
| **Message**            | Payload (data + metadata) in the queue.                                         | **Corruption**: Malformed payloads; **TTL**: Expired messages stuck.               |
| **Monitoring Tools**   | Logs, metrics, and dashboards (Prometheus, ELK, CloudWatch).                   | **Alert fatigue**: Too many non-actionable warnings; **Lag**: Delayed consumer lag. |

**Key Metrics to Monitor:**
| Metric                | Tool/Source                     | Thresholds/Alerts                          |
|-----------------------|---------------------------------|--------------------------------------------|
| `Queue Depth`         | Broker UI/API                   | >75% capacity → Scale consumers             |
| `Consumption Rate`    | Metrics (e.g., `msg_consumed`)  | <50% max rate → Investigate bottlenecks     |
| `Producer Rate`       | Application logs                | Sudden spikes → Check for retries           |
| `DLQ Size`            | Broker UI                       | >0 → Review failed retries/ack logic       |
| `Latency`             | End-to-end (P99)                | >X sec → Trace slow consumers                |

---

## **Query Examples**
### **1. Identifying Backpressure**
**Problem**: Consumers are slow, causing queue growth.

**Tools & Commands**:
- **RabbitMQ**:
  ```bash
  # Check queue length (via CLI)
  rabbitmqctl list_queues name messages_ready messages_unacknowledged
  ```
  **Expected Output**:
  ```
  Listing queues ...
  consumer_queue     5000    4500
  ```
  *Action*: Scale consumers or increase concurrency.

- **Kafka**:
  ```sql
  -- Check lag in Confluent Control Center or CLI
  kafka-consumer-groups --bootstrap-server <broker> --describe --group <group>
  ```
  **Alert Rule** (Prometheus):
  ```yaml
  - alert: HighQueueDepth
    expr: rabbitmq_queue_messages_unacknowledged{queue="*"} > 1000
    for: 5m
    labels:
      severity: warning
  ```

### **2. Diagnosing Throttling**
**Problem**: Producer is blocked due to broker limits.

**Tools**:
- **AWS SQS**:
  ```bash
  # Check throttling metrics via CloudWatch
  aws cloudwatch get-metric-statistics --namespace AWS/SQS --metric-name NumberOfThrottledMessages
  ```
  **Remediation**:
  - Increase `SendMessageBatch` limit (default: 10 messages).
  - Use **FIFO queues** for ordered processing.

- **Azure Service Bus**:
  ```bash
  # Check session/queue metrics via Azure Portal
  az monitor metrics list --resource <queue> --metric "ActiveMessageCount"
  ```
  **Fix**: Adjust `MaxConcurrentCalls` or use **prefetch counts**.

### **3. Tracing Message Loss**
**Problem**: Messages disappear without DLQ.

**Steps**:
1. **Check DLQ**:
   - **RabbitMQ**:
     ```bash
     rabbitmqctl list_queues dead_letter_exchange
     ```
   - **Kafka**:
     ```sql
     -- Enable DLQ via topic config
     kafka-configs --bootstrap-server <broker> --entity-type topics --entity-name <topic> --alter --add-config retention.ms=604800000
     ```
2. **Review Producer Code**:
   ```python
   # Example (Pika/RabbitMQ)
   channel.basic_publish(exchange='', routing_key='queue', body='data')
   channel.basic_ack(delivery_tag=method.delivery_tag)  # Ensure ack on success
   ```
3. **Enable Idempotency**: Use message IDs to deduplicate retries.

---

## **Implementation Details**
### **Key Concepts**
| Concept               | Definition                                                                 | Example Fixes                                  |
|-----------------------|-----------------------------------------------------------------------------|------------------------------------------------|
| **Persistent Messages** | Messages saved to disk (survive broker restarts).                          | Enable `durable: true` (RabbitMQ/Kafka).       |
| **Consumer Groups**   | Partition workload across consumers (Kafka/SQS).                           | Scale group size if `lag` > expected throughput.|
| **Retry Policies**    | Exponential backoff for transient failures.                               | Use `aws sqs send_message --retry<policy>`.      |
| **Dead-Letter Queues** | Redirect failed messages for analysis.                                     | Configure `x-dead-letter-exchange` (RabbitMQ). |

### **Common Pitfalls**
| Pitfall                          | Impact                                                                 | Solution                                      |
|-----------------------------------|-------------------------------------------------------------------------|-----------------------------------------------|
| **No Message TTL**               | Messages stuck forever.                                                  | Set `message_ttl` (Kafka) or `x-message-ttl` (RabbitMQ). |
| **Unbounded Concurrency**        | Consumers overwhelmed by spikes.                                         | Use **dynamic scaling** (K8s HPA) or quotas.  |
| **Ignored ACKs**                 | Orphaned messages consume broker resources.                              | Implement `auto_ack: false` + manual acks.     |
| **No Circuit Breaker**           | Cascading failures from one consumer.                                     | Use **Hystrix/Resilience4j** in consumers.     |

---

## **Related Patterns**
| Pattern                     | Description                                                                 | When to Use                                  |
|-----------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **[Circuit Breaker]**       | Prevents cascading failures by stopping requests to a failing service.       | High-latency dependencies.                   |
| **[Bulkheading]**           | Isolates queue consumers to avoid resource contention.                      | Multi-tenant queues.                         |
| **[Retry with Backoff]**    | Handles transient errors with exponential delays.                          | Unreliable networks/APIs.                    |
| **[Saga Pattern]**          | Manages distributed transactions via compensating actions.                 | Microservices with complex workflows.        |
| **[Rate Limiting]**         | Controls producer/consumer throughput.                                      | Preventing broker overload.                  |

---

## **Next Steps**
1. **Instrumentation**: Add OpenTelemetry traces to messages for end-to-end analysis.
2. **Automated Remediation**: Use **Chaos Engineering** (Gremlin) to test failure scenarios.
3. **Document SLAs**: Define queue retention policies and failure recovery times.