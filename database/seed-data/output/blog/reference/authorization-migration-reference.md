# **[Pattern] Authorization Migration: Reference Guide**

---

## **Overview**
The **Authorization Migration** pattern addresses the challenge of transitioning an application’s security model from legacy to modern authorization systems without disrupting functionality or user experience. This may involve moving from a traditional role-based access control (RBAC) system, custom in-house solutions, or OAuth with fixed scopes to a more flexible, attribute-based or identity-aware approach (e.g., ABAC, IAM, or fine-grained permissions).

Migrations are critical for modernizing security, scaling access controls efficiently, and integrating with identity providers or microservices architectures. This guide outlines key concepts, implementation schemas, query patterns, and best practices for a seamless migration.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     | **Use Case Example**                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Legacy System**       | Existing authorization infrastructure (e.g., hardcoded roles, legacy RBAC, or custom claims).    | A monolithic app with user roles (`ADMIN`, `EDITOR`) stored in a SQL table.          |
| **Target System**       | Modern framework (e.g., Open Policy Agent, Microsoft Entra External IDs, or fine-grained ABAC). | A microservice using JWT claims (`scopes: ["read:profile", "update:settings"]`).  |
| **Authorization Rule**  | Statement defining *who* (subject), *what* (resource), and *how* (action) access is granted.       | `ALLOW user:123, role:Editor FROM /api/content TO CREATE`                           |
| **Migration Strategy**  | Plan to translate legacy rules to target system syntax (e.g., mapping legacy roles to scopes).    | Converting `role:Admin` → `scope:admin:full` in JWT.                               |
| **Test Environment**    | Isolated space for validating rule translations before production deployment.                   | A staging instance mirroring production data but with no live user impact.         |
| **Grace Period**        | Overlap phase where both legacy and target systems operate temporarily.                           | Legacy RBAC runs alongside new ABAC until rollout completes.                       |

---

## **Schema Reference**
### **Legacy Authorization Schema (Source)**
| **Field**         | **Type**         | **Description**                                                                                     | **Example**                              |
|--------------------|------------------|---------------------------------------------------------------------------------------------------|------------------------------------------|
| `user_id`          | UUID             | Unique identifier for the user.                                                                   | `a1b2c3d4-e5f6-7890-g1h2-i3j4kl567890`   |
| `role`             | String           | Legacy role (e.g., `ADMIN`, `USER`).                                                              | `"SUPER_ADMIN"`                         |
| `permissions`      | Array[JSON]      | Hardcoded permissions as key-value pairs (e.g., `{"action":"read","resource":"user"}`).           | `[{ "action": "delete", "resource": "post" }]` |
| `deprecated`       | Boolean          | Flag marking entries for migration (default: `false`).                                           | `true`                                   |

**Table Name:** `legacy_access_controls`

---
### **Target Authorization Schema (Destination)**
| **Field**            | **Type**         | **Description**                                                                                     | **Example**                              |
|----------------------|------------------|---------------------------------------------------------------------------------------------------|------------------------------------------|
| `principal_id`       | UUID             | Subject identifier (user/group/application).                                                       | `a1b2c3d4-e5f6-7890-g1h2-i3j4kl567890`   |
| `scope`              | String           | Modernized permission scope (e.g., `organizations:read`, `billing:update`).                       | `"content:manage"`                       |
| `resource_id`        | UUID             | Unique identifier for the protected resource.                                                      | `x2y3z4a5-b6c7-8901-d2e3-f4g5h6i7j8k9l`   |
| `action`             | String           | CRUD operation or verb (e.g., `create`, `delete`, `audit`).                                       | `"audit"`                                |
| `effective_from`     | Timestamp        | Versioned timestamp for rule enforcement.                                                          | `2024-01-01T00:00:00Z`                  |

**Table Name:** `target_policies`

---

## **Migration Strategies**
### **1. Direct Mapping (Role → Scope)**
Convert legacy roles to target scopes with a static lookup table.
**Example:**
```sql
-- Legacy role: "SUPER_ADMIN" → Target scope: "admin:full"
INSERT INTO target_policies
SELECT
  user_id,
  'admin:full' AS scope,
  NULL AS resource_id,
  NULL AS action,
  NOW() AS effective_from
FROM legacy_access_controls
WHERE role = 'SUPER_ADMIN';
```

### **2. Permission Decomposition**
Break down legacy permissions into granular actions/resources.
**Example:**
```sql
-- Legacy permission: {"action":"delete","resource":"post"} → Target scope: "posts:delete"
INSERT INTO target_policies
SELECT
  user_id,
  CONCAT('posts:', action) AS scope,
  NULL AS resource_id,
  NULL AS action,
  NOW() AS effective_from
FROM legacy_access_controls
WHERE JSON_EXTRACT(permissions, '$[0].action') = 'delete'
  AND JSON_EXTRACT(permissions, '$[0].resource') = 'post';
```

### **3. Hybrid Phase (Parallel Rule Engine)**
Run both legacy and target systems in parallel, syncing decisions via middleware.
**Pseudo-code:**
```python
def authorize(request: Request):
    legacy_check = legacy_engine.check(request.user, request.resource)
    target_check = target_engine.check(request.user, request.resource)
    return legacy_check or target_check  # OR: use legacy_check until grace period ends
```

---

## **Query Examples**
### **1. Validate Legacy Users in Target System**
```sql
-- Check if a user's legacy role exists in target scopes
SELECT l.user_id, l.role, t.scope
FROM legacy_access_controls l
JOIN (
  SELECT DISTINCT user_id FROM target_policies
) t ON l.user_id = t.principal_id
WHERE l.role = 'USER';
```

### **2. Audit Migration Gaps**
```sql
-- Find legacy users missing target scopes
SELECT l.user_id, l.role
FROM legacy_access_controls l
WHERE NOT EXISTS (
  SELECT 1 FROM target_policies WHERE principal_id = l.user_id
);
```

### **3. Generate Migration Reports**
```sql
-- Count permissions per legacy role mapped to target scopes
SELECT
  l.role,
  COUNT(DISTINCT t.scope) AS scope_count,
  STRING_AGG(DISTINCT t.scope, ', ') AS scopes
FROM legacy_access_controls l
JOIN target_policies t ON l.user_id = t.principal_id
GROUP BY l.role;
```

### **4. Test Target Rule Enforcement**
```sql
-- Simulate a request against target policies (e.g., for `/api/content`)
SELECT
  t.principal_id,
  t.scope,
  CASE
    WHEN t.resource_id IS NULL THEN 'global'
    ELSE 'resource-specific'
  END AS policy_type
FROM target_policies t
WHERE t.scope LIKE '%content%'  -- Filter for content-related permissions
ORDER BY t.scope;
```

---

## **Implementation Steps**
1. **Inventory**
   - Audit legacy roles/permissions using:
     ```sql
     SELECT DISTINCT role, permissions FROM legacy_access_controls;
     ```
   - Document scope-to-action mappings.

2. **Develop Mapping Rules**
   - Use ETL tools (e.g., AWS Glue, custom scripts) to translate legacy data.
   - Example script (Python) to map permissions:
     ```python
     def legacy_to_scope(permission):
         action, resource = permission["action"], permission["resource"]
         return f"{resource}:{action}"
     ```

3. **Deploy Target System**
   - Deploy the target policy engine (e.g., OPA, Azure Policy) alongside legacy.
   - Configure middleware to log failures for auditing.

4. **Run Parallel Validation**
   - Use a **grace period** (e.g., 2 weeks) to:
     - Validate `legacy_check == target_check` for all requests.
     - Log discrepancies via middleware.

5. **Cutover**
   - Disable legacy system for new requests after validation.
   - Gradually phase out legacy database entries marked `deprecated = true`.

6. **Post-Migration**
   - Archive legacy data for compliance.
   - Update documentation with new authorization flow diagrams.

---

## **Error Handling & Fallbacks**
| **Scenario**               | **Solution**                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------|
| **Missing Target Scope**   | Fall back to legacy logic or reject with `403 Forbidden` (configured in middleware).           |
| **Permission Conflict**    | Apply least privilege: reject if legacy allows but target denies.                               |
| **Database Sync Lag**      | Use a queue (e.g., Kafka) to asynchronously sync policies.                                       |
| **Rollback Required**      | Re-enable legacy system via feature flag until target is fixed.                                  |

---

## **Related Patterns**
1. **Fine-Grained Authorization**
   - Complements migration by enabling dynamic, context-aware policies (e.g., ABAC).
   - *See:* [Fine-Grained Access Control Pattern](link).

2. **Delegated Authorization**
   - Offloads policy enforcement to a service (e.g., Auth0, Cognito) during migration.
   - *See:* [Delegated Access Pattern](link).

3. **Permission Elevation**
   - Temporarily grants higher privileges during cutover (e.g., `admin:override` scope).
   - *See:* [Emergency Access Pattern](link).

4. **Policy Versioning**
   - Tracks policy changes over time (e.g., with `effective_from` timestamps).
   - *See:* [Canonical Policy Pattern](link).

---

## **Tools & Libraries**
| **Purpose**               | **Tools**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------|
| **Policy As Code**        | Open Policy Agent (OPA), AWS IAM Policy Simulator, Azure Policy.                            |
| **ETL/Translation**       | Apache Spark, AWS Glue, custom Python scripts.                                               |
| **Middleware**            | Express.js middleware, Spring Security, AWS Lambda for request validation.                  |
| **Testing**               | Postman/Newman for API tests, OPA’s `opa eval` for policy validation.                        |
| **Observability**         | Datadog, Prometheus for tracking policy enforcement latency.                                 |

---

## **Best Practices**
- **Phase Migration**: Start with non-critical systems (e.g., admin panels) before core features.
- **Document Changes**: Maintain a change log (e.g., GitHub/GitLab issue) tracking scope mappings.
- **Automate Testing**: Use property-based testing (e.g., Hypothesis) to validate policy equivalence.
- **Monitor**: Alert on policy violations (e.g., `target_denied_but_legacy_allowed`).
- **Plan for Rollback**: Ensure legacy system can be reinstated if target fails.

---
**Note**: Adjust schemas and queries based on your database (e.g., replace `JSON_EXTRACT` with `->>` for PostgreSQL). For cloud-native migrations, refer to provider-specific docs (e.g., AWS IAM, GCP IAM).