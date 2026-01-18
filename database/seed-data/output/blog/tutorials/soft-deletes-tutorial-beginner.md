```markdown
---
title: "Soft Deletes vs Hard Deletes: The Database Pattern Every Backend Dev Should Know"
date: 2023-08-15
author: Jane Doe
tags: ["database design", "backend engineering", "patterns", "sql"]
description: "Learn when to use soft deletes vs hard deletes, with practical SQL/ORM examples, tradeoffs, and implementation tips."
---

---

# Soft Deletes vs Hard Deletes: The Recycle Bin for Your Database

Imagine you’re working on a social media platform. A user posts a photo, and after a heated argument, they delete it—but they regret it later. Or maybe a financial app accidentally deletes a customer’s transaction record, and now you’ve lost audit trails. These scenarios aren’t hypothetical; they happen *constantly* in real-world applications. The question is: **How do you handle "deletion" in your database**?

Most beginners default to **hard deletes**—permanently removing data from the database. But what if I told you there’s a better way? One that prevents accidental data loss, keeps your audit trails intact, and gives you flexibility for recovery? This is the **soft delete pattern**, and it’s a game-changer for backend developers.

In this post, we’ll break down:
1. Why hard deletes cause real-world problems
2. How soft deletes solve them (with code examples)
3. When to use each approach (and when to avoid mistakes)
4. A practical implementation guide for your favorite ORM

By the end, you’ll never accidentally lose critical data again.

---

## The Problem: Why Hard Deletes Are Risky

Hard deletes are simple: `DELETE FROM table WHERE id = 123`. But simplicity comes at a cost:

### 1. **Accidental Deletions Are Permanent**
Imagine this flow:
- A developer runs a migration script to clean up old data.
- A misconfigured `WHERE` clause deletes critical records.
- The data is *gone forever*—no backups can recover it because the DB transaction was committed.

```sql
-- Oops! Whoops!
DELETE FROM orders WHERE created_at < '2022-01-01'; -- Missing OR condition
```

**Consequence**: Hours of work undone, potentially violating compliance.

### 2. **Audit Trails Become Garbled**
Soft deletes are like a **database Recycle Bin**. Hard deletes? They’re like *emptying the Recycle Bin*—referential integrity breaks if other tables point to the deleted record.

```sql
-- Foreign key constraint violation (if ON DELETE CASCADE is set)
DELETE FROM user_posts WHERE user_id = 1;
-- What happens to posts, comments, or likes on this post?
```

### 3. **Foreign Key Constraints Break**
If your app uses referential integrity (which it should), hard deletes force you to choose:
- **`ON DELETE CASCADE`**: Deletes child records. This is *usually* bad.
- **`ON DELETE SET NULL`**: Nullifies foreign keys (often unnecessary).
- **`ON DELETE RESTRICT`**: Prevents deletion (but can be bypassed with `IGNORE`).

### 4. **Compliance and Legal Risks**
GDPR, HIPAA, and other regulations often require **data retention**. Hard deletes violate these rules if they remove data permanently. Even if you delete records, you might need to keep them for audit purposes.

### 5. **Historical Analytics Become Impossible**
If you need to track trends over time (e.g., "user churn in 2023"), hard deletes erase that data forever. Imagine losing a year of user behavior data because you "cleaned up" the database.

---

## The Solution: Soft Deletes + Hard Deletes

**Rule of thumb**:
> **Default to soft deletes.** Only use hard deletes for compliance (e.g., GDPR) or truly ephemeral data (e.g., temp files).

### How It Works
Soft deletes:
- **Mark** records as deleted (e.g., with a `deleted_at` timestamp).
- **Hide** them from queries (e.g., via a default scope).
- **Keep** them in the database for recovery or compliance.

Hard deletes:
- Occur **after** a retention period (e.g., 90 days).
- Are used for **true purification** (e.g., GDPR requests).

---

## Soft Deletes in Action: Code Examples

Let’s implement this in **SQL** and **Python (SQLAlchemy)**.

---

### 1. Database Schema: Adding `deleted_at`
First, add a `deleted_at` column to your model.

#### SQL:
```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE orders ADD COLUMN deleted_at TIMESTAMP NULL;
```

#### SQLAlchemy:
```python
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)  # Optional: For non-timestamp soft deletes

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    deleted_at = Column(DateTime, nullable=True)
```

---

### 2. Soft Delete: Marking a Record as Deleted
Instead of `DELETE`, we update the `deleted_at` field.

#### SQL:
```sql
-- Soft delete a user
UPDATE users SET deleted_at = NOW(), is_deleted = TRUE WHERE id = 123;
```

#### SQLAlchemy (Python):
```python
from sqlalchemy.orm import sessionmaker

# Soft delete a user
user = session.query(User).filter_by(id=123).first()
if user:
    user.deleted_at = func.now()  # Set timestamp
    user.is_deleted = True
    session.commit()
```

---

### 3. Querying: Ignoring Deleted Records
Add a **default scope** (SQLAlchemy) or **query filter** to exclude deleted records.

#### SQLAlchemy:
```python
from sqlalchemy import and_

# Default scope: Automatically exclude deleted records
Base.query = Base.query.with_options(
    orm.load_only("id", "name")  # Example: Only load these fields
)

# Add a filter for deleted records
def is_deleted_filter():
    return and_(User.deleted_at.is_(None), User.is_deleted == False)

Base.query = Base.query.filter(is_deleted_filter())

# Now queries auto-ignore deleted records:
users = session.query(User).all()  # Skips soft-deleted users
```

#### Raw SQL:
```sql
-- Exclude deleted records
SELECT * FROM users WHERE deleted_at IS NULL OR is_deleted = FALSE;
```

---

### 4. Hard Delete: Permanently Removing After Retention
After 90 days, permanently delete soft-deleted records.

#### SQL (via a scheduled job, e.g., Cron + `pg_trgm`):
```sql
-- Delete users soft-deleted > 90 days ago
DELETE FROM users
WHERE deleted_at < NOW() - INTERVAL '90 days';
```

#### Python (SQLAlchemy):
```python
from datetime import datetime, timedelta

# Delete users soft-deleted > 90 days ago
cutoff = datetime.now() - timedelta(days=90)
session.query(User).filter(
    User.deleted_at.isnot(None),
    User.deleted_at < cutoff
).delete(synchronize_session=False)
session.commit()
```

---

### 5. Restoring Soft-Deleted Records
If you need to recover a record, just set `deleted_at = NULL` (or `is_deleted = False`).

#### SQL:
```sql
-- Restore a user
UPDATE users SET deleted_at = NULL, is_deleted = FALSE WHERE id = 123;
```

#### SQLAlchemy:
```python
user = session.query(User).filter_by(id=123).first()
if user.deleted_at:
    user.deleted_at = None
    user.is_deleted = False
    session.commit()
```

---

## Implementation Guide: Step-by-Step

### Step 1: Add `deleted_at` to All Models
- Start with a **migration** (e.g., Alembic, Flyway) to add `deleted_at` to tables.
- Use `NULL` or a specific value (e.g., `'1970-01-01'`) to indicate "not deleted."

### Step 2: Create a Global Filter (ORM)
- Use **default scopes** (SQLAlchemy) or **query hooks** (Django) to auto-exclude deleted records.
- Example in Django:
  ```python
  # models.py
  class BaseModel(models.Model):
      deleted_at = models.DateTimeField(null=True, blank=True)

      class Meta:
          abstract = True

      def delete(self, *args, **kwargs):
          self.deleted_at = timezone.now()
          self.save()
          super().delete()
  ```

### Step 3: Soft Delete Endpoints
- Replace `DELETE` API endpoints with `soft_delete()` methods.
- Example in Flask (Flask-SQLAlchemy):
  ```python
  @app.route("/users/<int:user_id>/delete", methods=["POST"])
  def soft_delete_user(user_id):
      user = User.query.get_or_404(user_id)
      user.deleted_at = func.now()
      db.session.commit()
      return {"status": "success"}
  ```

### Step 4: Hard Delete (Scheduled Job)
- Use a **cron job** (Linux) or **Cloud Scheduler** (AWS/GCP) to run cleanup.
- Example with `psycopg2` (PostgreSQL):
  ```python
  import psycopg2
  from datetime import datetime, timedelta

  conn = psycopg2.connect("dbname=app user=postgres")
  cursor = conn.cursor()

  cutoff = datetime.now() - timedelta(days=90)
  cursor.execute(
      "DELETE FROM users WHERE deleted_at < %s",
      (cutoff,)
  )
  conn.commit()
  ```

### Step 5: Testing
- Test recovery: Soft-delete a record, then restore it.
- Test queries: Ensure `SELECT *` ignores deleted records.
- Test referential integrity: Ensure foreign keys don’t break.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Not Filtering Deleted Records in Queries
**Problem**: Forgetting to exclude `deleted_at` in queries leads to "ghost" data appearing in results.
**Fix**: Use default scopes (as shown above).

### ❌ Mistake 2: Using Soft Deletes for Compliance Data
**Problem**: GDPR requires *permanent* deletion for "right to be forgotten" requests.
**Fix**: For compliance, use **hard deletes** (or encrypt the data after deletion).

### ❌ Mistake 3: Overusing `ON DELETE CASCADE`
**Problem**: Soft deletes + `ON DELETE CASCADE` cause **orphaned records**.
**Fix**: Set `ON DELETE SET NULL` or avoid cascading for soft-deleted parent records.

### ❌ Mistake 4: Not Backing Up Soft-Deleted Data
**Problem**: If you lose your DB, soft-deleted data is gone unless backed up.
**Fix**: Include all records (including deleted) in backups.

### ❌ Mistake 5: Ignoring Performance Impact
**Problem**: Too many soft-deleted records slow down queries.
**Fix**: Archive old soft-deleted data (e.g., move to a "deleted_archive" table after X days).

---

## Key Takeaways

✅ **Default to soft deletes** for most cases (like a Recycle Bin).
✅ **Hide deleted records** via default scopes or query filters.
✅ **Only hard delete** after a retention period or for compliance.
✅ **Add `deleted_at`** to all tables that might need recovery.
✅ **Test recovery**—soft deletes are useless if you can’t restore.
✅ **Avoid `ON DELETE CASCADE`** with soft-deleted parents.
✅ **Back up all data**, not just active records.

---

## Conclusion: Protect Your Data Like You Protect Your Code

Soft deletes are the **Recycle Bin of databases**: safe, recoverable, and user-friendly by default. They prevent accidental data loss, keep audit trails intact, and give you flexibility—without sacrificing performance.

**When to hard delete?**
- GDPR "right to be forgotten" requests.
- Temporary data (e.g., session tokens, logs).
- Data that’s *truly* ephemeral (e.g., temporary files).

**When to soft delete?**
- User-generated content (posts, comments).
- Financial records (transactions, invoices).
- Any data you *might* need to recover.

Start implementing soft deletes today. Your future self (and your users) will thank you when that "accidental deletion" turns into a "recovered record."

---

### Further Reading
- [SQLAlchemy Soft Delete Plugin](https://sqlalchemy.org/docs/extensions/soft_delete/)
- [Django Soft Delete Guide](https://docs.djangoproject.com/en/stable/ref/contrib/admin/)
- [PostgreSQL `ON DELETE` Rules](https://www.postgresql.org/docs/current/sql-altertable.html)

---
**What’s your experience with soft deletes? Have you faced a case where hard deletes caused trouble? Share in the comments!**
```