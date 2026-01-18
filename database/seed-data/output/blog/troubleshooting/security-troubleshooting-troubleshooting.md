# **Debugging Security Troubleshooting: A Practical Guide**
*For Senior Backend Engineers*

---

## **Introduction**
Security issues can manifest in subtle ways—performance degradation, unexpected rejections, or silent data breaches. This guide focuses on **quick resolution** of common security-related backend problems, emphasizing **practical debugging** and **prevention strategies**.

---

## **1. Symptom Checklist**
Check for these signs to identify security-related issues:

| **Symptom**                     | **Possible Cause**                          |
|---------------------------------|--------------------------------------------|
| Unexpected `403 Forbidden`      | Authentication/Authorization failure       |
| High latency in API responses   | Rate limiting, DDoS protection in action   |
| Unauthorized access to sensitive endpoints | Misconfigured CORS, RBAC, or JWT validation |
| Database queries leaking data   | SQL injection or improper ORM sanitization |
| Unexpected API key revocations | Security key rotation or blacklisting      |
| Slow logins / failed authentications | Credential stuffing attacks or lockouts    |
| Unusual API traffic patterns    | Bot/scraper detection or abuse mitigation  |
| Unexpected `5xx` errors         | Backend security middleware (e.g., WAF) blocking requests |

---

## **2. Common Issues & Fixes**

### **Issue 1: Authentication Failures (401/403)**
**Symptoms:**
- API returns `401 Unauthorized` or `403 Forbidden`.
- Logs show JWT validation errors or session mismatches.

**Root Causes:**
- Expired tokens
- Incorrect token signing/verification
- Race conditions in token generation

**Quick Fixes:**

#### **A. Check JWT Validation (Node.js/Express Example)**
```javascript
const jwt = require('jsonwebtoken');

// Ensure secret key is correct and not exposed
app.use((req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send('No token provided');

  jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
    if (err) {
      console.error('JWT Validation Error:', err.message);
      return res.status(403).send('Forbidden');
    }
    req.user = decoded;
    next();
  });
});
```
**Debugging Steps:**
1. Verify `JWT_SECRET` is in environment variables, not hardcoded.
2. Check token expiration (`iat`, `exp` claims).
3. Ensure `alg: HS256` matches your implementation.

---

#### **B. Session Fixation Attack (Express-Session Example)**
```javascript
const { v4: uuidv4 } = require('uuid');
const session = require('express-session');

app.use(session({
  secret: uuidv4(), // Rotate this in production
  resave: false,
  saveUninitialized: false,
}));
```
**Debugging Steps:**
- Check if `session.secret` is unique and rotated regularly.
- Ensure `express-session` middleware is placed **before** auth checks.

---

### **Issue 2: Rate Limiting Blocking Legitimate Users**
**Symptoms:**
- API suddenly returns `429 Too Many Requests`.
- Logs show unexpected IP-based blocking.

**Root Causes:**
- Misconfigured rate limits (e.g., too low threshold).
- IP reputation services (e.g., Cloudflare) flagging valid traffic.

**Quick Fixes:**

#### **A. Adjust Rate Limiting (Express-Rate-Limit)**
```javascript
const rateLimit = require('express-rate-limit');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per window
  message: 'Too many requests, try again later.',
  standardHeaders: true,
});

app.use(limiter);
```
**Debugging Steps:**
1. Check `max` and `windowMs` values in production.
2. Use **user-based (not IP-based) rate limiting** for APIs needing flexibility.
3. Test with `curl` to simulate traffic:
   ```bash
   for i in {1..101}; do curl -v http://localhost:3000/api/endpoint; done
   ```

---

#### **B. Whitelist Internal Traffic (Cloudflare Workaround)**
```javascript
// In Cloudflare WAF rules, allow trusted IPs:
// "IP matches `192.168.1.0/24` OR `10.0.0.0/8`" → Allow
```

---

### **Issue 3: SQL Injection Vulnerabilities**
**Symptoms:**
- Database query errors with suspicious inputs.
- Unexpected data leaks (e.g., `UNION SELECT` in logs).

**Root Causes:**
- Raw SQL queries without parameterization.
- Poorly sanitized user inputs.

**Quick Fixes:**

#### **A. Use Parameterized Queries (Sequelize Example)**
```javascript
const { DataTypes } = require('sequelize');
const { sequelize } = require('./db');

const User = sequelize.define('User', {
  name: DataTypes.STRING,
  email: DataTypes.STRING,
});

// Safe: Inputs are escaped automatically
const user = await User.findOne({ where: { email: userInputEmail } });
```
**Debugging Steps:**
1. **Never** use `query.raw('SELECT * FROM users WHERE name = "' + name + '"')`.
2. For raw SQL, use **prepared statements**:
   ```javascript
   const [rows] = await pool.execute('SELECT * FROM users WHERE id = ?', [id]);
   ```

---

#### **B. Log Suspicious Queries**
```javascript
app.use((req, res, next) => {
  if (req.path.startsWith('/api/debug')) {
    console.warn('Debug Query:', req.query);
  }
  next();
});
```

---

### **Issue 4: CORS Misconfigurations**
**Symptoms:**
- Frontend fails with `No 'Access-Control-Allow-Origin'` header.
- Mixed-content errors (HTTP → HTTPS).

**Root Causes:**
- Missing or incorrect `Access-Control-Allow-Origin`.
- Credential flags not set for cookies/auth.

**Quick Fixes:**

#### **A. Enable CORS (Express Example)**
```javascript
const cors = require('cors');

app.use(cors({
  origin: ['https://yourfrontend.com', 'http://localhost:3000'],
  credentials: true, // Required for cookies/auth
}));
```
**Debugging Steps:**
1. Verify `origin` matches the frontend domain.
2. For development, allow `*` temporarily:
   ```javascript
   app.use(cors({ origin: '*' }));
   ```
3. Check headers in browser DevTools (`Network` tab → click request → `Response Headers`).

---

#### **B. Handle Preflight OPTIONS Requests**
```javascript
app.options('*', cors()); // Handle OPTIONS for preflight
```

---

### **Issue 5: Security Headers Missing**
**Symptoms:**
- Browser security warnings (e.g., "Your connection is not private").
- Missing `Content-Security-Policy` or `X-Content-Type-Options`.

**Root Causes:**
- Missing `helmet.js` or raw Express middleware.
- Incorrect `Strict-Transport-Security` headers.

**Quick Fixes:**

#### **A. Enable Security Headers (Helmet.js)**
```javascript
const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"], // Adjust for CDNs
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true }, // Enforce HTTPS
}));
```
**Debugging Steps:**
1. Verify headers in browser DevTools (`Security` tab).
2. Test with [SecurityHeaders.com](https://securityheaders.com/).

---

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**               | **Use Case**                          | **Example Command**                     |
|-----------------------------------|---------------------------------------|------------------------------------------|
| **JWT Debugging**                 | Validate tokens                      | `openssl dgst -sha256 -hmac "secret" -hex` |
| **Burp Suite / OWASP ZAP**        | Scan for SQLi/XSS                     | Run passive scan on `/api/endpoint`       |
| **`fail2ban`**                    | Block brute-force attackers           | Check logs: `grep "sshd" /var/log/auth.log` |
| **`ngrep` / `tcpdump`**           | Inspect network traffic               | `ngrep -d any port 8080`                 |
| **`strace`**                      | Debug system calls (e.g., file access)| `strace -e trace=file -p <PID>`           |
| **Postman / cURL**                | Test API endpoints                    | `curl -v -H "Authorization: Bearer $TOKEN" https://api.example.com` |
| **AWS WAF / Cloudflare Logging**  | Analyze blocked requests             | Check `AWS CloudTrail` or CF dashboard   |

---

### **Key Debugging Commands**
| **Scenario**               | **Command**                          |
|----------------------------|---------------------------------------|
| Check open ports           | `netstat -tulnp`                      |
| Inspect HTTP headers       | `curl -v https://api.example.com`     |
| Test SQL injection         | `curl -X POST -d "' OR '1'='1"`        |
| Check rate limit logs      | `grep "rate limit" /var/log/nginx`    |
| Validate JWT manually      | `jwt.io` (paste token)                |

---

## **4. Prevention Strategies**
| **Risk**                          | **Mitigation**                          | **Tools**                          |
|-----------------------------------|-----------------------------------------|------------------------------------|
| Brute-force attacks               | Rate limiting + 2FA                    | `express-rate-limit`, `aws-waf`    |
| Data breaches (SQLi)              | Parameterized queries + input sanitization | ORMs (`Sequelize`, `TypeORM`)      |
| Token leaks                       | Short-lived tokens + refresh tokens      | `jsonwebtoken` + `passport-httponly` |
| API abuse                         | Cloudflare / AWS Shield                 | `Cloudflare Enterprise`             |
| Misconfigured CORS                | Strict `origin` + `credentials: true`  | `cors` middleware                   |
| Missing security headers          | Helmet.js + CSP                          | `helmet.js`                         |

---

### **Checklist Before Production**
1. **Security Headers:**
   - ✅ `Content-Security-Policy` set
   - ✅ `Strict-Transport-Security` enabled
   - ✅ `X-XSS-Protection` present

2. **Authentication:**
   - ✅ JWT/Session secrets rotated
   - ✅ `httpOnly`, `Secure` cookies enforced
   - ✅ Rate limits on `/login` endpoints

3. **API Security:**
   - ✅ CORS restricted to trusted domains
   - ✅ Input validation (e.g., `express-validator`)
   - ✅ Logging for failed auth attempts

4. **Database:**
   - ✅ No raw SQL queries in production
   - ✅ Regular `GRANT`/`REVOKE` audits

5. **Monitoring:**
   - ✅ Fail2ban for SSH/API brute force
   - ✅ Cloudflare / AWS WAF for DDoS
   - ✅ Log analysis for unusual traffic

---

## **Conclusion**
Security debugging requires **methodical testing** and **automated safeguards**. Focus on:
1. **Quick wins** (CORS, rate limiting, JWT validation).
2. **Proactive monitoring** (fail2ban, WAF, logging).
3. **Prevention** (parameterized queries, security headers, secrets rotation).

**Final Tip:** Always **test security changes in staging** before deploying to production.

---
**Need deeper analysis?** Use tools like:
- [OWASP ZAP](https://www.zaproxy.org/) (automated scanning)
- [Lynis](https://cisofy.com/lynis/) (system hardening)
- [Chaos Monkey](https://github.com/Netflix/chaosmonkey) (fault injection testing)