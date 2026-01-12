# **Debugging Authorization Context Extraction: A Troubleshooting Guide**

The **Authorization Context Extraction** pattern ensures that security-relevant data (JWT claims, session tokens, tenant IDs, etc.) is correctly captured and propagated across services. Misconfigurations or failures here can lead to unauthorized access, inconsistent authentication, or application errors.

This guide provides a structured approach to diagnose and resolve issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, verify these **common symptoms** to narrow down the problem:

| **Symptom**                          | **Description**                                                                 | **Possible Cause**                          |
|---------------------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Missing claims in request context** | API responses show `null` or empty context where JWT claims should be present.   | JWT parsing failure, middleware misconfig. |
| **401/403 errors after claim extraction** | Users logged in but denied access due to missing/incorrect context.           | Invalid token, claim extraction logic bug. |
| **Tenant context not propagated**     | Services behave differently per tenant, but context is lost in microservices.   | Middleware bypass, context incorrectly passed. |
| **Session inconsistency**             | Session data changes unpredictably across requests.                            | Improper session handling, race conditions. |
| **High latency in auth checks**       | Delays in token validation or claim extraction.                                | Expired tokens, slow JWT verification.     |
| **Logging shows `null` claims**       | Debug logs reveal missing or malformed claims.                                  | JWT parsing errors, corrupted payload.     |

**Next Step:** If any symptom matches, proceed to the relevant section.

---

## **2. Common Issues & Fixes**

### **A. JWT Claims Extraction Failure**
**Symptom:** `Authorization` header missing, claims appear as `null` in context.

#### **Possible Causes & Fixes**
1. **Missing/Invalid Authorization Header**
   - **Error:** Client sends no token or malformed header (`Bearer <token>`).
   - **Fix:** Ensure clients include the header correctly:
     ```http
     GET /api/resource HTTP/1.1
     Authorization: Bearer <valid-jwt>
     ```
   - **Server-side validation (Express.js example):**
     ```javascript
     const jwt = require('jsonwebtoken');

     app.use((req, res, next) => {
       const token = req.headers.authorization?.split(' ')[1];
       if (!token) return res.status(401).send('No token provided');

       try {
         req.user = jwt.verify(token, process.env.JWT_SECRET);
       } catch (err) {
         return res.status(403).send('Invalid token');
       }
       next();
     });
     ```

2. **JWT Parsing Errors**
   - **Error:** `jsonwebtoken.JsonWebTokenError` or `Unexpected token`.
   - **Fix:** Validate token structure and signature:
     ```javascript
     try {
       const decoded = jwt.verify(token, process.env.JWT_SECRET, {
         algorithms: ['HS256'], // Ensure correct algorithm
       });
       req.user = decoded; // Store in request context
     } catch (err) {
       if (err.name === 'TokenExpiredError') {
         return res.status(401).send('Token expired');
       }
       console.error('JWT parse error:', err);
       res.status(403).send('Invalid token');
     }
     ```

3. **Claims Not Extracted into Context**
   - **Error:** `req.user` is `undefined` despite a valid token.
   - **Fix:** Explicitly attach claims to the request object:
     ```javascript
     app.use((req, res, next) => {
       const token = req.headers.authorization?.split(' ')[1];
       if (!token) return res.status(401).send('No token');

       jwt.verify(token, process.env.JWT_SECRET, (err, decoded) => {
         if (err) return res.status(403).send('Invalid token');
         req.user = decoded; // Attach to request
         next();
       });
     });
     ```

---

### **B. Tenant Context Not Propagated**
**Symptom:** Services behave inconsistently due to missing `tenantId` in context.

#### **Possible Causes & Fixes**
1. **Middleware Order Issues**
   - **Error:** Tenant extraction middleware runs after context is lost.
   - **Fix:** Ensure tenant extraction happens **before** other middleware:
     ```javascript
     // Correct order: Tenant extraction → Auth → Route handlers
     app.use(tenantMiddleware); // Extracts tenantId from token/headers
     app.use(authMiddleware);    // Validates JWT
     app.use('/api', apiRoutes); // Uses both contexts
     ```

2. **Tenant ID Missing from Token**
   - **Error:** `tenantId` claim is not included in JWT.
   - **Fix:** Include `tenantId` during token generation:
     ```javascript
     const token = jwt.sign(
       { userId: user.id, tenantId: user.tenantId, roles: user.roles },
       process.env.JWT_SECRET,
       { expiresIn: '1h' }
     );
     ```

3. **Context Not Passed Across Microservices**
   - **Error:** Services in an API gateway lose tenant context.
   - **Fix:** Propagate context via headers or JWT claims:
     ```http
     # Example: Forward tenantId in request headers
     POST /orders
     Authorization: Bearer <jwt>
     X-Tenant-ID: <tenant-id>
     ```

---

### **C. Session Inconsistency**
**Symptom:** Session data changes unexpectedly or is lost.

#### **Possible Causes & Fixes**
1. **Session Not Stored in Redis/Memory**
   - **Error:** `req.session` is empty or corrupted.
   - **Fix:** Configure session storage:
     ```javascript
     const session = require('express-session');
     const RedisStore = require('connect-redis')(session);

     app.use(
       session({
         store: new RedisStore({ client: redisClient }),
         secret: process.env.SESSION_SECRET,
         resave: false,
         saveUninitialized: false,
       })
     );
     ```

2. **Race Conditions in Session Updates**
   - **Error:** Concurrent requests overwrite session data.
   - **Fix:** Use optimistic concurrency or transactions:
     ```javascript
     async function updateUserSession(userId, data) {
       await redisClient.get(`session:${req.sessionID}`).then((session) => {
         if (!session) throw new Error('Session expired');
         // Merge new data safely
         req.session.user = { ...req.session.user, ...data };
       });
     }
     ```

---

## **3. Debugging Tools & Techniques**

### **A. Logging & Assertions**
- **Log claims extraction:**
  ```javascript
  console.log('Extracted claims:', req.user);
  ```
- **Assert claims exist early:**
  ```javascript
  if (!req.user?.tenantId) {
    console.error('Missing tenantId in claims');
    throw new Error('Invalid context');
  }
  ```

### **B. Handy Debugging Libraries**
| Tool               | Purpose                                  | Example Usage                     |
|--------------------|------------------------------------------|-----------------------------------|
| `debug` npm package | Log middleware execution flow.           | `const debug = require('debug')('auth');` |
| `jwks-rsa`         | Debug JWT public keys (for RS256 tokens). | `const jwks = new JWKS({ ... });` |
| `express-validator` | Validate input claims.                   | `validate(tenantId: isUUID()).run()` |

### **C. API Gateway Inspection**
- **Check forwarded headers:**
  ```sh
  curl -v http://api-gateway/protected-endpoint
  ```
  Look for:
  - `X-Forwarded-User`
  - `X-Tenant-ID`
  - `Authorization` header

### **D. Postman/Insomnia Debugging**
1. **Intercept JWT claims:**
   - Use Postman’s **Pre-request Script** to decode tokens:
     ```javascript
     pm.environment.set("decodedToken", pm.cookiesAll().find(c => c.name === 'token').value);
     console.log(JSON.parse(atob(decodedToken.split('.')[1])));
     ```
2. **Test tenant context:**
   - Send a request with a hardcoded tenant ID:
     ```http
     POST /orders
     X-Tenant-ID: test-tenant
     ```

---

## **4. Prevention Strategies**
### **A. Infrastructure-Level Checks**
1. **Rate-limit JWT validation endpoints** to prevent brute-force attacks.
2. **Use circuit breakers** for authentication services:
   ```javascript
   const CircuitBreaker = require('opossum');
   const breaker = new CircuitBreaker(async () => { /* JWT verify call */ }, { timeout: 100 });
   ```

### **B. Code-Level Safeguards**
1. **Validate claims early:**
   ```javascript
   const requiredClaims = ['sub', 'tenantId', 'exp'];
   requiredClaims.forEach(claim => {
     if (!req.user[claim]) throw new Error(`Missing claim: ${claim}`);
   });
   ```

2. **Immutable Context Objects:**
   - Never modify `req.user` directly; use a wrapper:
     ```javascript
     class AuthContext {
       constructor(user) { this.user = { ...user }; }
       get tenantId() { return this.user.tenantId; }
     }
     req.auth = new AuthContext(decoded);
     ```

### **C. Testing**
1. **Unit Tests for Claim Extraction:**
   ```javascript
   const { extractClaims } = require('./middleware/auth');
   test('extracts tenantId correctly', () => {
     const token = jwt.sign({ tenantId: 'test' }, 'secret');
     const req = { headers: { authorization: `Bearer ${token}` } };
     expect(extractClaims(req)).toEqual({ tenantId: 'test' });
   });
   ```
2. **Integration Tests for Tenant Context:**
   - Mock a tenant ID in tests and verify it propagates:
     ```javascript
     describe('tenantContextMiddleware', () => {
       it('attaches tenantId to request', () => {
         const req = { headers: { 'X-Tenant-ID': 'mock-tenant' } };
         tenantContextMiddleware(req, {}, () => {});
         expect(req.tenantId).toBe('mock-tenant');
       });
     });
     ```

---

## **5. Escalation Path**
If the issue persists:
1. **Check infrastructure logs** (Kubernetes, ECS, etc.) for token decode failures.
2. **Compare production vs. staging tokens** (are claims structured differently?).
3. **Reach out to the auth team** if the JWT issuer is external (e.g., Auth0, Okta).

---
**Final Tip:** Always **document the context extraction flow** in your architecture diagrams. A visual map of how `req.user`, `tenantId`, and sessions propagate helps future troubleshooting.

---
**End of Guide.** For further reading, refer to:
- [OWASP JWT Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Express Middleware Docs](https://expressjs.com/en/guide/using-middleware.html)