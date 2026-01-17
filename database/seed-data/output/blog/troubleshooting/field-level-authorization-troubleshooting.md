# **Debugging Field-Level Authorization (FLA): A Troubleshooting Guide**

## **Introduction**
Field-Level Authorization (FLA) ensures that users only see the fields they have permission to access in API responses. Misconfigured FLA can lead to data leaks, inconsistent behavior, or overly complex queries. This guide helps you diagnose and resolve common FLA issues quickly.

---

## **1. Symptom Checklist**
Before diving into fixes, verify these symptoms:

| Symptom | Likely Cause |
|---------|--------------|
| Users access fields they shouldn’t (e.g., `password`, `salary`) | Missing field-level permission checks |
| Different roles require separate query logic | FLA logic not role-aware |
| Performance issues with overly complex queries | Eager loading + FLA checks |
| API responses inconsistent across clients | Race conditions or static caching |
| Debug logs show no FLA-related filters applied | Missing middleware/API checks |

If multiple symptoms appear, prioritize **data leakage** (privacy risk) before performance or consistency issues.

---

## **2. Common Issues & Fixes**

### **Issue 1: Fields Leaking Through**
**Symptom:** Users can see restricted fields (e.g., `ssn`, `privateNotes`).

#### **Root Cause**
- Missing middleware/API-level filtering.
- Database query bypassing app-layer checks.

#### **Fix**
**Option A: Middleware Filtering (Recommended)**
Apply FLA in a middleware layer (e.g., Express, FastAPI, or Spring Security):
```javascript
// Express.js example
app.use((req, res, next) => {
  if (req.user.role === 'admin') return next(); // Skip filtering for admins

  // Example: Mask sensitive fields
  const filteredData = JSON.parse(JSON.stringify(req.body))
    .filter(field => !['password', 'ssn'].includes(field));
  req.body = filteredData;
  next();
});
```

**Option B: Database-Level Filtering (If App Layer is Untrusted)**
Use database triggers or row-level security (RLS) in Postgres:
```sql
-- PostgreSQL RLS example
ALTER TABLE employees POLICY allow_view
    USING (user_id = current_setting('app.current_user_id')::int OR role = 'admin');
```

**Option C: Client-Side Filtering (Last Resort)**
Only apply if server-side is compromised (e.g., in production with monitoring).

---

### **Issue 2: Complex Queries for Different Roles**
**Symptom:** Role A requires `select * from users`, but Role B needs only `select name, email from users`.

#### **Root Cause**
- Hardcoded queries per role.
- No dynamic schema projection.

#### **Fix**
Use **dynamic query building** with a permission map:
```typescript
// TypeScript example
interface RolePermissions {
  view: string[];
  edit: string[];
}

const rolePermissions: Record<string, RolePermissions> = {
  admin: { view: ['*'], edit: ['*'] },
  user: { view: ['name', 'email'], edit: ['name'] },
};

function buildQuery(userRole: string) {
  const allowedFields = rolePermissions[userRole].view;
  return allowedFields === ['*']
    ? 'SELECT * FROM users'
    : `SELECT ${allowedFields.join(', ')} FROM users`;
}
```

---

### **Issue 3: Performance Bottlenecks**
**Symptom:** Slow responses due to N+1 queries or excessive filtering.

#### **Root Cause**
- Field-level filters applied after loading all data.
- No batch processing for permission checks.

#### **Fix**
**A. Database Projections**
Restrict fields at the query level:
```sql
SELECT name, email FROM users WHERE role = 'user';
```

**B. Caching with Field-Level Granularity**
Use Redis to cache pre-filtered views:
```javascript
// Redis cache per role
const cacheKey = `user_data_${user.role}`;
const cachedData = await redis.get(cacheKey);
if (!cachedData) {
  const filteredData = await db.query(`SELECT ${allowedFields} FROM users`);
  await redis.set(cacheKey, filteredData, 'EX', 300); // 5 min TTL
}
```

---

### **Issue 4: Missing Logs for Debugging**
**Symptom:** No visibility into which fields were filtered.

#### **Root Cause**
- No logging middleware.
- Debugging relies on trial-and-error.

#### **Fix**
Add structured logging:
```javascript
// Express middleware
app.use((req, res, next) => {
  const originalBody = req.body;
  const filteredBody = deepFilterFields(originalBody, req.user.role);
  console.debug(
    { action: 'FLA Applied', original: originalBody, filtered: filteredBody },
    'Field-Level Authorization',
  );
  req.body = filteredBody;
  next();
});
```

**Tools:**
- Use `console.debug` (or `winston`/`pino` in production) to log before/after filtering.
- **Postman/Thunder Client:** Test with `curl -v` to inspect headers/requests.

---

## **3. Debugging Tools & Techniques**

### **Tool 1: API Request/Response Validation**
- **Postman/Newman:**
  Record requests with `field-level` headers and validate responses.
  Example:
  ```json
  {
    "headers": {
      "X-FLA-Roles": "user"
    }
  }
  ```
- **Swagger/OpenAPI:** Define `x-amazon-apigateway-integration` policies for field-level checks.

### **Tool 2: Database Query Logging**
Enable slow query logs and audit filters:
```sql
-- PostgreSQL
SET log_min_duration_statement = '100';
SET log_statement = 'all';
```

### **Tool 3: Unit/Integration Tests**
Test FLA logic with role-based assertions:
```javascript
// Jest example
test('User role should not see password field', async () => {
  const user = await db.query('SELECT * FROM users WHERE id = ?', [1]);
  expect(user.password).toBeUndefined(); // Should be masked
});
```

### **Tool 4: Static Analysis**
- **ESLint Plugin:** Detect missing `if (user.role)` checks.
- **TypeScript:** Enforce FLA types:
  ```typescript
  interface UserRole {
    read: string[];
    write: string[];
  }
  ```

---

## **4. Prevention Strategies**

### **1. Design-Time Checks**
- **Schema Enforcement:** Annotate fields with `@RestrictToRoles` in your ORM (e.g., TypeORM).
  ```typescript
  @Column({ select: false }) // Hide by default
  @RestrictToRoles(['admin'])
  private ssn: string;
  ```
- **Automated Policy Generation:** Use tools like **Open Policy Agent (OPA)** to auto-generate field-level rules.

### **2. Runtime Safeguards**
- **Input Sanitization:** Always validate `req.user.role` before applying filters.
- **Rate Limiting:** Throttle requests from users with elevated permissions (e.g., admins).

### **3. Audit Trails**
- Log all FLA violations to SIEM (e.g., Splunk, Datadog).
  ```javascript
  if (violationDetected) {
    await auditLog({
      event: 'Unauthorized Field Access',
      userId: req.user.id,
      fieldsAccessed: ['ssn'],
    });
  }
  ```

### **4. Documentation**
- **API Docs:** Clearly state which fields are restricted per role.
- **On-Call Slack:** Assign a team to respond to FLA-related incidents (e.g., data leaks).

---

## **5. Escalation Paths**
If issues persist:
1. **Verify Database Schema:** Ensure `ROW LEVEL SECURITY` is enabled (Postgres).
2. **Review IAM/RBAC:** Confirm no bypass via `SELECT *` grants.
3. **Test with Mock Users:** Simulate different roles in staging.

---

## **Final Checklist for FLA Implementation**
| Step | Action |
|------|--------|
| 1 | Map fields to roles in a config file. |
| 2 | Apply filters in middleware (before DB calls). |
| 3 | Unit-test edge cases (e.g., `role = null`). |
| 4 | Log violations for auditing. |
| 5 | Cache filtered responses where possible. |
| 6 | Monitor for unexpected field access. |

---
**Key Takeaway:** Field-level authorization is a **defensive layer**. Combine app-level, DB-level, and client-side checks for resilience. If in doubt, **deny by default** and log violations.