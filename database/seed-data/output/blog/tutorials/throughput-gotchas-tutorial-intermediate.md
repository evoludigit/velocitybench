```markdown
# **Throughput Gotchas: How Your System’s Performance Slowly Unravels**

## **Introduction**

You’ve designed a scalable system. Your API handles connections gracefully. The load tests passed. But six months later, users complain of sluggish responses. What happened?

The culprit is rarely a single component—but rather, **throughput gotchas**: subtle performance bottlenecks that creep in under normal operational loads. These aren’t obvious at first glance. They arise from cumulative inefficiencies in query patterns, connection management, caching strategies, and even seemingly benign choices like batching or parallelism.

This guide dissects the most common throughput gotchas in **database and API design**, reveals how they manifest, and provides actionable fixes. We’ll look at:
- **Data access patterns** that silently drain performance
- **Resource leaks** in connection pooling and batching
- **Over-engineered optimizations** that backfire
- **Caching anti-patterns** that make things worse

By the end, you’ll know how to spot these pitfalls and design systems that stay fast—even as traffic grows.

---

## **The Problem: Throughput Gotchas in Action**

Let’s start with a real-world example. Consider a **user profile service** that fetches user data, their posts, and comments in real-time.

### **The Illusion of Scalability (And Why It Fails)**
Here’s a seemingly efficient design (in JavaScript, with PostgreSQL):

```javascript
// Pseudo code: "The Optimistic Fetch"
async function getUserProfile(userId) {
  // Fetch user data
  const user = await db.query(`
    SELECT * FROM users WHERE id = $1
  `, [userId]);

  // Fetch user posts (50 max)
  const posts = await db.query(`
    SELECT * FROM posts
    WHERE user_id = $1
    ORDER BY created_at DESC
    LIMIT 50
  `, [userId]);

  // Fetch comments for each post (inefficient)
  const comments = await Promise.all(posts.rows.map(post =>
    db.query(`
      SELECT * FROM comments
      WHERE post_id = $1
      ORDER BY created_at DESC
      LIMIT 10
    `, [post.id])
  ));

  return { user, posts, comments };
}
```

This looks fine in development. But when 10,000 users hit it concurrently:

- **Problem 1**: Each user spins up a new connection, exhausting the pool.
- **Problem 2**: 50 `LIMIT 10` queries per user = **500 queries** per request.
- **Problem 3**: PostgreSQL’s default `LIMIT` + `ORDER BY` triggers full table scans for each subquery.

The database *could* handle this… if the queries were optimized. But they’re not. The system **gradually slowing down** under load—**not because it’s overloaded, but because it’s ineffeciently designed**.

---

## **The Solution: How to Avoid Throughput Gotchas**

The key is to think about **throughput holistically**: not just one query, but the entire request lifecycle. Here’s how to approach it:

### **1. Measure Before You Optimize**
Before diving into fixes, **profile real-world usage**. Use tools like:
- **Database**: `pg_stat_statements` (PostgreSQL), `EXPLAIN ANALYZE`, or slow query logs.
- **API**: APM tools (Datadog, New Relic) or custom instrumentation (e.g., `requestDuration` metrics).

Example: Add this to PostgreSQL config:
```sql
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
```

### **2. Optimize the Query *First***
Bad queries kill throughput. Common culprits:
- **Missing indexes** on `JOIN` fields, `WHERE` clauses, or `ORDER BY`.
- **N+1 queries** (like in the example above).
- **SELECT *** (fetching unused columns increases I/O).
- **Unbounded `LIMIT`** or missing pagination.

#### **Fixed Example: Efficient User Profile Fetch**
```sql
-- Pre-built views for performance
CREATE VIEW user_posts AS
  SELECT p.*, c.comments_count
  FROM posts p
  LEFT JOIN (
    SELECT post_id, COUNT(*) as comments_count
    FROM comments
    GROUP BY post_id
  ) c ON p.id = c.post_id
  WHERE p.user_id = $1
  ORDER BY p.created_at DESC
  LIMIT 50;

-- Then fetch in a single query
async function getUserProfileOptimized(userId) {
  const [user, posts] = await Promise.all([
    db.query(`
      SELECT * FROM users WHERE id = $1
    `, [userId]),
    db.query(`
      SELECT * FROM user_posts WHERE user_id = $1
    `, [userId])
  ]);

  return { user, posts };
}
```

Key improvements:
- **Eliminated 50 N+1 queries** → now just **2 queries total**.
- **Pre-computed comments count** in the view (avoids extra `JOIN`s).
- **Used LIMIT** on the posts view.

---

### **3. Connection Pooling: Don’t Let It Leak**
If your app creates a new connection per request, **throughput tanks after 100 users**.

#### **Bad:**
```javascript
// Lets 10,000 users hog connections
db.query("SELECT ...");
```

#### **Good:**
```javascript
// Configure a pool (e.g., `pg-pool` for PostgreSQL)
const pool = new Pool({
  max: 20, // Adjust based on your DB
  idleTimeoutMillis: 30000
});

// Reuse connections
async function fetchData() {
  const client = await pool.connect();
  try {
    const res = await client.query("SELECT ...");
    return res;
  } finally {
    client.release(); // Critical: always release!
  }
}
```

---

### **4. Batching: When Less Is More**
Parallelism feels fast, but **too many concurrent queries** can block the server or exhaust resources.

#### **Bad:**
```javascript
// Spins up 500+ queries for 10 users
await Promise.all(users.map(userId => db.query(...)));
```

#### **Good: Batch by Time or Workload**
```javascript
// Group queries into batches (e.g., 50 per batch)
async function batchFetch(users, batchSize = 50) {
  const batches = chunk(users, batchSize);
  return await Promise.all(
    batches.map(batch =>
      db.query(`
        SELECT * FROM users
        WHERE id IN ($1, $2, ...)
      `, batch.map(id => `$${batch.indexOf(id) + 1}`)
    )
  );
}
```

---

### **5. Caching: Cache the Right Thing**
Caching is a double-edged sword. **Bad caching** (e.g., too many small blobs) can **increase memory pressure** and hurt throughput.

#### **Anti-Pattern:**
```javascript
// Cache every single query result
cache.set(`user:${id}`, userData);
```

#### **Better:**
```javascript
// Cache at the right level (e.g., user profile, not individual posts)
cache.set(`user:${id}:profile`, {
  user,
  lastUpdated: Date.now()
});

// Expire aggressively (e.g., 10 mins)
```

---

## **Implementation Guide**
Here’s a step-by-step plan to audit and fix throughput bottlenecks:

1. **Profile First**: Use `EXPLAIN ANALYZE`, APM tools, or custom metrics.
2. **Fix Queries**:
   - Add missing indexes.
   - Replace N+1 with `JOIN` or materialized views.
   - Avoid `SELECT *`.
3. **Optimize Connection Pooling**:
   - Configure max connections.
   - Always release clients (`finally` block!).
4. **Batch External Calls**:
   - Group DB/API calls into batches.
   - Use coalescing for repeated queries.
5. **Leverage Caching Wisely**:
   - Cache at the right granularity (e.g., user profiles, not rows).
   - Use TTLs to reduce stale data.
6. **Monitor Over Time**:
   - Set up alerts for query latency spikes.
   - Log slow queries automatically.

---

## **Common Mistakes to Avoid**
| **Mistake**                          | **Why It’s Bad**                                      | **Fix**                                  |
|---------------------------------------|-------------------------------------------------------|------------------------------------------|
| **Ignoring `SELECT *`**               | Fetches unnecessary data, increasing I/O.             | Explicitly list columns.                 |
| **No connection cleanup**            | Leaks connections, causing pool exhaustion.          | Always `release()` or use `finally`.      |
| **Unbounded `LIMIT`**                 | Forces full table scans, even if results are small.    | Always add `LIMIT` + `OFFSET` for pagination. |
| **Over-caching small objects**        | Increases memory pressure, hurting throughput.       | Cache at higher levels (e.g., user IDs, not rows). |
| **Parallelizing too aggressively**    | Starves the DB or server with too many connections. | Batch requests or use async pooling.     |

---

## **Key Takeaways**
- **Throughput gotchas** are often **cumulative**, not obvious in small-scale tests.
- **Fix queries first**—bad SQL is the #1 throughput killer.
- **Pool connections** and **release them properly** to avoid leaks.
- **Batch calls** when appropriate (e.g., DB queries, API calls).
- **Cache strategically**—avoid tiny blobs; think at higher levels.
- **Monitor over time**—what works at 100 users may fail at 10,000.

---

## **Conclusion**
Throughput gotchas are the silent assassins of scalability. They don’t crash your system overnight—they **eat performance slowly**, making users frustrated without obvious cause.

The good news? These issues are **preventable**. By:
✅ Profiling early and often,
✅ Writing efficient queries,
✅ Managing connections and batches wisely,
✅ Caching at the right level,

you can build systems that stay fast **even as traffic grows**.

**Next steps:**
- Audit your slowest API routes with `EXPLAIN ANALYZE`.
- Set up connection pooling with proper timeouts.
- Implement batching for repeated queries.

Now go fix that throughput—before it fixes itself (by becoming slow).

---
**Want more?** Check out:
- [PostgreSQL Indexing Guide](https://use-the-index-luke.com/)
- [Connection Pooling Best Practices](https://www.pgpool.net/docs/latest/en/html/runtime-config-connection.html)
```