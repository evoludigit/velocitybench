# **[Pattern] CDC Event Testing Reference Guide**

---

## **Overview**
The **CDC (Change Data Capture) Event Testing** pattern automates the validation of data synchronization across systems by capturing, replaying, and testing changes in a controlled environment. This pattern ensures that event-driven architectures, ETL pipelines, or database replication remain accurate over time by simulating real-world change scenarios.

Key benefits:
- **Automated validation** of CDC feeds without manual testing.
- **Isolation** of edge cases (e.g., concurrent updates, partial failures).
- **Reproducibility** of test scenarios using historical data snapshots.
- **Performance benchmarking** of event processing pipelines.

This pattern is ideal for **data engineers**, **devops teams**, and **test automation engineers** managing systems where **event sourcing**, **stream processing**, or **microservices** rely on CDC for consistency.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| Component          | Description                                                                                     |
|--------------------|-------------------------------------------------------------------------------------------------|
| **CDC Provider**   | Source system emitting change events (e.g., PostgreSQL logical decoding, Kafka connectors).    |
| **Event Store**    | Persistent log of CDC events (e.g., CDC-optimized DB table, Kafka topic, or change data stream).|
| **Test Harness**   | Framework to replay events, inject failures, and validate outcomes (e.g., custom scripts, TestContainers, or tools like **Debezium Test Container**). |
| **Sink Systems**   | Targets receiving CDC events (e.g., data warehouse, microservices, or secondary databases).      |
| **Validation Layer**| Mechanisms to assert correctness (e.g., checksums, row-count comparisons, or business logic checks). |

---

### **2. Architecture Flow**
1. **Capture**: The CDC provider records changes from the source system (e.g., inserts, updates, deletes) into an event store.
2. **Replay**: The test harness replays events in a controlled environment (e.g., staging database or mock sink).
3. **Validate**: The system verifies the sink’s state matches expectations (e.g., using assertions or audit checks).
4. **Inject Faults (Optional)**: Simulate failures (e.g., network timeouts, schema mismatches) to test resilience.

---
### **3. Test Scenarios**
| Scenario Type          | Description                                                                                     | Example Use Case                                                                 |
|------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Replay Validation**  | Replay historical events to confirm accurate synchronization.                                    | Verify a data warehouse reflects all CDC updates from the last 30 days.            |
| **Concurrency Testing**| Test handling of simultaneous changes (e.g., race conditions).                                  | Simulate 1,000 concurrent users updating records in a PostgreSQL table via Debezium. |
| **Failure Injection**  | Introduce deliberate failures (e.g., schema drift, sink downtime) to validate recovery.          | Test if the CDC pipeline retries failed inserts automatically.                     |
| **Partial Data Checks**| Validate specific fields or relationships after CDC applies changes.                            | Ensure `customer_id` and `order_total` match across source and sink after an update. |
| **Performance Benchmarking** | Measure latency or throughput under load.                                                     | Benchmark how many events/second the sink can process with 99% uptime.              |

---

## **Schema Reference**
Below are common schemas for CDC event testing.

### **1. CDC Event Schema (Source)**
| Field               | Type          | Description                                                                                     | Example Value                     |
|---------------------|---------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `event_id`          | UUID          | Unique identifier for the change event.                                                       | `550e8400-e29b-41d4-a716-446655440000` |
| `source_system`     | String        | Name of the source system (e.g., `postgres_db`, `sales_microservice`).                         | `postgres_db`                     |
| `event_type`        | Enum          | Type of operation (`insert`, `update`, `delete`).                                               | `update`                          |
| `table_name`        | String        | Name of the affected table.                                                                    | `customers`                       |
| `timestamp`         | Timestamp     | When the change occurred in the source.                                                       | `2023-10-01 14:30:00 UTC`        |
| `payload`           | JSON          | Key-value pairs of changed data (varies by table).                                             | `{"id": 101, "name": "Alice"}`    |
| `previous_payload`  | JSON          | Data *before* the change (for `update`/`delete`).                                              | `{"id": 101, "name": "Bob"}`      |
| `metadata`          | JSON          | Optional context (e.g., user who made the change, transaction ID).                              | `{ "user": "admin123" }`          |

---
### **2. Validation Check Schema (Sink)**
| Field               | Type          | Description                                                                                     | Example Value                     |
|---------------------|---------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| `sink_table`        | String        | Name of the validated table in the sink system.                                               | `customers_validated`             |
| `expected_row`      | JSON          | Pre-computed expected state after CDC applies the event.                                       | `{"id": 101, "name": "Alice"}`    |
| `actual_row`        | JSON          | Fetched row from the sink for comparison.                                                     | `{"id": 101, "name": "Alice"}`    |
| `checksum`          | String        | Hash of the row for quick validation (e.g., MD5 of JSON serialization).                       | `a1b2c3...`                      |
| `validation_status` | Boolean       | `true` if `actual_row` matches `expected_row`; `false` otherwise.                             | `true`                            |
| `error_message`     | String        | If validation fails, details of the discrepancy.                                               | `"Name mismatch: expected 'Alice', got 'Bob'"` |

---

## **Query Examples**
Below are SQL and tool-specific examples for CDC event testing.

---

### **1. Querying CDC Events from a Source Database**
Assume a CDC-optimized table (`cdc_events`) logs changes from `customers`:

```sql
-- Fetch all "update" events for the `customers` table in the last hour
SELECT *
FROM cdc_events
WHERE table_name = 'customers'
  AND event_type = 'update'
  AND timestamp > NOW() - INTERVAL '1 hour';
```

---
### **2. Validating Sink Data Against CDC Events**
Compare a sink table (`customers_sink`) with expected changes:

```sql
-- Validate that the sink reflects a specific update event
WITH expected_data AS (
  SELECT payload AS expected_row
  FROM cdc_events
  WHERE event_id = '550e8400-e29b-41d4-a716-446655440000'
)
SELECT
  c.*,
  (SELECT expected_row FROM expected_data) AS expected_row,
  CASE WHEN c.name = (SELECT expected_row->>'name' FROM expected_data)
       THEN 'PASS'
       ELSE 'FAIL'
  END AS validation_status
FROM customers_sink c
WHERE c.id = (SELECT payload->>'id' FROM expected_data);
```

---
### **3. Testing with Debezium (Kafka Connect)**
Use the Debezium Test Container to replay events via Kafka:

```bash
# Start a Debezium test container for PostgreSQL
docker run -d --name debezium-test -p 8083:8083 \
  confluentinc/debezium-test-container:1.9 \
  --providers org.postgresql \
  --bootstrapServers localhost:9092 \
  --brokerPort 9092 \
  --postgresHost postgres-db \
  --postgresPort 5432 \
  --postgresUser postgres \
  --postgresPassword postgres \
  --postgresDb postgres \
  --postgresTable customers

# Replay events from Kafka to validate
docker exec debezium-test kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic postgres.public.customers \
  --from-beginning \
  --formatter 'kafka.json.JSONFormatter' \
  --property print.keys=true \
  | jq 'select(.op =="u")' > updates.json
```

---
### **4. Fault Injection in a Pipeline**
Simulate a network failure between CDC provider and sink:

```python
# Python script to drop Kafka partitions (using Confluent Kafka)
from confluent_kafka.admin import AdminClient

config = {'bootstrap.servers': 'localhost:9092'}
admin = AdminClient(config)

# Drop the partition for topic "postgres.public.customers" (partition 0)
admin.delete_topics(['postgres.public.customers'], operation_timeout=10)
print("Partition dropped. Testing retry logic...")
```

---
### **5. Performance Benchmarking**
Use `kafka-producer-perf-test` to measure throughput:

```bash
# Measure messages/sec for a CDC topic
kafka-producer-perf-test \
  --topic postgres.public.customers \
  --num-records 10000 \
  --throughput -1 \
  --record-size 100 \
  --producer-props bootstrap.servers=localhost:9092
```

---

## **Related Patterns**
| Pattern                     | Description                                                                                     | When to Use                                                                                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **[Event Sourcing]**        | Stores state changes as a sequence of immutable events.                                           | When you need a full audit trail of system state changes.                                         |
| **[Data Mesh]**             | Decentralizes data ownership with domain-driven pipelines.                                        | For large-scale organizations with multiple data producers.                                      |
| **[Schema Registry]**       | Centralizes schema governance for avro/protobuf events.                                          | When CDC events use complex nested schemas (e.g., Avro).                                        |
| **[Idempotent Consumer]**   | Ensures duplicate events don’t cause side effects.                                               | For unreliable CDC consumers (e.g., microservices with timeouts).                                 |
| **[Backpressure Handling]** | Dynamically controls event flow to avoid sink overload.                                          | When the sink can’t keep up with the CDC event rate.                                             |

---
## **Best Practices**
1. **Isolate Tests**: Use separate environments (e.g., TestContainers) to avoid polluting production data.
2. **Idempotency**: Design tests to handle duplicate events (e.g., using transaction IDs).
3. **Reproducibility**: Seed databases with known states before running tests.
4. **Monitoring**: Log validation failures and integrate with CI/CD (e.g., failure = build block).
5. **Incremental Testing**: Prioritize testing recent CDC events over historical ones.
6. **Tooling**: Leverage libraries like:
   - **Debezium** for CDC capture.
   - **TestContainers** for isolated test environments.
   - **Apache Beam** for replaying events in a dataflow job.

---
## **Troubleshooting**
| Issue                          | Root Cause                          | Solution                                                                                     |
|--------------------------------|-------------------------------------|-----------------------------------------------------------------------------------------------|
| **Validation Fails**           | Sink data doesn’t match source.      | Check for schema drift, parsing errors, or missing events in the CDC log.                    |
| **Slow Test Execution**        | Large replay volume.                | Filter events by date range or sample a subset.                                             |
| **Kafka Consumer Lag**         | Sink is slower than producer.        | Scale consumers or increase partition count.                                                 |
| **False Positives**            | Race conditions in validation.      | Use transactional outbox pattern or retry failed checks.                                      |

---
## **Example Workflow**
1. **Setup**:
   - Deploy a staging PostgreSQL DB with Debezium capturing `customers` table changes.
   - Set up a Kafka topic (`postgres.public.customers`) and a mock sink (e.g., Redis).

2. **Test Execution**:
   ```bash
   # Inject sample data into the source
   psql -d staging_db -c "INSERT INTO customers (id, name) VALUES (1, 'Alice');"

   # Replay events to the sink (via Debezium)
   kafka-avro-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic postgres.public.customers \
     --property schema.registry.url=http://schema-registry:8081 \
     --from-beginning \
     | avro-console-consumer --print-data-log \
     | python3 validate_sink.py
   ```

3. **Validation**:
   - The script `validate_sink.py` queries Redis and asserts `customers` data matches the event payload.

4. **Failure Injection**:
   - Kill the Redis consumer process mid-test to verify retry logic.

---
## **Further Reading**
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/)
- [TestContainers for Kafka](https://www.testcontainers.org/modules/drivers/kafka/)
- [Event Sourcing Patterns](https://martinfowler.com/eaaDev/EventSourcing.html)
- [CDC Patterns (InfoQ)](https://www.infoq.com/articles/cdc-patterns/)