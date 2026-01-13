# **[Pattern] Encryption Setup Reference Guide**

---

## **Overview**
This guide provides a structured approach to **Encryption Setup** within application architectures, ensuring data confidentiality, integrity, and compliance. It details key components, schema validation, query examples, and interoperability with related security patterns.

Encryption Setup involves configuring cryptographic algorithms, key management, and data protection mechanisms. This pattern is critical for securing data at rest, in transit, or within databases. Implementation requires balancing security strength with performance and operational overhead. Below, we outline the core elements and best practices for encryption configurations.

---

## **1. Key Concepts**
| **Term**               | **Definition**                                                                                                      | **Use Case**                                                                                     |
|------------------------|------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| **Symmetric Encryption** | Uses a single key for encryption/decryption (e.g., AES-256).                                                     | Encrypting bulk data, secrets, or large volumes of unclassified data.                           |
| **Asymmetric Encryption** | Uses a public/private key pair (e.g., RSA, ECC).                                                                | Secure key exchange, digital signatures, or encrypting small metadata (e.g., TLS handshakes). |
| **Key Management System (KMS)** | Service (e.g., AWS KMS, HashiCorp Vault) for generating, storing, and rotating encryption keys.                | Managing cryptographic keys without exposing them to applications.                                |
| **Cipher Suite**        | Configuration of algorithms and protocols (e.g., AES-GCM, RSA-OAEP).                                           | Defining cryptographic standards for secure communication (e.g., TLS).                            |
| **Data Masking**        | Partial or selective encryption of sensitive fields (e.g., PII, financial data).                                  | Compliance with regulations like GDPR or PCI-DSS.                                                |
| **Transit Encryption**  | Encrypting data *while in transit* (e.g., TLS 1.3 for HTTP).                                                     | Protecting data from interception during network transfers.                                       |
| **Rest Encryption**     | Encrypting data *at rest* (e.g., database tables, storage buckets).                                               | Shielding data from unauthorized access on servers or backups.                                    |

---

## **2. Schema Reference**
Below is a **schema validation template** for an Encryption Setup configuration. Use this as a foundation for your implementation.

### **2.1 Core Schema (JSON/YAML)**
```json
{
  "$schema": "https://your-org/schema/encryption-schema-v1.json",
  "encryption": {
    "enabled": boolean, // true/false (default: true)
    "mode": "symmetric" | "asymmetric" | "hybrid", // Hybrid = asymmetric + symmetric
    "symmetry": {
      "algorithm": "AES-128" | "AES-192" | "AES-256", // Default: AES-256
      "key_rotation": {
        "enabled": boolean, // true/false
        "interval_hours": 720, // Default: 30 days (720h)
        "key_management_system": {
          "type": "AWS_KMS" | "HARSHICORP_VAULT" | "LOCAL_FILE", // Support custom providers
          "endpoint": "string", // e.g., "https://kms.aws-region.amazonaws.com"
          "secret_id": "string" // Key identifier (KMS ARN, Vault path)
        }
      },
      "data_masks": { // Optional: Fields to mask and encrypt
        "pattern": {
          "field_name": "string", // e.g., "ssn_last_four"
          "mask_char": "*",
          "encrypt": boolean // Default: false (mask but don't encrypt)
        }
      }
    },
    "asymmetry": {
      "public_key": "base64_encoded_string", // RSAPublicKey or EC Public Key
      "private_key": "base64_encoded_string", // Securely stored externally (e.g., TLS private key)
      "algorithm": "RSA" | "ECC" // Default: ECC (P-256)
    },
    "transit": {
      "tls": {
        "version": "TLS_1_2" | "TLS_1_3", // Default: TLS_1_3
        "ciphers": ["AES_256_GCM_SHA384", ...], // List of supported ciphers
        "certificate": {
          "path": "string", // Path to PEM file
          "private_key": "string" // Path to private key (if self-signed)
        }
      }
    },
    "rest": {
      "database": {
        "mode": "column-level" | "table-level", // Default: column-level
        "columns": ["column1", "column2"] // List of columns to encrypt
      },
      "storage": {
        "s3_bucket_encryption": boolean, // Default: true (if S3 supported)
        "encryption_key_id": "string" // Optional: Override default KMS key
      }
    }
  },
  "compliance": {
    "audit": boolean, // Log encryption events?
    "audit_trail": string[] // Fields to audit (e.g., ["key_rotation", "data_access"])
  }
}
```

---

## **3. Query Examples**
Below are **pseudo-code snippets** and **API query examples** for configuring encryption.

---

### **3.1 Symmetric Encryption (AES-256)**
```python
# Python example using PyCryptodome
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

key = get_key_from_kms("aws-kms-key-arn")  # Fetch from KMS via your KMS provider
cipher = AES.new(key, AES.MODE_GCM)
plaintext = b"SensitiveData123"
ciphertext, tag = cipher.encrypt_and_digest(plaintext)
# ciphertext: Encrypted blob + nonce + tag (for integrity)
```

```bash
# AWS CLI: Encrypt using KMS
aws kms encrypt \
  --key-id "alias/my-encryption-key" \
  --plaintext "U2VjcmV0Q29sbGFib3g=" \
  --query "CiphertextBlob" \
  --output text
```

---

### **3.2 Asymmetric Encryption (RSA)**
```bash
# OpenSSL example: Encrypt with RSA public key
openssl rsautl -encrypt -inkey public_key.pem -pubin \
  -in "plaintext.txt" -out "encrypted.bin"
```

```python
# Python example using PyCryptodome
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

public_key = RSA.import_key(open("public_key.pem").read()).publickey()
cipher = PKCS1_OAEP.new(public_key)
ciphertext = cipher.encrypt(b"SensitiveData123")
```

---

### **3.3 Transit Encryption (TLS 1.3)**
```bash
# Enable TLS 1.3 on a web server (Nginx example)
server {
  listen 443 ssl http2;
  ssl_certificate /path/to/cert.pem;
  ssl_certificate_key /path/to/key.pem;
  ssl_protocols TLSv1.3;
  ssl_ciphers 'TLS_AES_256_GCM_SHA384';
}
```

```json
# API Gateway (AWS): Force TLS 1.3
{
  "policy_name": "tls-1-3-only",
  "policy": {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": "*",
        "Action": "execute-api:Invoke",
        "Resource": "*",
        "Condition": {
          "StringEquals": {
            "aws:SecureTransport": "tls-1-3"
          }
        }
      }
    ]
  }
}
```

---

### **3.4 Rest Encryption (Database)**
```sql
-- PostgreSQL example: Encrypting a column with pgcrypto
ALTER TABLE users ADD COLUMN ssn_encrypted BYTEA;
UPDATE users SET ssn_encrypted = pgp_sym_encrypt(ssn, 'key_here');

-- Query (returns encrypted blob)
SELECT ssn_encrypted FROM users WHERE id = 1;
```

```python
# SQLAlchemy + cryptography
from sqlalchemy import Column, LargeBinary
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt data before saving
encrypted_data = cipher.encrypt(b"123-45-6789")
```

---

## **4. Implementation Best Practices**
### **4.1 Key Management**
- Use **hardware security modules (HSMs)** for high-security scenarios.
- Rotate keys **automatically** (e.g., 90-day intervals).
- Never hardcode keys in source code; use **KMS/Vault integration**.

### **4.2 Performance**
- **Avoid over-encryption**: Encrypt only sensitive fields (cost/performance trade-off).
- **Use hardware acceleration**: L leveraging AES-NI for faster AES operations.
- **Batch operations**: Encrypt/decrypt in bulk where possible.

### **4.3 Compliance**
- **Audit logs**: Track all encryption/decryption events.
- **Key revival plan**: Ensure keys can be recovered in case of loss.
- **Regulatory checks**: Align with **GDPR (data subject rights)**, **PCI-DSS (payment data)**, or **HIPAA (health records)**.

---

## **5. Related Patterns**
| **Pattern**                 | **Description**                                                                                     | **When to Use**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Authentication & Authorization** | Validates user identity before granting access to encrypted data.                                     | Pair with Encryption Setup for *defense-in-depth*.                                                |
| **Secure Secrets Management** | Stores encryption keys/certificates in a secure vault (e.g., HashiCorp Vault).                  | When keys need to be shared across microservices.                                                  |
| **Zero-Trust Networking**   | Assumes no implicit trust; enforces encryption at every hop.                                         | Cloud-native applications with dynamic workloads.                                                 |
| **Data Masking**            | Redacts sensitive data in logs/debugging (e.g., `ssn: ***-**-****1234`).                           | Compliance requirements for logging/reporting.                                                        |
| **Hardware Security Module (HSM)** | Provides tamper-resistant key storage and cryptographic operations.                                   | High-security environments (e.g., financial systems, government).                                   |
| **Tokenization**            | Replaces sensitive data (e.g., credit cards) with tokens.                                           | PCI-DSS compliance for payment processing.                                                          |

---

## **6. Troubleshooting**
| **Issue**                          | **Solution**                                                                                     |
|-------------------------------------|-------------------------------------------------------------------------------------------------|
| **Key rotation failure**           | Verify KMS/Vault connectivity and permissions.                                                    |
| **Performance degradation**        | Check for CPU-bound encryption; use hardware acceleration or reduce scope.                      |
| **TLS handshake errors**           | Ensure client/server ciphers match (e.g., `openssl s_client -connect`).                          |
| **Database encryption corruption** | Validate column types (e.g., `BYTEA` in PostgreSQL) and padding schemes.                         |
| **Compliance audit failures**      | Review `audit_trail` logs for missing events (e.g., key access).                                  |

---

## **7. Further Reading**
- [NIST Special Publication 800-57 (Recommended Cryptographic Algorithms)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57.1r5.pdf)
- [OWASP Encryption Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Encryption_Cheat_Sheet.html)
- [AWS KMS Developer Guide](https://docs.aws.amazon.com/kms/latest/developerguide/)
- [PostgreSQL pgcrypto Module](https://www.postgresql.org/docs/current/pgcrypto.html)