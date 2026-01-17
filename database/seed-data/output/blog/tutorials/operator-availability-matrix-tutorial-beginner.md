```markdown
---
title: "Operator Availability Matrix: How to Build Flexible Database APIs"
date: 2023-11-15
author: "Alex Chen"
description: "Learn the Operator Availability Matrix pattern to build database-agnostic APIs in this practical guide for backend beginners."
tags: ["Database Design", "API Patterns", "Flexible Architecture", "Backend Engineering"]
---

# Operator Availability Matrix: How to Build Flexible Database APIs

![Database Operator Matrix](https://via.placeholder.com/800x400?text=Operator+Availability+Matrix+Diagram)
*An example conceptual diagram of operator availability across database systems*

---

## Introduction

As a backend developer, you've probably experienced the frustrating moment when an elegant query solution in PostgreSQL fails completely in MySQL—or worse, in both but with different error messages. This inconsistency isn't just an annoyance; it can become a major architectural bottleneck as your application scales across multiple database engines.

The **Operator Availability Matrix** pattern addresses this challenge by creating a systematic way to handle database-specific syntax variations. Imagine being able to write a single API layer that seamlessly adapts to different database backends without exposing the underlying differences to your application code. This pattern makes that possible.

In this post, we'll explore how operator availability matrices work, when you should use them, and how to implement them effectively. We'll start with a concrete problem most developers face, then build a practical solution with code examples. By the end, you'll understand how to create database-agnostic APIs that work anywhere.

---

## The Problem: Database-Specific Operator Inconsistencies

Let's consider a typical CRUD application that needs to support both PostgreSQL and MongoDB. While both are document stores at a high level, their query capabilities differ dramatically when we get into the details:

```sql
-- PostgreSQL (Single Document)
SELECT * FROM users WHERE (last_name = 'Smith' OR first_name = 'John') AND active = true;

-- MongoDB (Aggregation Pipeline)
db.users.aggregate([
  { $match: {
    $or: [
      { last_name: 'Smith' },
      { first_name: 'John' }
    ],
    active: true
  }}
]);
```

The problem grows even more complex when we consider:

1. **Logical equivalence vs. literal equivalence**: Many operators exist with similar meanings but different syntaxes
2. **Missing operators**: Some databases support what others don't (e.g., PostgreSQL's `array` functions vs MongoDB's `$elemMatch`)
3. **Performance variations**: Even identical queries can behave differently across databases
4. **Transaction boundaries**: Different isolation levels and transaction semantics

Without a systematic approach, we're forced to either:
- Write conditional logic that branches based on the database
- Create database-specific API endpoints
- Restrict ourselves to the least-capable database
- Build complex query translators

All of these approaches introduce technical debt and make future database migrations difficult.

---

## The Solution: Operator Availability Matrix

The operator availability matrix pattern provides a structured way to handle database differences by:

1. **Mapping abstract operators** to database-specific implementations
2. **Centralizing operator knowledge** in one place
3. **Maintaining a canonical operator set** that your APIs expose
4. **Hiding implementation details** from application code

The core idea is simple: Create a matrix that shows which operators are available in which databases, then build wrappers around each implementation. Here's a conceptual example:

| Operator Name       | PostgreSQL Implementation | MySQL Implementation       | MongoDB Implementation      |
|---------------------|--------------------------|----------------------------|-----------------------------|
| `contains`          | `!= NULL` with `jsonb`   | `LIKE '%value%'`           | `$elemMatch`                |
| `startsWith`        | `LIKE 'prefix%'`         | `LIKE 'prefix%'`           | `$regex` with `^` prefix    |
| `arrayContains`     | `ANY(array::text[] = value)` | JSON functions          | `$in` with array elements   |

This approach lets us write clean, database-agnostic query builders while ensuring our actual queries work correctly on each target database.

---

## Components of the Operator Availability Matrix

A complete implementation requires several components:

1. **Operator Registry**: The canonical set of operators your API exposes
2. **Database Adapters**: Concrete implementations for each supported database
3. **Query Builder**: The abstraction layer that uses the matrix to generate queries
4. **Type Mappings**: How to convert between your application types and database types
5. **Result Transformers**: Convert database results to your application models

Let's explore these with code examples using a simple user profile service.

---

## Implementation: A Practical Example

### 1. Define the Operator Registry

First, we'll create a type-safe registry of supported operators:

```typescript
// types.ts
type OperatorName =
  | 'equals'
  | 'notEquals'
  | 'contains'
  | 'startsWith'
  | 'endsWith'
  | 'arrayContains'
  | 'inList'
  | 'greaterThan';

// Operator type definitions
interface BaseOperator {
  name: OperatorName;
  appliesTo?: 'string' | 'number' | 'array' | 'any';
}

export const OPERATORS: Record<OperatorName, BaseOperator> = {
  equals: { name: 'equals', appliesTo: 'any' },
  notEquals: { name: 'notEquals', appliesTo: 'any' },
  contains: { name: 'contains', appliesTo: 'string' },
  // ... other operators
};
```

### 2. Create Database Adapters

Each database adapter implements operators according to its capabilities:

```typescript
// adapters/postgres-adapter.ts
import { OPERATORS } from '../types';

export class PostgreSQLAdapter {
  static supports(operator: OperatorName) {
    return ['equals', 'notEquals', 'contains', 'startsWith',
            'greaterThan', 'arrayContains'].includes(operator);
  }

  static buildWhereClause(operator: OperatorName, field: string, value: any) {
    switch (operator) {
      case 'equals':
        return `${field} = $1`;
      case 'notEquals':
        return `${field} != $1`;
      case 'contains':
        return `jsonb_path_exists(${field}::jsonb, '$ * ? (contains($, ?))')`;
      case 'startsWith':
        return `${field} LIKE $1 || '%'`;
      case 'greaterThan':
        return `${field} > $1`;
      case 'arrayContains':
        return `array_position(${field}::text[], $1::text) > 0`;
      default:
        throw new Error(`Operator ${operator} not supported by PostgreSQL`);
    }
  }
}
```

```typescript
// adapters/mongodb-adapter.ts
export class MongoDBAdapter {
  static supports(operator: OperatorName) {
    return ['equals', 'notEquals', 'contains', 'startsWith',
            'greaterThan', 'endsWith'].includes(operator);
  }

  static buildWhereClause(operator: OperatorName, field: string, value: any) {
    const opMap = {
      equals: `$eq`,
      notEquals: `$ne`,
      contains: `$regex`,
      startsWith: `$regex`,
      endsWith: `$regex`,
      greaterThan: `$gt`
    };

    const operatorName = opMap[operator];

    switch (operator) {
      case 'contains':
      case 'startsWith':
      case 'endsWith':
        const regexValue = operator === 'startsWith'
          ? `^${value}`
          : operator === 'endsWith'
            ? `${value}$`
            : value;

        return {
          [field]: {
            [operatorName]: new RegExp(regexValue)
          }
        };

      default:
        return {
          [field]: {[operatorName]: value}
        };
    }
  }
}
```

### 3. Build the Query Builder

The query builder uses the matrix pattern to determine which operators are available:

```typescript
// query-builder.ts
import { OPERATORS } from './types';
import { PostgreSQLAdapter } from './adapters/postgres-adapter';
import { MongoDBAdapter } from './adapters/mongodb-adapter';

type DatabaseType = 'postgres' | 'mongodb';

class QueryBuilder {
  private readonly adapter: any;
  private readonly databaseType: DatabaseType;
  private conditions: any[] = [];

  constructor(databaseType: DatabaseType) {
    this.databaseType = databaseType;
    this.adapter = databaseType === 'postgres'
      ? PostgreSQLAdapter
      : MongoDBAdapter;
  }

  filter(operator: OperatorName, field: string, value: any) {
    if (!this.adapter.supports(operator)) {
      throw new Error(
        `${operator} operator not supported by ${this.databaseType}`
      );
    }

    const clause = this.adapter.buildWhereClause(operator, field, value);
    this.conditions.push(clause);
    return this;
  }

  build() {
    if (!this.conditions.length) return null;

    // Implementation varies by database
    switch (this.databaseType) {
      case 'postgres':
        return this.buildPostgresQuery();
      case 'mongodb':
        return this.buildMongoQuery();
      default:
        throw new Error('Database not supported');
    }
  }

  private buildPostgresQuery() {
    // Combine with AND logic
    const whereClause = this.conditions.map(
      (_, i) => `($${i + 1})`
    ).join(' AND ');

    return {
      sql: `SELECT * FROM users WHERE ${whereClause}`,
      params: this.conditions.map(clause => {
        // Simplified parameter handling
        return this.conditions.map(cond => {
          if (typeof cond === 'string') return clause;
          return cond.value; // For MongoDB-style objects
        });
      })
    };
  }

  private buildMongoQuery() {
    // Combine with AND logic
    const filter = this.conditions.reduce((acc, cond) => {
      if (typeof cond === 'string') {
        // For PostgreSQL-style conditions
        // This would be more complex in real implementation
        return { ...acc, ...cond };
      }
      return { ...acc, ...cond };
    }, {});

    return { filter };
  }
}

export default QueryBuilder;
```

### 4. Example Usage

Using our query builder to get active users whose last names contain "Smith":

```typescript
// Usage example
const dbType = 'postgres';
const builder = new QueryBuilder(dbType);

try {
  const query = builder
    .filter('equals', 'active', true)
    .filter('contains', 'last_name', 'Smith')
    .build();

  if (dbType === 'postgres') {
    console.log('Executing:', query.sql, 'with params:', query.params);
    // Output: SELECT * FROM users WHERE ($1) AND (jsonb_path_exists(last_name::jsonb, '$ * ? (contains($, ?))')) with params...
  } else if (dbType === 'mongodb') {
    console.log('Executing MongoDB query:', query.filter);
    // Output: { $and: [{ active: true }, { last_name: { $regex: /^Smith/ } }] }
  }
} catch (error) {
  console.error('Query error:', error.message);
}
```

---

## Advanced Implementation Considerations

### Dynamic Operator Discovery

For a more flexible system, we might want to dynamically discover available operators:

```typescript
// adapter-factory.ts
export class DatabaseAdapterFactory {
  static getAdapter(databaseType: DatabaseType) {
    const adapters = {
      postgres: PostgreSQLAdapter,
      mongodb: MongoDBAdapter
    };

    if (!adapters[databaseType]) {
      throw new Error(`No adapter for ${databaseType}`);
    }

    return adapters[databaseType];
  }

  static getSupportedOperators(databaseType: DatabaseType) {
    const adapter = this.getAdapter(databaseType);
    return Object.keys(OPERATORS).filter(op =>
      adapter.supports(op as OperatorName)
    );
  }
}
```

### Type-Safe Operator Usage

We can enhance our type safety with interfaces:

```typescript
// user-queries.ts
interface UserQueryFilters {
  lastNameContains?: string;
  activeOnly?: boolean;
}

function buildUserQuery(filters: UserQueryFilters) {
  const builder = new QueryBuilder('postgres');

  if (filters.activeOnly) {
    builder.filter('equals', 'active', true);
  }

  if (filters.lastNameContains) {
    builder.filter('contains', 'last_name', filters.lastNameContains);
  }

  return builder.build();
}
```

### Transaction Support

For databases that support transactions:

```typescript
// query-builder.ts
class QueryBuilder {
  // ... existing code

  transaction() {
    const tx = {
      begin() {
        // Database-specific transaction start
        return this.adapter.startTransaction();
      },
      commit() {
        // Database-specific commit
        return this.adapter.commitTransaction();
      },
      rollback() {
        // Database-specific rollback
        return this.adapter.rollbackTransaction();
      },
      builder: new QueryBuilder(this.databaseType)
    };

    return tx;
  }
}
```

---

## Common Mistakes to Avoid

1. **Overly complex operator mappings**: Start simple and add complexity only when needed
   - ❌ Create 100 operators for every corner case upfront
   - ✅ Begin with core operators and add as you encounter real needs

2. **Ignoring performance implications**: Different databases optimize differently
   - PostgreSQL might use a different execution plan for JSONB vs. regex
   - MongoDB's `$regex` is less efficient than `$text` indexes

3. **Assuming all databases support your use cases**
   - Example: `arrayContains` might be implemented differently in each database
   - Some databases might not support this operator at all

4. **Not validating operator applicability**
   - Always check `supports()` before attempting to use an operator
   - Provide clear error messages when operators aren't available

5. **Tight coupling to specific implementations**
   - Avoid leaking database-specific details to application code
   - Keep all database knowledge contained within adapters

6. **Ignoring migration paths**
   - Design your matrix to be extensible for new databases
   - Consider how to add new databases to your system

---

## Key Takeaways

✅ **Database differences are inevitable** – Learn to work with them
✅ **Operator availability varies** – Some operators exist only in certain databases
✅ **The matrix pattern provides a structured way** to handle this complexity
✅ **Start with core operators** and expand as needed
✅ **Keep database knowledge localized** in adapters, not spread across application code
✅ **Always validate operator support** before using them
✅ **Consider performance implications** of each implementation
✅ **Design for extensibility** when adding new databases
✅ **Document your matrix** clearly for future developers
✅ **Test thoroughly across all supported databases**

---

## Conclusion

The Operator Availability Matrix pattern provides a powerful way to build flexible database APIs that work across different database systems. By centralizing operator knowledge in a structured matrix and implementing database-specific adapters, we can create clean abstractions that hide implementation details from our application code.

Remember that while this pattern gives us flexibility, it also introduces some complexity. The key is to implement it judiciously—starting with just the operators you need and expanding as your system grows. As your application evolves, you might find yourself adding more sophisticated features like:

- Operator performance metrics
- Database-specific query optimizations
- Dynamic query plan selection
- More advanced type mappings and transformations

The operator availability matrix isn't a silver bullet, but when applied thoughtfully, it can significantly reduce the complexity of building database-agnostic applications. The next time you're faced with a query that works in PostgreSQL but not MySQL, remember: you don't have to choose between them. With this pattern, you can have both.

---

## Further Exploration

To dive deeper into this topic:

1. **Database Abstraction Layers**: Explore existing projects like [Knex.js](https://knexjs.org/) or [Prisma](https://www.prisma.io/) that implement similar patterns

2. **Query Optimization**: Learn about how different databases optimize the same queries, and how to write portable queries that perform well everywhere

3. **Multi-Database Architectures**: Consider how this pattern fits into polyglot persistence strategies

4. **Testing Strategies**: Develop test approaches that verify your matrix works across all supported databases

As you continue your backend development journey, keep this pattern in your toolbox—it's an essential building block for scalable, flexible database applications.

---

Happy querying!
```