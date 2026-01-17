# **[Pattern] Query Complexity Analysis: Reference Guide**

---

## **Overview**
The **Query Complexity Analysis** pattern evaluates the performance impact of SQL `WHERE` clause conditions by measuring their computational complexity (e.g., linear, logarithmic, or exponential) and associated query execution costs. This ensures predictable query efficiency, particularly in large datasets or multi-table joins.

Key objectives:
- **Identify bottlenecks** in filtering logic (e.g., nested inequalities or recursive subqueries).
- **Optimize query plans** by replacing expensive operations with indexed or precomputed alternatives.
- **Establish baseline metrics** for post-deployment performance regression.

Use cases include:
- Analyzing slow `WHERE` clauses in analytical workloads.
- Refactoring APIs with dynamic filtering (e.g., e-commerce product search).
- Ensuring compliance with cost thresholds in cloud databases (e.g., AWS RDS, Azure SQL).

---

## **Schema Reference**

| **Attribute**               | **Purpose**                                                                                     | **Constraints**                                                                                     | **Recommended Index**                     |
|-----------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `where_clause`              | Raw SQL `WHERE` condition (e.g., `status = 'active' AND created_at BETWEEN ...`)              | Length: Max 5,000 characters (to avoid parsing overhead)                                           | None (parsed by query engine)              |
| `complexity_rating`         | Numerical score (1–10) assessing logical complexity (1 = trivial, 10 = exponential).        | Valid range: `1–10`                                                                                  | Indexed for fast filtering                 |
| `cost_estimate`             | Estimated execution time in milliseconds (based on table stats).                              | Positive value (0 for trivial queries)                                                              | Indexed if used for query prioritization  |
| `join_depth`                | Number of tables referenced in the `WHERE` (e.g., `tableA JOIN tableB WHERE ...` → 2).         | Integer ≥0                                                                                            | Indexed for join-heavy workloads            |
| `is_indexed`                | Boolean flag for whether any column in `where_clause` is indexed.                             | `TRUE`/`FALSE`                                                                                       | Filter column                                |
| `recursive_subqueries`      | Count of correlated subqueries (e.g., `WHERE id IN (SELECT ... FROM ... WHERE id = ...)`).   | Integer ≥0                                                                                            | Indexed for complex queries                 |
| `date_range_filter`         | Boolean flag for `BETWEEN`, `>`, or `<` clauses on datetime fields.                          | `TRUE`/`FALSE`                                                                                       | Indexed for temporal queries                |

---

## **Query Examples**
### **1. Simple WHERE Clause (Low Complexity)**
```sql
-- Complexity: 2 (two independent conditions)
SELECT * FROM users
WHERE status = 'active' AND signup_date > '2023-01-01';

-- Analysis:
-- - `status` (likely indexed).
-- - `signup_date` (indexed) with a range filter.
-- - Cost estimate: Low (O(log n) per column).
```

### **2. Nested Inequalities (Moderate Complexity)**
```sql
-- Complexity: 5 (chained inequalities with no index)
SELECT * FROM products
WHERE price BETWEEN 10 AND 100
  AND stock_quantity > (SELECT AVG(stock_quantity) FROM products);

-- Analysis:
-- - `BETWEEN` + correlated subquery → forces table scan.
-- - Cost estimate: High (O(n²) due to subquery).
-- - Optimization: Precompute `AVG(stock_quantity)` or use a materialized view.
```

### **3. Exponential Complexity (High Risk)**
```sql
-- Complexity: 9 (recursive CTE with dynamic conditions)
WITH RECURSIVE expensive_query AS (
  SELECT id FROM users WHERE status = 'admin'
  UNION ALL
  SELECT u.id FROM users u JOIN expensive_query eq ON u.manager_id = eq.id
)
SELECT * FROM expensive_query;

-- Analysis:
-- - Recursive CTE with no termination condition → exponential growth.
-- - Cost estimate: Unbounded (O(2ⁿ)).
-- - Replacement: Use connected components algorithm or graph traversal with limits.
```

### **4. Optimized Dynamic Filtering (Post-Analysis)**
```sql
-- Original (high cost):
SELECT * FROM orders
WHERE customer_id IN (SELECT id FROM customers WHERE region = 'US')
  AND order_date BETWEEN '2023-01-01' AND '2023-12-31';

-- Refactored (low cost):
-- 1. Pre-filter customers (materialized view):
CREATE VIEW us_customers AS SELECT id FROM customers WHERE region = 'US';
-- 2. Query becomes:
SELECT * FROM orders
WHERE customer_id IN (SELECT id FROM us_customers)
  AND order_date BETWEEN '2023-01-01' AND '2023-12-31';
```

---

## **Implementation Details**
### **Key Concepts**
1. **Logical Complexity Scoring**:
   - **1–3**: Simple predicates (equals, `IN`, `LIKE` with patterns).
   - **4–6**: Joins or range filters (`BETWEEN`, `>`, `<`) without recursion.
   - **7–9**: Correlated subqueries, recursive CTEs, or dynamic SQL.
   - **10**: Infinite recursion or undecidable predicates (e.g., `WHERE 1=1`).

2. **Cost Estimation**:
   - Use database-specific tools:
     - **PostgreSQL**: `EXPLAIN ANALYZE`.
     - **SQL Server**: `SET SHOWPLAN_TEXT ON`.
     - **AWS RDS**: CloudWatch Query Performance Insights.
   - **Fallback**: Heuristic based on `WHERE` clause length and token patterns (e.g., `BETWEEN`, `IN`).

3. **Index Utilization**:
   - **Covering Indexes**: Prioritize indexes that include all `SELECT` columns.
   - **Composite Indexes**: Order columns by selectivity (e.g., `status (ASC), created_at (DESC)`).

### **Tools and Libraries**
| **Tool**               | **Purpose**                                                                                     | **Example Use Case**                                  |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| **SQL Parser (ANTLR)** | Parse `WHERE` clauses into an abstract syntax tree (AST) for complexity analysis.          | Identify nested subqueries in user-provided queries.  |
| **Database Profiler**  | Capture execution plans and actual runtime metrics.                                           | Compare `EXPLAIN` vs. real-world performance.        |
| **Redgate SQL Doc**    | Generate schema diagrams linked to query complexity logs.                                     | Audit legacy systems for hidden bottlenecks.         |
| **Custom Metrics API** | Track `complexity_rating` and `cost_estimate` in a time-series database (e.g., TimescaleDB). | Set alerts for queries exceeding 500ms.                 |

### **Common Anti-Patterns**
| **Anti-Pattern**               | **Impact**                                  | **Fix**                                                                 |
|---------------------------------|---------------------------------------------|--------------------------------------------------------------------------|
| `WHERE id NOT IN (SELECT ...)`  | Anti-join → full table scans.               | Rewrite as `LEFT JOIN ... WHERE right_column IS NULL`.                  |
| Dynamic `ORDER BY`              | Forces sorting on unsorted data.            | Pre-sort data or cache sorted results.                                   |
| `COUNT(*)` in subqueries        | Expensive for large datasets.               | Use `COUNT(column)` or approximate functions (e.g., `pg_catalog.cardinality`). |
| Unbounded `LIKE '%text%'`       | Full-text scan.                             | Use full-text indexes or `LIKE 'text%'`.                                  |

---

## **Requirements Traceability**
| **Requirement**                          | **Artifact**                                                                 | **Validation Method**                          |
|------------------------------------------|-------------------------------------------------------------------------------|------------------------------------------------|
| Measure `WHERE` complexity               | `complexity_rating` column in schema.                                         | Unit tests against known patterns.             |
| Estimate query cost                      | `cost_estimate` calculated via `EXPLAIN ANALYZE`.                            | Benchmark against production data.             |
| Index optimization recommendations      | `is_indexed` flag + suggested indexes in UI.                                  | A/B test query performance with/without indexes. |
| Alert for exponential queries           | Dashboards with `complexity_rating > 7`.                                       | Simulate workloads with synthetic data.        |

---

## **Related Patterns**
1. **[Query Rewriting](https://example.com/query-rewriting-pattern)**
   - Refactors slow queries into optimized forms (e.g., `NOT IN` → `LEFT JOIN`).

2. **[Partition Pruning](https://example.com/partition-pruning-pattern)**
   - Reduces scanned data by filtering partitions (e.g., date-based).

3. **[Cost-Based Optimization](https://example.com/cost-based-optimization-pattern)**
   - Uses statistical models (e.g., machine learning) to predict query costs.

4. **[Query Caching](https://example.com/query-caching-pattern)**
   - Mitigates complexity impact for repeated queries (e.g., Redis cache).

5. **[Slow Query Logging](https://example.com/slow-query-logging-pattern)**
   - Captures long-running queries for post-mortem analysis (e.g., `log_slow_queries`).

---
**Note**: Combine this pattern with **Query Optimization Audits** for continuous improvement. For cloud databases, integrate with **Cost Explorer** to correlate complexity with billable resources.