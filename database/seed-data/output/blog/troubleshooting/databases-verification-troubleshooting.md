# **Debugging Database Integration: A Troubleshooting Guide**
*(Focused on **Database Verification & Validation** Patterns)*

---

## **1. Introduction**
Database verification ensures data consistency, schema integrity, and system reliability. Issues here can lead to:
- **Data corruption** (e.g., invalid records, missing references)
- **Performance degradation** (e.g., slow queries due to missing indexes)
- **Application failures** (e.g., ORM errors, transaction rollbacks)
- **Security risks** (e.g., unauthorized schema changes)

This guide covers **common symptoms, root causes, quick fixes, debugging tools, and prevention** for database verification problems.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these symptoms:

✅ **Application Errors**
- ORM exceptions (e.g., `ForeignKeyConstraintViolation`, `DataIntegrityError`)
- Null pointer exceptions (NPE) due to missing DB records
- `SQLIntegrityError` (e.g., duplicate keys, constraint violations)

✅ **Database-Specific Issues**
- Slow queries (e.g., `EXPLAIN` shows full table scans)
- Unhandled transactions (e.g., open connections, orphaned sessions)
- Schema drift (e.g., missing columns, incorrect data types)

✅ **Performance & Reliability**
- High CPU/memory usage on DB queries
- Timeouts during bulk operations
- Logs showing `Failed to commit transaction`

✅ **Security & Access Issues**
- Permission denied errors (`PermissionError` in Python)
- Unexpected schema changes (e.g., tables altered via `ALTER TABLE`)
- Injection vulnerabilities (e.g., SQL injection attempts)

---

## **3. Common Issues & Fixes**

### **3.1 Issue: Foreign Key Constraint Violations**
**Symptom:** `psycopg2.IntegrityError: foreign key constraint failed` (PostgreSQL) or `SQLITE_CONSTRAINT_FOREIGN_KEY` (SQLite).
**Root Cause:**
- Attempting to delete a parent record referenced by child records.
- Mismatched data types between referencing and referenced columns.

**Quick Fixes:**
**Option 1: Soft Delete (Recommended for Production)**
```python
# Example: Use ON DELETE SET NULL (PostgreSQL/MySQL)
ALTER TABLE child_table ADD CONSTRAINT fk_constraint
    FOREIGN KEY (parent_id) REFERENCES parent_table(id) ON DELETE SET NULL;
```

**Option 2: Temporary Workaround (Dev Only)**
```python
# Bypass constraints (use with caution)
conn.execute("PRAGMA foreign_keys = OFF")  # SQLite
# OR for PostgreSQL/MySQL:
conn.execute("SET FOREIGN_KEY_CHECKS = 0")
# Re-enable later:
conn.execute("SET FOREIGN_KEY_CHECKS = 1")
```

**Option 3: Delete Child Records First**
```python
# Delete children before parent
with conn.cursor() as cur:
    cur.execute("DELETE FROM parent_table WHERE id = %s", (parent_id,))
    conn.commit()  # Ensure transaction completes
```

---

### **3.2 Issue: Data Consistency Violations (NULL/Invalid Data)**
**Symptom:** Application crashes with `NoneType` errors or `ValueError` on type mismatches.
**Root Cause:**
- NULL values where NOT NULL constraints exist.
- String data inserted where numeric types are expected.

**Quick Fixes:**
**Option 1: Validate Input Before Insert**
```python
def insert_user(user_data):
    if not user_data.get("age"):
        raise ValueError("Age cannot be NULL")
    # Use parameterized queries to prevent injection
    conn.execute(
        "INSERT INTO users (name, age) VALUES (%s, %s)",
        (user_data["name"], user_data["age"])
    )
```

**Option 2: Use Database Triggers (PostgreSQL Example)**
```sql
CREATE OR REPLACE FUNCTION validate_age()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.age IS NULL THEN
        RAISE EXCEPTION 'Age cannot be NULL';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_age
BEFORE INSERT OR UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION validate_age();
```

**Option 3: Handle NULL Gracefully in Application**
```python
# Example: Default value for NULL
with conn.cursor() as cur:
    cur.execute(
        "INSERT INTO orders (user_id, status) VALUES (%s, %s)",
        (user_id, "PENDING" if status is None else status)
    )
```

---

### **3.3 Issue: Schema Drift (Mismatched DB & Application Schema)**
**Symptom:** ORM fails to map models (e.g., `No such column` errors).
**Root Cause:**
- Manual SQL migrations not reflected in the app.
- Direct DB edits (e.g., `ALTER TABLE` via admin tools).

**Quick Fixes:**
**Option 1: Auto-Generate Schema (ORM-Based)**
```python
# Flask-SQLAlchemy example
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)  # New column
    # DB will auto-create missing columns on first run

# Run:
python manage.py db upgrade
```

**Option 2: Manual Schema Sync**
```sql
-- Check existing schema
SELECT column_name FROM information_schema.columns WHERE table_name = 'users';

-- Add missing column
ALTER TABLE users ADD COLUMN email VARCHAR(120) UNIQUE NOT NULL;
```

**Option 3: Version Control Migrations (Best Practice)**
Use tools like:
- **Flask-Migrate** (`flask db migrate -m "add_email_column"`)
- **Alembic** (SQLAlchemy) (`alembic revision --autogenerate -m "fix_schema"`)

---

### **3.4 Issue: Transaction Issues (Open Connections/Timeouts)**
**Symptom:** `OperationalError: connection still open` or `TransactionRollbackError`.
**Root Cause:**
- Forgetting to `commit()` or `rollback()`.
- Long-running transactions blocking DB.

**Quick Fixes:**
**Option 1: Explicit Transaction Management**
```python
try:
    with conn.cursor() as cur:
        cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s",
                   (amount, account_id))
    conn.commit()  # Explicit commit
except Exception as e:
    conn.rollback()
    raise e
```

**Option 2: Timeout Configuration (PostgreSQL Example)**
```sql
-- Set transaction timeout (in ms)
SET statement_timeout = '30000';  -- 30 seconds
```

**Option 3: Connection Pooling (Prevent Leaks)**
```python
# Example: SQLAlchemy connection pooling
app.config['SQLALCHEMY_POOL_SIZE'] = 5
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 10
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
```

---

### **3.5 Issue: Slow Queries (Full Table Scans)**
**Symptom:** Queries taking >1s, high DB CPU usage.
**Root Cause:**
- Missing indexes on `WHERE`/`JOIN` columns.
- Poorly optimized queries (e.g., `SELECT *`).

**Quick Fixes:**
**Option 1: Add Indexes**
```sql
-- Add index for a frequently queried column
CREATE INDEX idx_users_email ON users(email);
```

**Option 2: Optimize Queries**
```python
# Bad: SELECT * (returns all columns)
users = session.query(User).all()

# Good: Select only needed columns
users = session.query(User.id, User.email).all()
```

**Option 3: Use `EXPLAIN` to Debug**
```sql
-- PostgreSQL example
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```
**Expected Output:**
- Should use an index (`Index Scan`), not a full table scan (`Seq Scan`).

---

### **3.6 Issue: Permission Denied (DB Access Errors)**
**Symptom:** `psycopg2.OperationalError: permission denied`.
**Root Cause:**
- User lacks `SELECT`, `INSERT`, or `ALTER` privileges.
- Schema ownership mismatch.

**Quick Fixes:**
**Option 1: Grant Permissions**
```sql
-- Grant SELECT, INSERT, UPDATE on a table
GRANT SELECT, INSERT, UPDATE ON users TO app_user;
```

**Option 2: Change Schema Owner**
```sql
ALTER SCHEMA public OWNER TO app_user;
```

**Option 3: Use a Dedicated DB User**
```bash
# Create user with restricted access
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE db_name TO app_user;
```

---

## **4. Debugging Tools & Techniques**

### **4.1 Database-Specific Tools**
| Tool/Feature          | Purpose                                  | Example Command/Usage                     |
|-----------------------|------------------------------------------|-------------------------------------------|
| **PostgreSQL**        | `pgAdmin`, `psql`, `EXPLAIN`             | `psql -U user -d db_name`                 |
| **MySQL**             | `MySQL Workbench`, `SHOW PROCESSLIST`    | `SHOW INDEX FROM users;`                  |
| **SQLite**            | `.schema` command                       | `.schema users`                          |
| **Redis**             | `INFO`, `KEYS`                          | `INFO stats`                              |
| **MongoDB**           | `explain()`                             | `db.users.find().explain()`               |

### **4.2 Logging & Monitoring**
- **Enable DB Logging:**
  ```ini
  # PostgreSQL postgresql.conf
  log_statement = 'all'  # Log all SQL queries
  log_min_duration_statement = 1000  # Log slow queries (>1s)
  ```
- **APM Tools:**
  - **New Relic**, **Datadog**, or **Prometheus + Grafana** for query metrics.

### **4.3 Stress Testing**
- **Simulate High Load:**
  ```bash
  # Use `ab` (ApacheBench) to test DB under load
  ab -n 1000 -c 100 http://localhost/api/orders
  ```
- **Check for Deadlocks:**
  ```sql
  -- PostgreSQL: Find locked transactions
  SELECT * FROM pg_locks;
  ```

---

## **5. Prevention Strategies**

### **5.1 Schema Management**
- **Use ORM Migrations** (Alembic, Flask-Migrate).
- **Never modify DB directly in production** (use migrations).
- **Document schema changes** in a `CHANGELOG.md`.

### **5.2 Data Validation**
- **Client-Side Validation** (React/Vue forms).
- **Server-Side Validation** (Pydantic, Django Forms).
- **Database-Level Constraints** (NOT NULL, CHECK, UNIQUE).

**Example: Pydantic Validation**
```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    name: str
    age: int

    @validator('age')
    def age_must_be_positive(cls, value):
        if value <= 0:
            raise ValueError("Age must be positive")
        return value
```

### **5.3 Transaction Safety**
- **Follow the "Commit Early" Principle** (small transactions).
- **Use `@property` or `@cached_property` for computed fields** (avoid redundant queries).
- **Set reasonable timeouts**:
  ```python
  # Flask-SQLAlchemy timeout
  app.config['SQLALCHEMY_COMMIT_TEARDOWN'] = True
  app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
  ```

### **5.4 Monitoring & Alerts**
- **Set up alerts for:**
  - High query latency (`>500ms`).
  - Connection leaks (`>100 open connections`).
  - Failed transactions (`>5 rollbacks/hour`).
- **Tools:**
  - **UptimeRobot** (simple health checks).
  - **Sentry** (error tracking).

### **5.5 Backup & Rollback Plan**
- **Automated Backups:**
  ```bash
  # PostgreSQL: pg_dump to S3
  pg_dump -U user -d db_name | aws s3 cp - s3://backups/db_name.sql
  ```
- **Test Restores** (simulate disaster recovery).

---

## **6. Quick Checklist for Fast Resolution**
| Step               | Action                                                                 |
|--------------------|-----------------------------------------------------------------------|
| **1. Check Logs**  | Review DB/application logs for errors.                                |
| **2. Reproduce**   | Isolate the issue (e.g., run a specific query).                       |
| **3. Examine Schema** | Compare expected vs. actual schema.                                   |
| **4. Test Fixes**  | Apply small changes (e.g., add an index) and verify.                  |
| **5. Monitor**     | Use `EXPLAIN` or APM tools to confirm improvement.                     |
| **6. Document**    | Update runbooks for future incidents.                                 |

---

## **7. When to Escalate**
- **DB performance degradation** (e.g., 10x slower queries).
- **Data corruption** (e.g., phantom records).
- **Security breach** (e.g., unauthorized schema access).

**Escalation Steps:**
1. **Capture a full DB dump** (for analysis).
2. **Engage DBAs** if the issue is schema-related.
3. **Review audit logs** for suspicious activity.

---

## **8. Summary of Key Takeaways**
| Issue Type               | Common Fixes                                                                 |
|--------------------------|------------------------------------------------------------------------------|
| **Constraint Violations** | Use `ON DELETE CASCADE` or validate data early.                             |
| **Schema Drift**         | Use migrations (Alembic/Flask-Migrate).                                      |
| **Slow Queries**         | Add indexes, optimize queries, use `EXPLAIN`.                               |
| **Permission Issues**    | Grant proper roles (`SELECT`, `INSERT`).                                     |
| **Transaction Problems** | Commit early, set timeouts, use connection pooling.                         |

---
**Final Note:** Database issues often require **systemic fixes** (e.g., schema changes) rather than quick patches. Always **validate in staging** before production deployment.

---
**End of Guide.**
*Next Steps: Apply these fixes iteratively and monitor for regressions.*