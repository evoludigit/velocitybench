# **[Pattern] CDC (Change Data Capture) Change Log Fields Reference Guide**

---

## **Overview**
This pattern defines a **standardized set of fields** for tracking changes in Change Data Capture (CDC) logs. These fields ensure consistency across systems when monitoring, auditing, or transforming CDC records. The pattern applies to both event-based (real-time) and batch-based CDC pipelines.

Key benefits include:
- **Unified schema** for cross-system compatibility.
- **Auditability** via standardized metadata.
- **Efficient querying** (e.g., filtering by temporal or entity-specific changes).
- **Compatibility** with tooling like Kafka Connect, Debezium, or custom CDC pipelines.

This guide covers **mandatory and optional fields**, schema examples, and practical query patterns.

---

## **Schema Reference**

| **Field Name**       | **Type**       | **Description**                                                                 | **Mandatory** | **Notes**                                                                 |
|----------------------|----------------|---------------------------------------------------------------------------------|---------------|---------------------------------------------------------------------------|
| **`log_id`**         | `UUID`         | Unique identifier for the change log entry.                                     | ✅ Yes         | Auto-generated (e.g., UUIDv4).                                           |
| **`entity_type`**    | `String`       | Type of entity (e.g., `user`, `order`, `product`).                               | ✅ Yes         | Controls downstream processing logic.                                    |
| **`entity_id`**      | `String/UUID`  | Unique identifier for the affected entity (e.g., `user_123`).                    | ✅ Yes         | Matches the primary key in the source database.                          |
| **`operation`**      | `String`       | CDC operation type (`create`, `update`, `delete`, `upsert`).                   | ✅ Yes         | Used to filter or transform changes.                                     |
| **`payload`**        | `JSON/Object`  | Serialized entity data before/after the change (key depends on `operation`).    | ✅ Yes         | Structure varies by `operation` (see [Payload Format](#payload-format)). |
| **`old_value`**      | `JSON/Object`  | (For `update`/`delete`) Entity state **before** the change.                     | ❌ No*        | Omitted if not applicable (e.g., `create`).                                |
| **`new_value`**      | `JSON/Object`  | (For `update`/`create`) Entity state **after** the change.                     | ❌ No*        | Omitted if not applicable (e.g., `delete`).                                |
| **`schema_version`** | `String`       | Schema version of `entity_type` (e.g., `v1.2`).                               | ✅ Yes         | Helps enforce backward compatibility.                                     |
| **`timestamp`**      | `Timestamp`    | When the change occurred (source system time).                                 | ✅ Yes         | Prefer UTC for consistency.                                              |
| **`source_system`**  | `String`       | Name of the source system (e.g., `db_postgres`, `api_gateway`).                 | ✅ Yes         | Critical for multi-system environments.                                   |
| **`source_table`**   | `String`       | Original table name (if applicable).                                             | ❌ No          | Useful for debugging or raw data queries.                                 |
| **`user_id`**        | `String/UUID`  | ID of the user/actor who triggered the change (if tracked).                      | ❌ No          | Nullable; omit if anonymous actions.                                      |
| **`metadata`**       | `JSON/Object`  | Extensible field for custom key-value pairs (e.g., `correlation_id`).           | ❌ No          | Avoid shadowing standard fields.                                         |
| **`partition_key`**  | `String`       | Key for partitioning (e.g., `user_id` or `entity_type+entity_id`).              | ❌ No          | Optimizes query performance.                                             |
| **`processing_status`** | `String`      | State of log entry (`queued`, `processed`, `failed`).                           | ❌ No          | Useful for pipeline monitoring.                                          |

*_For `create`: omit `old_value`; for `delete`: omit `new_value`._

---

### **Payload Format**
The `payload` field’s structure depends on the `operation`:

| **Operation** | **`payload` Structure**                                                                 | **Example**                                                                 |
|---------------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| `create`      | `{ "new_value": { ... } }`                                                               | `{ "new_value": { "name": "Alice", "email": "alice@example.com" } }`      |
| `update`      | `{ "old_value": { ... }, "new_value": { ... } }`                                       | `{ "old_value": { "email": "old@example.com" }, "new_value": { ... } }`   |
| `delete`      | `{ "old_value": { ... } }`                                                              | `{ "old_value": { "id": "user_456", "name": "Bob" } }`                     |
| `upsert`      | `{ "old_value": { ... } (if existed), "new_value": { ... } }`                           | `{ "new_value": { ... } }` (if created) or `{ "old_value": {...}, ... }` |

---

## **Query Examples**
Use these queries to interact with CDC logs in SQL, Kafka, or other systems.

### **1. Basic Filtering**
**Find all user account creations in the last hour:**
```sql
SELECT *
FROM change_logs
WHERE entity_type = 'user'
  AND operation = 'create'
  AND timestamp > NOW() - INTERVAL '1 hour';
```

**Kafka (KSQL):**
```sql
SELECT *
FROM change_logs
WHERE entity_type = 'user'
  AND operation = 'create'
  AND timestamp BETWEEN '2023-10-01T00:00:00Z' AND '2023-10-01T23:59:59Z';
```

---

### **2. Tracking Entity Changes**
**Get all updates to a specific product (`entity_id = 'prod_789'`):**
```sql
SELECT timestamp, old_value, new_value
FROM change_logs
WHERE entity_type = 'product'
  AND entity_id = 'prod_789'
  AND operation = 'update'
ORDER BY timestamp DESC;
```

**Filter for failed processing (if `processing_status` is tracked):**
```sql
SELECT log_id, source_system, metadata
FROM change_logs
WHERE processing_status = 'failed';
```

---

### **3. Aggregations**
**Count daily `delete` operations by `entity_type`:**
```sql
SELECT
  entity_type,
  DATE(timestamp) AS day,
  COUNT(*) AS delete_count
FROM change_logs
WHERE operation = 'delete'
GROUP BY entity_type, day
ORDER BY day DESC;
```

**Calculate the % of `update` vs. `create` operations:**
```sql
SELECT
  operation,
  COUNT(*) AS total,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM change_logs
GROUP BY operation;
```

---

### **4. Joining with Source Data**
**Reconstruct a user’s state after an update (join with `new_value`):**
```sql
SELECT u.*, cl.timestamp
FROM users u
JOIN change_logs cl ON u.id = cl.entity_id
  AND u.id = cl.new_value->>'id'
  AND cl.operation = 'update'
WHERE cl.entity_type = 'user'
ORDER BY cl.timestamp DESC
LIMIT 1;  -- Latest update
```

---

### **5. Partitioned Queries**
**Optimize by `entity_type` and `entity_id` (if partitioned):**
```sql
-- Assume logs are partitioned by entity_type + entity_id
SELECT * FROM change_logs
PARTITION ('user', 'user_123')
WHERE timestamp > '2023-10-01';
```

---

## **Payload Format Variations**
### **Nested Entity Changes**
For entities with nested objects (e.g., `address`), include the full path in `payload`:
```json
{
  "operation": "update",
  "entity_type": "user",
  "entity_id": "user_123",
  "payload": {
    "old_value": { "address": { "city": "Old City" } },
    "new_value": { "address": { "city": "New City" } }
  }
}
```

### **Array Updates**
For arrays (e.g., `tags`), track additions/deletions explicitly:
```json
{
  "operation": "update",
  "payload": {
    "old_value": { "tags": ["tag1", "tag2"] },
    "new_value": { "tags": ["tag1", "tag3"] }
  }
}
```

---

## **Related Patterns**
1. **[CDC Pipeline Design](link)**
   - Best practices for building scalable CDC pipelines (e.g., Kafka, Debezium).
2. **[Schema Registry Integration](link)**
   - How to use Confluent Schema Registry with CDC logs for backward compatibility.
3. **[Change Data Capture for Event Sourcing](link)**
   - Combining CDC with CQRS/event-sourcing architectures.
4. **[Audit Logging Extension](link)**
   - Adding compliance fields (e.g., `change_reason`, `compliance_flag`) to logs.
5. **[Delta Lake CDC Optimization](link)**
   - Leveraging Delta Lake’s CDC features with this pattern.

---

## **Implementation Notes**
### **Tools & Libraries**
- **Debezium**: Automatically generates logs matching this schema for PostgreSQL/MySQL.
  ```yaml
  # Debezium config (simplified)
  source.connector: postgres
  source.database.hostname: db.example.com
  source.plugin.name: pgoutput
  transformation: add-source-column=source_system:postgres
  ```
- **Kafka Connect**: Use a custom sink connector to validate logs against this schema.
- **Custom CDC**: Implement validation hooks to enforce field presence/types.

### **Validation**
Validate logs programmatically (e.g., using JSON Schema):
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["log_id", "entity_type", "entity_id", "operation", "payload", "timestamp", "source_system"],
  "properties": {
    "old_value": { "nullable": true },
    "new_value": { "nullable": true },
    "metadata": { "type": "object" }
  }
}
```

### **Performance Considerations**
- **Indexing**: Add indexes on `entity_type`, `entity_id`, and `timestamp` for large datasets.
- **Partitioning**: Partition logs by `entity_type` + `entity_id` if querying per-entity frequently.
- **Compression**: For Kafka, use Snappy compression for `payload` (often JSON-heavy).

### ** Evolution**
- **Backward Compatibility**: Use `schema_version` to support breaking changes (e.g., add `new_value.field` without dropping `old_value`).
- **Deprecation**: Add `deprecated_since` to fields/methods in `metadata`.

---

## **Examples by Source System**
### **PostgreSQL (Debezium)**
```json
{
  "log_id": "a1b2c3d4-e5f6-7890",
  "entity_type": "orders",
  "entity_id": "order_999",
  "operation": "update",
  "payload": {
    "old_value": { "status": "pending", "amount": 100.00 },
    "new_value": { "status": "shipped", "amount": 105.00 }
  },
  "schema_version": "v1.0",
  "timestamp": "2023-10-05T14:30:00Z",
  "source_system": "db_postgres"
}
```

### **API Gateway (Manual CDC)**
```json
{
  "log_id": "a1b2c3d4-e5f6-7890",
  "entity_type": "users",
  "entity_id": "user_42",
  "operation": "create",
  "payload": {
    "new_value": {
      "name": "Charlie",
      "roles": ["admin"],
      "last_login": null
    }
  },
  "schema_version": "v1.1",
  "timestamp": "2023-10-05T15:15:00Z",
  "source_system": "api_gateway",
  "user_id": "auth_789"
}
```

---

## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|------------------------------------|-----------------------------------------------------------------------------|
| Missing `entity_id` in logs        | Check Debezium connector config for `table.include-list`.                   |
| Schema drift                      | Use Schema Registry to enforce `schema_version` compliance.                |
| High cardinality in `entity_type` | Consider hierarchical types (e.g., `user_profile`, `user_preferences`).     |
| Large `payload` sizes              | Compress JSON or use protobuf for nested structures.                       |
| Timezone mismatches                | Store all timestamps in UTC; document source system timezones in `metadata`.|

---
**Last Updated:** [YYYY-MM-DD]
**Owner:** [Team/Contact]