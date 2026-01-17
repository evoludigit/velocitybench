# **[Signing Patterns] Reference Guide**

---

## **Overview**
The **Signing Patterns** design pattern provides a structured way to validate and authorize API requests by embedding cryptographic signatures within requests. This pattern ensures data integrity, authentication, and non-repudiation for services where requests may originate from untrusted clients (e.g., IoT devices, third-party applications, or internal microservices).

Signing Patterns leverage asymmetric cryptography (RSA, ECDSA, Ed25519) or symmetric keys (HMAC) to generate and verify signatures. Implementations typically include:
- **Key rotation policies** (short-lived or long-term keys).
- **Timestamp validation** to prevent replay attacks.
- **Scope-based permissions** (e.g., API versioning, resource access).
- **JWT or custom signing headers** for integration flexibility.

This guide covers implementation details, schema requirements, and practical examples for RESTful APIs, gRPC, and event-driven systems.

---

## **Schema Reference**
The following tables define core components of a signing pattern implementation.

### **1. Signature Header Schema**
| **Field**            | **Type**   | **Description**                                                                                     | **Example**                          |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Authorization`      | `string`   | Base64-encoded JWT or custom signature header (e.g., `Bearer <sig>`).                              | `Bearer s3cr3t_signature_h3r3`       |
| `Signature`          | `string`   | (Alternative) Direct signature payload (e.g., HMAC-SHA256).                                        | `HMAC-SHA256=abc123...`               |
| `Key-ID`             | `string`   | Unique identifier for the signing key (e.g., AWS `JWKS` thumbprint).                                | `rsakey-20230501`                    |
| `Timestamp`          | `datetime` | UTC ISO8601 timestamp (validity window: ±5 minutes).                                                | `2023-10-15T14:30:00Z`               |
| `Scope`              | `string`   | Space-separated list of permissions (e.g., `api:read user:profile`).                               | `scope="api:v1.0 user:admin"`        |
| `Nonce`              | `string`   | Optional replay attack mitigation token (client-side generated).                                  | `nonce=1a2b3c4d-5e6f-7g8h-9i0j`     |
| `Signature-Algorithm`| `string`   | Algorithm used (e.g., `RS256`, `ES256`, `EdDSA`).                                                   | `Signature-Algorithm=EdDSA`           |

---

### **2. Request Body Signature Payload**
The signed payload (for JWT or custom signatures) includes:
| **Field**            | **Type**   | **Description**                                                                                     | **Example**                          |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `header`             | `object`   | Metadata (e.g., `alg`, `kid`, `jti`).                                                                | `{"alg":"RS256","kid":"rsakey-123"}` |
| `payload`            | `object`   | Signed data (URL-encoded or JSON Web Payload).                                                      | `{ "aud":"api.example.com", "iat":1697000000 }` |
| `signature`          | `string`   | Base64-encoded signature (generated via `HMAC-SHA256(payload + secret_key)`.                       | `signature=base64_encoded_sig`       |

**Example JWT Payload:**
```json
{
  "header": {
    "alg": "RS256",
    "kid": "rsakey-20230501"
  },
  "payload": {
    "aud": "api.example.com",
    "iat": 1697000000,
    "scope": "api:v1.0 user:create",
    "nonce": "1a2b3c4d-5e6f-7g8h-9i0j"
  },
  "signature": "base64_encoded_signature"
}
```

---

### **3. Key Management Schema**
| **Field**            | **Type**   | **Description**                                                                                     | **Example**                          |
|----------------------|------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| `Key-ID`             | `string`   | Unique identifier for the key (e.g., `sha256:abc123...`).                                          | `sha256:d5e908b3a1c2d4e5f6...`       |
| `Algorithm`          | `string`   | Supported algorithms (`RS256`, `ES256`, `HS256`, `EdDSA`).                                           | `RS256`                              |
| `Public-Key`         | `string`   | Base64-encoded PEM or JWK (JWK preferred for dynamic rotation).                                     | `{"kty":"RSA","e":"AQAB","n":"..."}` |
| `Expiry`             | `datetime` | Key validity period (e.g., 24h for short-lived keys).                                               | `2023-11-01T14:30:00Z`               |
| `Issuer`             | `string`   | Key issuer (e.g., `aws:iam`, `gcp:kms`).                                                           | `aws:iam:123456789012:signing-key`  |

---

## **Implementation Details**
### **1. Key Generation**
- **Public/Private Key Pairs**: Use RSA (2048-bit+), ECDSA (P-256/P-384), or Ed25519.
- **Key Storage**:
  - **Short-Lived Keys**: Rotate every 24h (ideal for IoT/third-party apps).
  - **Long-Term Keys**: Use HSMs (AWS KMS, HashiCorp Vault) for compliance.
  - **JWKS Endpoint**: Publish public keys at `/jwks` (JWT standard).

**Example (Ed25519 Key Pair in Python):**
```python
importssh_keys
key = ssh_keys.Ed25519Key.generate()
private_pem = key.private_pem
public_pem = key.public_pem  # For JWKS
```

---

### **2. Signing the Request**
#### **Option A: JWT-Based Signing**
1. **Create payload** with `alg`, `kid`, and signed claims (e.g., `iat`, `aud`, `scope`).
2. **Sign** using the private key:
   ```bash
   jwt_sign --algorithm RS256 --key private_key.pem --payload payload.json
   ```
3. **Append `Authorization: Bearer <jwt>`** to headers.

#### **Option B: Custom HMAC Header**
1. **Compute HMAC-SHA256** of the request body + secret key:
   ```python
   import hmac, hashlib
   secret = b"shared_secret_key"
   message = b"POST /api/reset HTTP/1.1\r\nHost: example.com\r\n..."
   signature = hmac.new(secret, message, hashlib.sha256).hexdigest()
   ```
2. **Add to headers**:
   ```
   X-Signature: HMAC-SHA256=abc123...
   X-Key-ID: shared-key-123
   ```

---

### **3. Verification**
#### **Server-Side Validation**
1. **Extract `kid`** from JWT header or `Key-ID` header.
2. **Fetch public key** from JWKS or local cache.
3. **Verify signature**:
   - For JWT: Use `pyjwt` or `jwt-lib`:
     ```python
     from jwt import verify
     verify(jwt_token, public_key, algorithms=["RS256"], audience="api.example.com")
     ```
   - For HMAC: Recompute signature and compare:
     ```python
     if hmac.compare_digest(signature, computed_signature):
         return True
     ```

4. **Check validity**:
   - Timestamp (±5 minutes).
   - Scope permissions (e.g., `scope="api:v1.0"`).
   - Nonce (if present).

---
### **4. Timeouts and Rotation**
- **Short-Lived Keys**: Validate `exp` (JWT) or `expiry` (custom) fields.
- **Replay Attack Mitigation**: Use `nonce` + `Signature-Algorithm` headers.
- **Automatic Rotation**: Integrate with AWS Lambda (for AWS KMS) or Vault.

---

## **Query Examples**
### **1. REST API Request (JWT)**
**Request:**
```http
POST /api/users HTTP/1.1
Host: example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "Alice",
  "email": "alice@example.com"
}
```

**Response (200 OK):**
```json
{
  "id": "user-123",
  "status": "created"
}
```

---
### **2. gRPC Request (HMAC)**
**Request:**
```protobuf
syntax = "proto3";
service UserService {
  rpc CreateUser (CreateUserRequest) returns (UserResponse) {
    option (google.api.http) = {
      body: "*",
      additional_bindings: {
        "@http.signature": {
          method: "POST",
          path: "v1/users"
        }
      }
    };
  }
}
```
**Headers:**
```
X-Signature: HMAC-SHA256=abc123...
X-Key-ID: hmac-key-456
```

---
### **3. Event-Driven (Kafka)**
**Payload (signed JSON):**
```json
{
  "topic": "orders.created",
  "data": { "order_id": "123", "user_id": "456" },
  "signature": "base64_encoded",
  "alg": "HS256",
  "key_id": "event-key-789"
}
```

**Server Validation:**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hmac import HMAC
import json

def verify_event(event):
    data = json.dumps(event["data"], sort_keys=True).encode()
    hmac_obj = HMAC(event["signature"].decode(), hashes.SHA256())
    hmac_obj.verify(data)
    return True
```

---

## **Error Handling**
| **Error Code** | **Description**                          | **HTTP Status** | **Example Response**                          |
|----------------|------------------------------------------|-----------------|-----------------------------------------------|
| `invalid_signature` | Signature verification failed.         | 401 Unauthorized | `{"error": "Signature invalid"}`             |
| `key_not_found`    | Key-ID not in JWKS.                     | 403 Forbidden    | `{"error": "Key not found"}`                 |
| `expired_key`      | Key has expired.                        | 403 Forbidden    | `{"error": "Key expired"}`                   |
| `scope_mismatch`   | Insufficient permissions.               | 403 Forbidden    | `{"error": "Missing scope: api:v1.0"}`       |
| `timestamp_out_of_range` | Request outside validity window.     | 403 Forbidden    | `{"error": "Timestamp invalid"}`              |

---

## **Security Considerations**
1. **Key Leakage**: Never expose private keys; use HSMs or ephemeral keys.
2. **Side-Channel Attacks**: Use constant-time comparison for HMAC verification.
3. **Replay Attacks**: Combine `nonce` + timestamp validation.
4. **Algorithm Agility**: Support multiple algorithms (e.g., `RS256` + `ES256`).
5. **Audit Logs**: Log failed signature attempts (without PII).

---

## **Related Patterns**
| **Pattern**               | **Relationship**                                                                 | **When to Use**                                  |
|---------------------------|---------------------------------------------------------------------------------|--------------------------------------------------|
| **JWT (JSON Web Tokens)** | Signing Patterns often use JWT for token-based auth.                             | Stateless authentication.                        |
| **OAuth 2.0**             | Signing Patterns can replace OAuth tokens for API requests.                      | Delegated authorization (third-party apps).      |
| **API Gateway Signing**   | Some gateways (e.g., AWS API Gateway) support custom signing headers.         | Serverless architectures.                        |
| **MFA with Signing**      | Combine with TOTP or hardware tokens for multi-factor auth.                     | High-security APIs.                              |
| **gRPC Signing**          | Extend gRPC with HTTP-style signing headers.                                    | Microservices communication.                     |
| **Webhooks Signing**      | Sign webhook payloads to prevent spoofing.                                      | Event-driven systems (e.g., Stripe, GitHub).     |
| **HMAC vs. Asymmetric**  | Symmetric (HMAC) for shared secrets; asymmetric (RSA/ECDSA) for keys.         | Tradeoff: HMAC (faster) vs. RSA (more secure).   |

---
## **Tools and Libraries**
| **Language**  | **Library**                          | **Features**                                  |
|---------------|--------------------------------------|-----------------------------------------------|
| Python        | `cryptography`, `pyjwt`              | HMAC, RSA, ECDSA, JWT support.                |
| Node.js       | `jsonwebtoken`, `crypto`             | JWT, HMAC, EdDSA.                             |
| Go            | `github.com/golang/jwt`, `golang.org/x/crypto` | JWT, HMAC, RSA.          |
| Java          | `jjwt`, `BC Providers`               | JWT, ECDSA, EdDSA.                            |
| .NET          | `System.IdentityModel.Tokens.Jwt`    | JWT, RSA, HMAC.                               |

---
## **Performance Optimizations**
1. **Key Caching**: Cache public keys in-memory (TTL: 1 hour).
2. **Parallel Verification**: Use async workers for high-throughput APIs.
3. **Short Payloads**: Minimize data signed (e.g., exclude `Authorization` header from HMAC).
4. **Algorithm Selection**: Prefer Ed25519 or ES256 over RSA for speed.

---
## **Migration Strategy**
1. **Phased Rollout**: Deploy signing alongside legacy auth (e.g., API keys).
2. **Backward Compatibility**: Allow both signed and unsigned requests temporarily.
3. **Deprecation Policy**: Set `Deprecation-Time` in headers (e.g., `Deprecation-Time: 2024-05-01`).

---
## **Example: Full Workflow**
### **1. Client (Python) Signs Request**
```python
import hmac, hashlib, time
from cryptography.hazmat.primitives import serialization

# Load private key
with open("private_key.pem", "rb") as f:
    key = serialization.load_pem_private_key(
        f.read(),
        password=None
    )

# Generate HMAC signature
message = b"POST /api/data\r\nHost: example.com\r\nContent-Type: application/json"
signature = hmac.new(
    key.private_bytes(encoding=serialization.Encoding.DER, format=serialization.PrivateFormat.PKCS8,
                     encryption_algorithm=serialization.NoEncryption()),
    message,
    hashlib.sha256
).hexdigest()

# Send request
headers = {
    "X-Signature": f"HMAC-SHA256={signature}",
    "X-Key-ID": "my-key-123",
    "X-Timestamp": str(int(time.time()))
}
response = requests.post("https://example.com/api/data", headers=headers)
```

### **2. Server Verifies Signature**
```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.hmac import HMAC

def verify_signature(request):
    key_id = request.headers.get("X-Key-ID")
    if key_id != "my-key-123":
        return False

    # Fetch public key (from JWKS or cache)
    public_key = get_public_key(key_id)
    message = b"POST /api/data\r\nHost: example.com\r\nContent-Type: application/json"
    hmac_obj = HMAC(public_key, hashes.SHA256())
    hmac_obj.verify(request.headers["X-Signature"].split("=")[1].encode())
    return True
```

---
## **Troubleshooting**
| **Issue**                     | **Diagnosis**                          | **Solution**                                  |
|-------------------------------|----------------------------------------|-----------------------------------------------|
| `Signature invalid`           | Key rotation not handled.             | Update `Key-ID` in JWKS.                      |
| `Timestamp expired`           | Server clock skew.                     | Sync clocks (NTP).                           |
| `Scope mismatch`              | Incorrect permissions.                 | Update `scope` header or grant permissions.   |
| **Slow verification**         | Large payloads signed.                 | Exclude headers from signature (e.g., `Host`). |

---
## **Further Reading**
- [RFC 7515 (JWT)](https://datatracker.ietf.org/doc/html/rfc7515) (Standard for JWT).
- [AWS Signing AWS Requests](https://docs.aws.amazon.com/general/latest/gr/signing-aws-api-requests.html) (HMAC-SHA256 examples).
- [Google’s gRPC Signing](https://cloud.google.com/endpoints/docs/openapi/validate-requests-with-signatures) (Custom headers).
- [OWASP Signing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Signature_Cheatsheet.html).