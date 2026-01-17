# **Debugging REST Migration: A Troubleshooting Guide**

## **1. Introduction**
REST Migration involves updating or replacing an existing API system while minimizing downtime, ensuring backward compatibility, and maintaining data integrity. Common scenarios include upgrading from an older REST version (e.g., v1 → v2), migrating from RPC to REST, or switching from a monolithic to microservices-based REST architecture.

This guide focuses on **practical debugging**—identifying issues, applying fixes, and preventing failures during a REST Migration.

---

## **2. Symptom Checklist: Detecting REST Migration Issues**
Before diving into fixes, confirm which symptoms match your environment:

| **Symptom**                     | **Description**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|
| **Client API Errors (4xx/5xx)** | Clients (frontend, mobile, third-party) report `400 Bad Request`, `404 Not Found`, or `500 Internal Server Error`. |
| **Inconsistent Responses**      | Some requests succeed, others fail, or responses differ across deployments.    |
| **Data Mismatch**               | Database records differ between old and new APIs, or payloads are corrupted.   |
| **Performance Degradation**     | Latency spikes, timeouts, or reduced throughput after migration.              |
| **Deprecation Warnings**        | API clients receive warnings about unsupported endpoints or deprecated methods. |
| **Authentication Failures**     | Token validation errors (`401 Unauthorized`) or rate-limiting issues.         |
| **Test Failures**               | Automated tests (unit, integration, E2E) fail with migration-related errors.   |
| **Logging & Monitoring Alerts** | High error rates, connection resets, or unusual traffic patterns in logs.     |

**Next Step:** If multiple symptoms overlap, check **Common Issues and Fixes** below.

---

## **3. Common Issues & Fixes (With Code Examples)**

### **A. Endpoint Mismatch (404 Not Found)**
**Symptom:**
- Clients requesting `/v1/users` return a `404` after migration.
- Server logs show requested endpoints don’t exist in the new version.

**Root Cause:**
- Old endpoints were removed or renamed without proper redirects.
- Version paths (e.g., `/v1/`, `/v2/`) were misconfigured.

**Fix:**
1. **Add Redirects (Temporary)**
   Use reverse proxy (Nginx, Apache) or framework-level redirects:
   ```nginx
   location /v1/users {
       return 307 /v2/users;
   }
   ```
   **OR** (Express.js):
   ```javascript
   app.get('/v1/users', (req, res) => {
       res.redirect(307, '/v2/users');
   });
   ```

2. **Implement Deprecation Headers**
   Notify clients via HTTP headers:
   ```node
   res.set('X-Deprecation', 'v1/users will be removed in 6 months');
   ```

3. **Ensure Versioned Routing**
   Verify framework routing (e.g., FastAPI, Spring Boot):
   ```python
   # FastAPI (v2)
   @app.get("/users")  # No version prefix
   async def get_users():
       return {"data": [...]}
   ```

---

### **B. Payload Mismatch (400 Bad Request)**
**Symptom:**
- Clients send JSON payloads that no longer match the new API schema.
- Server returns `400 Bad Request` with validation errors.

**Root Cause:**
- Removed optional fields, changed required fields, or altered data types.
- Missing schema evolution strategy.

**Fix:**
1. **Gradual Schema Migration**
   Use **openAPI/Swagger** or **JSON Schema** to document changes:
   ```json
   // Old API (v1)
   {
     "name": "string",
     "email": "string"
   }
   // New API (v2)
   {
     "name": "string",
     "email": "string",
     "preferences": { ... }
   }
   ```

2. **Backend Validation with Backward Compatibility**
   Example (Express.js with Joi):
   ```javascript
   const schema = Joi.object({
     name: Joi.string().required(),
     email: Joi.string().email().optional(), // Allow missing in v1
     preferences: Joi.object().default({})  // Default empty object
   });
   ```

3. **Client-Side Fallback**
   If clients are under your control, update them incrementally:
   ```javascript
   // Client: Send v2 payload with v1-compatible default
   fetch("/v2/users", {
     method: "POST",
     body: JSON.stringify({
       name: "Alice",
       email: "alice@example.com" // Required in v2
     })
   });
   ```

---

### **C. Database Migration Issues**
**Symptom:**
- New API returns empty responses or stale data.
- Transactions fail due to schema changes.

**Root Cause:**
- Database tables were altered without proper migration scripts.
- ORM mappings are outdated.

**Fix:**
1. **Use Transactional Migrations**
   Example (using Sequelize for PostgreSQL):
   ```javascript
   // Migration file
   module.exports = {
     up: async (queryInterface, Sequelize) => {
       await queryInterface.addColumn('users', 'preferences', Sequelize.JSONB);
     },
     down: async (queryInterface) => {
       await queryInterface.removeColumn('users', 'preferences');
     }
   };
   ```

2. **Data Transformation Layer**
   Add a middleware to enrich old data with new fields:
   ```python
   # Django: Transform old records
   def enhance_user_data(user):
       if not user.preferences:
           user.preferences = {"theme": "dark"}
       return user
   ```

3. **Validate Data Integrity**
   Run checks after migration:
   ```sql
   SELECT COUNT(*) FROM users WHERE preferences IS NULL;
   ```

---

### **D. Authentication Failures (401 Unauthorized)**
**Symptom:**
- `/v2/auth/token` fails, but `/v1/auth/token` works.
- JWT tokens are rejected after migration.

**Root Cause:**
- Secret keys were not synchronized between old/new auth systems.
- Token algorithms changed (e.g., from HMAC to RS256).

**Fix:**
1. **Update Token Generation**
   Ensure new auth service uses the same algorithm:
   ```javascript
   // Old (HMAC)
   const token = jwt.sign({ userId: 1 }, 'old_secret', { algorithm: 'HS256' });
   // New (RS256)
   const token = jwt.sign({ userId: 1 }, 'public_key.pem', { algorithm: 'RS256' });
   ```

2. **Backward-Compatible Token Validation**
   Temporarily allow both old and new formats:
   ```javascript
   try {
     // Try new format first
     jwt.verify(token, 'new_secret');
   } catch (err) {
     jwt.verify(token, 'old_secret'); // Fallback
   }
   ```

3. **Rotate Keys Gradually**
   Use **zero-downtime key rotation**:
   - Issue new tokens with both old and new keys.
   - Decommission old keys after validation.

---

### **E. Performance Bottlenecks**
**Symptom:**
- New API endpoints are slower than old ones.
- High latency or timeouts after migration.

**Root Cause:**
- New implementation has inefficient queries.
- Caching layer was not migrated.
- Load balancer misconfiguration.

**Fix:**
1. **Profile API Endpoints**
   Use APM tools (New Relic, Datadog) or `traceroute`:
   ```bash
   # Example: Check slow API call
   curl -o /dev/null -s -w "%{time_total}s" http://api.example.com/v2/users
   ```

2. **Optimize Database Queries**
   Add indexes for frequently queried fields:
   ```sql
   CREATE INDEX idx_users_email ON users(email);
   ```

3. **Enable Caching**
   Example (Redis + Express):
   ```javascript
   const cache = require('memory-cache');
   app.get('/v2/users/:id', (req, res) => {
     const key = `user:${req.params.id}`;
     const cached = cache.get(key);
     if (cached) return res.send(cached);

     // Fetch from DB
     db.getUser(req.params.id, (err, user) => {
       cache.put(key, user, 1000 * 60 * 5); // Cache for 5 mins
       res.send(user);
     });
   });
   ```

---

### **F. CORS & Cross-Origin Issues**
**Symptom:**
- Frontend makes requests to `/v2/api` but gets `CORS preflight` errors.
- `OPTIONS` requests fail.

**Root Cause:**
- Missing `Access-Control-Allow-Origin` headers.
- Preflight (`OPTIONS`) not handled.

**Fix:**
1. **Enable CORS Middleware**
   Example (Express):
   ```javascript
   const cors = require('cors');
   app.use(cors({
     origin: ['https://client.example.com'],
     methods: ['GET', 'POST', 'OPTIONS']
   }));
   ```

2. **Handle Preflight Requests Explicitly**
   ```javascript
   app.options('*', cors());
   app.use(cors());
   ```

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**          | **Use Case**                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| **Postman/Insomnia**        | Test endpoints with different headers, payloads, and versions.              |
| **cURL**                    | Debug raw HTTP requests/responses.                                         |
| **TLS Decryption (mitmproxy)** | Inspect encrypted traffic (e.g., OAuth flows).                          |
| **Database Logs**           | Check SQL query performance (e.g., `pgBadger` for PostgreSQL).              |
| **APM Tools (New Relic, Datadog)** | Monitor latency, errors, and throughput in production.                   |
| **Distributed Tracing (Jaeger, OpenTelemetry)** | Trace requests across services (useful for microservices).       |
| **Load Testing (k6, Gatling)** | Simulate traffic to find bottlenecks.                                     |
| **Reverse Proxy (Nginx, Envoy)** | Log and inspect incoming/outgoing requests.                             |
| **Git Diff & Migration Scripts** | Compare old/new code to spot regressions.                                  |

**Example Debugging Workflow:**
1. **Reproduce the issue** with `curl`:
   ```bash
   curl -v http://localhost:3000/v2/users -H "Authorization: Bearer token"
   ```
2. **Inspect logs**:
   ```bash
   grep "GET /v2/users" /var/log/nginx/error.log
   ```
3. **Use APM** to trace a failing request:
   ```
   New Relic > APM > Transactions > Filter by endpoint
   ```

---

## **5. Prevention Strategies for Future Migrations**
To avoid REST migration headaches, follow these best practices:

### **A. Pre-Migration Planning**
1. **Document API Versioning Rules**
   - Use **semantic versioning** (`/v1`, `/v2`, etc.).
   - Define **deprecation policy** (e.g., 6 months notice before removal).
2. **Backward Compatibility Test Matrix**
   | Old API | New API | Test Case |
   |---------|--------|-----------|
   | v1      | v2     | Endpoint redirects work |
   | v1      | v2     | Payload validation passes |
   | v1      | v3     | Data transformation works |

3. **Staggered Rollout**
   - Deploy new API in parallel with old (canary release).
   - Monitor error rates before full switch.

### **B. Automated Testing**
1. **Contract Testing**
   Use **Pact** to test consumer-producer contracts:
   ```bash
   pact-broker verify-consumer http://client-service pact-file.json
   ```
2. **Schema Validation**
   Validate JSON payloads with **JSON Schema**:
   ```bash
   jsonschema -i payload.json schema-v2.json
   ```
3. **Load & Chaos Testing**
   Simulate 10K RPS to check stability:
   ```javascript
   // k6 script
   import http from 'k6/http';
   export default function () {
     http.get('http://api.example.com/v2/users');
   }
   ```

### **C. Monitoring & Alerting**
1. **Track Migration Metrics**
   - % of traffic using old vs. new API.
   - Error rates for deprecated endpoints.
2. **Set Up Alerts**
   Example (Prometheus + Alertmanager):
   ```yaml
   # alert_rules.yml
   - alert: HighMigrationErrorRate
     expr: rate(http_requests_total{status=~"5.."}[1m]) > 0.1
     for: 5m
     labels:
       severity: critical
   ```

### **D. Documentation & Communication**
1. **API Changelog**
   Maintain a **GitHub/GitLab issue** with migration notes:
   ```
   ## Migration: v1 → v2
   - **Breaking**: Removed `legacy_field` (use `new_field` instead).
   - **Deprecated**: `/v1/users` → Redirect to `/v2/users` by [date].
   ```
2. **Notify Consumers**
   - Publish deprecation warnings in API docs.
   - Send email alerts to dependent services.

### **E. Rollback Plan**
1. **Feature Flags**
   Use tools like **LaunchDarkly** to toggle API versions:
   ```javascript
   if (featureFlags.useV2API) {
     return newV2Handler(req);
   } else {
     return oldV1Handler(req);
   }
   ```
2. **Database Rollback Scripts**
   Keep a copy of the old schema for quick recovery.

---

## **6. Final Checklist Before Going Live**
| **Task**                          | **Done?** |
|------------------------------------|----------|
| ✅ All endpoints have redirects or deprecation warnings |          |
| ✅ Database schema is validated with migration scripts |          |
| ✅ Authentication/authorization is backward-compatible |          |
| ✅ Performance is tested under load |          |
| ✅ CORS and preflight are configured |          |
| ✅ Monitoring is set up for error tracking |          |
| ✅ Rollback plan is documented |          |
| ✅ All teams (devs, QA, ops) are notified |          |

---

## **7. Conclusion**
REST migrations are complex but manageable with:
1. **Systematic testing** (contract, load, chaos).
2. **Gradual rollouts** (canary, feature flags).
3. **Clear documentation** (deprecation policies, changelogs).
4. **Observability** (APM, logging, alerts).

**Key Takeaway:**
*"Assume the old API will be used until explicitly deprecated."* Always provide fallbacks, monitor traffic shifts, and have a rollback plan.

---
**Further Reading:**
- [REST API Versioning Best Practices](https://restfulapi.net/)
- [Google’s API Design Guide](https://apis.google.com/tools)
- [Kubernetes Migration Checklist](https://kubernetes.io/docs/concepts/cluster-administration/cluster-management/) (for microservices)