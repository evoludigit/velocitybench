# **Debugging Hybrid Conventions: A Troubleshooting Guide**
*(For Backend Engineers Handling Mixed REST & GraphQL APIs)*

---

## **1. Introduction**
The **Hybrid Conventions** pattern combines RESTful and GraphQL APIs into a single service, often exposing both paradigms side-by-side. While this approach offers flexibility (e.g., REST for traditional clients, GraphQL for complex queries), it introduces complexity in routing, schema consistency, and request handling.

This guide focuses on **practical debugging** for hybrid systems, covering common symptoms, root causes, and solutions with code examples.

---

## **2. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| **Symptom** | **Description** | **Likely Cause** |
|-------------|----------------|------------------|
| **404 Not Found** on REST endpoints | GraphQL routes (e.g., `/graphql`) block REST paths | Misconfigured router |
| **500 Errors** in GraphQL queries | Schema drift between REST & GraphQL | Inconsistent data models |
| **Slow Responses** in GraphQL | Over-fetching or inefficient resolvers | Poorly optimized queries |
| **CORS Issues** | REST API not accessible from frontend | Inconsistent CORS headers |
| **Authentication Failures** | REST & GraphQL use different keys | Token validation mismatch |
| **Race Conditions** | Concurrent REST & GraphQL writes | Lack of transaction isolation |

---

## **3. Common Issues & Fixes**

### **3.1 REST Endpoints Blocked by GraphQL Router**
**Symptom:** `/users` (REST) returns `404` but `/graphql` works.
**Root Cause:** GraphQL route (e.g., `/graphql`) is defined before REST routes, causing conflicts.

**Fix 1: Reorder Routes (Express Example)**
```javascript
// Incorrect (GraphQL blocks REST)
app.use('/graphql', graphQLRouter);
app.get('/users', restController.getUsers);

// Correct (REST first, GraphQL fallback)
app.get('/users', restController.getUsers);
app.use('/graphql', graphQLRouter);
```

**Fix 2: Use Exact Path Matching**
```javascript
app.use('/graphql', graphQLRouter); // Only matches `/graphql`
app.get('/users', restController.getUsers); // Only matches `/users`
```

---

### **3.2 Schema Inconsistency Between REST & GraphQL**
**Symptom:** REST returns `{ id, name }` but GraphQL returns `{ id, name, email }` (extra field).
**Root Cause:** GraphQL schema includes fields not exposed in REST.

**Fix: Align Schemas**
```javascript
// REST (Single Responsibility Principle)
const restUserSchema = {
  id: { type: String, required: true },
  name: { type: String, required: true }
};

// GraphQL (Extends REST + Adds Fields)
const graphqlUserType = new GraphQLObjectType({
  name: 'User',
  fields: {
    id: { type: GraphQLID },
    name: { type: GraphQLString },
    email: { type: GraphQLString } // New field not in REST
  }
});
```
**Solution:** Adjust REST API to include all fields or document the discrepancy.

---

### **3.3 GraphQL Over-Fetching**
**Symptom:** GraphQL queries return tens of KB of data for simple requests.
**Root Cause:** Resolvers fetch entire records instead of projections.

**Fix: Use Projections**
```javascript
// Bad: Fetches full user
const user = await User.findById(req.userId);

// Good: Fetches only needed fields
const user = await User.findOne({
  _id: req.userId,
  projection: { name: 1, email: 1 } // Only include required fields
});
```

---

### **3.4 CORS Mismatch Between REST & GraphQL**
**Symptom:** Frontend fails to call REST but GraphQL works.
**Root Cause:** CORS headers differ between routes.

**Fix: Standardize CORS**
```javascript
// Middleware (Express)
app.use(cors({
  origin: ['http://frontend.com', 'http://localhost:3000'],
  methods: ['GET', 'POST', 'OPTIONS']
}));
```
**Note:** If using `graphql-middleware`, ensure CORS is applied to all routes.

---

### **3.5 Authentication Failures**
**Symptom:** REST accepts tokens, but GraphQL rejects them.
**Root Cause:** Different auth middleware.

**Fix: Unify Auth**
```javascript
// REST Auth (JWT)
app.use(jwtAuthMiddleware);

// GraphQL Auth (Same Middleware)
const graphQLRouter = new ApolloServer({
  context: ({ req }) => ({ user: req.user })
});
```

---

## **4. Debugging Tools & Techniques**

### **4.1 Logging & Tracing**
- **Tool:** `Morgan` (HTTP request logging)
  ```javascript
  const morgan = require('morgan');
  app.use(morgan('combined'));
  ```
- **Tool:** ` Winston` (Structured logging)
  ```javascript
  const winston = require('winston');
  const logger = winston.createLogger({ ... });
  logger.info({ request: req.path, method: req.method });
  ```

### **4.2 API Tracing**
- **Tool:** OpenTelemetry + Jaeger
  ```javascript
  const tracer = new Tracer('my-service');
  tracer.startSpan('processRequest').end();
  ```

### **4.3 Schema Validation**
- **Tool:** `GraphQL Code Generator` (Ensure schema consistency)
  ```bash
  graphql-codegen --config graphql.config.js
  ```

### **4.4 Postman/Insomnia**
- Test both REST (`/users`) and GraphQL (`/graphql`) endpoints independently.
- Use **Variables** to reuse auth headers across requests.

---

## **5. Prevention Strategies**
### **5.1 Design Guidelines**
- **Separate Concerns:** REST → CRUD, GraphQL → Complex Queries.
- **Shared Data Layer:** Use the same database models for both APIs.
- **Versioning:** Add `/v1/users` to avoid conflicts.

### **5.2 CI/CD Checks**
- **Unit Tests:** Mock both REST & GraphQL endpoints.
  ```javascript
  test('REST GET /users works', async () => {
    const res = await request(app).get('/users');
    expect(res.status).toBe(200);
  });
  ```
- **Schema Validation:** Lint GraphQL schema on push.
  ```bash
  graphql-schema-linter --schema schema.graphql
  ```

### **5.3 Monitoring**
- **Metrics:** Track REST vs. GraphQL latency (Prometheus + Grafana).
- **Alerts:** Set up alerts for 5xx errors in either API.

---

## **Conclusion**
Hybrid APIs are powerful but require meticulous debugging. Focus on:
1. **Router conflicts** (REST vs. GraphQL paths).
2. **Schema alignment** (avoid inconsistent fields).
3. **Performance bottlenecks** (projections, batching).
4. **Security** (unified auth, CORS).

By standardizing logging, testing, and monitoring, you can minimize outages in hybrid systems. Start with **symptom isolation** (e.g., `curl` vs. Postman tests) before diving into code fixes.

---
**Next Steps:**
- Audit your current router configuration.
- Compare REST & GraphQL schemas for drift.
- Implement a shared logging system.

Would you like a deeper dive into any specific issue?