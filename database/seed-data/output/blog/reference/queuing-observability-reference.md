# **[Pattern] Queuing Observability Reference Guide**

---

## **Overview**
The **Queuing Observability** pattern provides end-to-end visibility into message queues and streaming systems by collecting, processing, and analyzing telemetry data from producers, consumers, brokers, and infrastructure. This pattern ensures you can **monitor queue throughput, latency, error rates, backpressure, and system health**—critical for optimizing performance, debugging bottlenecks, and ensuring reliability in event-driven architectures.

Key use cases include:
- Detecting message loss, duplication, or delays.
- Tracking consumer lag and broker bottlenecks.
- Proactively identifying scaling needs (e.g., dynamic partition adjustment).
- Auditing compliance with SLA guarantees (e.g., maximum message latency).

Observability tools (e.g., Prometheus, OpenTelemetry, Grafana) integrate with queue metrics to create dashboards, alerts, and root-cause analysis. This guide covers implementation details, schema requirements, and query examples for common queue systems (Kafka, RabbitMQ, AWS SQS/SNS, Apache Pulsar).

---

## **Implementation Details**

### **1. Key Concepts**
| **Concept**               | **Definition**                                                                                     | **Example Metrics**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Producer Telemetry**    | Tracks outbound messages (e.g., publish rate, failures, serialization errors).                     | `producer_messages_total`, `producer_failed_publishes`, `publish_latency`.                           |
| **Broker Telemetry**      | Monitors queue infrastructure (e.g., partition counts, disk/CPU usage, network throughput).           | `broker_partitions`, `broker_disk_utilization`, `network_bandwidth`.                                  |
| **Consumer Telemetry**    | Measures inbound consumption (e.g., lag, processing time, failures, checkpoint offsets).           | `consumer_lag`, `processing_time`, `consumer_errors`, `checkpoint_offset`.                           |
| **Schema Validation**    | Verifies message schemas (e.g., Avro, Protobuf) against expected formats in transit.               | `schema_validation_errors`, `schema_version_mismatches`.                                              |
| **Dead-Letter Queues (DLQ)** | Tracks messages routed to error handling queues for retry/analysis.                               | `dlq_messages_total`, `dlq_processing_time`.                                                          |
| **Backpressure**          | Indicates when consumers cannot keep up with producers (e.g., queue depth spikes).                   | `queue_depth`, `backpressure_duration`, `consumer_pacing`.                                              |

---

### **2. Schema Reference**
Define a structured schema (e.g., OpenTelemetry Protocol, Prometheus) to standardize telemetry collection. Below is a schema table for **Kafka**-specific observability (adapt for other systems):

| **Category**              | **Metric Name**               | **Type**   | **Description**                                                                                     | **Labels**                                  | **Units**   | **Example Value**       |
|---------------------------|-------------------------------|------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|-------------|--------------------------|
| **Producer**              | `kafka_producer_messages`     | Counter    | Total messages published.                                                                           | `topic`, `partition`, `broker_id`           | `{count}`   | `1000`                   |
|                           | `kafka_producer_failures`     | Counter    | Total publish failures (e.g., serialization errors).                                                | `topic`, `error_type`                      | `{count}`   | `5`                      |
|                           | `kafka_producer_latency`      | Histogram  | Time taken for publish (P50/P99).                                                                       | `topic`, `partition`                       | `ms`        | `{0.1, 0.5, 1.2, ...}`   |
| **Broker**                | `kafka_broker_partitions`     | Gauge      | Active partitions per broker.                                                                         | `broker_id`, `topic`                        | `{count}`   | `10`                     |
|                           | `kafka_broker_disk_util`      | Gauge      | Disk usage percentage.                                                                               | `broker_id`, `storage_type`                 | `%`         | `85`                     |
|                           | `kafka_network_throughput`    | Counter    | Bytes sent/received per second.                                                                       | `broker_id`, `direction` (ingest/outgoing)  | `bytes/s`   | `1024`                   |
| **Consumer**              | `kafka_consumer_lag`          | Gauge      | Time lag (seconds) between latest offset and broker’s log end.                                       | `consumer_group`, `topic`, `partition`      | `s`         | `120`                    |
|                           | `kafka_consumer_processing`   | Histogram  | Time to process a single message (P50/P99).                                                          | `consumer_group`, `topic`                  | `ms`        | `{50, 75, 100}`          |
|                           | `kafka_checkpoint_offset`     | Gauge      | Latest committed offset for a consumer group.                                                        | `consumer_group`, `topic`, `partition`      | `{count}`   | `42`                     |
| **DLQ**                   | `kafka_dlq_messages`          | Counter    | Total messages in the dead-letter queue.                                                             | `topic`, `dlq_reason`                      | `{count}`   | `20`                     |
| **Backpressure**          | `kafka_queue_depth`           | Gauge      | Current unprocessed messages in the queue.                                                          | `topic`, `partition`                       | `{count}`   | `1500`                   |
| **Schema Validation**     | `kafka_schema_errors`         | Counter    | Failures due to schema mismatches.                                                                    | `topic`, `version`                         | `{count}`   | `3`                      |

---

### **3. Query Examples**
Use the following queries (in **PromQL**, **Kafka Metrics API**, or **OpenTelemetry**) to analyze observability data.

#### **A. Kafka Consumer Lag Alert**
```promql
# Alert if lag exceeds threshold (e.g., 10 seconds)
rate(kafka_consumer_lag[1m]) > 10
```
**Visualization**:
```promql
# Dashboard: Consumer Lag by Topic
sum by(topic) (kafka_consumer_lag) > 0
```

#### **B. Producer Failure Rate**
```promql
# % of failed publishes (alert if > 1%)
(kafka_producer_failures_total / kafka_producer_messages_total) * 100 > 1
```

#### **C. Broker Disk Utilization Alert**
```promql
# Alert if disk usage > 90%
kafka_broker_disk_util > 90
```

#### **D. Backpressure Detection**
```promql
# Increasing queue depth (suggests backpressure)
increase(kafka_queue_depth[5m]) > 1000
```

#### **E. Schema Validation Errors**
```promql
# Failures per hour
rate(kafka_schema_errors_total[1h]) > 0
```

#### **F. Consumer Processing Time (P99)**
```promql
# Slow consumers (P99 latency > 500ms)
histogram_quantile(0.99, rate(kafka_consumer_processing[5m])) > 0.5
```

---
### **4. Handling Edge Cases**
| **Scenario**               | **Solution**                                                                                     | **Metrics to Monitor**                          |
|----------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Consumer Dropped**       | Use `consumer_dropped_messages_total` (if supported) or track DLQ entries.                      | `dlq_messages_total`                             |
| **Broker Restart**         | Check `broker_restart_total` (custom metric) and reprocessing latency.                          | `broker_restart_total`, `processing_time`         |
| **Schema Drift**           | Enforce schema versioning (e.g., Avro IDs) and monitor `schema_version_mismatches`.             | `schema_validation_errors`                      |
| **Network Partitions**     | Monitor `broker_network_errors` (custom) and `kafka_cluster_partition_count`.                   | `broker_network_errors`                          |
| **Slow Producers**         | Optimize `producer_batch_size` and track `publish_latency`.                                     | `producer_latency`, `producer_batch_size`        |

---

### **5. Related Patterns**
| **Pattern**                | **Description**                                                                                     | **Integration**                                  |
|----------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **Circuit Breaker**        | Temporarily halt producers/consumers during broker failures.                                        | Use `kafka_consumer_lag` to trigger circuit breaks. |
| **Rate Limiting**          | Control producer/consumer throughput to avoid overload.                                              | Monitor `kafka_queue_depth` + `producer_throughput`. |
| **Distributed Tracing**    | Trace message flows end-to-end (e.g., producer → broker → consumer).                                  | Use OpenTelemetry spans with `message_id`.         |
| **Canary Releases**        | Gradually roll out changes to consumers/producers and observe metrics.                             | Compare old/new `consumer_processing_time`.       |
| **Chaos Engineering**      | Inject failures (e.g., broker restarts) to test recovery.                                           | Monitor `broker_restart_total` + `recovery_time`. |

---

## **Tools & Libraries**
| **Tool/Library**           | **Purpose**                                                                                       | **Example**                                  |
|----------------------------|---------------------------------------------------------------------------------------------------|----------------------------------------------|
| **Prometheus + Grafana**   | Scrape metrics and visualize trends.                                                               | [Kafka Exporter](https://github.com/dkiinker/kafka_exporter) |
| **OpenTelemetry**          | Standardize traces, metrics, and logs across systems.                                              | [OTel Kafka Collector](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/kafkaconsumer) |
| **Confluent Control Center** | GUI for Kafka observability (metrics, schema registry).                                          | Built-in dashboards for broker health.     |
| **Datadog/New Relic**      | Hosted observability with prebuilt Kafka dashboards.                                               | APM for consumer/producer traces.             |
| **Burrow**                 | Track Kafka consumer lag and visualize offsets.                                                   | [Burrow GitHub](https://github.com/datawire/burrow) |

---
## **Best Practices**
1. **Instrument Early**: Add metrics during development (e.g., mock brokers for testing).
2. **Sample High-Volume Topics**: Use histogram percentiles (e.g., P99) to avoid cardinality explosion.
3. **Align SLAs with Metrics**:
   - `max_message_latency` (producer → consumer) ≤ 1s.
   - `consumer_lag` ≤ 10s for critical topics.
4. **Retain Historical Data**: Use Prometheus retention policies or time-series databases (e.g., TimescaleDB).
5. **Correlate Traces**: Add `message_id` to OpenTelemetry spans for end-to-end tracing.
6. **Automate Alerts**: Set up alerts for:
   - `kafka_consumer_lag` > threshold.
   - `producer_failures` rising.
   - `broker_disk_util` nearing 90%.

---
## **Example Implementation (Python + OpenTelemetry)**
```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider, Counter, Histogram
from opentelemetry.sdk.resources import Resource

# Configure OpenTelemetry
resource = Resource(attributes={
    "service.name": "kafka-producer",
    "service.version": "1.0"
})
provider = MeterProvider(resource=resource)
metrics.set_meter_provider(provider)

meter = metrics.get_meter("kafka_producer_meter")

# Metrics
producer_messages = Counter(
    "kafka_producer_messages",
    description="Total messages published",
    unit="1"
)
producer_latency = Histogram(
    "kafka_producer_latency",
    description="Publish latency",
    unit="ms"
)

# Instrument producer
def publish_message(topic: str, message: str):
    start_time = time.time()
    try:
        # Simulate publishing
        producer_messages.add(1, {"topic": topic})
        producer_latency.record(time.time() - start_time * 1000)  # Convert to ms
    except Exception as e:
        print(f"Publish failed: {e}")
```

---
## **Troubleshooting**
| **Issue**                  | **Diagnostic Query**                                                                             | **Root Cause**                                  |
|----------------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------|
| **High Consumer Lag**      | `kafka_consumer_lag > 30`                                                                         | Slow processing (bottleneck) or low partitions. |
| **Producer Backlog**       | `kafka_queue_depth` increasing while `producer_throughput` flat.                               | Producer too slow or broker throttling.        |
| **Schema Errors**          | `kafka_schema_errors_total` rising                                                          | Schema drift (e.g., Avro version mismatch).    |
| **Broker Overloaded**      | `kafka_broker_cpu > 90` or `kafka_broker_disk_util > 80`                                   | Insufficient resources or misconfigured partitions. |

---
**See Also**:
- [Kafka Monitoring Guide](https://kafka.apache.org/documentation/#monitoring)
- [OpenTelemetry Kafka Collector](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/kafkaconsumer)
- [Grafana Kafka Dashboard](https://grafana.com/grafana/dashboards/?search=kafka)