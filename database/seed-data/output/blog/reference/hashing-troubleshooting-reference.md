# **[Pattern] Hashing Troubleshooting – Reference Guide**

---
## **Overview**
Hashing is a critical process for data integrity, authentication, and security, yet inconsistencies—such as mismatched hashes, incorrect salt handling, or performance bottlenecks—can disrupt applications. This reference guide provides structured troubleshooting steps, schema references, and best practices to diagnose and resolve common hashing-related issues.

Key areas covered:
- Common hash collision and validation failures
- Salt-related errors (handling, leakage, or missing salts)
- Performance degradation in hash computations
- Cross-platform or environment inconsistencies
- Integration issues with APIs or databases

This guide assumes familiarity with hashing algorithms (SHA-256, bcrypt, Argon2, etc.), cryptographic libraries, and basic debugging techniques.

---

## **Key Concepts & Implementation Details**
### **1. Why Hashes Fail**
Hashes generate fixed-length outputs from input data (e.g., passwords, files). Failures typically stem from:

| **Root Cause**               | **Description**                                                                                     |
|------------------------------|-----------------------------------------------------------------------------------------------------|
| **Algorithm Mismatch**       | Using SHA-256 where bcrypt is expected (or vice versa)                                              |
| **Salt Issues**              | Missing, incorrect, or hardcoded salts; salt length mismatch                                         |
| **Data Modification**        | Input data changes (e.g., whitespace, case sensitivity, trimming)                                  |
| **Encoding/Decoding Errors** | Incorrect base64/hex encoding (e.g., `base64url` vs. `base64`)                                     |
| **Race Conditions**          | Concurrent hash computations leading to stale or duplicate results                                   |
| **Environment Variability**  | Differences in platform libraries (e.g., OpenSSL vs. libsodium)                                     |
| **API/API Errors**           | Network failures or malformed responses in external hash services                                   |

### **2. Common Hashing Libraries & Standards**
| **Algorithm**  | **Purpose**                          | **Library Examples**                          | **Key Considerations**                                                                 |
|----------------|---------------------------------------|-----------------------------------------------|---------------------------------------------------------------------------------------|
| **SHA-256**    | Data integrity, file checks           | OpenSSL, Python’s `hashlib`                  | Fast but **not secure for passwords**; vulnerable to brute-force attacks.                |
| **bcrypt**     | Secure password hashing               | `bcrypt` (Node.js), `bcrypt` (Python), PHP’s `password_hash()` | **Salted**, adjustable cost factor (work factor). **Recommended for passwords**.       |
| **Argon2**     | Memory-hard hashing (post-KDF)        | `Argon2id`, `libsodium`                       | Resistant to GPU/ASIC attacks; **preferred over bcrypt for high-security needs**.    |
| **PBKDF2**     | Legacy password hashing               | `PBKDF2` (Node.js), `bcrypt` (Python)        | Requires a **salt** and iteration count; less performant than Argon2.                    |
| **HMAC-SHA256**| Message authentication               | `HMAC` (Python/Node.js)                      | **Key-dependent**; used with secrets or tokens.                                        |

---

## **Schema Reference**
### **1. Hash Validation Schema**
Used to validate stored hashes against new inputs (e.g., passwords).

```json
{
  "schema": "hash_validation_v1",
  "properties": {
    "algorithm": { "type": "string", "enum": ["bcrypt", "argon2id", "sha256", "pbkdf2"], "required": true },
    "hash": { "type": "string", "format": "byte", "required": true },
    "salt": { "type": "string", "format": "byte", "nullable": true },
    "costFactor": { "type": "integer", "minimum": 4, "maximum": 31, "nullable": true }, // bcrypt
    "memory": { "type": "integer", "minimum": 65536, "nullable": true },                 // Argon2
    "iterations": { "type": "integer", "minimum": 1000, "nullable": true }               // PBKDF2
  },
  "required": ["algorithm", "hash"]
}
```

### **2. Hash Storage Schema**
Best practices for storing hashes securely.

| **Field**       | **Type**       | **Description**                                                                                     | **Example Values**                          |
|-----------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------------|
| `algorithm`     | String         | Hashing algorithm used.                                                                               | `"bcrypt"`, `"argon2id"`                    |
| `salt`          | Binary/HEX     | Random salt (base64url-encoded or HEX). Must be **unique per entry**.                                | `"base64:JDhK..."` or `"hex:5f4dcc3b..."`   |
| `hash`          | Binary/HEX     | The generated hash.                                                                                   | `"hash:2y$10$..."` (bcrypt) or `"hash:..."` |
| `costFactor`    | Integer        | Work factor for bcrypt (recommended: **10–12**).                                                     | `12`                                        |
| `lastUpdated`   | ISO 8601       | Timestamp of last hash update (for rotation).                                                        | `"2023-10-01T12:00:00Z"`                     |

---
## **Query Examples**
### **1. Validate a Stored Hash (Password Example)**
**Scenario**: User submits `password123`; verify against stored `bcrypt` hash.

#### **Input**
```json
{
  "algorithm": "bcrypt",
  "hash": "$2a$12$N9qo8uLOq7XQb8ZMYZ4Pme",
  "salt": "base64:N9qo8uLOq7XQb8ZMYZ4Pme",
  "input": "password123"
}
```

#### **Command (Node.js)**
```javascript
const bcrypt = require('bcrypt');

async function validatePassword(input, storedHash) {
  try {
    const match = await bcrypt.compare(input, storedHash);
    return { success: match, message: match ? "Valid" : "Invalid" };
  } catch (error) {
    return { success: false, error: error.message };
  }
}
```

#### **Expected Output**
```json
{
  "success": true,
  "message": "Valid"
}
```

---
### **2. Detect Hash Collisions (SHA-256)**
**Scenario**: Two different inputs generate the same SHA-256 hash (extremely rare but possible).

#### **Input**
```python
import hashlib

def detect_collision(input1, input2):
    hash1 = hashlib.sha256(input1.encode()).hexdigest()
    hash2 = hashlib.sha256(input2.encode()).hexdigest()
    return hash1 == hash2
```

#### **Output**
```json
{
  "collision": false,
  "hash1": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
  "hash2": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---
### **3. Troubleshoot Missing Salts**
**Scenario**: Database stores hashes without salts (bcrypt/PBKDF2).

#### **Diagnosis Steps**
1. Query the database for hashes without a `salt` column.
2. Example SQL:
   ```sql
   SELECT * FROM user_accounts
   WHERE salt IS NULL OR salt = '';
   ```
3. **Fix**: Regenerate hashes with unique salts using the user’s input.

#### **Regeneration (Python Example)**
```python
import bcrypt
import os

def regenerate_hash(input_password):
    salt = bcrypt.gensalt(rounds=12).decode()
    hashed = bcrypt.hashpw(input_password.encode(), salt.encode())
    return {"salt": salt, "hash": hashed.decode()}
```

---
### **4. Cross-Environment Comparison**
**Scenario**: Hashes generated in `Node.js` (OpenSSL) don’t match those in `Python` (libsodium).

#### **Diagnosis Table**
| **Library**       | **Algorithm** | **Default Output Encoding** | **Fix**                                  |
|-------------------|---------------|-----------------------------|------------------------------------------|
| Node.js (OpenSSL) | bcrypt        | `$2a$cost$salt$hash`        | Use `bcrypt.hash()` with explicit salt. |
| Python (libsodium)| Argon2        | Raw bytes                   | Encode output as `base64url`.            |
| PHP              | Password_hash | `algorithm$cost$salt$hash`  | Use `password_hash()` with `PASSWORD_BCRYPT`. |

#### **Solution (Normalize Output)**
```bash
# Node.js (OpenSSL) → Python (libsodium)
node -e "console.log(require('bcrypt').hashSync('password', 12))" | python3 -c "
import sys; import base64; hash = sys.stdin.read().strip(); print(base64.b64encode(hash.encode()).decode())
"
```

---
## **Common Error Messages & Fixes**
| **Error**                                      | **Root Cause**                          | **Solution**                                                                 |
|-------------------------------------------------|------------------------------------------|------------------------------------------------------------------------------|
| `"Invalid hash format"`                        | Wrong algorithm or corrupt salt         | Re-generate hash with correct parameters.                                   |
| `"Cost factor too low"`                        | bcrypt work factor < 4                   | Increase `costFactor` (recommended: **10+**).                                |
| `"HMAC mismatch"`                              | Key or input data differs               | Verify HMAC key and original input.                                          |
| `"Argon2 memory limit exceeded"`               | Insufficient memory allocation          | Reduce `memory` parameter or upgrade hardware.                               |
| `"Hash collision detected"`                    | Rare but possible with SHA-256          | Use a stronger algorithm (Argon2, bcrypt).                                   |
| `"Salt too short"`                             | Salt length < 16 bytes                   | Generate a new salt with `crypto.randomBytes(16)`.                           |

---

## **Related Patterns**
1. **[Secure Password Storage](https://example.com/patterns/password-storage)**
   - Complements this pattern by detailing salt management and key derivation.

2. **[Cryptographic Token Validation](https://example.com/patterns/token-validation)**
   - Explores HMAC-SHA256 for JWT or API tokens.

3. **[Performance Optimization for Hashing](https://example.com/patterns/async-hashing)**
   - Discusses parallelizing hash computations (e.g., using Web Workers).

4. **[Handling Hash Leakage](https://example.com/patterns/hash-leakage)**
   - Strategies for mitigating breaches (e.g., rainbow tables, rate limiting).

5. **[Cross-Language Hashing Compatibility](https://example.com/patterns/cross-lang-hashing)**
   - Ensures hash consistency across Python, Node.js, Java, etc.

---
## **Further Reading**
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [Argon2 Documentation](https://argon2.net/)
- [BCrypt Specification](https://github.com/atom/bcrypt-rfc)