# **[Pattern] N+1 Query Prevention – Reference Guide**

---

## **Overview**
The **N+1 Query Problem** occurs when an application performs a single query to fetch a collection of entities (e.g., `SELECT * FROM users`), followed by **N additional queries** to fetch related data (e.g., `SELECT * FROM posts WHERE user_id = ?` for each user). This inefficiency causes performance degradation, especially in high-traffic applications.

This pattern prevents N+1 queries by **eagerly loading related data** upfront, typically using **joins (SQL), batch fetching (ORM), or pre-aggregating data (views/Denormalization)**. The most scalable approach is to **use database views** to precompute and flatten relationships, reducing round trips to the database.

---

## **Key Concepts & Implementation**

### **1. Root Cause of N+1 Queries**
- **Scenario**: A frontend request retrieves `User` objects, each requiring related data (e.g., `Post`, `Order`, `Profile`).
- **Result**: For `N` users, the application issues:
  ```
  1 query (fetch users)
  + N queries (fetch related data per user)
  = N+1 total queries
  ```
- **Impact**: High latency, database overload, and poor scalability.

### **2. Solutions to Prevent N+1 Queries**
| **Approach**            | **Pros**                          | **Cons**                          | **Best For**                     |
|-------------------------|-----------------------------------|-----------------------------------|----------------------------------|
| **Database Joins**      | Fast, single query               | Risk of overly large result sets  | Read-heavy workloads             |
| **Batch Fetching (ORM)**| Simple to implement (e.g., JPA `@BatchSize`) | ORM-specific, no SQL control   | ORM-based apps (e.g., Hibernate) |
| **Denormalization**     | Avoids joins, reduces reads      | Increases write complexity        | Read-heavy, write-sparse data    |
| **Database Views**      | Pre-aggregates data, scalable     | Requires DB schema changes         | Complex relationships            |

**This guide focuses on the *Views* approach** for its scalability and control over query optimization.

---

## **Schema Reference**

### **Example Schema: Users & Posts**
Assume a `users` table with related `posts`:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255),
    user_id INT REFERENCES users(id)
);
```

### **Problem: N+1 Queries**
```sql
-- Query 1: Fetch all users (1 query)
SELECT * FROM users;

-- Query 2-3: Fetch posts for each user (N queries, e.g., 100 users → 100 queries)
SELECT * FROM posts WHERE user_id = 1;
SELECT * FROM posts WHERE user_id = 2;
// ... and so on
```

### **Solution: Create a Materialized View**
A **materialized view** pre-computes and stores the joined result, eliminating N+1 queries.

```sql
-- Step 1: Create a view (or materialized view for frequent access)
CREATE VIEW users_with_posts AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    p.id AS post_id,
    p.title AS post_title
FROM users u
LEFT JOIN posts p ON u.id = p.user_id;

-- Step 2: Query the view in a single pass
SELECT * FROM users_with_posts;
```

**For dynamic data**, use a **refreshable materialized view** (PostgreSQL, Oracle) or a **denormalized table**:

```sql
CREATE TABLE users_with_posts AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    ARRAY_AGG(p.id) AS post_ids,
    ARRAY_AGG(p.title) AS post_titles
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id;
```

---

## **Query Examples**

### **1. Basic View Usage**
```sql
-- Fetch all users with their posts in one query
SELECT * FROM users_with_posts;
```

### **2. Filtering with Views**
```sql
-- Filter users by name and include posts
SELECT * FROM users_with_posts
WHERE user_name LIKE '%John%';
```

### **3. Joining Additional Tables**
```sql
-- Extend the view to include user profiles
CREATE VIEW users_with_posts_profiles AS
SELECT
    uwp.user_id,
    uwp.user_name,
    uwp.post_title,
    up.profile_picture
FROM users_with_posts uwp
LEFT JOIN user_profiles up ON uwp.user_id = up.user_id;
```

### **4. Partial Loading (Selective Joins)**
To avoid over-fetching, explicitly define columns:
```sql
-- Only load user names and post titles
SELECT user_name, post_title
FROM users_with_posts;
```

### **5. Denormalized Aggregation**
For analytics, pre-aggregate data:
```sql
CREATE TABLE user_post_stats AS
SELECT
    user_id,
    COUNT(*) AS post_count,
    ARRAY_AGG(DISTINCT post_id) AS post_ids
FROM posts
GROUP BY user_id;
```

---

## **Implementation Steps**

### **Step 1: Identify N+1 Patterns**
- Log slow queries (`EXPLAIN ANALYZE` in PostgreSQL).
- Review ORM-generated queries (e.g., Hibernate SQL logs).

### **Step 2: Design the View**
- Decide which relationships to denormalize.
- Include only necessary columns to avoid bloat.

### **Step 3: Implement the View**
```sql
CREATE VIEW optimized_users AS
SELECT
    u.id,
    u.name,
    jsonb_agg(jsonb_build_object(
        'id', p.id,
        'title', p.title
    )) AS posts
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id;
```

### **Step 4: Update Applications**
Replace N+1 queries with view-based queries:
```python
# Old (N+1):
users = db.session.query(User).all()
for user in users:
    user.posts = db.session.query(Post).filter_by(user_id=user.id).all()

# New (Single Query):
result = db.execute("SELECT * FROM optimized_users")
users = [User(id=r['id'], name=r['name'], posts=r['posts']) for r in result]
```

### **Step 5: Handle Updates**
- For **real-time data**, use triggers or application-level refreshes.
- For **batch refreshes**, schedule job e.g., `REFRESH MATERIALIZED VIEW users_with_posts`.

---

## **Performance Considerations**

| **Factor**               | **Impact**                                                                 | **Mitigation**                          |
|--------------------------|----------------------------------------------------------------------------|------------------------------------------|
| **View Bloat**           | Large result sets slow down queries.                                      | Select only required columns.            |
| **Write Overhead**       | Denormalization increases write complexity.                               | Use triggers or application-side updates.|
| **Cache Staleness**      | Materialized views may lag behind source data.                           | Refresh periodically or on-demand.       |
| **Schema Changes**       | Views require schema alignment.                                           | Use views for stable relationships.      |

---

## **Query Examples in Different Languages**

### **PostgreSQL (Views)**
```sql
-- Create and query
CREATE VIEW user_posts AS
SELECT u.*, p.title FROM users u LEFT JOIN posts p ON u.id = p.user_id;

-- Usage
SELECT * FROM user_posts WHERE u.id = 1;
```

### **MySQL (Denormalized Table)**
```sql
-- Create a denormalized table
CREATE TABLE user_posts_denormalized AS
SELECT
    u.id AS user_id,
    u.name AS user_name,
    GROUP_CONCAT(p.title SEPARATOR ', ') AS post_titles
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id;

-- Query
SELECT * FROM user_posts_denormalized WHERE user_id = 1;
```

### **Application-Level (ORM: Django)**
```python
# Old (N+1):
users = User.objects.all()
for user in users:
    user.posts = Post.objects.filter(user=user).all()

# New (Prefetch_related):
from django.db.models import Prefetch
users = User.objects.prefetch_related(
    Prefetch('posts', queryset=Post.objects.select_related())
).all()
```

---

## **When to Avoid This Pattern**
- **High Write Volume**: Denormalization complicates transactions.
- **Frequent Schema Changes**: Views may require frequent recreation.
- **Overly Complex Relationships**: Joins can become unmanageable with >3 tables.

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **Use Case**                          |
|---------------------------|-------------------------------------------------------------------------------|----------------------------------------|
| **Eager Loading**         | ORM-level batch fetching (e.g., `@BatchSize`, `Prefetch_related`).           | ORM applications.                     |
| **Data Denormalization**  | Store redundant data to reduce joins.                                         | Read-heavy, write-sparse systems.     |
| **Caching (Redis/Memcached)** | Cache query results to avoid repeated DB calls.                          | High-read, low-write workloads.       |
| **GraphQL (Batch Resolvers)** | Efficiently fetch nested data in GraphQL APIs.                               | API-driven applications.              |
| **Event Sourcing**        | Append-only data model to reduce query complexity.                            | Audit-heavy, time-series data.        |

---

## **Tools & Libraries**
| **Tool**               | **Purpose**                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| **PostgreSQL**         | Materialized views, `EXPLAIN ANALYZE` for query optimization.              |
| **Django ORM**         | `Prefetch_related`, `select_related` for eager loading.                   |
| **Hibernate (JPA)**    | `@BatchSize`, `@Fetch(FetchMode.SUBSELECT)` for batch fetching.           |
| **DBeaver/pgAdmin**    | Visualize query plans and identify N+1 patterns.                           |
| **SQLAlchemy**         | `joinedload()` for lazy/eager loading.                                     |

---

## **Example: Full Workflow**
### **Problem**
A blog app fetches `User` objects and their `Post` objects, causing 100+ queries for 10 users.

### **Solution: Views**
1. **Create a view**:
   ```sql
   CREATE VIEW blog_users_with_posts AS
   SELECT
       u.id, u.username,
       jsonb_agg(jsonb_build_object('id', p.id, 'title', p.title)) AS posts
   FROM users u
   LEFT JOIN posts p ON u.id = p.user_id
   GROUP BY u.id;
   ```
2. **Query the view**:
   ```sql
   SELECT * FROM blog_users_with_posts WHERE id IN (1, 2, 3);
   ```
3. **Application code**:
   ```python
   results = db.execute("SELECT * FROM blog_users_with_posts")
   users = [User(id=r['id'], username=r['username'], posts=r['posts']) for r in results]
   ```

### **Result**
- **Before**: 101 queries (1 + 100).
- **After**: 1 query (view join).

---
## **Conclusion**
The **N+1 Query Prevention** pattern mitigates performance bottlenecks by **eagerly loading relationships** via views or denormalization. Choose between:
- **Views/Materialized Views** for read-heavy, stable schemas.
- **Denormalized Tables** for flexibility and write efficiency.
- **ORM Eager Loading** for rapid prototyping with ORMs.

**Key Takeaways**:
✅ Prefer **joins/views** for predictable queries.
✅ Use **denormalization** for analytics or high-read workloads.
✅ **Monitor** query plans to validate improvements.
❌ Avoid **over-denormalizing** if writes are frequent.

For further optimization, combine this pattern with **caching** or **database sharding**.