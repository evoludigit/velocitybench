**[Pattern] GraphQL Approaches Reference Guide**

---

### **Overview**
The **GraphQL Approaches** pattern encompasses strategies for designing, querying, and optimizing GraphQL APIs to balance flexibility, performance, and maintainability. Unlike REST’s resource-centric focus, GraphQL allows clients to request *only* the data they need via typed queries. This guide covers core approaches—**single-query fetching, batching, subscriptions, and federation**—along with schema design principles, query optimization, and integration considerations.

Key benefits include:
- **Declared data needs** (no over-fetching or under-fetching).
- **Efficient pipelines** via caching and batching.
- **Real-time updates** with subscriptions.
- **Modular scalability** via federation.

This guide assumes familiarity with GraphQL basics (types, queries, mutations) and standard tooling (e.g., Apollo Server, Hasura).

---

### **1. Schema Reference**

#### **Core GraphQL Approaches and Their Schema Requirements**

| **Approach**       | **Purpose**                                                                 | **Schema Requirements**                                                                                     | **Example Type**                          |
|--------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| **Single Query**   | Fetch specific data in one request                                          | Root query type with nested fields; scalar/Object types for data models.                                    | `type Query { user(id: ID!): User! }`     |
| **Pagination**     | Reduce response size; split large datasets                                  | `cursor`/`offset`/`limit` args; `Connection`/relay-style cursors for pagination.                           | `type Query { posts(first: Int): PostConnection! }` |
| **Batch Queries**  | Combine multiple queries into one RPC call (reduces latency)                   | No schema change; relies on server-side batching (e.g., `graphql-batch-request`).                          | *N/A*                                     |
| **Subscriptions**  | Enable real-time data updates                                                 | Root subscription type; `on` clauses for event triggers.                                                  | `type Subscription { postCreated: Post! }` |
| **Federation**     | Compose APIs from multiple services                                          | `@key` directives; shared type definitions (e.g., `@extends`).                                             | `@key(fields: "id") type User @key(`id`)`|
| **DataLoader**     | Batch/parallelize data fetching                                             | No schema change; used alongside resolvers for caching.                                                   | *N/A*                                     |

---

### **2. Query Examples**

#### **2.1 Single Query Approach**
Fetch a user’s profile with nested data (one request):
```graphql
query {
  user(id: "123") {
    id
    name
    posts(first: 3) {
      title
      publishedAt
    }
  }
}
```
**Server-Side Resolution:**
- Resolve `user` resolver fetches from DB.
- `posts` resolver fetches linked data (e.g., via `DataLoader` to avoid N+1 queries).

---

#### **2.2 Pagination Approach**
Fetch paginated posts (cursor-based):
```graphql
query {
  posts(first: 5, after: "YWRtaW46MQ==") {
    edges {
      cursor
      node {
        id
        title
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}
```
**Key Directives:**
- `after`/`before`: Cursor-based pagination (avoids offset issues).
- `first`/`last`: Limit results per page.

---

#### **2.3 Batch Queries Approach**
Combine multiple queries into one call (e.g., using `graphql-batch-request`):
```javascript
// Client-side batch request (libraries like `graphql-batch-request` handle this)
const queries = [
  { query: '{ user(id: "1") { name } }' },
  { query: '{ post(id: "1") { title } }' }
];
const results = await batchRequest(queries);
```
**Server-Side Note:**
- Requires middleware to parse batch payloads (e.g., Apollo’s `batch` plugin).

---

#### **2.4 Subscription Approach**
Subscribe to real-time updates (e.g., new posts):
```graphql
subscription {
  postCreated {
    id
    title
    publishedAt
  }
}
```
**Server-Side Setup:**
- Use a pub/sub system (e.g., Redis, Apollo’s `PubSub`).
- Example resolver:
  ```javascript
  const resolvers = {
    Subscription: {
      postCreated: {
        subscribe: (_, __, { pubsub }) => pubsub.asyncIterator('POST_CREATED'),
      },
    },
  };
  ```

---

#### **2.5 Federation Approach**
Compose data from multiple GraphQL services (e.g., microservices):
```graphql
# Gateway schema (composes User from multiple services)
type Query {
  user(id: ID!): User!
}

# Service 1 (e.g., "Auth Service")
type User @key(fields: "id") {
  id: ID!
  name: String!
}

# Service 2 (e.g., "Post Service")
extend type User @key(fields: "id") {
  posts: [Post!]!
}
```
**Key Directives:**
- `@key`: Defines how to route requests to services.
- `@external`: Marks types resolved externally.

---

### **3. Implementation Details**

#### **3.1 Single Query Optimization**
- **Avoid N+1 Queries:** Use `DataLoader` to batch DB calls:
  ```javascript
  const DataLoader = require('dataloader');
  const userLoader = new DataLoader(async (ids) =>
    await db.query('SELECT * FROM users WHERE id IN ($1)', ids),
  );
  ```
- **Cursor-Based Pagination:** Use `pg-cursor` for PostgreSQL or `relay-cursor` for general use.

#### **3.2 Batching Strategies**
- **Client-Side Batching:** Libraries like `graphql-batch-request` group queries.
- **Server-Side Batching:** Use Apollo’s `batch` plugin or implement custom middleware.

#### **3.3 Real-Time with Subscriptions**
- **Tools:** Apollo Subscriptions, GraphQL Yoga, or custom WebSocket handlers.
- **Scaling:** Use Redis Pub/Sub for horizontal scaling.

#### **3.4 Federation Setup**
- **Gateway:** Apollo Federation or GraphQL Gateway.
- **Service Registration:** Each service must:
  1. Implement `@key` directives.
  2. Register with the gateway (e.g., via `supergraphSDL`).

#### **3.5 Error Handling**
- **Client:** Use `onError` in Apollo Client:
  ```javascript
  client.query({ query: GET_USER }).catch((error) => {
    console.error(error.networkError);
  });
  ```
- **Server:** Return proper GraphQL errors (e.g., `404` for missing data).

---

### **4. Code Snippets**

#### **4.1 Apollo Server Setup (Single Query)**
```javascript
const { ApolloServer } = require('apollo-server');
const { DataLoader } = require('dataloader');

const resolvers = {
  Query: {
    user: async (_, { id }, { dataSources }) => {
      return dataSources.userAPI.getUser(id);
    },
  },
};

const server = new ApolloServer({ typeDefs, resolvers });
```

#### **4.2 Subscription with PubSub**
```javascript
const { PubSub } = require('graphql-subscriptions');
const pubsub = new PubSub();

const resolvers = {
  Subscription: {
    postCreated: {
      subscribe: () => pubsub.asyncIterator('POST_CREATED'),
    },
  },
};
```

#### **4.3 Federation Gateway (Apollo)**
```yaml
# .env
SUPERGRAPH_SDL=https://example.com/supergraph.sdl
```
Run the gateway:
```bash
apollo gateway --config=gateway.config.yaml
```

---

### **5. Related Patterns**
| **Pattern**               | **Connection**                                                                 | **Use Case**                                  |
|---------------------------|---------------------------------------------------------------------------------|-----------------------------------------------|
| **GraphQL Persisted Queries** | Reduces payload size by caching query IDs.                                    | High-performance apps (e.g., mobile).        |
| **GraphQL Shield**         | Fine-grained access control via directives (e.g., `@auth`).                     | Secure APIs with role-based permissions.    |
| **GraphQL Persisted Queries** | Cache query hashes for repeated requests.                                   | Reduce network overhead.                      |
| **GraphQL Over HTTP**      | Transport layer (e.g., REST-like over HTTP).                                  | Legacy integration.                           |
| **GraphQL Query Complexity** | Limits query depth to prevent DoS via `complexity-as-you-go`.                 | Prevent abusive queries.                      |

---

### **6. Best Practices**
1. **Schema Design:**
   - Keep types modular (e.g., `User @interface` for extensibility).
   - Use `@deprecated` for obsolete fields.
2. **Query Optimization:**
   - Enforce complexity limits (e.g., `maxComplexity: 1000`).
   - Implement client-side caching (e.g., Apollo Cache).
3. **Performance:**
   - Use `DataLoader` for batching/fetching.
   - Compress payloads (e.g., `gzip` for large responses).
4. **Real-Time:**
   - Test subscription reliability with load testing.
   - Use connection timeouts for WebSocket endpoints.
5. **Federation:**
   - Version types consistently across services.
   - Monitor gateway latency (e.g., with Apollo Studio).

---
**References:**
- [GraphQL Specification](https://spec.graphql.org/)
- [Apollo Federation Docs](https://www.apollographql.com/docs/federation/)
- [Relay Cursor Connections](https://relay.dev/graphql/connections.htm)