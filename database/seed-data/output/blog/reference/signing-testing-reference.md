**[Pattern] Signing Testing Reference Guide**

---

### **Overview**
The **Signing Testing** pattern facilitates secure validation of messages, APIs, or artifacts by verifying cryptographic signatures before processing. This ensures data integrity, authenticity, and non-repudiation. Implementations typically include **asymmetric cryptography** (e.g., RSA, ECDSA) to generate and verify signatures, often embedded in headers, payloads, or tokens. Common use cases include:
- **Webhooks** (e.g., Slack, Stripe)
- **Microservice communication**
- **Blockchain transaction validation**
- **Code artifact verification** (e.g., Docker images, software packages)

Key components:
- **Signing Key**: Private key used to generate signatures (never shared).
- **Verification Key**: Public key or certificate distributed for validation.
- **Signature Algorithm**: Standard (e.g., HMAC-SHA256, RSASSA-PKCS1-v1_5).
- **Payload**: Data being signed (often hashed before signing for efficiency).
- **Timestamp/OPAQUE**: Optional additions for replay attacks or freshness.

---

### **Implementation Details**

#### **Key Concepts**
| Concept               | Description                                                                                     | Example Values/Notes                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| **Signature Generation** | Process of creating a cryptographic signature using a private key and payload.                | `signature = sign(private_key, payload)` (e.g., `HMAC-SHA256(private_key, payload)`). |
| **Signature Verification** | Process of validating a signature using a public key to confirm the payload’s integrity.   | `bool = verify(public_key, signature, payload)`.                                     |
| **Payload Hashing**     | Pre-signing step to reduce payload size and improve efficiency.                               | SHA-256 or SHA-3 hashing (e.g., `hash = SHA256(payload)`).                           |
| **JWT-like Signing**    | Signing the entire payload (e.g., JSON) via headers (common in APIs/webhooks).                 | `.signing.headers.signature = "..."`, `.signing.payload = {data: {...}}`.            |
| **OPAQUE (HMAC-based)** | Uses a symmetric key (shared secret) for signing; less secure but simpler for internal systems. | `signature = HMAC-SHA255(secret_key, payload)`.                                       |
| **Certificate Validation** | Public key may be embedded in an X.509 certificate for key rotation and revocation support.   | CRLs (Certificate Revocation Lists) or OCSP (Online Certificate Status Protocol).    |
| **Replay Attack Mitigation** | Timestamps or nonce values prevent replay of signed messages.                                   | `timestamp: 1672531200`, `nonce: "abcd1234"`.                                      |

---

#### **Schema Reference**
Below are common schemas for signing testing, categorized by use case.

##### **1. Webhook Signing (e.g., Stripe, GitHub)**
```json
{
  "signing": {
    "headers": {
      "stripe-signature": "v1=abc123...==",  // HMAC-SHA256 header
      "timestamp": "1672531200"
    },
    "payload": {
      "type": "charge",
      "data": { "id": "ch_123", "amount": 100 }
    }
  }
}
```
| Field               | Type     | Description                                                                 | Required |
|---------------------|----------|-----------------------------------------------------------------------------|----------|
| `stripe-signature`  | String   | HMAC-SHA256 signature of `payload` + `timestamp`.                          | Yes      |
| `timestamp`         | Integer  | Unix timestamp to prevent replay attacks.                                   | Yes      |
| `payload.type`      | String   | Event type (e.g., `"charge"`, `"webhook_delivery"`).                       | Yes      |
| `payload.data`      | Object   | Raw event data to be verified.                                               | Yes      |

**Signature Calculation**:
```python
import hmac, hashlib
import base64

secret_key = b'stripe_webhook_signing_secret'
payload_str = json.dumps({"type": "charge", "data": {"id": "ch_123"}}, separators=(',', ':'))
message = f"{payload_str}{timestamp}".encode()
signature = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
```

---

##### **2. JWT-like Signing (e.g., API Tokens)**
```json
{
  "header": {
    "alg": "HS256",  // or "RS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user123",
    "exp": 1672531200,
    "data": { "user": "Alice" }
  },
  "signature": "abc123..."
}
```
| Field       | Type     | Description                                                                 | Required |
|-------------|----------|-----------------------------------------------------------------------------|----------|
| `header.alg`| String   | Algorithm (e.g., `"HS256"`, `"RS256"`).                                     | Yes      |
| `payload.sub`| String | Subject (e.g., user ID).                                                     | Conditional |
| `payload.exp`| Integer | Expiration timestamp.                                                         | Conditional |
| `signature` | String   | HMAC (for HMAC-based alg) or RSA signature of `header.payload`.               | Yes      |

**Verification**:
```python
import jwt
try:
  decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
except jwt.ExpiredSignatureError:
  print("Token expired!")
```

---

##### **3. Docker Image Signing (Cosign)**
```yaml
# .sigs/dev/hello-world-sha256.1672531200.sig
{
  "payload": {
    "image": "docker.io/library/hello-world:latest",
    "digest": "sha256:abc123...",
    "mediaType": "application/vnd.docker.distribution.manifest.v2+json"
  },
  "signature": {
    "signed": {
      "payload": "base64_encoded_payload",
      "signature": "base64_encoded_signature"
    },
    "signature": "RS256"
  }
}
```
| Field               | Type     | Description                                                                 | Required |
|---------------------|----------|-----------------------------------------------------------------------------|----------|
| `payload.image`     | String   | Docker image reference.                                                     | Yes      |
| `payload.digest`    | String   | SHA256 digest of the image layers.                                           | Yes      |
| `signature`         | Object   | Contains the signed payload + signature (base64-encoded).                   | Yes      |

**Verification**:
```bash
cosign verify --key cosign.pub docker.io/library/hello-world:latest
```

---

#### **Query Examples**
##### **1. Validating a Stripe Webhook**
```python
import hmac, hashlib, json, time

def verify_webhook(request):
  signature = request.headers.get("stripe-signature")
  secret_key = "whsec_abc123..."
  payload = request.get_json()

  # Reconstruct message
  timestamp = payload["timestamp"]
  payload_str = json.dumps(payload["payload"], separators=(',', ':'))
  message = f"{payload_str}{timestamp}".encode()

  # Verify HMAC
  expected_signature = hmac.new(
    secret_key.encode(),
    message,
    hashlib.sha256
  ).hexdigest()

  return hmac.compare_digest(signature, expected_signature)
```

##### **2. Checking a JWT Token**
```python
import jwt
from cryptography.hazmat.primitives import serialization

def verify_jwt(token, public_key):
  try:
    # Load public key from PEM
    pem = public_key.encode()
    public_key = serialization.load_pem_public_key(pem)

    # Decode JWT
    decoded = jwt.decode(
      token,
      public_key,
      algorithms=["RS256"],
      audience="api.example.com"
    )
    return decoded
  except jwt.ExpiredSignatureError:
    return {"error": "Token expired"}
  except jwt.InvalidTokenError:
    return {"error": "Invalid token"}
```

##### **3. Testing Docker Image Signing**
```bash
# Generate a test manifest
DIGEST=$(skopeo inspect docker://docker.io/library/hello-world:latest | jq -r '.hashes."sha256"')

# Sign the manifest (requires COSIGN_KEY)
cosign sign --key cosign.key docker.io/library/hello-world:latest

# Verify
cosign verify --key cosign.public docker.io/library/hello-world:latest
```

---

### **Requirements for Implementation**
| Requirement                          | Notes                                                                                                                                 |
|--------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| **Cryptographic Library**            | Use standardized libraries (e.g., Python `cryptography`, Java `BouncyCastle`, Go `crypto/ecdsa`).                               |
| **Key Management**                   | Store private keys securely (e.g., HSM, AWS KMS, HashiCorp Vault). Avoid hardcoding keys in source.                              |
| **Algorithm Support**                | Ensure support for multiple algorithms (e.g., RS256, ES256, HS256) for interoperability.                                           |
| **Timestamp Validation**             | Reject signatures older than `T_ttl` (e.g., 5 minutes) to prevent replay attacks.                                                  |
| **Certificate Rotation**             | Implement key rotation policies (e.g., rotate keys every 90 days) and validate certificate chains.                                |
| **Logging & Auditing**               | Log signature verification failures (without exposing sensitive data) for security audits.                                        |
| **Payload Size Limits**              | Optimize payload hashing to avoid excessive computation (e.g., truncate long payloads if needed).                               |

---

### **Common Pitfalls & Mitigations**
| Pitfall                                  | Mitigation                                                                                     |
|------------------------------------------|------------------------------------------------------------------------------------------------|
| **Hardcoded Secrets**                    | Use environment variables or secrets managers (e.g., AWS Secrets Manager).                     |
| **Algorithm Mismatches**                 | Always specify the algorithm explicitly (e.g., `"alg": "RS256"`).                              |
| **Replay Attacks**                       | Include timestamps or nonces and enforce freshness (e.g., `timestamp + 5 min`).                |
| **Key Leakage**                          | Restrict private key access to trusted processes; use short-lived keys where possible.         |
| **Invalid JSON Parsing**                 | Validate payload structure before signing (e.g., JSON schema validation).                      |
| **Performance Bottlenecks**              | Pre-compute hashes for large payloads; consider parallel verification for high-throughput systems. |

---

### **Related Patterns**
1. **[Authorization Patterns: JWT](https://example.com/jwt-pattern)**
   - Signing is foundational to JWT; use this pattern for token-based authentication.

2. **[Webhook Testing](https://example.com/webhook-testing)**
   - Combines signing with webhook request/response validation (e.g., schema checks).

3. **[Code Signing for Packages](https://example.com/package-signing)**
   - Extends signing to software distribution (e.g., npm, PyPI, Maven).

4. **[Asymmetric Encryption](https://example.com/asymmetric-encryption)**
   - Signing often pairs with encryption for end-to-end security.

5. **[OAuth 2.0 Introspection](https://example.com/oauth-introspection)**
   - Validates JWT tokens with an authorization server (similar to signature verification).

---
### **Further Reading**
- [RFC 7515 (JWT)](https://datatracker.ietf.org/doc/html/rfc7515)
- [Stripe Webhook Signing](https://stripe.com/docs/webhooks/signatures)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/)
- [OWASP Signing Testing](https://owasp.org/www-community/Signing_Testing)