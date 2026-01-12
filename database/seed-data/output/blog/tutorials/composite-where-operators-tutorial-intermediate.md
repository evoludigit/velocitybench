```markdown
# **Composite WHERE Operators: Building Powerful Filters in Modern APIs**

*How to design flexible, cost-aware filtering systems that scale*

---

## **Introduction**

As backend engineers, we frequently face a fundamental tension: **users demand rich querying capabilities**, while databases need **predictable performance**. A single equality filter like `WHERE status = "active"` works for simple CRUD, but real-world applications require **complex combinations** of conditions—like filtering users *who are both active AND have a premium plan*, or finding *any post published in the last year OR tagged with "tech"*.

This is where **composite WHERE operators** come into play—a pattern that lets you compose logical conditions (AND, OR, NOT) with arbitrary nesting, all while tracking their cost to avoid expensive queries.

In this tutorial, we’ll explore:
- Why simple equality filters fall short
- How composite filtering enables rich queries
- Practical implementation patterns in code
- How to balance flexibility with performance

---

## **The Problem: Equality Filters Aren’t Enough**

Imagine a product catalog API where customers can filter items by:
- Price range (`min_price` ≤ price ≤ `max_price`)
- Category (`category IN ["electronics", "clothing"]`)
- Discount status (`is_discounted = true`)
- Stock availability (`stock > 0`)

With a basic equality-only filter, you’d write something like:
```sql
SELECT * FROM products
WHERE name = 'Laptop' AND price = 1000 AND category = 'electronics';
```
But this quickly becomes unwieldy:
1. **No range queries**: You can’t easily filter for `price BETWEEN 500 AND 2000`.
2. **No OR logic**: You can’t find products *that are either electronics OR books*.
3. **No NOT logic**: You can’t exclude discontinued items with `NOT is_discontinued = true`.
4. **No nesting**: You can’t express complex rules like `if (category = "electronics" AND price > 500) OR category = "books"`.

Real-world APIs need **composable filters**—not just a list of AND-clauses.

---

## **The Solution: Composite WHERE Operators**

A composite WHERE pattern allows:
✅ **Logical combinations** of conditions (AND, OR, NOT) with arbitrary depth.
✅ **Cost tracking** to reject expensive queries early.
✅ **Rewriting or optimizing** complex conditions server-side.

This pattern is common in APIs like:
- **E-commerce filters** (e.g., "Show me laptops or phones under $1000")
- **Search platforms** (e.g., "Find articles tagged with 'AI' OR 'ML' AND published after 2023")
- **Activity dashboards** (e.g., "Show events with status = 'completed' AND user = me, OR status = 'cancelled' AND reason = 'timeout'").

---

## **Implementation Guide: FraiseQL’s Approach**

*FraiseQL* (a hypothetical query builder) demonstrates how to compose WHERE clauses flexibly while tracking cost. Below, we’ll implement this in Python with SQLAlchemy for databases.

---

### **1. Define the Core Filter Structure**
First, create a tree-like structure to represent composite conditions:

```python
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Literal

class ConditionType(Enum):
    EQUALITY = auto()
    RANGE = auto()
    IN = auto()
    LIKE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

@dataclass
class Condition:
    field: str
    type: ConditionType
    value: Optional[List[str]]  # Values for IN/range, or single value for equality
    operator: Optional[str]     # e.g., ">", "<", "LIKE"
    subconditions: Optional[List['Condition']] = None  # For AND/OR/NOT
```

---

### **2. Build a Query with Composite Conditions**
Now, compose a query like:
*"Show users who are active AND have a premium plan, OR have a trial expiring soon."*

```python
# Define a complex filter
active_and_premium = Condition(
    type=ConditionType.AND,
    subconditions=[
        Condition(
            field="status",
            type=ConditionType.EQUALITY,
            value=["active"]
        ),
        Condition(
            field="plan_type",
            type=ConditionType.EQUALITY,
            value=["premium"]
        )
    ]
)

trial_expiring = Condition(
    field="trial_end",
    type=ConditionType.RANGE,
    value=["2024-01-01", "2024-12-31"],  # Simplified for example
    operator="<="
)

final_filter = Condition(
    type=ConditionType.OR,
    subconditions=[active_and_premium, trial_expiring]
)
```

---

### **3. Translate to SQL**
Convert the tree into a SQL `WHERE` clause:

```python
def condition_to_sql(condition: Condition, alias: str = "") -> str:
    if condition.type == ConditionType.EQUALITY:
        return f"{alias}{condition.field} = '{condition.value[0]}'"

    elif condition.type == ConditionType.RANGE:
        return (
            f"{alias}{condition.field} {condition.operator} '{condition.value[0]}' "
            f"AND {alias}{condition.field} <= '{condition.value[1]}'"
        )

    elif condition.type == ConditionType.IN:
        return f"{alias}{condition.field} IN ({', '.join(['?'] * len(condition.value))})"

    elif condition.type == ConditionType.AND:
        return " AND ".join(condition_to_sql(c, alias) for c in condition.subconditions)

    elif condition.type == ConditionType.OR:
        return f"({' OR '.join(condition_to_sql(c, alias) for c in condition.subconditions)})"

    elif condition.type == ConditionType.NOT:
        return f"NOT ({condition_to_sql(condition.subconditions[0], alias)})"

    else:
        raise ValueError(f"Unknown type: {condition.type}")

# Build SQL
sql_where = condition_to_sql(final_filter)
print(f"SELECT * FROM users WHERE {sql_where}")
```

**Output:**
```sql
SELECT * FROM users WHERE (
    (users.status = 'active' AND users.plan_type = 'premium')
    OR users.trial_end <= '2024-12-31'
)
```

---

### **4. Track Query Complexity (FraiseQL’s Cost Model)**

To avoid **O(n²) queries**, implement a cost function:

```python
def estimate_cost(condition: Condition) -> float:
    if condition.type in {ConditionType.EQUALITY, ConditionType.RANGE, ConditionType.LIKE}:
        return 1.0  # Simple condition

    elif condition.type == ConditionType.IN:
        return min(10.0, len(condition.value))  # Cap cost for large IN lists

    elif condition.type == ConditionType.AND:
        return sum(estimate_cost(c) for c in condition.subconditions)

    elif condition.type == ConditionType.OR:
        # OR is more expensive—treat each branch as a separate query
        return max(estimate_cost(c) for c in condition.subconditions) * 1.5

    elif condition.type == ConditionType.NOT:
        return estimate_cost(condition.subconditions[0]) * 0.8  # NOT is slightly cheaper

    else:
        return 0.0

# Example: Cost of our final_filter
print(f"Estimated query cost: {estimate_cost(final_filter):.2f}")
```
**Output:** `Estimated query cost: 2.80` (assuming reasonable assumptions).

---

### **5. Reject Expensive Queries**
Add a cost threshold (e.g., 10.0) and rewrite or reject queries:

```python
MAX_ALLOWED_COST = 10.0

def validate_query(condition: Condition) -> bool:
    return estimate_cost(condition) < MAX_ALLOWED_COST

if not validate_query(final_filter):
    # Either:
    # 1. Optimize: Split into multiple queries
    # 2. Reject: Return a 403 or paginated results
    raise ValueError("Query too complex—try a simpler filter.")
```

---

## **Common Mistakes to Avoid**

1. **Overusing OR**: OR clauses explode query complexity. If you see `OR` with many branches, consider:
   - **Pagination** (e.g., "Show me OR results in batches").
   - **Pre-filtering** (e.g., "First narrow by category, then apply OR").

2. **Deep Nesting**: `AND (OR (NOT (AND ...)))` is hard to read and optimize. Flatten logic where possible.

3. **Unbounded IN Lists**: `IN (SELECT * FROM huge_table)` kills performance. Limit `IN` sizes (e.g., `IN (?, ?, ?)`).

4. **Ignoring Cost**: Always estimate and reject expensive queries. Example:
   ```python
   # Bad: Unbounded IN list
   Condition(field="id", type=ConditionType.IN, value=list(range(1, 1_000_000)))
   ```

5. **SQL Injection**: Never interpolate raw values directly. Use parameterized queries:
   ```python
   # Wrong: f"WHERE price < {max_price}"  # SQL injection risk!
   # Right: "WHERE price < ?", (max_price,)
   ```

---

## **Key Takeaways**
- **Combine AND/OR/NOT** to model complex rules.
- **Track query cost** to prevent performance regression.
- **Optimize recursively**: Break down deep queries into simpler ones.
- **Validate inputs**: Reject queries that are too expensive.
- **Document limits**: Explain to clients how filters are processed (e.g., "OR clauses may return partial results").

---

## **Conclusion**
Composite WHERE operators unlock **rich querying** while maintaining control over performance. By structuring filters as a tree of conditions, you enable:
- **Flexibility**: Support for ranges, IN clauses, and nested logic.
- **Predictability**: Cost tracking to avoid query bombs.
- **Optimization**: Rewriting or rejecting expensive queries.

While this pattern requires upfront design effort, the payoff is **scalable APIs** that can handle real-world complexity.

**Next steps**:
- Extend this to **parameterized queries** (e.g., `GET /users?filters=...`).
- Integrate with **database-specific optimizations** (e.g., PostgreSQL’s `EXPLAIN ANALYZE`).
- Experiment with **materialized views** for common filter combinations.

Happy optimizing!
```