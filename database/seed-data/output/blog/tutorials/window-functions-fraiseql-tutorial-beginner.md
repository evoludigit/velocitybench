```markdown
# **Window Functions in FraiseQL (Phase 5): Turning Analytical Queries from "Grouped" to "Granular"**

*A beginner-friendly guide to window functions—keeping all your data while adding smart context to every row.*

---

## **Introduction: When GROUP BY Isn’t Enough**

Imagine you’re running a small e-commerce business and want to analyze your product sales. You could group your sales data by product category to see which categories are performing best—*that’s what `GROUP BY` does*. But what if you want to answer more nuanced questions?

- Which products in the "Electronics" category are selling the most?
- How does this month’s revenue compare to last month’s in each category?
- What’s the running total of orders so far this year?

`GROUP BY` hides the details—it collapses rows into aggregated rows (e.g., `SUM(sales) per category`). But window functions solve this problem by *keeping all rows* while adding calculated columns based on related rows. These are **window functions**, and they’re coming to FraiseQL in **Phase 5**.

In this post, we’ll explore:
✅ **What window functions do** (and why they’re better than `GROUP BY` for analytics)
✅ **Key window functions** (ranking, LAG/LEAD, running aggregates)
✅ **Real-world examples** with SQL code
✅ **Common mistakes** and how to avoid them

Let’s dive in!

---

## **The Problem: Grouping Loses Context**

### **Example 1: Ranking Products Without Losing Data**
Suppose you want to rank your best-selling products *within each category*, but you also want to keep all the original rows (not just the top ones).

With `GROUP BY`, you’d lose the individual product details:
```sql
-- Problem: GROUP BY collapses rows!
SELECT
    category,
    SUM(quantity) AS total_sales,
    RANK() OVER (ORDER BY SUM(quantity)) AS global_rank
FROM sales
GROUP BY category
ORDER BY category;
```
This gives you totals per category *and* a global rank—but you’ve lost the per-product details!

### **Example 2: Month-over-Month Growth**
You want to compare each month’s revenue to the previous month’s revenue. `GROUP BY` won’t help because it groups by month and replaces each month with a single aggregated value.

### **Example 3: Running Totals**
Calculating a running total (e.g., cumulative orders) requires seeing every row while adding a "total so far" column. `GROUP BY` can’t do this—window functions can.

---
## **The Solution: Window Functions Keep All Rows**

Window functions **preserve all rows** while adding calculated columns based on a "window" of related rows. The key is the `OVER()` clause, which defines how the window is formed.

### **Core Components of a Window Function**
A window function has this structure:
```sql
window_function() OVER (
    PARTITION BY column1, column2,
    ORDER BY column3,
    [FRAME CLause]
)
```
- **`PARTITION BY`**: Divides rows into groups (like `GROUP BY` but keeps rows)
- **`ORDER BY`**: Defines the order within each partition
- **`FRAME CLAUSE` (optional)**: Controls which rows are included in calculations (e.g., "last 3 rows")

---

## **Part 1: Ranking Functions (Assigning Order Within Partitions)**

Ranking functions assign an ordinal to each row within a partition. There are four key types:

| Function       | Description                                                                 |
|----------------|-----------------------------------------------------------------------------|
| `ROW_NUMBER()` | Assigns a unique number (no gaps)                                            |
| `RANK()`       | Assigns ranks with gaps if there are ties                                      |
| `DENSE_RANK()` | Assigns ranks without gaps (e.g., 1,2,2,3)                                   |
| `NTILE(n)`     | Divides rows into `n` equal-sized "tiles" (e.g., `NTILE(4)` → 4 quartiles) |

### **Example 1: Top 3 Products per Category**
```sql
-- Find the top 3 selling products in each category
SELECT
    category,
    product_name,
    SUM(quantity) AS total_quantity,
    RANK() OVER (PARTITION BY category ORDER BY SUM(quantity) DESC) AS sales_rank
FROM sales
GROUP BY category, product_name
ORDER BY category, sales_rank;
```
**Output:**
| category      | product_name   | total_quantity | sales_rank |
|---------------|----------------|----------------|------------|
| Electronics   | Laptop Pro     | 150            | 1          |
| Electronics   | Smartphone X   | 130            | 2          |
| Electronics   | Headphones     | 100            | 3          |
| Electronics   | Wireless Earbuds | 80          | 4          |

### **Example 2: Dynamic Tiling (NTILE)**
```sql
-- Divide products into 4 performance groups (quartiles)
SELECT
    product_name,
    SUM(quantity) AS total_sales,
    NTILE(4) OVER (ORDER BY SUM(quantity) DESC) AS performance_tier
FROM sales
GROUP BY product_name
ORDER BY total_sales DESC;
```
**Output:**
| product_name   | total_sales | performance_tier |
|----------------|-------------|------------------|
| Laptop Pro     | 150         | 1                |
| Smartphone X   | 130         | 1                |
| Headphones     | 100         | 2                |
| Wireless Earbuds | 80     | 2                |

---

## **Part 2: Value Functions (Accessing Other Rows in the Window)**

Value functions let you reference values from other rows in the same window. These are useful for:
- Comparing current month to previous month (`LAG`)
- Looking ahead to next month (`LEAD`)
- Using the first/last value in a window (`FIRST_VALUE`, `LAST_VALUE`)

| Function      | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| `LAG(column)` | Gets the value from a previous row                                            |
| `LEAD(column)`| Gets the value from a next row                                               |
| `FIRST_VALUE` | Gets the first value in the window                                           |
| `LAST_VALUE`  | Gets the last value in the window                                            |

### **Example 1: Month-over-Month Growth**
```sql
-- Compare this month's revenue to last month's
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue,
    revenue - LAG(revenue) OVER (ORDER BY month) AS growth
FROM monthly_revenue
ORDER BY month;
```
**Output:**
| month       | revenue | previous_month_revenue | growth   |
|-------------|---------|------------------------|----------|
| Jan 2024    | 5000    | NULL                   | 5000     |
| Feb 2024    | 5500    | 5000                   | 500      |
| Mar 2024    | 6000    | 5500                   | 500      |

### **Example 2: Using FIRST_VALUE for "First in Partition"**
```sql
-- Find the best-selling product in each category
SELECT
    category,
    product_name,
    SUM(quantity) AS total_quantity,
    FIRST_VALUE(product_name) OVER (
        PARTITION BY category
        ORDER BY SUM(quantity) DESC
    ) AS best_seller
FROM sales
GROUP BY category, product_name
ORDER BY category, total_quantity DESC;
```
**Output:**
| category      | product_name   | total_quantity | best_seller     |
|---------------|----------------|----------------|-----------------|
| Electronics   | Laptop Pro     | 150            | Laptop Pro      |
| Electronics   | Smartphone X   | 130            | Laptop Pro      |
| Electronics   | Headphones     | 100            | Laptop Pro      |

---

## **Part 3: Aggregate as Window (Running Totals & Moving Averages)**

You can use aggregates like `SUM`, `AVG`, or `COUNT` inside `OVER()` to calculate running totals or other statistics.

### **Example 1: Running Total**
```sql
-- Calculate cumulative orders
SELECT
    order_date,
    quantity,
    SUM(quantity) OVER (ORDER BY order_date) AS running_total
FROM orders
ORDER BY order_date;
```
**Output:**
| order_date   | quantity | running_total |
|--------------|----------|----------------|
| 2024-01-01   | 5        | 5              |
| 2024-01-02   | 3        | 8              |
| 2024-01-03   | 2        | 10             |

### **Example 2: Moving Average (3-Month Window)**
```sql
-- Calculate a 3-month moving average of revenue
SELECT
    month,
    revenue,
    AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3m
FROM monthly_revenue
ORDER BY month;
```
**Output:**
| month       | revenue | moving_avg_3m |
|-------------|---------|---------------|
| Jan 2024    | 5000    | 5000          |
| Feb 2024    | 5500    | 5250          |
| Mar 2024    | 6000    | 5500          |
| Apr 2024    | 6500    | 6000          |

---

## **Part 4: The FRAME Clause (Controlling the Window)**

The `FRAME` clause defines which rows are included in the window calculation. There are three types:

1. **`ROWS BETWEEN ... AND ...`**: Rows are selected based on their physical position.
   ```sql
   OVER (ORDER BY date ROWS BETWEEN 5 PRECEDING AND CURRENT ROW)
   ```

2. **`RANGE BETWEEN ... AND ...`**: Rows are selected based on their value (e.g., "all rows where date is within 1 month").
   ```sql
   OVER (ORDER BY date RANGE BETWEEN INTERVAL '1 month' PRECEDING AND CURRENT ROW)
   ```

3. **`GROUPS`**: Groups rows into buckets (e.g., every 3 rows).
   ```sql
   OVER (ORDER BY date GROUPS BETWEEN 3 PRECEDING AND CURRENT ROW)
   ```

### **Example: 7-Day Moving Average**
```sql
-- Moving average over the last 7 days
SELECT
    date,
    temperature,
    AVG(temperature) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS avg_last_7_days
FROM weather_data
ORDER BY date;
```

---

## **Implementation Guide: When to Use Window Functions**

| Scenario                          | Solution                          | Code Example                                                                 |
|-----------------------------------|-----------------------------------|------------------------------------------------------------------------------|
| Rank items within groups          | `RANK() / DENSE_RANK()`           | `RANK() OVER (PARTITION BY category ORDER BY sales DESC)`                   |
| Compare to previous row           | `LAG()`                           | `LAG(revenue) OVER (ORDER BY month)`                                         |
| Calculate running total           | `SUM() OVER (ORDER BY ...)`       | `SUM(quantity) OVER (ORDER BY order_date)`                                  |
| Find top N per group              | `NTILE()` + `WHERE` filter        | `NTILE(3) OVER (PARTITION BY category ORDER BY sales DESC)`                 |
| Moving average                    | `AVG() OVER (ORDER BY ... ROWS ...)` | `AVG(sales) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)` |

---

## **Common Mistakes to Avoid**

1. **Forgetting `PARTITION BY`**
   ❌ `ROW_NUMBER() OVER (ORDER BY sales)` → Ranks all rows globally.
   ✅ `ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales)` → Ranks per category.

2. **Misusing `GROUP BY` vs. Window Functions**
   - `GROUP BY` collapses rows (use for summaries).
   - Window functions keep rows (use for analytics).

3. **Incorrect `ORDER BY` in Window Functions**
   If you don’t `ORDER BY`, the window is unordered, and results may vary.

4. **Overcomplicating `FRAME` Clauses**
   Start with `CURRENT ROW` or simple ranges before diving into complex frames.

5. **Ignoring NULL Handling**
   - `LAG()` with no previous row returns `NULL`.
   - Use `COALESCE` to provide defaults:
     ```sql
     COALESCE(LAG(revenue) OVER (ORDER BY month), 0) AS prev_revenue
     ```

---

## **Key Takeaways**

✔ **Window functions keep all rows** while adding calculated columns (unlike `GROUP BY`).
✔ **`OVER()` is the key clause**—it defines the window (partition, order, frame).
✔ **Ranking functions** (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`) assign order.
✔ **Value functions** (`LAG`, `LEAD`, `FIRST_VALUE`) access other rows.
✔ **Aggregates as windows** (`SUM`, `AVG`) enable running totals and moving averages.
✔ **`FRAME` clauses** control which rows are included in calculations.

---
## **Conclusion: Why Window Functions Are a Game-Changer**

Window functions are a **powerful tool** for analytical queries because they:
✅ **Preserve granularity** (no collapsed rows).
✅ **Enable complex comparisons** (rankings, time-series analysis).
✅ **Simplify multi-step calculations** (e.g., running totals, moving averages).

In FraiseQL’s **Phase 5**, these functions will be available, giving you the flexibility to answer questions like:
- *"What’s the month-over-month growth in each category?"*
- *"Which products are in the top quartile for sales?"*
- *"What’s the cumulative revenue trend over time?"*

Ready to try them out? Start with simple rankings (`RANK()`, `ROW_NUMBER()`) and gradually explore `LAG`, running totals, and moving averages. Happy querying!

---
### **Further Reading**
- [PostgreSQL Window Functions Docs](https://www.postgresql.org/docs/current window-functions.html)
- [SQLWindow Functions Tutorial (W3Schools)](https://www.w3schools.com/sql/sql_window_functions.asp)
- [FraiseQL Roadmap (Phase 5)](https://fraise.dev/roadmap)

**Got questions?** Drop them in the comments or tweet at us (@fraise_db)!
```