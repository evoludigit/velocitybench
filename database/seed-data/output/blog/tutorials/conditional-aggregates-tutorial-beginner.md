```markdown
# **Conditional Aggregates: Filtering Data on the Fly with FILTER and CASE WHEN**

![Coins in different denominations](https://images.unsplash.com/photo-1576941402866-0f75004b6011?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80)

Ever found yourself writing multiple queries just to get a simple breakdown of your data? Maybe you want to see **total sales** alongside **revenue from credit cards** and **revenue from PayPal**, but each requires its own `SELECT` statement or a complex `UNION`. What if I told you there’s a way to calculate all these numbers in a **single query**?

That’s the power of **conditional aggregates**—a technique that lets you filter data *inside* an aggregation function itself, saving you round-trips to the database and making your queries cleaner and more efficient. In this post, we’ll explore:

- The problem with traditional filtering approaches
- How **PostgreSQL’s `FILTER` clause** and **`CASE WHEN` emulation** solve it
- Practical examples for calculating segmented totals
- Common pitfalls and how to avoid them

By the end, you’ll see why this pattern is a game-changer for reporting, analytics, and even simple breakdowns in your applications.

---

## **The Problem: Why Calculating Filtered Aggregates is Painful**

Most SQL beginners (and even some experienced devs) fall into one of these traps when trying to get filtered aggregates:

### **1. Multiple Queries = Slow and Annoying**
Imagine you’re building a dashboard that shows:
- Total orders
- Orders from premium customers
- Orders from the last 30 days

Traditionally, you’d write three separate queries:

```sql
-- Total orders
SELECT COUNT(*) FROM orders;

-- Premium customers
SELECT COUNT(*) FROM orders WHERE customer_type = 'premium';

-- Last 30 days
SELECT COUNT(*) FROM orders WHERE order_date >= NOW() - INTERVAL '30 days';
```

This means **three database round-trips**, which is slow and inefficient—especially if you’re doing this in a high-traffic application.

### **2. UNION Overhead = Clunky and Hard to Optimize**
If you try to combine these into a single query using `UNION`, you end up with something like this:

```sql
SELECT
  SUM(amount) AS total,
  NULL AS category
FROM orders

UNION ALL

SELECT
  SUM(amount),
  'premium'
FROM orders
WHERE customer_type = 'premium'

UNION ALL

SELECT
  SUM(amount),
  'recent'
FROM orders
WHERE order_date >= NOW() - INTERVAL '30 days';
```

This works, but:
- The database has to process the same table multiple times.
- Performance suffers as the dataset grows.
- The query becomes harder to read and maintain.

### **3. Application-Side Filtering = Inefficient**
Some devs fetch all data and filter in the app:

```python
# Bad: Fetching ALL data and filtering in Python
all_orders = db.execute("SELECT * FROM orders")
total = len(all_orders)
premium = len([o for o in all_orders if o.customer_type == 'premium'])
recent = len([o for o in all_orders if o.order_date >= date.today() - timedelta(days=30)])
```

This is **terrible** for performance because:
- The entire table is transferred over the network (expensive!).
- The app has to process the data, adding latency.

### **4. Subqueries with Different Conditions = Messy**
Some try to cram everything into one query with subqueries:

```sql
SELECT
  COUNT(*) AS total_orders,
  (SELECT COUNT(*) FROM orders WHERE customer_type = 'premium') AS premium_orders,
  (SELECT COUNT(*) FROM orders WHERE order_date >= NOW() - INTERVAL '30 days') AS recent_orders
FROM orders
LIMIT 1;
```

This **technically works**, but:
- It’s hard to read and debug.
- The database optimizer struggles with correlated subqueries.
- Performance degrades with larger datasets.

---
## **The Solution: Conditional Aggregates**

The cleanest way to solve this is by using **conditional aggregates**—functions that let you filter data *inside* the aggregation itself. There are two main approaches:

1. **PostgreSQL’s `FILTER` Clause** (the cleanest and most efficient)
2. **`CASE WHEN` Emulation** (works in MySQL, SQLite, SQL Server, and others)

Both achieve the same goal: **calculate multiple filtered aggregates in a single pass**.

---

## **Solution 1: PostgreSQL’s `FILTER` Clause (The Best of All Worlds)**

PostgreSQL introduced the `FILTER` clause in **version 9.4**, and it’s *exactly* what we need for this problem.

### **How It Works**
The `FILTER` clause lets you specify conditions *inside* aggregation functions like `SUM`, `COUNT`, `AVG`, etc. This means:
- The database applies the filter *before* aggregation.
- The query runs in a single pass.
- No extra subqueries or `UNION` needed.

### **Example: Calculating Revenue by Payment Method**
Let’s say we have an `orders` table with `amount` and `payment_method`, and we want:

| Metric          | Value      |
|-----------------|------------|
| Total Revenue   | $10,000    |
| Credit Card Rev.| $8,000     |
| PayPal Rev.     | $2,000     |

**Traditional approach (three queries):**
```sql
-- Total revenue
SELECT SUM(amount) FROM orders;

-- Credit card
SELECT SUM(amount) FROM orders WHERE payment_method = 'credit_card';

-- PayPal
SELECT SUM(amount) FROM orders WHERE payment_method = 'paypal';
```

**With `FILTER` (one query):**
```sql
SELECT
  SUM(amount) AS total_revenue,
  SUM(amount) FILTER (WHERE payment_method = 'credit_card') AS credit_card_revenue,
  SUM(amount) FILTER (WHERE payment_method = 'paypal') AS paypal_revenue
FROM orders;
```

**Result:**
| total_revenue | credit_card_revenue | paypal_revenue |
|----------------|----------------------|----------------|
| 10000          | 8000                 | 2000           |

### **Why This is Awesome**
✅ **Single query** – No round-trips.
✅ **Database optimizes it** – The query planner knows to process this efficiently.
✅ **Readable** – The intent is clear.
✅ **Works with any aggregate** – `COUNT`, `AVG`, `MIN`, `MAX`, etc.

---

## **Solution 2: `CASE WHEN` Emulation (For Non-PostgreSQL Databases)**

If you’re using **MySQL, SQLite, SQL Server, or Oracle**, you don’t have `FILTER`. But you can **emulate** the same behavior using `CASE WHEN` inside aggregations.

### **How It Works**
Instead of filtering *after* aggregation, we `CASE WHEN` to include or exclude values *before* the aggregate function applies.

### **Example: Revenue by Payment Method (MySQL)**
```sql
SELECT
  SUM(amount) AS total_revenue,
  SUM(CASE WHEN payment_method = 'credit_card' THEN amount ELSE 0 END) AS credit_card_revenue,
  SUM(CASE WHEN payment_method = 'paypal' THEN amount ELSE 0 END) AS paypal_revenue
FROM orders;
```

**Result:** Same as above!

### **Pros and Cons**
✅ **Works everywhere** – No `FILTER` needed.
❌ **Slightly less readable** – Requires more keywords.
❌ **No real filtering** – The database still processes all rows.

---
## **Implementation Guide: When and How to Use This Pattern**

### **When to Use Conditional Aggregates**
| Scenario                          | Tool to Use               |
|-----------------------------------|---------------------------|
| PostgreSQL user                   | `FILTER` clause           |
| MySQL, SQLite, SQL Server         | `CASE WHEN` emulation     |
| Need simple breakdowns            | Both                      |
| Complex business rules             | `CASE WHEN` (more flexible)|
| High-performance reporting        | `FILTER` (best optimized) |

### **Step-by-Step: Applying to a Real Example**

**Problem:** We have a `products` table with `price` and `category`, and we want to calculate:

- Total revenue
- Revenue from electronics
- Revenue from books

**Solution:**
```sql
-- PostgreSQL (FILTER)
SELECT
  SUM(price) AS total_revenue,
  SUM(price) FILTER (WHERE category = 'electronics') AS electronics_revenue,
  SUM(price) FILTER (WHERE category = 'books') AS books_revenue
FROM products;

-- MySQL/SQLite (CASE WHEN)
SELECT
  SUM(price) AS total_revenue,
  SUM(CASE WHEN category = 'electronics' THEN price ELSE 0 END) AS electronics_revenue,
  SUM(CASE WHEN category = 'books' THEN price ELSE 0 END) AS books_revenue
FROM products;
```

### **Multiple Conditions in One Query**
You can even calculate **multiple filtered aggregates at once**:

```sql
-- PostgreSQL: Count orders by payment method and status
SELECT
  COUNT(*) AS total_orders,
  COUNT(*) FILTER (WHERE payment_method = 'credit_card') AS credit_card_orders,
  COUNT(*) FILTER (WHERE status = 'shipped') AS shipped_orders,
  COUNT(*) FILTER (WHERE payment_method = 'credit_card' AND status = 'shipped') AS cc_shipped_orders
FROM orders;
```

---
## **Common Mistakes to Avoid**

### **1. Overcomplicating with `CASE WHEN`**
❌ **Don’t do this:**
```sql
SUM(CASE WHEN category = 'electronics' THEN price ELSE NULL END)  -- Wrong!
```
✅ **Do this instead:**
```sql
SUM(CASE WHEN category = 'electronics' THEN price ELSE 0 END)  -- Correct!
```
**Why?** `NULL` values are ignored in aggregates, so this doesn’t work. Always use `0` or another default.

### **2. Forgetting NULL Values**
If your data has `NULL` values, they’ll be excluded by default. If you need to include them, adjust:

❌ **Excludes NULLs:**
```sql
SUM(price) FILTER (WHERE price IS NOT NULL)
```
✅ **Includes NULLs (if needed):**
```sql
SUM(CASE WHEN price IS NULL THEN 0 ELSE price END)
```

### **3. Mixing `FILTER` with `GROUP BY`**
If you `GROUP BY` and use `FILTER`, the filter applies *per group*, not the whole table:

```sql
-- Correct: Filters per group
SELECT
  category,
  SUM(price),
  SUM(price) FILTER (WHERE payment_method = 'credit_card')
FROM products
GROUP BY category;
```

❌ **Avoid this confusion:**
```sql
-- Wrong: Filter applies to entire table, not per group
SELECT
  category,
  SUM(price),
  SUM(price) FILTER (WHERE category = 'electronics')  -- Redundant!
FROM products
GROUP BY category;
```

### **4. Assuming `FILTER` Works Everywhere**
If you write a query using `FILTER` but deploy it to MySQL, it’ll fail. Always check your database dialect!

---
## **Key Takeaways (TL;DR)**
✔ **Conditional aggregates** let you calculate multiple filtered aggregates in **one query**.
✔ **PostgreSQL’s `FILTER` clause** is the cleanest and most efficient solution.
✔ **`CASE WHEN` emulation** works in other databases but is slightly less performant.
✔ **Avoid multiple queries, `UNION`, or app-side filtering**—they’re slower and harder to maintain.
✔ **Use `FILTER` for simple breakdowns** and `CASE WHEN` for complex logic.
✔ **Watch out for NULLs**—they behave differently in aggregates.
✔ **Test your queries**—some databases optimize better than others.

---
## **Conclusion: Write Fewer Queries, Get Better Performance**

Conditional aggregates are a **powerful tool** in your SQL toolkit. They:
- **Reduce database round-trips** (faster responses).
- **Simplify complex breakdowns** (cleaner code).
- **Let the database do the heavy lifting** (better optimization).

Next time you need to calculate **total X, filtered X, and segmented X**, reach for `FILTER` (PostgreSQL) or `CASE WHEN` (elsewhere). Your queries—and your users—will thank you.

### **Try It Yourself!**
1. Create a sample `orders` table:
   ```sql
   CREATE TABLE orders (
     id SERIAL PRIMARY KEY,
     amount DECIMAL(10, 2),
     payment_method VARCHAR(20),
     status VARCHAR(20)
   );

   INSERT INTO orders (amount, payment_method, status)
   VALUES
     (100.00, 'credit_card', 'shipped'),
     (50.00, 'paypal', 'shipping'),
     (200.00, 'credit_card', 'shipped');
   ```
2. Run a conditional aggregate query and see the magic!

---
### **Further Reading**
- [PostgreSQL FILTER Documentation](https://www.postgresql.org/docs/current/sql-expressions.html#SQL-FILTER)
- [MySQL CASE WHEN Guide](https://dev.mysql.com/doc/refman/8.0/en/case.html)
- [SQL Performance Tuning with Aggregates](https://use.thecode.coach/sql-performance/aggregates.html)

---

**What’s your favorite way to handle filtered aggregates? Drop a comment and let me know!** 🚀**
```