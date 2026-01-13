---
# **[Pattern] Error Handling and Partial Results Reference Guide**

## **1. Overview**
This pattern ensures **graceful failure handling** when processing nested data structures (e.g., parent-child relationships in APIs, database records, or RPC calls). Instead of failing the entire operation on a single error, successful field(s) return **valid results**, while **invalid fields** include structured error metadata.

Use this pattern when:
- Processing **heterogeneous data** (e.g., a parent record with multiple child fields).
- Avoiding **cascading failures** (e.g., one failed field shouldn’t break the entire response).
- Supporting **batch operations** (e.g., bulk updates where some entries succeed while others fail).
- Designing **resilient APIs** that prioritize **partial success** over strict validation.

Implementation is **API-agnostic**, but examples use **REST JSON** and **GraphQL-like** structures for clarity.

---

## **2. Schema Reference**
### **2.1 Core Response Structure**
| Field               | Type                     | Description                                                                                     | Example Value                          |
|---------------------|--------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------|
| `successful_fields` | Object/Array             | Fields/objects with **no errors** (returned as-is).                                            | `{ id: 123, name: "Valid Entry" }`      |
| `failed_fields`     | Array                    | Array of objects with **error metadata** for each failed field.                               | `[ { field: "email", error: "invalid" } ]`|
| `errors` (optional) | Array/Object             | Root-level errors (e.g., authentication failures) that don’t belong to a specific field.       | `{ code: "403", message: "Permission denied" }` |
| `status` (optional) | String                   | Human-readable summary (e.g., `"partial_success"` or `"no_errors"`).                           | `"mixed_results"`                      |
| `metadata`          | Object                   | Additional context (e.g., timestamps, correlation IDs).                                         | `{ request_id: "abc123" }`             |

---

### **2.2 Failed Field Schema**
Each entry in `failed_fields` must include:

| Field   | Type   | Description                                                                                     | Example Value          |
|---------|--------|-------------------------------------------------------------------------------------------------|------------------------|
| `field` | String | Name of the **failed field** (e.g., `"email"`, `"nested.address"`).                           | `"user.address.city"`   |
| `error` | String | **Error code** (e.g., `"required"`, `"invalid_format"`, `"server_error"`).                     | `"invalid_json"`        |
| `message` | String | **Human-readable description** of the issue.                                                   | `"Invalid email format"`|
| `code`   | String | **Machine-readable error code** (optional, for programmatic handling).                        | `"EMAIL_INVALID"`       |
| `suggestions` (optional) | Array | **Remediation steps** (e.g., format hints or validation rules).                               | `["Use format: user@example.com"]` |

---
### **2.3 Nested Field Handling**
For deeply nested structures (e.g., `{ parent: { child: { field } } }`), errors **reference the full path**:
```json
{
  "failed_fields": [
    {
      "field": "parent.child.field",
      "error": "invalid_length",
      "message": "Must be 3-20 characters",
      "code": "FIELD_TOO_SHORT"
    }
  ]
}
```

---
### **2.4 Success vs. Partial Success Responses**
| Scenario                     | Response Example                                                                               |
|------------------------------|-----------------------------------------------------------------------------------------------|
| **All fields valid**         | `{ "successful_fields": { "id": 1, "name": "Alice" }, "status": "complete_success" }`          |
| **Some fields invalid**      | `{ "successful_fields": { "id": 1 }, "failed_fields": [ { "field": "email", "error": "invalid" } ], "status": "partial_success" }` |
| **All fields invalid**       | `{ "errors": [ { "code": "400", "message": "Validation failed" } ], "status": "complete_failure" }` |

---

## **3. Query Examples**
### **3.1 REST API (JSON)**
**Request:**
```http
POST /users/bulk-update
Content-Type: application/json

{
  "users": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" },
    { "id": 2, "name": "Bob", "email": "invalid-email" }
  ]
}
```

**Success Response (Partial):**
```json
{
  "status": "partial_success",
  "successful_fields": [
    {
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com",
      "updated_at": "2023-10-01T12:00:00Z"
    }
  ],
  "failed_fields": [
    {
      "field": "users[1].email",
      "error": "invalid_format",
      "message": "Email must contain '@'",
      "code": "EMAIL_FORMAT"
    }
  ],
  "metadata": { "processed": 2, "success_count": 1 }
}
```

---
### **3.2 GraphQL (Partial Results)**
**Query:**
```graphql
query UpdateProfiles($input: [UpdateProfileInput!]!) {
  updateProfiles(input: $input) {
    successfulUpdates {
      id
      name
    }
    failedUpdates {
      field
      error
      message
    }
    status
  }
}
```

**Variables:**
```json
{
  "input": [
    { "id": 1, "name": "Alice" },
    { "id": 2, "invalid_field": "malformed" }
  ]
}
```

**Response:**
```json
{
  "data": {
    "updateProfiles": {
      "successfulUpdates": [ { "id": 1, "name": "Alice" } ],
      "failedUpdates": [
        {
          "field": "input[1].invalid_field",
          "error": "missing_required_field",
          "message": "Field 'email' is required"
        }
      ],
      "status": "partial_success"
    }
  }
}
```

---
### **3.3 Database Bulk Insert**
**Input (SQL-like):**
```sql
INSERT INTO users (id, name, email)
VALUES
  (1, 'Alice', 'alice@example.com'),
  (2, 'Bob', 'invalid-email')
ON CONFLICT (id)
DO UPDATE SET
  validated = CASE
    WHEN email ~* '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$'
    THEN true ELSE false
  END
RETURNING
  id,
  name,
  email,
  validated,
  error_code
```

**Result Set:**
| id  | name | email            | validated | error_code       |
|-----|------|------------------|-----------|------------------|
| 1   | Alice| alice@example.com| true      | null             |
| 2   | Bob  | invalid-email    | false     | `EMAIL_FORMAT`   |

---

## **4. Implementation Best Practices**
### **4.1 Client-Side Handling**
- **Log failed fields** for debugging (e.g., send `failed_fields` to an analytics tool).
- **Retry failed operations** (e.g., retry `POST /users/bulk-update` with corrected data).
- **Display user-friendly errors** (e.g., highlight invalid email fields in a form).

### **4.2 Server-Side Considerations**
- **Validate in bulk** (e.g., process all fields before responding to avoid partial responses mid-execution).
- **Correlate errors** (include `request_id` or `transaction_id` in `metadata` for tracing).
- **Rate-limit partial failures** (avoid overwhelming clients with large `failed_fields` arrays).

### **4.3 Error Codes**
Use a **consistent naming convention** (e.g., `PREFIX_FIELD_TYPE_ERROR`):
| Error Code          | Description                          | Example Usage                     |
|---------------------|--------------------------------------|-----------------------------------|
| `REQUIRED_FIELD_MISSING` | Field is mandatory.                  | `"name": missing`                 |
| `INVALID_JSON`      | Field parsing failed.                | `"metadata.address": "invalid"`   |
| `SERVER_ERROR`      | Backend processing failed.           | `"nested.data[0]": null`          |
| `PERMISSION_DENIED` | Authz failure (root-level).          | `errors: [{ code: "403" }]`       |

---

## **5. Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                  |
|----------------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **[Idempotency Keys]**           | Ensure retries of partial operations don’t duplicate side effects.          | Batch operations with retries.              |
| **[Backoff & Retry]**             | Exponential backoff for transient errors in failed fields.                 | Network/timeouts (e.g., external API calls). |
| **[Circuit Breaker]**             | Temporarily halt calls to failing services after repeated errors.           | Dependencies with unstable providers.       |
| **[Validation at the Edge]**     | Validate data **before** sending to backend to reduce partial errors.      | Frontend/API layer validations.             |
| **[Retry with Exponential Backoff]** | Retry failed field operations with delays.                        | Idempotent operations (e.g., DB updates).  |

---

## **6. Edge Cases & FAQ**
### **6.1 Can I disable partial results?**
Yes, add a query parameter (e.g., `?strict=true`) to **fail fast** on the first error:
```json
{
  "error": "strict_mode_enabled",
  "message": "Operation aborted due to validation errors"
}
```

### **6.2 How to handle circular references?**
- **Option 1:** Omit circular fields from `successful_fields`.
- **Option 2:** Return a **truncated version** with a warning:
  ```json
  {
    "failed_fields": [ { "field": "nested.self_reference", "error": "circular" } ],
    "truncated": true
  }
  ```

### **6.3 Performance Considerations**
- **Batch processing:** Process valid fields first to return partial results **before** completing validation.
- **Streaming:** For large datasets, use **server-sent events (SSE)** to stream partial results incrementally.

---
## **7. Example Libraries/Frameworks**
| Language/Framework | Implementation Notes                                                                 |
|--------------------|---------------------------------------------------------------------------------------|
| **JavaScript (Express)** | Use middleware to parse errors into the `failed_fields` structure.                  |
| **Python (FastAPI)**   | Leverage Pydantic’s `ValidationError` and transform to our schema.                   |
| **Go**               | Use `error` structs with `field` and `error` tags in JSON marshaling.               |
| **Ruby (Rails)**     | Override `ActiveModel::Errors` to return partial results in API responses.           |

---
## **8. Migration Strategy**
1. **Backward Compatibility:** Start by **appending** `failed_fields` to existing error responses.
2. **Deprecation:** Warn clients via `Deprecation` header before removing legacy error formats.
3. **Testing:** Validate partial responses with tools like **Postman** or **JMeter**.

---
**Key Takeaway:**
This pattern balances **resilience** (partial success) with **clarity** (structured errors). Use it to build APIs that **fail gracefully** while minimizing user impact.