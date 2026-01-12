```markdown
---
title: "Caching Migration: The Smart Way to Upgrade Your Database Without Downtime"
date: 2024-02-15
tags: ["database", "API design", "caching", "migration", "backend engineering"]
author: "Alex Mercer"
description: "Learn how to migrate your database schema safely using the caching migration pattern. Avoid downtime and data inconsistencies while upgrading."
---

# Caching Migration: The Smart Way to Upgrade Your Database Without Downtime

![Database Migration Illustration](https://miro.medium.com/max/1400/1*XQZ7Zr4gXZyU2v7EJ7O5qw.png)
*Migrating databases doesn’t have to be painful—with the right patterns, you can do it smoothly.*

As a backend engineer, you’ve probably faced the dreaded database migration—especially when you need to add a new column, change a field type, or refactor your schema. The usual approach is to stop all writes, update the schema, and then restart services. But what if you could upgrade your database while users continue to read and write without interruption? That’s the promise of **caching migration**, a pattern that lets you safely introduce schema changes without downtime.

This guide will walk you through the caching migration pattern, its challenges, and how to implement it in practice—with real-world examples in Node.js, Python, and PostgreSQL. By the end, you’ll understand how to:
- Gradually migrate data without blocking reads or writes
- Handle edge cases like invalidated cache
- Detect and fix stale cache entries
- Balance consistency with performance

---

## The Problem: Why Caching Migration?

Imagine you’re maintaining an e-commerce platform with a `users` table that stores `email`, `name`, and `tax_id`. Your team decides to add a new `tier` column to track customer loyalty levels. A naive migration would look like this:

```sql
ALTER TABLE users ADD COLUMN tier VARCHAR(20);
UPDATE users SET tier = 'gold' WHERE membership_points > 1000;
```

But what happens if:
1. **You stop writes mid-migration**? New users won’t have a `tier` column, causing errors when code tries to access it.
2. **Old queries still run**? If you don’t update all services at once, some code may query the old `users` table without the `tier` column, leading to inconsistencies.
3. **Data gets corrupted**? If the migration fails halfway, you might lose data or leave some rows in an inconsistent state.

This is why traditional migrations often require a full cutover: you must freeze all writes, apply the changes, and then restart all services. But what if you could migrate incrementally, without downtime?

---

## The Solution: Caching Migration

**[The Caching Migration Pattern](https://www.citusdata.com/blog/2020/02/12/online-schema-changes-for-postgresql/)** works by **gradually replacing the old database schema with the new one while keeping both versions in sync**. The key idea is to **let the database and cache handle the discrepancy temporarily** while new data is migrated.

Here’s how it works:

1. **Add the new column** to the database schema.
2. **Write a migration script** to populate the new column for existing records.
3. **Update your application** to read from the new column (or fallback to the old logic if needed).
4. **Cache the new data** along with the old data (if applicable).
5. **Slowly migrate stale data** from the old format to the new one.
6. **Once all data is migrated**, remove the old column (or logic) from the database and cache.

### Key Components
| Component          | Purpose                                                                 |
|--------------------|-------------------------------------------------------------------------|
| **Schema Changes** | Alter the database to include the new column.                           |
| **Migration Script** | Populate the new column for existing records.                          |
| **Cache Layer**    | Temporarily store new data alongside old data for consistency.          |
| **Gradual Rollout** | Update services one by one to avoid downtime.                          |
| **Validation**     | Detect and fix stale cache entries.                                       |

---

## Code Examples: Implementing Caching Migration

We’ll walk through a **real-world example** of migrating a `tier` column for users in an e-commerce system. Our stack includes:
- **Database:** PostgreSQL
- **Cache:** Redis
- **Backend:** Node.js (Express) and Python (FastAPI)

---

### 1. Starting Database Schema
Before migration, our `users` table looks like this:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    membership_points INT DEFAULT 0
);
```

---

### 2. Adding the New Column
First, we add the `tier` column (but don’t update existing data yet):

```sql
ALTER TABLE users ADD COLUMN tier VARCHAR(20);
```

---

### 3. Updating the Application to Handle the New Column
Our backend service needs to:
- Read from both the old and new columns temporarily.
- Write to the new column immediately.
- Cache the new data properly.

#### **Node.js Example (Express)**
Here’s how we modify our `UserService` to handle the migration:

```javascript
// services/userService.js
class UserService {
  constructor(dbClient, cacheClient) {
    this.dbClient = dbClient;
    this.cacheClient = cacheClient;
  }

  async getUser(id) {
    // Try to fetch from cache first
    const cachedUser = await this.cacheClient.get(`user:${id}`);
    if (cachedUser) return JSON.parse(cachedUser);

    // Fetch from DB
    const user = await this.dbClient.query(
      'SELECT * FROM users WHERE id = $1',
      [id]
    );

    if (!user.rows[0]) return null;

    const result = user.rows[0];

    // If tier is still NULL (old data), compute it
    if (!result.tier && result.membership_points) {
      result.tier = this._calculateTier(result.membership_points);
    }

    // Cache the result (with tier if computed)
    await this.cacheClient.set(
      `user:${id}`,
      JSON.stringify(result),
      'EX', 3600 // Cache for 1 hour
    );

    return result;
  }

  async saveUser(user) {
    // Always write to DB with tier (new column)
    await this.dbClient.query(
      'UPDATE users SET tier = $2 WHERE id = $1',
      [user.id, user.tier]
    );

    // Update cache with the new data
    await this.cacheClient.set(
      `user:${id}`,
      JSON.stringify(user),
      'EX', 3600
    );
  }

  _calculateTier(points) {
    if (points >= 1000) return 'gold';
    if (points >= 500) return 'silver';
    return 'bronze';
  }
}

module.exports = UserService;
```

#### **Python Example (FastAPI)**
Here’s the equivalent in Python:

```python
# services/user_service.py
from fastapi import Depends
from sqlalchemy.orm import Session
import redis

class UserService:
    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def get_user(self, user_id: int):
        # Try cache first
        cached_user = await self.redis.get(f"user:{user_id}")
        if cached_user:
            return json.loads(cached_user)

        # Fetch from DB
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        # If tier is NULL, compute it
        if not user.tier and user.membership_points:
            user.tier = self._calculate_tier(user.membership_points)

        # Cache the result
        await self.redis.set(
            f"user:{user_id}",
            json.dumps({
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "membership_points": user.membership_points,
                "tier": user.tier
            }),
            ex=3600  # Cache for 1 hour
        )

        return user

    async def save_user(self, user: User):
        # Always write to DB with tier
        user.tier = self._calculate_tier(user.membership_points)
        self.db.merge(user)
        self.db.commit()

        # Update cache
        await self.redis.set(
            f"user:{user.id}",
            json.dumps({
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "membership_points": user.membership_points,
                "tier": user.tier
            }),
            ex=3600
        )

    def _calculate_tier(self, points: int) -> str:
        if points >= 1000:
            return "gold"
        if points >= 500:
            return "silver"
        return "bronze"
```

---

### 4. Gradually Migrating Old Data
Now, we need to **populate the `tier` column for existing users**. We can do this in batches to avoid locking the table:

```sql
-- Run this in a separate process or during low-traffic hours
DO $$
DECLARE
    user RECORD;
BEGIN
    FOR user IN SELECT id, membership_points FROM users WHERE tier IS NULL LOOP
        IF user.membership_points >= 1000 THEN
            UPDATE users SET tier = 'gold' WHERE id = user.id;
        ELSIF user.membership_points >= 500 THEN
            UPDATE users SET tier = 'silver' WHERE id = user.id;
        ELSE
            UPDATE users SET tier = 'bronze' WHERE id = user.id;
        END IF;
    END LOOP;
END $$;
```

Alternatively, use `pg_cron` or a separate worker service to handle this:

```python
# migrate_old_users.py
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from datetime import datetime

engine = create_engine("postgresql://user:pass@localhost/db")
db = Session(engine)

def migrate_batch(batch_size=1000):
    offset = 0
    while True:
        users = db.query(User).filter(User.tier.is_(None)).offset(offset).limit(batch_size).all()
        if not users:
            break

        for user in users:
            user.tier = _calculate_tier(user.membership_points)

        db.bulk_update_mappings(User, users)
        db.commit()
        offset += batch_size
        print(f"Migrated {offset} users so far...")

if __name__ == "__main__":
    migrate_batch()
```

---

### 5. Handling Cache Invalidation
As we gradually update the `tier` column in the database, we need to ensure the cache stays in sync. There are two approaches:

#### **Option 1: Delete Cache on Write**
When a user updates their membership points (or `tier` directly), clear the cache:

```javascript
async saveUser(user) {
  await this.dbClient.query(
    'UPDATE users SET tier = $2 WHERE id = $1',
    [user.id, user.tier]
  );

  // Clear cache for this user
  await this.cacheClient.del(`user:${user.id}`);
}
```

#### **Option 2: Lazy Invalidation**
Only clear the cache if the data changes:

```python
async def save_user(self, user: User):
    old_user = self.db.query(User).filter(User.id == user.id).first()
    if old_user.tier == user.tier:
        return  # No change, no need to clear cache

    # Update DB
    user.tier = self._calculate_tier(user.membership_points)
    self.db.merge(user)
    self.db.commit()

    # Clear cache
    await self.redis.delete(f"user:{user.id}")
```

---

### 6. Finalizing the Migration
Once **all users** have a `tier` column populated, we can:
1. **Drop the old logic** from the application (e.g., remove the `if (!result.tier)` checks).
2. **Remove the old column** (if no longer needed):
   ```sql
   ALTER TABLE users DROP COLUMN membership_points; -- Only if no other tables reference it
   ```
3. **Update all services** to rely solely on the new schema.

---

## Implementation Guide: Step-by-Step

### **Phase 1: Plan the Migration**
1. **Identify the change**: What column/table is being modified? (e.g., adding `tier` to `users`).
2. **Estimate migration time**: How long will it take to migrate all data? (Batch size matters!)
3. **Choose a low-traffic window**: Schedule the migration during off-peak hours if possible.
4. **Test in staging**: Verify the pattern works before going live.

### **Phase 2: Add the New Schema**
```sql
ALTER TABLE users ADD COLUMN tier VARCHAR(20);
```

### **Phase 3: Update Application Logic**
- Modify your service layer to handle both old and new data.
- Write a migration script to populate the new column.

### **Phase 4: Gradually Migrate Old Data**
- Use batch processing to update rows incrementally.
- Monitor progress (e.g., track how many users have `tier` populated).

### **Phase 5: Monitor and Validate**
- Ensure reads and writes work correctly.
- Check for cache inconsistencies (e.g., DB has `tier` but cache doesn’t).
- Use logging to detect stale cache entries.

### **Phase 6: Finalize**
- Once all data is migrated, clean up old logic.
- Remove the old column (if no longer needed).

---

## Common Mistakes to Avoid

### **1. Not Handling Cache Invalidation Properly**
- **Problem**: If you don’t invalidate the cache when `tier` is updated, users might see outdated data.
- **Solution**: Always clear the cache when the data changes.

### **2. race Conditions During Migration**
- **Problem**: Two services might try to update the same user at the same time, leading to inconsistent `tier` values.
- **Solution**: Use database locks or optimistic concurrency control:
  ```sql
  -- Use FOR UPDATE to lock the row
  SELECT * FROM users WHERE id = $1 FOR UPDATE;
  ```

### **3. Skipping Batch Processing**
- **Problem**: Updating the entire table at once can lock it for a long time.
- **Solution**: Use batch processing with small offsets (e.g., 1000 rows at a time).

### **4. Not Testing Edge Cases**
- **Problem**: What if a user’s `membership_points` change mid-migration?
- **Solution**: Test scenarios like:
  - User updates points before migration completes.
  - Cache is stale during migration.

### **5. Forgetting to Clean Up Old Logic**
- **Problem**: Leaving old code paths open can cause inconsistencies.
- **Solution**: Gradually remove fallback logic once all data is migrated.

---

## Key Takeaways

✅ **Caching migration allows zero-downtime schema changes** by keeping old and new data in sync.
✅ **Gradual rollout reduces risk**—you can pause and restart migrations if needed.
✅ **Cache invalidation is critical**—always update the cache when data changes.
✅ **Batch processing prevents long locks** on production tables.
✅ **Monitor progress** to ensure the migration completes successfully.
✅ **Test thoroughly**—especially edge cases like concurrent updates.

---

## Conclusion

Database migrations don’t have to be scary. With the **caching migration pattern**, you can safely upgrade your schema while keeping your application running. By **gradually migrating data**, **invalidating cache properly**, and **monitoring progress**, you can avoid downtime and data inconsistencies.

### Final Checklist Before You Migrate
1. [ ] Add the new column/schema changes.
2. [ ] Update services to handle both old and new data.
3. [ ] Write a batch migration script.
4. [ ] Implement cache invalidation logic.
5. [ ] Test in staging with realistic data.
6. [ ] Schedule the migration during low traffic.
7. [ ] Monitor the migration closely.
8. [ ] Clean up old logic once migration is complete.

Now go forth and migrate with confidence! 🚀

---
**Want to dive deeper?**
- [PostgreSQL Online Schema Changes](https://www.citusdata.com/blog/2020/02/12/online-schema-changes-for-postgresql/)
- [Redis Cache Invalidation Strategies](https://redis.io/topics/invalidation)
- [Database Migration Best Practices](https://www.intersystems.com/white-papers/databases/migration-best-practices.aspx)
```