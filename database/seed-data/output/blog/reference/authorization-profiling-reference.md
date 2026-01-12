# **[Pattern] Authorization Profiling: Reference Guide**

---

## **Overview**
Authorization Profiling is a security pattern that enforces fine-grained access control by dynamically assigning roles or permissions ("profiles") to users or systems based on contextual attributes, rather than static configurations. This approach reduces manual permission management, improves compliance, and adapts to changing security policies. It is particularly useful in multi-tenant systems, zero-trust architectures, and environments with high turnover or evolving access requirements. By evaluating attributes like user location, device type, or application context, the system assigns temporary or situational permissions, mitigating risks like privilege escalation or data leaks. The pattern complements role-based access control (RBAC) by adding adaptability while maintaining auditability.

---

## **Key Concepts**

| **Concept**               | **Definition**                                                                                                                                                                                                 | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Profile**               | A dynamic set of permissions or roles assigned based on evaluated attributes. Profiles can be temporary or long-lived.                                                                                     | A profile granting "read-only" access while a user is outside the office but "edit" access while on-premises. |
| **Attribute Evaluator**   | A component that assesses contextual data (e.g., time, IP, device compliance) to determine applicable profiles.                                                                                              | A rule: *"If user’s device is compliant AND location is corporate network → assign `Admin` profile."* |
| **Profile Registry**      | A repository storing predefined profiles, their rules, and associated permissions.                                                                                                                            | A database table listing profiles like `Guest`, `Contractor`, and `Executive`, each with JSON-specified permissions. |
| **Context Provider**      | A service (e.g., LDAP, SIEM, or custom API) that supplies real-time or historical data for attribute evaluation.                                                                                              | An API call to a SIEM tool to verify device health before assigning a profile.                  |
| **Decision Engine**       | The logic layer that matches attributes to profiles and enforces permissions. Can be rule-based (e.g., Drools), policy-based (e.g., Open Policy Agent), or AI-driven.                                    | A decision engine selecting the `AuditOnly` profile for users accessing sensitive data from a non-corporate device. |
| **Audit Log**             | Records of profile assignments, attribute checks, and permission denials for compliance and forensics.                                                                                                         | A log entry: *"User: john.doe → Profile: `Guest` → Attributes: `device=uncompliant, location=public`."* |

---

## **Implementation Details**

### **1. Architecture Components**
Authorization Profiling requires five core components (see diagram below):

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Context    │    │ Attribute   │    │ Decision    │    │ Profile     │    │ Audit       │
│  Provider   ├───▶│  Evaluator   ├───▶│  Engine      ├───▶│  Registry    ├───▶│  Log        │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```
- **Context Provider**: Supplies attributes (e.g., user geolocation via GPS, device compliance via MDM).
- **Attribute Evaluator**: Validates and enriches attributes (e.g., normalizing IP ranges or flagging anomalies).
- **Decision Engine**: Matches attributes to profiles using rules/policies (e.g., *"IF (attribute X AND NOT attribute Y) THEN profile Z"*).
- **Profile Registry**: Stores profiles and their permissions in a structured format (e.g., JSON, XACML policies).
- **Audit Log**: Captures profile assignments and rejections for traceability.

---

### **2. Profile Definition Schema**
Profiles are defined with **attributes**, **rules**, and **permissions**. Below is a reference schema (JSON example):

```json
{
  "profile_id": "audit-only",
  "description": "Profile for users accessing sensitive data from non-corporate devices",
  "attributes": [
    {
      "name": "device_compliance",
      "operator": "equals",
      "value": "false"
    },
    {
      "name": "user_location",
      "operator": "not_in",
      "value": ["corporate_network", "vpn"]
    }
  ],
  "rules": [
    {
      "condition": {
        "logical_operator": "AND",
        "attributes": ["device_compliance", "user_location"]
      },
      "action": "assign"
    }
  ],
  "permissions": [
    {
      "resource": "hr/payroll",
      "action": "read",
      "scope": "view_salary_only"
    }
  ],
  "expiration": "30m"  // Optional: Temporary profile
}
```

| **Field**          | **Type**       | **Description**                                                                                                                                                                                                 | **Example Value**                     |
|--------------------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------|
| `profile_id`       | String         | Unique identifier for the profile.                                                                                                                                                                         | `"audit-only"`                         |
| `description`      | String         | Human-readable explanation of the profile’s purpose.                                                                                                                                                       | *"Limited access for external auditors"* |
| `attributes`       | Array[Object]  | List of evaluated attributes (key-value pairs) that trigger the profile. Each attribute includes an `operator` (e.g., `equals`, `in`, `not_in`).                                                        | `[{"name": "device_compliance", ...}]` |
| `rules`            | Array[Object]  | Logical conditions (AND/OR) defining when the profile applies. Rules can reference multiple attributes.                                                                                                   | `[{"condition": {...}, "action": "assign"}]` |
| `permissions`      | Array[Object]  | Granular access controls (resource + action + scope). Resources can be URLs, database tables, or API endpoints.                                                                                               | `[{"resource": "finance/reports", ...}]` |
| `expiration`       | String (ISO 8601)| Duration or timestamp for profile validity (e.g., time-based access).                                                                                                                                           | `"P1D"` (1 day) or `"2024-01-01T00:00:00Z"`  |

---

### **3. Common Attribute Sources**
| **Attribute Category** | **Example Attributes**                          | **Data Source**                          |
|------------------------|-----------------------------------------------|------------------------------------------|
| User Identity          | `user_id`, `role`, `department`                | LDAP, OAuth, HRIS                          |
| Device Context         | `device_compliance`, `os_version`, `antivirus` | MDM (Mobile Device Management), EDR       |
| Network Context        | `ip_address`, `dns_domain`, `vpn_status`       | Firewall logs, SIEM (Splunk, ELK)         |
| Time-Based             | `current_time`, `time_zone`, `day_of_week`    | System clock, geolocation (GPS)            |
| Application Context    | `app_name`, `user_session_age`                | Application logs, JWT tokens               |
| Behavioral             | `login_frequency`, `click_pattern`            | UX analytics, behavioral AI               |

---

## **Query Examples**
### **1. Assigning a Profile Dynamically**
**Scenario**: A user accesses a system from a non-corporate device. Assign the `guest` profile.
**Request (REST API)**:
```http
POST /api/v1/profiles/assign
Headers:
  Content-Type: application/json
Body:
{
  "user_id": "user123",
  "context": {
    "device_compliance": "false",
    "user_location": "public_wifi"
  }
}
```
**Response**:
```json
{
  "profile_id": "guest",
  "permissions": [
    { "resource": "public_assets", "action": "read" }
  ],
  "expiration": "30m"
}
```

### **2. Evaluating Attributes for a Rule**
**Scenario**: Check if a user meets the criteria for the `admin` profile.
**Request (Rule Engine Query)**:
```plaintext
EVALUATE profile "admin"
WHERE
  user_id = "admin456"
  AND device_compliance = true
  AND user_location IN ["corporate_network", "vpn"]
```
**Response**:
```json
{
  "profile_assigned": true,
  "permissions": [
    { "resource": "*", "action": "read_write" }
  ]
}
```

### **3. Auditing Profile Assignments**
**Query (Audit Log)**:
```sql
SELECT
  user_id,
  profile_id,
  assigned_at,
  attributes,
  decision_outcome
FROM audit_logs
WHERE profile_id = 'audit-only'
  AND assigned_at > NOW() - INTERVAL '1 hour'
ORDER BY assigned_at DESC;
```
**Result**:
| `user_id` | `profile_id` | `assigned_at`       | `attributes`                          | `decision_outcome` |
|-----------|--------------|---------------------|---------------------------------------|---------------------|
| john.doe  | audit-only   | 2024-01-15 09:30:00 | `{"device_compliance": "false"}`    | `assigned`          |

---

## **Implementation Steps**
1. **Define Profiles**:
   - Create profile templates in the **Profile Registry** (e.g., `Guest`, `Contractor`, `Executive`).
   - Example: Use Terraform or Ansible to deploy profiles to a central store (e.g., Redis, PostgreSQL).

2. **Integrate Context Providers**:
   - Connect to sources like:
     - LDAP for user attributes (`dn`, `department`).
     - SIEM tools (e.g., Splunk) for network context (`ip_address`).
     - MDM (e.g., Microsoft Intune) for device compliance.

3. **Build the Decision Engine**:
   - **Option A**: Use a rule engine like **Drools** or **Easy Rules** for simple logic.
   - **Option B**: Deploy **Open Policy Agent (OPA)** for policy-as-code.
   - **Option C**: Train a lightweight ML model (e.g., XGBoost) to score risk and assign profiles dynamically.

4. **Enforce Permissions**:
   - Integrate with your authorization layer (e.g., **Casbin**, **Auth0**, or **AWS IAM**).
   - Example: Modify an RBAC policy dynamically:
     ```plaintext
     # Casbin Policy Rule (Temporary)
     p, user123, guest, read, public_assets
     ```

5. **Audit and Monitor**:
   - Log all profile assignments/rejections to a database (e.g., Elasticsearch).
   - Set up alerts for anomalies (e.g., "Profile `admin` assigned to non-admin user").

---

## **Query Examples (Advanced)**
### **1. Real-Time Profile Assignment (gRPC)**
**Request**:
```protobuf
rpc AssignProfile(AssignProfileRequest) returns (ProfileAssignment) {
  message AssignProfileRequest {
    string user_id = 1;
    map<string, string> context = 2; // e.g., {"device_compliance": "true"}
  }
  message ProfileAssignment {
    string profile_id = 1;
    repeated Permission permissions = 2;
    string expiration = 3;
  }
}
```
**Response**:
```json
{
  "profile_id": "editor",
  "permissions": [
    { "resource": "docs/**", "action": "create_update" }
  ],
  "expiration": "PT1H" // 1 hour
}
```

### **2. Batch Profile Validation (GraphQL)**
**Query**:
```graphql
query ValidateProfiles($users: [String!]!, $context: AttributeInput!) {
  validateProfiles(users: $users, context: $context) {
    userId
    profileId
    isAllowed
    reason
  }
}
```
**Variables**:
```json
{
  "users": ["alice", "bob"],
  "context": {
    "device_compliance": "true",
    "user_location": "corporate_network"
  }
}
```
**Result**:
```json
{
  "data": {
    "validateProfiles": [
      { "userId": "alice", "profileId": "editor", "isAllowed": true },
      { "userId": "bob", "profileId": "guest", "isAllowed": false, "reason": "Device not compliant" }
    ]
  }
}
```

---

## **Performance Considerations**
- **Attribute Evaluation Overhead**: Minimize expensive queries (e.g., avoid real-time SIEM calls for every request). Cache attributes (e.g., Redis) for high-frequency checks.
- **Decision Engine Latency**: Use lightweight engines (e.g., Easy Rules) for low-latency scenarios. Offload complex logic to microservices.
- **Profile Registry Scalability**: Shard profiles by tenant (multi-tenancy) or use a distributed cache (e.g., DynamoDB Global Tables).
- **Audit Log Volume**: Compress logs or sample high-volume events to reduce storage costs.

---

## **Security Considerations**
- **Profile Escape**: Ensure no profile can silently escalate permissions (e.g., validate rules in a sandbox).
- **Attribute Tampering**: Sign context data (e.g., JWT) to prevent spoofing.
- **Profile Registry Access**: Restrict writes to the registry to security teams only.
- **Expiring Profiles**: Automatically revoke permissions after `expiration` to reduce dwell time.
- **Zero Trust**: Combine with other patterns like **Attribute-Based Access Control (ABAC)** for granular control.

---

## **Related Patterns**
| **Pattern**                          | **Description**                                                                                                                                               | **When to Use Together**                                                                                     |
|--------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| **Attribute-Based Access Control (ABAC)** | Grants permissions based on attributes like time, location, or device state. Similar to profiling but often stateless.                                      | Use ABAC for simple attribute checks; use Profiling for dynamic, multi-attribute workflows.               |
| **Role-Based Access Control (RBAC)**  | Assigns permissions via roles (e.g., `Admin`, `Editor`). Profiling can derive roles dynamically.                                                               | Combine RBAC with Profiling to assign roles based on contextual attributes (e.g., "Temp Admin" role).       |
| **Just-In-Time Provisioning (JIT)**   | Temporarily grants access (e.g., MFA approval). Profiling can automate JIT based on attributes.                                                                | Use Profiling to auto-approve JIT requests when conditions (e.g., `device_compliance = true`) are met.        |
| **Zero Trust Network Access (ZTNA)**  | Verifies every access request without trust in networks. Profiling can define access policies for ZTNA gateways.                                              | Deploy Profiling in ZTNA to dynamically allow/deny access to apps based on device or user state.              |
| **Policy as Code (PaC)**               | Manages security policies (e.g., OPA) in version control. Profiling rules can be expressed as policies.                                                          | Store Profile definitions in Git and enforce with OPA for auditability.                                     |
| **Least Privilege (LPP)**              | Grants minimal access. Profiling enforces least privilege by dynamically assigning tight permissions based on context.                                        | Use Profiling to ensure users only get permissions needed for their current task (e.g., "Audit Mode").     |
| **Continuous Authentication**        | Validates user identity during sessions. Profiling can adjust permissions based on ongoing behavior (e.g., device risk score).                                | Combine with Profiling to revoke permissions if a device becomes compromised during a session.              |

---
## **Tools and Technologies**
| **Category**               | **Tools/Frameworks**                                                                                                                                                     | **Use Case**                                                                                             |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Rule Engines**           | Drools, Easy Rules, OpenPeppol                                                                                                                                       | Execute complex attribute-based rules.                                                                |
| **Policy-as-Code**         | Open Policy Agent (OPA), AWS IAM Policy Simulator, Azure Policy                                                                                                          | Enforce profiles via declarative policies.                                                             |
| **Context Providers**      | SIEM (Splunk, ELK), MDM (Intune, Jamf), OAuth/OIDC, Custom APIs                                                                                                        | Fetch real-time attributes (e.g., device health, IP location).                                         |
| **Authorization Layers**   | Casbin, Auth0, AWS Cognito, Azure AD                                                                                                                                 | Enforce profile-derived permissions at runtime.                                                          |
| **Audit Logging**          | ELK Stack, Datadog, Splunk, Custom databases                                                                                                                          | Store and analyze profile assignment logs.                                                              |
| **Caching**                | Redis, Memcached, HashiCorp Consul                                                                                                                                      | Cache frequent attribute evaluations to reduce latency.                                                  |
| **Orchestration**          | Kubernetes (with OPA sidecars), Terraform, Ansible                                                                                                                   | Deploy and manage profiles dynamically in cloud-native environments.                                   |

---
## **Example Workflow: Dynamic Access for Field Engineers**
1. **Context Provided**:
   - User: `engineer42`, Location: `customer_site`, Device: `corporate_laptop`, Time: `09:00 AM`.
   - Attributes:
     ```json
     { "user_role": "field_engineer", "device_compliance": "true", "location": "customer_site" }
     ```

2. **Decision Engine Evaluates**:
   - Rule: *"IF (user_role = 'field_engineer' AND location = 'customer_site' AND device_compliance) THEN profile = 'on_site_access'"* → **Match**.

3. **Profile Assigned**:
   ```json
   {
     "profile_id": "on_site_access",
     "permissions": [
       { "resource": "customer_portal/*", "action": "read_write" },
       { "resource": "inventory", "action": "view" }
     ],
     "expiration": "P1D"  // Expires after 1 day
   }
   ```

4. **Audit Log Entry**:
   ```json
   {
     "user_id": "engineer42",
     "profile_id": "on_site_access",
     "assigned_at": "2024-01-15T09:00:00Z",
     "attributes": { "location": "customer_site" },
     "decision_out