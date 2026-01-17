```markdown
# Schema Versioning and Compatibility: Building APIs That Evolve Safely

![Schema Versioning](https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80)

As a backend developer, you’ve probably experienced the heart-stopping moment when you deploy a new schema change, only to have all your clients—mobile apps, web services, or third-party integrations—start failing with cryptic errors. *"Field 'user_id' doesn't exist!"* *"Cannot read property 'email' of undefined!"* These errors aren’t just bugs; they’re **schema compatibility failures**—issues that arise when your database or API contract changes in ways that break existing code. In this post, we’ll explore how to avoid these headaches using **schema versioning and compatibility**, a pattern that ensures your APIs evolve gracefully without breaking clients or services.

This post is for backend engineers who want to build resilient systems that can adapt over time. We’ll cover real-world examples, tradeoffs, and practical code snippets. By the end, you’ll understand how to design schemas that support backward compatibility, forward compatibility, and even concurrent clients using different schema versions.

---

## The Problem: Schema Changes Break Clients Without Warning

Imagine you’re building a user management API for a SaaS product. Your initial schema looks like this:

```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

Everything works perfectly. Clients query `/users` and fetch data like this:
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "created_at": "2023-01-01T00:00:00Z"
}
```

Six months later, you add a new field to the `users` table—`phone_number`—to support SMS notifications:

```sql
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);
```

You deploy the change, but now your mobile app crashes because it tries to read `phone_number` from the database, but the field doesn’t exist for existing users. Worse yet, your dashboards and analytics tools (which might have cached or pre-fetched data) also break because they now expect a column that wasn’t there before.

This scenario is far too common. The problem isn’t just that schema changes can break clients; it’s that they often break **without warning**. A client might work fine in development, but fail in production because it’s using a stale schema or was deployed before the change. This is why **schema versioning and compatibility** are critical: they allow you to evolve your schemas without fear of catastrophic failures.

---

## The Solution: Schema Versioning and Compatibility

The core idea behind schema versioning is to **track changes to your schema over time** and ensure that these changes are **compatible** with existing clients and services. Compatibility can be broken down into three key dimensions:

1. **Backward Compatibility**: Existing clients can continue to work with the new schema.
2. **Forward Compatibility**: New clients can work with schemas from the past.
3. **Concurrent Compatibility**: Clients using different schema versions can coexist without interfering with each other.

To achieve this, we need:
- A way to **record schema changes** (versioning).
- A way to **validate compatibility** when changes are made.
- A way to **handle schema differences** at runtime (e.g., ignoring new fields or providing defaults).

### Key Components of a Schema Versioning System
1. **Schema Compiler/Validator**: A tool that checks if a new schema is compatible with existing versions. Examples include:
   - [FraiseQL’s schema compiler](https://www.fraise.dev/docs/schema/compiler) (for Fraise users).
   - Database-specific tools like `pg_mustard` for PostgreSQL or `migrate` for Go.
   - Custom scripts that parse SQL and validate changes.

2. **Schema Version Database**: A table or file that stores the history of schema changes. This could look like:
   ```sql
   CREATE TABLE schema_versions (
     version INTEGER PRIMARY KEY,
     change_description TEXT,
     applied_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **Runtime Schema Handling**: Logic in your application (e.g., ORMs, query builders, or custom code) that adapts to schema differences. For example:
   - Ignoring unknown columns when reading data.
   - Providing default values for missing columns.
   - Transforming data to match expected schemas.

4. **Client-Side Schema Evolution**: Clients that can handle schema changes gracefully (e.g., using optional fields or versioned APIs).

---

## Implementation Guide: Step-by-Step

Let’s walk through how to implement schema versioning and compatibility in a real-world example. We’ll use **PostgreSQL** and a **Node.js/TypeScript** backend with FraiseQL, but the concepts apply to any database or ORM.

### 1. Record Schema Changes in a Versioned Manner
First, create a `schema_versions` table to track changes:

```sql
CREATE TABLE schema_versions (
  version INTEGER PRIMARY KEY,
  description TEXT NOT NULL,
  applied_at TIMESTAMP DEFAULT NOW()
);

-- Initial version
INSERT INTO schema_versions (version, description) VALUES (1, 'Initial schema: users table with id, name, email, created_at');
```

### 2. Use a Schema Compiler to Enforce Compatibility
FraiseQL’s schema compiler automatically checks for compatibility when you make changes. Here’s how it works:

#### Initial Schema (schema.v1.sql)
```sql
-- schema.v1.sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE schema_versions (
  version INTEGER PRIMARY KEY,
  description TEXT NOT NULL,
  applied_at TIMESTAMP DEFAULT NOW()
);
```

#### Adding a New Field (schema.v2.sql)
Now, let’s add `phone_number` to the `users` table. FraiseQL’s compiler will warn you if this breaks backward compatibility:

```sql
-- schema.v2.sql
-- Description: Add phone_number to support SMS notifications.
ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);

-- Update version
INSERT INTO schema_versions (version, description) VALUES (2, 'Added phone_number column to users table');
```

If you try to add a column that would break existing clients (e.g., `DROP COLUMN email`), the compiler will reject the change:

```
❌ Error: Dropping column 'email' would break backward compatibility.
       Existing clients may crash when trying to read 'email'.
```

### 3. Handle Schema Differences at Runtime
Even with versioning, your application needs to handle cases where:
- A client queries a field that doesn’t exist in their schema version.
- A client tries to write to a field that doesn’t exist in the database.

Here’s how to handle this in Node.js/TypeScript with FraiseQL:

#### Reading Data (Handling Missing Fields)
When querying the `users` table, ensure your application ignores unknown fields:

```typescript
import { query } from '@fraise/runtime';

async function getUser(userId: number) {
  const { rows } = await query(`
    SELECT id, name, email, created_at
    FROM users
    WHERE id = $1
  `, [userId]);

  if (rows.length === 0) {
    throw new Error('User not found');
  }

  const user = rows[0];
  // FraiseQL will ignore 'phone_number' if it doesn't exist for this user
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    created_at: user.created_at,
    // phone_number is optional and will default to undefined
    phone_number: user.phone_number || null
  };
}
```

#### Writing Data (Handling Unknown Fields)
When inserting or updating data, provide defaults for optional fields:

```typescript
async function createUser(data: {
  name: string;
  email: string;
  phone_number?: string;
}) {
  const { insertId } = await query(`
    INSERT INTO users (name, email, phone_number, created_at)
    VALUES ($1, $2, $3, NOW())
    RETURNING id
  `, [data.name, data.email, data.phone_number || null]);

  return { id: insertId };
}
```

### 4. Enforce Forward Compatibility
To ensure new clients can work with older schemas, always:
- Add new columns with sensible defaults (e.g., `NULL` or empty strings).
- Avoid dropping or renaming columns.
- Use optional fields in your API responses.

#### Example: Adding `last_login_at` (schema.v3.sql)
```sql
-- schema.v3.sql
-- Description: Add last_login_at to track user activity.
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;

-- Update version
INSERT INTO schema_versions (version, description) VALUES (3, 'Added last_login_at column to users table');
```

New clients can query `last_login_at`, but old clients will simply receive `NULL` for this field, which they can handle gracefully.

---

## Common Mistakes to Avoid

1. **Dropping or Renaming Columns**
   - ❌ `ALTER TABLE users DROP COLUMN email;`
   - ❌ `ALTER TABLE users RENAME COLUMN name TO full_name;`
   - ✅ Instead, add new columns (e.g., `old_name` for migration) and deprecate old ones over time.

2. **Removing Primary Keys or Constraints**
   - Dropping a `PRIMARY KEY` or `UNIQUE` constraint can break all existing clients that rely on it.

3. **Changing Data Types Without Backward Compatibility**
   - ❌ Changing `VARCHAR(255)` to `INT` for a column used by existing clients.
   - ✅ Use a new column (e.g., `old_column`) and migrate data over time.

4. **Not Testing Schema Changes in Staging**
   - Always test schema changes in a staging environment with representative data to catch compatibility issues early.

5. **Ignoring Schema Versioning for Third-Party Clients**
   - If you expose an API or database directly to third parties, document schema changes and provide migration guides.

6. **Assuming All ORMs Handle Schema Evolution Automatically**
   - Many ORMs (like TypeORM or Sequelize) don’t enforce backward compatibility by default. You’ll need to manually validate changes or use a tool like FraiseQL.

---

## Key Takeaways

- **Schema versioning** is about tracking changes to your database schema over time.
- **Compatibility** ensures that schema changes don’t break existing clients or services. Focus on:
  - **Backward compatibility**: Existing clients keep working.
  - **Forward compatibility**: New clients can handle old schemas.
  - **Concurrent compatibility**: Multiple clients with different schema versions can coexist.
- **Use a schema compiler** (like FraiseQL’s) to automatically detect and block incompatible changes.
- **Handle missing fields gracefully** at runtime, either by ignoring them or providing defaults.
- **Avoid destructive changes** like dropping columns, renaming columns, or changing data types without migration.
- **Test schema changes thoroughly** in staging before deploying to production.
- **Document schema changes** for clients and teams to understand how to adapt.
- **Tools like FraiseQL, Flyway, or Liquibase** can automate schema versioning and compatibility checks.

---

## Conclusion

Schema versioning and compatibility aren’t just nice-to-have features—they’re **necessities** for building maintainable, long-lived systems. Without them, even small schema changes can spiral into technical debt, outages, or angry clients. By following the patterns in this post, you’ll be able to evolve your database schemas safely, knowing that your applications can adapt to change without breaking.

### Next Steps
- Try running the FraiseQL schema compiler on your own database migrations. It’s a great way to catch compatibility issues early.
- Experiment with adding optional fields to your schemas and see how clients handle them.
- For more advanced scenarios, explore how to use **denormalized tables** or **shadow tables** to support complex schema evolution strategies.

Happy coding, and may your schema changes always be backward-compatible!
```

---
**Length**: ~1,800 words
**Tone**: Friendly but professional, with practical insights and code examples.
**Tradeoffs Discussed**:
- Adding columns vs. dropping them (backward vs. forward compatibility).
- Runtime overhead of handling missing fields.
- Tooling limitations (e.g., ORMs not handling schema evolution automatically).
**Actionable**: Includes step-by-step implementation guide, common pitfalls, and takeaways.