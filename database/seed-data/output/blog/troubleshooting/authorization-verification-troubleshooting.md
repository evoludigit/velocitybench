# **Debugging [Authorization Verification]: A Troubleshooting Guide**
*A Focused Guide for Backend Engineers*

---

## **1. Introduction**
Authorization Verification ensures that users, services, or requests have the necessary permissions to access resources. Issues in this pattern can lead to unauthorized access, denial of service, or inconsistent security policies.

This guide provides a structured approach to diagnosing and resolving common authorization failures while minimizing downtime.

---

## **2. Symptom Checklist**
Use this checklist to quickly identify where the issue lies:

| **Symptom**                          | **Possible Cause**                          | **Check First** |
|--------------------------------------|---------------------------------------------|----------------|
| User denied access despite valid credentials | **RBAC (Role-Based Access Control) misconfiguration** | Check policy rules, role assignments |
| Permission errors in API responses   | **Policy engine misconfiguration**           | Verify middleware, JWT claims, or claim-based auth |
| Intermittent auth failures           | **Token expiration/revocation issues**       | Check token TTL, refresh logic, and CORS settings |
| 403 Forbidden despite correct roles   | **Incorrect claim mapping**                 | Validate JWT payload vs. policy rules |
| Service-to-service auth failures     | **OAuth2/OIDC misconfiguration**             | Check client secret, scopes, and token validation |
| Logs show "Missing Authorization Header" | **Missing middleware**                     | Verify `express-auth`, `spring-security`, or equivalent |

---

## **3. Common Issues & Fixes**

### **A. Role-Based Access Control (RBAC) Misconfiguration**
**Symptom:** Users with correct credentials get `403 Forbidden`.

#### **Debugging Steps:**
1. **Log the Request Context**
   ```javascript
   // Express.js Example
   const roles = req.user.roles; // Should log: ["admin", "user"]
   console.log("Assigned Roles:", roles);
   ```
2. **Verify Policy Rules**
   ```plaintext
   // Check if policy allows the action:
   // Rule: { user: { read: ["user", "admin"] } }
   ```
   - If `req.user.roles` is `["admin"]`, but the policy expects `["user"]`, access is denied.

3. **Fix: Adjust Role Matching Logic**
   ```javascript
   function canAccess(resource, action, userRoles) {
       const allowedRoles = resource.policies[action];
       return userRoles.some(role => allowedRoles.includes(role));
   }
   ```

---

### **B. JWT Claim Mismatch**
**Symptom:** API responds with `403` despite valid token.

#### **Debugging Steps:**
1. **Decode the JWT (Avoid Signing Validation)**
   ```bash
   echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... | openssl base64 -d | jq .`
   ```
   - Check `roles`, `permissions`, or `resource_access` claims.

2. **Compare with Expected Claims**
   ```plaintext
   // JWT Payload:
   {
     "user_id": 123,
     "roles": ["admin"]
   }
   // Policy Rule:
   {
     "users": {
       "read": ["user", "admin"]
     }
   }
   ```
   - If `req.user.roles` does not match, access is denied.

3. **Fix: Update Token Issuance**
   ```javascript
   // Ensure correct roles are embedded in the token
   const token = jwt.sign({ roles: ["admin", "viewer"] }, SECRET, { expiresIn: "1h" });
   ```

---

### **C. Intermittent Token Expiry Issues**
**Symptom:** Users randomly get `401 Unauthorized`.

#### **Debugging Steps:**
1. **Check Token Expiry & Refresh Logic**
   ```javascript
   // If token expires, should trigger refresh
   const decoded = jwt.decode(req.headers.authorization.split(" ")[1]);
   if (decoded.exp < Date.now() / 1000) {
       return res.status(401).json({ error: "Token expired" });
   }
   ```
2. **Verify Token Renewal Endpoint**
   ```http
   POST /auth/refresh
   Headers: { Authorization: "Bearer <refresh_token>" }
   ```
   - If missing, implement:
     ```javascript
     app.post("/auth/refresh", (req, res) => {
         const { refreshToken } = req.body;
         const newAccessToken = generateJWT(refreshToken);
         res.json({ access_token: newAccessToken });
     });
     ```

3. **Fix: Adjust TTL or Add Retry Logic**
   ```javascript
   const tokenTTL = 300; // 5 mins (default: 1h)
   const token = jwt.sign(userData, SECRET, { expiresIn: `${tokenTTL}min` });
   ```

---

### **D. Missing or Misconfigured Middleware**
**Symptom:** Some endpoints skip auth checks.

#### **Debugging Steps:**
1. **Check Middleware Application**
   ```javascript
   // Express.js: Ensure auth middleware runs before routes
   app.use("/api", authMiddleware);
   app.get("/api/secure", (req, res) => { ... });
   ```
2. **Verify CORS & Token Validation**
   ```javascript
   app.use(cors({ credentials: true })); // Ensure cookies/JWT headers pass
   app.use(authMiddleware); // Must run before routes
   ```
3. **Fix: Standardize Auth Middleware**
   ```javascript
   function authMiddleware(req, res, next) {
       const token = req.headers.authorization?.split(" ")[1];
       if (!token) return res.status(401).json({ error: "Missing token" });
       jwt.verify(token, SECRET, (err, user) => {
           if (err) return res.status(403).json({ error: "Invalid token" });
           req.user = user;
           next();
       });
   }
   ```

---

### **E. Service-to-Service Auth Failures (OAuth2/OIDC)**
**Symptom:** Microservices reject each other’s requests.

#### **Debugging Steps:**
1. **Check Client Credentials**
   ```plaintext
   // Ensure client_id & client_secret are correct
   Client Credentials Flow:
   POST /token
   {
     "grant_type": "client_credentials",
     "client_id": "serviceA",
     "client_secret": "secret123",
     "scope": "api:read"
   }
   ```
2. **Validate Token Scopes**
   ```javascript
   // Verify scope in auth middleware
   const scopes = token.payload.scope.split(" ");
   if (!scopes.includes("api:read")) {
       return res.status(403).json({ error: "Insufficient scope" });
   }
   ```
3. **Fix: Configure Scopes in Auth Server**
   ```plaintext
   // OAuth2 Config (Node.js example):
   server.setDefaultGrantHandler(async (grant, req, token, callback) => {
       if (grant === "client_credentials") {
           const scope = req.body.scope || "api:read";
           token.setScope(scope);
           callback(null, token);
       }
   });
   ```

---

## **4. Debugging Tools & Techniques**

### **A. Logging & Observability**
- **Log Requests with Context**
  ```javascript
  morgan(':method :url :status :response-time ms - :res[content-length] bytes', {
      skip: (req) => req.originalUrl.startsWith('/health'),
  });
  ```
- **Use Structured Logging (JSON)**
  ```javascript
  winston.logger.info({
      labels: { requestId: req.id, userId: req.user?.id },
      message: "Access granted to resource X",
  });
  ```
- **Distributed Tracing (OpenTelemetry)**
  ```python
  # Python Example (FastAPI)
  from opentelemetry import trace
  tracer = trace.get_tracer(__name__)
  with tracer.start_as_current_span("auth_check"):
      verify_token(req.headers["authorization"])
  ```

### **B. Static Analysis & Testing**
- **Unit Test Auth Logic**
  ```javascript
  // Jest Example
  test("Admin can access restricted route", () => {
      req.user = { roles: ["admin"] };
      const res = {};
      mockAuthMiddleware(req, res);
      expect(res.status).toHaveBeenCalledWith(200);
  });
  ```
- **Policy Testing Tools**
  - **OPA (Open Policy Agent):** Test RBAC rules via `opa eval` CLI.
    ```bash
    opa eval --data file://policies.authz rules,req --input '{"input": {"roles": ["user"]}}'
    ```

### **C. Network Debugging**
- **Inspect API Requests (Postman/curl)**
  ```bash
  curl -X GET "http://api.example.com/secure" \
       -H "Authorization: Bearer <token>"
  ```
- **Use Wireshark to Check Header Transmissions**
  - Verify `Authorization: Bearer <token>` is included.

---

## **5. Prevention Strategies**

### **A. Infrastructure & Configuration**
1. **Enforce Least Privilege**
   - Use IAM policies (AWS) or Kubernetes RBAC to restrict service accounts.
   ```yaml
   # Kubernetes RBAC Example
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata: name: api-reader
   rules:
   - apiGroups: [""]
     resources: ["pods"]
     verbs: ["get", "list"]
   ```
2. **Rotate Secrets Regularly**
   - Automate JWT secret rotation via CI/CD.

### **B. Code-Level Safeguards**
1. **Immutable Claims**
   - Avoid modifying JWT claims after issuance.
2. **Rate-Limiting for Auth Endpoints**
   ```javascript
   // Express-rate-limit
   const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
   app.use("/auth/login", limiter);
   ```

### **C. Monitoring & Alerts**
1. **Track Auth Failures**
   - Monitor `401/403` responses in Prometheus/Grafana.
   ```promql
   rate(http_requests_total{status=~"4.."}[5m]) > 0
   ```
2. **Anomaly Detection**
   - Use tools like **Sentry** or **Datadog** to alert on sudden auth spikes.

### **D. Documentation & Onboarding**
1. **Document Policy Rules**
   - Maintain a **README** for RBAC rules.
2. **Train Developers**
   - Run **Phishing Simulations** for auth credentials.

---

## **6. Quick-Resolution Checklist**
| **Issue**                     | **Immediate Fix**                          |
|-------------------------------|--------------------------------------------|
| **403 Forbidden**             | Verify JWT claims vs. policy rules          |
| **Token Expired**             | Implement token refresh logic              |
| **Missing Middleware**        | Ensure auth middleware runs before routes  |
| **Service Auth Failure**      | Check OAuth2 client credentials/scope      |
| **RBAC Misconfiguration**     | Validate role assignments in logs          |

---

## **7. Conclusion**
Authorization failures are often traceable to **mismatched claims**, **misconfigured policies**, or **missing middleware**. By following this guide, you can:
✅ **Log requests with context** for quick debugging.
✅ **Validate token claims** against policy rules.
✅ **Automate token refresh** to avoid expiry issues.
✅ **Use observability tools** to monitor auth failures.

**Next Steps:**
1. **Audit your current auth middleware** against this guide.
2. **Test edge cases** (e.g., expired tokens, missing roles).
3. **Automate policy validation** with tools like OPA.

---
**Final Tip:** If all else fails, **reproduce the issue in a staging environment** with identical configs. Debugging in production should be a last resort.