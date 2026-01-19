# **[Pattern] Real-Time Analytics Patterns Reference Guide**

---
## **1. Overview**
Real-Time Analytics Patterns enable organizations to process, analyze, and derive insights from streaming data within milliseconds to seconds. These patterns are essential for applications requiring immediate decision-making, such as fraud detection, personalized recommendations, IoT telemetry, clickstream analysis, and live customer support.

This guide outlines key **Real-Time Analytics Patterns**, including **Stream Processing**, **Incremental Aggregations**, **Feature Stores**, **Complex Event Processing (CEP)**, and **Anomaly Detection**. Each pattern is designed to optimize latency, scalability, and actionability in real-time data flows.

---
## **2. Schema Reference**

Below is a **normalized schema** for common real-time analytics data models, categorized by use case:

| **Component**          | **Data Model**                     | **Description**                                                                 | **Typical Fields**                                                                 |
|------------------------|------------------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Event Stream**       | `Event`                            | Raw, time-ordered data records from applications, sensors, or logs.              | `event_id (UUID)`, `timestamp (ISO8601)`, `source (str)`, `payload (JSON)`          |
| **User Interaction**   | `UserClick`, `UserSession`         | Tracks user behavior (e.g., clicks, page views, session duration).              | `user_id`, `session_id`, `event_type`, `page_url`, `timestamp`, `duration (ms)`   |
| **IoT Device**         | `DeviceTelemetry`, `Alert`         | Sensor data and device-generated alerts.                                        | `device_id`, `sensor_reading`, `status`, `location`, `timestamp`                  |
| **Transaction**        | `Transaction`, `Payment`           | Financial transactions and payment status.                                      | `txn_id`, `amount`, `merchant_id`, `status`, `fraud_score`, `timestamp`           |
| **Feature Store**      | `Feature`, `FeatureSnapshot`       | Precomputed features for ML models (e.g., user engagement score).              | `feature_id`, `entity_type`, `value`, `version`, `last_updated`                   |
| **Event Correlation**  | `CorrelatedEvent`, `SessionPath`   | Aggregates related events (e.g., checkout funnel steps).                       | `session_id`, `event_sequence`, `start_time`, `end_time`                          |
| **Anomaly Detection**  | `AnomalyAlert`                     | Flags unusual patterns (e.g., fraudulent transactions).                        | `alert_id`, `entity_type`, `severity`, `reason`, `detected_at`                   |
| **Aggregation**        | `WindowResult`                     | Precomputed metrics (e.g., 5-min sliding window counts).                       | `window_start`, `window_end`, `metric_name`, `value`, `timestamp`                |

---
## **3. Implementation Patterns & Query Examples**

### **A. Stream Processing**
**Use Case:** Process data in real-time with low latency (e.g., live dashboards, fraud alerts).

#### **Schema:**
```sql
CREATE TABLE Events (
  event_id STRING,
  timestamp TIMESTAMP,
  user_id STRING,
  event_type STRING, -- e.g., "click", "purchase"
  value DOUBLE,      -- e.g., page load time
  PRIMARY KEY (event_id, timestamp)
) WITH (
  'connector' = 'kafka',
  'topic' = 'user-events',
  'format' = 'json'
);
```

#### **Queries:**
1. **Ingest & Stream Processing (Flink/Spark SQL):**
   ```sql
   -- Stream query to detect high-value purchases in real-time
   SELECT
     user_id,
     AVG(value) AS avg_purchase_value,
     COUNT(*) AS num_transactions
   FROM Events
   WHERE event_type = 'purchase'
     AND value > 1000
   GROUP BY user_id, HOP(TUMBLE(timestamp, INTERVAL '5' MINUTE))
   ```
   - **Output:** Triggers alerts for suspicious transactions.

2. **Windowed Aggregations (Sliding/Tumbling):**
   ```sql
   -- Session-based analysis (e.g., "users who clicked 3+ items in last 10s")
   SELECT
     user_id,
     COUNT(*) AS clicks_in_window
   FROM Events
   WHERE event_type = 'click'
   GROUP BY user_id, SLIDE(TUMBLE(timestamp, INTERVAL '10' SECOND))
   HAVING clicks_in_window > 3;
   ```

---
### **B. Incremental Aggregations**
**Use Case:** Maintain running totals/averages without reprocessing all data (e.g., live leaderboards).

#### **Schema:**
```sql
CREATE TABLE RunningStats (
  metric_name STRING,
  window_end TIMESTAMP,
  count BIGINT,
  sum_value DOUBLE,
  last_updated TIMESTAMP
) WITH (
  'connector' = 'jdbc',
  'url' = 'jdbc:postgresql://db/analytics'
);
```

#### **Queries:**
1. **Update Incremental Stats (Delta Merge):**
   ```sql
   -- Insert/update running stats for "page_views" metric
   MERGE INTO RunningStats AS target
   USING (
     SELECT
       'page_views' AS metric_name,
       CAST(MAX(timestamp) AS TIMESTAMP) AS window_end,
       COUNT(*) AS count,
       SUM(1) AS sum_value,
       CURRENT_TIMESTAMP AS last_updated
     FROM Events
     WHERE event_type = 'view'
       AND timestamp >= '2023-01-01'
   ) AS source
   ON target.metric_name = source.metric_name
     AND target.window_end = source.window_end
   WHEN MATCHED THEN
     UPDATE SET count = source.count, sum_value = source.sum_value
   WHEN NOT MATCHED THEN
     INSERT VALUES (source.metric_name, source.window_end, source.count, source.sum_value, source.last_updated);
   ```

---
### **C. Feature Store**
**Use Case:** Store precomputed features for ML models (e.g., "user engagement score").

#### **Schema:**
```sql
CREATE TABLE Features (
  entity_type STRING,  -- e.g., "user", "product"
  entity_id STRING,    -- e.g., user_id, product_id
  feature_id STRING,   -- e.g., "avg_session_length"
  value DOUBLE,
  version INT,
  last_updated TIMESTAMP,
  PRIMARY KEY (entity_type, entity_id, feature_id, version)
) COMPACT STORAGE;
```

#### **Queries:**
1. **Compute Feature on Flight (Example: User Engagement):**
   ```sql
   -- Update "avg_session_length" for each user
   INSERT INTO Features
   SELECT
     'user' AS entity_type,
     user_id,
     'avg_session_length' AS feature_id,
     AVG(duration_ms) AS value,
     1 AS version,
     CURRENT_TIMESTAMP AS last_updated
   FROM UserSessions
   WHERE session_start >= '2023-01-01'
   GROUP BY user_id;
   ```

2. **Retrieve Features for ML Prediction:**
   ```sql
   -- Join features with live data for prediction
   SELECT
     u.user_id,
     f.avg_session_length,
     f.last_login_days,
     CASE WHEN f.fraud_score > 0.9 THEN 'HIGH_RISK' ELSE 'LOW_RISK' END AS risk_level
   FROM Users u
   JOIN Features f
     ON u.user_id = f.entity_id
     AND f.entity_type = 'user'
     AND f.feature_id IN ('avg_session_length', 'last_login_days', 'fraud_score');
   ```

---
### **D. Complex Event Processing (CEP)**
**Use Case:** Detect patterns across events (e.g., "3 failed logins in 5 minutes = brute force attack").

#### **Schema:**
```sql
CREATE TABLE LoginAttempts (
  user_id STRING,
  attempt_time TIMESTAMP,
  success BOOLEAN,
  location STRING
);
```

#### **Queries:**
1. **CEP Rule (Window + Pattern Matching):**
   ```sql
   -- Detect brute force attacks (3 failed attempts in 5 min)
   WITH failed_attempts AS (
     SELECT
       user_id,
       COUNT(*) AS attempt_count
     FROM LoginAttempts
     WHERE NOT success
     GROUP BY user_id, SLIDE(TUMBLE(attempt_time, INTERVAL '5' MINUTE))
   )
   SELECT
     user_id,
     MAX(attempt_count) AS failed_attempts_in_window
   FROM failed_attempts
   WHERE failed_attempts_in_window >= 3
   GROUP BY user_id, window_start;
   ```

---
### **E. Anomaly Detection**
**Use Case:** Flag outliers in real-time (e.g., unusual transaction amounts).

#### **Schema:**
```sql
CREATE TABLE Transactions (
  txn_id STRING,
  amount DOUBLE,
  timestamp TIMESTAMP,
  user_id STRING,
  PRIMARY KEY (txn_id, timestamp)
);
```

#### **Queries:**
1. **Statistical Anomaly Detection (Z-Score):**
   ```sql
   -- Compute Z-score for transaction amounts (3σ threshold)
   WITH stats AS (
     SELECT
       AVG(amount) AS mean,
       STDDEV(amount) AS stddev
     FROM Transactions
     WHERE timestamp >= '2023-01-01'
   )
   SELECT
     t.txn_id,
     t.amount,
     (t.amount - s.mean) / NULLIF(s.stddev, 0) AS z_score
   FROM Transactions t
   JOIN stats s
     ON TRUE
   WHERE ABS((t.amount - s.mean) / NULLIF(s.stddev, 0)) > 3
   ORDER BY z_score DESC;
   ```

2. **Machine Learning (Pre-trained Model):**
   ```python
   # Pseudocode for online ML anomaly detection (e.g., using TensorFlow Serving)
   def detect_anomaly(amount: float, user_features: Dict) -> bool:
       model = load_anomaly_model("fraud_detection")
       prediction = model.predict({
           "amount": [amount],
           **user_features
       })
       return prediction[0]["anomaly_score"] > 0.9
   ```

---
## **4. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  | **Tools/Libraries**                          |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|-----------------------------------------------|
| **Lambda Architecture**   | Combines batch and real-time processing for consistency.                        | When both real-time and historical accuracy are needed. | Kafka, Spark, HBase                            |
| ** Kappa Architecture**   | Fully stream-based (no batch layer).                                          | For pure real-time systems with no batch needs.   | Flink, Kafka Streams                          |
| ** Event Sourcing**       | Stores state changes as immutable events for replayability.                   | Auditable systems (e.g., financial ledgers).     | Apache Kafka, EventStoreDB                    |
| ** Microservices Stream Processing** | Decouples processing into specialized services (e.g., fraud, recommendations). | Large-scale distributed systems.                | Spring Cloud Stream, Kafka Streams            |
| ** Real-Time Joins**      | Enriches streams with reference data (e.g., user profiles).                   | When joining hot/cold data (e.g., sensor + user data). | Flink, Spark Structured Streaming            |
| ** Rule-Based Alerting**  | Triggers alerts on CEP patterns (e.g., "2 failed logins → lock account").    | Security/compliance use cases.                    | Drools, Esper                                  |

---
## **5. Best Practices**
1. **Latency Optimization:**
   - Use **in-memory state** (e.g., RocksDB in Flink) for low-latency aggregations.
   - **Parallelize processing** with keyed streams (e.g., `keyBy(user_id)` in Spark).

2. **Scalability:**
   - **Partition streams** by high-cardinality keys (e.g., `user_id`, `device_id`).
   - **Auto-scaling** in managed services (e.g., AWS Kinesis, Google Dataflow).

3. **Fault Tolerance:**
   - **Checkpointing** (e.g., Flink’s savepoints) to recover from failures.
   - **Idempotent sinks** (e.g., Kafka topics with deduplication).

4. **Cost Efficiency:**
   - **Sampling** for non-critical streams (e.g., 1% of events for analytics).
   - **Downsampling** for low-frequency metrics (e.g., hourly aggregates).

5. **Data Governance:**
   - **Schema evolution** with backward-compatible changes (e.g., Avro/Protobuf).
   - **Audit logs** for event streams (e.g., Kafka’s `ISR` monitoring).

---
## **6. Tools & Technologies**
| **Category**               | **Tools**                                                                 |
|----------------------------|--------------------------------------------------------------------------|
| **Stream Processing**      | Apache Flink, Apache Spark Streaming, Kafka Streams, AWS Kinesis         |
| **Feature Stores**         | Google Feature Store, Feast, Tecton, Hopsworks                            |
| **CEP Engines**            | Apache Flink CEP, Esper, Drools, IBM InfoSphere Streams                   |
| **Anomaly Detection**      | TensorFlow Anomaly Detection, PyOD, DeeperFlow                           |
| **Storage**                | Kafka, Pulsar, Apache Pulsar, Apache Iceberg (for materialized views)    |
| **Orchestration**          | Apache Airflow (for pipelines), Kubernetes (for stream apps)              |
| **Observability**          | Prometheus + Grafana, Datadog, MLOps tools (e.g., MLflow)                |

---
## **7. Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│             │    │             │    │                 │    │             │
│  Applications│───▶│  Kafka      │───▶│  Flink/Stream  │───▶│  Feature    │
│             │    │  Topics     │    │  Processing Job │    │  Store      │
└─────────────┘    └─────────────┘    └─────────────────┘    └─────────────┘
                 ▲                  ▲                     ▲                    ▲
                 │                  │                     │                   │
                 │                  │                     │                    │
┌─────────────┐  │  ┌─────────────┐ │  ┌─────────────┐     │  ┌─────────────┐
│             │  │  │             │ │  │             │     │  │             │
│  IoT/Sensors│  │  │  Database   │ │  │  ML Model   │     │  │  Alert      │
│             │  │  │  (Postgres) │ │  │  (TensorFlow)│     │  │  System     │
└─────────────┘  │  └─────────────┘ │  └─────────────┘     │  └─────────────┘
                 │                  │                     │
                 └──────────────────┘                     │
                                             ┌─────────────┐
                                             │             │
                                             │  Dashboard   │
                                             │  (Grafana)  │
                                             └─────────────┘
```