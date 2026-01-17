```markdown
---
title: "Hashing Anti-Patterns: What NOT to Do in Your Database and API Design"
date: 2023-11-05
author: David Chen
tags:
  - database-design
  - api-patterns
  - backend-engineering
  - hashing
  - security
---

# **Hashing Anti-Patterns: What NOT to Do in Your Database & API Design**

Hashing is a fundamental operation in backend systems—used for password storage, data integrity checks, deduplication, and caching. But hash functions are not perfect, and poor usage can lead to security vulnerabilities, performance bottlenecks, and logical errors.

In this guide, we’ll explore **hashing anti-patterns**—common mistakes that developers make when working with hashing in databases and APIs. We’ll analyze why they’re problematic, provide practical examples, and offer solutions to avoid them.

---

## **Introduction: Why Hashing Matters (and Why It’s Tricky)**

Hashing is everywhere in backend engineering:

- **Password storage**: Never store plaintext passwords. Always use cryptographic hashes (e.g., bcrypt, Argon2).
- **Data integrity**: Checksums ensure files or database records haven’t been tampered with.
- **Deduplication**: Hashing documents (e.g., MD5 of JSON) helps identify duplicates.
- **Caching**: Distributed caches (Redis, Memcached) rely on hash-based key lookups.

But hashing is **not** a silver bullet. Misusing it can:
✅ **Break security** (e.g., using SHA-1 for passwords).
✅ **Bloat your database** (e.g., storing large hashes unnecessarily).
✅ **Create performance bottlenecks** (e.g., poor hash distribution).
✅ **Introduce logical errors** (e.g., incorrect collision handling).

This guide will help you **avoid these pitfalls** and design robust hashing strategies.

---

## **The Problem: Common Hashing Anti-Patterns**

### **1. Using Weak Hash Functions**
**Problem:**
Some developers still use **SHA-1, MD5, or CRC32** for security-sensitive operations (like password storage). These functions:
- Have **collision vulnerabilities** (SHA-1 broken in 2023).
- Are **fast but not secure** (MD5 is cryptographically broken).
- **Do not support salting** (unlike bcrypt or Argon2).

**Example of a Bad Practice:**
```python
import hashlib

def store_password_bad(password: str) -> str:
    # ❌ SHA-1 is broken and not secure for passwords
    return hashlib.sha1(password.encode()).hexdigest()
```

**Why it’s dangerous:**
An attacker could create a **rainbow table** to crack the password quickly.

---

### **2. Storing Hashes Without Salting**
**Problem:**
Even if you use a strong hash function (like bcrypt), **not salting passwords** makes them vulnerable to precomputed attacks.

**Example of Missing Salting:**
```python
# ❌ No salt, same password → same hash
def hash_password_saltless(password: str) -> str:
    salt = "default"  # Hardcoded salt (bad practice)
    return hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
```

**Why it’s risky:**
Two users with the same password will generate the same hash, making it easier for attackers to guess.

---

### **3. Hashing Sensitive Data for Deduplication**
**Problem:**
Some teams **hash sensitive fields** (like emails or credit cards) to "protect" them. But hashing:
- Is **not reversible** (you can’t retrieve the original data).
- **Doesn’t provide encryption** (hashing is one-way, not secure storage).
- Can **leak data via collisions** (two different inputs → same hash).

**Example of Bad Deduplication:**
```sql
-- ❌ Hashing PII (Personally Identifiable Info) is not a privacy solution
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email_hash VARCHAR(255) NOT NULL,
    -- Other fields...
);

-- Store raw email, then hash it
INSERT INTO users (email_hash)
VALUES (hash(email_column));
```

**Why it’s wrong:**
- **Not secure**: If breached, hashed emails can still be identified.
- **Not useful**: You can’t verify correctness later.

---

### **4. Using MD5 or SHA-1 for Integrity Checks**
**Problem:**
While **MD5/SHA-1 are fast**, they are **not collision-resistant** for security purposes. New attacks (e.g., **SHA-1 collision attacks**) can forge documents.

**Example of a Bad Integrity Check:**
```python
import hashlib

def verify_file_integrity_bad(file_path: str) -> bool:
    # ❌ SHA-1 is broken for integrity checks
    known_hash = "abc123..."
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha1(f.read()).hexdigest()
    return file_hash == known_hash
```

**Better Alternatives:**
- Use **SHA-256 or SHA-3** for integrity checks.
- For critical data (e.g., firmware), use **HMAC with a secret key**.

---

### **5. Overusing Hashes in Indexes**
**Problem:**
Some developers **store hashes in database columns** to save space, but this can:
- **Slow down queries** (hash functions are CPU-intensive).
- **Cause unexpected behavior** (different inputs → same hash).

**Example of Poor Indexing:**
```sql
-- ❌ Storing hashes slows down lookups
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_name_hash VARCHAR(64),  -- 🚩 Bad for filtering
    price DECIMAL(10, 2)
);

-- Query: Find products by name (but we hashed it!)
SELECT * FROM products WHERE product_name_hash = hash('Laptop');
```

**Why it’s bad:**
- **No inverse lookup**: You can’t easily find all products with a given hash.
- **Performance hit**: Hashing every row on insert/update.

---

### **6. Not Handling Hash Collisions Properly**
**Problem:**
Hash collisions (two inputs → same hash) are inevitable. If unhandled, they can:
- **Cause duplicate data** (e.g., two emails → same hash).
- **Break deduplication logic**.

**Example of Collision-Prone Deduplication:**
```python
def is_duplicate(email1: str, email2: str) -> bool:
    # ❌ Collisions can happen!
    return hashlib.sha256(email1.encode()).hexdigest() == hashlib.sha256(email2.encode()).hexdigest()
```

**Solution:**
- Use **a stronger hash (SHA-3 or BLAKE3)**.
- Accept that collisions are rare but possible.

---

## **The Solution: Hashing Best Practices**

| **Anti-Pattern**               | **Correct Approach**                          | **Example** |
|---------------------------------|-----------------------------------------------|-------------|
| Weak hash (SHA-1, MD5)         | Use bcrypt/Argon2 for passwords, SHA-256/3 for integrity | `bcrypt.hash(password)` |
| No salting                     | Always use a unique salt per password        | `bcrypt.hash(password + salt)` |
| Hashing PII for deduplication  | Use **deterministic encryption (e.g., AWS KMS)** | `kms.encrypt(email)` |
| Storing hashes in indexes      | Store original data + index on it            | `CREATE INDEX ON users(email)` |
| Not handling collisions        | Use a probabilistic data structure (Bloom Filter) | `bloom_filter.lookup(email)` |

---

## **Implementation Guide: How to Fix Common Mistakes**

### **1. Secure Password Hashing (bcrypt + Salt)**
```python
import bcrypt

def hash_password_safe(password: str) -> str:
    # ✅ bcrypt with automatic salting
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password_safe(stored_hash: str, input_password: str) -> bool:
    # ✅ Compare hash with input
    return bcrypt.checkpw(input_password.encode(), stored_hash.encode())
```

### **2. Proper Data Integrity Checks (SHA-3)**
```python
import hashlib

def calculate_integrity_hash(data: bytes) -> str:
    # ✅ SHA-3 is collision-resistant
    return hashlib.sha3_256(data).hexdigest()
```

### **3. Deduplication Without Hashing PII**
```sql
-- ✅ Store original PII but create a searchable deduplication key
ALTER TABLE emails ADD COLUMN deduplication_key UUID NOT NULL DEFAULT gen_random_uuid();

-- Alternatively, use a deterministic function (PostgreSQL example)
CREATE EXTENSION IF NOT EXISTS pgcrypto;
ALTER TABLE emails ADD COLUMN email_digest BYTEA
GENERATED ALWAYS AS (encode(digest(email, 'sha256'), 'hex')) STORED;
```

### **4. Avoiding Hash Collisions (Bloom Filters)**
```python
# Using a library like 'pybloom_live' to handle collisions gracefully
from pybloom_live import ScalableBloomFilter

def is_possible_duplicate(email: str) -> bool:
    bloom = ScalableBloomFilter(capacity=1000000, error_rate=0.001)
    if bloom.contains(email):
        return True  # Possible duplicate, verify manually
    bloom.add(email)
    return False
```

---

## **Common Mistakes to Avoid**

### ❌ **Using MD5/SHA-1 for Anything Security-Related**
- **Fix:** Use bcrypt (passwords), SHA-256/3 (integrity), or BLAKE3 (general hashing).

### ❌ **Not Salting Passwords**
- **Fix:** Always use `bcrypt.gensalt()` or `Argon2`.

### ❌ **Hashing Sensitive Data for Privacy**
- **Fix:** Use **encryption (AES) with proper key management** instead.

### ❌ **Storing Hashes Instead of Original Data**
- **Fix:** Keep original data + hash for integrity checks, but **never lose the original**.

### ❌ **Ignoring Hash Collisions**
- **Fix:** Accept that collisions happen; use probabilistic structures (Bloom Filters) to handle them.

---

## **Key Takeaways**
✅ **Use strong hashing algorithms** (bcrypt for passwords, SHA-3 for data integrity).
✅ **Always salt passwords** (never reuse salts).
✅ **Never hash PII for deduplication** (use encryption or deterministic keys).
✅ **Avoid storing hashes in indexes** (store original data + index).
✅ **Handle collisions gracefully** (Bloom Filters, manual verification).
✅ **Test hashing functions** (e.g., SHA-1 collision attacks).

---

## **Conclusion: Hashing Right Matters**
Hashing is a powerful tool, but **misusing it can lead to security breaches, data corruption, and performance issues**. By avoiding these anti-patterns and following best practices, you can ensure your database and API designs remain **secure, efficient, and reliable**.

### **Final Checklist Before Deploying:**
- [ ] Are passwords stored with bcrypt/Argon2 + salting?
- [ ] Are integrity checks using SHA-3 or better?
- [ ] Is PII encrypted, not hashed?
- [ ] Are hash collisions handled (e.g., Bloom Filters)?
- [ ] Are hashes not used in indexes?

Now go forth and hash **correctly**!

---
**Author Bio:**
David Chen is a Senior Backend Engineer with 10+ years of experience in database design and API security. He’s written extensively on security patterns and has led teams implementing scalable hashing solutions for fintech and healthcare.

🔗 **Further Reading:**
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [NIST Guidelines on Hash Functions](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-131A.pdf)
```

---
**Why this works:**
1. **Clear structure** – Separates problems, solutions, and code.
2. **Practical examples** – Shows bad vs. good implementations.
3. **Honest tradeoffs** – Acknowledges that hashing isn’t perfect (collisions, etc.).
4. **Actionable checklist** – Helps developers self-audit their code.
5. **Professional yet friendly** – Explains complexity without sugarcoating.

Would you like any refinements (e.g., more focus on APIs, different languages)?