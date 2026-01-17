# **[Pattern] Hashing Approaches – Reference Guide**

---

## **Overview**
The **Hashing Approaches** pattern provides standardized ways to transform input data into fixed-size, deterministic hash values. Hashing is critical for data integrity checks, caching, deduplication, and secure data storage (e.g., password hashing). This pattern ensures consistency across implementations while allowing flexibility for specific use cases like collision resistance, performance, or memory constraints.

Key benefits include:
- **Data consistency**: Guaranteed identical output for identical input.
- **Efficiency**: Fast lookups, comparisons, and storage.
- **Security**: Resistance to reverse-engineering (e.g., salted hashing).
- **Compatibility**: Clear interfaces for integration with other patterns (e.g., **Serialization**, **Data Validation**).

---

## **Key Concepts**
Hashing approaches vary by **purpose**, **collision resistance**, and **performance**. Common implementations include:

| **Term**               | **Definition**                                                                 | **Example Use Cases**                          |
|------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **Hash Function**      | Algorithm that maps input to a fixed-size string (e.g., SHA-256).            | File integrity checks, checksums.            |
| **Salt**              | Randomized string prepended to input to mitigate rainbow table attacks.      | Password storage.                              |
| **Deterministic**     | Same input → same output (repeatable).                                        | Deduplication, caching.                       |
| **Collision Resistance** | Low probability of two inputs producing the same hash.                       | Cryptographic applications.                  |
| **Hashing Strategy**   | Rule for selecting a hash function/salt combination (e.g., "SHA-256 with salt"). | Enforced via API contracts.                   |

---

## **Schema Reference**
### **1. Hash Function Configurations**
Define supported hash functions and their properties.

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                     |
|-------------------------|----------------|-------------------------------------------------------------------------------|----------------------------------------|
| `function`              | `string`       | Name of the hash algorithm (e.g., MD5, SHA-1).                              | `"SHA-256"`, `"BLAKE3"`                |
| `outputLength`          | `integer`      | Bit length of the hash output.                                                | `256`, `512`                           |
| `collisionResistant`   | `boolean`      | Flag indicating resistance to collisions (cryptographic-grade only).          | `true` (SHA-256), `false` (MD5)        |
| `performanceProfile`    | `enum`         | Optimization priority (speed, memory, or security).                          | `"speed"`, `"memory-efficient"`        |

**Example Schema:**
```json
{
  "hashFunctions": [
    {
      "function": "SHA-256",
      "outputLength": 256,
      "collisionResistant": true,
      "performanceProfile": "security"
    },
    {
      "function": "MD5",
      "outputLength": 128,
      "collisionResistant": false,
      "performanceProfile": "speed"
    }
  ]
}
```

---

### **2. Hashing Strategies**
Describe how to apply hashing in practice (e.g., with/without salt).

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                     |
|-------------------------|----------------|-------------------------------------------------------------------------------|----------------------------------------|
| `strategyName`          | `string`       | Identifier for the strategy (e.g., "plaintext_hash", "salted_hash").         | `"SHA256_SALTED"`                      |
| `usesSalt`              | `boolean`      | Whether the strategy includes random salts.                                  | `true`                                 |
| `saltLength`            | `integer`      | Length of the salt in bytes (if applicable).                                 | `16`, `32`                             |
| `hashFunction`          | `reference*`   | Reference to the `hashFunctions` schema above.                              | `"SHA-256"`                            |
| `iterationCount`        | `integer`      | Number of hashing rounds (e.g., for key derivation).                         | `1000` (PBKDF2), `null` (single-step) |

**Example Schema:**
```json
{
  "strategies": [
    {
      "strategyName": "SHA256_SALTED",
      "usesSalt": true,
      "saltLength": 16,
      "hashFunction": "SHA-256",
      "iterationCount": 1000
    },
    {
      "strategyName": "BLAKE3_PLAINTEXT",
      "usesSalt": false,
      "saltLength": null,
      "hashFunction": "BLAKE3"
    }
  ]
}
```

---

### **3. Input/Output Contracts**
Define how data is transformed via hashing.

| **Field**               | **Type**       | **Description**                                                                 | **Example Values**                     |
|-------------------------|----------------|-------------------------------------------------------------------------------|----------------------------------------|
| `inputType`             | `string`       | Format of the input (e.g., plaintext, serialized JSON).                       | `"text"`, `"binary"`                   |
| `outputFormat`          | `string`       | How the hash is returned (hex string, base64).                               | `"hex"`, `"base64"`                    |
| `strategyRef`           | `string`       | Reference to a `strategyName` from above.                                     | `"SHA256_SALTED"`                      |

**Example Schema:**
```json
{
  "hashingContract": {
    "inputType": "text",
    "outputFormat": "hex",
    "strategyRef": "SHA256_SALTED"
  }
}
```

---

## **Implementation Details**

### **1. Core Hashing Algorithm**
Use a cryptographically secure hash function (e.g., SHA-256, BLAKE3) for security-sensitive data. Avoid legacy hashes like MD5/SHA-1 due to collision vulnerabilities.

**Pseudocode (Generic):**
```python
def hash_input(input_data: bytes, strategy: dict) -> str:
    if strategy["usesSalt"]:
        salt = generate_random_salt(strategy["saltLength"])
        input_with_salt = salt + input_data
        if strategy["iterationCount"]:
            for _ in range(strategy["iterationCount"]):
                input_with_salt = hash_function(input_with_salt)
    else:
        input_with_salt = input_data
    hash_result = hash_function(strategy["hashFunction"], input_with_salt)
    return format_output(hash_result, strategy["outputFormat"])
```

---

### **2. Handling Edge Cases**
- **Empty Input**: Return a predefined hash (e.g., `"d41d8cd98f00b204e9800998ecf8427e"` for SHA-256 of `""`).
- **Non-UTF-8 Text**: Encode input to UTF-8 before hashing.
- **Large Data**: Process in chunks (e.g., for file hashing) using a rolling hash.

---

### **3. Salt Management**
- **Storage**: Store salts alongside hashes (e.g., in a database column).
- **Versioning**: Include salt length/format in the hashing strategy to avoid compatibility issues.

**Example Salt Storage:**
```json
{
  "hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
  "salt": "d1b1c2d3e4f5a6b7c8d9e0f1",
  "strategy": "SHA256_SALTED"
}
```

---

## **Query Examples**
### **1. Hashing a String (Deterministic)**
**Input:**
```json
{
  "data": "password123",
  "strategy": "SHA256_SALTED"
}
```
**Output:**
```json
{
  "hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
  "salt": "7f8a2b1c3d4e5f6a7b8c9d0e1f2a3b4c",
  "saltedInput": "7f8a2b1c3d4e5f6a7b8c9d0e1f2a3b4cc2f8b2b1d5d88e9515c2f256d08e945c8"
}
```

---

### **2. File Hashing (Chunked)**
**Input:**
```python
hashing_strategy = {"function": "MD5", "outputFormat": "hex"}
with open("large_file.txt", "rb") as f:
    hash_result = chunked_hash(f.read(), hashing_strategy)
```
**Output:**
```
"d41d8cd98f00b204e9800998ecf8427e"  # For an empty file
```

---

### **3. Schema Validation**
Validate input/output against the defined contracts:
```json
// Validate a hash output
{
  "inputType": "text",
  "outputFormat": "hex",
  "strategyRef": "SHA256_SALTED"
}
```
**Rule:** Reject if `outputFormat` ≠ `"hex"` or `strategyRef` is invalid.

---

## **Query Language Examples**
### **SQL-like Hash Calculation**
```sql
-- Pseudocode for a database view
SELECT
  sha256_concat(salt, input_data) AS hashed_value,
  salt,
  "SHA256_SALTED" AS strategy
FROM users;
```

### **Programmatic Integration (Python)**
```python
from Cryptodome.Hash import SHA256, BLAKE3
from Cryptodome.Random import get_random_bytes

def apply_strategy(data: str, strategy: dict) -> dict:
    if strategy["strategyName"] == "BLAKE3_PLAINTEXT":
        return {
            "hash": BLAKE3.new(data.encode()).hexdigest(),
            "salt": None
        }
    elif strategy["strategyName"] == "SHA256_SALTED":
        salt = get_random_bytes(strategy["saltLength"])
        h = SHA256.new(salt + data.encode()).hexdigest()
        return {"hash": h, "salt": salt.hex()}
```

---

## **Error Handling**
| **Error**                     | **Code**       | **Description**                                                                 | **Solution**                                  |
|-------------------------------|----------------|-------------------------------------------------------------------------------|----------------------------------------------|
| `InvalidHashFunction`         | `400`          | Unsupported hash algorithm (e.g., "RSA").                                     | Use `SHA-256`/`BLAKE3` instead.              |
| `SaltMismatch`                | `403`          | Provided salt doesn’t match expected length/strategy.                       | Regenerate salt or update strategy.          |
| `InputTooLarge`               | `413`          | Input exceeds chunking limits (e.g., >1MB).                                | Process in smaller chunks.                   |
| `CollisionDetected`           | `422`          | Hash collision with existing record (rare, but possible with non-crypto hashes). | Use a stronger hash function.                |

---

## **Performance Considerations**
| **Strategy**               | **Speed**       | **Memory**      | **Use Case**                          |
|----------------------------|-----------------|-----------------|---------------------------------------|
| SHA-256 (no salt)          | High            | Low             | Checksums, caching.                    |
| SHA-256 + Salt (1 round)   | Medium          | Low             | Password storage.                     |
| Argon2id (key derivation)  | Low             | High            | Secure password hashing.              |

**Optimizations:**
- **Caching**: Precompute hashes for static data.
- **Parallelism**: Hash independent chunks concurrently (e.g., for files).
- **Hardware Acceleration**: Use GPU/FPGA for bulk hashing.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Integration Point**                          |
|---------------------------|-------------------------------------------------------------------------------|-----------------------------------------------|
| **[Serialization]**       | Convert complex data to a hashable format (e.g., JSON → bytes).              | Input preprocessing.                         |
| **[Data Validation]**     | Ensure input meets hashing requirements (e.g., UTF-8 encoding).             | Pre-hash validation.                          |
| **[Key Derivation]**      | Extend hashing for cryptographic keys (e.g., PBKDF2, bcrypt).               | When `iterationCount` > 1.                    |
| **[Caching]**             | Store hashes to avoid recomputation (e.g., ETAGs for HTTP responses).        | Output caching.                               |
| **[Audit Logging]**       | Record hash operations for traceability.                                    | Post-hash logging.                            |

---

## **Example Workflow**
1. **Validate Input**: Ensure data is UTF-8 encoded.
2. **Select Strategy**: Choose `SHA256_SALTED` for passwords.
3. **Generate Salt**: Create a 16-byte random salt.
4. **Hash**: Concatenate salt + input → SHA-256 → hex.
5. **Store**: Save `(hash, salt, strategy)` to database.
6. **Verify**: Recompute hash during login and compare.

---
**References:**
- [RFC 4648](https://tools.ietf.org/html/rfc4648) (Base64)
- [NIST SP 800-131A](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131A.pdf) (Key Derivation)
- [Python `cryptography` lib](https://cryptography.io/) for implementations.