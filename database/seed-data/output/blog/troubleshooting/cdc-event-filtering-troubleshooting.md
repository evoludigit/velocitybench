# **Debugging CDC Event Filtering: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) is a mechanism to capture and process database changes (inserts, updates, deletes) in real time. **Filtering CDC events** ensures that only relevant changes are routed to downstream consumers, improving efficiency and reducing noise. This guide helps you debug common issues with CDC event filtering.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms to narrow down the problem:

| **Symptom** | **Description** |
|-------------|----------------|
| **Too many events processed** | Unfiltered CDC events flood consumers. |
| **Missed events** | Some relevant events bypass filters. |
| **Performance degradation** | Filtering logic is too slow, delaying consumers. |
| **Incorrect event routing** | Events are sent to wrong subscribers. |
| **Consistency issues** | Filtered events sometimes include stale data. |
| **Deadlocks/timeout errors** | Subscribers time out waiting for events. |
| **Duplicate events** | Same event processed multiple times. |

If any of these are present, proceed with debugging.

---

## **2. Common Issues & Fixes**

### **Issue 1: Events Not Filtered Properly**
**Symptom:** All CDC events are processed, regardless of business logic.
**Cause:**
- Filter logic is misconfigured (e.g., `WHERE` clause missing in SQL-based filtering).
- Filter key mismatches between source and sink.
- CDC stream is not partitioned correctly.

#### **Debugging Steps:**
1. **Verify filter criteria**
   Ensure the filter condition matches the schema and business rules.
   Example (Debezium/Kafka Connect):
   ```json
   // MySQL CDC Source Config (Debezium)
   {
     "value.converter": "io.debezium.connector.mysql.MysqlValueConverter",
     "key.converter": "org.apache.kafka.connect.storage.StringConverter",
     "transforms": "dropNonStructuredPayload",
     "transforms.dropNonStructuredPayload.type": "org.apache.kafka.connect.transforms.DropNonStructuredPayload$KeyValueFilter"
   }
   ```
   If using **Debezium’s `filter.field`**, ensure it matches:
   ```json
   "transforms": "filter",
   "transforms.filter.type": "org.apache.kafka.connect.transforms.FilterField$",
   "transforms.filter.blacklist": "id,deleted,createdAt"
   ```

2. **Check schema compatibility**
   If filtering by a column (e.g., `user_id`), ensure the column name matches:
   ```sql
   -- Correct filter in CDC config
   WHERE user_id IN (100, 200)
   ```

3. **Test locally**
   Use a small test dataset and verify filtering:
   ```bash
   # Example: Kafka Consumer Test
   kafka-console-consumer --bootstrap-server localhost:9092 --topic dbserver1.mysql.table.orders --from-beginning --formatter kafka.tools.DefaultMessageFormatter --property print.key=true
   ```

---

### **Issue 2: Performance Bottlenecks**
**Symptom:** Filtering slows down CDC processing, causing delays.
**Cause:**
- Complex filtering logic (e.g., nested conditions).
- Large payloads being processed in-memory.
- Blocking I/O operations inside filters.

#### **Debugging Steps:**
1. **Profile the filtering logic**
   Use JVM profilers (e.g., **VisualVM, JFR**) to identify slow methods:
   ```java
   // Example: Avoid heavy computations in CDC filters
   @Override
   public boolean filter(StreamRecord record) {
       // Bad: Expensive DB call inside filter
       // new ExternalService().isValid(record.value());

       // Good: Pre-filter with lightweight checks
       return record.key().equals("valid_key");
   }
   ```

2. **Optimize queries**
   If using database filters (e.g., **Debezium’s `database.history`: "mysqlbinarylog"), ensure indexes exist:
   ```sql
   CREATE INDEX idx_user_id ON users(user_id);
   ```

3. **Use Kafka Streams for filtering**
   Offload filtering to Kafka Streams for better performance:
   ```java
   StreamsBuilder builder = new StreamsBuilder();
   builder.stream("dbserver1.mysql.table.orders")
          .filter((key, value) -> ((JsonObject)value).getString("status").equals("active"));
   ```

---

### **Issue 3: Duplicate Events**
**Symptom:** Same event appears multiple times in the stream.
**Cause:**
- Debezium’s `only.dataset.changes` mode misconfigured.
- Transaction retries in the CDC source.
- Consumer lag causing reprocessing.

#### **Debugging Steps:**
1. **Check Debezium’s CDC mode**
   Ensure `only.dataset.changes` is set to `false` if duplicates are expected:
   ```json
   "only.dataset.changes": true  // Default: false
   ```

2. **Enable CDC source debug logging**
   Increase logging for Debezium:
   ```properties
   # Debezium connector logs
   log4j.logger.org.apache.kafka.connect.runtime=DEBUG
   log4j.logger.io.debezium=DEBUG
   ```

3. **Use Kafka consumer offsets**
   Ensure consumers don’t reprocess from the same offset:
   ```java
   consumer.seek(TopicPartition, offset); // Avoid manual seeks
   ```

---

### **Issue 4: Incorrect Event Routing**
**Symptom:** Events go to the wrong Kafka topic/subscriber.
**Cause:**
- Mismatch between CDC source topic and sink.
- Dynamic topic naming not handled.
- Incorrect `key` or `value` serialization.

#### **Debugging Steps:**
1. **Verify topic naming**
   Check if Debezium’s topic suffix matches expectations:
   ```json
   # Default: dbserver1.mysql.table.<table_name>
   "transforms": "route",
   "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
   "transforms.route.regex": ".*\\.(orders|invoices)",
   "transforms.route.replacement": "$1"
   ```

2. **Test with `kafka-console-producer`**
   Manually send a test event and verify routing:
   ```bash
   echo '{"name":"test","status":"active"}' | kafka-console-producer --topic dbserver1.mysql.table.users --bootstrap-server localhost:9092
   ```

3. **Check Kafka ACLs & Partitions**
   Ensure topics exist and consumers can access them:
   ```bash
   kafka-topics --list --bootstrap-server localhost:9092
   kafka-consumer-groups --describe --group my-group --bootstrap-server localhost:9092
   ```

---

### **Issue 5: Filtering Not Applied to New Events**
**Symptom:** New database changes bypass filters.
**Cause:**
- CDC connector restarted without reapplying filters.
- New Debezium offset not handled correctly.

#### **Debugging Steps:**
1. **Check Debezium’s `log.min.poll.interval.ms`**
   Ensure it’s not too aggressive:
   ```json
   "log.min.poll.interval.ms": 1000  # Default: 100ms
   ```

2. **Verify offset commit behavior**
   Ensure offsets are committed after filtering:
   ```java
   // In Kafka Streams
   KStream<Key, Value> filteredStream = stream.filter(...);
   filteredStream.to("filtered-topic", Produced.with(...));
   ```

3. **Restart connector with correct config**
   If filters were changed, restart the connector (Debezium/Kafka Connect):
   ```bash
   kafka-connect restart <connector-name>
   ```

---

## **3. Debugging Tools & Techniques**

### **A. Kafka Tools**
| **Tool** | **Purpose** |
|----------|------------|
| `kafka-consumer-groups` | Check consumer offsets and lag. |
| `kafka-topics` | Verify topic existence and partitions. |
| `kafka-console-consumer` | Inspect raw events. |
| **Kafka REST Proxy** | Query topics via API. |

**Example Command:**
```bash
# Check consumer lag
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-group

# Inspect a topic
kafka-console-consumer --topic dbserver1.mysql.table.orders --from-beginning
```

### **B. Logging & Monitoring**
- **Debezium Metrics:**
  ```sh
  kafka-connect plugins --list  # Verify connector is running
  kafka-connect connectors      # Check status
  ```
- **Prometheus + Grafana:**
  Monitor `kafka.connect.offset.lag` and `debezium.offset.lag`.

### **C. Static Analysis**
- **Check CDC Schema:**
  ```bash
  curl http://localhost:8083/connectors/<connector-name>/status
  ```
- **Validate SQL Filters:**
  Run a test query manually:
  ```sql
  SELECT * FROM users WHERE id IN (1, 2);
  ```

---

## **4. Prevention Strategies**

### **A. Design Best Practices**
1. **Use idempotent consumers**
   Ensure consumers can handle duplicates gracefully.
2. **Partition CDC topics**
   Avoid hot partitions by key distribution.
3. **Test with `kafka-avro-console-consumer`**
   For Avro payloads:
   ```bash
   kafka-avro-console-consumer --topic dbserver1.mysql.table.users --bootstrap-server localhost:9092 --property schema.registry.url=http://localhost:8081
   ```

### **B. Configuration Tips**
- **Debezium:**
  ```json
  "transforms": "unwrap",
  "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState"
  ```
- **Kafka Streams:**
  ```java
  StreamsConfig config = new StreamsConfig(props);
  config.put(StreamsConfig.CACHE_MAX_BYTES_BUFFERING, 1024 * 1024 * 2); // 2MB
  ```

### **C. Automated Testing**
- **Unit Test Filters:**
  ```java
  @Test
  public void testEventFilter() {
      StreamRecord<String, String> record = new StreamRecord<>(
          "test-key", "{\"id\": 1, \"name\": \"test\"}"
      );
      assertTrue(new MyFilter().filter(record));
  }
  ```
- **Integration Test CDC Pipeline:**
  Use **Testcontainers** for Kafka/Debezium:
  ```java
  DockerContainer kafka = DockerContainer.fromImage("confluentinc/cp-kafka");
  DebeziumServer debezium = new DebeziumServer(kafka);
  ```

---

## **5. Next Steps**
| **Action** | **When to Take** |
|------------|----------------|
| Restart connector | Filter config changed. |
| Check logs | New errors appear. |
| Optimize queries | Performance degradation. |
| Update schema | New fields added. |
| Review ACLs | Permissions denied. |

---

## **Conclusion**
CDC event filtering is critical for scalable event-driven architectures. By following this guide, you can:
✅ **Identify misconfigured filters**
✅ **Optimize performance bottlenecks**
✅ **Debug routing issues**
✅ **Prevent duplicates and stale data**

If issues persist, check **Debezium’s documentation** (`docs.debezium.io`) and **Kafka’s issue tracker** (`github.com/apache/kafka`).