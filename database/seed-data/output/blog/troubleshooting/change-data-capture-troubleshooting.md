# Debugging **Change Data Capture (CDC) Patterns**: A Troubleshooting Guide
*For backend engineers implementing or maintaining real-time data sync*

---

## **1. Symptom Checklist**
Before diving into debugging, systematically verify these signs of CDC issues:

| **Symptom**                     | **Question to Ask**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------|
| Stale downstream data           | Are recent DB changes missing in target systems? (e.g., cache, analytics DB)       |
| High latency in downstream sync | Are changes delayed by seconds/minutes?                                             |
| Duplicates or missing events    | Are there duplicate/wrongly processed updates?                                       |
| Spikes in network traffic       | Is downstream traffic abnormally high? (May indicate misconfigured CDC triggers)   |
| Application inconsistencies     | Are UI/API responses incorrect despite DB updates?                                  |
| Deadlocks/hanging consumers     | Are messages stuck in Kafka/RabbitMQ queues?                                        |
| Logs flooding with errors       | Are CDC workers crashing or failing silently?                                       |

**Action**: Cross-reference symptoms with logs (`stdout`, databases, message brokers) and metrics (latency, error rates).

---

## **2. Common Issues and Fixes**
### **Issue 1: CDC Log Replication Failure**
**Symptom**: Changes aren’t captured, or log files are empty.
**Root Causes**:
- **Database-specific**: Incorrect WAL (Write-Ahead Log) or binary log (`binlog`) configuration (e.g., MySQL `binlog_row_events_extra` not enabled).
- **Missing permissions**: User lacks `REPLICATION CLIENT` or `LOG_REPLICATION_ADD_SLAVE` privileges.
- **Network issues**: Replication user can’t connect to the database.

**Fixes**:
#### **MySQL Example: Enable Binlog**
```sql
-- Check if binlog is enabled
SHOW VARIABLES LIKE 'log_bin';
-- Enable if disabled
SET GLOBAL log_bin = ON;
SET GLOBAL binlog_format = 'ROW'; -- Required for CDC
-- Restart MySQL (if needed) or flush logs:
FLUSH LOGS;
```

#### **PostgreSQL: Logical Decoding Setup**
```sql
-- Enable WAL archiving (if not done via pg_basebackup)
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_replication_slots = 4; -- Adjust based onCDC consumers
-- Restart PostgreSQL
```

**Verify**:
```bash
# Check binlog positions (MySQL)
SHOW MASTER STATUS;
# Check for replication slots (PostgreSQL)
SELECT * FROM pg_replication_slots;
```

---

### **Issue 2: Lag in CDC Stream Consumption**
**Symptom**: Downstream systems receive changes with noticeable delay (>100ms).
**Root Causes**:
- **Throttled consumers**: Too few workers processing messages.
- **Slow query performance**: CDC capture queries are inefficient.
- **Message broker backpressure**: Kafka/RabbitMQ queues are full.

**Fixes**:
#### **Scale Consumers**
```python
# Example: Scaling Kafka consumers (Python + Confluent)
from confluent_kafka import Consumer

# Increase partitions to parallelize
props = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'my-cdc-group',
    'auto.offset.reset': 'earliest',
    'partition.assignment.strategy': 'round_robin'  # Distribute load
}
consumer = Consumer(props)
consumer.subscribe(['change_events'], **{'auto.partition.assignor': 'roundrobin'})
```

#### **Optimize Capture Query**
```sql
-- Replace full-table scans with incremental queries
-- PostgreSQL example (logical decoding)
SELECT * FROM pg_replication_slot_get_changes('my_slot', 0, NULL);
-- MySQL example (with binlog)
SELECT * FROM mysql_binlog_event WHERE log_pos = [last_position];
```

**Monitor**:
```bash
# Check Kafka lag
kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group my-cdc-group
```

---

### **Issue 3: Schema Mismatch Between Source and Target**
**Symptom**: CDC consumers fail with `schema validation errors`.
**Root Causes**:
- **Schema drift**: New columns added to source DB but not reflected in target.
- **Data type incompatibility**: `TIMESTAMP` → `STRING` in target.
- **Missing relationships**: Parent/child tables not aligned.

**Fixes**:
#### **Schema Evolution Strategies**
1. **Avro/Protobuf**: Use backward-compatible schemas.
   ```json
   // Example Avro schema snippet (schema_registry)
   {
     "type": "record",
     "name": "UserChange",
     "fields": [
       {"name": "user_id", "type": "long", "doc": "Nullable?"},
       {"name": "updated_at", "type": "long", "doc": "Epoch millis"}
     ]
   }
   ```
2. **Database-specific sync**: Run a one-time sync for schema changes.
   ```sql
   -- Add missing columns to target
   ALTER TABLE target_table ADD COLUMN new_column VARCHAR(255);
   ```

**Verify**:
```bash
# Check Avro schema compatibility
avro schema-compatibility check -a old_schema.json -b new_schema.json
```

---

### **Issue 4: Duplicate Events in CDC Stream**
**Symptom**: Same change appears multiple times in downstream logs.
**Root Causes**:
- **Idempotent operations misconfigured**: Retries without deduplication.
- **Database retries**: Transactions rolled back and reapplied.
- **Broker replay**: Kafka/RabbitMQ partition reassignment.

**Fixes**:
#### **Idempotent Consumer Design**
```python
# Example: Deduplication with Kafka (Python)
from confluent_kafka import Consumer

seen_ids = set()
while True:
    msg = consumer.poll(timeout=1.0)
    if msg:
        event = msg.value().decode()
        if event['id'] not in seen_ids:
            seen_ids.add(event['id'])
            process_change(event)  # Your business logic
```

#### **Database-Level Deduplication**
```sql
-- Add unique constraint to target table
ALTER TABLE target_table ADD CONSTRAINT unique_id UNIQUE (user_id, event_timestamp);
-- Handle duplicates via ON CONFLICT (PostgreSQL)
INSERT INTO target_table (user_id, data)
VALUES (id, json_data)
ON CONFLICT (user_id) DO UPDATE SET data = EXCLUDED.data;
```

---

### **Issue 5: Connection Timeouts in CDC Workers**
**Symptom**: Workers crash with `connection refused` or `timeout` errors.
**Root Causes**:
- **Database limits**: Too many open connections.
- **Network latency**: High ping to DB or message broker.
- **Resource starvation**: CPU/memory pressure.

**Fixes**:
#### **Connection Pooling**
```python
# Python example with SQLAlchemy (PostgreSQL)
from sqlalchemy import create_engine

engine = create_engine(
    'postgresql+psycopg2://user:pass@example:5432/db',
    pool_size=20,
    max_overflow=50,
    pool_timeout=30,
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

#### **Monitor Connection Pool Metrics**
```bash
# Check PostgreSQL connections
SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;
# Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';
```

---

## **3. Debugging Tools and Techniques**
### **Database-Specific Tools**
| **Database** | **Tool**                          | **Use Case**                                  |
|--------------|-----------------------------------|-----------------------------------------------|
| MySQL        | `mysqlbinlog`                     | Inspect binlog events in real-time.           |
| PostgreSQL   | `pgBadger`                        | Analyze replication lag.                     |
| MongoDB      | `mongodump --oplogReplay`         | Replay oplog events offline.                 |
| SQL Server   | `T-SQL CDC` + `DBCC` commands     | Query CDC tables; check `DBCC SQLPERF` for blocking. |

**Example**: Dump MySQL binlog for debugging:
```bash
mysqlbinlog --start-datetime="2023-10-01 00:00:00" --stop-never /var/log/mysql/mysql-bin.000001 | grep "update"
```

### **Message Broker Tools**
| **Broker**  | **Tool**                          | **Use Case**                                  |
|-------------|-----------------------------------|-----------------------------------------------|
| Kafka       | `kafka-consumer-groups`           | Check lag, offsets.                           |
| Kafka       | `kafkacat`                        | Inspect topics/raw messages.                  |
| RabbitMQ    | `rabbitmqctl` + `rabbitmq-diagnostics` | Monitor queue depth, consumer health.  |

**Example**: Check Kafka consumer lag:
```bash
kafka-consumer-groups --bootstrap-server kafka:9092 --describe --group my-cdc-group --topic change_events
```

### **Logging and Tracing**
- **Structured Logging**: Use JSON logs with `structlog` or `loguru` to filter by `event_type` or `source_system`.
  ```python
  import loguru
  log = loguru.logger.bind(service="cdc-worker", instance="worker-1")
  log.debug("Processing event {} (offset {})", event, msg.offset)
  ```
- **Distributed Tracing**: Inject OpenTelemetry to trace CDC pipeline end-to-end.
  ```python
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("process_cdc_event"):
      # Your processing logic
  ```

### **Performance Profiling**
- **Database**: `pg_stat_statements` (PostgreSQL) or `perf` (Linux) to find slow queries.
- **Application**: `py-spy` (Python) or `pprof` to identify CPU bottlenecks.
  ```bash
  # Capture Python profile
  py-spy top -p $(pgrep -f "cdc_worker.py")
  ```

---

## **4. Prevention Strategies**
### **Design-Time Mitigations**
1. **Schema as Code**: Version control schema changes (e.g., Flyway, Liquibase).
   ```yaml
   # Example Liquibase changelog
   databaseChangeLog:
     - changeSet:
         id: add_notes_column
         author: engineer
         changes:
           - addColumn:
               tableName: users
               column:
                 name: notes
                 type: text
   ```
2. **Rate Limiting**: Use Kafka `consumer.lag-max-ratio` to prevent overload.
   ```properties
   # Kafka consumer config
   consumer.lag-max-ratio=2.0  # Warn if lag > 2x partitions
   ```
3. **Circuit Breakers**: Implement retries with exponential backoff (e.g., `tenacity` library).
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
   def sync_to_target(event):
       try:
           target_db.apply(event)
       except ConnectionError as e:
           log.error("Sync failed: %s", e)
           raise
   ```

### **Runtime Monitoring**
- **Alerts**: Set up Prometheus alerts for:
  - CDC lag > 5s.
  - Error rates > 0.1% in consumers.
  - Database connection pool exhaustion.
- **Dashboard**: Grafana dashboard with:
  - Kafka lag by topic.
  - CDC worker throughput (events/sec).
  - Database replication lag (e.g., PostgreSQL `pg_stat_replication`).

**Example Prometheus Alert**:
```yaml
groups:
- name: cdc-alerts
  rules:
  - alert: CDCHighLatency
    expr: rate(kafka_consumer_lag{topic="change_events"}[1m]) > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "CDC lag high on {{ $labels.topic }}"
```

### **Chaos Engineering**
- **Test Failover**: Kill CDC workers to verify self-healing.
- **Simulate Network Partitions**: Use `netem` to throttle DB connections.
  ```bash
  # Throttle CDC worker DB connections to 20% speed
  sudo tc qdisc add dev eth0 root netem delay 50ms 10ms loss 0%
  ```

---

## **5. Checklist for Quick Resolution**
| **Step**               | **Action**                                                                 |
|------------------------|----------------------------------------------------------------------------|
| **1. Is CDC capturing?** | Check DB log files/binlog for new entries.                                |
| **2. Are messages delivered?** | Verify message broker (Kafka/RabbitMQ) topics.                            |
| **3. Are consumers running?** | Check pod logs (`kubectl logs`).                                          |
| **4. Is schema aligned?** | Compare source/target schemas.                                             |
| **5. Are there duplicates?** | Sample events for ID uniqueness.                                           |
| **6. Is the DB healthy?** | Check connection pools, replication lag (`pg_stat_replication`).          |
| **7. Are alerts firing?** | Review Prometheus/Grafana for anomalies.                                  |

---
**Final Tip**: For production issues, **start with logs**. Use `journalctl` (Linux) or Kubernetes logs to isolate the failing component. Most CDC problems boil down to:
1. **Capture**: Database logs/binlog.
2. **Transport**: Message broker connectivity.
3. **Consume**: Worker health and schema alignment.