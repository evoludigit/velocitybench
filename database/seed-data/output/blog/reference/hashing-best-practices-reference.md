# **[Pattern] Hashing Best Practices – Reference Guide**

---

## **Overview**
Hashing is a critical cryptographic technique used to secure data integrity, protect sensitive information, and enable efficient data retrieval via unique fingerprints. This reference guide covers best practices for selecting hashing algorithms, handling collisions, managing keys, and integrating hashing into applications while mitigating security risks. It emphasizes trade-offs between performance, security, and data corruption resistance, ensuring robust implementation across authentication, password storage, checksums, and data deduplication.

---

## **Key Concepts & Implementation Details**

### **1. Core Principles**
- **Purpose**: Convert input data (hash *input*) into a fixed-size *hash digest* (e.g., hexadecimal string) resistant to reverse-engineering.
- **Properties**:
  - **Deterministic**: Same input → same output.
  - **Avalanche Effect**: Small input changes drastically alter output.
  - **Irreversibility**: No feasible way to derive input from hash (cryptographic hashes).
- **Use Cases**:
  - Password storage (with salting).
  - Data integrity verification (e.g., file checksums).
  - Deduplication (e.g., database indexing).
  - Cryptographic proofs (e.g., Merkle trees).

### **2. Choosing the Right Hashing Algorithm**
Select algorithms based on security requirements and performance constraints:

| **Algorithm**       | **Output Size (bits)** | **Security Level**       | **Use Case**                          | **Notes**                                                                 |
|----------------------|------------------------|--------------------------|---------------------------------------|-----------------------------------------------------------------------------|
| **MD5**              | 128                    | Low (deprecated)         | Legacy checksums                      | Collision-resistant attacks exist; avoid for security.                    |
| **SHA-1**            | 160                    | Low (deprecated)         | Hashing small data                     | Vulnerable to collision attacks; replace with SHA-2/3.                    |
| **SHA-2 (e.g., SHA-256)** | 256–512               | High                     | Passwords, cryptographic hashes       | Balances security and performance; NIST-standardized.                   |
| **SHA-3**            | 224–512                | High                     | Future-proof hashing                   | Keccak-based; similar security to SHA-2 but improved resistance to side-channel attacks. |
| **BLAKE3**           | 160–640                | High                     | Fast hashing, checksums               | Modern alternative to SHA-3; optimized for performance and security.     |
| **Argon2**           | Variable               | Very High                | Password hashing (key derivation)     | Resistant to GPU/ASIC attacks; designed for memory-hardness.               |
| **scrypt**           | Variable               | High                     | Password storage                      | Slower than Argon2 but widely supported; requires tuning.                 |

> **Critical Note**: Avoid **MD5** and **SHA-1** for security-sensitive applications. Use **SHA-256**, **SHA-3**, or **Argon2** for passwords; **SHA-2** or **BLAKE3** for general hashing.

---

## **Schema Reference**
### **1. Password Hashing Schema**
```plaintext
{
  "algorithm": "Argon2id" | "scrypt" | "SHA-256" | ...,
  "salt": "<base64-encoded-salt>",  // Randomly generated; unique per password.
  "hash": "<hex-encoded-hash>",     // Derived from: HASH(algo, password + salt).
  "cost_factor": number,           // For memory-hard algorithms (e.g., Argon2's "memory" parameter).
  "iterations": number,            // For iterative algorithms (e.g., PBKDF2).
  "created_at": ISO_8601_timestamp  // Track salt/key rotation.
}
```
**Example**:
```json
{
  "algorithm": "Argon2id",
  "salt": "a1b2c3...",  // 16 bytes (base64-encoded)
  "hash": "9f86d081...",
  "cost_factor": 3,
  "iterations": 3,
  "created_at": "2023-10-01T00:00:00Z"
}
```

---

### **2. Data Integrity Checksum Schema**
```plaintext
{
  "file_path": "<path/to/file>",
  "algorithm": "SHA-256" | "BLAKE3",
  "checksum": "<hex-encoded-hash>",
  "computed_at": ISO_8601_timestamp,
  "size_bytes": number  // Optional: For validation
}
```
**Example**:
```json
{
  "file_path": "/data/release.txt",
  "algorithm": "SHA-256",
  "checksum": "a94a8fe5...",
  "computed_at": "2023-10-01T00:01:00Z",
  "size_bytes": 1024
}
```

---

## **Query Examples**
### **1. Generating a Secure Password Hash**
**Language: Python**
```python
import hashlib
import os
import binascii

# Generate a random salt (16 bytes)
salt = os.urandom(16)

# Hash with SHA-256 (salted)
password = b"secure_password123"
hashed = hashlib.pbkdf2_hmac(
    "sha256",
    password,
    salt,
    100000  # Iterations (adjust based on security needs)
)
hash_hex = binascii.hexlify(hashed).decode("utf-8")

print(f"Salt: {binascii.b64encode(salt).decode()}")  # Base64-encoded salt
print(f"Hash: {hash_hex}")
```

**Output**:
```
Salt: a1B2c3... (16 bytes base64)
Hash: 9f86d081884c7d659a2feaa6c4c26097...
```

---

### **2. Verifying a Password Hash**
**Language: JavaScript**
```javascript
const crypto = require("crypto");

// Assume we have stored salt and hash from earlier
const salt = Buffer.from("a1B2c3...", "base64");
const storedHash = "9f86d081884c7d659a2feaa6c4c26097...";

const password = "secure_password123";
const hashedPassword = crypto.pbkdf2Sync(
  password,
  salt,
  100000,
  32,  // SHA-256 output length
  "sha256"
).toString("hex");

const isValid = hashedPassword === storedHash;
console.log("Password valid?", isValid);
```

---

### **3. Computing a File Checksum**
**Language: Bash**
```bash
# Compute SHA-256 checksum of a file
sha256sum /path/to/file > checksum.txt

# Verify checksum later
expected_checksum=$(awk '{print $1}' checksum.txt)
computed_checksum=$(sha256sum /path/to/file | awk '{print $1}')
if [ "$expected_checksum" == "$computed_checksum" ]; then
  echo "Checksum verified."
fi
```

---

## **Best Practices & Implementation Guidance**

### **1. Password Storage**
- **Always salt passwords**:
  - Use cryptographically secure random salts (e.g., `secrets.token_bytes(16)` in Python).
  - Store salt alongside the hash (never derive salt from password).
- **Use memory-hard algorithms**:
  - **Argon2id** or **scrypt** for high-security applications (e.g., authentication).
  - Avoid PBKDF2 unless legacy support is required.
- **Adjust parameters**:
  - **Iterations**: Increase to slow down brute-force attacks (e.g., 100,000+).
  - **Memory**: For Argon2, set `memory` to 64MB+ to resist GPU attacks.

### **2. Data Integrity**
- **Use SHA-256 or SHA-3** for checksums (larger output = better collision resistance).
- **Avoid rolling your own hash**: Prefer standardized algorithms (e.g., `hashlib` in Python, `crypto` in Node.js).
- **Validate file sizes**: Cross-check hash + file size to detect partial/corrupted downloads.

### **3. Collision Resistance**
- **For cryptographic use**: SHA-256/SHA-3 are collision-resistant for practical purposes.
- **For non-cryptographic use**: SHA-1 or MD5 *may* suffice if collision resistance isn’t critical (e.g., deduplication).

### **4. Performance Considerations**
| **Algorithm** | **Speed (ops/sec)** | **Notes**                          |
|---------------|---------------------|------------------------------------|
| **SHA-256**   | ~1–5 billion        | Fast for general hashing.          |
| **Argon2id**  | ~1–10 thousand      | Slower but secure for passwords.   |
| **BLAKE3**    | ~2–8 billion        | Faster than SHA-3 for some workloads. |

- **Trade-off**: Security vs. speed. Prioritize security for passwords; use faster hashes for checksums.

### **5. Key Management**
- **Never reuse salts**: Generate a unique salt per password/hash.
- **Rotate keys periodically**: For systems using hashes in authentication (e.g., OAuth tokens).
- **Secure storage**: Encrypt stored salts/hashes if regulatory compliance requires it (e.g., HIPAA).

---

## **Security Risks & Mitigations**
| **Risk**                          | **Mitigation**                                      |
|-----------------------------------|-----------------------------------------------------|
| **Precomputed table attacks**     | Use salts + high iteration counts.                 |
| **Brute-force attacks**           | Memory-hard algorithms (Argon2/scrypt).             |
| **Side-channel attacks**          | Constant-time comparison (e.g., `scrypt_verify`).  |
| **Weak randomness**               | Use cryptographically secure RNG (`os.urandom`, `secrets`). |
| **Algorithm obsolescence**        | Stay updated on NIST recommendations (e.g., SHA-3). |

---

## **Query Examples (Advanced)**
### **1. Password Hash Comparison (Constant-Time)**
**Language: Python**
```python
def verify_password(stored_hash, salt, input_password):
    # Decode stored hash (e.g., from database)
    stored_salt, stored_hash_bytes = stored_hash.split("$")[1:3]
    salt = binascii.unhexlify(stored_salt)
    stored_hash_bytes = binascii.unhexlify(stored_hash)

    # Compute hash with constant-time comparison
    computed_hash = hashlib.pbkdf2_hmac(
        "sha256",
        input_password,
        salt,
        100000
    )

    # Use timsort to prevent timing attacks
    return secrets.compare_digest(computed_hash, stored_hash_bytes)
```

### **2. Batch Hashing (Efficiency)**
**Language: Go**
```go
package main

import (
	"crypto/sha256"
	"encoding/base64"
	"log"
	"math/rand"
	"time"
)

func generateSalt() string {
	b := make([]byte, 16)
	rand.Read(b) // Cryptographically secure
	return base64.StdEncoding.EncodeToString(b)
}

func hashPassword(password string) (string, string) {
	salt := generateSalt()
	h := sha256.New()
	h.Write([]byte(password + salt))
	hash := base64.StdEncoding.EncodeToString(h.Sum(nil))
	return hash, salt
}

func main() {
	passwords := []string{"user1", "user2"}
	hashes := make(map[string]string)
	salts := make(map[string]string)

	for _, pw := range passwords {
		h, s := hashPassword(pw)
		hashes[pw] = h
		salts[pw] = s
		log.Printf("Password: %s\nHash: %s\nSalt: %s\n", pw, hashes[pw], salts[pw])
	}
}
```

---

## **Related Patterns**
1. **[Secure Password Storage]** – Combines hashing with salting and key stretching (e.g., Argon2).
2. **[Token-Based Authentication]** – Uses hashed tokens (e.g., HMAC-SHA256) for stateless sessions.
3. **[Data Anonymization]** – Applies hashing (e.g., SHA-256) to PII for compliance (e.g., GDPR).
4. **[Cryptographic Signatures]** – Uses HMAC or ECDSA with hashing for authentication/integrity.
5. **[Blockchain Data Integrity]** – Leverages SHA-256 for Merkle trees and transaction hashing.

---

## **Further Reading**
- **[NIST SP 800-131A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131A.pdf)**: Guidelines for password hashing.
- **[RFC 2104](https://tools.ietf.org/html/rfc2104)**: HMAC: Keyed-Hashing for Message Authentication.
- **[Argon2 Paper](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/conti)**: Security analysis of Argon2.

---
**Last Updated**: 2023-10-01
**Version**: 1.2