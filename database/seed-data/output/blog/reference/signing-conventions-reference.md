---
**[Pattern] Reference Guide: Signing Conventions**

---

### **Title**
**[Pattern] Signing Conventions: Standardizing Digital Signatures for Verifiable Content**

---

### **Overview**
Signing Conventions provide a structured approach to digitally signing data, ensuring consistency, security, and interoperability across systems. This pattern standardizes the **format, algorithms, and workflows** used for signing documents, messages, or APIs, reducing ambiguity and enforcing verifiable integrity. It is critical in domains like **contracts, blockchains, API authentication, and IoT device validation**, where tamper-evidence and trust are paramount.

Key use cases include:
- **Document Authenticity:** Certifying legal or financial records (e.g., PDFs, emails).
- **API Security:** Securing REST/gRPC endpoints with JWT or X.509 certificates.
- **Blockchain Transactions:** Validating smart contract signatures.
- **IoT Device Trust:** Authenticating firmware updates or sensor data.

---

## **1. Schema Reference**
Below is a standardized **JSON Schema** for defining signing conventions. Adopters should customize fields as needed.

| **Field**               | **Type**       | **Description**                                                                                     | **Requirements**                                                                                     |
|-------------------------|----------------|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `version`               | `string`       | Schema version (e.g., `"1.0"`).                                                                     | Required. Must be semver-compatible.                                                                  |
| `purpose`               | `string`       | Use case (e.g., `"document_authentication"`, `"api_authentication"`).                             | Required. Reference a predefined enum or namespace.                                                  |
| `signingAlgorithm`      | `string`       | Algorithm (e.g., `"ES256"`, `"RS256"`, `"HS512"`).                                                 | Required. Must comply with [RFC 7518](https://tools.ietf.org/html/rfc7518).                            |
| `keyType`               | `string`       | Public key format (e.g., `"JWK"`, `"PEM"`, `"X509"`).                                             | Required. Default: `"JWK"` unless specified otherwise.                                               |
| `digitalOceanKey`       | `object`       | DigitalOcean-compatible key structure (if applicable).                                               | Optional. For cloud-specific integrations.                                                          |
| `validityPeriod`        | `object`       | Key expiry details.                                                                                 | Optional. Includes `notBefore` (ISO 8601) and `expiresAt` (ISO 8601).                                 |
| `signatureField`        | `string`       | Key path in payload (e.g., `"$.signature"`).                                                        | Required if signing arbitrary data.                                                                  |
| `hashAlgorithm`         | `string`       | Hash function (e.g., `"SHA-256"`, `"SHA-384"`).                                                     | Required. Default: `"SHA-256"` unless overridden.                                                     |
| `keyEncoding`           | `string`       | Encoding (e.g., `"base64url"`, `"hex"`).                                                           | Required. Default: `"base64url"`.                                                                     |
| `requiredHeaders`       | `array`        | HTTP headers required for signing (e.g., `"x-api-key"`, `"date"`).                                | Optional. Used for API signing.                                                                    |
| `verificationRules`     | `object`       | Custom rules for validation (e.g., `"keyUsage": ["sign"]`).                                      | Optional. Extensible for domain-specific logic.                                                      |

#### **Example JSON Schema:**
```json
{
  "version": "1.0",
  "purpose": "document_authentication",
  "signingAlgorithm": "ES256",
  "keyType": "JWK",
  "validityPeriod": {
    "notBefore": "2023-01-01T00:00:00Z",
    "expiresAt": "2024-01-01T00:00:00Z"
  },
  "signatureField": "$.signature",
  "hashAlgorithm": "SHA-256"
}
```

---

## **2. Implementation Details**
### **Key Concepts**
1. **Signing Algorithm**
   - Supported: `ES256`, `RS256`, `PS256`, `HS512` (RFC 7518).
   - **Best Practice:** Use asymmetric keys (e.g., `ES256`) for non-repudiation; symmetric (`HS512`) only for shared-secrets.

2. **Key Management**
   - Store private keys securely (e.g., **HSMs**, **AWS KMS**, **Vault**).
   - Rotate keys periodically (e.g., annually) with `validityPeriod`.

3. **Payload Structure**
   - **Signed Data:** Must include a **timestamp** and **payload hash** (e.g., HMAC/SHA).
   - Example (JSON Web Signature - JWS):
     ```json
     {
       "header": { "alg": "ES256", "typ": "JWT" },
       "payload": { "data": "..." },
       "signature": "eyJhbGciOi..."
     }
     ```

4. **Verification Workflow**
   - Decode signature → Validate alg/hash → Recompute hash → Compare.
   - **Libraries:** Use `crypto` (Node.js), `jose` (JWT), or `cryptography` (Python).

---

### **Implementation Steps**
1. **Generate Keys**
   ```bash
   # OpenSSL (RSA)
   openssl genpkey -algorithm RSA -out private.key -pkeyopt rsa_keygen_bits:2048

   # Generate JWK
   openssl pkey -in private.key -outform pem | openssl pkey -outform jwk
   ```

2. **Sign Data**
   ```javascript
   // Node.js (using 'jsonwebtoken')
   const jwt = require('jsonwebtoken');
   const signature = jwt.sign(
     { data: "..." },
     "private_key_pem",
     { algorithm: "ES256" }
   );
   ```

3. **Verify Signature**
   ```python
   # Python (using 'cryptography')
   from cryptography.hazmat.primitives.asymmetric import ec
   from cryptography.hazmat.primitives import hashes, serialization

   public_key = ec.EllipticCurvePublicKey.from_peem(public_key_pem)
   signature.verify(data, public_key, hashes.SHA256())
   ```

---

## **3. Query Examples**
### **A. REST API Signing**
**Request Header:**
```http
Authorization: Signature keyId="dY01",algorithm="ES256",headers="content-type date",signature="..."
Content-Type: application/json
Date: Mon, 01 Jan 2023 00:00:00 GMT
```

**Signature Calculation (HMAC):**
1. Canonicalize headers → Concatenate → Hash → Sign with private key.

### **B. Blockchain Transaction Signing (Ethereum)**
```javascript
// Using 'ethers.js'
const { Wallet } = require('ethers');
const privateKey = '0x...';
const wallet = new Wallet(privateKey);

const signedTx = await wallet.signTransaction({
  to: '0x...',
  value: '1000000000000000000'
});
```

### **C. Document Signing (PDF)**
**Tools:**
- **Libraries:** `pdfrw` (Python), `pdf-lib` (Node.js).
- **Workflow:**
  1. Embed signature field in PDF.
  2. Sign with `pkcs7` or `cms` (e.g., using Adobe’s `SignDoc`).

---

## **4. Error Handling & Validation**
| **Error**               | **Cause**                          | **Solution**                                                                                     |
|-------------------------|------------------------------------|---------------------------------------------------------------------------------------------------|
| `alg_mismatch`          | Wrong signature algorithm.         | Reject request; log for audit.                                                                  |
| `key_expired`           | Key validity period expired.       | Rotate keys; serve old keys temporarily during transition.                                      |
| `invalid_signature`     | Hash mismatch.                    | Redact sensitive data for debugging; do not expose payloads.                                    |
| `missing_header`        | Required headers (e.g., `date`) missing. | Require strict header validation.                                                              |
| `key_revoked`           | Key revoked via CRL/OCSP.          | Integrate with CRL/OCSP checkers (e.g., `pem-crl` in Node.js).                                  |

---

## **5. Related Patterns**
| **Pattern**               | **Relation**                                                                 | **Tools/Libraries**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| **OAuth 2.0**             | Uses signing conventions for tokens (e.g., JWT with RS256).                | `auth0`, `keycloak`                                                                 |
| **Zero-Knowledge Proofs** | Integrates with signing for privacy-preserving verification.               | `snarkjs`, `zk-SNARKs`                                                                |
| **PKI (Public Key Infrastructure)** | Underpins key distribution and validation.                              | `OpenSSL`, `CertifiGate`                                                             |
| **API Gateways**          | Applies signing at the gateway layer (e.g., Kong, Apigee).                 | `Kong-Inc/insomnia`                                                                   |
| **Smart Contracts**       | Signs transactions for blockchain immutability.                           | `web3.js`, `ethers.js`                                                              |

---

## **6. Best Practices**
1. **Algorithm Selection**
   - Prefer **elliptic-curve** (`ES256`) over RSA for efficiency.
   - Avoid deprecated algs (e.g., `SHA-1`).

2. **Key Rotation**
   - Schedule rotations via **certificate chains** (e.g., CRLs).

3. **Logging**
   - Audit signatures with timestamps (non-repudiation).

4. **Compatibility**
   - Test with **OpenSSL**, **JWT.io**, and **Postman** for interop.

5. **Documentation**
   - Publish conventions in **OpenAPI/Swagger** for API teams.

---
**Last Updated:** 2023-10-01
**Feedback:** [GitHub Issues](https://github.com/your-org/signing-conventions/issues)