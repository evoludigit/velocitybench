# **[Pattern] Streaming Gotchas Reference Guide**

---

## **Overview**
Streaming data in real-time systems introduces unique challenges that can lead to subtle bugs, performance issues, or logical errors if not handled properly. This guide documents common "streaming gotchas"—unexpected pitfalls in data processing pipelines, event-driven architectures, and streaming frameworks (e.g., Kafka, Flink, Spark Streaming). Understanding these gotchas helps developers design resilient systems and troubleshoot anomalies.

Gotchas covered include:
- **Ordering and consistency issues** (e.g., late data, exactly-once semantics).
- **Resource exhaustion** (backpressure, unbounded queues).
- **Fault tolerance failures** (checkpointing, recovery).
- **Data corruption** (schema evolution, serialization issues).
- **Monitoring and observability gaps**.

---

## **Key Concepts & Implementation Details**

### **1. Ordering & Event Time Semantics**
- **Problem**: Stream processing assumes *event time* (when data was produced) rather than *ingestion time* (when it arrives). Late-arriving or out-of-order events can break logic.
- **Schema Reference**:
  | Concept               | Description                                                                 | Example Use Case                     |
  |-----------------------|-----------------------------------------------------------------------------|---------------------------------------|
  | **Event Time**        | Timestamp embedded in the event (e.g., Kafka `timestamp`).                   | Detecting windowing anomalies.        |
  | **Watermark**         | Bound for determining "late" data (e.g., `current timestamp + 5s`).    | Handling late-arriving records.      |
  | **Watermark Propagation** | Watermarks must advance monotonically.                                   | Avoiding stuck watermarks in joins.   |
  | **Allowed Lateness**  | Configurable delay for late data (trade-off: accuracy vs. speed).          | Cleaning up micro-batches.            |

- **Anti-Pattern**: Processing data in *processing time* without event-time watermarks.
- **Fix**: Use **exactly-once processing** and watermarks to tolerate late data.

---

### **2. Backpressure & Resource Exhaustion**
- **Problem**: Consumers can’t keep up with producers, causing:
  - Queue buildup (e.g., Kafka partitions overflow).
  - JVM heap exhaustion (e.g., Spark accumulators).
  - Deadlocks (e.g., unbounded `flatMap` in Flink).
- **Schema Reference**:
  | Gotcha               | Impact                          | Mitigation                          |
  |----------------------|---------------------------------|-------------------------------------|
  | **Unbounded Queues** | Consumer lag spikes.             | Dynamic scaling (e.g., Kafka consumer groups). |
  | **Parallelism Mismatch** | Skewed workloads.          | Auto-scaling workers (e.g., Flink dynamic scaling). |
  | **Memory Leaks**     | OOM crashes.                     | Monitor `GC logs` and bound buffers. |

- **Anti-Pattern**: Disabling backpressure in Flink/Kafka.
- **Fix**:
  - Set **max partitions per consumer** (Kafka) or **parallelism** (Flink).
  - Use **buffer timeouts** (e.g., Spark `recevier.maxRate`).

---

### **3. Fault Tolerance & Checkpointing**
- **Problem**: Failures during stateful processing (e.g., UDFs) cause data loss or reprocessing.
- **Schema Reference**:
  | Concept               | Responsibility               | Failure Mode                     |
  |-----------------------|-----------------------------|----------------------------------|
  | **Checkpointing**     | Framework (Flink/Spark).     | Incremental state recovery.       |
  | **Savepoints**        | Manual triggers (e.g., `savepoint()` in Flink). | Persistent state rollback. |
  | **State Backend**     | Memory vs. disk (trade-off: speed vs. durability). | State corruption if backend fails. |

- **Anti-Pattern**: Disabling checkpoints or using short intervals (increases overhead).
- **Fix**:
  - Enable **exactly-once checkpointing** (e.g., Flink’s RocksDB state backend).
  - Test recovery with `kill -9` on workers.

---
### **4. Schema Evolution & Serialization**
- **Problem**: Schema changes (e.g., adding/removing fields) break deserialization.
- **Schema Reference**:
  | Gotcha               | Impact                          | Solution                            |
  |----------------------|---------------------------------|-------------------------------------|
  | **Forward/Backward Incompatibility** | Dropped fields cause errors. | Use Avro/Protobuf with backward-compatible updates. |
  | **Dynamic Typing**   | Runtime type mismatches.        | Explicit schema enforcement (e.g., Kafka Avro). |

- **Anti-Pattern**: Hardcoding schema assumptions in code.
- **Fix**:
  - Use **schema registry** (e.g., Confluent Schema Registry).
  - Validate schemas at runtime (e.g., Flink’s `Schema` API).

---

### **5. Monitoring & Observability**
- **Problem**: Streaming bugs often manifest as silent failures (e.g., dropped records).
- **Schema Reference**:
  | Metric               | Tool/Framework               | Threshold Example          |
  |----------------------|-----------------------------|----------------------------|
  | **End-to-End Latency** | Prometheus + Grafana.       | >100ms = investigate.      |
  | **Record Lag**       | Kafka Consumer Lag.          | >10k records = scale.       |
  | **Watermark Stalls** | Flink metrics.               | Watermark <5s = adjust lateness. |

- **Anti-Pattern**: Relying on logs only.
- **Fix**:
  - Instrument **watermark lag**, **throughput**, and **error rates**.
  - Use **structured logging** (e.g., OpenTelemetry).

---

## **Query Examples**
### **1. Detecting Late Data in Flink**
```java
// Configure watermark strategy (with allowed lateness)
env.setStreamTimeCharacteristic(TimeCharacteristic.EventTime);
DataStream<Event> stream = env.addSource(source)
    .assignTimestampsAndWatermarks(
        WatermarkStrategy
            .<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
            .withTimestampAssigner((event, timestamp) -> event.timestamp));
```

### **2. Handling Kafka Consumer Lag**
```bash
# Check lag (topic-partition-wise)
kafka-consumer-groups --bootstrap-server <broker> --group <group> --describe
# Output:
  TOPIC:       PARTITION:  LOG_END_OFFSET  LAG
  events:      0          1000            5000
```

### **3. Schema Validation in Spark Structured Streaming**
```python
from pyspark.sql.functions import col

# Ensure schema compatibility
df = spark.readStream.format("kafka") \
    .load() \
    .select(from_json(col("value").cast("string"), schema).alias("data")) \
    .where(col("data.field1").isNotNull())
```

---

## **Related Patterns**
1. **[Idempotent Sinks](https://example.com/idempotent-sinks)**
   - Ensures duplicate writes don’t corrupt state (e.g., Kafka transactions).
2. **[Exactly-Once Processing](https://example.com/exactly-once)**
   - Combines checkpointing + transactional sinks for atomicity.
3. **[Dynamic Scaling](https://example.com/dynamic-scaling)**
   - Adjusts consumers/workers based on load (e.g., Flink’s `scale-out`).
4. **[Side Outputs](https://example.com/side-outputs)**
   - Routes errors/specials to dead-letter queues (e.g., Flink `OutputTag`).
5. **[Event Sourcing](https://example.com/event-sourcing)**
   - Replays events for debugging (complements streaming).

---
**Note**: Links above are placeholder URLs; replace with actual references. For deeper dives, consult:
- [Apache Flink Documentation](https://flink.apache.org)
- [Kafka Consumer Lag Guide](https://kafka.apache.org/documentation/#consumerlag)
- [Schema Registry Best Practices](https://docs.confluent.io)