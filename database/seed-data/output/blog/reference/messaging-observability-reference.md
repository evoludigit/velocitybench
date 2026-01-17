**[Pattern] Messaging Observability Reference Guide**

---

### **Overview**
Messaging Observability ensures real-time visibility into message queues, exchanges, and broker infrastructure to detect latency, failures, or bottlenecks in distributed systems. This pattern helps diagnose issues like dropped messages, slow consumers, or routing errors by correlating metadata, performance metrics, and event traces across messaging components.

**Core goals:**
- Monitor message flow, latency, and volume.
- Detect anomalies (e.g., backpressure, throttle events).
- Trace messages across services via unique IDs (e.g., correlation IDs).
- Validate routing rules and message integrity.

---

### **Schema Reference**
Store observability data in structured formats for queryability. Below are common schemas—optimize based on your stack (e.g., Kafka, RabbitMQ, AWS SQS).

#### **1. Core Message Metrics**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `message_id`        | String     | Unique identifier for tracing (e.g., Kafka’s `message_id`).                |
| `topic/queue`       | String     | Destination name (e.g., `orders.created`).                                 |
| `broker_host`       | String     | Broker instance (e.g., `kafka-prod-1`).                                   |
| `timestamp`         | Timestamp  | Event time (e.g., message ingestion/release).                              |
| `publish_time`      | Timestamp  | When the message was sent.                                                 |
| `processing_time`   | Duration   | End-to-end latency (publish → consume).                                    |
| `status`            | Enum       | `SUCCESS`, `FAILURE`, `TIMEOUT`, `DROPPED`, `RETRYING`.                   |
| `error_code`        | String     | (Optional) Vendor-specific error (e.g., `AMQP_406` for RabbitMQ).          |
| `consumer_host`     | String     | Consumer instance (e.g., `microservice-payment-01`).                      |

---

#### **2. Enrichment Fields (for Context)**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `correlation_id`    | String     | Links related messages (e.g., `order-service:1234`).                        |
| `source_service`    | String     | Originating service (e.g., `auth-service`).                                |
| `destination`       | String     | Target service/endpoint.                                                   |
| `payload_size`      | Integer    | Bytes (helps detect malformed messages).                                   |
| `routing_key`       | String     | (Kafka/RabbitMQ) Binding rule identifier.                                  |
| `partition`         | Integer    | (Kafka) Partition number for parallelism tracking.                        |

---
#### **3. Broker-Level Metrics**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `broker_metrics`    | Object     | Subfields: `messages_in_queue`, `bytes_in`, `consume_latency_p99`.        |
| `backpressure`      | Boolean    | True if consumers are lagging behind producers.                            |
| `consumer_lag`      | Integer    | (Kafka) Queue depth vs. processed messages.                                 |

---
#### **4. Trace Context (Distributed Tracing)**
| Field               | Type       | Description                                                                 |
|---------------------|------------|-----------------------------------------------------------------------------|
| `trace_id`          | String     | Unique ID for cross-service tracing (e.g., Jaeger/Otel).                  |
| `span_id`           | String     | Isolates individual message-processing steps.                              |
| `tags`              | JSON       | Key-value pairs (e.g., `{ "user_id": "abc123" }`).                          |

---

### **Implementation Details**
#### **Key Concepts**
1. **End-to-End Latency Monitoring**
   - Track `publish_time` (broker inbound) and `processing_time` (consumer outbound).
   - Use percentiles (P99) to flag slow consumers.

2. **Message Retry Tracking**
   - Log retry counts and timestamps to detect stuck messages (e.g., `retry_count: 5, last_retry: "2023-01-01T12:00:00"`).

3. **Anomaly Detection**
   - Flags: Sudden `message_drops` or `backpressure` spikes.
   - Example rule: `IF (consumer_lag > 1000) THEN alert`.

4. **Correlation ID Propagation**
   - Append correlation IDs to headers/attributes for tracing (e.g., Kafka’s `headers` field).

5. **Schema Evolution**
   - Use backward-compatible schemas (e.g., Avro) or version tags (e.g., `schema_version: 2`).

---

#### **Tech Stack Options**
| Component          | Tools/Technologies                                                                 |
|--------------------|------------------------------------------------------------------------------------|
| **Broker**         | Apache Kafka, RabbitMQ, AWS SQS/SNS, Azure Service Bus                              |
| **Observability**  | Prometheus (metrics), OpenTelemetry (traces), ELK Stack (logs)                     |
| **Storage**        | TimescaleDB (time-series), Cassandra (scalable), or clickhouse                      |
| **Alerts**         | Grafana Alerts, Datadog, or custom Lambda/Python scripts                            |

---

### **Query Examples**
#### **1. Find Slow Message Processing (Kafka)**
```sql
-- Query: Messages with P99 latency > 1s in the last hour
SELECT
  topic,
  AVG(processing_time) AS avg_latency,
  PERCENTILE_CONT(processing_time, 0.99) AS p99_latency
FROM message_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY topic
HAVING p99_latency > INTERVAL '1 second';
```

#### **2. Detect Dropped Messages (RabbitMQ)**
```sql
-- Query: Queues with failed message rates > 1%
SELECT
  queue_name,
  SUM(CASE WHEN status = 'FAILURE' THEN 1 ELSE 0 END) AS failed_messages,
  COUNT(*) AS total_messages,
  ROUND(SUM(CASE WHEN status = 'FAILURE' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)::float, 2) AS failure_rate
FROM message_metrics
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY queue_name
HAVING failure_rate > 1.0;
```

#### **3. Trace Correlated Events (Distributed)**
```sql
-- Query: Order processing steps for `correlation_id = "order:123"`
SELECT
  timestamp,
  service_name,
  event_type,
  payload
FROM distributed_traces
WHERE trace_id = 'order-processor-20230101'
  AND correlation_id = 'order:123'
ORDER BY timestamp;
```

#### **4. Broker Backpressure Alert**
```sql
-- Query: Brokers with consumer lag > 5000 messages
SELECT
  broker_host,
  AVG(consumer_lag) AS avg_lag
FROM broker_metrics
WHERE timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY broker_host
HAVING AVG(consumer_lag) > 5000;
```

---

### **Related Patterns**
1. **[Distributed Tracing](https://patterns.dev/observability/distributed-tracing)**
   - Extend messaging observability with full request flows (e.g., OpenTelemetry).

2. **[Circuit Breaker](https://patterns.dev/resilience/circuit-breaker)**
   - Complement observability by failing fast on high error rates.

3. **[Rate Limiting](https://patterns.dev/resilience/rate-limiting)**
   - Use metrics to enforce quotas (e.g., `messages_per_second`).

4. **[Idempotent Producer](https://patterns.dev/messaging/idempotent-producer)**
   - Avoid duplicates via deduplication keys (e.g., `correlation_id`).

5. **[Dead Letter Queue (DLQ) Pattern](https://patterns.dev/messaging/dlq)**
   - Route failed messages to a queue for analysis (link to observability dashboards).

---

### **Best Practices**
- **Sampling**: For high-volume topics, sample messages (e.g., 1% of traffic) to reduce costs.
- **Retention**: Archive raw logs for 7–30 days; aggregate metrics long-term (e.g., 1 year).
- **Integration**: Sync with APM tools (e.g., New Relic) to correlate API calls with message events.
- **Security**: Mask PII in logs (e.g., `user_id: "[REDACTED]"`).

---
**Example Workflow**:
1. Producer sends message to Kafka with `correlation_id` and OpenTelemetry trace context.
2. Broker logs `publish_time` and `topic`.
3. Consumer processes message, records `processing_time` and tags (e.g., `user_id`).
4. Alerts trigger if `processing_time` > threshold or `retry_count > 3`.
5. Distributed traces link to upstream API calls in APM.