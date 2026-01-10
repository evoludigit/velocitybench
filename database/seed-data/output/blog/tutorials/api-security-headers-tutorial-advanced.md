```markdown
# **HTTP Security Headers for APIs: A Practical Guide to Defense in Depth**

APIs are the backbone of modern applications, yet they’re often overlooked when it comes to security. While authentication (OAuth, JWT) and authorization (RBAC) are critical, **HTTP security headers** provide a lightweight yet powerful way to harden your API against common attacks—**for free**.

Most browsers and clients default to insecure behaviors if no security headers are specified:
- **Cross-Site Scripting (XSS):** Scripts from malicious third-party domains can execute.
- **Clickjacking:** Your API responses can be embedded in invisible iframes to trick users into unintended actions.
- **MIME Sniffing:** Browsers may misinterpret content types, leading to file downloads instead of rendering pages.
- **HTTPS Downgrades:** Connections can be forced to HTTP, exposing sensitive data.
- **Referrer Leaks:** Sensitive API endpoints may leak in Referer headers.

Security headers like `Content-Security-Policy`, `Strict-Transport-Security`, and `X-Content-Type-Options` act as **defense-in-depth** controls. They’re **easy to implement**, **do not require code changes**, and **add minimal overhead**—yet they prevent catastrophic breaches.

In this guide, we’ll explore **real-world examples**, tradeoffs, and best practices for securing APIs with HTTP headers.

---

## **The Problem: When Headers Are Missing**

### **1. Cross-Site Scripting (XSS) Attacks**
Without `Content-Security-Policy`, a malicious script from `https://evil.com` can execute in your API responses:
```http
GET /api/profile HTTP/1.1
Host: myapi.example.com

Response:
Content-Type: text/html
<iframe src="https://evil.com/steal-cookies.js"></iframe>
```
The browser executes `steal-cookies.js`, leading to session hijacking.

### **2. Clickjacking (UI Hijacking)**
Without `X-Frame-Options` or `Frame-Options`, an attacker embeds your API in an invisible iframe:
```html
<iframe src="https://myapi.example.com/api/delete-account" style="display:none;"></iframe>
```
When the victim clicks elsewhere on the page, their account is deleted.

### **3. MIME Sniffing (Content-Type Confusion)**
A server sends `Content-Type: text/plain` but the browser guesses `text/html`. Instead of rendering JSON, it treats it as HTML, allowing script injection:
```http
Content-Type: text/plain; charset=utf-8
"{\"user\":\"admin\"}" <!-- Browser renders this as HTML -->
```

### **4. HTTPS Downgrade Attacks**
An attacker tricks a client into accepting an HTTP connection instead of HTTPS:
```http
Link: </api>; rel=alternate; https=off
```
This exposes sensitive data in transit.

### **5. Referrer Leaks**
Some APIs (like OAuth redirects) leak sensitive paths in Referer headers:
```http
GET /oauth/callback?token=jwtxyz HTTP/1.1
Referer: https://myapp.example.com/admin-dashboard
```
Attackers can hijack these tokens.

**Result:** Even with proper auth, poorly configured headers **compromise security**.

---

## **The Solution: Defense in Depth with HTTP Headers**

HTTP security headers are **not a replacement** for proper authentication/authorization, but they **enforce secure defaults** that prevent many attacks.

| **Issue**               | **Solution Header**               | **Effect**                                                                 |
|--------------------------|------------------------------------|----------------------------------------------------------------------------|
| XSS                      | `Content-Security-Policy` (CSP)   | Restricts script sources to trusted domains.                              |
| Clickjacking             | `X-Frame-Options` / `Frame-Options` | Blocks embedding in iframes.                                             |
| MIME Sniffing            | `X-Content-Type-Options: nosniff` | Prevents browser guessing of content types.                              |
| HTTPS Downgrade          | `Strict-Transport-Security` (HSTS) | Forces HTTPS and prevents protocol downgrades.                           |
| Referer Leaks            | `Referrer-Policy`                 | Controls how referrer info is sent.                                        |

**Tradeoff:** Some headers (like HSTS) require **careful deployment** (e.g., preloading lists). Others (like CSP) are **strict** and may break existing functionality if misconfigured.

---

## **Implementation Guide**

### **1. Choosing Your Headers**
Not all headers are needed for all APIs. Here’s a **recommended baseline** for RESTful APIs:

| **Header**               | **Value**                                                                 | **When to Use**                                                                 |
|--------------------------|---------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload`                        | Always (if using HTTPS).                                                       |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' https://trusted.cdn.com`          | If serving HTML/JavaScript.                                                    |
| `X-Content-Type-Options` | `nosniff`                                                                 | Always (prevents MIME sniffing).                                                |
| `X-Frame-Options`        | `DENY`                                                                   | If embedding is unsafe (e.g., `/api/admin`).                                  |
| `Referrer-Policy`        | `strict-origin-when-cross-origin`                                         | If exposing sensitive endpoints.                                             |
| `Permissions-Policy`     | `geolocation=(), microphone=()`                                           | Restricts modern browser features.                                            |

---

### **2. Applying Headers in Code**

#### **Option A: Middleware (Express.js)**
```javascript
const express = require('express');
const helmet = require('helmet');

const app = express();

// Enable security headers via middleware
app.use(helmet());

// OR: Custom CSP header (strict policy)
app.use((req, res, next) => {
  res.set({
    "Content-Security-Policy": `
      default-src 'self';
      script-src 'self' https://cdn.trusted.com;
      style-src 'self' 'unsafe-inline';
      font-src 'self';
      img-src 'self' data:;
    `
  });
  next();
});

app.listen(3000, () => console.log('Secure API running'));
```

#### **Option B: Nginx (Reverse Proxy)**
```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    # Force HTTPS (HSTS)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Prevent MIME sniffing
    add_header X-Content-Type-Options "nosniff" always;

    # Block embedding
    add_header X-Frame-Options "DENY" always;

    # CSP (example)
    add_header Content-Security-Policy "
      default-src 'self';
      script-src 'self' https://cdn.trusted.com;
    " always;
}
```

#### **Option C: Cloudflare (CDN)**
1. Go to **Security → Security Header**.
2. Add:
   ```
   Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
   Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.trusted.com
   ```
3. Deploy changes.

---

### **3. Testing Your Headers**
#### **Manual Check**
Use browser dev tools (**Network tab → Response headers**) to verify:
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
```

#### **Automated Tools**
- **[SecurityHeaders.com](https://securityheaders.com/)** – Grades your API.
- **[Mozilla Observatory](https://observatory.mozilla.org/)** – Detailed security report.
- **[OWASP Amass](https://github.com/OWASP/Amass)** – Scans for misconfigurations.

---

## **Common Mistakes to Avoid**

### **1. Overly Permissive CSP**
❌ Bad:
```http
Content-Security-Policy: default-src *
```
✅ Good:
```http
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.js.com
```
**Why?** Wildcards (`*`) defeat the purpose. CSP should be **strict by default**.

### **2. Skipping HSTS Preload**
❌ Bad:
```http
Strict-Transport-Security: max-age=604800
```
✅ Good:
```http
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```
**Why?** Preload ensures browsers enforce HTTPS even after your max-age expires.

### **3. Not Testing CSP Errors**
Browsers **block** pages with invalid CSP. Test in **Incognito Mode**:
```javascript
console.log("CSP Violations: " + window.performance.getEntriesByType("security"));
```

### **4. Forgetting Mobile/UAT Testing**
- **iOS/mobile apps** may ignore some headers (test with `curl`/`Postman`).
- **User-Agent Testing:** Some corporate proxies or old browsers behave differently.

### **5. Using `unsafe-inline` or `unsafe-eval`**
❌ Bad:
```http
Content-Security-Policy: script-src 'self' 'unsafe-inline'
```
✅ Good:
```http
Content-Security-Policy: script-src 'self' https://cdn.trusted.com;
  object-src 'none'; // Block plugins (Flash, etc.)
```
**Why?** `unsafe-inline` disables CSP’s purpose. Use **hashes** instead:
```http
script-src 'self' 'sha256-ABC123...'
```

---

## **Key Takeaways**

✅ **Always enforce HTTPS** (`Strict-Transport-Security`).
✅ **Prevent MIME sniffing** (`X-Content-Type-Options: nosniff`).
✅ **Block embedding** (`X-Frame-Options: DENY` or `samedomain`).
✅ **Use CSP to restrict scripts/styles** (start restrictive, add allowances gradually).
✅ **Control referrers** (`Referrer-Policy: strict-origin-when-cross-origin`).
✅ **Test in Incognito Mode** to catch CSP errors early.
✅ **Preload HSTS** if possible (reduce attack surface).
❌ **Avoid `Content-Security-Policy: default-src *`** (too permissive).
❌ **Don’t skip CSP evaluation** (browsers block pages with errors).
❌ **Don’t assume mobile apps respect all headers** (test with `curl`).

---

## **Conclusion: Security Headers = Free Defense**

HTTP security headers are **one of the most underutilized security controls** for APIs. They:
✔ **Prevent XSS, clickjacking, and MIME attacks** without code changes.
✔ **Enforce HTTPS** and prevent protocol downgrades.
✔ **Cost nothing** but provide **massive protection**.

**Start with these headers:**
1. `Strict-Transport-Security` (HSTS)
2. `Content-Security-Policy` (CSP)
3. `X-Content-Type-Options` (nosniff)
4. `X-Frame-Options` (DENY for sensitive endpoints)

**Then gradually refine** based on your app’s needs (e.g., CSP `hashes` for inline scripts).

**Remember:** No header is a silver bullet. Combine them with:
- **Rate limiting** (to prevent brute force).
- **JWT validation** (to enforce auth).
- **Logging & monitoring** (to detect attacks).

**Your API deserves defense in depth. Start today.**

---
### **Further Reading**
- [OWASP Security Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Security_Headers_Cheat_Sheet.html)
- [MDN CSP Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Cloudflare Security Headers Guide](https://developers.cloudflare.com/security/header-security/)
```