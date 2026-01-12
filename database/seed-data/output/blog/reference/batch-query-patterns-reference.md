**[Pattern] Batch Query Patterns – Reference Guide**

---

### **Overview**
The **Batch Query Patterns** anti-pattern refers to techniques for efficiently executing multiple data retrieval operations in a single request, reducing latency, network overhead, and database load. Unlike traditional "query N times," batch operations consolidate requests into optimized calls, improving performance and scalability—critical for high-throughput applications (e.g., dashboards, analytics, or real-time systems). Common patterns include **batch fetching**, **paginated queries**, **joined subqueries**, and **parallel processing with limits**. This guide outlines key concepts, schema dependencies, implementation examples, and related patterns to avoid pitfalls like **N+1 queries** or **excessive memory usage**.

---

### **Key Concepts & Implementation Details**

#### **1. Why Batch Queries?**
- **Reduce Round Trips**: Minimizes HTTP/database connections.
- **Improve Caching**: Increases the chance of cache hits (e.g., Redis).
- **Lower Overhead**: Reduces network latency and server load.
- **Avoid N+1 Queries**: Common in ORMs/ORM-like frameworks where a single query triggers follow-up fetches (e.g., `User.findAll()` + `Post.findByUserId(userId)` for each user).

#### **2. Common Batch Patterns**
| **Pattern**               | **Use Case**                          | **Pros**                                  | **Cons**                                  |
|---------------------------|---------------------------------------|------------------------------------------|------------------------------------------|
| **Batch Fetch**           | Retrieve multiple records in one call. | Single query, low latency.               | Risk of data volume (e.g., `SELECT *`).  |
| **Paginated Queries**     | Fetch data in chunks (e.g., offset/limit). | Controls memory usage.                   | Requires multiple requests for full data.|
| **Joined Subqueries**     | Combine related data in one query.    | Reduces joins in application code.       | Complex SQL; risk of Cartesian products. |
| **Parallel Batch Processing** | Process batches concurrently.       | Speeds up large operations.              | Coordination overhead; potential race conditions. |
| **GraphQL Batching**      | Resolve nested GraphQL queries in bulk. | Efficient for APIs with deep resolution. | Requires GraphQL server support.       |

#### **3. Schema Considerations**
Batch queries often rely on **predefined relationships** or **denormalized data**. Ensure your schema supports efficient joins or bulk operations:

| **Component**       | **Description**                                                                 | **Example**                                  |
|----------------------|---------------------------------------------------------------------------------|----------------------------------------------|
| **Primary Keys**     | Unique identifiers for batch references.                                        | `user_id (PRIMARY KEY)`.                     |
| **Indexes**          | Optimize join/filter performance.                                               | `INDEX (post_user_id)` for `JOIN users`.    |
| **Composite Keys**   | Support multi-column batch queries.                                             | `UNIQUE (user_id, status)`.                  |
| **Batch Tables**     | Temporary tables for intermediate results.                                      | `#batch_users AS SELECT * FROM users WHERE active = true`. |
| **Partitioning**     | Distribute batch loads across shards.                                           | Partition `log_events` by `date`.           |

**Avoid:**
- Unbounded `WHERE IN` clauses (risk of SQL injection or performance degradation).
- Over-fetching (retrieve only required columns; use `SELECT id, name` instead of `SELECT *`).

---

### **Query Examples**

#### **1. Batch Fetch (Single Query)**
**Scenario**: Retrieve all active users and their posts in one call.
```sql
-- PostgreSQL
SELECT
    u.id, u.name,
    STRING_AGG(p.title, ', ') AS post_titles
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.active = true
GROUP BY u.id, u.name;
```
**Alternative (ORM-like):**
```python
# Pseudo-code for Django ORM
users = User.objects.filter(active=True).prefetch_related('posts')
```
**Warning**: `STRING_AGG` aggregates data; verify if this meets your needs (e.g., for UI rendering).

---

#### **2. Paginated Batch Queries**
**Scenario**: Fetch users in pages of 50, with total count.
```sql
-- SQL (with limit/offset)
SELECT * FROM users
WHERE active = true
ORDER BY created_at DESC
LIMIT 50 OFFSET 0; -- Page 1

-- GraphQL (batch-friendly)
query GetUsers($limit: Int = 50, $offset: Int = 0) {
  users(limit: $limit, offset: $offset, where: { active: true }) {
    id
    name
    posts {
      title
    }
  }
  totalUsers
}
```
**Optimization**: Use **keyset pagination** (e.g., `WHERE created_at < last_seen_at`) instead of `OFFSET` for large datasets.

---

#### **3. Joined Subqueries (Avoid N+1)**
**Scenario**: Fetch users and their post counts without individual queries.
```sql
-- SQL (IN subquery)
SELECT u.*
FROM users u
WHERE u.id IN (
    SELECT user_id FROM posts WHERE status = 'published'
    LIMIT 1000  -- Batch size
);
```
**ORM Equivalent (Bad):**
```python
# Anti-pattern: N+1 queries
users = User.objects.filter(post__status='published')
for user in users:
    user.posts.count()  # Separate query per user!
```

**Fix (ORM):**
```python
# Bulk annotate (PostgreSQL/ORM-specific)
users = User.objects.filter(post__status='published').annotate(
    post_count=Count('posts')
).only('id', 'name', 'post_count')
```

---

#### **4. Parallel Batch Processing**
**Scenario**: Process user data across threads/processes.
```python
# Python (e.g., with `concurrent.futures`)
def process_user(user):
    return user.posts.filter(status='published').count()

users = User.objects.filter(active=True).values_list('id', flat=True)[:1000]
results = list(process_user(User.objects.get(id=user_id)) for user_id in users)
```
**Database-Side Parallelism**:
```sql
-- PostgreSQL (parallel query)
SELECT * FROM users
WHERE active = true
PARALLEL USING 4;  -- Distribute across 4 workers
```

---

#### **5. GraphQL Batch Example**
**Scenario**: Batch resolve `posts` and `comments` for multiple users.
```graphql
query GetUserData($userIds: [ID!]!) {
  users(where: { id: { _in: $userIds } }) {
    id
    posts(batchResolve: true) {  # Hypothetical GraphQL feature
      id
      comments {
        id
        text
      }
    }
  }
}
```
**Backend Implementation (Node.js + DataLoader):**
```javascript
const DataLoader = require('dataloader');

const batchLoader = new DataLoader(async (userIds) => {
  const users = await db.query('SELECT id, posts FROM users WHERE id IN ($1)', userIds);
  // Group posts by user_id for batch resolution
  return users.reduce((acc, user) => {
    acc[user.id] = user.posts || [];
    return acc;
  }, {});
});
```

---

### **Requirements & Constraints**
| **Requirement**               | **Details**                                                                 |
|-------------------------------|-----------------------------------------------------------------------------|
| **Database Support**          | PostgreSQL (CTEs, `STRING_AGG`), MySQL (JSON functions), MongoDB (bulk ops). |
| **ORM Considerations**        | Use `prefetch_related`, `select_related`, or bulk annotate.               |
| **Error Handling**            | Batch queries may fail partially; implement retries or transaction rollback. |
| **Memory Limits**             | Avoid fetching terabytes of data; use chunking.                          |
| **Authentication**            | Ensure batch queries respect RBAC (e.g., `WHERE created_by = current_user`). |

---

### **Common Pitfalls & Mitigations**
| **Pitfall**                     | **Mitigation**                                                                 |
|---------------------------------|-------------------------------------------------------------------------------|
| **Cartesian Products**          | Limit subquery size or use explicit joins.                                    |
| **Race Conditions**             | Use database transactions or `SELECT FOR UPDATE`.                            |
| **Over-Fetching**               | Specify columns explicitly (`SELECT id, name`).                              |
| **Unpredictable Performance**   | Test with realistic batch sizes (e.g., 100–1,000 records).                   |
| **ORM Limitations**             | Fall back to raw SQL for complex batches (e.g., `JOIN`, `UNION`).           |

---

### **Related Patterns**
1. **Optimistic Locking**
   - Use `VERSION` or `CTIMESTAMP` columns to handle concurrent batch writes.
   - Example: `UPDATE users SET name = ? WHERE id = ? AND version = ?`.

2. **Caching Strategies**
   - Cache batch results (e.g., Redis) with TTLs to avoid repeated queries.
   - Example:
     ```python
     @cache.memoize(timeout=300)
     def get_user_posts_batch(user_ids):
         return db.query("SELECT * FROM posts WHERE user_id IN %s", user_ids)
     ```

3. **Event Sourcing**
   - Append-only logs for replayable batch processing (e.g., Kafka topics).

4. **Denormalization**
   - Pre-compute batch aggregations (e.g., `user_post_counts` table) for read-heavy workloads.

5. **Asynchronous Batch Jobs**
   - Offload batch processing to queues (e.g., Celery, AWS SQS) for non-critical data.

---

### **When to Avoid Batch Queries**
- **Real-Time Data**: If batch processing introduces unacceptable latency.
- **Small Datasets**: Overhead may outweigh benefits (e.g., <10 records).
- **Highly Dynamic Data**: Frequent updates invalidate batches (use `FOR UPDATE` cautiously).

---
**Further Reading**:
- [PostgreSQL Batch Operations](https://www.postgresql.org/docs/current/static/sql-select.html)
- [GraphQL DataLoader](https://github.com/graphql/dataloader)
- [ORM Anti-Patterns (N+1)](https://martinfowler.com/eaaCatalog/nPlusOne.html)