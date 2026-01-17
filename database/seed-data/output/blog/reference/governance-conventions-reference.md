# **[Pattern] Governance Conventions Reference Guide**

---

## **Overview**
Governance Conventions establish **standardized naming, tagging, and labeling rules** for datasets, models, APIs, and infrastructure to ensure **consistency, traceability, and compliance** across an organization. This pattern enforces **discoverability, versioning, and automated governance** by defining conventions for metadata, lineage, and access controls. Proper implementation reduces operational overhead, improves collaboration, and aligns with regulatory requirements (e.g., GDPR, CCPA).

Key benefits:
✔ **Reduced ambiguity** in resource identification
✔ **Automated compliance tracking** via metadata
✔ **Simplified auditing** through standardized tags
✔ **Interoperability** with governance frameworks (e.g., DAMA-DMBOK, OMDF)

---

## **Implementation Details**

### **1. Core Components**
Governance Conventions rely on the following **mandatory and optional** elements:

| **Component**               | **Description**                                                                 | **Example**                          |
|------------------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Resource Naming**          | Unique, descriptive, and versioned identifiers for datasets, models, etc.   | `finance_billing_tier_v2_2024_03`    |
| **Metadata Fields**          | Structured tags for lineage, ownership, sensitivity, and compliance.          | `"dataowner": "finance_team"`        |
| **Tagging Standard**         | Categorization system (e.g., business domain, data source, usage rights).    | `"source": "ERP", "purpose": "reporting"` |
| **Versioning**               | Semantic versioning or timestamp-based identifiers.                            | `v1.0.3` or `2024-05-15`             |
| **Access Controls**          | Role-based access (RBA) or attribute-based access (ABAC) policies.             | `"access": "read:engineering,write:data_owners"` |
| **Deprecation Policy**       | Rules for retiring obsolete resources (e.g., 12 months of inactivity).        | `"deprecated": true, "replacement": "new_model_v2"` |
| **Compliance Tags**          | Mapping to regulations (e.g., GDPR, HIPAA) or internal policies.               | `"compliance": ["GDPR", "CCPA"]`     |
| **Lineage Tracking**         | Recording transformations, dependencies, and lineage for auditability.        | `"depends_on": ["raw_sales_data", "inventory_db"]` |
| **Documentation Link**       | Reference to formal documentation (e.g., Confluence, Markdown).               | `"docs_url": "https://docs.example.com/ds123"` |

---

### **2. Schema Reference**
Governance Conventions adhere to a **standardized schema** for metadata. Below is the **minimal required schema**:

| **Field**               | **Type**       | **Description**                                                                 | **Required?** | **Example Values**                          |
|-------------------------|----------------|---------------------------------------------------------------------------------|---------------|----------------------------------------------|
| `resource_name`         | String         | Unique, human-readable identifier.                                             | ✅             | `customer_transactions_2023_q1`             |
| `version`               | String         | Semantic or timestamp-based version.                                           | ✅             | `v1.2.0` or `2023-01-15`                    |
| `domain`                | String         | Business domain (e.g., finance, marketing).                                   | ✅             | `finance`, `hr`                              |
| `data_owner`            | String         | Team/role responsible for governance.                                           | ✅             | `"finance_team"`                             |
| `created_at`            | Timestamp      | Date/time of resource creation.                                                 | ✅             | `2024-05-20T14:30:00Z`                     |
| `updated_at`            | Timestamp      | Last modification timestamp.                                                    | ✅             | `2024-06-05T09:15:00Z`                     |
| `sensitivity`           | Enum           | Classification (PII, Public, Internal, etc.).                                  | ❌             | `PII`, `restricted`                         |
| `purpose`               | List[String]   | Intended use cases (e.g., analytics, reporting).                               | ❌             | `["reporting", "analytics"]`                |
| `source_system`         | String         | Original data source (e.g., Salesforce, ERP).                                 | ❌             | `salesforce`, `sap`                          |
| `access_policy`         | JSON           | Role-based or attribute-based access rules.                                    | ❌             | `{"roles": ["data_scientist"], "abac": {"team": "analytics"}}` |
| `deprecated`            | Boolean        | Flag if resource is no longer supported.                                       | ❌             | `true`                                       |
| `compliance`            | List[String]   | Relevant regulations (e.g., GDPR, HIPAA).                                     | ❌             | `["GDPR", "CCPA"]`                          |
| `lineage`               | List[JSON]     | Dependency graph (input/output resources).                                     | ❌             | `[{"input": "raw_orders", "transform": "ETL"}]` |
| `documentation`         | String         | Link to formal docs.                                                            | ❌             | `https://docs.example.com/model_123`         |

---
**Note:** Extend fields as needed for domain-specific requirements (e.g., healthcare datasets may require `hitech_compliance`).

---

## **Query Examples**
Governance Conventions enable **efficient querying** of resources via metadata. Below are common **SQL, Python (Pandas), and API query patterns**:

---

### **1. Find All PII-Classified Datasets**
**SQL (PostgreSQL):**
```sql
SELECT *
FROM resources
WHERE sensitivity = 'PII'
AND domain IN ('hr', 'finance');
```

**Python (Pandas):**
```python
import pandas as pd
df = pd.read_csv("resources_metadata.csv")
pii_datasets = df[(df["sensitivity"] == "PII") &
                  (df["domain"].isin(["hr", "finance"]))]
print(pii_datasets)
```

**API (REST):**
```http
GET /api/v1/resources?sensitivity=PII&domains=hr,finance
```

---

### **2. List Deprecated Resources with Replacements**
**SQL:**
```sql
SELECT resource_name, version, deprecated, replacement
FROM resources
WHERE deprecated = true
ORDER BY updated_at DESC;
```

**Python:**
```python
deprecated = df[df["deprecated"] == True].sort_values("updated_at", ascending=False)
print(deprecated[["resource_name", "version", "replacement"]])
```

**API:**
```http
GET /api/v1/resources?deprecated=true
```

---

### **3. Find Resources Modified in the Last 30 Days**
**SQL:**
```sql
SELECT *
FROM resources
WHERE updated_at > CURRENT_DATE - INTERVAL '30 days';
```

**Python:**
```python
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=30)
recent_updates = df[df["updated_at"] > cutoff.strftime("%Y-%m-%d %H:%M:%S")]
```

**API:**
```http
GET /api/v1/resources?updated_after=2024-06-20
```

---

### **4. Retrieve Lineage for a Specific Dataset**
**SQL:**
```sql
SELECT resource_name, version, lineage
FROM resources
WHERE resource_name = 'customer_transactions';
```

**Python:**
```python
lineage_data = df[df["resource_name"] == "customer_transactions"]["lineage"].values[0]
```

**API:**
```http
GET /api/v1/resources/customer_transactions/lineage
```

---

## **Tagging Conventions**
Governance Conventions require **structured tagging** for categorization. Use the following **tag prefixes** for consistency:

| **Tag Prefix** | **Purpose**                          | **Example Tags**                     |
|----------------|--------------------------------------|--------------------------------------|
| `domain:`      | Business domain.                     | `domain:finance`, `domain:marketing` |
| `source:`      | Data source system.                  | `source:erp`, `source:api`           |
| `purpose:`     | Use case.                           | `purpose:reporting`, `purpose:ml`    |
| `compliance:`  | Regulatory tags.                     | `compliance:gdp`, `compliance:hipaa` |
| `access:`      | Access control type.                 | `access:rba`, `access:abac`          |
| `sensitivity:` | Data classification.                | `sensitivity:pii`, `sensitivity:internal` |
| `status:`      | Lifecycle stage.                     | `status:active`, `status:deprecated` |

**Prohibited Tags:**
❌ `tag:important` (vague)
❌ `tag:new` (non-standardized)

---

## **Versioning Rules**
Enforce **semantic versioning** (`MAJOR.MINOR.PATCH`) or **timestamp-based** naming:

| **Scenario**               | **Versioning Example**               | **Description**                                  |
|-----------------------------|--------------------------------------|--------------------------------------------------|
| **Breaking Changes**        | `v2.0.0`                             | New major release with backward-incompatible API.|
| **Non-Breaking Additions**  | `v1.1.0`                             | New features without breaking existing code.     |
| **Bug Fixes**               | `v1.0.2`                             | Patches to previous versions.                    |
| **Timestamp-Based**         | `2024-06-01`                         | Use for non-semantic datasets (e.g., logs).      |

**Naming Template:**
```
{resource}_{domain}_{purpose}_{version}_{timestamp}
```
**Example:**
`customer_orders_finance_reporting_v1.0.3_20240615`

---

## **Access Control Policies**
Governance Conventions integrate with **RBAC (Role-Based Access Control)** or **ABAC (Attribute-Based Access Control)**. Example policies:

### **RBAC Example**
| **Role**               | **Access Rights**                          |
|------------------------|--------------------------------------------|
| `data_scientist`       | `read:*, execute:models, write:drafts`    |
| `data_analyst`         | `read:*, query:datasets`                  |
| `compliance_officer`   | `read:*, audit:metadata`                  |
| `engineering`          | `read:*, write:*, deploy:models`         |

### **ABAC Example (Python-like Pseudocode)**
```python
def can_access(resource, user):
    if user.team == "engineering":
        return True
    if user.role == "data_scientist" and resource.type == "model":
        return True
    if user.role == "auditor" and resource.sensitivity == "PII":
        return False  # Explicit deny
    return False
```

---

## **Deprecation Workflow**
1. **Identify**: Tag deprecated resources with `deprecated: true`.
2. **Notify**: Send email to `data_owner` with replacement info.
3. **Retire**: Remove access after `deprecation_period` (e.g., 12 months).
4. **Archive**: Store in long-term storage with `access: read-only`.

**Example Deprecation Tag:**
```json
{
  "resource_name": "legacy_customer_db",
  "deprecated": true,
  "replacement": "customer_db_v2_2024",
  "deprecation_date": "2024-12-31",
  "deprecation_reason": "Migrated to new schema"
}
```

---

## **Automation & Tooling**
Governance Conventions should be **enforced via automation**:

| **Tool/Framework**       | **Purpose**                                  | **Example Integration**                     |
|--------------------------|----------------------------------------------|----------------------------------------------|
| **OpenLineage**          | Lineage tracking.                            | Annotate Spark/Flask workflows.              |
| **Great Expectations**   | Data validation + metadata tagging.          | Auto-tag failing tests.                     |
| **Azure Purview / AWS Glue** | Governance catalog.                     | Enforce naming/policy rules.                |
| **Terraform**            | Infrastructure-as-code governance.          | Tag resources with `domain:finance`.       |
| **Custom Scripts**       | Ad-hoc validation.                          | Python regex to validate `resource_name`.   |

---
**Example Terraform Tagging:**
```hcl
resource "aws_s3_bucket" "finance_data" {
  bucket = "finance-data-v1"
  tags = {
    domain       = "finance"
    sensitivity  = "internal"
    data_owner   = "finance_team"
    compliance   = "gdp"
  }
}
```

---

## **Related Patterns**
Governance Conventions interact with other patterns for **end-to-end governance**:

| **Pattern**               | **Description**                                                                 | **Synergy with Governance Conventions**                          |
|---------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------|
| **[Data Mesh](https://docs.data-mesh.com/)** | Decentralized data ownership.                                                | Use `domain:` tags to align with domain teams.                   |
| **[Data Lakehouse](https://delta.io/)**        | Unified storage + governance.                                                | Enforce naming in Delta Lake tables.                             |
| **[Observability](https://www.datastack.ai/)** | Monitoring for data quality.                                                 | Track `sensitivity` and `compliance` in alerts.                 |
| **[Security Posture Management](https://www.gartner.com/)** | Compliance auditing.                                                       | Sync `compliance` tags with SPM tools.                           |
| **[Data Catalog](https://en.wikipedia.org/wiki/Data_catalog)** | Centralized metadata repository.                                             | Population source for Governance Conventions metadata.          |
| **[Feature Store](https://www.feature-labs.com/)** | Managed feature serving.                                                    | Tag features with `purpose:ml` and `sensitivity`.                |

---

## **Best Practices**
1. **Standardize Early**: Enforce conventions during **resource creation**, not retroactively.
2. **Automate Validation**: Use CI/CD to reject non-compliant resources.
   - **Example**: Reject S3 buckets without `domain:` tag.
3. **Document Exceptions**: Log deviations (e.g., `legacy_system: true`).
4. **Audit Regularly**: Query for orphaned (`data_owner: null`) or deprecated resources.
5. **Train Teams**: Include conventions in onboarding docs (e.g., Confluence wiki).

---
**Anti-Patterns to Avoid:**
❌ **Ad-Hoc Naming**: `dataset_123` → Use `customers_payment_v1_2024`.
❌ **Over-Tagging**: Add unnecessary tags (e.g., `tag:quick`).
❌ **Ignoring Deprecation**: Keep deprecated resources accessible indefinitely.

---

## **Troubleshooting**
| **Issue**                          | **Cause**                                | **Solution**                                  |
|------------------------------------|------------------------------------------|-----------------------------------------------|
| **Resource not found in queries**  | Incorrect `domain:` tag.                | Verify tag consistency in metadata.           |
| **Access denied**                  | Missing `access_policy`.                | Assign roles via RBAC/ABAC.                   |
| **Lineage gaps**                   | Missing `lineage` field.                | Enable OpenLineage or manual documentation.    |
| **Compliance violations**          | Missing `compliance` tags.             | Audit with SPM tools.                         |
| **Version conflicts**              | Non-semantic versions (e.g., `v2`).     | Stick to `MAJOR.MINOR.PATCH` or timestamps.   |

---

## **Example Workflow: Onboarding a New Dataset**
1. **Create Resource**:
   ```json
   {
     "resource_name": "product_reviews_v1",
     "domain": "ecommerce",
     "data_owner": "product_team",
     "sensitivity": "public",
     "purpose": ["analytics", "feedback"],
     "source_system": "web_app",
     "access_policy": {"roles": ["data_analyst", "marketing"]},
     "lineage": [{"input": "raw_reviews"}]
   }
   ```
2. **Deploy with Automation**:
   - Terraform tags the S3 bucket.
   - Great Expectations tags validation results.
3. **Query for Usage**:
   ```sql
   SELECT * FROM resources
   WHERE domain = 'ecommerce' AND purpose = 'analytics';
   ```
4. **Rotate Version**:
   ```json
   {
     "resource_name": "product_reviews_v2",
     "version": "v2.0.0",
     "deprecated": true,
     "replacement": "product_reviews_v1"
   }
   ```

---
## **Further Reading**
- [DAMA-DMBOK Governance Principles](https://dama.org/)
- [OMDF Governance Framework](https://omdf.io/)
- [OpenLineage Specification](https://github.com/OpenLineage/OpenLineage)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework) (for compliance alignment)

---
**Last Updated:** [Date]
**Maintainer:** [Team/Contact]