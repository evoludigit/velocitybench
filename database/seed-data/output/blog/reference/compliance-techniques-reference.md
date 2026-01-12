# **[Design Pattern] Compliance Techniques – Reference Guide**

---

## **Overview**
The **Compliance Techniques** pattern provides structured, reusable strategies to ensure systems, applications, and workflows adhere to regulatory, organizational, or industry-specific requirements. This pattern focuses on **detecting, preventing, and documenting** compliance risks while minimizing operational overhead. It is critical for domains such as finance, healthcare, legal, and security-sensitive industries where adherence to laws (e.g., GDPR, HIPAA, SOX) or internal policies is non-negotiable.

Key benefits include:
- **Automated enforcement** of compliance rules via configurable techniques
- **Reduced manual audits** through system-driven validation
- **Traceability** of compliance events for reporting and remediation
- **Scalability** to accommodate evolving regulations

Techniques within this pattern cover **preventive controls, detective controls, and corrective actions**, integrating seamlessly with **code, infrastructure, and policy management systems**.

---

## **1. Key Concepts**
### **1.1 Compliance Technique Categories**
Compliance techniques are categorized by their primary function:

| **Category**          | **Description**                                                                                     | **Use Case Examples**                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| **Preventive**        | Proactively block non-compliant actions or configurations.                                            | - Data encryption at rest for GDPR<br>- Role-based access control (RBAC) for SOX<br>- Input validation for PCI DSS |
| **Detective**         | Identify violations or anomalies post-occurrence.                                                    | - Anomaly detection in user behavior (e.g., large data exports)<br>- Log-based auditing for HIPAA<br>- Regular compliance scans |
| **Corrective**        | Automate remediation of detected violations.                                                          | - Auto-rollback of misconfigured systems<br>- Alerting and ticket creation for manual fixes<br>- Data masking for breach responses |
| **Documentation**     | Maintain records of compliance efforts for audits.                                                   | - Timestamped compliance event logs<br>- Automated report generation (e.g., quarterly GDPR reports)      |
| **Hybrid**            | Combine preventive + detective + corrective in a unified workflow.                                     | - CI/CD pipeline checks for compliance before deployment<br>- Policy-as-code enforcement with remediation |

---

### **1.2 Core Components**
Each technique involves these foundational elements:

| **Component**         | **Description**                                                                                                                                       | **Example**                                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Rule Engine**       | Evaluates compliance rules against system state (e.g., policies, logs, configurations).                                                     | OpenPolicyAgent (OPA), Prometheus rules, or custom script-based validators.                                    |
| **Data Source**       | Provides inputs for rule evaluation (e.g., logs, databases, configurations).                                                                     | AWS CloudTrail, Kubernetes audit logs, or file system scans.                                                   |
| **Action Handler**    | Executes responses to rule violations (e.g., block, alert, remediate).                                                                             | API calls to block a user, Slack alerts, or Terraform scripts to fix misconfigurations.                         |
| **Metrics & Logging** | Tracks compliance performance (e.g., violations, resolution time).                                                                             | Prometheus metrics, ELK Stack for logs, or compliance dashboards in Grafana.                                  |
| **Policy Registry**   | Centralized storage of compliance rules (e.g., JSON, YAML, or custom DSL).                                                                       | Git repo for policy-as-code, HashiCorp Vault for secrets policies, or Azure Policy definitions.                |

---

## **2. Schema Reference**
### **2.1 Compliance Technique Schema**
Define a technique as a structured JSON object:

```json
{
  "name": "string (e.g., 'PCI_DSS_Encryption_Enforcement')",
  "category": ["preventive", "detective", "corrective", "documentation", "hybrid"],
  "description": "string (e.g., 'Ensure all credit card data is encrypted at rest')",
  "scope": {
    "targets": ["system", "application", "user", "data", "infrastructure"],
    "environments": ["prod", "staging", "dev"]
  },
  "rules": [
    {
      "id": "string (e.g., 'PCI_001')",
      "condition": "string (e.g., 'SELECT * FROM logs WHERE field="sensitive_data" AND NOT encrypted=true')",
      "severity": ["low", "medium", "high", "critical"],
      "threshold": "number (e.g., 'violations > 5')",
      "data_sources": ["string[] (e.g., ['cloudtrail_logs', 'database_audit'])"]
    }
  ],
  "actions": [
    {
      "type": "prevent", "detect", "correct", "notify",
      "handler": "string (e.g., 'block_user', 'send_slack_alert', 'run_terraform_script')",
      "parameters": "object (e.g., {'channel': '#compliance'})"
    }
  ],
  "metadata": {
    "owner": "string (e.g., 'security_team')",
    "last_updated": "ISO8601 timestamp",
    "references": ["string[] (e.g., ['GDPR Art. 32', 'SOX §404'])"]
  }
}
```

---
### **2.2 Example Schema (PCI_DSS_Encryption)**
```json
{
  "name": "PCI_DSS_Encryption_Enforcement",
  "category": ["preventive", "corrective"],
  "description": "Enforce TLS 1.2+ for all traffic handling credit card data.",
  "scope": {
    "targets": ["application", "infrastructure"],
    "environments": ["prod", "staging"]
  },
  "rules": [
    {
      "id": "PCI_TLS_12",
      "condition": "SELECT * FROM nginx_configs WHERE ssl_protocol != 'TLSv1.2'",
      "severity": "high",
      "threshold": null
    }
  ],
  "actions": [
    {
      "type": "prevent",
      "handler": "update_config",
      "parameters": {"config_path": "/etc/nginx/ssl.conf", "tls_version": "TLSv1.2"}
    },
    {
      "type": "notify",
      "handler": "send_email",
      "parameters": {"recipients": ["security@company.com"], "subject": "PCI TLS Violation"}
    }
  ],
  "metadata": {
    "owner": "security_team",
    "last_updated": "2023-10-15T00:00:00Z",
    "references": ["PCI DSS 4.0 Requirement 4"]
  }
}
```

---

## **3. Implementation Techniques**
### **3.1 Preventive Techniques**
| **Technique**               | **Implementation**                                                                                                                                                     | **Tools/Frameworks**                                                                                          |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Policy-as-Code**          | Define compliance rules in code (e.g., YAML, Terraform, Open Policy Agent). Enforce via CI/CD pipelines.                                                      | Terraform, OPA (Open Policy Agent), Kyverno (Kubernetes), AWS Config Rules                                 |
| **Input Validation**        | Validate user/input data against compliance requirements (e.g., mask PII, reject malformed requests).                                                          | Custom middleware (e.g., Express.js validators), AWS WAF, Cloudflare Bot Management                        |
| **Access Control**          | Enforce least-privilege access (e.g., RBAC, IAM policies).                                                                                                     | IAM (AWS), Role-Based Access Control (RBAC), HashiCorp Vault                                                 |
| **Infrastructure Guardrails** | Restrict configurations (e.g., block root SSH access, enforce encryption).                                                                                  | AWS Control Tower, Azure Policy, GCP Security Command Center                                                 |
| **Data Encryption**         | Enforce encryption at rest/transit (e.g., AES-256, TLS 1.3).                                                                                                 | AWS KMS, TLS certificates (Let’s Encrypt), PostgreSQL pgcrypto                                                  |

---
### **3.2 Detective Techniques**
| **Technique**               | **Implementation**                                                                                                                                                     | **Tools/Frameworks**                                                                                          |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Anomaly Detection**       | Flag unusual patterns (e.g., unexpected data exports, unusual login times).                                                                                     | Prometheus + Grafana, SIEM tools (Splunk, ELK Stack), AWS GuardDuty                                         |
| **Log Auditing**            | Continuously monitor logs for compliance violations (e.g., unauthorized data access).                                                                       | AWS CloudTrail, Datadog, Fluentd + ELK Stack, OpenTelemetry                                                 |
| **Static/Dynamic Analysis** | Scan code/infrastructure for vulnerabilities (e.g., hardcoded secrets, outdated libraries).                                                                      | SonarQube, Trivy, Snyk, Checkmarx                                                                             |
| **Compliance Scanning**     | Run automated compliance checks (e.g., CIS benchmarks, NIST guidelines).                                                                                       | CIS Benchmark Tools, AWS Config, OpenSCAP, Prisma Cloud                                                         |
| **Behavioral Analytics**    | Use ML to detect insider threats or policy violations.                                                                                                     | Darktrace, IBM QRadar, CrowdStrike Falcon                                                                     |

---
### **3.3 Corrective Techniques**
| **Technique**               | **Implementation**                                                                                                                                                     | **Tools/Frameworks**                                                                                          |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Automated Remediation**   | Fix violations via code (e.g., Terraform, Ansible) or API calls.                                                                                               | Terraform, Ansible, AWS Systems Manager, GitHub Actions                                                      |
| **Incident Response Playbooks** | Define workflows for handling violations (e.g., data breach protocol).                                                                                       | Jira, ServiceNow, incident response platforms (e.g., IBM Resilient)                                        |
| **Rollback Mechanisms**     | Revert to compliant state (e.g., rollback Kubernetes deployments).                                                                                        | Argo Rollouts, Kubernetes rollback API, GitLab CI/CD                                                           |
| **Data Masking/Anonymization** | Automatically redact sensitive data in logs/reports.                                                                                                       | AWS Data Masking, PostgreSQL `pgcrypto`, custom Python scripts (e.g., `censor` library)                     |
| **User Education Triggers** | Notify users of policy violations (e.g., password reset due to expiration).                                                                                    | Custom scripts (e.g., Python + SMTP), Auth0, Okta                                                                 |

---
### **3.4 Documentation Techniques**
| **Technique**               | **Implementation**                                                                                                                                                     | **Tools/Frameworks**                                                                                          |
|-----------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------|
| **Automated Reporting**     | Generate compliance reports (e.g., GDPR accountability records).                                                                                               | Custom scripts (e.g., Python + Pandas), Grafana + Prometheus, AWS QuickSight                              |
| **Audit Trails**            | Log all compliance-relevant actions (e.g., who changed what and when).                                                                                     | AWS CloudTrail, Kafka + ELK Stack, Vault audit logs                                                           |
| **Policy Documentation**    | Store rules in version-controlled docs (e.g., Confluence, Notion).                                                                                         | Confluence, Notion, GitHub Markdown (e.g., `POLICIES.md`)                                                   |
| **Compliance Dashboards**   | Visualize compliance status (e.g., % of rules passed).                                                                                                   | Grafana, Power BI, Tableau                                                                                   |
| **Evidence Vault**          | Store proof of compliance (e.g., screenshots, logs, certificates).                                                                                       | AWS S3, Git for artifacts, custom databases (e.g., PostgreSQL)                                             |

---

## **4. Query Examples**
### **4.1 Querying Compliance State (SQL-like Logic)**
Assume a database storing compliance events. Example queries:

#### **Find High-Severity Violations in the Last 30 Days**
```sql
SELECT *
FROM compliance_events
WHERE
  severity = 'high'
  AND timestamp > DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND resolved = FALSE;
```

#### **Count Unresolved Violations by Rule**
```sql
SELECT
  rule_id,
  rule_name,
  COUNT(*) as unresolved_count
FROM compliance_events
WHERE resolved = FALSE
GROUP BY rule_id, rule_name
ORDER BY unresolved_count DESC;
```

#### **List Applications with PCI Violations**
```sql
SELECT DISTINCT
  target_application,
  rule_id,
  COUNT(*) as violation_count
FROM compliance_events
WHERE rule_id LIKE '%PCI%'
GROUP BY target_application, rule_id
HAVING COUNT(*) > 0;
```

---
### **4.2 Querying Policy Registry (JSON/Git)**
#### **Filter Rules by Category (e.g., Preventive)**
```bash
# Assuming policies are stored in a Git repo
git grep -l 'category: "preventive"' -- './policies/**/*.json'
```

#### **Extract All References to GDPR**
```bash
grep -r '"references":.*"GDPR"' ./policies/
```

---
### **4.3 Automated Compliance Checks (Example Script)**
**Python script to validate a set of compliance rules against a system state:**
```python
import json
from datetime import datetime

def validate_rule(rule, system_state):
    # Example: Check if all logs are encrypted (simplified)
    logs = system_state.get("logs", [])
    encrypted_logs = [log for log in logs if log.get("encrypted")]

    if len(encrypted_logs) != len(logs):
        return {
            "status": "violation",
            "details": f"Rule {rule['id']}: {len(logs) - len(encrypted_logs)} unencrypted logs found."
        }
    return {"status": "compliant"}

# Load policy and system state
with open("pci_policy.json") as f:
    policy = json.load(f)

system_state = {
    "logs": [
        {"path": "/var/log/app.log", "encrypted": False},
        {"path": "/var/log/secure.log", "encrypted": True}
    ]
}

# Run validation
results = {rule["id"]: validate_rule(rule, system_state) for rule in policy["rules"]}
print(json.dumps(results, indent=2))
```

**Output:**
```json
{
  "PCI_TLS_12": {
    "status": "violation",
    "details": "Rule PCI_TLS_12: 1 unencrypted logs found."
  }
}
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                                                                                               | **When to Use**                                                                                                   |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| **Policy as Code**       | Define and enforce policies using code (e.g., Terraform, OPA).                                                                                             | When compliance rules need version control and automation (e.g., AWS IAM policies, Kubernetes RBAC).           |
| **Observability as Code** | Centralize logging, metrics, and tracing for compliance auditing.                                                                                         | When visibility into system state is critical (e.g., detecting data leaks in real-time).                        |
| **Secure by Default**    | Design systems to minimize attack surfaces and reduce compliance risks.                                                                            | During new system development to embed compliance early (e.g., default-deny IAM policies).                      |
| **Chaos Engineering**     | Test system resilience to compliance failures (e.g., simulate data breaches).                                                                         | For high-stakes environments (e.g., financial services) to validate breach response plans.                      |
| **Data Mesh**            | Decentralize data ownership with compliance controls (e.g., PII encryption per domain).                                                               | In large organizations with federated data teams (e.g., healthcare systems).                                    |
| **Zero Trust**            | Enforce strict identity and access controls to minimize compliance risks.                                                                              | For environments with high-risk data (e.g., government, defense).                                             |
| **Infrastructure as Code (IaC)** | Manage infrastructure via code to ensure compliant deployments.                                                                                       | When infrastructure configurations drift or need auditing (e.g., AWS CloudFormation, Terraform).             |
| **Event-Driven Security** | React to compliance events (e.g., alerts, remediation) via event streams.                                                                              | For real-time compliance enforcement (e.g., AWS EventBridge, Kafka).                                           |

---

## **6. Best Practices**
1. **Separate Rules by Scope**:
   - Use different policy repositories for **infrastructure**, **application**, and **data** compliance.
   - Example: `policies/infra/`, `policies/app/`, `policies/data/`.

2. **Version Control Policies**:
   - Store compliance rules in Git (e.g., `policies/v1.0.json`) with changelogs for audits.

3. **Automate Audits**:
   - Schedule regular compliance scans (e.g., daily CIS benchmarks) and automate report generation.

4. **Integrate with CI/CD**:
   - Block deployments if compliance checks fail (e.g., OPA gates in GitHub Actions).

5. **Document Exceptions**:
   - Track approved waivers (e.g., for legacy systems) with justification and sunset dates.

6. **Monitor False Positives**:
   - Use machine learning to reduce noise in alerts (e.g., Darktrace’s anomaly detection).

7. **Train Teams**:
   - Educate engineers on compliance implications (e.g., why RBAC matters for SOX).

8. **Leverage Native Tools**:
   - Use built-in compliance features (e.g., AWS Config, GCP Security Command Center) to reduce overhead.

9. **Simulate Breaches**:
   - Use chaos engineering to test compliance response plans (e.g., Chaos Monkey for data leaks).

10. **Stay Updated**:
    - Subscribe to regulatory updates (e.g., GDPR guidance from EDPB) and update rules proactively.

---

## **7. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                                                                                               |
|--------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Overly Complex Rules**             | Start with high-impact, easy-to-enforce rules (e.g., encryption). Decompose complex rules into smaller units.                                           |
| **False Positives Overloading Teams** | Use ML to flag likely false positives (e.g., Darktrace’s Sofia). Prioritize alerts by severity.                                                      |
| **Ignoring Legacy Systems**          | Phase out non