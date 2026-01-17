# **[Pattern] GROUP BY with JSONB Dimensions Reference Guide**

---
## **1. Overview**
FraiseQL enables flexible **GROUP BY** operations on **JSONB** columns by dynamically extracting dimensions (e.g., `data->>'field'`) without modifying the database schema. This pattern supports:
- **Single/multiple dimensions** (e.g., `GROUP BY data->>'status', data->>'region'`)
- **Nested paths** (e.g., `data->'metadata'->>'city'`)
- **High performance** (1–3ms for 1M+ rows with GIN indexes)

Unlike traditional aggregate operations (e.g., `GROUP BY table.column`), this approach preserves the **schema-agnostic nature** of JSONB while leveraging PostgreSQL’s native JSONB indexing for speed.

---
## **2. Schema Reference**

| **Component**          | **Description**                                                                                     | **Example**                          |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **JSONB Column**       | Column storing semi-structured data (e.g., `metadata`, `config`).                                 | `{ "status": "active", "region": "us" }` |
| **GIN Index**          | Speeds up JSONB path extraction (mandatory for performance).                                       | `CREATE INDEX idx_jsonb_path ON table USING GIN (data->'metadata');` |
| **Dimension Extraction** | SQL operator to extract scalar values from JSONB: `->>` (text) or `->` (JSONB).                     | `data->>'status'` → `"active"`       |
| **Nested Path**        | Access nested fields (e.g., `metadata` → `city`).                                                  | `data->'metadata'->>'city'` → `"NY"` |

**Schema Example:**
```sql
-- Table with JSONB column and GIN index
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    data JSONB NOT NULL,
    amount DECIMAL(10,2)
);

-- Index for fast path extraction
CREATE INDEX idx_transactions_data ON transactions USING GIN (data);
```

---
## **3. Query Examples**

### **Basic GROUP BY with Single Dimension**
```sql
SELECT
    data->>'status' AS status,
    COUNT(*) AS transaction_count
FROM transactions
GROUP BY data->>'status';
-- Output:
--   status   | transaction_count
-- ──────────+────────────────-
--   active   | 500000
--   inactive | 200000
```

### **GROUP BY with Multiple Dimensions**
```sql
SELECT
    data->>'status' AS status,
    data->>'region' AS region,
    SUM(amount) AS total_amount
FROM transactions
GROUP BY data->>'status', data->>'region';
```

### **GROUP BY with Nested Paths**
```sql
SELECT
    data->'metadata'->>'city' AS city,
    data->>'status' AS status,
    COUNT(*) AS count
FROM transactions
GROUP BY data->'metadata'->>'city', data->>'status';
```

### **Performance-Optimized GROUP BY**
```sql
-- Pre-indexed for speed (1–3ms for 1M rows)
EXPLAIN ANALYZE
SELECT
    data->>'status',
    COUNT(*)
FROM transactions
GROUP BY data->>'status';
-- Index Scan: idx_transactions_data (cost=0.15..2.50 rows=2 width=12)
```

---
## **4. Implementation Details**

### **Key Concepts**
1. **Dynamic Dimension Extraction**
   - Uses PostgreSQL’s `->>` operator to extract text values from JSONB.
   - Supports nested access: `data->'parent'->>'child'`.

2. **GIN Index Optimization**
   - Without a GIN index, `data->>'path'` queries can take **100ms+** for large tables.
   - With a GIN index:
     ```sql
     CREATE INDEX idx_transactions_status ON transactions USING GIN (data->'status');
     ```
     Performance drops to **1–3ms** for 1M rows.

3. **Multiple Dimensions**
   - Group by any combination of JSONB paths:
     ```sql
     GROUP BY data->>'status', data->'metadata'->>'region'
     ```

4. **Aggregations**
   - Works with standard aggregations (`COUNT`, `SUM`, `AVG`):
     ```sql
     SUM(data->>'amount') AS total_spent
     ```

### **Limitations**
- **Case Sensitivity**: `data->>'field'` is case-sensitive (use `jsonb_path_query` for case-insensitive patterns).
- **NULL Handling**: Missing fields return `NULL` in GROUP BY. Use `COALESCE` to default:
  ```sql
  GROUP BY COALESCE(data->>'status', 'unknown')
  ```

---
## **5. Related Patterns**

| **Pattern**                     | **Use Case**                                                                 | **Example** |
|----------------------------------|------------------------------------------------------------------------------|-------------|
| **JSONB Aggregations**           | Compute stats (e.g., `AVG`, `STRING_AGG`) on JSONB fields.                   | `JSONB_EXTRACT_PATH(data, 'metrics', 'value')` |
| **Filtering with JSONB**         | Apply predicates like `WHERE data->>'status' = 'active'`.                    | `data->>'region' IN ('us', 'eu')` |
| **Denormalized Dimensions**      | Store dimensions inside JSONB to avoid schema changes.                        | `{ "category": "books", "price": 20 }` |
| **Materialized JSONB Views**     | Pre-compute GROUP BY results for performance.                              | `CREATE MATERIALIZED VIEW view_transactions AS SELECT ... GROUP BY ...` |

---
## **6. Best Practices**
1. **Index Strategically**
   - Index paths frequently used in `GROUP BY`:
     ```sql
     CREATE INDEX idx_transactions_status ON transactions USING GIN (data->'status');
     ```

2. **Avoid Deep Nests**
   - Deep paths (e.g., `data->'a'->'b'->'c'->>'x'`) slow down queries.

3. **Test NULL Handling**
   - Use `COALESCE` or `FILTER` to exclude NULL values:
     ```sql
     GROUP BY data->>'status' FILTER (data->>'status' IS NOT NULL)
     ```

4. **Use `jsonb_path_query` for Flexibility**
   - Supports wildcards and case-insensitive queries:
     ```sql
     GROUP BY jsonb_path_query(data, '$..status')
     ```