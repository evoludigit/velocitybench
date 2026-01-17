# **[Pattern] Keyset Pagination: Reference Guide**

---

## **Overview**
Keyset pagination is a database query optimization technique that fetches data in chunks while minimizing performance degradation caused by large offset-based queries (e.g., `LIMIT 10, 100` and `OFFSET 100`). Instead of relying on row numbers (e.g., offsets), it uses column values (e.g., IDs, timestamps) to define the "keys" for subsequent requests. This approach avoids expensive `OFFSET` calculations and scales efficiently even with massive datasets.

**Key Benefits:**
✔ **Performance:** Reduces database load by avoiding slow `OFFSET` scans.
✔ **Scalability:** Works well with distributed databases (e.g., Cassandra, MongoDB).
✔ **Flexibility:** Supports both ascending/descending order and reverse pagination.

---

## **Implementation Details**

### **Core Principles**
1. **Anchor-Based Fetching:** Each request starts from a "key" (e.g., a primary key or timestamp) to fetch the next batch.
2. **No Global Ordering:** The keyset ensures continuous pagination without needing a full table scan.
3. **Client-Side State:** The client tracks the last fetched key to make the next request.

### **When to Use**
- **Large datasets** (e.g., social media feeds, logs).
- **No native cursor-based support** (e.g., some NoSQL databases).
- **Avoiding `OFFSET`-based pagination** (e.g., Slack’s infinite scroll).

### **When to Avoid**
- Small datasets (overhead may outweigh benefits).
- Databases with poor indexing on the keyset column.

---

## **Schema Reference**

| **Column**          | **Purpose**                                                                 | **Example**                     | **Data Type**       |
|----------------------|----------------------------------------------------------------------------|---------------------------------|---------------------|
| `key_column`        | Defines the "anchor" for pagination (e.g., `id`, `timestamp`).             | `user_id`, `created_at`          | `INT`, `DATETIME`   |
| `direction`         | Specifies if pagination is ascending or descending.                       | `desc` (default for reverse)    | `ENUM` (`asc`, `desc`)|
| `order_by`          | Column to sort results (must be indexed).                                 | `id`, `timestamp`                | Same as `key_column`|
| `start_after`       | The last key fetched (for ascending) or before (for descending).          | `12345` (last `id`)              | Matches `key_column`|
| `limit`             | Number of records per request.                                             | `20`                             | `INT`               |

**Example Table:**
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    content TEXT,
    created_at TIMESTAMP,
    user_id INT REFERENCES users(id)
);

-- Add index for efficient range queries:
CREATE INDEX idx_posts_created_at ON posts(created_at);
```

---

## **Query Examples**

### **1. Ascending Keyset (Forward Pagination)**
Fetch the next batch of records where `id > start_after`:
```sql
-- First page (no start_after)
SELECT * FROM posts
ORDER BY id ASC
LIMIT 20;

-- Subsequent pages
SELECT * FROM posts
WHERE id > [last_fetched_id]
ORDER BY id ASC
LIMIT 20;
```

### **2. Descending Keyset (Reverse Pagination)**
Fetch the next batch of records where `id < start_after`:
```sql
-- First page (no start_after, but direction=desc)
SELECT * FROM posts
ORDER BY id DESC
LIMIT 20;

-- Subsequent pages
SELECT * FROM posts
WHERE id < [last_fetched_id]
ORDER BY id DESC
LIMIT 20;
```

### **3. Mixed Keyset (Composite Column)**
Use multiple columns to define keys:
```sql
-- Assume `created_at` and `user_id` define the order
SELECT * FROM posts
WHERE (user_id, created_at) >
    (SELECT user_id, created_at FROM posts ORDER BY user_id DESC, created_at DESC LIMIT 1)
ORDER BY user_id DESC, created_at DESC
LIMIT 20;
```

### **4. Edge Cases**
- **Empty Result:** If no records match `WHERE key_column > start_after`, return `null` or a "no more results" flag.
- **Dynamic `start_after`:** The client tracks the last fetched `key_column` (e.g., `last_id`) to pass in the next request.

---

## **Implementation Workflow**

1. **Client Request:**
   - Send `start_after`, `limit`, and `direction` (e.g., `?start_after=123&limit=20&direction=desc`).
2. **Server Query:**
   - Constructs a range query using the keyset (e.g., `WHERE id > 123`).
   - Returns paginated results + the `last_key` (e.g., `last_id=456`) for the next request.
3. **Client State Management:**
   - Stores `last_key` until the user requests the next page.

---
## **Performance Considerations**

| **Aspect**            | **Best Practice**                                                                 |
|-----------------------|----------------------------------------------------------------------------------|
| **Indexing**          | Ensure `key_column` is indexed (e.g., `CREATE INDEX idx_column ON table(column)`). |
| **Limit Size**        | Use `LIMIT` values between 10–100 for balance between latency and batch size.    |
| **Concurrency**       | Keyset pagination is thread-safe; no race conditions on the keyset column.         |
| **Database Choices**  | Works best with B-trees (e.g., PostgreSQL, MySQL). Avoid with unindexed columns. |

---

## **Query Optimization Tips**
1. **Composite Keys:** For better granularity, use `(column1, column2)` as the keyset.
   ```sql
   -- Example: Sort by user, then timestamp
   WHERE (user_id, created_at) > (last_user_id, last_timestamp)
   ```
2. **Avoid `OFFSET`:** Always use `WHERE column > last_key` instead of `OFFSET`.
3. **Denormalize for Performance:** If `key_column` is frequently used in pagination, consider adding it to the index.

---

## **Example API Endpoint**

```http
# Fetch next 20 posts after id=123 (ascending)
GET /api/posts?start_after=123&limit=20&direction=asc

# Response:
{
  "data": [post1, post2, ..., post20],
  "next_start_after": 456,  # Use this for the next request
  "has_more": true           # Indicates more results exist
}
```

---

## **Related Patterns**

| **Pattern**               | **Description**                                                                 | **Use Case**                          |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------|
| **Offset Pagination**     | Uses `LIMIT` + `OFFSET` (inefficient for large offsets).                       | Small datasets, legacy systems.       |
| **Cursor-Based Pagination** | Uses a unique cursor token (e.g., base64-encoded keyset).                   | Highly scalable apps (e.g., Twitter). |
| **Range Queries**         | Uses date/time ranges (e.g., `WHERE created_at > '2023-01-01'`).            | Time-series data.                     |
| **Infinite Scroll**       | Frontend handles pagination by appending results to a list.                    | Social media feeds.                  |

---

## **Comparison: Keyset vs. Offset Pagination**

| **Feature**              | **Keyset Pagination**                          | **Offset Pagination**                  |
|--------------------------|-----------------------------------------------|---------------------------------------|
| **Performance**          | O(1) for each batch (index seek).            | O(n) for large offsets (table scan).  |
| **Scalability**          | Scales to millions of records.               | Fails with >100K records.              |
| **Complexity**           | Requires client-side state management.        | Simpler (but risky for large data).   |
| **Reverse Pagination**   | Supported via `WHERE column < start_after`.   | Not efficient (requires full scan).   |

---

## **Troubleshooting**
1. **Slow Queries:**
   - Check if `key_column` is indexed.
   - Test with `EXPLAIN ANALYZE` to verify the query plan.
2. **Duplicate Keys:**
   - Ensure `key_column` is unique (or use a composite key).
3. **Gaps in Data:**
   - Keyset pagination may skip deleted/soft-deleted records. Use `WHERE ... AND active = true`.

---
## **Further Reading**
- [PostgreSQL Official Docs: Keyset Pagination](https://www.postgresql.org/docs/)
- [Slack’s Infinite Scroll Implementation](https://slack.engineering/infinite-scrolling-in-slack/)
- [MongoDB Cursor Pagination](https://docs.mongodb.com/manual/core/cursor-pagination/)

---
**Last Updated:** [Date]
**Version:** 1.2