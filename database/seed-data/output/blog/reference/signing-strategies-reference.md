# **[Pattern] Signing Strategies Reference Guide**

---

## **Overview**
This guide provides a structured reference for implementing **Signing Strategies**—a design pattern used to manage cryptographic signing workflows in distributed systems, APIs, and microservices. Signing Strategies standardize how data (e.g., requests, responses, or payloads) is verified and authenticated using digital signatures (e.g., JWT, HMAC, RSA, or ECDSA). The pattern decouples signing logic from business logic, enabling flexibility for security policies, key rotation, and algorithmic upgrades while improving maintainability and auditability.

**Key Benefits:**
- Security: Prevents tampering and ensures data integrity.
- Flexibility: Supports multiple signing algorithms and key types.
- Extensibility: Easily integrate new signing providers or policies.
- Compliance: Facilitates audit trails for regulatory requirements.

---

## **Key Concepts**
### **1. Components of a Signing Strategy**
| **Component**       | **Purpose**                                                                 | **Examples**                                                                 |
|----------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| **Signer**           | Generates digital signatures using a signing key.                           | RSA, ECDSA, HMAC, or custom providers.                                        |
| **Verifier**         | Validates signatures against a verification key.                             | OpenSSL, CryptoJS, or framework-specific libraries (e.g., Spring Security).   |
| **Signing Policy**   | Defines rules for when/where to sign (e.g., per request, per payload field). | JWT header claims, payload fields, or metadata signing.                        |
| **Key Management**   | Handles key generation, storage, and rotation.                              | AWS KMS, HashiCorp Vault, or HSMs (Hardware Security Modules).                 |
| **Strategy Interface** | Abstracts signing logic into reusable implementations.                    | `ISigningStrategy<T>` (e.g., `JwtSigner`, `HmacSigner`).                     |

### **2. Signing Workflow**
1. **Pre-Signing:**
   - Apply signing policy to determine what to sign (e.g., `Authorization` header or payload).
   - Retrieve the current signing key from the key management system.
2. **Signing:**
   - The `Signer` creates a signature over the target data.
   - The data + signature are combined (e.g., JWT `payload.signature`).
3. **Verification:**
   - The `Verifier` extracts the signature and data.
   - The data is re-signed using the public/verification key.
   - Compare the re-signed data with the received signature.

---

## **Implementation Details**

### **1. Schema Reference**
Use the following schema to define a signing strategy implementation:

| **Field**            | **Type**               | **Description**                                                                 | **Required** | **Notes**                                                                 |
|----------------------|------------------------|-------------------------------------------------------------------------------|--------------|---------------------------------------------------------------------------|
| `strategyName`       | `String`               | Unique identifier for the signing strategy (e.g., `"jwt-rsa"`).               | Yes          | Used for dependency injection or configuration.                           |
| `signer`             | `Object`               | Configuration for the signer component.                                       | Yes          | Includes `algorithm`, `keyId`, and `key` (or `keyReference`).               |
| `signer.algorithm`   | `Enum` (`RSA`, `ECDSA`, `HMAC`, `custom`) | Specifies the cryptographic algorithm.                                        | Yes          | Must match the key type (e.g., use `RS256` for RSA).                        |
| `signer.keyId`       | `String`               | Identifier for the signing key (e.g., KMS ARN).                               | Yes          | Used to fetch the key from the key management system.                     |
| `signer.key`         | `String` (**Base64**)  | Raw key (for testing only; avoid in production).                            | No           | Overrides `keyId` if provided.                                            |
| `verifier`           | `Object`               | Configuration for the verifier component.                                     | Yes          | Includes `algorithm` and `keyId` (must match signer’s public key).         |
| `verifier.algorithm` | `Enum` (`RS256`, `ES256`, `HS256`, `custom`) | Verification algorithm (must match signer).                                  | Yes          |                                                                                |
| `verifier.keyId`     | `String`               | Identifier for the verification key.                                          | Yes          | Typically the same as `signer.keyId` (public key counterpart).            |
| `policy`             | `Object`               | Rules for when/where to sign.                                                 | No           | Defaults to signing the entire payload or header.                          |
| `policy.fields`      | `Array[String]`        | Specific fields to sign (e.g., `["timestamp", "userId"]`).                   | No           | Used for selective signing (e.g., JWT claims).                           |
| `policy.header`      | `String`               | HTTP header to sign (e.g., `"x-api-key"`).                                   | No           | Applies to REST/gRPC requests.                                            |
| `policy.ttl`         | `Integer` (seconds)    | Time-to-live for the signature (optional).                                    | No           | Enforces signature expiration (e.g., for JWT).                          |

**Example Schema (JSON):**
```json
{
  "strategyName": "jwt-rsa",
  "signer": {
    "algorithm": "RS256",
    "keyId": "arn:aws:kms:us-east-1:123456789012:key/abcd1234",
    "key": null
  },
  "verifier": {
    "algorithm": "RS256",
    "keyId": "arn:aws:kms:us-east-1:123456789012:key/abcd1234-public"
  },
  "policy": {
    "fields": ["iat", "exp", "sub"],
    "header": "Authorization"
  }
}
```

---

### **2. Implementation Steps**
#### **Step 1: Define the Strategy Interface**
```csharp
// C# Example
public interface ISigningStrategy<T>
{
    string Sign(T data);
    bool Verify(string data, string signature);
}
```

#### **Step 2: Implement a Concrete Strategy (e.g., JWT Signer)**
```java
// Java Example (Using JWT Library)
public class JwtSigningStrategy implements ISigningStrategy<Map<String, Object>> {
    private final JwtBuilder jwtBuilder;
    private final JwtVerifier jwtVerifier;

    public JwtSigningStrategy(...) {
        // Initialize with signer/verifier configs
    }

    @Override
    public String Sign(Map<String, Object> payload) {
        return jwtBuilder.setClaims(payload).sign();
    }

    @Override
    public boolean Verify(String token, String signature) {
        return jwtVerifier.verify(token, signature);
    }
}
```

#### **Step 3: Integrate with Dependency Injection**
```python
# Python Example (Using FastAPI + PyJWT)
from fastapi import Depends
from fastapi.security import APIKeyHeader

async def get_signing_strategy() -> ISigningStrategy:
    config = load_config()  # Load from schema
    return JwtSigningStrategy(**config)
```

#### **Step 4: Apply to HTTP Requests/Responses**
``` typescript
// TypeScript Example (Express Middleware)
app.use((req: Request, res: Response, next: NextFunction) => {
  const strategy = getSigningStrategy(req.config);
  const signature = req.headers["x-signature"];
  if (!strategy.verify(req.body, signature)) {
    return res.status(401).send("Invalid signature");
  }
  next();
});
```

---

### **3. Query Examples**
#### **Example 1: Signing a JWT Payload**
**Input:**
```json
{
  "sub": "user123",
  "iat": 1625097600,
  "exp": 1625184000
}
```
**Strategy Config:**
```json
{
  "strategyName": "jwt-rsa",
  "signer": { "algorithm": "RS256", "keyId": "key-rsa" },
  "verifier": { "algorithm": "RS256", "keyId": "key-rsa-public" }
}
```
**Output (Signed JWT):**
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### **Example 2: Signing an API Request Header**
**Request Headers:**
```http
POST /api/data
x-api-key: "secret"
x-signature: "HmacSHA256(key=secret,data=timestamp=1625097600)"
```
**Strategy Config:**
```json
{
  "strategyName": "hmac-header",
  "signer": { "algorithm": "HS256", "key": "base64-encoded-secret" },
  "policy": { "header": "x-api-key" }
}
```

#### **Example 3: Selective Field Signing**
**Payload:**
```json
{
  "userId": "123",
  "email": "user@example.com",
  "timestamp": "2021-07-01T00:00:00Z"
}
```
**Strategy Config:**
```json
{
  "strategyName": "selective-sign",
  "signer": { "algorithm": "ECDSA", "keyId": "key-ecdsa" },
  "policy": { "fields": ["userId", "timestamp"] }
}
```
**Output (Signature Covering Only `userId` and `timestamp`):**
```
"signature=signature-data-over-userId-and-timestamp"
```

---

## **Query Examples (API Calls)**
### **1. Register a New Signing Strategy**
```http
POST /api/signing-strategies
Content-Type: application/json

{
  "strategyName": "audit-log-sign",
  "signer": { "algorithm": "RS256", "keyId": "arn:aws:kms:...:key/audit" },
  "policy": { "header": "x-audit-log" }
}
```

### **2. Verify a Signature**
```http
POST /api/verify-signature
Content-Type: application/json

{
  "strategyName": "jwt-rsa",
  "data": "eyJhbGciOiJSUzI1NiIs...",
  "signature": "signature-data"
}
```

### **3. Rotate a Signing Key**
```http
PUT /api/signing-strategies/jwt-rsa/keys
{
  "currentKeyId": "old-key-id",
  "newKeyId": "new-key-id",
  "algorithm": "RS256"
}
```

---

## **Error Handling**
| **Error Code** | **Description**                          | **Example Response**                          |
|----------------|------------------------------------------|-----------------------------------------------|
| `400 Bad Request` | Invalid signature format.               | `{ "error": "InvalidSignatureFormat" }`     |
| `401 Unauthorized` | Signature verification failed.          | `{ "error": "SignatureVerificationFailed" }` |
| `403 Forbidden`   | Key not found or expired.               | `{ "error": "KeyNotFound" }`                 |
| `500 Internal Error` | Key management service unavailable.     | `{ "error": "KeyServiceUnavailable" }`       |

---

## **Related Patterns**
1. **[Authentication Patterns](link-to-docs):**
   - Integrates Signing Strategies with OAuth2, OpenID Connect, or API keys.
2. **[Key Management Patterns](link-to-docs):**
   - Covers HSMs, KMS, and Vault integration for key rotation.
3. **[Payload Transformation Patterns](link-to-docs):**
   - Uses Signing Strategies alongside data serialization (e.g., Avro, Protobuf).
4. **[Rate Limiting with Signatures](link-to-docs):**
   - Combines signatures with rate-limiting policies (e.g., signed tokens with TTL).
5. **[Idempotency Patterns](link-to-docs):**
   - Signs requests to ensure idempotent operations (e.g., `x-idempotency-key`).