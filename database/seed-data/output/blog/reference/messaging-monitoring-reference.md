# **[Pattern] Messaging Monitoring – Reference Guide**

## **Overview**
The **Messaging Monitoring** pattern tracks the flow, status, and performance of messages exchanged between systems or services via messaging brokers (e.g., RabbitMQ, Apache Kafka, AWS SQS). It ensures reliability, detects anomalies, and provides observability into latency, throughput, errors, and system health.

Monitoring covers:
- **Message quality** (validity, completeness, correctness)
- **System health** (broker performance, resource utilization)
- **Operational metrics** (delivery success/failure rates, retry counts)

This pattern is critical for **event-driven architectures**, **microservices**, and **real-time data processing** where unmonitored failures can cascade.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                                     | **Example**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Message Broker**     | Middleware that routes, stores, and manages messages (e.g., RabbitMQ, Kafka, ActiveMQ).            | Kafka topics, SQS queues.            |
| **Producers**          | Systems/sources that publish messages to a broker.                                                 | Microservice APIs, IoT devices.      |
| **Consumers**          | Systems targeting messages (e.g., service handlers, data sinks).                                    | Database processing scripts.         |
| **Monitoring Agents**  | Tools agents (e.g., Prometheus, custom scripts) that collect metrics.                              | Kafka Lag Exporter, RabbitMQ Metrics Plugin. |
| **Alerting System**    | Triggers notifications for anomalies (e.g., Slack, PagerDuty, Grafana).                            | Alert on >95% message errors.        |
| **Data Store**         | Persists metrics/logs for analysis (e.g., Prometheus, ELK, AWS CloudWatch).                       | Time-series database for metrics.   |

---

### **2. Metrics to Monitor**
Monitor these KPIs to ensure health and performance:

| **Category**          | **Metric**                          | **Description**                                                                 | **Tooling Example**                |
|-----------------------|-------------------------------------|---------------------------------------------------------------------------------|-------------------------------------|
| **Message Volume**     | Messages/sent, received, processed   | Tracks throughput and potential bottlenecks.                                   | Kafka `messages.in`, `messages.out` |
| **Latency**           | End-to-end delay                    | Time from send to successful processing (e.g., P99 latency).                   | Prometheus `message_latency_seconds` |
| **Error Rates**       | Failed deliveries, throttling       | % of messages rejected or delayed (e.g., due to invalid payloads).              | RabbitMQ `unroutable_messages`      |
| **Resource Usage**    | Memory, CPU, queue depth            | Broker health; high queue depth may indicate consumer lag.                     | RabbitMQ management UI.            |
| **Retry Behavior**    | Retry counts, backoffs               | Detects deadlocks or poison pills in transactional workflows.                   | Custom monitoring script.           |

---

### **3. Implementation Approaches**

#### **A. Broker-Level Monitoring**
- **Purpose**: Track broker health and message flow.
- **Tools**:
  - **RabbitMQ**: Built-in plugin for metrics (e.g., `rabbitmq_management`).
  - **Kafka**: JMX metrics + tools like [Kafka Lag Exporter](https://github.com/dvcorg/kafka-lag-exporter).
- **Example Setup**:
  ```bash
  # Enable RabbitMQ metrics plugin
  rabbitmq-plugins enable rabbitmq_management
  ```

#### **B. Agent-Based Monitoring**
- **Purpose**: Instrument producers/consumers to log custom metrics.
- **Tools**:
  - **Prometheus Client Libraries**: Embed metrics in apps (e.g., `prometheus_client` for Python).
  - **OpenTelemetry**: Unified tracing/metrics (supports Kafka, RabbitMQ).
- **Example Metric Labeling**:
  ```
  message_processing_seconds{consumer="order_service", topic="orders"}
  ```

#### **C. Log-Based Monitoring**
- **Purpose**: Correlate logs with metrics (e.g., trace message IDs through systems).
- **Tools**:
  - **Fluentd/Fluent Bit**: Ship logs to ELK Stack or Loki.
  - **Structured Logging**: Include `message_id`, `timestamp`, and `status` in logs.
- **Log Pattern**:
  ```json
  {
    "event": "message_processed",
    "message_id": "abc123",
    "status": "success",
    "latency_ms": 420
  }
  ```

#### **D. Alerting Rules**
- **Common Thresholds**:
  - **Error Rate**: >1% failed messages (adjustable by SLA).
  - **Latency**: P99 >500ms (configurable per service).
  - **Queue Depth**: >10K messages (indicates consumer lag).
- **Alert Channels**: Slack, PagerDuty, or team email.
- **Example Grafana Alert**:
  ```yaml
  - alert: HighMessageLatency
    expr: message_latency_seconds > 1000
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High latency in {{ $labels.service }}"
  ```

---

## **Schema Reference**
Below are **standardized metrics schemas** for interoperability. Use these to structure your monitoring pipeline.

### **1. Producer Metrics**
| **Field**           | **Type**   | **Description**                          | **Example Value**       |
|---------------------|------------|------------------------------------------|-------------------------|
| `timestamp`         | ISO 8601   | When metrics were recorded.              | `2024-02-20T14:30:00Z`  |
| `producer_id`       | String     | Unique ID of the producer system.        | `order-service-001`     |
| `topic`             | String     | Message topic/queue.                     | `user_orders`           |
| `messages_sent`     | Integer    | Total messages published.                 | `4200`                  |
| `message_size`      | Float (MB) | Avg. message size.                       | `0.05`                  |
| `errors`            | Integer    | Failed sends (e.g., broker rejection).    | `4`                     |

### **2. Consumer Metrics**
| **Field**           | **Type**   | **Description**                          | **Example Value**       |
|---------------------|------------|------------------------------------------|-------------------------|
| `timestamp`         | ISO 8601   | When metrics were recorded.              | `2024-02-20T14:30:05Z`  |
| `consumer_id`       | String     | Unique ID of the consumer.               | `payment-processor`     |
| `topic`             | String     | Message topic/queue.                     | `user_orders`           |
| `messages_received` | Integer    | Total received messages.                  | `4195`                  |
| `messages_processed`| Integer    | Successfully processed.                   | `4190`                  |
| `processing_time`   | Float (ms) | Avg. time per message.                   | `120.5`                 |
| `retry_count`       | Integer    | Messages reprocessed.                    | `5`                     |

### **3. Broker Metrics**
| **Field**           | **Type**   | **Description**                          | **Example Value**       |
|---------------------|------------|------------------------------------------|-------------------------|
| `broker_name`       | String     | Broker identifier (e.g., cluster name).  | `kafka-cluster-1`       |
| `queue_name`        | String     | Topic/queue monitored.                   | `orders`                |
| `queue_depth`       | Integer    | Unacknowledged messages.                 | `120`                   |
| `consumer_lag`      | Integer    | Messages behind consumer (Kafka only).   | `500`                   |
| `disk_usage`        | Float (%)  | Broker disk usage.                       | `85`                    |

---

## **Query Examples**
### **1. Detecting High Error Rates (Grafana/PromQL)**
```promql
# % of messages with errors in the last 5 minutes
100 * sum(rate(message_errors_total[5m]))
  / sum(rate(message_sent_total[5m]))
```

### **2. Finding Slow Consumers (InfluxDB)**
```sql
SELECT
  mean("processing_time_ms") as avg_latency,
  count("message_id") as messages
FROM "consumer_metrics"
WHERE topic = 'orders'
  AND time > now() - 1h
GROUP BY "consumer_id"
ORDER BY avg_latency DESC
```

### **3. Kafka Consumer Lag Alert (Bash + jq)**
```bash
curl -s "http://kafka-cluster-1:9092/kafka-consumer-lag?topic=orders" | jq '
  .consumers[] |
  select (.lag > 1000) |
  .consumer + { lag: .lag }'
```
**Output**:
```json
{
  "consumer": "payment-processor",
  "lag": 1500
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **[Dead Letter Queue](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterQueue.html)** | Routes failed messages for debugging.                                    | When messages repeatedly fail processing. |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Manages distributed transactions via compensating actions.              | For long-running workflows.              |
| **[Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)** | Prevents cascading failures by throttling.                               | When downstream services are unreliable. |
| **[Idempotent Producer](https://www.cloudamqp.com/blog/2017-11-17-what-is-idempotency.html)** | Ensures duplicate messages don’t cause side effects.                      | For event sourcing or retries.           |
| **[Event Sourcing](https://martinfowler.com/eaaT/es.html)**           | Stores state changes as immutable logs.                                  | Audit trails or replayability needed.     |

---
## **Best Practices**
1. **Define SLAs**: Set acceptable thresholds for latency/errors (e.g., 99.9% success rate).
2. **Correlate Metrics**: Link message IDs across producers/consumers/brokers.
3. **Sample Heavy Traffic**: Monitor spikes (e.g., Black Friday) to avoid alert fatigue.
4. **Retain Logs**: Store raw logs for 30+ days to debug past issues.
5. **Automate Recovery**: Use DLQs + retry policies (e.g., exponential backoff).

---
## **Tools & Libraries**
| **Category**          | **Tools**                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| **Metrics Collection** | Prometheus, Datadog, New Relic, Telegraf                                   |
| **Log Management**    | ELK Stack, Loki, Splunk, Fluentd                                          |
| **Tracing**           | OpenTelemetry, Jaeger, Zipkin                                             |
| **Alerting**          | Grafana Alerting, PagerDuty, Opsgenie                                     |
| **Broker-Specific**   | RabbitMQ Management UI, Confluent Control Center (Kafka), SQS Metrics      |