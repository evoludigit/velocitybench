# **[Pattern] Stream Processing Reference Guide**

## **Overview**
The **Stream Processing** pattern enables real-time analysis and processing of **unbounded, time-ordered data** streams from sources like IoT devices, logs, user events, or financial transactions. Unlike batch processing, stream processing applies continuous transformations, aggregations, or actions to data as it arrives, making it ideal for applications requiring low-latency insights (e.g., fraud detection, real-time dashboards, or anomaly monitoring).

Key characteristics of stream processing include:
- **Continuous ingestion** – Data is processed as it streams in, not stored in bulk.
- **Exactly-once or at-least-once semantics** – Ensures consistency and avoids duplication.
- **Stateful processing** – Maintains state (e.g., counters, sessions) across events.
- **Fault tolerance** – Handles failures gracefully via checkpointing or replay mechanisms.
- **Scalability** – Distributed processing frameworks (e.g., Apache Flink, Kafka Streams) handle high throughput.

---

## **Schema Reference**
Stream processing systems typically model data using the following components:

| **Component**       | **Description**                                                                                     | **Example**                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Source**           | Generates raw event data. Can be messages, logs, or sensor data.                                   | `{ "user_id": 123, "timestamp": "2024-05-20T12:00:00Z", "event": "purchase" }`               |
| **Stream**           | Ordered sequence of events (e.g., `orders`, `clicks`).                                              | `OrdersStream = Source("order-service", "orders")`                                               |
| **Window**           | Time-based or count-based grouping for aggregations (e.g., tumbling, sliding, session windows).     | `window.Tumbling(interval=5.minutes)`                                                           |
| **State**            | Persistent key-value storage for maintaining state across events (e.g., user session data).       | `StateDescriptor("user_sessions", new ValueStateDescriptor<>("session", String.class))`       |
| **Processing Logic** | Functions/applications (e.g., `map`, `filter`, `aggregate`) to transform or react to data.        | `.filter(event -> event.value >= 100).reduce((acc, val) -> acc + val)`                         |
| **Sink**             | Outputs processed results (e.g., databases, dashboards, other streams).                            | `sink.to("alerts-database")`                                                                   |
| **Error Handling**   | Mechanisms to retry, log, or dead-letter failed events.                                            | `ErrorSink("alerts", "error_logs_kafka")`                                                       |

**Related Concepts:**
- **Watermarks** – Indicates progress through a stream to handle late events.
- **Checkpoints** – Periodic snapshots of state for recovery.

---

## **Implementation Options**
| **Framework**       | **Key Features**                                                                                     | **Use Case**                                                                                     |
|---------------------|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Apache Flink**    | Low-latency, stateful processing, exactly-once semantics, Kubernetes integration.                   | Fraud detection, real-time analytics.                                                            |
| **Apache Kafka Streams** | Lightweight, integrates with Kafka, simple API (DStreams).                                        | Event-driven microservices, log processing.                                                     |
| **Apache Spark Streaming** | Batch-like processing (DStream API), fault tolerance via RDDs.                                       | Large-scale historical + real-time analytics.                                                   |
| **AWS Kinesis**     | Serverless, scales automatically; integrates with Lambda or Flink.                                   | Media processing, IoT telemetry.                                                               |
| **Custom (e.g., Python/Go)** | Lightweight for niche needs; requires manual fault tolerance/state management.                      | Prototyping, edge devices.                                                                       |

---

## **Query Examples**
Below are common operations in stream processing frameworks like Flink or Kafka Streams.

### **1. Simple Filtering**
```java
// Flink: Filter orders over $100
DataStream<Order> orders = env.addSource(new KafkaSource<>(...));
DataStream<Order> highValueOrders = orders
    .filter(order -> order.getAmount() > 100);
```

```python
# Python (e.g., with PyFlink)
orders = env.add_source(KafkaSource(...))
high_value_orders = orders.filter(lambda order: order.amount > 100)
```

### **2. Time-Based Aggregations**
```java
// Flink: Tumbling window avg. order value per minute
DataStream<Double> avgOrderValue = orders
    .keyBy(Order::getUserId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new AvgOrderValueAggregator());
```

### **3. Stateful Session Processing**
```java
// Flink: Track user sessions (inactive > 30 mins)
StateTemporalFunctions<UserSession> sessionState =
    new UserSessionState(stateTemporalFunctions);
sessionState
    .addSink(new SessionSink())
    .setIdlenessGap(Time.minutes(30));
```

### **4. Joining Streams**
```java
// Flink: Enrich orders with user profiles
DataStream<Order> enrichedOrders = orders
    .keyBy(Order::getUserId)
    .connect(userProfiles)
    .process(new UserProfileEnrichment());
```

### **5. Late Data Handling**
```java
// Flink: Allow late events up to 5 mins
env.getConfig().setAutoWatermarkInterval(1000);
orders.assignTimestampsAndWatermarks(
    WatermarkStrategy
        .<Order>forBoundedOutOfOrderness(Duration.ofSeconds(300))
        .withTimestampAssigner((event, timestamp) -> event.getTimestamp())
);
```

---

## **Best Practices**
1. **Optimize State Storage**
   - Use **RocksDB** for large state (Flink) or **Kafka** as a state backend.
   - Evict old state with TTL policies.

2. **Control Parallelism**
   - Align `keyBy()` partitions with downstream resources to avoid bottlenecks.

3. **Monitor Latency**
   - Track **end-to-end latency** (source → sink) and **processing latency**.
   - Use metrics (Prometheus, Flink’s built-in metrics).

4. **Handle Backpressure**
   - Scale sources/sinks or increase parallelism if buffers overflow.

5. **Test with Realistic Data**
   - Simulate **out-of-order events**, **gaps**, and **failures** (e.g., using tools like [TestContainers](https://www.testcontainers.org/)).

6. **Leverage Exactly-Once**
   - Use transactional sinks (e.g., Kafka, JDBC) to avoid duplicates.

7. **Security**
   - Encrypt streams in transit (TLS) and at rest (e.g., S3).
   - Restrict access to state backends (e.g., Kafka ACLs).

---

## **Failure Scenarios & Mitigations**
| **Scenario**               | **Impact**                          | **Mitigation**                                                                 |
|----------------------------|-------------------------------------|-------------------------------------------------------------------------------|
| **Source failure**         | Data loss or delay                  | Replay from checkpointed offsets (Kafka).                                   |
| **Sink failure**           | Backpressure, dropped events        | Dead-letter queues (DLQ) + retries.                                         |
| **State corruption**       | Incorrect aggregations              | Periodic state snapshots + rebuilds.                                        |
| **Late events**            | Stale aggregations                  | Watermarks + allow-late policies.                                           |
| **Resource exhaustion**     | Crashes or timeouts                 | Auto-scaling (Kubernetes) + resource quotas.                               |

---

## **Query Performance Tips**
| **Technique**               | **Description**                                                                                     | **Example**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Local Key Groups**        | Co-locate related keys for faster joins.                                                          | `.keyBy(Order::getUserId).connect(userProfiles.keyBy(U::getId))`                             |
| **Watermark Tuning**        | Adjust `boundedOutOfOrderness` to balance latency vs. throughput.                                  | `.withTimestampAssigner(...).withTimestampAssigner(Duration.ofSeconds(60))`                |
| **State Backend**           | Use **heap-based** (Flink) for small state; **RocksDB** for large.                               | `env.setStateBackend(new RocksDBStateBackend(...))`                                           |
| **Window Optimization**     | Prefer **sliding windows** over tumbling for overlapping data.                                    | `SlidingEventTimeWindows.of(5.minutes, 1.minute)`                                              |

---

## **Related Patterns**
1. **Event Sourcing**
   - Store state changes as an immutable event log. Stream processing can replay events for reconstructions.

2. **CQRS (Command Query Responsibility Segregation)**
   - Use streams to decouple writes (commands) from reads (queries). Stream processing powers real-time query views.

3. **Lambda Architecture**
   - Combines batch (for historical) + stream processing (for real-time) for hybrid analytics.

4. **Event-Driven Architecture (EDA)**
   - Streams enable event propagation across services (e.g., Kafka topics as message buses).

5. **State Machine Pattern**
   - Use stream processing to model state transitions (e.g., order workflows).

---

## **Example Architecture**
```
[IoT Devices] → [Kafka] → [Stream Processor (Flink)] → [Alerts DB] / [Dashboard]
                  ↓
[State Backend: RocksDB/Kafka]
                  ↓
[Checkpoint Storage: S3]
```

---
**Further Reading:**
- [Apache Flink Documentation](https://flink.apache.org/)
- [Kafka Streams Guide](https://kafka.apache.org/documentation/streams/)
- ["Designing Data-Intensive Applications" (Ch. 9)](https://dataintensive.net/)