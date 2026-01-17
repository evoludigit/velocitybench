# **[Pattern] Operator Type Definition Reference Guide**

---

## **1. Overview**
The **Operator Type Definition** pattern standardizes how comparison operators (`eq`, `ne`, `lt`, `gt`, `in`, `like`) are applied across query systems, APIs, or domain-specific languages. It defines a reusable schema for specifying operator behavior, compatibility rules, and syntax variations. This pattern ensures consistency in filtering, sorting, and data comparisons while accommodating type-specific optimizations (e.g., numeric vs. string operations).

Key benefits include:
- **Portability**: Easily adaptable across different query engines or APIs.
- **Type Safety**: Explicit operator definitions reduce runtime errors (e.g., comparing strings with `>`).
- **Extensibility**: New operators or custom behaviors can be added without breaking existing systems.
- **Readability**: Uniform syntax for developers and users (e.g., `{"field": {"eq": "value"}}`).

This pattern is commonly used in:
- Search APIs (e.g., Elasticsearch, Algolia).
- ORMs (e.g., Django ORM, Hibernate).
- Configuration-driven tools (e.g., Grafana dashboards, OpenSearchDSL).

---

## **2. Schema Reference**

### **2.1 Core Schema Structure**
The pattern defines a nested object structure for operators, with the following mandatory fields:

| Field          | Type       | Description                                                                 | Example Value          |
|----------------|------------|-----------------------------------------------------------------------------|------------------------|
| **operator**   | `string`   | The operator keyword (`eq`, `ne`, `lt`, `gt`, `in`, `like`).               | `"eq"`, `"like"`       |
| **value**      | `any`      | The operand value(s) to compare against.                                    | `42`, `"pattern%"`, `[1, 2]` |
| **field**      | `string`   | (Optional) The target field/path (e.g., `"user.id"`, `"metadata.tags"`).   | `"age"`, `"name.first"`|

### **2.2 Supported Operators**
| Operator | Description                                                                 | Compatible Types               | Example Usage                     |
|----------|-----------------------------------------------------------------------------|--------------------------------|-----------------------------------|
| `eq`     | Equals                                                                     | Any type                       | `{"field": {"eq": "John"}}`       |
| `ne`     | Not equals                                                                 | Any type                       | `{"field": {"ne": 10}}`           |
| `lt`     | Less than                                                                  | Numeric, temporal (e.g., timestamps) | `{"age": {"lt": 30}}`      |
| `gt`     | Greater than                                                                | Numeric, temporal               | `{"score": {"gt": 80}}`           |
| `in`     | Value is in a list                                                        | Any type                       | `{"status": {"in": ["active", "pending"]}}` |
| `like`    | SQL-style pattern matching (`%`, `_`)                                      | String                         | `{"name": {"like": "A%"}}`        |
| `contains` | Substring match                                                           | String                         | `{"keywords": {"contains": "search"}}` |
| `range`   | Numeric/temporal range (`{gt: ..., lt: ...}`)                            | Numeric, temporal               | `{"price": {"range": {"gt": 0, "lt": 100}}}` |

### **2.3 Type-Specific Rules**
| Type        | Notes                                                                       |
|-------------|-----------------------------------------------------------------------------|
| **String**  | `like`/`contains` use `%` wildcards. `eq`/`ne` are case-sensitive by default unless configured otherwise. |
| **Numeric** | `lt`/`gt` enforce strict comparison. `in` accepts lists of numbers.       |
| **Boolean** | Supported by `eq`/`ne` only (e.g., `{"is_active": {"eq": true}}`).        |
| **Array**   | `in` checks for intersection (e.g., `[1, 2]` matches `[1, 2, 3]`).        |
| **Nested**  | Fields can reference nested objects (e.g., `{"user.address.city": {"eq": "NY"}}`). |

### **2.4 Operator Combinations**
Multiple operators can be chained for complex queries using logical operators (`AND`, `OR`, `NOT`):

```json
{
  "filters": [
    {"field": {"eq": "value1"}},
    {"field": {"ne": "value2"}},
    {"field": {"gt": 10}}
  ],
  "logical_operator": "AND"
}
```

---

## **3. Query Examples**

### **3.1 Basic Filtering**
```json
// Find users with age equal to 30
{"age": {"eq": 30}}
```

```json
// Find products priced above $50
{"price": {"gt": 50}}
```

### **3.2 Wildcard Search**
```json
// Find strings starting with "Elastic"
{"name": {"like": "Elastic%"}}
```

```json
// Find strings containing "search"
{"keywords": {"contains": "search"}}
```

### **3.3 List Membership**
```json
// Find users with roles in ["admin", "editor"]
{"role": {"in": ["admin", "editor"]}}
```

### **3.4 Range Queries**
```json
// Find values between 10 and 50 (inclusive)
{"score": {"range": {"gt": 10, "lt": 50}}}
```

### **3.5 Nested Field Access**
```json
// Find documents where nested.path.key equals "value"
{"nested.path.key": {"eq": "value"}}
```

### **3.6 Logical Combinations**
```json
{
  "filters": [
    {"status": {"eq": "active"}},
    {"created_at": {"gt": "2023-01-01"}}
  ],
  "logical_operator": "AND"
}
```

```json
{
  "filters": [
    {"category": {"eq": "electronics"}},
    {"price": {"lt": 100}}
  ],
  "logical_operator": "OR"
}
```

---

## **4. Implementation Details**

### **4.1 Key Concepts**
1. **Operator Precedence**:
   - Logical operators (`AND`, `OR`) override per-field operators if not explicitly nested.
   - Example: `{"field": {"and": [{"eq": "A"}, {"gt": 10}]}}` takes precedence over a global `AND`.

2. **Type Casting**:
   - Systems may automatically cast values (e.g., `"123"` → `123` for numeric fields). Explicit casting (e.g., `{"eq": {"type": "string", "value": "123"}}`) ensures consistency.

3. **Performance Considerations**:
   - Use `in` for small lists (optimized for indexed fields).
   - Avoid `like` with leading wildcards (`"%pattern"`) on large datasets.

4. **Custom Operators**:
   - Extend the schema with vendor-specific operators (e.g., `{"text": {"match": "query"}}`).
   - Document new operators in a `custom_operators` section:
     ```json
     {
       "custom_operators": {
         "match": {
           "description": "Full-text search (vendor-specific)",
           "type": "string"
         }
       }
     }
     ```

### **4.2 Validation Rules**
| Rule                          | Description                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| Required Fields               | `operator` must exist. `value` is required unless `range` is used.        |
| Type Mismatch                 | `like`/`contains` must pair with string fields. `lt`/`gt` require numeric types. |
| Wildcard Limits               | `like` patterns may be limited to a maximum length (e.g., 100 chars).       |
| Nested Field Depth             | Maximum depth for nested fields (e.g., 5 levels) to prevent slow queries.   |

### **4.3 Example Validation Schema (JSON Schema)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "field": {"type": "string"},
    "operator": {
      "enum": ["eq", "ne", "lt", "gt", "in", "like", "contains", "range"]
    },
    "value": {"anyOf": [{"type": "string"}, {"type": "number"}, {"type": "boolean"}, {"type": "array"}]},
    "range": {
      "type": "object",
      "properties": {"gt": {"type": "number"}, "lt": {"type": "number"}},
      "required": ["gt", "lt"]
    }
  },
  "required": ["operator", "value"]
}
```

---

## **5. Related Patterns**

| Pattern                          | Description                                                                 | Usage Case                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **[Pagination Pattern]**         | Standardizes offset/limit or cursor-based pagination.                       | Large datasets where partial results are needed.                          |
| **[Projection Pattern]**         | Defines field selection (`_source` in Elasticsearch, `SELECT` in SQL).      | Reducing payload size for performance-critical APIs.                       |
| **[Aggregation Pattern]**        | Standardizes group-by, count, and statistical operations.                   | Analytics dashboards requiring summarization.                              |
| **[Sorting Pattern]**            | Defines field-based sorting with direction (`asc`, `desc`).                  | Ranking results by relevance or priority.                                  |
| **[Full-Text Search Pattern]**   | Extends this pattern with `match`, `phrase`, and `highlight` operators.     | Text-heavy applications (e.g., search engines).                            |
| **[Geospatial Pattern]**         | Adds `geo_distance`, `geo_shape` operators for location-based queries.       | Maps, delivery routing, or proximity searches.                            |

---

## **6. Troubleshooting**
| Issue                          | Cause                          | Solution                                                                   |
|--------------------------------|---------------------------------|-----------------------------------------------------------------------------|
| Partial matches               | Using `like` with no wildcards.  | Add `%` wildcards (e.g., `{"like": "pattern%"}`).                          |
| Type errors                   | Incorrect operator/type pairing. | Check [Type-Specific Rules](#23-type-specific-rules).                       |
| Performance degradation       | Full-table scans on unindexed fields. | Ensure fields are indexed or use `in` with small lists.                   |
| Invalid nested paths          | Malformed dot notation.         | Validate fields with `{"field": {"eq": "valid.field"}}`.                    |

---

## **7. See Also**
- **[JSON Schema for Operators](https://example.com/operator-schema)** – Formal validation rules.
- **[Performance Best Practices](#42-validation-rules)** – Guidelines for scalable implementations.
- **[Vendor-Specific Extensions]** – Custom operators (e.g., OpenSearch’s `wildcard` vs. Elasticsearch’s `regex`).