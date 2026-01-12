# **[Pattern] CDC (Change Data Capture) Event Filtering Reference Guide**

---

## **Overview**
CDC (Change Data Capture) Event Filtering is a **pattern** for selectively subscribing to only the events of interest from a stream of changes in a database or event source. Instead of consuming all changes (e.g., inserts, updates, deletes) from a CDC feed, this pattern allows applications to **filter events** based on specified criteria—such as entity type, record attributes, or business logic conditions—reducing noise, latency, and resource consumption.

This guide covers:
- Key concepts and use cases for event filtering
- Schema definitions for filtering rules
- Implementation examples in common CDC tools (Debezium, Kafka Streams, etc.)
- Best practices for performance and scalability

---

## **Key Concepts**

| Concept               | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| **CDC Feed**          | A stream of change events (e.g., `INSERT`, `UPDATE`, `DELETE`) emitted from a database.      |
| **Event Filter**      | A rule or predicate applied to filter events before subscription.                               |
| **Source Table**      | The database table emitting CDC events (e.g., `customers`, `orders`).                          |
| **Target Queue/Topic**| Where filtered events are routed (e.g., Kafka topic, RabbitMQ queue).                           |
| **Filter Context**    | Metadata available per event (e.g., `table_name`, `operation_type`, `record_key`).             |
| **Dynamic Filtering** | Filters that adapt based on runtime conditions (e.g., user permissions, A/B testing flags).   |

---
## **Schema Reference**

### **1. Core Filtering Schema**
Filters are defined using a **JSON-like schema** (adapted for CDC tools like Debezium/Kafka). Key fields:

| Field                | Type               | Description                                                                                     | Required |
|----------------------|--------------------|-------------------------------------------------------------------------------------------------|----------|
| `table_name`         | `string`           | Name of the source table (e.g., `"orders"`).                                                     | Yes       |
| `operation_type`     | `string` (enum)    | `INSERT`, `UPDATE`, `DELETE`, or `TRUNCATE`.                                                     | No        |
| `record_key`         | `string`           | Primary key of the changed record (e.g., `"order_id"`).                                          | No        |
| `payload`            | `object`           | The changed record’s fields (dynamic per table).                                               | Yes       |
| `metadata`           | `object`           | Contextual data (e.g., `{ source: "db", timestamp: "2024-01-01" }`).                           | No        |

---

### **2. Filter Expression Syntax**
Filters use a **predicate-based** syntax (similar to SQL `WHERE` clauses). Supported operators:

| Operator       | Example                          | Description                                                                 |
|----------------|----------------------------------|-----------------------------------------------------------------------------|
| `==`           | `payload.status == "active"`     | Equality check.                                                              |
| `!=`           | `payload.user_id != null`        | Not equal.                                                                  |
| `in`           | `payload.country in ["US", "CA"]`| Membership test.                                                              |
| `>=`, `<=`     | `payload.amount >= 100`           | Numeric/date comparisons.                                                    |
| `regex`        | `payload.email ~ /.*@gmail.com/` | Regex matching on strings.                                                   |
| `and`, `or`    | `payload.active and payload.type == "premium"` | Boolean logic.                     |

**Example Filter Rule:**
```json
{
  "table_name": "orders",
  "operation_type": ["INSERT", "UPDATE"],
  "predicate": {
    "and": [
      { "payload.status": { "==": "active" } },
      { "payload.amount": { ">": 50 } }
    ]
  }
}
```

---

### **3. Filter Metadata Fields**
Additional fields for advanced filtering:

| Field               | Description                                                                                     |
|---------------------|-------------------------------------------------------------------------------------------------|
| `source_version`    | Version of the CDC source (e.g., Debezium offset).                                             |
| `schema_name`       | Database schema (if applicable).                                                              |
| `event_time`        | Timestamp of the change (useful for windowed filtering).                                       |

---

## **Implementation Examples**

---

### **1. Debezium Filtering (Kafka Connect)**
Debezium allows filtering in **connectors** (e.g., `mysql-connector`, `postgres-connector`) using:
- **Connector Configs**:
  ```properties
  transformers=filter
  filter.pattern=.*\\.(customers|products).*
  ```
- **Kafka Streams Filter**:
  ```java
  StreamsBuilder builder = new StreamsBuilder();
  builder.stream("raw-cdc-topic")
    .filter((key, value) -> {
      var payload = (JsonNode) value.get("payload");
      return payload.path("status").asText().equals("active");
    })
    .to("filtered-orders");
  ```

---

### **2. Kafka Streams (Server-Side)**
Use **`filter()`** or **`process()`** with a custom predicate:
```java
KStream<String, String> cdcStream = builder.stream("cdc-topic");
cdcStream.filter((key, value) ->
    value.contains("\"table_name\":\"orders\"")
)
.filter((key, value) -> {
    ObjectMapper mapper = new ObjectMapper();
    JsonNode json = mapper.readTree(value);
    return json.path("payload").path("status").asText().equals("active");
})
.to("filtered-orders");
```

---

### **3. SQL-Based Filtering (Debezium + Flink SQL)**
Flink SQL can filter CDC data:
```sql
CREATE TABLE filtered_orders (
  `key` STRING,
  `value` STRING,
  `topic` STRING,
  `partition` INT,
  `offset` LONG
) WITH (
  'connector' = 'kafka',
  'topic' = 'raw-cdc',
  'format' = 'json'
);

INSERT INTO target_orders
SELECT key, value
FROM filtered_orders
WHERE PARSE_JSON(value).payload.status = 'active';
```

---

### **4. Dynamic Filtering (Runtime Conditions)**
For **context-aware filtering** (e.g., user permissions), use:
- **Kubernetes Sidecars**: Inject filters based on pod metadata.
- **Envoy Proxy**: Route events via runtime config (e.g., Istio).
- **Custom Interceptors**: Modify events in transit (e.g., Spring Cloud Stream).

**Example (Spring Cloud Stream):**
```java
@Bean
public Function<Source<JsonNode, Void>, Sinks.Many<JsonNode>> filterOrders() {
    return source -> {
        Sinks.Many<JsonNode> sink = Sinks.many().unicast();
        source.subscribe()
            .doOnNext(json -> {
                if (json.path("payload").path("table").asText().equals("orders")) {
                    sink.emitNext(json.filter(status -> status.asText().equals("active")));
                }
            });
        return sink.asStep();
    };
}
```

---

## **Best Practices**

### **1. Performance Considerations**
- **Push vs. Pull Filtering**:
  - *Push*: Filter at source (Debezium connector) to reduce network traffic.
  - *Pull*: Filter in consumers (Kafka Streams) for flexibility.
- **Indexing**: Ensure filtered fields are indexed in the database (e.g., `WHERE status = 'active'`).
- **Batch Processing**: Aggregate filters for high-throughput topics.

### **2. Scalability**
- **Partitioning**: Distribute filters across Kafka partitions to parallelize.
- **Stateful Filters**: Use `KeyValueStore` in Kafka Streams for stateful predicates.

### **3. Debugging**
- **Logging**: Log filtered-out events for troubleshooting.
- **Metrics**: Track filter hit rates (e.g., Prometheus metrics).
- **Unit Testing**: Test filters in isolation (e.g., JUnit + Mockito for Kafka Streams).

### **4. Dynamic Filter Updates**
- **Hot Reloading**: Use tools like **Confluent Schema Registry** to update filters without downtime.
- **Feature Flags**: Toggle filters via config (e.g., LaunchDarkly).

---

## **Query Examples**

---

### **Example 1: Filter Active Users**
**Filter Rule:**
```json
{
  "table_name": "users",
  "operation_type": ["INSERT", "UPDATE"],
  "predicate": {
    "payload.is_active": { "==": true }
  }
}
```
**Kafka Streams Implementation:**
```java
cdcStream.filter((key, value) -> {
    JsonNode json = new ObjectMapper().readTree(value);
    return json.path("payload").path("is_active").asBoolean();
});
```

---

### **Example 2: Route High-Value Orders**
**Filter Rule:**
```json
{
  "table_name": "orders",
  "operation_type": ["INSERT"],
  "predicate": {
    "payload.amount": { ">": 1000 }
  }
}
```
**Debezium Connector Config:**
```properties
transforms=route
route.topic.regex=orders-(.*)  # Routes to topic "orders-highvalue"
route.key.headers.enable=true
route.headers.add=X-Filtered=true
```

---

### **Example 3: Exclude Soft-Deleted Records**
**Filter Rule:**
```json
{
  "table_name": "products",
  "operation_type": ["UPDATE", "DELETE"],
  "predicate": {
    "or": [
      { "payload.is_deleted": { "==": false } },
      { "metadata.operation": { "==": "DELETE" } }
    ]
  }
}
```
**Flink SQL:**
```sql
SELECT *
FROM products_cdc
WHERE NOT (payload.is_deleted AND operation = 'UPDATE');
```

---

### **Example 4: Time-Based Filtering**
Filter events older than **24 hours**:
```json
{
  "table_name": "*",
  "predicate": {
    "metadata.event_time": {
      ">": "2024-01-01T00:00:00Z"
    }
  }
}
```
**Kafka Streams:**
```java
cdcStream.filter((key, value) -> {
    Instant timestamp = Instant.parse(value.get("metadata.event_time"));
    return timestamp.isAfter(Instant.parse("2024-01-01T00:00:00Z"));
});
```

---

## **Related Patterns**

| Pattern                          | Description                                                                                     | When to Use                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[CDC Debezium Connector]**     | Captures database changes via Debezium (supports PostgreSQL, MySQL, etc.).                   | When integrating relational databases with Kafka/streaming pipelines.       |
| **[Event Sourcing]**             | Stores state changes as a sequence of events (CDF).                                            | For audit logs, replayable systems, or domain-driven design.                |
| **[Kafka Streams Processing]**   | Processes streams with stateful operations (e.g., aggregations, joins).                       | When deriving insights from CDC data (e.g., real-time dashboards).         |
| **[Schema Registry]**           | Manages event schemas (Avro/Protobuf) for backward compatibility.                              | To ensure consumers parse events correctly over time.                       |
| **[Dead Letter Queue (DLQ)]**   | Routes failed/filtered events to a separate topic/queue for inspection.                       | For handling malformed or unprocessable events.                           |
| **[Canary Releases]**            | Gradually filters traffic to test new features (e.g., 10% of active users).                  | For A/B testing or experimenting with new filters.                         |

---

## **Troubleshooting**

| Issue                          | Solution                                                                                     |
|--------------------------------|---------------------------------------------------------------------------------------------|
| **High Latency**               | Optimize filters (e.g., push filtering at source).                                          |
| **Missing Events**             | Check connector offsets (Debezium) or consumer groups (Kafka).                               |
| **Schema Mismatches**          | Use Schema Registry or validate schemas in consumers.                                       |
| **Dynamic Filter Failures**    | Isolate filter logic (e.g., use Spring Cloud Config for dynamic configs).                  |
| **Overloaded Topics**          | Split filtered streams into multiple topics (e.g., `orders-highvalue`, `orders-lowvalue`). |

---

## **Tools & Libraries**
| Tool/Library               | Use Case                                                                                     |
|----------------------------|------------------------------------------------------------------------------------------------|
| **Debezium**               | CDC connectors for databases (PostgreSQL, MySQL, etc.).                                     |
| **Kafka Streams**          | Stateful stream processing with filters.                                                     |
| **Apache Flink**           | Advanced stream processing (windowing, joins).                                              |
| **Spring Cloud Stream**    | Java-based stream processing with CDC support.                                               |
| **Confluent Schema Registry**| Manages Avro/Protobuf schemas for CDC events.                                               |
| **Prometheus + Grafana**   | Monitor filter performance (e.g., drop rates).                                              |

---
## **Further Reading**
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/)
- [Kafka Streams Filtering Guide](https://kafka.apache.org/documentation/streams/developer-guide/)
- [CDC Patterns: Event Filtering (Martin Fowler)](https://martinfowler.com/eaaCatalog/ChangeDataCapture.html)