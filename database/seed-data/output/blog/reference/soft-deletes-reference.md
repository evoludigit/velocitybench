# **[Pattern] Soft Deletes vs. Hard Deletes Reference Guide**

---

## **Overview**
Soft deletes and hard deletes are complementary data management strategies that balance data preservation and deletion requirements. **Soft deletes** mark records as inactive (e.g., via a `deleted_at` timestamp) while keeping them in the database, enabling recovery, auditing, and referential integrity. **Hard deletes** permanently remove records, used when compliance (e.g., GDPR) or performance demands justify irreversible erasure.

Choose soft deletes for:
- **Auditability** (track who/when deleted data).
- **Data recovery** (roll back accidental deletions).
- **Referential integrity** (orphaned records remain accessible).

Use hard deletes for:
- **Compliance** (e.g., "right to be forgotten").
- **Permanent cleanup** (temporary logs, expired sessions).
- **Performance-critical systems** (reduce storage bloat).

---

## **Schema Reference**
### **1. Soft Delete Implementation**
Add a `deleted_at` column (nullable timestamp) to tables requiring soft deletes.

| Column       | Type          | Default      | Notes                                  |
|--------------|---------------|--------------|----------------------------------------|
| `deleted_at` | `TIMESTAMP`   | `NULL`       | `NULL` = active; non-NULL = soft-deleted. |
| Sample Schema: |               |              |                                        |
| ```sql CREATE TABLE users ( id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), deleted_at TIMESTAMP NULL ); ``` |               |              |                                        |

---

### **2. Hard Delete Implementation**
Hard deletes require no schema changes but may involve:
- **Automated retention cleanup** (e.g., cron job deleting records older than 30 days).
- **Manual or API-triggered deletion** (e.g., user request via `/forget-me` endpoint).

| Action               | Trigger                     | Example Query                          |
|----------------------|-----------------------------|----------------------------------------|
| **Permanent removal**| Manual/API call             | `DELETE FROM users WHERE id = 1;`       |
| **Scheduled cleanup**| Cron job (e.g., daily)       | `DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';` |

---

## **Query Examples**

### **1. Soft Delete Queries**
#### **a) Basic Query (Exclude Deleted Records)**
```sql
-- Default scope (Laravel-style)
SELECT * FROM users WHERE deleted_at IS NULL;

-- Equivalent raw SQL (PostgreSQL)
SELECT * FROM users WHERE deleted_at IS NULL;
```
*Tip:* Use a **default scope** (ORM-specific) to auto-filter soft-deleted records:
```php
// Laravel Example
User::query()->whereNull('deleted_at');
```

#### **b) Force Include Deleted Records**
```sql
-- PostgreSQL
SELECT * FROM users;

-- Laravel (bypass scope)
User::query()->withTrashed()->get();
```

#### **c) Restore a Soft-Deleted Record**
```sql
-- Set deleted_at NULL
UPDATE users SET deleted_at = NULL WHERE id = 1;

-- Laravel (restore method)
$user = User::withTrashed()->find(1);
$user->restore();
```

#### **d) Permanently Delete a Soft-Deleted Record**
```sql
-- Hard delete (ORM example)
$deletedUser = User::withTrashed()->find(1);
$deletedUser->forceDelete(); // Bypasses soft-delete logic
```

---

### **2. Hard Delete Queries**
#### **a) Manual Hard Delete**
```sql
DELETE FROM users WHERE id = 1;
```
*Use cases:* User requests permanent deletion (e.g., GDPR compliance).

#### **b) Scheduled Hard Delete (Retention Policy)**
```sql
-- Delete logs older than 30 days
DELETE FROM activity_logs WHERE created_at < NOW() - INTERVAL '30 days';

-- Business rule: Delete cancelled orders older than 90 days
DELETE FROM orders
WHERE status = 'cancelled'
  AND created_at < NOW() - INTERVAL '90 days';
```

#### **c) Conditional Hard Delete (API Example)**
```python
# FastAPI (Pydantic + SQLAlchemy)
@app.post("/forget-me")
def forget_me(user_id: int):
    db.query(
        "DELETE FROM users WHERE id = :id AND deleted_at IS NULL",
        {"id": user_id}
    ).execute()
    return {"status": "deleted"}
```

---

## **Implementation Details**

### **Key Patterns**
| Pattern               | Description                                                                 | Example                                  |
|-----------------------|-----------------------------------------------------------------------------|------------------------------------------|
| **Default Scope**     | Auto-exclude soft-deleted records from queries.                           | `User::query()->whereNull('deleted_at')` |
| **Force Include**     | Query soft-deleted records (e.g., admin views).                            | `User::withTrashed()`                   |
| **Retention Policy**  | Automate hard deletes after TTL (e.g., 90 days).                           | Cron job + SQL `DELETE`.                 |
| **Audit Logs**        | Log soft deletes for compliance (e.g., `deleted_by_user_id`, `deleted_at`). | Add columns to `users` table.           |
| **Bulk Operations**   | Soft-delete/force-delete batches (e.g., `IN` clause).                     | `UPDATE users SET deleted_at = NOW() WHERE id IN (1, 2, 3)`. |

---

### **Database-Specific Considerations**
| Database   | Note                                                                       |
|------------|-----------------------------------------------------------------------------|
| **PostgreSQL** | Supports `ON DELETE CASCADE` for foreign keys (soft-deleted records remain). |
| **MySQL**     | Use `TRUNCATE` for hard deletes (faster but less selective).               |
| **SQLite**    | No native soft-delete support; rely on application logic.                |
| **MongoDB**   | Use `is_deleted: true/false` field or TTL indexes for automatic expiry.   |

---

### **ORM-Specific Examples**
| ORM       | Soft Delete Implementation                                      | Hard Delete Implementation              |
|-----------|------------------------------------------------------------------|------------------------------------------|
| **Laravel** | `SoftDeletes` trait + `deleted_at` column + `withTrashed()`.     | `forceDelete()` method.                 |
| **Django**  | `SoftDelete` model mixin + `is_deleted` boolean field.         | `delete()` (if `is_deleted=True`).      |
| **Elixir/Phoenix** | Add `deleted_at` column; filter in queries (`where: [deleted_at: nil]`). | `Repo.delete()` after soft-delete.      |

---

## **Performance Implications**
| Operation          | Impact                          | Optimization                          |
|--------------------|---------------------------------|---------------------------------------|
| **Soft Deletes**   | Slightly slower queries (extra `WHERE` clause). | Add index on `deleted_at`.           |
| **Hard Deletes**   | Faster queries (no filtering), but storage cleanup may lag. | Use partitioning for large tables.  |
| **Bulk Restores**  | High CPU/memory if restoring many records. | Batch updates (e.g., `UPDATE ... WHERE id IN (...)`). |

---

## **Security Considerations**
- **Soft Deletes:**
  - Ensure `deleted_at` cannot be manually set to bypass logic.
  - Restrict admin access to `forceDelete()` or bulk operations.
- **Hard Deletes:**
  - Log deletions (e.g., `audit_logs`) for compliance.
  - Use **row-level security (RLS)** (PostgreSQL) to mask sensitive data from non-admin users.
  - Example RLS policy:
    ```sql
    CREATE POLICY user_data_policy ON users
    USING (not deleted_at IS NOT NULL OR current_user = 'admin');
    ```

---

## **Related Patterns**
1. **Audit Logs**
   - Track changes (e.g., `created_at`, `updated_at`, `updated_by`) alongside soft deletes.
   - Example table:
     ```sql
     CREATE TABLE user_audit_logs (
       id SERIAL PRIMARY KEY,
       user_id INT REFERENCES users(id),
       action VARCHAR(20),  -- 'create', 'update', 'delete'
       changed_at TIMESTAMP,
       changed_by INT       -- admin user ID
     );
     ```

2. **Data Archiving**
   - Move "deleted" records to an archive table (e.g., `users_archive`) instead of soft-deleting.
   - Useful for long-term retention (e.g., compliance).

3. **Optimistic Locking**
   - Prevent concurrent modifications during soft-deletes (e.g., `version` column).
   - Example:
     ```sql
     CREATE TABLE users (
       id SERIAL PRIMARY KEY,
       name VARCHAR(100),
       deleted_at TIMESTAMP NULL,
       version INT DEFAULT 0  -- For optimistic locking
     );
     ```

4. **Event Sourcing**
   - Replace soft deletes with "deletion events" in a stream (e.g., Kafka, RabbitMQ).
   - Example event:
     ```json
     {"type": "user_deleted", "user_id": 1, "deleted_at": "2023-10-01T12:00:00Z"}
     ```

5. **CQRS (Command Query Responsibility Segregation)**
   - Separate read (soft-deleted) and write (hard-deleted) models.
   - Example:
     ```python
     # Read Model (soft deletes)
     class UserRead:
       @classmethod
       def get(cls, id):
           return User.query.where(User.deleted_at == None).get(id)

     # Write Model (hard deletes)
     class UserWrite:
       @classmethod
       def delete(cls, id):
           User.query.filter_by(id=id).delete()
     ```

---

## **Best Practices**
1. **Schema Design:**
   - Add `deleted_at` to tables requiring soft deletes **before** production.
   - Document deprecated columns (e.g., `old_email` → replace with soft deletes).

2. **Migration Strategy:**
   - For existing data:
     ```sql
     -- Backfill deleted_at for legacy soft deletes
     UPDATE users SET deleted_at = '2020-01-01' WHERE is_active = false;
     ```

3. **Backup Strategy:**
   - Include soft-deleted records in backups (they’re still in the database).
   - Test restore procedures for soft-deleted data.

4. **API Design:**
   - Expose soft-delete endpoints (e.g., `/users/{id}/soft-delete`).
   - Distinguish between soft/hard delete in API responses:
     ```json
     {
       "id": 1,
       "deleted": true,
       "deleted_at": "2023-10-01T00:00:00Z",
       "force_deleted": false
     }
     ```

5. **Testing:**
   - Write tests for:
     - Soft-delete/restore cycles.
     - Hard-delete retention policies.
     - Edge cases (e.g., concurrent deletions).

6. **Compliance:**
   - Document retention periods for hard deletes (e.g., GDPR: "Data erased within 30 days of request").
   - Example compliance note:
     > *"Soft-deleted records are retained for 90 days before hard deletion. Hard-deleted records are irrecoverable."*

---

## **Anti-Patterns**
| Pattern               | Why It Fails                                      | Alternative                          |
|-----------------------|---------------------------------------------------|--------------------------------------|
| **Hidden Columns**    | Logic spread across application/code (e.g., `is_deleted` flag). | Use `deleted_at` for sorting/auditing. |
| **Manual Soft Deletes** | Forgetting to update `deleted_at` in all queries.  | Use default scopes/ORM traits.       |
| **No Retention Policy** | Soft-deleted data accumulates indefinitely.        | Automate hard deletes after TTL.     |
| **Bulk Hard Deletes** | Deleting without audit logs or user confirmation. | Require explicit API calls.          |

---

## **Example Workflow**
### **Scenario: User Requests Data Deletion**
1. **Soft Delete (Default):**
   ```python
   # API Endpoint
   @app.post("/users/{id}/soft-delete")
   def soft_delete_user(id: int):
       user = User.get(id)
       if user.deleted_at is None:
           user.deleted_at = datetime.now()
           user.save()
           log_deletion_audit(user.id, "self_deletion")
       return {"status": "soft_deleted"}
   ```

2. **Hard Delete (After 90 Days):**
   ```sql
   -- Cron job (runs daily)
   DELETE FROM users
   WHERE deleted_at < NOW() - INTERVAL '90 days';
   ```

3. **User Requests Hard Deletion (GDPR):**
   ```python
   @app.post("/users/{id}/hard-delete")
   def hard_delete_user(id: int, user: User = Depends(get_current_user)):
       if user.id != id and not user.is_admin:
           raise HTTPException(403, "Unauthorized")

       user = User.get_or_404(id)
       if user.deleted_at is None:
           raise HTTPException(400, "User not soft-deleted")

       user.delete_instance()  # Hard delete (ORM implementation)
       log_deletion_audit(user.id, "hard_deletion")
       return {"status": "hard_deleted"}
   ```

---

## **Tools & Libraries**
| Tool/Library         | Purpose                                                                 |
|----------------------|-------------------------------------------------------------------------|
| **Laravel**          | `SoftDeletes` trait, `withTrashed()`, `forceDelete()`.                |
| **Django**           | `SoftDelete` model mixin, `is_deleted` field.                           |
| **Sequelize.js**     | `SoftDeletes` plugin for association support.                          |
| **Ruby on Rails**    | `soft_delete_columns`, `with_deleted` scope.                           |
| **Entity Framework (C#)** | `HasSoftDelete()` extension.                       |
| **Prisma**           | `$or` clause for soft-deleted queries (e.g., `where: { deletedAt: { not: null } }`). |

---

## **Troubleshooting**
| Issue                          | Cause                                  | Solution                                  |
|--------------------------------|----------------------------------------|-------------------------------------------|
| **Soft-deleted records still visible** | Default scope not applied.           | Check ORM/query builder for `whereNull`.   |
| **Concurrent modification conflicts** | No optimistic locking.          | Add `version` column + `ON UPDATE CASCADE`. |
| **Hard delete fails silently** | Missing retention check.              | Log errors + validate `deleted_at` before hard delete. |
| **Slow queries after soft deletes** | Missing index on `deleted_at`.      | Add `CREATE INDEX idx_deleted_at ON users(deleted_at)`. |

---
**End of Document.**
*(Word count: ~950)*