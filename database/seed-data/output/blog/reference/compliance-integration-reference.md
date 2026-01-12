# **[Pattern] Compliance Integration: Reference Guide**

---

## **Overview**
The **Compliance Integration** pattern ensures that applications, services, and workflows automatically adhere to regulatory, industry-specific, and internal policies by embedding compliance checks into core operations. This pattern eliminates manual audits, reduces risk exposure, and streamlines compliance reporting by integrating validation rules, event monitoring, and automated remediation directly into system workflows. It is applicable in environments where strict governance (e.g., HIPAA, GDPR, PCI-DSS, SOX, or financial regulations) is required.

The pattern consists of:
- **Compliance Rules Engine**: A configurable module that enforces policies via dynamic or static validation logic.
- **Event Logging & Auditing**: Immutable records of user actions, system events, and validation outcomes for forensic analysis.
- **Alerting & Remediation**: Automated notifications and corrective actions (e.g., data masking, role adjustments) when violations are detected.
- **Integration with Compliance Frameworks**: Plug-ins or SDKs that map system behavior to standardized compliance models (e.g., OWASP ZAP, IBM Compliance Insight).

This reference guide covers implementation strategies, schema references, query examples, and integrations with broader system patterns.

---

## **Implementation Details**

### **Key Concepts**
| **Concept**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **Validation Rules**      | Defined via YAML, JSON, or custom policies (e.g., "All PII must be encrypted within 24 hours").       |
| **Event Lifecycle**       | Stages: Pre-Action (pre-check), Action (real-time validation), Post-Action (audit log), and Remediation. |
| **Rule Severity Levels**  | Critical (blocks actions), High (flags but allows), Low (logs only).                                |
| **Rule Sources**          | Built-in policies, external APIs (e.g., compliance-as-code tools), or user-defined exceptions.     |
| **Immutable Audit Logs**  | Timestamped, non-editable records of all validated events (e.g., Kafka, relational DB).          |
| **Dynamic Rule Updates**  | Rules can be updated without service downtime via configuration APIs.                                |

---

### **Components**
| **Component**            | **Purpose**                                                                                     | **Example Technologies**                                      |
|--------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| **Rule Engine**          | Executes validation logic against system events/data.                                            | OpenPolicyAgent (OPA), Apache Drools                          |
| **Event Pipeline**       | Captures and processes system events (e.g., user logins, API calls) in real-time.             | Kafka, AWS EventBridge, RabbitMQ                               |
| **Audit Database**       | Stores immutable logs for compliance reporting and forensics.                                   | AWS CloudTrail, PostgreSQL, MongoDB Atlas                     |
| **Alerting System**      | Notifies stakeholders of rule violations via email, Slack, or SIEM.                             | PagerDuty, Splunk, Opsgenie                                       |
| **Remediation Engine**   | Automates corrective actions (e.g., revoke access, re-encrypt data).                           | Custom scripts, AWS Lambda, Kubernetes Operators              |
| **Policy Dashboard**     | Provides real-time visibility into compliance status and rule violations.                       | Grafana, PRT (Policy Reporting Tool), Custom React dashboards  |

---

## **Schema Reference**

### **1. Compliance Rule Schema**
```json
{
  "name": "string (e.g., 'PCI_DSS_HMAC_VIOLATION')",
  "description": "Compliance requirement description",
  "severity": "enum (CRITICAL | HIGH | MEDIUM | LOW)",
  "rule_type": "enum (SYSTEM | USER | DATA | API)",
  "source": {
    "type": "enum (BUILTIN | EXTERNAL | CUSTOM)",
    "id": "string (e.g., 'HIPAA-425')"
  },
  "condition": {
    "field": "string (e.g., 'data.encryption_key.used')",
    "operator": "enum (EQ | GT | CONTAINS | NULL)",
    "value": "any (configures based on operator)"
  },
  "action": {
    "type": "enum (ALERT | BLOCK | MASK | AUDIT_ONLY)",
    "payload": {
      "alert_level": "enum (INFO | WARNING | CRITICAL)",
      "remediation_script": "string (if applicable)"
    }
  },
  "exceptions": [
    {
      "user_id": "string",
      "ip_address": "string",
      "valid_until": "ISO 8601 timestamp"
    }
  ]
}
```

**Example Rule**:
```json
{
  "name": "SOC2_L2_EXPIRED_CERTIFICATE",
  "severity": "CRITICAL",
  "rule_type": "SYSTEM",
  "condition": {
    "field": "tls.certificate.expiry",
    "operator": "LT",
    "value": "2024-06-01"
  },
  "action": {
    "type": "BLOCK",
    "payload": {
      "alert_level": "CRITICAL",
      "remediation_script": "rotate_ssl_certificates.sh"
    }
  }
}
```

---

### **2. Event Schema**
```json
{
  "event_id": "UUID",
  "timestamp": "ISO 8601",
  "type": "enum (USER_ACTION | SYSTEM_EVENT | DATA_CHANGE)",
  "source": "string (e.g., 'auth_service', 'user_console')",
  "payload": {
    "user": {
      "id": "string",
      "role": "string"
    },
    "data": {
      "key": "string",
      "value": "any"
    },
    "context": {
      "ip": "string",
      "request_id": "string"
    }
  },
  "compliance_status": [
    {
      "rule_id": "string",
      "severity": "enum",
      "status": "enum (PASS | FAIL | EXCEPTION)"
    }
  ]
}
```

**Example Event**:
```json
{
  "event_id": "a1b2c3d4-e5f6-7890",
  "timestamp": "2024-05-20T14:25:30Z",
  "type": "DATA_CHANGE",
  "payload": {
    "data": {
      "key": "user.pii.social_security_num",
      "value": "987-65-4321"
    }
  },
  "compliance_status": [
    {
      "rule_id": "GDPR_PII_ENCRYPTION",
      "severity": "HIGH",
      "status": "FAIL"
    }
  ]
}
```

---

### **3. Audit Log Schema**
```json
{
  "log_id": "UUID",
  "event_id": "UUID",
  "rule_triggered": "string",
  "user": "string",
  "action": "string",
  "result": "enum (AUTHORIZED | BLOCKED | MASKED)",
  "metadata": {
    "timestamp": "ISO 8601",
    "ip": "string",
    "system": "string"
  }
}
```

---

## **Query Examples**

### **1. Query Violations in the Last 7 Days**
```sql
-- PostgreSQL
SELECT
  rule_triggered,
  COUNT(*) AS violation_count,
  MAX(timestamp) AS last_violation
FROM compliance_audit_log
WHERE timestamp >= NOW() - INTERVAL '7 days'
  AND result = 'BLOCKED'
GROUP BY rule_triggered
ORDER BY violation_count DESC;
```

### **2. Find Users with PII Exposure (GDPR Violation)**
```sql
-- MongoDB
db.compliance_events.find(
  {
    "compliance_status": {
      "$elemMatch": {
        "rule_id": "GDPR_PII_EXPOSURE",
        "status": "FAIL"
      }
    },
    "payload.user.id": { "$exists": true }
  },
  {
    "payload.user": 1,
    "compliance_status": 1
  }
)
```

### **3. List Exceptions for a Specific Rule**
```bash
# Using a REST API (e.g., Rule Engine)
GET /v1/rules/HIPAA-425/exceptions
Headers: Accept: application/json
Response:
[
  {
    "user_id": "user_785",
    "ip_address": "192.168.1.100",
    "valid_until": "2024-07-01"
  }
]
```

### **4. Filter Events by User Role**
```python
# Using Python (e.g., with an audit log database)
from datetime import datetime, timedelta

def get_role_violations(role, days=7):
    seven_days_ago = datetime.now() - timedelta(days=days)
    query = {
        "compliance_status": {
            "$elemMatch": {
                "status": "FAIL"
            }
        },
        "payload.user.role": role,
        "timestamp": {"$gte": seven_days_ago}
    }
    return db.events.find(query)
```

---

## **Related Patterns**

### **1. Event-Driven Architecture (EDA)**
- **Connection**: Compliance Integration relies on real-time event streams for validation and auditing.
- **Integration**: Use Kafka or AWS EventBridge to fan out events to compliance and other systems.

### **2. Policy-as-Code**
- **Connection**: Compliance rules can be defined as IaC (e.g., Terraform policies, Kubernetes OPA gates).
- **Integration**: Deploy rules via GitOps pipelines to ensure consistency across environments.

### **3. Immutable Infrastructure**
- **Connection**: Audit logs and system states must be tamper-proof for compliance.
- **Integration**: Store logs in S3 + Glacier or blockchain-based ledgers for air-gapped compliance.

### **4. Zero Trust Architecture**
- **Connection**: Enforces least-privilege access and real-time validation of user actions.
- **Integration**: Combine with compliance rules to auto-revoke access for non-compliant users.

### **5. Chaos Engineering**
- **Connection**: Test compliance remediation workflows in low-risk environments.
- **Integration**: Use tools like Gremlin or Chaos Mesh to simulate rule violations (e.g., certificate expiry).

### **6. Observability**
- **Connection**: Visibility into compliance violations is critical for incident response.
- **Integration**: Log compliance events into Prometheus, Datadog, or CloudWatch for monitoring.

---
## **Troubleshooting & Best Practices**
### **Common Challenges**
| **Challenge**                          | **Solution**                                                                                     |
|----------------------------------------|-------------------------------------------------------------------------------------------------|
| **Rule Overhead**                      | Use lightweight rules for low-severity items; cache rule evaluations.                            |
| **False Positives**                    | Implement exception workflows and user overrides with approval gates.                           |
| **Rule Drift**                         | Automate rule reconciliation with external frameworks (e.g., NIST, ISO).                        |
| **Performance Bottlenecks**            | Deploy rule engines as microservices; batch validate non-critical events.                        |
| **Multi-Region Compliance**            | Use global rule versions with regional exception policies.                                       |

### **Best Practices**
1. **Start Small**: Pilot compliance integration with one high-risk workflow (e.g., data encryption).
2. **Automate Exceptions**: Define clear processes for temporary rule overrides (with audit).
3. **Test Remediation**: Validate remediation scripts in staging before deployment.
4. **Document Rules**: Maintain a compliance rule registry with owners and change logs.
5. **Combine Patterns**: Integrate with Zero Trust for granular access control and Chaos Engineering for resilience testing.

---
## **Example Workflow: GDPR PII Compliance**
1. **Event**: User uploads `user_data.csv` containing PII to the application.
2. **Validation**:
   - Rule `GDPR_PII_ENCRYPTION` triggers.
   - Checks if `user_data.csv` is encrypted.
   - Fails: `value = false`, `severity = CRITICAL`.
3. **Action**:
   - Alerts Slack channel (#compliance-alerts).
   - Blocks upload for the user (remediation: "Encrypt data before re-upload").
4. **Audit**:
   - Logs event in PostgreSQL with `result = BLOCKED`.
   - Generates report for GDPR inspector via API.

---
**References**:
- NIST SP 800-53: Security and Privacy Controls for Systems and Organizations.
- OWASP Compliance-As-Code Project.
- AWS Well-Architected Compliance Framework.