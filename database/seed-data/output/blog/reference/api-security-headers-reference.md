# **[Pattern] HTTP Security Headers for APIs – Reference Guide**

---

## **1. Overview**
HTTP security headers are metadata transmitted in HTTP responses that instruct browsers, proxies, and other clients on how to handle and secure content. They are a **low-cost, high-impact** defense mechanism against common web vulnerabilities like **Cross-Site Scripting (XSS), Clickjacking, MIME Sniffing, and Session Hijacking**.

For APIs—especially those accessed via browsers or third-party clients—implementing security headers is critical to prevent data leakage, unauthorized resource embedding, and malicious content execution. This guide covers essential headers, their configurations, and implementation best practices for API security.

---

## **2. Schema Reference**
Below is a structured reference table of recommended HTTP security headers for APIs, categorized by security concern.

| **Header**               | **Purpose**                                                                                     | **API-Specific Notes**                                                                 | **Example Values**                                                                 |
|--------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Content-Security-Policy (CSP)** | Mitigates XSS, data injection, and prevents loading untrusted resources.                     | Use `default-src` liberally for APIs; block inline scripts if possible.                 | `default-src 'self'; script-src 'self' https://trusted.cdn.com`                     |
| **Strict-Transport-Security (HSTS)** | Enforces HTTPS, preventing SSL stripping attacks.                                             | Must be served over HTTPS initially; use `preload` for maximum security.                | `max-age=63072000; includeSubDomains; preload`                                    |
| **X-Frame-Options**      | Prevents Clickjacking by restricting embedding in iframes.                                    | Deprecated in favor of `Content-Security-Policy`.                                      | `deny` (block all), `sameorigin` (only allow parent origin)                         |
| **X-Content-Type-Options** | Mitigates MIME sniffing attacks by preventing browsers from interpreting content as a different type. | Useful for JSON/XML APIs with file extensions (e.g., `.json`) that could be misread.     | `nosniff`                                                                          |
| **Referrer-Policy**      | Controls how much referrer information is sent with requests.                                 | Protects against tracking leaks; use `strict-origin-when-cross-origin` for APIs.       | `strict-origin-when-cross-origin`                                                   |
| **Cross-Origin-Opener-Policy (COOP)** | Restricts cross-origin access via window.opener.                                              | Reduces risk of tabnabbing attacks.                                                     | `same-origin` (default), `same-origin-when-cross-origin`                          |
| **Cross-Origin-Resource-Policy (CORP)** | Controls cross-origin resource sharing.                                                       | Useful for APIs serving assets (images, scripts) to third-party domains.               | `same-origin`, `cross-origin`                                                      |
| **Permissions-Policy**   | Restricts browser permissions (e.g., camera, geolocation) for cross-origin requests.         | Critical for APIs accessed via browser extensions or iframes.                           | `geolocation=(), camera=()`                                                          |
| **Expect-CT**            | Enforces Certificate Transparency for future enforcement of valid certificates.                | Helps detect MITM attacks early.                                                         | `max-age=86400, enforce`                                                            |
| **Server**               | Obfuscates backend server details (reduces attack surface).                                   | Replace with generic values (e.g., `"MyApp/1.0"`).                                      | `Server: nginx/1.18.0` (avoid exposing real versions)                             |
| **X-XSS-Protection**     | Legacy header for XSS filtering (now deprecated in favor of CSP).                            | Rarely needed if CSP is configured properly.                                            | `0` (disabled)                                                                     |
| **Feature-Policy**       | Deprecated; replaced by `Permissions-Policy`.                                                | Avoid using.                                                                             | *(Deprecated)*                                                                    |

---

## **3. Implementation Examples**
### **3.1 Setting Headers in Common Frameworks**
#### **Node.js (Express)**
```javascript
const express = require('express');
const app = express();

app.use((req, res, next) => {
  res.set({
    "Content-Security-Policy": "default-src 'self'; script-src 'self' https://trusted.cdn.com",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin"
  });
  next();
});

app.get('/api/data', (req, res) => {
  res.json({ data: "Secure API response" });
});

app.listen(3000);
```

#### **Python (Flask)**
```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'"
    response.headers['Strict-Transport-Security'] = "max-age=63072000; includeSubDomains"
    response.headers['X-Content-Type-Options'] = "nosniff"
    return response

@app.route('/api/data')
def get_data():
    return jsonify({"data": "Secure API response"})

if __name__ == '__main__':
    app.run(ssl_context='adhoc')  # For HTTPS in development
```

#### **Nginx (Configuration)**
```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://trusted.cdn.com" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    location /api/ {
        proxy_pass http://backend;
    }
}
```

#### **Apache (`.htaccess`)**
```apache
Header set Content-Security-Policy "default-src 'self'; script-src 'self'"
Header set Strict-Transport-Security "max-age=63072000; includeSubDomains"
Header set X-Content-Type-Options "nosniff"
Header set Referrer-Policy "strict-origin-when-cross-origin"
```

---

### **3.2 Dynamic Header Generation (Example: CSP for APIs)**
For APIs returning HTML (e.g., documentation or error pages), dynamically generate CSP:
```javascript
// Node.js example for HTML responses
app.get('/api/docs', (req, res) => {
  const html = `<!DOCTYPE html><html><head><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'">...</head>`;
  res.send(html);
});
```

---

## **4. Query Examples**
### **4.1 Testing Headers with `curl`**
```bash
curl -I https://api.example.com/data
# Check for headers in response:
# HTTP/2 200
# content-security-policy: default-src 'self'; script-src 'self'
# strict-transport-security: max-age=63072000; includeSubDomains
# x-content-type-options: nosniff
```

### **4.2 Validating Headers with Online Tools**
- **[SecurityHeaders.com](https://securityheaders.com/)** – Audit your API’s headers.
- **[Mozilla Observatory](https://observatory.mozilla.org/)** – Comprehensive security checks.
- **[WhatWeb](https://whatweb.me/)** – Identify misconfigurations.

### **4.3 Example API Response Headers**
```http
HTTP/2 200 OK
Content-Security-Policy: default-src 'self'; script-src 'self' https://trusted.cdn.com; object-src 'none'
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
Cross-Origin-Resource-Policy: same-origin
Permissions-Policy: geolocation=()
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Server: MyApp/1.0
```

---

## **5. Common Pitfalls & Mitigations**
| **Issue**                          | **Cause**                                  | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------|------------------------------------------------------------------------------|
| **CSP blocking legitimate scripts** | Overly restrictive `script-src` rules.     | Whitelist all trusted domains (CDNs, third-party APIs).                       |
| **HSTS preload errors**             | Missing `includeSubDomains` or SSL misconfig. | Verify SSL certificates and regenerate HSTS header.                          |
| **CORP misconfiguration**            | Incorrect `Cross-Origin-Resource-Policy`.   | Use `same-origin` unless assets are intentionally shared.                    |
| **Permissions-Policy too restrictive** | Blocking required features (e.g., `camera`). | Allow only necessary permissions (e.g., `camera=('https://example.com')`).    |
| **X-Frame-Options ignored**         | Deprecated in favor of CSP.               | Replace with `frame-ancestors` in CSP: `frame-ancestors 'none'`.            |

---

## **6. Related Patterns**
1. **[API Authentication & Authorization](#)** – Combine with headers for secure access (e.g., `Authorization: Bearer <token>`).
2. **[Rate Limiting for APIs](#)** – Protect against brute-force attacks alongside security headers.
3. **[Input Validation for APIs](#)** – Validate all inputs to prevent injection attacks (e.g., SQLi, XSS).
4. **[API Gateway Security](#)** – Use gateways (e.g., Kong, AWS API Gateway) to enforce headers centrally.
5. **[Certificate Transparency](#)** – Pair `Expect-CT` with CT monitoring for MITM detection.
6. **[JSON Web Tokens (JWT) for APIs](#)** – Secure token transmission with `Strict-Transport-Security`.

---
## **7. Further Reading**
- [OWASP HTTP Security Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Security_Headers_Cheat_Sheet.html)
- [MDN Web Docs: Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [CSP Evaluator](https://csp-evaluator.withgoogle.com/) – Test your CSP rules.

---
**Note:** Always test headers in a staging environment before production deployment. Some headers (e.g., HSTS) require careful planning to avoid breaking existing HTTPS setups.