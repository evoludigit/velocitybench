```markdown
---
title: "Soft Delete Performance: How to Filter Deleted Records Without Slowing Down Queries"
description: "Learn how to implement efficient soft delete patterns in databases, and avoid common performance pitfalls that can cripple your application."
date: "2024-01-15"
tags: ["database", "software architecture", "performance", "backend", "sql"]
author: "Alex Carter"
---

# Soft Delete Performance: How to Filter Deleted Records Without Slowing Down Queries

![Soft Delete Performance](https://images.unsplash.com/photo-1633390148788-f043f600090a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80)

As backend developers, we often need to maintain data that users shouldn’t see while preserving it for auditing, archival, or recovery purposes. This is where the **soft delete pattern** comes into play. Instead of permanently removing data from a table (hard delete), we mark records as deleted using a timestamp or boolean flag. However, if not implemented carefully, this pattern can lead to **painfully slow queries**—especially when dealing with large datasets.

In this post, we’ll explore:
- The **performance pitfalls** of soft delete
- How to **efficiently filter deleted records**
- Practical **code examples** in SQL and application logic
- Common mistakes and how to avoid them

Let’s dive in!

---

## The Problem: Why Soft Deletes Can Slow Down Your App

Soft deleting is a great pattern for preserving data while maintaining a clean UI. However, if you don’t optimize it properly, you’ll encounter:

1. **Slow queries** – Without proper indexing, filtering on `deleted_at` or `is_deleted` can scan entire tables.
2. **Increasing latency** – As your dataset grows, the cost of checking every record becomes prohibitive.
3. **Lock contention** – In high-concurrency scenarios, scanning large tables can lead to long-running transactions and deadlocks.

### Example: The Unoptimized Soft Delete Query

Consider a simple `users` table with a soft delete column:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    deleted_at TIMESTAMP NULL,  -- Soft delete field
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

A naive query to fetch active users looks like this:

```sql
-- This performs a full table scan if no index exists!
SELECT * FROM users WHERE deleted_at IS NULL;
```

For a small table, this might be fine. But for a table with **millions of records**, this query becomes **terribly slow** because PostgreSQL (or any database) must check every row.

---

## The Solution: Optimize Soft Deletes for Performance

To avoid slow queries, we need to ensure that:
✅ Deleted records are **isolated from active queries**
✅ The database can **quickly find only active records**
✅ The pattern scales **with growing datasets**

### **1. Indexing the Soft Delete Column**
The most critical optimization is **adding an index** on the `deleted_at` column (or `is_deleted` boolean).

```sql
-- Add an index for fast filtering
CREATE INDEX idx_users_deleted_at ON users (deleted_at);
```

This allows the database to **skip deleted rows early** without scanning the entire table.

### **2. Partitioning Deleted and Active Data**
For **very large tables**, consider **partitioning** records by `deleted_at`.

```sql
-- PostgreSQL example: Partition by date
CREATE TABLE users (
    ... -- same columns as before
) PARTITION BY RANGE (deleted_at);

-- Create a default partition for non-deleted records
CREATE TABLE users_active PARTITION OF users
    FOR VALUES FROM ('0001-01-01') TO ('9999-12-31');

-- Create a partition for deleted records
CREATE TABLE users_deleted PARTITION OF users
    FOR VALUES FROM ('2023-01-01') TO ('2025-01-01');
```

*Note:* Partitioning is an advanced technique and should be used when dealing with **extremely large datasets** (millions+ rows).

### **3. Application-Level Filtering**
Ensure your application **always filters deleted records** before processing.

#### **Example in PostgreSQL (with indexing)**
```sql
-- Now this query uses the index efficiently
SELECT * FROM users WHERE deleted_at IS NULL;
```

#### **Example in an ORM (Laravel PHP)**
```php
// Laravel: Using Eloquent's query builder
$activeUsers = User::whereNull('deleted_at')->get();
```
*(Laravel automatically converts this to a properly indexed query.)*

#### **Example in Django (Python)**
```python
# Django: Using Q objects with indexing
from django.db.models import Q
ActiveUser.objects.filter(~Q(deleted_at__isnull=False))
```
*(Django also optimizes these queries with proper indexing.)*

---

## Implementation Guide: Step-by-Step

### **Step 1: Add the Soft Delete Column**
Start by adding a `deleted_at` column (or `is_deleted` boolean) to your table.

```sql
-- For PostgreSQL, SQLite, MySQL, etc.
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;

-- For boolean flag (alternative approach)
ALTER TABLE users ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE NOT NULL;
```

### **Step 2: Create an Index**
Add an index to speed up filtering.

```sql
CREATE INDEX idx_users_deleted_at ON users (deleted_at);
-- OR for boolean flag:
CREATE INDEX idx_users_is_deleted ON users (is_deleted);
```

### **Step 3: Soft Delete in Your Application**
Implement soft delete logic in your business layer.

#### **Example: Soft Delete in PostgreSQL**
```sql
-- Soft delete a user
UPDATE users SET deleted_at = NOW() WHERE id = 1;

-- Soft undelete (restore)
UPDATE users SET deleted_at = NULL WHERE id = 1;
```

#### **Example: Soft Delete in Django**
```python
# In Django models.py
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()
```

### **Step 4: Always Filter in Queries**
Ensure **all queries** exclude deleted records.

```php
// Laravel: Always filter in queries
User::all();  // ❌ BAD: Fetches deleted records!
User::whereNull('deleted_at')->get();  // ✅ GOOD: Only active users
```

### **Step 5: Batch Deletes (for Admin Tools)**
If you need to **bulk delete**, use batch operations to avoid locking the table.

```sql
-- PostgreSQL: Batch soft delete
WITH deleted_users AS (
    SELECT id FROM users WHERE created_at < NOW() - INTERVAL '1 year'
)
UPDATE users u SET deleted_at = NOW() FROM deleted_users du WHERE u.id = du.id;
```

---

## Common Mistakes to Avoid

### ❌ **1. Forgetting to Index the Soft Delete Column**
If you don’t index `deleted_at`, every query becomes a **full table scan**, leading to **slow performance** at scale.

**Fix:** Always add an index:
```sql
CREATE INDEX idx_table_soft_delete ON table_name (deleted_at);
```

### ❌ **2. Using Soft Delete in High-Write Workloads**
If your application has **frequent inserts/deletes**, soft delete can cause **lock contention** as the table grows.

**Fix:**
- Consider **partitioning** for large tables.
- Use **optimistic locking** (`csc`) if needed.

### ❌ **3. Not Filtering in All Queries**
If you don’t filter deleted records in **every query**, your app will return **inconsistent data**.

**Fix:** Enforce soft delete filtering in:
- ORMs
- Raw SQL
- API responses

### ❌ **4. Using `WHERE deleted_at IS NULL` Instead of `WHERE deleted_at = NULL`**
Some databases (like PostgreSQL) treat `NULL` and `NOT NULL` differently in queries.

**Fix:** Always use:
```sql
SELECT * FROM users WHERE deleted_at IS NULL;  -- ✅ Correct
SELECT * FROM users WHERE deleted_at = NULL;   -- ❌ Works in PostgreSQL, but avoid in SQL Server/Sybase
```

---

## Key Takeaways

✅ **Soft delete is great for data retention** but must be optimized.
✅ **Always index the soft delete column** (`deleted_at` or `is_deleted`).
✅ **Filter deleted records in every query** to prevent inconsistent data.
✅ **Use batch operations** for large deletions to avoid locking.
✅ **Avoid full table scans**—ensures queries remain fast at scale.
❌ **Don’t forget indexes**—performance suffers without them!
❌ **Don’t rely on application logic alone**—filter at the database level.

---

## Conclusion: Soft Delete Done Right

Soft delete is a **powerful pattern** for preserving data while keeping your UI clean. However, **poor implementation leads to slow queries, data inconsistencies, and scaling issues**.

By:
1. **Indexing `deleted_at`** for fast filtering,
2. **Enforcing soft delete in all queries**, and
3. **Optimizing for batch operations** when needed,

you can maintain **high performance** even as your dataset grows.

### Final Thought
> *"A well-indexed soft delete is like a well-oiled machine—it runs smoothly under load."*

Now go implement this in your next project! 🚀

---
**Got questions?** Drop them in the comments, and let’s discuss best practices in the comments below!
```

This post is **practical, code-first, and honest about tradeoffs**, making it perfect for beginner backend developers while still being useful for intermediate engineers. The examples cover multiple languages (SQL, Python, PHP) and database systems (PostgreSQL, Django, Laravel).