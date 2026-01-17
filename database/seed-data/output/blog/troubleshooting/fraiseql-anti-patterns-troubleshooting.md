# **Debugging FraiseQL Anti-Patterns: A Troubleshooting Guide**
*A Practical Guide to Identifying and Fixing Database-Centric GraphQL Pitfalls*

---

## **1. Introduction**
FraiseQL (a hypothetical database-centric GraphQL resolution layer) introduces efficiency by pushing logic closer to the database—where it belongs. However, misusing its features can lead to **performance bottlenecks, security risks, and unmaintainable code**.

This guide helps you **quickly diagnose and resolve** common FraiseQL anti-patterns, ensuring optimal performance, security, and scalability.

---

## **2. Symptom Checklist: When to Suspect FraiseQL Anti-Patterns**
Check for these red flags:

| **Symptom**                          | **Likely Cause**                          | **Impact** |
|---------------------------------------|------------------------------------------|------------|
| ✅ Resolvers repeatedly querying DB   | Data fetching logic in wrong layer       | N+1 queries, slow responses |
| ✅ Runtime permission checks         | No declarative auth in schema            | Security risks, inconsistent access |
| ✅ Duplicate query projections        | Manual view generation in resolvers       | Logic duplication, hard to maintain |
| ✅ High query complexity → slow joins | Poorly designed views                   | High CPU, slow response times |
| ✅ Stored procedures with side effects| Business logic mixed with DB ops        | Unpredictable state changes |

**If you see these, proceed to troubleshooting.**

---

## **3. Common Issues & Fixes (With Code Examples)**

### **Issue 1: Misusing Resolvers for Data Fetching**
**Problem:**
Writing SQL-like logic in **Node.js/Python resolvers** instead of leveraging FraiseQL’s **compiled view system**.

**Symptom:**
```javascript
// ❌ Bad: Resolver does all work
const userResolver = (parent, args, context) => {
  const result = await knex('users')
    .where({ id: args.id })
    .join('posts', 'users.id', '=', 'posts.user_id')
    .select('users.name', 'posts.title');
  return result;
};
```
**Fix:** Push logic to **FraiseQL views** (compiled SQL queries).

**Solution:**
```sql
-- ✅ Good: Define a compiled view in FraiseQL
CREATE VIEW user_with_posts AS
  SELECT users.name, posts.title
  FROM users
  LEFT JOIN posts ON users.id = posts.user_id;
```
Then resolve in GraphQL:
```javascript
const userResolver = (parent, args) => {
  return db.query("SELECT * FROM user_with_posts WHERE user_id = $1", [args.id]);
};
```
**Debugging:**
- **Check:** Are resolvers doing `SELECT * FROM table` instead of using views?
- **Fix:** Refactor to **FraiseQL views** or **Knex joins** (if needed).

---

### **Issue 2: Runtime Authorization Instead of Declarative**
**Problem:**
Using **JavaScript checks** (`if (user.permissions)`) instead of **schema-level permissions**.

**Symptom:**
```javascript
// ❌ Bad: Runtime permission check
const editPostResolver = (parent, args, context) => {
  if (context.user.role !== 'admin') throw new Error("Unauthorized");
  return db.query("UPDATE posts SET content = $1 WHERE id = $2", [args.content, args.id]);
};
```
**Fix:** Enforce **declarative auth** in the schema.

**Solution:**
```graphql
type Post @auth(requires: { role: Admin }) {
  id: ID!
  content: String!
}
```
**Debugging:**
- **Check:** Are permissions hardcoded in resolvers?
- **Fix:** Use **GraphQL directives** (`@auth`) or **FraiseQL policy functions**.

---

### **Issue 3: Duplicate Query Projections**
**Problem:**
Manually rewriting the same query in multiple resolvers.

**Symptom:**
```javascript
// ❌ Bad: Repeated projection logic
const getUserPosts = () => db.query("SELECT * FROM posts WHERE user_id = $1", [userId]);
const getUserStats = () => db.query("SELECT COUNT(*) FROM posts WHERE user_id = $1", [userId]);
```
**Fix:** Define a **shared view** in FraiseQL.

**Solution:**
```sql
-- ✅ Good: Single source of truth
CREATE VIEW user_posts AS
  SELECT * FROM posts WHERE user_id = $1;
```
Then reuse in resolvers:
```javascript
const userPostsResolver = () => db.query("SELECT * FROM user_posts");
const userStatsResolver = () => db.query("SELECT COUNT(*) FROM user_posts");
```
**Debugging:**
- **Check:** Are projections duplicated across resolvers?
- **Fix:** Extract into **FraiseQL views** or **prepared statements**.

---

### **Issue 4: Poor View Design → N+1 Problems**
**Problem:**
Views that **don’t optimize joins**, forcing **multiple round-trips**.

**Symptom:**
```sql
-- ❌ Bad: No join optimization → N+1
SELECT * FROM posts WHERE user_id = 1;
-- Followed by N individual user fetches
```
**Fix:** Use **pre-built FraiseQL aggregations**.

**Solution:**
```sql
-- ✅ Good: Optimized view with joins
CREATE VIEW user_post_stats AS
  SELECT
    u.name,
    COUNT(p.id) as post_count,
    SUM(p.views) as total_views
  FROM users u
  LEFT JOIN posts p ON u.id = p.user_id
  WHERE u.id = $1
  GROUP BY u.name;
```
**Debugging:**
- **Check:** Are resolvers making **separate queries** for related data?
- **Fix:** Use **FraiseQL `JOIN` optimizations** or **Knex `with()`** for subqueries.

---

### **Issue 5: Side Effects in Stored Procedures**
**Problem:**
Stored procedures that **modify state outside transactions**.

**Symptom:**
```sql
-- ❌ Bad: Procedure with side effects
CREATE OR REPLACE FUNCTION send_notification(pid int) RETURNS void AS $$
BEGIN
  UPDATE posts SET status = 'read' WHERE id = pid;
  PERFORM pg_sleep(1); -- Unpredictable delay
  INSERT INTO notifications (...) VALUES (...); -- Race condition!
END;
$$ LANGUAGE plpgsql;
```
**Fix:** Enforce **transactional integrity** in FraiseQL.

**Solution:**
```sql
-- ✅ Good: Atomic transaction in FraiseQL
BEGIN;
UPDATE posts SET status = 'read' WHERE id = $1;
INSERT INTO notifications (...) VALUES ($2, NOW());
COMMIT;
```
**Debugging:**
- **Check:** Do stored procedures have **unexpected delays**?
- **Fix:** Use **FraiseQL transactions** or **Knex `transaction()`**.

---

## **4. Debugging Tools & Techniques**
| **Tool/Technique**          | **Use Case**                                                                 | **Example** |
|------------------------------|------------------------------------------------------------------------------|-------------|
| **FraiseQL Query Profiler**  | Analyze slow queries in real-time.                                           | `--profile ON` in `fraiseql.conf` |
| **Knex Logging**             | Check SQL execution times and resource usage.                                | `knex.debug(true)` |
| **PostgreSQL `EXPLAIN ANALYZE`** | Inspect query execution plans.                                              | `EXPLAIN ANALYZE SELECT * FROM user_posts;` |
| **GraphQL Tracing**          | Identify resolvers causing delays.                                           | `graphql-inspector` |
| **Database Locks**           | Detect deadlocks in long-running transactions.                               | `pg_locks` table |

**Quick Debugging Steps:**
1. **Check logs** (`fraiseql.log`, Knex debug mode).
2. **Profile slow queries** (`EXPLAIN ANALYZE`).
3. **Validate permissions** (`SELECT * FROM auth_policy_matches`).
4. **Review transaction state** (`SELECT * FROM pg_locks`).

---

## **5. Prevention Strategies**
### **✅ Best Practices to Avoid Anti-Patterns**
| **Strategy**                     | **How to Apply**                                                                 |
|-----------------------------------|----------------------------------------------------------------------------------|
| **Use FraiseQL Views**           | Push all data projections into **compiled views** (no raw SQL in resolvers).    |
| **Enforce Declarative Auth**      | Move permissions to **schema-level directives** (`@auth`).                       |
| **Leverage Transactions**         | Use **FraiseQL transactions** for multi-step DB ops.                            |
| **Optimize Joins Early**          | Design **index-friendly views** to avoid N+1.                                   |
| **Avoid Stored Procedures**       | Prefer **Knex/FraiseQL** for side-effect control.                                |

### **⚠️ Common Mistakes to Avoid**
- ❌ **Putting business logic in resolvers** → Move to **FraiseQL middle tier**.
- ❌ **Using `SELECT *` in views** → Always **project only needed fields**.
- ❌ **Ignoring database locks** → Use **optimistic concurrency** (`SELECT ... FOR UPDATE`).
- ❌ **Assuming joins are fast** → Always **profile with `EXPLAIN ANALYZE`**.

---

## **6. Final Checklist for Compliance**
| **Check**                          | **Pass/Fail** |
|-------------------------------------|---------------|
| ✅ All data fetching uses FraiseQL views |               |
| ✅ Permissions are declarative (not runtime checks) |          |
| ✅ No duplicate query logic          |               |
| ✅ Views are optimized for joins     |               |
| ✅ No side-effect stored procedures   |               |
| ✅ Transactions are atomic            |               |

**If any fail: Refactor immediately.**

---
### **Next Steps**
1. **Audit your FraiseQL schema** for these anti-patterns.
2. **Test fixes** with `fraiseql profiler`.
3. **Monitor performance** in production.

By following this guide, you’ll **eliminate bottlenecks, improve security, and keep your GraphQL API scalable**. 🚀