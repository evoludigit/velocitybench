---
title: "Real-Time Dashboards with CDC: Updating Your Analytics in Milliseconds"
date: "2023-11-15"
author: "Alex Carter"
---

# **Real-Time Dashboards with CDC: Updating Your Analytics in Milliseconds**

---

Imagine you’re running an e-commerce platform where customers make purchases every second. Your sales dashboard isn’t just a snapshot—it reflects real-time revenue, conversion rates, and user behavior as they happen. But what if your current analytics solution only updates every 5 minutes? Customers (and investors) won’t wait.

This is the problem **Change Data Capture (CDC)** solves. CDC streams database changes in **real time**, enabling dashboards, alerts, and analytics to reflect the latest state of your data—without requiring batch jobs or polling. In this tutorial, we’ll explore how to build a real-time dashboard using CDC, covering:

- **The problem** with traditional dashboard updates and why CDC is the solution
- **Key components** of a CDC-powered real-time system
- **Practical implementations** using Kafka, Debezium, and a sample Python dashboard
- **Tradeoffs** and common pitfalls
- **A step-by-step guide** to setting up your own CDC pipeline

---

## **The Problem: Why Real-Time Dashboards Matter**

Most dashboards—even those labeled "real-time"—are only as real as the last batch job. Traditional approaches rely on:
1. **Periodic polling**: Your backend fetches data from the database at fixed intervals (e.g., every 1–5 minutes).
2. **Batch processing**: NoSQL databases like MongoDB and Cassandra use occasional writes and batch exports for analytics.
3. **Scheduled cron jobs**: Aggregations are precomputed and refreshed hourly/daily.

These methods introduce **latency**—customers see stale data, and you miss crucial insights. Worse, they create **discrepancies** between operational data (e.g., orders) and analytics data (e.g., revenue dashboards).

### **Example: The $100K Stakeholder Miscommunication**
A retail company’s dashboard showed **$5M in daily sales** (based on a 10-minute delay), while their real-time support system flagged **$100K in fraudulent transactions** that weren’t reflected. The gap? **A reliance on batch updates**.

Real-time dashboards ensure **operational data and analytics stay consistent**. With CDC, every order, login, or customer action triggers an immediate update to your dashboard.

---

## **The Solution: Real-Time Dashboards with CDC**

CDC captures **every change** to a database (inserts, updates, deletes) and streams them to a consumer (e.g., Kafka, a real-time dashboard). Here’s how it works:

1. **CDC Agent**: Monitors a database (PostgreSQL, MySQL, MongoDB) for changes.
2. **Event Stream**: Changes are published to a **message queue** (e.g., Kafka, RabbitMQ).
3. **Consumer**: A dashboard service subscribes to the stream and updates in real time.

The result? **No polling, no batch lag, just instant visibility**.

---

## **Key Components of a CDC-Powered Dashboard**

| **Component**       | **Purpose**                                                                 | **Example Tools**                     |
|----------------------|-----------------------------------------------------------------------------|----------------------------------------|
| **Database**         | Source of truth for business data                                         | PostgreSQL, MySQL, MongoDB             |
| **CDC Agent**        | Captures and streams database changes                                     | Debezium, AWS DMS, Logstash            |
| **Event Stream**     | Buffers and publishes changes to consumers                                | Apache Kafka, RabbitMQ, AWS Kinesis     |
| **Dashboard**        | Consumes streamed events and renders real-time metrics                    | Python (FastAPI + Streamlit), React   |
| **Aggregation Layer**| (Optional) Pre-computes metrics for performance (e.g., 10-second averages)| Apache Flink, Spark Streaming          |

---

## **Code Example: Real-Time Sales Dashboard with Debezium and Kafka**

Let’s build a **real-time sales dashboard** that updates whenever a new order is placed.

### **1. Set Up Debezium to Capture Changes**
Debezium is an open-source CDC tool that streams PostgreSQL/MySQL changes to Kafka.

#### **Install PostgreSQL and Enable CDC**
```sql
-- Enable CDC in PostgreSQL (PostgreSQL 10+)
ALTER TABLE sales.order SET (logseq = 'ON');
```

#### **Start Debezium Connect with Kafka**
Run a Kafka Connect worker with the PostgreSQL connector:
```yaml
# debezium-postgres-connector.yaml
name: postgres-connector
config:
  connector.class: io.debezium.connector.postgresql.PostgresConnector
  database.hostname: localhost
  database.port: 5432
  database.user: debezium
  database.password: debezium
  database.dbname: sales
  topic.prefix: sales
  plugin.name: pgoutput
  schema.include.list: order,product
  slot.name: sales_slot
```

### **2. Publish Changes to Kafka**
When a new order is created:
```sql
-- Insert a new order
INSERT INTO sales.order (order_id, user_id, product_id, amount)
VALUES (123, 10, 1001, 99.99);
```
Debezium captures this change and emits a JSON event to Kafka:
```json
{
  "schema": "public.sales.order",
  "op": "c",
  "key": {"user_id": 10, "order_id": 123},
  "value": {
    "order_id": 123,
    "user_id": 10,
    "product_id": 1001,
    "amount": 99.99
  }
}
```

### **3. Consume Events in Python (FastAPI + Streamlit)**
We’ll build a **real-time dashboard** using:
- **Kafka** (via `confluent-kafka-python`)
- **FastAPI** (to serve the dashboard)
- **Streamlit** (for the UI)

#### **Install Dependencies**
```bash
pip install confluent-kafka streamlit fastapi uvicorn python-multipart
```

#### **Kafka Consumer (consumer.py)**
```python
from confluent_kafka import Consumer
import json

def consume_orders():
    conf = {
        'bootstrap.servers': 'localhost:9092',
        'group.id': 'dashboard-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)
    consumer.subscribe(['sales.sales.order'])

    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Error: {msg.error()}")
            continue

        event = json.loads(msg.value().decode('utf-8'))
        print(f"New order: {event['value']}")

        # Update dashboard data (simplified for demo)
        update_dashboard(event['value'])

if __name__ == "__main__":
    consume_orders()
```

#### **FastAPI Dashboard (dashboard.py)**
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import streamlit as st
import requests

app = FastAPI()

# Mock data store (in real apps, use Redis or a database)
order_data = []

@app.get("/")
def read_root():
    st.title("Real-Time Sales Dashboard")
    st.subheader(f"Total Sales: ${sum([order['amount'] for order in order_data]):.2f}")

    for order in order_data:
        st.markdown(f"- Order #{order['order_id']}: **${order['amount']:.2f}** by User {order['user_id']}")
    return {"status": "Dashboard running"}

# Simulate update_dashboard (pseudo-code)
def update_dashboard(order):
    order_data.append(order)  # In practice, append to Redis or DB
```

#### **Run the Dashboard**
```bash
uvicorn dashboard:app --reload
streamlit run dashboard.py
```

Now, whenever a new order is placed, **Debezium streams the change to Kafka**, and our dashboard updates **instantly**.

---

## **Implementation Guide: Step-by-Step**

### **1. Choose Your CDC Tool**
| **Tool**          | **Best For**                          | **Pros**                          | **Cons**                          |
|--------------------|---------------------------------------|-----------------------------------|-----------------------------------|
| **Debezium**       | PostgreSQL, MySQL, MongoDB            | Open-source, plugin-based         | Requires Kafka setup              |
| **AWS DMS**        | AWS-native CDC                       | Managed, scalable                  | Expensive                          |
| **Logstash**       | Elasticsearch pipelines                | Integrates with ELK stack         | Overkill for simple dashboards     |

### **2. Set Up Kafka**
If you don’t have Kafka, use:
- **Confluent Cloud** (fully managed)
- **Local Kafka** (for testing):
  ```bash
  docker-compose up -d zookeeper kafka
  ```

### **3. Configure the CDC Pipeline**
1. **Enable CDC in your database** (Debezium-specific config).
2. **Start the Kafka Connect worker** with the Debezium connector.
3. **Verify events are streaming** to Kafka:
   ```bash
   kafka-console-consumer --bootstrap-server localhost:9092 --topic sales.sales.order --from-beginning
   ```

### **4. Build the Dashboard**
- **Option A**: Use **Streamlit** (for simple dashboards).
- **Option B**: Use **React + Kafka** (for scalable apps).
- **Option C**: Use **Elasticsearch + Kibana** (for advanced analytics).

### **5. Optimize for Performance**
- **Batch small events** (e.g., combine 100 orders into one update).
- **Use Kafka topics per entity** (e.g., `orders`, `users`, `products`).
- **Cache aggregations** (e.g., "total sales last 5 minutes") in Redis.

---

## **Common Mistakes to Avoid**

1. **Ignoring Event Ordering**
   - Kafka messages aren’t guaranteed to arrive in order. Use `key` fields (e.g., `order_id`) to ensure correct sequencing.

2. **Not Handling Duplicates**
   - Kafka can replay messages. Implement **idempotent consumers** (e.g., track processed messages in a DB).

3. **Overloading the Dashboard**
   - Streaming **every change** can overwhelm the UI. Use **exponential backoff** or **rate-limiting**.

4. **Tight Coupling to Kafka**
   - If Kafka goes down, your dashboard fails. Use **dead-letter queues (DLQ)** for failed events.

5. **Forgetting Schema Evolution**
   - Database schemas change. Use **Avro/Protobuf** for backward-compatible event schemas.

---

## **Key Takeaways**

✅ **Real-time dashboards reduce latency**—no more "almost real-time" delays.
✅ **CDC decouples data sources** from consumers (e.g., dashboards can be updated without database changes).
✅ **Kafka is the backbone**—it buffers, scales, and ensures reliability.
✅ **Start small**—begin with a single CDC stream (e.g., orders) before expanding.
⚠ **Tradeoffs exist**:
   - **Complexity**: CDC requires Kafka, connectors, and monitoring.
   - **Cost**: Managed CDC (AWS DMS) adds expenses.
   - **Performance**: Over-fetching events can slow your dashboard.

---

## **Conclusion: When to Use CDC for Dashboards**

CDC is **ideal** when:
- You need **real-time metrics** (e.g., live sports analytics, trading platforms).
- Your analytics depend on **operational data** (e.g., fraud detection, A/B testing).
- You want to **avoid batch processing** (e.g., no daily nightly reports).

But if you’re only building a **static dashboard** that updates hourly, CDC may be **overkill**.

### **Next Steps**
1. **Try it yourself**: Spin up Kafka, PostgreSQL, and Debezium in Docker.
2. **Experiment with aggregations**: Use Kafka Streams or Spark to precompute metrics.
3. **Explore managed options**: AWS Kinesis Data Streams or Google Pub/Sub for production.

Real-time dashboards don’t have to be a black box. With CDC, you can **turn your data into a live, actionable stream**—enabling faster decisions, happier customers, and more data-driven confidence.

---

**Want a deeper dive?** Check out our follow-up on [scaling CDC at high throughput](link-to-next-post) or [handling schema changes in real-time systems](link-to-next-post).

---
**Alex Carter** is a backend engineer specializing in real-time systems and distributed data pipelines. He’s built CDC-powered dashboards for fintech and e-commerce platforms. Connect on [LinkedIn](https://linkedin.com/in/alexcarterdev).