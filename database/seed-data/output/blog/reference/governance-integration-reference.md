# **[Pattern] Governance Integration – Reference Guide**

---

## **Overview**
The **Governance Integration** pattern enables seamless alignment between software systems and enterprise governance frameworks (e.g., **GRC**, **ITIL**, **SOX**, **NIST**, **ISO 27001**). This pattern ensures compliance, risk management, and policy enforcement by embedding governance controls directly into application workflows.

Governance Integration prevents siloed compliance efforts by:
- Automating policy checks (e.g., access controls, audit logs).
- Centralizing governance data via APIs, event streams, or database hooks.
- Providing audit trails for regulatory requirements (e.g., **GDPR**, **HIPAA**).
- Reducing manual intervention with automated remediation workflows.

---
### **Key Use Cases**
| Scenario                     | Benefit                          |
|------------------------------|----------------------------------|
| **Regulatory compliance**    | Automate audit reports (SOX, PCI). |
| **Identity & Access Mgmt**    | Enforce least-privilege policies. |
| **Data governance**          | Track data lineage and access.   |
| **Incident response**        | Trigger remediation via SIEM.    |
| **Third-party risk**         | Validate vendor compliance.      |

---

## **Core Components**
Governance Integration relies on four foundational elements:

| **Component**          | **Description**                                                                 | **Implementation**                                                                 |
|------------------------|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Governance API**     | REST/gRPC endpoints to query policies, roles, and compliance status.              | Expose CRUD APIs for policy rules (e.g., `/api/policies/{policyId}`).            |
| **Event Bus/Stream**   | Real-time governance events (e.g., policy violations, role changes) via **Kafka**, **Webhooks**, or **MQTT**. | Stream compliance events to a centralized **SIEM** or **audit log**.          |
| **Database Hooks**     | Embed governance checks into database operations (e.g., PostgreSQL **PL/pgSQL**, **SQL Server Triggers**). | Trigger checks on `INSERT/UPDATE/DELETE` via stored procedures.                 |
| **Remediation Engine** | Automated fixes for policy violations (e.g., revoking access, escalating tickets). | Integrate with **Jira**, **Slack**, or **SOAR** platforms for workflows.         |

---

## **Schema Reference**

### **1. Policy Schema**
Defines governance rules (e.g., mandatory fields, access controls).

```json
{
  "id": "string (UUID)",
  "name": "string (e.g., 'PCI-DSS_V4')",
  "scope": "string (e.g., 'finance', 'hr')",
  "type": "enum ('access', 'data', 'audit', 'incident')",
  "rule": {
    "condition": "string (e.g., 'user.role == "admin"')",
    "action": "enum ('deny', 'warn', 'escalate')",
    "severity": "enum ('low', 'medium', 'high', 'critical')"
  },
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

**Example Query (Find all high-severity access policies for 'finance'):**
```sql
SELECT * FROM policies
WHERE scope = 'finance' AND rule.severity = 'high' AND rule.type = 'access';
```

---

### **2. Governance Event Schema**
Tracks compliance-related actions (e.g., access requests, violations).

```json
{
  "eventId": "string (UUID)",
  "policyId": "string (reference)",
  "userId": "string (optional)",
  "action": "string (e.g., 'ACCESS_GRANTED', 'VIOLATION_DETECTED')",
  "timestamp": "datetime",
  "details": {
    "resource": "string (e.g., 'customer_records_table')",
    "impact": "string (e.g., 'PII_exposure')"
  },
  "status": "enum ('resolved', 'pending', 'rejected')"
}
```

**Example Query (List unresolved violations in the last 7 days):**
```sql
SELECT *
FROM governance_events
WHERE timestamp > NOW() - INTERVAL '7 days'
  AND status = 'pending'
ORDER BY timestamp DESC;
```

---

### **3. Role-Policy Binding Schema**
Links user roles to governance policies.

```json
{
  "roleId": "string (reference)",
  "policyId": "string (reference)",
  "effectiveFrom": "datetime",
  "effectiveTo": "datetime (nullable)",
  "justification": "string (optional)"
}
```

**Example Query (Find all policies assigned to the 'auditor' role):**
```sql
SELECT p.*
FROM policies p
JOIN role_policy_bindings rpb ON p.id = rpb.policyId
WHERE rpb.roleId = 'auditor-role-uuid';
```

---

## **Implementation Details**

### **1. Step-by-Step Setup**
#### **A. Define Policies**
- Use a **policy-as-code** approach (e.g., **Open Policy Agent (OPA)** rules).
- Store rules in a database or **GitOps**-managed YAML files.

**Example OPA Policy (JSON):**
```json
{
  "allow_access": {
    "if": "request.user.role == 'manager' || request.user.department == 'finance'",
    "then": {
      "access": "granted"
    },
    "else": {
      "access": "denied"
    }
  }
}
```

#### **B. Integrate with Application Workflows**
- **API Layer:** Add governance checks in middleware (e.g., **Kong**, **Apigee**).
- **Database Layer:** Use triggers or stored procedures to validate operations.
- **Event Layer:** Forward governance events to a **SIEM** (e.g., **Splunk**, **ELK**).

**Example (PostgreSQL Trigger for Audit Logging):**
```sql
CREATE OR REPLACE FUNCTION log_access()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND NEW.role != OLD.role {
    INSERT INTO governance_events (userId, action, details)
    VALUES (NEW.userId, 'ROLE_CHANGE', '{"oldRole": OLD.role, "newRole": NEW.role}');
  }
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_access
AFTER UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION log_access();
```

#### **C. Automate Remediation**
- Use **serverless functions** (e.g., **AWS Lambda**, **Azure Functions**) to:
  - Revoke access if a policy is violated.
  - Escalate to a **ticketing system** (e.g., **ServiceNow**).
  - Notify stakeholders via **Slack/SMS**.

**Example Lambda (Deny Access on Policy Violation):**
```python
import boto3

def lambda_handler(event, context):
    policy_id = event['policyId']
    user_id = event['userId']

    # Check if policy is violated
    violated = check_policy_violation(policy_id)

    if violated:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('user_access')

        # Revoke access
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET access = :val',
            ExpressionAttributeValues={':val': 'denied'}
        )
        return {'status': 'actioned'}
```

---

### **2. Querying Governance Data**
#### **A. Find Compliance Gaps**
```sql
-- Policies with no assigned roles (orphaned policies)
SELECT p.name, p.id
FROM policies p
LEFT JOIN role_policy_bindings rpb ON p.id = rpb.policyId
WHERE rpb.roleId IS NULL;
```

#### **B. Track Policy Enforcement**
```sql
-- Events where access was denied due to governance
SELECT *
FROM governance_events
WHERE action = 'ACCESS_DENIED'
ORDER BY timestamp DESC
LIMIT 50;
```

#### **C. Verify SOX Controls**
```sql
-- Segregation of duties (SoD) violations
SELECT u1.username, u2.username
FROM users u1, users u2
JOIN role_policy_bindings rpb1 ON u1.id = rpb1.roleId
JOIN role_policy_bindings rpb2 ON u2.id = rpb2.roleId
WHERE rpb1.policyId = 'sox-segregation-policy'
  AND rpb2.policyId = 'sox-segregation-policy'
  AND u1.username != u2.username;
```

---

## **Best Practices**
1. **Centralized Governance Store**
   - Use a dedicated database (e.g., **MongoDB**, **PostgreSQL**) or **GraphQL** schema for policies.
   - Avoid hardcoding rules in application logic.

2. **Real-Time Monitoring**
   - Stream governance events to a **SIEM** or **data lake** (e.g., **AWS Kinesis**, **Confluent**).

3. **Automated Remediation**
   - Define **pre-built remediation rules** (e.g., "If policy X is violated, revoke role Y").

4. **Auditability**
   - Log all governance actions with **immutable timestamps** (e.g., **blockchain-based ledgers**).

5. **Role-Based Access Control (RBAC) Integration**
   - Sync with **Okta**, **Azure AD**, or **FreeIPA** for dynamic policy enforcement.

---

## **Query Examples**

### **1. Check User Access Rights**
```sql
-- Does user 'john.doe' have access to 'finance_data'?
SELECT *
FROM user_roles ur
JOIN policies p ON ur.roleId = p.roleId
WHERE ur.userId = 'john-doe-uuid'
  AND p.resource = 'finance_data'
  AND p.rule.condition = 'true';
```

### **2. Detect Unapproved Access Requests**
```sql
-- Find requests pending approval > 24 hours
SELECT r.*
FROM access_requests r
WHERE r.status = 'pending'
  AND r.createdAt < NOW() - INTERVAL '24 hours';
```

### **3. Generate SOX Audit Report**
```sql
-- List all financial transactions requiring manual review
SELECT transaction_id, amount, timestamp
FROM transactions
WHERE department = 'finance'
  AND approval_status = 'pending';
```

### **4. Monitor Data Exposure Risks**
```sql
-- Find tables with PII exposed to non-compliant users
SELECT t.table_name, u.username
FROM tables t
JOIN table_permissions tp ON t.id = tp.tableId
JOIN users u ON tp.userId = u.id
WHERE t.sensitivity = 'high'
  AND u.compliance_status = 'non_compliant';
```

---

## **Tools & Integrations**
| **Category**          | **Tools**                                                                 |
|-----------------------|--------------------------------------------------------------------------|
| **Policy Engine**     | Open Policy Agent (OPA), AWS IAM, Azure Policy                          |
| **Event Streaming**   | Apache Kafka, AWS Kinesis, RabbitMQ                                     |
| **SIEM/Audit**        | Splunk, ELK Stack, IBM QRadar, Datadog                                  |
| **Database Hooks**    | PostgreSQL Triggers, SQL Server CLR, MySQL Events                        |
| **RBAC**              | Okta, Azure AD, FreeIPA, Auth0                                          |
| **Remediation**       | AWS Lambda, Azure Functions, ServiceNow, Jira                            |
| **Governance DB**     | MongoDB, PostgreSQL, DynamoDB, Apache Cassandra                         |

---

## **Related Patterns**
| **Pattern**               | **Relationship to Governance Integration**                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------|
| **[Observability]**       | Governance events feed into monitoring dashboards (e.g., **Prometheus**, **Grafana**).                   |
| **[Access Control]**      | Embeds governance policies into **RBAC/IAM** workflows.                                                     |
| **[Audit Logging]**       | Stores governance events in **immutable logs** for compliance.                                             |
| **[Event-Driven Architecture]** | Uses **Kafka/Event Sourcing** to propagate governance changes in real-time.                           |
| **[Policy as Code]**      | Defines governance rules in **Git**-managed YAML/JSON (e.g., **Terraform**, **Open Policy Agent**).   |
| **[Resilience]**          | Ensures governance checks don’t break under high load (e.g., **rate limiting**, **async processing**).  |

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                                                                 | **Solution**                                                                 |
|-------------------------------------|--------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Policies not enforced**          | Middleware bypassed or event stream failed.                                  | Check **API gateways** and **event logs**.                                  |
| **High latency in governance checks** | Complex policies or DB bottlenecks.                                       | Optimize queries; use **caching** (e.g., Redis).                          |
| **False positives in violations**  | Overly strict conditions in rules.                                         | Refine **policy conditions** with stakeholder feedback.                     |
| **Remediation failures**           | Integration issues with **ticketing systems** or **IAM**.                 | Test **end-to-end workflows** manually.                                     |
| **Audit logs incomplete**           | Event stream partitioning or DB triggers missed.                           | Validate **replication** and **trigger coverage**.                          |

---

## **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌───────────────┐
│             │    │             │    │             │    │               │
│  Application│───▶│  API Gateway│───▶│Policy Engine│───▶│Governance DB  │
│             │    │             │    │(OPA, AWS IAM)│    │(PostgreSQL)   │
└─────────────┘    └─────────────┘    └─────────────┘    └───────────────┘
                                             │
                                             ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                                                                           │
│                          Event Bus (Kafka)                               │
│                                                                           │
└──────────────┬───────────────────────────────────────────────────┬───────┘
               │                                               │
               ▼                                               ▼
┌─────────────┐               ┌─────────────┐                   ┌─────────────────┐
│             │               │             │                   │                 │
│   SIEM      │               │Remediation  │                   │   Audit Logs    │
│(Splunk)     │               │(Lambda/     │                   │(Immutable     │
│             │               │ServiceNow)  │                   │  Ledger)      │
└─────────────┘               └─────────────┘                   └─────────────────┘
```

---
**Final Notes:**
- Start with **non-critical policies** (e.g., logging) before enforcing strict controls.
- Document **policy intent** (e.g., "Why does this rule exist?").
- Use **chaos engineering** to test governance resilience.