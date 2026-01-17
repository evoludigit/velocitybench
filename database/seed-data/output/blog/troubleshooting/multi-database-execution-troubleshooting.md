# **Debugging Multi-Database Execution: A Troubleshooting Guide**
*Adapting Query Execution Across PostgreSQL, SQLite, MySQL, and More*

## **Introduction**
The **Multi-Database Execution** pattern allows a single codebase to interact with different database backends (PostgreSQL, SQLite, MySQL, etc.) while maintaining SQL portability. Common issues arise due to syntax differences, unsupported features, or performance bottlenecks.

This guide provides a structured approach to diagnosing and resolving problems efficiently.

---

## **🔍 Symptom Checklist**
Before diving into fixes, verify these symptoms to narrow down the issue:

| Symptom | Description | Likely Cause |
|---------|------------|-------------|
| ✅ Query works in PostgreSQL but fails in SQLite | Syntax incompatibility (e.g., `REGEXP`, window functions) | Database-specific features not abstracted |
| ✅ Performance varies drastically (e.g., fast in PostgreSQL, slow in SQLite) | Missing database optimizations (indexes, query planning) | Lack of backend-specific query tuning |
| ✅ `SQLiteError: unsupported feature` or `PostgresError: syntax error` | Direct SQL injection or unabstracted SQL | Hardcoded SQL or inconsistent ORM usage |
| ✅ Transaction isolation issues (e.g., dirty reads) | Different default transaction settings | Missing isolation level configuration |
| ✅ Schema migrations fail | Database-specific DDL syntax | Inconsistent migration scripts |

---

## **🐞 Common Issues & Fixes**
### **1. Syntax Differences Across Databases**
**Problem:** Some SQL features (e.g., `JOIN`, `GROUP BY`, `REGEXP`) work in PostgreSQL but fail in SQLite.

**Example:**
```sql
-- Works in PostgreSQL but fails in SQLite
SELECT * FROM users WHERE email REGEXP '^[^@]+@[^@]+\.[^@]+$';

-- SQLite alternative:
SELECT * FROM users WHERE email LIKE '%@%.%';
```

**Fix:**
Use a **query adapter** or **ORM abstraction layer** to map features:
```python
# Using SQLAlchemy Core with dialect-aware query rewriting
from sqlalchemy.dialects import postgresql, sqlite

def sanitize_regex(query: str, engine):
    if "REGEXP" in query and "sqlite" in engine.name.lower():
        return query.replace("REGEXP", "LIKE")
    return query
```

---

### **2. Missing Database-Specific Features**
**Problem:** Some databases lack functions (e.g., `CURRENT_TIMESTAMP` vs. `NOW()`).

**Fix:** Use a **feature detection** or **fallback mechanism**:
```python
def get_current_timestamp(db_name: str):
    if db_name.lower() == "postgresql":
        return "CURRENT_TIMESTAMP"
    elif db_name.lower() == "sqlite":
        return "datetime('now')"
    else:  # MySQL default
        return "NOW()"
```

---

### **3. Performance Issues**
**Problem:** A query optimized for PostgreSQL runs slowly in SQLite.

**Debugging Steps:**
1. **Check execution plans** (`EXPLAIN` in PostgreSQL, `EXPLAIN QUERY PLAN` in MySQL).
2. **Verify indexing** (SQLite has weaker auto-indexing than PostgreSQL).
3. **Limit `JOIN` operations** (SQLite performs poorly with many joins).

**Fix:**
```python
# Force SQLite to use a simpler query plan if needed
if "sqlite" in engine.name.lower():
    query = query.limit(1000)  # Reduce result set size
```

---

### **4. Schema Mismatches**
**Problem:** A schema migration fails because `SERIAL` (PostgreSQL) isn’t supported in SQLite.

**Fix:** Use **ORM-level schema definitions** instead of raw SQL:
```python
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)  # PostgreSQL/MySQL: SERIAL, SQLite: INTEGER
    name = Column(String(50))
```

---

### **5. Transaction Isolation Issues**
**Problem:** PostgreSQL allows `REPEATABLE READ`, but SQLite defaults to `READ COMMITTED`.

**Fix:** Set isolation levels explicitly:
```python
# Using SQLAlchemy
from sqlalchemy import create_engine
engine = create_engine("postgresql://...", isolation_level="REPEATABLE READ")
```

---

## **🛠 Debugging Tools & Techniques**
### **1. Log Query Execution**
Enable **query logging** to detect problematic SQL:
```python
from sqlalchemy import event

@event.listens_for(engine, "before_cursor_execute")
def log_query(dbapi_connection, cursor, statement, parameters, context, executemany):
    print(f"Executing: {statement}")
```

### **2. Use Dialect-Specific Debuggers**
- **psycopg2 (PostgreSQL):** `psycopg2.log`
- **SQLAlchemy:** `echo=True` in engine creation
- **SQLite:** `PRAGMA debugging_on = 1` (if available)

### **3. Schema Inspection**
Check for unsupported types or constraints:
```python
# Using SQLAlchemy's inspect
inspector = inspect(engine)
print(inspector.get_table_names())  # Verify tables exist
```

### **4. Benchmark Queries**
Compare execution time across databases:
```python
import time

def time_query(db_name, query):
    engine = create_engine(f"{db_name}://...")
    with engine.connect() as conn:
        start = time.time()
        conn.execute(query)
        print(f"{db_name} took {time.time() - start:.3f}s")
```

---

## **🚀 Prevention Strategies**
### **1. Use an ORM with Good Database Abstraction**
- **SQLAlchemy** (best for PostgreSQL/SQLite/MySQL)
- **Django ORM** (built-in PostgreSQL/SQLite/MySQL support)
- **TypeORM** (for TypeScript/Node.js)

### **2. Write Database-Aware Code**
```python
def get_users(db_type: str, offset: int = 0):
    if db_type == "postgresql":
        return session.query(User).offset(offset).limit(100).all()
    elif db_type == "sqlite":
        return session.query(User).order_by(User.id).offset(offset).limit(100).all()
```

### **3. Test Across Databases Early**
Use **Dockerized databases** for quick testing:
```dockerfile
# Docker Compose for testing
services:
  postgres:
    image: postgres:15
  sqlite:
    image: sqlite:latest
```

### **4. Avoid Raw SQL When Possible**
Prefer ORM methods over direct SQL:
```python
# Bad (raw SQL)
cursor.execute("SELECT * FROM users WHERE email = %s", [email])

# Good (ORM)
users = session.query(User).filter(User.email == email).all()
```

### **5. Document Database Limitations**
Maintain a **database compatibility matrix** (e.g., GitHub Wiki) with:
| Feature          | PostgreSQL | MySQL | SQLite |
|------------------|------------|-------|--------|
| `REGEXP`         | ✅ Yes      | ✅*   | ❌ No  |
| `SERIAL`         | ✅ Yes      | ✅*   | ❌ No  |

---

## **📌 Summary Checklist**
| Task | Action |
|------|--------|
| ✅ **Check syntax errors** | Use query rewriting or ORM |
| ✅ **Benchmark performance** | Compare `EXPLAIN` plans |
| ✅ **Verify schema compatibility** | Use ORM over raw SQL |
| ✅ **Set transaction isolation** | Explicitly define levels |
| ✅ **Log queries** | Debug with `echo=True` |
| ✅ **Test early** | Use Dockerized DBs |

---
**Final Tip:** If debugging a **specific issue**, search for the error message + database name in your ORM’s documentation (e.g., *"SQLite unsupported feature error"* → [SQLAlchemy SQLite docs](https://docs.sqlalchemy.org/en/14/dialects/sqlite.html)).

By following this guide, you can **quickly identify and resolve** multi-database execution problems while maintaining a clean, maintainable codebase. 🚀