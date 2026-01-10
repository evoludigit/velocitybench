# **Debugging Database Migration Strategies: A Troubleshooting Guide**
*Ensuring zero-downtime schema evolution for production databases*

---

## **1. Symptom Checklist**
Before diving into fixes, verify these common issues:

| **Symptom**                     | **Likely Cause**                          | **Quick Check** |
|----------------------------------|-------------------------------------------|-----------------|
| Database locks during `ALTER TABLE` | Online migration not implemented         | Check `SHOW PROCESSLIST` for blocked queries |
| Slow query performance after migration | Missing indexes or incorrect constraints | Run `EXPLAIN` on affected queries |
| Failed rollback                             | Transaction isolation or schema conflicts | Check `SHOW ENGINE INNODB STATUS` |
| Data corruption after migration       | Incorrect `ON DUPLICATE KEY` or `MERGE` logic | Verify sample rows with `SELECT * FROM table LIMIT 10` |
| Application crashes on startup         | Schema mismatch between app and DB      | Compare schema versions (`schema_version` table) |
| High `InnoDB` buffer pool usage         | Large temporary tables during migration   | Check `SHOW GLOBAL STATUS LIKE '%Buffer%'` |

---

## **2. Common Issues & Fixes**
### **A. Table Locks During `ALTER TABLE`**
**Problem:** Traditional `ALTER TABLE` locks the table, blocking reads/writes.

**Fix: Use Online Schema Change Techniques**
#### **Option 1: MySQL `pt-online-schema-change` (Percona Toolkit)**
```bash
# Step 1: Create a new table with desired schema
ALTER TABLE users CREATE TABLE users_new (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

# Step 2: Copy data in batches (low-contention)
pt-online-schema-change \
  --alter "MODIFY COLUMN email VARCHAR(255) NOT NULL" \
  --execute \
  --recreate \
  --alter-foreign-keys-method=restore-keys \
  --socket=/var/run/mysqld/mysqld.sock \
  D=your_db,t=users,p=user:pass
```
**Fix:** Unlocks table while migrating data incrementally.

#### **Option 2: PostgreSQL `pg_partman` or `pg_repack`**
```sql
-- Step 1: Create new table with constraints
CREATE TABLE users_new (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Step 2: Copy data in parallel
COPY users_new(id, email, created_at) FROM (SELECT * FROM users) WITH NO DATA;
INSERT INTO users_new SELECT * FROM users;

-- Step 3: Swap tables
ALTER TABLE users DISABLE TRIGGERS;
UPDATE pg_class SET relname='users_old' WHERE relname='users';
UPDATE pg_class SET relname='users' WHERE relname='users_new';
ALTER TABLE users ENABLE TRIGGERS;
DROP TABLE users_old;
```

---

### **B. Failed Rollback Due to Schema Conflicts**
**Problem:** Rollback fails if migrations depend on each other or have cascading constraints.

**Debug Steps:**
1. **Check pending transactions:**
   ```sql
   SELECT * FROM information_schema.innodb_trx WHERE trx_state = 'RUNNING';
   ```
2. **Roll back transaction manually:**
   ```sql
   BEGIN;
   -- Undo ALTER TABLE steps in reverse order
   ALTER TABLE users DROP COLUMN new_column;
   ALTER TABLE users DROP INDEX new_index;
   ROLLBACK;
   ```

**Prevention:** Use **transactional migrations** with explicit rollback steps:
```python
def migrate_up():
    with db.transaction():
        db.execute("CREATE TABLE users_new AS SELECT * FROM users")
        db.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")
        db.execute("INSERT INTO users_new SELECT * FROM users WHERE email IS NULL")

def migrate_down():
    with db.transaction():
        db.execute("DROP TABLE users_new")
        db.execute("ALTER TABLE users DROP COLUMN email")
```

---

### **C. Data Loss During Migration**
**Problem:** Incorrect `MERGE` logic or `ON DUPLICATE KEY` causes missing rows.

**Debugging:**
1. **Verify sample data before/after:**
   ```sql
   SELECT COUNT(*) FROM users_before_migration;
   SELECT COUNT(*) FROM users_after_migration;
   ```
2. **Check for orphaned rows:**
   ```sql
   SELECT * FROM users WHERE email IS NULL; -- Example of missing constraint
   ```

**Fix:** Use **double-write pattern** for critical data:
```sql
-- Step 1: Backup original table
CREATE TABLE users_backup AS SELECT * FROM users;

-- Step 2: Apply changes to new table
CREATE TABLE users_new (
  id INT PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL
);

-- Step 3: Validate data integrity
SELECT * FROM users_backup
EXCEPT
SELECT * FROM users_new;

-- Step 4: Swap tables (only if data matches)
ALTER TABLE users_backup RENAME TO users;
ALTER TABLE users_new RENAME TO users_backup;
```

---

## **3. Debugging Tools & Techniques**
### **A. Real-Time Monitoring**
- **MySQL:** `pt-stalk` (Percona Toolkit) to track locks:
  ```bash
  pt-stalk --host=localhost --user=root --interval=5 --duration=30
  ```
- **PostgreSQL:** `pgBadger` for analyzing slow queries:
  ```bash
  pgBadger -f /var/log/postgresql/postgresql.log
  ```

### **B. Schema Comparison Tools**
- **Liquibase:** Detect mismatches:
  ```bash
  liquibase --changeLogFile=db.changelog-master.xml diff --to-database
  ```
- **Flyway:** Compare schema state:
  ```bash
  flyway compare -target=production
  ```

### **C. Performance Profiling**
- **MySQL:** `SHOW PROFILE` for slow `ALTER TABLE`:
  ```sql
  SET PROFILING = 1;
  ALTER TABLE users MODIFY COLUMN email VARCHAR(255);
  SHOW PROFILE;
  ```
- **PostgreSQL:** `pg_stat_statements` to find bottlenecks:
  ```sql
  CREATE EXTENSION pg_stat_statements;
  SELECT query, calls, total_time FROM pg_stat_statements ORDER BY total_time DESC;
  ```

---

## **4. Prevention Strategies**
### **A. Design for Extensibility**
- **Add columns first, modify later:**
  ```sql
  -- Bad: Drops a column
  ALTER TABLE users DROP COLUMN old_email;

  -- Good: Add a new column and migrate data
  ALTER TABLE users ADD COLUMN email VARCHAR(255);
  UPDATE users SET email = old_email;
  ```
- **Use JSON/Array columns for flexibility:**
  ```sql
  ALTER TABLE users MODIFY COLUMN preferences JSONB;
  ```

### **B. Automated Testing**
- **Schema migration tests:**
  ```python
  # Using django-migrations or Alembic
  def test_migration():
      with transaction.atomic():
          migrate('up')
          assert Table('users').has_column('email')
          migrate('down')
          assert Table('users').columns == ['id', 'name']  # Pre-migration state
  ```
- **Data consistency checks:**
  ```sql
  -- Example: Ensure no NULL emails after migration
  SELECT email FROM users WHERE email IS NULL;
  ```

### **C. Rollback Plan**
1. **Document critical migrations** in a `migrations/` folder with:
   - `migration_1_up.sql`
   - `migration_1_down.sql`
2. **Test rollback in staging:**
   ```bash
   ./run_migration.sh down --force
   ```

### **D. Database-Specific Optimizations**
| **DB**      | **Online Migration Tool**       | **Best Practice**                          |
|-------------|----------------------------------|--------------------------------------------|
| MySQL       | `pt-online-schema-change`        | Use `--alter-foreign-keys-method=restore`  |
| PostgreSQL  | `pg_partman` or `pg_repack`      | Schedule during low-traffic periods        |
| MongoDB     | `mongod` `--repair` + `migrate`  | Use `mongos` for sharded collections       |

---

## **5. Summary Checklist for Zero-Downtime Migrations**
✅ **Always test in staging** before production.
✅ **Use online migration tools** (`pt-online-schema-change`, `pg_partman`).
✅ **Implement rollback plans** in every migration script.
✅ **Monitor locks** with `pt-stalk` or `SHOW PROCESSLIST`.
✅ **Validate data integrity** before/after migrations.

---
**Final Note:** Database migrations are high-risk, high-reward. Treat them like a **code review**—every change should be:
1. **Tested**
2. **Documented**
3. **Rollback-safe**

For production, consider **feature flags** to hide migrated fields until ready:
```python
# App code
if settings.USE_NEW_SCHEMA:
    user_email = user['email']
else:
    user_email = user['old_email']
```