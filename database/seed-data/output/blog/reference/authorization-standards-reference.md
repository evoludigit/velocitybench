# **[Pattern] Authorization Standards Reference Guide**

---
## **Overview**
The **Authorization Standards** pattern defines a structured approach to implementing permission policies in software systems, emphasizing consistency, scalability, and security. It standardizes how access control decisions are evaluated by defining clear schemas for **Subjects** (users/accounts), **Objects** (resources), and **Actions** (allowed operations). This pattern ensures compliance with least-privilege principles while reducing code duplication and complexity. Organizations use it to enforce access policies across microservices, APIs, and on-premise applications, often integrating with identity providers (IdPs) like OAuth2, OpenID Connect, or attribute-based access control (ABAC) systems.

---

## **Key Concepts**
### **1. Core Components**
| **Component**       | **Description**                                                                 |
|---------------------|---------------------------------------------------------------------------------|
| **Subject**         | An entity requesting access (e.g., user, service account, system).              |
| **Object**          | A resource being accessed (e.g., database table, API endpoint, file system path). |
| **Action**          | An operation permitted on the object (e.g., `read`, `write`, `delete`).        |
| **Policy**          | A rule defining conditions for granting/rejecting access (e.g., `owner-only`).  |
| **Scope**           | Contextual constraints (e.g., time-based, role-specific).                      |

---
### **2. Authorization Models Covered**
| **Model**               | **Use Case**                                  | **Example**                          |
|-------------------------|-----------------------------------------------|---------------------------------------|
| **Role-Based Access (RBAC)** | Assign permissions via roles (e.g., `admin`). | `role = "editor" → can: [write]`     |
| **Attribute-Based (ABAC)** | Dynamic policies based on attributes.         | `department = "finance" && role = "auditor"` |
| **OAuth2 Scopes**       | Token-based granular access.                 | `scope = "read:profile write:settings"` |
| **Policy-as-Code**      | Declarative policies in YAML/JSON.           | `{ "rule": "allow if user.group == 'admin'" }` |

---
## **Implementation Details**
### **1. Schema Reference**
Define authorization standards using the following schema for consistency:

| **Field**      | **Type**       | **Description**                                                                 | **Examples**                          |
|----------------|----------------|---------------------------------------------------------------------------------|----------------------------------------|
| `subject`      | String/Object  | Identifier for the requesting entity (e.g., `user_id` or `{ "id": "123", "type": "service" }`). | `"12345"`, `{"type": "app", "name": "logger"}` |
| `object`       | String/Object  | Target resource (e.g., path, UUID, or nested structure).                         | `"/api/data"`, `{"table": "users", "column": "email"}` |
| `action`       | String/Array   | Permitted operation(s).                                                          | `"read"`, `["write", "delete"]`       |
| `policy`       | String/Object  | Condition logic (see [Policy Formats](#policy-formats)).                       | `"owner-only"`, `{ "rule": "dept == 'engineering'" }` |
| `scope`        | String/Array   | Contextual limits (e.g., time or location).                                    | `"region=us-west"`, `["2024-01-01", "2024-12-31"]` |
| `metadata`     | Object         | Additional attributes (e.g., `created_at`, `version`).                          | `{ "expires": "2024-12-31" }`         |

---
### **2. Policy Formats**
| **Format**               | **Syntax**                          | **Example**                          | **Use Case**                          |
|--------------------------|-------------------------------------|---------------------------------------|---------------------------------------|
| **Role-Based (RBAC)**    | `role: "role_name"`                 | `"role": "data_analyst"`              | Simple team hierarchies.              |
| **Condition Check**      | `if: "attr == value"`               | `{ "if": "user.department == 'hr'" }` | Dynamic attribute-based rules.        |
| **Time-Based**           | `notBefore: ISO8601` + `notAfter`   | `{ "notBefore": "2024-01-01", "notAfter": "2024-01-31" }` | Temporary access. |
| **Combined Policies**    | Logical `AND`/`OR` operators        | `{ "if": "user.role == 'admin' || user.department == 'security'" }` | Complex multi-condition rules. |

---
### **3. Evaluation Flow**
1. **Request Parsing**: Extract `subject`, `object`, `action`, and `policy` from the access request (e.g., HTTP headers, JWT claims).
2. **Policy Resolution**: Evaluate conditions against the subject/object attributes.
3. **Decision**: Return `ALLOW`/`DENY` + optional metadata (e.g., `expires_at`).

**Pseudocode Example**:
```javascript
function authorize(request) {
  const policy = resolvePolicy(request.subject, request.object, request.action);
  if (matchesConditions(policy, request.subject, request.object)) {
    return { status: "ALLOW", expires: policy.scope?.expiry };
  } else {
    return { status: "DENY" };
  }
}
```

---
## **Query Examples**
### **1. REST API Authorization Header**
```http
GET /api/users/123 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Authorization-Policy: {"role": "admin"}
```

**Response (Granted)**:
```json
{
  "status": "ALLOW",
  "permitted_actions": ["read", "write"]
}
```

---
### **2. OAuth2 Scope Validation**
**Request**:
```http
GET /api/files/private
Authorization: Bearer <token_with_scope="read:files write:disable_deletion">
```

**Response (Granted)**:
```json
{
  "status": "ALLOW",
  "scope": "read:files"
}
```

**Response (Denied)**:
```json
{
  "status": "DENY",
  "reason": "Missing scope 'write:disable_deletion'"
}
```

---
### **3. ABAC Policy Evaluation (JSON)**
**Policy**:
```json
{
  "rule": "user.role == 'auditor' && object.sensitivity == 'high'",
  "scope": { "region": "us", "hour": "09:00-17:00" }
}
```

**Request**:
```json
{
  "subject": { "id": "user1", "role": "auditor" },
  "object": { "id": "doc1", "sensitivity": "high" },
  "action": "view"
}
```

**Response**:
```json
{
  "status": "ALLOW",
  "scope": { "region": "us" }
}
```

---
## **Schema Validation Tools**
| **Tool**               | **Purpose**                                                                 | **Example**                          |
|------------------------|-----------------------------------------------------------------------------|---------------------------------------|
| **JSON Schema**        | Validate policy structure.                                                  | [Example Schema](https://json-schema.org/) |
| **Open Policy Agent (OPA)** | Run-time policy enforcement.                                                | `allow { input.action == "read" }`   |
| **Casbin**             | Flexible RBAC/ABAC engine.                                                  | [Casbin GitHub](https://github.com/casbin/casbin) |
| **AWS IAM Policies**   | Cloud-native access control.                                                | `{"Effect": "Allow", "Action": ["s3:GetObject"]}` |

---
## **Requirements & Constraints**
| **Requirement**               | **Description**                                                                 | **Example**                          |
|-------------------------------|-------------------------------------------------------------------------------|---------------------------------------|
| **Least Privilege**           | Grant only necessary permissions.                                            | Role: `editor` → `["write", "delete"]` (not `admin`). |
| **Immutable Tokens**          | Avoid token revocation mid-session (use short-lived tokens).                  | JWT expiry: `15m`.                   |
| **Audit Logging**             | Log all authorization decisions for compliance.                              | `{ "timestamp": "2024-01-10T12:00", "decision": "DENY", "reason": "missing scope" }` |
| **Policy Versioning**         | Support backward compatibility for policies.                                  | `policy_v1.json` vs. `policy_v2.json`. |

---
## **Related Patterns**
| **Pattern**                 | **Connection to Authorization Standards**                                  | **Reference**                          |
|-----------------------------|-----------------------------------------------------------------------------|-----------------------------------------|
| **[Identity Federation]**   | Integrates with IdPs (OAuth2, SAML) to validate subjects.                  | [OAuth2 RFC](https://datatracker.ietf.org/doc/html/rfc6749) |
| **[Rate Limiting]**         | Combines with auth to throttle actions (e.g., `action: "create" → max 5/min`). | [OpenAPI Rate Limit Extension](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.1.md#rate-limiting) |
| **[Canonical Data Model]**  | Standardizes `object` definitions (e.g., `resource_type: "user_profile"`). | [CDM Guide](https://www.enterprisedt.com/canonical-data-model/) |
| **[Policy-as-Code]**        | Stores policies in Git for versioning and review.                           | [Open Policy Agent](https://www.openpolicyagent.org/) |

---
## **Troubleshooting**
| **Issue**                     | **Diagnosis**                                      | **Solution**                                  |
|--------------------------------|---------------------------------------------------|-----------------------------------------------|
| **403 Forbidden**              | Policy evaluation failed.                          | Check `policy.rule` and subject/object attrs. |
| **Token Expiry Errors**        | Short-lived tokens invalidated.                   | Increase `exp` claim or use refresh tokens.   |
| **Policy Conflicts**           | Multiple policies deny access.                    | Use higher-priority rules or `OR` logic.      |
| **Performance Bottlenecks**    | Slow ABAC evaluations.                              | Cache policy results or use OPA’s `revision`. |

---
## **Example Ecosystem Integration**
### **1. Backend Service (Node.js + Express)**
```javascript
const express = require('express');
const app = express();

// Middleware to validate auth headers
app.use((req, res, next) => {
  const policy = req.headers['x-authorization-policy'];
  if (!validatePolicy(policy)) return res.status(403).send("Forbidden");
  next();
});

// Route with dynamic ABAC
app.get('/api/data', (req, res) => {
  const decision = authorize({
    subject: req.user,
    object: req.query.resource,
    action: 'read'
  });
  if (decision.status === "DENY") return res.status(403).send("DENY");
  res.json(decision);
});
```

---
### **2. Kubernetes RBAC Example**
**Role Definition**:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
```

**Binding**:
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
subjects:
- kind: User
  name: alice
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

---
## **Best Practices**
1. **Standardize Naming**:
   - Use consistent `action` verbs (e.g., `create`, `update` instead of `modify`).
   - Define canonical `object` types (e.g., `user_profile`, not `profile`).

2. **Avoid Over-Permissioning**:
   - Default to `DENY` unless explicitly allowed.
   - Use tools like [AWS IAM Access Analyzer](https://aws.amazon.com/iam/features/access-analyzer/) to audit permissions.

3. **Document Policies**:
   - Maintain a **policy registry** (e.g., Confluence page or Git repo) with:
     - Owner contact.
     - Last modified date.
     - Example usage.

4. **Test Edge Cases**:
   - Validate policies with:
     - Empty attributes (e.g., `subject.hasNoRole`).
     - Malformed inputs (e.g., `object.id` missing).
   - Use property-based testing (e.g., [Hypothesis](https://hypothesis.works/)).

5. **Monitor Anomalies**:
   - Track `DENY` decisions in logs (e.g., ELK Stack).
   - Set up alerts for unusual patterns (e.g., "User `bob` was denied 10x in 1 hour").

---
## **Further Reading**
- [IETF OAuth 2.1](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-01) (Modern OAuth standards).
- [Cloud Security Alliance ABAC Guide](https://www.cloudsecurityalliance.org/research/abac/).
- [Open Policy Agent Documentation](https://www.openpolicyagent.org/docs/latest/).
- [Microsoft Entra ID (Azure AD) Permissions Model](https://learn.microsoft.com/en-us/azure/active-directory/develop/).