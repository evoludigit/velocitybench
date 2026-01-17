# **Debugging Signing Debugging: A Troubleshooting Guide**

## **1. Introduction**
The **"Signing Debugging"** pattern is used to ensure data integrity, authenticity, and non-repudiation by verifying cryptographic signatures embedded in messages, tokens, or data payloads. Common use cases include:
- API request validation
- Microservices communication authentication
- JWT (JSON Web Token) verification
- Blockchain/ledger data validation
- Audit logging and tamper-proofing

This guide provides structured troubleshooting steps to diagnose and resolve signature-related issues efficiently.

---

## **2. Symptom Checklist**
Before diving into debugging, check for these common symptoms:

| **Symptom**                     | **Description**                                                                 |
|---------------------------------|---------------------------------------------------------------------------------|
| **Failed signature verification** | HTTP 401/403 errors, JWT validation failures, or custom signing checks rejecting data. |
| **Random signature mismatches**   | Signatures work intermittently or fail in specific environments (dev/stage/prod). |
| **"Signature expired" errors**   | Timestamps in signed payloads are invalid or too far into the future/past.      |
| **Partial data corruption**      | Only some fields in a signed payload fail verification (e.g., JWT missing claims). |
| **Performance degradation**      | Slow signature verification (especially in high-load systems).                  |
| **Environment-specific failures**| Works in local dev but fails in CI/CD or production.                            |
| **Missing/incorrect keys**       | Private keys missing, wrong key formats, or misconfigured key rotation.         |

---

## **3. Common Issues & Fixes**

### **Issue 1: Failed Signature Verification**
**Symptoms:**
- HTTP 403: Invalid signature
- `JSONWebTokenError: jwt expired` (if short-lived)
- Custom signing checks failing silently or throwing vague errors

**Root Causes:**
- Incorrect **secret key** (e.g., hardcoded wrong values, environment mismatch).
- **Missing/expired** JWT (if using short-lived tokens).
- **Key rotation** not handled (old keys still referenced).
- **Data tampering** (payload modified after signing).
- **Clock skew** (server time vs. token issue time).

#### **Debugging Steps:**
1. **Log the raw payload and signature** for comparison:
   ```javascript
   const payload = req.headers['x-signed-payload'];
   const signature = req.headers['x-signature'];
   console.log('Payload:', payload, 'Signature:', signature);
   ```
2. **Verify the signature manually** (using the correct secret):
   ```javascript
   const jwt = require('jsonwebtoken');
   try {
     const verified = jwt.verify(payload, process.env.JWT_SECRET);
     console.log('Signature valid:', verified);
   } catch (err) {
     console.error('Signature error:', err.message);
   }
   ```
3. **Check for clock drift** (if JWT):
   ```javascript
   // Adjust leeway (e.g., 1 minute) if needed
   jwt.verify(payload, key, { clockTolerance: 60 });
   ```
4. **Inspect key storage**:
   ```bash
   # Example: Check AWS KMS key ARN in env vars
   echo $SIGNING_KEY_ARN
   ```

**Fixes:**
- **Re-generate secrets** and rotate keys properly (use tools like AWS KMS, HashiCorp Vault).
- **Ensure time sync** (NTP) across all servers.
- **Add logging for failures** (e.g., `logger.error('Signature failed:', { payload, signature, error })`).

---

### **Issue 2: Random Signature Failures (Intermittent)**
**Symptoms:**
- Signatures work in local dev but fail in staging/production.
- No consistent pattern (e.g., works for API A but not API B).

**Root Causes:**
- **Environment variable mismatches** (e.g., `DEV_KEY` vs. `PROD_KEY`).
- **Key caching issues** (e.g., stale keys in a cache layer like Redis).
- **Network latency** (e.g., signing happens async but fails due to timeouts).
- **Race conditions** in multi-threaded signing.

#### **Debugging Steps:**
1. **Compare exact keys** (avoid secrets in logs, use hashes):
   ```bash
   echo "DEV_KEY=$(echo $DEV_KEY | sha256sum)"  # Log hash instead
   ```
2. **Check for caching layers** (e.g., Redis, CDN):
   ```bash
   # Purge cache before testing
   redis-cli FLUSHDB
   ```
3. **Enable verbose logging** for signing libraries:
   ```javascript
   process.env.DEBUG = 'jwt-verify,signing';
   ```
4. **Test with a known-good signature**:
   ```bash
   # Manually sign a test payload
   echo '{"test":1}' | openssl dgst -sha256 -sign private_key.pem
   ```

**Fixes:**
- **Use feature flags** to toggle signing in dev.
- **Implement key versioning** (e.g., `key-v1`, `key-v2`).
- **Add retry logic** with exponential backoff for async signing.

---

### **Issue 3: Partial Data Validation Failures**
**Symptoms:**
- Only some fields in a JWT payload fail verification (e.g., `iat` valid but `nbf` invalid).
- Custom claims (e.g., `user.role`) are ignored during verification.

**Root Causes:**
- **Incomplete key validation** (e.g., only checking `alg` but not `typ`).
- **Missing optional claims** in verification (e.g., `nbf` not required).
- **Custom signing libraries** with overly strict checks.

#### **Debugging Steps:**
1. **Inspect the JWT payload structure**:
   ```bash
   echo '{"alg":"HS256","typ":"JWT"}' | jq '.'  # Check header
   echo '{"test":1}' | openssl dgst -sha256 -sign private_key.pem | base64 -d | jq '.'
   ```
2. **Compare against a known-good token**:
   ```javascript
   const goodToken = jwt.sign({ test: 1 }, 'secret', { expiresIn: '1m' });
   console.log('Good token:', goodToken);
   ```
3. **Adjust verification options**:
   ```javascript
   jwt.verify(token, key, {
     algorithms: ['HS256'], // Restrict allowed algs
     issuer: 'trusted-issuer', // Validate issuer
     audience: 'api-client'   // Validate audience
   });
   ```

**Fixes:**
- **Standardize payload schemas** (e.g., use OpenAPI for JWT claims).
- **Add schema validation** (e.g., `zod`, `joi`) before signing.

---

## **4. Debugging Tools & Techniques**

### **A. Logging & Monitoring**
- **Structured logging** (for correlation):
  ```javascript
  const { v4: uuidv4 } = require('uuid');
  const requestId = uuidv4();
  logger.info('Signing attempt', { requestId, payload, signature });
  ```
- **Distributed tracing** (e.g., OpenTelemetry) to track signature flow.

### **B. Key Management Debugging**
- **AWS KMS Debugging**:
  ```bash
  aws kms describe-key --key-id alias/your-key
  ```
- **Hashicorp Vault Debugging**:
  ```bash
  vault read secret/signing-key
  ```

### **C. Performance Profiling**
- **Benchmark signature speed**:
  ```bash
  ab -n 1000 -c 100 http://localhost/sign  # Use ApacheBench
  ```
- **Profile slow verifications** (e.g., with `node --inspect` + Chrome DevTools).

### **D. Postmortem Analysis**
- **Capture failing signatures** in a dead-letter queue (DLQ).
- **Analyze failure patterns** (e.g., is it always the same key?).

---

## **5. Prevention Strategies**

| **Strategy**                          | **Implementation**                                                                 |
|---------------------------------------|-------------------------------------------------------------------------------------|
| **Key Rotation Automation**           | Use tools like AWS KMS or Vault to auto-rotate keys.                               |
| **Secret Management**                 | Never hardcode keys; use **environment variables** or **secrets managers**.         |
| **Time Synchronization**              | Deploy **NTP** (e.g., `chrony`, `ntpd`) to avoid clock skew.                       |
| **Signature Validation Middleware**   | Centralize signing checks (e.g., Express middleware, AWS Lambda layers).           |
| **Schema Validation**                 | Validate payloads **before** signing (e.g., `zod` schema).                          |
| **Test Coverage for Signing**         | Mock signing libraries in unit tests (e.g., `jest.mock('jsonwebtoken')`).          |
| **Canary Deployments**                | Roll out key changes gradually to avoid outages.                                     |
| **Alerting**                          | Monitor signature failures (e.g., Prometheus + Alertmanager).                      |

### **Example: Secure Signing Middleware (Node.js)**
```javascript
const jwt = require('jsonwebtoken');

function signingMiddleware(req, res, next) {
  const signature = req.headers['x-signature'];
  const payload = req.headers['x-payload'];

  jwt.verify(payload, process.env.JWT_SECRET, (err, decoded) => {
    if (err) return res.status(403).send('Invalid signature');
    req.user = decoded;
    next();
  });
}
```

---

## **6. Checklist for Quick Resolution**
| **Step**                          | **Action**                                                                 |
|-----------------------------------|----------------------------------------------------------------------------|
| 1. **Log raw payload/signature**  | Capture exact values for comparison.                                      |
| 2. **Check keys**                 | Verify `JWT_SECRET`, KMS ARN, or Vault path.                               |
| 3. **Test manually**              | Sign/verify locally with `openssl` or `jwt.io`.                            |
| 4. **Inspect environment vars**    | Ensure `DEV` vs. `PROD` keys are correct.                                  |
| 5. **Enable debug logs**          | Use `DEBUG=jwt` or equivalent.                                             |
| 6. **Compare with good token**     | Decode a known-working token for reference.                                |
| 7. **Adjust validation options**   | Tweak `clockTolerance`, `algorithms`, or `issuer`.                          |
| 8. **Rotate keys**                | If old keys are failing, rotate and test incrementally.                      |

---

## **7. Conclusion**
Signing debugging often boils down to **three core issues**:
1. **Key mismatches** (wrong secret, expired, or missing).
2. **Time synchronization** (clock drift causing JWT expiry).
3. **Partial validation failures** (incomplete payload checks).

**Key takeaways:**
✅ **Log everything** (payloads, signatures, errors).
✅ **Test in isolation** (sign/verify locally before production).
✅ **Automate key rotation** (never manually update secrets).
✅ **Monitor failures** (alert on signature rejection spikes).

By following this guide, you can diagnose and resolve signing issues in **<30 minutes** in most cases. For persistent problems, use distributed tracing and postmortem analysis to identify root causes.