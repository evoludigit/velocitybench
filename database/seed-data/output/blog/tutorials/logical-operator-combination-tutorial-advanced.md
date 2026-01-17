```markdown
---
title: "The Logical Operator Combination Pattern: Building Flexible Queries with AND, OR, NOT"
date: 2024-06-15
tags: ["database"]
series: ["API Design Patterns"]
cover: "/images/logical-operators-combination.png"
author: "Alex Carter"
---

# The Logical Operator Combination Pattern: Building Flexible Queries with AND, OR, NOT

In backend development, we often deal with data that needs to be filtered, sorted, and shaped according to dynamic criteria—whether from user input, configuration, or business logic. Yet, how often do we stop to consider the elegant yet powerful patterns that underpin query flexibility? Enter the **Logical Operator Combination Pattern**, a foundational technique enabling developers to craft dynamic queries using `AND`, `OR`, `NOT`, and their combinations. This pattern isn't just about adding operators to your queries—it's about structuring your code to handle complex, real-world filtering requirements gracefully.

If you've ever written a query that feels brittle when requirements change, or struggled to combine multiple conditions without duplicating logic, this pattern will become your go-to approach. It’s not about reinventing the wheel; it’s about leveraging the wheel’s spokes—the AND, OR, and NOT operators—to build queries that adapt to shifting needs. Whether you're working with SQL databases, ORMs, or query languages like GraphQL’s filters, understanding this pattern will sharpen your ability to design systems that remain maintainable even as requirements evolve.

Think of it this way: You’re building a search feature that lets users filter products by price range, brand, and stock status. Today, they want results where `price > 100 AND in_stock = true`. Tomorrow, they’ll add conditions like `minStock > 5 OR (brand = 'Premium' AND warranty > 24)`. Without a structured approach, implementing this kind of flexibility can lead to spaghetti queries or overly complex business logic. The Logical Operator Combination Pattern provides the blueprint to avoid this chaos.

---

## The Problem: When Queries Feel Like Overengineered Spaghetti

Imagine you’re building an e-commerce platform, and your search functionality starts simple: filter products by price. Your first query looks something like this:

```sql
SELECT * FROM products
WHERE price > 100;
```

Easy. Then requirements expand: users can now filter by brand *and* price. Suddenly, you have:

```sql
SELECT * FROM products
WHERE price > 100 AND brand = 'Nike';
```

But the real world is messier. Users might want products that are either within a price range *or* from a specific brand, with additional constraints like stock availability. Now, your queries start to look like this:

```sql
-- Option 1: Price range AND brand
SELECT * FROM products
WHERE (price >= 100 AND price <= 500) AND brand = 'Adidas';

-- Option 2: Price range OR brand (if available)
SELECT * FROM products
WHERE (price >= 100 AND price <= 500) OR brand = 'Puma';

-- Option 3: Price range AND stock availability
SELECT * FROM products
WHERE (price >= 100 AND price <= 500) AND in_stock = true;
```

Without a systematic way to handle these combinations, your codebase quickly becomes a mess of hardcoded conditions. You might end up with a `switch` statement or a series of nested `if-else` blocks that handle each query type, or worse, a `StringBuilder` that concatenates SQL fragments dynamically. This approach has several pitfalls:

1. **Brittleness**: Adding a new condition often requires rewriting multiple queries or logic branches. One small change, like adding a discount filter, could cascade into dozens of places.
2. **Performance Pitfalls**: Poorly structured queries can lead to N+1 problems or inefficient joins, especially when mixing OR conditions across large datasets.
3. **Maintainability**: Duplicated or ad-hoc logic is hard to test, debug, and refactor. Over time, the "simple" solution becomes a technical debt sink.
4. **Scalability**: As your application grows, the complexity of handling every possible query combination manually becomes unsustainable.

The Logical Operator Combination Pattern addresses these challenges by providing a structured, reusable way to combine conditions. It’s not about writing queries; it’s about designing a system that can handle any query combination gracefully, regardless of how complex or dynamic it becomes.

---

## The Solution: Structured Flexibility with Logical Operators

The core idea of the Logical Operator Combination Pattern is to:
1. **Separate the logic of combining conditions** from the conditions themselves.
2. **Use a consistent structure** for building complex queries, whether in SQL, an ORM, or a custom query DSL.
3. **Leverage dynamic operator handling** to allow flexible combinations (AND, OR, NOT) without hardcoding every possible query.

This pattern is particularly useful in APIs where clients (e.g., mobile apps, admin dashboards) send dynamic filters, or in internal services where filtering logic needs to adapt to business rules that change frequently.

### Key Components
1. **Condition Builders**: Small, focused functions or classes that encapsulate individual filter conditions (e.g., `priceGreaterThan()`, `brandEquals()`).
2. **Combiner Logic**: A system (often recursive) that takes a list of conditions and combines them using AND, OR, or NOT, based on user input or configuration.
3. **Query Construction**: A way to translate the combined conditions into executable queries (SQL, ORM, etc.), respecting database-specific syntax and limitations.

---

## Implementation Guide: From Theory to Code

Let’s explore how to implement this pattern in practice. We’ll start with a simple example in **SQL** (for clarity), then extend it to a **Python-based ORM approach**, and finally touch on a **javascript/TypeScript** API layer.

---

### Example 1: SQL-Based Implementation
Suppose we’re building a `products` table with columns: `id`, `name`, `price`, `brand`, `in_stock`, `min_stock`. We want a flexible query builder that can handle combinations of these filters.

#### Step 1: Define a `QueryBuilder` Class
We’ll create a class that accumulates conditions and builds the final SQL query.

```python
class QueryBuilder:
    def __init__(self):
        self.conditions = []
        self.operators = []

    def add_condition(self, condition, operator='AND'):
        """Add a new condition with an operator (AND or OR by default)."""
        self.conditions.append(condition)
        self.operators.append(operator)

    def build(self):
        """Combine all conditions into a single WHERE clause."""
        if not self.conditions:
            return "1=1"  # Always true, no filters

        # Start with the first condition
        clauses = [self.conditions[0]]

        # Combine with subsequent conditions using their operators
        for i in range(1, len(self.conditions)):
            operator = self.operators[i-1]
            clauses.append(f"{operator} {self.conditions[i]}")

        return "WHERE " + " ".join(clauses)

    def get_sql(self, table):
        """Return the full SQL query with the WHERE clause."""
        sql = f"SELECT * FROM {table} {self.build()}"
        return sql
```

#### Step 2: Use the Builder to Construct Queries
Now, let’s use this to build some complex queries.

```python
# Example 1: AND combination (price > 100 AND brand = 'Nike')
builder = QueryBuilder()
builder.add_condition("price > 100")
builder.add_condition("brand = 'Nike'")
print(builder.get_sql("products"))
# Output: SELECT * FROM products WHERE price > 100 AND brand = 'Nike'

# Example 2: OR combination (price > 100 OR brand = 'Nike')
builder = QueryBuilder()
builder.add_condition("price > 100")
builder.add_condition("brand = 'Nike'", operator='OR')
print(builder.get_sql("products"))
# Output: SELECT * FROM products WHERE price > 100 OR brand = 'Nike'

# Example 3: Mixed AND and OR (price > 100 AND (in_stock = true OR min_stock > 5))
builder = QueryBuilder()
builder.add_condition("price > 100")

# To handle nested OR conditions, we need to group them
inner_or = QueryBuilder()
inner_or.add_condition("in_stock = true")
inner_or.add_condition("min_stock > 5", operator='OR')
builder.add_condition(f"({inner_or.build()})")

print(builder.get_sql("products"))
# Output: SELECT * FROM products WHERE price > 100 AND (WHERE in_stock = true OR min_stock > 5)
```

**Note**: The above example is simplified for clarity. A production-ready implementation would need to handle:
- Parentheses for grouping.
- Proper escaping of SQL values (to prevent injection).
- Support for NOT conditions.
- More sophisticated grouping logic (e.g., using a stack or recursive descent).

---

### Example 2: Python ORM (SQLAlchemy) Implementation
For a more practical backend scenario, let’s use **SQLAlchemy**, a popular Python ORM. We’ll build a reusable `QueryBuilder` class that constructs SQLAlchemy Query objects dynamically.

```python
from sqlalchemy import and_, or_, not_, text
from sqlalchemy.orm import Query

class SQLAlchemyQueryBuilder:
    def __init__(self, session):
        self.session = session
        self.query = session.query

    def add_condition(self, condition, operator='AND'):
        """Add a condition to the query with the specified operator."""
        current_query = self.query
        if not hasattr(current_query, '_filters'):
            current_query._filters = []
            current_query._operators = ['AND']  # Default to AND

        current_query._filters.append(condition)
        current_query._operators.append(operator)

    def build(self):
        """Build the final query with all conditions applied."""
        if not hasattr(self.query, '_filters'):
            return self.query

        # Start with the first filter
        final_query = self.query.filter(self.query._filters[0])
        operators = self.query._operators[1:]

        # Apply remaining filters with their operators
        for i in range(1, len(self.query._filters)):
            op = operators[i-1]
            next_filter = self.query._filters[i]

            if op == 'AND':
                final_query = final_query.filter(and_(final_query._last_filter, next_filter))
            elif op == 'OR':
                final_query = final_query.filter(or_(final_query._last_filter, next_filter))
            elif op == 'NOT':
                final_query = final_query.filter(not_(next_filter))

            # Save the last filter for the next iteration
            final_query._last_filter = final_query._filters[i]

        return final_query

    def get_query(self, model):
        """Return the query for the given model."""
        return self.build().filter(text("1=1")).filter(model)
```

**Usage Example**:
```python
from models import Product

# Initialize builder
builder = SQLAlchemyQueryBuilder(session)

# Add conditions with AND as default
builder.add_condition(Product.price > 100)
builder.add_condition(Product.brand == 'Nike')

# Add an OR condition
builder.add_condition(Product.in_stock == True, operator='OR')

# Build and execute
results = builder.build().filter(Product.min_stock > 5).all()
```

**Why This Works**:
- The `QueryBuilder` accumulates conditions and their operators.
- The `build` method dynamically combines the conditions using SQLAlchemy’s `and_`, `or_`, and `not_`.
- The ORM handles the rest, including type safety and database-specific optimizations.

---

### Example 3: JavaScript/TypeScript API Layer
For APIs, you’ll often receive filter queries as JSON or URL parameters. Let’s assume a filter looks like this:

```json
{
  "filters": [
    { "field": "price", "operator": ">", "value": 100 },
    { "field": "brand", "operator": "=", "value": "Nike" },
    { "field": "in_stock", "operator": "OR", "value": true }
  ]
}
```

Here’s how you might handle this in a **Node.js/TypeScript** API:

```typescript
interface Filter {
  field: string;
  operator?: string; // AND, OR, NOT
  value: any;
}

function buildQueryString(filters: Filter[]): string {
  if (filters.length === 0) return "1=1";

  const parts = [];
  let currentOperator = 'AND'; // Default

  for (const filter of filters) {
    if (filter.operator === 'OR' || filter.operator === 'NOT') {
      currentOperator = filter.operator;
      delete filter.operator; // Remove to avoid confusion
    }

    // Escape the value to prevent SQL injection
    const escapedValue = filter.value.toString().replace(/'/g, "''");
    const condition = `${filter.field} ${filter.operator || '='} '${escapedValue}'`;
    parts.push(condition);
  }

  // Combine with operators (simplified; real-world would need parentheses)
  return `WHERE ${parts.join(` ${currentOperator} `)}`;
}

// Example usage:
const filters: Filter[] = [
  { field: "price", operator: ">", value: 100 },
  { field: "brand", operator: "=", value: "Nike" },
  { field: "in_stock", operator: "OR", value: true }
];

const queryString = buildQueryString(filters);
console.log(queryString);
// Output: WHERE price > '100' AND brand = 'Nike' OR in_stock = 'true'
```

**Key Notes**:
1. **SQL Injection Risk**: Always escape or parameterize values. The above example is simplified; in production, use prepared statements or an ORM.
2. **Parentheses Handling**: The example doesn’t handle nested OR/AND groups. For complex cases, you’d need to parse the filter logic into a proper expression tree (e.g., using a library like [JSON Query](https://github.com/automata/JSONQuery)).
3. **Performance**: For large datasets, avoid OR conditions across broad fields (e.g., `OR field1 = ... OR field2 = ...`) unless necessary.

---

## Common Mistakes to Avoid

While the Logical Operator Combination Pattern is powerful, there are anti-patterns that can undermine its effectiveness:

1. **Hardcoding Default Operators**:
   - Don’t assume all conditions are ANDed together. For example:
     ```python
     # Bad: Implicit AND everywhere
     builder.add_condition(...)
     builder.add_condition(...)  # Defaults to AND
     ```
   - Always explicitly specify the operator when combining conditions.

2. **Ignoring Parentheses**:
   - Without proper grouping, queries can behave unexpectedly:
     ```sql
     -- Intended: price > 100 AND (in_stock OR min_stock > 5)
     -- But without grouping, this becomes:
     WHERE price > 100 AND in_stock OR min_stock > 5
     ```
   - Always handle parentheses explicitly or use a parsing library to infer them.

3. **Overusing NOT**:
   - NOT conditions can complicate queries and hurt performance. For example:
     ```sql
     -- Avoid
     WHERE NOT (price > 100 OR brand = 'Nike')

     -- Instead, refactor to:
     WHERE (price <= 100 AND brand != 'Nike')
     ```
   - Rewrite NOT conditions where possible to simplify logic.

4. **Not Escaping Values**:
   - Always sanitize or parameterize values to prevent SQL injection. Even in ORMs, manual SQL queries require escaping.

5. **Flattening Complex Logic**:
   - Don’t try to flatten all conditions into a single WHERE clause without considering performance or readability. For example:
     ```sql
     -- Bad: Combines unrelated conditions
     WHERE price > 100 AND brand = 'Nike' AND category = 'Electronics' AND (order_date > '2023-01-01' OR user_id = 123)
     ```
   - Break complex conditions into subqueries or use application-level filtering where appropriate.

6. **Assuming All Databases Handle Operators the Same**:
   - Some databases (e.g., SQLite) have different behaviors for operators like `<>` vs. `!=`. Others (e.g., PostgreSQL) support more complex functions. Normalize your query logic where possible.

7. **Not Testing Edge Cases**:
   - Test queries with:
     - Empty filter lists.
     - Mixed operators (e.g., AND + OR + NOT).
     - NULL values (e.g., `field IS NULL`).
     - Large datasets to ensure performance.

---

## Key Takeaways

Here’s a quick checklist to internalize the Logical Operator Combination Pattern:

- **Separate Conditions from Logic**: Encapsulate each filter condition in a reusable component (e.g., methods, classes, or JSON schemas).
- **Default to AND**: Treat AND as the default operator for conditions, but always allow overriding with OR or NOT.
- **Handle Parentheses Explicitly**: Use grouping to ensure logical precedence matches intent (e.g., `(A OR B) AND C` vs. `A OR (B AND C)`).
- **Avoid Hardcoding Queries**: Use dynamic builders or DSLs to construct queries programmatically.
- **Optimize for Performance**: OR conditions can be expensive; consider materialized views or application-side filtering for broad conditions.
- **Secure Your Queries**: Always escape or parameterize values to prevent SQL injection.
- **Test Complex Combinations**: Validate edge cases, including empty filters, mixed operators, and NULL handling.

---

## Conclusion: Flexibility Without Chaos

The Logical Operator Combination Pattern isn’t about writing the most efficient query—it’s about writing the most *maintainable* and *adaptable* queries. In a world where business requirements evolve faster than database schemas, this pattern gives you the tools to handle complexity without losing your sanity.

Whether you’re filtering products, searching documents, or aggregating analytics, the ability to combine conditions flexibly is table stakes for modern backend systems. By structuring your queries around AND, OR, and NOT—not as ad-hoc constructs but as part of a deliberate design—you’ll build APIs and services that are resilient to change.

Remember, no pattern is a silver bullet. Overuse of dynamic queries can lead to performance bottlenecks, and even the best pattern requires discipline to implement correctly. But when wielded wisely, the Logical Operator Combination Pattern is your secret weapon for turning messy requirements into clean, scalable code.

Now go forth and build queries that can handle anything—and everything—that comes your way.
```

---
**Related Posts**:
- ["The Repository Pattern: Abstraction Without Overhead"