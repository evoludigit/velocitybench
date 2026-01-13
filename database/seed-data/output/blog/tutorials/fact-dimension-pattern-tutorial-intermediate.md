```markdown
# **Fact-Dimension Pattern in FraiseQL: Denormalized Speed for Analytics Queries**

*By [Your Name]*

---

## **Introduction**

In the world of analytics, we often face a tradeoff: **flexibility vs. performance**. Traditional star schemas with fact and dimension tables work well for relational integrity but struggle with performance at scale. Join-heavy queries become bottlenecks as datasets grow, and even small changes to dimensional data require costly CASCADE updates.

Enter **FraiseQL’s fact-dimension pattern**—a denormalized approach that stores numeric measures as SQL columns (for 10-100x faster aggregation) while keeping flexible grouping attributes in a **JSONB column**. This pattern eliminates expensive joins, allowing instant aggregation on millions of records without the overhead of query planners.

This blog post dives into:
- Why traditional fact-dimension schemas fail at scale
- How FraiseQL’s denormalized approach solves performance problems
- Practical implementation examples
- Common pitfalls and best practices

---

## **The Problem: Why Star Schemas Struggle**

Consider a typical e-commerce analytics system tracking `orders`, `products`, and `customers`. A star schema might look like this:

```sql
-- Fact table (orders)
CREATE TABLE orders_fact (
    order_id UUID PRIMARY KEY,
    order_date TIMESTAMP,
    revenue DECIMAL(10, 2),
    quantity INT,
    -- Joins here...
    product_category_id VARCHAR(255),
    customer_country VARCHAR(100)
);

-- Dimension tables
CREATE TABLE products_dimension (
    id VARCHAR(255) PRIMARY KEY,
    name TEXT,
    category VARCHAR(255),
    price DECIMAL(10, 2)
);

CREATE TABLE customers_dimension (
    id VARCHAR(255) PRIMARY KEY,
    name TEXT,
    country VARCHAR(100)
);
```

### **Performance Issues**
1. **Join Overhead**
   Aggregating `SUM(revenue) BY product_category` requires:
   ```sql
   SELECT pd.category, SUM(off.revenue)
   FROM orders_fact off
   JOIN products_dimension pd ON off.product_category_id = pd.id
   GROUP BY pd.category;
   ```
   As data grows, the join becomes costly.

2. **Query Optimizer Chaos**
   Complex joins (e.g., `orders`, `products`, `customers`) force the planner to evaluate multiple potential execution paths, leading to slow execution.

3. **Data Consistency Hell**
   If `products_dimension.category` changes, all fact tables must update—CASCADE rules are error-prone.

4. **JSONB Aggregation is Slow**
   Storing dimensions in JSONB (e.g., `{ "product": { "category": "Electronics" } }`) means aggregating requires JavaScript-style filtering:
   ```sql
   SELECT JSONB_ARRAY_ELEMENTS(TO_JSONB(dimensions) ->> 'product' ->> 'category') AS category
   FROM orders_fact;
   ```
   This is **orders of magnitude slower** than native SQL aggregation.

---

## **The Solution: FraiseQL’s Denormalized Fact Pattern**

FraiseQL inverts the traditional approach:
- **Measures** stay as **SQL columns** (for fast aggregation).
- **Dimensions** are **denormalized into a JSONB column** (for flexibility).
- **Filter columns** (e.g., `product_category_id`) are **indexed SQL fields** (for fast filtering).

### **Schema Example**
```sql
CREATE TABLE orders_fact (
    id BIGSERIAL PRIMARY KEY,
    order_time TIMESTAMP NOT NULL,
    revenue DECIMAL(10, 2) NOT NULL, -- Measure
    quantity INT NOT NULL,             -- Measure
    -- Denormalized dimensions
    dimensions JSONB NOT NULL,
    -- Filter columns (indexed for fast WHERE)
    product_category_id VARCHAR(255) NOT NULL,
    customer_country VARCHAR(100) NOT NULL
);

-- Indexes for filtering
CREATE INDEX idx_orders_fact_product_category ON orders_fact(product_category_id);
CREATE INDEX idx_orders_fact_customer_country ON orders_fact(customer_country);
```

### **Why This Works**
1. **No Joins**: All dimensional data is preflattened into `dimensions` at ETL.
2. **Fast Aggregation**: `SUM(revenue)` is native Postgres—no JSON parsing.
3. **Flexible Grouping**: `dimensions ->> 'product' ->> 'category'` allows dynamic grouping.
4. **Scalable Filtering**: Filtering on `product_category_id` is fast due to indexing.

---

## **Implementation Guide**

### **Step 1: Define Your Measures & Dimensions**
Measures must be **numeric** (for aggregation), while dimensions are **flexible attributes**.

```sql
-- Example: Sales analytics
CREATE TABLE sales_fact (
    id BIGSERIAL PRIMARY KEY,
    sale_time TIMESTAMP NOT NULL,
    transaction_amount DECIMAL(10, 2) NOT NULL, -- Measure
    units_sold INT NOT NULL,                      -- Measure
    dimensions JSONB NOT NULL,
    product_uuid VARCHAR(255) NOT NULL,           -- Filter column
    region VARCHAR(100) NOT NULL                  -- Filter column
);
```

### **Step 2: Populate with Denormalized Data**
At ETL time, flatten dimensions into JSONB. Example:

```sql
-- Sample data (simplified)
INSERT INTO sales_fact (
    sale_time, transaction_amount, units_sold, dimensions, product_uuid, region
) VALUES (
    '2023-01-01 10:00:00',
    99.99,
    2,
    '{
        "product": {
            "name": "Laptop",
            "category": "Electronics",
            "brand": "Dell"
        },
        "sale_channel": "web"
    }'::jsonb,
    '123e4567-e89b-12d3-a456-426614174000',
    'North America'
);
```

### **Step 3: Write Fast Aggregation Queries**
#### **Option 1: Exact Grouping (Predefined)**
```sql
-- Sum by product category (fast due to indexed filter column)
SELECT
    product_uuid,
    SUM(transaction_amount) AS total_spend
FROM sales_fact
WHERE product_category_id = 'Electronics'
GROUP BY product_uuid;
```

#### **Option 2: Dynamic Grouping (JSONB)**
```sql
-- Flexible grouping (slower but flexible)
SELECT
    (dimensions ->> 'product' ->> 'category') AS category,
    SUM(transaction_amount) AS total_spend
FROM sales_fact
GROUP BY (dimensions ->> 'product' ->> 'category');
```

### **Step 4: Optimize with Indexes**
```sql
-- Index for fast filtering
CREATE INDEX idx_sales_fact_region ON sales_fact(region);

-- Partial index for common queries
CREATE INDEX idx_sales_fact_high_value ON sales_fact(transaction_amount)
WHERE (transaction_amount > 1000);
```

---

## **Common Mistakes to Avoid**

1. **Not Indexing Filter Columns**
   Without indexes on `product_uuid` or `region`, `WHERE` clauses perform like a linear scan.
   **Fix**: Always index foreign-key-like columns.

2. **Overusing JSONB for Measures**
   Storing `transaction_amount` in JSONB slows down aggregation.
   **Fix**: Keep measures as native SQL types.

3. **Ignoring Schema Evolution**
   If dimensions change (e.g., adding a `subcategory`), ensure ETL updates the JSONB structure.
   **Fix**: Use migrations or script versioning.

4. **No Partitioning for Time-series Data**
   Large fact tables slow down queries. Partition by date:
   ```sql
   CREATE TABLE sales_fact (
       -- columns...
   ) PARTITION BY RANGE (sale_time);
   ```

5. **Over-Denormalizing**
   If a dimension is frequently queried (e.g., `customer_country`), denormalize it as a column, not JSONB.

---

## **Key Takeaways**

✅ **Eliminate joins** by denormalizing dimensions at ETL.
✅ **Use JSONB for flexibility**, but keep measures as SQL columns.
✅ **Index filter columns** (e.g., `product_uuid`) for fast WHERE clauses.
✅ **Partition large tables** by time or ID range.
✅ **Avoid mixing JSONB with measures**—that defeats the purpose.

---

## **Conclusion**

The **fact-dimension pattern in FraiseQL** is a powerful alternative to traditional star schemas, trading relational integrity for raw performance. By denormalizing dimensions into JSONB and keeping measures as native SQL columns, you unlock:
- **10-100x faster aggregations** (no JSON parsing overhead).
- **Simple ETL** (no join maintenance).
- **Flexible grouping** (adapt to new query needs without schema changes).

### **When to Use This Pattern?**
- **Analytics workloads** where aggregation speed > data consistency.
- **Event-based data** (logs, clicks) where schema changes frequently.
- **Systems where joins are a bottleneck**.

### **When to Avoid?**
- **Transactional systems** with strong referential integrity needs.
- **Small datasets** where join overhead is negligible.

For teams optimizing analytics pipelines, this pattern is a game-changer. Start small—denormalize a critical fact table—and measure the performance gains!

---
*Need more details? Check out [Fraise’s documentation](https://fraise.dev) or [our GitHub examples](https://github.com/fraise-ai/fraise).*

---
**What’s your biggest analytics bottleneck?** Share in the comments—let’s discuss!
```