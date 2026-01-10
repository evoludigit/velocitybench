# **[Pattern] Database Indexing Strategies Reference Guide**
*Optimize query performance by selecting the right index type for your workload.*

---

## **Overview**
Indexes are crucial for reducing query latency by avoiding full table scans. A well-chosen index can transform O(n) linear scans into O(log n) logarithmic lookups. PostgreSQL provides five index types, each optimized for specific data patterns:

- **B-tree**: The default, general-purpose index for equality and range queries.
- **Hash**: Fast equality lookups but inefficient for ranges.
- **GIN**: Efficient for complex data types like full-text, JSONB, and arrays.
- **GiST**: Flexible for geometric data, full-text search, and custom data types.
- **BRIN**: Optimized for large, ordered tables with sparse data distribution.

This guide covers index types, creation syntax, use cases, and performance considerations.

---

## **Schema Reference**

| **Index Type** | **Best Use Case**                          | **Supported Operations**                     | **When to Avoid**                     | **Example Syntax**                                                                 |
|----------------|-------------------------------------------|---------------------------------------------|---------------------------------------|----------------------------------------------------------------------------------|
| **B-tree**     | Equality, range, sorting                  | `<`, `>`, `=`, `BETWEEN`, `ORDER BY`        | High-cardinality hash lookups          | `CREATE INDEX idx_name ON table (column);`                                      |
| **Hash**       | Equality-heavy workloads                   | `=` only                                    | Range queries, approximate results     | `CREATE INDEX CONCURRENTLY idx_name ON table USING HASH (column);`               |
| **GIN**        | Full-text search, JSONB arrays            | Text search, array containment               | Small or exact-match lookups          | `CREATE INDEX idx_name ON table USING GIN (column gin_trgm_ops);`                 |
| **GiST**       | Geometric data, full-text (alternative)  | Proximity, range (e.g., `&&`, `@>`)        | Simple equality queries               | `CREATE INDEX idx_name ON table USING GiST (column gist_geography_ops);`         |
| **BRIN**       | Large, ordered tables (e.g., timestamps) | Range scans                                | Small or unordered data               | `CREATE INDEX idx_name ON table USING BRIN (column) WITH BRIN_LAYOUT = linear;` |

---

## **Query Examples**

### **1. B-tree (General-Purpose Index)**
**Use Case**: Range queries and sorting.
```sql
-- Create index
CREATE INDEX idx_customer_email ON customers (email);

-- Query (uses index for equality + range)
SELECT * FROM customers
WHERE email LIKE 'a%' AND age > 30
ORDER BY last_name;
```

**Explain Analyze Output**:
```
Index Scan using idx_customer_email on customers  (cost=0.15..8.16 rows=1000 width=200)
```

---

### **2. Hash (Equality-Only Index)**
**Use Case**: High-volume `=` lookups (e.g., session IDs).
```sql
-- Create index (concurrent to avoid locks)
CREATE INDEX CONCURRENTLY idx_user_session ON users USING HASH (session_id);

-- Query (fast hash lookup)
SELECT * FROM users WHERE session_id = 'abc123';
```

**When to Avoid**:
Hash indexes fail for range queries:
```sql
-- Inefficient (full scan)
SELECT * FROM users WHERE age > 40;
```

---

### **3. GIN (Full-Text/JSONB Arrays)**
**Use Case**: Searching within arrays or full-text.
```sql
-- Create index for JSONB array
CREATE INDEX idx_posts_tags ON posts USING GIN (tags);

-- Query (uses GIN for array containment)
SELECT * FROM posts WHERE tags @> ARRAY['postgresql', 'database'];
```

**Full-Text Example**:
```sql
CREATE INDEX idx_articles_content ON articles USING GIN (content gin_trgm_ops);
SELECT * FROM articles WHERE to_tsvector('english', content) @@ to_tsquery('performance & indexing');
```

---

### **4. GiST (Geometric/Advanced Range Queries)**
**Use Case**: Spatial data (e.g., points, polygons).
```sql
-- Create index for geography type
CREATE INDEX idx_locations_geom ON locations USING GiST (location gist_geography_ops);

-- Query (uses GiST for spatial containment)
SELECT * FROM locations
WHERE location && ST_MakeEnvelope(-122.5, 37.5, -122.3, 37.7, 4326);
```

---

### **5. BRIN (Large Ordered Tables)**
**Use Case**: Time-series or ID-based columns with natural ordering.
```sql
-- Create BRIN index (adjust BRIN_BLOCKSIZE for table size)
CREATE INDEX idx_logs_timestamp ON logs USING BRIN (timestamp)
WITH (BRIN_BLOCKSIZE = 1024);

-- Query (uses BRIN for range)
SELECT * FROM logs
WHERE timestamp BETWEEN '2023-01-01' AND '2023-01-02';
```

**For Small Tables**:
BRIN may perform worse than B-tree:
```sql
-- Avoid BRIN if table < 1M rows
EXPLAIN ANALYZE SELECT * FROM small_table WHERE id = 1;
-- Output: Seq Scan (full scan)
```

---

## **Performance Considerations**

### **When to Use Which Index**
| **Query Pattern**       | **Recommended Index** | **Avoid**               |
|-------------------------|-----------------------|-------------------------|
| Equality (`=`)          | B-tree, Hash          | None                    |
| Range (`>`, `<`)        | B-tree, BRIN          | Hash                    |
| Full-text search        | GIN, GiST             | B-tree                  |
| JSONB array lookup      | GIN                   | B-tree                  |
| Geospatial queries      | GiST                  | B-tree                  |

---

### **Index Maintenance**
- **Concurrent Creation**: Use `CREATE INDEX CONCURRENTLY` to avoid locks.
  ```sql
  CREATE INDEX CONCURRENTLY idx_name ON table (column);
  ```
- **Partial Indexes**: Index only a subset of rows (e.g., active users).
  ```sql
  CREATE INDEX idx_active_users ON users (email)
  WHERE is_active = TRUE;
  ```
- **Composite Indexes**: Cover multiple columns for complex queries.
  ```sql
  CREATE INDEX idx_name_age ON customers (last_name, age);
  ```

---

### **Anti-Patterns**
1. **Over-Indexing**: Each index adds write overhead. Rule of thumb: <10% of columns.
   ```sql
   -- Avoid indexing every column
   CREATE INDEX idx_every_column ON table (col1, col2, col3, ...);
   ```
2. **Ignoring Selectivity**: Low-cardinality columns (e.g., gender) create large indexes.
   ```sql
   -- Bad: Low selectivity
   CREATE INDEX idx_gender ON users (gender);
   ```
3. **Forgetting `EXPLAIN ANALYZE`**: Always verify index usage.
   ```sql
   EXPLAIN ANALYZE SELECT * FROM table WHERE column = 'value';
   ```

---

## **Related Patterns**
1. **[Query Optimization]** – Analyze `EXPLAIN` output to diagnose bottlenecks.
2. **[Partitioning]** – Combine with indexing for large tables (e.g., partition by range + BRIN).
3. **[Materialized Views]** – Pre-compute aggregations to avoid expensive scans.
4. **[Connection Pooling]** – Reduce overhead from repeated index lookups.
5. **[Denormalization]** – Duplicate data to avoid joins (trade-off: storage vs. speed).

---

## **Further Reading**
- [PostgreSQL Indexing Handbook](https://www.postgresql.org/docs/current/indexes.html)
- [GIN vs. GiST](https://www.postgresql.org/docs/current/gin-indexes.html#GIN-VS-GIST)
- [BRIN Index Deep Dive](https://www.citusdata.com/blog/2018/12/20/brin-indexes-postgresql/)

---
**Last Updated**: [Date]
**Author**: [Your Name]
**License**: [MIT/CC-BY-SA]