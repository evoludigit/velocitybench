```markdown
---
title: "FraiseQL Anti-Patterns: How Not to Build Scalable Database-Centric APIs"
date: YYYY-MM-DD
author: Your Name
tags: ["database", "FraiseQL", "API Design", "GraphQL", "Backend Patterns"]
---

# FraiseQL Anti-Patterns: How Not to Build Scalable Database-Centric APIs

FraiseQL is a database-centric query language designed to push as much responsibility to the database as possible. Unlike traditional GraphQL—where resolvers handle data fetching, authorization, and business logic—FraiseQL compiles queries into optimized database operations, blurring the line between application and database layers. This shift introduces unique pitfalls, especially for developers accustomed to GraphQL or REST. In this post, we’ll dissect **FraiseQL anti-patterns**: common mistakes that undermine scalability, performance, and maintainability. We’ll explore why traditional patterns fail here, how to avoid them, and provide code-first examples.

---

## The Problem: Why Traditional Patterns Fail in FraiseQL

FraiseQL’s strength—offloading logic to the database—becomes a weakness if misapplied. Here’s why:

1. **Resolver Overuse**: In GraphQL, resolvers handle dynamic data fetching, but FraiseQL’s compile-time nature makes resolvers unnecessary for simple queries. Overusing them reintroduces application logic, defeating FraiseQL’s purpose.
2. **Runtime Authorization**: FraiseQL prefers declarative security (e.g., row-level security in PostgreSQL), but runtime checks (like in resolvers) can’t leverage the database’s optimized access patterns.
3. **View Duplication**: FraiseQL encourages reusable database views, but duplicating them across schemas or applications leads to inconsistencies and maintenance overhead.
4. **N+1 Queries from Poor View Design**: Poorly structured views can force the database to execute redundant queries, negating FraiseQL’s performance gains.
5. **Resolver Side Effects**: FraiseQL queries are pure; side effects (e.g., caching, event triggering) outside the database break this principle.

These anti-patterns stem from treating FraiseQL like GraphQL—ignoring its database-first philosophy. Below, we’ll refactor each issue into scalable solutions.

---

## The Solution: Database-Centric Alternatives

### 1. Avoid Resolver Overuse: Push Logic to Views and Functions
**Problem**: Wrapping FraiseQL queries in resolvers for "extended logic" defeats the purpose—application code becomes the bottleneck.
**Solution**: Use SQL views, stored procedures, or FraiseQL’s `function` keyword for reusable logic.

#### Bad (Resolver-Heavy):
```sql
-- fraiseql.sdl
type Post @fractional { id: ID! text: String! }
type Query {
  posts: [Post]
}

# Resolver (pseudo-Code)
def resolvePosts(parent, args):
  # Too much application logic here!
  query = "SELECT id, text FROM posts WHERE author_id = %s" % user_id
  return db.query(query)
```

#### Good (Database Logic):
```sql
-- Create a view that encapsulates filtering
CREATE VIEW user_posts AS
  SELECT id, text
  FROM posts
  WHERE author_id = current_setting('app.current_user_id')::int;

# Query in FraiseQL
type Query {
  posts: [Post] @fractional(view: "user_posts")
}
```

**Tradeoff**: Views require schema migrations, but they’re immutable and faster than resolvers.

---

### 2. Replace Runtime Checks with Database Security
**Problem**: Runtime authorization (e.g., checking permissions in resolvers) can’t scale with FraiseQL’s parallel queries.
**Solution**: Use PostgreSQL’s row-level security (RLS) or FraiseQL’s `@fractional(policy: "`{current_user_id}`")`.

#### Bad (Runtime Check):
```sql
type Post {
  id: ID!
  text: String!
  author: User! @fractional
}
# Pseudo-resolver:
def resolvePost(parent, args):
  if not user_has_permission_to_read_post(parent.id):
    raise Error("Unauthorized")
  return parent
```

#### Good (RLS + FraiseQL):
```sql
-- Enable RLS on the posts table
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_post_policy ON posts
  USING (author_id = current_setting('app.current_user_id')::int);

# FraiseQL query (auto-secured)
type Query {
  posts: [Post] @fractional
}
```

**Tradeoff**: RLS requires careful policy design but scales horizontally.

---

### 3. Consolidate Views to Avoid Duplication
**Problem**: Copying views across schemas or applications leads to divergence.
**Solution**: Centralize views in a shared database layer.

#### Bad (Duplicate Views):
```sql
-- Schema A
CREATE VIEW user_posts AS SELECT ...;

-- Schema B (copy-pasted)
CREATE VIEW user_posts AS SELECT ...;
```

#### Good (Single Source of Truth):
```sql
-- Shared database layer (e.g., PostgreSQL extension)
CREATE EXTENSION IF NOT EXISTS shared_views;

-- Extend the view to all schema users
CREATE VIEW shared.user_posts AS SELECT ...;

-- Grant access
GRANT USAGE ON SCHEMA shared TO app_user;
```

**Tooling Tip**: Use tools like [Flyway](https://flywaydb.org/) to sync views across environments.

---

### 4. Design Views for N+1-Free Querying
**Problem**: Poorly structured views force FraiseQL to issue redundant queries (e.g., loading `Post` + `User` separately).
**Solution**: Denormalize views to include relationships.

#### Bad (N+1 Risk):
```sql
-- View limits to `Post` only
CREATE VIEW posts AS SELECT id, text FROM posts;

# FraiseQL query
type Query {
  posts: [Post] @fractional
  # Resolver adds `author` in app code → N+1!
  post(id: ID!): Post!
}
```

#### Good (Denormalized View):
```sql
CREATE VIEW posts_with_authors AS
  SELECT p.id, p.text, u.username
  FROM posts p
  JOIN users u ON p.author_id = u.id;

type Query {
  posts: [PostWithAuthor] @fractional(view: "posts_with_authors")
}
```

**Tradeoff**: Denormalization increases view size but reduces network roundtrips.

---

### 5. Replace Resolver Side Effects with Database Triggers
**Problem**: Resolvers for side effects (e.g., caching, notifications) break FraiseQL’s pure-query model.
**Solution**: Use database triggers or async message queues.

#### Bad (Side Effect in Resolver):
```sql
type Post {
  id: ID!
  text: String!
  # Resolver sends event
  @fractional
  def onPostCreated(_parent, _args):
    send_notification(parent.id)
}
```

#### Good (Trigger + Queue):
```sql
-- PostgreSQL trigger
CREATE OR REPLACE FUNCTION send_post_notification()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('post_created', row_to_json(NEW));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER post_created_trigger
AFTER INSERT ON posts
FOR EACH ROW EXECUTE FUNCTION send_post_notification();

# FraiseQL (pure query)
type Mutation {
  createPost(input: PostInput!): Post!
}
```

**Tooling Tip**: Use [Debezium](https://debezium.io/) for CDC-based event streaming.

---

## Implementation Guide: Checklist for FraiseQL Projects

1. **Audit Resolver Usage**:
   - Replace resolvers with views for data fetching.
   - Move logic to stored procedures if it’s too complex for SQL.

2. **Adopt PostgreSQL Security**:
   - Enable RLS on tables and define policies.
   - Use FraiseQL’s `@fractional(policy: "...")` for dynamic policies.

3. **Standardize Views**:
   - Create a `shared` schema for reusable views.
   - Use versioning (e.g., `view_v1`) for breaking changes.

4. **Denormalize Early**:
   - Include relationships in views to avoid N+1.
   - Profile queries with `EXPLAIN ANALYZE` to spot inefficiencies.

5. **Externalize Side Effects**:
   - Replace resolver events with triggers or async queues.
   - Document side effects in your schema comments.

---

## Common Mistakes to Avoid

1. **Treating FraiseQL Like GraphQL**:
   - ❌: Adding resolvers for "complex logic."
   - ✅: Push logic into the database with views/functions.

2. **Overusing `@fractional` on Tables**:
   - ❌: Querying raw tables without views → poor performance.
   - ✅: Always wrap tables in views for consistency.

3. **Ignoring RLS**:
   - ❌: Handling security in resolvers.
   - ✅: Define policies in the database and let FraiseQL enforce them.

4. **Copy-Pasting Views**:
   - ❌: Duplicating views across schemas.
   - ✅: Centralize in a shared layer and sync with tools like Flyway.

5. **Denormalizing Blindly**:
   - ❌: Adding all columns to a view for "ease of use."
   - ✅: Denormalize only what’s needed to avoid bloat.

---

## Key Takeaways

- **Offload logic to the database**: Views, procedures, and RLS are your allies.
- **Embrace immutability**: Views should be static; avoid dynamic queries in FraiseQL.
- **Design for parallelism**: N+1 issues are solved at the database level.
- **Security at the source**: RLS is cheaper than runtime checks at scale.
- **Document your schema**: Comments are critical when logic lives in SQL.

---

## Conclusion

FraiseQL’s database-centric approach rewards those who treat the database as a first-class citizen. Avoiding its anti-patterns—like resolver overuse or runtime authorization—requires a mindset shift from traditional GraphQL or REST. By pushing logic to the database, standardizing views, and leveraging PostgreSQL’s features, you’ll build APIs that scale seamlessly with your data.

Start small: Refactor one resolver-heavy query into a view today. The payoff in performance and maintainability will be immediate. For further reading, explore FraiseQL’s [official docs](https://www.fraiseql.org/) and PostgreSQL’s [RLS documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).

Happy compiling!
```