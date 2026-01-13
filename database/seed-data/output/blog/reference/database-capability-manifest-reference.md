---
# **[Pattern] Database Capability Manifest & Multi-Target Compilation – Reference Guide**

---

## **1. Overview**
The **Database Capability Manifest and Multi-Target Compilation** pattern ensures cross-database compatibility in FraiseQL by dynamically detecting supported SQL features (operators, functions, windowing syntax) per target database (PostgreSQL, MySQL, SQLite, SQL Server). The compiler generates database-specific SQL, resolving syntax variations via compile-time introspection of a **capability manifest** and fallback mechanisms (e.g., `FILTER` → `CASE WHEN` for MySQL).

This pattern eliminates runtime errors due to unsupported features, enabling portable queries while preserving performance and readability.

---

## **2. Key Concepts**
| **Term**                     | **Definition**                                                                                     |
|------------------------------|---------------------------------------------------------------------------------------------------|
| **Capability Manifest**      | A JSON/YAML config defining SQL features, operators, and functions available per database target.|
| **SQL Lowering**             | Codegen phase converting FraiseQL ast to target-specific SQL using manifest data.                  |
| **Compile-Time Detection**   | Runtime (compile phase) validation against manifest to detect unsupported features.              |
| **Fallback Rules**           | Predefined transformations for unsupported features (e.g., `FILTER` → `HAVING`).                 |

---

## **3. Schema Reference**

### **3.1. Capability Manifest Schema**
Defines supported features per database. Example (`capabilities.json`):

```json
{
  "databases": {
    "postgresql": {
      "operators": {
        ">==": { "supported": true, "sql_syntax": ">==" },
        "IS NULL": { "supported": true, "sql_syntax": "IS NULL" }
      },
      "aggregations": {
        "FILTER": { "supported": true, "sql_syntax": "FILTER" },
        "ARRAY_AGG": { "supported": true, "fallback": "NULLIF" }
      },
      "window_functions": {
        "LEAD": { "supported": true },
        "LAG": { "supported": true }
      }
    },
    "mysql": {
      "operators": {
        ">==": { "supported": false, "fallback": ">" } // mysql lacks >=, use '>' + 1
      },
      "aggregations": {
        "FILTER": { "supported": false, "fallback": "CASE WHEN" }
      }
    }
  }
}
```

**Fields:**
- `operators`: Syntax for comparison operators.
- `aggregations`: List of supported aggregates and fallbacks.
- `window_functions`: Window function support status.
- `functions`: Custom functions (e.g., `jsonb_extract_path_text`).

---

### **3.2. SQL Lowering Rules**
| **FraiseQL Syntax** | **PostgreSQL Output** | **MySQL Output**          | **SQLite Output**       |
|---------------------|-----------------------|---------------------------|-------------------------|
| `FILTER (col > 0)`  | `FILTER (WHERE col > 0)` | `CASE WHEN col > 0 THEN ...` | `CASE WHEN col > 0 THEN ...` |
| `ARRAY_AGG(col)`    | `array_agg(col)`      | `GROUP_CONCAT(col)`       | `GROUP_CONCAT(col)`     |
| `LEAD(col) OVER()`  | `LEAD(col) OVER()`    | `LAG(col, -1) OVER()`     | Unsupported             |

---

## **4. Implementation Steps**

### **4.1. Define Capabilities**
1. Create a manifest file (e.g., `capabilities.json`) mapping features to databases.
2. Use tools like `jq` or Python to validate manifest syntax:
   ```bash
   jq empty capabilities.json
   ```

### **4.2. Compile-Time Detection**
The FraiseQL compiler parses the manifest and:
1. Validates all queries against `capabilities.databases`.
2. Logs warnings for unsupported features (e.g., `FILTER` in MySQL).
3. Rejects queries with incompatible syntax during compilation.

**Example Failure:**
```sql
-- Compilation error for MySQL
SELECT name FILTER (WHERE length > 5);
```
**Output:**
```
Error: MySQL does not support 'FILTER'. Use 'CASE WHEN'.
```

---

### **4.3. SQL Generation (Lowering)**
The compiler generates database-specific SQL, applying fallbacks. Example:

**Input FraiseQL:**
```sql
SELECT ARRAY_AGG(id) OVER w AS ids
FROM orders
WINDOW w AS (PARTITION BY user_id ORDER BY created_at)
```

**PostgreSQL Output:**
```sql
SELECT ARRAY_AGG(id) OVER (PARTITION BY user_id ORDER BY created_at) AS ids FROM orders;
```

**MySQL Output:**
```sql
SELECT GROUP_CONCAT(id ORDER BY created_at SEPARATOR ',') AS ids
FROM (
  SELECT id, user_id, created_at
  FROM orders
  ORDER BY user_id, created_at
) AS subq
GROUP BY user_id;
```

---

## **5. Query Examples**

### **5.1. Supported Query (Cross-Database)**
```sql
SELECT user_id,
       SUM(amount) FILTER (WHERE is_active = true) AS active_sales
FROM orders
GROUP BY user_id;
```

**PostgreSQL:**
```sql
SELECT user_id, SUM(amount) FILTER (WHERE is_active = true) AS active_sales
FROM orders
GROUP BY user_id;
```

**MySQL:**
```sql
SELECT user_id,
       SUM(CASE WHEN is_active THEN amount ELSE 0 END) AS active_sales
FROM orders
GROUP BY user_id;
```

---

### **5.2. Unsupported Query (Compile Error)**
```sql
SELECT LEAD(created_at) OVER w
FROM orders
WINDOW w AS (PARTITION BY user_id);
```

**MySQL Error:**
```
Error: MySQL does not support 'LEAD'. Use 'LAG' with negative offset.
```

---

## **6. Fallback Strategies**
| **FraiseQL Feature** | **PostgreSQL/SQLite** | **MySQL**                     | **SQL Server**          |
|----------------------|-----------------------|-------------------------------|-------------------------|
| `FILTER`             | Native                | `CASE WHEN`                   | Native                  |
| `ARRAY_AGG`          | Native                | `GROUP_CONCAT`                | `STRING_AGG`            |
| `IS NULL`            | Native                | `IS NULL`                     | Native                  |
| `JSON_EXTRACT`       | `->>`                | `JSON_EXTRACT()`              | `->>`                   |

**Example Fallback Rule (YAML):**
```yaml
fallbacks:
  - feature: FILTER
    mysql:
      pattern: "FILTER (WHERE {condition})"
      replacement: "CASE WHEN {condition} THEN value ELSE NULL END"
```

---

## **7. Related Patterns**
1. **[Database-Driven Query Optimization](https://example.com)**
   Use capability manifests to route queries to optimal databases (e.g., PostgreSQL for JSON, SQLite for embedded).
2. **[Dynamic SQL Generation](https://example.com)**
   Combine with template engines (e.g., Jinja) for runtime SQL tweaks.
3. **[Schema-Evolving Queries](https://example.com)**
   Leverage manifests to handle schema changes gracefully (e.g., dropping deprecated columns).
4. **[Benchmarking Across Databases](https://example.com)**
   Use manifests to compare query performance per target.

---

## **8. Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|------------------------------------------------------------------------------|
| Query fails on MySQL but works elsewhere | Check `capabilities.mysql.aggregations` for missing fallbacks.              |
| Compilation warnings for SQLite      | Add missing features to `capabilities.sqlite` (e.g., `LEAD` is unsupported).|
| Performance degradation              | Audit fallbacks (e.g., `CASE WHEN` is slower than native `FILTER`).          |

**Debug Command:**
```bash
fraise compile --manifest capabilities.json --target mysql --log-level debug
```

---

## **9. Best Practices**
1. **Version Capabilities:** Align manifest versions with database versions (e.g., `postgresql:15`).
2. **Document Fallbacks:** Add comments in the manifest explaining non-obvious transformations.
3. **Test Edge Cases:** Validate queries with empty results or NULL values.
4. **Leverage Extensions:** Use database-specific extensions (e.g., PostgreSQL’s `array_ops`) where possible.

---
**Notes:**
- This pattern assumes FraiseQL’s compiler supports manifest introspection and SQL lowering.
- For custom databases, extend the manifest schema or add a plugin system.