# **Debugging "Database Capability Manifest and Multi-Target Compilation" – A Troubleshooting Guide**

## **1. Introduction**
This guide focuses on debugging issues related to the **"Database Capability Manifest and Multi-Target Compilation"** pattern, which detects database features at compile-time (or runtime) to generate safe, cross-database SQL. Common problems arise from incorrect feature detection, unsupported SQL constructs, or improper fallback logic.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these issues:

| **Symptom** | **Possible Cause** |
|-------------|-------------------|
| SQL fails when deploying to a non-targeted DB (e.g., PostgreSQL-to-MySQL) | Missing capability check for unsupported syntax (e.g., `FILTER` in MySQL) |
| Code breaks when switching database drivers (e.g., `sqlite3` to `pg`) | Hardcoded queries without runtime checks |
| Errors like `SyntaxError: unknown keyword 'WITH'` or `ambiguous column` | Unsupported SQL features used without detection |
| Performance degradation on some databases | Excessive runtime checks or overly complex SQL generation |
| Build/compile errors due to unsupported preprocessor directives | Incorrect use of `#ifdef` or conditional compilation |

If you see **any of these**, proceed to troubleshooting.

---

## **3. Common Issues & Fixes**

### **3.1. Incorrect Capability Detection (False Positives/Negatives)**
**Symptom:**
`FILTER` works in PostgreSQL but fails in MySQL, even though the code checks `HasFilterClause`.

**Root Cause:**
The capability check is either:
- Missing entirely (hardcoded assumption), or
- Incorrectly implemented (e.g., checks for `PostgreSQL` but allows `FILTER` in MySQL).

**Fix:**
Use a **standardized manifest** (e.g., a `database_features.json` file) to define supported features per DB type.

#### **Example: Correct Implementation**
```python
# database_features.json
{
  "PostgreSQL": { "supports_filter": true, "supports_jsonb": true },
  "MySQL": { "supports_filter": false, "supports_jsonb": false },
  "SQLite": { "supports_filter": false, "supports_jsonb": false }
}

# SQL generator logic
def generate_query(db_type: str, rows: List[Dict]) -> str:
    manifest = load_features(db_type)  # Load from JSON
    if manifest["supports_filter"]:
        return f"SELECT * FROM table WHERE id IN ({', '.join([f'$id_{i}' for i in range(len(rows))])}) FILTER (WHERE something)"
    else:
        return f"SELECT * FROM table WHERE id IN ({', '.join([f'$id_{i}' for i in range(len(rows))])}) AND something"
```

**Debugging Steps:**
✅ Check if the `database_features.json` matches your actual target DB.
✅ Verify that `load_features()` is being called with the correct DB type.
✅ Use `print(manifest)` to confirm feature flags.

---

### **3.2. Hardcoded Assumptions (e.g., PostgreSQL Only)**
**Symptom:**
Code assumes `JSONB` support, causing errors in MySQL.

**Root Cause:**
Missing runtime check or incorrect capability detection.

**Fix:**
Replace assumptions with **explicit feature checks** (e.g., `DB_CAPABILITIES['supports_jsonb']`).

#### **Example: Refactored Code**
```python
# BEFORE (❌ Hardcoded)
query = f"SELECT jsonb_agg(data) FROM results"

# AFTER (✅ Capability Check)
if DB_CAPABILITIES["supports_jsonb"]:
    query = f"SELECT jsonb_agg(data) FROM results"
elif DB_CAPABILITIES["supports_json"]:
    query = f"SELECT json_arrayagg(data) FROM results"
else:  # Fallback for SQLite/old MySQL
    query = f"SELECT GROUP_CONCAT(data) FROM results"
```

**Debugging Steps:**
✅ Search for `jsonb_agg`, `to_jsonb`, or `FILTER` in your codebase.
✅ Run `grep -r "jsonb\|FILTER" .` to find hardcoded uses.

---

### **3.3. Unsupported SQL Syntax Errors**
**Symptom:**
`"Syntax error near 'WITH'"` when running on SQLite (which doesn’t support CTEs).

**Root Cause:**
No check for `WITH` (CTE) support.

**Fix:**
Use a **predefined list of unsupported constructs** per DB.

#### **Example: Fallback Logic**
```python
def generate_query_with_cte(db_type: str, query: str) -> str:
    if db_type not in ["PostgreSQL", "MySQL", "SQLServer"]:
        # Replace CTE with subquery
        return query.replace("WITH x AS (", "")
    return query
```

**Debugging Steps:**
✅ Check for unsupported keywords (`WITH`, `FILTER`, `JSONB`).
✅ Test with a **minimal query** to isolate the issue.

---

### **3.4. Build/Compile Errors (Preprocessor Misuse)**
**Symptom:**
`#ifdef POSTGRES` causes C compilation errors.

**Root Cause:**
Incorrect use of `#ifdef` in non-C/C++ code (e.g., Python/JS).

**Fix:**
Replace with **runtime checks** (e.g., `if db_type == "PostgreSQL"`).

#### **Example: Replacing `#ifdef`**
```python
# BEFORE (❌ For C/C++)
#ifdef POSTGRES
#   return "SELECT jsonb_agg(...)";
#else
#   return "SELECT json_arrayagg(...)";
#endif

# AFTER (✅ Python)
if db_type == "PostgreSQL":
    return "SELECT jsonb_agg(...)"
else:
    return "SELECT json_arrayagg(...)"
```

**Debugging Steps:**
✅ Search for `#ifdef`/`#ifndef` in non-compiled files.
✅ Replace with **dynamic checks** based on `db_type`.

---

### **3.5. Performance Issues from Overly Complex Checks**
**Symptom:**
Slow query generation due to excessive `if-else` chains.

**Root Cause:**
Too many `DB_CAPABILITIES` checks per query.

**Fix:**
**Cache capability flags** and **pre-generate SQL templates**.

#### **Example: Optimized SQL Generation**
```python
# Cache features on first load
FEATURES = load_features(DB_TYPE)

# Use pre-built templates
if FEATURES["supports_jsonb"]:
    return JSONB_TEMPLATE % (param1, param2)
else:
    return FALLBACK_TEMPLATE % (param1, param2)
```

**Debugging Steps:**
✅ Profile slow queries with `timeit`.
✅ Replace nested `if-else` with **lookup tables**.

---

## **4. Debugging Tools & Techniques**

### **4.1. Logging & Assertions**
Log **capability checks** to verify correctness:
```python
print(f"Database: {DB_TYPE}, Supports FILTER: {FEATURES['supports_filter']}")
assert FEATURES["supports_jsonb"], "JSONB unsupported!"
```

### **4.2. Unit Tests for SQL Generation**
Test SQL generation against **different DB types**:
```python
import pytest

def test_postgres_filter():
    db_type = "PostgreSQL"
    query = generate_query(db_type, [...])
    assert "FILTER" in query

def test_sqlite_no_filter():
    db_type = "SQLite"
    query = generate_query(db_type, [...])
    assert "FILTER" not in query
```

### **4.3. Dynamic SQL Validation**
Use tools like **[SQL Fluff](https://www.sqlfluff.com/)** to validate generated SQL:
```bash
sqlfluff lint query.sql --dialect postgresql
sqlfluff lint query.sql --dialect mysql
```

### **4.4. Database-Specific Test Containers**
Run tests in **isolated DB environments** (e.g., Docker):
```dockerfile
# Test PostgreSQL
docker run -it --rm postgres psql -U postgres -c "SELECT * FROM test_table;"
```

---

## **5. Prevention Strategies**

### **5.1. Standardize Capability Detection**
- Use a **shared `database_features` module**.
- Define **explicitly supported/unsupported features**.

### **5.2. Enforce SQL Dialect Checks**
- **Never hardcode SQL** (e.g., avoid `jsonb_path_ops` without checks).
- Use **template-based generation** with fallbacks.

### **5.3. Automated SQL Sanity Checks**
- Run **pre-commit hooks** to validate SQL against target DBs.
- Example GitHub Action:
  ```yaml
  - name: Validate SQL
    run: |
      sqlfluff lint --dialect postgresql --strict queries/*.sql
  ```

### **5.4. Document Database Assumptions**
- Add **comments** explaining why certain features are used:
  ```python
  # MySQL doesn't support positional arguments, so use named placeholders
  query = "SELECT * FROM table WHERE id = %s" % (user_id,)
  ```

### **5.5. Test in Multiple Environments Early**
- **CI/CD pipeline** should test against **PostgreSQL, MySQL, SQLite**.
- Use **feature flags** to isolate DB-specific logic.

---

## **6. Summary of Key Fixes**
| **Issue** | **Quick Fix** |
|-----------|--------------|
| `FILTER` breaks in MySQL | Check `FEATURES["supports_filter"]` |
| `JSONB` unsupported | Use `json_arrayagg` or `GROUP_CONCAT` fallback |
| Hardcoded `WITH` clause | Replace with subquery for SQLite |
| `#ifdef` in wrong language | Replace with runtime checks |
| Slow SQL generation | Cache `DB_CAPABILITIES` and use templates |

---
### **Final Checklist**
✅ **Verify capability checks** (log `DB_CAPABILITIES`).
✅ **Test on all target DBs** (PostgreSQL, MySQL, SQLite).
✅ **Replace hardcoded SQL** with dynamic checks.
✅ **Optimize fallbacks** (avoid excessive `if-else`).
✅ **Add unit tests** for SQL generation.

By following this guide, you should be able to **diagnose and fix** most issues related to the **"Database Capability Manifest"** pattern.