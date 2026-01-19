```markdown
---
title: "Transforming GraphQL Filters to SQL: The WHERE Clause Compilation Pattern"
date: 2023-11-15
author: "Alex Carter, Senior Backend Engineer"
tags: ["database", "SQL", "GraphQL", "API Design", "Backend Patterns"]
---

# Transforming GraphQL Filters to SQL: The WHERE Clause Compilation Pattern

In today’s API-driven world, GraphQL has become the go-to choice for flexible querying across multiple frontends. However, as your API evolves to support complex filtering, aggregations, and sorting, translating GraphQL’s declarative syntax into efficient database queries becomes a challenge. Enter the *WHERE Clause Compilation Pattern*—a technique for dynamically constructing SQL `WHERE` clauses from GraphQL inputs like filters, sorts, and search parameters.

This pattern bridges the gap between GraphQL’s human-readable abstractions and SQL’s performance-driven optimizations. By compiling filter inputs into database-ready conditions, you avoid manual SQL string interpolation (which is unsafe and brittle) and enable rich querying without exposing database internals to clients.

Below, we’ll explore how to build a robust, maintainable system for translating GraphQL filters into SQL—complete with code examples, tradeoffs, and pitfalls to avoid.

---

## The Problem: Manual WHERE Clause Construction is Error-Prone

Imagine you’re building a review system for a video game platform. Your API needs to support filtering reviews based on criteria like:
- **Score range**: `score BETWEEN 4 AND 5`
- **Reviewer reputation**: `author.reputation > 100`
- **Date range**: `created_at BETWEEN '2023-01-01' AND '2023-12-31'`
- **Complex conditions**: `score > avg_score AND review_length > 50`

Manually writing a SQL query for each of these cases looks like this:

```javascript
// Example 1: Simple range filter
const query1 = `SELECT * FROM reviews
WHERE score BETWEEN ${scoreStart} AND ${scoreEnd}`;

// Example 2: Nested conditions
const query2 = `SELECT * FROM reviews
WHERE (score > ${avgScore})
AND (review_length > ${minLength})
AND author.reputation > ${reputationThreshold}`;

const params = [scoreStart, scoreEnd, avgScore, minLength, reputationThreshold];
```

### The Pitfalls
1. **SQL Injection**: Hardcoding values directly into SQL strings is dangerous. Even if you use parameterized queries, mismatched parameters can lead to vulnerabilities.
2. **Maintenance Nightmare**: As filters grow complex, supporting additional operators (`IN`, `NOT LIKE`, `ILIKE`) becomes tedious. Each new operator requires new code paths.
3. **Database Variability**: PostgreSQL’s `ILIKE` differs from MySQL’s `LIKE`, and `BETWEEN` syntax isn’t universally supported for all date types.
4. **Performance Collapse**: Poorly constructed WHERE clauses can cause full table scans. For example, `LIKE '%search_term%'` forces an index scan and is slow.
5. **Type Mismatches**: Passing a string where an integer is expected (e.g., `"score > '5'"`) silently fails and corrupts query results.

---
## The Solution: WHERE Clause Compilation

The *WHERE Clause Compilation Pattern* solves these problems by:
1. **Parsing GraphQL inputs** into a structured format (e.g., an AST or JSON object).
2. **Generating SQL-ready conditions** programmatically, handling operators, types, and database metadata.
3. **Parameterizing values** to prevent SQL injection and enable reuse.
4. **Supporting database-specific syntax** for performance and correctness.

### Key Components
1. **GraphQL Input Parser**: Converts GraphQL filter args (e.g., `{ score_gt: 4 }`) into a structured object.
2. **SQL Condition Builder**: Generates SQL clauses from parsed inputs (e.g., `{ operator: 'gt', field: 'score', value: 4 }` → `score > $1`).
3. **Database Adapter**: Handles database-specific syntax (e.g., `ILIKE` vs `LIKE`).
4. **Parameter Interpolator**: Safely escapes and parameterizes values.

---

## Implementation Guide

### 1. Define a Filter AST (Abstract Syntax Tree)
We’ll represent filters as a tree of operations. For example:
```json
{
  "field": "score",
  "operator": "gt",
  "value": 4
}
```
vs.
```json
{
  "operator": "and",
  "conditions": [
    { "field": "score", "operator": "gt", "value": 4 },
    { "field": "reputation", "operator": "gt", "value": 100 }
  ]
}
```

### 2. Build a Condition Compiler
Here’s a Node.js implementation using TypeScript for type safety:

```typescript
import { DatabaseError } from "pg";

type FieldCondition = {
  field: string;
  operator: "eq" | "gt" | "lt" | "gte" | "lte" | "ne" | "in" | "like" | "ilike";
  value: any;
  table?: string;
};

type CompoundCondition = {
  operator: "and" | "or";
  conditions: Array<FieldCondition | CompoundCondition>;
};

class WhereClauseCompiler {
  constructor(private db: { name: string }) {}

  compile(condition: FieldCondition | CompoundCondition): { sql: string; params: any[] } {
    if (this.isFieldCondition(condition)) {
      return this.compileFieldCondition(condition);
    } else {
      return this.compileCompoundCondition(condition);
    }
  }

  private isFieldCondition(condition: any): condition is FieldCondition {
    return "field" in condition && "operator" in condition && "value" in condition;
  }

  private compileFieldCondition(condition: FieldCondition): { sql: string; params: any[] } {
    const { field, operator, value, table } = condition;
    const fullField = table ? `${table}.${field}` : field;

    let sqlPart: string;
    let params = [value];

    switch (operator) {
      case "eq": sqlPart = `${fullField} = $1`; break;
      case "gt": sqlPart = `${fullField} > $1`; break;
      case "lt": sqlPart = `${fullField} < $1`; break;
      case "gte": sqlPart = `${fullField} >= $1`; break;
      case "lte": sqlPart = `${fullField} <= $1`; break;
      case "ne": sqlPart = `${fullField} != $1`; break;
      case "in": {
        if (!Array.isArray(value)) throw new Error("'in' operator requires an array");
        sqlPart = `${fullField} IN ($<)>`;
        params = value; // Replace $<> with $1, $2, etc.
        break;
      }
      case "like": sqlPart = `${fullField} LIKE $1`; break;
      case "ilike": sqlPart = `${fullField} ILIKE $1`; break;
      default: throw new Error(`Unsupported operator: ${operator}`);
    }

    // Handle IN operator's parameter placeholders
    if (operator === "in" && params.length > 1) {
      sqlPart = sqlPart.replace(/\$<\>/g, (_, idx) => `$${idx + 1}`);
    }

    return { sql: sqlPart, params };
  }

  private compileCompoundCondition(condition: CompoundCondition): { sql: string; params: any[] } {
    const { operator, conditions } = condition;
    const subConditions = conditions.map(cond => this.compile(cond));

    const sqlParts = subConditions.map(cond => cond.sql);
    const params = subConditions.flatMap(cond => cond.params);

    const connector = operator === "and" ? " AND " : " OR ";
    return { sql: `(${sqlParts.join(connector)})`, params };
  }
}
```

### 3. GraphQL Resolver Integration
Here’s how to integrate this with GraphQL:

```typescript
import { WhereClauseCompiler } from "./whereClauseCompiler";
import { GraphQLScalarType, GraphQLNonNull } from "graphql";

// Custom scalar for dates in GraphQL
const dateScalar = new GraphQLScalarType({
  name: "Date",
  parseValue(value) { return new Date(value); },
  serialize(value) { return value.toISOString(); },
});

const REVIEW_FILTER_INPUT = new GraphQLInputObjectType({
  name: "ReviewFilterInput",
  description: "Filters for review queries",
  fields: {
    score: { type: GraphQLFloat },
    score_gt: { type: GraphQLFloat },
    score_lt: { type: GraphQLFloat },
    created_after: { type: dateScalar },
    author_reputation_gt: { type: GraphQLInt },
    contains_text: { type: new GraphQLNonNull(String) },
  },
});

const REVIEW_QUERY = new GraphQLObjectType({
  name: "Query",
  fields: {
    reviews: {
      type: GraphQLList(REVIEW),
      resolve: async (_, args, { db }) => {
        const compiler = new WhereClauseCompiler(db);
        const { filter } = args;

        // Parse GraphQL input into an AST
        const conditions: Array<FieldCondition> = [];

        if (filter.score !== undefined) {
          conditions.push({ field: "score", operator: "eq", value: filter.score });
        }

        if (filter.score_gt !== undefined) {
          conditions.push({ field: "score", operator: "gt", value: filter.score_gt });
        }

        // Handle text search with ILIKE
        if (filter.contains_text) {
          conditions.push({
            field: "content",
            operator: "ilike",
            value: `%${filter.contains_text}%`,
          });
        }

        // Build the WHERE clause
        const whereClause = conditions.length
          ? compiler.compile({ operator: "and", conditions })
          : { sql: "1=1", params: [] };

        // Construct the full query
        const query = `
          SELECT * FROM reviews
          WHERE ${whereClause.sql}
          ORDER BY created_at DESC
          LIMIT 100
        `;

        const { rows } = await db.query(query, whereClause.params);
        return rows;
      },
    },
  },
});
```

### 4. Database-Specific Adaptations
To support different databases (PostgreSQL, MySQL, SQLite), extend the compiler:

```typescript
class PostgreSQLAdapter {
  private compiler = new WhereClauseCompiler(this.db);

  public compile(condition: FieldCondition | CompoundCondition): { sql: string; params: any[] } {
    const result = this.compiler.compile(condition);

    // Transform LIKE to ILIKE for PostgreSQL
    if (result.sql.includes("LIKE")) {
      result.sql = result.sql.replace(/LIKE/g, "ILIKE");
    }

    return result;
  }
}
```

---

## Common Mistakes to Avoid

1. **Overusing `LIKE '%search_term%'`**
   This prevents index usage and slows queries. Instead, use full-text search (PostgreSQL’s `tsvector`) or prefix searches (`LIKE 'search_term%'`).

2. **Ignoring NULL Handling**
   A filter like `score > 0` silently excludes NULL values. Use `COALESCE(score, -1) > 0` to include NULLs.

3. **Hardcoding Table Names**
   Always qualify fields with table names or use a schema registry to avoid conflicts.

4. **Assuming All Databases Support Everything**
   MySQL lacks `ILIKE` and `BETWEEN` for datetime ranges. Test queries on your target database.

5. **Neglecting Performance**
   Compiled queries should avoid SELECT * unless pagination is handled client-side. Prefer explicit columns:
   ```sql
   SELECT id, title, created_at FROM reviews WHERE ...
   ```

6. **Not Validating Inputs**
   Always validate filter inputs (e.g., ensure `score_gt` is numeric) before compilation.

---

## Key Takeaways
- **GraphQL Filters → SQL**: Compile GraphQL filter inputs into structured ASTs before generating SQL.
- **Parameterization**: Always use parameterized queries to prevent SQL injection.
- **Database Awareness**: Account for database-specific syntax (e.g., `ILIKE` vs `LIKE`).
- **Maintenance**: Modular design (compiler + adapters) simplifies adding new operators or databases.
- **Performance**: Optimize queries with indexes and avoid full-text scans where possible.
- **Safety**: Validate inputs and handle NULL values explicitly.

---

## Conclusion
The *WHERE Clause Compilation Pattern* transforms GraphQL filters into efficient, database-safe SQL queries. By separating the logic for parsing, compiling, and parameterizing queries, you reduce bugs, improve security, and future-proof your API.

Start small—implement a basic compiler for your most common filters. As complexity grows, extend it with database adapters and more operators. Tools like [GraphQL-js](https://www.graphql-js.com/) and [Prisma](https://www.prisma.io/) can also help bridge the gap between GraphQL and SQL.

Remember: The goal isn’t to build the "perfect" query compiler in one sitting. Refactor incrementally, test thoroughly, and always monitor query performance in production.
```

---
**Further Reading**
- [PostgreSQL `ilike` vs. `like`](https://www.postgresqltutorial.com/postgresql-ilike/)
- [GraphQL Input Types](https://graphql.org/learn/global-object-types/#input-types)
- [SQL Injection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)