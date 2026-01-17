```markdown
---
title: "GraphQL Request Validation: Stop Invalid Queries Before They Break Your App"
description: "Learn how to validate GraphQL requests effectively, avoid runtime errors, and improve API reliability with real-world examples."
date: "2024-05-15"
author: "Alex Carter"
tags: ["GraphQL", "API Design", "Backend Engineering", "Validation"]
---

# GraphQL Request Validation: Stop Invalid Queries Before They Break Your App

## Introduction

GraphQL is a powerful API architecture that lets clients request exactly what they need—no more, no less. But if you’ve ever debugged a `GraphQLValidationError` at 3 AM or seen mysterious failures in production, you know GraphQL’s flexibility can become a double-edged sword. Invalid queries—malformed, unsupported, or otherwise non-compliant—can slip through and hit your database or business logic, wasting resources and confusing users.

Validation is the backbone of robust API design, and GraphQL’s validation layer (implemented in the `graphql-js` core) is both a blessing and an oversight for many. Most frameworks (like Apollo Server or Express GraphQL) abstract it away, but they’re not magic—misconfigured or disabled validation can leave your API vulnerable. In this tutorial, we’ll explore how GraphQL *should* validate requests, why it’s critical to handle edge cases, and how to implement validation effectively—including when the built-in system falls short.

By the end, you’ll know how to:
- Understand GraphQL’s native validation rules.
- Debug why validations are failing (or not failing enough).
- Extend validation for custom business rules.
- Avoid common pitfalls that turn GraphQL into a "try everything and see what works" playground.

Let’s dive in.
---

## The Problem: Invalid Queries Reach Execution Without Feedback

GraphQL’s power comes from its dynamic nature: clients can request fields, arguments, or fragment spreads at runtime. But this flexibility introduces risks. Consider these real-world scenarios:

### Scenario 1: Unintended Field Spreads
A third-party app sends this query to your API:
```graphql
query {
  post(id: "123") {
    title
    ... on Post {
      publishedAt
    }
    ... on Article {
      author  # Not a real type, but GraphQL won’t reject it silently
    }
  }
}
```
Most GraphQL servers will **execute this** even though:
- `author` doesn’t exist on `Post`.
- The `... on Article` fragment won’t match `Post` (and `Article` isn’t defined).

The result? A runtime error—**but the client wasted bandwidth sending invalid fields**.

---

### Scenario 2: Malformed Arguments
A client sends:
```graphql
query {
  createUser(email: "invalid@email") {
    id
  }
}
```
Assuming your schema defines `email` as a non-null `String!`, the server *should* reject this. But if validation is disabled or misconfigured, it might:
- Pass silently, then fail during execution (e.g., when sending an email).
- In some cases (like schema-first setups), it *might* reject—but only at execution time.

---

### Scenario 3: Missing Required Arguments
A query omits a required argument:
```graphql
query {
  fetchUserByEmail(email: "user@example.com") {  # Missing `id` argument
    name
  }
}
```
Without proper validation, your resolver might fail mid-execution, returning a cryptic error instead of the expected `400 Bad Request`.

---

### Why Does This Happen?
1. **Validation is enabled by default but not enforced by GraphQL itself**: The runtime *can* validate, but many frameworks disable it for "simplicity" or performance.
2. **Execution-first mentality**: Some developers prioritize "fix it in the resolver" over preventing bad requests.
3. **Custom types/mutations**: Extending schema validation requires explicit configuration.

The result? **Unpredictable API behavior** that frustrates clients and wastes server resources.

---

## The Solution: Robust GraphQL Validation

GraphQL’s validation layer (defined in the [spec](https://graphql.github.io/spec/June2018/#sec-Validation)) is designed to catch:
1. **Syntax errors** (malformed queries).
2. **Schema compliance** (does the query match the schema?).
3. **Argument/field requirements** (are all `!` fields provided?).
4. **Type safety** (e.g., passing a `String` where an `Int` is expected).

But validation isn’t one-size-fits-all. You’ll need to configure it carefully and extend it for business rules.

---

## Key Components of GraphQL Validation

| Component               | Description                                                                 | Example                                                                 |
|-------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------|
| **Schema Validation**   | Ensures queries/fragments match the schema’s types/fields.                  | Rejects `... on Article` if `Article` doesn’t exist.                     |
| **Argument Validation** | Validates required arguments, type constraints, and `defaultValue`.       | Rejects `{ id: "text" }` if `id` is an `Int!`.                           |
| **Query Depth/Complexity** | Limits query depth or complexity to prevent abuse.                     | Rejects a query with 50 nested fields if the limit is 10.                 |
| **Custom Directives**    | Adds validation logic (e.g., `@auth`).                                        | Rejects queries missing `@auth` on a protected field.                  |
| **Execution-Safe Validation** | Checks for runtime safety (e.g., no circular references).               | Prevents infinite loops in fragments.                                  |

---

## Implementation Guide: Validating Like a Pro

### Step 1: Enable Validation in Your Framework

#### Apollo Server Example
Apollo Server enables validation by default, but you can customize it:
```javascript
import { ApolloServer } from 'apollo-server';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    // Custom rules can be added here
    require('./validationRules').customRules,
  ],
});

await server.start().listen({ port: 4000 });
```

#### Express-GraphQL Example
Express-GraphQL relies on `graphql-js` validation. Ensure it’s not disabled:
```javascript
const express = require('express');
const { graphqlHTTP } = require('express-graphql');
const { buildSchema } = require('graphql');

const app = express();
app.use(
  '/graphql',
  graphqlHTTP({
    schema: buildSchema(typeDefs),
    graphiql: true, // Disable in production
    validationRules: [require('./customValidationRules')], // Optional
  })
);
```

---

### Step 2: Understand the Built-In Rules

GraphQL’s default validator checks for:
1. **Syntax**: No malformed queries.
2. **Schema**: Fields/fragments exist.
3. **Types**: Inputs match expected types.
4. **Requirements**: Non-null fields are provided.

Example: A query like `{ user(id: "text") { name } }` fails because:
- `id` is an `Int!` but receives a `String`.

---

### Step 3: Extend Validation for Custom Rules

#### Example: Validate User Inputs
Suppose you want to ensure `email` is valid before execution:
```javascript
const { GraphQLNonNull, GraphQLString } = require('graphql');
const { GraphQLScalarType } = require('graphql');

// Custom scalar for validation
const EmailScalar = new GraphQLScalarType({
  name: 'Email',
  description: 'Validates email format',
  parseValue: (value) => {
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      throw new Error('Invalid email format');
    }
    return value;
  },
  serialize: (value) => value,
});

// Schema example
const typeDefs = `
  input UserInput {
    email: Email!
    password: String!
  }
  type Mutation {
    createUser(input: UserInput!): User
  }
`;
```

#### Example: Add a Custom Validation Rule
Use the `validationRules` option in Apollo Server:
```javascript
import { GraphQLArgument, GraphQLField } from 'graphql';

const validateArgs = (schema) => ({
  Field: {
    enter(fieldConfig, args, context, info) {
      if (info.parentType.name === 'Mutation' && info.fieldName === 'createUser') {
        const inputArgs = args[info.returnType.toString()];
        if (!inputArgs?.email || !isValidEmail(inputArgs.email)) {
          throw new ValidationError('Invalid email address');
        }
      }
    },
  },
});

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [validateArgs],
});
```

---

### Step 4: Handle Edge Cases

#### Case 1: Fragments with Missing Types
A query includes a fragment that doesn’t match any type:
```graphql
query {
  user(id: 1) {
    ...UnknownFragment
  }
}
```
**Fix**: Apollo Server rejects this by default, but ensure `validationRules` aren’t suppressing it.

#### Case 2: Deeply Nested Queries
Large queries can cause performance issues. Use `maxComplexity`:
```javascript
const server = new ApolloServer({
  schema,
  validationRules: [
    require('graphql-validation-complexity')({
      maximumComplexity: 1000,
    }),
  ],
});
```

#### Case 3: Circular References
Prevent infinite loops in fragments:
```graphql
type Query {
  me: User
}

type User {
  posts: [Post!]!
}

type Post {
  author: User!
}
```
**Fix**: GraphQL’s validation catches this automatically, but if you nest cycles manually, add:
```javascript
const { validate } = require('graphql');
const { visit } = require('graphql/language/visitor');

const hasCircularReferences = (queryAst) => {
  // Custom logic to detect cycles
};
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Disabling Validation for "Performance"
Some developers disable validation to reduce overhead, but this:
- Increases execution errors.
- Wastes more resources fixing runtime issues.

**Fix**: Use `validationRules` to limit complexity or depth instead.

### ❌ Mistake 2: Assuming Schema Validation is Enough
Schema validation ensures *syntax* compliance, but not *business logic*. For example:
- A `username` field might exist in the schema but require unique checks.
- A `deleteUser` mutation might need admin privileges.

**Fix**: Use directives (e.g., `@auth`) or custom validation rules.

### ❌ Mistake 3: Ignoring Argument Defaults
If an argument has a default value (e.g., `published: boolean = false`), GraphQL *will* accept omitting it—but it might not behave as expected.

**Fix**: Document defaults clearly or enforce them:
```graphql
type Query {
  posts(limit: Int = 10): [Post!]!
}
```
Ensure your resolver handles the default if needed.

### ❌ Mistake 4: Not Testing Edge Cases
Always test:
- Empty inputs.
- `null` values where `!` is expected.
- Very deep/nested queries.

**Fix**: Use tools like [`graphql-playground`](https://github.com/graphql/graphql-playground) or Postman to send invalid requests.

---

## Key Takeaways

✅ **GraphQL validation is enabled by default but can be misconfigured**—always verify it’s active.
✅ **Schema validation catches syntax/type mismatches**, but **custom rules catch business logic**.
✅ **Use directives (`@auth`, `@validate`) for reusable validation**.
✅ **Limit query depth/complexity to prevent abuse**.
✅ **Test invalid requests rigorously**—clients will send them.
✅ **Combine validation with error handling** for graceful fallbacks.

---

## Conclusion

GraphQL’s dynamic nature is its strength, but without proper validation, it becomes a source of unpredictable failures. By enabling and extending validation—using built-in rules, custom directives, and complexity limits—you can:
- Reduce runtime errors.
- Improve API reliability.
- Keep your database and business logic safe from malformed requests.

Start with the defaults, then add layers of validation as needed. And remember: **the client’s job is to send valid requests; your job is to make it easy for them to do so (and hard for them to send invalid ones)**.

Now go forth and validate like a backend engineer—your API (and sanity) will thank you.

---

### Further Reading
- [GraphQL Specification: Validation Rules](https://graphql.github.io/spec/June2018/#sec-Validation)
- [Apollo Server Validation Rules](https://www.apollographql.com/docs/apollo-server/guides/validation/)
- [`graphql-validation-complexity`](https://github.com/anthony-lazee/graphql-validation-complexity)
- [Testing GraphQL APIs with Jest](https://www.apollographql.com/docs/devtools/testing/testing-with-jest/)

---
```sql
-- No SQL needed here, but if you wanted to visualize validation in a database context:
-- Imagine a schema like this for a User:
-- ```
-- CREATE TABLE users (
--   id SERIAL PRIMARY KEY,
--   email VARCHAR(255) UNIQUE NOT NULL,
--   password_hash VARCHAR(255) NOT NULL
-- );
-- ```
-- A GraphQL query like `{ user(id: "invalid") { email } }` would fail validation if `id` is `Int!`.
-- ```
```