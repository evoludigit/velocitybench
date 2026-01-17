# **Debugging "Signing Migration" Pattern: A Troubleshooting Guide**
*(For Backend Engineers)*

---

## **1. Overview of the Signing Migration Pattern**
The **Signing Migration** pattern is used to securely transfer authority (e.g., API keys, JWT signing keys, or database credentials) from one system (e.g., old infrastructure) to a new one without exposing them in transit.

### **Key Use Cases:**
- **Zero-downtime migration** of secrets (e.g., AWS keys, database credentials).
- **Gradual rollout** of new signing keys while validating old ones.
- **Secure credential rotation** without exposing secrets in logs or environment variables.

### **How It Works:**
1. **Old system signs an authorization request** with its existing key.
2. **New system verifies the request** using the old key (temporarily).
3. **New system issues a signed response** authorizing the migration.
4. **Client/app updates its trust store** to use the new system’s key.

---

## **2. Symptom Checklist**
Check these symptoms when troubleshooting a Signing Migration issue:

| **Symptom**                          | **Possible Cause**                                                                 | **Action** |
|--------------------------------------|------------------------------------------------------------------------------------|------------|
| **Requests fail with `403 Forbidden`** | Old key verification fails or new key not trusted.                                  | Check key rotation status, logs, and client trust store. |
| **Latency spikes during migration**   | New system processing both old and new key signatures.                              | Monitor key switch timing. |
| **Partial functionality**            | Some requests use old key, others new (race condition).                             | Ensure atomic key rotation. |
| **Logs show failed HMAC/SHA verification** | Incorrect key material or signing algorithm mismatch.                              | Verify key hashing (e.g., `HMAC-SHA256`). |
| **Client apps timeout during migration** | New system response takes longer due to double-key validation.                  | Optimize validation logic. |
| **Audits show unauthorized access**   | Old key still granted access after cutoff.                                         | Force client updates via metadata. |

---

## **3. Common Issues & Fixes**

### **Issue 1: Key Verification Fails (HMAC/SHA Mismatch)**
**Symptoms:**
- `InvalidSignatureError` in logs.
- `403 Forbidden` responses for all requests.

**Root Cause:**
- The client or server uses a different key (e.g., wrong key derivate, incorrect HMAC algorithm).
- Timestamps in the signature are stale (e.g., `JWT` with `exp` field expired).

**Fix:**
**Server-Side (Node.js Example):**
```javascript
const crypto = require('crypto');
const { verify } = require('jsonwebtoken');

function isSignatureValid(requestSignature, payload, oldKey, newKey) {
  try {
    // Try old key first (fallback)
    verify(payload, oldKey, { algorithms: ['HS256'] });
    return { success: true, keyUsed: 'old' };
  } catch (err) {
    try {
      verify(payload, newKey, { algorithms: ['HS256'] });
      return { success: true, keyUsed: 'new' };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }
}

// Usage:
const result = isSignatureValid(req.headers.signature, req.body, oldKey, newKey);
if (!result.success) throw new Error(`Invalid signature: ${result.error}`);
```

**Client-Side (Python Example):**
```python
import hmac
import hashlib

def verify_signature(signature, payload, key):
    try:
        expected_signature = hmac.new(key, msg=payload.encode(), digestmod=hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected_signature)
    except:
        return False
```

---

### **Issue 2: Race Condition During Key Rotation**
**Symptoms:**
- Some requests use the old key, others use the new key (inconsistent behavior).
- Clients fail partway through migration.

**Root Cause:**
- No atomic switch; clients or services fall back to old keys after a delay.
- Database/topic changes (e.g., Kafka, Redis) aren’t synchronized.

**Fix:**
**Atomic Key Rotation Strategy:**
1. **Deploy new key** alongside old key.
2. **Use metadata headers** to enforce transitions:
   ```http
   X-Key-Rotation: transition old→new
   ```
3. **Force client update** after cutoff (e.g., via `x-api-version` header).

**Example (API Gateway Policy):**
```yaml
# AWS API Gateway: Force clients to use new key after TTL
x-api-version: "v2"  # Enforce new key after 2024-01-01
```

---

### **Issue 3: Slow Performance During Migration**
**Symptoms:**
- Requests take 3x longer during migration.
- Timeouts for clients using old systems.

**Root Cause:**
- Dual-key validation adds CPU overhead.
- Database lookups (e.g., `WHERE key_version = 1 OR key_version = 2`) bloat queries.

**Fix:**
**Optimizations:**
- **Caching:** Cache verified signatures (e.g., Redis).
- **Async Validation:** Use worker queues for key checks.
- **Hardware Acceleration:** Offload HMAC verification to AWS KMS or HSM.

**Example (Optimized Key Validator):**
```javascript
const cache = new NodeCache({ stdTTL: 600 }); // 10-minute cache

async function verifyWithCache(req, oldKey, newKey) {
  const cacheKey = JSON.stringify({ payload: req.body, timestamp: req.headers['x-request-time'] });
  const cached = cache.get(cacheKey);
  if (cached) return cached;

  const result = isSignatureValid(req.headers.signature, req.body, oldKey, newKey);
  if (result.success) cache.set(cacheKey, result);
  return result;
}
```

---

### **Issue 4: Client Apps Ignore New Key**
**Symptoms:**
- New key works in tests but fails in production.
- Logs show `UnknownKeyError` from client side.

**Root Cause:**
- Clients not updated with new public key.
- Key not properly installed in client libraries (e.g., `aws-sdk`, `jose`).

**Fix:**
**Client Update Strategy:**
1. **Bump API version** in metadata:
   ```json
   {
     "apiVersion": "2.0",
     "publicKey": "new_key_here"
   }
   ```
2. **Use feature flags** to enforce updates:
   ```javascript
   // Client-side check
   if (getFeatureFlag('keyMigrationComplete')) {
     verifyWithNewKey();
   } else {
     verifyWithOldKey();
   }
   ```
3. **For AWS SDK:** Use `credentials` chain fallback:
   ```javascript
   const client = new AWS.Service({ region: 'us-east-1', credentials: { chain: 'old→new' } });
   ```

---

## **4. Debugging Tools & Techniques**
### **Logging & Monitoring**
- **Key Switch Timeline:**
  ```bash
  # Track key rotation events (e.g., AWS CloudTrail, Datadog)
  grep "key.*switch" /var/log/api-gateway.log | ts '[%Y-%m-%d %H:%M:%S]'
  ```
- **Failure Analytics:**
  ```python
  # Python example for tracking failed verifications
  from prometheus_client import Counter
  FAILED_VERIFICATIONS = Counter('key_verification_failed', 'Failed HMAC/SHA checks')

  def verifySignature(sig, payload, key):
      if not hmac.compare_digest(sig, ...):
          FAILED_VERIFICATIONS.inc()
          raise ValueError("Signature failed")
  ```

### **Debugging Tools**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **`openssl dgst`**     | Verify HMAC manually: `openssl dgst -sha256 -hmac "old_key" -hex < payload` |
| **`jq`**               | Inspect JWT payloads: `echo "$JWT" | jq '.exp, .iat'`                              |
| **AWS KMS Debug Logs** | Check key access: `aws kms get-key-usage-metrics`                            |
| **Postman/Newman**     | Test API endpoints with custom headers: `x-signature`, `x-key-version`       |
| **Chaos Engineering**  | Kill old-key processes (e.g., `docker kill old-key-service`).               |

### **Network Debugging**
- **Capture Requests:**
  ```bash
  # Use Wireshark/tcpdump to inspect HTTP headers
  tcpdump -i any -A port 8080 | grep "X-Signature"
  ```
- **Compare Requests:**
  Use `curl` to replay successful vs. failing requests:
  ```bash
  # Save a working request
  curl -v -X POST http://api.example.com -H "X-Signature: $GOOD_SIG" > working_req.log

  # Compare with failing request
  diff working_req.log failed_req.log
  ```

---

## **5. Prevention Strategies**
### **Pre-Migration Checklist**
1. **Test Key Rotation:**
   - Simulate a key rotation in staging with 50% traffic.
   - Verify no data leakage (e.g., old key still works in prod).

2. **Automate Key Generation:**
   - Use **AWS KMS**, **HashiCorp Vault**, or **AWS Secrets Manager** to auto-derive keys.
   - Example (AWS KMS):
     ```bash
     aws kms generate-data-key --key-id old_key_alias --key-spec HSM --output text
     ```

3. **Document Rollback Plan:**
   - Keep old key in **read-only mode** for 24h post-migration.
   - Example rollback trigger:
     ```yaml
     # Prometheus Alert: If >5% requests fail for 1h, rollback
     - alert: KeyRotationFailure
       expr: rate(api_errors[5m]) > 0.05
       for: 1h
       labels: severity=critical
     ```

### **Post-Migration Best Practices**
- **Enforce Key Expiry:**
  - Set short-lived JWTs (e.g., `exp` in 1h) and rotate via ACLs.
- **Audit Logs:**
  - Use **AWS CloudTrail**, **OpenTelemetry**, or **Splunk** to track key usage.
- **Client Hardening:**
  - Use **code signing** for client binaries to prevent tampering.
  - Example (Signing JavaScript apps with Web Crypto API):
    ```javascript
    const { sign, verify } = crypto.subtle;
    const keyPair = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
    ```

---

## **6. Summary of Key Actions**
| **Step**               | **Action**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **Detect Issues**      | Check `403 Forbidden`, latency spikes, and failed verifications.             |
| **Validate Keys**      | Use `openssl`/`jq` to debug signatures.                                    |
| **Optimize Performance**| Cache validations, use async workers.                                     |
| **Enforce Migration**  | Use metadata headers (`x-api-version`) to force updates.                   |
| **Monitor**            | Track key usage with Prometheus/CloudTrail.                                  |
| **Prevent Future Issues** | Automate key rotation, audit logs, and document rollback plans.           |

---
**Final Note:**
Signing migrations are **high-risk, high-reward**. Always:
1. **Test in staging first.**
2. **Monitor failure rates in prod.**
3. **Have a rollback plan.**