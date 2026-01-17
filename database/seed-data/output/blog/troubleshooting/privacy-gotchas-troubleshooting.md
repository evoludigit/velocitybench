# **Debugging Privacy Gotchas: A Troubleshooting Guide**

Privacy Gotchas refer to subtle or overlooked security and privacy issues in applications, APIs, or systems that expose sensitive data unintentionally. These can occur due to misconfigured permissions, insecure data handling, logging leaks, or improper sanitization. This guide provides a structured approach to identifying, diagnosing, and resolving privacy-related issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, confirm the presence of these symptoms:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| **Exposed API Keys** | API keys, tokens, or credentials appear in:
  - Log files
  - Browser cache
  - Network requests (curl, Postman) | Misconfigured `traces`, `debug` output, or unsecured endpoints. |
| **Sensitive Data in Logs** | Personal data (PII), passwords, or tokens logged in:
  - Server-side logs (`stdout`, `stderr`)
  - Client-side console logs (`console.log`) | Unsanitized logging, debug statements in production. |
| **Unintended Data Exposure** | End users receive:
  - Other users' data (e.g., `SELECT * FROM users` without restrictions)
  - Sensitive metadata (e.g., `X-Powered-By` header leaks stack traces) | Loose database queries, CSP misconfigurations, or verbose error handling. |
| **CSRF or Session Hijacking** | Users’ sessions are stolen due to:
  - Missing `SameSite` cookies
  - Lack of CSRF tokens
  - Weak token generation | Insecure cookie settings, missing security headers. |
| **Data Leaks via Endpoints** | Developers expose:
  - Admin panels (`/admin`) without authentication
  - Debug pages (`/debug`) in production | Improper route security, missing middleware. |
| **Third-Party Tracking Leaks** | User data sent to analytics/unauthorized services without consent | Missing GDPR/CCPA compliance, improper SDK usage. |
| **DDoS via API Abuse** | High volume of requests from:
  - Scrapers hitting undocumented endpoints
  - Misconfigured rate-limiting | Missing rate limits, `OPTIONS` CORS preflight abuse. |

---

## **2. Common Issues and Fixes**

### **Issue 1: API Keys Exposed in Logs or Network Traffic**
**Symptoms:**
- API keys appear in logs (`curl -v`, `Postman` requests).
- Keys are printed in browser console or network tab.

**Root Cause:**
- Debug statements remain in production (`console.log`, `print` statements).
- Unencrypted secrets sent over HTTP.

**Fixes:**
#### **Backend Fix (Node.js/Express Example)**
```javascript
// ❌ BAD: Debug logs in production
if (process.env.NODE_ENV === 'development') {
  console.log('API Key:', process.env.DB_PASSWORD); // Leak in logs!
}

// ✅ GOOD: Sanitize logs
const sanitizedLogs = (data: any) => {
  const sensitiveKeys = ['password', 'key', 'secret', 'token'];
  return sanitizedLogs(data, sensitiveKeys);
};
console.log('DB Config:', sanitizedLogs(process.env));
```

#### **Frontend Fix (React Example)**
```javascript
// ❌ BAD: Hardcoded API key
const fetchData = async () => {
  const response = await fetch('https://api.example.com/data', {
    headers: { 'Authorization': 'Bearer DEVELOPER_KEY_HERE' } // Leaked in network tab!
  });
  // ...
};

// ✅ GOOD: Use environment variables
const fetchData = async () => {
  const response = await fetch('https://api.example.com/data', {
    headers: { 'Authorization': `Bearer ${process.env.REACT_APP_API_KEY}` }
  });
};
```
**Prevention:**
- Use `.env` files (exclude from Git via `.gitignore`).
- Enable **logging sanitization** (e.g., PII masking in logs).

---

### **Issue 2: Sensitive Data in Database Queries**
**Symptoms:**
- Users access other users’ data (e.g., `SELECT * FROM users`).
- Error messages leak schema details.

**Root Cause:**
- **No row-level security** in SQL.
- **Overly permissive queries** (e.g., `SELECT *`).

**Fixes:**
#### **PostgreSQL (Row-Level Security)**
```sql
-- ✅ Restrict queries to current user
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_access_policy ON users
  USING (user_id = current_setting('app.current_user_id')::uuid);
```

#### **Python (Django ORM)**
```python
# ❌ BAD: Query all users
User.objects.all()

# ✅ GOOD: Filter by user ID
User.objects.filter(id=request.user.id)
```

#### **Node.js (Prisma)**
```javascript
// ❌ BAD: No restrictions
const users = await prisma.user.findMany();

// ✅ GOOD: Use filters
const users = await prisma.user.findMany({
  where: { userId: req.user.id },
});
```
**Prevention:**
- Use **database-level permissions** (RLS).
- **Audit queries** with tools like `pgAudit` or `AWS RDS Performance Insights`.

---

### **Issue 3: Unintended Data via Error Handling**
**Symptoms:**
- Stack traces expose database schemas.
- Error messages include sensitive data.

**Root Cause:**
- **Verbose error handling** (e.g., `try-catch` logging full DB dumps).
- **Missing CSP headers** (allowing XSS).

**Fixes:**
#### **Backend (Express.js)**
```javascript
// ❌ BAD: Sensitive errors in production
app.use((err, req, res, next) => {
  console.error(err.stack); // Exposes DB connection strings!
  res.status(500).send(err.stack);
});

// ✅ GOOD: Sanitized errors
app.use((err, req, res, next) => {
  const sanitizedError = {
    message: err.message,
    status: 500,
    // Never expose DB details
  };
  res.status(500).json(sanitizedError);
});
```

#### **Frontend (React - CSP)**
```html
<!-- ✅ Add Content Security Policy (CSP) to prevent XSS -->
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net;">
```

**Prevention:**
- Use **error sanitization libraries** (e.g., `sentry-sanitize`).
- Enable **CSP headers** to block inline scripts.

---

### **Issue 4: CSRF or Session Hijacking**
**Symptoms:**
- Users logged out unexpectedly.
- Sessions stolen via cross-site attacks.

**Root Cause:**
- Missing `SameSite=Strict/Lax`.
- No CSRF tokens.
- Weak session tokens.

**Fixes:**
#### **Express.js (CSRF & Cookies)**
```javascript
// ✅ Secure cookies with CSRF protection
app.use(cors({
  origin: 'https://yourdomain.com',
  credentials: true,
}));

app.use(cors({ origin: 'https://yourdomain.com', credentials: true }));

// Set SameSite cookie policy
res.cookie('session', token, {
  httpOnly: true,
  secure: true,       // HTTPS only
  sameSite: 'strict', // Prevent CSRF
});
```

#### **React (CSRF Token)**
```javascript
// ✅ Include CSRF token in form submissions
fetch('/api/submit', {
  method: 'POST',
  headers: { 'X-CSRF-Token': localStorage.getItem('csrfToken') },
  body: JSON.stringify({ data })
});
```

**Prevention:**
- Use **CSRF protection middleware** (e.g., `csurf` for Express).
- Set **`SameSite=Strict`** for all cookies.

---

### **Issue 5: Debug Endpoints in Production**
**Symptoms:**
- `/debug`, `/health`, or `/admin` exposed.
- Stack traces visible in error pages.

**Root Cause:**
- Debug routes left in production.
- No middleware to block sensitive paths.

**Fixes:**
#### **Express.js (Route Protection)**
```javascript
// ✅ Block debug routes in production
const debugRoutes = require('./routes/debug');

if (process.env.NODE_ENV === 'development') {
  app.use('/debug', debugRoutes);
} else {
  app.all('/debug*', (req, res) => {
    res.status(403).send('Debug endpoint disabled in production');
  });
}
```

#### **Django (Admin Security)**
```python
# ✅ Restrict Django admin access
LOGIN_URL = '/accounts/login/'
ADMIN_URL = '/admin/'
MIDDLEWARE += [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]
```

**Prevention:**
- **Auto-remove debug routes** in production builds.
- Use **WAF rules** to block `/debug` in production.

---

## **3. Debugging Tools and Techniques**

| **Tool/Technique** | **Purpose** | **How to Use** |
|--------------------|------------|----------------|
| **`curl -v`** | Inspect HTTP headers/body | `curl -v https://api.example.com/endpoint` |
| **Postman/Insomnia** | Check API responses | Enable "Raw" to see unencoded responses. |
| **Browser DevTools (Network Tab)** | Check XSS, leaks | Look for `Authorization` headers in requests. |
| **`grep`/`awk` (Logs)** | Search for sensitive data | `grep -i "password\|key" /var/log/app.log` |
| **SQL Injection Tools (OWASP ZAP)** | Test DB vulnerabilities | Scan for `UNION SELECT` leaks. |
| **CSP Evaluator** | Validate CSP headers | Use [CSP Evaluator](https://csp-evaluator.withgoogle.com/). |
| **Sensitive Data Detection (GitHub Advanced Security)** | Scan repo for leaks | Upload code to GitHub CodeQL. |
| **OWASP ZAP** | Automated web app scanning | Scan for CSRF, XSS, and sensitive data exposure. |

**Debugging Workflow:**
1. **Check logs** (`grep` for API keys).
2. **Inspect network requests** (Postman/cURL).
3. **Audit database queries** (pgAudit, AWS RDS).
4. **Test for XSS/CSRF** (OWASP ZAP).
5. **Validate CSP headers** (DevTools → Security).

---

## **4. Prevention Strategies**

### **A. Development Best Practices**
✅ **Never log passwords/API keys** – Use masked logging.
✅ **Use environment variables** – `.env` + `.gitignore`.
✅ **Enable CSP headers** – Block inline scripts.
✅ **Sanitize errors** – Never expose DB schemas.
✅ **Test in staging** – Mimic production before deploy.

### **B. Infrastructure Hardening**
✅ **Restrict database access** – RLS (PostgreSQL), IAM (AWS).
✅ **Use HTTPS** – Prevent MITM attacks.
✅ **Rotate secrets frequently** – CI/CD should auto-rotate keys.
✅ **Enable WAF rules** – Block `/debug` in production.
✅ **Audit logs centrally** – Use Datadog, Splunk, or ELK.

### **C. Compliance Checks**
✅ **GDPR/CCPA compliance** – Right to erasure, data minimization.
✅ **PCI-DSS for payments** – Tokenize sensitive data.
✅ **OWASP Top 10** – Prevent common attacks (A01:A07).
✅ **Regular security audits** – Penetration testing, SAST/DAST.

### **D. Automated Security**
✅ **SAST/DAST tools** – Detect hardcoded secrets (GitHub Advanced Security).
✅ **Dependency scanning** – Check for vulnerable npm packages (`npm audit`).
✅ **CI/CD security gates** – Block deployments with secrets.

---

## **Final Checklist for Privacy Gotchas**
| **Area** | **Action Items** |
|----------|----------------|
| **Logging** | Mask PII, exclude secrets. |
| **APIs** | Rate limiting, key rotation. |
| **Database** | Row-level security, no `SELECT *`. |
| **Frontend** | CSP, no `console.log` in prod. |
| **Cookies** | `SameSite=Strict`, `HttpOnly`. |
| **Error Handling** | Sanitized responses. |
| **Debug Endpoints** | Block in production. |
| **Third-Party SDKs** | Check for GDPR compliance. |

---
**Next Steps:**
1. **Scan your app** (OWASP ZAP, GitHub Security).
2. **Review logs** for sensitive data leaks.
3. **Rotate exposed secrets** immediately.
4. **Implement CSP & RLS** if missing.

By following this guide, you’ll systematically eliminate privacy gotchas and harden your system against common data leaks.