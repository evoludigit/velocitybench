# **Debugging Signing Anti-Patterns: A Troubleshooting Guide**
*For Backend Engineers*

## **1. Introduction**
Signing mechanisms (e.g., JWT, HMAC, RSA, ECDSA) are critical for authentication, authorization, and data integrity. However, poorly implemented signing can lead to security vulnerabilities, performance bottlenecks, or system failures. This guide covers common **Signing Anti-Patterns**, their symptoms, debugging techniques, and preventive measures.

---

## **2. Symptom Checklist**
Before diving into debugging, verify these common symptoms of signing-related issues:

| **Symptom**                          | **Possible Cause**                          | **Impact**                          |
|--------------------------------------|--------------------------------------------|-------------------------------------|
| JWT token verification fails silently | Incorrect key, algorithm mismatch, or expired claims | Authentication failures |
| High CPU/memory usage in signing/verification | Poorly optimized crypto libraries (e.g., RSA with large keys) | System slowdowns, crashes |
| Tokens signed with wrong keys        | Hardcoded keys, misconfigured secret rotation | Security breaches (impersonation) |
| Slow token generation/validation     | Suboptimal signing algorithms (e.g., RSA over ECDSA) | Poor user experience |
| Tokens signed with incorrect headers | Manual signing bypassing libraries | Invalid token structure |
| Key leakage in logs/debug output     | Debug logs exposing secrets (e.g., `console.log(secretKey)`) | Security incidents |
| Race conditions in key rotation      | Stale keys still in use during rotation | Temporary security gaps |
| Invalid tokens despite correct keys  | Clock skew (e.g., `nbf`, `exp` claims) | False positives in validation |

**Quick Check:**
- Are tokens being signed/verified with the correct algorithm and key?
- Are secret keys rotated securely?
- Are signing operations hitting performance bottlenecks?
- Are sensitive keys logged or exposed?

---

## **3. Common Issues & Fixes**

### **3.1. Incorrect Key Usage**
**Problem:**
Tokens signed with the wrong key (e.g., dev key in production) or using an expired key.

**Symptoms:**
- `InvalidSignatureError` in JWT libraries
- Tokens work in dev but fail in prod

**Debugging Steps:**
1. **Inspect the signing key:**
   ```javascript
   // Example: Check if the key matches expected format
   const key = process.env.JWT_SECRET;
   if (!key || typeof key !== 'string' || key.length < 32) {
     throw new Error("Invalid or missing signing key!");
   }
   ```
2. **Verify key rotation:**
   - Ensure old keys are revoked (e.g., via `jti` or token blacklisting).
   - Use a key rotation strategy (e.g., asymmetric keys + symmetric fallback).

**Fix:**
- **Use environment variables:**
  ```env
  JWT_SECRET=your_secure_random_string_32_characters
  ```
- **Avoid hardcoding keys:**
  ```javascript
  // ❌ Bad: Hardcoded key
  const key = "secret123";

  // ✅ Good: Load from env
  const key = process.env.JWT_SECRET;
  ```

---

### **3.2. Algorithm Mismatch**
**Problem:**
Signing with `HS256` but verifying with `RS256`, or using deprecated algorithms like `SHA1`.

**Symptoms:**
- `Algorithm mismatch` errors
- Tokens valid in one environment but invalid in another

**Debugging Steps:**
1. **Check the `alg` header in the token:**
   ```json
   {
     "alg": "HS256",
     "typ": "JWT"
   }
   ```
2. **Verify library settings:**
   ```javascript
   // Example: Force algorithm in jsonwebtoken
   jwt.verify(token, key, { algorithms: ['HS256'] });
   ```

**Fix:**
- **Standardize on secure algorithms:**
  ```javascript
  // ✅ Use HS256 or RS256 (never SHA1!)
  jwt.sign(payload, key, { algorithm: 'HS256' });
  ```
- **Reject weak algorithms:**
  ```javascript
  jwt.verify(token, key, { algorithms: ['HS256', 'RS256'] });
  ```

---

### **3.3. Performance Bottlenecks**
**Problem:**
Slow signing/verification due to:
- Large RSA keys (e.g., 4096-bit)
- Inefficient key caching
- Blocking operations in Node.js

**Symptoms:**
- High CPU usage in `/auth` endpoints
- Timeouts during JWT processing

**Debugging Steps:**
1. **Profile crypto operations:**
   ```javascript
   const crypto = require('crypto');
   const start = Date.now();
   crypto.createVerify('rsa-sha256').update(payload).sign(key);
   console.log(`Signing took ${Date.now() - start}ms`);
   ```
2. **Compare algorithms:**
   - **ECDSA (P-256)** is ~10x faster than RSA (2048-bit).
   - **HS256** is fastest but requires key rotation.

**Fix:**
- **Use ECDSA for better performance:**
  ```javascript
  // ✅ Faster than RSA (if key management is secure)
  const key = crypto.generateKeyPairSync('ecdsa', { namedCurve: 'p-256' });
  ```
- **Cache keys in memory (if secure):**
  ```javascript
  const cachedKey = crypto.createPrivateKeySync({ key: fs.readFileSync('key.pem') });
  ```

---

### **3.4. Clock Skew Issues**
**Problem:**
Tokens rejected due to `nbf` (Not Before) or `exp` (Expiration) timestamps not matching the server’s time.

**Symptoms:**
- `TokenExpiredError` despite recent issuance
- `NotYetValidError` even after waiting

**Debugging Steps:**
1. **Check server time sync:**
   ```bash
   date
   ```
2. **Verify token claims:**
   ```javascript
   const token = jwt.decode(token); // Use a library like `jwt-decode`
   console.log(token.nbf, token.exp);
   ```

**Fix:**
- **Allow small clock drift (e.g., ±5 mins):**
  ```javascript
  jwt.verify(token, key, { clockTolerance: 60 });
  ```
- **Ensure servers use NTP (Network Time Protocol).**

---

### **3.5. Key Leakage in Logs**
**Problem:**
Sensitive keys logged or exposed in error messages.

**Symptoms:**
- Keys appear in `console.log`, `server.log`, or error traces.

**Debugging Steps:**
1. **Search logs for secrets:**
   ```bash
   grep -r "JWT_SECRET\|private_key" /var/log/
   ```
2. **Check stack traces:**
   ```javascript
   try { jwt.sign(...) } catch (err) {
     console.error(err); // ❌ Avoid logging secrets in errors
   }
   ```

**Fix:**
- **Never log keys directly:**
  ```javascript
  // ❌ Bad: Logs the key
  console.error(`Failed to sign: ${err.message}`, key);

  // ✅ Good: Redact secrets
  console.error(`Failed to sign: ${err.message}`);
  ```
- **Use structured logging (e.g., Winston with transport):**
  ```javascript
  logger.error({ error: err.message, meta: { userId: 123 } });
  ```

---

### **3.6. Race Conditions in Key Rotation**
**Problem:**
New keys deployed before old ones are revoked, or tokens signed with stale keys.

**Symptoms:**
- Some tokens work, others fail intermittently.
- Authentication fails during rotation.

**Debugging Steps:**
1. **Check token signing time:**
   ```javascript
   const decoded = jwt.decode(token);
   console.log(decoded.iat); // Issued at timestamp
   ```
2. **Verify key revocation list:**
   - Ensure old keys are blacklisted (e.g., via `jti` or DB lookup).

**Fix:**
- **Use asymmetric keys (RS256/ECDSA) for rotation:**
  ```javascript
  // Deploy new public key to clients
  // Keep old private key available for a short window
  ```
- **Implement a token blacklist (for symmetric keys):**
  ```javascript
  const blacklistedTokens = new Set();
  function verify(token) {
    if (blacklistedTokens.has(token)) throw new Error("Token blacklisted");
    return jwt.verify(token, key);
  }
  ```

---

### **3.7. Manual Signing Bypasses**
**Problem:**
Tokens signed manually (e.g., with `crypto.sign()`) instead of using a library, leading to invalid headers or malformed tokens.

**Symptoms:**
- Tokens missing `alg` header.
- Invalid payload structure.

**Debugging Steps:**
1. **Inspect raw token:**
   ```bash
   echo 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' | base64 -d | jq
   ```
2. **Check header alignment:**
   ```json
   {
     "alg": "HS256",
     "typ": "JWT"
   }
   ```

**Fix:**
- **Always use a library (e.g., `jsonwebtoken`, `jwt-simple`):**
  ```javascript
  // ✅ Correct: Library handles headers
  jwt.sign(payload, key);

  // ❌ Risky: Manual signing
  const header = Buffer.from(JSON.stringify({ alg: 'HS256' })).toString('base64');
  const payload = Buffer.from(JSON.stringify({ userId: 123 })).toString('base64');
  const signature = crypto.createHmac('sha256', key)
    .update(`${header}.${payload}`)
    .sign('hex');
  const token = `${header}.${payload}.${signature}`;
  ```

---

## **4. Debugging Tools & Techniques**

### **4.1. Token Inspection**
- **Online Decoders:** [jwt.io](https://jwt.io) (for quick checks).
- **Command Line:**
  ```bash
  echo 'header.payload.signature' | base64 -d | jq
  ```
- **Debug Middleware (Express):**
  ```javascript
  app.use((req, res, next) => {
    if (req.headers.authorization) {
      const token = req.headers.authorization.split(' ')[1];
      console.log('Decoded token:', jwt.decode(token));
    }
    next();
  });
  ```

### **4.2. Performance Profiling**
- **Node.js `perf_hooks`:**
  ```javascript
  const perfHooks = require('perf_hooks').performance;
  const start = perfHooks.now();
  jwt.sign(payload, key);
  console.log(`Signing took ${perfHooks.now() - start}ms`);
  ```
- **APM Tools:** New Relic, Datadog (for endpoint-level signing latency).

### **4.3. Key Validation**
- **Check key formats:**
  ```javascript
  function isValidKey(key) {
    return (
      key instanceof Buffer ||
      typeof key === 'string' &&
      (key.startsWith('-----BEGIN ') || key.length >= 32)
    );
  }
  ```
- **Test key rotation:**
  ```javascript
  // Sign with old key → verify with new key (should fail)
  const oldToken = jwt.sign(payload, oldKey);
  try { jwt.verify(oldToken, newKey); } catch (err) { console.log("Revoked correctly:", err.message); }
  ```

### **4.4. Logging & Monitoring**
- **Log signing/verification errors:**
  ```javascript
  app.use((err, req, res, next) => {
    if (err.name === 'JsonWebTokenError') {
      logger.error(`JWT Error: ${err.message}`, { token: req.headers.authorization });
    }
    next();
  });
  ```
- **Set up alerts for high latency in `/auth` endpoints.**

---

## **5. Prevention Strategies**

### **5.1. Secure Key Management**
- **Never commit keys to version control.**
  Add `.gitignore`:
  ```
  # Ignore sensitive files
  *.pem
  *.key
  ```
- **Use secrets managers (AWS Secrets, HashiCorp Vault).**
- **Rotate keys periodically (e.g., every 30 days for symmetric keys).**

### **5.2. Algorithm & Library Best Practices**
- **Avoid deprecated algorithms (SHA1, MD5).**
- **Use standardized libraries (e.g., `jsonwebtoken`, `libsodium`).**
- **Prefer ECDSA (P-256) over RSA for performance.**

### **5.3. Environment Separation**
- **Use different keys for dev/stage/prod.**
- **Never reuse keys across environments.**

### **5.4. Automated Testing**
- **Test signing/verification in CI:**
  ```javascript
  test('JWT signing/verification', () => {
    const payload = { userId: 123 };
    const token = jwt.sign(payload, key);
    expect(jwt.verify(token, key)).toEqual(payload);
  });
  ```
- **Fuzz test with invalid tokens (e.g., malformed headers).**

### **5.5. Observability**
- **Log token issuance/blacklisting events.**
- **Monitor token expiration stats (e.g., "tokens expiring in <1h").**

### **5.6. Security Hardening**
- **Rate-limit `/auth` endpoints.**
- **Use short-lived tokens (e.g., 15-min JWT + refresh tokens).**
- **Enable CORS restrictions for token endpoints.**

---

## **6. Quick Reference Cheat Sheet**

| **Issue**               | **Debug Command**                          | **Fix**                                  |
|--------------------------|--------------------------------------------|------------------------------------------|
| Wrong key                | `jwt.verify(token, key)` fails            | Check `process.env.JWT_SECRET`            |
| Algorithm mismatch       | `AlgorithmError` in logs                  | Standardize on `HS256`/`RS256`            |
| Slow performance         | High CPU in `/auth`                       | Switch to ECDSA or optimize key caching  |
| Clock skew               | `TokenExpiredError` despite recent token   | Set `clockTolerance: 60`                 |
| Key leakage              | Key in `server.log`                       | Redact logs, use structured logging       |
| Manual signing           | Missing `alg` header                      | Use `jsonwebtoken` library               |
| Race condition           | Intermittent auth failures                | Asymmetric keys + revocation list        |

---

## **7. Final Checklist Before Deployment**
✅ Keys are not hardcoded.
✅ Algorithm is `HS256`/`RS256` (no SHA1).
✅ Key rotation is tested.
✅ Tokens are short-lived.
✅ Logs don’t expose keys.
✅ Performance is profiled.
✅ CI tests signing/verification.

---
**Next Steps:**
- Auditing existing signing implementations.
- Implementing automatic key rotation.
- Setting up monitoring for token-related errors.