# **[Pattern] Logical Operator Combination: Reference Guide**

## **Overview**
Logical operators (`AND`, `OR`, `NOT`) enable conditional filtering and complex query logic in data processing, search, or rule-based systems. This pattern systematically combines these operators to refine results based on multiple criteria, improving precision and granularity.

Common use cases include:
- **Search queries** (e.g., `"(keyboard AND wireless) OR laptop AND NOT cheap"`).
- **Rule engines** (e.g., `"(age > 18 AND income > 50k) OR studentDiscount = TRUE"`).
- **Database filtering** (e.g., `WHERE (category = 'Electronics' AND brand = 'Sony') OR price < 100`).

This guide covers *how* to structure logical combinations, validate syntax, and optimize performance when using these operators.

---

## **Key Concepts & Implementation Details**

### **1. Operator Precedence**
Logical operators follow mathematical precedence:
1. `NOT` (highest)
2. `AND`
3. `OR` (lowest)

Parentheses override precedence. Example:
```plaintext
NOT (A AND B) ≠ (NOT A) AND (NOT B)
```

### **2. Operator Types**
| Operator | Logical Meaning                 | Example                     |
|----------|---------------------------------|-----------------------------|
| `AND`    | Both conditions must be true    | `color="red" AND size="large"` |
| `OR`     | At least one condition must be true | `status="active" OR status="pending"` |
| `NOT`    | Inverts a condition             | `NOT expired`               |

### **3. Combining Operators**
- **Multiple `AND`/`OR`** (e.g., `(A AND B) OR (C AND D)`).
- **Nested conditions** (e.g., `NOT (A OR B)`).
- **Wildcard usage** (e.g., `NOT "invalid_*"`).

### **4. Performance Considerations**
- **Indexing**: Ensure indexed fields are used in `WHERE` clauses for speed.
- **Avoid Cartesian explosion**: Limit `OR` combinations to reduce unintended join results.
- **Grouping**: Use `AND` for tight constraints, `OR` for alternative paths (e.g., `OR` over `AND` for broader searches).

### **5. Syntax Variations**
- **Boolean fields**: Directly assign `TRUE/FALSE` (e.g., `active=true`).
- **Equality checks**: Prefer `=` over `==`.
- **Negation**: Use `NOT` for exclusion (e.g., `NOT NULL`, `NOT in [list]`).

---

## **Schema Reference**

### **Core Structure**
| **Component**       | **Description**                                                                 | **Format**                     | **Example**                          |
|---------------------|-------------------------------------------------------------------------------|--------------------------------|--------------------------------------|
| **Field**           | Target attribute for filtering.                                               | `[field_name]`                 | `category`, `status`                 |
| **Operator**        | Logical operator (`AND`, `OR`, `NOT`).                                       | `[operator]`                   | `AND`, `OR`, `!` (abbreviated `NOT`) |
| **Value**           | Literal, range, or list of values.                                            | `[value]`                      | `"premium"`, `2023-01-01`, `[1,2,3]`  |
| **Parentheses**     | Encloses sub-expressions to enforce precedence.                              | `([subquery])`                 | `(color="red" AND size="large")`     |
| **Wildcards**       | Supports partial matching (`*`, `?`).                                         | `[prefix*]` or `[*suffix]`     | `user_*`                             |

### **Operator Combinations Table**
| **Combination**          | **Syntax**                     | **Logical Meaning**                                                                 |
|--------------------------|--------------------------------|------------------------------------------------------------------------------------|
| Single condition         | `field=value`                  | Exact match                                                                         |
| AND-combined             | `field1=value1 AND field2=value2` | Both conditions must evaluate to `true`                                            |
| OR-combined              | `field=value1 OR field=value2`    | Either condition evaluates to `true`                                                |
| NOT negation             | `NOT field=value`              | Excludes matches where `field=value`                                                |
| Nested OR/AND            | `(field1=value1 OR field2=value2) AND field3=value3` | Combines nested logical blocks                                                     |
| Range with AND           | `field > 100 AND field < 200`    | Intersection of ranges (inclusive)                                                  |
| List with OR             | `field IN ["A", "B"] OR field IN ["C", "D"]` | Union of lists                                                                     |

---

## **Query Examples**

### **1. Boolean Filtering (Basic)**
- **Query**: `status="active" AND (type="premium" OR type="standard")`
- **Use Case**: Filter active users with either premium or standard subscriptions.

### **2. Exclusion Logic**
- **Query**: `NOT (region="EU" OR region="Asia")`
- **Use Case**: Exclude EU and Asian regions in a campaign (global focus).

### **3. Nested Complex Filter**
- **Query**: `((category="Electronics" AND brand="Sony") OR (category="Furniture" AND NOT discontinued))`
- **Use Case**: Find Sony electronics **or** non-discontinued furniture.

### **4. Wildcard Matching**
- **Query**: `product_name LIKE "*wireless*" AND (price > 50 OR (price <= 50 AND on_sale=true))`
- **Use Case**: Wireless products priced >50 or on-sale items <50.

### **5. Performance-Friendly Optimization**
- **Query**: `category="Books" AND (author="Tolkien" OR title LIKE "Lord%")`
  - *Note*: Index `author` and `title` for faster OR evaluation.
- **Anti-Query**: `NOT (category="Accessories" AND stock <= 10)`
  - *Note*: Rewrite as `category!="Accessories" OR stock > 10` where possible.

---

## **Related Patterns**

1. **[Filtering by Field Values](link)**
   - Discusses exact match, range, and list-based filtering.

2. **[Operator Precedence Management](link)**
   - Details how to enforce precedence in complex queries without parentheses.

3. **[Wildcard & Regex Patterns](link)**
   - Extends match logic with flexible string patterns (`*`, `?`, regex).

4. **[Phrase & Proximity Search](link)**
   - Combines logical operators with keyword proximity (e.g., `"quick brown fox"`).

5. **[Aggregation with Conditions](link)**
   - Uses `GROUP BY` with `HAVING` to filter aggregated results.

6. **[Dynamic Rule Engines](link)**
   - Implements rule-based systems combining logical operators for dynamic logic.

---

## **Best Practices**
1. **Clarify Intent**: Use parentheses explicitly for ambiguous queries.
2. **Test Edge Cases**: Validate queries with `NULL`, empty lists, or overlapping conditions.
3. **Document Complex Rules**: Add inline comments for nested logic or team collaboration.
4. **Leverage Caching**: Cache frequent combinations (e.g., `category="A" OR category="B"`).

---
**See Also**: For database-specific implementations (e.g., SQL `WHERE`, Elasticsearch `bool` query), consult the engine’s official documentation.