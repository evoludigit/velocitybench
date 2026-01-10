# **[Pattern] API Authentication Patterns – Reference Guide**

---

## **Overview**
API authentication ensures that only authorized entities (users, services, or applications) can access protected resources. This pattern outlines common authentication approaches, their trade-offs, and implementation patterns to secure API endpoints.

Choosing an authentication method depends on factors like:
- **Security needs** (e.g., sensitive vs. public data).
- **Scalability** (stateless vs. stateful).
- **Complexity** (simplicity vs. granular control).
- **Use case** (internal services vs. third-party integrations).

Common patterns include **API keys**, **JSON Web Tokens (JWT)**, **OAuth 2.0**, and **session-based authentication**, each with distinct trade-offs. This guide provides implementation details, security considerations, and code examples for each approach.

---

## **Schema Reference**
| **Pattern**       | **State** | **Security** | **Scalability** | **Complexity** | **Use Case**                          |
|-------------------|------------|--------------|------------------|---------------|--------------------------------------|
| API Keys          | Stateless | Low          | High             | Low           | Simple internal services            |
| JWT               | Stateless | Medium       | High             | Medium        | Stateless microservices, mobile apps |
| OAuth 2.0         | Stateless | High         | High             | High          | Third-party integrations, delegated auth |
| Session-Based     | Stateful   | Medium       | Medium           | Medium        | Traditional web apps with cookies    |

---

## **1. API Keys**
API keys are simple, unencrypted strings used to identify clients. They are typically passed via:
- **Query parameters** (`?api_key=123abc`)
- **Headers** (`X-API-Key: 123abc`)
- **Authorization header** (`Authorization: Bearer 123abc`)

### **Implementation**
#### **Server-Side Validation**
```javascript
// Node.js/Express example
const allowedKeys = ['123abc', 'xyz789'];

app.use((req, res, next) => {
  const apiKey = req.headers['x-api-key'] || req.query.api_key;
  if (!allowedKeys.includes(apiKey)) {
    return res.status(403).send('Forbidden');
  }
  next();
});
```

#### **Database Storage (Recommended)**
Store keys securely in a database to allow revocation:
```sql
-- Example: PostgreSQL table for API keys
CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  key_value VARCHAR(128) UNIQUE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### **Trade-offs**
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Simple to implement               | No built-in expiration            |
| Stateless                        | Limited to application-level auth |
| Scales horizontally               | No per-resource permissions       |

### **Security Considerations**
- **Never log API keys** (risk of exposure).
- **Use HTTPS** to prevent interception.
- **Rotate keys periodically**.

---

## **2. JSON Web Tokens (JWT)**
JWTs are compact, URL-safe tokens containing claims (data about the user) encoded in a JSON object. They consist of three parts:
1. **Header** (algorithm, token type)
2. **Payload** (claims, e.g., `sub`, `exp`)
3. **Signature** (HMAC/SHA or RSA)

#### **Example JWT Structure**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```
- **Header**: `{"alg": "HS256", "typ": "JWT"}`
- **Payload**: `{"sub": "1234567890", "name": "John Doe", "iat": 1516239022}`
- **Signature**: Generated using a secret key.

#### **Server-Side Validation**
```javascript
// Node.js with `jsonwebtoken`
const jwt = require('jsonwebtoken');

app.post('/login', (req, res) => {
  const token = jwt.sign(
    { userId: 123, role: 'admin' },
    'your-secret-key',
    { expiresIn: '1h' }
  );
  res.json({ token });
});

app.use((req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).send('Unauthorized');

  jwt.verify(token, 'your-secret-key', (err, user) => {
    if (err) return res.status(403).send('Invalid token');
    req.user = user;
    next();
  });
});
```

#### **Client-Side Usage**
```javascript
// Fetch with JWT in Authorization header
fetch('https://api.example.com/protected', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

### **Trade-offs**
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Stateless                        | Signature verification required   |
| Scales horizontally               | Token size limits payload         |
| Supports additional claims       | Short-lived tokens reduce attack window |

### **Security Considerations**
- **Store secrets securely** (e.g., environment variables).
- **Use HTTPS** to prevent token theft.
- **Set short expiration times** (`exp` claim).
- **Avoid storing sensitive data** in payload (encode, don’t encrypt).

---

## **3. OAuth 2.0**
OAuth 2.0 enables **delegated authentication**, allowing third-party services (e.g., Google, Facebook) to authenticate users without sharing credentials. It uses **access tokens** (short-lived) and **refresh tokens** (long-lived).

### **Key Components**
| **Term**         | **Description**                                                                 |
|------------------|---------------------------------------------------------------------------------|
| **Client**       | Application requesting access (e.g., your API).                                |
| **Resource Owner** | User granting access.                                                          |
| **Authorization Server** | Issues tokens (e.g., Google OAuth server).                                    |
| **Resource Server** | Server protecting resources (your API).                                       |
| **Access Token** | Short-lived token for API access.                                              |
| **Refresh Token** | Long-lived token to get new access tokens.                                     |

### **Flow Examples**
#### **(1) Authorization Code Flow (Recommended for Web Apps)**
1. Redirect user to OAuth provider (e.g., `https://oauth.example.com/authorize`).
2. User approves access → provider redirects with `code`.
3. Client exchanges `code` for tokens:
   ```http
   POST /token HTTP/1.1
   Host: oauth.example.com
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code&code=AUTH_CODE&redirect_uri=CALLBACK_URL&client_id=CLIENT_ID&client_secret=CLIENT_SECRET
   ```
4. Provider returns:
   ```json
   {
     "access_token": "ACCESS_TOKEN",
     "refresh_token": "REFRESH_TOKEN",
     "expires_in": 3600
   }
   ```
5. Client uses `access_token` to call your API:
   ```http
   GET /protected HTTP/1.1
   Authorization: Bearer ACCESS_TOKEN
   ```

#### **(2) Client Credentials Flow (Machine-to-Machine)**
For service-to-service auth (no user involved):
```http
POST /token HTTP/1.1
Host: oauth.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=CLIENT_ID&client_secret=CLIENT_SECRET
```

### **Server-Side Validation**
Validate tokens using the provider’s **JWT introspection endpoint** (e.g., Google’s `/tokeninfo`):
```javascript
// Pseudocode to validate Google OAuth token
async function validateGoogleToken(token) {
  const response = await fetch('https://oauth2.googleapis.com/tokeninfo?access_token=' + token);
  const data = await response.json();
  return data.active; // Checks if token is valid
}
```

### **Trade-offs**
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Industry-standard                | Complex to implement              |
| Supports granular permissions    | Requires provider integration     |
| Stateless                        | Token revocation requires introspection |

### **Security Considerations**
- **Use HTTPS** for all OAuth flows.
- **Store refresh tokens securely** (avoid client-side storage).
- **Rotate client secrets periodically**.
- **Implement token revocation endpoints**.

---

## **4. Session-Based Authentication**
Session-based auth uses a **server-side session** (e.g., cookies) to track users. The client receives a session ID after login, which the server validates for subsequent requests.

### **Implementation**
#### **Server-Side (Node.js/Express)**
```javascript
const session = require('express-session');

app.use(session({
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: true } // HTTPS-only
}));

app.post('/login', (req, res) => {
  req.session.userId = 123;
  res.redirect('/dashboard');
});

app.use((req, res, next) => {
  if (!req.session.userId) {
    return res.redirect('/login');
  }
  next();
});
```

#### **Client-Side (Cookies)**
Browsers automatically send cookies with requests:
```javascript
// No action needed; cookies are sent automatically
fetch('/dashboard', {
  credentials: 'include' // Required for cookies
});
```

### **Trade-offs**
| **Pros**                          | **Cons**                          |
|-----------------------------------|-----------------------------------|
| Simple to implement               | Stateful (requires session storage) |
| Built-in CSRF protection          | Scales poorly with distributed servers |
| Session hijacking risk            | Lack of portability               |

### **Security Considerations**
- **Use `HttpOnly` cookies** to prevent XSS.
- **Set `Secure` flag** (HTTPS-only).
- **Implement CSRF tokens**.
- **Use short session timeouts**.

---

## **Query Examples**
### **API Key Example (cURL)**
```bash
curl -H "X-API-Key: abc123xyz" https://api.example.com/data
```

### **JWT Example (cURL)**
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." https://api.example.com/protected
```

### **OAuth 2.0 Example (cURL)**
```bash
curl -H "Authorization: Bearer ACCESS_TOKEN" https://api.example.com/user
```

---

## **Related Patterns**
1. **[API Rate Limiting]** – Protect APIs from abuse.
2. **[JWT Introspection]** – Validate JWTs dynamically.
3. **[OpenID Connect]** – Extends OAuth 2.0 for identity.
4. **[API Gateway Patterns]** – Centralize authentication (e.g., Kong, Apigee).
5. **[Secure Cookie Handling]** – Best practices for session auth.

---

## **When to Use Which Pattern?**
| **Scenario**               | **Recommended Pattern**       |
|----------------------------|--------------------------------|
| Simple internal API        | **API Keys**                   |
| Stateless microservices     | **JWT**                        |
| Third-party integrations   | **OAuth 2.0**                  |
| Legacy web applications     | **Session-Based**              |
| High-security requirements | **OAuth 2.0 + JWT**            |

---
**Further Reading**:
- [RFC 6750 (OAuth 2.0 Bearer Tokens)](https://tools.ietf.org/html/rfc6750)
- [JWT Best Practices (OWASP)](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Session Management Guide (OWASP)](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)