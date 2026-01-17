```markdown
# **Keyset Pagination: The High-Performance Way to Fetch Large Datasets**

*Efficiently load infinite scroll data without the pain of offset-based pagination*

---

## **Introduction**

When building applications that display large datasets—like social media feeds, product listings, or logs—you need a way to fetch data in manageable chunks without overwhelming your database or users. Traditional pagination with `LIMIT` and `OFFSET` is tempting, but it’s slow, inefficient, and scales poorly under heavy load.

**Keyset pagination** (also called cursor-based pagination) solves these problems by letting users navigate through data using unique identifiers (keys) from previous responses. This approach avoids the pitfalls of offset-based pagination while maintaining simplicity. It’s the secret weapon behind high-performance APIs like GitHub’s issue lists, Twitter’s tweets, and Instagram’s infinite scroll.

In this guide, we’ll:
- Explore why offset pagination fails when datasets grow.
- Dive into how keyset pagination works under the hood.
- Walk through practical code examples for SQL, NoSQL, and API design.
- Discuss tradeoffs and best practices to implement this pattern effectively.

Let’s get started.

---

## **The Problem: Why Offset Pagination Fails**

Offset pagination (e.g., `LIMIT 10 OFFSET 20`) is simple but has critical flaws:

1. **Poor Performance at Scale**
   Databases must scan all records from the start to find the offset. For large tables, this becomes a bottleneck:
   ```sql
   SELECT * FROM posts
   ORDER BY created_at DESC
   LIMIT 10 OFFSET 20;
   ```
   This query may read **millions of rows** even if only 10 are needed. As the offset grows, performance degrades linearly.

2. **Race Conditions**
   If two users fetch data simultaneously and modify the dataset, their offset-based requests may return inconsistent results.

3. **No Natural Keys for Navigation**
   Offset values (`OFFSET 10`) don’t represent meaningful data points. If you delete or insert records, offsets break completely, forcing a reset.

4. **App Server Burden**
   The API must handle large `OFFSET` requests, which can max out server resources during peak loads.

### **A Real-World Example**
Imagine a forum with 1M posts. A user requests page 10 (`OFFSET 90`):
- The database scans the first 90 records to find the 10th page.
- If the forum grows to 2M posts, the same request now requires **scanning 1.9M rows**—a 20x slowdown!
- Adding new posts or deleting old ones means `OFFSET` values suddenly refer to the wrong posts.

Keyset pagination solves all of these issues.

---

## **The Solution: Keyset Pagination**

Keyset pagination replaces offsets with **sortable, unique keys** from previous results. Here’s how it works:

1. **Fetch the First Page**
   Retrieve the first set of records (e.g., the 10 most recent posts).
   No offset is needed—just sort by a natural key (e.g., `created_at`).

2. **Use the Last Key as the Cursor**
   The last record’s key (e.g., `post_id`) becomes the starting point for the next page.
   Subsequent requests include this cursor to fetch the next batch of records that come **after** it.

3. **Handle Edge Cases**
   - If the cursor is invalid (e.g., deleted or out of order), return an empty list or an error.
   - Allow resetting to the first page (e.g., via `cursor=null`).

### **Why Keyset Pagination Works**
- **No Scanning**: Only records *after* the cursor are fetched, reducing I/O.
- **Deterministic**: Keys are unique and immutable (assuming they don’t change).
- **Resilient to Data Changes**: Deletions or inserts don’t invalidate pagination keys.

---

## **Implementation Guide**

### **1. Choosing the Right Key**
The cursor key must be:
✅ **Unique** – No duplicates.
✅ **Sortable** – Must align with your `ORDER BY` clause.
✅ **Stable** – Shouldn’t change over time (e.g., `post_id` is better than `created_at` in some cases).

**Good Choices**:
- Primary keys (`id`, `post_id`)
- Auto-incrementing columns
- Timestamps (if no other keys exist)

**Bad Choices**:
- Hashes of data (unless you control the hashing)
- Non-unique columns (e.g., `username`)

---

### **2. Database-Level Implementation**

#### **Example 1: SQL (PostgreSQL/MySQL)**
```sql
-- First page: No cursor
SELECT * FROM posts
WHERE deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 10;

-- Subsequent pages: Fetch posts after the cursor's id
SELECT * FROM posts
WHERE id < 123456  -- "after" cursor (assuming DESC order)
AND deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 10;
```

**Optimization**: Use an index on the cursor column:
```sql
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
```

#### **Example 2: NoSQL (MongoDB)**
```javascript
// First page
db.posts.find()
  .sort({ created_at: -1 })
  .limit(10);

// Subsequent page (cursor is the last post's _id)
db.posts.find({ _id: { $lt: ObjectId("5f8d2e0f...") } })
  .sort({ created_at: -1 })
  .limit(10);
```

---

### **3. API Design: Request/Response Format**
**Request**:
- Optional `cursor`: The last key from the previous page (e.g., `cursor=123`).
- `limit`: Number of items to fetch (e.g., `limit=10`).

**Response**:
```json
{
  "data": [
    { "id": 123, "title": "First Post" },
    { "id": 122, "title": "Second Post" }
  ],
  "cursor": 122,  // Last item's ID (for next page)
  "has_more": true // Indicates if more pages exist
}
```

**Example Endpoint**:
```bash
GET /posts?limit=10&cursor=122
```

---

### **4. Handling Edge Cases**
| Case                | Solution                                                                 |
|---------------------|--------------------------------------------------------------------------|
| Invalid/Deleted Key | Return empty data or error (e.g., `cursor=999999` doesn’t exist).          |
| No Previous Cursor  | Serve the first page (e.g., `cursor=null`).                               |
| Empty Result Set    | Return `has_more: false` to signal the end.                               |
| Concurrent Changes  | Use transactions if cursor keys are mutable (unlikely with IDs).          |

---

## **Code Examples**

### **Example 1: SQL (Python with SQLAlchemy)**
```python
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://user:pass@localhost/db")
Session = sessionmaker(bind=engine)

def get_posts(session, cursor=None, limit=10):
    query = session.query(Post).filter(Post.deleted_at == None)
    if cursor:
        query = query.filter(Post.id < cursor)  # Assuming DESC order
    query = query.order_by(desc(Post.created_at)).limit(limit)
    posts = query.all()
    next_cursor = posts[-1].id if posts else None
    return {
        "data": posts,
        "cursor": next_cursor,
        "has_more": bool(next_cursor)
    }
```

### **Example 2: FastAPI Implementation**
```python
from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI()

@app.get("/posts")
async def read_posts(
    cursor: Optional[int] = None,
    limit: int = Query(10, ge=1, le=100)
):
    # Fetch posts from DB using cursor logic
    posts = db_query(cursor, limit)
    next_cursor = posts[-1].id if posts else None
    return {
        "data": posts,
        "cursor": next_cursor,
        "has_more": next_cursor is not None
    }
```

### **Example 3: Redis (For Caching)**
```python
# Using Redis to cache paginated results
def get_posts_from_cache(cursor):
    key = f"posts:cursor:{cursor}"
    cached = redis.get(key)
    if cached:
        return json.loads(cached)

    posts = db_query(cursor)
    redis.setex(key, 3600, json.dumps(posts))  # Cache for 1 hour
    return posts
```

---

## **Common Mistakes to Avoid**

1. **Using Non-Unique Keys**
   - ❌ `cursor=email` (emails can collide).
   - ✅ `cursor=post_id` (always unique).

2. **Forgetting to Handle `cursor=null`**
   Always validate if `cursor` is `None` and serve the first page.

3. **Ignoring `has_more` Logic**
   Not indicating whether more pages exist leads to poor UX (e.g., infinite loading spinners).

4. **Not Indexing the Cursor Column**
   Without an index, queries become slow as the dataset grows.

5. **Assuming Keys Are Immutable**
   If you use timestamps as keys, a server time-sync issue could cause race conditions.

6. **Overcomplicating the Cursor Format**
   Start simple (e.g., `cursor=123`). Complex formats (e.g., `cursor=eyJkIjo...`) add unnecessary overhead.

---

## **Key Takeaways**

✅ **Performance**:
- Keyset pagination avoids scanning unnecessary rows, making it **O(log n)** in many cases vs. **O(n)** for offset pagination.

✅ **Scalability**:
- Works efficiently even with millions of records because it fetches only relevant data.

✅ **Resilience**:
- Deletions/inserts don’t break pagination unless the cursor key itself is modified.

✅ **Simplicity**:
- No complex math (like offsets) or race conditions.

⚠️ **Tradeoffs**:
- Requires a sortable, unique key (often your primary key).
- Not ideal for random access (e.g., "give me pages 10–20").

---

## **Conclusion**

Keyset pagination is the **most performant and scalable** way to fetch large datasets without overwhelming your database. It’s the default choice for high-traffic APIs like GitHub, Twitter, and Instagram, and it’s easy to implement once you understand the core idea: **use a stable key to fetch the next batch of data**.

### **When to Use It**
- Infinite scroll lists (e.g., timelines, feeds).
- Logs or audit trails.
- Any API with long lists of items.

### **When to Avoid It**
- Small datasets (offset pagination is simpler).
- Cases where you need random access (e.g., "show me page 5").

### **Next Steps**
1. Try implementing keyset pagination in your next project.
2. Compare its performance against offset pagination in your database.
3. Explore hybrid approaches (e.g., combining keyset pagination with caching).

By mastering keyset pagination, you’ll build APIs that **load faster, scale smoother, and provide a better user experience**—no matter how large your dataset grows.

---

**Happy coding!**
[Your Name/Blog Name]
```

---
**Word Count**: ~1,800
**Tone**: Practical, code-first, and solution-oriented with clear warnings about tradeoffs.
**Audience**: Intermediate backend engineers ready to optimize their APIs.