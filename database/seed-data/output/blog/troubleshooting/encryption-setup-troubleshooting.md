# **Debugging Encryption Setup: A Troubleshooting Guide**

## **Introduction**
Encryption is a critical component of secure systems, ensuring data confidentiality, integrity, and availability. Misconfigurations, key management errors, or implementation flaws can lead to security vulnerabilities, data breaches, or system failures. This guide provides a structured approach to diagnosing and resolving common encryption-related issues.

---

## **1. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

✅ **Encryption Failures**
- API/server responses with `403 Forbidden`, `401 Unauthorized`, or `500 Internal Error` when handling encrypted payloads.
- Decryption errors (`"Failed to decrypt payload"`, `"Invalid signature"`).
- Unexpected behavior when validating tokens (JWT, OAuth, etc.).

✅ **Performance Degradation**
- Slow response times due to excessive CPU usage in encryption/decryption.
- Long-running key exchange processes (e.g., TLS handshake failures).

✅ **Security Alerts & Logs**
- Warnings in security logs about weak encryption algorithms (`SHA-1`, `RC4`, `DES`).
- Suspicious access patterns (e.g., repeated failed decryption attempts).
- Logs indicating missing or compromised keys.

✅ **Compatibility Issues**
- Incompatible cipher suites (e.g., legacy clients failing to connect with modern TLS).
- Mismatched key formats (e.g., PEM vs. DER).

✅ **Key Management Problems**
- Failed key rotation causing service interruptions.
- Orphaned keys leading to revocation errors.
- Incorrect key storage (e.g., keys exposed in logs or source code).

✅ **Dependency & Framework Errors**
- Library versions with known vulnerabilities (e.g., OpenSSL `CVE-2022-3602`).
- Missing or misconfigured encryption dependencies (e.g., `bcrypt` not installed).

---

## **2. Common Issues & Fixes**

### **Issue 1: Failed Decryption (Incorrect Key or Algorithm)**
**Symptoms:**
- `Decryption failed: "AAD mismatch"` (AES-GCM)
- `Decryption failed: "Invalid padding"` (AES-CBC)
- `Decryption failed: "Unrecognized cipher"`

**Root Causes:**
- Wrong encryption key used for decryption.
- Mismatched IV (Initialization Vector) or algorithm.
- Corrupted ciphertext.

**Fixes:**

#### **Example: AES-GCM (Node.js)**
```javascript
const crypto = require('crypto');

// Correct decryption (if key, iv, and ciphertext match)
function decrypt(data, key, iv) {
  const decipher = crypto.createDecipheriv('aes-256-gcm', Buffer.from(key), Buffer.from(iv, 'hex'));
  decipher.setAuthTag(Buffer.from(data.tag, 'hex')); // Must match encryption
  let decrypted = decipher.update(data.ciphertext, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  return decrypted;
}

// If decryption fails, verify:
console.log(`Key length: ${key.length} (should be 32 for AES-256)`);
console.log(`IV length: ${iv.length} (should be 12 for AES-GCM)`);
```

**Debugging Steps:**
1. **Log Key & IV:** Ensure they match encryption.
2. **Check Ciphertext Integrity:** Verify no corruption.
3. **Test with Hardcoded Values:**
   ```javascript
   const testKey = '0123456789abcdef0123456789abcdef'; // 32-byte key
   const testIv = '0123456789abcdef'; // 12-byte IV for GCM
   ```

---

#### **Example: RSA (Python)**
```python
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

# If decryption fails:
try:
    cipher = PKCS1_OAEP.new(rsa_key)
    decrypted = cipher.decrypt(ciphertext)
except ValueError as e:
    print(f"RSA decryption error: {e}")  # Check for wrong key or padding
```

**Debugging Steps:**
1. **Verify Key Format:** Ensure public/private keys are in PEM/DER format.
2. **Check Padding Scheme:** `PKCS1_OAEP` vs. `PKCS1_v1_5`.

---

### **Issue 2: TLS Handshake Failures**
**Symptoms:**
- `SSL_ERROR_SSL` (TLS 1.3 downgrade attack).
- `unable to verify certificate` (misconfigured CA).
- `No common cipher suite` (protocol mismatch).

**Root Causes:**
- Outdated TLS versions (`SSLv3`, `TLS 1.0`).
- Missing intermediate certificates.
- Weak cipher suites (e.g., `TLS_RSA_WITH_AES_128_CBC_SHA`).

**Fixes:**

#### **Example: Configuring TLS in Node.js (Express)**
```javascript
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('server.key'),
  cert: fs.readFileSync('server.cert'),
  minVersion: 'TLSv1.2', // Force TLS 1.2+
  ciphers: 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384',
};

const server = https.createServer(options, app);
server.listen(443);
```

**Debugging Steps:**
1. **Check TLS Version Support:**
   ```bash
   openssl s_client -connect example.com:443 -tls1_3
   ```
2. **Test Cipher Suites:**
   ```bash
   openssl s_client -connect example.com:443 -cipher 'ECDHE-ECDSA-AES256-GCM-SHA384'
   ```
3. **Verify Cert Chain:**
   ```bash
   openssl verify -CAfile rootCA.pem server.crt
   ```

---

### **Issue 3: Key Rotation & Revocation Failures**
**Symptoms:**
- `Revoked key used` errors.
- Services failing after key rotation.
- Orphaned keys in HSMs (Hardware Security Modules).

**Root Causes:**
- Incomplete key revocation (e.g., cached keys still in use).
- Missing key rotation logic in application code.

**Fixes:**

#### **Example: Key Rotation in JWT (Node.js)**
```javascript
const jwt = require('jsonwebtoken');

// Store old and new signing keys
const oldKey = 'old_secret_key';
const newKey = 'new_secret_key';
const keyList = [oldKey, newKey]; // Add old key until rotation completes

function verifyToken(token) {
  for (const key of keyList) {
    try {
      return jwt.verify(token, key, { algorithms: ['HS256'] });
    } catch (err) {
      if (err.name !== 'JsonWebTokenError') throw err;
    }
  }
  throw new Error('Invalid token');
}
```

**Debugging Steps:**
1. **Audit Key Usage:**
   ```sql
   -- Check if old keys are still referenced in DB
   SELECT * FROM auth_keys WHERE version < 'latest';
   ```
2. **Test Token Validation:**
   ```bash
   echo '{"alg":"HS256","kid":"old_key_id"}' | jq -r '.kid'
   ```
3. **Monitor HSM Cache:**
   ```bash
   aws kms list-aliases --query 'Aliases[?contains(KeyId, `old-key`)].KeyId'
   ```

---

### **Issue 4: Weak Randomness (Predictable Encryption Keys)**
**Symptoms:**
- Repeated errors like `"PRNG not seeded"`.
- Predictable encryption keys (e.g., hardcoded `secret=123`).

**Root Causes:**
- Missing randomness seeding (`crypto.randomBytes` not used).
- Hardcoded keys in configuration.

**Fixes:**

#### **Example: Secure Key Generation (Python)**
```python
import os
from Crypto.Random import get_random_bytes

# Secure key generation (never hardcode!)
def generate_key():
    return get_random_bytes(32).hex()  # AES-256

key = generate_key()
print(f"Generated key: {key[:16]}...")  # Should be unpredictable
```

**Debugging Steps:**
1. **Check for Hardcoded Keys:**
   ```bash
   grep -r 'secret=' --include="*.conf" .
   ```
2. **Test PRNG Quality:**
   ```python
   import random
   print(random.getrandbits(32))  # Should vary
   ```

---

### **Issue 5: JWT (JSON Web Token) Validation Failures**
**Symptoms:**
- `jwt_expired` or `invalid_signature` errors.
- Wrong audience (`aud`) or issuer (`iss`) claims.

**Root Causes:**
- Expired tokens not handled.
- Wrong algorithm (`HS256` vs. `RS256`).
- Mismatched `kid` (key ID) in JWT header.

**Fixes:**

#### **Example: Validating JWT in Java (Spring Boot)**
```java
import io.jsonwebtoken.*;
import io.jsonwebtoken.security.SignatureException;

public class JwtValidator {
    public static boolean validateToken(String token, String secret) {
        try {
            Jwts.parserBuilder()
                .setSigningKey(secret)
                .requireIssuer("secure-issuer")
                .requireAudience("secure-audience")
                .require("exp", claims -> claims.get("exp", Long.class) > System.currentTimeMillis() / 1000)
                .build()
                .parseClaimsJws(token);
            return true;
        } catch (SignatureException e) {
            System.err.println("Invalid signature: " + e.getMessage());
        } catch (ExpiredJwtException e) {
            System.err.println("Token expired: " + e.getExpiredAt());
        }
        return false;
    }
}
```

**Debugging Steps:**
1. **Verify Token Claims:**
   ```bash
   jwt_decode --header 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
   ```
2. **Check Key ID (`kid`):**
   ```bash
   jwt_decode --kid 'old-key-id' 'token...'
   ```

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**       | **Purpose**                                                                 | **Example Command/Usage**                          |
|--------------------------|-----------------------------------------------------------------------------|---------------------------------------------------|
| **`openssl`**            | TLS debugging, key inspection, cipher suite testing.                       | `openssl s_client -connect example.com:443`       |
| **`strace`**             | Trace system calls for key-related operations.                               | `strace -e trace=process ./decrypt`               |
| **`tcpdump`**            | Capture TLS handshake for analysis.                                          | `tcpdump -i any port 443 -w capture.pcap`         |
| **JWT Tools**            | Decode, validate, and inspect JWT tokens.                                   | `jwt_decode --header 'token'`                     |
| **Hashicorp Vault**      | Dynamic secrets management & key rotation.                                  | `vault read secret/data/encryption_key`           |
| **AWS KMS CLI**          | Check AWS KMS key policies and rotations.                                   | `aws kms describe-key --key-id alias/my-key`      |
| **Logging & Tracing**    | Correlate logs with encryption events (e.g., ELK Stack).                     | `logger.info("Decrypted data: " + data.toString())`|
| **Static Analysis**      | Detect hardcoded keys in code.                                              | `grep -r 'base64_decode("secret"' --include="*.py"`|

---

## **4. Prevention Strategies**

### **A. Secure Key Management**
- **Use Hardware Security Modules (HSMs)** for high-security environments (AWS KMS, Hashicorp Vault).
- **Rotate keys periodically** (e.g., every 90 days for RSA keys).
- **Avoid hardcoding keys** in source code (use environment variables or secret managers).
- **Implement key revocation lists (CRLs)** for public keys.

### **B. Algorithm & Protocol Hardening**
- **Use modern algorithms:**
  - **Symmetric:** AES-256-GCM (GCM mode is authenticated).
  - **Asymmetric:** RSA-4096 or ECDSA (P-256, P-384).
- **Disable weak TLS versions** (`SSLv3`, `TLS 1.0`, `TLS 1.1`).
- **Enforce strong cipher suites** (e.g., `TLS_AES_256_GCM_SHA384`).

### **C. Code & Configuration Best Practices**
- **Validate inputs** before decryption (e.g., check JWT `alg` claim).
- **Use constant-time comparison** for passwords/keys (mitigate timing attacks).
- **Log keys securely** (never log raw keys; use masks or metadata only).
- **Test key rotation** in staging before production.

### **D. Monitoring & Alerting**
- **Set up alerts** for:
  - Failed decryption attempts.
  - Key rotation failures.
  - TLS handshake errors.
- **Audit logs** for key access (e.g., AWS CloudTrail for KMS).
- **Regular penetration testing** to check for weak encryption.

### **E. Dependency Management**
- **Keep crypto libraries updated** (e.g., OpenSSL, Bouncy Castle).
- **Scan for CVEs** (e.g., `npm audit`, `snyk test`).
- **Use well-audited libraries** (e.g., `crypto` in Node.js, `PyCryptodome` in Python).

---

## **5. Conclusion**
Encryption misconfigurations can lead to severe security breaches. By following this guide, you can:
✔ **Diagnose decryption failures** (wrong keys, algorithms, IVs).
✔ **Debug TLS issues** (cipher suites, certs, versions).
✔ **Handle key rotation smoothly** (avoid downtime).
✔ **Prevent weak randomness & hardcoded keys**.
✔ **Validate JWTs securely** (aud, iss, alg, exp).

**Final Checklist Before Production:**
1. [ ] Test encryption/decryption with edge cases.
2. [ ] Verify TLS hardening (`openssl s_client`).
3. [ ] Audit key storage (no hardcoded secrets).
4. [ ] Set up monitoring for encryption events.
5. [ ] Document key rotation procedure.

By combining systematic debugging with proactive security practices, you can ensure robust encryption in your systems.