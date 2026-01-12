# **[Pattern] Capability Manifest Design Reference Guide**

---

## **Overview**
FraiseQL’s **Capability Manifest Design** pattern standardizes how databases declare supported features (operators, functions, windowing extensions, etc.) via a structured metadata schema. This enables **capability-driven compilation**—where query processing adapts dynamically to the target database’s feature set—rather than relying on a monolithic feature set.

By defining capabilities explicitly, FraiseQL ensures compatibility while optimizing performance by avoiding unnecessary transformations for unsupported operations. The manifest serves as a **contract** between the query planner and database backends, allowing for:
- **Flexible execution** across heterogeneous databases (e.g., DuckDB, ClickHouse).
- **Progressive feature adoption** (new capabilities added without breaking existing queries).
- **Automated schema validation** against supported operators/functions.

---

## **Core Schema Reference**

The **Capability Manifest** is defined as a JSON schema with three primary sections:

| **Field**               | **Type**       | **Description**                                                                                                                                                                                                 | **Examples**                          |
|--------------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------|
| `metadata`               | Object         | Metadata about the manifest version and origin.                                                                                                                                                           | `{ "version": "1.0", "origin": "duckdb" }` |
| `operators`              | Array[Object]  | List of supported **set operators** (e.g., `SELECT`, `JOIN`).                                                                                                                                               | `[ {"name": "SELECT", "args": [...]}, ... ]` |
| `aggregate_functions`    | Array[Object]  | List of supported **aggregations** with their signatures.                                                                                                                                               | `[ { "name": "SUM", "args": [ { "type": "numeric" } ] } ]` |
| `scalar_functions`       | Array[Object]  | List of supported **scalar functions** (e.g., `SIN`, `CONCAT`).                                                                                                                                                    | `[ { "name": "CONCAT", "args": [ { "type": "string" } ] } ]` |
| `window_functions`       | Array[Object]  | List of supported **windowing functions** (e.g., `RANK()`, `LEAD()`).                                                                                                                                       | `[ { "name": "RANK", "over": { "partition_by": [ ... ] } } ]` |
| `expression_support`    | Array[String]  | Optional: List of **SQL expression types** that can be compiled (e.g., `"CASE", "EXISTS"`).                                                                                                              | `[ "CASE", "EXISTS" ]`                |
| `extensions`             | Array[String]  | Optional: Database-specific extensions (e.g., `"timezones", "geospatial"`).                                                                                                                                      | `[ "timezones" ]`                      |
| `limitations`            | Object         | Database-specific **restrictions** (e.g., max window frame size).                                                                                                                                             | `{ "max_window_frame_size": 1000 }`   |

---
### **Example Manifest (DuckDB)**
```json
{
  "metadata": {
    "version": "1.0",
    "origin": "DuckDB",
    "capability_type": "online"
  },
  "operators": [
    { "name": "SELECT", "args": ["expression*", "target*"] },
    { "name": "JOIN", "types": ["INNER", "LEFT"] }
  ],
  "aggregate_functions": [
    { "name": "SUM", "args": [ { "type": "numeric" } ] },
    { "name": "AVG", "args": [ { "type": "numeric" } ] }
  ],
  "window_functions": [
    { "name": "RANK", "over": { "partition_by": "column*", "order_by": "column*" } }
  ],
  "extensions": ["timezones"],
  "limitations": { "max_window_frame_size": 1000 }
}
```

---

## **Query Processing Rules**

FraiseQL uses the manifest to **validate and transform queries** before execution. Key behaviors:

### **1. Operator Validation**
- If a query uses an **unsupported operator** (e.g., a `CROSS JOIN` in a DuckDB manifest that lacks it), FraiseQL emits a **compile-time error**:
  ```
  ERROR: Operator 'CROSS JOIN' not supported by DuckDB (manifest: v1.0).
  ```

### **2. Fallback Mechanism**
- For **unsupported aggregations**, FraiseQL may:
  - **Push down** compatible functions to the database (e.g., `SUM` in DuckDB).
  - **Materialize** intermediate results in memory (for unsupported `WINDOW` functions).

### **3. Extension Handling**
- Databases with `extensions: ["timezones"]` can process timezone-aware operations (e.g., `TIMEZONE('UTC', ts)`), while others fall back to naive datetime handling.

### **4. Window Function Limits**
- If `limitations.max_window_frame_size: 1000`, queries like:
  ```sql
  SELECT RANK() OVER (ORDER BY id ROWS BETWEEN 5000 AND CURRENT ROW)
  ```
  **fail** unless the database supports large frame sizes.

---

## **Query Examples**

### **1. Supported Query (DuckDB Manifest)**
```sql
-- Valid: Uses SUM (supported) and a LEFT JOIN (supported by DuckDB).
SELECT t1.id, SUM(t2.value) as total
FROM table1 t1
LEFT JOIN table2 t2 ON t1.id = t2.id
GROUP BY t1.id;
```
**Execution Flow**:
1. Manifest validates `SUM` and `LEFT JOIN`.
2. Query is compiled for DuckDB without transformations.

---

### **2. Unsupported Query (Fails)**
```sql
-- Invalid: Uses CROSS JOIN (not in DuckDB manifest).
SELECT * FROM orders CROSS JOIN customers;
```
**Error**:
```
ERROR: Operator 'CROSS JOIN' not in DuckDB's capability manifest.
```

---

### **3. Fallback Behavior (Unsupported Window)**
```sql
-- Invalid in DuckDB (small frame size limit), but works in Postgres.
SELECT RANK() OVER (ORDER BY id ROWS BETWEEN 1500 AND CURRENT ROW)
FROM users;
```
**Error (DuckDB)**:
```
ERROR: Window frame size 1500 exceeds max limit of 1000.
```
**Fallback (Memory)**:
If the database supports **partial windowing**, FraiseQL may split the query into chunks:
```sql
-- FraiseQL-generated fallback for unsupported window size.
WITH ranked_1 AS (
  SELECT id, RANK() OVER (ORDER BY id ROWS BETWEEN 1000 AND CURRENT ROW)
  FROM users
),
ranked_2 AS (
  SELECT id, RANK() FROM ranked_1 WHERE window_frame_valid = true
)
SELECT * FROM ranked_2;
```

---

### **4. Extension-Dependent Query**
```sql
-- Valid only in databases with 'timezones' extension (e.g., DuckDB).
SELECT TIMEZONE('UTC', event_time) as utc_time
FROM events;
```
**Error (No Extension)**:
```
ERROR: 'TIMEZONE' function requires 'timezones' extension.
```

---

## **Performance Considerations**

| **Capability**               | **Impact**                                                                 | **Optimization**                                  |
|------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **Set Operators**            | Limits join strategies (e.g., no `CROSS JOIN` in DuckDB).                     | Prefer supported joins (e.g., `INNER/LEFT`).      |
| **Aggregation Support**      | Avoids sharding unsupported `GROUP BY` operations.                          | Use `COUNT(*)` (universal) instead of `APPROX_COUNT`. |
| **Window Functions**         | Large frames may require memory-based processing.                           | Batch window ops or limit frame size.             |
| **Extensions**               | Enables advanced features (e.g., geospatial).                               | Enable extensions only when needed.               |
| **Limitations**              | May truncate results (e.g., `max_window_frame_size`).                       | Rewrite queries to comply with limits.            |

---

## **Related Patterns**

### **1. Pluggable Backend Adaptation**
- **Relation**: The Capability Manifest works alongside the **[Pluggable Backend](link)** pattern to dynamically route queries to compatible databases.
- **Use Case**: A system with DuckDB and ClickHouse backends uses manifests to route `WINDOW` functions to ClickHouse (which supports large frames) and `geospatial` ops to DuckDB.

### **2. Progressive Query Compilation**
- **Relation**: Manifests enable **[Progressive Query Compilation](link)**, where FraiseQL validates capabilities **before** full query parsing, reducing runtime errors.
- **Example**: A query with `CORR()` (correlation) fails fast if the database lacks it, instead of parsing the entire query.

### **3. Dynamic Schema Translation**
- **Relation**: When databases have **incompatible schemas** (e.g., DuckDB’s `PARQUET` vs. ClickHouse’s `CSV`), manifests can **annotate supported formats** and trigger auto-translation.
- **Example**:
  ```json
  "data_formats": ["parquet", "csv"]
  ```
  A query reading `parquet` is translated to `CSV` for ClickHouse via a middleware step.

### **4. Capability-Based Query Routing**
- **Relation**: Used with **[Query Routing](link)** to direct queries to the **best-fit database** based on capabilities.
- **Example**: A query with `RANK()` is routed to ClickHouse (supports large windows), while a `GEO_DISTANCE` query goes to DuckDB.

---

## **Best Practices**

1. **Minimize Manifest Changes**:
   - New capabilities should be **additive** (e.g., extend `window_functions` rather than modify existing ones).
   - Use semantic versioning in `metadata.version` for breaking changes.

2. **Default to Conservative Support**:
   - If unsure about an operator’s support, **omit it** from the manifest. FraiseQL defaults to **blocking unsupported ops** for safety.

3. **Leverage Extensions Wisely**:
   - Extensions like `timezones` or `geospatial` should only be included if the database fully implements them. Partial support leads to unexpected behavior.

4. **Monitor Capability Gaps**:
   - Log warnings when queries hit limitations (e.g., `max_window_frame_size`), allowing operators to adjust queries or upgrade databases.

5. **Test Edge Cases**:
   - Verify manifests against **mixed-workload queries** (e.g., a `JOIN` with an unsupported `WINDOW` function in the same query).

---
## **Troubleshooting**

| **Issue**                          | **Cause**                                  | **Solution**                                  |
|-------------------------------------|--------------------------------------------|-----------------------------------------------|
| Query fails with "unsupported op"   | Manifest lacks the operator.               | Update the database’s manifest or rewrite the query. |
| Window function returns partial data | Frame size exceeds `limitations`.          | Reduce the window frame or use a supported DB. |
| Extension error (e.g., `TIMEZONE`)  | Database lacks the `timezones` extension.   | Enable the extension or use a compatible DB.  |
| Performance degradation             | Fallback to memory for unsupported ops.   | Rewrite queries or use a database with broader support. |

---

## **Further Reading**
- [Pluggable Backend Pattern](link) – How manifests coordinate with backend selection.
- [Progressive Query Compilation](link) – Early-stage capability validation.
- [Query Routing](link) – Dynamic database selection based on manifests.