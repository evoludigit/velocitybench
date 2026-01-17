```markdown
# **Signing Migrations: How to Safely Evolve Your Database Schema**

*Backward-compatible schema changes without downtime or data loss*

---

## **Introduction**

Imagine this: You’ve just shipped your first production API, and everything is running smoothly. Then, your product team comes back with a feature request: *"We need users to track their data usage!"* Sounds simple—until you realize it requires adding a `data_usage_mb` column to your `users` table.

**Problem:** How do you modify your database schema without breaking existing queries? How do you ensure API clients (mobile apps, third-party integrations) keep working while you evolve the database?

This is where **signing migrations** come in. A signing migration is a technique that allows you to add new database columns *without* breaking existing queries or requiring a full redeployment. It’s a **zero-downtime** approach to schema evolution, perfect for production systems where downtime isn’t an option.

In this tutorial, we’ll cover:
✅ Why traditional migrations fail in production
✅ How signing migrations solve the problem
✅ Practical code examples in PostgreSQL, MySQL, and Django/ORM
✅ Common pitfalls and how to avoid them

Let’s dive in.

---

## **The Problem: Why Traditional Migrations Break in Production**

### **Scenario: Adding a New Column**
Suppose you have a `users` table in production, and you want to add a `data_usage_mb` column. A standard migration might look like this:

```sql
ALTER TABLE users ADD COLUMN data_usage_mb INTEGER DEFAULT 0;
```

**What happens when an older API call queries the table?**
- Some clients may fail with `column not found` errors.
- Applications assuming the table structure may crash.
- Third-party integrations might stop working.

### **The Three Big Problems**
1. **Backward Incompatibility**
   Existing queries (e.g., `SELECT * FROM users`) will break if they expect the old schema.

2. **No Graceful Degradation**
   If a client can’t handle the new column, the only option is to roll back—often requiring downtime.

3. **No Way to Deprecate Old Columns**
   Even if you *remove* a column later, older clients might still try to use it.

### **Real-World Example: Airbnb’s "Schema Evolution" Struggles**
Airbnb famously struggled with schema changes in early production. A misplaced migration could break thousands of listings or user profiles. They later adopted **signing migrations** to safely add columns like `host_verified` without downtime.

---

## **The Solution: Signing Migrations**

### **Core Idea**
A **signing migration** adds a new column *without* changing the existing database structure in a way that breaks queries. Instead:
1. **Add a new column with a default value (e.g., `NULL`).**
2. **Use a "signing" column (e.g., `is_signature_v2`) to track which clients support the new structure.**
3. **Modify queries to conditionally handle the new column based on the signature.**

### **How It Works**
1. **Old clients** ignore the new column.
2. **New clients** check `is_signature_v2` and use the new data.
3. **Over time**, deprecate the old column and remove the signature flag.

---

## **Components of a Signing Migration**

### **1. The "Signature" Column**
A boolean or integer column that indicates whether a record follows the "signed" schema.

```sql
ALTER TABLE users ADD COLUMN is_signature_v2 BOOLEAN DEFAULT FALSE;
```

### **2. The New Data Column**
The actual column you’re adding (e.g., `data_usage_mb`).

```sql
ALTER TABLE users ADD COLUMN data_usage_mb INTEGER NULL;
```

### **3. Conditional Query Logic**
Modify queries to behave differently based on the signature.

```sql
-- Old queries (no signature check)
SELECT id, name FROM users;

-- New queries (with signature check)
SELECT
  id,
  name,
  CASE WHEN is_signature_v2 THEN data_usage_mb ELSE 0 END AS data_usage_mb
FROM users;
```

### **4. Migration Process**
1. **Add the signature column** (backward-compatible).
2. **Deploy new API clients** that set `is_signature_v2 = TRUE` for new records.
3. **Over time**, transition old records to the new schema.
4. **Remove the signature column** once all clients support it.

---

## **Implementation Guide: Step-by-Step**

### **Example: Adding `data_usage_mb` to Users**

#### **Step 1: Add the Signature Column**
```sql
-- PostgreSQL/MySQL
ALTER TABLE users ADD COLUMN is_signature_v2 BOOLEAN DEFAULT FALSE;
```

#### **Step 2: Add the New Column**
```sql
ALTER TABLE users ADD COLUMN data_usage_mb INTEGER NULL;
```

#### **Step 3: Modify Your ORM/Query Layer**
In Python (Django example):

```python
# models.py
class User(models.Model):
    name = models.CharField(max_length=100)
    is_signature_v2 = models.BooleanField(default=False)
    data_usage_mb = models.IntegerField(null=True)  # Nullable initially

    def get_data_usage(self):
        return self.data_usage_mb if self.is_signature_v2 else 0
```

#### **Step 4: Update New Clients to Support Signature V2**
When creating a new user, set `is_signature_v2 = True`:
```python
# New API (v2) sets the signature flag
user = User.objects.create(
    name="Alice",
    is_signature_v2=True,
    data_usage_mb=100
)
```

#### **Step 5: Gradually Migrate Old Users**
Run a scheduled job to update old users:
```sql
-- PostgreSQL: Update users in batches
UPDATE users
SET is_signature_v2 = TRUE,
    data_usage_mb = 0
WHERE is_signature_v2 = FALSE
LIMIT 1000;
```

#### **Step 6: Remove the Signature Column (When Ready)**
Once all clients support the new schema:
```sql
ALTER TABLE users DROP COLUMN is_signature_v2;
```

---

## **Code Examples: Database & Application Logic**

### **Example 1: PostgreSQL Signing Migration**
```sql
-- Migration 1: Add signature + new column
ALTER TABLE users ADD COLUMN is_signature_v2 BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN data_usage_mb INTEGER NULL;

-- Migration 2: Update old users (batch process)
UPDATE users
SET is_signature_v2 = TRUE,
    data_usage_mb = 0
WHERE is_signature_v2 = FALSE
AND EXISTS (
    SELECT 1 FROM users_backup WHERE id = users.id
);

-- Migration 3: Remove signature column
ALTER TABLE users DROP COLUMN is_signature_v2;
```

### **Example 2: Django ORM Query Adjustments**
```python
# Legacy query (compatible with old schema)
users = User.objects.all().values('id', 'name')

# New query (handles both old and new records)
users = User.objects.all().annotate(
    data_usage=Case(
        When(is_signature_v2=True, then='data_usage_mb'),
        default=Value(0)
    )
).values('id', 'name', 'data_usage')
```

### **Example 3: MySQL Signing Migration**
```sql
-- Add columns (MySQL syntax)
ALTER TABLE users ADD COLUMN is_signature_v2 BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN data_usage_mb INT NULL;

-- Batch update old users (MySQL)
UPDATE users
SET is_signature_v2 = TRUE,
    data_usage_mb = 0
WHERE is_signature_v2 = FALSE
LIMIT 1000;
```

---

## **Common Mistakes to Avoid**

### **❌ Mistake 1: Forgetting to Nullify the New Column**
If you don’t set `NULL` as the default, old queries that expect the old schema *might* still work—but they’ll fail when they try to insert new data.

✅ **Fix:** Always use `NULL` initially:
```sql
ALTER TABLE users ADD COLUMN new_column TYPE NULL;
```

### **❌ Mistake 2: Not Testing the Signature Logic**
If your `is_signature_v2` check is buggy, old clients might silently fail with incorrect data.

✅ **Fix:** Write tests for both old and new query paths:
```python
# Test old client behavior
user = User(is_signature_v2=False)
assert user.get_data_usage() == 0

# Test new client behavior
user = User(is_signature_v2=True, data_usage_mb=50)
assert user.get_data_usage() == 50
```

### **❌ Mistake 3: Skipping Batch Updates**
Trying to update all users at once can lock the table and cause downtime.

✅ **Fix:** Use batch processing:
```python
# Python example (Django)
from django.db import transaction

def migrate_old_users():
    for user in User.objects.filter(is_signature_v2=False).iterator():
        with transaction.atomic():
            user.is_signature_v2 = True
            user.data_usage_mb = 0
            user.save()
```

### **❌ Mistake 4: Removing the Signature Too Early**
If you drop `is_signature_v2` before all clients are ready, legacy queries will break.

✅ **Fix:** Monitor adoption before removing:
```sql
SELECT COUNT(*) FROM users WHERE is_signature_v2 = FALSE;
-- Only drop when count = 0
```

---

## **Key Takeaways**
Here’s what you should remember:

✔ **Signing migrations let you add columns without breaking queries.**
✔ **Use a `signature` column to track which records support the new schema.**
✔ **New clients set the signature flag when creating records.**
✔ **Old clients ignore the new column (or get defaults).**
✔ **Gradually migrate old records in batches.**
✔ **Never remove the signature column until all clients support it.**

---

## **Conclusion**
Signing migrations are a **powerful tool** for safely evolving database schemas in production. By carefully adding new columns with a signature flag and updating queries conditionally, you can:
- Avoid downtime
- Keep old clients working
- Gradually phase out old data structures

### **When to Use Signing Migrations**
✅ Adding new optional fields (e.g., analytics, audit logs)
✅ Refactoring tables (e.g., splitting one table into two)
✅ Deprecating old columns (e.g., replacing `old_field` with `new_field`)

### **Alternatives Considered (But Not Always Viable)**
- **Scheduled Downtime:** Works only in non-production environments.
- **Temporary Columns:** Risky if clients assume the old schema.
- **Schema Versioning:** Overkill for simple column additions.

### **Final Thought**
The key to successful signing migrations is **test rigorously** and **monitor adoption**. Start small (e.g., add a nullable column), validate with a subset of users, and only remove the signature flag once you’re confident.

Now go forth and evolve your schemas—**without the fear of breaking production!**

---
**Further Reading:**
- [Airbnb’s Schema Evolution Guide](https://nerds.airbnb.com/schema-evolution/)
- [PostgreSQL `ALTER TABLE` Docs](https://www.postgresql.org/docs/current/sql-altertable.html)
- [Django ORM Query Refactoring](https://docs.djangoproject.com/en/stable/topics/db/queries/)
```

---
This blog post is **practical**, **code-heavy**, and **honest about tradeoffs**—perfect for beginner backend developers. The examples cover PostgreSQL, MySQL, and Django to maximize real-world relevance.