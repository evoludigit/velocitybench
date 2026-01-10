# **Debugging API Issues: A Practical Troubleshooting Guide**

APIs are the backbone of modern software systems, enabling seamless communication between services, clients, and databases. When APIs fail, the entire application ecosystem can be affected, leading to timeouts, data inconsistencies, security breaches, or degraded performance. This guide provides a structured approach to diagnosing and resolving API-related issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, identify and classify the issue using this checklist:

### **A. Client-Side Symptoms (Frontend/Application Issues)**
✅ **Request Failures**
- HTTP 4xx (Client Errors) – e.g., 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found)
- HTTP 5xx (Server Errors) – e.g., 500 (Internal Server Error), 502 (Bad Gateway), 503 (Service Unavailable), 504 (Gateway Timeout)
- CORS errors when making cross-origin requests
- Network timeouts (requests hanging indefinitely)

✅ **Response Issues**
- Incorrect data format (e.g., JSON parsing errors)
- Incomplete or missing payloads
- API responses delayed beyond acceptable thresholds

✅ **Authentication & Authorization Failures**
- Invalid API keys, JWT tokens, or OAuth tokens
- Missing or expired credentials
- Permission denied errors

✅ **Rate Limiting & Throttling**
- `"429 Too Many Requests"` errors
- Unexpected delays in API responses

---

### **B. Server-Side Symptoms (Backend Issues)**
✅ **Performance Degradation**
- Slow response times (e.g., > 1s for critical APIs)
- High CPU/memory usage on the API server
- Database bottlenecks (slow queries, locks)

✅ **Data Inconsistencies**
- Incorrect data returned vs. stored in the database
- Race conditions (e.g., concurrent updates leading to conflicts)
- Missing or duplicate records

✅ **Dependency Failures**
- Downstream service (DB, third-party API) unavailability
- Circuit breaker trips (e.g., in service mesh or retry logic)
- Network partitions affecting inter-service communication

✅ **Logging & Monitoring Alerts**
- Unhandled exceptions in logs
- High error rates in API call metrics
- Logs indicating deadlocks or timeouts

---

### **C. Network & Infrastructure Issues**
✅ **Connectivity Problems**
- DNS resolution failures
- Firewall or proxy blocking requests
- Load balancer misconfiguration (sticky sessions, health checks)

✅ **Load Balancer & Scaling Issues**
- Uneven distribution of traffic
- Session affinity failures
- Auto-scaling misconfigurations (e.g., new instances not ready)

✅ **Security Violations**
- SQL injection attempts in logs
- Unauthorized API access attempts
- Data leaks in responses (e.g., sensitive fields exposed)

---
**Next Step:** Once symptoms are identified, proceed to [Common Issues and Fixes](#3-common-issues-and-fixes) based on the observed behavior.

---

## **2. Common Issues and Fixes**

### **A. HTTP 4xx Errors (Client-Side Failures)**

#### **1. 400 Bad Request – Invalid Payload**
**Symptoms:**
- Frontend sends malformed JSON/XML.
- Required fields missing in the request body.

**Debugging Steps:**
1. **Inspect the Request Payload**
   Use browser DevTools (**Network tab**), Postman, or `curl` to check the exact request sent.
   ```bash
   curl -X POST https://api.example.com/users \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice", "email": "alice@example.com"}' \
     --verbose
   ```
   - Verify JSON structure matches API schema (e.g., using JSON Schema validation).
   - Check for typos in field names or missing required fields.

2. **Log Payload Validation Errors**
   Server-side, log the raw request body and validation failures:
   ```javascript
   // Express.js example
   app.use(jsonParser());
   app.post('/users', (req, res, next) => {
     const { name, email } = req.body;
     if (!name || !email) {
       console.error(`Validation failed: Missing fields. Body=${JSON.stringify(req.body)}`);
       return res.status(400).json({ error: "Missing required fields" });
     }
     next();
   });
   ```

3. **Frontend Validation**
   Add client-side validation (e.g., with libraries like `zod` or `yup`) to catch issues early.

---

#### **2. 401 Unauthorized – Invalid/Expired Token**
**Symptoms:**
- API requires authentication (Bearer/JWT/OAuth).
- Token missing, expired, or invalid.

**Debugging Steps:**
1. **Check Token Presence**
   - Ensure the `Authorization` header is included:
     ```http
     Authorization: Bearer <token>
     ```
   - Verify the token is not empty or malformed.

2. **Validate Token Format**
   - Verify the token structure (e.g., `Bearer <base64-encoded-payload>.<base64-encoded-signature>`).
   - Use tools like [jwt.io](https://jwt.io) to decode and verify JWTs.

3. **Expiration Check**
   - Ensure the token hasn’t expired (check `exp` claim in JWT).
   - Log token metadata for debugging:
     ```javascript
     // Express middleware
     app.use((req, res, next) => {
       const authHeader = req.headers.authorization;
       if (!authHeader) return res.status(401).send("No token provided");
       const token = authHeader.split(" ")[1];
       jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
         if (err) {
           console.error(`JWT Error: ${err.message}. Token: ${token}`);
           return res.status(401).send("Invalid token");
         }
         req.user = user;
         next();
       });
     });
     ```

4. **Token Rotation**
   - If using short-lived tokens, ensure the frontend fetches a new one on expiration.
   - Implement refresh tokens for seamless transitions.

---

#### **3. 403 Forbidden – Permission Denied**
**Symptoms:**
- User lacks permissions to access the endpoint.
- Role-based access control (RBAC) misconfiguration.

**Debugging Steps:**
1. **Check User Roles**
   - Log the user’s role and requested permissions:
     ```javascript
     console.log(`User ${req.user.id} (Role: ${req.user.role}) tried to access ${req.path}`);
     ```
   - Verify the role is correctly assigned in the database.

2. **Policy Engine Logs**
   - If using policy-based authorization (e.g., Casbin), check logs:
     ```bash
     grep "deny" /var/log/casbin.log
     ```

3. **Frontend Audit**
   - Ensure the frontend doesn’t send unauthorized requests (e.g., bypassing auth checks).

---

#### **4. 404 Not Found – Endpoint Missing**
**Symptoms:**
- Endpoint does not exist or is misconfigured.
- Routing table errors.

**Debugging Steps:**
1. **Verify API Gateway/Routing**
   - Check if the route is defined in the server (Express, FastAPI, etc.):
     ```javascript
     // Express route check
     app.get('/api/v1/users/:id', (req, res) => { ... });
     ```
   - For API gateways (Kong, NGINX), inspect the route configuration:
     ```nginx
     location /api/v1/users {
       proxy_pass http://backend;
     }
     ```

2. **Log Route Requests**
   - Log incoming requests to identify mismatches:
     ```javascript
     app.use((req, res, next) => {
       console.log(`Request to path: ${req.path}`);
       next();
     });
     ```

3. **Client-Side URL Check**
   - Ensure the frontend constructs the correct URL (e.g., `/users` vs. `/api/users`).

---

### **B. HTTP 5xx Errors (Server-Side Failures)**

#### **1. 500 Internal Server Error – Unhandled Exceptions**
**Symptoms:**
- Generic server error with no details.
- Application crashes silently.

**Debugging Steps:**
1. **Review Server Logs**
   - Check logs for stack traces:
     ```bash
     tail -f /var/log/app.log
     ```
   - Example error log:
     ```
     [2024-02-20T12:00:00] [ERROR] TypeError: Cannot read property 'id' of null at UserController.getUser
     ```

2. **Add Comprehensive Error Handling**
   - Wrap database/third-party calls in try-catch:
     ```javascript
     try {
       const user = await User.findById(req.params.id);
       if (!user) throw new Error("User not found");
       res.json(user);
     } catch (err) {
       console.error(`Error fetching user: ${err.stack}`);
       res.status(500).json({ error: "Internal server error" });
     }
     ```

3. **Graceful Degradation**
   - Return meaningful errors without exposing sensitive details:
     ```javascript
     res.status(500).json({
       error: "An unexpected error occurred",
       code: "INTERNAL_ERROR"
     });
     ```

---

#### **2. 502 Bad Gateway – Upstream Service Failure**
**Symptoms:**
- API acts as a proxy to another service (e.g., database, payment gateway).
- Upstream service returns an error or times out.

**Debugging Steps:**
1. **Inspect Proxy Logs**
   - Check if the upstream service is reachable:
     ```bash
     curl -v http://db-service:5432/status
     ```
   - For NGINX, check proxy errors:
     ```nginx
     error_log /var/log/nginx/error.log;
     ```

2. **Circuit Breaker Patterns**
   - Use libraries like `opossum` (Node.js) or `Resilience4j` (Java) to handle failures:
     ```javascript
     // Example with Opossum
     const { CircuitBreaker } = require('opossum');
     const cb = new CircuitBreaker(async (userId) => {
       return await db.query(`SELECT * FROM users WHERE id = ?`, [userId]);
     }, { timeout: 5000 });
     try {
       const user = await cb.fire(req.params.id);
       res.json(user);
     } catch (err) {
       res.status(503).json({ error: "Service temporarily unavailable" });
     }
     ```

3. **Retry Logic with Jitter**
   - Implement exponential backoff retries:
     ```javascript
     const retry = require('async-retry');
     await retry(
       async () => {
         const res = await axios.get('https://upstream-service');
         if (res.status !== 200) throw new Error("Failed");
       },
       { retries: 3, minTimeout: 1000 }
     );
     ```

---

#### **3. 503 Service Unavailable – Overloaded Server**
**Symptoms:**
- High CPU/memory usage.
- Database connections exhausted.

**Debugging Steps:**
1. **Monitor System Metrics**
   - Check CPU, memory, and disk usage:
     ```bash
     top -c
     free -h
     ```
   - For containers, use `docker stats` or Prometheus/Grafana.

2. **Optimize Queries**
   - Slow queries cause timeouts. Use `EXPLAIN ANALYZE` (PostgreSQL):
     ```sql
     EXPLAIN ANALYZE SELECT * FROM users WHERE created_at > '2023-01-01';
     ```
   - Add indexes on frequently queried fields.

3. **Horizontal Scaling**
   - Deploy additional API instances behind a load balancer.
   - Use connection pooling (e.g., `pg-pool` for PostgreSQL).

4. **Graceful Degradation**
   - Return `503` instead of crashing:
     ```javascript
     if (req.cpuUsage > 0.9) {
       return res.status(503).json({ error: "Service busy" });
     }
     ```

---

#### **4. 504 Gateway Timeout – Request Takes Too Long**
**Symptoms:**
- Request hangs longer than the server’s timeout (default: 60s in Nginx).
- Database transactions block for too long.

**Debugging Steps:**
1. **Adjust Timeout Settings**
   - Increase timeout in the server or load balancer:
     ```nginx
     location / {
       proxy_read_timeout 300s;
       proxy_connect_timeout 300s;
     }
     ```

2. **Optimize Slow Queries**
   - Identify and fix long-running queries (see `503` section).
   - Use pagination to avoid fetching large datasets.

3. **Implement Async Processing**
   - Offload heavy tasks to a queue (e.g., RabbitMQ, SQS):
     ```javascript
     // Example with Bull (Node.js)
     const queue = new Queue(1, 'long-tasks');
     queue.add({ task: 'generate-report', userId: req.user.id });
     res.json({ taskId: queue.id });
     ```

---

### **C. Data Inconsistencies**

#### **1. Race Conditions (e.g., Double Booking)**
**Symptoms:**
- Two users reserve the same resource simultaneously.
- Database records updated by multiple transactions.

**Debugging Steps:**
1. **Use Optimistic Concurrency Control**
   - Add version stamps to records:
     ```sql
     CREATE TABLE bookings (
       id SERIAL PRIMARY KEY,
       user_id INT,
       resource_id INT,
       version INT DEFAULT 1
     );

     -- In application code:
     const booking = await Booking.findOne({ where: { id: req.params.id } });
     if (booking.version !== req.body.version) {
       throw new Error("Stale version");
     }
     await Booking.update({ version: booking.version + 1 }, { where: { id: req.params.id } });
     ```

2. **Pessimistic Locking (for critical operations)**
   - Use database locks (e.g., PostgreSQL `SELECT ... FOR UPDATE`):
     ```sql
     BEGIN;
     SELECT * FROM bookings WHERE id = 123 FOR UPDATE;
     -- Update logic here
     COMMIT;
     ```

---

#### **2. Missing or Duplicate Data**
**Symptoms:**
- API returns empty records when data exists.
- Duplicate records created on retry.

**Debugging Steps:**
1. **Audit Database Transactions**
   - Check for failed transactions in logs:
     ```sql
     SELECT * FROM pg_stat_statements ORDER BY calls DESC LIMIT 10;
     ```

2. **Idempotency Keys**
   - Ensure retries don’t create duplicates:
     ```javascript
     // Use a unique constraint or idempotency key
     const idempotencyKey = req.headers['idempotency-key'];
     if (!idempotencyKey) return res.status(400).send("Missing idempotency key");
     const existing = await IdempotencyKey.findOne({ where: { key: idempotencyKey } });
     if (existing) return res.status(200).json("Already processed");
     await IdempotencyKey.create({ key: idempotencyKey });
     // Proceed with the request
     ```

---

## **3. Debugging Tools and Techniques**

### **A. Logging and Monitoring**
1. **Structured Logging**
   - Use formats like JSON for easy parsing:
     ```javascript
     console.log({
       level: "ERROR",
       message: "User not found",
       userId: req.params.id,
       timestamp: new Date().toISOString()
     });
     ```
   - Tools: `winston`, `pino`, `ELK Stack`.

2. **Distributed Tracing**
   - Trace requests across microservices using OpenTelemetry or Jaeger:
     ```javascript
     const { trace } = require('@opentelemetry/api');
     const span = trace.getActiveSpan() || trace.startSpan('api-request');
     try {
       // Business logic
       span.addEvent('database-query');
     } finally {
       span.end();
     }
     ```

3. **Error Tracking**
   - Send errors to Sentry or Datadog:
     ```javascript
     import * as Sentry from '@sentry/node';
     Sentry.init({ dsn: 'YOUR_DSN' });
     try { ... } catch (err) { Sentry.captureException(err); }
     ```

---

### **B. API Testing Tools**
1. **Postman/Newman**
   - Test endpoints with assertions:
     ```json
     // Postman collection example
     {
       "request": {
         "method": "POST",
         "url": "http://api.example.com/users",
         "body": { "name": "Alice" }
       },
       "assertions": [
         { "test": "pm.response.code === 201" }
       ]
     }
     ```

2. **Automated Testing**
   - Write unit/integration tests with `Jest`, `Pytest`, or `Supertest`:
     ```javascript
     // Example with Supertest
     const request = require('supertest');
     describe('GET /users/:id', () => {
       it('returns user data', async () => {
         const res = await request(app).get('/users/1');
         expect(res.status).toBe(200);
         expect(res.body).toHaveProperty('id', 1);
       });
     });
     ```

3. **Load Testing**
   - Use `k6` or `Locust` to simulate traffic:
     ```javascript
     // k6 script
     import http from 'k6/http';
     export default function () {
       http.get('https://api.example.com/health');
     }
     ```

---

### **C. Network Debugging**
1. **Packet Capture**
   - Use `tcpdump` or Wireshark to inspect traffic:
     ```bash
     tcpdump -i eth0 -w capture.pcap port 8080
     ```

2. **Latency Analysis**
   - Check DNS, TCP, and application latency with `curl -v`:
     ```bash
     curl -v -o /dev/null https://api.example.com/users
     ```

3. **API Mocking**
   - Mock external APIs with `msw` (Mock Service Worker):
     ```javascript
     import { setupWorker, rest } from 'msw';
     const worker = setupWorker(
       rest.get('https