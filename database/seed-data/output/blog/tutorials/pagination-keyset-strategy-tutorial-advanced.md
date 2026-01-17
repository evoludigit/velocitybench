```markdown
# **Keyset Pagination: The Right Way to Load Infinite Data Efficiently**

## **Introduction**

When you build a web or mobile application that queries large datasets (like timelines, search results, or product listings), you eventually hit a wall: **raw pagination with `LIMIT` and `OFFSET` sucks**.

Imagine a social media feed—if you paginate using `OFFSET`, every page request might require scanning millions of rows (even if you only display 20 items per page). This leads to slow queries, high server costs, and a terrible user experience. **Keyset pagination (also known as cursor-based pagination) solves this by replacing offsets with a logical "key" to fetch the next set of results.**

In this post, we’ll cover:
- Why traditional `LIMIT-OFFSET` pagination is broken
- How keyset pagination works (and why it’s better)
- Practical implementations in SQL, Redis, and REST APIs
- Common pitfalls and how to avoid them
- Performance benchmarks

Let’s dive in.

---

## **The Problem: Why `LIMIT-OFFSET` Pagination Fails**

Traditional pagination uses `LIMIT` and `OFFSET` to fetch chunks of data:

```sql
-- First page (items 1-10)
SELECT * FROM posts ORDER BY created_at DESC LIMIT 10 OFFSET 0;

-- Second page (items 11-20)
SELECT * FROM posts ORDER BY created_at DESC LIMIT 10 OFFSET 10;
```

### **The Hidden Costs**
1. **Slow Queries**
   - Every `OFFSET` forces the database to scan all previous rows (even if they’re already cached in memory).
   - Example: `OFFSET 1,000,000` scans **1 million rows**—even if you only need 20!

2. **Cache Bloat**
   - Databases like PostgreSQL store intermediate results in caching layers (like `pg_buffers`), which grow with `OFFSET`.

3. **No Parallelism**
   - Large `OFFSET` values prevent query optimization (e.g., index skips, parallel scans).

4. **Database Lock Contention**
   - Long-running queries block other operations (e.g., writes).

### **Real-World Example: Twitter’s Early Feeds**
Twitter’s early implementation used `OFFSET`, leading to:
- **Slow loading** when users scrolled to older posts.
- **Higher server costs** due to inefficient queries.
- **Poor UX** (feeds felt "stuck" after a few pages).

This is why **keyset pagination** became the standard for platforms like Instagram, Reddit, and Slack.

---

## **The Solution: Keyset Pagination**

### **How It Works**
Instead of jumping by row numbers (`OFFSET`), keyset pagination:
1. **Uses a column value (the "key")** to define the boundary.
2. **Fetches only the next logical set** of records.
3. **Scales linearly** (O(1) per page, not O(N)).

### **Example: Fetching a Feed by `created_at`**
1. **First request** (no cursor):
   ```sql
   SELECT * FROM posts ORDER BY created_at DESC LIMIT 10;
   ```
2. **Second request** (using the oldest post’s ID as a cursor):
   ```sql
   SELECT * FROM posts
   WHERE created_at < '2023-01-01 12:00:00'
   ORDER BY created_at DESC
   LIMIT 10;
   ```
3. **Third request** (using the oldest post’s `id` from the previous page):
   ```sql
   SELECT * FROM posts
   WHERE id < 123456789
   ORDER BY id DESC
   LIMIT 10;
   ```

### **Why This Is Better**
✅ **No `OFFSET` scanning** → Faster queries.
✅ **Uses indexes efficiently** → Lower I/O.
✅ **Works well with caching** (Redis, CDNs).
✅ **No row-count leaks** (unlike `OFFSET`).

---

## **Implementation Guide**

### **1. Choosing the Right Key Column**
A good keyset column should:
- Be **monotonically increasing/decreasing** (e.g., `id`, `timestamp`).
- **Not be a primary key** (if it is, you risk gaps due to deletions).

#### **Bad Choice: `id` (if auto-incremented with gaps)**
```sql
-- If you delete a post (id=5), the next page might skip it.
SELECT * FROM posts WHERE id > 5 ORDER BY id LIMIT 10;
```

#### **Good Choice: `id` (if sequential) or `created_at`**
```sql
-- Safer: Fetches only non-deleted posts.
SELECT * FROM posts WHERE created_at < '2023-01-01' ORDER BY created_at DESC LIMIT 10;
```

---

### **2. Database Implementations**

#### **SQL (PostgreSQL, MySQL)**
```sql
-- First page
SELECT * FROM posts ORDER BY created_at DESC LIMIT 10;

-- Next page (using the oldest post from the previous page)
SELECT * FROM posts
WHERE created_at < '2023-01-01'  -- cursor value
ORDER BY created_at DESC
LIMIT 10;
```

#### **Redis (Sorted Sets)**
If storing data in Redis, use `ZRANGEBYSCORE`:
```bash
# First page (last 10 posts)
ZRANGE post_rank 0 9 WITHSCORES

# Next page (after post with score=12345)
ZREVRANGEBYSCORE post_rank +inf 12345 LIMIT 0 10
```

#### **MongoDB**
```javascript
// First page
db.posts.find().sort({ created_at: -1 }).limit(10);

// Next page (using last seen timestamp)
db.posts.find({ created_at: { $lt: "2023-01-01" } })
       .sort({ created_at: -1 })
       .limit(10);
```

---

### **3. API Design (REST/GraphQL)**
#### **Example: JSON Response**
```json
{
  "data": [
    { "id": 1, "message": "First post" },
    { "id": 2, "message": "Second post" }
  ],
  "next_cursor": "2023-01-01T00:00:00Z"  // For the next page
}
```

#### **Implementation (Node.js + Express)**
```javascript
app.get("/feed", (req, res) => {
  const { cursor } = req.query;
  let query = "SELECT * FROM posts ORDER BY created_at DESC LIMIT 10";

  if (cursor) {
    query += ` WHERE created_at < '${cursor}'`;
  }

  db.query(query, (err, results) => {
    const nextCursor = results.length > 0
      ? results[results.length - 1].created_at
      : null;

    res.json({
      data: results,
      next_cursor: nextCursor
    });
  });
});
```

---

## **Common Mistakes to Avoid**

### **1. Using a Non-Indexed Column as the Key**
❌ **Bad:**
```sql
-- If `content` is not indexed, this is slow!
SELECT * FROM posts WHERE content LIKE '%query%' ORDER BY created_at DESC LIMIT 10;
```

✅ **Good:**
```sql
-- Always index the key!
CREATE INDEX idx_posts_created_at ON posts(created_at);
```

### **2. Not Handling Edge Cases (Deleted/Soft-Deleted Records)**
If users delete posts, your cursor might become invalid.

✅ **Solution: Use `NULL` as a safe boundary:**
```sql
-- If a post is deleted, fetch after it (if it exists).
SELECT * FROM posts
WHERE created_at < '2023-01-01' OR created_at IS NULL
ORDER BY created_at DESC
LIMIT 10;
```

### **3. Ignoring Race Conditions (Concurrent Writes)**
If multiple users fetch pages simultaneously, cursors might overlap.

✅ **Solution:**
- Use **optimistic locking** (e.g., `created_at` + `updated_at`).
- In Redis, use **atomic operations** (`INCR` for counters).

```sql
-- Example: Fetch while ensuring no gaps
SELECT * FROM posts
WHERE (id, version) > (last_seen_id, 0)
ORDER BY id
LIMIT 10;
```

### **4. Forgetting to Cache Frequently Accessed Pages**
Keyset pagination works well with **Redis**, but avoid hitting the DB every time.

✅ **Caching Strategy:**
```python
# Pseudocode for caching
cache_key = f"feed:{cursor}"
if cache_key in redis:
    return cached_data
else:
    data = fetch_from_db(cursor)
    redis.setex(cache_key, 3600, json.dumps(data))  # Cache for 1 hour
    return data
```

---

## **Key Takeaways**
✔ **Keyset pagination is faster** than `LIMIT-OFFSET` (avoids scanning rows).
✔ **Works well with indexes** (choose a monotonically changing column).
✔ **Handles large datasets efficiently** (O(1) per page).
✔ **Requires careful API design** (proper cursor handling).
✔ **Combine with caching** (Redis, CDNs) for even better performance.
✔ **Avoid gaps** (use `NULL` or versioning if deletions occur).

---

## **Conclusion**

Keyset pagination is **the right way** to handle infinite scroll, search results, and large datasets. Unlike `OFFSET`, it scales predictably, avoids database bloat, and keeps users happy with fast load times.

### **When to Use It?**
✅ Timelines (Twitter, Instagram)
✅ Search results (Google, GitHub)
✅ Product listings (e-commerce)
✅ Logs (ELK stack)

### **When to Avoid It?**
❌ Small datasets (where `OFFSET` is fine).
❌ If the key column changes frequently (e.g., `random_hash`).

### **Final Thought**
Keyset pagination is **not just a trick**—it’s a **performance best practice**. If you’re building a high-scale app, **implement it today**.

---
**Want to try it?**
1. Pick a dataset (e.g., a table with `id` and `created_at`).
2. Write a `LIMIT-OFFSET` query—then rewrite it using keyset pagination.
3. Compare execution times!

Happy coding! 🚀
```

---
**P.S.** If you’re using **GraphQL**, consider [`relay-cursor`](https://relay.dev/graphql/cursor-based-pagination.html) for a standardized approach. Would love to hear how you implement it in your stacks! 👇