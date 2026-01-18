# **[Pattern] Streaming Approaches Reference Guide**

---
## **Overview**
The **Streaming Approaches** pattern enables real-time processing of data by ingesting, processing, and acting upon continuous data streams, rather than batching or storing it for later. This pattern is essential for applications requiring low-latency responses (e.g., IoT, financial trading, fraud detection, or live analytics). Streaming architectures handle unbounded data by dividing it into events or records processed sequentially as they arrive, using frameworks like Apache Kafka, Apache Flink, or AWS Kinesis.

Key capabilities include:
- **Event-driven processing**: Data flows as events, enabling instant reactions.
- **Stateful computations**: Maintaining state (e.g., aggregations, session tracking) across streams.
- **Fault tolerance**: Guaranteeing no data loss via replay or checkpointing.
- **Scalability**: Horizontal scaling via distributed stream processors.

This guide covers core concepts, schema design, query techniques, and trade-offs for implementing streaming approaches.

---

## **Key Concepts & Implementation Details**
### **Core Components**
| **Term**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Data Sources**       | Systems (e.g., sensors, APIs, databases) producing raw event streams.                                                                                                                                       | IoT devices sending temperature readings every second.                         |
| **Stream Processors**  | Frameworks (e.g., Flink, Spark Streaming) that ingest, transform, and route streams.                                                                                                                      | Flink Job processing clickstream data to detect anomalies.                   |
| **Event Types**        | Structured records (e.g., JSON, Avro) with metadata (timestamp, key, value).                                                                                                                               | `{"user_id": "123", "action": "purchase", "timestamp": "2024-01-01T12:00:00Z"}` |
| **Partitioning**       | Splitting streams into parallel channels for parallel processing.                                                                                                                                         | Kafka topic with 3 partitions for 3 consumer threads.                      |
| **Checkpointing**      | Saving state snapshots to recover from failures.                                                                                                                                                           | Flink saving window aggregates to HDFS every 5 minutes.                     |
| **Sink**               | Destination (e.g., database, dashboard) for processed data.                                                                                                                                                 | Writing aggregated sales data to PostgreSQL.                                |
| **Windowing**          | Grouping events into time-based or count-based batches (e.g., tumbling, sliding, session windows).                                                                                                          | Tumbling window: Summing sales every 10 minutes.                           |
| **Late Data Handling** | Strategies for events arriving after a window closes (e.g., watermarks, allowable lateness).                                                                                                                   | Watermark delay of 5 seconds for Kafka streams.                             |

---

### **Stream Processing Models**
| **Model**          | **Description**                                                                                                                                                                                                 | **Use Case**                          |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| **Event Sourcing** | Appends immutable logs of state changes; replayable for reprocessing.                                                                                                                                            | Financial audit trails.               |
| **Lambda Architecture** | Combines batch (for accuracy) and real-time (for speed) layers via merge step.                                                                                                                                 | Personalized recommendations.        |
| **Kappa Architecture** | Single real-time pipeline replacing batch; state managed via databases.                                                                                                                                       | Log analytics.                        |
| **Microservices with Streams** | Decoupled services communicate via streamed events (e.g., Kafka).                                                                                                                                           | E-commerce order fulfillment.         |

---

## **Schema Reference**
Design schemas to ensure consistency across sources, processors, and sinks. Below are common **event schemas** and **state schemas**.

### **1. Event Schema (Source → Processor)**
| **Field**         | **Type**      | **Description**                                                                                     | **Example**                     |
|--------------------|---------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `event_id`         | String (UUID) | Unique identifier for the event.                                                                     | `"550e8400-e29b-41d4-a716-446655440000"` |
| `timestamp`        | Timestamp     | When the event was generated (use system clock or ingestion time).                                    | `"2024-01-01T12:00:00.000Z"`   |
| `source`           | String        | System/origin of the event (e.g., `"sensor_42"`, `"checkout_page"`).                                | `"sensor_42"`                   |
| `data`             | JSON          | Structured payload (schema-on-read or schema-on-write).                                             | `{"value": 23.5, "unit": "C"}`  |
| `metadata`         | JSON          | Additional context (e.g., user ID, session ID).                                                     | `{"user_id": "abc123"}`         |

---
### **2. State Schema (Processor → Sink)**
Used for aggregations, sessions, or side outputs.

| **Field**         | **Type**      | **Description**                                                                                     | **Example**                     |
|--------------------|---------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `window_id`        | String        | Key for windowed operations (e.g., `user_id#tumbling_10min`).                                        | `"abc123#tumbling_10min"`       |
| `value`            | Numeric       | Aggregated result (e.g., sum, count).                                                                | `{"total_sales": 99.99}`        |
| `last_updated`     | Timestamp     | When the state was last modified.                                                                      | `"2024-01-01T12:05:00.000Z"`   |
| `ttl`              | Duration      | Time-to-live for ephemeral state (e.g., session tracking).                                           | `"P1H"`                          |

---
### **3. Schema Evolution Strategies**
| **Strategy**               | **Pros**                                                                 | **Cons**                                                                 | **Tools**                     |
|----------------------------|--------------------------------------------------------------------------|--------------------------------------------------------------------------|-------------------------------|
| **Backward-Compatible**    | No breaking changes for consumers.                                        | Limited flexibility for new fields.                                      | Avro/Schema Registry          |
| **Forward-Compatible**     | New consumers tolerate old events.                                        | Producers must handle missing fields.                                    | Protobuf + Optional Fields    |
| **Schema Registry**        | Centralized versioning and validation.                                     | Additional infrastructure.                                                | Confluent Schema Registry      |
| **Dynamic Typing**         | Flexible but requires runtime parsing.                                    | Higher overhead; harder to validate.                                     | JSON + Custom Parsers         |

---

## **Query Examples**
Streaming queries differ from batch SQL; below are templates for common operations using **Apache Flink SQL** and **Kafka Streams**.

---

### **1. Basic Filtering & Aggregation**
**Use Case**: Count daily active users (DAU) from clickstream events.
```sql
-- Flink SQL
CREATE TABLE UserClicks (
  user_id STRING,
  event_time TIMESTAMP(3),
  WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'clickstream',
  'format' = 'json'
);

SELECT
  user_id,
  COUNT(*) AS daily_clicks
FROM (
  SELECT DISTINCT user_id, event_time
  FROM UserClicks
  WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL '1' DAY
)
GROUP BY user_id, DATE(event_time);
```

**Equivalent Kafka Streams (Java)**:
```java
StreamsBuilder builder = new StreamsBuilder();
KStream<String, UserClick> clicks = builder.stream("clickstream");
clicks
  .groupByKey()
  .windowedBy(TimeWindows.of(Duration.ofHours(24)))
  .aggregate(
    () -> 0,
    (key, value, agg) -> agg + 1,
    Materialized.with("dau-store", Serdes.String(), Serdes.Long())
  )
  .toStream()
  .to("dau-results");
```

---

### **2. Windowed Joins**
**Use Case**: Join user events with product catalog updates (stream-stream join).
```sql
-- Flink SQL
CREATE TABLE ProductUpdates (
  product_id STRING,
  price DOUBLE,
  update_time TIMESTAMP(3),
  WATERMARK FOR update_time AS update_time - INTERVAL '10' SECOND
) WITH (...);

SELECT
  u.user_id,
  p.product_id,
  u.event_time,
  p.price
FROM UserClicks u
JOIN ProductUpdates p
  ON u.product_id = p.product_id
  AND u.event_time BETWEEN p.update_time AND p.update_time + INTERVAL '1' HOUR
```

---

### **3. Session Windows**
**Use Case**: Detect inactive users (session gap >30 min).
```sql
-- Flink SQL
SELECT
  user_id,
  event_time,
  COUNT(*) AS events_in_session
FROM (
  SELECT
    user_id,
    event_time,
    TUMBLE_START(event_time, INTERVAL '30' MINUTE) AS session_window
  FROM UserClicks
)
GROUP BY user_id, session_window
HAVING COUNT(*) < 2;  -- Users with <2 events in 30-min window
```

---

### **4. Stateful Processing (Sessionization)**
**Use Case**: Track user sessions and calculate session duration.
```java
// Kafka Streams (Java)
StreamsBuilder builder = new StreamsBuilder();
KStream<String, UserEvent> events = builder.stream("user-events");

// Define session window (30 min inactivity)
SessionWindows sessionWindows = SessionWindows.of(Duration.ofMinutes(30))
    .withGap(Duration.ofMinutes(30));

KeyValueStore<String, Long> sessionStore = Stores.keyValueStoreBuilder(
    Stores.inMemoryKeyValueStore("sessions"),
    Serdes.String(),
    Serdes.Long()
).build();

builder.addStateStore(sessionStore);

events
    .groupByKey()
    .windowedBy(sessionWindows)
    .aggregate(
        () -> 0L,
        (key, value, agg) -> agg + 1,
        Materialized.with("sessions", Serdes.String(), Serdes.Long())
    )
    .toStream()
    .foreach((key, value) -> {
        // Calculate duration: last_event_time - first_event_time
        long duration = ...;
        System.out.printf("Session %s lasted %d ms%n", key.key(), duration);
    });
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                                                                                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **[Event Sourcing](link)** | Append-only log of state changes; replayable for auditing/reconstruction.                                                                                                                              | Financial systems, audit trails.         |
| **[CQRS](link)**           | Separate read/write models for scalable querying (e.g., Materialized Views).                                                                                                                         | Complex queries on streaming data.       |
| **[Sink Pattern](link)**  | Decouple producers/consumers via buffers (e.g., Kafka topics).                                                                                                                                         | High-throughput event pipelines.         |
| **[Side Outputs](link)**  | Route events to multiple destinations (e.g., alerts + analytics).                                                                                                                                         | Multi-channel notifications.             |
| **[Exactly-Once Processing](link)** | Guarantee no duplicates/loss via transactional sinks (e.g., Kafka transactions).                                                                                                                       | Critical financially systems.            |
| **[Dynamic Routing](link)** | Conditionally route events based on runtime logic (e.g., A/B testing).                                                                                                                                | Personalized user experiences.           |

---

## **Best Practices & Pitfalls**
### **Do:**
✅ **Use Watermarks**: Handle late data gracefully (e.g., `event_time - 5s`).
✅ **Partition Strategically**: Align partitions with keys to avoid skew.
✅ **Monitor Lag**: Track consumer lag in Kafka (`kafka-consumer-groups --describe`).
✅ **Leverage Idempotency**: Design sinks to handle duplicate events (e.g., upsert DB rows).
✅ **Test with Chaos**: Simulate failures (e.g., `kafka-producer-perf-test --producer-props bootstrap.servers=localhost:9092` with `--record-errors`).

### **Avoid:**
❌ **Long-Running Windows**: Tumbling windows >1 hour increase state memory.
❌ **Global State**: Avoid single-node state; use distributed stores (e.g., RocksDB).
❌ **Untyped Schemas**: Use schemas (Avro/Protobuf) instead of raw JSON for tooling.
❌ **Tight Coupling**: Decouple producers/consumers via streams (e.g., Kafka topics).
❌ **Ignoring Backpressure**: Monitor `KafkaConsumer.poll()` delays to avoid OOMs.

---
## **Tools & Frameworks**
| **Category**       | **Tools**                                                                 | **Key Features**                                                                 |
|--------------------|---------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Streaming Engines** | Apache Flink, Apache Spark Streaming, Kafka Streams, Amazon Kinesis      | Stateful processing, exactly-once, windowing.                                   |
| **Messaging**      | Apache Kafka, AWS MSK, Confluent Cloud                                    | High-throughput, durable, partitioned topics.                                  |
| **Schemas**        | Avro, Protobuf, Confluent Schema Registry                                  | Backward/forward compatibility, ser/de.                                         |
| **State Backends** | RocksDB, FSStateBackend (Flink), DynamoDB (Kinesis)                       | Scalable, fault-tolerant state storage.                                        |
| **Monitoring**     | Prometheus + Grafana, Kafka Manager, Flink Web UI                         | Latency, throughput, consumer lag.                                             |
| **Testing**        | Kafka Streams Unit Tests, Flink TestHarness, TestContainers              | Unit/integration tests for event processing.                                  |

---
## **Further Reading**
- [Apache Flink SQL Guide](https://nightlies.apache.org/flink/flink-docs-master/docs/connectors/table/sql/)
- [Kafka Streams Developer Guide](https://kafka.apache.org/documentation/streams/)
- [Lambda vs. Kappa Architecture](https://engineering.linkedin.com/distributed-systems/lambda-architecture-simplified)
- [Event-Driven Microservices](https://www.oreilly.com/library/view/event-driven-microservices/9781491993471/)