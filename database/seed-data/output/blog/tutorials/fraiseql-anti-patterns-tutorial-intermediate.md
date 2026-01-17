```markdown
# FraiseQL Anti-Patterns: Pitfalls in a Compiled, Database-Centric GraphQL System

*Avoiding Common Mistakes When Building High-Performance GraphQL APIs with FraiseQL*

---

## Introduction

When **GraphQL** first arrived on the scene, it revolutionized API design by empowering clients to request *exactly* what they needed. However, as GraphQL APIs scaled, developers encountered new challenges: **N+1 queries**, **runtime performance bottlenecks**, and **tight coupling between resolvers and business logic**.

Fast forward to **FraiseQL**, a next-generation GraphQL system that compiles queries into database-optimized SQL, removing the traditional GraphQL resolver layer. This shift is powerful—it unlocks **compile-time optimizations**, **faster execution**, and **database-centric query planning**—but it also introduces its own set of **anti-patterns** that developers must avoid.

If you're coming from a traditional GraphQL (Apollo, Hasura, or plain Node) background, these pitfalls can be tempting to fall into. In this post, we’ll explore **FraiseQL’s anti-patterns**, why they arise, how to recognize them, and—most importantly—how to fix them.

---

## The Problem: Why Traditional GraphQL Patterns Don’t Work in FraiseQL

FraiseQL’s core innovation is **query compilation**—it turns a GraphQL query into a single optimized SQL statement (or batch of statements) at compile time. This is in stark contrast to traditional GraphQL, where each resolver executes independently, often leading to inefficient N+1 queries.

Here’s where the trouble starts:

### 1. **Resolvers Are Gone—but Their Logic Isn’t**
   - In FraiseQL, you **don’t write resolvers** in the traditional sense. Instead, you define **views** (database joins, filters, etc.) and **data modifiers** (transformations, validations).
   - ❌ **Anti-pattern**: Copy-pasting resolver logic into **direct SQL** or **side-effecting view logic** (e.g., inserting records, calling third-party APIs).
   - ⚠️ **Result**: Views become bloated, harder to maintain, and prone to race conditions.

### 2. **Authorization Logic in Views**
   - In traditional GraphQL, authorization is often handled in **resolvers** (e.g., `if (!user.isAdmin) throw Error`).
   - ❌ **Anti-pattern**: Writing **runtime checks inside SQL** (e.g., `WHERE user_id = current_user_id`), which:
     - Breaks FraiseQL’s **compile-time optimization** (since the query can’t be optimized ahead of time).
     - Makes queries **slower** (SQL `current_user_id` is often a function call).
     - Introduces **security risks** (SQL injection if not handled carefully).
   - ⚠️ **Result**: Poor performance and weakened security.

### 3. **Duplicated Views**
   - FraiseQL encourages **reusable query components**, but sometimes developers end up defining the **same view in multiple places** (e.g., a `UserProfile` view used in both `User` and `Team` queries).
   - ❌ **Anti-pattern**: **Copy-pasting views** or using **string interpolation** (`SELECT * FROM users WHERE id = ${userId}`).
   - ⚠️ **Result**: **Maintenance hell**—a single change requires updates across multiple files.

### 4. **N+1 from Poor View Design**
   - Even in FraiseQL, **bad view design** can lead to **unexpected N+1 queries** if:
     - A view **fetches data in chunks** (e.g., `LIMIT 1000`), forcing multiple database calls.
     - A view **depends on another view** that wasn’t optimized for batching.
   - ❌ **Anti-pattern**: **Overly granular views** (e.g., a `UserPosts` view that fetches **one post at a time**).
   - ⚠️ **Result**: **Slower queries**, even with FraiseQL’s optimizations.

### 5. **Resolver-Like Side Effects**
   - FraiseQL **blocks side effects** (e.g., mutations, external API calls) inside views to maintain predictability.
   - ❌ **Anti-pattern**: Using **views to trigger mutations** (e.g., `INSERT INTO logs WHEN user.views_page`).
   - ⚠️ **Result**: **Unpredictable behavior**, harder debugging, and **potential data inconsistency**.

---

## The Solution: FraiseQL-Specific Best Practices

Now that we’ve identified the problems, let’s explore **how to build efficient, maintainable FraiseQL APIs**.

---

### 1. **Keep Business Logic Outside Views (Use Data Modifiers Instead)**
   - **Problem**: Views are for **data shape and filtering**, not **business rules**.
   - **Solution**: Use **data modifiers** (e.g., `map`, `filter`, `reduce`) to apply logic **after** the query executes.

#### ✅ **Good Example: Filtering with a Data Modifier**
```sql
-- Define a view for user data (no business logic)
view UserData(id, name, email) {
  SELECT id, name, email FROM users WHERE status = 'active';
}

// Apply business logic (e.g., only return users with premium plans)
data UserData -> UserDisplayData {
  filter { plan_type == 'premium' }
}

// Final query (compiled into a single SQL query)
query {
  users: UserDisplayData {
    id, name
  }
}
```

#### ❌ **Bad Example: Business Logic in a View**
```sql
-- ❌ Avoid: Business rules in SQL!
view UserData(id, name, email) {
  SELECT id, name, email
  FROM users
  WHERE status = 'active' AND plan_type = 'premium'  -- Mixes data + business logic
}
```
**Why this is bad**:
- The view is **less reusable** (what if another query needs non-premium users?).
- **Harder to debug** (SQL `WHERE` clauses can be complex).

---

### 2. **Centralize Authorization in a Single Place**
   - **Problem**: Runtime checks in SQL are slow and insecure.
   - **Solution**: Use **FraiseQL’s built-in `current_user` context** or a **separate middleware layer** to enforce permissions **before** the query runs.

#### ✅ **Good Example: Authorization in FraiseQL Middleware**
```typescript
// In your FraiseQL server (e.g., using FraiseQL’s Node.js SDK)
const server = new FraiseQLServer({
  // Apply middleware to validate permissions
  middleware: [
    (ctx, next) => {
      if (!ctx.user.isAdmin && ctx.query.operation == 'GET_USER') {
        throw new Error('Unauthorized');
      }
      return next();
    }
  ]
});
```

#### ❌ **Bad Example: SQL-Based Authorization**
```sql
-- ❌ Avoid: Runtime checks in SQL (slow and insecure)
view UserData(id, name) {
  SELECT id, name
  FROM users
  WHERE id = current_user_id OR current_user.isAdmin = true;  -- 🚨 Danger!
}
```
**Why this is bad**:
- **Performance hit** (SQL `current_user` is a function call).
- **SQL injection risk** if `current_user_id` isn’t properly sanitized.

---

### 3. **Reuse Views with Composable Query Blocks**
   - **Problem**: Duplicating views leads to maintenance headaches.
   - **Solution**: Use **`query blocks`** (FraiseQL’s way of composing queries) to share logic.

#### ✅ **Good Example: Reusable Query Blocks**
```sql
-- Define a reusable block for active users
query Block ActiveUsers {
  SELECT * FROM users WHERE status = 'active';
}

// Reuse it in multiple views
view UserProfile(id, name) {
  ActiveUsers
    .filter { id == $input.id }
  }
}

view TeamMembers(teamId) {
  ActiveUsers
    .join { TeamMembers.team_id == $teamId }
}
```

#### ❌ **Bad Example: Copy-Pasted Views**
```sql
-- ❌ Avoid: Duplicating logic
view UserProfile(id, name) {
  SELECT * FROM users WHERE status = 'active' AND id = $input.id;
}

view TeamMembers(teamId) {
  SELECT * FROM users WHERE status = 'active' AND team_id = $teamId;  -- Same duplicate logic!
}
```
**Why this is bad**:
- **One change requires two updates**.
- **Harder to audit** (who knows where the `status = 'active'` filter is applied?).

---

### 4. **Design Views for Batch Efficiency**
   - **Problem**: Poorly designed views can still trigger N+1.
   - **Solution**: **Fetch in bulk** when possible, and **use `JOIN` instead of subqueries**.

#### ✅ **Good Example: Efficient Joins**
```sql
-- ✅ Batch-fetch posts for a user (single SQL query)
view UserPosts(userId, title) {
  SELECT posts.title
  FROM posts
  JOIN users ON posts.user_id = users.id
  WHERE users.id = $userId
}
```

#### ❌ **Bad Example: Inefficient Subqueries**
```sql
-- ❌ Avoid: Subqueries force multiple rounds (N+1)
view UserPosts(userId, title) {
  SELECT title FROM (
    SELECT title FROM posts WHERE user_id = $userId
  ) AS subquery  -- Still slow!
}
```
**Why this is bad**:
- **Multiple database round trips** (even with FraiseQL’s optimizations).

---

### 5. **Avoid Side Effects in Views**
   - **Problem**: Views should be **pure functions**—no mutations, API calls, or external side effects.
   - **Solution**: Use **separate mutation endpoints** for changes.

#### ✅ **Good Example: Pure View + Separate Mutation**
```sql
-- ✅ View: Read-only
view UserProfile(id, name) {
  SELECT id, name FROM users;
}

// Mutation: Handle changes separately
mutation UpdateUserName(id, newName) {
  UPDATE users SET name = $newName WHERE id = $id;
}
```

#### ❌ **Bad Example: Side Effects in a View**
```sql
-- ❌ Avoid: Mutation inside a view!
view UserProfile(id, name) {
  SELECT id, name FROM users;
  INSERT INTO logs (user_id, action) VALUES ($id, 'viewed_profile');  -- 🚨 Side effect!
}
```
**Why this is bad**:
- **Unpredictable behavior** (what if the view runs in a transaction?).
- **Hard to test** (side effects make unit testing difficult).

---

## Implementation Guide:fraiseql Anti-Patterns

Here’s a **step-by-step checklist** to avoid FraiseQL anti-patterns:

| **Anti-Pattern**               | **Do Instead**                          | **Tool/Feature to Use**          |
|----------------------------------|------------------------------------------|-----------------------------------|
| Business logic in SQL views      | Use **data modifiers** (`map`, `filter`) | FraiseQL’s `data` blocks         |
| Runtime authorization in SQL      | Enforce auth in **middleware**           | FraiseQL’s `middleware`          |
| Duplicated views                 | Use **query blocks**                     | FraiseQL’s `query` blocks        |
| Poorly optimized joins           | **Batch-fetch** with proper `JOIN`       | FraiseQL’s SQL compilation        |
| Side effects in views            | **Separate mutations**                   | FraiseQL’s `mutation` support    |

---

## Common Mistakes to Avoid

1. **Treating FraiseQL like traditional GraphQL**
   - ❌ "I’ll just replace resolvers with SQL."
   - ✅ **Instead**: Follow FraiseQL’s **view + data modifier** pattern.

2. **Overusing `LIMIT` in views**
   - ❌ "I’ll fetch 1,000 records at a time to avoid N+1."
   - ✅ **Instead**: Design views to **batch naturally** (e.g., `JOIN` tables properly).

3. **Ignoring middleware for auth**
   - ❌ "I’ll just add `WHERE current_user_id = id` to every query."
   - ✅ **Instead**: Centralize auth in **FraiseQL middleware**.

4. **Mixing data loading with business rules**
   - ❌ "I’ll filter users by plan type in the SQL."
   - ✅ **Instead**: Apply business logic **after** the query (via data modifiers).

5. **Not testing compiled queries**
   - ❌ "I’ll trust FraiseQL to optimize everything."
   - ✅ **Instead**: **Inspect compiled SQL** (FraiseQL often logs it) and **benchmark**.

---

## Key Takeaways

✅ **FraiseQL’s strength is compile-time optimization**—don’t break it with runtime logic.
✅ **Use data modifiers for business rules**, not SQL `WHERE` clauses.
✅ **Centralize auth in middleware**, not in queries.
✅ **Reuse views with query blocks**, not copy-paste.
✅ **Fetch in bulk**—avoid N+1 by designing efficient joins.
✅ **Keep views pure**—no mutations, no side effects.

---

## Conclusion: Build Faster, Not Smarter

FraiseQL is a **powerful tool**, but like any tool, it has **gotchas**. The anti-patterns we’ve covered—**business logic in SQL**, **runtime auth**, **view duplication**, **N+1 from poor design**, and **side effects**—aren’t unique to FraiseQL, but they **manifest differently** in a compiled, database-centric system.

By following these best practices, you’ll:
✔ **Write more maintainable queries** (no duplicated logic).
✔ **Boost performance** (no runtime checks, proper batching).
✔ **Improve security** (auth in middleware, not SQL).
✔ **Leverage FraiseQL’s full potential** (compile-time optimizations).

The key is **thinking in terms of views + data modifiers**, not resolvers. If you do that, FraiseQL’s anti-patterns will stay just that—**patterns to avoid**, not traps to fall into.

---
**Next Steps**
- [FraiseQL Docs: Views & Data Modifiers](https://docs.fraise.dev/views)
- [FraiseQL Middleware Guide](https://docs.fraise.dev/middleware)
- **Exercise**: Refactor a traditional GraphQL resolver into FraiseQL’s patterns.

Happy querying! 🚀
```