# **Debugging Hashing Migration: A Troubleshooting Guide**
*A structured approach to resolving issues in database schema migrations involving hash-based data transformations.*

---

## **1. Introduction**
Hashing migrations (e.g., changing a `username` column to a hashed version for security) are critical for security improvements but can introduce bugs if not implemented correctly. This guide covers common failure modes, debugging techniques, and preventive measures.

---
## **2. Symptom Checklist**
Before diving into debugging, verify these common issues:

| **Symptom**                     | **Likely Cause**                          |
|----------------------------------|-------------------------------------------|
| Application crashes on startup   | Missing or invalid hash function          |
| Incorrect user authentication     | Broken hash migration logic              |
| Slow query performance           | Blocking `UPDATE` during migration        |
| "Duplicate key" errors           | Collision risk in hash storage            |
| Data corruption after migration  | Race conditions in concurrent writes       |

**Quick validation steps:**
```sql
-- Check for uncommitted migrations
SELECT * FROM schema_migrations WHERE name LIKE '%hash_migration%';
-- Verify hash consistency
SELECT COUNT(*) FROM users WHERE hash_column != expected_hash;
```

---
## **3. Common Issues and Fixes**

### **⚠️ Issue 1: Missing/Invalid Hash Function**
**Symptom:** App crashes with `UnsupportedAlgorithmException` or `NoSuchMethodError`.
**Root Cause:** The chosen hash algorithm (e.g., SHA-256) is not available or misconfigured.

**Fix:**
```java
// Ensure crypto library is included (Maven/Gradle)
implementation 'org.bouncycastle:bcprov-jdk15on:1.70'
// Verify hash function availability
try {
    MessageDigest.getInstance("SHA-256"); // Test before use
} catch (NoSuchAlgorithmException e) {
    throw new RuntimeException("Hash algorithm missing!");
}
```

### **⚠️ Issue 2: Race Conditions in Concurrent Writes**
**Symptom:** Inconsistent hashes across replicas after `UPDATE` during migration.
**Root Cause:** No transaction isolation during the hash recalculation.

**Fix:**
```sql
-- Use a transaction with SERIALIZABLE isolation
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
UPDATE users SET hash_column = hash_function(plain_text_column)
WHERE migration_flag = FALSE;
UPDATE users SET migration_flag = TRUE WHERE migration_flag = FALSE;
COMMIT;
```

### **⚠️ Issue 3: Collision Risks in Hash Storage**
**Symptom:** Duplicate entries after migration.
**Root Cause:** Hash collisions (rare but possible with weak hash functions).

**Fix:**
```python
# Append a unique salt or use a zero-padding technique
def safe_hash(value, salt):
    return hashlib.sha256(salt + value).hexdigest()
```

### **⚠️ Issue 4: Unhandled Migration State**
**Symptom:** App hangs during migration validation.
**Root Cause:** Missing migration status column or failed atomic rollback.

**Fix:**
```ruby
# Add a status column to track migration progress
ALTER TABLE users ADD COLUMN migration_status ENUM('pending', 'failed', 'complete');

# Use a retry mechanism with exponential backoff
def retry_migration(max_attempts = 3)
  attempts = 0
  while attempts < max_attempts
    if db.migration_completed?
      break
    else
      begin
        process_migration
        mark_migration_complete!
      rescue => e
        attempts += 1
        sleep(2**attempts)
      end
    end
  end
end
```

---
## **4. Debugging Tools and Techniques**

### **🔍 Tool 1: Migration Log Analysis**
**Goal:** Verify step-by-step progress.
**Example:** Check PostgreSQL logs for slow queries:
```sh
grep "hash_migration" /var/log/postgresql/postgresql-*.log
```

### **🔍 Tool 2: Hash Verification Script**
**Verify hashes match expectations:**
```bash
# Bash script to compare old vs. new hashes
for user in $(db_query "SELECT username FROM users"); do
  old_hash=$(db_query "SELECT hash_column FROM users WHERE username='$user'")
  new_hash=$(python3 -c "import hashlib; print(hashlib.sha256('$user'.encode()).hexdigest())")
  if [ "$old_hash" != "$new_hash" ]; then
    echo "MISMATCH: $user"
  fi
done
```

### **🔍 Tool 3: Stress Testing with LoadSim**
**Simulate concurrent writes:**
```java
// Simulate 1000 parallel user hash updates
List<User> users = db.findAll();
CompletableFuture.allOf(
    IntStream.range(0, 1000)
        .mapToObj(i -> CompletableFuture.runAsync(() -> updateUserHash(users.get(i))))
        .toArray(CompletableFuture[]::new)
);
```

### **🔍 Debugging SQL Queries**
**Slow migration?** Check for blocking locks:
```sql
SELECT * FROM pg_locks WHERE relation = 'users'::regclass;
```

---
## **5. Prevention Strategies**

### **🛡️ 1. Atomic Migration Scripts**
Use transactions + rollback logic:
```go
func migrateHash(db *sql.DB) error {
    tx, err := db.Begin()
    if err != nil { return err }

    _, err = tx.Exec("UPDATE users SET hash_column = SHA256(plain_text_column) WHERE migration_flag = 0")
    if err != nil {
        tx.Rollback()
        return fmt.Errorf("migration failed: %v", err)
    }
    return tx.Commit()
}
```

### **🛡️ 2. Blue-Green Deployment**
Deploy to a staging environment first:
```bash
# Test workflow
docker-compose -f docker-migration.yml up --abort-on-container-exit
```

### **🛡️ 3. Input Validation**
Sanitize input before hashing:
```javascript
// Node.js example
function safeHash(input) {
  if (!input || typeof input !== 'string') throw new Error("Invalid input");
  return crypto.createHash('sha256').update(input).digest('hex');
}
```

### **🛡️ 4. Monitoring**
Set up alerts for migration anomalies:
```yaml
# Prometheus alert rule
- alert: HashMigrationFailed
  expr: hash_migration_errors > 0
  for: 5m
  labels:
    severity: critical
```

### **🛡️ 5. Backward Compatibility**
Support both plaintext and hashed columns during transition:
```sql
ALTER TABLE users ADD COLUMN plain_text_column VARCHAR(255) DEFAULT NULL;
-- Later drop it in a separate migration
```

---
## **6. Final Checklist Before Production**
✅ **Tested on staging** (realistic load)
✅ **Backup database** before migration
✅ **Rollback plan** documented
✅ **Monitoring** in place for hash consistency
✅ **Validation script** confirms correctness

---
### **When All Else Fails**
- **Revert:** Roll back to pre-migration state.
- **Investigate:** Check `pg_stat_activity` for stuck transactions.
- **Document:** Log findings for future migrations.

---
**Pro Tip:** Always design migrations **idempotent**—running them multiple times should yield the same result.

---
**End of Guide**
*Debugging hashing migrations requires patience. Focus on transactions, collisions, and concurrency first.*