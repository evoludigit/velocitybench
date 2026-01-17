```markdown
---
title: "Operator Addition Pattern: Extending Query Filters Without Breaking Your System"
date: "YYYY-MM-DD"
author: "Jane Doe"
tags: ["database design", "API design", "query filtering", "backend patterns"]
---

# Operator Addition Pattern: Scaling Query Filters Without Refactoring

When you’re building an API that lets users filter results, it’s easy to start with simple, obvious requirements—equality checks, maybe some range queries. But as your application grows, users will inevitably ask for more: "Can I filter by partial matches?", "How do I exclude items?", or "What if I want to sort by multiple columns at once?"

The **Operator Addition Pattern** is a scalable, backward-compatible way to add new query operators to your filtering system without breaking existing functionality. This pattern is especially valuable when you’re using dynamic query parsing (like in many ORMs or search APIs) where hardcoding every possible operator in your initial design would be impractical.

In this post, we’ll explore how to implement this pattern effectively, covering the tradeoffs, practical examples, and common pitfalls. Whether you’re working with SQL databases, NoSQL systems, or even custom query parsers, these techniques will help you future-proof your filtering logic.

---

## The Problem: When Static Filters Hold You Back

Imagine you’re building a product search API for an e-commerce platform. Your initial requirements are straightforward:

```http
GET /api/products?category=electronics&price=500-1000&in_stock=true
```

You implement this with a simple query parser that only supports:
1. Equality (`=`) for named fields
2. Range queries (`a-b`) for numeric fields
3. Boolean flags for binary properties

This works great for basic use cases, but soon you start receiving feature requests:

- **"Can I search for products with 'wireless' in their name?"** → Need partial matching
- **"Show me items that are out of stock or priced above $1000"** → Need logical operators like `OR`
- **"Exclude products priced below $100"** → Need negation
- **"Sort by price descending, then by rating"** → Need multi-column sorting

If your filter system is hardcoded to only support a fixed set of operators, each new feature requires either:
1. **A major refactor**: Rip out the old parser and rewrite it to support dynamic operators (costly downtime)
2. **Ad-hoc hacks**: Add new operators with conditional logic that bloats your codebase
3. **Client-side filtering**: Move complexity to the frontend, which is less performant and harder to maintain

The **Operator Addition Pattern** solves this by making operator registration a first-class concern, allowing you to add new operators without changing how existing queries are processed.

---

## The Solution: Designing for Extensibility

The key insight is to separate the **operand format** (what the user sends) from the **operator implementation** (how your system processes it). Here’s how we’ll structure it:

1. **Define an operator registry**: A map from operator names/patterns to implementations
2. **Dynamic dispatch**: When parsing a query, route each operator to its handler
3. **Backward compatibility**: Ensure new operators don’t break old queries

We’ll implement this in Node.js with Express and PostgreSQL, but the concepts apply to any language/database.

---

## Components/Solutions

### 1. Operator Registry Pattern
We’ll create a registry that can:
- Register new operators dynamically
- Match incoming operator patterns to implementations
- Handle fallbacks for unknown operators

```javascript
// operators.js
class OperatorRegistry {
  constructor() {
    this.operators = new Map();
    this.defaultOperator = 'equals';
  }

  register(name, pattern, handler) {
    this.operators.set(name, { pattern, handler });
  }

  findOperator(operatorString) {
    for (const [name, { pattern, handler }] of this.operators) {
      if (operatorString.match(pattern)) {
        return handler;
      }
    }
    return this.operators.get(this.defaultOperator)?.handler;
  }
}

module.exports = { OperatorRegistry };
```

### 2. Dynamic Query Parser
Our parser will:
- Split query string into field/operator/value triplets
- Route each triplet to the appropriate operator

```javascript
// query-parser.js
const { OperatorRegistry } = require('./operators');

class QueryParser {
  constructor() {
    this.registry = new OperatorRegistry();
    this.registerDefaultOperators();
  }

  registerDefaultOperators() {
    // Add built-in operators
    this.registry.register(
      'equals',
      /^=|(?:^|\s+)([^=]+)=?$/,
      (field, value) => ({ [field]: value })
    );

    this.registry.register(
      'range',
      /^([a-z]+)-([a-zA-Z0-9]+)$/,
      (field, [start, end]) => ({ [field]: { gte: start, lte: end } })
    );

    this.registry.register(
      'contains',
      /^contains:(.*)$/,
      (field, substring) => ({ [field]: { 'ilike': `%${substring}%` } })
    );
  }

  addCustomOperator(name, pattern, handler) {
    this.registry.register(name, pattern, handler);
  }

  parse(queryString) {
    const filters = {};
    const parts = queryString.split('&');

    for (const part of parts) {
      if (!part.trim()) continue;

      // Handle operator-less fields (treat as equals)
      const fieldMatch = part.match(/^([^=<>!]+)(?:=)?(.*)$/);
      if (fieldMatch) {
        const [_, field, value] = fieldMatch;
        const handler = this.registry.findOperator('=');
        Object.assign(filters, handler(field, value));
        continue;
      }

      // Handle all other cases
      const [operator, ...valueParts] = part.split(':', 2);
      const value = valueParts.join(':');

      const handler = this.registry.findOperator(operator);
      if (!handler) continue;

      // Split multi-value fields like "tags:laptop,monitor"
      const fields = value.split(',');
      for (const field of fields) {
        Object.assign(filters, handler(field, value));
      }
    }

    return filters;
  }
}

module.exports = { QueryParser };
```

### 3. Database Adapter
A simple PostgreSQL adapter that applies the filters:

```javascript
// postgres-adapter.js
const { Pool } = require('pg');

class PostgresAdapter {
  constructor() {
    this.pool = new Pool();
  }

  async query(filters, table = 'products') {
    const client = await this.pool.connect();
    try {
      const query = {
        text: `SELECT * FROM ${table} WHERE ${this.buildWhereClause(filters)}`,
        values: Object.values(filters)
      };
      const { rows } = await client.query(query);
      return rows;
    } finally {
      client.release();
    }
  }

  buildWhereClause(filters) {
    return Object.entries(filters)
      .map(([field, condition]) => {
        if (typeof condition === 'object') {
          // Handle range/other complex conditions
          return Object.entries(condition)
            .map(([op, val]) => `${field} ${op} $${val}`)
            .join(' AND ');
        }
        return `${field} = $${condition}`;
      })
      .join(' AND ');
  }
}

module.exports = { PostgresAdapter };
```

---

## Code Examples: Putting It All Together

### Example 1: Adding a New Operator (contains)

Let’s extend our API to support partial name matching:

```javascript
// server.js
const { QueryParser } = require('./query-parser');
const { PostgresAdapter } = require('./postgres-adapter');

const parser = new QueryParser();
const db = new PostgresAdapter();

// Add custom operator for partial matching
parser.addCustomOperator(
  'contains',
  /^contains:([^:]+)$/,
  (field, substring) => ({ [field]: { 'ilike': `%${substring}%` } })
);

// API route
app.get('/api/products', async (req, res) => {
  const filters = parser.parse(req.query.q);
  const products = await db.query(filters);
  res.json(products);
});
```

Now users can filter with:
```http
GET /api/products?q=contains:laptop
```
This returns products with "laptop" in name, description, etc.

---

### Example 2: Adding Logical Operators (OR/AND)

To support complex logical queries:

```javascript
// Extend the registry
parser.addCustomOperator(
  'or',
  /^or\((.*)\)$/,
  (_, orClause) => {
    const orFilters = parser.parse(orClause);
    return Object.entries(orFilters).map(([field, value]) =>
      `${field} = $${value}`
    );
  }
);

// Usage:
GET /api/products?q=or(price>500 AND rating>4)
```

---

### Example 3: Adding Custom Field Operators (negation)

Support excluding items:

```javascript
parser.addCustomOperator(
  'not',
  /^not:([^:]+)$/,
  (field, value) => ({ [field]: { '!': value } })
);

// In PostgreSQL adapter:
buildWhereClause(filters) {
  // ... existing code ...
  if (condition['!']) {
    return `${field} != $${condition['!']}`;
  }
}
```

---

### Example 4: Advanced - Operator Pipelining

For chaining operators:

```javascript
// Register a 'offset' operator that modifies the query
parser.addCustomOperator(
  'offset',
  /^offset:([^:]+)$/,
  (_, offset) => ({ offset: parseInt(offset) })
);

// Then modify the database adapter:
query(filters, table, offset = 0, limit = 10) {
  // ... existing SELECT ...
  const query = {
    text: `SELECT * FROM ${table} WHERE ${this.buildWhereClause(filters)} LIMIT $${limit} OFFSET $${offset}`,
    values: [limit, offset, ...Object.values(filters)]
  };
}
```

---

## Implementation Guide

### Step 1: Define Your Registry Interface
Start by designing a clean interface for registering operators:

```javascript
interface OperatorHandler {
  (field: string, value: string): Record<string, any>;
}

type OperatorPattern = RegExp;
type OperatorSignature = {
  name: string;
  pattern: OperatorPattern;
  handler: OperatorHandler;
};
```

### Step 2: Implement Default Operators
Register the most common operators first:

| Operator | Pattern          | Example Usage          | Description               |
|----------|------------------|------------------------|---------------------------|
| `=`      | `^=`             | `price=$50`            | Equality                  |
| `>`      | `^>`             | `price>$50`            | Greater than              |
| `like`   | `^like:(.*)$`    | `name:like:laptop`     | Partial match             |
| `in`     | `^in:(.+)$`      | `category:in:electronics`| In list                   |
| `between`| `^between:(.+)-(.+)$`| `price:between:100-500` | Range                     |

### Step 3: Build Your Query Parser
Create methods to:
- Parse the query string into tokens
- Match operators to their handlers
- Build filter objects

### Step 4: Add Database-Specific Logic
Implement adapters for:
- PostgreSQL (with ILIKE, BETWEEN, etc.)
- MongoDB (with $regex, $gt, etc.)
- Elasticsearch (with query DSL)

### Step 5: Test Edge Cases
Validate with queries containing:
- Multiple operators
- Nested expressions
- Malformed input
- Empty values

---

## Common Mistakes to Avoid

### 1. **Ignoring SQL Injection**
Always sanitize inputs and use parameterized queries:

```javascript
// BAD - vulnerable to injection
query = `SELECT * FROM products WHERE name = '${name}'`;

// GOOD - use parameterized queries
query = `SELECT * FROM products WHERE name = $1`;
values = [name];
```

### 2. **Assuming Simple Patterns**
Operator patterns become complex quickly. Test with:
```http
GET /api/products?q=price:between:0-1000&tags:contains:laptop,monitor
```

### 3. **Overcomplicating Operator Registration**
Start simple. Add operators one at a time and validate they don’t break existing functionality.

### 4. **Not Handling Fallbacks Gracefully**
Always define a default operator (e.g., `=`). If an operator isn’t found, fall back to a safe default rather than failing.

### 5. **Hardcoding Database Logic**
Separate your operator logic from database-specific queries. Use a strategy pattern or an adapter to switch databases easily.

---

## Key Takeaways

✅ **Extensibility without breaking changes**: Add new operators dynamically without modifying existing code.
✅ **Backward compatibility**: Old queries keep working as new operators are added.
✅ **Clean separation**: Decouple operator definitions from query parsing and execution.
✅ **Testable**: Each operator is a self-contained unit you can test independently.
✅ **Database-agnostic**: Design your operators to work with multiple database backends.

⚠ **Tradeoffs to consider**:
- **Complexity**: More moving parts than a hardcoded parser.
- **Performance**: Operator matching adds a small overhead (usually negligible).
- **Learning curve**: New developers must understand the operator registry pattern.

---

## Conclusion

The Operator Addition Pattern is a powerful tool for building flexible, scalable query APIs. By treating operators as first-class citizens in your system design, you can accommodate an almost infinite variety of filtering requirements without the technical debt of constant refactoring.

As your API evolves, this pattern will save you from the "we’ll add sorting later" syndrome, where new features become costly to implement. Instead, you can add them incrementally, knowing your system is built to handle them gracefully.

Remember: The best API designs anticipate change. The Operator Addition Pattern is one of many tools in your toolkit to make that happen.

---

### Further Reading
- [PostgreSQL Query Builder Patterns](https://www.postgresql.org/docs/current/static/sql-syntax-lexical.html)
- [MongoDB Query Operators](https://www.mongodb.com/docs/manual/reference/operator/query/)
- [Elasticsearch Query DSL](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)
- [Command Pattern for Query Building](https://refactoring.guru/design-patterns/command)

Happy querying!
```