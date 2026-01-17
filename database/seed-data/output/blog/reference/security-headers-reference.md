# **[Pattern] HTTP Security Headers (CSP, HSTS, etc.) Reference Guide**

---

## **Overview**
HTTP Security Headers are HTTP response headers that instruct browsers, proxies, and other clients on security behaviors, mitigating risks like cross-site scripting (XSS), data injection, and session hijacking. This pattern covers critical headers such as **Content Security Policy (CSP)**, **HTTP Strict Transport Security (HSTS)**, **X-Content-Type-Options**, and others. Proper implementation defends against OWASP Top 10 vulnerabilities like **A01:2021 Broken Access Control** and **A03:2021 Sensitive Data Exposure**.

Best practices include:
- Using **HTTP/2 or HTTP/3** (TLS required).
- Deploying headers via **server-side middleware** (e.g., Nginx, Apache, Cloudflare).
- Gradually enforcing **CSP** with `report-only` mode before strict enforcement.
- Validating headers via **security scanners** (e.g., OWASP ZAP, Burp Suite).

---

## **Schema Reference**

| **Header**               | **Purpose**                                                                 | **Format/Example**                                                                 | **Best Practices**                                                                                     |
|--------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Content-Security-Policy (CSP)** | Mitigates XSS, data injection by restricting resource loads (scripts, styles, images). | `Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.cdn.com;` | Start with `report-only` mode (`Content-Security-Policy-Report-Only`). Use nonces for dynamic scripts. |
| **Strict-Transport-Security (HSTS)** | Enforces HTTPS, prevents SSL stripping.                                     | `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`         | Deploy after verifying HTTPS setup. Use `includeSubDomains` cautiously.                              |
| **X-Content-Type-Options** | Prevents MIME-sniffing attacks (e.g., `.html` files served as `.php`).     | `X-Content-Type-Options: nosniff`                                                  | Enable for all static/dynamic content.                                                               |
| **X-Frame-Options**      | Blocks clickjacking by restricting embedding in `<frame>`/`<iframe>`.       | `X-Frame-Options: DENY` or `SAMEORIGIN`                                             | Use `DENY` for sensitive pages, `SAMEORIGIN` for internal tools.                                     |
| **Referrer-Policy**      | Controls referrer headers sent with requests (privacy/leak protection).     | `Referrer-Policy: strict-origin-when-cross-origin`                                 | Default: `no-referrer-when-downgrade`. Adjust per security/privacy needs.                            |
| **Permissions-Policy**   | Granular control over browser features (e.g., camera, geolocation).         | `Permissions-Policy: geolocation=() camera=(self)`                                 | Restrict to `self` for sensitive APIs; audit regularly.                                               |
| **Feature-Policy** (Deprecated; use `Permissions-Policy`) | Legacy header for feature control.                                         | (Replaced by `Permissions-Policy`)                                                  | Migrate to `Permissions-Policy` for compatibility.                                                   |
| **Cache-Control**        | Prevents cache poisoning by restricting caching of sensitive responses.     | `Cache-Control: no-store, must-revalidate`                                         | Use `no-store` for authentication tokens; `private` for user-specific data.                          |
| **Server**               | Hides server software (reduces attack surface).                             | (Omit or use generic: `Server: nginx/1.25.3`)                                      | Avoid disclosing exact versions (e.g., `Apache/2.4.54`).                                             |

---

## **Implementation Details**

### **1. Content Security Policy (CSP)**
CSP defines allowed sources for resources (scripts, styles, images). Use **three modes**:

| **Mode**               | **Header Prefix**       | **Purpose**                                                                 |
|------------------------|-------------------------|---------------------------------------------------------------------------|
| **Enforce Mode**       | `Content-Security-Policy` | Blocks violations; requires precise directives.                           |
| **Report-Only Mode**   | `Content-Security-Policy-Report-Only` | Logs violations to a `report-uri` endpoint (debugging).                  |
| **Hash Mode**          | `Content-Security-Policy` | Allows scripts/styles with specific hashes (e.g., `sha256-...`).          |

**Example (Enforcement):**
```http
Content-Security-Policy:
  default-src 'self';
  script-src 'self' https://cdn.example.com 'nonce-abc123';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data:;
  report-uri /csp-report-endpoint
```

**Key Directives:**
- `default-src`: Fallback for unlisted types.
- `script-src`: Whitelist script origins (use `nonce`/`hash` for dynamic scripts).
- `style-src`: Controls CSS loading (avoid `unsafe-inline` unless necessary).
- `connect-src`: Restricts `fetch()`/`XMLHttpRequest` origins.
- `font-src`: Limits font loading (e.g., Google Fonts).

**Debugging Tools:**
- [Report URI Validator](https://csp-evaluator.withgoogle.com/)
- Browser DevTools (Security tab for CSP violations).

---

### **2. HTTP Strict Transport Security (HSTS)**
HSTS forces HTTPS and prevents downgrade attacks. **Rollout procedure:**
1. **Test Phase (1 day):** `max-age=86400` + `includeSubDomains`.
2. **Production Phase (1 year):** `max-age=31536000`.
3. **Preload (Optional):** Submit to [HSTS Preload List](https://hstspreload.org/).

**Example:**
```http
Strict-Transport-Security:
  max-age=31536000;
  includeSubDomains;
  preload
```

**Critical Notes:**
- **Do not use `max-age` < 1 year** in production (risk of broken redirects).
- **Avoid `preload`** until fully tested (irreversible once submitted).
- **Fix mixed content issues** before deploying HSTS.

---

### **3. X-Content-Type-Options**
Prevents browsers from interpreting files (e.g., `.txt` as `.php`) as MIME types other than declared.

**Example:**
```http
X-Content-Type-Options: nosniff
```

**When to Use:**
- Always enable for **user-uploaded files** (e.g., PDFs, images).
- Standard for **dynamic content** (e.g., API responses).

---

### **4. X-Frame-Options**
Blocks clickjacking by restricting embedding.

| **Value**   | **Behavior**                                                                 |
|-------------|-----------------------------------------------------------------------------|
| `DENY`      | Blocks all framing.                                                        |
| `SAMEORIGIN`| Allows framing only from same origin.                                       |
| `ALLOW-FROM uri` | Allows framing from specific URIs (rarely used).                          |

**Example:**
```http
X-Frame-Options: DENY
```

**Best Practice:**
- Use `DENY` for **sensitive pages** (login, dashboards).
- Use `SAMEORIGIN` for **internal tools** (e.g., admin panels).

---

### **5. Referrer-Policy**
Controls how much referrer info is sent with requests.

| **Policy**                          | **Description**                                                                 |
|-------------------------------------|---------------------------------------------------------------------------------|
| `no-referrer`                       | No referrer sent (privacy-focused).                                              |
| `no-referrer-when-downgrade` (default) | Omits referrer unless HTTPS → HTTP.                                             |
| `origin`                            | Sends only the origin (e.g., `https://example.com`).                            |
| `strict-origin`                     | Like `origin`, but drops path/query fragments.                                 |
| `strict-origin-when-cross-origin`   | Like `strict-origin` but only for cross-origin requests.                       |
| `unsafe-url`                        | Always sends full referrer (avoid).                                             |

**Example:**
```http
Referrer-Policy: strict-origin-when-cross-origin
```

**Use Cases:**
- `strict-origin` for **public pages**.
- `no-referrer` for **sensitive logins**.

---

### **6. Permissions-Policy**
Replaces `Feature-Policy`; grants/denies browser APIs (e.g., camera, geolocation).

**Example (Restrictive):**
```http
Permissions-Policy:
  geolocation=(),
  camera=(self),
  microphone='none',
  payment=(self)
```

**Common Directives:**
- `geolocation`: `(self)` or `()` (block).
- `camera/microphone`: `(self)` or `'none'`.
- `payment`: Restrict to payment processors.

**Audit Tool:** [Permissions Policy Violation Reporter](https://permissions-policy.com/).

---

### **7. Cache-Control**
Prevents cache poisoning by restricting sensitive responses.

| **Directive**       | **Behavior**                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| `no-store`          | Never cache (critical for cookies/tokens).                                  |
| `private`           | Cache only for the user (e.g., user-specific data).                        |
| `public`            | Cache for anyone (use cautiously).                                          |
| `must-revalidate`   | Requires re-validation before reuse (security-sensitive).                   |
| `max-age=0`         | Disable caching (like `no-cache`).                                          |

**Example (Secure):**
```http
Cache-Control: no-store, must-revalidate
```

**Use Cases:**
- `no-store` for **auth tokens**.
- `private` for **user-specific API responses**.

---

## **Query Examples**

### **1. Nginx Configuration (CSP + HSTS)**
```nginx
server {
    listen 443 ssl;
    server_name example.com;

    # CSP (Report-Only Mode)
    add_header Content-Security-Policy-Report-Only "default-src 'self'; script-src 'self' https://cdn.example.com; report-uri /csp-report";

    # HSTS
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Other Headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=()" always;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
}
```

### **2. Apache `.htaccess` (Basic Headers)**
```apache
<IfModule mod_headers.c>
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
</IfModule>
```

### **3. Node.js (Express Middleware)**
```javascript
const helmet = require('helmet');
const express = require('express');
const app = express();

app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            scriptSrc: ["'self'", "https://cdn.example.com"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            reportUri: "/csp-report"
        }
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true
    },
    referrerPolicy: { policy: "strict-origin-when-cross-origin" }
}));
```

### **4. Cloudflare (Firebase) Rules**
```json
{
  "hosts": ["example.com"],
  "rules": [
    {
      "type": "headers",
      "content_type": null,
      "key": "Content-Security-Policy",
      "value": "default-src 'self'; script-src 'self' https://cdn.example.com;"
    },
    {
      "type": "headers",
      "content_type": null,
      "key": "Strict-Transport-Security",
      "value": "max-age=31536000; includeSubDomains"
    }
  ]
}
```

---

## **Validation & Testing**
1. **Browser DevTools:**
   - Check **Network tab** for missing headers.
   - **Security tab** for CSP violations.
2. **Automated Scanners:**
   - [OWASP ZAP](https://www.zaproxy.org/) (CSP/HSTS tests).
   - [SecurityHeaders.com](https://securityheaders.com/) (compliance score).
3. **Manual Checks:**
   - Use `curl -I` to inspect headers:
     ```bash
     curl -I https://example.com
     ```
   - Test HSTS with [HSTS Preflight Checker](https://hstspreload.org/check).

---

## **Related Patterns**
1. **[Secure Cookies](SecureCookies.md)** – Guide to `SameSite`, `Secure`, and `HttpOnly` attributes.
2. **[Rate Limiting](RateLimiting.md)** – Mitigates brute-force attacks on APIs.
3. **[Web Application Firewall (WAF)](WAF.md)** – Filters malicious traffic (e.g., Cloudflare, AWS WAF).
4. **[TLS Configuration](TLS.md)** – Best practices for strong encryption (e.g., TLS 1.3, cipher suites).
5. **[API Security](APISecurity.md)** – Securing REST/gRPC endpoints (auth, validation).

---
## **Troubleshooting**
| **Issue**                          | **Solution**                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| **CSP violations in production**    | Start with `report-only` mode; debug via `report-uri`.                     |
| **HSTS breaking HTTPS sites**       | Ensure all subdomains use HTTPS; fix mixed content (HTTP → HTTPS redirects). |
| **X-Frame-Options blocking iframes** | Use `SAMEORIGIN` if embedding from same domain is allowed.                  |
| **Permissions-Policy blocking features** | Whitelist origins explicitly (e.g., `camera=(self)`).                    |

---
## **References**
- [CSP Specification (W3C)](https://content-security-policy.com/)
- [HSTS Best Practices (Mozilla)](https://httpwg.org/http-extensions/draft-ietf-httpbis-hsts.html)
- [OWASP Security Headers Project](https://owasp.org/www-project-secure-headers/)
- [Google’s Security Header Cheat Sheet](https://developers.google.com/web/fundamentals/security/csp)