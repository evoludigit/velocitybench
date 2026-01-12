**[Pattern] Authorization Validation – Reference Guide**

---

### **1. Overview**
The **Authorization Validation** pattern ensures that users or systems attempting to access protected resources possess the necessary **permissions, roles, or attributes** to perform requested operations. This pattern mitigates unauthorized access risks by systematically validating credentials, policies, and contextual constraints before granting access.

Authorization validation integrates with **Authentication** (proving identity) to enforce **least-privilege principles**, often combining:
- **Role-Based Access Control (RBAC)** – Assigning permissions to predefined roles.
- **Attribute-Based Access Control (ABAC)** – Evaluating dynamic attributes (e.g., time, location).
- **Policy Engines** – Deciding access via declarative rules.

---
### **2. Implementation Details**

#### **2.1 Key Concepts**
| **Term**               | **Definition**                                                                                     | **Example**                                  |
|-------------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Policy**              | Rules defining permitted operations per role/attribute.                                            | `"engineers:can-edit:pmt-123"`              |
| **Principal**           | User, service account, or system requesting access.                                               | `"alice@org.com"`                           |
| **Resource**            | Data, endpoints, or actions being accessed.                                                       | API endpoint: `GET /projects/42`            |
| **Permission Scope**    | Granularity of control (e.g., read-only, full access).                                          | `read:projects`, `write:payroll`            |
| **Contextual Rules**    | Time/location-based overrides (e.g., "only accessible after 5 PM").                              | `admin_access:only:office_hours`            |

#### **2.2 Core Components**
| **Component**          | **Description**                                                                                     | **Implementation Tools**                     |
|-------------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------|
| **Policy Storage**      | Stores authorization rules (e.g., JSON/YAML files, databases).                                   | Redis, PostgreSQL, Policy-as-Code (OPA)     |
| **Policy Engine**       | Validates requests against rules.                                                                | Open Policy Agent (OPA), AWS IAM, Azure RBAC|
| **Token Validation**    | Decodes and verifies JWT/OAuth tokens for claims (e.g., roles).                                  | JWT Libraries (e.g., `jsonwebtoken` Node.js)|
| **Attribute Fetchers**  | Retrieves dynamic attributes (e.g., user’s department, location).                                 | LDAP, REST APIs, Datastores                |
| **Audit Logs**          | Tracks access decisions (success/failure) for compliance/auditing.                              | ELK Stack, Datadog                            |

---
### **3. Schema Reference**

#### **3.1 Core Authorization Policy Schema (Open Policy Agent)**
```json
{
  "policy_id": "string",         // Unique identifier (e.g., "delete-documents")
  "description": "string",      // Policy purpose (e.g., "Only admins can delete projects")
  "input": {
    "request": {
      "principal": "string",    // "user:alice123" or "service:payment-gateway"
      "action": "string",       // "delete", "update", "read"
      "resource": "string",     // "project:team-blue"
      "context": {               // Dynamic attributes
        "user_attributes": {     // From LDAP/DB
          "department": "string",
          "location": "string"
        },
        "time": "ISO-8601"       // "2024-05-20T14:30:00Z"
      }
    }
  },
  "rule": {
    "operator": "and/or",       // Logical combination of conditions
    "conditions": [
      {
        "field": "principal.type",
        "operator": "==",
        "value": "user"
      },
      {
        "field": "request.action",
        "operator": "in",
        "values": ["delete", "update"]
      },
      {
        "field": "context.user_attributes.department",
        "operator": "==",
        "value": "engineering"
      }
    ]
  },
  "effect": "allow/deny"        // Outcome if conditions pass
}
```

#### **3.2 Token Claim Schema (JWT/OAuth2)**
```json
{
  "iss": "string",               // Issuer (e.g., "https://idp.org")
  "sub": "string",               // Subject (user/service ID)
  "aud": ["string"],             // Audience (APIs/clients)
  "exp": "timestamp",            // Expiration
  "iat": "timestamp",            // Issued at
  "roles": ["string"],           // Permitted roles (e.g., ["admin", "auditor"])
  "permissions": {               // Fine-grained scopes
    "projects": ["read", "write"],
    "payroll": ["view"]
  },
  "custom_attrs": {              // Extensions (e.g., "department:engineering")
    "dept": "string"
  }
}
```

---
### **4. Query Examples**

#### **4.1 Policy Evaluation (OPA Rego)**
```rego
package authz

default allow = false

allow {
  input.request.principal.type == "user"
  input.request.action == "update"
  input.request.resource == "project:team-blue"
  input.context.user_attributes.department == "engineering"
}
```

**Input (Structured JSON):**
```json
{
  "request": {
    "principal": "user:alice123",
    "action": "update",
    "resource": "project:team-blue"
  },
  "context": {
    "user_attributes": {
      "department": "engineering"
    }
  }
}
```

**Output:**
```json
{ "allow": true }
```

---

#### **4.2 Token Validation (Node.js Example)**
```javascript
const jwt = require('jsonwebtoken');
const policyEngine = require('./policy-engine');

async function validateAccess(token, request) {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const { roles, permissions } = decoded;

    // Check RBAC
    if (!roles.includes('admin') && !permissions.projects.includes('update')) {
      throw new Error('Insufficient permissions');
    }

    // Evaluate contextual policies
    const context = { user_attributes: await fetchUserAttrs(decoded.sub) };
    const policyResult = await policyEngine.evaluate(request, context);

    return policyResult.allow;
  } catch (err) {
    return false;
  }
}

// Usage
const isAllowed = await validateAccess(token, {
  action: 'update',
  resource: 'project:team-blue'
});
```

---
### **5. Common Implementation Patterns**

| **Pattern**               | **Use Case**                                  | **Example Tools/Policies**                     |
|---------------------------|-----------------------------------------------|-----------------------------------------------|
| **Role-Based (RBAC)**     | Static roles assign permissions.               | `admin:can*:*`, `editor:can-read:projects`   |
| **Attribute-Based (ABAC)**| Dynamic rules (e.g., "HR can edit payroll only after 3 PM"). | OPA Policy: `input.context.time >= "15:00:00"` |
| **Token-Based**           | Embed policies in JWT claims.                 | `permissions: { "payroll": ["view"] }`        |
| **API Gateway Validation**| Validate requests at entry points (e.g., Kong, AWS API Gateway). | Lambda Authorizers, JWT Plugins               |
| **Microsegmentation**     | Isolate access in microservices.              | Istio Authorization Policies                  |

---
### **6. Error Handling & Logging**
| **Error Type**          | **Scenario**                                      | **Response**                                  |
|-------------------------|---------------------------------------------------|-----------------------------------------------|
| **Malformed Token**     | Invalid JWT signature/expired.                    | HTTP 401 Unauthorized                         |
| **Missing Permissions** | User lacks required role/permission.              | HTTP 403 Forbidden                            |
| **Policy Conflict**     | Multiple policies deny access.                   | Log conflict + default to `deny` (zero-trust) |
| **Context Fetch Fail**  | LDAP/API timeout retrieving user attributes.      | Cache fallback + retry                       |

**Audit Log Entry Example:**
```json
{
  "timestamp": "2024-05-20T14:30:00Z",
  "principal": "user:bob456",
  "resource": "project:team-blue",
  "action": "update",
  "decision": "deny",
  "reason": "Missing role: 'editor'",
  "policy_id": "update-projects-2.0"
}
```

---
### **7. Related Patterns**
1. **[Authentication](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-policies.html)**
   - *Complements authorization by verifying identity (e.g., JWT/OAuth).*
2. **[Least Privilege](https://cloud.google.com/blog/products/identity-security/least-privilege-access-control)**
   - *Guides permission scoping to minimize attack surface.*
3. **[Policy-as-Code](https://www.openpolicyagent.org/docs/latest/policy-language.html)**
   - *Defines rules in declarative languages (e.g., Rego, JSON).*
4. **[OAuth2/OIDC Flows](https://auth0.com/docs/get-started/authentication-and-authorization-flow)**
   - *Enables delegation of authorization via tokens.*
5. **[Microservices Authorization](https://istio.io/latest/docs/tasks/security/authz/)**
   - *Enforces per-service access controls in distributed systems.*

---
### **8. Best Practices**
- **Granularity**: Prefer fine-grained permissions (e.g., `update:project:123`) over broad roles.
- **Immutability**: Store policies in version-controlled repositories (e.g., Git).
- **Testing**: Use tools like **OPA Test** or **Policy Simulator** to validate rules.
- **Caching**: Cache policy evaluations to reduce latency (e.g., Redis).
- **Zero Trust**: Default to `deny` and require explicit allowance where possible.

---
**References:**
- [Open Policy Agent Docs](https://www.openpolicyagent.org/docs/latest/)
- [AWS IAM Policy Examples](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples.html)
- [OAuth 2.0 RFC](https://datatracker.ietf.org/doc/html/rfc6749)