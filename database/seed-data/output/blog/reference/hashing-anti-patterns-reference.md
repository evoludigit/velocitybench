# **[Anti-Pattern] Hashing Pitfalls – Reference Guide**

---

## **Overview**
Hashing is a fundamental technique for data integrity, caching, and lookup optimization, but improper implementation leads to critical vulnerabilities or inefficiencies. This guide outlines **common hashing anti-patterns**—misapplications that degrade performance, compromise security, or violate design principles. Understanding these pitfalls ensures robust, maintainable, and secure systems.

Key risks include:
- **Collision attacks** (weak/universal hash functions).
- **Timing-side channels** (predictable hash computation).
- **Memory exhaustion** (caching collisions).
- **Over-reliance on cryptographic hashes** (when non-cryptographic suffices).

---

## **Schema Reference**
Anti-patterns are categorized by their technical impact:

| **Anti-Pattern**               | **Description**                                                                                     | **Risk Level** | **Affected Layers**       | **Mitigation Strategy**                                  |
|----------------------------------|-----------------------------------------------------------------------------------------------------|-----------------|----------------------------|----------------------------------------------------------|
| **1. Universal Hashing**         | Using a single, non-cryptographic hash (e.g., MD5) for security-sensitive data (passwords, tokens). | High            | Security, Persistence      | Replace with cryptographic hashes (e.g., SHA-3, bcrypt). |
| **2. Hash Collision Exploitation** | Ignoring collision probability in non-cryptographic hashes (e.g., using `String.hashCode()` for IDs). | Medium          | Data Integrity, Caching    | Use cryptographic hashes + salting; validate collision handling. |
| **3. Timing Attacks**            | Revealing internal state via measurable hash computation time (e.g., brute-force password checks).   | High            | Security, Authentication   | Constant-time algorithms (e.g., bcrypt, Argon2).        |
| **4. Over-Salting**              | Applying redundant salting to hashes (e.g., multiple salts per user).                               | Low             | Performance, Security      | Use one unique salt per user; derive from context.       |
| **5. Hashing Sensitive Data**    | Storing plaintext data alongside hashes (e.g., logging both `password` and `hashed_password`).     | High            | Security, Compliance       | Store only hashes; use field-level encryption if needed. |
| **6. Chaining for Caching**      | Using linked-list chaining for hash tables without resizing, leading to O(n) lookups.               | Medium          | Performance, Caching       | Implement dynamic resizing (e.g., 75%/25% load factor). |
| **7. Insecure Hashing Parameters** | Fixed iterations/key lengths (e.g., SHA-1 with 10 rounds instead of 1,000+).                       | High            | Security                    | Follow NIST/SHA-3 guidelines; use key stretching.        |
| **8. Hash-Based Authentication** | Relying solely on hash verification (e.g., comparing `SHA-256(password)` directly).                 | Critical        | Authentication             | Use HMAC + nonces or password-based key derivation (PBKDF2). |
| **9. Ignoring Input Size**       | Processing arbitrarily large inputs (e.g., files) via hash functions without bounds.                 | Medium          | Performance, Security      | Enforce size limits; truncate or reject oversized inputs. |
| **10. Hash Leakage**             | Exposing derived hashes (e.g., logging `hashed_user_id` when `user_id` could be inferred).          | High            | Security, Privacy          | Mask or redirect to IDs; avoid reversible derivations.   |

---

## **Query Examples & Anti-Pattern Analysis**

### **Scenario 1: Password Storage**
❌ **Anti-Pattern:**
```sql
-- Vulnerable: Plain MD5 without salt
SELECT * FROM users WHERE MD5(password) = 'a1b2c3...';
```
**Problem:** MD5 is reversible; salts are omitted. An attacker could precompute rainbow tables.

✅ **Mitigation:**
```sql
-- Secure: bcrypt with per-user salt
SELECT * FROM users WHERE bcrypt(password, '$2a$12$saltstring$hashvalue') = '...';
```

### **Scenario 2: Database Indexing**
❌ **Anti-Pattern:**
```sql
-- Using non-cryptographic hash for primary keys (e.g., `user_id_hash`)
-- Collisions may violate uniqueness constraints.
CREATE TABLE users (
    user_id_hash VARCHAR(32) PRIMARY KEY,
    -- ...
);
```
**Problem:** `String.hashCode()` collisions are possible; primary keys must be unique.

✅ **Mitigation:**
```sql
-- Use UUIDs or auto-increment IDs instead of hashes.
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_hash VARCHAR(64)  -- Store hash separately for lookup.
);
```

### **Scenario 3: Timing Attack Vulnerability**
❌ **Anti-Pattern:**
```python
# Vulnerable: Checks hash sequentially (timing leak)
def check_password(plaintext, stored_hash):
    return hmac.compare_digest(plaintext, stored_hash)  # Still timing-effective
```
**Problem:** Attackers can measure computation time to guess passwords.

✅ **Mitigation:**
```python
# Constant-time comparison
def verify_password(plaintext, stored_hash):
    return secrets.compare_digest(plaintext.encode(), stored_hash.encode())
```

### **Scenario 4: Cache Collision Flooding**
❌ **Anti-Pattern:**
```java
// Fixed-size cache with no resizing
HashMap<String, Object> cache = new HashMap<>(1000);  // 1k buckets
// Attacker submits 10k entries with same hash → O(10) lookups.
```
**Problem:** O(n) lookup times degrade performance under collision attacks.

✅ **Mitigation:**
```java
// Dynamic resizing (e.g., Java’s default resize threshold)
HashMap<String, Object> cache = new HashMap<>();
cache.computeIfAbsent("key", k -> new Object());  // Auto-resizes as needed.
```

---

## **Related Patterns**
To counter hashing anti-patterns, adopt these complementary strategies:

| **Pattern**                  | **Purpose**                                                                                     | **When to Use**                                                                 |
|------------------------------|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Cryptographic Hashing**    | Secure data integrity (e.g., SHA-3, BLAKE3)                                                     | Authentication, signing, nonces.                                               |
| **Password-Based Key Derivation (PBKDF2, Argon2)** | Slow hashing for passwords to resist brute force.                                           | User authentication systems.                                                   |
| **Salting**                  | Protects against rainbow table attacks by adding unique data per hash.                          | Storing passwords, tokens.                                                     |
| **HMAC**                     | Authenticates messages with a shared secret (e.g., `hmac-sha256`).                           | API signatures, data validation.                                               |
| **Bloom Filters**            | Probabilistic membership testing (e.g., for cache hit/miss).                                  | Large datasets with low false-positive tolerance (e.g., spell checkers).        |
| **Deterministic Equivalent (DE)** | Replaces cryptographic hashes with predictable, reversible derivations (e.g., `SHA-256`) for IDs. | Legacy systems needing reproducible IDs.                                      |
| **Key Stretching**           | Extends hash computation time to defend against GPU/ASIC attacks (e.g., bcrypt).               | High-security passwords (e.g., banking).                                     |

---

## **Best Practices Summary**
1. **Security:**
   - Use **cryptographic hashes** (SHA-3, BLAKE3) for sensitive data.
   - **Never** use MD5, SHA-1, or non-cryptographic hashes for passwords.
   - Employ **constant-time comparison** (e.g., `secrets.compare_digest`).
2. **Performance:**
   - **Resize hash tables** dynamically to avoid collisions.
   - **Profile hash functions** under workload to detect bottlenecks.
3. **Design:**
   - Store **only hashes**, not plaintext or derivation steps.
   - Use **salts** for uniqueness but avoid over-salting.
4. **Testing:**
   - Verify **collision resistance** in non-cryptographic hashes.
   - Test for **timing attacks** in authentication flows.

---
**Final Note:** Hashing anti-patterns often stem from misunderstanding trade-offs between speed, security, and scalability. Prioritize **defense-in-depth**: combine cryptographic hashing with salting, constant-time checks, and principle-of-least-privilege storage. Always review hashing implementations with tools like **OWASP ZAP** or **hashcat** for vulnerabilities.