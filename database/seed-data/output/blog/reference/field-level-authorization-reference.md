# **[Pattern] Field-Level Authorization: Reference Guide**

---

## **Overview**
Field-Level Authorization (FLA) is a security pattern that enforces granular access controls at the attribute/field level in API responses. Unlike traditional role-based access control (RBAC), which restricts entire resource visibility, FLA dynamically constructs responses by including or excluding individual fields based on user permissions. This ensures users only receive data they are authorized to see, reducing exposure of sensitive information while maintaining a consistent API contract.

Common use cases include:
- **Compliance & data privacy** (e.g., GDPR, CCPA), where certain fields (e.g., PII) must be redacted.
- **Internal vs. external APIs**, where external systems require less granular data.
- **Multi-tenant SaaS platforms**, where permissions vary between tenants or user roles.
- **Auditability**, by logging which fields were accessed (and denied).

---

## **Key Concepts**

| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authorization Rule** | A policy defining which users/roles can access a specific field. Rules are evaluated during request processing.                                                                                     |
| **Field Mask**        | A static or dynamic set of fields determined by the rule engine. Masking can be rule-based, role-based, or context-aware (e.g., tenant-specific).                                                          |
| **Policy Engine**     | A component (e.g., middleware, decorator, or library) that applies rules to incoming requests and modifies responses. May integrate with identity providers (e.g., Auth0, Okta) or custom policies. |
| **Fallback Mechanism**| A default behavior when a rule denies all fields (e.g., return an empty object or a "no-access" marker).                                                                                                 |
| **Dynamic Masking**   | Field inclusion/exclusion determined at runtime (e.g., based on request headers, claims, or external services).                                                                                          |
| **Validation Layer**  | Ensures the policy engine processes valid field names and avoids unintended data leakage (e.g., via `*` wildcards or inheritance).                                                                     |

---

## **Schema Reference**
Below is a reference schema for defining `Field-Level Authorization` rules. Implementations may vary by framework (e.g., OData, GraphQL, REST).

### **1. Authorization Policy Schema**
| Field               | Type          | Required | Description                                                                                                                                                                                                 |
|---------------------|---------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `policy_id`         | `string`      | Yes      | Unique identifier for the policy (e.g., `"P-2023-001"`).                                                                                                                                                      |
| `resource_type`     | `string`      | Yes      | The object type (e.g., `"User"`, `"Order"`) or API endpoint (e.g., `"/api/accounts"`).                                                                                                                   |
| `fields`            | `array`       | Yes      | List of fields to include/exclude. Each entry can specify conditions.                                                                                                                                      |
| `fields[*].name`    | `string`      | Yes      | Field name (e.g., `"email"`, `"ssn"`).                                                                                                                                                                 |
| `fields[*].allow`   | `boolean`     | No       | If `true`, the field is included by default; if `false`, excluded unless overridden by a rule. Default: `true` (inclusive).                                                                        |
| `fields[*].rules`   | `array`       | No       | List of conditions to evaluate.                                                                                                                                                                         |
| `fields[*].rules[*].role` | `string`    | No       | Role required to access the field (e.g., `"admin"`, `"manager"`).                                                                                                                                          |
| `fields[*].rules[*].claim` | `string`    | No       | JWT claim (e.g., `"tenant_id"`, `"department"`) with a value requirement.                                                                                                                               |
| `fields[*].rules[*].default` | `boolean` | No       | Default behavior if no rules match (e.g., `false` to exclude by default).                                                                                                                                  |
| `fields[*].fallback` | `string`     | No       | Value to return if the field is denied (e.g., `"****"` for masked PII).                                                                                                                                       |

---

### **2. Example Policy Definitions**
#### **Policy 1: Role-Based Field Access**
```json
{
  "policy_id": "P-2023-001",
  "resource_type": "User",
  "fields": [
    {
      "name": "email",
      "allow": true,
      "rules": [
        { "role": "admin" },
        { "role": "user", "default": false }  // Users cannot see email unless they are admins
      ]
    },
    {
      "name": "ssn",
      "allow": false,
      "fallback": "****-**-****"  // Masked PII
    }
  ]
}
```

#### **Policy 2: Tenant-Specific Masking**
```json
{
  "policy_id": "P-2023-002",
  "resource_type": "Order",
  "fields": [
    {
      "name": "customer_data",
      "allow": true,
      "rules": [
        { "claim": "tenant_id", "value": "tenant-a" }  // Only include for tenant "a"
      ]
    }
  ]
}
```

---

## **Query Examples**
Below are examples of how to apply FLA in different contexts.

### **1. REST API (Middleware-Based)**
Assume a Node.js/Express middleware (`authorize-fields.js`):
```javascript
const express = require('express');
const app = express();

app.use((req, res, next) => {
  const policy = require('./policies/P-2023-001.json');
  const userRoles = req.headers.authorization?.split(' ')[1]; // JWT roles

  // Simulate policy evaluation
  const allowedFields = policy.fields.filter(field => {
    const ruleMatch = field.rules.some(rule =>
      rule.role && userRoles.includes(rule.role) ||
      rule.claim && req.user[rule.claim] === rule.value
    );
    return ruleMatch ? field.name : null;
  });

  // Modify response before sending
  const originalSend = res.send;
  res.send = (body) => {
    if (body && allowedFields.length) {
      const maskedBody = { ...body };
      allowedFields.forEach(name => delete maskedBody[name]);
      originalSend(maskedBody);
    } else {
      originalSend(body);
    }
  };

  next();
});

app.get('/api/user', (req, res) => {
  res.json({ email: "user@example.com", ssn: "123-45-6789", name: "Alice" });
});
```
**Request:**
```http
GET /api/user
Authorization: Bearer roles=admin
```
**Response:**
```json
{
  "name": "Alice",
  "email": "user@example.com"
}
```

---

### **2. GraphQL (Schema Directives)**
Using Apollo Server with a custom directive `@authorize`:
```graphql
type User {
  id: ID!
  name: String!
  email: String! @authorize(roles: ["admin", "user"])
  ssn: String @authorize(allow: false, fallback: "****-**-****")
}

schema {
  directive @authorize(
    allow: Boolean = true
    roles: [String!]
    claim: String
    value: String
    fallback: String
  ) on FIELD_DEFINITION
}
```
**Query:**
```graphql
query {
  user(id: "123") {
    name
    email
    ssn
  }
}
```
**Response (with user role):**
```json
{
  "data": {
    "user": {
      "name": "Alice",
      "email": "user@example.com"
    }
  }
}
```

---

### **3. OData (Query Option)**
OData supports `$select` with dynamic filtering via `$filter` and custom annotations:
```http
GET /api/users?id=123&$select=name,email&$orderby=name asc
X-Authorization: Bearer roles=admin
```
**Response:**
```json
{
  "@odata.context": "...",
  "value": [
    {
      "id": "123",
      "name": "Alice",
      "email": "user@example.com"
    }
  ]
}
```
*Server-side logic would validate `$select` against the user’s permissions.*

---

## **Implementation Patterns**

### **1. Middleware Approach (REST)**
- **Pros**: Decouples policy logic from business logic; reusable across endpoints.
- **Cons**: Requires careful error handling for race conditions.
- **Tools**: Express middleware, FastAPI dependency injectors, Spring Security filters.

### **2. Schema Directives (GraphQL)**
- **Pros**: Declares authorization at the schema level; type-safe.
- **Cons**: Requires GraphQL-specific tooling (e.g., Apollo, Hasura).
- **Tools**: GraphQL directives, `@authorize`, `@read`, `@write`.

### **3. Query Filtering (OData/REST)**
- **Pros**: Leverages existing query parameters for flexibility.
- **Cons**: Harder to enforce complex rules without server-side validation.
- **Tools**: OData `$select`/$filter, JWT claim validation.

### **4. Database-Level Filtering (Last Resort)**
- **Warning**: Avoid exposing database schema or using `SELECT *` with application-side filtering. Use only for critical performance cases with strict auditing.

---

## **Security Considerations**
| Risk                          | Mitigation Strategy                                                                                                                                                                                                 |
|-------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Over-Permissive Policies**  | Validate rules against least-privilege principles. Use tools like OWASP ZAP to audit policies.                                                                                                          |
| **Field Injection**           | Sanitize field names in `$select`/`$filter` clauses. Reject wildcard requests (`*` in `$select`).                                                                                                       |
| **Cache Poisoning**           | Invalidate caches when policies change or user permissions update.                                                                                                                                             |
| **Fallback Exposure**         | Avoid returning sensitive defaults (e.g., `null` instead of `"****"`). Log denied field accesses for auditing.                                                                                              |
| **Performance Overhead**      | Cache policy evaluations for high-traffic endpoints. Use lightweight engines (e.g., JSON-based rules) instead of complex RBAC systems.                                                                     |

---

## **Related Patterns**
1. **[Attribute-Based Access Control (ABAC)](https://www.nist.gov/topics/information-security/attribute-based-access-control-abac)**
   - Extends FLA by evaluating dynamic attributes (e.g., time-of-day, location) alongside user roles.

2. **[Policy as Code](https://www.policy-as-code.org/)**
   - Manage authorization rules in infrastructure-as-code (IaC) tools (e.g., Terraform, Kubernetes RBAC) for consistency.

3. **[Request Scoping](https://auth0.com/docs/secure/request-scoping)**
   - Combine FLA with API request scoping to limit endpoints based on user context (e.g., `/api/internal`).

4. **[Data Masking](https://en.wikipedia.org/wiki/Data_masking)**
   - Use static masking (e.g., `****-**-****`) alongside dynamic FLA for compliance.

5. **[JWT Claims-Based Authorization](https://datatracker.ietf.org/doc/html/rfc7519#section-4.1)**
   - Embed field-level permissions in JWT tokens to avoid repeated policy checks.

---
## **Further Reading**
- [OWASP Field-Level Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Microsoft Entra ID Field-Level Encryption](https://learn.microsoft.com/en-us/azure/active-directory/manage-apps/field-level-encryption)
- [Hasura’s Data Security](https://hasura.io/docs/latest/graphql/core/data-security/) (GraphQL-specific).