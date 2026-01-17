---
# **[Pattern] **Signing Guidelines Reference Guide**

---

## **Overview**
The **Signing Guidelines** pattern defines a standardized process for validating and enforcing digital signatures on critical system operations, mitigating risks like unauthorized access, data tampering, and compliance violations. This pattern ensures that only authenticated and authorized actions are executed—such as API calls, configuration changes, or deployments—by requiring cryptographic verification of signers via **JWT (JSON Web Tokens)** or **TLS client certificates**.

Key use cases include:
- **API Security**: Protecting against API abuse or unauthorized invocations.
- **Infrastructure Operations**: Validating deployments, CI/CD pipelines, or cloud resource updates.
- **Regulatory Compliance**: Ensuring audit trails for signed actions (e.g., GDPR, HIPAA).
- **Service-to-Service Auth**: Trusted communication between microservices in distributed systems.

---

## **Schema Reference**
Below is the core schema for implementing **Signing Guidelines**. Customize fields based on your authentication mechanism (JWT, X.509, etc.).

| **Field**               | **Type**         | **Description**                                                                                     | **Example Value**                          |
|-------------------------|------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------------|
| `signature`             | String (Base64)  | The cryptographic signature (HMAC-SHA256, RSA, or ECDSA) of the signed payload.                     | `"d123...abc456"`                          |
| `algorithm`             | String           | Signing algorithm used (e.g., `HS256`, `RS256`, `ES256`).                                             | `"RS256"`                                  |
| `signed_at`             | Datetime (ISO8601)| Timestamp of when the signature was generated (prevents replay attacks).                             | `"2024-02-20T12:00:00Z"`                  |
| `key_id`                | String           | Unique identifier for the signing key (e.g., JWK thumbprint or X.509 CN).                           | `"key-12345"`                              |
| `payload_hash`          | String (Base64)  | SHA-256 hash of the signed data (required for verification).                                        | `"a1b2...c3d4"`                            |
| `aud` (Optional)        | String           | Audience claim (JWT) to restrict signature validity to specific services.                           | `"api.v1.example.com"`                     |
| `iss` (Optional)        | String           | Issuer identifier (JWT) to validate the signer’s identity.                                          | `"org-corp-issuer"`                       |
| `exp` (Optional)        | Datetime (ISO8601)| Expiration time for the signature (prevents stale signatures).                                     | `"2024-03-01T00:00:00Z"`                  |

---

## **Implementation Details**
### **1. Core Components**
- **Signing Key Management**:
  - Use **Hardware Security Modules (HSMs)** or **AWS KMS**/**Azure Key Vault** for key storage (never hardcode private keys).
  - Rotate keys periodically (e.g., quarterly) and revoke compromised keys.
- **Payload Validation**:
  - Sign **only critical, immutable fields** (e.g., API requests, config updates). Exclude non-deterministic fields like timestamps.
  - Example payload (simplified):
    ```json
    {
      "action": "deploy",
      "resource": "/app/v1",
      "params": { "env": "prod" }
    }
    ```
  - Hash the payload (SHA-256) before signing to ensure integrity.
- **Signature Verification**:
  - Validate:
    1. **Signature correctness** (HMAC/RSA/ECDSA).
    2. **Key validity** (check `key_id` against a trusted keystore).
    3. **Timestamp freshness** (`signed_at` + `exp`).
    4. **Audience/issuer claims** (if applicable).

---

### **2. Algorithms**
| **Algorithm** | **Use Case**                          | **Security Notes**                                  |
|----------------|---------------------------------------|----------------------------------------------------|
| `HS256`        | Symmetric signing (shared secret).   | Use only in low-risk scenarios (e.g., internal services). |
| `RS256`        | Asymmetric (RSA-SHA256).              | Preferred for public/private key pairs.           |
| `ES256`        | Asymmetric (ECDSA-SHA256).            | Faster than RSA, suitable for IoT/edge devices.    |

---

### **3. Error Handling**
| **Error Code** | **Description**                          | **HTTP Status (API)** | **Remediation**                          |
|----------------|------------------------------------------|-----------------------|------------------------------------------|
| `SIG_001`      | Invalid signature verification.          | `401 Unauthorized`    | Check key/algorithm or resubmit.         |
| `SIG_002`      | Expired signature.                       | `403 Forbidden`       | Request a new signature.                |
| `SIG_003`      | Missing required fields (`key_id`, etc.). | `400 Bad Request`     | Provide all required signature metadata. |
| `SIG_004`      | Key revoked or invalid.                  | `403 Forbidden`       | Update your keystore.                    |

---

## **Query Examples**
### **1. Signing a Request (Python Example)**
```python
import hmac
import hashlib
import json

# Payload
payload = {
    "action": "deploy",
    "resource": "/app/v1",
    "params": {"env": "prod"}
}

# Convert to JSON string and encode to bytes
payload_str = json.dumps(payload, sort_keys=True).encode("utf-8")
payload_hash = hashlib.sha256(payload_str).digest()

# Sign with HMAC-SHA256 (shared secret)
secret_key = b"your-256-bit-secret-key"
signature = hmac.new(secret_key, payload_hash, hashlib.sha256).hexdigest()

# Output
{
    "signature": signature,
    "algorithm": "HS256",
    "signed_at": "2024-02-20T12:00:00Z",
    "key_id": "main-secret",
    "payload_hash": hashlib.sha256(payload_str).hexdigest()
}
```

### **2. Verifying a Signature (Go Example)**
```go
package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"log"
)

type SignedRequest struct {
	Signature    string `json:"signature"`
	Algorithm    string `json:"algorithm"`
	PayloadHash  string `json:"payload_hash"`
	KeyID        string `json:"key_id"`
}

func verifySignature(sig SignedRequest, payload []byte, secretKey []byte) bool {
	// Compute payload hash again
	computedHash := sha256.Sum256(payload)
	expectedHash := sig.PayloadHash

	if sig.PayloadHash != fmt.Sprintf("%x", computedHash) {
		return false
	}

	// Verify HMAC
	mac := hmac.New(sha256.New, secretKey)
	mac.Write(computedHash[:])
	expectedSig := fmt.Sprintf("%x", mac.Sum(nil))

	return sig.Signature == expectedSig
}

func main() {
	payload := map[string]interface{}{"action": "deploy", "resource": "/app/v1"}
	payloadBytes, _ := json.Marshal(payload)

	sig := SignedRequest{
		Signature:    "d123...abc456", // Replace with actual signature
		Algorithm:    "HS256",
		PayloadHash:  "a1b2...c3d4",   // SHA-256 of payload
		KeyID:        "main-secret",
	}

	if !verifySignature(sig, payloadBytes, []byte("your-256-bit-secret-key")) {
		log.Fatal("Invalid signature")
	}
	fmt.Println("Signature verified successfully!")
}
```

---

## **Related Patterns**
1. **[Authentication Patterns]**
   - *Related to*: Integrates with **JWT/OAuth 2.0** for identity validation before signature verification.
   - *Reference*: [OAuth 2.0 Core](https://datatracker.ietf.org/doc/html/rfc6749).

2. **[Cryptographic Key Management]**
   - *Related to*: Key rotation, HSMs, and certificate revocation lists (CRLs) for signing keys.
   - *Reference*: [NIST SP 800-57](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-57.1r5.pdf).

3. **[Audit Logging]**
   - *Related to*: Logging signed events for compliance (e.g., store `key_id`, `signed_at`, and `action`).
   - *Reference*: [ISO 27001 Annex A.12](https://www.iso.org/standard/54534.html).

4. **[Rate Limiting]**
   - *Related to*: Combine with signing to prevent brute-force attacks on signatures.
   - *Reference*: [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket).

5. **[Distributed Tracing]**
   - *Related to*: Correlate signed requests across services using `trace_id` or `request_id` in the payload.

---
## **Best Practices**
- **Key Rotation**: Rotate signing keys every 90 days (or per NIST guidelines).
- **Payload Design**: Avoid signing dynamic fields (e.g., timestamps, UUIDs).
- **Key Isolation**: Use separate keys for different environments (dev/stage/prod).
- **Performance**: Cache verified keys (TTL: 1 hour) to avoid repeated validation.
- **Fallbacks**: For high-latency systems, implement **short-lived signatures** (e.g., `exp` ≤ 5 minutes).

---
## **Troubleshooting**
| **Issue**               | **Diagnostic Steps**                                                                 | **Tools**                          |
|-------------------------|---------------------------------------------------------------------------------------|------------------------------------|
| Signature fails         | Check `payload_hash`, `algorithm`, and `key_id` mismatch.                             | `openssl dgst -sha256 -hmac secret payload.json` |
| Key revocation          | Verify `key_id` isn’t in the revocation list.                                         | CRL/OCSP checks                    |
| Timestamp skew          | Ensure `signed_at` and server clock are within 5-minute tolerance.                   | NTP synchronization               |
| Missing fields          | Validate schema compliance (e.g., `aud` claim for JWT).                               | JSON schema validator (Ajv)        |

---
**Last Updated**: 2024-02-20
**Version**: 1.2