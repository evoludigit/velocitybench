```markdown
---
title: "Type Closure Testing: A Pattern for Uncovering Hidden Dependencies in Complex Systems"
date: 2023-10-15
author: "Alex Carter"
tags: ["database design", "API design", "testing patterns", "backend engineering", "domain-driven design"]
description: >
  Learn how the Type Closure Testing pattern helps you discover and verify implicit type relationships in your systems,
  catching bugs before they hit production. Practical examples included.
---

# Type Closure Testing: A Pattern for Uncovering Hidden Dependencies in Complex Systems

As backend engineers, we often find ourselves staring at exceptions in production logs:
```
TypeError: Cannot read property 'someField' of undefined
```
or SQL errors like:
```
ERROR: column "invalid_column" does not exist
```
These are often symptoms of a deeper problem: **implicit type relationships** that weren't properly validated during development.

In complex systems—especially those built using Domain-Driven Design (DDD) or microservices—entities, value objects, and domain services rely on strict type contracts. But how do you ensure that these contracts remain valid across code, database schemas, and API boundaries? This is where **Type Closure Testing** comes in—a pattern that systematically verifies all implicit type dependencies in your system.

---

## The Problem: Invisible Type Coupling

The problem isn't about missing type definitions—it's about **implicit coupling** that emerges when:

1. **Database schemas evolve independently** of the application code (e.g., migrations lag behind refactors)
2. **API contracts drift** between client and server (e.g., OpenAPI specs are outdated)
3. **Domain models outgrow their type safety** (e.g., a `User` entity gains a `premiumSubscription` field, but the `Subscription` model isn't properly anchored)
4. **Third-party integrations introduce new types** without proper validation (e.g., a payment processor returns a `Transaction` object with extra fields)

These issues manifest as:
- Silent failures (e.g., `null` fields in POST requests)
- Runtime type errors (e.g., `TypeError` when casting a field to an expected type)
- Data inconsistency (e.g., foreign keys broken due to schema changes)

Without intentional testing, these problems go unnoticed until users report them—and by then, fixing them is expensive.

### The Cost of Discovery
Imagine a payment service where:
- The frontend sends a `Request` object with a `currency` field
- The backend validates against `Currency` enum
- A migration renames `currency` to `isoCode`
- The frontend isn't updated, but users keep trying

Now every request fails with `currency` missing. How much time would you spend tracking this down? Would you have caught it earlier with automated validation?

---

## The Solution: Type Closure Testing

Type Closure Testing (TCT) is a pattern that treats **type validity as a contract**—just like API contracts or schema migrations. The goal is to:
1. **Capture all explicit and implicit type dependencies** in your system
2. **Test these dependencies in isolation** before they propagate to other components
3. **Enforce type consistency** across code, database, and API boundaries

The pattern borrows ideas from **graph traversal algorithms** (used in dependency injection) and **schema validation** (used in databases like Cassandra). It's particularly useful for systems with:
- Complex domain models (e.g., DDD aggregates)
- Polyglot persistence (mixing SQL, NoSQL, and message queues)
- Frequently changing schemas (e.g., microservices)

### Core Principle
Think of your system as a **type graph**:
- **Nodes** represent types (e.g., `User`, `Subscription`)
- **Edges** represent dependencies (e.g., `User` has a `Subscription`)

TCT ensures that every edge in this graph is **validated** for:
- **Existence**: Does the target type exist?
- **Backward compatibility**: Can old types still be used?
- **Forward compatibility**: Are new types valid?

---

## Components of Type Closure Testing

To implement TCT, you'll need these components:

### 1. **Type Graph Discovery Tool**
A utility to scan your codebase and generate a type graph. This could be a static analysis tool or a custom script.

### 2. **Validation Rules Engine**
Rules that define what constitutes a valid type relationship. Examples:
- A field of type `Subscription` must map to a table/collection with a `subscription_id` foreign key.
- A `User` object in an API response must include all non-sensitive fields from the database.

### 3. **Test Framework Integration**
A way to run validation checks as part of your CI/CD pipeline.

### 4. **Schema Synchronization Layer**
To bridge gaps between code types and database/API schemas.

---

## Practical Code Examples

Let’s walk through a concrete example using Node.js, TypeScript, and PostgreSQL.

### Example Scenario: E-commerce Order System

#### Domain Model
```typescript
// models.ts
export class Order {
  constructor(
    public orderId: string,
    public customerId: string,
    public items: OrderItem[],
    public status: OrderStatus
  ) {}
}

export class OrderItem {
  constructor(
    public productId: string,
    public quantity: number,
    public unitPrice: number
  ) {}
}

export type OrderStatus = 'CREATED' | 'PAID' | 'SHIPPED' | 'CANCELLED';
```

#### Database Schema
```sql
-- migrations/20231001_create_orders.sql
CREATE TABLE orders (
  order_id VARCHAR(36) PRIMARY KEY,
  customer_id VARCHAR(36) REFERENCES users(id),
  status VARCHAR(10) CHECK (status IN ('CREATED', 'PAID', 'SHIPPED', 'CANCELLED')),
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
  item_id SERIAL PRIMARY KEY,
  order_id VARCHAR(36) REFERENCES orders(order_id),
  product_id VARCHAR(36),
  quantity INT NOT NULL,
  unit_price DECIMAL(10, 2) NOT NULL
);
```

#### API Contract (OpenAPI)
```yaml
# openapi.yaml
paths:
  /orders:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrderRequest'
      responses:
        201:
          description: Order created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Order'
components:
  schemas:
    OrderRequest:
      type: object
      properties:
        customerId:
          type: string
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItemRequest'
    OrderItemRequest:
      type: object
      properties:
        productId:
          type: string
        quantity:
          type: integer
          minimum: 1
        unitPrice:
          type: number
          minimum: 0.01
    Order:
      allOf:
        - $ref: '#/components/schemas/OrderRequest'
        - type: object
          properties:
            orderId:
              type: string
            status:
              type: string
              enum: [CREATED, PAID, SHIPPED, CANCELLED]
```

### TCT Implementation

#### Step 1: Discover the Type Graph
We'll write a script to generate a graph of dependencies:
```typescript
// type-graph.ts
import { Class } from 'typescript';
import { readFileSync } from 'fs';

export function discoverTypeGraph() {
  const graph: Record<string, string[]> = {};

  // Load all TypeScript files
  const files = readTypeScriptFiles('src/models');
  for (const file of files) {
    const types = analyzeFile(file);
    for (const typeName of types) {
      graph[typeName] = [];
    }
  }

  // Analyze relationships (simplified for example)
  graph.Order = ['OrderItem']; // Order has items
  graph.OrderItem = ['Product']; // OrderItem references Product

  return graph;
}

function analyzeFile(filePath: string): string[] {
  const content = readFileSync(filePath, 'utf8');
  // Parse TypeScript to extract class names
  const classes = extractClasses(content);
  return [...new Set(classes)]; // Deduplicate
}
```

#### Step 2: Define Validation Rules
```typescript
// validators.ts
import { TypeGraph } from './type-graph';

export function validateTypeGraph(graph: TypeGraph, dbSchema: string, apiSpec: string) {
  const errors: string[] = [];

  // Rule 1: All types in code must exist in the database
  for (const [typeName, _] of Object.entries(graph)) {
    if (!dbSchema.includes(`CREATE TABLE ${typeName}`) &&
        !dbSchema.includes(`CREATE TYPE ${typeName}`)) {
      errors.push(`Type '${typeName}' not found in database.`);
    }
  }

  // Rule 2: API types must match code types
  if (!apiSpec.includes('OrderItemRequest')) {
    errors.push('API spec missing OrderItemRequest type.');
  }

  // Rule 3: Database foreign keys must match code dependencies
  if (graph.Order.includes('OrderItem') &&
      !dbSchema.includes('order_id VARCHAR(36) REFERENCES orders(order_id)')) {
    errors.push('Database missing foreign key for Order items.');
  }

  return errors;
}
```

#### Step 3: Run TCT in CI
Integrate the validation into your test suite:
```typescript
// tct.test.ts
import { discoverTypeGraph } from './type-graph';
import { validateTypeGraph } from './validators';
import { readFileSync } from 'fs';

describe('Type Closure Testing', () => {
  it('should validate type consistency', () => {
    const graph = discoverTypeGraph();
    const dbSchema = readFileSync('migrations/20231001_create_orders.sql', 'utf8');
    const apiSpec = readFileSync('openapi.yaml', 'utf8');

    const errors = validateTypeGraph(graph, dbSchema, apiSpec);
    if (errors.length > 0) {
      console.error('Type Closure Validation Errors:');
      errors.forEach(err => console.error(`- ${err}`));
      throw new Error('Type closure validation failed');
    }
  });
});
```

#### Step 4: Handle a Refactor Example
Let’s say we add a `shippingAddress` to `Order`:
```typescript
// Updated models.ts
export class Order {
  constructor(
    public orderId: string,
    public customerId: string,
    public items: OrderItem[],
    public status: OrderStatus,
    public shippingAddress: ShippingAddress // NEW!
  ) {}
}

export class ShippingAddress {
  constructor(
    public street: string,
    public city: string,
    public zipCode: string
  ) {}
}
```

Now, our TCT will fail because:
1. `ShippingAddress` isn't in the database.
2. The API spec doesn’t include `shippingAddress` in `Order`.

Run the test again:
```
Type Closure Validation Errors:
- Type 'ShippingAddress' not found in database.
- API spec missing shippingAddress in Order.
```

You’d then update the database and API spec:
```sql
-- Updated database
ALTER TABLE orders ADD COLUMN shipping_street VARCHAR(255);
ALTER TABLE orders ADD COLUMN shipping_city VARCHAR(100);
ALTER TABLE orders ADD COLUMN shipping_zip VARCHAR(20);
```

```yaml
# Updated API spec
components:
  schemas:
    Order:
      allOf:
        - $ref: '#/components/schemas/OrderRequest'
        - type: object
          properties:
            shippingAddress:
              type: object
              properties:
                street:
                  type: string
                city:
                  type: string
                zipCode:
                  type: string
```

---

## Implementation Guide

### Step 1: Audit Your Current System
1. **List all types** in your codebase (classes, interfaces, enums).
2. **List all database schemas** (tables, collections, types).
3. **List all API contracts** (OpenAPI, GraphQL schemas, etc.).
4. **Map dependencies** between these artifacts.

### Step 2: Choose a Discovery Tool
- **For TypeScript/JavaScript**: Use `ts-morph` or `typescript` AST parser.
- **For Java**: Use `jsr305` annotations or `JavaPoet` for reflection.
- **For Python**: Use `ast` module or `mypy` plugins.
- **For Database Schemas**: Parse SQL migrations or use ORM-generated metadata.

### Step 3: Define Validation Rules
Start with these critical rules:
1. **Existence**: All code types must exist in the database/API.
2. **Backward Compatibility**: Remove old types gracefully (e.g., add `is_deprecated` flag).
3. **Forward Compatibility**: New types must be optional where possible.
4. **Data Consistency**: Foreign keys must match code dependencies.

### Step 4: Integrate into CI/CD
Add TCT as a pre-commit step or a CI pipeline job. Example `.git hooked` script:
```bash
#!/bin/bash
# pre-commit-hook.sh
if git diff --cached --name-only | grep -E '\.(ts|js|sql|yaml)$'; then
  npm run test:tct || exit 1
fi
```

### Step 5: Gradually Introduce TCT
- Start with one module (e.g., `Order` subsystem).
- Expand to the entire codebase over time.
- Use TCT to catch regressions during refactoring.

---

## Common Mistakes to Avoid

### 1. **Overly Strict Validation**
   - **Problem**: Blocking all changes until TCT passes can slow down development.
   - **Solution**: Allow "pending" type changes with clear documentation. Use a `type-whitelist` or `type-blacklist` for critical systems.

### 2. **Ignoring Third-Party Types**
   - **Problem**: External APIs (e.g., payment processors) may change their types without notice.
   - **Solution**: Treat third-party types as "optional" and validate their presence only where critical.

### 3. **Not Updating TCT for Refactors**
   - **Problem**: Renaming a type but forgetting to update TCT rules.
   - **Solution**: Refactor types atomically—rename code first, then update TCT, then update database/API.

### 4. **Assuming Database and Code Are in Sync**
   - **Problem**: Migrations lag behind code changes.
   - **Solution**: Treat database schemas as "another codebase" and enforce version control (e.g., Git for migrations).

### 5. **Skipping API Contract Validation**
   - **Problem**: API clients and servers drift apart.
   - **Solution**: Use tools like `openapi-validator` or `spec-validator` to catch discrepancies early.

---

## Key Takeaways

- **Type Closure Testing is proactive**, not reactive. It catches issues before users report them.
- **It’s not about perfect consistency**, but about **catching regressions** when code and schemas diverge.
- **Start small**. Validate one subsystem thoroughly before expanding.
- **Automate everything**. TCT should run as part of your CI/CD pipeline.
- **Document type contracts**. Use comments or annotations to clarify non-obvious dependencies.

---

## Conclusion

Type Closure Testing is a powerful pattern for maintaining type consistency in large, evolving systems. While it requires upfront effort, the payoff is **fewer runtime errors, better maintainability, and faster debugging**.

Adopt TCT gradually. Start with a single module, then expand to the entire codebase. Over time, you’ll find that the cost of testing type closures is far less than the cost of fixing silent failures in production.

### Next Steps
1. **Audit your current system** for type inconsistencies.
2. **Implement TCT for one subsystem** (e.g., `User` or `Order`).
3. **Share the pattern** with your team to encourage adoption.

By treating type relationships as first-class contracts, you’ll build systems that are **resilient to change** and **easy to debug**.

---

## Appendix: Example TCT Tooling
For inspiration, check out these libraries that can help implement TCT:
- [TypeGraphQL](https://typegraphql.com/) (GraphQL + TypeScript)
- [Prisma Migrate](https://www.prisma.io/docs/guides/database/operations/migrate) (Schema migrations)
- [OpenAPI Generator](https://openapi-generator.tech/) (API contract validation)
- [SchemaSpy](http://schemaspy.org/) (Database schema visualization)

Happy testing!
```

---

This blog post provides a practical, code-first guide to Type Closure Testing, balancing theory with actionable examples. It addresses the pain points of type inconsistency while offering clear steps to implement the pattern. Would you like me to expand on any section?