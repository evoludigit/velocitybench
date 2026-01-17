# **Debugging GraphQL Approaches: A Troubleshooting Guide**
*(Focusing on "GraphQL Federation," "Relay," and "Subscriptions" Approaches)*

---

## **1. Introduction**
GraphQL’s flexibility allows multiple approaches (Federation, Relay, Subscriptions, etc.), but misconfigurations, performance bottlenecks, or incorrect usage can cause failures. This guide covers troubleshooting common issues across these approaches.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom**                          | **Possible Cause**                          | **Key Area to Check**                     |
|--------------------------------------|--------------------------------------------|------------------------------------------|
| Slow queries (> 1s latency)          | N+1 queries, inefficient resolvers          | Federation: `extends`, Relay: `connection` |
| Missing data in responses            | Incorrect `__schema` or fragment mismatches | Federation: `typeDefs`, Relay: `mutation` |
| Subscription timeouts or disconnections | websocket misconfig, rate limits          | Subscriptions: `onConnect`, `onDisconnect` |
| Type errors (e.g., "Cannot query X") | Missing `__ProxyTypeDefs`, wrong scalar types | Federation: `pluralization`, Relay: `cursor` |
| High memory usage                     | Large batching, inefficient dataLoader     | Federation: `entityKey`, Relay: `dataLoader` |

---

## **3. Common Issues & Fixes**

---

### **3.1 GraphQL Federation Issues**

#### **Issue: Missing or malformed `__schema`**
**Symptom:** `Cannot query type 'X'` or `Unknown type 'X'` errors.
**Root Cause:** Federation requires `__schema` definition in `typeDefs`.
**Fix:**
```graphql
# Example of correct `@key` and `__schema` generation
type User @key(fields: "id") {
  id: ID!
  name: String!
}

# Ensure __schema is available (Apollo Federation)
type _Service {
  sdl: String!
}
```
**Debugging Steps:**
1. Validate `__schema` manually:
   ```bash
   curl -X POST http://your-gateway/graphql -H "Content-Type: application/json" -d '{"query": "{ __schema { types { name } } }"}'
   ```
2. Check if `typeDefs` is merged correctly in the gateway.

---

#### **Issue: N+1 Queries**
**Symptom:** Slow responses due to missing `@extends` or `@requires`.
**Fix:**
```graphql
# Correct usage: Share resolvers via `@extends`
type User @key(fields: "id") @extends {
  id: ID!
  # Fetch from subgraph if missing
  posts: [Post] @requires(fields: "id")
}

# Subgraph defines `posts`
type Post @key(fields: "id") {
  id: ID!
  userId: ID!
}
```
**Debugging Tools:**
- Use Apollo Studio’s [Query Analyzer](https://www.apollographql.com/studio/) to detect N+1 issues.
- Enable debugging in Federation subgraphs:
  ```env
  APOLLO_FEDERATION_DEBUG=true
  ```

---

### **3.2 Relay Modern Issues**

#### **Issue: Failed Relay Connections (`connection`)**
**Symtom:** `Cannot query 'edges'` or `cursor malformed`.
**Root Cause:** Missing `cursor` alignment in edges/nodes.
**Fix:**
```javascript
// Correct cursor handling (e.g., in Node.js resolver)
const users = await db.users.findAll();
const edges = users.map(user => ({
  cursor: bytesToBase64(encodeCursor(user.id)), // Relay-compatible cursor
  node: user,
}));
```
**Debugging Steps:**
1. Verify cursor format:
   ```graphql
   query {
     users(first: 5) {
       edges {
         cursor
         node {
           id
         }
       }
     }
   }
   ```
2. Use Relay’s `Cursor` utilities:
   ```bash
   npm install relay-cursor
   ```

---

#### **Issue: Mutation Failures**
**Symtom:** `Cannot mutate 'createUser'` (e.g., missing `__typename`).
**Fix:**
```graphql
mutation {
  createUser(input: { name: "Alice" }) {
    user {
      id
      __typename
    }
  }
}
```
**Debugging Steps:**
1. Add `__typename` to all returned types.
2. Check for typos in mutation input types.

---

### **3.3 Subscriptions Issues**

#### **Issue: WebSocket Connection Drops**
**Symtom:** `Connection terminated` or empty subscriptions.
**Root Cause:** Invalid WebSocket URL or missing auth.
**Fix:**
```javascript
// Server-side: Validate WebSocket connections
server.use(
  async ({ event, connectionParams }) => {
    if (!connectionParams.authToken) throw new Error("Missing token");
    return {};
  }
);

// Client-side: Ensure correct URL
const subscription = new GraphQLClient(
  { uri: "ws://localhost:4000/graphql" },
  { connect: () => {} }
);
```
**Debugging Tools:**
- Use `ws` client to test manually:
  ```bash
  wscat -c ws://localhost:4000/graphql
  ```
- Check server logs for WebSocket errors.

---

---

## **4. Debugging Tools & Techniques**

### **4.1 Apollo Studio**
- **Query Tracing:** Identify slow queries.
- **Schema Registry:** Validate Federation `__schema`.

### **4.2 Golden Gate (Apollo)**
- Simulate schema changes pre-release.

### **4.3 `graphql-debugger`**
```bash
npm install graphql-debugger
```
Automatically logs query execution.

### **4.4 Performance Profiling**
- **Bubblewrap (Apollo):** Detect N+1 queries.
- **K6:** Simulate subscription load.

---

## **5. Prevention Strategies**

| **Strategy**                     | **Action**                                  |
|-----------------------------------|--------------------------------------------|
| **Federation**                    | Use `@key` consistently and test `__schema` |
| **Relay**                         | Enforce `__typename` in all mutations       |
| **Subscriptions**                 | Validate WebSocket URLs and auth            |
| **General**                       | Use `DataLoader` to batch queries          |

### **Best Practices**
1. **Federation:**
   - Always test schema merges with `apollo federation merge`.
   - Use `@requires` to avoid N+1 queries.
2. **Relay:**
   - Use `relay-normalize` to validate cursors.
   - Mock `createUser` mutations in tests.
3. **Subscriptions:**
   - Rate-limit subscriptions to prevent abuse.
   - Use `onConnect` guards.

---

## **6. Conclusion**
GraphQL patterns like Federation, Relay, and Subscriptions require careful debugging. Start with the **symptom checklist**, use **Apollo Studio** for schema validation, and ensure **cursor/WebSocket correctness**. Prevent issues by enforcing type safety and batching.

**Key Takeaways:**
- Federation: Check `__schema` and `@key` fields.
- Relay: Validate `cursor` and `__typename`.
- Subscriptions: Test WebSocket connections.

---
**Need deeper dives?** Check Apollo’s [official docs](https://www.apollographql.com/docs/) or Relay’s [spec](https://relay.dev/).