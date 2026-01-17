```markdown
---
title: "GraphQL Conventions: Writing Clean, Consistent, and Maintainable APIs"
date: "2023-11-15"
categories: ["Backend Engineering", "API Design", "GraphQL"]
tags: ["API Design Patterns", "GraphQL Best Practices", "Backend Development", "JavaScript/TypeScript"]
description: "Learn how to adopt GraphQL conventions to build scalable, maintainable APIs with consistent naming, querying patterns, and error handling. Practical examples included."
---

# GraphQL Conventions: Writing Clean, Consistent, and Maintainable APIs

GraphQL has emerged as a powerful alternative to REST, offering fine-grained data fetching and flexible query shapes. However, without well-defined conventions, even a beautifully designed GraphQL API can become a chaotic mess over time. This post explores the **GraphQL Conventions pattern**, a set of best practices and standards that help maintain consistency, readability, and scalability in your GraphQL APIs.

As a senior backend engineer, you’ve likely wrangled with APIs where:
- Field names changed across versions (`getUser` → `fetchUser` → `retrieveUserProfile`).
- Mutations lacked explicit success/failure responses.
- Queries required nested objects for simple operations, increasing latency.
- Errors were wrapped in random strings like `{ "error": "Something went wrong" }`.

These inconsistencies create friction for developers, testers, and even end users. **GraphQL conventions** help you design APIs that feel intuitive, predictable, and easy to maintain—without sacrificing flexibility.

---

## The Problem: Why GraphQL APIs Need Conventions

GraphQL’s strength is its expressiveness, but this flexibility can become a liability without guardrails. Here are the key pain points:

### 1. **Lack of Naming Consistency**
Imagine querying the same data across two GraphQL endpoints:
```graphql
# Endpoint A
query {
  getActiveUsers {
    id
    name
    email
  }
}

# Endpoint B
query {
  users(filter: ACTIVE) {
    userId
    displayName
    contactEmail
  }
}
```
Why?
- `getActiveUsers` vs. `users`
- `id` vs. `userId`
- `name` vs. `displayName`
- `email` vs. `contactEmail`

This inconsistency forces clients to adapt, increasing cognitive load and error rates.

### 2. **Overly Complex Query Shapes**
GraphQL’s strength is fetching only what you need, but clients often over-fetch:
```graphql
query {
  getOrder(orderId: "123") {
    id
    user { id name email }
    items { id product { name price } }
    shipping { address city }
  }
}
```
This query fetches deep relationships even if the client only needs the order ID and a single item’s price. Without conventions, clients might not know what’s necessary vs. optional.

### 3. **Poor Error Handling**
GraphQL errors are powerful but often not standardized:
```graphql
# Ambiguous error
mutation {
  createUser(input: { email: "invalid" })
}
# Response: { errors: ["Something went wrong"] }

# Better, but inconsistent
mutation {
  createUser(input: { email: "invalid" })
}
# Response: { data: null, errors: { email: "Must be a valid email" } }
```
Without conventions, clients can’t reliably parse errors.

### 4. **Versioning Nightmares**
Field names and types change over time, breaking clients:
```graphql
# v1
query {
  getUser(id: "1") {
    name
    age
  }
}

# v2
query {
  fetchProfile(id: "1") {
    fullName
    birthYear
  }
}
```
Clients must be updated for every breaking change.

### 5. **No Clear Mutation Success Patterns**
Mutations often lack a consistent way to return success/failure:
```graphql
# Mutation A
mutation {
  createUser(user: { name: "Alice" })
  # Returns: { user: { id: "1" } } on success, { errors: [...] } on failure
}

# Mutation B
mutation {
  updateOrder(orderId: "1", status: "SHIPPED")
  # Returns: { success: true } on success, { message: "Failed" } on failure
}
```

---

## The Solution: Adopting GraphQL Conventions

GraphQL conventions are **not** restrictions—they’re guardrails that make your API more predictable and easier to work with. The goal is to:
1. **Standardize field names and types** for consistency.
2. **Define clear querying patterns** to optimize performance.
3. **Unify error responses** for easier debugging.
4. **Version changes incrementally** without breaking clients.
5. **Document expectations** so developers can write correct clients.

---

## Components of GraphQL Conventions

### 1. Naming Conventions
Avoid arbitrary field names by following a schema:
| Field Type       | Convention                          | Example                     |
|------------------|-------------------------------------|-----------------------------|
| **Queries**      | `get{EntityName}`                   | `getUser`, `getOrders`      |
| **Mutations**    | `create{EntityName}`, `update{EntityName}`, `delete{EntityName}` | `createUser`, `updateOrder` |
| **Input Fields** | `{entityName}{Action}`              | `userName`, `orderStatus`   |
| **Output Fields**| `{entityName}{Property}`            | `userId`, `orderTotal`      |
| **Relationships**| `{entityName}{Relationship}`        | `userPosts`, `productReviews`|

**Why?**
- Reduces cognitive load for developers.
- Makes introspection (e.g., `__schema`) more predictable.
- Helps tools like GraphQL Code Generator auto-generate clients.

---

### 2. Querying Patterns
#### **Flattened Queries for Performance**
Encourage clients to request only what they need:
```graphql
# ❌ Over-fetching
query {
  getUser(id: "1") {
    id
    name
    email
    posts { id title }
  }
}

# ✅ Under-fetching (but requires multiple queries)
query {
  getUser(id: "1") {
    id
    name
    email
  }
}

query {
  getUserPosts(userId: "1") {
    id
    title
  }
}
```

#### **Paginated Lists**
Use `offset`/`limit` or `cursor-based pagination` for large datasets:
```graphql
query {
  getUsers(first: 10, after: "cursor123") {
    edges {
      node { id name }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```

---

### 3. Error Handling
Standardize error responses for consistency:
```graphql
# Mutation response structure
mutation {
  createUser(input: { email: "invalid" })
}
# Response (on error):
{
  "errors": [
    {
      "field": "input.email",
      "message": "Must be a valid email",
      "extensions": {
        "code": "VALIDATION_ERROR",
        "details": { "maxLength": 255 }
      }
    }
  ]
}
```

**Key Fields in Errors:**
- `field`: The input field causing the error (if applicable).
- `message`: A human-readable explanation.
- `extensions`: Machine-readable details (e.g., `code`, `timestamp`).

---

### 4. Mutation Success Patterns
Return a consistent structure for mutations:
```graphql
# ✅ Consistent success response
mutation {
  createUser(input: { name: "Alice", email: "alice@example.com" })
}
# Response (on success):
{
  "data": {
    "createUser": {
      "user": {
        "id": "1",
        "name": "Alice",
        "email": "alice@example.com"
      }
    }
  }
}

# ✅ Consistent failure response
mutation {
  createUser(input: { email: "invalid" })
}
# Response (on error):
{
  "errors": [
    { "field": "input.email", "message": "Invalid email" }
  ]
}
```

---

### 5. Versioning Strategies
#### **Schema Stitching**
For breaking changes, introduce a new query/mutation without deprecating the old one:
```graphql
# v1 (deprecated)
query {
  getUser(id: "1")
}

# v2 (new)
query {
  fetchProfile(id: "1")
}
```

#### **Feature Flags**
Enable new fields/mutations via feature flags:
```graphql
# Enable via config
"resolvers": {
  "Query": {
    "fetchProfile": async (_, args, { dataSources }) => {
      if (!process.env.ENABLE_NEW_PROFILE_API) {
        throw new Error("Feature not available");
      }
      return dataSources.userAPI.fetchProfile(args.id);
    }
  }
}
```

#### **Deprecation Warnings**
Mark deprecated fields with `@deprecated`:
```graphql
type Query {
  getUser(id: ID!): User @deprecated(reason: "Use fetchProfile instead")
  fetchProfile(id: ID!): Profile
}
```

---

## Implementation Guide

### Step 1: Define a Naming Schema
Start by documenting your naming conventions. Here’s an example for a blog API:

| Entity       | Query          | Mutation               | Input Fields               | Output Fields          |
|--------------|----------------|------------------------|----------------------------|------------------------|
| Post         | `getPosts`     | `createPost`, `updatePost`, `deletePost` | `postTitle`, `postContent` | `postId`, `postSlug`    |
| Comment      | `getComments`  | `createComment`, `updateComment`, `deleteComment` | `commentText`, `postId`    | `commentId`, `authorId` |

```graphql
# Example schema snippet
type Query {
  getPosts(limit: Int, offset: Int): [Post!]!
}

type Mutation {
  createPost(input: PostInput!): PostPayload!
}

input PostInput {
  title: String!
  content: String!
}

type PostPayload {
  post: Post!
  errors: [FieldError!]
}

type FieldError {
  field: String!
  message: String!
}
```

---

### Step 2: Standardize Error Responses
Implement a global error handler. For example, in Apollo Server:

```javascript
// server.js
const { ApolloServer } = require('apollo-server');
const { printSchema } = require('graphql');

const typeDefs = require('./schema');
const resolvers = require('./resolvers');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }) => ({ user: req.user }),

  // Custom error formatting
  formatError: (err) => {
    if (!err.originalError) return err;

    const message = err.originalError.message;
    const extensions = {
      code: err.originalError.code,
      details: err.originalError.details,
    };

    return {
      message,
      extensions,
    };
  },
});

server.listen().then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});
```

Example resolver with structured errors:
```javascript
// resolvers.js
const createUser = async (_, { input }, { dataSources }) => {
  const { name, email } = input;

  if (!email.includes('@')) {
    throw new Error('Invalid email format');
  }

  try {
    const user = await dataSources.userAPI.createUser({ name, email });
    return { user };
  } catch (err) {
    throw new Error(`Failed to create user: ${err.message}`);
  }
};
```

---

### Step 3: Enforce Query Patterns
Use Apollo’s `validationRules` to enforce query patterns. For example, disallow over-fetching:

```javascript
// server.js
const { ApolloServer } = require('apollo-server');
const { GraphQLError } = require('graphql');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    (schema) => (document) => {
      const operations = document.definitions.filter(
        (def) => def.kind === 'OperationDefinition'
      );

      operations.forEach((op) => {
        if (op.selectionSet.selections.some(
          (s) => s.kind === 'Field' && s.name.value === 'user' && s.selectionSet
        )) {
          throw new GraphQLError(
            'Over-fetching detected: user data should be split into separate queries.'
          );
        }
      });
    },
  ],
});
```

---

### Step 4: Implement Versioning
Add a version query to check API compatibility:
```graphql
query {
  apiVersion
}
# Response: { "apiVersion": "v2" }
```

Modify resolvers to return the version:
```javascript
// resolvers.js
const resolvers = {
  Query: {
    apiVersion: () => process.env.API_VERSION || 'v1',
  },
};
```

---

### Step 5: Document Your Conventions
Add a `README.md` to your GraphQL docs with:
- Field naming rules.
- Error response formats.
- Query patterns (e.g., "Always paginate lists").
- Versioning strategy.

Example:
```markdown
# GraphQL API Conventions

## Naming
- Queries: `get{EntityName}`
- Mutations: `create{EntityName}`, `update{EntityName}`
- Fields: `{entityName}{property}`

## Errors
All errors follow this structure:
```json
{
  "errors": [
    {
      "field": "input.email",
      "message": "Required field",
      "extensions": { "code": "VALIDATION_ERROR" }
    }
  ]
}
```

## Pagination
Use `first` and `after` for cursor-based pagination:
```graphql
query {
  getPosts(first: 10, after: "cursor123") {
    edges { node { id title } }
    pageInfo { hasNextPage }
  }
}
```

---

## Common Mistakes to Avoid

### 1. **Overusing `@deprecated`**
- **Mistake**: Marking every minor change as deprecated.
  ```graphql
  type Query {
    getUser(id: ID!): User @deprecated(reason: "Use fetchUser")
    fetchUser(id: ID!): User
  }
  ```
- **Fix**: Only deprecate when the old API is truly obsolete. Deprecate incrementally:
  - First, add the new API.
  - Deprecate the old API after a few months.
  - Remove the old API after another few months.

### 2. **Ignoring Fossil Records**
- **Mistake**: Removing deprecated fields too quickly, breaking existing clients.
- **Fix**: Keep deprecated fields for at least 6–12 months to allow clients to migrate. Example:
  ```graphql
  type Query {
    getUser(legacyId: ID): User @deprecated(reason: "Use fetchUser(id)")
    fetchUser(id: ID!): User
  }
  ```
  After a year, remove `getUser`.

### 3. **Complex Query Shapes Without Documentation**
- **Mistake**: Assuming clients know what to fetch.
  ```graphql
  query {
    getOrder(orderId: "123") {
      id
      user { id name email }
      items { id product { name price } }
      shipping { address city }
    }
  }
  ```
- **Fix**: Document required vs. optional fields. Example:
  ```markdown
  ## getOrder
  - **Required**: `orderId`
  - **Optional**:
    - `user`: Fetch user details if you need authentication context.
    - `items`: Fetch items if you need to process payments.
    - `shipping`: Fetch shipping if you need to update address.
  ```

### 4. **Not Handling Large Objects**
- **Mistake**: Returning huge objects in a single query.
  ```graphql
  query {
    getPost(postId: "1") {
      id
      title
      content  # 500KB of HTML
      author { name avatar }  # 10KB
    }
  }
  ```
- **Fix**: Implement streaming or chunking for large fields:
  ```graphql
  type Post {
    id: ID!
    title: String!
    content: String!
    author: Author!
    metadata: PostMetadata!  # Small fields
  }

  type PostMetadata {
    wordCount: Int!
    readingTime: String!
  }
  ```
  Or use Apollo’s `stream` directive:
  ```graphql
  query {
    getPost(postId: "1") {
      id
      content @stream
    }
  }
  ```

### 5. **Assuming Clients Understand Your Schema**
- **Mistake**: Not documenting type hierarchies.
  ```graphql
  type User {
    id: ID!
    name: String!
    roles: [Role!]!
  }

  enum Role {
    ADMIN
    EDITOR
    READER
  }
  ```
- **Fix**: Clearly document relationships and enums:
  ```markdown
  ## User
  - `roles`: Array of `Role` enum values. Possible values:
    - `ADMIN`: Full access.
    - `EDITOR`: Can edit content.
    - `READER`: Read-only access.
  ```

---

## Key Takeaways

- **Consistency is king**: Standardize field names, query patterns, and error responses.
- **Document everything**: Clients (including future you) will thank you.
- **Version incrementally**: Use deprecation warnings and feature flags to migrate safely.
- **Optimize for readability**: Avoid overly nested queries; encourage under-fetching.
- **Handle errors gracefully**: Provide machine-readable details in extensions.
- **Avoid over-engineering**: Conventions should simplify, not complicate.

---

## Conclusion: Build APIs That Feel Like Home

GraphQL’s power lies in its flexibility, but without conventions, that flexibility can become a liability. By adopting standardized naming, querying patterns, and error handling, you create an API that:
- Feels intuitive to developers and clients.
- Is easier to maintain and extend.
- Reduces breaking changes over time.

Start small—pick one convention (e.g., field naming) and iterate. Over time, your GraphQL API will evolve into a well-oiled machine, not a chaotic playground.

**Further Reading:**
- [Apollo’s Guide to GraphQL Best Practices](https://www.apollographql.com/docs/apollo-server/performance/)
- [GraphQL Error Handling Patterns](https://www.howtographql.com/advanced/errors/)
- [Prisma’s Schema Design Guide](https://www.pr