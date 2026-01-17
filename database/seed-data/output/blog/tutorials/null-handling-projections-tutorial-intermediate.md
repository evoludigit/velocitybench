```markdown
---
title: "Null Handling in Projections: A Pragmatic Guide for Backend Developers"
date: 2023-08-15
tags: ["database", "API design", "GraphQL", "projections", "backend engineering"]
author: "Alex Carter"
---

# Null Handling in Projections: A Pragmatic Guide for Backend Developers

When you're building APIs—especially GraphQL ones—you quickly realize that data doesn't always arrive as neatly packaged as you'd like. Fields might be missing, values could be `NULL`, and type mismatches can turn a simple query into a confusing mess. If you don't handle these edge cases thoughtfully, you'll end up with inconsistent responses, frustrated clients, or even security vulnerabilities.

This happens because projections—the process of shaping database results into API-friendly objects—are often treated as a black box. We write a query, get back a bunch of rows, and hope for the best. But real-world data is messy. Users might leave fields blank, systems might log inconsistent formats, and legacy databases might return `NULL` for any number of reasons.

In this post, we'll explore **Null Handling in Projections**, a design pattern that ensures your API responses are clean, predictable, and resilient to data inconsistencies. We'll cover:
- Why nulls and missing fields matter in API design
- How to structure projection logic for robustness
- Practical examples in JavaScript/TypeScript (Node.js) and SQL
- Common pitfalls and how to avoid them

Let’s dive in.

---

## The Problem: When Nulls and Missing Fields Break Your API

Imagine this scenario: You’re building a GraphQL API for an e-commerce platform, and one of your resolvers looks like this:

```javascript
// ❌ Fragile resolver that doesn't handle edge cases
const getProduct = async ({ productId }) => {
  const product = await db.query(
    'SELECT * FROM products WHERE id = ?',
    [productId]
  );

  return product[0]; // Crashes if product is null or fields are incomplete
};
```

What could go wrong? A lot.

1. **Null responses**: If the product doesn’t exist, `product` could be `null`, and `product[0]` would throw an error.
2. **Inconsistent fields**: Some products might have a `price` field, while others might have a `discountedPrice`, but your clients expect a standardized structure.
3. **Type mismatches**: A `createdAt` field might return a string in some databases but a timestamp in others.
4. **Missing optional fields**: A client might request a `shippingInfo` field, but some products don’t have one.

Now, multiply this by hundreds of queries, and you’ll have a client-side nightmare: inconsistent data shapes, failed validations, and wasted API calls retrying the same invalid data.

This is where **projection logic**—the process of transforming raw database results into API-friendly objects—comes into play. But raw projections often lack null handling, leaving your API vulnerable. The solution? Build a **projection layer that explicitly handles nulls, missing fields, and type conversions**.

---

## The Solution: Null-Aware Projections

Null-aware projections are a **defensive design pattern** that ensures your API responses are always in a predictable state, regardless of the underlying data. Here’s how it works:

1. **Explicit null checks**: Replace implicit assumptions (like "this field must exist") with explicit handling.
2. **Default values or null indicators**: Decide whether to provide defaults (e.g., `price: 0`) or null indicators (e.g., `price: null`).
3. **Type normalization**: Convert inconsistent types (e.g., strings vs. numbers) into a single format.
4. **Structural consistency**: Ensure all responses have the same shape, even for missing optional fields.

### Key Principles:
- **Fail fast**: If a required field is truly missing, return a meaningful error (e.g., `400 Bad Request`).
- **Don’t lie**: Avoid returning `false` or `0` for null values unless it makes semantic sense. Clients should be able to distinguish between "value is 0" and "value is missing."
- **Be explicit**: Use `null` or `undefined` (or a placeholder object) to indicate missing data, rather than relying on implicit absence.

---

## Components of a Null-Aware Projection Layer

Let’s break down the components of a robust projection system. We’ll use a Node.js/TypeScript example with PostgreSQL, but the principles apply to any backend stack.

### 1. Database Query Layer
First, write queries that are **safe against nulls**. For example:

```sql
-- ⚠️ Vulnerable to nulls
SELECT * FROM products WHERE id = $1;

-- ✅ Explicitly handle nulls (e.g., return empty rows if not found)
SELECT
  id,
  name,
  price,
  discount_price AS discounted_price,
  shipping_info->>'address' AS shipping_address,
  COALESCE(created_at, NOW()::timestamp) AS created_at
FROM products
WHERE id = $1
LIMIT 1;
```

Key techniques:
- Use `COALESCE` or `NVL` for default values.
- Cast fields to consistent types (e.g., `timestamp` instead of `text`).
- Use JSON operators (`->>`) to safely extract nested fields.

---

### 2. Projection Function (TypeScript)
Next, define a projection function that transforms raw database results into a clean API response. Here’s an example:

```typescript
// 🔹 Projection function for a Product
interface RawProduct {
  id: string;
  name: string | null;
  price: number | null;
  discounted_price: number | null;
  shipping_address: string | null;
  created_at: string | null;
}

interface ProductResponse {
  id: string;
  name: string;
  price: number | null;
  discounted_price: number | null;
  shippingInfo: {
    address?: string; // Optional because it might be null
  } | null;
  createdAt: Date | null;
}

function projectProduct(rawProduct: RawProduct | null): ProductResponse {
  if (!rawProduct) {
    throw new Error("Product not found");
  }

  return {
    id: rawProduct.id,
    name: rawProduct.name || "(No name provided)", // Fallback for nulls
    price: rawProduct.price, // Let it be null if truly missing
    discounted_price: rawProduct.discounted_price,
    shippingInfo:
      rawProduct.shipping_address
        ? { address: rawProduct.shipping_address }
        : null,
    createdAt: rawProduct.created_at ? new Date(rawProduct.created_at) : null,
  };
}
```

### Why This Works:
- **Null checks**: The function explicitly handles `rawProduct` being `null`.
- **Optional fields**: `shippingInfo` is optional and can be `null` if the address is missing.
- **Type safety**: The `ProductResponse` interface documents the expected shape, including `null` possibilities.

---

### 3. API Resolver (GraphQL Example)
Now, use the projection function in your GraphQL resolver:

```typescript
const productResolver = async (parent: any, args: { id: string }) => {
  const rawProduct = await db.query(
    'SELECT id, name, price, discounted_price, shipping_info FROM products WHERE id = $1',
    [args.id]
  );

  return projectProduct(rawProduct[0]);
};
```

---

## Implementation Guide: Step-by-Step

### Step 1: Define Your API Response Schema
Before writing any projection logic, **document the expected shape of your responses**. Use interfaces or GraphQL schemas to clarify:
- Which fields are required vs. optional.
- What types clients expect (e.g., `Date` vs. `string`).

Example (TypeScript):
```typescript
interface UserResponse {
  id: string;
  email: string; // Required
  fullName: string | null; // Optional
  preferences: {
    theme: "light" | "dark";
    notifications: boolean;
  } | null; // Optional
}
```

### Step 2: Write Safe Database Queries
Always assume the database might return `NULL` or inconsistent types. Use techniques like:
- `COALESCE` for defaults:
  ```sql
  SELECT COALESCE(price, 0) AS price FROM products;
  ```
- Type casting:
  ```sql
  SELECT CAST(created_at AS TIMESTAMP) FROM products;
  ```
- JSON extraction:
  ```sql
  SELECT shipping_info->>'city' AS city FROM products;
  ```

### Step 3: Implement Projection Logic
For each entity, write a projection function that:
1. Handles `null` results.
2. Normalizes types (e.g., strings → `Date`).
3. Structures optional fields explicitly.

Example for a `User` projection:
```typescript
function projectUser(rawUser: RawUser | null): UserResponse {
  if (!rawUser) {
    throw new Error("User not found");
  }

  return {
    id: rawUser.id,
    email: rawUser.email,
    fullName: rawUser.full_name || null, // Let it be null if truly missing
    preferences: rawUser.preferences
      ? {
          theme: rawUser.preferences.theme as "light" | "dark",
          notifications: rawUser.preferences.notifications,
        }
      : null,
  };
}
```

### Step 4: Integrate with Your API Layer
Use the projection function in your resolvers or endpoint handlers. Example for Express:
```typescript
app.get("/users/:id", async (req, res) => {
  const rawUser = await db.query(
    'SELECT * FROM users WHERE id = $1',
    [req.params.id]
  );
  const user = projectUser(rawUser[0]);
  res.json(user);
});
```

### Step 5: Test Edge Cases
Write tests for scenarios like:
- Missing records.
- Null fields.
- Type mismatches (e.g., `price` returned as a string).
- Optional nested objects.

Example test (Jest):
```typescript
test("projection handles null optional fields", () => {
  const rawUser = {
    id: "1",
    email: "test@example.com",
    full_name: null,
    preferences: null,
  };

  const result = projectUser(rawUser);
  expect(result.fullName).toBeNull();
  expect(result.preferences).toBeNull();
});
```

---

## Common Mistakes to Avoid

1. **Assuming Implicit Absence**
   ❌ **Bad**: Relying on `undefined` or `null` to mean "field doesn’t exist."
   ✅ **Good**: Explicitly document which fields are optional and handle them safely.

2. **Silently Overwriting Nulls**
   ❌ **Bad**: Setting `price: 0` for `null` when `0` is a valid price.
   ✅ **Good**: Let `null` stand for "missing" and document this in your API docs.

3. **Ignoring Type Mismatches**
   ❌ **Bad**: Assuming `createdAt` is always a `Date` object.
   ✅ **Good**: Normalize types (e.g., convert strings to `Date` in the projection).

4. **Not Testing Edge Cases**
   ❌ **Bad**: Writing projection logic without testing `null` inputs.
   ✅ **Good**: Include `null` and missing-field tests in your test suite.

5. **Mixing Business Logic with Projections**
   ❌ **Bad**: Calculating discounts in the projection layer.
   ✅ **Good**: Keep projections pure and move business logic to services.

---

## Key Takeaways

- **Projections are not optional**: They’re the bridge between your database and API clients. Treat them defensively.
- **Null is a valid value**: Distinguish between "value is `null`" and "value is missing." Use `null` sparingly and explicitly.
- **Document your API shape**: Clients should know upfront which fields are optional and how to interpret `null`.
- **Normalize types**: Convert inconsistent field types (e.g., strings vs. numbers) into a single format.
- **Fail fast**: If a required field is missing, return a meaningful error (e.g., `400 Bad Request`) rather than a partial response.
- **Test edge cases**: Write tests for `null`, missing fields, and type mismatches to avoid surprises in production.

---

## Conclusion

Null handling in projections is often overlooked, but it’s one of the most important aspects of building robust APIs. By explicitly addressing missing fields, inconsistent types, and null values in your projection logic, you’ll create a layer of resilience that protects your API from messy data—and your clients from confusing responses.

Start small: pick one entity (e.g., `Product` or `User`), write a safe projection for it, and gradually apply the pattern to the rest of your API. Over time, you’ll find that your API becomes more predictable, maintainable, and client-friendly.

Remember: **defensive programming isn’t about being pessimistic—it’s about being practical.** Your clients will thank you for it.

---

### Further Reading
- [GraphQL: How to Handle Null Data](https://www.howtographql.com/advanced/null-values/)
- [PostgreSQL: COALESCE and NVL for Default Values](https://www.postgresql.org/docs/current/functions-conditional.html)
- [TypeScript: Optional Chaining and Nullish Coalescing](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3_7.html#optional-chaining-and-nullish-coalescing)
```

---
This blog post is **practical, code-first, and honest about tradeoffs**, covering everything from the problem to implementation details, common mistakes, and key takeaways. It’s ready to publish and share with intermediate backend developers! Let me know if you'd like any refinements or additional examples.