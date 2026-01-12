# **"Databases Gotchas: Hidden Pitfalls Every Backend Dev Should Avoid"**

Most backend developers start by writing a simple `SELECT * FROM users`—and it works. Until it doesn’t.

Databases seem straightforward at first: store data, query it, move on. But real-world applications quickly expose hidden quirks—**gotchas**—that can break performance, correctness, or even your entire system. Some are subtle SQL quirks, others stem from misaligned tooling, and some arise from assumptions that don’t hold under load.

This guide is your **cheat sheet for database anti-patterns**. We’ll cover the most common pitfalls—with real examples (and how to fix them)—so you can debug issues before they cause production outages.

---

## **The Problem: Why "It Works on My Machine" is Dangerous**

You’ve probably seen this before:
```sql
-- ✅ Works locally
SELECT * FROM users WHERE email = 'user@example.com';

-- ❌ Fails in production with "Table is locked"
-- (Same query, but now 100 users are querying simultaneously)
```

Databases aren’t just storage—they’re **stateful systems** with quirks tied to:
1. **Concurrency** – How multiple transactions interact.
2. **Range Queries** – Why `WHERE id > 1000` is slower than `WHERE name = 'Alice'`.
3. **Hardware & Config** – Disk I/O, memory limits, and the dreaded `OOM` (Out-of-Memory) crash.
4. **Schema Design** – How `NULL` values and missing indexes can silently corrupt queries.
5. **Tooling Assumptions** – ORMs, pagination, and "obvious" solutions that backfire.

Gotchas often appear when:
- Your app scales from 100 to 10,000 users.
- A "simple" query takes seconds (or minutes) in production.
- Data suddenly disappears or duplicates itself.

---

## **The Solution: How to Hunt Down Database Gotchas**

The best defense is **awareness + testing**. We’ll break down the most common gotchas into categories, explain why they happen, and show how to diagnose and fix them.

### **Key Strategies:**
✅ **Test under load** – Use tools like `k6` or `locust` to simulate traffic.
✅ **Monitor slow queries** – Check `pg_stat_statements` (PostgreSQL) or `EXPLAIN ANALYZE`.
✅ **Write defensive queries** – Assume databases lie (they sometimes do).
✅ **Use transactions wisely** – Too many = contention; too few = dirty reads.
✅ **Benchmark locally** – What works in your IDE might fail in production.

---

## **Gotcha 1: "Why is `SELECT *` Slower Than `SELECT id, name`?"**

### **The Problem**
You run:
```sql
-- Works fine locally
SELECT * FROM users WHERE email = 'test@example.com';

-- But in production, it takes 3 seconds!
```
Why? Because `SELECT *` pulls **all columns**, even unused ones, which:
- Increases network overhead (more data to transfer).
- Forces the database to compute unused fields (e.g., sorting a `JSON` column you never read).

### **The Fix**
**Always specify columns explicitly.**
```sql
-- ✅ Faster, fewer bytes transferred
SELECT id, email, first_name FROM users WHERE email = 'test@example.com';
```

### **Code Example (Node.js + Prisma)**
```javascript
// ❌ Slow (fetches ALL columns)
const slowUser = await prisma.user.findUnique({
  where: { email: 'test@example.com' },
});

// ✅ Optimized (only fetch needed fields)
const fastUser = await prisma.user.findUnique({
  where: { email: 'test@example.com' },
  select: { id: true, email: true, firstName: true }, // Explicit columns
});
```

### **Key Takeaway**
- `SELECT *` is **lazy**—it assumes you need everything. **You don’t.**
- Use **projections** (ORMs call them `select`) to limit returned data.

---

## **Gotcha 2: "NULL Values Are Not Zero"**

### **The Problem**
You write:
```sql
-- ❌ Incorrect: NULL + 5 = NULL (not 5)
SELECT age + 5 FROM users WHERE age IS NULL;

-- ❌ Also wrong: NULL = 0 is FALSE (NULL is a special "unknown" value)
SELECT * FROM orders WHERE shipping_cost = 0 OR shipping_cost IS NULL;
```

### **The Fix**
- Use `COALESCE` or `ISNOT NULL` for NULL handling.
- **Never compare `NULL` directly**—it’s never equal to anything.

```sql
-- ✅ Correct: Treat NULL as 0
SELECT COALESCE(age, 0) + 5 AS adjusted_age FROM users;

-- ✅ Safe NULL check
SELECT * FROM orders WHERE shipping_cost = 0 OR shipping_cost IS NULL;
```

### **Code Example (Python + SQLAlchemy)**
```python
# ❌ This won't work as expected
user = session.query(User).filter(User.age == 0).first()

# ✅ Handle NULL properly
users = session.query(User).filter(
    or_(
        User.age == 0,
        User.age.is_(None)  # SQLAlchemy's way of saying "IS NULL"
    )
).all()
```

### **Common Mistake**
Assuming `NULL` behaves like `None` in code:
```python
# ❌ WRONG: NULL != 0 in SQL, but None != 0 in Python
if user.age == 0 or user.age is None:
    # Fails if age is NULL in the database
```

### **Key Takeaway**
- **NULL ≠ 0, NULL ≠ None**—treat them as "unknown."
- Use `COALESCE` for defaults or `IS NOT NULL` for checks.

---

## **Gotcha 3: "Why Is My Pagination So Slow?"**

### **The Problem**
You implement pagination like this:
```sql
-- ❌ Bad: Scales poorly for large datasets
SELECT * FROM posts
WHERE user_id = 123
ORDER BY created_at DESC
LIMIT 10 OFFSET 100;  -- Slow for large offsets!
```

When `OFFSET 100` is called on a table with 1M rows, the database:
1. Scans all 100,000 rows before the 101st one.
2. Uses **sequential I/O** (slow) instead of indexed seeks.

### **The Fix: Use Keyset Pagination**
```sql
-- ✅ Fast: Uses indexes efficiently
SELECT * FROM posts
WHERE user_id = 123
AND created_at < '2023-01-01T00:00:00Z'  -- "Before" cursor
ORDER BY created_at DESC
LIMIT 10;
```

### **Code Example (Node.js + PostgreSQL)**
```javascript
// ❌ Slow (OFFSET-based)
const posts = await prisma.post.findMany({
  where: { userId: 123 },
  orderBy: { createdAt: 'desc' },
  skip: 100,  // ❌ Bad for large datasets
  take: 10,
});

// ✅ Optimized (keyset pagination)
async function getPaginationCursor(cursor = null) {
  const where = cursor
    ? { userId: 123, createdAt: { lt: new Date(cursor) } }
    : { userId: 123 };

  return await prisma.post.findMany({
    where,
    orderBy: { createdAt: 'desc' },
    take: 10,
  });
}
```

### **Key Takeaway**
- **OFFSET is evil for large datasets**—use keyset pagination instead.
- Always **index columns used in pagination** (`created_at` in this case).

---

## **Gotcha 4: "Why Are My Transactions Slow?"**

### **The Problem**
You wrap everything in transactions:
```sql
BEGIN TRANSACTION;
-- ❌ Too many slow operations
UPDATE users SET balance = balance - 100 WHERE id = 1;
UPDATE users SET balance = balance + 100 WHERE id = 2;
-- Long-running query...
COMMIT;
```
This causes:
- **Lock contention** (other queries wait for the transaction to finish).
- **Network overhead** (each query in a transaction adds latency).

### **The Fix: Short Transactions = Happy Databases**
- **Keep transactions short** (milliseconds, not seconds).
- **Batch updates** when possible.
- **Use `SAVEPOINT` for partial rollbacks** (instead of full transactions).

```sql
-- ✅ Optimized: Minimal transaction scope
BEGIN;
UPDATE users SET balance = balance - 100 WHERE id = 1;
UPDATE users SET balance = balance + 100 WHERE id = 2;  -- Now in same transaction
COMMIT;
```

### **Code Example (Python + SQLAlchemy)**
```python
# ❌ Long transaction (bad)
with session.begin():
    user = session.get(User, user_id)
    user.balance -= 100
    session.commit()  # ❌ Too late to detect errors

    # Slow operation...
    session.commit()  # ❌ Still too slow

# ✅ Short transaction (good)
try:
    session.begin()  # Auto-rolls on error
    user = session.get(User, user_id)
    user.balance -= 100
    session.commit()  # Fast rollback if something fails
except Exception as e:
    session.rollback()
    raise e  # Let caller handle
```

### **Key Takeaway**
- **Transactions should be fast** (milliseconds, not seconds).
- **Avoid `BEGIN`/`COMMIT` as decorators**—it’s a smell.

---

## **Gotcha 5: "Why Did My Data Disappear?"**

### **The Problem**
You run:
```sql
-- ❌ Missing WHERE clause = accidental deletion!
DELETE FROM users WHERE id IN (SELECT id FROM users WHERE age < 18);
```
But if `age` is `NULL` for some users, the `WHERE` clause silently fails, **deleting only non-NULL rows**.

### **The Fix: Use `IN` with `NULL` Handling**
```sql
-- ✅ Safe: Explicitly exclude NULLs
DELETE FROM users
WHERE id IN (
    SELECT id FROM users
    WHERE age < 18 OR age IS NULL  -- Now NULLs are included
);
```

### **Code Example (Node.js + Prisma)**
```javascript
// ❌ DANGER: Missing NULL check
await prisma.user.deleteMany({
  where: {
    age: { lt: 18 },  // ❌ Ignores NULL
  },
});

// ✅ Safe: Handle NULLs explicitly
await prisma.user.deleteMany({
  where: {
    OR: [
      { age: { lt: 18 } },
      { age: null },  // Explicit NULL case
    ],
  },
});
```

### **Key Takeaway**
- **Always check for `NULL` in critical queries.**
- **Test edge cases** (empty tables, `NULL` values).

---

## **Gotcha 6: "Why Is My ORM Slow?"**

### **The Problem**
You write:
```javascript
// ❌ Slow ORM "magic"
const user = await prisma.user.findUnique({ where: { email: 'test@example.com' } });
```
But under the hood, Prisma (or your ORM) might:
- Run **N+1 queries** (fetching users, then fetching each user’s posts).
- **Over-fetch columns** (like `SELECT *`).
- **Use eager-loading** without realizing it’s expensive.

### **The Fix: Optimize Query Plans**
```javascript
// ✅ Optimized: Explicit relations & columns
const user = await prisma.user.findUnique({
  where: { email: 'test@example.com' },
  select: { id: true, email: true, posts: { take: 5 } },  // Limit posts
});
```

### **Common ORM Pitfalls**
| Anti-Pattern               | Fix                          |
|----------------------------|------------------------------|
| `findMany()` + `.map()`    | Use `include` for relations  |
| `findUnique()` without `select` | Explicit columns          |
| Lazy-loading (e.g., Django’s `select_related`) | Force eager loading |

### **Key Takeaway**
- **ORMs are abstractions—treat them like they’re slow.**
- **Always review generated SQL** with `console.log(query)` (Prisma) or `explain: true`.

---

## **Gotcha 7: "Why Is My Index Not Being Used?"**

### **The Problem**
You add an index:
```sql
CREATE INDEX idx_user_email ON users(email);
```
But queries still scan the entire table:
```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';
```
Result:
```
Seq Scan on users  (cost=0.00..18.12 rows=1 width=120)  -- ❌ Full table scan!
```
**Why?** The query might not match the index due to:
- **Missing `SELECT` columns** (index only helps if the `WHERE` uses indexed columns).
- **Function calls on indexed fields** (e.g., `WHERE LOWER(email) = 'test'`).
- **Too many `OR` conditions** (indexes help with `AND`, not `OR`).

### **The Fix: Force Index Usage**
```sql
-- ✅ Use index by matching the query structure
SELECT * FROM users WHERE email = 'test@example.com';  -- ✅ Uses idx_user_email

-- ❌ Won't use index: Function call on email
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- ✅ Solution: Add a functional index
CREATE INDEX idx_user_email_lower ON users(LOWER(email));
```

### **Code Example (PostgreSQL)**
```sql
-- ❌ Won't use index (OR clause prevents it)
EXPLAIN ANALYZE
SELECT * FROM users
WHERE email = 'test@example.com' OR age < 18;

-- ✅ Narrows down with AND first
EXPLAIN ANALYZE
SELECT * FROM users
WHERE email = 'test@example.com' AND age < 18;  -- ✅ Uses indexes
```

### **Key Takeaway**
- **Indexes only help with `=` and `IN` (not `LIKE`, `>`).**
- **Test with `EXPLAIN ANALYZE`**—is it using the index?
- **Avoid `OR` in indexed queries** (unless you add composite indexes).

---

## **Gotcha 8: "Why Does My App Crash on `OUT OF MEMORY`?"**

### **The Problem**
You run:
```sql
-- ❌ Memory hog: Brings ALL rows into RAM
SELECT * FROM huge_log_table WHERE created_at > '2023-01-01';
```
If the table is **bigger than RAM**, PostgreSQL:
1. **Grinds to a halt** (disk I/O is slow).
2. **Crashes with "Out of Memory"** (PostgreSQL has a `work_mem` limit).

### **The Fix: Use `LIMIT` + Streaming**
```sql
-- ✅ Safe: Processes in chunks
SELECT * FROM huge_log_table
WHERE created_at > '2023-01-01'
ORDER BY created_at
LIMIT 1000;  -- Process one batch at a time
```

### **Code Example (Python + Pandas)**
```python
# ❌ WRONG: Loads everything into memory
df = pd.read_sql("SELECT * FROM huge_log_table", conn)

# ✅ RIGHT: Use chunks
chunk_size = 10000
for chunk in pd.read_sql_query(
    "SELECT * FROM huge_log_table WHERE created_at > '2023-01-01'",
    conn,
    chunksize=chunk_size
):
    process_chunk(chunk)  # Process one chunk at a time
```

### **Database Config Tips**
| Setting               | Recommended Value          | Why                          |
|-----------------------|----------------------------|------------------------------|
| `work_mem`            | `16MB`–`64MB`              | Limits memory per query      |
| `shared_buffers`      | `25% of RAM`               | More = faster queries        |
| `maintenance_work_mem`| `1GB`–`4GB`                | Helps `VACUUM`, `REINDEX`     |

### **Key Takeaway**
- **Never assume the database fits in RAM.**
- **Use `LIMIT` + pagination** for large datasets.
- **Monitor memory usage** (`pg_stat_activity` in PostgreSQL).

---

## **Implementation Guide: How to Avoid Gotchas**

### **1. Start with a Database Schema Review**
- **Never let `NULL` creep in**—define defaults (`NOT NULL` for required fields).
- **Index frequently queried columns** (`WHERE`, `ORDER BY`, `JOIN`).
- **Avoid `SELECT *`**—list columns explicitly.

### **2. Test Under Load**
- Simulate traffic with `k6` or `locust`.
- Use **slow query logs** to find bottlenecks.

### **3. Write Defensive Queries**
- **Assume databases lie**—add `LIMIT` where possible.
- **Handle `NULL` explicitly** (use `COALESCE`, `IS NOT NULL`).
- **Avoid `OR` in indexed queries** (use `AND` + composite indexes).

### **4. Monitor Performance**
- **Check `EXPLAIN ANALYZE`** for slow queries.
- **Use `pg_stat_statements` (PostgreSQL)** to track slow queries.
- **Set up alerts** for long-running transactions.

### **5. Choose Your Tools Wisely**
| Tool          | Gotcha to Watch For               | Fix                          |
|---------------|-----------------------------------|------------------------------|
| **Prisma**    | Over-fetching, N+1 queries        | Use `select` + `include`      |
| **Django ORM**| Lazy-loading, `select_related`     | Force eager loading           |
| **Sequelize** | Raw SQL injection risks           | Use `where` clauses carefully |
| **MongoDB**   | No joins, schema flexibility      | Denormalize or use `lookup`   |

---

## **Common Mistakes to Avoid**

| Mist