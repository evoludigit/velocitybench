---
# **[Pattern] Streaming Setup Reference Guide**

---

## **Overview**
The **Streaming Setup pattern** enables real-time data ingestion, processing, and distribution by establishing a continuous data pipeline from source to destination. This pattern is ideal for applications requiring low-latency event-driven processing, such as live analytics, IoT telemetry, financial transactions, or media streaming. It abstracts the complexity of managing connectors, transformations, and scalability, ensuring seamless data flow across distributed systems.

Key use cases include:
- **Real-time dashboards** (e.g., stock prices, sensor data).
- **Event-driven architectures** (e.g., microservices with asynchronous communication).
- **Media streaming** (e.g., video/audio transcoding pipelines).
- **Log and monitoring pipelines** (e.g., centralized analytics).

This guide covers the foundational components, schema design, query conventions, and integration best practices for implementing the Streaming Setup pattern.

---

## **Implementation Details**

### **Core Components**
A typical streaming setup consists of the following layers:

| **Component**          | **Purpose**                                                                 | **Example Technologies**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **Producers**          | Ingest and emit events/data streams.                                        | Kafka Producers, IoT devices, Webhooks, APIs      |
| **Stream Brokers**     | Decouple producers and consumers; buffer and forward events.                | Apache Kafka, AWS Kinesis, Pulsar, RabbitMQ      |
| **Stream Processors**  | Transform, filter, or aggregate data in real-time.                          | Apache Flink, Apache Spark Streaming, KSQL       |
| **Consumers**          | Process or store streamed data (e.g., databases, analytics engines).       | PostgreSQL (logical decoding), Elasticsearch, S3  |
| **Sink Adapters**      | Handle downstream delivery (e.g., batch writes, cache updates).              | JDBC Connectors, HTTP Clients, gRPC                |
| **Monitoring**         | Track pipeline health, latency, and throughput.                              | Prometheus, Grafana, Kafka Metrics                |

### **Key Concepts**
1. **Event-Driven Architecture (EDA):**
   - Data is emitted as **events** (e.g., JSON objects) with a **timestamp** and **schema**.
   - Producers publish events to topics/queues; consumers subscribe asynchronously.

2. **At-Least-Once vs. Exactly-Once Semantics:**
   - **At-least-once:** Events may be duplicated but never missed (default in most brokers).
   - **Exactly-once:** Guarantees no duplicates or omissions (requires idempotent consumers and transactional writes).

3. **Partitioning and Parallelism:**
   - Topics are divided into **partitions** to enable parallel processing.
   - Each partition assigns an **offset** to track progress (critical for fault tolerance).

4. **Backpressure Handling:**
   - Consumers should **throttle** or **buffer** data if processing lag exceeds thresholds to avoid broker overload.

5. **Schema Evolution:**
   - Use **avro**, **protobuf**, or **JSON Schema** for backward-compatible changes.
   - Avoid breaking changes mid-pipeline (e.g., renaming required fields).

---

## **Schema Reference**

### **1. Stream Event Schema**
All events in the pipeline must adhere to a **standard schema** for consistency. Below is a recommended template:

| **Field**          | **Type**       | **Description**                                                                 | **Example**                          | **Requirements**                          |
|--------------------|---------------|---------------------------------------------------------------------------------|--------------------------------------|-------------------------------------------|
| `event_id`        | `string` (UUID) | Unique identifier for the event (for deduplication).                           | `"550e8400-e29b-41d4-a716-446655440000"` | Mandatory. Auto-generated if not provided. |
| `timestamp`       | `timestamp`   | Event generation time (ISO 8601 format).                                       | `"2023-10-01T12:34:56.789Z"`        | Mandatory. Broker may override with ingestion time. |
| `source`          | `string`      | System/component originating the event (e.g., `"sensor_node_001"`).             | `"iot/weather_station"`              | Mandatory.                    |
| `data`            | `object`      | Payload specific to the event type (e.g., sensor readings, user actions).       | `{ "temperature": 23.5, "humidity": 45 }` | Mandatory. Schema defined per event type. |
| `metadata`        | `object`      | Non-payload context (e.g., `partition_key`, `processing_timestamp`).           | `{ "partition": "0", "processed_at": "2023-10-01T12:35:00Z" }` | Optional. |

---
### **2. Event Type Schemas**
Extend the base schema with **event-specific fields**. Example for a **sensor reading**:

| **Field**          | **Type**       | **Description**                                                                 | **Example**                          | **Notes**                                  |
|--------------------|---------------|---------------------------------------------------------------------------------|--------------------------------------|-------------------------------------------|
| `sensor_id`       | `string`      | Unique ID of the sensor (acts as partition key).                                | `"sensor_123"`                       | Used for keyed streams.                   |
| `value`           | `number`      | Measured value (e.g., temperature in Celsius).                                 | `23.5`                                | Required.                                 |
| `units`           | `string`      | Unit of measurement.                                                          | `"°C"`                                | Optional. Defaults to schema definition.   |
| `threshold_alert` | `boolean`     | Flag if value exceeds configured limits.                                      | `false`                               | Derived from processing logic.            |

---
### **3. Partition Key Strategy**
To ensure **even distribution** and **ordered processing**, define a **partition key** (e.g., `sensor_id` for sensor data). Avoid high-cardinality keys (e.g., `user_id` in a global stream).

| **Key**            | **Use Case**                                                                 | **Example**                     |
|--------------------|-----------------------------------------------------------------------------|----------------------------------|
| `sensor_id`       | Device-specific streams (e.g., IoT sensor telemetry).                      | `"sensor_123"`                   |
| `user_id`         | User-centric events (e.g., clickstreams).                                 | `"user_456"`                     |
| Composite Key     | Multi-dimensional partitioning (e.g., `device_id:location`).               | `"sensor_123:us-west"`           |

---

## **Query Examples**

### **1. Producing Events**
Producers emit events to a topic. Below is an example in **Python (using `confluent_kafka`)**:

```python
from confluent_kafka import Producer
import json

conf = {'bootstrap.servers': 'kafka-broker:9092'}
producer = Producer(conf)

event = {
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2023-10-01T12:34:56.789Z",
    "source": "iot/weather_station",
    "data": {"temperature": 23.5, "humidity": 45},
    "metadata": {"partition_key": "sensor_123"}
}

producer.produce(
    topic="sensor_telemetry",
    key=event["metadata"]["partition_key"],
    value=json.dumps(event).encode('utf-8')
)
producer.flush()
```

---
### **2. Consuming and Processing Events**
Consumers read events from a topic and apply transformations. Example in **Java (using `kafka-streams`)**:

```java
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.kstream.*;
import org.apache.kafka.common.serialization.*;

public class SensorStreamProcessor {
    public static void main(String[] args) {
        Properties props = new Properties();
        props.put(StreamsConfig.APPLICATION_ID_CONFIG, "sensor-processor");
        props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka-broker:9092");

        StreamsBuilder builder = new StreamsBuilder();

        // Define input/output topics and serialization
        KStream<String, String> stream = builder.stream(
            "sensor_telemetry",
            Produced.with(
                Serdes.String(),
                Serdes.String()
            )
        );

        // Parse JSON and filter alerts
        stream
            .mapValues(value -> {
                try {
                    Map<String, Object> data = new Gson().fromJson(value, Map.class);
                    Map<String, Object> event = (Map<String, Object>) data.get("data");
                    event.put("processed", System.currentTimeMillis());
                    return new Gson().toJson(event);
                } catch (Exception e) {
                    return "PARSE_ERROR";
                }
            })
            .filter((key, value) -> !value.equals("PARSE_ERROR"))
            .to("processed_sensor_data");

        KafkaStreams streams = new KafkaStreams(builder.build(), props);
        streams.start();
    }
}
```

---
### **3. Querying Processed Data**
Consumers can query processed data using **SQL (via KSQL)** or direct topic consumption:

#### **KSQL Example:**
```sql
-- Create a stream table from a Kafka topic
CREATE STREAM sensor_processed (
    sensor_id VARCHAR,
    value DOUBLE,
    units VARCHAR,
    processed_at TIMESTAMP
) WITH (
    KAFKA_TOPIC='processed_sensor_data',
    VALUE_FORMAT='JSON'
);

-- Run a query to find alerts
SELECT *
FROM sensor_processed
WHERE value > 30;
```

---
### **4. Sink Integration (Writing to Database)**
Use **CDC (Change Data Capture)** or direct writes for persistence. Example with **Debezium + Postgres**:

```sql
-- Listening for changes on a table
CREATE TABLE sensor_alerts (
    event_id VARCHAR PRIMARY KEY,
    sensor_id VARCHAR,
    value DOUBLE,
    alert Boolean,
    processed_at TIMESTAMP
);

-- Debezium captures inserts/updates from Postgres and emits to Kafka
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Event Sourcing]**      | Store state changes as immutable event logs instead of snapshots.                | Audit trails, complex state management.          |
| **[CQRS]**                | Separate read and write models for scalability.                                  | High-write, low-read workloads.                 |
| **[Lambda Architecture]** | Combine batch (historical) and real-time (lambda) layers for analytics.          | Hybrid analytics pipelines.                     |
| **[Serverless Streaming]**| Use serverless functions (e.g., AWS Lambda + Kinesis) for event processing.    | Cost-sensitive, bursty workloads.                |
| **[Exactly-Once Processing]** | Ensure no duplicates in event processing with idempotent sinks.               | Financial transactions, critical data pipelines.|

---

## **Best Practices**
1. **Schema Management:**
   - Use **Confluent Schema Registry** or **Apicurio** to enforce schemas.
   - Tag schemas with versions (e.g., `sensor-v1.avsc`).

2. **Performance:**
   - **Batch small events** when possible (e.g., aggregate sensor readings every 500ms).
   - **Tune consumer lag** with `fetch.min.bytes` and `fetch.max.wait.ms`.

3. **Fault Tolerance:**
   - **Monitor offsets** (e.g., via `kafka-consumer-groups` CLI).
   - **Restart consumers gracefully** (avoid manual `kill -9`).

4. **Security:**
   - Enable **SASL/SSL** for broker communication.
   - **Mask sensitive fields** (e.g., PII) in event payloads.

5. **Testing:**
   - **Unit test producers/consumers** in isolation.
   - **End-to-end tests** with tools like **TestContainers** for Kafka.

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                                  | **Solution**                                      |
|------------------------------------|------------------------------------------------|---------------------------------------------------|
| **Consumer lag**                   | Slow processing or backpressure.               | Scale consumers or optimize queries.              |
| **Duplicate events**               | At-least-once delivery + non-idempotent sink.   | Add deduplication (e.g., `event_id` + DB upsert).  |
| **Schema errors**                  | Producer/consumer mismatch.                    | Validate schemas with `confluent schema-registry`.|
| **Partition imbalance**            | Uneven key distribution.                       | Redesign partition key or increase partitions.    |

---
## **Further Reading**
- [Kafka Documentation: Streams API](https://kafka.apache.org/documentation/streams/)
- [Confluent Blog: Streaming Patterns](https://www.confluent.io/blog/category/streaming-patterns/)
- [AWS Kinesis Developer Guide](https://docs.aws.amazon.com/streams/latest/dev/developerguide.html)