# **Debugging API Patterns: A Troubleshooting Guide**
*For Senior Backend Engineers*

APIs (Application Programming Interfaces) are the backbone of modern distributed systems. When APIs misbehave—whether due to misconfigurations, network issues, or logic errors—they can cause cascading failures, degraded performance, or security vulnerabilities. This guide covers common API-related issues and provides actionable debugging steps.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these symptoms to narrow down the problem:

| **Symptom**                          | **Possible Causes**                          |
|--------------------------------------|---------------------------------------------|
| **API Unresponsive**                 | - Server down, misconfigured load balancer   |
| **4xx/5xx Errors in Logs**           | - Invalid requests, rate limits exceeded    |
| **Slow Response Times**              | - Database bottlenecks, cold starts         |
| **Authentication Failures**          | - Expired tokens, misconfigured JWT/OAuth   |
| **Data Mismatch**                    | - Schema drift, incorrect transformations   |
| **Unexpected Delayed Responses**     | - Asynchronous operations stuck in queues   |
| **Third-Party API Failures**         | - Service outages, API key invalid          |
| **Memory/CPU Spikes**                | - Infinite loops, memory leaks              |

---
## **2. Common Issues and Fixes (With Code Examples)**

### **A. API Endpoints Returning 500 Errors (Internal Server Error)**
**Cause:** Unhandled exceptions, invalid database queries, or code crashes.
**Debugging Steps:**
1. **Check Server Logs** (`/var/log/nginx/error.log`, `/var/log/apache2/error.log`, or application logs).
2. **Verify Exception Handling** – Ensure proper error responses are returned.
3. **Test Endpoints Manually** (Postman/curl) to confirm the issue.

**Fix Example (Node.js/Express):**
```javascript
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: "Something went wrong!" });
});
```

### **B. Authentication Failures (401/403)**
**Cause:** Expired tokens, incorrect JWT/OAuth, or misconfigured middleware.
**Debugging Steps:**
1. **Inspect Headers** – Ensure `Authorization: Bearer <token>` is sent.
2. **Verify Token Validity** – Check token expiration (`exp` claim in JWT).
3. **Test with Valid Credentials** – Use Postman or `curl` with `--header "Authorization: Bearer ..."`.

**Fix Example (Python/Flask):**
```python
from flask_httpauth import HTTPTokenAuth
auth = HTTPTokenAuth()

@auth.verify_token
def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        return False, 401  # Token expired
    except jwt.InvalidTokenError:
        return False, 403  # Invalid token
```

### **C. Rate Limiting Issues (429 Too Many Requests)**
**Cause:** Client exceeds allowed requests per minute/hour.
**Debugging Steps:**
1. **Check Rate Limiter Logs** (e.g., Redis, database, or middleware logs).
2. **Verify Rate Limit Headers** (`X-RateLimit-Limit`, `X-RateLimit-Remaining`).
3. **Test with Burst Traffic** – Simulate high requests using `ab` (Apache Benchmark).

**Fix Example (Node.js with Express-Rate-Limit):**
```javascript
const rateLimit = require("express-rate-limit");

const limiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,           // Limit each IP to 100 requests per window
});

app.use("/api", limiter);
```

### **D. Slow API Responses (High Latency)**
**Cause:** Database queries, external API calls, or unoptimized code.
**Debugging Steps:**
1. **Profile Slow Queries** (e.g., PostgreSQL’s `pg_stat_statements`).
2. **Check External API Calls** – Use `curl -v` to measure latency.
3. **Enable APM Tools** (New Relic, Datadog) to identify bottlenecks.

**Fix Example (Optimizing Database Queries):**
```sql
-- Bad: Scans entire table
SELECT * FROM users WHERE created_at > '2023-01-01';

-- Good: Uses index
SELECT * FROM users WHERE created_at > '2023-01-01' ORDER BY id;
```

### **E. CORS (Cross-Origin Resource Sharing) Errors (403/401)**
**Cause:** Missing `Access-Control-Allow-Origin` headers.
**Debugging Steps:**
1. **Check Frontend Requests** – Ensure `Origin` header is present.
2. **Verify Server Response Headers** (`curl -I http://api.example.com`).

**Fix Example (Node.js/Express):**
```javascript
const cors = require("cors");
app.use(cors({ origin: "https://your-frontend.com" }));
```

### **F. Data Mismatch (Frontend vs. Backend)**
**Cause:** Schema mismatch, incorrect transformations, or caching issues.
**Debugging Steps:**
1. **Compare API Response vs. Frontend Expectation** (Postman vs. UI).
2. **Check Middleware** – Ensure data is formatted correctly (e.g., JSON parsing).

**Fix Example (Normalizing API Responses):**
```javascript
app.get("/users", async (req, res) => {
  const users = await db.query("SELECT * FROM users");
  res.json(users.rows.map(user => ({
    id: user.id,
    name: user.first_name + " " + user.last_name,
  })));
});
```

---

## **3. Debugging Tools and Techniques**

| **Tool**               | **Purpose**                                                                 | **Example Command/Usage**                     |
|------------------------|----------------------------------------------------------------------------|-----------------------------------------------|
| **curl**               | Send HTTP requests for manual testing.                                     | `curl -X POST http://api.example.com/login -H "Content-Type: application/json" -d '{"user": "test"}'` |
| **Postman / Insomnia** | UI-based API testing with request/response inspection.                   | Import Swagger/OpenAPI specs for automation.  |
| **NGINX Access Logs**  | Track HTTP requests, response times, and errors.                          | `tail -f /var/log/nginx/access.log`           |
| **Prometheus + Grafana** | Monitor API performance metrics (latency, errors, traffic).          | Query `http_request_duration_seconds` in Grafana. |
| **New Relic / Datadog** | APM for tracing slow API calls.                                            | Set up transaction traces for `/users` endpoint. |
| **Redis Inspector**    | Debug Redis-based rate limiting or caching issues.                       | `redis-cli MONITOR`                           |
| **Docker Logs**        | Debug containerized API issues.                                           | `docker logs <container_name>`                |
| **Swagger/OpenAPI**    | Validate API contracts and auto-generate client SDKs.                     | `/swagger-ui.html`                            |

---

## **4. Prevention Strategies**

### **A. Code-Level Best Practices**
✅ **Use Circuit Breakers** (e.g., `opossum` in Node.js) to prevent cascading failures.
```javascript
const { CircuitBreaker } = require("opossum");
const breaker = new CircuitBreaker(async () => fetchExternalAPI(), {
  timeout: 1000,
  errorThresholdPercentage: 50,
});
```
✅ **Implement Retry Logic** (with exponential backoff) for transient errors.
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_external_api():
    response = requests.get("https://api.example.com")
    response.raise_for_status()
```

### **B. Infrastructure & Monitoring**
✅ **Set Up Alerts** for:
   - High error rates (`5xx` responses > 1%).
   - Slow endpoints (`> 1s` response time).
   - Rate limit breaches.
✅ **Use Feature Flags** to disable problematic endpoints.
```javascript
if (featureFlags.isEnable("new_auth_system")) {
  return authenticateWithNewSystem(req);
} else {
  return authenticateWithOldSystem(req);
}
```
✅ **Containerize APIs** (Docker + Kubernetes) for easy scaling and rollback.

### **C. Testing & Validation**
✅ **Unit & Integration Tests** for API endpoints.
```javascript
test("GET /users should return 200", async () => {
  const res = await request(app).get("/users");
  expect(res.status).toBe(200);
});
```
✅ **Postman/Newman Tests** for automated API regression testing.
```json
// postman_collection.json
{
  "item": [
    {
      "name": "Test Login Endpoint",
      "request": {
        "method": "POST",
        "url": { "raw": "https://api.example.com/login" },
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": '{"user": "test", "password": "123"}'
        }
      },
      "response": [{"status": 200}]
    }
  ]
}
```

---

## **5. Quick Reference Cheat Sheet**

| **Issue**               | **Quick Fix**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|
| **500 Error**           | Check logs, add error handling middleware.                                  |
| **401/403 (Unauthorized)** | Verify JWT/OAuth tokens, check middleware.                                |
| **429 (Rate Limited)**  | Adjust rate limits, use caching.                                             |
| **Slow API**            | Profile queries, optimize DB indexes, cache responses.                      |
| **CORS Errors**         | Add `cors()` middleware, verify `Access-Control-Allow-Origin`.              |
| **Data Mismatch**       | Standardize API response format, validate schemas.                          |
| **External API Failures** | Implement retry logic with backoff.                                          |

---
## **Final Notes**
- **Start small**: Isolate the issue (client vs. server vs. database).
- **Log everything**: Use structured logging (JSON) for easier parsing.
- **Automate testing**: CI/CD should include API regression tests.
- **Monitor proactively**: Use APM tools to catch issues before users do.

By following this guide, you should be able to **quickly identify, debug, and fix** most API-related issues. For persistent problems, consider **reproducing in staging** or **opening a GitHub issue with logs and reproduction steps**.