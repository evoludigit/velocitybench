**[Pattern] Hashing Verification Reference Guide**

---

### **1. Overview**
Hashing verification is a security pattern used to **validate data integrity** by comparing a precomputed hash (e.g., SHA-256, MD5) against a newly generated hash of the same input. This ensures data hasn’t been altered between storage and retrieval. Common use cases include:
- File integrity checks (e.g., software downloads, firmware updates).
- Database record validation (e.g., ensuring API responses match expectations).
- Cryptographic attestation (e.g., verifying signature hashes in blockchain systems).

This guide covers implementation details, schemas, query examples, and related patterns for hashing verification in software systems.

---

### **2. Key Concepts & Implementation Details**

#### **2.1 Core Components**
| **Component**       | **Purpose**                                                                 | **Example Values**                     |
|----------------------|-----------------------------------------------------------------------------|----------------------------------------|
| **Hash Algorithm**   | Determines how the hash is computed (e.g., SHA-256, BLAKE3).               | `"SHA-256"`, `"BLAKE3"`               |
| **Hash Input**       | Raw data (bytes, string, file) to be hashed.                                | `"file.txt"`, `buffer_of_data`        |
| **Stored Hash**      | Precomputed hash (e.g., from a trusted source like a manifest or database). | `"a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"` |
| **Verification**     | Compare the stored hash with the newly computed hash.                      | **Pass** if equal; **Fail** otherwise. |

---

#### **2.2 Workflow**
1. **Generate a hash** of the input data using a chosen algorithm.
2. **Compare** the generated hash with the stored hash.
3. **Handle results**:
   - **Success**: Data is intact.
   - **Failure**: Data has been modified (or corrupted).

#### **2.3 Security Considerations**
- **Collision Resistance**: Use cryptographically secure hashes (e.g., SHA-3, BLAKE3).
- **Pre-image Resistance**: Avoid weak hashes like MD5 for sensitive data.
- **Salt for Hashing**: If hashing passwords/secrets, **always** use a salt to prevent rainbow table attacks.

---

#### **2.4 Supported Algorithms**
| **Algorithm** | **Security Level** | **Use Case**                          | **Node.js Library**       | **Python Library**       |
|----------------|--------------------|---------------------------------------|---------------------------|--------------------------|
| SHA-256        | High               | General-purpose hashing               | `crypto.createHash('sha256')` | `hashlib.sha256()`      |
| SHA-3          | High               | Modern cryptographic applications      | `crypto.createHash('sha3-256')` | `hashlib.sha3_256()`    |
| BLAKE3         | High               | High-speed, memory-hard hashing        | `blake3-wasm` (browser)   | `blake3` (Python)       |
| MD5            | **Low (Avoid)**    | Legacy systems (not recommended)      | `crypto.createHash('md5')` | `hashlib.md5()`         |

---

### **3. Schema Reference**

#### **3.1 Input Schema (Hash Generation)**
| Field            | Type     | Required | Description                                  | Example                          |
|------------------|----------|----------|----------------------------------------------|----------------------------------|
| `algorithm`      | String   | Yes      | Hash algorithm (e.g., `"SHA-256"`).          | `"SHA-384"`                      |
| `input`          | String/Bytes | Yes    | Data to hash (file path, string, or binary). | `"user_data.bin"` or `byte[16]`   |
| `salt`           | String/Bytes | No     | Optional salt for password hashing.          | `"random_salt_123"`              |

**Example JSON Payload:**
```json
{
  "algorithm": "SHA-256",
  "input": "/path/to/file.txt",
  "salt": "optional_salt_value"
}
```

---

#### **3.2 Output Schema (Verification)**
| Field            | Type     | Description                                  | Example                          |
|------------------|----------|----------------------------------------------|----------------------------------|
| `algorithm`      | String   | Algorithm used.                              | `"SHA-256"`                      |
| `generated_hash` | String   | Newly computed hash.                        | `"a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"` |
| `stored_hash`    | String   | Precomputed hash for comparison.            | `"a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"` |
| `is_valid`       | Boolean  | `true` if hashes match; `false` otherwise.   | `true`                           |
| `error`          | String   | Optional error message (e.g., algorithm mismatch). | `"Algorithm mismatch: SHA-1 not supported"` |

**Example Response:**
```json
{
  "algorithm": "SHA-256",
  "generated_hash": "a591a6d4...",
  "stored_hash": "a591a6d4...",
  "is_valid": true
}
```

---

### **4. Query Examples**

#### **4.1 Generating a Hash (Node.js)**
```javascript
const crypto = require('crypto');
const fs = require('fs');

function generateHash(filePath, algorithm = 'sha256') {
  const data = fs.readFileSync(filePath);
  return crypto.createHash(algorithm).update(data).digest('hex');
}

const hash = generateHash('/path/to/file.txt', 'sha3-256');
console.log(hash);
```

#### **4.2 Verifying a Hash (Python)**
```python
import hashlib

def verify_hash(file_path, stored_hash, algorithm='sha256'):
    with open(file_path, 'rb') as f:
        data = f.read()
    new_hash = hashlib.new(algorithm, data).hexdigest()
    return new_hash == stored_hash

is_valid = verify_hash('user_data.bin', 'a591a6d4...', 'sha3-256')
print(f"Hash verified: {is_valid}")
```

#### **4.3 Integrating with APIs (REST)**
**Request (Verify File Hash):**
```
POST /verify/hash
Content-Type: application/json

{
  "algorithm": "BLAKE3",
  "input": "https://example.com/downloads/app.zip",
  "stored_hash": "1a2b3c..."
}
```

**Response (Success):**
```json
{
  "status": "success",
  "is_valid": true,
  "algorithm": "BLAKE3",
  "generated_hash": "1a2b3c..."
}
```

**Response (Failure):**
```json
{
  "status": "error",
  "error": "Hash mismatch: Expected 1a2b3c..., got 4d5e6f..."
}
```

---

### **5. Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                          |
|---------------------------|---------------------------------------------------------------------------------|------------------------------------------|
| **HMAC (Hash-based Message Authentication Code)** | Adds a key to hashing for integrity + authenticity (e.g., API request validation). | Secure communication channels.          |
| **Digital Signatures**    | Uses private/public keys to verify sender authenticity + data integrity.        | Cryptographic attestation (e.g., code signing). |
| **Cryptographic Checksums** | Similar to hashing but often used for error-detection (e.g., parity checks).   | Non-cryptographic data validation.      |
| **Zero-Knowledge Proofs (ZKPs)** | Proves knowledge of a value (e.g., password hash) without revealing it.        | Privacy-preserving authentication.       |
| **Blockchain Merkle Trees** | Efficiently verifies large datasets via hierarchical hashing.                | Distributed ledgers, data provenance.   |

---

### **6. Troubleshooting**
| **Issue**                          | **Root Cause**                          | **Solution**                              |
|-------------------------------------|----------------------------------------|-------------------------------------------|
| Hash mismatch                       | Input data altered or corrupted.       | Re-download/recompute hash.               |
| Unsupported algorithm               | Client/server uses incompatible hashes.| Standardize on SHA-3 or BLAKE3.            |
| Performance bottlenecks             | Large files or slow algorithms.        | Use BLAKE3 or parallel processing.         |
| Hash collision (extremely rare)     | Weak hash algorithm (e.g., MD5).       | Upgrade to SHA-3 or BLAKE3.               |

---

### **7. Best Practices**
1. **Prefer SHA-3 or BLAKE3** over legacy hashes (SHA-1, MD5).
2. **Store hashes securely** (e.g., in databases with access controls).
3. **Validate input sources** (e.g., ensure `input` data isn’t tampered with mid-transit).
4. **Log verification failures** for auditing (e.g., suspicious hashes may indicate attacks).
5. **Test edge cases** (empty files, binary data, Unicode strings).