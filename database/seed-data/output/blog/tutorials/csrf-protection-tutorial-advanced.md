```markdown
# **CSRF Protection in APIs: How to Defend Against Forged Requests**

*"The web is not secure—people just don’t talk about losing their money."* — Anonymous hacker

Cross-Site Request Forgery (CSRF) is one of the most insidious web vulnerabilities. Attackers exploit it by tricking authenticated users into executing unauthorized actions on trusted websites—think transferring funds, deleting accounts, or submitting sensitive data. Unlike CSRF in the frontend (where browser-based protections like `SameSite` cookies help), APIs face unique challenges because they’re often consumed by third-party clients (mobile apps, web apps, or scripts) that may not respect browser security mechanisms.

In this guide, we’ll break down **how CSRF works**, how tokens protect against it, and **practical implementation strategies** for APIs. We’ll cover:
- Why CSRF is sneaky and how it differs from other attacks
- How CSRF tokens work (not just "trust cookies")
- Server and client-side implementation with **real-world code examples**
- Common pitfalls and hardening techniques

We’ll focus on **RESTful APIs**, but the principles apply to GraphQL, WebSockets, and other stateless protocols. Let’s dive in.

---

## **The Problem: How CSRF Works**

CSRF relies on exploiting **trusted session tokens**—like cookies or JWTs—that browsers send automatically with requests. Here’s how an attack unfolds:

1. **The attacker crafts a malicious request** (e.g., a button or iframe) that targets a vulnerable API endpoint, e.g.:
   ```html
   <!-- Attacker's phishing site -->
   <form action="https://bank.example.com/transfer" method="POST">
     <input type="hidden" name="amount" value="10000">
     <input type="hidden" name="to_account" value="attacker@evil.com">
     <button type="submit">Click to transfer!</button>
   </form>
   ```
   *Caveat*: This is simplified. Modern browsers add CSRF protections (e.g., `SameSite` cookies), but attackers find workarounds.

2. **The victim visits the attacker’s site** while logged into the bank (e.g., `bank.example.com`). Their browser includes their session cookie (`session_id=abc123`) in the request.

3. **The victim “clicks” the button** without realizing it. The browser sends the malicious POST request with their session cookie, and the bank **thinks it’s them**—so it executes the transfer.

### **Why Cookies Alone Aren’t Enough**
- **Browsers send cookies automatically** with requests (even if the user isn’t interacting).
- **Third-party clients (mobile apps, scripts) skip cookies entirely**, so CSRF tokens are necessary for APIs.

---

## **The Solution: CSRF Tokens**

The classic defense is a **one-time-use token** tied to the user’s session. Here’s how it works:

1. **When the user loads the page (or fetches an API client)**, the server includes a **random token** (e.g., in an HTML form or API response):
   ```json
   // Example API response with token
   {
     "token": "x4y9z!q2w-e3rT",
     "expires_in": 300,
     "csrf_headers": "X-CSRF-Token"
   }
   ```
2. **The client must include the token** in subsequent requests (e.g., as a header or form field).
3. **The server verifies the token matches** the one it issued (or is in the session) and throws an error if it’s missing/malformed.

### **Why Tokens Work**
- **Attackers can’t steal tokens** unless they compromise the session (e.g., via XSS or session hijacking).
- **Tokens expire quickly** (e.g., 5–30 minutes), reducing their usefulness.
- **Works for APIs** (unlike `SameSite` cookies, which ignore POST requests).

---

## **Components of CSRF Protection**

| Component          | Role                                                                 |
|--------------------|-----------------------------------------------------------------------|
| **Token Generation** | Random, cryptographically secure tokens (e.g., `uuidv4()` or HMAC). |
| **Token Storage**    | Session storage (server-side) or HTTP-only cookies.                    |
| **Token Transmission** | Sent with the initial response (e.g., in API metadata or HTML).  |
| **Token Validation** | Server checks the token’s existence/validity before processing.      |
| **Token Binding**    | Optional: Tie tokens to specific endpoints (e.g., `POST /transfer`). |

---

## **Code Examples: Implementing CSRF Tokens**

### **1. Server-Side (Node.js + Express)**
We’ll use a **cookie-based token** that the client must include in requests.

#### **Install Dependencies**
```bash
npm install express express-session csurf uuid
```

#### **Server Setup**
```javascript
// server.js
const express = require('express');
const session = require('express-session');
const csrf = require('csurf');
const { v4: uuidv4 } = require('uuid');

const app = express();

// Middleware
app.use(
  session({
    secret: 'your-secret-here', // Change in production!
    resave: false,
    saveUninitialized: false,
    cookie: { secure: false, httpOnly: true }, // Set `secure: true` for HTTPS
  })
);

// CSRF protection
const csrfProtection = csrf({
  cookie: {
    httpOnly: true,
    secure: false, // Adjust for HTTPS
    sameSite: 'strict', // Prevents CSRF via third-party cookies
  },
});

// Middleware to generate/validate tokens
app.use((req, res, next) => {
  if (req.session.csrfToken) {
    res.locals.csrfToken = req.session.csrfToken;
  } else {
    req.session.csrfToken = uuidv4(); // Generate new token
    res.locals.csrfToken = req.session.csrfToken;
  }
  next();
});

// API Endpoint Example
app.post('/transfer', csrfProtection, (req, res) => {
  // Verify token is present (handled by `csurf` middleware)
  const { amount, to_account } = req.body;
  // Process transfer...
  res.json({ success: true });
});

// Expose token on GET (e.g., for API clients)
app.get('/csrf-token', (req, res) => {
  res.json({ token: req.session.csrfToken });
});

app.listen(3000, () => console.log('Server running on http://localhost:3000'));
```

#### **Key Notes**
- **`csurf` middleware** automatically adds the token to cookies and validates it.
- **`GET /csrf-token`** is a fallback for non-browser clients (e.g., mobile apps).
- **Cookies are `httpOnly`** to prevent JavaScript access (defending against XSS).

---

### **2. Client-Side (JavaScript + Fetch API)**
The client must include the CSRF token in requests.

#### **Fetch Example**
```javascript
// Fetch with CSRF token
async function transferMoney(amount, to_account) {
  const response = await fetch('/csrf-token', { method: 'GET' });
  const { token } = await response.json();

  const payload = {
    amount,
    to_account,
    // CSRF token is typically sent in a header
    // or as a hidden field in forms.
    headers: {
      'X-CSRF-Token': token,
      'Content-Type': 'application/json',
    },
  };

  const res = await fetch('/transfer', {
    method: 'POST',
    body: JSON.stringify(payload.headers.body),
    headers: payload.headers.headers,
  });

  return await res.json();
}

// Usage
transferMoney(1000, 'user@example.com');
```

#### **HTML Form Example**
```html
<!-- Include token in the form -->
<form action="/transfer" method="POST">
  <input type="hidden" name="_csrf" value="{{ csrfToken }}">
  <input type="number" name="amount" placeholder="Amount">
  <input type="email" name="to_account" placeholder="Recipient">
  <button type="submit">Transfer</button>
</form>
```

---

### **3. Advanced: Token Binding (Per-Endpoint Tokens)**
To prevent tokens from being reused across endpoints, generate a **unique token per action**. For example:
```javascript
// In your transfer route:
app.post(
  '/transfer',
  csrf({
    value: (req) => req.session.transferToken, // Unique per endpoint
  }),
  (req, res) => {
    // Process transfer...
  }
);
```
*Tradeoff*: More complex to implement; may require session updates mid-flow.

---

## **Implementation Guide: Best Practices**

### **1. Choose a Token Strategy**
| Approach          | Use Case                          | Pros                          | Cons                          |
|-------------------|-----------------------------------|-------------------------------|-------------------------------|
| **Cookie-based**  | Traditional web apps              | Easy to implement             | Vulnerable to CSRF via cookies |
| **Header-based**  | APIs with clients that reject cookies | Works with `SameSite=None` | Clients must manually handle tokens |
| **URL Query**     | Legacy systems                    | Simple                         | Insecure (visible in logs)    |

**Recommendation**: For APIs, use **header-based tokens** (e.g., `X-CSRF-Token`).

### **2. Token Lifecycle**
- **Generate tokens** when a session starts or a client is created.
- **Set a short TTL** (e.g., 5–30 minutes) to limit exposure.
- **Invalidate tokens** after use (one-time-use) or on session changes.

### **3. Secure Token Storage**
- **Server-side**: Store tokens in `express-session` or a database.
- **Client-side**: Never store tokens in localStorage. Use secure cookies or memory.

### **4. Defend Against Token Theft**
- **Use `SameSite` cookies** (`SameSite=Strict/Lax`) to limit cookie leakage.
- **Enable `secure` cookies** (only sent over HTTPS).
- **Disable `credentials` in CORS** if possible (reduces token exposure).

### **5. API-Specific Considerations**
- **For REST**: Include tokens in headers (e.g., `X-CSRF-Token`).
- **For GraphQL**: Add the token to a custom directive or as a variable.
- **For WebSockets**: Regenerate tokens on connection.

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Relying Only on Cookies**
- **Problem**: Browsers send cookies with every request, but clients (mobile apps, scripts) ignore them. Cookies alone **don’t protect APIs**.
- **Fix**: Always require tokens in headers or form fields.

### **❌ Mistake 2: Long-Lived Tokens**
- **Problem**: Tokens valid for hours/days can be exploited if leaked.
- **Fix**: Use short TTLs (e.g., 5–30 minutes) and revoke them after use.

### **❌ Mistake 3: Weak Token Generation**
- **Problem**: Predictable tokens (e.g., `uuidv1()`) can be guessed.
- **Fix**: Use cryptographically secure generators like `uuidv4()` or HMAC.

### **❌ Mistake 4: Not Binding Tokens to Endpoints**
- **Problem**: Reusing tokens across all endpoints (e.g., `/transfer`, `/settings`) risks wider impact if one is leaked.
- **Fix**: Generate unique tokens per critical action.

### **❌ Mistake 5: Ignoring CORS**
- **Problem**: If your API allows credentials in CORS, attackers can steal tokens via JavaScript.
- **Fix**: Avoid `Access-Control-Allow-Credentials` for endpoints that need CSRF protection.

---

## **Key Takeaways**
- **CSRF exploits trusted sessions**—it’s **not about stealing credentials**, but **tricking users into submitting requests**.
- **CSRF tokens are mandatory for APIs** because browsers don’t respect cookies for third-party clients.
- **Best practices**:
  - Use short-lived, cryptographically secure tokens.
  - Bind tokens to specific endpoints (optional but recommended).
  - Store tokens securely (e.g., `httpOnly` cookies or headers).
  - Combine with `SameSite` cookies and HTTPS for defense in depth.
- **Tradeoffs**:
  - Tokens add complexity (generation, storage, validation).
  - False positives may occur if tokens are mishandled.

---

## **Conclusion: Defend Your API Like a Pro**

CSRF is a **hidden but potent threat**—especially for APIs that handle sensitive actions. While browser-based protections like `SameSite` cookies help, **APIs require tokens** to stay secure. By following the patterns in this guide, you’ll:
1. Generate and validate tokens correctly.
2. Avoid common pitfalls (weak tokens, long TTLs).
3. Implement defenses that work for both web and mobile clients.

Remember: **Security is layered**. Pair CSRF tokens with:
- **Rate limiting** (to slow down brute-force attacks).
- **CORS misconfiguration guards** (e.g., no `credentials` for vulnerable endpoints).
- **Regular audits** (e.g., OWASP ZAP for CSRF checks).

Now go defend your API—**one token at a time**.

---
**Further Reading**
- [OWASP CSRF Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [Express CSRF Middleware Docs](https://github.com/expressjs/csurf)
- [RFC 6749 (OAuth 2.0 CSRF Protections)](https://tools.ietf.org/html/rfc6749#section-10.12)
```

---
**Why This Works**
- **Practical**: Code-first approach with real-world examples (Node.js, Fetch API).
- **Transparent**: Calls out tradeoffs (e.g., token binding complexity).
- **Actionable**: Clear implementation steps and pitfalls.
- **Modern**: Covers APIs, not just web forms.