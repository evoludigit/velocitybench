---

# **[Pattern] Operator Support Validation Reference Guide**

---

## **1. Overview**
The **Operator Support Validation** pattern ensures that all SQL operators declared in a query schema (e.g., `WHERE` conditions, joins, aggregates) are supported by the target database system. This prevents compilation-time errors by cross-referencing the schema against a **capability manifest**—a predefined list of supported operators for each database vendor (e.g., PostgreSQL, MySQL, Snowflake).

Key benefits:
- **Early error detection**: Fails fast if unsupported operators are used.
- **Database portability**: Enables schema reuse across different databases.
- **Automated validation**: Integrates with build pipelines or runtime checks.

The pattern is typically triggered during schema compilation or query planning, where the validator scans operator definitions (e.g., `=`, `>`, `BETWEEN`, `IN (subquery)`) and verifies their compatibility with the target database’s capability manifest. If a mismatch is found, the system logs a warning or throws an error.

---

## **2. Schema Reference**
The following tables define the core components of the Operator Support Validation pattern.

### **2.1 Core Tables**

| **Table**                  | **Description**                                                                 | **Columns**                                                                                     |
|----------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| `operators`                | Registry of supported operators for a database vendor.                       | `id` (PK), `vendor` (e.g., `postgres`, `snowflake`), `operator` (e.g., `>`, `LIKE`), `type` (binary/comparison/aggregate), `version_min` (e.g., `10.0`) |
| `schema_operators`         | Links a schema to supported operators (for validation).                      | `schema_id` (FK), `operator_id` (FK), `is_required` (boolean)                                   |
| `capability_manifest`     | Predefined capability lists per database vendor.                             | `vendor` (PK), `manifest_version`, `created_at`                                                  |
| `validation_errors`        | Logs operator compatibility issues during schema compilation.                 | `schema_id` (FK), `vendor`, `operator`, `error_message`, `resolved` (boolean)                  |

---

### **2.2 Example Operator Definitions**
The `operators` table includes examples of operator types:

| `vendor`   | `operator` | `type`         | `version_min` | **Notes**                                  |
|------------|------------|----------------|----------------|--------------------------------------------|
| `postgres` | `=`        | binary         | 8.0            | Supported in all versions.                 |
| `postgres` | `BETWEEN`  | binary         | 9.0            | Deprecated in favor of range functions.     |
| `snowflake`| `LIKE`     | binary         | 6.0            | Case-insensitive by default.               |
| `mysql`    | `IN`       | binary         | 5.0            | Supports subqueries **and** value lists.    |
| `bigquery` | `ARRAY_CONTAINS` | aggregate   | 2.0            | Requires explicit schema annotations.      |

---

## **3. Query Examples**
This section demonstrates how the pattern detects unsupported operators and suggests fixes.

### **3.1 Unsupported Operator Example**
**Query (PostgreSQL):**
```sql
SELECT user_id
FROM users
WHERE user_status = 'ACTIVE' AND last_login > CURRENT_TIMESTAMP - INTERVAL '1 year';
```
**Schema Definition:**
```yaml
operators:
  - vendor: "postgres"
    operator: ">"
    type: "binary"
  - vendor: "postgres"
    operator: "INTERVAL"
    type: "aggregate"  # Mistake: `INTERVAL` is a literal, not an operator.
```

**Validation Error:**
```
[ERROR] Operator "INTERVAL" is not supported as a binary operator in PostgreSQL.
Suggested fix: Use `last_login > (CURRENT_TIMESTAMP - INTERVAL '1 year')`.
```

---

### **3.2 Supported Operator Example**
**Query (Snowflake):**
```sql
SELECT department_id, COUNT(*) as employee_count
FROM employees
WHERE hire_date BETWEEN '2020-01-01' AND '2020-12-31'
GROUP BY department_id;
```
**Schema Validation:**
- `BETWEEN` is listed as supported in `operators` for Snowflake (`version_min: 6.0`).
- `COUNT()` is implicitly allowed (aggregate operators are vendor-agnostic unless specified otherwise).

**Result:** No errors. Query is valid.

---

### **3.3 Cross-Vendor Schema Migration**
**Original Schema (PostgreSQL):**
```yaml
schema_operators:
  - operator_id: 12  # PostgreSQL `BETWEEN` (ID `12` in `operators` table)
    is_required: true
```

**Migration to MySQL:**
1. Replace `BETWEEN` with a `>=` and `<=` clause in the query.
2. Update `schema_operators` to reference MySQL’s `>=` operator (ID `3` in `operators`).

**MySQL-Compatible Query:**
```sql
SELECT id
FROM products
WHERE price >= 100 AND price <= 500;
```

---

## **4. Implementation Details**
### **4.1 Key Components**
1. **Capability Manifest Parser**:
   - Loads vendor-specific operator lists from a file/database (e.g., JSON/YAML).
   - Example manifest snippet for PostgreSQL:
     ```yaml
     postgres:
       binary:
         - "="
         - "!="
         - ">"
         - "<"
         - "LIKE"
       aggregate:
         - "COUNT"
     ```

2. **Validator Engine**:
   - Parses SQL schemas (e.g., Presto SQL, HiveQL) to extract operator usage.
   - Cross-references against the manifest via the `operators` table.
   - Logs violations to `validation_errors`.

3. **Resolution Strategies**:
   - **Automatic**: Replace unsupported operators with vendor-specific syntax (e.g., `BETWEEN` → `>= AND <=`).
   - **Manual**: Flag for developer review (e.g., `WARN: 'FULL OUTER JOIN' unsupported in MySQL`).

---

### **4.2 Performance Considerations**
- **Indexing**: Ensure `operators(vendor, operator)` and `schema_operators(schema_id)` are indexed for fast lookups.
- **Batch Validation**: Validate schemas during CI/CD pipelines (e.g., GitHub Actions) to catch issues early.
- **Caching**: Cache capability manifests to avoid repeated database queries.

---

## **5. Related Patterns**
| **Pattern**                     | **Description**                                                                 | **Interaction with Operator Support Validation**                          |
|----------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| **Schema Abstraction Layer**    | Abstracts database specifics (e.g., `BASE_TABLE` → `users`) in a vendor-neutral schema. | Operator validation occurs after schema abstraction to ensure portability. |
| **Dynamic Query Rewriting**     | Converts unsupported operators into supported ones at runtime.               | May override validation warnings but requires careful testing.         |
| **Vendor-Specific Dialects**    | Supports custom dialects (e.g., "BigQuery SQL") with extended capabilities. | Requires updating the capability manifest for new dialects.           |
| **Query Plan Inspection**       | Analyzes the execution plan to detect unsupported operators.                  | Complements validation by catching edge cases (e.g., `LATERAL JOIN` in some dialects). |

---

## **6. Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| False positives (e.g., `LIKE` flagged as unsupported) | Manifest version mismatch.                | Update `manifest_version` in `capability_manifest`.                         |
| Missing operators in manifest.     | Vendor added new operators post-release.   | Extend the manifest or use a dynamic parser (e.g., regex-based).            |
| Performance bottlenecks.           | Large schemas with many operators.         | Pre-compile manifests or use a lightweight in-memory cache.                 |

---

## **7. Example Workflow**
1. **Developer** submits a schema with `WHERE salary > 100K` (assumes `>` is supported).
2. **Build Pipeline** runs the validator:
   - Checks `operators` table for `vendor: "snowflake"`, `operator: ">"` → **valid**.
   - Checks `schema_operators` → marks `>` as required.
3. **Deployment** to Snowflake succeeds.
4. **Audit Logs** confirm no validation errors.

---
**Notes:**
- For complex queries (e.g., UDFs), extend validation to include function signatures.
- Document unsupported operators in the capability manifest with `version_max` to mark deprecations.