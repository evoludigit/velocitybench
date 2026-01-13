# **[Encryption Approaches] Pattern Reference Guide**

---

## **Overview**
The **Encryption Approaches** pattern defines structured methods for securing sensitive data at rest, in transit, and during processing. It categorizes encryption techniques based on use case (e.g., disk encryption, field-level encryption, or transport security) and provides implementation guidance for compliance-driven environments (e.g., GDPR, HIPAA, PCI DSS). This guide covers key concepts, schema mappings, operational considerations, and real-world query examples for integrating encryption into systems.

---

## **Implementation Details**

### **1. Key Concepts**
Encryption approaches are classified into **three primary categories**:
- **Data-at-Rest Encryption (DRE)**: Secures stored data (databases, backups, file systems).
- **Data-in-Transition Encryption (DTE)**: Protects data in transit (e.g., TLS for HTTP).
- **Data-in-Use Encryption (DUE)**: Encrypts data while being processed (e.g., ephemeral keys for in-memory operations).

| **Approach**               | **Scope**                          | **Use Case Examples**                          | **Compliance Alignment**       |
|----------------------------|------------------------------------|------------------------------------------------|-------------------------------|
| **Disk Encryption**        | OS/storage layer                   | Full-disk encryption (BitLocker, LUKS)         | HIPAA, FIPS 140-2              |
| **Transparent Data Encryption (TDE)** | Database layer | SQL Server TDE, Oracle Transparent encryption  | PCI DSS, GDPR                  |
| **Field-Level Encryption (FLE)** | Application layer | Masking PII (e.g., credit cards, SSNs)         | PCI DSS, CCPA                  |
| **Transport Security (TLS/SSL)** | Network layer | HTTPS, API endpoints                           | SOC 2, FIPS 140-2              |
| **Key Management (KMS)**   | Cryptographic layer                 | AWS KMS, HashiCorp Vault                       | NIST SP 800-57, FIPS 140-3     |
| **Homomorphic Encryption** | Computation layer                | Secure processing of encrypted data            | Research, specialized use-cases|

---

### **2. Schema Reference**
Below are schema mappings for common encryption approaches in JSON format:

#### **2.1. TLS/SSL Endpoint Configuration**
```json
{
  "transportSecurity": {
    "tlsVersion": "1.3",
    "certificateAuthority": {
      "path": "/etc/ssl/certs/ca.pem",
      "issuer": "Let's Encrypt"
    },
    "key": {
      "type": "RSA",
      "sizeBits": 2048,
      "rotationPolicy": {
      "intervalDays": 90,
      "notificationEmail": "security@domain.com"
      }
    },
    "cipherSuites": ["TLS_AES_256_GCM_SHA384", "ECDHE-ECDSA-AES128-GCM-SHA256"]
  }
}
```

#### **2.2. Transparent Data Encryption (TDE) for SQL Server**
```json
{
  "transparentDataEncryption": {
    "dbName": "customer_data",
    "encryptionKey": {
      "keyStoreProvider": "AWS_KMS",
      "keyId": "arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-ghij-klmnopqrstuv"
    },
    "columns": ["ssn", "credit_card", "email"],
    "compressionEnabled": true
  }
}
```

#### **2.3. Key Management Service (KMS) Policy**
```json
{
  "keyManagement": {
    "service": "AWS_KMS",
    "keyPolicy": {
      "allow": [
        {
          "principal": "*",
          "action": ["kms:Decrypt", "kms:GenerateDataKey"],
          "resource": "*",
          "condition": {
            "boolean": {
              "aws:SecureTransport": "true"
            }
          }
        }
      ]
    }
  }
}
```

---

### **3. Query Examples**
#### **3.1. Querying Encryption Status of Databases**
**SQL (PostgreSQL):**
```sql
SELECT
  database_name,
  pg_catalog.pg_get_userbyid(owning_user) AS owner,
  CASE
    WHEN pg_catalog.pg_isencryptable(database_name) THEN 'Encrypted'
    ELSE 'Not Encrypted'
  END AS encryption_status
FROM pg_catalog.pg_database
WHERE datistemplate = false;
```

**Output:**
| `database_name` | `owner`    | `encryption_status` |
|-----------------|------------|---------------------|
| `customer_db`   | `admin`    | Encrypted           |
| `logs`          | `read_user`| Not Encrypted       |

---

#### **3.2. Decrypting Field-Level Data (Python + PyCryptodome)**
```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

# Decryption example for a masked credit card (FLE)
def decrypt_credit_card(encrypted_data: str, key: bytes) -> str:
    cipher = AES.new(key, AES.MODE_CBC, key[:16])  # Use IV from key prefix
    decrypted = unpad(cipher.decrypt(base64.b64decode(encrypted_data)), AES.block_size)
    return decrypted.decode()
```

**Usage:**
```python
decrypted_card = decrypt_credit_card(
    encrypted_data="AQIDBA==",
    key=b'\x00\x11\x22\x33...'  # AES-256 key (truncated for example)
)
```

---

#### **3.3. Rotating Keys in AWS KMS**
**AWS CLI Command:**
```bash
aws kms rotate-key --key-id alias/my-app-key
```
**Expected Output:**
```json
{
  "KeyId": "arn:aws:kms:us-east-1:123456789012:key/abcd1234-5678-90ef-ghij-klmnopqrstuv",
  "KeySpec": "SYMMETRIC_DEFAULT",
  "DeletionDate": "2025-01-01T00:00:00Z",
  "KeyUsage": "ENCRYPT_DECRYPT"
}
```

---

### **4. Operational Considerations**
- **Key Rotation**:
  - Symmetric keys must rotate every **90–365 days** (NIST SP 800-57).
  - Asymmetric keys (RSA/ECC) require rotation **every 2–4 years**.
- **Performance**:
  - **TDE** adds ~10–20% overhead to I/O operations.
  - **FLE** increases CPU usage by ~5–15% during decryption.
- **Audit Logging**:
  - Log all key access events (e.g., AWS KMS `KeyUsage` audits).

---

### **5. Compliance Checklist**
| **Compliance Standard** | **Key Requirements**                                                                 |
|-------------------------|--------------------------------------------------------------------------------------|
| **PCI DSS 3.2.1**       | Encrypt all PAN (Primary Account Number) data at rest and in transit.               |
| **HIPAA**               | Implement TDE for electronic protected health information (ePHI).                    |
| **GDPR**                | Pseudonymize PII (e.g., FLE for personal identifiers).                             |
| **FIPS 140-2/3**        | Use validated cryptographic modules (e.g., AWS Nitro Enclaves, Azure Confidential VMs). |

---

### **6. Related Patterns**
- **[Zero Trust Architecture](https://example.com/zero-trust)**: Combines encryption with micro-segmentation.
- **[Data Masking](https://example.com/data-masking)**: Complements FLE by hiding sensitive data in logs/backups.
- **[Tokenization](https://example.com/tokenization)**: Replaces PII with non-sensitive tokens (e.g., PCI DSS tokenization).
- **[Secure Multi-Party Computation (MPC)](https://example.com/mpc)**: Enables encrypted data processing without decryption.

---
**Last Updated**: `[Insert Date]`
**Version**: `1.3`