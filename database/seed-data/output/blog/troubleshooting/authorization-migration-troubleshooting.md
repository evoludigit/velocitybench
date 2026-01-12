# **Debugging Authorization Migration: A Troubleshooting Guide**

## **1. Introduction**
Authorization Migration refers to the process of transitioning from an older authorization system (e.g., role-based access control (RBAC), attribute-based access control (ABAC), or legacy JWT/OAuth flows) to a newer, more scalable, or secure system. Common migration patterns include:
- Migrating from **RBAC to ABAC**
- Transitioning from **legacy in-memory permissions** to a **database-backed policy engine**
- Replacing **JWT-based auth with OAuth2/OIDC**
- Integrating **fine-grained permissions** (e.g., Casbin, Open Policy Agent)

This guide provides a structured approach to diagnosing and resolving common issues during authorization migration.

---

## **2. Symptom Checklist**
Before diving into fixes, identify which symptoms match your situation:

| **Symptom** | **Possible Cause** |
|-------------|-------------------|
| **Unauthorized Access Granted** | - Policy misconfiguration<br>- Cache inconsistency<br>- Mismatched user/role data |
| **Permission Denied Errors** | - Incorrect policy rule syntax<br>- Missing resource/action definitions<br>- Database schema mismatch |
| **Performance Degradation** | - Slow policy evaluation (e.g., complex ABAC rules)<br>- Unoptimized database queries |
| **Login/Session Issues** | - Token validation failure (expired/JWT mismatch)<br>- Session store corruption |
| **Unexpected 403 Errors in Production** | - Deployment drift (dev vs. prod)<br>- Environment variable mismatches |
| **Logs Showing Conflicting Rules** | - Duplicate or conflicting policies<br>- Race conditions in policy updates |
| **High Latency in Policy Decisions** | - Inefficient rule matching (e.g., linear scan instead of indexed lookup) |

---

## **3. Common Issues & Fixes**
### **3.1. Unauthorized Access Granted (False Positives)**
**Symptom:** Users/roles with insufficient privileges can still access restricted resources.
**Root Causes:**
- Policy rules are too permissive.
- Mismatch between old and new role mappings.
- Cache or temporary state overriding policies.

**Debugging Steps:**
1. **Check Policy Rules**
   - Review the new policy engine’s rules (e.g., Casbin, OPA).
   - Example (Casbin RBAC → ABAC migration):
     ```plaintext
     # Old RBAC rule (too permissive)
     p, admin, /admin, read
     p, admin, /admin, write

     # New ABAC rule (requires additional attributes)
     p, alice, data, read, { "department": "engineering" }
     ```
   - **Fix:** Enforce stricter rules and validate with:
     ```bash
     casbin efm -p policy.conf -m models/rbac_model.conf
     ```
   - Use a rule validator like [Policy Validator](https://github.com/open-policy-agent/policy-validator).

2. **Verify Role-User Mapping**
   - Ensure the new system correctly maps legacy roles to new permissions.
   - Example fix (SQL query to reconcile roles):
     ```sql
     UPDATE users u
     SET new_permissions = (
         SELECT string_agg('data:' || perm.action, ',')
         FROM permissions p
         WHERE p.role_id = u.role_id
     )
     WHERE u.role_id IN (SELECT role_id FROM legacy_roles_migration);
     ```

3. **Clear Cache Inconsistencies**
   - If using a caching layer (Redis, Memcached), purge stale entries:
     ```bash
     redis-cli KEYS "policy:*" | xargs redis-cli DEL
     ```

---

### **3.2. Permission Denied Errors (False Negatives)**
**Symptom:** Users with correct permissions are blocked.
**Root Causes:**
- Incorrect policy syntax.
- Missing resource/action definitions.
- Database schema drift.

**Debugging Steps:**
1. **Validate Policy Syntax**
   - Test rules independently:
     ```bash
     # Casbin test
     casbin test -p policy.conf -m models/abac_model.conf

     # OPA test
     opa eval --data /path/to/policy.json \
       'data.policy.allow' \
       --input '{"user": "alice", "action": "read", "resource": "/data"}'
     ```
   - **Fix:** Correct syntax (e.g., ensure `p`/`e`/`m` rules are properly defined in Casbin).

2. **Check Resource/Action Definitions**
   - Example (OPA policy):
     ```rego
     # ❌ Missing action definition causes denials
     default allow = false

     allow {
       input.action == "read"
       input.user == "alice"
       input.resource == "/data"
     }
     ```
   - **Fix:** Ensure all actions/resources are covered:
     ```rego
     # ✅ Explicitly allow known actions
     allow {
       input.action in {"read", "write", "delete"}
       data.users[input.user].role == "admin"
     }
     ```

3. **Verify Database Schema**
   - Run migration checks:
     ```sql
     -- Check for orphaned records
     SELECT COUNT(*) FROM permissions
     WHERE resource NOT IN (SELECT resource_id FROM resources);
     ```

---

### **3.3. Performance Degradation**
**Symptom:** Policy evaluation takes >50ms (too slow for real-time access).
**Root Causes:**
- Linear rule scanning (O(n) complexity).
- Unoptimized database queries.
- Excessive caching misses.

**Debugging Steps:**
1. **Profile Policy Evaluation**
   - For Casbin: Use `casbin efm --profile`.
   - For OPA: Check runtime metrics:
     ```bash
     opa run --metrics-addr :8181
     ```
   - **Fix:**
     - **Index rules** (e.g., group similar actions):
       ```plaintext
       # Before (slow)
       p, alice, /admin, read
       p, alice, /admin, write

       # After (faster with prefix matching)
       p, alice, admin, *
       ```
     - **Use a policy index** (OPA):
       ```rego
       package policy
       default allow = false

       allow {
           input.resource[:3] == "api"
           input.action == "read"
       }
       ```

2. **Optimize Database Queries**
   - Add indexes:
     ```sql
     CREATE INDEX idx_permissions_user ON permissions(user_id);
     CREATE INDEX idx_permissions_action ON permissions(action);
     ```

---

### **3.4. Login/Session Issues**
**Symptom:** Users cannot authenticate or sessions expire unexpectedly.
**Root Causes:**
- Token validation mismatch (old vs. new JWT/OIDC claims).
- Session store corruption.
- Clock skew in token expiration.

**Debugging Steps:**
1. **Compare JWT Claims**
   - Old system (legacy):
     ```json
     {
       "sub": "alice",
       "roles": ["admin", "user"],
       "exp": 1735689600
     }
     ```
   - New system (OIDC):
     ```json
     {
       "sub": "alice",
       "permissions": ["data:read:*"],
       "iat": 1735689600,
       "exp": 1735776000
     }
     ```
   - **Fix:** Update claim mapping in the new auth service.

2. **Check Session Store**
   - Verify Redis/MongoDB session consistency:
     ```bash
     redis-cli KEYS "sess:*" | wc -l  # Count active sessions
     ```
   - **Fix:** Rebuild sessions if corrupted:
     ```python
     # Example using Flask-Session
     with app.app_context():
         db.session.query(Session).delete()
         db.session.commit()
     ```

3. **Synchronize Clock**
   - Ensure all servers use NTP (e.g., `ntpdate pool.ntp.org`).

---

### **3.5. Unexpected 403 Errors in Production**
**Symptom:** Errors appear after deployment but not in staging.
**Root Causes:**
- Environment variable mismatches.
- Policy file differences.
- A/B testing or canary deployment drift.

**Debugging Steps:**
1. **Compare Configs**
   - Use `diff` to compare policy files:
     ```bash
     diff /prod/policy.conf /staging/policy.conf
     ```
   - **Fix:** Deploy the correct config.

2. **Enable Debug Logging**
   - Casbin:
     ```plaintext
     [log]
     log_level = debug
     ```
   - OPA:
     ```bash
     opa run --log-level=debug
     ```

3. **Check Canary Traffic**
   - If using gradual rollouts, isolate the affected traffic:
     ```bash
     kubectl rollout status deployment/auth-service --watch
     ```

---

## **4. Debugging Tools & Techniques**
| **Tool**               | **Use Case**                                  | **Example Command**                          |
|------------------------|----------------------------------------------|---------------------------------------------|
| **Casbin `efm`**       | Evaluate and validate policies               | `casbin efm -p policy.conf -m model.conf`   |
| **OPA `eval`**         | Test Rego policies                           | `opa eval --data policy.json 'allow'`       |
| **Prometheus + Grafana** | Monitor policy latency                       | `rate(opa_evaluation_duration_seconds[5m])` |
| **Redis CLI**          | Inspect cached policies                      | `redis-cli GET "policy:alice"`              |
| **Postman/Newman**     | Fuzz-test policy boundaries                  | `newman run auth_migration.postman_collection.json` |
| **Chaos Engineering**  | Test failure modes (e.g., policy DB down)   | `kill -9 $(pgrep nginx)`                    |

**Techniques:**
- **Shadow Testing:** Run old and new auth in parallel.
- **Chaos Mesh:** Simulate network partitions.
- **Policy Auditing:** Use tools like [OpenPolicyAgent Auditor](https://www.openpolicyagent.org/docs/latest/audit/).

---

## **5. Prevention Strategies**
### **5.1. Pre-Migration Checklist**
| **Task**                          | **Tool/Action**                              |
|-----------------------------------|---------------------------------------------|
| Audit old policies                | `casbin efm` / `opa eval`                   |
| Back up legacy auth data          | `pg_dump auth_db`                            |
| Unit test new policy rules        | `pytest` (with `casbin-py`/`opa-python`)    |
| Load test with production traffic | `locust -f auth_migration.locustfile.py`     |

### **5.2. Deployment Best Practices**
- **Feature Flags:** Enable new auth incrementally.
- **Canary Releases:** Route 5% of traffic to the new system.
- **Rollback Plan:** Maintain the old system for 24h post-migration.

### **5.3. Monitoring & Alerts**
- **SLOs:** Track `p99` policy evaluation latency (<100ms).
- **Alerts:**
  - `1m` 403 errors per endpoint.
  - Policy cache misses >1% of requests.
- **Example Prometheus Alert:**
  ```yaml
  - alert: HighPolicyLatency
    expr: histogram_quantile(0.99, sum(rate(opa_evaluation_seconds_bucket[5m])) by (le)) > 0.2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Policy evaluation slow ({{ $value }}s)"
  ```

### **5.4. Documentation**
- Maintain a **decision log** (e.g., GitHub issue) for policy changes.
- Document **breakage points** (e.g., "Role X → Permission Y was removed").

---

## **6. Conclusion**
Authorization migration is high-risk but manageable with:
1. **Symptom-driven debugging** (start with logs, then policies).
2. **Incremental testing** (shadow deployments).
3. **Performance profiling** (OPA/Casbin metrics).
4. **Prevention** (SLOs, canary releases).

**Final Checklist Before Going Live:**
✅ All policies are tested in staging.
✅ Canary traffic shows no 403 spikes.
✅ Rollback procedure is documented.
✅ Monitoring alerts are configured.

By following this guide, you can resolve authorization migration issues efficiently and minimize downtime.