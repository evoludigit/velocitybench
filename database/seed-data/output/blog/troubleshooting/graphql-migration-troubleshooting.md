# **Debugging GraphQL Migration: A Troubleshooting Guide**

## **1. Introduction**
Migrating from REST to GraphQL—or upgrading an existing GraphQL schema—can introduce unexpected issues. This guide provides a structured approach to **identifying, diagnosing, and resolving** common problems during a GraphQL migration.

---

## **2. Symptom Checklist**
Before diving into fixes, validate these symptoms to pinpoint the root cause:

| **Category**               | **Symptoms**                                                                 |
|----------------------------|------------------------------------------------------------------------------|
| **Schema Mismatch**        | Queries return unexpected fields, errors like `Cannot query field "X"`.    |
| **Performance Issues**     | Slow responses, timeouts, or excessive memory usage.                        |
| **Data Inconsistency**     | Stale data, orphaned records, or missing relationships.                     |
| **Authentication/Authorization** | Missing permissions, 403/401 errors, or incorrect role-based access.       |
| **Dependency Issues**      | Missing database migrations, unresolved resolver dependencies.              |
| **Testing Failures**       | Unit tests pass but integration tests fail; CI/CD pipeline breaks.         |
| **Client-Side Errors**     | Frontend queries fail with malformed responses or missing data.             |

---

## **3. Common Issues & Fixes**

### **3.1 Schema Mismatch: Unexpected Fields or Errors**
**Symptoms:** `GraphQLError: Cannot query field "X" on type Y` or missing expected fields.
**Root Cause:**
- Schema not updated to match new API structure.
- Resolvers not aligned with the schema.

**Debugging Steps:**
1. **Verify Schema Changes**
   - Compare old vs. new schema using tools like:
     ```bash
     graphql-codegen generate --schema-out schema.json --input schema.graphql
     ```
   - Ensure all types, fields, and directives are correctly defined.

2. **Check Resolver Alignment**
   ```javascript
   // Example: Ensure resolver matches the schema type
   type Query {
     user(id: ID!): User
   }

   const resolvers = {
     Query: {
       user: async (_, { id }, { dataSources }) => {
         return await dataSources.db.getUser(id); // Ensure method exists
       }
     }
   };
   ```

3. **Update Client Queries**
   - Regenerate GraphQL client types if using `graphql-codegen`:
     ```bash
     graphql-codegen generate --schema schema.graphql --document ./queries.graphql
     ```

---

### **3.2 Performance Bottlenecks: Slow Queries or Timeouts**
**Symptoms:** Latency spikes, long-running queries, or HTTP 504 errors.
**Root Cause:**
- Deeply nested queries.
- Missing data loaders or inefficient database queries.
- Lack of caching.

**Debugging Steps:**
1. **Profile Queries**
   - Use Apollo’s **server-side instrumentation**:
     ```javascript
     const server = new ApolloServer({
       typeDefs,
       resolvers,
       tracing: true, // Enable query tracing
     });
     ```
   - Check the **Network tab** in Chrome DevTools for slow queries.

2. **Optimize Resolvers**
   - Use **Data Loaders** to batch database calls:
     ```javascript
     const DataLoader = require('dataloader');

     const userLoader = new DataLoader(async (ids) => {
       const users = await db.query('SELECT * FROM users WHERE id IN ($1)', ids);
       return users.map(u => u.id); // Batch fetch
     });

     resolvers.Query.user = async (_, { id }) => {
       return userLoader.load(id);
     };
     ```

3. **Implement Caching**
   - Cache frequent queries with `@cache-control` directives or Redis.

---

### **3.3 Data Inconsistency: Missing or Stale Data**
**Symptoms:** Frontend receives empty responses or incorrect data.
**Root Cause:**
- Missing database migrations.
- Schema changes not reflected in the database.

**Debugging Steps:**
1. **Verify Database Schema**
   - Check if migrations ran successfully:
     ```bash
     # Example for Prisma
     prisma migrate status
     ```
   - Compare DB schema with the new GraphQL schema.

2. **Validate Sample Queries**
   - Manually test queries in **GraphiQL/Playground**:
     ```graphql
     query {
       users {
         id
         name
         posts { title }
       }
     }
     ```
   - Cross-check with raw SQL if needed.

3. **Check Resolver Logic**
   ```javascript
   // Example: Ensure resolver fetches latest data
   resolvers.Post = {
     content: async (post) => {
       return await db.getPostContent(post.id); // Must fetch from DB, not cache only
     }
   };
   ```

---

### **3.4 Authentication Issues: 403/401 Errors**
**Symptoms:** Frontend fails to authenticate or lacks permissions.
**Root Cause:**
- Missing or misconfigured context providers.
- Incorrect role-based permissions.

**Debugging Steps:**
1. **Inspect Context**
   - Ensure `context` is passed correctly:
     ```javascript
     const server = new ApolloServer({
       context: ({ req }) => ({
         user: decodeToken(req.headers.authorization), // Ensure token is decoded
       }),
     });
     ```

2. **Validate Permissions**
   ```javascript
   // Example: Check if user has access
   resolvers.Query.deletePost = async (_, { postId }, { user }) => {
     if (!user.isAdmin) throw new Error("Forbidden");
     await db.deletePost(postId);
   };
   ```

3. **Test with `curl`**
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:4000/graphql
   ```

---

### **3.5 Dependency Issues: Missing Database Tables**
**Symptoms:** Resolvers fail with `Error: Column does not exist`.
**Root Cause:**
- Database migrations forgot to run.
- Schema defines fields without DB columns.

**Debugging Steps:**
1. **Run Migrations**
   ```bash
   # Example for TypeORM
   npm run migration:run
   ```

2. **Check Schema ↔ DB Sync**
   - Ensure `prisma schema.prisma` (or ORM config) matches the DB.

3. **Add Fallbacks**
   ```javascript
   resolvers.User = {
     email: async (user) => {
       // Fallback if DB lacks email
       return user.email || 'default@example.com';
     }
   };
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**       | **Use Case**                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| **GraphiQL/Playground**  | Manually test queries/resolvers.                                           |
| **Apollo Trace**         | Analyze slow queries.                                                       |
| **Logging (Winston/Pino)** | Debug resolver execution.                                                  |
| **Database Logs**        | Check SQL queries for inefficiencies.                                       |
| **Postman/curl**         | Verify HTTP-level issues.                                                   |
| **Lighthouse (Chrome)**  | Audit performance bottlenecks.                                             |

**Example: Apollo Tracing**
```javascript
const server = new ApolloServer({
  schema,
  context: ({ req }) => ({ req }),
  tracing: true,
  plugins: [
    {
      requestDidStart: () => ({
        willResolveField({ fieldName }) {
          console.log(`Resolving ${fieldName}`);
        }
      })
    }
  ]
});
```

---

## **5. Prevention Strategies**
### **5.1 During Migration**
✅ **Use Schema Stubs** – Start with a working schema, incrementally update.
✅ **Mock Data Early** – Test resolvers with fake data before DB migration.
✅ **Automate Schema Validation** – Use `graphql-schema-tools` to detect conflicts.

### **5.2 Post-Migration**
🔹 **Feature Flags** – Roll out changes gradually.
🔹 **Canary Testing** – Deploy to 10% of users before full rollout.
🔹 **Schema Registry** – Track versioned schemas for rollback.

### **5.3 Best Practices**
🔧 **Modularize Resolvers** – Keep them small and testable.
🔧 **Use TypeScript** – Catch schema/resolver mismatches early.
🔧 **Document Breaking Changes** – Maintain a changelog.

---

## **6. Final Checklist Before Going Live**
| **Check**                          | **Action**                                                                 |
|------------------------------------|----------------------------------------------------------------------------|
| ✅ Schema matches DB structure     | Run `graphql-codegen` validation.                                         |
| ✅ Resolvers pass unit tests        | Update test suite for new schema.                                          |
| ✅ Performance under load           | Benchmark with k6/Apache Bench.                                            |
| ✅ Authentication works for all roles | Test with `curl` and different tokens.                                   |
| ✅ Rollback plan exists             | Document database rollback SQL.                                            |

---

## **7. Summary**
GraphQL migrations can be smooth if you:
1. **Validate schema early** (avoid runtime errors).
2. **Optimize resolvers** (use Data Loaders, caching).
3. **Test thoroughly** (unit + integration tests).
4. **Monitor in production** (Apollo, logging).
5. **Plan rollbacks** (feature flags, versioned schemas).

By following this guide, you can **minimize downtime** and **ship GraphQL migrations confidently**. 🚀