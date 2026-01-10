# **Debugging CORS & Cross-Origin Resource Sharing Security: A Troubleshooting Guide**
*For Backend Engineers*

Cross-Origin Resource Sharing (CORS) is a critical security mechanism that controls how web applications interact with APIs across different origins. Misconfigurations can lead to security vulnerabilities, performance bottlenecks, or outright failures. This guide helps you diagnose and resolve CORS-related issues efficiently.

---

## **1. Symptom Checklist**
✅ **Frontend fails to call API with CORS error** (e.g., `No 'Access-Control-Allow-Origin' header`)
✅ **Preflight (OPTIONS) requests fail silently** or take too long
✅ **Credentials (cookies, auth headers) are blocked** when they shouldn’t be
✅ **`Access-Control-Allow-Credentials: true` is missing** when needed
✅ **`Access-Control-Allow-Origin` is set to `*` (wildcard) incorrectly**
✅ **Backend ignores `Origin` or `Access-Control-Request-Headers` headers**
✅ **Frontend and backend use different schemes (HTTP vs HTTPS)**

---

## **2. Common Issues and Fixes**

### **Issue 1: Missing or Incorrect `Access-Control-Allow-Origin` Header**
**Symptom:**
```
Access to fetch at 'https://api.example.com/data' from origin 'https://app.example.com' has been blocked by CORS policy.
```

**Root Cause:**
The backend doesn’t send the proper `Access-Control-Allow-Origin` header.

**Fix (Backend Response Headers):**
- **For single-domain access:**
  ```http
  Access-Control-Allow-Origin: https://app.example.com
  ```
- **For wildcard (not recommended for credentials):**
  ```http
  Access-Control-Allow-Origin: *
  ```
- **For multiple domains:**
  ```http
  Access-Control-Allow-Origin: https://app1.example.com, https://app2.example.com
  ```

**Example (Node.js/Express):**
```javascript
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "https://app.example.com");
  next();
});
```

---

### **Issue 2: Preflight (OPTIONS) Requests Failing**
**Symptom:**
- `OPTIONS` request fails with `404` or `405`
- Frontend hangs waiting for preflight response

**Root Cause:**
The backend doesn’t handle `OPTIONS` requests, or missing required headers:
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`

**Fix:**
**Express.js (Node.js):**
```javascript
app.options("*", (req, res) => {
  res.header("Access-Control-Allow-Origin", "https://app.example.com");
  res.header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE");
  res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
  res.sendStatus(200);
});
```

**Flask (Python):**
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.before_request
def preflight_handler():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        }
        return jsonify(), 200, headers
```

---

### **Issue 3: Credentials Not Allowed (Cookies/Authorization)**
**Symptom:**
- `No 'Access-Control-Allow-Credentials' in response`
- Frontend fails with `Request failed with status 403`

**Root Cause:**
- `Access-Control-Allow-Credentials` is missing.
- `Origin` header is not included in the request (or `Access-Control-Allow-Origin` is `*`).

**Fix:**
- **Backend Response:**
  ```http
  Access-Control-Allow-Origin: https://app.example.com
  Access-Control-Allow-Credentials: true
  ```
- **Frontend Request:**
  ```javascript
  fetch('https://api.example.com/data', {
    credentials: 'include' // Must match backend
  });
  ```

**Example (Express):**
```javascript
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "https://app.example.com");
  res.header("Access-Control-Allow-Credentials", true);
  next();
});
```

**Note:** If using `*` (`Access-Control-Allow-Origin: *`), **credentials cannot be sent**.

---

### **Issue 4: Wildcard (`*`) Misuse**
**Symptom:**
- API works with `*` but fails when credentials are needed.
- Security risk (any domain can access the API).

**Fix:**
- Replace `*` with explicit domains.
- If credentials are needed, **never** use `*`.

---

### **Issue 5: Incorrect `Access-Control-Allow-Methods`**
**Symptom:**
- `PUT`/`DELETE` requests fail with `405 Method Not Allowed`.

**Fix:**
Ensure the backend allows the required methods:
```http
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
```

**Example (Nginx Config):**
```nginx
location / {
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
    add_header 'Access-Control-Allow-Origin' 'https://app.example.com';
}
```

---

## **3. Debugging Tools & Techniques**

### **Browser DevTools (F12)**
- **Network Tab:** Check CORS headers in the response.
- **Headers:** Verify `Access-Control-Allow-Origin`, `Access-Control-Allow-Credentials`, etc.
- **Preflight Requests:** Look for `OPTIONS` requests before the real request.

### **cURL for Manual Testing**
```bash
curl -I -X OPTIONS "https://api.example.com/data" -H "Origin: https://app.example.com"
```
Check headers for missing CORS responses.

### **Postman / Insomnia**
- Send requests with `Origin` header.
- Verify response headers match expectations.

---

## **4. Prevention Strategies**

### **Best Practices for Secure CORS**
✔ **Explicit Origins Only:** Avoid `*`; specify exact domains.
✔ **HTTPS Enforcement:** Ensure both frontend and backend use HTTPS.
✔ **Preflight Handling:** Always respond to `OPTIONS`.
✔ **Credentials Security:** Use `Access-Control-Allow-Credentials` only when necessary.
✔ **Rate Limiting:** Protect against CORS-related attacks.
✔ **Logging & Monitoring:** Audit CORS-related requests.

### **Example: Secure CORS Middleware (Express)**
```javascript
const cors = require("cors");

const allowedOrigins = ["https://app.example.com", "https://dashboard.example.com"];

app.use(
  cors({
    origin: allowedOrigins,
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
);
```

---

### **Final Notes**
- **Test in Production:** Always validate CORS settings in a staging environment.
- **Update Frameworks:** Use the latest CORS middleware (Express `cors`, Flask extensions).
- **Document Policies:** Clearly define which origins are allowed.

By following this guide, you can quickly diagnose and fix CORS issues while maintaining security and performance. 🚀