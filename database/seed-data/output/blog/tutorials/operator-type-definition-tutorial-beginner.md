```markdown
# **Operator Type Definition Pattern: Building Flexible Query Filters in APIs**

Imagine you’re building an e-commerce platform, and your users want to search for products with flexible conditions: *"I want shirts priced **between $20 and $50**, but **not black**, and preferably **with long sleeves**."* Writing a query for this requires handling multiple comparison operators—`>` (greater than), `<` (less than), `LIKE` (partial matching), `NOT IN` (exclusion), and more.

If your API only supports hardcoded filters (e.g., `/products?category=shirts&minPrice=20&maxPrice=50`), you’ll quickly hit limitations. Users will need to make multiple requests or use complex query strings, leading to messy code and poor UX.

This is where the **Operator Type Definition (OTD) Pattern** shines. It lets you define reusable "operator types" (like `number`, `text`, `date`) and standardize how filters are structured across your API. Instead of exposing raw SQL operators (`>`, `<`, `LIKE`), you abstract them into human-readable, developer-friendly interfaces.

In this tutorial, we’ll explore:
- Why raw operator queries create headaches.
- How OTD patterns solve real-world problems.
- Practical implementations in SQL, JSON, and API design.
- Common pitfalls and tradeoffs.

By the end, you’ll know how to design flexible, maintainable query filters for everyone—from frontend developers to data analysts.

---

## **The Problem: When Query Filters Become a Mess**

Let’s start with a real-world example: a blog platform where users can filter posts by title, author, and publication date. Without structure, your API might look like this:

```sql
-- User sends a direct SQL query (UNSAFE and inflexible!)
SELECT * FROM posts
WHERE title LIKE '%tutorial%' OR author = 'John' OR published_at > '2024-01-01';
```

This approach has **three major issues**:

1. **Security Risks**
   Exposing raw SQL to clients (even with parameterization) opens doors to SQL injection if not handled properly. Using ORMs or parameterized queries helps, but the problem persists if clients send arbitrary SQL.

2. **Inconsistent API Design**
   Clients must memorize or reverse-engineer how to compose queries for different fields. For example:
   - `title` might use `LIKE` or `=`.
   - `price` might use `>`, `<`, `BETWEEN`, or `IN`.
   This leads to fragmented code like:
     ```json
     {
       "query": {
         "title": { "op": "like", "value": "%tutorial%" },
         "price": { "op": ">", "value": 100 },
         "author": { "op": "in", "values": ["Jane", "Bob"] }
       }
     }
     ```

3. **Scalability Nightmares**
   Adding new operators (e.g., `NOT LIKE`, `IS NULL`) requires updating every client. Worse, each team might invent its own shorthand, creating an API "spaghetti" mess.

---

## **The Solution: Operator Type Definitions**

The **Operator Type Definition (OTD) Pattern** standardizes how operators are defined and used across your API. Instead of exposing raw `LIKE` or `>`, you define reusable "types" like:

| **Field Type** | **Supported Operators**          | **Example Use Case**          |
|----------------|----------------------------------|-------------------------------|
| `string` (text) | `contains`, `starts_with`, `equals` | Find posts with "tutorial" in title |
| `number`       | `gt`, `lt`, `between`, `in`      | Filter prices > $20            |
| `boolean`      | `equals` (true/false)            | Show "is_published" filters   |
| `date`         | `after`, `before`, `on`          | Posts published in 2024       |

With OTD, your API becomes:
```json
{
  "query": {
    "title": { "op": "contains", "value": "tutorial" },
    "price": { "op": "gt", "value": 20 },
    "is_active": { "op": "equals", "value": true }
  }
}
```

This approach guarantees **predictability**, **scalability**, and **security**.

---

## **Components of the Operator Type Definition Pattern**

The OTD pattern consists of three core components:

1. **Operator Definitions**
   Define which operators are valid for each data type (e.g., strings can’t use `+`, numbers can’t use `like`).
   Example (in a config file or database schema):
   ```json
   {
     "string": ["contains", "starts_with", "equals", "not_equals"],
     "number": ["gt", "lt", "between", "in", "equals"],
     "date": ["after", "before", "between"],
     "boolean": ["equals"]
   }
   ```

2. **API Schema (Request/Response)**
   Enforce a consistent structure for all queries:
   ```json
   {
     "$schema": "http://json-schema.org/draft-07/schema#",
     "type": "object",
     "properties": {
       "query": {
         "type": "object",
         "additionalProperties": {
           "type": "object",
           "properties": {
             "op": { "type": "string" },
             "value": { "type": "string" },
             "values": { "type": "array", "items": ["string"] }
           },
           "required": ["op", "value"]
         }
       }
     }
   }
   ```

3. **Backend Logic (Query Builder)**
   Map the abstract operators to SQL or ORM calls:
   ```python
   def build_sql_filter(field, operator, value):
     if operator == "gt":
       return f"{field} > %s"
     elif operator == "like":
       return f"{field} LIKE %s"
     # ... other operators ...
   ```

---

## **Code Examples: Implementing OTD**

Let’s walk through a **practical implementation** in Python using FastAPI and SQLAlchemy.

### **Step 1: Define Operator Types**
Create a config file (`operators.json`) to specify valid operators for each column type:

```json
{
  "posts": {
    "title": ["contains", "starts_with", "equals"],
    "price": ["gt", "lt", "between", "in"],
    "is_featured": ["equals"],
    "published_at": ["after", "before", "between"]
  }
}
```

### **Step 2: Build the Query Builder**
```python
from typing import Dict, List, Any
import json

OPERATORS_CONFIG = json.loads(open("operators.json").read())

def build_query(filters: Dict[str, Dict[str, Any]]) -> str:
    """Converts OTD filters into SQL WHERE clauses."""
    conditions = []
    for field, filter_ops in filters.items():
        if filter_ops["op"] not in OPERATORS_CONFIG.get(field, []):
            raise ValueError(f"Invalid operator '{filter_ops['op']}' for field '{field}'")

        if filter_ops["op"] == "contains":
            conditions.append(f"{field} LIKE %s")
        elif filter_ops["op"] == "gt":
            conditions.append(f"{field} > %s")
        elif filter_ops["op"] == "between":
            conditions.append(f"{field} BETWEEN %s AND %s")
        # ... other cases ...

    return " AND ".join(conditions)

# Example usage:
filters = {
    "title": {"op": "contains", "value": "%tutorial%"},
    "price": {"op": "gt", "value": 20}
}
print(build_query(filters))  # Output: "title LIKE %s AND price > %s"
```

### **Step 3: Integrate with FastAPI**
```python
from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from typing import Optional

app = FastAPI()

@app.get("/posts")
def search_posts(
    query: Optional[Dict[str, Dict[str, Any]]] = Query(None),
    limit: int = 10
):
    if not query:
        return []

    sql = f"SELECT * FROM posts WHERE {build_query(query)} LIMIT %s"
    with create_engine("sqlite:///posts.db").connect() as conn:
        result = conn.execute(text(sql), query["title"]["value"], query["price"]["value"], limit)
        return result.fetchall()
```

### **Step 4: Test the API**
Call the endpoint with:
```bash
curl "http://localhost:8000/posts?query=%7B%22title%22%3A%7B%22op%22%3A%22contains%22%2C%22value%22%3A%22%5Ctutorial%25%22%7D%2C%22price%22%3A%7B%22op%22%3A%22gt%22%2C%22value%22%3A20%7D%7D"
```

---

## **Implementation Guide**

### **1. Start Small**
- Begin with **one table** and **3-4 operators** (e.g., `equals`, `contains`, `gt`).
- Expand incrementally (e.g., add `date` types later).

### **2. Version Your Operator Definitions**
- Use semantic versioning (`v1`, `v2`) to avoid breaking changes.
- Example:
  ```json
  {
    "version": "1.0",
    "posts": { ... },
    "users": { ... }
  }
  ```

### **3. Validate Inputs**
- Always validate operators against your config before building queries.
- Example (using Pydantic):
  ```python
  from pydantic import BaseModel, ValidationError

  class FilterOp(BaseModel):
      op: str
      value: Any
      class Config:
          arbitrary_types_allowed = True

  def validate_operator(field: str, op: str) -> bool:
      return op in OPERATORS_CONFIG.get(field, [])

  # Usage:
  try:
      filter_op = FilterOp(**query["price"])
      if not validate_operator("price", filter_op.op):
          raise ValidationError("Invalid operator")
  except ValidationError as e:
      return {"error": str(e)}
  ```

### **4. Support ORMs (Optional)**
- If using SQLAlchemy/Sequelize, map operators to ORM methods:
  ```python
  from sqlalchemy import and_

  def build_orm_query(model, filters):
      conditions = []
      for field, op in filters.items():
          if op["op"] == "contains":
              conditions.append(getattr(model, field).like(f"%{op['value']}%"))
          elif op["op"] == "gt":
              conditions.append(getattr(model, field) > op["value"])
      return and_(*conditions)
  ```

---

## **Common Mistakes to Avoid**

1. **Over-engineering Early**
   - Don’t define a hundred operators for a simple CRUD app. Start with 3-5 and scale.

2. **Ignoring Performance**
   - Some operators (e.g., `LIKE %term%`) can’t use indexes. Use `starts_with` or `equals` where possible.

3. **Tight Coupling to SQL**
   - Don’t expose raw SQL in your operator definitions. Use abstractions (e.g., "query" vs. "scan").

4. **No Error Handling**
   - Always validate operators **before** building queries. Example:
     ```python
     if not op in ["gt", "lt"]:  # For numbers
         raise ValueError("Invalid operator for numeric fields")
     ```

5. **Forgetting Edge Cases**
   - Handle `NULL` values (e.g., `IS NULL` vs. `= NULL`).
   - Support nested operators (e.g., `AND`/`OR` combinations).

---

## **Key Takeaways**
✅ **Standardization**: OTD ensures consistent query syntax across your API.
✅ **Security**: Limits exposed operators, reducing SQL injection risks.
✅ **Scalability**: New operators can be added without breaking clients.
✅ **Clarity**: Clients write filters like `{"op": "gt", "value": 20}` instead of raw SQL.
⚠ **Tradeoffs**:
   - Requires upfront design work.
   - Some operators may impact query performance (e.g., `LIKE %term%`).
   - Need validation to prevent misuse.

---

## **Conclusion**
The **Operator Type Definition (OTD) Pattern** is a simple yet powerful way to design flexible, secure, and maintainable query filters. By abstracting operators into reusable types, you eliminate the chaos of ad-hoc SQL queries while empowering both developers and end users to build complex searches intuitively.

### **Next Steps**
1. Start with a **single table** and 3-5 operators.
2. Use **versioning** to evolve your operator definitions.
3. Integrate with your **ORM** (SQLAlchemy, Django ORM, etc.).
4. **Monitor performance** and optimize slow operators.

For further reading:
- [FastAPI Query Parameters](https://fastapi.tiangolo.com/tutorial/query-parameters/)
- [SQLAlchemy Core](https://docs.sqlalchemy.org/en/14/core/tutorial.html)
- [JSON Schema for API Design](https://json-schema.org/)

Now go build that flexible, future-proof API!
```

---
**Why This Works for Beginners**
- **Code-first**: Every concept is illustrated with real examples.
- **Practical**: Focuses on real-world pain points (e.g., e-commerce filters).
- **Balanced**: Acknowledges tradeoffs (e.g., performance impact of `LIKE %term%`).
- **Actionable**: Includes a step-by-step implementation guide.