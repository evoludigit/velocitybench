# **Debugging *The Evolution of API Architectures: From RPC to GraphQL* – A Troubleshooting Guide**
*Troubleshooting API latency, schema conflicts, performance bottlenecks, and connectivity issues across RPC, REST, GraphQL, and gRPC.*

---

## **1. Symptom Checklist**
Before diving into debugging, confirm which symptoms match your issue:

### **API Latency & Performance Issues**
- [ ] High **response times** (e.g., >500ms for GraphQL vs expected <200ms)
- [ ] Slow **query execution** (GraphQL) or **call chaining** (RPC)
- [ ] **Cold start delays** (serverless or microservices)
- [ ] **Throttling errors** (e.g., `429 Too Many Requests`)

### **Schema & Data Issues**
- [ ] **Schema conflicts** (GraphQL schema drift, gRPC protobuf mismatches)
- [ ] **Missing or incorrect response data** (e.g., fields not returned in GraphQL)
- [ ] **Type errors** (e.g., `Invalid GraphQL Response`, `protobuf decode error`)

### **Connectivity & Network Problems**
- [ ] **Connection resets** (gRPC `UNKNOWN` error, REST `502 Bad Gateway`)
- [ ] **DNS/timeouts** (DNS resolution failures, TCP handshake timeouts)
- [ ] **Load balancer issues** (unexpected request routing)

### **Error Handling & Logging**
- [ ] **Incomplete error messages** (e.g., no stack trace in GraphQL errors)
- [ ] **Missing logs** (debug logs not enabled in RPC/gRPC servers)
- [ ] **Uncaught exceptions** (e.g., `NullPointerException` in gRPC interceptors)

### **Security & Authentication Issues**
- [ ] **JWT/OAuth failures** (invalid tokens, missing headers)
- [ ] **CORS errors** (GraphQL: `No 'Access-Control-Allow-Origin'`)
- [ ] **gRPC auth misconfiguration** (`PERMISSION_DENIED` errors)

---

## **2. Common Issues & Fixes**

### **2.1 High Latency in GraphQL (Deep Querying)**
**Symptom:**
A GraphQL query with nested selections (e.g., `users { id, posts { title } }`) takes **3+ seconds** despite simple data.

**Root Cause:**
- **N+1 queries** (missing `@defer` or `@stream` directives).
- **Large payloads** (thousands of records).
- **Unoptimized resolvers** (database calls per field).

**Fixes:**
#### **A. Optimize Query Resolution (N+1 Problem)**
**Before (Problematic):**
```javascript
// Users resolver fetches posts for each user (N+1 queries)
const users = await db.query("SELECT * FROM users");
const posts = await db.query("SELECT * FROM posts WHERE userId IN (...)");
// Manually map posts to users (inefficient)
```
**After (Fixed):**
```javascript
// Use DataLoader (Facebook's batching library)
// or GraphQL Persisted Queries to reduce round trips
const { DataLoader } = require('dataloader');

const userLoader = new DataLoader(async (userIds) => {
  const users = await db.query("SELECT * FROM users WHERE id IN (...)");
  return userIds.map(id => users.find(u => u.id === id));
});

const postsLoader = new DataLoader(async (userIds) => {
  const posts = await db.query("SELECT * FROM posts WHERE userId IN (...)");
  // Group posts by userId (denormalized)
  const postsByUser = {};
  posts.forEach(post => postsByUser[post.userId] = posts);
  return userIds.map(id => postsByUser[id] || []);
});

// Usage in resolver:
const userData = await userLoader.load(userId);
const userPosts = await postsLoader.load(userId);
```

#### **B. Use Persisted Queries (Reduces Payload Size)**
```graphql
# Client sends a hash reference instead of the full query
POST /graphql
{
  "operationName": "GetUserPosts",
  "queryId": "abc123",
  "variables": { "id": 1 }
}
```
**Server-side configuration (Apollo):**
```javascript
// server.js
const { makeExecutableSchema } = require('@graphql-tools/schema');
const { createPersistedQueryPlugin } = require('apollo-server-plugin-persisted-queries');

const schema = makeExecutableSchema({ typeDefs, resolvers });
const server = new ApolloServer({
  schema,
  plugins: [createPersistedQueryPlugin({ cache: new PersistedQueryCache() })],
});
```

---

### **2.2 gRPC Connection Drops (`UNKNOWN` Errors)**
**Symptom:**
Clients intermittently get `grpc:client_connection_error:Unknown local service` or `Connection reset by peer`.

**Root Causes:**
- **Network instability** (VPN, cloud provider issues).
- **gRPC deadlines not enforced** (server hangs on slow calls).
- **Load balancer misconfiguration** (TCP health checks too aggressive).

**Fixes:**
#### **A. Set Deadlines for RPC Calls**
**Client-side (Node.js):**
```javascript
const { Client } = require('@grpc/grpc-js');
const client = new Client(target, credentials, {
  'grpc.default_call_options': { deadline: 5000 }, // 5s timeout
});
```
**Server-side (gRPC Go):**
```go
// Enable gRPC timeouts
server := grpc.NewServer(grpc.MaxCallRecvMsgSize(1024*1024),
                        grpc.MaxCallSendMsgSize(1024*1024),
                        grpc.Timeout(10*time.Second))
```

#### **B. Check Load Balancer Health Checks**
- **AWS ALB/NLB:** Ensure TCP health checks target a non-blocking gRPC service.
- **Kubernetes:** Set `readinessProbe` to check `/healthz` (not gRPC endpoints).

---

### **2.3 GraphQL Schema Mismatches (Type Errors)**
**Symptom:**
`Cannot return null for non-nullable field 'User.id'` or `GraphQL error: Field "posts" missing from schema`.

**Root Causes:**
- **Schema drift** (frontend queries changed without backend sync).
- **Missing resolvers** (new field added to schema but no resolver).
- **Incorrect GraphQL type definitions**.

**Fix:**
#### **A. Validate Schema with `graphql-tools`**
```bash
npm install graphql-tools @graphql-tools/schema
```
```javascript
const { validateSchema } = require('graphql-tools');

const schema = makeExecutableSchema({ typeDefs, resolvers });
const errors = validateSchema(schema);
if (errors.length > 0) {
  console.error("Schema validation errors:", errors);
  process.exit(1);
}
```

#### **B. Use Code Generation (GraphQL Codegen)**
```yaml
# codegen.yml
overwrite: true
schema: "src/schema.graphql"
generates:
  src/generated/graphql.ts:
    plugins:
      - typescript
      - typescript-resolvers
```
Run:
```bash
npx graphql-codegen
```
This ensures **frontend types match backend schema**.

---

### **2.4 RPC (REST/gRPC) Timeouts & Timeouts**
**Symptom:**
Client waits indefinitely for a response (e.g., REST `504 Gateway Timeout`).

**Root Causes:**
- **No timeout configuration** (server keeps processing).
- **Database query hangs** (e.g., `SELECT * FROM huge_table`).
- **gRPC `MaxCallRecvMsgSize` too low** (large payloads fail).

**Fix:**
#### **A. Set Timeout in REST (Express)**
```javascript
const express = require('express');
const app = express();
app.set('timeout', 3000); // 3s timeout
```
#### **B. Configure gRPC Message Size Limits**
```go
// Server-side (Go)
server := grpc.NewServer(
  grpc.MaxRecvMsgSize(100 * 1024 * 1024), // 100MB
  grpc.MaxSendMsgSize(100 * 1024 * 1024),
)
```

---

## **3. Debugging Tools & Techniques**
### **3.1 GraphQL-Specific Tools**
| Tool | Purpose | Example Command |
|------|---------|-----------------|
| **GraphiQL/Apollo Studio** | Interactive schema inspection | `http://localhost:4000/graphql` |
| **Stitch** | Schema merging (for federated GraphQL) | `npx @apollo/gateway` |
| **PostHog/Amplitude** | Query performance analytics | Track `executionTime` metrics |
| **Sentry** | Error tracking (GraphQL errors) | Configure in Apollo Server |

**Example: Apollo Server Metrics**
```javascript
const server = new ApolloServer({
  schema,
  introspection: true,
  plugins: [ApolloServerPluginUsageReporting],
});
server.listen().then(({ url }) => console.log(`🚀 Server ready at ${url}`));
```

### **3.2 gRPC Debugging**
| Tool | Purpose | Example |
|------|---------|---------|
| **gRPCurl** | Send gRPC requests like `curl` | `grpcurl -plaintext localhost:50051 api.User.GetUser 1` |
| **Kubernetes `kubectl port-forward`** | Debug pod logs | `kubectl port-forward svc/grpc-service 50051:50051` |
| **Envoy Proxy** | gRPC traffic inspection | Enable `access_log` in Envoy config |
| **Jager/WireMock** | Mock gRPC services | `wiremock-server -port 8080` |

**Example: gRPCurl Debugging**
```bash
# List available services
grpcurl -plaintext localhost:50051 list

# Check service health
grpcurl -plaintext -d '{}' localhost:50051 health.status
```

### **3.3 Network Diagnostics**
| Command | Purpose |
|---------|---------|
| **`tcpdump`** | Capture gRPC traffic | `tcpdump -i any port 50051` |
| **`netstat -tulnp`** | Check open gRPC ports | `ss -tulnp | grep 50051` |
| **`mtr`** | Trace gRPC endpoint latency | `mtr grpc-service.example.com` |
| **`curl -v`** | Debug HTTP/REST headers | `curl -v http://api.example.com/users` |

---

## **4. Prevention Strategies**
### **4.1 Schema Management**
- **Automate schema versioning** (e.g., GitHub PRs trigger schema updates).
- **Use GraphQL Federation** for microservices:
  ```graphql
  # Example: Apollo Federation
  type User @extends
    @key(fields: "id") {
    id: ID!
    posts: [Post!] @requires(fields: "userId")
  }

  type Post @key(fields: "id") {
    id: ID!
    author: User @requires(fields: "id")
  }
  ```
- **Enforce schema changes via CI/CD**:
  ```yaml
  # GitHub Actions
  - name: Validate schema
    run: npx graphql-codegen validate
  ```

### **4.2 Performance Optimization**
| Technique | Description | Tools |
|-----------|-------------|-------|
| **Batch & Caching** | Use `DataLoader` for N+1 fixes | `dataloader.js` |
| **Query Persistence** | Reduce payload size | `apollo-server-plugin-persisted-queries` |
| **gRPC Streaming** | Handle large datasets efficiently | `grpc-ts` |
| **Lazy Loading** | Defer non-critical fields | GraphQL `@defer` |

### **4.3 Error Handling & Monitoring**
- **Centralized logging** (ELK Stack, Datadog).
- **gRPC Error Codes Mapping**:
  ```go
  // Convert custom errors to gRPC codes
  if err == sql.ErrNoRows {
    return status.Errorf(codes.NotFound, "User not found")
  }
  ```
- **SLOs for API Latency**:
  - **P99 latency < 300ms** for GraphQL.
  - **5xx errors < 0.1%** for gRPC.

### **4.4 Security Hardening**
- **GraphQL:**
  - Rate limiting (`graphql-shield`).
  - Input validation (`graphql-validation`).
- **gRPC:**
  - TLS enforcement (`grpc-tls`).
  - Token-based auth (JWT in metadata):
    ```javascript
    // Client-side
    const metadata = new grpc.Metadata();
    metadata.set('authorization', `Bearer ${token}`);
    client.sayHello({ message: "Hello" }, metadata);
    ```

---

## **5. Quick Reference Table**
| **Issue** | **Debug Command** | **Fix** |
|-----------|------------------|---------|
| **GraphQL N+1 queries** | Use `DataLoader` | Batch database calls |
| **gRPC `UNKNOWN` errors** | `grpcurl -plaintext localhost:50051` | Set deadlines (`grpc.Timeout`) |
| **Schema mismatch** | `npx graphql-codegen validate` | Sync frontend/backend schemas |
| **High REST latency** | `curl -v --max-time 2 http://api.example.com` | Add timeout (`app.set('timeout', 2000)`) |
| **gRPC payload too large** | Check `MaxRecvMsgSize` | Increase in server config |

---

## **Final Checklist Before Production**
1. **Test schema changes** with `graphql-codegen validate`.
2. **Set gRPC deadlines** (`grpc.Timeout`).
3. **Enable metrics** (Apollo Server + Prometheus).
4. **Rate-limit GraphQL** (`graphql-shield`).
5. **Monitor gRPC connections** (`tcpdump` + `mtr`).

---
**Next Steps:**
- If issues persist, check **Kubernetes logs** (`kubectl logs <pod>`).
- For **gRPC**, verify **protobuf schema compatibility** (`protoc --validate`).
- For **GraphQL**, use **Apollo Studio** to compare dev/staging/prod schemas.

This guide ensures **fast troubleshooting** for API evolution challenges.