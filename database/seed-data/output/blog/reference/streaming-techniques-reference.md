# **[Pattern] Streaming Techniques: Reference Guide**

## **Overview**
The **Streaming Techniques** pattern enables real-time data processing, analysis, and delivery by breaking information into continuous, sequenced chunks (streams) rather than discrete batches. This pattern is ideal for applications requiring low-latency ingestion (e.g., IoT telemetry, financial transactions, or live analytics) where traditional batch processing is infeasible. Implementations leverage pub/sub architectures, event sourcing, or streaming databases to ensure data is processed as it arrives, with decoupled producers/consumers, fault tolerance, and dynamic scaling capabilities.

---

## **Key Concepts & Implementation Details**

### **Core Components**
| **Component**          | **Description**                                                                                                                                                                                                 | **Example Use Case**                          |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Producer**            | Generates and emits data events (e.g., sensors, APIs, logs). Uses lightweight serialization (Protobuf, JSON, Avro).                                                                                    | IoT devices sending temperature readings.     |
| **Streaming Pipeline**  | Pipeline of processing stages (e.g., Kafka Streams, Flink, Spark Streaming) to transform, filter, or aggregate data. Stages may include:                                      | Real-time fraud detection in payments.      |
|   - **Source Stage**    | Ingests raw data (e.g., Kafka topics, webhooks).                                                                                                                                        | REST API streaming stock price updates.      |
|   - **Processing**      | Applies business logic (e.g., windowing, joins, machine learning).                                                                                                                                       | Anomaly detection on sensor data.             |
|   - **Sink Stage**      | Writes output (e.g., databases, dashboards, external APIs).                                                                                                                                           | Updating a live dashboard with metrics.       |
| **Consumer**            | Subscribes to processed streams (e.g., webhooks, long-polling, or server-sent events).                                                                                                                | Mobile app displaying live sports scores.    |
| **State Management**    | Maintains durable state (e.g., checkpoints, RocksDB in Flink) to handle restart failures and backpressure.                                                                                          | Recovering from a Flink job crash.            |
| **Partitioning**        | Divides streams into parallelizable chunks (e.g., Kafka partitions, Flink sources) to enable horizontal scaling.                                                                                       | Distributing log analysis across 10 nodes.   |
| **Exactly-Once Semantics** | Guarantees no duplication or loss of events via transactional writes (e.g., Kafka transactions, Flink checkpointing).                                                                                  | Financial audit trails for transactions.      |

---

### **Data Models & Schema**
Streaming systems often use **event-driven schemas** (schema registry + Avro/Protobuf) for backward compatibility. Below is a sample schema for a **sensor telemetry event**:

| **Field**            | **Type**   | **Description**                                                                 | **Example Value**               |
|-----------------------|------------|---------------------------------------------------------------------------------|----------------------------------|
| `event_id`           | `string`   | Unique identifier for the event (UUID).                                           | `"a1b2c3d4-5678-90ef-ghij"`      |
| `timestamp`          | `long`     | Unix epoch milliseconds (for ordering and windowing).                            | `1712345678901`                  |
| `sensor_id`          | `string`   | Device identifier (e.g., `factory-line-001`).                                     | `"factory-line-001"`             |
| `value`              | `double`   | Measured metric (e.g., temperature, pressure).                                  | `23.5`                           |
| `unit`               | `string`   | Physical unit (e.g., `"°C"`, `"psi"`).                                            | `"°C"`                           |
| `metadata`           | `map`      | Key-value pairs (e.g., `{"location": "zone_A", "status": "active"}`).            | `{"location": "zone_A"}`         |
| `partition_key`      | `string`   | Key for stream partitioning (e.g., `sensor_id`).                                  | `"factory-line-001"`             |

**Schema Evolution**: Use schema registries (e.g., Confluent Schema Registry) to manage backward/forward compatibility. Example:
```json
// Avro Schema (additive changes only)
{
  "type": "record",
  "name": "SensorEvent",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "sensor_id", "type": "string"},
    {"name": "value", "type": "double"},
    {"name": "unit", "type": "string", "default": "°C"},
    {"name": "metadata", "type": ["null", {"type": "map", "values": "string"}]}
  ]
}
```

---

## **Implementation Patterns**

### **1. Kafka Streams Processing**
**Use Case**: Real-time aggregations with low latency.
**Example**: Calculate 5-minute moving average of sensor values.

```java
// Java (Kafka Streams)
StreamsBuilder builder = new StreamsBuilder();
KStream<String, SensorEvent> sensorStream =
    builder.stream("sensor-topic");

KTable<String, Double> avgTable = sensorStream
    .groupBy((key, event) -> event.sensor_id, Materialized.with(String.class, Double.class))
    .windowedBy(TimeWindows.of(Duration.ofMinutes(5)))
    .aggregate(
        () -> 0.0,
        (key, value, agg) -> agg + value.value,
        Materialized.with(String.class, Double.class)
    )
    .mapValues(value -> value / 5.0); // Divide by window size

avgTable.toStream().to("sensor-avg-topic");
```

**Key Parameters**:
- `windowedBy`: Sliding/tumbling windows (e.g., `TimeWindows.of(Duration.ofMinutes(5)).advanceBy(Duration.ofMinutes(1))` for sliding).
- `Materialized`: State store backend (e.g., RocksDB for durability).

---

### **2. Apache Flink Processing**
**Use Case**: Complex event processing (CEP) with stateful transformations.
**Example**: Detect "spike" events (value > 10x rolling average).

```python
# PyFlink
from pyflink.datastream import StreamExecutionEnvironment, TableEnvironment
from pyflink.table import StreamTableEnvironment

env = StreamExecutionEnvironment.get_execution_environment()
t_env = StreamTableEnvironment.create(env)

t_env.execute_sql("""
    CREATE TABLE sensor_events (
        event_id STRING,
        sensor_id STRING,
        value DOUBLE,
        timestamp BIGINT,
        WATERMARK FOR timestamp AS timestamp - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'sensor-topic',
        'properties.bootstrap.servers' = 'localhost:9092',
        'format' = 'json'
    )
""")

t_env.execute_sql("""
    CREATE TABLE sensor_spikes AS
    SELECT
        sensor_id,
        value,
        ROW_NUMBER() OVER (PARTITION BY sensor_id ORDER BY timestamp) as row_num
    FROM sensor_events
    WHERE value > AVG(value) OVER (
        PARTITION BY sensor_id
        ORDER BY timestamp
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) * 10
""")
```

**Key Features**:
- **Watermarks**: Define event-time processing boundaries (e.g., `timestamp - INTERVAL '5' SECOND`).
- **CEP Libraries**: Use `Pattern` APIs for sequence detection (e.g., "three consecutive spikes").

---

### **3. Server-Sent Events (SSE) for Web Consumers**
**Use Case**: Real-time updates for web/mobile apps.
**Example**: Stream processed sensor data to a React dashboard.

```javascript
// Node.js (Express + Kafka Consumer)
const { Kafka } = require('kafkajs');
const kafka = new Kafka({ brokers: ['localhost:9092'] });
const consumer = kafka.consumer({ groupId: 'web-dashboard' });

async function startConsumer() {
  await consumer.connect();
  await consumer.subscribe({ topic: 'sensor-avg-topic', fromBeginning: true });

  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const data = JSON.parse(message.value.toString());
      console.log(`New avg for ${data.sensor_id}: ${data.value}`);
      // Emit via SSE
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    },
  });
}

// Express SSE endpoint
app.get('/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  startConsumer();
});
```

**Client-Side (React)**:
```javascript
useEffect(() => {
  const eventSource = new EventSource('http://localhost:3000/stream');
  eventSource.onmessage = (e) => {
    const data = JSON.parse(e.data);
    setSensorData((prev) => [...prev, data]);
  };
  return () => eventSource.close();
}, []);
```

---

## **Query Examples**
### **1. SQL-over-Stream (Flink/Spark SQL)**
```sql
-- Flink SQL: Tumbling window count per sensor
SELECT
    sensor_id,
    COUNT(*) as event_count,
    TUMBLE_START(timestamp, INTERVAL '5' MINUTE) as window_start,
    TUMBLE_END(timestamp, INTERVAL '5' MINUTE) as window_end
FROM sensor_events
GROUP BY sensor_id, TUMBLE(timestamp, INTERVAL '5' MINUTE)
```

### **2. Kafka Streams Joins**
```java
// Join sensor data with reference tables (e.g., sensor_calibration)
KStream<String, SensorEvent> sensorStream = ...;
KTable<String, CalibrationData> calibrationTable = ...;

sensorStream.join(calibrationTable,
    (event, calibration) -> new SensorEvent(
        event.event_id,
        event.sensor_id,
        event.value * calibration.factor,
        event.unit
    ))
    .to("calibrated-sensor-topic");
```

### **3. Windowed Aggregations (Spark Streaming)**
```python
# PySpark
from pyspark.sql.functions import window, avg

df = spark.readStream.format("kafka").load("sensor-topic")
sensor_df = df.selectExpr("CAST(value AS STRING) as json")

# Parse JSON and compute windowed avg
parsed_df = sensor_df.select(
    from_json("json", schema).alias("data"),
    col("data.timestamp").cast("timestamp")
).select("data.*", "timestamp")

windowed_avg = parsed_df.withWatermark("timestamp", "10 minutes") \
    .groupBy(
        window("timestamp", "5 minutes"),
        "sensor_id"
    ) \
    .avg("value")

windowed_avg.writeStream \
    .outputMode("update") \
    .format("console") \
    .start()
```

---

## **Performance Considerations**
| **Factor**               | **Recommendation**                                                                                                                                                                                                 | **Tooling**                          |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| **Throughput**           | Partition data evenly; avoid hot partitions. Use Kafka partitions or Flink sources with parallelism > CPU cores.                                                                                         | Kafka `num.partitions`, Flink `parallelism` |
| **Latency**              | Optimize serialization (Protobuf > JSON); reduce window sizes.                                                                                                                                                     | Avro/Protobuf, small tumbling windows |
| **State Size**           | Use incremental checks (e.g., `reduceFunction` in Flink) to avoid full scans.                                                                                                                                  | Flink `StateBackend` (RocksDB)       |
| **Backpressure**         | Scale consumers dynamically; use buffer pools (e.g., Spark’s `maxRatePerPartition`).                                                                                                                        | Spark `spark.streaming.backpressure` |
| **Fault Tolerance**      | Enable idempotent producers (Kafka `enable.idempotence=true`) and state checkpoints (Flink, Spark).                                                                                                     | Kafka `transactional.id`, Flink `checkpointing` |

---

## **Related Patterns**
| **Pattern**                     | **Relation to Streaming**                                                                                                                                                                                                         | **When to Use**                          |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------|
| **[CQRS](https://microservices.io/)** | Streaming enables real-time event sourcing for *command* streams and *query* projections.                                                                                                                             | Event-driven architectures with read/write separation. |
| **[Event Sourcing](https://eventstore.com/)** | Streams are the primary source of truth; replay events for state reconstruction.                                                                                                                                         | Auditable systems (e.g., banking, gaming). |
| **[Saga Pattern](https://microservices.io/patterns/data/saga.html)** | Use streams to coordinate distributed transactions (e.g., Kafka + Saga orchestration).                                                                                                                                    | Microservices with ACID-like workflows. |
| **[Materialized View](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/ch04.html)** | Pre-compute aggregations in streams (e.g., Flink tables) to serve low-latency queries.                                                                                                                                  | OLAP workloads with real-time needs.   |
| **[Pub/Sub Decoupling](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CategorizeMessage.html)** | Producers/consumers communicate via streams (e.g., Kafka topics) to decouple services.                                                                                                                                          | Decentralized event-driven apps.        |
| **[Lambda Architecture](https://lambda-architecture.net/)** | Streaming layer handles real-time processing; batch layer corrects errors.                                                                                                                                            | Hybrid batch/real-time analytics.       |

---

## **Anti-Patterns & Pitfalls**
1. **Batch Thinking in Streams**
   - *Issue*: Treating streams like batches (e.g., buffering all events before processing).
   - *Fix*: Process events as they arrive; use micro-batching only for cost optimization.

2. **Ignoring Watermarks**
   - *Issue*: Late data causes incorrect windowed results (e.g., Flink/Spark watermarks not aligned).
   - *Fix*: Set `allowedLateness` and use event-time processing.

3. **Unbounded State Growth**
   - *Issue*: Accumulating state without TTL (e.g., Flink RocksDB tables growing indefinitely).
   - *Fix*: Enable TTL policies (e.g., `stateTTL=PT1H` in Flink).

4. **Tight Coupling to Producers**
   - *Issue*: Consumers depend on producer schemas (e.g., hardcoded Kafka topics).
   - *Fix*: Use schema registries + dynamic topic discovery (e.g., Kafka’s `new topic` hooks).

5. **No Exactly-Once Guarantees**
   - *Issue*: Duplicate or lost events due to retries (e.g., HTTP backpressure).
   - *Fix*: Use transactional writes (Kafka `producer` + `transactional.id`) or idempotent consumers.

---
**See Also**:
- [Kafka Streams Docs](https://kafka.apache.org/documentation/streams/)
- [Flink CEP Guide](https://nightlies.apache.org/flink/flink-docs-stable/docs/learn/flink_cep/)
- [Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)