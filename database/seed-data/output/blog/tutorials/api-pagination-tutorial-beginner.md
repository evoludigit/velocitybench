```markdown
# **Mastering API Pagination Patterns: A Beginner’s Guide**

*How to design efficient, scalable pagination for your APIs*

---

## **Introduction: Why Pagination Matters**

Imagine building an API for a social media platform. Your users want to see their friends’ posts—but what if there are *thousands* of posts? If you return everything at once, your API crashes under load. Users wait forever. Servers burn out. **This is the pagination problem.**

Pagination breaks large datasets into manageable chunks, making APIs faster, more scalable, and user-friendly. Without it, you’re handing a user a stack of paper with 100,000 records and saying, *"Enjoy!"*—while they panic and call support.

But not all pagination is created equal. There are **three main approaches**:
- **Offset-based pagination** (think: "Give me page 5")
- **Cursor-based pagination** (think: "Give me records after this token")
- **Keyset pagination** (think: "Give me records where ID > X")

Each has pros, cons, and real-world use cases. In this guide, we’ll cover:
✅ The problem pagination solves (and why you *need* it)
✅ How each method works with **SQL, Python (FastAPI), and Node.js (Express)**
✅ Tradeoffs to consider when choosing a pattern
✅ Common mistakes (and how to avoid them)

By the end, you’ll be able to design pagination that feels **fast, intuitive, and scalable**—no more API timeouts or user complaints.

---

## **The Problem: When APIs Break Under Pressure**

Let’s say you’re building an API for a blog platform. A user visits `/posts`, and your database has **500,000 posts**. If you return all records without pagination:

```json
// Bad! (Imagine this response is 50MB+)
{
  "posts": [
    { "id": 1, "title": "First Post", ... },
    { "id": 2, "title": "Second Post", ... },
    ...
    { "id": 500000, "title": "Last Post", ... }
  ]
}
```
### **The Consequences:**
1. **Slow Response Times**
   - Databases struggle to fetch millions of rows at once.
   - Network latency spikes (users wait minutes).
   - Example: A `SELECT * FROM posts` on a slow server might take **30+ seconds**.

2. **Memory Overload**
   - Servers crash with `OutOfMemoryError` if they try to load all data.
   - Example: A Python app with `LIMIT None` may exhaust RAM before returning results.

3. **Poor User Experience**
   - Users see a loading spinner forever, then get a giant payload they’ll **never scroll through**.
   - Mobile users on slow connections **abandon the app**.

4. **Database Bottlenecks**
   - Without pagination, databases perform **full table scans**, wasting resources.
   - Example: A `WHERE` clause with `ORDER BY` on a large table becomes **extremely slow**.

---
## **The Solution: Three Pagination Patterns**

Here’s where pagination comes in. Instead of returning all records, we break them into **smaller, digestible chunks**. Let’s explore each method with code examples.

---

### **1. Offset-Based Pagination (Page Numbers)**
**How it works:**
You tell the API: *"Start at offset X, return Y records."*
- `offset` = How many records to skip.
- `limit` = How many records to return.

**SQL Example:**
```sql
-- Fetch posts 20-40 (offset 20, limit 20)
SELECT * FROM posts
ORDER BY id
LIMIT 20 OFFSET 20;
```

**Pros:**
✔ Simple to understand (like "page 3").
✔ Works well for small datasets (<10,000 records).

**Cons:**
❌ **Slow for large offsets** (e.g., `OFFSET 100000` = full table scan first).
❌ No way to "go back" without recalculating from the start.

**Python (FastAPI) Example:**
```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/posts")
async def get_posts(
    page: int = Query(1, description="Page number (1-based)"),
    page_size: int = Query(10, description="Records per page")
):
    offset = (page - 1) * page_size
    posts = db.execute(
        "SELECT * FROM posts ORDER BY id LIMIT ? OFFSET ?",
        (page_size, offset)
    ).fetchall()
    return {"posts": posts, "page": page, "page_size": page_size}
```

**When to use:**
- Small datasets (<10K records).
- Simple APIs where users rarely jump far into results.

---

### **2. Cursor-Based Pagination (Opaque Tokens)**
**How it works:**
Instead of page numbers, you return a **token** (e.g., a timestamp or ID) to continue fetching.
- First request: No cursor.
- Subsequent requests: Use `cursor` to fetch "next" records.

**SQL Example:**
```sql
-- Initial request (no cursor)
SELECT * FROM posts ORDER BY id LIMIT 10;

-- Next request (after cursor)
SELECT * FROM posts
WHERE id > 5 ORDER BY id LIMIT 10;
```

**Pros:**
✔ **Fast for large datasets** (no full table scans).
✔ Supports reverse pagination (e.g., "previous" button).

**Cons:**
❌ Requires **consistent ordering** (e.g., `ORDER BY` must match cursor logic).
❌ Tokens can expire or become invalid if data changes.

**Python (FastAPI) Example:**
```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/posts")
async def get_posts(
    cursor: int = Query(None, description="Last post ID fetched"),
    page_size: int = Query(10)
):
    if cursor:
        posts = db.execute(
            "SELECT * FROM posts WHERE id > ? ORDER BY id LIMIT ?",
            (cursor, page_size)
        ).fetchall()
    else:
        posts = db.execute(
            "SELECT * FROM posts ORDER BY id LIMIT ?",
            (page_size,)
        ).fetchall()
    return {"posts": posts, "next_cursor": posts[-1]["id"] if posts else None}
```

**When to use:**
- Large datasets (>1M records).
- APIs where users frequently scroll (e.g., social media, feeds).

---

### **3. Keyset Pagination (Ordered Column Values)**
**How it works:**
Similar to cursor-based, but uses a **specific column** (e.g., `created_at`, `user_id`) instead of an opaque token.
- First request: No keyset.
- Next request: Fetch records where `column > keyset_value`.

**SQL Example:**
```sql
-- Initial request
SELECT * FROM posts ORDER BY created_at DESC LIMIT 10;

-- Next request
SELECT * FROM posts
WHERE created_at < '2023-01-01' ORDER BY created_at DESC LIMIT 10;
```

**Pros:**
✔ **Predictable and efficient** (no arbitrary tokens).
✔ Works well with **time-based or sorted data** (e.g., news feeds).

**Cons:**
❌ Requires **strict ordering** (e.g., `created_at` must be unique).
❌ Can’t easily "go backward" without a separate `WHERE created_at > ...` query.

**Python (FastAPI) Example:**
```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/posts")
async def get_posts(
    after: str = Query(None, description="Last post's created_at"),
    page_size: int = Query(10)
):
    query = "SELECT * FROM posts ORDER BY created_at DESC LIMIT ?"
    params = (page_size,)
    if after:
        query += " WHERE created_at < ?"
        params = (page_size, after)

    posts = db.execute(query, params).fetchall()
    next_after = posts[-1]["created_at"] if posts else None
    return {
        "posts": posts,
        "next_after": next_after,
        "has_more": next_after is not None
    }
```

**When to use:**
- Time-ordered data (e.g., tweets, news articles).
- When you need **deterministic pagination** (e.g., "show me posts after Jan 1, 2023").

---

## **Implementation Guide: Choosing the Right Pattern**

| **Pattern**          | **Best For**                          | **Worst For**                     | **Example Use Cases**               |
|----------------------|---------------------------------------|-----------------------------------|-------------------------------------|
| **Offset-Based**     | Small datasets (<10K records)          | Large datasets (>100K records)     | Admin dashboards, simple CRUD APIs  |
| **Cursor-Based**     | Large datasets, user scrolls frequently | Inconsistent ordering             | Social media feeds, infinite scroll |
| **Keyset**           | Time-ordered or sorted data           | Non-unique columns (e.g., `name`) | News apps, activity streams         |

### **Step-by-Step: Building a Paginated API (FastAPI)**
1. **Decide on pagination type** (e.g., cursor-based for scalability).
2. **Define query parameters** (`page`, `page_size`, `cursor`, etc.).
3. **Write the SQL query** with `LIMIT` and `OFFSET` (or `WHERE column > X`).
4. **Return metadata** (e.g., `next_cursor`, `total_count` for consistency).
5. **Test with large datasets** (e.g., 1M+ records).

**Example (FastAPI + SQLite):**
```python
from fastapi import FastAPI, Query
import sqlite3

app = FastAPI()
conn = sqlite3.connect("database.db")

@app.get("/posts")
async def get_posts(
    cursor: int = Query(None, description="Last post ID"),
    limit: int = Query(10, description="Records per page")
):
    query = "SELECT * FROM posts ORDER BY id LIMIT ?"
    params = (limit,)
    if cursor:
        query += " WHERE id > ?"
        params = (limit, cursor)

    cursor.execute(query, params)
    posts = cursor.fetchall()

    next_cursor = posts[-1]["id"] if posts else None
    return {
        "posts": posts,
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None
    }
```

---

## **Common Mistakes to Avoid**

1. **Not Including Metadata**
   - ❌ Only return paginated data (users have no idea if they reached the end).
   - ✅ Return `next_cursor`, `total_count`, or `has_more`.

2. **Ignoring Performance for Large Datasets**
   - ❌ Using `OFFSET` with big numbers (e.g., `OFFSET 100000`).
   - ✅ Use **cursor-based or keyset** for >10K records.

3. **Inconsistent Sorting**
   - ❌ Changing `ORDER BY` between requests breaks cursor logic.
   - ✅ Stick to one consistent sort (e.g., always `ORDER BY id`).

4. **No Error Handling for Invalid Cursors**
   - ❌ Silently failing if `cursor` is invalid.
   - ✅ Return `400 Bad Request` if cursor doesn’t exist.

5. **Overcomplicating for Small APIs**
   - ❌ Using GraphQL cursors for a simple REST API.
   - ✅ Start simple (`page` + `limit`), then optimize later.

---

## **Key Takeaways**

✔ **Pagination solves:**
   - Slow API responses.
   - Database overload.
   - Poor user experience.

✔ **Three main patterns:**
   - **Offset-based** (simple, but slow for large offsets).
   - **Cursor-based** (fast, but needs consistent ordering).
   - **Keyset** (best for time-ordered data).

✔ **Best practices:**
   - Always return **metadata** (`next_cursor`, `total_count`).
   - For **>10K records**, prefer **cursor-based or keyset**.
   - **Test with large datasets** before production.

✔ **When to avoid pagination:**
   - Small datasets (<1K records).
   - Admin tools where users need "all data" occasionally.

---

## **Conclusion: Build APIs That Scale**

Pagination isn’t just a "nice-to-have"—it’s a **necessity** for any real-world API. Without it, your users will abandon your app, your servers will crash, and your database will cry.

**Which pattern should you choose?**
- **Startups with small data?** Offset-based (simple).
- **Social media apps?** Cursor-based (scalable).
- **News feeds?** Keyset (time-ordered).

Remember: **No pattern is perfect.** Offset-based is simple but slow for big data. Cursor-based is fast but needs careful ordering. Keyset is deterministic but tricky with edge cases.

**Next steps:**
1. Try implementing **cursor-based pagination** in your next project.
2. Benchmark different patterns with **100K+ records**.
3. Read [GraphQL’s Relay Connection spec](https://relay.dev/graphql/connections.htm) if you use GraphQL.

Now go build **fast, scalable APIs**—your users (and database) will thank you.

---
**Further Reading:**
- [PostgreSQL OFFSET vs. Cursor Pagination](https://use-the-index-luke.com/no-offset)
- [FastAPI Pagination Docs](https://fastapi.tiangolo.com/tutorial/sql-databases/#pagination)
- [Twitter’s Pagination Guide](https://dev.twitter.com/web/building/timelines/pagination)

---
**What’s your favorite pagination pattern?** Let me know in the comments!
```