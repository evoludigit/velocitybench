# **[Pattern] Audit Guidelines Reference Guide**

---

## **Overview**
The **Audit Guidelines** pattern provides a structured framework for defining, documenting, and enforcing standardized audit requirements across systems, applications, or organizational processes. It ensures compliance with regulatory mandates (e.g., GDPR, HIPAA, SOX), enhances security visibility, and simplifies forensic investigations by centralizing audit rules, logging policies, and exception-handling workflows.

This pattern is critical for:
- **Compliance audits:** Aligning with legal/industry standards.
- **Operational transparency:** Standardizing how changes, access, and events are recorded.
- **Risk mitigation:** Automating anomaly detection via predefined audit triggers.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                 | **Example**                          |
|------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Audit Rule**         | A predefined condition for logging (e.g., "Log all failed login attempts"). | `IF (status = "FAILED") THEN LOG`     |
| **Audit Action**       | The specific event or operation to be audited (e.g., user delete, file access). | `DELETE_USER`, `READ_FILE`           |
| **Audit Scope**        | The boundaries of what is audited (e.g., system-wide, application-level).     | `DATABASE`, `CLOUD_STORAGE`          |
| **Audit Severity**     | Priority/urgency level (e.g., Critical, High, Medium, Low).                 | `CRITICAL (Data Exfiltration)`        |
| **Audit Log Entry**    | A structured record containing event details (timestamp, actor, action).      | JSON/XML payload                     |
| **Audit Policy**       | A collection of rules tied to a specific domain (e.g., "PCI-DSS Compliance").   | `PCI_AUDIT Policy`                   |
| **Alert Threshold**    | Trigger for alerts based on rule violations (e.g., "Alert if 5+ failures").  | `THRESHOLD = 5`                      |
| **Retention Policy**   | Rules governing how long audit logs are retained.                             | `7 years for financial transactions`  |

---

## **Schema Reference**
### **Audit Rule Schema (JSON)**
```json
{
  "rule_id": "AUDIT_RULE_001",
  "name": "Failed Login Attempts",
  "description": "Log all failed login attempts to detect brute-force attacks.",
  "scope": ["AUTHENTICATION_SERVICE"],
  "severity": "HIGH",
  "action": {
    "type": "LOG",
    "parameters": {
      "fields": ["user_id", "ip_address", "timestamp", "attempt_count"]
    }
  },
  "conditions": [
    { "field": "status", "operator": "==", "value": "FAILED" }
  ],
  "alert": {
    "enabled": true,
    "threshold": 5,
    "recipients": ["security_team@example.com"]
  },
  "retention_days": 90
}
```

### **Audit Log Entry Schema**
```json
{
  "event_id": "LOG_20240615_143022_5678",
  "timestamp": "2024-06-15T14:30:22Z",
  "rule_id": "AUDIT_RULE_001",
  "actor": {
    "user_id": "usr_456",
    "role": "AUDITOR"
  },
  "action": {
    "type": "LOGIN_ATTEMPT",
    "status": "FAILED",
    "details": {
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0"
    }
  },
  "context": {
    "system": "SSO_SERVICE",
    "environment": "PRODUCTION"
  }
}
```

---

## **Implementation Guidance**
### **1. Define Audit Policies**
- **Scope:** Align with regulations (e.g., GDPR’s "Right to Erasure" may require auditing data deletions).
- **Ownership:** Assign a compliance officer to maintain policies.
- **Versioning:** Tag policies with versions (e.g., `PCI_DSS_V3.2.1`).

### **2. Implement Audit Rules**
- **Use Cases:**
  - **Access Control:** Audit all `GRANT`/`REVOKE` commands in a database.
  - **Data Sensitivity:** Flag access to PII fields (e.g., `SSN`, `Credit_Card`).
  - **Configuration Changes:** Log all modifications to server settings (e.g., `CVE-2023-1234` patches).
- **Tools:**
  - **Open-Source:** [OSSEC](https://www.ossec.net/), [Falco](https://falco.org/).
  - **Commercial:** Splunk Audit, IBM QRadar, Datadog.

### **3. Deploy Audit Log Storage**
- **Requirements:**
  - **Immutability:** Prevent tampering (e.g., write-once storage like AWS S3 Object Lock).
  - **Searchability:** Index logs for fast querying (e.g., Elasticsearch, Azure Log Analytics).
  - **Retention:** Comply with legal holds (e.g., HIPAA’s 6-year requirement).
- **Example Architecture:**
  ```
  [Application] → [Audit Agent] → [Centralized Log Store] → [SIEM/Analytics Tool]
  ```

### **4. Automate Alerting**
- **Triggers:**
  - Repeated failed attempts (`THRESHOLD=5`).
  - Unusual access patterns (e.g., `user_id=usr_123` accessing `FINANCE_DB` at `3 AM`).
- **Tools:**
  - SIEM systems (Splunk, Wazuh).
  - Cloud-native (AWS CloudTrail + SNS for alerts).

### **5. Test and Validate**
- **Red Team Exercises:** Simulate attacks to verify rule coverage.
- **Automated Checks:** Use tools like [OWASP ZAP](https://www.zaproxy.org/) to validate audit trails.

---

## **Query Examples**
### **1. Query Failed Logins (SQL)**
```sql
SELECT
    user_id,
    ip_address,
    COUNT(*) as failure_count
FROM audit_logs
WHERE rule_id = 'AUDIT_RULE_001'
  AND status = 'FAILED'
GROUP BY user_id, ip_address
HAVING COUNT(*) > 5
ORDER BY failure_count DESC;
```

### **2. Find Unusual Access Patterns (Elasticsearch)**
```json
GET /audit_logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "action.type": "DB_ACCESS" } },
        { "range": { "@timestamp": { "gte": "now-1d/d" } } }
      ],
      "filter": [
        { "term": { "context.environment": "PRODUCTION" } },
        { "script": {
            "script": "params.unusualAccess = (doc['user_id'].value == 'usr_123' && doc['context.path'].value.contains('FINANCE'))"
          }
        }
      ]
    }
  }
}
```

### **3. List All High-Severity Rules (Python + API)**
```python
import requests

response = requests.get("https://audit-server/rules?severity=HIGH")
rules = response.json()
for rule in rules:
    print(f"Rule ID: {rule['rule_id']}, Name: {rule['name']}")
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                          |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------|
| **[Event Sourcing]**      | Capture state changes as immutable logs for replayability.                     | Financial transactions                |
| **[Centralized Logging]** | Aggregate logs from multiple sources in a single repository.                   | Troubleshooting distributed systems   |
| **[SIEM Integration]**    | Correlate audit logs with threat intel feeds for real-time alerts.             | Cybersecurity incident response      |
| **[Policy as Code]**      | Define audit policies using declarative languages (e.g., YAML, Open Policy Agent). | IaC (Infrastructure as Code) compliance |
| **[Immutable Storage]**    | Store logs in systems where data cannot be altered after writing.              | Legal compliance (e.g., GDPR audits)  |
| **[Anomaly Detection]**   | Use ML to flag deviations from normal audit patterns.                          | Detecting insider threats             |

---

## **Best Practices**
1. **Granularity:** Audit at the right level (e.g., API call vs. system shutdown).
2. **Minimize Overhead:** Avoid excessive logging that impacts performance.
3. **Standardize Formats:** Use structured logs (e.g., Common Event Format) for consistency.
4. **Regular Reviews:** Update rules quarterly to align with new threats/regulations.
5. **Employee Training:** Ensure teams know how to interpret audit logs (e.g., "Why was my access blocked?").

---
**Note:** For cloud environments, leverage native audit services (e.g., AWS CloudTrail, Azure Monitor). For on-premises, consider [Linux Audit Framework](https://linux-audit.github.io/) or Windows Event Tracing for Windows (ETW).