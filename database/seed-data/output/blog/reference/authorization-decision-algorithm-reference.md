# **[Pattern] Reference Guide: Authorization Decision Algorithm**

---

## **Overview**
The **Authorization Decision Algorithm** pattern centralizes access control logic by evaluating compiled authorization rules against runtime inputs (roles, JWT claims, custom attributes, etc.). It dynamically determines whether to allow or deny a request based on a structured decision process, ensuring consistency, auditability, and adaptability. This pattern is essential for microservices, APIs, and systems requiring fine-grained access control.

The algorithm:
- **Compiles** role-based rules, attribute requirements, and custom conditions into executable logic.
- **Evaluates** these rules against incoming requests (e.g., JWT tokens, HTTP headers, or context data).
- **Returns a decision** (allow/deny) with optional granularity (e.g., partial permissions).
- Supports **dynamic updates** to rules without redeploying the application.

---

## **Schema Reference**
The pattern operates on the following core components:

| **Component**               | **Description**                                                                                                                                                                                                 | **Example**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Request Context**         | Input data for evaluation: user identity (JWT/JTI), roles, attributes, and request metadata (e.g., resource path, method).                                                     | `{"userId": "123", "roles": ["admin", "editor"], "context": {"resource": "/api/users"}}` |
| **Authorization Rule**      | Defines access requirements (roles, attributes, or conditions). Rules can be **mandatory** (must pass) or **optional** (must not block).                                                                 | `{"requirements": [{"type": "role", "value": "admin"}, {"type": "attribute", "key": "isActive", "value": true}]}` |
| **Decision Outcome**        | Result of evaluation (`allow`, `deny`, or `partial` with remaining constraints).                                                                                                                                   | `{"status": "allow", "remainingRoles": ["superuser"]}`                                            |
| **Custom Condition**        | A function or predicate to enforce business logic (e.g., "user has >3 pending requests").                                                                                                                    | `user.requestCount > 3`                                                                          |

---

## **Decision Algorithm Logic**
The algorithm follows this **pipeline**:
1. **Input Validation**: Checks for required fields (e.g., `userId`, `token`).
2. **Rule Compilation**: Converts static/dynamic rules into executable logic (e.g., using a **policy engine** or **advanced evaluator**).
3. **Context Extraction**: Parses JWT claims, headers, or external services for attributes.
4. **Requirement Evaluation**:
   - **Role Check**: Verifies if the user’s roles meet the rule’s `requirements.type: "role"`.
   - **Attribute Check**: Validates user properties (e.g., `isActive: true`).
   - **Custom Condition**: Executes user-defined logic (e.g., SQL query, third-party API call).
5. **Decision Aggregation**:
   - **Allow**: All requirements pass.
   - **Deny**: Any requirement fails (or `denyOverrides` is set).
   - **Partial**: Some requirements pass; remaining constraints are returned (e.g., for progressive access).
6. **Output**:
   - Returns a structured decision with metadata (e.g., `deniedReason`, `validUntil`).

---

## **Query Examples**
### **1. Basic Role-Based Access**
**Request**:
```json
{
  "userId": "abc123",
  "roles": ["admin"],
  "context": {
    "resource": "/api/data",
    "method": "DELETE"
  }
}
```
**Rule**:
```json
{
  "id": "delete-data",
  "requirements": [
    { "type": "role", "value": "admin" },
    { "type": "method", "value": ["DELETE", "POST"] }
  ]
}
```
**Decision**:
```json
{ "status": "allow", "remainingRoles": [] }
```

---
### **2. JWT Claims + Custom Condition**
**Request**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // JWT with "userType": "premium"
  "context": { "resource": "/api/premium" }
}
```
**Rule**:
```json
{
  "id": "premium-access",
  "requirements": [
    { "type": "claim", "key": "userType", "value": "premium" },
    { "type": "custom", "fn": "checkSubscriptionStatus", "args": { "userId": "{{userId}}" } }
  ]
}
```
**Custom Function (`checkSubscriptionStatus`)**:
```javascript
// Returns true if subscription is active
return await api.isActive(userId);
```
**Decision**:
```json
{ "status": "allow" }
```

---
### **3. Attribute + Time-Based Constraint**
**Request**:
```json
{
  "userId": "def456",
  "attributes": { "isAdmin": true, "lastLogin": "2024-01-01T12:00:00Z" },
  "context": { "resource": "/api/admin", "timestamp": "2024-01-02T09:00:00Z" }
}
```
**Rule**:
```json
{
  "id": "admin-dashboard",
  "requirements": [
    { "type": "attribute", "key": "isAdmin", "value": true },
    { "type": "timeSince", "key": "lastLogin", "maxHours": 24 }
  ]
}
```
**Decision**:
```json
{ "status": "deny", "deniedReason": "lastLogin too old" }
```

---

## **Implementation Strategies**
### **1. Compiler-Based Approach**
- **Pre-compile rules** into a queryable format (e.g., JSON Path for attributes, Lua scripts for custom logic).
- **Tooling**: Use a **policy-as-code** engine (e.g., Open Policy Agent, AWS IAM).
- **Pros**: Fast evaluation, supports complex logic.
- **Cons**: Requires rule maintenance.

**Example Compilation**:
```json
// Compiled from rule above
{
  "type": "and",
  "children": [
    { "type": "equals", "path": "$.attributes.isAdmin", "value": true },
    { "type": "lessThan", "path": "$.context.timestamp", "value": "$.attributes.lastLogin + 24h" }
  ]
}
```

---
### **2. Runtime Evaluator**
- **Evaluate rules dynamically** per request (e.g., using a **switch-case** or **dependency injection** for conditions).
- **Tooling**: Custom lambda functions or a lightweight evaluator (e.g., PyODID for Python).
- **Pros**: Flexible, no pre-compilation needed.
- **Cons**: Slower for high-throughput systems.

**Pseudocode**:
```python
def evaluate_rule(context, rule):
    for req in rule["requirements"]:
        if req["type"] == "role" and req["value"] not in context["roles"]:
            return {"status": "deny"}
        elif req["type"] == "custom":
            if not req["fn"](context["userId"]):
                return {"status": "deny"}
    return {"status": "allow"}
```

---
### **3. Hybrid Approach**
- **Cache compiled rules** for performance (e.g., Redis) but allow **dynamic overrides** (e.g., admin bypass).
- **Use case**: High-scale systems with infrequent rule changes.

---

## **Error Handling & Edge Cases**
| **Scenario**               | **Handling**                                                                                                                                                                                                 |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Missing JWT**             | Return `401 Unauthorized`; log for security audits.                                                                                                                                                            |
| **Invalid Rule Syntax**     | Compile-time error; validate rules before deployment (e.g., using a schema like [JSON Schema](https://json-schema.org/)).                                                                          |
| **Custom Condition Failure**| Retry logic (e.g., 2x) or fallback to default deny.                                                                                                                                                           |
| **Attribute Conflict**      | Prioritize explicit rules over implicit ones (e.g., JWT claims > headers).                                                                                                                               |
| **Partial Denial**          | Return `200 OK` with `remainingRoles` to guide the client (e.g., "upgrade to premium").                                                                                                                   |

---

## **Performance Considerations**
- **Rule Compilation**:
  - Pre-compile rules during **cold start** (e.g., serverless functions) or at **startup**.
  - Use **memoization** for identical user contexts.
- **Context Extraction**:
  - Cache JWT claims (TTL: 5–30 minutes).
  - Parallelize attribute lookups (e.g., fetch user roles + subscription status concurrently).
- **Custom Conditions**:
  - Limit complexity (avoid blocking I/O; use async/await).
  - Rate-limit external calls (e.g., 3 calls/sec per user).

---

## **Security Best Practices**
1. **Least Privilege**:
   - Default to `deny` unless all requirements pass.
   - Avoid `*` wildcards in roles/attributes.
2. **Immutable Rules**:
   - Sign rules with HMAC to prevent tampering.
3. **Audit Logs**:
   - Record decisions with:
     - Requester (`userId`, `IP`).
     - Rule ID, requirements.
     - Outcome and timestamp.
4. **Separation of Concerns**:
   - Decouple **authentication** (JWT validation) from **authorization** (rule evaluation).

---

## **Related Patterns**
| **Pattern**                     | **Description**                                                                                                                                                                                                 | **When to Use**                                                                                     |
|----------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **[Policy Enforcement Point](https://msdn.microsoft.com/en-us/library/aa334728.aspx)** | Intercepts requests to enforce authorization rules (e.g., API Gateway, WAF).                                                                                                                                   | Front-end access control (e.g., REST APIs, WebSockets).                                               |
| **[Attribute-Based Access Control (ABAC)**](https://www.oasis-open.org/committees/tc_home.php?wg_ab=abac) | Evaluates rules based on **attributes** (e.g., time, location, device) rather than just roles.                                                                                                                  | Context-aware systems (e.g., geofenced apps, time-based promotions).                                  |
| **[Role-Based Access Control (RBAC)**](https://www.omnisecu.com/kb/rbac-role-based-access-control) | Simplified access control using roles (e.g., "admin," "user").                                                                                                                                                   | Hierarchical organizations with static roles.                                                           |
| **[Delegated Authorization**](https://auth0.com/docs/secure/delegated-authorization) | Uses **OAuth tokens** to delegate authority (e.g., "user can act as admin for X hours").                                                                                                                           | Temporary privileges (e.g., "audit mode," "support ticket escalation").                                |
| **[Permission Granularity**](https://medium.com/geekculture/role-based-permission-granularity-68794294f0ea) | Fine-grained permissions (e.g., `edit:user:profile`, `delete:post:#123`).                                                                                                                                          | Highly modular systems (e.g., SaaS platforms with per-resource controls).                            |
| **[Circular Dependency Resolution**](https://www.baeldung.com/java-circular-dependency) | Handles cyclic role hierarchies (e.g., "manager" → "admin" → "manager").                                                                                                                                    | Complex org charts (e.g., "CTO inherits 'admin' role but not all sub-roles").                          |

---

## **Tools & Libraries**
| **Tool/Library**              | **Language/Framework** | **Key Features**                                                                                     | **Links**                                                                                           |
|--------------------------------|------------------------|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Open Policy Agent (OPA)**    | Go                     | Policy-as-code with Rego language; supports ABAC, RBAC, and custom logic.                                | [https://www.openpolicyagent.org/](https://www.openpolicyagent.org/)                                 |
| **AWS IAM Policy Simulator**   | JavaScript/Python      | Simulates IAM policies for access control testing.                                                      | [https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_testing-policies.html) |
| **Casbin**                     | Go, Python, Java       | Open-source access control with support for RBAC, ABAC, and custom models.                              | [https://casbin.org/](https://casbin.org/)                                                           |
| **Kyma (SAP)**                  | Kubernetes              | Policy engine for Kubernetes workloads (e.g., pod-to-pod access).                                     | [https://kyma-project.io/](https://kyma-project.io/)                                                 |
| **PyODID**                     | Python                 | Rule engine for dynamic decision-making (e.g., fraud detection).                                      | [https://github.com/odidtech/pyodid](https://github.com/odidtech/pyodid)                             |
| **Spring Security**            | Java/Spring Boot       | Built-in RBAC, OAuth2, and method-level security annotations.                                           | [https://spring.io/projects/spring-security](https://spring.io/projects/spring-security)             |

---
## **Example: Full Implementation (Node.js + JWT)**
```javascript
const jwt = require('jsonwebtoken');
const { evaluateRule } = require('./ruleEvaluator');

async function authorize(request) {
  try {
    const { token, context } = request;
    const payload = jwt.verify(token, process.env.JWT_SECRET);

    // Extract user attributes from JWT or external service
    const userAttributes = await fetchUserAttributes(payload.sub);

    // Evaluate rules
    const decision = evaluateRule({
      userId: payload.sub,
      roles: payload.roles,
      attributes: userAttributes,
      context
    });

    if (decision.status === "deny") {
      throw new Error(decision.deniedReason || "Access denied");
    }
    return decision;
  } catch (err) {
    console.error("Authorization failed:", err);
    throw new Error(err.message);
  }
}
```

**Rule Evaluator (`ruleEvaluator.js`)**:
```javascript
function evaluateRule(context) {
  for (const rule of RULES) {
    if (rule.id === context.context.resource && rule.requirements.every(validateRequirement)) {
      return { status: "allow", remainingRoles: [] };
    }
  }
  return { status: "deny", deniedReason: "No applicable rule" };

  function validateRequirement(req) {
    switch (req.type) {
      case "role": return context.roles.includes(req.value);
      case "attribute": return context.attributes[req.key] === req.value;
      case "custom": return req.fn(context);
      default: return true;
    }
  }
}
```

---
## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Rules not applying**              | Missing `userId` in context or incorrect role matching.                        | Validate input with `console.log(context, RULES)`.                                               |
| **Custom condition fails silently** | Uncaught errors in async functions.                                         | Wrap in `try/catch`; log errors to a monitoring system (e.g., Sentry).                         |
| **Performance bottleneck**          | Too many custom condition calls or inefficient rule compilation.              | Cache compiled rules; batch attribute lookups.                                                   |
| **Permission creep**                | Roles attributed without review.                                             | Implement **role hierarchy audits** (e.g., quarterly).                                           |
| **JWT claims mismatch**             | Expired token or unexpected `sub` claim.                                     | Add middleware to validate JWT before rule evaluation.                                           |

---
## **Migration Path**
1. **Audit Existing Rules**:
   - Map current access patterns to the **Authorization Decision Algorithm** schema.
   - Example: Convert SQL `WHERE` clauses to rule requirements.
2. **Phase 1: Static Rules**:
   - Replace hardcoded checks (e.g., `if (user.role === "admin")`) with compiled rules.
3. **Phase 2: Dynamic Logic**:
   - Introduce custom conditions for business rules (e.g., "user can edit if draft status").
4. **Phase 3: Testing**:
   - Use a **test harness** to verify rules against edge cases (e.g., malformed JWTs).
5. **Phase 4: Rollout**:
   - Deploy in **canary** (e.g., 10% of traffic) with feature flags for rollback.

---
## **Further Reading**
- [IETF OAuth 2.1](https://datatracker.ietf.org/wg/oauth/documents/draft-ietf-oauth-v2-1/) – Standard for JWT-based auth.
- [OASIS ABAC](https://www.oasis-open.org/committees/tc_home.php?wg_ab=abac) – ABAC specification.
- [Cloud Native Security](https://cloudnativeland.com/) – Patterns for Kubernetes-based auth.