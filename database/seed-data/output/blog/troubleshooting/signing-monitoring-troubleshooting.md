# **Debugging Signing Monitoring: A Troubleshooting Guide**
*A Practical Backend Engineer’s Guide to Resolving Signing-Related Issues*

---

## **1. Introduction**
The **Signing Monitoring** pattern ensures data integrity by verifying digital signatures (e.g., JWT, HMAC, RSA) before processing requests, logs, or system events. When this pattern fails, it can lead to:
- **Unauthorized access** (invalid signatures bypassing auth)
- **Data corruption** (malformed or tampered payloads)
- **System outages** (cryptographic key mismatches)
- **Audit failures** (invalid logs or metrics)

This guide provides **practical steps** to identify, diagnose, and resolve common signing-related issues quickly.

---

## **2. Symptom Checklist**
Before diving into debugging, verify the following symptoms:

| **Symptom**                          | **Likely Cause**                          | **Impact Level** |
|---------------------------------------|-------------------------------------------|------------------|
| **`401 Unauthorized` on API calls**  | Invalid JWT/HMAC signature                | Critical         |
| **`403 Forbidden` with signed logs**  | Expired or invalid signature              | High             |
| **System crashes on signature validation** | Key mismatch or corrupted keys       | Critical         |
| **Audit logs show tampered entries**  | Weak or broken HMAC/RSA verification     | High             |
| **Slow response times on signed payloads** | Expensive key operations (e.g., RSA) | Medium           |
| **Signatures failing intermittently** | Clock skew (JWT expiry checks)           | Medium           |

**Next Steps:**
- Check **error logs** (`stderr`, `audit logs`, `metrics`).
- Reproduce the issue with a **test payload** (e.g., `curl` with malformed headers).
- Verify **key storage** (HSM, AWS KMS, local files).

---

## **3. Common Issues & Fixes**

### **Issue 1: Invalid Signatures (401/403 Errors)**
**Symptoms:**
- API returns `401 Unauthorized` despite correct credentials.
- HMAC/JWT signatures fail verification.

**Root Causes:**
✅ **Incorrect Secret Key** (e.g., wrong HMAC secret, leaked key).
✅ **Clock Skew** (JWT `exp`/`nbf` misaligned with server time).
✅ **Key Rotation Not Applied** (old key still in use).
✅ **Base64URL Decoding Errors** (malformed JWT payload/headers).

#### **Debugging Steps:**
1. **Log the Raw Signature & Payload**
   ```javascript
   // Example (Node.js with JWT)
   const jwt = require('jsonwebtoken');
   const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

   try {
     const decoded = jwt.verify(token, "CORRECT_SECRET");
     console.log("Decoded payload:", decoded);
   } catch (err) {
     console.error("Verification failed:", err);
     console.log("Raw token:", token); // Compare with expected signature
   }
   ```
   - **Check:** Is the secret key **exactly the same** as during signing?
   - **Fix:** Regenerate keys if compromised (`openssl rand -hex 32` for HMAC).

2. **Verify Time Synchronization**
   ```bash
   # Linux: Check NTP status
   timedatectl status
   # Windows: Check Time Sync Settings
   w32tm /query /status
   ```
   - **Fix:** Adjust server time or use **leeway in JWT expiry** (`exp: Math.floor(Date.now() / 1000) + 300`).

3. **Test with a Known Good Token**
   ```bash
   curl -X POST \
     http://api.example.com/protected \
     -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
     -H "Content-Type: application/json" \
     -d '{"test": "payload"}'
   ```
   - **Expected:** `200 OK` if the token is valid.
   - **If failure:** Compare the token with a **working example** (e.g., Postman).

---

### **Issue 2: Slow Signature Validation (High Latency)**
**Symptoms:**
- API responses take **2-3x longer** for signed requests.
- `CPU usage spikes` during signature checks.

**Root Causes:**
✅ **Expensive Algorithm** (e.g., RSA-OAEP vs. HMAC-SHA256).
✅ **Key Lookup Bottleneck** (KMS/HSM latency).
✅ **Parallel Signature Verification** (e.g., per-field HMAC).

#### **Debugging Steps:**
1. **Profile the Code**
   ```python
   # Python (using `cProfile`)
   import cProfile
   def verify_signature():
       import hmac, hashlib
       key = b'secret'
       message = b'test'
       hmac.new(key, message, hashlib.sha256).hexdigest()

   cProfile.runctx("verify_signature()", globals(), locals(), "profile.out")
   ```
   - **Identify:** Is the bottleneck in `sha256()` or key access?

2. **Benchmark Key Storage**
   - **Local Key:** Fast (but insecure).
   - **AWS KMS:** ~100ms latency.
   - **HSM (e.g., AWS CloudHSM):** ~200ms.
   - **Fix:** Cache keys in-memory (short-lived) or optimize KMS calls.

3. **Switch to Faster Algorithms**
   ```javascript
   // Prefer HMAC over RSA where possible
   const hmac = require('crypto').createHmac('sha256', 'secret');
   hmac.update('data').digest('hex'); // Faster than RSA
   ```

---

### **Issue 3: Key Rotation Failures**
**Symptoms:**
- Some services accept old signatures, others reject them.
- Mixed behaviors in microservices.

**Root Causes:**
✅ **No Key Rotation Strategy** (old key not revoked).
✅ **Async Key Update** (cache inconsistency).
✅ **Service Misconfiguration** (some services ignore `kid` claim).

#### **Debugging Steps:**
1. **Check `kid` Claim in JWT**
   ```json
   {
     "kid": "old-key-123",  // Should match current public key
     "exp": 1234567890
   }
   ```
   - **Fix:** Ensure **all services** validate `kid` and fetch the correct public key.

2. **Test Key Revocation**
   ```bash
   # Simulate an old key
   OPENSSL_KEY="old_key_base64"
   NEW_KEY="new_key_base64"

   # Verify old key fails
   jwt verify --secret "$OPENSSL_KEY" --token "eyJhbGciOiJSUzI1NiIsImtpZCI6Im9sdGV..."  # Should fail
   ```
   - **Fix:** Update **all clients** to use the new key + revoke the old one.

3. **Implement a Grace Period**
   ```go
   // Go example: Allow old keys for 1 hour after rotation
   func isKeyValid(keyID string, now time.Time) bool {
       if now.Sub(lastRotationTime) < 3600*time.Second {
           return true // Allow old key
       }
       return keyID == currentKeyID
   }
   ```

---

### **Issue 4: Base64URL Decoding Errors**
**Symptoms:**
- `Error: invalid signature` with no clear cause.
- JWT payload shows `eyJh...` instead of decoded JSON.

**Root Causes:**
✅ **Malformed Base64URL** (missing padding, wrong padding).
✅ **Incorrect URL-safe Decoding** (e.g., `+` → `-`, `/` → `_`).
✅ **Corrupted Token** (network issues during transmission).

#### **Debugging Steps:**
1. **Manually Decode the JWT**
   ```bash
   # Decode JWT parts (remove padding first)
   echo "eyJhbGciOiJIUzI1NiJ9" | base64 --decode
   ```
   - **Fix:** Ensure tokens are **properly URL-decoded** before verification.

2. **Validate Token Structure**
   ```python
   import base64

   token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
   parts = token.split('.')

   # Fix URL-safe decoding
   def urlsafe_b64decode(s):
       s = s.replace('-', '+').replace('_', '/')
       return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))

   header = urlsafe_b64decode(parts[0])
   payload = urlsafe_b64decode(parts[1])
   print(header, payload)
   ```
   - **Expected:** `b'{"alg":"HS256","typ":"JWT"}'`, `b'{"sub":"123456789","name":"John Doe"...'`

3. **Check for Transmission Errors**
   - **Fix:** Ensure tokens are **transmitted over HTTPS** (not HTTP) to prevent tampering.

---

## **4. Debugging Tools & Techniques**

| **Tool**               | **Use Case**                                  | **Example Command/Code**                          |
|------------------------|-----------------------------------------------|---------------------------------------------------|
| **`jq` (JWT Debugging)** | Parse and validate JWT structure.            | `echo $TOKEN | jq -r '@base64d'`                                |
| **Postman**            | Test signed requests manually.                | Send `Authorization: Bearer <token>`              |
| **`openssl`**          | Verify HMAC/RSA signatures.                   | `openssl dgst -sha256 -hmac "secret" -binary "data" | base64` |
| **`jwt_tool`**         | CLI tool for JWT analysis.                   | `jwt decode --secret "key" <token>`               |
| **`cURL` (Debug Headers)** | Check raw HTTP requests.               | `curl -v -H "Authorization: Bearer ..." <url>`    |
| **Tracing (OpenTelemetry)** | Track signature latency in distributed systems. | Add timing to `jwt.verify()` calls.               |
| **Key Rotation Simulator** | Test revocation policies.               | Rotate keys in staging and monitor failures.      |

**Pro Tip:**
- **Use a sandbox** (e.g., Docker) to test key rotation without affecting production.
- **Log raw tokens** (redact secrets) for audit trails:
  ```javascript
  console.log(`[DEBUG] Raw Token (truncated): ${token.slice(0, 60)}...`);
  ```

---

## **5. Prevention Strategies**
### **A. Secure Key Management**
- **Never hardcode secrets** → Use **environment variables** or **secret managers** (AWS Secrets Manager, HashiCorp Vault).
- **Rotate keys automatically** → Use tools like:
  ```bash
  # Example: AWS KMS key rotation (via CloudWatch Events)
  aws kms enable-key-rotation --key-id alias/my-key
  ```
- **Cache keys short-lived** → Invalidate cache after rotation.

### **B. Robust Validation**
- **Always check `exp`, `nbf`, and `iat`** (not just `alg`).
  ```python
  from datetime import datetime
  def is_jwt_valid(token, now=None):
      try:
          decoded = jwt.decode(token, "secret", algorithms=["HS256"])
          if now is None:
              now = datetime.utcnow()
          if decoded["exp"] < now.timestamp():
              return False
          return True
      except:
          return False
  ```
- **Use strict HMAC algorithms** → Avoid weak hashes (`SHA1`).

### **C. Monitoring & Alerts**
- **Monitor signature failure rates** (Prometheus/Grafana):
  ```promql
  rate(jwt_signature_fails_total[5m]) / rate(jwt_signature_attempts_total[5m]) > 0.01
  ```
- **Alert on key rotation failures** (e.g., Datadog):
  ```yaml
  # Alert if >10% of requests fail after key rotation
  - alert: HighSignatureFailureRate
    expr: rate(jwt_errors[1m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Signature validation failing ({{ $value }}%)"
  ```

### **D. Testing**
- **Unit Tests for Signing/Verification**
  ```typescript
  // Example (Jest)
  test("JWT verification fails on wrong secret", () => {
      const token = jwt.sign({ user: "alice" }, "correct_key", { expiresIn: '1m' });
      expect(() => jwt.verify(token, "wrong_key")).toThrow();
  });
  ```
- **Chaos Engineering** → Inject bad signatures to test resilience.

---

## **6. Quick Reference Cheat Sheet**
| **Problem**               | **First Check**               | **Immediate Fix**                          | **Long-Term Fix** |
|---------------------------|-------------------------------|--------------------------------------------|-------------------|
| `401 Unauthorized`        | Secret key mismatch?           | Verify `secret` in code matches signing.   | Rotate key, use Vault. |
| Slow signature checks     | Using RSA instead of HMAC?     | Benchmark algorithms.                    | Cache keys, optimize KMS. |
| Key rotation broken       | `kid` claim ignored?           | Ensure all services validate `kid`.        | Implement graceful rotation. |
| Base64URL decode fails     | Missing padding?               | Add `=` to decode properly.               | Validate input strictly. |
| Intermittent failures     | Clock skew?                   | Adjust `nbf`/`exp` leeway.                | Use NTP, log time differences. |

---

## **7. Conclusion**
Signing Monitoring failures are often **symptoms of misconfiguration**, not defects. Follow this guide’s **structured debugging approach**:
1. **Reproduce** the issue with a test payload.
2. **Log raw data** (tokens, keys, timestamps).
3. **Compare expected vs. actual** behavior.
4. **Fix at the source** (keys, algorithms, time sync).
5. **Prevent recurrence** (automated rotation, monitoring).

**Final Tip:** If all else fails, **compare against a known-good example**—most signing issues boil down to **key mismatches or clock drift**.

---
**Further Reading:**
- [OAuth 2.0 JWT Best Practices](https://tools.ietf.org/html/rfc7519)
- [AWS KMS Key Rotation Guide](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html)
- [Base64URL Decoding Pitfalls](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.171.pdf)