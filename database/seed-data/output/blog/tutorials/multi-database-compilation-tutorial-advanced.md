```markdown
---
title: "Multi-Database Compilation: Building a Schema That Works Everywhere Without Losing Your Mind"
date: 2023-11-15
tags: ["database", "api", "design-patterns", "sql", "backend", "fraise-ql"]
---

# Multi-Database Compilation: Building a Schema That Works Everywhere Without Losing Your Mind

Back in 2017, I was part of a team maintaining a SaaS application that needed to scale across PostgreSQL, MySQL, and eventually Azure SQL Server. Our team spent months migrating queries and adjusting schemas to fit each implementation. Those months were a constant balance between "Get this working in PostgreSQL" and "Oh no, MySQL doesn't support that subquery". Database compatibility was the elephant in the room, and no matter how much we refactored, we couldn't shake the feeling that we were perpetually playing catch-up.

By the time we discovered **multi-database compilation**, I was exhausted. It wasn’t a perfect solution, but it cut our deployment time by 80% and stabilized our schema across all our environments. Fast-forward to 2023, and I’m sharing this pattern not just to save you time, but to help you avoid the same frustrations we went through.

---

## The Problem: Separate Compilation and Schema per Database

Most applications need to work across multiple database systems because:

1. **Fallen Relics of the Past:** Legacy systems are still running on MySQL.
2. **The Cloud is Not Monolithic:** Azure, AWS, and GCP all have different SQL dialects.
3. **Local Development vs. Production:** You can’t run PostgreSQL locally if you only use SQLite in development.
4. **Database Versioning:** Even within a vendor, feature support can differ wildly across versions (e.g., CTEs in MySQL 8.0 vs. 5.7).

Traditionally, the way to handle this was to:

- Write a schema in one dialect (e.g., PostgreSQL)
- Manually rewrite queries for other databases
- Use tools like Flyway or Liquibase to manage migrations, but that didn’t help with runtime compatibility
- Accept that your application had to behave slightly differently depending on the backend

The problem? **Every time you needed to add a new feature**, you had to rewrite it for each database. And if you later moved parts of your application to a new database? You were back to square one.

### Example: The Same Query in Different Dialects

Let’s take a seemingly simple query:

```sql
-- PostgreSQL works fine
SELECT user.id, COUNT(*) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id
```

But in MySQL, this fails because MySQL doesn’t allow non-aggregated columns in `SELECT` without a `GROUP BY` clause:

```sql
-- MySQL throws an error here
SELECT user.id, COUNT(*) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id
```

Fixing this requires rewriting the query:

```sql
-- MySQL-compatible rewrite
SELECT u.id, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id
```

Even more painful? **Adding a new feature** means you have to update **every** query in every database. This is unsustainable.

---

## The Solution: Multi-Database Compilation

Multi-database compilation solves this by **compiling once to an intermediate representation** before targeting a specific database. The key idea is to:

1. **Define a database-agnostic schema** (often called "CompiledSchema" in tools like FraiseQL)
2. **Compile this schema to a target database** once, with optimizations and adjustments for that specific backend
3. **Share the compiled schema** across all environments without needing to write database-specific SQL

This approach is conceptually similar to how Java compiles to bytecode, which can run on any JVM. Here’s how it works in practice:

- You write your schema and queries in a language that doesn’t rely on any database-specific features.
- The compiler converts your schema into an abstract, database-agnostic structure (the "CompiledSchema").
- You then target this CompiledSchema to your specific database, which applies dialect-specific optimizations (e.g., indexing, query rewriting).
- Your application interacts with the database **through this target schema**, not directly with raw SQL.

---

## Components/Solutions

Multi-database compilation relies on three core components:

1. **A Schema Definition Language (SDL)**
   The language you use to define your database schema without database-specific features. Think of it like SQL without `ORDER BY` or `LIMIT` unless it’s supported everywhere.

2. **A Compilation Pipeline**
   A system that takes your SDL schema and converts it into a database-agnostic intermediate representation (the CompiledSchema), then compiles it to target databases.

3. **A Query Engine**
   A runtime that translates queries from your application into database-specific SQL based on the CompiledSchema.

### Tools and Libraries That Support This Pattern
Tools like **FraiseQL**, **Prisma**, **TypeORM**, and **Knex.js** (with dialects) all use variations of this pattern. FraiseQL, for example, compiles once to a CompiledSchema and then optimizes for PostgreSQL, SQLite, MySQL, etc.

---

## Implementation Guide: Building a Multi-Database Schema with FraiseQL

Let’s walk through an example using FraiseQL, a tool that implements multi-database compilation. If you aren’t familiar with it, don’t worry—I’ll keep this practical.

### Step 1: Define Your Database-Agnostic Schema

FraiseQL uses a JSON-based schema definition language. Here’s how we define a simple schema for users and orders:

```json
// users_and_orders.schema.json
{
  "tables": {
    "users": {
      "columns": [
        { "name": "id", "type": "uuid", "primaryKey": true },
        { "name": "email", "type": "string", "unique": true }
      ]
    },
    "orders": {
      "columns": [
        { "name": "id", "type": "uuid", "primaryKey": true },
        { "name": "user_id", "type": "uuid", "references": { "table": "users", "column": "id" } },
        { "name": "amount", "type": "integer" }
      ]
    }
  }
}
```

This schema is **database-agnostic** and doesn’t assume features like `UUID` support (though FraiseQL handles it for you).

---

### Step 2: Compile to a Target Database

Now we compile this schema to PostgreSQL:

```bash
fraise compile --target=postgresql --output=postgresql.compiled.json users_and_orders.schema.json
```

FraiseQL’s compiler handles database-specific optimizations (e.g., UUID handling, indexing). The output is a **compiled schema** for PostgreSQL:

```json
// postgresql.compiled.json (simplified)
{
  "tables": {
    "users": {
      "id": { "type": "uuid", "primaryKey": true },
      "email": { "type": "varchar(255)", "unique": true },
      "indexes": [{ "name": "idx_users_email", "columns": ["email"] }]
    },
    ...
  }
}
```

Notice how it generates a PostgreSQL-specific index for the `email` column.

---

### Step 3: Generate Database-Specific SQL

Now, we can generate SQL for any database:

```bash
fraise generate --target=postgresql --schema=postgresql.compiled.json --output=postgresql/migrations
```

This generates:

1. `postgresql/migrations/000_users_migration.sql`
2. `postgresql/migrations/001_orders_migration.sql`

Example output (simplified):

```sql
-- postgresql/migrations/000_users_migration.sql
CREATE TABLE users (
  id uuid PRIMARY KEY,
  email varchar(255) UNIQUE NOT NULL,
  CONSTRAINT idx_users_email UNIQUE (email)
);
```

---

### Step 4: Run Migrations and Use the Compiled Schema

Now we can run these migrations on our PostgreSQL database. But here’s the key part:

**We don’t need to rewrite queries for MySQL!**

FraiseQL provides a query builder that compiles your queries to the target database:

```typescript
// Using FraiseQL’s query builder
const users = await fraise.query({
  select: ["email"],
  distinct: true,
  from: "users"
}).compileToPostgres(); // or compileToMySQL(), compileToSQLite()

// Outputs PostgreSQL-specific SQL:
SELECT DISTINCT "email"
FROM "users";
```

Or, if you target MySQL:

```typescript
const users = await fraise.query({
  select: ["email"],
  distinct: true,
  from: "users"
}).compileToMySQL();

// Outputs MySQL-specific SQL:
SELECT DISTINCT `email`
FROM `users`;
```

---

## Common Mistakes to Avoid

1. **Assuming All Databases Support Everything**
   Even if you use a tool like FraiseQL, some features (like window functions in MySQL) might not compile cleanly. Always test your compiled schema in your target databases.

2. **Not Compiling for Version-Specific Dialects**
   MySQL 5.7 and 8.0 differ in how they handle JSON, CTEs, and other features. Ensure your compiler supports the exact version you’re targeting.

3. **Ignoring Performance Implications**
   While multi-database compilation abstracts away the worst of database differences, some databases are still slower than others for certain queries. Profile your compiled queries to ensure they perform well.

4. **Not Testing Edge Cases**
   If your application uses transactions, stored procedures, or complex joins, test the compiled schemas thoroughly. Some edge cases might not work as expected across databases.

5. **Tight Coupling to a Specific Tool**
   If you rely on FraiseQL, but later need to add Oracle support, ensure your tool supports it. No single tool handles every database perfectly.

---

## Key Takeaways

✔ **Multi-database compilation reduces duplication** by compiling once to a database-agnostic schema.
✔ **Optimizations are handled at compile time**, not runtime.
✔ **You can generate SQL for multiple databases** from the same schema definition.
✔ **Migrations are simpler** because you only need to maintain one schema. 🚀
⚠️ **Not all databases support the same features**, so test rigorously.
⚠️ **Performance varies**—profile your compiled queries.
⚠️ **Tool choice matters**—pick one that supports your target databases.

---

## Conclusion: No More Database-Specific Nightmares

The multi-database compilation pattern is a game-changer for applications that need to run across multiple databases. It eliminates the need to rewrite queries for every environment and gives you a single source of truth for your schema.

But remember: **No single tool or pattern is perfect**. You’ll still need to test, profile, and optimize. However, this pattern saves you **months of manual rewrites** and gives you the freedom to choose your database without fear.

**Try it yourself:**
1. Define your schema once (no database-specific SQL).
2. Compile it to your target databases.
3. Generate migrations and use the compiled schema.

If your team is still fighting with database dialects, multi-database compilation is worth exploring. And if you’ve been there, you’ll know—it’s worth every second saved.

Happy coding!
```

---

**Appendix A: Example of FraiseQL’s Query API**
Here’s a more complete example of how FraiseQL’s query builder compiles to different databases:

```typescript
// Query for user orders, compiled to PostgreSQL vs. MySQL
const query = fraise.query({
  select: ["u.id", fraise.fn.count("o.id").as("order_count")],
  from: "users u",
  leftJoin: ["orders o", "o.user_id = u.id"],
  groupBy: ["u.id"]
});

// Compile to PostgreSQL (CTE-friendly)
const postgresqlSQL = query.compileToPostgres();
console.log(postgresqlSQL);
// SELECT u.id, COUNT(o.id) AS order_count
// FROM users u
// LEFT JOIN orders o ON o.user_id = u.id
// GROUP BY u.id

// Compile to MySQL (no CTEs, uses subquery)
const mysqlSQL = query.compileToMySQL();
console.log(mysqlSQL);
// SELECT u.id, (
//   SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id
// ) AS order_count
// FROM users u
```

---

**Appendix B: When to Use Multi-Database Compilation**
Use this pattern when:
- You need to run in multiple database environments (dev, staging, prod).
- Your team writes queries in a single language (e.g., TypeScript/JS) and wants to avoid SQL dialect hell.
- You’re scaling out and need to avoid vendor lock-in.

Avoid it if:
- Your app is **single-database only**, and you’re okay with explicit SQL.
- You need **low-latency compilation** (this adds runtime overhead).
- Your database has **proprietary features** not supported by the compiler (e.g., some Oracle-specific optimizations).

---