# **[Pattern] Composite WHERE Operators in FraiseQL**
*Building Nested, Logical Filter Expressions for Complex Queries*

---

## **Overview**
FraiseQL’s **Composite WHERE Operators** pattern allows users to construct complex filter conditions using **logical operators (`AND`, `OR`, `NOT`)** with arbitrary nesting depth. This enables expressive query capabilities while maintaining traceability of query complexity to support cost-based query rejection at runtime.

Key features include:
- **Logical composition**: Combine simple conditions (`=` , `<>`, `LIKE`) into nested expressions.
- **Operator precedence**: Explicit grouping with parentheses resolves ambiguity.
- **Cost tracking**: FraiseQL monitors query complexity to enforce reasonable limits and reject expensive operations.
- **Semantic validation**: Ensures logical correctness (e.g., avoiding `OR NULL` or redundant `NOT NOT`).

Unlike conventional WHERE clauses, this pattern emphasizes **clarity** (via structured nesting) and **scalability** (via cost estimation).

---

## **Schema Reference**
The following tables define the syntax and semantics of composite WHERE operators.

### **1. Core Operators**
| Operator | Syntax           | Description                                                                 |
|----------|------------------|-----------------------------------------------------------------------------|
| Logical AND | `A AND B`        | Returns rows where *both* `A` and `B` are true.                             |
| Logical OR  | `A OR B`         | Returns rows where *either* `A` or `B` is true.                            |
| Logical NOT | `NOT A`          | Inverts the condition `A`.                                                  |
| Parentheses | `(A)`            | Explicitly groups nested sub-conditions for precedence control.            |

### **2. Supported Operands**
Composite operators apply to **simple conditions** (e.g., `column op value`) or other composite expressions.

| Type               | Example                     | Notes                                  |
|--------------------|-----------------------------|----------------------------------------|
| **Comparison**     | `age > 30`, `name LIKE 'J%'` | Standard operators (`=`, `<>`, `IN`, etc.). |
| **Aggregate**      | `SUM(sales) > 1000`         | May require `GROUP BY` for validity.   |
| **Subquery**       | `(SELECT * FROM orders)`    | Allowed in `IN`, `EXISTS`, or nesting. |
| **Composite**      | `(price > 100 AND stock > 0)`| Nested conditions.                      |

### **3. Operator Precedence**
Parentheses override implicit precedence (`NOT` > `AND` > `OR`). Example:
```sql
-- Evaluates as: ((NOT A) AND (B OR C))
NOT A AND B OR C
```

---

## **Query Examples**
### **1. Basic Composition**
```sql
SELECT * FROM products
WHERE category = 'Electronics' AND (price > 100 OR warranty > 12);
```
- **Semantics**: Returns "Electronics" items priced over $100 **or** with >12-month warranty.

### **2. Nested NOT**
```sql
SELECT * FROM users
WHERE NOT (country = 'USA' AND status = 'inactive');
```
- **Semantics**: Excludes *only* US users who are inactive. Equivalent to:
  ```sql
  SELECT * FROM users
  WHERE country <> 'USA' OR status <> 'inactive';
  ```

### **3. Aggregate + Composite**
```sql
SELECT department
FROM employees
WHERE job_level > 5
AND (
    (title LIKE 'Manager%' AND salary > 80000)
    OR (title = 'Director' AND salary > 100000)
);
```
- **Semantics**: Filters departments with high-tier roles (**Manager** salary > $80K **or** **Director** salary > $100K).

### **4. Cost-Sensitive Rejection**
FraiseQL may reject queries exceeding a complexity threshold (e.g., >5 nested `OR` clauses). Example:
```sql
-- Likely rejected (logical explosion):
SELECT * FROM transactions
WHERE (
    (type = 'deposit' AND user_id IN (SELECT * FROM blocked_users))
    OR (type = 'withdrawal' AND amount > 10000)
    OR (type = 'transfer' AND (
        (sender_id = 'admin') OR
        (receiver_id LIKE '%banned%')
    ))
);
```

---

## **Implementation Details**
### **1. Internal Representation**
Composite WHERE clauses are parsed into an **Abstract Syntax Tree (AST)**. Example for:
```sql
A AND B OR C
```
Becomes:
```
OR
├── AND
│   ├── A (simple condition)
│   └── B (simple condition)
└── C (simple condition)
```

### **2. Cost Estimation**
FraiseQL estimates query cost via:
- **Node depth**: Penalizes deep nesting (e.g., 5 `OR` levels may incur a "cost" of `2^5`).
- **Subquery recursion**: Depth-first traversal of nested subqueries.
- **Cardinality bounds**: Limits `OR` clauses to avoid Cartesian products.

### **3. Validation Rules**
| Rule                     | Example Violation                          | Outcome                     |
|--------------------------|--------------------------------------------|-----------------------------|
| No `OR NULL`             | `status = 'active' OR status IS NULL`     | Rejected (undefined logic). |
| No redundant `NOT NOT`   | `NOT (NOT (x = 5))`                       | Optimized to `x = 5`.       |

---

## **Related Patterns**
| Pattern                     | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **[Simple WHERE Conditions]** | Primitives (`=`, `LIKE`, `IN`) without nesting.                             |
| **[Query Cost Modeling]**     | Framework for predicting execution time/complexity.                         |
| **[Subquery Rewriting]**      | Optimizing nested `SELECT` statements in WHERE clauses.                     |
| **[Window Functions]**        | Extending filtering with `OVER()` partitions (e.g., `WHERE RANK() < 3`).  |

---
**Note**: For advanced use cases, see the [FraiseQL Query Optimizer Guide](#) for tuning parameters like `max_nesting_depth`.