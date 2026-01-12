```markdown
# **Data Type Mapping: Bridging the Gap Between API and Database**

When you design APIs, you’re not just writing code—you’re building a *contract*. That contract formalizes how clients interact with your system, and at its heart, it dictifies the data shapes they’ll receive. But here’s the tricky part: your database, the heart of your backend, often doesn’t speak the same language as your API.

If you’ve ever sent a JSON response with a `string` field that your database stored as a `JSONB` blob, or returned a `boolean` that your SQL database stored as `TINYINT(1)`, you’ve already encountered **data type mapping**. This isn’t just a minor inconvenience—it’s a pattern that, if approached poorly, can lead to inconsistent data, performance bottlenecks, or even security vulnerabilities.

In this guide, we’ll explore **data type mapping**: why it’s necessary, how to implement it effectively, and how to avoid the common pitfalls that trip up even experienced engineers. By the end, you’ll have a practical, production-ready approach to handling type mismatches between your API and database.

---

## **The Problem: When Databases and APIs Speak Different Languages**

Most developers know that APIs excel at **interoperability**—they provide clean, structured data to clients regardless of their language or platform. Meanwhile, databases are optimized for **storage efficiency, query performance, and atomicity**.

But these two worlds often clash on a fundamental level: **data types**.

### **1. Type Semantics Don’t Always Align**
Consider these common scenarios:

| **API Type**       | **Database Type** | **Problem** |
|--------------------|------------------|-------------|
| `string`           | `TEXT` / `VARCHAR` | How long is "long"? |
| `boolean`          | `TINYINT(1)` / `BIT` | What’s the default? |
| `array` / `object` | `JSONB` / `JSON` | Schema validation vs. dynamic fields |
| `datetime`         | `TIMESTAMP` / `DATETIME` | Timezones, precision, nullability |
| `number`           | `INTEGER` / `DECIMAL(10,2)` | Floating-point vs. fixed precision |

A `boolean` in JSON is a `true` or `false`, but in PostgreSQL, it might be stored as a `TINYINT(1)` with `0`/`1` values. Or worse—missing a proper mapping could mean your API returns `null` when the database returns `-1` (a common convention for `FALSE`).

### **2. Schema Evolution Creates Technical Debt**
When you start, everything is simple. Your API sends `{"status": "active"}` and your database stores it as a `VARCHAR(50)`. But as your app grows:

- Your frontend team wants `true`/`false` instead of `"active"/"inactive"`.
- A new feature requires an `enum` column in the database, but your API still returns strings.
- A third-party client expects `ISO 8601` timestamps, but your backend generates `YYYY-MM-DD` strings.

Without explicit type mapping, these changes become **hidden technical debt**, causing subtle bugs and inconsistent behavior.

### **3. Performance and Storage tradeoffs**
Sometimes, the "right" type in the database isn’t the "right" type for the API.

- **Example 1**: Storing a `JSONB` column for flexibility is great, but querying it requires `->`, `->>`, or `jsonb_path_ops`, which can be slower than indexed fields.
- **Example 2**: Using `INTEGER` for timestamps (Unix epochs) saves space but means your API has to convert to `ISO 8601` for readability.

### **4. Data Integrity Risks**
If your mapping logic isn’t robust, you could:
- Lose precision (e.g., storing `DECIMAL(10,2)` as a `FLOAT`).
- Create invalid data (e.g., writing `{"age": "30"}` to an `INT` column).
- Violate business rules (e.g., sending a `null` to a `NOT NULL` field).

---

## **The Solution: Explicit Data Type Mapping**

The key is **not to assume** that the type in your database should directly map to the type in your API. Instead, you need a **strategic mapping layer** that:

1. **Standardizes data** before it reaches the API.
2. **Validates and sanitizes** input before it touches the database.
3. **Optimizes for both worlds**: the database’s efficiency *and* the API’s usability.

### **Components of a Robust Mapping System**
A complete solution includes:

| **Component**       | **Purpose** | **Example** |
|---------------------|------------|-------------|
| **Input Mappers**   | Convert API payloads to database-ready values | `"age": "30" → 30` |
| **Output Mappers**  | Convert database results to API-friendly JSON | `INT → string (e.g., "active")` |
| **Schema Definitions** | Explicit type contracts between layers | `{ status: { fromDB: "enum", toAPI: "boolean" } }` |
| **Validation**      | Ensure data integrity | Reject `{ age: "thirty" }` |
| **Error Handling**  | Graceful degradation | Return `400 Bad Request` for invalid data |

---

## **Implementation Guide: Step-by-Step**

Let’s build a practical mapping system using **Python (FastAPI) + PostgreSQL**, but the principles apply to any language/framework.

### **1. Define Your Type Mappings Explicitly**
Instead of hardcoding mappings in your queries, define them in a **centralized config** (e.g., a YAML file or a Python dict).

```yaml
# mappings.yaml
status:
  db_type: enum('active', 'inactive', 'pending')
  api_type: boolean
  conversions:
    from_db: { 'active': true, 'inactive': false, 'pending': null }
    to_db: { true: 'active', false: 'inactive', null: 'pending' }
age:
  db_type: integer
  api_type: string
  validate: { min: 0, max: 120 }
```

### **2. Input Mapping: Sanitize Before Storage**
When receiving an API request, validate and transform the data before passing it to the database.

```python
# models/mappers.py
from typing import Dict, Any
from enum import Enum
import yaml

# Load mappings
with open("mappings.yaml") as f:
    MAPPINGS = yaml.safe_load(f)

class DatabaseEnum(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

def map_payload(payload: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert API payload to DB-ready format."""
    mapped = {}
    for field, config in schema.items():
        value = payload.get(field)

        # 1. Validate (e.g., age is a number)
        if "validate" in config:
            if config["validate"].get("min") is not None and value < config["validate"]["min"]:
                raise ValueError(f"{field} must be >= {config['validate']['min']}")
            if config["validate"].get("max") is not None and value > config["validate"]["max"]:
                raise ValueError(f"{field} must be <= {config['validate']['max']}")

        # 2. Type conversion (e.g., boolean → enum)
        if config.get("from_db"):
            if field == "status" and isinstance(value, bool):
                mapped[field] = DatabaseEnum(value).value
            elif field == "age" and isinstance(value, str):
                mapped[field] = int(value)

        else:
            mapped[field] = value

    return mapped
```

### **3. Output Mapping: Format for the API**
When returning data, apply the inverse transformation.

```python
# models/mappers.py
def map_db_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert DB record to API-friendly format."""
    mapped = {}
    for field, config in schema.items():
        value = record.get(field)

        # 1. Handle enums (e.g., "active" → true)
        if config.get("from_db") and field == "status":
            mapped[field] = config["conversions"]["to_db"].get(value, value)

        # 2. Format numbers (e.g., INT → string)
        elif field == "age" and isinstance(value, int):
            mapped[field] = str(value)

        else:
            mapped[field] = value

    return mapped
```

### **4. Integrate with FastAPI**
Now, use these mappers in your routes.

```python
# main.py
from fastapi import FastAPI, HTTPException
from models.mappers import map_payload, map_db_record, MAPPINGS

app = FastAPI()

@app.post("/users/")
async def create_user(user_data: Dict):
    try:
        # 1. Map input to DB format
        db_data = map_payload(user_data, MAPPINGS["user"])

        # 2. Insert into DB (simplified)
        # result = db.execute("INSERT INTO users (...) VALUES (...) RETURNING id")
        # user_id = result[0]["id"]

        # For demo, just return a mock record
        mock_record = {"id": 1, "status": "active", "age": 30}

        # 3. Map output to API format
        api_response = map_db_record(mock_record, MAPPINGS["user"])
        return api_response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### **5. Handle Edge Cases**
- **Null values**: Define how `null` should be handled in both directions.
- **Precision**: Ensure `DECIMAL` fields don’t lose precision when converted to `FLOAT`.
- **Timezones**: Normalize all timestamps to UTC before storage.

```python
# Add to map_payload:
if config.get("db_type") == "timestamp" and value is not None:
    # Convert to UTC if input is a string (e.g., "2023-01-01T12:00:00+00:00")
    mapped[field] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
```

---

## **Common Mistakes to Avoid**

### **1. Assuming 1:1 Type Correspondence**
❌ Bad:
```python
# Just cast and move on—what if the API sends "yes" instead of true?
status = payload["status"]  # type: bool
```

✅ Good:
```python
status = DatabaseEnum(payload["status"]).value  # Explicit conversion
```

### **2. Ignoring Schema Evolution**
- If you start with `VARCHAR` but later switch to `ENUM`, old API calls may fail.
- **Solution**: Use **backward-compatible migrations** and **fallback logic**.

```python
# Example: Handle both "active" (string) and true (boolean)
if isinstance(value, bool):
    return DatabaseEnum.ACTIVE.value
return value  # Assume it's already in enum format
```

### **3. Skipping Input Validation**
- Never trust client data blindly.
- **Solution**: Validate **before** mapping.

```python
# Reject invalid ages early
if not (0 <= float(age) <= 120):
    raise ValueError("Age must be between 0 and 120")
```

### **4. Over-Optimizing for the Database**
- Don’t map everything to `INTEGER` just to save space.
- **Tradeoff**: `INTEGER` saves space but loses readability.
- **Solution**: Balance usability and performance.

### **5. Not Documenting Mappings**
- If a new dev joins, they should know:
  - `status` is an enum, not a string.
  - `age` is stored as `INT` but returned as `string`.
- **Solution**: Document mappings **alongside your API schema**.

---

## **Key Takeaways**
✅ **Don’t assume type equivalence**—explicitly define how data flows between layers.
✅ **Validate before mapping** to catch errors early.
✅ **Standardize on a single representation** (e.g., always use UTC timestamps).
✅ **Handle edge cases** (nulls, invalid inputs, schema changes).
✅ **Document your mappings** to avoid future confusion.
✅ **Avoid over-optimizing for storage**—sometimes readability matters more.

---

## **Conclusion: Type Mapping as a First-Class Concern**

Data type mapping isn’t just a "nice-to-have"—it’s a **critical part of your system’s robustness**. Poor mappings lead to inconsistent data, hard-to-debug issues, and even security vulnerabilities (e.g., SQL injection via unchecked inputs).

By following this pattern, you:
- **Reduce bugs** by validating and sanitizing data early.
- **Improve maintainability** with clear, documented mappings.
- **Future-proof your API** by separating concerns between storage and presentation.

### **Next Steps**
1. **Audit your current system**: Are there places where types don’t align?
2. **Start small**: Pick one model (e.g., `users`) and implement explicit mappings.
3. **Automate validation**: Use tools like **Pydantic** (Python) or **Zod** (TypeScript) to enforce schemas.
4. **Monitor for issues**: Log unexpected type conversions in production.

Type mapping is an investment in **clarity and reliability**—two things no system can afford to neglect.

---
**What’s your experience with data type mapping?** Have you run into tricky edge cases? Share in the comments!

---
```