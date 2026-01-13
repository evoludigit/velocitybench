# **[Pattern] Encryption Verification Reference Guide**

---

## **Overview**
Encryption Verification is a security pattern used to ensure data integrity and authenticity by validating encrypted payloads at runtime. This pattern guarantees that encrypted data (e.g., API responses, database records, or messages) has not been tampered with by an unauthorized party. It typically involves generating and validating cryptographic hashes (e.g., HMAC), digital signatures, or certificates against stored verification keys.

Common use cases include:
- **API Security:** Verifying JWT tokens, API responses, or request payloads.
- **Database Integrity:** Ensuring encrypted record integrity before decryption.
- **Message Verification:** Validating PGP-encrypted emails or blockchain transactions.

This guide provides implementation details, schema references, and best practices for deploying Encryption Verification in various environments.

---

## **Key Concepts**

| **Concept**               | **Description**                                                                                                                                                                                                 |
|---------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Symmetric Verification** | Uses shared keys (e.g., AES-256) to verify data integrity. Commonly paired with HMAC (e.g., HMAC-SHA256) for verification.                                         |
| **Asymmetric Verification** | Relies on public/private key pairs (e.g., RSA, ECDSA) to verify signatures. Public keys are distributed widely; private keys remain secure.                                         |
| **Hash-based Verification** | Generates a cryptographic hash (e.g., SHA-3, BLAKE3) of the original data and compares it to a stored hash. Vulnerable to collision attacks; rarely used alone. |
| **Certificates (X.509)**    | Digital certificates bind public keys to identities (e.g., TLS/SSL). Used in PKI (Public Key Infrastructure) for mutual authentication.                                        |
| **Deterministic Encryption** | Ensures the same plaintext produces the same encrypted output (e.g., AES-GCM) for reliable verification. Non-deterministic (e.g., RSA-OAEP) is less suitable.                   |
| **Zero-Knowledge Proofs**   | Advanced technique (e.g., ZK-SNARKs) to verify computations without exposing data. Used in privacy-preserving systems like Monero or Ethereum smart contracts. |

---

## **Schema Reference**

### **1. Symmetric Verification (HMAC)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "algorithm": {
      "type": "string",
      "enum": ["HMAC-SHA256", "HMAC-SHA384", "HMAC-SHA512"],
      "description": "Hash algorithm used for HMAC generation."
    },
    "secretKey": {
      "type": "string",
      "format": "byte",
      "minLength": 32,
      "description": "Symmetric secret key (e.g., 32-byte AES key). Must be shared securely between parties."
    },
    "payload": {
      "type": "string",
      "format": "byte",
      "description": "Data to be verified (must match original plaintext)."
    },
    "signature": {
      "type": "string",
      "format": "byte",
      "description": "HMAC signature generated from `secretKey` and `payload`."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Optional timestamp to prevent replay attacks."
    }
  },
  "required": ["algorithm", "secretKey", "payload", "signature"],
  "additionalProperties": false
}
```

**Example Use Case:**
Verifying a message payload (`payload`) against a stored HMAC (`signature`) using a shared secret (`secretKey`).

---

### **2. Asymmetric Verification (RSA/ECDSA)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "algorithm": {
      "type": "string",
      "enum": ["RSASSA-PKCS1-v1_5", "RSASSA-PSS", "ECDSA"],
      "description": "Asymmetric signing algorithm."
    },
    "publicKey": {
      "type": "object",
      "properties": {
        "key": { "type": "string", "format": "byte" },
        "algorithm": { "type": "string" },
        "curve": { "type": "string", "enum": ["P-256", "P-384", "P-521"] }  // ECDSA-specific
      },
      "required": ["key", "algorithm"]
    },
    "signature": {
      "type": "string",
      "format": "byte",
      "description": "Digital signature generated with the private key."
    },
    "data": {
      "type": "string",
      "format": "byte",
      "description": "Original data signed by the private key."
    }
  },
  "required": ["algorithm", "publicKey", "signature", "data"]
}
```

**Example Use Case:**
Validating a JWT token’s signature using the issuer’s public key (`publicKey`) against the token payload (`data`).

---

### **3. Certificate-based Verification (X.509)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "certificate": {
      "type": "string",
      "format": "byte",
      "description": "PEM-encoded X.509 certificate (public key + metadata)."
    },
    "signatureAlgorithm": {
      "type": "string",
      "enum": ["RSA", "ECDSA", "Ed25519"],
      "description": "Algorithm used to sign the certificate."
    },
    "data": {
      "type": "string",
      "format": "byte",
      "description": "Data signed by the private key (e.g., TLS handshake)."
    },
    "signature": {
      "type": "string",
      "format": "byte",
      "description": "Signature over `data` using the certificate's private key."
    },
    "trustChain": {
      "type": "array",
      "items": { "type": "string", "format": "byte" },
      "description": "Intermediate CA certificates to validate the root CA."
    }
  },
  "required": ["certificate", "signatureAlgorithm", "data", "signature"]
}
```

**Example Use Case:**
Validating a TLS server certificate (`certificate`) during a handshake by verifying its signature (`signature`) against a trusted CA root.

---

## **Implementation Details**

### **1. Tools/Libraries**
| **Language/Tool** | **Library**                          | **Support**                                                                 |
|--------------------|--------------------------------------|-----------------------------------------------------------------------------|
| Python             | `cryptography`, `pyca/hmac`          | HMAC, RSA, ECDSA, X.509                                                  |
| Java               | `BC Provider` (Bouncy Castle)       | All algorithms; widely used in enterprise Java                            |
| JavaScript         | `crypto` (Node.js), `web-crypto`     | HMAC, RSA, ECDSA (Web Crypto API)                                         |
| C#                 | `System.Security.Cryptography`      | AES, RSA, SHA-3, X.509 (built-in)                                         |
| Go                 | `crypto` package                     | HMAC, RSA, ECDSA, SHA-3                                                   |
| Rust               | `ring` crate                         | Zero-allocation cryptography; supports HMAC, RSA, and ECDSA              |

---

### **2. Best Practices**
1. **Key Management:**
   - Use Hardware Security Modules (HSMs) or cloud KMS (e.g., AWS KMS) for private keys.
   - Rotate keys periodically (e.g., every 90 days for RSA).
   - Never hardcode keys in source code; use environment variables or secrets managers.

2. **Algorithm Selection:**
   - **Avoid obsolete algorithms:** DES, MD5, SHA-1, RC4.
   - **Prefer modern standards:** AES-256-GCM, ECDSA (P-384), HMAC-SHA3-512.
   - **For signatures:** Use PSS over PKCS#1-v1.5 to mitigate padding oracle attacks.

3. **Security Headers:**
   - Include `Content-Type: application/hmac` or `Content-Type: application/pkcs7-mime` for APIs.
   - Use `Strict-Transport-Security` (HSTS) to enforce HTTPS for certificate validation.

4. **Replay Attacks:**
   - Add timestamps (`timestamp` field) or nonce to signatures.
   - For PKI, validate certificate expiration and revocation lists (CRL/OCSP).

5. **Performance:**
   - Cache public keys (e.g., in memory or Redis) to avoid repeated I/O.
   - Use hardware-accelerated crypto (e.g., Intel SGX, AWS Nitro Enclaves).

---

## **Query Examples**

### **1. Verify HMAC in Python**
```python
import hmac
import hashlib

# Shared secret key (32 bytes for AES-256)
SECRET_KEY = b'\x00' * 32
PAYLOAD = b"Sensitive data to verify"
HMAC_SIGNATURE = b"\xde\xad\xbe\xef..."  # Stored or received signature

# Verify HMAC
try:
    hmac.new(SECRET_KEY, PAYLOAD, hashlib.sha256).digest() == HMAC_SIGNATURE
    print("Verification successful.")
except:
    print("Verification failed.")
```

### **2. Validate RSA Signature in Java**
```java
import java.security.*;
import java.security.spec.*;
import java.util.Base64;

public class RSAVerifier {
    public static boolean verifySignature(
        String publicKeyPem,
        byte[] data,
        byte[] signature
    ) throws Exception {
        PublicKey publicKey = KeyFactory
            .getInstance("RSA")
            .generatePublic(new X509EncodedKeySpec(
                Base64.getDecoder().decode(publicKeyPem)
            ));
        Signature sig = Signature.getInstance("SHA256withRSA");
        sig.initVerify(publicKey);
        sig.update(data);
        return sig.verify(signature);
    }
}
```

### **3. Verify X.509 Certificate in Go**
```go
package main

import (
    "crypto/x509"
    "encoding/pem"
    "fmt"
)

func verifyCertificate(certPEM string, data, signature []byte) error {
    block, _ := pem.Decode([]byte(certPEM))
    cert, err := x509.ParseCertificate(block.Bytes)
    if err != nil {
        return err
    }

    options := x509.VerifyOptions{
        Roots:         x509.NewCertPool(),
        IntermediateCAs: x509.NewCertPool(), // Add trust chain if needed
    }
    options.Roots.AddCert(cert) // Self-signed example

    _, err = cert.Verify(options)
    if err != nil {
        return fmt.Errorf("certificate verification failed: %v", err)
    }

    return nil
}
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **JWT Authentication**    | JSON Web Tokens (JWT) with HMAC/RSA verification for stateless auth.            | APIs, OAuth2, microservices.                                                    |
| **TLS/SSL**               | Encrypts traffic (TLS) and verifies certificates for server/client auth.       | Web servers, HTTPS, VPNs.                                                       |
| **Opaque Tokens**         | Short-lived tokens (e.g., OAuth2) with opaque identifiers to avoid key exposure. | High-security APIs (e.g., payment systems).                                      |
| **Key Rotation**          | Automated process to replace cryptographic keys without downtime.              | Long-running systems (e.g., databases, HSMs).                                   |
| **Zero-Knowledge Proofs** | Proves knowledge of a value without revealing it (e.g., ZK-SNARKs).           | Privacy-focused apps (e.g., blockchain, VPNs).                                   |
| **Attribute-Based Encryption (ABE)** | Fine-grained access control via encrypted attributes.           | Multi-party data sharing (e.g., healthcare, research).                          |

---

## **Common Pitfalls & Mitigations**

| **Pitfall**                          | **Risk**                                                                       | **Mitigation**                                                                 |
|--------------------------------------|--------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Weak Keys**                        | Predictable or short keys (e.g., 128-bit RSA).                                | Use 2048-bit RSA or 384-bit ECDSA.                                              |
| **Key Leakage**                      | Private keys exposed via logs or code.                                       | Use HSMs, restrict file permissions, rotate keys.                               |
| **Timing Attacks**                   | Side-channel leaks (e.g., CPU cache, branch prediction).                      | Use constant-time algorithms (e.g., `hmac.compare_digest`).                   |
| **Replay Attacks**                   | Stale signatures/responses reused.                                           | Add `timestamp` or nonce to signatures.                                        |
| **Certificate Chaining Errors**      | Missing intermediate CA certificates.                                        | Validate full trust chain (e.g., using `x509.VerifyOptions` in Go).            |
| **Quantum Vulnerability**            | RSA/ECDSA broken by quantum computers.                                        | Migrate to post-quantum algorithms (e.g., Kyber, Dilithium).                  |

---

## **Further Reading**
- [RFC 2104 (HMAC)](https://datatracker.ietf.org/doc/html/rfc2104)
- [RFC 8017 (RSA Crypto)](https://datatracker.ietf.org/doc/html/rfc8017)
- [NIST SP 800-57 (Key Mgmt)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57.html)
- [OWASP Crypto Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)