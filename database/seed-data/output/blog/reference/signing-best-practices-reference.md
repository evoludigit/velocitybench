# **[Pattern] Signing Best Practices – Reference Guide**

---

## **Overview**
Securing digital assets, messages, or software artifacts with cryptographic signatures is critical for authentication, integrity, and non-repudiation. The **Signing Best Practices** pattern outlines guidelines for implementing cryptographic signatures effectively, balancing security, usability, and compliance. This guide covers key concepts, implementation details, validation schemas, and real-world examples for robust signing practices in systems.

---

## **1. Key Concepts**
### **1.1 Core Principles**
- **Authenticity:** Ensure signatures prove the origin of data.
- **Integrity:** Detect tampering with signed content.
- **Non-Repudiation:** Prevent signers from denying action (via cryptographic proof).
- **Confidentiality (Optional):** Combine with encryption for end-to-end security.

### **1.2 Signature Types**
| Type               | Use Case                          | Algorithm Examples                     |
|--------------------|-----------------------------------|----------------------------------------|
| **Asymmetric**     | Digital signatures (keys ≥ 2048)  | RSA, ECDSA, Ed25519                   |
| **Symmetric**      | MACs (keys ≤ 256)                 | HMAC-SHA256, Poly1305                  |
| **Hash-Based**     | Lightweight integrity checks       | BLAKE3, SHA-3                         |

### **1.3 Threat Model**
| Threat               | Mitigation Strategy                                                                 |
|----------------------|-------------------------------------------------------------------------------------|
| Key Compromise       | Use short-lived keys, hardware security modules (HSMs), and key rotation.           |
| Signature Forgery    | Validate signatures with the correct public key and algorithm.                      |
| Replay Attacks       | Include timestamps or nonces in signed messages.                                    |
| Weak Algorithms      | Avoid deprecated algorithms (e.g., SHA-1, RSA < 2048 bits).                          |

---

## **2. Implementation Best Practices**

### **2.1 Key Management**
- **Key Hierarchy:**
  Use nested key pairs (root CA → intermediate → signing keys).
  Example:
  ```
  Root CA → Subordinate CA → Application Signing Key (ECDSA P-256)
  ```
- **Hardware Security:** Store private keys in **HSMs** or **TPMs** for FIPS 140-2 Level 3+ compliance.
- **Key Rotation:** Rotate keys every **90–365 days**; revoke compromised keys via **OCSP/CRL**.

### **2.2 Signature Algorithms**
| Algorithm      | Security Level | Use Cases                          | Notes                                  |
|----------------|----------------|------------------------------------|----------------------------------------|
| **Ed25519**    | High           | Short-term signatures, IoT        | Fast, 256-bit security.                |
| **ECDSA (P-256)** | High       | Balanced performance, web apps    | Prefer over RSA for speed.             |
| **RSA-PSS**    | High           | Long-term signatures               | Resistant to padding oracle attacks.   |
| **SHA-384**    | High           | Hashing before signing             | Avoid SHA-1/SHA-224.                   |

### **2.3 Data Preparation**
- **Structured Signing:** Sign canonical JSON/XML (e.g., JWS, XAdES).
- **Nonces/Timestamps:** Add to prevent replay attacks:
  ```json
  {
    "nonce": "abc123",
    "timestamp": "2024-05-20T12:00:00Z",
    "data": { ... }
  }
  ```
- **Deterministic Signing:** Use `dry-run` flags for reproducible signatures (e.g., Ed25519).

### **2.4 Validation Rules**
- **Public Key Binding:** Ensure public key matches the signer’s identity (e.g., via X.509 certificates).
- **Algorithm Verification:** Reject signatures using deprecated algorithms.
- **Signature Freshness:** Check timestamps/nonces for replay attacks.

---

## **3. Schema Reference**
### **3.1 Canonical Data Format**
| Field               | Type    | Description                                                                 | Example                        |
|---------------------|---------|-----------------------------------------------------------------------------|--------------------------------|
| `signature`         | `bytes` | Base64url-encoded cryptographic signature.                                   | `dBjfti...`                  |
| `signed_data`       | `object`| Structured payload with metadata (nonce, timestamp).                         | `{ "nonce": "abc123" }`      |
| `public_key`        | `string`| Base64url-encoded public key (X.509 or raw).                                | `MIIBIj...`                   |
| `algorithm`         | `string`| `Ed25519`, `ECDSA-SHA256`, etc. (RFC 8037).                                 | `Ed25519`                     |
| `timestamp`         | `string`| ISO8601 timestamp (UTC).                                                     | `2024-05-20T12:00:00Z`        |

### **3.2 Validation Schema (JSON Schema)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["signature", "signed_data", "public_key", "algorithm"],
  "properties": {
    "signature": { "type": "string", "format": "base64url", "minLength": 44 },
    "signed_data": {
      "type": "object",
      "properties": {
        "nonce": { "type": "string" },
        "timestamp": { "type": "string", "format": "date-time" }
      }
    },
    "public_key": { "type": "string", "format": "base64url" },
    "algorithm": {
      "enum": ["Ed25519", "ECDSA-SHA256", "RSA-PSS-SHA384"]
    }
  },
  "additionalProperties": false
}
```

---

## **4. Query Examples**
### **4.1 Signing a Message (Python)**
```python
import ed25519
import base64

# Generate key pair
private_key, public_key = ed25519.create_keypair()

# Sign data
data = b'{"message": "Hello"}'
signature = ed25519.sign(private_key, data)

# Encode for transport
signature_b64 = base64.urlsafe_b64encode(signature).decode()

print(f"Signature: {signature_b64}")
```

### **4.2 Validating a Signature (Go)**
```go
package main

import (
	"crypto/ed25519"
	"encoding/base64"
	"fmt"
)

func main() {
	sigB64 := "dBjftiLk..."
	signedData := []byte(`{"message": "Hello"}`)
	publicKey, _ := base64.URLEncoding.DecodeString("MIIBIj...")

	sig, _ := base64.URLEncoding.DecodeString(sigB64)
	isValid := ed25519.Verify(publicKey, signedData, sig)
	fmt.Println("Signature valid:", isValid) // true/false
}
```

### **4.3 Integrating with JWT (JWS)**
```json
{
  "header": {
    "alg": "EdDSA",
    "kid": "key-1"
  },
  "payload": {
    "sub": "user@example.com",
    "iat": 1716000000
  },
  "signature": "dBjfti..."
}
```
**Verify with:** [`jwt.io`](https://jwt.io) or `jwt-go`.

---

## **5. Common Pitfalls & Fixes**
| Pitfall                          | Solution                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| **Weak Key Size (e.g., RSA 1024)** | Upgrade to ≥ 2048 bits or use ECDSA.                                    |
| **No Timestamps**                 | Add `iat` (issued at) or `nbf` (not before) claims in tokens.             |
| **Hardcoded Keys**                | Use **HSMs** or **key vaults** (AWS KMS, HashiCorp Vault).                |
| **No Key Rotation**               | Automate rotation (e.g., Terraform + AWS KMS).                           |
| **Algorithm Mismatch**            | Enforce allowed algorithms via validation rules (e.g., RFC 8037).        |

---

## **6. Related Patterns**
- **[HA1] Hardware Security Modules (HSMs)** – Secure key storage for cryptographic operations.
- **[HA2] Key Rotation Strategies** – Automated policies for revoking/rotating keys.
- **[CA1] Certificate Authority (CA) Design** – Hierarchical trust models for public keys.
- **[AES] Encryption Best Practices** – Combine with signing for end-to-end security.
- **[TPM] Trusted Platform Module (TPM)** – Hardware-based root of trust for signing.

---
### **Further Reading**
- [RFC 8037: Ed25519 and Ed448 Signature Schemes](https://datatracker.ietf.org/doc/html/rfc8037)
- [NIST SP 800-57: Key Management](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57Part4r5.pdf)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

---
**Last Updated:** MM/YYYY
**Version:** 1.2