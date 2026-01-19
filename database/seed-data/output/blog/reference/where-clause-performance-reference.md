---
# **[Pattern] **WHERE Clause Performance Reference Guide**

---

## **Overview**
The **WHERE Clause Performance** pattern optimizes query execution by leveraging operator choice, index usage, and logical predicate structure to minimize runtime costs. Database engines evaluate predicates in the `WHERE` clause sequentially, and certain operators or constructs (e.g., `=` vs. `BETWEEN`, `LIKE '%text'` vs. `LIKE 'text%'`) can drastically impact performance due to differences in index utilization and search cost.

This pattern guides developers in selecting high-performance operators and structuring predicates to reduce full table scans, improve index seek operations, and minimize memory/CPU overhead. Key considerations include:
- **Operator affinity** (e.g., equality vs. range scans)
- **Predicate order** (placing highly selective filters first)
- **Pattern matching** (avoiding leading wildcards)
- **Data type alignment** (explicit vs. implicit casting)

---

## **Schema Reference**
The following tables outline common operators, their performance characteristics, and optimal use cases.

### **1. Operator Performance Comparison**
| **Operator**       | **Scan Type**       | **Index Utilization** | **Best Use Case**                     | **Avoid When...**                     |
|--------------------|---------------------|-----------------------|---------------------------------------|---------------------------------------|
| `=` (equality)     | **Index Seek**      | High (B-tree, hash)   | Exact values, indexed columns          | Column is unindexed or highly selective|
| `>`, `<`, `<=`, `>=` | **Index Range Scan** | Medium (B-tree)       | Sorted ranges (e.g., dates, IDs)      | Wide ranges (e.g., `> 1990-01-01`)   |
| `BETWEEN a AND b`  | **Index Range Scan** | High (B-tree)         | Numeric/date ranges with gaps          | Many nullable/outlier values           |
| `IN (val1, val2)`  | **Index Multi-Seek** | High (B-tree)         | Small, fixed lists (<10 values)       | Large lists (use `EXISTS` or temp tables)|
| `LIKE 'prefix%'`   | **Index Prefix Scan**| Medium-High (B-tree)  | Text searches with known prefixes      | Leading wildcards (`'%suffix'` or `'%any%'`)|

### **2. Predicate Order Impact**
| **Pattern**               | **Performance Impact**                          | **Notes**                                  |
|---------------------------|------------------------------------------------|--------------------------------------------|
| **Selective filters first** | Minimizes rows early, reducing CPU/memory load. | Place `WHERE id = 123 AND status = 'A'` before broader filters. |
| **Equality before range**  | Limits range scans to a smaller dataset.      | `WHERE user_id = 100 AND created_date > '2023-01-01'` > `WHERE created_date > '2023-01-01' AND user_id = 100`. |
| **Composite indexes**     | Enables seeks on multiple columns.            | Use `WHERE (col1, col2) IN ((val1, val2), ...)` for covering indexes. |

---
## **Query Examples**

### **1. Optimized Equality Filtering**
**Goal:** Find all active users with ID `1000` efficiently.
**Optimized Query:**
```sql
SELECT * FROM users
WHERE user_id = 1000 AND is_active = TRUE;
```
**Why?**
- Both columns are indexed (assuming `(user_id, is_active)` composite index).
- Equality filters trigger **index seeks**, avoiding full table scans.

**Avoid:**
```sql
SELECT * FROM users
WHERE is_active = TRUE AND user_id = 1000;
```
(Identical performance *if* both columns are indexed, but order matters for non-indexed columns.)

---

### **2. Range Scans with Indexes**
**Goal:** Retrieve orders placed in Q3 2023 with a value > $1000.
**Optimized Query:**
```sql
SELECT * FROM orders
WHERE order_date BETWEEN '2023-07-01' AND '2023-09-30'
  AND amount > 1000;
```
**Why?**
- `BETWEEN` leverages a **range scan** on `(order_date, amount)` if indexed.
- Placing `amount > 1000` *after* narrows the range first.

**Avoid:**
```sql
SELECT * FROM orders
WHERE amount > 1000 AND order_date BETWEEN '2023-07-01' AND '2023-09-30';
```
(Slower if `amount` lacks an index—range scans on non-indexed columns force full table reads.)

---

### **3. Pattern Matching (LIKE)**
**Goal:** Search for names starting with "Jo".
**Optimized Query:**
```sql
SELECT * FROM employees
WHERE name LIKE 'Jo%';
```
**Why?**
- **Prefix matching** (`LIKE 'prefix%'`) uses index scans (B-tree traversal).
- Wildcards at the **end** (`'%suffix'`) require full table scans.

**Avoid:**
```sql
SELECT * FROM employees
WHERE name LIKE '%Jo%'; -- Full scan
```
**Alternative for ambiguous searches:**
```sql
SELECT * FROM employees
WHERE name >= 'Jo' AND name < 'Jo\0'; -- Simulates LIKE 'Jo%'
```

---

### **4. IN vs. EXISTS (Large Lists)**
**Goal:** Find users with IDs in a large list (1000+ values).
**Optimized Query:**
```sql
-- Option 1: EXISTS (avoids temporary table overhead)
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM user_ids_temp WHERE user_ids_temp.id = u.user_id
);

-- Option 2: Temp table (for very large datasets)
CREATE TEMP TABLE temp_ids (id INT);
INSERT INTO temp_ids VALUES (100, 200, ...);
SELECT * FROM users u WHERE u.user_id IN (SELECT id FROM temp_ids);
```
**Why?**
- `IN` with large lists may create a temporary table (slow).
- `EXISTS` stops at the first match, reducing I/O.

---

### **5. Avoiding Function Calls on Columns**
**Goal:** Filter users where `year(created_at) = 2023`.
**Bad Query (index unusable):**
```sql
SELECT * FROM users
WHERE YEAR(created_at) = 2023; -- Forces full scan
```
**Optimized Query (uses index):**
```sql
SELECT * FROM users
WHERE created_at >= '2023-01-01' AND created_at < '2024-01-01';
```
**Why?**
- Database cannot use an index on `created_at` if it calls `YEAR()`.
- Range comparisons preserve index usage.

---

## **Implementation Details**
### **Key Concepts**
1. **Index Seek vs. Scan:**
   - **Seek:** Directly accesses rows via index (e.g., `=` or range on indexed columns).
   - **Scan:** Sequentially reads table data (e.g., `LIKE '%text%'` or non-indexed filters).

2. **Cost of Predicate Evaluation:**
   - Databases estimate row counts early. Place **high-selectivity filters first** to reduce work:
     ```sql
     WHERE status = 'active' AND created_at > '2023-01-01'  -- Good
     WHERE created_at > '2023-01-01' AND status = 'active' -- Slower
     ```

3. **Data Type Alignment:**
   - Ensure predicate types match column types (e.g., avoid `WHERE date_column = '2023-01-01'`; use `WHERE date_column = '2023-01-01'` with proper casting).

4. **Covering Indexes:**
   - Optimize for queries that retrieve only indexed columns:
     ```sql
     CREATE INDEX idx_user_active ON users(user_id, is_active);
     -- Query uses the index entirely (no table lookup):
     SELECT user_id, is_active FROM users WHERE user_id = 1000;
     ```

---

### **Anti-Patterns to Avoid**
| **Anti-Pattern**               | **Impact**                                  | **Fix**                                      |
|---------------------------------|--------------------------------------------|---------------------------------------------|
| Leading wildcards (`LIKE '%x%'`)| Full table scan.                           | Use `LIKE 'x%'` or full-text search.         |
| Function calls on columns       | Index unusable.                            | Rewrite as range comparisons.               |
| OR without parentheses          | Ambiguous evaluation order.                | Enclose predicates: `WHERE (a = 1 OR b = 2)`.|
| Large `IN` lists (>10 values)   | Temporary table overhead.                  | Use `EXISTS` or pagination.                 |
| Unnecessary column projections  | Increases I/O.                             | Select only required columns.                |

---

## **Related Patterns**
1. **[Index Selection Strategies](link)**
   - Guide for choosing between B-trees, hash indexes, or full-text indexes.
2. **[Query Plan Analysis](link)**
   - Tools (e.g., `EXPLAIN ANALYZE`) to diagnose WHERE clause bottlenecks.
3. **[Partitioned Tables](link)**
   - Optimizing range filters on partitioned data (e.g., `PARTITION BY RANGE`).
4. **[Materialized Views](link)**
   - Pre-computing aggregates to avoid expensive WHERE clause computations.
5. **[Batch Processing](link)**
   - Using `UPDATE`/`DELETE` with correlated subqueries for bulk operations.

---
**Note:** Performance varies by database (PostgreSQL, MySQL, SQL Server, etc.). Always test with `EXPLAIN` or equivalents. For distributed systems, consider **partition pruning** and **sharding** impacts.