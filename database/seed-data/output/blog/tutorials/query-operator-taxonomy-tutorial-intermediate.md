```markdown
---
title: "The Query Operator Taxonomy: Building Flexible and Portable Filtering Systems"
date: 2023-11-15
author: Alex Carter
tags: ["database design", "API patterns", "filtering", "query composition", "PostgreSQL", "SQL"]
description: "Learn how to design flexible filtering systems with the Query Operator Taxonomy pattern, inspired by FraiseQL. Avoid forcing clients into awkward workarounds while maintaining database performance."
---

# The Query Operator Taxonomy: Building Flexible and Portable Filtering Systems

When you need to build an API that lets users filter complex data—think product search, analytics dashboards, or admin interfaces—you quickly run into a fundamental question: *How do you expose filtering capabilities without making the API rigid or overwhelming?* Too restrictive, and users can't express their needs; too open, and you risk bloat and performance problems.

This is where **the Query Operator Taxonomy** comes into play. Popularized by [FraiseQL](https://github.com/teamfrais/fraise), this pattern organizes a vast array of filtering operators into logical categories, ensuring your filtering system is expressive yet maintainable. With support for 150+ operators across 14 categories, it ensures flexibility without sacrificing readability or performance.

In this tutorial, we'll explore how to implement this pattern, starting from the problem of limiting filtering operators to the practical tradeoffs and code examples needed to build a robust solution.

---

## The Problem: Limited Filtering Operators Force Workarounds

Imagine you're building an API for a SaaS SaaS platform where users can filter "User" records based on fields like:

- **Basic fields**: `id`, `name`, `email`, `status`
- **Arrays**: `roles` (array of strings), `device_ids` (array of UUIDs)
- **Dates**: `created_at`, `last_login`
- **Nested data**: `address.city` within a JSON structure
- **Spatial data**: `coordinates` (geographic location)
- **Custom metadata**: `metadata` (JSONB field with arbitrary key-value pairs)

Without a thoughtful operator taxonomy, your API might initially support only basic comparisons like `=`, `<`, `>`, `LIKE`, and `IN`. But what happens when you need to support:

- **Partial matching**: Filter users whose `name` contains "John"
- **Array containment**: Users with roles `["admin"]` or `["user", "editor"]`
- **Date ranges**: Users active between `2023-01-01` and `2023-06-30`
- **Geospatial queries**: Users within 50km of a location
- **Nested field access**: Users living in "New York" (where `address.city` is nested in JSONB)

If your API only allows basic operators, you're forced to do one of the following:

1. **Expose raw SQL**: Let clients write arbitrary queries, which is insecure and unmanageable.
2. **Use a rigid schema**: Map every possible filter to a fixed API endpoint (e.g., `/users?status=active&name=John`), which becomes unwieldy as requirements grow.
3. **Overuse workarounds**: Use `IS NULL`, `IS NOT NULL`, or `LIKE` in creative ways, leading to unreadable code and performance issues.

This is where the Query Operator Taxonomy helps: it provides a structured way to expose filtering capabilities without losing flexibility.

---

## The Solution: A Taxonomy of Filtering Operators

The Query Operator Taxonomy organizes filtering operators into categories based on their use case and database compatibility. This approach has three key benefits:

1. **Clarity**: Operators are grouped logically, so clients can discover and use them intuitively.
2. **Portability**: The taxonomy can be implemented across multiple databases (PostgreSQL, MySQL, MongoDB) with minor adjustments.
3. **Extensibility**: New operators can be added without breaking existing APIs.

FraiseQL categorizes operators into 14 groups, but even a subset of these can solve 90% of filtering needs. Below is a simplified taxonomy inspired by FraiseQL, along with examples of how to implement it in a client-friendly API (e.g., GraphQL or REST with query parameters).

### Operator Taxonomy Categories and Examples

| **Category**         | **Database Support**       | **Operators**                                                                 | **Example Use Case**                          |
|----------------------|---------------------------|----------------------------------------------------------------------------|-----------------------------------------------|
| **Basic Comparison** | All                       | `=`, `!=`, `<`, `>`, `<=`, `>=`, `IS NULL`, `IS NOT NULL`, `BETWEEN` | `status = "active"`, `age > 18`               |
| **String/Text**      | All                       | `LIKE`, `ILIKE`, `~` (regex), `!~`, `CONTAINS`, `STARTS WITH`, `ENDS WITH` | `name LIKE %John%`, `email ~ ".*@example.com"` |
| **Arrays**           | PostgreSQL, MongoDB       | `IN`, `ALL`, `ANY`, `NOT IN`, `@>`, `->>`, `=ANY`, `?|`                  | `roles @> ["admin"]`, `device_ids = ANY(ARRAY[1, 2, 3])` |
| **JSONB (PostgreSQL)** | PostgreSQL               | `#>>`, `->`, `@>`, `->>`, `?`, `?|`, `?&`, `?&[]`               | `metadata #>> '{status}' = "complete"`        |
| **Date/Time**        | All                       | `BETWEEN`, `>`, `<`, `=`, `IS NULL`, `IS NOT NULL`, `DATE_TRUNC`          | `created_at BETWEEN '2023-01-01' AND '2023-12-31'` |
| **Geographic**       | PostgreSQL (PostGIS)      | `&&`, `<`, `>`, `ST_DWithin`, `ST_Contains`                                | `coordinates && ST_MakeEnvelope(-74, 40, -73, 41)` |
| **Vector**           | PostgreSQL (pgvector)     | `ST_Distance`, `ST_Similarity`, `ST_Within`                                 | `embedding ST_Similarity '0.9'`               |
| **Numeric**          | All                       | `+`, `-`, `*`, `/`, `MOD`, `ROUND`, `FLOOR`, `CEIL`                      | `price BETWEEN 100 AND 200`                   |
| **UUID**             | PostgreSQL, MongoDB       | `=`, `!=`, `IN`, `UUID_IS_VALID`                                           | `id = '123e4567-e89b-12d3-a456-426614174000'` |
| **Enum**             | All                       | `=`, `IN`, `IS NULL`, `IS NOT NULL`                                        | `status IN ["active", "inactive"]`            |
| **Boolean**          | All                       | `AND`, `OR`, `NOT`, `IS TRUE`, `IS FALSE`                                  | `active = true AND admin = false`             |

---

## Components/Solutions

To implement the Query Operator Taxonomy, you'll need the following components:

1. **Operator Registry**: A centralized map of operators categorized by type (e.g., `BasicComparison`, `JSONB`).
2. **Query Parser**: Converts client-provided filters into database-compatible queries (e.g., SQL, MongoDB queries).
3. **Database Adapter**: Maps operators to database-specific syntax (e.g., `@>` for array containment in PostgreSQL vs. `$elemMatch` in MongoDB).
4. **API Layer**: Exposes the taxonomy to clients (e.g., as a GraphQL filter input or REST query parameters).

Below, we'll focus on implementing this in a REST API with PostgreSQL, but the same principles apply to other databases.

---

## Code Examples: Building a Filtering API

### 1. Define the Operator Taxonomy

First, let's define a taxonomy of operators in Python (or your preferred language). This will map each category to its supported operators and database-specific syntax.

```python
# operators.py
from typing import Dict, List, Tuple, Optional

class OperatorTaxonomy:
    def __init__(self):
        self.taxonomy: Dict[str, Dict[str, List[OperatorSpec]]] = {
            "basic_comparison": {
                "operators": [
                    {"name": "equal", "sql": "=", "description": "Exact match"},
                    {"name": "not_equal", "sql": "!=", "description": "Not equal"},
                    {"name": "less_than", "sql": "<", "description": "Less than"},
                    {"name": "greater_than", "sql": ">", "description": "Greater than"},
                    {"name": "less_equal", "sql": "<=", "description": "Less than or equal"},
                    {"name": "greater_equal", "sql": ">=", "description": "Greater than or equal"},
                    {"name": "is_null", "sql": "IS NULL", "description": "Is null"},
                    {"name": "is_not_null", "sql": "IS NOT NULL", "description": "Is not null"},
                    {"name": "between", "sql": "BETWEEN", "description": "Between two values"},
                ],
                "description": "Basic field comparisons",
            },
            "string_text": {
                "operators": [
                    {"name": "contains", "sql": "LIKE", "description": "Contains substring (case-sensitive)"},
                    {"name": "icontains", "sql": "ILIKE", "description": "Contains substring (case-insensitive)"},
                    {"name": "regex", "sql": "~", "description": "Regex match (PostgreSQL)"},
                    {"name": "not_regex", "sql": "!~", "description": "Does not match regex"},
                    {"name": "starts_with", "sql": "LIKE", "left_pad": True, "description": "Starts with prefix"},
                    {"name": "ends_with", "sql": "LIKE", "right_pad": True, "description": "Ends with suffix"},
                ],
                "description": "String and text matching",
            },
            # Add more categories (arrays, JSONB, etc.) here...
        }

    def get_operators(self) -> Dict[str, List[Dict]]:
        return {category: ops["operators"] for category, ops in self.taxonomy.items()}

    def build_query_operator(self, operator_name: str, field: str, value: any) -> Tuple[str, str]:
        """
        Builds a SQL fragment for a given operator, field, and value.
        Returns (field_expression, sql_operator) or raises ValueError.
        """
        # Look through all operators to find a match
        for category, ops in self.taxonomy.items():
            for op in ops["operators"]:
                if op["name"] == operator_name:
                    sql_operator = op["sql"]
                    # Handle special cases (e.g., LIKE with wildcards)
                    if sql_operator == "LIKE" and operator_name in ["contains", "starts_with", "ends_with"]:
                        if operator_name == "contains":
                            value = f"%{value}%"
                        elif operator_name == "starts_with":
                            value = f"{value}%"
                        elif operator_name == "ends_with":
                            value = f"%{value}"
                    return f"{field}", sql_operator
        raise ValueError(f"Operator {operator_name} not found")
```

### 2. Parse Client Filters into SQL

Next, we'll create a simple parser that converts client input (e.g., `{"status": {"equal": "active"}, "name": {"contains": "John"}}`) into a PostgreSQL `WHERE` clause.

```python
# query_parser.py
from operators import OperatorTaxonomy
from typing import Dict, List

class QueryParser:
    def __init__(self):
        self.taxonomy = OperatorTaxonomy()

    def parse_filter(self, filters: Dict) -> str:
        """
        Parses a filter dictionary into a SQL WHERE clause.
        Example: {"status": {"equal": "active"}} -> "status = 'active'"
        """
        clauses = []
        for field, operators in filters.items():
            for op_name, op_value in operators.items():
                try:
                    field_expr, sql_op = self.taxonomy.build_query_operator(op_name, field, op_value)
                    # Handle special cases (e.g., JSONB, arrays)
                    if field.endswith("[]"):  # Array field
                        clauses.append(f"({field} {sql_op} ARRAY[{op_value}])")
                    elif field.startswith("metadata."):  # JSONB field
                        if sql_op == "=":
                            clauses.append(f"{field} = '{op_value}'::jsonb")
                        elif sql_op == "!=":
                            clauses.append(f"{field} != '{op_value}'::jsonb")
                    else:
                        clauses.append(f"{field} {sql_op} {self._quote_value(op_value)}")
                except ValueError as e:
                    raise ValueError(f"Invalid filter operator: {e}")
        return " AND ".join(clauses) if clauses else "1=1"  # Return "1=1" for empty filters

    def _quote_value(self, value: any) -> str:
        """
        Quotes values safely for SQL.
        """
        if isinstance(value, str):
            return f"'{value.replace("'", "''")}'"
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f"'{str(value).replace("'", "''")}'"
```

### 3. Integrate with a REST API

Now, let's integrate this with a Flask-like API (or FastAPI, Django, etc.) to handle incoming filters.

```python
# api.py
from flask import Flask, request, jsonify
from query_parser import QueryParser
import psycopg2
from psycopg2 import sql

app = Flask(__name__)
parser = QueryParser()

@app.route("/users", methods=["GET"])
def get_users():
    filters = request.args.get("filters", "{}")
    try:
        filters_dict = eval(filters)  # In production, use a proper JSON parser!
        where_clause = parser.parse_filter(filters_dict)

        conn = psycopg2.connect("dbname=test user=postgres")
        cursor = conn.cursor()

        query = sql.SQL("""
            SELECT * FROM users
            WHERE {}
        """).format(sql.SQL(where_clause))

        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"users": users})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
```

### 4. Example API Requests

With this setup, clients can now make requests like:

```
# Filter users with status "active" and name containing "John"
GET /users?filters={"status": {"equal": "active"}, "name": {"contains": "John"}}

# Filter users with role "admin" (array field)
GET /users?filters={"roles[]": {"equal": "admin"}}

# Filter users living in New York (nested JSONB field)
GET /users?filters={"address.city": {"equal": "New York"}}

# Filter users within 50km of coordinates (PostgreSQL PostGIS)
GET /users?filters={"coordinates": {"st_dwithin": "POINT(-74 40), 50km"}}
```

---

## Implementation Guide

Here’s a step-by-step guide to implementing the Query Operator Taxonomy in your project:

### 1. Define Your Taxonomy
   - Start with the categories that matter most to your use case (e.g., `basic_comparison`, `arrays`, `JSONB`).
   - Document each operator’s purpose and database support.
   - Example:
     ```python
     # Example operator for array containment in PostgreSQL
     {
         "name": "contains_any",
         "sql": "@>",
         "description": "Array contains at least one of the given values",
         "category": "arrays",
         "database": ["postgresql", "mongodb"]
     }
     ```

### 2. Build a Parser
   - Write a parser (like `QueryParser` above) that converts client filters into database-compatible queries.
   - Handle edge cases:
     - Quoting values safely (e.g., escaping single quotes in strings).
     - Supporting nested fields (e.g., `metadata.status`).
     - Handling array operations (e.g., `@>` for PostgreSQL, `$elemMatch` for MongoDB).

### 3. Expose the API
   - Decide how to expose filters to clients:
     - **REST**: Query parameters (`?filters={"field": {"op": "value"}}`).
     - **GraphQL**: Filter inputs with a schema like:
       ```graphql
       enum StatusFilter {
         EQUAL
         NOT_EQUAL
         CONTAINS
       }
       input StringFilter {
         op: StatusFilter!
         value: String!
       }
       type Query {
         users(filters: [StringFilter]): [User]!
       }
       ```
     - **Webhooks**: Send filters as part of a payload.

### 4. Database-Specific Adjustments
   - PostgreSQL: Use `LIKE`, `ILIKE`, `@>`, `#>>`, etc.
   - MySQL: Replace `ILIKE` with `LIKE` + `LOWER()` or use `REGEXP`.
   - MongoDB: Replace `@>` with `$elemMatch` or `$in`.

### 5. Performance Considerations
   - Avoid `LIKE` with leading wildcards (e.g., `%John` is slow; `John%` is faster).
   - Use composite indexes for common filter combinations (e.g., `(status, created_at)`).
   - For large datasets, limit the number of distinct filters (e.g., don’t allow `OR` chaining across too many fields).

### 6. Testing
   - Test edge cases:
     - Empty filters.
     - Invalid operators (e.g., `{"x": {"invalid_op": "value"}}`).
     - Malicious input (SQL injection).

---

## Common Mistakes to Avoid

1. **Exposing Raw SQL**: Always validate and sanitize filters to prevent SQL injection. Never concatenate user input directly into SQL.
   - ❌ `query = f"SELECT * FROM users WHERE {user_input}"`
   - ✅ Use parameterized queries or libraries like SQLAlchemy.

2. **Over