```markdown
---
title: "API Pagination Patterns: Choosing the Right Approach for Large Datasets"
author: "Jane Doe"
date: "2023-11-15"
tags: ["backend", "database", "API design", "pagination", "performance"]
featuredImage: "/images/api-pagination-patterns/featured-image.jpg"
description: "Master the art of API pagination with offset, cursor, and keyset patterns. Learn tradeoffs, real-world examples, and how to handle pagination in GraphQL."
---

# API Pagination Patterns: Choosing the Right Approach for Large Datasets

Imagine you’re building an API for a social media platform with millions of posts.
If you return all posts in a single response—20 million records at once—the client will
crash, the server will explode, and your users will abandon you in frustration.
Pagination is your savior: it breaks data into smaller, manageable chunks. But not all
pagination is created equal. Should you use offset-based, cursor-based, or keyset pagination?
Let’s dive into the patterns, tradeoffs, and code examples to help you choose wisely.

---

## The Problem: Why Pagination is Non-Negotiable

APIs often need to fetch large datasets, such as user posts, product listings, or transaction history.
Returning everything at once is a disaster:

- **Memory overload**: Servers can’t hold millions of records in RAM or even disk space efficiently.
- **Slow responses**: Clients wait minutes for a 50MB JSON payload they’ll never fully parse.
- **Network bottlenecks**: Large payloads consume bandwidth, increasing costs and latency.
- **Database strain**: Scans over millions of rows slow down queries, risking timeouts or crashes.

Even with filtering, sorting, or limited fields, unchecked pagination can break your app.
Without it, you lose performance, scalability, and user satisfaction.

---

## The Solution: Three Pagination Patterns

There are three primary pagination approaches, each with unique strengths and weaknesses.
We’ll explore them one by one with code examples.

### 1. Offset-Based Pagination (Basic but Fragile)

#### How it works:
Fetch a fixed number of records starting from an `offset` (e.g., "skip the first 10 items").
Example: `GET /posts?page=2&limit=10` translates to `OFFSET 10 LIMIT 10`.

#### SQL Example:
```sql
-- Page 2, 10 items per page
SELECT * FROM posts
ORDER BY created_at DESC
OFFSET 10 LIMIT 10;
```

#### Pros:
- Simple to implement.
- Works with most SQL dialects.

#### Cons:
- **Performance nightmare**: `OFFSET` scans rows sequentially, which becomes slow for large offsets.
  Example: `OFFSET 999999` on a 10M-row table scans 999,999 rows before finding results.
- **Hard to preload**: If you need two pages at once, you may query the same data twice.
- **Unpredictable**: Changing `limit` invalidates precomputed offsets.

#### When to use:
Only for small datasets or one-off queries. Avoid for production APIs with frequent pagination.

---

### 2. Cursor-Based Pagination (Flexible and Efficient)

#### How it works:
Instead of an offset, return an opaque token (cursor) representing a specific row. The next request uses this token to fetch the next "page".
Example: `GET /posts?cursor=abc123`

#### SQL Example (PostgreSQL):
```sql
-- Get first page (no cursor)
SELECT * FROM posts
ORDER BY created_at DESC
LIMIT 10;

-- Get next page (using cursor)
SELECT * FROM posts
WHERE created_at < '2023-10-01 12:00:00'  -- Value from last row's 'created_at'
ORDER BY created_at DESC
LIMIT 10;
```

#### Implementation (Node.js + PostgreSQL):
```javascript
// Fetch first page
const firstPage = await pool.query(
  'SELECT * FROM posts ORDER BY created_at DESC LIMIT 10'
);

// Get cursor for next page (last 'created_at' value)
const nextCursor = firstPage.rows[firstPage.rows.length - 1].created_at;

// Fetch next page
const nextPage = await pool.query(
  `SELECT * FROM posts WHERE created_at < $1 ORDER BY created_at DESC LIMIT 10`,
  [nextCursor]
);
```

#### Pros:
- **Efficient**: Skips rows directly to the next page, no scanning.
- **Predictable**: Changing `limit` doesn’t break cursors.
- **Reverse pagination**: Append `"before"`/`"after"` cursors for infinite scroll.

#### Cons:
- **Requires unique, ordered columns**: Works best with timestamps or IDs.
- **Cursor storage**: Clients must preserve cursors (e.g., in localStorage).

#### When to use:
For APIs with high traffic, large datasets, or frequent pagination (e.g., feeds, timelines).

---

### 3. Keyset Pagination (Keyset = Cursor for IDs)

#### How it works:
Like cursor-based, but uses a specific column (e.g., `post_id`) instead of a timestamp.
Fetches all items with IDs *greater than* (for "next") or *less than* (for "previous") a given key.

#### SQL Example:
```sql
-- Get next page (ids > last_id)
SELECT * FROM posts
WHERE id > 1234
ORDER BY id ASC
LIMIT 10;

-- Get previous page (ids < first_id)
SELECT * FROM posts
WHERE id < 1234
ORDER BY id DESC
LIMIT 10;
```

#### Implementation (Node.js):
```javascript
// Fetch first page (no cursor)
const firstPage = await pool.query(
  'SELECT * FROM posts ORDER BY id ASC LIMIT 10'
);

// Get cursor for next page (last 'id')
const nextCursor = firstPage.rows[firstPage.rows.length - 1].id;

// Fetch next page
const nextPage = await pool.query(
  'SELECT * FROM posts WHERE id > $1 ORDER BY id ASC LIMIT 10',
  [nextCursor]
);
```

#### Pros:
- **Idempotent**: Uses integers, which are always unique and ordered.
- **Scalable**: Works even if `created_at` is updated (unlike timestamps).
- **Efficient**: Direct key lookups avoid scanning.

#### Cons:
- **No reverse pagination**: "Previous" requires a separate query with `<`.
- **Identity dependency**: Requires a monotonically increasing ID (e.g., auto-increment).

#### When to use:
When you need deterministic, scalable pagination (e.g., product catalogs, code repositories).

---

## Implementation Guide: Choosing the Right Pattern

| Scenario                     | Recommended Pattern       | Why                          |
|-------------------------------|---------------------------|-------------------------------|
| Small dataset (<10k items)    | Offset-based              | Simplicity outweighs costs.   |
| Large, frequently accessed    | Cursor-based              | Efficient and flexible.      |
| Static, ordered data         | Keyset pagination         | Predictable and scalable.     |
| GraphQL API                  | Cursor-based (Relay spec) | Built-in support.            |

### Step-by-Step: Cursor-Based Pagination in PostgreSQL

1. **Create a table with an ordered column**:
   ```sql
   CREATE TABLE posts (id SERIAL PRIMARY KEY, created_at TIMESTAMP);
   ```

2. **Fetch first page**:
   ```javascript
   const firstPage = await pool.query(
     'SELECT * FROM posts ORDER BY created_at DESC LIMIT 10'
   );
   ```

3. **Generate cursor**:
   ```javascript
   const lastCreatedAt = firstPage.rows[firstPage.rows.length - 1].created_at;
   const cursor = lastCreatedAt.toISOString(); // or encode as Base64
   ```

4. **Fetch next page**:
   ```javascript
   const nextPage = await pool.query(
     `SELECT * FROM posts WHERE created_at < $1 ORDER BY created_at DESC LIMIT 10`,
     [cursor]
   );
   ```

### Step-by-Step: Keyset Pagination in PostgreSQL

1. **Use auto-increment IDs**:
   ```sql
   CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR);
   ```

2. **Fetch first page**:
   ```javascript
   const firstPage = await pool.query('SELECT id, name FROM products ORDER BY id ASC LIMIT 10');
   ```

3. **Generate cursor**:
   ```javascript
   const lastId = firstPage.rows[firstPage.rows.length - 1].id;
   const cursor = lastId.toString(); // or encode as Base64
   ```

4. **Fetch next page**:
   ```javascript
   const nextPage = await pool.query(
     'SELECT id, name FROM products WHERE id > $1 ORDER BY id ASC LIMIT 10',
     [cursor]
   );
   ```

---

## Common Mistakes to Avoid

1. **Ignoring Edge Cases**:
   - Empty results: Return `{ items: [], cursor: null }` instead of breaking the API.
   - Too many cursors: Limit depth (e.g., 100 pages) to prevent abuse.

2. **Assuming `OFFSET` is Safe**:
   - A `LIMIT 100` with `OFFSET 10000` is 10x slower than cursor-based pagination.

3. **Hardcoding Ordering**:
   - Always allow clients to specify `order_by` (e.g., `?order=desc`).

4. **Not Validating Cursors**:
   - Sanitize cursors to prevent SQL injection (e.g., use parameterized queries).

5. **Overcomplicating GraphQL**:
   - Use the [Relay Cursor Connections](https://relay.dev/graphql/connections.htm) spec for consistent pagination.

---

## Key Takeaways

- **Offset-based**: Simple but inefficient for large datasets. Avoid in production.
- **Cursor-based**: Best for dynamic, ordered data (e.g., timelines). Use timestamps or IDs.
- **Keyset pagination**: Ideal for static, ordered data (e.g., product listings). Uses IDs.
- **GraphQL**: Adopt the Relay spec for cursor-based pagination (e.g., `first`, `after`).
- **Edge cases matter**: Handle empty results, depth limits, and cursor validation.
- **Performance > Simplicity**: Optimize for real-world use, not just code ease.

---

## Conclusion: Design for Scale from Day One

Pagination isn’t just a performance trick—it’s a fundamental part of API design.
Your choice of pattern affects scalability, maintainability, and user experience.
For most high-traffic APIs, **cursor-based pagination** (or keyset) is the right call.
Use offset-based only for small, simple datasets, and always validate assumptions.

Start small, measure performance, and iterate. Your future self (and users) will thank you.

---
## Further Reading
- [Relay Cursor Connections](https://relay.dev/graphql/connections.htm) (GraphQL spec)
- [Database Performance: Pagination](https://use-the-index-luke.com/sql/where-clause/offset-limit)
- [PostgreSQL `LIMIT OFFSET` vs. Keyset](https://www.postgresql.org/message-id/flat/CAJmNfVLx%2BkKm5F26Qv1p78X6CfdZ9TgJqjW%3D8jXqXyh3F%2F1uXo5mD2w%40k)
```