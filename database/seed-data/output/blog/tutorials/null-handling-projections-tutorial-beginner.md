```markdown
---
title: "Null Handling in Projections: Building Robust GraphQL Resolvers"
date: 2023-10-15
author: "Alex Carter"
description: "Learn how to handle nulls, missing fields, and type conversions gracefully in GraphQL projections. Real-world examples and best practices."
---

# Null Handling in Projections: Building Robust GraphQL Resolvers

Since I started writing backend APIs, one of the most painful gotchas I've encountered is **null handling in projections**. GraphQL resolvers often return data that looks clean and consistent on paper, but when real-world data has gaps, missing fields, or unexpected nulls, responses can break or become inconsistent. This isn’t just about GraphQL—it’s a pattern that applies to JSON APIs, DTOs (Data Transfer Objects), and any projection layer.

In this post, we’ll explore **Null Handling in Projections**, a pattern designed to make your API responses predictable, user-friendly, and resilient. We’ll cover why nulls are problematic, walk through practical solutions, and examine common pitfalls to avoid. By the end, you’ll have a toolkit for crafting robust projections that handle edge cases gracefully.

---

## The Problem: Inconsistent or Invalid Responses

### The Unfortunate Reality of Nulls
Let’s say you’re building an e-commerce API that includes a `User` type with fields like `name`, `email`, `phone`, and `address`. In the database, `phone` might be nullable, and `email` might be required. When a user signs up without a phone number, the database stores `NULL` for that field. But what happens when you project that user to a JSON response?

Consider these scenarios:

1. **Nulls are passed through**: The response includes `"phone": null`, which might be needed for validation logic but can make your API less intuitive for front-end developers.
2. **Nulls are omitted**: The response omits `"phone": null`, resulting in inconsistent object shapes for users with and without phones.
3. **Nulls are coerced**: The API converts `NULL` to empty strings or default values (e.g., `"phone": ""`), which might break downstream logic that expects `"phone": null` to indicate "no phone entered."

### The Pain of Inconsistent Resolvers
If your team has different engineers writing resolvers, you’ll often end up with inconsistent null-handling logic. One resolver might handle a `NULL` value by returning `null`, while another might return an empty string, and a third might omit the field entirely. This inconsistency can lead to:

- Front-end bugs: A component might expect `"phone"` to always exist in the response, but sometimes it’s missing or set to `null`.
- Schema validation issues: GraphQL clients might complain about missing required fields if they’re not always present.
- Debugging nightmares: Troubleshooting why a specific API response is malformed becomes harder when the shape can vary unpredictably.

### Example: A Null-Ridden Response
Here’s what a poorly handled projection might look like:

```json
{
  "user": {
    "id": "123",
    "name": "Alice",
    "email": "alice@example.com",
    "phone": null,
    "address": null
  }
}
```

This response is valid JSON, but it’s not user-friendly. Front-end developers might have to write logic like this:

```javascript
if (user.phone === null) {
  // Handle missing phone
} else if (user.phone) {
  // Handle non-empty phone
} else {
  // Handle empty string? (Huh?)
}
```

The problem isn’t just about the code—it’s about **clarity**. A missing field or a `null` value should convey meaning clearly.

---

## The Solution: Null Handling in Projections

The goal of **Null Handling in Projections** is to standardize how your API handles `NULL`, `MISSING`, and `EMPTY` values. This pattern ensures that:

1. **Responses are consistent**: Every object in a response has the same shape, regardless of whether certain fields are present.
2. **Nulls are meaningful**: Fields with `null` or missing values have a clear, documented convention.
3. **Front-end development is easier**: Clients don’t have to handle edge cases for every possible field.

### Key Components of the Solution

1. **Projection Strategy**: Decide whether to include `null` values, omit fields, or use defaults.
2. **Null-to-Type Conversion**: Convert `NULL` or missing values to a more intuitive type (e.g., `""` for strings, `0` for numbers).
3. **Field-Specific Logic**: Handle different field types (e.g., strings, booleans, nested objects) differently.
4. **Documentation**: Clearly document your null-handling rules in your API documentation.

---

## Implementation Guide: Code Examples

Let’s walk through examples in **TypeScript** (common for GraphQL resolvers) and **SQL** (for database queries). We’ll use a hypothetical `User` entity with the following database schema:

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  phone VARCHAR(20),
  address TEXT,
  is_active BOOLEAN DEFAULT TRUE
);
```

### Step 1: Define Your Projection Strategy
Before writing code, decide how you want to handle `NULL` values for each field. Common strategies:

| Field       | Strategy                          | Example Output               |
|-------------|-----------------------------------|------------------------------|
| `phone`     | Omit if `NULL`                    | `"phone": absent`            |
| `address`   | Convert `NULL` to `""`            | `"address": ""`              |
| `is_active` | Convert `NULL` to `false`         | `"is_active": false`         |

For this example, we’ll:
- Omit fields if they’re `NULL` (e.g., `phone`).
- Convert `NULL` strings to `""` (e.g., `address`).
- Convert `NULL` booleans to `false` (e.g., `is_active`).

---

### Step 2: Write a Null-Safe Resolver in TypeScript

Here’s a robust resolver for a `User` type using the `graphql-js` library. We’ll handle `NULL` values gracefully:

```typescript
import { GraphQLScalarType } from 'graphql';

interface User {
  id: string;
  name: string;
  email: string;
  phone?: string | null;
  address?: string | null;
  isActive?: boolean | null;
}

const userType = new GraphQLObjectType({
  name: 'User',
  fields: {
    id: { type: GraphQLString, resolve: (user: User) => user.id },
    name: { type: GraphQLString, resolve: (user: User) => user.name },
    email: { type: GraphQLString, resolve: (user: Email) => user.email },
    phone: {
      type: GraphQLString,
      resolve: (user: User) => {
        // Omit if phone is null
        if (user.phone === null) return null;
        return user.phone;
      },
    },
    address: {
      type: GraphQLString,
      resolve: (user: User) => {
        // Convert null to empty string
        return user.address ?? '';
      },
    },
    isActive: {
      type: new GraphQLScalarType({
        name: 'BooleanNullScalar',
        serialize: (value: boolean | null) => {
          // Convert null to false for consistency
          return value ?? false;
        },
        parseValue: (value: any) => value,
        parseLiteral: (ast) => ast.value,
      }),
      resolve: (user: User) => user.isActive,
    },
  },
});

// Example resolver for a user by ID
export const getUserResolver = async (root: any, args: { id: string }) => {
  // In a real app, this would query the database
  const user = await db.queryUserById(args.id);

  // Project the user with null handling
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    phone: user.phone, // `null` will be omitted by the resolver
    address: user.address ?? '', // `null` becomes ""
    isActive: user.isActive ?? false, // `null` becomes `false`
  };
};
```

### Step 3: Optimize Database Queries with `COALESCE` and `ISNULL`
To reduce nulls at the database level, use SQL functions like `COALESCE` (PostgreSQL) or `ISNULL` (MySQL/SQL Server). For example:

```sql
-- Return an empty string for NULL addresses
SELECT
  id,
  name,
  email,
  phone,
  COALESCE(address, '') AS address,
  COALESCE(is_active, false) AS is_active
FROM users
WHERE id = 123;
```

This reduces the number of `NULL` values your application needs to handle.

---

### Step 4: Handle Missing Fields in GraphQL Schema
GraphQL’s `FieldPolicy` can enforce consistent field inclusion. For example, you might want `phone` to be optional but not `null`:

```typescript
const userType = new GraphQLObjectType({
  name: 'User',
  fields: () => ({
    id: { type: GraphQLString, resolve: (user: User) => user.id },
    name: { type: GraphQLString, resolve: (user: User) => user.name },
    // Note: `phone` is optional in the schema, but resolvers handle nulls
    phone: {
      type: GraphQLString,
      args: {
        default: { type: GraphQLString },
      },
      resolve: (user: User, args) => user.phone ?? args.default,
    },
    // Other fields...
  }),
});
```

---

## Common Mistakes to Avoid

### 1. Assuming All Fields Are Non-Null
Many developers forget that database columns, even required ones, can have `NULL` values in edge cases. Always validate and handle `NULL` values explicitly.

**Bad:**
```typescript
// What if `phone` is NULL?
const user = { phone: userDbRecord.phone };
```

**Good:**
```typescript
const user = {
  phone: userDbRecord.phone ?? null,
};
```

### 2. Inconsistent Null Handling Across Resolvers
Different engineers might handle `NULL` values differently. Standardize your approach by documenting rules (e.g., "All string fields convert `NULL` to `''`") and using helper functions.

**Example Helper Function:**
```typescript
function handleStringNull(value: string | null): string {
  return value ?? '';
}
```

### 3. Forgetting to Document Null Behavior
If your API documentation doesn’t explain how `NULL` values are handled, clients will have to reverse-engineer the behavior. Document your rules clearly, e.g.:

> "Fields with `NULL` values are omitted from responses. String fields default to `''`, booleans default to `false`."

### 4. Overusing `ISNULL` or `COALESCE` Blindly
While `COALESCE` can reduce `NULL` values, it’s not always the right choice. For example, converting `NULL` to `0` for a `quantity` field might hide business logic (e.g., "0" could mean "sold out," while `NULL` could mean "not yet determined").

### 5. Not Testing Edge Cases
Test your resolvers with:
- Records where all fields are `NULL`.
- Records with mixed `NULL` and non-`NULL` values.
- Empty strings (`""`) vs. `NULL` (they’re different in SQL!).

**Test Case Example:**
```typescript
test('NULL address becomes empty string', () => {
  const user = { address: null };
  expect(handleUser(user)).toEqual({ address: '' });
});
```

---

## Key Takeaways

Here are the critical lessons from this pattern:

- **Nulls are everywhere**: Database fields, API responses, and client-side code all need to handle them predictably.
- **Consistency is key**: Standardize how your API handles `NULL` values to avoid confusing clients.
- **Document your choices**: Clearly explain your null-handling rules in your API documentation.
- **Use database tools**: Leverage `COALESCE`, `ISNULL`, or default values in SQL to reduce `NULL` values early.
- **Write defensive code**: Always assume fields might be `NULL` and handle them explicitly.
- **Test edge cases**: Test with `NULL`, missing fields, and empty values to catch bugs early.

---

## Conclusion

Null handling in projections is often overlooked, but it’s one of the most important aspects of building a robust API. By adopting a standardized approach—whether that’s omitting `NULL` values, converting them to defaults, or documenting their meaning—you’ll make your API more predictable, easier to debug, and less painful for front-end developers to work with.

### Next Steps
1. **Audit your current resolvers**: Review existing projections and identify inconsistent null-handling patterns.
2. **Pick a strategy**: Decide whether to omit, convert, or document `NULL` values for each field.
3. **Refactor incrementally**: Update one resolver at a time to avoid breaking changes in production.
4. **Document**: Add a section to your API docs explaining null-handling rules.
5. **Test**: Write tests for edge cases to ensure your projections behave as expected.

Remember: There’s no one-size-fits-all solution. The goal is to **make your API’s behavior explicit and consistent**. By treating null handling as a first-class part of your projection logic, you’ll build APIs that are resilient, user-friendly, and easier to maintain.

Happy coding!
```

---
**P.S.** If you’re working with a team, consider creating a shared library of projection utilities to enforce consistency across all resolvers. For example:
```typescript
// utils/projection.ts
export const handleNulls = (user: User) => ({
  ...user,
  phone: user.phone ?? null,
  address: user.address ?? '',
  isActive: user.isActive ?? false,
});
```
Then use it in all your resolvers:
```typescript
const user = handleNulls(dbUser);
return user;
```