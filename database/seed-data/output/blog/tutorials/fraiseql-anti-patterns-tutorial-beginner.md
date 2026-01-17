```markdown
# Designing with FraiseQL: Anti-Patterns That'll Make You Cry (And How to Avoid Them)

## Introduction

If you’ve been building GraphQL APIs for a while, you’ve likely heard of **FraiseQL**—the open-source, query-compiled database-first GraphQL server that shines in scenarios where you need tight database coupling (like high-performance analytics or legacy system integration). Unlike traditional GraphQL servers that rely on resolvers, FraiseQL compiles your GraphQL queries into SQL (or your database’s native query language), optimizing for raw performance and reducing the overhead of runtime execution.

But here’s the catch: **FraiseQL’s simplicity can also trap you in anti-patterns that look innocent at first glance but grow into technical debt.** In this guide, we’ll explore five **FraiseQL anti-patterns**—missteps that are subtle but costly—and show you how to design around them. We’ll start with the core problem: why traditional GraphQL patterns fail in FraiseQL, then dive into practical solutions with code examples.

---

## The Problem: Traditional GraphQL Patterns Don’t Apply to FraiseQL

Traditional GraphQL servers (like Apollo or Hasura) rely on **resolvers**—custom JavaScript functions that fetch and transform data at runtime. Resolvers give you flexibility: you can modify data, handle authorization, or refetch data dynamically. But FraiseQL *compiles* your GraphQL queries into SQL before execution. This means:

1. **No resolver runtime**: FraiseQL executes queries as SQL, so logic that runs “between” the database and the client (like middleware, side-effect hooks, or complex transformations) becomes *impossible*.
2. **No dynamic authorization per-request**: While you can define *static* access rules (e.g., using FraiseQL’s `permission` system), runtime checks aren’t straightforward.
3. **No partial refetching**: If your query depends on cached data, you’ll need to adjust your design (e.g., use `fragments` and `update` operations).
4. **No lazy loading**: FraiseQL generates all SQL upfront, so lazy-loading `hasMany` relationships (e.g., `user.orders`) requires explicit design choices.

This isn’t a limitation of FraiseQL—it’s a deliberate tradeoff for performance. But if you blindly port a traditional GraphQL API to FraiseQL without adapting, you’ll hit walls that look like bugs but are actually architectural mismatches.

---

## The Solution: Designing for FraiseQL’s Strengths

FraiseQL thrives when you:
- **Push logic into the database** (or pre-compute it).
- **Use schema-first design** to ensure queries map cleanly to SQL.
- **Embrace static rules** rather than runtime logic.
- **Optimize for N+0** by designing views that fetch everything at once.

Let’s break down the key anti-patterns and how to avoid them.

---

## Anti-Pattern 1: Using Resolvers for Data Fetching

### The Problem
In traditional GraphQL, you might write a resolver like this:

```javascript
// User resolver (Apollo-style)
const resolvers = {
  User: {
    orders(user, _, { dataSources }) {
      return dataSources.userAPI.getOrdersByUser(user.id);
    },
  },
};
```

But in FraiseQL, resolvers don’t exist. If you try to fetch data outside the query’s root, you’ll get runtime errors or silent failures. Worse, FraiseQL *compiles* the entire query to SQL, so any ad-hoc logic here breaks the compilation.

### The Solution: Precompute or Use Database Views
Instead of fetching data in a resolver, **design your schema so all fields are directly queryable from the database**. For example:

```sql
-- Precompute orders for a user in the database (e.g., via a materialized view)
CREATE MATERIALIZED VIEW user_orders_view AS
  SELECT u.id AS user_id, o.id AS order_id
  FROM users u
  JOIN orders o ON u.id = o.user_id;
```

Then define your FraiseQL schema to reference this view:

```graphql
type User {
  id: ID!
  name: String!
  orders: [Order!]! @fraiseql(view: "user_orders_view")
}
```

### Why This Works
- The entire query (including `User.orders`) compiles to a single SQL query.
- No resolver runtime needed—FraiseQL handles the join.

---

## Anti-Pattern 2: Runtime Authorization in Resolvers

### The Problem
In traditional GraphQL, you might check permissions in a resolver:

```javascript
const resolvers = {
  User: {
    sensitiveData(user, _, { auth }) {
      if (!auth.isAdmin) throw new Error("Forbidden");
      return db.getSensitiveData(user.id);
    },
  },
};
```

But FraiseQL compiles queries to SQL *before* execution, so runtime checks like `auth.isAdmin` are impossible. You’ll either:
- Get a compilation error, or
- Have the query execute unchecked.

### The Solution: Use Schema Permissions or Row-Level Security
FraiseQL supports **static permissions** via the `@fraiseql` directive. For example:

```graphql
type User {
  id: ID!
  sensitiveData: String @fraiseql(permission: "adminOnly")
}
```

Then configure your database to enforce `adminOnly` at the SQL level (e.g., with PostgreSQL’s **Row-Level Security**):

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY admin_only_policy ON users
  FOR SELECT USING (admin = true);
```

Now, FraiseQL will compile queries like this:
```sql
SELECT * FROM users WHERE admin = true;
```

### Why This Works
- Permissions are enforced at the database level.
- No runtime checks needed—queries are compiled with filters applied.

---

## Anti-Pattern 3: View Duplication (The "Fragment Hell" Problem)

### The Problem
If you duplicate views (e.g., `user_profile_view`, `user_detail_view`, `user_settings_view`), you risk:
1. **Inconsistent data**: All three views might not sync if source tables change.
2. **Performance penalties**: Each view might fetch the same data redundantly.
3. **Schema complexity**: Managing duplicates becomes a chore.

In FraiseQL, a single `User` type should map to a single view or query. Duplicating it just leads to maintenance headaches.

### The Solution: Use a Single View with Modular Design
Design your schema to reuse views via **fragments** or **inheritance**. For example:

```graphql
type UserBase {
  id: ID!
  name: String!
  email: String!
}

type UserProfile @fraiseql(view: "user_profile_view") implements UserBase {
  profilePicture: String
}

type UserSettings @fraiseql(view: "user_settings_view") implements UserBase {
  darkMode: Boolean
}
```

Then, if your database schema changes (e.g., `name` moves to a `user` table), you only update one view.

### Why This Works
- **Single source of truth**: One view for `UserBase` fields.
- **Flexibility**: Extend with `UserProfile` or `UserSettings` as needed.

---

## Anti-Pattern 4: N+1 Queries from Poor View Design

### The Problem
In traditional GraphQL, N+1 queries often happen when resolvers fetch related data one-by-one:

```javascript
// Apollo resolver (bad)
const resolvers = {
  User: {
    orders(user) {
      return db.getOrdersByUser(user.id);
    },
  },
  Order: {
    items(order) {
      return db.getOrderItems(order.id);
    },
  },
};
```
With FraiseQL, if you don’t design your views to include relationships, you might still hit N+1 problems—but now it’s worse, because FraiseQL compiles the *entire query* to SQL, and poor design can lead to **massive, inefficient joins** or **multiple roundtrips**.

### The Solution: Denormalize or Use Joins Explicitly
In FraiseQL, **pull all data in a single query** by designing views that include related data. For example:

```sql
-- A view that fetches users + their orders in one query
CREATE VIEW user_with_orders AS
  SELECT
    u.*,
    jsonb_agg(o.id) AS orders
  FROM users u
  LEFT JOIN orders o ON u.id = o.user_id
  GROUP BY u.id;
```

Then map this to your schema:

```graphql
type User @fraiseql(view: "user_with_orders") {
  id: ID!
  name: String!
  orders: [Order!]!  # Denormalized as JSON array
}
```

### When to Use Joins vs. Denormalization
- **Use joins** if you need precise filtering on related data (e.g., `order WHERE status = "shipped"`).
- **Denormalize** (use JSON/arrays) if you just need the data in one query and can filter client-side.

### Why This Works
- **No N+1**: Everything fetches in a single query.
- **Explicit design**: You control the tradeoff between denormalization and join complexity.

---

## Anti-Pattern 5: Resolver Side Effects (Mutations That Aren’t Mutations)

### The Problem
In traditional GraphQL, you might use mutation resolvers for side effects like logging or caching:

```javascript
const resolvers = {
  Mutation: {
    createUser(_, { input }, { dataSources }) {
      const user = dataSources.createUser(input);
      dataSources.logEvent("user_created", user.id); // Side effect
      return user;
    },
  },
};
```

But in FraiseQL:
1. **Mutations must map to database operations** (e.g., `INSERT`, `UPDATE`).
2. **Side effects can’t be handled in the query compiler**—they must be explicit.

### The Solution: Use Database Triggers or Separate Services
For side effects, **offload them to the database** (triggers, stored procedures) or a separate service. For example:

```sql
-- PostgreSQL trigger to log user creation
CREATE OR REPLACE FUNCTION log_user_creation()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO user_events (event_type, user_id)
  VALUES ('created', NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_user_creation
AFTER INSERT ON users
FOR EACH ROW EXECUTE FUNCTION log_user_creation();
```

Then your FraiseQL mutation is pure:

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    id
    name
  }
}
```

### Why This Works
- **No side effects in queries**: Mutations are database-only.
- **Decoupled design**: Logging happens in the DB, not in the query layer.

---

## Implementation Guide: How to Avoid These Anti-Patterns

### Step 1: Start with a Schema-First Approach
Design your GraphQL schema **before** writing database views. Use tools like:
- [GraphQL Code Generator](https://graphql-code-generator.com/) to scaffold your schema.
- FraiseQL’s [`@fraiseql` directive](https://docs.fraise.dev/features/schema-directives) to map types to views.

Example:
```graphql
# schema.graphql
type User @fraiseql(view: "users") {
  id: ID!
  name: String!
  orders: [Order!]! @fraiseql(view: "user_orders")
}
```

### Step 2: Precompute Everything
If you need to fetch related data (e.g., `User.orders`), **precompute it in the database**:
- Use **materialized views** for frequently accessed data.
- Use **JSON arrays** to denormalize relationships when joins are impractical.

### Step 3: Enforce Permissions at the Database Level
Instead of runtime checks, use:
- **PostgreSQL Row-Level Security** (RLS).
- FraiseQL’s [`@fraiseql(permission)`](https://docs.fraise.dev/features/permissions) directive.

### Step 4: Avoid Resolvers
FraiseQL’s compiler won’t let you use resolvers for data fetching. If you need custom logic:
- Move it to the database (triggers, functions).
- Use **FraiseQL’s `scalar` types** for complex transformations.

### Step 5: Test Queries with `curl` or Postman
Before writing resolvers, **verify your queries work as SQL**:
```bash
curl -X POST http://localhost:3000/playground \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ user(id: \"1\") { name orders { id } } }"
  }'
```
This ensures your schema maps cleanly to SQL.

---

## Common Mistakes to Avoid

1. **Assuming Resolvers Work Like in Apollo**
   FraiseQL doesn’t support resolver functions. If you’re used to Apollo’s flexibility, you’ll need to adjust.

2. **Overusing Denormalization**
   Denormalizing everything can make queries harder to maintain. Use joins when you need precise filtering.

3. **Ignoring Performance**
   FraiseQL is fast, but if you design views poorly (e.g., wide tables with N columns), queries will be slow. Profile your SQL!

4. **Mixing Static and Dynamic Logic**
   If a field’s value depends on runtime data (e.g., `isActive` based on `createdAt`), you’ll need a workaround like a scalar function.

5. **Not Testing Edge Cases**
   FraiseQL compiles queries at startup, so errors might only appear in production. Test with:
   - Invalid permissions.
   - Large datasets.
   - Edge-case queries.

---

## Key Takeaways

✅ **FraiseQL is a database-first tool**—design your schema to map cleanly to SQL.
✅ **Avoid resolvers for data fetching**—precompute or use views.
✅ **Enforce permissions in the database**, not at runtime.
✅ **Design for N+0**: Pull all related data in a single query.
✅ **Use denormalization judiciously**—it’s a tool, not a crutch.
✅ **Leverage database features** (triggers, RLS) for side effects.
✅ **Test queries as SQL** before writing GraphQL.

---

## Conclusion: FraiseQL Is Different—but It’s Powerful

FraiseQL’s compiler changes how you design GraphQL APIs. The anti-patterns here aren’t bugs—they’re **mistakes we make when we expect FraiseQL to behave like a traditional GraphQL server**. But once you adjust your mindset and embrace its strengths (performance, simplicity, database integration), you’ll build APIs that are:
- **Blazing fast** (no resolver overhead).
- **Easy to maintain** (schema-first design).
- **Secure by default** (permissions enforced at the DB level).

The key is to **think in SQL first, GraphQL second**. Start small, iterate, and you’ll avoid the pitfalls that trip up even experienced developers. Happy querying! 🚀

---
### Further Reading
- [FraiseQL Docs: Schema Directives](https://docs.fraise.dev/features/schema-directives)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [GraphQL Code Generator](https://graphql-code-generator.com/)
```

This blog post is **practical, code-first**, and **honest about tradeoffs**, while keeping it beginner-friendly. It balances theory with actionable guidance, ensuring readers can apply the lessons immediately.