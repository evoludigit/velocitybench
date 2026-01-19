# **[Pattern] SQL Window Functions – Reference Guide**

---

## **1. Overview**
SQL **window functions** compute values over a set of table rows related to the current row, without collapsing rows into aggregate results. Unlike `GROUP BY`, which reduces rows to a single output, window functions preserve individual rows while applying calculations across defined *frames* of data. Common use cases include:

- **Ranking** (`RANK()`, `DENSE_RANK()`, `ROW_NUMBER()`) for leaderboards or performance tracking.
- **Analytics** (running totals, moving averages, percentiles).
- **Time-series** comparisons (year-over-year growth, rolling sums).
- **Gap-and-island analysis** (identifying sequential groups).

Window functions are supported in all major SQL dialects (PostgreSQL, SQL Server, MySQL 8.0+, Oracle, BigQuery).

---

## **2. Core Components**

| **Component**       | **Purpose**                                                                                     | **Example**                                                                 |
|---------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **OVER(…)**         | Defines the window frame for calculations.                                                     | `OVER(PARTITION BY category ORDER BY sale_date)`                           |
| **PARTITION BY**    | Divides rows into groups (like `GROUP BY`, but rows remain).                                | `PARTITION BY region`                                                        |
| **ORDER BY**        | Orders rows within each partition (required unless using `ROWS/RANGE BETWEEN`).              | `ORDER BY sale_date DESC`                                                  |
| **Frame Clauses**   | Specifies which rows contribute to the calculation (optional if not specified).              | `ROWS BETWEEN 1 PRECEDING AND CURRENT ROW`                                  |
| **Window Functions**| Performs calculations (e.g., `SUM()`, `AVG()`, `RANK()`).                                     | `SUM(sale_amount) OVER(...)`                                               |

---

## **3. Schema Reference**

### **Sample Table: `sales`**
```sql
CREATE TABLE sales (
    sale_id INT PRIMARY KEY,
    product_id INT NOT NULL,
    sale_date DATE NOT NULL,
    sale_amount DECIMAL(10,2) NOT NULL,
    region VARCHAR(50) NOT NULL
);
```

| Column        | Type         | Description                          |
|---------------|--------------|--------------------------------------|
| `sale_id`     | INT          | Unique identifier for each sale.      |
| `product_id`  | INT          | ID of the sold product.               |
| `sale_date`   | DATE         | Date of the transaction.              |
| `sale_amount` | DECIMAL(10,2)| Amount spent (in USD).                |
| `region`      | VARCHAR(50)  | Geographic region of the sale.        |

---
---

## **4. Query Examples**

### **4.1 Basic Window Function: Running Total**
Calculate a cumulative sum of sales per product.

```sql
SELECT
    product_id,
    sale_date,
    sale_amount,
    SUM(sale_amount) OVER (
        PARTITION BY product_id
        ORDER BY sale_date
    ) AS running_total
FROM sales
ORDER BY product_id, sale_date;
```
**Output:**
Shows each sale alongside the total sales for the product up to that date.

---

### **4.2 Ranking: Top 3 Products by Revenue**
Rank products by total sales, ignoring ties (use `DENSE_RANK()` for no gaps).

```sql
SELECT
    product_id,
    SUM(sale_amount) AS total_revenue,
    RANK() OVER (ORDER BY SUM(sale_amount) DESC) AS sales_rank
FROM sales
GROUP BY product_id;
```
**Output:**
| product_id | total_revenue | sales_rank |
|------------|---------------|------------|
| 101        | 5000.00       | 1          |
| 102        | 3500.00       | 2          |
| 103        | 3500.00       | 3          |

---

### **4.3 Moving Average (3-Day Window)**
Compute a 3-day rolling average of sales.

```sql
SELECT
    sale_date,
    sale_amount,
    AVG(sale_amount)
    OVER (
        ORDER BY sale_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3d
FROM sales
ORDER BY sale_date;
```
**Key Clause:**
- `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` includes the current row and 2 prior rows.

---

### **4.4 Year-over-Year Growth**
Compare current-year sales to the same period last year.

```sql
SELECT
    sale_date,
    sale_amount,
    sale_amount -
    LAG(sale_amount, 12) OVER (PARTITION BY product_id ORDER BY sale_date) AS yoy_growth
FROM sales
WHERE sale_date >= '2023-01-01'
ORDER BY product_id, sale_date;
```
**Key Function:**
- `LAG()` retrieves the value *n* rows before the current row.

---

### **4.5 Gap-and-Island Analysis**
Identify distinct groups of sequential dates (e.g., for inventory turnover).

```sql
WITH date_groups AS (
    SELECT
        product_id,
        sale_date,
        sale_amount,
        sale_date - ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY sale_date
        ) AS grp_id
    FROM sales
)
SELECT
    product_id,
    MIN(sale_date) AS start_date,
    MAX(sale_date) AS end_date,
    SUM(sale_amount) AS total_sales
FROM date_groups
GROUP BY product_id, grp_id
ORDER BY product_id, start_date;
```
**Key Insight:**
- `ROW_NUMBER() OVER(...)` assigns a sequential ID to each date, which is subtracted from the date to create groups.

---

### **4.6 Percentile Analysis**
Find the 90th percentile of sale amounts per region.

```sql
SELECT
    region,
    sale_amount,
    PERCENT_RANK()
    OVER (PARTITION BY region ORDER BY sale_amount) AS percentile_90
FROM sales
WHERE PERCENT_RANK() OVER (PARTITION BY region ORDER BY sale_amount) >= 0.9
ORDER BY region, sale_amount DESC;
```

---

## **5. Frame Clauses (Advanced)**
Define the window boundaries for calculations. Common options:

| Clause                          | Inclusive? | Example Use Case                          |
|---------------------------------|------------|-------------------------------------------|
| `ROWS BETWEEN n PRECEDING AND m FOLLOWING` | Yes       | Sliding window (e.g., moving average).    |
| `UNBOUNDED PRECEDING AND CURRENT ROW` | Yes       | Running total up to current row.          |
| `CURRENT ROW AND UNBOUNDED FOLLOWING`  | Yes       | Aggregate all future rows.                 |
| `RANGE BETWEEN ...`             | No         | Uses a value's range (e.g., `RANGE BETWEEN '2023-01-01' AND '2023-12-31'`). |

**Example: Sliding 7-Day Window**
```sql
SELECT
    sale_date,
    sale_amount,
    AVG(sale_amount)
    OVER (
        ORDER BY sale_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS weekly_avg
FROM sales;
```

---

## **6. Performance Considerations**
1. **Avoid `SELECT *`**: Only select columns used in window functions to reduce I/O.
2. **Index `ORDER BY` columns**: Critical for performance (e.g., `CREATE INDEX idx_sales_date ON sales(sale_date)`).
3. **Limit partitions**: Large `PARTITION BY` clauses can slow queries.
4. **Use approximate functions** (e.g., `APPROX_COUNT_DISTINCT`) for large datasets in BigQuery/Spark.

---

## **7. Related Patterns**
| Pattern                          | Description                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|
| **[Aggregate Functions]**        | Compare with `GROUP BY` (collapsing rows vs. preserving rows).             |
| **[Self-Join for Ranking]**       | Alternative to window functions for simple rankings.                        |
| **[CTEs for Complex Logic]**      | Break down multi-step window calculations into readable chunks.             |
| **[Partition Pruning]**          | Filter partitions early to reduce window Processing (e.g., `WHERE region = 'US'`). |
| **[Time-Based Joins]**           | Correlate window data with external time-series tables.                    |

---
---
**Key Takeaway:**
Window functions enable **rich analytics without collapsing data**, making them indispensable for reporting, time-series analysis, and competitive intelligence. Mastery of `PARTITION BY`, `ORDER BY`, and frame clauses unlocks powerful query capabilities.