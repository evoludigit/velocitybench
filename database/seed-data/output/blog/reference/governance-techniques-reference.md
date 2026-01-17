# **[Pattern] Governance Techniques Reference Guide**

---

## **Overview**
The **Governance Techniques** pattern provides structured methods to enforce policy compliance, track decision-making processes, and ensure consistency across systems, teams, or organizations. Governance techniques help mitigate risks, streamline audits, and align operations with strategic objectives.

This guide covers key techniques like **Role-Based Access Control (RBAC), Audit Trails, Configuration Policies, and Anomaly Detection**, along with their implementations, best practices, and integration scenarios.

---

## **Schema Reference**

| **Technique**          | **Purpose**                                                                 | **Key Components**                                                                 | **Use Cases**                                                                 |
|-------------------------|-----------------------------------------------------------------------------|------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Role-Based Access Control (RBAC)** | Restricts permissions based on user roles.                                 | - Roles (e.g., `Admin`, `Developer`, `Guest`)<br>- Permission groups<br>- Least-privilege principle | IaaS/PaaS environments, enterprise applications, compliance enforcement.      |
| **Audit Trails**        | Logs user actions and system changes for traceability.                     | - Timestamps<br>- User identifiers<br>- Action type (e.g., `create`, `delete`)<br>- Metadata (IP, context) | Regulatory compliance, incident investigations, forensic analysis.          |
| **Configuration Policies** | Enforces system configurations to meet standards.                       | - Policy rules (e.g., "Disable SSH root login")<br>- Compliance checkers<br>- Remediation scripts | Cloud infrastructure, security hardening, DevOps pipelines.               |
| **Anomaly Detection**   | Identifies unusual behavior deviating from established patterns.          | - Baseline models (e.g., access patterns)<br>- Alert thresholds<br>- ML-based scoring | Fraud detection, security breaches, operational anomalies.                  |
| **Change Management**   | Standardizes workflows for system modifications.                          | - Request workflows<br>- Approval gates<br>- Rollback procedures                 | Enterprise IT, cloud migrations, critical updates.                          |
| **Data Governance**     | Ensures data accuracy, consistency, and compliance with regulations.      | - Metadata management<br>- Lineage tracking<br>- Access controls<br>- Right to erasure | Healthcare (HIPAA), finance (GDPR), enterprise data lakes.                 |

---

## **Implementation Details**

### **1. Role-Based Access Control (RBAC)**
**Concept:** Assigns permissions to user roles rather than individual users to simplify management.

#### **Key Features:**
- **Role Hierarchies:** Inheritance allows child roles to inherit parent permissions.
- **Temporary Role Elevation:** Short-term privilege escalation (e.g., for admin tasks).
- **Attribute-Based Access Control (ABAC):** Extends RBAC with dynamic attributes (e.g., time-based access).

#### **Implementation Steps:**
1. **Define Roles:**
   ```json
   {
     "roles": [
       {
         "name": "DatabaseAdmin",
         "permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"]
       },
       {
         "name": "ReadOnlyUser",
         "permissions": ["SELECT"]
       }
     ]
   }
   ```
2. **Assign Roles to Users:**
   ```sql
   GRANT 'ReadOnlyUser' TO 'user1'@'%';
   ```
3. **Enforce Least Privilege:**
   Regularly audit roles using tools like **AWS IAM Access Analyzer** or **Open Policy Agent (OPA)**.

#### **Tools:**
- **Cloud:** AWS IAM, Azure RBAC, GCP IAM.
- **Enterprise:** Okta, ForgeRock, IdentityServer.

---

### **2. Audit Trails**
**Concept:** Records all actions performed in a system for accountability.

#### **Key Features:**
- **Immutable Logs:** Prevent tampering (e.g., using blockchain or WORM storage).
- **Structured Logging:** JSON/XML format for easy querying.
- **Retention Policies:** Automated log purging to comply with regulations.

#### **Implementation:**
1. **Enable Logging:**
   ```bash
   # Example: AWS CloudTrail setup
   aws cloudtrail create-trail --name "AuditTrail" --enable-log-file-validation
   ```
2. **Querying Logs (CloudWatch Athena):**
   ```sql
   SELECT userIdentity, eventName, resourceType
   FROM cloudtrail_logs
   WHERE eventTime > '2023-10-01'
     AND eventName = 'DeleteBucket';
   ```
3. **Local Example (Python + Logging):**
   ```python
   import logging
   logging.basicConfig(filename='audit.log', level=logging.INFO)
   logging.info(f"User {user_id} executed: {action}")
   ```

#### **Tools:**
- **Cloud:** AWS CloudTrail, Azure Monitor, GCP Audit Logs.
- **Open Source:** ELK Stack (Elasticsearch, Logstash, Kibana), Splunk.

---

### **3. Configuration Policies**
**Concept:** Enforces system configurations to meet security/compliance standards.

#### **Key Features:**
- **Policy-as-Code:** Define rules in YAML/JSON (e.g., **Open Policy Agent**.
- **Remediation:** Automated fixes for non-compliant resources.
- **Compliance Reporting:** Dashboards for gap analysis.

#### **Implementation (AWS Config):**
1. **Create a Policy:**
   ```json
   {
     "ComplianceResourceType": "AWS::EC2::Instance",
     "ComplianceResourceId": "${aws_instance.id}",
     "Annotation": "Disable unnecessary ports",
     "ComplianceResourceOrder": 1,
     "ExpectedValue": "Closed",
     "ActualValue": "${var.ssh_port_status}",
     "Status": "NOT_COMPLIANT",
     "ComplianceType": "CUSTOM_RULE",
     "Ordering": 1
   }
   ```
2. **Apply Policy:**
   ```bash
   aws configrule create --name "require-sshd-disabled" --input-policy '{"Statement": [...]}'
   ```
3. **Remediate Non-Compliant Instances:**
   ```bash
   aws config resource-compliance --resource-id i-1234567890abcdef0
   ```

#### **Tools:**
- **Cloud:** AWS Config, Azure Policy, GCP Security Command Center.
- **Open Source:** Terraform with `terraform validate`, Chef InSpec.

---

### **4. Anomaly Detection**
**Concept:** Uses ML to detect deviations from normal behavior.

#### **Implementation (AWS GuardDuty):**
1. **Enable GuardDuty:**
   ```bash
   aws guardduty create-detector --detector-name "AnomalyDetector"
   ```
2. **Configure Findings:**
   ```bash
   aws guardduty update-members --detector-id "d-1234567890" --members "123456789012"
   ```
3. **Query Alerts (Athena):**
   ```sql
   SELECT * FROM guardduty_findings
   WHERE type = 'UnauthorizedAccess:EC2'
     AND severity = 'HIGH';
   ```

#### **Open Source Alternative (Elastic SIEM):**
```groovy
// Kibana Anomaly Detection Rules (JSON)
{
  "name": "High-Volume API Calls",
  "rule_type": "statistical",
  "threshold": "95th_percentile",
  "field": "api_calls_count",
  "period": "30m"
}
```

#### **Tools:**
- **Cloud:** AWS GuardDuty, Azure Sentinel, GCP Chronicle.
- **Open Source:** Graylog, Wazuh, OSSEC.

---

### **5. Change Management**
**Concept:** Standardizes workflows for system modifications to minimize risks.

#### **Implementation (GitHub + LinearB):**
1. **Define Workflow in YAML (GitHub Actions):**
   ```yaml
   name: Production Deployment
   on:
     workflow_dispatch:
       inputs:
         approval:
           description: 'Requires team lead approval'
           required: true
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - run: ./deploy.sh --env production
   ```
2. **Integrate with Change Review Tools:**
   - **LinearB:** Pre-approval gates for critical changes.
   - **Jira:** Change ticketing for tracking.

#### **Tools:**
- **DevOps:** GitHub Actions, GitLab CI/CD, Jenkins.
- **Enterprise:** ServiceNow, BMC Helix, Cherwell.

---

### **6. Data Governance**
**Concept:** Manages data quality, lineage, and compliance (e.g., GDPR, HIPAA).

#### **Implementation (Collibra + DataStax):**
1. **Tag Sensitive Data:**
   ```python
   # Pseudocode: Mark PII in a database
   db.execute("ALTER TABLE users ADD COLUMN is_pii BOOLEAN")
   ```
2. **Track Lineage (Collibra):**
   - Visualize data flow from source to consumption.
   - Example: A `patient_record` table updates `billing_system`.

3. **Enforce Access Controls:**
   ```sql
   -- Example: PostgreSQL row-level security
   CREATE POLICY patient_access_policy ON patient_records
     USING (user_id = current_setting('app.current_user_id')::int);
   ```

#### **Tools:**
- **Data Catalogs:** Collibra, Alation, Apache Atlas.
- **GDPR Tools:** OneTrust, TrustArc.

---

## **Query Examples**

### **1. RBAC Query (AWS IAM)**
```sql
-- Find users with 'Admin' permissions (Athena)
SELECT user_name, attached_policy_arn
FROM iam_policies_attached_to_users
WHERE attached_policy_arn LIKE '%AmazonAdministratorAccess%';
```

### **2. Audit Trail Query (CloudTrail)**
```sql
-- Find all S3 bucket deletions in the last 7 days
SELECT eventTime, userIdentity, eventName, resourceType, resourceName
FROM cloudtrail_logs
WHERE eventTime > TIMESTAMPADD(day, -7, CURRENT_TIMESTAMP)
  AND eventName = 'DeleteBucket';
```

### **3. Policy Compliance Check (AWS Config)**
```sql
-- List non-compliant EC2 instances (Athena)
SELECT resource_id, compliance_resource_id, compliance_resource_status
FROM config_resource_compliance
WHERE compliance_resource_status = 'non_compliant'
  AND compliance_resource_type = 'AWS::EC2::Instance';
```

### **4. Anomaly Detection Alerts (GuardDuty)**
```sql
-- List high-severity EC2 unauthorized access attempts
SELECT * FROM guardduty_findings
WHERE type = 'UnauthorizedAccess:EC2'
  AND severity = 'HIGH'
  AND service = 'AWSGuardDuty';
```

### **5. Change Request Status (Jira API)**
```http
GET /rest/api/2/search?jql=project=DEV&fields=status,summary,key
Headers: Authorization: Bearer {token}
Response:
[
  {
    "id": "10001",
    "fields": {
      "status": { "name": "In Progress" },
      "summary": "Deploy v2.0 to staging"
    }
  }
]
```

---

## **Best Practices**
1. **RBAC:**
   - Rotate credentials regularly.
   - Use **Just-In-Time (JIT) access** for sensitive operations.

2. **Audit Trails:**
   - Enable **centralized logging** (e.g., CloudWatch, ELK).
   - Retain logs for **7–10 years** (regulatory compliance).

3. **Configuration Policies:**
   - Start with **low-severity policies** and gradually enforce stricter rules.
   - Automate **remediation** where possible.

4. **Anomaly Detection:**
   - ** continuo**ously update baselines (e.g., monthly).
   - Reduce **false positives** with tuning rules.

5. **Change Management:**
   - Enforce **pre-production testing** for critical changes.
   - Document **rollback procedures**.

6. **Data Governance:**
   - **Automate PII detection** (e.g., regex, ML models).
   - Train teams on **data handling policies**.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Security Hardening]**   | Strengthens systems against attacks by applying patches and reducing attack surfaces. | Cloud deployments, on-premises servers.        |
| **[Compliance Automation]** | Uses tools to enforce regulatory requirements (e.g., ISO 27001, SOC 2).        | Enterprises with strict compliance demands.     |
| **[Observability]**        | Centralizes logging, metrics, and tracing for system health monitoring.       | Large-scale distributed systems.                |
| **[Infrastructure as Code (IaC)]** | Manages infrastructure via code (e.g., Terraform, CloudFormation).          | DevOps pipelines, repeatable deployments.       |
| **[Zero Trust]**          | Assumes breach and verifies every access request dynamically.                  | High-security environments (finance, healthcare). |

---

## **References**
- **AWS:** [IAM Best Practices](https://aws.amazon.com/blogs/security/), [Config Rules](https://docs.aws.amazon.com/config/latest/userguide/config-references-by-language.html)
- **GCP:** [IAM Documentation](https://cloud.google.com/iam/docs), [Security Command Center](https://cloud.google.com/security-command-center)
- **Open Source:** [Open Policy Agent (OPA)](https://www.openpolicyagent.org/), [ELK Stack](https://www.elastic.co/elk-stack)
- **Standards:** [NIST SP 800-53](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final), [ISO 27001](https://www.iso.org/standard/27001.html)