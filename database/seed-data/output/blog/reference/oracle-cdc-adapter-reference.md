# **[Pattern] Oracle Change Data Capture (CDC) Adapter Reference Guide**

---

## **1. Overview**
The **Oracle CDC Adapter** enables real-time data synchronization between an Oracle database and external systems (e.g., data warehouses, streaming platforms, or applications) by efficiently capturing and transmitting incremental changes (INSERTs, UPDATEs, DELETEs). This pattern leverages Oracle’s **flashback data archive (FBD), logical change capture (LCC), or database triggers** to capture changes and forwards them via **Kafka, debris, or direct HTTP/webhooks** to downstream consumers.

For high-throughput systems, Oracle CDC is preferred over batch ETL processes, as it minimizes latency and ensures data consistency.

---
## **2. Key Concepts**
| Concept         | Description |
|-----------------|-------------|
| **Change Data Capture (CDC)** | Mechanism to detect and extract changes (DML operations) from an Oracle database in near real-time. |
| **Logical Change Capture (LCC)** | Oracle’s built-in feature (since 12c) that captures DMLs via **DDL redo logs** (Oracle 12c+) or **flashback data archive (FBA)**. |
| **FBA (Flashback Data Archive)** | Captures historical changes in a separate table; used for point-in-time recovery and CDC. Requires separate storage. |
| **Debezium (Oracle Connector)** | Open-source CDC framework by Red Hat that consumes Oracle redo logs and streams changes to Kafka. |
| **Triggers-Based CDC** | Custom PL/SQL triggers log changes to a staging table; less scalable than LCC but useful for complex logic. |
| **Consumer Topics (Kafka/Debris)** | Kafka topics (e.g., `oracle.db1.changes`) where CDC events are published. |
| **Schema Registry** | Stores schema metadata for downstream consumers (Avro/Protobuf). |

---
## **3. Implementation Approaches**
### **3.1 Oracle LCC (Logical Change Capture)**
**Best for:** High-performance CDC with minimal overhead.

#### **Prerequisites**
- Oracle Database 12c or later.
- **Flashback Data Archive (FBA)** enabled for older versions (11g+).

#### **Steps**
1. **Enable LCC for the database:**
   ```sql
   ALTER DATABASE ADD LOGFILE GROUP logcapture GROUP 1 ('/u01/oradata/orcl/logcapture01.log', 'REDO LOG FILESIZE 100M');
   ALTER DATABASE ADD LOGFILE GROUP logcapture GROUP 2 ('/u01/oradata/orcl/logcapture02.log', 'REDO LOG FILESIZE 100M');
   ALTER DATABASE ADD LOGFILE GROUP logcapture GROUP 3 ('/u01/oradata/orcl/logcapture03.log', 'REDO LOG LOGGING ON');
   ```
2. **Create a logical capture group:**
   ```sql
   BEGIN
     DBMS_LOGCAPTURE.ADD_CAPTURE(
       capture => 'ORA$CAPTURE_ORCL',
       logfile_group_names => 'logcapture',
       options => DBMS_LOGCAPTURE.CAPTURE_ONLINE_LOG | DBMS_LOGCAPTURE.CAPTURE_ONLINE_ARCHIVELOG
     );
     DBMS_LOGCAPTURE.START_CAPTURE(capture => 'ORA$CAPTURE_ORCL');
   END;
   ```
3. **Deploy Debezium Oracle Connector** (for Kafka integration):
   ```yaml
   # connector config (connector.properties)
   name=oracle-cdc-connector
   connector.class=io.debezium.connector.oracle.OracleConnector
   database.hostname=orcl.example.com
   database.port=1521
   database.user=debezium
   database.password=secret
   database.dbname=ORCL
   database.server.name=orcl
   include.schema.changes=false
   ```

#### **Pros/Cons**
| Aspect | Pros | Cons |
|--------|------|------|
| **Performance** | Low latency, high throughput. | Requires Oracle 12c+ or FBA. |
| **Complexity** | Minimal manual tuning. | Debezium setup can be resource-intensive. |

---
### **3.2 Flashback Data Archive (FBA)**
**Best for:** Oracle versions <12c or when LCC is unavailable.

#### **Steps**
1. **Enable FBA:**
   ```sql
   ALTER TABLE employees ADD (FLASHBACK_DATA_ARCHIVE BYTES 10M);
   ```
2. **Capture changes via `FLASHBACK_ARCHIVE_POINTS`:**
   ```sql
   SELECT * FROM FLASHBACK_ARCHIVE_POINTS;
   ```
3. **Query historical data:**
   ```sql
   SELECT * FROM employees AS OF TIMESTAMP (SYSTIMESTAMP - INTERVAL '1' DAY);
   ```
4. **Forward changes to a staging table** (e.g., via triggers or batch jobs).

#### **Pros/Cons**
| Aspect | Pros | Cons |
|--------|------|------|
| **Compatibility** | Works with older Oracle versions. | Higher storage overhead. |
| **Latency** | Slightly higher than LCC. | Requires manual synchronization. |

---
### **3.3 Triggers-Based CDC**
**Best for:** Custom logic or on-premises environments without Debezium.

#### **Example Implementation**
1. **Create a CDC staging table:**
   ```sql
   CREATE TABLE cdc_events (
     event_id NUMBER GENERATED ALWAYS AS IDENTITY,
     table_name VARCHAR2(100),
     operation VARCHAR2(10),
     operation_timestamp TIMESTAMP,
     old_data JSON,
     new_data JSON
   );
   ```
2. **Add AFTER INSERT/UPDATE/DELETE triggers:**
   ```sql
   CREATE OR REPLACE TRIGGER trg_employees_insert
   AFTER INSERT ON employees
   FOR EACH ROW
   BEGIN
     INSERT INTO cdc_events (table_name, operation, new_data)
     VALUES ('EMPLOYEES', 'INSERT', to_jsonb(row_to_json(row())));
   END;
   ```
3. **Poll the staging table** and forward changes via HTTP/webhooks.

#### **Pros/Cons**
| Aspect | Pros | Cons |
|--------|------|------|
| **Flexibility** | Full control over CDC logic. | Higher maintenance. |
| **Scalability** | Limited by trigger performance. | Not ideal for high-volume tables. |

---

## **4. Schema Reference**
### **4.1 Oracle CDC Event Schema (Debezium Format)**
| Field          | Type       | Description |
|----------------|------------|-------------|
| `source`       | Object     | Metadata (e.g., `version`, `connector`, `ts_ms`). |
| `header`       | Object     | Event header (e.g., `x-minimal-endpoint` for Kafka). |
| `payload`      | Object     | Change payload. |
| `payload.before` | JSON/NULL | Pre-change row data. |
| `payload.after`  | JSON     | Post-change row data. |
| `payload.op`    | String    | `c` (create), `u` (update), `d` (delete). |
| `payload.source` | Object | Table metadata (`table`, `db`, `schema`). |

**Example Payload:**
```json
{
  "source": { "version": "1.0", "connector": "oracle", "name": "orcl" },
  "header": { "x-minimal-endpoint": "https://example.com/api" },
  "payload": {
    "before": null,
    "after": { "id": 100, "name": "John Doe" },
    "op": "c",
    "source": { "table": "EMPLOYEES", "schema": "HR" }
  }
}
```

### **4.2 Staging Table Schema (Triggers-Based)**
| Column          | Data Type   | Description |
|-----------------|-------------|-------------|
| `event_id`      | NUMBER      | Auto-incrementing ID. |
| `table_name`    | VARCHAR2(100)| Source table name. |
| `operation`     | VARCHAR2(10)| `INSERT`, `UPDATE`, `DELETE`. |
| `operation_ts`  | TIMESTAMP   | When the change occurred. |
| `old_data`      | JSON        | Pre-change row (NULL for INSERT). |
| `new_data`      | JSON        | Post-change row (NULL for DELETE). |

---

## **5. Query Examples**
### **5.1 Debezium Kafka Query (KSQL)**
```sql
-- List all changes for the 'employees' table
SELECT *
FROM ORCL.HR__EMPLOYEES
EMIT CHANGES;
```

### **5.2 Oracle SQL Query (FBA)**
```sql
-- Find all updates to 'employees' in the last hour
SELECT * FROM employees AS OF TIMESTAMP (SYSTIMESTAMP - INTERVAL '1' HOUR)
MINUS
SELECT * FROM employees AS OF TIMESTAMP (SYSTIMESTAMP - INTERVAL '2' HOUR);
```

### **5.3 Staging Table Query (Triggers-Based)**
```sql
-- Get all INSERTs for 'employees' in the last 5 minutes
SELECT new_data
FROM cdc_events
WHERE table_name = 'EMPLOYEES'
  AND operation = 'INSERT'
  AND operation_timestamp > SYSTIMESTAMP - INTERVAL '5' MINUTE;
```

---

## **6. Deployment Architecture**
```
[Oracle DB] ----[Debezium/CDC Connector]----> [Kafka/Debris]
       ▲                                       ▲
       │                                       │
[LCC/FBA]                                   [Consumer App]
       │                                       │
       └──────────────────────────────────────► [Sink: Snowflake/Redshift]
```

---
## **7. Error Handling & Monitoring**
| Issue               | Solution |
|---------------------|----------|
| **Consumer Lag**    | Scale Kafka partitions or increase Debezium workers. |
| **Schema Drift**    | Use Debezium’s schema registry to auto-update schemas. |
| **Failed Events**   | Implement dead-letter queues (DLQ) for retries. |
| **Performance Bottlenecks** | Monitor `V$LOGCAPTURE` and `V$ARCHIVESTAT` views. |

**Key Metrics to Track:**
- **Debezium:** `checkpoint_lag` (ms), `errors`.
- **Oracle:** `lochcapture.lag` (seconds), `redo log wait time`.

---
## **8. Related Patterns**
| Pattern               | Purpose |
|-----------------------|---------|
| **[Kafka Connect Debezium](https://debezium.io/)** | CDC framework for streaming changes to Kafka. |
| **[CDC + Sink Connector](https://github.com/confluentinc/kafka-connect-s3)** | Export CDC events to S3/HDFS. |
| **[Oracle GoldenGate](https://www.oracle.com/database/goldengate/)** | Enterprise-grade CDC with high availability. |
| **[Triggers + Webhooks](https://cloud.google.com/eventarc)** | Custom CDC with HTTP targets. |
| **[Change Data Capture with Snowflake](https://docs.snowflake.com/en/user-guide/change-data-capture-intro)** | Snowflake-native CDC for warehousing. |

---
## **9. Best Practices**
1. **Batch Size:** Use Debezium’s `batch.size` (default: 2048) to balance latency/throughput.
2. **Schema Evolution:** Enable Debezium’s `include.schema.changes=true` for schema updates.
3. **Security:** Encrypt Kafka messages (SSL) and restrict Debezium credentials.
4. **Testing:** Validate CDC with `debizium-test-container` for isolated testing.
5. **Fallback:** Use triggers for critical tables if LCC fails.

---
## **10. Troubleshooting**
| Problem               | Check |
|-----------------------|-------|
| **No changes in Kafka** | Verify `DBMS_LOGCAPTURE.STATUS` for LCC. |
| **Debezium connector down** | Check `kafka-connect-oracle-connector.log`. |
| **High redo log usage** | Monitor `V$LOGFILE` and adjust loggroup sizes. |
| **Schema mismatch**   | Compare `schema.registry` with downstream consumers. |

---
## **11. References**
- [Oracle Logical Change Capture](https://docs.oracle.com/en/database/oracle/oracle-database/19/upgfg/logical-change-capture.html)
- [Debezium Oracle Connector](https://debezium.io/documentation/reference/stable/connectors/oracle.html)
- [Kafka Connect Documentation](https://kafka.apache.org/documentation/#connect)

---
**End of Document** (Word count: ~950)