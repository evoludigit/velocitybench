# **[Pattern Name] Hashing Setup Pattern – Reference Guide**

---

## **Overview**
The **Hashing Setup Pattern** defines a structured approach to configuring, storing, and managing cryptographic hash functions in distributed systems to enhance data integrity, security, and performance. It standardizes how hash algorithms (e.g., SHA-256, MD5) are initialized, applied, and verified across components, minimizing inconsistencies and reducing vulnerabilities.

This pattern is critical for:
- Ensuring deterministic hashing (same input → same hash).
- Preventing replay attacks via one-way hash functions.
- Optimizing storage (e.g., checksums for large files).
- Enforcing consistency in data validation (e.g., authentication tokens, passwords).

The pattern balances flexibility (supporting multiple algorithms) and enforceability (mitigating misconfigurations).

---

## **Key Concepts & Implementation Details**

### **1. Core Components**
| **Component**               | **Description**                                                                                     | **Example**                          |
|-----------------------------|-----------------------------------------------------------------------------------------------------|--------------------------------------|
| **Hash Algorithm Registry** | Centralized list of supported hash algorithms (e.g., `SHA-384`, `BLAKE2b`) with their parameters. | `{"sha256": { "blockSize": 64, "outputSize": 32 }}` |
| **Hash Generator**           | Module that computes hashes using the configured algorithm and input (e.g., text, binary data).    | `HashGenerator.generate("data", "sha256")` → `abc123...` |
| **Hash Verifier**            | Validates hashes against stored references (e.g., checksums, tokens).                               | `HashVerifier.verify("abc123...", "data", "sha256")` → `true` |
| **Key Derivation Function (KDF)*** | (Optional) Securely derives keys from passwords/secrets using hashing (e.g., **PBKDF2**, **Argon2**). | `KDF.derive("password", "salt", 10000)` → `key_material` |
| **Configuration Store**      | Persistent storage for algorithm-specific settings (e.g., salt lengths, iteration counts).        | Database/table: `hash_algorithms`    |

\* *KDFs are recommended for password hashing (see [Password Hashing Patterns](#related-patterns)).*

---

### **2. Hash Algorithm Selection**
| **Algorithm**       | **Use Case**                          | **Security Level** | **Output Size (bits)** | **Notes**                          |
|---------------------|---------------------------------------|--------------------|------------------------|------------------------------------|
| **SHA-256**         | General-purpose hashing (files, data). | High               | 256                    | FIPS 180-4 compliant.              |
| **SHA-512**         | High-security applications.           | Very High          | 512                    | Slower but more collision-resistant.|
| **BLAKE2b**         | Performance-critical scenarios.        | High               | Configurable           | Faster than SHA-256.               |
| **Bcrypt/Argon2**   | Password hashing (with KDFs).          | Very High          | Configurable           | Resistant to brute-force attacks.  |
| **MD5**\*           | Legacy systems (avoid for new use).   | Low                | 128                    | Insecure; use only for compatibility. |

\* *MD5 is deprecated due to collision vulnerabilities (e.g., [SHA-1 vs. MD5 attacks](#related-patterns)).*

---

### **3. Configuration Workflow**
#### **Step 1: Define Supported Algorithms**
Configure valid algorithms in the **Hash Algorithm Registry** (e.g., via config file or database).
**Example (JSON):**
```json
{
  "defaultAlgorithm": "sha256",
  "supportedAlgorithms": [
    {"name": "sha256", "enabled": true, "saltLength": 16},
    {"name": "blake2b", "enabled": true, "outputSize": 32}
  ]
}
```

#### **Step 2: Initialize Hash Generator**
Instantiate the generator with the target algorithm and parameters.
**Pseudocode:**
```python
hash_generator = HashGenerator(
  algorithm="sha256",
  salt=salt_generator.generate(16),  # 16-byte salt for SHA-256
  iterations=10000  # For KDFs like PBKDF2
)
```

#### **Step 3: Process Data**
Apply the hash to input data (e.g., file, string, binary).
**Example (File Hashing):**
```python
file_hash = hash_generator.compute(file_path="data.txt")
# Output: "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
```

#### **Step 4: Verify Hashes**
Compare computed hashes against stored references.
**Example (Token Validation):**
```python
is_valid = hash_verifier.verify(
  stored_hash="abc123...",
  input_data="user_token",
  algorithm="sha256"
)
```

#### **Step 5: Store Algorithm Metadata**
Log configuration details (e.g., algorithm, salt, iterations) for reproducibility.
**Example (Database Table):**
```sql
INSERT INTO hash_configs (algorithm, salt, iterations, created_at)
VALUES ('sha256', 'a1b2c3...', 10000, NOW());
```

---

## **Schema Reference**
### **1. `hash_algorithms` Table (Configuration Store)**
| **Field**          | **Type**    | **Description**                                      | **Example**               |
|--------------------|-------------|------------------------------------------------------|---------------------------|
| `algorithm_name`   | VARCHAR(32) | Name of the hash algorithm (e.g., `sha256`).          | `sha256`                  |
| `is_enabled`       | BOOLEAN     | Whether the algorithm is active.                     | `TRUE`                    |
| `salt_length`      | INTEGER     | Bytes of salt to generate (0 = no salt).            | `16`                      |
| `output_size_bits` | INTEGER     | Output hash size (e.g., 256 for SHA-256).            | `256`                     |
| `kdf_iterations`   | INTEGER     | iterations (for KDFs like PBKDF2).                   | `10000`                   |
| `created_at`       | TIMESTAMP   | When the algorithm was added.                        | `2023-10-01 12:00:00`     |

---

### **2. `hash_verifications` Table (Audit Log)**
| **Field**          | **Type**    | **Description**                                      | **Example**               |
|--------------------|-------------|------------------------------------------------------|---------------------------|
| `hash`             | VARCHAR(64) | The computed hash value.                             | `9f86d081884c7d659a2feaa0...` |
| `input_data_id`    | BIGINT      | References the original data (e.g., file ID).         | `12345`                   |
| `algorithm_used`   | VARCHAR(32) | Algorithm name (e.g., `sha512`).                     | `sha512`                  |
| `is_valid`         | BOOLEAN     | Result of verification (`TRUE`/`FALSE`).             | `TRUE`                    |
| `verified_at`      | TIMESTAMP   | When verification occurred.                          | `2023-10-01 12:05:00`     |

---

## **Query Examples**
### **1. List Enabled Algorithms**
```sql
SELECT algorithm_name, salt_length, output_size_bits
FROM hash_algorithms
WHERE is_enabled = TRUE;
```
**Output:**
| `algorithm_name` | `salt_length` | `output_size_bits` |
|------------------|---------------|--------------------|
| `sha256`         | `16`          | `256`              |
| `blake2b`        | `32`          | `32`               |

---

### **2. Verify a File Hash Against Stored Reference**
```sql
-- Step 1: Compute hash in application code (pseudocode)
file_hash = compute_sha256("data.txt");  // Returns "abc123..."

-- Step 2: Check if stored hash matches
SELECT is_valid =
  (hash = "abc123...") AND
  algorithm_used = "sha256"
FROM hash_verifications
WHERE input_data_id = 12345;
```

---

### **3. Update Algorithm Configuration**
```sql
-- Disable MD5 (deprecated)
UPDATE hash_algorithms
SET is_enabled = FALSE
WHERE algorithm_name = 'md5';

-- Enable BLAKE2b with custom output size
INSERT INTO hash_algorithms (algorithm_name, is_enabled, output_size_bits)
VALUES ('blake2b', TRUE, 512);
```

---

### **4. Audit Failed Verifications**
```sql
SELECT input_data_id, hash, algorithm_used, verified_at
FROM hash_verifications
WHERE is_valid = FALSE
ORDER BY verified_at DESC
LIMIT 10;
```

---

## **Error Handling & Edge Cases**
| **Scenario**                          | **Solution**                                                                 |
|----------------------------------------|------------------------------------------------------------------------------|
| Unsupported algorithm selected.        | Reject with `HashError("Algorithm not supported")`.                          |
| Collision detected (rare for SHA-256). | Fall back to SHA-512 or log as anomaly.                                     |
| Salt length mismatch.                  | Validate salt length against `salt_length` field in config.                  |
| KDF iterations too low.                | Enforce minimum iterations (e.g., 10,000 for PBKDF2).                        |
| Memory exhaustion (e.g., Argon2).      | Set resource limits (e.g., `memory_cost=65536`).                            |

---

## **Performance Considerations**
| **Factor**               | **Optimization Strategy**                                  |
|--------------------------|-----------------------------------------------------------|
| **Algorithm Choice**     | Prefer BLAKE2b for speed, SHA-512 for security-critical data. |
| **Parallel Processing**  | Hash large files in chunks (e.g., 64KB blocks for SHA-256). |
| **Caching**              | Cache frequent hashes (e.g., HTTP headers, API responses). |
| **Hardware Acceleration**| Use AES-NI or GPU-based hashing (e.g., CUDA) for bulk operations. |

---

## **Security Best Practices**
1. **Avoid MD5/SHA-1**: Use only SHA-256+, BLAKE2, or KDFs like Argon2.
2. **Salt Every Hash**: Prevent rainbow table attacks (even for SHA-256).
3. **Iterate for KDFs**: Add computational overhead (e.g., 10,000+ iterations).
4. **Immutable Configuration**: Store algorithm params in a read-only store.
5. **Regular Audits**: Scan for weak hashes (e.g., `hashcat` testing).

---

## **Related Patterns**
1. **[Password Hashing with KDFs]**
   - Extends hashing for passwords using **Argon2**, **PBKDF2**, or **bcrypt**.
   - *Key Difference*: Adds iterations, work factor, and memory limits to resist brute force.

2. **[Checksum Validation]**
   - Focuses on error detection (e.g., file integrity) using lightweight hashes (e.g., CRC32).
   - *Use Case*: Download verification, data transmission checks.

3. **[HMAC for Data Integrity]**
   - Combines hashing with a secret key (`HMAC-SHA256`) for message authentication.
   - *Use Case*: API requests, database record validation.

4. **[Secure Random Number Generation]**
   - Essential for generating cryptographically secure salts.
   - *Tools*: `/dev/urandom`, `secrets` (Python), `CSPRNG`.

5. **[Collision Resistance]**
   - Discusses attacks (e.g., **SHA-1 vs. MD5**) and modern defenses (e.g., **BLAKE3**).
   - *Resources*: [NIST SP 800-177](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-177r1.pdf).

---

## **Example Architectures**
### **1. Microservice Hashing Layer**
```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Client     │───(1)│  API Gateway │───(2)│  Hash Service │───(3)→ Database
└─────────────┘       └─────────────┘       └─────────────┘
                   │                           │
                   ▼                           ▼
              ┌─────────────┐          ┌─────────────┐
              │  File Cache │          │  Hash Config │
              └─────────────┘          └─────────────┘
```
- **(1)** Client sends data (e.g., file) to API Gateway.
- **(2)** API Gateway forwards to `Hash Service` (e.g., `Python`/`Go` backend).
- **(3)** Service stores hash + metadata in database.

### **2. Client-Side Hashing (e.g., Browser)**
```javascript
// Compute SHA-256 in browser using Web Crypto API
async function hashData(data) {
  const encoder = new TextEncoder();
  const dataBuffer = encoder.encode(data);
  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Usage
const fileHash = await hashData("user@example.com");
console.log(fileHash); // "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e"
```

---

## **Troubleshooting**
| **Issue**                          | **Diagnosis**                          | **Solution**                          |
|-------------------------------------|----------------------------------------|---------------------------------------|
| Hash mismatch between systems.      | Check for salt/algorithm inconsistencies. | Standardize config via `hash_algorithms` table. |
| Slow hashing (e.g., SHA-512).       | CPU-bound operations.                 | Use parallel processing or BLAKE2b.    |
| False negatives in verification.   | Data encoding differences (e.g., UTF-8 vs. ASCII). | Normalize input (e.g., UTF-8 always). |
| Storage bloat from long hashes.     | Large output sizes (e.g., SHA-512 = 64 bytes). | Use prefix hashes (e.g., first 16 bytes) for comparisons. |

---

## **Further Reading**
- [NIST SP 800-131A (Hash Functions)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131Ar1.pdf)
- [OWASP Hashing Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Hashing_Cheat_Sheet.html)
- [BLAKE3: A Faster, Simpler Alternative](https://blake3.readthedocs.io/)
- [SHA-1 Collision Attack Paper](https://www.schneier.com/blog/archives/2017/02/a_new_sha1_coll.html)