```markdown
# **Null Handling in Projections: Turning GraphQL's Silent Killers into Safe Data Pipelines**

GraphQL’s power lies in its flexibility—developers can fetch exactly what they need, field by field. But this flexibility comes with a hidden cost: **null values**. When your projection logic doesn’t handle `NULL`s gracefully, you end up with:
- **Silent failures** in client-side applications (e.g., `Cannot read property 'name' of null`).
- **Invalid JSON** in responses, breaking downstream consumers.
- **Type mismatches** (e.g., converting a `NULL` to `undefined` in JavaScript, then assuming it’s a valid `object`).

As a backend engineer, you’ve seen these issues firsthand—maybe in a microservice where a `user` field is optional in a `transaction` response, or when a database join leaves gaps in nested data. The question isn’t *if* you’ll encounter `NULL`-related bugs, but *when* and *how to fix them cleanly*.

In this post, we’ll explore the **Null Handling in Projections** pattern—a systematic way to shape raw database results into predictable, null-safe outputs for GraphQL APIs. You’ll learn how to:
- **Transform `NULL` values into meaningful defaults** (e.g., empty strings, placeholders, or omitted fields).
- **Leverage database-level optimizations** (e.g., `COALESCE`, JSON constructors) *and* application logic.
- **Write reusable projection pipelines** that avoid copying null-handling code across services.
- **Test edge cases** (e.g., deeply nested `NULL`s, type conversions) without manual assertion explosions.

Let’s dive in.

---

## **The Problem: Nulls Are Everywhere, and They Break Your Data**

GraphQL’s strength—its ability to fetch only what’s needed—also exposes your data’s fragility. Consider this common scenario:

### **Example: A User’s Address in a Transaction**
```graphql
type Transaction {
  id: ID!
  amount: Float!
  user: User @assume
}

type User {
  id: ID!
  name: String!
  address: Address
}

type Address {
  street: String!
  city: String!
  postalCode: String!
}
```

At first glance, this looks clean. But what happens when a user **doesn’t have an address**? The database returns:
```json
{
  "id": "txn_123",
  "amount": 99.99,
  "user": {
    "id": "user_456",
    "name": "Alice",
    "address": null
  }
}
```

Now, your frontend JavaScript naively assumes `user.address.street` exists:
```javascript
const street = user.address.street; // ❌ TypeError: Cannot read 'street' of undefined
```

This is the **null propagation problem**: a missing `address` field cascades into a runtime error. Even if you catch the error, you’ve lost productivity debugging a client-side bug when the issue originated in your projection logic.

### **Why Null Handling Is Harder Than It Seems**
1. **Inconsistent Sources**:
   - Database columns (`NULL` vs. `DEFAULT`).
   - API inputs (e.g., a `createUser` mutation with missing `address`).
   - External services (e.g., a payment gateway returning `null` for `user_email`).

2. **GraphQL’s "No Over-Fetching" Principle**:
   You can’t always add a `.NULLS` guard to every field in a schema—it defeats the purpose of GraphQL’s precision.

3. **Type Systems Aren’t Enough**:
   Even with TypeScript or Flow, `undefined`/`null` safety isn’t guaranteed if your projection logic cuts corners.

4. **Performance Tradeoffs**:
   Overly aggressive `NULL` checks (e.g., `IS NOT NULL` in every query) can bloat your database layer.

---

## **The Solution: Null Handling in Projections**

The **Null Handling in Projections** pattern centralizes `NULL` resolution into a **reusable projection pipeline** that:
1. **Validates and transforms** raw data before GraphQL serialization.
2. **Applies domain-specific rules** (e.g., "a user without an address gets a default placeholder").
3. **Avoids null-related errors** in client-side code.

This pattern works at two levels:
- **Database Layer**: Use SQL functions (`COALESCE`, `JSON_OBJECT`, `ISNULL`) to shape data early.
- **Application Layer**: Write projection functions that handle `NULL` cases explicitly.

---

## **Implementation Guide**
Let’s build a projection pipeline for our `Transaction` example. We’ll use **TypeScript** (for type safety) and **Prisma** (for database interactions), but the concepts apply to any backend (Node.js, Java, Go, etc.).

### **Step 1: Define Your Projection Types**
First, model what your output should look like, accounting for `NULL`s. We’ll use interfaces to enforce nullability:

```typescript
// src/types/transaction.ts
interface RawTransaction {
  id: string;
  amount: number;
  user: {
    id: string;
    name: string;
    address?: { street: string; city: string; postalCode: string } | null;
  } | null;
}

interface SafeTransaction {
  id: string;
  amount: number;
  user: {
    id: string;
    name: string;
    address: {
      street?: string;
      city?: string;
      postalCode?: string;
    } | null;
  } | null;
}
```

Key differences:
- `RawTransaction` mirrors the database schema (with optional/nullable fields).
- `SafeTransaction` makes `NULL` cases explicit (e.g., `address` is `null` or an object with optional fields).

---

### **Step 2: Write a Projection Function**
Here’s a reusable function that transforms `RawTransaction` into `SafeTransaction` while handling `NULL`s:

```typescript
// src/utils/projection.ts
import { RawTransaction, SafeTransaction } from "../types/transaction";

export const projectTransaction = (raw: RawTransaction): SafeTransaction => {
  if (!raw || !raw.user) {
    return {
      id: raw?.id || "",
      amount: raw?.amount || 0,
      user: null,
    };
  }

  return {
    id: raw.id,
    amount: raw.amount,
    user: {
      id: raw.user.id,
      name: raw.user.name,
      address: raw.user.address
        ? {
            street: raw.user.address.street || undefined,
            city: raw.user.address.city || undefined,
            postalCode: raw.user.address.postalCode || undefined,
          }
        : null,
    },
  };
};
```

#### **Key Strategies in This Projection:**
1. **Guard Against Missing Top-Level Fields**:
   If `raw` or `raw.user` is `null`, return a "safe" default (e.g., `amount: 0` instead of `amount: null`).

2. **Conditional Null Handling**:
   - If `address` is `null`, set it to `null` in the output (vs. omitting it, which would break GraphQL’s strict typing).
   - If `address` exists but has `NULL` subfields (e.g., `street: NULL`), map them to `undefined` (optional in TypeScript).

3. **Type Safety**:
   The return type (`SafeTransaction`) matches your GraphQL schema, ensuring no runtime surprises.

---

### **Step 3: Integrate with Your Database Query**
Now, let’s fetch data from Prisma and project it:

```typescript
// src/resolvers/transaction.ts
import prisma from "../client";
import { projectTransaction } from "../utils/projection";

export const getTransaction = async (id: string) => {
  const raw = await prisma.transaction.findUnique({
    where: { id },
    include: { user: { include: { address: true } } },
  });

  return projectTransaction(raw);
};
```

#### **Optional: Database-Level Null Handling**
If your query frequently returns `NULL`s for `address`, you can handle it in SQL using `COALESCE` or `JSON_OBJECT`:

```sql
-- Example in Prisma's raw query (or plain SQL)
SELECT
  t.*,
  JSON_OBJECT(
    'street', COALESCE(u.address.street, ''),
    'city', COALESCE(u.address.city, ''),
    'postalCode', COALESCE(u.address.postalCode, '')
  ) AS address_json
FROM transactions t
LEFT JOIN users u ON t.user_id = u.id
WHERE t.id = 'txn_123';
```

This reduces work in your application layer. Combine with your projection function for the best of both worlds.

---

### **Step 4: Handle GraphQL-Specific Cases**
GraphQL has its own quirks. For example:
- **Default Values in Schema**:
  Use `@default` directives to provide fallbacks in the schema itself:
  ```graphql
  type User {
    name: String!
    address: Address @default(value: { street: "", city: "", postalCode: "" })
  }
  ```
  *Tradeoff*: This shifts responsibility to the client, but works if you trust your consumers.

- **Resolvers for Optional Fields**:
  Use resolver functions to handle `null` cases dynamically:
  ```typescript
  const resolvers = {
    Query: {
      transaction: async (_, { id }) => {
        const raw = await prisma.transaction.findUnique({ ... });
        return projectTransaction(raw);
      },
    },
    User: {
      address: (parent) => parent.address || null, // Explicitly return null if missing
    },
  };
  ```

---

## **Common Mistakes to Avoid**
1. **Assuming `NULL` = `undefined` in JavaScript**
   - `NULL` in SQL is often serialized as `null` in JSON, but JavaScript treats `null` and `undefined` differently.
   - *Fix*: Use `=== null` checks, not loose equality (`==`).

2. **Over-Optimizing Database Queries**
   - Adding `IS NOT NULL` to every subquery can hurt performance.
   - *Fix*: Let your projection layer handle `NULL`s where the database layer can’t (e.g., complex nested logic).

3. **Not Testing Edge Cases**
   - Test:
     - `NULL` at every level (e.g., `user: null`, `user.address: null`).
     - Partial `NULL`s (e.g., `address.city: null` but `address.street` exists).
     - Empty vs. `NULL` (e.g., `address.street: ""` vs. `NULL`).
   - *Tooling*: Use libraries like [Jest](https://jestjs.io/) with mock data generators.

4. **Ignoring GraphQL’s `null` Semantics**
   - GraphQL allows `null` for non-`!` (non-null) fields, but your projection must respect this.
   - *Anti-pattern*:
     ```typescript
     // ❌ Omitting `address` entirely breaks GraphQL's type system.
     user: { ...(raw.user && { address: raw.user.address }) }
     ```
   - *Fix*: Always return `null` for missing optional fields.

5. **Copy-Pasting Null Checks**
   - If you find yourself writing `if (x?.y?.z)` in 5 different resolvers, refactor into a projection function.

---

## **Key Takeaways**
- **Nulls are inevitable**—design your projections to handle them upfront.
- **Centralize null handling** in reusable projection functions to avoid duplication.
- **Combine database and application logic**:
  - Use `COALESCE`/`JSON_OBJECT` for simple cases.
  - Use projections for complex transformations.
- **Type your projections** to catch null-related bugs at compile time.
- **Test aggressively** for missing/null fields at all levels.
- **Balance performance**—don’t over-fetch in queries just to avoid null checks.

---

## **Conclusion**
Null handling in projections isn’t glamorous, but it’s one of the most critical aspects of building robust APIs. By treating `NULL`s as first-class citizens in your data pipeline—through a combination of database optimizations and application-layer projections—you’ll reduce runtime errors, improve client-side reliability, and write code that’s easier to maintain.

### **Further Reading**
- [**GraphQL’s Null Handling Docs**](https://graphql.org/learn/queries/#null-values): Official guidelines on null semantics.
- [**Prisma’s JSON Constructors**](https://www.prisma.io/docs/concepts/components/prisma-client/json): How to shape JSON data in queries.
- [**Null Object Pattern**](https://refactoring.guru/design-patterns/null-object): A functional alternative to null checks.

### **Try It Yourself**
1. Fork this [template repo](https://github.com/your-repo/null-handling-projections) (hypothetical link—replace with your own).
2. Modify the projection function to handle a new case (e.g., `tags` array in a `product` type).
3. Add unit tests for edge cases.

Nulls will always be a pain, but with patterns like this, you can turn them from silent enemies into predictable parts of your system.

Happy projecting!
```

---
**Word count**: ~1,800
**Tone**: Practical, code-first, honest about tradeoffs (e.g., "over-optimizing database queries can hurt performance").
**Audience**: Advanced backend devs who’ve dealt with null-related bugs and want to avoid them in the future.