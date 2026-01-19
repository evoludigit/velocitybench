---

# ****[Pattern] Streaming Validation Reference Guide**

---

## **1. Overview**
**Streaming Validation** is a real-time data processing pattern that validates input streams (e.g., logs, IoT sensor data, or transaction events) incrementally as they arrive, rather than batch-processing entire datasets. This approach ensures low-latency feedback, minimizes memory usage, and enables early detection of errors or anomalies. Ideal for high-throughput systems, **Streaming Validation** integrates with event-driven architectures, stream processing frameworks (e.g., Kafka Streams, Flink), or serverless functions.

Key benefits:
- **Real-time correctness**: Detects invalid records as they arrive.
- **Scalability**: Processes unbounded data streams efficiently.
- **Fault tolerance**: Isolates failures without halting the entire pipeline.
- **Cost efficiency**: Reduces reprocessing of corrupted data.

---

## **2. Key Concepts**
| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Stream Source**      | The origin of events (e.g., database CDC, Kafka topic, HTTP/gRPC API).                                                                                                                                                |
| **Validation Rule**    | A schema or business logic (e.g., regex, SQL, custom function) applied per record.                                                                                                                                  |
| **Validator**          | A service/component (e.g., function, stateful processor) that enforces rules.                                                                                                                                      |
| **Sink**               | Where validated data is written (e.g., database, S3, another stream).                                                                                                                                          |
| **Error Handling**     | Mechanism to route invalid records (e.g., dead-letter queue, alerting).                                                                                                                                         |
| **State Management**   | Tracking context (e.g., session IDs, cumulative checks) across partitions.                                                                                                                                         |
| **Throughput Bottleneck** | The validator’s speed (TPS) relative to the stream’s arrival rate.                                                                                                                                           |

---

## **3. Schema Reference**
Below are common validation schema fields and their formats. Customize based on your data model.

| **Field**            | **Type**       | **Description**                                                                                                                                                                                                 | **Example**                          |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------|
| `stream_name`        | `string`       | Identifier for the input stream (e.g., `user_logs`, `sensor_readings`).                                                                                                                                           | `"payment_transactions"`             |
| `record_id`          | `UUID`/`string`| Unique identifier for tracing invalid records.                                                                                                                                                              | `"abc123-4567"`                      |
| `payload`            | `JSON`         | Serialized record data (schema-defined).                                                                                                                                                                    | `{"user_id": 123, "amount": 100}`    |
| `validation_rules`   | `array`        | List of rules applied to the payload (see **Rule Formats** below).                                                                                                                                           | `[{"type": "regex", "field": "email", "pattern": "^[^@]+@[^@]+$"}]` |
| `timestamp`          | `ISO8601`      | When the record was generated/processed.                                                                                                                                                                     | `"2023-10-15T12:00:00Z"`             |
| `status`             | `enum`         | `"valid"`, `"invalid"`, or `"pending"` (for async checks).                                                                                                                                                     | `"invalid"`                          |
| `error_codes`        | `array`        | List of validation failures (e.g., `MISSING_FIELD`, `INVALID_FORMAT`).                                                                                                                                          | `["MISSING_FIELD: 'ssn'"]`           |

---

### **Rule Formats**
| **Rule Type**  | **Description**                                                                                                                    | **Example**                                                                                     |
|----------------|------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Schema Check** | Validates payload against a JSON Schema (e.g., OpenAPI, Avro).                                                                     | `{"type": "schema", "schema": { "$ref": "#/definitions/User" }}`                              |
| **Regex**       | Validates string fields against regex patterns.                                                                                  | `{"field": "email", "pattern": "^[^@]+@[^@]+$"}`                                                |
| **SQL**         | Runs SQL queries on the payload (e.g., `SELECT * FROM unnest(payload) WHERE amount > 0`).       | `{"query": "SELECT * FROM unnest(payload) WHERE age >= 18;"}`                                   |
| **Custom Lambda**| Executes a user-defined function (e.g., Python/JavaScript) for complex logic.                                                   | `{"fn": "is_greater_than_18", "args": ["payload.age"]}`                                         |

---

## **4. Implementation Patterns**

### **4.1. Stateless Validation**
**Use Case**: Simple, independent checks (e.g., field presence, regex).
**Example Architecture**:
```
Stream Source → [Validator A] → [Validator B] → Sink
```
- **Validator A**: Checks `payload.user_id` exists (`!isNull(payload.user_id)`).
- **Validator B**: Validates `payload.email` via regex.

**Query Example (Kafka Streams)**:
```java
KStream<String, String> stream = builder.stream("raw-events");
stream.filter((key, value) -> isValidEmail(value.get("email")))
     .to("validated-events");
```

---

### **4.2. Stateful Validation**
**Use Case**: Session-based checks (e.g., transaction totals, rate limiting).
**Example Architecture**:
```
Stream Source → [Stateful Validator] → Sink
```
- **State**: Tracks cumulative values (e.g., `totalSpentPerUser`).
- **Validator**: Rejects if `totalSpent > 1000`.

**Query Example (Apache Flink)**:
```python
# PyFlink: Accumulate spending per user
spending = env.add_source(KafkaSource(...))
          .key_by(lambda x: x["user_id"])
          .map(lambda x: (x["user_id"], {"amount": float(x["amount"])}))
          .process(lambda: StatefulValidator())
```
**Validator Logic** (Pseudocode):
```python
class StatefulValidator:
    def process(self, key, value):
        if self.state.get(key, 0) + value["amount"] > 1000:
            return ("invalid", "exceeds_limit")
        self.state[key] += value["amount"]
        return ("valid", value)
```

---

### **4.3. Async Validation**
**Use Case**: Expensive checks (e.g., fraud detection, external API calls).
**Example Architecture**:
```
Stream Source → [Async Validator] → [Pending Queue] → [Sink]
               ↓
               [Rejection Queue]
```
- **Validator**: Submits checks to a background task (e.g., Celery, AWS Lambda).
- **Timeout**: Moves to rejection queue if unanswered in 5s.

**Query Example (AWS Lambda)**:
```python
def lambda_handler(event, context):
    record = event["Records"][0]["S3"]["object"]["key"]
    is_valid = call_external_api(record)
    if is_valid:
        s3.put_object(Bucket="valid-data", Key=f"valid/{record}")
    else:
        s3.put_object(Bucket="invalid-data", Key=f"invalid/{record}")
```

---

### **4.4. Dynamic Rules**
**Use Case**: Rules change over time (e.g., A/B testing new validation logic).
**Example**:
- **Ruleset**: Stored in DynamoDB (key: `stream_name`, value: JSON rules).
- **Update**: Triggers validator reload via Kafka signal topic.

**Query Example (Kafka Streams)**:
```java
// Load rules on startup
KTable<String, String> rules = builder.table("validation-rules");

// Reprocess old records if rules change
stream.join(rules, (payload, rule) -> apply_rule(payload, rule))
     .to("validated-events");
```

---

## **5. Query Examples**

### **5.1. Basic Schema Validation (JSON Schema)**
**Input Stream**:
```json
{"user_id": "abc123", "email": "invalid-email", "age": 25}
```
**Rule**:
```json
{
  "type": "object",
  "properties": {
    "email": { "format": "email" },
    "age": { "minimum": 18 }
  },
  "required": ["user_id", "email"]
}
```
**Output**:
```json
{
  "record_id": "abc123",
  "status": "invalid",
  "error_codes": [
    "INVALID_EMAIL: 'invalid-email'",
    "MISSING_FIELD: 'age' is required"
  ]
}
```

---

### **5.2. Rate Limiting (Stateful)**
**Rule**: Reject if >5 requests/minute per IP.
**State Tracking**:
| IP Address | Request Count | Last Reset Time  |
|------------|---------------|------------------|
| `192.168.1.1` | 6             | `2023-10-15T12:01:00Z` |

**Payload**:
```json
{"ip": "192.168.1.1", "action": "purchase"}
```
**Output**:
```json
{
  "status": "invalid",
  "error_codes": ["RATE_LIMIT_EXCEEDED: 6 requests/minute"]
}
```

---

### **5.3. External API Validation**
**Rule**: Call `/api/validate` for `payload.type == "credit_card"`.
**Payload**:
```json
{"type": "credit_card", "number": "4111111111111111", "exp_date": "12/25"}
```
**API Response**:
```json
{"is_valid": false, "reason": "expired"}
```
**Output**:
```json
{
  "status": "invalid",
  "error_codes": ["EXPIRED_CARD: 12/25"]
}
```

---

## **6. Error Handling Strategies**
| **Strategy**               | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Dead-Letter Queue (DLQ)** | Routes invalid records to a separate stream/topic for later inspection.                                                                                                                                       | Critical data where recovery is possible.                                                             |
| **Alerting**               | Triggers a webhook/PagerDuty when validation fails (e.g., `error_rate > 0.1%`).                                                                                                                                 | Monitoring anomalies in real time.                                                                   |
| **Discard**                | Silently drops invalid records (use with caution).                                                                                                                                                            | Non-critical streams (e.g., analytics logs).                                                         |
| **Retry with Backoff**     | Resubmits failed records after exponential backoff (e.g., 1s, 2s, 4s).                                                                                                                                         | Transient failures (e.g., API timeouts).                                                              |
| **API Gateway**            | Uses HTTP status codes (e.g., `400 Bad Request`) to reject clients early.                                                                                                                                       | REST/gRPC APIs with client-side handling.                                                              |

---

## **7. Performance Considerations**
| **Factor**               | **Optimization**                                                                                                                                                                                                 | Tools/Libraries                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Throughput**           | Parallelize validators (e.g., per-shard processing).                                                                                                                                                          | Kafka Streams (parallel KStreams), Flink (parallel operators)                                   |
| **Latency**              | Minimize async call duration (e.g., cache API responses).                                                                                                                                                       | Redis, local in-memory caches                                                                       |
| **State Size**           | Use RocksDB for large state (e.g., Flink’s `StateBackend`).                                                                                                                                                   | Apache Flink (RocksDBStateBackend), Kafka (compacted topics)                                  |
| **Rule Complexity**      | Offload to a microservice if rules are CPU-intensive.                                                                                                                                                         | AWS Lambda, Google Cloud Functions                                                              |
| **Monitoring**           | Track validation latency/pass-fail rates.                                                                                                                                                                       | Prometheus + Grafana, DataDog                                                                       |

---

## **8. Related Patterns**
| **Pattern**                  | **Connection to Streaming Validation**                                                                                                                                                                                                 | Reference Link                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Event Sourcing**           | Validates events before appending to a log (e.g., CQRS).                                                                                                                                                                | [Event Sourcing Docs](https://martinfowler.com/eaaT/)                                           |
| **Circuit Breaker**          | Protects validators from cascading failures (e.g., if external API fails).                                                                                                                                           | [Resilience4j](https://resilience4j.readme.io/docs/circuitbreaker)                              |
| **Data Lakehouse (Iceberg)** | Enforces schema validation on ingested files (e.g., Parquet tables).                                                                                                                                            | [Apache Iceberg](https://iceberg.apache.org/)                                                    |
| **Saga Pattern**             | Validates transactions across services before committing.                                                                                                                                                       | [Saga Pattern](https://microservices.io/patterns/data/saga.html)                               |
| **Schema Registry**          | Centralizes validation schemas (e.g., Confluent Schema Registry).                                                                                                                                                     | [Confluent](https://docs.confluent.io/platform/current/schema-registry/index.html)              |
| **Stream Processing (Kafka/Flink)** | Core frameworks for implementing streaming validation.                                                                                                                                                           | [Kafka Streams](https://kafka.apache.org/documentation/streams/), [Flink](https://flink.apache.org/) |

---

## **9. Anti-Patterns**
| **Anti-Pattern**               | **Problem**                                                                                                                                                                                                   | Mitigation                                                                                           |
|---------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Batch Validation**           | Validates entire batches, delaying feedback.                                                                                                                                                               | Use streaming validation for real-time needs.                                                      |
| **No State Management**        | Duplicate processing of the same record (e.g., retries without idempotency).                                                                                                                               | Use exactly-once semantics (Kafka, Flink).                                                          |
| **Overly Complex Rules**       | Hard-to-maintain logic (e.g., nested SQL in validators).                                                                                                                                                      | Decompose into microservices or use a rule engine (e.g., Drools).                                   |
| **Ignoring Backpressure**      | Validator fails under load (e.g., Lambda throttling).                                                                                                                                                          | Implement backpressure (e.g., Kafka consumer lag, Flink’s `bufferTimeout`).                        |
| **Tight Coupling to Sink**     | Sink failures halt validation.                                                                                                                                                                           | Use async sinks (e.g., SNS + Lambda) or idempotent writes.                                         |

---
**Last Updated**: `2023-10-15`
**Version**: `1.2`