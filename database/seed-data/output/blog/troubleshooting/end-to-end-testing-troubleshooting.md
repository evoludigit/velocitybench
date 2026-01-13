# **Debugging End-to-End (E2E) Testing Patterns: A Troubleshooting Guide**

---

## **1. Title**
**Debugging End-to-End Testing: A Practical Troubleshooting Guide**
*(For when unit/integration tests pass, but real-world workflows fail)*

---

## **2. Symptom Checklist**
Before diving deep, rule out these common root causes:

| **Symptom** | **Likely Cause** | **Quick Check** |
|-------------|------------------|-----------------|
| Login fails despite 100% unit test coverage | Authentication flow mismatch (e.g., token expiration, API version drift) | Check logs, compare test vs. prod auth endpoints |
| Orders work in tests but fail in production | Dependency mismatch (e.g., payment gateway version, external API changes) | Compare `package.json`/`requirements.txt` between test and prod |
| UI breaks after DB schema migration | Legacy queries breaking due to missing columns/constraints | Run `SELECT * FROM information_schema.columns` on prod DB |
| Post-deployment workflow crashes | Environment variable leaks (e.g., `DEBUG=true` in production) | Check `env` variables for leaked dev configs |
| Search functionality degrades over time | Caching layer misconfiguration (Redis, CDN) | Verify cache keys, TTL, and invalidation rules |
| Mobile app crashes on checkout | API contract drift (JSON schemas, field deprecations) | Use `Postman`/`Insomnia` to validate API responses |
| High latency in user flows | Database connection pooling exhausted | Check `pg_stat_activity` (PostgreSQL) for idle connections |
| "Works on my machine" production failures | Local vs. cloud environment mismatch (e.g., storage paths, time zones) | Use `docker-compose` to replicate the exact environment |

---

## **3. Common Issues and Fixes (with Code Examples)**

### **Issue 1: Authentication/Authorization Mismatch**
**Symptom:** *"All unit tests pass, but users can’t log in."*
**Root Cause:**
- Test auth uses mock services (e.g., `jest.mock('user-service')`), but production relies on real JWT/OAuth.
- Token signing/validation algorithms differ between test and prod.

**Debugging Steps:**
1. **Compare Auth Flows**
   ```javascript
   // Test (mocked)
   const authService = { validateToken: () => true };

   // Production (real)
   const authService = require('./real-auth-service');
   ```
2. **Check Token Expiry/Revocation**
   - Use `jwt-decode` to inspect tokens:
     ```bash
     npm install jwt-decode
     echo 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' | base64 --decode | jq
     ```
3. **Enable Debug Logging**
   ```javascript
   app.use((req, res, next) => {
     if (req.headers['x-debug-auth']) {
       console.log('Request auth headers:', req.headers.authorization);
     }
     next();
   });
   ```

**Fix:**
- Use **feature flags** to toggle auth services:
  ```javascript
  const useMockAuth = process.env.NODE_ENV === 'test';
  const authService = useMockAuth
    ? require('./mock-auth')
    : require('./prod-auth');
  ```

---

### **Issue 2: Dependency/External API Drift**
**Symptom:** *"Integration tests pass, but checkout fails in production."*
**Root Cause:**
- Payment gateway (`Stripe`) or third-party API changed endpoints/fields.
- Local testing uses a sandbox version, but prod uses live credentials.

**Debugging Steps:**
1. **Validate API Responses**
   - Compare test vs. prod responses:
     ```bash
     curl -v https://test-api.stripe.com/v1/payment_methods \
       -H "Authorization: Bearer test_..." |
       jq '.' > test-response.json

     curl -v https://api.stripe.com/v1/payment_methods \
       -H "Authorization: Bearer live_..." |
       jq '.' > prod-response.json
     ```
2. **Check for Deprecated Fields**
   ```javascript
   // Test might ignore 'id' but prod requires it
   const stripeResponse = await stripe.paymentMethods.list();
   if (!stripeResponse.data[0].id) {
     throw new Error('Missing required field: id');
   }
   ```

**Fix:**
- **Pin API versions** in code:
  ```javascript
  const stripe = require('stripe')(process.env.STRIPE_KEY, { apiVersion: '2023-08-16' });
  ```
- **Use API diff tools** like [Swagger Editor](https://editor.swagger.io/) to compare OpenAPI specs.

---

### **Issue 3: Database Schema Mismatch**
**Symptom:** *"Migration ran, but UI throws 'Column X does not exist'."*
**Root Cause:**
- Migration script was run on staging but not production.
- `ON UPDATE CASCADE` or `DEFAULT` constraints broke legacy queries.

**Debugging Steps:**
1. **Compare Schemas**
   ```sql
   -- Generate schema diff (PostgreSQL)
   \dx
   -- Or use a tool like Sqitch or Flyway
   ```
2. **Check for Unapplied Migrations**
   ```bash
   docker exec -it postgres psql -U postgres -c "
     SELECT migration_name, applied_at
     FROM migrations
     ORDER BY applied_at DESC;
   "
   ```

**Fix:**
- **Rollback and retry** migrations:
  ```bash
  # With Sqitch
  sqitch deploy --db postgres://user@localhost:5432/prod --to latest
  ```
- **Add schema validation** in tests:
  ```javascript
  const { checkSchema } = require('@mikro-orm/core');
  test('schema matches expected', async () => {
    const schema = await checkSchema(Entity);
    expect(schema).toMatchSnapshot();
  });
  ```

---

### **Issue 4: Environment Variable Leaks**
**Symptom:** *"Debug mode enabled in production."*
**Root Cause:**
- `DEBUG=true` or `SECRET_KEY` hardcoded in a Dockerfile.
- `.env` files committed to Git.

**Debugging Steps:**
1. **Audit Environment Variables**
   ```bash
   # Check running containers
   docker inspect <container> | jq '.Config.Env'
   ```
2. **Search for Secrets**
   ```bash
   grep -r "SECRET_" .
   git grep "password"
   ```

**Fix:**
- **Use secrets management** (AWS Secrets Manager, HashiCorp Vault):
  ```dockerfile
  ENV DEBUG=${DEBUG:-false}
  ```
- **Rotate secrets** immediately:
  ```bash
  kubectl delete secret my-app-secrets
  kubectl create secret generic my-app-secrets --from-literal=SECRET=$(new-secret)
  ```

---

### **Issue 5: Caching Layer Issues**
**Symptom:** *"Search results degrade over time."*
**Root Cause:**
- Cache key mismatch (e.g., missing `user_id` in key).
- TTL too short/long for the use case.

**Debugging Steps:**
1. **Inspect Cache Keys**
   ```bash
   redis-cli keys 'user:*'
   redis-cli get 'user:123:search'
   ```
2. **Check Cache Hits/Misses**
   ```javascript
   const { Redis } = require('ioredis');
   const redis = new Redis(process.env.REDIS_URL);
   const stats = await redis.info('stats');
   console.log('Keyspace hits:', stats.keyspace_hits);
   ```

**Fix:**
- **Design keys for uniqueness**:
  ```javascript
  const cacheKey = `user:${userId}:search:${searchQuery}:${sortBy}`;
  ```
- **Use cache invalidation patterns**:
  ```javascript
  // Invalidate when a new product is added
  redis.del(`products:search`);
  ```

---

## **4. Debugging Tools and Techniques**

| **Tool**               | **Use Case**                          | **Example Command**                          |
|------------------------|---------------------------------------|---------------------------------------------|
| **Postman/Insomnia**   | API contract validation               | `POST /checkout` with prod headers          |
| **Sentry**            | Error tracking in production          | `sentry.io` dashboard                         |
| **Docker Compose**    | Recreate exact production environment | `docker-compose -f docker-compose.prod.yml up` |
| **JWT Debugger**      | Inspect tokens                        | [jwt.io](https://jwt.io/)                  |
| **SQL Dumper**        | Compare DB states                     | `pg_dump -U postgres db_prod > prod.dump`     |
| **New Relic**         | Latency profiling                     | New Relic APM dashboard                       |
| **Git Bisect**        | Find when a regression was introduced | `git bisect start HEAD v1.0.0`               |

**Debugging Workflow for E2E Failures:**
1. **Reproduce in staging** → Use `docker-compose` or Terraform to spin up a staging clone.
2. **Compare logs** → `journalctl -u my-app` (Linux) or `kubectl logs`.
3. **Enable tracing** → Use OpenTelemetry or Datadog to trace requests end-to-end.
4. **Isolate the component** → Temporarily bypass external services (e.g., mock `Stripe`).

---

## **5. Prevention Strategies**

### **1. Shift Testing Left**
- **Add E2E checks to CI/CD**:
  ```yaml
  # GitHub Actions example
  - name: Run E2E tests
    run: |
      npm run test:e2e --env=production
  ```
- **Use feature flags** to toggle risky changes:
  ```javascript
  const isFeatureEnabled = require('flagsmith').get('new_checkout_flow');
  ```

### **2. Environment Parity**
- **Use Infrastructure as Code (IaC)** to ensure staging ≈ production:
  ```hcl
  # Terraform example
  module "db" {
    source = "./modules/postgres"
    env    = "production" # or "staging"
  }
  ```
- **Pin all dependencies** (including OS, Node.js, Docker versions):
  ```dockerfile
  FROM node:18.16.0-alpine
  ```

### **3. Observability**
- **Instrument all critical paths**:
  ```javascript
  const { trace } = require('opentelemetry');
  const activeSpan = trace.getActiveSpan();
  activeSpan?.addEvent('checkout_started');
  ```
- **Set up alerts** for E2E failure patterns:
  - High error rates on `/api/checkout`
  - Authentication failures > 0.1%

### **4. Automated Rollback**
- **Use blue-green deployments** or canary releases:
  ```bash
  # Kubernetes canary example
  kubectl set image deployment/my-app my-app=my-app:latest --record
  ```
- **Auto-rollback on failure**:
  ```yaml
  # Argo Rollouts example
  autoRollback:
    strategy: Recreate
    trigger: FailureThreshold(2)
  ```

### **5. Post-Mortem Culture**
- **Run retrospectives** after E2E failures:
  - What broke? (e.g., "Changed Stripe API version")
  - Why was it missed? (e.g., "No staging test for API changes")
  - How to prevent? (e.g., "Add API contract tests")
- **Document "gotchas"** in a `CONTRIBUTING.md` or Confluence page.

---

## **6. Cheat Sheet: Quick Fixes**
| **Symptom**               | **Immediate Fix**                          | **Long-Term Fix**                          |
|---------------------------|--------------------------------------------|--------------------------------------------|
| Login fails               | Reset auth token secrets                    | Use Vault for secrets management          |
| Payment gateway fails     | Check Stripe API version                   | Pin API version in code                   |
| DB errors                 | Run migration on staging → prod            | Add migration tests                        |
| Slow queries              | Add indexes, optimize queries              | Use query profiling (e.g., `EXPLAIN ANALYZE`) |
| Cache issues              | Clear cache, adjust TTL                    | Design keys for uniqueness                |
| Environment leaks         | Rotate secrets, audit configs              | Use GitHub Actions secrets                 |

---

## **7. Final Checklist Before Production**
Before merging to `main`:
- [ ] **E2E tests pass in staging** → `npm run test:e2e --env=staging`
- [ ] **Database schema matches** → `sqitch deploy --target production`
- [ ] **No `DEBUG` or `SECRET_*` in Dockerfiles** → `grep -r "DEBUG" .`
- [ ] **External API contracts validated** → Postman collection tests
- [ ] **Rollback plan documented** → `docs/deploy-rollback.md`

---
**Key Takeaway:**
End-to-end failures often stem from **environment drift**, not missing unit tests. Focus on **replicating production conditions** in staging and **instrumenting critical paths** for observability. Use **feature flags** and **canary deployments** to reduce blast radius.

**Further Reading:**
- [Google’s Site Reliability Engineering](https://sre.google/sre-book/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/) (Reliability Pillar)