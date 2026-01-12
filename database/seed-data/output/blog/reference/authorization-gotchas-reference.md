**[Pattern] Reference Guide: Authorization Gotchas**

---

### **Overview**
Authorization patterns are designed to ensure secure access control while preventing misconfigurations, logic errors, or unintended permissions. However, even well-designed systems can fall prey to subtle bugs—**authorization gotchas**—that undermine security. This guide catalogs common pitfalls, their causes, and mitigation strategies to help developers and architects avoid costly vulnerabilities (e.g., privilege escalation, data leaks, or bypasses). Gotchas span **OAuth 2.0 scopes**, **role-based access control (RBAC)**, **attribute-based access control (ABAC)**, and application logic. Proactively identifying these issues improves resilience and reduces attack surfaces.

---

### **1. Schema Reference**
| **Gotcha Category**       | **Description**                                                                                     | **Common Causes**                                                                                     | **Mitigation Strategies**                                                                                       |
|---------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Scope Mismatches**       | Incorrect OAuth 2.0 scope usage (overly permissive, missing granularity, or misconfigured).         | Poor API designer scope selection; client libraries defaulting to broad scopes.                     | Enforce [scope modularity](https://datatracker.ietf.org/doc/html/rfc6749#section-3.3) (e.g., `read:profile` vs. `read:all`). Use [OAuth 2.1](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-03) for stricter controls. |
| **RBAC Over-Provisioning** | Roles grant excessive permissions (e.g., "Superadmin" for low-risk actions).                         | Static role definitions; lack of least-privilege enforcement.                                          | Implement **tiered roles** (e.g., `admin:canonical`, `admin:legacy`) and audit tools like [Open Policy Agent](https://www.openpolicyagent.org/). |
| **Dynamic Authorization**  | Logic flaws in dynamic checks (e.g., race conditions, cached decisions, or context mismatches).      | Asynchronous workflows; hardcoded logic bypassing dynamic checks.                                      | Validate context (e.g., `request.time < cache.ttl`) and use **idempotent checks**. Prioritize [ABAC](https://tools.ietf.org/html/rfc8324) for dynamic rules. |
| **Silent Permission Escalation** | Privileges escalate silently due to unchecked implicit grants (e.g., "session hijacking" via tokens). | Token refresh without re-authentication; session scope expansion.                                     | Enforce [short-lived tokens](https://oauth.net/2/tokens/) + [refresh token rotation](https://datatracker.ietf.org/doc/html/rfc6749#section-1.5). Use [Proxy Rewriting](https://tools.ietf.org/html/draft-ietf-oauth-v2-proxy-05) for scopes. |
| **Data Leakage via Queries** | Queries expose unauthorized data (e.g., SQL injection, excessive `SELECT *`).                       | Poor query composition; client-side filtering ignored.                                                 | Validate query inputs (e.g., [PostgreSQL’s `jsonb`](https://www.postgresql.org/docs/current/functions-json.html) for structured data). Use **row-level security** (RLS) policies. |
| **Circumvention via Metadata** | Attackers exploit hidden attributes (e.g., `X-API-Key` in headers over OAuth scopes).               | Over-reliance on legacy auth methods; metadata leakage.                                                 | Replace metadata headers with [OAuth2’s `Authorization` header](https://datatracker.ietf.org/doc/html/rfc6750). Audit all headers with tools like [Burp Suite](https://portswigger.net/burp). |
| **Time-Based Access**       | Time-sensitive permissions (e.g., "active only during office hours") are misconfigured.             | Hardcoded time zones; lack of timezone-aware logic.                                                     | Store permissions in UTC; use libraries like [Joda-Time](https://www.joda.org/joda-time/) for time handling. |
| **Indirect Permission Grants** | Users grant permissions indirectly (e.g., "delegate" or "share" actions).                          | Third-party integrations (e.g., linked accounts).                                                       | Enforce [proxy consent](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-linked-data-00) for shared access. |
| **Dependency Vulnerabilities** | External auth libraries (e.g., JWT parsers) have critical flaws.                                    | Outdated libraries; missing updates.                                                                    | Pin dependencies (e.g., `jjwt:0.11.5`); use [OWASP’s Dependency-Check](https://owasp.org/www-project-dependency-check/). |
| **Closed World Assumptions** | Systems assume all users/roles are explicitly defined (breaks when new roles are added).             | Static permission lists; no dynamic role mapping.                                                        | Adopt **open-world** principles (default to deny unless explicitly granted). Use [Policy as Code](https://www.openpolicyagent.org/docs/latest/policy-as-code/). |

---

### **2. Query Examples**
#### **✅ Correct Usage (Mitigated Gotchas)**
**OAuth 2.0 Scope Granularity (Avoiding Over-Permission):**
```http
GET /api/user/123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Scopes: "profile:read user:metadata"  # Explicitly limits access
```

**ABAC Dynamic Check (Time-Window Validation):**
```python
# Pseudocode: Check if request coincides with "business hours"
if request.timezone == "UTC" and now.isoweekday() in [1, 2, 3, 4, 5] and 9 <= now.hour <= 17:
    allow()
else:
    deny()
```

**SQL Query with Row-Level Security (Preventing Data Leakage):**
```sql
-- PostgreSQL RLS policy to restrict user data access
CREATE POLICY user_data_policy ON orders
    USING (user_id = current_setting('app.current_user_id')::uuid);
```

---

#### **❌ Incorrect Usage (Gotchas Triggered)**
**Scope Mismatch (Overly Permissive):**
```http
-- Client requests broad scope despite only needing `profile:read`
GET /api/user/123
Authorization: Bearer ...
Scopes: "openid profile email"  # Should be scoped to minimal requirements
```

**Race Condition in Dynamic Auth (Bypassed Check):**
```python
# User A requests token, then B intercepts it before validation
def issue_token(user_id):
    token = generate_token(user_id)  # No immediate revocation
    return token
```

**Metadata Bypass (Abusing Headers):**
```http
-- Attacker mimics OAuth with a hardcoded API key
GET /api/admin/dashboard
X-API-Key: admin123  # Bypasses OAuth scopes entirely
```

---

### **3. Implementation Details**
#### **Key Concepts**
1. **Least Privilege Principle**:
   - Grant minimal permissions required for a task (e.g., a "blog editor" shouldn’t edit user profiles).
   - *Tooling*: Use [AWS IAM Policy Simulator](https://aws.amazon.com/premiumsupport/knowledge-center/iam-policy-simulator/) to test permissions.

2. **Defense in Depth**:
   - Combine OAuth scopes, ABAC, and application logic checks to layer security.

3. **Audit Trails**:
   - Log all permission denials/revocations (e.g., using [ELK Stack](https://www.elastic.co/elasticsearch/)).

4. **Tooling**:
   - **Static Analysis**: [OWASP ZAP](https://www.zaproxy.org/) to scan for scope leaks.
   - **Runtime Monitoring**: [Falco](https://falco.org/) for runtime permission anomalies.

#### **Gotcha-Specific Workarounds**
| **Gotcha**               | **Workaround**                                                                                     |
|--------------------------|----------------------------------------------------------------------------------------------------|
| **Silent Escalation**    | Enforce [token blacklisting](https://auth0.com/docs/tokens/session-management/token-revocation) on logout. |
| **Data Leakage**         | Use [column-level security](https://learn.microsoft.com/en-us/sql/relational-databases/security/column-level-security) in DBs. |
| **Time-Based Issues**    | Store permissions as UTC timestamps; use [cronjobs](https://crontab.guru/) for automated revokes.   |
| **Dependency Bugs**      | Automate updates via [Renovate](https://docs.renovatebot.com/) and scan with [Snyk](https://snyk.io/). |

---

### **4. Query Examples (Edge Cases)**
#### **ABAC Rule for Cost Sensitivity**
```json
// Policy: Allow user to edit if their plan >= "pro"
{
  "user": {
    "id": "123",
    "plan": "premium"
  },
  "action": "edit_post",
  "resource": {
    "type": "blog_post",
    "id": "456"
  },
  "allowed": true
}
```

#### **PostgreSQL RLS for Multi-Tenant Apps**
```sql
-- Only allow tenant A to access their data
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_policy ON orders USING (tenant_id = current_setting('app.active_tenant'));
```

---

### **5. Related Patterns**
| **Related Pattern**               | **Connection to Gotchas**                                                                          |
|------------------------------------|---------------------------------------------------------------------------------------------------|
| **[Permission Elevation](https://docs.oasis-open.org/ws-tx/wstx-ws-secureconversation-1.4-cs-01.pdf)** | Gotchas often stem from improper elevation checks (e.g., "modes" in WSTX).                       |
| **[Attribute-Based Access Control (ABAC)](https://tools.ietf.org/html/rfc8324)** | ABAC mitigates dynamic gotchas (time, location, etc.) but requires careful rule design.        |
| **[Token Revocation](https://datatracker.ietf.org/doc/html/rfc7009)** | Critical for mitigating silent escalation; gotchas arise from delayed revocation.              |
| **[Zero Trust Architecture](https://wwwzero.trust/)** | Gotchas are reduced by assuming breach; enforce least privilege + micro-segmentation.          |
| **[Policy as Code](https://www.openpolicyagent.org/)** | Helps automate gotcha detection (e.g., scope mismatches) via static analysis.                    |

---
**Note**: This guide assumes familiarity with OAuth 2.0, RBAC, and basic SQL. For deeper dives, refer to:
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/rfc8252)
- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)