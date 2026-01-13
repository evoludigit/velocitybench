---
title: "Efficiency Conventions: The Pattern That Makes Your Queries Run Faster (Without Rewriting Everything)"
date: "2024-02-15"
---

---

# Efficiency Conventions: The Pattern That Makes Your Queries Run Faster (Without Rewriting Everything)

## Introduction

You’ve seen it before. A perfectly functional application that suddenly slows to a crawl as users hit scale. Maybe it works fine locally but breaks under production load. Or perhaps your team spends more time optimizing individual queries than shipping new features. **The problem isn’t the tools—it’s the conventions.**

Efficiency isn’t just about writing optimized SQL or caching every endpoint. It’s also about *how you design your patterns*. That’s where the **Efficiency Conventions pattern** comes in. It’s not a framework or a new library, but a set of system-level agreements that make it easier to write efficient code *by default*. The best part? You can start applying it today without exhaustively rewriting legacy apps.

In this guide, we’ll break down how efficiency conventions work, why they matter, and how to implement them in a way that scales with your application. We’ll explore database schemas, indexing strategies, query patterns, and even how to balance consistency with performance. By the end, you’ll have a clear, actionable plan to reduce database overhead and speed up your APIs—without refactoring the entire codebase.

---

## The Problem: Why Your Code Feels Like a Sloth Race

Imagine this common scenario:

1. A new feature request comes in: *"Let users filter products by price range and category."*
2. The developer implements it with a simple `WHERE` clause and joins three tables.
3. It works in development, but after deployment, the response time jumps from 50ms to 2 seconds under load.
4. Debugging reveals that the query is scanning 90% of the `products` table because of missing indexes.
5. The developer adds an index, but the fix breaks in other places, or the index creation slows down writes.

This isn’t a failure—it’s a lack of *system-level efficiency conventions*. Without these, every optimization becomes a guess or a reactive fix. Developers don’t have a consistent way to think about performance, leading to:

- **Inconsistent indexes**: Some tables have the right indexing, others don’t.
- **Avoiding joins**: Teams add redundant columns to tables to "avoid joins," bloating the database schema.
- **Over-caching**: Some endpoints are cached aggressively (slowing down writes), others are not cached at all (causing latency).
- **Ad-hoc schema design**: New tables are added without considering how they’ll be queried.
- **Unpredictable performance**: Endpoints work fine for some users but fail for others based on the data they access.

Efficiency conventions solve this by creating a **shared baseline** for how your team writes code. They turn performance from a "nice-to-have" into a "built-in" part of the system.

---

## The Solution: A Framework for Writing Efficient Code by Default

The **Efficiency Conventions** pattern is a system of rules and standards that guide your team to write performant code *without requiring constant optimization*. It consists of four key pillars:

1. **Database Efficiency Rules**: How to structure schemas, indexes, and queries.
2. **API Efficiency Rules**: How to design endpoints and responses.
3. **Caching & Optimization Strategies**: When and how to cache, and what to avoid.
4. **Performance Monitoring & Enforcement**: How to ensure conventions are followed.

### Why Conventions Work Better Than "Optimizing Later"
If you wait until performance becomes a problem, you’re stuck playing whack-a-mole. Conventions work because:
- They make performance predictable.
- They reduce the cost of scaling.
- They don’t require every developer to be a performance expert.

Let’s dive into each pillar.

---

## Components/Solutions: Building Your Efficiency Conventions

### **1. Database Efficiency Rules**

#### Schema Design Conventions
**Rule:** *Design tables to match common query patterns.*

If your team frequently queries `users` with `WHERE status = 'active' AND created_at > '2023-01-01'`, your schema should reflect that. Avoid "de-normalizing" tables to "avoid joins"—joins are fine if they’re optimized.

```sql
-- Bad: Table with 20 columns just to avoid joins
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2),
    stock INT,
    last_updated TIMESTAMP,
    category_id INT,
    brand_id INT,
    -- And 15 more columns...
    attributes JSONB  -- Hiding complexity behind JSON
);

-- Good: Narrow tables with clear join paths
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2),
    stock INT,
    last_updated TIMESTAMP,
    category_id INT REFERENCES categories(id),
    brand_id INT REFERENCES brands(id),
    description TEXT
);

CREATE TABLE product_attributes (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    key VARCHAR(50),
    value TEXT
);
```

**Why it works:**
- Smaller tables = faster scans.
- Clear joins = predictable performance.
- JSON fields should be used sparingly (they’re slow to query).

#### Indexing Conventions
**Rule:** *Index columns that are always filtered or joined.*

Not all columns need indexes. But if a column is in a `WHERE`, `JOIN`, or `ORDER BY`, it should have one—unless it’s a unique constraint (which already indexes it).

```sql
-- Bad: No index on a frequently queried column
SELECT * FROM orders WHERE customer_id = 123;

-- Good: Index on customer_id
CREATE INDEX idx_orders_customer_id ON orders(customer_id);

-- Also good: Partial index if only some values are queried
CREATE INDEX idx_orders_active_customers ON orders(customer_id) WHERE status = 'active';
```

**Partial indexes** (`WHERE` clause) save space and improve performance when only a subset of data is relevant.

#### Query Pattern Conventions
**Rule:** *Standardize how complex queries are written.*

Poorly written queries are often the root of performance problems. Enforce these:
- **Limit `SELECT *`**: Only fetch what you need.
- **Use `EXPLAIN ANALYZE`**: Always run this before production queries.
- **Avoid `DISTINCT ON` with large datasets**: It forces a full sort.
- **Use `WITH` clauses (`CTEs`) for readability, not raw joins**.

```sql
-- Bad: Scans the entire table, returns unnecessary data
SELECT * FROM users WHERE status = 'active';

-- Good: Only selects needed columns, includes index
SELECT id, email, created_at
FROM users
WHERE status = 'active'
ORDER BY created_at DESC
LIMIT 100;

-- Even better: Add an index on (status, created_at)
CREATE INDEX idx_users_status_created_at ON users(status, created_at);
```

---

### **2. API Efficiency Rules**

#### Response Design Conventions
**Rule:** *Only return what the client needs.*

APIs should follow the **"least surprise"** principle for clients. If a frontend only uses `id`, `name`, and `price`, don’t send the entire user object.

```json
// Bad: Sending 50 fields when only 3 are used
{
    "id": 1,
    "name": "Widget",
    "price": 9.99,
    "stock": 100,
    "last_updated": "2023-01-01",
    "attributes": { "color": "red", "weight": "1kg" },
    "metadata": { ... },
    // ... 47 more fields
}

// Good: Only send what’s needed
{
    "id": 1,
    "name": "Widget",
    "price": 9.99
}
```

**Tooling tip:** Use **OpenAPI/Swagger** to document expected responses and enforce them with API gateways (e.g., Kong, Apigee).

#### Pagination Conventions
**Rule:** *Always paginate results.*

Without pagination, a `LIMIT 1000` query can still return a huge response. Enforce:
- **Cursor-based pagination** (better for performance than `LIMIT/OFFSET`).
- **Default `LIMIT` of 20-50 items** (balance usability and load).

```sql
-- Bad: Heavy pagination (slow for large offsets)
SELECT * FROM posts WHERE user_id = 1 ORDER BY created_at LIMIT 10 OFFSET 5000;

-- Good: Cursor-based pagination
WITH ranked_posts AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY created_at) AS row_num
    FROM posts
    WHERE user_id = 1
)
SELECT * FROM ranked_posts
WHERE row_num BETWEEN 1 AND 100
ORDER BY created_at;
```

---

### **3. Caching & Optimization Strategies**

#### Cache Invalidation Conventions
**Rule:** *Cache aggressively, but invalidate smartly.*

Caching is powerful, but it’s useless if the data is stale. Enforce:
- **TTL-based caching** for dynamic data (e.g., 5-15 minutes).
- **Event-based invalidation** for critical data (e.g., Redis pub/sub for `users` changes).
- **Avoid caching writes** (use optimistic concurrency control instead).

```python
# Bad: Cache everything for 1 hour (stale data)
CACHE.set(f"products_{product_id}", product_data, timeout=3600)

# Good: Use short TTL + event-based invalidation
CACHE.set(f"products_{product_id}", product_data, timeout=300)  # 5 minutes
# On product update:
CACHE.delete(f"products_{product_id}")
```

#### Batch Operations Conventions
**Rule:** *Avoid N+1 queries.*

The classic **N+1 problem** happens when you query a list, then loop and query each item individually.

```python
# Bad: N+1 queries
posts = db.session.query(Post).filter_by(user_id=1).all()
for post in posts:
    comments = db.session.query(Comment).filter_by(post_id=post.id).all()
    # Work with comments...
```

**Fix:** Use **eager loading** (ORM) or **join-based queries**.

```python
# Good: Join-based query (1 query)
posts = db.session.query(Post, Comment).join(Comment).filter(Post.user_id == 1).all()

# OR (ORM eager loading)
posts = db.session.query(Post).options(
    joinedload(Post.comments)
).filter_by(user_id=1).all()
```

---

### **4. Performance Monitoring & Enforcement**

#### Query Logging Conventions
**Rule:** *Log slow queries automatically.*

Use middleware to log queries above a threshold (e.g., 50ms).

```python
# Django example (using django-debug-toolbar)
DEBUG_TOOLBAR_PANELS = [
    "debug_toolbar.panels.versions.VersionsPanel",
    "debug_toolbar.panels.timer.TimerPanel",
    "debug_toolbar.panels.settings.SettingsPanel",
    "debug_toolbar.panels.headers.HeadersPanel",
    "debug_toolbar.panels.request.RequestPanel",
    "debug_toolbar.panels.sql.SQLPanel",  # Log all SQL queries
]
```

**Red flags to alert on:**
- Queries taking >100ms.
- Full table scans (`Seq Scan` in PostgreSQL).
- Missing indexes (`index scan using ...`).

#### Performance Review Conventions
**Rule:** *Review PRs for performance before merging.*

Add a **performance checklist** to your PR template:
1. Did you add indexes for new query patterns?
2. Did you test with realistic data volumes?
3. Did you avoid `SELECT *`?
4. Is this code cache-friendly?

---

## Implementation Guide: How to Adopt Efficiency Conventions

### Step 1: Audit Your Current Codebase
Start by identifying the biggest performance bottlenecks:
- Run `EXPLAIN ANALYZE` on slow queries.
- Check slow query logs.
- Look for tables with high write/read ratios (index tuning is critical here).

### Step 2: Define Your Conventions
Create a **team doc** (e.g., in Google Docs or Confluence) with rules like:
```
DATABASE EFFICIENCY RULES:
1. Use `EXPLAIN ANALYZE` before writing production code.
2. Index all columns used in `WHERE`, `JOIN`, or `ORDER BY`.
3. Avoid `SELECT *`—list exact columns.
4. Use cursor-based pagination.

API EFFICIENCY RULES:
1. Only return fields the client uses.
2. Default `LIMIT` to 20.
3. Cache responses with 5-minute TTL unless data is volatile.

CACHING RULES:
1. Invalidate cache on writes.
2. Use Redis for short-lived data, CDN for static assets.
```

### Step 3: Enforce with Code
Use tools to enforce conventions:
- **Database:** Add schema migrations that set up indexes.
- **Application:** Use linters (e.g., SQLFluff for SQL, pylint for Python).
- **CI/CD:** Fail builds if slow queries are detected.

Example: Use `sqlfluff` to lint SQL queries:
```bash
sqlfluff lint your_app/migrations/*.sql
```

### Step 4: Educate the Team
- Run a **brownbag lunch** on efficiency conventions.
- Add a section to your onboarding docs.
- Pair new hires with experienced developers to review their queries.

### Step 5: Iterate
- Regularly review slow queries in production.
- Update conventions as your data model evolves.

---

## Common Mistakes to Avoid

### 1. Over-Indexing
**Mistake:** Adding indexes just in case.
**Problem:** Indexes slow down writes and consume storage.
**Solution:** Only index what you query.

### 2. Avoiding Joins
**Mistake:** Adding duplicate columns to avoid joins.
**Problem:** Bloats the database and makes updates harder.
**Solution:** Optimize joins instead.

### 3. Ignoring `EXPLAIN ANALYZE`
**Mistake:** Writing queries without checking their execution plan.
**Problem:** You might "optimize" a query that already works.
**Solution:** Always run `EXPLAIN ANALYZE` before production.

### 4. Over-Caching
**Mistake:** Caching everything for hours/days.
**Problem:** Stale data hurts user experience.
**Solution:** Use short TTLs + event-based invalidation.

### 5. Not Monitoring
**Mistake:** Assuming performance is "good enough."
**Problem:** Slow queries creep in silently.
**Solution:** Log and alert on slow queries.

---

## Key Takeaways

Here’s a quick checklist for implementing efficiency conventions:

✅ **Database:**
- Design tables for query patterns, not to "avoid joins."
- Index columns used in `WHERE`, `JOIN`, or `ORDER BY`.
- Avoid `SELECT *`—fetch only what you need.
- Use `EXPLAIN ANALYZE` to debug queries.

✅ **API:**
- Return only the data clients need.
- Paginate results (use cursor-based pagination).
- Cache responses with short TTLs (5-15 minutes).

✅ **Caching:**
- Invalidate cache on writes (use events).
- Avoid over-caching volatile data.
- Batch operations to avoid N+1 queries.

✅ **Enforcement:**
- Document conventions in a shared location.
- Use linters and CI/CD to enforce rules.
- Regularly review slow queries in production.

✅ **Culture:**
- Educate the team on efficiency patterns.
- Treat performance as part of the onboarding process.
- Celebrate when efficiency improvements reduce load times.

---

## Conclusion: Efficiency Conventions Are Your Secret Weapon

Performance isn’t about writing the "perfect" query—it’s about having a system that *encourages* good habits. Efficiency conventions give you that system. They turn performance from a reactive fix into a proactive part of your development process.

Start small:
1. Add indexes to your most queried tables.
2. Review your slowest API endpoints.
3. Document one convention today.

Over time, your codebase will become more predictable, scalable, and—most importantly—less likely to surprise you with performance issues. And when you *do* hit a bottleneck, you’ll know exactly where to look because your conventions have already set you up for success.

Now go write some efficient code. 🚀