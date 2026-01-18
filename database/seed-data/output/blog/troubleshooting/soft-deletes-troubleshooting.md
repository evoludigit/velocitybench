# **Debugging Soft Deletes vs. Hard Deletes: A Troubleshooting Guide**
*A practical guide for diagnosing and resolving misconfigurations in the Soft Delete pattern.*

---

## **1. Introduction**
The **Soft Delete** pattern (marking records as deleted via a `is_deleted` flag rather than physically removing them) is a common way to maintain data integrity while allowing recovery. However, misconfigurations can lead to broken references, data inconsistencies, or accidental hard deletes.

This guide helps you:
- Identify symptoms of **Soft Delete** problems.
- Diagnose common root causes.
- Apply fixes with code examples.
- Prevent future issues.

---

## **2. Symptom Checklist**
Before diving into debugging, verify which symptoms match your issue:

| **Symptom**                          | **Likely Cause**                          | **Impact**                          |
|--------------------------------------|------------------------------------------|-------------------------------------|
| Foreign keys reference non-existent records | Missing Soft Delete constraints in joins | Query failures, N+1 problems        |
| Audit logs show deleted entities    | Incorrect `SoftDeleteScope` in Eloquent (Laravel) or manual queries | Data inconsistencies                |
| Accidental hard deletes (e.g., `DELETE FROM table`) | Misconfigured migration or ORM behavior | Permanent data loss                 |
| "Record not found" errors on valid data | Missing `SoftDelete` model trait (Laravel) | App crashes on legitimate queries   |
| Performance issues with large datasets | No `is_deleted` index or inefficient queries | Slow queries, timeouts              |

**Next Step:** If you see any of these, jump to the relevant **Common Issues** section.

---

## **3. Common Issues & Fixes**

### **Issue 1: Foreign Key Constraints Breaking Due to Soft Deletes**
**Symptom:**
`ForeignKeyConstraintViolationException` or "Record not found" when querying related models.

**Root Cause:**
Soft-deleted records are still referenced by foreign keys, but the database doesn’t know they’re "inactive." Some ORMs (like Laravel) automatically exclude soft-deleted records, but raw queries or foreign-key joins may fail.

#### **Fixes:**
##### **Option A: Use Join Conditions (Recommended)**
Modify your query to explicitly filter out soft-deleted records in joins:
```php
// Laravel (Eloquent)
$users = DB::table('users')
    ->join('posts', 'posts.user_id', '=', 'users.id')
    ->where('users.is_deleted', false)
    ->get();

// Raw SQL (if needed)
SELECT * FROM users u
JOIN posts p ON p.user_id = u.id
WHERE u.is_deleted = false;
```

##### **Option B: Add a Soft Delete Constraint (PostgreSQL Example)**
If using PostgreSQL, enforce referential integrity with `ON DELETE RESTRICT` (default) or `SET NULL`:
```sql
ALTER TABLE posts
ADD CONSTRAINT fk_user_soft_delete
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE RESTRICT;  -- Prevents deletion if referenced
```

##### **Option C: Use a Soft Delete Scope (Laravel)**
Ensure your model has the `SoftDeletes` trait and a proper scope:
```php
use Illuminate\Database\Eloquent\SoftDeletes;

class User extends Model {
    use SoftDeletes;

    protected $dates = ['deleted_at'];
    public static function bootSoftDeletes() {
        static::addGlobalScope('active', function (Builder $builder) {
            $builder->whereNull('deleted_at');
        });
    }
}
```

---

### **Issue 2: Audit Logs Showing Deleted Entities**
**Symptom:**
Audit logs reference records marked as `is_deleted = true`, even though they should be invisible.

**Root Cause:**
- Missing `deleted_at` filtering in audit log queries.
- Manual soft-deletes bypassing the ORM’s default scope.

#### **Fixes:**
##### **Option A: Apply Soft Delete Scopes to Audit Logs**
If using Laravel’s `auditlog` package, ensure it respects `SoftDeletes`:
```php
// In your AuditLog model
protected static function boot() {
    parent::boot();
    static::addGlobalScope('active', function (Builder $builder) {
        $builder->whereNull('deleted_at');
    });
}
```

##### **Option B: Manually Filter in Raw Queries**
If auditing is done via raw SQL:
```sql
SELECT * FROM audit_logs
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE users.id = audit_logs.user_id AND users.deleted_at IS NOT NULL
);
```

---

### **Issue 3: Accidental Hard Deletes**
**Symptom:**
`DELETE FROM table` was executed instead of a soft delete.

**Root Cause:**
- Misconfigured migrations (e.g., using `drop()` instead of `softDelete()`).
- Legacy code calling `Model::forceDelete()` when `delete()` was intended.

#### **Fixes:**
##### **Option A: Revert the Hard Delete (If Possible)**
If the table has a `deleted_at` column, restore via:
```php
// Laravel
User::where('id', $id)->restore();

// Raw SQL
UPDATE users SET deleted_at = NULL WHERE id = 123;
```

##### **Option B: Prevent Future Hard Deletes**
- **Enforce Soft Deletes in Migrations:**
  ```php
  Schema::table('users', function (Blueprint $table) {
      $table->softDeletes(); // Adds `deleted_at` column
  });
  ```
- **Override `delete()` in Model:**
  ```php
  public function delete() {
      if (!$this->isSoftDeletable()) {
          $this->forceDelete();
      } else {
          $this->performSoftDelete();
      }
  }
  ```

---

### **Issue 4: "Record Not Found" Errors on Valid Data**
**Symptom:**
`ModelNotFoundException` even though the record exists in the database.

**Root Cause:**
- Missing `SoftDeletes` trait or `deleted_at` column.
- ORM scope overriding valid queries.

#### **Fixes:**
##### **Option A: Add Missing Trait**
Ensure your model uses `SoftDeletes`:
```php
use Illuminate\Database\Eloquent\SoftDeletes;

class User extends Model {
    use SoftDeletes;
    protected $dates = ['deleted_at'];
}
```

##### **Option B: Temporarily Disable Scopes for Debugging**
```php
User::withoutGlobalScope(ActiveScope::class)
    ->where('id', 5)
    ->first(); // Forces a direct query
```

---

### **Issue 5: Performance Issues with Soft Deletes**
**Symptom:**
Slow queries due to missing `deleted_at` indexes or inefficient filtering.

**Root Cause:**
- No index on `deleted_at`.
- Full-table scans on large datasets.

#### **Fixes:**
##### **Option A: Add an Index**
```php
Schema::table('users', function (Blueprint $table) {
    $table->index('deleted_at');
});
```

##### **Option B: Optimize Queries**
Use `whereNull('deleted_at')` instead of `where('is_deleted', false)` for better index usage:
```php
// Bad (full scan)
User::where('is_deleted', false)->get();

// Good (uses index)
User::whereNull('deleted_at')->get();
```

---

## **4. Debugging Tools & Techniques**
### **A. Query Logging (Laravel)**
Enable query logging to inspect soft-delete behavior:
```php
DB::enableQueryLog();
$users = User::all();
dd(DB::getQueryLog()); // Check for unexpected `deleted_at` conditions
```

### **B. Raw SQL Inspection**
Run the generated SQL to see if `deleted_at` is filtered:
```sql
-- Example: Check if soft deletes are applied
SELECT * FROM users WHERE deleted_at IS NULL LIMIT 1;
```

### **C. Database Tools**
- **PHPMyAdmin/pgAdmin:** Check for `deleted_at` nullability.
- **Explain Plan:** Analyze query execution:
  ```sql
  EXPLAIN ANALYZE SELECT * FROM users WHERE deleted_at IS NULL;
  ```

### **D. Unit Tests**
Add tests to verify soft-delete behavior:
```php
public function test_soft_delete_works() {
    $user = User::factory()->create();
    $user->delete(); // Soft delete
    $this->assertNull(DB::table('users')->find($user->id)->deleted_at);
    $this->assertNull(User::find($user->id)); // Should return null (soft-deleted)
}
```

---

## **5. Prevention Strategies**
| **Strategy**                          | **Implementation**                                                                 |
|---------------------------------------|-----------------------------------------------------------------------------------|
| **Enforce Soft Deletes in Models**    | Always use `SoftDeletes` trait and define `$dates = ['deleted_at']`.             |
| **Audit Log Consistency**             | Ensure audit logs filter out `deleted_at` records via scopes.                     |
| **Migration Safety**                  | Use `softDeletes()` instead of `drop()` or `delete()`.                           |
| **Query Optimization**               | Index `deleted_at` and prefer `whereNull('deleted_at')` over `is_deleted = false`.|
| **Documentation**                     | Clearly mark methods like `forceDelete()` as destructive in your API/docs.        |
| **Backup Strategy**                   | Regular backups (especially before mass soft-deletes).                           |
| **CI/CD Checks**                      | Add tests to verify soft-delete behavior in pipelines.                           |

---

## **6. Final Checklist for Resolution**
Before closing an issue:
- [ ] Verified soft-deleted records are excluded from queries.
- [ ] Foreign key constraints account for `deleted_at`.
- [ ] Audit logs ignore soft-deleted entities.
- [ ] No accidental hard deletes (use `restore()` if needed).
- [ ] Performance is optimized (indexes, query patterns).
- [ ] Tests cover soft-delete scenarios.

---
**Next Steps:**
- If the issue persists, check database logs for `ON DELETE` constraints.
- For complex relationships, consider denormalizing a `is_active` flag alongside `deleted_at`.