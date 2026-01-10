**[Pattern] Audit Approaches: Reference Guide**

---

### **Overview**
The **Audit Approaches** pattern enables organizations to systematically review security controls, compliance adherence, and operational risks by applying tailored audit methodologies. This pattern categorizes audits into structured approaches—**Compliance Audits**, **Risk-Based Audits**, **Technical Audits**, and **Process Audits**—to ensure thorough and efficient assessments. By defining clear audit scopes, criteria, and frequencies, this pattern supports regulatory compliance, incident response, and continuous improvement. It integrates with other patterns like *Access Control*, *Logging & Monitoring*, and *Configuration Management* to provide a holistic security posture evaluation framework.

---

### **Key Concepts & Implementation Details**

#### **1. Audit Approaches: Definitions**
| **Approach**         | **Description**                                                                                     | **Key Focus Areas**                                                                                     |
|----------------------|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Compliance Audit** | Evaluates adherence to industry standards (e.g., GDPR, PCI-DSS, HIPAA) or internal policies.         | Regulatory alignment, documentation, governance, third-party vendor compliance.                        |
| **Risk-Based Audit** | Prioritizes controls based on threat severity, impact, or likelihood of exploitation.         | Vulnerability exposure, residual risk, mitigation effectiveness, regulatory gaps.                       |
| **Technical Audit**  | Assesses system configurations, access controls, encryption, and technical safeguards.            | Network segmentation, IAM policies, patch management, endpoint security, logging retention.             |
| **Process Audit**    | Reviews workflows, change management, and operational procedures for efficiency and security.   | Incident response workflows, escalation paths, documentation accuracy, employee training records.     |

#### **2. Core Components**
| **Component**        | **Purpose**                                                                                     | **Example Implementation**                                                                         |
|----------------------|-------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| **Audit Scope**      | Defines boundaries (e.g., systems, departments, geographies)                                    | *"Audit all web applications hosted on AWS EC2 instances in the 'prod' environment."*               |
| **Criteria**         | Checklist of controls or metrics evaluated (e.g., "Is MFA enforced for admin accounts?").      | *"Compliance with NIST SP 800-171 for data handling."*                                               |
| **Frequency**        | Scheduling (e.g., annual, post-incident, quarterly).                                            | *"Risk-based audits conducted every 6 months for high-severity assets."*                             |
| **Evidence Sources** | Data inputs (e.g., logs, configuration files, interview transcripts).                           | *"Review SIEM alerts for suspicious activity during the audit period."*                              |
| **Ownership**        | Responsible team (e.g., Security Team, Compliance Officer).                                     | *"IT Security leads process audits; Legal handles GDPR compliance audits."*                        |
| **Reporting**        | Output format (e.g., findings report, automated dashboards).                                     | *"Generate a finding summary with remediation deadlines in a Jira ticket."                          |

#### **3. Audit Lifecycle**
1. **Planning**
   - Define scope, criteria, and resources.
   - Example: *"Audit all RDBMS servers for SQL injection vulnerabilities using OWASP tests."*

2. **Execution**
   - Collect evidence (e.g., automated scans, manual reviews).
   - Example: *"Run Nessus scans on endpoint hosts and cross-reference with patch records."*

3. **Analysis**
   - Compare evidence against criteria.
   - Example: *"30% of admin accounts lack MFA (finding: C101).*"

4. **Reporting**
   - Document findings, risks, and remediation steps.
   - Example: *"Top 3 risks: Unpatched servers (25%), insufficient logging (18%), third-party vendor gaps (15%)."*

5. **Remediation**
   - Track fixes and re-audit if needed.
   - Example: *"MFA enforced via Conditional Access policies by Q3 2024."*

6. **Closure**
   - Archive audit artifacts and update procedures.
   - Example: *"Retire audit package in the compliance repository."*

---

### **Schema Reference**
Below is a structured schema for defining audit approaches in JSON/YAML format. Use this to model audits in your tooling (e.g., databases, configuration files).

```json
{
  "audit_approaches": [
    {
      "name": "PCI-DSS Annual Compliance Audit",
      "type": "Compliance",
      "scope": {
        "assets": ["payment gateways", "POS systems"],
        "geographies": ["NA", "EU"],
        "timeframe": "Jan 1–Dec 31"
      },
      "criteria": [
        {
          "id": "PCI.01",
          "description": "MFA enforced for all admin accounts",
          "evidence_sources": ["IAM logs", "password policy documents"]
        },
        {
          "id": "PCI.02",
          "description": "PCI DSS v4.0 requirements met",
          "evidence_sources": ["automated scanner reports", "manual validation"]
        }
      ],
      "frequency": "annual",
      "owner": "Compliance Team",
      "report_template": {
        "format": "PDF",
        "fields": ["findings", "remediation_status", "due_date"]
      },
      "related_patterns": ["Access Control", "Logging & Monitoring"]
    },
    {
      "name": "Critical Infrastructure Risk-Based Audit",
      "type": "Risk-Based",
      "scope": {
        "assets": ["SCADA systems", "industrial IoT"],
        "risk_level": "High"
      },
      "criteria": [
        {
          "id": "RISK.H01",
          "description": "Zero Trust network segmentation enforced",
          "evidence_sources": ["network topology diagrams", "firewall rules"]
        }
      ],
      "frequency": "quarterly",
      "owner": "Security Operations"
    }
  ]
}
```

---

### **Query Examples**
Use these queries to automate audit data retrieval in tools like **SQL**, **Elasticsearch**, or **SPL (Splunk)**.

#### **1. List All Audits for a Specific Type**
**SQL:**
```sql
SELECT *
FROM audit_schedules
WHERE audit_type = 'Compliance';
```

**Elasticsearch:**
```json
{
  "query": {
    "match": { "type": "Compliance" }
  }
}
```

#### **2. Find Overdue Audits**
**SQL:**
```sql
SELECT a.name, s.due_date, a.owner
FROM audit_schedules a
JOIN schedule_status s ON a.id = s.audit_id
WHERE s.due_date < CURRENT_DATE AND s.status != 'Completed';
```

**Splunk:**
```spl
| search index=audits earliest=-30d
| where end_time < now()
| table audit_name, owner, end_time
```

#### **3. Cross-Reference Findings with Vulnerabilities**
**SQL:**
```sql
SELECT f.finding_id, v.cve_id, v.severity
FROM findings f
JOIN vulnerabilities v ON f.related_vuln = v.cve_id
WHERE f.audit_id = 42;
```

#### **4. Generate a Risk Heatmap (Risk-Based Audits)**
**Python (Pandas):**
```python
import pandas as pd

audit_data = pd.read_csv("audit_risks.csv")
risk_matrix = audit_data.pivot_table(
    index="severity",
    columns="likelihood",
    values="count",
    aggfunc="sum"
)
print(risk_matrix)
```

---

### **Automation Integration**
To streamline audit approaches, integrate with the following tools:
| **Tool**               | **Integration Use Case**                                                                 |
|------------------------|----------------------------------------------------------------------------------------|
| **SIEM (e.g., Splunk)** | Automate evidence collection (e.g., logs, alerts) for audit criteria.                   |
| **CMDB (e.g., ServiceNow)** | Sync asset inventories to define audit scopes dynamically.                          |
| **Vulnerability Scanners** | Feed findings into audit reports (e.g., Nessus → Compliance Audit).               |
| **Ticketing (e.g., Jira)** | Auto-create tickets for remediation steps from audit findings.                       |
| **Configuration Management (e.g., Ansible)** | Verify compliance of configurations post-remediation.                                |

---

### **Related Patterns**
To enhance the Audit Approaches pattern, reference these supplementary patterns for broader security coverage:

| **Pattern**                  | **Connection to Audit Approaches**                                                                                     | **Example Synergy**                                                                                     |
|------------------------------|---------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| **Access Control**           | Audits rely on accurate IAM policies to verify compliance with criteria like "least privilege."                       | *"Audit Approach: Verify MFA enforcement (Access Control pattern)."*                                    |
| **Logging & Monitoring**     | Audit evidence (e.g., logs) is critical for validating controls like "incident response time."                      | *"Audit Approach: Review SIEM alerts for compliance events (Logging pattern)."*                          |
| **Configuration Management** | Automated audits of system configurations (e.g., CIS benchmarks) reduce manual effort.                            | *"Audit Approach: Scan servers for CIS v8 compliance (Config Mgmt pattern)."*                             |
| **Incident Response**        | Post-incident audits assess whether response plans were followed.                                                   | *"Audit Approach: Review breach response documentation for SOPs compliance."*                            |
| **Third-Party Risk**        | Vendor audits are a subset of compliance audits (e.g., GDPR for outsourced data processing).                     | *"Audit Approach: Assess third-party vendors' security controls (Third-Party Risk pattern)."*            |
| **Data Loss Prevention (DLP)** | Audits can validate DLP policies (e.g., encryption, data masking) are enforced.                                     | *"Audit Approach: Scan for unencrypted PII storage (DLP pattern)."*                                      |

---

### **Best Practices**
1. **Standardize Criteria**: Use templates for common audits (e.g., ISO 27001, CIS Controls) to ensure consistency.
2. **Automate Evidence Collection**: Leverage APIs (e.g., AWS Config, Azure Policy) to reduce manual work.
3. **Link to Remediation**: Tag findings with Jira/Git issues for tracking progress.
4. **Document Exceptions**: Justify deviations from criteria (e.g., *"MFA waived for legacy system X due to vendor lock-in"*).
5. **Train Auditors**: Ensure auditors understand the tools and criteria (e.g., OWASP ZAP for web app audits).
6. **Update Frequently**: Revisit audit approaches annually or after major policy changes (e.g., GDPR updates).
7. **Leverage Dashboards**: Visualize audit trends (e.g., "Compliance score over 3 years") for leadership reports.

---
### **Example Workflow: Risk-Based Audit**
1. **Trigger**: Security Team identifies a new threat (e.g., ransomware exploits).
2. **Scope**: Audit all file servers with unclear backup procedures (`Risk Level: High`).
3. **Criteria**:
   - *"Backups tested monthly (C1)"*.
   - *"Encryption enabled on shared drives (C2)"*.
4. **Evidence**: Query SIEM for backup failure alerts; review cloud storage policies.
5. **Finding**: *"C2 failed for 15% of drives (Critical)"*.
6. **Remediation**: Deploy Azure Site Recovery; re-audit in 3 months.
7. **Report**: *"Reduced risk exposure by 80% post-remediation."*

---
**See Also**:
- [Access Control Pattern](link) for IAM audit criteria.
- [Logging & Monitoring Pattern](link) for evidence sourcing.