# **[Pattern] Signing Validation – Reference Guide**

---
## **Overview**
The **Signing Validation** pattern ensures data integrity and authentication by verifying cryptographic signatures embedded in requests, responses, or payloads. This pattern is critical for securing API interactions, message exchanges, and distributed systems where tampering, replay attacks, or spoofing must be prevented.

Signing validation works by validating a cryptographic signature against:
- A known public key (asymmetric) or shared secret (symmetric).
- The message itself (e.g., via HMAC, RSA, ECDSA, or Ed25519).
- A timestamp or nonce to prevent replay attacks.

Implementation requires generating signatures before transmission, validating them upon receipt, and optionally enforcing policies like:
- Strict signature verification (reject invalid signatures).
- Signature expiration (immutable after a timestamp).
- Key rotation policies (periodic public key updates).

This guide covers key concepts, schema references, query examples, and related patterns for robust signing validation.

---

## **Key Concepts**

### **1. Signing vs. Validation**
| **Term**       | **Definition**                                                                 | **Example**                          |
|----------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Signing**    | Generating a signature using a private key (sender’s secret).                 | `signature = HMAC(message, privateKey)` |
| **Validation** | Verifying a signature using a public key (receiver’s trust anchor).         | `verify(message, signature, publicKey)` |

### **2. Signing Algorithms**
| **Algorithm** | **Type**       | **Use Case**                          | **Security Notes**                          |
|---------------|----------------|---------------------------------------|---------------------------------------------|
| **HMAC-SHA256** | Symmetric     | Shared secrets (e.g., JWT)            | Fast but vulnerable to key compromise      |
| **RSA-SHA256**  | Asymmetric    | PKI-based authentication (e.g., TLS)   | Slower; vulnerable to key leakage           |
| **ECDSA**      | Asymmetric    | Space-efficient (e.g., blockchain)     | Strong but requires secure key management   |
| **Ed25519**    | Asymmetric    | Modern alternative to ECDSA            | Curve25519-based; resistant to side-channel attacks |

### **3. Signature Components**
| **Component**       | **Description**                                                                 | **Example**                          |
|---------------------|-------------------------------------------------------------------------------|--------------------------------------|
| **Payload**        | Data being signed (e.g., JSON, XML, or raw bytes).                            | `{"user": "alice", "action": "login"}` |
| **Signature**      | Output of the signing algorithm (base64-encoded or hex).                      | `"30440220..."`                      |
| **Public Key**     | Trusted key used to validate the signature (e.g., PEM, JWK).                 | `-----BEGIN PUBLIC KEY-----`         |
| **Algorithm**      | Specifies the signing algorithm (e.g., `Ed25519`, `RS256`).                   | `"alg": "Ed25519"`                   |

### **4. Validation Rules**
| **Rule**               | **Description**                                                                 | **Implementation Note**               |
|------------------------|-------------------------------------------------------------------------------|----------------------------------------|
| **Strict Verification** | Signature must match exactly (no partial verification).                       | Use `verify(message, signature, key)`  |
| **Nonce/Timestamp Check** | Prevent replay attacks by validating uniqueness (e.g., `nonce` or `iat`).        | Store and check `nonce` or `exp`       |
| **Key Rotation**       | Public keys expire or are revoked; use the latest key.                          | Fetch keys from a **Key Management System (KMS)** |
| **Signature Length**   | Ensure the signature matches the algorithm’s output size.                      | E.g., Ed25519 produces 64-byte signatures |
| **Message Integrity**  | Verify the payload’s hash (e.g., SHA-256) before signature validation.          | Hash the payload first (`sha256(payload)`) |

---

## **Schema Reference**
Below are JSON schemas for signing payloads and validation responses.

### **1. Signed Payload Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["payload", "signature", "key_id", "alg"],
  "properties": {
    "payload": {
      "type": "object",
      "description": "The data being signed (e.g., API request/response)."
    },
    "signature": {
      "type": "string",
      "format": "base64url|hex",
      "description": "The cryptographic signature of the payload."
    },
    "key_id": {
      "type": "string",
      "description": "Identifier for the public key used (e.g., `RSAPublicKey-2023`)."
    },
    "alg": {
      "type": "string",
      "enum": ["Ed25519", "RS256", "HS256", "ES256"],
      "description": "Signing algorithm used."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Issuance time (RFC 3339)."
    },
    "nonce": {
      "type": "string",
      "description": "Prevents replay attacks (unique per request)."
    }
  }
}
```

### **2. Validation Response Schema**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "valid": {
      "type": "boolean",
      "description": "True if signature is valid; false otherwise."
    },
    "error": {
      "type": "string",
      "description": "Error message if validation fails (e.g., 'InvalidSignature').",
      "nullable": true
    },
    "key_used": {
      "type": "string",
      "description": "Public key ID used for validation."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Validation time (RFC 3339)."
    }
  }
}
```

---

## **Query Examples**

### **1. Signing a Request (Node.js Example)**
```javascript
const crypto = require('crypto');

const payload = JSON.stringify({ user: "alice", action: "login" });
const privateKey = crypto.createPrivateKey({
  key: {
    // Your Ed25519 private key (PEM format)
    crv: "Ed25519",
    kty: "OKP",
    d: "...",
    x: "..."
  }
});

// Sign the payload
const signature = crypto.sign("ed25519", payload, privateKey);
const signedPayload = {
  payload,
  signature: signature.toString('base64url'),
  key_id: "ed25519-key-2023",
  alg: "Ed25519",
  timestamp: new Date().toISOString()
};
```

### **2. Validating a Signature (Python Example)**
```python
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

public_key = ed25519.Ed25519PublicKey.from_pem(open("public_key.pem").read().encode())
payload = b'{"user": "alice", "action": "login"}'
signature = bytes.fromhex("...")  # Base64url-decoded or raw bytes

try:
    public_key.verify(signature, payload, hashes.SHA256())
    print("✅ Signature valid")
except:
    print("❌ Invalid signature")
```

### **3. HTTP Header-Based Validation (API Example)**
**Request:**
```http
POST /api/secure-endpoint HTTP/1.1
Host: example.com
Authorization: Signature keyId="ed25519-key-2023",alg="Ed25519",timestamp="2023-10-01T12:00:00Z",signature="..."
Content-Type: application/json

{
  "user": "alice",
  "action": "login"
}
```

**Server Validation (Pseudocode):**
```python
def validate_signature(request):
    signature = request.headers["Signature"]
    payload = request.body
    key_id = signature["keyId"]
    public_key = fetch_public_key(key_id)  # From KMS

    try:
        assert verify(payload, signature["signature"], public_key)
        assert not is_expired(signature["timestamp"])
        return {"valid": True}
    except:
        return {"valid": False, "error": "InvalidSignature"}
```

### **4. JWT with Signing Validation (OAuth2)**
```json
{
  "valid": true,
  "payload": {
    "sub": "123456789",
    "iat": 1696089600,
    "exp": 1696176000,
    "data": "sensitive_info"
  },
  "signature": "valid_jwt_signature_here..."
}
```

**Validation Check (JWTlib):**
```python
from jwt import decode
from jwt.exceptions import InvalidSignatureError

try:
    token = decode(
        jwt_token,
        public_key,
        algorithms=["Ed25519"],
        options={"verify_exp": True}
    )
    print("✅ JWT validated")
except InvalidSignatureError:
    print("❌ Invalid signature")
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **When to Use**                                  |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| **[JWT (JSON Web Tokens)](https://tools.ietf.org/html/rfc7519)** | Stateless authentication using signed tokens.                             | API authentication, session management.         |
| **[PKI (Public Key Infrastructure)**](https://datatracker.ietf.org/doc/html/rfc5280) | Hierarchical key management for asymmetric encryption.                 | Enterprise-grade security (e.g., TLS certificates). |
| **[HMAC-Based Message Authentication Code (HMAC)**](https://datatracker.ietf.org/doc/html/rfc2104) | Symmetric signing for shared secrets.                                        | Internal systems with trusted parties.           |
| **[Key Rotation Policies](https://cloud.google.com/kms/docs/key-rotation)** | Automated key renewal to reduce exposure risk.                              | High-security environments (e.g., banking).      |
| **[Replay Attack Prevention](https://www.ietf.org/rfc/rfc7697.txt)** | Nonce/timestamp validation to block duplicate messages.                    | Real-time systems (e.g., IoT, gaming).           |
| **[OAuth 2.0 with Proof-of-Possession](https://datatracker.ietf.org/doc/html/rfc7636)** | JWT signing for OAuth2 authentication flows.                               | Delegated authorization (e.g., GitHub OAuth).   |

---

## **Best Practices**
1. **Use Recent Algorithms**:
   - Prefer **Ed25519** or **ES256** over older RSA/SHA-1.
   - Avoid deprecated algorithms (e.g., SHA-1, MD5).

2. **Key Management**:
   - Store public keys in a **KMS** (e.g., AWS KMS, HashiCorp Vault).
   - Rotate keys periodically (e.g., every 90 days).

3. **Performance Considerations**:
   - Cache public keys to avoid repeated KMS calls.
   - Precompute hashes for large payloads.

4. **Logging & Monitoring**:
   - Log failed signature validations (without exposing sensitive data).
   - Set up alerts for unusual activity (e.g., repeated failed attempts).

5. **Test Coverage**:
   - Unit tests: Validate edge cases (e.g., malformed signatures, expired keys).
   - Integration tests: Simulate attack scenarios (e.g., tampered payloads).

---
**See Also:**
- [RFC 7515 (JWT)](https://datatracker.ietf.org/doc/html/rfc7515)
- [RFC 8037 (Ed25519)](https://datatracker.ietf.org/doc/html/rfc8037)
- [OWASP Signing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Signature_Cheat_Sheet.html)