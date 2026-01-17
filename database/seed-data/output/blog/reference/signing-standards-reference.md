# **[Signing Standards] Reference Guide**

## **Overview**
The **Signing Standards** pattern ensures secure, auditable, and machine-readable authentication of API requests, messages, and data exchanges by enforcing consistent cryptographic signing practices. This pattern defines how entities (clients, servers, or services) generate, validate, and handle cryptographic signatures using standardized algorithms, key management, and message formats. It is critical for securing data integrity, preventing tampering, and enabling compliance with security policies. This guide provides implementation details, schema references, and best practices for adopting this pattern in distributed systems.

---

## **1. Key Concepts**

| **Term**               | **Description**                                                                                     |
|------------------------|-----------------------------------------------------------------------------------------------------|
| **Signature Algorithm** | Cryptographic method (e.g., HMAC-SHA256, RSASSA-PSS) used to generate/validate signatures.           |
| **Key Pair**           | A pair of cryptographic keys (public for verification, private for signing).                       |
| **Base64 Encoding**    | Ensures signatures are URL-safe and can be transmitted as text.                                   |
| **Header Signing**     | Signing HTTP headers (e.g., `Authorization` or custom headers) to validate request authenticity.    |
| **Payload Signing**    | Signing request/response bodies to ensure message integrity.                                       |
| **Signature Expiration**| Time-based validity for signatures to mitigate replay attacks.                                     |
| **Key Rotation**       | Periodic replacement of private keys to reduce exposure risks.                                        |
| **Signature Format**  | Standardized output (e.g., `Signature="<signed-data>"`) for parsing and validation.              |

---
## **2. Implementation Requirements**

### **2.1 Core Requirements**
| **Requirement**               | **Description**                                                                                     |
|-------------------------------|-----------------------------------------------------------------------------------------------------|
| **Algorithm Choice**          | Use widely supported algorithms (e.g., **HMAC-SHA256**, **RSASSA-PSS-2048**, or **Ed25519** for key efficiency). |
| **Key Management**            | Store private keys in secure environments (HSMs, AWS KMS, or HashiCorp Vault) with restricted access. |
| **Message Canonicalization**  | Convert unstructured data (e.g., JSON/XML) into a standardized string (e.g., Canonical JSON) before signing. |
| **Timestamping**              | Include a timestamp to prevent replay attacks (e.g., `x-signing-timestamp="2024-05-20T12:00:00Z"`). |
| **Signature Validation**      | Verify signatures using the sender’s public key during request processing.                         |

---
## **2.2 Supported Algorithms**
| **Algorithm**      | **Key Type**       | **Description**                                                                                     | **Use Case**                          |
|--------------------|--------------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| HMAC-SHA256         | Symmetric (Secret) | Shared secret key (e.g., API keys).                                                               | Low-security internal APIs.           |
| RSASSA-PSS-2048     | Asymmetric         | RSA with PSS padding (FIPS 186-5 compliant).                                                       | High-security APIs, compliance.       |
| Ed25519             | Asymmetric         | Efficient elliptic-curve cryptography (no padding needed).                                          | High-performance APIs.                |
| ECDSA (P-256)       | Asymmetric         | Elliptic-curve digital signature (suitable for mobile/web clients).                               | Mobile/web-based authentication.      |

---
## **3. Schema Reference**
### **3.1 Signing Header Schema (HTTP)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Signing Headers",
  "type": "object",
  "properties": {
    "Authorization": {
      "type": "string",
      "description": "Bearer token or signed header format (e.g., `Signature=...`)",
      "examples": [
        "Signature keyId=\"abc123\",algorithm=\"HMAC-SHA256\",headers=\"(request-target) host date\",signature=\"d5e...\""
      ]
    },
    "X-Signature-Algorithm": {
      "type": "string",
      "description": "Cryptographic algorithm used (e.g., \"RSASSA-PSS-2048\").",
      "enum": ["HMAC-SHA256", "RSASSA-PSS-2048", "Ed25519", "ECDSA-P256"]
    },
    "X-Public-Key": {
      "type": "string",
      "description": "Base64-encoded public key for verification (optional if pre-shared).",
      "format": "base64"
    },
    "X-Signing-Timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp to prevent replay attacks."
    },
    "X-Signature": {
      "type": "string",
      "description": "Base64-encoded signature of the signed headers/payload.",
      "format": "base64"
    }
  },
  "required": ["Authorization"]
}
```

---
### **3.2 Signed Payload Schema (JSON)**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Signed JSON Payload",
  "type": "object",
  "properties": {
    "data": {
      "type": "object",
      "description": "Application-specific payload (e.g., API request body)."
    },
    "signature": {
      "type": "string",
      "format": "base64",
      "description": "Base64-encoded signature of the canonicalized payload."
    },
    "keyId": {
      "type": "string",
      "description": "Unique identifier for the signing key (e.g., AWS KMS ARN)."
    },
    "algorithm": {
      "type": "string",
      "enum": ["HMAC-SHA256", "RSASSA-PSS-2048"]
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": ["data", "signature"]
}
```

---

## **4. Query Examples**

### **4.1 Generating a Signature (HMAC-SHA256)**
**Input:**
```http
POST /api/resource HTTP/1.1
Host: example.com
Date: Mon, 20 May 2024 12:00:00 GMT
Content-Type: application/json
Content-Length: 20

{"key": "value"}
```
**Steps:**
1. **Canonicalize headers** (sorted by name, lowercase):
   ```
   (request-target): post /api/resource
   content-length: 20
   content-type: application/json
   date: mon, 20 may 2024 12:00:00 gmt
   host: example.com
   ```
2. **Concatenate headers + payload** (using `\n` as separator):
   ```
   (request-target): post /api/resource\n
   content-length: 20\n
   content-type: application/json\n
   date: mon, 20 may 2024 12:00:00 gmt\n
   host: example.com\n
   {"key": "value"}
   ```
3. **Compute HMAC-SHA256** with secret key `your-secret-key`:
   ```bash
   echo -n "CANONICALIZED_STRING" | openssl dgst -sha256 -hmac "your-secret-key" -binary | base64
   ```
4. **Construct `Authorization` header**:
   ```
   Authorization: Signature keyId="secret",algorithm="HMAC-SHA256",headers="(request-target) content-length content-type date host",signature="BASE64_SIGNATURE"
   ```

---

### **4.2 Validating a Signature (RSASSA-PSS-2048)**
**Steps:**
1. **Extract headers** from the `Authorization` header.
2. **Retrieve the public key** (e.g., from a key store like AWS KMS).
3. **Re-canonicalize headers** and concatenate with payload.
4. **Verify signature**:
   ```bash
   openssl dgst -sha256 -verify public_key.pem -signature signature.bin canonicalized_string.bin
   ```

---

## **5. Error Handling**
| **Error Type**          | **HTTP Status** | **Description**                                                                                     | **Example Response**                     |
|-------------------------|-----------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------|
| Invalid Algorithm       | 400 Bad Request | Unsupported or unsupported algorithm.                                                              | `{"error": "Unsupported algorithm: HMAC-SHA1"}` |
| Missing Signature       | 401 Unauthorized| Missing `Authorization` or `X-Signature` header.                                                  | `{"error": "Signature header missing"}`    |
| Expired Signature       | 401 Unauthorized| Timestamp outside valid window (e.g., ±5 minutes).                                                | `{"error": "Signature expired"}`         |
| Signature Mismatch      | 403 Forbidden   | Signature does not match computed hash.                                                           | `{"error": "Invalid signature"}`          |
| Key Not Found           | 500 Internal Error | Public key not available in the key store.                                                       | `{"error": "Key not found"}`              |

---
## **6. Best Practices**
1. **Key Rotation**:
   - Rotate private keys every **90–180 days** (longer for asymmetric keys like Ed25519).
   - Use **AWS KMS** or **HashiCorp Vault** for automated rotation.

2. **Signature Expiration**:
   - Set a **5-minute window** (`x-signing-timestamp`) to mitigate replay attacks.

3. **Canonicalization**:
   - Always **sort headers alphabetically** and **normalize whitespace** in payloads.

4. **Algorithm Selection**:
   - Avoid deprecated algorithms (e.g., **SHA-1, MD5**).
   - Prefer **Ed25519** or **RSASSA-PSS** for long-term security.

5. **Logging**:
   - Log **signature failures** (without exposing the signature itself) for auditing.

6. **Testing**:
   - Use **static analysis tools** (e.g., `jshint` for JS, `Pylint` for Python) to validate signing logic.

---
## **7. Related Patterns**
| **Pattern**               | **Description**                                                                                     |
|---------------------------|-----------------------------------------------------------------------------------------------------|
| **[Token-Based Authentication](#)** | Combine with JWT/OAuth for additional security layers.                                             |
| **[API Gateway Validation](#)** | Implement signing validation in API gateways (e.g., AWS API Gateway, Kong).                        |
| **[HMAC for Secret Sharing](#)** | Use HMAC for mutual authentication in service-to-service communication.                           |
| **[TLS Transport Security](#)** | Always encrypt traffic with **TLS 1.2+** before signing.                                          |
| **[Key Rotation Policies](#)** | Automate key rotation using **AWS KMS** or **HashiCorp Vault**.                                   |

---
## **8. Tools & Libraries**
| **Language/Tool**       | **Library**                                                                                       | **Key Features**                                      |
|-------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| Python                  | `cryptography`                                                                                   | Supports RSA, Ed25519, HMAC.                           |
| Java                    | `Bouncy Castle`                                                                                 | Broad algorithm support (PGP, X.509).                   |
| Node.js                 | `crypto` (built-in), `sign-thing`                                                               | HMAC, RSA, Ed25519.                                   |
| AWS SDKs                | `AWS Signer`                                                                                   | Pre-built signing for AWS APIs.                       |
| Go                      | `golang.org/x/crypto`                                                                        | Ed25519, RSA, HMAC implementations.                 |

---
## **9. Compliance Notes**
- **GDPR**: Ensure signatures do not expose PII in logs.
- **PCI DSS**: Use **FIPS-validated algorithms** (e.g., RSASSA-PSS) for payment data.
- **HIPAA**: Audit signature validation logs for medical data.
- **ISO 27001**: Document key management and access controls.

---
## **10. Troubleshooting**
| **Issue**                          | **Solution**                                                                                     |
|-------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Signature fails validation**      | Check for timestamp drift, incorrect header sorting, or key mismatches.                       |
| **High latency in signing**         | Use **pre-computed signatures** for high-volume APIs or **asymmetric cryptography** (Ed25519). |
| **Key storage vulnerabilities**    | Store keys in **HSMs** (AWS CloudHSM) or **ephemeral secrets** (AWS Secrets Manager).         |
| **Legacy system compatibility**     | Support multiple algorithms (e.g., SHA-256 + RSA) for backward compatibility.                   |

---
This guide ensures a **secure, scalable, and auditable** signing implementation. For further customization, consult your organization’s security policies.