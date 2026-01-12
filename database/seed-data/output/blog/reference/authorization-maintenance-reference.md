# **[Authorization Maintenance] Reference Guide**

---

## **Overview**
The **Authorization Maintenance** pattern ensures that access control rules (authorizations) remain synchronized with an application’s state, preventing inconsistencies between user permissions and system capabilities. This pattern is critical in multi-user, collaborative, or dynamic environments where permissions must adapt to changes in roles, entities, or system configurations.

Key use cases include:
- **RBAC (Role-Based Access Control):** Automating permission updates when roles change.
- **Dynamic Workflows:** Adjusting authorizations when tasks or objects are reassigned.
- **Audit & Compliance Tracking:** Maintaining an immutable record of permission changes for auditing.
- **Microservices Coordination:** Ensuring authorizations persist across services in distributed systems.

The pattern follows a **reactive** or **event-driven** model, where authorization rules are updated in real-time via triggers (e.g., role changes, policy overrides, or user activity logs). It avoids static "check-then-update" flaws by integrating authorization logic directly into workflows and data models.

---

## **Schema Reference**

| **Component**               | **Description**                                                                                                                                                                                                 | **Example Fields**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **Authorization Rule**      | Defines a structured permission (e.g., "read," "write"). Rules include constraints like scopes, time windows, or dependencies.                                                                       | `id`, `name` ("viewProject"), `type` ("read"), `scope` ("project:123"), `active` (boolean)              |
| **Role**                    | A named set of permissions (e.g., "Admin," "Editor"). Roles can inherit permissions from parent roles.                                                                                                      | `role_id`, `name`, `parent_role_id`, `permissions` (list of rule IDs)                                    |
| **Subject**                 | Entity requesting access (e.g., user, system service). Subjects may have custom attributes affecting permissions (e.g., `department`, `group_membership`).                                                  | `user_id`, `subject_type` ("user" or "service"), `custom_attrs` (map)                                   |
| **Trigger**                 | Event or condition that initiates an authorization update (e.g., role assignment, data modification). Triggers can be event-based (e.g., `user.updated`) or poll-based.                          | `type` ("roleUpdate"), `source` ("UserService"), `payload` (event data)                               |
| **Audit Log**               | Immutable record of permission changes for compliance and debugging. Includes timestamps, actors, and rule versions.                                                                                     | `log_id`, `timestamp`, `actor` (subject_id), `rule_id`, `old_value`, `new_value`                     |
| **Policy Override**         | Temporary or context-specific exceptions to rules (e.g., time-based access, exception requests). Overrides are validated against system policies.                                                              | `override_id`, `rule_id`, `subject_id`, `condition` (e.g., `"time:2024-05-01T00:00:00Z-2024-05-02T00:00:00Z"`) |
| **Authorization Service**   | Centralized system (or microservice) responsible for evaluating and maintaining rules. May integrate with identity providers (e.g., OAuth2, LDAP).                                                        | `service_uri`, `evaluation_method` ("JWT," "Attribute-Based"), `cache_ttl`                               |

---

## **Implementation Details**

### **1. Core Principles**
- **Separation of Concerns:**
  Authorization rules are decoupled from business logic. Changes to rules (e.g., via a UI) trigger updates without requiring code modifications.
- **Atomicity:**
  Updates to permissions are treated as transactions. If a rule change fails (e.g., due to a validation error), the system rolls back all related modifications.
- **Idempotency:**
  Authorization updates are designed to be retried safely. For example, reassociating a user with a role should not create duplicate entries.

### **2. Key Workflows**
#### **A. Role-Based Authorization Updates**
1. **Trigger:** A user’s role is changed (e.g., `user` entity updates `role_id` from `"editor"` to `"admin"`).
2. **Action:**
   - The system **evaluates** the new role’s permissions against the user’s existing rules.
   - **Overrides** are resolved (e.g., a time-bound exception for `"admin"` may restrict access to `"read_only"`).
   - **Audit logs** are created for the change.
3. **Result:**
   - The user’s effective permissions are recalculated, and the `Authorization Service` updates its cache.

#### **B. Entity-Specific Permissions**
1. **Trigger:** A project’s `visibility` setting is updated from `"internal"` to `"public"`.
2. **Action:**
   - The system **scans** all users with the `"viewProject"` role.
   - For each user, it **validates** if their permissions align with the new visibility (e.g., external users may lose access).
   - **Logs** are generated for affected users, and cached permissions are invalidated.

#### **C. Policy Overrides**
1. **Trigger:** A temporary override is requested for `user_id:42` to write to `project:123` during hours of `09:00–17:00`.
2. **Action:**
   - The system checks if the override conflicts with existing rules (e.g., the user lacks the `"write"` permission).
   - If approved, the override is **linked** to the user’s context (e.g., stored in a `PolicyOverride` table).
   - The `Authorization Service` dynamically evaluates permissions during runtime, prioritizing overrides.

### **3. Technical Considerations**
- **Caching:**
  Authorization results are cached (e.g., Redis) with TTLs to reduce latency. Invalidations are triggered by:
  - Direct updates (e.g., `PUT /roles/{id}`).
  - Event-based notifications (e.g., Kafka topics like `role.updated`).
- **Conflict Resolution:**
  For concurrent updates (e.g., two admins modifying the same role), use:
  - **Optimistic locking** (e.g., `version` field in the `Role` table).
  - **Pessimistic locking** for critical operations (e.g., database row locks).
- **Validation:**
  Rules must pass constraints before application:
  - **Syntax:** JSON Schema validation for rule definitions.
  - **Semantics:** Checks for circular dependencies (e.g., Role A inherits from Role B, which inherits from Role A).
  - **Data Integrity:** Foreign key checks (e.g., `role_id` must exist in the `Role` table).

### **4. Example Architecture**
```mermaid
graph TD
    A[Business App] -->|Triggers: Role Update| B[Event Bus]
    B --> C[Authorization Service]
    C -->|Evaluates Rules| D[Cache: Redis]
    C -->|Logs Changes| E[Audit DB]
    F[API Gateway] -->|Requests: "Can user:42 read project:123?"| C
    C -->|Response| F
```

---
## **Query Examples**

### **1. Retrieving a User’s Effective Permissions**
```sql
-- SQL (simplified)
SELECT
    r.name AS role_name,
    ar.name AS permission,
    ao.condition AS override_condition
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
LEFT JOIN auth_rules ar ON r.id = ar.role_id
LEFT JOIN policy_overrides ao ON ao.rule_id = ar.id AND ao.subject_id = u.id
WHERE u.id = 42;
```

**Equivalent in Python (with `authz-service` SDK):**
```python
from authz_service import AuthorizationService

service = AuthorizationService(cache_ttl=300)
permissions = service.get_subject_permissions(subject_id="42", scope="project:123")
print(permissions)  # Returns list of {"name": "viewProject", "active": True, "override": {"time": "..."}}
```

---

### **2. Updating a Role’s Permissions**
**Request (REST):**
```http
PATCH /api/v1/roles/123/permissions
{
  "add": ["editProject", "deleteProject"],
  "remove": ["viewProject"],
  "override": {
    "project:456": {
      "editProject": {
        "condition": "time:09:00-17:00",
        "actor": "admin@org.com"
      }
    }
  }
}
```

**Response (200 OK):**
```json
{
  "role_id": 123,
  "updated_permissions": ["editProject", "deleteProject"],
  "removed_permissions": ["viewProject"],
  "overrides_applied": 1,
  "audit_log_id": "abc123"
}
```

---

### **3. Listing Audit Logs for a Permission Change**
```http
GET /api/v1/audit/logs?rule_id=viewProject&subject_id=42
```

**Response:**
```json
[
  {
    "log_id": "def456",
    "timestamp": "2024-05-15T14:30:00Z",
    "actor": {
      "user_id": 101,
      "name": "Jane Doe"
    },
    "old_value": {"active": true},
    "new_value": {"active": false},
    "context": {
      "scope": "project:123",
      "reason": "Role reassigned to 'Viewer'"
    }
  }
]
```

---

### **4. Checking Permission via JWT Claims**
If the `Authorization Service` issues JWTs with embedded permissions:
```bash
# Decode a JWT (e.g., with jwt.io)
{
  "sub": "user:42",
  "roles": ["editor", "admin"],
  "permissions": {
    "project:123": ["viewProject"],
    "project:456": ["viewProject", "editProject"]
  },
  "exp": 1715750400
}
```

---

## **Related Patterns**

| **Pattern**                     | **Description**                                                                                                                                                     | **When to Use**                                                                                     |
|----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **[Attribute-Based Access Control (ABAC)]** | Grants access based on attributes (e.g., `department`, `time`, `environment`). Often used alongside Authorization Maintenance for dynamic constraints.       | When permissions depend on contextual factors (e.g., time-of-day, device type).                     |
| **[Policy as Code]**             | Defines authorization rules as machine-readable code (e.g., Open Policy Agent Rego). Integrates with Authorization Maintenance for declarative management.        | For complex, version-controlled policies requiring collaboration between devs and security teams.     |
| **[Event Sourcing]**             | Stores authorization changes as an append-only log. Authorizations are reconstructed by replaying events.                                                          | In systems requiring full audit trails or eventual consistency.                                      |
| **[Delegation Pattern]**         | Allows temporary permission transfer (e.g., a manager delegates a task to an employee). Integrates with Authorization Maintenance to update subject permissions. | For ad-hoc access delegation (e.g., project handoffs).                                             |
| **[Resource Owner Permissions]** | Users explicitly grant permissions to third-party apps. The pattern ensures these permissions are reflected in the Authorization Maintenance system.               | For OAuth2/OpenID Connect flows where external services need access.                               |
| **[Least Privilege Enforcement]** | Combines with Authorization Maintenance to ensure users only have permissions necessary for their tasks. Audits detect overprivileged roles.                    | For security-hardened applications (e.g., financial systems, healthcare).                            |

---

## **Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                                                                                     |
|---------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Stale Cached Permissions**          | Use short TTLs for cache (e.g., 5–15 minutes) and invalidate on rule changes.                                                                                     |
| **Permission Explosion**              | Group permissions into roles and use inheritance. Limit direct rule assignments.                                                                                   |
| **Circular Role Inheritance**        | Validate role graphs at runtime (e.g., detect cycles during role creation).                                                                                       |
| **Overriding Without Auditing**       | Log all overrides with actor and context. Require approval for non-temporary overrides.                                                                       |
| **Race Conditions in Concurrent Updates** | Use optimistic/pessimistic locking or event sourcing for conflict resolution.                                                                        |

---
## **Tools & Libraries**
| **Category**               | **Tools/Libraries**                                                                                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authorization Services** | Open Policy Agent (OPA), AWS IAM, Azure ABAC, Casbin, Google Zanzibar                                                                           |
| **Eventing**               | Kafka, RabbitMQ, AWS EventBridge, NATS                                                                                                               |
| **Caching**                | Redis, Memcached, HashiCorp Consul                                                                                                                   |
| **Audit Logging**          | ELK Stack (Elasticsearch, Logstash, Kibana), Splunk, AWS CloudTrail                                                                                  |
| **SDKs**                   | Auth0 JavaScript SDK, Firebase Admin SDK, Keycloak Python Client                                                                                     |