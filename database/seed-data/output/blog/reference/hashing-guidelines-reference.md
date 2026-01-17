# **[Pattern] Reference Guide: Hashing Guidelines**

## **Overview**
The **Hashing Guidelines** pattern ensures consistent, predictable, and secure hashing of data across applications. This guide defines standard practices for selecting hash algorithms, parameterization, key derivation, and output formatting. Adherence to these guidelines minimizes cryptographic vulnerabilities like rainbow table attacks, salting collisions, and output reuse while improving performance and interoperability.

Key benefits include:
- **Security:** Mitigation of brute-force and precomputed attacks.
- **Portability:** Compatibility across systems via standardized outputs.
- **Efficiency:** Optimized hashing trade-offs between speed and strength.
- **Auditability:** Clear documentation for compliance and forensic purposes.

This pattern applies to all data classified as sensitive (PII, credentials, tokens) and should be paired with **Key Derivation Functions (KDFs)** or **Secure Hashing Algorithms (SHAs)** as appropriate.

---

## **Core Concepts**

### **1. Hash Algorithm Selection**
Choose algorithms based on security requirements, performance, and output size. Avoid legacy or broken algorithms (e.g., MD5, SHA-1).

| **Algorithm**       | **Use Case**                          | **Output Size** | **Key Stretch (KDF)**? | **Deprecation Status** |
|---------------------|---------------------------------------|-----------------|------------------------|------------------------|
| **SHA-256**         | General-purpose hashing               | 256 bits        | No                     | Supported              |
| **SHA-3 (Keccak)**  | High-security requirements            | 256–512 bits    | No                     | Supported (SHA-3-256)  |
| **Argon2**          | Password hashing (KDF)                | 32+ bytes       | Yes (memory-hard)       | Recommended            |
| **bcrypt**          | Password storage                      | 22+ bytes       | Yes (work-factor)       | Supported              |
| **PBKDF2**          | Legacy systems (with caution)         | Configurable    | Yes                    | Deprecated             |

**Guideline:**
- Use **SHA-2** or **SHA-3** for non-KDF applications (e.g., file integrity checks).
- Prefer **Argon2** or **bcrypt** for password hashing due to their built-in salting and work factors.

---

### **2. Salting**
Add a unique salt to each hash to prevent rainbow table attacks. Salts must:
- Be **random** (cryptographically secure).
- Be **unique per entry**.
- Be **securely stored** alongside the hash (never reused).

**Schema Reference: Salt Requirements**
| **Field**      | **Description**                                                                 | **Example**                     |
|----------------|-------------------------------------------------------------------------------|---------------------------------|
| `salt_size`    | Minimum 16 bytes (128 bits) for modern algorithms.                            | `32` (bytes)                    |
| `salt_format`  | Hexadecimal or Base64 encoding for readability.                                | `base64`                        |
| `salt_storage` | Stored alongside hash in a secure database column (e.g., `salt_varchar(64)`). | `{"salt":"AQ=="}`               |

**Implementation:**
```python
import os
salt = os.urandom(16)  # 16 bytes for SHA-2
```

---

### **3. Key Derivation Functions (KDFs)**
For passwords, combine hashing with a KDF to add computational overhead (defending against brute-force).

| **Parameter**      | **Purpose**                                                                 | **Example Value**               |
|--------------------|-----------------------------------------------------------------------------|---------------------------------|
| `iterations`       | Work factor (higher = slower, more secure; start with 1M).                   | `100_000`                       |
| `key_length`       | Output length in bytes (32+ recommended).                                    | `32`                            |
| `algorithm`        | Derived from `Argon2`, `bcrypt`, or `PBKDF2`.                               | `Argon2id`                      |

**Formulas:**
- **Argon2:** `Argon2id(password + salt, iterations=100_000, memory=64MB, hash_len=32)`
- **bcrypt:** `bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))`

---

### **4. Output Formatting**
Hashes and salts should be **base64-encoded** for storage/transmission. Example structure:
```
<algorithm>:<iterations>:<salt>:<hash>
```
**Example (Argon2):**
```
Argon2id$v=19$m=65536,t=2,p=1$...$abc123...==
```
*(Format derived from [Argon2 spec](https://github.com/P-H-C/phc-winner-argon2).)*

---

## **Schema Reference**
| **Component**      | **Type**       | **Description**                                                                 | **Constraints**                                                                 |
|--------------------|----------------|-------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| `hash_algorithm`   | `string`       | Algorithm name (SHA-256, Argon2id, etc.).                                      | Must match supported list (e.g., `SHA-256` or `Argon2id`).                    |
| `salt`            | `string`       | Base64-encoded salt (16+ bytes).                                               | Unique per entry; stored securely.                                             |
| `iterations`      | `integer`      | Work factor for KDFs (ignored for pure hashing).                              | ≥100,000 for passwords (Argon2/bcrypt).                                        |
| `hash_value`      | `string`       | Base64-encoded hash output.                                                   | Length varies by algorithm (e.g., 44 chars for SHA-256).                     |
| `version`         | `string`       | Schema version (e.g., `v1.0`).                                                 | Increment for breaking changes.                                                |

---

## **Query Examples**
### **1. Verify a Password (Argon2)**
```sql
-- Pseudocode: Check if hashed_password matches input_password
SELECT
    CASE
        WHEN Argon2Verify(hashed_password, input_password)
        THEN 'Match'
        ELSE 'No match'
    END AS verification
FROM users
WHERE user_id = 123;
```

### **2. Generate a Secure Hash (SHA-256)**
```python
import hashlib
import base64

def generate_sha256(salt: bytes, data: str) -> str:
    h = hashlib.sha256(salt + data.encode()).digest()
    return base64.b64encode(h).decode()
```
**Usage:**
```python
salt = os.urandom(16)
hash = generate_sha256(salt, "password123")
```

### **3. Database Schema (SQL)**
```sql
CREATE TABLE user_credentials (
    id INT PRIMARY KEY,
    username VARCHAR(50),
    hash_algorithm VARCHAR(20),  -- e.g., "Argon2id"
    salt VARCHAR(64),           -- Base64-encoded
    hash_value VARCHAR(64),     -- Base64-encoded
    iterations INT              -- For KDFs
);
```

---

## **Related Patterns**
1. **[Key Derivation Functions (KDFs)](link)** – Extends hashing for passwords with memory/compute overhead.
2. **[Secure Storage Guidelines](link)** – Best practices for encrypting hashes at rest.
3. **[Password Policies](link)** – Rules for enforcing complexity and rotation.
4. **[Cryptographic Nonce Usage](link)** – Ensuring uniqueness in salts and tokens.

---

## **Best Practices**
- **Never hash without salting.**
- **Use the strongest algorithm for your threat model** (e.g., Argon2 for passwords).
- **Rotate salts** if a breach occurs (though hashes remain secure if properly salted).
- **Document schema versions** for backward compatibility.
- **Audit hashes** periodically for anomalies (e.g., collision checks).

---
**Last Updated:** `[Insert Date]`
**Contributors:** `[List Names]`