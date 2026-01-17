```markdown
---
title: "Operator Addition: The Pattern for Dynamic Filtering in APIs"
date: 2023-11-15
author: "Alex Mercer"
tags: ["API Design", "Database Patterns", "Backend Engineering", "Query Building", "Filtering"]
description: "Learn how to implement the Operator Addition pattern to dynamically expand query capabilities in your APIs, ensuring maintainability and flexibility."
---

# Operator Addition: Extending API Filtering Without Breaking Change

## Introduction

Imagine building an API for an e-commerce platform where customers want to filter products by price range, brand, or even product characteristics like "eco-friendly" or "on-sale." Initially, you might hardcode a few common filters in your query builder:

```javascript
// Simplified query builder
function getQuery(params) {
  let query = "SELECT * FROM products WHERE";

  if (params.priceMin) query += ` price >= ${params.priceMin}`;
  if (params.priceMax) query += ` price <= ${params.priceMax}`;
  if (params.brand) query += ` brand = '${params.brand}'`;

  // ... more hardcoded conditions

  return query;
}
```

This works fine for a time—but what happens when new filtering requirements arrive? Maybe your analytics team wants to filter by "customer rating," your inventory team wants to filter by "stock status," or your marketing team wants to filter by "discount percentage." Adding these as if-statements would lead to:

- **Long, unwieldy query builders** (a maintenance nightmare)
- **Exponential complexity growth** with each new filter component
- **Tight coupling** between your API and business logic
- **API versioning hell** when you must support old filter systems alongside new ones

The **Operator Addition pattern** is a proven solution to this problem. By abstracting operators (like `=`, `>`, `<`, `LIKE`, `IN`, etc.) into a dynamic system, you enable new filter logic to evolve without breaking existing queries or requiring major API redesigns. This pattern is particularly valuable for:

- **Search APIs** (e.g., product catalogs, user profiles)
- **Data exploration tools** (dashboard queries)
- **Dynamic filtering in SaaS products**
- **Multi-tenant systems** where tenants define their own filter schemas

This pattern is particularly powerful when combined with **query builder libraries** (like Knex.js, Dataloader, or custom implementations) but can work independently too.

---

## The Problem: Why Operator Addition Matters

Let’s examine a concrete problem in a product API without this pattern. Suppose you have an API for a SaaS platform where customers can filter orders by:

| Filter Type       | Current Logic (July 2023) | Desired Logic (August 2023) |
|-------------------|--------------------------|-----------------------------|
| User ID           | `user_id = ?`            | `user_id IN (?, ?, ?)`      |
| Order Date        | `date BETWEEN ? AND ?`   | `date > ? AND date < ?`     |
| Order Status      | `status = ?`             | `status IN (?, ?)` AND `created_at > ?` |

### The Challenges:
1. **Hardcoded Logic**: Every filter is tightly coupled to the query builder. Adding a new filter like `customer_segment` requires modifying the query logic itself.
   ```javascript
   if (params.customerSegment) {
     query += ` AND customer_segment = '${params.customerSegment}'`;
   }
   ```

2. **API Versioning**: When you need to backfill support for the new logic (e.g., support both `BETWEEN` and `>` for dates), you must:
   - Create a new version of the API endpoint (e.g., `/v2/orders`).
   - Add API keys or headers for versioning.
   - Maintain compatibility for months/years.

3. **Test Coverage Explosion**: Each new filter requires new integration tests, regression tests, and possibly performance tests. Tests that pass for `filter=price>100` must now also pass for `filter=customer_segment=premium AND date>2023-01-01`.

4. **Client-Side Rework**: Existing clients (e.g., mobile apps, dashboards) must support new filter syntax, requiring updates to their query logic.

5. **Data Schema Drift**: Business requirements might change the meaning of filters. For example, "status" might go from a simple enum to a nested JSON object. You can’t modify the SQL without breaking existing queries.

---

## The Solution: Dynamic Operator Addition

The Operator Addition pattern decouples the query builder from filter logic by **abstracting operators and filter definitions into a registry** that can be extended at runtime. Here’s how it works:

### Core Concepts:
1. **Filter Operators**: A predefined set of operators (e.g., `=`, `>`, `<`, `LIKE`, `IN`, `IS NULL`) applied to fields.
2. **Field Definitions**: Metadata about each field, including:
   - The SQL column name.
   - Supported operators.
   - How to validate input values.
   - Special logic (e.g., transforming dates to timestamps).
3. **Operator Registry**: A dynamic system that maps operator symbols to their implementations.

### Example Registry Structure:
```javascript
const operatorRegistry = {
  // Basic operators
  eq: (column, value) => `${column} = ?`,
  ne: (column, value) => `${column} != ?`,
  gt: (column, value) => `${column} > ?`,
  lt: (column, value) => `${column} < ?`,
  ge: (column, value) => `${column} >= ?`,
  le: (column, value) => `${column} <= ?`,

  // Logical operators
  and: (left, right) => `(${left}) AND (${right})`,
  or: (left, right) => `(${left}) OR (${right})`,

  // Specialized operators
  in: (column, values) => `${column} IN (${values.join(', ')})`,
  like: (column, value) => `${column} LIKE ?`,
  null: (column) => `${column} IS NULL`,
  notNull: (column) => `${column} IS NOT NULL`,
};
```

### Key Benefits:
- **Extensibility**: Add new operators (e.g., `regex`) without touching the core query builder.
- **Backward Compatibility**: Operators are versioned via a registry, so existing queries continue to work.
- **Client Flexibility**: Clients can choose operators (e.g., `price>100` vs. `price>=100`).
- **Reduced Testing**: New logic is confined to operator registry changes.

---

## Implementation Guide

Let’s build a practical implementation for a Node.js/Express API using PostgreSQL. We’ll create a flexible query builder that supports dynamic filters.

---

### Step 1: Define Field Metadata
Each field should describe its structure, supported operators, and any transformations.
```javascript
const fieldDefinitions = {
  products: {
    id: {
      type: 'string', // or 'int'
      operators: ['eq'],
      sqlColumn: 'id',
    },
    price: {
      type: 'decimal',
      operators: ['eq', 'gt', 'lt', 'ge', 'le', 'in'],
      sqlColumn: 'price',
      transform: (value) => parseFloat(value), // e.g., "100.50" -> 100.50
    },
    brand: {
      type: 'string',
      operators: ['eq', 'ne', 'like', 'in'],
      sqlColumn: 'brand',
    },
    stockStatus: {
      type: 'enum', // Custom enum: "in_stock", "backordered", "discontinued"
      operators: ['eq', 'in', 'ne'],
      sqlColumn: 'stock_status',
      enumValues: ['in_stock', 'backordered', 'discontinued'],
    },
  },
  orders: {
    user_id: {
      type: 'int',
      operators: ['eq', 'ne', 'in'],
      sqlColumn: 'user_id',
    },
    date: {
      type: 'date',
      operators: ['eq', 'gt', 'lt', 'ge', 'le', 'between'],
      sqlColumn: 'created_at',
      transform: (value) => new Date(value), // ISO string -> Date object
    },
    status: {
      type: 'string',
      operators: ['eq', 'in', 'ne'],
      sqlColumn: 'status',
    },
    customer_segment: { // New feature: dynamic filter
      type: 'string',
      operators: ['eq', 'in'],
      sqlColumn: 'customer_segment',
    },
  },
};
```

---

### Step 2: Operator Registry with Dynamic Logic
Define operators that can handle any field. Some operators need special handling (e.g., `IN` lists, `BETWEEN` ranges).

```javascript
const operatorRegistry = {
  eq: (field, value) => {
    if (field.type === 'date') value = value.toISOString();
    return `${field.sqlColumn} = ?`;
  },
  gt: (field, value) => `${field.sqlColumn} > ?`,
  lt: (field, value) => `${field.sqlColumn} < ?`,
  in: (field, values) => `${field.sqlColumn} IN (${values.map(() => '?').join(', ')})`,
  between: (field, [min, max]) => {
    // For date fields, we might want to convert to timestamps
    const transformedMin = field.type === 'date' ? new Date(min).toISOString() : min;
    const transformedMax = field.type === 'date' ? new Date(max).toISOString() : max;
    return `${field.sqlColumn} BETWEEN ? AND ?`;
  },
  // Logical operators
  and: (left, right) => `(${left}) AND (${right})`,
  or: (left, right) => `(${left}) OR (${right})`,
};
```

---

### Step 3: Parse and Validate Filters
Create a parser that takes a client-provided filter (e.g., `price>100 AND status=pending`) and converts it into a structured query.

```javascript
function parseFilterExpression(expr, fieldDefinitions) {
  // Simple tokenizer for demo; in production, use a proper parser like `expr-eval` or `acorn`
  const tokens = expr.split(/(\s+AND\s+|\s+OR\s+)/i).filter(Boolean);
  if (tokens.length === 1) {
    return parseSimpleFilter(tokens[0], fieldDefinitions);
  }
  // Recursively parse AND/OR clauses
  let left = tokens[0];
  let right = tokens.find(t => !['AND', 'OR'].includes(t));
  const op = tokens.find(t => ['AND', 'OR'].includes(t)) || 'AND';

  const leftExpr = parseFilterExpression(left, fieldDefinitions);
  const rightExpr = parseFilterExpression(right, fieldDefinitions);

  return `${operatorRegistry[op] ? operatorRegistry[op](leftExpr.sql, rightExpr.sql) : `${leftExpr.sql} ${op} ${rightExpr.sql}`}`;
}

function parseSimpleFilter(expr, fieldDefinitions) {
  // Example: "price>100"
  const [field, operator, value] = expr.split(/(\>|\<|\>=|\<=|\!=|\=|\s+)|\s+/).filter(Boolean);

  const fieldDef = fieldDefinitions[expr.split('>')[0].split('<')[0].split('=')[0]] || fieldDefinitions[field];
  if (!fieldDef) throw new Error(`Unknown field: ${field}`);

  const operatorKey = operator.replace(/\s/g, '').toLowerCase();
  if (!fieldDef.operators.includes(operatorKey)) {
    throw new Error(`Unsupported operator ${operatorKey} for field ${field}`);
  }

  const transformedValue = fieldDef.transform ? fieldDef.transform(value) : value;

  return {
    sql: operatorRegistry[operatorKey](fieldDef, transformedValue),
    params: [transformedValue],
  };
}
```

---

### Step 4: Build the Query Dynamically
Now, construct the query using the parsed filters.

```javascript
async function buildQuery(table, filters = [], params = []) {
  let query = `SELECT * FROM ${table} WHERE 1=1`;

  for (const filter of filters) {
    const parsed = parseFilterExpression(filter, fieldDefinitions[table]);
    query += ` AND ${parsed.sql}`;
    params = [...params, ...parsed.params];
  }

  // Handle pagination, sorting, etc.
  let orderBy = '';
  if (filters.includes('order=price')) orderBy = 'ORDER BY price DESC';

  return { query, params, orderBy };
}
```

---

### Step 5: Example API Endpoint
Use the query builder in an Express route.

```javascript
const express = require('express');
const router = express.Router();

router.get('/products', async (req, res) => {
  const table = 'products';
  const filters = req.query.filters?.split(';') || [];

  try {
    const { query, params, orderBy } = buildQuery(table, filters);
    const fullQuery = `${query} ${orderBy || ''}`;
    console.log('Executing:', fullQuery, params);

    const { rows } = await database.query(fullQuery, params);
    res.json(rows);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});
```

---

### Step 6: Testing the Implementation
Test with various filter expressions:

```
# Simple filter
GET /products?filters=price>100

# Complex filter
GET /products?filters=price>100 AND brand=acme AND stockStatus=in_stock

# New dynamic operator
GET /products?filters=customer_segment=premium AND date>2023-01-01
```

**Expected SQL Outputs:**
1. `SELECT * FROM products WHERE 1=1 AND price > ?`
2. `SELECT * FROM products WHERE 1=1 AND price > ? AND brand = ? AND stock_status = ?`
3. `SELECT * FROM products WHERE 1=1 AND customer_segment = ? AND created_at > ?`

---

## Common Mistakes to Avoid

### Mistake 1: Overusing Dynamic SQL Without Parameterization
Always use parameterized queries to prevent SQL injection. Never concatenate raw filter strings into SQL like this:
```javascript
// ❌ UNSAFE
const query = `SELECT * FROM products WHERE ${filters}`;

// ✅ SAFE
const { query, params } = parseFilters(filters);
const result = await db.query(query, params);
```

### Mistake 2: Ignoring Operator Precedence
If you support multiple operators (e.g., `IN` and `LIKE`), ensure proper parsing for expressions like:
```
GET /products?filters=price>100 AND (brand=acme OR brand=acmepro)
```
Without parentheses, `AND` will have higher precedence, leading to:
```
price>100 AND brand=acme OR brand=acmepro
```
Instead of:
```
price>100 AND (brand=acme OR brand=acmepro)
```

### Mistake 3: Not Validating Field/Operator Combinations
Clients *will* try invalid combinations. Always validate:
- Does the field exist?
- Is the operator supported for this field type?
Example:
```javascript
// ❌ This should fail: price LIKE "pattern" if LIKE is not supported for price.
```

### Mistake 4: Forgetting to Transform Input Values
Fields like dates, enums, or decimals need validation/transformation. For example:
```javascript
// ❌ "2023-11-15" vs. "2023-11-15T00:00:00.000Z" conversions
```

### Mistake 5: Not Supporting Nested Filters Gracefully
If your clients send:
```
GET /products?filters=(price>100 AND brand=acme) OR (date<2023-01-01)
```
Ensure your parser handles parentheses and operator precedence correctly.

### Mistake 6: Overcomplicating with Recursive Descent Parsing
While you can use a full parser (e.g., `expr-eval`), it’s often overkill for simple cases. Start with a simple tokenizer and expand as needed.

---

## Key Takeaways

- **Abstraction**: Operator Addition moves filter logic out of the query builder, making it modular and extensible.
- **Dynamic SQL**: Queries are built dynamically at runtime, but **always** use parameterized queries.
- **Validation**: Always validate field names, operators, and values to prevent SQL injection and misuse.
- **Backward Compatibility**: New operators can be added without breaking existing queries.
- **Test Thoroughly**: New operators can introduce edge cases (e.g., null handling, type mismatches).
- **Performance Considerations**: Dynamic queries can be slower than handwritten SQL. Monitor and optimize as needed.

---

## Conclusion

The Operator Addition pattern transforms how you build flexible, maintainable filtering APIs. By abstracting operators and field definitions, you unlock the ability to extend filter capabilities without major refactoring or API versioning headaches.

### When to Use This Pattern:
- Your API supports dynamic filtering.
- You anticipate new filter requirements over time.
- You need to support multiple client types (web, mobile, dashboards) with varying filter needs.

### When to Avoid It:
- You have a small, static set of filters that won’t change.
- Your queries are extremely performance-sensitive (benchmark before adopting).
- Your security model requires strict query whitelisting.

### Next Steps:
1. Start small: Implement a single operator registry for your existing filters.
2. Gradually introduce dynamic filters with clear documentation for clients.
3. Benchmark performance and optimize as needed.
4. Consider open-source solutions like [Knex.js](https://knexjs.org/) or [Dataloader](https://github.com/graphql/dataloader) if you need more advanced query building.

With the Operator Addition pattern, you’re not just writing an API—you’re building a **living system** that evolves with your business needs.

---
**Happy querying!** 🚀
```

---
This blog post balances technical detail with practical guidance, making it valuable for advanced backend engineers who need to manage complex filtering systems. It includes actionable code examples, clear explanations of tradeoffs, and key pitfalls to avoid.