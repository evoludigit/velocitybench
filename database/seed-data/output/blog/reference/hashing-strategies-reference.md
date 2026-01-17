# **[Pattern] Hashing Strategies Reference Guide**

---
## **Overview**
The **Hashing Strategies** pattern defines a set of techniques for securely transforming data into a fixed-size string (hash) to enable efficient storage, comparison, and retrieval without exposing original values. Hashing is critical for secure password storage, data integrity verification, deduplication, and indexing. This guide covers key concepts, implementation best practices, schema design, and query examples for common hashing strategies, including cryptographic (e.g., bcrypt, Argon2), checksum-based (e.g., SHA-256), and non-cryptographic (e.g., MD5) approaches.

---

## **Key Concepts**
| **Term**               | **Definition**                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------|
| **Hash Function**       | Algorithmic process producing a fixed-size hash value from input data.                          |
| **Collision Resistance**| Minimizing the likelihood of two distinct inputs producing the same hash (e.g., SHA-3272).       |
| **Salt**               | Random data appended to input before hashing to prevent rainbow table attacks.                   |
| **Peper**              | A secret key added to the salt, further enhancing security.                                      |
| **Work Factor**        | Computational cost (e.g., bcrypt rounds) to slow down brute-force attacks.                        |
| **Deterministic Hash** | Same input always produces the same hash (e.g., SHA-256).                                        |
| **Nonce**              | Unique per-use value (e.g., in HMAC) to ensure hash uniqueness for the same input.               |

---
## **Schema Reference**
Below are common database schema examples for storing hashed data. Adjust fields based on your use case (e.g., password storage vs. file integrity checks).

### **1. Password Storage (Cryptographic Hashing)**
```sql
CREATE TABLE user_credentials (
    user_id INT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    -- bcrypt/Argon2 schema (includes salt/pepper metadata)
    hashed_password BYTEA NOT NULL,
    salt VARCHAR(64) NOT NULL,          -- Base64-encoded salt
    pepper VARCHAR(32),                 -- Optional server-side pepper (store securely!)
    cost_factor INT DEFAULT 12,         -- bcrypt/Argon2 parameter (e.g., bcrypt rounds)
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **2. File Integrity Checksums (SHA-256)**
```sql
CREATE TABLE file_checksums (
    file_id INT PRIMARY KEY,
    file_path VARCHAR(512) UNIQUE NOT NULL,
    hash_algorithm VARCHAR(20) NOT NULL,  -- e.g., "SHA-256", "SHA-512"
    file_hash BYTEA NOT NULL,
    salt VARCHAR(32),                     -- Optional for keyed hashes (e.g., HMAC)
    last_verified TIMESTAMP DEFAULT NOW()
);
```

### **3. Deduplication (Non-Cryptographic MD5)**
```sql
CREATE TABLE dedup_cache (
    data_id INT PRIMARY KEY,
    raw_data BYTEA NOT NULL,
    hash_algorithm VARCHAR(10) DEFAULT "MD5",  -- Fast, but avoid for security-sensitive data
    hash_value VARCHAR(64) NOT NULL,          -- Base64-encoded for readability
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (hash_value)                       -- Enforce deduplication
);
```

---
## **Implementation Details**

### **1. Cryptographic Hashing (Security-Focused)**
Use **bcrypt**, **Argon2**, or **PBKDF2** for password storage due to their resistance to brute force.

#### **Example: Hashing a Password with bcrypt (Python)**
```python
import bcrypt

def hash_password(password: str, salt: bytes = None) -> tuple[bytes, int]:
    """Hashes a password with bcrypt and returns (hashed_password, cost_factor)."""
    if salt is None:
        salt = bcrypt.gensalt(rounds=12)  # Default cost factor: 12
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed, 12  # Store cost factor separately for validation later

# Usage:
hashed_pw, cost = hash_password("user123")
print(f"Hashed: {hashed_pw}, Cost: {cost}")
```

#### **Schema Validation Query**
```sql
-- Verify a user's password against stored hash
SELECT * FROM user_credentials
WHERE bcrypt.hash_password_hash(:input_password, salt) = hashed_password;
```

---

### **2. Checksums for Data Integrity**
Use **SHA-256** or **SHA-3** for file/data verification. Prepend a **salt** if hashing sensitive keys (e.g., HMAC).

#### **Example: Generate SHA-256 Checksum (JavaScript)**
```javascript
const crypto = require('crypto');

function generateChecksum(data: Buffer, salt?: string): string {
    const hash = crypto.createHash('sha256');
    hash.update(salt ? salt + data : data);
    return hash.digest('hex');  // Hex format for readability
}

// Usage:
const checksum = generateChecksum(Buffer.from("sensitive_data"), "random_salt");
console.log(checksum);  // e.g., "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
```

#### **Query to Compare Checksums**
```sql
-- Find files with mismatched checksums
SELECT file_path, file_hash
FROM file_checksums
WHERE file_hash != sha256(file_content)  -- Pseudocode; use application logic
```

---

### **3. Non-Cryptographic Hashing (Performance-Focused)**
Use **MD5** or **XXHash** for fast deduplication, but **avoid for security-sensitive data**.

#### **Example: MD5 for Deduplication (Go)**
```go
package main

import (
	"crypto/md5"
	"encoding/hex"
)

func hashData(data []byte) string {
	hash := md5.Sum(data)
	return hex.EncodeToString(hash[:])  // Base64 or hex for storage
}
```

#### **Schema Query for Deduplication**
```sql
-- Find duplicates by hash
SELECT COUNT(*) FROM dedup_cache
WHERE hash_value = 'a1b2c3...' GROUP BY hash_value HAVING COUNT(*) > 1;
```

---

## **Query Examples**
### **1. Password Hash Verification (PostgreSQL)**
```sql
-- Check if input password matches stored hash (bcrypt)
WITH hashed_input AS (
    SELECT bcrypt.hashpw(:plain_password, salt) AS input_hash
    FROM user_credentials WHERE user_id = :user_id
)
SELECT * FROM hashed_input
WHERE input_hash = hashed_password;
```

### **2. Check File Integrity (SQLite)**
```sql
-- Flag files with corrupted checksums
SELECT
    file_id,
    file_path,
    file_hash,
    hex(sha256(file_content)) AS computed_hash
FROM file_checksums
WHERE file_hash <> hex(sha256(file_content))  -- Compare stored vs. recomputed
```

### **3. Deduplicate Records (MySQL)**
```sql
-- Insert only if hash doesn't exist
INSERT INTO dedup_cache (data_id, raw_data, hash_value)
SELECT
    :new_id,
    :raw_data,
    MD5(:raw_data) AS hash_value
WHERE NOT EXISTS (
    SELECT 1 FROM dedup_cache WHERE hash_value = MD5(:raw_data)
);
```

---

## **Performance Considerations**
| **Strategy**       | **Use Case**                  | **Speed**       | **Security**          | **Notes**                                  |
|--------------------|-------------------------------|-----------------|-----------------------|--------------------------------------------|
| **bcrypt/Argon2**  | Password storage              | Slow (intended) | High                  | Adjust `cost_factor` for balance.          |
| **SHA-256**        | Data integrity checks         | Medium          | High                  | Use salt for keyed hashes (HMAC).          |
| **MD5/XXHash**     | Deduplication                 | Fast            | Low                   | Never use for passwords or sensitive data. |

---

## **Security Best Practices**
1. **Always Salt**: Prevent rainbow table attacks by generating a unique salt per record.
2. **Use High Work Factors**: Configure `cost_factor` (bcrypt) or `degree_of_parallelism` (Argon2) to resist brute force.
3. **Store Hashes Securely**: Use `BYTEA` or binary formats to avoid corruption.
4. **Avoid Plaintext Hashes**: Never store or transmit raw hashes without additional context.
5. **Regularly Update Algorithms**: Move to stronger hashes (e.g., SHA-3) as vulnerabilities emerge.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                                     |
|---------------------------|---------------------------------------------------------------------------------------------------|
| **[Salted Hashing]**      | Extends hashing strategies to include dynamic salts.                                             |
| **[Keyed-HMAC]**          | Uses symmetric keys (e.g., HMAC-SHA256) for authenticated hashing.                               |
| **[Password Reset Tokens]** | Combines hashing with expiration (e.g., HMAC + timestamp) for time-limited access.               |
| **[Bloom Filters]**       | Probabilistic data structure for quick membership tests using hashing.                            |
| **[Rate Limiting]**       | Protects against brute-force attacks on hashed endpoints (e.g., login attempts).                 |

---
**Note**: For production use, consult [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) for up-to-date recommendations.