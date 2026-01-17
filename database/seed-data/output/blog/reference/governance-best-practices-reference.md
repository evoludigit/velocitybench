# **[Pattern] Governance Best Practices – Reference Guide**

---

## **Overview**
This reference guide outlines **Governance Best Practices**, a structured framework for ensuring accountability, compliance, and consistency in software development, infrastructure, and organizational processes. Governance reduces risks, enforces standards, and aligns technology with business objectives.

Best practices include **policy enforcement, access control, auditability, and automated compliance checks**. This pattern applies to:
- **Infrastructure-as-Code (IaC) governance** (e.g., Terraform, CloudFormation)
- **Code governance** (e.g., CI/CD pipelines, PR review policies)
- **Data governance** (e.g., classification, access controls)
- **Security governance** (e.g., least privilege, vulnerability scanning)

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
| Principle               | Description                                                                                                                                                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Least Privilege**     | Grant only the minimum permissions required for a user/role to perform their tasks. Example: Limit admin access to critical resources only for approved teams.               |
| **Separation of Duties**| Divide responsibilities (e.g., code review vs. deployment, approvals) to prevent abuse or errors.                                                                                             |
| **Automation**          | Use tools (e.g., Policy as Code, CI/CD scans) to enforce governance rules automatically rather than manual checks.                                                                                     |
| **Auditability**        | Log all changes (e.g., IaC drift detection, API calls) and retain records for compliance (e.g., SOX, GDPR).                                                                                            |
| **Transparency**        | Document policies, decisions, and exceptions clearly for accountability.                                                                                                                               |
| **Continuous Monitoring** | Regularly assess compliance (e.g., weekly security scans, rotation of credentials) and remediate deviations.                                                                                          |

---

### **2. Governance Layers**
Governance applies across multiple layers of an organization’s tech stack:

| Layer               | Governance Focus                                                                 | Example Tools/Rules                                                                 |
|---------------------|-----------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| **Policy**          | Define "what" is allowed/required.                                                 | - IaC templates with mandatory tags (e.g., `CostCenter=Finance`).                     |
|                       |                                                                                   | - Code repositories with required files (e.g., `LICENSE`, `CONTRIBUTING.md`).       |
| **Enforcement**     | Automate compliance checks.                                                        | - **IaC:** Terraform policies, AWS Config rules.                                     |
|                       |                                                                                   | - **Code:** GitHub Actions to block PRs without security checks.                    |
| **Audit**           | Track compliance and detect violations.                                           | - CloudTrail logs for AWS resource changes.                                         |
|                       |                                                                                   | - Jira tickets for approved exceptions.                                             |
| **Remediation**     | Fix violations or raise exceptions.                                                | - Auto-rollback for non-compliant deployments.                                      |
|                       |                                                                                   | - Slack alerts for policy violations.                                               |

---

### **3. Governance Models**
Choose a model based on organizational needs:

| Model               | Description                                                                                                                                 | Use Case                                                                             |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Centralized**     | Single governance team enforces policies across all teams.                                                                                     | Large enterprises with uniform compliance needs (e.g., banking, healthcare).        |
| **Decentralized**   | Teams define and enforce their own policies (with oversight).                                                                               | Startups or agile organizations where flexibility is critical.                       |
| **Hybrid**          | Central policies for critical areas (e.g., security, data) + team-specific rules for others.                                                 | Mid-sized companies balancing standardization and autonomy.                           |
| **Autonomous**      | Teams self-govern with minimal oversight (e.g., feature flags for canary deployments).                                                     | High-trust cultures or mature engineering teams.                                      |

---

## **Schema Reference**
Use this schema to define governance policies in a structured format.

| Field               | Type      | Description                                                                                                                                                                                                 | Example                                                                                     |
|---------------------|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `policy_id`         | String    | Unique identifier for the policy.                                                                                                                                                                  | `gov-policy-001`                                                                              |
| `name`              | String    | Human-readable name of the policy.                                                                                                                                                              | "Enforce Multi-Factor Authentication"                                                         |
| `scope`             | Enum      | Applies to: `code`, `infra`, `data`, `security`, `all`.                                                                                                                                          | `security`                                                                                   |
| `owner`             | String    | Team or role responsible for enforcement.                                                                                                                                                          | `security-team@company.com`                                                              |
| `rules`             | Array     | List of conditions to enforce.                                                                                                                                                                   | `{ "require_mfa": true }`                                                                   |
| `enforcement`       | Object    | How the policy is enforced.                                                                                                                                                                    | `{ "tool": "aws_iam", "action": "block_access" }`                                           |
| `audit`             | Object    | Logging and monitoring requirements.                                                                                                                                                             | `{ "log_to": "s3://compliance-logs", "frequency": "daily" }`                               |
| `exceptions`        | Array     | Allowed exceptions (e.g., projects, users).                                                                                                                                                     | `[ { "team": "marketing", "reason": "legacy_system" } ]`                                  |
| `severity`          | Enum      | `low`, `medium`, `high`, `critical`.                                                                                                                                                          | `high`                                                                                       |
| `status`            | Enum      | `draft`, `active`, `deprecated`.                                                                                                                                                                | `active`                                                                                     |
| `documentation`     | String    | Link to policy details or rationale.                                                                                                                                                             | "/docs/governance/policies/mfa-policy.md"                                                 |

---

## **Query Examples**
Use these queries to check compliance or retrieve governance data.

### **1. List All Active Policies**
```sql
-- SQL (e.g., PostgreSQL)
SELECT * FROM governance_policies
WHERE status = 'active';
```

```graphql
# GraphQL (if using a governance API)
query GetActivePolicies {
  governance_policies(filter: { status: { eq: "active" } }) {
    policy_id
    name
    owner
    rules
  }
}
```

### **2. Check Compliance for a Specific Resource**
```python
# Python (using boto3 for AWS)
import boto3

client = boto3.client('config')
response = client.describe_compliance_by_resource(
    ResourceType='AWS::EC2::Instance',
    ResourceIds=['i-1234567890abcdef0']
)
print(response['ComplianceResourceTypes']['compliance']['status'])
```

### **3. Find Exceptions for a Policy**
```bash
# CLI (e.g., grep through governance YAML files)
grep -r "policy_id: gov-policy-001" /path/to/policies/ | grep "exceptions"
```

### **4. Generate a Compliance Report**
```bash
# Shell script to aggregate compliance logs
#!/bin/bash
aws logs filter-log-events --log-group-name "/aws/lambda/governance-scanner" \
  --query "events[].message" | grep "NON_COMPLIANT" > compliance_report.txt
```

---

## **Implementation Steps**
Follow this workflow to implement governance best practices:

1. **Define Policies**
   - Use the schema above to document rules (e.g., in Markdown, YAML, or a governance database).
   - Example YAML policy:
     ```yaml
     policy_id: gov-policy-002
     name: Tag All Resources
     scope: infra
     rules:
       - required_tags: ["Environment", "Owner"]
     enforcement:
       tool: terraform
       action: error
     ```

2. **Integrate with Tools**
   - **IaC:** Add policy checks to Terraform (`terraform validate --check-variables`) or CloudFormation.
   - **Code:** Use Git hooks or CI (e.g., GitHub Actions) to block PRs without compliance checks.
   - **Cloud:** Use managed services like AWS Config, GCP Security Command Center, or Azure Policy.

3. **Automate Enforcement**
   - Schedule scans (e.g., daily AWS Config evaluations).
   - Set up alerts for violations (e.g., Slack notifications for high-severity issues).

4. **Monitor and Remediate**
   - Use dashboards (e.g., Grafana, Datadog) to track compliance trends.
   - Assign owners to fix violations (e.g., Jira tickets for non-compliant resources).

5. **Document Exceptions**
   - Approve exceptions via a formal process (e.g., Jira tickets with approvals).
   - Example exception record:
     ```json
     {
       "policy_id": "gov-policy-001",
       "exception_id": "exc-2023-045",
       "resource": "database:legacy-sales-db",
       "reason": "Legacy system incompatible with encryption requirements",
       "approved_by": "db-admin@company.com",
       "expiry_date": "2025-01-01"
     }
     ```

---

## **Query Examples by Layer**
### **Infra Governance**
**Check for untagged EC2 instances:**
```bash
aws ec2 describe-instances \
  --query "Reservations[*].Instances[?Tags == null].InstanceId" \
  --output text
```

**Apply Terraform policy to block public S3 buckets:**
```hcl
# main.t4f
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }

  # Enforce deny_public_access = true via Terraform policy
  lifecycle {
    prevent_destroy = true
  }
}
```

### **Code Governance**
**Block PRs without security checks (GitHub Actions):**
```yaml
# .github/workflows/security-checks.yml
name: Security Review
on: [pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high
```

**Require license headers in code:**
```bash
# CLI tool: license-checker
license-checker --required-licenses apache-2.0
```

### **Data Governance**
**Classify sensitive data (e.g., PII) in S3:**
```python
# AWS Lambda (using Amazon Macie)
import boto3

client = boto3.client('macie2')
response = client.list_findings(
    FindingCriteria={
        'TimeRange': {
            'StartTime': '2023-01-01T00:00:00Z',
            'EndTime': '2023-12-31T23:59:59Z'
        },
        'Classification': 'PERSONALLY_IDENTIFIABLE_INFORMATION'
    }
)
```

---

## **Related Patterns**
Governance Best Practices often intersects with these patterns:

| Related Pattern               | Description                                                                                                                                                                                                 | How They Interact                                                                                     |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **[Security Hardening](link)** | Strengthens systems against threats.                                                                                                                                                               | Governance enforces security policies (e.g., patching, encryption), while hardening implements technical controls. |
| **[Observability](link)**     | Monitors systems for performance and anomalies.                                                                                                                                                       | Governance requires observability data to be retained and accessible for audits.                        |
| **[Infrastructure as Code](link)** | Manages infrastructure via code.                                                                                                                                                                    | Governance policies are often enforced via IaC tools (e.g., Terraform policies).                     |
| **[Zero Trust](link)**        | Assumes no user/service is trusted by default.                                                                                                                                                     | Governance enforces least-privilege access and micro-segmentation as part of Zero Trust.               |
| **[Chaos Engineering](link)** | Tests system resilience by introducing failures.                                                                                                                                                     | Governance requires chaos experiments to follow approval processes and log results for auditing.      |
| **[Policy as Code](link)**    | Defines policies in code (e.g., OPA, Kyverno).                                                                                                                                                      | Governance leverages Policy as Code to automate compliance checks.                                   |

---

## **Troubleshooting**
| Issue                          | Cause                                                                                     | Solution                                                                                                                                                                                                 |
|---------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Policy violations ignored**   | No enforcement mechanism or exceptions not logged.                                         | Audit enforcement tools (e.g., Terraform plan logs) and reconcile with exception records.                                                               |
| **Overly restrictive policies** | Policies block legitimate use cases.                                                     | Review exceptions and adjust policies with input from affected teams.                                                                                                                    |
| **Compliance data missing**     | Logs not retained or tools misconfigured.                                                 | Configure retention policies (e.g., AWS S3 lifecycle rules) and validate logs via sampling.                                                                  |
| **Slow enforcement**            | Batch checks or high-volume scans.                                                          | Optimize scan frequency (e.g., incremental scans) or parallelize checks.                                                                                                                 |
| **Policy drift**                | Manual changes bypass automation.                                                          | Use tools like Drift Detection (e.g., AWS Config) or Git hooks to alert on unauthorized changes.                                                          |

---

## **Examples by Cloud Provider**
| Provider  | Governance Tools                                                                                     |
|-----------|-----------------------------------------------------------------------------------------------------|
| **AWS**   | - AWS Config Rules                                                                                 |
|           | - AWS IAM Access Analyzer                                                                          |
|           | - Control Tower for multi-account governance                                                     |
|           | - Service Catalog for pre-approved resources                                                      |
| **GCP**   | - Security Command Center                                                                         |
|           | - Binary Authorization                                                                             |
|           | - Organization Policies                                                                           |
| **Azure** | - Azure Policy                                                                                     |
|           | - Azure RBAC with Blueprints                                                                       |
|           | - Azure Defender for Cloud                                                                         |
| **Kubernetes** | - Kyverno for cluster policies                                                                     |
|           | - OPA/Gatekeeper for Policy as Code                                                                |
|           | - Cluster Admission Controllers                                                                   |

---

## **Further Reading**
- **[OASIS Open Policy Agent (OPA)](https://www.openpolicyagent.org/)** – Policy as Code framework.
- **[Cloud Native Computing Foundation (CNCF) Policies](https://www.cncf.io/)** – Industry standards for cloud governance.
- **[NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)** – Governance model for cybersecurity.
- **[Terraform Policy Documentation](https://developer.hashicorp.com/terraform/language/policies)** – Implementing Terraform policies.