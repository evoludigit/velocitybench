```markdown
# **Window Functions in FraiseQL: Powerful Analytics Without Collapsing Rows**

If you’ve ever analyzed data in SQL and wished you could calculate rankings, compare rows to their neighbors, or track running totals—**without losing individual rows**—then window functions are your secret weapon.

FraiseQL, a modern SQL-like query language, is planning to introduce **Phase 5 window functions** as part of its ongoing evolution. These functions will let you perform complex analytical calculations while preserving every single row in your dataset. Whether you're ranking products, computing month-over-month growth, or calculating cumulative orders, window functions keep your data intact while adding powerful context.

In this guide, we’ll explore **why window functions exist**, how they differ from `GROUP BY`, and how FraiseQL’s upcoming implementation will work. We’ll also dive into practical examples, common pitfalls, and best practices to help you leverage this powerful feature effectively.

---

## **The Problem: Why GROUP BY Isn’t Enough**

Traditional aggregations like `GROUP BY` are great for summarizing data—like calculating total sales per product category—but they **collapse rows**, making it harder to analyze individual records. Here are real-world scenarios where window functions shine:

### **1. Ranking Without Losing Data**
Suppose you want to **rank all products by sales within their category**—but you also need to keep every product’s original details (name, price, etc.).
With `GROUP BY`, you’d lose the ability to reference individual rows:

```sql
-- ❌ Loses individual product data
SELECT
    category,
    SUM(quantity) AS total_sales,
    RANK() OVER (PARTITION BY category ORDER BY SUM(quantity)) AS rank
FROM products
GROUP BY category
-- This is invalid SQL (can't use window functions with GROUP BY directly)
```

### **2. Comparing Rows to Their Neighbors**
You might need to **compare each month’s revenue to the previous month** (moMo growth), but you still need every month’s original data.

```sql
-- ❌ Hard to compute without window functions
SELECT
    month,
    revenue,
    (revenue - LAG(revenue) OVER (ORDER BY month)) / LAG(revenue) OVER (ORDER BY month) * 100 AS moMo_growth
FROM sales
```

### **3. Running Totals & Moving Averages**
Calculating **cumulative orders** or **moving averages** requires looking at rows before the current one—but `GROUP BY` doesn’t support this.

```sql
-- ❌ GROUP BY can't compute running sums
SELECT
    customer,
    order_date,
    SUM(amount) OVER (PARTITION BY customer ORDER BY order_date) AS running_total
FROM orders
```

### **4. Filtering After Ranking (Partitions + Window)**
You might want to **find the top 3 products in each category** but keep all rows for further analysis.

```sql
-- ❌ GROUP BY can't filter after ranking
SELECT *
FROM (
    SELECT
        product,
        category,
        sales,
        RANK() OVER (PARTITION BY category ORDER BY sales DESC) AS rank
    FROM product_sales
) ranked_products
WHERE rank <= 3
```

### **The Issue**
`GROUP BY` **collapses rows**, while window functions **preserve all rows** and add computed columns. FraiseQL’s upcoming window functions will finally bring this power to its query engine.

---

## **The Solution: Window Functions in FraiseQL (Phase 5)**

FraiseQL is planning to support **three core types of window functions**:

1. **Ranking Functions** (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`)
2. **Value Functions** (`LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`)
3. **Aggregate as Window** (`SUM()`, `AVG()`, `COUNT()`, etc. with `OVER`)

Each is defined using the `OVER()` clause, which includes:
- `PARTITION BY` (groups rows like `GROUP BY` but keeps them)
- `ORDER BY` (defines row order within partitions)
- **Frame Clause** (optional, defines which rows to include in calculations)

---

## **Implementation Guide: Practical Examples**

Let’s explore each type of window function with FraiseQL-compatible syntax.

---

### **1. Ranking Functions**
Assigns ranks to rows within a partition.

#### **Example: ROW_NUMBER() (Unique Ranking)**
```sql
-- Assign unique ordinal numbers within each category
SELECT
    product,
    category,
    sales,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY sales DESC) AS rank_in_category
FROM products;
```
**Output:**
| product   | category   | sales | rank_in_category |
|-----------|------------|-------|------------------|
| Laptop X  | Electronics| 1000  | 1                |
| Smartphone| Electronics| 800   | 2                |
| Monitor   | Electronics| 500   | 3                |
| Shirt     | Clothing   | 600   | 1                |

#### **Example: RANK() (Handles Ties)**
```sql
-- Same rank for tied rows, gaps in numbering
SELECT
    product,
    category,
    sales,
    RANK() OVER (PARTITION BY category ORDER BY sales DESC) AS sales_rank
FROM products;
```
**Output:**
| product   | category   | sales | sales_rank |
|-----------|------------|-------|------------|
| Laptop X  | Electronics| 1000  | 1          |
| Smartphone| Electronics| 800   | 2          |
| Monitor   | Electronics| 500   | 3          |
| Shirt     | Clothing   | 600   | 1          |
| Pants     | Clothing   | 600   | 1          |  <!-- Same rank due to tie -->

#### **Example: DENSE_RANK() (No Gaps in Ranking)**
```sql
-- No gaps in ranking (ties get same rank, next rank is consecutive)
SELECT
    product,
    category,
    sales,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY sales DESC) AS dense_rank
FROM products;
```
**Output:**
| product   | category   | sales | dense_rank |
|-----------|------------|-------|------------|
| Laptop X  | Electronics| 1000  | 1          |
| Smartphone| Electronics| 800   | 2          |
| Monitor   | Electronics| 500   | 3          |
| Shirt     | Clothing   | 600   | 1          |
| Pants     | Clothing   | 600   | 1          |

#### **Example: NTILE() (Equal-Sized Groups)**
```sql
-- Divides rows into equal-sized buckets
SELECT
    product,
    category,
    sales,
    NTILE(3) OVER (PARTITION BY category ORDER BY sales DESC) AS sales_quartile
FROM products;
```
**Output:**
| product   | category   | sales | sales_quartile |
|-----------|------------|-------|----------------|
| Laptop X  | Electronics| 1000  | 1              |
| Smartphone| Electronics| 800   | 2              |
| Monitor   | Electronics| 500   | 3              |
| Shirt     | Clothing   | 600   | 1              |
| Pants     | Clothing   | 600   | 1              |

---

### **2. Value Functions**
Accesses values from other rows in the window.

#### **Example: LAG() (Previous Row’s Value)**
```sql
-- Compare each month’s revenue to the previous month
SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue,
    (revenue - LAG(revenue) OVER (ORDER BY month)) AS moMo_change
FROM sales;
```
**Output:**
| month   | revenue | previous_month_revenue | moMo_change |
|---------|---------|------------------------|-------------|
| Jan     | 10000   | NULL                   | NULL        |
| Feb     | 12000   | 10000                  | 2000        |
| Mar     | 11000   | 12000                  | -1000       |

#### **Example: LEAD() (Next Row’s Value)**
```sql
-- Check if next month’s revenue increases
SELECT
    month,
    revenue,
    LEAD(revenue) OVER (ORDER BY month) AS next_month_revenue,
    CASE WHEN LEAD(revenue) OVER (ORDER BY month) > revenue THEN 'Increase' ELSE 'Decrease' END AS trend
FROM sales;
```
**Output:**
| month   | revenue | next_month_revenue | trend       |
|---------|---------|--------------------|-------------|
| Jan     | 10000   | 12000              | Increase    |
| Feb     | 12000   | 11000              | Decrease    |

#### **Example: FIRST_VALUE() (First Row in Window)**
```sql
-- Get the max price in each category
SELECT
    product,
    category,
    price,
    FIRST_VALUE(price) OVER (PARTITION BY category ORDER BY price DESC) AS max_price_in_category
FROM products;
```
**Output:**
| product   | category   | price | max_price_in_category |
|-----------|------------|-------|------------------------|
| Laptop X  | Electronics| 1500  | 1500                   |
| Smartphone| Electronics| 800   | 1500                   |
| Monitor   | Electronics| 300   | 1500                   |

---

### **3. Aggregate as Window**
Computes aggregates over a set of rows (running totals, moving averages).

#### **Example: Running Total (SUM with OVER)**
```sql
-- Calculate cumulative sales per category
SELECT
    product,
    category,
    sales,
    SUM(sales) OVER (PARTITION BY category ORDER BY sales) AS running_total
FROM products;
```
**Output:**
| product   | category   | sales | running_total |
|-----------|------------|-------|----------------|
| Laptop X  | Electronics| 1000  | 1000           |
| Smartphone| Electronics| 800   | 1800           |
| Monitor   | Electronics| 500   | 2300           |
| Shirt     | Clothing   | 600   | 600            |

#### **Example: Moving Average (AVG with Frame)**
```sql
-- 3-month moving average (using RANGE BETWEEN)
SELECT
    month,
    revenue,
    AVG(revenue) OVER (
        PARTITION BY month
        ORDER BY month
        RANGE BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg
FROM sales;
```
**Output:**
| month   | revenue | moving_avg |
|---------|---------|------------|
| Jan     | 10000   | NULL       |
| Feb     | 12000   | 11000      |
| Mar     | 11000   | 11333      |

---

## **Frames: Controlling Which Rows to Include**

The `OVER` clause supports **frame definitions** to restrict calculations:

| Syntax               | Description                                  |
|----------------------|----------------------------------------------|
| `ROWS BETWEEN ...`   | Row-based (position in result set)           |
| `RANGE BETWEEN ...`  | Value-based (e.g., date ranges)              |
| `GROUPS`             | Entire partition (like `OVER (PARTITION BY)`) |

#### **Example: ROWS BETWEEN (Fixed Window)**
```sql
-- Compare revenue to the immediately preceding 2 months
SELECT
    month,
    revenue,
    AVG(revenue) OVER (
        ORDER BY month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS avg_last_2_months
FROM sales;
```

#### **Example: RANGE BETWEEN (Date-Based Window)**
```sql
-- 7-day moving average
SELECT
    order_date,
    amount,
    AVG(amount) OVER (
        ORDER BY order_date
        RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW
    ) AS weekly_avg
FROM orders;
```

---

## **Common Mistakes to Avoid**

1. **Forgetting `PARTITION BY`**
   Without `PARTITION BY`, window functions treat the **entire dataset** as one window, which is usually incorrect.
   ❌ `SUM(value) OVER (ORDER BY date)` (Wrong)
   ✅ `SUM(value) OVER (PARTITION BY user_id ORDER BY date)` (Correct)

2. **Overusing Window Functions for Simple Aggregations**
   If you only need a **single aggregate** (e.g., total sales), use `GROUP BY` instead of `OVER()` for better performance.

3. **Ignoring NULLs in LAG/LEAD**
   `LAG()` and `LEAD()` return `NULL` for the first and last rows, respectively. Handle this explicitly:
   ```sql
   SELECT
       month,
       revenue,
       LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_revenue,
       COALESCE(revenue - LAG(revenue, 1) OVER (ORDER BY month), NULL) AS moMo_change
   FROM sales;
   ```

4. **Using `ORDER BY` Without a Partition**
   Without `PARTITION BY`, `ORDER BY` in `OVER()` affects the **entire result set**, which is often unintended.

5. **Frame Clause Misconfigurations**
   Incorrect `ROWS`/`RANGE` definitions can lead to unexpected results. Always test with small datasets first.

---

## **Key Takeaways**

✅ **Window functions keep all rows** while adding computed columns.
✅ **Three main types**:
   - **Ranking** (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`)
   - **Value access** (`LAG`, `LEAD`, `FIRST_VALUE`)
   - **Aggregate as window** (`SUM`, `AVG` with `OVER`)
✅ **`PARTITION BY` groups rows like `GROUP BY` but keeps them.**
✅ **`ORDER BY` defines row ordering within partitions.**
✅ **Frames (`ROWS BETWEEN`, `RANGE BETWEEN`) control which rows influence calculations.**
✅ **Common mistakes**: Forgetting `PARTITION BY`, ignoring `NULLs`, and misusing frames.

---

## **Conclusion: Why Window Functions Matter**

FraiseQL’s upcoming **Phase 5 window functions** will bring **powerful analytical capabilities** to your queries—without collapsing rows. Whether you’re ranking products, computing month-over-month growth, or calculating running totals, window functions give you **fine-grained control** over your data.

### **Next Steps**
1. **Experiment with window functions** in your existing SQL queries.
2. **Compare performance** between `GROUP BY` and window functions for analytical tasks.
3. **Stay updated** on FraiseQL’s Phase 5 rollout for full support.

By mastering window functions, you’ll unlock **a new level of data insight**—keeping your rows intact while uncovering hidden patterns.

---
**Want to dive deeper?**
- [SQL Window Functions (Official Docs)](https://www.w3schools.com/sql/sql_window_functions.asp)
- [PostgreSQL Window Functions](https://www.postgresql.org/docs/current窗口函数.html)
- [FraiseQL Roadmap (Phase 5)](https://fraise.dev/roadmap)

Happy querying!
```