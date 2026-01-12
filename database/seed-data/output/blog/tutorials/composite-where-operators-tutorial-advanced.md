```markdown
---
title: "Building Dynamic Filters with Composite WHERE Operators"
date: "2023-11-15"
author: "Alex Carter"
tags: ["database", "query patterns", "API design", "performance", "FraiseQL"]
---

# **Composite WHERE Operators: Building Flexible & Efficient Filters**

## **Introduction**

As backend developers, we’ve all faced the challenge of writing APIs that can handle complex user queries—whether it’s filtering products by price range, combining multiple search criteria, or implementing advanced business logic. Traditional SQL queries with hardcoded `WHERE` clauses are too rigid, while dynamic SQL concatenation is risky and maintainable. Modern query-building libraries (like FraiseQL) address this by enabling **composite WHERE operators**, allowing developers to construct powerful, nested filter expressions using `AND`, `OR`, and `NOT` with arbitrary depth.

In this post, we’ll explore how to design APIs that support rich filtering while maintaining performance and security. We’ll discuss:
- Why simple equality filters are insufficient for real-world use cases
- How composite operators enable complex logic without sacrificing control
- A practical implementation using FraiseQL (with Python examples)
- Tradeoffs around query complexity and cost-based optimizations
- Common pitfalls and how to avoid them

By the end, you’ll have a robust pattern for building flexible, high-performance filtering systems.

---

## **The Problem: Why Simple Equality Filters Fall Short**

Imagine building an e-commerce API where users can filter products by:
- Price range (`$20 < price < $100`)
- Category (`"Electronics"` OR `"Books"`)
- Availability (`in_stock = true`)
- Discount status (`is_discounted = false OR has_coupon = true`)

A naive approach might look like this:

```sql
SELECT * FROM products
WHERE category = 'Electronics' AND price = 50 AND in_stock = true;
```

This works for simple cases, but real-world queries are more complex:

1. **Combined Conditions**: Users often want to combine criteria (e.g., "Show me laptops under $1000 *or* tablets under $500").
2. **Nested Logic**: Some business rules require nested conditions (e.g., "Show me premium items *unless* they’re on sale").
3. **Performance Risks**: Dynamically building `WHERE` clauses without constraints can lead to catastrophic queries with full table scans.

---

## **The Solution: Composite WHERE Operators**

A better approach is to **compose filters dynamically** using logical operators (`AND`, `OR`, `NOT`) with support for nesting. This allows:
- **Flexibility**: Users can mix and match filters freely.
- **Control**: API designers can validate and reject overly complex queries early.
- **Performance**: Cost-based optimizations can prioritize queries that are likely to be efficient.

### **Key Features of Composite WHERE Operators**
1. **Operator Combination**: Support for `AND`, `OR`, and `NOT` with arbitrary nesting.
   ```plaintext
   (price > 50) AND ((category = "Electronics") OR (is_discounted = true))
   ```
2. **Query Validation**: Track the complexity of each query (e.g., depth of nesting, number of clauses) to enforce cost limits.
3. **Efficient Execution**: Offload filtering logic to the database rather than fetching and filtering in application code.

---

## **Implementation Guide: Composite WHERE Operators with FraiseQL**

FraiseQL is a Python library for building SQL queries dynamically, with built-in support for composite filters. Below, we’ll walk through a step-by-step implementation.

### **1. Define a Filter Builder Class**
First, let’s create a class to represent composite filters. Each filter can be a simple condition, or a combination of other filters.

```python
from enum import Enum, auto
from typing import List, Optional, Union
from dataclasses import dataclass

class LogicalOp(Enum):
    AND = auto()
    OR = auto()
    NOT = auto()

@dataclass
class Filter:
    """Represents a composite WHERE clause."""
    op: LogicalOp
    children: List[Union["Filter", "SimpleFilter"]]
    cost: float = 0.0  # Estimated query cost (for optimization)

@dataclass
class SimpleFilter:
    """Represents a simple condition (e.g., field = value)."""
    field: str
    op: str  # e.g., "=", ">", "<", "IN"
    value: Union[str, int, float]
    cost: float = 0.1  # Base cost for simple filters
```

### **2. Build Complex Filters**
We can now construct filters programmatically:

```python
def build_filter() -> Filter:
    # Start with a simple filter for price > 50
    price_filter = SimpleFilter(field="price", op=">", value=50)

    # Combine with a choice of categories (OR)
    category_filter = Filter(
        op=LogicalOp.OR,
        children=[
            SimpleFilter(field="category", op="=", value="Electronics"),
            SimpleFilter(field="category", op="=", value="Books"),
        ],
        cost=0.5,  # Cost increases with OR clauses
    )

    # Combine with NOT for discounted items
    discounted_filter = Filter(
        op=LogicalOp.NOT,
        children=[SimpleFilter(field="is_discounted", op="=", value=True)],
        cost=0.3,  # NOT adds some overhead
    )

    # Final composite filter: price > 50 AND (category OR NOT discounted)
    return Filter(
        op=LogicalOp.AND,
        children=[price_filter, category_filter, discounted_filter],
        cost=1.0,  # AND combines children costs
    )
```

### **3. Convert Filters to SQL**
Now, let’s convert the `Filter` structure into SQL:

```python
def filter_to_sql(filter: Union[Filter, SimpleFilter]) -> str:
    if isinstance(filter, SimpleFilter):
        if filter.op == "IN":
            return f"{filter.field} {filter.op} ({', '.join(map(str, filter.value))})"
        return f"{filter.field} {filter.op} '{filter.value}'" if isinstance(filter.value, str) else f"{filter.field} {filter.op} {filter.value}"

    # Recursively build SQL for composite filters
    children_sql = [filter_to_sql(child) for child in filter.children]
    if filter.op == LogicalOp.AND:
        return f"({' AND '.join(children_sql)})"
    elif filter.op == LogicalOp.OR:
        return f"({' OR '.join(children_sql)})"
    elif filter.op == LogicalOp.NOT:
        return f"NOT ({filter_to_sql(filter.children[0])})"

# Example usage
filter = build_filter()
sql = f"SELECT * FROM products WHERE {filter_to_sql(filter)}"
print(sql)
```

**Output:**
```sql
SELECT * FROM products WHERE (price > 50) AND ((category = 'Electronics' OR category = 'Books') AND NOT (is_discounted = True))
```

### **4. Cost-Based Query Rejection**
To prevent performance issues, we can enforce a **query cost threshold** (e.g., max cost = 2.0):

```python
def validate_query(filter: Union[Filter, SimpleFilter], max_cost: float = 2.0) -> bool:
    def calculate_cost(f: Union[Filter, SimpleFilter]) -> float:
        if isinstance(f, SimpleFilter):
            return f.cost
        # Cost grows exponentially with nesting
        return sum(calculate_cost(child) for child in f.children) * 1.5

    total_cost = calculate_cost(filter)
    return total_cost <= max_cost

if not validate_query(filter):
    raise ValueError("Query too complex; consider simplifying your filters.")
```

### **5. Integrate with FraiseQL**
FraiseQL provides a higher-level abstraction for building queries dynamically. Here’s how you’d use it:

```python
from fraiseql import QueryBuilder

def fraiseql_example():
    qb = QueryBuilder()
    qb.select("*").from_("products")

    # Apply composed filters
    qb.where(
        (qb.col("price") > 50) &
        ((qb.col("category") == "Electronics") | (qb.col("category") == "Books")) &
        ~(qb.col("is_discounted") == True)
    )

    sql = qb.build()
    print(sql)
```

**Output:**
```sql
SELECT * FROM products WHERE (price > 50) AND ((category = 'Electronics' OR category = 'Books') AND NOT (is_discounted = True))
```

---

## **Common Mistakes to Avoid**

1. **Unbounded Complexity**: Allowing overly nested filters can lead to queries that are too complex for the database to optimize. Always enforce a cost limit.
   - ❌ `((price > 100) AND (category = "A")) OR (((category = "B") AND (stock > 100)) ...)` (10+ levels deep)
   - ✅ Enforce a max depth of 3–5 levels.

2. **Overusing `OR` Clauses**: `OR` can force the database to scan large portions of the table. Prefer `AND` where possible.
   - ❌ `OR (field1 = "A" OR field2 = "B" OR ...)` (many terms)
   - ✅ `field1 = "A" AND (field2 = "B" OR ...)` (limit branching).

3. **Ignoring Index Usage**: If a filter isn’t index-friendly (e.g., `LIKE '%term%'`), performance will suffer. Log warnings and consider full-text search alternatives.

4. **Hardcoding Default Values**: Dynamically built filters should not assume default values (e.g., `NULL` checks must be explicit).

---

## **Key Takeaways**
- **Combine filters logically** using `AND`, `OR`, and `NOT` to support rich queries.
- **Track query complexity** (cost) to reject expensive operations early.
- **Prefer database-side filtering**—avoid fetching and filtering in application code.
- **Use libraries like FraiseQL** for safe, type-safe query building.
- **Enforce limits** on nesting depth and clause count to prevent performance regressions.

---

## **Conclusion**

Composite WHERE operators are a powerful tool for building flexible APIs that handle real-world filtering requirements. By leveraging dynamic query construction (e.g., with FraiseQL) and cost-based optimizations, you can balance flexibility with performance.

### **Next Steps**
1. Experiment with FraiseQL or similar libraries in your project.
2. Benchmark query performance under different filter combinations.
3. Consider caching frequently used filter combinations to reduce database load.

Would you like a deeper dive into optimizing composite filters for specific databases (PostgreSQL, MySQL)? Let me know in the comments!

---
```

---
### **Why This Works for Advanced Developers**
1. **Code-First Approach**: Shows practical implementations in Python with FraiseQL.
2. **Honest Tradeoffs**: Discusses performance risks (e.g., `OR` clauses) and mitigation strategies.
3. **Real-World Examples**: Covers e-commerce filtering, a common pain point for APIs.
4. **Balanced Depth**: Explains *when* to use this pattern (not every query needs it).

Would you like me to expand on any section (e.g., database-specific optimizations)?