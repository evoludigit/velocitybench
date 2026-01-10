# **[Pattern] Data Pipeline Architecture and Orchestration Reference Guide**

---

## **1. Overview**
Data Pipeline Architecture and Orchestration defines a structured approach to **ingesting, processing, transforming, and delivering data** across systems while ensuring **scalability, fault tolerance, and observability**. Modern pipelines support both:
- **Batch processing** (scheduled, large-scale data loads)
- **Streaming processing** (real-time event-driven flows)

Key components include:
- **Data Sources** (databases, APIs, files, event streams)
- **Ingestion Layers** (ETL/ELT, message brokers like Kafka)
- **Processing Engines** (Spark, Flink, custom scripts)
- **Orchestrators** (Airflow, Luigi, Dagster)
- **Storage & Sinks** (data lakes, warehouses, databases)
- **Monitoring & Alerts** (metrics, logs, SLAs)

This pattern emphasizes **idempotency, retries, dead-letter queues (DLQs), and versioned schema management** to handle failures gracefully.

---
## **2. Schema Reference**

| **Component**          | **Purpose**                                                                                     | **Key Technologies**                                                                 | **Non-Functional Requirements**                     |
|------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------|
| **Source**             | Extracts raw data from heterogeneous systems (e.g., APIs, databases, IoT).                     | REST/gRPC APIs, JDBC, CDC (Debezium), Kafka Connect                                   | Low-latency ingestion, schema evolution support       |
| **Ingestion Layer**    | Buffers and routes data for processing (batch/streaming).                                      | Kafka, RabbitMQ, Pub/Sub, AWS SQS/SNS                                               | Partition tolerance, exactly-once delivery           |
| **Processing Engine**  | Transforms/cleans/aggregates data (e.g., joins, windowing, ML features).                         | Apache Spark (Structured Streaming), Flink, dbt, SQL-on-lake (BigQuery, Snowflake)   | Parallelism, dynamic scaling, UDF support            |
| **Orchestrator**       | Coordinates workflows, dependencies, and retries.                                               | Apache Airflow, Luigi, Dagster, AWS Step Functions                                  | DAG visualization, parametric runs, SLA compliance   |
| **Storage**            | Persists intermediate/processed data (structured/unstructured).                                | Delta Lake, Iceberg, Parquet, Hadoop HDFS, S3                                      | ACID transactions, schema enforcement               |
| **Sink**               | Delivers processed data to target systems (databases, dashboards, ML models).                  | JDBC, API sinks, Kafka topics, BigQuery, Redshift                                   | Idempotent writes, schema compatibility               |
| **Monitoring**         | Tracks pipeline health, performance, and anomalies.                                             | Prometheus, Grafana, ELK Stack, Custom metrics (e.g., Airflow Task Duration)        | Alerting thresholds, lineage tracking                |
| **Recovery Mechanism** | Handles failures (retries, DLQs, checkpointing).                                               | Dead-letter queues, Spark checkpoints, Airflow XCom                                | Minimal data loss, replayability                     |

---

## **3. Implementation Details**

### **3.1 Core Principles**
1. **Decoupled Architecture**:
   - Use **event-driven** (streaming) or **scheduled** (batch) triggers.
   - Example: Kafka topics decouple producers (sources) from consumers (processors).
2. **Idempotent Operations**:
   - Design transformations to handle duplicate records (e.g., `MERGE` in SQL, `UPSERT` in NoSQL).
3. **Schema Management**:
   - Enforce schemas at ingestion (e.g., Avro/Protobuf) and validation (e.g., Great Expectations).
4. **Observability**:
   - Log metadata (e.g., `job_id`, `timestamp`) for debugging.
   - Instrument critical paths (e.g., Spark job duration, Kafka lag).

### **3.2 Batch vs. Streaming Tradeoffs**

| **Aspect**            | **Batch Processing**                          | **Streaming Processing**                      |
|-----------------------|-----------------------------------------------|-----------------------------------------------|
| **Latency**           | Minutes/hours (scheduled)                     | Milliseconds–seconds (real-time)              |
| **State Management**  | Stateless (or checkpointed)                  | Stateful (e.g., windowed aggregations)        |
| **Fault Tolerance**   | Retries + checkpointing                      | Exactly-once semantics (checkpoints, idempotency) |
| **Tools**             | Spark, Hadoop, Airflow                        | Flink, Spark Structured Streaming, Kafka Streams |

### **3.3 Error Handling**
- **Retries**: Exponential backoff for transient failures (e.g., network timeouts).
- **Dead-Letter Queues (DLQ)**:
  - Failed records routed to a DLQ (e.g., S3 bucket) for manual review.
  - Example Airflow XCom + DLQ table in a database.
- **Checkpointing**:
  - Spark/Flink save offsets/watermarks to recover from failures.

---
## **4. Query Examples**

### **4.1 SQL (Batch Processing)**
**Example: Incremental Load from Database to Data Lake**
```sql
-- PostgreSQL CDC source (Debezium)
CREATE TABLE sales_incremental (
    sale_id BIGINT,
    product_id VARCHAR,
    amount DECIMAL(10,2),
    event_time TIMESTAMP,
    PRIMARY KEY (sale_id)
)
WITH (
    format = 'parquet',
    partitioned_by = 'date(event_time)'
);

-- Spark SQL: Join source with reference data
SELECT
    s.sale_id,
    p.product_name,
    s.amount,
    DATE(s.event_time) AS sale_date
FROM sales_incremental s
JOIN products p ON s.product_id = p.product_id;
```

### **4.2 Streaming (Kafka + Flink)**
**Example: Real-Time Fraud Detection**
```java
// Flink Java DSL: Stream processing
DataStream<Transaction> transactions = env
    .addSource(new FlinkKafkaConsumer<>("transactions", new TransactionSchema(), props))
    .keyBy(Transaction::getUserId);

StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.enableCheckpointing(5000); // Checkpoint every 5s
env.setStateBackend(new RocksDBStateBackend("s3://checkpoints/"));

transactions
    .process(new FraudDetector())
    .addSink(new KafkaSink<>("fraud-alerts", new AlertSchema(), props));
```

### **4.3 Orchestration (Airflow DAG)**
**Example: Airflow Workflow for ETL**
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime

def extract_data():
    # Ingest from API to S3
    pass

def transform_data():
    # Run Spark job via ClusterModeOperator
    pass

with DAG(
    'etl_pipeline',
    schedule_interval="@daily",
    start_date=datetime(2023, 1, 1),
    catchup=False
) as dag:
    extract = PythonOperator(task_id='extract', python_callable=extract_data)
    transform = PythonOperator(task_id='transform', python_callable=transform_data)
    extract >> transform
```

---

## **5. Related Patterns**

| **Pattern**                     | **Description**                                                                                     | **When to Use**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Event-Driven Architecture]**   | Decouple producers/consumers using event buses (e.g., Kafka).                                      | High-throughput, loosely coupled systems.                                     |
| **[Lambda Architecture]**        | Combine batch (historical) + speed layer (real-time) for analytics.                                 | Hybrid batch/streaming needs with low-latency requirements.                     |
| **[Data Mesh]**                  | Decentralize data ownership with domain-specific pipelines.                                        | Large-scale organizations with siloed teams.                                   |
| **[Schema Registry]**            | Centralized schema management for Avro/Protobuf.                                                   | Cross-team schema consistency.                                                 |
| **[Data Quality Monitoring]**    | Validate data at rest/motion (e.g., Great Expectations).                                           | Ensuring pipeline outputs meet SLAs.                                           |

---
## **6. Best Practices**
1. **Modularity**:
   - Split pipelines into small, reusable tasks (e.g., 1 task per transformation).
2. **Testing**:
   - Unit test transformations (e.g., pytest for Python UDFs).
   - Test edge cases (nulls, schema drifts).
3. **Cost Optimization**:
   - Auto-scale Spark/Flink clusters based on load.
   - Use spot instances for batch jobs.
4. **Security**:
   - Encrypt data in transit (TLS) and at rest (KMS).
   - Least-privilege access for pipeline roles (e.g., IAM policies).
5. **Documentation**:
   - Annotate schemas (e.g., [data-dictionary](https://github.com/microsoft/glossary)).
   - Log pipeline lineage (e.g., Apache Atlas).

---
## **7. Anti-Patterns to Avoid**
- **Tight Coupling**: Directly linking sinks to sources (use intermediaries like Kafka).
- **Monolithic Jobs**: Single large jobs are harder to debug than modular tasks.
- **No Monitoring**: Uninstrumented pipelines fail silently.
- **Over-Retailiation**: Retrying every failure (e.g., 10 retries for network timeouts).
- **Ignoring Schema Drift**: Untracked schema changes break downstream systems.