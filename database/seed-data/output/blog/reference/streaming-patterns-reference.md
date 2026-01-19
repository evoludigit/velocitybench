# **[Streaming Patterns] Reference Guide**

---

## **Overview**
The **Streaming Patterns** framework provides a structured approach to processing data in real-time as it is generated, rather than in batch. This pattern is essential for applications requiring low-latency decision-making, such as IoT telemetry, financial transactions, log analytics, or fraud detection. It leverages event-driven architectures, distributed processing (e.g., Kafka, Flink, Spark Streaming), and stateless or stateful transformations to handle unbounded data streams efficiently.

Key goals include **scalability**, **fault tolerance**, **exactly-once processing**, and **decoupled components**. This guide covers core patterns (e.g., *Filter*, *Aggregate*, *Join*), their use cases, implementation primitives, and anti-patterns.

---
## **Schema Reference**

| **Pattern**          | **Purpose**                                                                 | **Key Operations**                                                                 | **State**       | **Example Components**                     |
|----------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|-----------------|---------------------------------------------|
| **Filter**           | Selects records matching a condition (e.g., `WHERE` clause).                 | Predicate evaluation (`filter`/`where` in SQL).                                     | Stateless       | Kafka Streams KTable, Flink `FilterFunc`   |
| **Aggregate**        | Computes metrics (e.g., `SUM`, `COUNT`, `AVG`) over a window of events.      | Windowing (`tumbling`, `sliding`, `session`), keyed aggregations.                   | Stateful (per-key)| Spark Streaming `aggregate()`, Flink `Reduce` |
| **Join**             | Combines two streams by a key (e.g., stream-stream or stream-table).         | Inner/outer joins with time-based alignment (e.g., *late data handling*).           | Stateful        | Flink `Join`, Spark `joinWith`              |
| **Enrich**           | Augments event data with external references (e.g., lookup tables).           | Dynamic joins with small, cached datasets.                                         | Stateless       | Kafka Streams `join` (local table)         |
| **Sessionize**       | Groups events into sessions based on inactivity gaps (e.g., user clicks).     | Session windowing (e.g., gaps of 10 minutes).                                      | Stateful        | Flink `SessionWindows`, Spark `session`     |
| **WindowAll**        | Applies an operation to *all* events in a time window (e.g., global stats). | Non-keyed windows (e.g., rolling 5-minute averages).                                | Stateless       | Flink `GlobalWindow`, Kafka `windowStore`   |
| **Split**            | Routes events to multiple branches (e.g., routing by priority).              | Conditional branching (e.g., `if-else` logic).                                    | Stateless       | Kafka Streams `branching`                   |
| **Watermark**        | Tracks event processing progress to handle out-of-order data.                 | Assigns timestamps/watermarks; enables late-arriving data handling.                | Stateful        | Flink `WatermarkStrategy`, Spark `watermark`|
| **Sink**             | Writes processed data to a destination (e.g., database, file).               | Idempotent writes, checkpointing.                                                    | Stateful        | Kafka Sink Connector, Flink `SinkFunction`  |

---
## **Implementation Details**

### **1. Core Concepts**
- **Event Time vs. Processing Time**:
  - *Event time* uses timestamps embedded in events (for order preservation).
  - *Processing time* uses the system clock (simpler but prone to delays).
- **Windows**:
  - **Tumbling**: Non-overlapping fixed intervals (e.g., every 5 minutes).
  - **Sliding**: Overlapping windows with fixed steps (e.g., 5-minute steps every 1 minute).
  - **Session**: Dynamically sized based on inactivity (e.g., 30-minute gaps).
- **State Management**:
  - **Keyed State**: Per-key state (e.g., aggregations like `COUNT`).
  - **Operator State**: Shared state for non-keyed operations (e.g., `WindowAll`).

### **2. Fault Tolerance**
- **Checkpointing**: Periodically saving state to durable storage (e.g., HDFS, S3).
- **Exactly-Once Processing**: Ensures no duplicate or missing events via:
  - Transactional sinks (e.g., Kafka transactions).
  - Idempotent operations (e.g., upsert-only writes).
- **Backpressure**: Throttling producers/consumers to avoid resource exhaustion.

### **3. Anti-Patterns**
- **Overusing Stateful Operations**: Excessive joins/aggregates can lead to memory bloat.
- **Ignoring Watermarks**: Late data may cause incorrect results without watermarking.
- **Tight Coupling**: Avoid dependency on specific event sources (e.g., use adapters).

---

## **Query Examples**

### **1. Filter Pattern (Kafka Streams)**
```java
// Filter logs with error codes
KStream<String, String> logs = builder.stream("log-topic");
logs.filter((key, value) -> value.contains("ERROR"))
    .to("errors-topic");
```

### **2. Aggregate Pattern (Flink)**
```python
# Count events per user in a 10-minute tumbling window
tumbledCounts = (
    events.keyBy("user_id")
           .window(TumblingEventTimeWindows.of(Time.minutes(10)))
           .aggregate(AggFunction, new CountAggregator())
)
```

### **3. Stream-Stream Join (Spark Streaming)**
```scala
// Join user activity with product catalog (left outer join)
val activity: DStream[(String, String)] = ...
val catalog: DStream[(String, Product)] = ...
val joined = activity.join(catalog)
                    .map { case (user, (activityEvent, product)) =>
                        (user, s"${activityEvent} - ${product.name}")
                    }
```

### **4. Enrich Pattern (Kafka Streams)**
```java
// Look up user details from a local cache
KTable<String, User> userTable = builder.table("user-store");
KStream<String, Event> events = builder.stream("events-topic");
events.join(userTable, (event, user) -> new EnrichedEvent(event, user))
      .to("enriched-events-topic");
```

### **5. Sessionize Pattern (Flink)**
```java
// Group user clicks into sessions (30-minute gap)
SessionWindows sessionWindows = SessionWindows
    .withGap(Time.minutes(30));
events.keyBy("user_id")
       .window(sessionWindows)
       .aggregate(new SessionAggregator())
       .to("user-sessions-topic");
```

### **6. Watermark Handling (Spark)**
```python
# Process late data with a 5-second allowed lateness
ssc.checkpoint("checkpoint-dir")
windowedCounts = activity.map(lambda x: (x.user, x.timestamp))
                        .window(TimeWindow(30, "seconds"),
                                allowedLateness=Time(5, "seconds"))
                        .count()
```

---
## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                          |
|---------------------------|---------------------------------------------------------------------------------|----------------------------------------------------------|
| **CQRS**                  | Separates read and write models for scalability.                                | High-throughput writes with complex queries.             |
| **Event Sourcing**        | Stores state changes as an append-only log.                                     | Audit trails, replayability.                             |
| **Side Output**           | Routes side data (e.g., alerts) separately from main output.                     | Monitoring or logging secondary events.                  |
| **Dynamic Routing**       | Adapts processing paths at runtime (e.g., A/B testing).                          | Flexible event handling without code changes.            |
| **Backpressure Handling** | Controls producer/consumer rates to avoid overload.                              | Resource-constrained environments.                      |

---
## **Setup Checklist**
1. **Event Source**:
   - Kafka topics, Kinesis streams, or custom publishers.
2. **Processor**:
   - Spark Streaming, Flink, or Kafka Streams (choose based on latency/state needs).
3. **Sink**:
   - Configure checkpointing (e.g., HDFS, S3).
4. **Monitoring**:
   - Track lag, watermarks, and backpressure (e.g., Prometheus + Grafana).
5. **Testing**:
   - Test with out-of-order data and failures.

---
**References**:
- [Apache Flink Docs](https://nightlies.apache.org/flink/flink-docs-stable/)
- [Kafka Streams Guide](https://kafka.apache.org/documentation/streams/)
- *Streaming Systems* (book by Tyler Akidau et al.).