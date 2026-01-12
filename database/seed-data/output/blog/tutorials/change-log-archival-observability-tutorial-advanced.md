```markdown
---
title: "Change Log Archival for Observability: How to Keep Your Data Alive Long-Term"
date: 2023-11-15
author: "Jane Doe"
description: "Learn how to implement the Change Log Archival pattern to maintain observability over long periods of time without sacrificing performance."
tags: ["database design", "api design", "observability", "data architecture", "backend engineering"]
---

# Change Log Archival for Observability: How to Keep Your Data Alive Long-Term

![Observability Data Over Time](https://images.unsplash.com/photo-1620712521881-df8d5d3de8c5?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80)

As systems grow more complex, the data they generate becomes increasingly critical—not just for immediate debugging, but for understanding long-term trends, forensic analysis, and compliance. Yet, traditional database and log systems face a fundamental challenge: **how to retain data long enough to be useful while keeping operational costs and performance impact low**. This is where the **Change Log Archival for Observability** pattern comes into play.

In this post, we’ll explore why traditional logging and change tracking fall short for long-term observability, how the Change Log Archival pattern addresses these gaps, and how you can implement it in your systems. We’ll walk through practical code examples using a mix of SQL, application code, and infrastructure configurations, while weighing the tradeoffs at each step.

---

## The Problem: Why Traditional Logging Lacks Long-Term Observability

Modern applications generate **volumes of data**—logs, database changes, API calls, and monitoring metrics. While short-term observability (e.g., troubleshooting a recent outage) is straightforward, **long-term observability**—such as analyzing data decay over weeks, months, or years—requires a different approach. Here’s why traditional solutions often fail:

### 1. **Performance and Storage Costs**
   - Most logging systems (e.g., ELK, Splunk, or even database transaction logs) are optimized for **hot data**: the most recent entries that need fast access.
   - Archiving older data to cheaper storage (e.g., S3, Snowflake) often breaks the **single query interface**—you end up with disparate systems for hot and cold data, complicating analysis.

   Example: A high-traffic e-commerce site may need to query:
   ```sql
   -- Today's orders (fast access)
   SELECT * FROM orders WHERE order_date > CURRENT_DATE - INTERVAL '1 day';

   -- Monthly trend analysis (slower, archived)
   SELECT AVG(price) FROM orders WHERE order_date >= '2023-01-01' GROUP BY MONTH(order_date);
   ```
   The second query might require joining multiple archived datasets, increasing complexity.

### 2. **Data Retention vs. Access Patterns**
   - Most applications **rarely query data older than 30–90 days** directly from production databases.
   - Yet, compliance or forensic investigations **require access to data for years**. Storing everything in the hot layer is prohibitively expensive, while dumping it to cold storage breaks usability.

### 3. **Inconsistent Data Models**
   - As systems evolve, schemas change. If you archive data as-is, **backward compatibility becomes a nightmare**:
     - New tables or columns may not exist in older archives.
     - Querying historical data requires complex transformations or ETL pipelines.

### 4. **No Built-In Observability**
   - Traditional logs are **event streams**, not designed for analytical queries. For example:
     - You can’t easily correlate a `POST /api/checkout` with a later `PUT /api/order/{id}` in logs alone.
     - Database change logs (e.g., PostgreSQL’s WAL) are **binary and non-human-readable** out of the box.

---

## The Solution: Change Log Archival for Observability

The **Change Log Archival** pattern addresses these challenges by:
1. **Decoupling hot and cold data**: Keeping recent data in a performant storage layer (e.g., PostgreSQL) and archiving older data to cheaper layers (e.g., S3, BigQuery) while ensuring queries can access both seamlessly.
2. **Standardizing data models**: Archiving data in a **flattened, schemaless (or semi-structured) format** that remains compatible with future schema changes.
3. **Enabling cross-layer queries**: Implementing a **unified query interface** so analysts can join hot and cold data without knowing where the data physically resides.
4. **Leveraging change data capture (CDC)**: Using tools like Debezium or logical decoding to capture **only the changes** (inserts/updates/deletes) rather than full tables, reducing storage and network overhead.

---

## Components of the Solution

Here’s how you can implement this pattern in a real-world scenario:

### 1. **Change Data Capture (CDC) Layer**
   Capture every change to your database in near real-time. Tools like:
   - **Debezium** (Kafka-based CDC)
   - **PostgreSQL logical decoding**
   - **Database-native CDC** (e.g., MySQL Binlog, Oracle Streams)

   Example using Debezium with Kafka:
   ```yaml
   # debezium-postgres-connector.properties
   name=postgres-connector
   connector.class=io.debezium.connector.postgresql.PostgresConnector
   database.hostname=postgres-db
   database.port=5432
   database.user=debezium
   database.password=dbpassword
   database.dbname=orders
   table.include.list=orders
   slot.name=debezium
   ```

### 2. **Hot Storage Layer**
   Store recent data (e.g., last 30 days) in a **high-performance OLTP database** (PostgreSQL, MySQL) for fast queries. Example schema:
   ```sql
   CREATE TABLE orders (
       id SERIAL PRIMARY KEY,
       user_id INT NOT NULL,
       amount DECIMAL(10, 2) NOT NULL,
       order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
       status VARCHAR(20) NOT NULL,
       -- Indexes for common query patterns
       INDEX idx_user_id (user_id),
       INDEX idx_order_date (order_date),
       INDEX idx_status (status)
   );
   ```

### 3. **Archival Storage Layer**
   Archive older data to a **cost-effective, scalable storage** (e.g., S3, BigQuery, Snowflake) in a **flattened, time-partitioned format**. Example:
   ```sql
   -- Partitioned table in Snowflake (simplified)
   CREATE TABLE orders_archive (
       id STRING,
       user_id STRING,
       amount STRING,
       order_date TIMESTAMP_NTZ,
       status STRING,
       _partition_date DATE
   )
   CLUSTER BY _partition_date
   PARTITION BY RANGE_BUCKET(order_date, GENERATOR(ROWCOUNT => 30));
   ```

   Or as JSON in S3:
   ```
   s3://orders-bucket/year=2023/month=01/day=15/
   ├── order_12345.json
   ├── order_67890.json
   ```

### 4. **Unified Query Interface**
   Use a **materialized view** or **ETL pipeline** to expose a single query surface. Tools like:
   - **dbt** (data build tool) for SQL-based transformations.
   - **Airflow** for orchestrating data movement.
   - **Custom application logic** to handle hot/cold data joins.

   Example with dbt (in `models/orders/db.yml`):
   ```yaml
   version: 2

   models:
     - name: orders_observability
       description: "Unified view for hot and cold orders data."
       columns:
         - name: id
           data_type: INTEGER
           tests:
             - not_null
   ```

### 5. **Observability Layer**
   Add metadata to logs and change events for correlation. Example:
   ```json
   {
     "event_type": "order_created",
     "trace_id": "abc123-456-def789",
     "order_id": 12345,
     "user_id": 9876,
     "amount": 99.99,
     "timestamp": "2023-11-15T12:00:00Z"
   }
   ```

---

## Practical Implementation Guide

Let’s walk through implementing this pattern for an e-commerce platform. We’ll use:
- **PostgreSQL** for hot storage.
- **Debezium + Kafka** for CDC.
- **Snowflake** for cold storage.
- **Python (FastAPI)** for the application layer.

---

### Step 1: Set Up CDC with Debezium
1. **Deploy Debezium connector** to capture changes from PostgreSQL:
   ```docker-compose.yml
   version: '3'
   services:
     zookeeper:
       image: confluentinc/cp-zookeeper:7.0.0
       environment:
         ZOOKEEPER_CLIENT_PORT: 2181
         ZOOKEEPER_TICK_TIME: 2000
     kafka:
       image: confluentinc/cp-kafka:7.0.0
       depends_on:
         - zookeeper
       ports:
         - 9092:9092
       environment:
         KAFKA_BROKER_ID: 1
         KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
         KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
         KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
     postgres:
       image: postgres:13
       environment:
         POSTGRES_DB: orders
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: postgres
       ports:
         - 5432:5432
     postgres-connector:
       image: debezium/connect:2.1
       depends_on:
         - kafka
         - postgres
       ports:
         - 8083:8083
       environment:
         GROUP_ID: 1
         CONFIG_STORAGE_TOPIC: connector_configs
         OFFSET_STORAGE_TOPIC: connector_offsets
         STATUS_STORAGE_TOPIC: connector_statuses
         BOOTSTRAP_SERVERS: kafka:9092
         CONNECT_REST_ADVERTISED_HOST_NAME: postgres-connector
   ```

2. **Run the connector** with the config from earlier. Verify it’s capturing changes:
   ```bash
   kafka-console-consumer --bootstrap-server localhost:9092 \
     --topic orders.orders \
     --from-beginning \
     --property print.key=true
   ```

---

### Step 2: Archive Data to Snowflake
1. **Set up a Snowflake table** with a schema compatible with your hot database:
   ```sql
   -- In Snowflake
   CREATE TABLE orders_archive (
       id BIGINT,
       user_id BIGINT,
       amount DECIMAL(10, 2),
       order_date TIMESTAMP_NTZ,
       status VARCHAR(20),
       _partition_date DATE
   )
   CLUSTER BY _partition_date;
   ```

2. **Write a Kafka consumer** (e.g., in Python) to ingest CDC events and load them into Snowflake:
   ```python
   # consumer.py
   from confluent_kafka import Consumer
   import snowflake.connector
   import json
   import os

   kafka_config = {
       'bootstrap.servers': 'localhost:9092',
       'group.id': 'snowflake-loader',
       'auto.offset.reset': 'earliest'
   }
   consumer = Consumer(kafka_config)
   consumer.subscribe(['orders.orders'])

   snowflake_conn = snowflake.connector.connect(
       user=os.getenv('SNOWFLAKE_USER'),
       password=os.getenv('SNOWFLAKE_PASSWORD'),
       account=os.getenv('SNOWFLAKE_ACCOUNT'),
       warehouse='COMPUTE_WH',
       database='OBSERVABILITY',
       schema='PUBLIC'
   )
   cursor = snowflake_conn.cursor()

   while True:
       msg = consumer.poll(1.0)
       if msg is None:
           continue
       if msg.error():
           print(f"Error: {msg.error()}")
           continue

       try:
           payload = json.loads(msg.value().decode('utf-8'))
           # Extract key fields; handle different event types (insert/update/delete)
           if payload['op'] == 'c':
               cursor.execute("""
                   INSERT INTO orders_archive (id, user_id, amount, order_date, status, _partition_date)
                   VALUES (%s, %s, %s, %s, %s, %s)
               """, (
                   payload['payload']['after']['id'],
                   payload['payload']['after']['user_id'],
                   payload['payload']['after']['amount'],
                   payload['payload']['after']['order_date'],
                   payload['payload']['after']['status'],
                   payload['payload']['after']['order_date'].date()
               ))
           elif payload['op'] == 'd':
               cursor.execute("""
                   DELETE FROM orders_archive
                   WHERE id = %s AND _partition_date = %s
               """, (
                   payload['payload']['before']['id'],
                   payload['payload']['before']['order_date'].date()
               ))
           snowflake_conn.commit()
       except Exception as e:
           print(f"Error processing message: {e}")
   ```

3. **Run the consumer** in a Kubernetes pod or serverless environment (e.g., AWS Lambda).

---

### Step 3: Implement a Unified Query Interface
1. **Create a materialized view** in Snowflake to join hot and cold data:
   ```sql
   CREATE OR REPLACE VIEW orders_unified AS
   SELECT
       id, user_id, amount, order_date, status,
       CASE
           WHEN order_date >= DATEADD('day', -30, CURRENT_TIMESTAMP()) THEN 'HOT'
           ELSE 'COLD'
       END AS storage_layer
   FROM orders_archive
   UNION ALL
   SELECT
       id, user_id, amount, order_date, status,
       'HOT' AS storage_layer
   FROM orders
   WHERE order_date >= DATEADD('day', -30, CURRENT_TIMESTAMP());
   ```

2. **Expose the view via an API** (FastAPI example):
   ```python
   # main.py
   from fastapi import FastAPI
   import snowflake.connector

   app = FastAPI()

   def get_snowflake_connection():
       conn = snowflake.connector.connect(
           user=os.getenv('SNOWFLAKE_USER'),
           password=os.getenv('SNOWFLAKE_PASSWORD'),
           account=os.getenv('SNOWFLAKE_ACCOUNT')
       )
       return conn.cursor()

   @app.get("/orders/trends")
   async def get_order_trends(period: str = "30d"):
       cursor = get_snowflake_connection()
       if period == "30d":
           query = """
               SELECT
                   DATE_TRUNC('month', order_date) AS month,
                   SUM(amount) AS total_amount,
                   COUNT(*) AS order_count
               FROM orders_unified
               WHERE order_date >= DATEADD('day', -30, CURRENT_TIMESTAMP())
               GROUP BY month
               ORDER BY month
           """
       else:
           query = """
               SELECT
                   DATE_TRUNC('month', order_date) AS month,
                   SUM(amount) AS total_amount,
                   COUNT(*) AS order_count
               FROM orders_unified
               WHERE order_date >= DATEADD('month', -12, CURRENT_TIMESTAMP())
               GROUP BY month
               ORDER BY month
           """
       cursor.execute(query)
       results = cursor.fetchall()
       return {"data": results}
   ```

---

### Step 4: Add Observability Metadata
1. **Extend your CDC events** to include trace IDs and correlation data:
   ```python
   # Modify the Debezium connector config to include additional fields
   "transforms": "unwrap,add-source-column",
   "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
   "transforms.unwrap.drop.tombstones": "false",
   "transforms.add-source-column.type": "org.apache.kafka.connect.transforms.RegexRouter",
   "transforms.add-source-column.regex": ".*",
   "transforms.add-source-column.replacement": "$1,$trace_id"
   ```

2. **Log application events** with correlation data:
   ```python
   # Example in a FastAPI endpoint
   from uuid import uuid4

   @app.post("/api/checkout")
   async def checkout(order_data: dict):
       trace_id = str(uuid4())
       # Log with trace context
       logger.info(
           f"Order processing started (trace_id={trace_id})",
           extra={
               "order_id": order_data["id"],
               "user_id": order_data["user_id"],
               "trace_id": trace_id
           }
       )
       # Process order...
   ```

---

## Common Mistakes to Avoid

1. **Ignoring Data Decay Patterns**
   - Not all data decays at the same rate. For example:
     - **Recent orders** (last 30 days) may need sub-second response times.
     - **Older orders** (years ago) may only need hourly refreshes.
   - **Mistake**: Using the same storage layer for everything without tiering.

2. **Overcomplicating the Schema**
   - Flattening data too much can make queries harder to write.
   - **Mistake**: Storing all JSON blobs in a single column without denormalizing for common queries.

3. **Skipping Backpressure Handling**
   - CDC pipelines can become overwhelmed during high-volume events (e.g., database migrations).
   - **Mistake**: Not implementing rate limiting or batching in your consumer.

4. **Neglecting Security**
   - Archival data may contain sensitive information (e.g., PII in old orders).
   - **Mistake**: Not applying encryption or tokenization before archiving.

5. **Assuming All Queries Are Equal**
   - Not all queries need to scan all archived data. For example:
     - Analyzing "top users by spend" may only need aggregations, not full joins.
   - **Mistake**: Designing a one-size-fits-all query interface without optimizing for common patterns.

---

## Key Takeaways

-