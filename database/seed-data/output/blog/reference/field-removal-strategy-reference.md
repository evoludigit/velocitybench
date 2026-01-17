# **[Pattern] Field Removal Reference Guide**

---

## **Overview**
The **Field Removal** pattern ensures controlled and safe deletion of fields from a data structure (e.g., a JSON payload, database record, or message object) without causing unintended side effects. This is critical when migrating systems, cleaning up legacy data, or dynamically modifying data based on business rules. The pattern provides a structured way to:
- **Conditionally remove fields** based on criteria (e.g., null values, deprecated fields, or user permissions).
- **Handle cascading effects** (e.g., removing dependent fields or references).
- **Log removals** for auditability.
- **Support backward compatibility** during transitions.

Use this pattern when:
✅ You need to decommission obsolete fields.
✅ A field’s presence violates data integrity rules.
✅ A third-party system mandates field removal.
✅ You’re refactoring schemas incrementally.

---

## **Implementation Details**

### **Core Principles**
1. **Idempotency**: Repeated application of the pattern should not alter data further.
2. **Atomicity**: Field removal should be atomic where possible (e.g., in a single database transaction).
3. **Validation**: Ensure removed fields don’t break downstream processes (e.g., validation rules, queries).
4. **Notification**: Optionally notify consumers of schema changes.

### **Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Field Criteria**        | Rules to determine which fields to remove (e.g., `field == null`, `deprecated_since > now()`).     |
| **Cascading Removal**     | Automatically removing dependent fields (e.g., removing `parent_id` requires removing child records). |
| **Backup/Shadow Field**   | Temporarily storing removed fields in a new field for backward compatibility.                     |
| **Audit Trail**           | Logging removals with metadata (timestamp, user, reason).                                           |
| **Phased Rollout**        | Gradually removing fields across versions to minimize disruption.                                  |

---

## **Schema Reference**
Below are common data structures used in Field Removal implementations.

### **1. JSON Payload (Restructured After Removal)**
```json
{
  "original_data": {
    "id": "user_123",
    "name": "Alice",
    "removed_field_old": null,  // Explicitly set to null (or deleted)
    "replaced_field_new": "Alice Smith"  // Updated field
  },
  "audit": {
    "removed_fields": ["removed_field_old"],
    "timestamp": "2024-05-20T12:00:00Z",
    "user": "admin"
  }
}
```

### **2. Database Schema (Before/After Removal)**
| **Operation**       | **Before Schema**                          | **After Schema**                     |
|----------------------|--------------------------------------------|---------------------------------------|
| **Standard Removal** | `{ id INT, deprecated_field VARCHAR(255) }` | `{ id INT }`                          |
| **Shadow Field**     | `{ id INT, old_field VARCHAR(255) }`       | `{ id INT, old_field VARCHAR(255), new_field VARCHAR(255) }` |
| **Cascading**        | `{ parent_id INT, child_records JSON[] }` | `{ child_records_filtered JSON[] }`  |

### **3. Event-Based Removal (Example: Kafka Topic)**
```json
// Topic: "field_removal_events"
{
  "event_type": "FIELD_REMOVAL",
  "resource_id": "user_123",
  "field_removed": "email",
  "timestamp": "2024-05-20T12:00:00Z",
  "previous_value": "alice@example.com"
}
```

---

## **Query Examples**
Below are query patterns for common use cases.

---

### **1. SQL: Remove Null/Empty Fields**
```sql
-- Remove NULL/empty fields from a table (PostgreSQL)
UPDATE users
SET jsonb_set(metadata, '{name}') = NULL
WHERE metadata->>'name' IS NULL
AND metadata->>'created_at' > '2023-01-01';
```

### **2. JSON: Conditional Field Removal (JavaScript)**
```javascript
// Remove deprecated fields where a condition is met
function removeDeprecatedFields(data) {
  if (data.deprecated_since && data.deprecated_since < new Date().toISOString()) {
    delete data.deprecated_field;
  }
  return data;
}

const updatedData = removeDeprecatedFields(originalPayload);
```

### **3. NoSQL: MongoDB Update (Remove Field If Matches Criteria)**
```javascript
// Remove 'old_api_key' if it exists and is empty
db.users.updateMany(
  { old_api_key: { $exists: true, $eq: "" } },
  [ { $unset: { old_api_key: "" } } ]
);
```

### **4. API Endpoint: Safe Field Removal (REST)**
```http
PATCH /users/{id}/metadata
Headers: { "Content-Type": "application/json" }
Body:
{
  "operations": [
    {
      "remove": "legacy_field",
      "condition": { "active": true }
    }
  ]
}
```

### **5. Streaming: Kafka Consumer (Remove Fields in Real-Time)**
```python
# Python (Confluent Kafka)
def remove_fields(record):
    if record.value():
        data = json.loads(record.value())
        if "temp_field" in data and data["temp_field"] == "delete":
            del data["temp_field"]
            record.value(bytes(json.dumps(data), 'utf-8'))
    return record

# Apply to a topic
consumer.subscribe(["input_topic"])
while True:
    msg = consumer.poll(timeout=1.0)
    if msg:
        remove_fields(msg)
```

---

## **Error Handling & Edge Cases**
| **Scenario**                          | **Solution**                                                                                     |
|----------------------------------------|-------------------------------------------------------------------------------------------------|
| **Orphaned References**               | Use transactions to delete dependent records first (e.g., cascade deletes in SQL).            |
| **Concurrent Modifications**          | Implement pessimistic locking or versioning (e.g., `ETag` headers in HTTP).                     |
| **Schema Validation Failures**        | Temporarily add fields as optional (`nullable: true`) during migration.                         |
| **Partial Field Removal**             | Use partial updates (e.g., `PATCH` in REST) to avoid overwriting unrelated fields.              |
| **Backward Compatibility**            | Shadow fields with aliases (e.g., `old_field: new_field`).                                        |

---

## **Related Patterns**
1. **[Schema Evolution](https://example.com/schema-evolution)**
   - Gradually modify schemas while maintaining backward compatibility.
2. **[Conditional Logic](https://example.com/conditional-logic)**
   - Apply field removal based on runtime conditions (e.g., user permissions).
3. **[Data Migration](https://example.com/data-migration)**
   - Move data between systems while handling field compatibility.
4. **[Immutable Data](https://example.com/immutable-data)**
   - Use versioned data structures to avoid modifying existing records.
5. **[Event Sourcing](https://example.com/event-sourcing)**
   - Log field removals as immutable events for auditability.

---

## **Best Practices**
- **Phase Rollouts**: Remove fields in stages (e.g., deprecate → remove → audit).
- **Automated Testing**: Test removal logic with edge cases (e.g., nested objects, circular references).
- **Downtime Planning**: Schedule removals during low-traffic periods.
- **Documentation**: Update API/docs to reflect removed fields (e.g., mark them as deprecated).
- **Monitoring**: Track errors or unexpected field removals (e.g., via logs or alerts).

---
**Example Workflow**:
1. **Deprecate**: Add a `deprecated_since` field to mark obsolete fields.
2. **Notify**: Emit an event to consumers (e.g., Kafka topic).
3. **Remove**: Delete the field in a new release.
4. **Audit**: Log removals for compliance (e.g., GDPR).

---
**See Also**:
- [Field Deprecation Checklist](#)
- [Migration Strategies for Legacy Systems](#)