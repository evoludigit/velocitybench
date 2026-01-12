---

**[Pattern: **Compliance Guidelines**] Reference Guide**

---

### **Overview**
The **Compliance Guidelines** pattern provides a structured framework for defining, maintaining, and validating rules that ensure adherence to regulatory, organizational, or industry standards. These guidelines are typically represented as a **composable set of rules**, each with defined:
- **Scope** (applicable systems/data domains)
- **Severity levels** (e.g., critical, high, medium, low)
- **Validation methods** (static checks, runtime assertions, automated audits)
- **Remediation steps** (corrective actions if violated)

This pattern ensures traceability, automates compliance checks, and minimizes manual review overhead. It is widely used in **enterprise governance, risk management, and compliance (GRC)**, **financial services (AML/KYC)**, **healthcare (HIPAA/GDPR)**, and **cybersecurity**.

---

### **Key Concepts**

| **Term**               | **Definition**                                                                                                                                                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Guideline**          | A high-level principle (e.g., "Customer data must be encrypted at rest").                                                                                                                                       |
| **Rule**               | A machine-enforceable condition derived from a guideline (e.g., "All PII fields must use AES-256 encryption by [date]").                                                        |
| **Control**            | A mechanism to enforce a rule (e.g., database column constraints, API gateways, or scheduled scans).                                                                                                           |
| **Exemption**          | A documented pause or waiver for a rule (e.g., legacy systems not yet upgraded).                                                                                                                                |
| **Audit Trail**        | A log of rule violations, remediation attempts, and compliance status updates.                                                                                                                                   |
| **Severity**           | Priority level for rule violations (e.g., `critical` = system-wide failure risk, `low` = minor formatting issue).                                                                                             |

---

### **Schema Reference**
Below is the core schema for **Compliance Guidelines** in JSON/JSON Schema format.

#### **1. `ComplianceGuideline` (Top-Level Object)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ComplianceGuideline",
  "description": "A structured guideline for regulatory adherence.",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },  // Unique identifier
    "name": { "type": "string", "maxLength": 255" },
    "description": { "type": "string" },
    "scope": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "system": { "type": "string" },       // e.g., "Payment Service"
          "dataDomain": { "type": "string" },   // e.g., "Customer Records"
          "entityType": { "type": "string" }    // e.g., "API Endpoint"
        }
      }
    },
    "severity": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"]
    },
    "createdAt": { "type": "string", "format": "date-time" },
    "updatedAt": { "type": "string", "format": "date-time" },
    "rules": { "type": "array", "items": "$ref": "#/definitions/ComplianceRule" },
    "exemptions": { "type": "array", "items": "$ref": "#/definitions/Exemption" },
    "relatedStandards": {
      "type": "array",
      "items": { "type": "string" }  // e.g., ["GDPR", "PCI-DSS"]
    },
    "status": {
      "type": "string",
      "enum": ["draft", "active", "deprecated", "obsolete"]
    }
  }
}
```

#### **2. `ComplianceRule` (Nested Object)**
```json
"definitions": {
  "ComplianceRule": {
    "type": "object",
    "properties": {
      "id": { "type": "string", "format": "uuid" },
      "description": { "type": "string" },
      "condition": {
        "type": "object",
        "properties": {
          "field": { "type": "string" },       // e.g., "password"
          "operator": {
            "type": "string",
            "enum": ["equals", "contains", "matchesRegex", "greaterThan"]
          },
          "value": { "type": "string" },        // or `number`/`boolean`
          "expression": { "type": "string" }    // Custom logic (e.g., "age > 18")
        }
      },
      "controls": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": { "type": "string" },        // e.g., "databaseConstraint", "apiValidator"
            "implementation": {
              "type": "object",
              "properties": {
                "code": { "type": "string" },     // e.g., "NOT NULL"
                "script": { "type": "string" }    // Custom logic (e.g., SQL/JS)
              }
            }
          }
        }
      },
      "automatedCheck": {
        "type": "boolean",
        "default": true
      },
      "remediationSteps": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "step": { "type": "string" },
            "owner": { "type": "string" },       // Role (e.g., "DevOps", "Security")
            "dueDate": { "type": "string", "format": "date" }
          }
        }
      },
      "validationFrequency": {
        "type": "string",
        "enum": ["real-time", "daily", "weekly", "monthly"]
      }
    }
  }
}
```

#### **3. `Exemption` (Nested Object)**
```json
"Exemption": {
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "reason": { "type": "string" },
    "approvedBy": { "type": "string" },  // e.g., "Compliance Officer"
    "validFrom": { "type": "string", "format": "date" },
    "validUntil": { "type": "string", "format": "date" },
    "ruleId": { "type": "string", "format": "uuid" }
  }
}
```

---
### **Query Examples**
Use the following queries to interact with **Compliance Guidelines** in a graph database (e.g., Neo4j) or relational system.

#### **1. List All Active Compliance Guidelines**
```cypher
MATCH (g:ComplianceGuideline {status: "active"})-[:CONTAINS]->(r:ComplianceRule)
RETURN g.name, g.id, r.description, r.severity
ORDER BY g.name
```

#### **2. Find Violation Reports for a Specific Rule**
```sql
-- PostgreSQL example
SELECT
  a.audit_id,
  c.guideline_name,
  r.rule_description,
  v.violation_timestamp,
  v.severity,
  CASE WHEN v.remediated = true THEN 'Resolved' ELSE 'Open' END AS status
FROM
  violation_logs v
JOIN
  compliance_rules r ON v.rule_id = r.id
JOIN
  guidelines c ON r.guideline_id = c.id
WHERE
  r.id = 'rule-uuid-123'
  AND v.remediated = false
ORDER BY v.violation_timestamp DESC;
```

#### **3. Check Exemptions for Legacy Systems**
```json
// GraphQL query
query GetExemptions($system: String!) {
  guidelines(filter: { scope: { system: $system } }) {
    exemptions {
      id
      reason
      validFrom
      validUntil
    }
  }
}
```

#### **4. Generate a Compliance Report**
```powershell
# CLI tool example: Export violations by severity
compliance-report --format csv --severity "critical" |
  convert-to-csv -Property guideline,rule,violationCount,lastSeen |
  Export-Csv -Path "critical-violations.csv"
```

---

### **Implementation Details**
#### **1. Data Sources**
- **Static Sources**: Configuration files (YAML/JSON), policies stored in a GRC platform (e.g., ServiceNow, MetricStream).
- **Dynamic Sources**: Runtime checks (e.g., API response validation, database triggers).
- **External Sources**: Third-party APIs (e.g., credit bureau checks for AML).

#### **2. Validation Methods**
| **Method**               | **Use Case**                                  | **Tools/Examples**                          |
|--------------------------|-----------------------------------------------|---------------------------------------------|
| **Static Analysis**      | Code reviews, config validation               | SonarQube, OWASP ZAP                         |
| **Runtime Assertions**   | API/Data validation                           | OpenAPI/Swagger validators, Prisma hooks    |
| **Scheduled Scans**      | Regular compliance checks                    | Trivy, Aqua Security                        |
| **Event Triggers**       | Real-time monitoring                         | AWS Lambda for S3 access logs                |
| **User Workflows**       | Manual approvals/exemptions                   | Jira/Confluence plugins                     |

#### **3. Exemption Workflow**
1. **Request**: Team submits an exemption via a portal (e.g., ServiceNow).
2. **Review**: Compliance team approves/rejects within SLA (e.g., 48 hours).
3. **Documentation**: Exemption logged with justification and timeline.
4. **Monitoring**: Automated alerts if exemption terms expire.

#### **4. Remediation Automation**
- **Critical Violations**: Auto-trigger incident responses (e.g., failover to compliant systems).
- **Medium/Low Violations**: Escalate to teams via Slack/email with deadlines.
- **Example Toolchain**:
  - **Detect**: Prometheus + Grafana alerts.
  - **Remediate**: Terraform scripts to auto-apply fixes.
  - **Audit**: Immutable logs in AWS CloudTrail or Datadog.

#### **5. Integration Patterns**
- **GRC Platforms**: Sync with tools like MetricStream or RSA Archer.
- **CI/CD**: Enforce compliance in build pipelines (e.g., GitHub Actions with OWASP checks).
- **SIEM**: Correlate violations with security events (e.g., Splunk, ELK Stack).

---

### **Related Patterns**
Consume or extend these complementary patterns for a robust compliance framework:

| **Pattern**                     | **Purpose**                                                                 | **Connection to Compliance Guidelines**                                                                 |
|----------------------------------|-----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| **[Policy as Code](pattern-policy-as-code)**        | Define governance policies in code (e.g., Open Policy Agent).            | Use **Compliance Guidelines** to translate policies into enforceable rules.                           |
| **[Audit Logging](pattern-audit-logging)**           | Capture immutable records of system changes.                              | Store violation events and remediation actions in the **Compliance Guidelines** audit trail.         |
| **[Secret Management](pattern-secret-management)** | Securely handle credentials/keys.                                         | Enforce encryption rules in **Compliance Guidelines** for sensitive data.                              |
| **[Event Sourcing](pattern-event-sourcing)**        | Track state changes via events.                                             | Log compliance rule violations as domain events for traceability.                                        |
| **[Dynamic Configuration](pattern-dynamic-config)** | Adjust rules at runtime (e.g., tiered access controls).                 | Update **Compliance Guidelines** dynamically via config services (e.g., Consul, etcd).                |

---
### **Anti-Patterns**
- **Static Rules**: Hardcoding rules without versioning or exemption support.
- **Manual Workarounds**: Bypassing automated checks (e.g., disabling validators).
- **Over-Automation**: Assuming all rules can be validated without human oversight.
- **Silos**: Isolating compliance teams from engineering teams for rule maintenance.

---
### **Example Workflow**
**Scenario**: Enforce **GDPR Data Minimization** for a customer portal.
1. **Define Guideline**:
   ```json
   {
     "name": "GDPR Data Minimization",
     "scope": [{ "system": "CustomerPortal", "dataDomain": "UserProfiles" }],
     "rules": [
       {
         "condition": { "field": "email", "operator": "contains", "value": "@unverified.email" },
         "severity": "high",
         "remediationSteps": [
           { "step": "Request verification", "owner": "CustomerSupport" }
         ]
       }
     ]
   }
   ```
2. **Enforce with Controls**:
   - **API Layer**: Add a validator to block unverified emails.
   - **Database**: Add a constraint or trigger to flag non-compliant records.
3. **Trigger Audits**:
   - Scheduled scan daily to check for unverified emails.
   - Real-time block on API calls with invalid emails.
4. **Handle Exemptions**:
   - Allow legacy users until migration (e.g., `validUntil: "2024-12-31"`).
5. **Report**:
   - Export violations to GDPR compliance dashboard monthly.

---
**Tools/Libraries**
- **Validation**: [Zod](https://github.com/colinhacks/zod), [Ajv](https://ajv.js.org/)
- **ORM Integration**: [Prisma](https://www.prisma.io/), [TypeORM](https://typeorm.io/)
- **GRC Platforms**: [ServiceNow GRC](https://www.servicenow.com/products/governance-risk-compliance.html), [RSA Archer](https://www.rsasecurity.com/en-us/solutions/governance-risk-compliance)
- **Automation**: [Terraform](https://www.terraform.io/), [Ansible](https://www.ansible.com/)