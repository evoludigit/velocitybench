**[Pattern] GraphQL Techniques Reference Guide**

---

### **Overview**
GraphQL Techniques is a collection of patterns and best practices for designing, implementing, and optimizing GraphQL APIs. Unlike traditional REST APIs, GraphQL enables clients to request exactly the data they need, reducing over-fetching and under-fetching. This pattern guide covers core concepts (querying, mutations, subscriptions), schema design, performance optimizations (caching, batching, pagination), and advanced techniques (federation, directives, and error handling).

---

### **Key Concepts**
GraphQL APIs consist of three primary components:

| **Component**       | **Description**                                                                                     |
|----------------------|-----------------------------------------------------------------------------------------------------|
| **Schema**           | Defines the available types, queries, mutations, and subscriptions. Written in GraphQL Schema Definition Language (SDL). |
| **Resolver**         | Function that fetches data for a given field. Can be synchronous or asynchronous.                     |
| **Execution Engine** | Processes queries, validates requests, and resolves data. Handles execution pipelines, caching, and error handling. |

---

### **Schema Reference**
The **schema** is the backbone of a GraphQL API. Below are common GraphQL SDL constructs:

| **Directive**               | **Description**                                                                                     | Example                                                                 |
|-----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| `query`                     | Defines the root query type (read-only operations).                                                 | `type Query { user(id: ID!): User }`                                      |
| `mutation`                  | Defines the root mutation type (write operations).                                                   | `type Mutation { createUser(input: UserInput!): User }`                  |
| `subscription`              | Defines real-time updates (server-sent events).                                                     | `type Subscription { userUpdated: User }`                               |
| `input Type`                | Customizable input objects for mutations.                                                            | `input UserInput { name: String!, email: String! }`                     |
| `interface`/`union`         | Allows overlapping types or mixed field sets.                                                      | `interface Node { id: ID! }`                                             |
| `@deprecated`               | Marks a field as deprecated (to avoid breaking changes).                                           | `@deprecated(reason: "Use new field")`                                   |
| `@auth`/`@rolePermission`   | Custom directives for authorization (e.g., GraphQL Shield).                                          | `@auth(requires: ["admin"])`                                             |
| `@field`/`@args`            | Modifies field/mutation argument behavior (e.g., default values).                                   | `@field(resolve: "customResolver")`                                     |
| **Scalars**                 | Built-in (`String`, `Int`, `Float`, `Boolean`, `ID`) or custom (`Date`, `JSON`).                    | `scalar Date`                                                           |

---

### **Query Examples**
#### **1. Basic Query**
Fetch a single `User` by ID:
```graphql
query GetUser {
  user(id: "1") {
    id
    name
    email
  }
}
```

#### **2. Mutation**
Create a new `User`:
```graphql
mutation CreateUser {
  createUser(input: { name: "Alice", email: "alice@example.com" }) {
    id
    name
  }
}
```

#### **3. Subscriptions**
Receive real-time updates for a `User`:
```graphql
subscription OnUserUpdated {
  userUpdated {
    id
    name
  }
}
```

#### **4. Fragments**
Reuse fields across queries:
```graphql
fragment UserInfo on User {
  name
  email
}

query GetUsers {
  users {
    ...UserInfo
    posts { title }
  }
}
```

#### **5. Directives**
Conditional field inclusion (e.g., client-side filtering):
```graphql
query GetConditional {
  user(id: "1") @include(if: true) {
    name
  }
}
```

---

### **Advanced Techniques**
| **Technique**               | **Purpose**                                                                                     | Implementation Notes                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **DataLoader Batching**     | Reduces N+1 query problems by batching identical requests.                                        | Use libraries like `dataloader` (JavaScript) or `graphql-java-dataloader`.          |
| **Persisted Queries**      | Improves performance by caching serialized queries during execution.                             | Enable in Apollo Server: `persistedQueries: { cache: ... }`.                        |
| **GraphQL Federation**      | Combines multiple GraphQL APIs into a unified schema.                                            | Requires `@extends`/`@key` directives (Apollo Federation).                           |
| **Custom Scalars**          | Extend GraphQL with custom types (e.g., `Date`).                                                | Implement `GraphQLScalarType` resolvers or use libraries like `graphql-scalars`.      |
| **Error Handling**          | Gracefully manage errors (e.g., authentication failures, invalid inputs).                         | Use `Error` types or custom errors: `extend type Query { throwError(input: Boolean!): Boolean! }`. |

---

### **Performance Optimization**
| **Optimization**            | **Implementation**                                                                              | When to Use                                                                          |
|-----------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Cursor-Based Pagination** | Use `limit`/`offset` with cursor tokens (better for large datasets).                           | Large datasets (e.g.,Pagination over 1000 items).                                    |
| **Query Depth Limiting**    | Prevent deeply nested queries (potential performance risk).                                     | High-cardinality data (e.g., `user { posts { comments { replies } } }`).             |
| **Field-Level Permissions** | Restrict access via directives (e.g., `@auth`).                                                  | Secure APIs with role-based access control.                                          |
| **Caching**                 | Cache resolvers or query results (e.g., Redis, Apollo Cache).                                   | Read-heavy APIs with repetitive queries.                                             |

---

### **Tooling & Libraries**
| **Tool**                     | **Purpose**                                                                                     |
|------------------------------|-------------------------------------------------------------------------------------------------|
| **Apollo Server**            | Production-ready GraphQL server with caching, subscriptions, and federation.                     |
| **GraphQL Playground**       | Interactive IDE for testing queries/mutations.                                                  |
| **Hot Chocolate (C#)**       | ASP.NET Core GraphQL implementation.                                                            |
| **GraphQL Code Generator**   | Auto-generates types/queries from GraphQL schemas.                                              |
| **GraphQL Inspector**        | Analyzes schema for best practices/errors.                                                      |

---

### **Common Pitfalls & Solutions**
| **Issue**                     | **Solution**                                                                                     |
|-------------------------------|-------------------------------------------------------------------------------------------------|
| **Over-Fetching**             | Encourage clients to request only needed fields.                                                  |
| **N+1 Query Problem**         | Use `DataLoader` or `@connection` directives (Relay-style).                                     |
| **Schema Bloat**              | Modularize schemas (e.g., split into `users.graphql`, `posts.graphql`).                          |
| **Slow Resolvers**            | Use pagination, caching, or lazy-load data.                                                      |
| **Direct Access to DB**       | Abstract data access behind a service layer (e.g., `UserService`).                               |

---

### **Related Patterns**
1. **[REST ↔ GraphQL Gateway]**
   - Translates REST requests to GraphQL (or vice versa) for backward compatibility.
   - Example: Use [Apollo Gateway](https://www.apollographql.com/docs/apollo-server/data/federation/) for federation.

2. **[Microservices with GraphQL]**
   - Each service exposes its own GraphQL schema, aggregated via federation or a unified gateway.

3. **[GraphQL + gRPC]**
   - Combines GraphQL’s flexible querying with gRPC’s high-performance RPC for internal services.

4. **[Query Complexity Analysis]**
   - Limits the complexity of queries to prevent abuse (e.g., `Complexity: 1000`).

5. **[GraphQL + Event Sourcing]**
   - Store state changes as events and rebuild data on-demand (e.g., using `graphql-yoga`).

---
### **Further Reading**
- [GraphQL Spec (GitHub)](https://github.com/graphql/graphql-spec)
- [Apollo Docs](https://www.apollographql.com/docs/)
- [GraphQL Federation Guide](https://www.apollographql.com/docs/apollo-server/data/federation/)
- ["GraphQL in Depth" (Book)](https://www.graphql-in-depth.com/)

---
**Last Updated:** [Date]
**Contributors:** [Team/Organization]