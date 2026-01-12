# **[Pattern] Audit Optimization Reference Guide**

---

## **Overview**
The **Audit Optimization** pattern minimizes performance overhead and reduces storage costs in audit logging systems while maintaining compliance and forensic traceability. By optimizing audit data collection, storage, and retrieval, this pattern ensures that systems track necessary changes efficiently, without sacrificing auditability or security.

Key benefits include:
- **Reduced resource consumption** (CPU, storage, I/O) during audit logging.
- **Faster query performance** via indexing, filtering, and selective logging.
- **Cost efficiency** by compressing or archiving older audit data.
- **Selective logging** to focus on critical events (e.g., data modifications, role changes) rather than low-risk operations.

This guide covers implementation strategies, schema design, query optimization, and related patterns to achieve a balanced approach between audit granularity and system performance.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Selective Logging**     | Only log high-impact events (e.g., `INSERT`, `UPDATE`, `DELETE` on sensitive tables, role assignments) while omitting trivial operations (e.g., `SELECT`, minor configuration changes).                     |
| **Delta Logging**         | Store only changes (deltas) rather than full records. Useful for large datasets where tracking every transaction would be prohibitively expensive.                                                           |
| **Data Compression**      | Compress audit logs (e.g., gzip, Snappy) to reduce storage footprint. Balance between CPU overhead during compression and storage savings.                                                                      |
| **Partitioning**          | Split audit tables by time (e.g., monthly/weekly partitions) or event type to improve query performance and simplify archival.                                                                                  |
| **Indexing Strategies**   | Optimize indexes for common query patterns (e.g., `WHERE timestamp BETWEEN ...` or `WHERE user_id = ...`). Avoid over-indexing to prevent write performance degradation.                                    |
| **Archival Policies**     | Automatically move or purge old logs (e.g., logs older than 90 days) to cold storage (S3, Glacier) or delete them after retention periods, while retaining critical data for compliance.                     |
| **Event Filtering**       | Use middleware or database triggers to filter out irrelevant events (e.g., batch jobs, automated backups) before they are logged.                                                                           |
| **Sampling**              | For high-volume systems, log a sample of events (e.g., 1% of transactions) to reduce load while maintaining statistical accuracy for forensic analysis.                                                     |
| **Encryption**            | Encrypt sensitive audit data at rest (e.g., using AES-256) and in transit (TLS) to protect against unauthorized access.                                                                                            |
| **Log Consolidation**     | Aggregate logs from multiple sources (e.g., microservices, databases) into a centralized repository (e.g., ELK Stack, Splunk) to reduce redundancy and simplify analysis.                                   |

---

## **Schema Reference**

Below are optimized database schema examples for audit logging. Adjust fields based on your compliance requirements (e.g., GDPR, HIPAA, SOX).

### **1. Core Audit Table (PostgreSQL Example)**
```sql
CREATE TABLE audit_logs (
    log_id                 BIGSERIAL PRIMARY KEY,
    event_timestamp        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type             VARCHAR(50) NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE', 'ROLE_CHANGE', etc.
    table_name             VARCHAR(100) NOT NULL,
    record_id              BIGINT,               -- ID of the affected record (NULL for system events)
    old_values             JSONB,                -- Only for UPDATE/DELETE (stores pre-change data)
    new_values             JSONB,                -- Only for INSERT/UPDATES (stores post-change data)
    user_id                VARCHAR(255),         -- User or system account triggering the event
    user_ip                INET,                 -- Source IP (if applicable)
    action_details         JSONB,                -- Additional metadata (e.g., {'query': 'UPDATE users SET ...', 'duration_ms': 120})
    is_sensitive           BOOLEAN DEFAULT FALSE -- Flag for highly regulated data (e.g., PII)
) PARTITION BY RANGE (event_timestamp);
```

**Partitioning Strategy:**
```sql
-- Monthly partitions (example for 2023)
CREATE TABLE audit_logs_y2023m01 PARTITION OF audit_logs
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

CREATE TABLE audit_logs_y2023m02 PARTITION OF audit_logs
    FOR VALUES FROM ('2023-02-01') TO ('2023-03-01');
-- Repeat for each month/quarter.
```

---

### **2. Index Recommendations**
| **Index**                          | **Purpose**                                                                                     | **Use Case**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `CREATE INDEX idx_audit_timestamp`  | Speeds up time-range queries (e.g., "Show logs from last 7 days").                              | Compliance reviews, forensic analysis.                                                          |
| `CREATE INDEX idx_audit_user_id`     | Faster lookups by user (e.g., "Audit all actions by user X").                                  | Account activity monitoring.                                                                    |
| `CREATE INDEX idx_audit_table_name` | Quick filtering by table (e.g., "Audit changes to `users` table").                             | Table-specific audits.                                                                         |
| `CREATE INDEX idx_audit_event_type`  | Filter logs by event type (e.g., only `DELETE` operations).                                     | Event-specific investigations.                                                                  |
| **GIN Index for JSONB**             | Accelerate queries on `old_values` or `new_values` (e.g., "Find logs where email was changed").| Complex filter requirements.                                                                    |

---

### **3. Supporting Tables**
| **Table**               | **Purpose**                                                                                     | **Example Fields**                                                                              |
|-------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `audit_user_mapping`    | Maps user IDs to human-readable names (for readability in logs).                                 | `user_id`, `display_name`, `department`, `role`                                              |
| `audit_archive_logs`    | Stores compressed/archived older logs (e.g., >90 days).                                         | `log_id`, `compressed_data` (BLOB), `archive_timestamp`                                       |
| `audit_exclusion_rules` | Defines events to exclude (e.g., batch jobs, automated scripts).                                | `event_pattern` (regex), `is_excluded` (BOOLEAN)                                              |

---

## **Query Examples**

### **1. Retrieve Recent Logs (Optimized)**
```sql
-- Fetch latest 100 logs with indexing on event_timestamp
SELECT
    log_id,
    event_timestamp,
    event_type,
    table_name,
    user_id,
    display_name,
    action_details->>'query' AS query_executed
FROM audit_logs
JOIN audit_user_mapping ON user_id = user_id
WHERE event_timestamp >= NOW() - INTERVAL '7 days'
ORDER BY event_timestamp DESC
LIMIT 100;
```

### **2. Query Sensitive Data Changes**
```sql
-- Find all updates to PII fields in the 'users' table
SELECT
    event_timestamp,
    user_id,
    display_name,
    table_name,
    old_values->>'email' AS old_email,
    new_values->>'email' AS new_email
FROM audit_logs
WHERE
    table_name = 'users'
    AND event_type = 'UPDATE'
    AND is_sensitive = TRUE
    AND new_values->>'email' IS NOT NULL
ORDER BY event_timestamp DESC;
```

### **3. Bulk Audit for Compliance (Partitioned)**
```sql
-- Aggregate audit data for SOX compliance (example: 2023 Q2)
SELECT
    table_name,
    COUNT(*) AS change_count,
    SUM(CASE WHEN event_type = 'DELETE' THEN 1 ELSE 0 END) AS delete_count
FROM audit_logs_y2023m04, audit_logs_y2023m05, audit_logs_y2023m06
GROUP BY table_name;
```

### **4. Exclude Irrelevant Events (Using Exclusion Rules)**
```sql
-- Log only critical events (ignore batch jobs)
SELECT *
FROM audit_logs
WHERE
    event_type NOT IN (
        SELECT event_pattern
        FROM audit_exclusion_rules
        WHERE is_excluded = TRUE
    )
    AND table_name NOT IN ('temp_data', 'cache');
```

### **5. Archive Old Logs Automatically**
```sql
-- Move logs older than 90 days to archive table (PostgreSQL example)
INSERT INTO audit_archive_logs (log_id, compressed_data)
SELECT
    log_id,
    pg_compress(to_jsonb(log_id || '|' || event_timestamp || '|' || event_type || '|' || table_name))
FROM audit_logs
WHERE event_timestamp < NOW() - INTERVAL '90 days';
```

---

## **Implementation Strategies**

### **1. Database-Level Optimization**
- **Use `ON UPDATE`/`ON DELETE` triggers** to log changes automatically (e.g., PostgreSQL `AFTER INSERT/UPDATE/DELETE` triggers).
  ```sql
  CREATE OR REPLACE FUNCTION log_user_changes()
  RETURNS TRIGGER AS $$
  BEGIN
      INSERT INTO audit_logs (
          event_type, table_name, record_id, old_values, new_values, user_id
      ) VALUES (
          TG_OP, TG_TABLE_NAME, NEW.id,
          row_to_json(OLD), row_to_json(NEW), current_user
      );
      RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trg_log_users
  AFTER INSERT OR UPDATE OR DELETE ON users
  FOR EACH ROW EXECUTE FUNCTION log_user_changes();
  ```
- **Leverage database-native JSON support** (e.g., PostgreSQL `JSONB`) for flexible schema without schema migrations.

### **2. Application-Level Logging**
- **Filter events in the application** before logging:
  ```python
  # Pseudocode: Filter out low-impact events
  if event.event_type in ['SELECT', 'LIST']:
      return  # Skip logging
  if event.table_name in ['temp_data']:
      return  # Skip logging

  # Log only critical changes
  audit_logs.insert({
      'event_type': event.event_type,
      'table_name': event.table_name,
      'old_values': old_record.to_dict(),
      'new_values': new_record.to_dict(),
      'user_id': current_user.id
  })
  ```
- **Use async logging** to avoid blocking application performance:
  ```python
  # Example with Python + RQ
  from rq import Queue
  q = Queue(connection='redis://localhost:6379')
  q.enqueue(call='log_audit_event', event_data=event)
  ```

### **3. Storage Optimization**
- **Compress logs** during ingestion or at rest:
  ```sql
  -- Example: Compress JSON logs before storing in PostgreSQL
  INSERT INTO audit_logs_compressed (compressed_data)
  SELECT pg_compress(to_jsonb(log_data))
  FROM audit_logs;
  ```
- **Partition tables by time** (as shown in the schema) to limit full-table scans.

### **4. Monitoring and Retention**
- **Set up automated retention policies** (e.g., AWS Lambda, PostgreSQL `pg_cron`):
  ```sql
  -- Example: Delete logs older than 180 days in monthly partitions
  DO $$
  DECLARE
      partition_name TEXT;
  BEGIN
      FOR partition_name IN
          SELECT tablename
          FROM pg_tables
          WHERE tablename LIKE 'audit_logs_y%'
          AND tablename < 'audit_logs_y' || EXTRACT(YEAR FROM NOW()) || 'm' || EXTRACT(MONTH FROM NOW())
      LOOP
          EXECUTE format('DELETE FROM %I WHERE event_timestamp < NOW() - INTERVAL ''%s''', partition_name, '180 days');
      END LOOP;
  END $$;
  ```
- **Monitor log volume** and adjust sampling rates dynamically:
  ```sql
  -- Alert if log volume exceeds threshold (e.g., 1M rows/day)
  SELECT COUNT(*) FROM audit_logs
  WHERE event_timestamp >= NOW() - INTERVAL '1 day';
  ```

---

## **Performance Considerations**

| **Action**                          | **Impact**                                  | **Mitigation**                                                                                     |
|-------------------------------------|---------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Full-table scans**                 | Slow queries on large audit tables.         | Use partitioning, indexing, and `WHERE` clauses to avoid scans.                                    |
| **Large JSONB storage**             | High I/O and memory usage.                  | Compress JSONB data or sample high-volume fields (e.g., store only checksums of large blobs).     |
| **High-frequency triggers**         | Database bottlenecks.                       | Batch inserts (e.g., queue logs and insert in batches of 1000) or use CDC (Change Data Capture). |
| **Over-indexing**                    | Slower writes.                              | Limit indexes to columns frequently queried; use partial indexes (e.g., `WHERE is_sensitive = TRUE`). |
| **Network latency** (distributed)    | Slow cross-service logging.                 | Log locally first, then sync to centralized storage asynchronously.                               |

---

## **Related Patterns**

### **1. Change Data Capture (CDC)**
- **Purpose**: Track database changes in real-time for audit and replication.
- **Tools**: Debezium, AWS DMS, PostgreSQL logical decoding.
- **When to Use**: If you need low-latency audit trails for distributed systems or real-time analytics.

### **2. Event Sourcing**
- **Purpose**: Store all state changes as a sequence of immutable events.
- **When to Use**: For systems requiring full auditability (e.g., financial transactions) or complex replay capabilities.
- **Tradeoff**: Higher storage costs and complexity compared to traditional audit logging.

### **3. Sparse Auditing**
- **Purpose**: Log only changes to critical fields (e.g., PII) rather than entire records.
- **Implementation**: Use triggers with conditional logic to log only high-value fields:
  ```sql
  CREATE OR REPLACE FUNCTION sparse_audit()
  RETURNS TRIGGER AS $$
  BEGIN
      IF TG_TABLE_NAME = 'users' AND (OLD.email IS DISTINCT FROM NEW.email OR OLD.password_hash IS DISTINCT FROM NEW.password_hash) THEN
          INSERT INTO audit_logs (event_type, table_name, record_id, old_values, new_values)
          VALUES (TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
      END IF;
      RETURN NEW;
  END;
  $$;
  ```

### **4. Audit Log Encryption at Rest**
- **Purpose**: Protect sensitive audit data from unauthorized access.
- **Tools**: PostgreSQL TDE (Transparent Data Encryption), AWS KMS, or application-level encryption.
- **Key Management**: Use HSMs (Hardware Security Modules) or cloud KMS for key storage.

### **5. Audit Log Centralization**
- **Purpose**: Aggregate logs from multiple services into a single repository.
- **Tools**: ELK Stack, Splunk, Datadog, or custom solutions with Kafka/Flume.
- **Optimization**: Use log sampling or filtering at the ingestion layer to reduce volume.

### **6. Time-Based Retention Policies**
- **Purpose**: Automatically purge or archive old logs to reduce storage costs.
- **Implementation**:
  - **Database**: Use `pg_cron` (PostgreSQL) or AWS Lambda to delete old partitions.
  - **Cloud**: Leverage S3 lifecycle policies or Elasticsearch retention settings.
- **Compliance Note**: Ensure policies align with legal requirements (e.g., GDPR’s 6-month retention for some data).

---

## **Anti-Patterns to Avoid**

| **Anti-Pattern**                  | **Why It’s Bad**                                                                                     | **Alternative**                                                                                     |
|-----------------------------------|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| **Logging everything**            | High storage costs, performance overhead, and noise in critical investigations.                     | Use selective logging (e.g., only log `UPDATE DELETE` on critical tables).                        |
| **No partitioning**               | Full-table scans slow down queries as the audit table grows.                                        | Partition by time or event type (e.g., monthly partitions).                                         |
| **Uncompressed logs**             | Wastes storage space and increases I/O latency.                                                     | Compress logs (e.g., `pg_compress` in PostgreSQL) or use columnar storage (e.g., Parquet).       |
| **No indexing**                   | Slow queries for common audit scenarios (e.g., "Show all changes by user X").                        | Index frequently queried columns (e.g., `user_id`, `event_timestamp`).                              |
| **Blocking writes for logging**   | Degrades application performance during high-volume operations.                                      | Use async logging (queues, background workers) or batch inserts.                                    |
| **Ignoring retention policies**    | Risk of missing compliance deadlines or excessive storage costs.                                     | Automate archival/deletion (e.g., PostgreSQL `pg_cron`, AWS S3 lifecycle).                        |
| **Over-encrypting logs**           | Adds CPU overhead without significant security benefit.                                             | Encrypt only highly sensitive fields (e.g., PII) or use column-level encryption in the database.  |

---

## **Tools and Technologies**
| **Category**               | **Tools**                                                                                          | **Use Case**                                                                                     |
|----------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Database**               | PostgreSQL, MySQL, MongoDB, Cassandra                                                               | Store structured audit logs with partitioning/indexing.                                         |
| **Log Management**         | ELK Stack (Elasticsearch, Logstash, Kibana), Splunk, Datadog                                  | Centralize, search, and visualize logs.                                                          |
| **Stream Processing**      | Apache Kafka, AWS Kinesis, RabbitMQ                                                            | Handle high-volume audit events asynchronously.                                                 |
| **CDC (Change Data Capture)** | Debezium, AWS DMS, PostgreSQL logical decoding                                                    | Capture database changes in real-time for auditing.                                               |
| **Encryption**             | AWS KMS, PostgreSQL TDE, HashiCorp Vault                                                          | Protect audit data at rest and in transit.                                                       |
| **Sampling/Filtering**     | Logstash filters, Fluentd, custom middleware                                                     | Red