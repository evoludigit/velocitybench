# **Debugging the "Trinity Pattern" in FraiseQL: A Troubleshooting Guide**

The **Trinity Pattern** (also known as the **"Id-UUID-Identifier" pattern**) is a common primary key strategy in databases where:
- **`pk_*` (auto-incremented surrogate key)** – Internal system identifier (e.g., `pk_user`).
- **`id` (UUID)** – Unique but less human-readable identifier (e.g., `user_id`).
- **`identifier` (string)** – Human-friendly, mutable identifier (e.g., `username` or `email`).

While this pattern improves readability and reduces conflicts, it introduces complexity in queries, joins, and application logic. This guide helps debug common issues efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, confirm which symptoms match your problem:

| **Symptom** | **Description** | **Possible Cause** |
|-------------|----------------|-------------------|
| **Slow queries with multiple joins** | `SELECT * FROM users u JOIN orders o ON u.pk_user = o.pk_user WHERE u.identifier = 'john.doe'` is inefficient. | Missing proper indexing or suboptimal query structure. |
| **Application logs show "No matching record"** | Queries fail despite correct UUID or identifier. | Incorrect join conditions, missing columns, or race conditions. |
| **"Duplicate identifier" errors** | A human-friendly identifier (e.g., email) conflicts with an existing one. | No unique constraint enforcement or improper validation. |
| **Confusion in API responses** | Frontend expects `id` (UUID), but database uses `pk_*`. | Inconsistent data mapping between API and DB. |
| **UUID-based entities failing to update** | Changing `identifier` (e.g., renaming a user) breaks references. | Foreign keys rely on `pk_*` but applications use `id` or `identifier`. |
| **High database load with frequent UUID lookups** | `WHERE id = '...'` queries are slow. | Missing indexes or incorrect query patterns. |

If multiple symptoms appear, start with **slow queries** or **data consistency issues**.

---

## **2. Common Issues and Fixes**

### **Issue 1: Inefficient Queries Due to Multiple Joins**
**Symptoms:**
- Queries involving `pk_*`, `id`, and `identifier` require multiple joins.
- Example:
  ```sql
  -- Slow because it joins on surrogate keys, not natural keys
  SELECT p.name, o.amount
  FROM products p
  JOIN product_orders po ON p.pk_product = po.pk_product
  JOIN orders o ON po.pk_product_order = o.pk_order
  WHERE p.identifier = 'book-123';
  ```

**Fix: Optimize with Proper Indexing & Query Structure**
- **Add composite indexes** on frequently queried columns:
  ```sql
  CREATE INDEX idx_product_identifier ON products(identifier);
  CREATE INDEX idx_order_product_identifier ON orders(identifier, pk_product);
  ```
- **Use `id` (UUID) for joins when possible**:
  ```sql
  -- Faster if orders reference UUIDs instead of pk_*
  SELECT p.name, o.amount
  FROM products p
  JOIN orders o ON p.id = o.product_id  -- Assuming foreign key is UUID
  WHERE p.identifier = 'book-123';
  ```
- **Avoid `SELECT *`** – Only fetch required columns:
  ```sql
  SELECT p.identifier, o.amount
  FROM products p
  JOIN orders o ON p.id = o.product_id
  WHERE p.identifier = 'book-123';
  ```

---

### **Issue 2: "No Matching Record" Errors**
**Symptoms:**
- Application crashes with `RecordNotFound` when querying by `identifier`.
- Example:
  ```python
  # FraiseQL Query
  query = db.query("SELECT * FROM users WHERE identifier = 'john.doe'")
  user = query.first()  # Returns None
  ```

**Debugging Steps:**
1. **Verify the exact value in the database**:
   ```sql
   SELECT * FROM users WHERE identifier = 'john.doe' LIMIT 1;
   ```
2. **Check for case sensitivity** (if applicable):
   ```sql
   -- If needed, normalize case first
   UPDATE users SET identifier = LOWER(identifier);
   ```
3. **Ensure no typos in the `identifier`**:
   ```python
   # Log the exact query being executed
   print(query.sql)  # Check for escaped characters or spaces
   ```
4. **Check for race conditions** (if using async writes):
   ```sql
   -- Verify if another process deleted the record
   SELECT * FROM users WHERE id = '...' FOR UPDATE;  -- Lock to debug
   ```

**Fix: Use Transactions & Fallback Queries**
- **Fallback to `id` (UUID) if `identifier` fails**:
  ```python
  def get_user_by_identifier(identifier):
      user = db.query("SELECT * FROM users WHERE identifier = %s", identifier).first()
      if not user:
          # Try UUID-based lookup (if available)
          uuid = get_uuid_from_identifier(identifier)
          user = db.query("SELECT * FROM users WHERE id = %s", uuid).first()
      return user
  ```

---

### **Issue 3: Duplicate Identifier Conflicts**
**Symptoms:**
- Duplicate `identifier` (e.g., two users with `email@example.com`).
- Database throws `UNIQUE constraint failed` error.

**Root Cause:**
- Missing `UNIQUE` constraint on `identifier`.
- Application allows duplicate submissions without validation.

**Fix: Enforce Uniqueness in Schema**
```sql
ALTER TABLE users ADD CONSTRAINT unique_identifier UNIQUE (identifier);
```
**Fix: Update Application Logic**
```python
# Check before inserting
def create_user(identifier):
    if db.query("SELECT 1 FROM users WHERE identifier = %s", identifier).first():
        raise ValueError("Identifier already exists")
    db.execute("INSERT INTO users (identifier) VALUES (%s)", identifier)
```

---

### **Issue 4: Inconsistent Data Between `pk_*`, `id`, and `identifier`**
**Symptoms:**
- Frontend expects `id` (UUID), but backend returns `pk_*`.
- Foreign keys reference `pk_*` but applications use `id`.

**Debugging Steps:**
1. **Check API response structure**:
   ```json
   {  // ❌ Wrong (returns surrogate key)
     "id": 123,  // Should be UUID
     "pk_user": "user-123"
   }
   ```
2. **Verify database schema**:
   ```sql
   SELECT * FROM orders WHERE pk_user = 123;  -- Should reference UUID, not int
   ```

**Fix: Standardize UUID Usage**
- **Change foreign keys to UUID**:
  ```sql
  ALTER TABLE orders DROP CONSTRAINT fk_user,
  ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);
  ```
- **Update application to always use `id` (UUID)**:
  ```python
  # Instead of:
  # order.user_id = user.pk_user  # Wrong

  # Use:
  order.user_id = user.id  # Correct (UUID)
  ```

---

### **Issue 5: Slow UUID-Based Lookups**
**Symptoms:**
- `WHERE id = 'a1b2c3...'` queries are slow (UUIDs are large).
- Full-table scans occur despite indexes.

**Debugging Steps:**
1. **Check if `id` is indexed**:
   ```sql
   SELECT * FROM users WHERE id = 'a1b2c3...';  -- Should be fast if indexed
   EXPLAIN ANALYZE SELECT * FROM users WHERE id = 'a1b2c3...';
   ```
2. **If slow, add an index**:
   ```sql
   CREATE INDEX idx_users_id ON users(id);
   ```

**Fix: Use Partial UUID Indexing (If Needed)**
- If UUIDs are generated in a way that allows partial matching (e.g., first 8 chars):
  ```sql
  CREATE INDEX idx_users_id_partial ON users(id) WHERE id LIKE 'a1b2c3%';
  ```

---

## **3. Debugging Tools & Techniques**

### **A. Database-Side Debugging**
1. **Use `EXPLAIN ANALYZE` to profile queries**:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM users WHERE identifier = 'john.doe';
   ```
   - Look for **Seq Scan** (slow) vs. **Idx Scan** (fast).
   - Check if the wrong index is being used.

2. **Check index usage**:
   ```sql
   -- PostgreSQL: See if indexes are being used
   SELECT relname, idx_scan, seq_scan
   FROM pg_stat_user_indexes
   WHERE relname = 'users';
   ```

3. **Slow query log (enable in `fraise.conf`)**:
   ```ini
   [fraise]
   slow_query_time = 1
   log_statement = 'all'
   ```

### **B. Application-Level Debugging**
1. **Log raw SQL queries** before execution:
   ```python
   def debug_query(query):
       print("DEBUG SQL:", query.sql, query.params)
       return query.execute()

   user = debug_query(db.query("SELECT * FROM users WHERE id = %s", user_id))
   ```

2. **Use a transaction log to track data changes**:
   ```python
   from fraise import transaction
   with transaction():
       print("Before change:", db.query("SELECT * FROM users WHERE id = %s", user_id).first())
       db.execute("UPDATE users SET identifier = 'new_name' WHERE id = %s", user_id)
       print("After change:", db.query("SELECT * FROM users WHERE id = %s", user_id).first())
   ```

3. **Validate UUID formatting**:
   ```python
   import uuid
   def is_valid_uuid(uuid_str):
       try:
           uuid.UUID(str(uuid_str))
           return True
       except ValueError:
           return False
   ```

### **C. FraiseQL-Specific Debugging**
- **Enable query tracing**:
  ```python
  fraise.config.TRACE_QUERIES = True
  ```
- **Use FraiseQL’s debug mode**:
  ```python
  from fraise import debug
  debug.enable()
  result = db.query("SELECT * FROM ...")
  debug.disable()  # Generates a detailed report
  ```

---

## **4. Prevention Strategies**

### **A. Design-Time Best Practices**
1. **Use UUIDs for all foreign keys** (not surrogate keys):
   ```sql
   -- ❌ Avoid
   ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_pk) REFERENCES users(pk_user);

   -- ✅ Prefer
   ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);
   ```
2. **Define clear rules for `identifier`**:
   - **Never change an `identifier`** (e.g., usernames, emails) after creation.
   - If a change is needed, **flag the old record as "deprecated"** and create a new one.
3. **Use views for application-specific queries**:
   ```sql
   CREATE VIEW user_public_view AS
   SELECT id, identifier, created_at
   FROM users;
   ```
   (Hides implementation details like `pk_*`).

### **B. Runtime Best Practices**
1. **Validate inputs strictly**:
   ```python
   def sanitize_identifier(identifier):
       if not isinstance(identifier, str) or len(identifier) > 100:
           raise ValueError("Invalid identifier")
       return identifier
   ```
2. **Use transactions for critical operations**:
   ```python
   def transfer_order(user_id, new_owner_id):
       with transaction():
           db.execute("UPDATE orders SET user_id = %s WHERE id = %s", new_owner_id, order_id)
           # Additional checks here
   ```
3. **Cache frequent lookups**:
   ```python
   from fraise.cache import Cache
   user_cache = Cache()

   def get_user(user_id):
       cached = user_cache.get(user_id)
       if cached:
           return cached
       user = db.query("SELECT * FROM users WHERE id = %s", user_id).first()
       user_cache.set(user_id, user)
       return user
   ```

### **C. Migration Strategies**
- **Avoid direct `ALTER TABLE` on production** – Use schema migrations:
  ```python
  # Example migration (FraiseQL Migrate)
  def migrate_to_uuid_foreign_keys():
      db.execute("ALTER TABLE orders DROP CONSTRAINT fk_user;")
      db.execute("ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);")
  ```
- **Add new columns first, then drop old ones**:
  ```sql
  ALTER TABLE orders ADD COLUMN user_id UUID;
  UPDATE orders SET user_id = (SELECT id FROM users WHERE pk_user = order_user_pk);
  ALTER TABLE orders DROP COLUMN order_user_pk;
  ```

---

## **5. Summary Checklist for Quick Resolution**
| **Problem** | **Quick Fix** | **Long-Term Solution** |
|-------------|--------------|-----------------------|
| Slow queries | Add indexes on `identifier`, `id`, and join columns | Redesign queries to avoid `pk_*` joins |
| "No matching record" | Fallback to `id` lookup | Ensure `identifier` is unique and validated |
| Duplicate identifiers | Add `UNIQUE` constraint | Enforce uniqueness in application logic |
| Inconsistent data | Standardize on `id` (UUID) | Migrate all foreign keys to UUID |
| Slow UUID lookups | Add index on `id` | Use partial UUID indexing if needed |

---

## **Final Notes**
- **The Trinity Pattern is powerful but risky** if not managed properly. **Prefer UUIDs for all external references** and **avoid changing `identifier`**.
- **Always test migrations in staging** before applying to production.
- **Use FraiseQL’s debug tools** to catch issues early.

By following these guidelines, you can **minimize debugging time** and **ensure data consistency** in systems using the Trinity Pattern.