# **[Pattern] Encryption Validation – Reference Guide**

---
## **Overview**
Encryption Validation is a **security pattern** designed to ensure that encrypted data is **authentic, intact, and unmodified** after decryption. This pattern is critical for **end-to-end encryption (E2EE), distributed systems, and sensitive data transmission** (e.g., APIs, databases, or storage). It prevents **man-in-the-middle (MITM) attacks, tampering, and data corruption** by leveraging **cryptographic hashes (HMACs) or digital signatures** alongside encrypted payloads.

This guide covers:
- **Key concepts** (hashing, HMAC, digital signatures).
- **Implementation schemas** (JSON, XML, or binary formats).
- **Practical examples** (HTTP headers, database validation).
- **Integration with related security patterns** (e.g., JWT, PKI).

---

## **1. Key Concepts**
Before implementing, understand these core principles:

| **Term**               | **Definition**                                                                                     | **Example Use Case**                          |
|------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------|
| **HMAC (Hash-Based Message Authentication Code)** | A cryptographic hash function (e.g., SHA-256) combined with a secret key to verify message integrity. | Validating API request payloads.       |
| **Digital Signature**  | A cryptographic scheme using private keys (e.g., RSA, ECDSA) to prove message authenticity.       | Secure email or blockchain transactions.    |
| **Salt + Pepper**      | Additional random data mixed with keys to prevent rainbow table attacks.                          | Password hashing in databases.                |
| **Nonce**              | A one-time-use value to prevent replay attacks in symmetric encryption.                           | HTTPS session tokens.                       |
| **Key Rotation**       | Periodically replacing cryptographic keys to limit exposure if compromised.                        | AWS KMS or Azure Key Vault.                  |

---

## **2. Implementation Schema**
The validation schema depends on the encryption method (symmetric/asymmetric) and use case. Below are standard formats:

### **2.1. Schema for HMAC-Based Validation**
Used when both parties share a secret key (e.g., API clients/servers).

| **Field**         | **Type**       | **Description**                                                                                     | **Example Format**                          |
|-------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `encryptedPayload` | `base64`       | The ciphertext of the original data.                                                               | `"AQIDBAUGBwg..."`                          |
| `hmac`            | `hex`          | HMAC-SHA256 of `(encryptedPayload + secretKey)`.                                                   | `"3a7b4c9d..."`                             |
| `nonce`           | `uint64`       | Prevents replay attacks (optional but recommended).                                               | `1234567890`                                |
| `timestamp`       | `ISO 8601`     | Ensures freshness (prevents stale data).                                                          | `"2024-05-20T12:00:00Z"`                   |
| `algorithm`       | `string`       | Specifies crypto parameters (e.g., `"AES-256-CBC/HMAC-SHA256"`).                                  | `"AES-256-CBC/HMAC-SHA256"`                 |

**Example Payload (JSON):**
```json
{
  "encryptedPayload": "AQIDBAUGBwg...",
  "hmac": "3a7b4c9d...",
  "nonce": 1234567890,
  "timestamp": "2024-05-20T12:00:00Z",
  "algorithm": "AES-256-CBC/HMAC-SHA256"
}
```

---
### **2.2. Schema for Digital Signature Validation**
Used for asymmetric encryption (e.g., RSA, ECDSA) where keys are public/private.

| **Field**            | **Type**       | **Description**                                                                                     | **Example Format**                          |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `encryptedData`      | `base64`       | The ciphertext of the original data.                                                              | `"AQIDBAUGBwg..."`                          |
| `signature`         | `base64`       | Digital signature of `encryptedData` (using private key).                                          | `"MEUCIQD..."`                             |
| `publicKey`          | `PEM/JSON`     | Recipient’s public key for verification.                                                          | `{"type":"RSA","modulus":"..."}`            |
| `algorithm`          | `string`       | Signature algorithm (e.g., `"RS256"`, `"ES256"`).                                                   | `"RS256"`                                   |

**Example Payload (JSON Web Signature - JWS):**
```json
{
  "encryptedData": "AQIDBAUGBwg...",
  "signature": "MEUCIQD...",
  "publicKey": {
    "type": "RSA",
    "modulus": "eJ...",
    "exponent": "AQAB"
  },
  "alg": "RS256"
}
```

---
### **2.3. Database Storage Schema**
For validating encrypted data at rest (e.g., SQL, NoSQL).

| **Column**           | **Type**       | **Description**                                                                                     |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------|
| `data`               | `bytea`/`BLOB` | Encrypted payload (e.g., AES-256).                                                                |
| `hmac`               | `varchar`      | HMAC-SHA256 of `data + secret_salt`.                                                              |
| `version`            | `int`          | Schema version (for backward compatibility).                                                       |
| `created_at`         | `timestamp`    | When the record was encrypted.                                                                     |
| `key_id`             | `uuid`         | Reference to the encryption key (e.g., AWS KMS ARN).                                               |

**Example (PostgreSQL):**
```sql
CREATE TABLE sensitive_data (
  id SERIAL PRIMARY KEY,
  data BYTEA NOT NULL,
  hmac VARCHAR(64) NOT NULL,
  version INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  key_id UUID
);
```

---

## **3. Query Examples**
### **3.1. Validating an API Request (HMAC)**
**Server-Side Pseudocode (Python):**
```python
import hmac, hashlib

def validate_hmac(request_data, secret_key):
    expected_hmac = hmac.new(
        secret_key.encode(),
        request_data["encryptedPayload"].encode() + request_data["nonce"].to_bytes(8, 'big'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_hmac, request_data["hmac"])
```

**Request (HTTP Header):**
```
Authorization: HMAC <request_id>=<hmac_value>
```

---
### **3.2. Validating a Database Record**
**Query to Check Integrity (SQL):**
```sql
SELECT *
FROM sensitive_data
WHERE hmac = (
    SHA256(
        data || 'salt_' || key_id,
        256
    )
) AND version = 1;
```

**Application-Level Check (Pseudocode):**
```javascript
const crypto = require('crypto');
const record = db.getRecordById(123);

const expectedHmac = crypto
    .createHmac('sha256', 'salt_' + record.key_id)
    .update(record.data)
    .digest('hex');

if (expectedHmac !== record.hmac) {
    throw new Error("Data tampered or corrupted!");
}
```

---
### **3.3. Validating a Digital Signature (JWT-like)**
**Server-Side Verification (Node.js):**
```javascript
const jwt = require('jsonwebtoken');

const verifySignature = (payload, publicKey) => {
    return jwt.verify(
        payload.signature,
        publicKey,
        { algorithms: ["RS256"] }
    );
};
```

**Example Payload:**
```json
{
  "encryptedData": "base64_ciphertext",
  "signature": "base64_signature",
  "header": {
    "alg": "RS256",
    "typ": "JWS"
  }
}
```

---

## **4. Common Pitfalls & Mitigations**
| **Risk**                          | **Mitigation**                                                                                     |
|-----------------------------------|---------------------------------------------------------------------------------------------------|
| **Replay attacks**                | Use **nonces** or **timestamps** to track unique requests.                                      |
| **Key leakage**                   | Rotate keys **automatically** (e.g., AWS KMS schedules).                                        |
| **Incorrect HMAC calculation**    | **Never** concatenate secrets in plaintext; use libraries (e.g., `crypto` in Node.js).         |
| **Algorithmic weakness**          | Stick to **NIST-approved** ciphers (e.g., AES-256, SHA-3).                                        |
| **Storage bloat**                 | Compress data **before** encryption (e.g., `gzip` + AES).                                       |

---

## **5. Related Patterns**
| **Pattern**                      | **Description**                                                                                     | **When to Use**                                  |
|----------------------------------|---------------------------------------------------------------------------------------------------|--------------------------------------------------|
| **[JSON Web Tokens (JWT)](https://jwt.io/)** | Uses digital signatures for stateless authentication.                                           | API authentication/authorization.              |
| **[Key Management System (KMS)](https://aws.amazon.com/kms/)** | Centralized encryption key storage/rotation.                                                      | Enterprise-grade key security.                  |
| **[End-to-End Encryption (E2EE)](https://en.wikipedia.org/wiki/End-to-end_encryption)** | Encrypts data from user to user (e.g., Signal, WhatsApp).                                      | Messaging apps, healthcare data.                |
| **[HMAC for REST APIs](https://auth0.com/blog/cryptographic-signatures-rest-api-authentication/)** | Signs API requests to prevent tampering.                                                          | Secure API design.                               |
| **[PostgreSQL pgcrypto](https://www.postgresql.org/docs/current/pgcrypto.html)** | Built-in crypto functions for database-level validation.                                         | Encrypted databases (e.g., financial systems). |

---

## **6. Tools & Libraries**
| **Tool/Library**          | **Language/Use Case**                          | **Key Features**                                  |
|---------------------------|-----------------------------------------------|---------------------------------------------------|
| **Tink (Google)**         | Multi-language (C++, Java, Python)           | Modern crypto with key rotation.                  |
| **AWS KMS**               | Serverless key management                      | Auto-rotation, IAM policies.                      |
| **OpenSSL**               | CLI/binary crypto operations                 | HMAC, RSA, AES.                                  |
| **Bouncy Castle**         | Java/.NET                                     | Supports ECC, RSA, and PBKDF2.                    |
| **PyCryptodome**          | Python                                        | AES, HMAC, digital signatures.                    |

---
## **7. References**
1. [NIST SP 800-57 Rev. 5](https://csrc.nist.gov/publications/detail/sp/800-57/rev-5/final) – Key Management.
2. [RFC 7518](https://datatracker.ietf.org/doc/html/rfc7518) – JWA/JWS (JWT).
3. [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html).
4. [HMAC RFC 2104](https://www.rfc-editor.org/rfc/rfc2104).

---
**Last Updated:** [Insert Date]
**Version:** 1.2