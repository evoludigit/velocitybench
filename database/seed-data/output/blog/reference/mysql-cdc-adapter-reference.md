# **[Pattern] MySQL Change Data Capture (CDC) Adapter Reference Guide**

---

## **1. Overview**
This reference guide documents the **MySQL CDC Adapter pattern**, a robust framework for capturing, processing, and delivering real-time changes from MySQL databases to downstream systems. The adapter abstracts low-level CDC complexities (e.g., log binaries, replication filters, and event transformations) into declarative configurations and reusable components. Ideal for microservices, data pipelines, and event-driven architectures, it ensures **low-latency synchronization** while minimizing resource overhead. Key use cases include:
- **Real-time analytics** (e.g., streaming insights)
- **Data replication** (e.g., multi-active deployments)
- **Audit trails** (e.g., compliance tracking)
- **Event sourcing** (e.g., CQRS patterns)

The adapter supports **MySQL Binlog-based CDC** (via `mysqlbinlog` or proxies) and integrates seamlessly with **Kafka, RabbitMQ, or HTTP endpoints**. This guide covers core concepts, schema requirements, query examples, and related patterns for extensible implementations.

---

## **2. Key Concepts & Implementation Details**

### **2.1 Architecture Overview**
The adapter follows a **pipeline architecture** with the following layers:

| **Layer**               | **Responsibility**                                                                 | **Components**                          |
|-------------------------|-----------------------------------------------------------------------------------|-----------------------------------------|
| **Capture Layer**       | Reads and decodes MySQL binary logs (binlogs).                                    | Binlog Proxy, Debezium, M3U            |
| **Filter Layer**        | Applies schema/table filters and transforms events (e.g., DML/DDL).              | `filter.config` (YAML/JSON)             |
| **Serialization Layer** | Converts CDC events to structured formats (e.g., Avro, JSON, Protobuf).          | Schema Registry, Confluent Schema      |
| **Routing Layer**       | Routes events to consumers (Kafka topics, HTTP, etc.).                             | Consumer Groups, Adapters (`kafka.js`, `http-server`) |

---
### **2.2 Core Components**
| **Component**          | **Description**                                                                                     | **Configuration**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Binlog Reader**      | Connects to MySQL server via `binlog_client` protocol.                                             | `mysql_uri: "mysql://user:pass@host:3306"` |
| **Change Tracker**     | Maintains GTID/position offsets to avoid duplicate events.                                           | `tracker: "mysql"` (GTID or Log Position)  |
| **Event Processor**    | Parses events (INSERT/UPDATE/DELETE/DDL) and applies transformations.                             | `transforms: ["mask-columns", "flatten-json"]` |
| **Consumer Adapter**   | Delivers events to consumers (e.g., Kafka, HTTP).                                                   | `consumer: "kafka"`                        |

---
### **2.3 Supported MySQL Features**
| **Feature**            | **Supported?** | **Notes**                                                                                     |
|------------------------|----------------|-----------------------------------------------------------------------------------------------|
| **DML Events**         | ✅ Yes          | `INSERT`, `UPDATE`, `DELETE` with full transaction support.                                  |
| **DDL Events**         | ✅ (Partial)    | `CREATE TABLE`, `ALTER TABLE` (schema changes may require manual reconciliation).         |
| **GTID Replication**   | ✅ Yes          | Uses `replica_gtid_domain` for position tracking.                                           |
| **Binary Log Format**  | ✅ ROW          | ROW-based logs preferred for accuracy; STATEMENT/MIXED may require additional handling.     |
| **Temporal Tables**    | ❌ No           | CDC does not support `SYSTEM_VERSIONING`. Use `before_image`/`after_image` for workarounds. |

---

## **3. Schema Reference**

### **3.1 Required Database Schema**
The adapter does **not require** a separate schema. However, tables must comply with the following constraints:

| **Constraint**               | **Description**                                                                               | **Example**                          |
|------------------------------|-----------------------------------------------------------------------------------------------|---------------------------------------|
| **Primary Key**              | Required for event reconstruction.                                                           | `id INT NOT NULL PRIMARY KEY`         |
| **UUID Support**             | Optional but recommended for high-volume systems.                                         | `id UUID DEFAULT (UUID())`            |
| **Binlog Row Image**         | Must use `ROW` format (configured in `binlog_row_image: "FULL"`).                           | `binlog_rows_query_log_events: ON`    |
| **Column Filtering**         | Use `INFORMATION_SCHEMA.COLUMNS` to limit captured columns.                                 | Exclude `password`, `token` fields.   |

---
### **3.2 Event Payload Schema (JSON)**
CDC events are emitted as JSON with the following structure:

```json
{
  "schema": "public.users",
  "type": "INSERT|UPDATE|DELETE",
  "timestamp": "2023-10-01T12:00:00Z",
  "transaction_id": "12345",
  "data": {
    "before": { "id": 1, "name": "Alice" },  // For UPDATE/DELETE
    "after": { "id": 1, "name": "Alice Updated" }  // Always present
  },
  "source": {
    "database": "my_db",
    "table": "users",
    "server_id": 1,
    "gtid": "123-456-789"
  }
}
```

---
### **3.3 Filter Configuration (YAML)**
Define filters in `filter.yaml` to exclude tables/columns:

```yaml
tables:
  - include: ["users", "orders"]
    exclude_columns: ["password", "ssn"]
ddl:
  include: ["CREATE TABLE"]  # Exclude DDL by default
transforms:
  - type: "mask"
    columns: ["email", "phone"]
```

---

## **4. Query Examples**

### **4.1 Capturing Changes from MySQL**
Start the adapter with a binlog configuration:

```bash
# Run with Docker (using Debezium MySQL Connector)
docker run -d \
  --name mysql-cdc \
  -e MYSQL_USER=debezium \
  -e MYSQL_PASSWORD=dbz \
  -p 3306:3306 \
  mysql:8.0

# Initialize Debezium Connector
docker run -d \
  --link mysql-cdc:mysql \
  confluentinc/cp-debezium-server \
  --config.file=/etc/debezium/connect-mysql.properties
```

---
### **4.2 Filtering Specific Tables**
Configure `filter.yaml` to capture only `users` table:

```yaml
tables:
  - include: ["users"]
```

Then restart the adapter. Only `users` table changes will be emitted.

---
### **4.3 Transforming Data**
Add transformations to flatten nested JSON or mask PII:

```yaml
transforms:
  - type: "flatten"
    fields: ["address.*"]
  - type: "mask"
    columns: ["credit_card"]
```

Example input/output:
```json
# Input (from MySQL)
{
  "address": { "city": "NY", "zip": "10001" }
}
# Output (after transform)
{
  "address_city": "NY",
  "address_zip": "10001"
}
```

---
### **4.4 Consuming Events via Kafka**
Publish events to a Kafka topic:

```java
// Java Consumer Example
Properties props = new Properties();
props.put("bootstrap.servers", "localhost:9092");
props.put("group.id", "mysql-cdc-group");

KafkaConsumer<String, String> consumer = new KafkaConsumer<>(props);
consumer.subscribe(Collections.singletonList("mysql.public.users"));

while (true) {
  ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
  for (ConsumerRecord<String, String> record : records) {
    System.out.println("Event: " + record.value());
  }
}
```

---
### **4.5 Handling Schema Changes**
For DDL events (e.g., `ALTER TABLE`):

```sql
-- Example: Add a column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
```

The adapter emits a schema change event:
```json
{
  "type": "DDL",
  "sql": "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
  "timestamp": "2023-10-01T12:05:00Z"
}
```

**Note:** Manually reconcile schema changes in downstream systems.

---

## **5. Error Handling & Troubleshooting**

| **Issue**                     | **Cause**                                      | **Solution**                                  |
|--------------------------------|------------------------------------------------|-----------------------------------------------|
| **Missing Events**             | GTID/position mismatch.                        | Reset adapter position: `SET GLOBAL binlog_row_image = 'FULL'` |
| **Duplicate Events**           | Replayed binlog or misconfigured tracker.      | Enable `debounce: true` in config.           |
| **Schema Mismatch**            | Downstream schema differs from source.        | Use `schema_registry` for Avro/Protobuf.      |
| **High Latency**               | Slow consumer or network bottlenecks.         | Increase consumer parallelism.               |
| **Permission Denied**          | MySQL user lacks `REPLICATION SLAVE` rights.   | Grant: `GRANT REPLICATION SLAVE ON *.* TO 'user'@'%';` |

---

## **6. Related Patterns**

### **6.1 Data Pipeline Patterns**
| **Pattern**               | **Description**                                                                                     | **Use Case**                                  |
|---------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **Event Sourcing**        | Store state as a sequence of events.                                                            | Audit trails, replayability.                 |
| **CQRS**                  | Separate read/write models.                                                                         | High-performance queries.                     |
| **Schema Registry**       | Centralized schema management for Avro/Protobuf.                                                 | Cross-system compatibility.                   |
| **Idempotent Consumers**   | Process events exactly-once despite retries.                                                      | Exactly-once semantics.                       |

---
### **6.2 Integration Patterns**
| **Pattern**               | **Adapter Example**                                                                               | **Tools**                                      |
|---------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------|
| **Kafka Connect**         | Use Debezium MySQL Connector for Kafka integration.                                               | `debezium-connector-mysql`                     |
| **HTTP Webhooks**         | Push events to REST endpoints (e.g., Slack, Zapier).                                             | `http-server` (Express.js)                    |
| **Change Data Capture + ML**| Train models on real-time data streams.                                                          | TensorFlow + Kafka Streams                     |
| **Multi-Active Replication**| Sync MySQL with PostgreSQL/Redis via CDC.                                                        | `pg_bouncer`, `redis-om`                       |

---
### **6.3 Advanced Topics**
- **Cross-Data Center CDC**: Use **MySQL Group Replication** + adapter for global sync.
- **Debezium vs. Custom Adapter**: Compare Debezium’s pre-built connectors vs. lightweight custom solutions.
- **Performance Tuning**: Adjust `binlog_cache_size` and `binlog_row_image` for high-throughput setups.

---

## **7. Reference Links**
- [MySQL Binlog Documentation](https://dev.mysql.com/doc/refman/8.0/en/binary-log.html)
- [Debezium MySQL Connector](https://debezium.io/documentation/reference/connectors/mysql.html)
- [Kafka Streams API](https://kafka.apache.org/documentation/streams/)
- [Schema Registry (Confluent)](https://docs.confluent.io/platform/current/schema-registry/index.html)

---
**Note:** This guide assumes MySQL 8.0+. For older versions, adjust `binlog_row_image` settings.