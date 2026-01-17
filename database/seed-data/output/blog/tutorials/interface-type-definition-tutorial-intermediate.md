```markdown
---
title: "Interface Type Definition: Unifying Your API with Shared Field Contracts"
date: "2023-11-15"
tags: ["API Design", "Database Patterns", "Interface Segregation", "Backend Engineering"]
author: "Alex Carter"
description: "Learn how the Interface Type Definition pattern (ITD) helps standardize shared fields across your database and API layers, reducing duplication and improving maintainability."
---

# Interface Type Definition: Unifying Your API with Shared Field Contracts

As backend engineers, we often juggle multiple data models—API schemas, database tables, event payloads, and business domain objects. Writing the same field definitions repeatedly in each layer is tedious, error-prone, and leads to **inconsistencies** when updates are needed. This is where the **Interface Type Definition (ITD)** pattern comes in.

The ITD pattern is a **shared definition contract** for fields (like `id`, `createdAt`, `updatedAt`) that appear across multiple domains in your system. Instead of duplicating these fields in every schema, you define them **once** in a shared contract, then **reference** them wherever needed. This reduces boilerplate, improves consistency, and makes updates easier.

In this post, we’ll explore how ITDs solve real-world problems in backends, walk through a full implementation (with code examples), and discuss tradeoffs, anti-patterns, and best practices.

---

## The Problem: The Duplication & Inconsistency Trap

Imagine you’re building a modern SaaS application with:
- A **PostgreSQL database** for persistent storage
- A **GraphQL API** for frontends
- A **Kafka topic** for event publishing
- A **payment service** with its own schema

Here’s the **real-world headache** this creates:

### 1. **Boilerplate Hell**
Every new entity (e.g., `User`, `Order`, `Product`) requires redundant field definitions across all schemas:

```javascript
// Database (PostgreSQL)
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  ...other fields...
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  user_id INT REFERENCES users(id),
  status VARCHAR(50),
  ...other fields...
);
```

```javascript
// GraphQL API (TypeScript)
type User {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  name: String!
  email: String!
}

type Order {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  userId: ID!
  status: String!
}
```

```javascript
// Kafka Event (Schema Registry)
{
  "type": "user_created",
  "payload": {
    "id": 123,
    "createdAt": "2023-11-15T10:00:00Z",
    "updatedAt": "2023-11-15T10:00:00Z",
    "name": "Alex"
  }
}
```

### 2. **Inconsistent Updates**
When you need to change a shared field (e.g., `updatedAt` to be nullable or add validation), you have to **update every schema manually**. This is error-prone and slows down iteration.

### 3. **Tight Coupling**
Schemas are tightly coupled to their domain (e.g., `users` table only knows about its own fields). Adding a new shared field like `auditLog` requires **refactoring every table and API endpoint**.

### 4. **Difficult Refactoring**
What if you decide to split `createdAt` and `updatedAt` into `createdOn` and `modifiedOn`? Without a single source of truth, you risk **breaking changes** across the system.

---
## The Solution: **Interface Type Definition (ITD)**

The **Interface Type Definition** pattern is a **contract-based approach** to standardize shared fields across your system. Here’s how it works:

1. **Define shared fields once** in a **central location** (e.g., JSON schema, TypeScript interface, or database view).
2. **Reference these fields** in your domain-specific schemas (API, DB, events) using imports or inheritance.
3. **Update shared fields in one place**—all consuming systems sync automatically.

### Key Benefits:
- **Single Source of Truth**: No more duplicate definitions.
- **Consistency Guaranteed**: Shared fields stay in sync across all layers.
- **Easier Refactoring**: Change a field in the ITD, and all dependent schemas update.
- **Decoupled Design**: Domain-specific schemas focus only on their unique fields.

---

## Components of the ITD Pattern

An ITD system typically includes:

1. **Shared Field Contracts** (e.g., `BaseModelSchema.json`)
2. **Domain-Specific Extensions** (e.g., `UserModelSchema.json` extends `BaseModelSchema`)
3. **Tooling** to merge contracts (e.g., schema merge scripts, TypeScript extends)
4. **Validation Layers** (e.g., Zod, JSON Schema, or database constraints)

---

## Implementation Guide: A Practical Example

Let’s build an ITD system step by step using **TypeScript interfaces** (for API schemas) and **PostgreSQL views** (for database unification).

### 1. Define Shared Fields in a Contract

Create a file `schemas/base-model.ts`:

```typescript
// schemas/base-model.ts
export interface BaseModel {
  id: string;                     // Unique identifier
  createdAt: string;              // ISO timestamp (creation)
  updatedAt: string;              // ISO timestamp (last update)
  isActive: boolean;              // Soft delete flag
  metadata?: Record<string, unknown>; // Extension support
}
```

### 2. Extend for Domain-Specific Models

Now, define your domain models by **extending** `BaseModel`:

```typescript
// schemas/user-model.ts
import { BaseModel } from './base-model';

export interface UserModel extends BaseModel {
  email: string;
  name: string;
  role: 'admin' | 'user';
}
```

```typescript
// schemas/order-model.ts
import { BaseModel } from './base-model';

export interface OrderModel extends BaseModel {
  userId: string;
  amount: number;
  status: 'pending' | 'completed' | 'failed';
}
```

### 3. Unify Database Schemas with Views

For PostgreSQL, create a **base view** for shared fields and **extend it** in domain views:

```sql
-- shared/base_model_view.sql
CREATE VIEW base_model_view AS
SELECT
  id,
  created_at AS createdAt,
  updated_at AS updatedAt,
  is_active AS isActive,
  metadata
FROM (
  SELECT * FROM jsonb_to_record('{"id": text, "created_at": timestamp, "updated_at": timestamp, "is_active": boolean, "metadata": jsonb}') AS t(id text, created_at timestamp, updated_at timestamp, is_active boolean, metadata jsonb)
) AS temp;
```

Wait, that’s abstract. Let’s make it concrete. Instead, we’ll create **table-level constraints** and **views** to enforce the ITD.

Here’s a better approach:

```sql
-- Create a shared table for base fields (if needed)
CREATE TABLE if not exists base_model (
  id UUID PRIMARY KEY,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  metadata JSONB
);

-- Extend users table to include base_model columns (not repeated, but inherited via constraints)
CREATE TABLE users (
  id UUID PRIMARY KEY REFERENCES base_model(id),
  email VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'user')),
  -- Foreign key for base_model is handled by inheritance
  CONSTRAINT fk_base_model FOREIGN KEY (id) REFERENCES base_model(id)
);

-- Create a unified view for users that includes base_model fields
CREATE VIEW user_with_base AS
SELECT
  u.*,
  b.created_at AS base_created_at,
  b.updated_at AS base_updated_at,
  b.is_active AS base_is_active
FROM users u
LEFT JOIN base_model b ON u.id = b.id;
```

*Note: This is a simplified approach. In production, you’d likely use **inheritance** (PostgreSQL `INHERITS`) or **JSON columns** to avoid repeating fields. See the "Tradeoffs" section for details.*

### 4. Sync API Schemas with Base Contracts

Use **TypeScript generics** to enforce ITDs in your API:

```typescript
// api/types.ts
import { BaseModel } from '../schemas/base-model';

export type ApiUser = Omit<UserModel, keyof BaseModel> & {
  base: BaseModel;
};
```

Then, validate requests/responses with this contract:

```typescript
// api/resolvers.ts
import { z } from 'zod';
import { BaseModel, UserModel } from '../schemas';

const UserSchema = z.object({
  ...BaseModel,
  email: z.string().email(),
  name: z.string().min(1),
  role: z.union([z.literal('admin'), z.literal('user')])
});

export const createUser = async (input: z.infer<typeof UserSchema>) => {
  // Validate against ITD
  const parsed = UserSchema.parse(input);
  // ... save to DB
};
```

### 5. Automate with Scripts

Write a script to **merge schemas** and generate API/OpenAPI docs:

```typescript
// scripts/generate-schemas.ts
import { readFileSync, writeFileSync } from 'fs';
import { BaseModel } from '../schemas/base-model';
import { UserModel } from '../schemas/user-model';

const mergedUserSchema = {
  ...BaseModel,
  ...UserModel,
};

writeFileSync(
  'api/generated/user-openapi.yml',
  `openapi: 3.0.0
info:
  title: User API
paths:
  /users:
    post:
      requestBody:
        content:
          application/json:
            schema: ${JSON.stringify(mergedUserSchema)}`
);
```

---

## Common Mistakes to Avoid

1. **Over-Extending the ITD**
   *Problem*: If you include **too many** shared fields (e.g., `lastLogin`, `ipAddress`), you’ll create a **monolithic base model** that forces every domain to use it.
   *Solution*: Keep ITDs focused on **universal fields** (e.g., `id`, `createdAt`). Domain-specific fields should remain in their own schemas.

2. **Ignoring Database Constraints**
   *Problem*: Defining ITDs in TypeScript/API layers but **not in the database** leads to inconsistencies (e.g., a missing `NOT NULL` constraint).
   *Solution*: Enforce ITDs in **both** schema layers:
     ```typescript
     // TypeScript
     export interface BaseModel {
       id: string;      // Required
       createdAt: string; // Required
     }
     ```
     ```sql
     -- SQL
     ALTER TABLE users ADD CONSTRAINT not_null_id CHECK (id IS NOT NULL);
     ```

3. **Static ITDs Only**
   *Problem*: Hardcoding ITDs in JSON/TypeScript **doesn’t handle dynamic changes** (e.g., soft delete renamed to `deletedAt`).
   *Solution*: Use **feature flags** or **migration scripts** to evolve ITDs over time.

4. **Not Versioning ITDs**
   *Problem*: Breaking changes in ITDs (e.g., dropping `isActive`) can **cascade failures** across services.
   *Solution*: Version your ITDs (e.g., `BaseModelV1`, `BaseModelV2`) and deprecate old versions.

5. **Forgetting to Update Clients**
   *Problem*: Changing ITDs (e.g., adding `metadata`) may **break existing clients** if not documented.
   *Solution*: Use **backward-compatible updates** (e.g., optional fields) and versioned schemas.

---

## Key Takeaways

### ✅ **Do:**
- **Centralize shared fields** in one source of truth (TypeScript, JSON schema, or database views).
- **Extend ITDs** for domain-specific models (e.g., `UserModel` extends `BaseModel`).
- **Validate ITDs** in all layers (API, DB, events) to catch inconsistencies early.
- **Automate schema merging** to reduce manual errors.
- **Document breaking changes** and plan migrations carefully.

### ❌ **Don’t:**
- Include **domain-specific fields** in ITDs (e.g., `status` for `Order` belongs in `OrderModel`, not `BaseModel`).
- Assume ITDs are **silver bullets**—they require discipline to maintain.
- Ignore **database constraints** when defining ITDs.
- Update ITDs **without backward compatibility** in mind.

---

## Tradeoffs & Real-World Considerations

### 1. **Performance Overhead**
- **Problem**: Views and inheritance can add **query complexity** in PostgreSQL.
- **Solution**: Cache frequently accessed ITD fields or use **materialized views** for performance.

### 2. **Migration Complexity**
- **Problem**: Changing ITDs (e.g., adding a column) requires **updating all dependent tables**.
- **Solution**: Use **database migrations** (e.g., Flyway, Liquibase) and **versioned ITDs**.

### 3. **Tooling Dependencies**
- **Problem**: ITDs require **additional tooling** (e.g., schema merging scripts, OpenAPI generators).
- **Solution**: Start small—manually merge schemas for core ITDs, then automate later.

### 4. **Tight Coupling to Base Types**
- **Problem**: If ITDs are **too broad**, they can **limit flexibility** in domain models.
- **Solution**: Keep ITDs **minimal** (e.g., only `id`, `createdAt`, `updatedAt`) and extend only when necessary.

---

## When to Use (and Avoid) ITDs

### **Use ITDs When:**
- You have **multiple schemas** (API, DB, events) with **repeated fields**.
- Your system **scales across services** (microservices, serverless).
- You want **consistency** and **easier refactoring**.

### **Avoid ITDs When:**
- Your system is **small and simple** (e.g., a single monolith with no shared fields).
- Fields are **highly domain-specific** and rarely reused.
- You **lack tooling** to merge/validate schemas.

---

## Conclusion: Unify Your Schemas with ITDs

The **Interface Type Definition** pattern is a **practical way to decouple shared fields** from domain-specific logic in your backend. By defining contracts once and reusing them across APIs, databases, and event systems, you:
- **Reduce duplication** and **boilerplate**.
- **Enforce consistency** across your stack.
- **Simplify refactoring** when requirements change.

Start small—define ITDs for **universal fields** like `id`, `createdAt`, and `updatedAt**, then gradually expand as your system grows. Combine ITDs with **automated validation** (Zod, JSON Schema) and **database constraints** to keep everything in sync.

---
### Next Steps:
1. **Try ITDs in your project**: Start with just `id`, `createdAt`, and `updatedAt`.
2. **Automate schema merging**: Use scripts or tools like [`json-schema-ref-resolver`](https://github.com/microsoft/json-schema-ref-resolver).
3. **Version your ITDs**: Plan for backward compatibility when evolving contracts.

By embracing ITDs, you’ll trade a bit of initial setup for **years of maintainability**—a win for any backend engineer.

---
### Further Reading:
- [PostgreSQL Inheritance vs. JSONB](https://www.citusdata.com/blog/postgresql-inheritance-vs-jsonb/)
- [Zod for Runtime Type Validation](https://github.com/colinhacks/zod)
- [OpenAPI 3.0 Documentation](https://swagger.io/specification/)

---
*What’s your experience with shared field patterns? Have you used ITDs or something similar? Share your thoughts in the comments!*
```