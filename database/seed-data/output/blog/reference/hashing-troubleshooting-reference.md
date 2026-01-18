# **[Pattern] Hashing Troubleshooting – Reference Guide**

---

## **Overview**
Hashing is a critical component of data integrity, authentication, and security, but issues like collisions, incorrect hashing algorithms, or improper handling can introduce vulnerabilities or data inconsistencies. This guide provides a structured approach to diagnosing and resolving common hashing-related problems in applications. It covers validation techniques, algorithm selection, and practical troubleshooting steps for hashes in databases, APIs, and authentication systems.

---

## **Key Concepts**
| Term                | Definition                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| **Hash Collision**  | Two different inputs producing the same hash (mitigated via strong algorithms like SHA-3). |
| **Salt**            | Random data added to input to prevent rainbow table attacks.                 |
| **Hashing Algorithm** | Function converting input to a fixed-length hash (e.g., MD5, SHA-256).     |
| **Hash Length**     | Bit-size of the hash output (e.g., 256-bit SHA-256).                      |

---

## **Troubleshooting Workflow**

### **1. Identify the Problem**
#### **Common Issues**
- **Hash Mismatches**: Unauthorized data alteration or incorrect comparison.
- **Performance Bottlenecks**: Slow hashing due to weak algorithms or unsalted inputs.
- **Security Vulnerabilities**: Weak algorithms (e.g., MD5, SHA-1) or no salting.

#### **Symptoms**
| Symptom                     | Likely Cause                                      |
|-----------------------------|---------------------------------------------------|
| Verification fails         | Incorrect hash generation or storage.              |
| Slow authentication         | Inefficient algorithm (e.g., MD5).                 |
| Known vulnerabilities      | Outdated or weak algorithm (CVE-2017-14164, etc.). |

---

### **2. Validation Steps**
#### **Check Algorithm Compatibility**
| Algorithm      | Security Level | Recommendation               |
|----------------|----------------|-----------------------------|
| MD5            | Low            | Avoid (pre-2012).             |
| SHA-1          | Low            | Avoid (pre-2017).             |
| SHA-256        | High           | Preferred for most use cases.|
| SHA-3          | High           | Future-proof alternative.    |

**Best Practice**:
```python
import hashlib
def generate_hash(input_data: str, salt: str = "", algorithm: str = "sha256") -> str:
    hasher = hashlib.new(algorithm)
    if salt:
        hasher.update(salt.encode())
    hasher.update(input_data.encode())
    return hasher.hexdigest()
```

#### **Verify Salting**
- **Static Salt**: Use a fixed salt (e.g., `app.secret_key`) for consistency but avoid hardcoding.
- **Dynamic Salt**: Generate per record (store salt alongside hash).
- **No Salt**: Vulnerable to precomputed attacks (e.g., rainbow tables).

**Example Salt Handling**:
```sql
-- Database schema with salt
CREATE TABLE users (
    id INT PRIMARY KEY,
    password_hash VARCHAR(64),
    salt VARCHAR(32)
);
```

---

### **3. Debugging Hash Mismatches**
| Scenario                          | Root Cause                          | Solution                                |
|-----------------------------------|-------------------------------------|-----------------------------------------|
| Hash A ≠ Hash B (same input)      | Algorithm mismatch, wrong salt.     | Re-generate hash with same parameters.  |
| Length mismatch                   | Output format (hex vs. binary).     | Ensure consistent encoding (e.g., `hexdigest()`). |
| Time-based inconsistency          | Leaky encryption or race conditions.| Use atomic operations or retry logic. |

**Debugging Command**:
```bash
# Compare two hashes interactively
echo -n "input_data" | sha256sum --stdin  # Linux
```

---

### **4. Performance Optimization**
| Issue                | Solution                          |
|----------------------|-----------------------------------|
| Slow hashing         | Use hardware acceleration (e.g., `openssl speed`). |
| Bottleneck in bulk   | Parallelize with threads/processes. |
| Unnecessary rehashes | Cache hashes (e.g., Redis) for frequent inputs. |

**Benchmarking**:
```bash
# Compare algorithm speeds
openssl speed -evp sha256 -evp sha3-256
```

---

### **5. Security Audits**
#### **Vulnerability Checks**
- **Outdated Libraries**: Update `bcrypt`, `Argon2`, or `PBKDF2`.
- **Weak Hashes in Storage**: Audit databases for `SHA-1` hashes.
- **Side-Channel Attacks**: Use constant-time comparison (e.g., `hmac.compare_digest`).

**Example Secure Comparison**:
```python
import hmac
def verify_hash(stored_hash: str, input_data: str, salt: str) -> bool:
    computed_hash = generate_hash(input_data, salt)
    return hmac.compare_digest(stored_hash, computed_hash)
```

---

## **Schema Reference**
| Component       | Description                                                                 | Example Value               |
|-----------------|-----------------------------------------------------------------------------|-----------------------------|
| **Hash Algorithm** | Determines hash strength (SHA-256, Argon2).                                              | `sha256`                    |
| **Salt**        | Random string appended to input (min 32 bytes).                                           | `salt=0xAEf3...`            |
| **Hash Length** | Bit-size of output (e.g., 256 for SHA-256).                                          | `256`                       |
| **Iterations**  | Key stretching rounds (e.g., Argon2’s `m_cost`).                                    | `3` (low) / `19` (high)     |

**Database Schema Example**:
```sql
ALTER TABLE user_credentials ADD COLUMN
    security_hash VARCHAR(64) NOT NULL,
    salt VARCHAR(32) NOT NULL DEFAULT (gen_salt()); -- Hypothetical function
```

---

## **Query Examples**
### **1. Find Weakly Hashed Records**
```sql
-- Identify SHA-1 hashes (vulnerable)
SELECT id, security_hash
FROM user_credentials
WHERE LENGTH(security_hash) = 40 AND
      SUBSTRING(security_hash, 1, 4) = '5e8'; -- SHA-1 prefix
```

### **2. Verify Hash Integrity**
```python
# Python: Verify stored password hash
def check_password(stored_hash: str, input_password: str, stored_salt: str) -> bool:
    new_hash = generate_hash(input_password, stored_salt, "sha256")
    return hmac.compare_digest(stored_hash, new_hash)
```

### **3. Rehash Old Records**
```sql
-- Rehash SHA-1 to SHA-256 (batch job)
UPDATE user_credentials
SET security_hash = generate_hash(
    password || salt,
    'sha256',
    salt
)
WHERE SUBSTRING(security_hash, 1, 4) = '5e8';
```

---

## **Related Patterns**
1. **Secure Authentication**
   - Use **Argon2** or **PBKDF2** for password storage (see [Secure Storage Pattern](link)).
2. **Data Integrity**
   - Combine hashing with **HMAC** for message authenticity.
3. **Distributed Systems**
   - Use **consistent hashing** (e.g., for cache distribution).
4. **Cryptographic Key Management**
   - Rotate keys periodically (apply to hash salts).

---
**Key Resources**:
- [NIST SP 800-131A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131A.pdf) (Hashing Standards)
- [OWASP Hashing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Hashing_Cheat_Sheet.html)