**[Pattern] Messaging Verification Reference Guide**

---

### **Overview**
The **Messaging Verification** pattern ensures that messages exchanged between systems are authentic, unaltered, and correctly processed. This is achieved through cryptographic verification, checksums, or digital signatures. It helps validate:
- **Message integrity** (no tampering).
- **Sender authenticity** (message origin is trusted).
- **Non-repudiation** (sender cannot deny sending).

This pattern is critical for **transactional messaging**, **event streaming**, and **API-based communication** where security and reliability are non-negotiable. It typically involves:
1. **Message signing** (pre-production).
2. **Verification** (post-receipt).
3. **Failure handling** (if validation fails).

---

### **Schema Reference**
The following JSON schema defines the metadata required for messaging verification:

| **Field**               | **Type**       | **Description**                                                                 | **Example**                          |
|-------------------------|---------------|---------------------------------------------------------------------------------|--------------------------------------|
| `messageId`             | `string`      | Unique identifier for the message.                                              | `"msg_12345"`                        |
| `timestamp`             | `datetime`    | Timestamp of message creation (ISO 8601 format).                                | `"2024-05-20T14:30:00Z"`             |
| `sender`                | `object`      | Sender details (includes `keyId` for digital signatures).                       | `{"id": "org_abc123", "keyId": "sig_key_xyz"}` |
| `signature`             | `string`      | Base64-encoded cryptographic signature (e.g., HMAC or RSA).                     | `"a1B2c3D4e5F6..."`                  |
| `payloadHash`           | `string`      | SHA-256 hash of the message payload (for integrity checks).                     | `"a1b2c3d4e5f6..."`                  |
| `algorithm`             | `string`      | Hashing/signing algorithm (e.g., "SHA-256", "RSASSA-PKCS1-v1_5").             | `"HS256"` or `"RS256"`                |
| `expiration`            | `datetime`    | Optional: When the message becomes invalid (useful for short-lived tokens).    | `"2024-05-21T10:00:00Z"`             |

---
**Note:**
- The `payloadHash` is computed as `SHA-256(payload)` before signing.
- For **HMAC**, the `sender.keyId` references a symmetric key (shared secret).
- For **RSA**, the `sender.keyId` references a public key in a key store (e.g., AWS KMS).

---

### **Implementation Details**
#### **1. Pre-Production: Signing the Message**
Before sending, the sender:
1. Computes the **payload hash** (e.g., `SHA-256(payload)`).
2. Signs the hash using the specified algorithm (e.g., HMAC with a secret key or RSA private key).
3. Attaches the `signature`, `sender`, and `algorithm` metadata to the message.

**Example (Pseudocode for HMAC):**
```javascript
const crypto = require('crypto');
const secretKey = bufferFromEnvironment('SENDER_SECRET_KEY');
const payload = JSON.stringify({ data: "order_placed" });
const hash = crypto.createHash('sha256').update(payload).digest();
const signature = crypto.createHmac('HS256', secretKey)
                     .update(hash)
                     .digest('base64');
```

#### **2. Post-Receipt: Verification Process**
The receiver validates the message by:
1. Extracting the `signature`, `sender.keyId`, `algorithm`, and `payloadHash`.
2. Recomputing the payload hash and verifying it matches the received `payloadHash`.
3. Validating the signature using the sender’s public key (or symmetric key for HMAC).
4. Checking `expiration` (if present) to ensure timeliness.

**Example (Pseudocode for RSA Verification):**
```javascript
const jwks = await fetchPublicKeyFromKMS(sender.keyId); // e.g., AWS KMS
const signatureBuffer = bufferFromBase64(message.signature);
const payloadBuffer = bufferFromBase64(message.payloadHash);
const isValid = crypto.verify(
  'RS256',
  payloadBuffer,
  jwks.publicKey,
  signatureBuffer
);
```

#### **3. Failure Handling**
- **Invalid signature**: Log and discard the message (potential attack).
- **Mismatched hash**: Treat as corrupted (retry or alert).
- **Expired message**: Reject or queue for replay (depends on use case).

---

### **Query Examples**
#### **1. Verify a Signed Message (REST API)**
**Request:**
```http
POST /api/messages/verify
Content-Type: application/json

{
  "message": {
    "messageId": "msg_12345",
    "timestamp": "2024-05-20T14:30:00Z",
    "sender": { "id": "org_abc123", "keyId": "sig_key_xyz" },
    "signature": "a1B2c3D4e5F6...",
    "payloadHash": "a1b2c3d4e5f6...",
    "algorithm": "RS256",
    "payload": { "data": "order_placed" }
  }
}
```
**Response (Success):**
```json
{
  "valid": true,
  "messageId": "msg_12345"
}
```
**Response (Failure):**
```json
{
  "valid": false,
  "error": "Invalid signature (possible tampering)"
}
```

---
#### **2. Generate a Signed Message (Python)**
```python
import base64
import hashlib
import hmac

def sign_message(payload: str, secret_key: bytes) -> dict:
    payload_hash = hashlib.sha256(payload.encode()).digest()
    signature = hmac.new(secret_key, payload_hash, digestmod='sha256').digest()
    return {
        "signature": base64.b64encode(signature).decode(),
        "payloadHash": base64.b64encode(payload_hash).decode(),
        "algorithm": "HS256"
    }

# Usage
payload = '{"order_id": "123"}'
signed_message = sign_message(payload, b'my_secret_key_123')
```

---

### **Related Patterns**
1. **Message Encryption**
   - Complements verification by securing sensitive payloads (e.g., AES-256 encryption).
   - *Use together*: Sign the encrypted payload’s metadata + ciphertext.

2. **Idempotency Keys**
   - Ensures duplicate messages are handled safely (e.g., deduplicate via `messageId`).
   - *Use together*: Combine with verification to avoid replay attacks.

3. **Event Sourcing**
   - Stores verified messages as immutable event logs for auditing.
   - *Use together*: Replay verified messages to rebuild state.

4. **SASL/SCRAM**
   - Authenticates the sender’s identity before message exchange (e.g., in Kafka or SMTP).
   - *Use instead*: For low-latency systems where per-message signatures are too costly.

5. **Token-Based Authentication**
   - Uses JWTs or OAuth tokens for lightweight verification (stateless).
   - *Use instead*: For stateless APIs where per-message signing is impractical.

---
### **Tools/Libraries**
| **Purpose**               | **Tools**                                                                 |
|---------------------------|---------------------------------------------------------------------------|
| **Cryptography**          | OpenSSL, libsodium, crypto-js, BouncyCastle                             |
| **Key Management**        | AWS KMS, HashiCorp Vault, Azure Key Vault                               |
| **Message Queues**        | Apache Kafka (with SASL/SRPC), RabbitMQ (with AMQP 1.0 JMS), NATS.io    |
| **API Gateways**          | Kong, Apigee, AWS API Gateway (with Lambda authorizers)                  |
| **SDKs**                  | AWS SDK (Signer), Google Cloud Signer, Azure Key Vault SDK              |

---
### **Best Practices**
1. **Key Rotation**:
   - Rotate keys periodically (e.g., every 90 days) and revoke old keys in the key store.
2. **Algorithm Standards**:
   - Prefer **SHA-256** or stronger (avoid SHA-1 due to collision risks).
   - Use **RS256** or **ES256** for RSA/ECC (avoid weaker schemes like MD5).
3. **Performance**:
   - For high-throughput systems, consider **HMAC** over RSA (faster, but requires shared secrets).
4. **Logging**:
   - Log verification failures without exposing sensitive data (e.g., truncate signatures).
5. **Testing**:
   - Test with forged signatures, expired messages, and corrupted payloads.

---
### **Troubleshooting**
| **Issue**                          | **Cause**                                  | **Solution**                                  |
|-------------------------------------|--------------------------------------------|-----------------------------------------------|
| `Invalid signature`                 | Key mismatch or tampering                  | Verify key store and network integrity.       |
| `Hash mismatch`                     | Payload altered post-signing               | Enable end-to-end encryption.                 |
| `Key not found`                     | Sender key revoked or misconfigured        | Update key store or use a fallback key.      |
| `Slow validation`                   | RSA overhead in high-throughput systems    | Switch to HMAC or delegate verification to a proxy. |

---
### **Example Architecture**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
│  Sender App  │───▶│  Signer     │───▶│  Encrypted Msg  │
└─────────────┘    │  (AWS KMS)  │    └───────────────┘
                   └─────────────┘
                                      ▲
                                      │
                                      ▼
┌─────────────┐    ┌─────────────┐
│  API Gateway│───▶│  Verifier   │
│  (Kong)     │    │  (Lambda)   │
└─────────────┘    └─────────────┘
                                      ▲
                                      │
                                      ▼
┌─────────────┐
│  Consumer App│
└─────────────┘
```

---
### **References**
1. [RFC 7515 (JWT)](https://datatracker.ietf.org/doc/html/rfc7515) – Standard for JSON Web Signatures.
2. [NIST SP 800-57 (Key Management)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57_Part4.pdf).
3. [Kafka Security Guide](https://kafka.apache.org/documentation/#security).
4. [OAuth 2.0 Token Verification](https://datatracker.ietf.org/doc/html/rfc6750).