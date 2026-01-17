# **Debugging GraphQL: A Troubleshooting Guide**

GraphQL is a powerful query language for APIs, but its flexibility can introduce edge cases that are difficult to debug. This guide covers common symptoms, troubleshooting steps, debugging tools, and preventive strategies to resolve GraphQL-related issues efficiently.

---

## **1. Symptom Checklist**

Before diving into fixes, identify which symptoms match your issue:

| **Category**               | **Possible Symptoms** |
|----------------------------|-----------------------|
| **Client-Side Issues**     | - 400/500 errors in response <br> - Missing/extra fields in responses <br> - Infinite loops (deep nesting) <br> - Slow query performance |
| **Server-Side Issues**     | - Unresolved references (missing types) <br> - Schema conflicts (multiple definitions) <br> - Database connection errors <br> - Memory leaks (large query depth) |
| **Network & Proxy Issues** | - CORS restrictions <br> - Rate-limiting or throttling <br> - Authentication failures (JWT/OAuth) |
| **Debugging Logs**         | - Missing error details <br> - Poorly formatted logs <br> - No GraphQL-specific debugging hooks |

If multiple symptoms appear, prioritize **client-side issues** (accessible via browser DevTools) before diving into server-side debugging.

---

## **2. Common Issues & Fixes**

### **2.1 Error: "Cannot Query Field X on Type Y"**
**Cause:** The requested field does not exist on the specified type in the schema.
**Fix:**
```graphql
# Example: Trying to query `user.email` but `User` type only has `name`.
query {
  user {
    name  # ✅ Valid
    email # ❌ Missing
  }
}
```
**Solution:**
- Check the schema with `curl http://localhost:4000/graphql -d '{ query { __schema { types { name fields { name } } } } }'`
- Ensure the field exists in the resolver or schema definition.
- If using auto-generated schemas (e.g., Dataloader), verify the resolver exists.

---

### **2.2 Error: "Maximum Execution Time Exceeded"**
**Cause:** Deeply nested queries or inefficient resolvers.
**Fix:**
```javascript
// Optimize resolvers to avoid deep recursion
const resolvers = {
  Query: {
    deepObject: async (_, __, { dataLoader }) => {
      const loader = dataLoader.load('deeperKey');
      return loader; // Avoid manual recursion
    }
  }
};
```
**Prevention:**
- Use **DataLoader** to batch and cache queries.
- Implement **query depth limiting** in middleware:
  ```javascript
  const graphqlMiddleware = (req, res, next) => {
    const maxDepth = 10;
    // Parse query and enforce depth limits
    next();
  };
  ```

---

### **2.3 Error: "403 Forbidden (Authentication Failure)"**
**Cause:** Missing or invalid tokens in headers.
**Fix:**
- Verify headers in Postman/curl:
  ```bash
  curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:4000/graphql
  ```
- Ensure the resolver checks permissions:
  ```javascript
  const resolvers = {
    Query: {
      secretData: (_, __, { user }) => {
        if (!user.isAdmin) throw new Error("Unauthorized");
        return { data: "Confidential" };
      }
    }
  };
  ```

---

### **2.4 Error: "Schema Validation Failed"**
**Cause:** Conflicting type definitions or invalid syntax.
**Fix:**
- Run schema validation:
  ```bash
  graphql validate http://localhost:4000/graphql --schema schema.graphql
  ```
- Example issue: Duplicate types.
  ```graphql
  type User { id: ID }
  type User { name: String } # ❌ Conflict
  ```
  **Fix:** Merge types or remove duplicates.

---

### **2.5 Error: "Missing Required Argument"**
**Cause:** A resolver expects an argument but it was omitted.
**Fix:**
```graphql
query {
  getPost(id: 1)  # ✅ Correct
  getPost         # ❌ Missing argument
}
```
**Solution:**
- Use `@arg` annotations in SDL (Schema Definition Language):
  ```graphql
  type Query {
    getPost(id: ID!): Post  # `!` makes it required
  }
  ```

---

## **3. Debugging Tools & Techniques**

### **3.1 GraphQL Playground / Apollo Studio**
- **Features:**
  - Auto-completion for queries.
  - Persisted queries (for caching).
  - Real-time error highlighting.

### **3.2 GraphQL Logger Middleware**
Add this to your Express/Apollo server:
```javascript
const { ApolloServer } = require('apollo-server');
const server = new ApolloServer({
  schema,
  context: ({ req }) => ({ req }),
  plugins: [
    {
      requestDidStart: () => ({
        willSendResponse({ response }) {
          if (response.errors) {
            console.error("GraphQL Error:", response.errors);
          }
        }
      })
    }
  ]
});
```

### **3.3 Performance Profiling**
Use `graphql-depth-limit` to detect slow queries:
```bash
npm install graphql-depth-limit
```
Configure in Apollo:
```javascript
const { createComplexityLimitRule } = require('graphql-validation-complexity');
const limit = createComplexityLimitRule(1000); // Max 1000 complexity
const schema = makeExecutableSchema({ ... });
const server = new ApolloServer({
  schema,
  validationRules: [limit]
});
```

### **3.4 Network Debugging**
- **Chrome DevTools (Network Tab):**
  - Check payloads for malformed GraphQL.
  - Inspect response headers for CORS/timeout issues.
- **cURL for Direct Testing:**
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    -d '{"query": "{ user { id name } }"}' \
    http://localhost:4000/graphql
  ```

---

## **4. Prevention Strategies**

### **4.1 Schema First Approach**
- Define your GraphQL schema **before** writing resolvers.
- Use **SDL (Schema Definition Language)** for clarity:
  ```graphql
  type User {
    id: ID!
    name: String!
  }

  type Query {
    user(id: ID!): User
  }
  ```

### **4.2 Query Depth & Complexity Limits**
- Enforce execution limits to prevent abuse:
  ```javascript
  const { GraphQLField } = require('graphql');
  const { createComplexityLimitRule } = require('graphql-validation-complexity');

  const complexityLimit = createComplexityLimitRule(1000); // 1000 complexity units
  const schema = makeExecutableSchema({
    resolvers,
    validationRules: [complexityLimit]
  });
  ```

### **4.3 DataLoader for Caching**
- Mitigate N+1 query problems:
  ```javascript
  const DataLoader = require('dataloader');
  const usersLoader = new DataLoader(
    async (ids) => {
      const results = await db.query('SELECT * FROM users WHERE id IN ($1)', ids);
      return ids.map(id => results.find(u => u.id === id));
    },
    { batch: true }
  );

  const resolvers = {
    Query: {
      user: (_, { id }, { dataLoaders }) => dataLoaders.usersLoader.load(id)
    }
  };
  ```

### **4.4 Automated Testing**
- Use Jest + `graphql-test-utils` to test queries:
  ```javascript
  const { createTestClient } = require('apollo-server-testing');
  const { ApolloServer } = require('apollo-server');
  const server = new ApolloServer({ schema });

  test('Should return a user', async () => {
    const { query } = createTestClient(server);
    const response = await query({
      query: `{ user { id } }`
    });
    expect(response.data.user.id).toBeDefined();
  });
  ```

---

## **5. Final Checklist for Quick Resolution**

| **Step** | **Action** |
|----------|------------|
| **1** | Check browser DevTools (Network tab) for raw GraphQL payloads. |
| **2** | Verify schema with `curl` or Apollo Studio. |
| **3** | Enable GraphQL error logging middleware. |
| **4** | Test with `cURL` to isolate client/server issues. |
| **5** | Apply query limits and DataLoader optimizations. |
| **6** | Use `graphql-depth-limit` to catch slow queries. |

---
**Key Takeaway:** GraphQL debugging follows a structured approach:
1. **Client issues (payload, headers, CORS)**
2. **Schema/Resolver conflicts**
3. **Network/Performance bottlenecks**
4. **Authentication/validation errors**

By combining logging, schema validation, and performance tools, you can resolve 90% of issues in under 30 minutes. Always start with the simplest checks (DevTools, `cURL`) before diving into server internals.