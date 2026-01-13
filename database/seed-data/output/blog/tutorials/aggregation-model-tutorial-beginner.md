```markdown
# FraiseQL Aggregation Model: How to Move Aggregations from Apps to Databases

## Introduction

Imagine running a small e-commerce business. You’re tracking sales every minute—products sold, revenue, customer data—all stored in a PostgreSQL database. Now you want to know:

- *"What’s my monthly revenue breakdown by product category?"*
- *"Which customers spend the most on average?"*
- *"How many orders were placed last month?"*

If you calculate these in your application code, you’ll fetch every single sale, send it over the network to the server, sort through it all in memory, and then perform the math. This is slow, expensive, and inefficient. That’s where FraiseQL’s **Aggregation Model** comes in.

In this post, we’ll explore how FraiseQL compiles GraphQL aggregate queries into optimized SQL aggregations and executes them directly in the database. You’ll learn how to move heavy lifting from your application to PostgreSQL, drastically improving performance, reducing costs, and unleashing the power of your database’s query optimizer.

---

## The Problem: Why Application-Side Aggregations Are a Nightmare

Aggregation is a common operation in APIs. Whether you’re calculating totals, averages, or breakdowns by category, your application needs to:

1. **Fetch all data** (e.g., all sales records for a month).
2. **Transmit it over the network** (which costs money if your database isn’t local).
3. **Sort and group in memory** (consume significant CPU and RAM).
4. **Calculate aggregates** (SUM, AVG, etc.) in code (slow for large datasets).

Here’s an example: calculating monthly revenue by product category.

### The Slow Way (Application-Side Aggregation)

```python
# Python example: slow, inefficient aggregation
def calculate_monthly_revenue_by_category(db_cursor):
    # Step 1: Fetch all sales for the month
    sales = db_cursor.execute("""
        SELECT product_id, category, amount
        FROM sales
        WHERE date BETWEEN '2023-01-01' AND '2023-01-31'
    """).fetchall()

    # Step 2: Group and aggregate in memory
    revenue_by_category = {}
    for sale in sales:
        category = sale['category']
        revenue_by_category[category] = revenue_by_category.get(category, 0) + sale['amount']

    return revenue_by_category
```

### Why This Sucks

| Issue          | Impact                                                                 |
|----------------|-------------------------------------------------------------------------|
| **Network cost** | Transferring 100,000+ rows over HTTP wastes bandwidth and money.       |
| **Scalability** | If sales grow, your app crashes from memory overload.                   |
| **Latency**     | More work means slower response times for users.                         |
| **Cost**       | Databases charge by query execution, not data transfer.                 |
| **Optimizer miss** | Your app can’t leverage PostgreSQL’s query planner or indexes.       |

FraiseQL solves this by pushing aggregations to the database, where they execute in **milliseconds** instead of **seconds**.

---

## The Solution: Server-Side Aggregations with FraiseQL

FraiseQL’s **Aggregation Model** compiles GraphQL queries like this:

```graphql
query {
  monthlyRevenueByCategory {
    category
    totalRevenue
  }
}
```

Into optimized PostgreSQL SQL like this:

```sql
SELECT
  category,
  SUM(amount) AS total_revenue
FROM sales
WHERE date BETWEEN '2023-01-01' AND '2023-01-31'
GROUP BY category
HAVING SUM(amount) > 0
```

### Key Features of FraiseQL Aggregations

| Feature                     | Example                                              | Benefit                          |
|-----------------------------|------------------------------------------------------|----------------------------------|
| **Native SQL Aggregates**   | `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `STDDEV`        | Leverages PostgreSQL’s optimized functions. |
| **JSONB Grouping**          | `data->>'field' AS category`                        | Flexible grouping on nested data. |
| **HAVING Clause**           | `HAVING SUM(amount) > 1000`                         | Filter aggregates post-grouping. |
| **Temporal Bucketing**      | `DATE_TRUNC('month', sale_date)`                    | Group by time periods efficiently. |
| **No Joins Required**       | Dimensions must be denormalized into JSONB at ETL.  | Simplifies complex joins.         |

---

## Implementation Guide: How to Build FraiseQL Aggregations

### Step 1: Schema Design – Denormalize Dimensions into JSONB

FraiseQL requires **dimensions** (like `category` or `customer_id`) to be stored as **JSONB** in the table. This allows flexible grouping without joins.

#### Example Table Structure

```sql
CREATE TABLE sales (
    id SERIAL PRIMARY KEY,
    amount DECIMAL(10, 2),
    sale_date TIMESTAMP,
    product_id INTEGER,
    category JSONB,          -- {"category": "Electronics", ...}
    customer_id INTEGER,
    metadata JSONB           -- Additional attributes for grouping
);
```

Insert data with dimensions as JSONB:

```sql
INSERT INTO sales (amount, sale_date, category, customer_id)
VALUES
    (199.99, '2023-01-15', '{"category": "Electronics", "subcategory": "Headphones"}', 42),
    (49.99,  '2023-01-16', '{"category": "Fashion", "subcategory": "T-Shirts"}', 101);
```

### Step 2: Write PostgreSQL Aggregations

Now define your aggregations in SQL:

```sql
-- Query: Revenue by category (monthly)
SELECT
  category->>'category' AS category,
  SUM(amount) AS total_revenue,
  COUNT(*) AS transaction_count
FROM sales
WHERE sale_date >= '2023-01-01'
  AND sale_date < '2023-02-01'
GROUP BY category->>'category'
HAVING SUM(amount) > 2000
ORDER BY total_revenue DESC;
```

**Output**:
```
category    | total_revenue | transaction_count
------------|---------------|-------------------
Electronics | 4000.00       | 20
Fashion     | 2500.00       | 50
```

### Step 3: Expose via GraphQL

Connect your GraphQL layer to PostgreSQL. FraiseQL automatically translates GraphQL aggregate queries to SQL:

```graphql
query {
  revenueByCategory(month: "2023-01") {
    category
    totalRevenue
    transactionCount
  }
}
```

### Step 4: Handle Temporal Aggregations

FraiseQL supports **time-series grouping** with PostgreSQL’s date functions:

```sql
-- Breakdown by week
SELECT
  DATE_TRUNC('week', sale_date) AS week_start,
  SUM(amount) AS weekly_revenue
FROM sales
WHERE sale_date >= '2023-01-01'
GROUP BY week_start
ORDER BY week_start;
```

### Step 5: Advanced Aggregations

Use **PostgreSQL’s advanced functions** for deeper insights:

```sql
-- Calculate average order value by customer segment
SELECT
  customer_id,
  AVG(amount) AS avg_order_value,
  STDDEV(amount) AS order_value_stddev
FROM sales
GROUP BY customer_id
HAVING STDDEV(amount) > 100
ORDER BY avg_order_value DESC;
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Forgetting to Denormalize Dimensions into JSONB
**Problem**: FraiseQL requires dimensions to be stored as JSONB for flexible grouping.

**Fix**: Always design your schema with dimensions in JSONB format. Example:
```sql
-- Bad: Spread dimensions across columns
CREATE TABLE sales (
    product_id INTEGER,
    product_name TEXT,  -- Not JSONB
    product_category TEXT
);

-- Good: Use JSONB for dimensions
CREATE TABLE sales (
    product_attrs JSONB  -- {"id": 100, "name": "T-Shirt", "category": "Fashion"}
);
```

### ❌ Mistake 2: Overusing JOINs
**Problem**: FraiseQL avoids joins for aggregation. If you join tables, you lose the performance benefits.

**Fix**: Denormalize dimensions at ETL time. Example:
```sql
-- Bad: Join sales with products
SELECT s.category, SUM(s.amount)
FROM sales s
JOIN products p ON s.product_id = p.id
GROUP BY p.category;

-- Good: Store category as JSONB in sales
SELECT category->>'category', SUM(amount)
FROM sales
GROUP BY category->>'category';
```

### ❌ Mistake 3: Ignoring HAVING Filters
**Problem**: Applying filters *before* grouping (`WHERE`) can lead to incorrect aggregates.

**Fix**: Use `HAVING` for post-aggregation filters. Example:
```sql
-- Bad: Filter before grouping (wrong logic)
SELECT category, SUM(amount)
FROM sales
WHERE SUM(amount) > 1000  -- ❌ This doesn’t work!
GROUP BY category;

-- Good: Use HAVING
SELECT category, SUM(amount)
FROM sales
GROUP BY category
HAVING SUM(amount) > 1000;  -- ✅ Correct
```

### ❌ Mistake 4: Not Using Indexes for JSONB Fields
**Problem**: Fast aggregations require indexes on JSONB dimensions.

**Fix**: Create GIN indexes for JSONB fields:
```sql
CREATE INDEX idx_sales_category ON sales USING GIN (category jsonb_path_ops);
```

### ❌ Mistake 5: Forgetting to Handle NULLs
**Problem**: `NULL` values in JSONB fields (`{"category": null}`) cause grouping errors.

**Fix**: Explicitly filter `NULL` values:
```sql
SELECT category->>'category', SUM(amount)
FROM sales
WHERE category->>'category' IS NOT NULL
GROUP BY category->>'category';
```

---

## Key Takeaways

✅ **Move aggregations to the database** – Never calculate `SUM`/`AVG` in your app.
✅ **Denormalize dimensions into JSONB** – Avoid joins for better performance.
✅ **Leverage PostgreSQL’s `GROUP BY` + `HAVING`** – Use native SQL for optimal queries.
✅ **Bucket time efficiently** – Use `DATE_TRUNC` for daily/weekly/monthly aggregation.
✅ **Index JSONB fields** – GIN indexes speed up grouping and filtering.
✅ **Use `HAVING` for post-aggregation filters** – Filters like `SUM(amount) > 1000` belong here.
✅ **Avoid joins for aggregation** – Denormalize at ETL time for simplicity.

---

## Conclusion

FraiseQL’s **Aggregation Model** is a game-changer for performance-sensitive applications. By compiling GraphQL aggregates into optimized PostgreSQL SQL, you:

🚀 **Reduce latency** – Aggregations run in **milliseconds** instead of seconds.
💰 **Lower costs** – No more transferring terabytes of data over the network.
🔧 **Simplify joins** – Use JSONB for flexible grouping without complex SQL.
📊 **Unlock deeper insights** – Leverage PostgreSQL’s advanced functions (`STDDEV`, `PERCENTILE`).

### Next Steps

1. **Try it yourself**: Denormalize your dimensions into JSONB and rewrite your aggregates in SQL.
2. **Experiment with temporal grouping**: Use `DATE_TRUNC` for time-series analysis.
3. **Optimize**: Add GIN indexes to speed up JSONB queries.
4. **Extend**: Explore PostgreSQL’s advanced aggregates like `PERCENTILE_CONT`.

Aggregations don’t have to be slow or expensive. With FraiseQL, you can offload the heavy lifting to your database and focus on building great applications.

---
**What’s your biggest aggregation challenge?** Share in the comments—I’d love to hear how you solve it!
```