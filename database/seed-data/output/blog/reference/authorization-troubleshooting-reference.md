# **[Pattern] Authorization Troubleshooting Reference Guide**

---

## **Overview**
Authorization troubleshooting ensures systems correctly validate permissions, preventing unauthorized access while minimizing false denials. This guide outlines systematic approaches to diagnose and resolve authorization failures, covering common failure modes (e.g., insufficient permissions, misconfigured policies, or role conflicts), technical validation techniques (logs, audits, and live testing), and best practices to streamline resolution. Whether dealing with a single request rejection or widespread policy misalignment, this pattern provides actionable steps to restore secure, compliant access control.

---

## **Implementation Details**

### **Key Failure Scenarios**
| Scenario               | Description                                                                                     | Root Cause                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **403 Forbidden**      | Client lacks required permissions for the resource/action.                                      | Missing role assignment, incorrect policy rules, or stale cache.                             |
| **500 Server Error**   | Authorization service failure (e.g., database errors, runtime exceptions).                      | Backend misconfiguration (e.g., missing dependencies, permissions tables corrupted).          |
| **Silent Failures**    | Requests proceed but lack proper enforcement (e.g., bypassed auth checks).                      | Misconfigured middleware, race conditions, or incomplete policy updates.                      |
| **Role Overlap**       | Conflicting roles grant conflicting permissions (e.g., `admin` vs. `view-only`).                | Unintended role inheritance or conflicting policies.                                           |
| **Policy Drift**       | Permissions misaligned with business requirements (e.g., outdated rules).                      | Lack of audits, manual edits, or automated policy sync failures.                            |

---

## **Diagnostic Workflow**

### **Step 1: Gather Context**
1. **Reproduce the Issue**
   - Log request details (HTTP method, path, headers, body, user context).
   - Example:
     ```json
     {
       "method": "POST",
       "path": "/api/users/5/create",
       "headers": {"Authorization": "Bearer invalid-token"},
       "user_id": "123",
       "timestamp": "2024-05-20T14:30:00Z"
     }
     ```
   - Use tools like `curl` or Postman to replicate failures.

2. **Check Logs**
   - **Backend Logs**: Look for authorization engine errors (e.g., `PermissionDeniedException`).
     ```log
     [ERROR] AuthorizationEngine: User 123 lacks permission 'create:user' (PolicyID: 42).
     ```
   - **Audit Trails**: Verify if the policy was updated recently (e.g., `PolicyUpdatedEvent`).

3. **Review Permissions**
   - Query the permissions database or auth store for the user’s assigned roles/permissions.
   - Schema reference below.

---

### **Step 2: Validate Infrastructure**
| Component          | Validation Steps                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------------|
| **Auth Service**   | Confirm service is running (e.g., `docker ps` for Kubernetes). Check for connection pools exhausted. |
| **Policy Store**   | Verify policy sync status (e.g., `GET /v1/policies/sync-status` returns `200`).                     |
| **Caching Layer**  | Check Redis/Memcached for stale cache (e.g., `redis-cli GET user:123:permissions`).                |
| **Middleware**     | Ensure auth middleware is enabled in the request pipeline (e.g., `Nginx` or `Express`).

---

### **Step 3: Test Permissions**
#### **Schema Reference**
| Entity            | Fields                                                                                         | Example Value                          |
|-------------------|-----------------------------------------------------------------------------------------------|----------------------------------------|
| **User**          | `id`, `username`, `roles` (array of role IDs), `last_login`, `status`                      | `{"id": "123", "roles": ["45", "67"]}`  |
| **Role**          | `id`, `name`, `permissions` (array of permission IDs), `inherits_from` (role ID)           | `{"id": "45", "permissions": ["1"]}`    |
| **Permission**    | `id`, `resource_type`, `action`, `description`                                                  | `{"id": "1", "resource_type": "user", "action": "create"}` |
| **Policy**        | `id`, `version`, `rules` (JSON schema defining conditions), `last_updated`                    | `{"rules": {"conditions": {"user.roles": ["45"]}}}`     |

#### **Query Examples**
1. **List User Permissions**
   ```sql
   -- SQL (Auth Database)
   SELECT p.id, p.resource_type, p.action
   FROM permissions p
   JOIN roles_permissions rp ON p.id = rp.permission_id
   JOIN roles r ON rp.role_id = r.id
   WHERE r.id IN (SELECT role_id FROM users_roles WHERE user_id = 123);
   ```

2. **Check Role Inheritance**
   ```bash
   # CLI (Example: Using Python)
   import requests
   response = requests.get("http://auth-service/v1/roles/45?recursive=true")
   print(response.json())  # Returns inherited roles/permissions
   ```

3. **Simulate a Request**
   ```bash
   # Using curl with mocked auth headers
   curl -X POST \
     http://api.example.com/users \
     -H "Authorization: Bearer <valid-token>" \
     -H "X-User-ID: 123" \
     -d '{"name": "Test"}'
   ```

---

### **Step 4: Resolve Issues**
| Issue Type               | Solution                                                                                           | Tools/Commands                                                                                  |
|--------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Missing Permission**   | Assign the required role/permission via admin dashboard or API.                                  | `PUT /v1/users/123/roles` (add role ID `45`).                                                 |
| **Policy Misconfiguration** | Update the policy (e.g., add a rule for the action).                                           | `PATCH /v1/policies/42` with new `rules` schema.                                              |
| **Cache Stale**          | Invalidate cache for the user: `redis-cli DEL user:123:permissions`.                            | Use `FLUSHDB` (caution: clears all cache).                                                     |
| **Auth Service Down**    | Restart the service or scale horizontally.                                                       | `kubectl rollout restart deployment/auth-service`.                                             |
| **Role Conflict**        | Audit conflicting roles (e.g., `admin` and `view-only`). Remove redundant roles.                 | `GET /v1/roles/conflicts` (custom endpoint).                                                   |

---

### **Step 5: Prevent Recurrence**
1. **Automated Audits**
   - Schedule regular policy validation (e.g., `cron` job running `python validate_policies.py`).
   - Example script:
     ```python
     def check_permissions():
         missing = []
         for role in roles:
             for perm in required_perms:
                 if perm not in role["permissions"]:
                     missing.append((role["id"], perm))
         return missing
     ```

2. **Testing**
   - **Unit Tests**: Mock auth checks (e.g., `jest` for Node.js or `pytest` for Python).
     ```javascript
     // Example: Testing permission check
     it("should deny create if role lacks permission", () => {
       const user = { roles: ["view-only"] };
       expect(hasPermission(user, "create:user")).toBe(false);
     });
     ```
   - **Integration Tests**: Use tools like **Postman** or **Gatling** to simulate traffic with varied permissions.

3. **Documentation**
   - Maintain a **permissions matrix** (e.g., CSV or Confluence page) mapping roles to resources/actions.
     Example:
     ```
     | Role      | Users | Orders | Products |
     |-----------|-------|--------|----------|
     | Customer  | Read  | Create | Read     |
     | Admin     | CRUD  | CRUD   | CRUD     |
     ```

---

## **Query Examples (Expanded)**
### **1. Check User Roles via API**
```bash
# REST API
curl -X GET \
  "http://auth-service/v1/users/123/roles" \
  -H "Authorization: Bearer admin-token"
# Response:
# [
#   {"id": "45", "name": "Editor"},
#   {"id": "67", "name": "Guest"}
# ]
```

### **2. Validate Policy Rules**
```bash
# GraphQL (if using a schema-based policy engine)
query {
  policy(id: "42") {
    rules {
      conditions {
        path
        operator
        value
      }
    }
  }
}
# Response:
# {
#   "policy": {
#     "rules": [
#       {
#         "conditions": [
#           {"path": "user.roles", "operator": "includes", "value": ["45"]}
#         ]
#       }
#     ]
#   }
# }
```

### **3. Debug a 403 Error**
1. **Extract the Policy ID** from logs:
   ```log
   [ERROR] PolicyEngine: PolicyID=42 failed for user=123
   ```
2. **Fetch the Policy**:
   ```bash
   curl -X GET \
     "http://auth-service/v1/policies/42" \
     -H "Authorization: Bearer admin-token"
   ```
3. **Compare with User Context**:
   ```bash
   # Cross-check user roles against policy rules
   curl -X GET "http://auth-service/v1/users/123" | jq '.roles'
   # Output: ["67"] (but policy requires ["45"])
   ```

---

## **Tools & Utilities**
| Tool              | Purpose                                                                                     |
|-------------------|---------------------------------------------------------------------------------------------|
| **Prometheus**    | Monitor auth service latency/errors (e.g., `auth_errors_total`).                          |
| **Grafana**       | Visualize permission denials over time.                                                   |
| **OpenPolicyAgent (OPA)** | Enforce policies at runtime (e.g., `opa eval --data file:/path/to/policy.rego`).       |
| **Loki**          | Aggregate auth logs for large-scale debugging.                                             |
| **PostHog**       | Track permission-related user flows (e.g., failed API calls).                             |

---

## **Related Patterns**
1. **[Authorization as a Service (AAaaS)]**
   - Centralize auth logic in a microservice for cross-team consistency.
   - *See*: [Pattern] AAaaS Reference Guide

2. **Least Privilege Enforcement**
   - Design roles with minimal permissions; audit regularly.
   - *See*: [Pattern] Least Privilege Reference Guide

3. **Policy as Code**
   - Use Infrastructure as Code (IaC) tools (e.g., Terraform) to manage policies.
   - *See*: [Pattern] Policy-as-Code Reference Guide

4. **Event-Driven Authorization**
   - Sync permissions via events (e.g., Kafka/Kinesis) to avoid cache inconsistencies.
   - *See*: [Pattern] Event-Driven Workflows Reference Guide

5. **Attribute-Based Access Control (ABAC)**
   - Extend beyond roles to dynamic attributes (e.g., `time_of_day`, `location`).
   - *See*: [Pattern] ABAC Reference Guide

---
**Note**: For enterprise-scale systems, combine this pattern with **Chaos Engineering** (e.g., simulate auth service failures to test resilience).