---
**[Pattern] Privacy Standards Reference Guide**
*Ensure compliance, transparency, and user control in data handling.*

---

### **Overview**
The **Privacy Standards** pattern provides a structured framework for organizations to adhere to global privacy regulations (e.g., GDPR, CCPA) while implementing best practices for data collection, processing, storage, and subject rights. This guide outlines the core components, schema requirements, query patterns, and related patterns to operationalize privacy compliance in technical systems.

---

## **1. Key Concepts**
### **Core Principles**
| Term               | Definition                                                                                     |
|--------------------|---------------------------------------------------------------------------------------------|
| **Data Subject**   | An individual whose personal data is collected, stored, or processed.                          |
| **Privacy Rights** | User entitlements (e.g., access, deletion, portability) defined by regulations.             |
| **Data Processing**| Any action performed on personal data (e.g., collection, anonymization, sharing).             |
| **Consent**        | Explicit or implied affirmation by a subject for data processing.                              |
| **Pseudonymization**| Processing personal data in a way that renders it unlinkable to subjects without additional info. |

### **Regulatory Alignment**
- **GDPR (EU)**: Focuses on consent, data minimization, and subject rights.
- **CCPA (US)**: Grants California residents rights over their data and opt-out mechanisms.
- **LPD (Brazil)**: Similar to GDPR, with additional local provisions.

---

## **2. Schema Reference**
The **Privacy Standards** pattern relies on the following schema tables. All fields are **mandatory** unless noted.

| Table               | Fields                                                                 | Data Type       | Description                                                                                     |
|---------------------|-------------------------------------------------------------------------|-----------------|-------------------------------------------------------------------------------------------------|
| **`data_subjects`** | `id`, `first_name`, `last_name`, `email`, `created_at`                 | UUID, String    | Unique identifiers and contact details for individuals.                                           |
| **`privacy_rights`**| `id`, `subject_id`, `type` (e.g., `access`, `deletion`), `status` (e.g., `granted`, `pending`) | UUID, Enum, Enum | Tracks user-granted rights and their resolution status.                                          |
| **`data_processing`** | `id`, `subject_id`, `purpose` (e.g., `marketing`, `analytics`), `consent_status`, `legal_basis` (e.g., `legitimate_interest`, `contract`) | UUID, String, Enum, Enum | Records why and how data is processed.                                                          |
| **`processing_actions`** | `id`, `processing_id`, `action` (e.g., `collect`, `share`), `timestamp`, `data_masked` (boolean) | UUID, Enum, Timestamp, Boolean | Logs individual data handling operations with details on pseudonymization.                    |
| **`consent_records`** | `id`, `subject_id`, `purpose`, `consent_version`, `expiry_date`, `ip_address` (optional) | UUID, String, Version, Date, IP | Stores consent statements with version tracking and opt-out capabilities.                      |
| **`regulatory_compliance`** | `id`, `standard` (e.g., `GDPR`, `CCPA`), `audit_logs` (JSON array), `last_compliance_date` | UUID, Enum, JSON, Date | Maps compliance efforts to regulations and maintains audit trails.                             |

---

## **3. Query Examples**
### **3.1. Retrieve User Privacy Rights**
*Query all privacy rights granted to a subject, ordered by status.*

```sql
SELECT
    p.id,
    p.type,
    p.status,
    p.created_at
FROM
    privacy_rights p
WHERE
    p.subject_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY
    p.status, p.created_at DESC;
```

**Output Fields**:
- `id`, `type`, `status`, `created_at`

---

### **3.2. Audit Data Processing for GDPR Compliance**
*List all processing actions for a subject, filtering for GDPR-relevant purposes.*

```sql
SELECT
    d.id,
    d.purpose,
    d.legal_basis,
    pa.action,
    pa.timestamp
FROM
    data_processing d
JOIN
    processing_actions pa ON d.id = pa.processing_id
WHERE
    d.subject_id = '550e8400-e29b-41d4-a716-446655440000'
    AND d.legal_basis = 'legitimate_interest'
    AND pa.data_masked = TRUE;
```

---

### **3.3. Check Consent Validity**
*Verify if a subject’s consent for "analytics" is still active.*

```sql
SELECT
    c.id,
    c.consent_version,
    c.expiry_date,
    c.purpose
FROM
    consent_records c
WHERE
    c.subject_id = '550e8400-e29b-41d4-a716-446655440000'
    AND c.purpose = 'analytics'
    AND c.expiry_date >= CURRENT_DATE;
```

---

### **3.4. Generate CCPA Opt-Out Report**
*Retrieve all records linked to a subject for potential CCPA opt-out requests.*

```sql
SELECT
    ds.id,
    ds.email,
    dp.purpose,
    pa.action
FROM
    data_subjects ds
JOIN
    data_processing dp ON ds.id = dp.subject_id
JOIN
    processing_actions pa ON dp.id = pa.processing_id
WHERE
    ds.id = '550e8400-e29b-41d4-a716-446655440000'
    AND pa.timestamp >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR);
```

---

## **4. Implementation Steps**
### **4.1. Data Collection**
- **Pseudonymize data** during ingestion using UUIDs or hashing.
- **Log collection events** in `processing_actions` with `action = 'collect'`.

### **4.2. Subject Rights Management**
- **Expose an API endpoint** `/privacy/rights` to process:
  - Access requests (`type = access`).
  - Deletion requests (`type = deletion`).
- **Update `privacy_rights` status** to `granted` or `denied` upon resolution.

### **4.3. Consent Tracking**
- **Implement a consent management system** (CMS) to:
  - Store consent versions in `consent_records`.
  - Automatically expire consents on `expiry_date`.
- **Trigger audits** when consents are revoked or updated.

### **4.4. Compliance Monitoring**
- **Schedule nightly jobs** to:
  - Check `consent_records` for expired consents.
  - Update `regulatory_compliance` with audit logs.
- **Generate reports** for regulators via:
  ```sql
  SELECT
      rc.standard,
      COUNT(*) AS action_count,
      MAX(pa.timestamp) AS last_action
  FROM
      processing_actions pa
  JOIN
      data_processing dp ON pa.processing_id = dp.id
  JOIN
      regulatory_compliance rc ON dp.legal_basis = rc.standard
  GROUP BY
      rc.standard;
  ```

---

## **5. Error Handling & Edge Cases**
| Scenario                          | Solution                                                                                     |
|-----------------------------------|---------------------------------------------------------------------------------------------|
| **Missing consent**              | Default to `legal_basis = 'legitimate_interest'` if consent is not recorded.                 |
| **Subject deletion request**     | Soft-delete data in `processing_actions` with `action = 'delete'` and mark `data_masked = TRUE`. |
| **Partial data access request**   | Return only the subject’s `first_name`, `email`, and `privacy_rights` via API.             |
| **Regulatory updates**            | Version `consent_records` and `regulatory_compliance` to reflect new standards.              |

---

## **6. Related Patterns**
| Pattern                        | Description                                                                                     |
|--------------------------------|---------------------------------------------------------------------------------------------|
| **[Data Encryption]**          | Encrypts personal data at rest and in transit to complement privacy standards.               |
| **[Audit Logging]**            | Records all changes to privacy-related data for forensic analysis.                            |
| **[Anonymization Techniques]** | Applies statistical or synthetic data methods to minimize re-identification risks.         |
| **[API Gateways]**             | Controls access to privacy endpoints (e.g., `/privacy/rights`) with role-based authentication. |
| **[Data Retention Policies]**  | Automates purging of data post-expiry (e.g., GDPR’s 1-year limit for anonymized data).       |

---

## **7. Example Workflow**
1. **User Submits Opt-Out Request**:
   - API call to `/privacy/rights` with `type = deletion`.
2. **System Records Request**:
   ```sql
   INSERT INTO privacy_rights (id, subject_id, type, status)
   VALUES ('uuid2', '550e8400-e29b-41d4-a716-446655440000', 'deletion', 'pending');
   ```
3. **Team Approves Request**:
   - Update `status = 'granted'`.
4. **Data Purged**:
   - Execute stored procedure to mask or delete records in `processing_actions`.

---
**Last Updated**: [Insert Date]
**Version**: 1.3
**Owners**: Compliance Team, Engineering