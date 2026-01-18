# **[Pattern] SQL Query Composition Reference Guide**
*FraiseQL – Optimized SQL Query Generation from GraphQL*

---

## **1. Overview**
FraiseQL uses **SQL Query Composition** to transform nested GraphQL queries into **efficient, single SQL queries** by intelligently structuring `JOIN` operations, **Common Table Expressions (CTEs)**, and subqueries. This approach eliminates the **N+1 query problem**, reduces network overhead, and leverages **database optimizers** for optimal performance.

Key benefits:
✔ **Avoids N+1 queries** by resolving all relationships in one execution.
✔ **Reduces data transfer** by fetching only required fields.
✔ **Leverages SQL optimizations** (indexes, query plans, CTEs) for better efficiency.
✔ **Supports complex GraphQL structures** (aggregations, filtering, pagination).

This pattern is implemented via **query parsing, schema mapping, and SQL generation** to ensure readability, maintainability, and performance.

---

## **2. Schema Reference**

| **Component**               | **Description**                                                                                                                                                                                                 | **Example (PostgreSQL)**                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| **Root Query**              | The top-level GraphQL resolver that initiates SQL execution.                                                                                                                                                   | `WITH root_cte AS (SELECT id, name FROM users)...`                                      |
| **CTE (Common Table Expression)** | Temporary result sets used for modular query construction (improves readability and performance).                                                                                                       | `WITH user_data AS (SELECT * FROM users WHERE id = 1)...`                             |
| **JOIN Strategy**           | Strategically links tables based on GraphQL relationships (implicit or explicit).                                                                                                                       | `JOIN orders ON users.id = orders.user_id` (left/inner/outer)                          |
| **Field Selection**         | Only includes required fields in SQL to minimize data transfer.                                                                                                                                              | `SELECT u.id, u.name, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id` |
| **Subqueries**              | Used for nested filters, aggregations, or derived data.                                                                                                                                                   | `WHERE EXISTS (SELECT 1 FROM reviews WHERE review.user_id = u.id)`                     |
| **Filter Handling**         | Translates GraphQL filters (`where`, `orderBy`, `limit`) into SQL conditions.                                                                                                                            | `WHERE u.is_active = TRUE AND o.created_at > '2023-01-01'`                               |
| **Pagination**              | Implements `limit` and `offset` via SQL’s `LIMIT` and `OFFSET`.                                                                                                                                             | `SELECT * FROM users ORDER BY name LIMIT 10 OFFSET 20`                                 |
| **Aggregations**            | Converts GraphQL `@aggregate` directives into SQL `GROUP BY`/`HAVING`.                                                                                                                                   | `SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id`                 |

---

## **3. Query Examples**

### **3.1 Basic Relationship Query (1-to-Many)**
**GraphQL:**
```graphql
query {
  user(id: 1) {
    id
    name
    orders {
      id
      amount
    }
  }
}
```

**Generated SQL (FraiseQL):**
```sql
WITH user_data AS (
  SELECT id, name FROM users WHERE id = $1
)
SELECT
  u.id,
  u.name,
  (
    SELECT json_agg(
      json_build_object('id', o.id, 'amount', o.amount)
    )
    FROM orders o
    WHERE o.user_id = u.id
  ) AS orders
FROM user_data u;
```
**Optimized SQL (CTE or JOIN):**
```sql
WITH user_data AS (
  SELECT id, name FROM users WHERE id = 1
),
user_orders AS (
  SELECT o.id, o.amount FROM orders o
  WHERE o.user_id = (SELECT id FROM user_data)
)
SELECT
  u.id,
  u.name,
  (
    SELECT json_agg(json_build_object('id', id, 'amount', amount))
    FROM user_orders
  ) AS orders
FROM user_data u;
```

---

### **3.2 Filtered Query with Aggregation**
**GraphQL:**
```graphql
query {
  users(where: { age: { gt: 25 } }) {
    id
    name
    orderCount
  }
}
```
**Generated SQL:**
```sql
WITH filtered_users AS (
  SELECT id, name FROM users WHERE age > $1
)
SELECT
  f.id,
  f.name,
  (
    SELECT COUNT(*)
    FROM orders o
    WHERE o.user_id = f.id
  ) AS orderCount
FROM filtered_users f;
```

---

### **3.3 Paginated Query with Sorting**
**GraphQL:**
```graphql
query {
  orders(
    where: { amount: { gt: 100 } },
    orderBy: { createdAt: DESC },
    limit: 10,
    offset: 20
  ) {
    id
    amount
  }
}
```
**Generated SQL:**
```sql
SELECT
  o.id,
  o.amount
FROM orders o
WHERE o.amount > $1
ORDER BY o.created_at DESC
LIMIT $2 OFFSET $3;
```
*(Parameters: `$1 = 100`, `$2 = 10`, `$3 = 20`)*

---

### **3.4 Nested Filtering (Subquery)**
**GraphQL:**
```graphql
query {
  user(id: 1) {
    id
    reviews {
      rating
      comments
      author { name }
    }
  }
}
```
**Generated SQL:**
```sql
WITH user_data AS (
  SELECT id FROM users WHERE id = $1
),
user_reviews AS (
  SELECT r.rating, r.comments, r.user_id
  FROM reviews r
  WHERE r.user_id = (SELECT id FROM user_data)
),
author_names AS (
  SELECT name FROM users WHERE id = (SELECT author_id FROM user_reviews)
)
SELECT
  ur.rating,
  ur.comments,
  an.name AS author
FROM user_reviews ur
JOIN author_names an ON ur.author_id = an.id;
```

---

## **4. Key Implementation Details**

### **4.1 Query Parsing & Schema Mapping**
- **GraphQL → SQL Translation**:
  - GraphQL **selection sets** → SQL `SELECT` columns.
  - GraphQL **arguments** (`where`, `orderBy`) → SQL `WHERE/ORDER BY` clauses.
  - GraphQL **relationships** → SQL `JOIN` or subqueries.

- **Schema Annotations**:
  - `@table`: Maps GraphQL types to database tables.
  - `@join`: Defines relationships (e.g., `@join(field: "user", type: "User")`).
  - `@filterable`: Specifies which fields support filtering.

### **4.2 JOIN Strategy Selection**
| **Scenario**               | **Recommended Approach**                          | **Example**                                                                 |
|----------------------------|---------------------------------------------------|-----------------------------------------------------------------------------|
| **Direct 1-to-Many**       | Left JOIN with subquery aggregation               | `LEFT JOIN orders ON users.id = orders.user_id`                            |
| **Deeply Nested Relations**| CTEs for modularity                                 | `WITH user_data AS (...), orders_data AS (...) SELECT ...`                  |
| **Filterable Relations**   | Filter in subquery before joining                 | `WHERE EXISTS (SELECT 1 FROM reviews WHERE user_id = u.id)`                |
| **Large Data Sets**        | Pagination via `LIMIT/OFFSET`                     | `SELECT ... FROM users ORDER BY id LIMIT 100 OFFSET 0`                     |

### **4.3 Performance Optimizations**
- **Index Utilization**:
  - Ensure foreign keys (`user_id`) and filter fields (`created_at`) are indexed.
- **CTE vs. Subquery**:
  - Use **CTEs** for complex, reusable logic (e.g., repeated filtering).
  - Use **subqueries** for simple conditions (e.g., `WHERE EXISTS`).
- **Column Selection**:
  - Only select **required fields** to reduce payload size.
- **Parameterized Queries**:
  - Always use **prepared statements** to prevent SQL injection.

### **4.4 Handling Edge Cases**
| **Case**                     | **Solution**                                                                 |
|------------------------------|------------------------------------------------------------------------------|
| **Circular Dependencies**    | Detect and reject (e.g., `User → Post → User`).                             |
| **Missing Fields**           | Return `NULL` for optional fields or skip unrelated tables.                |
| **Large Result Sets**        | Apply pagination early (e.g., filter before `JOIN`).                        |
| **Database-Specific Syntax** | Abstract with `dbAdapter` (e.g., PostgreSQL `json_agg` vs. MySQL `JSON_ARRAYAGG`). |

---

## **5. Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use**                                                                 |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| **[Pagination & Caching]**       | Optimizes large datasets with pagination and query caching to reduce database load.                                                                                                                 | When queries return thousands of records.                                       |
| **[Projection Pushdown]**        | Pushes field selection into database tables to minimize data transfer.                                                                                                                               | When GraphQL clients request only a subset of fields.                          |
| **[Incremental Loading]**       | Loads related data in batches (e.g., for large `orders`).                                                                                                                                                 | When nested data is too large for a single query.                              |
| **[Query Batching]**             | Combines multiple GraphQL queries into a single database request.                                                                                                                                         | When resolving multiple unrelated queries in one call.                          |
| **[Denormalization]**            | Pre-computes and stores aggregated data (e.g., `orderCount`) for faster reads.                                                                                                                         | When read-heavy workloads require sub-10ms responses.                          |

---

## **6. Best Practices**
1. **Design for Query Efficiency**:
   - Prefer **shallow queries** over deep nesting.
   - Use **aliases** for complex selections (e.g., `AS order_count`).
2. **Leverage Database Features**:
   - Use **CTEs** for readability and optimizer hints.
   - Apply **indexes** on frequently filtered fields.
3. **Monitor & Optimize**:
   - Profile SQL queries with `EXPLAIN ANALYZE`.
   - Avoid `SELECT *`—always specify columns.
4. **Database Compatibility**:
   - Test on target DB (e.g., PostgreSQL vs. MySQL syntax).
   - Use **query plan caching** where supported.

---
**See also:**
- [FraiseQL Schema Definition](link)
- [GraphQL-to-SQL Translation Guide](link)
- [Performance Benchmarks](link)