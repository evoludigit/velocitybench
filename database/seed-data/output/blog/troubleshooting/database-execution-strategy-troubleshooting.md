# **Debugging Database Execution Strategy: A Troubleshooting Guide**

---

## **1. Introduction**
The **Database Execution Strategy** pattern ensures your application generates query plans that work across different database dialects (PostgreSQL, MySQL, SQLite, etc.). When queries behave differently or fail across databases, it often indicates a mismatch between execution strategies, SQL syntax, or underlying query structures.

This guide helps diagnose and resolve issues where queries work in one database (e.g., PostgreSQL) but fail in another (e.g., SQLite) or produce inconsistent results.

---

## **2. Symptom Checklist**
Before debugging, confirm if your issue matches any of these symptoms:

✅ **"Works on PostgreSQL but fails on SQLite"** (e.g., `LIMIT`/`OFFSET` behavior, function support)
✅ **"Different results across databases"** (e.g., `JOIN` ordering, `NULL` handling)
✅ **"Database-specific features not supported"** (e.g., `WITH` clause in SQLite < 3.25)
✅ **Slow performance in one DB but fast in another** (e.g., missing indexes, query plan differences)
✅ **Type mismatches** (e.g., `UUID` handling, `TIMESTAMP` precision)
✅ **Aggregation/GROUP BY inconsistencies** (e.g., `HAVING` vs. `WHERE` optimizations)

---

## **3. Common Issues & Fixes**

### **3.1. Query Syntax Mismatches**
**Symptom:**
A query works in PostgreSQL but fails in SQLite due to unsupported syntax.

**Example:**
```sql
-- PostgreSQL: Works
SELECT * FROM users WHERE id IN (SELECT post_id FROM posts WHERE category = 'coding');

-- SQLite: Fails (IN clause with subquery not supported in older versions)
```

**Fix:**
- Rewrite to use `EXISTS` (more portable):
  ```sql
  SELECT * FROM users WHERE EXISTS (
      SELECT 1 FROM posts WHERE post_id = users.id AND category = 'coding'
  );
  ```
- Use `JOIN` instead of `IN` for complex subqueries:
  ```sql
  SELECT users.* FROM users JOIN posts ON users.id = posts.post_id
  WHERE posts.category = 'coding';
  ```

---

### **3.2. LIMIT/OFFSET Behavior Differences**
**Symptom:**
Pagination works in PostgreSQL but returns incorrect results in SQLite.

**Example:**
```sql
-- PostgreSQL: Returns rows 101-200
-- SQLite: May return fewer rows due to different OFFSET handling
SELECT * FROM products LIMIT 100 OFFSET 100;
```

**Fix (PostgreSQL-compatible pagination):**
```sql
-- Use keyset pagination (better for large datasets)
SELECT * FROM products
WHERE id > last_seen_id LIMIT 100;

-- Or, for SQLite-compatibility:
SELECT * FROM (
    SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS row_num
    FROM products
) ranked WHERE row_num BETWEEN 101 AND 200;
```

---

### **3.3. Function & Operator Differences**
**Symptom:**
A query fails because a function operates differently across databases.

**Example:**
```sql
-- PostgreSQL: NULLIF(a, b) works
SELECT NULLIF(column_a, 'default') FROM table;

-- SQLite: NULLIF may not be available
```

**Fix:**
- Use database-agnostic expressions (e.g., CASE):
  ```sql
  SELECT CASE WHEN column_a = 'default' THEN NULL ELSE column_a END FROM table;
  ```
- Replace PostgreSQL-specific functions:
  | PostgreSQL | MySQL/SQLite Equivalent |
  |------------|--------------------------|
  | `ARRAY_AGG` | `GROUP_CONCAT` (MySQL) / `GROUP BY` + string join |
  | `DATE_TRUNC` | `DATE_FORMAT` (MySQL) / `CAST(date AS string)` (SQLite) |
  | `JSONB` | `JSON` (MySQL) / `TEXT` (SQLite with manual parsing) |

---

### **3.4. NULL Handling in JOINs**
**Symptom:**
Joins return inconsistent results due to `LEFT JOIN` handling.

**Example:**
```sql
-- PostgreSQL: Returns NULL if no match
SELECT * FROM customers LEFT JOIN orders ON customers.id = orders.customer_id;

-- SQLite/MySQL: May behave differently with NULLs in JOIN conditions
```

**Fix:**
- Explicitly handle `NULL` cases:
  ```sql
  SELECT
      c.*,
      COALESCE(o.order_id, 'no_orders') AS order_id
  FROM customers c
  LEFT JOIN orders o ON c.id = o.customer_id;
  ```
- Use `LEFT JOIN ... ON ... IS NOT NULL` for stricter filtering.

---

### **3.5. Data Type Mismatches**
**Symptom:**
A query fails due to unsupported data types (e.g., UUID, JSON).

**Example:**
```sql
-- PostgreSQL: UUID works
INSERT INTO users (id) VALUES (gen_random_uuid());

-- SQLite/MySQL: No native UUID support
```

**Fix:**
- Store UUIDs as text:
  ```sql
  -- PostgreSQL
  CREATE TABLE users (id UUID PRIMARY KEY);

  -- SQLite/MySQL
  CREATE TABLE users (id TEXT PRIMARY KEY);
  ```
- Use database-agnostic UUID generation:
  ```sql
  -- Generate UUID in application code before insertion
  INSERT INTO users (id) VALUES (uuid_v4());
  ```

---

### **3.6. Aggregation & GROUP BY Inconsistencies**
**Symptom:**
`HAVING` or `GROUP BY` behaves differently across databases.

**Example:**
```sql
-- PostgreSQL: Works as expected
SELECT department, COUNT(*)
FROM employees
GROUP BY department
HAVING COUNT(*) > 5;

-- SQLite: May not support non-aggregated columns in HAVING (pre-3.35)
```

**Fix:**
- Move filters to `WHERE` where possible:
  ```sql
  SELECT department
  FROM employees
  WHERE department IN ('IT', 'HR')
  GROUP BY department
  HAVING COUNT(*) > 5;
  ```
- Use `GROUP BY` with all non-aggregated columns (SQLite requirement).

---

## **4. Debugging Tools & Techniques**

### **4.1. Query Plan Analysis**
**Tool:** `EXPLAIN` (PostgreSQL), `EXPLAIN ANALYZE` (MySQL), or SQLite’s `EXPLAIN QUERY PLAN`
**Steps:**
1. Run `EXPLAIN` on the problematic query to compare execution plans.
2. Look for differences in:
   - Join strategies (`Nested Loop` vs. `Hash Join`)
   - Sorting operations (`Sort` vs. `Index Scan`)
   - Filter efficiency (`Seq Scan` vs. `Index Scan`)

**Example:**
```sql
-- PostgreSQL
EXPLAIN ANALYZE SELECT * FROM users WHERE email LIKE '%@example.com%';

-- SQLite
EXPLAIN QUERY PLAN SELECT * FROM users WHERE email LIKE '%@example.com%';
```

---

### **4.2. Database-Specific Logs**
**Symptom:** Query fails silently; logs show the issue.
**Steps:**
- Enable SQL logging in your database config:
  - **PostgreSQL:** `log_statement = 'all'`
  - **MySQL:** `general_log = 1`
  - **SQLite:** Use `PRAGMA logging = on;` (temporary)
- Check for errors like:
  - `UNKNOWN FUNCTION: jsonb_agg`
  - `OUT OF MEMORY` (due to inefficient joins)

---

### **4.3. Dynamic SQL Generation**
**Tool:** Use a templating engine (e.g., SQLFormats, SQLX, or raw string interpolation).
**Steps:**
1. Identify database-specific dialect.
2. Generate SQL dynamically based on the dialect.

**Example (TypeScript):**
```ts
const generateQuery = (db: 'postgres' | 'sqlite') => {
  if (db === 'postgres') {
    return `SELECT * FROM users WHERE id = $1`;
  } else {
    return `SELECT * FROM users WHERE id = ?`;
  }
};

// Usage
console.log(generateQuery('postgres')); // "SELECT * FROM users WHERE id = $1"
```

---

### **4.4. Unit Testing with Database Mocks**
**Tool:** Testcontainers, SQLite In-Memory DB, or mocking libraries.
**Steps:**
1. Write tests to verify queries across dialects.
2. Use a test database that matches the target dialect.

**Example (Python with `pytest`):**
```python
def test_query_across_databases():
    # Test in PostgreSQL
    assert postgres_query("SELECT 1 + 1") == 2

    # Test in SQLite
    assert sqlite_query("SELECT 1 + 1") == 2
```

---

## **5. Prevention Strategies**

### **5.1. Use a Query Builder**
**Tools:** SQLAlchemy, TypeORM, Prisma, or raw libraries like `pg` (PostgreSQL) + `sqlite3` (SQLite).
**Benefits:**
- Abstracts dialect differences.
- Provides type safety.
- Supports parameterized queries (prevents SQL injection).

**Example (SQLAlchemy):**
```python
from sqlalchemy import text

# Works across PostgreSQL/SQLite
query = text("SELECT * FROM users WHERE id = :id")
result = db.execute(query, {"id": 1})
```

---

### **5.2. Feature Detection**
**Steps:**
1. Detect the database at runtime.
2. Apply dialect-specific optimizations.

**Example (JavaScript):**
```javascript
function getUpsertQuery(db) {
  if (db === 'postgres') {
    return `INSERT INTO table (id, name) VALUES ($1, $2) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name`;
  } else {
    return `INSERT INTO table (id, name) VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET name = EXCLUDED.name`;
  }
}
```

---

### **5.3. Standardize on a Common Subset**
**Strategy:** Use only SQL-92 features (e.g., no window functions, minimal `GROUP BY`).
**Example:**
- Replace `DISTINCT ON` (PostgreSQL) with `ROW_NUMBER() OVER (PARTITION BY ...)` (SQLite-compatible).
- Use `COALESCE` instead of PostgreSQL’s `COALESCE` with expression lists.

---

### **5.4. CI/CD Checks**
**Steps:**
1. Run integration tests on all target databases (PostgreSQL, MySQL, SQLite).
2. Fail the build if queries behave inconsistently.

**Example (GitHub Actions):**
```yaml
jobs:
  test:
    runs-on: ubuntu
    services:
      postgres:
        image: postgres:13
      mysql:
        image: mysql:8.0
    steps:
      - run: npm run test:postgres
      - run: npm run test:mysql
```

---

## **6. Summary of Key Fixes**
| **Issue**               | **PostgreSQL Fix**               | **SQLite/MySQL Fix**               |
|--------------------------|----------------------------------|------------------------------------|
| `IN` with subqueries     | Supported                        | Use `EXISTS` or `JOIN`            |
| `NULLIF` function        | Works                            | Replace with `CASE WHEN`           |
| Pagination (`LIMIT/OFFSET`) | Works                          | Use keyset pagination              |
| `UUID` storage           | Native `UUID` type               | Store as `TEXT`                    |
| `JSON` functions         | `jsonb_agg`, `jsonb_set`         | Use `group_concat` or manual parsing |

---

## **7. Final Checklist for Resolving Issues**
1. **Isolate the query:** Test it directly in the problematic database.
2. **Compare `EXPLAIN` plans:** Check for performance bottlenecks.
3. **Review dialect differences:** Use a reference table (e.g., [SQLite vs. PostgreSQL](https://www.sqlite.org/lang_keywords.html)).
4. **Refactor to be database-agnostic:** Use `CASE`, `JOIN`, and common subsets.
5. **Test in CI:** Ensure consistency across all target databases.

---
By following this guide, you should be able to quickly diagnose and resolve **Database Execution Strategy** issues, ensuring your queries work consistently across all supported databases.