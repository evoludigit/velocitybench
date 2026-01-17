```markdown
# Mastering the Operator Availability Matrix: Designing Flexible Database Query Execution

Protect your database queries from vendor lock-in by letting operators choose their own tools. The **Operator Availability Matrix** pattern lets you implement identical functionality across different database platforms—Postgres, MySQL, MongoDB, or even custom solutions—while maintaining performance, consistency, and developer happiness.

This isn’t just database abstraction—it’s a battle-tested approach to **polyglot persistence** that gives you the flexibility to use the right tool for the job. You’ll learn how to design a system where query execution depends on the available operators, not the database engine. Ready to build resilient, portable, and optimized data access layers? Let’s dive in.

---

## The Problem: Vendor Lock-in in Data Access

Imagine you build a robust application with PostgreSQL, only to realize you need to support read replicas managed by a different vendor. Or perhaps you’re scaling horizontally and need to shard your data, forcing a switch to MongoDB. Without careful planning, your application’s query logic becomes tightly coupled to a specific database engine.

### The Cost of Rigidity
When your ORM or query builder assumes a single database, you face these challenges:

- **Schema migrations become nightmares.** Changing from PostgreSQL to MySQL often requires rewriting queries (e.g., handling `LIMIT` vs. `OFFSET` differences).
- **Performance bottlenecks appear.** PostgreSQL’s `ORDER BY` on arbitrary columns is faster than MySQL’s, but your app doesn’t adapt.
- **Vendor-specific features can’t be leveraged.** PostgreSQL’s `jsonb` operators or MongoDB’s `$lookup` aggregations might not be accessible.

### The Hidden Opportunity
Many applications overlook that **operators (functions, comparators, aggregations) are abstract concepts**. The same sum (`+` in SQL) or filter (`WHERE`) can exist across platforms. The key is to **decorate your query logic with metadata** that tells your system which operators to use based on the underlying database.

---

## The Solution: Operator Availability Matrix

The **Operator Availability Matrix** is a design pattern that shifts operator selection from the database engine to your application’s data access layer. Here’s how it works:

1. **Define metadata for every operator** (e.g., `JSON_CONTAINS`, `GROUP_CONCAT`, `$lookup`).
2. **Map each operator to its syntax** across supported databases.
3. **Let the system dynamically choose the operator** based on the database platform.

### Why This Works
- **Portability:** Swap databases without rewriting queries.
- **Performance:** Leverage native optimizations (e.g., PostgreSQL’s `ILIKE` vs. MySQL’s `LIKE`).
- **Extensibility:** Add new databases without touching business logic.

---

## Components: The Operator Availability Matrix

### 1. Operator Definitions
Each operator has a canonical name and a JSON schema defining its parameters and syntax variations.

```json
{
  "operator": "contains",
  "description": "Check if a JSON object contains a key-value pair",
  "variants": [
    {
      "database": "postgres",
      "syntax": "-> 'key' = 'value'",
      "note": "Uses jsonb path access"
    },
    {
      "database": "mysql",
      "syntax": "JSON_EXTRACT(`data`, '$.key') = 'value'",
      "note": "Requires JSON_EXTRACT"
    },
    {
      "database": "mongo",
      "syntax": "$elemMatch: { 'key': value }",
      "note": "Aggregation pipeline"
    }
  ]
}
```

### 2. Query Builder
The query builder dynamically constructs SQL/aggregation pipelines using the selected operator.

```typescript
class QueryBuilder {
  constructor(database: string) {
    this.operators = loadOperatorMatrix();
    this.currentDatabase = database;
  }

  contains(field: string, value: unknown): string {
    const operator = this.operators.find(op =>
      op.operator === "contains" && op.variants.some(v => v.database === this.currentDatabase)
    );
    if (!operator) throw new Error(`No variant for "contains" on ${this.currentDatabase}`);
    return operator.variants.find(v => v.database === this.currentDatabase).syntax
      .replace("'key'", `"${field}"`)
      .replace("value", `"${value}"`);
  }
}

// Usage:
const builder = new QueryBuilder("postgres");
const query = builder.contains("user.profile", "admin"); // "-> 'user.profile' = 'admin'"
```

### 3. Runtime Dispatcher
At execution time, the dispatcher selects the correct syntax based on the target database.

```python
class OperatorDispatcher:
    def __init__(self, database: str):
        self.matrix = self._load_matrix()  # JSON from above
        self.db = database

    def get_operator(self, operator_type: str, field: str, value: str) -> str:
        variant = next(
            v for op in self.matrix if op["operator"] == operator_type
            for v in op["variants"] if v["database"] == self.db
        )
        return variant["syntax"].format(key=field, value=value)

# Example:
dispatcher = OperatorDispatcher("mongo")
query = dispatcher.get_operator("contains", "user.profile", "admin")
# Returns: "$elemMatch: { 'user.profile': 'admin' }"
```

---

## Implementation Guide

### Step 1: Define Your Operator Matrix
Start with a JSON file (or database table) mapping each operator to its variants:

```json
{
  "operators": [
    {
      "operator": "concat",
      "description": "Concatenate strings",
      "variants": [
        { "database": "postgres", "syntax": "`${key}` || '${value}'" },
        { "database": "mysql", "syntax": "CONCAT(`${key}`, '${value}')" },
        { "database": "mongo", "syntax": "$concatArrays: [${key}, '${value}']" }
      ]
    }
  ]
}
```

### Step 2: Build a Query Parser
Use a parser to translate business logic (e.g., `user.name + " (Admin)"`) into database-specific queries.

```javascript
function buildQuery(operator, field, value) {
  const matrix = require("./operator-matrix.json");
  const variant = matrix.operators.find(op =>
    op.operator === operator
  ).variants.find(v => v.database === currentDatabase);

  if (!variant) throw new Error("Unsupported operator for current database");

  return variant.syntax.replace(/\${key}/g, `"${field}"`)
                       .replace(/\${value}/g, `'${value}'`);
}

// Example:
const postgresQuery = buildQuery("concat", "user.name", " (Admin)")
// "user.name || '(Admin)'"
```

### Step 3: Add Database-Specific Optimizations
For critical operations, include performance notes in the matrix:

```json
{
  "operator": "group_concat",
  "variants": [
    {
      "database": "mysql",
      "syntax": "GROUP_CONCAT(`field` SEPARATOR ', ')",
      "note": "Use ORDER BY for consistent results; watch for performance on large tables."
    }
  ]
}
```

### Step 4: Support Aggregation Queries
Extending to MongoDB or PostgreSQL’s JSONB requires pipeline support:

```typescript
class AggregationBuilder {
  constructor(database: string) {
    this.db = database;
  }

  contains(field: string, value: string): any {
    if (this.db === "mongo") {
      return {
        $match: {
          $expr: {
            $eq: [ { $type: [ `$${field}` ] }, "object" ],
            $elemMatch: { `$${field}`: { ...value } }
          }
        }
      };
    }
    // Postgres or MySQL logic...
  }
}
```

---

## Common Mistakes to Avoid

### 1. Overcomplicating the Matrix
- ✅ **Do** keep your matrix focused on core operations.
- ❌ **Don’t** include every niche function (e.g., PostgreSQL’s `array_to_string` might not need a variant if your app uses `GROUP_CONCAT` instead).

### 2. Ignoring Performance Quirks
- Example: `LIKE` vs. `ILIKE` in PostgreSQL. If case-insensitive search is critical, define a separate variant for `ILIKE`.
- Challenge: Always test variants on your target database.

### 3. Hardcoding Database Logic
- ❌ **Bad:** `if (db === "mysql") { return "COUNT(*)"; }` in a utility function.
- ✅ **Good:** Use the matrix for all database decisions.

### 4. Forgetting Edge Cases
- Example: JSON path queries in PostgreSQL vs. MongoDB.
  ```json
  {
    "operator": "json_path",
    "variants": [
      { "database": "postgres", "syntax": "`data`->>'$.key.path'" },
      { "database": "mongo", "syntax": "$getField": { "field": "data", "path": "$.key.path" } }
    ]
  }
  ```

---

## Key Takeaways

- **Operator Selection ≠ Database Features:** The matrix exposes the same abstract operators across platforms.
- **Dynamic Dispatch:** Let your code choose operators at runtime based on the database.
- **Portability > Convenience:** Sacrifice some syntactic sugar for flexibility.
- **Test Variants:** Every database has quirks—validate each variant.
- **Extend Easily:** New databases? Add variants without rewriting business logic.

---

## Conclusion

The Operator Availability Matrix is a powerful tool for **unlocking database flexibility** in your applications. By treating operators as first-class citizens and managing their implementation details separately, you avoid vendor lock-in and future-proof your data access layer.

Start small—define a few critical operators and expand as needed. Over time, you’ll find that your system becomes more adaptable, performant, and resilient.

Now go ahead: **build once, deploy anywhere**.

---
**Further Reading**
- [Polyglot Persistence Patterns](https://docs.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/polyglot-persistence)
- [PostgreSQL vs. MongoDB JSON Path Querying](https://blog.crunchydata.com/blog/understanding-json-paths-postgresql-vs-mongodb)
- [Optimizing MySQL GROUP_CONCAT](https://dev.mysql.com/doc/refman/8.0/en/group-by-functions.html#function_group-concat)
```