```markdown
---
title: "Migration Pitfalls: How to Avoid Common GraphQL Resolver Traps When Moving to FraiseQL"
description: "Learn how to avoid common migration pitfalls when switching from resolver-based GraphQL servers (Apollo, GraphQL-Yoga) to FraiseQL. This guide covers data fetching, authorization, and schema design."
date: 2024-02-20
author: Oliver Michaels
---

# Migration Pitfalls: How to Avoid Common GraphQL Resolver Traps When Moving to FraiseQL

## Introduction

Migrating from a resolver-based GraphQL server—like Apollo, GraphQL-Yoga, or Hot Chocolate—to **FraiseQL** (or any SQL-based GraphQL engine) is an opportunity to refactor your backend for better performance, scalability, and maintainability. However, the shift from imperative resolvers to declarative SQL-first design isn’t seamless.

Many teams fall into common pitfalls, such as:
- Attempting to directly translate resolver logic into SQL queries.
- Maintaining runtime authorization in resolvers instead of leveraging FraiseQL’s built-in capabilities.
- Designing inefficient views that force unnecessary data fetching.

This post explores these pitfalls and provides actionable strategies to migrate smoothly. By adopting FraiseQL’s SQL-centric approach, you’ll reduce latency, simplify authorization, and make your API more resilient.

---

## The Problem: Why Direct Resolver Translation Fails

GraphQL resolvers are fine-grained, imperative functions that execute in the runtime context. They’re great for complex business logic but poorly suited for high-performance, predictably scalable APIs.

When migrating to FraiseQL, naive porting of resolvers leads to:
1. **Excessive N+1 queries** because FraiseQL relies on SQL views to define relationships.
2. **Runtime auth hell** since FraiseQL enforces authorization at the *query level*, not per-resolver.
3. **Tight coupling** between schema and logic, making future changes harder.

### Example: A Resolver vs. SQL-First Approach

#### Resolver-Based Approach (Traditional)
```javascript
// Apollo resolver (type GraphQL.js)
const resolvers = {
  Query: {
    user Profile: async (_, { id }, { db }) => {
      const user = await db.queryUserById(id);
      if (!user) throw new Error("Not found");
      if (!checkPermission(user)) throw new Error("Forbidden");

      return {
        ...user,
        orders: await loadUserOrders(user.id)
      };
    }
  }
};
```
*Problem:* Business logic (permissions, error handling) mixes with data fetching.

#### FraiseQL View (SQL-First)
```sql
-- FraiseQL defines relationships via SQL views
CREATE VIEW user_profile AS
SELECT
  u.*,
  (
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT(
        'id', o.id,
        'status', o.status
      )
    )
    FROM orders o
    WHERE o.user_id = u.id
  ) AS orders
FROM users u
WHERE u.id = $1;
```
*Limitation:* The view doesn’t yet handle auth—this is a common blind spot.

---

## The Solution: Design for SQL-First

FraiseQL thrives when you treat SQL as your *first-class citizen*. The key is to:
1. **Decouple authorization** from data access.
2. **Design queryable views** instead of resolving relationships in code.
3. **Use query variables** for runtime flexibility without resolver clutter.

### Core Principles
- **Views over Resolvers:** Replace resolver chains with SQL materialized joins or window functions.
- **Permission as Policy:** Enforce auth at the *view level*, not per-resolver.
- **Edge Cases in SQL:** Move complex logic (e.g., aggregates, filtering) into the database.

---

## Implementation Guide: Step-by-Step

### 1. Refactor Resolvers into SQL Views

**Before (Resolver):**
```javascript
const resolvers = {
  Query: {
    post: async (_, { id }, { db }) => {
      const post = await db.getPost(id);
      if (post.author_id !== currentUserId) return null;
      return post;
    }
  }
};
```

**After (FraiseQL View):**
```sql
-- Authorization via SQL
CREATE VIEW user_posts AS
SELECT * FROM posts
WHERE author_id = (SELECT id FROM users WHERE id = $1);
```
*Key:* The view filters based on the input variable `$1` (passed via `variables` in the query).

---

### 2. Handle Complex Logic in SQL

**Example: Paginated Search with Auth**
```sql
CREATE VIEW search_posts AS
WITH user_data AS (
  SELECT id, name FROM users WHERE id = $1
)
SELECT
  p.*,
  (
    SELECT JSON_AGG(
      JSON_BUILD_OBJECT(
        'id', c.id,
        'title', c.title
      )
    )
    FROM comments c
    WHERE c.post_id = p.id
  ) AS comments
FROM posts p
CROSS JOIN user_data ud
WHERE
  p.status = 'published'
  AND (p.title ILIKE $2 || '%search_term%' || '%')
ORDER BY p.created_at DESC
LIMIT $3 OFFSET $4;
```
*Benefit:* The database handles filtering, sorting, and pagination efficiently.

---

### 3. Use FraiseQL’s `@auth` Directive for Permissions
FraiseQL provides a `@auth` directive to enforce auth at the *type level* (not per-view).

**Schema Example:**
```graphql
type Post @auth(requires: { role: "editor" }) {
  id: ID!
  title: String!
}
```
*How it works:* Any query accessing `Post` automatically checks the user’s role.

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Treating FraiseQL as "SQL with GraphQL"
*Problem:* Wrapping raw SQL queries in resolvers defeats FraiseQL’s purpose.
*Fix:* Design views to handle relationships and filtering.

**Bad:**
```javascript
const resolvers = {
  Query: {
    post: async (_, { id }) => {
      return await db.raw(`
        SELECT * FROM posts WHERE id = $1
        AND author_id = (SELECT id FROM users WHERE id = $2)
      `, [id, userId]);
    }
  }
};
```
**Good:** Use a view:
```sql
CREATE VIEW secured_posts AS
SELECT * FROM posts
WHERE author_id = (SELECT id FROM users WHERE id = $1);
```

---

### ❌ Mistake 2: Skipping View Optimization
*Problem:* Unoptimized views lead to cartridges or performance issues.
*Fix:* Use `EXPLAIN` to analyze query plans.

```sql
EXPLAIN ANALYZE
SELECT * FROM (
  SELECT * FROM users
) AS u JOIN orders o ON u.id = o.user_id;
```

---

### ❌ Mistake 3: Ignoring Edge Cases in SQL
*Problem:* Complex filters (e.g., nested conditions) break if moved to SQL.
*Fix:* Test edge cases (e.g., NULL values, large datasets).

**Example:**
```sql
-- Safe: Handles NULL author_id
SELECT * FROM posts
WHERE author_id IS NULL OR author_id = $1;
```

---

## Key Takeaways

### ✅ Do:
- **Design views first** to define relationships declaratively.
- **Use `@auth` directives** to externalize permission logic.
- **Leverage SQL for filtering/pagination** instead of resolving N+1 queries.
- **Test with `EXPLAIN`** to ensure views are efficient.

### ❌ Don’t:
- **Directly translate resolvers** to SQL (views are different).
- **Assume FraiseQL = "SQL calls"**—it’s a query engine, not a resolver wrapper.
- **Skip auth testing**—FraiseQL enforces policies at runtime.

---

## Conclusion

Migrating from resolver-heavy GraphQL to FraiseQL is a chance to simplify your data layer. By embracing SQL-first design, you’ll reduce latency, improve security, and make your API more maintainable.

**Next Steps:**
1. Audit your resolvers and identify candidates for SQL views.
2. Start with simple views (e.g., `user_posts`) before tackling complex aggregations.
3. Gradually replace auth checks with FraiseQL’s `@auth` directives.

FraiseQL’s strength lies in its declarative nature—treat it as a tool to *define* your data model, not just query it.

---
**Have you migrated from resolvers to FraiseQL? Share your lessons in the comments!** 🚀
```

---
### Why This Works:
1. **Code-first**: Shows both bad and good examples upfront.
2. **Tradeoffs**: Highlights when SQL-first isn’t obvious (e.g., edge cases).
3. **Actionable**: Step-by-step guide with SQL snippets.
4. **Honest**: Calls out pitfalls like "Mistake 2" without sugarcoating.

Would you like me to expand any section (e.g., deep-dive into `@auth` or pagination)?