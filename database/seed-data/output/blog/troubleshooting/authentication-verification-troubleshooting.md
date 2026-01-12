# **Debugging Authentication Verification: A Troubleshooting Guide**
*For Backend Engineers*

Authors: [Your Name]
Last Updated: [Date]

---

## **Table of Contents**
1. [Introduction](#introduction)
2. [Symptom Checklist](#symptom-checklist)
3. [Common Issues & Fixes](#common-issues--fixes)
   - [3.1 Authentication Token Not Being Sent](#31-authentication-token-not-being-sent)
   - [3.2 Token Expiration or Refresh Issues](#32-token-expiration-or-refresh-issues)
   - [3.3 Token Validation Failing](#33-token-validation-failing)
   - [3.4 Session Management Problems](#34-session-management-problems)
   - [3.5 CSRF Tokens Missing or Incorrect](#35-csrf-tokens-missing-or-incorrect)
   - [3.6 Rate Limiting Blocking Valid Requests](#36-rate-limiting-blocking-valid-requests)
   - [3.7 Database-Side Auth Mismatch](#37-database-side-auth-mismatch)
4. [Debugging Tools & Techniques](#debugging-tools--techniques)
   - [4.1 Network Inspection](#41-network-inspection)
   - [4.2 Logging & Tracing](#42-logging--tracing)
   - [4.3 Unit & Integration Testing](#43-unit--integration-testing)
   - [4.4 Security Headers & Misconfigurations](#44-security-headers--misconfigurations)
5. [Prevention Strategies](#prevention-strategies)
6. [Conclusion](#conclusion)

---

## **1. Introduction**
Authentication Verification (AuthN/AuthZ) is a critical component in securing backend systems. Issues here can range from minor inconveniences (e.g., wrong credentials) to critical security breaches (e.g., token leaks, bypasses). This guide provides a systematic approach to diagnosing and resolving common authentication-related problems.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the issue with these diagnostic checks:

✅ **User-Reported Symptoms:**
- `"I can't log in"` → Credential mismatch, rate limiting, or service downtime
- `"Session expired unexpectedly"` → Token expiry, session cleanup, or backend misconfig
- `"API returns 403/401 for valid requests"` → Token validation failing, permissions issue, or JWT misconfig
- `"API works in Postman but not in production"` → CORS, headers, or environment-specific misconfig
- `"CSRF token validation failing"` → Incorrect token generation, missing headers, or form submissions
- `"Users stuck in refresh loop"` → Broken refresh token logic, DB inconsistency

✅ **Server-Side Indicators:**
- **Logs:** `invalid_token`, `token_expired`, `missing_credentials`, `rate_limited`
- **Monitoring Alerts:** Failed login attempts, high latency in auth endpoints
- **Error Codes:**
  - `401 Unauthorized` → Invalid/missing credentials or token
  - `403 Forbidden` → Valid auth but insufficient permissions
  - `400 Bad Request` → Malformed token, missing headers
  - `500 Internal Server Error` → Backend logic failure (e.g., DB query)

---

## **3. Common Issues & Fixes**

### **3.1 Authentication Token Not Being Sent**
**Symptoms:**
- `401 Unauthorized` on API requests (e.g., `/api/data`)
- Postman/DevTools shows missing `Authorization` header
- Works in Postman but fails in the app → header omission in frontend

**Root Causes:**
- Frontend not sending token (e.g., `fetch`/`axios` call missing header)
- Backend expects a different header format (e.g., `Bearer` vs. `Token`)
- Token stored incorrectly (e.g., localStorage vs. cookies)

**Fixes:**
#### **Frontend (React Example)**
```javascript
// ✅ Correct: Send token in Authorization header
const response = await axios.get('/api/data', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```
#### **Backend (Express.js)**
```javascript
const jwt = require('jsonwebtoken');
app.use((req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1]; // "Bearer <token>"
  if (!token) return res.status(401).send('Unauthorized');
  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) return res.status(403).send('Invalid token');
    req.user = user;
    next();
  });
});
```
**Debugging Tip:**
Inspect **Request Headers** in DevTools (Network tab) to confirm the `Authorization` header is sent.

---

### **3.2 Token Expiration or Refresh Issues**
**Symptoms:**
- `token_expired: JWT expired at ...` in logs
- Users forced to log in repeatedly
- Refresh token not returning a new access token

**Root Causes:**
- **Token TTL too short** (e.g., 5 mins vs. expected 1 hour)
- **Refresh token invalidated prematurely** (e.g., DB cleanup too aggressive)
- **Race condition in refresh flow** (e.g., user refreshes before token expires but DB deletes old token)

**Fixes:**
#### **Backend (JWT Setup)**
```javascript
// ✅ Configure JWT with reasonable TTLs
const accessTokenTTL = '1h';
const refreshTokenTTL = '7d';

const generateTokens = (user) => {
  const accessToken = jwt.sign({ userId: user.id }, process.env.JWT_SECRET, {
    expiresIn: accessTokenTTL
  });
  const refreshToken = jwt.sign({ userId: user.id }, process.env.REFRESH_SECRET, {
    expiresIn: refreshTokenTTL
  });
  return { accessToken, refreshToken };
};
```
#### **Refresh Token Logic (Express.js)**
```javascript
app.post('/refresh', (req, res) => {
  const { refreshToken } = req.body;
  if (!refreshToken) return res.status(401).send('No refresh token');

  jwt.verify(refreshToken, process.env.REFRESH_SECRET, (err, user) => {
    if (err) return res.status(403).send('Invalid refresh token');
    const newAccessToken = jwt.sign({ userId: user.userId }, process.env.JWT_SECRET, {
      expiresIn: '1h'
    });
    res.json({ accessToken: newAccessToken });
  });
});
```
**Debugging Tip:**
- Check token expiry in **JWT.io** decoder (paste the token).
- Add logging for `refresh` endpoint calls to verify token state.

---

### **3.3 Token Validation Failing**
**Symptoms:**
- `InvalidTokenError: jwt malformed` or `SignatureVerificationError`
- Works locally but fails in staging/prod
- Token signed with wrong algorithm (e.g., HS256 vs. RS256)

**Root Causes:**
- **Secret mismatch** (e.g., `JWT_SECRET` differs between environments)
- **Algorithm mismatch** (e.g., backend uses `HS256` but frontend sends `RS256`)
- **Token tampered with** (e.g., MITM attack, but unlikely in production)

**Fixes:**
#### **Verify Secret in Backend**
```javascript
// Ensure JWT_SECRET matches across environments
console.log('JWT_SECRET:', process.env.JWT_SECRET); // Should be same in all envs
```
#### **Check Algorithm**
```javascript
jwt.verify(token, secret, { algorithms: ['HS256'] }); // Explicitly set algorithm
```
**Debugging Tip:**
- Use `node` REPL to manually decode:
  ```bash
  node -e "const jwt = require('jsonwebtoken'); console.log(jwt.decode('token'));"
  ```
- Compare `alg` field in decoded token with backend config.

---

### **3.4 Session Management Problems**
**Symptoms:**
- Session persists after logout
- Multiple devices show same session (e.g., interactive auth)
- Logout fails silently

**Root Causes:**
- **No session cleanup** (e.g., no DB record deletion)
- **Race condition** (e.g., logout request lost)
- **Frontend not clearing tokens** (e.g., localStorage not wiped)

**Fixes:**
#### **Backend (Express-Session)**
```javascript
const session = require('express-session');
const MySQLStore = require('express-mysql-session')(session);

app.use(session({
  secret: 'secret',
  store: new MySQLStore({ /* DB config */ }),
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 24 * 60 * 60 * 1000 } // 1 day
}));

// ✅ Logout route
app.post('/logout', (req, res) => {
  req.session.destroy(err => {
    if (err) return res.status(500).send('Logout error');
    res.clearCookie('sessionID');
    res.send('Logged out');
  });
});
```
#### **Frontend (React)**
```javascript
// ✅ Clear token and session on logout
const handleLogout = () => {
  localStorage.removeItem('token');
  sessionStorage.removeItem('session');
  axios.post('/logout').then(() => window.location.href = '/login');
};
```
**Debugging Tip:**
- Check DB for lingering session records.
- Verify `setCookie` flags in `/logout` response.

---

### **3.5 CSRF Tokens Missing or Incorrect**
**Symptoms:**
- `CSRF token missing` errors on form submissions
- Works in Postman but fails in browser
- Token expires too quickly (e.g., every 5 mins)

**Root Causes:**
- **Token not generated** (e.g., middleware skipped)
- **Token not sent** (e.g., frontend missed `<input name="_csrf">`)
- **Token mismatch** (e.g., backend expects `X-CSRF-Token` but frontend sends `csrf-token`)

**Fixes:**
#### **Backend (Express)**
```javascript
const csrf = require('csurf');
const csrfProtection = csrf({ cookie: true });

app.use(csrfProtection);
// Middleware to expose token in response (for JavaScript)
app.use((req, res, next) => {
  if (req.csrfToken) res.locals.csrfToken = req.csrfToken;
  next();
});
```
#### **Frontend (HTML Form)**
```html
<!-- ✅ Include CSRF token in form -->
<form method="POST" action="/api/submit">
  <input type="hidden" name="_csrf" value="{{ csrfToken }}">
  <!-- Other fields -->
</form>
```
#### **React Example**
```javascript
// Fetch CSRF token on page load
const [csrfToken, setCsrfToken] = useState('');

useEffect(() => {
  fetch('/api/csrf')
    .then(res => res.json())
    .then(data => setCsrfToken(data.csrfToken));
}, []);

const submitForm = () => {
  fetch('/api/submit', {
    method: 'POST',
    headers: { 'X-CSRF-Token': csrfToken },
    // ...
  });
};
```
**Debugging Tip:**
- Use DevTools **Network** tab to confirm the CSRF token is sent in form data/headers.
- Check backend logs for `Invalid CSRF token` errors.

---

### **3.6 Rate Limiting Blocking Valid Requests**
**Symptoms:**
- `429 Too Many Requests` for legitimate users
- Works in Postman but fails in app
- Rate limit resets too aggressively (e.g., every 1 minute)

**Root Causes:**
- **IP-based rate limiting** (e.g., cloudflare without user identification)
- **Too aggressive limits** (e.g., 100 requests/minute for API)
- **Misconfigured window time** (e.g., sliding window vs. fixed window)

**Fixes:**
#### **Express Rate Limiter (User-Aware)**
```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP/user to 100 requests per windowMs
  keyGenerator: (req) => req.user?.id || req.ip, // Use user ID if available
  handler: (req, res) => res.status(429).json({ error: 'Too many requests' })
});

app.use('/api', limiter);
```
**Debugging Tip:**
- Check rate-limit logs for suspicious activity.
- Test with `curl` or Postman to confirm behavior.

---

### **3.7 Database-Side Auth Mismatch**
**Symptoms:**
- User logs in successfully but loses access later
- DB records don’t match JWT payload (e.g., `userId` mismatch)
- Soft-deleted users still authenticated

**Root Causes:**
- **JWT not updating user data** (e.g., email changes not reflected)
- **DB queries failing silently** (e.g., no error handling for deleted users)
- **Race condition** (e.g., user deletes account while token valid)

**Fixes:**
#### **Backend (User Validation)**
```javascript
// ✅ Verify JWT user exists in DB
const verifyUser = async (userId) => {
  const user = await User.findById(userId);
  if (!user || user.deletedAt) {
    throw new Error('User not found or deleted');
  }
  return user;
};

// Inside auth middleware
jwt.verify(token, secret, async (err, payload) => {
  if (err) return res.status(403).send('Invalid token');
  const user = await verifyUser(payload.userId);
  if (!user) return res.status(403).send('User no longer exists');
  req.user = user;
  next();
});
```
**Debugging Tip:**
- Query the DB directly (`SELECT * FROM users WHERE id = ?`) to verify records.
- Add logging for `verifyUser` calls.

---

## **4. Debugging Tools & Techniques**

### **4.1 Network Inspection**
- **DevTools (Chrome/Firefox):**
  - **Network tab:** Inspect headers, payloads, and responses.
  - **Application tab:** Check cookies, localStorage, sessionStorage.
- **Postman/curl:**
  ```bash
  curl -v -H "Authorization: Bearer <token>" https://api.example.com/data
  ```
- **Charles Proxy/Wireshark:**
  - Capture traffic to analyze raw HTTP requests.

### **4.2 Logging & Tracing**
**Backend Logging (Express.js):**
```javascript
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// Log auth events
app.post('/login', (req, res) => {
  console.log('Login attempt:', req.body.email);
  // ...
});
```
**Structured Logging (Winston/Pino):**
```javascript
const pino = require('pino');
const logger = pino({
  level: 'info',
  transport: {
    target: 'pino-destination',
    options: { destination: 1 } // Logs to stdout
  }
});

logger.info({ event: 'login', userId: 123 }, 'User logged in');
```
**Debugging Tip:**
- Use `process.env.NODE_ENV === 'development'` to enable detailed logging.
- Correlate logs with requests using `requestId` (e.g., `req.id = uuid()`).

### **4.3 Unit & Integration Testing**
**Test Authentication Flow:**
```javascript
// Jest + Supertest example
describe('Auth API', () => {
  it('should return 401 for missing credentials', async () => {
    const res = await request(app)
      .post('/login')
      .send({ email: '', password: '' });
    expect(res.status).toBe(401);
  });

  it('should refresh token on valid request', async () => {
    const loginRes = await request(app)
      .post('/login')
      .send({ email: 'user@example.com', password: 'pass123' });
    const { refreshToken } = loginRes.body;
    const refreshRes = await request(app)
      .post('/refresh')
      .send({ refreshToken });
    expect(refreshRes.status).toBe(200);
    expect(refreshRes.body).toHaveProperty('accessToken');
  });
});
```
**Debugging Tip:**
- Mock DB calls in unit tests to isolate auth logic.
- Use tools like `nock` to mock external APIs.

### **4.4 Security Headers & Misconfigurations**
**Check for Missing Headers:**
```bash
# Test with curl
curl -I https://yourdomain.com
```
**Common Headers:**
| Header               | Purpose                          | Example Value                     |
|----------------------|----------------------------------|-----------------------------------|
| `Strict-Transport-Security` | Enforce HTTPS                     | `max-age=63072000; includeSubDomains` |
| `Content-Security-Policy` | Mitigate XSS                     | `default-src 'self'`              |
| `X-Content-Type-Options` | Prevent MIME sniffing             | `nosniff`                         |
| `X-Frame-Options`    | Prevent clickjacking              | `DENY`                            |
**Fix Example (Express):**
```javascript
app.use((req, res, next) => {
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  next();
});
```

---

## **5. Prevention Strategies**

### **5.1 Secure Coding Practices**
- **Never store secrets in client-side code** (use environment variables).
- **Rotate secrets regularly** (e.g., `JWT_SECRET` every 3 months).
- **Use HTTPS everywhere** (enforce with `HSTS`).
- **Validate all inputs** (e.g., email format, password strength).

### **5.2 Infrastructure Hardening**
- **Rate limiting** at the load balancer/CDN (e.g., Cloudflare rate limiting).
- **Database backups** to prevent data loss (e.g., `pg_dump` for PostgreSQL).
- **Monitor failed auth attempts** (e.g., Elasticsearch + Kibana for logs).

### **5.3 Testing & Review**
- **Penetration testing** (e.g., OWASP ZAP) for auth endpoints.
- **Automated security scans