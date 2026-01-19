# **[Pattern] Window Functions in FraiseQL (Phase 5) Reference Guide**

---
## **Overview**
Window functions in FraiseQL allow analytical calculations across sets of rows—**without collapsing or aggregating them**—using the `OVER` clause. Unlike `GROUP BY`, window functions preserve individual rows while returning computed results for each. Key use cases include ranking, running totals, time-series analysis, and comparative metrics.

**Core Features (Phase 5):**
- **Ranking Functions:** `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`
- **Value Functions:** `LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`
- **Aggregate as Window:** Standard aggregates (e.g., `SUM`, `AVG`) with `OVER`
- **Windowing Clauses:** `PARTITION BY`, `ORDER BY`, and frame clauses (`ROWS`, `RANGE`, `GROUPS`)

Window functions are ideal for:
- Ranking items (e.g., top N customers by sales).
- Tracking changes across rows (e.g., week-over-week growth).
- Calculating moving averages (e.g., 3-day rolling sales).

---

## **Schema Reference**
Below are the supported window functions and their syntax components.

### **1. Ranking Functions**
| Function        | Description                                                                 | Returns                     |
|-----------------|-----------------------------------------------------------------------------|-----------------------------|
| `ROW_NUMBER()`  | Assigns a unique sequential number to rows within a window.                 | Integer (no gaps)           |
| `RANK()`        | Assigns ranks with gaps if ties exist.                                        | Integer (gaps for ties)     |
| `DENSE_RANK()`  | Assigns ranks without gaps for tied values.                                   | Integer (no gaps)           |
| `NTILE(n)`      | Divides rows into `n` equal-sized buckets.                                    | Integer (1 to n)            |

**Example Schema:**
```sql
CREATE TABLE sales (
    sale_id INT,
    product_id INT,
    amount DECIMAL(10,2),
    sale_date DATE
);
```

---

### **2. Value Functions**
| Function       | Description                                                                 | Returns                     |
|----------------|-----------------------------------------------------------------------------|-----------------------------|
| `LAG(expr)`    | Retrieves the value from a row *before* the current row.                   | `expr` type                 |
| `LEAD(expr)`   | Retrieves the value from a row *after* the current row.                    | `expr` type                 |
| `FIRST_VALUE()`| Returns the first value in the window (relative to `ORDER BY`).             | `expr` type                 |
| `LAST_VALUE()` | Returns the last value in the window (relative to `ORDER BY`; requires `ROWS BETWEEN`). | `expr` type |

**Optional Parameters:**
- `OFFSET`: Number of rows to skip (e.g., `LAG(amount, 1)`).
- `DEFAULT`: Value to return if the referenced row is missing.

---

### **3. Aggregate as Window**
Standard aggregates (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`) can be applied within a window using `OVER`.
Example:
```sql
SUM(sale_amount) OVER (PARTITION BY product_id ORDER BY sale_date)
```

---

### **4. Window Clauses**
| Clause       | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `PARTITION BY`| Groups rows into partitions (like `GROUP BY` but preserves rows).           |
| `ORDER BY`   | Defines the logical order of rows within a partition.                       |
| `ROWS/RANGE` | Frame clause to limit rows included in calculations (e.g., `ROWS BETWEEN`). |

**Frame Clause Examples:**
- `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW` → Current and prior row.
- `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` → All rows up to current.

---

## **Query Examples**

### **1. Ranking Products by Sales**
```sql
SELECT
    product_id,
    SUM(amount) AS total_sales,
    RANK() OVER (ORDER BY SUM(amount) DESC) AS sales_rank
FROM sales
GROUP BY product_id;
```
**Output:**
| product_id | total_sales | sales_rank |
|------------|-------------|------------|
| 101        | 500.00      | 1          |
| 102        | 450.00      | 2          |

---

### **2. Running Total of Sales**
```sql
SELECT
    product_id,
    sale_date,
    amount,
    SUM(amount) OVER (
        PARTITION BY product_id
        ORDER BY sale_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_total
FROM sales;
```
**Output:**
| product_id | sale_date  | amount | running_total |
|------------|------------|--------|---------------|
| 101        | 2023-01-01 | 100.00 | 100.00        |
| 101        | 2023-01-02 | 200.00 | 300.00        |

---

### **3. Comparing Sales to Prior Week**
```sql
SELECT
    product_id,
    sale_date,
    amount,
    LAG(amount, 1) OVER (PARTITION BY product_id ORDER BY sale_date) AS prev_week_sales,
    amount - LAG(amount, 1) OVER (PARTITION BY product_id ORDER BY sale_date) AS delta
FROM sales;
```
**Output:**
| product_id | sale_date  | amount | prev_week_sales | delta   |
|------------|------------|--------|-----------------|---------|
| 101        | 2023-01-01 | 100.00 | NULL            | NULL    |
| 101        | 2023-01-02 | 200.00 | 100.00          | 100.00  |

---

### **4. Moving Average (3-Day)**
```sql
SELECT
    sale_date,
    amount,
    AVG(amount) OVER (
        ORDER BY sale_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg
FROM sales;
```
**Output:**
| sale_date  | amount | moving_avg |
|------------|--------|------------|
| 2023-01-01 | 100.00 | 100.00     |
| 2023-01-02 | 200.00 | 150.00     |
| 2023-01-03 | 150.00 | 150.00     |

---

### **5. Dividing Rows into Percentiles (NTILE)**
```sql
SELECT
    product_id,
    NTILE(3) OVER (ORDER BY SUM(amount) DESC) AS sales_quartile
FROM sales
GROUP BY product_id;
```
**Output:**
| product_id | sales_quartile |
|------------|----------------|
| 101        | 1              |
| 102        | 2              |
| 103        | 3              |

---

## **Implementation Details**
### **Performance Considerations**
- **Partitioning:** Large `PARTITION BY` clauses may impact performance. Use indexes on partitioned columns.
- **Frame Clauses:** Avoid unbounded frames (e.g., `UNBOUNDED PRECEDING`) on large datasets.
- **Memory:** Window functions require temporary storage for calculations.

### **Compatibility**
- Supported in FraiseQL **Phase 5** (backward-compatible with Phase 4).
- Not supported in older phases or non-FraiseQL engines.

### **Limitations (Future Work)**
- No `CUBE`/`ROLLSUP` support for windowed aggregates.
- No `IGNORE NULLS` option for value functions (e.g., `LAG`).

---

## **Related Patterns**
1. **[Pattern] Aggregation Functions**
   - Compare with `GROUP BY` vs. window functions (e.g., `SUM OVER` vs. `GROUP BY SUM`).
2. **[Pattern] Common Table Expressions (CTEs)**
   - Use `WITH` clauses to modularize window function logic.
3. **[Pattern] Joins**
   - Combine window functions with joins for complex analytics (e.g., ranking joined tables).
4. **[Pattern] Time-Series Analysis**
   - Leverage window functions for date-based rolling calculations (e.g., month-over-month growth).

---
**Last Updated:** [Insert Date]
**Version:** 1.0 (Phase 5 Preview)