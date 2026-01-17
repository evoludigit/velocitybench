# **[Pattern] JSONB Index Optimization with GiST/GIN Reference Guide**

---

## **Overview**
PostgreSQL’s **JSONB** data type offers efficient storage and querying of semi-structured data, but raw JSONB tables lack performance for complex queries. This pattern optimizes JSONB queries using **GIN (Generalized Inverted Index)** and **GiST (Generalized Search Tree)** indexes, which enable fast full-text, path, and array operation lookups.

GIN indexes are ideal for **multi-column values** (e.g., arrays, JSON objects), while GiST indexes excel at **geospatial, JSON path, and full-text** operations. This guide covers when to use each index type, how to implement them, and best practices for performance.

---

## **Key Concepts**
### **1. Why Optimize JSONB Queries?**
Without indexes, PostgreSQL performs **full table scans**, slowing down queries on large JSONB datasets. Indexes allow PostgreSQL to bypass scans by navigating predefined data structures.

### **2. GIN vs. GiST for JSONB**
| **Index Type** | **Use Case**                          | **Best For**                          | **Syntax Example**                     |
|----------------|---------------------------------------|---------------------------------------|----------------------------------------|
| **GIN**        | Arrays, JSON objects, full-text       | Multi-column lookups, nested data     | `CREATE INDEX idx_json ON table_name USING gin (jsonb_column GIN);` |
| **GiST**       | Path queries, geospatial, full-text   | JSON path indexes (`@>`), `jsonb_path_ops` | `CREATE INDEX idx_json_path ON table_name USING gist (jsonb_column gist_jsonb_path_ops);` |

### **3. When to Use Each Index**
| **Scenario**                     | **Recommended Index**       | **Example Query**                          |
|----------------------------------|-----------------------------|--------------------------------------------|
| Filtering arrays                 | GIN                         | `WHERE jsonb_column @> '{"key": [1, 2]}'`   |
| JSON path queries (`->`, `@>`)   | GiST (`gist_jsonb_path_ops`)| `WHERE jsonb_column ? '$.nested.key'`      |
| Full-text search                 | GIN (with `gin_trgm_ops`)   | `WHERE jsonb_column @@ 'search term'`      |
| Geospatial lookups               | GiST (`gist_brin`)          | `WHERE jsonb_column @ "POLYGON(...)"`      |

---

## **Schema Reference**
Use the following schema as a template for JSONB tables with indexes.

| **Column**       | **Type**   | **Description**                          | **Recommended Index**          |
|------------------|------------|------------------------------------------|--------------------------------|
| `id`             | `SERIAL`   | Primary key                              | `CREATE INDEX idx_id ON table USING btree(id);` |
| `metadata`       | `JSONB`    | Semi-structured data                     | `CREATE INDEX idx_metadata ON table USING gin(metadata);` |
| `tags`           | `JSONB[]`  | Array of tags                            | `CREATE INDEX idx_tags ON table USING gin(tags);` |
| `geolocation`    | `JSONB`    | Geospatial coordinates                   | `CREATE INDEX idx_geo ON table USING gist(geolocation gist_jsonb_path_ops);` |
| `fulltext`       | `JSONB`    | Text for search                          | `CREATE INDEX idx_fulltext ON table USING gin(fulltext gin_trgm_ops);` |

---

## **Index Types in Detail**

### **1. GIN Index**
**Best for:** Arrays, JSON objects, and multi-column lookups.

#### **Syntax**
```sql
-- Basic GIN index on JSONB
CREATE INDEX idx_json_data ON table_name USING gin (jsonb_column);

-- GIN with operator class for arrays
CREATE INDEX idx_json_array ON table_name USING gin (jsonb_column gin_array_ops);

-- GIN with trigram for full-text search
CREATE INDEX idx_json_trgm ON table_name USING gin (jsonb_column gin_trgm_ops);
```

#### **Example Queries**
```sql
-- Filter JSON array
SELECT * FROM table_name
WHERE jsonb_column @> '{"key": [1, 2]}';  -- Uses GIN index on jsonb_column

-- Search nested JSON
SELECT * FROM table_name
WHERE jsonb_column ? '$.nested.key';       -- Uses GIN (or GiST with path_ops)
```

---

### **2. GiST Index**
**Best for:** JSON path queries, geospatial data, and advanced full-text operations.

#### **Syntax**
```sql
-- GiST index for JSON path operations
CREATE INDEX idx_json_path ON table_name USING gist (jsonb_column gist_jsonb_path_ops);

-- GiST for geospatial (PostGIS-style)
CREATE INDEX idx_geo ON table_name USING gist (jsonb_column gist_brin);
```

#### **Example Queries**
```sql
-- JSON path query (e.g., ? '$.nested.key')
SELECT * FROM table_name
WHERE jsonb_column ? '$.nested.key';       -- Uses GiST with path_ops

-- Geospatial query (e.g., ST_Contains)
SELECT * FROM table_name
WHERE jsonb_column @ "POLYGON((0 0, 10 0, 10 10, 0 10, 0 0))";
```

---

## **Query Examples**

### **Scenario 1: Filtering Arrays with GIN**
**Schema:**
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    metadata JSONB,
    tags JSONB[]
);
CREATE INDEX idx_products_tags ON products USING gin (tags);
```

**Query:**
```sql
-- Find products with tags "electronics" or "sale"
SELECT * FROM products
WHERE tags @> ARRAY['"electronics"', '"sale"'];
-- Uses GIN index on `tags` for fast array lookup.
```

---

### **Scenario 2: JSON Path Query with GiST**
**Schema:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    profile JSONB
);
CREATE INDEX idx_users_profile ON users USING gist (profile gist_jsonb_path_ops);
```

**Query:**
```sql
-- Find users with an active status in their profile
SELECT * FROM users
WHERE profile ? '$.status' AND profile->>'status' = 'active';
-- Uses GiST index for path operations (faster than full scan).
```

---

### **Scenario 3: Full-Text Search with Trigram**
**Schema:**
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    content JSONB
);
CREATE INDEX idx_articles_content ON articles USING gin (content gin_trgm_ops);
```

**Query:**
```sql
-- Search articles containing the word "performance"
SELECT * FROM articles
WHERE content @@ to_tsvector('english', 'performance');
-- Uses GIN with trigram for efficient full-text matching.
```

---

## **Performance Considerations**

| **Factor**               | **Recommendation**                                                                 |
|--------------------------|------------------------------------------------------------------------------------|
| **Index Size**           | GIN indexes use more disk space than B-tree; monitor with `pg_stat_user_indexes`. |
| **Query Patterns**       | Use GiST for path operations, GIN for arrays/nested data.                          |
| **Partial Indexes**      | Optimize with `WHERE` clauses to reduce index size: `CREATE INDEX ON table (jsonb_column) WHERE condition`. |
| **Avoid Over-Indexing**  | Each index adds overhead; benchmark with `EXPLAIN ANALYZE`.                        |

---

## **Related Patterns**
1. **[Partial Indexes for JSONB]** – [Link] – Optimize indexes with `WHERE` conditions.
2. **[Materialized Views for JSON Aggregations]** – [Link] – Pre-compute JSON aggregations for faster reads.
3. **[JSON Functions Optimization]** – [Link] – Use `jsonb_path_query` and `jsonb_array_elements` efficiently.
4. **[Partitioning Large JSONB Tables]** – [Link] – Split data by range or list for scalable queries.

---
## **Further Reading**
- [PostgreSQL GIN Index Documentation](https://www.postgresql.org/docs/current/indexes-types.html#IDX-IDX-GIN-INDEXES)
- [PostgreSQL GiST Index Documentation](https://www.postgresql.org/docs/current/indexes-types.html#IDX-IDX-GIST-INDEXES)
- [JSONB Path Query Guide](https://www.postgresql.org/docs/current/functions-json.html#FUNCTIONS-JSON-PATH-QUERY)

---
**Last Updated:** [Insert Date]
**Version:** 1.0