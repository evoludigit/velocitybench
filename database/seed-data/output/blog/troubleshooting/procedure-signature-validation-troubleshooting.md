# **Debugging Procedure Signature Validation: A Troubleshooting Guide**

## **1. Introduction**
This guide focuses on debugging issues related to **Procedure Signature Validation**, where stored procedures fail due to mismatches between:
- Defined parameter signatures
- Actual input mutations
- Expected return types

Common pitfalls include **wrong parameter counts**, **incorrect data types**, or **return type mismatches**. The goal is to quickly identify and resolve discrepancies.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm which symptoms apply:

- **Compile-time errors** (e.g., "Parameter count mismatch")
- **Runtime errors** (e.g., "Type mismatch exception")
- **Unexpected return values** (e.g., `NULL` returned when non-`NULL` expected)
- **Database logs** showing SQL parsing failures
- **API responses** indicating "signature validation failed"
- **Client-side errors** (e.g., TypeScript/JSON schema mismatches)

---

## **3. Common Issues and Fixes**

### **A. Wrong Parameter Count**
#### **Symptom:**
```
PostgreSQL: ERROR: function my_proc(int, int) does not exist
```
or
```
Oracle: PLS-00306: wrong number or types of arguments in call to 'MYPROC'
```

#### **Debugging Steps:**
1. **Check stored procedure signature** (e.g., in `pg_proc` for PostgreSQL or `ALL_ARGUMENTS` in Oracle):
   ```sql
   -- PostgreSQL
   SELECT proname, proargnames, oid FROM pg_proc WHERE proname = 'my_proc';

   -- Oracle
   SELECT * FROM ALL_ARGUMENTS WHERE object_name = 'MYPROC';
   ```
2. **Compare with actual call** (e.g., application logs, ORM query logs).
3. **Fix mismatch** by either:
   - Updating the procedure signature:
     ```sql
     CREATE OR REPLACE PROCEDURE my_proc(int, int, int) AS ...;
     ```
   - Adjusting the caller to match the signature.

---

### **B. Incorrect Parameter Data Types**
#### **Symptom:**
```
TypeError: Argument must be of type "DATE", got "string"
```
or
```
SQLite: near "wrong_value": syntax error (SQLITE_MISUSE)
```

#### **Debugging Steps:**
1. **Verify expected vs. actual types**:
   - **Procedure definition**:
     ```sql
     CREATE PROCEDURE update_user(IN name VARCHAR(50), age INT);
     ```
   - **Application call** (e.g., Python with SQLAlchemy):
     ```python
     # Wrong (string passed where INT expected)
     conn.execute("CALL update_user(?, ?)", ["Alice", "thirty"])
     ```
2. **Fix by**:
   - **Type casting in SQL**:
     ```sql
     CALL update_user(CAST(? AS VARCHAR), CAST(? AS INT));
     ```
   - **Frontend validation** (e.g., TypeScript):
     ```typescript
     const params = [name, Number(age)]; // Ensure age is a number
     ```

---

### **C. Return Type Mismatch**
#### **Symptom:**
```
Expected: { user_id: number }
Actual: { user_id: null }
```

#### **Debugging Steps:**
1. **Check return type in procedure**:
   ```sql
   -- PostgreSQL: function returns SETOF RECORD or specific type
   CREATE OR REPLACE FUNCTION get_user(id INT)
   RETURNS TABLE(user_id INT, name VARCHAR) AS ...;
   ```
2. **Verify API/ORM mapping** (e.g., Django ORM vs. raw SQL):
   ```python
   # Wrong: Assuming single-row return
   user = conn.execute("SELECT * FROM get_user(1)").fetchone()
   ```
3. **Fix by**:
   - **Explicitly handle results**:
     ```python
     # Oracle/PostgreSQL: Use server-side cursors
     cursor = conn.cursor()
     cursor.callproc("get_user", (1,))
     results = cursor.fetchall()  # Return as list of dicts
     ```

---

## **4. Debugging Tools and Techniques**

### **A. Database-Specific Tools**
| Database  | Command/Tool                     | Use Case                          |
|-----------|----------------------------------|-----------------------------------|
| PostgreSQL| `\df+` (PSQL)                    | List all functions/procedures     |
| Oracle    | `DBMS_METADATA.GET_DDL`          | Inspect function signatures       |
| MySQL     | `SHOW CREATE PROCEDURE proc_name` | Verify definition                 |
| SQLite    | `.schema`                        | Check stored procedures           |

### **B. Logging and Tracing**
- **Enable query logging** (e.g., PostgreSQL `log_statement = 'ddl'`).
- **Use WAL/GCS logs** (e.g., Cloud SQL logs for GCP).
- **Client-side logging** (e.g., PgBouncer logs for connection issues).

### **C. Unit Testing**
- **Test procedure signatures** with mock inputs:
  ```python
  # Example with pytest + PostgreSQL
  def test_procedure_signature():
      conn.execute("CALL my_proc(1, 'test')")
      conn.commit()
  ```
- **Use ORM fixtures** (e.g., Django `TestCase` with `django.db.backends`).

### **D. Schema Validation**
- **Compare schemas**:
  ```bash
  # PostgreSQL: Generate schema diff
  pg_dump -s my_db | diff -u /dev/stdin <(pg_dump -s my_db_other)
  ```
- **Tools**:
  - [SQLDelight](https://cashapp.github.io/sqldelight/) (type-safe queries)
  - [Flyway](https://flywaydb.org/) (schema migration tracking)

---

## **5. Prevention Strategies**

### **A. Design-Time Checks**
1. **Document procedure signatures** in README.md:
   ```markdown
   ## API: update_user
   - `IN name` (VARCHAR(50))
   - `IN age` (INT)
   - Returns `INT` (user ID)
   ```
2. **Use ORM schema generators** (e.g., SQLAlchemy auto-generate from DB).
3. **Leverage codegen** (e.g., `sqlx` for Rust, TypeORM for TypeScript).

### **B. Runtime Assertions**
- **Add validation layers**:
  ```sql
  -- Oracle: PL/SQL validation
  CREATE OR REPLACE PROCEDURE safe_update_user(
    IN p_name VARCHAR2,
    IN p_age NUMBER DEFAULT 0
  ) AS
    BEGIN
      IF p_age < 0 THEN
        RAISE_APPLICATION_ERROR(-20001, 'Age cannot be negative');
      END IF;
      -- Rest of logic
    END;
  ```
- **API gateways** (e.g., Kong, Apigee) to validate requests before DB calls.

### **C. Automated Testing**
- **Integration tests** for every procedure call.
- **CI/CD pipeline** to validate signatures post-deploy:
  ```yaml
  # GitHub Actions example
  - name: Run procedure tests
    run: |
      psql -U user -d test_db -f tests/procedure_tests.sql
  ```

### **D. Versioning Strategies**
- **Use schema migrations** (e.g., Alembic, Flyway) to track changes.
- **Tag procedures** for backward compatibility:
  ```sql
  CREATE PROCEDURE update_user_v2(...) -- Add optional parameters
  ```

---

## **6. Quick Reference Table**
| Issue                | Symptom                          | Debug Command                          | Fix Example                          |
|----------------------|-----------------------------------|----------------------------------------|--------------------------------------|
| Parameter count      | `function does not exist`         | `\df+` (PostgreSQL)                    | `ALTER PROCEDURE ... ADD param`      |
| Type mismatch        | `TypeError`                       | `SHOW CREATE PROCEDURE proc_name`      | `CAST(param AS INT)`                 |
| Return type          | `NULL` vs. expected type          | `EXPLAIN get_user(1)`                 | Adjust ORM mapping                    |
| Connection issues    | Timeout/connection refused        | Check `pg_stat_activity`               | Update connection pool settings      |

---

## **7. Conclusion**
By following this guide, you can:
1. **Quickly identify** signature mismatches via logs/DB tools.
2. **Fix issues** with targeted SQL/ORM changes.
3. **Prevent regressions** through validation, testing, and documentation.

**Final Tip**: Always compare **definition** (`CREATE PROCEDURE`) vs. **usage** (call logs/API contracts) when troubleshooting.