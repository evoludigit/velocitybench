# **[Pattern] CORS (Cross-Origin Resource Sharing) Security Reference Guide**
*Enforce controlled cross-origin access to APIs while mitigating vulnerabilities.*

---

## **Overview**
Cross-Origin Resource Sharing (CORS) is a browser-enforced security mechanism that restricts how web applications can access resources (e.g., APIs) from domains, protocols, or ports different from their own. While CORS enables safe cross-origin communication (e.g., JavaScript `fetch()` calls), misconfigured policies can expose APIs to unauthorized access, leading to data leaks, CSRF (Cross-Site Request Forgery), or information disclosure.

This guide provides implementation details for secure CORS policies, including proper header usage, validation requirements, and mitigation strategies for common vulnerabilities.

---

## **Key Concepts**
| **Term**               | **Description**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Origin**             | A combination of `<scheme>://<host>:<port>` (e.g., `https://api.example.com`).                      |
| **Preflight Request**  | An HTTP `OPTIONS` request sent by browsers before actual requests (e.g., `PUT`, `DELETE`) involving headers or custom methods. |
| **Simple Requests**    | `GET`, `POST`, `HEAD`, or `OPTIONS` with headers: `Accept`, `Accept-Language`, `Content-Language`, `Content-Type` (only `text/plain`, `multipart/form-data`, or `application/x-www-form-urlencoded`). |
| **Credentials**        | Sensitive data (e.g., cookies, HTTP auth) included in cross-origin requests via `withCredentials: true`. |
| **Wildcard (`*`)**     | Allows any origin but is insecure for sensitive APIs; should be avoided.                            |
| **Access-Control-Allow-Origin** | Specifies which origins can access the resource. Must match the request origin exactly (or use `*` for development only). |
| **Access-Control-Allow-Methods** | Lists permitted HTTP methods (e.g., `GET, POST, PUT`).                                               |
| **Access-Control-Allow-Headers** | Specifies allowed custom headers in requests (e.g., `Authorization`).                                  |
| **Access-Control-Max-Age** | Cache preflight responses for `N` seconds to reduce redundant `OPTIONS` requests.                     |
| **Access-Control-Allow-Credentials** | Required if `withCredentials: true` is used in the frontend. Cannot be `*`; must specify exact origins. |

---

## **Schema Reference**
Below are the required and optional CORS headers for secure API responses.

### **1. Required Headers for Simple Requests**
| **Header**                          | **Purpose**                                                                                     | **Example Value**                          |
|-------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------|
| `Access-Control-Allow-Origin`      | Explicitly allow the origin(s) that can access the resource.                                      | `https://client.example.com`                |
| `Access-Control-Allow-Methods`     | Define permitted HTTP methods (comma-separated).                                                 | `GET, POST, OPTIONS`                       |
| `Access-Control-Allow-Headers`     | Specify custom headers allowed in requests (e.g., `Authorization`).                              | `Content-Type, Authorization`              |
| `Access-Control-Max-Age`            | Cache preflight responses for `N` seconds (reduce latency).                                        | `86400` (24 hours)                          |

### **2. Required Headers for Preflight Requests**
| **Header**                          | **Purpose**                                                                                     | **Example Value**                          |
|-------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------|
| `Access-Control-Allow-Origin`      | Same as above (must match preflight origin).                                                    | `https://client.example.com`                |
| `Access-Control-Allow-Methods`     | Include all methods used in the actual request.                                                  | `POST, PUT`                                 |
| `Access-Control-Allow-Headers`     | Include all headers from the preflight request.                                                  | `Content-Type, Authorization`              |
| `Access-Control-Allow-Credentials` | Required if credentials are included (`withCredentials: true` in frontend).                       | `true`                                      |
| `Access-Control-Max-Age`            | Optional but recommended to cache preflight responses.                                            | `3600` (1 hour)                             |
| `Access-Control-Expose-Headers`    | Specify custom headers exposed to the frontend (e.g., `X-Custom-Header`).                          | `X-RateLimit-Limit, X-RateLimit-Remaining` |

### **3. Headers for Credentials (Sensitive Data)**
| **Header**                          | **Purpose**                                                                                     | **Example Value**                          |
|-------------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------|
| `Access-Control-Allow-Credentials` | Explicitly allow credentials (cannot be `*`).                                                    | `true`                                      |
| `Access-Control-Allow-Origin`      | Must specify exact origin (no wildcard).                                                          | `https://client.example.com`                |

---

## **Implementation Rules**
### **1. Basic CORS for Simple Requests**
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
Access-Control-Max-Age: 86400
```

### **2. Handling Preflight Requests**
When a browser sends a preflight `OPTIONS` request:
```http
OPTIONS /api/resource HTTP/1.1
Origin: https://client.example.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: Authorization, X-Custom-Header

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Methods: PUT, POST
Access-Control-Allow-Headers: Authorization, X-Custom-Header
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 3600
```

### **3. Credentials Support**
If the frontend uses `withCredentials: true`:
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Content-Type
```

### **4. Wildcard Usage (Development Only)**
⚠️ **Never use `*` in production for sensitive endpoints.**
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: *  # UNSAFE for production
```

---

## **Query Examples**
### **Example 1: Simple GET Request (No Preflight)**
**Frontend (JavaScript):**
```javascript
fetch('https://api.example.com/data')
  .then(response => response.json());
```

**Backend Response:**
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Methods: GET
```

---

### **Example 2: Preflight for PUT Request**
**Frontend (JavaScript):**
```javascript
fetch('https://api.example.com/data', {
  method: 'PUT',
  headers: { 'Authorization': 'Bearer token', 'X-Custom-Header': 'value' }
});
```
**Browser sends (first):**
```http
OPTIONS /data HTTP/1.1
Origin: https://client.example.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: Authorization, X-Custom-Header
```
**Backend Response (Preflight):**
```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Methods: PUT
Access-Control-Allow-Headers: Authorization, X-Custom-Header
Access-Control-Allow-Credentials: true
```
**Backend Response (Actual PUT):**
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Credentials: true
```

---

### **Example 3: CSRF Protection with CORS**
To prevent CSRF, use:
- **SameSite Cookies** (`SameSite=Strict` or `SameSite=Lax`).
- **CSRF Tokens** in POST/PUT requests.
```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: https://client.example.com
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: POST
Access-Control-Allow-Headers: Content-Type, X-CSRF-Token
```

---

## **Security Recommendations**
| **Risk**                          | **Mitigation Strategy**                                                                         |
|-----------------------------------|-------------------------------------------------------------------------------------------------|
| **Overly Permissive `*` Origin** | Replace with exact origin(s) in production.                                                     |
| **Missing `Access-Control-Allow-Credentials`** | Always include if credentials are used.                                                          |
| **No Preflight Handling**         | Ensure backend responds to `OPTIONS` requests with correct headers.                              |
| **Missing `Access-Control-Allow-Methods`** | Explicitly list allowed methods to prevent method spoofing.                                       |
| **CSRF Vulnerability**            | Use `SameSite` cookies + CSRF tokens for state-changing requests.                               |
| **Exposing Sensitive Headers**    | Use `Access-Control-Expose-Headers` to limit exposed headers.                                    |
| **Cache Stampedes**               | Set reasonable `Access-Control-Max-Age` (e.g., 1 hour).                                          |

---

## **Common Pitfalls & Fixes**
| **Issue**                          | **Symptom**                                                                                     | **Solution**                                                                                     |
|------------------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **CORS Blocked (403/405)**        | `No 'Access-Control-Allow-Origin' header` error in console.                                    | Add `Access-Control-Allow-Origin` with correct origin.                                             |
| **Preflight Failed**              | `OPTIONS` request rejected with missing headers.                                                | Ensure backend responds to `OPTIONS` with `Access-Control-Allow-Methods` and `-Headers`.       |
| **Credentials Not Sent**          | Backend receives no cookies/auth headers.                                                        | Set `Access-Control-Allow-Credentials: true` + `withCredentials: true` in frontend.              |
| **Wildcard (`*`) in Production** | Unauthorized access via third-party sites.                                                      | Replace `*` with exact origins.                                                                    |
| **Missing `VARY: Origin` Header** | Caching issues with different origins.                                                          | Add `VARY: Origin` to prevent shared caching.                                                     |

---

## **Related Patterns**
1. **[Authentication & Authorization]** – Securely validate user credentials before granting CORS access.
2. **[CSRF Protection]** – Combine with `SameSite` cookies and tokens to prevent CSRF attacks.
3. **[Rate Limiting]** – Protect APIs from abuse via headers like `X-RateLimit-Limit`.
4. **[JSON Web Tokens (JWT)]** – Use JWT for stateless authentication in cross-origin requests.
5. **[Subresource Integrity (SRI)]** – Validate frontend scripts to prevent injection attacks.
6. **[Web Application Firewall (WAF)]** – Filter suspicious CORS-related requests at the network level.

---
**See Also:**
- [MDN CORS Documentation](https://developer.mozilla.org/docs/Web/HTTP/CORS)
- [OWASP CORS Guide](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Web_Socket_Hijacking_Prevention_Cheat_Sheet.html#cors)