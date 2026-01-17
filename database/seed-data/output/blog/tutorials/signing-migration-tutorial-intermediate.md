```markdown
---
title: "Signing Migrations: How to Safely Evolve Your Database Without Breaking Things"
date: "2023-11-15"
author: "Alex J. Hopkins"
tags: ["database", "migrations", "backend engineering", "data integrity", "api design"]
description: "Learn how to safely evolve your database schema with the Signing Migration pattern—the definitive guide to keeping your data intact during schema changes."
---

# Signing Migrations: How to Safely Evolve Your Database Without Breaking Things

In modern backend development, we often find ourselves in a circular dance: **change database schema → regenerate models → test locally → deploy → pray**. This process can seem like a minefield, especially when you need to introduce breaking schema changes to existing production databases. Even small schema changes—like adding or removing columns or altering constraints—can cause downtime, data corruption, or application crashes if not handled carefully.

The **Signing Migration** pattern is a powerful way to mitigate these risks. It allows you to safely introduce breaking changes to your database schema while ensuring backward compatibility for existing data and applications. This is particularly useful when you need to update foreign keys, rename tables, or add non-nullable columns to millions of records.

At its core, signing migrations allows you to:
- Apply schema changes incrementally
- Keep old and new data in sync
- Validate data integrity in real-time
- Rollback gracefully if something goes wrong

This isn't just about "safe migrations"—this is about **controlled evolution** of your database schema while maintaining data integrity during the transition period.

---

## The Problem: Why Migrations Without Signing Can Be Dangerous

Let's start with a common scenario. You're maintaining a popular SaaS application with millions of records in your `users` table. One day, you discover a critical bug: the `email` column is a `VARCHAR(255)`, but your team has been storing emails with custom domains that exceed this length. To fix it, you need to:

1. Add a new `email` column (longer capacity)
2. Migrate all existing data from the old column to the new one
3. Remove the old column when the migration is complete

This seems straightforward, but here's what can go wrong:

### 1. Downtime and Complications
- **Single-step migrations** require downtime. You can't run this during peak hours.
- **Application crashes** if the old column is required by other services.
- **Data loss** if the migration fails midway.

### 2. Data Corruption
- If you try to add a non-nullable column in one migration and not all existing records have values, you'll corrupt your database.
- If you modify foreign key constraints without ensuring referential integrity, orphaned records will appear.

### 3. Application Breaks
- Incremental migrations often require changes to application logic. If your API assumes the old schema during migration, the app will break.

### 4. No Recovery Options
- Failed migrations are hard to roll back, especially when they involve data transformation.

---

## The Solution: Signing Migrations

Signing migrations is a pattern where you **preserve both old and new schema versions** during the transition period. This allows your application to remain functional while you safely migrate data. Here's how it works:

### Core Principles
1. **Add a new column (or table) with the desired schema** before removing the old one.
2. **Use a “signing” column** to track which records have been migrated.
3. **Update application logic** to read from both old and new columns during the transition.
4. **Once all data is migrated**, you can remove the old column.

### When to Use Signing Migrations
Signing migrations are especially useful for:
✅ Adding non-nullable columns to large tables
✅ Renaming tables or columns
✅ Modifying foreign key constraints
✅ Increasing or decreasing column sizes
✅ Changing data types (e.g., `INT` to `BIGINT`)

---

## Implementation Guide: Code Examples

Let's walk through a practical example with a popular migration: **adding a new non-nullable column to a users table**.

### Database Schema Before Migration
Assume we have this table:
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255) NOT NULL,
  account_created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

We want to add a `premium_status` column (non-nullable) to support a new feature.

### Step 1: Add New Column with Default Value
Run this migration first:
```sql
ALTER TABLE users ADD COLUMN premium_status BOOLEAN DEFAULT FALSE;
```

At this point, all existing records get `FALSE` by default, and we can start the migration process.

### Step 2: Create a Migration Tracking Table
We'll track which records have been migrated:
```sql
CREATE TABLE user_migrations (
  user_id BIGINT PRIMARY KEY REFERENCES users(id),
  migrated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  status VARCHAR(20) CHECK (status IN ('pending', 'completed'))
);

INSERT INTO user_migrations (user_id)
SELECT id FROM users
WHERE NOT EXISTS (
  SELECT 1 FROM user_migrations WHERE user_id = users.id
);
```

### Step 3: Implement the Migration Process
Now we'll create a job that processes users in batches:

```python
# Python example using PostgreSQL and asyncio
import asyncio
import psycopg
from typing import List

async def migrate_user(user_id: int) -> None:
    async with psycopg.AsyncConnection.connect("postgresql://user:pass@localhost:5432/db") as conn:
        async with conn.cursor() as cur:
            # Mark as pending if not already migrated
            await cur.execute("""
                UPDATE user_migrations
                SET status = 'pending'
                WHERE user_id = $1 AND status = 'pending'
            """, (user_id,))

            # Fetch user data
            await cur.execute("SELECT name, email, premium_status FROM users WHERE id = $1", (user_id,))
            row = await cur.fetchone()

            # Process migration logic here
            # (In real app, you'd decide premium_status based on business rules)
            new_premium_status = "some_complex_business_logic(row)"

            # Update user data
            await cur.execute("""
                UPDATE users
                SET premium_status = $1
                WHERE id = $2
            """, (new_premium_status, user_id))

            # Mark as completed
            await cur.execute("""
                UPDATE user_migrations
                SET status = 'completed'
                WHERE user_id = $1 AND status = 'pending'
            """, (user_id,))

async def batch_migration(batch_size: int = 1000) -> None:
    async with psycopg.AsyncConnection.connect("postgresql://user:pass@localhost:5432/db") as conn:
        while True:
            async with conn.cursor() as cur:
                # Get pending migrations
                await cur.execute("""
                    SELECT user_id FROM user_migrations
                    WHERE status = 'pending'
                    LIMIT $1
                """, (batch_size,))

                users_to_migrate = await cur.fetchall()

                if not users_to_migrate:
                    break

                # Process batch
                tasks = [migrate_user(user[0]) for user in users_to_migrate]
                await asyncio.gather(*tasks, return_exceptions=True)

                # Commit batch
                await conn.commit()

if __name__ == "__main__":
    asyncio.run(batch_migration())
```

### Step 4: Update Application to Handle Both Columns
During migration, your application must work with both the old and new column. Here's a sample query:

```sql
-- Example query that supports both old and new tables
SELECT
    id,
    name,
    email,
    COALESCE(premium_status, FALSE) AS premium_status
FROM users
```

### Step 5: Finalize Migration
Once all records are migrated:
```sql
-- Verify no pending migrations
SELECT COUNT(*) FROM user_migrations WHERE status = 'pending';
-- Should return 0

-- Remove tracking table if no longer needed
DROP TABLE user_migrations;

-- Add NOT NULL constraint to new column (if needed)
ALTER TABLE users ALTER COLUMN premium_status SET NOT NULL;
```

---

## Key Implementation Details

### 1. Using a Signing Column vs. a Signing Table
For small changes, a single column in the main table might suffice:
```sql
ALTER TABLE users ADD COLUMN migration_status VARCHAR(20) DEFAULT 'partial' CHECK (
    migration_status IN ('partial', 'completed')
);
```

For complex migrations, a dedicated table is better because:
- Prevents transactions from locking the main table
- Allows for parallel processing

### 2. Batch Sizing
- Start small (100-1000 records per batch)
- Monitor transaction logs and database performance
- Use database-specific features like `LIMIT` with `OFFSET` or `CURSOR` for large tables

### 3. Data Validation
Always validate data integrity before and after migration:
```sql
-- Example: Check for orphaned records
SELECT * FROM user_migrations WHERE user_id NOT IN (SELECT id FROM users);

-- Check all users have premium_status set
SELECT COUNT(*) FROM users WHERE premium_status IS NULL;
```

### 4. Rollback Strategy
Implement a rollback mechanism:
```sql
-- Create a backup table before making changes
CREATE TABLE users_backup AS SELECT * FROM users;

-- If something fails, restore from backup
DROP TABLE users;
CREATE TABLE users AS SELECT * FROM users_backup;
DROP TABLE users_backup;
```

---

## Common Mistakes to Avoid

❌ **Not tracking migration status** → You'll never know if all records were processed
❌ **Processing in a single transaction** → Locks the table for too long
❌ **Ignoring transaction logs** → Without logs, you can't track migration progress
❌ **Assuming migrations are instant** → Large tables take time; be patient
❌ **Not testing rollbacks** → Always plan for failure
❌ **Removing old columns before data is fully migrated** → Breaks existing apps
❌ **Skipping data validation** → Ensures data isn't corrupted

---

## Key Takeaways

Here are the essential lessons from signing migrations:

✔ **Preserve backward compatibility** by keeping old schemas available
✔ **Process migrations in batches** to avoid locking large tables
✔ **Track migration status** to ensure all records are processed
✔ **Validate data integrity** before and after migrations
✔ **Plan for rollback** in case of failures
✔ **Update your application logic** to handle both old and new schemas
✔ **Start small** and monitor database performance
✔ **Document your migration steps** for future reference
✔ **Consider using migration frameworks** like Liquibase, Flyway, or custom solutions
✔ **Signing migrations are not a silver bullet**—always test with realistic data

---

## Conclusion: Evolve Your Database Safely

Signing migrations are a critical tool in your database engineer's arsenal. They allow you to safely introduce breaking changes to your schema without causing downtime or data loss. While they require more planning and discipline than simple migrations, the benefits far outweigh the costs:

- **Less downtime**: Migrate data when it's convenient
- **Higher reliability**: Failures are easier to recover from
- **Smoother transitions**: Applications can handle both old and new schemas
- **Maintainable migrations**: Clear tracking and validation

The key is to treat migrations as **first-class citizens** in your development process. Invest time in designing robust migration strategies, and you'll avoid the pain of rushed, risky database changes.

### Next Steps
1. **Practice with a non-critical database** first
2. **Review your most recent migration** and ask: "Could signing migrations have made this safer?"
3. **Automate your migration tracking** with a dedicated database service
4. **Document your migration strategy** for your team

Remember: The goal isn't just to make your database changes *work*—it's to make them *safe*.

Happy migrating!
```