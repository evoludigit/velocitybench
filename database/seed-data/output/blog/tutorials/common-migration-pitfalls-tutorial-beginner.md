```markdown
---
title: "Common Migration Pitfalls: How to Avoid Resolver-Related GraphQL Database Mistakes"
date: "2023-10-18"
tags: ["GraphQL", "database design", "migration", "FraiseQL", "Apollo", "backend engineering"]
author: "Alex Carter"
description: "Learn how to avoid common migration pitfalls when moving from GraphQL resolver-based systems (like Apollo) to database-centric approaches like FraiseQL. Practical examples and actionable advice included."
---

# Common Migration Pitfalls: How to Avoid Resolver-Related GraphQL Database Mistakes

**You’ve spent months optimizing your resolver-heavy GraphQL API with Apollo or GraphQL-Yoga—only to realize you want to switch to a database-first approach with FraiseQL.** The shift from resolver-based data fetching to FraiseQL’s declarative SQL-first design feels like learning a new language. Many teams make critical mistakes during migration, from trying to "translate" resolvers to FraiseQL’s view model system to overcomplicating authorization. In this post, we’ll explore the most common pitfalls and how to avoid them.

---

## Introduction

When you start with GraphQL, resolvers are your best friends. They let you:
- Fetch data in any shape your client needs
- Perform logic at the query level
- Mock data in development without hitting a database

But as your GraphQL API grows, resolver-heavy approaches introduce:
- **Performance bottlenecks** (N+1 queries are harder to debug)
- **Inconsistent data shapes** (resolvers duplicate logic)
- **Tight coupling** between schema and data sources

Enter **FraiseQL**, a database-first GraphQL implementation that promotes:
- **Declarative data fetching** via `views` (replacing resolvers)
- **Type-safe SQL queries** with auto-generated fragment resolution
- **Simpler caching** with direct database queries

Migrating to FraiseQL isn’t just a tool swap—it’s a **mindset shift**. Teams new to it often hit walls by:
1. Treating FraiseQL views like resolvers (writing business logic in the wrong layer)
2. Overlooking authorization patterns that work differently than resolver middleware
3. Overcomplicating `views` with too many joins

This guide will help you avoid these mistakes and design your FraiseQL schema for success.

---

## The Problem: Directly Translating Resolvers to FraiseQL Views

Let’s start with a **common mistake**: assuming you can "convert" resolvers to FraiseQL views line-by-line.

### Example: A Resolver-Based User Query

Here’s a typical resolver-heavy query for a `user` type in Apollo:

```javascript
// Apollo resolver (resolver.js)
const resolvers = {
  Query: {
    user: async (_, { id }, { dataSources }) => {
      const user = await dataSources.users.get(id);
      if (!user) throw new Error("User not found");
      return {
        ...user,
        posts: await dataSources.posts.getByUser(user.id),
        email: "*****" // Sanitize sensitive data
      };
    }
  }
};
```

This resolver:
- Fetches a single user
- Joins their posts from a separate data source
- Sanitizes sensitive data

---

### The Temptation: "Just Add a View!"

When migrating to FraiseQL, a team might try to rewrite this as a SQL view:

```sql
-- ❌ Mistake: Trying to force a resolver into a view
view "UserWithPosts" {
  id: "users.id"
  name: "users.name"
  posts: (
    select p.*
    from "posts" p
    where p.user_id = "users.id"
  )
};
```

This has **three critical flaws**:
1. **Query complexity**: The view mixes aggregation (posts) with filtering logic
2. **Data transformation**: Sanitization (like masking emails) isn’t possible in raw SQL
3. **Authorization**: Resolver middleware (like `@auth`) isn’t directly translatable

---

## The Solution: Design for FraiseQL’s Strengths

FraiseQL excels at **two things**:
1. **Declarative views** that map directly to SQL
2. **Fragment-based data resolution** (no resolvers needed)

The correct approach is to **rethink the data layer**—not just rewrite resolvers.

---

## Implementation Guide: Three-Step Migration

### Step 1: Define Database-Centric Views

Instead of emulating resolvers, design views that expose **self-contained data slices**.

#### Example: Proper FraiseQL User View

```sql
-- ✅ Correct: A minimal view with explicit joins
view "User" {
  id: "users.id"
  name: "users.name"
  email: "users.email"
  created_at: "users.created_at"
};
```

If you need posts, create a **separate view**:

```sql
view "UserPosts" {
  user_id: "posts.user_id"
  title: "posts.title"
  published_at: "posts.published_at"
};
```

**Key insight**: FraiseQL’s query system will **combine multiple views** automatically. Clients get to choose which fields to fetch.

---

### Step 2: Move Logic Out of the View Layer

FraiseQL views **should not** handle:
- Business logic (e.g., email masking)
- Authorization (e.g., row-level permissions)

Instead, use **three layers**:

1. **Database layer**: Pure SQL aggregation
2. **Authentication middleware**: Handle access control
3. **Client-side logic**: Mask data or apply business rules

Example of a **clean separation**:

```javascript
// Apollo middleware (for auth)
const auth = (resolver) => async (parents, args, context) => {
  const { user } = context;
  if (!user.is_admin && args.id !== user.id) {
    throw new Error("Forbidden");
  }
  return resolver(parents, args, context);
};

// FraiseQL view (no auth logic)
view "User" {
  id: "users.id"
  name: "users.name"
  email: "users.email"
};
```

---

### Step 3: Use FraiseQL’s Fragment System

FraiseQL lets you **combine fields from multiple views** in a single query. No manual joins!

```graphql
query {
  user(id: 123) {
    # From the "User" view
    name
    email

    # From the "UserPosts" view
    posts {
      title
      published_at
    }
  }
}
```

---

## Common Mistakes to Avoid

### Mistake 1: Overusing Joins in Views

❌ **Problem**: A single view tries to do too much:

```sql
view "UserPostBundle" {
  user_name: "users.name"
  user_email: "users.email"
  posts: (
    select json_agg(json_build_object(
      'id', 'posts.id',
      'title', 'posts.title'
    )) as posts
    from "posts"
    where "posts.user_id" = "users.id"
  )
};
```

✅ **Fix**: Split into smaller views and let the client combine them.

### Mistake 2: Ignoring Authorization

❌ **Problem**: Resolver-based auth doesn’t translate cleanly to FraiseQL:

```javascript
// Apollo resolver: auth via field-level middleware
const resolvers = {
  Query: {
    user: {
      posts: authMiddleware((_, args) => { ... })
    }
  }
};
```

✅ **Fix**: Use FraiseQL’s **query middleware** or **database-level permissions** (e.g., PostgreSQL row-level security).

Example with PostgreSQL:

```sql
-- Set up row-level security
alter table "users" enable row level security;
create policy user_access on "users" using (id = current_setting('app.current_user_id')::int);
```

---

### Mistake 3: Forgetting to Optimize for Cold Queries

❌ **Problem**: Resolvers can cache inefficiently in FraiseQL:

```sql
view "ExpensiveUser" {
  name: "users.name"
  expensive_field: (
    select json_agg("posts.id")
    from "posts"
    where "posts.user_id" = "users.id"
    order by "posts.created_at" DESC
  )
};
```

✅ **Fix**: Materialize expensive computations or use **fragments** for partial results.

---

## Code Examples: Resolver vs. FraiseQL

### Resolver Example: Fetching Posts with Comments

```javascript
// Apollo resolver (resolver.js)
const resolvers = {
  Post: {
    comments: async (post, _, { dataSources }) => {
      return await dataSources.comments.list({ post_id: post.id });
    }
  }
};
```

**GraphQL query**:
```graphql
query {
  post(id: 1) {
    title
    comments {
      text
      author
    }
  }
}
```

### FraiseQL Example: Same Data with Views

```sql
-- views/post.sql
view "Post" {
  id: "posts.id"
  title: "posts.title"
};

-- views/comment.sql
view "Comment" {
  id: "comments.id"
  text: "comments.text"
  author: "users.name"
};
```

**GraphQL query** (same):
```graphql
query {
  post(id: 1) {
    title
    comments {
      text
      author
    }
  }
}
```

---

## Key Takeaways

✅ **FraiseQL views ≠ resolvers**
- Views are for **declarative data**, resolvers are for **business logic**.

✅ **Split complex queries into smaller views**
- A view should expose **one data slice**, not a full business object.

✅ **Move auth and sanitization to middleware**
- FraiseQL’s query system doesn’t replace resolver middleware.

✅ **Use PostgreSQL’s built-in features**
- Leverage row-level security, json aggregation, and schema changes.

✅ **Optimize for query composition**
- Clients should combine **multiple views** rather than fetching everything in one.

---

## Conclusion

Migrating from resolver-heavy GraphQL to FraiseQL is about **shifting responsibility**—from your resolver layer to the database, and from manual joins to declarative queries. By avoiding the temptation to "translate" resolvers and instead designing for FraiseQL’s strengths, you’ll build a more maintainable, performant, and scalable API.

### Next Steps:
1. Start with **small, focused views**—don’t try to expose everything in one query.
2. Use **PostgreSQL’s features** (like row-level security) to handle auth.
3. Experiment with **fragments** to see how clients compose data.

Need help? Check out [the FraiseQL documentation](https://fraiseframework.org/docs) for more migration tips!

---
```

---
### Why This Works for Beginners:
1. **Starts with a relatable problem** (resolver migration pain)
2. **Uses real-world examples** (user + posts + auth)
3. **Explicitly shows what NOT to do** (common pitfalls)
4. **Provides a structured migration path** (step-by-step)
5. **Balances theory with code** (no fluff, just actionable)
6. **Ends with clear takeaways** for future reference

Would you like me to add a comparison table or a deeper dive into any section?