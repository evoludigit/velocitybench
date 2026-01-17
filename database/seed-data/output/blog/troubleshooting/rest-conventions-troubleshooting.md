# **Debugging REST Conventions: A Troubleshooting Guide**

## **1. Introduction**
REST (Representational State Transfer) is a widely adopted architectural style for designing networked applications. While REST is flexible, adhering to **REST Conventions** ensures consistency, maintainability, and testability. This guide focuses on debugging common REST API issues by following a structured troubleshooting approach.

---

## **2. Symptom Checklist**
Before diving into fixes, verify if your REST API is experiencing any of these symptoms:

| **Symptom**                          | **Description**                                                                 | **Possible Root Cause**                          |
|--------------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **API Endpoint Not Found (404)**     | Request to `/api/v1/users` returns `404 Not Found`.                           | Misconfigured routing, incorrect endpoint path.    |
| **Method Not Allowed (405)**         | `POST /api/v1/users` returns `405 Method Not Allowed` (only `GET` works).      | Incorrect HTTP method handling in server config.  |
| **Invalid Request (400 Bad Request)**| `POST /api/v1/users` fails with `{"error": "Validation failed"}`               | Missing/invalid request body or payload.         |
| **Unauthorized (401/403)**           | Access denied even with valid credentials.                                    | JWT token invalid/missing, role-based access denied. |
| **Rate Limiting (429 Too Many Requests)** | API returns `429` after heavy load.                                          | Missing rate-limiting middleware.                 |
| **CORS Issues (CORS Errors)**        | Frontend requests blocked with `No 'Access-Control-Allow-Origin' header`.    | CORS headers missing in response.                 |
| **Slow Response Times**              | API takes >5s to respond despite low traffic.                                 | Unoptimized database queries, missing caching.    |
| **Inconsistent Response Formats**    | Some endpoints return JSON, others plain text.                                | Improper response formatting logic.              |
| **Duplicate ID Issues**              | API generates duplicate IDs for new resources.                              | Missing auto-increment or UUID generation.      |
| **Schema Mismatch Errors**           | Validation fails due to schema changes.                                       | Backend schema not aligned with frontend contracts. |
| **Database Connectivity Issues**     | API crashes on database operations.                                          | Invalid DB config, connection pooling issues.     |

---

## **3. Common Issues & Fixes**

### **3.1. Endpoint Not Found (404)**
**Symptom:** Requesting `/api/v1/users` returns `404`.

**Possible Causes & Fixes:**

#### **A. Misconfigured Routing (Node.js/Express Example)**
```javascript
// ❌ Wrong: Incorrect path prefix
app.use("/api", require("./routes/users")); // Missing "/v1"

// ✅ Fix: Properly versioned route
app.use("/api/v1", require("./routes/users"));
```

#### **B. Missing API Documentation**
- **Fix:** Use tools like **Swagger/OpenAPI** to auto-document endpoints.
  ```yaml
  # openapi.yml
  paths:
    /api/v1/users:
      get:
        summary: "List all users"
        responses:
          200:
            description: "Users list"
  ```
- Deploy **Swagger UI** (`/swagger`) for live testing.

#### **C. Server Misconfiguration (Docker/Kubernetes)**
- **Check:** Ensure the container is exposing the correct port (`-p 3000:3000`).
- **Fix:** Verify `server.listen(3000)` matches frontend expectations.

---

### **3.2. Method Not Allowed (405)**
**Symptom:** `POST /api/v1/users` fails with `405`.

**Possible Causes & Fixes:**

#### **A. Incorrect HTTP Method Handling (Express Middleware)**
```javascript
// ❌ Only GET is allowed
app.get("/api/v1/users", (req, res) => { ... });

// ✅ Allow POST with validation
app.post("/api/v1/users", bodyParser(), validateUserInput, (req, res) => { ... });
```

#### **B. Missing `allow` Headers (CORS)**
```javascript
// ✅ Fix: Explicitly allow methods
app.use((req, res, next) => {
  res.header("Allow", "GET, POST, PUT, DELETE");
  next();
});
```

---

### **3.3. Invalid Request (400 Bad Request)**
**Symptom:** Frontend sends `{ name: "John" }`, but backend expects `{ username: "John" }`.

**Fix: Schema Validation (JSON Schema + Zod)**
```javascript
// ✅ Using Zod for validation
const userSchema = z.object({
  username: z.string().min(3), // Frontend must match this
  email: z.string().email(),
});

app.post("/api/v1/users", (req, res) => {
  const validatedData = userSchema.parse(req.body); // Throws error if invalid
  res.json(validatedData);
});
```
**Debugging Tip:**
- Use **Postman** to manually test payloads.
- Log `req.body` to verify received data:
  ```javascript
  console.log("Received:", req.body);
  ```

---

### **3.4. Authentication Errors (401/403)**
**Symptom:** `/api/v1/admin` returns `403 Forbidden` even with a valid token.

**Possible Causes & Fixes:**

#### **A. JWT Token Not Verified**
```javascript
// ❌ No token validation
app.get("/api/v1/admin", (req, res) => { ... });

// ✅ Verify JWT
const authenticate = (req, res, next) => {
  const token = req.headers.authorization?.split(" ")[1];
  if (!token) return res.status(401).send("Unauthorized");
  jwt.verify(token, "SECRET_KEY", (err, user) => {
    if (err) return res.status(403).send("Forbidden");
    req.user = user;
    next();
  });
};

app.get("/api/v1/admin", authenticate, (req, res) => { ... });
```

#### **B. Role-Based Access Control (RBAC) Missing**
```javascript
// ✅ Check user role
app.get("/api/v1/admin", authenticate, (req, res) => {
  if (req.user.role !== "admin") return res.status(403).send("Not allowed");
  res.json({ adminData: true });
});
```

---

### **3.5. Rate Limiting (429 Too Many Requests)**
**Symptom:** API fails after 100 requests in 1 minute.

**Fix: Implement Rate Limiting (Express Rate Limit)**
```javascript
const rateLimit = require("express-rate-limit");

const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,           // Limit each IP to 100 requests
});

app.use(limiter); // Apply to all requests
```
**Debugging Tip:**
- Check logs for `HTTP 429` errors.
- Use **Prometheus + Grafana** for monitoring.

---

### **3.6. CORS Issues**
**Symptom:** Frontend blocked: `Access to fetch at 'http://api.example.com' from origin 'http://localhost:3000' has been blocked by CORS policy`.

**Fix: Enable CORS (Express CORS Middleware)**
```javascript
const cors = require("cors");

app.use(
  cors({
    origin: ["http://localhost:3000", "https://your-frontend.com"], // Allowed domains
    methods: ["GET", "POST", "PUT", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);
```

---

### **3.7. Slow API Responses**
**Symptom:** API takes 5+ seconds to respond.

**Possible Causes & Fixes:**

#### **A. Unoptimized Database Queries**
```javascript
// ❌ Slow: N+1 query problem
const users = await User.findMany();
const posts = await Promise.all(users.map(user => UserPost.find({ userId: user.id })));

// ✅ Optimized: Single query with relation
const usersWithPosts = await User.findMany({
  include: { posts: true }, // Eager loading
});
```

#### **B. Missing Caching (Redis)**
```javascript
const redis = require("redis");
const client = redis.createClient();

app.get("/api/v1/trending", async (req, res) => {
  const cacheKey = "trending_posts";
  const cachedData = await client.get(cacheKey);

  if (cachedData) return res.json(JSON.parse(cachedData));

  const data = await db.query("SELECT * FROM trending_posts ORDER BY views DESC");
  await client.set(cacheKey, JSON.stringify(data), "EX", 60); // Cache for 60s
  res.json(data);
});
```

---

### **3.8. Inconsistent Response Formats**
**Symptom:** Some endpoints return `{ data: [...] }`, others `{ result: [...] }`.

**Fix: Standardize Response Structure**
```javascript
function standardizedResponse(res, status, data = {}, message = "") {
  res.status(status).json({
    success: status >= 200 && status < 300,
    data,
    message,
  });
}

app.get("/api/v1/users", (req, res) => {
  standardizedResponse(res, 200, { users: [...] });
});
```

---

### **3.9. Duplicate IDs**
**Symptom:** New users get duplicate IDs.

**Fix: Use UUID or Auto-Increment**
#### **Option 1: UUID (Database-Level)**
```sql
ALTER TABLE users ADD COLUMN id UUID DEFAULT gen_random_uuid();
```
#### **Option 2: Auto-Increment (Sequelize Example)**
```javascript
// ✅ Auto-increment enabled by default
const User = sequelize.define("User", {
  name: String,
});
```

---

### **3.10. Schema Mismatch Errors**
**Symptom:** Backend schema changed, but frontend still sends old payload.

**Fix: Version API Contracts**
1. **Use OpenAPI/Swagger** to document schemas.
2. **Add API Versioning** in headers:
   ```http
   Accept: application/vnd.api.v1+json
   ```
3. **Implement Deprecation Headers**:
   ```http
   Deprecation: "This endpoint will be removed in v2"
   ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**          | **Use Case**                                                                 | **Example Command**                     |
|-----------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Postman/Newman**          | Manual testing & automation of API calls.                                    | `newman run collection.json`             |
| **Swagger UI**              | Interactive API documentation & testing.                                     | `http://localhost:3000/swagger`         |
| **cURL**                    | Quick debugging of HTTP requests.                                            | `curl -X POST -H "Content-Type: json" -d '{"name":"John"}' http://api/users` |
| **Redis Inspector**         | Debug caching behavior.                                                     | `redis-cli --scan --pattern "*:trending_posts"` |
| **Prometheus + Grafana**    | Monitor response times, error rates, and rate limits.                        | `curl http://localhost:9090/targets`     |
| **K6 (Load Testing)**       | Simulate high traffic to find bottlenecks.                                  | `k6 run --vus 100 script.js`             |
| **Express Logger**          | Log request/response details for debugging.                                  | `app.use(morgan(':method :url :status :response-time ms'))` |
| **Database Query Profiler** | Identify slow SQL queries.                                                  | PostgreSQL: `EXPLAIN ANALYZE SELECT * FROM users;` |
| **JWT Debugging**           | Verify token signatures.                                                     | `jwt.verify(token, "SECRET_KEY")`       |

---

## **5. Prevention Strategies**

### **5.1. Automated Testing**
- **Unit Tests (Jest/Supertest):**
  ```javascript
  test("POST /users should return 201", async () => {
    const res = await request(app)
      .post("/api/v1/users")
      .send({ username: "test", password: "123" });
    expect(res.status).toBe(201);
  });
  ```
- **Integration Tests (Pact):**
  - Mock external services (e.g., Stripe API) to avoid flaky tests.

### **5.2. API Gateway & Load Balancing**
- **Use Kong/Apigee** to:
  - Rate-limit requests.
  - Route traffic (A/B testing).
  - Transform responses (CORS, headers).

### **5.3. Contract Testing (Pact)**
- Ensure frontend/backend schemas match:
  ```bash
  pact-broker verify --pact-dir=pacts --broker-base-url=http://pact-broker:8080
  ```

### **5.4. Feature Flags**
- Roll out changes gradually:
  ```javascript
  // Use flags like launchdarkly to toggle features
  const isNewAuthEnabled = launchdarkly.variation("new_auth", false);
  if (!isNewAuthEnabled) return oldAuthFlow(req, res);
  ```

### **5.5. Observability Stack**
- **Log Aggregation (ELK Stack):**
  - Centralize logs for easy debugging.
- **Distributed Tracing (Jaeger):**
  - Track requests across microservices.

### **5.6. Postmortem Meetings**
- After incidents:
  - Identify root cause.
  - Document fixes in a runbook (e.g., Confluence).
  - Automate detection (e.g., Slack alerts for `4xx` errors).

---

## **6. Quick Reference Cheat Sheet**
| **Issue**               | **Quick Fix**                                      | **Tool to Use**          |
|-------------------------|----------------------------------------------------|--------------------------|
| `404 Not Found`         | Check routing & API docs.                          | Swagger, Postman         |
| `405 Method Not Allowed`| Allow HTTP method in middleware.                    | Express `app.use()`      |
| `400 Bad Request`       | Validate input with Zod/Jooi.                       | `req.body` logging       |
| `401/403 Unauthorized`  | Verify JWT & roles.                                | `jwt.verify()`           |
| Slow Responses          | Optimize DB queries, add caching.                  | Redis, PostgreSQL EXPLAIN |
| CORS Errors             | Configure CORS headers.                             | `cors()` middleware      |
| Rate Limiting           | Use `express-rate-limit`.                           | Prometheus               |
| Duplicate IDs           | Use UUID or auto-increment.                        | Database schema          |

---

## **7. Conclusion**
Debugging REST APIs efficiently requires:
1. **Systematic Symptom Checking** (use the checklist).
2. **Leveraging Tools** (Postman, Swagger, Prometheus).
3. **Preventive Measures** (testing, observability, contract testing).

By following this guide, you can resolve 90% of REST API issues in under 30 minutes. For complex problems, **log everything** and **reproduce locally**.

---
**Final Tip:** Always **version your API** (`/v1/users`) to avoid breaking changes. 🚀