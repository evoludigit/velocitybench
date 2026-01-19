# **Debugging Signing Issues: A Troubleshooting Guide**
*(Cryptographic Signing, JWT, Digital Signatures, Code Signing, TLS/SSL, HMAC, etc.)*

Signing mechanisms are critical for security, authenticity, and integrity verification in systems. When signing fails—whether in cryptographic operations, JWT validation, code signing, or TLS handshakes—applications may reject requests, fail deployments, or expose vulnerabilities. This guide provides a structured approach to debugging signing-related issues quickly.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm these common symptoms:

| **Symptom**                          | **Description**                                                                 |
|--------------------------------------|-------------------------------------------------------------------------------|
| **HTTP/JWT Signing Errors**          | `SignatureInvalid`, `InvalidToken`, `NoSuchAlgorithmException` in auth flows. |
| **Code Signing Failures**            | "Signature verification failed," untrusted executable warnings.              |
| **TLS/SSL Handshake Failures**       | `SSLHandshakeException`, `PKIX path building failed`.                         |
| **HMAC/SHA Verification Failures**   | `SignatureMismatch`, cryptographic comparisons failing in APIs/gateways.      |
| **Database/App Logs**                | Timestamps of failed signing attempts, missing private keys, or certificate expiry alerts. |

**Quick Checks:**
- Are timestamps involved (e.g., JWT expiration, HMAC time-based)? *(Clock skew issues are common.)*
- Does the error occur in **creation** or **verification** steps?
- Is the error **intermittent** or consistent?
- Are logs showing `NoSuchAlgorithm` or `InvalidKeySpecException`?
- Is the environment (dev/staging/prod) affected differently?

---

## **2. Common Issues and Fixes**
*(Focused on code and configuration fixes.)*

### **A. JWT (JSON Web Token) Signing Errors**
#### **Issue:** `jose` or `jwks` library fails to verify/issue tokens.
**Symptoms:**
```java
// Example error (Java)
jose4j.jwk.JsonWebKeyException: Signature verification failed
```
```javascript
// Example error (Node.js)
Error: invalid signature
    at finalize ()
```

**Debugging Steps:**
1. **Check Key Pair Mismatch**
   - Ensure the **private key** used for signing matches the **public key** in the JWKS endpoint.
   - Verify key type (e.g., `RS256` vs `HS256`). RS256 requires asymmetric keys; HS256 uses symmetric keys.
   - **Fix:**
     ```java
     // Java (jose4j)
     String privateKeyPem = "-----BEGIN PRIVATE KEY-----...\n-----END PRIVATE KEY-----";
     JsonWebKey jwk = JsonWebKey.Factory.newJwk(privateKeyPem);
     JwsHeader header = new JwsHeader(JwsAlgorithm.RS256);
     JwsSignature jwsSig = new JwsSignature(header, secret);
     ```
     ```javascript
     // Node.js (jsonwebtoken)
     const jwk = {
       kty: 'RSA',
       use: 'sig',
       kid: 'unique-id',
       n: '...modulus...',
       e: 'AQAB',
       d: '...private-exponent...'
     };
     const token = jwt.sign(payload, jwk, { algorithm: 'RS256' });
     ```

2. **Clock Skew Issues**
   - JWTs expire with `iat` (issued-at) and `exp` (expiration) timestamps. If the server/client clocks differ by >5 minutes, validation fails.
   - **Fix:**
     ```java
     // Enable JWT lease time tolerance (Java)
     JwtConsumerBuilder builder = new JwtConsumerBuilder()
         .setLeewayToExpiration(180) // 3 minutes buffer
         .setClock(new SystemClock() {
             @Override
             public Date getCurrentTime() { return new Date(System.currentTimeMillis() + 120000); }
         });
     ```

3. **Missing Header Parameters**
   - Ensure `kid` (key identifier) matches the JWKS endpoint.
   - **Fix:**
     ```javascript
     // Node.js
     const token = jwt.sign(payload, 'secret', {
       algorithm: 'HS256',
       header: { kid: 'unique-key-id' }
     });
     ```

4. **Base64 Padding Issues**
   - JWTs use **URL-safe Base64** (no padding `=`). Ensure padding is removed.
   - **Fix:**
     ```python
     import base64
     base64.urlsafe_b64encode(b'data').decode('utf-8')  # Add to signing logic
     ```

---

### **B. Digital Certificate & Code Signing Failures**
#### **Issue:** `Signature verification failed` during package deployment or runtime.
**Symptoms:**
- Maven/Gradle: `[ERROR] Error signing artifact`
- Windows: "The signature of this file is invalid."
- Linux: `gpg: signing failed: No secret key`

**Debugging Steps:**
1. **Missing or Expired Certificate**
   - Check certificate expiry with:
     ```bash
     openssl x509 -enddate -noout -in cert.pem
     ```
   - **Fix:** Regenerate CSR/certificate.

2. **Key Usage Mismatch**
   - A key signed for **tls_client** won’t work for **code_signing**.
   - **Fix:** Request a **code signing** certificate (e.g., from DigiCert, Sectigo).

3. **GPG Key Issues**
   - Ensure the private key is imported:
     ```bash
     gpg --list-secret-keys
     ```
   - **Fix:**
     ```bash
     # Export public key for others to verify
     gpg --export --armor <email> > public.key
     # Sign a file
     gpg --detach-sign --armor -u <key-id> file.txt
     ```

4. **Timestamps in Code Signing (TSA)**
   - If using **Time Stamped Archives (TSA)**, ensure the TSA server is reachable.
   - **Fix:** Test TSA connection:
     ```bash
     openssl ts -query -data <file> -cert -untrusted <tsa-cert> -cafile <tsa-root>
     ```

---

### **C. TLS/SSL Handshake Failures**
#### **Issue:** `PKIX path building failed` or `SSLPeerUnverifiedException`.
**Symptoms:**
```java
// Java
javax.net.ssl.SSLHandshakeException: PKIX path building failed
```
```python
# Python
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: _ssl.c:727
```

**Debugging Steps:**
1. **Missing Intermediate Certificates**
   - The client/server may not trust the **root CA** or **intermediate CA**.
   - **Fix:** Bundle all certificates (root + intermediate) in a `ca-bundle.pem`.
     ```bash
     cat rootCA.crt intermediateCA.crt >> ca-bundle.pem
     ```

2. **Hostname Mismatch**
   - The certificate’s `CN` (Common Name) or `SAN` (Subject Alternative Name) must match the hostname.
   - **Fix:** Use a wildcard (`*.example.com`) or SAN entry.

3. **Clock Skew in Certificate Validation**
   - Like JWTs, certificates have `notBefore`/`notAfter` fields.
   - **Fix:** Configure strict clock validation.
     ```java
     // Java (disable clock skew for tests)
     SSLContext sslContext = SSLContext.getInstance("TLS");
     sslContext.init(keyManagers, trustManagers, new SecureRandom() {
         @Override
         public void nextBytes(byte[] bytes) {
             System.arraycopy(new byte[]{0}, 0, bytes, 0, bytes.length);
         }
     });
     ```

4. **Untrusted CA in Truststore**
   - If the root CA is self-signed, import it into the truststore.
   - **Fix:**
     ```bash
     keytool -import -alias myCA -file rootCA.crt -keystore truststore.jks
     ```

---

### **D. HMAC/SHA Verification Failures**
#### **Issue:** `HMAC does not match` during API validation.
**Symptoms:**
```python
# Python (PyHMAC)
hmac.compare_digest(hmac_new(secret, msg).digest(), received_hmac)  # Returns False
```

**Debugging Steps:**
1. **Key/Secret Mismatch**
   - Ensure the **secret key** used for signing matches verification.
   - **Fix:**
     ```python
     import hmac
     secret = b'my-secret-key'
     msg = b'test-message'
     hmac_new = hmac.new(secret, msg, 'sha256').hexdigest()
     ```

2. **Message Ordering Issues**
   - HMAC is order-sensitive. If inputs differ (e.g., whitespace, trailing `=` in Base64), verification fails.
   - **Fix:** Normalize inputs:
     ```java
     // Java
     String normalizedMsg = msg.replaceAll("\\s+", "").replace("=", "");
     ```

3. **Hash Algorithm Mismatch**
   - If signing uses `SHA-256` but verification uses `SHA-1`, it fails.
   - **Fix:** Standardize on one algorithm.

4. **Clock Drift in Time-Based HMAC (e.g., AWS Signature v4)**
   - AWS Signature v4 includes a timestamp (`x-amz-date`).
   - **Fix:** Ensure server clocks sync with AWS.
     ```bash
     ntpdate -u time.amazonaws.com
     ```

---

## **3. Debugging Tools and Techniques**
### **A. Logging & Validation**
- **JWT:**
  - Use `jwt_tool` (CLI) to decode and verify:
    ```bash
    jwt_tool verify --secret 'my-secret' --token 'eyJhbGciOiJIUzI1NiIs...'
    ```
- **Certificates:**
  - Validate with `openssl`:
    ```bash
    openssl x509 -text -in cert.pem
    openssl verify -CAfile ca-bundle.pem cert.pem
    ```
- **TLS:**
  - Use `ssllabs` ([https://www.ssllabs.com/ssltest/](https://www.ssllabs.com/ssltest/)) to check handshake issues.

### **B. Code-Level Debugging**
1. **Enable Verbose Logging**
   - Java:
     ```java
     System.setProperty("javax.net.debug", "ssl:handshake");
     ```
   - Python:
     ```python
     import logging
     logging.basicConfig(level=logging.DEBUG)
     requests.get('https://example.com', verify=False)  # Temporarily disable for testing
     ```
2. **Unit Tests for Signing**
   - Mock signatures to verify logic:
     ```python
     # Example: Test HMAC without real signing
     assert hmac.compare_digest(
         hmac.new(b'secret', b'msg', 'sha256').digest(),
         b'expected-hmac-here'
     )
     ```

### **C. Network Inspection**
- **Wireshark/tcpdump** for TLS handshakes:
  ```bash
  tcpdump -i any -s 0 -w tls.pcap port 443
  ```
- **Burp Suite** for intercepting JWT/TLS requests.

---

## **4. Prevention Strategies**
### **A. Key Management Best Practices**
1. **Use Hardware Security Modules (HSMs)** for private keys.
2. **Rotate Keys Periodically** (e.g., yearly for TLS certificates).
3. **Never Hardcode Secrets** in source code:
   ```java
   // ❌ Bad
   private static final String SECRET = "my-Secret123";

   // ✅ Good (use environment variables)
   private static final String SECRET = System.getenv("API_SECRET");
   ```

### **B. Automated Validation**
1. **Pre-deploy Checks**
   - Run `crt.sh` to validate certificates before deployment:
     ```bash
     curl -X POST https://crt.sh/ --cert your-cert.pem --key your-key.pem
     ```
2. **CI/CD Pipeline Validation**
   - Test signing in every commit (e.g., GitHub Actions for code signing).

### **C. Security Headers**
- For JWTs, enforce:
  ```nginx
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
  add_header X-Content-Type-Options "nosniff" always;
  ```

### **D. Monitor Expiry Alerts**
- Set up alerts for:
  - TLS certificate expiry.
  - JWT token expiry trends.
  - GPG key rotation schedules.

---

## **5. Quick Reference Table**
| **Issue Type**       | **Error Example**                          | **Likely Cause**                          | **Immediate Fix**                          |
|----------------------|--------------------------------------------|------------------------------------------|--------------------------------------------|
| JWT Verification     | `SignatureInvalid`                         | Wrong key, clock skew                     | Check `kid`, adjust `iat/exp` tolerance.    |
| Code Signing         | `Signature verification failed`            | Expired cert, wrong key usage            | Regenerate cert, ensure correct key type.  |
| TLS Handshake        | `PKIX path building failed`                | Missing intermediate CA                  | Bundle all certs in `ca-bundle.pem`.       |
| HMAC Mismatch        | `HMAC mismatch`                            | Secret key mismatch, message ordering    | Normalize inputs, verify secret key.        |
| Self-Signed Cert     | `Untrusted CA`                             | Missing root CA in truststore            | Import root CA into keystore.              |

---
## **6. Final Checklist Before Production**
✅ **For JWT:**
- [ ] `kid` matches JWKS endpoint.
- [ ] Clock skew ≤ 5 minutes.
- [ ] No padding in Base64 tokens.

✅ **For Certificates:**
- [ ] No expiry within 30 days.
- [ ] Correct key usage (e.g., `code signing` vs `tls_client`).
- [ ] Intermediate certificates included.

✅ **For TLS:**
- [ ] Hostname matches `CN` or `SAN`.
- [ ] Truststore includes all CAs.
- [ ] `SSLContext` configured for strict validation.

✅ **For HMAC:**
- [ ] Secret key consistent across signing/verification.
- [ ] Hash algorithm matches (`SHA-256` everywhere).

---
**Next Steps:**
- If issues persist, **isolate the environment** (e.g., test with a fresh key pair).
- **Escalate to security teams** if root CA or private key compromise is suspected.

By following this guide, you can quickly identify and resolve signing-related issues while preventing future occurrences.