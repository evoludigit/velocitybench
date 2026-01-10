# **Debugging Multi-Tenancy Database Patterns: A Troubleshooting Guide**

## **Pattern Overview**
Multi-tenancy allows a single application instance to serve multiple customers (tenants) efficiently by sharing infrastructure while ensuring **logical isolation** between tenants. Common implementations include:

- **Schema-per-tenant** (each tenant gets a dedicated schema)
- **Row-level security (RLS)** (tenants share a schema but have row-level access controls)
- **Encryption-based isolation** (data is encrypted per tenant, stored in the same table)
- **Compartmentalized database** (a separate database instance per major tenant group)

---

## **Symptom Checklist**
Before diving into debugging, verify if the issue aligns with multi-tenancy concerns:

✅ **Data Leakage Issues**
- A tenant queries data outside their allowed scope.
- Sensitive data (e.g., financial records) is exposed to unauthorized users.

✅ **Performance Degradation**
- Slow queries despite low traffic (resource contention).
- High lock contention in shared database tables.

✅ **Deployment & Scaling Problems**
- Slow tenant onboarding due to manual schema/database creation.
- Hardcoded tenant identifiers in application code.

✅ **Concurrency & Consistency Issues**
- Race conditions when multiple tenants modify shared resources.
- Transaction isolation leading to dirty reads between tenants.

✅ **Authentication & Authorization Failures**
- Incorrect tenant context propagation (e.g., wrong tenant ID in queries).
- Missing row-level access controls.

---

## **Common Issues & Fixes**

### **1. Data Leakage Due to Missing Row-Level Security (RLS)**
**Symptoms:**
- A tenant queries records belonging to another tenant.
- SQL injection bypasses RLS checks.

**Root Cause:**
- Missing or misconfigured row-level policies.
- Dynamic SQL bypasses RLS (e.g., `EXECUTE IMMEDIATE`).

**Fix (PostgreSQL Example):**
```sql
-- Define a row-level policy to restrict access
CREATE POLICY tenant_policy ON accounts
    USING (tenant_id = current_setting('app.tenant_id')::uuid);
```

**Fix for Dynamic SQL (Application Code):**
```java
// Instead of raw SQL, use parameterized queries with tenant ID
String query = "SELECT * FROM accounts WHERE tenant_id = ?";
preparedStatement.setString(1, currentTenant.getId());
```

---

### **2. Slow Queries Due to Schema Contention**
**Symptoms:**
- Long-running `SELECT *` queries on shared tables.
- Lock waits (`pg_locks` shows blocking queries).

**Root Cause:**
- Missing proper indexing on tenant-filtered columns (e.g., `tenant_id`).
- Large result sets being fetched unnecessarily.

**Fix:**
```sql
-- Add an index on the tenant_id column
CREATE INDEX idx_accounts_tenant_id ON accounts(tenant_id);

-- Optimize queries to avoid full scans
SELECT * FROM accounts WHERE tenant_id = ? AND status = 'active';
```

**Debugging Query Performance:**
```sql
EXPLAIN ANALYZE SELECT * FROM accounts WHERE tenant_id = 'tenant123';
```
- Look for **Seq Scan** (full table scan) instead of **Index Scan**.

---

### **3. Tenant Context Leakage in Middleware**
**Symptoms:**
- Different tenants see each other’s sessions.
- Sticky sessions incorrectly assigned.

**Root Cause:**
- Session storage (Redis, database) not scoped per tenant.
- Missing tenant ID in API request context.

**Fix (Express.js Example):**
```javascript
// Middleware to set tenant context
app.use((req, res, next) => {
  const tenantId = req.headers['x-tenant-id'];
  req.tenantId = tenantId;
  next();
});

// Use in queries
const query = `SELECT * FROM accounts WHERE tenant_id = $1`;
connection.query(query, [req.tenantId]);
```

---

### **4. Schema-per-Tenant Migration Errors**
**Symptoms:**
- New tenant schemas fail to create during deployment.
- Data migration between schemas breaks.

**Root Cause:**
- Hardcoded schema names in queries.
- Missing schema permissions.

**Fix (Flyway Migration Script Example):**
```sql
-- Dynamic schema creation (if using schema-per-tenant)
CREATE SCHEMA IF NOT EXISTS tenant_${tenantId};

-- Grant necessary permissions
GRANT USAGE ON SCHEMA tenant_${tenantId} TO app_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA tenant_${tenantId} TO app_user;
```

**Debugging:**
- Check `pg_stat_user_tables` for missing schemas.
- Verify `GRANT` logs in `pg_audit` (if enabled).

---

### **5. Transaction Isolation Conflicts**
**Symptoms:**
- Phantom reads (data reappears after deletion).
- Dirty reads (uncommitted changes visible to other tenants).

**Root Cause:**
- Default `READ COMMITTED` isolation is too lenient.
- Missing tenant-aware locking.

**Fix (PostgreSQL):**
```sql
-- Set appropriate transaction isolation
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Use advisory locks for critical sections
SELECT pg_advisory_xact_lock(tenant_id);
```

---

## **Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Command**                     |
|--------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Database Profiling**   | Identify slow queries.                                                      | `EXPLAIN ANALYZE`                       |
| **Query Slower Than**    | Log queries above a threshold.                                              | `pg_stat_statements`                     |
| **Audit Logs**           | Track schema/RLS changes.                                                   | `pg_audit`                               |
| ** Tenant Context Check** | Verify tenant ID in requests.                                               | `SELECT current_setting('app.tenant_id')` |
| **Lock Monitoring**      | Detect blocking tenants.                                                    | `SELECT * FROM pg_locks;`                |

---

## **Prevention Strategies**

### **1. Enforce Least Privilege**
- **Database:** Grant minimal permissions per tenant (e.g., `USAGE` on schemas).
- **Application:** Use row-level policies (PostgreSQL) or column-level encryption.

### **2. Automate Tenant Setup**
- **Infrastructure as Code (IaC):** Use Terraform/Ansible to provision schemas.
- **Database Migrations:** Use Flyway/Liquibase for tenant-aware schemas.

### **3. Tenant-Aware Query Generation**
- **ORM Best Practice:** Always include `tenantId` in generated queries.
  ```java
  @Query("SELECT * FROM accounts WHERE tenant_id = :tenantId")
  ```
- **Avoid Dynamic SQL:** Prefer parameterized queries.

### **4. Monitoring & Alerts**
- **Monitor RLS Violations:** Log failed row-level policy checks.
- **Performance Alerts:** Warn if `pg_stat_statements` shows slow tenant queries.

### **5. Regular Audits**
- **Data Integrity Checks:** Verify no cross-tenant data exists.
  ```sql
  SELECT COUNT(*) FROM accounts WHERE tenant_id NOT IN (
      SELECT id FROM tenants WHERE active = true
  );
  ```

---

## **Final Checklist for Debugging**
Before escalating:
✔ Verify tenant ID is correctly propagated in all layers.
✔ Check if the issue is tenant-specific or global.
✔ Audit recent schema/policy changes.
✔ Review query execution plans for full scans.

---
**Next Steps:**
- If RLS is missing → **Add row-level policies**.
- If performance is bad → **Optimize indexes & queries**.
- If context leaks → **Fix middleware session handling**.

This guide ensures quick diagnosis and resolution of multi-tenancy issues while maintaining isolation and performance.