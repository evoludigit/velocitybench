```markdown
---
title: "Canary Rollouts: The Art of Gradual Database Schema Updates"
date: "2023-11-15"
author: "Alexandra Chen"
tags: ["database", "postgresql", "schema migration", "api design", "devops", "backend", "cicd"]
draft: false
---

# Canary Rollouts: The Art of Gradual Database Schema Updates

![Canary Rollout Illustration](https://miro.medium.com/max/1400/1*_ZQ1xkVzXJQVlYwvbL9YfA.png)
*Starting small, thinking big. Illustration by Medium*

Ever felt that classic panic when you deploy a new feature, only to realize your database schema change broke 10% of your users? Or maybe you need to roll back and ask yourself *"why did I ever think this was a good idea?"* These scenarios are all too common, and they happen because we often deploy database changes directly to production in one big leap—**all-or-nothing**. But what if you could make the process smooth, controlled, and reversible? That’s where **canary rollouts** come in.

In this post, we’ll explore how canary rollouts can transform your database schema updates from a risky gamble to a calculated, gradual improvement. We’ll dive into why the traditional "big bang" approach fails, how canary rollouts mitigate risk, and how to implement them using practical examples with PostgreSQL and a lightweight API. By the end, you’ll understand not just what canary rollouts are, but *how* to apply them effectively in your projects.

---

## **The Problem: Why "Big Bang" Schema Updates Are Dangerous**

Let’s start with a familiar scenario. You’re working on a **v2.0 release** of your SaaS app, and one of the key features requires a new column in your `users` table:

```sql
ALTER TABLE users ADD COLUMN last_active_at TIMESTAMP;
```

You’ve tested it locally and in staging, so you’re confident. But when the production deployment rolls out, you discover:
- Some older client libraries still expect the old schema.
- Your analytics scripts are now broken because the new column is missing.
- Worse, your **data migration** from the old format to the new one fails for a small subset of users.

Now you’re stuck:
- **Do you roll back?** That means unhappy users for a day.
- **Do you keep the change?** That means living with a partially broken system.

This is the **big bang** approach: a single, irreversible change that affects every user at once. It’s the backend developer’s equivalent of flipping a switch in a dark room—you might get lucky, but you’re also risking a short circuit.

### **Why It Happens**
1. **Schema Drift**: Your backend and frontend might not always agree on the latest schema version.
2. **Data Migration Complexity**: Adding a column often requires migrating old data (e.g., default values, legacy formats).
3. **Non-Atomic Changes**: Unlike code deployments (where you can rollback quickly), database changes can be difficult to undo.
4. **Unpredictable Workloads**: Some users might hit the new schema at the wrong time (e.g., during a bulk export).

Big bang updates are the **technical equivalent of throwing a grenade and hoping it lands safely**. Canary rollouts, on the other hand, let you **feel the grenade’s pin before you pull it**.

---

## **The Solution: Canary Rollout for Database Schemas**

A **canary rollout** (borrowed from DevOps) is a strategy where you gradually roll out a change to a small subset of users or systems before expanding it fully. For databases, this means:
1. **Adding a new schema version in parallel** (not replacing the old one).
2. **Routing a tiny percentage of traffic** to the new schema.
3. **Monitoring for issues** before scaling up.
4. **Failing fast** if something goes wrong.

### **How It Works in Practice**
Imagine your `users` table has two versions:
- `users_v1`: The old schema with just `email`, `created_at`.
- `users_v2`: The new schema with `email`, `created_at`, and `last_active_at`.

Instead of dropping `users_v1` and renaming everything to `users_v2`, you:
1. **Create `users_v2` as a copy** of `users_v1` (or use a columnar approach).
2. **Route a small percent of users** to `users_v2` via your API.
3. **Slowly migrate data** from `users_v1` to `users_v2`.
4. **Monitor for errors** (e.g., missing data, schema conflicts).
5. **Once confident, scale up**—finally dropping `users_v1`.

This way, even if something breaks, only a tiny fraction of users are affected.

---

## **Components of a Canary Rollout**

To implement canary rollouts, you’ll need:

### **1. Database Schema Versioning**
Have multiple versions of your tables (e.g., `users_v1`, `users_v2`). Use a **postfix convention** (like `_v1`, `_v2`) to avoid conflicts.

```sql
-- V1: Original schema
CREATE TABLE users_v1 (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- V2: New schema with migration logic
CREATE TABLE users_v2 (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_active_at TIMESTAMP NULL  -- NULL = not yet migrated
);

-- Add a migration flag (optional)
ALTER TABLE users_v1 ADD COLUMN is_migrated BOOLEAN DEFAULT FALSE;
```

### **2. Routing Logic in Your API**
Use a service layer (e.g., your backend API) to route requests based on a **canary flag** or **percentage-based routing**. Here’s a simple example in Python (FastAPI):

```python
from fastapi import FastAPI, Depends, HTTPException
from random import random

app = FastAPI()

# Simulate canary flag (e.g., from a config or header)
CANARY_PERCENT = 5  # 5% of users go to v2

def get_user_version(user_id: int):
    # In reality, use a database or config to determine this
    return "v2" if random() < CANARY_PERCENT / 100 else "v1"

@app.get("/users/{user_id}")
async def get_user(user_id: int, version: str = Depends(get_user_version)):
    if version == "v1":
        # Fetch from users_v1
        return {"version": "v1", "id": user_id}
    elif version == "v2":
        # Fetch from users_v2 (may still have NULL last_active_at)
        return {"version": "v2", "id": user_id, "last_active_at": None}
    else:
        raise HTTPException(status_code=400, detail="Invalid version")
```

### **3. Data Migration Strategy**
You need a way to **gradually move data** from `v1` to `v2`. Common approaches:
- **Lazy Migration**: Fill in missing fields on demand (e.g., only compute `last_active_at` when accessed).
- **Batch Migration**: Run a scheduled job to migrate a small batch of records at a time.
- **Hybrid Reads/Writes**: Allow reads from both schemas but write only to `v2`.

Example batch migration (PostgreSQL):

```sql
-- Step 1: Add a migration lock to prevent concurrent migrations
INSERT INTO users_v1 (id, is_migrated)
SELECT id, FALSE FROM users_v1 WHERE is_migrated = FALSE
LIMIT 1000;  -- Process 1000 at a time

-- Step 2: Update last_active_at for the batch
UPDATE users_v1
SET last_active_at = NOW() - INTERVAL '1 DAY', is_migrated = TRUE
WHERE id IN (
  SELECT id FROM users_v1 WHERE is_migrated = FALSE
  LIMIT 1000
);

-- Step 3: Copy to users_v2 (if not already done)
INSERT INTO users_v2 (id, email, created_at, last_active_at)
SELECT id, email, created_at, last_active_at FROM users_v1 WHERE is_migrated = TRUE;
```

### **4. Monitoring and Alerts**
Track:
- **Error rates**: Are more errors happening in the canary group?
- **Performance**: Is the new schema slower?
- **Data consistency**: Are records missing or duplicated?
- **User impact**: Do users in the canary group report issues?

Example monitoring query:

```sql
-- Check for users in v2 with missing last_active_at
SELECT COUNT(*) FROM users_v2 WHERE last_active_at IS NULL;
```

### **5. Rollback Plan**
If something goes wrong, you need to:
1. **Stop the canary rollout** (e.g., set `CANARY_PERCENT = 0`).
2. **Revert the schema** (e.g., drop `users_v2` and restore `users_v1`).
3. **Notify users** (e.g., via in-app messages or email).

---

## **Implementation Guide: Step-by-Step**

Let’s walk through a complete example. Suppose you’re adding a `last_active_at` column to your `users` table.

### **Step 1: Prepare the Database**
```sql
-- Create v2 with a migration flag (if needed)
CREATE TABLE users_v2 (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_active_at TIMESTAMP NULL
);

-- Copy existing data (optional: include migration flag)
INSERT INTO users_v2 (id, email, created_at)
SELECT id, email, created_at FROM users_v1;
```

### **Step 2: Update Your API Layer**
Modify your API to support both versions. Here’s a Node.js (Express) example:

```javascript
const express = require('express');
const app = express();

// Canary flag (simplified)
const CANARY_PERCENT = 5;

app.get('/users/:id', async (req, res) => {
  const { id } = req.params;
  const isCanary = Math.random() * 100 < CANARY_PERCENT;

  try {
    if (isCanary) {
      // Query users_v2 (may have NULL last_active_at)
      const user = await db.query(
        'SELECT * FROM users_v2 WHERE id = $1',
        [id]
      );
      res.json({ ...user.rows[0], version: 'v2' });
    } else {
      // Query users_v1 (legacy)
      const user = await db.query(
        'SELECT * FROM users_v1 WHERE id = $1',
        [id]
      );
      res.json({ ...user.rows[0], version: 'v1' });
    }
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
});

app.listen(3000, () => console.log('Server running'));
```

### **Step 3: Gradually Migrate Data**
Use a job to migrate records in batches. Example with Node.js and pg:

```javascript
const { Pool } = require('pg');
const pool = new Pool();

async function migrateBatch() {
  const client = await pool.connect();
  try {
    // Lock a batch of records
    await client.query(`
      UPDATE users_v1
      SET is_migrated = TRUE
      WHERE is_migrated = FALSE
      LIMIT 100
    `);

    // Copy to v2 (only if not already migrated)
    await client.query(`
      INSERT INTO users_v2 (id, email, created_at, last_active_at)
      SELECT id, email, created_at, last_active_at
      FROM users_v1
      WHERE is_migrated = TRUE
      ON CONFLICT (id) DO NOTHING
    `);

    console.log('Migrated 100 records');
  } catch (err) {
    console.error(err);
  } finally {
    client.release();
  }
}

// Run every 5 minutes
setInterval(migrateBatch, 5 * 60 * 1000);
```

### **Step 4: Monitor and Scale**
1. **Monitor errors** in your canary group (e.g., via Sentry or Datadog).
2. **Increase `CANARY_PERCENT`** gradually (e.g., 5% → 10% → 20%).
3. **Once stable**, drop `users_v1` and update the API to always use `users_v2`.

```sql
-- Final cleanup (after confirming stability)
DROP TABLE users_v1;
ALTER TABLE users_v2 RENAME TO users;
```

---

## **Common Mistakes to Avoid**

1. **Skipping Monitoring**
   - *Mistake*: Assuming "it works in staging" means it’ll work in production.
   - *Fix*: Always monitor canary groups for errors and performance.

2. **Overcomplicating the Schema**
   - *Mistake*: Creating 10 schema versions for minor changes.
   - *Fix*: Use canary rollouts for **breaking changes** (e.g., new columns, dropped columns). For non-breaking changes, use a single schema.

3. **Not Having a Rollback Plan**
   - *Mistake*: Thinking you’ll "figure it out later" if something goes wrong.
   - *Fix*: Always document your rollback steps (e.g., "Set CANARY_PERCENT = 0 and drop users_v2").

4. **Ignoring Data Migration Complexity**
   - *Mistake*: Assuming `INSERT ... ON CONFLICT DO UPDATE` will handle everything.
   - *Fix*: Test your migration logic with edge cases (e.g., NULL values, race conditions).

5. **Rushing the Canary Phase**
   - *Mistake*: Expanding the canary too quickly (e.g., 5% → 100% in a day).
   - *Fix*: Start small (e.g., 0.1%) and move slowly.

6. **Not Updating Client Libraries**
   - *Mistake*: Assuming your API handles all versioning without client-side changes.
   - *Fix*: Document the new schema changes and update client libraries incrementally.

---

## **Key Takeaways**

✅ **Canary rollouts reduce risk** by exposing changes to a small subset first.
✅ **Use schema versioning** (e.g., `v1`, `v2`) to avoid conflicts.
✅ **Gradual data migration** prevents downtime and data loss.
✅ **Monitor aggressively**—errors in canary groups are your early warnings.
✅ **Have a rollback plan**—assume something will go wrong.
✅ **Start small**—begin with 0.1% of traffic and scale up.
✅ **Document everything**—future you (or your team) will thank you.
✅ **Automate testing**—include canary-specific tests in your CI/CD.

---

## **Conclusion: Why Canary Rollouts Matter**

Database schema changes are often treated as binary: **"it works or it breaks everything."** Canary rollouts flip this mindset. By adopting this pattern, you:
- **Reduce downtime** (no more "blue-green" swaps).
- **Lower risk** (failures affect only a fraction of users).
- **Improve reliability** (data migrations happen gradually).

The best part? It’s not just for massive systems. Even a small project with a handful of users benefits from canary rollouts because:
- You’ll catch bugs early.
- You’ll sleep better at night.
- Your users will have a smoother experience.

### **Next Steps**
1. **Start small**: Add canary support to your next breaking schema change.
2. **Automate monitoring**: Set up alerts for canary group errors.
3. **Experiment**: Try a 0.1% canary and see how it feels.
4. **Share**: Discuss with your team—schema changes affect everyone!

Canary rollouts aren’t about perfection; they’re about **progressive improvement**. Your database schema will thank you, and so will your users.

---
### **Further Reading**
- [PostgreSQL’s `ON CONFLICT` Documentation](https://www.postgresql.org/docs/current/sql-insert.html)
- [DevOps Canary Deployments Explained](https://www.datadoghq.com/blog/canary-deployment/)
- [Lenny Rappaport’s "Schema Evolution" Talk](https://www.youtube.com/watch?v=U368A9ZJz5I)
```

---
**Image Attribution**:
The illustration in this post is a placeholder. In a real blog post, you’d want to use a high-quality diagram (e.g., from [Excalidraw](https://excalidraw.com/) or [Mermaid](https://mermaid.js.org/)) to visualize the canary rollout flow.