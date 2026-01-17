# **[Pattern] Pre-Compiled Query Plans – Reference Guide**

---

## **Overview**
FraiseQL optimizes GraphQL performance by **pre-compiling queries into SQL execution plans during schema compilation**, rather than resolving them dynamically at runtime. This approach ensures:
- **Consistent performance** (eliminates variable query planning overhead).
- **No runtime query planning** (reduces latency and resource usage).
- **Predictable execution** (SQL plans are generated once per unique query, not per request).

Unlike traditional GraphQL resolvers that build query trees on-the-fly, FraiseQL generates **static SQL queries** based on the GraphQL schema at **compile-time**. This avoids the need for runtime query analysis and plan caching, which is common in systems like Hasura or Apollo Federated.

---

## **Key Concepts**

### **1. Schema Compilation**
- FraiseQL processes the GraphQL schema alongside its underlying database schema (e.g., PostgreSQL, MySQL).
- For each **unique GraphQL query**, FraiseQL generates:
  - A **SQL query** (e.g., `SELECT * FROM users WHERE id = ?`).
  - An **execution plan** (optimized for the database engine).
- Plans are stored in a **plan cache** (e.g., a Redis store or database table).

### **2. Plan Caching**
- Plans are **persisted** after compilation to avoid recomputation.
- Cache invalidation occurs when:
  - The **database schema** changes (e.g., new columns, indexes).
  - The **GraphQL schema** is updated (e.g., new queries, type modifications).

### **3. Query Resolution at Runtime**
- When a client submits a GraphQL request:
  1. FraiseQL **looks up the pre-compiled plan** (from the cache).
  2. **Executes the SQL query** directly (bypassing GraphQL parsing overhead).
  3. Returns results in GraphQL-compatible format.

---

## **Schema Reference**

| **Component**               | **Description**                                                                 | **Example**                                                                 |
|-----------------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **GraphQL Schema**          | Defines types, queries, and relationships.                                    | `type User { id: ID! email: String! } query { users: [User!]! }`            |
| **Database Schema**         | Underlying RDBMS tables/columns (PostgreSQL, MySQL, etc.).                     | `CREATE TABLE users (id SERIAL PRIMARY KEY, email VARCHAR(255) NOT NULL);` |
| **Pre-Compiled Plan**       | SQL query + execution plan generated from the GraphQL schema.                 | `SELECT id, email FROM users` (with query plan).                           |
| **Plan Cache**              | Storage for compiled plans (e.g., Redis, PostgreSQL table).                    | `{ "users": "SELECT id, email FROM users", "plan_hash": "abc123" }`         |
| **Query Variables**         | Optional runtime parameters (e.g., `WHERE` clauses, pagination).               | `{ first: 10, after: "cursor" }`                                           |

---

## **Query Examples**

### **Example 1: Basic Query Compilation**
**GraphQL Query:**
```graphql
query {
  users {
    id
    email
  }
}
```
**Generated SQL Plan:**
```sql
SELECT id, email FROM users;
```
**Execution:**
- FraiseQL retrieves the pre-compiled `users` plan from the cache.
- Executes directly without runtime parsing.

---

### **Example 2: Query with Variables**
**GraphQL Query (with variables):**
```graphql
query GetUser($id: ID!) {
  user(id: $id) {
    id
    email
  }
}
```
**Generated SQL Plan:**
```sql
SELECT id, email FROM users WHERE id = $1;
```
**Execution:**
- FraiseQL uses the cached plan but substitutes `$1` with the runtime value (e.g., `id = 42`).
- Variables are **sanitized** to prevent SQL injection.

---

### **Example 3: Paginated Query**
**GraphQL Query (with pagination):**
```graphql
query UsersPage($first: Int, $after: String) {
  users(first: $first, after: $after) {
    edges {
      node {
        id
        email
      }
      cursor
    }
    pageInfo {
      hasNextPage
    }
  }
}
```
**Generated SQL Plan (with OFFSET/LIMIT):**
```sql
-- Assuming cursor-based pagination (e.g., OFFSET)
SELECT id, email FROM users
ORDER BY id
OFFSET $1 LIMIT $2;
```
**Key Notes:**
- FraiseQL **does not** natively support cursor-based pagination (unlike GraphQL specs).
- Workarounds:
  - Use `OFFSET` + `LIMIT` (less efficient for large datasets).
  - Implement **custom cursors** (e.g., `next_val` in PostgreSQL).

---

### **Example 4: Nested Queries (Relations)**
**GraphQL Schema:**
```graphql
type User {
  id: ID!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
}
```
**GraphQL Query (nested relation):**
```graphql
query {
  user(id: 1) {
    id
    posts {
      id
      title
    }
  }
}
```
**Generated SQL Plan (Joins):**
```sql
SELECT u.id, p.id AS post_id, p.title
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.id = $1;
```
**Execution:**
- FraiseQL **flattens nested queries** into a single SQL query with joins.
- Avoids N+1 query problems by default.

---

## **Advanced Patterns**

### **1. Dynamic Query Plans (Variables & Conditions)**
FraiseQL supports **conditional query plans** via runtime logic:
```graphql
query FilteredUsers($age: Int) {
  users(age: $age) {
    id
    email
  }
}
```
**Generated Plans:**
| Condition      | SQL Plan                          |
|----------------|------------------------------------|
| `age: null`    | `SELECT * FROM users;`             |
| `age: 25`      | `SELECT * FROM users WHERE age = $1;` |

---

### **2. Fragments & Reusable Plans**
**GraphQL Fragment:**
```graphql
fragment UserDetails on User {
  id
  email
}

query {
  users {
    ...UserDetails
    posts {
      title
    }
  }
}
```
**Generated Plan:**
- FraiseQL **reuses** the `UserDetails` fragment logic in the main query.
- Avoids duplicating fields in the SQL plan.

---

### **3. Plan Invalidation & Hot Reloading**
- **Schema Changes:**
  - Altering a table (e.g., adding a column) **invalidates all plans** referencing that table.
  - FraiseQL **recompiles** affected plans on next request.
- **Hot Reloading:**
  - Enable in `fraise.config.js`:
    ```javascript
    module.exports = {
      hotReload: true, // Recompile on schema changes
    };
    ```

---

## **Performance Considerations**

| **Aspect**               | **Pre-Compiled Plans** | **Traditional GraphQL** |
|--------------------------|-----------------------|-------------------------|
| Query Planning Time      | **Compile-time (0ms)** | **Runtime (varies)**    |
| Cache Overhead           | **Low (SQL plans)**   | **Higher (query trees)** |
| Database Load            | **Optimized SQL**     | **Suboptimal queries**  |
| Schema Flexibility       | **Requires recompilation** | **Dynamic**         |

**Best For:**
- **High-traffic APIs** (e.g., social media feeds).
- **Predictable workloads** (e.g., dashboards with fixed queries).
- **Read-heavy applications** (OLAP).

**Avoid For:**
- **Frequent schema changes** (e.g., microservices with rapid iterations).
- **Write-heavy workloads** (pre-compilation is read-optimized).

---

## **Related Patterns**

### **1. Query Caching (L2 Cache)**
- Combine with **Redis** or **CDN caching** for repeated queries.
- Example:
  ```graphql
  query GetTrendingPosts {
    posts(isTrending: true) {
      id
      title
    }
  }
  ```
  - Cache results in Redis with a TTL (e.g., 5 minutes).

### **2. Federation-Aware Plans**
- If using **GraphQL Federation**, FraiseQL can:
  - Generate **partitioned SQL queries** (e.g., `users` from one DB, `posts` from another).
  - Use **remote schema stitching** with pre-compiled subqueries.

### **3. Materialized Views**
- For **complex aggregations**, pre-compute results as materialized views:
  ```sql
  CREATE MATERIALIZED VIEW user_stats AS
  SELECT user_id, COUNT(*) as post_count
  FROM posts
  GROUP BY user_id;
  ```
  - Reference the view in FraiseQL plans:
    ```sql
    SELECT u.id, mv.post_count
    FROM users u
    JOIN user_stats mv ON u.id = mv.user_id;
    ```

### **4. Denormalization (Edge Caching)**
- **Avoid joins** by denormalizing frequently accessed data:
  ```sql
  ALTER TABLE posts ADD COLUMN user_email VARCHAR(255);
  ```
  - Update plans to reference the pre-denormalized data.

---

## **Troubleshooting**

| **Issue**                          | **Solution**                                                                 |
|------------------------------------|------------------------------------------------------------------------------|
| Plan cache miss (stale data)       | Check `fraise cache clear` command or invalidate schema changes.            |
| Slow query performance             | Review SQL plan with `EXPLAIN ANALYZE`; add indexes to bottleneck columns. |
| N+1 query problem                  | Ensure nested queries are flattened into single joins.                       |
| Variable substitution failures     | Validate type safety (e.g., `WHERE age = $1::int`).                         |

---

## **Configuration**
### **Enabling Pre-Compiled Plans**
```javascript
// fraiserc.js or fraiserc.toml
[schema]
precompile_plans = true  # Enable (default: true)
cache_backend = "postgres"  # Options: redis, postgres, memory
```

### **Custom Plan Cache**
```javascript
cache = {
  backend = "redis",
  host = "redis.example.com",
  ttl = 3600,  # Cache plans for 1 hour
}
```

---
## **Conclusion**
FraiseQL’s **pre-compiled query plans** eliminate runtime query planning overhead, delivering **consistent, high-performance GraphQL resolution**. This pattern is ideal for **read-heavy, high-traffic applications** where query predictability is critical. Combine it with **caching**, **denormalization**, or **federation** for advanced use cases.

For further reading:
- [FraiseQL Documentation](https://docs.fraise.dev)
- [SQL Query Optimization Guide](https://use-the-index-luke.com/)