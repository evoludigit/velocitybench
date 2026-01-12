# **[Pattern] Reference Guide: Compliance Standards (PCI, HIPAA, GDPR)**

---
## **Overview**
This **Compliance Standards (PCI, HIPAA, GDPR)** pattern provides a structured approach to integrating and enforcing regulatory compliance requirements into technical architectures, workflows, and system designs. It ensures alignment with **Payment Card Industry Data Security Standard (PCI DSS)**, **Health Insurance Portability and Accountability Act (HIPAA)**, and **General Data Protection Regulation (GDPR)** while minimizing operational overhead. This guide covers key components, implementation best practices, validation mechanisms, and integration points to help teams maintain continuous compliance.

The pattern addresses:
✅ **Data Protection:** Encryption, access controls, and anonymization.
✅ **Audit & Monitoring:** Logging, anomaly detection, and regular risk assessments.
✅ **Incident Response:** Automated alerts, breach containment, and documentation.
✅ **Vendor & Third-Party Controls:** Contractual obligations and compliance tracking.

---

## **Schema Reference**
Below is a structured schema defining the core elements of the **Compliance Standards** pattern, along with their attributes and relationships.

| **Component**               | **Attributes**                                                                 | **Type**      | **Description**                                                                                                                                                                                                 |
|------------------------------|---------------------------------------------------------------------------------|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Compliance Framework**     | `id`, `name` (PCI, HIPAA, GDPR), `version`, `scope` (global/regional)          | Object        | Defines the regulatory framework, its version, and applicable jurisdiction.                                                                                                                                       |
| **Requirement**              | `id`, `frameworkId`, `title`, `description`, `severity` (Critical/Low)          | Object        | Individual compliance requirement (e.g., "Encrypt PII at rest").                                                                                                                                                    |
| **Control**                  | `id`, `requirementId`, `type` (Technical/Administrative), `status` (Active/Inactive) | Object        | Implementation mechanism for a requirement (e.g., "Enable TLS 1.2+").                                                                                                                                              |
| **Data Classification**      | `id`, `name` (PII, PCI Data, PHI), `sensitivityLevel` (High/Medium/Low)        | Object        | Categorizes data based on regulatory sensitivity.                                                                                                                                                               |
| **Access Policy**            | `id`, `dataClassificationId`, `role` (Admin/User), `permissions` (Read/Write)   | Object        | Defines access rules for classified data (e.g., "HIPAA PHI: Read-Only for Clinicians").                                                                                                                         |
| **Audit Log**                | `id`, `eventType` (Login/Deletion), `timestamp`, `userId`, `severity`           | Object        | Records system events for compliance audits.                                                                                                                                                                      |
| **Incident**                 | `id`, `status` (Open/Resolved), `impact` (PCI/HIPAA/GDPR), `mitigationSteps`   | Object        | Tracks security incidents and their resolution.                                                                                                                                                                 |
| **Vendor Contract**          | `id`, `vendorName`, `complianceScope` (PCI/HIPAA), `contractTerms`             | Object        | Manages third-party compliance obligations.                                                                                                                                                                       |
| **Compliance Scan**          | `id`, `frameworkId`, `scanDate`, `results` (Pass/Fail), `remediationStatus`     | Object        | Automated/manual compliance assessment results.                                                                                                                                                                    |
| **User Training Record**     | `id`, `userId`, `frameworkId`, `completionDate`, `certificate`                 | Object        | Tracks employee training on compliance policies.                                                                                                                                                                      |

---

### **Relationships Between Components**
1. **Framework → Requirements**
   - A compliance framework (e.g., GDPR) contains multiple requirements (e.g., "Right to Erasure").
2. **Requirement → Controls**
   - Each requirement maps to one or more controls (e.g., "Encrypt PII with AES-256").
3. **Data Classification → Access Policy**
   - Data sensitivity (e.g., "PCI Cardholder Data") defines access permissions.
4. **Audit Log → Incident**
   - Logs may trigger incidents (e.g., unauthorized access to PHI).
5. **Compliance Scan → Remediation Status**
   - Scan failures flag controls needing fixes (linked to **Control** status).

---

## **Implementation Best Practices**
### **1. Data Protection**
- **Encryption:**
  - Use **AES-256** for data at rest (PCI, GDPR) and **TLS 1.2+** in transit (PCI, HIPAA).
  - Example: Store credit card numbers in a **tokenized database field** (PCI DSS 3.5.2).
- **Masking/Anonymization:**
  - Apply **dynamic data masking** for PHI/PII (e.g., `XXX-XXX-1234` for SSNs).
  - Use **differential privacy** for GDPR-compliant analytics.

### **2. Access Control**
- **Principle of Least Privilege (PoLP):**
  - Assign roles (e.g., `Compliance_Auditor`, `PCI_Processor`) via **RBAC**.
  - Example: Limit HIPAA PHI access to `Clinical_Team` only.
- **Multi-Factor Authentication (MFA):**
  - Enforce MFA for **administrative accounts** (PCI DSS 8.3.3, GDPR Art. 25).

### **3. Audit & Monitoring**
- **Centralized Logging:**
  - Use **SIEM tools** (e.g., Splunk, ELK) to collect logs from web apps, databases, and APIs.
  - Retain logs for **7 years** (HIPAA) or **6 years** (GDPR).
- **Automated Alerts:**
  - Trigger alerts for:
    - Failed login attempts (HIPAA Security Rule).
    - Unauthorized data exports (GDPR Art. 32).

### **4. Incident Response**
- **Playbooks:**
  - Define steps for **PCI breaches** (e.g., notify card networks within 72 hours).
  - For GDPR, notify authorities within **72 hours** of data breaches (Art. 33).
- **Documentation:**
  - Maintain an **incident log** with:
    - Timestamp, root cause, actions taken, and resolution status.

### **5. Vendor Management**
- **Contract Clauses:**
  - Require vendors to sign **compliance agreements** (e.g., AICPA SOC 2 for GDPR).
  - Example: "Vendor must implement PCI DSS in its infrastructure."
- **Monitoring:**
  - Conduct **quarterly vendor compliance audits** (PCI DSS 12.8).

### **6. Employee Training**
- **Annual Refresh:**
  - Certify employees on **PCI DSS**, **HIPAA Security Rule**, and **GDPR** annually.
- **Phishing Simulations:**
  - Test for awareness of **social engineering risks** (GDPR Art. 32).

---

## **Query Examples**
Below are sample queries (using **GraphQL** or **SQL-like syntax**) to interact with the compliance schema.

---

### **1. List All Active PCI Controls**
```graphql
query {
  complianceFramework(name: "PCI DSS") {
    requirements(severity: "Critical") {
      controls(status: "Active") {
        type
        description
      }
    }
  }
}
```
**Expected Output:**
```json
{
  "data": {
    "complianceFramework": {
      "requirements": [
        {
          "controls": [
            { "type": "Technical", "description": "Encrypt PII at rest" },
            { "type": "Administrative", "description": "Conduct annual risk assessments" }
          ]
        }
      ]
    }
  }
}
```

---

### **2. Find Users with HIPAA PHI Access**
```sql
SELECT u.userId, u.role
FROM User u
JOIN AccessPolicy ap ON u.userId = ap.userId
JOIN DataClassification dc ON ap.dataClassificationId = dc.id
WHERE dc.name = 'HIPAA_PHI';
```
**Expected Output:**
| userId | role        |
|--------|-------------|
| user123| Clinical_Team |
| user456| Admin       |

---

### **3. Identify Unresolved Incidents Impacting GDPR**
```graphql
query {
  incidents(impact: ["GDPR"]) {
    id
    status
    mitigationSteps
  }
}
```
**Expected Output:**
```json
{
  "data": {
    "incidents": [
      {
        "id": "inc001",
        "status": "Open",
        "mitigationSteps": ["Isolate affected system", "Notify DPO"]
      }
    ]
  }
}
```

---

### **4. Check Compliance Scan Results for GDPR**
```sql
SELECT frameworkId, scanDate, results, remediationStatus
FROM ComplianceScan
WHERE frameworkId = 'GDPR' AND scanDate > '2023-01-01';
```
**Expected Output:**
| frameworkId | scanDate   | results | remediationStatus |
|-------------|------------|---------|-------------------|
| GDPR        | 2023-05-15 | Fail    | Pending           |

---

## **Related Patterns**
1. **[Security Incident Response]**
   - Integrates with this pattern for **incident logging** and **compliance-driven containment**.

2. **[Data Masking & Tokenization]**
   - Complements **PCI DSS** requirements for encrypting cardholder data.

3. **[Role-Based Access Control (RBAC)]**
   - Provides granular access policies for **HIPAA/PHI** and **GDPR PII**.

4. **[Audit Logging & Compliance Monitoring]**
   - Extends **audit log** requirements for **GDPR Art. 30** and **HIPAA Security Rule**.

5. **[Third-Party Risk Management]**
   - Works with **vendor contract tracking** for **PCI DSS 12** and **GDPR Art. 28**.

6. **[Privacy-Preserving Analytics]**
   - Supports **GDPR’s right to erasure** via anonymization techniques.

---

## **Tools & Integrations**
| **Tool Category**       | **Recommended Tools**                                                                 |
|--------------------------|--------------------------------------------------------------------------------------|
| **Compliance Scanning**  | PCI: **PCI DSS Scanner** (Qualys, Rapid7)                                             |
|                          | HIPAA/GDPR: **Deloitte GDPR Assessment Tool**, **Trusteer**                            |
| **Access Control**       | **Okta**, **PingIdentity** (RBAC), **Vault** (secret management)                     |
| **Audit Logging**        | **Splunk**, **ELK Stack**, **Datadog**                                                |
| **Incident Response**    | **SentinelOne**, **Palo Alto XSOAR**, **Demisto**                                    |
| **Vendor Management**    | **OneTrust**, **Trusona** (third-party risk)                                         |
| **Employee Training**    | **KnowBe4**, **PhishMe** (security awareness)                                       |

---

## **Key Takeaways**
- **PCI DSS:** Focus on **cardholder data protection** (encryption, access controls).
- **HIPAA:** Prioritize **PHI security** (audit logs, incident reporting).
- **GDPR:** Ensure **user rights** (right to access, erasure) and **data minimization**.
- **Automation:** Use **SIEM tools** and **compliance scanners** to reduce manual effort.
- **Documentation:** Maintain records for **audits** (HIPAA: **Business Associate Agreements**, GDPR: **records of processing activities**).

---
**Next Steps:**
- Map existing systems to this schema.
- Automate compliance checks via **CI/CD pipelines**.
- Schedule **quarterly compliance reviews**.