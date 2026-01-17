---
# **[Pattern] Reference Guide: Signing Techniques**

---

## **1. Overview**
The **Signing Techniques** pattern standardizes methods for cryptographically signing messages, requests, or data payloads to ensure authenticity, integrity, and non-repudiation. It defines structured approaches for generating, validating, and managing signatures across APIs, microservices, and distributed systems. Common use cases include:
- **API authentication** (e.g., OAuth 2.0 token validation).
- **Data integrity** (e.g., verifying JSON payloads or attachments).
- **Audit trails** (e.g., signing logs for compliance).

This pattern supports multiple signing algorithms (e.g., HMAC-SHA256, RSA-SHA512, ECDSA) and key formats (e.g., PEM, JWK). Implementations must balance security (e.g., key rotation, tamper-evident signatures) with performance (e.g., batch signing).

---
## **2. Implementation Details**

### **2.1 Key Concepts**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Signing Key**       | A cryptographic key (private/public) used to generate/sign or verify signatures. Must be securely stored and rotated periodically.                                                                    |
| **Signature Algorithm** | Defines the cryptographic operation (e.g., `HMACSHA256`, `RS256`). Determines security strength and performance characteristics.                                                                             |
| **Payload**           | The data being signed (e.g., JSON request body, header, or message digest). Must include a `Content-Type` and timestamp to prevent replay attacks.                                                        |
| **Signature Format**  | Standardized encoding (e.g., JWT `compact` or `json` format, or raw binary). Example: `Base64URL`-encoded JWT signatures.                                                                              |
| **Key Rotation**      | Process for replacing signing keys before expiration to mitigate breach risks. Requires a handoff mechanism (e.g., `jwk` URLs or metadata headers).                                                        |
| **Nonce/Timestamp**   | Optional but recommended to prevent replay attacks. Includes a `iat` (issued-at) or unique request ID.                                                                                                       |
| **Validation Rules**  | Criteria for accepting signatures, e.g., algorithm consistency, key expiration checks, and payload tampering detection.                                                                                     |
| **Key Recovery**     | Mechanism to reclaim lost keys (e.g., via key management systems like AWS KMS or HashiCorp Vault).                                                                                                         |

---

### **2.2 Algorithm Support**
| Algorithm       | Description                                                                                     | Use Case                                                                                   |
|-----------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| **HMAC-SHA256** | Uses symmetric keys (shared secret) for signing.                                               | Low-latency scenarios (e.g., server-to-server calls).                                     |
| **RSA-SHA256**  | Asymmetric key pair (public/private). Requires secure key storage.                             | High-security APIs (e.g., OAuth 2.0).                                                    |
| **ECDSA**       | Elliptic curve cryptography for compact signatures.                                           | Mobile apps or IoT devices where key size matters.                                         |
| **EdDSA**       | High-performance alternative to ECDSA (e.g., Ed25519).                                        | Performance-critical systems (e.g., blockchain nodes).                                    |

---

### **2.3 Schema Reference**
#### **2.3.1 Request Signing Payload**
```json
{
  "signing_key_id": "urn:uuid:12345678-1234-5678-1234-567812345678", // Unique key identifier
  "algorithm": "RS256",                                      // Supported algorithm
  "signature": "bW9uZ29sYX...J1ZXJ5",                         // Base64URL-encoded signature
  "headers": {                                              // Critical headers (if applicable)
    "Date": "2023-10-05T12:00:00Z",
    "Content-Type": "application/json"
  },
  "payload_digest": "sha256:d8f...731..."                  // Optional HMAC over payload (if signed separately)
}
```

#### **2.3.2 Validation Response Schema**
```json
{
  "valid": true,                                           // Boolean: signature is valid
  "key_id": "urn:uuid:12345678-1234-5678-1234-567812345678",  // Used key identifier
  "algorithm": "RS256",                                    // Validated algorithm
  "expired": false,                                        // Key expiration status
  "errors": null                                           // Optional: Array of error strings
}
```

#### **2.3.3 Key Metadata**
```json
{
  "key_id": "urn:uuid:12345678-1234-5678-1234-567812345678",
  "algorithm": "RS256",
  "use": "signing",                                        // Purpose (e.g., "signing", "encryption")
  "expires_at": "2023-12-31T23:59:59Z",
  "key": {                                                 // Optional: Public key JWK
    "kty": "RSA",
    "e": "AQAB",
    "n": "hXa..."
  }
}
```

---

## **3. Query Examples**

### **3.1 Signing a Payload (HMAC-SHA256)**
```javascript
const crypto = require('crypto');
const secretKey = Buffer.from('shared-secret-key-123', 'utf8');

const payload = JSON.stringify({
  user_id: 12345,
  action: "update_profile"
});

const hmac = crypto.createHmac('sha256', secretKey)
  .update(payload)
  .digest('base64url');

console.log(hmac); // "bW9uZ29sYX...J1ZXJ5"
```

### **3.2 Validating a JWT Signature**
```javascript
const jwt = require('jsonwebtoken');
const publicKey = require('./public_key.pem');

try {
  const token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...";
  const decoded = jwt.verify(token, publicKey, { algorithms: ['RS256'] });
  console.log('Valid signature:', decoded);
} catch (err) {
  console.error('Invalid signature:', err.message);
}
```

### **3.3 Generating a Key Pair (RSA)**
```bash
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_max_bits:2048
openssl rsa -pubout -in private_key.pem -out public_key.pem
```

### **3.4 Batch Signing (ECDSA)**
```python
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# Generate key pair
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
public_key = private_key.public_key()

# Sign multiple messages
messages = ["msg1", "msg2"]
signatures = []
for msg in messages:
    signature = private_key.sign(msg.encode(), ec.ECDSA(hashes.SHA256()))
    signatures.append(base64.b64encode(signature).decode('utf8'))
```

### **3.5 Validating a Signature with Key Rotation**
```python
from jose import jwt, jwk

# Fetch key metadata (e.g., from a JWKS endpoint)
key_metadata = {
  "keys": [
    {
      "kid": "key-1",
      "kty": "RSA",
      "exp": 1702073600,
      "use": "sig",
      "x5c": ["..."]
    },
    {
      "kid": "key-2",
      "kty": "RSA",
      "exp": 1733587200,
      "use": "sig",
      "x5c": ["..."]
    }
  ]
}

# Validate with active keys
try:
  decoded = jwt.get_unverified_claims("token")
  kid = decoded["kid"]
  jwk_dict = next(k for k in key_metadata["keys"] if k["kid"] == kid)
  key = jwk.construct(jwk_dict)
  jwt.validate_token("token", key, algorithms=["RS256"])
except Exception as e:
  print("Validation failed:", e)
```

---

## **4. Best Practices**

### **4.1 Security Considerations**
- **Key Storage**: Use hardware security modules (HSMs) or cloud KMS for private keys.
- **Rotation**: Rotate keys every **90–180 days** or when compromised.
- **Replay Protection**: Include `iat` (issued-at) timestamps or unique request IDs.
- **Algorithm Selection**: Prefer **RS256** or **ES256** over weaker algorithms (e.g., SHA1).
- **Key Diversification**: Use separate keys for signing vs. encryption.

### **4.2 Performance Optimization**
- **Batch Signing**: Sign multiple messages at once (e.g., using `batch_sign` APIs in libraries like `libsodium`).
- **Caching**: Cache public keys in-memory for low-latency validation (with TTL).
- **Asynchronous Validation**: Offload signature validation to background workers if latency is critical.

### **4.3 Error Handling**
| Error Type               | Example Response                                                                                     |
|--------------------------|-----------------------------------------------------------------------------------------------------|
| **Invalid Algorithm**    | `{"error": "unsupported_algorithm", "details": "algorithm='HS512' not allowed"}`                     |
| **Expired Key**          | `{"error": "expired_key", "key_id": "urn:uuid:..."}`                                                |
| **Tampered Payload**     | `{"error": "invalid_signature", "status": 403}`                                                    |
| **Missing Key**          | `{"error": "key_not_found", "key_id": "urn:uuid:..."}`                                             |
| **Replay Attack**        | `{"error": "replay_detected", "timestamp": "2023-10-01T10:00:00Z"}`                              |

---

## **5. Related Patterns**
| Pattern Name               | Description                                                                                     | When to Use                                                                                     |
|----------------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **JWT (JSON Web Tokens)**  | Standard for encoding claims and signatures in a compact format.                              | Stateless authentication/authorization.                                                      |
| **OAuth 2.0**              | Framework for delegated access using tokens (often signed via Signing Techniques).            | Third-party APIs (e.g., social logins).                                                        |
| **Key Management**         | Secure storage and rotation of cryptographic keys.                                             | When managing multiple signing keys at scale.                                                 |
| **Idempotency Keys**       | Ensures duplicate requests are processed only once.                                          | Replay-resistant APIs (complements signing).                                                   |
| **API Gateway**           | Centralizes request/response validation, including signatures.                                | Multi-tenant APIs with complex signing requirements.                                           |

---
## **6. References**
- [RFC 7515 (JWT)](https://datatracker.ietf.org/doc/html/rfc7515)
- [RFC 8037 (ECDSA)](https://datatracker.ietf.org/doc/html/rfc8037)
- [OWASP Signing Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Signature_Validation_Cheat_Sheet.html)
- [AWS KMS Documentation](https://docs.aws.amazon.com/kms/latest/developerguide/)