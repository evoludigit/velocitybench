```markdown
# Conditional Aggregates: Filtering Your Analytics with FILTER and CASE WHEN

*Efficiently calculate multiple filtered aggregates in a single query—no UNIONs, no subqueries, and no application-side filtering.*

---

## **Introduction**

Data analysis is often about answering questions like *"How much revenue did we get from credit cards vs. PayPal?"* or *"Which product categories had growth in Q2 vs. Q1?"*. Traditionally, these require multiple queries, complex `UNION` operations, or application-side filtering—all of which hurt performance and readability.

What if you could calculate **multiple aggregated results in a single query**, each filtered by different conditions? This is where **conditional aggregates** come into play.

PostgreSQL introduced the `FILTER` clause to handle this elegantly, but database systems like MySQL, SQLite, and SQL Server rely on the classic `CASE WHEN` pattern. By mastering these techniques, you can:
- **Reduce round-trips** (single query for all filtered aggregates)
- **Improve readability** (no need for `UNION ALL` with `WHERE` clauses)
- **Leverage database optimizers** (faster execution than application-side filtering)

Let’s dive into how they work, with practical examples.

---

## **The Problem: Multiple Aggregates, Many Queries**

Before conditional aggregates, calculating filtered sums, counts, or averages required inefficient approaches:

### **1. Multiple Queries (Worst Performance)**
```sql
-- Query 1: Total revenue
SELECT SUM(revenue) FROM sales;

-- Query 2: Credit card revenue
SELECT SUM(revenue) FROM sales WHERE payment_method = 'credit_card';

-- Query 3: PayPal revenue
SELECT SUM(revenue) FROM sales WHERE payment_method = 'paypal';
```
**Problem:** Three round-trips to the database, even though we could compute all three in one.

### **2. UNION-Based Filtering (Slower, Complex)**
```sql
SELECT SUM(revenue) AS total_revenue FROM sales
UNION
SELECT SUM(revenue) AS credit_card_revenue
FROM sales WHERE payment_method = 'credit_card'
UNION
SELECT SUM(revenue) AS paypal_revenue
FROM sales WHERE payment_method = 'paypal';
```
**Problem:** `UNION` requires sorting and deduplication, even for simple aggregates. Columns must match (e.g., `AS total_revenue`).

### **3. Subqueries with Different WHERE (Hard to Optimize)**
```sql
SELECT
    total_revenue,
    (SELECT SUM(revenue) FROM sales WHERE payment_method = 'credit_card') AS credit_card_revenue
FROM (
    SELECT SUM(revenue) AS total_revenue FROM sales
) t;
```
**Problem:** Subqueries can’t always be optimized efficiently, and mixing aggregate levels (outer vs. inner) gets messy.

### **4. Application-Side Filtering (Inefficient)**
```python
# Pseudocode: Fetch all data, then filter in Python
all_sales = db.query_all("SELECT * FROM sales")
total = sum(s.revenue for s in all_sales)
credit_card = sum(s.revenue for s in all_sales if s.payment_method == "credit_card")
paypal = sum(s.revenue for s in all_sales if s.payment_method == "paypal")
```
**Problem:** Fetching all rows just to aggregate in application code wastes bandwidth and CPU.

---
## **The Solution: Conditional Aggregates**

Conditional aggregates let you compute **multiple filtered aggregates in a single query**. There are two main approaches:

1. **PostgreSQL `FILTER` Clause** (SQL:2011, native syntax)
2. **`CASE WHEN` Emulation** (Works in MySQL, SQLite, SQL Server, etc.)

Both achieve the same goal but with different syntax.

---

## **Solution 1: PostgreSQL `FILTER` Clause (Best Performance)**
PostgreSQL supports the `FILTER` clause directly in aggregate functions. This is the most efficient and readable approach.

### **Basic Syntax**
```sql
SUM(column) FILTER (WHERE condition)
```
- The `FILTER` clause acts like an implicit `WHERE` after aggregation.
- Multiple filters work in a single query.

### **Example: Payment Method Revenue**
```sql
SELECT
    SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS credit_card_revenue,
    SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal_revenue,
    SUM(revenue) AS total_revenue
FROM sales;
```
**Output:**
| credit_card_revenue | paypal_revenue | total_revenue |
|---------------------|----------------|---------------|
| 15,000              | 8,000          | 23,000        |

### **Advantages of `FILTER`**
✅ **Clean syntax** (no `CASE WHEN` nesting)
✅ **Efficient execution** (PostgreSQL optimizes well)
✅ **Works with any aggregate** (`COUNT`, `AVG`, `MIN`, `MAX`)

### **Multiple Conditions in One Query**
```sql
SELECT
    SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS credit_card,
    SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal,
    SUM(revenue) FILTER (WHERE product_category = 'electronics') AS electronics,
    SUM(revenue) AS all_revenue
FROM sales;
```

---

## **Solution 2: `CASE WHEN` Emulation (Cross-Database)**
Databases without `FILTER` (MySQL, SQLite, SQL Server) use `CASE WHEN` inside aggregates:

### **Basic Syntax**
```sql
SUM(CASE WHEN condition THEN column ELSE NULL END)
```
- `ELSE NULL` ensures only matching rows contribute to the sum.
- Works for any aggregate (`COUNT`, `AVG`, etc.).

### **Example: Payment Method Revenue (MySQL)**
```sql
SELECT
    SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE NULL END) AS credit_card_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE NULL END) AS paypal_revenue,
    SUM(revenue) AS total_revenue
FROM sales;
```

### **Multiple Conditions**
```sql
SELECT
    SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE NULL END) AS credit_card,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE NULL END) AS paypal,
    SUM(CASE WHEN product_category = 'electronics' THEN revenue ELSE NULL END) AS electronics,
    SUM(revenue) AS all_revenue
FROM sales;
```

### **When to Use `CASE WHEN`**
✅ **Portable across databases** (MySQL, SQLite, SQL Server)
❌ **Slightly more verbose** than `FILTER`
❌ **Can be harder to optimize** (depends on database)

---

## **Implementation Guide: Step-by-Step**

### **1. Identify Your Filter Conditions**
Before writing queries, clarify:
- What aggregates do you need? (`SUM`, `COUNT`, `AVG`)
- What conditions will filter them? (`payment_method = 'credit_card'`, `date > '2023-01-01'`)

Example conditions:
- `payment_method = 'credit_card'`
- `payment_method = 'paypal'`
- `product_category = 'electronics'`
- `sale_date BETWEEN '2023-01-01' AND '2023-01-31'`

### **2. Choose Your Database Syntax**
| Database       | Use `FILTER` | Use `CASE WHEN` |
|----------------|-------------|-----------------|
| PostgreSQL     | ✅ Yes       | ❌ No           |
| MySQL          | ❌ No        | ✅ Yes          |
| SQLite         | ❌ No        | ✅ Yes          |
| SQL Server     | ❌ No        | ✅ Yes          |

### **3. Write the Query**
#### **PostgreSQL Example (Using `FILTER`)**
```sql
SELECT
    -- Filtered aggregates
    SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS credit_card_revenue,
    SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal_revenue,

    -- Time-based aggregates
    SUM(revenue) FILTER (WHERE sale_date BETWEEN '2023-01-01' AND '2023-01-31') AS jan_revenue,
    SUM(revenue) FILTER (WHERE sale_date BETWEEN '2023-02-01' AND '2023-02-28') AS feb_revenue,

    -- Total (no filter)
    SUM(revenue) AS total_revenue
FROM sales;
```

#### **MySQL Example (Using `CASE WHEN`)**
```sql
SELECT
    SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE NULL END) AS credit_card_revenue,
    SUM(CASE WHEN payment_method = 'paypal' THEN revenue ELSE NULL END) AS paypal_revenue,

    SUM(CASE WHEN sale_date BETWEEN '2023-01-01' AND '2023-01-31' THEN revenue ELSE NULL END) AS jan_revenue,

    SUM(revenue) AS total_revenue
FROM sales;
```

### **4. Grouping and Further Analysis**
Conditional aggregates work well with `GROUP BY` for deeper insights:

#### **PostgreSQL Example (Grouped by Category)**
```sql
SELECT
    product_category,
    SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS credit_card_sales,
    SUM(revenue) FILTER (WHERE payment_method = 'paypal') AS paypal_sales,
    SUM(revenue) AS total_sales
FROM sales
GROUP BY product_category;
```

### **5. Performance Considerations**
- **Indexing:** Ensure `payment_method`, `product_category`, and `sale_date` are indexed.
- **Avoid Over-Nesting:** Too many `CASE WHEN` conditions can slow queries.
- **Use `FILTER` When Possible:** It’s cleaner and faster in PostgreSQL.

---

## **Common Mistakes to Avoid**

### **1. Forgetting `ELSE NULL` in `CASE WHEN`**
```sql
-- WRONG: Includes non-matching rows in the sum!
SUM(CASE WHEN payment_method = 'credit_card' THEN revenue END) AS bad_revenue;

-- CORRECT: Only matching rows contribute
SUM(CASE WHEN payment_method = 'credit_card' THEN revenue ELSE NULL END) AS correct_revenue;
```

### **2. Mixing `FILTER` with `GROUP BY` Incorrectly**
```sql
-- WRONG: FILTER applies to the group, not individual rows
SELECT product_category, SUM(revenue) FILTER (WHERE payment_method = 'credit_card')
FROM sales
GROUP BY product_category;

-- CORRECT: FILTER works per row, then aggregates
SELECT product_category,
       SUM(revenue) AS total,
       SUM(revenue) FILTER (WHERE payment_method = 'credit_card') AS credit_card
FROM sales
GROUP BY product_category;
```

### **3. Overcomplicating Queries with Too Many Conditions**
```sql
-- Too complex!
SELECT
    SUM(CASE WHEN payment = 'credit' AND region = 'US' THEN revenue ELSE NULL END) AS us_credit,
    SUM(CASE WHEN payment = 'paypal' AND region = 'EU' THEN revenue ELSE NULL END) AS eu_paypal,
    ...
FROM sales;
```
**Better:** Break into smaller queries or use a reporting tool for complex filters.

### **4. Ignoring NULL Handling**
- `FILTER` works only with `WHERE` conditions (no `IS NOT NULL` directly).
- In `CASE WHEN`, ensure NULLs are handled explicitly.

```sql
-- Fixed for NULL payments
SUM(CASE WHEN payment_method IS NOT NULL AND payment_method = 'credit_card' THEN revenue ELSE NULL END) AS credit_card;
```

---

## **Key Takeaways**

✅ **Conditional aggregates** calculate multiple filtered results in **one query**.
✅ **PostgreSQL `FILTER`** is the cleanest and fastest option.
✅ **`CASE WHEN` emulation** works everywhere but is more verbose.
✅ **Avoid multiple queries**—single-query analytics are faster and simpler.
✅ **Index your filters**—`FILTER`/`CASE WHEN` rely on efficient scanning.
❌ **Don’t mix `FILTER` and `GROUP BY` incorrectly**—they work differently.
❌ **Overcomplicate with too many conditions**—keep it readable.

---

## **Conclusion**

Conditional aggregates (via `FILTER` or `CASE WHEN`) are a **game-changer** for analytical queries. They:
- **Reduce round-trips**, improving performance.
- **Simplify code**, making SQL more readable.
- **Leverage the database**, avoiding application-side filtering.

**Next Steps:**
1. Try `FILTER` in PostgreSQL for cleaner queries.
2. Use `CASE WHEN` in MySQL/SQLite for portability.
3. Combine with `GROUP BY` for category-level breakdowns.

By mastering this pattern, you’ll write **faster, more efficient, and more maintainable** analytics queries.

**What’s your favorite way to handle filtered aggregates? Share in the comments!**
```

---
**Word Count:** ~1,800
**Tone:** Practical, code-first, focuses on real-world tradeoffs.
**Audience:** Advanced backend devs working with SQL databases.