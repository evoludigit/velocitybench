# **Debugging Hashing Integration: A Troubleshooting Guide**

## **1. Title**
**Debugging Hashing Integration: A Troubleshooting Guide**
*A Practical Guide for Backend Engineers*

---

## **2. Symptom Checklist**
Before diving into debugging, verify the following symptoms to narrow down the issue:

### **Client-Side Issues**
- [ ] **Authentication Failures**
  - `401 Unauthorized` or `403 Forbidden` responses when logging in.
  - Missing or malformed `Authorization` headers.
- [ ] **Incorrect Hash Verification**
  - Login succeeds but fails after subsequent requests (session mismatch).
  - Password reset tokens not working.
- [ ] **Hash Mismatch Errors**
  - `Invalid hash` or `Hash mismatch` in logs (e.g., from `bcrypt`, `Argon2`, or `SHA-256`).
- [ ] **Slow Hashing Performance**
  - Login delays due to expensive hashing algorithms (e.g., Argon2 with high iterations).
- [ ] **Browser-Side Hashing Issues**
  - JavaScript hashing (e.g., `SHA-1` in legacy systems) not matching server-side hashes.

### **Server-Side Issues**
- [ ] **Database Stored Hashes Don’t Match**
  - Newly hashed passwords fail verification.
  - Salt mismatches (if using salted hashes).
- [ ] **Race Conditions in Hash Updates**
  - Concurrent password changes corrupting stored hashes.
- [ ] **Environment Mismatch**
  - Development hashes work, but production fails (e.g., `pepper` differences).
- [ ] **Logging Missing Critical Hash Details**
  - No logs for failed hash comparisons (debugging hard).
- [ ] **Third-Party Hashing Service Failures**
  - OAuth tokens or session tokens not hashing correctly (e.g., Firebase Auth, AWS Cognito).

### **Infrastructure & Configuration**
- [ ] **Hashing Algorithm Changes Break Compatibility**
  - Switching from `bcrypt` to `Argon2` without migration.
- [ ] **Database Schema Mismatch**
  - Old entries use plaintext passwords, new ones use hashes.
- [ ] **Clock Skew Issues**
  - JWT/refresh token expiration hashes failing due to time misalignment.
- [ ] **Load Balancer or Proxy Modifying Headers**
  - `Authorization` header truncated or altered.

---
## **3. Common Issues & Fixes (With Code)**

### **Issue 1: Hash Verification Fails (Wrong Hashing Algorithm or Salt)**
**Symptoms:**
- `bcrypt.compare()` returns `false` even with correct password.
- `Argon2` fails with `Argon2Error: Invalid hash`.

**Root Cause:**
- Wrong algorithm used during password reset.
- Salt not stored or mismatched.
- Environment variables for hashing config differ.

**Fix (Node.js Example):**
```javascript
// Wrong: Using SHA-1 (vulnerable) instead of bcrypt
const wrongHash = require('crypto').createHash('sha1').update('password').digest('hex');

// Correct: Using bcrypt with salt
const bcrypt = require('bcrypt');
const saltRounds = 10;
const hashedPassword = await bcrypt.hash('password', saltRounds);

// Verify
const isMatch = await bcrypt.compare('password', storedHash); // Should be true
```

**Prevention:**
- Always use **bcrypt, Argon2, or PBKDF2** (never SHA-1/SHA-256 directly).
- Store **salt** alongside the hash in the database.

---

### **Issue 2: Slow Hashing Performance (Login Delays)**
**Symptoms:**
- API response time spikes during login.
- `bcrypt` taking >500ms to hash.

**Root Cause:**
- Too many iterations (`bcrypt` default is 10, but 12+ is recommended for security).
- Missing caching (re-hashing same password repeatedly).

**Fix:**
```javascript
// Optimize bcrypt iterations (balance security & speed)
const hashed = await bcrypt.hash('password', 12); // 12 rounds (secure but faster than 14+)

// Cache hashes if possible (e.g., Redis for repeated requests)
```

**Prevention:**
- Benchmark hashing latency in production.
- Use **worker pools** for async hashing.

---

### **Issue 3: JWT/Token Hashing Mismatch**
**Symptoms:**
- `InvalidSignatureError` when validating tokens.
- Refresh tokens not working after token rotation.

**Root Cause:**
- **Secret key mismatch** between signing and verification.
- **Peppers/secrets** changed but not updated in all environments.
- **Clock skew** causing expired tokens.

**Fix (Node.js Example):**
```javascript
const jwt = require('jsonwebtoken');

// Wrong: Using different secret in verification
const token = jwt.sign({ userId: 1 }, 'wrong-secret');
jwt.verify(token, 'correct-secret'); // Fails

// Correct: Use same secret
const secret = process.env.JWT_SECRET;
const token = jwt.sign({ userId: 1 }, secret);
jwt.verify(token, secret); // Works
```

**Prevention:**
- **Never hardcode secrets** (use `.env` + CI/CD secrets).
- **Rotate secrets** gradually (avoid breaking all sessions at once).

---

### **Issue 4: Database Hash Mismatch (Legacy vs. New Code)**
**Symptoms:**
- Old users login fine, new users fail.
- Mixed hashing algorithms in the same table.

**Root Cause:**
- New code uses `bcrypt`, but old entries use plaintext.
- Schema migration didn’t update hashes.

**Fix (SQL Migration Example):**
```sql
-- Step 1: Add a new column for hashes (if not exists)
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);

-- Step 2: Update old entries (if plaintext)
UPDATE users SET password_hash = bcrypt_hash(password);

-- Step 3: Update app logic to check both fields
```

**Prevention:**
- **Version migration scripts** for hashing upgrades.
- **Feature flag** for gradual rollout.

---

### **Issue 5: Salt Not Stored or Mismatched**
**Symptoms:**
- Hash works once, then fails on subsequent logins.
- `bcrypt` throws `Error: Invalid salt`.

**Root Cause:**
- Salt **not stored** in the database.
- Salt **generated per-user but lost during updates**.

**Fix (Example with Salt):**
```javascript
// Wrong: No salt storage
const hash = bcrypt.hash('password', 10); // Loses salt info

// Correct: Store salt with hash
const salt = await bcrypt.genSalt(10);
const hash = await bcrypt.hash('password', salt);
```

**Prevention:**
- **Always store salt** with the hash (e.g., `SELECT hash, salt FROM users`).
- **Never recompute salt**—use the stored one.

---

## **4. Debugging Tools & Techniques**

### **A. Logging & Instrumentation**
- **Log hash comparison results** (success/failure):
  ```javascript
  try {
    const match = await bcrypt.compare(password, storedHash);
    console.log(`Hash match: ${match}`);
  } catch (err) {
    console.error('Hash verification failed:', err);
  }
  ```
- **Check stored vs. computed hashes** (for debugging only—**never log raw passwords!**):
  ```javascript
  console.log(`Stored hash: ${storedHash}`);
  console.log(`Computed hash: ${await bcrypt.hash('password', salt)}`);
  ```

### **B. Security Auditing Tools**
- **Hashcat** (GPU-based brute-force test):
  ```bash
  hashcat -m 3200 hashed_passwords.txt rockyou.txt  # Test bcrypt hashes
  ```
- **John the Ripper** (CPU-based):
  ```bash
  john --format=bcrypt hashed_passwords.txt
  ```
- **OWASP ZAP** (for JWT token validation issues).

### **C. Performance Profiling**
- **Measure hashing latency**:
  ```bash
  ab -n 1000 -c 100 http://your-api/login  # ApacheBench for load testing
  ```
- **Use `console.time()` in Node.js**:
  ```javascript
  console.time('hashing');
  await bcrypt.hash('password', 10);
  console.timeEnd('hashing'); // Should be <100ms for bcrypt
  ```

### **D. Database Inspection**
- **Verify stored hashes**:
  ```sql
  SELECT password_hash FROM users WHERE id = 1;
  ```
- **Check for NULL salts**:
  ```sql
  SELECT COUNT(*) FROM users WHERE salt IS NULL;
  ```

---

## **5. Prevention Strategies**

### **A. Hashing Best Practices**
| **Recommendation** | **Why?** |
|--------------------|----------|
| Use **bcrypt (12+ rounds)** or **Argon2** | Resistant to brute force. |
| **Never** use SHA-1/SHA-256 directly | Too fast (vulnerable to rainbow tables). |
| **Store salts** with hashes | Needed for verification. |
| **Rotate secrets gradually** | Avoid breaking all sessions. |
| **Use HTTPS** | Prevent MITM attacks on hashing. |

### **B. Code & Infrastructure**
- **Environment Separation**:
  - `JWT_SECRET` should **never** be the same across dev, staging, prod.
- **Automated Testing**:
  ```javascript
  // Test hash verification
  it('should verify correct password', async () => {
    const salt = await bcrypt.genSalt(10);
    const hash = await bcrypt.hash('test123', salt);
    const match = await bcrypt.compare('test123', hash);
    expect(match).toBe(true);
  });
  ```
- **Feature Flags for Hashing Upgrades**:
  ```javascript
  const useNewHashing = process.env.USE_NEW_HASHING === 'true';
  const hashPassword = useNewHashing ? hashWithArgon2 : bcryptHash;
  ```

### **C. Monitoring & Alerts**
- **Set up alerts** for:
  - High latency in hashing operations.
  - Failed hash verifications (anomaly detection).
- **Example Prometheus Alert**:
  ```yaml
  - alert: HighHashingLatency
    expr: rate(hash_operation_duration_seconds{status="error"}[5m]) > 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Hashing operation failed"
  ```

### **D. Disaster Recovery Plan**
- **Backup hashes** before major migrations.
- **Document hashing schemes** (e.g., "All users before 2023 use SHA-256, post-2023 use bcrypt").
- **Test rollback** if a new hashing method breaks authentication.

---
## **Final Checklist for Hashing Issues**
| **Step** | **Action** |
|----------|------------|
| 1. | Verify **client-side** hashing matches server. |
| 2. | Check **database** for correct salt/hash storage. |
| 3. | Test with **logging** to compare hashes. |
| 4. | Benchmark **hashing performance**. |
| 5. | Rotate **secrets/peppers** safely. |
| 6. | Audit **old vs. new hashes** in the database. |

---
**Next Steps:**
- If the issue persists, **reproduce in a staging environment** with the same configs.
- **Isolate the problem** (client vs. server vs. database).
- **Engage the team** if it’s a shared dependency (e.g., OAuth provider).

---
This guide focuses on **practical, actionable steps** to resolve hashing issues quickly. Always **balance security and performance**—never sacrifice one for the other arbitrarily.