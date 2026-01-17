# **[Pattern] PostgreSQL Capabilities Reference Guide**

## **Overview**
PostgreSQL is a powerful, open-source relational database management system (RDBMS) that extends standard SQL capabilities with advanced features, including **JSON/JSONB support**, **full-text search**, **window functions**, **partitioning**, **row-level security (RLS)**, **stored procedures**, and more. This reference guide outlines PostgreSQL-specific patterns, focusing on key concepts, schema design, query syntax, and best practices.

---

## **1. Key PostgreSQL Features & Capabilities**
PostgreSQL supports the following distinct capabilities beyond ANSI SQL:

| **Category**          | **Feature**                     | **Description**                                                                 |
|-----------------------|---------------------------------|---------------------------------------------------------------------------------|
| **Data Types**        | JSON/JSONB                     | Native support for nested JSON structures, with JSONB being binary-optimized.   |
|                       | Arrays                         | Multi-dimensional arrays for flexible schema design.                           |
|                       | hstore                         | Key-value store for semi-structured data.                                     |
| **Query Language**    | Common Table Expressions (CTEs)| `WITH` clauses for complex recursive and iterative queries.                     |
|                       | Window Functions (`OVER()`)     | Non-aggregating calculations across partitioned result sets (e.g., `RANK()`, `LEAD()`). |
|                       | Lateral Joins (`FROM LATERAL`) | Correlated subqueries for dynamic result sets.                                 |
| **Indexing**          | GiST, GIN, BRIN, Hash Indexes   | Specialized indexing for JSON, full-text, and time-series data.                 |
|                       | Partial Indexes                | Indexes on subsets of rows (e.g., `WHERE status = 'active'`).                   |
| **Data Integrity**    | Foreign Data Wrappers (FDW)    | Connect to external data sources (e.g., MySQL, Oracle) via SQL.               |
|                       | Row-Level Security (RLS)        | Fine-grained access control at the row level.                                   |
| **Partitioning**      | Table Partitioning             | Split large tables by range, list, or hash.                                    |
| **Text Search**       | Full-Text Search (`tsvector`, `tsquery`) | Advanced text indexing and querying with `pg_trgm` for fuzzy matching.   |
| **Concurrency**       | MVCC (Multi-Version Concurrency Control) | Isolated transactions without locks via snapshot isolation.              |
| **Extensions**        | `uuid-ossp`, `postgis`, `plpgsql` | Custom functions, custom types, and spatial data support.                     |

---

## **2. Schema Reference**

### **Tables Supporting PostgreSQL-Specific Features**
| **Table**          | **Description**                                                                 | **Key Constraints/Features**                          |
|--------------------|---------------------------------------------------------------------------------|------------------------------------------------------|
| `products`         | Stores product data with JSON attributes.                                      | Uses `JSONB` column for flexible schema evolution.   |
| `user_activities`  | Logs user actions with timestamp partitioning.                                   | Partitioned by date range (`PARTITION BY RANGE`).    |
| `documents`        | Stores semi-structured documents (e.g., unstructured text).                     | Uses `hstore` or `JSONB` for dynamic fields.         |
| `user_preferences` | Key-value preferences for users.                                                | Uses `hstore` or `JSONB` for flexible key-value storage. |

#### **Example Table Definition**
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    attributes JSONB,          -- Flexible schema
    price DECIMAL(10, 2),
    tags TEXT[],               -- Array type
    variants JSONB[]           -- Array of JSON objects
);

-- Partial index for active products
CREATE INDEX idx_products_active ON products (name) WHERE status = 'active';

-- GiST index for JSON path queries
CREATE INDEX idx_products_attributes_gist ON products USING GIST (attributes jsonb_path_ops);

-- Partitioned table for user activities
CREATE TABLE user_activities (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action TEXT NOT NULL,
    metadata JSONB,
    timestamp TIMESTAMP
) PARTITION BY RANGE (timestamp);
```

---

## **3. Query Examples**

### **3.1 JSON/JSONB Queries**
#### **Query 1: Filter and Extract JSON Data**
```sql
-- Find products with "color" = "red" in their attributes
SELECT id, name, attributes->>'color'
FROM products
WHERE attributes->>'color' = 'red';

-- Update JSON field incrementally
UPDATE products
SET attributes = jsonb_set(attributes, '{price}', to_jsonb(19.99))
WHERE id = 1;
```

#### **Query 2: JSON Operators**
```sql
-- Check if JSON contains a key
SELECT id FROM products
WHERE attributes ? 'size';

-- Array operations
SELECT id, tags
FROM products
WHERE 'large' = ANY(tags);
```

---

### **3.2 Window Functions**
#### **Query 3: Rank Products by Sales**
```sql
WITH ranked_products AS (
    SELECT
        id,
        name,
        sales_amount,
        RANK() OVER (ORDER BY sales_amount DESC) AS sales_rank
    FROM products
    WHERE sales_amount > 0
)
SELECT * FROM ranked_products;
```

#### **Query 4: Compare with Previous Sale**
```sql
SELECT
    id,
    name,
    sales_amount,
    LAG(sales_amount) OVER (PARTITION BY category ORDER BY sales_amount DESC) AS prev_sale
FROM products;
```

---

### **3.3 Full-Text Search**
#### **Query 5: Search for "best deals" in Product Descriptions**
```sql
-- Create a full-text search index (if not exists)
CREATE INDEX idx_products_desc_gin ON products USING GIN (to_tsvector('english', description));

-- Query using tsvector and tsquery
SELECT id, name, description
FROM products, to_tsvector('english', description) AS search_vec
WHERE search_vec @@ to_tsquery('best deals');
```

#### **Query 6: Fuzzy Matching with `pg_trgm`**
```sql
-- Enable trgm extension (if not active)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Find products with names similar to "laptop"
SELECT id, name
FROM products
WHERE name % 'laptop';
```

---

### **3.4 Partitioning**
#### **Query 7: Query Partitioned `user_activities`**
```sql
-- Create monthly partitions
CREATE TABLE user_activities_2023_01 PARTITION OF user_activities
    FOR VALUES FROM ('2023-01-01') TO ('2023-02-01');

-- Query all actions for a user in a specific month
SELECT * FROM user_activities
WHERE user_id = 1 AND timestamp BETWEEN '2023-01-01' AND '2023-01-31';
```

---

### **3.5 Row-Level Security (RLS)**
#### **Query 8: Enable RLS on a Table**
```sql
-- Enable RLS and define a policy
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY product_view_policy ON products
    USING (user_id = current_setting('app.user_id')::INT);
```

---

### **3.6 Lateral Joins**
#### **Query 9: Correlated Subquery with Lateral**
```sql
-- Find products with their top 3 customer tags
SELECT
    p.id,
    p.name,
    tag
FROM products p,
LATERAL (
    SELECT tag
    FROM product_tags pt
    WHERE pt.product_id = p.id
    ORDER BY count(*) DESC
    LIMIT 3
) AS top_tags;
```

---

## **4. Best Practices**

1. **Use `JSONB` for Structured Data**
   - Prefer `JSONB` over `JSON` for faster queries and indexing.
   - Example: Store product variants in `JSONB[]` for flexible schema.

2. **Leverage Partitioning for Large Tables**
   - Partition `user_activities`, `logs`, or `sensor_data` by time ranges for performance.

3. **Optimize with Specialized Indexes**
   - Use **GIN** for `JSONB`/`JSON` operations.
   - Use **GiST** for full-text search or geospatial data.

4. **Enable RLS for Security**
   - Apply row-level security to sensitive tables (e.g., `users`, `payments`).

5. **Use `WITH` CTEs for Readability**
   - Break complex queries into named subqueries for clarity.

6. **Avoid `SELECT *`**
   - Explicitly list columns in queries to reduce network overhead.

7. **Batch JSON Updates**
   - Use `jsonb_set()` or `jsonb_insert()` for incremental JSON updates.

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|
| **[Data Partitioning][1]** | Techniques for splitting large tables for performance and maintainability.    |
| **[JSON Schema Evolution][2]** | How to handle schema changes in JSON/JSONB columns without downtime.           |
| **[Full-Text Search Optimization][3]** | Best practices for indexing and querying text data efficiently.               |
| **[Row-Level Security (RLS)][4]** | Implementing fine-grained access control in PostgreSQL.                        |
| **[PostgreSQL Extensions][5]** | Leveraging extensions like `postgis`, `plpgsql`, or `uuid-ossp` for specialized needs. |

---
**[1]: Data Partitioning**
**[2]: JSON Schema Evolution**
**[3]: Full-Text Search Optimization**
**[4]: Row-Level Security (RLS)**
**[5]: PostgreSQL Extensions**