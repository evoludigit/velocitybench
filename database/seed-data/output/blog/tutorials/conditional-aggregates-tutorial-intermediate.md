```markdown
# **Conditional Aggregates in SQL: FILTER vs. CASE WHEN for Smart Data Analysis**

*Write fewer queries. Get cleaner metrics. Master conditional aggregates like a pro.*

You’ve worked with SQL for years, and you know the drill: when you need multiple filtered aggregates—like revenue broken down by payment method—you’ve either:
- Run separate queries for each condition (slow, messy)
- Stuck multiple `UNION` operations (complex, inefficient)
- Filtered results in your app code (slow, fragile)

What if you could get **all** your conditional aggregates in a single query?

Welcome to **conditional aggregates**—a powerful pattern using either PostgreSQL’s native `FILTER` clause or the ubiquitous `CASE WHEN` trick. With this technique, you can compute:
- Total revenue **and** credit card revenue **and** PayPal revenue **in one query**
- Active users **by region** while tracking overall active user count
- Sales trends **filtered by product category** alongside total sales

No more round-trips to the database. No more application-side filtering. Just clean, efficient SQL.

In this tutorial, we’ll cover:
✔ When and why to use conditional aggregates
✔ PostgreSQL’s `FILTER` clause (native and powerful)
✔ The `CASE WHEN` emulation for MySQL, SQL Server, and SQLite
✔ How to handle multiple conditions in a single query
✔ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Why You’ve Been Writing Suboptimal SQL**

Calculating conditional aggregates isn’t just a coding nuisance—it’s a **performance tax**. Traditional approaches force you to:

### **1. Write Separate Queries**
```sql
-- Total revenue
SELECT SUM(revenue) FROM sales;

-- Just credit card revenue
SELECT SUM(revenue) FROM sales WHERE payment_method = 'credit_card';

-- Just PayPal revenue
SELECT SUM(revenue) FROM sales WHERE payment_method = 'paypal';
```
**Problem:** Three round-trips to the database. Each query runs independently, potentially hitting the same indexes and tables repeatedly.

### **2. Use `UNION` to Merge Results**
```sql
SELECT 'Total' AS payment_type, SUM(revenue) FROM sales
UNION ALL
SELECT 'Credit Card', SUM(revenue) FROM sales WHERE payment_method = 'credit_card'
UNION ALL
SELECT 'PayPal', SUM(revenue) FROM sales WHERE payment_method = 'paypal';
```
**Problem:** `UNION` is inefficient for large datasets. The database can’t optimize the separate filtered scans as a single operation.

### **3. Filter Aggregates in Application Code**
```javascript
// Pseudo-code: app-side filtering
const sales = await db.query('SELECT * FROM sales');
const totalRevenue = sum(sales.revenue);
const ccRevenue = sum(sales.filter(s => s.payment_method === 'credit_card').revenue);
const paypalRevenue = sum(sales.filter(s => s.payment_method === 'paypal').revenue);
```
**Problem:** Transferring raw data to the app forces you to fetch **everything** upfront, then filter in memory. This is slow for large datasets and adds unnecessary load.

### **4. Use Multiple Subqueries with Fixed Conditions**
```sql
SELECT
  SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE 0 END) AS cc_revenue,
  SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS paypal_revenue,
  SUM(revenue) AS total_revenue
FROM sales;
```
**Problem:** Works, but you’re repeating logic for every filter.

**Conditional aggregates solve all of this.** They let you calculate **all** filtered aggregates in **one query**, leveraging the database’s optimizer to do the heavy lifting.

---

## **The Solution: Two Ways to Conditional Aggregates**

The goal is simple: **Apply a filter to an aggregate function**. The database should handle this natively, not as afterthoughts.

There are two ways to achieve this:

1. **PostgreSQL’s `FILTER` Clause** (Native and elegant)
2. **`CASE WHEN` Emulation** (Works everywhere else)

Both achieve the same result but with different syntax. Let’s explore each.

---

### **1. PostgreSQL: Native `FILTER` (Best for New Projects)**
PostgreSQL’s `FILTER` clause is designed for this exact use case. It lets you apply a `WHERE`-like condition directly to an aggregate function.

#### **Basic Syntax**
```sql
SUM(column_name) FILTER (WHERE condition)
```

#### **Example: Revenue by Payment Method**
```sql
SELECT
  SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS credit_card_total,
  SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal_total,
  SUM(revenue) AS total_revenue
FROM sales;
```
**Output:**
```
credit_card_total | paypal_total | total_revenue
-----------------+-------------+---------------
30,000.00        | 12,000.00   | 50,000.00
```

#### **Advantages of `FILTER`**
✅ **Readable:** Clearly expresses intent.
✅ **Efficient:** PostgreSQL optimizes each filter independently.
✅ **Extensible:** Works with any aggregate (`AVG`, `COUNT`, `MAX`).

#### **What If I Need a Column Value?**
Sometimes, you need both the filtered value **and a column value** (e.g., "PayPal" for the PayPal revenue row). Use `CASE` for that:

```sql
SELECT
  CASE
    WHEN payment_method = 'credit_card' THEN SUM(revenue)
    WHEN payment_method = 'paypal' THEN SUM(revenue)
    ELSE NULL
  END AS revenue,
  payment_method
FROM sales
GROUP BY payment_method;
```

---

### **2. `CASE WHEN` (Works Everywhere)**
Not all databases support `FILTER`. For MySQL, SQLite, SQL Server, and others, use `CASE WHEN` to emulate the same behavior.

#### **Basic Syntax**
```sql
SUM(CASE WHEN condition THEN column_name ELSE 0 END)
```

#### **Example: Same Revenue Query as Above**
```sql
SELECT
  SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE 0 END) AS credit_card_total,
  SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS paypal_total,
  SUM(revenue) AS total_revenue
FROM sales;
```

#### **When to Use `CASE WHEN`?**
✅ **Cross-database compatibility** (MySQL, SQLite, SQL Server, etc.).
✅ **When you need dynamic conditions** (e.g., filtering based on a variable).
✅ **Legacy systems** that don’t support `FILTER`.

#### **Disadvantages of `CASE WHEN`**
❌ **Less readable** for complex conditions.
❌ **Slightly slower** in some databases (but negligible in practice).
❌ **Harder to debug** if conditions grow complicated.

#### **Example with Dynamic Conditions**
```sql
-- Using a variable for flexibility (e.g., in a stored procedure)
DECLARE @min_revenue DECIMAL(10,2) = 100;

SELECT
  SUM(CASE WHEN revenue >= @min_revenue THEN revenue ELSE 0 END) AS high_value_sales
FROM sales;
```

---

## **Implementation Guide: Practical Examples**

Let’s build up from simple to complex scenarios.

### **Example 1: Basic Conditional Aggregates**
**Goal:** Calculate total sales, credit card sales, and PayPal sales in one query.

#### **PostgreSQL (`FILTER`)**
```sql
SELECT
  SUM(revenue) AS total_sales,
  SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS cc_sales,
  SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal_sales
FROM sales;
```

#### **MySQL (`CASE WHEN`)**
```sql
SELECT
  SUM(revenue) AS total_sales,
  SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE 0 END) AS cc_sales,
  SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS paypal_sales
FROM sales;
```

### **Example 2: Multiple Groups with Conditions**
**Goal:** Calculate revenue by product category, but **only** for sales above $100.

#### **PostgreSQL (`FILTER`)**
```sql
SELECT
  category,
  SUM(revenue) AS total_category_revenue,
  SUM(revenue) FILTER (WHERE revenue > 100) AS high_value_category_revenue
FROM sales
GROUP BY category;
```

#### **MySQL (`CASE WHEN`)**
```sql
SELECT
  category,
  SUM(revenue) AS total_category_revenue,
  SUM(CASE WHEN revenue > 100 THEN revenue ELSE 0 END) AS high_value_category_revenue
FROM sales
GROUP BY category;
```

### **Example 3: Dynamic Filtering (Advanced)**
**Goal:** Filter based on a parameter (e.g., only include sales from the last 30 days).

#### **PostgreSQL (with a variable)**
```sql
DO $$
DECLARE
  start_date DATE := CURRENT_DATE - INTERVAL '30 days';
BEGIN
  SELECT
    SUM(revenue) AS recent_sales,
    SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS recent_paypal_sales
  FROM sales
  WHERE sale_date >= start_date;
END $$;
```

#### **MySQL (stored procedure)**
```sql
DELIMITER //
CREATE PROCEDURE get_recent_sales(IN days INT)
BEGIN
  DECLARE start_date DATE;

  SET start_date = DATE_SUB(CURRENT_DATE(), INTERVAL days DAY);

  SELECT
    SUM(revenue) AS recent_sales,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE 0 END) AS recent_paypal_sales
  FROM sales
  WHERE sale_date >= start_date;
END //
DELIMITER ;
```

---

## **Common Mistakes to Avoid**

### **1. Forgetting to Handle NULLs**
If your column contains `NULL`, `CASE WHEN` will ignore it, but `FILTER` may behave unexpectedly.
**Fix:** Explicitly include `NULL` in your conditions.

```sql
-- Bad: NULLs are ignored
SUM(CASE WHEN revenue > 0 THEN revenue ELSE 0 END)

-- Better: Explicitly handle NULL
SUM(CASE WHEN revenue IS NULL OR revenue > 0 THEN revenue ELSE 0 END)
```

### **2. Overcomplicating with `CASE`**
If you have many conditions, a long `CASE` statement becomes unreadable. Consider pivoting to a separate query or using a `UNION` with a dummy column.

```sql
-- Unreadable with 5+ conditions
SUM(CASE
  WHEN payment_method = 'cc' THEN revenue
  WHEN payment_method = 'paypal' THEN revenue
  WHEN payment_method = 'bank_transfer' THEN revenue
  ELSE 0
END)

-- Better: Use a pivot approach
SELECT
  payment_type,
  SUM(revenue) AS revenue
FROM (
  VALUES
    ('Total', NULL, revenue),
    ('Credit Card', 'cc', revenue),
    ('PayPal', 'paypal', revenue)
) AS t(payment_type, method, revenue)
JOIN sales ON t.method = sales.payment_method OR t.method IS NULL
WHERE t.payment_type IS NULL OR sales.payment_method = t.method
GROUP BY payment_type;
```

### **3. Not Using `ELSE` in `CASE WHEN`**
If you omit `ELSE 0`, the aggregate will ignore rows where the condition fails, which may not be what you want.

```sql
-- Wrong: Skips rows where payment_method isn't 'cc' or 'paypal'
SUM(CASE WHEN payment_method = 'cc' THEN revenue END)

-- Correct: Treats non-matching rows as 0
SUM(CASE WHEN payment_method = 'cc' THEN revenue ELSE 0 END)
```

### **4. Assuming `FILTER` Works Everywhere**
If you’re using a non-PostgreSQL database, `FILTER` won’t work. Always check your database dialect.

### **5. Forgetting Indexes**
Conditional aggregates **still** benefit from proper indexes. If your filter column (`payment_method`, `category`) isn’t indexed, the query will be slow.

```sql
-- Create an index for faster filtering
CREATE INDEX idx_sales_payment_method ON sales(payment_method);
```

---

## **Key Takeaways**

Here’s what you should remember:

✅ **Use `FILTER` in PostgreSQL** for cleaner, more efficient conditional aggregates.
✅ **Use `CASE WHEN` elsewhere** for cross-database compatibility.
✅ **Conditional aggregates reduce database round-trips**—better performance and cleaner code.
✅ **Handle `NULL` values explicitly** to avoid unintended behavior.
✅ **Keep conditions simple**—avoid unreadable `CASE` statements.
✅ **Leverage indexes** for filtered columns to keep queries fast.
✅ **Dynamic filtering is possible** with variables or stored procedures.

---

## **Conclusion: Write Smarter SQL, Not Harder**

Conditional aggregates are a **game-changer** for anyone who’s ever had to:
- Run three queries just to get a single dashboard metric.
- Merge results with `UNION` and wonder why it’s slow.
- Filter raw data in application code and sigh at the performance hit.

With `FILTER` or `CASE WHEN`, you can **combine multiple filtered aggregations into a single query**, letting the database do the heavy lifting efficiently.

### **Next Steps**
1. **Try it in your project:** Replace slow, multi-query reports with conditional aggregates.
2. **Experiment with `FILTER` vs. `CASE WHEN:** See which fits your database better.
3. **Optimize:** Check your query plan to ensure the database is using indexes effectively.

The goal isn’t just to write *faster* SQL—it’s to write **smarter** SQL. And conditional aggregates are a key part of that.

Now go write that clean, efficient query and stop banging your head against the database wall.

---
**What’s your favorite trick for optimizing SQL queries? Drop a comment below!**
```