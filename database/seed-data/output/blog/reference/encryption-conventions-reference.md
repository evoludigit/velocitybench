# **[Pattern] Encryption Conventions Reference Guide**

---

## **Overview**
Encryption conventions ensure consistent, secure handling of sensitive data across systems. This guide outlines best practices for key management, data encryption at rest/transit, and metadata handling to mitigate risks like unauthorized access, data leaks, or compliance violations.

**Key Use Cases:**
- Protecting **PII (Personally Identifiable Information)**, **financial data**, or **confidential business documents**.
- Ensuring **compliance** (e.g., GDPR, HIPAA, PCI-DSS).
- Enabling **secure cross-system communication** (APIs, databases, backups).
- Maintaining **auditability** through clear encryption metadata.

---

## **Implementation Details**
### **1. Core Principles**
| Principle               | Description                                                                 |
|-------------------------|-----------------------------------------------------------------------------|
| **Consistency**         | Uniform encryption mechanisms across all systems.                           |
| **Defensibility**       | Keys and practices must withstand forensic review.                          |
| **Minimal Scope**       | Encrypt only what’s necessary; avoid over-encryption.                       |
| **Key Hierarchy**       | Use **root/master keys** (e.g., HSM-backed) to derive **data keys** dynamically. |
| **Separation of Duties**| Never combine key management with application logic (e.g., avoid in-code keys). |

---

### **2. Encryption Layers**
#### **Data Encryption**
| Layer                  | Purpose                          | Methods                          |
|------------------------|----------------------------------|----------------------------------|
| **At Rest**            | Secure stored data (DBs, files).  | AES-256 (GCM mode), AES-128.     |
| **In Transit**         | Protect data in motion.           | TLS 1.3, TLS 1.2 (with curve25519). |
| **Field-Level**        | Encrypt sensitive fields (e.g., SSN). | Deterministic AES (for queries), Randomized AES. |

#### **Key Management**
| Component          | Responsibility                                                                 | Best Practice                          |
|--------------------|-------------------------------------------------------------------------------|----------------------------------------|
| **HSM (Hardware Security Module)** | Stores root/master keys.                                                   | Use FIPS 140-2 Level 3 certified HSMs. |
| **KMS (Key Management Service)** | Rotates and revokes keys dynamically.                                       | Cloud: AWS KMS, GCP KMS.              |
| **Application Keys** | Derived from root keys (short-lived).                                       | Rotate every **90 days**; log access.  |
| **Key Escrow**      | Backup keys for recovery (compliance).                                       | Store in **air-gapped HSMs** or vaults. |

---

### **3. Metadata Standards**
Encryption metadata must include:
- **Encryption Algorithm** (e.g., `"AES-256-GCM"`).
- **Key ID** (reference to KMS/HSM entry).
- **IV/Nonce** (for authenticated encryption).
- **Timestamp** (for key rotation tracking).
- **Purpose** (e.g., `"customer_data"`, `"api_auth"`).

**Example Metadata (JSON):**
```json
{
  "encrypted_field": "d8...e5",
  "algorithm": "AES-256-GCM",
  "key_id": "hsm:ae12-3456-7890",
  "iv": "a1b2c3...",
  "created_at": "2023-10-01T12:00:00Z",
  "purpose": "ssn_encryption"
}
```

---

## **Schema Reference**
### **1. Core Schema: `EncryptionPolicy`**
| Field               | Type     | Required | Description                                                                 | Example Value                          |
|---------------------|----------|----------|-----------------------------------------------------------------------------|----------------------------------------|
| `algorithm`         | String   | Yes      | Symmetric cipher (e.g., `"AES-256-GCM"`).                                 | `"AES-128-CBC"`                       |
| `key_rotation_days` | Integer  | Yes      | Days before key expiry/replacement.                                        | `90`                                    |
| `key_escrow`        | Boolean  | No       | Enable backup escrow for compliance.                                        | `true`                                 |
| `hsm_integration`   | Boolean  | No       | Use HSM for key storage.                                                    | `true`                                 |
| `iv_length`         | Integer  | No       | Initialization vector length in bytes (for GCM/AES).                       | `12` (AES-128), `16` (AES-256)        |
| `purpose_tags`      | Array    | No       | Comma-separated use cases (e.g., `"pii", "healthcare"`).                   | `["pii", "financial"]`                |

---
### **2. Database Field Schema**
| Field               | Type     | Required | Description                                                                 | Example                          |
|---------------------|----------|----------|-----------------------------------------------------------------------------|----------------------------------|
| `data`              | Binary   | Yes      | Encrypted payload.                                                         | `0x4f...9a` (hex-encoded)       |
| `key_id`            | String   | Yes      | Reference to KMS/HSM key entry.                                             | `"kms:aws:arn:1234"`             |
| `algorithm`         | String   | Yes      | Encryption algorithm used.                                                  | `"AES-256-GCM"`                  |
| `iv`                | Binary   | Yes      | Initialization vector (for GCM).                                            | `0x5e...1a`                       |
| `tag`               | Binary   | No       | Auth tag (GCM mode).                                                       | `0x3d...f8`                       |

---
### **3. API Encryption Payload Schema**
```json
{
  "data": "U29tZSBvbmx5IGJhc2U2NCA8L3NvbWU+",
  "algorithm": "AES-128-CBC",
  "key_id": "api:prod:key-123",
  "iv": "AAECAwQFBgcICQoLDA0ODw==",
  "purpose": "user_auth"
}
```

---

## **Query Examples**
### **1. Querying Encrypted Data (Database)**
**Language:** SQL (PostgreSQL with `pgcrypto` extension)
```sql
-- Fetch encrypted field (decryption handled client-side)
SELECT
  customer_id,
  encrypted_ssn,
  key_id,
  algorithm
FROM customers
WHERE customer_id = '12345';

-- Update with new encrypted data
UPDATE customers
SET
  encrypted_ssn = encrypt('123-45-6789', 'AES-256-GCM', key_id, GENERATE_RANDOM_BYTES(12) AS iv)
WHERE customer_id = '12345';
```

---
### **2. API: Request/Response (TLS + Encrypted Payload)**
**Request (TLS 1.3):**
```http
POST /api/secure/data
Host: example.com
Content-Type: application/json

{
  "encrypted_payload": "U29tZSBvbmx5IGJhc2U2NCA8L3NvbWU+",
  "key_id": "api:prod:key-123",
  "algorithm": "AES-128-CBC",
  "iv": "AAECAwQFBgcICQoLDA0ODw=="
}
```
**Response (Decrypted Client-Side):**
```json
{
  "status": "success",
  "decrypted_data": "Secret message"
}
```

---
### **3. Key Rotation Workflow (Automated)**
**Trigger:** Scheduled job (e.g., Cron) or KMS event.
**Steps:**
1. Generate new **data key** in KMS (`CreateDataKey` API).
2. Update metadata for affected records:
   ```sql
   UPDATE logs
   SET key_id = 'kms:new:123',
       iv = encrypt_rand(12)
   WHERE purpose = 'audit' AND created_at > '2023-10-01';
   ```
3. **Re-encrypt** sensitive fields (batch job):
   ```python
   # Pseudocode
   for record in database_query("SELECT ssn FROM users"):
       new_ssn_encrypted = encrypt(record.ssn, new_key)
       update_record(record.id, new_ssn_encrypted)
   ```

---

## **Related Patterns**
| Pattern                          | Description                                                                 | When to Use                                  |
|----------------------------------|-----------------------------------------------------------------------------|----------------------------------------------|
| **[Key Rotation]**               | Automated process to replace encryption keys.                               | When keys near expiry or compromised.       |
| **[Data Masking]**               | Dynamic redaction of sensitive data in queries.                            | For audit logs or non-sensitive views.       |
| **[Hardware Security Module]**   | Isolated key storage for root keys.                                         | High-security environments (e.g., banking).  |
| **[Field-Level Encryption]**     | Encrypt individual DB columns (e.g., SSN).                                  | PostgreSQL, SQL Server with extensions.       |
| **[Tokenization]**               | Replace sensitive data with non-sensitive tokens.                           | PCI-DSS compliance for payment data.         |
| **[Secure API Design]**          | Protect APIs with TLS + OAuth + encrypted payloads.                         | Public-facing services.                      |

---
## **Compliance Mappings**
| Standard          | Requirements Met by This Pattern                          |
|-------------------|-----------------------------------------------------------|
| **GDPR**          | Pseudonymization (via field-level encryption).             |
| **HIPAA**         | Encryption of PHI at rest/transit.                        |
| **PCI-DSS**       | Tokenization + encryption for cardholder data.            |
| **SOX**           | Audit trails via key metadata.                           |
| **NIST SP 800-53**| Key management (FIPS-validated HSMs).                     |

---
## **Troubleshooting**
| Issue                          | Solution                                                                 |
|--------------------------------|-------------------------------------------------------------------------|
| **Decryption fails**           | Verify `key_id`, `iv`, and algorithm match the encryption context.       |
| **Key rotation errors**        | Log `kms:CreateDataKey` failures; check permissions.                    |
| **Performance bottlenecks**    | Offload decryption to edge services (e.g., Lambda@Edge).               |
| **Metadata corruption**        | Use checksums (e.g., `SHA-256`) for metadata integrity.                  |

---
## **Tools & Integrations**
| Tool/Service               | Use Case                                  |
|----------------------------|-------------------------------------------|
| **AWS KMS**                | Key management + automatic rotation.      |
| **HashiCorp Vault**        | Dynamic secrets + key transient storage.  |
| **PostgreSQL `pgcrypto`**  | Field-level encryption in databases.       |
| **OpenSSL**                | Custom encryption (e.g., for offline systems). |
| **TLS Everywhere**         | Enforce TLS 1.2+ for all communications.   |