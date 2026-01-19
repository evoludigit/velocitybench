# **Debugging Type Evolution Safety Pattern: A Troubleshooting Guide**
*(Ensuring Backward/Forward Compatibility in Type Changes)*

This guide provides a structured approach to diagnosing and resolving issues when implementing or modifying **Type Evolution Safety** patterns in your backend systems. The goal is to minimize runtime breaking changes when evolving types (e.g., JSON schemas, API responses, or database records).

---

## **1. Symptom Checklist**
Before diving into fixes, confirm the issue using these checks:

| **Symptom** | **Description** | **Possible Causes** |
|-------------|----------------|---------------------|
| **Runtime errors on type mismatch** | `TypeError`, `SchemaValidationError`, or `UnknownFieldError` when processing older data with new types. | Missing backward compatibility, incomplete migration, or schema drift. |
| **Silent data loss or corruption** | Fields appear missing or malformed in logs/error messages. | Unhandled `null`/`undefined` falls, missing `default` values, or serialization mismatches. |
| **API/deprecated endpoint failures** | Older clients fail with `400 Bad Request` or `500 Internal Server Error`. | Missing versioned schemas, deprecated fields not handled gracefully. |
| **Database integrity issues** | ORM/DB migrations fail due to schema changes not propagating. | Transaction rollbacks, partial schema updates, or missing `ALTER TABLE` statements. |
| **Testing errors** | Unit/integration tests fail unexpectedly due to type evolution. | Test data not reflecting backward compatibility, or mocks outdated. |

**Quick Validation Steps:**
1. **Log raw payloads:** Ensure the incoming/outgoing data matches expectations (e.g., `console.log(JSON.stringify(request.body))`).
2. **Check versioning headers:** If using versioned APIs, verify `Accept: application/vnd.api.v1+json` or similar.
3. **Review migrations:** Confirm database/schema migrations are applied in all environments.

---

## **2. Common Issues and Fixes**

### **Issue 1: Missing Backward Compatibility (Schema Drift)**
**Symptoms:**
- Older clients fail with `Missing required field: "newField"`.
- New code crashes when processing legacy data.

**Root Cause:**
The new type omits optional fields or renames required ones without handling transitions.

**Fix:**
Use **optional fields + defaults** or **versioned schemas**:
```typescript
// Old schema (v1)
interface UserV1 {
  id: string;
  name: string;
}

// New schema (v2) with backward compatibility
interface UserV2 {
  id: string;
  name: string;
  email?: string; // Optional in v2, nullable for v1
}

function parseUser(data: unknown): UserV2 {
  if (!data) throw new Error("Invalid data");
  const parsed = typeof data === "object" ? data : { ...data };
  return {
    id: parsed.id || "",
    name: parsed.name || "",
    email: parsed.email, // Gracefully skips if missing
  };
}
```

**Alternative:** Use a **schema migrator** (e.g., JSON Schema `migrate` library) to transform legacy data:
```python
from jsonschema import Draft7Validator
from jsonschema.validators import migrate

# Migrate v1 → v2 schema
v1_schema = {"type": "object", "properties": {"name": {"type": "string"}}}
v2_schema = {"type": "object", "properties": {"email": {"type": "string"}}}
migrated_schema = migrate(v1_schema, v2_schema)
```

---

### **Issue 2: Deprecated Fields Not Handled**
**Symptoms:**
- Logs show `DeprecationWarning: 'oldField' is deprecated since v2`.
- New code fails silently or with `undefined` errors.

**Root Cause:**
Deprecated fields are not filtered out or replaced.

**Fix:**
Use **runtime field filtering**:
```javascript
// Node.js example
function filterDeprecatedFields(obj, deprecatedFields = []) {
  const result = { ...obj };
  deprecatedFields.forEach(field => delete result[field]);
  return result;
}

const cleanedData = filterDeprecatedFields(request.body, ["oldField"]);
```

**For Database Migrations:**
Add a `WHERE` clause to drop deprecated columns in a transaction:
```sql
BEGIN TRANSACTION;
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- Step 2: Copy data from deprecated field (if needed)
UPDATE users SET email = old_field WHERE old_field IS NOT NULL;

-- Step 3: Drop deprecated column
ALTER TABLE users DROP COLUMN old_field;
COMMIT;
```

---

### **Issue 3: Type Cast Mismatches**
**Symptoms:**
- `TypeError: Cannot convert undefined to integer` when parsing numbers.
- `SyntaxError: Unexpected token` in JSON parsing.

**Root Cause:**
Inconsistent typing between old/new data (e.g., `string` vs. `number`).

**Fix:**
Use **safe casting** with defaults:
```go
func safeInt(value string) int {
    num, err := strconv.Atoi(value)
    if err != nil {
        return 0 // Default for invalid/int conversion
    }
    return num
}

type User struct {
    Age int `json:"age"`
}

func parseUser(data map[string]interface{}) User {
    age, _ := data["age"].(string) // Cast to string first
    return User{Age: safeInt(age)}
}
```

**For JSON Parsing:**
Validate and sanitize input:
```python
import json
from typing import Any

def safe_parse_json(data: Any) -> dict:
    try:
        parsed = json.loads(data) if isinstance(data, str) else data
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed
```

---

### **Issue 4: Database Schema Mismatches**
**Symptoms:**
- ORM fails with `ColumnNotFoundError`.
- Slow queries due to missing indexes on new fields.

**Root Cause:**
Database schema lags behind code changes.

**Fix:**
1. **Add new columns first** (minimal migration risk):
   ```sql
   ALTER TABLE users ADD COLUMN email VARCHAR(255);
   ```
2. **Update indexes** (if needed):
   ```sql
   CREATE INDEX idx_user_email ON users(email);
   ```
3. **Backfill data** (optional):
   ```sql
   UPDATE users SET email = old_field WHERE old_field IS NOT NULL;
   ```

**For ORMs:**
Use **migration tools** (e.g., SQLAlchemy, TypeORM) to auto-generate scripts:
```typescript
// TypeORM migration example
async function migration(): Promise<void> {
  await queryRunner.addColumn(
    userTable,
    new TableColumn({ name: "email", type: "varchar", isNullable: true }),
  );
}
```

---

### **Issue 5: Testing Gaps**
**Symptoms:**
- Tests fail with `AssertionError: expected { ... } but got {}`.
- CI pipeline breaks on schema changes.

**Root Cause:**
Tests assume current schema but don’t account for backward compatibility.

**Fix:**
1. **Mock legacy data** in tests:
   ```javascript
   test("handles missing email field", () => {
     const legacyUser = { id: "123", name: "Alice" };
     const result = parseUser(legacyUser);
     expect(result.email).toBeUndefined(); // Not null, but missing
   });
   ```
2. **Use schema validators** (e.g., JSON Schema):
   ```json
   // test/schema-v1.json
   {
     "type": "object",
     "properties": { "name": { "type": "string" } },
     "required": ["name"]
   }
   ```
3. **Test migrations** in CI:
   ```yaml
   # GitHub Actions example
   - name: Run migration tests
     run: npm run test:migrations
   ```

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique**       | **Use Case**                                  | **Example Command/Code**                     |
|--------------------------|-----------------------------------------------|---------------------------------------------|
| **Postman/Newman**       | Test API versioning headers.                  | `newman post http://api.example.com/v1/users` |
| **SQL Query Logs**       | Debug schema migrations.                     | `SELECT * FROM information_schema.columns;` |
| **JSON Schema Validators** | Validate request/response schemas.          | `jsonschema validate -i payload.json schema.json` |
| **Logging Middleware**   | Inspect raw payloads in transit.             | `app.use((req, res, next) => { console.log(req.body); next(); })` |
| **Database Change Data Capture (CDC)** | Track schema drift over time.         | `pgAudit` (PostgreSQL), `binlog` (MySQL)    |
| **Feature Flags**        | Gradually roll out type changes.             | LaunchDarkly, Flagsmith                     |
| **Chaos Testing**        | Simulate network errors during migrations.   | `curl --fail --retry 3 http://api.example.com` |

**Advanced Debugging:**
- Use **source maps** to trace errors to original type definitions.
- Enable **SQL logging** in ORMs to catch schema mismatches:
  ```javascript
  // Sequelize example
  sequelize.on('query', console.log.bind(console));
  ```

---

## **4. Prevention Strategies**

### **A. Design-Time Mitigations**
1. **Adopt Versioned Schemas**
   - Use semantic versioning (e.g., `v1`, `v2`) for types/APIs.
   - Example:
     ```typescript
     // API Gateway routes
     app.get("/users/v1", v1UserHandler);
     app.get("/users/v2", v2UserHandler);
     ```
2. **Enforce Backward Compatibility**
   - Use **structural typing** (e.g., TypeScript interfaces) to allow extensions:
     ```typescript
     interface UserV1 { name: string; }
     interface UserV2 extends UserV1 { email?: string; } // Extends, doesn’t override
     ```
   - For databases, **add columns first**, then drop deprecated ones.

3. **Document Breaking Changes**
   - Use **CHANGELOG.md** to track type evolutions.
   - Example:
     ```
     ## [2.0.0] - 2023-10-01
     ### Breaking Changes
     - Renamed `user.name` → `user.fullName` (deprecated `name` is ignored).
     ```

### **B. Runtime Mitigations**
1. **Use Schema Registry**
   - Tools like **Confluent Schema Registry** or **JSON Schema Store** track evolving types.
2. **Implement a Schema Adapter**
   - Centralize type conversion logic:
     ```typescript
     class SchemaAdapter {
       static toV2(data: UserV1): UserV2 {
         return { ...data, email: data.deprecatedEmail }; // Deprecated → new field
       }
     }
     ```
3. **Feature Flags for Type Changes**
   - Gradually roll out new types:
     ```javascript
     if (featureFlags.newTypeEnabled) {
       return parseNewType(data);
     } else {
       return parseLegacyType(data);
     }
     ```

### **C. Testing Strategies**
1. **Fuzz Testing**
   - Inject malformed data to test robustness:
     ```javascript
     const fuzzData = { id: "123", name: null, email: "invalid" };
     try {
       parseUser(fuzzData);
     } catch (err) {
       console.error("Fuzz test failed:", err);
     }
     ```
2. **Schema Regression Tests**
   - Ensure new changes don’t break old validations:
     ```bash
     npm run test:schema-regression
     ```
3. **Canary Deployments**
   - Test type changes in a subset of traffic before full rollout.

### **D. Tooling**
| **Tool**               | **Purpose**                          |
|------------------------|--------------------------------------|
| **JSON Schema**        | Define and validate evolving types.  |
| **Avro/Protobuf**      | Binary schemas with backward/forward compatibility. |
| **SQL Migration Tools** | Auto-generate safe schema changes.   |
| **OpenTelemetry**      | Trace type evolution across services. |

---

## **5. Quick Reference Cheat Sheet**
| **Problem**               | **Solution Path**                          | **Code Snippet**                          |
|---------------------------|--------------------------------------------|--------------------------------------------|
| Missing optional fields   | Add `default` values or `null` checks.     | `field: data.field || null`                |
| Deprecated fields         | Filter out or remap fields.               | `delete obj.deprecatedField`              |
| Type cast errors          | Safe conversion with fallbacks.           | `Number.parseFloat(data.age) || 0`         |
| Database schema mismatches| Add columns first, then migrate.          | `ALTER TABLE ... ADD COLUMN`              |
| Testing gaps              | Mock legacy data in tests.                | `test("legacy data", () => { ... })`       |
| API versioning           | Route by version (`/v1`, `/v2`).           | `app.use("/v1", v1Router)`                 |

---

## **6. When to Seek Help**
If issues persist:
1. **Check community resources**:
   - [TypeScript GitHub Discussions](https://github.com/microsoft/TypeScript/issues)
   - [OpenAPI/Swagger forums](https://github.com/OAI/OpenAPI-Specification/issues)
2. **Consult architecture docs**:
   - Review **Type Evolution Patterns** (e.g., [Event Sourcing", "CQRS"]).
3. **Engage senior engineers**:
   - Ask: *"Did we follow the [Schema Migration Guide]?"*

---
**Final Note:** Type evolution is safer when treated as a **controlled migration** (like database schema changes). Always:
1. **Test changes in staging** with legacy data.
2. **Monitor rollout metrics** (e.g., error rates in new vs. old types).
3. **Communicate breaking changes** to consumers (e.g., via GitHub Discussions).

By following this guide, you’ll minimize runtime errors and ensure smooth type transitions.