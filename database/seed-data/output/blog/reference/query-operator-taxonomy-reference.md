# **[Pattern] Query Operator Taxonomy Reference Guide**
*Version: 1.0*

---

## **Overview**
FraiseQL’s **Query Operator Taxonomy** organizes **150+ WHERE clause operators** into **14 semantic categories**, ensuring consistency, discoverability, and cross-database compatibility. This pattern standardizes operator behavior across relational databases (PostgreSQL, MySQL, SQLite, etc.) while accounting for database-specific extensions.

Key benefits:
- **Intuitive navigation**: Operators are grouped by use case (e.g., `date_time` for temporal logic).
- **Performance awareness**: Includes operators like `<<<` (trigram match) for specialized indexing.
- **Database-agnostic**: Flags availability per DB (e.g., `~` for full-text search is **PostgreSQL-only**).
- **Edge cases covered**: Supports niche operators like `OPERATOR_UUID()` for UUID manipulation.

---

## **Schema Reference**
Below is a **scannable table** of operator categories, core operators, syntax, and database support. *(Full reference: [FraiseQL Doc → Query Operators](insert-link))*

| **Category**          | **Operator**       | **Syntax**               | **Description**                                                                 | **Databases**                     |
|-----------------------|--------------------|--------------------------|---------------------------------------------------------------------------------|-----------------------------------|
| **Basic Comparisons** | `=`, `!=`, `<>`, `>`, `<`, `>=` | `col = value`            | Standard equality/comparison.                                                | All                                |
|                       | `IS NULL`, `IS NOT NULL` | `col IS NULL`          | Null handling.                                                                   | All                                |
|                       | `IN`, `NOT IN`     | `col IN (val1, val2)`    | Membership tests.                                                               | All                                |
|                       | `ANY`, `SOME`, `ALL`| `EXPR OP (subquery)`     | Correlated subquery comparisons.                                                 | PostgreSQL, MySQL                  |
| **String/Text**       | `=~`, `!~`         | `col =~ 'pattern'`       | Regex matching (PostgreSQL).                                                   | PostgreSQL                         |
|                       | `LIKE`, `NOT LIKE` | `col LIKE '%text%'`      | Wildcard pattern matching.                                                     | All                                |
|                       | `ILIKE`            | `col ILIKE '%text%'`     | Case-insensitive `LIKE`.                                                        | PostgreSQL                         |
|                       | `<<`, `>>`         | `col << 'substring'`     | Trigram search (PostgreSQL).                                                    | PostgreSQL                         |
|                       | `~*`               | `col ~* 'phrase'`        | Full-text search (PostgreSQL).                                                  | PostgreSQL                         |
| **Arrays**            | `@>`, `<@`         | `col @> ARRAY[val1, val2]`| Array containment.                                                             | PostgreSQL                         |
|                       | `#>>`, `#<<`       | `col #>> '{2}'`          | Array element extraction.                                                       | PostgreSQL                         |
|                       | `&&`               | `col && ARRAY[val1]`     | Array overlap.                                                                   | PostgreSQL                         |
| **JSONB**             | `->`, `->>`        | `col->'key'`             | JSONB key/path access.                                                          | PostgreSQL                         |
|                       | `@>`               | `col @> '{"key": "val"}'`| JSONB containment.                                                               | PostgreSQL                         |
| **Date/Time**         | `BETWEEN`          | `col BETWEEN '2023-01-01' AND '2023-12-31'` | Range checks.                     | All                                |
|                       | `~`                | `col ~ '2023-01-01'`     | Date parsing (PostgreSQL).                                                      | PostgreSQL                         |
|                       | `EXTRACT`          | `EXTRACT(YEAR FROM col)` | Date field extraction.                                                          | PostgreSQL, MySQL                  |
| **Network**           | `CIDR`             | `col >< '192.168.1.0/24'`| IP subnet matching.                                                              | PostgreSQL                         |
|                       | `INET`, `CIDR`     | `col ~ '192.168.*'`      | IP pattern matching.                                                           | PostgreSQL                         |
| **Geographic**        | `<>`               | `ST_DWithin(col, pt)`    | Spatial distance (PostGIS).                                                     | PostgreSQL (PostGIS)               |
|                       | `&&`               | `col && ST_MakePoint(0,0)`| Spatial containment.                                                           | PostgreSQL (PostGIS)               |
| **Vector**            | `<->`              | `v1 <-> v2`              | Vector cosine similarity.                                                       | PostgreSQL (pgvector)              |
|                       | `<<<`              | `v1 <<< v2`              | Vector approximate search.                                                     | PostgreSQL (pgvector)              |
| **LTree**             | `@>`               | `col @> 'geography/usa/north-carolina'` | Hierarchical matching. | PostgreSQL (ltree) |
| **Full-Text**         | `~`                | `col ~ 'query'`          | Full-text search (PostgreSQL).                                                  | PostgreSQL                         |
|                       | `TO_TSQUERY`       | `TO_TSQUERY(col)`        | Full-text query parsing.                                                        | PostgreSQL                         |
| **Numeric**           | `MOD`              | `MOD(col, 3)`            | Modulo operation.                                                               | All                                |
|                       | `GREATEST`, `LEAST`| `GREATEST(col1, col2)`   | Aggregation functions.                                                         | All                                |
| **UUID**              | `OPERATOR_UUID()`  | `OPERATOR_UUID(col)`     | UUID-specific functions (e.g., version checks).                                 | PostgreSQL                         |
| **Enum**              | `= ANY`            | `col = ANY(ARRAY['val1', 'val2'])` | Enum membership.               | All (via type casting)             |
| **Boolean**           | `AND`, `OR`, `NOT` | `col1 AND col2`          | Logical operators.                                                             | All                                |

---
**Notes**:
- **PostgreSQL-specific**: `=~`, `<<`, `>>`, `~*`, `OPERATOR_UUID()`, `ltree`, `pgvector`.
- **MySQL/SQLite**: Limited to `BETWEEN`, `LIKE`, basic comparisons.
- **Full list**: [FraiseQL Query Operators](insert-link).

---

## **Query Examples**
### **1. Basic Comparisons**
```sql
-- Check for NULL
SELECT * FROM users WHERE email IS NULL;

-- Membership test
SELECT * FROM products WHERE category_id IN (1, 2, 3);
```

### **2. String/Text**
```sql
-- Regex match (PostgreSQL)
SELECT * FROM posts WHERE title =~ '^[A-Z].+';

-- Trigram search (PostgreSQL)
SELECT * FROM articles WHERE to_tsvector('english', content) <<< to_tsvector('english', 'query');
```

### **3. Arrays**
```sql
-- Array containment
SELECT * FROM tags WHERE tags @> ARRAY['database', 'sql'];

-- Array overlap
SELECT * FROM users WHERE roles && ARRAY['admin'];
```

### **4. JSONB**
```sql
-- JSONB key access
SELECT * FROM orders WHERE json_data->'status' = 'completed';

-- JSONB path operator
SELECT * FROM products WHERE json_data->>'price_range' > 100;
```

### **5. Date/Time**
```sql
-- Date range (all DBs)
SELECT * FROM events WHERE start_date BETWEEN '2023-01-01' AND '2023-12-31';

-- Date parsing (PostgreSQL)
SELECT * FROM logs WHERE log_time ~ '2023-01-01';
```

### **6. Geographic (PostGIS)**
```sql
-- Spatial distance (PostgreSQL)
SELECT * FROM locations
WHERE ST_DWithin(location, ST_SetSRID(ST_Point(-74.0060, 40.7128), 4326), 1000);
```

### **7. Vector Search (pgvector)**
```sql
-- Exact vector search
SELECT * FROM embeddings
WHERE embedding <-> '[0.1, 0.2, 0.3]' < 0.5;

-- Approximate search
SELECT * FROM embeddings
WHERE embedding <<< '[0.1, 0.2, 0.3]' < 5;
```

### **8. LTree Hierarchy**
```sql
-- Check parent-child relationship
SELECT * FROM directories
WHERE path @> '/usa/california/san_francisco';
```

### **9. UUID**
```sql
-- UUID version check (PostgreSQL)
SELECT * FROM users
WHERE OPERATOR_UUID(uuid) = 4; -- Version 4 (random)
```

### **10. Boolean Logic**
```sql
-- Combined conditions
SELECT * FROM orders
WHERE (status = 'completed' AND amount > 100)
   OR (status = 'pending' AND created_at > '2023-01-01');
```

---

## **Related Patterns**
1. **[Filter Expression Optimization]**
   - Complements this pattern by recommending operator choices for query performance (e.g., avoid `LIKE '%text%'`; use `LIKE 'text%'` instead).

2. **[Parameterized Queries]**
   - Ensures safe usage of operators with dynamic values (prevents SQL injection).

3. **[Indexing Strategies]**
   - Operators like `<<`, `>>`, and `GIN` indexes for `JSONB`/`array` columns improve performance.

4. **[Aggregate Operators]**
   - Extends filtering with `GROUP BY` + `HAVING` (e.g., `HAVING COUNT(*) > 5`).

5. **[Window Functions]**
   - Combines with `PARTITION BY` + `ORDER BY` for ranked filtering (e.g., `RANK() OVER (PARTITION BY category ORDER BY sales DESC)`).

---
## **Best Practices**
- **Prefer indexed operators**: `=`, `>`, `<`, `BETWEEN`, `IN` (use `EXPLAIN ANALYZE` to verify).
- **Avoid unbounded wildcards**: `LIKE '%text%'` cannot use indexes; rewrite as `LIKE 'text%'` if possible.
- **Leverage database extensions**: Use `PostGIS` for geometry or `pgvector` for embeddings.
- **Document operator availability**: Note database-specific operators in comments (e.g., `/* PostgreSQL-only */`).