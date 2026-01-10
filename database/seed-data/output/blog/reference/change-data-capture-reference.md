# **[Pattern] Change Data Capture (CDC) Reference Guide**

---

## **1. Overview**
Change Data Capture (CDC) automatically detects and logs changes (inserts, updates, deletes) in a source system (e.g., database, file system) and streams them in real time to downstream consumers. This enables **low-latency synchronization**, **event-driven architecture**, and **decoupled processing** without polling or batching.

CDC is critical for:
- **Real-time analytics** (e.g., monitoring dashboards, fraud detection).
- **Data synchronization** (e.g., replicating databases across regions).
- **Event sourcing** (storing state changes for auditing/replay).
- **Cache invalidation** (updating caches when data changes).
- **Microservices** (propagating changes to dependent services).

Popular tools like **Debezium** (Kafka-based), **Debtrac**, or **Debezium Connector for PostgreSQL/MySQL** abstract low-level log parsing, making CDC accessible. This guide covers core concepts, implementation patterns, and configuration steps.

---

## **2. Core Components & Schema Reference**

| **Component**       | **Purpose**                                                                 | **Example Implementations**                     |
|---------------------|-----------------------------------------------------------------------------|-------------------------------------------------|
| **Source Database** | System storing data (e.g., PostgreSQL, MySQL).                               | PostgreSQL (WAL), MongoDB (OpLog), Kafka Logs.  |
| **Change Log**      | Underlying transaction logs (WAL, binlog, etc.).                            | PostgreSQL’s WAL, MySQL’s binary log.          |
| **CDC Connector**   | Reads change logs, captures DML operations (inserts/updates/deletes).       | Debezium PostgreSQL Connector, Kafka Connect.   |
| **Message Queue**   | Buffered, ordered stream of change events (e.g., Kafka topics, RabbitMQ). | Apache Kafka, Google Pub/Sub, AWS Kinesis.     |
| **Consumer**        | Processes changes (e.g., write to sink DB, trigger alerts).                 | Custom app, Kafka Streams, Flink.               |
| **Sink Database**   | Target system receiving changes (e.g., another DB, data warehouse).        | Snowflake, Redis, Elasticsearch.                |

---

## **3. Implementation Patterns**

### **3.1. Architecture Overview**
A typical CDC workflow:
1. **Capture**: Connector reads source logs (e.g., PostgreSQL WAL) and emits JSON events.
2. **Stream**: Change events are published to a message queue (e.g., Kafka topic).
3. **Consume**: Subscribers process events (e.g., update a cache or replicate to a warehouse).

```
[Source DB] → [CDC Connector] → [Kafka Topic] → [Consumer App] → [Sink DB]
```

---

### **3.2. Key CDC Patterns**

#### **A. Debezium-Based CDC (Kafka Connect)**
1. **Install Debezium Connector**:
   ```bash
   docker run -d --name debezium-connect -p 8083:8083 \
     --link kafka:kafka -e GROUP_ID=1 \
     mustafisoydan/confluentinc/cp-schema-registry:6.2.0 \
     -e CONNECT_BOOTSTRAP_SERVERS=kafka:9092 \
     -e CONNECT_REST_ADVERTISED_HOST_NAME=debezium-connect \
     -e CONNECT_GROUP_ID=connect -e CONNECT_CONFIG_STORAGE_TOPIC=connect_configs \
     -e CONNECT_OFFSET_STORAGE_TOPIC=connect_offsets -e CONNECT_STATUS_STORAGE_TOPIC=connect_statuses \
     -e CONNECT_KEY_CONVERTER=io.confluent.connect.avro.AvroConverter \
     -e CONNECT_VALUE_CONVERTER=io.confluent.connect.avro.AvroConverter \
     -e CONNECT_PLUGIN_PATH=/usr/share/java,/usr/share/confluent-hub-components \
     -e CONNECT_LOG4J_LOGGERS=org.apache.zookeeper=ERROR,org.I0Itec.zkclient=ERROR
   ```
2. **Configure PostgreSQL Connector**:
   Add this to `connect-standalone.properties`:
   ```properties
   connector.class=io.debezium.connector.postgresql.PostgresConnector
   database.hostname=postgres
   database.port=5432
   database.user=debezium
   database.password=dbz
   database.dbname=testdb
   database.server.name=postgres
   include.schema.changes=true
   slot.name=debezium
   ```
3. **Start Connector**:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     http://localhost:8083/connectors -d '{
       "name": "postgres-connector",
       "config": {
         "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
         "tasks.max": "1",
         "database.hostname": "postgres",
         "database.port": "5432",
         "database.user": "debezium",
         "database.password": "dbz",
         "database.dbname": "testdb",
         "database.server.name": "postgres",
         "include.schema.changes": "true",
         "slot.name": "debezium"
       }
     }'
   ```

#### **B. Direct Log Parsing (e.g., PostgreSQL WAL)**
For custom solutions, parse WAL files directly:
```sql
-- Enable logical decoding in PostgreSQL
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_wal_senders = 10;
```
Use tools like [`pg_epoch`](https://github.com/eulerto/pg_epoch) or [`pg_logical`](https://github.com/2ndQuadrant/pg_logical) to decode changes.

---

### **3.3. Event Schema**
Debezium emits events in Avro/JSON format. Example:
```json
{
  "schema": "...",
  "payload": {
    "op": "u",  // Insert (i), Update (u), Delete (d)
    "key": {    // Primary key of affected row
      "id": 1
    },
    "before": null,  // For inserts
    "after": {      // Updated row
      "id": 1,
      "name": "Updated Value"
    },
    "source": {
      "version": "1.1",
      "connector": "postgresql",
      "name": "postgres",
      "ts_ms": 1634567890123
    }
  }
}
```
Key fields:
- `op`: Operation type (`i`, `u`, `d`).
- `after/before`: Row state changes.
- `source`: Metadata (timestamp, connector).

---

## **4. Query Examples**
### **4.1. List CDC Events for a Table**
```bash
# Using Kafka CLI (Debezium example)
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic postgres.public.orders \
  --from-beginning \
  --formatter "kafka.tools.json.JsonKeyValueDeserializer"
```

### **4.2. Filter for Specific Schema Changes**
```sql
-- SQL query to track changes in Debezium's _debezium table (conceptual)
SELECT * FROM _debezium.public.orders
WHERE op = 'u' AND after->>'name' LIKE '%Updated%';
```

### **4.3. Replay CDC Events to a Sink**
Use **Kafka Streams** to transform/events:
```java
StreamsBuilder builder = new StreamsBuilder();
KStream<String, String> stream = builder.stream("postgres.public.orders");
stream.mapValues(value -> {
    // Transform Avro to JSON
    return new Gson().toJson(getAfterValue(value));
}).to("sink-topic");
```

---

## **5. Common Pitfalls & Mitigations**

| **Challenge**               | **Solution**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Schema Drift**            | Use schema registry (e.g., Confluent Schema Registry) to auto-register schemas. |
| **Slow Consumers**          | Scale consumers (parallel processing) or adjust batch size.                  |
| **Duplicate Events**        | Use `offset` tracking (Kafka) or transactional writes.                     |
| **High Latency**            | Optimize WAL settings (e.g., `wal_buffers = -1` in PostgreSQL).             |
| **Connector Crashes**       | Enable health checks and retries (Debezium’s `offset.storage` topic).        |

---

## **6. Related Patterns**
1. **[Event Sourcing](https://microservices.io/patterns/data/event-sourcing.html)**
   - Store state changes as a sequence of events (CDC emits these events).
2. **[CQRS](https://microservices.io/patterns/data/cqrs.html)**
   - Separate read/write models; CDC feeds only the read model.
3. **[Database Replication](https://www.postgresql.org/docs/current/warm-standby.html)**
   - Traditional sync vs. CDC: CDC is incremental and event-based.
4. **[Message Broker Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/MessageBroker.html)**
   - Kafka/PubSub act as CDC’s message broker.
5. **[Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)**
   - Manages evolving schemas of CDC events.

---
## **7. Tools & Libraries**
| **Tool**               | **Purpose**                                  | **Link**                                  |
|------------------------|---------------------------------------------|-------------------------------------------|
| **Debezium**           | Kafka Connect connectors for databases.     | [debezium.io](https://debezium.io/)       |
| **Kafka Connect**      | Framework for CDC connectors.               | [kafka.apache.org](https://kafka.apache.org/) |
| **pg_logical**         | PostgreSQL logical decoding.                | [2ndQuadrant](https://www.2ndquadrant.com/) |
| **Debtrac**            | Commercial CDC for PostgreSQL.               | [debtrac.com](https://debtrac.com/)       |
| **AWS DMS**            | Managed CDC for AWS services.               | [aws.amazon.com/dms](https://aws.amazon.com/dms/) |

---
## **8. Example Use Cases**
### **8.1. Real-Time Analytics**
- **Setup**: Debezium → Kafka → Flink (stream processing) → Elasticsearch.
- **Use Case**: Index recent orders for a search dashboard.

### **8.2. Cache Invalidation**
- **Setup**: Debezium → Kafka → Redis pub/sub.
- **Use Case**: Invalidate Redis cache when a product price changes.

### **8.3. Multi-Region Sync**
- **Setup**: PostgreSQL (Region A) → Debezium → Kafka → PostgreSQL (Region B).
- **Use Case**: Global low-latency database replication.

---
## **9. References**
- [Debezium Docs](https://debezium.io/documentation/reference/)
- [PostgreSQL Logical Decoding](https://www.postgresql.org/docs/current/logical-decoding.html)
- [Kafka Connect API](https://kafka.apache.org/documentation/#connect)
- [CDC in Microservices](https://microservices.io/patterns/data/change_data_capture.html)