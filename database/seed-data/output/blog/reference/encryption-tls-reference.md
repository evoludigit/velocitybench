# **[Pattern] Encryption & TLS/SSL Reference Guide**

---

## **Overview**
This reference guide provides best practices, implementation specifics, and optimizations for securing data using **Encryption** and **Transport Layer Security (TLS)/Secure Sockets Layer (SSL)**. It covers cryptographic fundamentals, key management, protocol selection, and deployment considerations to ensure secure data transmission and storage. Whether for APIs, databases, or cloud services, adherence to this pattern mitigates risks such as eavesdropping, tampering, and authentication breaches.

---

## **Key Concepts**
### **1. Encryption Fundamentals**
| **Term**               | **Definition**                                                                 | **Use Case**                                                                 |
|------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| **Symmetric Encryption** | Uses the same key for encryption/decryption (e.g., AES-256, ChaCha20).       | Fast bulk data encryption (e.g., database fields, stored files).            |
| **Asymmetric Encryption** | Uses a public/private key pair (e.g., RSA, ECC).                          | Secure key exchange (e.g., TLS handshake), digital signatures.              |
| **Hashing**            | One-way function (e.g., SHA-256) to generate fixed-size digests.           | Verifying data integrity (e.g., password storage, checksums).               |
| **Key Derivation**     | Strengthens keys via iterative hashing (e.g., PBKDF2, Argon2).             | Securing passwords or derived keys from master keys.                        |

---
### **2. TLS/SSL Protocols**
| **Protocol**       | **Version** | **Security Notes**                                                                 | **Recommended Usage**                                  |
|--------------------|------------|-------------------------------------------------------------------------------------|------------------------------------------------------|
| TLS 1.2            | Deprecated  | Vulnerable to POODLE, BEAST attacks.                                               | Avoid.                                                  |
| TLS 1.3            | Current    | Optimized for performance (reduced handshake steps), no legacy ciphers.          | **Preferred** for new implementations.             |
| DTLS              | 1.0/1.2    | TLS for **datagrams** (e.g., VoIP, webRTC).                                        | Use when TCP is unavailable.                        |

---
### **3. Cipher Suites**
A **cipher suite** combines encryption, authentication, and key exchange algorithms. Example modern suites:
- **TLS_AES_256_GCM_SHA384** (authenticated encryption)
- **TLS_CHACHA20_POLY1305_SHA256** (performance-focused, for TLS 1.3)
- **TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256** (forward secrecy)

**Avoid**: CBC-mode ciphers (e.g., AES-CBC) due to padding oracle risks.

---
### **4. Key Management**
| **Concept**         | **Details**                                                                                     | **Best Practices**                                              |
|---------------------|-------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| **Master Key**      | Encrypts other keys (e.g., database encryption keys).                                         | Store in **Hardware Security Module (HSM)** or **cloud KMS**. |
| **Transient Keys**  | Short-lived keys (e.g., TLS session keys).                                                    | Rotate automatically (e.g., 1-hour lifetime).                |
| **Key Rotation**    | Periodic replacement of keys to limit exposure.                                                | Rotate every 90–365 days (depends on sensitivity).          |
| **Certificate Lifecycle** | Issue, renew, revoke certificates using **PKI** or **ACME** (Let’s Encrypt). | Use **Short Lived Certificates (SLC)** for better security.  |

---
### **5. Implementation Layers**
#### **A. Data at Rest**
| **Component**       | **Encryption Method**          | **Tools/Libraries**                          |
|---------------------|--------------------------------|---------------------------------------------|
| Database Fields     | AES-256-GCM (transparent data encryption) | PostgreSQL `pgcrypto`, SQL Server TDE      |
| Filesystem          | Full-disk encryption (FDE)     | Windows BitLocker, Linux LUKS               |
| Cloud Storage       | Server-side encryption (SSE)   | AWS KMS, Google Cloud KMS                  |

#### **B. Data in Transit**
| **Use Case**        | **Protocol**   | **Configuration**                                      |
|---------------------|----------------|------------------------------------------------------|
| Web Traffic         | TLS 1.3        | Enable HSTS, use SNI (Server Name Indication).      |
| API Communication   | TLS 1.2+       | Enforce mutual TLS (mTLS) for service-to-service.   |
| Messaging           | DTLS or TLS    | Use TLS 1.3 for WebSockets (e.g., `wss://`).          |

#### **C. Authentication**
| **Method**          | **Description**                                                                 | **Example Libraries**          |
|---------------------|---------------------------------------------------------------------------------|--------------------------------|
| **Mutual TLS (mTLS)** | Both client and server authenticate via certificates.                          | AWS Signer, OpenSSL             |
| **JWT/OAuth2**      | Token-based auth with encrypted payloads (e.g., JWT using AES).                 | `authlib`, `spring-security`  |
| **X.509 Certificates** | Public-key certificates for client/server auth.                               | Java `jssecacerts`, Python `cryptography` |

---

## **Schema Reference**
### **1. TLS Configuration Schema**
```plaintext
TLS_Settings:
  - Protocol: TLS_1_3 | TLS_1_2
  - CipherSuites: ["TLS_AES_256_GCM_SHA384", ...]  # Ordered preference list
  - MinVersion: TLS_1_2
  - Certificate:
      - Path: "/path/to/cert.pem"
      - PrivateKeyPath: "/path/to/key.pem"
      - KeyPassphrase: "optional"
  - KeyExchange: ECDHE | RSA
  - SessionTimeout: 3600  # Seconds (default: 3600)
  - OCSPStapling: true/false
```

### **2. Encryption Key Schema**
```plaintext
Encryption_Key:
  - KeyId: "uuid"
  - Algorithm: AES_256 | ChaCha20
  - RotationPolicy:
      - DaysUntilRotation: 90
      - MaxUses: 1000
  - KeyMaterial: "[base64-encoded]"
  - Purpose: "DB_ENCRYPTION" | "API_KEY"
  - Storage: "HSM" | "AWS_KMS"
```

### **3. PKI Certificate Schema**
```plaintext
Certificate:
  - Subject: "CN=example.com, O=Org"
  - Issuer: "CN=Let’s Encrypt"
  - NotBefore: "2024-01-01T00:00:00Z"
  - NotAfter:  "2024-06-30T23:59:59Z"
  - SerialNumber: "0123456789"
  - SignatureAlgorithm: "SHA256withRSA"
  - SANs: ["example.com", "*.example.com"]
  - Revoked: false/true
```

---

## **Query Examples**
### **1. Verify TLS Configuration**
**Command (OpenSSL):**
```bash
openssl s_client -connect example.com:443 -tls1_3 | openssl x509 -noout -dates -text
```
**Output:**
```
notBefore=Jan  1 00:00:00 2024 GMT
notAfter=Jun 30 23:59:59 2024 GMT
Signature Algorithm: sha256WithRSAEncryption
```
**Check Cipher Suite:**
```bash
openssl s_client -connect example.com:443 -tls1_3 -cipher TLS_AES_256_GCM_SHA384 2>/dev/null | grep "Cipher"
```
**Expected:** `Cipher is TLS_AES_256_GCM_SHA384`

---

### **2. Rotate a Database Encryption Key**
**Using AWS KMS (CLI):**
```bash
aws kms create-alias --alias-name alias/db-key-rotation --target-key-id 1234abcd-5678-efgh-90ij-klmnopqrstuv
aws kms rotate-key --key-id 1234abcd-5678-efgh-90ij-klmnopqrstuv
```
**PostgreSQL (SQL):**
```sql
ALTER ENCRYPTION KEY FOR DATABASE db_name ROTATE 'new_key_arn';
```

---
### **3. Generate a Self-Signed Certificate (Testing)**
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 \
  -nodes -subj "/CN=localhost"
```
**Usage:**
```bash
python3 -m http.server 8000 --bind localhost --cert cert.pem --key key.pem
```

---
### **4. Audit TLS Handshake**
**Use `ssllabs` Scan Tool:**
```bash
curl -I https://example.com | grep "SSL/TLS"
```
**Or:**
```bash
openssl s_server -accept 4433 -cert cert.pem -key key.pem -quiet -debug 2>&1 | grep "Protocol"
```

---

## **Best Practices & Optimizations**
### **1. Performance**
- **Enable Session Resumption**: Use `session_tickets` (TLS 1.3) or `session_ids` (TLS 1.2) to avoid full handshakes.
- **Protocol Selection**: Prefer TLS 1.3 (fewer round-trips, modern ciphers).
- **Cipher Order**: List strongest ciphers first (e.g., `ECDHE` before `RSA`).

### **2. Security**
- **Forward Secrecy**: Use **Ephemeral Diffie-Hellman (ECDHE/DHE)** key exchange.
- **Certificate Pinning**: Mitigate MITM attacks with HTTP Public Key Pinning (HPKP) or **Certificate Transparency**.
- **HSTS**: Enforce HTTPS via `Strict-Transport-Security` header.

### **3. Compliance**
- **GDPR/PCI-DSS**: Encrypt PII and credit card data at rest and in transit.
- **FIPS 140-2**: Use certified HSMs for government/military applications.

### **4. Monitoring**
- **Log TLS Warnings**: Monitor for protocol downgrades (e.g., TLS 1.0).
- **Certificate Expiry Alerts**: Use tools like **Certify the Web** or **Let’s Encrypt’s ACME protocol**.

---

## **Related Patterns**
1. **[Authentication & Authorization]** – Complementary to TLS for access control.
2. **[Secure Coding]** – Prevent cryptographic vulnerabilities (e.g., weak RNG, side-channel attacks).
3. **[API Security]** – Implement TLS for REST/gRPC APIs, combine with OAuth2/JWT.
4. **[Zero Trust]** – Use mTLS for service-to-service communication.
5. **[Data Masking]** – Encrypt PII in logs/databases beyond TLS.

---
## **Resources**
- **[TLS Handbook (Cloudflare)](https://tls.mozillafoundation.org/)**
- **[NIST SP 800-52 (TLS Guide)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-52r2.pdf)**
- **[OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)**

---
**Last Updated:** [YYYY-MM-DD]
**Version:** 1.2