---
# **Debugging "Real-Time Dashboards from CDC" (Change Data Capture) – A Troubleshooting Guide**
*For Senior Backend Engineers*

## **1. Overview**
The **"Real-Time Dashboards from CDC"** pattern involves capturing database changes (inserts, updates, deletes) via a **Change Data Capture (CDC**) pipeline (e.g., Debezium, Kafka Connect, AWS DMS) and streaming them to a **real-time analytics engine** (e.g., Kafka Streams, Flink, or a dashboard like Grafana/Power BI). If dashboards fail to reflect live updates, latency spikes, or errors occur, this guide will help diagnose and resolve issues quickly.

---

## **2. Symptom Checklist**
Before diving into debugging, confirm which symptoms match your environment:

| **Symptom**                          | **Description**                                                                 | **Severity** |
|--------------------------------------|---------------------------------------------------------------------------------|--------------|
| **Delayed dashboard updates**        | Real-time data appears minutes/hours late                                         | Medium       |
| **Missing CDC records**              | Some database changes don’t appear in the stream or dashboard                  | High         |
| **High latency spikes**              | Sudden delays in processing (e.g., 10ms → 1s)                                  | High         |
| **Duplicate/missing records**        | Data anomalies (e.g., duplicate rows, gaps in timestamps)                        | High         |
| **Error logs in CDC/streaming layer**| `OffsetCommitFailed`, `SchemaRegressionError`, or `ConsumerTimeout`            | Critical     |
| **Dashboard timeouts**               | Frontend fails to fetch data (e.g., 504 Gateway Time-out)                       | Medium       |
| **Resource exhaustion**              | High CPU/memory on Kafka brokers, Flink workers, or DB connection pool         | Critical     |
| **Schema drift**                     | New DB columns aren’t captured in the CDC pipeline                              | Medium       |

---

## **3. Common Issues & Fixes**
### **A. CDC Pipeline Failures**
#### **Issue 1: Debezium/Kafka Connect Not Capturing Changes**
**Symptoms:**
- No messages in Kafka topics (e.g., `your-db.your-table`).
- `debizium-connect` pod logs show `Connection refused` or `Table not found`.

**Root Causes:**
- **DB user lacks CDC permissions** (e.g., `REPLICATION` or `CDC` schema access).
- **Debezium connector misconfiguration** (e.g., wrong `database.hostname`, `table.include.list`).
- **Network/firewall blocking DB binlog streams**.

**Fixes:**
```bash
# 1. Verify DB user has CDC permissions (PostgreSQL example)
CREATE USER cdc_user WITH REPLICATION LOGIN PASSWORD 'password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cdc_user;
ALTER USER cdc_user CREATEDB;
```

```yaml
# 2. Check Debezium connector config (example for PostgreSQL)
{
  "name": "postgres-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "your-db-host",
    "database.port": "5432",
    "database.user": "cdc_user",
    "database.password": "password",
    "database.dbname": "your_db",
    "table.include.list": "public.users,public.orders",
    "plugin.name": "pgoutput"
  }
}
```

**Debugging Steps:**
- Check Debezium logs for `ERROR` or `WARN` entries.
- Test DB connectivity: `psql -h your-db-host -U cdc_user -d your_db`.
- Verify `table.include.list` matches your schema tables.

---

#### **Issue 2: Offset Commit Failures (Kafka Consumer)**
**Symptoms:**
- Consumer lags behind producer (`kafka-consumer-groups --describe` shows `LAG > 0`).
- Logs: `OffsetCommitFailedException`, `ConsumerRebalanceException`.

**Root Causes:**
- **Consumer crashes** (e.g., unhandled exceptions in stream processing).
- **Manual offset commits** (if using `commitSync()` in code).
- **Kafka broker misconfiguration** (e.g., `offsets.topic.replication.factor=1`).

**Fixes:**
```java
// Fix: Use async commits (best practice for Flink/Kafka Streams)
env.enableCheckpointing(10000); // Flink
properties.setProperty(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, "false");
```

```bash
# Check consumer group lag
kafka-consumer-groups --bootstrap-server kafka-broker:9092 --describe
```

**Debugging Steps:**
- Enable debug logs for Kafka consumers.
- If using Flink, check `Checkpointing` metrics in the UI.
- Ensure `offsets.topic.replication.factor` ≥ broker count.

---

### **B. Streaming Pipeline Bottlenecks**
#### **Issue 3: High Latency in Kafka Streams/Flink**
**Symptoms:**
- Real-time data appears with **10s–1m delay**.
- Flink/Kafka UI shows **backpressure** or **slow processing**.

**Root Causes:**
- **Low Kafka partition count** → Consumer threads bottleneck.
- **Underpowered Flink workers** (CPU/memory insufficient).
- **Joins/aggregations** (e.g., `window.count()`) causing lag.
- **Checkpointing too frequent** (default 1s may be too aggressive).

**Fixes:**
```java
// Flink: Optimize parallelism and state backend
StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
env.setParallelism(4); // Match Kafka partitions
env.setStateBackend(new RocksDBStateBackend("file:///checkpoints", true));
```

```bash
# Scale Kafka partitions (if underutilized)
kafka-topics --alter --topic your-topic --partitions 4
```

**Debugging Steps:**
- Use **Flink Web UI** (`http://flink-jobmanager:8081`) to check:
  - **Backpressure indicators** (red bars = bottleneck).
  - **Source/sink processing time** (latency per operation).
- Enable **Kafka producer metrics** (`kafka.producer.type=embedded`).

---

#### **Issue 4: Schema Mismatch Between DB and CDC**
**Symptoms:**
- **Missing columns** in Kafka messages.
- **New DB columns** not appearing in dashboards.
- **Type mismatches** (e.g., `VARCHAR` → `JSON`).

**Root Causes:**
- Debezium connector **schema evolution** not enabled.
- **Exclusion of columns** in `table.include.list` or `transforms`.

**Fixes:**
```yaml
# Enable schema evolution in Debezium
"transforms": "unwrap",
"transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
"transforms.unwrap.drop.tombstones": "false",
```

**Debugging Steps:**
- Inspect CDC topic schema with `kafka-avro-console-consumer`:
  ```bash
  kafka-avro-console-consumer --bootstrap-server kafka-broker:9092 \
    --topic your-db.users --property schema.registry.url=http://schema-registry:8081
  ```
- Compare DB schema with Avro schema in **Confluent Schema Registry**.

---

### **C. Dashboard-Specific Issues**
#### **Issue 5: Dashboard Timeouts (Grafana/Power BI)**
**Symptoms:**
- Frontend fails to fetch data (`504 Gateway Timeout`).
- Grafana alerts show `Query took too long`.

**Root Causes:**
- **Kafka consumer timeout** (e.g., `max.poll.interval.ms` too low).
- **Dashboard query complexity** (e.g., `GROUP BY` over large time windows).
- **Proxies (NGINX, Envoy) misconfigured**.

**Fixes:**
```properties
# Increase Kafka poll timeout (Consumer props)
max.poll.interval.ms=300000  # 5 minutes
fetch.max.bytes=52428800     # 50MB (if using large payloads)
```

```sql
-- Grafana: Optimize query (example)
# Bad: GROUP BY across 1 year of data
SELECT count(*) FROM "your-topic" WHERE time > now() - 1y

# Good: Use time bucketing
SELECT count(*) FROM "your-topic" WHERE time > now() - 1d GROUP BY time(1h)
```

**Debugging Steps:**
- Check **Grafana logs** (`/var/log/grafana/grafana.log`) for timeouts.
- Test Kafka consumer **locally** to isolate issue:
  ```bash
  kafka-console-consumer --bootstrap-server kafka-broker:9092 \
    --topic your-topic --from-beginning --max-messages 100
  ```
- If using **Kafka Connect to dashboard**, check `connect-worker` logs.

---

## **4. Debugging Tools & Techniques**
### **A. Real-Time Monitoring**
| **Tool**               | **Purpose**                                                                 | **Command/URL**                                  |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Kafka Consumer Groups** | Check lag between producers/consumers                                    | `kafka-consumer-groups --bootstrap-server ...`   |
| **Flink UI**           | Monitor backpressure, checkpointing, and job status                       | `http://flink-jobmanager:8081`                   |
| **Prometheus + Grafana** | Track CDC pipeline metrics (e.g., `debizium.export.rate`)              | See [Debezium Prometheus Exporter](https://debezium.io/documentation/reference/stable/monitoring.html) |
| **Kafka Avro Console**  | Inspect CDC payloads for schema issues                                   | `kafka-avro-console-consumer --bootstrap-server` |
| **DB Binlog Monitor**  | Verify CDC is capturing changes (Debezium-specific)                        | `debizium-status` (if using Debezium UI)         |

### **B. Logs to Check**
| **Component**         | **Key Error Patterns**                          | **Log Location**                          |
|-----------------------|-------------------------------------------------|-------------------------------------------|
| **Debezium/Kafka Connect** | `ConnectionException`, `NoSuchTableException`  | `logs/connect/connect.log`                |
| **Flink**             | `Backpressure`, `CheckpointFailed`              | `logs/flink/`                              |
| **Kafka Broker**      | `ReplicaUnderReplicated`, `DiskError`           | `/var/log/kafka/server.log`               |
| **Dashboard (Grafana)** | `QueryError`, `Timeout`                        | `/var/log/grafana/grafana.log`            |
| **DB**                | `Binlog cleanup blocked`, `Replication lag`    | `POSTGRES_DATA_DIR/log/postgresql-*.log`   |

### **C. Performance Profiling**
- **Kafka Latency Test**:
  ```bash
  kafka-producer-perf-test --topic test --throughput -1 --record-size 1000 --num-records 1000000 --producer-props bootstrap.servers=kafka-broker:9092
  ```
- **Flink Tracing**:
  ```bash
  # Enable Flink metrics in `flink-conf.yaml`
  metrics.reporter.prom.class: org.apache.flink.metrics.prometheus.PrometheusReporter
  ```
- **DB Replication Lag**:
  ```sql
  -- PostgreSQL: Check replication status
  SELECT pg_stat_replication;
  ```

---

## **5. Prevention Strategies**
### **A. Architectural Best Practices**
1. **Partitioning Strategy**:
   - Align Kafka partitions with **DB tables** (1:1 if possible).
   - Example: If `users` table has 1M rows, target **10–100 partitions**.
   ```bash
   kafka-topics --create --topic users --partitions 8 --replication-factor 2
   ```

2. **Schema Management**:
   - Use **Confluent Schema Registry** for Avro/Protobuf.
   - Enable **schema evolution** in Debezium:
     ```yaml
     "schema.registry.url": "http://schema-registry:8081",
     "transforms": "unwrap",
     ```

3. **Resource Planning**:
   - **Debezium**: 2 vCPU + 4GB RAM per DB instance.
   - **Flink**: Scale workers based on **state size** (e.g., `--taskmanager.memory.process.size 4096m`).
   - **Kafka**: Ensure brokers have **fast disques** (SSD) for CDC logs.

### **B. Alerting & Automation**
| **Issue**               | **Alert Rule**                          | **Remediation Script**                     |
|-------------------------|-----------------------------------------|--------------------------------------------|
| **Consumer lag > 5 min** | `kafka_consumer_lag > 300`              | Scale Flink workers: `kubectl scale --replicas=3 flink-jobmanager` |
| **DB replication lag**  | `pg_stat_replication.latency > 60s`      | Restart Debezium connector                  |
| **Checkpoint failures** | `flink_job_checkpoint_failure`          | Restart failed task: `flink list -a`       |
| **Disk full on broker** | `kafka_disk_usage > 90%`                | Clean old logs: `kafka-log-dirs.sh cleanup` |

### **C. Testing & Validation**
1. **CDC Pipeline Smoke Test**:
   ```bash
   # Insert test data, verify it appears in Kafka
   psql -c "INSERT INTO users (id, name) VALUES (1, 'test')"
   kafka-console-consumer --topic your-db.users --from-beginning --max-messages 1
   ```

2. **End-to-End Latency Test**:
   - Use a **load generator** (e.g., `kafka-producer-perf-test`) and measure time from DB → Dashboard.
   - Target: **<1s for 99th percentile**.

3. **Chaos Engineering**:
   - **Kill a Flink task** to test recovery:
     ```bash
     kubectl delete pod -l app=flink-taskmanager
     ```
   - **Simulate network partitions** (if using Kafka MirrorMaker).

4. **Backup CDC State**:
   - **Flink**: Enable `state.backend.incremental` for faster recovery.
   - **Debezium**: Backup `offsets` and `schema` topics periodically.

---

## **6. Quick Reference Table**
| **Problem**               | **First Check**                          | **Immediate Fix**                          | **Long-Term Fix**                     |
|---------------------------|------------------------------------------|--------------------------------------------|----------------------------------------|
| No CDC messages in Kafka  | Debezium logs, DB permissions             | Recheck `table.include.list`, restart connector | Add monitoring for `debizium.export.rate` |
| High Flink latency        | Flink UI backpressure, checkpoint logs   | Scale parallelism, reduce window size      | Optimize stateful ops (e.g., use `KeyedStreams`) |
| Dashboard timeouts        | Grafana logs, Kafka consumer lag          | Increase `max.poll.interval.ms`           | Use materialized views in dashboard   |
| Schema drift              | Compare DB schema with Avro schema       | Update Debezium `transforms`                | Use Schema Registry + backward compatibility |

---

## **7. Final Checklist for Resolution**
Before declaring the issue resolved:
1. **[ ]** Verify CDC pipeline is **capturing 100% of changes** (test with inserts/updates/deletes).
2. **[ ]** Confirm **end-to-end latency** is <1s (99th percentile).
3. **[ ]** Test **failure scenarios** (e.g., broker crash, DB restart).
4. **[ ]** Validate **schema compatibility** between DB and CDC.
5. **[ ]** Set up **alerts** for lag, errors, and resource limits.

---
**Next Steps:**
- If the issue persists, **dig into logs** with `grep`/`jq`:
  ```bash
  # Search Flink task logs for failures
  kubectl logs <flink-taskmanager-pod> | grep -i "error\|timeout\|backpressure"

  # Decode Avro messages
  kafka-avro-console-consumer --bootstrap-server kafka-broker:9092 --topic your-topic --property value.deserializer=io.confluent.kafka.serializers.KafkaAvroDeserializer --property schema.registry.url=http://schema-registry:8081
  ```
- Consider **opening an issue** in the relevant GitHub repo (Debezium/Kafka/Flink).