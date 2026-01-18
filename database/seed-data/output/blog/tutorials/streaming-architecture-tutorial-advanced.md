```markdown
---
title: "Real-Time Streaming Data Architecture: Building Event-Driven Systems at Scale"
date: 2023-11-15
author: "Alexei Kovalev"
description: "Learn how to design and implement real-time streaming architectures with Apache Kafka, Pulsar, and cloud services. Practical code examples, tradeoffs, and anti-patterns included."
tags: ["backend", "distributed-systems", "kafka", "pulsar", "real-time", "data-pipelines"]
---

# Real-Time Streaming Data Architecture: Building Event-Driven Systems at Scale

![Streaming Architecture Diagram](https://storage.googleapis.com/kddx-docs/real-time-streaming-architecture.png)

Modern applications increasingly demand real-time reactions—whether it's updating user dashboards, processing financial transactions, or enabling interactive IoT devices. Traditional batch processing can't keep up. **Real-time streaming architectures** address this by ingesting, processing, and acting on data as it happens, not in scheduled batches. This pattern shifts your system from a pipeline (`start → transform → load`) to a **stream** (`produce → process → consume`), unlocking unprecedented agility and responsiveness.

But real-time systems come with complexity. You're no longer dealing with static datasets; you're managing infinite, ordered sequences of records where latency, throughput, and exactly-once semantics are non-negotiable. This post dives into the core components of streaming architectures, tradeoffs to consider, and practical implementations using **Apache Kafka**, **Apache Pulsar**, and cloud-native solutions like AWS Kinesis.

Let's build a production-ready streaming pipeline from scratch.

---

## **The Problem: Why Batch Processing Falls Short**

Before streaming, most applications relied on **batch processing**:
- **Scheduled jobs** (e.g., nightly ETL) process data periodically.
- **Decoupling** happens via files (CSV, JSON) or message queues (e.g., RabbitMQ).
- **State** is maintained in databases or caches.

### **The Symptoms of Batch Limitations**
1. **Latency is Unpredictable**
   - A financial transaction processed in a 6-hour batch might not reflect in a customer’s dashboard until the next day.
   - Example: A ride-hailing app’s "driver availability" updates only after a batch job runs.

2. **Real-Time Requirements Are Impossible**
   - Use cases like fraud detection, live analytics, or IoT telemetry require **sub-second processing**.
   - Example: A stock trading bot needs to react to market changes immediately, not after a 10-minute batch.

3. **Complexity Scales Poorly**
   - Batch systems often use **file-based synchronization**, leading to:
     ```bash
     # Pseudocode for a batch "ETL" process
     for file in /var/data/transactions/*.json:
         process_file(file)
         if error:
             retry(file, max_attempts=3)
         else:
             move_to_processed(file)
     ```
   - This becomes a **tight coupling** nightmare when files are corrupted, delayed, or out of order.

4. **Eventual Consistency is Accepted (But Not Ideal)**
   - Batch systems often rely on **eventual consistency** (e.g., database triggers that run asynchronously).
   - Example: A user’s "last active" timestamp updates in real-time via a stream, but their dashboard shows stale data until the next batch.

### **When You Need Streaming**
Use streaming when:
✅ You need **sub-second latency** (e.g., fraud alerts, live notifications).
✅ Your data is **unbounded and continuous** (e.g., IoT sensors, clickstreams).
✅ You’re building **event-driven architectures** (e.g., microservices reacting to changes).
✅ You need **exactly-once processing** (no duplicates, no missed records).

---

## **The Solution: Real-Time Streaming Architecture**

A typical streaming pipeline consists of **three core layers**:

1. **Ingestion Layer**: Collects and buffers raw events (producers).
2. **Processing Layer**: Filters, transforms, and aggregates streams (consumers).
3. **Storage/Consumption Layer**: Stores results for persistence or real-time queries.

### **Architecture Overview**
```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   ┌──────────┐    ┌─────────────┐    ┌───────────────────┐    ┌───────────┐   │
│   │          │    │             │    │                   │    │           │   │
│   │  Producer │───▶│  Kafka      │───▶│  Stream Processor │───▶│  Consumer │   │
│   │          │    │  Cluster    │    │                   │    │           │   │
│   └──────────┘    └─────────────┘    └───────────────────┘    └───────────┘   │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
       ▲                   ▲                   ▲                   ▲
       │                   │                   │                   │
┌──────┴─────┐ ┌───────────┴─────┐ ┌───────────┴─────┐ ┌───────────┴─────┐
│  IoT Devices │ │ Web/Mobile Apps │ │ Event Sources  │ │ Analytics DB   │
│              │ │                 │ │ (e.g., Click     │ │ (e.g., Elastic│
└──────────────┘ └─────────────────┘ │   Housekeeping)  │ └───────────────┘
                                    └─────────────────────┘
```

---

## **Code-First Implementation Guide**

### **1. Choosing a Streaming Platform**
| **Option**       | **Best For**                          | **Pros**                                  | **Cons**                                  |
|------------------|---------------------------------------|-------------------------------------------|-------------------------------------------|
| **Apache Kafka** | High-throughput, fault-tolerant      | Mature, scalable, rich tooling            | Complex setup, operational overhead      |
| **Apache Pulsar**| Multi-tenancy, geo-distributed        | Unified pub/sub + messaging              | Smaller ecosystem                         |
| **AWS Kinesis**  | Serverless, managed                  | Easy to deploy, integrations with AWS   | Vendor lock-in, cost at scale            |

For this tutorial, we’ll use **Apache Kafka** (the most widely adopted) with **Confluent Schema Registry** for schema evolution.

---

### **2. Setting Up a Kafka Producer (Event Generation)**
Producers publish events to Kafka topics. Let’s simulate a **user clickstream** (e.g., a user clicking a button on a webpage).

#### **Prerequisites**
- Install [Confluent Platform](https://www.confluent.io/download/) (includes Kafka, Schema Registry).
- Run `kafka-server-start.sh config/server.properties` (default port: 9092).

#### **Code: Kafka Producer (Python)**
```python
# producer.py
from confluent_kafka import Producer
import json
import time
import uuid

# Kafka configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
}
producer = Producer(conf)

# Define the topic and schema
topic = 'clickstream'
schema = {
    "type": "record",
    "name": "ClickEvent",
    "fields": [
        {"name": "user_id", "type": "string"},
        {"name": "timestamp", "type": "string"},
        {"name": "event_type", "type": "string"},
        {"name": "metadata", "type": "string"}  # e.g., JSON object
    ]
}

def delivery_report(err, msg):
    """Callback for message delivery."""
    if err:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def generate_click_event():
    """Simulate a click event."""
    return {
        "user_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "event_type": "button_click",
        "metadata": json.dumps({
            "button_name": "subscribe",
            "page_url": "https://example.com/pricing"
        })
    }

# Publish events
for i in range(10):
    event = generate_click_event()
    producer.produce(
        topic=topic,
        key=str(event["user_id"]),
        value=json.dumps(event),
        callback=delivery_report
    )
    producer.poll(0)  # Trigger delivery
    time.sleep(0.5)   # Simulate real-world delay

producer.flush()
```

#### **Key Producer Concepts**
- **Topic**: A logical channel for events (e.g., `clickstream`).
- **Partitioning**: Kafka partitions topics into segments for parallelism.
- **Key**: Determines partition assignment (critical for ordering).
- **Schema Registry**: Ensures producers/consumers agree on event structure.

Run the producer:
```bash
python3 producer.py
```
You should see messages like:
```
Message delivered to clickstream [0]
```

---

### **3. Setting Up a Kafka Consumer (Stream Processing)**
Consumers subscribe to topics and process events. Let’s build a **simple aggregator** that counts button clicks per user.

#### **Code: Kafka Consumer (Python)**
```python
# consumer.py
from confluent_kafka import Consumer
import json
from collections import defaultdict

# Kafka configuration
conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'click-analyzer',
    'auto.offset.reset': 'earliest'  # Start from beginning if no offset
}
consumer = Consumer(conf)

# Subscribe to the topic
consumer.subscribe(['clickstream'])

# Track click counts per user
click_counts = defaultdict(int)

def process_event(event):
    """Process a single click event."""
    data = json.loads(event.value().decode('utf-8'))
    click_counts[data["user_id"]] += 1
    print(f"User {data['user_id']} clicked: {click_counts[data['user_id']]}")

# Poll for messages
try:
    while True:
        msg = consumer.poll(1.0)  # Wait 1 second
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        process_event(msg)
        consumer.commit()  # Acknowledge processed message
except KeyboardInterrupt:
    print("Shutting down consumer...")
finally:
    consumer.close()
```

#### **Key Consumer Concepts**
- **Consumer Group**: Multiple consumers can work together (scalability).
- **Offsets**: Track progress in the stream (committed vs. unacknowledged).
- **At-Least-Once Processing**: By default, Kafka ensures no message is lost.
- **Exactly-Once Semantics**: Requires transactional writes (see [Kafka docs](https://kafka.apache.org/documentation/#transactional)).

Run the consumer in a separate terminal:
```bash
python3 consumer.py
```
You’ll see output like:
```
User 550e8400-e29b-41d4-a716-446655440000 clicked: 1
User 550e8400-e29b-41d4-a716-446655440001 clicked: 2
```

---

### **4. Adding a Stream Processor (Kafka Streams)**
For more complex logic (e.g., windowed aggregations), use **Kafka Streams**. Let’s count clicks per **5-minute window**.

#### **Code: Kafka Streams Aggregator**
```python
# stream_processor.py
from confluent_kafka import KafkaAdminClient, KafkaException
from confluent_kafka.admin import NewTopic
import json
from kafka_streams import KafkaStreams, StreamsConfig
from kafka_streams.topology import StreamTopology, ValueMapper, SinkRecord, JoinWindows, Materialized
from kafka_streams.kstream import (
    ConsumerFunction, KStream, KTable,
    TimeWindowed, Windowed,
    Aggregator, Aggregators, Join
)
from kafka_streams.processor import ProcessorContext

# Kafka configuration
admin_conf = {'bootstrap.servers': 'localhost:9092'}
kafka_admin = KafkaAdminClient(admin_conf)

# Create a topic for results (if it doesn’t exist)
try:
    topic = NewTopic('click_counts', num_partitions=1, replication_factor=1)
    kafka_admin.create_topics([topic])
except KafkaException as e:
    print(f"Topic may already exist: {e}")

# Define the topology
topology = StreamTopology()

def value_to_click(event: bytes) -> dict:
    """Convert Kafka value to click event dict."""
    return json.loads(event.decode('utf-8'))

# Step 1: Create a KStream from the clickstream topic
click_stream = topology.stream(
    'clickstream',
    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
    key_serializer=lambda x: x.encode('utf-8')
)

# Step 2: Parse the JSON value
parsed_stream = click_stream.map_values(value_to_click)

# Step 3: Aggregate counts per user in 5-minute windows
windowed_counts = parsed_stream.groupby(
    key=lambda record: record["user_id"]
).windowedby(
    TimeWindowed.withSizeDur(5 * 60 * 1000),  # 5-minute window
    name="user-window"
).aggregate(
    aggregator=Aggregators.count(),
    initializer=lambda _: 0,
    name="count-aggregator"
)

# Step 4: Store results in a new topic
windowed_counts.to_streams(
    'click_counts',
    serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Build and launch the streams app
streams_config = {
    'bootstrap.servers': 'localhost:9092',
    'application.id': 'click-analyzer',
    'value.serializer': lambda x: json.dumps(x).encode('utf-8'),
    'key.serializer': lambda x: x.encode('utf-8')
}

streams = KafkaStreams(topology, streams_config)
streams.start()
```

#### **Key Kafka Streams Concepts**
- **DStreams vs. KTables**:
  - `KStream`: Infinite sequences of records (like a SQL `SELECT * FROM events`).
  - `KTable`: Mutable key-value store (like a SQL `VIEW` with windowed aggregations).
- **Windows**: Time-based (`TimeWindowed`) or tumbling/sliding windows.
- **Joins**: Correlate streams (e.g., join user clicks with their profiles).

Run the processor:
```bash
python3 stream_processor.py
```

---

### **5. Consuming Results (Real-Time Dashboard)**
Now, let’s consume the aggregated counts to simulate a **real-time dashboard**.

#### **Code: Dashboard Consumer**
```python
# dashboard_consumer.py
from confluent_kafka import Consumer
import json
from collections import defaultdict

conf = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'dashboard',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(conf)
consumer.subscribe(['click_counts'])

# Store windowed results
windowed_counts = defaultdict(dict)

def print_dashboard():
    """Print current dashboard state."""
    print("\n=== Dashboard ===")
    for user_id, windows in windowed_counts.items():
        for window_end, count in windows.items():
            print(f"User {user_id[:8]}...: {count} clicks in window ending {window_end}")

try:
    while True:
        msg = consumer.poll(1.0)
        if not msg:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        data = json.loads(msg.value().decode('utf-8'))
        key = data["key"].decode('utf-8')  # Format: "user_id#window_end"
        user_id, window_end = key.split('#')
        value = data["value"]
        windowed_counts[user_id][window_end] = value
        print_dashboard()

except KeyboardInterrupt:
    print("Exiting dashboard...")
finally:
    consumer.close()
```

Run it:
```bash
python3 dashboard_consumer.py
```
Output:
```
=== Dashboard ===
User 550e8...: 3 clicks in window ending 1699879400000
User 660e8...: 1 clicks in window ending 1699879400000
```

---

## **Implementation Guide: Key Considerations**

### **1. Choosing Between Kafka and Pulsar**
| **Decision Point**       | **Kafka**                          | **Pulsar**                          |
|--------------------------|-------------------------------------|-------------------------------------|
| **Multi-tenancy**        | Manual (e.g., tenancy plugins)     | Built-in (tenant + namespace)       |
| **Geo-Replication**      | Requires MirrorMaker                 | Native support                      |
| **Schema Management**    | Schema Registry (Avro/Protobuf)     | Native schema caching               |
| **Latency**              | ~1ms (ideal for high throughput)   | ~2ms (slightly higher overhead)     |

**Use Kafka** if:
- You need **highest throughput** (millions of messages/sec).
- You’re already using **Confluent Cloud** or tools like **Debezium**.

**Use Pulsar** if:
- You need **multi-region deployments** with low latency.
- You want **unified pub/sub + messaging** (e.g., async RPC).

---

### **2. Partitioning Strategy**
- **Too few partitions**: Bottlenecks (consumers blocked on one partition).
- **Too many partitions**: Overhead (Zookeeper/Kafka broker load).

**Rule of Thumb**:
- Start with **3–6 partitions** per topic.
- Scale based on **consumer throughput** (e.g., 1 partition per consumer).

Example:
```bash
# Increase partitions for a topic
kafka-topics --bootstrap-server localhost:9092 \
    --alter --topic clickstream --partitions 6
```

---

### **3. Exactly-Once Processing**
Kafka guarantees **at-least-once** by default. For **exactly-once**:
1. **Enable transactions**:
   ```python
   producer = Producer({
       'bootstrap.servers': 'localhost:9092',
       'transactional.id': 'produ