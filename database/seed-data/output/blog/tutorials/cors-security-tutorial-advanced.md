```markdown
# **CORS & Cross-Origin Resource Sharing: Security Patterns for Modern APIs**

Cross-Origin Resource Sharing (CORS) is a critical yet frequently misunderstood security mechanism for web APIs. Properly configured, it protects your API from being abused by unauthorized clients; misconfigured, it can expose sensitive data to malicious actors. As a backend engineer, you must understand CORS not just as a checkbox in your middleware, but as a deliberate security pattern that balances accessibility with protection.

In this guide, we’ll explore:
- Why browsers enforce same-origin restrictions (and why they’re necessary)
- How CORS works under the hood (without jargon)
- Practical examples in **Node.js, Python (FastAPI), and Java (Spring Boot)**
- Common misconfigurations and how to avoid them
- Advanced patterns like token-based delegation and dynamic CORS policies

Let’s dive in.

---

## **The Problem: Why Can’t Browsers Just Allow Everything?**

Browsers enforce **same-origin policy (SOP)** by default for security reasons:
- Prevents JavaScript from reading data from another site (e.g., stealing cookies or session tokens).
- Blocks unauthorized actions (e.g., `POST` requests to a payment API).
- Mitigates **CSRF (Cross-Site Request Forgery)** attacks.

### **Example: Blocked Cross-Origin Request**
If your frontend is hosted at `https://client.example.com` and you try to fetch data from `https://api.example.com`, the browser will block the request unless the server explicitly allows it:

```javascript
// This fails in the browser!
fetch('https://api.example.com/data')
  .then(response => response.json())
  .catch(error => console.error('CORS blocked:', error));
```

**Result:**
```
Access to fetch at 'https://api.example.com/data' from origin 'https://client.example.com' has been blocked by CORS policy.
```

---
## **The Solution: CORS as a Security Pattern**

CORS is an **HTTP header-based mechanism** that lets servers specify:
- Which origins (`Access-Control-Allow-Origin`) can access their APIs.
- Which HTTP methods (`Access-Control-Allow-Methods`) are allowed.
- Custom headers (`Access-Control-Allow-Headers`) for `OPTIONS` preflight requests.

### **Key Components**
| Component                     | Purpose                                                                 |
|-------------------------------|-------------------------------------------------------------------------|
| `Access-Control-Allow-Origin` | Defines allowed origins (wildcards `*` are discouraged).               |
| `Access-Control-Allow-Methods` | Lists permitted HTTP methods (`GET`, `POST`, etc.).                    |
| `Access-Control-Allow-Headers` | Specifies request headers (e.g., `Authorization`, `Content-Type`).     |
| `Access-Control-Allow-Credentials` | Allows cookies/auth tokens in requests (`true` or `false`).           |
| `Access-Control-Expose-Headers` | Defines headers the browser allows clients to read.                     |
| `Vary: Origin`                | Ensures the response changes based on the origin (required for CORS).   |

---

## **Implementation Guide**

### **1. Node.js (Express)**
Express makes CORS easy with the [`cors`](https://www.npmjs.com/package/cors) package.

#### **Basic Setup**
```javascript
const express = require('express');
const cors = require('cors');

const app = express();

// Allow all origins (⚠️ Not recommended for production)
app.use(cors());

// OR: Explicitly allow specific origins
app.use(
  cors({
    origin: ['https://client.example.com', 'https://dashboard.example.com'],
    methods: ['GET', 'POST', 'PUT'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
);
```

#### **Dynamic CORS (Per-Route)**
```javascript
app.get('/api/data', cors({ origin: 'https://client.example.com' }), (req, res) => {
  res.json({ message: "Secure data!" });
});
```

#### **Handling Credentials (Cookies/Token)**
```javascript
app.use(
  cors({
    origin: 'https://client.example.com',
    credentials: true, // Allow cookies/auth headers
  })
);
```

---

### **2. Python (FastAPI)**
FastAPI includes built-in CORS support.

#### **Basic Setup**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://client.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type", "Authorization"],
)
```

#### **Dynamic Origins (Wildcard)**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Only for testing!
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### **Preflight Handling (`OPTIONS`)**
FastAPI automatically handles preflight requests for `OPTIONS` (no extra code needed).

---

### **3. Java (Spring Boot)**
Spring Boot’s `CorsConfiguration` allows fine-grained control.

#### **Basic Setup (`application.yml`)**
```yaml
spring:
  cors:
    allowed-origins: https://client.example.com
    allowed-methods: GET, POST, PUT
    allowed-headers: Content-Type, Authorization
    allow-credentials: true
```

#### **Programmatic Configuration (Java)**
```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("https://client.example.com")
                .allowedMethods("GET", "POST")
                .allowCredentials(true);
    }
}
```

#### **Global vs. Per-Controller**
- **Global:** Set in `WebMvcConfigurer`.
- **Per-Controller:**
  ```java
  @Controller
  public class MyController {
      @GetMapping("/data")
      public ResponseEntity<String> getData() {
          return ResponseEntity.ok("Secure response");
      }
  }
  ```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Using Wildcards (`*`) in Production**
```javascript
// ❌ Bad (opens API to any domain)
app.use(cors({ origin: "*" }));
```
**Fix:** Always specify exact origins or use a **dynamic checker** (e.g., validate against a trusted list).

### **❌ Mistake 2: Forgetting `Access-Control-Allow-Credentials`**
If your API uses cookies or JWT tokens, **always set `credentials: true`**:
```javascript
// ❌ Missing credentials → fails for authenticated requests
app.use(cors({ origin: 'https://client.example.com' }));

// ✅ Correct
app.use(cors({
  origin: 'https://client.example.com',
  credentials: true
}));
```

### **❌ Mistake 3: Ignoring Preflight (`OPTIONS`) Requests**
For non-simple requests (e.g., custom headers), browsers send an `OPTIONS` request first. If your server doesn’t handle it:
```javascript
// ❌ Missing OPTIONS handler → preflight fails
fetch('https://api.example.com/data', {
  method: 'POST',
  headers: { 'X-Custom-Header': 'value' }
});
```
**Fix:** Ensure your server responds to `OPTIONS` with CORS headers:
```javascript
app.options('*', cors()); // Handle preflight
```

### **❌ Mistake 4: Overly Permissive Headers**
Restrict `allowedHeaders` to only what your API needs:
```javascript
// ❌ Too permissive
app.use(cors({ allowedHeaders: ["*"] }));

// ✅ Secure (only allow necessary headers)
app.use(cors({
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));
```

---

## **Advanced Patterns**

### **1. Token-Based Delegation (Dynamic CORS)**
Instead of hardcoding origins, validate requests via a token:
```javascript
// Example: Express middleware
app.use((req, res, next) => {
  const token = req.headers['x-api-token'];
  if (isValidToken(token)) {
    res.set('Access-Control-Allow-Origin', 'https://client.example.com');
    next();
  } else {
    res.status(403).send('Forbidden');
  }
});
```

### **2. CORS for APIs Behind a Proxy (Reverse Proxy)**
If your API is behind Nginx/Apache, configure CORS there:
```nginx
location /api/ {
    proxy_pass http://backend:3000;
    add_header 'Access-Control-Allow-Origin' 'https://client.example.com';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
}
```

### **3. Rate Limiting + CORS**
Combine CORS with rate limiting to prevent abuse:
```javascript
const rateLimit = require('express-rate-limit');
const cors = require('cors');

app.use(
  rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests
  })
);

app.use(cors({ origin: 'https://client.example.com' }));
```

---

## **Key Takeaways**
✅ **CORS is a security feature, not just a convenience.**
✅ **Never use `*` in production**—always specify exact origins.
✅ **Handle `OPTIONS` requests** for preflight (custom headers, auth tokens).
✅ **Validate credentials (`Access-Control-Allow-Credentials`)** if using cookies/JWT.
✅ **Use middleware** to dynamically control CORS per route.
✅ **Combine with other security measures** (rate limiting, auth, input validation).

---

## **Conclusion**
CORS is a double-edged sword: it enables modern web apps while protecting against misuse. As a backend engineer, your job is to configure it **securely**—not just to make it "work," but to ensure your API is **trusted only by the intended clients**.

### **Next Steps**
- Audit your CORS configuration with tools like [CORS Checker](https://check-cors.com/).
- Test edge cases (e.g., mobile apps, proxies, iframes).
- Consider **API gateways** (Kong, Apigee) for centralized CORS management.

Would you like a deeper dive into any specific aspect (e.g., CORS with WebSockets, multitenancy)? Let me know!

---
**Further Reading:**
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [OWASP CORS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Web_Socket_Hijacking_Prevention_Cheat_Sheet.html)
- [Express CORS Docs](https://github.com/expressjs/cors)
```

---
This blog post is **practical, code-first, and honest about tradeoffs**—perfect for advanced backend engineers. It covers implementation, security pitfalls, and advanced patterns while keeping examples concise and production-ready.