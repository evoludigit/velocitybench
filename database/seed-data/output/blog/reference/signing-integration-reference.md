# **[Pattern] Signing Integration Reference Guide**

---

## **Overview**
**Signing Integration** is a security pattern used to verify the authenticity and integrity of messages, APIs, or data exchanges between parties. By leveraging cryptographic signatures (e.g., HMAC, RSA, ECDSA), this pattern ensures that:
- Unauthorized parties cannot alter data without detection.
- Messages originate from a trusted source.
- Tampering during transit (e.g., in APIs or messaging systems) is detected.

This guide covers implementation requirements, data schemas, sample queries, and related patterns. It assumes prior knowledge of cryptographic signing (e.g., JSON Web Signatures, OAuth 2.0 tokens, or API keys).

---

## **Key Concepts**
| **Term**               | **Description**                                                                 | **Example Use Case**                     |
|-------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **Signer**              | Entity responsible for generating signatures (e.g., a service, user, or device). | API server or IoT device.               |
| **Verifier**            | Entity checking signatures for validity (e.g., a client or middleware).       | Mobile app validating a received token. |
| **Secret Key/Public Key** | Symmetric (HMAC) or asymmetric (RSA/ECDSA) keys for signing/verification.       | API authentication keys or TLS certs.    |
| **Integrity Check**     | Verification that data hasn’t been altered since signing.                       | Checking a signed API response payload.  |
| **Nonce**               | Unique token to prevent replay attacks.                                        | Unique timestamp in OAuth tokens.       |

---

## **Implementation Requirements**
### **1. Prerequisites**
- **Cryptographic Library**: Use a library that supports your chosen algorithm (e.g., Python’s `cryptography`, Node.js’s `jsonwebtoken`, or Java’s `Bouncy Castle`).
  - *Example Algorithms*:
    - Symmetric: HMAC-SHA256, HMAC-SHA512.
    - Asymmetric: RSA-SHA256, ECDSA-SHA256.
- **Key Management**:
  - Store keys securely (e.g., AWS KMS, HashiCorp Vault, or HSMs).
  - Rotate keys periodically (e.g., every 90 days for RSA).
- **Message Format**:
  - For APIs: Sign the entire request/response payload (excluding headers).
  - For messaging: Sign headers + body (e.g., AWS SNS, Kafka).

### **2. Steps to Implement**
1. **Generate Keys**:
   - Use tools like OpenSSL (`openssl genpkey -algorithm RSA -out private_key.pem`) or libraries to create keypairs.
   - Example (Python):
     ```python
     from cryptography.hazmat.primitives import serialization
     private_key = generate_private_key(Algorithm.RSA, key_size=2048)
     private_pem = private_key.private_bytes(
         encoding=serialization.Encoding.PEM,
         format=serialization.PrivateFormat.PKCS8,
         encryption_algorithm=serialization.NoEncryption()
     )
     ```

2. **Sign Data**:
   - Hash the data, then sign it with the private key.
   - Example (HMAC in Node.js):
     ```javascript
     const crypto = require('crypto');
     const hmac = crypto.createHmac('sha256', 'your-secret-key');
     const signature = hmac.update('data-to-sign').digest('hex');
     ```

3. **Verify Signatures**:
   - Reconstruct the signature using the public key (asymmetric) or shared secret (symmetric).
   - Example (RSA Verification in Java):
     ```java
     PublicKey publicKey = loadPublicKeyFromFile("public_key.pem");
     Signature sig = Signature.getInstance("SHA256withRSA");
     sig.initVerify(publicKey);
     sig.update(dataBytes);
     boolean valid = sig.verify(signatureBytes);
     ```

4. **Handle Errors**:
   - Invalid signatures → Reject requests (e.g., HTTP 401 Unauthorized).
   - Expired nonces → Block replay attacks.

---

## **Schema Reference**
### **Signing Request/Response Payload**
| **Field**               | **Type**      | **Required** | **Description**                                                                 | **Example**                          |
|--------------------------|---------------|--------------|---------------------------------------------------------------------------------|--------------------------------------|
| `signature`              | String        | Yes          | Base64-encoded cryptographic signature of the payload.                           | `a1B2c3D4...`                       |
| `signed_data`            | Object/JSON   | Yes          | The original data payload signed.                                                | `{ "user_id": 123, "action": "login" }` |
| `algorithm`              | String        | Yes          | Signing algorithm used (e.g., `HMAC-SHA256`, `RSASSA-PKCS1-v1_5`).               | `RS256`                             |
| `key_id`                 | String        | Optional     | Identifier for the signing key (e.g., fingerprint or alias).                     | `rsa-key-1234`                      |
| `nonce`                  | String        | Optional     | Unique token to prevent replay attacks.                                          | `xyz789`                            |
| `timestamp`              | String (ISO8601) | Optional    | UTC timestamp of signing (e.g., for expiration checks).                          | `2023-10-01T12:00:00Z`              |

---

### **Example JSON Payload**
```json
{
  "signature": "a1B2c3D4...",
  "signed_data": {
    "user_id": 123,
    "action": "login"
  },
  "algorithm": "HS256",
  "key_id": "shared-secret-abc",
  "nonce": "xyz789"
}
```

---

## **Query Examples**
### **1. Signing an API Request (Python)**
```python
import hmac
import hashlib
import base64

def sign_request(data: dict, secret: str) -> dict:
    data_str = json.dumps(data, sort_keys=True).encode('utf-8')
    signature = hmac.new(secret.encode('utf-8'), data_str, hashlib.sha256).hexdigest()
    return {"signed_data": data, "signature": signature, "algorithm": "HS256"}

# Usage
request_data = {"user_id": 123, "action": "login"}
signed = sign_request(request_data, "your-secret-key")
```

### **2. Verifying a Signed API Response (Node.js)**
```javascript
const crypto = require('crypto');

function verifyResponse(response) {
  const expectedSig = crypto
    .createHmac('sha256', 'your-secret-key')
    .update(JSON.stringify(response.signed_data))
    .digest('hex');

  return expectedSig === response.signature;
}

// Usage
const response = {
  signed_data: { user_id: 123, action: "login" },
  signature: "a1B2c3D4...",
  algorithm: "HS256"
};

if (!verifyResponse(response)) {
  throw new Error("Invalid signature");
}
```

### **3. Signing a Kafka Message (Pseudocode)**
```python
// Producer
def sign_kafka_message(message: str, private_key: RSAPrivateKey):
  sha256_hash = hashlib.sha256(message.encode()).digest()
  signature = private_key.sign(sha256_hash, padding.PSS(mgf=padding.MGF1(hashes.SHA256())))
  return {
    "payload": message,
    "signature": base64.b64encode(signature).decode(),
    "alg": "RS256"
  }
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                      |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------------------|
| **[JWT (JSON Web Tokens)](https://jwt.io/)** | Stateless authentication using signed tokens.                                  | API authentication, session management.             |
| **[OAuth 2.0](https://oauth.net/2/)**          | Delegated access with signed tokens (e.g., `id_token`).                          | Third-party integrations (e.g., Google Login).       |
| **[API Gateway Signing](https://aws.amazon.com/api-gateway/)** | Gateways (e.g., AWS API Gateway) may require client-side signing.            | Serverless architectures with custom signatures.    |
| **[TLS/SSL Encryption](https://www.digicert.com/ssl-tls/what-is-tls.htm)** | End-to-end encryption for data in transit.                                      | Secure HTTP(S) communication.                        |
| **[HMAC for Shared Secrets](https://datatracker.ietf.org/doc/html/rfc2104)** | Symmetric signing for APIs where both parties share a secret.                  | Internal microservices communication.               |

---

## **Best Practices**
1. **Key Rotation**: Automate key rotation (e.g., quarterly for RSA).
2. **Short-Lived Signatures**: Use nonces or timestamps to limit signature validity.
3. **Algorithm Agility**: Support multiple algorithms (e.g., `RS256`, `ES256`) for future compatibility.
4. **Logging**: Log signature failures (without exposing secrets) for auditing.
5. **Performance**: For high-throughput systems, precompute signatures (e.g., batch signing).

---
## **Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                      |
|-------------------------------------|--------------------------------------------|---------------------------------------------------|
| Signature verification fails       | Incorrect secret/key used.                | Double-check key storage and encoding (e.g., base64). |
| Replay attacks detected            | Missing nonce or stale timestamp.         | Implement nonce tracking or short-lived tokens.    |
| Slow signing latency               | Large payloads or inefficient library.     | Optimize payload size or use faster algorithms.   |
| Key compromise suspected          | Unknown source of leaks.                   | Rotate keys immediately and investigate access logs. |

---
**See Also**:
- [RFC 7515 (JWS)](https://datatracker.ietf.org/doc/html/rfc7515) (JSON Web Signatures).
- [OAuth 2.0 Security Best Practices](https://auth0.com/blog/critical-oauth-2-0-security-considerations/).