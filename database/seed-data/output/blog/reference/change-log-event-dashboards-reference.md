# **[Pattern] Real-Time Dashboards from CDC Reference Guide**

---

## **1. Overview**
The **Real-Time Dashboards from CDC (Change Data Capture)** pattern enables near-instantaneous data visualization by ingesting, processing, and streaming incremental changes (inserts, updates, deletes) from data sources via CDC. This pattern replaces traditional batch-oriented updates (e.g., ETL jobs) with event-driven pipelines, ensuring dashboards reflect the latest state of the data with minimal latency.

Ideal for:
- Financial dashboards tracking live transactions.
- IoT platforms visualizing real-time sensor metrics.
- Log aggregation systems monitoring application health.
- Real-time analytics on user behavior (e.g., e-commerce activity).

**Key Benefits:**
- **Sub-second latency** (vs. batch delays).
- **Scalable** (handles high-throughput CDC streams).
- **Cost-efficient** (avoids reprocessing full datasets).
- **Low operational overhead** (decoupled from source systems).

---

## **2. Core Components**
| **Component**          | **Description**                                                                                                                                                                                                 | **Technologies**                                                                             |
|------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **CDC Source**         | Captures transactional changes (inserts/updates/deletes) from databases or event logs.                                                                                                                  | Debezium, AWS DMS, Kafka Connect, Kafka Streams, Spark Structured Streaming                |
| **Stream Processing**  | Transforms/filters CDC data in real-time, enriches with context (e.g., aggregations), and routes to sinks.                                                                                                    | Kafka Streams, Flink, Spark Streaming, Kubernetes Stream Processing                       |
| **Storage Layer**      | Persists aggregated metrics or raw events for dashboard queries.                                                                                                                                         | Time-series DBs (InfluxDB, TimescaleDB), Data Lakes (S3, Delta Lake), OLAP (ClickHouse)      |
| **Cache Layer**        | Optimizes read performance for frequently accessed metrics (e.g., dashboards).                                                                                                                             | Redis, Memcached                                                                              |
| **Dashboard Engine**   | Renders real-time visualizations (e.g., charts, alerts) using live data streams.                                                                                                                         | Grafana, Superset, Apache Superset, Metabase, Tableau Server                               |
| **Monitoring**         | Tracks pipeline health, latency, and data quality.                                                                                                                                                   | Prometheus + Grafana, Datadog, ELK Stack                                                    |

---

## **3. Schema Reference**
### **3.1. CDC Source Schema (Example: PostgreSQL)**
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `source`           | String         | Identifies the table/source (e.g., `users`, `orders`).                                               | `users`                         |
| `operation`        | Enum           | Type of change: `insert`, `update`, `delete`.                                                       | `insert`                        |
| `timestamp`        | Timestamp      | When the change was captured (not necessarily when it happened in the source).                     | `2024-02-15T14:30:00Z`          |
| `payload`          | JSON           | Key-value pairs of the changed row.                                                                   | `{"id": "123", "name": "Alice"}`|
| `offset`           | String         | CDC-specific position marker (e.g., for replayability).                                             | `eyJyb2xlIjp7InBhc3N3b3JkIjoi...`|

---
*Note: Schema varies by CDC tool (e.g., Debezium’s Avro vs. Kafka’s JSON).*

---

### **3.2. Stream Processing Schema (Enriched Event)**
Transformed CDC data before storage/display:
| **Field**          | **Type**       | **Description**                                                                                     | **Example**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| `event_time`       | Timestamp      | Timestamp of the original source event (for exact ordering).                                         | `2024-02-15T14:29:45Z`          |
| `metric_name`      | String         | Aggregated metric (e.g., `user_signups`, `order_value`).                                             | `order_value`                    |
| `value`            | Double/Int     | Numeric result of aggregation (e.g., sum, count).                                                   | `150.00`                        |
| `dimensions`       | Object         | Filters for granularity (e.g., `region: "us"`).                                                     | `{"region": "us", "product": "X"}`|
| `window`           | String         | Time window for aggregations (e.g., `5_min`, `hourly`).                                              | `5_min`                         |

---

### **3.3. Dashboard Data Model (Optimized for Queries)**
| **Table**           | **Columns**                                                                                     | **Optimization**                                                                 |
|---------------------|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `real_time_metrics` | `metric_name`, `value`, `timestamp`, `dimensions` (JSON)                                        | Partitioned by `dimensions` for fast filtering.                                   |
| `aggregates`        | `metric_name`, `window`, `value`, `timestamp`, `aggregation` (e.g., `sum`, `avg`)           | Time-series partitioning (e.g., daily/weekly buckets).                           |

---

## **4. Query Examples**
### **4.1. Aggregating Order Values by Region (SQL-like)**
*Query real-time order sums by region using a time-series database (e.g., TimescaleDB):*
```sql
-- Aggregates order values in 5-minute windows
SELECT
  window_start,
  region,
  SUM(value) AS total_orders
FROM real_time_metrics
WHERE
  metric_name = 'order_value'
  AND window = '5_min'
  AND timestamp >= now() - interval '1 hour'
GROUP BY 1, 2
ORDER BY 1 DESC;
```

---
### **4.2. Stream Processing (Kafka Streams)**
*Java/Kafka Streams code to compute real-time counts:*
```java
StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> orders = builder.stream("orders-topic");

orders
  .filter((key, value) -> !value.equals("cancelled"))
  .mapValues(value -> "processed")
  .groupByKey()
  .count(Materialized.as("order-counts"))
  .toStream()
  .to("processed-orders-topic", Produced.with(Serdes.String(), Serdes.Long()));
```

---
### **4.3. Grafana Dashboard Query (InfluxDB)**
*Visualize live CPU usage metrics:*
```sql
from(bucket: "metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu_usage")
  |> filter(fn: (r) => r.host == "server-01")
  |> aggregateWindow(every: 10s, fn: mean)
```

---
### **4.4. Alerting (Prometheus)**
*Trigger an alert if order failures exceed threshold:*
```yaml
- alert: HighOrderFailures
  expr: rate(order_failures_total[5m]) > 10
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Order failures spiked to {{ $value }}"
```

---

## **5. Implementation Steps**
### **5.1. Phase 1: Configure CDC**
1. **Set up CDC source** (e.g., Debezium connector for PostgreSQL):
   ```yaml
   # Debezium MySQL connector config
   name: mysql-connector
   config:
     connector.class: io.debezium.connector.mysql.MySqlConnector
     database.hostname: db.example.com
     database.port: 3306
     database.user: user
     database.password: password
     database.server.id: 123
     database.server.name: db-server
   ```
2. **Deploy connector** to Kafka Connect.

---
### **5.2. Phase 2: Process Streams**
1. **Define stream topology** (e.g., Flink job):
   ```scala
   val env = StreamExecutionEnvironment.getExecutionEnvironment
   val stream: DataStream[OrderEvent] = env
     .addSource(new FlinkKafkaConsumer[OrderEvent]("orders", kafkaProps))
     .filter(_.status == "completed")

   stream
     .keyBy(_.region)
     .process(new OrderAggregator())
     .addSink(new InfluxSink())
   ```
2. **Test with backpressure handling** (e.g., buffered sinks).

---
### **5.3. Phase 3: Store & Serve**
1. **Write to time-series DB** (e.g., TimescaleDB):
   ```bash
   # Using TimescaleDB COPY command
   COPY INTO cpu_usage FROM '/tmp/stream_data.csv' WITH (FORMAT csv, HEADER true);
   ```
2. **Cache hot metrics** (e.g., Redis):
   ```bash
   # Populate Redis from stream
   redis-cli RPUSH metrics:order_count $(date +%s).123 42
   ```

---
### **5.4. Phase 4: Build Dashboard**
1. **Add data source to Grafana**:
   - **Type**: InfluxDB/ClickHouse.
   - **Database**: `metrics_db`.
   - **Access**: Token-based auth.
2. **Create panel** (e.g., live orders chart):
   - **Query**: `SELECT SUM(value) FROM "real_time_metrics" WHERE metric_name = 'order_value' GROUP BY time(5s)`.
   - **Visualization**: Line chart with alert thresholds.

---

## **6. Query Examples (Advanced)**
### **6.1. Windowed Aggregations (Spark)**
```scala
// Spark Structured Streaming: 30-minute rolling averages
val windowed = orders
  .withWatermark("eventTime", "10 minutes")
  .groupBy(
    window($"eventTime", "30 minutes"),
    $"region"
  )
  .avg("value")
  .writeStream
  .foreachBatch { (batchDF: DataFrame, batchId: Long) =>
    batchDF.write.parquet(s"output/avg_${batchId}")
  }.start()
```

---
### **6.2. Join Streams (Flink)**
*Join order events with customer profiles:*
```java
DataStream<OrderEvent> orders = ...;
DataStream<CustomerProfile> profiles = ...;

// Windowed join with 1-minute alignment
orders.keyBy(OrderEvent::getCustomerId)
  .intervalJoin(profiles.keyBy(CustomerProfile::getId))
    .between(Time.minutes(-1), Time.minutes(1))
    .process(new OrderProfileJoinFunction())
```

---

## **7. Performance Considerations**
| **Challenge**               | **Solution**                                                                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| High throughput             | Partition streams (e.g., by region) and scale consumers.                                                                                     |
| Late data                   | Use event-time watermarks and allowable lateness (e.g., 5 minutes).                                                                       |
| Dashboard lag                | Cache aggregated results (e.g., Redis) and pre-compute hot paths.                                                                          |
| Cost of time-series storage  | Compress old data (e.g., TimescaleDB’s hyperfunctions) or archive to cold storage (e.g., S3).                                                 |
| Schema evolution             | Use Avro/Protobuf for backward-compatible schemas or Kafka’s schema registry.                                                               |

---

## **8. Error Handling**
| **Issue**                  | **Mitigation**                                                                                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| CDC lag                    | Monitor `lag` metrics (e.g., Prometheus: `kafka_consumer_lag`) and scale consumers.                                                      |
| Schema drift               | Validate payloads with Avro/JSON Schema and fail fast.                                                                                    |
| Dashboard stale data       | Implement **stateful** components (e.g., Flink state backends) and **correctness checks** (e.g., data quality alerts).                   |
| Stream failure             | Use **exactly-once** semantics (e.g., Kafka transactions) and dead-letter queues for failed records.                                       |

---
*Example alert for CDC lag:*
```yaml
- alert: CdCLagHigh
  expr: kafka_consumer_lag > 1000
  for: 5m
  labels:
    severity: warning
```

---

## **9. Related Patterns**
| **Pattern**                     | **Use Case**                                                                                                                                 | **Connection to CDC Dashboards**                                                                 |
|----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Event Sourcing**              | Store state changes as immutable events (e.g., for audit trails).                                                                          | CDC can feed event-sourced streams into dashboards (e.g., user activity).                           |
| **Complex Event Processing (CEP)** | Detect patterns across streams (e.g., "3 failed logins in 5 minutes").                                                        | CEP can trigger alerts in real-time dashboards.                                                     |
| **Lambda Architecture**         | Blend real-time (stream) and batch (micro-batch) processing.                                                                      | CDC feeds the "lambda layer" for low-latency dashboards.                                          |
| **Serverless Stream Processing** | Run CDC pipelines on FaaS (e.g., AWS Lambda + Kinesis).                                                                              | Useful for sporadic workloads (e.g., IoT dashboards).                                             |
| **Data Mesh**                   | Decentralized data ownership with product-specific pipelines.                                                                          | Each "domain" team owns its CDC stream (e.g., `hr_events`, `finance_transactions`).               |

---
### **9.1. Anti-Patterns to Avoid**
- **Polling sources** (e.g., cron jobs): Use CDC for true real-time.
- **Blocking dashboard queries**: Always cache aggregated results.
- **Ignoring watermarks**: Can cause "late data" issues in aggregations.
- **Over-partitioning**: Leads to "small file" problems in storage.

---

## **10. Tools & Vendors**
| **Category**          | **Tools**                                                                                     | **Key Features**                                                                               |
|-----------------------|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **CDC**              | Debezium, AWS DMS, Debezium CDC, Oracle GoldenGate, Logstash JDBC                          | Database-specific connectors; schema evolution support.                                        |
| **Stream Processing**| Apache Flink, Kafka Streams, Spark Streaming, AWS Kinesis Data Analytics                    | Stateful processing, windowing, exactly-once semantics.                                       |
| **Dashboards**       | Grafana, Superset, Metabase, Tableau Server, Apache Superset                               | Plugins for SQL/NoSQL; alerting; collaboration.                                              |
| **Storage**          | TimescaleDB, InfluxDB, ClickHouse, Delta Lake, S3                                            | Time-series optimizations; query efficiency.                                                 |

---
*Example Grafana plugin for TimescaleDB:*
```bash
# Install TimescaleDB plugin in Grafana
grafana-cli plugins install timescaledb-app
```

---

## **11. Example Architecture Diagram**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │    │                 │
│   PostgreSQL    │───▶│   Debezium      │───▶│  Kafka Streams │───▶│ InfluxDB       │───▶│ Grafana
│                 │    │   (CDC)         │    │  (Flink)       │    │ (Time-series) │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
       ▲                                   ▲                              ▲
       │                                   │                              │
       └───────────────┬───────────────────┘                              │
                      │                                       ┌───────────▼───────────┐
                      ▼                                       │                   │
┌─────────────────┐    ┌─────────────────┐                     │   Redis          │
│                 │    │                 │                     │ (Cache)          │
│   Alert Manager │───▶│  Prometheus     │─────────────────────┘                   │
│                 │    │                 │                     │                   ▼
└─────────────────┘    └─────────────────┘                     │           ┌─────────────────┐
                                                             └───────────▶│   Superset       │
                                                                               │ (Dashboards)    │
                                                                               └─────────────────┘
```

---
**Key Labels:**
- **Dashed lines** = Control plane (e.g., monitoring).
- **Solid lines** = Data flow.
- **Dotted lines** = Optional (e.g., caching).

---

## **12. Troubleshooting**
| **Symptom**               | **Root Cause**                          | **Solution**                                                                                     |
|---------------------------|----------------------------------------|-------------------------------------------------------------------------------------------------|
| Dashboard lags source     | CDC lag or slow stream processing.     | Scale consumers; optimize Flink/Kafka partitions.                                               |
| Missing data in dashboards| Failed CDC capture or stream dropout.  | Check Kafka consumer lag; review Debezium connector logs.                                       |
| High storage costs        | Uncompressed raw events retained.      | Configure TTL (e.g., 7 days in Kafka) or archive to S3.                                         |
| Alerts fire incorrectly    | Watermark misconfiguration.            | Adjust `allowedLateness` in Flink/Spark to match SLA.                                           |
| Schema errors             | Backward-incompatible changes.         | Use Avro with schema registry (e.g., Confluent).                                                 |

---
*Example: Debugging CDC lag*
```bash
# Check Debezium connector lag
curl http://localhost:8083/connectors/mysql-connector/status
# Look for `tasks.n` and `records-lag-*` metrics.
```

---

## **13. Cost Optimization**
| **Area**               | **Optimization**                                                                                     | **Impact**                          |
|------------------------|------------------------------------------------------------------------------------------------------|-------------------------------------|
| **CDC**                | Use lightweight connectors (e.g., Debezium for PostgreSQL over MySQL).                              | Lower compute resources.            |
| **Stream Processing**  | Optimize window sizes (e.g., 5-min windows instead of 1-min).                                       | Reduced state storage.              |
| **Storage**            | Compress time-series data (e.g., TimescaleDB