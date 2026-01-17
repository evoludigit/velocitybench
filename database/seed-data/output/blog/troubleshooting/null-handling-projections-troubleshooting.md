# **Debugging Null Handling in JSONB Projections: A Troubleshooting Guide**

## **Overview**
When working with JSONB data in PostgreSQL projections, **null handling** can lead to unexpected behavior—such as missing fields, incorrect default values, or type mismatches. This guide provides a structured approach to diagnosing and fixing null-related issues in JSONB projections.

---

## **Symptom Checklist**
Before diving into fixes, verify the following symptoms:
- **[ ]** Unexpected `null` values in API responses.
- **[ ]** Fields that should have defaults (`0`, `""`, `false`) are `null`.
- **[ ]** Type conversions fail due to `null` values (e.g., casting `null` to `int`).
- **[ ]** Missing fields in JSONB responses when they should exist.
- **[ ]** `WHERE` clauses incorrectly filter out records due to `null` comparisons.

---

## **Common Issues & Fixes**

### **1. Missing Defaults for Null Fields**
**Symptoms:**
- A field should default to `0`, `false`, or `""`, but appears as `null`.

**Root Cause:**
PostgreSQL JSONB projections do not automatically apply defaults.

**Fix:**
Use `COALESCE` and `NULLIF` in SQL projections:
```sql
SELECT
    id,
    JSONB_BUILD_OBJECT(
        'name', name,
        'age', COALESCE(age, 0), -- Defaults to 0 if null
        'is_active', NULLIF(NULLIF(is_active, ''), 'false')  -- Defaults to false if null or empty string
    ) AS user_data
FROM users;
```
**Alternative (Application-Level):**
Process nulls in your backend (e.g., Python, JavaScript):
```javascript
// Example in Express.js (Node.js)
const user = { name: "John", age: null };
const safeUser = {
    ...user,
    age: user.age ?? 0, // Nullish coalescing operator
};
```

---

### **2. Nulls in Type Casting**
**Symptoms:**
- `CAST(jsonb_field->>'value' AS integer)` fails because `null` cannot be cast to `int`.

**Root Cause:**
JSONB fields sometimes contain `null`, and casting `null` to a numeric/boolean type raises an error.

**Fixes:**
- **Use `NULLIF` to filter out nulls before casting:**
  ```sql
  SELECT
      id,
      (NULLIF(jsonb_data->>'score', 'null')::integer) AS score
  FROM games;
  ```
- **Use `COALESCE` with a default value:**
  ```sql
  SELECT
      id,
      COALESCE((jsonb_data->>'score')::integer, 0) AS score
  FROM games;
  ```

---

### **3. Missing Fields in JSONB Projections**
**Symptoms:**
- A field exists in the database but is absent in the response.

**Root Cause:**
- The field might be `null` and filtered out by JSON serialization.
- The field might not be explicitly included in the projection.

**Fixes:**
- **Explicitly include all fields (even nulls):**
  ```sql
  SELECT
      id,
      JSONB_OBJECT(
          'name', name,
          'preferences', preferences,
          'created_at', created_at
      ) AS user_profile
  FROM users;
  ```
- **Use `jsonb_build_object` with all possible keys (including nulls):**
  ```sql
  SELECT
      id,
      (
          SELECT jsonb_build_object(
              'name', name,
              'age', age,
              'preferences', preferences,
              'last_login', last_login
          )
          FROM users
      ) AS user_data
  FROM users;
  ```

---

### **4. Nulls in WHERE Clauses**
**Symptoms:**
- Records are excluded from queries when they should be included.

**Root Cause:**
- `WHERE jsonb_data->>'key' = 'value'` fails if the field is `null`.
- `WHERE jsonb_data ? 'key'` filters out `null` fields.

**Fixes:**
- **Use `jsonb_data ? 'key'` for existence checks (ignores nulls):**
  ```sql
  SELECT * FROM orders
  WHERE jsonb_data ? 'status' AND jsonb_data->>'status' = 'shipped';
  ```
- **Use `IS NULL` explicitly:**
  ```sql
  SELECT * FROM orders
  WHERE (jsonb_data->>'status') IS NULL OR jsonb_data->>'status' = 'shipped';
  ```
- **Use `NULLIF` to avoid `null` comparisons:**
  ```sql
  SELECT * FROM orders
  WHERE NULLIF(jsonb_data->>'status', null) = 'shipped';
  ```

---

### **5. JSONB Path Resolution Issues**
**Symptoms:**
- `jsonb_path_query` or `->>` operators fail due to nested `null` paths.

**Root Cause:**
- A field exists in the JSONB structure but contains `null` at a deeper level.

**Fix:**
- **Use `jsonb_path_query_first` with a fallback:**
  ```sql
  SELECT
      id,
      jsonb_path_query_first(
          jsonb_data,
          '$[*] ? (@.name == "preferences" && @.status == "active")'
      ) AS preferences
  FROM users;
  ```
- **Check for nulls before querying:**
  ```sql
  SELECT
      id,
      CASE
          WHEN jsonb_data ? 'preferences' AND jsonb_data->'preferences' ? 'status'
          THEN jsonb_data->'preferences'->>'status'
          ELSE 'default_status'
      END AS status
  FROM users;
  ```

---

## **Debugging Tools & Techniques**

### **1. Inspect Raw JSONB Data**
Use `to_jsonb()` to see the raw structure:
```sql
SELECT id, to_jsonb(jsonb_data) FROM users WHERE id = 1;
```
- Helps identify **missing keys** or **unexpected `null` values**.

### **2. Use `jsonb_pretty()` for Readability**
```sql
SELECT jsonb_pretty(jsonb_data) FROM users WHERE id = 1;
```
- Makes nested `null` structures easier to spot.

### **3. Log Null Handling in Application Code**
Add debug logs (e.g., in Python):
```python
import json
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    age: int = 0  # Default for null

def handle_nulls(json_data: dict) -> dict:
    if json_data.get("age") is None:
        json_data["age"] = 0
    return json_data

user_data = handle_nulls(user_dict)
```

### **4. Test Edge Cases with `NULL` Values**
Manually insert `null` values and verify:
```sql
INSERT INTO users (name, age) VALUES ('Test', NULL);
SELECT * FROM users WHERE id = 5;  -- Check null handling
```

### **5. Use `pg_dump` for Schema Inspection**
```sh
pg_dump -t users -Fc --column-inserts --data-only db_name > users_dump.dump
```
- Helps identify if `null` values are stored as `NULL` in the database.

---

## **Prevention Strategies**

### **1. Define Explicit Projection Schemas**
Use **Pydantic (Python), Prisma (JS), or GraphQL schemas** to enforce null handling:
```python
from pydantic import BaseModel

class UserResponse(BaseModel):
    name: str
    age: int = 0  # Auto-defaults to 0 if null
    preferences: Optional[dict] = None  # Optional fields

@router.get("/users/{id}")
def get_user(id: int):
    user = db.query("SELECT * FROM users WHERE id = %s", (id,))
    return UserResponse(**user[0][0])
```

### **2. Use JSONB Default Values in Database**
Set column defaults:
```sql
ALTER TABLE users ALTER COLUMN age SET DEFAULT 0;
```
- Ensures `null` → `0` at the database level.

### **3. Standardize Null Handling in API Responses**
- **Frontend:** Use `||` (JavaScript) or `??` (Python) for defaults.
- **Backend:** Use **pipeline operators** (`COALESCE`, `ISNULL`).

### **4. Write Unit Tests for Null Cases**
```python
# Example in Jest (Node.js)
test("Handles null age gracefully", () => {
    const user = { name: "Alice", age: null };
    expect(applyDefaults(user)).toEqual({ name: "Alice", age: 0 });
});
```

### **5. Document Null Behavior in Code**
Add comments or a README in your service:
```python
"""
Null Handling Rules:
- age: Defaults to 0 if null
- preferences: Optional (can be null)
"""
```

---

## **Final Checklist for Null-Free Projections**
✅ **Database Level:**
- [ ] Set column defaults where needed (`ALTER TABLE ... SET DEFAULT`).
- [ ] Use `COALESCE`/`NULLIF` in SQL projections.

✅ **Application Level:**
- [ ] Use ORMs/schemas (Pydantic, GraphQL) to enforce defaults.
- [ ] Log and test `null` edge cases.

✅ **Debugging:**
- [ ] Use `to_jsonb()` and `jsonb_pretty()` to inspect raw data.
- [ ] Test with `NULL` values inserted manually.

By following this guide, you should be able to **quickly identify, debug, and prevent** null-related issues in JSONB projections. 🚀