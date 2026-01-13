# **[Pattern] Debugging Validation – Reference Guide**

---

## **Overview**
**Debugging Validation** is a structured approach to identifying and resolving validation errors in applications (e.g., APIs, microservices, or client-side form inputs). This pattern ensures errors are clearly communicated, reproducible, and actionable by:

- **Isolating** validation failures (input, schema, business logic).
- **Standardizing** error reporting (machine-readable + user-friendly).
- **Providing** granular debugging tools (logs, traces, interactive diagnostics).
- **Automating** root-cause analysis (e.g., via feedback loops).

Common scenarios include:
- API requests failing due to malformed payloads.
- Database transactions rejecting invalid data.
- Frontend validation mismatches between client and server.

---

## **Key Concepts & Implementation Details**

### **1. Error Classification**
Validation errors fall into these categories (prioritized for debugging):

| **Category**          | **Description**                                                                 | **Example**                          |
|-----------------------|---------------------------------------------------------------------------------|--------------------------------------|
| **Syntax Errors**     | Invalid data structure (e.g., missing fields, wrong types).                      | `"age": "twenty"` (should be `int`).  |
| **Semantic Errors**   | Valid syntax but invalid meaning (e.g., negative age, duplicate IDs).            | `"age": -5`, `"userId": "123abc"`      |
| **Business Logic**    | Violates domain rules (e.g., password complexity, inventory limits).              | `"password": "123"` (too weak).       |
| **Dependency Errors** | Invalid references to external systems (e.g., non-existent DB records).          | `"accountId": 999` (not found).       |
| **Context Errors**    | Validation depends on runtime context (e.g., session permissions).               | User lacks `update:profile` permission. |

---

### **2. Error Representation**
**Standardized Output Format (JSON):**
```json
{
  "error": {
    "code": "VALIDATION_FAILED",
    "type": "SemanticError",
    "field": "email",
    "message": "Must be a valid email format",
    "details": {
      "expected": "string matching regex",
      "actual": "user@example",
      "suggestedFix": "Add missing '@' symbol"
    },
    "path": ["request", "user", "email"],
    "timestamp": "2024-05-20T12:00:00Z"
  }
}
```
**Key Fields:**
- `code`: Machine-readable identifier (e.g., `INVALID_EMAIL`).
- `type`: Classification (e.g., `SemanticError`).
- `field`: Root cause location (nested paths supported).
- `details`: Diagnostic data (e.g., regex, suggestions).
- `path`: Traces the error through the request pipeline.

---

### **3. Debugging Workflow**
#### **Step 1: Reproduce the Error**
- **Log Inputs:** Capture the full request payload, headers, and context (e.g., `userId`, `sessionToken`).
- **Replay Tools:** Use APIs like **Postman** or **k6** to automate reproduction.
- **Environment Variables:** Ensure debug flags are enabled (e.g., `DEBUG_VALIDATION=true`).

#### **Step 2: Analyze Logs**
- **Structured Logging:** Log errors in the standardized format above.
- **Correlation IDs:** Add a `traceId` to link logs across services.
- **Sampling:** For high-volume systems, log errors with Y% probability (e.g., 1%).

**Example Log Entry:**
```json
{
  "level": "ERROR",
  "timestamp": "2024-05-20T12:00:00Z",
  "traceId": "abc123-xyz456",
  "message": "Validation error detected",
  "error": { ... }  // Standardized error payload
}
```

#### **Step 3: Schema Validation**
- **Validate Against Schemas:** Use tools like:
  - **JSON Schema** (for APIs).
  - **Zod** (TypeScript) / **Pydantic** (Python) for runtime checks.
  - **OpenAPI/Swagger** for API contracts.
- **Automated Testing:** Run `jq` or schema validators (e.g., `jsonschema`) on logs.

**Example Schema Snippet (JSON Schema):**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "user": {
      "type": "object",
      "properties": {
        "email": { "type": "string", "format": "email" },
        "age": { "type": "integer", "minimum": 0 }
      },
      "required": ["email"]
    }
  }
}
```

#### **Step 4: Interactive Debugging**
- **Dynamic Validation UI:** For web apps, display a "validation summary" page with:
  - Field-level errors.
  - Suggested fixes (e.g., "Add `@` to email").
  - Preview of corrected data.
- **CLI Tools:** Provide commands like:
  ```bash
  $ validate-user --input user.json --schema schema.json
  ERROR: Missing required field: "email"
  ```

#### **Step 5: Automated Root-Cause Analysis**
- **Feedback Loops:** Integrate with:
  - **Error Tracking:** Sentry, Datadog, or custom dashboards.
  - **Anomaly Detection:** Flag recurring errors (e.g., "10% of requests fail on `age` validation").
- **A/B Testing:** Compare validation rules between environments (e.g., staging vs. production).

---

## **Schema Reference**
| **Field**          | **Type**       | **Description**                                                                 | **Example Values**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `error.code`       | String         | Unique error identifier (e.g., `INVALID_EMAIL`).                               | `"EMAIL_FORMAT"`                       |
| `error.type`       | Enum           | Error category (`SyntaxError`, `SemanticError`, etc.).                         | `"SemanticError"`                      |
| `error.field`      | String         | Root field name or path (e.g., `"user.email"`).                               | `"age"`                                 |
| `error.message`    | String         | User-friendly description.                                                     | `"Age must be a positive number."`     |
| `error.details`    | Object         | Technical diagnostics (e.g., regex, expected/actual values).                  | `{"expected": "int", "actual": "twenty"}` |
| `error.path`       | Array[String]  | JSONPath to the invalid field.                                                 | `["request", "user", "age"]`           |
| `error.timestamp`  | ISO8601        | When the error occurred.                                                       | `"2024-05-20T12:00:00Z"`               |
| `traceId`          | String         | Correlation ID for distributed tracing.                                         | `"abc123-xyz456"`                      |
| `suggestedFix`     | String         | Optional: Auto-generated correction hint.                                       | `"Add '@' to email."`                  |

---

## **Query Examples**
### **1. Filtering Logs for Validation Errors**
**Tool:** `grep` + `jq`
```bash
# Filter logs for validation errors in the last hour
grep -i "VALIDATION_FAILED" /var/log/app.log | jq '.error.code == "VALIDATION_FAILED"'
```

**Tool:** Elasticsearch Query DSL
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "message.keyword": "VALIDATION_FAILED" } },
        { "range": { "@timestamp": { "gte": "now-1h/hour" } } }
      ]
    }
  }
}
```

### **2. Validating a JSON Payload**
**Tool:** `jsonschema` (CLI)
```bash
jsonschema -i user.json -s schema.json
# Outputs errors if validation fails
```

**Tool:** Python (Pydantic)
```python
from pydantic import ValidationError
from models import UserSchema

try:
    user = UserSchema.parse_obj(raw_data)
except ValidationError as e:
    print(e.json())  # Returns standardized error payload
```

### **3. Debugging API Responses**
**Tool:** `curl` + `jq`
```bash
curl -X POST http://api.example.com/users -d '{"age": "twenty"}' \
  -H "Accept: application/json" | jq '.error'
```

**Tool:** Postman Collections:
1. Set a **Test** script to check for `error.code` in the response.
2. Save failing requests to a **Failed Tests** folder for later analysis.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Schema as Contract](https://link.example.com/schema-contract)** | Define validation rules upfront in schemas (e.g., OpenAPI, JSON Schema). | Designing APIs or microservices.         |
| **[Circuit Breaker](https://link.example.com/circuit-breaker)** | Isolate validation failures from cascading errors (e.g., retry transient failures). | High-availability systems.                |
| **[Feature Flags](https://link.example.com/feature-flags)**       | Gradually roll out new validation rules.                                    | A/B testing validation changes.           |
| **[Observability Stack](https://link.example.com/observability)** | Logs + metrics + traces for validation diagnostics.                          | Monitoring production validation errors. |
| **[Idempotency Keys](https://link.example.com/idempotency)**         | Retry failed validation requests safely.                                   | Resilient APIs with retries.              |

---

## **Best Practices**
1. **Early Validation:** Fail fast (e.g., validate on input, not after DB operations).
2. **Idempotency:** Ensure retries don’t duplicate side effects.
3. **Localization:** Support multi-language error messages (e.g., `"Age must be positive"` → `français: "L'âge doit être positif"`).
4. **Performance:** Limit validation complexity for high-throughput systems.
5. **Tooling:** Integrate with CI/CD (e.g., validate schemas on commit hooks).

---
**See also:**
- [OWASP Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Validation_Cheat_Sheet.html)
- [JSON Schema Draft 7](https://json-schema.org/understanding-json-schema/reference/validation.html)