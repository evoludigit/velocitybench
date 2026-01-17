# **[Pattern] HAVING Clause for Post-Aggregation Filtering – Reference Guide**

---

## **Overview**
The **HAVING clause** enables filtering aggregated data *after* grouping, distinguishing it from `WHERE`, which filters rows *before* aggregation. In FraiseQL, `HAVING` transforms GraphQL arguments (e.g., `having: { revenue_gte: 10000 }`) into SQL `HAVING` clauses, supporting complex post-aggregation conditions like:
- *"Show sales categories with average revenue > $10k."*
- *"List products where (avg_rating > 4.5) AND (total_units_sold > 100)."*

This pattern bridges GraphQL’s declarative syntax with SQL’s aggregation capabilities, ensuring efficient data retrieval at the database level.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                                                                                                                                 | **SQL Equivalent**                          | **GraphQL Equivalent**                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|---------------------------------------------|
| **HAVING Clause**           | Filters group results after `GROUP BY` and aggregation (e.g., `SUM`, `AVG`, `COUNT`).                                                                                                                        | `HAVING <condition>`                        | `having: { <filter> }`                     |
| **Aggregate Function**      | SQL functions like `SUM()`, `AVG()`, `COUNT()` applied to grouped rows.                                                                                                                                              | `SUM(column)`, `AVG(column)`, `COUNT(*)`    | `-- Auto-derived from GraphQL aggregations`|
| **Comparison Operator**     | Filters aggregates against thresholds (e.g., `>`, `<=`, `BETWEEN`).                                                                                                                                                     | `>`, `<`, `>=`, `<=`, `BETWEEN`            | `revenue_gt`, `revenue_lt`, `revenue_between` |
| **Boolean Logic**           | Combines multiple `HAVING` conditions with `AND`/`OR`.                                                                                                                                                               | `HAVING <cond1> AND <cond2>`                | `AND`/`OR` operators in `having` object    |
| **Subquery HAVING**         | Uses nested aggregations (e.g., *"Show categories where their subcategory’s avg_revenue > X"*).                                                                                                                 | Subquery in `HAVING`                        | Requires recursive GraphQL nesting         |

---

## **Implementation Details**

### **Key Concepts**
1. **Precedence**:
   - `WHERE` → `GROUP BY` → `HAVING` → `ORDER BY`/`LIMIT`.
   - FraiseQL enforces this order by first resolving `WHERE`, then aggregations, and finally applying `HAVING`.

2. **Aggregate Inheritance**:
   - If `WHERE` filters rows before aggregation, `HAVING` filters the *resulting groups*. For example:
     ```sql
     SELECT category, SUM(revenue)
     FROM sales
     WHERE date > '2023-01-01'
     GROUP BY category
     HAVING SUM(revenue) > 10000  -- Filters categories *after* summing.
     ```

3. **Performance**:
   - `HAVING` is executed *after* `GROUP BY`, so the database processes all aggregation work first. Use `WHERE` for early row elimination.

4. **GraphQL ↔ SQL Mapping**:
   | GraphQL Argument       | SQL `HAVING` Equivalent          | Notes                                  |
   |------------------------|----------------------------------|----------------------------------------|
   | `{ revenue_gt: 5000 }` | `HAVING SUM(revenue) > 5000`     | Auto-detected from aggregation type.   |
   | `{ avg_rating_gte: 4.5 }` | `HAVING AVG(rating) >= 4.5`     | Requires `AVG` in the query.           |
   | `{ count_lt: 10 }`    | `HAVING COUNT(*) < 10`           | Defaults to `COUNT(*)`.                 |

---

## **Query Examples**

### **1. Basic HAVING with Aggregate Comparison**
**GraphQL Input:**
```graphql
query {
  salesByCategory(having: { total_revenue_gt: 10000 }) {
    category
    total_revenue
  }
}
```
**SQL Output:**
```sql
SELECT category, SUM(revenue) AS total_revenue
FROM sales
GROUP BY category
HAVING SUM(revenue) > 10000
```

---

### **2. Multiple Conditions with Boolean Logic**
**GraphQL Input:**
```graphql
query {
  salesByMonth(
    having: {
      total_revenue_gt: 5000
      order_count_gte: 100
    }
  ) {
    month
    total_revenue
    order_count
  }
}
```
**SQL Output:**
```sql
SELECT
  EXTRACT(MONTH FROM sale_date) AS month,
  SUM(revenue) AS total_revenue,
  COUNT(*) AS order_count
FROM sales
GROUP BY EXTRACT(MONTH FROM sale_date)
HAVING SUM(revenue) > 5000 AND COUNT(*) >= 100
```

---

### **3. HAVING with Subqueries (Advanced)**
**GraphQL Input (Nested Aggregation):**
```graphql
query {
  topCategories(having: {
    avg_revenue_gt: {
      subquery: {
        filter: { category: "Electronics" }
        field: "avg_revenue"
      }
    }
  }) {
    category
    avg_revenue
  }
}
```
**SQL Output (Simplified):**
```sql
SELECT
  c.category,
  AVG(c.revenue) AS avg_revenue
FROM (
  SELECT category, revenue
  FROM sales
  WHERE category = 'Electronics'
) c
GROUP BY c.category
HAVING AVG(c.revenue) > (
  SELECT AVG(e.revenue)
  FROM sales e
  WHERE e.category = 'Electronics'
)
```

---

### **4. Edge Cases**
#### **a) HAVING with `NULL` Aggregates**
**GraphQL:**
```graphql
query {
  salesByRegion(
    having: { order_count_gt: 0 }  # Excludes NULL counts
  ) {
    region
    order_count
  }
}
```
**SQL:**
```sql
SELECT region, COUNT(*) AS order_count
FROM sales
GROUP BY region
HAVING COUNT(*) > 0  -- NULL counts == 0
```

#### **b) HAVING with `DISTINCT` Aggregates**
**GraphQL:**
```graphql
query {
  uniqueCustomersByCategory(
    having: { distinct_count_gt: 50 }
  ) {
    category
    distinct_customer_count
  }
}
```
**SQL:**
```sql
SELECT
  category,
  COUNT(DISTINCT customer_id) AS distinct_customer_count
FROM sales
GROUP BY category
HAVING COUNT(DISTINCT customer_id) > 50
```

---

## **Components/Solutions**
| **Solution**               | **Use Case**                                                                 | **Example**                                                                 |
|---------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Single Aggregate Filter** | Filter groups by one aggregated value (e.g., revenue > X).                  | `HAVING SUM(revenue) > 10000`                                                 |
| **Composite HAVING**      | Combine multiple aggregates with `AND`/`OR`.                                | `HAVING AVG(rating) > 4.5 AND COUNT(*) > 10`                                 |
| **Subquery HAVING**        | Compare groups to subquery results (e.g., "top 20% of categories").          | `HAVING SUM(revenue) > (SELECT AVG(r) FROM (SELECT SUM(revenue) AS r FROM sales GROUP BY category) AS stats)` |
| **Custom Scalar Functions** | Apply user-defined functions to aggregates (e.g., profit_margin = revenue - cost). | `HAVING profit_margin > 0` (requires function registration in FraiseQL).    |
| **Window Function HAVING** | Use window functions (e.g., `RANK()`, `PERCENT_RANK()`) in `HAVING`.         | `HAVING RANK() OVER (ORDER BY revenue DESC) <= 10` (with `PARTITION BY`).    |

---

## **Requirements & Constraints**
| **Requirement**                          | **Note**                                                                                     |
|------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Supported Aggregates**                | `SUM`, `AVG`, `COUNT`, `MIN`, `MAX`, `DISTINCT COUNT`, custom aggregates via extensions.     |
| **Operators**                           | `=`, `>`, `<`, `>=`, `<=`, `BETWEEN`, `IN`, `LIKE`, `IS NULL`, `IS NOT NULL`.                 |
| **Boolean Logic**                       | `AND`, `OR`, parentheses for precedence.                                                    |
| **Subqueries in HAVING**                | Supported for nested aggregations (see *Query Examples* section).                          |
| **Performance**                         | Avoid `HAVING` with non-SARGable conditions (e.g., `LIKE '%term%'`).                         |
| **GraphQL Argument Naming**             | Follows `field_<operator>` convention (e.g., `revenue_gt`, `count_between`).                 |
| **Extension Points**                    | Custom scalar types and functions can extend `HAVING` logic (e.g., `HAVING profitability > 20%`). |

---

## **Related Patterns**
1. **[WHERE Clause for Pre-Aggregation Filtering](link)**
   - Filters rows *before* aggregation (complements `HAVING`).
   - *Use case*: Eliminate irrelevant rows early to reduce `GROUP BY` overhead.

2. **[Aggregate Functions](link)**
   - Core building blocks for `HAVING` (e.g., `SUM`, `AVG`).
   - *Use case*: Define what to aggregate before applying filters.

3. **[Window Functions](link)**
   - Enable ranking/pivoting within partitions (e.g., `RANK() OVER (PARTITION BY category)`).
   - *Use case*: Combine with `HAVING` for conditional rankings (e.g., "top 3 categories by revenue").

4. **[Subquery Rewriting](link)**
   - Optimizes complex `HAVING` subqueries into efficient JOINs or CTEs.
   - *Use case*: Avoid performance pitfalls with nested aggregations.

5. **[GraphQL-to-SQL Translation](link)**
   - Details how FraiseQL parses `having` arguments into SQL.
   - *Use case*: Debug or extend the translation logic for custom aggregations.

---

## **Best Practices**
1. **Minimize Aggregations in HAVING**:
   - Use `WHERE` for row-level filters first to reduce the dataset early.
   - Example: Filter by date ranges before grouping.

2. **Prefer Indexed Columns**:
   - Ensure columns in `GROUP BY` and `HAVING` are indexed for speed.
   - Example: Index `category` and `revenue` for `GROUP BY category HAVING SUM(revenue) > 10000`.

3. **Avoid Redundant Calculations**:
   - Reuse aggregates in `HAVING` rather than recalculating:
     ```graphql
     # Bad: Repeats SUM(revenue)
     having: {
       revenue_gt: 10000,
       profit_margin_gt: 0.2  # Requires SUM(revenue) + SUM(cost)
     }

     # Good: Use derived fields
     fields: ["total_revenue", "profit_margin"]
     having: {
       total_revenue_gt: 10000,
       profit_margin_gt: 0.2
     }
     ```

4. **Leverage Subqueries for Complex Logic**:
   - For multi-table comparisons, use subqueries in `HAVING`:
     ```sql
     HAVING SUM(revenue) > (
       SELECT AVG(r) FROM revenue_stats
     )
     ```

5. **Test Edge Cases**:
   - Validate `HAVING` with `NULL` values, empty groups, and large datasets.

---

## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------|-------------------------------------------------------------------------------|
| `HAVING` returns no results        | Threshold too high or no matching groups. | Adjust the filter or check aggregation logic.                              |
| Slow performance                   | Unoptimized `GROUP BY` or missing indexes. | Add indexes or rewrite the query to reduce data volume before `GROUP BY`.   |
| `HAVING` ignores subqueries        | Subquery returns `NULL`.                | Ensure subqueries return valid values (e.g., use `COALESCE`).                 |
| GraphQL argument not mapped to SQL | Invalid syntax or unsupported operator. | Verify the operator (e.g., `revenue_between` requires `BETWEEN` in SQL).    |

---
**See also:**
- [FraiseQL Schema Designer](link) – Configure `HAVING` rules for custom fields.
- [SQL Performance Guide](link) – Optimize `GROUP BY` and `HAVING` operations.