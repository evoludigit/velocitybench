# **Debugging API Guidelines: A Troubleshooting Guide**

## **1. Introduction**
APIs are the backbone of modern software systems, enabling seamless communication between services. Poorly designed APIs lead to inefficiencies, security vulnerabilities, and integration failures. This guide provides a structured approach to troubleshooting common API-related issues, ensuring compliance with best practices (API Guidelines) while resolving problems efficiently.

---

## **2. Symptom Checklist**
Before diving into debugging, identify which symptoms align with your API issue:

### **Client-Side Issues**
✅ **HTTP Errors (4xx/5xx)**
   - 400 Bad Request → Malformed payload or invalid input
   - 401/403 Unauthorized/Forbidden → Authentication/authorization failure
   - 404 Not Found → Endpoint or resource missing
   - 500 Internal Server Error → Server-side failure

✅ **Network-Timeouts or Slow Responses**
   - Requests hanging or taking too long (>2s)

✅ **Rate Limiting (429 Too Many Requests)**
   - Client exceeding allowed request limits

✅ **CORS (Cross-Origin Resource Sharing) Errors**
   - Browser blocks requests due to missing `Access-Control-Allow-Origin` headers

✅ **Authentication Failures**
   - Invalid API keys, expired tokens, or misconfigured OAuth2 flows

### **Server-Side Issues**
✅ **High Latency or Crashes**
   - Database queries slow/blocking API responses
   - Memory leaks causing OOM (Out of Memory) errors

✅ **Database Connection Issues**
   - Pool exhausted → `SQLSTATE[HY000] [2006] MySQL server has gone away`
   - Invalid credentials → `Connection refused`

✅ **Caching Problems**
   - Stale data returned → `Cache-Control` misconfiguration

✅ **Logging & Monitoring Gaps**
   - Missing request/response logs → Hard to trace failures

✅ **Security Vulnerabilities**
   - SQL Injection (`' OR 1=1 --`) → Unsanitized queries
   - XSS (`<script>alert(1)</script>`) → Unescaped responses

### **Integration Issues**
✅ **Microservices Communication Failures**
   - Service A failing to call Service B → Retry logic missing

✅ **Event-Driven Delays**
   - Kafka/RabbitMQ messages stuck → Consumer lag

✅ **Versioning Mismatches**
   - v1 vs. v2 endpoints causing incompatible payloads

---

## **3. Common Issues & Fixes (With Code Examples)**

### **3.1 HTTP Errors (4xx/5xx) & Debugging**
**Symptoms:**
- `400 Bad Request` → Malformed JSON/XML
- `500 Internal Server Error` → Server-side crash

**Debugging Steps:**
1. **Check Request Payload**
   Validate input structure (e.g., using OpenAPI/Swagger).
   ```json
   // Invalid (missing required field)
   { "name": "John" } // Missing "email"

   // Valid
   { "name": "John", "email": "john@example.com" }
   ```

2. **Enable Detailed Logging**
   ```javascript
   // Express.js example
   app.use(morgan('combined')); // Logs request/response details
   ```

3. **Validate API Responses**
   Ensure responses match expected formats (e.g., JSON Schema).
   ```javascript
   // Node.js with Joi validation
   const schema = Joi.object({ name: Joi.string().required() });
   const { error } = schema.validate(req.body);
   if (error) return res.status(400).send(error.details[0].message);
   ```

**Fixes:**
- **400 Bad Request** → Add input validation (e.g., Joi, Zod).
- **500 Errors** → Check server logs (`Nginx`, `ELK Stack`, `CloudWatch`).

---

### **3.2 Authentication & Authorization Failures**
**Symptoms:**
- `401 Unauthorized` → Invalid API key/token
- `403 Forbidden` → User lacks permissions

**Debugging Steps:**
1. **Verify Token Format**
   ```bash
   # Check JWT structure (e.g., base64 decode header payload)
   echo 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' | base64 -d | jq .
   ```

2. **Test with Postman/Insomnia**
   - Use correct `Authorization: Bearer <token>` header.

3. **Check Token Expiry**
   ```javascript
   // Node.js - Verify JWT expiry
   const { payload } = jwt.verify(token, secret);
   if (payload.exp < Date.now()) throw new Error("Token expired");
   ```

**Fixes:**
- **API Key Missing** → Ensure `x-api-key` header is sent.
- **Expired Token** → Implement refresh token flow.

---

### **3.3 Rate Limiting Issues**
**Symptoms:**
- `429 Too Many Requests` → Client exceeding limits

**Debugging Steps:**
1. **Check Rate Limit Headers**
   ```http
   HTTP/1.1 429 Too Many Requests
   Retry-After: 60
   X-Rate-Limit-Remaining: 0
   ```

2. **Monitor Requests**
   ```javascript
   // Express-rate-limit middleware
   const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
   app.use(limiter);
   ```

**Fixes:**
- **Increase Limits** → Adjust `max` in rate limiter.
- **Add Retry Logic** → Use `retry-after` header.

---

### **3.4 Database Connection Failures**
**Symptoms:**
- `SQLSTATE[HY000] [2006] MySQL server has gone away`
- `Connection refused`

**Debugging Steps:**
1. **Check Connection Pool**
   ```javascript
   // Node.js - MySQL connection pool
   const pool = mysql.createPool({ host: 'localhost', user: 'root' });
   pool.getConnection((err, conn) => { ... });
   ```

2. **Verify Credentials in Config**
   ```yaml
   # Correct vs. Incorrect (bad password)
   database:
     host: db.example.com
     user: admin
     password: secure123 # <-- Incorrect if wrong
   ```

**Fixes:**
- **Increase Pool Size** → `connectionLimit: 20` in `mysql.createPool`.
- **Retry Logic** → Exponential backoff for reconnections.

---

### **3.5 CORS Errors**
**Symptoms:**
- Browser blocks requests due to missing headers.

**Debugging Steps:**
1. **Check Response Headers**
   ```http
   HTTP/1.1 200 OK
   Access-Control-Allow-Origin: https://client.com
   Access-Control-Allow-Methods: GET, POST
   ```

2. **Test with `curl` (No CORS)**
   ```bash
   curl -H "Origin: https://client.com" http://api.example.com/data
   ```

**Fixes:**
- **Enable CORS in Server**
  ```javascript
  // Express.js - CORS middleware
  const cors = require('cors');
  app.use(cors({ origin: 'https://client.com' }));
  ```

---

### **3.6 Slow API Responses**
**Symptoms:**
- Requests taking >2s (perceived slowness).

**Debugging Steps:**
1. **Enable Tracing (OpenTelemetry)**
   ```bash
   curl -H "traceparent: 00-..." http://api.example.com/data
   ```

2. **Check Database Queries**
   ```sql
   -- Slow query log (MySQL)
   SET GLOBAL slow_query_log = 'ON';
   ```

**Fixes:**
- **Add Indexes** → Speed up `SELECT` queries.
- **Implement Caching (Redis)**
  ```javascript
  const redis = require('redis');
  const client = redis.createClient();
  const cacheKey = `user:${req.params.id}`;
  client.get(cacheKey, (err, data) => { ... });
  ```

---

## **4. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                          | **Example** |
|--------------------------|---------------------------------------|-------------|
| **Postman/Insomnia**     | Test API endpoints                   | Send `POST /users` with headers |
| **Swagger/OpenAPI**      | Validate API contract                 | `/docs` endpoint |
| **Log Aggregation**      | Debug server errors                   | ELK Stack, Datadog |
| **Database Profiler**    | Find slow queries                     | `EXPLAIN SELECT * FROM users;` |
| **Load Testing**         | Simulate traffic (k6, Locust)         | `k6 run script.js` |
| **Distributed Tracing**  | Trace request flow (OpenTelemetry)    | Jaeger UI |
| **Health Checks**        | Monitor service status                | `/health` endpoint |

---

## **5. Prevention Strategies**

### **5.1 API Design Best Practices**
✔ **Versioning** → `/v1/users` (avoid breaking changes)
✔ **Idempotency** → Use `Idempotency-Key` header for retries
✔ **Pagination** → Return `page=1&limit=10` instead of huge responses
✔ **Graceful Degradation** → Handle failures (e.g., fallback to cache)

### **5.2 Monitoring & Observability**
- **Logging** → Structured logs (JSON) for easier parsing.
- **Alerts** → Set up for `5xx` errors (PagerDuty, Slack).
- **Metrics** → Track latencies (`avg_response_time` in Prometheus).

### **5.3 Security Hardening**
- **Input Validation** → Sanitize all inputs (e.g., `helmet.js` for Express).
- **Rate Limiting** → Mitigate DDoS attacks.
- **HTTPS Enforcement** → Redirect `http` → `https`.
- **JWT Best Practices** → Short expiry, refresh tokens.

### **5.4 Testing Strategies**
- **Unit Tests** → Validate business logic (Jest, pytest).
- **Integration Tests** → Test API contracts (Postman, Karate).
- **E2E Tests** → Simulate real user flows (Cypress, Selenium).

### **5.5 Documentation & Collaboration**
- **OpenAPI/Swagger Docs** → Auto-generate client SDKs.
- **API Changelog** → Document breaking changes.
- **Internal API Guidelines** → Enforce consistency (e.g., `request_id` header).

---

## **6. Conclusion**
API debugging requires a systematic approach:
1. **Identify the symptom** (4xx? Slow? Auth fail?).
2. **Reproduce locally** (Postman, `curl`).
3. **Check logs & metrics** (ELK, Prometheus).
4. **Fix & validate** (unit tests, load testing).
5. **Prevent recurrence** (auto-healing, monitoring).

By following this guide, you’ll resolve API issues faster and maintain a robust API ecosystem.

---
**Next Steps:**
- Audit your APIs for compliance with [RESTful guidelines](https://restfulapi.net/).
- Automate testing with `API Blueprint` or `Swagger`.
- Implement **chaos engineering** (failover testing).