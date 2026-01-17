# **Debugging REST Setup: A Troubleshooting Guide**
*For Backend Engineers (Practical & Fast Resolution Focused)*

---

## **1. Overview**
This guide covers debugging common issues in **REST API setup**, including **server-side configuration, request/response handling, authentication, rate limiting, and performance bottlenecks**. We’ll focus on **practical troubleshooting**—minimizing fluff, maximizing efficiency.

---

## **2. Symptom Checklist**
Before diving into fixes, quickly verify these **symptoms** to narrow down issues:

| **Category**          | **Symptoms**                                                                 | **Likely Cause**                               |
|-----------------------|------------------------------------------------------------------------------|-------------------------------------------------|
| **Network/Connectivity** | Timeouts, CORS errors, DNS resolution fails, `5xx` errors                    | Proxy, firewall, DNS misconfiguration          |
| **Server-Side**       | `4xx` (bad request), `500` (server error), slow responses, crashes            | Missing middleware, unhandled exceptions       |
| **Authentication**    | `401/403` errors, JWT validation fails, session expired                      | Incorrect token, expired JWT, misconfigured auth |
| **Database**          | Queries timing out, `SQL syntax errors`, slow reads/writes                   | Connection pool exhaustion, index missing      |
| **Rate Limiting**     | `429` errors, sudden throttling, slow responses                             | Misconfigured rate limits, missing headers     |
| **Client-Side**       | Frontend reports `network:error`, `JSON.parse` failures, empty responses   | Incorrect payload, malformed headers           |
| **Performance**       | High latency, memory leaks, CPU spikes                                     | Inefficient queries, unoptimized code          |

**Quick Check:**
✅ **Is the issue client-side or server-side?**
✅ **Are logs (server & client) consistent?**
✅ **Does the problem occur in staging/production or locally?**

---

## **3. Common Issues & Fixes (Code Examples)**

### **A. Network & Connectivity Problems**
#### **Issue 1: CORS Errors (`Access-Control-Allow-Origin` missing)**
- **Symptom:**
  ```
  Access to fetch at 'https://api.example.com/data' from origin 'http://localhost:3000' has been blocked by CORS policy.
  ```
- **Fix (Node.js/Express):**
  ```javascript
  const express = require('express');
  const cors = require('cors');

  const app = express();

  // Allow all origins (dev only; restrict in production)
  app.use(cors());

  // OR explicitly allow specific domains
  app.use(cors({
    origin: ['http://localhost:3000', 'https://client.com']
  }));
  ```
  **Best Practice:**
  - Never use `'*'` in production. Use **WHITELISTED DOMAINS**.
  - If using **Nginx/Apache**, add headers in config:
    ```nginx
    add_header 'Access-Control-Allow-Origin' 'https://client.com';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
    ```

#### **Issue 2: Timeouts (`ETIMEDOUT`, `ECONNRESET`)**
- **Symptom:**
  - Client waits indefinitely, server logs no errors.
  - **Common in load-balanced environments.**
- **Fix (Node.js):**
  ```javascript
  // Increase timeout (e.g., for slow DB queries)
  app.use(express.json({ limit: '50mb' })); // Payload size
  app.use(express.urlencoded({ extended: true, limit: '50mb' }));

  // For HTTP requests (e.g., database calls)
  const axios = require('axios');
  axios.get('https://slow-db.com/api', { timeout: 10000 }); // 10s timeout
  ```
  **Backend Fix (Nginx):**
  ```nginx
  proxy_read_timeout 60s;
  proxy_connect_timeout 60s;
  ```

#### **Issue 3: DNS Resolution Fails**
- **Symptom:**
  - `dns_probe_finished_nxdomain` (browser), `ENOTFOUND` (Node.js).
- **Fix:**
  - Verify **hosts file** (`/etc/hosts` on Linux/Mac, `C:\Windows\System32\drivers\etc\hosts` on Windows).
  - Check **DNS server** (e.g., AWS Route 53, Cloudflare).
  - **Node.js workaround:**
    ```javascript
    const dns = require('dns');
    dns.setServers(['8.8.8.8', '1.1.1.1']); // Fallback to Google/Cloudflare DNS
    ```

---

### **B. Server-Side Errors**
#### **Issue 4: `404 Not Found` (Route Misconfiguration)**
- **Symptom:**
  - `GET /api/users` returns `404`.
- **Fix:**
  ```javascript
  // Express Router (check order matters!)
  app.use('/api', require('./routes/users'));
  app.use('/api', require('./routes/products')); // Wrong if users comes after products
  ```
  **Debugging Steps:**
  1. Run `app._router.stack.map(r => console.log(r.route.methods)).flat()` to list all routes.
  2. Verify **path matching** (e.g., `/users` vs `/api/users`).

#### **Issue 5: `500 Internal Server Error` (Unhandled Exception)**
- **Symptom:**
  - Server crashes silently or returns `500`.
- **Fix:**
  ```javascript
  // Add global error handler (Express)
  app.use((err, req, res, next) => {
    console.error('Error:', err.stack);
    res.status(500).json({ error: 'Internal Server Error' });
  });

  // Example: Database error
  const { Pool } = require('pg');
  const pool = new Pool();

  app.get('/data', async (req, res) => {
    try {
      const { rows } = await pool.query('SELECT * FROM users');
      res.json(rows);
    } catch (error) {
      console.error('DB Error:', error);
      res.status(500).json({ error: 'Database query failed' });
    }
  });
  ```
  **Best Practice:**
  - **Log errors with context** (e.g., request ID, user agent).
  - Use **structured logging** (e.g., `winston`, `pino`).

---

### **C. Authentication Issues**
#### **Issue 6: `401 Unauthorized` (Missing/JWT Token)**
- **Symptom:**
  - `/api/protected` returns `401`.
- **Fix (JWT Validation):**
  ```javascript
  const jwt = require('jsonwebtoken');

  app.use('/api', (req, res, next) => {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ error: 'No token' });

    jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
      if (err) return res.status(403).json({ error: 'Invalid token' });
      req.user = user;
      next();
    });
  });
  ```
  **Debugging:**
  - Verify `JWT_SECRET` is **not leaked** (check `.gitignore`).
  - Check token **expiry** (`iat`, `exp` claims).

#### **Issue 7: Session Timeout**
- **Symptom:**
  - `401` after **N minutes** of inactivity.
- **Fix (Redis + Express-Session):**
  ```javascript
  const session = require('express-session');
  const RedisStore = require('connect-redis')(session);

  app.use(session({
    secret: 'your-secret',
    store: new RedisStore({ client: redisClient }),
    saveUninitialized: false,
    cookie: { maxAge: 1000 * 60 * 60 * 24 } // 1 day
  }));
  ```
  **Debugging:**
  - Check Redis **TTL** for sessions.
  - Verify **session cookie** is sent in responses.

---

### **D. Database Problems**
#### **Issue 8: Slow Queries (`TIMEOUT` or `Query too large`)**
- **Symptom:**
  - `Query exceeded timeout` (PostgreSQL), or `504 Gateway Timeout`.
- **Fix:**
  ```javascript
  // Increase timeout (PostgreSQL)
  const pool = new Pool({
    connectionTimeoutMillis: 5000,
    max: 20,
    idleTimeoutMillis: 30000
  });

  // Optimize query (add index)
  await pool.query(`
    CREATE INDEX idx_users_email ON users(email);
  `);

  // Use pagination for large datasets
  app.get('/users', async (req, res) => {
    const { page = 1, limit = 10 } = req.query;
    const offset = (page - 1) * limit;
    const { rows } = await pool.query(
      'SELECT * FROM users LIMIT $1 OFFSET $2',
      [limit, offset]
    );
    res.json(rows);
  });
  ```

#### **Issue 9: Connection Pool Exhausted**
- **Symptom:**
  - `Pool exhausted` error, `ECONNRESET` from DB.
- **Fix:**
  ```javascript
  const pool = new Pool({
    max: 20, // Adjust based on DB capacity
    idleTimeoutMillis: 30000
  });
  ```
  **Best Practice:**
  - **Monitor pool usage** (Prometheus + Grafana).
  - **Reuse connections** (set `keepAlive: true` in PostgreSQL).

---

### **E. Rate Limiting Issues**
#### **Issue 10: `429 Too Many Requests` (Misconfigured Limits)**
- **Symptom:**
  - API slows down after **N requests/minute**.
- **Fix (Express-Rate-Limit):**
  ```javascript
  const rateLimit = require('express-rate-limit');

  const limiter = rateLimit({
    windowMs: 60 * 1000, // 1 minute
    max: 100, // limit each IP to 100 requests per window
    message: 'Too many requests from this IP, try again later'
  });

  app.use('/api', limiter);
  ```
  **Debugging:**
  - Check **IP whitelisting** (allow trusted IPs).
  - Use **fallback mechanisms** (e.g., retry-after header).

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**       | **Purpose**                                                                 | **Example Command/Usage**                     |
|--------------------------|-----------------------------------------------------------------------------|-----------------------------------------------|
| **Postman/Newman**       | Test API endpoints, check responses, logs.                                  | `newman run collection.json --reporters cli`    |
| **cURL**                 | Debug raw HTTP requests/responses.                                          | `curl -v -H "Authorization: Bearer token" ...` |
| **K6**                   | Load testing, identify bottlenecks.                                         | `k6 run script.js --vus 100 --duration 30s`    |
| **Strace (Linux)**       | Trace system calls (e.g., blocked I/O).                                     | `strace -e trace=file -p <PID>`                |
| **Redis Insight**        | Monitor Redis sessions/cache.                                               | Download from [RedisLabs](https://redis.com/) |
| **Prometheus + Grafana** | Track metrics (latency, errors, rate limits).                              | Deploy via Docker: `docker run prom/prometheus` |
| **Express Logger**       | Log HTTP requests/responses.                                                | `app.use(morgan('combined'));`                 |
| **Chrome DevTools**      | Inspect Network tab for failed requests.                                    | F12 → Network → Filter by XHR                  |

**Pro Tip:**
- **For slow APIs**, use **Chrome’s Performance tab** to profile.
- **For DB issues**, enable **PostgreSQL logging**:
  ```sql
  ALTER SYSTEM SET log_statement = 'all';
  ALTER SYSTEM SET log_min_duration_statement = '100ms';
  ```

---

## **5. Prevention Strategies**
### **A. Infrastructure**
- ✅ **Use a reverse proxy** (Nginx, Traefik) for:
  - Load balancing.
  - Rate limiting.
  - TLS termination.
- ✅ **Enable auto-scaling** (AWS ECS, Kubernetes).
- ✅ **Monitor with Prometheus + Alertmanager** for:
  - `5xx` errors.
  - High latency (`> 1s`).
  - Rate limit breaches.

### **B. Code Best Practices**
- ✅ **Validate all inputs** (use `express-validator`):
  ```javascript
  const { body, validationResult } = require('express-validator');

  app.post('/login',
    body('email').isEmail(),
    body('password').isLength({ min: 8 }),
    (req, res) => {
      const errors = validationResult(req);
      if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
      }
      // Proceed
    }
  );
  ```
- ✅ **Use connection pooling** (avoid `new Pool()` per request).
- ✅ **Cache frequently accessed data** (Redis, CDN):
  ```javascript
  const Redis = require('ioredis');
  const redis = new Redis();

  async function getCachedData(key) {
    const data = await redis.get(key);
    if (data) return JSON.parse(data);
    const freshData = await fetchFromDB();
    await redis.set(key, JSON.stringify(freshData), 'EX', 300); // 5min TTL
    return freshData;
  }
  ```
- ✅ **Implement circuit breakers** (e.g., `opossum` library) for DB calls.

### **C. Testing**
- ✅ **Unit Test Endpoints** (Jest + Supertest):
  ```javascript
  const request = require('supertest');
  const app = require('../app');

  describe('GET /api/users', () => {
    it('should return users', async () => {
      const res = await request(app)
        .get('/api/users')
        .expect('Content-Type', /json/)
        .expect(200);
      expect(res.body).toHaveLength(5);
    });
  });
  ```
- ✅ **Mock External Services** (Nock, Sinon) for integration tests.
- ✅ **Load Test with k6** before deployment:
  ```javascript
  import http from 'k6/http';

  export default function () {
    http.get('https://api.example.com/protected', {
      headers: { Authorization: 'Bearer valid-token' }
    });
  }
  ```
  Run with:
  ```bash
  k6 run --vus 100 --duration 30s script.js
  ```

### **D. Security**
- ✅ **Use HTTPS** (Let’s Encrypt for free certs).
- ✅ **Sanitize inputs** (prevent SQLi, XSS):
  ```javascript
  // Prevent SQL injection
  const { query } = req;
  const sanitizedQuery = { ...query, user_id: sanitizeUserId(query.user_id) };

  // Prevent XSS (express-sanitize)
  app.use(sanitizeBody());
  ```
- ✅ **Rotate secrets** (JWT, DB passwords) regularly.
- ✅ **Use `helmet` for security headers**:
  ```javascript
  const helmet = require('helmet');
  app.use(helmet());
  ```

---

## **6. Quick Resolution Checklist**
| **Step**               | **Action**                                                                 |
|------------------------|----------------------------------------------------------------------------|
| **1. Reproduce Locally** | Test in dev environment.                                                  |
| **2. Check Logs**      | Server logs (`/var/log/nginx/error.log`, `console.error`).               |
| **3. Validate Inputs** | Verify `req.body`, `req.query`, `req.headers`.                            |
| **4. Test Endpoint**   | Use `curl` or Postman to isolate the issue.                              |
| **5. Monitor DB**      | Check `pg_stat_activity` (PostgreSQL) for slow queries.                  |
| **6. Review Middleware** | Disable middleware one by one to find culprit.                          |
| **7. Update Dependencies** | Run `npm audit` or check for known vulnerabilities.                     |
| **8. Rollback Last Change** | Use Git to revert recent commits if issue is recent.                     |

---

## **7. Final Notes**
- **Most `500` errors** → **Unhandled exceptions** or **DB connection issues**.
- **Most `404`** → **Route misconfiguration** or **missing middleware**.
- **Most `429`** → **Misconfigured rate limiting**.
- **Slow APIs?** → **DB queries, missing indexes, or unoptimized code**.

**Quick Wins:**
1. **Add logging** (even temporary `console.log`).
2. **Check dependencies** (`npm ls express`).
3. **Test with minimal payload** (rule out malformed data).

---
**Happy debugging!** 🚀
*If stuck, share:*
- **Full error log** (redact secrets).
- **Repro steps** (cURL/command).
- **Environment** (Node.js version, DB, OS).