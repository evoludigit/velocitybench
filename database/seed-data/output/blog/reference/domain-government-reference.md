**[Pattern] Government Domain Patterns Reference Guide**

---

### **Overview**
The **Government Domain Patterns** guide outlines standardized architectural and design patterns tailored for government systems. These patterns address key requirements such as **data sovereignty, compliance (GDPR, FOIA), auditability, interoperability, and citizen-centric service delivery**. This guide provides implementation details, best practices, and anti-patterns to ensure scalable, secure, and maintainable solutions for public sector applications.

The pattern focuses on:
- **Structured Data Governance**: Ensuring data is categorized, annotated, and controlled per legal standards.
- **Citizen-Centric APIs**: Standardized endpoints for government services (e.g., tax filings, permit applications).
- **Role-Based Access Control (RBAC)**: Fine-grained permissions for officials (e.g., mayors, administrators).
- **Audit Trails**: Immutable logs for all system changes (critical for transparency).
- **Interoperability**: Seamless data exchange between agencies (e.g., via FHIR, HL7, or proprietary schemas).

---

### **Core Schema Reference**

| **Category**               | **Pattern Name**               | **Purpose**                                                                 | **Key Attributes**                                                                 | **Example Use Case**                          |
|----------------------------|--------------------------------|-----------------------------------------------------------------------------|-----------------------------------------------------------------------------------|-----------------------------------------------|
| **Data Governance**        | **Metadata Catalog**           | Centralized registry of government datasets (e.g., tax records, voter rolls). | `dataset_id`, `owner_agency`, `classification_level`, `retention_policy`, `metadata_schema` | Classifying a dataset as *"Sensitive"* for restricted access. |
| **Citizen Services**       | **Unified Identity Service**   | Single Sign-On (SSO) for citizens using government portals.                  | `auth_provider` (e.g., "ID.me"), `mfa_requirement`, `consent_management`          | Logging in via a citizen portal with biometric verification. |
| **Audit & Compliance**     | **Event Sourcing Log**         | Immutable record of all system actions (FOIA/audit compliance).             | `event_type`, `actor_role`, `timestamp`, `data_modified`, `hash_verify`          | Tracking a permit application modification.      |
| **Interoperability**       | **Federated Data Exchange**    | Secure cross-agency data sharing (e.g., health records, land registries).    | `source_agency`, `destination_agency`, `access_control_policy`, `transform_rules` | Sharing COVID-19 case data between health departments. |
| **RBAC**                   | **Role Hierarchy Tree**        | Define nested roles (e.g., "City Clerk" → "Permit Officer").                 | `role_id`, `parent_role`, `permissions`, `inheritance_flag`                      | Granting a junior officer "read-only" access.   |
| **Citizen Portals**        | **Pre-Approved Workflows**     | Standardized service requests (e.g., business licenses).                    | `workflow_id`, `submission_fields`, `approval_chain`, `compliance_checks`         | Automating a business license renewal process. |

---

### **Implementation Details**

#### **1. Metadata Catalog**
- **Structured Annotations**: Use ontologies (e.g., [Data.gov Schema](https://schema.data.gov/)) to tag datasets.
  Example annotation:
  ```json
  {
    "dataset_id": "tax_2023",
    "classification": "Public",
    "retention_policy": "7_years",
    "schema_reference": "https://tax.schema.data.gov/2023"
  }
  ```
- **Access Control**: Enforce via **Attribute-Based Access Control (ABAC)** tied to `classification_level`.
- **Anti-Pattern**: Avoid hardcoding sensitive data paths; use environment variables for compliance.

#### **2. Unified Identity Service**
- **Supported Providers**: Integrate with:
  - **Government-issued IDs** (e.g., DMV, passport via [ID.me](https://www.id.me/)).
  - **Biometrics** (fingerprint/FaceID for high-risk actions).
- **Consent Management**: Store citizen consent in a **blockchain-ledger** for FOIA compliance.
  Example API call:
  ```http
  POST /api/auth/consent
  {
    "citizen_id": "cit_12345",
    "service": "tax_filing",
    "consent_timestamp": "2024-05-20T12:00:00Z",
    "digital_signature": "base64_encoded"
  }
  ```

#### **3. Event Sourcing Log**
- **Schema**:
  | Field               | Type         | Description                                  |
  |---------------------|--------------|----------------------------------------------|
  | `event_id`          | UUID         | Unique identifier                            |
  | `timestamp`         | ISO 8601     | When the event occurred                     |
  | `actor`             | JSON         | `{ role: "PermitOfficer", agency: "CityHall" }` |
  | `action`            | Enum         | `create`, `modify`, `delete`, `approve`     |
  | `data_hash`         | SHA-256      | Cryptographic proof of data integrity       |
- **Querying Logs**:
  ```sql
  -- Find all events for a permit application
  SELECT * FROM event_log
  WHERE data_hash IN (SELECT hash FROM permit_data WHERE permit_id = 'perm_98765')
  ORDER BY timestamp DESC;
  ```

#### **4. Federated Data Exchange**
- **Security Layer**:
  - **Data Masking**: Strip PII unless explicitly requested (via `access_control_policy`).
  - **Zero-Trust Model**: Require mutual TLS for inter-agency requests.
- **Example Integration (HL7 FHIR)**:
  ```http
  GET /FHIR/Patient?identifier=SSN:123-45-6789
  Headers: X-Agency: "HealthDept", X-Requestor: "SocialServices"
  ```

#### **5. Role Hierarchy Tree**
- **Implementation**:
  ```graphql
  type Role {
    id: ID!
    name: String!
    parent: Role
    permissions: [Permission!]!
  }

  type Permission {
    resource: String!
    action: String!  # e.g., "READ", "APPROVE"
  }
  ```
- **Query Example**:
  ```graphql
  query {
    role(id: "perm_officer_1") {
      name
      permissions {
        resource
        action
      }
    }
  }
  ```

#### **6. Pre-Approved Workflows**
- **State Machine Design**:
  ```mermaid
  flowchart TD
    A[Submitted] -->|citizen| B[Under Review]
    B -->|officer| C[Approved]
    C -->|citizen| D[Completed]
    subgraph "Validation Checks"
      B -->|fail| E[Rejected\n(FOIA Logged)]
    end
  ```
- **Automation Rules**:
  - Trigger `fraud_check` if `submission_fields.submitter = "REPEAT_LAST_YEAR"`.
  - Send `compliance_notice` if `tax_filing.missing_deductions > 0`.

---

### **Query Examples**

#### **1. Querying Citizen Consents**
```graphql
query {
  citizen(id: "cit_12345") {
    consentHistory {
      service
      timestamp
      revoked
    }
  }
}
```

#### **2. Checking Audit Logs for Data Breaches**
```sql
-- Alert if an unauthorized DELETE occurs
SELECT actor.role, event_id, data_hash
FROM event_log
WHERE action = 'DELETE'
  AND actor.role NOT IN ('DataCustodian', 'ComplianceOfficer');
```

#### **3. Validating Federated Data Share**
```http
POST /api/agency/share/validate
{
  "source_agency": "HealthDept",
  "destination_agency": "SocialServices",
  "data_payload": "base64_encoded",
  "signature": "RS256_signature"
}
```

---

### **Best Practices & Pitfalls**

#### **Best Practices**
✅ **Compliance by Design**:
   - Embed **GDPR/FOIA checks** in the data model (e.g., `right_to_erasure` flag).
   - Use **automated classification tools** (e.g., Amazon Macie) for sensitive data.

✅ **Performance**:
   - Cache **frequent citizen queries** (e.g., tax refund status) with a TTL of 24 hours.
   - Partition **event logs** by agency for parallel queries.

✅ **Interoperability**:
   - Publish **API schemas** as open standards (e.g., [Schema.org](https://schema.org/) for citizen data).

#### **Common Pitfalls**
❌ **Overly Complex RBAC**:
   - **Fix**: Limit nested roles to **3 levels deep** (e.g., `Mayor` → `DepartmentHead` → `Officer`).

❌ **Ignoring Data Sovereignty**:
   - **Fix**: Enforce **data residency laws** (e.g., store EU citizen data in EU DCs).

❌ **Lack of Audit Trail for AI Decisions**:
   - **Fix**: Log **AI model outputs** (e.g., "Fraud Score = 0.85") as actionable events.

---

### **Related Patterns**
| **Pattern Name**               | **Relation to Government Domain**                                                                 | **Reference**                                  |
|----------------------------------|---------------------------------------------------------------------------------------------------|------------------------------------------------|
| **Event-Driven Architecture**    | Enables real-time citizen notifications (e.g., permit approval alerts).                            | [EventStorming](https://eventstorming.com/)    |
| **Policy-as-Code**              | Automate compliance rules (e.g., "No approvals after 5 PM").                                       | [Open Policy Agent](https://www.openpolicyagent.org/) |
| **Citizen Data Portability**    | Allow citizens to export their data (GDPR "Right to Data Portability").                           | [GA4GH](https://ga4gh.org/)                   |
| **Multi-Tenancy for Agencies**   | Isolate agency data while sharing infrastructure (e.g., AWS Organizations).                        | [AWS Multi-Tenant Architecture](https://aws.amazon.com/solutions/patterns/multi-tenant-saas/) |
| **Blockchain for Voting**       | Immutable audit logs for election systems.                                                          | [Hyperledger Fabric](https://www.hyperledger.org/) |

---

### **Further Reading**
- [U.S. Digital Services Playbook](https://playbook.cio.gov/)
- [ISO/IEC 27001](https://www.iso.org/standard/77504.html) (Information Security Management)
- [Data.gov API Standards](https://developer.data.gov/)

---
**Last Updated**: `{{DATE}}`
**Version**: `1.3`