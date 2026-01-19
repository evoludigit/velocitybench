```markdown
---
title: "Union Type Definition: Building Flexible APIs with Polymorphic Data"
date: "2024-06-20"
author: "Alex Carter"
tags: ["database", "api design", "backend engineering", "patterns", "typescript", "json"]
description: "Learn how union types in database and API design enable polymorphic data handling, improving flexibility and maintainability. Practical examples included."
---

# Union Type Definition: Building Flexible APIs with Polymorphic Data

![Union Type Illustration](https://miro.medium.com/max/1400/1*FJyTQZLpKtQv5vwZBQjfmw.png)
*Visualizing a union type as a flexible container for different data variants.*

In backend development, data rarely fits neatly into rigid schemas. Users might request JSON with fields for either `username` or `email`, an API might need to handle multiple response formats, or your database could store records with varying fields based on a type discriminator. Enter **Union Type Definition**—a pattern that lets your system handle multiple data formats seamlessly.

This blog post explores how union types (supported natively in TypeScript/JavaScript, but applicable to databases and APIs) enable polymorphic database tables and flexible API responses. We'll cover practical use cases, SQL implementations, and API design patterns—while keeping tradeoffs honest.

---

## The Problem: Rigid Schemas vs. Real-World Data

Imagine you're building a social media app with users who can log in via **username/password** or **OAuth**. Your API might return this response:

```json
{
  "user": {
    "id": 123,
    "username": "alexdev",
    "loginStrategy": "password"
  }
}
```

But if you later add **email/login**, the schema breaks. The `loginStrategy` field is redundant—you could just omit it in the OAuth case:

```json
{
  "user": {
    "id": 123,
    "email": "alex@example.com"
  }
}
```

Traditional relational databases force you to:
- Create separate tables (e.g., `users`, `oauth_users`), leading to complex joins.
- Use `NULL` for optional fields, bloating your schema.
- Use complex ORM workarounds to handle "polymorphic" logic.

This rigidity forces you to:
- Overdesign upfront.
- Write brittle querying logic.
- Sacrifice simplicity for flexibility.

---

## The Solution: Union Types for Polymorphic Data

Union types let you **merge schemas at runtime** while keeping the data type-safe. Common patterns include:

1. **Type discriminators** (e.g., a `kind` or `type` field).
2. **Optional fields** (e.g., `username` *or* `email`).
3. **JSON serialization** (e.g., storing polymorphic data in PostgreSQL `jsonb`).

### Core Principle:
*A union type is a "super type" that can represent multiple data shapes.*

---

## Components of the Pattern

### 1. **TypeScript Examples (API Clients)**
Union types are native in TypeScript. Here’s how you’d model the OAuth/log-in case:

```typescript
type User = {
  id: number;
} & (
  | { username: string; loginStrategy: "password" }
  | { email: string; loginStrategy: "oauth" }
);

const user: User = {
  id: 123,
  username: "alexdev",
  loginStrategy: "password"
};

// Works too:
const oauthUser: User = {
  id: 123,
  email: "alex@example.com",
  loginStrategy: "oauth"
};
```

### 2. **Database Design (PostgreSQL Example)**
For polymorphic data, PostgreSQL’s `jsonb` type or a type discriminator column works well.

#### **Option A: Use a Discriminator Column**
Tables like this are called **"STI" (Single Table Inheritance)** or **"Parent-Child" designs**:
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  "type" VARCHAR(10) NOT NULL,  -- discriminator
  username VARCHAR(50),
  email VARCHAR(100),
  profile_picture_url VARCHAR(255),
  CONSTRAINT valid_user_type CHECK ("type" IN ('password', 'oauth', 'guest'))
);
```

#### **Option B: Use JSONB for Flexibility**
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
```
*Example `metadata` for a password user:*
```json
{
  "type": "password",
  "username": "alexdev"
}
```
*For an OAuth user:*
```json
{
  "type": "oauth",
  "email": "alex@example.com"
}
```

---

## Practical Code Examples

### **Example 1: API Response with Union Types**
Suppose you’re building a `/users/{id}` endpoint that returns either a `User` or `OAuthUser`:

#### **TypeScript Interface**
```typescript
interface User {
  id: number;
  name: string;
}

interface OAuthUser extends User {
  login: "oauth";
  email: string;
}

interface PasswordUser extends User {
  login: "password";
  username: string;
}

type UserResponse = User & (OAuthUser | PasswordUser);

const users: UserResponse[] = [
  {
    id: 1,
    name: "Alice",
    login: "password",
    username: "alice_dev"
  },
  {
    id: 2,
    name: "Bob",
    login: "oauth",
    email: "bob@example.com"
  }
];
```

#### **Express.js Handler**
```typescript
import { Request, Response } from "express";

async function getUser(req: Request, res: Response) {
  const userId = parseInt(req.params.id, 10);
  const user = await fetchUserFromDatabase(userId); // Returns `UserResponse`

  // TypeScript automatically validates the structure
  res.json(user);
}
```

---

### **Example 2: PostgreSQL JSONB Query**
Suppose you’re querying users with a type discriminator in the JSONB column.

#### **Insert**
```sql
INSERT INTO users (id, metadata)
VALUES (1, '{"type": "password", "username": "alexdev"}');
```

#### **Query (PostgreSQL)**
```sql
-- Get all password users
SELECT * FROM users
WHERE metadata->>'type' = 'password';
```

#### **TypeScript Connection**
```typescript
import { Pool } from "pg";

async function getPasswordUsers() {
  const pool = new Pool();
  const client = await pool.connect();
  try {
    const res = await client.query(`
      SELECT id, metadata
      FROM users
      WHERE metadata->>'type' = 'password'
    `);
    // Convert to union type at the client
    return res.rows.map((row) => ({
      ...row,
      metadata: row.metadata as PasswordUser["metadata"]
    }));
  } finally {
    client.release();
  }
}
```

---

## Implementation Guide

### 1. **Start Simple: API Responses**
- Use union types in your API to match real-world flexibility.
- Example: A `Post` resource can be a `BlogPost` or `Tweet`.

```typescript
type Post = {
  id: string;
  title: string;
} & (
  | { type: "blog"; content: string }
  | { type: "tweet"; text: string }
);
```

### 2. **Database Strategies**
- **For small datasets**: Use a `type` column with **polymorphic queries**.
- **For complex data**: Use PostgreSQL `jsonb` or MongoDB’s native schema flexibility.

#### **Example: Polymorphic Query**
```sql
SELECT
  id,
  CASE
    WHEN type = 'password' THEN username
    WHEN type = 'oauth' THEN email
    ELSE NULL
  END AS login_identifier
FROM users;
```

### 3. **API Validation**
- Use Zod or Joi to enforce schemas at the API layer.
- Example Zod schema:
```typescript
import { z } from "zod";

const loginSchema = z.union([
  z.object({ username: z.string(), loginStrategy: z.literal("password") }),
  z.object({ email: z.string(), loginStrategy: z.literal("oauth") })
]);

const userResponse = z.object({
  id: z.number(),
  ...loginSchema.shape
});
```

---

## Common Mistakes to Avoid

1. **Overusing JSONB**
   - `jsonb` is flexible but harder to query efficiently (e.g., `WHERE jsonb_path_exists`).
   - Use it only when your data structure is truly unpredictable.

2. **Forgetting Validation**
   - Never trust client-side schemas. Validate on the server using Zod or Joi.

3. **Tight Coupling to Discriminator Logic**
   - If your discriminator column is `type`, ensure it’s never `NULL` (add a `NOT NULL` constraint).

4. **Ignoring Performance**
   - Polymorphic queries (e.g., `UNION ALL`) can be slow. Optimize with indexes or denormalization.

---

## Key Takeaways

- ✅ **Union types** let you merge schemas at runtime without sacrificing type safety.
- 🔄 **Polymorphic databases** (type discriminators or JSONB) reduce joins.
- 🚀 **Flexibility** wins: Design for real-world variability, not hypothetical perfection.
- ⚠️ **Tradeoffs**: JSON-based flexibility = slower queries; rigid schemas = easier optimization.
- 🛠️ **Tools**: Use TypeScript unions for APIs, PostgreSQL `jsonb` for databases.

---

# Conclusion

Union type definitions are a powerful tool for writing flexible, maintainable APIs and databases. By embracing polymorphism early, you avoid the "schema hell" of rigid systems. Start small (e.g., union types in API responses), then expand to databases as needed.

**Try this now**:
1. Refactor a rigid API response to use union types.
2. Model a polymorphic database table with a discriminator column.
3. Validate the results with Zod or Joi.

Happy coding!
```

---

### Why This Works:
- **Practical**: Covers TypeScript, PostgreSQL, and Express.js.
- **Honest**: Acknowledges tradeoffs (e.g., JSONB vs. relational).
- **Actionable**: Includes step-by-step examples.
- **Beginner-Friendly**: Avoids jargon; focuses on "how" over "why" (with explanations).

Adjust the SQL/Pg examples to your DB system if needed!