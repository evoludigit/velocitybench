# **Debugging CDC Change Log Fields: A Troubleshooting Guide**

## **Introduction**
Change Data Capture (CDC) with **standard fields** in change logs is critical for tracking modifications in databases, APIs, or event streams. If these fields are misconfigured, corrupted, or missing, applications relying on change tracking may fail.

This guide provides a structured approach to diagnosing and resolving issues with CDC change log fields.

---

## **1. Symptom Checklist**
Before diving into debugging, verify whether the issue matches any of these symptoms:

### **Data Integrity Issues**
- [ ] Missing or incorrect `_id`, `_version`, `_createdAt`, or `_updatedAt` fields in CDC records.
- [ ] Duplicate entries in change logs despite transactions being rolled back.
- [ ] Unexpected timestamp values (e.g., future timestamps, `null` values where expected).

### **Performance & Latency Problems**
- [ ] Slow CDC processing due to large or malformed log entries.
- [ ] Timeouts when querying change logs.

### **Application Behavior Issues**
- [ ] Event-driven systems (e.g., Kafka, RabbitMQ) receiving incomplete or corrupted CDC payloads.
- [ ] Synchronization gaps where changes are lost or duplicated.
- [ ] Applications failing with `NoSuchFieldException` or schema validation errors.

### **Logging & Observability**
- [ ] No or insufficient CDC-related logs in application/error logs.
- [ ] Missing or incorrect metadata in audit logs.

---

## **2. Common Issues & Fixes**

### **Issue 1: Missing or Incorrect `_id` Field**
**Symptom:** Duplicate records or failed deduplication logic.

**Root Cause:**
- The CDC source (DB, Kafka, etc.) does not generate a unique identifier.
- Manual overrides or schema changes removed the `_id` field.

**Fix:**
- **For Databases (PostgreSQL, MySQL, MongoDB):**
  Ensure CDC tools (e.g., Debezium, AWS DMS) correctly capture primary keys.
  ```sql
  -- Example: Verify CDC configuration in Debezium
  SELECT * FROM pg_stat_activity WHERE application_name LIKE '%debezium%';
  ```
- **For Kafka Connect:** Check `value.converter` and `key.converter` settings in the connector config.
  ```json
  {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "localhost",
    "database.port": "5432",
    "database.user": "user",
    "database.password": "pass",
    "database.dbname": "dbname",
    "table.include.list": "orders",
    "key.converter": "org.apache.kafka.connect.storage.StringConverter",
    "value.converter": "io.debezium.converter.ChangeCaptureConverter"
  }
  ```
- **For Custom CDC:** Manually generate `_id` using a UUID:
  ```javascript
  const record = { ...changeData, _id: uuidv4() };
  ```

---

### **Issue 2: Incorrect Timestamps (`_createdAt`, `_updatedAt`)**
**Symptom:** CDC records have wrong or missing timestamps.

**Root Cause:**
- Timezone mismatch between source and CDC pipeline.
- CDC tool not respecting system clock.

**Fix:**
- **For PostgreSQL (Debezium):**
  Ensure `transaction.timeout.ms` and `timestamp.conversion` are set:
  ```json
  "timestamp.conversion": "Strict",
  "transaction.timeout.ms": "180000"
  ```
- **For Custom CDC:** Use UTC timestamps:
  ```javascript
  const updatedAt = new Date().toISOString(); // ISO 8601 format
  ```

---

### **Issue 3: Schema Mismatch in Change Logs**
**Symptom:** Applications fail due to schema validation errors.

**Root Cause:**
- CDC tool emits a different schema than expected.
- Manual modifications to log entries.

**Fix:**
- **Compare Expected vs. Actual Schema:**
  ```bash
  # Example: Check Kafka schema registry for CDC topic
  curl -X GET "http://localhost:8081/subjects/orders-value/versions/latest"
  ```
- **Validate with OpenAPI/Swagger:**
  ```bash
  swagger-validate schema.json log-entry.json
  ```
- **Fix Schema in CDC Tool:**
  ```json
  "transforms": "unwrap",
  "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
  "transforms.unwrap.drop.tombstones": "false"
  ```

---

### **Issue 4: Missing Transaction Metadata (`_version`, `_op`)**
**Symptom:** Changes are not tracked correctly (e.g., `INSERT` vs. `UPDATE`).

**Root Cause:**
- CDC tool not capturing operation type (`c`, `u`, `d` for create/update/delete).
- Custom processing strips transaction metadata.

**Fix:**
- **For Debezium Kafka Connector:**
  Ensure `transforms` are enabled:
  ```json
  "transforms": "wrap,add-source-column",
  "transforms.wrap.type": "io.debezium.transforms.ByLogicNameRoutingTransformer",
  "transforms.add-source-column.type": "org.apache.kafka.connect.transforms.AddField$"
  ```
- **For Custom CDC:**
  Explicitly track operations:
  ```javascript
  const operation = changeType === "INSERT" ? "c" : changeType === "UPDATE" ? "u" : "d";
  logEntry = { ...changeData, _op: operation };
  ```

---

## **3. Debugging Tools & Techniques**

### **A. Database-Level Debugging**
- **Check CDC Logs:**
  ```bash
  # PostgreSQL Debezium logs
  tail -f /var/log/debezium/postgres.log
  ```
- **Verify CDC Capture:**
  ```sql
  -- Check if Debezium is connected
  SELECT * FROM pg_catalog.pg_stat_activity WHERE application_name LIKE '%debezium%';
  ```
- **Use `pg_audit` for PostgreSQL:**
  ```sql
  CREATE EXTENSION pg_audit;
  ALTER SYSTEM SET pg_audit.log = 'all, -misc';
  ```

### **B. Kafka & Event Stream Debugging**
- **Inspect Kafka Topics:**
  ```bash
  # List CDC topic
  kafka-console-consumer --bootstrap-server localhost:9092 --topic dbserver1.public.orders --from-beginning
  ```
- **Check Kafka Connect Workers:**
  ```bash
  # Check connector status
  curl -X GET http://localhost:8083/connectors/
  ```
- **Use `kafkacat` for Debugging:**
  ```bash
  kafkacat -b localhost:9092 -t dbserver1.public.orders -C
  ```

### **C. Application-Level Debugging**
- **Enable Debug Logging:**
  ```properties
  # Logback example
  <logger name="com.your.app.cdc" level="DEBUG"/>
  ```
- **Validate CDC Payloads:**
  ```javascript
  console.log(JSON.stringify(cdcPayload, null, 2));
  ```
- **Use Postman/Insomnia for API Testing:**
  ```bash
  # Test CDC API endpoint
  curl -X POST http://localhost:3000/api/cdc/events -H "Content-Type: application/json" -d @log-entry.json
  ```

---

## **4. Prevention Strategies**

### **A. Schema Management**
- **Use Contract Testing:**
  - **Pact.io** for API CDC compatibility tests.
  - **Avro/Protobuf for Structured Schemas:** Forces strict field definitions.
    ```bash
    # Validate Avro schema
    avro schema -validate schema.avsc cdc-payload.json
    ```

### **B. Monitoring & Alerts**
- **Prometheus + Grafana for CDC Metrics:**
  - Track lag, error rates, and processing time.
  ```yaml
  # Example Prometheus alert
  - alert: HighCDCErrorRate
    expr: rate(cdc_errors_total[5m]) > 10
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High CDC error rate"
  ```

### **C. Automated Testing**
- **Unit Tests for CDC Handlers:**
  ```javascript
  // Example: Test CDC payload parsing
  test('should parse CDC record correctly', () => {
    const payload = { _id: '123', _op: 'c', data: { ... } };
    const parsed = parseCDCRecord(payload);
    expect(parsed).toMatchObject({ ... });
  });
  ```

### **D. Disaster Recovery**
- **Backup CDC Logs:**
  - Store raw CDC logs in S3/Blob Storage.
  ```bash
  # Example: Sync Kafka logs to S3
  /usr/bin/kafka-consumer-groups --bootstrap-server localhost:9092 \
    --group dbserver1.public.orders --topic dbserver1.public.orders \
    --from-beginning | aws s3 cp - s3://your-bucket/cdc-backup/
  ```

### **E. Idempotency in CDC**
- **Use `ETag` or `If-Match` Headers for Replay Safety:**
  ```http
  # Example: Conditional PUT for idempotency
  PUT /api/orders/123 HTTP/1.1
  If-Match: "abc123"
  ```

---

## **5. Conclusion**
CDC change log fields are essential for reliable event-driven systems. By following this guide:
- You can **quickly identify** missing/corrupt fields.
- Apply **fixes** for common issues (missing IDs, timestamps, schema mismatches).
- Use **debugging tools** to inspect logs, Kafka, and database state.
- Implement **prevention strategies** (schema validation, monitoring, testing).

If issues persist, check:
1. **Database transaction logs** (WAL, binlog).
2. **CDC tool documentation** (Debezium, Kafka Connect).
3. **Application dependency graphs** (e.g., `mvn dependency:tree`).

**Final Tip:** Always **back up CDC logs** before major schema changes.

---
**References:**
- [Debezium Documentation](https://debezium.io/documentation/reference/stable/)
- [Kafka Connect Best Practices](https://kafka.apache.org/documentation/#connect_best_practices)
- [OpenTelemetry for CDC Observability](https://opentelemetry.io/docs/)

---
Would you like a deeper dive into any specific tool (e.g., Debezium, Kafka Connect)?