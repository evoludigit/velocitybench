```markdown
# **Keyset Pagination: A Scalable Way to Fetch Data Efficiently**

Pagination is a fundamental technique for handling large datasets in web applications. Without it, your users would be overwhelmed by endless scrolls of data, and your database would struggle under the weight of too many requests. Traditional pagination—like `LIMIT` and `OFFSET`—is simple, but it has critical flaws at scale.

In this tutorial, we’ll explore the **keyset pagination** (also called cursor-based pagination) pattern—a performant, scalable alternative to `LIMIT-OFFSET` that avoids performance pitfalls while delivering smooth user experiences. You’ll learn how it works, when to use it, and how to implement it in real-world applications.

---

## **Introduction**

Imagine running an app with millions of records—say, a social media platform with billions of posts. If you fetch all posts at once, the server crashes, the user’s browser freezes, and the experience collapses.

Traditional pagination with `LIMIT` and `OFFSET` (e.g., `SELECT * FROM posts LIMIT 10 OFFSET 100`) seems like a good solution. However, as the dataset grows, `OFFSET` becomes inefficient because the database must scan through every row up to the offset before returning results. This leads to slow queries and poor scalability.

Keyset pagination solves this problem by leveraging sorted columns (like `id`, `timestamp`, or `created_at`) to fetch only the rows needed for the next page. Instead of counting rows to skip, it fetches data in ranges based on a unique "key" value. This approach is **O(log n)** at worst and often **O(1)** for modern databases, making it far more efficient.

---

## **The Problem: Why Traditional Pagination Fails at Scale**

Let’s examine why `LIMIT-OFFSET` pagination becomes problematic.

### **Performance Degradation with Large Datasets**

Consider a table with `10 million` records. To fetch **page 2**, your query might look like this:

```sql
-- Traditional pagination for page 2
SELECT * FROM posts
ORDER BY id
LIMIT 10 OFFSET 20;
```

The database must:
1. Count all rows from offset `0` to `19`.
2. Skip those rows.
3. Return rows `20` to `29`.

This is inefficient, especially if `OFFSET` is large (e.g., `OFFSET 1_000_000`). The query runs slower and slower as the dataset grows.

### **Inconsistent Performance**

Keyset pagination avoids this by using a **range-based filter** instead of a fixed offset. For example, if the previous page’s last post had `id = 50`, the next page only needs:

```sql
-- Keyset pagination for next page
SELECT * FROM posts
WHERE id > 50
ORDER BY id
LIMIT 10;
```

This query is **blazing fast** because the database can leverage an index on `id` to jump directly to the correct range.

### **Edge Cases and Race Conditions**

Traditional pagination also introduces subtle issues:
- **Race conditions**: If two users refresh quickly, they might fetch the same batch of data.
- **No resuming after refresh**: If a user leaves and returns, they need to start from the beginning again.

Keyset pagination mitigates these issues by allowing users to **resume from their last position** using the returned key.

---

## **The Solution: Keyset Pagination Explained**

Keyset pagination works like this:

1. **First request**: Fetch the first batch of data (e.g., first 10 posts).
2. **Subsequent requests**: The client sends the **last key** (e.g., last `id`) from the previous page.
3. **Server follows up**: It queries for records **greater than** (or **after**) that key.
4. **Repeat**: The cycle continues, with each request fetching only the next batch.

### **Key Advantages**
✅ **Efficient**: Uses indexes for fast range queries.
✅ **Scalable**: Performance remains constant regardless of dataset size.
✅ **Race-condition safe**: Each fetch depends on the last key, preventing duplicates.
✅ **Resume-friendly**: Users can return to their last position.

---

## **Implementation Guide**

Let’s implement keyset pagination in **SQL**, **Node.js (Express)**, and **React**.

---

### **1. Database Schema**
We’ll use a `posts` table with `id` and `created_at`:

```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (created_at)  -- Optional but helpful for time-based pagination
);
```

---

### **2. SQL Query for Keyset Pagination**

#### **First Page (No Key)**
```sql
-- Fetch the first 10 posts
SELECT * FROM posts
ORDER BY id ASC
LIMIT 10;
```
**Response**:
```json
[
    { "id": 1, "title": "Post 1", "created_at": "2023-01-01" },
    { "id": 2, "title": "Post 2", "created_at": "2023-01-02" },
    // ... 10 posts
]
```
The client should **store the last `id`** (e.g., `10`) for the next request.

---

#### **Subsequent Pages (With Key)**
```sql
-- Fetch next 10 posts after id = 10
SELECT * FROM posts
WHERE id > 10
ORDER BY id ASC
LIMIT 10;
```
**Response**:
```json
[
    { "id": 11, "title": "Post 11", "created_at": "2023-01-11" },
    // ... next 10 posts
]
```
The client now stores `id = 20` for the next request.

---

### **3. Backend Implementation (Node.js + Express)**

#### **API Endpoint**
```javascript
const express = require('express');
const app = express();
app.use(express.json());

// Mock database (replace with real DB in production)
const posts = [
    { id: 1, title: "Post 1", created_at: new Date("2023-01-01") },
    { id: 2, title: "Post 2", created_at: new Date("2023-01-02") },
    // ... 100+ posts
];

app.get('/posts', (req, res) => {
    const { lastId } = req.query;  // e.g., ?lastId=10
    let query = { id: null };

    if (lastId) {
        query.id = { $gt: parseInt(lastId) };  // Greater than lastId
    }

    const page = posts
        .filter(post => (lastId ? post.id > lastId : true))
        .sort((a, b) => a.id - b.id)
        .slice(0, 10);

    const nextKey = page.length > 0 ? page[page.length - 1].id : null;

    res.json({
        data: page,
        nextKey: nextKey  // Pass this to the client for the next request
    });
});

app.listen(3000, () => console.log('Server running on port 3000'));
```

#### **Key Takeaways in Code**
- The client sends the `lastId`.
- The server filters records **greater than** `lastId`.
- The **next key** (last `id` of the current page) is returned for the next request.

---

### **4. Frontend Implementation (React)**

```jsx
import React, { useState, useEffect } from 'react';

function PostsList() {
    const [posts, setPosts] = useState([]);
    const [nextKey, setNextKey] = useState(null);
    const [loading, setLoading] = useState(false);

    const fetchPosts = async (key) => {
        setLoading(true);
        const res = await fetch(`http://localhost:3000/posts?lastId=${key}`);
        const data = await res.json();
        setPosts(prev => [...prev, ...data.data]);
        setNextKey(data.nextKey);
        setLoading(false);
    };

    useEffect(() => {
        fetchPosts(null);  // Initial load
    }, []);

    return (
        <div>
            <ul>
                {posts.map(post => (
                    <li key={post.id}>
                        <h3>{post.title}</h3>
                        <p>{post.created_at.toDateString()}</p>
                    </li>
                ))}
            </ul>
            {nextKey && !loading && (
                <button onClick={() => fetchPosts(nextKey)}>Load More</button>
            )}
            {loading && <p>Loading...</p>}
        </div>
    );
}

export default PostsList;
```

#### **Key Takeaways in React**
- The client stores `nextKey` and uses it for the next request.
- New posts are appended to the existing list.
- Loading state prevents duplicate clicks.

---

## **Common Mistakes to Avoid**

1. **Not Using an Index**
   - If `WHERE id > X` lacks an index, the query will scan the entire table.
   - **Fix**: Ensure the key column (`id`, `created_at`) is indexed.

2. **Using `OFFSET` in Keyset Queries**
   - Mixing `OFFSET` with keyset pagination defeats the purpose.
   - **Fix**: Always use range-based filtering (`>`, `<`).

3. **Not Handling Edge Cases**
   - If all records are fetched, `nextKey` should be `null`.
   - **Fix**: Check if `nextKey` exists before making the next request.

4. **Assuming Keys Are Monotonically Increasing**
   - If keys can be deleted or reordered (e.g., `updated_at`), keyset pagination may fail.
   - **Fix**: Use a **versioned key** (e.g., `version_id`) if data can change.

5. **Exposing Internal Keys**
   - Don’t let clients manipulate keys directly (e.g., `?lastId=999999`).
   - **Fix**: Validate and sanitize keys on the server.

---

## **Key Takeaways**

✔ **Keyset pagination is more efficient than `LIMIT-OFFSET`** because it avoids full table scans.
✔ **Use a sorted column** (e.g., `id`, `created_at`) as the key for fast range queries.
✔ **Return a `nextKey`** to allow the client to fetch the next batch.
✔ **Index your key column** to ensure optimal performance.
✔ **Handle edge cases** (empty results, null keys) gracefully.
✔ **Avoid race conditions** by letting the server determine the next batch.

---

## **Conclusion**

Keyset pagination is a powerful pattern for fetching large datasets efficiently. It outperforms traditional pagination at scale, avoids race conditions, and provides a seamless user experience.

### **When to Use It**
- Fetching **sorted lists** (e.g., posts, comments, timelines).
- **Long scroll views** (e.g., social media feeds).
- **Any case where `OFFSET` would be inefficient**.

### **When Not to Use It**
- If your data is **unsorted** and lacks a natural key (e.g., random `uuid`s).
- For **random access** (e.g., "Show me page 100 immediately").
- If your dataset is **small enough** that `LIMIT-OFFSET` works fine.

### **Final Tip**
Start with a simple implementation, then optimize. Use tools like `EXPLAIN ANALYZE` (PostgreSQL) to verify your queries are using indexes efficiently.

Give keyset pagination a try—your users (and your database) will thank you!

---
**Happy coding!** 🚀
```

This blog post is **practical**, **code-first**, and **honest about tradeoffs** while keeping it beginner-friendly.