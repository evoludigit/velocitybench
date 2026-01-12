# **[Pattern] Compliance Conventions Reference Guide**
*Structured guidelines for consistent data representation in regulatory contexts*

---

## **Overview**
The **Compliance Conventions** pattern standardizes how organizations encode and validate data to meet regulatory, industry, or internal governance requirements. This pattern ensures traceability, auditability, and interoperability of data across systems—critical for sectors like healthcare (HIPAA), finance (SOX), and cybersecurity (NIST). By defining reusable conventions for metadata, data formats, and validation rules, teams reduce ambiguities and streamline compliance workflows.

Key benefits:
- **Reduced operational risk** via automated validation checks.
- **Faster audits** with standardized evidence artifacts.
- **Scalability** through reusable schema templates for evolving regulations.

---

## **Implementation Details**

### **1. Core Components**
| Component               | Description                                                                                     | Example Use Cases                                                                 |
|-------------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **Data Categories**     | Predefined taxonomies (e.g., `PII`, `Financial`, `AuditTrail`) to classify data sensitivity.   | Masking PII in logs, flagging SOX-relevant transactions.                           |
| **Metadata Tags**       | Key-value pairs tied to data (e.g., `compliance_rule = "GDPR_ART_30"`) for quick filtering.   | Querying all dataset logs tagged with `NIST_800-171`.                              |
| **Validation Rules**    | Regex, fixed schemas (JSON, XML), or business logic to enforce compliance.                     | Validating CC numbers against PCI DSS regex; enforcing GDPR retention periods.      |
| **Evidence Artifacts**  | Immutable logs or hashes of actions (e.g., access control list changes) for audit trails.      | Storing SHA-256 hashes of dataset accesses for SOX compliance.                    |
| **Metadata Propagation**| Rules for propagating compliance tags across systems (e.g., databases → APIs → dashboards).   | Tagging a database table in PostgreSQL automatically tags the connected Spark DataFrame. |

---

### **2. Data Classification Schema**
Classify data using these standardized categories. **Mandatory** fields are marked with `*`.

| Field              | Type       | Description                                                                               | Required | Example Values                     |
|--------------------|------------|-------------------------------------------------------------------------------------------|----------|-------------------------------------|
| `compliance_domain` | Enum       | Regulation or framework (e.g., `GDPR`, `HIPAA`, `SOX`, `NIST`).                          | Yes       | `HIPAA_501`, `GDPR_ART_30`         |
| `data_type`        | Enum       | Data category (e.g., `PII`, `Financial`, `Audit`, `Healthcare`).                           | Yes       | `Healthcare.PatientRecord`          |
| `sensitivity_level`| Enum       | Severity of exposure risk (e.g., `High`, `Medium`, `Low`).                                | Yes       | `High`                              |
| `retention_policy` | String     | Compliance-specific retention duration (e.g., `7_years`).                                  | Conditional| `GDPR_30_years`, `HIPAA_6_years`    |
| `access_control`   | String     | Permissions required (e.g., `role_based`, `attribute_based`).                             | Yes       | `role_based`                        |
| `evidence_requirement*` | Boolean   | Whether evidence artifacts must be generated during lifecycle events.                   | Yes       | `true`/`false`                      |
| `custom_tags`      | Array[String]| User-defined tags for internal workflows (e.g., `["deprecated"]`).                        | No        | `["legacy_system", "archived"]`    |

---

### **3. Validation Rule Syntax**
Apply rules using a **YAML-like schema** (supporting regex, fixed patterns, or custom scripts).

#### **Simple Regex Example**
```yaml
# Validate a UK National Insurance Number (NINO)
rules:
  - name: "NINO_format"
    type: "regex"
    pattern: "^([A-Z]{2}\d{2}[A-Z]{2}\d{2}[A-Z]{2})$"
    error_message: "Invalid NINO format. Must match AA99AA99AA format."
```

#### **Nested Schema Validation (JSON)**
```yaml
# Validate a GDPR-consent log structure
rules:
  - name: "consent_log_schema"
    type: "json_schema"
    schema:
      type: "object"
      required: ["timestamp", "subject_id", "consent_id"]
      properties:
        timestamp:
          type: "string"
          format: "date-time"
        subject_id:
          type: "string"
          pattern: "^SUB-[A-Z0-9]{8}$"
```

#### **Custom Validation (Python)**
```yaml
# Validate a SOX-relevant journal entry
rules:
  - name: "sox_journal_entry"
    type: "custom"
    script: |
      def validate(entry):
          if entry["amount"] < 0:
              raise ValueError("SOX requires non-negative journal entries.")
      validate(entry)
```

---

## **4. Implementation Steps**
### **Step 1: Define Compliance Domains**
Map your organization’s relevant regulations to the `compliance_domain` enum.
**Example:**
```python
# Python snippet to extend the enum
from enum import Enum
class ComplianceDomain(Enum):
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    SOX = "SOX"
    NIST_800_171 = "NIST_800_171"
```

### **Step 2: Apply Metadata to Data**
Tag data sources (databases, APIs, files) with compliance attributes.
**Example (PostgreSQL):**
```sql
-- Add compliance metadata to a table
ALTER TABLE patients ADD COLUMN compliance_metadata JSONB;
UPDATE patients SET compliance_metadata =
  '{
    "compliance_domain": "HIPAA",
    "data_type": "Healthcare.PatientRecord",
    "retention_policy": "HIPAA_6_years",
    "access_control": "role_based"
  }';
```

### **Step 3: Enforce Validation**
Integrate validation into pipelines (e.g., Kafka, Airflow) or database triggers.
**Example (Kafka Schema Registry):**
```json
// Avro schema for a GDPR consent log
{
  "type": "record",
  "name": "GDPRConsentLog",
  "fields": [
    {"name": "timestamp", "type": "string"},
    {"name": "subject_id", "type": "string"},
    {"name": "consent_id", "type": "string"},
    {
      "name": "compliance_metadata",
      "type": {
        "type": "map",
        "values": "string"
      }
    }
  ]
}
```

### **Step 4: Generate Evidence Artifacts**
Automate logging of lifecycle events (e.g., access, modifications).
**Example (Python + Pandas):**
```python
import pandas as pd
from datetime import datetime

# Simulate logging dataset access
def log_access(df: pd.DataFrame, user: str):
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "access",
        "user": user,
        "dataset": df.name,
        "metadata": df.compliance_metadata.to_dict()
    }
    # Store in a compliance-evidence database (e.g., Elasticsearch)
    evidence_db.index(event, index="audit_logs")

log_access(patients_df, "auditor_42")
```

---

## **5. Query Examples**
### **Query 1: Find All GDPR-Relevant Data**
```sql
-- SQL (PostgreSQL)
SELECT * FROM datasets
WHERE compliance_metadata->>'compliance_domain' = 'GDPR';
```

### **Query 2: Extract SOX-Exempt Transactions**
```python
# Python + Pandas
sox_exempt = df[
    (~df["compliance_metadata"].apply(lambda x: x.get("compliance_domain") == "SOX"))
    & (df["amount"] < 1_000_000)  # Internal threshold
]
```

### **Query 3: Audit Access to High-Sensitivity Data**
```json
// Elasticsearch query for audit logs
{
  "query": {
    "bool": {
      "must": [
        { "term": { "metadata.compliance_domain": "GDPR" } },
        { "term": { "metadata.sensitivity_level": "High" } }
      ]
    }
  }
}
```

---

## **6. Common Pitfalls & Mitigations**
| Pitfall                                  | Mitigation Strategy                                                                 |
|------------------------------------------|------------------------------------------------------------------------------------|
| **Overly restrictive rules**             | Start with a "minimum viable compliance" set; refine iteratively.                |
| **Metadata drift**                      | Automate metadata propagation with tools like OpenMetadata or Collibra.            |
| **False positives in validation**       | Use weighted scoring for rules (e.g., `criticality: "high"`).                     |
| **Performance overhead**                 | Cache validation results; batch-process non-critical validations.                  |
| **Ignoring dynamic regulations**         | Subscribe to regulatory feeds (e.g., GDPR updates via [EU Official Journal](https://eur-lex.europa.eu/)). |

---

## **7. Related Patterns**
| Pattern Name               | Purpose                                                                           | Use When...                                                                       |
|----------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| **[Data Lineage]**         | Track how data moves through pipelines.                                           | Need to justify compliance decisions (e.g., GDPR Article 30).                     |
| **[Dynamic Data Masking]**| Automatically redact sensitive fields in queries.                                 | Querying compliance-tagged datasets in production.                               |
| **[Access Control Lists]**| Enforce role-based or attribute-based access.                                   | Restricting SOX-sensitive data to approved roles.                                 |
| **[Audit Event Streaming]**| Real-time logging of compliance-critical actions.                                | Monitoring live system changes for NIST 800-171 compliance.                      |
| **[Compliance Dashboard]**| Visualize compliance status across systems.                                       | Reporting to auditors or leadership (e.g., "95% of datasets comply with GDPR").   |

---
## **8. Tools & Integrations**
| Tool Category       | Recommended Tools                                                                 |
|---------------------|-----------------------------------------------------------------------------------|
| **Metadata Catalog**| [Collibra](https://www.collibra.com/), [Alation](https://www.alityo.com/), [Amundsen](https://github.com/lyft/amundsen) |
| **Validation**      | [Great Expectations](https://greatexpectations.io/), [Deequ](https://aws.amazon.com/blogs/big-data/deequ-validate-your-data-at-scale/) |
| **Evidence Storage**| [Elasticsearch](https://www.elastic.co/), [Druid](https://druid.apache.org/), [AWS Audit Manager](https://aws.amazon.com/audit-manager/) |
| **Schema Enforcement**| [Apache Avro](https://avro.apache.org/), [Protocol Buffers](https://developers.google.com/protocol-buffers), [JSON Schema](https://json-schema.org/) |
| **Automation**      | [Apache Airflow](https://airflow.apache.org/), [Prefect](https://www.prefect.io/), [Dagster](https://dagster.io/) |

---
**Last Updated:** [MM/YYYY]
**Owner:** [Team/Contact]