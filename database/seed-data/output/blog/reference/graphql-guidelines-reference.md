# **[Pattern] GraphQL Guidelines Reference Guide**

---

## **Overview**
GraphQL Guidelines establish best practices for designing, implementing, and maintaining efficient, maintainable, and scalable GraphQL APIs. Unlike REST, GraphQL fosters a schema-first approach, where the API contract is explicitly defined in a schema (SDDL/GraphQL SDL). This document provides structured guidelines to ensure consistency, performance, and developer experience while adhering to GraphQL principles.

Key objectives include:
- **Schema design** (avoiding over/under-fetching, reducing complexity).
- **Type consistency** (avoiding ambiguous or overly complex types).
- **Performance optimization** (query depth, batching, and caching).
- **Security & validation** (input sanitization, field permissions).
- **Documentation** (self-descriptive schema, clear type definitions).

Adhering to these guidelines reduces common pitfalls such as N+1 queries, bloated responses, and vendor lock-in, while improving long-term maintainability.

---

## **Schema Design Guidelines**

| **Category**       | **Guideline**                                                                 | **Example**                                                                                     | **Rationale**                                                                                     |
|--------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Schema Structure** | Use modular schema definitions (split into separate `.graphql` files or packages). | ```graphql
type Query { users(id: ID): User @module(import: "users.graphql") } ``` | Modularity improves reusability and reduces schema complexity.                                    |
| **Type Definitions** | Prefer simple, reusable types over deep nesting.                             | ```graphql
type User { id: ID! name: String! email: String! posts: [Post!]! } ``` | Shallow nesting reduces N+1 queries and improves readability.                                  |
| **Input Types**     | Use `Input` types (e.g., `CreateUserInput`) for mutations.                   | ```graphql
input CreateUserInput { name: String! email: String! } mutation { createUser(input: CreateUserInput): User } ``` | Encapsulates mutation arguments, improving type safety.                                        |
| **Non-Null Types**  | Use `!` sparingly; prefer `String` over `String!` unless required.           | ```graphql
type User { id: ID! name: String # `email` is optional } ``` | Balances strictness with flexibility.                                                           |
| **Scalars**         | Avoid custom scalars for simple types (e.g., `DateTime`). Use built-ins.       | ```graphql
scalar DateTime # Replace with `String` (ISO format) where possible. ``` | Reduces implementation overhead; leverages GraphQL’s built-in support.                           |
| **Aliases**         | Limit aliases to avoid query ambiguity.                                       | ```graphql
query { userAlias: user(id: 1) userByEmail: user(email: "test@example.com") } ``` | Clarifies intent but avoids excessive nesting.                                                  |
| **Enums**           | Keep enums small (≤10 values); prefer `String` for large sets.                | ```graphql
enum Status { ACTIVE, PENDING, INACTIVE } ``` | Enums with many values create bloated payloads.                                                 |
| **Interfaces/Unions** | Use interfaces for shared fields; unions for discriminated types.          | ```graphql
interface Commentable { id: ID! comments: [Comment!]! } union SearchResult = User | Post ``` | Interfaces enforce consistency; unions enable polymorphic responses.                         |
| **Directives**      | Standardize custom directives (e.g., `@auth`, `@cache`).                    | ```graphql
directive @auth(roles: [Role!] = USER) on FIELD_DEFINITION ``` | Enforces permissions and metadata across the schema.                                            |
| **Pagination**      | Use cursor-based (not offset-based) pagination.                             | ```graphql
type Query { posts(first: Int, after: String): PostsConnection } ``` | Prevents performance issues with large datasets.                                                 |
| **Relationships**   | Avoid deep nesting; use list types for collections.                         | ```graphql
type User { posts: [Post!]! } # Instead of: { posts: Post { title: String } } ``` | Reduces query planning overhead.                                                                |

---

## **Query & Mutation Patterns**

### **Best Practices**
1. **Avoid Over-Fetching**: Fetch only required fields (client decides payload shape).
2. **Minimize Depth**: Shallow queries reduce complexity and improve execution speed.
3. **Use Fragments**: Reuse field sets across queries.
4. **Batch Relationships**: Use `@client` directives or DataLoader for batching.
5. **Error Handling**: Return structured errors (e.g., `errors: [Error!]!`).

### **Query Examples**

#### **1. Shallow Query (Recommended)**
```graphql
query GetUser {
  user(id: "123") {
    id
    name
    email
  }
}
```

#### **2. Deep Query (Avoid; Use DataLoader Instead)**
```graphql
query Bad_Practice {
  user(id: "123") {
    id
    name
    posts {
      title
      author { name } # N+1 query risk
    }
  }
}
```
**Fix:** Use a dedicated `posts` query or DataLoader:
```graphql
query GetUserWithPosts {
  user(id: "123") { id name email }
  posts(authorId: "123") { title }
}
```

#### **3. Paginated Query**
```graphql
query GetPosts {
  posts(first: 10, after: "cursor") {
    edges {
      node { id title }
      cursor
    }
    pageInfo { hasNextPage }
  }
}
```

#### **4. Mutation with Input Type**
```graphql
mutation CreatePost {
  createPost(input: {
    title: "Hello GraphQL"
    content: "World"
    authorId: "123"
  }) {
    id
    title
  }
}
```

#### **5. Using Fragments**
```graphql
query GetUserWithFragment {
  user(id: "123") {
    ...userCommonFields
    posts(first: 3) {
      edges { node { id title } }
    }
  }
}

fragment userCommonFields on User {
  id
  name
  email
}
```

---

## **Performance Optimization**

### **1. Query Depth Limitation**
- **Guideline**: Limit query depth to 5–7 levels (default: 5).
- **Implementation**:
  ```graphql
  directive @maxDepth(level: Int!) on QUERY | MUTATION
  ```
  Apply to root queries:
  ```graphql
  query @maxDepth(level: 5) { ... }
  ```

### **2. Persisted Queries**
- **Guideline**: Use hashed query IDs for repeated queries.
- **Example**:
  ```http
  POST /graphql
  { "id": "abc123", "variables": { "id": "123" } }
  ```

### **3. DataLoader (Batching & Caching)**
- **Use Case**: Batch database queries (e.g., loading a user’s posts).
- **Example** (Node.js):
  ```javascript
  const DataLoader = require('dataloader');
  const userLoader = new DataLoader(async (ids) => {
    const users = await db.query('SELECT * FROM users WHERE id IN ($1)', ids);
    return ids.map(id => users.find(u => u.id === id));
  });

  resolver: { user } async(userId) { return await userLoader.load(userId); }
  ```

### **4. Field-Level Caching**
- **Guideline**: Cache immutable fields (e.g., `User#id`).
- **Implementation** (Apollo Server):
  ```javascript
  const { ApolloServer } = require('apollo-server');
  const server = new ApolloServer({
    typeDefs,
    resolvers,
    cache: "bounded",
  });
  ```

---

## **Security Guidelines**

| **Risk**               | **Mitigation**                                                                 | **Example**                                                                                     |
|------------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Unauthorized Access** | Use `@auth` directive for sensitive fields.                                  | ```graphql
type User { id: ID! email: String @auth(roles: [ADMIN]) } ```                                     |
| **Injection Attacks**   | Validate all inputs (e.g., scalars, enums).                                  | ```graphql
scalar JSON # Sanitize input with GraphQL JSON library. ```                                         |
| **Over-Posting**        | Restrict mutation input fields.                                               | ```graphql
mutation UpdateUser { updateUser(id: ID!, input: { name: String }) { ... } } ```                     |
| **Rate Limiting**       | Enforce rate limits per operation.                                            | ```javascript
const { rateLimit } = require('graphql-rate-limit');
const { schema } = rateLimit({
  schema,
  maxRequests: 100,
  timeWindow: '1 minute',
});
```                                                                                                  |

---

## **Documentation & Maintenance**

### **1. Schema Comments**
- **Guideline**: Use `#` for descriptions and `@deprecated` for obsolete fields.
- **Example**:
  ```graphql
  "Returns a user by ID."
  type User { id: ID! }
  ```

### **2. Versioning**
- **Guideline**: Use schema extensions for backward compatibility.
- **Example**:
  ```graphql
  extend type Query {
    "Deprecated in v2.0; use `getUser` instead."
    legacyUser(id: ID!): User @deprecated(reason: "Use getUser.")
  }
  ```

### **3. Tooling**
| **Tool**               | **Purpose**                                                                 | **Link**                                                                                       |
|------------------------|----------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **GraphQL Playground** | Interactive schema exploration.                                           | https://github.com/graphql/graphql-playground                                                 |
| **GraphiQL**           | Built-in IDE for GraphQL.                                                  | Included in Apollo Studio                                                                      |
| **GraphQL Codegen**    | Generate types from schema (TypeScript/JavaScript).                        | https://graphql-code-generator.com                                                         |
| **Linters**            | Enforce schema guidelines (e.g., `graphql-config`, `eslint-plugin-graphql`). | [ESLint GraphQL Plugin](https://github.com/apollographql/eslint-plugin-graphql)               |

---

## **Related Patterns**

1. **Schema Stitching**
   - Combine multiple GraphQL schemas into a single endpoint.
   - **Use Case**: Microservices federation.
   - **Tools**: Apollo Federation, Relay Modern.

2. **Subscriptions**
   - Real-time updates via WebSockets.
   - **Example**:
     ```graphql
     subscription {
       userUpdated(id: "123") {
         name
         email
       }
     }
     ```

3. **Batch Loading**
   - Optimize N+1 queries using DataLoader.
   - **See**: [DataLoader Pattern](https://github.com/graphql/dataloader).

4. **GraphQL + REST Hybrid**
   - Use GraphQL for complex queries and REST for simple CRUD.
   - **Example**: `/graphql` for queries, `/api/v1/users` for POST/PUT.

5. **Persisted Queries**
   - Cache query hashes to reduce payload size.
   - **See**: [Persisted Queries Guide](https://www.apollographql.com/docs/apollo-server/data/persisted-queries/).

6. **GraphQL over gRPC**
   - Use Protocol Buffers for high-performance GraphQL.
   - **Example**: [gRPC-Gateway](https://github.com/grpc-ecosystem/grpc-gateway).

---

## **Troubleshooting**

| **Issue**               | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------|------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **N+1 Queries**         | Deeply nested queries trigger repeated DB calls.                            | Use DataLoader or shallow queries.                                                              |
| **Schema Too Large**    | Schema exceeds 1MB or 10,000+ fields.                                         | Split into subschemas or use federation.                                                        |
| **Slow Queries**        | Query depth > 5 or complex joins.                                            | Optimize resolvers; use persisted queries.                                                      |
| **Authentication Errors** | Missing `@auth` directive or invalid tokens.                                | Validate tokens server-side; log errors.                                                        |
| **Circular Dependencies** | Schema types reference each other recursively.                              | Refactor into interfaces/unions or break into modules.                                          |

---

## **Further Reading**
1. [GraphQL Spec](https://spec.graphql.org/)
2. [Apollo Server Docs](https://www.apollographql.com/docs/apollo-server/)
3. [Relay Modern](https://relay.dev/docs/guides/graphql-server-specification/)
4. [GraphQL Best Practices (Udacity)](https://www.udacity.com/course/graphql-fundamentals--ud606)