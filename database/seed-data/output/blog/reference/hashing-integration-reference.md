---

**[Pattern] Hashing Integration Reference Guide**
*Securely integrate cryptographic hashing into applications for data integrity, authentication, and deduplication.*

---

## **Overview**
This reference provides technical guidance for implementing **Hashing Integration**, a security pattern used to:
- Verify data integrity via **hash comparison**.
- Securely store and compare sensitive data (e.g., passwords, fingerprints) without exposing raw values.
- Enable **efficient deduplication** (e.g., caching, logs) via consistent hash representation.
- Comply with security standards like **OWASP** (password storage) or **PII anonymization**.

The pattern combines **hashing algorithms** (e.g., SHA-256, bcrypt) with application logic to generate, compare, and store hashes. Key trade-offs include **collision resistance** (algorithm choice), **computational overhead** (e.g., bcrypt’s salting), and **reverse-engineering risks** (plaintext exposure during processing).

---

## **1. Key Concepts**
| Concept               | Description                                                                                                                                                                                                 | Example                                                                                     |
|-----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| **Hashing Algorithm** | A one-way function transforming input data into a fixed-size string (e.g., SHA-3, Argon2). Must resist collisions (same input → different output) and reverse-calculation. | SHA-256: `"password123"` → `"5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"` |
| **Salt**              | Random data appended to input to prevent rainbow-table attacks. Critical for password hashing.                                                                                                            | `bcrypt`: `"$2a$12$N9qo8u9xQJQvr6Y.."` (salt embedded in hash)                               |
| **Hash Comparison**   | Verifies input matches a stored hash (e.g., comparing hashed passwords). **Never compare plaintext hashes directly.**                                                                                     | Python: `bcrypt.checkpw(user_input, stored_hash)`                                             |
| **Deterministic Hashes** | Same input → same output (e.g., SHA-256). Useful for deduplication but **not** for passwords (use salts).                                                                                              | SHA-256 of `"user@domain.com"` → always `0x7a45...`                                           |
| **Key Stretching**    | Slows down hash calculation to resist brute-force attacks (e.g., bcrypt, PBKDF2). Trade-off: higher CPU usage for security.                                                                        | bcrypt: 2¹² iterations by default (adjustable)                                               |
| **Hash Length**       | Longer hashes (e.g., 512-bit SHA-2) reduce collision probability but increase storage/bandwidth.                                                                                                         | SHA-512: 64-character hex output                                                             |

---

## **2. Schema Reference**
Below are common data structures for hashing integration.

### **2.1. Stored Hash Schema**
| Field       | Type     | Description                                                                                                                                                                                                 | Example (bcrypt)                                                                           |
|-------------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| `hash`      | String   | The computed hash (including salt for passwords). **Never store plaintext.**                                                                                                                             | `"$2a$10$N9qo8u9xQJQvr6Y...uLx"`                                                            |
| `algorithm` | String   | Specifies the hashing algorithm (e.g., `bcrypt`, `argon2id`, `SHA-256`).                                                                                                                                | `"bcrypt"`                                                                                  |
| `salt`      | String   | The random salt (embedded in bcrypt/argon2 hashes; stored separately for SHA-256).                                                                                                                     | `"a1b2c3..."` (or omitted if algorithm handles it)                                         |
| `iterations`| Integer  | Key-stretching iterations (e.g., 10 for bcrypt). Higher = more secure but slower.                                                                                                                       | `10` (default for bcrypt)                                                                 |
| `timestamp` | Datetime | When the hash was created (audit trail).                                                                                                                                                               | `"2023-10-15T08:30:00Z"`                                                                   |
| `metadata`  | Object   | Additional context (e.g., `purpose: "password"`, `key_length: 64`).                                                                                                                              | `{"purpose": "password_hash", "key_length": 512}`                                          |

---

### **2.2. Hash Comparison Flow**
```mermaid
graph TD
    A[User Input] -->|Input| B{Deterministic?}
    B -->|Yes (SHA-256)| C[Generate Hash]
    B -->|No (Password)| D[Add Salt]
    D --> E[Apply Algorithm]
    C & E --> F[Compare with Stored Hash]
    F -->|Match| G[Allow Access]
    F -->|No Match| H[Reject Access]
```

---

## **3. Implementation Details**
### **3.1. Algorithm Selection**
| Use Case                  | Recommended Algorithm       | Why?                                                                                                                                                          | Libraries                                                                                     |
|---------------------------|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| **Password Storage**      | bcrypt, Argon2id, PBKDF2    | Resists brute-force and rainbow tables via salting/key stretching.                                                                                          | Python: `bcrypt`, `passlib`; Java: `PBKDF2WithHmacSHA256`                                  |
| **Data Integrity (PII)**  | SHA-256, SHA-3             | Fast, collision-resistant for checksums/logs. **Do not use for passwords.**                                                                              | Node.js: `crypto.createHash('sha256')`; Java: `MessageDigest`                              |
| **Deduplication**         | MurmurHash3, xxHash        | Extremely fast, consistent hashes for non-sensitive data (e.g., caching keys).                                                                           | Python: `murmurhash3`; Go: `xxHash`                                                        |
| **HMAC (Authentication)** | HMAC-SHA256/3              | Ensures data + secret integrity (e.g., API tokens).                                                                                                       | Node.js: `crypto.createHmac('sha256', secretKey)`                                          |

---

### **3.2. Password Hashing Example (bcrypt)**
#### **1. Generate Hash**
```python
import bcrypt

plain_password = "securePass123".encode('utf-8')
salt = bcrypt.gensalt(rounds=12)  # Adjust `rounds` for security/speed
hashed = bcrypt.hashpw(plain_password, salt)

# Stored: hashed = "$2a$12$N9qo8u9xQJQvr6Y...uLx"
```

#### **2. Verify Password**
```python
def verify_password(plain_pass: str, stored_hash: str) -> bool:
    return bcrypt.checkpw(plain_pass.encode('utf-8'), stored_hash.encode('utf-8'))
```

---
### **3.3. Integrity Check (SHA-256)**
```python
import hashlib

def generate_sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

# Example: Verify file integrity
file_hash = generate_sha256("user_data.txt")
if file_hash == stored_integrity_hash:
    print("Data is unchanged.")
```

---
### **3.4. Deduplication (MurmurHash3)**
```python
from murmurhash3 import murmurhash3

def cache_key(user_id: int) -> str:
    return murmurhash3(user_id, 32).hexdigest()  # 32-bit hash as hex
```

---

## **4. Query Examples**
### **4.1. SQL: Store Password Hash**
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- Stores bcrypt hash (e.g., "$2a$...")
    salt VARCHAR(100),                   -- Optional for algorithms needing explicit salts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert with bcrypt hash
INSERT INTO users (username, password_hash)
VALUES ('alice', bcrypt.hashpw('password', bcrypt.gensalt()));
```

### **4.2. API: Verify Hash (Node.js)**
```javascript
const crypto = require('crypto');

function verifySha256(input, storedHash) {
    const hash = crypto.createHash('sha256').update(input).digest('hex');
    return hash === storedHash;
}

// Usage
verifySha256("data_to_verify", "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e");
```

### **4.3. Cache Key Generation (Python)**
```python
from hashlib import sha1

def generate_cache_key(user_data: dict) -> str:
    # Combine fields deterministically (order matters!)
    data_str = "|".join(f"{k}:{v}" for k, v in sorted(user_data.items()))
    return sha1(data_str.encode()).hexdigest()

# Example: Cache key for {user_id: 42, session_token: "abc123"}
key = generate_cache_key({"user_id": 42, "session_token": "abc123"})
```

---

## **5. Security Considerations**
### **5.1. Pitfalls to Avoid**
| Risk                          | Mitigation                                                                                                                                                                                                 |
|-------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Storing plaintext hashes**  | Always store **hashed + salted** data. Never compare raw hashes.                                                                                                                                        |
| **Weak algorithms**          | Avoid **MD5**, **SHA-1**, or **SHA-256 without key stretching** for passwords. Use **bcrypt**, **Argon2**, or **PBKDF2**.                                                                          |
| **Fixed salts**               | Use **unique salts** per password (bcrypt/argon2 handle this automatically).                                                                                                                         |
| **Hardcoded salts**           | Never reuse salts across systems. Generate salts **per record**.                                                                                                                                    |
| **Collision attacks**         | Use **256-bit+ hashes** (SHA-256, SHA-3) for data integrity. For passwords, prioritize **key stretching** over hash length.                                                                         |
| **Timing attacks**            | Use **constant-time comparison** (e.g., `bcrypt.checkpw`, OpenSSL’s `HMAC_verify`).                                                                                                                  |

---
### **5.2. Performance Trade-offs**
| Algorithm       | Speed (Relative) | Security Level | Use Case                          |
|-----------------|------------------|-----------------|-----------------------------------|
| SHA-256         | Very Fast        | Medium          | Data integrity, non-password hashes |
| bcrypt          | Slow             | High            | Password storage                  |
| Argon2id        | Slow (but memory-hard) | Very High | Password storage (modern)         |
| MurmurHash3     | Instant          | Low             | Deduplication, caching            |

---
## **6. Query Examples (Extended)**
### **6.1. Update Password Hash (SQL)**
```sql
-- Step 1: Generate new hash and salt
INSERT INTO users (user_id, password_hash)
VALUES (
    42,
    bcrypt.hashpw('new_secure_password', bcrypt.gensalt())
)
WHERE username = 'alice';
```

### **6.2. Batch Integrity Check (Python)**
```python
import hashlib

def check_batch_integrity(file_paths: list[str], expected_hashes: dict[str, str]) -> dict[str, bool]:
    results = {}
    for file_path, expected_hash in expected_hashes.items():
        with open(file_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        results[file_path] = file_hash == expected_hash
    return results
```

---

## **7. Related Patterns**
| Pattern                          | Description                                                                                                                                                                                                 | When to Use                                                                                     |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **[Password Storage Best Practices](#)** | Combines hashing with **rate-limiting**, **multi-factor auth**, and **password policies**.                                                                                                         | Secure password management in user systems.                                                    |
| **[HMAC for Authentication](#)** | Uses **HMAC** to verify data + secret integrity (e.g., API tokens, JWTs).                                                                                                                               | Secure API communication or token validation.                                                  |
| **[Salting Patterns](#)**        | Focuses on **generating secure salts** for passwords (e.g., cryptographically random, unique per password).                                                                                           | When implementing custom password hashing (e.g., PBKDF2 without built-in salt management).     |
| **[Data Masking](#)**            | Stores **hashes or tokens** instead of raw PII (e.g., GDPR compliance).                                                                                                                               | Anonymizing logs or databases while maintaining queryable data.                                |
| **[Rate Limiting](#)**           | Prevents brute-force attacks on hash verification (e.g., login attempts).                                                                                                                           | Protecting hash-based authentication endpoints.                                                |
| **[Key Derivation Functions (KDFs](#)** | Extends hashing with **PBKDF2**, **Argon2**, or **scrypt** for defense-in-depth.                                                                                                                       | High-security applications needing adaptive computational costs.                              |

---

## **8. Further Reading**
- **[OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)**
- **[NIST SP 800-63B (Digital Identity Guidelines)](https://pages.nist.gov/800-63-3/sp800-63b.html)**
- **[Argon2 Documentation](https://argon2.org/)**
- **[Python `passlib` Library](https://passlib.readthedocs.io/)** (Supports bcrypt, Argon2, etc.)