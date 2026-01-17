```markdown
---
title: "Hashing Migration: A Complete Guide for Backend Developers"
date: 2023-11-15
author: Alex Carter
tags: ["database", "security", "backend design", "migrations", "hashing"]
---

# **Hashing Migration: A Complete Guide for Backend Engineers**

When you start building authentication systems, passwords seem straightforward: store them in a database and compare them during login. But this is dangerous—plain-text passwords are a single breach away from disaster. Enter **hashing**, a cryptographic technique that transforms passwords into one-way, irreversible strings.

However, hashing isn’t static. Over time, you’ll upgrade your system to use stronger algorithms like **bcrypt** or **Argon2**, or fix security vulnerabilities in legacy hashes. This is where **hashing migration** comes in—the process of securely transitioning user credentials from an old hash format to a new one. Done poorly, it can leave users exposed to attacks. Done well, it’s seamless, secure, and maintains trust.

In this guide, we’ll cover:
- The risks of improper hash migrations
- How to safely migrate between hash formats
- Practical code examples for Python, Node.js, and SQL
- Common pitfalls to avoid

---

## **The Problem: Why Hash Migrations Are Tricky**

When you first deploy a system, you might start with a simple hash like **SHA-1** because it’s easy to implement:

```python
import hashlib
def hash_password_v1(password):
    return hashlib.sha1(password.encode()).hexdigest()
```

But **SHA-1 is broken**—it’s fast to compute, making brute-force attacks trivial. Over time, you realize your system is vulnerable, so you decide to migrate to **bcrypt**, which is slower and more secure:

```python
import bcrypt
def hash_password_v2(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()
```

Now you face a dilemma: **How do you update existing passwords without exposing them?**

### **The Risks of Improper Migration**
If you naively replace `hash_password_v1` with `hash_password_v2`, old passwords stop working. Worse, if an attacker gains access to the database, they can still crack SHA-1 hashes while bcrypt ones remain secure. This creates a **security gap** where old hashes are still vulnerable.

Here’s what could go wrong:
1. **Downtime**: Users can’t log in during migration.
2. **Exposure**: Old hashes remain crackable if the migration isn’t verified.
3. **Trust Erosion**: Users may abandon a service if logins fail.

The solution? **A gradual, secure migration strategy** that lets you phase out old hashes safely.

---

## **The Solution: The Hashing Migration Pattern**

The goal is to **support both old and new hashes simultaneously** until all users are migrated. Here’s how it works:

1. **Add a "hash_version" column** to track which algorithm was used.
2. **Write a verification function** that tries both old and new hashes.
3. **Gradually phase out old hashes** as new ones are adopted.
4. **Monitor progress** and force-migrate users if needed.

### **Key Principles**
- **Never delete old hashes** until they’re fully migrated.
- **Use a deterministic migration process**—the same password should always hash to the same value.
- **Test thoroughly** before deploying to production.

---

## **Implementation Guide**

Let’s build a migration system step by step. We’ll use **PostgreSQL** as the database and **Python with Flask** for the backend.

### **Step 1: Database Schema Update**
First, add a `hash_version` column to your users table:

```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS hash_version INTEGER DEFAULT 1;

-- Add a comments column to store legacy hash formats (optional but useful for debugging)
ALTER TABLE users ADD COLUMN IF NOT EXISTS hash_raw TEXT;
```

### **Step 2: Hashing Functions**
Define functions for both old and new hashing:

#### **Old Hash (SHA-1)**
```python
import hashlib

def hash_v1(password: str) -> str:
    """Legacy SHA-1 hashing (should be phased out)."""
    return hashlib.sha1(password.encode()).hexdigest()
```

#### **New Hash (bcrypt)**
```python
import bcrypt

def hash_v2(password: str) -> tuple[str, int]:
    """Secure bcrypt hashing (preferred)."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode(), 2  # version 2
```

### **Step 3: Password Verification Logic**
Write a function that checks both versions:

```python
def verify_password(plain_password: str, hashed_password: str, hash_version: int = None) -> bool:
    """
    Verify a password against either SHA-1 (v1) or bcrypt (v2).
    If hash_version is None, auto-detect from the prefix.
    """
    if hash_version is None:
        # Auto-detect version (bcrypt has '$2b$' prefix)
        if hashed_password.startswith('$2b$'):
            hash_version = 2
        else:
            hash_version = 1

    if hash_version == 1:
        # Legacy SHA-1 check
        return hashlib.sha1(plain_password.encode()).hexdigest() == hashed_password
    elif hash_version == 2:
        # bcrypt check
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    else:
        raise ValueError(f"Unknown hash version: {hash_version}")
```

### **Step 4: Migration Utility**
Add a function to migrate users from SHA-1 to bcrypt:

```python
def migrate_user(user_id: int) -> bool:
    """
    Migrate a user from SHA-1 to bcrypt.
    Returns True if migration was successful, False if already migrated.
    """
    with db_session() as session:
        user = session.query(User).get(user_id)
        if not user or user.hash_version == 2:
            return False

        # Hash the old password with bcrypt
        new_hash, new_version = hash_v2(user.password)

        # Update the record
        user.password = new_hash
        user.hash_version = new_version
        session.commit()
        return True
```

### **Step 5: Migration Strategy**
Here’s how to deploy the migration:
1. **During deployment**, set `hash_version=2` for new users.
2. **Run a background job** to migrate old users:
   ```python
   def migrate_all_users():
       with db_session() as session:
           for user in session.query(User).filter_by(hash_version=1).limit(1000):
               if migrate_user(user.id):
                   print(f"Migrated user {user.id}")
   ```
3. **Monitor progress** and manually trigger migrations if needed.
4. **After >99% migration**, you can **drop the `hash_raw` column** and **remove SHA-1 support** from `verify_password`.

---

## **Code Examples in Other Languages**

### **Node.js (Express + PostgreSQL)**
```javascript
// Old hash (SHA-1)
const crypto = require('crypto');
function hashV1(password) {
    return crypto.createHash('sha1').update(password).digest('hex');
}

// New hash (bcrypt)
const bcrypt = require('bcrypt');
async function hashV2(password) {
    const salt = await bcrypt.genSalt(10);
    return await bcrypt.hash(password, salt);
}

// Verify password
async function verifyPassword(plainPassword, hashedPassword) {
    if (hashedPassword.startsWith('$2b$')) {
        return bcrypt.compare(plainPassword, hashedPassword);
    } else {
        return hashV1(plainPassword) === hashedPassword;
    }
}

// Migration
async function migrateUser(userId) {
    const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);
    if (!user || parseInt(user.hash_version) === 2) return false;

    const newHash = await hashV2(user.password);
    await db.query(`
        UPDATE users
        SET password = $1, hash_version = 2
        WHERE id = $2
    `, [newHash, userId]);
    return true;
}
```

### **SQL Migration Script**
```sql
-- Initial setup
ALTER TABLE users ADD COLUMN IF NOT EXISTS hash_version INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS hash_raw TEXT;

-- Migrate a batch of users (PostgreSQL)
DO $$
DECLARE
    user_id INTEGER;
    new_hash TEXT;
    new_version INTEGER := 2;
BEGIN
    FOR user_id IN SELECT id FROM users WHERE hash_version = 1 LIMIT 1000 LOOP
        -- Re-hash the password (assuming you can retrieve it securely)
        -- Note: In practice, you'd do this in-app, not here.
        UPDATE users
        SET password = new_hash,
            hash_version = new_version,
            hash_raw = NULL
        WHERE id = user_id;
    END LOOP;
END $$;
```

---

## **Common Mistakes to Avoid**

1. **Skipping the Migration Phase**
   - **Bad**: Replace all hashes in one go.
   - **Good**: Keep old hashes until they’re fully deprecated.

2. **Using Insecure Hash Functions**
   - **Never** use MD5, SHA-1, or rainbow tables like `mkpasswd`.
   - **Always** use bcrypt, Argon2, or PBKDF2.

3. **Not Testing the Migration**
   - Spin up a test database and verify migrations work before production.

4. **Assuming All Users Will Migrate Automatically**
   - Some users may log in during migration. Ensure your login flow handles both versions.

5. **Forgetting to Clean Up Old Code**
   - Remove old hashing functions **only after** all users are migrated.

6. **Overcomplicating the Migration**
   - Start simple. Add complexity (e.g., rolling back migrations) later if needed.

---

## **Key Takeaways**
✅ **Always plan a migration path** before deploying a new hash algorithm.
✅ **Track hash versions** to support old and new formats.
✅ **Never delete old hashes** until they’re fully deprecated.
✅ **Use bcrypt or Argon2**—they’re designed for password storage.
✅ **Test migrations in staging** before production.
✅ **Monitor progress** and force-migrate stubborn users if needed.
✅ **Communicate with users** if logins fail during migration.

---

## **Conclusion**

Hashing migrations are a necessary evil in secure system design. While they add complexity, they prevent catastrophic security breaches. By following the pattern outlined here—**gradual migration, version tracking, and thorough testing**—you can ensure a smooth transition without exposing users to risk.

### **Next Steps**
- **Audit your system**: Check if you’re using outdated hashing (e.g., MD5, SHA-1).
- **Set up a migration plan**: Start with a small batch of users in staging.
- **Automate monitoring**: Use logs to track migration progress.
- **Stay updated**: Follow security research (e.g., [Have I Been Pwned](https://haveibeenpwned.com/)) to know when to migrate.

Security isn’t a one-time setup—it’s an ongoing process. By treating hashing migrations as part of your CI/CD pipeline, you’ll keep your users’ data safe for years to come.

---
**Want to dive deeper?**
- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [bcrypt Documentation](https://github.com/alexeygrigorev/bcrypt)
- [Argon2: The Password Hashing Competition Winner](https://pwhash.com/)

Happy coding (and hashing)! 🚀
```