---
# **[Pattern] Privacy Integration – Reference Guide**

---

## **1. Overview**
The **Privacy Integration** pattern ensures compliance with data privacy regulations (e.g., GDPR, CCPA) while enabling controlled data sharing, consent management, and anonymization. This pattern standardizes how systems collect, process, and disclose user data, integrating privacy controls at the architectural, API, and UI levels.

Key goals:
- **Consent management**: Track and enforce user consent for data collection.
- **Data minimization**: Limit data collection to only what’s necessary.
- **Access controls**: Restrict access to sensitive data via role-based or attribute-based policies.
- **Anonymization & pseudonymization**: Mask personal data when sharing or storing.
- **Audit trails**: Log data access and modifications for compliance.

This guide covers implementation details, schema requirements, query examples, and related patterns for seamless privacy integration.

---

## **2. Schema Reference**
Use the following tables to model privacy-related entities in your database or data model.

### **2.1 Core Privacy Entities**
| **Entity**            | **Fields**                                                                                     | **Description**                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **User Consent**      | `consent_id` (UUID), `user_id` (UUID), `purpose` (string), `status` (enum: GRANTED/REVOKED), `created_at`, `updated_at` | Tracks user consent for specific data uses (e.g., marketing, analytics).                           |
| **Data Subject Request** | `request_id` (UUID), `user_id` (UUID), `type` (enum: ACCESS/ERASE/CORRECT), `status` (enum: PENDING/COMPLETED), `notes` (text) | Logs requests for data access, deletion, or corrections per GDPR/CCPA.                              |
| **Data Access Log**   | `log_id` (UUID), `user_id` (UUID), `entity_id` (UUID), `action` (enum: READ/WRITE), `timestamp`, `permissions_granted` (array) | Audits who accessed what data and when.                                                             |
| **Pseudonymization Key** | `key_id` (UUID), `user_id_original` (UUID), `pseudonym` (string), `encryption_key` (hash), `expiry_date` | Maps original user IDs to temporary pseudonyms for anonymized data sharing.                        |
| **Data Inventory**    | `inventory_id` (UUID), `data_type` (string), `purpose` (string), `data_location` (string), `owner_department` (string) | Catalogs data assets, their purposes, and storage locations for compliance reporting.           |

---

### **2.2 Relationships**
| **From**               | **To**                     | **Cardinality** | **Description**                                                                                     |
|------------------------|----------------------------|------------------|-----------------------------------------------------------------------------------------------------|
| `User Consent`         | `Data Subject Request`     | 1:N             | A consent record may relate to multiple requests (e.g., a user revokes consent across all purposes).|
| `Data Access Log`      | `User Consent`             | 1:1             | Each log entry references the consent status of the accessed user.                                   |
| `Pseudonymization Key` | `User Consent`             | 1:N             | A pseudonym is tied to user consent for a specific purpose (e.g., analytics).                       |
| `Data Inventory`       | `User Consent`             | N:N (via tags) | Inventory items may be tagged with consent purposes (e.g., "marketing").                            |

---

### **2.3 Example Data Model (Simplified)**
```sql
CREATE TABLE User_Consent (
    consent_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES Users(user_id),
    purpose VARCHAR(50) NOT NULL,  -- e.g., "marketing", "analytics"
    status VARCHAR(20) NOT NULL CHECK (status IN ('GRANTED', 'REVOKED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE Data_Access_Log (
    log_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    entity_id UUID NOT NULL,  -- References the table/record accessed
    action VARCHAR(10) NOT NULL CHECK (action IN ('READ', 'WRITE')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    permissions_granted JSONB  -- e.g., { "field": "name", "read": true }
);
```

---

## **3. Implementation Details**
### **3.1 Key Concepts**
1. **Consent Lifecycle**
   - Users grant/revoke consent via a UI (e.g., cookie banner, privacy dashboard).
   - Consents are stored with timestamps and purposes (e.g., "personalized ads").
   - Systems **automatically enforce** revoked consents (e.g., drop analytics tracking).

2. **Data Minimization**
   - Only collect data **necessary** for the stated purpose.
   - Example: Avoid storing email unless required for GDPR "right to be forgotten" notifications.

3. **Anonymization Strategies**
   - **Pseudonymization**: Replace PII (personally identifiable information) with reversible tokens (e.g., `user_123`).
     ```sql
     UPDATE users SET email = 'pseudo_' || pseudonym_id WHERE user_id = original_id;
     ```
   - **Tokenization**: Replace PII with non-reversible tokens (e.g., for payment systems).
   - **Aggregation**: Share only anonymized aggregates (e.g., "users aged 25–34").

4. **Access Control**
   - Use **attribute-based access control (ABAC)** to grant permissions dynamically:
     - *Role*: "Data Privacy Officer"
     - *Attribute*: `consent_status = 'GRANTED' AND purpose = 'analytics'`
   - Example policy (in Open Policy Agent):
     ```rego
     default allow = false
     allow {
       input.action == "read"
       input.user.consent[input.purpose]["status"] == "GRANTED"
     }
     ```

5. **Audit Trail Requirements**
   - Log **who**, **what**, **when**, and **why** (purpose) for all data access.
   - Retain logs for **at least 6 years** (GDPR) or as required by jurisdiction.

---

### **3.2 Integration Points**
| **Component**         | **Privacy Integration Actions**                                                                                     |
|-----------------------|--------------------------------------------------------------------------------------------------------------------|
| **Authentication**    | Anonymize user data in session tokens (e.g., JWT with `sub` claim as pseudonym).                                  |
| **APIs**              | Add headers/params for consent checks: `X-Consent-Purpose: analytics`.                                          |
| **Database**          | Use row-level security (RLS) or views to enforce consent-based filtering.                                         |
| **Event Streaming**   | Mask PII in event payloads (e.g., `user_id` → `pseudo_123`).                                                     |
| **Analytics**         | Use anonymized datasets for reporting (e.g., PostgreSQL’s `pgcrypto` for pseudonymization).                        |
| **Third-Party Vendors** | Require contracts with **data processing agreements (DPAs)** and consent validation endpoints.                   |

---

## **4. Query Examples**
### **4.1 Consent-Based Data Access**
**Query:** Fetch user data only if consent is granted for "analytics."
```sql
SELECT u.*
FROM users u
JOIN user_consent uc ON u.user_id = uc.user_id
WHERE uc.purpose = 'analytics'
  AND uc.status = 'GRANTED'
  AND uc.updated_at > NOW() - INTERVAL '30 days';  -- Ensure recent consent
```

**PostgreSQL with Row-Level Security (RLS):**
```sql
CREATE POLICY consent_policy ON users
    USING (user_consent.purpose = current_setting('app.consent_purpose')::text)
    WITH CHECK (user_consent.status = 'GRANTED');
```

---

### **4.2 Pseudonymization**
**Query:** Replace original user IDs with pseudonyms for a shared dataset.
```sql
CREATE VIEW anonymized_users AS
SELECT
    pseudo.pseudonym_id,
    u.age,
    u.preferred_language
FROM users u
JOIN pseudonymization_keys pseudo ON u.user_id = pseudo.user_id_original
WHERE pseudo.purpose = 'analytics';
```

---

### **4.3 Data Subject Requests**
**Query:** List pending "right to erase" requests.
```sql
SELECT
    dsr.request_id,
    dsr.user_id,
    u.email,
    dsr.type,
    dsr.status,
    dsr.created_at
FROM data_subject_requests dsr
JOIN users u ON dsr.user_id = u.user_id
WHERE dsr.type = 'ERASE'
  AND dsr.status = 'PENDING';
```

---

### **4.4 Audit Log Query**
**Query:** Find all reads of sensitive fields (e.g., `email`) in the last 7 days.
```sql
SELECT
    dal.user_id,
    u.email,
    dal.entity_id,
    dal.action,
    dal.timestamp,
    dal.permissions_granted->>'field' AS sensitive_field
FROM data_access_log dal
JOIN users u ON dal.user_id = u.user_id
WHERE dal.timestamp > NOW() - INTERVAL '7 days'
  AND dal.permissions_granted->>'field' = 'email';
```

---

## **5. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                                     |
|----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **[Data Masking](https://example.com)** | Dynamically redacts PII in queries based on user role.                                             | Internal reports where full PII isn’t needed.                                                     |
| **[Federated Identity](https://example.com)** | Centralizes authentication and consent management across services.                              | Multi-tenant SaaS applications.                                                                     |
| **[Event Sourcing for Privacy](https://example.com)** | Stores privacy events (e.g., "consent granted") as immutable logs.                                | High-audit systems (e.g., healthcare, finance).                                                   |
| **[Attribute-Based Access Control (ABAC)](https://example.com)** | Grants access based on dynamic attributes (e.g., consent, time).                                  | Systems with fine-grained privacy policies.                                                        |
| **[Data Minimization via Schema Design](https://example.com)** | Structures data to avoid storing unnecessary PII.                                                  | New systems where schema design is flexible.                                                      |

---

## **6. Best Practices**
1. **Automate Consent Checks**
   - Use middleware (e.g., AWS Lambda, Kubernetes ingress controllers) to validate consent before data access.

2. **Pseudonymize Early**
   - Apply pseudonymization at the **data ingestion layer** (e.g., when collecting form submissions).

3. **Simplify Data Subject Requests**
   - Provide a **self-service portal** for users to review/control their data (e.g., "Download your data" button).

4. **Document Everything**
   - Maintain a **data inventory** and **processing agreements** for vendors. Use tools like:
     - [GDPR Data Inventory Template (IAPP)](https://iapp.org)
     - [Privacy by Design Toolkit (EU Commission)](https://ec.europa.eu/info/sites/default/files/privacy-by-design-toolkit_en.pdf)

5. **Test for Compliance**
   - Run **automated scans** for PII exposure (e.g., using tools like [Prisma Cloud](https://prismacloud.io)).
   - Conduct **penetration tests** for access controls.

6. **Plan for Breaches**
   - Store anonymized backups separately to limit breach impact.
   - Use **differential privacy** for analytics to prevent re-identification (e.g., adding noise to queries).

---
**See also:**
- [GDPR Article 5 (Data Protection Principles)](https://gdpr-info.eu/art-5-gdpr/)
- [CCPA Section 1798.100](https://oag.ca.gov/privacy/ccpa) (California Consumer Privacy Act)