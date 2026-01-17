# **Debugging GraphQL Integration: A Troubleshooting Guide**

## **1. Introduction**
GraphQL integration can introduce complex issues due to its dynamic query nature, schema validation, and client-server interactions. This guide provides a structured approach to diagnosing and resolving common problems when integrating GraphQL into your backend systems.

---

## **2. Symptom Checklist**
Before diving into debugging, confirm which symptoms are present. Common GraphQL-related issues may manifest as:

### **Client-Side Symptoms**
- [ ] **4xx/5xx HTTP Errors** (e.g., `400 Bad Request`, `500 Server Error`)
- [ ] **Missing or Malformed Responses** (e.g., incomplete data, unexpected fields)
- [ ] **Query Timeouts** (slow responses or outright timeouts)
- [ ] **Authentication/Authorization Failures** (e.g., missing JWT, invalid permissions)
- [ ] **Schema Mismatches** (e.g., queried fields don’t exist, types are incorrect)
- [ ] **Subscription Issues** (failed real-time updates, dead connections)

### **Server-Side Symptoms**
- [ ] **Database Errors** (e.g., `ForeignKeyViolation`, `Timeout`)
- [ ] **Schema Validation Failures** (e.g., `ValidationError` on queries)
- [ ] **High Memory/CPU Usage** (query depth/execution time issues)
- [ ] **Caching Problems** (stale data, inconsistent responses)
- [ ] **Slow Query Performance** (N+1 query problems, inefficient resolvers)
- [ ] **Database Connection Leaks** (unclosed connections in resolvers)

---
## **3. Common Issues & Fixes**

### **Issue 1: Schema Validation Errors**
**Symptoms:**
- `ValidationError: Cannot query field "nonexistent" on type "User"`
- `ValidationError: Argument "invalidArg" of required type "Int!" was not provided.`

**Root Cause:**
The client is sending a query that doesn’t match the GraphQL schema (e.g., missing fields, incorrect types, or undefined arguments).

**Debugging Steps:**
1. **Check the Schema:**
   Ensure the query matches the defined schema. Use tools like GraphQL Playground or Apollo Studio to inspect the schema.
   ```graphql
   # Example schema snippet:
   type User {
     id: ID!
     name: String!
     age: Int  # Not required
   }
   ```
   A query like `query { user { age } }` would fail if `age` is not required.

2. **Validate Queries with `graphql-validate` (Node.js):**
   ```javascript
   import { validate } from 'graphql';

   const result = validate(schema, document);
   if (result.length > 0) {
     console.error("Validation errors:", result);
   }
   ```

3. **Enable GraphQL Debugging Middleware (Express/Apollo):**
   ```javascript
   const { ApolloServer } = require('apollo-server-express');
   const server = new ApolloServer({
     schema,
     debug: true, // Logs validation errors
   });
   ```

**Fix:**
- Update the client query to match the schema.
- Add `@deprecated` annotations for removed fields.
- Use GraphQL code generation tools (e.g., GraphQL Code Generator) to auto-generate types.

---

### **Issue 2: N+1 Query Problems**
**Symptoms:**
- Slow response times when fetching related data.
- High database load despite simple queries.

**Root Cause:**
The resolver executes a new query for each relationship (e.g., fetching all users, then for each user, fetching their posts).

**Debugging Steps:**
1. **Enable Query Tracing (Apollo/Dataloader):**
   ```javascript
   const server = new ApolloServer({
     schema,
     dataSources: () => new DataSource(),
     context: ({ req }) => ({ user: req.user }),
     plugins: [ApolloServerPluginUsageReportingReport],
   });
   ```
   Check the generated query plan for redundant calls.

2. **Check Resolver Logic:**
   ```javascript
   UserType.resolveField('posts', user, {}, context) {
     // BAD: N+1 query
     return Post.findAll({ where: { userId: user.id } });
   }
   ```

**Fix:**
- **Use Dataloader (Batch & Cache):**
  ```javascript
  import DataLoader from 'dataloader';

  const userLoader = new DataLoader(async (userIds) => {
    const users = await User.findAll({ where: { id: userIds } });
    return userIds.map(id => users.find(u => u.id === id));
  });

  UserType.resolveField('posts', user, {}, { dataLoader: { userLoader } }) {
    return userLoader.load(user.id);
  }
  ```

- **Preload Data (DataLoader Batch):**
  ```javascript
  async function fetchUserWithPosts(userIds) {
    const users = await User.findAll({ where: { id: userIds }, include: [Posts] });
    return users.map(u => ({ user: u, posts: u.posts }));
  }
  ```

---

### **Issue 3: Authentication/Authorization Failures**
**Symptoms:**
- `403 Forbidden` or `401 Unauthorized`.
- Missing fields in responses despite valid JWT.

**Root Cause:**
- Missing or incorrect JWT validation.
- Incorrect permission checks in resolvers.

**Debugging Steps:**
1. **Check Middleware:**
   ```javascript
   // Example: Apollo middleware for auth
   const context = ({ req }) => {
     const token = req.headers.authorization || '';
     if (!token) throw new AuthenticationError("Missing token");
     const user = verifyToken(token); // Custom verify logic
     return { user };
   };
   ```

2. **Test with Postman/curl:**
   ```bash
   curl -H "Authorization: Bearer <token>" http://localhost:4000/graphql
   ```

**Fix:**
- **Validate JWT Properly:**
  ```javascript
  import jwt from 'jsonwebtoken';

  const verifyToken = (token) => {
    try {
      return jwt.verify(token, process.env.JWT_SECRET);
    } catch (err) {
      throw new AuthenticationError("Invalid token");
    }
  };
  ```

- **Use Permission Checks in Resolvers:**
  ```javascript
  PostType.resolveField('content', post, { user }, context) {
    if (!context.user || context.user.id !== post.authorId) {
      throw new ForbiddenError("Not authorized");
    }
    return post.content;
  }
  ```

---

### **Issue 4: Subscriptions Not Working**
**Symptoms:**
- Subscriptions fail silently or return no data.
- WebSocket connection drops immediately.

**Root Cause:**
- Missing PubSub or incorrect subscription setup.
- Event bus not properly configured.

**Debugging Steps:**
1. **Check PubSub Initialization:**
   ```javascript
   import { PubSub } from 'graphql-subscriptions';

   const pubsub = new PubSub();
   ```

2. **Verify Subscription Resolver:**
   ```graphql
   type Subscription {
     newPost: Post!
   }
   ```

   ```javascript
   PostType.subscriptions({
     newPost: {
       subscribe: () => pubsub.asyncIterator(['NEW_POST']),
     },
   });
   ```

3. **Test with GraphQL Playground/Apollo Client:**
   ```graphql
   subscription {
     newPost {
       id
       title
     }
   }
   ```

**Fix:**
- **Ensure PubSub is Properly Linked:**
  ```javascript
  const postCreated = (payload) => {
    pubsub.publish('NEW_POST', { newPost: payload.post });
  };
  // Call `postCreated` after creating a post in your resolver.
  ```

- **Check WebSocket Endpoint:**
  Apollo Server requires a dedicated WebSocket server. Ensure:
  ```javascript
  const server = new ApolloServer({ schema });
  const { url } = await server.listen({ port: 4000 });
  console.log(`🚀 Server ready at ${url}`);
  ```

---

### **Issue 5: Slow Query Performance**
**Symptoms:**
- Long query execution times (e.g., >500ms).
- Timeout errors in production.

**Root Cause:**
- Unoptimized database queries.
- Deeply nested GraphQL queries.

**Debugging Steps:**
1. **Enable Query Tracing:**
   ```javascript
   const server = new ApolloServer({
     schema,
     tracing: true, // Logs query execution time
   });
   ```

2. **Profile with `apollo-server` Metrics:**
   ```javascript
   import { ApolloServerPluginUsageReporting } from 'apollo-server-core';

   const server = new ApolloServer({
     plugins: [ApolloServerPluginUsageReportingReport],
   });
   ```

**Fix:**
- **Add Query Depth Limits:**
  ```javascript
  const server = new ApolloServer({
    schema,
    maxQueryDepth: 5, // Prevents overly complex queries
  });
  ```

- **Optimize Resolvers with Indexes:**
  Ensure database indexes are set for frequently queried fields.

- **Use Fragments/Aliases to Reduce Redundancy:**
  ```graphql
  query {
    user {
      id
      posts {
        id
        title
      }
      comments {
        id
        content
      }
    }
  }
  ```

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Purpose**                                                                 | **Example Usage**                                                                 |
|------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **GraphQL Playground** | Interactive query testing & schema inspection.                             | `http://localhost:4000/graphql`                                                   |
| **Apollo Studio**      | Schema introspection, performance monitoring.                               | Upload schema to `https://studio.apollographql.com`                             |
| **Postman/curl**       | Testing mutations/subscriptions with HTTP/WebSocket.                        | `curl -X POST -H "Content-Type: application/json" http://localhost:4000/graphql` |
| **Apollo Server Plugins** | Query tracing, metrics, and debugging.                                    | `ApolloServerPluginUsageReportingReport`                                         |
| **Dataloader**         | Batch loading & caching to prevent N+1 queries.                              | `new DataLoader(fetchUserPosts)`                                                 |
| **Logging Middleware** | Log query context (request ID, user, etc.).                                 | `console.log({ reqId, user, query })`                                             |

---

## **5. Prevention Strategies**

### **1. Schema First Approach**
- **Define Schema Before Implementing Logic:**
  Use tools like GraphQL CodeGen to auto-generate types from your schema.
  ```bash
  graphql-codegen --schema schema.graphql --generates src/types.ts
  ```

### **2. Input Validation**
- **Use `GraphQLInputObjectType` for Inputs:**
  ```javascript
  const CreateUserInput = new GraphQLInputObjectType({
    name: 'CreateUserInput',
    fields: {
      name: { type: new GraphQLNonNull(GraphQLString) },
      email: { type: new GraphQLNonNull(GraphQLString) },
    },
  });
  ```

### **3. Rate Limiting & Query Complexity**
- **Prevent Complexity Attacks:**
  ```javascript
  const server = new ApolloServer({
    schema,
    maxQueryComplexity: 5000, // Prevent overly complex queries
  });
  ```

### **4. Monitoring & Alerts**
- **Track Slow Queries:**
  Use Prometheus + Grafana to monitor GraphQL query performance.
- **Enable Error Reporting:**
  Integrate with Sentry or Datadog for automated error tracking.

### **5. Testing**
- **Write Unit Tests for Resolvers:**
  ```javascript
  import { mockDeep } from 'jest-mock-extended';
  import { UserResolver } from './user.resolver';

  test('should return user with posts', async () => {
    const mockUser = { id: 1, name: 'Alice' };
    const mockPosts = [{ id: 1, title: 'Post 1' }];
    const mockDb = mockDeep<UserDb>();
    mockDb.findUserById.mockResolvedValue(mockUser);
    mockDb.getPostsByUserId.mockResolvedValue(mockPosts);

    const resolver = new UserResolver(mockDb);
    const result = await resolver.getUserWithPosts(1);
    expect(result.posts).toEqual(mockPosts);
  });
  ```

- **Integration Tests for Subscriptions:**
  Use `graphql-request` for subscription testing.
  ```javascript
  import { graphqlRequest } from 'graphql-request';

  test('should emit subscription event', async () => {
    const response = await graphqlRequest(
      'ws://localhost:4000/graphql',
      `
        subscription {
          newPost {
            title
          }
        }
      `
    );
    expect(response).toMatchSnapshot();
  });
  ```

---

## **6. Conclusion**
GraphQL integration requires careful handling of schema validation, query performance, and real-time features. By following this troubleshooting guide, you can:
✅ **Diagnose** issues using logs, tools, and validation.
✅ **Fix** common problems (N+1 queries, auth failures, slow responses).
✅ **Prevent** future issues with schema-first design, rate limiting, and monitoring.

**Final Tip:** Always **start with the client-side logs**, then move to the server if needed. Use **Dataloader for batching**, **PubSub for subscriptions**, and **Apollo tracing for performance**.