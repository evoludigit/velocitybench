# **[Hashing Patterns] Reference Guide**

---

## **Overview**
**Hashing Patterns** are design strategies that leverage cryptographic or non-cryptographic hashing to improve security, performance, and data integrity in distributed systems. This pattern uses hash functions (e.g., SHA-256, MD5, MurmurHash) to transform input data into fixed-size outputs, enabling efficient indexing, deduplication, and secure storage of sensitive data.

Hashing is widely used for:
- **Data deduplication** (reducing storage/bandwidth)
- **Password storage** (via salted hashing)
- **Caching** (e.g., Redis key generation)
- **Distributed consensus** (e.g., IPFS, blockchain)
- **Authorization** (e.g., OAuth tokens)

This guide covers core implementation variants, key trade-offs, and practical examples.

---

## **Core Concepts & Schema Reference**

### **1. Hashing Patterns Variants**

| **Pattern**               | **Use Case**                          | **When to Apply**                          | **Implementation Notes**                                                                 |
|---------------------------|---------------------------------------|--------------------------------------------|-------------------------------------------------------------------------------------------|
| **Cryptographic Hashing** | Secure storage (e.g., passwords)      | High security requirements                 | Use SHA-256, bcrypt, or Argon2 (resistant to brute force)                               |
| **Non-Cryptographic Hashing** | Fast lookups (e.g., bloom filters)   | Performance-critical systems               | Use MurmurHash, CityHash for consistency; avoid collisions                                |
| **Consistent Hashing**    | Distributed data routing              | Scalable key-value stores (e.g., Cassandra)| Mitigates rebalancing overhead via virtual nodes                                       |
| **Preimage-Resistant Hashing** | Proof-of-work (e.g., mining)        | Energy-efficient validation                 | Use SHA-3 or BLAKE3 for modern PoW; avoid SHA-256 if CPU/GPU optimized                     |
| **Chaining Hashing**      | Secure hashing with multiple rounds   | High-security derivatives (e.g., HMAC)     | Combine with HMAC-SHA256 for keyed input hashing                                         |
| **Bloom Filter Hashing**  | Probabilistic deduplication           | Large-scale data checks                    | 3-5 hash functions per filter to minimize false positives                                |
| **Salting Hashing**       | Brute-force resistance                | Password storage                           | Use random salt per entry + iterations (e.g., bcrypt)                                     |

---

### **2. Schema Reference (Properties & Parameters)**

#### **Hashing Function Interface**
```typescript
interface HashFunction {
  /**
   * Transforms input into a hash (hex-encoded string).
   * @param input - Raw data (string, buffer, or ArrayBuffer).
   * @returns Hash string (e.g., "5f4dcc3b5aa765d61d8327deb882cf99").
   */
  hash(input: string | Buffer | ArrayBuffer): string;

  /**
   * Optionally supports salted hashing for passwords.
   * @param input - Raw data.
   * @param salt - Random bytes (e.g., 16 bytes for bcrypt).
   * @param iterations - Number of hashing rounds (e.g., 12 for bcrypt).
   * @returns Salted hash + salt (base64-encoded).
   */
  hashWithSalt?(input: string, salt: Buffer, iterations: number): string;

  /**
   * Verifies a salted hash against input.
   * @param input - Raw data.
   * @param storedHash - Existing salted hash (e.g., "$2a$12$...").
   * @returns Boolean.
   */
  verify?: (input: string, storedHash: string) => boolean;
}
```

#### **Supported Libraries**
| **Library**       | **Language** | **Hashing Variants**                          | **Notes**                                  |
|-------------------|-------------|-----------------------------------------------|---------------------------------------------|
| `bcrypt`          | Node.js     | Salted hashing (bcrypt)                       | Default: 12 iterations                     |
| `sha3`            | JS/Python   | SHA-3 family (SHA3-256, SHA3-512)              | Modern alternative to SHA-2                 |
| ` murmur3`        | C/Java      | Non-cryptographic (MurmurHash3_32)            | Fast, no collisions for most inputs        |
| `scrypt`          | Rust/Go     | Adaptive key derivation (scrypt)               | Slower than bcrypt but resistant to ASICs   |
| `lru_hash`        | Go          | Consistent hashing with LRU cache           | Built-in eviction policy                    |

---

## **Query Examples**

### **1. Cryptographic Hashing (Password Storage)**
**Use Case:** Securely store user passwords with salting.
```
javascript
const bcrypt = require('bcrypt');
const saltRounds = 12;

async function hashPassword(password) {
  const salt = await bcrypt.genSalt(saltRounds);
  const hash = await bcrypt.hash(password, salt);
  return hash; // "$2a$12$xYz..."
}

async function verifyPassword(password, storedHash) {
  return await bcrypt.compare(password, storedHash);
}
```

**Output:**
```
$2a$12$xYzABc1234567890!@#$%^&*()_+abcde
```

---

### **2. Consistent Hashing (Distributed Storage)**
**Use Case:** Distribute keys across nodes with minimal rebalancing.
```
python
from consistenthash import ConsistentHash
from hashlib import md5

# Create a ring with 3 nodes
ring = ConsistentHash(md5, "192.168.1.1:8080", "192.168.1.2:8080", "192.168.1.3:8080")
ring.add_node("192.168.1.4:8080")  # Virtual nodes for even distribution

# Get node for key "user:123"
node = ring.get("user:123")
print(node)  # Output: "192.168.1.1:8080"
```

---

### **3. Bloom Filter Hashing (Deduplication)**
**Use Case:** Probabilistically check if a key exists in a dataset.
```
java
import com.google.common.hash.BloomFilter;
import com.google.common.hash.Funnels;

BloomFilter<String> filter = BloomFilter.create(
  Funnels.stringFunnel(Charsets.UTF_8),
  10_000_000,  // Expected items
  0.01        // False positive rate
);

// Add/Check
filter.put("key123");
boolean exists = filter.mightContain("key123");  // true
```

---

### **4. Preimage-Resistant Hashing (Proof-of-Work)**
**Use Case:** Validate energy-intensive tasks (e.g., mining).
```
rust
use sha3::{Sha3_256, Digest};

fn mine(nonce: u64, target: &str) -> String {
  let mut hasher = Sha3_256::new();
  hasher.update(format!("{}{}", nonce, target));
  let hash = hasher.finalize();
  format!("{:x}", hash)
}

fn valid_hash(hash: &str, target: &str) -> bool {
  hash.starts_with(&target[..3]) // Simplified example
}
```

---

## **Implementation Trade-offs**

| **Decision Point**               | **Option A**                          | **Option B**                          | **Recommendation**                     |
|----------------------------------|---------------------------------------|---------------------------------------|----------------------------------------|
| **Security vs. Speed**           | SHA-3-512 (slow)                      | MurmurHash (fast)                      | Use SHA-3 for security; MurmurHash for caching. |
| **Salt Length**                  | 16 bytes (bcrypt)                     | 32 bytes                              | 16 bytes balances speed/safety.        |
| **Hash Collision Resistance**    | SHA-256                               | MurmurHash3                           | SHA-256 for critical data.             |
| **Keyed Hashing**                | HMAC-SHA256                            | Chaining (e.g., SHA256(SHA256(input))) | HMAC is more secure.                   |
| **Distributed Hashing**          | Consistent hashing (virtual nodes)    | Local hashing (e.g., modulo)          | Consistent hashing reduces rebalancing. |

---

## **Best Practices**

1. **For Passwords:**
   - Always use **bcrypt**, **Argon2**, or **PBKDF2**.
   - Store salts alongside hashes (e.g., `$2a$12$...` format).
   - Avoid **MD5/SHA-1** (vulnerable to rainbow tables).

2. **For Performance-Critical Hashing:**
   - Use **MurmurHash3** or **CityHash** for non-critical data.
   - Prefer **64-bit hashes** over 32-bit to reduce collisions.

3. **For Distributed Systems:**
   - Combine **consistent hashing** with **virtual nodes** for load balancing.
   - Use **SHA-256** for uniqueness in blockchain-like systems.

4. **Security:**
   - **Never** use hashing alone for encryption (use AES instead).
   - **Validate** hash implementations (e.g., fuzzing for edge cases).

---

## **Related Patterns**

| **Pattern**                     | **Connection to Hashing**                                                                 | **When to Pair**                          |
|---------------------------------|------------------------------------------------------------------------------------------|--------------------------------------------|
| **[Rate Limiting]**              | Use hash functions to distribute requests across time windows.                           | High-traffic APIs                          |
| **[Idempotency Keys]**           | Hash transaction IDs to ensure deduplication.                                           | Payment systems, microservices             |
| **[Circuit Breakers]**           | Hash metrics to sample system health (e.g., error rates).                               | Fault-tolerant architectures               |
| **[Bloom Filters]**              | Probabilistic membership checks using hashing.                                           | Large-scale caches (Redis, Bigtable)      |
| **[Consistent Prefix Hashing]**  | Extends consistent hashing for range-based queries.                                     | Time-series databases                      |
| **[Obfuscation]**                | Non-cryptographic hashing (e.g., for logging PII).                                     | Logging systems                            |

---
## **Further Reading**
- [OAuth 2.0 Token Hashing](https://datatracker.ietf.org/doc/html/rfc6749#section-7.1)
- [Consistent Hashing (Karger et al.)](https://www.cs.cmu.edu/~scytzer/papers/cuhk.pdf)
- [Bcrypt: Adaptive Hashing](https://cr.yp.to/docs/bcrypt/bcrypt.pdf)