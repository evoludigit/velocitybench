---
# **[Pattern] Field Addition Reference Guide**

## **Overview**
The **Field Addition** pattern describes how to safely introduce new fields to an existing schema or data model without disrupting existing systems, clients, or services. This pattern is critical in evolving APIs, databases, or event schemas over time, ensuring backward compatibility while enabling forward progression.

Key principles include:
- **Backward compatibility**: Existing code must continue to function without modification.
- **Forward compatibility**: New code must be able to utilize new fields where available.
- **Minimal disruption**: Changes should not require redeployment or refactoring of dependent systems.
- **Gradual adoption**: Fields can be introduced as optional to allow smooth migration.

This guide covers implementation strategies, schema design, query patterns, and related considerations for employing **Field Addition** effectively.

---

## **Key Concepts & Implementation Details**

### **Core Techniques**
1. **Optional Fields**:
   - New fields are introduced as optional (e.g., `NULL`-able in databases, absent in JSON).
   - Clients ignore unknown fields, and servers omit them when backward compatibility is required.

2. **Versioning (Schema Evolution)**:
   - Explicitly track schema versions via headers (e.g., `X-API-Version`), attributes, or metadata fields.
   - Deprecate fields via version tags or `@deprecated` annotations.

3. **Data Migration Strategies**:
   - **Lazy Initialization**: Populate new fields on-demand during writes/updates.
   - **Batch Processing**: Backfill new fields for existing records via scheduled jobs.
   - **Hybrid Schema**: Temporarily support both old and new schemas before phasing out the old.

4. **Client-Side Handling**:
   - Use dynamic schemas (e.g., OpenAPI/Swagger, Protobuf) to auto-discover new fields.
   - Implement field-mapping logic to handle schema changes gracefully.

---

## **Schema Reference**

### **Table 1: Backward-Compatible Schema Evolution**
| **Component**       | **Old Schema**                          | **New Schema (With Added Field)**       | **Key Behavior**                          |
|----------------------|------------------------------------------|-----------------------------------------|-------------------------------------------|
| **Database (SQL)**   | `users(id INT, username VARCHAR(255))`  | `users(id INT, username VARCHAR(255), email VARCHAR(255))` (email `NULL` default) | New field defaults to `NULL`; queries ignore it. |
| **API (JSON)**       | `{"id": 1, "username": "user1"}`        | `{"id": 1, "username": "user1", "email": "user1@example.com"}` (email optional) | Clients parse only known fields.          |
| **Event (Kafka)**    | `{ "user_id": 1, "action": "create" }`  | `{ "user_id": 1, "action": "create", "metadata": { "email": "user1@example.com" } }` | New fields nested under a metadata object. |

### **Table 2: Deprecation Strategy**
| **Field**       | **New Field**       | **Deprecation Policy**                     | **Migration Window** |
|-----------------|---------------------|--------------------------------------------|-----------------------|
| `user.roles`    | `user.permissions`  | Deprecate `roles` after 6 months; log warnings. | Phased rollout.       |
| `order.status`  | `order.status_code` | `status_code` replaces `status`; alias `status`. | Dual-writing for 3 months. |

---

## **Query Examples**

### **1. Database (SQL)**
**Query: Select with Optional New Field**
```sql
-- Backward-compatible query: ignore 'email' if not present
SELECT id, username, email FROM users WHERE id = 1;
```
**Result**:
- If `email` exists: `id=1, username="user1", email="user1@example.com"`.
- If `email` is `NULL`: `id=1, username="user1", email=NULL`.

**Query: Insert with New Field (Optional)**
```sql
-- New field defaults to NULL; existing queries unaffected
INSERT INTO users (id, username, email) VALUES (2, "user2", NULL);
```

### **2. REST API (JSON)**
**Request: POST with New Field**
```http
POST /users
Content-Type: application/json

{
  "id": 3,
  "username": "user3",
  "email": "user3@example.com"  -- New field; omitted for backward compatibility
}
```
**Response (Legacy Client)**:
```json
{
  "id": 3,
  "username": "user3"
}
```
**Response (Modern Client)**:
```json
{
  "id": 3,
  "username": "user3",
  "email": "user3@example.com"
}
```

### **3. Event-Driven (Kafka)**
**Message: User Created Event (New Field)**
```json
{
  "event": "user.created",
  "user_id": 4,
  "metadata": {  -- New field structure
    "email": "user4@example.com",
    "created_at": "2023-10-01T00:00:00Z"
  }
}
```
**Consumer Logic (Backward-Compatible)**:
```python
def handle_user_event(event):
    if "metadata" in event:
        email = event["metadata"].get("email")  # Optional
    else:
        email = None
```

---

## **Best Practices**

### **1. Schema Management**
- **Use Versioning**: Add an `schema_version` field to track evolution:
  ```json
  {
    "schema_version": "2.0",
    "id": 1,
    "username": "user1",
    "email": "user1@example.com"
  }
  ```
- **Document Changes**: Maintain a `CHANGELOG.md` or API versioned docs.

### **2. Client Implementation**
- **Dynamic Parsing**: Use libraries like:
  - JavaScript: `JSON.parse()` with `reviver` function.
  - Python: `dataclasses.asdict()` with `ignore_missing=True`.
- **Field Aliasing**: Map old fields to new ones temporarily:
  ```python
  def update_order(order):
      if "status" in order:
          order["status_code"] = map_status_to_code(order["status"])
  ```

### **3. Testing**
- **Regression Tests**: Validate backward compatibility with existing clients.
- **Canary Releases**: Gradually expose new fields to a subset of users.

### **4. Monitoring**
- **Deprecation Warnings**: Log usage of deprecated fields (e.g., Prometheus metrics).
- **Field Coverage**: Track adoption rate of new fields (e.g., % of records with `email`).

---

## **Query Examples: Edge Cases**

### **1. Partial Updates (Database)**
```sql
-- Update a field that may not exist (e.g., PostgreSQL's `ON CONFLICT`)
INSERT INTO users (id, username, email)
VALUES (5, "user5", NULL)
ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email;
```

### **2. JSON Patch (API)**
**Request: Add New Field via PATCH**
```http
PATCH /users/1
Content-Type: application/json-patch+json

[
  { "op": "add", "path": "/email", "value": "user1@example.com" }
]
```
**Response**:
```json
{
  "id": 1,
  "username": "user1",
  "email": "user1@example.com"
}
```

### **3. Event Schema Evolution**
**Legacy Consumer (Ignores New Field)**:
```json
# Old event: { "user_id": 1, "action": "update" }
# New event: { "user_id": 1, "action": "update", "details": { ... } }
def process_event(event):
    if "details" in event:
        print("New schema detected!")
    # Process known fields
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[Field Deprecation]**   | Gradually phase out old fields while supporting new ones.                     | When replacing or renaming fields.               |
| **[Schema Registry]**     | Centralized management of evolving schemas (e.g., Confluent Schema Registry).  | For event-driven systems with multiple consumers. |
| **[Feature Flags]**       | Control rollout of new fields via feature toggles.                            | For gradual client adoption.                     |
| **[Backward-Incompatible Change]** | Documented breaking changes with migration guides.                     | Rare; requires coordination with all clients.    |
| **[Polyglot Persistence]** | Use different storage formats (e.g., JSON vs. SQL) for flexible schemas.     | When working with heterogeneous data sources.    |

---

## **Anti-Patterns**
1. **Forced Field Updates**:
   - ❌ `UPDATE users SET email = 'fallback@example.com' WHERE email IS NULL;`
   - ✅ Use lazy initialization or client-side defaults instead.

2. **Breaking API Contracts**:
   - ❌ Changing `username` from `VARCHAR(255)` to `TEXT` without notification.
   - ✅ Always document schema changes and provide migration paths.

3. **Ignoring Deprecated Fields**:
   - ❌ Removing `roles` without deprecation warnings.
   - ✅ Log warnings and support aliases during the transition.

---

## **Tools & Libraries**
| **Tool**                     | **Purpose**                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| **OpenAPI/Swagger**          | Define evolving API schemas with `deprecated` tags.                         |
| **Protobuf**                 | Supports schema evolution via wire compatibility.                           |
| **Avro**                     | Schema registry for event schemas.                                          |
| **Django REST Framework**    | `Field` class supports optional/nullable fields via `allow_null=True`.       |
| **Spring Data MongoDB**      | Dynamic `ObjectMapper` for unstructured documents.                          |

---
**End of Guide**
*Total Word Count: ~1,000*