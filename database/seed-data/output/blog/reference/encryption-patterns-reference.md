# **[Encryption Patterns] Reference Guide**

---
## **Overview**
The **Encryption Patterns** reference guide provides best practices for securing data in transit and at rest using standardized encryption methods. These patterns ensure confidentiality, integrity, and compliance with security standards like **PCI-DSS, GDPR, and HIPAA**. The guide covers key concepts, schema reference, implementation steps, query examples (where applicable), and related security patterns for modern applications (web, mobile, APIs, databases).

---

## **1. Key Concepts**
Encryption Patterns define how to apply cryptographic techniques to protect sensitive data. The core components include:

| **Component**          | **Description**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Symmetric Encryption** | Single key for encryption/decryption (e.g., AES-256). Fast but requires secure key management.   |
| **Asymmetric Encryption** | Public/private key pair (e.g., RSA, ECC). Used for key exchange or digital signatures.            |
| **Hashing**             | One-way transformation (e.g., SHA-256) for verifying data integrity (e.g., passwords).            |
| **Hybrid Encryption**   | Combines symmetric (data) + asymmetric (key exchange) for efficiency and security.               |
| **Key Management**      | Secure storage, rotation, and access control (e.g., AWS KMS, HashiCorp Vault).                     |
| **Data in Transit**     | TLS/SSL for HTTPS, VPN, or mutual TLS (mTLS) for secure communication channels.                 |
| **Data at Rest**        | Encrypting databases (e.g., PostgreSQL TDE), file systems (e.g., BitLocker), or S3 buckets.      |

---

## **2. Pattern Schemas**
Below are common encryption patterns with their configurations and use cases.

### **Schema: Symmetric Encryption (AES-256)**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Algorithm`             | String         | Cipher algorithm (e.g., AES-256, GCM).                                                              | `"AES-256-GCM"`                      |
| `Key`                   | Byte[]         | 32-byte key (base64-encoded). Must be securely stored (e.g., in a key vault).                       | `Base64("YOUR_256_BIT_KEY_HERE")`    |
| `IV` (Initialization Vector) | Byte[]   | Random 12/16-byte vector per encryption session (for GCM, optional).                                | `Base64("IV_RANDOM_BYTES")`           |
| `Salt` (Optional)       | Byte[]         | For key derivation (e.g., PBKDF2) to protect against rainbow table attacks.                       | `Base64("SALT_VALUE")`                |
| `Data`                  | Byte[]         | Plaintext bytes to encrypt.                                                                          | `Base64("user_data")`                |
| **Output**              | Byte[]         | Encrypted ciphertext (IV + ciphertext in most modes).                                               | `Base64("ENCRYPTED_DATA")`            |

**Use Case:**
Encrypting sensitive fields (e.g., PII) in a database or API response.

---

### **Schema: Asymmetric Encryption (RSA-OAEP)**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Public Key`            | String         | Base64-encoded RSA public key (PEM format).                                                          | `-----BEGIN PUBLIC KEY-----...`      |
| `Private Key`           | String         | Base64-encoded RSA private key (PEM format). **Never expose this in code.**                          | `-----BEGIN PRIVATE KEY-----...`     |
| `Algorithm`             | String         | Encryption padding (e.g., RSA-OAEP, RSA-PKCS1).                                                       | `"RSA-OAEP"`                         |
| `Data`                  | Byte[]         | Plaintext bytes to encrypt (max ~256 bytes for RSA).                                                | `Base64("message")`                  |
| **Output**              | Byte[]         | Encrypted ciphertext (base64).                                                                       | `Base64("ENCRYPTED_BY_RSA")`         |

**Use Case:**
Encrypting small tokens (e.g., JWT claims) or exchanging symmetric keys (e.g., in TLS handshakes).

---
### **Schema: Hybrid Encryption (AES + RSA)**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `AES Key (Symmetric)`   | Byte[]         | 32-byte AES key derived from RSA-encrypted key material.                                              | `Base64("AES_KEY")`                  |
| `RSA Public Key`        | String         | Used to encrypt the AES key before transmission.                                                     | `-----BEGIN PUBLIC KEY-----...`      |
| `Encrypted AES Key`     | Byte[]         | RSA-encrypted AES key (sent over insecure channels).                                                 | `Base64("RSA_ENCRYPTED_AES_KEY")`    |
| `IV`                    | Byte[]         | 16-byte IV for AES-GCM.                                                                             | `Base64("IV")`                       |
| `Data`                  | Byte[]         | Plaintext to encrypt (e.g., API payload).                                                             | `Base64("user_data")`                |
| **Output**              | Object         | `{ encryptedAESKey: "...", iv: "...", ciphertext: "..." }`                                           | `{ encryptedAESKey: "...", ... }`    |

**Use Case:**
Securely sending encrypted data over APIs (e.g., OAuth2 token exchange).

---

### **Schema: Key Derivation (PBKDF2)**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Password`              | String         | User-provided password (never store plaintext).                                                     | `"user_password123"`                  |
| `Salt`                  | Byte[]         | Random 16-byte salt (unique per user).                                                              | `Base64("SALT")`                     |
| `Iterations`            | Integer        | Work factor (e.g., 100,000). Higher = slower (resistant to brute force).                            | `100000`                             |
| `Key Length`            | Integer        | Output key length (e.g., 32 for AES-256).                                                           | `32`                                  |
| `Hash Algorithm`        | String         | Hash function (e.g., SHA-256, bcrypt).                                                             | `"SHA-256"`                          |
| **Output**              | Byte[]         | Derived 32-byte key.                                                                               | `Base64("DERIVED_AES_KEY")`           |

**Use Case:**
Securing passwords or deriving encryption keys from user input.

---
### **Schema: Data in Transit (TLS 1.3)**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Protocol`              | String         | TLS version (e.g., "TLS1.3").                                                                         | `"TLS1.3"`                           |
| `Cipher Suite`          | String         | Suite (e.g., `TLS_AES_256_GCM_SHA384`).                                                             | `"TLS_AES_256_GCM_SHA384"`           |
| `Certificate`           | String         | Base64-encoded X.509 cert (PEM format).                                                              | `-----BEGIN CERTIFICATE-----...`     |
| `Private Key`           | String         | Base64-encoded private key (PEM format). **Securely stored.**                                    | `-----BEGIN PRIVATE KEY-----...`     |
| `Key Log** (Optional)   | String         | For MITM protection (e.g., enterprise PKI).                                                          | `Base64("KEY_LOG")`                  |

**Use Case:**
Securing HTTP traffic (e.g., REST APIs, web apps).

---
### **Schema: Data at Rest (Transparency Data Encryption - TDE)**
| **Field**               | **Type**       | **Description**                                                                                     | **Example**                          |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Table/Column**         | String         | Database object to encrypt (e.g., `users.pin`).                                                     | `"users.pin"`                        |
| `Encryption Key**       | Byte[]         | Database-managed key (or CMK from KMS).                                                             | `Base64("DB_KEY")`                   |
| `Algorithm**            | String         | AES-256-XTS (for disk encryption) or AES-256-CBC (for DB columns).                                | `"AES-256-XTS"`                      |
| `Key Encryption Key (KEK)** | Byte[] | Encrypts the encryption key (e.g., from AWS KMS).                                                   | `Base64("KEK")`                      |

**Use Case:**
Encrypting database columns (e.g., credit cards in PostgreSQL) or disk volumes (e.g., AWS EBS).

---

## **3. Query Examples**
While encryption patterns primarily involve code/configuration, below are examples of how to integrate them:

---

### **Example 1: Encrypting a Field in PostgreSQL (TDE)**
```sql
-- Enable column-level encryption (requires pgcrypto extension)
CREATE EXTENSION pgcrypto;
ALTER TABLE users ALTER COLUMN credit_card ADD ENCRYPTED USING pgp_sym_encrypt(data, 'AES_KEY_HERE');
```
**Output:** The `credit_card` column is encrypted at rest.

---

### **Example 2: Java AES-256-GCM Encryption/Decryption**
```java
import javax.crypto.*;
import javax.crypto.spec.*;
import java.nio.ByteBuffer;
import java.util.Base64;

// Encrypt
public String encrypt(String plaintext, SecretKey key) throws Exception {
    GCMParameterSpec params = new GCMParameterSpec(128, new byte[12]); // 12-byte IV
    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
    cipher.init(Cipher.ENCRYPT_MODE, key, params);
    byte[] ciphertext = cipher.doFinal(plaintext.getBytes());
    byte[] iv = cipher.getIV();
    ByteBuffer buf = ByteBuffer.allocate(iv.length + ciphertext.length);
    buf.put(iv).put(ciphertext);
    return Base64.getEncoder().encodeToString(buf.array());
}

// Decrypt
public String decrypt(String encryptedData, SecretKey key) throws Exception {
    byte[] data = Base64.getDecoder().decode(encryptedData);
    ByteBuffer buf = ByteBuffer.wrap(data);
    byte[] iv = new byte[12];
    buf.get(iv);
    GCMParameterSpec params = new GCMParameterSpec(128, iv);
    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
    cipher.init(Cipher.DECRYPT_MODE, key, params);
    return new String(cipher.doFinal(buf.array()));
}
```

---
### **Example 3: Python RSA-OAEP Encryption**
```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Load public key
public_key = RSA.import_key(open('public_key.pem').read())
cipher = PKCS1_OAEP.new(public_key)

# Encrypt
plaintext = b"sensitive_data"
encrypted = cipher.encrypt(plaintext)
print(base64.b64encode(encrypted).decode('utf-8'))
```
**Output:**
```
ENCODING_OF_RSA_ENCRYPTED_DATA
```

---

### **Example 4: SQL Server Always Encrypted**
```sql
-- Enable Always Encrypted
ALTER DATABASE YourDB SET ENCRYPTION ON;
-- Define column master key
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongPassword123!';
-- Encrypt a column
DECLARE @colEncryptionKey VARBINARY(16);
SELECT @colEncryptionKey = MasterKeyKeyGuid('YourDB');
EXEC sp_add_encrypted_column_key
    @database_name = 'YourDB',
    @schema_name = 'dbo',
    @table_name = 'Users',
    @column_name = 'Email',
    @encryption_key = @colEncryptionKey;
```
**Use Case:** Encrypting sensitive fields in SQL Server without application changes.

---

## **4. Implementation Steps**
### **Step 1: Choose a Pattern**
- **Symmetric:** For bulk data (e.g., databases, files).
- **Asymmetric:** For key exchange or digital signatures.
- **Hybrid:** For APIs or secure messaging.
- **Key Derivation:** For passwords or PINs.
- **TLS:** For network traffic.
- **TDE:** For databases or storage.

### **Step 2: Key Management**
1. **Generate Keys:**
   - Symmetric: Use `secrets` (Python), `BouncyCastle` (Java), or `OpenSSL`.
   - Asymmetric: Use `openssl genpkey` or libraries like `BouncyCastle`.
2. **Store Securely:**
   - **Options:** Hardware Security Modules (HSMs), cloud KMS (AWS KMS, Azure Key Vault), or secrets managers (Vault, AWS Secrets Manager).
   - **Never hardcode keys in code.**
3. **Rotate Keys Periodically:**
   - AES keys: Every 6–12 months.
   - TLS certificates: Every 90–365 days.

### **Step 3: Implement Encryption**
- **In Code:** Use libraries like:
  - **Java:** BouncyCastle, javax.crypto.
  - **Python:** `cryptography`, `PyCryptoDome`.
  - **Node.js:** `crypto` module.
  - **Go:** `crypto` package.
- **In Databases:**
  - PostgreSQL: `pgcrypto`, TDE.
  - SQL Server: Always Encrypted.
  - MySQL: `AES_ENCRYPT()` (limited; prefer application-level).

### **Step 4: Secure Transmission**
- **TLS:** Enforce TLS 1.2+ in all services (use modern cipher suites like `TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384`).
- **HTTPS:** Redirect `http` → `https` in web servers (Nginx, Apache).
- **APIs:** Use mutual TLS (mTLS) for service-to-service communication.

### **Step 5: Validate Integrity**
- **Hashing:** Use SHA-256 for checksums (e.g., verify file integrity).
- **HMAC:** For authenticated encryption (e.g., `AES-GCM` with HMAC).

### **Step 6: Testing**
- **Penetration Testing:** Test against brute force (e.g., slow hash functions like Argon2).
- **Key Escrow:** Ensure recovery procedures exist for lost keys.
- **Compliance Audits:** Validate PCI-DSS (tokenization), GDPR (right to erasure), or HIPAA.

---
## **5. Query Examples (APIs)**
### **Example: Encrypted API Response (Hybrid Encryption)**
**Request:**
```http
POST /api/data HTTP/1.1
Content-Type: application/json
Authorization: Bearer RSA_ENCRYPTED_AES_KEY
```

**Response:**
```json
{
  "iv": "AQIDBA==",
  "ciphertext": "U2FsdGVkX1+...",
  "timestamp": "2023-10-01T00:00:00Z"
}
```
**Steps:**
1. Client decrypts `RSA_ENCRYPTED_AES_KEY` with their private key.
2. Uses the AES key to decrypt `ciphertext` with `iv`.

---

### **Example: JWT with Encrypted Claims**
```json
{
  "header": {
    "alg": "RSA-OAEP-256",
    "enc": "A256GCM"
  },
  "protected": "base64url(headers + claims)",
  "iv": "IV_BASE64",
  "ciphertext": "ENCRYPTED_CLAIMS_BASE64",
  "tag": "AUTH_TAG_BASE64"
}
```
**Use Case:** Encrypt sensitive JWT claims (e.g., `user_id`, `credit_card`).

---
## **6. Related Patterns**
| **Pattern**               | **Description**                                                                                     | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| **Hashing Patterns**      | Securely store passwords using bcrypt, Argon2, or PBKDF2.                                         | User authentication systems.              |
| **Tokenization**          | Replace sensitive data (e.g., credit cards) with tokens.                                          | PCI-DSS compliance.                       |
| **Secure Session**        | Use tokens (JWT, cookies) with short expiration and refresh tokens.                               | Web/mobile applications.                 |
| **Key Rotation**          | Automatically rotate encryption keys without downtime.                                             | Long-term key management.                |
| **Zero-Knowledge Proofs** | Prove knowledge of a secret (e.g., password) without revealing it.                                 | Advanced authentication (e.g., ZK-SNARKs).|
| **HSM Integration**       | Offload cryptographic operations to a hardware security module.                                   | High-security environments (e.g., banking).|
| **Attribute-Based Encryption (ABE)** | Encrypt data with access policies (e.g., "only HR can see salaries").                            | Fine-grained data access control.        |

---
## **7. Security Considerations**
1. **Key Management:**
   - Use **HSMs** for high-security environments.
   - Avoid reinventing wheel; leverage **managed KMS** (AWS KMS, Azure Key Vault).
2. **Performance:**
   - Symmetric encryption is faster than asymmetric (avoid RSA for bulk data).
   - Use **AEAD modes** (e.g., AES-GCM) for authenticated encryption.
3. **Compliance:**
   - **PCI-DSS:** Tokenize PANs (Primary Account