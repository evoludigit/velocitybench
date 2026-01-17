# **[Pattern] Privacy Techniques – Reference Guide**

---

## **Overview**
The **Privacy Techniques** pattern defines a structured approach to protecting sensitive data by applying technical controls to limit exposure, prevent unauthorized access, or ensure compliance with privacy regulations (e.g., GDPR, CCPA). This guide outlines key techniques—*obfuscation, tokenization, zero-trust principles, and differential privacy*—along with implementation considerations, schema references, and practical query examples. These techniques are applicable across systems handling **PII (Personally Identifiable Information), logs, analytics, and ML models**.

Adopting these techniques requires balancing **usability** and **security**; misuse may degrade performance or functionality. Always align with organizational policies and legal requirements.

---

## **Key Concepts & Implementation Details**
### **1. Core Techniques**
| **Technique**          | **Description**                                                                                     | **Use Case Examples**                                                                 |
|------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **Obfuscation**        | Hides data in plain sight (e.g., masking, formatting, or distortion) without altering meaning.       | Logs: `[USER=****-1234]`, reports with placeholders for PII.                          |
| **Tokenization**       | Replaces sensitive data with non-sensitive tokens (e.g., tokens for credit cards or IDs).          | Database fields: `{SSN: token_1234}`, API responses with masked PII.                  |
| **Zero-Trust Access**  | Requires verification for every access attempt, even within a network.                             | Multi-factor authentication (MFA), short-lived credentials, or role-based restrictions.|
| **Differential Privacy**| Adds calculated noise to data to prevent re-identification while preserving analytical value.     | Aggregated analytics (e.g., "95% ±3% of users prefer Feature X").                     |
| **Encryption**         | Transforms data into unreadable ciphertext (in transit or at rest).                                | TLS for APIs, AES-256 for database columns storing passwords.                         |
| **Data Minimization**  | Collects and stores only the data necessary for a specific purpose.                                | Forms: Only request fields relevant to the user journey.                             |

### **2. Complementary Controls**
- **Access Controls**: Least privilege, just-in-time (JIT) access.
- **Audit Logging**: Track all data access/events for compliance.
- **Data Retention Policies**: Automate deletion of unnecessary records.
- **Secure Defaults**: Disable features exposing PII unless explicitly enabled.

---

## **Schema Reference**
Below are schema templates for implementing Privacy Techniques in common systems.

### **Table 1: Privacy-Aware Database Schema**
| **Field**          | **Type**       | **Technique Applied**       | **Example Value**         | **Notes**                                      |
|--------------------|----------------|-----------------------------|---------------------------|-----------------------------------------------|
| `user_id`          | VARCHAR(100)   | Tokenization                | `tok_5ae2b7c4e0f...`      | Replace with cryptographic token.              |
| `email`            | VARCHAR(255)   | Obfuscation (masking)       | `john.d****@example.com`  | Front/back masking; store hashed version.       |
| `credit_card`      | VARCHAR(50)    | Tokenization                | `tok_cc3847...`           | Use PCI-compliant tokenization services.       |
| `age`              | INT            | Differential Privacy        | `30±2`                    | Report as ranges with noise.                  |
| `last_login_ip`    | VARCHAR(45)    | Encryption (TLS)            | `192.168.1.1` (encrypted)| Encrypt in transit and at rest.                |
| `consent_status`   | BOOLEAN        | Access Controls             | `true/false`              | Enforce via RBAC policies.                    |

### **Table 2: API Response Schema (PII Masking)**
```json
{
  "user": {
    "id": "tok_user_abc123",       // Tokenized
    "name": "J. Doe",              // Obfuscated (first letter + placeholder)
    "email": "[REDACTED]",          // Fully masked or hashed
    "is_active": true              // Unchanged
  },
  "metrics": {
    "total_users": 95,              // Differential privacy: 95±3%
    "avg_age": null                 // Non-sensitive aggregate
  }
}
```

---

## **Query Examples**
### **1. Masking Queries (Database)**
**Scenario**: Retrieve user emails for reporting without exposing raw data.
```sql
-- SQL (PostgreSQL)
SELECT
  user_id AS "User ID",
  CONCAT(SUBSTRING(email, 1, 3), '****') AS "Masked Email",
  role
FROM users
WHERE active = true;
```
**Output**:
| User ID | Masked Email | Role        |
|---------|--------------|-------------|
| tok_123 | john@****    | Admin       |

### **2. Tokenization in API Calls (REST)**
**Request (Masking Sensitive Headers)**:
```http
GET /api/reports HTTP/1.1
Host: api.example.com
Authorization: Bearer tok_auth_5e37...  # Tokenized JWT
X-Correlation-ID: tok_corr_abc...      # Obfuscated
```
**Response**:
```json
{
  "data": {
    "total_transactions": 42,
    "user_count": "50±2"  // Differential privacy
  },
  "metadata": {
    "processed_by": "tok_user_987"
  }
}
```

### **3. Zero-Trust Access (Role-Based Filtering)**
**Query (Redact data based on user role)**:
```sql
-- SQL (with dynamic redacting function)
SELECT
  CASE
    WHEN current_user_has_role('admin') THEN full_name
    ELSE CONCAT(SUBSTRING(full_name, 1, 1), '****')
  END AS "Display Name",
  department
FROM employees
WHERE project_id = 'tok_proj_456';
```

### **4. Differential Privacy in Aggregates**
**Query (Adding noise to sensitive aggregates)**:
```sql
-- Python (using opendp)
from opendp import (
    DifferentialPrivacy,
    LaplaceMechanism
)

def noisy_count(count):
    mechanism = LaplaceMechanism(epsilon=1.0, sensitivity=1)
    return int(count + mechanism.noise())

# Example: Query with noise
total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
print(f"Noisy user count: {noisy_count(total_users)}")
```

---

## **Performance Considerations**
| **Technique**       | **Impact on Performance**                          | **Mitigation**                                  |
|---------------------|---------------------------------------------------|------------------------------------------------|
| **Tokenization**    | Minimal (adds lookup overhead)                    | Use memory-efficient token tables.              |
| **Obfuscation**     | Low (client-side masking)                         | Cache masked values.                            |
| **Differential Privacy** | High (noise increases query time)             | Pre-compute noisy aggregates.                  |
| **Encryption**      | Moderate (CPU/memory for decryption)              | Use hardware acceleration (AWS KMS, HSMs).       |
| **Zero-Trust**      | High (JIT auth adds latency)                      | Cache short-lived tokens.                       |

---

## **Related Patterns**
1. **[Data Encryption]**
   - Complements tokenization/obfuscation by securing data at rest/transit.

2. **[Audit Logging]**
   - Essential for tracking access to obfuscated or tokenized data.

3. **[Federated Learning]**
   - Useful for privacy-preserving ML models trained on decentralized data.

4. **[Consent Management]**
   - Works with obfuscation/minimization to honor user privacy choices.

5. **[Compliance Enforcement]**
   - Integrates with privacy techniques to automate GDPR/CCPA checks.

---
## **Regex for Obfuscation (Example)**
```regex
-- Mask email domains (e.g., "user@*ample.com" → "user@*****.com")
(.*?)@([^.]+)\.([^.]+)\.[^.]+
=> $1@$2.***.$3
```
**Input**: `john@company.org`
**Output**: `john@com****.org`

---
## **Tools & Libraries**
| **Tool/Library**          | **Purpose**                                  | **Links**                                  |
|---------------------------|---------------------------------------------|-------------------------------------------|
| AWS KMS                   | Encryption key management                    | [aws.amazon.com/kms](https://aws.amazon.com/kms/) |
| Microsoft Purview         | PII discovery and masking                   | [Microsoft Docs](https://learn.microsoft.com/en-us/purview/) |
| OpenDP                    | Differential privacy for Python             | [GitHub](https://github.com/openprivacy/opendp) |
| HashiCorp Vault           | Secrets management for tokens/credentials   | [Vault.io](https://www.vaultproject.io/)    |
| Apache Druid              | Column-level encryption for time-series data| [Druid.io](https://druid.apache.org/)      |

---
## **Best Practices**
1. **Classify Data**: Tag PII with metadata (e.g., "GDPR-Sensitive") for automated processing.
2. **Default to Least Privilege**: Assume all data is sensitive; obfuscate/mask by default.
3. **Test Failures**: Verify obfuscation/encryption doesn’t break applications (e.g., login forms).
4. **Document Policies**: Maintain a privacy impact assessment (PIA) for each technique.
5. **Regular Audits**: Rotate tokens, re-evaluate access controls, and test differential privacy parameters.