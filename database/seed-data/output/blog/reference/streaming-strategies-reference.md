# **[Pattern] Reference Guide: Streaming Strategies**

---
## **Overview**
The **Streaming Strategies** pattern defines approaches to efficiently process, transform, and deliver data streams in real-time or near-real-time systems. Streaming architectures are critical for handling high-volume, low-latency workloads such as IoT sensors, financial transactions, log analytics, and live event processing.

This pattern balances trade-offs between **throughput**, **latency**, **resource utilization**, and **fault tolerance**, enabling scalable data pipelines. Implementations may involve streaming frameworks like **Apache Kafka**, **Apache Flink**, **Apache Spark Streaming**, or custom solutions (e.g., WebSockets, Server-Sent Events). Key considerations include **partitioning**, **checkpointing**, **backpressure handling**, and **state management**.

---
## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Term**               | **Definition**                                                                 | **Use Case**                                                                 |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Stream Source**      | Origin of data (e.g., Kafka topic, database CDC logs, HTTP streams).          | Ingesting raw events from IoT devices or user interactions.                  |
| **Stream Processor**   | Framework or engine (e.g., Flink, Spark) that processes data in micro-batches or events. | Applying transformations, filtering, or aggregations on-the-fly.          |
| **State Store**        | Persistent storage for maintaining state (e.g., RocksDB, Redis).             | Tracking session IDs, user preferences, or windowed aggregations.           |
| **Sink**               | Destination for processed data (e.g., database, file system, message queue). | Storing results in Parquet files, updating a real-time dashboard, or forwarding to another system. |
| **Backpressure**       | Mechanism to throttle producers when sinks are overwhelmed.                   | Preventing bottlenecks during peak loads (e.g., scaling consumers dynamically). |
| **Checkpointing**      | Saving processor state to restart from a fault.                              | Ensuring exactly-once processing after failures (e.g., Flink’s savepoints). |
| **Watermarking**       | Tracking event-time progress (vs. processing-time) for late data.              | Handling out-of-order events in event-time windows (e.g., 5-minute tumbling windows). |

---

### **2. Streaming Strategies**
Choose a strategy based on **latency**, **complexity**, and **resource constraints**:

| **Strategy**               | **Description**                                                                                                                                                                                                 | **Best For**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Event-Time Processing** | Processes data based on timestamps embedded in events (not system clock). Uses watermarks to handle late arrivals.                                                          | Financial transactions, clickstream analytics (where order matters).     |
| **Processing-Time**       | Processes events in the order they arrive in the system (no watermarks).                                                                                                                      | Debugging, low-latency dashboards (if order isn’t critical).              |
| **Micro-Batch Processing**| Groups events into small batches (e.g., 100ms–1s windows) for efficient processing.                                                                                                              | High-throughput analytics (e.g., log aggregation with Spark).             |
| **Continuous Processing** | Streams data in a stream-of-streams model (e.g., Flink’s stateful operations).                                                                                                                  | Real-time fraud detection, dynamic filtering.                              |
| **Windowed Aggregations** | Processes data in fixed/sliding/windows (e.g., tumbling: 1-hour windows; sliding: 10-min overlaps).                                                                                           | Time-series metrics (e.g., "average order value per 5-minute window").      |
| **Join Strategies**       | **Keyed Join**: Joins streams on a common key (e.g., user ID). <br>**Interval Join**: Matches events across non-overlapping time windows.                                          | Personalized recommendations, correlating sensor + user behavior data.     |
| **Stateful Processing**   | Maintains mutable state (e.g., session counters, ML model predictions) across events.                                                                                                            | Churn prediction, anomaly detection.                                         |
| **Side Outputs**         | Splits stream into primary output + secondary streams (e.g., alerts, debug logs).                                                                                                                      | Logging errors separately from main results.                               |
| **Dynamic Scaling**       | Adjusts resource allocation (e.g., Kafka consumer partitions, Flink task slots) based on load.                                                                                                         | Handling bursty traffic (e.g., Black Friday sales spikes).                 |

---

### **3. Schema Reference**
Define schemas for **source**, **intermediate**, and **sink** data to ensure type safety.

| **Field**               | **Type**          | **Description**                                                                 | **Example**                          |
|-------------------------|-------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **Source Schema**       |                   |                                                                                 |                                      |
| `event_id`              | `UUID`            | Unique identifier for the event.                                                | `550e8400-e29b-41d4-a716-446655440000` |
| `timestamp`             | `timestamp`       | Event-time (not processing-time).                                               | `2023-10-01T12:00:00Z`               |
| `sensor_data`           | `struct{value: float, unit: str}` | Embedded schema for nested data.               | `{"value": 23.5, "unit": "°C"}`       |
| **Intermediate Schema** |                   | After transformations (e.g., aggregations).                                   |                                      |
| `window_start`          | `timestamp`       | Start of the tumbling/sliding window.                                          | `2023-10-01T11:50:00Z`               |
| `window_end`            | `timestamp`       | End of the window.                                                              | `2023-10-01T12:00:00Z`               |
| `aggregated_metric`     | `float`           | Result of an aggregation (e.g., mean, count).                                  | `42.7`                               |
| **Sink Schema**         |                   | Final output for storage/ingestion.                                             |                                      |
| `recorded_at`           | `timestamp`       | When the record was written to the sink.                                       | `2023-10-01T12:05:00Z`               |
| `partition_key`         | `string`          | Key for partitioning (e.g., `user_id#region`).                                 | `alice#us-west`                      |

---
## **Query Examples**
### **1. Event-Time Tumbling Window Aggregation (Flink SQL)**
```sql
-- Query: Count events per 5-minute window
CREATE TABLE Events (
  event_id STRING,
  timestamp AS TO_TIMESTAMP(CAST(event_time AS STRING), 'yyyy-MM-dd HH:mm:ss'),
  sensor_data MAP<STRING, STRING>
) WITH (
  'connector' = 'kafka',
  'topic' = 'raw_events',
  'format' = 'json'
);

CREATE TABLE AggregatedMetrics (
  window_start TIMESTAMP(3),
  window_end TIMESTAMP(3),
  event_count BIGINT,
  avg_temp DOUBLE
) WITH (
  'connector' = 'filesystem',
  'path' = 'file:///opt/output',
  'format' = 'parquet'
);

INSERT INTO AggregatedMetrics
SELECT
  TUMBLE_START(timestamp, INTERVAL '5' MINUTE) AS window_start,
  TUMBLE_END(timestamp, INTERVAL '5' MINUTE) AS window_end,
  COUNT(*) AS event_count,
  AVG(CAST(sensor_data['value'] AS DOUBLE)) AS avg_temp
FROM Events
GROUP BY TUMBLE(timestamp, INTERVAL '5' MINUTE);
```

### **2. Keyed Join (Spark Streaming)**
```python
from pyspark.sql import functions as F

# Define DataFrames
stream_df = spark.readStream\
    .format("kafka")\
    .load("raw_events")\
    .selectExpr("CAST(value AS STRING)")

# Parse JSON and project
parsed_df = stream_df.select(
    F.from_json(F.col("value"), schema).alias("data")
).select("data.*")

# Keyed join with static reference data
user_prefs_df = spark.read.parquet("user_preferences.parquet")
joined_df = parsed_df.join(
    user_prefs_df,
    parsed_df["user_id"] == user_prefs_df["id"],
    "left"
)

# Write output
query = joined_df.writeStream\
    .outputMode("append")\
    .format("parquet")\
    .option("path", "output/joined_data")\
    .start()
```

### **3. Stateful Session Window (Flink Java API)**
```java
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
KafkaSource<String> source = KafkaSource.<String>builder()
    .setTopics("sensor_data")
    .setDeserializer(new SimpleStringSchema())
    .build();

DataStream<String> stream = env.fromSource(
    source,
    WatermarkStrategy.noWatermarks(),
    "Kafka Source"
);

KeyedStream<String, Tuple2<String, Integer>> keyedStream = stream
    .keyBy(event -> extractKey(event));

// Define session window (gap = 10 min inactivity)
SessionWindows.session(TIME_WINDOW(10, TimeUnit.MINUTES))
    .allowedLateness(Duration.ofMinutes(5))
    .sideOutputLateData(new PatternOutputTag<>("late_data"));

stream.process(new ProcessWindowFunction<>(
    Types.STRING,
    new TypeHint<Tuple2<String, Integer>>() {},
    window -> // Implement aggregation logic
));
```

---

## **4. Best Practices**
1. **Partitioning**:
   - Align Kafka partitions with Flink/Spark parallelism (e.g., 1:1 ratio) to avoid skew.
   - Use **custom partitioners** for non-uniform data (e.g., zip codes).

2. **Fault Tolerance**:
   - Enable **checkpointing** (e.g., every 10s) with external storage (S3, HDFS).
   - Use **exactly-once semantics** for sinks (e.g., idempotent Kafka producers).

3. **Late Data Handling**:
   - Set **watermark intervals** (e.g., 5s) to advance event time.
   - Use **side outputs** to separate late data from primary results.

4. **Resource Management**:
   - Monitor **backpressure** via metrics (e.g., Flink’s `numInFlightRequests`).
   - Scale consumers dynamically (e.g., Kafka consumer lag < 5 minutes).

5. **Testing**:
   - Test with **chaotic conditions**: network partitions, late data, or restarting the processor.
   - Use **unit tests** for transformations (e.g., mock streams with `TestStream` in Flink).

---
## **5. Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Event Sourcing]**      | Streams can emit events from an event-sourced system.                          | Audit logs, replayable state changes.                                           |
| **[CQRS]**                | Streaming strategies update read models independently of write models.         | Real-time dashboards with eventual consistency.                                |
| **[Bulkhead Pattern]**    | Limit resource contention when scaling streaming consumers.                     | Isolating high-priority streams (e.g., fraud alerts).                          |
| **[Saga Pattern]**        | Use streams to orchestrate distributed transactions.                           | Microservices with compensating transactions (e.g., order processing).        |
| **[Idle Connection Handling]** | Manage long-lived streaming connections (e.g., WebSockets).               | Continuous user sessions (e.g., live gaming scores).                            |
| **[Circuit Breaker]**     | Protect streaming pipelines from downstream failures.                          | Resilient to database or API timeouts.                                         |

---
## **6. Anti-Patterns to Avoid**
- **Ignoring Watermarks**: Leads to incorrect event-time aggregations with late data.
- **Overusing State**: Stateful processing increases resource usage; prefer **windowed** or **session** aggregations.
- **Tight Coupling**: Avoid hardcoding sinks (e.g., always write to PostgreSQL); use **adapters**.
- **No Backpressure Handling**: Can overwhelm downstream systems (e.g., Kafka producers).
- **Skipping Checkpoints**: Risks losing state upon failure.

---
## **7. Tools & Libraries**
| **Category**           | **Tools**                                                                 |
|------------------------|---------------------------------------------------------------------------|
| **Streaming Frameworks** | Apache Flink, Apache Spark Streaming, Apache Kafka Streams, Google Dataflow |
| **Message Brokers**    | Kafka, Pulsar, RabbitMQ (for event-driven sinks)                        |
| **State Backends**     | RocksDB (embedded), Redis, Cassandra                                       |
| **Testing**           | Flink’s `TestHarness`, Spark’s `Structured Streaming` mocks              |
| **Monitoring**        | Prometheus + Grafana (metrics), ELK Stack (logs), Kafka Lag Exporter    |

---
## **8. References**
- **Apache Flink Documentation**: [`flink.apache.org`](https://flink.apache.org)
- **Kafka Streams Guide**: [`kafka.apache.org`](https://kafka.apache.org/documentation/streams)
- **Spark Streaming API**: [`spark.apache.org/docs/latest/structured-streaming.html`](https://spark.apache.org/docs/latest/structured-streaming.html)
- **Event-Time Processing**: [Voldemort (2007)](https://www.usenix.org/legacy/publications/library/proceedings/nsdi07/full_papers/paper_3.pdf) (foundational paper)