```markdown
---
title: "Hashing Gotchas: The Secrets No Beginner Backend Developer Should Miss"
date: 2023-11-15
author: "Alex Carter"
tags: ["database", "api", "security", "hashing", "backend", "patterns"]
---

# Hashing Gotchas: The Secrets No Beginner Backend Developer Should Miss

![Hashing illustration](https://images.unsplash.com/photo-1633356122479-f531f0b994f1?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80)

Hashing is a fundamental tool in backend development—used everywhere from password storage to data integrity checks. But here’s the catch: **hashing isn’t magic**. Done wrong, it can turn into a security nightmare or a frustrating bug waiting to happen.

As a backend beginner, you’ve probably heard “always hash passwords” or “use SHA-256.” But real-world applications require deeper considerations. This guide dives into the **common gotchas** that trip up even experienced developers, with practical examples and code snippets to help you avoid them.

---

## The Problem: Why Hashing Is Tricky

Hashing is the process of converting data into a fixed-size, unique(ish) string of characters. It’s used for:

- Securely storing passwords (never store plaintext!)
- Checking data integrity (e.g., checksums)
- Distributed systems (e.g., caching keys)

But hashing is **deterministic** (same input = same output) and **one-way** (you can’t reverse it). This simplicity hides critical tradeoffs:

1. **Collision risks**: Two different inputs can produce the same hash (the birthday problem).
2. **Performance vs. security**: Fast hashes are vulnerable to brute-force attacks.
3. **Salt myths**: Salt isn’t just sprinkled—it’s carefully managed.
4. **Cryptographic vs. checksum hashes**: Using the wrong hash function for security is like locking your bike with a paperclip.
5. **API design pitfalls**: Hashing in transit (e.g., API keys) has entirely different rules.

### Real-World Example: The Equifax Breach
In 2017, Equifax’s data breach exposed millions of records—partly because they used **MD5**, a hash function **known to be cryptographically broken** for security (but still used for checksums). The lesson? Always match your use case to the right hash.

---

## The Solution: Best Practices for Hashing in Backend Code

Hashing isn’t a single tool but a **pattern** with multiple components. Here’s how to design it right:

### 1. **Use Cryptographic Hash Functions**
For security (passwords, tokens), use **slow, secure** hashes like:
- **bcrypt** (with adaptive cost factor)
- **Argon2** (winner of the Password Hashing Competition)
- **PBKDF2** (with HMAC-SHA256)

For checksums (data integrity), use **fast but collision-resistant** hashes:
- **SHA-256** (256-bit)
- **SHA-3** (Keccak-based)

> **⚠️ Avoid:** MD5, SHA-1, or older hashes like **SHA-0**. They’re obsolete for security.

---

### 2. **Always Salt Passwords**
Salting prevents rainbow table attacks by adding randomness. Here’s how to do it right:

#### Example: Secure Password Hashing in Python (with `bcrypt`)
```python
import bcrypt

def hash_password(password: str, salt: bytes = None) -> tuple[str, bytes]:
    """Hash a password with bcrypt and return (hash, salt)."""
    if salt is None:
        salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8"), salt

def verify_password(password: str, hashed: str, salt: bytes) -> bool:
    """Verify a password against a stored hash+salt."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
```

#### Example: In PostgreSQL (using `pgcrypto`)
```sql
-- Insert with salt
INSERT INTO users (username, password_hash, salt)
VALUES ('alice', crypt('secret123', gen_salt('bf')), gen_salt('bf'));

-- Verify
SELECT crypt('secret123', password_hash) = password_hash FROM users WHERE username = 'alice';
```

---

### 3. **Adjust Hash Costs Dynamically**
Modern hashes (bcrypt, Argon2) let you tweak **computational cost** to slow down brute-force attacks.

#### Example: Adjusting bcrypt’s Work Factor
```python
# Hash with cost factor 12 (adjust based on threat model)
salt = bcrypt.gensalt(rounds=12)
```

> **🔹 Tradeoff:** Higher costs = slower verification. Balance speed (e.g., API responses) with security.

---

### 4. **Handle Collisions Gracefully**
Collisions (two inputs → same hash) are inevitable. For checksums:
- Use **SHA-384** or **SHA-512** for higher collision resistance.
- For critical data, pair hashing with HMAC (authenticated checksums).

#### Example: HMAC-SHA256 for Data Integrity
```python
import hmac, hashlib

def compute_hmac(secret: str, data: str) -> str:
    """Compute HMAC-SHA256 for data integrity."""
    return hmac.new(secret.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()
```

---

## Implementation Guide: Full Workflow

### Step 1: Choose the Right Hash
| Use Case               | Recommended Hash          |
|------------------------|---------------------------|
| Password storage        | bcrypt, Argon2            |
| API keys (server-side) | HMAC-SHA256               |
| Database checksums     | SHA-256, SHA-3            |
| Non-security hashing   | xxHash, CityHash          |

### Step 2: Store Hashes Securely
- **Never** store plaintext passwords.
- Store **hash + salt** together (never salt alone).
- Use **separate columns** in databases:
  ```sql
  CREATE TABLE users (
      id SERIAL PRIMARY KEY,
      username VARCHAR(50) UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,  -- bcrypt/Argon2 output
      salt BYTEA NOT NULL           -- 16-byte salt
  );
  ```

### Step 3: API Considerations
If hashing in APIs (e.g., HMAC for API keys):
```python
from flask import Flask, request, jsonify

app = Flask(__name__)
SECRET_KEY = "your-secret-key-here"

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    received_signature = data.get('signature')
    computed_signature = compute_hmac(SECRET_KEY, str(data))
    if received_signature != computed_signature:
        return jsonify({"error": "Invalid signature"}), 403
    return jsonify({"success": True})
```

---

## Common Mistakes to Avoid

### ❌ **Mistake 1: Using SHA-256 for Passwords**
SHA-256 is fast and secure for checksums, but **not for passwords** because:
- It’s not **slow** (no built-in cost factor).
- Vulnerable to GPU/ASIC brute-force attacks.

**Fix:** Use bcrypt or Argon2 instead.

---

### ❌ **Mistake 2: Hardcoding Salts**
Salts must be **unique per user** and **random**.
**Bad:**
```python
salt = "fixed-salt"  # ❌ Vulnerable to rainbow tables
```

**Good:**
```python
import os
salt = os.urandom(16)  # ✅ 16-byte random salt
```

---

### ❌ **Mistake 3: Ignoring Hash Collisions**
For checksums, assume collisions **will** happen. Use:
- Longer hashes (SHA-384).
- Pairing with HMAC (as shown above).

---

### ❌ **Mistake 4: Reusing Old Hashes**
- **MD5/SHA-1** are obsolete for security.
- **SHA-0** is **mathmatically broken** (avoid entirely).

**Fix:** Use modern hashes (bcrypt, Argon2, SHA-3).

---

## Key Takeaways

✅ **Use the right tool for the job**: Cryptographic hashes (bcrypt, Argon2) for security, fast hashes (SHA-256, xxHash) for non-security.
✅ **Always salt**: Randomize salts per entry and store them separately.
✅ **Adjust costs**: Higher bcrypt/Argon2 cost factors slow down attackers but slow down your system too.
✅ **Handle collisions**: For checksums, use longer hashes or HMAC.
✅ **Avoid reusing old hashes**: MD5, SHA-1, SHA-0 are security disasters.
✅ **Store hashes securely**: Never expose raw salts or user data.

---

## Conclusion

Hashing is a double-edged sword: powerful when used correctly, but devastating when misapplied. As a beginner backend developer, focus on:
1. **Security first**: Use bcrypt/Argon2 for passwords.
2. **Salting**: Treat it as a hygiene practice, not an optional feature.
3. **Testing**: Always verify your hashing workflow (e.g., unit tests for password hashing).

### Next Steps
- **Experiment**: Try hashing passwords in Python with bcrypt.
- **Read further**: Check out the [NIST SP 800-63B](https://pages.nist.gov/800-63-3/sp800-63b.html) guidelines for password hashing.
- **Stay updated**: Hash function standards evolve (e.g., SHA-3 is now preferred for many use cases).

Hashing isn’t complicated—it’s about **making the right choices**. Now go build something secure!

---
**🔒 Want to dive deeper?**
- [Bcrypt Docs](https://github.com/alexanderyakubovsky/bcrypt.py)
- [Argon2 Paper](https://www.usenix.org/conference/usenixsecurity15/technical-sessions/presentation/genkin)
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
```