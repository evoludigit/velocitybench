---

# **[Pattern] Authorization Testing Reference Guide**

---

## **Overview**
The **Authorization Testing** pattern ensures that application logic enforces permissions correctly by validating that users, roles, or service accounts can or cannot perform specific actions based on defined rules. This pattern tests auth mechanisms (e.g., JWT validation, role-based access control (RBAC), or attribute-based access control (ABAC)) to prevent unauthorized access and verify compliance with security policies.

Use cases include:
- Validating that users interact with resources **only** when authorized.
- Testing edge cases (e.g., permission escalation, revoked tokens).
- Simulating malicious intent (e.g., testing brute-force auth attempts).
- Auditing auth changes (e.g., role assignment, password policies).

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                                                                 |
|-------------------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Test Scenario**       | A structured sequence of requests/actions to verify auth logic.              | *"Verify that an 'Admin' role can delete a project, but 'Guest' cannot."* |
| **Auth Rule**           | A policy defining allowed/disallowed actions (e.g., `role='Editor' → delete=true`). | `{ "action": "update", "resource": "user_profile", "required_role": "Manager" }` |
| **Assertion**           | A condition checked post-test (e.g., `HTTP 403 Forbidden` for unauthorized access). | `Response.status === 403` if user lacks permissions.                        |
| **Faker/Stub**          | Mock data to simulate users, roles, or auth tokens.                          | Generate a fake JWT token with a `user_id=123` and `role=Viewer`.          |
| **Edge Case**           | Unexpected scenarios (e.g., expired token, empty role list).                 | Test behavior when `auth_header` is malformed.                             |
| **Audit Log**           | Record of auth-related events (e.g., login attempts, permission denials).    | Log: `"User=abc123 failed to access /api/data (Missing 'Admin' role)"`.    |

---

## **Implementation Details**

### **1. Setting Up Test Data**
Use fakers/stubs to create test users and auth contexts:
```javascript
// Example: Faker library for generating test users
import { faker } from '@faker-js/faker';
const testUser = {
  id: faker.string.uuid(),
  username: faker.internet.userName(),
  roles: ['Viewer'] // Simulate role assignment
};
```

### **2. Auth Rule Validation**
Test rules against **expected outcomes**:
| **Rule Type**       | **Test Scenario**                          | **Expected Result**                     |
|---------------------|--------------------------------------------|------------------------------------------|
| **JBAC (JWT)**      | Verify token with expired `exp` field      | `401 Unauthorized`                       |
| **RBAC**            | Check if `role='Editor'` can `edit=true`   | `200 OK` (if policy allows)              |
| **ABAC**            | Test time-based access (e.g., `9am–5pm`)    | `403 Forbidden` outside hours            |
| **Dynamic Role**    | Validate role override (e.g., `super_admin`) | `200 OK` (even for restricted actions)  |

### **3. Testing Flow**
1. **Setup**: Inject mock auth context (e.g., headers, cookies).
2. **Execute**: Send authenticated request (e.g., `POST /api/update`).
3. **Assert**: Verify response matches auth rule outcome.
4. **Audit**: Log failures (e.g., `role_mismatch` errors).

---
## **Schema Reference**
Below is a schema for defining auth test cases. Use this to structure test configurations.

| **Field**               | **Type**       | **Description**                                                                 | **Example Value**                          |
|-------------------------|---------------|-------------------------------------------------------------------------------|--------------------------------------------|
| `test_name`             | String        | Human-readable test identifier.                                               | `"delete_project_with_admin_role"`         |
| `user`                  | Object        | Test user attributes (e.g., roles, token).                                   | `{ "id": 1, "roles": ["Admin"] }`           |
| `action`                | String        | API endpoint/action being tested.                                             | `/projects/123/delete`                    |
| `method`                | String        | HTTP method (GET, POST, etc.).                                                | `DELETE`                                   |
| `expected_status`       | Number        | Predicted HTTP status code.                                                    | `200` or `403`                             |
| `auth_header`           | String        | Mock auth token/cookie (if applicable).                                       | `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `policy`                | Object        | Auth rule (e.g., required role/resource).                                     | `{ "required_role": "Manager", "resource": "project" }` |
| `assertions`            | Array         | Post-request checks (e.g., response body validation).                         | `[ { "key": "success", "expected": true } ]` |
| `edge_case`             | Boolean       | Flag for testing unusual scenarios (e.g., null token).                       | `true`                                     |

---
## **Query Examples**
### **Example 1: Testing RBAC with a Valid Role**
```javascript
const testCase = {
  test_name: "edit_user_profile_with_editor_role",
  user: { id: 456, roles: ["Editor"] },
  action: "/api/users/me/profile",
  method: "PUT",
  expected_status: 200,
  policy: { required_role: "Editor", resource: "profile" },
  assertions: [
    { key: "message", expected: "Profile updated" }
  ]
};
// Execute:
const response = await apiRequest(testCase.method, testCase.action, {
  Authorization: `Bearer ${generateMockJWT(testCase.user)}`,
});
expect(response.status).toBe(testCase.expected_status);
```

### **Example 2: Testing JWT Expiration**
```javascript
const expiredToken = generateJWT({ exp: Math.floor(Date.now() / 1000) - 3600 }); // Expired 1 hour ago
const response = await apiRequest("GET", "/api/protected", {
  Authorization: `Bearer ${expiredToken}`,
});
expect(response.status).toBe(401); // Expired token denied access
```

### **Example 3: Testing Dynamic Role Override**
```javascript
const requestBody = {
  action: "force_role_override",
  new_role: "super_admin"
};
const response = await apiRequest("POST", "/api/admin/override", {
  Authorization: `Bearer ${generateJWT({ roles: ["Viewer"] })}`,
  body: requestBody
});
// Verify admin-like access was granted despite original role
expect(response.status).toBe(200);
```

### **Example 4: Testing ABAC Time-Based Restriction**
```javascript
// Simulate a time outside business hours (e.g., 9pm)
jest.useFakeTimers("modern");
jest.setSystemTime(new Date("2023-10-01T21:00:00"));
const response = await apiRequest("GET", "/api/billing", {
  Authorization: `Bearer ${generateJWT({ role: "Manager" })}`,
});
expect(response.status).toBe(403); // Restricted outside hours
```

---
## **Related Patterns**
1. **Token Validation**
   - Focus: Verify JWT/OAuth token integrity (e.g., signature, claims).
   - *Reference*: [Token Validation Testing Pattern](link).

2. **Role Assignment Auditing**
   - Focus: Track role changes and detect anomalies (e.g., sudden promotions).
   - *Reference*: [Audit Logging Pattern](link).

3. **Permission Granularity Testing**
   - Focus: Test fine-grained permissions (e.g., row-level access in databases).
   - *Reference*: [Row-Level Security Testing](link).

4. **Permission Reconciliation**
   - Focus: Ensure user permissions align with system policies post-change.
   - *Reference*: [Policy Synchronization Pattern](link).

5. **Brute-Force Protection**
   - Focus: Test how the system handles repeated auth failures.
   - *Reference*: [Rate Limiting Testing](link).

---
## **Best Practices**
1. **Isolate Tests**: Use separate test environments for auth testing to avoid polluting production data.
2. **Reusable Assertions**: Define helper functions for common checks (e.g., `assert403(response)`).
3. **Parameterize Rules**: Dynamically generate test cases from a ruleset (e.g., spreadsheets or YAML).
4. **Mock Dependencies**: Replace real auth services (e.g., Auth0, AWS Cognito) with fakes during tests.
5. **Document Policies**: Store auth rules in a machine-readable format (e.g., Open Policy Agent) for test generation.