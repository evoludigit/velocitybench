# **[Pattern] Operator Addition Reference Guide**

---

## **Overview**
The **Operator Addition** pattern enables developers to extend or modify query capabilities by adding **custom filter operators** to an existing search or filtering system. This pattern is commonly used in database query languages, search APIs, and application filtering systems where default operators (e.g., `=`, `>`, `<`, `IN`) are insufficient. By implementing this pattern, you allow users to define **new logical or mathematical operations** (e.g., `LIKE`, `BETWEEN`, `CONTAINS`), improve query flexibility, and adapt to domain-specific needs.

This reference guide covers:
- Key concepts and use cases
- Implementation details (schema, registration, and execution)
- Example queries
- Integration with related patterns (e.g., **Query Composition**, **Operator Chaining**)

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| Component               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Operator Registry**   | A centralized registry storing available operators (e.g., `=`, `>`, `LIKE`). |
| **Operator Definition** | Metadata describing an operator’s syntax, precedence, and evaluation logic. |
| **Operator Processor**  | Executes operators on column values (e.g., `WHERE price > 100`).             |
| **Parser/Lexer**        | Converts user input (e.g., `"name LIKE 'John' "`) into an abstract syntax tree (AST). |
| **Resolver**            | Maps operator names (e.g., `LIKE`) to their implementations.               |

---

### **2. Operator Definition Schema**
Operators are registered with a structured definition. Below is the **schema reference**:

| **Field**          | **Type**       | **Description**                                                                 | **Example Values**                     |
|--------------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `name`             | `String`       | Unique identifier for the operator (e.g., `"LIKE"`, `"BETWEEN"`).               | `"LIKE"`, `"CONTAINS"`                 |
| `arity`            | `Integer`      | Number of operands (unary: `1`, binary: `2`, ternary: `3`).                   | `2` (e.g., `A > B`)                   |
| `associativity`    | `Enum`         | `LEFT`, `RIGHT`, `NONE` (affects evaluation order in chained operators).       | `LEFT`                                 |
| `precedence`       | `Integer`      | Priority level (higher = evaluated first).                                      | `10` (higher than `+` but lower than `*`)|
| `syntax`           | `Object`       | Supported syntax variations.                                                    | `{ infix: `A [operator] B`, prefix: `NOT A` }` |
| `evaluation`       | `Function`     | Custom logic (e.g., `str.contains()`, `math.pow()`).                           | `function(a, b) { return a.includes(b); }` |
| `inputTypes`       | `[Type]`       | Accepted operand types (e.g., `String`, `Number`, `Date`).                      | `["String"]`                           |
| `outputType`       | `Type`         | Returned type after evaluation.                                                  | `Boolean`                              |
| `isNullable`       | `Boolean`      | Whether operator handles `NULL` values.                                         | `true`                                 |
| `literal`          | `String`       | Human-readable symbol (e.g., `"LIKE"`, `"~"`).                                  | `"LIKE"`                               |

---

### **3. Operator Lifecycle**
#### **A. Registration**
Operators are added to the registry during initialization or runtime.
Example (Pseudocode):
```javascript
const operators = [
  { name: "LIKE", arity: 2, precedence: 5, syntax: { infix: "[A] LIKE [B]" }, evaluation: stringLike },
  { name: "BETWEEN", arity: 3, precedence: 8, syntax: { infix: "[A] BETWEEN [B] AND [C]" }, evaluation: rangeCheck }
];

registry.register(operators);
```

#### **B. Resolution**
During query parsing, the resolver maps operator names to their implementations:
```plaintext
Input:  `WHERE name LIKE '%John%'`
Parsed: `LIKE(name, '%John%')`
Resolved: `LIKE` → `stringLike` function
```

#### **C. Execution**
Operators are invoked during query evaluation:
```plaintext
Query: `SELECT * FROM users WHERE age > 30 AND name LIKE 'A%'`
Steps:
1. `age > 30` → `true`/`false`
2. `name LIKE 'A%'` → `true`/`false`
3. Combine results with `AND`
```

---

### **4. Supported Operator Types**
| **Category**       | **Examples**                     | **Use Case**                          |
|--------------------|----------------------------------|----------------------------------------|
| **Comparison**     | `=`, `!=`, `>`, `<`, `BETWEEN`   | Range filtering, equality checks.     |
| **Text Search**    | `LIKE`, `CONTAINS`, `STARTS_WITH` | Pattern matching.                     |
| **Mathematical**   | `+`, `-`, `*`, `%`, `POW`        | Numeric calculations.                 |
| **Logical**        | `AND`, `OR`, `NOT`, `XOR`        | Conditional logic.                    |
| **Collection**     | `IN`, `NOT IN`, `ANY`, `ALL`     | Array/multi-value filtering.          |
| **Custom**         | `VERSION_GT`, `IS_PREMIUM`       | Domain-specific logic.                |

---

## **Query Examples**
### **1. Basic Filtering**
```sql
-- Standard operator
SELECT * FROM products
WHERE price > 100 AND stock < 50;
```

### **2. Text Pattern Matching**
```sql
-- LIKE operator (registered via Operator Addition)
SELECT * FROM users
WHERE name LIKE 'John%' OR email LIKE '%@gmail.com';
```

### **3. Range Queries**
```sql
-- BETWEEN operator
SELECT * FROM orders
WHERE order_date BETWEEN '2023-01-01' AND '2023-12-31';
```

### **4. Custom Domain Operator**
```sql
-- Custom operator: IS_PREMIUM (returns true if user has premium status)
SELECT * FROM users
WHERE IS_PREMIUM(user_id) AND active = true;
```

### **5. Chained Operators**
```sql
-- Combining registered operators
SELECT * FROM products
WHERE category = 'Electronics'
  AND (price > 200 OR (price < 100 AND stock > 0));
```

---

## **Edge Cases & Considerations**
| **Scenario**               | **Handling**                                                                 |
|----------------------------|------------------------------------------------------------------------------|
| **NULL Operands**          | Define `isNullable: true` and handle `NULL` in evaluation logic.             |
| **Type Mismatches**        | Validate `inputTypes` during resolution; reject incompatible types.         |
| **Performance**            | Optimize frequent operators (e.g., `IN` with indexed columns).              |
| **Operator Precedence**    | Test with parentheses to clarify evaluation order.                           |
| **Security**               | Sanitize dynamic operands (e.g., prevent SQL injection in `LIKE` patterns). |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Integration**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Query Composition]**   | Combines multiple filters/clauses into a single query.                        | Use `Operator Addition` to extend clauses (e.g., `GROUP BY`, `ORDER BY`).       |
| **[Operator Chaining]**   | Links operators sequentially (e.g., `A > B AND B < C`).                       | Leverage `associativity` and `precedence` to ensure correct chaining.           |
| **[Predicate Pushdown]**  | Moves filters to lower levels (e.g., database or caching layer).              | Register optimized operators for pushdown (e.g., indexed `=`, `>`).             |
| **[Dynamic Filtering]**   | Generates filters at runtime based on user input or context.                 | Extend with `Operator Addition` to support runtime-defined operators.           |
| **[Operator Overloading]** | Reuses operator names for different types (e.g., `+` for numbers/strings).     | Extend `inputTypes` and `evaluation` logic per type.                           |

---

## **Implementation Checklist**
1. **Define Operators**: Register custom operators with the registry schema.
2. **Test Resolvers**: Verify operator resolution for all syntax variations.
3. **Validate Types**: Ensure `inputTypes` and `outputType` match expected data.
4. **Optimize Performance**: Index columns used in frequent operators (e.g., `=`, `>`).
5. **Document Syntax**: Clearly describe supported formats (e.g., `LIKE` with wildcards).
6. **Handle Errors**: Gracefully manage invalid operators or malformed queries.

---
**Example Full Flow**:
```mermaid
graph TD
    A[User Query: "SELECT * WHERE name LIKE '%A%']"] --> B[Parser]
    B --> C[Resolver: "LIKE" → stringLike()]
    C --> D[Evaluator: Check each row's name]
    D --> E[Result Set]
```

---
**References**:
- [SQL Standard Operators](https://www.sql-standard.org/)
- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [LINQ Operator Model](https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/linq/linq-query-operators-overview)