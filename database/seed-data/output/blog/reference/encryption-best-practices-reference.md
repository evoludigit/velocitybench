# **[Pattern] Encryption Best Practices Reference Guide**

## **Overview**
This guide provides a structured approach to implementing robust encryption in software systems, focusing on confidentiality, integrity, and resilience against modern threats. It covers **key management, algorithm selection, implementation strategies, and operational best practices**, ensuring compliance with industry standards (e.g., NIST SP 800-57, RFC 7518). Best practices include leveraging **asymmetric cryptography for key exchange**, **symmetric cryptography for bulk data**, **proper key rotation**, and **secure storage mechanisms**. Follow this guide to minimize exposure to data breaches and regulatory penalties.

---

## **Key Concepts & Implementation Guidelines**

### **1. Classification of Data Classes**
Encryption requirements vary by data sensitivity. Classify data as follows:

| **Data Class**       | **Definition**                                                                 | **Encryption Requirements**                                                                 |
|----------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| **Confidential**     | Sensitive PII, financial, or proprietary data.                               | **AES-256-GCM**, **ChaCha20-Poly1305** (symmetric), **RSA-4096/ECC** (key exchange).       |
| **Internal**         | Non-sensitive but protected (e.g., HR records).                              | **AES-128-CBC** (with HMAC), **ECDHE** (TLS).                                             |
| **Public/Anonymous** | Non-sensitive or anonymized data.                                            | **No encryption** (if anonymized) or **lightweight** (e.g., **AES-128** for limited use).    |

---
### **2. Cryptographic Algorithms & Modes**
Use **NIST-approved** algorithms and modes to avoid vulnerabilities. Prioritize **forward secrecy** and **authenticated encryption**.

| **Algorithm Type**   | **Recommended Algorithms**                                                                 | **Avoid**                                                                 |
|----------------------|-------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Symmetric**        | AES-256-GCM (preferred), AES-128-CBC-HMAC-SHA256, ChaCha20-Poly1305 (mobile/IoT).        | DES, 3DES, CBC without HMAC, RC4.                                         |
| **Asymmetric**       | RSA-4096 (signing), RSA-3072 (encryption), ECC (P-384, P-521).                          | RSA < 2048, Diffie-Hellman (DH) without ECDH/EPHEM.                         |
| **Key Derivation**   | **Argon2id** (preferred), PBKDF2 (legacy), bcrypt.                                      | MD5, SHA-1, scrypt (if not tuned for memory hardness).                     |
| **Hashing**          | SHA-3-256, SHA-3-512, BLAKE3.                                                          | SHA-1, MD5.                                                                 |

---
### **3. Key Management**
**Principle:** *Never hardcode keys. Rotate keys periodically.*

#### **Key Hierarchy**
```
Root Key (HSM/Cloud KMS)
│
├── Data Encryption Keys (DEK) [per app/service]
│   ├── Master Key (MX) [for DEK encryption]
│   └── Ephemeral Keys (EK) [short-lived, per session]
│
└── Authentication Keys (AK) [signing, HMAC]
```

#### **Key Storage & Rotation**
| **Key Type**       | **Storage Method**                          | **Rotation Policy**                          | **Backup**                     |
|--------------------|--------------------------------------------|---------------------------------------------|--------------------------------|
| **Root Key**       | **HSM** (Hardware Security Module) or **Cloud KMS** (AWS KMS, Azure Key Vault). | Annual (or after breach). | Redundant HSM or offline backup (escrowed). |
| **DEK/MX**         | **Encrypted at rest** (AES-256 wrapped with Root Key). | Quarterly. | Encrypted backup (immutable storage). |
| **Ephemeral Keys** | **In-memory** (cleared post-use).          | Per session or hourly.                    | None.                          |
| **Api Keys**       | **Secrets Manager** (e.g., AWS Secrets).   | 90-day max.                                | Rotate automatically.          |

---
### **4. Implementation Strategies**
#### **A. Data-at-Rest Encryption**
- **Databases:** Use **TDE (Transparent Data Encryption)** with **AES-256**.
  - **PostgreSQL:** `pgcrypto` or `AWS KMS` integration.
  - **MongoDB:** Field-level encryption with **Client-Side Field-Level Encryption (CSFLE)**.
- **Filesystems:** **LUKS** (Linux) or **BitLocker** (Windows).
- **Cloud Storage:** Enable **S3 Server-Side Encryption (SSE-KMS)** or **Google Cloud KMS**.

#### **B. Data-in-Transit Encryption**
- **Transport Layer Security (TLS 1.3):** Enforce **TLS 1.3** with **ECDHE key exchange**.
  Example cipher suite: `TLS_AES_256_GCM_SHA384`.
  - Disable **TLS < 1.2** and **outdated ciphers** (e.g., RC4, SHA-1).
  - Use **certificate pinning** for mobile apps.
- **VPNs:** WireGuard (ChaCha20-Poly1305) or OpenVPN (TLS 1.3).

#### **C. Code-Level Encryption**
- **Libraries:**
  - **Node.js:** `crypto` module (AES-GCM), `tweetnacl` (ChaCha20).
  - **Python:** `pycryptodome` (AES-GCM), `cryptography` library.
  - **Java:** `Bouncy Castle` (ECC/RSA), `javax.crypto`.
  - **Go:** `crypto/aes`, `golang.org/x/crypto/nacl` (ChaCha20).
- **Best Practices:**
  - **Never log keys** or plaintext data.
  - **Use constant-time comparisons** (e.g., `timingSafeEqual` for passwords).
  - **Validate all crypto inputs** (prevent padding/oracle attacks).

#### **D. Secure Key Exchange**
- **Protocols:**
  - **TLS 1.3** (for HTTPS, APIs).
  - **Signal Protocol** (for messaging apps).
  - **OpenPGP** (email encryption).
- **Avoid:** Custom Diffie-Hellman or weak ECDH groups (e.g., secp256r1).

#### **E. Password Hashing**
| **Use Case**               | **Algorithm**               | **Parameters**                          | **Example**                          |
|----------------------------|----------------------------|----------------------------------------|--------------------------------------|
| General authentication     | Argon2id                   | Memory=64MB, Iterations=3, Parallelism=4 | `bcrypt` (legacy)                     |
| Low-security scenarios     | bcrypt                     | Cost=12                                | `PBKDF2-HMAC-SHA256` (if no Argon2)  |
| Password storage           | Argon2id or bcrypt         | As above                               |                                      |

---
### **5. Operational Security**
- **Key Escrow:** Store encrypted backups of Root Keys with a **trusted third party** (e.g., law enforcement access for compliance).
- **Key Auditing:** Log all key access (who, when, why) and rotate keys post-incident.
- **Incident Response:**
  1. **Revoke compromised keys** immediately.
  2. **Rotate all derived keys**.
  3. **Re-encrypt affected data**.
- **Compliance:**
  - **GDPR:** Encrypt PII "by design."
  - **HIPAA:** Encrypt ePHI at rest and in transit.
  - **PCI DSS:** Encrypt cardholder data.

---
### **6. Common Pitfalls & Mitigations**
| **Pitfall**                          | **Mitigation**                                                                 |
|---------------------------------------|---------------------------------------------------------------------------------|
| Hardcoded keys                       | Use **secrets management** (Vault, AWS Secrets).                               |
| Weak key derivation (e.g., MD5)       | Use **Argon2id** or **PBKDF2 with 100k+ iterations**.                         |
| Reusing keys                         | Implement **automatic key rotation**.                                          |
| No forward secrecy                   | Use **Ephemeral keys** (e.g., ECDHE in TLS).                                   |
| Side-channel attacks (e.g., timing)  | Use **constant-time algorithms** (e.g., OpenSSL’s `EVP_DecryptFinal` API).   |
| Insecure key wrapping                | Use **AES-GCM** for authenticated encryption.                                 |

---

## **Schema Reference**
### **1. Encryption Key Schema (JSON Example)**
```json
{
  "key_id": "str(uuid)",
  "key_type": "enum('root', 'dek', 'ephemeral', 'api')",
  "algorithm": "enum('AES-256-GCM', 'RSA-4096', 'ECDHE-P256')",
  "created_at": "datetime",
  "expiry_date": "datetime|null",
  "status": "enum('active', 'revoked', 'rotated')",
  "storage": {
    "location": "enum('hsm', 'kms', 'memory', 'vault')",
    "wrapped_key": "base64|null"  // Only present if stored encrypted
  },
  "access_log": [
    {
      "who": "str",          // User/system identifier
      "when": "datetime",
      "action": "enum('generate', 'access', 'rotate', 'revoke')"
    }
  ]
}
```

### **2. Encryption Policy Schema**
```json
{
  "policy_id": "str(uuid)",
  "data_class": "enum('confidential', 'internal', 'public')",
  "encryption": {
    "at_rest": {
      "algorithm": "str",
      "key_rotation": "int(days)"  // e.g., 90
    },
    "in_transit": {
      "protocol": "enum('tls_1.3', 'wireguard')",
      "cipher_suite": "str"
    },
    "key_management": {
      "hsm_required": "bool",
      "backup": "enum('immutable', 'escrowed')"
    }
  },
  "compliance": [
    "str"  // e.g., ["GDPR", "HIPAA"]
  ]
}
```

---

## **Query Examples**
### **1. Query Keys Due for Rotation (SQL)**
```sql
SELECT
    key_id,
    key_type,
    created_at,
    expiry_date
FROM keys
WHERE
    expiry_date < CURRENT_DATE
    AND status = 'active';
```

### **2. Audit Key Access (PostgreSQL)**
```sql
SELECT
    k.key_id,
    k.key_type,
    a.who,
    a.when,
    a.action
FROM keys k
JOIN access_logs a ON k.key_id = a.key_id
WHERE k.status = 'active'
ORDER BY a.when DESC
LIMIT 100;
```

### **3. Validate TLS Configuration (OpenSSL)**
```bash
openssl s_client -connect example.com:443 -tls1_3 -servername example.com | \
    openssl x509 -noout -dates -issuer
```
**Expected Output:**
```
notBefore=Sep  1 00:00:00 2023 GMT
notAfter=Sep  1 23:59:59 2024 GMT
issuer: /C=US/O=Let's Encrypt/...
```
*(Ensure `notAfter` is ≥ 13 months from issuance per RFC 5280.)*

### **4. Test Key Derivation (Python)**
```python
from passlib.hash import argon2

# Correct usage
hashed = argon2.hash("secure_password")
print(argon2.verify("secure_password", hashed))  # True

# Vulnerable (avoid)
import hashlib
hashed_bad = hashlib.sha1("password").hexdigest()  # Never use SHA-1 for hashing!
```

---

## **Related Patterns**
1. **[Secure Key Management]** – Detailed guide on HSMs, KMS, and key rotation.
2. **[Zero Trust Architecture]** – Integrate encryption with identity verification.
3. **[Post-Quantum Cryptography]** – Prepare for quantum-resistant algorithms (e.g., **CRYSTALS-Kyber**, **Sabre**).
4. **[Secure APIs]** – Encrypt API traffic with TLS + JWT (signed with asymmetric keys).
5. **[Tokenization]** – Replace sensitive data with non-sensitive tokens (e.g., PCI DSS compliance).
6. **[Secure Logging]** – Encrypt log files and use **Federated Learning** for anonymization.
7. **[Hardware Security Modules (HSMs)]** – Deep dive into HSM deployment (e.g., AWS CloudHSM, Thales).

---
## **Further Reading**
- [NIST SP 800-57 Part 1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57pt1r5.pdf)
- [RFC 7518 (JKU/JWE/JWE)](https://datatracker.ietf.org/doc/html/rfc7518)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [Google’s Best Practices for TLS](https://developers.google.com/web/fundamentals/security/encrypt-in-transit/overview#tls_versions)