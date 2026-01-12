# **[Authorization Patterns] Reference Guide**

---

## **Overview**
The **Authorization Patterns** reference guide outlines standardized approaches for implementing fine-grained access control in systems. Authorization determines whether an authenticated user is permitted to perform specific actions on resources based on predefined policies. This guide covers key concepts, implementation details, schema references, and query examples for common authorization patterns, including **Attribute-Based Access Control (ABAC)**, **Role-Based Access Control (RBAC)**, **Policy-Based Access Control (PBAC)**, and **Entitlement-Based Access Control (EnBaC)**. Organizations use these patterns to enforce security policies dynamically while maintaining scalability and flexibility.

---

## **1. Key Concepts**
Authorization patterns rely on four core components:

| **Component**       | **Description**                                                                 |
|----------------------|---------------------------------------------------------------------------------|
| **Subject**          | The entity (user, service, device) requesting access.                          |
| **Resource**         | The data, operation, or system component being accessed.                       |
| **Action**           | The permitted operations (e.g., `read`, `write`, `delete`).                   |
| **Environment**      | Contextual factors (e.g., time, location, device type) influencing access.     |
| **Policy**           | Rules governing access decisions.                                              |
| **Policy Engine**    | Evaluates policies against requests to grant/reject access.                   |
| **Policy Store**     | Repository (database, file, or registry) storing policy definitions.          |

---
## **2. Implementation Details**
### **2.1 Common Authorization Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                          |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------|
| **RBAC (Role-Based)**     | Access granted based on assigned roles (e.g., `admin`, `editor`).               | Simple hierarchical permissioning.    |
| **ABAC (Attribute-Based)**| Access granted based on attributes (e.g., `user.department = "Finance"`).     | Dynamic, context-aware policies.      |
| **PBAC (Policy-Based)**   | Access governed by external policy rules (e.g., GDPR compliance).              | Regulatory or domain-specific rules.  |
| **EnBaC (Entitlement-Based)** | Access defined by explicit permissions (e.g., `read:project:123`).        | Granular, permission-centric access. |
| **Hybrid (RBAC + ABAC)**  | Combines roles and attributes for flexibility.                                 | Complex workflows with contextual needs. |

### **2.2 Technical Considerations**
- **Policy Evaluation Order**:
  Policies are evaluated in sequence. Rules with higher specificity (e.g., `action=delete`) take precedence over broader rules.
- **Performance**:
  For high-throughput systems, use **caching** (e.g., Redis) for policy evaluations or **indexed queries** in policy stores.
- **Audit Logging**:
  Log all authorization decisions (success/failure) for compliance (e.g., `user:john_doe, action:delete, resource:/data/file.txt, result:denied`).
- **Dynamic Policies**:
  Use event-driven systems (e.g., Kafka) to update policies in real-time (e.g., revoking access when a user’s `is_active` flag changes).

---

## **3. Schema Reference**
### **3.1 Core Schema: Policy Definition**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": { "type": "string", "description": "Unique policy identifier (e.g., 'delete_project:xyz')" },
    "subject": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["user", "service", "group"] },
        "value": { "type": "string" }
      },
      "required": ["type", "value"]
    },
    "resource": {
      "type": "object",
      "properties": {
        "type": { "type": "string" },
        "id": { "type": "string" },
        "path": { "type": "string" }
      },
      "required": ["type"]
    },
    "action": { "type": "array", "items": { "type": "string" } },
    "condition": {
      "type": "object",
      "properties": {
        "environment": { "type": "object" },  // e.g., { "time": "before 2023-12-31" }
        "attributes": { "type": "object" }     // e.g., { "department": "Finance" }
      }
    },
    "effect": { "type": "string", "enum": ["allow", "deny"] },
    "priority": { "type": "integer" }         // Higher numbers take precedence
  },
  "required": ["id", "subject", "resource", "action", "effect"]
}
```

### **3.2 Example Policy Store Tables**
| **Table**               | **Columns**                                  | **Description**                          |
|-------------------------|---------------------------------------------|------------------------------------------|
| `policies`              | `id` (PK), `subject_type`, `subject_value`, `resource_type`, `resource_id`, `action`, `condition_json`, `effect`, `priority` | Stores policy rules.                     |
| `subject_attributes`    | `subject_id` (FK), `key`, `value`           | Dynamic subject attributes (e.g., `department`). |
| `resource_attributes`   | `resource_id` (FK), `key`, `value`          | Dynamic resource attributes.             |

---

## **4. Query Examples**
### **4.1 Evaluating a Policy Request**
**Request:**
```json
{
  "subject": { "type": "user", "value": "john_doe" },
  "resource": { "type": "project", "id": "123" },
  "action": "delete"
}
```

**Query (SQL-like pseudocode):**
```sql
SELECT effect
FROM policies
WHERE
  subject_type = 'user' AND subject_value = 'john_doe' AND
  resource_type = 'project' AND resource_id = '123' AND
  action = 'delete' AND
  (
    -- ABAC condition: user must be in Finance department
    JSON_CONTAINS(subject_attributes.value, '{"department": "Finance"}') OR
    -- Default deny for non-admins
    subject_value NOT IN (SELECT value FROM subject_attributes WHERE key = 'role' AND value = 'admin')
  )
ORDER BY priority DESC
LIMIT 1;
```

**Result:** `deny` (due to missing `Finance` department attribute).

---

### **4.2 Dynamic Policy Update (Event-Driven)**
**Event:** User’s department changed to `Finance` via API.
**Update Query:**
```sql
UPDATE subject_attributes
SET value = '{"department": "Finance"}'
WHERE subject_id = 'john_doe'
AND key = 'department';
```

**Re-evaluation:**
Now, the same request returns `allow`.

---

### **4.3 Hybrid RBAC + ABAC Example**
**Policy Rules:**
1. **Role-based:** `admin` role allows `delete` on all resources.
2. **Attribute-based:** Users in `Finance` can `delete` only their own projects.

**Query:**
```sql
-- Check if user has 'admin' role OR (Finance AND owns project)
SELECT
  CASE
    WHEN EXISTS (SELECT 1 FROM subject_attributes WHERE subject_id = 'john_doe' AND key = 'role' AND value = 'admin')
    THEN 'allow'
    WHEN EXISTS (
      SELECT 1 FROM subject_attributes sa
      JOIN resource_attributes ra ON sa.subject_id = ra.resource_id
      WHERE sa.subject_id = 'john_doe' AND sa.key = 'department' AND sa.value = 'Finance'
      AND ra.key = 'owner' AND ra.value = 'john_doe'
    )
    THEN 'allow'
    ELSE 'deny'
  END AS effect;
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------|
| **[Authentication Patterns]** | Verifies identity (e.g., OAuth 2.0, JWT).                                      | Precedes authorization.                   |
| **[Audit Logging]**       | Records access attempts for compliance.                                       | Required for regulatory audits.          |
| **[Least Privilege]**     | Grants minimum permissions for tasks.                                          | Reduces attack surface.                  |
| **[Temporal Policies]**   | Restricts access by time/date (e.g., read-only weekends).                      | Time-sensitive access.                   |
| **[Attribute Enrichment]**| Dynamically adds context (e.g., IP, device type) to policies.                  | Context-aware security.                  |

---
## **6. Best Practices**
1. **Separation of Concerns**:
   - Store policies separately from business logic.
   - Use a dedicated policy engine (e.g., [Open Policy Agent (OPA)](https://www.openpolicyagent.org/)).
2. **Immutable Policies**:
   - Avoid runtime policy modifications unless critical (prefer event-driven updates).
3. **Policy Testing**:
   - Test edge cases (e.g., overlapping rules, attribute conflicts) with tools like [Policy Simulator](https://github.com/open-policy-agent/policy-simulator).
4. **Documentation**:
   - Maintain a **policy registry** with human-readable descriptions of each rule.
5. **Scalability**:
   - For microservices, use **distributed policy stores** (e.g., Redis, etcd) with eventual consistency.

---
## **7. Tools & Frameworks**
| **Tool**                  | **Type**               | **Use Case**                          |
|---------------------------|------------------------|---------------------------------------|
| [Open Policy Agent (OPA)](https://www.openpolicyagent.org/) | Policy Engine | ReReusability across services.        |
| [AWS IAM](https://aws.amazon.com/iam/) | Managed RBAC | Cloud-based permissioning.           |
| [Zitadel](https://zitadel.com/) | Identity + Policy | Unified identity and access control. |
| [Casbin](https://casbin.org/) | Policy Enforcement | Lightweight, supports ABAC/RBAC.     |
| [Stratus](https://github.com/stratus-security/stratus) | Policy Orchestrator | Multi-cloud policy enforcement.       |

---
## **8. Troubleshooting**
| **Issue**                          | **Diagnosis**                                  | **Solution**                              |
|-------------------------------------|-----------------------------------------------|-------------------------------------------|
| **Permission Denied**               | Policy evaluation returns `deny`.             | Check conditions, subject/resource attributes, or priority. |
| **Policy Conflicts**                | Multiple rules apply; precedence unclear.      | Review `priority` field or merge rules.   |
| **Performance Bottlenecks**         | Slow policy lookups.                          | Add indexes, cache frequent queries.      |
| **Dynamic Attribute Delays**        | Attributes not updated in real-time.          | Use event sinks (e.g., Kafka) to sync.    |

---
## **9. Example Walkthrough: ABAC Implementation**
### **Scenario**
Grant `read` access to project files only to users in the `Finance` department.

### **Steps**
1. **Define Policy**:
   ```json
   {
     "id": "read_project:finance",
     "subject": { "type": "user", "value": "{user_id}" },
     "resource": { "type": "project", "id": "{project_id}" },
     "action": ["read"],
     "condition": {
       "attributes": { "department": "Finance" }
     },
     "effect": "allow",
     "priority": 100
   }
   ```
2. **Store Attributes**:
   - `subject_attributes`: `{"user_id": "john_doe", "key": "department", "value": "Finance"}`
3. **Evaluate Request**:
   ```sql
   SELECT effect FROM policies
   WHERE subject_type = 'user' AND subject_value = 'john_doe'
     AND resource_type = 'project' AND resource_id = '456'
     AND action = 'read'
     AND JSON_CONTAINS(condition, '{"attributes": {"department": "Finance"}}');
   ```
   **Result:** `allow`.

---
## **10. Glossary**
| **Term**               | **Definition**                                  |
|------------------------|-------------------------------------------------|
| **ABAC Context**       | Dynamic attributes (e.g., time, location).     |
| **Policy Engine**      | Software evaluating policies against requests. |
| **Entitlement**        | Permission granted to a subject (e.g., `view:report`). |
| **Attribute Store**    | Database storing dynamic subject/resource data. |
| **Delegated Authority**| Grants roles/policies to other systems (e.g., SaaS apps). |

---
## **References**
- [NIST SP 800-162](https://csrc.nist.gov/publications/detail/sp/800-162/final) (ABAC Guide)
- [Cloud Security Alliance ABAC](https://www.cloudsecurityalliance.org/research/abac/)
- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/latest/)