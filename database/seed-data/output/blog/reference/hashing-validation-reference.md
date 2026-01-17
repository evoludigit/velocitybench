---
# **[Pattern] Reference Guide: Hashing Validation**

---

## **Overview**
Hashing validation is a security pattern used to verify data integrity by comparing a computed hash of received data against a precomputed or previously stored hash. This ensures that data has not been tampered with during transmission or storage. Common use cases include API request validation, database record verification, and file integrity checks. Hashing algorithms (e.g., SHA-256, HMAC) generate unique "fingerprints" of data, enabling tamper detection. This pattern is widely adopted in authentication, cryptographic protocols, and distributed systems to mitigate replay attacks, data corruption, and unauthorized modifications.

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**          | **Description**                                                                                     | **Example**                     |
|------------------------|-----------------------------------------------------------------------------------------------------|---------------------------------|
| **Hashing Algorithm**  | Cryptographic function generating a fixed-size hash (e.g., SHA-256, SHA-512, HMAC-SHA256).         | `sha256("secret")`              |
| **Stored Hash**        | Precomputed hash stored securely (e.g., in a database or metadata).                                | `"abc123..."` (SHA-256)         |
| **Computed Hash**      | On-the-fly hash of received data for comparison.                                                    | `Hash(data)`                    |
| **Salt**               | Random value added to input to prevent rainbow table attacks (critical for password hashing).       | `"random_salt_123"`             |
| **Hashing Library**    | Framework/sdk (e.g., Python `hashlib`, Java `MessageDigest`, Node.js `crypto`).                     | `import { createHash } from 'crypto';` |

### **2. Types of Hashing Validation**
| **Type**               | **Use Case**                                                                                     | **Example**                          |
|------------------------|-------------------------------------------------------------------------------------------------|--------------------------------------|
| **Static Hashing**     | Verifying unchanging data (e.g., static API payloads, file checksums).                        | `verifyHash(data, "precomputed_hash")` |
| **Dynamic Hashing**    | Validating mutable data (e.g., user inputs, dynamic API responses) with optional salts.         | `verifyHash(data + salt, "pre_computed_hash")` |
| **HMAC Validation**    | Securing data with a shared secret (common in JWT or OAuth2 tokens).                            | `HMAC-SHA256(key, data)`             |
| **Chained Hashing**    | Combining multiple algorithms for enhanced security (e.g., SHA-256 + HMAC).                      | `HMAC(sha256(data), secret_key)`     |

### **3. Security Considerations**
- **Algorithm Selection**: Use modern algorithms (SHA-3, Argon2) over deprecated ones (MD5, SHA-1).
- **Salting**: Always apply salts to prevent precomputed attacks (especially for passwords).
- **Timing Attacks**: Avoid revealing hash comparison time differences to avoid side-channel leaks.
- **Key Management**: Securely store secrets (e.g., HMAC keys) using hardware security modules (HSMs).

---

## **Schema Reference**
| **Field**            | **Type**       | **Description**                                                                                     | **Example Value**                     |
|----------------------|----------------|-----------------------------------------------------------------------------------------------------|---------------------------------------|
| `algorithm`          | String         | Hashing algorithm used (e.g., `SHA-256`, `HMAC-SHA256`).                                           | `"SHA-256"`                           |
| `stored_hash`        | String         | Hex-encoded precomputed hash value.                                                                 | `"a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"` |
| `computed_hash`      | String         | Hex-encoded hash of received data.                                                                  | `null` (filled by validation logic)   |
| `salt`               | String/Binary  | Random value appended to input for salting.                                                         | `"salt123"`                           |
| `key`                | String/Binary  | Secret key for HMAC validation (if applicable).                                                    | `"super_secret_key"`                   |
| `input_data`         | String/Binary  | Raw data to be hashed (e.g., JSON payload, file content).                                         | `{"id": 123, "name": "Alice"}`         |
| `hash_version`       | Integer        | Version tag for hash algorithm changes (e.g., `1` for SHA-256).                                    | `1`                                   |

---
## **Query Examples**

### **1. Static Hashing (Python)**
```python
import hashlib

def compute_hash(data: str, algorithm: str = "sha256", salt: str = None) -> str:
    if salt:
        data += salt
    return hashlib.new(algorithm, data.encode()).hexdigest()

# Example: Verify static hash
stored_hash = "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
computed_hash = compute_hash("example_data", salt="salt123")
is_valid = hmac.compare_digest(computed_hash, stored_hash)  # Secure comparison
```

### **2. HMAC Validation (Node.js)**
```javascript
const crypto = require('crypto');

const verifyHMAC = (data, secret, storedHash) => {
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(data);
    const computedHash = hmac.digest('hex');
    return crypto.timingSafeEqual(
        Buffer.from(computedHash),
        Buffer.from(storedHash)
    );
};

// Example: Verify HMAC
const data = "user=Alice&action=login";
const secret = "my_secret_key";
const storedHMAC = "3fec..."; // Precomputed HMAC
const isValid = verifyHMAC(data, secret, storedHMAC);
```

### **3. Database Record Validation (SQL)**
```sql
-- Store record with computed hash
INSERT INTO users (id, name, hash)
VALUES (1, 'Alice', SHA256(CONCAT('Alice', 'salt123')));

-- Verify during lookup
SELECT * FROM users
WHERE name = 'Alice'
AND SHA256(CONCAT(name, 'salt123')) = 'stored_hash';
```

---

## **Error Handling**
| **Error**                     | **Cause**                                      | **Solution**                                                                 |
|--------------------------------|------------------------------------------------|------------------------------------------------------------------------------|
| `HashMismatchError`            | Computed hash ≠ stored hash.                   | Recompute hash; check for tampering.                                          |
| `AlgorithmNotSupported`        | Unrecognized algorithm.                       | Use supported algorithms (e.g., SHA-256).                                     |
| `InvalidInputData`             | Malformed or missing input.                   | Sanitize input; validate schema before hashing.                                |
| `TimingAttackDetected`         | Time-based side-channel leak.                  | Use `timingSafeEqual` (e.g., `crypto.timingSafeEqual` in Node.js).           |

---

## **Related Patterns**
1. **Signature Validation**: Extends hashing with asymmetric keys (e.g., RSA) for authentication.
2. **JWT Validation**: Uses HMAC/SHA for token integrity checks.
3. **Password Hashing**: Specialized salting (e.g., bcrypt, Argon2) for secure credential storage.
4. **Data Masking**: Complements hashing by obfuscating sensitive fields in logs.
5. **Cryptographic Signatures**: Combines hashing with digital signatures for non-repudiation.

---
## **Best Practices**
- **Versioning**: Track hash algorithm versions to migrate securely (e.g., `hash_version = 2` for SHA-3).
- **Logging**: Log hash mismatches without exposing sensitive data (e.g., append `hash: [REDACTED]`).
- **Performance**: Cache precomputed hashes where possible (e.g., file checksums).
- **Testing**: Simulate tampering (e.g., `data + modified_byte`) to validate defenses.

---
**See also**: [OWASP Hashing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Hashing_Cheat_Sheet.html).