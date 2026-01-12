# **Debugging Data Type Mapping: A Troubleshooting Guide**
*Quickly resolve issues when converting data types across databases*

---

## **1. Introduction**
Data type mismatches between databases are a common source of failures in distributed systems. This guide helps identify, diagnose, and fix issues when converting data types (e.g., SQL → NoSQL, PostgreSQL → MongoDB, or even different versions of the same DBMS).

---

## **2. Symptom Checklist**
Check these signs if you suspect a **Data Type Mapping** issue:

| **Symptom**                          | **Possible Cause**                          |
|--------------------------------------|--------------------------------------------|
| SQL syntax errors in NoSQL inserts | Incorrect type conversion (e.g., `JSON` vs. `TEXT`) |
| Data truncation or null values       | Field mapping error (e.g., `INT` → `VARCHAR` with insufficient length) |
| Unexpected casting errors            | Source DB uses implicit conversion (e.g., `TINYINT` → `TIMESTAMP` without notice) |
| Schema migration failures            | Version-controlled type mappings are outdated |
| Query plan performance degradation   | Suboptimal type casting in joins (e.g., `BIGINT` → `DECIMAL` in calculations) |
| Serialization/deserialization errors| Binary data (e.g., `BLOB`/`BYTEA`) not handled properly |
| Timezone or precision issues          | Date/time types mapped incorrectly (e.g., `TIMESTAMP WITH TIME ZONE` → `DATE`) |

---

## **3. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Database-Specific Type Ambiguities**
Different DBMS treat similar types differently. Example:

#### **Problem:**
- **Source:** PostgreSQL `INTEGER` (4-byte signed) → **Target:** MySQL `INT` (unspecified width)
- **Result:** MySQL may store as `INT(11)` (unpredictable width), causing overflow on large integers.

#### **Fix:**
Explicitly define width or use a common schema dialect (e.g., JSON schema).
```sql
-- Source (PostgreSQL)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    age INTEGER
);

-- Target (MySQL with explicit mapping)
CREATE TABLE users (
    id BIGINT UNSIGNED AUTO_INCREMENT,
    age INT(10)  -- Explicitly map to match PostgreSQL's 4-byte max
);
```

#### **Alternative:** Use a mapping layer (e.g., **ORM** or **DAL**):
```python
# SQLAlchemy (Python ORM) handles implicit mapping
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)  # Maps to DBMS-native INTEGER
```

---

### **Issue 2: Date/Time Zone Handling**
Mismatches between `TIMESTAMP` (with/without timezone) and `DATETIME`/`DATE` can cause silent data corruption.

#### **Problem:**
- **Source:** PostgreSQL `TIMESTAMP WITH TIME ZONE` → **Target:** MySQL `DATETIME`
- **Result:** Timezone conversion fails silently; queries return wrong times.

#### **Fix:**
Use UTC everywhere, or apply timezone-aware casts:
```sql
-- PostgreSQL (source)
SELECT age FROM users WHERE created_at > NOW() - INTERVAL '1 year';

-- MySQL (target) with timezone conversion
SELECT age FROM users WHERE created_at > CONVERT_TZ(NOW(), 'UTC', 'America/New_York');
```

#### **ORM Fix (SQLAlchemy):**
```python
from sqlalchemy import DateTime
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    created_at = Column(DateTime, server_default=func.now())  # Automatically timezone-aware
```

---

### **Issue 3: Text vs. Binary Data**
Automated tools may misinterpret `TEXT` vs. `BLOB`/`BYTEA`.

#### **Problem:**
- **Source:** MySQL `BLOB` → **Target:** PostgreSQL `VARCHAR`
- **Result:** Binary data (e.g., PDFs) stored as garbled text.

#### **Fix:**
Use `BYTEA` in PostgreSQL or encode binary data in JSON:
```sql
-- MySQL (source)
INSERT INTO files (data) VALUES (0x474946383961);  -- Base64/hex-encoded

-- PostgreSQL (target)
INSERT INTO files (data) VALUES (ENCODE(0x474946383961, 'hex'));  -- Handle as binary
```

#### **Application-Layer Fix (Python):**
```python
import base64
from typing import Optional

class File:
    def __init__(self, data: Optional[bytes] = None):
        self._data = data or b""

    def to_db(self) -> str:
        return base64.b64encode(self._data).decode('utf-8')  # Store as TEXT

    @classmethod
    def from_db(cls, encoded_data: str) -> 'File':
        return cls(base64.b64decode(encoded_data))  # Reconstruct binary
```

---

### **Issue 4: Precision Loss in Floating-Point Types**
`FLOAT` in one DB may map to `DOUBLE PRECISION` in another, causing calculation errors.

#### **Problem:**
- **Source:** PostgreSQL `FLOAT` (4 bytes) → **Target:** MongoDB `double` (8 bytes)
- **Result:** No data loss, but precision shifts affect small numbers.

#### **Fix:**
Use `DECIMAL` for monetary/precise calculations:
```sql
-- PostgreSQL (source)
CREATE TABLE products (
    price FLOAT  -- Problematic for financial data
);

-- Target (MongoDB) with explicit mapping
db.products.insertOne({
    "price": 9.99,  // Stored as double (8 bytes)
    "price_decimal": NumberDecimal("9.99")  // Preserves precision
});
```

---

### **Issue 5: Schema Migration Failures**
Outdated migration scripts assume old type mappings.

#### **Problem:**
A migration script updates `VARCHAR(50)` to `VARCHAR(100)` but the target DB uses `TEXT` instead.

#### **Fix:**
Use **versioned migrations** with type-safe checks:
```python
# Alembic (Python migration tool)
def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("username", type_=op.Func("TEXT", ["username"]), nullable=False)
        # Verify type compatibility
        if not op.get_bind().dialect.has_table("users"):
            raise Exception("Target table missing!")
```

#### **Database-Specific Fixes:**
- **PostgreSQL:** Use `ALTER TABLE ... ALTER COLUMN ... TYPE TEXT USING ...`
- **MySQL:** Use `ALTER TABLE ... MODIFY COLUMN username TEXT NOT NULL`

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**               | **Use Case**                                                                 | **Example Command/Code**                          |
|-----------------------------------|-----------------------------------------------------------------------------|--------------------------------------------------|
| **Database DDL Dump**             | Compare schemas between DBs.                                                | `pg_dump -s -d source_db > schema.sql`            |
| **Type Conversion Tests**         | Validate mappings with test data.                                           | `INSERT INTO target VALUES (CAST(source_value AS target_type))` |
| **ORM-Specific Profiling**        | Track type conversions in ORM interactions.                                 | SQLAlchemy: `engine.connect().execute("SELECT * FROM table").fetchall()` |
| **Log Type Casting Errors**       | Enable SQL error logging for implicit casts.                               | PostgreSQL: `log_min_duration_statement = 5000`  |
| **Static Analysis (for Code)**    | Detect unsafe type mappings in application code.                           | `mypy --strict` (Python type checker)            |
| **Serialization Tools**           | Test binary/text conversions (e.g., JSON, protobuf).                       | `echo '{"key": "value"}' | jq '.'` (JSON validator) |
| **Performance Profilers**         | Check if type mismatches cause slow queries.                                | `EXPLAIN ANALYZE SELECT * FROM slow_query;`      |

---

## **5. Prevention Strategies**

### **A. Standardize on a Common Schema Dialect**
- Use **JSON Schema** for NoSQL (MongoDB, DynamoDB).
- For relational DBs, enforce **PostgreSQL-like types** (e.g., `SERIAL` for auto-increment, `TIMESTAMP WITH TIME ZONE`).

### **B. Automated Type Mapping Validation**
- **Unit Tests:**
  ```python
  def test_integer_mapping():
      assert db_source.execute("SELECT CAST(123 AS TEXT)").fetchone() == "123"
      assert db_target.execute("SELECT CAST('123' AS INT)").fetchone() == 123
  ```
- **Integration Tests:** Test migrations in a staging environment.

### **C. Documentation & Annotations**
- **Schema Comments:**
  ```sql
  CREATE TABLE products (
      id SERIAL PRIMARY KEY,
      price DECIMAL(10, 2) COMMENT 'Use DECIMAL for monetary precision'
  );
  ```
- **ORM Metadata:** Annotate fields with expected types (e.g., `@property(type=Decimal)` in Django).

### **D. Use ORMs/DALs with Built-in Mapping**
| **Tool**          | **Feature**                                                                 |
|-------------------|-----------------------------------------------------------------------------|
| SQLAlchemy        | Auto-maps types via `TypeDecorator`.                                       |
| Django ORM        | Uses `Field` classes with `DecimalField`, `DateTimeField`.                 |
| Hibernate (Java)  | Configurable `UserType` mappings.                                          |
| Prisma (TypeScript)| Schema-first approach with strict type inference.                          |

### **E. CI/CD Pipeline Checks**
- **Pre-deploy Schema Validation:**
  ```bash
  # Example: Validate schema before deploying to production
  docker exec db sh -c "psql -U user -d db -c 'SELECT EXISTS(SELECT 1 FROM users)'"
  ```
- **Data Migration Tests:** Run in a staging DB before production.

### **F. Monitoring for Silent Failures**
- **Alert on Type Casting Errors:** Use database audit logs (e.g., PostgreSQL’s `pg_audit`).
- **Logging:** Log implicit type conversions in queries:
  ```sql
  -- Enable implicit casting alerts in PostgreSQL
  SET log_implicit_caast = on;
  ```

---

## **6. Quick Reference Cheat Sheet**
| **Source Type**       | **Common Target Types**       | **Risk**                     | **Fix**                                  |
|-----------------------|-------------------------------|------------------------------|------------------------------------------|
| PostgreSQL `INTEGER`  | MySQL `INT`, MongoDB `int`    | Width mismatch (MySQL)       | Use `BIGINT` or validate width.          |
| PostgreSQL `TEXT`     | MongoDB `string`, DynamoDB `S`| Encoding issues              | Encode as UTF-8 or Base64.               |
| MySQL `BLOB`          | PostgreSQL `VARCHAR`          | Binary data corruption       | Use `BYTEA` or JSON-encoded binary.     |
| SQLite `REAL`         | PostgreSQL `FLOAT`            | Precision loss               | Use `DOUBLE PRECISION` or `DECIMAL`.    |
| MongoDB `ObjectId`    | Relational DB `VARCHAR`       | Unique key collisions        | Use UUID or auto-increment.              |

---

## **7. When to Escalate**
- **Data Loss:** If type mismatches cause irreversible corruption (e.g., binary data lost).
- **Performance Impact:** If implicit conversions degrade query plans (check `EXPLAIN`).
- **Unsupported Types:** If the target DB lacks equivalent types (e.g., PostgreSQL `ARRAY` → NoSQL).

**Next Steps:**
1. Reproduce the issue in a staging environment.
2. Compare schemas with `pg_dump`/`mysqldump`.
3. Use ORM/DAL to abstract mappings.
4. Add automated tests for data integrity.

---
**Final Tip:** Treat type mappings like **external APIs**—document them, test them, and version them.