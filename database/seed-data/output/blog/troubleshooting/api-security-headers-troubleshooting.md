# **Debugging HTTP Security Headers for APIs: A Troubleshooting Guide**

This guide helps backend engineers diagnose and resolve security header misconfigurations in APIs. Secure headers prevent XSS, clickjacking, MIME-sniffing, and other attacks.

---

## **1. Symptom Checklist**
Check if your API exhibits any of these issues:

✅ **Security audit failures** (OWASP ZAP, Burp Suite, Nessus)
✅ **XSS vulnerabilities** (malicious scripts executing in browser)
✅ **Clickjacking** (iframes hiding UI, forcing unintended actions)
✅ **MIME-sniffing attacks** (server allowing unsafe responses)
✅ **Missing headers** (`Content-Security-Policy`, `X-Content-Type-Options`, etc.)
✅ **Headers not enforcing strict policies** (e.g., `Referrer-Policy` too permissive)

---

## **2. Common Issues & Fixes**

### **Issue 1: Missing `Content-Security-Policy (CSP)`**
**Symptom:** XSS or data injection vulnerabilities.

**Fix:**
```http
# Example CSP for an API (strict but flexible)
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://trusted.cdn.com;
  font-src 'self';
  img-src 'self' data:;
  object-src 'none';
  frame-ancestors 'none';  # Prevent clickjacking
```
**Debugging Steps:**
- Test with **Browser DevTools → Security → CSP Violations**.
- Use **Report-Only Mode** (`Content-Security-Policy-Report-Only`) to log violations without blocking.

### **Issue 2: Weak `Referrer-Policy`**
**Symptom:** Sensitive API data leaked in referrer headers.

**Fix:**
```http
Referrer-Policy: strict-origin-when-cross-origin
```
(Or `no-referrer-when-downgrade` for balanced security.)

**Debugging Steps:**
- Check requests in **DevTools → Network → Headers** for unexpected `Referer` values.

### **Issue 3: Missing `X-Content-Type-Options: nosniff`**
**Symptom:** MIME-sniffing attacks (e.g., forcing `.json` responses as HTML).

**Fix:**
Ensure headers are set in middleware (e.g., Express, Flask):
```javascript
// Node.js (Express)
app.use((req, res, next) => {
  res.set('X-Content-Type-Options', 'nosniff');
  next();
});
```
**Debugging Steps:**
- Test with `curl -I <API_URL>` to verify headers.

### **Issue 4: Missing `X-Frame-Options: DENY` (Clickjacking)**
**Symptom:** API responses embeddable in iframes.

**Fix:**
```http
X-Frame-Options: DENY
```
**Alternative (modern):**
```http
Content-Security-Policy: frame-ancestors 'none';
```
**Debugging Steps:**
- Try embedding the API in an iframe—if it loads, headers are missing.

### **Issue 5: `Strict-Transport-Security (HSTS)` Not Enforced**
**Symptom:** Mixed content warnings or downgrade attacks.

**Fix:**
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
**Debugging Steps:**
- Check headers with **`curl -I https://<API_URL>`**.
- Test downgrade attempts (e.g., accessing via `http://`).

---

## **3. Debugging Tools & Techniques**

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| **Browser DevTools (Network Tab)** | Inspect response headers. | Right-click → "Copy as cURL" |
| **`curl -I`** | Fetch headers without body. | `curl -I https://api.example.com` |
| **OWASP ZAP** | Automated security scans. | `zap-baseline.py -t https://api.example.com` |
| **SecurityHeaders.com** | Online header check. | [https://securityheaders.com](https://securityheaders.com) |
| **Nessus/OpenVAS** | Penetration testing. | Scan for missing headers. |

**Manual Checks:**
- Verify headers in **Cloudflare/WAF logs** (if applicable).
- Use **Postman → Headers** to inspect API responses.

---

## **4. Prevention Strategies**

### **A. Enforce Headers in Middleware**
- **Express.js (Node.js):**
  ```javascript
  const helmet = require('helmet');
  app.use(helmet());
  ```
- **Flask (Python):**
  ```python
  from flask_talisman import Talisman
  Talisman(app, content_security_policy={'default-src': "'self'"})
  ```
- **Nginx:**
  ```nginx
  add_header X-Content-Type-Options nosniff;
  add_header Referrer-Policy strict-origin-when-cross-origin;
  ```

### **B. Automated Scanning**
- Integrate **OWASP Dependency-Check** or **GitHub Actions** to scan headers.
- Example workflow:
  ```yaml
  - name: Security Headers Scan
    run: npx securityheaders.com --url https://api.example.com
  ```

### **C. Use Security Frameworks**
- **Helmet.js** (Node) – Auto-injects security headers.
- **CSRF-Protection** – Mitigate CSRF via `X-XSRF-TOKEN`.

### **D. Testing Strategies**
- **Fuzz Testing:** Try injecting malicious payloads (e.g., `<script>alert(1)</script>`).
- **API Gateway Rules:** Enforce headers at the gateway (AWS API Gateway, Kong).

---

## **5. Final Validation Checklist**
✔ **All required headers present?** (`CSP`, `Referrer-Policy`, `X-Frame-Options`, etc.)
✔ **Headers enforce strict policies?** (No `*` wildcards in CSP.)
✔ **HSTS properly configured?** (Preload if possible.)
✔ **No mixed content warnings?** (Test via browser console.)
✔ **Penetration test passed?** (Scan with ZAP/Nessus.)

---
**Conclusion:** Missing security headers are often misconfigurations. Use automated tools, middleware, and strict policies to enforce protections. If issues persist, check infrastructure (CDN, load balancers) for header stripping.