---
**[Pattern] Reference Guide: Signing Configuration**

---

## **Overview**
The **Signing Configuration** pattern ensures that data or software artifacts are cryptographically signed to verify authenticity, integrity, and non-repudiation. This pattern is critical in security-sensitive workflows (e.g., software deployment, API responses, or sensitive document exchanges) where tamper-proof validation is required.

Signing configurations define:
- **Signing algorithms** (e.g., RSA, ECDSA, HMAC).
- **Key infrastructure** (keys, certificates, or HSM-backed credentials).
- **Usage policies** (scope, expiration, and revocation checks).
- **Output formats** (e.g., JWT, PEM, DER for embedded signatures).

This guide covers schema structure, implementation details, and practical usage examples.

---

## **Schema Reference**
The signing configuration follows a modular schema to accommodate flexibility. Below are core components and their attributes:

| **Component**               | **Attributes**                                                                                     | **Data Type**       | **Required?** | **Description**                                                                                     |
|-----------------------------|-----------------------------------------------------------------------------------------------------|---------------------|---------------|-----------------------------------------------------------------------------------------------------|
| **SigningAlgorithm**        | - `type` (e.g., `"RSA-SHA256"`, `"ECDSA-P256"`)                                                   | `String`           | Yes           | Specifies the cryptographic algorithm and hash function.                                               |
|                             | - `keySize` (e.g., `"2048"`)                                                                    | `String` (numeric) | Conditional*  | Key size (e.g., RSA keys).                                                                         |
|                             | - `curve` (e.g., `"P-256"`)                                                                      | `String`           | Conditional*  | ECDSA curve for elliptic-curve keys.                                                                |
| **KeySource**               | - `type` (e.g., `"file"`, `"hsm"`, `"kms"`, `"certificate"`)                                      | `String`           | Yes           | Source of cryptographic material (e.g., PEM file, hardware security module).                         |
|                             | - `filePath`                                                                                     | `String`           | Conditional*  | Path to PEM/KEY file (if `type="file"`).                                                          |
|                             | - `hsmId`                                                                                         | `String`           | Conditional*  | HSM identifier (if `type="hsm"`).                                                                   |
|                             | - `certificateId`                                                                                 | `String`           | Conditional*  | Identifier for a managed certificate (e.g., AWS ACM).                                             |
|                             | - `keyAlias`                                                                                      | `String`           | Conditional*  | Key alias in KMS (e.g., `"app-signing-key"`).                                                     |
| **OutputFormat**            | - `type` (e.g., `"jwt"`, `"pem"`, `"der"`, `"inline"`)                                            | `String`           | Yes           | Format for signed output (e.g., JWT header/body signature pair).                                   |
|                             | - `headerLabel`                                                                                   | `String`           | Conditional*  | Custom JWT field name (e.g., `"x-custom-sig"`) for inline signatures.                             |
|                             | - `outputEncoding`                                                                               | `String` (e.g., `"base64"`) | Conditional*  | Encoding for binary output (e.g., PEM/DER).                                                        |
| **ValidationPolicy**        | - `trustedCAs` (array of certificate fingerprints/paths)                                          | `Array[String]`    | Optional       | List of trusted root CAs or paths to intermediate CAs for certificate chain validation.          |
|                             | - `revocationCheck`                                                                              | `Boolean`          | Optional       | Enable/disable OCSP/CRL checks for signed certificates.                                          |
|                             | - `maxValidityDuration`                                                                      | `String` (e.g., `"PT24H"`) | Optional       | Max allowed lifetime for signed tokens (ISO 8601 duration).                                     |
| **SigningScope**            | - `targets` (e.g., `"api-responses"`, `"deployment-artifacts"`)                                  | `Array[String]`    | Optional       | Scope of signed operations (e.g., API endpoints, files).                                         |
|                             | - `excludedTargets`                                                                              | `Array[String]`    | Optional       | Targets excluded from signing (e.g., `"logs"`).                                                   |

---
**Conditional\*** Attributes required only when the parent attribute’s `type` specifies the source (e.g., `keySize` is optional unless `SigningAlgorithm.type="RSA"`).

---

## **Implementation Details**
### **1. Key Infrastructure**
- **Private Keys**: Store in **HSMs** (e.g., AWS CloudHSM) or **KMS** (e.g., Azure Key Vault) for secure ephemeral use.
  Example HSM configuration:
  ```json
  "KeySource": {
    "type": "hsm",
    "hsmId": "us-east-1/45678901-1234-5678-90ab-cdef12345678"
  }
  ```
- **Certificates**: Use **certificate authorities (CA)** (e.g., Let’s Encrypt, internal PKI) or provisioned certificates (e.g., AWS Certificate Manager).
  Example certificate reference:
  ```json
  "KeySource": {
    "type": "certificate",
    "certificateId": "arn:aws:acm:us-west-2:123456789012:certificate/abc123"
  }
  ```

### **2. Algorithm Selection**
| **Algorithm**       | **Use Case**                          | **Notes**                                                                 |
|----------------------|---------------------------------------|---------------------------------------------------------------------------|
| `RSA-SHA256`         | General-purpose signing               | Supports 2048/4096-bit keys.                                                |
| `ECDSA-P256`         | High-performance signing              | Faster than RSA but less widely supported in legacy systems.                |
| `HMAC-SHA256`        | Symmetric key signing (e.g., API keys)| Use with a shared secret (e.g., `keySize="32"` for `HMAC-SHA256`).          |

### **3. Output Formats**
- **JWT**: Common for API tokens.
  ```json
  "OutputFormat": {
    "type": "jwt",
    "headerLabel": "sig"
  }
  ```
- **Inline Signature**: Embeds signature alongside data (e.g., JSON).
  ```json
  {
    "data": "sensitive-payload",
    "signature": "base64-encoded-sig"
  }
  ```
- **PEM/DER**: For embedded systems or cryptographic libraries.
  ```json
  "OutputFormat": {
    "type": "pem",
    "outputEncoding": "base64"
  }
  ```

### **4. Validation**
- **Certificate Trust Chain**: Specify trusted CAs or intermediate certificates.
  ```json
  "ValidationPolicy": {
    "trustedCAs": ["sha256:/Yt.../trusted-ca.pem"]
  }
  ```
- **Revocation Lists**: Enable OCSP/CRL checks for dynamic invalidation.
  ```json
  "ValidationPolicy": {
    "revocationCheck": true
  }
  ```

---

## **Query Examples**
### **Example 1: Sign an API Response with HMAC**
```json
{
  "SigningAlgorithm": {
    "type": "HMAC-SHA256",
    "keySize": "32"
  },
  "KeySource": {
    "type": "file",
    "filePath": "/etc/api-signing-key.bin"
  },
  "OutputFormat": {
    "type": "inline",
    "headerLabel": "x-api-sig"
  },
  "SigningScope": {
    "targets": ["/api/v1/orders"]
  }
}
```
**Usage**:
When an API responds to `/api/v1/orders`, append the HMAC signature:
```json
{
  "order": "...",
  "x-api-sig": "sig=base64(sign(data))"
}
```

### **Example 2: Deploy Signed Artifacts with RSA**
```json
{
  "SigningAlgorithm": {
    "type": "RSA-SHA256",
    "keySize": "2048"
  },
  "KeySource": {
    "type": "kms",
    "keyAlias": "prod-deploy-key"
  },
  "OutputFormat": {
    "type": "pem",
    "outputEncoding": "base64"
  },
  "ValidationPolicy": {
    "trustedCAs": ["sha256:/Yt.../deploy-ca.pem"],
    "maxValidityDuration": "PT168H"  // 7 days
  },
  "SigningScope": {
    "targets": ["*.jar", "*.deb"]
  }
}
```
**Output**:
Each `.jar` or `.deb` file is appended with:
```
-----BEGIN SIGNATURE-----
base64(signed-file)
-----END SIGNATURE-----
```

### **Example 3: JWT for Authenticated API Tokens**
```json
{
  "SigningAlgorithm": {
    "type": "ECDSA-P256"
  },
  "KeySource": {
    "type": "certificate",
    "certificateId": "jwt-cert-id"
  },
  "OutputFormat": {
    "type": "jwt"
  }
}
```
**Usage**:
Generate a JWT with:
```json
{
  "header": {
    "alg": "ES256",
    "kid": "jwt-cert-id"
  },
  "payload": { ... },
  "signature": "base64(urlsafe(header.payload))"
}
```

---

## **Related Patterns**
1. **[Cryptographic Key Management](https://example.com/key-management)**
   - For secure provisioning of signing keys (e.g., HSMs, KMS).
2. **[Token Validation](https://example.com/token-validation)**
   - Validates signed tokens (JWT, OAuth) against policies.
3. **[Audit Logging for Signing](https://example.com/audit-logging)**
   - Logs signing events for compliance (e.g., who signed what, when).
4. **[Certificate Rotation](https://example.com/cert-rotation)**
   - Automates key/certificate renewal to maintain security.
5. **[Secure Data Transmission](https://example.com/secure-transmission)**
   - Combines signing with encryption (e.g., TLS + signed payloads).

---
**Note**: For production, validate schemas against your organization’s security policies (e.g., FISMA, ISO 27001). Integrate with CI/CD pipelines for automated signing (e.g., GitHub Actions, Jenkins).