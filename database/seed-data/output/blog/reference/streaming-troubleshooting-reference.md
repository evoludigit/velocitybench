# **[Pattern] Streaming Troubleshooting Reference Guide**

## **Overview**
Streaming Troubleshooting is a structured approach to diagnosing and resolving issues in real-time data pipelines (e.g., Kafka, Kinesis, Pulsar). This pattern helps identify bottlenecks, connectivity problems, data skew, or system failures by leveraging metrics, logs, and instrumentation. It ensures low-latency processing, high availability, and data consistency in streaming architectures.

---

## **Key Concepts & Implementation Details**

### **1. Common Streaming Issues**
| Issue Type          | Description                                                                 | Typical Causes                                                                 |
|---------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Connectivity**    | Broken links between producers/consumers and brokers.                      | Network failures, misconfigured endpoints, authentication issues.               |
| **Latency**         | Delayed data processing or high end-to-end latency.                         | Resource constraints, inefficient serializers, backpressure in consumers.       |
| **Data Loss**       | Missing records in consumer output.                                          | Checkpoint timeouts, log retention policies, or producer retries exceeding limits. |
| **Ordering Issues** | Out-of-order events in consumer processing.                                 | Partitioning skew, network delays, or consumer lag.                             |
| **Resource Exhaustion** | OOM errors or high CPU/memory usage.                                       | Unbounded consumer processing, inefficient serializers, or unscaled brokers.    |
| **Schema Mismatch** | Incompatible producer/consumer schemas.                                     | Schema evolution without backward compatibility (e.g., Avro/Protobuf changes). |
| **Monitoring Gaps** | Lack of observability into pipeline health.                                | Missing metrics (e.g., `record-lag`, `commit-rate`), or log volume overload.  |

---

### **2. Troubleshooting Workflow**
Follow a **structured, diagnostic approach** to isolate and resolve issues efficiently.

#### **Step 1: Verify Basic Connectivity**
- **Check producer/consumer connectivity**:
  ```bash
  telnet <broker_host> <broker_port>  # Verify TCP connectivity
  ```
- **Test API/SDK connections**:
  - Use `kafka-console-producer`/`consumer` for manual data validation.
  - Example:
    ```bash
    kafka-console-producer --topic test-topic --bootstrap-server localhost:9092
    ```
    (Send a test message and validate it appears in a consumer.)

#### **Step 2: Inspect Broker Health**
- **Backend metrics** (e.g., Kafka):
  ```bash
  kafka-broker-api-versions --bootstrap-server localhost:9092
  ```
- **Monitor broker metrics** (e.g., `kafka-server-start` logs or tools like **Prometheus/Grafana**):
  - High `UnderReplicatedPartitions` → Replication issues.
  - High `RequestedRate` → Consumer/producer load imbalance.

#### **Step 3: Diagnose Consumer Lag**
- **Query consumer lag** (Kafka example via CLI):
  ```bash
  kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-consumer-group
  ```
  - Lag > 100K records → **Scale consumers or optimize processing**.
  - Lag spikes → **Check for backpressure or slow sinks**.

#### **Step 4: Validate Data Integrity**
- **Compare producer/consumer counts**:
  ```bash
  kafka-consumer-perf-test --topic test-topic --bootstrap-server localhost:9092 --messages 1000 --throughput -1 | grep "records/sec"
  ```
- **Check for duplicates**:
  - Use a `Deduplicator` pattern or unique keys (e.g., `message_id`).
  - Validate with:
    ```sql
    SELECT COUNT(DISTINCT message_id), COUNT(*) FROM events_table GROUP BY message_id HAVING COUNT(*) > 1;
    ```

#### **Step 5: Debug Serialization Issues**
- **Inspect schema compatibility** (Avro example):
  ```bash
  avro-tools validate-schema --schema-file schema.avsc --validate-only
  ```
- **Test deserialization**:
  - Write a script to deserialize raw bytes → Expect no `SerializationException`.

#### **Step 6: Review Logs & Traces**
- **Producer logs**:
  - Look for `send() errors` or `partition not available`.
- **Consumer logs**:
  - Check for `CommitterException` (checkpointing failures) or `DeserializationException`.
- **Distributed tracing**:
  - Use **OpenTelemetry** or **Zipkin** to trace end-to-end latency.

#### **Step 7: Optimize Performance**
| Bottleneck               | Solution                                                                 |
|--------------------------|--------------------------------------------------------------------------|
| High consumer lag        | Scale consumers, increase partitions, or optimize `poll()` logic.        |
| Slow serializers         | Use faster formats (e.g., Protobuf over Avro).                           |
| Network saturation       | Enable compression (`gzip`, `snappy`) or reduce batch size.               |
| Broker overload          | Add brokers, increase `num.partitions`.                                  |

---

## **Schema Reference**

| Field               | Type     | Description                                                                 | Example Value                     |
|---------------------|----------|-----------------------------------------------------------------------------|-----------------------------------|
| **`event_time`**    | Timestamp| Timestamp of the event (for windowed processing).                          | `2024-01-01T12:00:00Z`            |
| **`message_id`**    | String   | Unique identifier for deduplication.                                        | `uuid-123456789`                  |
| **`partition_key`** | String   | Key for partition assignment (e.g., `user_id`).                             | `user_42`                         |
| **`payload`**       | Binary   | Serialized event data (Avro/Protobuf/JSON).                               | `[...bytes...]`                   |
| **`metadata`**      | Object   | Additional context (e.g., `source_system`, `timestamp`).                    | `{"source": "api_v1", "version": 1}` |

---
## **Query Examples**

### **1. Kafka Consumer Lag (CLI)**
```bash
# List all consumer groups and their lag
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --all-groups

# Get lag for a specific group
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-consumer
```

### **2. SQL-like Query for Event Analysis (Spark SQL)**
```sql
-- Find late-arriving events (assuming `event_time` is in UTC)
SELECT
  topic,
  COUNT(*) as delayed_records,
  AVG(DATEDIFF('second', event_time, processed_time)) as avg_delay_seconds
FROM events_table
WHERE processed_time - event_time > INTERVAL '10 minutes'
GROUP BY topic
HAVING COUNT(*) > 0;
```

### **3. Python: Check for Duplicate Messages (Pandas)**
```python
import pandas as pd

# Load event data
df = pd.read_json("events.json")

# Find duplicates
duplicates = df[df.duplicated(subset=['message_id'], keep=False)]
print(f"Duplicate records: {len(duplicates)}")
```

### **4. Kafka Topic Inspection**
```bash
# List topics
kafka-topics --list --bootstrap-server localhost:9092

# Describe a topic (partitions, replication factor)
kafka-topics --describe --topic my-topic --bootstrap-server localhost:9092
```

---

## **Related Patterns**
| Pattern                  | Purpose                                                                 | When to Use                                                                 |
|--------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Idempotent Producer**  | Ensure no duplicate messages are sent (even on retries).                | Critical pipelines where duplicates cause data corruption.                 |
| **Exactly-Once Processing** | Guarantee each event is processed exactly once.                       | Financial transactions or audit logs.                                       |
| **Rate Limiting**        | Control producer/consumer throughput to avoid overload.                 | High-volume systems prone to backpressure.                                  |
| **Schema Evolution**     | Manage backward/forward compatibility in schema changes.                | Microservices with evolving APIs.                                           |
| **Dead Letter Queues (DLQ)** | Route failed records for manual inspection/reprocessing.               | Pipelines where errors cannot be auto-recovered.                            |
| **Dynamic Scaling**      | Auto-scale consumers based on lag or load.                             | Cloud-native streaming apps with variable traffic.                          |

---

## **Best Practices**
1. **Instrument Early**: Add metrics for `in-flight records`, `processing time`, and `error rates` during development.
2. **Test Failure Scenarios**: Simulate network partitions or broker failures in staging.
3. **Monitor End-to-End**: Track latency from producer to consumer (e.g., using Prometheus).
4. **Document Schema Changes**: Use tools like **Confluent Schema Registry** to track Avro/Protobuf versions.
5. **Automate Alerts**: Set up alerts for:
   - Consumer lag > threshold (e.g., 10K records).
   - Broker CPU > 90%.
   - Schema incompatibility errors.