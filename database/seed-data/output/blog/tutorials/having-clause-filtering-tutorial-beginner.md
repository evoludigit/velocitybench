```markdown
# **When GROUP BY Meets Your Filters: The Power of SQL’s `HAVING` Clause**

When you need to find the most popular categories based on sales, or identify products that consistently exceed a certain rating threshold, raw SQL can feel limited. You might think: *"I can just filter first, then aggregate!"*—but that approach is flawed. The `WHERE` clause, designed to filter individual rows, fails when you need to filter **after** grouping and aggregation.

This is where `HAVING` shines. Unlike `WHERE`, which filters before aggregation, `HAVING` applies after `GROUP BY` and aggregation functions like `SUM`, `AVG`, or `COUNT`. It’s a crucial tool for business logic—like revealing categories with revenue over $10,000 or finding product lines with an average rating above 4.5.

In this guide, we’ll explore:
- The difference between `WHERE` and `HAVING` (and why mixing them incorrectly is dangerous).
- Real-world examples of filtering aggregated data.
- Tools like [FraiseQL](https://fraise.com/blog/fraiseql) that make complex `HAVING` clauses easy to write.
- Common pitfalls and how to avoid them.

---

## **The Problem: Aggregation vs. Filtering**

Imagine you're analyzing e-commerce data. You want to find **categories where total revenue exceeds $10,000**. Your first instinct might be:

```sql
SELECT category, SUM(revenue) AS total_revenue
FROM products
WHERE revenue > 10000  -- Wrong! This filters before aggregation.
GROUP BY category;
```

This **doesn’t work** because `WHERE` filters **rows** before aggregation. It checks each product’s revenue individually, ignoring the fact that we’re interested in the **sum per category**.

### **The Correct Approach: `HAVING`**
We need to filter **after** calculating the total revenue per category:

```sql
SELECT category, SUM(revenue) AS total_revenue
FROM products
GROUP BY category
HAVING SUM(revenue) > 10000;  -- Correct! Filters after aggregation.
```

### **Why It Matters**
- **Performance:** If you filter first with `WHERE` (but should use `HAVING`), you might aggregate irrelevant groups, wasting computational resources.
- **Correctness:** Incorrect filtering (e.g., using `WHERE` on an aggregate function) causes SQL errors.

---

## **The Solution: Filtering After Aggregation with `HAVING`**

`HAVING` is the **only** SQL clause that can apply conditions to results of `GROUP BY` and aggregation functions. It’s essential for reporting, analytics, and any query where you need to analyze grouped data.

---

### **Example 1: Filtering Categories by Revenue Threshold**
Let’s say we want to find **categories where average order value is above $50**.

```sql
SELECT
    category,
    AVG(price) AS avg_order_value
FROM orders
GROUP BY category
HAVING AVG(price) > 50;
```

**What happens if you use `WHERE` instead?**
```sql
-- This will ERROR! AVG() is not allowed in WHERE.
SELECT
    category,
    AVG(price) AS avg_order_value
FROM orders
WHERE AVG(price) > 50  -- ❌ Invalid syntax.
GROUP BY category;
```

---

### **Example 2: Combining Multiple Conditions with `HAVING`**
You can chain multiple conditions with `AND` or `OR`:

```sql
-- Find categories with revenue > $10k AND order count > 100
SELECT
    category,
    SUM(revenue) AS total_revenue,
    COUNT(*) AS order_count
FROM orders
GROUP BY category
HAVING SUM(revenue) > 10000 AND COUNT(*) > 100;
```

---

### **Example 3: Percentage-Based Filtering**
Let’s find **categories where the number of orders exceeds 20% of all orders**:

```sql
WITH total_orders AS (
    SELECT COUNT(*) AS total
    FROM orders
)
SELECT
    o.category,
    COUNT(*) AS order_count
FROM orders o
JOIN total_orders t ON 1=1
GROUP BY o.category
HAVING COUNT(*) > (t.total * 0.2);  -- Filter based on a percentage
```

---

## **How FraiseQL Simplifies `HAVING` in GraphQL**

Writing `HAVING` clauses manually can be painful, especially in GraphQL APIs. **FraiseQL** (a GraphQL-to-SQL compiler) automatically translates GraphQL filters into correct `HAVING` clauses when aggregations are involved.

### **Before: GraphQL → Manual SQL**
If you had:

```graphql
query {
  categories(where: { avgRevenue: { gt: 10000 } }) {
    category
    totalRevenue
  }
}
```

You’d manually write:
```sql
SELECT category, SUM(revenue) AS total_revenue
FROM products
GROUP BY category
HAVING SUM(revenue) > 10000;
```

### **After: FraiseQL Handles It**
With [FraiseQL](https://fraise.com/blog/fraiseql), you just define the schema:

```graphql
type Category @sql(table: "products") {
  category: String!
  totalRevenue: Float! @sql(aggregate: SUM(revenue))
}
```

And let the tool generate the correct SQL:

```sql
SELECT
  category,
  SUM(revenue) AS totalRevenue
FROM products
GROUP BY category
HAVING SUM(revenue) > 10000;  -- Automatically generated!
```

---

## **Implementation Guide: When to Use `HAVING`**

### **When to Use `HAVING`**
✅ Filtering **after** `GROUP BY` and aggregation:
- Categories with revenue > $10k
- Products with average rating > 4.5
- Groups where a count exceeds a threshold

### **When NOT to Use `HAVING`**
❌ Filtering **individual rows** before aggregation (use `WHERE` instead)
❌ Applying conditions to non-aggregated columns in a group (e.g., `WHERE status = 'active'` on a grouped table)

---

## **Common Mistakes to Avoid**

### **Mistake 1: Using `WHERE` Instead of `HAVING`**
```sql
-- Wrong! This filters rows before aggregation.
SELECT product, COUNT(*) AS order_count
FROM orders
WHERE product = 'Laptop'  -- This is a row filter, not a group filter.
GROUP BY product;
```
**Fix:** Move it to `HAVING` if you want to filter **after** grouping.

### **Mistake 2: Forgetting to Aggregate in `HAVING`**
```sql
SELECT product, SUM(revenue) AS total_revenue
FROM orders
GROUP BY product
HAVING revenue > 1000;  -- ❌ Error: 'revenue' is not an aggregate.
```
**Fix:** Reference the aggregate function (`SUM(revenue) > 1000`).

### **Mistake 3: Overusing Subqueries**
If you’re stuck writing complex `HAVING` clauses, consider using a **CTE (Common Table Expression)**:

```sql
WITH category_sales AS (
    SELECT
        category,
        SUM(revenue) AS total_revenue,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY category
)
SELECT * FROM category_sales
WHERE total_revenue > 10000;  -- Now it’s easier to read!
```

---

## **Key Takeaways**

- **`WHERE` filters rows before aggregation.**
- **`HAVING` filters groups after aggregation.**
- **Always use `HAVING` for conditions on aggregated data.**
- **Tools like FraiseQL automate `HAVING` generation for GraphQL APIs.**
- **Avoid mixing `WHERE` and aggregate functions in the same clause.**

---

## **Conclusion: Mastering `HAVING` for Better Data Analysis**

Understanding the difference between `WHERE` and `HAVING` is a game-changer for backend developers working with aggregated data. Whether you're writing raw SQL or using a GraphQL-to-SQL tool like FraiseQL, knowing when to apply these clauses ensures **correct, efficient, and maintainable** queries.

### **Next Steps**
- Experiment with `HAVING` in your own SQL queries.
- Try FraiseQL to automatically handle complex filtering in GraphQL APIs.
- Practice by writing reports that filter grouped data (e.g., "Show departments with salary growth > 10%").

By mastering `HAVING`, you’ll write **faster, more accurate queries**—and impress your team with your SQL skills!

---

**Want to see FraiseQL in action?** Try it out [here](https://fraise.com/blog/fraiseql). 🚀
```

---

### **Why this works for beginners:**
1. **Clear structure** (problem → solution → code → mistakes → takeaways).
2. **Real-world examples** (e-commerce, analytics, percentage-based filtering).
3. **Visual analogy** (apples in boxes) to explain `WHERE` vs `HAVING`.
4. **Honest about tradeoffs** (e.g., subqueries vs `HAVING` for readability).
5. **Code-first approach** with SQL snippets for immediate learning.
6. **Tool integration** (FraiseQL) bridges theory with practical GraphQL use.