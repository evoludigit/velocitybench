# **Debugging REST APIs: A Practical Troubleshooting Guide**
*For Senior Backend Engineers*

---

## **Introduction**
REST (Representational State Transfer) APIs are the backbone of modern web services. When they fail, they can disrupt entire systems—from frontend applications to third-party integrations. This guide focuses on **practical debugging techniques** to quickly identify and resolve REST-related issues, minimizing downtime.

---

## **1. Symptom Checklist: When to Debug a REST API Issue**
Before diving into debugging, confirm the following symptoms:

### **Client-Side Symptoms (Frontend/Application)**
✅ **API requests failing silently** (no response from the server)
✅ **Error messages unclear** (e.g., "Network error," "Timeout")
✅ **Unexpected 4xx/5xx responses** (e.g., 401 Unauthorized, 500 Server Error)
✅ **Sluggish or inconsistent performance** (high latency, timeouts)
✅ **Request data not reaching the server** (missing headers, malformed payloads)
✅ **Response data not processed correctly** (parsing errors, schema mismatches)

### **Server-Side Symptoms (Backend/Logging)**
✅ **High error rates in logs** (`ConnectedRefused`, `Timeout`, `JSON parse errors`)
✅ **Unexpected HTTP status codes** (e.g., 400 Bad Request, 403 Forbidden)
✅ **Database queries timing out or failing** (if API interacts with a DB)
✅ **Rate limits being hit** (429 Too Many Requests)
✅ **Caching issues** (stale or missing responses)
✅ **Dependency failures** (external API timeouts, service unavailability)

### **Network-Side Symptoms**
✅ **Proxy/Firewall blocking requests** (HTTP 403 Forbidden, 502 Bad Gateway)
✅ **DNS resolution failing** (if API is behind a domain)
✅ **Load balancer misconfiguration** (traffic not routed correctly)
✅ **HTTPS/TLS handshake errors** (certificate issues, ciphers mismatch)

---

## **2. Common Issues & Fixes (With Code Examples)**

### **Issue 1: API Requests Failing with "Connection Refused" or "Timeout"**
**Symptoms:**
- Frontend logs: `NetworkError: Failed to fetch`
- Server logs: `TimeoutError` or `ECONNREFUSED`

**Root Cause:**
- Server is down, misconfigured, or unreachable.
- Network connectivity issues (firewall, proxy, VPN).
- Load balancer not forwarding traffic.

**Debugging Steps & Fixes:**

#### **A. Check Server Health**
```bash
# Ping the server (if TCP is allowed)
ping your-api-server

# Test HTTP connectivity with curl (no auth)
curl -v -X GET http://your-api-server:port/health

# Test with a tool like Postman
```
**Fix:**
- If server is down, check:
  - `systemctl status <service>` (Linux)
  - `netstat -tulnp | grep <port>` (check if port is listening)
  - Firewall rules (`ufw status` / `iptables -L`)

#### **B. Verify Network & Proxy Settings**
```bash
# Check if the request is going through a proxy
env | grep -i proxy
```
**Fix:**
- If behind a corporate proxy, ensure:
  ```bash
  export HTTP_PROXY=http://proxy-ip:port
  export HTTPS_PROXY=http://proxy-ip:port
  ```
- Disable proxy temporarily for testing:
  ```bash
  unset HTTP_PROXY HTTPS_PROXY
  ```

#### **C. Load Balancer Misconfiguration**
If using **NGINX / HAProxy**, check:
```nginx
# Example NGINX config issue
server {
    listen 80;
    server_name api.example.com;
    location / {
        proxy_pass http://localhost:3000;  # Wrong backend IP?
    }
}
```
**Fix:**
- Verify `proxy_pass` points to the correct backend.
- Check load balancer health checks:
  ```bash
  curl -I http://<load-balancer-ip>:health-check-endpoint
  ```

---

### **Issue 2: HTTP 401 Unauthorized (Authentication Failure)**
**Symptoms:**
- Frontend: `Unauthorized` (401) response.
- Server logs: Missing/expired JWT, invalid API key.

**Root Cause:**
- Missing `Authorization` header.
- Incorrect token format (e.g., `Bearer token` vs. `token`).
- Token expired or invalid.
- CORS preflight (OPTIONS) failing.

**Debugging Steps & Fixes:**

#### **A. Verify Headers in Request**
```javascript
// Correct way to send JWT in frontend (React example)
fetch('https://api.example.com/protected', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```
**Fix:**
- Ensure headers match the backend’s expected format.
- Check token validity:
  ```bash
  # Decode JWT (without verification)
  echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | base64 --decode | jq
  ```

#### **B. CORS Issues (Preflight Failure)**
If frontend makes a `PUT/DELETE` request, the server should handle `OPTIONS`:
```http
# Expected OPTIONS response (CORS preflight)
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
```
**Fix:**
- Ensure backend allows preflight:
  ```javascript
  // Express.js middleware (example)
  app.options('*', cors()); // Enable preflight
  ```

---

### **Issue 3: JSON Parsing Errors (400 Bad Request)**
**Symptoms:**
- Server logs: `SyntaxError: Unexpected token < in JSON at position X`
- Frontend: `JSON.parse error` or `SyntaxError`

**Root Cause:**
- Malformed JSON (e.g., trailing comma, unquoted key).
- Incorrect Content-Type (`text/plain` instead of `application/json`).
- Backend rejects non-JSON payloads.

**Debugging Steps & Fixes:**

#### **A. Validate JSON Input**
```bash
# Test with curl (ensure raw JSON)
curl -X POST http://api.example.com/data \
  -H "Content-Type: application/json" \
  -d '{"key": "value", "nested": {"ok": true}}'
```
**Fix:**
- Use a JSON validator like [JSONLint](https://jsonlint.com/).
- Ensure backend expects proper JSON:
  ```javascript
  // Express middleware to reject invalid JSON
  app.use(express.json({ strict: true }));
  ```

#### **B. Check Content-Type Headers**
```javascript
// Wrong: Sending JSON as text
fetch('...', {
  headers: { 'Content-Type': 'text/plain' }
});

// Correct:
fetch('...', {
  headers: { 'Content-Type': 'application/json' }
});
```

---

### **Issue 4: Rate Limiting (429 Too Many Requests)**
**Symptoms:**
- High error rates in logs (`429 Too Many Requests`).
- Frontend shows "Too many requests."

**Root Cause:**
- Missing `X-RateLimit-*` headers.
- No retry-after mechanism.
- Bot/abusive scraping.

**Debugging Steps & Fixes:**

#### **A. Check Rate Limit Headers**
```bash
curl -I http://api.example.com/protected
# Should return:
# HTTP/1.1 200 OK
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 5
# Retry-After: 10
```

**Fix:**
- Implement rate limiting (e.g., with `express-rate-limit`):
  ```javascript
  const rateLimit = require('express-rate-limit');

  app.use(rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests
  }));
  ```
- Use cache headers (`Cache-Control`) to reduce API calls.

---

### **Issue 5: Slow API Responses (High Latency)**
**Symptoms:**
- Frontend: `fetch` calls taking 5+ seconds.
- Server logs: Slow database queries.

**Root Causes:**
- Unoptimized database queries.
- External API calls blocking.
- Lack of caching (Redis, CDN).

**Debugging Steps & Fixes:**

#### **A. Profile Database Queries**
```javascript
// Example: Slow query in MongoDB
db.users.find().explain("executionStats")
// Look for "totalDocsExamined" >> "docsExamined"
```
**Fix:**
- Add indexes:
  ```javascript
  db.users.createIndex({ email: 1 });
  ```
- Use pagination (`limit`, `skip`).

#### **B. Cache Responses (Redis Example)**
```javascript
const redis = require('redis');
const client = redis.createClient();

app.get('/slow-query', async (req, res) => {
  const key = 'api:slow-query';
  const cached = await client.get(key);
  if (cached) return res.send(JSON.parse(cached));

  // Fetch from DB
  const data = await db.query('SELECT * FROM table WHERE ...');
  await client.set(key, JSON.stringify(data), 'EX', 3600); // Cache for 1h
  res.send(data);
});
```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                          | **Example Usage**                          |
|--------------------------|---------------------------------------|--------------------------------------------|
| **Postman / Insomnia**   | Test REST endpoints interactively.   | Send authenticated requests, check headers. |
| **cURL**                 | Debug raw HTTP requests/responses.    | `curl -v -H "Authorization: Bearer ..." ...` |
| **ngrep**                | Capture network traffic (port mirroring). | `ngrep -d eth0 'GET /api' port 80` |
| **Wireshark / tcpdump**  | Deep packet inspection.               | `tcpdump -i eth0 -s 0 -w debug.pcap` |
| **Kubernetes `kubectl`**| Debug containerized APIs.             | `kubectl logs <pod> -f`                   |
| **New Relic / Datadog**  | Monitor API performance.              | Check latency, error rates, traces.       |
| **JSON Validation**      | Catch malformed payloads.             | [JSONLint](https://jsonlint.com/)         |
| **GraphQL (if applicable)** | Debug GraphQL API errors.          | `query { user(id: 1) { name } }`           |
| **Strace / Ltrace**      | Debug system calls (Linux).           | `strace -f node /path/to/server.js`       |

---

## **4. Prevention Strategies**

### **A. Logging & Monitoring**
- **Structured logging** (JSON format) for easier parsing:
  ```javascript
  const { winston } = require('winston');
  const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
  });
  logger.info({ request: req.method, path: req.path, user: req.user });
  ```
- **Centralized logging** (ELK Stack, Datadog).
- **Alerting** (Slack/PagerDuty for 5xx errors).

### **B. API Documentation & Testing**
- **Automated API testing** (Postman Collections, Pact).
- **Contract testing** (ensure frontend <=> backend compatibility).
- **Swagger/OpenAPI** for auto-generated docs:
  ```javascript
  const swaggerUi = require('swagger-ui-express');
  const swaggerDocument = require('./swagger.json');
  app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));
  ```

### **C. Idempotency & Retry Mechanisms**
- **Idempotency keys** for duplicate requests:
  ```javascript
  // Example: Idempotency middleware
  const idempotencyMap = new Map();

  app.post('/create-user', (req, res) => {
    const idempotencyKey = req.headers['idempotency-key'];
    if (idempotencyMap.has(idempotencyKey)) {
      return res.status(200).send("Already processed");
    }
    idempotencyMap.set(idempotencyKey, true);
    // ... handle request
  });
  ```
- **Exponential backoff** for retries:
  ```javascript
  const retry = require('async-retry');
  async function callApiWithRetry() {
    await retry(
      async () => {
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
      },
      { retries: 3 }
    );
  }
  ```

### **D. Security Hardening**
- **Input validation** (Zod, Joi):
  ```javascript
  const { z } = require('zod');
  const schema = z.object({
    name: z.string().min(3),
    email: z.string().email(),
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).send(parsed.error);
  ```
- **Helmet.js** for HTTP headers:
  ```javascript
  const helmet = require('helmet');
  app.use(helmet());
  ```
- **Rate limiting** (as shown earlier).

### **E. Performance Optimization**
- **Database indexing** (ensure queries are fast).
- **Connection pooling** (for databases):
  ```javascript
  // PostgreSQL example
  const { Pool } = require('pg');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    max: 20, // Max connections
  });
  ```
- **Lazy loading** for large responses:
  ```javascript
  // GraphQL example (Prisma)
  const user = await prisma.user.findUnique({
    where: { id },
    select: { name: true }, // Only fetch needed fields
  });
  ```

---

## **5. Quick Checklist for Fast Debugging**
When an API issue arises, follow this **5-step checklist**:

1. **Check logs** (frontend + backend + server logs).
2. **Reproduce manually** (curl, Postman, or script).
3. **Isolate the issue** (client vs. server vs. network).
4. **Compare working vs. broken requests** (headers, payloads).
5. **Apply fixes incrementally** (test after each change).

---
## **Final Thoughts**
REST debugging often boils down to:
- **Network issues** (connections, proxies, load balancers).
- **Authentication problems** (headers, tokens, CORS).
- **Data format mismatches** (JSON, headers, payloads).
- **Performance bottlenecks** (DB, caching, external calls).

By following this guide, you should be able to **resolve 90% of REST issues within minutes**. For complex problems, **log analysis, network inspection, and performance profiling** are your best friends.

**Happy debugging!** 🚀