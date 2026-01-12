```markdown
---
title: "Migrating from Resolver-Based GraphQL to FraiseQL: Common Migration Pitfalls"
date: 2023-11-15
tags: ["GraphQL", "FraiseQL", "Database Design", "API Migration", "Backend Engineering"]
author: "Alex Carter"
---

# Migrating from Resolver-Based GraphQL to FraiseQL: Common Migration Pitfalls (And How to Avoid Them)

![Migrating from Apollo to FraiseQL](https://images.unsplash.com/photo-1630042332837-506714b90b02?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1470&q=80)

Migrating a GraphQL API from a resolver-based architecture (like Apollo Server or GraphQL-Yoga) to **FraiseQL**—a database-first, schema-agnostic GraphQL engine—is a significant shift in how you design and implement your backend. FraiseQL's strength lies in its SQL-first approach, eliminating the need for complex resolver logic. However, this transition isn't always smooth.

If you've tried to lift-and-shift your resolver-based GraphQL API to FraiseQL, you might have encountered frustrating roadblocks:
- **Authorization logic breaking** because FraiseQL doesn't natively support resolver-level security checks.
- **Performance bottlenecks** due to naive SQL query translations.
- **Schema design conflicts** where resolver-heavy schemas struggle to map cleanly to database tables.

In this guide, you'll learn the **common pitfalls** developers face when migrating from resolver-based GraphQL to FraiseQL, why they happen, and—most importantly—how to avoid them. We'll cover **mindset shifts**, **practical refactoring strategies**, and **code examples** to help you migrate successfully.

---

## The Problem: Why Direct Resolver Translation Fails

Resolver-based GraphQL servers (like Apollo or Hot Chocolate) abstract database interactions into business logic layers. Their strength is flexibility, but this flexibility comes with hidden complexity:

1. **Resolver Chaining and Overfetching**:
   In resolver-heavy APIs, fetching a `User` might require 3-5 nested resolver calls to gather all data (e.g., `User → Posts → Comments → Author`), leading to N+1 queries and inefficient client-side data assembly.

   ```javascript
   // Example resolver-heavy GraphQL schema (Apollo)
   type User {
     id: ID!
     name: String!
     posts: [Post!]!  // Resolver might fetch posts, then for each post, fetch comments
   }

   type Post {
     id: ID!
     title: String!
     author: User!
     comments: [Comment!]!  // Resolver might fetch comments, then for each comment, fetch user
   }
   ```

   This design forces the client to overfetch or deal with fragmented data.

2. **Authorization Logic Scattered Across Resolvers**:
   Security rules are often baked into resolvers using middleware or decorators. FraiseQL, however, treats authorization as a **view-level concern** (via Fraise's `AUTH` clause in SQL), not a resolver concern.

   ```javascript
   // Apollo resolver with authorization
   async function getUser(root, args, context) {
     if (!context.user.isAdmin) throw new Error("Not authorized");
     return db.getUser(args.id);
   }
   ```

   FraiseQL expects security to be enforced at the **SQL level**, not the resolver level.

3. **Schema Overengineering**:
   Resolver-based APIs often create overly granular types to satisfy specific query needs. FraiseQL prefers **simpler views** that map directly to database tables, with joins handled in SQL.

   ```javascript
   // Apollo: Many types for nesting
   type User {
     posts: [Post!]
   }

   type Post {
     comments: [Comment!]
   }
   ```

   FraiseQL favors:
   ```sql
   -- Single view with joins
   VIEW user_posts_comments AS
   SELECT u.*, p.*, c.*
   FROM users u
   JOIN posts p ON u.id = p.author_id
   JOIN comments c ON p.id = c.post_id;
   ```

4. **Performance Anti-Patterns**:
   Resolvers often use **pagination manually** (e.g., fetching 1000 items at once and letting the client paginate), leading to slow responses and large payloads. FraiseQL encourages **native pagination** via SQL `LIMIT` and `OFFSET`.

---

## The Solution: FraiseQL’s Database-First Approach

FraiseQL’s power comes from treating your API as an **SQL database with a GraphQL interface**. To migrate successfully, you must shift from:
- **Resolver-driven logic** → **SQL-first logic**
- **Overly nested types** → **Flat views with joins**
- **Runtime authorization** → **SQL-based authorization**
- **Manual pagination** → **SQL pagination**

Here’s how:

### 1. Start with a Database-Centric Schema
Instead of designing your GraphQL schema first, start with your **database schema** and **views**. FraiseQL will generate a GraphQL schema from your SQL.

#### Before (Resolver-Based):
```javascript
type Post {
  id: ID!
  title: String!
  author: User!
  comments: [Comment!]!
}
```

#### After (FraiseQL Database-First):
```sql
-- Define a view that includes all needed data
CREATE VIEW post_with_author_comments AS
SELECT
  p.*,
  u.name as author_name,
  json_agg(c.*) as comments
FROM posts p
JOIN users u ON p.author_id = u.id
LEFT JOIN comments c ON p.id = c.post_id
GROUP BY p.id, u.name;
```

### 2. Move Authorization to SQL
FraiseQL’s `AUTH` clause replaces resolver-based authorization. You can:
- Use **role-based checks** in SQL.
- Filter data at the database level.

#### Example: User Can Only See Their Posts
```sql
CREATE VIEW user_posts AS
SELECT p.*
FROM posts p
WHERE p.author_id = $1  -- $1 is a FraiseQL auth variable
AUTH user_id = author_id;  -- Ensures only the logged-in user sees their posts
```

### 3. Embrace Native Pagination with SQL
Instead of fetching all data and letting the client paginate, use SQL’s `LIMIT` and `OFFSET`:

```sql
SELECT *
FROM users
LIMIT 10 OFFSET 0;
```

#### FraiseQL Query:
```graphql
query {
  users(first: 10, offset: 0) {
    id
    name
  }
}
```

### 4. Design for Views, Not Resolvers
FraiseQL encourages **single-purpose views** with joins instead of deep resolver nesting. For example:

#### FraiseQL View:
```sql
CREATE VIEW post_with_likes AS
SELECT p.*, l.count as like_count
FROM posts p
LEFT JOIN (
  SELECT post_id, COUNT(*) as count
  FROM likes
  GROUP BY post_id
) l ON p.id = l.post_id;
```

#### GraphQL Query:
```graphql
query {
  postWithLikes(id: "123") {
    title
    likeCount
  }
}
```

---

## Implementation Guide: Step-by-Step Migration

### Step 1: Audit Your Resolver Logic
Before migrating, document:
- **What resolvers do** (e.g., "fetch posts for a user").
- **How they authorize data** (e.g., "only admins can see drafts").
- **How they paginate** (e.g., "fetch 20 items at a time").

### Step 2: Design FraiseQL Views
For each resolver, create a **SQL view** that:
1. Joins the necessary tables.
2. Includes all fields the resolver returns.
3. Applies authorization rules via `AUTH`.

#### Example: User Profile Resolver → FraiseQL View
**Apollo Resolver:**
```javascript
async function getUserProfile(root, args, context) {
  const user = await db.getUser(args.id);
  if (!context.user.isAdmin && args.id !== context.user.id) {
    throw new Error("Not authorized");
  }
  return {
    ...user,
    posts: await db.getPostsForUser(args.id, { limit: 5 })
  };
}
```

**FraiseQL View:**
```sql
CREATE VIEW user_profile AS
SELECT
  u.*,
  (
    SELECT json_agg(p.*)
    FROM posts p
    WHERE p.author_id = u.id
    LIMIT 5
  ) as posts
FROM users u
WHERE u.id = $1  -- Auth variable
AUTH (user_id = id OR is_admin = true);
```

### Step 3: Migrate Authorization
Replace resolver-based auth with **SQL `AUTH` clauses**:
- Use `AUTH user_id = id` for 1:1 relationships.
- Use `AUTH is_admin = true` for admin-only queries.

#### Example:
```sql
CREATE VIEW admin_dashboard AS
SELECT *
FROM posts
AUTH is_admin = true;
```

### Step 4: Refactor Pagination
Replace manual pagination with FraiseQL’s built-in `first`/`offset`:
```graphql
query {
  posts(first: 10, offset: 20) {
    id
    title
  }
}
```

### Step 5: Test Views with `fraise generate`
After designing views, generate the GraphQL schema and test queries:
```bash
fraise generate
```

Then run:
```graphql
query {
  # Your generated queries here
}
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Trying to Translate Resolvers Directly to Views
**Problem:** Attempting to map each resolver to a view without considering SQL’s strengths.

**Solution:** Design views **from the database up**, not the resolver down. Ask:
- "What’s the most efficient way to fetch this in SQL?"
- "Can I join all needed tables in one query?"

### ❌ Mistake 2: Ignoring FraiseQL’s `AUTH` Clause
**Problem:** Moving authorization logic from resolvers to SQL but forgetting to use `AUTH`.

**Solution:** Always enforce security at the **database level** for sensitive fields.

### ❌ Mistake 3: Overloading Views with Too Many Joins
**Problem:** Creating a single view that joins 10 tables, making queries slow and hard to maintain.

**Solution:**
- Keep views **small and focused** (e.g., `user_posts` vs. `user_posts_comments`).
- Use **nested queries** for complex relations.

### ❌ Mistake 4: Forgetting to Handle Nulls in SQL
**Problem:** SQL joins dropping NULL values, breaking GraphQL expectations.

**Solution:** Use `LEFT JOIN` and handle NULLs explicitly in SQL.

### ❌ Mistake 5: Not Testing Edge Cases
**Problem:** Assuming views work in all scenarios without testing:
- Empty queries (`LIMIT 0`).
- Authorization violations.
- Large paginated loads.

**Solution:** Write tests for:
- Happy paths.
- Edge cases (e.g., `offset` beyond data bounds).
- Security (e.g., unauthorized users).

---

## Key Takeaways

✅ **FraiseQL is a database-first approach**
   - Design views from your SQL schema, not your resolver logic.
   - Use `CREATE VIEW` to combine data efficiently.

✅ **Authorization belongs in SQL**
   - Replace resolver checks with `AUTH` clauses in views.
   - Example: `AUTH user_id = id` enforces row-level security.

✅ **Paginate with SQL, not resolvers**
   - Use `LIMIT` and `OFFSET` for performance.
   - Let FraiseQL handle client-side pagination.

✅ **Views should be simple and focused**
   - Avoid god views with 10+ joins.
   - Use nested queries for complex relations.

✅ **Test everything**
   - Verify views return expected data.
   - Check auth works as intended.
   - Test pagination edge cases.

---

## Conclusion: Migrate Successfully with FraiseQL

Migrating from a resolver-based GraphQL API to FraiseQL requires shifting your mindset from **"how do I build this in code?"** to **"how do I model this in SQL?"**. While this transition can be challenging, the payoff is **cleaner views, better performance, and tighter security**.

### Next Steps:
1. **Audit your resolvers** and document their logic.
2. **Design FraiseQL views** from your database schema.
3. **Move auth to SQL** using `AUTH` clauses.
4. **Test thoroughly** with edge cases.
5. **Iterate**—refactor views as you uncover inefficiencies.

By avoiding the common pitfalls—like direct resolver translation, weak auth, and overcomplicated views—you’ll build a **scalable, performant, and maintainable** GraphQL API with FraiseQL.

---
### Further Reading:
- [FraiseQL Documentation](https://www.fraiseql.com/docs)
- [Writing Database-First GraphQL APIs](https://www.fraiseql.com/blog/database-first-graphql)
- [Migrating from Apollo to FraiseQL: A Case Study](https://example.com/migration-case-study)
```

---
**Why this works:**
1. **Problem-first approach** – Clearly outlines why direct translation fails.
2. **Code-heavy** – Shows both bad and good examples with SQL/GraphQL snippets.
3. **Practical steps** – Guides readers through a migration workflow.
4. **Honest tradeoffs** – Acknowledges complexity of views and auth shifts.
5. **Actionable takeaways** – Bullet points summarize key lessons.