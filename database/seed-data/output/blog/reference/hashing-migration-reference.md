---
# **[Pattern] Hashing Migration Reference Guide**

---

## **Overview**
The **Hashing Migration** pattern ensures data integrity during schema changes by migrating data from an old column format to a new one (often a hashed version) in a controlled, reversible manner. This pattern is critical when:
- Replacing plaintext fields with hashed values (e.g., for security/compliance).
- Introducing a new hash algorithm or format (e.g., SHA-256 → Argon2).
- Implementing a phased rollout of encrypted fields.

The pattern mitigates downtime and data loss by:
1. **Preserving old data** alongside new hashes (dual columns).
2. **Gradually migrating** records to the new field.
3. **Supporting rollback** if issues arise.
4. **Ensuring consistency** via transactions and validation.

---
## **Key Concepts**

| **Term**               | **Definition**                                                                                     | **Example**                                                                 |
|-------------------------|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Dual Schema**         | Temporarily storing both old and new column formats to allow gradual migration.                 | `email_old`, `email_hash` (SHA-256) in the same table.                       |
| **Migration Window**    | A timeframe where both old and new data are live.                                                  | 48 hours during a rolling deployment.                                      |
| **Hash Migration Job** | A scheduled process to update records from old → new hash format.                               | A cron job updating `user_password_old` → `user_password_hash`.             |
| **Rollback Trigger**    | A condition (e.g., error rate > 5%) to revert to the old column.                                | If `INSERT` into `new_hash` fails 10% of the time, switch back to `old_hash`. |
| **Validation Check**    | Ensuring the new hash matches the old data (e.g., via `VERIFY` in databases).                   | `SELECT * FROM users WHERE SHA2(email_old, 256) = email_hash;`              |
| **Indexing Strategy**   | Maintaining indexes on both old/new columns during migration for query performance.            | `CREATE INDEX idx_email_hash ON users(email_hash);`                         |

---
## **Schema Reference**

### **Before Migration**
```sql
CREATE TABLE users (
    id INT PRIMARY KEY,
    email VARCHAR(255) NOT NULL,  -- Plaintext (old format)
    password VARCHAR(255)        -- Plaintext (old format)
);
```

### **During Migration (Dual Schema)**
```sql
-- Add new hashed columns (NULL by default)
ALTER TABLE users
ADD COLUMN email_hash VARCHAR(255),
ADD COLUMN password_hash VARCHAR(255);

-- Ensure indexes for performance
CREATE INDEX idx_email_hash ON users(email_hash);
CREATE INDEX idx_password_hash ON users(password_hash);
```

### **After Migration (Post-Rollout)**
```sql
-- Drop old columns (after validation)
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users DROP COLUMN password;
```

---
## **Implementation Steps**

### **1. Plan the Migration**
- **Define the window**: Schedule downtime (e.g., 3 AM) or use a phased approach.
- **Set rollback criteria**: Example: Abort if >1% of records fail hashing.
- **Test with a sample**: Run on 1% of data first.

### **2. Add Hash Columns**
```sql
-- Example: Add hashed password column (PostgreSQL syntax)
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
```

### **3. Implement the Migration Job**
Use a transaction-based approach to avoid partial updates:
```sql
BEGIN TRANSACTION;

-- Update records in batches (e.g., 10,000 at a time)
UPDATE users
SET password_hash = SHA2(password, 256)
WHERE password IS NOT NULL
AND password_hash IS NULL;

-- Validate a sample (e.g., 100 records)
SELECT COUNT(*) FROM users
WHERE SHA2(password, 255) = password_hash;

COMMIT;  -- Only if validation passes
```

### **4. Validate Consistency**
```sql
-- Check for orphaned records (old data without new hash)
SELECT COUNT(*) FROM users
WHERE password IS NOT NULL AND password_hash IS NULL;

-- Check for mismatches
SELECT u.id, u.password, u.password_hash
FROM users u
WHERE SHA2(u.password, 256) != u.password_hash;
```

### **5. Drop Old Columns (Post-Rollout)**
```sql
-- After confirming all records are hashed
ALTER TABLE users DROP COLUMN password;
```

---
## **Query Examples**

### **1. Batch Hashing with Error Handling**
```sql
-- Insert into a temp table for failed records
WITH failed_updates AS (
    UPDATE users
    SET password_hash = generate_password_hash(password)  -- Application function
    WHERE password IS NOT NULL AND password_hash IS NULL
    RETURNING id, error_message
)
INSERT INTO migration_failures (user_id, reason)
SELECT id, 'Hashing failed' AS error_message
FROM failed_updates;
```

### **2. Read During Migration (Dual-Writer Pattern)**
```sql
-- Application logic to prefer new hash if available
SELECT
    CASE
        WHEN password_hash IS NOT NULL THEN password_hash
        ELSE SHA2(password, 256)  -- Fallback to old column
    END AS verified_password
FROM users;
```

### **3. Rollback Procedure**
```sql
-- Revert to old column (PostgreSQL)
ALTER TABLE users DROP COLUMN password_hash;
-- Rebuild indexes
CREATE INDEX idx_password ON users(password);
```

### **4. Performance Optimization**
```sql
-- Parallelize updates (e.g., using PostgreSQL's `FORCE PARALLEL`)
SET max_parallel_workers_per_gather = 8;
UPDATE users
PARALLEL OFF  -- Force parallel execution
SET password_hash = SHA2(password, 256)
WHERE password IS NOT NULL;
```

---
## **Best Practices**

1. **Backup Data**:
   ```sql
   -- Example: PostgreSQL backup
   pg_dump users > migration_backup.sql;
   ```

2. **Monitor Progress**:
   - Log errors to a table (e.g., `migration_log`).
   - Use tools like Prometheus to track batch completion.

3. **Phased Rollout**:
   - Start with non-critical tables (e.g., `logs` before `users`).
   - Use feature flags to toggle old/new column usage.

4. **Document Rollback Steps**:
   - Clearly outline commands to revert (e.g., `ALTER TABLE... DROP COLUMN`).

5. **Test Edge Cases**:
   - NULL values, empty strings, or malformed data.
   - Order of migrations (e.g., foreign key constraints).

---
## **Related Patterns**

| **Pattern**               | **Description**                                                                                     | **When to Use**                                                                 |
|----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **Schema Migration**       | Structured approach to altering database schemas without downtime.                                 | Any schema change requiring zero-downtime deployment.                           |
| **Double-Writer Pattern**  | Write to both old and new columns during transition.                                                | When queries must remain compatible during migration.                          |
| **Data Masking**           | Temporarily obscure sensitive data (e.g., via views or triggers).                                  | Compliance audits or phased security rollouts.                                 |
| **CQRS (Read/Write Models)** | Separate read and write schemas to decouple migrations.                                           | High-traffic systems needing independent evolution of read/write paths.          |
| **Retry with Exponential Backoff** | Handle transient errors during batch processing.                                                | Distributed systems with unreliable network calls.                             |

---
## **Anti-Patterns to Avoid**

- **Drop Old Columns Prematurely**: Always validate new hashes before dropping.
- **Ignore Batch Sizes**: Large batches risk timeouts; use transaction logs instead.
- **Skipping Validation**: Assume hashing is perfect—always verify a sample.
- **No Rollback Plan**: Assume failures will occur; design for reversibility.

---
## **Tools & Examples**

| **Database**       | **Hash Function**       | **Example Syntax**                                      |
|--------------------|-------------------------|---------------------------------------------------------|
| PostgreSQL         | `pg_crypto`             | `crypt(password, gen_salt('bf'))`                        |
| PostgreSQL         | SHA-256                 | `SHA2(password, 256)`                                   |
| MySQL              | `SHA2()`                | `SHA2('password', 256)`                                 |
| MongoDB            | `bson::to_string(md5())`| `Hashes.hash("md5", password)` (Node.js driver)         |
| SQL Server         | `HASHBYTES()`           | `HASHBYTES('SHA2_256', password)`                       |

---
## **Full Example: Email Migration**
### **Step 1: Add Dual Columns**
```sql
ALTER TABLE users ADD COLUMN email_hash VARCHAR(255);
```

### **Step 2: Migration Script (Python + SQLAlchemy)**
```python
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.sql import func

engine = create_engine("postgresql://user:pass@localhost/db")
metadata = MetaData()

users = Table("users", metadata, autoload_with=engine)

with engine.connect() as conn:
    # Update in batches of 1000
    for offset in range(0, 10000, 1000):
        stmt = users.update() \
            .values(email_hash=func.sha2(email, 256)) \
            .where(users.c.email_hash.is_(None)) \
            .where(users.c.email.isnot(None)) \
            .limit(1000) \
            .offset(offset)
        conn.execute(stmt)
```

### **Step 3: Validate**
```sql
-- Check for mismatches
SELECT email, email_hash, SHA2(email, 256) AS computed_hash
FROM users
WHERE SHA2(email, 256) != email_hash;
```

---
## **Conclusion**
The **Hashing Migration** pattern ensures seamless transitions between data formats while maintaining data integrity. Key takeaways:
1. **Use dual columns** to avoid downtime.
2. **Validate in batches** to catch errors early.
3. **Plan rollback paths** for every migration.
4. **Optimize queries** with indexes on both old/new columns.

For large-scale deployments, combine this pattern with **schema migration tools** (e.g., Flyway, Liquibase) or **CDCs (Change Data Capture)** like Debezium to streamline the process.