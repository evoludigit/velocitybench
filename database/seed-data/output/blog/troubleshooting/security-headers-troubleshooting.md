# **Debugging Security Headers (CSP, HSTS, etc.): A Troubleshooting Guide**

Security headers (Content Security Policy (CSP), HTTP Strict Transport Security (HSTS), XSS Protection, etc.) are critical for protecting applications against cross-site scripting (XSS), clickjacking, data injection, and protocol downgrade attacks. When misconfigured, they can cause functionality breakdowns, performance issues, or even render your application unusable.

This guide provides a structured approach to diagnosing and fixing common security header-related issues.

---

## **1. Symptom Checklist**
Check for these signs that security headers may be misconfigured:

### **Functionality Issues**
- [ ] Browser console errors like:
  - `Refused to connect to '...' because it violates the following Content Security Policy`
  - `Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure script 'http://...'`
  - `Refused to display '...' in a frame because it violates the X-Frame-Options policy`
- [ ] Broken interactive elements (e.g., forms, buttons, dynamic content)
- [ ] Missing or broken third-party scripts (e.g., analytics, ads, payment gateways)
- [ ] 403/429 errors when accessing certain endpoints

### **Performance & Reliability Issues**
- [ ] High latency or timeout errors when fetching external resources
- [ ] Random 500 errors due to improper header validation
- [ ] Slow page loads due to blocked scripts/styles

### **Scalability & Maintenance Challenges**
- [ ] Difficulty updating CSP rules without breaking the site
- [ ] Frequent security scans flagging misconfigurations
- [ ] Inconsistent header enforcement across environments (dev/stage/prod)

### **HSTS-Specific Symptoms**
- [ ] Users stuck in HTTP loops (redirected endlessly between HTTP/HTTPS)
- [ ] Browser warnings: "This page loaded an insecure SSL certificate"
- [ ] Mixed content warnings when accessing HTTPS pages

---

## **2. Common Issues & Fixes**

### **Issue 1: Content Security Policy (CSP) Blocking Scripts/Styles**
**Symptom:**
`Refused to connect to '...' because it violates the following Content Security Policy: ...`

**Root Cause:**
- CSP allows/blocks certain resources (scripts, styles, images) by domain or hash.
- A misconfigured `script-src`, `style-src`, or `connect-src` directive blocks critical assets.

**Debugging Steps:**
1. **Check the error message** – Identify which resource is blocked (e.g., `https://cdn.example.com/script.js`).
2. **Verify CSP headers** (using browser dev tools → Network tab → Response Headers):
   ```
   Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.example.com; style-src 'self' 'unsafe-inline'; img-src *;
   ```
3. **Update CSP to allow the missing resource**:
   ```http
   Content-Security-Policy: script-src 'self' https://cdn.example.com;
   ```
   - If unsure, use `script-src 'unsafe-inline' 'unsafe-eval'` (temporarily for debugging, then tighten later).

**Best Fix:**
- Use nonces (`'nonce-abc123'`) for dynamic scripts:
  ```html
  <script nonce="abc123">...</script>
  ```
- Use hashes for static scripts:
  ```http
  script-src 'self' 'sha256-ABC123...'; style-src 'self';
  ```

---

### **Issue 2: Mixed Content Warnings (HTTP in HTTPS Page)**
**Symptom:**
`Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure script 'http://...'`

**Root Cause:**
- A script or image is loaded via `http://` on an otherwise HTTPS page.

**Debugging Steps:**
1. **Inspect Network tab** in Chrome DevTools → Look for `http://` requests on an HTTPS page.
2. **Fix all hardcoded `http://` links** in:
   - HTML attributes (`<img src="http://...">`)
   - JavaScript (`fetch("http://...")`)
   - Server responses (check API endpoints)
3. **Force HTTPS redirects** in your server (Nginx/Apache example):
   ```nginx
   server {
       listen 80;
       server_name example.com;
       return 301 https://$host$request_uri;
   }
   ```

**Best Fix:**
- Use `Content-Security-Policy: upgrade-insecure-requests` to auto-upgrade HTTP to HTTPS.

---

### **Issue 3: HSTS Loops or Browser Cache Issues**
**Symptom:**
Users stuck in HTTP/HTTPS redirect loops or see "SSL certificate error."

**Root Cause:**
- Incorrect HSTS header (`Strict-Transport-Security`).
- Preload list misconfiguration.
- Cache retention too long (default is 1 year).

**Debugging Steps:**
1. **Check HSTS header** (must include `max-age`):
   ```
   Strict-Transport-Security: max-age=31536000; includeSubDomains
   ```
2. **Verify no `preload` directive** is accidentally breaking production traffic:
   ```
   Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
   ```
3. **Clear browser cache** (`chrome://net-internals/#hsts`) if testing changes.

**Best Fix:**
- Start with a short `max-age` (e.g., `300`) for testing.
- Deploy `preload` only after thorough testing:
  ```http
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  ```
  Then submit to [Google HSTS Preload List](https://hstspreload.org/).

---

### **Issue 4: X-Frame-Options Blocking Embeds**
**Symptom:**
`Refused to display '...' in a frame because it violates the X-Frame-Options policy.`

**Root Cause:**
- `X-Frame-Options: DENY` or `SAMEORIGIN` blocks embedding in iframes.

**Debugging Steps:**
1. **Check server headers**:
   ```
   X-Frame-Options: DENY
   ```
2. **If embedding is required**, relax the policy:
   ```http
   X-Frame-Options: ALLOW-FROM https://trusted-site.com
   ```
   Or use `Content-Security-Policy: frame-ancestors 'none'` (modern alternative).

**Best Fix:**
- Use `frame-ancestors` in CSP for finer control:
  ```http
  Content-Security-Policy: frame-ancestors 'self' https://trusted-site.com;
  ```

---

### **Issue 5: Referrer-Policy Blocking API Calls**
**Symptom:**
API calls fail with `403 Forbidden` due to `Referer` header filtering.

**Root Cause:**
`Referrer-Policy: no-referrer` or `origin` blocks certain API requests.

**Debugging Steps:**
1. **Check `Referrer-Policy` header**:
   ```http
   Referrer-Policy: no-referrer-when-downgrade
   ```
2. **Update to allow necessary requests**:
   ```http
   Referrer-Policy: origin-when-cross-origin
   ```

---

## **3. Debugging Tools & Techniques**

### **A. Browser DevTools**
- **Network Tab**: Inspect `Content-Security-Policy`, `Strict-Transport-Security`, etc.
- **Console Tab**: Look for CSP violations.
- **Security Tab**: Check mixed content warnings.

### **B. Online Tools**
- [SecurityHeaders.com](https://securityheaders.com/) – Check current headers vs. best practices.
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/) – Test CSP rules.
- [HSTS File](https://www.hstspreload.org/) – Submit your domain for preload.

### **C. Server-Side Tools**
- **Nginx**:
  ```nginx
  add_header Content-Security-Policy "default-src 'self'";  # Example
  ```
- **Apache**:
  ```apache
  Header set Content-Security-Policy "default-src 'self'"
  ```
- **Cloudflare**:
  - Enable headers in **Firewall → Security Headers**.

### **D. Logging & Monitoring**
- **Error Tracking**: Log CSP violations (e.g., Sentry, Datadog).
- **Synthetic Monitoring**: Test headers in staging before production.

---

## **4. Prevention Strategies**

### **A. Header Best Practices**
| Header | Recommended Value | Example |
|--------|-------------------|---------|
| **CSP** | Start permissive, then tighten | `default-src 'self'` → `script-src 'self' https://cdn.example.com` |
| **HSTS** | Short `max-age` first | `max-age=300` (5 mins) → `max-age=31536000` (1 year) |
| **X-Frame-Options** | `DENY` or `frame-ancestors` | `frame-ancestors 'none'` |
| **XSS-Protection** | Disabled (modern CSP handles XSS) | `X-XSS-Protection: 0` |
| **Referrer-Policy** | `no-referrer-when-downgrade` | Preserves referrer in HTTPS |

### **B. Development Workflow**
1. **Start Permissive, Then Tighten**:
   - Begin with broad rules, then narrow down.
   - Example:
     ```http
     Content-Security-Policy: script-src 'self' 'unsafe-inline'; style-src 'self';
     ```
2. **Test in Staging First**:
   - Use `Content-Security-Policy-Report-Only` to report violations without blocking:
     ```http
     Content-Security-Policy-Report-Only: default-src 'self'; report-uri /csp-report-endpoint
     ```
3. **Use Nonces/Hashes for Dynamic Content**:
   - Avoid `'unsafe-inline'` where possible.
4. **Automate Header Testing**:
   - Use tools like [SecurityHeaders.com](https://securityheaders.com/) in CI/CD.

### **C. Crisis Response Plan**
- **If CSP breaks production**:
  - Temporarily disable CSP in staging before production.
  - Use `Content-Security-Policy-Report-Only` to debug.
- **If HSTS causes loops**:
  - Remove HSTS header temporarily.
  - Clear browser cache (`chrome://net-internals/#hsts`).

---

## **5. Final Checklist**
Before deploying changes:
✅ [ ] Test CSP in `Report-Only` mode.
✅ [ ] Verify HSTS `max-age` is reasonable for testing.
✅ [ ] Check mixed content warnings in DevTools.
✅ [ ] Test third-party integrations (analytics, payments).
✅ [ ] Monitor for errors post-deployment.

---
### **Summary**
Security headers are powerful but fragile. **Start permissive, test thoroughly, and gradually tighten rules.** Use tools like DevTools, SecurityHeaders.com, and CSP Evaluator to validate changes. If something breaks, revert quickly and analyze logs.

For further reading:
- [MDN CSP Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [OWASP HSTS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html)