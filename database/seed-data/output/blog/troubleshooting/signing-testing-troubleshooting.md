# **Debugging Signing & Testing: A Troubleshooting Guide**
*For Backend Engineers Handling Cryptographic & Authentication Failures*

---

## **1. Introduction**
The **Signing & Testing** pattern ensures data integrity, authentication, and non-repudiation by generating and verifying cryptographic signatures. Common use cases include:
- **JWT Validation** (API security)
- **API Key Authentication** (service-to-service)
- **Blockchain Transactions** (smart contract interactions)
- **File/Message Signing** (secure communication)

Failure in signing or verification leads to **authentication errors, API rejections, or security breaches**. This guide provides a structured approach to debugging issues efficiently.

---

## **2. Symptom Checklist**
Before diving into fixes, confirm the issue with this checklist:

| Symptom | Possible Cause |
|---------|----------------|
| ✅ **"Signature verification failed"** (e.g., `InvalidSignature` in JWT) | Wrong key, missing key rotation, or tampered payload |
| ✅ **API returns `401 Unauthorized`** | Invalid, expired, or missing signature |
| ✅ **Database record tampered** (e.g., financial transaction) | Missing signature verification |
| ✅ **API client rejects server response** | Unsigned/weakly signed payload |
| ✅ **Logging shows `HMAC mismatch`** | Incorrect secret key or key alignment |
| ✅ **Blockchain tx fails** (e.g., `invalid signature`) | Wrong private key or nonce issue |
| ✅ **"Key not found" errors** in signing | Missing key in keychain/secret manager |

---
**Next Step:** Identify if the issue is in **signing** (client-side) or **verification** (server-side).

---

## **3. Common Issues & Fixes**

### **Issue 1: Signature Mismatch (HMAC/SHA-256)**
**Symptoms:**
- `InvalidSignature` (JWT)
- `HMAC does not match` (custom signing)
- API rejects payload with `401`

**Root Causes:**
✔ Wrong secret key (stored incorrectly)
✔ Key rotation not applied
✔ Payload tampering (e.g., extra spaces, encoding issues)
✔ Time skew in JWT expiration

**Fixes:**

#### **A. Verify the Secret Key**
```javascript
// Example: Check if the secret key matches expected value
const expectedSecret = "your-secret-key-123";
const actualSecret = process.env.SIGNING_SECRET;

// Debug: Log keys for comparison
console.log(`Expected: ${expectedSecret}`);
console.log(`Actual: ${actualSecret}`);
if (expectedSecret !== actualSecret) {
  throw new Error("KEY_MISMATCH: Secret key mismatch!");
}
```

#### **B. Reproduce Signing Locally**
```python
# Python (HMAC-SHA256 Example)
import hmac, hashlib

secret = b"your-secret-key-123"
data = b"payload-to-sign"

# Re-sign to verify
signature = hmac.new(secret, data, hashlib.sha256).hexdigest()
print(f"Generated Signature: {signature}")
```

#### **C. Check Key Rotation**
If using **AWS KMS**, **HashiCorp Vault**, or **Okta**, ensure:
```bash
# Example: List active keys in AWS KMS
aws kms list-aliases --query 'Aliases[?starts_with(Name, \'alias/your-signing-key\')]'
```
- If old keys are still in use, **update clients**.

---

### **Issue 2: JWT Expiration or Clock Skew**
**Symptoms:**
- `exp` claim validation fails
- Server time vs. client time mismatch

**Fixes:**

#### **A. Adjust Server Time (if needed)**
```javascript
// Node.js: Force UTC time for JWT (if local time is off)
const jwt = require('jsonwebtoken');
const utcTime = new Date().toUTCString();

const token = jwt.sign(
  { userId: 123, exp: Math.floor(utcTime / 1000) + 3600 },
  process.env.JWT_SECRET,
  { algorithm: 'HS256' }
);
```

#### **B. Extend Leeway in Verification (if needed)**
```javascript
jwt.verify(token, process.env.JWT_SECRET, {
  algorithms: ['HS256'],
  clockTolerance: 60 // Allow 60s leeway
});
```

---

### **Issue 3: Key Not Found (Missing or Expired)**
**Symptoms:**
- `Key not found` in AWS KMS/Vault
- `InvalidKeyId` error

**Fixes:**

#### **A. Check Keychain/Secret Manager**
```bash
# Example: List keys in AWS Secrets Manager
aws secretsmanager list-secrets
```

#### **B. Regenerate Expired Keys**
```bash
# Example: Create a new HMAC-SHA256 key in AWS KMS
aws kms create-key --description "Signing Key (JWT)"
```

#### **C. Update Clients to Use New Key**
```json
// Example: Update JWT secret in client config
{
  "auth": {
    "jwtSecret": "NEW_SECRET_XXXX"
  }
}
```

---

### **Issue 4: Blockchain Signature Failures**
**Symptoms:**
- Ethers.js: `invalid signature`
- Web3.js: `VM Exception while processing transaction`

**Fixes:**

#### **A. Verify Private Key Correctly**
```javascript
// Ethers.js: Check if private key is correct
const { Wallet } = require('ethers');
const pk = '0x123...'; // Your private key
const wallet = new Wallet(pk);
console.log(wallet.address); // Should match expected address
```

#### **B. Re-sign with Correct Nonce**
```javascript
// If nonce is wrong, resubmit with correct nonce
const { ethers } = require('ethers');
const nonce = await provider.getTransactionCount(wallet.address);
const tx = await wallet.sendTransaction({
  to: recipient,
  value: ethers.utils.parseEther('1.0'),
  nonce: nonce
});
```

---

## **4. Debugging Tools & Techniques**

| Tool/Technique | Use Case |
|----------------|----------|
| **`openssl dgst -sha256 -hmac "secret" "data"`** | Verify HMAC signing manually |
| **`jwt.io` (Online Decoder)** | Debug JWT payload/secret mismatches |
| **AWS KMS CLI** (`aws kms list-keys`) | Check active signing keys |
| **HashiCorp Vault Dev Mode** (`vault read secret/signing-key`) | Test local key retrieval |
| **Postman/Insomnia** (Logging) | Capture raw request/response |
| **`node-inspect` (Chrome DevTools)** | Debug Node.js signing errors |
| **`strace` (Linux)** | Check file descriptor issues (e.g., missing `.pem` file) |

**Example Debug Workflow:**
1. **Capture failing request** (Postman/Insomnia).
2. **Reproduce signing locally** (Python/Node.js).
3. **Compare hashes** (`openssl` vs. app-generated).
4. **Check keychain logs** (AWS CloudTrail, Vault audit logs).

---

## **5. Prevention Strategies**

### **A. Key Management Best Practices**
✅ **Use Hardware Security Modules (HSMs)** for high-risk keys.
✅ **Rotate keys periodically** (e.g., every 6 months).
✅ **Enforce least privilege** (e.g., KMS policies restrict key usage).
✅ **Audit key access** (AWS CloudTrail, HashiCorp Vault audit logs).

### **B. Code-Level Protections**
✅ **Validate all payloads** before signing:
```javascript
// Node.js: Example payload validation
const { validate } = require('jsonschema');
const schema = { type: 'object', required: ['userId'] };

if (!validate(payload, schema).valid) {
  throw new Error("INVALID_PAYLOAD");
}
```

✅ **Use constant-time comparisons** (prevent timing attacks):
```python
# Python: Secure HMAC comparison
import hmac, hashlib

def secure_compare(a, b):
    return hmac.compare_digest(a, b)

if not secure_compare(actual_signature, expected_signature):
    raise ValueError("Signature mismatch")
```

✅ **Log signing events** (for audit):
```javascript
console.log(`[SIGNING] User ${userId} signed payload at ${new Date()}`);
```

### **C. Testing Strategies**
✅ **Unit Tests for Signing**
```javascript
// Jest Example: Test JWT signing
test('JWT signing works', () => {
  const token = jwt.sign({ userId: 1 }, 'secret', { expiresIn: '1h' });
  expect(jwt.verify(token, 'secret')).toEqual({ userId: 1 });
});
```

✅ **Fuzz Testing for Edge Cases**
- Test with **malformed payloads** (e.g., `{"userId": null}`).
- Test with **expired/old keys**.
- Test **time skew** (server vs. client clocks).

✅ **Chaos Engineering for Key Failures**
- Simulate **key deletion** in Vault/KMS.
- Test **key rotation** in staging.

---

## **6. Final Checklist Before Deployment**
| Task | Status |
|------|--------|
| ✅ All signing keys are rotated (if needed) | ☐ |
| ✅ Client & server use the same secret key | ☐ |
| ✅ Time synchronization (NTP) is working | ☐ |
| ✅ JWT clock tolerance is reasonable (≤ 5 min) | ☐ |
| ✅ Key access logs are enabled (AWS CloudTrail/Vault) | ☐ |
| ✅ Signing payload validation is enforced | ☐ |
| ✅ Backup keys are stored securely | ☐ |

---
## **7. Next Steps**
1. **Reproduce the issue locally** (if not done).
2. **Compare hashes/keys** manually (`openssl`, `jwt.io`).
3. **Update keys or client configs** if needed.
4. **Monitor logs** for recurring issues.
5. **Automate key rotation** (e.g., AWS KMS scheduled aliases).

---
**Pro Tip:**
If dealing with **blockchain signatures**, ensure the **private key never leaves the local machine** (use `ethers.Wallet.fromMnemonic()` instead of raw keys).

---
This guide should help resolve **90% of signing/testing issues** in backend systems. For persistent problems, check:
- **Network latency** (affects time-based claims).
- **Proxy/modifications** (e.g., CDN altering payloads).
- **Middleware interference** (e.g., Spring Security misconfigurations).