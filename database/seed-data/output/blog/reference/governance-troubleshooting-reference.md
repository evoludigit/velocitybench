# **[Pattern] Reference Guide: Governance Troubleshooting**

## **Overview**
Governance Troubleshooting is a structured approach to diagnosing and resolving issues in governance frameworks, policies, and operational controls within an organization. This pattern ensures compliance, mitigates risks, and maintains consistency across governance systems (e.g., cloud, data, access, or regulatory). It combines **root-cause analysis**, **audit trails**, **remediation scripts**, and **policy enforcement checks** to identify and fix misconfigurations, unauthorized changes, or policy violations. Key areas addressed include:
- **Policy compliance** (e.g., IAM misconfigurations, missing tags)
- **Audit failures** (e.g., log retention issues, insufficient monitoring)
- **Permission conflicts** (e.g., over-permissive roles, orphaned resources)
- **Resource drift** (e.g., unintended state changes in infrastructure)

This guide provides a structured methodology for troubleshooting governance-related issues, including schema definitions, query patterns, and remediation strategies.

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Policy Rule**           | Defines compliance requirements (e.g., "All S3 buckets must enable versioning"). Violations trigger alerts or remediation.                                                                                   |
| **Audit Trail**           | Logs governance events (e.g., API calls, policy changes) for forensic analysis.                                                                                                                               |
| **Remediation Playbook**  | Predefined steps to fix violations (e.g., automatically apply missing tags or revoke excess permissions).                                                                                                     |
| **Governance Scope**      | Defines the boundaries for checks (e.g., "AWS Account X," "All VPC resources").                                                                                                                               |
| **Compliance State**      | Tracks whether a resource/policy is "Compliant," "Non-Compliant," or "Pending Review."                                                                                                                     |
| **Trigger Conditions**    | Events that initiate troubleshooting (e.g., policy scan failure, manual alert).                                                                                                                               |

---
### **Schema Reference**
Below are core schema objects used in governance troubleshooting.

| **Schema**                | **Fields**                                                                                     | **Data Type**       | **Description**                                                                                                      |
|---------------------------|-------------------------------------------------------------------------------------------------|---------------------|----------------------------------------------------------------------------------------------------------------------|
| **PolicyDefinition**      | `id` (string), `name` (string), `ruleType` (enum: `tag`, `permission`, `encryption`), `status` (enum: `active`, `disabled`) | JSON              | Defines a governance rule (e.g., enforce "sensitive-data" tag on all databases).                                     |
| **ResourceInventory**     | `resourceId` (string), `type` (enum: `bucket`, `vm`, `role`), `location` (string), `tags` (map) | JSON              | Catalogs resources with attributes for policy evaluation.                                                           |
| **AuditLog**              | `logId` (string), `timestamp` (datetime), `action` (string), `resourceId` (string), `status` (enum: `success`, `failure`) | JSON              | Records governance-related actions (e.g., "Tag added to bucket `s3://data-lake`").                                   |
| **Violation**             | `violationId` (string), `policyId` (ref: `PolicyDefinition`), `resourceId` (ref: `ResourceInventory`), `severity` (enum: `low`, `high`), `remediationSteps` (list) | JSON              | Documents policy violations with actionable fixes.                                                                   |
| **RemediationScript**     | `scriptId` (string), `policyId` (ref: `PolicyDefinition`), `command` (string), `status` (enum: `pending`, `executed`, `failed`) | JSON              | Stores automated fix scripts (e.g., AWS CLI commands to apply tags).                                                  |
| **GovernanceScope**       | `scopeId` (string), `accountId` (string), `region` (string), `resourceTags` (map)              | JSON              | Defines the target environment for governance checks (e.g., "us-east-1, tag: `environment=prod`").                  |

---

## **Query Examples**
Use these queries to diagnose and resolve governance issues in databases or configuration management tools (e.g., AWS Config, Terraform State, or a custom governance DB).

---

### **1. List All Non-Compliant Resources**
**Purpose**: Identify resources violating active policies.
**Query**:
```sql
SELECT
    r.resourceId,
    r.type,
    p.name AS policy_name,
    v.severity,
    v.remediationSteps
FROM ResourceInventory r
JOIN Violation v ON r.resourceId = v.resourceId
JOIN PolicyDefinition p ON v.policyId = p.id
WHERE p.status = 'active' AND v.status = 'open'
ORDER BY v.severity DESC;
```
**Output**:
| `resourceId`       | `type` | `policy_name`          | `severity` | `remediationSteps`                     |
|--------------------|--------|------------------------|------------|----------------------------------------|
| `s3://logs-bucket`  | bucket | EnableBucketLogRetention | high       | `aws s3api put-bucket-logs --bucket logs-bucket --logging-configuration '{"LoggingEnabled": {"TargetBucket": "audit-logs"}}'` |

---

### **2. Find Orphaned IAM Roles**
**Purpose**: Detect roles with no attached policies or permissions.
**Query**:
```sql
SELECT
    r.roleName,
    COUNT(DISTINCT p.policyArn) AS attached_policies
FROM IAM_Roles r
LEFT JOIN IAM_Policies p ON r.roleName = p.roleName
WHERE COUNT(DISTINCT p.policyArn) = 0
AND r.status != 'disabled';
```
**Output**:
| `roleName`               | `attached_policies` |
|--------------------------|---------------------|
| `legacy-data-sync-role`  | 0                   |

---
### **3. Check Audit Log Retention Compliance**
**Purpose**: Verify if audit logs exceed the allowed retention period.
**Query**:
```sql
SELECT
    a.resourceId,
    a.action,
    DATEDIFF(CURRENT_DATE, a.timestamp) AS days_old
FROM AuditLog a
WHERE a.resourceId LIKE '%s3%'  -- Example: Focus on S3 buckets
  AND DATEDIFF(CURRENT_DATE, a.timestamp) > 30  -- Retention threshold
  AND a.status = 'success';
```
**Output**:
| `resourceId`       | `action`                     | `days_old` |
|--------------------|------------------------------|------------|
| `s3://data-lake`    | ObjectPut                   | 45         |

---
### **4. Generate Remediation Scripts for Missing Tags**
**Purpose**: Auto-generate tagging scripts for resources lacking critical tags.
**Query**:
```sql
SELECT
    CONCAT('aws ec2 create-tags --resources ', r.instanceId,
           ' --tags Key=environment,Value=production') AS remediation_script,
    r.instanceId,
    r.type
FROM ResourceInventory r
WHERE r.type = 'ec2'
  AND NOT EXISTS (
      SELECT 1 FROM r.tags WHERE key = 'environment'
  );
```
**Output**:
| `remediation_script`                                                                                     | `instanceId` | `type` |
|---------------------------------------------------------------------------------------------------------|--------------|--------|
| `aws ec2 create-tags --resources i-123456 --tags Key=environment,Value=production`                   | i-123456     | ec2    |

---
### **5. Filter Violations by Severity and Scope**
**Purpose**: Prioritize high-severity violations in a specific account/region.
**Query**:
```sql
SELECT
    v.violationId,
    p.name,
    r.resourceId,
    g.scopeId
FROM Violation v
JOIN PolicyDefinition p ON v.policyId = p.id
JOIN ResourceInventory r ON v.resourceId = r.resourceId
JOIN GovernanceScope g ON r.accountId = g.accountId AND r.region = g.region
WHERE g.scopeId = 'prod-east1'
  AND v.severity = 'high';
```

---
## **Remediation Strategies**
Use these patterns to address common governance issues:

| **Issue**                     | **Remediation Steps**                                                                                                                                        |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Missing Tags**              | Apply tags via script (e.g., Terraform, AWS CLI) or enforce tags through IAM policies.                                                                  |
| **Over-Permissive Roles**     | Audit role policies with `aws iam list-policies` and revoke excess permissions. Use least-privilege principles.                                             |
| **Unencrypted S3 Buckets**    | Run `aws s3api put-bucket-encryption` on all unencrypted buckets.                                                                                      |
| **Unmonitored Resources**     | Tag resources with `Monitoring=Enabled` and set up CloudWatch alarms for critical metrics.                                                               |
| **Drift from Policy**         | Use configuration-as-code (e.g., Terraform) to reconcile resources with defined standards.                                                               |

---

## **Related Patterns**
Governance Troubleshooting integrates with these complementary patterns:
1. **[Policy-as-Code]** – Enforce governance rules via infrastructure-as-code (e.g., Open Policy Agent, AWS Organizations SCPs).
2. **[Audit Logging]** – Centralize logs for governance events (e.g., AWS CloudTrail, Datadog).
3. **[Least Privilege Access]** – Continuously audit and adjust permissions to reduce attack surfaces.
4. **[Change Management]** – Track and approve governance-related changes (e.g., via GitOps or CI/CD pipelines).
5. **[Resource Tagging]** – Standardize tagging for cost tracking, access control, and compliance.
6. **[Automated Compliance Scans]** – Schedule regular policy scans (e.g., AWS Config Rules, Prisma Cloud).

---
## **Tools and Integrations**
| **Tool**               | **Use Case**                                                                                     |
|------------------------|-------------------------------------------------------------------------------------------------|
| **AWS Config**         | Continuously assess resources against governance rules.                                            |
| **Terraform**          | Enforce compliance via `terraform validate` and `terraform plan`.                                |
| **Open Policy Agent (OPA)** | Evaluate custom policies against resources at runtime.                                           |
| **Splunk/Graylog**     | Correlate governance logs with other operational data.                                           |
| **ServiceNow**         | Route governance violations as IT service requests.                                               |

---
## **Best Practices**
1. **Automate Remediation**: Use tools like **AWS Systems Manager** or **Ansible** to apply fixes without manual intervention.
2. **Define SLAs for Fixes**: Classify violations by severity and assign ownership (e.g., DevOps for IAM, Security for encryption).
3. **Document As-Built State**: Maintain an inventory of resources and their compliance status for audits.
4. **Test Fixes in Staging**: Validate remediation scripts in a non-production environment before applying to production.
5. **Monitor Post-Fix**: Re-run scans to confirm violations are resolved (e.g., using AWS Config rule compliance metrics).