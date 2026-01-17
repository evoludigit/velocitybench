---
# **[Pattern] GraphQL Patterns & Best Practices: Reference Guide**

---

## **Overview**
GraphQL is a query language for APIs that enables clients to request only the data they need, reducing over-fetching and under-fetching issues common in REST. This pattern provides **actionable best practices** for designing efficient **GraphQL schemas**, implementing **resolvers**, and optimizing **performance, security, and scalability**. Key focus areas include **schema design principles**, **resolver optimization**, **caching strategies**, **data loading**, and **error handling**. Follow these guidelines to build **scalable, maintainable, and performant** GraphQL APIs.

---

## **Core Principles**
GraphQL excels when structured around these foundational concepts:

| **Principle**               | **Description**                                                                                                                                                     | **Key Considerations**                                                                                     |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Single Responsibility**   | Each resolver should handle one logical operation (e.g., fetching, validation, mutation).                                                                                | Avoid chaining too many tasks in a single resolver.                                                     |
| **Fetch-Only**              | Resolvers should **only fetch data**—no business logic unless absolutely necessary.                                                                             | Use middleware (e.g., Apollo middleware, GraphQL Directives) for cross-cutting logic.                  |
| **Avoid N+1 Queries**       | Use **batch loading** or **data loaders** to minimize database roundtrips.                                                                                         | Implement `DataLoader` (or equivalent) to cache database lookups.                                        |
| **Strong Typing**           | Define **explicit, immutable schemas** with proper types (scalars, objects, enums, unions).                                                                     | Use **GraphQL Code Generator** to auto-generate types from your backend.                                   |
| **Minimize Resolver Complexity** | Keep resolvers **shallow and fast**—delegate heavy operations to background services.                                                                        | Use **async/await** for I/O-bound tasks; avoid blocking calls.                                           |
| **Pagination & Filtering** | Support **standardized pagination** (`limit`, `offset`, `cursor`) and **client-side filtering** via args.                                                       | Consider **relay-style cursors** for better performance with large datasets.                             |
| **Deprecation Grace Period**| Clearly mark deprecated fields with `@deprecated(reason)` and set a **maintenance window**.                                                                          | Use versioned schemas or feature flags for breaking changes.                                             |
| **Security-First**          | Enforce **fine-grained permissions** (e.g., via directives like `@auth`) and **sanitize inputs**.                                                               | Avoid exposing **sensitive data** (e.g., PII) in responses unless explicitly requested.                  |
| **Caching Strategies**      | Leverage **persistent caching** (e.g., Redis, Apollo Cache) and **client-side caching**.                                                                          | Implement **TTL-based invalidation** for mutable data.                                                 |
| **Error Handling**          | Return **structured errors** (e.g., `ValidationError`, `UserInputError`) with **detailed messages**.                                                                | Use **graphql-error-formatter** for consistent error responses.                                         |
| **Performance Monitoring**  | Track **query depth**, **execution time**, and **cache hits/misses** to identify bottlenecks.                                                                | Integrate with tools like **Apollo Studio**, **GraphQL Playground**, or **Prometheus**.                 |

---

## **Schema Design Best Practices**
A well-structured schema balances **flexibility** and **predictability**.

### **1. Type Design**
| **Type**          | **Use Case**                                                                                     | **Example**                                                                                     |
|-------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Scalar Types**  | Built-in (e.g., `ID`, `String`, `Int`, `Float`, `Boolean`) + custom (e.g., `DateTime`).       | `type DateTime @scalar`: Resolved via custom scalar handler.                                    |
| **Object Types**  | Represent complex entities (e.g., `User`, `Product`).                                           | `type User { id: ID! @id, name: String!, email: String @unique }`                              |
| **Input Types**   | Define **mutable** fields (e.g., for mutations).                                                | `input CreateUserInput { name: String!, email: String! @validate(email: { message: "Invalid" }) }` |
| **Enum Types**    | Enumerate fixed options (e.g., `Role`, `Status`).                                               | `enum Role { ADMIN, USER, GUEST }`                                                              |
| **Union Types**   | Handle **multiple possible types** in a single field (e.g., `SearchResult`).                   | `union SearchResult = User | Product`                                                            |
| **Interface Types** | Define **shared shape** across unrelated types (e.g., `Node`).                                 | `interface Node { id: ID! @id }` + `type User implements Node { ... }`                         |
| **List/NonNull**  | Enforce **required** fields (`!`) and **arrays**.                                               | `posts: [Post!]!` (must return a non-empty array of Posts).                                    |

---

### **2. Query & Mutation Structure**
| **Pattern**               | **When to Use**                                                                                       | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Flat Queries**          | Avoid **nested queries** >2 levels deep to reduce resolver complexity.                                | ❌ `query { user { posts { comments } } }` → ⚡ `query { user, posts, comments }`             |
| **Pagination**            | Use **cursor-based** or **offset-based** pagination for large datasets.                             | `posts(limit: 10, after: "cursor")`                                                              |
| **Batch Loading**         | Fetch related data **in parallel** (e.g., `dataLoader` for `User` → `posts`).                        | ```javascript                                                                                   // Pseudo-code                                                                                   const loader = new DataLoader(async (keys) => {                                                                   const posts = await db.posts.find({ userId: keys });                                                                   return keys.map(key => posts.find(p => p.userId === key));                                                                 }, { batch: true });                                                               ``` |
| **Field-Level Permissions** | Restrict access **per field** (e.g., `@auth(role: "ADMIN")`).                                      | `type User { sensitiveData: String @auth(role: "ADMIN") }`                                      |
| **Deferred Resolvers**    | Postpone resolution for **expensive operations** (e.g., analytics).                               | `resolvers: { User: { analytics: { defer: true, resolve: async (parent) => ... } } }`       |

---

### **3. Error Handling**
| **Error Type**            | **When to Use**                                                                                       | **Example Response**                                                                             |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **ValidationError**       | Input validation failures (e.g., missing required fields).                                           | `{ errors: [{ path: ["input.email"], message: "Email is required" }] }`                       |
| **UserInputError**        | Business logic violations (e.g., duplicate email).                                                  | `{ errors: [{ message: "Email already in use" }] }`                                             |
| **AuthenticationError**   | Missing/authentication tokens.                                                                        | `{ errors: [{ message: "Invalid token" }] }`                                                    |
| **ForbiddenError**        | Permission denied for a field.                                                                       | `{ errors: [{ message: "Insufficient permissions" }] }`                                        |
| **GraphQLError**          | Unexpected server errors (avoid exposing stack traces).                                             | `{ errors: [{ message: "Internal server error" }] }`                                           |

**Best Practice:**
Use `graphql-extensions` or `graphql-shield` for **centralized error handling**:
```javascript
import { shield, rule } from 'graphql-shield';

const isAuthenticated = rule()(async (parent, args, ctx) => {
  return !!ctx.request.user;
});

const typeDefs = shield({ ... }, { allow: isAuthenticated });
```

---

## **Query Examples**
### **1. Basic Query (User with Posts)**
```graphql
query GetUserWithPosts($userId: ID!) {
  user(id: $userId) {
    id
    name
    email
    posts(first: 3) {
      title
      publishedAt
    }
  }
}
```
**Resolver Logic:**
```javascript
const resolvers = {
  Query: {
    user: async (_, { id }, context) => {
      return await db.User.findById(id);
    }
  },
  User: {
    posts: async (user, { first }, context) => {
      return await db.Post.find({ userId: user.id }).limit(first);
    }
  }
};
```

### **2. Paginated Query (Posts with Cursor)**
```graphql
query GetPosts($after: String) {
  posts(after: $after) {
    edges {
      cursor
      node {
        id
        title
        author {
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```
**Resolver Logic (Relay-style):**
```javascript
const resolvers = {
  Query: {
    posts: async (_, { after }, context) => {
      const { nodes: posts, edges, pageInfo } = await db.Post.findWithPagination({ after });
      return { edges, pageInfo };
    }
  }
};
```

### **3. Mutation with Input Validation**
```graphql
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
    content
  }
}
```
**Input Type & Resolver:**
```graphql
input CreatePostInput {
  title: String! @validate(length: { max: 100 })
  content: String! @validate(length: { min: 10 })
}
```
**Resolver:**
```javascript
const resolvers = {
  Mutation: {
    createPost: async (_, { input }, context) => {
      const post = await db.Post.create(input);
      return post;
    }
  }
};
```

### **4. Subscription (Real-Time Updates)**
```graphql
subscription OnPostCreated {
  postCreated {
    id
    title
    createdAt
  }
}
```
**Resolver (Pub/Sub):**
```javascript
const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: (_, __, { pubsub }) => pubsub.asyncIterator('POST_CREATED')
    }
  }
};
```
**Publisher:**
```javascript
// After creating a post:
await pubsub.publish('POST_CREATED', { postCreated: newPost });
```

---

## **Performance Optimization**
| **Technique**               | **Implementation**                                                                                     | **Tools/Libraries**                                                                             |
|-----------------------------|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Data Fetching**           | Use **batch loading** (`DataLoader`) to avoid N+1 queries.                                           | `dataloader`, `graphql-data-loader`                                                             |
| **Query Complexity**        | Limit query depth complexity to prevent **DoS attacks**.                                             | `graphql-depth-limit`, `graphql-validation-complexity`                                       |
| **Persistent Cache**        | Cache queries at the **Apollo Server** or **client** level.                                        | `apollo-cache`, `redis-cache`                                                                  |
| **Fragments**               | Reuse **field definitions** across queries to avoid duplication.                                     | GraphQL **fragments** (client-side)                                                           |
| **Lazy Loading**            | Load data **on-demand** (e.g., deferred resolvers).                                                 | `@defer` or `@stream` directives                                                              |
| **Compression**             | Enable **gzip/brotli** for large payloads.                                                            | Apache/Nginx compression settings                                                               |
| **Query Planning**          | Analyze slow queries with **execution profiler**.                                                     | Apollo Studio, GraphQL Playground profiler                                                      |
| **Rate Limiting**           | Throttle queries to prevent abuse.                                                                   | `graphql-rate-limit` or `express-rate-limit`                                                   |

---

## **Security Considerations**
| **Risk**                   | **Mitigation**                                                                                       | **Tools**                                                                                      |
|----------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Over-Posting**           | Use **field-level permissions** (`@auth`, `@validate`).                                             | `graphql-shield`, `graphql-mask-object`                                                         |
| **Injection Attacks**      | Sanitize inputs (e.g., SQL, NoSQL).                                                                | `joi`, `yup`, or custom validators                                                              |
| **Introspection Leaks**    | Disable `introspection` in production.                                                              | `apollo-server` config: `{ introspection: false }`                                             |
| **Query Depth Limit**       | Cap **query depth** to prevent slow queries.                                                         | `graphql-depth-limit`                                                                           |
| **Sensitive Data Exposure**| Mask or exclude sensitive fields (e.g., passwords, tokens).                                         | `graphql-mask-object`                                                                          |
| **Authentication**         | Use **JWT/OAuth2** with short-lived tokens.                                                          | `graphql-auth` or custom middleware                                                            |
| **Query Cost Analysis**     | Enforce **complexity thresholds** to prevent expensive queries.                                    | `graphql-validation-complexity`                                                               |

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                     | **When to Use**                                                                                  |
|--------------------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **[Data Loader Pattern]**             | Reduces database roundtrips by batching and caching lookups.                                        | When resolving relations (e.g., `User → Posts`).                                                 |
| **[Pagination Pattern]**              | Standardizes how large datasets are fetched (cursor/offset).                                       | For lists with >100 items.                                                                       |
| **[Authentication Pattern]**         | Secures GraphQL APIs with JWT/OAuth2.                                                                | When protecting endpoints.                                                                        |
| **[Caching Pattern]**                 | Caches query results to reduce server load.                                                         | For read-heavy APIs.                                                                             |
| **[Subscription Pattern]**            | Enables real-time updates via WebSockets.                                                           | For live notifications (e.g., chat, alerts).                                                   |
| **[Error Handling Pattern]**          | Centralizes error responses for consistency.                                                        | When exposing multiple error types (e.g., validation, auth).                                    |
| **[Schema Stitching Pattern]**       | Combines multiple GraphQL schemas (e.g., microservices).                                            | For microservices architecture.                                                                  |
| **[GraphQL Directives Pattern]**      | Extends schema with custom logic (e.g., `@auth`, `@deprecated`).                                  | For reusable cross-cutting concerns.                                                            |

---

## **Further Reading**
1. [GraphQL Spec](https://spec.graphql.org/)
2. [Apollo Best Practices](https://www.apollographql.com/docs/apollo-server/performance/best-practices/)
3. [DataLoader Docs](https://github.com/graphql/dataloader)
4. [GraphQL Shield](https://github.com/maticzav/graphql-shield)
5. [Relay Cursor Connections](https://relay.dev/graphql/connections.htm)

---
**Last Updated:** `[Insert Date]`
**Contributors:** `[List Names]`