# **[Pattern] Intermediate Representation (IR) Design Reference Guide**

---
## **1. Overview**
The **Intermediate Representation (IR)** pattern serves as a standardized, database-agnostic abstraction layer in compilation pipelines. Schemas and queries written in diverse input languages (e.g., SQL-like dialects, graphql, or domain-specific languages) are **normalized, validated, and optimized** into a common internal format before final translation to target databases.

This pattern ensures **consistent query processing**, reduces redundant logic, and enables **cross-database compatibility** by decoupling frontend language semantics from backend execution. IRs are typically tree-based, structured to reflect logical relationships while abstracting low-level syntax and schema variations.

---
### **Key Goals**
- Normalize heterogeneous input schemas into a unified model.
- Enable **validation, optimization, and analysis** before target translation.
- Facilitate **query plan reuse** across databases.
- Simplify debugging by exposing a single canonical representation.

---
## **2. Schema Reference**

### **2.1 IR Schema Structure**
The IR schema defines a **hierarchical, object-oriented model** with the following core components:

| **Component**       | **Description**                                                                 | **Example Fields/Properties**                                                                 |
|---------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Database**        | Represents the target database or environment (e.g., PostgreSQL, MongoDB).   | `name (string)`, `engine (enum: PostgreSQL/MongoDB/…)`, `config (object)`                     |
| **Schema**          | Top-level container for IR models (tables, views, functions, etc.).             | `name (string)`, `namespace (string)`, `tables (array[Table])`, `views (array[View])`        |
| **Table**           | Normalized representation of a database table.                                 | `name (string)`, `columns (array[Column])`, `primaryKey (array[Column])`, `indexes (array)` |
| **Column**          | Describes a table attribute, including type and constraints.                   | `name (string)`, `type (enum: INT/STRING/JSON/…)`, `isNullable (bool)`, `defaultValue (any)` |
| **Query**           | Abstract tree representing a query (SELECT, INSERT, UPDATE, DELETE).           | `type (enum: SELECT/INSERT/…)`, `from (Table|Join)`, `where (Condition)`, `groupBy (array[Column])` |
| **Join**            | Represents a join operation between tables.                                    | `type (enum: INNER/LEFT/RIGHT/FULL)`, `on (Condition)`, `tables (array[Table])`               |
| **Condition**       | Logical predicate (filter, join condition, etc.).                              | `left (Column|Query)`, `operator (enum: =/!=/IN/…)`, `right (Column|Value|Subquery)`, `isNegated (bool)`  |
| **Value**           | Literal data (used in conditions, INSERT values, etc.).                        | `bool (boolean)`, `int (number)`, `string (string)`, `json (object/array)`                     |
| **Subquery**        | Embedded query (e.g., in WHERE, FROM clauses).                                 | `query (Query)`, `alias (string)`                                                               |

---
### **2.2 IR Schema Example**
Below is a simplified IR representation of a SQL query:

```json
{
  "database": {
    "name": "customer_db",
    "engine": "PostgreSQL"
  },
  "schema": {
    "name": "public",
    "tables": [
      {
        "name": "users",
        "columns": [
          {"name": "id", "type": "INT", "isNullable": false},
          {"name": "email", "type": "STRING"}
        ],
        "primaryKey": ["id"]
      }
    ],
    "queries": [
      {
        "type": "SELECT",
        "columns": ["email"],
        "from": {
          "table": "users",
          "alias": "u"
        },
        "where": {
          "left": {"column": "u.id", "table": "users"},
          "operator": ">",
          "right": {"value": 100}
        }
      }
    ]
  }
}
```

---
## **3. Query Examples**

### **3.1 Basic SELECT Query**
**Input (SQL-like):**
```sql
SELECT email FROM users WHERE id > 100;
```

**IR Representation:**
```json
{
  "type": "SELECT",
  "columns": [{"column": "email", "table": "users"}],
  "from": {"table": "users", "alias": "u"},
  "where": {
    "left": {"column": "id", "table": "users"},
    "operator": ">",
    "right": {"value": 100}
  }
}
```

---
### **3.2 JOIN Operation**
**Input (GraphQL-like):**
```graphql
query {
  users(where: { age: { gt: 25 } }) {
    name
    orders {
      id
    }
  }
}
```

**IR Representation:**
```json
{
  "type": "SELECT",
  "columns": [
    {"column": "name", "table": "users"},
    {"column": "id", "table": "orders", "join": "orders_join"}
  ],
  "from": {
    "table": "users",
    "alias": "u"
  },
  "joins": [
    {
      "type": "INNER",
      "tables": ["users", "orders"],
      "on": {
        "left": {"column": "user_id", "table": "orders"},
        "operator": "=",
        "right": {"column": "id", "table": "users"}
      },
      "alias": "orders_join"
    }
  ],
  "where": {
    "left": {"column": "age", "table": "users"},
    "operator": ">",
    "right": {"value": 25}
  }
}
```

---
### **3.3 Aggregation with GROUP BY**
**Input (Custom DSL):**
```python
aggregate(users: [
  group_by: "department",
  avg: "salary",
  max: "hire_date"
])
```

**IR Representation:**
```json
{
  "type": "SELECT",
  "columns": [
    {"column": "department", "table": "users", "aggregate": "GROUP_BY"},
    {"column": "salary", "table": "users", "aggregate": { "type": "AVG" }}
  ],
  "from": {"table": "users", "alias": "u"},
  "groupBy": ["department"],
  "having": null
}
```

---
## **4. Implementation Details**

### **4.1 Normalization Rules**
The IR enforces the following transformations during parsing:
1. **Case Normalization**: Column/table names are **lowercased** or standardized (e.g., `UserId` → `user_id`).
2. **Type Resolving**: Input types (e.g., `VARCHAR(255)`) are mapped to IR types (`STRING`).
3. **Alias Resolution**: Table aliases are **scoped** to avoid conflicts.
4. **Join Rewriting**: Complex joins (e.g., recursive) are **decomposed** into IR-compatible forms.
5. **Expression Flattening**: Nested expressions (e.g., `SUM(price * quantity)`) are **linearized**.

---
### **4.2 Validation**
The IR schema is validated against the following rules:
| **Rule**                          | **Description**                                                                 |
|-----------------------------------|---------------------------------------------------------------------------------|
| **Referential Integrity**         | All columns in `JOIN`/`WHERE` clauses must exist in declared tables.          |
| **Type Consistency**              | Operators (e.g., `+`) must apply to compatible types (e.g., `INT + INT`).      |
| **Aggregate Legality**            | `GROUP BY` columns must include all non-aggregated columns.                   |
| **Null Handling**                 | `NOT NULL` constraints are enforced where applicable.                          |
| **Database-Specific Limits**      | Avoids features unsupported by the target engine (e.g., `LIMIT OFFSET` in some NoSQL). |

---
### **4.3 Optimization Opportunities**
The IR enables the following optimizations:
1. **Predicate Pushdown**: Filter conditions are **pushed** to earlier stages (e.g., JOIN before SELECT).
2. **Join Reordering**: Joins are **rearranged** to minimize intermediate result sizes.
3. **Common Subexpression Elimination**: Repeated expressions (e.g., `user.age`) are **cached**.
4. **Projection Pushdown**: Only required columns are **pulled** from tables.
5. **Null Handling**: `NULL` checks are **optimized** (e.g., `IS NOT NULL` early termination).

---
## **5. Related Patterns**

| **Pattern**                     | **Relationship to IR**                                                                 | **When to Use**                                                                 |
|----------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Schema Registry**              | IR schemas are registered here for versioning and discovery.                           | When managing multiple schema versions across teams.                           |
| **Query Plan Cache**             | IR queries generate optimized plans stored in a cache for reuse.                      | For high-frequency queries with stable IRs.                                    |
| **Database Abstraction Layer**   | IR acts as the intermediate layer between abstract queries and concrete DB drivers.   | When supporting multiple databases with minimal code duplication.              |
| **Canonical Query Language (CQL)** | IR is a simplified subset of CQL for internal use.                                     | When defining a domain-specific query language.                                 |
| **Materialized Views**           | IR can model precomputed queries stored as views.                                      | For read-heavy workloads with frequent aggregations.                           |
| **Schema Evolution**             | IR handles backward-compatible schema changes (e.g., adding optional columns).       | When migrating schemas incrementally.                                           |

---
## **6. Best Practices**

1. **Minimize IR Complexity**:
   - Avoid over-engineering (e.g., avoid IR nodes for every edge case).
   - Prefer **composition** over **inheritance** (e.g., extend `Condition` via properties).

2. **Performance Considerations**:
   - **Tree Traversal**: Use depth-first or iterative traversal for analysis/optimization.
   - **Memory**: For large queries, stream IR nodes instead of loading into memory.

3. **Testing**:
   - Write **property-based tests** (e.g., "All IR queries must resolve columns").
   - Test **edge cases** (e.g., `NULL` values, empty tables).

4. **Extensibility**:
   - Use **plugins** for database-specific optimizations (e.g., PostgreSQL-specific indexes).
   - Document **extension points** for new IR features.

5. **Debugging**:
   - Provide **pretty-printing** of IR for logging.
   - Include **source mapping** to trace IR nodes back to original input.

---
## **7. Example Workflow**

1. **Input Parsing**:
   - Parse a GraphQL query → Convert to IR.
   ```graphql
   { users(where: { age: { gt: 25 } }) { name } }
   ```
   → IR: `SELECT(name) FROM users WHERE age > 25`.

2. **Validation**:
   - Check column existence, type compatibility.

3. **Optimization**:
   - Push `WHERE` clause to the `FROM` node.

4. **Target Translation**:
   - Convert IR to PostgreSQL:
   ```sql
   SELECT name FROM users WHERE age > 25;
   ```

---
## **8. Open Issues & Limitations**
| **Issue**                          | **Current Workaround**                                                                 | **Future Work**                                                                 |
|------------------------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Recursive Queries**              | Limited support via `WITH RECURSIVE` in SQL.                                          | Explore IR extensions for cyclic dependency detection.                          |
| **Partial Updates**                | IR treats updates as full-table rewrites.                                             | Add `UPDATE` semantics with `SET` clauses.                                      |
| **Stale Data Handling**            | Assumes data consistency; no conflict resolution.                                   | Integrate with **optimistic concurrency control** patterns.                     |
| **Dynamic IR Generation**           | IR is static; dynamic queries require runtime parsing.                               | Add **IR templating** for parameterized queries.                               |

---
## **9. References**
- **IR Design**: [Database Compilation Patterns (PDF)](https://example.com/ir-patterns.pdf).
- **Validation**: [SQL:1999 Standards](https://www.iso.org/standard/26029.html).
- **Optimization**: [Query Rewriting Techniques](https://dl.acm.org/doi/10.1145/3232618.3232626).

---
**Last Updated**: `YYYY-MM-DD`
**Version**: `1.0`