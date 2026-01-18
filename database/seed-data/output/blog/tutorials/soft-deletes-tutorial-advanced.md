```markdown
# **Soft Deletes vs Hard Deletes: A Practical Guide for Backend Engineers**

*When to hide data, when to erase it—and how to implement it correctly.*

---

## **Introduction**

Deletion is a fundamental operation in database design, but the "how" can have far-reaching consequences. Should you **soft delete**—marking records as inactive without removing them—or **hard delete**—permanently erasing them? The answer isn’t always obvious, but the choice can impact data recovery, compliance, performance, and even user trust.

In this post, we’ll explore the tradeoffs between **soft deletes** and **hard deletes**, when to use each, and how to implement them effectively. We’ll cover:

✅ When to use soft deletes (default approach)
✅ When hard deletes are non-negotiable
✅ Practical implementation patterns (SQL, ORM, and API design)
✅ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Why Hard Deletes Are Risky**

Hard deletes—removing data permanently—seem like the obvious solution, but they introduce several challenges:

### **1. Irreversible Mistakes**
Accidental deletions are irreversible. A misplaced `DELETE` query can wipe out critical data before anyone notices.

```sql
-- Oops. This query will delete ALL customers from the database.
DELETE FROM customers WHERE last_active_date < '2023-01-01';
```

### **2. Broken Foreign Key Integrity**
If a parent record is deleted, child records with `ON DELETE CASCADE` may also disappear—even if they should still exist.

```sql
-- This will delete all orders when a customer is hard-deleted.
ALTER TABLE orders ADD CONSTRAINT fk_customer
    FOREIGN KEY (customer_id) REFERENCES customers(id)
    ON DELETE CASCADE;
```

### **3. Compliance & Legal Risks**
GDPR, HIPAA, and other regulations require data retention policies. Hard deletions violate these laws if they happen before the required retention period.

### **4. Lost Audit Trails**
If a record is deleted, any audit logs or analytics referencing it become meaningless.

### **5. Performance Overhead (Ironically)**
Hard deletes don’t actually remove data—just mark it as unused. The database still scans it, wasting I/O and slowing queries.

### **6. Analytics & Historical Data Problems**
Businesses need historical data for trends, audits, and compliance. Hard deletes erase this context forever.

---

## **The Solution: Soft Deletes by Default, Hard Deletes When Required**

Soft deletes—marking records as inactive (`deleted_at` timestamp) instead of removing them—are the default choice for most applications. They provide:

✔ **Data recovery** (rollbacks, audits)
✔ **Consistent referential integrity** (no accidental cascading deletes)
✔ **Compliance-friendly** (data is still accessible if needed)
✔ **Easier analytics** (historical data remains intact)
✔ **Predictable behavior** (no accidental `DELETE` disasters)

**Hard deletes should only be used in rare cases:**
- **GDPR "Right to be Forgotten"** (permanent erasure required by law)
- **Temporary data** (e.g., session tokens, cache entries)
- **Extremely large datasets** (where soft delete bloat becomes a problem)

---

## **Implementation Guide: Soft Deletes in Practice**

### **1. Database Schema Design**
Add a `deleted_at` column (timestamp) to tables that need soft deletes.

```sql
-- PostgreSQL / MySQL
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;

-- SQL Server
ALTER TABLE users ADD deleted_at DATETIME NULL;
```

For new tables, include it in the initial schema:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    deleted_at TIMESTAMP NULL
);
```

---

### **2. Default Query Scopes (ORM & Raw SQL)**
**Automatically exclude deleted records** from most queries.

#### **Option A: Raw SQL (PostgreSQL Example)**
```sql
-- Default scope for all queries (PostgreSQL)
CREATE OR REPLACE FUNCTION fn_active_users()
RETURNS SETOF users AS $$
    SELECT * FROM users WHERE deleted_at IS NULL;
$$ LANGUAGE SQL;

-- Usage (wrap in a view or custom function)
SELECT * FROM fn_active_users();
```

#### **Option B: ORM (Laravel Example)**
Laravel’s `SoftDeletes` trait automates this:

```php
<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\SoftDeletes;

class User extends Model
{
    use SoftDeletes;

    protected $dates = ['deleted_at'];

    // Automatically filters out deleted records
    public function scopeActive($query)
    {
        return $query->whereNull('deleted_at');
    }
}
```

#### **Option C: Django (Python)**
Django’s `soft_delete` utility helps:

```python
from django.db import models
from django.db.models.functions import Now
from django.utils import timezone

class User(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
        return None  # Prevent physical deletion
```

---

### **3. API Design: Soft Delete Endpoints**
Expose a **soft delete** endpoint (e.g., `PATCH /users/{id}/soft-delete`) and optionally a **hard delete** for compliance cases.

#### **Example: FastAPI (Python)**
```python
from fastapi import APIRouter, HTTPException
from datetime import datetime

router = APIRouter()

@router.patch("/users/{user_id}/soft-delete")
async def soft_delete_user(user_id: int):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.deleted_at = datetime.utcnow()
    await update_user(user)
    return {"status": "success"}

@router.delete("/users/{user_id}/hard-delete")
async def hard_delete_user(user_id: int):
    user = await get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.deleted_at is None:
        await delete_user(user_id)  # Physical delete
    else:
        raise HTTPException(
            status_code=400,
            detail="User already soft-deleted"
        )
```

---

### **4. Hard Deletion Process (When Required)**
If a hard delete is necessary (e.g., after retention period), implement a **scheduled cleanup**:

#### **Example: PostgreSQL (Bulk Hard Delete)**
```sql
-- First check for records older than 30 days
DELETE FROM users
WHERE deleted_at < NOW() - INTERVAL '30 days'
AND deleted_at IS NOT NULL;
```

#### **Example: Laravel (Queue Job)**
```php
// app/Jobs/DeleteOldSoftDeletes.php
namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class DeleteOldSoftDeletes implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function handle()
    {
        \DB::table('users')
            ->where('deleted_at', '<', now()->subDays(30))
            ->whereNull('id')  // Ensure not already hard-deleted
            ->delete();
    }
}
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Ignoring `deleted_at` in Subqueries**
Forgetting to filter deleted records in joins or subqueries leads to **phantom records** appearing in results.

```sql
-- WRONG: Includes deleted users in subquery
SELECT * FROM orders
WHERE user_id IN (SELECT id FROM users WHERE deleted_at IS NOT NULL);
```

**Fix:** Always include `WHERE users.deleted_at IS NULL` in joins.

### **❌ Mistake 2: Not Indexing `deleted_at`**
Soft deletes slow down queries if `deleted_at` isn’t indexed.

```sql
-- Add this to your table
ALTER TABLE users ADD INDEX idx_deleted_at(deleted_at);
```

### **❌ Mistake 3: Mixing Soft & Hard Deletes Unpredictably**
Some teams allow **both** soft and hard deletes via the same endpoint, leading to confusion.

**Solution:** Use **separate endpoints** (`/soft-delete`, `/hard-delete`).

### **❌ Mistake 4: Forgetting to Update Related Models**
If a model has soft deletes, **all related models** should too (e.g., `users`, `orders`, `comments`).

```sql
-- WRONG: Only users have soft deletes, but orders don't
ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMP NULL;

-- FIX: Apply consistently
ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMP NULL;
```

### **❌ Mistake 5: No Retention Policy for Hard Deletes**
If you **do** hard delete, define a **scheduled cleanup** to avoid accumulating orphaned data.

---

## **Key Takeaways**

✅ **Default to soft deletes**—they’re safer, more flexible, and comply with most retention policies.
✅ **Add `deleted_at` to all tables** that need recovery or auditing.
✅ **Automate filtering** (ORM scopes, default queries) to hide deleted records by default.
✅ **Use separate endpoints** for soft and hard deletes (`PATCH /soft`, `DELETE /hard`).
✅ **Index `deleted_at`** for performance.
✅ **Scheduled cleanup** for permanent deletions (e.g., after 30 days).
✅ **Avoid `ON DELETE CASCADE`**—soft deletes break the need for it.
✅ **Document retention policies** for compliance (GDPR, HIPAA).

---

## **Conclusion**

Soft deletes vs. hard deletes isn’t a binary choice—it’s a **spectrum**. **Soft deletes should be the default**, while hard deletes are a last resort for compliance or temporary data.

By following these patterns:
- You **prevent accidental data loss**.
- You **future-proof analytics and audits**.
- You **keep referential integrity predictable**.
- You **reduce legal risks** with proper retention policies.

**Start today:** Add `deleted_at` to your next table. Your future self (and your users) will thank you.

---
**Further Reading:**
- [Laravel Soft Deletes Documentation](https://laravel.com/docs/soft-deletes)
- [Django Soft Delete Guide](https://docs.djangoproject.com/en/4.2/ref/models/fields/#soft-deleting)
- [PostgreSQL Soft Delete Patterns](https://use-the-index-luke.com/sql/postgresql/soft-delete)

What’s your team’s approach to deletions? Share in the comments!
```