---

# **[Pattern] Streaming Migration Reference Guide**

---

## **Overview**
The **Streaming Migration** pattern enables seamless data migration by processing records in real-time (or near-real-time) from a source system to a target system. Unlike batch migrations, which transfer large datasets at once, this pattern handles data incrementally—one record, event, or file chunk at a time—reducing downtime, improving reliability, and allowing for parallel processing. It is ideal for large-scale databases, event-driven architectures, and systems requiring continuous synchronization (e.g., legacy-to-cloud migrations or microservice transitions).

Key benefits:
- **Low latency**: Minimizes disruption by processing data continuously.
- **Fault tolerance**: Recovers from failures by reprocessing only failed records.
- **Scalability**: Handles high-throughput systems via parallel streams or distributed pipelines.
- **Idempotency**: Supports replayable operations to ensure correctness after failures.

---

## **Schema Reference**

| **Component**          | **Description**                                                                                                                                                                                                 | **Example Payload**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Source Stream**      | The data source (e.g., database table, message queue, file, or CDC feed) emitting records for migration. Must support incremental reads (e.g., via timestamps, IDs, or offsets).                            | `{ "schema": "orders", "operation": "insert/update", "data": { "order_id": 123, "status": "shipped" } }` |
| **Stream Processor**   | A middleware layer (e.g., Apache Kafka, AWS Kinesis, or Flink) that buffers, partitions, and ensures ordered processing of records.                                                                                  | `partition_key: order_id, timestamp: 1625097600000`                                                      |
| **Change Data Capture (CDC)** | A mechanism (e.g., Debezium, AWS DMS, or logical replication) to capture only incremental changes from the source database.                                                                                   | `{ "before": {}, "after": { "user_id": 456, "name": "Updated Name" }, "op": "update" }`                 |
| **Target Writer**      | The system receiving migrated data (e.g., cloud database, NoSQL store, or Kafka topic). Must support idempotent writes (e.g., via primary keys or UUIDs).                                                      | `POST /api/customers/456 { "id": 456, "name": "Updated Name" }`                                        |
| **Metadata Tracker**   | A store (e.g., database table or DynamoDB) tracking processed records to avoid duplicates, retry failed jobs, and resume from checkpoints.                                                                          | `{ "stream": "orders", "offset": 1000, "status": "completed", "last_updated": "2024-01-15T12:00:00Z" }` |
| **Error Handling**     | A queue (e.g., SQS, RabbitMQ) or dead-letter topic for failed records, with retry logic and alerts.                                                                                                              | `{ "record": { "order_id": 789 }, "error": "ConstraintViolation", "retries": 3 }`                      |
| **Validation Layer**   | Optional rules (e.g., schema validation, business logic checks) to filter or transform records before writing to the target.                                                                                       | `if (order.total > 10000) { apply_tax(); }`                                                             |

---

## **Implementation Details**

### **1. Core Workflow**
1. **Capture Changes**: Use CDC or incremental reads to emit records from the source.
2. **Stream Records**: Send records to a stream processor (e.g., Kafka) with unique offsets/keys.
3. **Process & Validate**: Transform, filter, or validate records (e.g., using Apache Beam or Spark).
4. **Write to Target**: Persist records to the target system with idempotency checks.
5. **Track Progress**: Log offsets/IDs in the metadata tracker to resume from failures.
6. **Handle Errors**: Route failed records to a dead-letter queue for retry or manual review.

### **2. Key Considerations**
- **Idempotency**: Ensure target writes are retriable (e.g., `INSERT ... ON CONFLICT` in PostgreSQL).
- **Ordering**: Use partition keys (e.g., `user_id`) to maintain event sequence if required.
- **Throughput**: Scale streams horizontally (e.g., Kafka partitions) or use batching for large payloads.
- **Schema Evolution**: Handle schema drift by versioning payloads or using polymorphic schemas.
- **Monitoring**: Track latency, error rates, and throughput via Prometheus or CloudWatch.

### **3. Example Architectures**
- **Database-to-Cloud**:
  `PostgreSQL (Debezium) → Kafka → Flink (validation) → DynamoDB (target)`
- **Event-Driven Migration**:
  `S3 (CSV files) → AWS Kinesis → Lambda (transform) → Snowflake`
- **Microservice Sync**:
  `Database (CDC) → RabbitMQ → Service B (processing) → Service C (target)`

---

## **Query Examples**

### **1. CDC Setup (Debezium Example)**
```sql
-- Capture changes in a PostgreSQL table for streaming
CREATE TABLE orders (
    order_id BIGSERIAL PRIMARY KEY,
    customer_id INT,
    amount DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE
);

-- Configure Debezium connector:
{
  "name": "orders-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "db-source",
    "database.port": "5432",
    "database.user": "user",
    "database.password": "password",
    "database.dbname": "retail",
    "table.include.list": "public.orders"
  }
}
```

### **2. Streaming Query (Kafka + SQL)**
```sql
-- Query Kafka topic for recent orders (using Kafka SQL)
SELECT
  order_id,
  customer_id,
  amount,
  ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at) as order_seq
FROM retail_orders
WHERE created_at > '2024-01-01'
EMIT CHANGES;
```

### **3. Target Upsert (PostgreSQL)**
```sql
-- Idempotent upsert using PostgreSQL's ON CONFLICT
INSERT INTO target_orders (order_id, customer_id, amount)
VALUES (EXCLUDED.order_id, EXCLUDED.customer_id, EXCLUDED.amount)
ON CONFLICT (order_id) DO UPDATE
SET
    amount = EXCLUDED.amount,
    updated_at = CURRENT_TIMESTAMP;
```

### **4. Dead-Letter Queue (SQS)**
```python
# Process failed records from SQS (Python example)
import boto3

sqs = boto3.client('sqs')
queue_url = 'https://sqs.region.amazonaws.com/1234567890-dlq'

def reprocess_failed_orders():
    response = sqs.receive_message(QueueUrl=queue_url)
    for message in response.get('Messages', []):
        record = json.loads(message['Body'])
        if record['retries'] < 3:
            retry_write(record['data'])
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
        else:
            alert_admin(record)
```

---

## **Related Patterns**
1. **Batch Migration**:
   - Use for one-time, offline migrations where real-time constraints are relaxed.
   - *Difference*: Processes entire datasets at once; no streaming overhead.

2. **Change Data Capture (CDC)**:
   - Focuses on capturing incremental database changes (e.g., Debezium, AWS DMS).
   - *Complements*: Streaming Migration relies on CDC to feed the stream.

3. **Event Sourcing**:
   - Stores historical state changes as a sequence of events.
   - *Use case*: Combine with Streaming Migration for immutable audit trails.

4. **CQRS (Command Query Responsibility Segregation)**:
   - Separates read (streaming queries) and write (target updates) models.
   - *Synergy*: Streaming Migration aligns with CQRS’s eventual consistency needs.

5. **Canary Migration**:
   - Gradually shifts traffic from source to target while monitoring.
   - *Hybrid*: Use Streaming Migration to sync data *before* traffic shift.

6. **Backpressure Handling**:
   - Manages stream overload (e.g., Kafka consumer lag, target throttling).
   - *Tools*: Dynamic scaling, buffering, or circuit breakers.

7. **Schema Registry**:
   - Tracks evolving schemas (e.g., Avro, Protobuf) for source/target compatibility.
   - *Critical*: Essential when schemas change mid-migration.

---

## **Tools & Technologies**
| **Category**          | **Options**                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **CDC**               | Debezium, AWS Database Migration Service, PostgreSQL Logical Decoding       |
| **Streaming Platforms** | Apache Kafka, AWS Kinesis, Pulsar, Google Pub/Sub                          |
| **Processors**        | Apache Flink, Apache Spark Streaming, AWS Kinesis Data Analytics           |
| **Metadata Tracking** | Database table, DynamoDB, Elasticsearch, ZooKeeper                         |
| **Error Handling**    | SQS, RabbitMQ, Dead-Letter Topics, Retry Policies                          |
| **Monitoring**        | Prometheus + Grafana, AWS CloudWatch, Datadog                              |

---
**Note**: For large-scale migrations, consider pairing Streaming Migration with **blue-green deployments** or **feature flags** to minimize risk. Always validate data integrity post-migration.