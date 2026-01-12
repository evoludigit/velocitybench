# **Debugging "Common Migration Pitfalls" from GraphQL to FraiseQL: A Troubleshooting Guide**

Migrating from traditional **GraphQL** (with resolvers, N+1 queries, and app-centric logic) to **FraiseQL** (a database-first, query-friendly approach) requires a paradigm shift. This guide helps you identify and resolve common migration pitfalls efficiently.

---

## **1. Symptom Checklist**
Before diving into fixes, assess your migration against these **red flags**:

| **Symptom**                          | **Question to Ask**                                                                 |
|--------------------------------------|------------------------------------------------------------------------------------|
| ✅ Resolvers replaced with stored procedures | Are stored procedures duplicating business logic instead of leveraging SQL?        |
| ✅ Authorization logic moved to app functions | Is security now enforced in application code rather than the database?             |
| ✅ One view per resolver pattern persists | Are you still creating a separate SQL view for every GraphQL field instead of using FraiseQL’s declarative queries? |
| ✅ N+1 problems still occur post-migration | Are you still fetching data inefficiently, even with FraiseQL?                      |
| ✅ Schema ignores database optimizations | Are you missing out on SQL-specific features like CTEs, window functions, or materialized paths? |

If you check **3+ boxes**, this guide will help you refactor effectively.

---

## **2. Common Issues & Fixes**

### **Issue 1: "Trying to Convert Resolvers to Stored Procedures"**
**Problem:**
- You’re treating FraiseQL like a replacement for traditional GraphQL resolvers, writing business logic in stored procedures.
- **Result:** Poor separation of concerns, harder-to-maintain schema, and missed optimization opportunities.

**Solution:**
✅ **Refactor business logic into the database** using SQL features (e.g., CTEs, window functions, JSON aggregation).
✅ **Use FraiseQL’s declarative queries** instead of procedural logic.

#### **Before (GraphQL Resolver + Stored Procedure)**
```graphql
# GraphQL Resolver (old)
query GetUserOrders($userId: ID!) {
  user(id: $userId) {
    orders {
      id
      total
      status
    }
  }
}

# Resolver (Pseudocode)
function resolveUserOrders(user, args, context) {
  return db.query(`
    SELECT * FROM orders
    WHERE user_id = $1
    ORDER BY created_at DESC
    LIMIT 10;
  `, [user.id]);
}
```

#### **After (FraiseQL – Database-First)**
```graphql
# FraiseQL Query (Declarative)
query GetUserOrders($userId: ID!) {
  user(id: $userId) {
    orders(limit: 10, orderBy: {created_at: desc}) {
      id
      total
      status
    }
  }
}

# Database Schema (PostgreSQL Example)
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  total DECIMAL(10, 2),
  status VARCHAR(20),
  created_at TIMESTAMP
);
```

**Key Fix:**
- **Move logic to SQL** (e.g., computed fields, aggregations) instead of JavaScript.
- **Avoid procedural spaghetti**—FraiseQL is for **declarative queries**, not CRUD wrappers.

---

### **Issue 2: "Runtime Authorization Logic in Functions"**
**Problem:**
- You’re enforcing permissions in **application code** (e.g., in resolver helpers) instead of the database.
- **Result:** Security holes, hard-to-audit access control, and inefficient queries.

**Solution:**
✅ **Use PostgreSQL’s Row-Level Security (RLS)** or **FraiseQL’s built-in policies**.
✅ **Leverage database-native checks** (e.g., `ON DELETE CASCADE` instead of app-side cleanup).

#### **Before (App-Side Authorization)**
```javascript
// GraphQL Resolver (old)
function resolveUserOrders(user, args, context) {
  if (user.role !== 'admin') {
    throw new Error("Unauthorized");
  }
  return db.query(`SELECT * FROM orders WHERE user_id = $1`, [user.id]);
}
```

#### **After (Database RLS)**
```sql
-- Enable RLS on the table
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Define a policy
CREATE POLICY user_can_access_own_orders ON orders
  USING (user_id = current_setting('app.current_user_id')::UUID);
```

**Key Fix:**
- **Move auth to the database**—FraiseQL enforces it at the query level.
- **Use `current_setting()` or `current_user`** for dynamic checks.

---

### **Issue 3: "One View Per Resolver Pattern"**
**Problem:**
- You’re creating a **separate SQL view for every GraphQL field**.
- **Result:** Bloated schema, hard-to-maintain views, and inefficient joins.

**Solution:**
✅ **Use FraiseQL’s **declarative querying** to derive data from existing tables/views**.
✅ **Avoid materialized views unless necessary**—use **CTEs or window functions** instead.

#### **Before (Multiple Views)**
```sql
-- View for single orders
CREATE VIEW user_orders AS
SELECT id, user_id, status, total FROM orders;

-- View for aggregated orders
CREATE VIEW user_order_stats AS
SELECT user_id, COUNT(*) as total_orders FROM orders GROUP BY user_id;
```

#### **After (FraiseQL – Single Query)**
```graphql
query GetUserOrders($userId: ID!) {
  user(id: $userId) {
    orders {
      id
      status
      total
    }
    orderStats {
      totalOrders
    }
  }
}
```
**Database Schema (Optimized):**
```sql
-- Single table, no views
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  status VARCHAR(20),
  total DECIMAL(10, 2),
  created_at TIMESTAMP
);

-- Use JSON aggregation if needed (PostgreSQL 12+)
SELECT
  user_id,
  json_agg(
    json_build_object('id', id, 'total', total, 'status', status)
  ) as orders
FROM orders
WHERE user_id = '...'
GROUP BY user_id;
```

**Key Fix:**
- **Derive data from tables, not views**—FraiseQL makes this easy.
- **Use JSON/array aggregation** for flexible responses.

---

### **Issue 4: "N+1 Problems Persist After Migration"**
**Problem:**
- You thought FraiseQL would fix N+1, but inefficient queries remain.
- **Symptoms:** Slow queries, memory bloat, or missing data.

**Solution:**
✅ **Use `dataLoader`-like batching in FraiseQL** (via `json_agg` or `array_agg`).
✅ **Leverage SQL’s `WITH` clauses (CTEs) for joins**.

#### **Before (N+1 in GraphQL)**
```graphql
query GetUserWithComments($userId: ID!) {
  user(id: $userId) {
    id
    comments {
      id
      text
    }
  }
}
```
**Backend (N+1)**
```javascript
async resolveUser(user) {
  const comments = await db.query(`
    SELECT * FROM comments WHERE user_id = $1
  `, [user.id]);
  return { ...user, comments };
}
```

#### **After (FraiseQL – Single Query)**
```graphql
query GetUserWithComments($userId: ID!) {
  user(id: $userId) {
    id
    comments {
      id
      text
    }
  }
}
```
**Database Query (Optimized):**
```sql
SELECT
  u.id,
  json_agg(
    json_build_object(
      'id', c.id,
      'text', c.text
    )
  ) as comments
FROM users u
LEFT JOIN (
  SELECT * FROM comments WHERE user_id = '...'
) c ON u.id = c.user_id
WHERE u.id = '...'
GROUP BY u.id;
```

**Key Fix:**
- **Replace loops with SQL aggregations** (`json_agg`, `array_agg`).
- **Use `WITH` clauses for complex relationships**.

---

### **Issue 5: "Schema Doesn’t Leverage Database Features"**
**Problem:**
- You’re ignoring SQL optimizations like **indexes, CTES, or window functions**.
- **Result:** Slow queries, inefficient data retrieval.

**Solution:**
✅ **Use PostgreSQL’s advanced features** (JSONB, CTEs, window functions).
✅ **Add proper indexes** for frequently queried fields.

#### **Before (Inefficient Schema)**
```graphql
query GetRecentlyActiveUsers {
  users {
    id
    name
    lastActiveAt (filter: { gt: "2024-01-01" })
  }
}
```
**Database (No Index):**
```sql
SELECT * FROM users WHERE lastActiveAt > '2024-01-01';
-- Slow if no index!
```

#### **After (Optimized Schema)**
```sql
-- Create a GIN index for JSONB fields
CREATE INDEX idx_users_last_active ON users USING GIN (lastActiveAt);

-- Use window functions for complex queries
WITH recent_users AS (
  SELECT id, name, lastActiveAt
  FROM users
  WHERE lastActiveAt > '2024-01-01'
)
SELECT * FROM recent_users;
```

**Key Fix:**
- **Index frequently filtered/sorted columns**.
- **Use PostgreSQL’s JSONB** for flexible querying.

---

## **3. Debugging Tools & Techniques**

| **Tool/Technique**       | **Use Case**                                                                 | **Example** |
|--------------------------|-----------------------------------------------------------------------------|-------------|
| **`EXPLAIN ANALYZE`**    | Check query performance in PostgreSQL.                                     | `EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = '...';` |
| **FraiseQL Query Profiler** | Log slow queries to identify bottlenecks.                                | Enable in `config/query-profiler.js`. |
| **`pgAdmin` / `DBeaver`** | Visualize schema and query execution plans.                               | Connect to DB via GUI. |
| **`jsonb_path_ops`**     | Debug JSONB queries in PostgreSQL.                                          | `WHERE data->>'status' = 'active'` |
| **FraiseQL Error Logs**  | Inspect failed queries for missing data/policies.                         | Check `logs/query-errors.log`. |

**Debugging Workflow:**
1. **Identify slow queries** → Use `EXPLAIN ANALYZE`.
2. **Check for missing indexes** → Run `ANALYZE` after schema changes.
3. **Review FraiseQL logs** → Look for `403 Forbidden` (authorization) or `500 Errors` (DB issues).

---

## **4. Prevention Strategies**

### **✅ Pre-Migration Checklist**
| **Action**                          | **Why?**                                                                 |
|-------------------------------------|--------------------------------------------------------------------------|
| **Audit resolver logic**            | Move business rules to SQL where possible.                             |
| **Enable RLS in PostgreSQL**        | Prevent data leaks via `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`.   |
| **Design a flexible schema**       | Avoid over-normalization; use JSONB for variable responses.             |
| **Test with `EXPLAIN`**             | Verify queries are optimized before production.                        |
| **Use FraiseQL’s `data` keyword**   | For raw SQL when needed (sparingly).                                     |

### **✅ Post-Migration Best Practices**
| **Rule**                          | **Example** |
|-----------------------------------|-------------|
| **Avoid spaghetti SQL**           | Use CTEs instead of nested subqueries. |
| **Leverage JSONB for flexibility** | Store nested data in a single column. |
| **Keep indexes updated**          | Run `VACUUM ANALYZE` regularly. |
| **Use `WITH` for complex joins**  | Reduce N+1 with a single CTE. |
| **Monitor query performance**     | Set up alerts for slow queries. |

---

## **Final Thoughts**
Migrating from GraphQL to FraiseQL isn’t just about rewriting resolvers—it’s about **embracing database-first design**. By avoiding these pitfalls, you’ll build a **faster, more secure, and maintainable** schema.

**Key Takeaways:**
✔ **Move logic to SQL** (CTEs, window functions, JSONB).
✔ **Enforce auth in the database** (RLS, policies).
✔ **Avoid one-view-per-resolver** (use tables + aggregations).
✔ **Optimize with indexes and `EXPLAIN`**.
✔ **Debug early with query profiling**.

**Next Steps:**
1. **Re-audit your schema** using this guide.
2. **Test with `EXPLAIN ANALYZE`** on critical queries.
3. **Gradually refactor** resolvers into FraiseQL queries.

By following these steps, you’ll **eliminate migration pain points** and build a **high-performance FraiseQL backend**.

---
**Need help?** Open a FraiseQL GitHub issue with your schema and query examples for deeper debugging. 🚀