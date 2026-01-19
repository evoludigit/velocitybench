# **[Pattern] Authorization Troubleshooting – Reference Guide**

---
## **Overview**
Authorization Troubleshooting is a structured pattern for diagnosing and resolving access-control failures in applications. When users encounter permission errors (e.g., "403 Forbidden"), developers must methodically inspect:
- **Authentication state** (valid tokens, sessions)
- **Role/permission mappings** (RBAC, ABAC, attribute validation)
- **Resource-level policies** (IAM, ACLs, fine-grained rules)
- **Policy cache** (staleness, propagation delays)
- **Configuration drift** (misaligned policies vs. infrastructure)

This guide outlines systematic steps to identify bottlenecks, validate policies, and apply fixes while minimizing downtime.

---

## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Common Pitfalls**                                                                 |
|------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Policy Evaluation**  | The process of checking user attributes (roles, claims) against resource-specific rules.       | Outdated role assignments, missing transitive permissions.                         |
| **Policy Cache**       | Local/remote storage of evaluated permissions to reduce latency (e.g., AWS IAM cache).           | Stale cache overwriting real-time changes (e.g., after IAM policy updates).       |
| **Least Privilege**    | Granting minimal permissions required for a task (best practice).                                  | Over-permissive policies (e.g., `*` wildcard for S3 buckets).                    |
| **Policy Conflict**    | Contradictory rules (e.g., deny/allow overlap) in multi-policy contexts (e.g., AWS Organizations). | Unintentional inheritance of conflicting rules from parent accounts.              |
| **Contextual Authorization** | Dynamic checks (e.g., time-based access, IP restrictions) beyond static roles.             | Overlooking environment-specific rules (e.g., staging vs. production).           |

---

## **Schema Reference**
**1. Common Authorization Models**

| **Model**               | **Description**                                                                                     | **Example Tools**                          |
|-------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------|
| **Role-Based (RBAC)**   | Assigns permissions to roles; users inherit permissions via roles.                                 | AWS IAM, Azure RBAC, Keycloak              |
| **Attribute-Based (ABAC)** | Evaluates attributes (user/group/environment) against policies (e.g., `requester in "admin" AND time in "9am-5pm"`). | Open Policy Agent (OPA), AWS IAM Conditions |
| **Claim-Based**         | Validates JWT/OAuth claims (e.g., `scope: "read:data"`).                                           | Auth0, Okta                                |
| **Resource-Based**      | Policies attached to resources (e.g., S3 bucket policies).                                         | AWS IAM, Kubernetes RBAC                   |

**2. Error Codes & Meanings**

| **Code** | **HTTP Response** | **Likely Cause**                                                                 | **Troubleshooting Steps**                                                                 |
|----------|-------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| `401`    | Unauthorized      | Invalid/missing credentials (authentication failure).                          | Verify JWT signature, refresh tokens, check session cookies.                             |
| `403`    | Forbidden         | Valid auth but insufficient permissions.                                         | Audit RBAC roles, check policy conditions, test with `aws iam simulate-principal-policy`. |
| `409`    | Conflict          | Policy conflict (e.g., explicit deny overrides allow).                          | Use `aws iam get-effective-policy` to reconcile rules.                                  |
| `500`    | Internal Error    | Policy evaluation failure (e.g., malformed JSON).                                | Check logs for `PolicyEvaluationException` (AWS), validate syntax with `opal validate`.   |

**3. Policy Fields (AWS IAM Example)**

| **Field**         | **Purpose**                                                                                     | **Example Value**                          | **Validation Rule**                                  |
|-------------------|-------------------------------------------------------------------------------------------------|--------------------------------------------|-----------------------------------------------------|
| `Effect`          | Specifies `Allow`/`Deny`.                                                                       | `"Allow"`                                  | Must be `Allow` or `Deny`.                          |
| `Action`          | List of permissions (e.g., `s3:GetObject`).                                                     | `"s3:GetObject", "s3:ListBucket"`          | Wildcards (`*`) disallowed if strict enforcement.  |
| `Resource`        | ARN/resource path to protect.                                                                   | `"arn:aws:s3:::my-bucket/*"`               | Must use exact ARN (no `*` unless explicitly allowed).|
| `Condition`       | Dynamic checks (e.g., `aws:SourceIP`).                                                          | `"aws:SourceIP": ["192.0.2.0/24"]`         | Keys must match AWS condition keys.                   |
| `Principal`       | Who the rule applies to (e.g., another AWS account).                                           | `"AWS": ["arn:aws:iam::123456789012:root"]` | Must be a valid AWS entity ARN.                     |

---

## **Troubleshooting Workflow**
Follow this step-by-step approach:

### **1. Reproduce the Issue**
- **Steps**:
  1. Record the **exact user action** (e.g., "User Alice clicks ‘Export Report’ in Dashboard").
  2. Capture **error details** (HTTP code, timestamp, policy evaluation logs).
  3. Verify the **user’s credentials** (e.g., `aws sts get-caller-identity`).
- **Tools**:
  - Browser DevTools (Network tab for API calls).
  - CloudTrail (AWS), Audit Logs (Azure).

### **2. Validate Authentication**
- **Checks**:
  - Is the token valid? Use `jwt.io` or `curl -X POST https://token-endpoint/introspect`.
  - Are claims present? Look for `exp`, `iat`, `roles`, or `permissions` in the payload.
- **Example (JWT Decoding)**:
  ```bash
  curl -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "token=$TOKEN" \
    https://auth0.com/oauth/token/introspect
  ```

### **3. Simulate Policy Evaluation**
- **RBAC (AWS IAM)**:
  ```bash
  aws iam simulate-principal-policy \
    --policy-arn arn:aws:iam::123456789012:policy/MyAppPolicy \
    --action-names s3:GetObject \
    --resource-arns arn:aws:s3:::my-bucket/data.csv
  ```
- **ABAC (Open Policy Agent)**:
  ```bash
  opal eval my_policy.rego \
    --input '{"user": {"roles": ["admin"]}, "resource": {"type": "report"}}'
  ```

### **4. Inspect Policy Caching**
- **AWS IAM Cache**: Policies are cached for **5 minutes** after update.
  ```bash
  aws iam list-policies --scope Local
  ```
- **OPA Cache**: Restart the OPA server or clear cache:
  ```bash
  opa serve --cache-size 0  # Disable caching (dev mode)
  ```

### **5. Check for Conflicts**
- **AWS Organizations SCPs**:
  ```bash
  aws organizations list-policies --policy-type SERVICE_CONTROL_POLICY
  ```
- **Example Conflict**: A **deny** in an SCP overrides an **allow** in IAM.

### **6. Test with Minimal Policies**
- **Isolate the Issue**: Temporarily replace the entire policy with a minimal `Allow`/`Deny` rule.
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::my-bucket/data.csv"
      }
    ]
  }
  ```

### **7. Review Recent Changes**
- **Git History**: Check for policy updates in the last 24 hours.
- **Infrastructure Drift**: Compare deployed policies with source (e.g., Terraform state):
  ```bash
  terraform show -json | jq '.values.root_module.resources[] | select(.type == "aws_iam_policy")'
  ```

### **8. Escalate if Necessary**
- **Permission Boundaries**: Check if the user’s role is constrained by a boundary policy.
- **Vendor Support**: For cloud providers, check their status pages (e.g., AWS Health Dashboard).

---

## **Query Examples**
### **1. AWS CLI: Check Effective Permissions**
```bash
# Get effective permissions for a role/principal
aws iam get-effective-policy \
  --target-arn arn:aws:iam::123456789012:role/AppRole

# Simulate a policy for a user
aws iam simulate-principal-policy \
  --policy-arn arn:aws:iam::123456789012:policy/MyPolicy \
  --action-names s3:*
  --resource-arns arn:aws:s3:::my-bucket/*
```

### **2. Open Policy Agent (OPA): Evaluate a Policy**
```bash
# Define a policy (my_policy.rego)
package example
default allow = false
allow {
  input.user.role == "admin"
  input.action == "write"
}
# Evaluate
opal eval my_policy.rego \
  --input '{"user": {"role": "editor"}, "action": "write"}'
```

### **3. Kubernetes RBAC: Debug Denied Requests**
```bash
# Check audit logs for a denied request
kubectl audit log | grep -i "forbidden"

# Test if a user can list pods
kubectl auth can-i list pods --as=alice
```

### **4. Azure AD: Check User Permissions**
```bash
# Get a user’s assigned roles
az ad user show --id "user@domain.com" --query "assignedRoles"
```

---

## **Related Patterns**
1. **[Authentication Troubleshooting]**
   - Focuses on validating tokens, sessions, and OAuth flows before authorization checks.

2. **[Policy-as-Code Best Practices]**
   - Guidelines for writing maintainable IAM/OPA policies (e.g., modular policies, tests).

3. **[Zero-Trust Architecture]**
   - Integrates dynamic authorization (e.g., time-based, device checks) into access control.

4. **[Audit Logging for Authorization]**
   - Designing logs to track policy violations (e.g., AWS CloudTrail, Splunk).

5. **[Fine-Grained Access Control]**
   - Techniques for ABAC (e.g., using Open Policy Agent with Kubernetes RBAC).

---
**Key Takeaway**: Authorization issues often stem from **policy misconfigurations** or **cache staleness**. Always validate policies in isolation and check for conflicts between layers (e.g., IAM vs. SCP). For dynamic environments, automate policy testing (e.g., GitHub Actions + OPA).