**[Pattern] Reference Guide: Authorization Guidelines**

---

### **Overview**
The **Authorization Guidelines** pattern provides a structured, policy-driven approach to defining and enforcing access control rules across an application or system. Unlike fine-grained role-based access control (RBAC), this pattern uses **predefined, hierarchical guidelines** (e.g., "read-only for guests," "edit for administrators") to simplify authorization logic, reduce boilerplate code, and ensure consistency. It is particularly useful in large-scale systems where granular permissions would introduce complexity.

Key benefits include:
- **Separation of concerns**: Policies are defined in one location (e.g., JSON/YAML schemas) and reused.
- **Reduced redundancy**: Avoids repetitive `if-then` logic for permission checks.
- **Extensibility**: New guidelines can be added without modifying core business logic.
- **Auditability**: Clear documentation of why a resource/action is allowed or denied.

This pattern is commonly paired with **Attribute-Based Access Control (ABAC)** or **Policy-Based Access Control (PBAC)** but operates independently as a framework for defining guardrails.

---

### **Implementation Details**

#### **Core Concepts**
1. **Authorization Guidelines (Schemas)**
   A structured definition of access rules tied to **resources**, **actions**, and **conditions**. Examples:
   - `Resource`: User profiles, orders, reports.
   - `Action`: `read`, `create`, `delete`.
   - `Condition`: `user.role == "admin"`, `order.status != "cancelled"`.

2. **Policy Engine**
   A service that evaluates guidelines against runtime context (e.g., user attributes, environment flags) to determine access.

3. **Context Providers**
   Modules that supply dynamic data (e.g., database queries, API responses) to the policy engine during evaluation.

4. **Fallback Rules**
   Default behaviors (e.g., "deny by default" or "permissive mode") when no guideline matches.

5. **Hierarchical Inheritance**
   Guidelines can inherit from parent policies (e.g., a "superuser" role overrides `read` permissions for all resources).

---

### **Schema Reference**
Below is the canonical schema for defining **Authorization Guidelines** (compatible with JSON/YAML).

| **Field**            | **Type**       | **Description**                                                                                     | **Example Value**                          |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `name`               | `string`       | Unique identifier for the guideline (e.g., `user-profile-edit`).                                     | `"user_profile_read_only_guests"`           |
| `description`        | `string`       | Human-readable rationale for the rule.                                                              | `"Guests cannot modify profiles."`           |
| `applies_to`         | `object`       | Resource scope (e.g., REST endpoints, database tables, microservices).                               | `{ "route": "/api/users/:id", "table": "users" }` |
| `actions`            | `array<string>`| Allowed actions (e.g., `["read", "create"]`).                                                      | `["read"]`                                  |
| `deny_actions`       | `array<string>`| Explicitly blocked actions (overrides `actions`).                                                  | `["delete"]`                                |
| `conditions`         | `array<object>`| Logic gates evaluating to `true`/`false`.                                                            | `[ { "key": "user.role", "op": "==", "value": "guest" } ]` |
| `inherits_from`      | `string`       | Parent guideline name (e.g., `default_user_permissions`).                                           | `"base_user_permissions"`                   |
| `fallback`           | `string`       | Default action if conditions fail (`"deny"`, `"allow"`, or a custom function name).               | `"deny"`                                    |
| `priority`           | `number`       | Integer determining evaluation order (higher = evaluated first).                                    | `10`                                        |
| `metadata`           | `object`       | Arbitrary key-value pairs (e.g., `created_by`, `last_revised`).                                     | `{ "documentation": "https://..." }`        |

---

### **Query Examples**
Guidelines are evaluated programmatically. Below are pseudocode snippets for common scenarios.

#### **1. Evaluating a Guideline**
```python
def evaluate_guideline(guideline, context):
    # Example: Check if a guest can read a user profile
    user_role = context["user"]["role"]
    resource = context["resource"]

    for condition in guideline["conditions"]:
        if not evaluate_condition(condition, context):
            return False  # Condition fails
    return True
```

#### **2. Dynamic Context Example**
```json
// Request context for evaluating `user_profile_read_only_guests`
{
  "user": {
    "id": "123",
    "role": "guest",
    "permissions": ["read:reports"]
  },
  "resource": {
    "type": "user_profile",
    "id": "456"
  },
  "environment": {
    "mode": "production"
  }
}
```

#### **3. Policy Engine Output**
```json
{
  "guideline_name": "user_profile_read_only_guests",
  "evaluation_result": false,
  "matched_actions": [],
  "reason": "User role 'guest' does not allow 'read' on resource 'user_profile'.",
  "conditions_evaluated": [
    { "key": "user.role", "value": "guest", "result": false }
  ]
}
```

---

### **Query Language (Templating)**
Conditions support a simple templating syntax:

| **Operator** | **Syntax**                  | **Description**                                      |
|--------------|-----------------------------|------------------------------------------------------|
| `==`         | `{ "key": "x", "op": "==", "value": 5 }` | Equality check.                                      |
| `!=`         | `{ "key": "status", "op": "!=", "value": "draft" }` | Inequality check.                                    |
| `in`         | `{ "key": "roles", "op": "in", "value": ["admin", "editor"] }` | Membership test. |
| `regex`      | `{ "key": "account_id", "op": "regex", "value": "^[a-z]+" }` | Regex match. |
| `and`/`or`   | `[ { "conditions": [ ... ] }, { "operator": "and" } ]` | Logical grouping. |

**Complex Example:**
```json
{
  "conditions": [
    {
      "key": "user.role",
      "op": "in",
      "value": ["admin", "superuser"]
    },
    {
      "key": "order.status",
      "op": "==",
      "value": "pending"
    }
  ],
  "operator": "and"
}
```

---

### **Related Patterns**
1. **[Policy-Based Access Control (PBAC)](https://docs.oasis-open.org/odata/abac/v1.0/os/abac-v1.0-os.html)**
   - **Relation**: Authorization Guidelines can be implemented as PBAC policies. PBAC provides a broader framework for dynamic attributes and external policy repositories.

2. **[Role-Based Access Control (RBAC)](https://www.ietf.org/rfc/rfc4648.txt)**
   - **Relation**: Guidelines can model RBAC roles via the `inherits_from` field. Unlike RBAC’s static roles, this pattern allows runtime-based overrides.

3. **[Attribute-Based Access Control (ABAC)](https://www.nist.gov/topics/information-security/attribute-based-access-control-abac)**
   - **Relation**: ABAC systems often use guideline-like policies. This pattern simplifies ABAC by bundling conditions into reusable schemas.

4. **[Open Policy Agent (OPA) Rego](https://www.openpolicyagent.org/docs/latest/policy-language/)**
   - **Relation**: OPA’s Rego language is a mature implementation of policy-as-code. Guidelines can be translated to Rego rules for execution in OPA.

5. **[Least Privilege](https://cheatsheetseries.owasp.org/cheatsheets/Least_Privilege_Cheat_Sheet.html)**
   - **Relation**: Guidelines inherently enforce least privilege by defining minimal required permissions.

---

### **Best Practices**
1. **Idempotency**: Design guidelines to avoid conflicting rules (e.g., use highest-priority matches).
2. **Documentation**: Annotate each guideline with business rationale (e.g., "Why `delete` is blocked for `guest` roles").
3. **Testing**: Mock context providers to test edge cases (e.g., missing user attributes).
4. **Performance**: Cache evaluated results for frequent requests (e.g., user sessions).
5. **Audit Logs**: Log guideline evaluations for compliance (include `guideline_name`, `context`, `result`).

---
### **Example Workflow**
1. **Define**:
   ```yaml
   name: order_cancel_allowlist
   applies_to: { route: "/api/orders/:id/actions/cancel" }
   actions: ["cancel"]
   conditions:
     - { key: "user.company", "op": "==", "value": "acme" }
   priority: 5
   ```
2. **Evaluate**:
   ```python
   context = { "user": { "company": "acme" }, "resource": { "id": "789" } }
   result = evaluate_guideline(guideline, context)  # Returns True
   ```

---
### **Anti-Patterns**
- **Overly Granular Rules**: Avoid thousands of single-use guidelines (increase complexity).
- **Static Conditions**: Hardcoding values (e.g., `value: "admin"`) reduces flexibility.
- **Circular Inheritance**: Guidelines referencing each other creates evaluation loops.
- **Unbounded Fallbacks**: Defaulting to `allow` in production risks security breaches.