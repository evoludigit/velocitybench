# **[Pattern] Privacy Conventions Reference Guide**

## **Overview**
Privacy Conventions define standardized ways to handle sensitive data—such as personal identifying information (PII), health records, or financial data—across applications and systems. This ensures compliance with regulations (e.g., GDPR, HIPAA, CCPA), minimizes security risks, and improves interoperability while maintaining user trust. These conventions include **format standardization**, **encryption/obfuscation rules**, **data minimization principles**, **access controls**, and **auditing mechanisms**.

---

## **Schema Reference**
Below is a structured schema for defining Privacy Conventions. Adapt fields to your domain (e.g., healthcare, finance, enterprise).

| **Field**               | **Description**                                                                                     | **Examples**                                                                                     | **Type**         | **Constraints**                                                                 |
|-------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|------------------|---------------------------------------------------------------------------------|
| **Convention ID**       | Unique identifier for the convention (e.g., `PR-CONV-001`).                                       | `PR-CONV-001`, `HIPAA-FORMAT-AES256`                                                              | String           | Required, UUID or alphanumeric.                                                 |
| **Convention Name**     | Human-readable name (e.g., "GDPR PII Tokenization").                                               | "Health Data Masking," "Financial Data Hashing"                                                 | String           | Max 128 chars.                                                                   |
| **Scope**               | Defines where the convention applies (e.g., REST API, database, file storage).                     | `API`, `Database`, `On-Premises`, `Cloud`                                                        | Array (String)   | Must include at least one scope.                                               |
| **Data Type**           | Categories of sensitive data (e.g., names, SSNs, biometrics).                                      | `PII`, `Credit_Card`, `Medical_Records`, `IP_Address`                                            | Array (String)   | Predefined taxonomy (customize as needed).                                     |
| **Compliance Rule**     | Applicable regulations or standards (e.g., GDPR Art. 5(1)(f), HIPAA 164.308).                     | `GDPR`, `HIPAA`, `CCPA`, `PCI-DSS`, `Custom_Policy_X`                                           | Array (String)   | Reference to regulatory or internal policies.                                   |
| **Format Standard**     | How data should be represented (e.g., UUID v4 for usernames, ISO standard for dates).             | `UUID`, `ISO_8601`, `SSN_Masked_XXX-XX-1234`, `AES_256_CBC`                                     | String           | Must align with compliance requirements.                                         |
| **Encryption Method**   | How data is encrypted/protected at rest/motion (e.g., AES-256, RSA, PGP).                         | `AES-256-CBC`, `RSA-2048`, `PGP_GPG`, `None` (for obfuscation)                                   | String           | Must support key management (e.g., KMS).                                         |
| **Key Rotation Policy** | Frequency of key rotation (e.g., `90-days`, `manual`, `per-session`).                             | `90-days`, `180-days`, `session-based`, `manual`                                               | String           | Define criticality (e.g., `high`: 30 days).                                      |
| **Obfuscation Rule**    | How to obscure raw data (e.g., redacting middle digits, shuffling characters).                     | `SSN: XXX-XX-1234`, `Email: ****@domain.com`, `Dynamic_Replacement`                             | String           | Must not allow reverse engineering.                                            |
| **Access Control**      | Who can access/modify data (e.g., `Role-Based`, `Attribute-Based`, `Temporary Access`).           | `RBAC`, `ABAC`, `MFA_Required`, `Audit-Only`                                                     | Array (String)   | Must include logging/auditing.                                                  |
| **Audit Logs**          | Requirement for tracking access/modifications (e.g., `IP_Address`, `Timestamp`, `User_ID`).       | `IP_Address + Timestamp`, `User_ID + Action_Type`, `Full_Audit_Trail`                           | Array (String)   | Must comply with `SOX`, `PCI`, or equivalent.                                    |
| **Data Minimization**   | Whether to limit collection/storage of data (e.g., `Only_What_Is_Necessary`).                     | `Minimal_PII`, `Temporary_Data_Storage`, `Anonymized_Logs`                                      | String           | Justify exceptions in policy.                                                  |
| **Deletion Policy**     | Rules for permanent data removal (e.g., `90-day_retention`, `Right_to_Erasure`).                  | `GDPR_Right_to_Erasure`, `90-day_retention`, `Automated_Deletion`                                | String           | Must include proof-of-deletion mechanisms.                                      |
| **Third-Party Risk**    | How third-party access is governed (e.g., `SAML_SSO`, `Data_Processing_Agreement`).               | `DPA_Signed`, `SAML_2.0`, `API_Gateways`                                                        | String           | Include vendor compliance checks.                                               |
| **Test Cases**          | Example scenarios to validate compliance (e.g., "PII tokenized before API response").             | `"Mask SSN in SQL queries," "Encrypt health records at rest"`                                  | Array (String)   | Include pass/fail criteria.                                                      |
| **Version**             | Schema version (e.g., `1.0`, `2023.1`) for backward compatibility.                                | `1.0`, `2023.04`                                                                                 | String           | Increment on breaking changes.                                                  |

---

## **Implementation Details**
### **1. Key Concepts**
- **Data Classification**: Categorize data by sensitivity (e.g., `Public`, `Internal`, `Confidential`, `Restricted`).
- **Encryption vs. Obfuscation**:
  - **Encryption**: Reversible (e.g., AES-256) for active use.
  - **Obfuscation**: Irreversible (e.g., tokenization, hashing) for logs/audits.
- **Key Management**:
  - Use Hardware Security Modules (HSMs) or cloud KMS (e.g., AWS KMS, Azure Key Vault).
  - Rotate keys automatically or via policy.
- **Access Control**:
  - **Role-Based Access Control (RBAC)**: Assign permissions by role (e.g., `Admin`, `Analyst`).
  - **Attribute-Based Access Control (ABAC)**: Grant access based on attributes (e.g., `Department = Finance`).
- **Audit Trails**:
  - Log all access/modification events with immutable timestamps.
  - Store logs in a secured, non-logic-based database (e.g., Splunk, ELK).

### **2. Common Patterns**
| **Pattern**               | **Use Case**                                                                 | **Example**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Tokenization**          | Replace sensitive data with tokens (e.g., credit card numbers).            | `Token: TKN_987654321` → Replaced by actual value during auth.                                |
| **Dynamic Data Masking**  | Mask fields in queries (e.g., `SELECT name FROM users WHERE ssn = XXX-XX-1234`). | SQL: `SELECT name FROM users WHERE ssn = <<MASKED>>`.                                          |
| **Field-Level Encryption**| Encrypt specific columns (e.g., `ssn`, `email`) in databases.            | PostgreSQL `pgcrypto`, MongoDB Field-Level Encryption.                                           |
| **Zero-Knowledge Proofs** | Verify data without exposing it (e.g., login without PII).                | ZK-SNARKs for authentication.                                                                   |
| **Data Minimization**     | Only collect what’s necessary (e.g., avoid storing IP addresses).          | API: `Request: { "email": "user@example.com" }` (no SSN).                                    |

### **3. Tools & Libraries**
| **Tool/Library**          | **Purpose**                                                                 | **Example Use Case**                                                                           |
|---------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **AWS KMS**               | Manage encryption keys.                                                    | Encrypt S3 buckets containing PII.                                                            |
| **HashiCorp Vault**       | Secure secrets management.                                                 | Store API keys with dynamic secrets rotation.                                                |
| **OpenSSL**               | Encrypt/decrypt data (AES, RSA).                                            | `openssl enc -aes-256-cbc -in plaintext.txt -out ciphertext.txt -pass pass:mykey`.           |
| **PostgreSQL `pgcrypto`** | Field-level encryption in SQL.                                              | `CREATE TABLE users (id SERIAL PRIMARY KEY, ssn BYTEA ENCRYPTED USING 'aes256');`              |
| **OpenPGP**               | Encrypt emails/files.                                                       | `gpg -c file.txt` → Encrypted `file.txt.gpg`.                                                |
| **Apache Kafka**         | Secure event streaming with encryption.                                     | Encrypt Kafka messages with `ssl.keystore.location`.                                        |
| **OpenTelemetry**         | Audit logging with privacy-preserving metadata.                          | Log events without exposing PII (e.g., `user_id: "uk-abc123"`).                                |

---

## **Query Examples**
### **1. SQL Query with Dynamic Masking**
```sql
-- Mask SSNs in a query result (PostgreSQL)
SELECT
    id,
    name,
    CAST(REGEXP_REPLACE(ssn, '(\d{3})-(\d{2})-(\d{4})', '\1-\2-\333') AS VARCHAR) AS masked_ssn
FROM users
WHERE department = 'HR';
```
**Output**:
| id | name   | masked_ssn |
|----|--------|------------|
| 1  | Alice  | 123-45-333 |

### **2. API Response with Tokenized Data**
**Request**:
```http
POST /users
{
  "email": "alice@example.com",
  "ssn": "123-45-6789"  -- Automatically tokenized
}
```
**Response**:
```json
{
  "id": "uk-abc123",
  "email": "alice@example.com",
  "ssn_token": "TKN_987654321"
}
```

### **3. Encrypted Database Column**
```sql
-- Insert encrypted SSN (PostgreSQL pgcrypto)
INSERT INTO users (id, name, ssn_encrypted)
VALUES (1, 'Alice', pgp_sym_encrypt('123-45-6789', 'secret_key'));

-- Query (returns encrypted blob)
SELECT pgp_sym_decrypt(ssn_encrypted, 'secret_key') FROM users;
```

### **4. Audit Log Entry**
```json
{
  "event_id": "aud-20230515-1020",
  "timestamp": "2023-05-15T10:20:00Z",
  "user_id": "uk-xyz789",
  "action": "READ",
  "resource": "users/1",
  "ip_address": "192.168.1.100",
  "metadata": {
    "original_ssn": "***-**-1234",  -- Obfuscated
    "requested_by": "admin@company.com"
  }
}
```

---

## **Related Patterns**
1. **[Data Encryption Best Practices]**
   - Complements Privacy Conventions by detailing encryption algorithms, key management, and cipher modes.
   - *See also*: [Cryptography Patterns](https://example.com/crypto-patterns).

2. **[Audit Logging]**
   - Ensures immutable records of access/modifications to sensitive data.
   - *See also*: [Immutable Audit Trails](https://example.com/audit-logging).

3. **[ZKP (Zero-Knowledge Proofs)]**
   - Enables authentication/authorization without exposing PII.
   - *See also*: [ZK-Proofs for Privacy](https://example.com/zk-proofs).

4. **[Data Minimization Framework]**
   - Guides reducing data collection to what’s necessary for compliance.
   - *See also*: [Minimal Data Collection](https://example.com/minimal-data).

5. **[API Security Conventions]**
   - Extends Privacy Conventions to secure APIs (e.g., OAuth 2.0, JWT tokenization).
   - *See also*: [Secure API Design](https://example.com/api-security).

6. **[Tokenization Systems]**
   - Standardizes how sensitive data is replaced with tokens (e.g., for databases, APIs).
   - *See also*: [Tokenization Architecture](https://example.com/tokenization).

7. **[Pseudonymization]**
   - Temporary anonymization of data (e.g., for analytics while preserving usability).
   - *See also*: [Pseudonymization Techniques](https://example.com/pseudonymization).

8. **[Compliance Automation]**
   - Tools to enforce Privacy Conventions via policies (e.g., Open Policy Agent).
   - *See also*: [Policy-as-Code](https://example.com/compliance-automation).

9. **[Secure Data Sharing]**
   - Methods for sharing sensitive data securely (e.g., federated learning, differential privacy).
   - *See also*: [Secure Data Collaboration](https://example.com/data-sharing).

10. **[Data Retention Policies]**
    - Defines when and how to delete data in compliance with regulations.
    - *See also*: [Data Lifecycle Management](https://example.com/data-retention).