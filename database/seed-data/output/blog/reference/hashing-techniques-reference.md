**[Pattern] Hashing Techniques – Reference Guide**

---

### **Overview**
Hashing Techniques is a **security and data integrity** pattern used to transform input data into a fixed-size hash value (digest) via a mathematical function. Hashes serve critical purposes:
- **Data verification** (e.g., checksums, cryptographic hashing).
- **Indexing and lookup** (e.g., hash tables, databases).
- **Password storage** (via salting and hashing).
- **Detection of tampering** (e.g., comparing hashes to detect changes).

This guide covers key concepts, implementation details, schema references, and practical examples for common hashing algorithms (e.g., MD5, SHA-256, bcrypt).

---

## **Key Concepts and Implementation Details**

### **1. Core Principles**
| Concept               | Description                                                                                                                                                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Deterministic**     | Same input always produces the same hash.                                                                                                                                                                |
| **Irreversible**      | Hash functions cannot reverse-engineer the original data (preimage resistance).                                                                                                                       |
| **Avalanche Effect**  | A small change in input drastically alters the hash (sensitivity to input differences).                                                                                                                 |
| **Collision Resistance** | Minimal probability of two different inputs producing the same hash (e.g., SHA-256 resists collisions better than MD5).                                                                                     |
| **Salting**           | Adding random data to inputs (e.g., passwords) to prevent rainbow table attacks.                                                                                                                          |
| **Iterations**        | Repeating the hashing process (e.g., bcrypt’s work factor) to slow down brute-force attacks.                                                                                                               |

---

### **2. Hashing Algorithms**
| Algorithm       | Output Size | Use Case                                                                 | Security Notes                                                                                     |
|-----------------|-------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **MD5**         | 128-bit     | Legacy checksums, non-cryptographic (deprecated for security).            | Vulnerable to collision attacks; avoid for passwords or critical data.                             |
| **SHA-1**       | 160-bit     | Deprecated due to collision risks (e.g., SHA-1 broken in 2017).          | Use SHA-2 or SHA-3 for security-sensitive applications.                                              |
| **SHA-256**     | 256-bit     | Cryptographic hashing, blockchain (e.g., Bitcoin), password storage.      | Strong collision resistance; ideal for most security needs.                                         |
| **SHA-512**     | 512-bit     | High-security applications (e.g., Windows passwords, TLS).              | Overkill for most use cases but offers maximum collision resistance.                                 |
| **bcrypt**      | Variable    | Password hashing with adaptive difficulty (via cost factor).              | Resistant to GPU/ASIC attacks; preferred for user authentication.                                   |
| **Argon2**      | Variable    | Modern password hashing (winner of Password Hashing Competition).         | Memory-hard; mitigates brute-force attacks on large-scale systems.                                  |
| **Blake3**      | 256/512-bit | Fast, cryptographically secure (recent alternative to SHA-3).            | Optimized for performance and security; gaining traction in modern systems.                        |

---

### **3. Schema Reference**
#### **Schema: Hashing Configuration**
| Field          | Type     | Description                                                                                                                                                                      | Example Value                     |
|----------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------|
| `algorithm`    | String   | Hash algorithm name (e.g., `SHA-256`, `bcrypt`).                                                                                                                                    | `"SHA-256"`                       |
| `salt`         | Binary   | Random salt value (if applicable).                                                                                                                                             | `b'\\x0f\\xab\\xcd\\x12\\x34...'` |
| `iterations`   | Integer  | Number of hashing rounds (e.g., bcrypt’s `cost factor`).                                                                                                                         | `10` (bcrypt default)             |
| `size`         | Integer  | Output hash size in bits (e.g., 256 for SHA-256).                                                                                                                                  | `256`                              |
| `key_derivation` | Boolean | Whether to use key derivation (e.g., PBKDF2, Argon2).                                                                                                                           | `true`                             |

#### **Schema: Password Hashing (bcrypt Example)**
```json
{
  "algorithm": "bcrypt",
  "cost": 12,         // Work factor (higher = slower/secure)
  "salt": "$2y$12$...", // Prepended salt (e.g., from `bcrypt.hash()`)
  "hash": "$2y$12$...abc123!"  // Full hashed password string
}
```

---

## **Query Examples**
### **1. Generating a Hash (Python)**
```python
import hashlib

# SHA-256
sha256 = hashlib.sha256(b"hello").hexdigest()
print(sha256)  # Output: "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

# bcrypt (requires `bcrypt` library)
import bcrypt
hashed = bcrypt.hashpw(b"password", bcrypt.gensalt(rounds=12))
print(hashed.decode())  # Output: "$2b$12$..." (random salt + hash)
```

### **2. Verifying a Password (bcrypt)**
```python
# Load stored hash and verify
stored_hash = b'$2b$12$N9qo8uLO...'.encode()
password = b"password"

if bcrypt.checkpw(password, stored_hash):
    print("Password matches!")
else:
    print("Invalid password.")
```

### **3. Checking Hash Integrity (SHA-256)**
```python
# Compare hashes of a file
import hashlib

def file_hash(filename, block_size=65536):
    hasher = hashlib.sha256()
    with open(filename, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()

original_hash = file_hash("data.txt")
new_hash = file_hash("data.txt")

if original_hash == new_hash:
    print("File is unchanged.")
else:
    print("File has been modified!")
```

### **4. Generating a Salt (Random Bytes)**
```python
import os
import base64

def generate_salt(size=16):
    return base64.urlsafe_b64encode(os.urandom(size)).decode()

salt = generate_salt()
print(salt)  # Output: "aGVsbG8td29ybGQtd29ybGQtCg=="
```

---

## **Best Practices**
1. **Never use MD5/SHA-1** for security-sensitive data.
2. **Always salt passwords**:
   ```python
   salt = os.urandom(16)
   hashed = hashlib.pbkdf2_hmac("sha256", b"password" + salt, salt, 100000)
   ```
3. **Use adaptive algorithms** (e.g., bcrypt, Argon2) for passwords to resist brute-force attacks.
4. **Store hashes securely**: Never log or expose raw hashes or salts.
5. **Validate hash sizes**: Ensure your algorithm’s output matches your schema (e.g., 256-bit for SHA-256).
6. **Update algorithms** if security vulnerabilities are discovered (e.g., switch from SHA-256 to SHA-3).

---

## **Common Pitfalls**
| Pitfall                                | Solution                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|
| **Hardcoded salts**                    | Generate unique salts per input.                                         |
| **Using weak algorithms**              | Prefer SHA-2/3, bcrypt, or Argon2 over MD5/SHA-1.                         |
| **No iterations**                     | Increase work factor for password hashing (e.g., bcrypt’s `cost=12`).   |
| **Exposing raw hashes**                | Store only the hash + salt; derive the hash on verification.              |
| **Assuming uniqueness**               | Hash collisions exist; use additional checks (e.g., timestamps).          |

---

## **Related Patterns**
1. **[Password Storage Best Practices]**
   - Complements hashing by covering salting, peppering, and secure storage.
   - *Link*: [Password Storage Guide](#)

2. **[Digital Signatures]**
   - Uses hashing (e.g., HMAC) to verify message authenticity with a private key.
   - *Link*: [Digital Signatures Pattern](#)

3. **[Checksums for Data Integrity]**
   - Lightweight hashing (e.g., CRC32) for error detection in files/networks.
   - *Link*: [Checksum Patterns](#)

4. **[Key Derivation Functions (KDFs)]**
   - Securely derives cryptographic keys from passwords (e.g., PBKDF2, Argon2).
   - *Link*: [Key Derivation Patterns](#)

5. **[Collision Resistance Attacks]**
   - Explores attacks like birthday paradox and mitigation strategies.
   - *Link*: [Security Attacks Guide](#)

---
**Note**: For production use, consult [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) for updates.