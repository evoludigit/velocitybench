# **Debugging Hashing Algorithms: A Troubleshooting Guide**

Hash functions play a critical role in security, data integrity, caching, and indexing. When hashing-related issues arise, they can lead to:
- Authentication failures
- Database corruption
- Cache inconsistencies
- Security vulnerabilities (e.g., rainbow table attacks)
- Performance bottlenecks in distributed systems

This guide provides a structured approach to diagnosing and resolving common hashing issues efficiently.

---

## **1. Symptom Checklist**
Before diving into debugging, identify which symptoms match your issue:

| **Symptom**                          | **Possible Cause**                          | **Impact**                          |
|--------------------------------------|---------------------------------------------|-------------------------------------|
| Authentication fails (`401 Unauthorized`) | Incorrect password hashing format or salt | Security breach risk               |
| Database records not matching expected hashes | Data corruption, wrong hashing algorithm  | Accuracy issues                     |
| Cache performance degradation         | Hash collisions in distributed systems      | Slow response times                 |
| Security audit flags suspicious hashes | Weak algorithms or improper salting        | Vulnerability to attacks            |
| API responses vary across environments | Environment variables (e.g., `HASH_ALGO`) misconfigured | Inconsistent behavior              |
| Memory leaks in high-frequency hashing | Inefficient hashing library usage          | System instability                  |

**Next Step:**
If multiple symptoms occur, check logs for **hash failure timestamps** and examine affected components (auth, DB, cache).

---

## **2. Common Issues and Fixes**

### **A. Authentication Failures Due to Hash Mismatches**
**Symptom:**
Users log in successfully in staging but fail in production with:
```bash
Hash of input password does not match stored hash.
```

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Code Example** |
|-------------------------------------|--------------------------------------------------------------------------|------------------|
| **Hashing algorithm mismatch**      | Ensure consistent algorithm (e.g., `bcrypt`, `Argon2`).                   | `require('bcrypt').hashSync(password, salt)` |
| **Salt not stored**                 | Store salt with the hash (e.g., in DB).                                  | `hash: "$2a$10$xyzsalt$hashedpassword"` |
| **Incorrect salt generation**       | Use a random, unique salt per password.                                  | `const salt = await bcrypt.genSalt(12);` |
| **Input sanitization issues**       | Trim whitespace, normalize case before hashing.                         | `const cleanPassword = password.trim().toLowerCase();` |
| **Environment variable mismatch**   | Check `HASH_ALGO` in `config.js` vs. deployment.                          | `process.env.HASH_ALGO === 'bcrypt'` |

**Debugging Steps:**
1. **Dump hashes** from DB and compare with computed hashes:
   ```javascript
   const storedHash = await bcrypt.compare(password, user.passwordHash);
   console.log({ storedHash, computedHash: bcrypt.hashSync(password, salt) });
   ```
2. **Check salt storage**:
   ```sql
   SELECT password_hash FROM users WHERE email = 'user@example.com';
   ```
   Ensure it’s a string like `$2a$10$salt$hash...`.

---

### **B. Hash Collisions in Distributed Caches**
**Symptom:**
High cache miss rate despite consistent key generation.

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Code Example** |
|-------------------------------------|--------------------------------------------------------------------------|------------------|
| **Same key generates different hashes** | Ensure deterministic output (e.g., use `SHA-256`).                 | `const hash = sha256Sync(key + secretSalt);` |
| **Race conditions in key building** | Use atomic operations for key construction.                            | `const key = await Promise.all([getUserId(), getTimestamp()]);` |
| **Custom hashing logic errors**     | Test edge cases (e.g., null/undefined values).                          | `if (!key) throw new Error('Invalid key');` |

**Debugging Steps:**
1. **Log generated keys and hashes**:
   ```javascript
   const cacheKey = `user:${userId}:${timestamp}:${sha256Sync(key)}`;
   console.log(cacheKey);
   ```
2. **Verify collision frequency**:
   ```bash
   grep "Collision" access.log | wc -l
   ```
3. **Benchmark hashing**:
   ```javascript
   const start = Date.now();
   for (let i = 0; i < 10000; i++) sha256Sync(`key_${i}`);
   console.log(`Time: ${Date.now() - start}ms`);
   ```

---

### **C. Security Vulnerabilities (Weak Algorithms)**
**Symptom:**
Security scanner flags:
- "BCrypt round count too low (e.g., 4 instead of 12)"
- "No salt detected"

#### **Root Causes & Fixes**
| **Cause**                          | **Fix**                                                                 | **Code Example** |
|-------------------------------------|--------------------------------------------------------------------------|------------------|
| **Legacy algorithms (MD5/SHA-1)**   | Migrate to `bcrypt`, `Argon2`, or `PBKDF2`.                              | `const hash = await bcrypt.hash(password, 12);` |
| **Forgotten salting**               | Always generate and store salt.                                           | `const salt = bcrypt.genSaltSync(12);` |
| **Hardcoded salts**                 | Avoid fixed salts; use per-user salts.                                    | `user.salt = randomBytes(16).toString('hex');` |

**Debugging Steps:**
1. **Audit existing hashes**:
   ```javascript
   const users = await User.findAll();
   users.forEach(user => {
     if (user.passwordHash.startsWith('$1')) {
       console.warn('Weak hash detected:', user.passwordHash);
     }
   });
   ```
2. **Test against rainbow tables**:
   ```bash
   hashcat -m 2500 hashed_password.txt /usr/share/wordlists/rockyou.txt
   ```

---

## **3. Debugging Tools and Techniques**

### **A. Logging & Monitoring**
- **Hash Comparison Utilities**:
  - **Hashcat**: Test weak hashes (`hashcat -m 2500 hashed_password.txt --show`).
  - **John the Ripper**: `john --wordlist=/usr/share/wordlists/rockyou.txt hashfile.txt`.
- **Logging**:
  ```javascript
  logger.info(`Hashing attempt: ${userId} | Algorithm: ${algorithm} | Time: ${Date.now()}`);
  ```

### **B. Unit Testing Hash Logic**
```javascript
const assert = require('assert');
const bcrypt = require('bcrypt');

test('Hash consistency', async () => {
  const password = 'secure123';
  const hash1 = await bcrypt.hash(password, 12);
  const hash2 = await bcrypt.hash(password, 12);
  assert.notEqual(hash1, hash2); // Different salts
  assert(bcrypt.compare(password, hash1)); // Match
});
```

### **C. Database Integrity Checks**
```sql
-- Verify no corrupted hashes
SELECT COUNT(*) FROM users
WHERE password_hash NOT REGEXP '^\$2a\$1[0-9]\$[a-zA-Z0-9./]{22}';
```

### **D. Performance Profiling**
- **Identify slow hashes**:
  ```javascript
  console.time('hashing');
  for (let i = 0; i < 1000; i++) bcrypt.hash('test', 12);
  console.timeEnd('hashing');
  ```
- **Use `perf` (Linux)**:
  ```bash
  perf stat -e cycles node server.js
  ```

---

## **4. Prevention Strategies**

### **A. Enforce Standards**
- **Algorithm Policy**: Use only `bcrypt`, `Argon2`, or `PBKDF2` (never MD5/SHA-1).
- **Salt Requirements**:
  - 128-bit salts (`randomBytes(16)`).
  - Store salt with the hash (e.g., PostgreSQL `pgcrypto` extension).

### **B. Secure Defaults**
- **Environment Variables**:
  ```env
  DEFAULT_HASH_ALGO=bcrypt
  DEFAULT_HASH_ROUNDS=12
  ```
- **Input Validation**:
  ```javascript
  if (!isStrongPassword(password)) {
    throw new Error('Password too weak');
  }
  ```

### **C. Automated Testing**
- **Pre-commit hooks** to validate hashing:
  ```javascript
  // .husky/pre-commit.js
  const { testHashConsistency } = require('./hashTests');
  testHashConsistency().catch(console.error);
  ```

### **D. Regular Audits**
- **Hash Strength Scanner**:
  ```bash
  node scripts/audit-hashes.js --db-uri=postgres://user:pass@localhost/users
  ```
- **Dependency Updates**:
  ```bash
  npm audit fix --force
  ```

---

## **5. Quick Reference Table**
| **Issue**               | **Check**                          | **Fix**                          | **Verification**                     |
|--------------------------|-------------------------------------|-----------------------------------|---------------------------------------|
| Auth failure             | `bcrypt.compare()` failure          | Re-hash passwords with salt        | Test login in all environments         |
| Cache collisions         | Duplicate keys                      | Use deterministic hashing         | Monitor cache metrics                 |
| Weak hashes              | `hashcat` detects old algo          | Migrate to `bcrypt`/`Argon2`      | Run security audit                    |
| Slow hashing             | High CPU usage                     | Optimize rounds (e.g., 10 instead of 12 if acceptable) | Benchmark with `perf` |

---

## **Final Checklist Before Production**
1. [ ] All passwords are hashed with **`bcrypt`/`Argon2`** (rounds: ≥10).
2. [ ] Salts are **random, 128-bit**, and stored with hashes.
3. [ ] Hash algorithms are **environment-agnostic** (no dev/prod mismatches).
4. [ ] **Unit tests** cover edge cases (empty inputs, Unicode, length limits).
5. [ ] **Security scans** (OWASP ZAP, Hashcat) pass for existing hashes.

---
**Example Fix for a Broken Auth System**:
```javascript
// Before (broken)
const user = await User.findOne({ where: { email: 'admin@example.com' } });
const valid = user.password === bcrypt.hashSync(password, 10); // ❌ Wrong!

// After (fixed)
const valid = await bcrypt.compare(password, user.passwordHash); // ✅ Correct
```

By following this guide, you’ll resolve hashing issues systematically while hardening your system against future problems.