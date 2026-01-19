# **Debugging Window Functions in FraiseQL (Phase 5): A Troubleshooting Guide**
*For ranking, LAG/LEAD, cumulative sums, and other window function issues in FraiseQL*

---

## **1. Introduction**
FraiseQL’s **Window Functions** (Phase 5) allow powerful analytics like **ranking, running totals, and offset lookups** without collapsing rows. This guide helps debug common issues when migrating from self-joins, subqueries, or application-side calculations.

---

## **2. Symptom Checklist**
Before diving into fixes, check if your issue matches these symptoms:

| **Symptom**                          | **Likely Cause**                          | **Quick Test** |
|--------------------------------------|------------------------------------------|----------------|
| Query slows dramatically with window functions | Inefficient window partition key or large dataset | `EXPLAIN ANALYZE` the query |
| Incorrect cumulative sums (`SUM() OVER (ORDER BY ...)`) | Missing `PARTITION BY` or wrong ordering | Verify `ORDER BY` and `PARTITION BY` logic |
| `LAG()`/`LEAD()` returns `NULL` where expected | Missing `IGNORE NULLS` or incorrect offsets | Check offset values and data |
| Rows missing from expected results | Filtering after window function breaks partitioning | Move `WHERE` before window operations |
| Memory errors with big datasets | Too many rows in a partition | Use `LIMIT` for testing, optimize partitioning |

---

## **3. Common Issues and Fixes**

### **Issue 1: Incorrect Cumulative Sums**
**Symptoms:**
- Sums don’t match expected totals.
- Values jump unexpectedly.

**Root Cause:**
- Missing `PARTITION BY` (treats all rows as one partition).
- Incorrect `ORDER BY` (wrong sequence).

**Fix:**
```sql
-- Wrong: Sums all rows (no partition)
SELECT id, value, SUM(value) OVER (ORDER BY id) AS running_total
FROM sales
WHERE date > '2024-01-01';

-- Right: Partition by date to group by day
SELECT id, date, value, SUM(value) OVER (PARTITION BY date ORDER BY id) AS daily_total
FROM sales
WHERE date > '2024-01-01';
```

**Debugging Tip:**
Add a small `LIMIT` to test partitions:
```sql
SELECT id, date, value, SUM(value) OVER (PARTITION BY date ORDER BY id) AS daily_total
FROM sales
WHERE date = '2024-01-01'
LIMIT 10;
```

---

### **Issue 2: `LAG()`/`LEAD()` Returns NULL Where Expected**
**Symptoms:**
- Expected previous/next row values are `NULL`.
- Data isn’t ordered correctly.

**Root Cause:**
- Missing `IGNORE NULLS` (or `DEFAULT` value not set).
- Ordering doesn’t match data sequence.

**Fix:**
```sql
-- Wrong: NULL on first row (no default)
SELECT id, value, LAG(value) OVER (ORDER BY id) AS prev_value
FROM orders;

-- Right: Provide default or use IGNORE NULLS
SELECT
  id,
  value,
  LAG(value, 1) OVER (ORDER BY id) IGNORE NULLS AS prev_value,
  COALESCE(LAG(value, 1) OVER (ORDER BY id), 0) AS prev_value_default
FROM orders;
```

**Debugging Tip:**
Check data order with:
```sql
SELECT id, value FROM orders ORDER BY id LIMIT 10;
```

---

### **Issue 3: Filtering Breaks Window Functions**
**Symptoms:**
- Totals/sums don’t match after `WHERE` clause.
- Rows are missing post-window operation.

**Root Cause:**
- Applying `WHERE` after window functions (e.g., `WHERE running_total > X`) breaks partitioning.

**Fix:**
Move `WHERE` before window functions:
```sql
-- Wrong: Filters after window (incorrect)
SELECT * FROM (
  SELECT id, value, SUM(value) OVER (ORDER BY id) AS running_total
  FROM sales
) WHERE running_total > 1000;

-- Right: Filter before window
SELECT id, value, SUM(value) OVER (ORDER BY id) AS running_total
FROM sales
WHERE date > '2024-01-01';
```

**Debugging Tip:**
Test with `EXPLAIN ANALYZE` to see if partitioning happens before filtering:
```sql
EXPLAIN ANALYZE
SELECT id, SUM(value) OVER (PARTITION BY product ORDER BY id) AS running_total
FROM sales
WHERE date > '2024-01-01';
```

---

### **Issue 4: Performance Bottlenecks**
**Symptoms:**
- Query times out or uses excessive memory.
- `EXPLAIN ANALYZE` shows full table scans.

**Root Cause:**
- Large `PARTITION BY` groups (e.g., no partitioning).
- No indexes on `ORDER BY` columns.
- Recursive window functions (e.g., `LEAD()` with large offsets).

**Fix:**
1. **Optimize Partitioning**
   ```sql
   -- Bad: All rows in one partition (inefficient)
   SELECT SUM(value) OVER (ORDER BY id) AS total;

   -- Good: Partition by high-cardinality column
   SELECT SUM(value) OVER (PARTITION BY product ORDER BY id) AS product_total;
   ```

2. **Add Indexes**
   ```sql
   CREATE INDEX idx_orders_id ON orders(id);
   CREATE INDEX idx_orders_date ON orders(date);
   ```

3. **Limit Window Size**
   ```sql
   -- Bad: Uses all rows (slow)
   SELECT LAG(value, 100) OVER (ORDER BY id);

   -- Good: Use smaller offsets
   SELECT LAG(value, 5) OVER (ORDER BY id);
   ```

**Debugging Tip:**
Use `EXPLAIN ANALYZE` to identify slow operations:
```sql
EXPLAIN ANALYZE
SELECT SUM(value) OVER (PARTITION BY product ORDER BY id)
FROM sales;
```

---

### **Issue 5: Missing Rows in Results**
**Symptoms:**
- Some expected rows are omitted.
- Window functions seem to "collapse" data.

**Root Cause:**
- Using `GROUP BY` after window functions (FraiseQL may deduce rows).
- Incorrect `DISTINCT` or aggregation.

**Fix:**
Ensure window functions don’t reduce row count unintentionally:
```sql
-- Wrong: GROUP BY after window (data loss)
SELECT product, MAX(id) FROM (
  SELECT id, product, SUM(value) OVER (PARTITION BY product) AS total
  FROM sales
) GROUP BY product;

-- Right: Keep all rows
SELECT id, product, SUM(value) OVER (PARTITION BY product) AS total
FROM sales;
```

**Debugging Tip:**
Compare row counts:
```sql
-- Original rows
SELECT COUNT(*) FROM sales;

-- After window (should be same)
SELECT COUNT(*) FROM (
  SELECT id, SUM(value) OVER (PARTITION BY product) AS total
  FROM sales
);
```

---

## **4. Debugging Tools and Techniques**

### **A. `EXPLAIN ANALYZE`**
- **Why?** Shows how FraiseQL executes the query (e.g., full scans, sorts).
- **Example:**
  ```sql
  EXPLAIN ANALYZE
  SELECT id, SUM(value) OVER (PARTITION BY product ORDER BY id)
  FROM sales;
  ```
- **Look for:**
  - Sort operations (`Sort`)
  - Window aggregate nodes (`WindowAgg`)

### **B. Temporary Data Validation**
- **Test with a small subset:**
  ```sql
  SELECT * FROM (
    SELECT id, value, SUM(value) OVER (ORDER BY id) AS running_total
    FROM sales
    WHERE date = '2024-01-01'
  ) LIMIT 10;
  ```
- **Compare with expected results** (e.g., spreadsheet calculations).

### **C. Log FraiseQL Metrics**
- Enable query logging for window functions:
  ```sql
  SET fraise.log_window_functions = on;
  ```
- Check logs for:
  - Partition sizes
  - Sorting overhead

### **D. Compare with Legacy Code**
- Replicate a window function in **FraiseQL vs. self-join** to verify correctness:
  ```sql
  -- Self-join (legacy)
  SELECT a.id, a.value, SUM(b.value) AS running_total
  FROM sales a
  JOIN sales b ON a.id >= b.id
  GROUP BY a.id;

  -- FraiseQL (new)
  SELECT id, value, SUM(value) OVER (ORDER BY id) AS running_total
  FROM sales;
  ```

---

## **5. Prevention Strategies**

### **A. Design for Performance**
1. **Partition wisely**: Use high-cardinality columns (e.g., `PARTITION BY user_id`).
2. **Order matters**: Ensure `ORDER BY` aligns with data sequence.
3. **Avoid large offsets**: `LAG(1000)` is expensive; use smaller values.

### **B. Code Reviews**
- **Check for common pitfalls**:
  - Missing `PARTITION BY`
  - `WHERE` after window functions
  - Unindexed `ORDER BY` columns
- **Use static analysis tools** (if available) to flag window function issues.

### **C. Testing Framework**
- **Unit tests for window logic**:
  ```python
  # Example test (pseudo-code)
  def test_cumulative_sum():
      data = [{"id": 1, "value": 10}, {"id": 2, "value": 20}]
      expected = [{"id": 1, "running_total": 10}, {"id": 2, "running_total": 30}]
      assert query("SELECT id, value, SUM(value) OVER (ORDER BY id) AS running_total FROM sales") == expected
  ```
- **Test edge cases**:
  - NULL values
  - Empty partitions
  - Large datasets (use `LIMIT`)

### **D. Documentation**
- **Add comments** to window functions:
  ```sql
  -- Window over orders per customer, ordered by date
  SELECT
    customer_id,
    order_date,
    amount,
    SUM(amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS customer_spend
  FROM orders;
  ```
- **Track migration from legacy code** (self-joins → window functions).

---

## **6. When to Escalate**
| **Issue**                          | **Escalation Level** | **Action**                          |
|-------------------------------------|----------------------|-------------------------------------|
| Query exceeds memory limits         | High                 | Optimize partitioning or use hints  |
| Bug in FraiseQL window implementation | Critical           | Report to Fraise dev team           |
| Performance degradation unexplainable | Medium             | Share `EXPLAIN ANALYZE` output      |

---

## **7. Summary Checklist**
| **Step**                          | **Action**                                  |
|------------------------------------|---------------------------------------------|
| **Verify symptoms**               | Check `EXPLAIN ANALYZE`, data order, partitions |
| **Fix common issues**             | Correct `PARTITION BY`, `ORDER BY`, `WHERE` placement |
| **Optimize performance**          | Add indexes, reduce partition size, limit offsets |
| **Test thoroughly**               | Validate small subsets, compare with legacy code |
| **Document changes**              | Add comments, update tests                   |

---
**Final Note:** Window functions can dramatically improve query efficiency when used correctly. If stuck, start with `EXPLAIN ANALYZE` and validate logic with small datasets. For complex issues, compare against a proven self-join implementation.