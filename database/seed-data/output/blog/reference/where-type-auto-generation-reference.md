# **[Pattern] WHERE Type Auto-Generation Reference Guide**

---

## **Overview**
The **WHERE Type Auto-Generation** pattern dynamically generates input types for `WHERE` clauses based on the database’s capability manifest rather than hardcoding filter operators. This ensures compatibility across databases (e.g., PostgreSQL, MySQL) by automatically selecting the appropriate data types and operators (e.g., `=`, `IN`, `LIKE`) based on the underlying system’s supported features. By leveraging dynamic schema introspection, FraiseQL eliminates manual operator mapping, reducing boilerplate and improving cross-database flexibility.

---

## **Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|----------------------------------------------------------------------------------------------------|
| **Capability Manifest**   | A metadata schema describing each database’s supported operators, data types, and queryfeatures.   |
| **Dynamic Type Resolution**| FraiseQL inspects the database’s manifest to determine valid filter types and operators.         |
| **Operator Overrides**    | If a database lacks a specific operator (e.g., `NOT IN`), FraiseQL falls back to equivalent logic (e.g., `NOT EXISTS`). |
| **Input Type Generation** | Input fields for `WHERE` clauses are auto-generated as JSON schemas based on the database’s schema and capabilities. |

---

## **Schema Reference**
### **1. Capability Manifest Structure**
The `capabilities.json` file defines supported operators, data types, and constraints per database.

```json
{
  "database": "postgresql",
  "operators": {
    "string": ["=", "!=", "LIKE", "ILIKE", "IN", "NOT IN"],
    "number": ["=", "!=", ">", "<", "IN"],
    "boolean": ["=", "!="],
    "datetime": ["=", "!=", ">", "<", "IN"]
  },
  "type_mappings": {
    "text": "string",
    "integer": "number",
    "boolean": "boolean",
    "timestamp": "datetime"
  }
}
```

### **2. Auto-Generated `WHERE` Input Schema**
FraiseQL generates a schema for query inputs based on the table’s columns and the database’s manifest.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FilterSchemaForOrders",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["pending", "shipped", "cancelled"]
    },
    "amount": {
      "type": "number",
      "minimum": 0
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

### **3. Dynamic Operator Selection**
The generated schema includes operator choices based on column types and database capabilities.

```json
{
  "status": {
    "type": "string",
    "operators": ["=", "IN", "LIKE"],
    "default": "="
  },
  "amount": {
    "type": "number",
    "operators": [">=", "<=", "IN", "BETWEEN"]
  }
}
```

---

## **Query Examples**
### **Example 1: Basic Filtering**
**Input:**
```json
{
  "status": {
    "op": "IN",
    "value": ["pending", "shipped"]
  }
}
```
**Generated SQL (PostgreSQL):**
```sql
SELECT * FROM orders WHERE status IN ('pending', 'shipped')
```

**Generated SQL (MySQL):**
```sql
SELECT * FROM orders WHERE status IN ('pending', 'shipped')
```

### **Example 2: Composite Filtering**
**Input:**
```json
{
  "created_at": {
    "op": ">",
    "value": "2023-01-01"
  },
  "amount": {
    "op": "BETWEEN",
    "value": [100, 500]
  }
}
```
**Generated SQL (PostgreSQL):**
```sql
SELECT * FROM orders
WHERE created_at > '2023-01-01'
  AND amount BETWEEN 100 AND 500
```

### **Example 3: Fallback Operator Handling**
If `BETWEEN` is unsupported in MySQL, FraiseQL rewrites it as:
```sql
AND (amount >= 100 AND amount <= 500)
```

---

## **Implementation Details**
### **1. Database Capability Introspection**
FraiseQL queries the database’s metadata to populate the `capabilities.json`:
```sql
-- Example: PostgreSQL introspection
SELECT
  column_name,
  data_type,
  is_numeric,
  is_datetime
FROM information_schema.columns
WHERE table_name = 'orders';
```

### **2. Dynamic Schema Generation**
FraiseQL processes the table schema to generate the input schema:
```python
def generate_filter_schema(table_schema, database_manifest):
    schema = {}
    for column in table_schema.columns:
        column_type = database_manifest["type_mappings"].get(column.type, "string")
        operators = database_manifest["operators"].get(column_type, [])
        schema[column.name] = {
            "type": column_type,
            "operators": operators,
            "default": "="
        }
    return schema
```

### **3. Operator Fallback Mechanism**
If a requested operator is unsupported, FraiseQL applies a fallback:
```python
def fallback_operator(original_op, column_type, value):
    if original_op == "BETWEEN" and column_type == "number":
        return f"({column_name} >= {value[0]} AND {column_name} <= {value[1]})"
    elif original_op == "NOT IN":
        return f"(1 = 1) -- Fallback not implemented (use NOT EXISTS)"
```

---

## **Query Examples (Advanced)**
### **Example 4: Nested Conditional Logic**
**Input:**
```json
{
  "AND": [
    {
      "status": { "op": "=", "value": "pending" }
    },
    {
      "OR": [
        { "amount": { "op": ">", "value": 100 } },
        { "created_at": { "op": "=", "value": "2023-01-01" } }
      ]
    }
  ]
}
```
**Generated SQL (PostgreSQL):**
```sql
SELECT * FROM orders
WHERE status = 'pending'
AND (
    amount > 100
    OR created_at = '2023-01-01'
)
```

### **Example 5: Aggregation Filters**
**Input:**
```json
{
  "avg_amount": {
    "op": ">",
    "value": 75,
    "aggregate": true
  }
}
```
**Generated SQL:**
```sql
SELECT * FROM orders
WHERE (SELECT AVG(amount) FROM orders) > 75
```

---

## **Performance Considerations**
- **Index Utilization:** Auto-generated filters prioritize indexed columns for performance.
- **Operator Cost:** Complex operators (e.g., `LIKE` without wildcards) may use additional subqueries.
- **Database-Specific Optimizations:** Some databases (e.g., PostgreSQL) optimize `BETWEEN` better than others.

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                     |
|----------------------------------|----------------------------------------------------------------------------------------------------|
| **Schema Registry**              | Stores database schemas and capabilities for consistency.                                           |
| **Operator Translation Layer**   | Maps high-level operators (e.g., `BETWEEN`) to database-specific syntax.                             |
| **Adaptive Query Optimization**  | Dynamically selects the most efficient SQL plan based on query patterns and database metadata.     |
| **Type Conversion Service**      | Handles implicit type conversions between input data and database columns.                         |

---
**Note:** For advanced use cases, refer to the [FraiseQL Developer Docs](link) for custom capability definitions.