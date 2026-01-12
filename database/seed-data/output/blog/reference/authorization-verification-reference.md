# **[Pattern] Authorization Verification Reference Guide**

---

## **Overview**
The **Authorization Verification** pattern ensures that requests to protected resources comply with predefined access controls before execution. It enforces policies such as role-based access control (RBAC), attribute-based access control (ABAC), or custom logic to determine whether a user or system entity can perform an action. This pattern is widely used in APIs, microservices, and applications requiring granular access control.

Key components:
- **Policy Engine**: Evaluates permissions against user attributes, resource metadata, and request context.
- **Authentication Token**: Validates identity (e.g., JWT, OAuth tokens) before authorization checks.
- **Access Policy Store**: Centralized rules defining allowed actions per user/role.
- **Decision Point**: Returns `Allow`/`Deny` based on policy evaluation.

---

## **Requirements & Key Concepts**
### **Core Requirements**
| **Requirement**               | **Description**                                                                 | **Example**                          |
|-------------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Identity Validation**       | Verify user/system identity via token/credentials before authorization.       | JWT validation                          |
| **Policy Evaluation**         | Check user roles/attributes against resource permissions.                     | `user.role == "Admin" && resource.type == "Edit"` |
| **Context-Aware Checks**      | Consider request-time factors (IP, time, device) in decisions.              | `hour < 10` (block early-morning access) |
| **Audit Logging**             | Log authorization decisions for compliance/review.                           | `"User: u123, Action: DELETE, Decision: DENY, Reason: Missing `admin` role"` |
| **Performance**               | Minimize latency via caching or rule optimization.                           | Pre-compile policies for faster checks |

### **Key Terminology**
| **Term**               | **Definition**                                                                 |
|------------------------|-------------------------------------------------------------------------------|
| **Subject**            | The entity requesting access (user, service account, etc.).                   |
| **Resource**           | The protected entity (e.g., `/api/data`, `user:johndoe`).                     |
| **Action**             | The permitted operation (`READ`, `WRITE`, `DELETE`).                          |
| **Permission**         | A formalized `Subject Action Resource` rule (e.g., `"Admin:DELETE:/api/*"`). |
| **Policy Engine**      | Logic that combines rules to determine access (e.g., PDPs in XACML).         |
| **Decision Point**     | Output of the policy engine (`Allow`/`Deny`).                                   |

---

## **Schema Reference**
### **1. Policy Rule Schema**
Defines permissions using a structured format (e.g., JSON, YAML).

| **Field**       | **Type**   | **Required** | **Description**                                                                 | **Example**                          |
|-----------------|------------|--------------|---------------------------------------------------------------------------------|--------------------------------------|
| `id`            | `string`   | Yes          | Unique identifier for the rule.                                                 | `"rule-123"`                         |
| `subject`       | `object`   | Optional     | Attributes of the requesting entity (e.g., `role`, `group`).                   | `{"role": "Editor", "tenant": "dev"}` |
| `resource`      | `object`   | Optional     | Metadata about the targeted resource (e.g., `type`, `path`).                   | `{"type": "Document", "path": "/api/docs"}` |
| `action`        | `string[]` | Optional     | Allowed operations (e.g., `["READ", "WRITE"]`).                                | `["EDIT"]`                           |
| `conditions`    | `object`   | Optional     | Additional checks (e.g., time, IP).                                            | `{"hour": {"$lt": 8}}`              |
| `effect`        | `string`   | Yes          | `Allow`/`Deny` or `PermitUnlessDenied` (default).                              | `"Allow"`                            |

**Example Policy (YAML):**
```yaml
rules:
  - id: "edit-documents"
    subject:
      role: "Editor"
    resource:
      type: "Document"
    action: ["EDIT"]
    effect: "Allow"
```

---

### **2. Authorization Request Schema**
Input to the policy engine (typically derived from HTTP headers or JWT claims).

| **Field**          | **Type**   | **Source**               | **Description**                                  | **Example**                          |
|--------------------|------------|--------------------------|--------------------------------------------------|--------------------------------------|
| `subject_id`       | `string`   | JWT `sub`                | Unique identifier of the requesting user.          | `"u456"`                             |
| `subject_role`     | `string[]` | JWT `roles`              | Assigned roles.                                  | `["Editor", "Guest"]`                |
| `resource_path`    | `string`   | HTTP `path`              | Target URI/resource.                             | `"/api/data/123"`                    |
| `action`           | `string`   | HTTP `method`            | Requested operation (`GET`, `POST`, etc.).        | `"DELETE"`                           |
| `context`          | `object`   | Headers/Query Params     | Dynamic factors (e.g., `IP`, `time`).            | `{"ip": "192.168.1.1", "hour": 3}`   |

---

### **3. Response Schema**
Output from the policy engine.

| **Field**    | **Type**   | **Description**                                                                 |
|--------------|------------|---------------------------------------------------------------------------------|
| `decision`   | `string`   | `Allow`/`Deny`.                                                                 |
| `reason`     | `string`   | Human-readable explanation (e.g., `"Missing `editor` role"`).                    |
| `policy_id`  | `string`   | ID of the rule that triggered the decision.                                    |
| `audit_data` | `object`   | Metadata for logging.                                                          | `{ "user": "u456", "resource": "/api/data/123", "timestamp": "2024-05-20T12:00:00Z" }` |

---

## **Implementation Details**
### **1. Flowchart**
```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│             │──────▶│             │──────▶│                 │
│  Request    │       │  Auth       │       │  Policy Engine  │
│  (JWT/Token)│       │  Validation │       │  (Evaluates     │
└─────────────┘       └─────────────┘       │   Rules)         │
     ▲                  ▲                  └─────────────┬────┘
     │                  │                          ▼
┌────┴──────────────────┴───────────────────────┐▶│             │
│  Redirect/Error (if   │                          │             │
│  auth fails)          │                          │             │
└───────────────────────┘                          │             │
                                                         └────────┬───────┐
                                                             ▼         │
                                                            Allow/Deny │
                                                             ▼         │
                                                       ┌─────────────┘
                                                       │             │
                                                       ▼             ▼
                                              ┌─────────────┐ ┌─────────────┐
                                              │  Grant      │ │  Reject     │
                                              │  Access     │ │  Access     │
                                              └─────────────┘ └─────────────┘
```

### **2. Decision Logic**
- **Precedence**: Rules can define `order` or use `effect: "DenyUnlessPermit"` for negative permissions.
- **Short-Circuit Evaluation**: Stop at the first matching rule (optimization).
- **Default Decision**: `PermitUnlessDenied` (allow if no rule denies).

### **3. Integration Patterns**
| **Pattern**               | **Use Case**                                      | **Implementation Notes**                          |
|---------------------------|---------------------------------------------------|---------------------------------------------------|
| **API Gateway**           | Centralized auth for microservices.               | Use plugins (e.g., Kong, AWS API Gateway).        |
| **Middleware**            | Embedded in app frameworks (e.g., Express, Flask).| Hook into route handlers (e.g., `beforeAction`).  |
| **Database-Defined Rules**| Dynamic policies (e.g., PostgreSQL `pg_policy`).   | Store rules in DB; evaluate during SQL queries.   |
| **Service Mesh**          | Istio/Linkerd for service-to-service auth.        | Use `AuthorizationPolicy` CRDs.                   |

---

## **Query Examples**
### **1. REST API Endpoint (Express.js)**
```javascript
const express = require('express');
const { verifyJwt, authorize } = require('./auth');

const app = express();

// Middleware to validate JWT and authorize
app.use((req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  verifyJwt(token)
    .then(user => {
      authorize(user, req.path, req.method)
        .then(decision => {
          if (decision.decision !== 'Allow') {
            return res.status(403).send(decision.reason);
          }
          next();
        })
        .catch(err => res.status(401).send(err.message));
    })
    .catch(() => res.status(401).send('Invalid token'));
});

// Protected route
app.get('/api/data/:id', (req, res) => {
  res.json({ data: "Sensitive content" });
});
```

### **2. SQL Query with Postgres Policy**
```sql
-- Create a policy to restrict DELETE to admins
CREATE POLICY admin_only_delete
ON documents
FOR DELETE
USING (current_setting('app.current_user_role') = 'admin');
```

### **3. Kubernetes AuthorizationPolicy (Istio)**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: require-editor-role
spec:
  selector:
    matchLabels:
      app: my-app
  rules:
  - from:
    - source:
        requestPrincipals: ["*.editor@example.com"]
    to:
    - operation:
        methods: ["POST", "PUT"]
        paths: ["/api/*"]
```

---

## **Performance Considerations**
| **Optimization**               | **Strategy**                                                                 | **Tools/Techniques**                          |
|---------------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Rule Caching**                | Cache evaluated policies for repeated requests.                              | Redis, Memcached                              |
| **Pre-Filtering**               | Evaluate coarse-grained rules (e.g., roles) before fine-grained checks.       | -                                             |
| **Rule Compilation**            | Convert policies to optimized data structures (e.g., trie for paths).        | Antlr, custom parsers                         |
| **Asynchronous Checks**         | Offload policy evaluation to a background service (e.g., for ABAC).          | Kafka, RabbitMQ                                |
| **Rate Limiting**               | Throttle excessive authorization requests.                                   | Nginx `limit_req`, AWS WAF                     |

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **[Authentication]**      | Verify identity (e.g., via OAuth2, JWT) before authorization.                | Required before `Authorization Verification`.  |
| **[Attribute-Based Access Control (ABAC)]** | Fine-grained policies tied to dynamic attributes (e.g., `time`, `location`). | When static roles/permissions are insufficient. |
| **[Policy as Code]**      | Define policies in code (e.g., Terraform, Open Policy Agent).                | For IaC and GitOps integrations.              |
| **[Zero Trust)**          | Assume breach; require re-authentication for every request.                  | High-security environments.                  |
| **[Decentralized Identity]** | Self-sovereign identity (e.g., DIDs, Verifiable Credentials).               | Blockchain/DID-based systems.                 |

---

## **Troubleshooting**
| **Issue**                          | **Possible Cause**                          | **Solution**                                  |
|-------------------------------------|--------------------------------------------|-----------------------------------------------|
| **403 Forbidden**                   | Incorrect role/action in token/policy.      | Verify JWT claims and policy rules.           |
| **High Latency**                    | Complex policies or uncached rules.         | Simplify rules; enable caching.               |
| **False Negatives**                 | Conditions misconfigured (e.g., `$lt` vs `$lte`). | Test edge cases (e.g., time zones).          |
| **Policy Drift**                    | Rules outdated (e.g., missing `new-role`).   | Automate policy sync with identity providers. |

---
**Final Notes**:
- Start with **RBAC** for simplicity; add **ABAC** for dynamic requirements.
- Use **Open Policy Agent (OPA)**/**AuthZForce** for policy-as-code implementations.
- Audit logs are critical for compliance (e.g., SOC2, GDPR).