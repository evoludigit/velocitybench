# **Debugging GraphQL: A Troubleshooting Guide**

GraphQL is a powerful query language for APIs, but its complexity—especially in server-side implementation, schema design, and client-side usage—can lead to frustrating issues. This guide provides a **practical, actionable approach** to debugging common GraphQL problems efficiently.

---

## **📋 Symptom Checklist: When to Suspect GraphQL Issues**
Before diving into debugging, check for these **red flags**:

### **Client-Side Symptoms**
- [ ] **Error responses** in the browser console:
  - `Network Error` (failed request)
  - `GraphQL Error: Syntax Error` (malformed query)
  - `400 Bad Request` (validation issues)
  - `500 Internal Server Error` (server-side failure)
- [ ] **Unexpected data shapes** (e.g., missing fields, extra fields)
- [ ] **Performance degradation** (slow queries, timeouts)
- [ ] **CORS issues** (cross-origin requests failing)
- [ ] **Authentication failures** (`401 Unauthorized`)

### **Server-Side Symptoms**
- [ ] **High CPU/memory usage** (due to complex queries)
- [ ] **Schema inconsistencies** (resolvers missing, type conflicts)
- [ ] **Database errors** (N+1 queries, connection timeouts)
- [ ] **Caching issues** (stale data, cache misses)
- [ ] **Race conditions** (in real-time subscriptions)

---
## **⚙️ Common Issues & Fixes (With Code Examples)**

### **1. Schema-Related Errors**
**Symptom:** `GraphQL Error: Cannot query field "missingField" on type "User"` or `Error: Expected scalar type, got Object!`

#### **Debugging Steps:**
✅ **Verify schema definition**
- Check if the field exists in the schema.
- Use `graphql-introspection` or Apollo Studio to inspect the schema.

✅ **Fix mismatched types**
```graphql
# ❌ Wrong: Nested object where a scalar is expected
type Query {
  user: String @deprecated  # Oops! Should be `User`
}
```
**Solution:**
```graphql
type Query {
  user: User!  # Correct type
}
```

✅ **Use `errors` field in GraphQL Playground/Studio**
```graphql
query {
  __schema {
    types {
      name
      fields {
        name
        type {
          name
          kind
        }
      }
    }
  }
}
```

---

### **2. Query Performance Issues (Slow Queries)**
**Symptom:** Long loading times, timeouts, or `Execution Timeout` errors.

#### **Debugging Steps:**
✅ **Check for N+1 Query Problem**
```graphql
# ❌ Bad: Requires 1 + n database calls
query {
  user(id: "1") {
    posts {
      comments {  # N queries
        author {  # Extra queries
          name
        }
      }
    }
  }
}
```
**Solution:** Use **data loader** (batch loading) or **persisted queries** (Apollo).
```javascript
// Example using DataLoader
const DataLoader = require('dataloader');

const batchUsers = async (keys) => {
  const users = await db.query('SELECT * FROM users WHERE id IN ($1)', keys);
  return users.map(user => ({ id: user.id, name: user.name }));
};

const userLoader = new DataLoader(batchUsers);
```

✅ **Enable Query Depth Limit (Apollo)**
```javascript
// server.js
const apolloServer = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [depthLimit(5)],  // Prevent too-deep queries
});
```

✅ **Use Apollo Client’s DevTools**
- Inspect **query depth, variables, and execution time**.
- Enable **persisted queries** to avoid repeated parsing.

---

### **3. Authentication & Authorization Errors**
**Symptom:** `403 Forbidden` or `401 Unauthorized` when accessing protected fields.

#### **Debugging Steps:**
✅ **Check middleware setup**
```javascript
// ❌ Bad: No auth check
const resolvers = {
  Query: {
    secretData: () => db.fetchSecret(),
  },
};
```
**Solution:** Use **directives** (`@auth`) or **context middleware**:
```javascript
// Using Apollo Server’s context
const resolvers = {
  Query: {
    secretData: (_, __, { user }) => {
      if (!user) throw new Error("Unauthorized");
      return db.fetchSecret();
    },
  },
};
```

✅ **Test with Postman/curl**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "{ secretData }"}' \
  http://localhost:4000/graphql
```

---

### **4. Caching & Stale Data Issues**
**Symptom:** Data not updating, or cached responses returning old values.

#### **Debugging Steps:**
✅ **Check Apollo Cache Behavior**
```javascript
// ❌ Bad: No cache control
const apolloServer = new ApolloServer({ ... });
```
**Solution:** Configure cache policies:
```javascript
const apolloServer = new ApolloServer({
  cache: new ApolloServerPluginCache({
    shouldReadFromCache: (ctx) => ctx/cacheControl !== 'no-cache',
    shouldWriteToCache: (ctx) => ctx/cacheControl !== 'no-store',
  }),
});
```

✅ **Use `cache-control` directives in GraphQL**
```graphql
type Post @cacheControl(maxAge: 60) {
  id: ID!
  title: String!
}
```

---

### **5. Subscription/Real-Time Issues**
**Symptom:** Subscriptions not working, or infinite re-renders in the client.

#### **Debugging Steps:**
✅ **Check WebSocket Connection**
- Ensure `apollo-client` is configured with WebSocket support:
```javascript
const client = new ApolloClient({
  uri: 'http://localhost:4000/graphql',
  cache: new InMemoryCache(),
  connectToDevTools: true,
  link: new split({
    // WebSocket for subscriptions
    condition: (operation) => operation.operation === 'subscription',
    // HTTP for queries/mutations
    otherLink: ApolloLink.from([httpLink]),
  }),
});
```

✅ **Test with `graphql-request`**
```bash
# Using Apollo Engine’s playground
curl --location 'ws://localhost:4000/graphql' \
     --header 'Content-Type: application/json' \
     --data '{
       "query": "subscription { newPost { id title } }"
     }'
```

---

## **🛠️ Debugging Tools & Techniques**
| **Tool**               | **Purpose**                                                                 | **How to Use**                                                                 |
|------------------------|-----------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| **GraphQL Playground** | Interactive query testing & error inspection.                              | Run `npm run dev` (Apollo Server) + access `http://localhost:4000/graphql`.    |
| **Apollo Studio**      | Schema validation, performance insights, and error tracking.                | Upload schema to `https://studio.apollo.dev`.                              |
| **Postman/curl**       | Debugging raw HTTP/WebSocket requests.                                     | Send queries with headers (`Authorization`, `Content-Type`).                 |
| **Chrome DevTools**    | Inspect Network tab for failed requests, response bodies.                  | Open DevTools → Network → Filter `graphql`.                                    |
| **Loki/Apollo Logs**   | Track errors in production.                                                 | Configure `ApolloServerPluginUsageReporting`.                               |
| **DataLoader**         | Batch loading to prevent N+1 queries.                                       | Wrap database calls in `DataLoader`.                                         |
| **GraphQL Code Generator** | Auto-generate TypeScript types from schema.                     | Run `graphql-codegen` to sync types.                                          |

---

## **🚀 Prevention Strategies**
### **1. Schema Best Practices**
- **Use `@deprecated`** for old fields to avoid breaking changes.
- **Limit query depth** (Apollo’s `depthLimit`).
- **Document your schema** (GraphQL SDL + comments).

### **2. Query Optimization**
- **Persist queries** (Apollo) to avoid parsing overhead.
- **Use fragments** to reuse query logic.
- **Implement batching** (DataLoader) and **caching** (Apollo Cache).

### **3. Error Handling**
- **Centralize error handling** in resolvers.
- **Log errors** with context (user ID, query details).
- **Return consistent error shapes** (avoid internal server errors leaking stacks).

### **4. Testing**
- **Unit test resolvers** (Jest + `graphql-tools`).
- **E2E test queries** (Cypress + `graphql-request`).
- **Mock dependencies** (e.g., `fakeDB` for integration tests).

### **5. Monitoring**
- **Track slow queries** (Apollo Engine).
- **Set up alerts** for high error rates.
- **Use tracing** (`@apollo/client` with `ApolloLink` plugins).

---

## **🔥 Final Checklist Before Deploy**
✅ **Schema is validated** (no syntax errors, all fields implemented).
✅ **Queries are optimized** (no N+1, depth limits set).
✅ **Authentication works** (test with Postman/curl).
✅ **Caching is configured** (avoid stale data).
✅ **Error boundaries exist** (graceful degradation).
✅ **Logs are in place** (for debugging in production).

---
### **When All Else Fails: Debugging Deep Dives**
- **Enable GraphQL debug logs** (`process.env.DEBUG = 'graphql'`).
- **Use `graphql-inspector`** to analyze resolved fields.
- **Check database logs** for slow queries.

---
By following this guide, you should be able to **quickly identify and resolve** most GraphQL issues. For persistent problems, **check the Apollo Docs** ([apollo.github.io](https://www.apollographql.com/docs/)) and community forums. 🚀