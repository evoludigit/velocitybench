# **[Pattern] Signing Troubleshooting: Reference Guide**

---

## **Overview**
Signing is a critical security and validation mechanism in distributed systems, APIs, and software deployment workflows. When signing fails—due to invalid certificates, mismatched keys, expired credentials, or misconfigured policies—operations stall, leading to downtime, security vulnerabilities, or failed integrations. This guide provides a structured approach to diagnosing and resolving common **signing-related issues** in systems using **JWT (JSON Web Tokens), HMAC, RSA/ECC signatures, or certificate-based authentication (e.g., TLS, OAuth2, SAML)**.

The document covers:
- Root causes of signing failures (e.g., expired keys, missing headers, algorithm mismatches).
- Step-by-step troubleshooting workflows for different signing mechanisms.
- Logging, monitoring, and validation tools to detect issues early.
- Best practices to prevent recurring problems.

---

## **Key Concepts & Implementation Details**

### **1. Signing Components**
| **Component**       | **Description**                                                                 | **Common Issues**                                                                 |
|---------------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| **Private Key**     | Used to sign data (e.g., JWT payload) or generate certificates.               | Corrupted, leaked, or misplaced keys.                                               |
| **Public Key**      | Used to verify signatures (e.g., RSA public key in `jwk` or PEM format).   | Mismatched with the private key; outdated in key rotation.                       |
| **Certificate**     | Bundles public key + metadata (e.g., issuer, validity period).                | Expired, revoked, or invalid chain of trust.                                       |
| **Algorithm**       | Defines cryptographic method (e.g., `RS256`, `HS256`, `ES256`).               | Unsupported algorithm or version skew between signer/verifier.                    |
| **Headers**         | Metadata in tokens (e.g., `alg`, `kid`).                                      | Missing or malformed headers (e.g., missing `alg`).                                |
| **Timestamp**       | `iat` (issued-at) and `exp` (expiration) claims in tokens.                   | Clock skew or incorrect time zones causing `exp` validation to fail.               |
| **Key Rotation**    | Process of replacing cryptographic keys periodically.                          | Overlapping windows; missing validation of new keys.                              |

---

### **2. Signing Workflow Breakdown**
A signing operation typically involves:
1. **Key Generation** → Securely create private/public key pairs (e.g., using OpenSSL, AWS KMS).
2. **Token Creation** → Sign payload with the private key (e.g., `jwt.sign()` in Node.js).
3. **Token Transmission** → Send signed token over a secure channel (e.g., HTTPS).
4. **Verification** → Decode and validate signature using the public key.
5. **Key Rotation** → Replace keys before expiration (e.g., using JWKS endpoints).

**Failure Points**:
- **Before Signing**: Incorrect key pair or algorithm selection.
- **During Signing**: Key corruption, insufficient entropy, or API misconfiguration.
- **During Verification**: Wrong public key, expired token, or clock drift.
- **Rotation**: Silent failures if old keys aren’t revoked or new keys aren’t trusted.

---

## **Schema Reference**
Below are common data structures for signing validation.

### **1. JWT (RFC 7519) Schema**
| **Field**       | **Type**       | **Description**                                                                 | **Validation Rules**                                                                 |
|----------------|---------------|-------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| `header`       | `object`      | Contains `alg` (algorithm), `typ` (token type), `kid` (key ID).             | `alg` must match verifier’s supported algorithms (e.g., `RS256`). `kid` must resolve to a valid key. |
| `payload`      | `object`      | Claims like `iss`, `sub`, `iat`, `exp`, `nbf`.                               | `exp` >= current time (accounting for ±5 min clock skew). `nbf` ≤ current time.   |
| `signature`    | `string`      | Base64Url-encoded HMAC/RSA/ECC signature of `header.payload`.                | Must pass `verify()` with the correct public key.                                  |

**Example JWT Header Payload:**
```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "abc123"
}
```

---

### **2. Key Validation Schema (JWKS)**
| **Field**       | **Type**       | **Description**                                                                 | **Example**                                      |
|----------------|---------------|-------------------------------------------------------------------------------|--------------------------------------------------|
| `kty`          | `string`      | Key type (`RSA`, `EC`, `OKP`).                                                  | `"RSA"`                                          |
| `alg`          | `string`      | Algorithm (e.g., `RS256`, `ES256`).                                            | `"RS256"`                                        |
| `use`          | `string`      | Key purpose (`sig`, `enc`).                                                     | `"sig"`                                          |
| `kid`          | `string`      | Unique key identifier.                                                         | `"abc123"`                                       |
| `n` (RSA)      | `string`      | Public exponent.                                                               | `"AQAB"`                                         |
| `e` (RSA)      | `string`      | Modulus.                                                                       | `"..."` (base64url)                               |
| `x` (EC)       | `string`      | EC public key x-coordinate.                                                     | `"..."`                                          |
| `y` (EC)       | `string`      | EC public key y-coordinate.                                                     | `"..."`                                          |

**Example JWKS Endpoint Response:**
```json
{
  "keys": [
    {
      "kty": "RSA",
      "alg": "RS256",
      "kid": "abc123",
      "n": "AQAB...",
      "e": "AQAB"
    }
  ]
}
```

---

### **3. Error Response Schema (Common)**
| **Error Code** | **HTTP Status** | **Description**                                                                 | **Example Payload**                                      |
|----------------|----------------|-------------------------------------------------------------------------------|----------------------------------------------------------|
| `invalid_signature` | `401`          | Signature verification failed.                                               | `{ "error": "invalid_signature" }`                       |
| `expired_token`      | `401`          | Token expired (`exp` < current time).                                        | `{ "error": "token_expired", "exp": "2023-01-01T00:00:00Z" }` |
| `missing_key`        | `500`          | Public key not found for `kid`.                                               | `{ "error": "key_not_found", "kid": "xyz789" }`          |
| `unsupported_alg`    | `400`          | Algorithm not supported (e.g., `HS256` but only `RS256` allowed).               | `{ "error": "unsupported_algorithm", "alg": "HS256" }`   |
| `clock_skew`         | `401`          | Time difference between server/client > threshold (e.g., ±5 min).               | `{ "error": "clock_skew", "current_time": "2023-01-01T00:01:00Z" }` |

---

## **Query Examples**
### **1. Debugging JWT Signature Validation (Node.js)**
```javascript
const jwt = require('jsonwebtoken');
const jwksClient = require('jwks-rsa');

function verifyToken(token, options) {
  const client = jwksClient({
    jwksUri: process.env.JWKS_URI,
    cache: true,
  });

  return new Promise((resolve, reject) => {
    client.getSigningKey(token.split('.')[1], (err, key) => {
      if (err) reject(new Error('Key not found'));
      const signingKey = key.getPublicKey();
      jwt.verify(token, signingKey, options, (err, decoded) => {
        if (err) reject(err);
        else resolve(decoded);
      });
    });
  });
}
```

**Error Handling**:
- If `jwt.verify()` throws `JsonWebTokenError: jwt malformed`, the token is corrupted.
- If `JsonWebTokenError: invalid signature`, check:
  - Public key correctness (`kid` resolution).
  - Algorithm match (`alg` in header vs. verifier’s supported algs).
  - Clock drift (`iat`/`exp` validation).

---

### **2. Validating RSA Key Pair (OpenSSL)**
```bash
# Generate a key pair
openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -pubout -in private_key.pem -out public_key.pem

# Verify signature
echo "Hello" | openssl dgst -sha256 -sign private_key.pem -out signature.bin
echo "Hello" | openssl dgst -sha256 -verify public_key.pem -signature signature.bin
```

**Expected Outputs**:
- `Signature Ok` → Keys are valid.
- `Verification Failure` → Keys are mismatched or corrupted.

---

### **3. Checking Certificate Validity (cURL)**
```bash
# Fetch cert chain and validate
curl -v --cert-chain --cert client.crt --key client.key https://example.com | openssl x509 -noout -dates
```
**Expected Output**:
```
notBefore=Jan  1 00:00:00 2023 GMT
notAfter=Jan  1 00:00:00 2024 GMT
```
- If `notAfter` is in the past, the certificate is expired.

---

## **Troubleshooting Workflow**
### **Step 1: Identify the Failure Point**
| **Symptom**               | **Likely Cause**                          | **Diagnostic Command/Tool**                          |
|---------------------------|------------------------------------------|-------------------------------------------------------|
| `401 Unauthorized`        | Invalid/signature/expired token.          | Check `Authorization` header; decode JWT.             |
| `500 Server Error`        | Missing/public key or algorithm mismatch.| Inspect JWKS endpoint; validate `kid`.                |
| Silent failures (retries) | Clock skew or key rotation gaps.          | Compare server/client time; audit key rotation logs. |

**Tools**:
- **Decoding Tokens**: [jwt.io](https://jwt.io), `openssl base64 -d -A` (for JWT parts).
- **Key Validation**: `curl <JWKS_URI>`; `openssl pkey -in public_key.pem -text`.
- **Logging**: Enable verbose logging for JWT libraries (e.g., `debug=jwt` in Node.js).

---

### **Step 2: Validate Keys and Certificates**
1. **For JWT/RSA/ECC**:
   - Ensure the private key used to sign matches the public key in the JWKS.
   - Test key rotation by verifying tokens signed with the old key still work during overlap.
2. **For TLS Certificates**:
   - Use [SSL Labs Test](https://www.ssllabs.com/ssltest/) to check chain validity.
   - Verify `notAfter` and `notBefore` dates.

**Example Command to Check Certificate Chain**:
```bash
openssl s_client -connect example.com:443 -showcerts
```

---

### **Step 3: Check for Clock Drift**
- **Symptom**: Tokens with `exp` just before current time failing validation.
- **Solution**:
  - Synchronize servers with NTP (`ntpdate` or `chronyd`).
  - Account for ±5-minute clock skew in verification (e.g., in JWT libraries):
    ```javascript
    jwt.verify(token, key, { clockTolerance: 5 * 60 });
    ```

---

### **Step 4: Audit Key Rotation**
- **Problem**: Tokens signed with old keys are rejected after rotation.
- **Fix**:
  1. Overlap key rotation windows (e.g., use old key for 1 hour post-new-key issuance).
  2. Update verifiers to trust the new `kid`.
  3. Log rejected tokens by `kid` to detect gaps.

**Example Overlap Workflow**:
1. Generate new key pair (`kid=new_abc`).
2. Deploy new key to JWKS and retain old key (`kid=old_abc`) for 1 hour.
3. Remove old key after confirmation.

---

### **Step 5: Validate Headers and Payload**
- **Check for Missing Headers**:
  ```javascript
  const [headerB64, payloadB64] = token.split('.');
  const header = JSON.parse(Buffer.from(headerB64, 'base64url').toString());
  if (!header.alg || !header.kid) throw new Error('Missing header fields');
  ```
- **Payload Validation**:
  - Ensure `iss` (issuer) matches expected value.
  - Check `aud` (audience) if required.

---

## **Query Examples for Common Scenarios**

### **Scenario 1: JWT Signature Verification Fails**
**Commands**:
```bash
# Decode header and payload
echo "$TOKEN" | jq -r '.header'  # Requires jq; base64url decode manually
openssl base64 -d -A <<< "$(echo $TOKEN | cut -d '.' -f 1 | sed 's/\.//g')" | base64 -d
```

**Debugging Steps**:
1. Verify `alg` in header matches the key’s algorithm (e.g., `RS256`).
2. Resolve `kid` to the correct public key from JWKS.
3. Recreate the signature locally:
   ```javascript
   const header = { alg: 'RS256', typ: 'JWT' };
   const payload = { sub: '123', iat: 1234567890 };
   const signingInput = Buffer.from(JSON.stringify(header) + '.' + JSON.stringify(payload));
   const signature = jwt.sign(payload, privateKey, { header });
   ```

---

### **Scenario 2: Certificate Revocation Check**
**Commands**:
```bash
# Check CRL (Certificate Revocation List)
openssl crl -text -in CA.crl
# Or use OCSP for real-time checks
openssl ocsp -issuer CA.cert -cert client.cert -url http://ocsp.example.com
```

**Expected Output**:
- `CRL Number:` → Valid if not revoked.
- `OCSP Response Status:` → `good` if not revoked.

---

### **Scenario 3: HMAC Key Mismatch**
**Commands**:
```bash
# Generate HMAC signature
echo -n "data" | openssl dgst -sha256 -hmac "secret_key" -binary | base64
# Compare with received signature
```

**Debugging**:
- Ensure the secret key is identical between signer and verifier (no trailing newlines).
- For distributed systems, use a key management service (e.g., AWS KMS, HashiCorp Vault).

---

## **Best Practices to Prevent Signing Issues**

### **1. Key Management**
- **Use Hardware Security Modules (HSMs)** for private keys (e.g., AWS CloudHSM, Azure Key Vault).
- **Rotate keys** every 90 days (or per compliance policies).
- **Avoid hardcoding keys**: Use secrets managers or environment variables.

### **2. Token Design**
- **Short-lived tokens**: Set `exp` to 15–30 minutes to minimize exposure.
- **Include `kid`**: Always include a key ID in JWT headers for dynamic key rotation.
- **Use `nbf`**: Set `notBefore` to prevent token reuse before intended use.

### **3. Monitoring and Alerts**
- **Log rejected tokens**: Track `kid`, `alg`, and timestamps for anomalies.
- **Alert on key rotation failures**: Monitor JWKS endpoint errors.
- **Clock drift monitoring**: Set up alerts for servers outside ±5 minutes of NTP.

**Example Prometheus Alert**:
```yaml
- alert: ClockSkewHigh
  expr: abs(server_time_offset_seconds) > 300
  for: 5m
  labels:
    severity: warning
```

### **4. Testing**
- **Unit tests**: Mock JWT verification in tests (e.g., using `jest` + `mock-jwt`).
- **Chaos testing**: Simulate key rotation failures by mocking JWKS responses.
- **Load testing**: Validate scaling under high signing/verification load.

**Example Test (Python)**:
```python
import jwt
from jwt import PyJWTError

def test_jwt_rotation():
    private_key = "-----BEGIN RSA PRIVATE KEY-----\n..."
    public_key = "-----BEGIN PUBLIC KEY-----\n..."

    # Sign with old key
    token = jwt.encode({"sub": "123"}, private_key, algorithm="RS256")
    assert jwt.decode(token, public_key, algorithms=["RS256"])  # Should pass

    # Rotate key (simulate by changing public key)
    new_public_key = "-----BEGIN PUBLIC KEY-----\n..."  # New kid
    try:
        jwt.decode(token, new_public_key, algorithms=["RS256"])
    except PyJWTError:
        pass  # Expected if old key not trusted
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|-------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[Key Rotation](https://example.com/key-rotation)** | Strategies for securely rotating cryptographic keys.                          | When keys expire or are compromised.                                             |
| **[JWT Best Practices](https://example.com/jwt-best-practices)** | Guidelines for secure JWT usage (e.g., short-lived tokens, claims validation). | Designing stateless APIs with JWT.                                              |
| **[Certificate Transparency](https://example.com/cert-transparency)** | Monitoring certificate issuance to detect misissued certificates.           | Mitigating MITM attacks via invalid TLS certificates.                             |
| **[HMAC for API Security](https://example.com/hmac-api-security)** | Using HMAC for request signing in APIs.                                      | When JWT is not feasible (e.g., large payloads, legacy systems).                 |
| **[OAuth2 Token Validation](https://example.com/oauth2-validation)** |