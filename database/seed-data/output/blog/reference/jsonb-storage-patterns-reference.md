# **[Pattern] JSONB Storage Patterns Reference Guide**

---

## **Overview**
FraiseQL leverages **PostgreSQL’s `JSONB`** for flexible semi-structured data storage, offering a middle ground between fully normalized relational tables and loose key-value stores. This pattern defines **when to use `JSONB` vs. normalized columns**, optimal **indexing strategies (GIN/GiST)**, and **query performance trade-offs** to maximize efficiency for common use cases.

Key benefits:
✅ **Schema flexibility** – Accommodates evolving data without migrations.
✅ **Query efficiency** – Supports complex nested queries with GIN indexes.
✅ **Performance balance** – Avoids over-normalization while mitigating JSONB’s overhead.

---
## **Schema Reference**

### **1. When to Use `JSONB` vs. Normalized Columns**
| **Use Case**               | **Recommended Storage**       | **Notes**                                                                 |
|----------------------------|-------------------------------|---------------------------------------------------------------------------|
| **Highly structured data** (e.g., user profiles with fixed fields) | **Normalized columns**       | Use JSONB only if data is **dynamic** (e.g., arbitrary metadata).         |
| **Dynamic metadata**       | **JSONB**                    | Example: `metadata → { "tags": ["tech", "ai"], "last_updated": "2024-01-01" }` |
| **Hierarchical data**      | **JSONB (nested arrays)**     | Example: `products → { "features": [{ "name": "A", "spec": {"value": 10}}] }` |
| **Low cardinality tags**   | **Normalized (e.g., `tags` table)** | Use JSONB only if tags are **rarely queried independently**.            |
| **Geospatial data**        | **JSONB (`{ "lon": -73.935, "lat": 40.730 }`)** | Pair with **GiST indexes** for spatial queries.                         |
| **Large text blobs**       | **JSONB (`content: text`)**   | Avoid if full-text search is critical (use `tsvector` + GIN instead).   |

---

### **2. GIN vs. GiST Indexing Strategy**
PostgreSQL provides two primary indexing options for `JSONB`:

| **Index Type** | **Use Case**                          | **Performance**                     | **Example Command**                          |
|----------------|---------------------------------------|--------------------------------------|----------------------------------------------|
| **GIN (Generalized Inverted Index)** | Full-text search, array operations, nested paths | Fast for **key lookups, wildcards (`->>`)** | `CREATE INDEX idx_user_metadata ON users USING GIN (metadata jsonb_path_ops);` |
| **GiST (Generalized Search Tree)** | Geospatial queries (`@>`, `<@`, `<>` operators) | Optimized for **`jsonb_ops`**      | `CREATE INDEX idx_product_location ON products USING GiST (location jsonb_path_ops);` |

**Best Practice:**
- Use **GIN** for **string/path-based queries** (e.g., `WHERE metadata->>'color' = 'red'`).
- Use **GiST** for **containment checks** (e.g., `WHERE data @> '{"status": "active"}'`).

---

### **3. Recommended Column Types for JSONB Data**
| **Data Type**       | **Use Case**                          | **Example**                                  |
|---------------------|---------------------------------------|----------------------------------------------|
| `jsonb`             | Full JSONB column (flexible storage)  | `metadata jsonb DEFAULT '{}'::jsonb`         |
| `jsonb[]`           | Array of JSONB objects                | `tags jsonb[] DEFAULT '[]'::jsonb[]`         |
| `text` (serialized) | When JSONB is immutable (e.g., logs)  | Store as `text` + parse manually if needed  |

---

## **Query Examples**

### **1. Basic JSONB Queries**
```sql
-- Insert JSONB data
INSERT INTO users (id, metadata)
VALUES (1, '{"name": "Alice", "preferences": {"theme": "dark"}}'::jsonb);

-- Query nested values
SELECT id, metadata->>'name' AS name
FROM users
WHERE metadata->>'name' LIKE '%Alice%';

-- Check if a key exists
SELECT id FROM users
WHERE metadata ? 'preferences';
```

### **2. Array Operations**
```sql
-- Insert array data
INSERT INTO products (id, features)
VALUES (1, '[{"name": "A", "spec": {"value": 10}}]'::jsonb);

-- Filter array elements
SELECT id
FROM products
WHERE features->0->>'name' = 'A';

-- Check array length
SELECT id FROM products
WHERE features ? '0';
```

### **3. Advanced Path Queries (GIN Optimized)**
```sql
-- Full-text search in JSONB
CREATE INDEX idx_user_search ON users USING GIN (metadata jsonb_path_ops);

-- Search for users with "AI" in metadata
SELECT id
FROM users
WHERE metadata @> '{"tags": ["AI"]}'::jsonb;
```

### **4. Aggregations and JSONB**
```sql
-- Count nested objects
SELECT id, jsonb_array_length(metadata->'features') AS feature_count
FROM products;

-- Extract a set of values
SELECT array_agg(metadata->>'name') AS all_names
FROM users;
```

### **5. Geospatial Queries (GiST Index)**
```sql
-- Define GiST index
CREATE INDEX idx_product_location ON products USING GiST (location jsonb_path_ops);

-- Find products near a point (pseudo-example; actual syntax may vary)
SELECT id FROM products
WHERE location @> '{"type": "Point", "coordinates": [-73.935, 40.730]}'::jsonb;
```

---

## **Performance Trade-offs**

| **Operation**               | **Normalized Tables** | **JSONB**               | **Recommendation**                          |
|-----------------------------|-----------------------|-------------------------|--------------------------------------------|
| **CRUD on single field**    | ⚡ **Very fast**       | 🐢 Slower (serialization) | Use normalized for **frequent updates**.   |
| **Full-table scans**        | 🔍 Slow (indexless)   | ⚡ Fast (GIN/GiST)       | Use JSONB if **filtering on nested data**.  |
| **Schema changes**          | 🔧 Requires migration | ✅ No migration needed  | Use JSONB for **evolving schemas**.         |
| **Joins**                   | ⚡ Efficient           | 🚫 Inefficient          | Avoid JSONB for **join-heavy queries**.      |

**Key Rule:**
- **Normalize** for **high-frequency, single-field access**.
- **Use JSONB** for **complex, nested, or rarely updated data**.

---

## **Related Patterns**

1. **[Normalized Tables Pattern]** – For rigid, high-performance schemas.
2. **[Materialized Views Pattern]** – Cache JSONB query results for repeated access.
3. **[Full-Text Search Pattern]** – Pair with `tsvector` + GIN for text-heavy `JSONB`.
4. **[Denormalization Pattern]** – Duplicate `JSONB` data to avoid joins in read-heavy workloads.

---
**Notes:**
- For **mixed workloads**, consider **hybrid schemas** (e.g., `JSONB` for metadata + normalized tables for core data).
- Benchmark with `EXPLAIN ANALYZE` to validate index efficacy.
- PostgreSQL 12+ optimizations (e.g., `jsonb_pluralize`) further improve performance.