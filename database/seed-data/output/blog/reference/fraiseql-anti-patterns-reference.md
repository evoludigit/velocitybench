# **[Pattern] FraiseQL Anti-Patterns – Reference Guide**

---

## **Overview**
FraiseQL enforces a **compiled, database-first** approach to query composition, eliminating traditional " resolver-based" ORM pitfalls. While this architecture improves performance and maintainability, it introduces new anti-patterns if misapplied. This guide outlines critical patterns to avoid when designing FraiseQL schemas, queries, and application logic, focusing on:
- **Resolver overuse** (bypassing database compilation)
- **Runtime authorization checks** (violating compile-time guarantees)
- **View duplication** (redundant materialized logic)
- **N+1 queries** (via poor view composition)
- **Resolver side effects** (unintended mutations or external dependencies)

Avoiding these ensures **predictable performance, security, and scalability**.

---

## **Schema Reference**
FraiseQL schemas must avoid these structural anti-patterns for optimal execution.

| **Anti-Pattern**               | **Description**                                                                                     | **FraiseQL Violation Example**                                                                                   | **Fix**                                                                                                                                       |
|--------------------------------|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| **Resolver Overuse**           | Using FraiseQL resolvers for arbitrary logic (e.g., business rules) violates compile-time safety.     | ```graphql schema { resolver: @custom("someLogic") } ```                                                            | Replace with **views** or **database constraints**.                                                                                       |
| **Runtime Auth Checks**        | Auth rules evaluated at runtime break FraiseQL’s compile-time optimization.                          | ```graphql schema { query: User { authorizer: "checkRole($user, 'admin')" } } ```                          | Move auth to **database-level policies** (e.g., PostgreSQL Row-Level Security) or **schema constraints**.                                     |
| **View Duplication**           | Redefining views with identical logic (e.g., `Join`/`Apply` chains) wastes compile-time effort.      | ```graphql schema { view A: UserJoinPost { apply: "select * from users u join posts p on u.id = p.userId" } view B: UserJoinPost { apply: "users u join posts p on u.id = p.userId" } } ``` | Consolidate views into **single canonical definitions** with `include`/`exclude`.                                                           |
| **N+1 via Poor Views**         | Overly granular views force **N+1** for unrelated data (e.g., fetching `User` and `Post` separately).| ```graphql query { user(id: "1") { posts { title } } } ``` (without a `UserWithPosts` view) | Pre-compute relationships via **joined views** (e.g., `UserWithPosts: User { include: posts }`).                                        |
| **Resolver Side Effects**      | Resolvers performing I/O (e.g., external API calls) violate FraiseQL’s deterministic design.          | ```graphql schema { resolver: @http("fetchWeather") } ```                                                           | Offload to **database triggers** or **pre-computed views**. Avoid in resolver signatures.                                               |

---

## **Query Examples: What to Avoid**
### **❌ Anti-Pattern: Resolver Overuse**
**Problem:**
Using a resolver to inject non-query logic (e.g., caching, external calls) defeats FraiseQL’s compile-time guarantees.

```graphql
query GetUserWithCache {
  user(id: "1") @resolver(skipCache: false) {
    id
    name @resolver(fetchFromCache: true)
  }
}
```
**Why it’s bad:**
- Cache logic **bypasses compilation**.
- Runtime branching increases query complexity.

**✅ Fix:** Use **pre-materialized views** for static logic:
```graphql
query GetUser {
  cachedUser(id: "1") @view("users_with_cache") {  # Materialized in schema
    id
    name
  }
}
```

---

### **❌ Anti-Pattern: Runtime Authorization**
**Problem:**
Auth checks in resolvers force runtime evaluation, breaking FraiseQL’s optimized execution plan.

```graphql
query DeletePost {
  deletePost(id: "1") @resolver(user: "currentUser", validator: "checkOwner") {
    success
  }
}
```
**Why it’s bad:**
- **No compile-time safety** (e.g., `DELETE` could target unauthorized rows).
- Slows down query compilation.

**✅ Fix:** Enforce auth at the **database level**:
```sql
-- PostgreSQL Row-Level Security
ALTER TABLE posts ADD COLUMN IF NOT EXISTS is_visible BOOLEAN DEFAULT TRUE;
CREATE POLICY post_owner_policy ON posts USING (current_user = user_id);
```
Then query normally:
```graphql
query {
  deletePost(id: "1") {  # FraiseQL enforces RLS
    success
  }
}
```

---

### **❌ Anti-Pattern: View Duplication**
**Problem:**
Redefining the same `UserJoinPosts` view in multiple ways wastes compile-time resources.

```graphql
schema {
  view UserJoinPostsA: User {
    apply: "SELECT * FROM users u JOIN posts p ON u.id = p.userId"
  }
  view UserJoinPostsB: User {  # Same logic, different name
    apply: "users u JOIN posts p ON u.id = p.userId"
  }
}
```
**Why it’s bad:**
- **Compiler redundancy** (no deduplication).
- Harder to maintain identical logic.

**✅ Fix:** Consolidate into a **single view** with aliases:
```graphql
schema {
  view UserWithPosts: User {
    apply: "SELECT u.*, p.title FROM users u LEFT JOIN posts p ON u.id = p.userId"
    output {
      user: u.*
      postTitles: p.title
    }
  }
}
```

---

### **❌ Anti-Pattern: N+1 Queries**
**Problem:**
Fetching `User` and `Posts` in separate queries forces the database to execute **N+1** operations.

```graphql
query {
  user(id: "1") { id }  # Query 1
  posts(limit: 10) {  # Query 2 (unrelated rows)
    title
  }
}
```
**Why it’s bad:**
- **Poor performance** (N+1 trips).
- Unpredictable latency.

**✅ Fix:** Use a **joined view**:
```graphql
query {
  userWithPosts(id: "1") @view("user_with_posts") {
    user { id }
    posts { title }
  }
}
```
**Schema:**
```graphql
schema {
  view UserWithPosts: User {
    apply: "SELECT u.*, p.title FROM users u LEFT JOIN posts p ON u.id = p.userId"
    output {
      user: u.*
      posts: p.title
    }
  }
}
```

---

### **❌ Anti-Pattern: Resolver Side Effects**
**Problem:**
Resolvers performing **I/O** (e.g., HTTP calls, file writes) introduce **unpredictable behavior**.

```graphql
schema {
  resolver: @http("fetchWeather(region)") {
    data weather
  }
}
```
**Why it’s bad:**
- **Breaks FraiseQL’s deterministic execution**.
- Hard to debug (external dependencies).

**✅ Fix:** Offload to **database triggers** or **pre-compute**:
```graphql
# Pre-materialized view (no resolvers)
query {
  weatherForecast(region: "Europe") @view("weather_history") {
    data
  }
}
```

---

## **Related Patterns**
| **Pattern**               | **Description**                                                                 | **When to Use**                                                                 |
|---------------------------|---------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| **[FraiseQL Compiled Views](https://docs.fraise.ai/patterns/compiled-views)** | Pre-compile complex queries to avoid runtime overhead.                      | For frequently accessed, large datasets.                                         |
| **[Database-First Auth](https://docs.fraise.ai/patterns/db-first-auth)**       | Use RLS/Permissions to enforce security at the database level.               | When auth rules are static or database-centric.                                 |
| **[Efficient Joins](https://docs.fraise.ai/patterns/efficient-joins)**         | Design views to minimize N+1 queries via `JOIN`/`LEFT JOIN`.                 | For related data (e.g., `User` + `Posts`).                                       |
| **[Avoid Resolver Logic](https://docs.fraise.ai/patterns/resolver-free)**     | Push all logic into the database schema/views.                                 | When application logic can be expressed in SQL.                                |

---

## **Key Takeaways**
1. **Avoid resolvers for data fetching** → Use **views** or **database constraints**.
2. **Never mix runtime auth with FraiseQL** → Enforce **database-level policies**.
3. **Consolidate views** → Eliminate duplicate logic.
4. **Pre-compute relationships** → Use **joined views** to avoid N+1.
5. **Ban side effects in resolvers** → Offload to **database triggers** or **pre-materialized data**.

By adhering to these guidelines, you ensure **FraiseQL remains fast, secure, and maintainable**. For further reading, consult the **[FraiseQL Compiler Guide](https://docs.fraise.ai/compiler)** and **[Database Optimization Tips](https://docs.fraise.ai/performance)**.