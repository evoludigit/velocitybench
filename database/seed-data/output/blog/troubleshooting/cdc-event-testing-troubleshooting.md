# **Debugging CDC (Change Data Capture) Event Testing: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) is a critical pattern for real-time data synchronization, enabling event-driven architectures, microservices, and reactive systems. Testing CDC pipelines effectively ensures data consistency and reliability across systems. This guide provides a structured approach to debugging common CDC event testing issues.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

### **General CDC Event Testing Issues**
- [ ] **Missing or delayed events** – No CDC events appear in the test target system.
- [ ] **Incorrect event payloads** – Data in CDC events doesn’t match source database changes.
- [ ] **Duplicate events** – Same change appears multiple times in the target.
- [ ] **Event ordering issues** – Events arrive out of sequence.
- [ ] **Deadlocks or timeouts** – CDC pipeline hangs or fails during testing.
- [ ] **Connection failures** – Database or event bus connectivity issues.
- [ ] **Schema mismatches** – Test system expects a different payload structure.
- [ ] **Concurrency conflicts** – Race conditions in test environment.

### **Database-Specific Issues**
- [ ] **Binlog/Binary Log corruption** (MySQL, MariaDB)
- [ ] **Transaction log (WAL) inconsistencies** (PostgreSQL, Oracle)
- [ ] **Incremental snapshot failures** (if CDC starts from a known state)
- [ ] **Trigger hangs or deadlocks** (if using trigger-based CDC)

### **Event Delivery Issues**
- [ ] **Kafka/Pulsar/Amazon Kinesis consumer lag** (if using event streaming).
- [ ] **Dead letter queue (DLQ) filling up** (malformed or unprocessable events).
- [ ] **Consumer group rebalancing issues** (race conditions in parallel processing).

---

## **2. Common Issues and Fixes**

### **Issue 1: Missing or Delayed CDC Events**
**Symptom:** No events appear in the target system, or events arrive significantly later than expected.

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Code/Configuration Example** |
|----------------|---------|----------------------------------|
| **Database binlog not enabled** (MySQL) | Ensure `binlog_row_event_max_metadata=0` and `binlog_format=ROW`. | ```sql -- MySQL Config my.cnf [mysqld] binlog_row_event_max_metadata=0 binlog_format=ROW server-id=1 ``` |
| **Debezium connector misconfigured** | Verify `database.history.*` settings and `offset.storage.*` (Kafka). | ```yaml -- Debezium Config offsets.storage.topic: debezium_offsets offsets.storage.file.filename: debezium_offsets ``` |
| **Snapshot isolation conflicts** | Disable `server-isolation` or adjust `snapshot.isolation.queries` in Debezium. | ```yaml snapshot.isolation.queries: ["LOCK TABLES ... SELECT"] ``` |
| **Consumer not reading from earliest offset** | Reset consumer to `EarliestOffset` in tests. | ```java // Kafka Consumer consumer.seekToBeginning(topicPartition); ``` |
| **Database transaction log not flushed** | Ensure `sync_binlog=1` (MySQL) or `wal_level=logical` (PostgreSQL). | ```sql -- PostgreSQL Config postgresql.conf wal_level = logical ``` |

---

### **Issue 2: Incorrect Event Payloads**
**Symptom:** CDC events contain wrong data (e.g., missing fields, wrong values).

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Example** |
|----------------|---------|-------------|
| **Schema evolution mismatch** | Use `schema.history.internal.*` in Debezium for backward compatibility. | ```yaml schema.history.internal.connector: debezium schema.history.internal.key.converter: org.apache.kafka.connect.json.JsonSchemaGenerator schema.history.internal.value.converter: org.apache.kafka.connect.json.JsonSchemaGenerator ``` |
| **Wrong CDC mode (New Only vs Full Image)** | Configure `transforms=unwrap` in Debezium to ensure correct payloads. | ```yaml transforms=unwrap transform.sources=unwrap1 transform.sources.unwrap1.type=io.debezium.transforms.ExtractNewRecordState transform.sources.unwrap1.drop.tombstones=false ``` |
| **Database triggers not firing** | Check if triggers are enabled and properly written. | ```sql CREATE TRIGGER after_insert_trigger AFTER INSERT ON test_table FOR EACH ROW BEGIN INSERT INTO audit_log (event_type, data) VALUES ('INSERT', NEW.*); END; ``` |
| **Timezone/locale issues** | Explicitly set `timestamp.generator.class.name` in Debezium. | ```yaml timestamp.generator.class.name: org.apache.kafka.connect.timestamp.GmtTimestampGenerator ``` |

---

### **Issue 3: Duplicate Events**
**Symptom:** The same database change appears multiple times in the CDC stream.

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Example** |
|----------------|---------|-------------|
| **Debezium snapshot retries** | Increase `snapshot.lag.time.ms` or disable snapshots in tests. | ```yaml snapshot.lag.time.ms: 60000 snapshot.isolation.queries: [] ``` |
| **Consumer rebalances** | Use `enable.auto.commit=false` and manual commits. | ```java consumer.enableAutoCommit(false); consumer.commitSync(); ``` |
| **Database deadlocks** | Increase `deadlock.timeout` in Debezium. | ```yaml deadlock.timeout.ms: 5000 ``` |
| **Retention window too short** | Adjust `offsets.topic.replication.factor` and `retention.ms` in Kafka broker. | ```yaml offsets.topic.replication.factor: 2 offsets.topic.retention.ms: 604800000 ``` |

---

### **Issue 4: Event Ordering Issues**
**Symptom:** Events arrive out of sequence, breaking transaction integrity.

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Example** |
|----------------|---------|-------------|
| **Multiple CDC workers** | Use `partition.key.generator.class.name` to ensure ordering. | ```yaml partition.key.generator.class.name: io.debezium.transforms.ByLogSequenceNumberPartition ``` |
| **Kafka consumer rebalance** | Use `cooperative-sticky-assignment` for Kafka consumers. | ```java props.put(ConsumerConfig.GROUP_ID_CONFIG, "test-group"); props.put(ConsumerConfig.ALLOW_AUTO_CREATION_BOOL_CONFIG, false); ``` |
| **Debezium source offset management** | Use `offset.storage.file.filename` for deterministic ordering. | ```yaml offsets.storage.file.filename: debezium_offsets ``` |

---

### **Issue 5: Connection & Network Issues**
**Symptom:** CDC pipeline fails with connection errors.

#### **Root Causes & Fixes**
| **Root Cause** | **Fix** | **Example** |
|----------------|---------|-------------|
| **Database firewall blocking CDC connector** | Whitelist connector IP in DB security rules. | ```sql GRANT ALL PRIVILEGES ON *.* TO 'debezium'@'192.168.1.100' IDENTIFIED BY 'password'; ``` |
| **Network latency/mtus** | Increase `network.mtu` and `socket.timeout.ms`. | ```yaml network.mtu: 1500 socket.timeout.ms: 30000 ``` |
| **Kafka authentication issues** | Configure `security.protocol` and `sasl.mechanism`. | ```yaml security.protocol=SASL_SSL sasl.mechanism=SCRAM-SHA-512 sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username="debezium" password="password"; ``` |

---

## **3. Debugging Tools & Techniques**

### **Database-Level Debugging**
- **Check binlog/WAL logs**:
  ```bash
  # MySQL binlog inspection
  mysqlbinlog --start-datetime="2024-01-01 00:00:00" /var/log/mysql/mysql-bin.000001
  ```
- **Enable slow query logging** (PostgreSQL):
  ```sql
  ALTER SYSTEM SET log_min_duration_statement = '100ms';
  ```
- **Debezium connector logs**:
  ```bash
  # Tail Debezium connector logs (Kafka Connect)
  docker logs debezium-connect
  ```

### **Event Streaming Debugging**
- **Kafka Consumer Offsets Debugger**:
  ```bash
  # List consumer group offsets
  kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group test-group
  ```
- **Kafka Producer-Consumer Test**:
  ```java
  // Simple Kafka consumer for debugging
  Props props = new Props();
  props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "localhost:9092");
  props.put(ConsumerConfig.GROUP_ID_CONFIG, "debug-group");
  KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
  consumer.subscribe(Collections.singletonList("test-topic"));
  while (true) {
      ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
      records.forEach(record -> System.out.printf("Offset: %d, Key: %s, Value: %s%n",
          record.offset(), record.key(), record.value()));
  }
  ```

### **Unit & Integration Testing**
- **MockCDC (TestCDC Library)** – Simulate CDC events in tests:
  ```java
  // Example using TestCDC (https://github.com/ibm-de/TransformPlugin)
  TestCDC testCDC = new TestCDC();
  testCDC.withSourceTableData(List.of("id=1,name=Test"));
  testCDC.apply();
  ```
- **Debezium Embedded Server** – Test CDC locally:
  ```bash
  docker run --name debezium-mysql -d -p 3306:3306 mysql:8.0
  docker run --name debezium-connect -d -p 8083:8083 debezium/connect:2.4
  curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d '{
      "name": "mysql-cdc-connector",
      "config": {
          "connector.class": "io.debezium.connector.mysql.MySqlConnector",
          "database.hostname": "debezium-mysql",
          "database.port": "3306",
          "database.user": "debezium",
          "database.password": "dbz",
          "database.server.id": "184054",
          "database.server.name": "mysql-db",
          "database.include.list": "test_db",
          "database.history.kafka.bootstrap.servers": "localhost:9092",
          "database.history.kafka.topic": "schema-changes.test_db"
      }
  }'
  ```

---

## **4. Prevention Strategies**

### **Best Practices for CDC Testing**
1. **Isolate Test Environments**
   - Use separate Kafka topics, Debezium connectors, and database instances.
   - Example: `test-topic-cdc`, `mysql-cdc-test`.

2. **Schema Management**
   - Enforce backward compatibility in CDC payloads.
   - Use `schema.history.internal` for Avro schema evolution.

3. **Monitoring & Alerts**
   - Track:
     - Debezium connector lag (`DebeziumConnector:lastHeartbeatAgeMs`).
     - Kafka consumer lag (`kafka.consumer:lag`).
     - Database binlog replication delay.
   - Example Prometheus alert:
     ```yaml
     - alert: HighDebeziumLag
       expr: (debezium_connector_last_heartbeat_age_ms > 30000)
       for: 5m
       labels:
         severity: warning
       annotations:
         summary: "Debezium connector {{ $labels.connector }} lagging"
     ```

4. **Idempotent Consumer Processing**
   - Ensure reprocessing the same event doesn’t cause side effects.
   - Use transactional writes with `ConsumerTransaction` in Kafka.

5. **Performance Tuning**
   - Adjust Debezium batch size (`snapshot.batch.size`) and poll interval (`poll.interval.ms`).
   - Optimize Kafka partitions (e.g., `partition.assignment.strategy=range`).

6. **Chaos Engineering**
   - Test failure recovery:
     - Kill Debezium connector and verify reconnection.
     - Simulate Kafka broker failures.

---

## **5. Conclusion**
Debugging CDC event testing requires a structured approach:
1. **Start with symptoms** (missing events, duplicates, ordering issues).
2. **Check logs** (Debezium, database, Kafka).
3. **Validate configurations** (binlog settings, Kafka offsets).
4. **Test incrementally** (mock CDC, embedded setups).
5. **Prevent future issues** (monitoring, idempotency, chaos testing).

By following this guide, you can quickly identify and resolve CDC testing bottlenecks while ensuring data consistency in production.