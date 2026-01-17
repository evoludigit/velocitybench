```markdown
# **Performance Conventions: The Secret Sauce for Faster, Scalable APIs**

As backend developers, we spend endless hours optimizing databases, fine-tuning queries, and tuning application servers. But what if I told you that **consistent performance conventions**—small but deliberate patterns—could save you more time than any single optimization?

In this guide, we’ll explore **Performance Conventions**, a set of best practices that make APIs and databases **faster by design**. We’ll cover the problem they solve, real-world examples, and implementation tips—without overcomplicating things. By the end, you’ll have a toolkit to apply immediately, whether you’re working with PostgreSQL, MySQL, or any backend framework.

---

## **The Problem: Unintended Performance Bottlenecks**

APIs and databases often **start fast but degrade over time**. Here’s why:

1. **Inconsistent Query Patterns**
   - One developer writes `SELECT * FROM users`; another uses `JOIN` sparingly.
   - Result: Some queries are slow, others over-fetch data.

2. **No Standards for Data Access**
   - A team member uses `LIMIT 10` and `OFFSET 1000` for pagination (bad for large datasets).
   - Another uses `KEYSET` pagination (better, but inconsistent).
   - **Outcome:** Inconsistent performance across the app.

3. **Missing Caching Layers**
   - Some endpoints cache responses; others don’t.
   - Example: A `/users` endpoint fetches fresh data, but `/users/:id` is cached only sometimes.

4. **Inefficient Data Structures**
   - Storing multiple JSON fields without indexing vs. normalizing and indexing properly.
   - Example: A `products` table with `{"attributes": {"color": "red", "size": "L"}}` vs. a normalized schema with indexed columns.

5. **Overlooking Indexes**
   - Adding indexes lazily, leading to slow queries after the fact.
   - Example: A frequently queried `created_at` column **without an index** becomes a nightmare.

These issues aren’t just theoretical—they **cascade into bad habits**:
- **Debugging becomes harder** (why is this query slow?).
- **Scaling feels reactive** instead of proactive.
- **Team conflicts arise** ("Why did you add this `JOIN`?").

---

## **The Solution: Performance Conventions**

**Performance Conventions** are **code and design patterns** that:
- **Standardize how we write queries** (fetch only what’s needed).
- **Enforce consistent caching** (avoid redundant work).
- **Optimize data structures** (avoid bloated tables).
- **Add indexes proactively** (not reactively).

They’re **not about reinventing the wheel**—just **enforcing best practices** with small, repeatable rules.

---

## **Components of Performance Conventions**

### **1. Query Standardization**

#### **Rule: Always use `SELECT ...` explicitly**
**Why?** Prevents over-fetching and accidental `SELECT *`.

**Bad (over-fetching):**
```sql
SELECT * FROM products;  -- Fetches ALL columns, even unused ones
```

**Good (explicit columns):**
```sql
SELECT id, name, price FROM products;  -- Only fetches what’s needed
```

#### **Rule: Avoid `SELECT *` in JOINs**
**Why?** Joins already return extra data; explicit columns reduce noise.

**Bad:**
```sql
SELECT * FROM orders o JOIN users u ON o.user_id = u.id;
```

**Good:**
```sql
SELECT o.id, o.amount, u.email FROM orders o JOIN users u ON o.user_id = u.id;
```

#### **Rule: Use `LIMIT` + `OFFSET` sparingly (or avoid it)**
**Why?** `OFFSET 1000` is **slow** for large datasets (skips 1000 rows before fetching 1).

**Bad (expensive):**
```sql
SELECT * FROM products LIMIT 10 OFFSET 1000;  -- Scans 1001 rows
```

**Good (efficient):**
```sql
-- Use keyset pagination (better for large datasets)
SELECT * FROM products
WHERE id > 1000
ORDER BY id
LIMIT 10;
```

---

### **2. Caching Conventions**

#### **Rule: Cache at the right level (API, DB, or app level)**
**Why?** Caching too early/late wastes resources.

| Level          | When to Use                          | Example                          |
|----------------|--------------------------------------|----------------------------------|
| **API Cache**  | Public endpoints (e.g., `/users`)    | Redis, CDN                        |
| **DB Cache**   | Slow queries (e.g., complex JOINs)   | PostgreSQL `pg_cache`             |
| **App Cache**  | Short-lived in-memory data           | In-memory caches (e.g., `memcached`) |

**Example (Redis caching for `/users/:id`):**
```javascript
// FastAPI (Python) example
from fastapi import FastAPI, Depends, HTTPException
import redis

app = FastAPI()
cache = redis.Redis(host='localhost', port=6379)

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    cached_data = cache.get(f"user:{user_id}")
    if cached_data:
        return json.loads(cached_data)

    # Fallback to DB if not cached
    user = await db.execute("SELECT * FROM users WHERE id = $1", user_id)
    if not user:
        raise HTTPException(404, "User not found")

    cache.set(f"user:{user_id}", json.dumps(user), ex=3600)  # Cache for 1 hour
    return user
```

#### **Rule: Set reasonable TTLs**
**Why?** Avoid stale data while not wasting cache space.

- **Short TTL (e.g., 5 min):** Real-time data (e.g., `/orders`).
- **Long TTL (e.g., 1 hour):** Stable data (e.g., `/products`).

---

### **3. Data Structure Optimization**

#### **Rule: Normalize data where possible**
**Why?** Denormalized JSON can bloat rows and hurt performance.

**Bad (denormalized):**
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    attributes JSONB  -- Slow to query, hard to index
);
```

**Good (normalized):**
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255)
);

CREATE TABLE product_attributes (
    product_id INT REFERENCES products(id),
    key VARCHAR(50),
    value VARCHAR(255)
);

-- Now you can index:
CREATE INDEX idx_product_attributes_key ON product_attributes(key);
```

#### **Rule: Avoid redundant computations**
**Why?** Calculating values on every query slows things down.

**Bad (recomputes on each access):**
```sql
SELECT name, LENGTH(name) as name_length FROM products;
```

**Good (store computed columns):**
```sql
-- PostgreSQL example (adds a computed column)
ALTER TABLE products ADD COLUMN name_length INT;

-- Update in a transaction (or use triggers)
UPDATE products SET name_length = LENGTH(name);
```

---

### **4. Indexing Conventions**

#### **Rule: Index frequently queried columns**
**Why?** Missing indexes make queries **10-100x slower**.

**Example: Should we index `created_at`?**
```sql
-- If you frequently query "products created in the last 30 days":
CREATE INDEX idx_products_created_at ON products(created_at);
```

#### **Rule: Avoid over-indexing**
**Why?** Too many indexes slow down writes.

**Bad (too many indexes):**
```sql
-- 10 indexes on a table with 1M rows = slower writes
CREATE INDEX idx_name ON users(name);
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_created_at ON users(created_at);
-- ... and so on
```

**Good (smart indexing):**
- Index only columns used in `WHERE`, `JOIN`, or `ORDER BY`.
- Use **partial indexes** for specific conditions:
  ```sql
  CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;
  ```

---

## **Implementation Guide: How to Apply These Conventions**

### **Step 1: Define a Query Style Guide**
Create a **team doc** (or enforce in code reviews) with rules like:
✅ Always **explicitly list columns** in `SELECT`.
✅ Use **keyset pagination** instead of `OFFSET`.
✅ **Cache API responses** by default (unless they’re write-heavy).
✅ **Normalize data** where possible.

**Example (for a new project):**
```
# Team Query Conventions
1. SELECT * is forbidden. Always specify columns.
2. If pagination > 1000 items, use keyset pagination.
3. All `/read` endpoints must cache responses for 1 hour.
```

### **Step 2: Enforce Caching Early**
- **APIs:** Use middleware (e.g., FastAPI’s `@app.cache_response(ttl=3600)`).
- **Databases:** Add query caching (PostgreSQL `pg_cache`).
- **Framework-level:** Use ORM caching (e.g., Django’s `select_related` + `@cached`).

**Example (FastAPI with caching):**
```python
from fastapi import FastAPI, Response
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

app = FastAPI()
app.state.cache = RedisBackend()

@app.get("/products")
async def get_products():
    return app.state.cache.get("products", default=[])
```

### **Step 3: Audit Queries Regularly**
Use **EXPLAIN ANALYZE** to catch slow queries:
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123;
```
- Look for **full table scans** (`Seq Scan`).
- Check if missing indexes are the culprit.

**Example (slow query → fix):**
```sql
-- Before (slow)
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
-- Output: Seq Scan (full table scan)

-- After (add index)
CREATE INDEX idx_users_email ON users(email);
```

### **Step 4: Document Performance Rules**
Add a **README.md** in your project explaining:
- **Query standards** (e.g., "Never use `SELECT *`").
- **Caching policies** (e.g., "All `/read` endpoints cache for 1 hour").
- **Indexing guidelines** (e.g., "Index `created_at` if queried by date").

**Example:**
```markdown
# Performance Conventions
## Query Rules
- ❌ Avoid `SELECT *`
- ✅ Use `LIMIT` + `ORDER BY` for pagination

## Caching
- All `/api/users/*` endpoints cache for 3600s (1 hour).
```

---

## **Common Mistakes to Avoid**

| Mistake                          | Why It’s Bad                          | Fix                          |
|----------------------------------|---------------------------------------|------------------------------|
| Using `SELECT *`                 | Over-fetches data, wastes memory      | Explicitly list columns     |
| `OFFSET`-based pagination       | Slow for large datasets               | Use keyset pagination        |
| No caching                       | Repeated DB calls for same data       | Cache responses             |
| Missing indexes                  | Slow queries, even with simple logic  | Add indexes proactively      |
| Denormalizing without thinking   | Hard to query, bloats rows            | Normalize where possible     |
| Ignoring `EXPLAIN ANALYZE`       | Blindly optimizing without diagnostics | Always run `EXPLAIN` first   |

---

## **Key Takeaways**

✅ **Performance Conventions are simple but powerful**—they prevent **10x slower queries** by enforcing consistency.

✅ **Standardized queries** (explicit `SELECT`, no `*`) reduce data transfer and improve speed.

✅ **Caching at the right level** (API, DB, or app) avoids redundant work.

✅ **Normalized data + smart indexing** keeps databases fast.

✅ **Audit queries with `EXPLAIN ANALYZE`**—don’t guess why things are slow.

✅ **Document rules** so the whole team follows them.

---

## **Conclusion: Start Small, Scale Fast**

Performance Conventions aren’t about **perfect optimization**—they’re about **avoiding regressions**. By enforcing small, consistent rules, you’ll:
- **Reduce debugging time** (no "random slow queries").
- **Scale smoother** (no last-minute performance fixes).
- **Ship faster** (changes won’t break performance).

**Your first step?**
1. Pick **one rule** (e.g., "No `SELECT *`").
2. Enforce it in your next pull request.
3. Measure the impact (faster queries, happier users).

Small conventions lead to **big performance wins**—start today.

---
**Further Reading:**
- [PostgreSQL `EXPLAIN ANALYZE` Guide](https://www.postgresql.org/docs/current/using-explain.html)
- [FastAPI Caching with Redis](https://fastapi-cache-backend-redis.readthedocs.io/)
- [keyset Pagination vs. OFFSET](https://use-the-index-luke.com/sql/where-clause/slower-substring/offset)

---
```