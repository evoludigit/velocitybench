# **[Pattern] CDC Real-Time Metrics Reference Guide**

---

## **1. Overview**
The **CDC Real-Time Metrics** pattern enables real-time monitoring and analysis of system changes by leveraging **Change Data Capture (CDC)** to stream metric updates from transactional databases (e.g., PostgreSQL, MySQL, Kafka Connect) to a processing layer (e.g., **Flink, Spark Streaming, or a metric aggregator like Prometheus**). This pattern ensures low-latency insights into critical business events (e.g., transaction volumes, user activity, or system health) without polling.

Key use cases include:
- **Fraud detection** (real-time anomaly scoring)
- **Operational dashboards** (live KPIs)
- **A/B testing** (split-test result tracking)
- **Event-driven architectures** (reacting to state changes)

Unlike traditional batch processing, CDC Real-Time Metrics provides **sub-second latency**, making it ideal for **high-velocity data pipelines**.

---

## **2. Implementation Details**

### **2.1 Core Components**
| Component               | Description                                                                                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **CDC Source**          | Captures changes (inserts/updates/deletes) from a database (e.g., Debezium, AWS DMS, or PostgreSQL logical decoding).                     |
| **Stream Processor**    | Processes changes in real-time (e.g., **Apache Flink**, **Spark Structured Streaming**). Filters, aggregates, or enriches metrics.         |
| **Metric Layer**        | Stores metrics for querying (e.g., **Prometheus**, **InfluxDB**, **TimescaleDB**). Stores time-series data optimized for fast reads.       |
| **Sink/Destination**    | Routes processed metrics to dashboards (Grafana), alerting systems, or other applications.                                                   |
| **Schema Registry**     | Maintains Avro/Protobuf schemas for CDC event data and metrics (optional but recommended for evolution).                                     |

---

### **2.2 Key Data Flows**
1. **CDC Capture**:
   - Database writes trigger CDC events (e.g., `user:created`, `order:shipped`).
   - Example payload:
     ```json
     {
       "before": null,  // For inserts
       "after":  {"id": "123", "value": 42},
       "op": "insert",
       "ts_ms": 1712345678901
     }
     ```

2. **Stream Processing**:
   - Filter irrelevant events (e.g., ignore `op: "delete"`).
   - Aggregate metrics (e.g., count orders per hour, calculate rolling averages).

3. **Metric Storage**:
   - Write processed metrics to a time-series database with tags (e.g., `service=user_service`, `metric=transaction_count`).

4. **Consumption**:
   - Query metrics via PromQL (`rate(user_transactions_total[5m])`) or Grafana dashboards.

---

### **2.3 Tradeoffs**
| **Pros**                          | **Cons**                                  |
|-----------------------------------|-------------------------------------------|
| Near real-time (seconds)          | Higher operational complexity (CDC + stream processing). |
| Scales horizontally (Flink/Spark). | Requires schema management for evolution. |
| Reduces polling overhead.         | Eventual consistency (no immediate sync). |

---

## **3. Schema Reference**

### **3.1 CDC Event Schema (Avro/Protobuf Example)**
| Field           | Type               | Description                                                                 |
|-----------------|--------------------|-----------------------------------------------------------------------------|
| `source`        | String             | Database/table name (e.g., `orders`).                                        |
| `after`         | Object             | Post-change row data (JSON).                                                |
| `before`        | Object (optional)  | Pre-change row data (for updates/deletes).                                  |
| `op`            | String             | `"insert"`, `"update"`, or `"delete"`.                                       |
| `ts_ms`         | Long               | Unix timestamp in milliseconds (UTC).                                       |
| `transaction_id`| String (optional)  | Correlates events in distributed transactions.                                |

**Example (JSON):**
```json
{
  "source": "orders",
  "op": "insert",
  "ts_ms": 1712345678901,
  "after": {"order_id": "abc123", "amount": 99.99, "user_id": "user456"}
}
```

---

### **3.2 Metric Schema (Prometheus/InfluxDB)**
Metrics follow a **time-series format** with labels:

| Field       | Type    | Description                                                                 |
|-------------|---------|-----------------------------------------------------------------------------|
| `timestamp` | ISO8601 | When the metric was recorded (e.g., `2024-04-01T12:00:00Z`).               |
| `metric`    | String  | Name (e.g., `transaction_count`, `latency_p99`).                             |
| `value`     | Float   | Numeric value (e.g., `42.0`).                                               |
| `tags`      | Object  | Key-value pairs for filtering (e.g., `service="checkout", region="us-west"`).|

**Example (PromQL-compatible):**
```plaintext
transaction_count{service="checkout", region="us-west"} 42 1712345678
```

---

## **4. Query Examples**

### **4.1 PromQL (Prometheus)**
**A. Real-time transaction rate:**
```sql
rate(transaction_count_total[5m])
```
**B. Percentile latency (99th):**
```sql
histogram_quantile(0.99, sum(rate(api_request_duration_seconds_bucket[5m])) by (le))
```
**C. Filter by tags:**
```sql
sum(active_users) by (region) where region="eu-central"
```

---

### **4.2 InfluxDB (Flux)**
**A. Aggregate hourly orders:**
```sql
from(bucket: "metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "orders")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

**B. Alert on spike:**
```sql
from(bucket: "metrics")
  |> filter(fn: (r) => r._measurement == "error_rate")
  |> filter(fn: (r) => r._field == "value")
  |> > 0.01  // Threshold
```

---

### **4.3 Grafana Variables (Dynamic Dashboards)**
Use PromQL variables to auto-update regions/services:
```plaintext
$__interval:auto
$region: us-west,eu-central,ap-southeast
```
**Variable query:**
```sql
label_values(transaction_count, region)
```

---

## **5. Implementation Steps**

### **5.1 Setup CDC**
**Option 1: Debezium (Kafka Connector)**
```bash
# Start Debezium connector for PostgreSQL
docker run -d --name debezium-connector \
  -e CONNECTOR_CLASS=io.debezium.connector.postgresql.PostgresConnector \
  -e DATABASE_HOST=postgres-db \
  -e DATABASE_PORT=5432 \
  -e DATABASE_USER=debezium \
  -e DATABASE_PASSWORD=dbpassword \
  -e DATABASE_DBNAME=orders \
  confluentinc/cp-debezium-connector:latest
```

**Option 2: AWS DMS**
1. Configure a **source replica** for your database.
2. Set the target as **Kafka** or **S3** for CDC logs.

---

### **5.2 Process with Flink**
```java
// Java (Flink) - Filter and aggregate CDC events
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
KafkaSource<String> source = KafkaSource.<String>builder()
    .setBootstrapServers("kafka:9092")
    .setTopics("orders-topic")
    .setGroupId("metrics-processor")
    .setStartingOffsets(OffsetsInitializer.latest())
    .setValueOnlyDeserializer(new SimpleStringSchema())
    .build();

DataStream<String> stream = env.fromSource(
    source,
    WatermarkStrategy.noWatermarks(),
    "Kafka Source"
);

// Parse JSON and extract metrics
stream
    .flatMap(new JsonParser())
    .filter(record -> record.getOp().equals("insert"))
    .process(new TransactionCounter())
    .addSink(new PrometheusHttpSink("http://prometheus:9090/api/v1/write"));
```

**Key Flink Operators:**
| Operator               | Purpose                                                                 |
|------------------------|-------------------------------------------------------------------------|
| `flatMap`              | Parse JSON and extract fields (e.g., `order_id`, `amount`).              |
| `filter`               | Drop irrelevant events (e.g., `op != "insert"`).                        |
| `keyBy` + `window`     | Aggregate (e.g., count orders per minute).                               |
| `sinkTo`               | Write to Prometheus/InfluxDB.                                           |

---

### **5.3 Store Metrics**
**Prometheus Example (Python Scraper):**
```python
from prometheus_client import start_http_server, Gauge

# Metric definition
TRANSACTION_COUNT = Gauge('transaction_count', 'Total orders processed')

def process_event(event):
    TRANSACTION_COUNT.inc()  # Increment on each insert event

# Start HTTP server for Prometheus to scrape
start_http_server(8000)
```

**TimescaleDB Example (SQL):**
```sql
-- Create hypertable for time-series metrics
CREATE TABLE metrics (
    metric_name TEXT,
    value FLOAT,
    timestamp TIMESTAMPTZ NOT NULL,
    tags JSONB
)
PARTITION BY RANGE (timestamp);

-- Insert CDC-derived metrics
INSERT INTO metrics
VALUES ('transaction_count', 42.0, NOW(), '{"service": "checkout"}');
```

---

## **6. Scaling Considerations**
| **Challenge**               | **Solution**                                                                 |
|-----------------------------|------------------------------------------------------------------------------|
| High CDC volume             | Partition Kafka topics by table/database.                                    |
| Stream processing backlog   | Scale Flink/Spark workers or adjust parallelism.                            |
| Metric storage growth       | Use TimescaleDB’s **continuous aggregates** or Prometheus **retention policies**. |
| Schema evolution             | Use **Avro schema registry** or **Protobuf**.                                |

---

## **7. Monitoring**
| **Metric**                  | Tool                          | Purpose                                                                 |
|-----------------------------|-------------------------------|-------------------------------------------------------------------------|
| CDC lag                     | Debezium UI                   | Track source-to-sink delay.                                             |
| Stream processing latency   | Flink Web UI                  | Monitor event processing time.                                          |
| Prometheus scrape errors    | Prometheus Alertmanager       | Alert on failed metric collection.                                       |
| Database load               | PostgreSQL pg_stat_statements | Ensure CDC doesn’t overburden the source.                               |

---

## **8. Related Patterns**
1. **[Event Sourcing]** – Store state changes as an immutable log (complements CDC).
2. **[Batch Loading]** – For historical data (vs. CDC for real-time).
3. **[Microservices Metrics]** – Distributed tracing (e.g., Jaeger) for latency analysis.
4. **[Data Mesh]** – Decentralized metric ownership (each team owns their CDC pipeline).
5. **[Serverless CDC]** – Use **AWS Kinesis Data Streams** + **Lambda** for event processing.

---

## **9. Troubleshooting**
| **Issue**                          | Diagnosis                          | Fix                                                                     |
|------------------------------------|------------------------------------|--------------------------------------------------------------------------|
| CDC lag > 1 minute                 | Check Debezium log, database load.  | Scale Debezium workers or tune `snapshot.isolation.policy`.              |
| Flink job stuck                    | View Flink UI for stuck tasks.     | Increase `taskmanager.numberOfTaskSlots` or optimize serializers.         |
| Prometheus metric missing          | Verify scrape config (`--path=/metrics` in service). | Update service discovery rules.                                         |
| Schema mismatch                    | Validate Avro schemas.             | Use `schemaregistry-cli` to validate events.                             |

---
**References:**
- [Debezium Quickstart](https://debezium.io/documentation/reference/stable/quickstart.html)
- [Prometheus Documentation](https://prometheus.io/docs/introduction/overview/)
- [Flink CDC Connector](https://nightlies.apache.org/flink/flink-docs-stable/docs/connectors/table/cdc/)