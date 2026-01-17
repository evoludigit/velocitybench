# **Debugging Signing Patterns: A Troubleshooting Guide**
*For Backend Engineers*

Signing Patterns (e.g., JWT, HMAC, RSA, ECDSA) ensure data integrity, authentication, and authorization in distributed systems. Misconfigurations, key management errors, or cryptographic flaws can lead to security breaches, failed validations, or degraded performance.

This guide focuses on **practical debugging** for common Signing Pattern issues in backend systems.

---

## **1. Symptom Checklist**
Use this checklist to isolate the problem before deep-diving into fixes:

| Symptom | Likely Cause |
|---------|-------------|
| **401/403 Unauthorized** | Invalid/expired signatures, missing keys, or incorrect signing algorithms |
| **Signature verification fails** | Incorrect secret key, wrong hash algorithm, or tampered data |
| **High latency in signing/validation** | Poorly optimized crypto libraries or CPU-bound operations |
| **Key rotation failures** | Broken revocation mechanisms or stale cache |
| **CSRF vulnerabilities** | Missing `SameSite` cookies or insufficient signature checks |
| **Debug logs show `SignatureExpired`** | Token expiration too short or clock skew issues |
| **Key leakage risks** | Hardcoded secrets, improper JWKS caching, or exposed private keys |
| **Third-party API rejections** | Mismatched key types (RSA vs. ECDSA) or incorrect headers |

---

## **2. Common Issues & Fixes (With Code)**

### **Issue 1: Signature Validation Fails**
**Symptom:**
`Error: Signature verification failed: invalid signature`

**Root Causes:**
- Incorrect secret key (e.g., HMAC vs. RSA mismatch)
- Wrong algorithm (e.g., using `HS256` with a public key instead of `RS256`)
- Tampered request/response data (e.g., missing headers)
- Key revocation not enforced

**Debugging Steps:**
1. **Check the algorithm** – Ensure the signing algorithm matches the verification algorithm.
   ```javascript
   // Example: Verify JWT with `RS256` (RSA)
   const jose = require('jose');
   const { verify } = jose;

   verify(token, new jose.Key({ 'kty': 'RSA', 'crv': 'RS256', 'x5c': [...] }), algorithm: 'RS256');
   ```

2. **Compare the secret key** – If using HMAC, ensure the secret matches exactly (no extra spaces or encodings).
   ```go
   // Go (HMAC-SHA256)
   sig, err := hmac.New(sha256.New, []byte("EXACT_SECRET_KEY"))
   ```

3. **Log the raw signature** – Compare the generated vs. received signature:
   ```python
   import jwt
   from jwt.algorithms import HMACAlgorithm

   try:
       decoded = jwt.decode(token, "SECRET_KEY", algorithms=["HS256"])
   except jwt.ExpiredSignatureError:
       print("Token expired!")
   except jwt.InvalidSignatureError:
       print(f"Generated Sig: {hmac.sign('data', 'SECRET_KEY').hex()}")
       print(f"Received Sig: {token.split('.')[1]}")  # Compare!
   ```

**Fix:**
- Regenerate keys if compromised.
- Use **JWKS (JSON Web Key Set)** for dynamic key rotation:
  ```javascript
  // Express Middleware for JWKS Fetching
  app.use(async (req, res, next) => {
      const jwks = await fetch('https://auth.example.com/.well-known/jwks.json').then(res => res.json());
      req.jwks = jwks.keys;
      next();
  });
  ```

---

### **Issue 2: Token Expiration Too Soon (Clock Skew)**
**Symptom:**
`SignatureExpiredError` even when the token is fresh.

**Root Causes:**
- Server clock drift (e.g., AWS EC2 vs. NTP misconfig)
- `clock_tolerance` not set in JWT libraries

**Debugging Steps:**
1. **Verify server time**:
   ```bash
   date -u  # Check UTC time
   ```
2. **Log the issuer/exp times**:
   ```javascript
   const decoded = jwt.decode(token, { complete: true });
   console.log(`Issued at: ${decoded.header.iat}`);
   console.log(`Expires at: ${decoded.payload.exp}`);
   ```
3. **Adjust JWT library settings** (e.g., Python `pyjwt`):
   ```python
   from jwt import jwt, ExpiredSignatureError, decode

   try:
       decode(token, "SECRET", options={"verify_exp": True, "clock_tolerance": 5})  # 5 sec leeway
   except ExpiredSignatureError:
       print("Token expired (or clock skew)")
   ```

**Fix:**
- Use **NTP sync** (`ntpdate`) on servers.
- Set `clock_tolerance` in JWT libraries.

---

### **Issue 3: Key Rotation Failures**
**Symptom:**
Old tokens still accepted after key rotation.

**Root Causes:**
- Stale JWKS cache
- Missing `kid` (Key ID) in JWT header
- No revocation mechanism

**Debugging Steps:**
1. **Check `kid` in JWT header**:
   ```bash
   echo "token" | jq -r 'split(".")[0]' | base64url -d | jq .kid
   ```
2. **Log JWKS cache hits**:
   ```go
   // Go: Check if key is cached
   if cachedKey, ok := jwksCache[tokenHeader.kid]; ok {
       fmt.Println("Using cached key:", cachedKey)
   }
   ```
3. **Test with `curl`**:
   ```bash
   curl -X POST https://api.example.com/validate \
     -H "Authorization: Bearer $TOKEN" \
     -v  # Check if response includes `kid` in validation logs
   ```

**Fix:**
- Implement **JWKS rotation** with proper invalidation:
  ```javascript
  // Node.js: Invalidate old keys
  const jwksKeys = new Map();
  jwksKeys.set("old_kid", oldPublicKey);
  jwksKeys.set("new_kid", newPublicKey);
  ```
- Use **JWT `jku` (JWK Set URL)** for dynamic updates.

---

### **Issue 4: Performance Bottlenecks in Signing/Validation**
**Symptom:**
High latency in `/auth/validate` endpoint (e.g., >200ms).

**Root Causes:**
- Unoptimized crypto library (e.g., Python `cryptography` vs. Go’s `crypto/rsa`)
- Blocking key fetching (e.g., HTTP calls to JWKS endpoint)
- Expensive HMAC operations

**Debugging Steps:**
1. **Profile the code**:
   ```go
   // Go: Use pprof to identify bottlenecks
   go tool pprof http.post profile.out
   ```
2. **Benchmark signing vs. RSA/ECDSA**:
   ```bash
   ab -n 1000 -c 50 http://localhost:3000/validate  # Load test
   ```
3. **Cache JWKS locally**:
   ```javascript
   // Cache JWKS for 5 minutes
   let jwksCache;
   async function getJwks() {
       if (!jwksCache || Date.now() > jwksCache.expiresAt) {
           const response = await fetch('https://auth.example.com/jwks.json');
           jwksCache = { keys: await response.json(), expiresAt: Date.now() + 300000 };
       }
       return jwksCache;
   }
   ```

**Fix:**
- **Prefer RSA over ECDSA** (faster signing/validation).
- Use **Go’s `crypto` package** over Python `cryptography` for better performance.
- Offload signing to a **message queue** (e.g., AWS Lambda + SQS).

---

### **Issue 5: CSRF Protection Missing**
**Symptom:**
Attacker sends forged requests with valid JWT.

**Root Causes:**
- Missing `SameSite` cookie
- No CSRF token validation
- JWT used alone (no `state` parameter)

**Debugging Steps:**
1. **Check cookie headers**:
   ```bash
   curl -I http://localhost:3000/protected -H "Cookie: session=..."
   ```
2. **Validate CSRF token**:
   ```javascript
   // Express Middleware
   app.use((req, res, next) => {
       if (req.method === 'POST' && !req.cookies['csrf_token']) {
           return res.status(403).send('CSRF token missing');
       }
       next();
   });
   ```
3. **Use `SameSite=Strict`**:
   ```plaintext
   Set-Cookie: session=abc123; SameSite=Strict; Secure
   ```

**Fix:**
- **Enforce `SameSite=Strict`** on cookies.
- **Add CSRF tokens** to stateful sessions:
  ```javascript
  // Generate CSRF token on login
  res.cookie('csrf_token', crypto.randomBytes(32).toString('hex'));
  ```

---

## **3. Debugging Tools & Techniques**

| Tool/Technique | Usage |
|----------------|-------|
| **`openssl`** | Verify keys, decode JWT, test HMAC |
   ```bash
   echo "HEADER.PAYLOAD" | base64 -d | openssl dgst -sha256
   ```
| **`jq`** | Parse JWT headers/payloads |
   ```bash
   echo "HEADER" | base64url -d | jq
   ```
| **Postman/Insomnia** | Test signing/validation with custom headers |
| **`go tool pprof`** | Profile Go crypto bottlenecks |
| **`ab` (Apache Bench)** | Load-test signing endpoints |
| **`fail2ban`** | Block brute-force signing attempts |
| **AWS CloudTrail / GCP Audit Logs** | Monitor key access logs |

**Advanced Debugging:**
- **ChaCha20-Poly1305** (faster than AES for signing).
- **EdDSA** (faster than ECDSA, but less widely supported).
- **Benchmark cryptographic libraries**:
  ```c
  // OpenSSL benchmark
  openssl speed -evp hmac -out time.txt
  ```

---

## **4. Prevention Strategies**

### **A. Secure Key Management**
✅ **Use HSMs (Hardware Security Modules)** for private keys (AWS KMS, HashiCorp Vault).
✅ **Rotate keys automatically** (e.g., every 30 days for JWT).
✅ **Never hardcode secrets** – Use environment variables or secrets managers.
✅ **Audit key access** (GCP Cloud KMS, AWS IAM policies).

### **B. Algorithm & Library Best Practices**
✅ **Prefer RSA-OAEP over RSA-PKCS1** (more secure against attacks).
✅ **Use short-lived tokens** (e.g., 15-30 min expiry).
✅ **Enable `alg` restriction** (e.g., only allow `RS256`, not `HS256`).
✅ **Update crypto libraries** (e.g., `cryptography` v32+ for better performance).

### **C. Monitoring & Alerts**
✅ **Monitor failed validations** (e.g., Prometheus + Grafana).
✅ **Set up alerts for key rotation failures**.
✅ **Log JWT claims** (but **never log secrets**).
✅ **Use WAF rules** to block suspicious requests (e.g., Cloudflare Bot Management).

### **D. Testing & Chaos Engineering**
✅ **Chaos test key revocation** (kill the JWKS endpoint to simulate failure).
✅ **Fuzz test signing/validation** (e.g., OWASP ZAP).
✅ **Penetration test JWT flows** (Burp Suite, JWT Hacker Tool).

---
## **Final Checklist for Signing Pattern Security**
| Check | Done? |
|-------|-------|
| Keys stored in HSM/secrets manager? | ☐ |
| Key rotation automated? | ☐ |
| `clock_tolerance` set in JWT lib? | ☐ |
| `SameSite` cookies enforced? | ☐ |
| CSRF protection implemented? | ☐ |
| Failed validations logged? | ☐ |
| Algorithms restricted (e.g., no `HS256` + RSA)? | ☐ |
| Load-tested signing endpoints? | ☐ |

---
### **Summary**
- **Debugging:** Compare signatures, check clocks, validate `kid`, profile performance.
- **Fixing:** Update keys, adjust tolerances, cache JWKS, optimize crypto.
- **Preventing:** Use HSMs, rotate keys, monitor, test.

Signing Patterns are critical—**failures here can break authentication entirely**. Always verify end-to-end with real-world traffic.

---
**Next Steps:**
- [OWASP JWT Testing Guide](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_developers.html)
- [Cloudflare’s JWT Security Guide](https://blog.cloudflare.com/jwt-security-best-practices/)