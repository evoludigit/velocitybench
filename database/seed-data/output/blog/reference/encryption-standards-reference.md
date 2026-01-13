# **[Pattern] Encryption Standards Reference Guide**

---

## **Overview**
This reference guide provides a structured breakdown of the **Encryption Standards** pattern, detailing best practices for secure data protection. Encryption ensures confidentiality, integrity, and authenticity by transforming plaintext into unreadable ciphertext using cryptographic algorithms. This pattern outlines key concepts, implementation standards (e.g., **AES, RSA, TLS**), and compliance requirements. Whether designing APIs, databases, or storage systems, adhering to these standards mitigates risks like data breaches and unauthorized access.

Key aspects covered:
- **Standardized algorithms** (symmetric/asymmetric) and their use cases.
- **Key management** (generation, storage, rotation).
- **Protocol compliance** (TLS, SSH, IPsec).
- **Validation and testing** for security assurance.

---

## **Schema Reference**
Below is a **standardized schema** for encryption configurations in common systems:

| **Component**          | **Field**               | **Description**                                                                 | **Example Values**                          |
|------------------------|-------------------------|---------------------------------------------------------------------------------|---------------------------------------------|
| **Encryption Algorithm** | Algorithm Type          | Symmetric (e.g., AES, ChaCha20) or asymmetric (e.g., RSA, ECC).               | `AES-256-CBC`, `RSA-4096`                  |
|                        | Key Size (bits)         | Minimum recommended key length for security.                                     | `256`, `3072`                               |
| **Key Management**     | Key Storage             | Secure vault (HSM, AWS KMS) or encrypted database.                              | `AWS KMS`, `Azure Key Vault`                |
|                        | Key Rotation Policy     | Time-based (e.g., every 90 days) or event-based (e.g., after breach).            | `90d`, `on-breach`                          |
| **Data Protection**    | Ciphertext Format       | Padding (e.g., PKCS#7) or mode (e.g., GCM for authenticated encryption).      | `AES-GCM`, `PKCS#7`                         |
| **Protocols**          | Transport Protocol      | TLS, SSH, or IPsec for network encryption.                                      | `TLS 1.3`, `SSH-2`                         |
|                        | Authentication           | Certificates (X.509), passwords, or hardware tokens for key access.              | `X.509`, `OAuth2`                           |
| **Validation**         | Compliance Standard     | Industry regulations (e.g., **FIPS 140-2**, **NIST SP 800-57**).                  | `FIPS 140-2 Level 3`, `HIPAA`               |
|                        | Penetration Testing     | Tools to audit encryption (e.g., OpenSSL, Nmap).                                | `OpenSSL`, `Burp Suite`                     |

---

## **Implementation Details**
### **Key Concepts**
1. **Symmetric Encryption**:
   - Same key for encryption/decryption (faster, e.g., **AES-256**).
   - Use for bulk data (e.g., databases, files).
   - **Risk**: Key distribution; mitigated by deriving keys from passwords (PBKDF2).

2. **Asymmetric Encryption**:
   - Public/private key pairs (slower, e.g., **RSA, ECC**).
   - Use for secure key exchange or digital signatures.
   - **Risk**: Key length (e.g., **RSA-2048** is vulnerable to quantum attacks).

3. **Hybrid Encryption**:
   - Combines symmetric (AES) and asymmetric (RSA) for efficiency + security.
   - Example: RSA encrypts an AES key; AES encrypts the data.

4. **Hashing**:
   - One-way functions (e.g., **SHA-3**) for integrity checks, not encryption.

---

### **Common Standards**
| **Standard**            | **Purpose**                          | **Example Use Cases**                     |
|-------------------------|--------------------------------------|-------------------------------------------|
| **AES-256**             | Symmetric block cipher.              | Disk encryption, VPNs.                    |
| **TLS 1.3**             | Secure web traffic.                  | HTTPS, APIs.                              |
| **RSA-OAEP**            | Asymmetric encryption with padding.  | Secure emails, SSH keys.                  |
| **NIST SP 800-57**      | Key management guidelines.           | Federal systems (U.S.).                  |
| **FIPS 140-2**          | Cryptographic module validation.     | Hardware security modules (HSMs).         |

---

### **Best Practices**
- **Key Generation**:
  - Use **CSPRNG** (e.g., `/dev/urandom` in Linux) for randomness.
  - Avoid predictable keys (e.g., sequential numbers).

- **Storage**:
  - Encrypt keys at rest (e.g., **AWS KMS**, **Azure Key Vault**).
  - Restrict access via **least privilege** (e.g., IAM roles).

- **Rotation**:
  - Rotate keys **automatically** (e.g., cloud services) or via scripts.
  - Use **HSMs** for hardware-based key storage.

- **Ciphertext Handling**:
  - Never log raw ciphertext; store only encrypted blobs.
  - Use **authenticated encryption** (e.g., AES-GCM) to detect tampering.

- **Compliance**:
  - Audit logs with **NIST SP 800-66** for incident response.
  - Validate vendors for **Common Criteria** or **FIPS compliance**.

---

## **Query Examples**
### **1. Generating an AES-256 Key (Python)**
```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key = get_random_bytes(32)  # 256-bit key
iv = get_random_bytes(16)   # Initialization vector

cipher = AES.new(key, AES.MODE_CBC, iv)
ciphertext = cipher.encrypt(b"Sensitive Data")
```

### **2. TLS Configuration (OpenSSL)**
```bash
# Generate RSA key (2048-bit)
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048

# Create self-signed cert for testing
openssl req -new -x509 -key private_key.pem -out cert.pem -days 365
```

### **3. Querying Encrypted Data (SQL)**
```sql
-- Example: Decrypt column in PostgreSQL using pgcrypto
SELECT pgp_sym_decrypt(
    data_column,
    'AES-256_KEY_HERE',
    'gcm'
) FROM encrypted_table;
```

### **4. Validating TLS with OpenSSL**
```bash
openssl s_client -connect example.com:443 -servername example.com | openssl x509 -noout -dates
# Check for valid expiration dates.
```

---

## **Related Patterns**
1. **[Key Management Service (KMS) Pattern]**
   - Centralized key management for scalable encryption.
   - *Use when*: Managing keys across multiple services/apps.

2. **[Secure Communication Pattern]**
   - Ensures end-to-end encryption (e.g., **TLS 1.3**, **Signal Protocol**).
   - *Use when*: Building client-server APIs with privacy requirements.

3. **[Data Masking Pattern]**
   - Anonymizes sensitive data in logs/databases.
   - *Use when*: Compliance needs (e.g., **GDPR**).

4. **[Zero-Trust Security Pattern]**
   - Combines encryption with identity verification (e.g., **OAuth2 + TLS**).
   - *Use when*: High-security environments (e.g., healthcare, finance).

5. **[Blockchain-Based Encryption]**
   - Immutable key storage via smart contracts.
   - *Use when*: Decentralized applications (dApps) require audit trails.

---
**References**:
- [NIST Special Publication 800-57](https://csrc.nist.gov/publications/detail/sp/800-57/final)
- [FIPS 140-2 Validation](https://csrc.nist.gov/projects/cryptographic-module-validation-program)
- [OWASP Encryption Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Encryption_Cheat_Sheet.html)