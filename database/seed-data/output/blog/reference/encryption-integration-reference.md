# **[Pattern] Encryption Integration – Reference Guide**

---
## **Overview**
This guide provides a structured approach to integrating encryption into systems, ensuring data confidentiality, compliance, and security. The **Encryption Integration** pattern standardizes how encryption (symmetric, asymmetric, or hybrid) is applied to sensitive data at rest, in transit, and in use. It clarifies roles, key management, and encryption boundaries while offering best practices for seamless integration into applications, APIs, and databases.

Best for:
- Securing sensitive data (e.g., PII, payment details, tokens).
- Compliance with regulations (GDPR, HIPAA, PCI-DSS).
- Hybrid cloud or multi-cloud environments.

**Key Considerations:**
- **Performance:** Encryption/decryption adds overhead; optimize algorithms (e.g., AES-256 for speed vs. RSA for key exchange).
- **Key Management:** Use dedicated systems (e.g., AWS KMS, HashiCorp Vault) to avoid hardcoded keys.
- **Compatibility:** Align encryption methods with client/server libraries (e.g., OpenSSL, .NET Crypto, libsodium).

---
## **Schema Reference**

| **Component**               | **Description**                                                                 | **Example Technologies**                          | **Required?** |
|-----------------------------|---------------------------------------------------------------------------------|---------------------------------------------------|----------------|
| **Encryption Algorithm**    | Symmetric (e.g., AES) for bulk data, asymmetric (e.g., RSA/ECC) for keys.     | AES-256, RSA-2048, ChaCha20                       | Yes            |
| **Key Management System**   | Centralized service to generate, rotate, and revoke keys.                        | AWS KMS, HashiCorp Vault, Azure Key Vault         | Yes            |
| **Data Storage Layer**      | Database/API where encrypted data is stored.                                    | PostgreSQL, MongoDB, RESTful APIs                | Yes            |
| **Encryption Wrapper**      | Library/module to encrypt/decrypt data before storage/transmission.             | Python `cryptography`, .NET `System.Security.Crypto`, OpenSSL | Yes |
| **Key Exchange Protocol**   | Secure method to share encryption keys (e.g., TLS for keys-in-transit).         | TLS 1.3, Signal Protocol                          | Conditional*   |
| **Data Masking**            | Tokens or obfuscation for non-sensitive queries (e.g., analytics).              | PostgreSQL `pgcrypto`, DynamoDB Conditional Encryption | Optional |
| **Audit Logs**              | Track access to encrypted data and key usage.                                   | AWS CloudTrail, Splunk, ELK Stack                | Highly Recommended |

*Required for dynamic key distribution (e.g., ephemeral keys).

---

## **Implementation Details**

### **1. Core Components**
#### **A. Encryption Algorithm Selection**
| **Use Case**               | **Recommended Algorithm** | **Notes**                                      |
|----------------------------|---------------------------|------------------------------------------------|
| **Data-at-rest**           | AES-256 (GCM mode)        | Balances speed/security; avoid ECB.            |
| **Key Exchange**           | RSA/PSS or ECDH           | Use PSS for signatures, ECDH for key agreement.|
| **Key Wrapping**           | RSA-OAEP or AES-KW        | Prevents key leakage if the master key is compromised. |

#### **B. Key Management**
- **Master Key:** Long-term key stored in a **Hardware Security Module (HSM)** or cloud KMS.
- **Data Encryption Keys (DEKs):** Short-lived keys derived from the master key (e.g., using HMAC-SHA256).
- **Key Rotation:** Rotate DEKs every **90 days** (or per compliance requirements).

**Example Workflow:**
1. **Master Key** → AWS KMS (HSM-backed).
2. **DEK Generation:** `openssl rand -hex 32` → Encrypted with master key.
3. **Encryption:** `AES-256-GCM(DEK, data)` → Store encrypted data + encrypted DEK.

#### **C. Encryption Boundaries**
Define where encryption applies:
- **At Rest:** Encrypt data before storing in databases/APIs.
- **In Transit:** Use TLS 1.2+ for all communications (HTTPS, mTLS).
- **In Use:** Use **Memory-Protected Execution** (e.g., SGX for sensitive operations).

---
### **2. Integration Patterns**
#### **A. Client-Side Encryption**
Encrypt data **before** sending to the server (e.g., mobile apps, browsers).
```python
# Python Example (using `cryptography` library)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def encrypt_data(data: bytes, key: bytes) -> bytes:
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext  # Prepend IV + tag for decryption
```

#### **B. Database-Level Encryption**
Use **Transparent Data Encryption (TDE)** or column-level encryption:
```sql
-- PostgreSQL Example (pgcrypto)
CREATE EXTENSION pgcrypto;
UPDATE users SET encrypted_name = enc(plain_name, 'secret_key');
SELECT dec(encrypted_name, 'secret_key') FROM users;
```

#### **C. API Gateway Encryption**
Encrypt payloads in transit and validate integrity:
```javascript
// Node.js Example (using `@aws-crypto/cdk`)
const encryptedPayload = await encrypt({
  key: awsKmsKey,
  plaintext: JSON.stringify(data),
  context: { api: "users-service" }
});
```

---
### **3. Query Examples**
#### **Encrypting a Database Field**
```sql
-- MySQL (AES_ENCRYPT)
UPDATE customers SET credit_card = AES_ENCRYPT(credit_card, 'dynamic_key');
-- Retrieve (requires key in application logic)
```

#### **TLS for Key Exchange**
```bash
# Generate ECDH keys for secure key exchange
openssl ecparam -genkey -name secp256r1 -out client.key
openssl ecparam -genkey -name secp256r1 -out server.key
```

#### **Audit Key Usage**
```sql
-- Track when a DEK was used (e.g., in PostgreSQL)
INSERT INTO key_usage_log (dek_id, timestamp, user_id)
VALUES (generate_random_uuid(), NOW(), current_user_id());
```

---
## **Query Examples (Pseudocode)**
### **1. Symmetric Encryption (AES)**
```python
# Encrypt
ciphertext = AES_GCM_encrypt(data, key="master_key_128")

# Decrypt
data = AES_GCM_decrypt(ciphertext, key="master_key_128")
```

### **2. Asymmetric Encryption (RSA)**
```python
# Encrypt with public key
ciphertext = RSA_public_encrypt(data, public_key)

# Decrypt with private key
data = RSA_private_decrypt(ciphertext, private_key)
```

### **3. Key Wrapping (AES for DEKs)**
```python
# Wrap a DEK with a master key
wrapped_dek = AES_wrap(dek, master_key)

# Unwrap
dek = AES_unwrap(wrapped_dek, master_key)
```

---
## **Related Patterns**
| **Pattern**                     | **Description**                                                                 | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **[Data Masking]**               | Obfuscate sensitive fields for analytics queries.                                | Non-production environments.                    |
| **[Secure Key Exchange]**        | Ephemeral key agreement (e.g., Diffie-Hellman).                                 | Secure key distribution between services.         |
| **[TLS for APIs]**                | Enforce mTLS for service-to-service communication.                              | Multi-tenant cloud deployments.                  |
| **[Zero-Knowledge Proofs]**      | Verify data without decrypting (e.g., ZK-SNARKs).                               | Privacy-preserving compliance checks.            |
| **[HSM Integration]**             | Use hardware tokens for master key storage.                                    | High-security environments (e.g., financial).   |

---
## **Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                                  |
|-------------------------------------|-----------------------------------------|-----------------------------------------------|
| **High Latency**                    | AES-GCM overhead.                       | Use AES-128 or hardware acceleration (e.g., AWS Nitro). |
| **Key Rotation Failures**           | Dependent services not updated.         | Test rotation in staging; use blue-green deployments. |
| **Compatibility Issues**            | Mixed algorithms (e.g., AES + RSA).    | Standardize on one library (e.g., OpenSSL).     |

---
## **Best Practices**
1. **Minimize Encrypted Data Scope:** Encrypt only what’s necessary.
2. **Key Backup:** Store master key backups offline (e.g., AWS KMS backup to S3).
3. **Performance Testing:** Benchmark encryption/decryption under load.
4. **Compliance Mapping:**
   - **GDPR:** Encrypt PII; log access.
   - **PCI-DSS:** Encrypt cardholder data; use TLS 1.2+.
5. **Chaos Engineering:** Test encryption failures (e.g., lost DEK).

---
**See Also:**
- [NIST SP 800-57](https://csrc.nist.gov/publications/detail/sp/800-57/final) for key management.
- [OWASP Encryption Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Encryption_Cheat_Sheet.html).