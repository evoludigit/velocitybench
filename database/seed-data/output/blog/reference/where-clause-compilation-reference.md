# **[Pattern] WHERE Clause Compilation to SQL Reference Guide**

---

## **Overview**
This pattern describes how **GraphQL filter inputs** (passed via arguments, fragments, or directives) are translated into **SQL `WHERE` clauses** during query execution. The conversion must preserve query intent while accounting for type systems, operators, and database-specific syntax (e.g., `LIKE`, `IN`, or `BETWEEN`).

Key considerations:
- **Type safety**: GraphQL types (e.g., `String`, `Int`, `Boolean`) must map to SQL-compatible columns (e.g., `VARCHAR`, `INTEGER`).
- **Operator support**: GraphQL filters (e.g., `eq`, `gt`) are mapped to SQL operators (e.g., `=`, `>`).
- **Complex conditions**: Logical operators (`AND`, `OR`, `NOT`) and nested filters require proper SQL grouping and negation.
- **Database-specific syntax**: Certain patterns (e.g., `LIKE`, `SOUNDEX`) may require platform-specific adjustments.
- **Null handling**: GraphQL’s `null` values must translate to SQL’s `IS NULL`/`IS NOT NULL`.

This pattern ensures that GraphQL filters compile to **efficient, correct, and database-portable SQL** while maintaining the original query’s semantics.

---

## **Schema Reference**
The following table outlines the key components of the pattern and their SQL equivalents.

| **GraphQL Input Type**       | **SQL Equivalent**               | **Notes**                                                                                     |
|-------------------------------|-----------------------------------|-----------------------------------------------------------------------------------------------|
| `String`                      | `VARCHAR`, `TEXT`                | Supports `eq`, `ne`, `contains`, `startsWith`, `endsWith`, `like`, `notLike`.              |
| `Int`, `Float`                | `INTEGER`, `DECIMAL`, `REAL`     | Supports `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `notIn`.                              |
| `Boolean`                     | `BOOLEAN`                        | Supports `eq`, `ne` (maps to `TRUE`/`FALSE`).                                               |
| `ID`                          | `VARCHAR`, `BIGINT` (auto-increment) | Treated as `String` unless database stores IDs as numeric. |
| `Date`, `DateTime`            | `DATE`, `TIMESTAMP`              | Supports temporal operators (`eq`, `gt`, `lt`, `between`).                                  |
| `Enum`                        | `VARCHAR` (or platform-specific) | Comparisons use exact matching (e.g., `= 'ACTIVE'`).                                           |
| **Logical Operators**         | SQL Logical Operators             | `AND` → `AND`, `OR` → `OR`, `NOT` → `NOT`.                                                   |
| `Null`                        | `IS NULL`/`IS NOT NULL`          | GraphQL `null` inputs map to SQL null checks.                                                |
| **Array/Object Filters**      | Subqueries, `JSON`/`IN` clauses  | Arrays use `IN`, objects may require `JSON_CONTAINS` (PostgreSQL) or `JSONPATH` (MySQL).     |

### **Operator Mapping**
| **GraphQL Operator** | **SQL Equivalent**       | **Example**                     | **Database Notes**                          |
|-----------------------|--------------------------|----------------------------------|---------------------------------------------|
| `eq`                  | `=`                      | `WHERE id = '123'`               | Standard.                                   |
| `ne`                  | `<>` or `!=`             | `WHERE status <> 'DELETED'`      | `!=` preferred if supported.               |
| `gt`                  | `>`                      | `WHERE price > 100`              | Works for numbers, dates, etc.               |
| `gte`                 | `>=`                     | `WHERE created_at >= '2023-01-01'`|                                               |
| `lt`                  | `<`                      | `WHERE rating < 4`               |                                               |
| `lte`                 | `<=`                     | `WHERE quantity <= 5`            |                                               |
| `in`                  | `IN`                     | `WHERE category IN ('A', 'B')`   | Use `IN` for small lists; avoid large lists.|
| `notIn`               | `NOT IN`                 | `WHERE status NOT IN ('DRAFT')`  |                                               |
| `contains`            | `LIKE '%...%'`           | `WHERE name LIKE '%smith%'`      | Case-sensitive by default; use `ILIKE` for case-insensitive (PostgreSQL). |
| `startsWith`          | `LIKE '...%'`            | `WHERE email LIKE 'john%'`       |                                               |
| `endsWith`            | `LIKE '%...'`            | `WHERE filename LIKE '%.pdf'`    |                                               |
| `like`                | `LIKE`                   | `WHERE description LIKE 'prod%'`  | Wildcards: `%` (any), `_` (single char).   |
| `notLike`             | `NOT LIKE`               | `WHERE title NOT LIKE '%test%'`  |                                               |
| `between`             | `BETWEEN ... AND ...`    | `WHERE age BETWEEN 18 AND 30`    | Inclusive of bounds.                        |
| `isNull`              | `IS NULL`                | `WHERE discount IS NULL`         |                                               |
| `isNotNull`           | `IS NOT NULL`            | `WHERE notes IS NOT NULL`        |                                               |

---

## **Query Examples**
### **1. Simple Filter (Single Field)**
**GraphQL Query:**
```graphql
query {
  products(where: { price_gt: 100 }) {
    id
    name
  }
}
```
**Compiled SQL:**
```sql
SELECT id, name
FROM products
WHERE price > 100
```

---

### **2. Multiple Conditions (AND)**
**GraphQL Query:**
```graphql
query {
  users(where: { age_gte: 21, status_eq: "ACTIVE" }) {
    name
    email
  }
}
```
**Compiled SQL:**
```sql
SELECT name, email
FROM users
WHERE age >= 21 AND status = 'ACTIVE'
```

---

### **3. Logical OR with NOT**
**GraphQL Query:**
```graphql
query {
  orders(
    where: {
      OR: [
        { customer_id_eq: "123" }
        { status_notEq: "CANCELLED" }
      ]
    }
  ) {
    total
  }
}
```
**Compiled SQL:**
```sql
SELECT total
FROM orders
WHERE customer_id = '123'
   OR status != 'CANCELLED'
```

---

### **4. Null Check and LIKE**
**GraphQL Query:**
```graphql
query {
  reviews(
    where: {
      rating_gt: 3,
      text_isNull: false,
      text_contains: "great"
    }
  ) {
    review_text
  }
}
```
**Compiled SQL:**
```sql
SELECT review_text
FROM reviews
WHERE rating > 3
  AND text IS NOT NULL
  AND text LIKE '%great%'
```

---

### **5. Array Filter (IN Clause)**
**GraphQL Query:**
```graphql
query {
  products(
    where: {
      category_in: ["ELECTRONICS", "CLOTHING"]
    }
  ) {
    name
  }
}
```
**Compiled SQL:**
```sql
SELECT name
FROM products
WHERE category IN ('ELECTRONICS', 'CLOTHING')
```

---

### **6. Date Range (BETWEEN)**
**GraphQL Query:**
```graphql
query {
  orders(
    where: {
      created_at_between: ["2023-01-01", "2023-12-31"]
    }
  ) {
    order_date
  }
}
```
**Compiled SQL:**
```sql
SELECT order_date
FROM orders
WHERE created_at BETWEEN '2023-01-01' AND '2023-12-31'
```

---

### **7. Complex Nested Conditions**
**GraphQL Query:**
```graphql
query {
  customers(
    where: {
      AND: [
        {
          country_eq: "USA",
          OR: [
            { age_lte: 30 }
            { tier_gt: "SILVER" }
          ]
        }
        { active_eq: true }
      ]
    }
  ) {
    name
  }
}
```
**Compiled SQL:**
```sql
SELECT name
FROM customers
WHERE (country = 'USA'
       AND (age <= 30 OR tier > 'SILVER'))
  AND active = TRUE
```

---

## **Database-Specific Adjustments**
| **Database**       | **Adjustments**                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| **PostgreSQL**     | Use `ILIKE` for case-insensitive `like`; supports `JSON_CONTAINS` for object filters. |
| **MySQL**          | Use `LIKE` with `COLLATE` for case sensitivity; escape special characters (e.g., `\_`). |
| **SQLite**         | `LIKE` is case-sensitive; use `REGEXP` for advanced pattern matching.        |
| **Oracle**         | Replace `LIKE` with `LIKE` or `REGEXP_LIKE`; use `BETWEEN` with timestamps.     |
| **SQL Server**     | Use `CONTAINS` for full-text search; `ILIKE` equivalent is `COLLATE SQL_Latin1_General_CP1_CI_AS`. |

---

## **Related Patterns**
1. **[GraphQL to SQL Type Mapping]**
   - Describes how GraphQL input/output types (e.g., `Int`, `Enum`) are mapped to database columns.

2. **[Pagination in GraphQL Queries]**
   - Explains how `limit` and `offset` (or cursor-based pagination) interact with compiled `WHERE` clauses.

3. **[Joins and Relationships in GraphQL]**
   - Details how `WHERE` clauses are applied across joined tables in SQL (e.g., filtering nested objects).

4. **[Optimizing WHERE Clause Performance]**
   - Strategies for indexing, avoiding `SELECT *`, and rewriting complex conditions for efficiency.

5. **[Error Handling for Invalid Filters]**
   - How to validate GraphQL filter inputs (e.g., checking if a filter applies to the correct field type).

---
## **Key Implementation Considerations**
1. **Error Handling**:
   - Reject unsupported operators or types with a clear error (e.g., `"Field 'price_like' does not support 'LIKE' operator"`).
   - Validate that filter fields exist in the schema.

2. **Security**:
   - **Never** directly interpolate user input into SQL (use parameterized queries to prevent SQL injection).
   - Sanitize wildcard characters (`%`, `_`) in `LIKE` clauses.

3. **Performance**:
   - Avoid `LIKE '%prefix%'` (use `FULLTEXT` indexes if needed).
   - For large `IN` clauses, consider subqueries or temporary tables.

4. **Extensibility**:
   - Allow plugins for database-specific functions (e.g., PostgreSQL’s `SOUNDEX`).
   - Support custom operators via directives (e.g., `@custom(op:"SOUNDEX")`).

5. **Testing**:
   - Write unit tests for operator mappings and edge cases (e.g., `null` values, empty arrays).
   - Test against multiple databases to ensure portability.

---
## **Example Implementation (Pseudocode)**
```javascript
function compileWhereClause(fields, tableName) {
  let sql = `WHERE 1=1`;
  let params = [];

  fields.forEach((filter, index) => {
    const operator = filter.op;
    const value = filter.value;
    const column = `${tableName}.${filter.field}`;

    switch (operator) {
      case 'eq':
        sql += ` AND ${column} = ?`;
        params.push(value);
        break;
      case 'gt':
        sql += ` AND ${column} > ?`;
        params.push(value);
        break;
      case 'contains':
        sql += ` AND ${column} LIKE CONCAT('%', ?, '%')`;
        params.push(value);
        break;
      case 'AND':
        // Recursively handle nested AND clauses
        sql += ` AND (${compileWhereClause(filter.args, tableName)})`;
        break;
      // ... other operators
    }
  });

  return { sql, params };
}
```

---
## **Troubleshooting**
| **Issue**                     | **Cause**                          | **Solution**                                                                 |
|--------------------------------|------------------------------------|------------------------------------------------------------------------------|
| `SQL syntax error`             | Invalid operator/field             | Validate input schema; check for typos in operators (e.g., `gt` vs `gte`). |
| Poor query performance         | Missing indexes on filtered fields | Add indexes to frequently filtered columns.                                  |
| `LIKE` not working as expected | Case sensitivity                  | Use `ILIKE` (PostgreSQL) or `COLLATE` (MySQL).                              |
| `IN` clause too large          | >1000 values                       | Use a temporary table or subquery.                                           |
| `NULL` handling incorrect      | GraphQL `null` treated as empty    | Explicitly check for `IS NULL`/`IS NOT NULL`.                              |

---
## **Further Reading**
- [GraphQL Filtering Specification](https://github.com/graphql/graphql-spec/blob/main/spec/GraphQL%20Operations/SD%202.5.md#filtering)
- [PostgreSQL JSON Functions](https://www.postgresql.org/docs/current/functions-json.html)
- [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)