```markdown
# **Data Type Mapping: The Backend Developer’s Guide to Smooth Database Conversions**

*How to handle type mismatches when databases and APIs don’t play nice together.*

---

## **Introduction**

Imagine this: You’re building a robust REST API to manage user profiles. Your frontend team sends JSON with timestamps like this:

```json
{
  "user": {
    "id": 123,
    "name": "Alice",
    "created_at": "2023-10-15T12:00:00.000Z"
  }
}
```

You store this data in PostgreSQL, which happily accepts the string `"2023-10-15T12:00:00.000Z"` as a text type. But then your devops team suggests switching to MySQL for cost reasons. Oops—now your timestamp field is a `TEXT` column, but your application expects a `DATETIME`.

This mismatch isn’t just a one-off issue. Different databases have different type systems, and even within the same database, types evolve. Maybe `INT` is fine today, but tomorrow your database vendor introduces `BIGINT` for security reasons. Without a plan, type inconsistencies will creep into your system, causing:

- **Data corruption** (e.g., storing a timestamp as a string in a numeric column).
- **Performance bottlenecks** (e.g., inefficient type casting during queries).
- **Development headaches** (e.g., debugging `SQLSTATE[22007]` errors when your app sends wrong types).

That’s where **data type mapping** comes in. This pattern ensures your application and database speak the same language, no matter the environment or schema changes.

---

## **The Problem: Databases and APIs Don’t Always Agree**

### **1. Database-Specific Quirks**
Different databases treat types differently:
| Database  | Preferred Timestamp Type | Preferred Numeric Type |
|-----------|--------------------------|-------------------------|
| PostgreSQL| `TIMESTAMP WITH TIME ZONE` | `BIGINT` (or `NUMERIC`) |
| MySQL     | `DATETIME`               | `INT` (or `DECIMAL`)    |
| MongoDB   | Object (`{ date: ISOString }`) | `NumberLong` |

If your app assumes PostgreSQL’s `TIMESTAMP` but writes to MySQL’s `TEXT`, you’ll get errors or incorrect data.

### **2. API ↔ Database Mismatches**
REST APIs often use JSON’s flexible types (e.g., booleans as `"true"` strings), but databases expect stricter formats:
- JSON: `{"is_active": true}`
- SQL (PostgreSQL): `bool` column
- SQL (MySQL): `TINYINT(1)` column

If your API ignores this, your database will reject the data or silently convert it (which is *never* safe).

### **3. Schema Evolution Chaos**
When you add a new field:
```sql
-- Original table (PostgreSQL)
ALTER TABLE users ADD COLUMN balance NUMERIC(10, 2);
```
But your API was sending a `float` (JavaScript) or `DOUBLE` (Python) instead of `NUMERIC`, and now it’s being rounded incorrectly.

### **4. Legacy Systems**
Old databases (e.g., Oracle, SQL Server) might use `VARCHAR2` or `NVARCHAR` for strings, while modern apps use UTF-8. If you don’t handle this, you’ll corrupt non-ASCII characters.

---

## **The Solution: Data Type Mapping**

The **data type mapping** pattern ensures your application and database communicate using a **shared canonical type system**. Here’s how it works:

1. **Define a canonical type system** (e.g., in your API/ORM layer) that abstracts database specifics.
2. **Automate conversions** between:
   - Client types (JSON, gRPC, XML).
   - Database types (PostgreSQL, MySQL, MongoDB).
   - Intermediate types (e.g., Python `datetime` vs. SQL `TIMESTAMP`).
3. **Handle edge cases** (nulls, time zones, precision loss).

### **Components of the Solution**
| Component               | Purpose                                                                 |
|-------------------------|--------------------------------------------------------------------------|
| **Type Registry**       | Maps database types ↔ application types (e.g., `JSON` ↔ `PostgreSQL JSONB`). |
| **Conversion Layer**    | Translates types during:
  - API request/response parsing.
  - Database query binding.
  - Schema migrations.                            |
| **Validation Rules**    | Ensures types match expectations (e.g., reject `INT` where `DECIMAL` is needed). |
| **Fallback Strategies** | Handles unsupported types (e.g., store JSON as `TEXT` if no native type exists). |

---

## **Implementation Guide: Code Examples**

### **1. Defining a Type Registry (Python Example)**
Use a dictionary to map database types to application types. This lives in your ORM or DTO layer.

```python
# types.py
from enum import Enum
from typing import Dict, Optional
import json

class DatabaseType(Enum):
    POSTGRES_TIMESTAMP = "TIMESTAMP WITH TIME ZONE"
    MYSQL_DATETIME = "DATETIME"
    TEXT = "TEXT"
    JSON = "JSONB"  # PostgreSQL
    DECIMAL = "DECIMAL(10, 2)"

class AppType(Enum):
    DATETIME = "datetime"  # Python's datetime
    STRING = "str"
    FLOAT = "float"
    JSON_OBJECT = "dict"   # Python dict

# Registry: DatabaseType → AppType conversion rules
TYPE_REGISTRY: Dict[DatabaseType, AppType] = {
    DatabaseType.POSTGRES_TIMESTAMP: AppType.DATETIME,
    DatabaseType.MYSQL_DATETIME: AppType.DATETIME,
    DatabaseType.TEXT: AppType.STRING,
    DatabaseType.JSON: AppType.JSON_OBJECT,
    DatabaseType.DECIMAL: AppType.FLOAT,
}

# Reverse lookup (for database schema generation)
REVERSE_REGISTRY: Dict[AppType, DatabaseType] = {
    AppType.DATETIME: DatabaseType.POSTGRES_TIMESTAMP,
    AppType.STRING: DatabaseType.TEXT,
    AppType.JSON_OBJECT: DatabaseType.JSON,
    AppType.FLOAT: DatabaseType.DECIMAL,
}
```

### **2. Converting Types in an API Handler (FastAPI)**
When parsing requests or building queries, use the registry to enforce type safety.

```python
# schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import json

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    balance: float = Field(..., ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# In your FastAPI route:
from fastapi import FastAPI, HTTPException
import psycopg2  # PostgreSQL driver

app = FastAPI()

@app.post("/users/")
def create_user(user: UserCreate):
    # Convert app types to database types
    db_types = {
        "name": TYPE_REGISTRY[DatabaseType.TEXT],
        "balance": TYPE_REGISTRY[DatabaseType.DECIMAL],
        "created_at": TYPE_REGISTRY[DatabaseType.POSTGRES_TIMESTAMP],
    }

    # Validate: Ensure all fields have matching types
    for field, app_type in db_types.items():
        if not hasattr(user, field) or not type(getattr(user, field)) in [
            AppType.STRING.value,
            AppType.FLOAT.value,
            AppType.DATETIME.value,
        ]:
            raise HTTPException(status_code=400, detail=f"Invalid type for {field}")

    # Prepare SQL query with type-safe binding
    query = """
        INSERT INTO users (name, balance, created_at)
        VALUES (%s, %s, %s)
    """
    conn = psycopg2.connect("dbname=test user=postgres")
    cursor = conn.cursor()

    # Convert Python types to PostgreSQL-ready values
    values = (
        user.name,               # str → TEXT
        str(user.balance),       # float → DECIMAL (as string to preserve precision)
        user.created_at.isoformat(),  # datetime → TIMESTAMP
    )
    cursor.execute(query, values)
    conn.commit()
    conn.close()
```

### **3. Handling JSON in NoSQL (MongoDB Example)**
If your backend uses MongoDB, map JSON fields to BSON types.

```python
# mongo_mapping.py
from pymongo import MongoClient
from bson import ObjectId, Decimal128

def ensure_type(obj: dict, target_type: AppType) -> dict:
    """Convert a dict to match MongoDB's expected types."""
    if target_type == AppType.JSON_OBJECT:
        return obj  # Already a Python dict
    elif target_type == AppType.FLOAT:
        return {"price": str(obj["price"])}  # Store as string to avoid BSON Decimal loss
    elif target_type == AppType.DATETIME:
        return {"date": obj["date"].isoformat()}  # ISO string for MongoDB's Date
    else:
        raise ValueError(f"Unsupported type: {target_type}")

# Usage in a MongoDB model:
client = MongoClient("mongodb://localhost:27017")
db = client.test_db

def insert_product(product: dict):
    # Assume product = {"name": "Laptop", "price": 999.99, "date": datetime.utcnow()}
    mapped_product = ensure_type(product, AppType.JSON_OBJECT)
    mapped_product["price"] = Decimal128(str(product["price"]))  # Force precise decimal
    db.products.insert_one(mapped_product)
```

### **4. Schema Migration Tool (SQLAlchemy Example)**
When updating a database schema, use the registry to generate type-safe migrations.

```python
# migrate.py
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import TIMESTAMP, DECIMAL

def generate_migration(new_schema: dict):
    """Convert app schema → database schema with type mapping."""
    metadata = MetaData()
    table = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(255), nullable=False),
        Column("balance", DECIMAL(10, 2), nullable=False),  # Mapped from AppType.FLOAT
        Column("created_at", TIMESTAMP(timezone=True), server_default=func.now()),
    )
    engine = create_engine("postgresql://user:pass@localhost/test")
    metadata.create_all(engine)
```

---

## **Common Mistakes to Avoid**

1. **Ignoring Null Handling**
   - *Problem*: Your app sends `NULL` for optional fields, but the database treats `NULL` as `0` or `''`.
   - *Fix*: Explicitly cast to `NULL` in your ORM or query builder.
     ```sql
     INSERT INTO users (name, balance) VALUES (%s, NULL)  -- Ensure NULL is passed as NULL
     ```

2. **Precision Loss with Numeric Types**
   - *Problem*: Storing a `FLOAT(64)` in MySQL’s `INT` truncates decimals.
   - *Fix*: Use `DECIMAL` for financial data and convert early.
     ```python
     # Bad: Python float → MySQL INT
     values = (user.balance,)  # 999.99 becomes 999

     # Good: Python float → MySQL DECIMAL
     values = (str(user.balance),)  # 999.99 preserved
     ```

3. **Time Zone Confusion**
   - *Problem*: PostgreSQL’s `TIMESTAMP WITH TIME ZONE` vs. MySQL’s `DATETIME`.
   - *Fix*: Normalize to UTC in your app.
     ```python
     from datetime import datetime, timezone
     user.created_at = user.created_at.astimezone(timezone.utc)
     ```

4. **Assuming JSON is Universal**
   - *Problem*: Storing everything as JSON in MongoDB or PostgreSQL `JSONB` can break queries.
   - *Fix*: Use native types where possible (e.g., `TIMESTAMP` instead of `{"date": "2023-10-15"}`).

5. **Hardcoding Database-Specific Code**
   - *Problem*: Writing `SELECT * FROM users WHERE created_at > '2020-01-01'` without parameterization.
   - *Fix*: Use ORMs or query builders that handle type conversion.
     ```python
     # SQLAlchemy (type-safe)
     query = session.query(User).filter(User.created_at > datetime(2020, 1, 1))
     ```

6. **Not Testing Edge Cases**
   - *Problem*: Your app works for `2023-01-01`, but fails for `2023-12-31T23:59:59.999Z`.
   - *Fix*: Add tests for:
     - Maximum/minimum values (e.g., `BIGINT` overflow).
     - Time zone boundaries (e.g., DST transitions).

---

## **Key Takeaways**

✅ **Define a canonical type system** (e.g., Python `datetime` → `PostgreSQL TIMESTAMP`).
✅ **Automate conversions** in your ORM, API layer, or schema migrations.
✅ **Validate types early** (e.g., reject `INT` where `DECIMAL` is required).
✅ **Handle time zones and precision** explicitly (don’t rely on database defaults).
✅ **Test with real-world data** (not just happy paths).
✅ **Document your mappings** for future developers.
✅ **Use tools** like:
   - SQLAlchemy (for ORM type mapping).
   - Pydantic (for API validation).
   - Custom converters (for database-specific quirks).

---

## **Conclusion**

Data type mapping might seem like a niche concern, but it’s the invisible glue that keeps your backend from falling apart when databases, APIs, and applications evolve. By treating type conversions as first-class citizens—with registries, validation, and clear boundaries—you’ll save yourself (and your team) countless debugging sessions.

### **Next Steps**
1. **Audit your current system**: Where are your type mismatches? Use tools like `pg_get_functiondef` (PostgreSQL) to inspect stored procedures.
2. **Start small**: Pick one field (e.g., `created_at`) and enforce strict type mapping.
3. **Automate**: Integrate type checks into your CI pipeline (e.g., fail tests if a `float` is sent where `DECIMAL` is expected).
4. **Share your registry**: Make your type mappings a team document so everyone knows the rules.

Type consistency isn’t just good practice—it’s how you build systems that scale without breaking. Now go forth and map those types!

---
**Further Reading**
- [SQLAlchemy Type System](https://docs.sqlalchemy.org/en/14/core/type_basics.html)
- [Pydantic Type Validation](https://pydantic-docs.helpmanual.io/usage/types/)
- [PostgreSQL vs. MySQL Type Differences](https://www.cybertec-postgresql.com/en/how-postgresql-differ-from-mysql/)
```