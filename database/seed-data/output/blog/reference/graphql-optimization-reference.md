# **[Pattern] GraphQL Optimization: Reference Guide**

---

## **Overview**
Optimizing GraphQL queries is critical for performance, cost efficiency, and scalability. This pattern outlines best practices to reduce payload size, minimize round trips, and improve query execution. GraphQL’s flexibility can lead to over-fetching or under-fetching if not managed properly. This guide covers:
- **Key concepts** (fragments, batching, data loader, persists queries).
- **Implementation strategies** (schema design, client optimizations, server-side techniques).
- **Trade-offs** and when to apply each technique.
- **Tools and libraries** for automation.

Optimizations apply to both REST-like GraphQL (via GraphQL-over-HTTP) and GraphQL Native applications.

---

## **Key Concepts & Implementation Details**

### **1. Query Optimization Strategies**
Optimize at the **client**, **schema**, and **server** levels.

| **Strategy**          | **Description**                                                                 | **When to Use**                                                                 |
|-----------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Pagination**        | Fetch data in chunks (e.g., `first`, `after` in Relay-style cursors).           | Large datasets, infinite scroll.                                                 |
| **Fragment Reuse**    | Reuse query fragments to avoid duplication (e.g., via `@defer`/`@stream`).    | Shared objects across queries (e.g., user profiles + posts).                     |
| **Batching**          | Group related queries into a single request using `BatchLoader`.               | Reduce N+1 query problems (e.g., fetching post comments).                        |
| **Persisted Queries** | Encode queries as hashes to avoid bandwidth overhead.                          | High-traffic APIs with repeated queries.                                        |
| **Field-Level Caching** | Cache specific fields (e.g., user IDs) to avoid recomputation.              | Frequently accessed static data (e.g., metadata).                              |
| **Data Loading**      | Use `DataLoader` to batch/database fetch related data.                          | Resolve nested relationships efficiently.                                        |
| **Query Complexity**  | Enforce a complexity limit to prevent expensive queries.                       | Security-sensitive APIs (e.g., prevent "query depth bombs").                     |
| **Deep Query Limiting**| Restrict query depth or nested selections.                                    | Prevent accidental expensive queries.                                           |

---

### **2. Schema Design Considerations**
Optimize your schema to avoid performance pitfalls:

| **Schema Element**    | **Optimization**                                                                 | **Example**                                                                     |
|-----------------------|---------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Resolvers**         | Avoid nested resolver calls; use `DataLoader` for batching.                   | Replace `@field` with a batched loader for `posts.comments`.                  |
| **Interfaces/Unions** | Flatten complex types to reduce payload size.                                   | Prefer a simple `Post` type over `Article|Tweet|Story`.                            |
| **Input Types**       | Use scalar inputs (`Int!`, `String`) over object inputs where possible.          | Avoid `CreateUserInput` if a single field (e.g., `email`) suffices.             |
| **Directives**        | Use `@defer`, `@stream` for large payloads.                                     | Split a 50KB response into 2 chunks.                                           |

---

### **3. Client-Side Optimizations**
#### **Query Examples**
##### **Avoid Over-Fetching**
```graphql
# Bad: Over-fetches all fields
query GetPost($id: ID!) {
  post(id: $id) {
    id
    title
    body
    comments {  # Nested fetch (potential N+1)
      text
      author { name }  # Deeper nesting
    }
  }
}
```
**Optimized:**
```graphql
# Good: Fetch only needed fields
query GetPost($id: ID!) {
  post(id: $id) {
    id
    title
  }
  commentsForPost(id: $id, first: 10) {  # Paginated, separate query
    text
    authorName: author { name }
  }
}
```

##### **Use Fragments for Reuse**
```graphql
# Define reusable fragment
fragment UserData on User {
  id
  name
  email
}

# Reuse in multiple queries
query UserProfile($id: ID!) {
  user(id: $id) { ...UserData }
}

query UserPosts($id: ID!) {
  user(id: $id) { ...UserData }
  postsByUser(userId: $id) { title }
}
```

##### **Persisted Queries (Example with Apollo)**
```javascript
// Client-side: Encode query as hash
const query = gql`query GetPost($id: ID!) { post(id: $id) { id } }`;
const persistedQuery = await client.persistedQuery(query, { hash: "abc123" });
```

---

#### **Tools for Client Optimization**
| **Tool/Library**      | **Purpose**                                                                 |
|-----------------------|-----------------------------------------------------------------------------|
| **Apollo Client**     | Persisted queries, caching, optimistic updates.                             |
| **URQL**              | Fine-grained caching with `cacheExchange`.                                  |
| **Relay Modern**      | GraphQL SDK with built-in optimizations (e.g., `useLazyLoadQuery`).         |
| **GraphQL URL**       | Encode queries in URLs for persistence.                                    |
| **GraphiQL/Playground** | Inspect query performance (e.g., "Playground" → "Query Profiler").       |

---

### **4. Server-Side Optimizations**
#### **A. DataLoader for Batching**
```javascript
// Example: Batch-comment resolution
const dataLoader = new DataLoader(async (commentIds) => {
  const comments = await db.comment.find({ where: { id: commentIds } });
  return commentIds.map(id => comments.find(c => c.id === id));
});

const resolvers = {
  Post: {
    comments: async (parent, args, context) => {
      return dataLoader.load(parent.id); // Batches all comment queries
    }
  }
};
```

#### **B. Query Complexity Analysis**
Add a plugin to enforce limits:
```javascript
const complexityPlugin = {
  visitOperation(operation) {
    const complexity = calculateComplexity(operation);
    if (complexity > MAX_COMPLEXITY) {
      throw new Error(`Query complexity too high: ${complexity}`);
    }
  }
};

// Usage in server config:
server.applyMiddleware({ graphqlServer: { plugins: [complexityPlugin] } });
```

#### **C. Persisted Queries**
Configure Apache/Nginx to reject non-persisted queries:
```nginx
location /graphql {
  rewrite ^/graphql$ /graphql?query_hash=$arg_query_hash permanent;
  # Only allow queries with a valid hash
  set $valid_hash "";
  if ($arg_query_hash ~ ^[a-z0-9]{16}$) {
    set $valid_hash "on";
  }
  if ($valid_hash = "") {
    return 400;
  }
}
```

---

## **Schema Reference Table**
| **Component**         | **Optimized Attribute**               | **Example Value**                     | **Impact**                                  |
|-----------------------|---------------------------------------|---------------------------------------|--------------------------------------------|
| **Query**             | Depth limit                            | `maxDepth: 10`                        | Prevents deep nesting attacks.             |
| **Type**              | Field resolution strategy             | `resolve: async (parent, args, ctx) => ...` | Use `DataLoader` for batching.            |
| **Directive**         | `@defer`/`@stream`                    | `@defer { if (isMobile) }`            | Split large responses.                     |
| **Input Type**        | Scalar vs. object inputs               | `email: String!` vs. `UserInput { ... }` | Reduces payload size.                      |

---

## **Query Examples: Common Patterns**
### **1. Pagination (Cursor-Based)**
```graphql
query GetPosts($after: String, $first: Int) {
  posts(after: $after, first: $first) {
    edges {
      node { id title }
      cursor
    }
    pageInfo { hasNextPage }
  }
}
```
**Variables:**
```json
{ "first": 10, "after": "Y3Vyc29yOnYyOpOzA=" }
```

### **2. Fragment Spread**
```graphql
query UserWithPosts($id: ID!) {
  user(id: $id) { ...UserFields }
  postsByUser(userId: $id) { ...PostFields }
}

fragment UserFields on User {
  id
  name
  posts(first: 5) { title }
}

fragment PostFields on Post {
  id
  body
}
```

### **3. Streaming with `@stream`**
```graphql
query StreamComments($postId: ID!) @stream {
  post(id: $postId) {
    comments {
      text
      author { name }
    }
  }
}
```
**Server-side:** Process chunks incrementally (e.g., WebSocket).

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Link to Reference**                          |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **GraphQL Federation**    | Decentralized schema composition for microservices.                          | [GraphQL Federation Guide]                    |
| **Subscriptions**         | Real-time updates via GraphQL (e.g., WebSocket).                             | [GraphQL Subscriptions Pattern]               |
| **Query Depth Limiting**  | Prevent accidental expensive queries.                                         | [Security: Query Depth Control]               |
| **Client-Side Caching**   | Optimize client interactions (e.g., Apollo Normalized Cache).               | [Apollo Caching Documentation]                |
| **Schema Stitching**      | Combine multiple GraphQL schemas into one.                                   | [Schema Stitching Guide]                     |

---

## **Trade-offs & Considerations**
| **Optimization**         | **Pros**                                      | **Cons**                                      | **Use Case**                          |
|--------------------------|-----------------------------------------------|-----------------------------------------------|---------------------------------------|
| **Persisted Queries**    | Reduces bandwidth, caches queries.           | Adds server-side complexity.                  | High-traffic APIs.                    |
| **DataLoader**           | Reduces N+1 queries.                           | Overhead for simple resolvers.               | API-heavy apps.                       |
| **Query Complexity**     | Prevents abuse.                               | May block legitimate queries.               | Public APIs.                          |
| **Pagination**           | Efficient data loading.                       | Requires client-side state management.        | Infinite scroll.                      |

---

## **Tools & Libraries**
| **Category**             | **Tools**                                                                 |
|--------------------------|---------------------------------------------------------------------------|
| **Client**               | Apollo Client, URQL, Relay, GraphQL URL, Relay Compiler.                   |
| **Server**               | Apollo Server (with `DataLoader`), GraphQL Yoga, Hasura, GraphQL Engine.  |
| **Analysis**             | GraphQL Inspector, Apollo Studio, Sentry GraphQL.                          |
| **Testing**              | Jest + `graphql-tag`, MSW (Mock Service Worker).                          |