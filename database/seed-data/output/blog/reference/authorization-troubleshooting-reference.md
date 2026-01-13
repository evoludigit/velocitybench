**[Pattern] Authorization Troubleshooting Reference Guide**

---

### **Overview**
This guide provides a systematic approach to diagnosing and resolving authorization-related issues in your application or system. Authorization failures can occur due to misconfigurations, policy conflicts, incorrect user permissions, or infrastructure issues. This reference outlines common failure scenarios, debugging steps, and best practices for log analysis, permission validation, and dependency checks. Use this guide to isolate root causes, verify configurations, and implement fixes efficiently.

---

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Authorization Failure** | Occurs when a user or system requests access to a resource but lacks the necessary permissions.                                                                                                                                                                                                                                        |
| **Policy Engine**         | A component (e.g., JWT validators, attribute-based access control [ABAC], or role-based access control [RBAC]) that enforces rules to grant/reject requests.                                                                                                                                                     |
| **Permission**            | A defined right (e.g., `read`, `write`, `delete`) assigned to roles, groups, or users for specific resources.                                                                                                                                                                                                              |
| **Scope**                 | A context-specific permission (e.g., `user:profile:edit`). Scopes define the granularity of resource access.                                                                                                                                                                                                                |
| **Token Validation**      | Process of verifying the integrity and authenticity of authentication tokens (e.g., OAuth 2.0 access tokens, JWTs) before granting access.                                                                                                                                                                       |
| **IAM (Identity & Access Management)** | Services (e.g., IdenityServer, AWS IAM, Azure AD) managing identities, credentials, and access policies.                                                                                                                                                                                                              |
| **Cache Invalidation**    | Issue where stale authorization data in caches (e.g., Redis, in-memory stores) leads to incorrect permission evaluations.                                                                                                                                                                                               |
| **Resource Metadata**     | Attributes (e.g., `owner`, `sensitivity`) attached to resources that influence authorization decisions.                                                                                                                                                                                                          |

---

### **Schema Reference**
Below is a reference schema for authorization-related data structures. Adjust fields to match your implementation.

#### **1. Authorization Policy Schema**
| Field               | Type       | Description                                                                                                                                                                                                                                                                          |
|---------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| policy_id           | `string`   | Unique identifier for the policy.                                                                                                                                                                                                                                   |
| name                | `string`   | Human-readable name of the policy (e.g., `AdminAccessPolicy`).                                                                                                                                                                                                       |
| scope               | `string`   | The resource scope (e.g., `user:profile`, `project:data`).                                                                                                                                                                                                           |
| action              | `string`   | Permitted action (e.g., `read`, `update`).                                                                                                                                                                                                                          |
| subject_type        | `string`   | Type of entity granted access (e.g., `role`, `user`, `group`).                                                                                                                                                                                                         |
| subject_identifier  | `string`   | Identifier for the subject (e.g., `role:admin`, `user:john.doe`).                                                                                                                                                                                                     |
| conditions          | `array`    | Optional rules (e.g., `{ time: {lt: "2023-12-31"}}`) or resource attributes to validate.                                                                                                                                                                                 |
| effect              | `boolean`  | `true` (allow), `false` (deny). Default: `true`.                                                                                                                                                                                                                   |
| created_at          | `datetime` | Timestamp of policy creation.                                                                                                                                                                                                                                      |
| updated_at          | `datetime` | Last update timestamp.                                                                                                                                                                                                                                           |
| version             | `string`   | Policy version for tracking changes.                                                                                                                                                                                                                                |

#### **2. Token Schema (JWT/OAuth 2.0)**
| Field               | Type       | Description                                                                                                                                                                                                                                                                          |
|---------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| token               | `string`   | Base64-encoded JWT or OAuth 2.0 token.                                                                                                                                                                                                                                     |
| token_type          | `string`   | `bearer`, `refresh`, etc.                                                                                                                                                                                                                                          |
| expires_at          | `datetime` | Expiration timestamp.                                                                                                                                                                                                                                         |
| issuer              | `string`   | Authority that issued the token (e.g., `auth.example.com`).                                                                                                                                                                                                              |
| audience            | `string[]` | List of intended recipients.                                                                                                                                                                                                                                     |
| claims               | `object`   | Standard claims (e.g., `sub`, `scope`) or custom claims (e.g., `permissions`).                                                                                                                                                                                 |

#### **3. Resource Metadata Schema**
| Field               | Type       | Description                                                                                                                                                                                                                                                                          |
|---------------------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| resource_id         | `string`   | Unique identifier for the resource (e.g., `user:123`, `project:456`).                                                                                                                                                                                                          |
| owner               | `string`   | User/role owning the resource.                                                                                                                                                                                                                                      |
| sensitivity         | `string`   | Classification (e.g., `public`, `internal`, `confidential`).                                                                                                                                                                                                           |
| tags                | `string[]` | Labels for categorization (e.g., `["finance", "backup"]`).                                                                                                                                                                                                             |

---

### **Troubleshooting Steps**
Follow this workflow to diagnose authorization issues systematically.

#### **1. Classify the Failure**
Determine the type of authorization failure:
- **Permission Denied**: User lacks required scope/action.
- **Token Expired/Invalid**: Token is malformed, expired, or untrusted.
- **Policy Conflict**: Multiple conflicting policies exist.
- **IAM Misconfiguration**: Incorrect role assignments or service permissions.
- **Resource Unavailable**: Resource metadata or cached data is stale/incomplete.

#### **2. Gather Logs and Metrics**
Extract relevant logs from:
- **Application Logs**: Check for `AuthorizationFailed` or `PermissionDenied` errors.
  Example log entry:
  ```json
  {
    "level": "ERROR",
    "message": "Access denied to resource 'user:123' with scope 'profile:read'",
    "user_id": "user:456",
    "timestamp": "2023-10-15T14:30:00Z",
    "policy_id": "profile-read-policy"
  }
  ```
- **Policy Engine Logs**: Verify policy evaluation steps (e.g., ABAC/RBAC conditions).
- **Authentication Service Logs**: Confirm token validation status (e.g., issuer verification).
- **Cache Metrics**: Monitor cache hits/misses for authorization data.

#### **3. Validate Configuration**
- **Policy Rules**: Ensure no contradictory policies exist. For example:
  ```json
  // Conflicting policies:
  {
    "policy_id": "read-policy",
    "scope": "user:profile",
    "action": "read",
    "subject_type": "role",
    "subject_identifier": "guest",
    "effect": false // Denies read access
  }
  ```
- **Token Claims**: Decode JWT tokens to verify scopes and permissions.
  Use tools like [JWT Debugger](https://jwt.io/) or CLI tools:
  ```bash
  echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." | base64 -d | jq .
  ```
- **IAM Roles**: Confirm user/group assignments in IAM consoles or CLI:
  ```bash
  aws iam list-attached-user-policies --user-name john.doe
  ```

#### **4. Test Policy Evaluation**
Manually simulate policy evaluation using your framework’s CLI or API:
- **Example with Open Policy Agent (OPA):**
  ```bash
  opa eval --data file://policies.json --input file://request.json \
    'data.policy.user_access'
  ```
  **Request Input (`request.json`):**
  ```json
  {
    "input": {
      "user": "user:456",
      "resource": "user:123",
      "action": "read"
    }
  }
  ```
- **Example with AWS IAM Policy Simulator:**
  ```bash
  aws iam simulate-principal-policy --policy-arn arn:aws:iam::123456789012:policy/MyPolicy \
    --action-names "s3:GetObject" --resource-arns "arn:aws:s3:::my-bucket/*"
  ```

#### **5. Check Caching Layers**
- **Cache Invalidation**: Ensure cached authorization data is flushed on policy changes:
  ```python
  # Example: Redis cache invalidation (Python)
  cache_key = f"auth:user:{user_id}"
  redis_client.delete(cache_key)
  ```
- **Stale Data**: Verify cache TTLs and consistency mechanisms.

#### **6. Verify Resource Metadata**
- Confirm resource metadata aligns with policies. For example:
  - A policy requiring `owner:admin` should match the `owner` field in resource metadata.
  - Use APIs like:
    ```bash
    curl -X GET "https://api.example.com/resources/{id}" -H "Authorization: Bearer {token}"
    ```

#### **7. Test with Minimal Reproducible Example**
Create a minimal reproduction case (e.g., a curl request or unit test) to isolate the issue:
```bash
# Example: Failed API request
curl -X GET "https://api.example.com/profile/123" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -v
```

---

### **Query Examples**
Use these SQL-like queries (adapted for your policy engine or data store) to debug policies.

#### **1. Find Conflicting Policies for a Scope/Action**
```sql
SELECT p.*
FROM policies p
WHERE p.scope = 'user:profile'
  AND p.action = 'read'
  AND p.effect = false;
```

#### **2. List Users Missing a Specific Permission**
```sql
SELECT u.user_id, u.username
FROM users u
JOIN user_permissions up ON u.user_id = up.user_id
WHERE up.permission = 'profile:read'
  AND NOT EXISTS (
    SELECT 1 FROM assigned_policies ap
    WHERE ap.user_id = u.user_id
      AND ap.policy_id IN (
        SELECT policy_id FROM policies
        WHERE scope = 'user:profile'
          AND action = 'read'
          AND effect = true
      )
  );
```

#### **3. Check Token Scopes Against Policy Requirements**
```sql
SELECT t.token, t.user_id, p.scope, p.action
FROM tokens t
JOIN policies p ON t.user_id = p.subject_identifier
WHERE p.effect = true
  AND t.scopes NOT LIKE '%' || p.scope || '%'
  AND t.expires_at < NOW();
```

#### **4. Audit Policy Changes**
```sql
SELECT p.policy_id, p.name, p.effect, u.username, u.change_timestamp
FROM policies p
JOIN policy_changes u ON p.policy_id = u.policy_id
WHERE u.change_timestamp > DATEADD(day, -7, GETDATE())
ORDER BY u.change_timestamp DESC;
```

---

### **Common Pitfalls and Fixes**
| **Pitfall**                          | **Symptom**                                  | **Solution**                                                                                                                                                                                                                                                                 |
|---------------------------------------|---------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Overly Permissive Policies**        | Unauthorized access to sensitive resources. | Audit policies with `effect = true` and refine scopes/actions.                                                                                                                                                                                                       |
| **Token Leakage**                     | Extracted tokens in logs or client-side.   | Rotate tokens immediately; enforce short-lived access tokens and refresh tokens separately.                                                                                                                                                                           |
| **Cache Stampedes**                   | Thundering herd problem during cache misses. | Implement token bucket or probabilistic early expiration.                                                                                                                                                                                                             |
| **Policy Versioning Mismatch**        | Users granted access under old policies.    | Use policy versions in claims and validate against the latest version.                                                                                                                                                                                                |
| **Resource Metadata Drift**           | Policies fail due to outdated metadata.    | Automate metadata sync with resource APIs or event-driven updates.                                                                                                                                                                                         |
| **Cross-Region IAM Misconfigurations** | Permissions not propagating across regions. | Use AWS Organizations or explicit trust policies.                                                                                                                                                                                                               |

---

### **Tools and Libraries**
| **Tool**                          | **Purpose**                                                                                                                                                                                                                                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Open Policy Agent (OPA)**       | Policy-as-code engine for dynamic authorization. Supports Rego language.                                                                                                                                                                                            |
| **AWS IAM Policy Simulator**      | Test IAM policies without affecting production.                                                                                                                                                                                                                      |
| **JWT Debugger**                  | Decode and validate JWT tokens.                                                                                                                                                                                                                                   |
| **Apache Griffin**                | Runtime policy enforcement for microservices.                                                                                                                                                                                                                           |
| **HashiCorp Sentinel**            | Policy-as-code for HashiCorp products (Terraform, Nomad).                                                                                                                                                                                                        |
| **Prometheus + Grafana**          | Monitor token expiration, cache hits, and policy evaluation times.                                                                                                                                                                                                |
| **Postman/Newman**                | Automate API tests for authorization flows.                                                                                                                                                                                                                               |

---

### **Related Patterns**
1. **[Authentication Patterns](link-to-auth-patterns)**
   - Focuses on securing user identities (e.g., OAuth 2.0, JWT).
2. **[Permission Management Patterns](link-to-permission-management)**
   - Best practices for assigning and revoking permissions.
3. **[Attribute-Based Access Control (ABAC)](link-to-abac)**
   - Dynamic authorization using resource attributes and environmental conditions.
4. **[Caching Strategies for Authorization](link-to-caching-patterns)**
   - Optimizing cache layers for low-latency authorization.
5. **[Multi-Factor Authentication (MFA)](link-to-mfa-patterns)**
   - Enhancing token security with additional verification steps.
6. **[Audit Logging for Authorization](link-to-audit-logging)**
   - Recording access attempts and policy evaluations for compliance.

---

### **Example Workflow: Troubleshooting a Permission Denied Error**
**Scenario**: User `john.doe` cannot access `profile:read` for resource `user:123`.

1. **Check Logs**:
   ```log
   [ERROR] Access denied to resource 'user:123' with scope 'profile:read' for user 'john.doe'.
   ```
2. **Validate Token**:
   ```bash
   jwt_decode eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
   Output:
   ```json
   {
     "sub": "user:456",
     "scopes": ["profile:read:own"],
     "exp": 1700000000
   }
   ```
   - **Issue**: Token scope is `profile:read:own`, but policy requires `profile:read`.

3. **Inspect Policy**:
   ```sql
   SELECT * FROM policies
   WHERE scope = 'user:123/profile/read';
   ```
   Output:
   ```json
   {
     "policy_id": "read-profile-policy",
     "scope": "user:profile",
     "action": "read",
     "subject_identifier": "role:admin",
     "effect": true
   }
   ```
   - **Issue**: Policy targets `role:admin`, not `user:456`.

4. **Fix**:
   - Update policy to include `user:456` or grant `profile:read:own` scope to `john.doe`.
   - Or, update token to include `profile:read` scope.

5. **Verify Cache**:
   ```bash
   redis-cli GET auth:user:456:profile:read
   ```
   - If stale, invalidate cache:
     ```python
     cache.invalidate("auth:user:456:profile:read")
     ```

6. **Test**:
   Re-run the API call. If resolved, document the fix in your runbooks.

---
**References**:
- [OAuth 2.0 Token Validation](https://datatracker.ietf.org/doc/html/rfc6750)
- [ABAC Specifications](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-er01-20130729.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)