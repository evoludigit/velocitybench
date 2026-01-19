**[Pattern] XSS Prevention (Cross-Site Scripting) Reference Guide**

---

### **1. Overview**
Cross-Site Scripting (XSS) is a **client-side code injection attack** where an attacker injects malicious scripts into web pages rendered by unsuspecting users. These scripts can hijack sessions, steal data (e.g., cookies), perform unauthorized actions, or redirect users to phishing sites. Prevention requires a combination of **output encoding**, **input sanitization**, **Content Security Policy (CSP)**, and secure coding practices. This guide outlines proven strategies to mitigate XSS vulnerabilities in web applications.

---

### **2. Key Concepts**
#### **2.1 Attack Vectors**
XSS exploits occur via:
- **Stored XSS**: Malicious payloads persist on a server (e.g., in databases, comment fields).
- **Reflected XSS**: Payloads are embedded in URLs or form inputs and reflected in responses.
- **DOM-Based XSS**: Vulnerabilities in client-side JavaScript manipulate the Document Object Model (DOM).

#### **2.2 Mitigation Strategies**
| Strategy               | Description                                                                                     | Scope                          |
|------------------------|-------------------------------------------------------------------------------------------------|--------------------------------|
| **Output Encoding**    | Escape special characters (`<`, `>`, `&`, `"`, `'`) when rendering user input.               | Server/client side rendering.   |
| **Input Sanitization** | Remove or neutralize malicious patterns before processing input (e.g., regex, allowlists).    | API/input validation.           |
| **Content Security Policy (CSP)** | Restrict script sources via HTTP headers to block inline/third-party scripts.            | Server-side (HTTP headers).     |
| **HTTP-only Cookies**  | Prevent JavaScript access to session cookies to limit data theft.                                | Server configuration.          |
| **SameSite Cookies**   | Mitigate CSRF/XSS by restricting cookie usage to same-site contexts.                           | Server configuration.          |

#### **2.3 Encoding Rules**
| Character/Entity | HTML Encoding      | JavaScript Encoding | URL Encoding       |
|-------------------|--------------------|---------------------|--------------------|
| `<`               | `&lt;`             | `&#x3C;`             | `%3C`              |
| `>`               | `&gt;`             | `&#x3E;`             | `%3E`              |
| `&`               | `&amp;`            | `&#x26;`             | `%26`              |
| `"`               | `&quot;`           | `\\"` (escaped)     | `%22`              |
| `'`               | `&#x27;`           | `\\'` (escaped)     | `%27`              |

---
---

### **3. Schema Reference**
Use the following schemas to enforce XSS prevention.

#### **3.1 Output Encoding Schema**
**Input:** Raw user input (e.g., from DB/API).
**Output:** Safely encoded string for context (HTML, JS, URL).

| Field          | Type      | Required | Description                                                                 | Example                          |
|----------------|-----------|----------|-----------------------------------------------------------------------------|----------------------------------|
| `context`      | Enum      | Yes      | Target context: `html`, `javascript`, or `url`.                            | `"html"`                         |
| `input`        | String    | Yes      | Raw user-provided data to encode.                                           | `"<script>alert('XSS')</script>"`|
| `encode`       | Boolean   | Yes      | Toggle encoding (default: `true`).                                          | `true`                           |
| `output`       | String    | No       | Encoded result (auto-populated).                                            | `&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;` |

**Example Request (JSON):**
```json
{
  "context": "html",
  "input": "<script>alert('XSS')</script>",
  "encode": true
}
```

---

#### **3.2 Input Sanitization Schema**
**Input:** User-submitted data (e.g., form fields).
**Output:** Sanitized string allowing only safe characters/patterns.

| Field          | Type      | Required | Description                                                                 | Example                          |
|----------------|-----------|----------|-----------------------------------------------------------------------------|----------------------------------|
| `input`        | String    | Yes      | Raw user input to sanitize.                                                  | `"<img src=x onerror=alert(1)>"`  |
| `allowlist`    | Object    | No       | Whitelist of permitted tags/attributes (default: empty).                     | `{"tags": ["b", "i"], "attrs": {"a": ["href"]}}` |
| `denylist`     | Array     | No       | Blacklist of forbidden patterns (e.g., `javascript:`).                      | `["javascript:", "<script>"]`    |
| `output`       | String    | No       | Sanitized result (auto-populated).                                           | `"<b>Clean text</b>"`            |

**Example Request (JSON):**
```json
{
  "input": "<div onmouseover='alert(XSS)'>",
  "allowlist": {"tags": ["b", "i"], "attrs": {"a": ["href"]}},
  "denylist": ["onmouseover", "javascript:"]
}
```

---

#### **3.3 Content Security Policy (CSP) Schema**
**Input:** HTTP response headers.
**Output:** CSP header string restricting script sources.

| Field          | Type      | Required | Description                                                                 | Example                          |
|----------------|-----------|----------|-----------------------------------------------------------------------------|----------------------------------|
| `directives`   | Object    | Yes      | CSP directives (e.g., `script-src`, `default-src`).                         | `{"script-src": ["'self'", "trusted.cdn.com"]}` |
| `report-uri`   | String    | No       | URI for CSP violation reports.                                               | `"https://monitoring.example.com/report"` |
| `output`       | String    | No       | Generated `Content-Security-Policy` header.                                  | `"default-src 'self'; script-src 'self' trusted.cdn.com; report-uri https://monitoring.example.com/report"` |

**Example Request (JSON):**
```json
{
  "directives": {
    "script-src": ["'self'", "https://trusted.cdn.com"],
    "style-src": ["'self'", "'unsafe-inline'"]
  },
  "report-uri": "https://monitoring.example.com/report"
}
```

---

### **4. Query Examples**
#### **4.1 Output Encoding Example**
**Request:**
```http
POST /api/encode HTTP/1.1
{
  "context": "html",
  "input": "<img src=x onerror=alert(1)>"
}
```
**Response:**
```json
{
  "output": "&lt;img src=x onerror=alert(&#x28;1&#x29;)&gt;"
}
```

#### **4.2 Input Sanitization Example**
**Request:**
```http
POST /api/sanitize HTTP/1.1
{
  "input": "<script>alert('Hacked')</script>",
  "denylist": ["<script>", "javascript:"]
}
```
**Response:**
```json
{
  "output": "alert('Hacked')"
}
```

#### **4.3 CSP Header Generation**
**Request:**
```http
POST /api/csp HTTP/1.1
{
  "directives": {
    "script-src": ["'self'", "https://trusted.cdn.com"],
    "frame-src": ["'none'"]
  }
}
```
**Response:**
```json
{
  "output": "default-src 'self'; script-src 'self' https://trusted.cdn.com; frame-src 'none'"
}
```

---

### **5. Implementation Notes**
#### **5.1 Library Support**
Use libraries to automate encoding/sanitization:
- **Output Encoding:** [DOMPurify](https://github.com/cure53/DOMPurify) (JavaScript), [OWASP ESAPI](https://owasp.org/www-project-enterprise-security-api/) (Java).
- **Input Sanitization:** [HTML Purifier](https://htmlpurifier.org/) (PHP), [Sanitizer](https://pub.dev/packages/sanitize) (Dart).
- **CSP:** Configure via server (e.g., `meta` tags in HTML or `X-Content-Security-Policy` header).

#### **5.2 Edge Cases**
- **URL Encoding:** Always encode URLs before rendering (e.g., `<a href="javascript:malicious()">` → `<a href="%2Fjavascript%3Amalicious%28%29">`).
- **Dynamic Content:** Apply encoding in templates (e.g., Jinja2’s `{{ user_input|e }}`, Django’s `{{ user_input|escapejs }}`).
- **Third-Party Scripts:** Use CSP to restrict `script-src` to trusted domains.

#### **5.3 Testing**
- **Manual Testing:** Inject payloads like `<script>alert(1)</script>` into forms/URLs.
- **Automated Tools:**
  - [OWASP ZAP](https://www.zaproxy.org/)
  - [Burp Suite](https://portswigger.net/burp)
  - [XSS Scanner](https://github.com/OWASP/xss-scanner) (Node.js).

---

### **6. Related Patterns**
| Pattern                          | Description                                                                                     | Use Case                          |
|----------------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------|
| **[CSP (Content Security Policy)](https://owasp.org/www-project-secure-headers/csp/)** | Hardens browser execution by restricting resources (scripts, styles).                     | Block inline scripts/third-party risks. |
| **[Input Validation](https://owasp.org/www-project-application-security-development-guide/v5/en/0x04a0-Input-Validation-Cheat-Sheet)** | Rejects malformed/invalid input before processing.                                          | API parameters, form submissions. |
| **[HTTP Headers](https://owasp.org/www-project-secure-headers/)** | Enhances security via headers like `X-XSS-Protection` (deprecated but legacy-supported).   | Legacy systems mitigation.        |
| **[DOM Security](https://developer.mozilla.org/en-US/docs/Web/Security/Subdomain_isolation)** | Secures DOM manipulation to prevent DOM-based XSS.                                          | Client-side frameworks (React/Angular). |
| **[JSON Web Tokens (JWT)](https://jwt.io/)**                     | Encrypts data in tokens to reduce XSS impact on session hijacking.                         | API authentication.              |

---

### **7. References**
- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [CSP Specification](https://content-security-policy.com/)
- [W3C HTML Spec (Encoding)](https://html.spec.whatwg.org/multipage/parsing.html#safe-html-text-integration-point)

---
**Version:** 1.0
**Last Updated:** `YYYY-MM-DD`
**Contributors:** `@security-team, @devops`